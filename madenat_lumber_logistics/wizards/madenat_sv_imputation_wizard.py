# -*- coding: utf-8 -*-
"""I2 — Asistente de imputación DOCUMENTAL SV (CANON/19 v1.6.0 / AD-91).

Registra/consolida etiquetas procesadas contra SV por guía **sin efecto en
stock**. Permite:

* listar las etiquetas de la guía con su **volumen nominal editable**;
* proponer un reparto **FIFO simple y editable** hacia los SV candidatos;
* advertir el **exceso SV-side** (blando: motivo + auditoría) y la **falta de
  SV candidato** (motivo, sin bloqueo) — respetando el **techo duro de
  etiqueta** (D-I2-16);
* **dejar pendiente** o **aplicar** según rol;
* idempotencia por **clave documental propia** (no `picking_id`).
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round

import re

from psycopg2.errors import SerializationFailure

from ..models.madenat_sv_imputation import I2_CONFLICT_MSG, I2_VOLUME_PRECISION


class MadenatSvImputationWizard(models.TransientModel):
    _name = 'madenat.sv.imputation.wizard'
    _description = 'Asistente de imputación documental SV (I2)'
    _inherit = ['madenat.deviation.mixin']

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía de retorno', required=True,
        domain=lambda self: self.env[
            'madenat.sv.imputation']._i2_return_guide_domain(),
        help='Guía de procesados (retorno) que origina la asignación (D2). El '
             'usuario la selecciona manualmente; no se preselecciona por fecha '
             'ni volumen. Sólo se ofrecen guías confirmadas como retorno de '
             'servicio («¿Es retorno de servicio?» = Sí) y no canceladas.')
    sv_lot_id = fields.Many2one(
        'stock.lot', string='SV de trabajo',
        domain="[('lot_flow_type', '=', 'volume')]",
        help='Etiqueta SV desde la que se abre la operación (Bloque B). '
             'Orienta la navegación y limita la selección inicial; NO genera '
             'reparto, NO introduce cantidades y NO aplica nada.')
    processor_id = fields.Many2one(
        'res.partner', string='Procesador',
        domain="[('is_processor', '=', True)]")
    reason = fields.Text(string='Motivo')
    note = fields.Text(string='Observaciones')
    reopen_reason = fields.Text(
        string='Motivo de reapertura',
        help='Motivo obligatorio para «Volver a borrador» de un documento '
             'anulado (trazabilidad).')
    line_ids = fields.One2many(
        'madenat.sv.imputation.wizard.line', 'wizard_id',
        string='Etiquetas del retorno')
    sv_line_ids = fields.One2many(
        'madenat.sv.imputation.wizard.sv.line', 'wizard_id',
        string='Asignación a SV (reparto editable)')
    imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación', readonly=True,
        help='Imputación de trabajo de la guía. Reintentar el asistente no '
             'crea una nueva (idempotencia, AD-91). Si ya existe una imputación '
             'de trabajo elegible, se abre y se reproduce su selección y '
             'reparto guardados.')
    imputation_state = fields.Selection(
        related='imputation_id.state', string='Estado del documento',
        store=False)
    expected_edit_version = fields.Integer(
        string='Versión esperada', default=0, copy=False,
        help='Versión de edición (`edit_version`) del documento capturada al '
             'abrir el asistente. Guardar/Aplicar la comparan de forma atómica: '
             'si el documento cambió en otra sesión, se rechaza de forma '
             'controlada (no se sobrescribe).')
    save_result = fields.Char(
        string='Confirmación de guardado', readonly=True, copy=False,
        help='Mensaje con la referencia y el estado del documento recién '
             'guardado (no implica aplicar la rebaja).')
    apply_result = fields.Char(
        string='Resultado de la aplicación', readonly=True, copy=False,
        help='Mensaje con la referencia, los m³ aplicados y el estado tras '
             'aplicar la rebaja en la misma ventana.')
    selected_line_count = fields.Integer(
        string='Seleccionadas', compute='_compute_selection_summary')
    available_line_count = fields.Integer(
        string='Disponibles', compute='_compute_selection_summary')
    selected_nominal_m3 = fields.Float(
        string='Nominal incluido (m³)', digits=(16, 3),
        compute='_compute_selection_summary')
    assigned_total_m3 = fields.Float(
        string='Total preparado a todos los SV (m³)', digits=(16, 3),
        compute='_compute_selection_summary',
        help='Σ de todo el reparto del borrador, incluidos SV distintos del de '
             'trabajo. Se muestra sólo cuando hay varios SV.')
    previous_applied_total_m3 = fields.Float(
        string='Aplicado previo (m³)', digits=(16, 3),
        compute='_compute_selection_summary')
    available_total_m3 = fields.Float(
        string='Disponible documental (seleccionadas) (m³)', digits=(16, 3),
        compute='_compute_selection_summary',
        help='Σ del disponible documental de las etiquetas SELECCIONADAS. Es '
             'agregable sin doble conteo porque la disponibilidad se calcula '
             'por lote.')
    prepared_line_count = fields.Integer(
        string='Con reparto preparado', compute='_compute_selection_summary',
        help='Etiquetas SELECCIONADAS con una cantidad > 0 ya preparada hacia '
             'el SV de trabajo. No es lo mismo que «seleccionadas»: una etiqueta '
             'seleccionada con 0 aún no prepara nada.')
    prepared_total_m3 = fields.Float(
        string='Preparado para el SV (m³)', digits=(16, 3),
        compute='_compute_selection_summary',
        help='Subtotal preparado hacia el SV de trabajo (no incluye repartos a '
             'otros SV).')
    packing_pieces_total = fields.Integer(
        string='Piezas de origen', compute='_compute_selection_summary',
        help='Σ de piezas del material del retorno (packing list de origen).')
    packing_documental_volume_total_m3 = fields.Float(
        string='Volumen documental de origen (m³)', digits=(16, 3),
        compute='_compute_selection_summary',
        help='Σ del volumen DOCUMENTAL del packing list de origen. NO es el '
             'volumen que se imputará al SV.')
    selectable_line_count = fields.Integer(
        string='Seleccionables', compute='_compute_selection_summary',
        help='Cantidad de etiquetas del retorno con saldo documental disponible para asignación.')
    not_assignable_line_count = fields.Integer(
        string='Sin disponibilidad', compute='_compute_selection_summary',
        help='Etiquetas seleccionadas sin disponibilidad documental para una '
             'nueva asignación (aplicado, reservado o sin capacidad).')
    no_availability_note = fields.Char(
        string='Aviso de disponibilidad', compute='_compute_selection_summary')
    multi_sv = fields.Boolean(
        string='Varios SV', compute='_compute_selection_summary',
        help='True cuando el reparto del borrador incluye más de un SV destino; '
             'en ese caso se muestra la columna «SV destino».')
    assigned_summary = fields.Char(
        string='Resumen de preparación', compute='_compute_selection_summary',
        help='Texto breve: «X etiquetas · Y m³ preparados para SV…». Se refiere '
             'sólo al reparto hacia el SV de trabajo; no aplica nada.')
    sv_documental_balance_m3 = fields.Float(
        string='Saldo documental del SV (m³)', digits=(16, 3),
        compute='_compute_sv_documental_balance',
        help='Saldo documental I2 del SV de trabajo (magnitud propia; NO es el '
             'stock físico ni el ledger SV).')
    # Bloque B/C (CANON/19 §19.11): selección de envíos a procesador que atienden
    # el retorno. Reutiliza el asistente de imputación (no se crea otro).
    shipment_picking_ids = fields.Many2many(
        'stock.picking', string='Envíos relacionados (a procesador)',
        help='Envíos elegibles que atienden este retorno. Al guardar se '
             'registran como relaciones de conciliación (borrador) y, al '
             'aplicar, como conciliación registrada (CANON/19 §19.11).')
    eligible_shipment_picking_ids = fields.Many2many(
        'stock.picking', compute='_compute_eligible_shipments',
        string='Envíos elegibles')

    @api.depends('line_ids.selected', 'line_ids.nominal_volume_m3',
                 'line_ids.piezas_lote', 'line_ids.volumen_documental_m3',
                 'line_ids.etiqueta_disponible_m3', 'line_ids.etiqueta_nominal_m3',
                 'line_ids.etiqueta_aplicado_m3', 'line_ids.etiqueta_reservado_m3',
                 'line_ids.disponibilidad_detalle',
                 'sv_line_ids.imputed_volume_m3', 'sv_line_ids.sv_lot_id',
                 'sv_lot_id', 'imputation_id')
    def _compute_selection_summary(self):
        Imputation = self.env['madenat.sv.imputation']
        for wiz in self:
            wiz.available_line_count = len(wiz.line_ids)
            selected = wiz.line_ids.filtered('selected')
            wiz.selected_line_count = len(selected)
            wiz.selected_nominal_m3 = sum(
                selected.mapped('nominal_volume_m3'))
            wiz.assigned_total_m3 = sum(
                wiz.sv_line_ids.mapped('imputed_volume_m3'))
            # ── Cabecera única: subtotal del SV de trabajo y totales de origen.
            work_allocs = wiz.sv_line_ids.filtered(
                lambda a: a.sv_lot_id == wiz.sv_lot_id)
            wiz.prepared_total_m3 = sum(
                work_allocs.mapped('imputed_volume_m3'))
            prepared_labels = work_allocs.filtered(
                lambda a: float_compare(
                    a.imputed_volume_m3, 0.0,
                    precision_rounding=I2_VOLUME_PRECISION) > 0
            ).mapped('wizard_line_id')
            wiz.prepared_line_count = len(set(prepared_labels.ids))
            wiz.packing_pieces_total = sum(wiz.line_ids.mapped('piezas_lote'))
            wiz.packing_documental_volume_total_m3 = sum(
                wiz.line_ids.mapped('volumen_documental_m3'))
            wiz.multi_sv = len(
                set(wiz.sv_line_ids.mapped('sv_lot_id').ids)) > 1
            # Aplicado previo y disponible documental EXCLUYENDO este documento
            # (evita contar dos veces la propia operación al editarla, §19.16).
            current = wiz.imputation_id
            wiz.previous_applied_total_m3 = sum(
                Imputation._i2_lot_applied_m3(lot, exclude_imputation=current)
                for lot in selected.mapped('processed_lot_id'))
            wiz.available_total_m3 = sum(
                Imputation._i2_lot_available_for_m3(
                    lot, exclude_imputation=current)
                for lot in selected.mapped('processed_lot_id'))
            # Filas seleccionadas sin disponibilidad documental (no asignables).
            wiz.selectable_line_count = len(wiz.line_ids.filtered('asignable'))
            wiz.not_assignable_line_count = wiz.available_line_count - wiz.selectable_line_count
            no_avail = wiz.line_ids.filtered(lambda l: not l.asignable)
            if no_avail:
                details = '; '.join(
                    '%s — %s' % (
                        (l.etiqueta or l.processed_lot_id.name or '?'),
                        l.disponibilidad_detalle
                        or _('sin disponibilidad documental'))
                    for l in no_avail)
                wiz.no_availability_note = _(
                    '%(n)s de las etiquetas no tienen '
                    'disponibilidad documental para una operación nueva. Se '
                    'conservan, pero no admiten una asignación positiva. '
                    'Causa: %(det)s') % {'n': len(no_avail), 'det': details}
            else:
                wiz.no_availability_note = ''
            # Resumen breve: seleccionadas ≠ con reparto preparado ≠ total.
            if wiz.not_assignable_line_count:
                wiz.assigned_summary = _(
                    '%(sel)s seleccionadas (%(unavail)s sin saldo) · %(prep)s etiquetas con reparto '
                    'preparado · %(vol).3f m³ → %(sv)s') % {
                    'sel': len(selected),
                    'unavail': wiz.not_assignable_line_count,
                    'prep': wiz.prepared_line_count,
                    'vol': wiz.prepared_total_m3,
                    'sv': wiz.sv_lot_id.name or '—'}
            else:
                wiz.assigned_summary = _(
                    '%(sel)s seleccionadas · %(prep)s etiquetas con reparto '
                    'preparado · %(vol).3f m³ → %(sv)s') % {
                    'sel': len(selected),
                    'prep': wiz.prepared_line_count,
                    'vol': wiz.prepared_total_m3,
                    'sv': wiz.sv_lot_id.name or '—'}

    def action_open_no_availability_docs(self):
        """Abre los documentos que explican el saldo de las etiquetas sin
        disponibilidad seleccionadas (§15). Sólo lectura; no altera nada."""
        self.ensure_one()
        docs = self.line_ids.filtered(
            lambda l: (l.selected or not l.asignable) and l.disponibilidad_imputacion_ids
        ).mapped('disponibilidad_imputacion_ids')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documentos que explican el saldo'),
            'res_model': 'madenat.sv.imputation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', docs.ids)],
            'target': 'current',
        }

    @api.depends('sv_lot_id', 'sv_line_ids.imputed_volume_m3')
    def _compute_sv_documental_balance(self):
        Imputation = self.env['madenat.sv.imputation']
        for wiz in self:
            wiz.sv_documental_balance_m3 = (
                Imputation._i2_sv_documental_available_m3(wiz.sv_lot_id)
                if wiz.sv_lot_id else 0.0)

    @api.depends('guia_processing_id', 'processor_id')
    def _compute_eligible_shipments(self):
        Link = self.env['madenat.processor.return.link']
        for wiz in self:
            wiz.eligible_shipment_picking_ids = (
                Link._eligible_shipment_pickings(
                    wiz.guia_processing_id, wiz.processor_id))


    # ── Defaults ─────────────────────────────────────────────────────────
    @api.model
    def _i2_guia_from_context(self):
        ctx = self.env.context
        if ctx.get('active_model') == 'madenat.guia.processing' \
                and ctx.get('active_id'):
            return self.env['madenat.guia.processing'].browse(ctx['active_id'])
        # SAVE (2026-10-11): «Continuar preparación» desde el SV abre el asistente
        # con la guía del documento guardado (reapertura determinista).
        if ctx.get('default_guia_processing_id'):
            return self.env['madenat.guia.processing'].browse(
                ctx['default_guia_processing_id'])
        return self.env['madenat.guia.processing']

    @api.model
    def _i2_sv_from_context(self):
        ctx = self.env.context
        if ctx.get('active_model') == 'stock.lot' and ctx.get('active_id'):
            return self.env['stock.lot'].browse(ctx['active_id'])
        if ctx.get('default_sv_lot_id'):
            return self.env['stock.lot'].browse(ctx['default_sv_lot_id'])
        return self.env['stock.lot']

    @api.model
    def _i2_guia_es_elegible(self, guia):
        """True si la guía es un retorno ELEGIBLE para una NUEVA operación."""
        return bool(
            guia and guia.service_return_confirmation == 'yes'
            and guia.state != 'cancelled')

    def _i2_reconstruct_commands(self, imp):
        """Comandos para reconstruir la representación del wizard (Bloque D).

        Reproduce ``line_ids`` con su **reparto anidado** desde las líneas
        guardadas del documento de trabajo, preservando **selección** y
        reparto. No recarga la guía completa: sólo lo que el usuario guardó.

        El reparto anidado incluye ``wizard_id`` cuando el asistente ya existe
        (p. ej. onchange); al crear el asistente desde ``default_get`` (aún sin
        id) se enlaza en ``create`` para que ``sv_line_ids`` conserve el reparto.
        """
        wizard_id = self.id or False
        commands = []
        for line in imp.line_ids:
            allocs = [(0, 0, {
                'wizard_id': wizard_id,
                'sv_lot_id': alloc.sv_lot_id.id,
                'imputed_volume_m3': alloc.imputed_volume_m3,
            }) for alloc in line.sv_allocation_ids]
            commands.append((0, 0, {
                'processed_lot_id': line.processed_lot_id.id,
                'nominal_volume_m3': line.nominal_volume_m3,
                'pieces': line.pieces,
                'selected': True,
                'sv_alloc_ids': allocs,
            }))
        return commands

    @api.model_create_multi
    def create(self, vals_list):
        """Crea el asistente y enlaza el reparto anidado al propio asistente.

        ``default_get`` reconstruye el reparto como ``line_ids[*].sv_alloc_ids``
        (sin ``wizard_id`` porque el asistente aún no existe). Tras crear el
        asistente se fija ``wizard_id`` para que ``sv_line_ids`` —pestaña
        «Asignación a SV» y cabeceras (``multi_sv``, totales)— refleje el reparto
        guardado. Sin efectos de negocio.
        """
        wizards = super().create(vals_list)
        for wiz in wizards:
            orphans = wiz.line_ids.sv_alloc_ids.filtered(
                lambda alloc: not alloc.wizard_id)
            if orphans:
                orphans.write({'wizard_id': wiz.id})
        return wizards

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sv_lot = self._i2_sv_from_context()
        if sv_lot and 'sv_lot_id' in fields_list and not res.get('sv_lot_id'):
            res['sv_lot_id'] = sv_lot.id
        guia = self._i2_guia_from_context()
        if guia and not self._i2_guia_es_elegible(guia):
            # El contexto puede traer una guía NO elegible (p. ej. abrir desde
            # una guía sin confirmar retorno). NO se preselecciona ni se
            # reconstruye trabajo: el usuario elige una guía de retorno
            # elegible (confirmada Sí y no cancelada).
            guia = self.env['madenat.guia.processing']
        if guia and 'guia_processing_id' in fields_list \
                and not res.get('guia_processing_id'):
            res['guia_processing_id'] = guia.id
        if guia and 'processor_id' in fields_list \
                and not res.get('processor_id'):
            processor = self.env[
                'madenat.processor.return.link']._guia_processor(guia)
            if processor:
                res['processor_id'] = processor.id
        if guia:
            work = self.env['madenat.sv.imputation']._i2_find_work_for_guia(guia)
            if work and 'imputation_id' in fields_list:
                res['imputation_id'] = work.id
            if work and 'expected_edit_version' in fields_list:
                res['expected_edit_version'] = work.edit_version or 1
            # Bloque D: al abrir/reabrir se reproduce la selección y el reparto
            # guardados del documento de trabajo (no se recarga la guía).
            if work and 'line_ids' in fields_list:
                res['line_ids'] = self._i2_reconstruct_commands(work)
            if work and 'reason' in fields_list and not res.get('reason'):
                res['reason'] = work.reason
            if 'shipment_picking_ids' in fields_list:
                links = self.env['madenat.processor.return.link'].search([
                    ('guia_processing_id', '=', guia.id),
                    ('state', 'in', ('draft', 'linked')),
                ])
                if links:
                    res['shipment_picking_ids'] = [(6, 0, links.mapped(
                        'picking_id').ids)]
        return res

    @api.onchange('guia_processing_id')
    def _onchange_guia_processing_id(self):
        """Selección manual de la guía: sin automatismos (D4/D5).

        * Si ya existe una imputación de trabajo elegible para esa guía, se
          **reutiliza** y se reproduce su selección/reparto (Bloque D); no se
          crea una segunda imputación de trabajo.
        * Si es una operación nueva, se listan las etiquetas candidatas **sin
          incluirlas** automáticamente (``selected=False``).
        """
        for wiz in self:
            # Bloque B (§19.16): rechaza selección forzada de guía No/vacía/
            # cancelada ANTES de construir o modificar nada (sin estados
            # parciales). Un dominio de UI no es validación de negocio.
            if wiz.guia_processing_id:
                self.env[
                    'madenat.sv.imputation'
                ]._i2_check_guia_is_eligible_return(wiz.guia_processing_id)
            wiz.line_ids = [(5, 0, 0)]
            wiz.sv_line_ids = [(5, 0, 0)]
            wiz.imputation_id = False
            wiz.expected_edit_version = 0
            if not wiz.guia_processing_id:
                continue
            work = self.env['madenat.sv.imputation']._i2_find_work_for_guia(
                wiz.guia_processing_id)
            if work:
                wiz.imputation_id = work.id
                wiz.expected_edit_version = work.edit_version or 1
                if work.reason:
                    wiz.reason = work.reason
                wiz.line_ids = wiz._i2_reconstruct_commands(work)
                links = self.env['madenat.processor.return.link'].search([
                    ('guia_processing_id', '=', wiz.guia_processing_id.id),
                    ('state', 'in', ('draft', 'linked')),
                ])
                if links:
                    wiz.shipment_picking_ids = [(6, 0, links.mapped(
                        'picking_id').ids)]
            else:
                wiz.line_ids = [
                    (0, 0, dict(wiz._i2_line_vals(lot), selected=False))
                    for lot in self._i2_processed_lots(wiz.guia_processing_id)]

    # ── Helpers ──────────────────────────────────────────────────────────
    @api.model
    def _i2_processed_lots(self, guia):
        """Etiquetas procesadas de la guía (excluye SV de volumen)."""
        return guia.lot_ids.filtered(lambda l: l.lot_flow_type != 'volume')

    @api.model
    def _i2_sv_candidates(self, processor=None, processed_lots=None):
        """SV candidatos elegibles (dominio canónico delegado al modelo I2)."""
        Imputation = self.env['madenat.sv.imputation']
        data = Imputation._i2_sv_candidate_data(
            processor=processor, processed_lots=processed_lots)
        return self.env['stock.lot'].browse([item['lot'].id for item in data])

    def _i2_propose_fifo(self, nominal_m3, processed_lots=None):
        """Reparto FIFO del nominal entre SV candidatos elegibles.

        Usa el **mismo** dominio y saldo documental que el flag y el guard.
        No aplica fallback al nominal cuando el saldo documental es
        cero/negativo (decisión C): solo candidatos con ``available > 0``.
        """
        self.ensure_one()
        remaining = float_round(nominal_m3 or 0.0, precision_digits=3)
        proposal = []
        Imputation = self.env['madenat.sv.imputation']
        data = Imputation._i2_sv_candidate_data(
            processor=self.processor_id, processed_lots=processed_lots)
        for item in data:
            if remaining <= 0:
                break
            take = min(remaining, item['available'])
            if take <= 0:
                continue
            proposal.append(
                (item['lot'], float_round(take, precision_digits=3)))
            remaining -= take
        return proposal

    @api.model
    def _i2_line_vals(self, lot):
        nominal = self.env['madenat.sv.imputation']._i2_lot_nominal_m3(lot)
        return {'processed_lot_id': lot.id, 'nominal_volume_m3': nominal}

    def action_propose_fifo(self):
        """Rellena (o rehace) el reparto SV de las etiquetas SELECCIONADAS.

        No incluye etiquetas no seleccionadas (D4/D5): la propuesta es un acto
        explícito del usuario sobre su selección.
        """
        for wiz in self:
            selected = wiz.line_ids.filtered('selected')
            if not selected:
                raise UserError(_(
                    'Seleccione al menos una etiqueta antes de proponer un '
                    'reparto.'))
            # Borra sólo el reparto de las etiquetas SELECCIONADAS; conserva el
            # reparto de las no seleccionadas (p. ej. a otros SV).
            commands = [(2, alloc.id) for alloc in wiz.sv_line_ids.filtered(
                lambda a: a.wizard_line_id in selected)]
            for wline in selected:
                for sv, vol in wiz._i2_propose_fifo(
                        wline.nominal_volume_m3, wline.processed_lot_id):
                    commands.append((0, 0, {
                        'wizard_line_id': wline.id,
                        'sv_lot_id': sv.id,
                        'imputed_volume_m3': vol,
                    }))
            wiz.sv_line_ids = commands
        return True

    def action_select_all(self):
        """Marca todas las candidatas disponibles como incluidas (elección expresa).

        P2: Limita la selección a etiquetas disponibles (asignables). Si alguna etiqueta
        se omite por falta de saldo, devuelve display_notification de advertencia.
        """
        omitted = 0
        for wiz in self:
            assignable = wiz.line_ids.filtered('asignable')
            unassignable = wiz.line_ids - assignable
            assignable.write({'selected': True})
            omitted += len(unassignable)
        if omitted > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Selección parcial de etiquetas'),
                    'message': _('%d etiqueta(s) omitida(s) por falta de saldo documental (ver pestaña «Sin disponibilidad»).') % omitted,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return True

    @api.model
    def _i2_valid_sv(self, sv_lot):
        """True si ``sv_lot`` es una etiqueta SV válida (Lote Volumen)."""
        return bool(sv_lot and sv_lot.lot_flow_type == 'volume')

    def action_assign_selected(self):
        """Prepara el reparto de las etiquetas SELECCIONADAS hacia el SV de trabajo.

        Acción **explícita** (Bloque de asignación): crea una línea de reparto por
        etiqueta seleccionada con el SV de trabajo **y volumen 0** — el usuario
        debe introducir o confirmar el volumen (o usar «Usar disponible»). **No**
        aplica, **no** mueve stock, **no** crea otro documento. No duplica filas
        existentes, no sobrescribe cantidades ya editadas y **no** borra repartos
        a otros SV.
        """
        for wiz in self:
            if not wiz._i2_valid_sv(wiz.sv_lot_id):
                raise UserError(_(
                    'Seleccione la etiqueta SV de trabajo antes de asignar las '
                    'etiquetas seleccionadas.'))
            selected = wiz.line_ids.filtered('selected')
            if not selected:
                raise UserError(_(
                    'Seleccione al menos una etiqueta para asignarla al SV de '
                    'trabajo.'))
            existing = {
                (alloc.wizard_line_id.id, alloc.sv_lot_id.id)
                for alloc in wiz.sv_line_ids}
            commands = []
            for line in selected:
                if (line.id, wiz.sv_lot_id.id) in existing:
                    continue  # no duplica ni sobrescribe
                commands.append((0, 0, {
                    'wizard_line_id': line.id,
                    'sv_lot_id': wiz.sv_lot_id.id,
                    'imputed_volume_m3': 0.0,
                }))
            if commands:
                wiz.sv_line_ids = commands  # agrega; conserva el resto
        return True

    def action_use_available(self):
        """Rellena **explícitamente** el volumen disponible documental por etiqueta.

        Alcance: las filas de reparto hacia el **SV de trabajo** cuya etiqueta
        está **seleccionada** (mismo comportamiento en ambas pestañas). Cantidad
        = ``min(disponible documental de la etiqueta, nominal comprometido de la
        línea)`` (≥ 0). **No sobrescribe** una cantidad ya escrita por el usuario:
        sólo rellena las filas aún en cero. Es una acción expresa y visible;
        **no** aplica ni mueve stock.
        """
        for wiz in self:
            if not wiz._i2_valid_sv(wiz.sv_lot_id):
                raise UserError(_(
                    'Seleccione la etiqueta SV de trabajo antes de usar la '
                    'disponibilidad.'))
            Imputation = self.env['madenat.sv.imputation']
            for alloc in wiz.sv_line_ids.filtered(
                    lambda a: a.sv_lot_id == wiz.sv_lot_id
                    and a.wizard_line_id.selected):
                # Respeta lo editado: no pisa una cantidad positiva existente.
                if float_compare(
                        alloc.imputed_volume_m3, 0.0,
                        precision_rounding=I2_VOLUME_PRECISION) > 0:
                    continue
                line = alloc.wizard_line_id
                lot = line.processed_lot_id
                available = Imputation._i2_lot_available_for_m3(
                    lot, exclude_imputation=wiz.imputation_id) if lot else 0.0
                alloc.imputed_volume_m3 = max(
                    0.0, min(available, line.nominal_volume_m3 or 0.0))
        return True

    def action_clear_selection(self):
        """Quita la selección y descarta la selección transitoria de reparto.

        Es una acción **explícita** (D5/Bloque D): no borra historia aplicada;
        sólo descarta la propuesta transitoria del asistente.
        """
        for wiz in self:
            wiz.line_ids.write({'selected': False})
            wiz.sv_line_ids = [(5, 0, 0)]
        return True

    # ── Construcción del documento ───────────────────────────────────────
    def _i2_signature(self):
        """Firma DETERMINISTA de la operación preparada (S1, FASE 10).

        Incluye las **etiquetas incluidas** (marcadas o con reparto, D4/D5) con
        su volumen nominal, **además** de los repartos SV. Así la clave
        documental identifica *qué* se registra, no sólo *a qué SV*: dos
        preparaciones con selecciones distintas de la misma guía no colisionan
        entre sí ni con un documento aplicado/terminal previo (defecto F1).

        La firma SÓLO se usa para construir claves NUEVAS: los documentos ya
        creados conservan su ``documentary_key`` (no se recalcula ni migra).
        """
        self.ensure_one()
        parts = []
        for wline in self._i2_included_lines().sorted('processed_lot_id'):
            parts.append('L%s:%.3f' % (
                wline.processed_lot_id.id, wline.nominal_volume_m3 or 0.0))
        for wline in self.line_ids.sorted('processed_lot_id'):
            for alloc in wline.sv_alloc_ids.sorted('sv_lot_id'):
                parts.append('%s:%s:%.3f' % (
                    wline.processed_lot_id.id, alloc.sv_lot_id.id,
                    alloc.imputed_volume_m3 or 0.0))
        return '|'.join(parts)

    def _i2_included_lines(self):
        """Líneas incluidas: marcadas O con reparto explícito (D4/D5)."""
        self.ensure_one()
        return self.line_ids.filtered(
            lambda l: l.selected or l.sv_alloc_ids)

    def _i2_build_imputation(self):
        """Crea/actualiza la imputación de trabajo SIN perder el borrador.

        Bloque D: reconciliación por ``processed_lot_id`` y por
        ``(línea, SV)`` (**upsert**), en lugar de borrar y recrear. Conserva las
        referencias del reparto, no duplica líneas, respeta la **selección**
        explícita y no toca documentos aplicados.
        """
        self.ensure_one()
        Imputation = self.env['madenat.sv.imputation']
        # Revalida la elegibilidad ANTES de crear/modificar el documento: una
        # guía que dejó de ser elegible entre la apertura y el guardado se
        # rechaza sin dejar documentos ni estados parciales (§19.16).
        Imputation._i2_check_guia_is_eligible_return(
            self.guia_processing_id)
        # S3 (FASE 10, 2026-10-15): NO se persiste un documento de rebaja VACÍO
        # —ni se borran en silencio las líneas ya registradas— exigiendo al
        # menos UNA etiqueta incluida (marcada O con reparto explícito, D4/D5).
        # La comprobación va ANTES de crear/actualizar: un guardado rechazado no
        # deja documento nuevo ni pierde líneas. Los flujos legítimos (anular,
        # «Volver a borrador», reabrir) no pasan por aquí y siguen intactos.
        included = self._i2_included_lines()
        if not included:
            raise UserError(_(
                'No se puede guardar un documento de rebaja sin etiquetas. '
                'Selecciona al menos una etiqueta (o asigna un destino SV con '
                'cantidad) antes de guardar; no se admiten documentos de '
                'rebaja vacíos.'))
        imp = self.imputation_id
        if not (imp and imp.exists()):
            # El asistente se abrió SIN documento vinculado. Si otra sesión creó
            # trabajo para la misma guía, NO se adopta ni sobrescribe en
            # silencio: se muestra su referencia (LOCK-08 / §7).
            existing = Imputation._i2_find_work_for_guia(
                self.guia_processing_id)
            if existing:
                raise UserError(_(
                    'Otra sesión creó un trabajo para la guía %(guia)s '
                    '(%(name)s) mientras este asistente estaba abierto. No se '
                    'reemplaza en silencio. Abre ese documento o usa «Recargar '
                    'versión actual» para continuar.') % {
                        'guia': self.guia_processing_id.name or '',
                        'name': existing.name})
            imp = Imputation._i2_get_or_create(
                self.guia_processing_id, self.processor_id,
                signature=self._i2_signature())
        # 1) ESTADO: un documento anulado/aplicado/reversado no admite
        # preparación. Se comprueba ANTES de la versión para dar el mensaje
        # operativo del estado (RESET-11) y no un conflicto genérico.
        if imp.state not in ('draft', 'pending'):
            if imp.state == 'cancelled':
                raise UserError(_(
                    'El documento %s fue anulado. Vuelve a borrador para '
                    'continuar, si su capacidad sigue disponible.') % imp.name)
            raise UserError(_(
                'La imputación %(name)s ya no admite preparación (estado '
                '%(state)s).') % {'name': imp.name, 'state': imp.state})
        # 2) LOCK (§6): comparación de versión ATÓMICA, ANTES de cualquier
        # escritura de contenido. Sólo cuando el asistente traía un documento
        # (si no, la preparación es una operación nueva). Una edición obsoleta
        # (otra sesión guardó) se rechaza sin sobrescribir ni fusionar.
        if self.imputation_id:
            imp._i2_assert_edit_version(self.expected_edit_version)
        if imp.guia_processing_id != self.guia_processing_id:
            raise UserError(_(
                'No se puede cambiar la guía de una imputación de trabajo ya '
                'vinculada (%(name)s ← %(old)s). Anule el borrador o abra una '
                'operación nueva para la guía %(new)s.') % {
                    'name': imp.name,
                    'old': imp.guia_processing_id.name or '',
                    'new': self.guia_processing_id.name or ''})
        if self.reason:
            imp.reason = self.reason
        # SAVE (2026-10-11): fija/refresca la relación de trabajo con el SV para
        # poder localizar y reabrir el borrador desde el SV (aunque aún no haya
        # reparto positivo).
        if self.sv_lot_id and imp.work_sv_lot_id != self.sv_lot_id:
            imp.work_sv_lot_id = self.sv_lot_id
        # `included` ya se calculó y validó arriba (S3): no se recalcula.
        existing_by_lot = {l.processed_lot_id.id: l for l in imp.line_ids}
        keep_line_ids = set()
        for wline in included:
            line = existing_by_lot.get(wline.processed_lot_id.id)
            line_vals = {
                'nominal_volume_m3': wline.nominal_volume_m3,
                'pieces': wline.pieces,
            }
            nominal_up = True
            if line:
                nominal_up = float_compare(
                    wline.nominal_volume_m3, line.nominal_volume_m3,
                    precision_rounding=I2_VOLUME_PRECISION) >= 0
                if nominal_up:
                    line.write(line_vals)
            else:
                line = imp.line_ids.create(dict(
                    line_vals, imputation_id=imp.id,
                    processed_lot_id=wline.processed_lot_id.id))
            keep_line_ids.add(line.id)
            existing_alloc = {
                a.sv_lot_id.id: a for a in line.sv_allocation_ids}
            keep_alloc_ids = set()
            for alloc in wline.sv_alloc_ids:
                # SAVE-05 (2026-10-11): una fila con cantidad 0 es un DESTINO
                # PREVISTO sin cantidad. NO se persiste como reparto (el reparto
                # exige volumen > 0) pero TAMPOCO bloquea el guardado: se
                # conserva la línea/etiqueta y el resto de repartos. Una cantidad
                # NEGATIVA sí se rechaza (no es «sin cantidad»).
                if float_compare(
                        alloc.imputed_volume_m3, 0.0,
                        precision_rounding=I2_VOLUME_PRECISION) < 0:
                    raise UserError(_(
                        'La cantidad a asignar no puede ser negativa '
                        '(%(lot)s → %(sv)s).') % {
                        'lot': wline.processed_lot_id.name or '',
                        'sv': alloc.sv_lot_id.name or ''})
                if float_compare(
                        alloc.imputed_volume_m3, 0.0,
                        precision_rounding=I2_VOLUME_PRECISION) == 0:
                    continue
                sline = existing_alloc.get(alloc.sv_lot_id.id)
                if sline:
                    if float_compare(
                            sline.imputed_volume_m3, alloc.imputed_volume_m3,
                            precision_rounding=I2_VOLUME_PRECISION) != 0:
                        sline.write({
                            'imputed_volume_m3': alloc.imputed_volume_m3})
                else:
                    sline = line.sv_allocation_ids.create({
                        'imputation_id': imp.id,
                        'imputation_line_id': line.id,
                        'sv_lot_id': alloc.sv_lot_id.id,
                        'imputed_volume_m3': alloc.imputed_volume_m3,
                    })
                keep_alloc_ids.add(sline.id)
            line.sv_allocation_ids.filtered(
                lambda a: a.id not in keep_alloc_ids).unlink()
            # Un nominal reducido se escribe DESPUÉS de ajustar el reparto, para
            # no bloquear una edición coherente (nominal + reparto juntos).
            if line and not nominal_up:
                line.write(line_vals)
        # Elimina sólo líneas de trabajo (draft/pending) no incluidas.
        imp.line_ids.filtered(
            lambda l: l.id not in keep_line_ids).unlink()
        self.imputation_id = imp.id
        # Bloque B (CANON/19 §19.11): sincroniza las relaciones envío↔retorno
        # seleccionadas (en borrador; se registran al aplicar).
        imp._sync_return_links(self.shipment_picking_ids)
        return imp

    # ── Acciones ─────────────────────────────────────────────────────────
    def _i2_guarded_build(self):
        """Ejecuta ``_i2_build_imputation`` de forma ATÓMICA frente a
        concurrencia: fuerza el flush dentro de la transacción, actualiza la
        versión esperada del asistente tras un guardado EXITOSO (para que
        Guardar→Continuar→Guardar no dé falso conflicto, LOCK-10) y traduce un
        ``SerializationFailure`` de PostgreSQL (carrera entre la comparación y la
        escritura) al MISMO mensaje operativo de conflicto (LOCK-16)."""
        try:
            imp = self._i2_build_imputation()
            self.env.flush_all()
        except SerializationFailure:
            raise UserError(_(I2_CONFLICT_MSG) % {
                'name': (self.imputation_id.name or '')})
        imp.invalidate_recordset(['edit_version'])
        self.expected_edit_version = imp.edit_version or 1
        return imp

    def action_prepare(self):
        """«Guardar borrador»: crea/actualiza el documento y **permanece** en el
        asistente mostrando la referencia real (UI‑02 / SAVE‑04)."""
        imp = self._i2_guarded_build()
        self._i2_notify_saved(imp)
        return self._i2_stay()

    def action_pending(self):
        imp = self._i2_guarded_build()
        imp.action_pending()
        self.expected_edit_version = imp.edit_version or 1
        self._i2_notify_saved(imp)
        return self._i2_stay()

    def action_apply(self):
        """«Aplicar»: crea/actualiza el documento, aplica la rebaja y
        **permanece** en la misma ventana. No exige «Preparar asignación» ni
        Guardar previo ni abrir el documento persistente.

        Idempotente: si el trabajo ya está aplicado, repetir «Aplicar» es un
        no-op controlado (no duplica ni consume dos veces)."""
        if self.imputation_id and self.imputation_id.state == 'applied':
            self._i2_notify_applied(self.imputation_id)
            return self._i2_stay()
        imp = self._i2_guarded_build()
        imp.action_apply()
        self.expected_edit_version = imp.edit_version or 1
        # Bloque B/C (CANON/19 §19.11): registra (draft → linked) las
        # relaciones envío↔retorno confirmadas al aplicar la imputación.
        imp.action_link_return_links()
        self._i2_notify_applied(imp)
        return self._i2_stay()

    def action_open_document(self):
        """Abre el documento persistente ya guardado (mantenimiento)."""
        self.ensure_one()
        if not self.imputation_id:
            raise UserError(_(
                'Todavía no hay un documento guardado para esta guía. Use '
                '«Guardar borrador».'))
        return self._i2_open(self.imputation_id)

    def action_wizard_reopen(self):
        """«Volver a borrador» desde el asistente (cancelled → draft).

        Reutiliza la transición controlada del documento; reconstruye la
        selección/reparto y permanece en la misma ventana. No aplica la rebaja.
        """
        self.ensure_one()
        if not self.imputation_id:
            raise UserError(_('No hay documento anulado que reabrir.'))
        imp = self.imputation_id
        if imp.state == 'draft':
            return self._i2_stay()            # idempotente
        if imp.state != 'cancelled':
            raise UserError(_(
                'Sólo un documento anulado puede volver a borrador.'))
        reason = (self.reopen_reason or '').strip()
        if not reason:
            raise UserError(_('Indique el motivo de la reapertura.'))
        # A-1 (FASE 11): el motivo ya NO se escribe en el documento por la vía
        # pública (es marca de transición protegida). Se pasa como PARÁMETRO a
        # la acción oficial, que lo congela en `reopen_reason` junto con el
        # usuario y la fecha.
        imp.action_reopen_to_draft(reason=reason)
        self.expected_edit_version = imp.edit_version or 1
        # Reconstruye la representación desde el documento reabierto.
        self.line_ids = [(5, 0, 0)]
        self.sv_line_ids = [(5, 0, 0)]
        self.line_ids = self._i2_reconstruct_commands(imp)
        self.apply_result = False
        self.save_result = _(
            'Documento %(name)s reabierto como borrador. Motivo: %(reason)s. '
            'Se restablecen las reservas previstas de borrador.') % {
            'name': imp.name, 'reason': reason}
        return self._i2_stay()

    def action_reload_current(self):
        """«Recargar versión actual» (LOCK-09/§9): reconstruye la representación
        desde el documento VIGENTE y actualiza la versión esperada. Descarta los
        cambios locales NO guardados (el usuario lo confirma en el cliente). No
        crea ni modifica documentos, reservas ni saldos."""
        self.ensure_one()
        Imputation = self.env['madenat.sv.imputation']
        imp = self.imputation_id
        if not imp or not imp.exists():
            imp = Imputation._i2_find_work_for_guia(self.guia_processing_id)
        self.line_ids = [(5, 0, 0)]
        self.sv_line_ids = [(5, 0, 0)]
        self.apply_result = False
        if imp and imp.state in ('draft', 'pending'):
            self.imputation_id = imp.id
            self.expected_edit_version = imp.edit_version or 1
            if imp.reason:
                self.reason = imp.reason
            self.line_ids = self._i2_reconstruct_commands(imp)
            self.save_result = _(
                'Versión vigente de %(name)s recargada (v%(v)s).') % {
                    'name': imp.name, 'v': imp.edit_version or 1}
        else:
            self.imputation_id = False
            self.expected_edit_version = 0
            self.save_result = _(
                'No hay trabajo en preparación para esta guía.')
        return self._i2_stay()

    def action_discard_changes(self):
        """«Descartar y volver»: descarta los cambios **no guardados** y vuelve
        al SV. NO elimina el documento ya guardado ni libera reservas (el
        asistente es transitorio; el documento persistente vive aparte)."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'madenat_lumber_logistics.action_madenat_sv_assignment')
        if self.sv_lot_id:
            action['res_id'] = self.sv_lot_id.id
            action['view_mode'] = 'form'
            action['views'] = [(
                self.env.ref(
                    'madenat_lumber_logistics.view_madenat_sv_assignment_form'
                ).id, 'form')]
        action['target'] = 'current'
        return action

    def _i2_notify_saved(self, imputation):
        """Confirmación con referencia real y estado (SAVE‑04)."""
        self.apply_result = False
        self.save_result = _(
            'Borrador %(name)s guardado. No se ha aplicado la rebaja. Las '
            'etiquetas seleccionadas mantienen la reserva documental prevista '
            '(estado: %(state)s).') % {
            'name': imputation.name, 'state': imputation.state}

    def _i2_notify_applied(self, imputation):
        """Resultado de la aplicación en la MISMA ventana (SIMPLE‑14)."""
        total = sum(imputation.sv_line_ids.filtered(
            lambda s: s.sv_lot_id == self.sv_lot_id
        ).mapped('imputed_volume_m3'))
        self.save_result = False
        self.apply_result = _(
            'Rebaja %(name)s aplicada · %(total).3f m³ hacia %(sv)s. '
            'Estado: %(state)s.') % {
            'name': imputation.name, 'total': total,
            'sv': self.sv_lot_id.name or '—', 'state': imputation.state}

    def _i2_stay(self):
        """Recarga el propio asistente (no navega al documento) para mostrar la
        referencia y las acciones de mantenimiento."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrar rebaja'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _i2_open(self, imputation):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrar rebaja'),
            'res_model': 'madenat.sv.imputation',
            'res_id': imputation.id,
            'view_mode': 'form',
            'target': 'current',
        }


class MadenatSvImputationWizardLine(models.TransientModel):
    _name = 'madenat.sv.imputation.wizard.line'
    _description = 'Etiqueta en asistente de imputación (I2)'

    wizard_id = fields.Many2one(
        'madenat.sv.imputation.wizard', required=True, ondelete='cascade')
    processed_lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta procesada', required=True,
        domain="[('lot_flow_type', '!=', 'volume')]")
    selected = fields.Boolean(
        string='Incluir', default=True,
        help='Marque las etiquetas que forman parte de la asignación (D4). Al '
             'abrir una operación nueva las etiquetas NO se incluyen '
             'automáticamente; el usuario selecciona todas o algunas.')
    nominal_volume_m3 = fields.Float(
        string='Volumen nominal (m³)', digits=(16, 3), required=True)
    pieces = fields.Integer(string='Piezas')
    etiqueta_label_proveedor = fields.Char(
        related='processed_lot_id.external_labels',
        string='Etiqueta proveedor', store=False)
    # ── Presentación del material (referencia «DETALLE DEL PACKING LIST») ──
    #    Etiqueta = ref del lote; SKU y dimensiones declaradas = línea de
    #    packing asociada por la MISMA regla de promoción
    #    (`name = etiqueta + SKU + dígitos de la guía`). No se corta el nombre.
    packing_line_id = fields.Many2one(
        'madenat.guia.processing.line', string='Línea de packing',
        compute='_compute_packing_line', store=False)
    etiqueta_ref = fields.Char(
        related='processed_lot_id.ref', string='Etiqueta (ref)', store=False)
    etiqueta = fields.Char(
        string='Etiqueta', compute='_compute_packing_line', store=False,
        help='Etiqueta LIMPIA del packing list (no el nombre concatenado del '
             'lote). Si no hay coincidencia de packing, se usa la referencia '
             'interna del lote y, en último caso, su nombre técnico.')
    asignable = fields.Boolean(
        string='Asignable', compute='_compute_asignable', store=False,
        help='Indica si la etiqueta tiene saldo documental disponible para ser asignada.')
    medidas = fields.Char(
        string='Medidas', compute='_compute_medidas', store=False,
        help='Medidas técnicas legibles: espesor × ancho (mm) · largo (m). '
             'Permiten distinguir lotes con la misma etiqueta visible.')
    disponibilidad_estado = fields.Selection(
        selection=[
            ('available', 'Disponible'),
            ('applied', 'Aplicado'),
            ('reserved', 'Reservado'),
            ('no_capacity', 'Sin capacidad documental'),
            ('other', 'Sin disponibilidad'),
        ],
        string='Estado disponibilidad',
        compute='_compute_disponibilidad_estado', store=False,
        help='Causa REAL del saldo documental cero, derivada de los saldos '
             '(aplicado/reservado/sin capacidad). No se infiere de la simple '
             'vista del 0,000.')
    sku_origen = fields.Char(
        related='packing_line_id.sku_original', string='SKU origen',
        store=False)
    lote_interno = fields.Char(
        related='processed_lot_id.name', string='Lote interno', store=False)
    producto_id = fields.Many2one(
        related='processed_lot_id.product_id', string='Producto', store=False)
    subproducto_id = fields.Many2one(
        related='processed_lot_id.subproducto_id', string='Subproducto',
        store=False)
    espesor_mm = fields.Float(
        related='processed_lot_id.espesor_mm', string='Espesor (mm)',
        digits=(10, 3), store=False)
    ancho_mm = fields.Float(
        related='processed_lot_id.ancho_mm', string='Ancho (mm)',
        digits=(10, 3), store=False)
    largo_m = fields.Float(
        related='processed_lot_id.largo_m', string='Largo (m)',
        digits=(10, 3), store=False)
    espesor_declarado_mm = fields.Float(
        related='packing_line_id.espesor_nominal_mm',
        string='Espesor declarado (mm)', digits=(10, 3), store=False)
    ancho_declarado_mm = fields.Float(
        related='packing_line_id.ancho_nominal_mm',
        string='Ancho declarado (mm)', digits=(10, 3), store=False)
    largo_declarado_m = fields.Float(
        related='packing_line_id.largo_nominal_m',
        string='Largo declarado (m)', digits=(10, 3), store=False)
    piezas_lote = fields.Integer(
        related='processed_lot_id.piezas', string='Piezas', store=False)
    volumen_documental_m3 = fields.Float(
        related='processed_lot_id.volume_purchase_m3',
        string='Volumen documental (m³)', digits=(16, 3), store=False)
    volumen_embarque_m3 = fields.Float(
        related='processed_lot_id.vol_shipment_m3',
        string='Volumen embarque (m³)', digits=(16, 3), store=False)
    etiqueta_nominal_m3 = fields.Float(
        string='Nominal referencia (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    etiqueta_aplicado_m3 = fields.Float(
        string='Rebajado etiqueta aplicado (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos',
        help='Volumen NOMINAL de esta etiqueta ya comprometido en documentos '
             'APLICADOS (lado etiqueta). No es el reparto al SV: el reparto al '
             'SV se ve en «Asignación a SV».')
    etiqueta_reservado_m3 = fields.Float(
        string='Reservado borrador/pend. (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    etiqueta_disponible_m3 = fields.Float(
        string='Disponible para esta operación (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    etiqueta_pendiente_m3 = fields.Float(
        string='Pendiente de reparto (m³)', digits=(16, 3),
        compute='_compute_etiqueta_pendiente',
        help='Nominal comprometido de esta línea menos lo ya repartido en este '
             'documento (a cualquier SV).')
    etiqueta_saldo_documental_m3 = fields.Float(
        string='Saldo documental etiqueta (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    sv_alloc_ids = fields.One2many(
        'madenat.sv.imputation.wizard.sv.line', 'wizard_line_id',
        string='Reparto SV')
    cantidad_asignar_m3 = fields.Float(
        string='A asignar (m³)', digits=(16, 3),
        compute='_compute_cantidad_asignar',
        inverse='_inverse_cantidad_asignar', store=False,
        help='Volumen de ESTA etiqueta hacia el SV de trabajo. Es EDITABLE: '
             'escribe aquí los m³ y se integra con el mismo reparto '
             '«Asignación a SV» (no crea un saldo paralelo y no borra repartos '
             'a otros SV).')
    # ── Causa concreta y trazable del saldo documental (AUD-ETQ-04, §15) ───
    #    No se usa «aplicado/reservado/sin capacidad» como sustituto: se nombra
    #    el/los documentos que explican el saldo y se ofrece acceso a ellos.
    disponibilidad_detalle = fields.Char(
        string='Causa del saldo', compute='_compute_disponibilidad_detalle',
        store=False,
        help='Explicación concreta (documento y volumen) de por qué la '
             'etiqueta no tiene disponibilidad documental. Trazable y '
             'consultable; no reemplaza a los documentos que la explican.')
    disponibilidad_imputacion_ids = fields.Many2many(
        'madenat.sv.imputation', string='Documentos que consumen la etiqueta',
        compute='_compute_disponibilidad_detalle', store=False,
        help='Imputaciones vigentes (borrador/pendiente/aplicada) que consumen '
             'la capacidad documental de esta etiqueta, excluyendo el '
             'documento en curso.')
    disponibilidad_documentos_count = fields.Integer(
        string='N° documentos que explican el saldo',
        compute='_compute_disponibilidad_detalle', store=False)

    @api.model
    def _i2_build_packing_map(self, guia):
        """Mapa ``nombre-de-lote → línea de packing`` por la regla de promoción.

        La promoción concatena ``lot_name + SKU + dígitos de la guía`` en el
        ``name`` del ``stock.lot``; aquí se reconstruye el mismo texto para
        asociar la línea del packing list. Si **dos** líneas producen la misma
        clave (colisión del mapa), la clave se marca **ambigua** y no se asocia
        ninguna: no se elige una línea arbitrariamente (AUD-ETQ-03).
        """
        digits = re.sub(r'[^0-9]', '', guia.name or '')
        mapping = {}
        ambiguous = set()
        for pl in guia.processing_line_ids:
            expected = ' '.join(p for p in (
                (pl.lot_name or '').strip(),
                (pl.sku_original or '').strip(),
                digits) if p)
            if not expected:
                continue
            if expected in mapping and mapping[expected] != pl:
                ambiguous.add(expected)
            mapping[expected] = pl
        return mapping, ambiguous

    def _compute_packing_line(self):
        """Línea de packing (SKU/dimensiones declaradas) del lote procesado.

        Se asocia por la MISMA regla con que se promovió el lote
        (``name = etiqueta + SKU + dígitos de la guía``). No se corta el nombre
        del lote; si no hay coincidencia honesta, queda vacío (se muestra «—»).
        El mapa se construye una vez por guía (lectura agrupada). Una **colisión
        del mapa** (dos líneas con la misma clave) NO se resuelve eligiendo una
        al azar: la asociación queda vacía (AUD-ETQ-03).

        Además resuelve la **etiqueta limpia** (``etiqueta``): el ``lot_name``
        del packing (etiqueta de proveedor), sin el nombre concatenado del lote.
        Si no hay coincidencia, cae a la referencia del lote, a las etiquetas
        externas y, en último caso, al nombre técnico.
        """
        maps = {}
        for line in self:
            guia = line.wizard_id.guia_processing_id
            lot = line.processed_lot_id
            line.packing_line_id = False
            line.etiqueta = (
                (lot.ref or '') or (lot.external_labels or '')
                or (lot.name or '')) if lot else ''
            if not lot or not guia:
                continue
            if guia.id not in maps:
                maps[guia.id] = self._i2_build_packing_map(guia)
            mapping, ambiguous = maps[guia.id]
            key = (lot.name or '').strip()
            if key and key not in ambiguous:
                line.packing_line_id = mapping.get(key)
            if line.packing_line_id and line.packing_line_id.lot_name:
                line.etiqueta = line.packing_line_id.lot_name.strip()

    @api.depends('sv_alloc_ids.imputed_volume_m3', 'sv_alloc_ids.sv_lot_id',
                 'wizard_id.sv_lot_id')
    def _compute_cantidad_asignar(self):
        for line in self:
            sv = line.wizard_id.sv_lot_id
            alloc = line.sv_alloc_ids.filtered(lambda a: a.sv_lot_id == sv)
            line.cantidad_asignar_m3 = sum(
                alloc.mapped('imputed_volume_m3'))

    @api.depends('nominal_volume_m3', 'sv_alloc_ids.imputed_volume_m3')
    def _compute_etiqueta_pendiente(self):
        for line in self:
            line.etiqueta_pendiente_m3 = max(
                0.0, (line.nominal_volume_m3 or 0.0)
                - sum(line.sv_alloc_ids.mapped('imputed_volume_m3')))

    @api.depends('processed_lot_id', 'wizard_id.imputation_id')
    def _compute_etiqueta_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for line in self:
            lot = line.processed_lot_id
            current = line.wizard_id.imputation_id
            line.etiqueta_nominal_m3 = (
                Imputation._i2_lot_nominal_m3(lot) if lot else 0.0)
            line.etiqueta_aplicado_m3 = (
                Imputation._i2_lot_applied_m3(lot) if lot else 0.0)
            line.etiqueta_reservado_m3 = (
                Imputation._i2_lot_reserved_m3(
                    lot, exclude_imputation=current) if lot else 0.0)
            line.etiqueta_disponible_m3 = (
                Imputation._i2_lot_available_for_m3(
                    lot, exclude_imputation=current) if lot else 0.0)
            line.etiqueta_saldo_documental_m3 = (
                Imputation._i2_lot_documental_available_m3(lot) if lot else 0.0)

    @api.depends('espesor_mm', 'ancho_mm', 'largo_m')
    def _compute_medidas(self):
        for line in self:
            line.medidas = self._i2_format_medidas(
                line.espesor_mm, line.ancho_mm, line.largo_m)

    @api.model
    def _i2_format_medidas(self, espesor_mm, ancho_mm, largo_m):
        """Medidas legibles: «45 × 125 mm · 2,900 m» (decimal es-ES).

        Los mm se muestran sin ceros sobrantes; el largo con 3 decimales fijos
        (misma precisión que los m³). Es presentación, no cálculo de negocio.
        """
        def trim(value):
            txt = '%.3f' % (value or 0.0)
            if '.' in txt:
                txt = txt.rstrip('0').rstrip('.')
            return (txt or '0').replace('.', ',')

        def fixed(value):
            return ('%.3f' % (value or 0.0)).replace('.', ',')

        parts = []
        if espesor_mm or ancho_mm:
            parts.append('%s × %s mm' % (trim(espesor_mm), trim(ancho_mm)))
        if largo_m:
            parts.append('%s m' % fixed(largo_m))
        return ' · '.join(parts)

    @api.depends('processed_lot_id', 'wizard_id.imputation_id',
                 'nominal_volume_m3', 'etiqueta_nominal_m3',
                 'etiqueta_aplicado_m3', 'etiqueta_reservado_m3',
                 'etiqueta_disponible_m3')
    def _compute_disponibilidad_estado(self):
        """Causa real del saldo documental (no se inventa: se deriva)."""
        for line in self:
            if float_compare(line.etiqueta_disponible_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                line.disponibilidad_estado = 'available'
            elif float_compare(line.etiqueta_aplicado_m3, 0.0,
                               precision_rounding=I2_VOLUME_PRECISION) > 0:
                line.disponibilidad_estado = 'applied'
            elif float_compare(line.etiqueta_reservado_m3, 0.0,
                               precision_rounding=I2_VOLUME_PRECISION) > 0:
                line.disponibilidad_estado = 'reserved'
            elif float_compare(line.etiqueta_nominal_m3, 0.0,
                               precision_rounding=I2_VOLUME_PRECISION) <= 0:
                line.disponibilidad_estado = 'no_capacity'
            else:
                line.disponibilidad_estado = 'other'

    @api.depends('disponibilidad_estado')
    def _compute_asignable(self):
        for line in self:
            line.asignable = (line.disponibilidad_estado == 'available')

    # Etiquetas legibles de los estados I2 para el detalle de disponibilidad.
    _I2_STATE_LABELS = {
        'draft': 'borrador',
        'pending': 'pendiente',
        'applied': 'aplicada',
    }

    @api.depends('processed_lot_id', 'wizard_id.imputation_id',
                 'etiqueta_disponible_m3')
    def _compute_disponibilidad_detalle(self):
        """Causa concreta del saldo: documento(s) y volumen que lo consumen.

        Deriva de los saldos documentales reales (no de la simple vista del
        0,000) y expone las imputaciones que consumen la etiqueta para poder
        abrirlas (AUD-ETQ-04, §15). No crea ni modifica documentos.
        """
        Line = self.env['madenat.sv.imputation.line']
        for line in self:
            lot = line.processed_lot_id
            current = line.wizard_id.imputation_id
            line.disponibilidad_detalle = ''
            line.disponibilidad_imputacion_ids = False
            line.disponibilidad_documentos_count = 0
            if not lot:
                continue
            if float_compare(line.etiqueta_disponible_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                line.disponibilidad_detalle = _(
                    'Disponible: %.3f m³ de %.3f m³ nominales.') % (
                        line.etiqueta_disponible_m3, line.etiqueta_nominal_m3)
                continue
            domain = [('processed_lot_id', '=', lot.id),
                      ('imputation_id.state', 'in',
                       ('draft', 'pending', 'applied'))]
            if current:
                domain.append(('imputation_id', '!=', current.id))
            consuming = Line.search(domain)
            imputations = consuming.mapped('imputation_id')
            line.disponibilidad_imputacion_ids = imputations
            line.disponibilidad_documentos_count = len(imputations)
            if imputations:
                parts = []
                for imp in imputations.sorted(lambda i: (i.state, i.id)):
                    volume = sum(consuming.filtered(
                        lambda c: c.imputation_id == imp
                    ).mapped('nominal_volume_m3'))
                    parts.append('%s (%s, %.3f m³)' % (
                        imp.name, self._I2_STATE_LABELS.get(imp.state, imp.state),
                        volume))
                line.disponibilidad_detalle = _(
                    'Sin disponibilidad: consumida por %s.') % '; '.join(parts)
            elif float_compare(line.etiqueta_nominal_m3, 0.0,
                               precision_rounding=I2_VOLUME_PRECISION) <= 0:
                line.disponibilidad_detalle = _(
                    'Sin capacidad: la etiqueta no tiene volumen nominal '
                    'documental (0 m³).')
            else:
                line.disponibilidad_detalle = _(
                    'Sin disponibilidad documental (sin documento vigente que '
                    'la consuma; revise el volumen nominal).')

    def action_open_consuming_documents(self):
        """Abre los documentos que explican el saldo de esta etiqueta (§15)."""
        self.ensure_one()
        ids = self.disponibilidad_imputacion_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documentos que explican el saldo — %s') % (
                self.processed_lot_id.name or ''),
            'res_model': 'madenat.sv.imputation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', ids)],
            'target': 'current',
        }

    def _inverse_cantidad_asignar(self):
        """«A asignar» editable: integra la cantidad en el reparto del SV de trabajo.

        Escribe en ``sv_alloc_ids`` la fila de ESTA etiqueta hacia el SV de
        trabajo (mismo mecanismo que «Asignación a SV»): crea, actualiza o
        elimina SÓLO esa fila; **no** toca repartos a otros SV ni crea un saldo
        paralelo. Volumen 0 deja sin reparto a esa etiqueta en el SV de trabajo.
        """
        SvLine = self.env['madenat.sv.imputation.wizard.sv.line']
        for line in self:
            wiz = line.wizard_id
            sv = wiz.sv_lot_id
            if not sv:
                continue
            volume = float_round(
                max(0.0, line.cantidad_asignar_m3 or 0.0),
                precision_digits=3)
            allocs = line.sv_alloc_ids.filtered(lambda a: a.sv_lot_id == sv)
            if float_compare(volume, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                if allocs:
                    allocs.unlink()
                continue
            if not line.selected:
                line.selected = True
            if allocs:
                allocs.write({'imputed_volume_m3': volume})
            else:
                SvLine.create({
                    'wizard_id': wiz.id,
                    'wizard_line_id': line.id,
                    'sv_lot_id': sv.id,
                    'imputed_volume_m3': volume,
                })

    @api.onchange('selected')
    def _onchange_selected(self):
        for line in self:
            if not line.selected:
                # Deseleccionar descarta el reparto transitorio de esa etiqueta
                # (sólo la propuesta del asistente; no toca historia aplicada).
                line.sv_alloc_ids = [(5, 0, 0)]


class MadenatSvImputationWizardSvLine(models.TransientModel):
    _name = 'madenat.sv.imputation.wizard.sv.line'
    _description = 'Reparto SV en asistente de imputación (I2)'

    wizard_id = fields.Many2one(
        'madenat.sv.imputation.wizard', string='Asistente',
        ondelete='cascade', index=True)
    wizard_line_id = fields.Many2one(
        'madenat.sv.imputation.wizard.line', string='Etiqueta',
        required=True, ondelete='cascade')
    sv_lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', required=True,
        domain="[('lot_flow_type', '=', 'volume')]")
    imputed_volume_m3 = fields.Float(
        string='Volumen (m³)', digits=(16, 3))
    etiqueta_retorno = fields.Char(
        related='wizard_line_id.processed_lot_id.name',
        string='Etiqueta retorno', store=False)
    etiqueta = fields.Char(
        related='wizard_line_id.etiqueta', string='Etiqueta', store=False)
    medidas = fields.Char(
        related='wizard_line_id.medidas', string='Medidas', store=False)
    sku_origen = fields.Char(
        related='wizard_line_id.sku_origen', string='SKU origen', store=False)
    disponibilidad_estado = fields.Selection(
        related='wizard_line_id.disponibilidad_estado',
        string='Estado disponibilidad', store=False)
    disponibilidad_detalle = fields.Char(
        related='wizard_line_id.disponibilidad_detalle',
        string='Causa del saldo', store=False)
    etiqueta_disponible_m3 = fields.Float(
        string='Disponible (m³)', digits=(16, 3),
        compute='_compute_sv_saldos')
    sv_nominal_m3 = fields.Float(
        string='Nominal SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos')
    sv_saldo_documental_m3 = fields.Float(
        string='Saldo documental SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos')

    @api.depends('sv_lot_id', 'wizard_line_id.processed_lot_id',
                 'wizard_id.imputation_id')
    def _compute_sv_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for sline in self:
            sv = sline.sv_lot_id
            current = sline.wizard_id.imputation_id
            lot = sline.wizard_line_id.processed_lot_id
            sline.etiqueta_disponible_m3 = (
                Imputation._i2_lot_available_for_m3(
                    lot, exclude_imputation=current) if lot else 0.0)
            sline.sv_nominal_m3 = (
                Imputation._i2_sv_nominal_m3(sv) if sv else 0.0)
            sline.sv_saldo_documental_m3 = (
                Imputation._i2_sv_documental_available_m3(sv) if sv else 0.0)
