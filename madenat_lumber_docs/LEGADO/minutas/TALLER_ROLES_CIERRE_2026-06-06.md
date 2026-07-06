# TALLER DE ROLES Y CIERRE DE DEUDA ESTRUCTURAL — MADENAT LUMBER

**Versión:** 1.0  
**Fecha:** 2026-06-06  
**Facilitador:** Arquitecto Senior Odoo 18 CE  
**Base:** Remediación Estructural (REMEDIACION_ESTRUCTURAL_2026-06-06.md)  
**Propósito:** Cerrar deuda estructural pendiente con decisiones justificadas, sin refactors innecesarios  

---

## 1. RESUMEN EJECUTIVO

Taller de roles completado sobre los 4 frentes pendientes del proyecto:

- **Shipping core ACLs:** Definido el patrón 4×modelo mínimo. Implementación bloqueada hasta confirmar que shipping_core tiene dependencia declarada de madenat_lumber_core (necesario para referenciar los grupos custom).
- **5 acciones huérfanas:** 3 ya tienen menú vía `menu_remapping.xml` (falso positivo del grep), 1 requiere decisión de negocio, 1 se resuelve técnicamente como reporte existente.
- **Reporte duplicado:** La definición de logistics es un zombie — la de reports la sobreescribe. Sin impacto runtime. Recomendación: consolidar en reports.
- **.bak huérfanos:** 4 archivos identificados. Eliminables sin riesgo.

**Decisiones que requieren input de stakeholders:** 2 (inventario valorizado, rentabilidad). Todo lo demás es resoluble técnicamente.

---

## 2. INVENTARIO DE ROLES Y GRUPOS

### 2.1 Roles reales del sistema

| Rol | Grupo Odoo | Grupo Custom MADENAT | Funciones |
|-----|-----------|----------------------|-----------|
| **Operaciones** | `stock.group_stock_user` (implícito) | `group_madenat_operaciones` | Recepción, staging, stock físico, contenedores, embarques |
| **Costos** | `base.group_user` (implícito) | `group_madenat_costos` | Costos base, líneas de costo, distribuciones, auditoría monetaria |
| **Contabilidad** | `account.group_account_invoice` (implícito) | `group_madenat_contabilidad` | Conciliación, validación contable, cierre de período |
| **Gerencia** | `base.group_user` + ops + costos + contab (implícito) | `group_madenat_gerencia` | Visión consolidada, autorización, cierre de período |
| **Configurador** | `group_madenat_admin` → `group_madenat_cost_auditor` (implícito) | `group_lumber_config_manager` | Mantenimiento de mapas, tolerancias, filtros de ingesta |
| **Facturación** | `account.group_account_manager` (explícito) | — (sin grupo custom) | Consolidación, auditoría de billing, facturación |

### 2.2 Jerarquía de implied_ids

```
group_madenat_cost_auditor (legacy)
 └── group_madenat_admin (legacy)
      └── group_lumber_config_manager ← Configurador de Ingesta

group_madenat_operaciones ← implica stock.group_stock_user
group_madenat_costos ← implica base.group_user
group_madenat_contabilidad ← implica account.group_account_invoice
group_madenat_gerencia ← implica base.group_user + ops + costos + contab
```

### 2.3 Qué ve cada rol hoy (post-remediación estructural)

