# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Intake',
    'version': '18.0.0.4.0',
    'summary': 'Puerta única de ingreso de madera — fachada sobre Recepción y Guía Processing',
    'description': """
Módulo fachada para el ingreso operacional simplificado ("Ingreso de Madera").
No duplica ni reemplaza lumber.reception ni madenat.guia.processing: consolida
ambas fuentes en una consola readonly (vista SQL) y delega el enrutamiento y la
validación a los métodos canónicos del core.

Capacidades:
- Consola única de revisión para Producto y Procesado.
- Asignación masiva de Producto/Subproducto vía los wizards del core.
- Descarga de Guía (PDF) y Packing list (Excel) para ambos flujos.
- Cancelación/reapertura controlada y vinculación de OC/proveedor (Producto).
    """,
    'author': 'MADENAT',
    'license': 'LGPL-3',
    'category': 'Inventory/Lumber',
    'depends': ['madenat_lumber_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/intake_wizard_views.xml',
        'views/intake_console_views.xml',
        'views/intake_reception_facade_views.xml',
        'views/intake_guia_processing_facade_views.xml',
        'views/intake_cancel_wizard_views.xml',
        'views/intake_po_link_wizard_views.xml',
        'views/intake_supplier_link_wizard_views.xml',
        'views/intake_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'madenat_lumber_intake/static/src/js/replace_current_action.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}