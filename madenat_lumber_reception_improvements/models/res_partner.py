# -*- coding: utf-8 -*-
"""
Extensión de res.partner para agregar campo is_processor.

FILOSOFÍA:
----------
- Agregar campos NUEVOS (no modificar existentes)
- Usar _inherit para extender
- No romper funcionalidad existente
"""

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # ======================================
    # NUEVOS CAMPOS
    # ======================================
    
    is_processor = fields.Boolean(
        string='Es Procesador',
        default=False,
        help='Marca si este partner es una planta procesadora de madera '
             '(cepillado, secado, tratamiento, etc.)'
    )
    
    processor_location = fields.Char(
        string='Ubicación Planta',
        help='Dirección física de la planta procesadora'
    )