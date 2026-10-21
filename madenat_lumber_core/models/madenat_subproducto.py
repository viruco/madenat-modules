# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MadenatSubproducto(models.Model):
    _name = 'madenat.subproducto'
    _description = 'Catálogo de Sub-productos MADENAT'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True, help="Ej: BLANK CLEAR, BLANK PANELEADO")
    code = fields.Char('Código', required=True, help="Código corto para reportes")
    description = fields.Text('Descripción')
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean('Activo', default=True)

    # ── Familia de Cálculo (H4 / AD-130) ─────────────────────────────────
    calculation_family = fields.Selection([
        ('blank', 'Blanks (Compra = Exportación, F5085 con +1/8")'),
        ('s2s', 'Cepillado RIP S2S (F1550 con +1/8", Compra mm)'),
        ('rough', 'Rugoso / Aserrada (Métrico Puro, Compra = Exportación)'),
    ], string='Familia de Cálculo', default='s2s', required=True,
    help="Define la familia de cubicación y reglas volumétricas según H4 / AD-130.")

    # ── Asociación estructural a caminos de ingesta ──────────────────────
    allowed_formula_ids = fields.Many2many(
        'lumber.export.formula',
        'madenat_subproducto_formula_rel',
        'subproducto_id',
        'formula_id',
        string='Perfiles de Ingesta Permitidos',
        help="Caminos de ingesta donde este subproducto/grado puede usarse.\n"
             "Sin selección = visible en todos los perfiles (comportamiento legacy)."
    )

    @api.model
    def _init_calculation_families(self):
        """Inicializa calculation_family según el nombre/código de registros existentes."""
        for rec in self.search([]):
            s = f"{rec.name or ''} {rec.code or ''}".upper()
            if 'BLANK' in s or 'BLANCK' in s:
                target = 'blank'
            elif 'ROUGH' in s or 'ASERRADA' in s:
                target = 'rough'
            else:
                target = 's2s'
            if rec.calculation_family != target:
                rec.calculation_family = target

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código del sub-producto debe ser único'),
        ('name_unique', 'UNIQUE(name)', 'El nombre del sub-producto debe ser único'),
    ]

    @api.constrains('code')
    def check_code_format(self):
        """Validar formato del código."""
        for record in self:
            if record.code and not record.code.replace(' ', '').replace('-', '').isalnum():
                raise ValidationError(
                    _('El código debe contener solo letras, números, espacios y guiones.')
                )
