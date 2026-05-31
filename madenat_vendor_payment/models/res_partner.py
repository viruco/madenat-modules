# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_service_type = fields.Selection(
        [
            ('supplier', 'Proveedor Madera'),
            ('packing', 'Consolidación'),
            ('customs', 'Agencia Aduana'),
            ('freight', 'Naviera/Freight'),
            ('insurance', 'Seguro'),
            ('warehouse', 'Almacenaje'),
            ('transport', 'Transporte'),
            ('service', 'Otro Servicio'),
        ],
        string='Tipo de Servicio del Proveedor',
        help="Clasifica al proveedor según el tipo de servicio que presta en la cadena logística."
    )