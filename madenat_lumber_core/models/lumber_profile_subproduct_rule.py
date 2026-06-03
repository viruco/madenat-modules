# -*- coding: utf-8 -*-
"""
REGLAS PERFILâ†"SUBPRODUCTO (Fase 2 - Modelo Persistente)

Define que subproductos estan permitidos, prohibidos o bloqueados para cada perfil
de ingesta. Alimenta los wizards de recepcion y guia de procesamiento.

Prioridad de fuentes (runtime):
  1. Este modelo (registros activos)
  2. ir.config_parameter 'madenat.profile_subproduct_filters' (Fase 1, fallback)
  3. Hardcode legacy: f5085->forbidden S2S/RIP, f1550->allowed S2S, metric->sin filtro
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class LumberProfileSubproductRule(models.Model):
    _name = 'lumber.profile.subproduct.rule'
    _description = 'Reglas Perfil<->Subproducto'
    _order = 'profile, rule_type, keyword'
    _sql_constraints = [
        ('unique_profile_rule_keyword', 'UNIQUE(profile, rule_type, keyword)',
         'Ya existe una regla con ese perfil, tipo y keyword.'),
    ]

    profile = fields.Selection([
        ('f5085', 'Blanks Clear (f5085)'),
        ('f1550', 'S2S / Rough (f1550)'),
        ('metric', 'Madera Bruta (metrico)'),
    ], string='Perfil de Ingesta', required=True, index=True,
       help='Perfil al que aplica esta regla de subproducto.')

    rule_type = fields.Selection([
        ('allowed', 'Permitido'),
        ('forbidden', 'Prohibido (filtro visual)'),
        ('forbidden_in_lock', 'Prohibido (candado)'),
    ], string='Tipo de Regla', required=True,
       help='Permitido: solo se muestran subproductos que contienen este keyword.\n'
            'Prohibido (filtro visual): se ocultan subproductos con este keyword.\n'
            'Prohibido (candado): se bloquea la asignacion.')

    keyword = fields.Char('Keyword', required=True,
        help='Palabra clave a buscar en el nombre del subproducto (ej: S2S, RIP, ROUGH, BLANK).')

    active = fields.Boolean('Activo', default=True,
        help='Desmarque para deshabilitar esta regla sin eliminarla.')

    @api.constrains('keyword')
    def _check_keyword_not_empty(self):
        for rec in self:
            if not rec.keyword or not rec.keyword.strip():
                raise ValidationError(_('El keyword no puede estar vacio.'))

    def name_get(self):
        result = []
        type_labels = {
            'allowed': 'Permitido',
            'forbidden': 'Prohibido',
            'forbidden_in_lock': 'Bloqueado',
        }
        for r in self:
            tl = type_labels.get(r.rule_type, r.rule_type)
            result.append((r.id, '[%s] %s: %s' % (r.profile, tl, r.keyword)))
        return result
