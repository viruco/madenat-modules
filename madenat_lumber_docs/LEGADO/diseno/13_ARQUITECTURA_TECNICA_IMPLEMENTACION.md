# CANON/13_ARQUITECTURA_TECNICA_IMPLEMENTACION — Guía Técnica de Implementación por Perfiles
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Estado: DOCUMENTO CANÓNICO — Traducción técnica de CANON/12
## Ref: CANON/12, CANON/00, CANON/08, Módulos activos

---

# 1. MAPA TÉCNICO DE TRADUCCIÓN

## 1.1 Resumen: de arquitectura funcional a elementos técnicos

| Capa funcional (CANON/12) | Elemento técnico Odoo | ¿Existe? | ¿Qué falta? |
|---|---|---|---|
| 4 perfiles de usuario | 4 `res.groups` con herencia | ❌ | Crear XML de grupos en `security/` |
| 16 pantallas | `ir.actions.act_window` + `ir.ui.view` | Parcial | 7 dashboards y vistas nuevas, extender 4 vistas existentes |
| 28 KPIs | `fields.Float`/`Monetary` computados + vistas pivot/graph | Parcial | 15 campos calculados nuevos, 4 dashboards, 3 vistas pivot |
| 6 Gates de Negocio | Validaciones Python `@api.constrains` + `UserError` | Parcial | 4 gates nuevos (GB-2, GB-4, GB-5, GB-6) |
| Matriz de permisos 14×4 | `ir.model.access.csv` + `ir.rule` | ❌ | Reemplazar CSV actual por matriz completa con los 4 grupos |
| Trazabilidad | `madenat.audit.log` (modelo existe) | Parcial | Extender con 7 eventos nuevos |
| Secuencia de menús | `<menuitem>` con `groups=` por perfil | Parcial | Reorganizar menú raíz con submenús por perfil |

## 1.2 Qué se implementa con qué mecanismo

| Mecanismo | Elementos | Esfuerzo |
|---|---|---|
| **Configuración (XML sin código)** | Grupos de seguridad, menús, acciones de ventana, vistas tree/form/kanban/search | 60% del total |
| **Código Python (modelos)** | Campos computados de KPIs, validaciones de gates, métodos de acción, audit log | 25% del total |
| **Vistas QWeb/JS (dashboards)** | Dashboards con widgets, gráficos embebidos, trazabilidad visual | 15% del total |

---

# 2. MENÚS, ACCIONES Y VISTAS

## 2.1 Estructura actual del menú raíz (PUNTO DE PARTIDA)

```text
🌲 MADENAT Lumber (menu_madenat_root, parent=stock.menu_stock_root, groups=base.group_user)
├── 🚨 Recepciones Pendientes (stock.group_stock_user)
├── 📦 Madera Bruta (Proveedor) (stock.group_stock_user)
├── 🏭 Post-Proceso (Servicios) (stock.group_stock_user)
│   └── Guías Procesadas
├── 📊 Logística Exportación (desde logistics)
│   ├── Embarques
│   ├── Consolidación
│   ├── Contenedores
│   └── Configuración
└── 📊 Auditoría (stock.group_stock_manager)
```

**Problema:** el menú está organizado por módulos, no por perfiles. Todos los usuarios con `base.group_user` ven lo mismo. No hay dashboards de entrada.

## 2.2 Estructura objetivo (4 menús principales por perfil)

```text
🌲 MADENAT Lumber (menu_madenat_root)
│
├── 🔧 Operaciones (group_madenat_operaciones)
│   ├── 📊 Dashboard (dashboard_madenat_ops)           ← NUEVO
│   ├── 📦 Recepciones (action_lumber_reception_raw_only + extend)
│   ├── 🚨 Recepciones Pendientes (existente)
│   ├── 📦 Lotes en Inventario (action_stock_lot_madenat) ← EXTENDER
│   ├── 🚢 Contenedores (action_lumber_container)
│   ├── 🚀 Embarques (action_lumber_export_shipment)
│   └── 📦 Consolidación (action_lumber_container_consolidation)
│
├── 💰 Costos (group_madenat_costos)
│   ├── 📊 Dashboard Costos (dashboard_madenat_costing) ← NUEVO
│   ├── 🏷️ Asignar Costo Base (action_lot_cost_assignment) ← NUEVO
│   ├── 📋 Expedientes Liquidación (action_lumber_cost_distribution)
│   ├── 🚢 Costos de Embarque (action_shipment_cost_lines) ← EXTENDER
│   └── 📊 Auditoría de Costos (action_madenat_cost_audit) ← NUEVO
│
├── 📒 Contabilidad (group_madenat_contabilidad)
│   ├── 📊 Panel Conciliación (action_accounting_reconciliation) ← NUEVO
│   ├── 📋 Landed Costs Contables (action_landed_cost_accounting) ← EXTENDER
│   └── 🔒 Cierre de Período (action_period_close_wizard) ← NUEVO
│
└── 📈 Gerencia (group_madenat_gerencia)
    ├── 📊 Dashboard Gerencial (dashboard_madenat_executive) ← NUEVO
    ├── 💵 Rentabilidad por Embarque (action_shipment_profitability) ← NUEVO
    └── 🔍 Trazabilidad 360 (action_traceability_360) ← NUEVO
```

