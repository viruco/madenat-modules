# -*- coding: utf-8 -*-
"""Línea de consumo parcial de lote crudo para salida a proceso (AD-66).

Modelo aditivo introducido por AD-66 (2026-09-20) para soportar el envío a
proceso por Balance de Masa (AD-65 §1.6): permite especificar, por lote de
origen, una cantidad parcial (m³) a consumir en lugar del volumen completo.
Coexiste deliberadamente con ``source_lot_ids`` (M2M legacy/fallback) en
``madenat.guia.processing``; ver ``04_DECISION_LOG.md`` AD-66.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MadenatGuiaProcessingSourceLotLine(models.Model):
    _name = 'madenat.guia.processing.source.lot.line'
    _description = 'Línea de consumo parcial de lote crudo para salida a proceso (AD-66)'

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía de Procesamiento',
        required=True,
        ondelete='cascade',
        index=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote Crudo de Origen',
        required=True,
        ondelete='restrict',
        help='Lote del cual se consumirá una cantidad parcial o total hacia proceso externo.',
    )
    qty_to_consume = fields.Float(
        string='Cantidad a Consumir (m³)',
        digits=(16, 3),
        required=True,
        help='Cantidad de volumen (m³) a enviar a proceso desde este lote. '
             'Debe ser mayor que 0 y no exceder el volumen disponible del lote (AD-66).',
    )

    @api.constrains('qty_to_consume', 'lot_id')
    def _check_qty_to_consume_range(self):
        for line in self:
            if line.qty_to_consume <= 0:
                raise ValidationError(
                    "⛔ La cantidad a consumir debe ser mayor que 0 "
                    f"(lote {line.lot_id.name or line.lot_id.id})."
                )
            if line.lot_id and line.qty_to_consume > line.lot_id.volumen_m3:
                raise ValidationError(
                    "⛔ La cantidad a consumir (%.3f m³) excede el volumen disponible "
                    "del lote %s (%.3f m³)." % (
                        line.qty_to_consume, line.lot_id.name, line.lot_id.volumen_m3
                    )
                )
