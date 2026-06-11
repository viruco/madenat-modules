# CANON/15 — Diagnóstico de Navegación Actual
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Estado: DIAGNÓSTICO — Pre-construcción de menús por perfil

---

# 1. ESTADO ACTUAL DE LA NAVEGACIÓN

## 1.1 Hallazgo principal: doble definición del menú raíz

Existen **dos definiciones** del menú `menu_madenat_root`:

| Archivo | Módulo | Línea | Rol |
|---------|--------|-------|-----|
| `views/lumber_core_menu.xml` | `madenat_lumber_core` | 66-70 | Definición original, parent=`stock.menu_stock_root` |
| `views/menu_remapping.xml` | `madenat_lumber_reports` | 3-6 | **Redefinición**, parent vacío (`sequence="1"` → raíz de primer nivel) |

La segunda definición (reports) **sobreescribe** la primera porque:
- `menu_remapping.xml` declara `menu_madenat_root` con `sequence="1"` y sin `parent=`, lo que lo convierte en un menú de nivel superior en Odoo.
- El módulo `madenat_lumber_reports` depende de `madenat_lumber_core`, por lo que se carga después.
- Odoo resuelve conflictos de XML ID por orden de carga — el último registrado gana.

**Consecuencia:** el menú que ve el usuario final es el definido por `menu_remapping.xml`, **no** el definido por `lumber_core_menu.xml`.

## 1.2 Estructura real del menú que ve el usuario

```
MADENAT Lumber (menu_madenat_root — madenat_lumber_reports)
│
├── 📦 Operaciones (menu_ops_main) ........................ seq=10
│   ├── Abastecimiento
│   │   ├── 🌲 Compra Madera Bruta (purchasing)
│   │   └── 📥 Gestión de Entradas
│   │       ├── 🪵 Madera Bruta (core)
│   │       ├── 🏭 Guías Procesadas (core)
│   │       └── 📋 Historial de Ingresos (core)
│   └── Control de Lotes
│       ├── ⚖️ Ajustes Físicos (Stock)
│       └── Procesamiento Externo (toll_processing)
│
├── 🚢 Exportaciones (menu_export_main) ................... seq=20
│   ├── Embarques y Naves (logistics)
│   └── Bookings y Reservas (shipping_core)
│
├── 📊 Reportes y Listados (menu_madenat_reports_main) .... seq=25
│   ├── 1. Comercial (Según Compra)
│   ├── 2. Medidas Reales (Físico)
│   └── 3. De Embarque (Exportación)
│
├── 💰 Costeo y Finanzas (menu_finance_main) .............. seq=30
│   │   groups="group_madenat_cost_auditor,base.group_system"  ← LEGACY
│   ├── Centro de Costeo
│   │   ├── 💸 Distribuir Gastos (Wizard) [costing]
│   │   ├── 📋 Expedientes de Costeo (Staging) [costing]
│   │   ├── ⚠️ Lotes sin Costear [costing]
│   │   ├── 📈 Tarja Valorizada (Inventario) [costing]
│   │   └── 📊 Análisis de Rentabilidad [logistics action]
│   └── Pagos y Facturación
│       ├── Pagos a Proveedores (vendor_payment)
│       └── Facturación Exportación (billing)
│
├── ⚖️ Auditoría (menu_audit_main) ........................ seq=40
│   ├── Trazabilidad 360° (core → menu_madenat_audit)
│   └── Reportes de Gestión (reports)
│
└── Configuración (menu_madenat_config_root) ............... seq=100
    │   groups="base.group_system"
    ├── 🏗️ Patios de Recepción
    └── 🏷️ Subproductos y Grados
```

## 1.3 Origen de cada menú

| Menú | XML ID | Módulo propietario |
|------|--------|-------------------|
| `menu_madenat_root` | `menu_madenat_root` | `madenat_lumber_reports` (sobreescribe) |
| `menu_ops_main` | `menu_ops_main` | `madenat_lumber_reports` |
| `menu_export_main` | `menu_export_main` | `madenat_lumber_reports` |
| `menu_madenat_reports_main` | `menu_madenat_reports_main` | `madenat_lumber_reports` |
| `menu_finance_main` | `menu_finance_main` | `madenat_lumber_reports` |
| `menu_audit_main` | `menu_audit_main` | `madenat_lumber_reports` |
| `menu_madenat_config_root` | `menu_madenat_config_root` | `madenat_lumber_reports` |
| Submenús importados | `madenat_lumber_core.menu_lumber_reception_pending` y otros | Referenciados por XML ID externo |

