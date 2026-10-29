from odoo import _, models

class ShippingVesselInherit(models.Model):
    _inherit = 'shipping.vessel'

    def action_open_vessel_shipments(self):
        """Abre la lista de Embarques de esta Motonave (sólo consulta)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Embarques de la Motonave %s') % self.name,
            'res_model': 'lumber.export.shipment',
            'view_mode': 'list,form',
            'domain': [('vessel_id', '=', self.id)],
            'context': {'search_default_vessel_id': self.id},
            'target': 'current',
        }
