# -*- coding: utf-8 -*-
from odoo import models, fields


class StockLotCostLine(models.Model):
    """
    REGLA DE ORO - Línea de Costo de Lote

    - Fuente única de desglose de costos por lote/tarja.
    - Cualquier módulo que asigne costos a lotes (costeo, logística,
      facturación) debe escribir aquí.
    - El lote (`stock.lot`) consolida estos datos para totales, costo
      por m³, margen, etc.
    """
    _name = 'stock.lot.cost.line'
    _description = 'Línea de Costo de Lote'
    _order = 'date, id'

    name = fields.Char(
        string='Descripción',
        required=True,
        help='Descripción del costo (ej: Fac. Agunsa 9988 - THC San Antonio).',
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lote',
        required=True,
        ondelete='cascade',
        index=True,  # FIX Regla de Oro + performance: búsquedas por lote
        help='Lote/Tarja al que se asocia este costo.',
    )

    cost_type = fields.Selection(
        [
            ('wood', 'Costo Madera'),
            ('logistic', 'Costo Logístico'),
            ('processing', 'Costo de Procesamiento'),
            ('internalfreight', 'Flete Interno'),
            ('portcost', 'Costo Puerto'),
            ('customsagent', 'Agente de Aduanas'),
            ('insurance', 'Seguro'),
            ('administrative', 'Gastos Administrativos'),
            ('other', 'Otros Costos'),
        ],
        string='Tipo de Costo',
        required=True,
        default='wood',
        help='Clasificación del costo para reportes y análisis de margen.',
    )

    amount_usd = fields.Float(
        string='Monto USD',
        digits=(16, 2),
        required=True,
        help='Monto del costo en USD.',
    )

    partnerid = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor del Servicio',
        index=True,
        help='Proveedor asociado a este costo (naviera, agente de aduana, '
             'operador portuario, seguro, etc.).',
    )

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        help='Fecha contable del costo.',
    )

    notes = fields.Text(
        string='Notas',
        help='Notas o referencias adicionales (ej: N° de factura, BL, '
             'comentarios de auditoría).',
    )

    # ════════════════════════════════════════════════════════════════════════
    # TRAZABILIDAD - Origen del Costo (Arquitectura Clase Mundial)
    # ════════════════════════════════════════════════════════════════════════
    # IMPLEMENTADO: 2025-12-13 (Migración a estándar SAP/Oracle/NetSuite)
    # PROPÓSITO: Mantener trazabilidad de costos distribuidos desde embarques