# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Intelligence & OS',
    'version': '18.0.2.2.0',
    'summary': 'Cerebro de Gestión y Remapeo - MADENAT',
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'depends': [
        'madenat_lumber_core',
        'madenat_lumber_purchasing',
        'madenat_lumber_logistics',
        'madenat_lumber_shipping_core',
        'madenat_lumber_costing',
        'madenat_toll_processing',
        'madenat_vendor_payment',
        'madenat_lumber_billing',
    ],
    'data': [
        # 📦 INVENTARIO RECEPCIÓN — Vistas y Acciones (antes que menús)
        'views/inventory_report_views.xml',
        'views/inventory_report_actions.xml',
        # 🏗️ FASE 1 PILOTO — Acción server R2 sobre stock.lot
        'views/stock_report_actions.xml',
        # 🏁 EL GRAN REMAPEO: Menús (dependen de las acciones arriba)
        'views/menu_remapping.xml',
        'views/lumber_reports_menu.xml',
        # 📦 INVENTARIO RECEPCIÓN — Reportes PDF
        'reports/inventory_report_pdf.xml',
    ],
    'installable': True,
    'application': True, # Esta es la App que Felipe y Cristhian verán
}