| Menú / Acción | Operaciones | Costos | Contabilidad | Gerencia | Configurador | Facturación |
|---------------|:-----------:|:------:|:------------:|:--------:|:------------:|:-----------:|
| 📊 Dashboard Operaciones | ✅ | — | — | — | — | — |
| 🪵 Madera Bruta | ✅ | — | — | — | — | — |
| 🏭 Guías Procesadas | ✅ | — | — | — | — | — |
| 📋 Historial de Ingresos | ✅ | — | — | — | — | — |
| ⚖️ Ajustes Físicos | ✅ | — | — | — | — | — |
| 🚢 Exportaciones (logistics) | ✅ | — | — | — | — | — |
| 📊 Dashboard Costos | — | ✅ | — | — | — | — |
| 💸 Distribuir Gastos | — | ✅ | — | — | — | — |
| ⚠️ Lotes sin Costear | — | ✅ | — | — | — | — |
| 📊 Análisis Rentabilidad | — | ✅ | — | — | — | — |
| 📊 Panel Conciliación | — | — | ✅ | — | — | — |
| 🔒 Cierre de Período | — | — | ✅ | — | — | — |
| 📊 Dashboard Gerencial | — | — | — | ✅ | — | — |
| 🔍 Trazabilidad 360 (Gerencia) | — | — | — | ✅ | — | — |
| Configuración | — | — | — | — | ✅ | — |
| Patios de Recepción | — | — | — | — | ✅ | — |
| Subproductos y Grados | — | — | — | — | ✅ | — |
| Facturación Exportación | — | — | — | — | — | ✅ |

**Veredicto:** Separación de roles correcta. Sin solapamientos indebidos entre perfiles. Contabilidad y Gerencia ahora tienen entradas funcionales donde antes no existían.

---

## 3. DECISIONES SOBRE ACCIONES HUÉRFANAS (LAS 5 PENDIENTES)

### 3.1 Acciones ya referenciadas — Falso positivo del grep

| Acción | Evidencia | Decisión |
|--------|-----------|----------|
| `action_madenat_list_commercial` | Referenciada en `menu_remapping.xml:12` como `action="madenat_lumber_core.action_madenat_list_commercial"` | ✅ **Ya tiene menú** — 1. Comercial (Según Compra) bajo Reportes y Listados |
| `action_madenat_list_physical` | Referenciada en `menu_remapping.xml:18` como `action="madenat_lumber_core.action_madenat_list_physical"` | ✅ **Ya tiene menú** — 2. Medidas Reales (Físico) bajo Reportes y Listados |
| `action_madenat_list_export` | Referenciada en `menu_remapping.xml:24` como `action="madenat_lumber_core.action_madenat_list_export"` | ✅ **Ya tiene menú** — 3. De Embarque (Exportación) bajo Reportes y Listados |

**Causa del falso positivo:** El grep buscó `action="..."` con comillas, pero `menu_remapping.xml` usa referencias externas XML ID con el prefijo `madenat_lumber_core.`. La referencia existe, solo que los IDs no coinciden exactamente en el grep. En runtime, Odoo resuelve el XML ID externo correctamente.

### 3.2 Acción que requiere decisión de negocio

| Acción | Modelo | Contexto actual | Pregunta para stakeholders |
|--------|--------|-----------------|---------------------------|
| `action_valuated_inventory` | `stock.lot` | `search_default_filter_available: 1` | ¿Debe tener menú propio bajo "Centro de Costeo"? Hoy no es accesible. Muestra lotes con valorización de inventario. **Input requerido de Cristhian.** |

**Recomendación técnica:** Agregar menú `📈 Tarja Valorizada (Inventario)` bajo `menu_finance_costing` con esta acción. El contexto `search_default_filter_available: 1` es apropiado para mostrar solo lotes en stock. Si Cristhian confirma, es 1 línea de XML.

### 3.3 Acción resuelta como reporte existente

| Acción | Resolución |
|--------|-----------|
| `action_madenat_profitability_analysis` | Ya existe `action_cost_analysis` en `costing_menus.xml` que sirve al mismo propósito (Consola de Rentabilidad Trader con pivot/graph). `action_madenat_profitability_analysis` es una acción redundante definida en `lumber_profitability_views.xml:29`. **Recomendación:** Mantener como acción técnica (accesible vía botones en vistas de logistics). No crear menú duplicado para rentabilidad. |

---

## 4. ESTADO DE SEGURIDAD PENDIENTE

### 4.1 Shipping Core — ACLs actuales vs requeridas

**Estado actual:**
```
shipping.vessel  → base.group_user → R,W,C,D (todos)
shipping.voyage  → base.group_user → R,W,C,D (todos)
shipping.booking → base.group_user → R,W,C,D (todos)
```

