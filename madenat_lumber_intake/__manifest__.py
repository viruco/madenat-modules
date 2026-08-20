# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Intake',
    'version': '18.0.0.3.0',
    'summary': 'Puerta única de ingreso global — fachada sobre Recepción y Guía Processing',
    'description': """
Módulo fachada para ingreso operacional simplificado.
No duplica ni reemplaza lumber.reception ni madenat.guia.processing.
En iteraciones futuras, este módulo decidirá el enrutamiento hacia
Recepción o Guía Processing, reutilizando Gates y piezas del core.
    """,
    'author': 'MADENAT',
    'license': 'LGPL-3',
    'category': 'Inventory/Lumber',
    'depends': ['madenat_lumber_core'],
    'data': [
        'security/ir.model.access.csv',
        'security/madenat_intake_security.xml',
        'views/intake_wizard_views.xml',
        'views/intake_console_views.xml',
        'views/intake_reception_facade_views.xml',
        'views/intake_guia_processing_facade_views.xml',
        'views/intake_cancel_wizard_views.xml',
        'views/intake_po_link_wizard_views.xml',
        'views/intake_supplier_link_wizard_views.xml',
        'views/intake_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}