# -*- coding: utf-8 -*-
"""
Extensión de product.product para inventario valorizado - Odoo 18 CE
VERSIÓN CORREGIDA: Sin store=True para evitar problemas de rendimiento
"""
from odoo import models, fields, api

class ProductProductExtended(models.Model):
    _inherit = 'product.product'
    
    # CAMPOS COMPUTADOS PARA INVENTARIO VALORIZADO (NO ALMACENADOS)
    stock_m3 = fields.Float(
        'Stock en m³',
        digits=(16, 3),
        compute='_compute_lumber_inventory_metrics',
        help="Volumen total en metros cúbicos disponible en stock (calculado en tiempo real)"
    )
    
    average_cost_usd_m3 = fields.Float(
        'Costo Promedio m³ (USD)',
        digits=(16, 2),
        compute='_compute_lumber_inventory_metrics',
        help="Costo promedio ponderado por metro cúbico (calculado en tiempo real)"
    )
    
    inventory_value_usd = fields.Float(
        'Valor Inventario (USD)',
        digits=(16, 2),
        compute='_compute_lumber_inventory_metrics',
        help="Valor total del inventario en USD (calculado en tiempo real)"
    )
    
    def _compute_lumber_inventory_metrics(self):
        """
        Calcular métricas de inventario en tiempo real
        OPTIMIZADO: Sin store=True para evitar problemas de rendimiento
        """
        for product in self:
            try:
                # Obtener todos los lotes disponibles para este producto
                # Usamos una búsqueda directa que se ejecuta solo cuando se visualiza
                available_lots = self.env['stock.lot'].search([
                    ('product_id', '=', product.id),
                    ('quant_ids.quantity', '>', 0),
                    ('quant_ids.location_id.usage', '=', 'internal')
                ])
                
                total_volume = sum(available_lots.mapped('volumen_m3'))
                total_cost = sum(available_lots.mapped('total_cost_usd'))
                
                product.stock_m3 = total_volume
                product.average_cost_usd_m3 = total_cost / total_volume if total_volume > 0 else 0.0
                product.inventory_value_usd = total_cost
                
            except Exception:
                # En caso de error, establecer valores por defecto
                product.stock_m3 = 0.0
                product.average_cost_usd_m3 = 0.0
                product.inventory_value_usd = 0.0