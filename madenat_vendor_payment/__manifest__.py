# -*- coding: utf-8 -*-
{
    'name': '💰 MADENAT - Gestión Profesional de Pagos a Proveedores',
    'version': '18.0.1.2.0',
    'category': 'Accounting/Payment',
    'summary': 'Sistema profesional de pagos a proveedores con clasificación por categorías y trazabilidad completa',
    'description': """
SISTEMA PROFESIONAL DE PAGOS A PROVEEDORES MADENAT
===================================================

🎯 **CARACTERÍSTICAS PRINCIPALES**
---------------------------------

📊 **Gestión por Categorías de Proveedores:**
   • 🌲 Proveedores de Madera
   • 🚚 Transportistas y Fleteros
   • 📦 Empresas de Consolidación
   • 🚢 Navieras y Agencias Marítimas
   • 📋 Agencias Aduanales
   • 🛡️ Aseguradoras
   • 🏗️ Servicios Portuarios
   • ⚙️ Otros Servicios

💰 **Control Financiero Completo:**
   • Estados de pago: Pendiente, Parcial, Pagado
   • Vinculación automática con facturas contables
   • Registro de pagos con trazabilidad completa
   • Cuentas contables específicas por categoría
   • Control de aprobaciones por montos

📋 **Gestión Documental:**
   • Adjunto de documentos de respaldo
   • Control de facturas y contratos
   • Seguimiento de estados de validación
   • Historial completo de movimientos

🔗 **Integraciones Avanzadas:**
   • Conexión nativa con módulo de Contabilidad
   • Vinculación con costos de embarque
   • Integración con logística de exportación
   • Sincronización con facturación MADENAT

🔄 **Flujos de Trabajo Optimizados:**
   • Validación → Facturación → Pago
   • Asignación por embarque, contenedor o lote
   • Aprobaciones multinivel por montos
   • Notificaciones automáticas

📈 **Reportes y Análisis:**
   • Pendientes de pago por categoría
   • Histórico de pagos por proveedor
   • Análisis de costos por embarque
   • Proyecciones de flujo de caja

🎨 **Experiencia de Usuario:**
   • Interfaz intuitiva con iconos visuales
   • Filtros y agrupaciones inteligentes
   • Vistas optimizadas para cada rol
   • Navegación rápida y eficiente

🔐 **Seguridad y Control:**
   • Permisos por roles (Contador, Gerente, Operador)
   • Aprobaciones por montos configurables
   • Auditoría completa de cambios
   • Protección de datos sensibles

⚡ **TECNOLOGÍA Y COMPATIBILIDAD**
---------------------------------
• Desarrollado para Odoo 18.0 Enterprise
• Compatible con estándares contables internacionales
• Optimizado para alto volumen de transacciones
• Arquitectura escalable y mantenible

📦 **MÓDULOS INTEGRADOS**
------------------------
• madenat_lumber_logistics - Costos de embarque
• madenat_lumber_billing - Facturación y consolidaciones
• account - Facturas y pagos contables nativos
• base - Gestión de proveedores y partners

👥 **EQUIPO DE DESARROLLO**
--------------------------
• MADENAT Development Team
• Especialistas en logística forestal
• Expertos en contabilidad y finanzas
• Desarrolladores Odoo certificados

🌐 **SOPORTE Y MÁS INFORMACIÓN**
-------------------------------
• Website: https://www.madenat.cl
• Documentación: https://docs.madenat.cl
• Soporte: soporte@madenat.cl
• GitHub: https://github.com/madenat
    """,
    
    'author': 'MADENAT Development Team',
    'website': 'https://www.madenat.cl',
    'license': 'LGPL-3',
    
    'depends': [
        # Core Odoo
        'base',
        'account',
        'web',
        
        # MADENAT Ecosystem
        'madenat_lumber_logistics',
        'madenat_lumber_billing',
    ],
    
    'data': [
        # ======================
        # SEGURIDAD Y PERMISOS
        # ======================
        'security/ir.model.access.csv',
        
        # ======================
        # DATOS MAESTROS
        # ======================
        'data/account_expense_mapping_data.xml',     # Mapeo cuentas contables
        
        # ======================
        # VISTAS Y INTERFAZ
        # ======================
        'views/account_expense_mapping_views.xml',   # Vistas del mapeo de gastos
        'views/res_config_settings_views.xml',   # Configuración de cuentas
        
        # ======================
        # MENÚS Y ACCIONES
        # ======================
        'views/vendor_payment_menus.xml',            # Menús y acciones
    ],
    
    'demo': [
        # 'demo/vendor_payment_demo.xml',            # Datos de demostración (opcional)
    ],
    
    # ======================
    # CONFIGURACIÓN TÉCNICA
    # ======================
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 0.0,
    'currency': 'USD',
    
    # ======================
    # METADATAS AVANZADAS
    # ======================
    'images': [
        'static/description/icon.png',
    ],
    
    'external_dependencies': {
        'python': [],
    },
    
    'support': 'soporte@madenat.cl',
    'maintainer': 'MADENAT Development Team <desarrollo@madenat.cl>',
    
    # ======================
    # CLASIFICACIÓN APPS
    # ======================
    'tags': [
        'accounting',
        'payment',
        'vendor',
        'supplier',
        'lumber',
        'forestry',
        'export',
        'logistics',
        'madenat',
        'chile',
        'enterprise',
        'professional',
    ],
    
    # ======================
    # CONFIGURACIÓN ODOO STORE
    # ======================
    'live_test_url': 'https://demo.madenat.cl',
}