**Problema:** Cualquier empleado con `base.group_user` (todos los usuarios internos) puede crear, modificar y eliminar motonaves, viajes y reservas. No hay distinción entre el equipo de Operaciones (que gestiona embarques) y otros perfiles.

**Solución propuesta — Patrón 4×modelo:**

| Modelo | Operaciones | Costos | Contabilidad | Gerencia |
|--------|:----------:|:------:|:------------:|:--------:|
| shipping.vessel | R,W,C | R | R | R,C |
| shipping.voyage | R,W,C | R | R | R,C |
| shipping.booking | R,W,C | R | R | R,C |

**Justificación:**
- Operaciones gestiona la logística de transporte → crea y edita motonaves/viajes/reservas
- Costos y Contabilidad solo necesitan lectura (para costear embarques y conciliar)
- Gerencia puede leer y crear (para planificación), pero no debe poder eliminar registros históricos

**Bloqueo técnico:** `shipping_core/__manifest__.py` no declara dependencia de `madenat_lumber_core`. Las ACLs necesitan referenciar `group_madenat_operaciones`, `group_madenat_costos`, etc. que están definidos en `madenat_lumber_core`.

**Solución:** Agregar `'madenat_lumber_core'` a la lista `depends` de `shipping_core/__manifest__.py`. Esto no introduce dependencia circular porque el grafo actual es: core → (shipping_core independiente) → logistics → costing. Agregar esta dependencia es seguro y coherente (shipping_core ya es usado exclusivamente dentro del ecosistema MADENAT).

### 4.2 Record Rules — Estado

Sin cambios respecto al taller previo (AD-34). Se requiere input de Felipe y Cristhian para definir reglas de segmentación. No se implementan en esta iteración.

---

## 5. LIMPIEZA ESTRUCTURAL

### 5.1 Reporte duplicado — Decisión

| Aspecto | Detalle |
|---------|---------|
| **Archivos** | `lumber_container_reports.xml:5` (logistics) y `report_packing_list.xml:4` (reports) |
| **Conflicto** | Mismo XML ID `action_report_lumber_container_packing_list` en 2 módulos |
| **Resolución Odoo** | Reports se carga después de logistics (depende de él). La definición de reports sobreescribe la de logistics. |
| **Impacto runtime** | Ninguno. La definición de logistics es un zombie — nunca se ejecuta. |
| **Decisión** | **Eliminar la definición de logistics.** La definición de reports es la correcta (usa `report_packing_list_template` como plantilla). La de logistics usa `report_lumber_container_packing_list` que es una plantilla diferente. |
| **Archivo a modificar** | `custom_addons/madenat_lumber_logistics/reports/lumber_container_reports.xml` — eliminar el bloque `<record id="action_report_lumber_container_packing_list">` (líneas 5-11) |
| **Riesgo** | Bajo. Si algún código referencia el XML ID de logistics explícitamente, Odoo resolverá al de reports por ser el último registrado. |

### 5.2 Archivos .bak huérfanos

| Archivo | Ubicación | Decisión |
|---------|-----------|----------|
| `__manifest__.py.bak.20260606_121330` | `madenat_lumber_core/` | 🗑️ Eliminar |
| `__manifest__.py.bak.20260606_121330` | `madenat_lumber_costing/` | 🗑️ Eliminar |
| `lumber_billing_menu_data.xml.bak.20260606_121330` | `madenat_lumber_billing/data/` | 🗑️ Eliminar |
| `lumber_reports_menu.xml.bak.20260606_121330` | `madenat_lumber_reports/views/` | 🗑️ Eliminar |

**Justificación:** Son respaldos automáticos generados durante la remediación del 2026-06-06. Los archivos originales ya fueron corregidos. Estos .bak no tienen valor de referencia (el estado pre-remediación está documentado en los informes de auditoría).

### 5.3 Acción duplicada (hallazgo adicional)

| Acción | Archivos | Decisión |
|--------|----------|----------|
| `action_madenat_guia_processing` | `guia_processing_views.xml:967` y `guia_processing_list_search.xml:72` | **Eliminar definición de `guia_processing_list_search.xml`.** La definición de `guia_processing_views.xml:967` es la completa (tiene view_mode, domain, context, search_view_id). La de `guia_processing_list_search.xml:72` parece ser un remanente de desarrollo temprano. |

