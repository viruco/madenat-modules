# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CreateTollOrderWizard(models.TransientModel):
    _name = 'create.toll.order.wizard'
    _description = 'Wizard para crear Orden Toll Processing'
    
    processor_id = fields.Many2one('res.partner', string='Procesador', required=True, domain="[('is_processor', '=', True)]")
    process_type = fields.Selection([
        ('planing', 'Cepillado'), ('drying', 'Secado'), ('planing_drying', 'Cepillado + Secado'),
        ('treatment', 'Tratamiento Químico'), ('other', 'Otro')
    ], string='Tipo Proceso', required=True, default='planing_drying')
    
    process_cost_per_m3 = fields.Monetary(string='Costo Proceso /m³', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.USD'), required=True)
    lead_time_days = fields.Integer(string='Lead Time (días)', default=7)
    
    lot_ids = fields.Many2many('stock.lot', string='Lotes a Procesar', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids and 'lot_ids' in fields_list:
            res['lot_ids'] = [(6, 0, active_ids)]
        return res
    
    def action_create_toll_order(self):
        self.ensure_one()
        lots = self.lot_ids or self.env['stock.lot'].browse(self.env.context.get('active_ids', []))
        if not lots: raise UserError("No hay lotes seleccionados.")
        
        # Validaciones
        if any(l.toll_order_id for l in lots): raise UserError("Algunos lotes ya tienen orden asignada.")
        if any(l.volumen_m3 <= 0 for l in lots): raise UserError("Algunos lotes tienen volumen 0.")

        toll_order = self.env['toll.processing.order'].create({
            'processor_id': self.processor_id.id,
            'process_type': self.process_type,
            'process_cost_per_m3': self.process_cost_per_m3,
            'lead_time_days': self.lead_time_days,
            'source_type': 'from_stock',
            'source_lot_ids': [(6, 0, lots.ids)],
            'state': 'sent',
            'date_sent': fields.Date.today()
        })
        lots.write({'toll_order_id': toll_order.id, 'processor_id': self.processor_id.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'toll.processing.order',
            'res_id': toll_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
