# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Core',
    'version': '18.0.5.0.0',
    'summary': 'Cimiento Técnico - MADENAT',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': [
        'stock', 'product', 'purchase', 'account', 'mail', 'sms',
    ],
    'data': [
        # 🛡️ 1. SEGURIDAD
        'security/madenat_security.xml', 
        'security/ir.model.access.csv',
        
        # 🖼️ 3. VISTAS Y MAESTROS (Los cuadros)
        'views/madenat_res_config_settings_views.xml',
        'views/madenat_subproducto_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_lot_actions.xml',
        
        # 🧙‍♂️ 4. WIZARDS (Ventanas emergentes)
        'wizard/lumber_reception_mass_update_views.xml',
        'wizard/madenat_guia_mass_update_views.xml', 

        'views/guia_processing_views.xml',
        'views/guia_processing_list_search.xml',
        'views/lumber_reception_views.xml',
        'views/lumber_ingestion_config_views.xml',
        
        # 🏗️ 2. ARQUITECTURA BASE (La pared donde cuelga todo)
        'views/lumber_core_menu.xml', 
        
        # 📊 5. REPORTES
        'reports/madenat_guia_report.xml',      
        'reports/madenat_guia_report_templates.xml',
        
        # ⚙️ 6. CONFIGURACIÓN PARAMETRIZABLE (Fase 1 — Desacoplamiento de hardcodes)
        'data/ingestion_config.xml',
        'data/ingestion_seed_fase2.xml',
        'data/ingestion_seed_fase3.xml',

        # 🌱 7. DATOS SEMILLA (subproductos dependen de fórmulas Fase 3)
        'data/madenat_subproducto_data.xml',

        # 🎨 8. RANGOS VISUALES NOMINAL COMERCIAL (C3 — obs. Cristhian)
        'data/thickness_visual_ranges_seed.xml',
    ],
    'installable': True,
    'application': False, # El Core es el motor, no la App
}