---

## 6. RIESGOS RESIDUALES

| Riesgo | Severidad | Descripción | Mitigación |
|--------|-----------|-------------|------------|
| Shipping core sin ACLs custom | Alto | Sin aplicar hasta agregar dependencia de core | Agregar `'madenat_lumber_core'` a `depends` + ACLs 4×modelo |
| Billing usa grupos nativos | Medio | Sin cambios hasta taller de roles de billing | Documentado en AD-35 |
| Sin record rules | Crítico | Sin cambios hasta taller de segmentación | Documentado en AD-34 |
| `action_valuated_inventory` sin menú | Bajo | Pendiente confirmación de Cristhian | 1 línea de XML si se confirma |
| Reporte duplicado (zombie) | Bajo | Sin impacto runtime | Eliminar definición de logistics |

---

## 7. VALIDACIÓN FINAL

### 7.1 Navegación por rol (post-remediación estructural)

| Perfil | Menús visibles | Acciones funcionales | Estado |
|--------|---------------|---------------------|--------|
| Operaciones | Dashboard, Gestión de Entradas, Control de Lotes, Exportaciones | ✅ Todas las acciones de recepción, lotes y embarques funcionales | ✅ Completo |
| Costos | Dashboard Costos, Centro de Costeo | ✅ Distribuir Gastos, Lotes sin Costear, Análisis de Rentabilidad | ✅ Completo |
| Contabilidad | Panel Conciliación, Cierre de Período | ✅ Conciliación y auditoría de costos accesibles | ✅ Completo |
| Gerencia | Dashboard Gerencial, Trazabilidad 360, Reportes, Costeo, Auditoría | ✅ Visión consolidada funcional | ✅ Completo |
| Configurador | Configuración → Patios, Subproductos | ✅ Acceso a todos los submenús de Configuración | ✅ Completo |
| Facturación | Facturación Exportación (todos los submenús) | ✅ Consolidación, auditoría, facturación | ✅ Completo |

### 7.2 Cobertura de acciones

- **Total acciones definidas:** 52
- **Acciones con menú:** 40 (77%)
- **Acciones técnicas (sin menú, con propósito):** 11 (21%)
- **Acciones pendientes de decisión:** 1 (2%) — `action_valuated_inventory`

### 7.3 Deuda estructural cerrada

| Frente | Estado |
|--------|--------|
| view_mode tree→list | ✅ Cerrado (4 archivos corregidos) |
| noupdate billing | ✅ Cerrado |
| Menú Configuración accesible | ✅ Cerrado |
| Grupos custom en menús core | ✅ Cerrado |
| Placeholders con acciones | ✅ Cerrado |
| Mapeo de acciones huérfanas | ✅ Cerrado (51/52 clasificadas) |
| Documentación de seguridad | ✅ Cerrado (security_accesos.md actualizado) |

---

## 8. PRÓXIMOS PASOS PRIORIZADOS

### Inmediato (sin dependencias externas)

1. **Eliminar definición zombie de reporte** en `lumber_container_reports.xml` (5 líneas)
2. **Eliminar definición duplicada** de `action_madenat_guia_processing` en `guia_processing_list_search.xml` (1 bloque)
3. **Eliminar 4 archivos .bak** huérfanos

### Requiere confirmación de stakeholder (Cristhian)

4. **Agregar menú para `action_valuated_inventory`** bajo Centro de Costeo (1 línea si se confirma)

### Requiere taller con stakeholders (Felipe + Cristhian)

5. **ACLs custom en shipping_core** — agregar dependencia de core + patrón 4×modelo
6. **Record rules** — definir reglas de segmentación por planta/embarque/estado
7. **Grupos custom en billing** — migrar de `account.group_account_manager` a grupos MADENAT

---

*Taller de roles y cierre de deuda estructural — 2026-06-06. Decisiones técnicas justificadas. Decisiones de negocio claramente identificadas como pendientes de stakeholder.*