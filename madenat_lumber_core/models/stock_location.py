# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_patio = fields.Boolean(
        string='Es Patio de Madera',
        default=False,
        index=True,
        help='Indica si esta ubicación corresponde a un patio operativo para recepción o almacenamiento de madera.',
    )
    patio_type = fields.Selection([
        ('service', 'Servicio / Cepillado'),
        ('port', 'Puerto / Embarque'),
    ], string='Tipo de Patio', index=True,
       help='Clasificación operativa del patio: Servicio (cepillado, maquila, volumen) o Puerto (recepción para embarque).')

    @api.model
    def resolve_patio_by_type(self, patio_type):
        """Resuelve dinámicamente el patio operativo activo según su tipo.
        Retorna (patio_record, warning_message).
        Si no hay exactamente un patio activo, patio_record es False y warning_message detalla el caso.
        """
        patios = self.search([
            ('is_patio', '=', True),
            ('patio_type', '=', patio_type),
            ('usage', '=', 'internal'),
        ])
        if len(patios) == 1:
            return patios[0], None
        elif len(patios) == 0:
            msg = f"Advertencia operativa: No existe ningún patio activo clasificado como tipo '{patio_type}'. No se realizó asignación automática."
            return False, msg
        else:
            nombres = ", ".join(patios.mapped('name'))
            msg = f"Advertencia operativa: Existen múltiples patios activos clasificados como tipo '{patio_type}' ({nombres}). Se requiere selección manual."
            return False, msg
