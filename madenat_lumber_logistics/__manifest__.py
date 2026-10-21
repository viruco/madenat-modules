# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Logistics',
    'version': '18.0.1.40.0',
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
        'madenat_lumber_shipping_core',  # Requerido: Define barcos y viajes
        # I1 canónico (CANON/19 §16): is_processor (res.partner) vive aquí.
        'madenat_lumber_reception_improvements'
    ],

    'data': [
        # 1. SEGURIDAD Y ACCESOS
        'security/ir.model.access.csv',
        # AUD-ETQ-07 (2026-10-11): regla de registro multi-compañía de la
        # imputación documental SV (cabecera, líneas y repartos).
        'security/madenat_sv_imputation_rules.xml',
        # Bloque B (CANON/19 §19.11): regla de registro multi-compañía del vínculo.
        'security/madenat_processor_return_link_rules.xml',
        
        # 2. DATOS MAESTROS Y SECUENCIAS
        'data/sequences.xml',
        'data/lumber_document_types_data.xml',
        
        # 3. WIZARDS (Deben cargar antes que las vistas para que los botones funcionen)
        'wizards/lumber_container_rollover_wizard_views.xml',
        'wizards/lumber_container_lot_wizard_views.xml',
        'wizards/lumber_shipment_rebaja_wizard_views.xml',
        # AD-88 (2026-10-01): asistentes de decisión blanda (B-01, B-03/B-06).
        'wizards/lumber_shipment_zarpe_wizard_views.xml',
        'wizards/lumber_container_rebaja_reverse_wizard_views.xml',
        # I1 canónico (CANON/19 §16, 2026-10-02): envío a procesador.
        'wizards/madenat_processor_shipment_wizard_views.xml',
        # I2 (CANON/19 v1.6.0 / AD-91): asistente de imputación documental SV.
        'wizards/madenat_sv_imputation_wizard_views.xml',
        # AD-92 (2026-10-05): rolleo centrado en Embarque.
        'wizards/lumber_vessel_rollover_wizard_views.xml',
        # Sub-bloque 4A (2026-10-04): regularización B-01 (R1 rebaja extemporánea).
        'wizards/lumber_b01_regularization_wizard_views.xml',
        # Bloque 7.2 (2026-10-21): Asistente de importación de consolidación de tarjas desde Excel.
        'wizards/lumber_consolidation_import_wizard_views.xml',

        # 4. REPORTES (Definiciones y Plantillas)
        'reports/lumber_container_reports.xml',            
        'reports/lumber_container_packing_list_template.xml',

        # 5. ACCIONES Y ESTRUCTURA DE MENÚS
        'views/lumber_actions.xml',
        'views/logistics_menus.xml', 
        # I1 canónico (CANON/19 §16): saldo por procesador (stock.quant, solo lectura).
        # Debe cargarse DESPUÉS de logistics_menus.xml (referencia menu_lumber_logistics).
        'views/madenat_processor_balance_views.xml',
        
        # 6. VISTAS PRINCIPALES (Ordenadas por jerarquía operativa)
        'views/lumber_export_shipment_views.xml', # Embarques (Padre)
        'views/lumber_container_views.xml',       # Contenedores (Hijo)
        'views/stock_lot_views_inherit.xml',      # Ajustes en Lotes
        # 🏷️ Programa SV — vínculo de rebajas SV con contenedor/embarque.
        'views/madenat_sv_operation_logistics_views.xml',
        # I2 (CANON/19 v1.6.0 / AD-91): imputación documental SV por guía.
        'views/madenat_sv_imputation_views.xml',
        # Bloque A/B/C (CANON/19 §19.11, 2026-10-10): relación de conciliación
        # envío a procesador ↔ retorno.
        'views/madenat_processor_return_link_views.xml',
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