# -*- coding: utf-8 -*-
"""
MAPA FÍSICO→NOMINAL BLANKS (Fase 2 — Modelo Persistente)

Permite definir reglas de redondeo de espesor físico a nominal para blanks.
Cada regla asocia un rango físico en pulgadas a un valor nominal también en pulgadas.

Prioridad de fuentes (runtime):
  1. Este modelo (registros activos)
  2. ir.config_parameter 'madenat.blanks_nominal_map' (Fase 1, fallback)
  3. Hardcode legacy en reception_parser._BLANKS_NOMINAL_MAP
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LumberBlankNominalMap(models.Model):
    _name = 'lumber.blank.nominal.map'
    _description = 'Mapa Físico→Nominal Blanks'
    _order = 'sequence, physical_min'
    _sql_constraints = [
        (
            'unique_profile_physical_min',
            'UNIQUE(profile, physical_min)',
            'Ya existe una regla para ese perfil con el mismo mínimo físico.'
        ),
        (
            'check_physical_min_positive',
            'CHECK(physical_min > 0)',
            'El mínimo físico debe ser mayor a cero.'
        ),
        (
            'check_physical_range_valid',
            'CHECK(physical_max > physical_min)',
            'El máximo físico debe ser mayor que el mínimo.'
        ),
        (
            'check_nominal_positive',
            'CHECK(nominal > 0)',
            'El nominal debe ser mayor a cero.'
        ),
    ]

    profile = fields.Selection(
        selection=[
            ('f5085', 'Blanks Clear (f5085)'),
            ('f1550', 'S2S / Rough (f1550)'),
            ('metric', 'Madera Bruta (métrico)'),
        ],
        string='Perfil de Ingesta',
        required=True,
        index=True,
        help='Perfil al que aplica esta regla de mapeo físico→nominal.'
    )

    physical_min = fields.Float(
        string='Mínimo Físico (pulg)',
        required=True,
        digits=(16, 4),
        help='Valor mínimo del rango físico en pulgadas (inclusive).'
    )

    physical_max = fields.Float(
        string='Máximo Físico (pulg)',
        required=True,
        digits=(16, 4),
        help='Valor máximo del rango físico en pulgadas (inclusive).'
    )

    nominal = fields.Float(
        string='Nominal (pulg)',
        required=True,
        digits=(16, 4),
        help='Valor nominal resultante en pulgadas.'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de evaluación. Menor número = mayor prioridad.'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Desmarque para deshabilitar esta regla sin eliminarla.'
    )

    @api.constrains('physical_min', 'physical_max', 'profile')
    def _check_no_overlap(self):
        """
        Valida que no existan solapes de rangos para el mismo perfil.
        Un solape ocurre si el rango [min, max] se cruza con otro registro activo.
        """
        for rec in self:
            if not rec.active:
                continue
            domain = [
                ('id', '!=', rec.id),
                ('profile', '=', rec.profile),
                ('active', '=', True),
                ('physical_min', '<', rec.physical_max),
                ('physical_max', '>', rec.physical_min),
            ]
            overlapping = self.search(domain, limit=1)
            if overlapping:
                raise ValidationError(_(
                    'Solape de rangos detectado para el perfil %(profile)s:\n'
                    'El rango [%(min)s, %(max)s] se solapa con la regla "%(other)s" '
                    '([%(omin)s, %(omax)s]).\n'
                    'Ajuste los rangos para que no se crucen.'
                ) % {
                    'profile': rec.profile,
                    'min': rec.physical_min,
                    'max': rec.physical_max,
                    'other': overlapping.display_name,
                    'omin': overlapping.physical_min,
                    'omax': overlapping.physical_max,
                })

    def name_get(self):
        result = []
        for rec in self:
            name = f'[{rec.profile}] {rec.physical_min}–{rec.physical_max}″ → {rec.nominal}″'
            result.append((rec.id, name))
        return result