---

# 2. MENÚS Y ACCIONES EXISTENTES

## 2.1 Acciones de ventana definidas

| Módulo | Archivo | Acciones |
|--------|---------|----------|
| `madenat_lumber_core` | `views/lumber_core_menu.xml` | `action_lumber_reception_pending`, `action_lumber_reception_raw_only`, `action_guia_processing_list`, `action_madenat_audit_logs`, `action_madenat_patios_recepcion` |
| `madenat_lumber_core` | `views/stock_lot_actions.xml` | `action_view_stock_lot_form` (form modal) |
| `madenat_lumber_logistics` | `views/lumber_actions.xml` | `action_lumber_export_shipment`, `action_lumber_container`, `action_lumber_container_consolidation` |
| `madenat_lumber_costing` | `views/costing_menus.xml` | `action_lots_costing_pending` (lotes sin costear), `action_cost_analysis` (rentabilidad trader) |
| `madenat_lumber_costing` | `views/lumber_cost_distribution_views.xml` | `action_lumber_cost_distribution`, `action_lumber_cost_matrix` |
| `madenat_lumber_reports` | `views/menu_remapping.xml` | `action_madenat_inventory_adjustments`, `action_madenat_patios_recepcion` (duplicada) |

## 2.2 Duplicidades y conflictos detectados

| Problema | Detalle | Archivos involucrados |
|----------|--------|----------------------|
| **Menú raíz duplicado** | `menu_madenat_root` definido en core (parent=stock) y reports (nivel superior) | `lumber_core_menu.xml:66` vs `menu_remapping.xml:3` |
| **Acción duplicada** | `action_madenat_patios_recepcion` definida en core y reports | `lumber_core_menu.xml:49` vs `menu_remapping.xml:131` |
| **Grupos legacy en finanzas** | `menu_finance_main` usa `group_madenat_cost_auditor` (grupo pre-C1) en lugar de `group_madenat_costos` | `menu_remapping.xml:110` |
| **Menú auditoría usa grupo incorrecto** | `menu_madenat_audit` se referencia con `stock.group_stock_manager` (original) pero reports lo pone bajo `menu_audit_main` sin groups | `lumber_core_menu.xml:104` vs `menu_remapping.xml:127` |
| **Menús de costing referencian parent legacy** | Costing usa `parent="madenat_lumber_reports.menu_finance_costing"` — correcto porque reports es dueño real | `costing_menus.xml:38,43,48` |

---

# 3. FLUJO DE USO REAL

## 3.1 Cómo navega cada perfil hoy

### Operaciones
- **Entrada real:** menú `📦 Operaciones` → `Abastecimiento` → `📥 Gestión de Entradas` → `🪵 Madera Bruta`
- También accede a: `Control de Lotes` → `⚖️ Ajustes Físicos`, `🚢 Exportaciones`
- **Fricción:** no hay dashboard de entrada. El operador llega a una lista de recepciones sin contexto de estado general. Debe navegar entre 3-4 menús para ver recepciones, lotes, contenedores y embarques.

### Costos / Auditoría
- **Entrada real:** menú `💰 Costeo y Finanzas`, visible solo para `group_madenat_cost_auditor` y `base.group_system`
- **Problema grave:** el grupo `group_madenat_cost_auditor` es un grupo legacy (C1). El nuevo grupo `group_madenat_costos` NO tiene acceso a este menú porque `menu_remapping.xml:110` no lo incluye en `groups=`.
- El analista de costos usa: `Centro de Costeo` → `⚠️ Lotes sin Costear`, `📊 Análisis de Rentabilidad`, `💸 Distribuir Gastos`

### Contabilidad
- **No tiene menú propio.** No existe un punto de entrada para el perfil contable.
- Las funciones contables (concilización, validación de landed costs, cierre de período) no tienen pantalla ni menú.
- El usuario de contabilidad hoy tendría que navegar por menús de otros perfiles si tuviera permisos.

