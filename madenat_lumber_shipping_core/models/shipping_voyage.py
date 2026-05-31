# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ShippingVoyage(models.Model):
    _name = 'shipping.voyage'
    _description = 'Viaje Marítimo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'etd desc'
    _rec_name = 'display_name'

    # ==================== CONSTRAINTS ====================
    _sql_constraints = [
        ('unique_vessel_voyage', 
         'UNIQUE(vessel_id, voyage_reference)',
         '⚠️ Ya existe un viaje con esta referencia para este buque. Verifique que no esté duplicando información.')
    ]

    name = fields.Char('Referencia Interna', compute='_compute_names', store=True)
    display_name = fields.Char('Nombre Mostrado', compute='_compute_names', store=True)

    vessel_id = fields.Many2one(
        'shipping.vessel', 
        string='Motonave', 
        required=True, 
        ondelete='restrict', 
        tracking=True
    )
    
    voyage_reference = fields.Char(
        string='N° Viaje Naviera', 
        required=True, 
        tracking=True,
        help="Referencia del viaje dada por la línea (ej. 052W)"
    )
    
    # Puertos (Usamos res.country.state como aproximación robusta o char simple si no hay maestro de puertos)
    # Mejor práctica Odoo: Usar Char o crear modelo shipping.port. Usaremos Char para simplicidad robusta.
    port_of_loading = fields.Char('Puerto de Origen', required=True, tracking=True, default='Coronel, CL')
    port_of_discharge = fields.Char('Puerto de Destino', required=True, tracking=True)
    
    etd = fields.Date('ETD (Salida Estimada)', required=True, tracking=True)
    eta = fields.Date('ETA (Llegada Estimada)', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('departed', 'Zarpado'),
        ('arrived', 'Arribado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', tracking=True, group_expand='_expand_states')

    @api.depends('vessel_id.name', 'voyage_reference')
    def _compute_names(self):
        for rec in self:
            vessel = rec.vessel_id.name or 'Sin Buque'
            ref = rec.voyage_reference or 'S/N'
            rec.name = f"{vessel} / {ref}"
            rec.display_name = f"🚢 {vessel} | V.{ref}"

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]