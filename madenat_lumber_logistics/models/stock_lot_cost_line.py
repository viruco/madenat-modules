# -*- coding: utf-8 -*-
# Extensión de stock.lot.cost.line para campos relacionados con logística de exportación.
# NOTA: Este campo se define aquí (no en madenat_lumber_core) porque referencia
# lumber.shipment.cost.line, que es un modelo de madenat_lumber_logistics.
# Definirlo en core crearía una dependencia inversa prohibida: core → logistics.
from odoo import models, fields


class StockLotCostLine(models.Model):
    _inherit = 'stock.lot.cost.line'

    source_shipment_cost_line_id = fields.Many2one(
        comodel_name='lumber.shipment.cost.line',
        string='Origen: Costo de Embarque',
        ondelete='restrict',
        index=True,
        help=(
            'Línea de costo de embarque desde la cual se distribuyó este costo.\n\n'
            'TRAZABILIDAD:\n'
            '- Si este campo tiene valor: El costo fue distribuido automáticamente\n'
            '  desde un embarque usando el sistema de distribución por volumen/peso.\n'
            '- Si está vacío: El costo fue ingresado manualmente.\n\n'
            'ESTÁNDAR: SAP S/4HANA Freight Cost Allocation, Oracle NetSuite Landed Costs\n'
            'PERMITE: Auditoría completa del origen de cada costo en el lote.'
        ),
    )
