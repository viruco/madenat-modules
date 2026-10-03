# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Core',
    'version': '18.0.6.5.0',
    'summary': 'Cimiento Técnico - MADENAT',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'product',
        'purchase',
        # 'sale' garantiza el orden de carga: su columna NOT NULL
        # product_template.sale_line_warn debe existir al cargar el dato de
        # producto maestro de este módulo (esquema preexistente en madenat_test).
        'sale',
        'account',
        'mail',
        'sms',
    ],
    'data': [
        # 🛡️ 1. SEGURIDAD
        'security/madenat_security.xml',
        'security/ir.model.access.csv',

        # 🖼️ 2. VISTAS, ACCIONES Y MAESTROS
        'views/madenat_res_config_settings_views.xml',
        'views/madenat_subproducto_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_lot_actions.xml',

        # 🧙‍♂️ 3. WIZARDS
        'wizard/lumber_reception_mass_update_views.xml',
        'wizard/madenat_guia_mass_update_views.xml',
        'wizard/madenat_sv_operation_views.xml',
        'wizard/lumber_reception_reset_wizard_views.xml',
        'wizard/madenat_guia_processing_reopen_wizard_views.xml',
        'wizard/madenat_guia_processing_historical_reverse_wizard_views.xml',
        'wizard/madenat_guia_processing_documental_correction_wizard_views.xml',

        # ✅ 4. VISTAS DE RECEPCIÓN Y ACCIONES QUE USA EL MENÚ
        'views/guia_processing_views.xml',
        'views/madenat_views_extensions.xml',
        'views/guia_processing_list_search.xml',
        'views/lumber_reception_views.xml',
        'views/lumber_reception_kanban_views.xml',

        # 🏗️ 5. MENÚS
        'views/lumber_core_menu.xml',
        # 🏷️ Programa SV — historial/acciones de etiquetas SV (usa menu_ops_main).
        'views/madenat_sv_operation_views.xml',
        'views/lumber_ingestion_config_views.xml',
        'views/madenat_lumber_product_default_views.xml',

        # 📊 6. REPORTES
        'reports/madenat_guia_report.xml',
        'reports/madenat_guia_report_templates.xml',

        # ⚙️ 7. CONFIGURACIÓN PARAMETRIZABLE
        'data/ingestion_config.xml',
        'data/ingestion_seed_fase2.xml',
        'data/ingestion_seed_fase3.xml',

        # 🌱 8. DATOS SEMILLA
        'data/madenat_subproducto_data.xml',
        'data/madenat_lumber_product_default_data.xml',
        # F3.1 — Secuencia global de etiquetas SV para Lotes Volumen.
        'data/madenat_volume_lot_sequence.xml',
        # 🏷️ Programa SV — secuencia propia del ledger de operaciones SV.
        'data/madenat_sv_operation_sequence.xml',

        # 🎨 9. RANGOS VISUALES NOMINAL COMERCIAL
        'data/thickness_visual_ranges_seed.xml',
    ],
    'installable': True,
    'application': False,
}