### 2.2.1 Implementación técnica de menús

**Archivo nuevo:** `custom_addons/madenat_lumber_core/views/madenat_menus_por_perfil.xml`

Este archivo NO reemplaza `lumber_core_menu.xml` — lo complementa. Los menús existentes se conservan y se reasignan `groups=` al grupo correspondiente.

**Regla de migración de menús existentes:**

| Menú existente (XML ID) | Grupo actual | Grupo destino | Acción |
|---|---|---|---|
| `menu_lumber_reception_pending` | `stock.group_stock_user` | `group_madenat_operaciones` | Cambiar groups |
| `menu_lumber_reception` | `stock.group_stock_user` | `group_madenat_operaciones` | Cambiar groups |
| `menu_guia_processing_root` | `stock.group_stock_user` | `group_madenat_operaciones` | Cambiar groups |
| `menu_madenat_audit` | `stock.group_stock_manager` | `group_madenat_gerencia` | Cambiar groups |
| `menu_lumber_logistics` (logistics) | `base.group_user` (implícito) | `group_madenat_operaciones` | Agregar groups explícito |
| `menu_lumber_export_shipment` | — | `group_madenat_operaciones` | Ok |
| Menús de costing | — | `group_madenat_costos` | Agregar groups |

## 2.3 Vistas por perfil — Especificación técnica

### 2.3.1 Operaciones

| Vista | XML ID | Modelo | Tipo | Hereda/Extiende | Archivo |
|-------|--------|--------|------|-----------------|---------|
| Dashboard Operaciones | `dashboard_madenat_ops` | `lumber.reception` (base) | `kanban` + `graph` | NUEVO | `views/madenat_ops_dashboard.xml` |
| Recepción (extendida) | hereda `view_lumber_reception_form` | `lumber.reception` | `form` | `lumber_reception_views.xml` | Modificar existente |
| Lotes (extendida) | hereda `view_stock_lot_form_madenat` | `stock.lot` | `form` (pestañas) | `stock_lot_views.xml` | Modificar existente |
| Contenedor (extendida) | hereda `view_lumber_container_form` | `lumber.container` | `form` | `lumber_container_views.xml` | Modificar existente |
| Embarque (extendida) | hereda `view_lumber_export_shipment_form` | `lumber.export.shipment` | `form` (pestañas) | `lumber_export_shipment_views.xml` | Modificar existente |

**Detalle del Dashboard de Operaciones (`dashboard_madenat_ops`):**

