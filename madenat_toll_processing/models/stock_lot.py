# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    # ==========================================
    # CAMPOS TOLL PROCESSING
    # ==========================================
    
    toll_order_id = fields.Many2one(
        'toll.processing.order',
        string='Orden Procesamiento',
        help='Orden de procesamiento toll asociada a este lote',
        copy=False,
        index=True  # Indexado para búsquedas rápidas
    )
    
    processor_id = fields.Many2one(
        'res.partner',
        string='Procesador Actual',
        domain="[('is_processor', '=', True)]",
        help='Procesador donde está actualmente el lote (si aplica)',
        copy=False
    )
    
    # CLAVE: Campo de agrupación visual
    origin_reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción Origen',
        help='Recepción original para lotes de drop shipment',
        copy=False,
        index=True
    )
    
    # === Mejoras de Robustez ===
    
    is_available_for_toll = fields.Boolean(
        string='Disp. Procesamiento',
        compute='_compute_is_available_for_toll',
        store=True,
        help="Indica si el lote es elegible para ser enviado a maquila."
    )

    @api.depends('toll_order_id', 'quant_ids.quantity')
    def _compute_is_available_for_toll(self):
        for lot in self:
            # Lógica: No tiene orden asignada Y (tiene stock físico > 0 O tiene volumen comercial > 0)
            # Usamos volumen_m3 como proxy de "existencia" si quant no está fiable aún
            has_stock = sum(lot.quant_ids.mapped('quantity')) > 0
            has_volume = getattr(lot, 'volumen_m3', 0) > 0
            
            lot.is_available_for_toll = not lot.toll_order_id and (has_stock or has_volume)
    
    def action_view_source_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lotes Origen',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.source_lot_ids.ids)],
            'context': {
                'search_default_group_by_origin_reception': 1,
            },
        }