### Gerencia
- **Entrada real:** menú `📊 Reportes y Listados` (3 reportes), `💰 Costeo y Finanzas` (análisis de rentabilidad), `⚖️ Auditoría`
- **Fricción:** no hay dashboard consolidado. La información está dispersa en 3 secciones del menú. Rentabilidad está bajo Costeo, no bajo un menú gerencial propio.
- `menu_finance_main` requiere `base.group_system` o `group_madenat_cost_auditor` — si gerencia no tiene estos grupos, no ve finanzas.

## 3.2 Comparación con arquitectura deseada

| Aspecto | Estado actual | Arquitectura deseada (CANON/12) |
|---------|--------------|-------------------------------|
| **Operaciones** | Tiene menú (`📦 Operaciones`) agrupado por función | Debe tener dashboard + submenús planos (recepciones, lotes, contenedores, embarques) |
| **Costos** | Tiene menú (`💰 Costeo y Finanzas`) pero usa grupo legacy | Debe usar `group_madenat_costos` y tener dashboard propio |
| **Contabilidad** | **No existe** | Debe tener panel de conciliación, landed costs, cierre de período |
| **Gerencia** | Dispersa entre Reportes, Costeo y Auditoría | Debe tener dashboard consolidado único |
| **Dashboard** | No existe para ningún perfil | Cada perfil debe tener dashboard de entrada |
| **Permisos** | Mezcla grupos legacy (`group_madenat_cost_auditor`, `base.group_system`) con grupos Odoo estándar | Debe usar los 4 grupos creados en C1 |

---

# 4. DESVIACIONES RESPECTO AL OBJETIVO

## 4.1 Qué falta

| Elemento | Estado |
|----------|--------|
| Dashboard de Operaciones | ❌ No existe |
| Dashboard de Costos | ❌ No existe |
| Dashboard de Contabilidad | ❌ No existe |
| Dashboard Gerencial | ❌ No existe |
| Menú de Contabilidad | ❌ No existe |
| Menú de Gerencia independiente | ❌ No existe (disperso) |
| Vistas pivot de rentabilidad en menú gerencial | ❌ Están bajo Costeo |
| Panel de conciliación | ❌ No existe |
| Cierre de período | ❌ No existe |
| Permisos alineados a los 4 grupos nuevos | ❌ `menu_finance_main` usa grupos legacy |

## 4.2 Qué sobra o está duplicado

| Elemento | Problema |
|----------|----------|
| `menu_madenat_root` en `lumber_core_menu.xml` | Redundante — el de reports lo sobreescribe |
| `action_madenat_patios_recepcion` duplicada | Definida en core y reports |
| `📊 Reportes y Listados` como menú independiente | Los reportes deberían estar dentro del menú de cada perfil, no como menú separado |
| `⚖️ Auditoría` como menú independiente | La trazabilidad debe estar en Gerencia; el log de auditoría es transversal |

## 4.3 Qué conviene conservar

| Elemento | Razón |
|----------|-------|
| `menu_remapping.xml` como dueño real de la navegación | Es lo que el usuario ve. Refleja la estructura pensada para operación real |
| Agrupación `Abastecimiento → Gestión de Entradas` | Tiene lógica operativa (separar compra de recepción) |
| `Centro de Costeo` como contenedor de herramientas de costing | Agrupa correctamente las funciones del analista de costos |
| Submenús de logistics (`Embarques y Naves`, `Bookings y Reservas`) | Están correctamente ubicados bajo Exportaciones |
| `Pagos y Facturación` bajo Finanzas | Correcto para el flujo contable futuro |

## 4.4 Qué conviene reorganizar

| Cambio | Razón |
|--------|-------|
| Crear menú `📈 Gerencia` independiente | Agrupar dashboard, rentabilidad y trazabilidad |
| Crear menú `📒 Contabilidad` | Dar entrada al perfil contable |
| Migrar `menu_finance_main` de `group_madenat_cost_auditor` a `group_madenat_costos` | Alinear con grupos C1 |
| Migrar `⚖️ Auditoría` como submenú de Gerencia | La trazabilidad es función gerencial |
| Mover reportes a cada perfil o unificar en Gerencia | Evitar menú "Reportes" genérico |
| Agregar `groups=` explícito a TODOS los menús | Actualmente varios menús no tienen restricción de grupo |

