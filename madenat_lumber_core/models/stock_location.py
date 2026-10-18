# -*- coding: utf-8 -*-
from odoo import models, fields


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_patio = fields.Boolean(
        string='Es Patio de Madera',
        default=False,
        index=True,
        help='Indica si esta ubicación corresponde a un patio operativo para recepción o almacenamiento de madera.',
    )
