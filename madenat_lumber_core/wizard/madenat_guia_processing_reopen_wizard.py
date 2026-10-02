# -*- coding: utf-8 -*-
"""Asistente: reapertura no bloqueante y trazable de una guía procesada.

Captura el motivo (obligatorio solo si hay efecto físico previsto) y confirma
la corrección. La ejecución real vive en
`madenat.guia.processing._reopen_to_draft_confirmed` (método privado, no
invocable por RPC) para impedir que una llamada directa evada la trazabilidad.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MadenatGuiaProcessingReopenWizard(models.TransientModel):
    _name = 'madenat.guia.processing.reopen.wizard'
    _description = 'Asistente: reabrir guía procesada (reversión trazable)'

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía', required=True, readonly=True,
        default=lambda self: self.env.context.get('default_guia_processing_id'))

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
        help='Obligatorio cuando existe efecto físico (reversión de consumo a '
             'proceso BT-04 o del ingreso de producción). Trazabilidad, no '
             'aprobación.')

    @api.depends('guia_processing_id')
    def _compute_effect_info(self):
        for wiz in self:
            guia = wiz.guia_processing_id
            if not guia:
                wiz.state_name = False
                wiz.has_physical_effect = False
                wiz.effect_summary = False
                wiz.warning_text = False
                continue
            info = guia._reopen_physical_effect_info()
            wiz.state_name = dict(guia._fields['state'].selection).get(
                guia.state, guia.state)
            wiz.has_physical_effect = info['has_effect']
            if info['has_effect']:
                wiz.effect_summary = '\n'.join(
                    '• %s' % effect for effect in info['effects'])
            else:
                wiz.effect_summary = (
                    '• Sin efecto físico atribuible: reapertura documental '
                    '(se conserva stock, lotes, pickings y movimientos).')
            wiz.warning_text = '\n'.join(info['warnings']) or False

    def action_confirm(self):
        self.ensure_one()
        guia = self.guia_processing_id
        if guia._reopen_physical_effect_info()['has_effect'] and not (
                self.reason or '').strip():
            raise UserError(_(
                'Indique un motivo para continuar: esta reapertura tiene efecto '
                'físico (reversión de consumo a proceso o de producción). Es '
                'trazabilidad, no aprobación.'))
        return guia._reopen_to_draft_confirmed(reason=self.reason)