---

# 5. RECOMENDACIÓN DE ALINEACIÓN

## 5.1 Qué hacer antes de construir nuevos menús

1. **Resolver la dualidad del menú raíz.** Decidir si `madenat_lumber_reports` sigue siendo dueño de `menu_madenat_root` o se devuelve a `madenat_lumber_core`.
2. **Migrar `menu_finance_main` groups.** Cambiar `group_madenat_cost_auditor,base.group_system` → `group_madenat_costos,group_madenat_gerencia`.
3. **Agregar `groups=` faltantes.** Todo `<menuitem>` sin `groups=` hereda visibilidad de `base.group_user`. Esto debe corregirse antes de crear nuevos menús.
4. **Eliminar la definición duplicada de `menu_madenat_root` en core.** Si reports es dueño, core no debe definir el mismo XML ID.
5. **Eliminar `action_madenat_patios_recepcion` duplicada.** Dejar solo una definición.

## 5.2 Qué conviene medir o validar en la UI

- ¿El menú `MADENAT Lumber` aparece como raíz o como submenú de Inventario?
- ¿Un usuario sin grupos MADENAT ve el menú?
- ¿Un usuario en `group_madenat_costos` (C1) ve `Costeo y Finanzas`? (Debería verlo, pero hoy no lo ve)
- ¿Un usuario en `group_madenat_contabilidad` ve algún menú MADENAT? (Hoy no)

## 5.3 Tipo de reorganización necesaria

**Reorganización mayor controlada.** No se parte de cero — `menu_remapping.xml` ya provee una estructura funcional. Pero requiere:

1. Corrección de grupos legacy → nuevos grupos C1.
2. Adición de 4 dashboards de entrada.
3. Creación de menú Contabilidad.
4. Separación de Gerencia como menú independiente.
5. Reubicación de submenús (Auditoría → Gerencia, Reportes → disolver).

---

# 6. CONCLUSIÓN EJECUTIVA

## 6.1 ¿Sirve la navegación actual como base?

**Sí, con ajustes.** `menu_remapping.xml` es el dueño real de la navegación y ya tiene una estructura operativa pensada. No hay que tirarlo — hay que extenderlo y corregir sus desviaciones.

## 6.2 Siguiente paso correcto

**Antes de crear `madenat_menus_por_perfil.xml`, ejecutar estos 3 micro-commits:**

| Micro-commit | Acción | Archivo |
|-------------|--------|---------|
| **C3a** | Eliminar `menu_madenat_root` duplicado de `lumber_core_menu.xml` | `views/lumber_core_menu.xml` |
| **C3b** | Eliminar `action_madenat_patios_recepcion` duplicada de `lumber_core_menu.xml` | `views/lumber_core_menu.xml` |
| **C3c** | Migrar `menu_finance_main` groups legacy → grupos C1 + agregar `groups=` faltantes en `menu_remapping.xml` | `views/menu_remapping.xml` |

Después de C3a-C3c, crear **C4: `views/madenat_menus_por_perfil.xml`** con los 4 submenús principales y dashboards, tomando `menu_remapping.xml` como base (no `lumber_core_menu.xml`).

## 6.3 Lo que NO debe hacerse todavía

- No crear dashboards sin tener la base de menús corregida.
- No implementar gates sin tener navegación por perfil.
- No asumir que `lumber_core_menu.xml` es el menú activo — no lo es.

---

*Documento creado: 2026-06-05*
*Versión: 1.1.0 — actualizado 2026-06-06 (post-remediación: +§7 Mapa de Navegación Consolidado)*
*Autor: Arquitectura MADENAT — CANON/15 (Diagnóstico pre-construcción)*

---

# 7. MAPA DE NAVEGACIÓN CONSOLIDADO (Post-Remediación 2026-06-06)

> Este mapa refleja el estado REAL del código de menús a 2026-06-06, tras la remediación de view_mode tree→list, noupdate en billing, y groups en Configuración.
> Leyenda: `[M]` = origen del menú (core/logistics/costing/purchasing/toll/billing/reports), `(A)` = tiene acción asociada, `(G:grupo)` = restricción de grupo explícita.

