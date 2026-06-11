# -*- coding: utf-8 -*-
"""Wizard de Cierre de Período — GB-4, GB-5, GB-6 (CANON/14, C20)"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MadenatPeriodClose(models.TransientModel):
    _name = 'madenat.period.close'
    _description = 'Cierre de Período MADENAT'

    confirm = fields.Boolean(string='Confirmar cierre', default=False)

    def action_close_period(self):
        """Valida GB-4, GB-5 y cierra el período con trazabilidad."""
        # GB-4: Embarques con costos distribuidos
        shipments_pending = self.env['lumber.export.shipment'].search([
            ('state', '=', 'in_transit'),
            ('cost_distribution_state', '=', 'pending')
        ])
        if shipments_pending:
            raise UserError(_(
                "🛑 GATE GB-4 BLOQUEADO: Costos logísticos sin distribuir.\n"
                "%d embarque(s) en tránsito no tienen costos distribuidos:\n%s\n"
                "Ejecute 'Distribuir Costos' en cada embarque antes del cierre."
            ) % (len(shipments_pending), "\n".join(shipments_pending.mapped('name'))))

        # GB-5: Recepciones conciliadas
        receptions_pending = self.env['lumber.reception'].search([
            ('reconciliation_state', '!=', 'done'),
            ('state', '=', 'done')
        ])
        if receptions_pending:
            raise UserError(_(
                "🛑 GATE GB-5 BLOQUEADO: Recepciones sin conciliar.\n"
                "%d recepcion(es) finalizadas no tienen conciliación contable.\n"
                "Complete el Panel de Conciliación antes del cierre."
            ) % len(receptions_pending))

        # Lotes sin costo base
        lots_sin_costo = self.env['stock.lot'].search([
            ('wood_cost_usd', '<=', 0)
        ])
        if lots_sin_costo:
            raise UserError(_(
                "🛑 CIERRE BLOQUEADO: Lotes sin costo base.\n"
                "%d lote(s) no tienen wood_cost_usd asignado.\n"
                "Contacte al equipo de Costos para completar la valorización."
            ) % len(lots_sin_costo))

        # Validación de distribuciones contables
        dists_sin_validar = self.env['lumber.cost.distribution'].search([
            ('state', '=', 'applied'),
            ('validated_by_accounting', '=', False)
        ])
        if dists_sin_validar:
            raise UserError(_(
                "🛑 GATE GB-4 BLOQUEADO: Expedientes sin validación contable.\n"
                "%d expediente(s) de liquidación aplicados no han sido validados por Contabilidad.\n"
                "Use la pestaña 'Validación Contable' en cada expediente."
            ) % len(dists_sin_validar))

        # Cierre exitoso — registrar trazabilidad
        self.env['madenat.audit.log'].sudo().create({
            'action_type': 'lot_update',
            'event_type': 'period_closed',
            'description': 'Cierre de período ejecutado. GB-4, GB-5 verificados.',
            'user_id': self.env.user.id,
        })

        _logger.info("MADENAT: Cierre de período ejecutado por %s", self.env.user.name)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Período Cerrado',
                'message': 'GB-4, GB-5 verificados. Cierre registrado en auditoría.',
                'type': 'success',
            }
        }