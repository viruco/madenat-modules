# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Core',
    'version': '18.0.5.0.0',
    'summary': 'Cimiento Técnico - MADENAT',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'product',
        'purchase',
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

        # ✅ 4. VISTAS DE RECEPCIÓN Y ACCIONES QUE USA EL MENÚ
        'views/guia_processing_views.xml',
        'views/guia_processing_list_search.xml',
        'views/lumber_reception_views.xml',
        'views/lumber_reception_kanban_views.xml',
        'views/lumber_ingestion_config_views.xml',

        # 🏗️ 5. MENÚS
        'views/lumber_core_menu.xml',

        # 📊 6. REPORTES
        'reports/madenat_guia_report.xml',
        'reports/madenat_guia_report_templates.xml',

        # ⚙️ 7. CONFIGURACIÓN PARAMETRIZABLE
        'data/ingestion_config.xml',
        'data/ingestion_seed_fase2.xml',
        'data/ingestion_seed_fase3.xml',

        # 🌱 8. DATOS SEMILLA
        'data/madenat_subproducto_data.xml',

        # 🎨 9. RANGOS VISUALES NOMINAL COMERCIAL
        'data/thickness_visual_ranges_seed.xml',
    ],
    'installable': True,
    'application': False,
}