```
MADENAT Lumber (menu_madenat_root) [core]
│
├── 📦 Operaciones (menu_ops_main) [core]
│   ├── 📊 Dashboard (menu_ops_dashboard) [core] (G:group_madenat_operaciones)
│   ├── Abastecimiento (menu_ops_supply) [core]
│   │   ├── 🌲 Compra Madera Bruta (menu_lumber_purchase) [purchasing] (A:action_madenat_purchase_order)
│   │   └── 📥 Gestión de Entradas (menu_ops_reception_cat) [core]
│   │       ├── 🪵 Madera Bruta (menu_lumber_reception_pending) [core] (A:action_lumber_reception_pending) (G:stock.group_stock_user)
│   │       ├── 🏭 Guías Procesadas (menu_guia_processing_root) [core]
│   │       │   └── Guías Procesadas (menu_guia_processing_list) [core] (A:action_guia_processing_list) (G:stock.group_stock_user)
│   │       └── 📋 Historial de Ingresos (menu_lumber_reception) [core] (A:action_lumber_reception_raw_only) (G:stock.group_stock_user)
│   └── Control de Lotes (menu_ops_inventory) [core]
│       ├── ⚖️ Ajustes Físicos (Stock) (menu_madenat_inventory_adjustments) [core] (A:action_madenat_inventory_adjustments)
│       └── Procesamiento Externo (menu_toll_processing_root) [toll] (G:group_toll_processing_user)
│           └── Órdenes Procesamiento (menu_toll_processing_orders) [toll] (A:action_toll_processing_order) (G:group_toll_processing_user)
│
├── 🚢 Exportaciones (menu_export_main) [core]
│   └── Embarques y Naves (menu_lumber_logistics) [logistics]
│       ├── Embarques (menu_lumber_export_shipment) [logistics] (A:action_lumber_export_shipment)
│       ├── Consolidación (menu_lumber_container_consolidation) [logistics] (A:action_lumber_container_consolidation)
│       ├── Contenedores (menu_lumber_containers) [logistics] (A:action_lumber_container)
│       └── Configuración (menu_logistics_config) [logistics]
│           ├── Motonaves (menu_shipping_vessel) [logistics] (A:shipping_core.action_shipping_vessel)
│           ├── Viajes (menu_shipping_voyage) [logistics] (A:shipping_core.action_shipping_voyage)
│           ├── Reservas (menu_shipping_booking) [logistics] (A:shipping_core.action_shipping_booking)
│           └── Reglas de Cubicación (menu_lumber_shipping_rule) [logistics] (A:action_lumber_shipping_rule)
│
├── 📊 Reportes y Listados (menu_madenat_reports_main) [core]
│   ├── 1. Comercial (Según Compra) (menu_report_commercial) [reports] (A:core.action_madenat_list_commercial)
│   ├── 2. Medidas Reales (Físico) (menu_report_physical) [reports] (A:core.action_madenat_list_physical)
│   ├── 3. De Embarque (Exportación) (menu_report_export) [reports] (A:core.action_madenat_list_export)
│   └── 📈 Reportes de Gestión (menu_lumber_reports_root) [reports]
│
├── 📒 Contabilidad (menu_contabilidad_main) [core]
│   ├── 📊 Panel Conciliación (menu_contabilidad_conciliacion) [core] (G:group_madenat_contabilidad)
│   └── 🔒 Cierre de Período (menu_contabilidad_cierre) [core] (G:group_madenat_contabilidad)
│
├── 💰 Costeo y Finanzas (menu_finance_main) [core]
│   ├── 📊 Dashboard Costos (menu_costos_dashboard) [core] (G:group_madenat_costos)
│   ├── Centro de Costeo (menu_finance_costing) [core]
│   │   ├── 💸 Distribuir Gastos (Wizard) (menu_lumber_cost_distribution) [costing] (A:action_lumber_cost_distribution)
│   │   ├── ⚠️ Lotes sin Costear (menu_lots_costing_pending) [costing] (A:action_lots_costing_pending)
│   │   └── 📊 Análisis de Rentabilidad (menu_cost_analysis) [costing] (A:action_cost_analysis)
│   └── Pagos y Facturación (menu_finance_payments) [core]
│       ├── 💳 Pagos a Proveedores (menu_vendor_payments_root) [reports→vendor_payment]
│       └── Facturación Exportación (menu_lumber_billing_root) [billing] (G:account.group_account_manager)
│           ├── 📋 Consolidaciones (A:action_lumber_billing_consolidation) (G:account.group_account_manager)
│           ├── 📊 Auditoría
│           │   ├── ⏳ Pendientes de Auditar (G:account.group_account_manager)
│           │   ├── 🔍 En Auditoría (G:account.group_account_manager)
│           │   └── ✅ Auditadas (G:account.group_account_manager)
│           ├── 🧾 Facturación
│           │   ├── ✅ Listas para Facturar (G:account.group_account_manager)
│           │   └── 📄 Facturadas (G:account.group_account_manager)
│           └── 📈 Reportes
│               └── 📊 Análisis de Variaciones (G:account.group_account_manager)
│
├── 📈 Gerencia (menu_gerencia_main) [core]
│   ├── 📊 Dashboard Gerencial (menu_gerencia_dashboard) [core] (G:group_madenat_gerencia)
│   └── 🔍 Trazabilidad 360 (menu_gerencia_trazabilidad) [core] (G:group_madenat_gerencia)
│
├── ⚖️ Auditoría (menu_audit_main) [core]
│   └── Trazabilidad 360° (menu_madenat_audit) [core] (A:action_madenat_audit_logs) (G:stock.group_stock_manager)
│
└── Configuración (menu_madenat_config_root) [core] (G:base.group_system,group_lumber_config_manager)
    ├── 🏗️ Patios de Recepción (menu_madenat_config_patios) [core] (A:action_madenat_patios_recepcion) (G:stock.group_stock_manager,base.group_system)
    └── 🏷️ Subproductos y Grados (menu_madenat_config_subproducto) [core] (A:core.action_madenat_subproducto_config) (G:stock.group_stock_manager,base.group_system)
```

