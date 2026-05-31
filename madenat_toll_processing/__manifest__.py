# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Toll Processing',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Manufacturing',
    'summary': 'Gestion de procesamiento en terceros (Toll Processing)',
    'description': '''
MADENAT Toll Processing
=======================
Gestion completa de procesamiento de madera en plantas terceras.
Concepto:
---------
MADENAT mantiene PROPIEDAD del material, pero lo envia a procesador
externo para servicios de valor agregado (cepillado, secado, tratamiento).
Flujos soportados:
------------------
1. Drop Shipment: Proveedor - Procesador directo
2. Stock Existente: Bodega MADENAT - Procesador - Retorno procesado
Caracteristicas:
----------------
* Ordenes de procesamiento a terceros
* Trazabilidad completa (origen - proceso - retorno)
* Control de costos de procesamiento
Autor: Equipo MADENAT
Fecha: Diciembre 2025
    ''',
    'author': 'MADENAT',
    'website': 'https://www.madenat.cl',
    'depends': [
        'base',
        'stock',
        'mail',
        'madenat_lumber_core',
        'madenat_lumber_reception_improvements',
        'account',
        'madenat_lumber_purchasing',
       
    ],
    'data': [
        'security/toll_processing_security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/toll_processing_order_views.xml',
        'views/stock_lot_views.xml',
        'views/lumber_reception_views.xml',
         'views/integration_views.xml', 
        'views/menus.xml',
        'wizards/create_toll_order_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}