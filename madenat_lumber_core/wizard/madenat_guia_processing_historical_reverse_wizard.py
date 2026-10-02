# -*- coding: utf-8 -*-
"""Asistente (H1): reversión física ASISTIDA de producción histórica Procesada.

Alcance EXCLUSIVO (H1 no sustituye a G1/G2/G3/BT-04):
- Guías de producción **no** ``granel`` y **no** ``service`` con consumo BT-04
  (`consumption_picking_id`) y **sin** producción atribuida por la llave fuerte
  G2 (`stock.picking.guia_processing_id`). Es decir: producción histórica.

Reglas aprobadas (ver informe de auditoría H1):
- NO hay atribución automática de históricos: ``origin``, ``lot_id``, proveedor,
  producto, texto y fecha son señales de PROPUESTA, nunca llaves.
- Solo **retorno TOTAL por picking** seleccionado explícitamente. Sin parciales.
- Se preserva la historia: no se borra/desvincula ``lot_ids``, lotes, pickings,
  moves ni move lines, y **nunca** se escribe ``stock.quant``.
- Idempotente: no se propone ni permite un picking con retorno previo.
- Warnings nunca bloquean. Motivo obligatorio solo si hay efecto físico.
- G1 (reapertura documental) conserva su ruta intacta; H1 no la invoca.
"""
import hashlib
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Prefijos históricos de `origin` (evidencia débil): NUNCA se proponen.
_HISTORICAL_PREFIXES = (
    'REVERTIDO-', 'ANULADO-', 'PURGADO-', 'HUERFANO-PROTEGIDO-',
)


class MadenatGuiaProcessingHistoricalReverseWizard(models.TransientModel):
    """Wizard de selección explícita para reversión histórica asistida."""

    _name = 'madenat.guia.processing.historical.reverse.wizard'
    _description = 'Asistente: reversión histórica asistida (H1)'

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía', required=True,
        readonly=True,
        default=lambda self: self.env.context.get('default_guia_processing_id'))

    state_name = fields.Char(
        string='Estado actual', compute='_compute_summary')
    warning_text = fields.Text(
        string='Advertencias (no bloquean)', compute='_compute_summary')
    guidance_text = fields.Text(
        string='Cómo continuar', compute='_compute_summary')
    candidate_ids = fields.One2many(
        'madenat.guia.processing.historical.reverse.candidate', 'wizard_id',
        string='Candidatos (señales de evidencia)')
    selected_count = fields.Integer(
        string='Seleccionados', compute='_compute_summary')
    has_selection = fields.Boolean(
        string='Hay selección', compute='_compute_summary')
    reason = fields.Text(
        string='Motivo de la reversión física',
        help='Obligatorio solo si selecciona al menos un albarán. '
             'Trazabilidad, no aprobación.')

    # ── Construcción de candidatos (propuesta, nunca atribución) ──────────
    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard in wizards:
            wizard._build_candidate_lines()
        return wizards

    def _build_candidate_lines(self):
        """Puebla las líneas candidatas a partir del análisis de la guía."""
        self.ensure_one()
        self.candidate_ids.unlink()
        guia = self.guia_processing_id
        if not guia:
            return
        Candidate = self.env[
            'madenat.guia.processing.historical.reverse.candidate']
        for data in guia._h1_collect_candidates():
            vals = dict(data)
            vals['wizard_id'] = self.id
            Candidate.create(vals)
        self.invalidate_recordset(['candidate_ids'])

    @api.depends('guia_processing_id', 'candidate_ids',
                 'candidate_ids.selected')
    def _compute_summary(self):
        for wizard in self:
            guia = wizard.guia_processing_id
            selected = wizard.candidate_ids.filtered('selected')
            wizard.selected_count = len(selected)
            wizard.has_selection = bool(selected)
            if not guia:
                wizard.state_name = False
                wizard.warning_text = False
                wizard.guidance_text = False
                continue
            wizard.state_name = dict(guia._fields['state'].selection).get(
                guia.state, guia.state)
            warnings = guia._h1_warnings()
            wizard.warning_text = '\n'.join(warnings) or False
            if wizard.candidate_ids.filtered('eligible'):
                wizard.guidance_text = _(
                    'Seleccione los albaranes completos a revertir. Solo se '
                    'muestran candidatos con evidencia; la selección es '
                    'explícita (nunca automática). Los candidatos «A» vienen '
                    'preseleccionados; los «B» requieren su confirmación.')
            else:
                wizard.guidance_text = _(
                    'No hay candidatos con evidencia suficiente. Puede '
                    'continuar sin selección: no habrá efecto físico y podrá '
                    'reabrir la guía documentalmente con «↩️ Reabrir a '
                    'Borrador» (G1), que conserva la historia física.')

    # ── Confirmación ──────────────────────────────────────────────────────
    def action_confirm(self):
        self.ensure_one()
        guia = self.guia_processing_id
        if not guia:
            raise UserError(_('No hay guía asociada al asistente.'))
        selected = self.candidate_ids.filtered('selected')
        ineligible = selected.filtered(lambda c: not c.eligible)
        if ineligible:
            raise UserError(_(
                'Hay candidatos seleccionados que no pueden revertirse '
                '(excluidos o ya retornados): %s.'
            ) % ', '.join(ineligible.mapped('picking_name')))
        if selected and not (self.reason or '').strip():
            raise UserError(_(
                'Indique un motivo para continuar: esta reversión tiene '
                'efecto físico (retorno total de producción histórica). Es '
                'trazabilidad, no aprobación.'))
        return guia._h1_confirm_historical_reverse(
            selected.mapped('picking_id'), reason=self.reason)



class MadenatGuiaProcessingHistoricalReverseCandidate(models.TransientModel):
    """Línea candidata: evidencia mostrada al operador (no atribución)."""

    _name = 'madenat.guia.processing.historical.reverse.candidate'
    _description = 'Candidato de reversión histórica asistida (H1)'
    _order = 'category, picking_id'

    wizard_id = fields.Many2one(
        'madenat.guia.processing.historical.reverse.wizard',
        required=True, ondelete='cascade', index=True)
    picking_id = fields.Many2one(
        'stock.picking', required=True, ondelete='cascade', readonly=True)
    category = fields.Selection([
        ('A', 'A — Evidencia alta'),
        ('B', 'B — Evidencia parcial'),
        ('C', 'C — Excluido / sin evidencia'),
    ], readonly=True, default='C')
    eligible = fields.Boolean(readonly=True)
    selected = fields.Boolean(
        string='Revertir',
        help='Selección explícita del operador. Solo los candidatos elegibles '
             '(A/B) pueden marcarse.')

    # Presentación (solo lectura) del candidato.
    picking_name = fields.Char(related='picking_id.name', readonly=True)
    picking_origin = fields.Char(related='picking_id.origin', readonly=True)
    picking_state = fields.Selection(
        related='picking_id.state', readonly=True)
    picking_type_code = fields.Selection(
        related='picking_id.picking_type_code', readonly=True)
    location_id = fields.Many2one(
        related='picking_id.location_id', readonly=True)
    location_dest_id = fields.Many2one(
        related='picking_id.location_dest_id', readonly=True)
    company_id = fields.Many2one(
        related='picking_id.company_id', readonly=True)
    date_done = fields.Datetime(related='picking_id.date_done', readonly=True)
    product_names = fields.Char(readonly=True)
    lot_names = fields.Text(readonly=True)
    move_count = fields.Integer(readonly=True)
    total_qty = fields.Float(readonly=True, digits=(16, 3))
    signal_summary = fields.Char(readonly=True)
    exclusion_reason = fields.Char(readonly=True)
