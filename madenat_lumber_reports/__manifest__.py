# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Intelligence & OS',
    'version': '18.0.1.0.0',
    'summary': 'Cerebro de Gestión y Remapeo - MADENAT',
    'license': 'LGPL-3',
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
        # 🏁 EL GRAN REMAPEO: Aquí es donde Madenat toma el control
        'views/menu_remapping.xml',
        'views/lumber_reports_menu.xml',
    ],
    'installable': True,
    'application': True, # Esta es la App que Felipe y Cristhian verán
}