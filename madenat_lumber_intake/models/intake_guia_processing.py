# -*- coding: utf-8 -*-
"""Fachada de operación para Procesados en Intake.

Este modelo hereda `madenat.guia.processing` DENTRO de `madenat_lumber_intake`
para exponer navegación de retorno al Ingreso de Madera sin modificar el core.
No se añade lógica de negocio: solo un método de UX que devuelve la consola
de intake filtrada por el registro origen actual.
"""
import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from .intake_constants import CONSOLE_ID_OFFSET, HEADER_DECLARED_ORIGIN

_logger = logging.getLogger(__name__)


class MadenatGuiaProcessingIntake(models.Model):
    _inherit = 'madenat.guia.processing'

    intake_direct_stock = fields.Boolean(
        string='Recepción Directa (Intake)',
        default=False,
        help='Guía creada por Intake como recepción directa a stock, sin consumo de materia prima.'
    )

    # Detalle documental editable para Ingreso por Volúmenes (evidencia PDF
    # consultable y corregible, sin dimensiones físicas ni cálculo geométrico).
    volume_detail_line_ids = fields.One2many(
        'madenat.lumber.volume.detail.line', 'guia_id',
        string='Detalle documental PDF'
    )

    # Nivel de detalle aplicado en la recepción (persistido para la regla de
    # volumen para stock de la consola).
    detalle_aplicado = fields.Selection(
        [('line_by_line', 'Línea por Línea'), ('consolidated', 'Consolidado')],
        string='Nivel de detalle aplicado',
        default='consolidated',
        help='Cómo se materializó la recepción física: línea por línea (N '
             'líneas) o consolidado (1 línea). Usado por la consola para '
             'decidir el volumen de stock.',
    )

    # Proveedor documental (emisor) extraído del PDF, separado del partner
    # resuelto en Odoo. Permite mostrar el emisor aunque aún no exista
    # res.partner vinculado (o la resolución quede pendiente).
    supplier_name = fields.Char(
        string='Proveedor documental (nombre)',
        help='Razón social del emisor/proveedor detectada en el PDF.',
    )
    supplier_rut = fields.Char(
        string='Proveedor documental (RUT)',
        help='RUT del emisor/proveedor detectado en el PDF.',
    )
    supplier_source = fields.Char(
        string='Fuente de detección del proveedor',
        help='Cómo se detectó el emisor: membrete (letterhead) o etiqueta '
             'explícita (label).',
    )
    supplier_confidence = fields.Selection(
        [('high', 'Alta'), ('medium', 'Media'), ('low', 'Baja'),
         ('none', 'Sin detección')],
        string='Confianza de detección del proveedor',
        help='Confianza de la extracción del emisor del PDF.',
    )

    # ── Evidencia documental y volumen operativo (Ingreso por Volúmenes) ──
    # Valores originales extraídos por documento. NO se sobrescriben por la
    # edición del usuario: son evidencia de auditoría inmutable de origen.
    volume_pdf_m3 = fields.Float(
        string='Volumen documental PDF (m³)', digits=(16, 3),
        help='Volumen total extraído del PDF (evidencia original).',
    )
    volume_excel_m3 = fields.Float(
        string='Volumen documental Excel (m³)', digits=(16, 3),
        help='Volumen total extraído del Excel (evidencia original).',
    )
    volume_detail_m3 = fields.Float(
        string='Suma detalle documental (m³)', digits=(16, 3),
        compute='_compute_volume_detail_m3',
        help='Suma calculada de las líneas documentales vigentes. '
             'Es EXCLUSIVAMENTE evidencia/control documental: nunca es volumen '
             'oficial, no es respaldo de stock ni de conciliación.',
    )

    # ══════════════════════════════════════════════════════════════════════
    # VOLUMEN OFICIAL (único) DEL INGRESO POR VOLÚMENES
    # ──────────────────────────────────────────────────────────────────────
    # Precedencia canónica — primer valor ESTRICTAMENTE positivo:
    #   1. volume_pdf_m3               → "Guía PDF"
    #   2. volume_excel_m3             → "Packing Excel"
    #   3. packing_volume_declared_m3  → "Packing declarado"
    #   4. Ninguno positivo            → sin volumen oficial disponible.
    #
    # NUNCA se usa como oficial: volume_detail_m3, suma del detalle, suma de
    # líneas de proceso, volume_operational_m3, volumen_declarado_m3,
    # vol_comercial_pdf, vol_comercial, vol_fisico, vol_total_m3, ni valores
    # derivados de stock, conciliación o costos.
    #
    # Fuente única de verdad: la consola y F3.1 consumen get_official_volume_m3().
    # ══════════════════════════════════════════════════════════════════════
    OFFICIAL_VOLUME_SOURCES = (
        ('volume_pdf_m3', 'Guía PDF'),
        ('volume_excel_m3', 'Packing Excel'),
        ('packing_volume_declared_m3', 'Packing declarado'),
    )

    official_volume_m3 = fields.Float(
        string='Volumen oficial de la guía (m³)', digits=(16, 3),
        compute='_compute_official_volume_m3',
        help='Único volumen oficial: total declarado en la Guía/PDF; si no '
             'existe, Packing Excel; si no, Packing declarado. 0,000 cuando '
             'no hay volumen documental oficial.',
    )
    official_volume_source = fields.Char(
        string='Fuente del volumen oficial',
        compute='_compute_official_volume_m3',
        help='Origen del volumen oficial vigente: "Guía PDF", "Packing Excel" '
             'o "Packing declarado". Vacío si no existe volumen oficial.',
    )
    official_vs_detail_diff_m3 = fields.Float(
        string='Diferencia vs volumen oficial (m³)', digits=(16, 3),
        compute='_compute_official_volume_m3',
        help='official_volume_m3 - volume_detail_m3. 0,000 si no hay volumen '
             'oficial disponible.',
    )

    # Volumen operativo aprobado por el usuario: co-existe con las evidencias
    # PDF/Excel/detalle sin pisarlas. Ya NO es la fuente de stock para F3.1
    # (esa es el volumen oficial), pero se conserva como referencia operativa.
    volume_operational_m3 = fields.Float(
        string='Volumen operativo (m³)', digits=(16, 3),
        help='Volumen operativo de referencia aprobado por Operaciones. No es '
             'el volumen oficial ni la fuente de stock de Volúmenes.',
    )
    volume_operational_source = fields.Selection(
        [('pdf', 'PDF'), ('excel', 'Excel'), ('detail', 'Detalle'),
         ('manual', 'Manual')],
        string='Fuente del volumen operativo',
        help='Origen del valor operativo vigente.',
    )
    volume_operational_note = fields.Text(
        string='Nota volumen operativo',
        help='Motivo obligatorio cuando la fuente es manual o el valor fue cambiado.',
    )
    volume_operational_user_id = fields.Many2one(
        'res.users', string='Modificado por',
        help='Usuario que realizó la última modificación del volumen operativo.',
    )
    volume_operational_date = fields.Datetime(
        string='Fecha de modificación operativa',
        help='Fecha/hora de la última modificación del volumen operativo.',
    )

    # ── Conciliación documental PDF–Excel ──
    conciliation_status = fields.Selection(
        [('not_compared', 'Sin contraste'),
         ('auto_matched', 'Conciliado automáticamente'),
         ('matched_with_differences', 'Conciliado con diferencias'),
         ('needs_manual_review', 'Requiere revisión manual'),
         ('incompatible', 'Documentos incompatibles'),
         ('manual_confirmed', 'Confirmado manualmente')],
        string='Estado de conciliación', default='not_compared', required=True,
        help='Resultado de comparar PDF y Excel cuando ambos existen.',
    )
    conciliation_summary = fields.Text(
        string='Resumen de conciliación',
        help='Resumen breve de las diferencias o coincidencias detectadas.',
    )
    conciliation_manual_note = fields.Text(
        string='Motivo de resolución manual',
        help='Comentario obligatorio al confirmar manualmente una conciliación.',
    )
    conciliation_manual_user_id = fields.Many2one(
        'res.users', string='Conciliación confirmada por',
    )
    conciliation_manual_date = fields.Datetime(
        string='Fecha de confirmación manual',
    )

    @api.depends('volume_detail_line_ids', 'volume_detail_line_ids.volume_m3',
                 'volume_detail_line_ids.origin')
    def _compute_volume_detail_m3(self):
        """Suma del detalle documental extraído (PDF/Excel).

        EXCLUYE la fila de cabecera declarada (`origin='header'`): esa fila
        refleja los datos declarados de la cabecera y el VOLUMEN OFICIAL
        VIGENTE, no detalle extraído del documento; sumarla duplicaría el
        volumen de las líneas del PDF/Excel. La exclusión conserva intactos
        `official_vs_detail_diff_m3`, la conciliación documental, el control
        documental interno y la consolidación.
        """
        for rec in self:
            rec.volume_detail_m3 = round(
                sum((line.volume_m3 or 0.0)
                    for line in rec.volume_detail_line_ids
                    if line.origin != HEADER_DECLARED_ORIGIN), 3)

    @api.depends(
        'volume_pdf_m3', 'volume_excel_m3', 'packing_volume_declared_m3',
        'volume_detail_line_ids', 'volume_detail_line_ids.volume_m3',
    )
    def _compute_official_volume_m3(self):
        """Volumen oficial único del Ingreso por Volúmenes (canónico).

        Primer valor ESTRICTAMENTE positivo según `OFFICIAL_VOLUME_SOURCES`:
        `volume_pdf_m3` → `volume_excel_m3` → `packing_volume_declared_m3`.

        Nunca usa como candidato: la suma del detalle documental
        (`volume_detail_m3`), la suma de líneas de proceso, el volumen
        operativo (`volume_operational_m3`), el declarado
        (`volumen_declarado_m3`), el comercial/físico/total
        (`vol_comercial_pdf`, `vol_comercial`, `vol_fisico`, `vol_total_m3`),
        ni valores derivados de stock, conciliación o costos.

        Lectura pura: no escribe, no crea/elimina registros, no valida, no
        toca lotes, stock, pickings, bitácora ni secuencia.
        """
        for rec in self:
            value, source = 0.0, False
            for field_name, label in self.OFFICIAL_VOLUME_SOURCES:
                candidate = float(rec[field_name] or 0.0)
                if float_compare(
                        candidate, 0.0, precision_rounding=0.001) > 0:
                    value, source = candidate, label
                    break
            rec.official_volume_m3 = value
            rec.official_volume_source = source
            rec.official_vs_detail_diff_m3 = (
                round(value - (rec.volume_detail_m3 or 0.0), 3)
                if value > 0 else 0.0)

    def get_official_volume_m3(self):
        """API canónica reutilizable: devuelve (volumen, fuente).

        Retorno exacto: `(official_volume_m3, official_volume_source)`.
        Es la única fuente de verdad del volumen oficial: la consola y el
        flujo F3.1 de envío a stock consumen este resultado y no duplican la
        precedencia. Nunca devuelve detalle, operativo, declarado, stock,
        conciliación ni costos como candidato oficial.
        """
        self.ensure_one()
        return self.official_volume_m3 or 0.0, self.official_volume_source or False

    def _get_or_create_consumption_picking(self):
        self.ensure_one()
        if self.intake_direct_stock:
            return False
        return super()._get_or_create_consumption_picking()

    def _get_intake_console_action(self):
        """Acción canónica de retorno a Ingreso de Madera (FIX 2026-08-21).

        Fuente única de verdad de navegación hacia la consola: evita que
        'name' hardcodeado compita con el breadcrumb de la fachada y que
        cada retorno genere una entrada de historial distinta.
        res_id=CONSOLE_ID_OFFSET+self.id es el id sintético de la vista SQL de
        consola. Sin side effects, escrituras ni búsquedas.
        FIX ACCESO (2026-08-22): ya NO se lee la acción técnica
        ir.actions.act_window (action_madenat_lumber_intake_console) para
        obtener el name, porque Operaciones carece de base.group_system y
        env.ref(...).name generaba AccessError. Se usa 'name' fijo
        'Ingreso de Madera', idéntico al nombre canónico de la acción.
        """
        self.ensure_one()
        console_form_view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ingreso de Madera',
            'res_model': 'madenat.lumber.intake.console',
            'res_id': CONSOLE_ID_OFFSET + self.id,
            # ROLLBACK 2026-08-22: se restaura la fachada/formulario original
            # de Ingreso de Madera (view_mode='form') que el flujo de envío a
            # stock necesita operar. El cambio anterior a 'list,form' (botón
            # "Nuevo") se revierte porque perdía la vista operativa principal.
            # views explícito se mantiene para la client action (doAction).
            'view_mode': 'form',
            'view_id': console_form_view.id,
            'views': [(console_form_view.id, 'form')],
            'target': 'current',
        }

    def action_back_to_intake_console(self):
        """Vuelve a Ingreso de Madera vía acción canónica (FIX 2026-08-21).

        AD-55: el core NO tiene este método; se define por herencia en Intake.
        No toca stock ni lógica de negocio. La acción proviene del helper
        único _get_intake_console_action para evitar nombre/contexto ad hoc.
        """
        self.ensure_one()
        # FIX 2026-08-22: envolver en client action para reemplazar el controller
        # actual (evita breadcrumbs repetidos). El helper canónico se preserva.
        inner = self._get_intake_console_action()
        return {
            'type': 'ir.actions.client',
            'tag': 'madenat_lumber_intake.replace_current_action',
            'params': {'action_to_execute': inner},
        }

    def action_reclassify(self):
        """Abre el wizard de reclasificación de tipo de ingreso (AD-73)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reclasificar Tipo de Ingreso'),
            'res_model': 'madenat.lumber.intake.reclassify.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_source_model': 'madenat.guia.processing',
                'default_source_res_id': self.id,
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # Ingreso por Volúmenes: edición controlada y validación sin geometría
    # ─────────────────────────────────────────────────────────────────────

    def set_volume_operational(self, volume, source, note=None):
        """Edita de forma controlada el volumen operativo (con auditoría).

        Conserva las evidencias originales PDF/Excel/detalle; exige fuente y,
        si es manual o cambia un valor prellenado, un motivo; deja chatter y
        bitácora en madenat.audit.log.
        """
        self.ensure_one()
        volume = float(volume or 0.0)
        if float_compare(volume, 0.0, precision_rounding=0.001) < 0:
            raise ValidationError(_('El volumen operativo no puede ser negativo.'))
        if source not in ('pdf', 'excel', 'detail', 'manual'):
            raise ValidationError(_('Fuente de volumen operativo no válida.'))

        changed = float_compare(
            volume, self.volume_operational_m3 or 0.0,
            precision_rounding=0.001) != 0
        if (source == 'manual' or changed) and not note:
            raise ValidationError(
                _('Debe registrar un motivo/comentario al definir manualmente '
                  'o modificar el volumen operativo.'))

        self.write({
            'volume_operational_m3': volume,
            'volume_operational_source': source,
            'volume_operational_note': note or False,
            'volume_operational_user_id': self.env.user.id,
            'volume_operational_date': fields.Datetime.now(),
        })
        self.message_post(body=_(
            'Volumen operativo actualizado a %.3f m³ (fuente: %s).%s'
        ) % (volume, source, ('\nMotivo: %s' % note) if note else ''))
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.id,
            'action_type': 'volume_operational_update',
            'description': 'Volumen operativo: %.3f m³ (fuente %s). %s'
                           % (volume, source, note or ''),
            'user_id': self.env.user.id,
        })
        return True

    def action_confirm_conciliation(self, note=None):
        """Resolución manual de una conciliación pendiente/incompatible."""
        self.ensure_one()
        if self.conciliation_status not in ('needs_manual_review', 'incompatible'):
            raise UserError(
                _('La conciliación no requiere confirmación manual en este estado.'))
        if not note:
            raise UserError(
                _('Debe registrar un comentario/motivo para confirmar la conciliación.'))
        self.write({
            'conciliation_status': 'manual_confirmed',
            'conciliation_manual_note': note,
            'conciliation_manual_user_id': self.env.user.id,
            'conciliation_manual_date': fields.Datetime.now(),
        })
        self.message_post(
            body=_('Conciliación confirmada manualmente.\nMotivo: %s') % note)
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.id,
            'action_type': 'conciliation_manual_confirm',
            'description': 'Conciliación confirmada manualmente: %s' % note,
            'user_id': self.env.user.id,
        })
        return True

    def action_validate(self):
        """Rama explícita para Volúmenes; el resto delega al flujo core."""
        self.ensure_one()
        if self.tipo_recepcion == 'granel':
            return self._action_validate_volume_intake()
        return super().action_validate()

    def _action_validate_volume_intake(self):
        """Validación de stock para Ingreso por Volúmenes, sin geometría.

        No exige espesor nominal ni subproducto comercial, no ejecuta
        cubicación geométrica ni salida automática a proceso. Crea/reutiliza
        un lote sintético consolidado y un picking incoming en m³ usando
        EXCLUSIVAMENTE el volumen oficial documental de la guía
        (`get_official_volume_m3()`): total declarado en la Guía/PDF o, en su
        defecto, Packing Excel / Packing declarado. La suma del detalle
        documental nunca sustituye al volumen oficial. Idempotente por estado.
        """
        self.ensure_one()
        if self.state not in ('verified', 'processed'):
            raise ValidationError(
                _('La guía debe estar Verificada para enviar Volúmenes a stock.'))

        errors = self._get_volume_intake_blockers()
        if errors:
            raise ValidationError(
                _('No se puede enviar Volúmenes a stock:\n\n') +
                '\n'.join('- %s' % e for e in errors))

        # ── Volumen OFICIAL (F3.1) ────────────────────────────────────────
        # Único volumen válido para stock: total declarado en la Guía/PDF
        # (o Packing Excel / Packing declarado). Sin sustituto silencioso:
        # ni suma de detalle, ni suma de líneas de proceso, ni volumen
        # operativo, ni declarado, ni valores de stock/conciliación/costos.
        official_volume_m3, official_source = self.get_official_volume_m3()
        if float_compare(
                official_volume_m3, 0.0, precision_rounding=0.001) <= 0:
            raise ValidationError(
                _('No existe volumen documental oficial para enviar a stock.'))

        lot = self._get_or_create_volume_synthetic_lot(official_volume_m3)

        picking = self._get_or_create_picking_unified()
        if not picking:
            raise UserError(
                _('No se pudo generar ni recuperar el albarán asociado.'))

        picking = self._validate_volume_picking(
            picking, lot, official_volume_m3)

        # F1 — Post-condición fail-closed: la guía solo puede marcarse como
        # Validada si el albarán y TODOS sus movimientos quedaron en 'done'.
        # A. El albarán debe existir.
        if not picking:
            raise UserError(_(
                'No se generó ni recuperó el albarán de la guía %s. '
                'La guía no puede marcarse como Validada.') % self.name)
        # B. El albarán debe estar en estado Realizado (Done).
        if picking.state != 'done':
            raise UserError(_(
                'El albarán %s no quedó en estado Realizado (Done): '
                'estado actual %s. La guía no puede marcarse como Validada.'
            ) % (picking.name, picking.state))
        # C. Todos los movimientos del albarán deben estar Realizados.
        pending_moves = picking.move_ids.filtered(
            lambda move: move.state != 'done')
        if pending_moves:
            raise UserError(_(
                'El albarán %s tiene movimientos sin estado Realizado: %s. '
                'La guía no puede marcarse como Validada.'
            ) % (picking.name, ', '.join(pending_moves.mapped('name'))))

        # D. Solo tras A, B y C se persiste la transición de estado.
        self.write({
            'state': 'validated',
            'validated_by_id': self.env.user.id,
            'validated_date': fields.Datetime.now(),
        })
        if self.lot_ids:
            self.lot_ids.write({
                'estado_trazabilidad': 'recepcionado',
                'technical_validation': 'approved',
            })
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.id,
            'action_type': 'validation_signature',
            'description': 'Validación de Volúmenes: %s (%.3f m³, fuente %s)'
                           % (self.name, official_volume_m3,
                              official_source or 'sin fuente'),
            'user_id': self.env.user.id,
        })
        self.message_post(body=_(
            'Volúmenes enviado a stock: %.3f m³ (fuente %s, lote %s).'
        ) % (official_volume_m3, official_source or 'sin fuente', lot.name))
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _get_volume_intake_blockers(self):
        """Errores bloqueantes propios de Volúmenes (sin espesor/subproducto)."""
        errors = []
        if not self.partner_id:
            errors.append(_('No se resolvió el proveedor.'))
        if not self.assignment_location_id:
            errors.append(_('Falta el Patio de Asignación (ubicación interna).'))
        if not (self.guide_pdf_file or self.excel_file or self.excel_attachment_id):
            errors.append(_('Falta evidencia documental (PDF o Excel).'))
        if not self.name:
            errors.append(_('No se detectó número de guía.'))
        if not self.date_emission:
            errors.append(_('No se detectó fecha documental.'))
        if self.conciliation_status in ('needs_manual_review', 'incompatible'):
            errors.append(
                _('La conciliación documental requiere revisión/confirmación manual.'))
        return errors

    def _find_volume_lot(self):
        """Busca el ÚNICO Lote Volumen de esta guía por identidad documental.

        F3.1 — El criterio es `volume_source_guia_id` (identidad permanente que
        sobrevive a la reapertura de la guía) + `lot_flow_type = 'volume'`.
        NUNCA se busca por el sufijo numérico del número de guía.
        """
        self.ensure_one()
        return self.env['stock.lot'].search([
            ('volume_source_guia_id', '=', self.id),
            ('lot_flow_type', '=', 'volume'),
        ], limit=1)

    def _get_or_create_volume_synthetic_lot(self, official_volume_m3):
        """Obtiene o crea el Lote Volumen único de la guía (identidad SV).

        F3.1 — Identidad operativa: etiqueta `SV` + 11 dígitos generada por la
        secuencia global `madenat.volume.lot`. El número de guía es metadata
        documental y no participa en la identidad del lote. Identidad
        documental permanente: `volume_source_guia_id`, que sobrevive a la
        reapertura de la guía.

        `official_volume_m3` es el volumen oficial documental de la guía
        (`get_official_volume_m3()`); la suma del detalle documental nunca se
        usa como sustituto.

        Idempotencia: si el lote de volumen de esta guía ya existe se reutiliza
        sin renombrarlo y sin reasignar su guía origen; solo se restaura la
        relación operativa `guia_processing_id` cuando el flujo la requiere
        (revalidación tras reapertura). Nunca se acuña una segunda etiqueta SV
        para la misma guía.
        """
        self.ensure_one()
        product = self.env['madenat.ingestion.config'].get_default_product(
            'bruta', profile=self.ingestion_profile)
        # Autorreparación de maestro: el producto debe ser almacenable antes de
        # reservar/validar stock (misma regla que do_full_processing).
        tmpl = product.product_tmpl_id.sudo()
        if not tmpl.is_storable:
            tmpl.write({'is_storable': True, 'type': 'consu'})
        lot = self._find_volume_lot()
        if lot and lot.guia_processing_id != self:
            # Reutilización idempotente: solo se restaura la relación operativa
            # con la MISMA guía (revalidación tras reapertura). El lote nunca se
            # renombra ni se reasigna a otra guía.
            lot.write({'guia_processing_id': self.id})

        # Re-búsqueda defensiva (una sola vez) antes de acuñar una etiqueta SV.
        if not lot:
            self.env['stock.lot'].flush_model(
                ['volume_source_guia_id', 'lot_flow_type'])
            lot = self._find_volume_lot()

        vals = {
            'product_id': product.id,
            'piezas': 1,
            'volume_purchase_m3': official_volume_m3,
            'vol_shipment_m3': official_volume_m3,
            'volumen_m3': official_volume_m3,
            'guia_processing_id': self.id,
            'volume_source_guia_id': self.id,
            'lot_flow_type': 'volume',
            'reception_id': False,
            'location_id': self.assignment_location_id.id,
            'supplier_id': self.partner_id.id if self.partner_id else False,
            'espesor_mm': 0.0,
            'ancho_mm': 0.0,
            'largo_m': 0.0,
            'espesor_nominal_mm': 0.0,
            'ancho_nominal_mm': 0.0,
            'subproducto_id': False,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'recepcionado',
        }
        if not lot:
            # Etiqueta SV única: se acuña solo cuando realmente se crea el lote.
            vals['name'] = self.env['stock.lot']._next_volume_lot_label()
            lot = self.env['stock.lot'].create(vals)
        if lot.id not in self.lot_ids.ids:
            self.write({'lot_ids': [(4, lot.id)]})
        return lot

    def _validate_volume_picking(self, picking, lot, official_volume_m3):
        """Confirma, asigna y valida el picking incoming de Volúmenes.

        La cantidad de stock es el volumen OFICIAL documental de la guía.
        """
        if picking.location_dest_id.usage != 'internal':
            raise UserError(
                _('El destino del albarán debe ser una ubicación interna (Bodega).'))
        if picking.state == 'draft':
            picking.action_confirm()
        if picking.state not in ('assigned', 'done'):
            picking.action_assign()

        if picking.state != 'done':
            moves = picking.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel'))
            for move in moves:
                if 'quantity' in move._fields:
                    move.quantity = official_volume_m3
                if 'picked' in move._fields:
                    move.picked = True
                if not move.move_line_ids:
                    vals = {
                        'picking_id': picking.id,
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'lot_id': lot.id,
                        'quantity': official_volume_m3,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'product_uom_id': move.product_uom.id,
                        'company_id': picking.company_id.id,
                    }
                    if 'picked' in self.env['stock.move.line']._fields:
                        vals['picked'] = True
                    self.env['stock.move.line'].create(vals)
                else:
                    for line in move.move_line_ids:
                        line.write({
                            'quantity': official_volume_m3,
                            'lot_id': lot.id,
                        })
                        if 'picked' in line._fields:
                            line.picked = True

            ctx = picking.env.context.copy()
            ctx.update({
                'skip_backorder': True,
                'skip_immediate': True,
                'check_move_validity': False,
            })
            try:
                res = picking.with_context(ctx).button_validate()
                if isinstance(res, dict) and 'res_model' in res:
                    Wizard = self.env[res['res_model']].with_context(
                        res.get('context', ctx))
                    wiz = Wizard.create({})
                    if hasattr(wiz, 'process'):
                        wiz.process()
                    elif hasattr(wiz, 'process_simple'):
                        wiz.process_simple()
            except Exception as e:
                raise UserError(_('Error al validar Picking: %s') % e)

        # F1 — Devolver explícitamente el albarán procesado para que el
        # llamador pueda verificar la post-condición (picking en 'done')
        # antes de persistir la transición de estado de la guía.
        return picking
