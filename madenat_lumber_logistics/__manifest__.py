# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Logistics',
    'version': '18.0.1.2.0',
    'category': 'Inventory/Logistics',
    'summary': 'Gestión avanzada de embarques y consolidación de exportación',
    'author': 'MADENAT / Desarrollo Senior',
    'description': """
MADENAT Logistics: Corazón de Exportación
==========================================
Este módulo extiende la funcionalidad de inventario para la gestión de:
* **Consolidación (Tarja):** Asignación de lotes a contenedores con validación de peso/volumen.
* **Flujo de Embarque:** Gestión de motonaves, viajes y cierres de nave (Zarpe).
* **Inteligencia de Negocios:** Análisis de rendimiento (Yield) y rentabilidad financiera.
* **Checklist Documental:** Control de SOLAS/VGM, BL y Facturación.
    """,
    
    # 🔗 DEPENDENCIAS: Blindaje contra errores de campos inexistentes
    'depends': [
        'base', 
        'stock', 
        'mail', 
        'madenat_lumber_core',          # Requerido: Define los lotes
        'madenat_lumber_shipping_core'  # Requerido: Define barcos y viajes
    ],

    'data': [
        # 1. SEGURIDAD Y ACCESOS
        'security/ir.model.access.csv',
        
        # 2. DATOS MAESTROS Y SECUENCIAS
        'data/sequences.xml',
        'data/lumber_document_types_data.xml',
        
        # 3. WIZARDS (Deben cargar antes que las vistas para que los botones funcionen)
        'wizards/lumber_container_rollover_wizard_views.xml',
        'wizards/lumber_container_lot_wizard_views.xml',

        # 4. REPORTES (Definiciones y Plantillas)
        'reports/lumber_container_reports.xml',            
        'reports/lumber_container_packing_list_template.xml',

        # 5. ACCIONES Y ESTRUCTURA DE MENÚS
        'views/lumber_actions.xml',
        'views/logistics_menus.xml', 
        
        # 6. VISTAS PRINCIPALES (Ordenadas por jerarquía operativa)
        'views/lumber_export_shipment_views.xml', # Embarques (Padre)
        'views/lumber_container_views.xml',       # Contenedores (Hijo)
        'views/stock_lot_views_inherit.xml',      # Ajustes en Lotes
        'views/lumber_document_checklist_views.xml',
        
        # 7. 🚀 BI & PROFITABILITY (Fix para error de dependencia de campos)
        # Este archivo contiene las vistas Pivot y Graph que usan campos de 'Logistics'
        'views/lumber_profitability_views.xml',
    ],
    
    'demo': [],
    'installable': True,
    'application': True,  # Aparece en el dashboard principal de Odoo
    'auto_install': False,
    'license': 'LGPL-3',
}