# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LumberShippingRule(models.Model):
    _name = 'lumber.shipping.rule'
    _description = 'Regla de Cubicación de Exportación'
    _order = 'sequence, id'

    name = fields.Char('Nombre de la Regla', required=True, help="Ej: Exportación USA (Nominal + 1/8)")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    
    # Tipo de Estrategia
    calculation_method = fields.Selection([
        ('metric_actual', 'Métrico Real (Físico)'),
        ('nominal_plus_allowance', 'Imperial Nominal + Sobreancho'),
        ('nominal_exact', 'Imperial Nominal Exacto')
    ], string='Método de Cálculo', default='metric_actual', required=True)

    # Parámetros (Solo visibles si aplica)
    allowance_inches = fields.Float(
        'Sobreancho (Pulgadas)', 
        default=0.125, 
        digits=(16, 4),
        help="Valor a sumar al ancho nominal. Ej: 0.125 para 1/8\""
    )

    @api.constrains('allowance_inches')
    def _check_allowance(self):
        for rec in self:
            if rec.allowance_inches < 0:
                raise ValidationError(_("El sobreancho no puede ser negativo."))
