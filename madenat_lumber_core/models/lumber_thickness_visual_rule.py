# -*- coding: utf-8 -*-
"""
RANGOS ESPESOR→VISUAL (Fase 2 — Modelo Persistente)

Define rangos de espesor en mm que se mapean a una etiqueta visual fraccionaria.
Alimenta _compute_visual_defaults y _compute_reception_summary en lumber_reception.py.

Prioridad de fuentes (runtime):
  1. Este modelo (registros activos)
  2. ir.config_parameter 'madenat.thickness_visual_ranges' (Fase 1, fallback)
  3. Hardcode legacy: [[37,46,1.5,"6/4"],[22,29,1.0,"4/4"],[30,36,1.25,"5/4"],[47,56,2.0,"8/4"]]
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class LumberThicknessVisualRule(models.Model):
    _name = 'lumber.thickness.visual.rule'
    _description = 'Rangos Espesor→Visual'
    _order = 'sequence, min_thickness'
    _sql_constraints = [
        ('unique_profile_min_thickness', 'UNIQUE(profile, min_thickness)',
         'Ya existe una regla para ese perfil con el mismo minimo de espesor.'),
        ('check_min_thickness_non_negative', 'CHECK(min_thickness >= 0)',
         'El minimo de espesor no puede ser negativo.'),
        ('check_range_valid', 'CHECK(max_thickness > min_thickness)',
         'El maximo de espesor debe ser mayor que el minimo.'),
    ]

    profile = fields.Selection([
        ('f5085', 'Blanks Clear (f5085)'),
        ('f1550', 'S2S / Rough (f1550)'),
        ('metric', 'Madera Bruta (metrico)'),
    ], string='Perfil de Ingesta', required=True, index=True,
       help='Perfil al que aplica esta regla de espesor→visual.')

    min_thickness = fields.Float(
        'Esp. Minimo (mm)', required=True, digits=(16, 2),
        help='Limite inferior del rango de espesor en mm (inclusive).')

    max_thickness = fields.Float(
        'Esp. Maximo (mm)', required=True, digits=(16, 2),
        help='Limite superior del rango de espesor en mm (inclusive).')

    visual_value = fields.Float(
        'Valor Visual (pulg)', required=True, digits=(16, 4),
        help='Valor visual en pulgadas decimales (ej: 1.5 para 6/4).')

    visual_label = fields.Char(
        'Etiqueta Visual', required=True,
        help='Texto visual para UI (ej: "4/4", "5/4", "6/4", "8/4").')

    sequence = fields.Integer('Secuencia', default=10,
        help='Orden de evaluacion. Menor numero = mayor prioridad.')

    active = fields.Boolean('Activo', default=True,
        help='Desmarque para deshabilitar esta regla sin eliminarla.')

    @api.constrains('min_thickness', 'max_thickness', 'profile')
    def _check_no_overlap(self):
        """Valida que no existan solapes de rangos para el mismo perfil."""
        for rec in self:
            if not rec.active:
                continue
            overlapping = self.search([
                ('id', '!=', rec.id),
                ('profile', '=', rec.profile),
                ('active', '=', True),
                ('min_thickness', '<', rec.max_thickness),
                ('max_thickness', '>', rec.min_thickness),
            ], limit=1)
            if overlapping:
                raise ValidationError(_(
                    'Solape de rangos detectado para el perfil %(p)s:\n'
                    'El rango [%(a)s, %(b)s] mm se solapa con "%(o)s" '
                    '([%(c)s, %(d)s] mm).\n'
                    'Ajuste los rangos para que no se crucen.'
                ) % {
                    'p': rec.profile,
                    'a': rec.min_thickness, 'b': rec.max_thickness,
                    'o': overlapping.display_name,
                    'c': overlapping.min_thickness, 'd': overlapping.max_thickness,
                })

    def name_get(self):
        result = []
        for r in self:
            result.append((r.id,
                f'[{r.profile}] {r.min_thickness}–{r.max_thickness} mm → {r.visual_label}'))
        return result