```xml
<!-- Archivo: views/madenat_ops_dashboard.xml -->
<record id="dashboard_madenat_ops" model="ir.ui.view">
    <field name="name">madenat.ops.dashboard</field>
    <field name="model">lumber.reception</field>
    <field name="arch" type="xml">
        <kanban class="o_kanban_dashboard" create="false" delete="false">
            <!-- Tarjetas por estado de recepción -->
            <templates>
                <t t-name="kanban-box">
                    <!-- Widgets: recepciones por estado, lotes pendientes, embarques activos -->
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

### 2.3.2 Costos

| Vista | XML ID | Modelo | Tipo | Acción requerida | Archivo |
|-------|--------|--------|------|------------------|---------|
| Dashboard Costos | `dashboard_madenat_costing` | `stock.lot` | `kanban` + `graph` | NUEVO | `views/madenat_costing_dashboard.xml` |
| Asignación Costo Base | `view_lot_cost_assignment` | `stock.lot` | `tree` editable inline | NUEVO | `views/madenat_lot_cost_assignment.xml` |
| Exp. Liquidación | `view_lumber_cost_distribution_form` | `lumber.cost.distribution` | `form` | EXTENDER | `costing/views/` |
| Auditoría Costos | `view_madenat_cost_audit` | `stock.lot` | `tree` + `pivot` + `graph` | NUEVO | `views/madenat_cost_audit.xml` |

### 2.3.3 Contabilidad

| Vista | XML ID | Modelo | Tipo | Acción requerida | Archivo |
|-------|--------|--------|------|------------------|---------|
| Panel Conciliación | `view_accounting_reconciliation` | `lumber.reception` | `tree` | NUEVO | `views/madenat_accounting_views.xml` |
| Landed Cost Contable | hereda `view_lumber_cost_distribution_form` | `lumber.cost.distribution` | `form` (pestaña) | EXTENDER | `costing/views/` |
| Cierre Período | `view_period_close_wizard` | `madenat.period.close` (nuevo) | `wizard` | NUEVO | `wizard/madenat_period_close.xml` |

### 2.3.4 Gerencia

| Vista | XML ID | Modelo | Tipo | Acción requerida | Archivo |
|-------|--------|--------|------|------------------|---------|
| Dashboard Gerencial | `dashboard_madenat_executive` | `lumber.export.shipment` | `kanban` (dashboard) | NUEVO | `views/madenat_executive_dashboard.xml` |
| Rentabilidad Embarque | `view_shipment_profitability` (extender `lumber_profitability_views.xml`) | `lumber.export.shipment` | `pivot` + `graph` | EXTENDER | `logistics/views/` |
| Trazabilidad 360 | `view_traceability_360` | `stock.lot` | `form` (readonly) | NUEVO | `views/madenat_traceability_360.xml` |

---

# 3. SEGURIDAD Y PERMISOS

## 3.1 Grupos de seguridad — Archivo nuevo

**Archivo:** `custom_addons/madenat_lumber_core/security/madenat_groups.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">

        <!-- Categoría de aplicación MADENAT -->
        <record id="module_category_madenat" model="ir.module.category">
            <field name="name">MADENAT Lumber</field>
            <field name="sequence">10</field>
        </record>

        <!-- Grupo: Operaciones -->
        <record id="group_madenat_operaciones" model="res.groups">
            <field name="name">Operaciones</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('stock.group_stock_user'))]"/>
            <field name="comment">Acceso completo a recepción, staging, stock (datos físicos), contenedores y embarques. No puede modificar costos ni datos contables.</field>
        </record>

        <!-- Grupo: Costos / Auditoría -->
        <record id="group_madenat_costos" model="res.groups">
            <field name="name">Costos y Auditoría</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
            <field name="comment">Gestión de costos base, líneas de costo, distribuciones y auditoría monetaria.</field>
        </record>

        <!-- Grupo: Contabilidad -->
        <record id="group_madenat_contabilidad" model="res.groups">
            <field name="name">Contabilidad</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('account.group_account_invoice'))]"/>
            <field name="comment">Conciliación, validación contable, tasas de cambio, cierre de período.</field>
        </record>

        <!-- Grupo: Gerencia -->
        <record id="group_madenat_gerencia" model="res.groups">
            <field name="name">Gerencia</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[
                (4, ref('base.group_user')),
                (4, ref('group_madenat_operaciones')),
                (4, ref('group_madenat_costos')),
                (4, ref('group_madenat_contabilidad'))
            ]"/>
            <field name="comment">Visión consolidada, autorización de excepciones, cierre de período.</field>
        </record>

    </data>
