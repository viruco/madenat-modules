# -*- coding: utf-8 -*-
# PLACEHOLDER - Se completará con el código completo

from odoo import models, fields, api

class VendorPaymentOrder(models.Model):
    _name = 'vendor.payment.order'
    _description = 'Orden de Pago a Proveedor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Número', required=True, default='/')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
    ], default='draft')