## 7.1 Inventario de acciones por módulo

| Módulo | Acción (XML ID) | Modelo | view_mode |
|--------|-----------------|--------|-----------|
| core | action_lumber_reception_pending | lumber.reception | list,form,kanban |
| core | action_lumber_reception_raw_only | lumber.reception | list,form |
| core | action_guia_processing_list | madenat.guia.processing | list,form |
| core | action_madenat_audit_logs | madenat.audit.log | list,form |
| core | action_madenat_inventory_adjustments | stock.quant | list |
| core | action_madenat_patios_recepcion | stock.location | list,form |
| core | action_madenat_subproducto_config | madenat.subproducto | list,form |
| core | action_madenat_lot_cost_assignment | stock.lot | list,form ✅ (corregido) |
| logistics | action_lumber_export_shipment | lumber.export.shipment | list,form |
| logistics | action_lumber_container | lumber.container | list,form |
| logistics | action_lumber_container_consolidation | lumber.container | list,form |
| logistics | action_lumber_shipping_rule | lumber.shipping.rule | list,form ✅ (corregido) |
| logistics | action_madenat_traceability_360 | stock.lot | list,form ✅ (corregido) |
| costing | action_lots_costing_pending | stock.lot | list,form |
| costing | action_cost_analysis | stock.lot | list,pivot,graph,form |
| costing | action_lumber_cost_distribution | lumber.cost.distribution | list,form |
| purchasing | action_madenat_purchase_order | purchase.order | list,kanban,pivot,graph,form |
| purchasing | action_purchase_tracking | purchase.order | list,form ✅ (corregido) |
| toll | action_toll_processing_order | toll.processing.order | list,form |

## 7.2 Correcciones aplicadas en remediación 2026-06-06

| Archivo | Cambio | Vista afectada |
|--------|--------|---------------|
| logistics_menus.xml | tree→list | Reglas de Cubicación |
| madenat_traceability_360.xml | tree→list | Trazabilidad 360 |
| madenat_lot_cost_assignment.xml | tree→list | Asignar Costo Base |
| purchase_tracking_views.xml | tree→list | Seguimiento de Compras |
| lumber_billing_menu_data.xml | noupdate=1→0 | Menús de billing actualizables |
| lumber_core_menu.xml | groups + config_manager | Configuración accesible al Configurador |
