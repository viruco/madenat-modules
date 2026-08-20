# -*- coding: utf-8 -*-
"""Wizard (TransientModel) para capturar el motivo de cancelación de Producto.

Aísla la trazabilidad de la cancelación en madenat_lumber_intake. No toca stock,
lotes, pickings, volúmenes ni inventario: solo persiste `cancel_reason` y cambia
`state` a `cancel` mediante el método canónico del core.
"""
from odoo import fields, models, _
from odoo.exceptions import UserError


class MadenatLumberIntakeCancel(models.TransientModel):
    _name = 'madenat.lumber.intake.cancel'
    _description = 'Motivo de cancelación de ingreso preliminar'

    reason = fields.Text(string='Motivo de cancelación', required=True)

    reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción',
        default=lambda self: self.env.context.get('default_reception_id'),
    )

    def action_confirm_cancel(self):
        """Confirma la cancelación no destructiva con motivo obligatorio."""
        self.ensure_one()
        if not self.reception_id:
            raise UserError(_('No se resolvió la recepción a cancelar.'))

        rec = self.reception_id
        if rec.state == 'done' or rec.lot_ids or rec.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede cancelarse de forma preliminar.')
            )
        if rec.state == 'cancel':
            raise UserError(_('El ingreso ya se encuentra cancelado.'))

        reason = self.reason.strip()
        rec.write({'cancel_reason': reason})
        # Cancelación canónica del core: escribe state='cancel' y deja bitácora.
        rec.action_cancel()
        rec.message_post(
            body=_('Cancelado desde Ingreso Global. Motivo: %s') % reason,
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}
