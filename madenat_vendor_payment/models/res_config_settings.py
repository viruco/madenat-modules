from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # ================================================================
    # MAPEO DE CUENTAS CONTABLES MADENAT
    # Configuración para eliminar hardcoding de cuentas
    # ================================================================
    
    account_expense_lumber_id = fields.Many2one(
        'account.account',
        string="Cuenta Proveedores Madera",
        config_parameter='madenat_vendor_payment.account_expense_lumber',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta contable para gastos de compra de madera (ej: 610100)"
    )
    
    account_expense_transport_id = fields.Many2one(
        'account.account',
        string="Cuenta Fletes y Transportes",
        config_parameter='madenat_vendor_payment.account_expense_transport',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para fletes y transportes (ej: 624001)"
    )
    
    account_expense_consolidation_id = fields.Many2one(
        'account.account',
        string="Cuenta Consolidación",
        config_parameter='madenat_vendor_payment.account_expense_consolidation',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para gastos de consolidación (ej: 624005)"
    )
    
    account_expense_naviera_id = fields.Many2one(
        'account.account',
        string="Cuenta Fletes Internacionales",
        config_parameter='madenat_vendor_payment.account_expense_naviera',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para navieras y fletes marítimos (ej: 624010)"
    )
    
    account_expense_aduana_id = fields.Many2one(
        'account.account',
        string="Cuenta Gastos Aduanales",
        config_parameter='madenat_vendor_payment.account_expense_aduana',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para agencias aduanales (ej: 624015)"
    )
    
    account_expense_seguros_id = fields.Many2one(
        'account.account',
        string="Cuenta Seguros",
        config_parameter='madenat_vendor_payment.account_expense_seguros',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para seguros (ej: 624020)"
    )
    
    account_expense_portuario_id = fields.Many2one(
        'account.account',
        string="Cuenta Servicios Portuarios",
        config_parameter='madenat_vendor_payment.account_expense_portuario',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta para servicios portuarios (ej: 624025)"
    )
    
    account_expense_otros_id = fields.Many2one(
        'account.account',
        string="Cuenta Otros Gastos",
        config_parameter='madenat_vendor_payment.account_expense_otros',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help="Cuenta por defecto para otros gastos (ej: 624030)"
    )