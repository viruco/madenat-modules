# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Billing',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Gestión de Facturación para Exportaciones Madereras',
    'description': """
        Módulo de Facturación MADENAT
        ==============================
        
        Gestiona el proceso completo de facturación separado de logística:
        
        * Consolidación de datos de embarques
        * Proceso de auditoría
        * Proceso de aprobación contable  
        * Generación de facturas en Odoo Accounting
        * Trazabilidad completa del proceso
    """,
    'author': 'MADENAT',
    'website': 'https://www.madenat.cl',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'base_automation',
        'stock',
        'madenat_lumber_core',
        'madenat_lumber_logistics',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/billing_sequences.xml',
        'data/billing_workflows.xml',
        'views/lumber_billing_consolidation_views.xml',
        'views/lumber_billing_actions.xml',
        'data/lumber_billing_menu_data.xml',
        'wizards/lumber_billing_invoice_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'test': ['tests/test_billing_consolidation.py'],
}
