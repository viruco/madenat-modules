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
from odoo.tools import float_round


class MadenatSvImputationWizard(models.TransientModel):
    _name = 'madenat.sv.imputation.wizard'
    _description = 'Asistente de imputación documental SV (I2)'
    _inherit = ['madenat.deviation.mixin']

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía de procesados', required=True)
    processor_id = fields.Many2one(
        'res.partner', string='Procesador',
        domain="[('is_processor', '=', True)]")
    reason = fields.Text(string='Motivo')
    note = fields.Text(string='Observaciones')
    line_ids = fields.One2many(
        'madenat.sv.imputation.wizard.line', 'wizard_id', string='Etiquetas')
    sv_line_ids = fields.One2many(
        'madenat.sv.imputation.wizard.sv.line', 'wizard_id',
        string='Reparto SV (editable)')
    imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación', readonly=True,
        help='Imputación de trabajo de la guía. Reintentar el asistente no '
             'crea una nueva (idempotencia, AD-91).')
    # Bloque B (CANON/19 §19.11): selección de envíos a procesador que atienden
    # el retorno. Reutiliza el asistente de imputación (no se crea otro).
    shipment_picking_ids = fields.Many2many(
        'stock.picking', string='Envíos a procesador (retorno)',
        help='Envíos elegibles que atienden este retorno. Al guardar se '
             'registran como relaciones de conciliación (borrador) y, al '
             'aplicar, como conciliación registrada (CANON/19 §19.11).')
    eligible_shipment_picking_ids = fields.Many2many(
        'stock.picking', compute='_compute_eligible_shipments',
        string='Envíos elegibles')

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
        return self.env['madenat.guia.processing']

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        guia = self._i2_guia_from_context()
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
            # Precarga los envíos ya relacionados (relaciones de trabajo).
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
        for wiz in self:
            wiz.line_ids = [(5, 0, 0)]
            if not wiz.guia_processing_id:
                continue
            wiz.line_ids = [
                (0, 0, wiz._i2_line_vals(lot))
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
        """Rellena (o rehace) el reparto SV FIFO de cada etiqueta."""
        for wiz in self:
            commands = [(5, 0, 0)]
            for wline in wiz.line_ids:
                for sv, vol in wiz._i2_propose_fifo(
                        wline.nominal_volume_m3, wline.processed_lot_id):
                    commands.append((0, 0, {
                        'wizard_line_id': wline.id,
                        'sv_lot_id': sv.id,
                        'imputed_volume_m3': vol,
                    }))
            wiz.sv_line_ids = commands
        return True

    # ── Construcción del documento ───────────────────────────────────────
    def _i2_signature(self):
        self.ensure_one()
        parts = []
        for wline in self.line_ids.sorted('processed_lot_id'):
            for alloc in wline.sv_alloc_ids.sorted('sv_lot_id'):
                parts.append('%s:%s:%.3f' % (
                    wline.processed_lot_id.id, alloc.sv_lot_id.id,
                    alloc.imputed_volume_m3 or 0.0))
        return '|'.join(parts)

    def _i2_build_imputation(self):
        """Crea (o reutiliza) la imputación de trabajo con sus líneas."""
        self.ensure_one()
        Imputation = self.env['madenat.sv.imputation']
        imp = self.imputation_id or Imputation._i2_get_or_create(
            self.guia_processing_id, self.processor_id,
            signature=self._i2_signature())
        if imp.state not in ('draft', 'pending'):
            raise UserError(_(
                'La imputación %s ya no admite preparación (estado %s).')
                % (imp.name, imp.state))
        if self.reason:
            imp.reason = self.reason
        # Rehacer líneas (solo en draft/pending).
        imp.line_ids.unlink()
        imp.sv_line_ids.unlink()
        for wline in self.line_ids:
            line = imp.line_ids.create({
                'imputation_id': imp.id,
                'processed_lot_id': wline.processed_lot_id.id,
                'nominal_volume_m3': wline.nominal_volume_m3,
                'pieces': wline.pieces,
            })
            for alloc in wline.sv_alloc_ids:
                imp.sv_line_ids.create({
                    'imputation_id': imp.id,
                    'imputation_line_id': line.id,
                    'sv_lot_id': alloc.sv_lot_id.id,
                    'imputed_volume_m3': alloc.imputed_volume_m3,
                })
        self.imputation_id = imp.id
        # Bloque B (CANON/19 §19.11): sincroniza las relaciones envío↔retorno
        # seleccionadas (en borrador; se registran al aplicar).
        imp._sync_return_links(self.shipment_picking_ids)
        return imp

    # ── Acciones ─────────────────────────────────────────────────────────
    def action_prepare(self):
        """Prepara/deja el documento en borrador (sin aplicar)."""
        return self._i2_open(self._i2_build_imputation())

    def action_pending(self):
        imp = self._i2_build_imputation()
        imp.action_pending()
        return self._i2_open(imp)

    def action_apply(self):
        imp = self._i2_build_imputation()
        imp.action_apply()
        # Bloque B/C (CANON/19 §19.11): registra (draft → linked) las
        # relaciones envío↔retorno confirmadas al aplicar la imputación.
        imp.action_link_return_links()
        return self._i2_open(imp)

    def _i2_open(self, imputation):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Imputación documental SV'),
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
    nominal_volume_m3 = fields.Float(
        string='Volumen nominal (m³)', digits=(16, 3), required=True)
    pieces = fields.Integer(string='Piezas')
    etiqueta_nominal_m3 = fields.Float(
        string='Nominal referencia (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    etiqueta_saldo_documental_m3 = fields.Float(
        string='Saldo documental etiqueta (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos')
    sv_alloc_ids = fields.One2many(
        'madenat.sv.imputation.wizard.sv.line', 'wizard_line_id',
        string='Reparto SV')

    @api.depends('processed_lot_id')
    def _compute_etiqueta_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for line in self:
            lot = line.processed_lot_id
            line.etiqueta_nominal_m3 = (
                Imputation._i2_lot_nominal_m3(lot) if lot else 0.0)
            line.etiqueta_saldo_documental_m3 = (
                Imputation._i2_lot_documental_available_m3(lot) if lot else 0.0)


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
    sv_nominal_m3 = fields.Float(
        string='Nominal SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos')
    sv_saldo_documental_m3 = fields.Float(
        string='Saldo documental SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos')

    @api.depends('sv_lot_id')
    def _compute_sv_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for sline in self:
            sv = sline.sv_lot_id
            sline.sv_nominal_m3 = (
                Imputation._i2_sv_nominal_m3(sv) if sv else 0.0)
            sline.sv_saldo_documental_m3 = (
                Imputation._i2_sv_documental_available_m3(sv) if sv else 0.0)
