from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Campo calculado para mostrar información personalizada
    custom_display = fields.Char(
        string='Display Personalizado',
        compute='_compute_custom_display'
    )
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Order Line',
        index=True,
        help='Related purchase order line for this stock move'
    )
    
    @api.depends('product_uom_qty', 'state', 'move_line_ids.quantity')
    def _compute_custom_display(self):
        for move in self:
            reserved_qty = sum(move.move_line_ids.mapped('quantity'))
            done_qty = sum(move.move_line_ids.mapped('quantity'))

            if move.state in ['assigned', 'partially_available']:
                display_value = f"{reserved_qty} / {move.product_uom_qty}"
            elif move.state == 'done':
                display_value = f"{done_qty} / {move.product_uom_qty}"
            else:
                display_value = f"0 / {move.product_uom_qty}"

            move.custom_display = display_value
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    _description = "Línea de Movimiento de Inventario Madenat" # Corrige el Warning del log

    # Aseguramos que lot_id se trate como el campo nativo de Odoo
    # Los related deben apuntar a lot_id.nombre_del_campo_en_stock_lot
    lot_thickness_visual = fields.Char(
        string="Medida (Frac)", 
        related='lot_id.espesor_inch_frac', 
        readonly=True
    )
    lot_volumen_m3 = fields.Float(
        string="Vol. Nominal", 
        related='lot_id.volumen_m3', 
        readonly=True
    )
    lot_vol_shipment_m3 = fields.Float(
        related='lot_id.vol_shipment_m3', 
        string='Volumen Embarque',
        store=False,
        readonly=True,
    )