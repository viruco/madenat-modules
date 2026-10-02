# -*- coding: utf-8 -*-
"""Bloque SV visible y acciones de Etiqueta SV (Consola y Guía).

Fase 2 (AD-80) — reemplaza la regla anterior «sin acciones SV en la Consola».

Contrato:

1. La Consola (`madenat.lumber.intake.console`) es una vista SQL readonly
   (`_auto = False`): los campos del bloque SV son proxies NO almacenados que
   leen exclusivamente las guardas canónicas de `stock.lot`
   (`sv_original_volume_m3`, `sv_regularized_baseline_m3`, `sv_rebajado_m3`,
   `sv_available_m3`, `sv_pieces_enabled`, `sv_available_pieces`,
   `sv_documentary_warning`) y el ledger `madenat.sv.operation`.
2. Las cinco acciones aprobadas (modificar etiqueta, regularizar volumen,
   rebajar, reversar rebaja y ver historial) se exponen SOLO cuando existe un
   lote SV real (`declared_sv_lot_id` / `volume_lot_id`). Sin lote no hay
   botón de mutación posible.
3. Toda mutación delega en los wizards existentes del Programa SV
   (`madenat.sv.rename.wizard`, `madenat.sv.volume.regularize.wizard`,
   `madenat.sv.rebaja.wizard`, `madenat.sv.rebaja.reverse.wizard`) y, por
   tanto, en el ledger append-only, la capacidad interna de un solo uso, las
   guardas server-side de `stock.lot`, el control de saldo, la concurrencia
   fail-closed y el escalamiento ya implementados.
4. NUNCA se edita directamente `stock.lot.name`, el volumen ni el saldo, y
   nunca se crean lotes, movimientos, pickings, quants ni secuencias.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare

# Precisión de volumen del Programa SV (misma que el core: 0.001 m³).
SV_VOLUME_PRECISION = 0.001


class MadenatLumberIntakeConsoleSv(models.Model):
    """Bloque SV visible y acciones de Etiqueta SV de la Consola."""

    _inherit = 'madenat.lumber.intake.console'

    # ── Bloque read-only: ETIQUETA SV Y SALDO OPERATIVO ───────────────────
    # Proxies no almacenados: la consola es una vista SQL y no admite columnas.
    sv_lot_label = fields.Char(
        string='Etiqueta SV vigente',
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_original_volume_m3 = fields.Float(
        string='Volumen documental original',
        digits=(16, 3),
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_regularized_baseline_m3 = fields.Float(
        string='Volumen regularizado',
        digits=(16, 3),
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_rebajado_m3 = fields.Float(
        string='Volumen rebajado',
        digits=(16, 3),
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_regularization_applied = fields.Boolean(
        string='Regularización aplicada',
        compute='_compute_sv_operational_block',
        readonly=True,
        help='Verdadero solo cuando la etiqueta SV tiene una regularización '
             'aplicada que cambia el baseline documental original. Controla '
             'la visibilidad de las filas «Volumen documental original» y '
             '«Volumen regularizado» del bloque SV.',
    )
    sv_available_m3 = fields.Float(
        string='Saldo disponible',
        digits=(16, 3),
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_pieces_enabled = fields.Boolean(
        string='Saldo de piezas habilitado',
        compute='_compute_sv_operational_block',
        readonly=True,
        help='Verdadero solo cuando la Guía declara piezas documentales '
             'positivas. Nunca por paquetes, líneas PDF ni piezas=1 técnico.',
    )
    sv_available_pieces = fields.Integer(
        string='Piezas disponibles',
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_documentary_warning = fields.Boolean(
        string='Advertencia documental',
        compute='_compute_sv_operational_block',
        readonly=True,
    )
    sv_reversible_rebaja_id = fields.Many2one(
        'madenat.sv.operation',
        string='Rebaja SV reversible',
        compute='_compute_sv_operational_block',
        readonly=True,
    )

    # ── Próxima etiqueta SV ESTIMADA (Fase 2, Bug #2) ─────────────────────
    # Proxy no almacenado y de SOLO LECTURA: estima el próximo número de la
    # secuencia global `madenat.volume.lot` mientras la guía aún no tiene
    # etiqueta SV (mismo caso en que la pantalla muestra el placeholder «Se
    # asignará al enviar a stock.»). NO reserva ni consume el número: la
    # etiqueta real se acuña al enviar a stock (F3.1) y puede diferir si otra
    # guía consume la secuencia antes. Nunca escribe en `ir.sequence`.
    sv_next_label_estimate = fields.Char(
        string='Próxima etiqueta SV (estimada)',
        compute='_compute_sv_next_label_estimate',
        readonly=True,
        store=False,
        help='Estimación referencial del próximo número de la secuencia '
             'madenat.volume.lot. No reserva el número: la etiqueta real se '
             'acuña al enviar a stock.',
    )

    # ── Helpers de lectura ────────────────────────────────────────────────
    def _sv_source_guia(self):
        """Guía de Volumen origen de la consola (o recordset vacío).

        Defensivo: la consola solo expone el bloque SV para guías reales de
        Ingreso por Volúmenes. Nunca crea ni escribe nada.
        """
        self.ensure_one()
        guia_model = self.env['madenat.guia.processing']
        if (self.source_model != 'madenat.guia.processing'
                or not self.source_res_id
                or self.ingestion_type != 'volume'):
            return guia_model
        source = self._get_source_record()
        if not source:
            return guia_model
        return source

    def _sv_volume_lot(self):
        """Lote SV real de la Guía (o recordset vacío). Lectura pura."""
        self.ensure_one()
        guia = self._sv_source_guia()
        return guia.volume_lot_id if guia else self.env['stock.lot']

    def _sv_reversible_rebaja(self, lot):
        """Rebaja SV aplicada y aún no reversada del lote (o vacío)."""
        if not lot:
            return self.env['madenat.sv.operation']
        return self.env['madenat.sv.operation'].search([
            ('lot_id', '=', lot.id),
            ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied'),
            ('reversed_operation_id', '=', False),
        ], limit=1)

    @api.depends('source_model', 'source_res_id', 'ingestion_type',
                 'declared_sv_lot_id')
    def _compute_sv_operational_block(self):
        """Lee el bloque SV de la etiqueta real. Solo lectura, sin guardas."""
        for rec in self:
            rec.sv_lot_label = False
            rec.sv_original_volume_m3 = 0.0
            rec.sv_regularized_baseline_m3 = 0.0
            rec.sv_regularization_applied = False
            rec.sv_rebajado_m3 = 0.0
            rec.sv_available_m3 = 0.0
            rec.sv_pieces_enabled = False
            rec.sv_available_pieces = 0
            rec.sv_documentary_warning = False
            rec.sv_reversible_rebaja_id = False

            lot = rec._sv_volume_lot()
            if not lot:
                continue
            rec.sv_lot_label = lot.name or False
            rec.sv_original_volume_m3 = lot.sv_original_volume_m3 or 0.0
            rec.sv_regularized_baseline_m3 = (
                lot.sv_regularized_baseline_m3 or 0.0)
            # Solo hay regularización aplicada cuando el baseline vigente
            # difiere del volumen documental original de la etiqueta.
            rec.sv_regularization_applied = bool(float_compare(
                rec.sv_regularized_baseline_m3, rec.sv_original_volume_m3,
                precision_rounding=SV_VOLUME_PRECISION))
            rec.sv_rebajado_m3 = lot.sv_rebajado_m3 or 0.0
            rec.sv_available_m3 = lot.sv_available_m3 or 0.0
            rec.sv_pieces_enabled = bool(lot.sv_pieces_enabled)
            rec.sv_available_pieces = lot.sv_available_pieces or 0
            rec.sv_documentary_warning = bool(lot.sv_documentary_warning)
            rec.sv_reversible_rebaja_id = rec._sv_reversible_rebaja(lot)

    # ── Próxima etiqueta SV estimada (Fase 2, Bug #2) ─────────────────────
    @api.depends('ingestion_type', 'declared_sv_lot_id')
    def _compute_sv_next_label_estimate(self):
        """Estimación NO vinculante de la próxima etiqueta SV (solo lectura).

        - Solo se calcula para Ingreso por Volúmenes SIN etiqueta SV real (el
          mismo caso en que la pantalla muestra el placeholder «Se asignará al
          enviar a stock.»). Con lote SV real manda `sv_lot_label`.
        - Lee `ir.sequence.number_next_actual`, cuyo compute usa
          `_predict_nextval()` («Predict next value for PostgreSQL sequence
          without consuming it»): predecir NO consume el número.
        - PROHIBIDO escribir en `ir.sequence`: nunca se invoca el inverse
          `_set_number_next_actual()` ni `write()`; solo lectura.
        - Fallback silencioso: si la secuencia no existe, no es legible o el
          número no es válido, el campo queda en False (la pantalla no muestra
          ningún estimado y jamás un error visible al usuario).
        """
        for rec in self:
            rec.sv_next_label_estimate = False
            if rec.ingestion_type != 'volume' or rec.declared_sv_lot_id:
                continue
            try:
                sequence = self.env['ir.sequence'].sudo().search(
                    [('code', '=', 'madenat.volume.lot')], limit=1)
                if not sequence:
                    continue
                number = sequence.number_next_actual
                if not number:
                    continue
                rec.sv_next_label_estimate = '%s%s' % (
                    sequence.prefix or '',
                    str(int(number)).zfill(sequence.padding or 0),
                )
            except Exception:  # pragma: no cover - defensivo
                rec.sv_next_label_estimate = False

    # ── Acciones SV aprobadas (delegación pura) ───────────────────────────
    def _sv_require_volume_lot(self):
        """Lote SV de la Guía origen o error funcional claro."""
        self.ensure_one()
        lot = self._sv_volume_lot()
        if not lot:
            raise UserError(_(
                'La Guía %s no tiene una etiqueta SV asociada. Las acciones '
                'SV se habilitan cuando existe un lote SV real.'
            ) % (self.guide_name or self.display_reference or ''))
        return lot

    def action_sv_rename(self):
        """Abre el asistente de modificación de etiqueta SV."""
        return self._sv_require_volume_lot().action_sv_rename()

    def action_sv_regularize_volume(self):
        """Abre el asistente de regularización documental de volumen."""
        return self._sv_require_volume_lot().action_sv_regularize_volume()

    def action_sv_rebaja(self):
        """Abre el asistente de rebaja de etiqueta SV."""
        return self._sv_require_volume_lot().action_sv_rebaja()

    def action_sv_reverse_rebaja(self):
        """Abre el asistente de reversa de la rebaja aplicada reversible."""
        self.ensure_one()
        operation = self.sv_reversible_rebaja_id
        if not operation:
            raise UserError(_(
                'La Guía %s no tiene una rebaja SV aplicada y reversible '
                'pendiente de reversa (o ya fue reversada).'
            ) % (self.guide_name or self.display_reference or ''))
        return operation.action_open_reverse_wizard()

    def action_open_sv_history(self):
        """Historial SV completo de la Guía origen (solo lectura)."""
        self.ensure_one()
        guia = self._sv_source_guia()
        if not guia:
            raise UserError(_(
                'La consola no tiene una Guía de Volúmenes asociada para '
                'consultar el historial SV.'))
        return guia.action_open_sv_history()

    # ── Ciclo de vida controlado (Fase 2, AD-80) ──────────────────────────
    def _guia_processing_source(self):
        """Guía de Procesados/Volúmenes origen (cualquier tipo de ingreso)."""
        self.ensure_one()
        guia_model = self.env['madenat.guia.processing']
        if (self.source_model != 'madenat.guia.processing'
                or not self.source_res_id
                or self.ingestion_type not in ('processed', 'volume')):
            return guia_model
        source = self._get_source_record()
        return source if source else guia_model

    def action_open_guide_lifecycle(self):
        """Abre el asistente de ciclo de vida controlado de la Guía origen.

        El asistente es el único punto de ejecución de los Modos A–D; la
        consola solo lo abre. Nunca elimina ni modifica nada por sí misma.
        """
        self.ensure_one()
        guia = self._guia_processing_source()
        if not guia:
            raise UserError(_(
                'La consola no tiene una Guía de Procesados o Volúmenes '
                'asociada para gestionar su ciclo de vida.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ciclo de vida de la guía %s') % (guia.name or ''),
            'res_model': 'madenat.lumber.intake.guide.lifecycle',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_console_id': self.id,
                'default_guia_processing_id': guia.id,
            },
        }


class MadenatGuiaprocessingIntakeSvUx(models.Model):
    """Acciones SV equivalentes en el formulario de la Guía (fachada Intake).

    No define lógica de negocio: expone la rebaja reversible y delega en las
    acciones canónicas de la Guía y del ledger SV.
    """

    _inherit = 'madenat.guia.processing'

    intake_sv_reversible_rebaja_id = fields.Many2one(
        'madenat.sv.operation',
        string='Rebaja SV reversible',
        compute='_compute_intake_sv_reversible_rebaja',
        readonly=True,
        help='Rebaja SV aplicada y aún no reversada de la etiqueta SV de la '
             'Guía. Habilita la acción "Reversar rebaja".',
    )

    @api.depends('sv_operation_ids.state',
                 'sv_operation_ids.action_type',
                 'sv_operation_ids.reversed_operation_id')
    def _compute_intake_sv_reversible_rebaja(self):
        Operation = self.env['madenat.sv.operation']
        for guia in self:
            lot = guia.volume_lot_id
            guia.intake_sv_reversible_rebaja_id = Operation.search([
                ('lot_id', '=', lot.id),
                ('action_type', '=', 'rebaja'),
                ('state', '=', 'applied'),
                ('reversed_operation_id', '=', False),
            ], limit=1) if lot else Operation

    def action_intake_sv_reverse_rebaja(self):
        """Reversa la rebaja SV aplicada reversible de la etiqueta SV."""
        self.ensure_one()
        operation = self.intake_sv_reversible_rebaja_id
        if not operation:
            raise UserError(_(
                'La Guía %s no tiene una rebaja SV aplicada y reversible '
                'pendiente de reversa.') % (self.name or self.id))
        return operation.action_open_reverse_wizard()
