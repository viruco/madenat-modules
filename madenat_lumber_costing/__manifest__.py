# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Costing',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Sistema de costeo multi-nivel para lotes de madera',
    'description': '''
        Sistema completo de costeo para MADENAT:
        - Costeo de madera (compra)
        - Costeo logístico (embarque)
        - Costeo de proceso
        - Distribución automática de costos
        - Valorización de inventario
    ''',
    'author': 'MADENAT Implementation Team',
    'website': 'https://www.madenat.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'madenat_lumber_core',
        'madenat_lumber_logistics',
        'madenat_lumber_shipping_core',
        # 🛑 ELIMINADO: 'madenat_lumber_costing' (Un módulo no puede depender de sí mismo)
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_lot_costing_views.xml',
        'data/ir_sequence_data.xml',
        'views/lumber_cost_distribution_views.xml',
      #  'views/costing_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}