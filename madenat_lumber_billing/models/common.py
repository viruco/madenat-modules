# CORRECCIÓN en /madenat_lumber_billing/models/common.py
from odoo import models, api

class MadenatBillingCommon(models.AbstractModel):
    _name = 'madenat.billing.common'
    _description = 'Utils comunes MADENAT Billing'

    @api.model
    def get_usd_currency(self):
        """
        Obtiene la moneda USD si existe, o retorna la moneda de la compañía.
        """
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        return usd or self.env.company.currency_id