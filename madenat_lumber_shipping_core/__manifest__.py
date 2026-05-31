{
    'name': 'MADENAT Shipping Core',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Logistics',
    'summary': 'Datos Maestros de Transporte Marítimo',
    'author': 'MADENAT Team',
    'depends': ['base','mail', 'uom'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
       # 'views/shipping_menus.xml',#ELIMINADO - Menús migrados a logistics
        'views/shipping_vessel_views.xml',
        'views/shipping_voyage_views.xml',
        'views/shipping_booking_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}