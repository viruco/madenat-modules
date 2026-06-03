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
