# -*- coding: utf-8 -*-
"""AD-88 / B-03 / B-06 — Reversa de rebaja con override de Gerencia.

Cuando el embarque ya fue entregado o el viaje está cancelado, la reversa de la
rebaja deja de ser un bloqueo duro sin salida: **Gerencia** puede autorizarla
con un motivo, que queda auditado (snapshot + SHA-256) vía el helper AD-88.
"""
from odoo import fields, models, _


class LumberContainerRebajaReverseWizard(models.TransientModel):
    _name = 'lumber.container.rebaja.reverse.wizard'
    _description = 'Reversa de rebaja con override de Gerencia (B-03/B-06)'

    container_id = fields.Many2one(
        'lumber.container', string='Contenedor', required=True,
        ondelete='cascade')
    reason = fields.Text(
        string='Motivo del override', required=True,
        help='Motivo por el que Gerencia autoriza revertir la rebaja con el '
             'embarque entregado o el viaje cancelado.')

    def action_confirm_override(self):
        self.ensure_one()
        self.container_id._reverse_rebaja_container(
            override_reason=self.reason)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reversa autorizada'),
                'message': _('Rebaja revertida con override de Gerencia.'),
                'type': 'warning',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
