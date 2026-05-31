# -*- coding: utf-8 -*-

from odoo import models, api

class MadenatCoreUtils(models.AbstractModel):
    _name = 'madenat.core.utils'
    _description = 'Utilidades Core Madenat'  # ✅ AGREGAR ESTA LÍNEA
    
    @api.model
    def resolve_partner_record(self, hint):
        """✅ REGLA DE ORO: Siempre retornar recordset, nunca ID entero"""
        if not hint:
            return self.env['res.partner']  # Recordset vacío
        
        Partner = self.env['res.partner']
        
        # Si hint es un ID entero
        if isinstance(hint, int):
            partner = Partner.browse(hint)
            return partner if partner.exists() else self.env['res.partner']
        
        # Si hint es texto (nombre, VAT, etc.)
        partner = Partner.search([('name', 'ilike', str(hint))], limit=1)
        return partner or self.env['res.partner']

    @api.model
    def resolve_currency_record(self, hint):
        """✅ REGLA DE ORO: Retornar recordset de moneda"""
        if not hint:
            return self.env['res.currency']
        
        Currency = self.env['res.currency']
        if isinstance(hint, int):
            rec = Currency.browse(hint)
            return rec if rec.exists() else self.env['res.currency']
        else:
            rec = Currency.search([('name', 'ilike', hint)], limit=1)
            return rec or self.env['res.currency']

    @api.model
    def resolve_uom_record(self, hint):
        """✅ REGLA DE ORO: Retornar recordset de UOM"""
        if not hint:
            return self.env['uom.uom']
        
        Uom = self.env['uom.uom']
        if isinstance(hint, int):
            rec = Uom.browse(hint)
            return rec if rec.exists() else self.env['uom.uom']
        else:
            rec = Uom.search([('name', 'ilike', hint)], limit=1)
            return rec or self.env['uom.uom']