</odoo>
```

**Nota sobre herencia:** `group_madenat_gerencia` hereda de los otros 3 grupos MADENAT. Esto significa que un usuario de Gerencia ve todo lo que ven Operaciones + Costos + Contabilidad. Esto es intencional: gerencia necesita lectura global.

## 3.2 Matriz `ir.model.access.csv` — Reescritura completa

**Regla:** el CSV actual (31 líneas) se reemplaza por una versión que usa los 4 grupos MADENAT.

**Archivo destino:** `custom_addons/madenat_lumber_core/security/ir.model.access.csv`

| Modelo | Operaciones | Costos | Contabilidad | Gerencia |
|--------|-------------|--------|--------------|----------|
| `lumber.reception` | 1,1,1,0 | 1,0,0,0 | 1,0,1,0 | 1,0,1,0 |
| `lumber.reception.line` | 1,1,1,0 | 1,0,0,0 | 1,0,0,0 | 1,0,0,0 |
| `stock.lot` | 1,1,1,0 | 1,0,1,0 | 1,0,0,0 | 1,0,1,0 |
| `stock.lot.cost.line` | 1,0,0,0 | 1,1,1,1 | 1,0,0,0 | 1,0,0,0 |
| `lumber.cost.distribution` | 1,0,0,0 | 1,1,1,1 | 1,0,1,0 | 1,0,0,0 |
| `lumber.cost.distribution.line` | 1,0,0,0 | 1,1,1,1 | 1,0,0,0 | 1,0,0,0 |
| `lumber.container` | 1,1,1,0 | 1,0,0,0 | 1,0,0,0 | 1,0,1,0 |
| `lumber.export.shipment` | 1,1,1,0 | 1,0,1,0 | 1,0,0,0 | 1,0,1,0 |
| `lumber.shipment.cost.line` | 1,0,0,0 | 1,1,1,1 | 1,0,0,0 | 1,0,0,0 |
| `lumber.billing.consolidation` | 1,0,0,0 | 1,0,0,0 | 1,0,1,0 | 1,0,0,0 |
| `madenat.audit.log` | 1,0,1,0 | 1,0,1,0 | 1,0,1,0 | 1,0,0,0 |
| `lumber.export.formula` | 1,0,0,0 | 1,1,1,0 | 1,0,0,0 | 1,0,0,0 |
| `lumber.ingestion.format` | 1,0,0,0 | 1,1,1,0 | 1,0,0,0 | 1,0,0,0 |
| `madenat.subproducto` | 1,0,0,0 | 1,0,0,0 | 1,0,0,0 | 1,1,1,1 |
| `account.move` (Fase D) | 0,0,0,0 | 0,0,0,0 | 1,1,1,0 | 1,0,0,0 |

**Leyenda:** `perm_read,perm_write,perm_create,perm_unlink`

**Reglas de acceso a nivel registro (`ir.rule`):**
- No se requieren reglas de dominio restrictivas en esta fase. Los 4 grupos comparten visibilidad de lectura sobre todos los registros.
- La restricción es por permiso de escritura (columna `perm_write` del CSV).
- Futuro: si se requiere segmentación por país/cliente, se agregarán `ir.rule` con dominio.

## 3.3 Restricciones de campo por perfil

Para restringir campos específicos dentro de un modelo (ej: Operaciones no puede tocar `wood_cost_usd` en `stock.lot`), se usa el atributo `groups` en las vistas XML y validaciones Python adicionales:

```xml
<!-- En stock_lot_views.xml: campo wood_cost_usd solo editable por Costos -->
<field name="wood_cost_usd" groups="madenat_lumber_core.group_madenat_costos"/>
```

**Campos con restricción de edición por perfil:**

| Modelo | Campo | Editable por | Solo lectura para |
|--------|-------|-------------|-------------------|
| `stock.lot` | `wood_cost_usd` | Costos | Operaciones, Contabilidad, Gerencia |
| `stock.lot` | `cost_line_ids` | Costos | Operaciones, Contabilidad, Gerencia |
| `stock.lot` | `volumen_m3`, `piezas`, `espesor_mm` | Operaciones | Costos, Contabilidad, Gerencia |
| `lumber.reception` | `exchange_rate`, `total_amount_clp` | Contabilidad | Operaciones, Costos, Gerencia |
| `lumber.export.shipment` | `cost_line_ids` (pestaña costos) | Costos | Operaciones, Contabilidad, Gerencia |
| `lumber.cost.distribution` | `state`, líneas | Costos | Contabilidad (solo validación) |

---

# 4. KPIS Y DASHBOARDS

## 4.1 Traducción de KPIs a elementos técnicos

### 4.1.1 KPIs resueltos con campos existentes (SIN CAMBIOS)

Estos ya existen como campos computados en los modelos — solo se exponen en vistas:

| KPI funcional | Campo existente | Modelo | Vista destino |
|---|---|---|---|
| Eficiencia de cubicación | `yield_efficiency_pct` | `lumber.export.shipment` | Dashboard Ops, Dashboard Gerencial |
| Margen bruto consolidado | `gross_margin_pct` | `lumber.export.shipment` | Dashboard Gerencial |
| Margen por embarque | `gross_margin_usd`, `gross_margin_pct` | `lumber.export.shipment` | Rentabilidad por Embarque |
| Revenue total | `total_revenue_usd` | `lumber.export.shipment` | Dashboard Gerencial |
| Costo total | `total_cost_usd` | `stock.lot` | Dashboard Costos, Auditoría |
| Costo por m³ | `cost_per_m3_usd` | `stock.lot` | Dashboard Costos, Auditoría |
| Costo por MBF | `cost_per_mbf_usd` | `stock.lot` | Dashboard Costos, Auditoría |
| Volumen exportado | `total_volume_m3`, `total_volume_mbf` | `lumber.export.shipment` | Dashboard Gerencial |
| % Documental completado | `document_completion` | `lumber.export.shipment` | Dashboard Ops |
| Embarques zarpados | `state` (in_transit, delivered) | `lumber.export.shipment` | Dashboard Ops |

### 4.1.2 KPIs que requieren campos calculados nuevos

| KPI funcional | Campo nuevo | Modelo | Tipo | Dependencias |
|---|---|---|---|---|
| % Lotes con costo asignado | N/A (consulta agregada) | Dashboard | SQL/domain | `stock.lot` WHERE `wood_cost_usd > 0` |
| % Costos adicionales | N/A (consulta agregada) | Dashboard | SQL/domain | AVG(cost_line_ids.sum / wood_cost_usd) |
| Expedientes pendientes | N/A (consulta agregada) | Dashboard | SQL/domain | COUNT(state='draft') |
| Lotes con margen negativo | N/A (consulta agregada) | Dashboard | SQL/domain | WHERE `margin_usd < 0` |
| Recepciones conciliadas | `reconciliation_state` | `lumber.reception` | Selection (NUEVO) | Campo nuevo pendiente/done |
| Tiempo staging→stock | N/A (diferencia de fechas) | `lumber.reception` | Compute | Gate 0 date vs Gate 3 date |
| Tiempo asignación costo | N/A (diferencia de fechas) | `stock.lot` | Compute | `create_date` vs `cost_assigned_date` (NUEVO) |

### 4.1.3 Estrategia de implementación de KPIs agregados

Los KPIs que son agregaciones (conteos, promedios, sumas) **no requieren campos computados store=True**. Se implementan como:

1. **Vistas `pivot` y `graph`** nativas de Odoo — el ORM genera las agregaciones automáticamente.
2. **Dashboards kanban** con `t-foreach` y `search_count()` para conteos rápidos.
3. **Acciones planificadas** (`ir.cron`) solo si el KPI requiere cálculo pesado diario/semanal (no es el caso actual con los volúmenes estimados de MADENAT).

## 4.2 Dashboards — Diseño técnico mínimo

### 4.2.1 Dashboard de Operaciones

**Archivo:** `custom_addons/madenat_lumber_core/views/madenat_ops_dashboard.xml`

**Componentes técnicos:**

| Widget | Implementación |
|--------|---------------|
| Recepciones por estado | `<kanban>` con `search_count()` por estado en `t-foreach` |
| Lotes sin asignar | `self.env['stock.lot'].search_count([('container_id', '=', False)])` |
| Embarques activos | `self.env['lumber.export.shipment'].search_count([('state', 'in', ['draft','confirmed'])])` |
| Alertas (lotes sin costo) | `self.env['stock.lot'].search_count([('wood_cost_usd', '=', 0)])` |
| Gráfico eficiencia | `<graph>` view apuntando a `yield_efficiency_pct` de `lumber.export.shipment` |

### 4.2.2 Dashboard de Costos

**Archivo:** `custom_addons/madenat_lumber_core/views/madenat_costing_dashboard.xml`

| Widget | Implementación |
|--------|---------------|
| Lotes sin wood_cost_usd | `search_count` con filtro `wood_cost_usd = 0` |
| Distribuciones pendientes | `search_count` en `lumber.cost.distribution` state=draft |
| Costo promedio por m³ (gráfico) | `<graph>` tipo línea sobre `stock.lot` agrupado por `create_date:week` |
| Distribución tipos de costo | `<graph>` tipo pie sobre `stock.lot.cost.line` agrupado por `cost_type` |
| Margen negativo | `search_count` en lotes con `margin_usd < 0` |

### 4.2.3 Dashboard Gerencial

**Archivo:** `custom_addons/madenat_lumber_core/views/madenat_executive_dashboard.xml`

| Widget | Implementación |
|--------|---------------|
| Margen bruto consolidado | Campo computado que suma `gross_margin_usd / total_revenue_usd` de embarques del mes |
| Revenue del mes | Suma de `total_revenue_usd` de embarques con filtro de fecha |
| Volumen exportado | Suma de `total_volume_m3` y `total_volume_mbf` |
| Top 5 clientes | `<pivot>` sobre `lumber.export.shipment` agrupado por `customer_id`, ordenado por `gross_margin_usd desc` |
| Top 5 productos | `<pivot>` sobre `stock.lot` agrupado por `product_id`, ordenado por `margin_usd desc` |
| Tendencia márgenes | `<graph>` tipo línea: `gross_margin_pct` por `create_date:month` |
| Eficiencia operativa | `<graph>` tipo barra: `yield_efficiency_pct` por embarque |

---

# 5. VALIDACIONES Y GATES

## 5.1 Traducción de Gates de Negocio a código

| Gate | Implementación técnica | Ubicación | Mecanismo |
|------|----------------------|-----------|-----------|
| **GB-1** (staging completo antes de Gate 3) | Validación en `action_confirm()` de `lumber.reception` | `models/lumber_reception.py` | `_check_lines_complete()` → `UserError` si hay líneas sin producto/subproducto/dimensiones |
| **GB-2** (costo > 0 antes de asignar a contenedor) | Validación en `write()` de `lumber.container` al agregar `lot_ids` | `models/lumber_container.py` o `stock.lot` extendido | `_check_lot_cost()` → `UserError` si `wood_cost_usd <= 0` |
| **GB-3** (contenedores loaded/sealed antes de zarpe) | **YA EXISTE** en `action_set_in_transit()` de `lumber.export.shipment` (líneas 450-458) | `lumber_export_shipment.py` | ✅ EXISTENTE — Sin cambios |
| **GB-4** (costos distribuidos antes de cierre contable) | Nuevo campo `cost_distribution_validated` + validación en wizard de cierre | `wizard/madenat_period_close.py` | `_check_costs_distributed()` → `UserError` |
| **GB-5** (recepción conciliada con factura) | Nuevo campo `reconciliation_state` + validación en cierre de período | `models/lumber_reception.py` | Selection: pending/done/difference |
| **GB-6** (cierre de período) | Wizard `madenat.period.close` que verifica GB-4 + GB-5 + todos los lotes con costo | `wizard/madenat_period_close.py` | `action_close_period()` con validaciones encadenadas |

## 5.2 Especificación de implementación de cada gate faltante

### 5.2.1 GB-1 — Validación pre-Gate 3

```python
# En lumber_reception.py, dentro de action_confirm() o método separado:
def _check_lines_ready_for_gate3(self):
    for reception in self:
        incomplete = reception.reception_line_ids.filtered(
            lambda l: not l.product_id or not l.subproduct_id 
                   or not l.thickness_nominal or not l.width_nominal
        )
        if incomplete:
            raise UserError(
                "No se puede ejecutar Gate 3. %d líneas incompletas. "
                "Verifique producto, subproducto y dimensiones nominales." 
                % len(incomplete)
            )
