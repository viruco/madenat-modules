# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LumberReception(models.Model):
    _inherit = 'lumber.reception'
    
    toll_order_ids = fields.One2many(
        'toll.processing.order', 
        'source_reception_id', 
        string='Órdenes de Procesamiento'
    )
    
    toll_order_count = fields.Integer(
        string='Cant. Órdenes',
        compute='_compute_toll_order_count'
    )
    
    @api.depends('toll_order_ids')
    def _compute_toll_order_count(self):
        for rec in self:
            rec.toll_order_count = len(rec.toll_order_ids)
            
    def action_create_toll_order(self):
        """Crea una orden de procesamiento desde la recepción (Drop Shipment)"""
        self.ensure_one()
        
        # CORRECCIÓN: Usamos supplier_id en lugar de partner_id
        if not self.supplier_id:
             raise UserError(_("La recepción debe tener un proveedor asignado."))
            
        # Crear la orden
        toll_order = self.env['toll.processing.order'].create({
            'source_type': 'from_drop_ship',
            'source_reception_id': self.id,
            'processor_id': self.supplier_id.id, # CORREGIDO
            'expected_volume_m3': self.commercial_volume_m3, 
            'notes': f"Drop Shipment desde Recepción {self.name}"
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Procesamiento',
            'res_model': 'toll.processing.order',
            'res_id': toll_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_toll_orders(self):
        """Ver órdenes asociadas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Procesamiento',
            'res_model': 'toll.processing.order',
            'view_mode': 'list,form',
            'domain': [('source_reception_id', '=', self.id)],
            'context': {'default_source_reception_id': self.id}
        }