# -*- coding: utf-8 -*-
"""Asistente: reset/reversión no bloqueante de una recepción.

Captura el motivo (obligatorio solo si hay efecto físico previsto) y confirma
la corrección. La ejecución real vive en `lumber.reception._reset_to_draft_confirmed`
(método privado, no invocable por RPC) para impedir que una llamada directa
evada la trazabilidad.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LumberReceptionResetWizard(models.TransientModel):
    _name = 'lumber.reception.reset.wizard'
    _description = 'Asistente: reabrir recepción (reversión trazable)'

    reception_id = fields.Many2one(
        'lumber.reception', string='Recepción', required=True, readonly=True,
        default=lambda self: self.env.context.get('default_reception_id'))

    state_name = fields.Char(
        string='Estado actual', compute='_compute_effect_info')

    has_physical_effect = fields.Boolean(
        string='Efecto físico previsto', compute='_compute_effect_info')

    effect_summary = fields.Text(
        string='Efecto físico previsto', compute='_compute_effect_info')

    warning_text = fields.Text(
        string='Advertencias (no bloquean)', compute='_compute_effect_info')

    reason = fields.Text(
        string='Motivo de la corrección',
        help='Obligatorio cuando existe efecto físico (reversión/cancelación '
             'de stock atribuible). Trazabilidad, no aprobación.')

    # ── Cálculos ──────────────────────────────────────────────────────────
    @api.depends('reception_id')
    def _compute_effect_info(self):
        for wiz in self:
            rec = wiz.reception_id
            if not rec:
                wiz.state_name = False
                wiz.has_physical_effect = False
                wiz.effect_summary = False
                wiz.warning_text = False
                continue
            info = rec._reset_physical_effect_info()
            wiz.state_name = dict(rec._fields['state'].selection).get(
                rec.state, rec.state)
            wiz.has_physical_effect = info['has_effect']
            lines = []
            if info['done_pickings']:
                lines.append('• %d picking(s) DONE → se creará retorno nativo.'
                             % len(info['done_pickings']))
            if info['pending_pickings']:
                lines.append('• %d picking(s) pendiente(s) → se cancelará/'
                             'desreservará con API nativa.' % len(info['pending_pickings']))
            if not lines:
                lines.append('• Sin pickings atribuibles: reset documental '
                             '(no se toca stock ni historial).')
            wiz.effect_summary = '\n'.join(lines)
            wiz.warning_text = '\n'.join(info['warnings']) or False

    # ── Acciones ──────────────────────────────────────────────────────────
    def action_confirm(self):
        self.ensure_one()
        rec = self.reception_id
        if rec._reset_physical_effect_info()['has_effect'] and not (self.reason or '').strip():
            raise UserError(_(
                'Indique un motivo para continuar: esta corrección tiene efecto '
                'físico (reversión/cancelación de stock atribuible). Es '
                'trazabilidad, no aprobación.'))
        return rec._reset_to_draft_confirmed(reason=self.reason)
