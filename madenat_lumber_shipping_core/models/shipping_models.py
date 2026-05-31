# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class ShippingVessel(models.Model):
    _name = 'shipping.vessel'
    _description = 'Motonave'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True, index=True)
    imo_number = fields.Char(string='Número IMO', index=True, help="Número de 7 dígitos de la Organización Marítima Internacional")
    flag_country_id = fields.Many2one('res.country', string='Bandera')
    vessel_type = fields.Selection([
        ('container', 'Portacontenedores'),
        ('bulk', 'Granelero'),
        ('general', 'General')],
        string='Tipo de Buque', default='container')
    capacity_teu = fields.Integer(string='Capacidad (TEU)')
    active = fields.Boolean(string='Activo', default=True)

    @api.constrains('imo_number')
    def _check_imo_number(self):
        for record in self:
            if record.imo_number:
                if not re.match(r'^IMO \d{7}$', record.imo_number):
                    raise ValidationError(_('El número IMO debe tener el formato "IMO 1234567"'))

class ShippingVoyage(models.Model):
    _name = 'shipping.voyage'
    _description = 'Viaje'
    _order = 'name desc'

    name = fields.Char(string='Viaje', compute='_compute_voyage_name', store=True)
    vessel_id = fields.Many2one('shipping.vessel', string='Motonave', required=True, ondelete='restrict')
    voyage_reference = fields.Char(string='Referencia de Viaje', required=True)
    port_of_loading_id = fields.Many2one('res.country.state', string='Puerto de Carga')
    port_of_discharge_id = fields.Many2one('res.country.state', string='Puerto de Descarga')
    etd = fields.Date(string='ETD')
    eta = fields.Date(string='ETA')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('in_transit', 'En Tránsito'),
        ('arrived', 'Arribado'),
        ('canceled', 'Cancelado')],
        string='Estado', default='draft')

    @api.depends('vessel_id', 'voyage_reference')
    def _compute_voyage_name(self):
        for voyage in self:
            if voyage.vessel_id and voyage.voyage_reference:
                voyage.name = f"{voyage.vessel_id.name} / {voyage.voyage_reference}"
            else:
                voyage.name = False

class ShippingBooking(models.Model):
    _name = 'shipping.booking'
    _description = 'Reserva'
    _order = 'name desc'

    name = fields.Char(string='Número de Reserva', required=True, index=True)
    shipping_line_id = fields.Many2one('res.partner', string='Línea Naviera', domain=[('is_company', '=', True)])
    voyage_id = fields.Many2one('shipping.voyage', string='Viaje')
    container_qty = fields.Integer(string='Cantidad de Contenedores')
    container_type = fields.Selection([
        ('40hc', '40ft High Cube'),
        ('40gp', '40ft General Purpose'),
        ('20gp', '20ft General Purpose')],
        string='Tipo de Contenedor', default='40hc')
    booking_date = fields.Date(string='Fecha de Reserva', default=fields.Date.today)
    cargo_cutoff_date = fields.Date(string='Fecha Límite de Carga')
