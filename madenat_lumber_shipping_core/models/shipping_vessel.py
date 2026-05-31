from odoo import models, fields, api, _

class ShippingVessel(models.Model):
    _name = 'shipping.vessel'
    _description = 'Motonave / Buque'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nombre del Buque', 
        required=True, 
        index=True, 
        tracking=True,
        help="Nombre oficial de la motonave (ej. MSC ISABELLA)"
    )
    
    imo_number = fields.Char(
        string='Número IMO', 
        index=True, 
        tracking=True,
        help="Número único de 7 dígitos de la Organización Marítima Internacional"
    )
    
    flag_country_id = fields.Many2one(
        'res.country', 
        string='Bandera (País)',
        tracking=True
    )
    
    vessel_type = fields.Selection([
        ('container', 'Portacontenedores'),
        ('bulk', 'Granelero'),
        ('roro', 'Ro-Ro'),
        ('general', 'Carga General')
    ], string='Tipo de Buque', default='container', tracking=True)
    
    capacity_teu = fields.Integer(
        string='Capacidad (TEU)',
        help="Capacidad en unidades equivalentes a 20 pies"
    )
    
    active = fields.Boolean('Activo', default=True)

    _sql_constraints = [
        ('imo_uniq', 'unique (imo_number)', 'El número IMO debe ser único. Ya existe un barco con este IMO.')
    ]

    @api.constrains('imo_number')
    def _check_imo_format(self):
        """Validación opcional de formato IMO (7 dígitos)"""
        for rec in self:
            if rec.imo_number and (not rec.imo_number.isdigit() or len(rec.imo_number) != 7):
                # Advertencia suave o log, no bloqueante para flexibilidad
                pass