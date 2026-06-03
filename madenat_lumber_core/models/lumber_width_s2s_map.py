# -*- coding: utf-8 -*-
"""
TABLA ROUGH→S2S (Fase 2 — Modelo Persistente)

Define la conversión de ancho rough (mm) a S2S decimal + etiqueta fraccionaria.
Fuente original: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx — 16-20 entradas canónicas.

Prioridad de fuentes (runtime):
  1. Este modelo (registros activos)
  2. ir.config_parameter 'madenat.width_s2s_map' (Fase 1, fallback)
  3. Hardcode legacy en width_mapping.WidthMappingTable.MAPPING
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LumberWidthS2SMap(models.Model):
    _name = 'lumber.width.s2s.map'
    _description = 'Tabla Rough→S2S'
    _order = 'sequence, rough_mm'
    _sql_constraints = [
        (
            'unique_rough_mm',
            'UNIQUE(rough_mm)',
            'Ya existe una entrada para ese valor de rough_mm.'
        ),
        (
            'check_rough_mm_positive',
            'CHECK(rough_mm > 0)',
            'El rough_mm debe ser mayor a cero.'
        ),
        (
            'check_s2s_decimal_positive',
            'CHECK(s2s_decimal > 0)',
            'El valor S2S decimal debe ser mayor a cero.'
        ),
    ]

    rough_mm = fields.Integer(
        string='Rough (mm)',
        required=True,
        help='Ancho bruto en milímetros (rough). Valor entero canónico de compra.'
    )

    s2s_decimal = fields.Float(
        string='S2S (decimal)',
        required=True,
        digits=(16, 4),
        help='Ancho S2S en pulgadas decimales (ej: 2.625 = 2 5/8).'
    )

    s2s_label = fields.Char(
        string='S2S (fracción)',
        required=True,
        help='Etiqueta fraccionaria para UI (ej: "2 5/8", "3 7/8").'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden en vistas y búsquedas. Menor número = primero.'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Desmarque para deshabilitar esta entrada sin eliminarla.'
    )

    def name_get(self):
        result = []
        for rec in self:
            name = f'{rec.rough_mm} mm → {rec.s2s_label}" ({rec.s2s_decimal})'
            result.append((rec.id, name))
        return result