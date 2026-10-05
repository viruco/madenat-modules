# -*- coding: utf-8 -*-
"""AD-88 / B-03 / B-06 — Reversa de rebaja con override de Gerencia.

Cuando el embarque ya fue entregado, el viaje está cancelado o la excepción
B-01 quedó regularizada (`resolved`), la reversa de la rebaja deja de ser un
bloqueo duro sin salida: **Gerencia** puede autorizarla con un motivo, que queda
auditado (snapshot + SHA-256) vía el helper AD-88.

Sub-bloque 4B (2026-10-04) — R2: la reversa ejecuta un **retorno físico TOTAL**
(Clientes → ubicación interna de origen, mismo lote). El asistente sólo expone
contexto de la cadena OUT → IN y el motivo; **no** ofrece retorno parcial.
"""
from odoo import api, fields, models, _


class LumberContainerRebajaReverseWizard(models.TransientModel):
    _name = 'lumber.container.rebaja.reverse.wizard'
    _description = 'Reversa de rebaja con override de Gerencia (B-03/B-06)'

    container_id = fields.Many2one(
        'lumber.container', string='Contenedor', required=True,
        ondelete='cascade')
    reason = fields.Text(
        string='Motivo del override', required=True,
        help='Motivo por el que Gerencia autoriza revertir la rebaja con el '
             'embarque entregado, el viaje cancelado o una B-01 regularizada '
             '(mínimo 20 caracteres).')
    # R2 (Sub-bloque 4B): contexto de la cadena de retorno físico total.
    container_state = fields.Selection(
        related='container_id.state', string='Estado del Contenedor',
        readonly=True)
    b01_exception_state = fields.Selection(
        related='container_id.b01_exception_state',
        string='Excepción B-01', readonly=True)
    origin_picking_names = fields.Char(
        string='Salida de rebaja (OUT)',
        compute='_compute_return_context')
    return_picking_names = fields.Char(
        string='Retorno físico (IN)',
        compute='_compute_return_context')

    @api.depends('container_id')
    def _compute_return_context(self):
        for wiz in self:
            container = wiz.container_id
            wiz.origin_picking_names = (
                container.rebaja_origin_picking_names if container else False)
            wiz.return_picking_names = (
                container.rebaja_return_picking_names if container else False)

    def action_confirm_override(self):
        self.ensure_one()
        self.container_id._reverse_rebaja_container(
            override_reason=self.reason)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reversa autorizada'),
                'message': _(
                    'Retorno físico total autorizado por Gerencia: la rebaja '
                    'fue revertida (Clientes → ubicación interna).'),
                'type': 'warning',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