```

### 5.2.2 GB-2 — Costo antes de contenedor

```python
# En lumber_container.py, sobrescribir write() o action_confirm_load():
def _check_lots_have_cost(self):
    for container in self:
        lots_sin_costo = container.lot_ids.filtered(
            lambda l: not l.wood_cost_usd or l.wood_cost_usd <= 0
        )
        if lots_sin_costo:
            raise UserError(
                "No se puede confirmar la carga. Los siguientes lotes no tienen "
                "costo base asignado (wood_cost_usd = 0):\n%s"
                % "\n".join(lots_sin_costo.mapped('name'))
            )
```

### 5.2.3 GB-4 — Costos distribuidos

```python
# En wizard madenat_period_close.py:
def _check_costs_distributed(self):
    shipments_sin_costos = self.env['lumber.export.shipment'].search([
        ('state', '=', 'in_transit'),
        ('cost_distribution_state', '=', 'pending')
    ])
    if shipments_sin_costos:
        raise UserError(
            "No se puede cerrar el período. %d embarques en tránsito "
            "sin costos logísticos distribuidos: %s"
            % (len(shipments_sin_costos), 
               ", ".join(shipments_sin_costos.mapped('name')))
        )
```

### 5.2.4 GB-5 y GB-6 — Conciliación y cierre

Requieren un wizard nuevo `madenat.period.close` que:
1. Verifica GB-4 (embarques con costos distribuidos).
2. Verifica GB-5 (recepciones conciliadas).
3. Verifica que todos los lotes tengan `wood_cost_usd > 0`.
4. Si todo OK, ejecuta cierre y registra `madenat.audit.log`.

## 5.3 Registro de rechazo o excepción

Todo rechazo de gate debe generar `madenat.audit.log`:

```python
self.env['madenat.audit.log'].create({
    'name': 'Gate GB-2 rechazado',
    'model_name': 'lumber.container',
    'res_id': container.id,
    'user_id': self.env.user.id,
    'description': f'Lotes sin costo: {", ".join(lots_sin_costo.mapped("name"))}',
})
```

---

# 6. PLAN DE IMPLEMENTACIÓN INCREMENTAL

## 6.1 Fase 1 — Grupos de seguridad (1-2 días, SIN cambios de código)

**Entregables:**
- `security/madenat_groups.xml` (4 grupos con herencia)
- Actualización de `security/ir.model.access.csv` (matriz completa con los 4 grupos)
- Actualización de `__manifest__.py` para cargar el nuevo XML de grupos y el CSV

**Validación:** login con cada grupo, verificar que no puede hacer lo que no debe.

**Dependencias:** ninguna. Es el primer paso.

## 6.2 Fase 2 — Reorganización de menús (1 día, SIN cambios de código)

**Entregables:**
- `views/madenat_menus_por_perfil.xml` con los 4 submenús principales
- Asignación de `groups=` a cada `<menuitem>` existente y nuevo
- Los menús de otros módulos (logistics, costing) heredan `groups=` del menú principal

**Validación:** cada perfil ve solo su menú al iniciar sesión.

**Dependencias:** Fase 1 (los grupos deben existir para asignarlos a los menús).

## 6.3 Fase 3 — Vistas por perfil (2-3 días, mayormente XML)

**Entregables:**
- `madenat_ops_dashboard.xml` — Dashboard de Operaciones
- `madenat_costing_dashboard.xml` — Dashboard de Costos
- `madenat_executive_dashboard.xml` — Dashboard Gerencial
- `madenat_cost_audit.xml` — Vista pivot de auditoría de costos
- `madenat_lot_cost_assignment.xml` — Lista editable para asignación masiva de costo base
- `madenat_accounting_views.xml` — Panel de conciliación
- `madenat_traceability_360.xml` — Vista de trazabilidad

**Extensión de vistas existentes (herencia XML):**
- `stock_lot_views.xml` → agregar pestañas "Costos" y "Trazabilidad" con `groups=`
- `lumber_export_shipment_views.xml` → agregar pestaña "Costos" con `groups=`
- `lumber_cost_distribution_views.xml` → agregar pestaña "Contabilidad" con `groups=`

**Dependencias:** Fase 2 (las acciones de menú apuntan a estas vistas).

## 6.4 Fase 4 — Campos calculados y KPIs (2 días, código Python)

**Entregables:**
- `models/lumber_reception.py` → `reconciliation_state` (Selection, nuevo)
- `models/lumber_reception.py` → `gate_duration_hours` (Float compute, staging→stock)
- `models/stock_lot.py` → `cost_assigned_date` (Datetime, nuevo)
- `models/stock_lot.py` → `cost_assignment_duration_days` (Float compute)
- `models/lumber_export_shipment.py` → KPIs de agregación para dashboard gerencial ya existen; solo se exponen en vistas

**Dependencias:** Fase 3 (los dashboards usan estos campos).

## 6.5 Fase 5 — Validaciones y Gates (2-3 días, código Python)

**Entregables:**
- `models/lumber_reception.py` → `_check_lines_ready_for_gate3()` (GB-1)
- `models/lumber_container.py` → `_check_lots_have_cost()` (GB-2)
- GB-3 ya existe en `action_set_in_transit()` ✅
- `models/lumber_cost_distribution.py` → campo `validated_by_accounting` (Boolean + Many2one user)
- `wizard/madenat_period_close.py` + `.xml` → wizard con GB-4, GB-5, GB-6
- Registro `madenat.audit.log` en cada rechazo de gate

**Dependencias:** Fase 4 (los gates usan algunos de los campos nuevos).

## 6.6 Fase 6 — Trazabilidad avanzada (1-2 días)

**Entregables:**
- Extender `madenat.audit.log` con evento_type (Selection: gate_rejected, gate_passed, cost_assigned, forced_reopen, etc.)
- Botón "Trazabilidad" en lote (`action_traceability_360` ya existe parcialmente en `stock_lot`)
- Vista de trazabilidad 360 para gerencia
- Reporte de auditoría (PDF) — opcional, prioridad baja

**Dependencias:** Fase 5 (los eventos de auditoría se están generando).

## 6.7 Fase 7 — Integración contable (5-7 días, Fase D del backlog)

**Entregables:**
- `stock.valuation.layer` automático desde `lumber.cost.distribution`
- `account.move` desde expedientes de liquidación validados
- Conciliación asistida

**Dependencias:** Fase 5 y Fase 6.

---

# 7. RIESGOS Y BRECHAS

## 7.1 Brechas técnicas identificadas

| ID | Brecha | Tipo | Severidad | Mitigación |
|----|--------|------|-----------|------------|
| **BR-01** | No existen grupos MADENAT; todo usa `stock.group_stock_user` | Configuración | Alta | Fase 1 crea los 4 grupos. Migrar menús existentes a los nuevos grupos. |
| **BR-02** | `ir.model.access.csv` actual no distingue entre roles | Configuración | Alta | Reescritura completa en Fase 1. El CSV actual tiene 31 líneas contra `base.group_user` y `stock.group_stock_manager`. |
| **BR-03** | No existen dashboards de entrada por perfil | Desarrollo (vistas) | Media | Fase 3 crea 3 dashboards kanban con widgets. |
| **BR-04** | `lumber.reception` no tiene campo `reconciliation_state` (GB-5) | Desarrollo (modelo) | Media | Agregar Selection en Fase 4. |
| **BR-05** | No existe wizard de cierre de período (GB-6) | Desarrollo (wizard) | Media | Crear `madenat.period.close` en Fase 5. |
| **BR-06** | `madenat.audit.log` existe como modelo pero no se usa sistemáticamente | Desarrollo (integración) | Media | Fase 6 integra audit.log en todos los eventos críticos. |
| **BR-07** | `wood_cost_usd` no tiene validación de asignación obligatoria antes de contenedor (GB-2) | Desarrollo (validación) | Media | Fase 5 agrega validación en `lumber.container`. |
| **BR-08** | Permisos a nivel de campo no existen — un usuario de Operaciones puede técnicamente escribir `wood_cost_usd` si tiene permiso al modelo | Configuración (vistas) | Media | Fase 3 agrega `groups=` en campos de vistas. Fase 1 limita `perm_write` por modelo. |
| **BR-09** | No hay campos para `cost_assigned_date` ni `gate_duration_hours` (KPIs de tiempo) | Desarrollo (modelo) | Baja | Fase 4 agrega campos compute. |
| **BR-10** | Vistas pivot de rentabilidad existen en `lumber_profitability_views.xml` pero no están enlazadas a menú de Gerencia | Configuración (menús) | Baja | Fase 2 enlaza en menú de Gerencia. |

## 7.2 Riesgos de implementación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **R-01: Romper instalación al cambiar grupos** | Media | Alto | Mantener los grupos existentes (`base.group_user`, `stock.group_stock_manager`) como implied de los nuevos. Nadie pierde acceso. |
| **R-02: Regresión en menús existentes** | Baja | Alto | No eliminar menús existentes. Solo agregar `groups=` y crear nuevos menús wrapper. |
| **R-03: Performance en dashboards con muchos lotes** | Baja | Medio | Usar `search_count()` con índices existentes. MADENAT no maneja millones de registros. |
| **R-04: Dependencia circular entre módulos** | Baja | Medio | Todos los nuevos archivos residen en `madenat_lumber_core`. Logistics y costing se extienden vía herencia XML, no vía dependencia inversa. |
| **R-05: Conflicto con constraint `stock_lot_check_cost_positive`** | Media | Medio | El constraint existente (ver CANON/02) debe resolverse antes o durante la Fase 4. Si sigue activo, puede bloquear lotes sin costo en un momento inadecuado. |

## 7.3 Resolución recomendada de R-05

El constraint `stock_lot_check_cost_positive` existe en el sistema. Si está forzando `wood_cost_usd > 0` en todo momento, entonces GB-2 (validación al asignar a contenedor) es redundante pero no dañina. Verificar el estado real antes de Fase 4:

```bash
grep -r "stock_lot_check_cost_positive" custom_addons/
```

Si el constraint está activo, GB-2 se convierte en un warning en lugar de un bloqueo. Si está inactivo, GB-2 es necesario como validación explícita.

---

# 8. CONCLUSIÓN EJECUTIVA

## 8.1 ¿Es suficiente CANON/12 para construir?

**Sí.** La arquitectura operativa define con precisión qué necesita cada perfil. Este documento (CANON/13) traduce esos requisitos a elementos técnicos concretos de Odoo 18 CE.

## 8.2 Resumen de lo que realmente falta

| Capa | ¿Existe base? | ¿Qué falta? | Fase | Esfuerzo |
|------|--------------|-------------|------|----------|
| Grupos de seguridad | ❌ | 4 grupos XML + CSV completo | 1 | 1-2 días |
| Menús por perfil | ❌ | Reorganización + nuevos menús wrapper | 2 | 1 día |
| Vistas/Dashboards | Parcial (vistas de modelo existen) | 7 dashboards/vistas nuevas, 4 extensiones | 3 | 2-3 días |
| Campos de KPIs | Parcial (∼10 de 28 existen) | 3 campos nuevos, 7 expuestos en vistas | 4 | 2 días |
| Gates de negocio | Parcial (GB-3 ya existe) | 5 gates nuevos con validaciones | 5 | 2-3 días |
| Trazabilidad | Parcial (modelo existe, sin integración) | Integración sistemática en 7 eventos | 6 | 1-2 días |
| Integración contable | ❌ | `stock.valuation.layer` + `account.move` | 7 (Fase D) | 5-7 días |

**Esfuerzo total estimado:** 14-20 días para Fase 1-6. +5-7 días para Fase 7 (D).

## 8.3 Siguiente acción técnica concreta

1. **Ejecutar Fase 1:** crear `security/madenat_groups.xml` y actualizar `ir.model.access.csv`.
2. **Verificar instalación:** `docker compose restart odoo18_app && docker compose logs odoo18_app`.
3. **Crear usuarios de prueba:** un usuario por grupo. Verificar que cada uno ve solo lo que debe.
4. **Proceder con Fase 2** inmediatamente después de validar Fase 1.

## 8.4 Principio rector de implementación

> Cada fase debe ser **independientemente testeable y deployable**. No se avanza a la siguiente hasta que la anterior está validada. Los menús y permisos (Fase 1-2) son la base sobre la que se construye todo lo demás. Sin ellos, cualquier dashboard o validación es inútil porque los usuarios equivocados pueden ver o hacer lo que no deben.

---

*Documento creado: 2026-06-05*
*Versión: 1.0.0*
*Autor: Arquitectura MADENAT — CANON/13*