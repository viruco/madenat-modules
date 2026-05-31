# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ShippingBooking(models.Model):
    _name = 'shipping.booking'
    _description = 'Reserva de Espacio (Booking)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'booking_date desc'

    name = fields.Char(
        string='N° Booking', 
        required=True, 
        index=True, 
        tracking=True,
        help="Número de reserva otorgado por la naviera"
    )
    
    shipping_line_id = fields.Many2one(
        'res.partner', 
        string='Línea Naviera', 
        tracking=True,
        domain="[('is_company', '=', True)]"
    )
    
    voyage_id = fields.Many2one(
        'shipping.voyage', 
        string='Viaje Asignado', 
        tracking=True,
        ondelete='restrict'
    )
    
    # Capacidad Reservada
    container_qty = fields.Integer('Cantidad Contenedores', default=1, tracking=True)
    container_type = fields.Selection([
        ('20gp', '20ft Standard'),
        ('40gp', '40ft Standard'),
        ('40hc', '40ft High Cube'),
        ('45hc', '45ft High Cube')
    ], string='Tipo Contenedor', default='40hc', tracking=True)
    
    booking_date = fields.Date('Fecha Reserva', default=fields.Date.context_today)
    cargo_cutoff_date = fields.Datetime('Stacking / Cut-off', tracking=True)
    vgm_cutoff_date = fields.Datetime('VGM Cut-off')
    
    notes = fields.Text('Notas / Instrucciones')
    
    active = fields.Boolean('Activo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'El número de Booking debe ser único.')
    ]