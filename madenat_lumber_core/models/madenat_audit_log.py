# -*- coding: utf-8 -*-
from odoo import models, fields, api  # ✅ AGREGAR: api

class MadenatAuditLog(models.Model):
    _name = 'madenat.audit.log'
    _description = 'Logs de Auditoría MADENAT'
    _order = 'timestamp desc'

    reception_id = fields.Many2one('lumber.reception', string='Recepción', ondelete='cascade')
    action_type = fields.Selection([
        ('creation', 'Creación Producto'),
        ('omission', 'Omisión Producto'),
        ('lot_creation', 'Creación Lote'),
        ('lot_update', 'Actualización Lote')
    ], string='Tipo de Acción', required=True)
    description = fields.Text(string='Descripción', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    batch_id = fields.Char(string='ID de Lote')
    month = fields.Char(string='Mes (YYYY-MM)', compute='_compute_month', store=True)
    
    @api.depends('timestamp')
    def _compute_month(self):
        for log in self:
            log.month = log.timestamp.strftime('%Y-%m') if log.timestamp else False
