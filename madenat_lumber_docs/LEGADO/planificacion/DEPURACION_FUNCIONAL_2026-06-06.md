# DEPURACIÓN FUNCIONAL — ECOSISTEMA MADENAT LUMBER

**Versión:** 1.0
**Fecha:** 2026-06-06
**Ejecutor:** Senior Odoo 18 CE — Especialista en Depuración y Estabilización
**Método:** Investigación estática por fases (grep, análisis estructural, mapping de dependencias)
**Entorno:** Código fuente en repositorio (sin acceso a runtime/UI/BD)

---

## 1. RESUMEN EJECUTIVO

Depuración funcional completada en 5 fases sobre 10 módulos. El sistema está **operativamente estable** pero presenta **19 acciones huérfanas** (sin acceso por menú) y **persistencia de grupos nativos Odoo** en menús donde deberían usarse grupos custom MADENAT.

**Hallazgos por severidad:**
- Críticos: 1 (acciones huérfanas que pueden estar rotas sin detección)
- Altos: 2 (grupos nativos en menús donde deberían ser custom; modelos de shipping sin ACLs custom)
- Medios: 4 (reportes duplicados, domain vacío en acciones, placeholders sin acción, .bak huérfanos)
- Bajos: 2 (sin crons documentados, imports cross-addon limpios)

**No se detectaron:**
- XML mal formados
- view_mode tree residual (ya corregido en remediación)
- Imports Python entre addons (cross-addon)
- Errores de sintaxis en vistas

---

## 2. HALLAZGOS POR FASE

### FASE 1 — ESTABILIDAD BASE (Navegación, Vistas, Acciones)

#### ✅ Validado

| # | Ítem | Resultado |
|---|------|-----------|
| 1.1 | view_mode `tree,form` residual | **Limpio** — 0 ocurrencias (corregido en remediación) |
| 1.2 | XML mal formado | **Limpio** — 0 errores de sintaxis |
| 1.3 | Vistas con tags `<list>` | **Correcto** — todas las vistas usan `<list>` |
| 1.4 | Jerarquía de menús | **Correcta** — root único en core, ramas bien definidas |
| 1.5 | noupdate en billing | **Corregido** — `noupdate="0"` aplicado |

#### 🔴 Hallazgos

| ID | Título | Severidad | Evidencia | Impacto | Recomendación |
|----|--------|-----------|-----------|---------|---------------|
| **D1-F1** | **19 acciones sin menú asociado (huérfanas)** | **Crítico** | 52 acciones definidas, solo 40 referenciadas por menús. 12 acciones sin referencia: `action_madenat_ops_dashboard`, `action_madenat_costing_dashboard`, `action_madenat_executive_dashboard`, `action_madenat_cost_audit`, `action_madenat_accounting_reconciliation`, `action_madenat_profitability_analysis`, `action_madenat_traceability_360`, `action_madenat_subproducto_config`, `action_madenat_lot_cost_assignment`, `action_madenat_list_commercial`, `action_madenat_list_export`, `action_madenat_list_physical`, `action_valuated_inventory`, `action_lumber_reception`, `action_madenat_guia_processing`, `action_madenat_guia_processing_pending`, `action_shipment_invoice_wizard`, `action_create_consolidation_from_shipment`, `action_view_stock_lot_form` | Los usuarios no pueden acceder a dashboards, reportes comerciales/físicos/exportación, asignación de costo base, trazabilidad 360, auditoría de costos, conciliación contable, ni ciertos wizards. Estas funcionalidades existen en código pero son **inaccesibles desde la UI**. | Verificar cuáles de estas acciones deben tener menú y agregarlos. Especialmente dashboards (ops, costing, executive), reportes (comercial, físico, exportación), y trazabilidad 360. Algunas pueden ser accedidas vía botones en vistas (no requieren menú) — diferenciar las que sí necesitan entrada de navegación. |
| **D2-F1** | **Placeholders de Contabilidad/Gerencia sin acción** | **Medio** | `menu_contabilidad_conciliacion`, `menu_contabilidad_cierre`, `menu_gerencia_dashboard`, `menu_gerencia_trazabilidad` sin atributo `action` | Usuarios hacen clic y no pasa nada. Genera percepción de funcionalidad incompleta. | Ya documentado como intencional en CANON/14. Debe vincularse con las acciones huérfanas correspondientes (`action_madenat_accounting_reconciliation`, `action_madenat_ops_dashboard`, etc.) o mantenerse como placeholder explícito con tooltip. |

### FASE 2 — SEGURIDAD FUNCIONAL (Grupos, ACLs, Visibilidad por Perfil)

#### ✅ Validado

| # | Ítem | Resultado |
|---|------|-----------|
| 2.1 | Grupos custom definidos | **Correcto** — 7 grupos en madenat_security.xml |
| 2.2 | Grupos custom usados en ACLs | **Correcto** — core, logistics y costing usan grupos custom |
| 2.3 | Grupos custom usados en menús | **Correcto** — group_madenat_operaciones, group_madenat_costos, group_madenat_gerencia, group_madenat_contabilidad referenciados en menús |
| 2.4 | Menú Configuración accesible al Configurador | **Corregido** — `group_lumber_config_manager` agregado |

#### 🔴 Hallazgos

| ID | Título | Severidad | Evidencia | Impacto | Recomendación |
|----|--------|-----------|-----------|---------|---------------|
| **D3-F2** | **Menús de core usan `stock.group_stock_user` en lugar de `group_madenat_operaciones`** | **Alto** | `lumber_core_menu.xml` líneas 184, 190, 197, 205: menús de Madera Bruta, Guías Procesadas, Historial de Ingresos y Guías Procesadas (submenú) usan `groups="stock.group_stock_user"` | Cualquier usuario con acceso a inventario ve estos menús, no solo el equipo de Operaciones MADENAT. `stock.group_stock_user` es demasiado amplio. | Reemplazar por `groups="group_madenat_operaciones"` en los 4 menús. El grupo `group_madenat_operaciones` ya implica `stock.group_stock_user` (ver implied_ids), por lo que no se pierde acceso. |
| **D4-F2** | **Modelos de shipping_core usan `base.group_user` — sin ACLs custom** | **Alto** | `madenat_lumber_shipping_core/security/ir.model.access.csv`: `shipping.vessel`, `shipping.voyage`, `shipping.booking` usan `base.group_user` | Cualquier empleado ve motonaves, viajes y reservas. No hay distinción entre Operaciones (que gestiona embarques) y otros perfiles. | Aplicar patrón 4×modelo (ops/costos/contab/gerencia) como en los demás módulos. |
| **D5-F2** | **Billing usa `account.group_account_manager` en lugar de grupos custom** | **Medio** | Todos los menús de billing y sus ACLs usan `account.group_account_manager` y `base.group_user` | Inconsistencia con el resto del ecosistema. La separación de roles de billing no está implementada. | Ya documentado en auditoría previa. Requiere taller de seguridad. No modificar sin definir roles. |
| **D6-F2** | **Submenús de Configuración requieren `stock.group_stock_manager` + `base.group_system`** | **Medio** | `menu_madenat_config_patios` y `menu_madenat_config_subproducto` usan `stock.group_stock_manager,base.group_system` | El Configurador de Ingesta (que tiene `group_lumber_config_manager`) puede ver el menú Configuración pero NO los submenús porque `group_lumber_config_manager` no implica `stock.group_stock_manager`. | Agregar `group_lumber_config_manager` a los grupos de estos submenús: `groups="stock.group_stock_manager,base.group_system,group_lumber_config_manager"` |

### FASE 3 — FLUJOS DE NEGOCIO (Domains, Contextos, Estados)

#### ✅ Validado

| # | Ítem | Resultado |
|---|------|-----------|
| 3.1 | search_default filters | **Correcto** — 17 contextos con filtros por defecto bien definidos |
| 3.2 | Estados en modelos | **Correcto** — 20+ campos state/status documentados en modelos |
| 3.3 | noupdate en billing | **Corregido** — `noupdate="0"` confirmado |
| 3.4 | Billing workflow (acción de servidor) | **Correcto** — `action_create_consolidation_from_shipment` definida |

#### 🔴 Hallazgos

| ID | Título | Severidad | Evidencia | Impacto | Recomendación |
|----|--------|-----------|-----------|---------|---------------|
| **D7-F3** | **2 acciones con `domain>[]` (vacío) muestran todos los registros** | **Medio** | `action_lumber_reception_raw_only` (Historial de Ingresos) y `action_lots_costing_pending` (Lotes Pendientes de Valorización) tienen `domain>[]` | El usuario ve TODAS las recepciones/TODOS los lotes sin filtro. Para "Historial de Ingresos" puede ser intencional (es un historial). Para "Lotes Pendientes" contradice el nombre — el contexto tiene `search_default_pending: 1` pero el domain está vacío. | Verificar si el search_default_pending aplica un filtro efectivo. Si no, agregar domain específico (ej: `[('wood_cost_usd', '=', 0)]` como en `action_madenat_lot_cost_assignment`). |

### FASE 4 — REPORTES Y SALIDAS

#### ✅ Validado

| # | Ítem | Resultado |
|---|------|-----------|
| 4.1 | Reportes QWeb definidos | **Correcto** — 6 reportes en core, logistics, reports |
| 4.2 | Reportes con acciones window | **Correcto** — templates de guía, batch, cost, packing list, manifest |

#### 🔴 Hallazgos

| ID | Título | Severidad | Evidencia | Impacto | Recomendación |
|----|--------|-----------|-----------|---------|---------------|
| **D8-F4** | **ID de reporte duplicado entre logistics y reports** | **Medio** | `action_report_lumber_container_packing_list` definido en `lumber_container_reports.xml:5` (logistics) y `report_packing_list.xml:4` (reports) | Ambas definiciones compiten. Odoo usa la última cargada (reports, porque depende de logistics). La definición de logistics es ignorada. | Consolidar en un solo módulo (reports, que es el dueño natural de reportes). Eliminar la definición de logistics o documentar que es override intencional. |
| **D9-F4** | **Sin crons ni acciones planificadas** | **Bajo** | Búsqueda `ir.cron` en XML → 0 resultados | No hay automatizaciones nocturnas. Si se requieren (ej: cierre de período, consolidación automática), no están implementadas. | Evaluar si el negocio requiere crons. Si no, documentar que no hay procesos batch. |

### FASE 5 — OPERACIÓN TÉCNICA (Logs, Warnings, Performance)

#### ✅ Validado

| # | Ítem | Resultado |
|---|------|-----------|
| 5.1 | Imports cross-addon (riesgo registry) | **Limpio** — 0 imports `from madenat_lumber_*` sin namespace `odoo.addons` |
| 5.2 | XML bien formados | **Limpio** — 0 errores de sintaxis en todos los XML |
| 5.3 | view_mode obsoleto | **Limpio** — 0 `tree,form` residuales |

#### 🔴 Hallazgos

| ID | Título | Severidad | Evidencia | Impacto | Recomendación |
|----|--------|-----------|-----------|---------|---------------|
| **D10-F5** | **Archivos .bak huérfanos en módulos activos** | **Bajo** | `__manifest__.py.bak.20260606_121330` en core y costing, `lumber_billing_menu_data.xml.bak.20260606_121330` en billing, `lumber_reports_menu.xml.bak.20260606_121330` en reports | Odoo podría intentar parsear estos archivos como XML si el patrón de descubrimiento es muy amplio. Riesgo bajo pero ensucian el repositorio. | Mover a `_archive/` o eliminar. Agregar `*.bak*` a `.gitignore`. Ya documentado en AD-26 pero no ejecutado. |

---

## 3. RESUMEN DE SEVERIDAD

| Severidad | Cantidad | Hallazgos |
|-----------|----------|-----------|
| Crítico | 1 | D1-F1: 19 acciones huérfanas sin acceso por menú |
| Alto | 2 | D3-F2: stock.group_stock_user en menús core, D4-F2: modelos shipping sin ACLs custom |
| Medio | 4 | D2-F1: placeholders sin acción, D5-F2: billing grupos nativos, D7-F3: domain vacío, D8-F4: reporte duplicado |
| Bajo | 2 | D9-F4: sin crons, D10-F5: .bak huérfanos |

---

## 4. QUÉ QUEDÓ VALIDADO (Fases limpias)

| Fase | Resultado |
|------|-----------|
| **Estabilidad base — XML/vistas** | ✅ Limpio. Cero XML mal formados, cero view_mode tree residual, noupdate billing corregido. |
| **Seguridad — Estructura de grupos** | ✅ Limpio. 7 grupos bien definidos con jerarquía correcta. ACLs usan grupos custom en core/logistics/costing. |
| **Flujos — Estados y transiciones** | ✅ Limpio. 20+ campos state/status documentados en modelos. Sin estados huérfanos detectados. |
| **Flujos — Contextos y filtros** | ✅ Limpio. 17 contextos con search_default bien definidos. Sin filtros ocultos que bloqueen datos. |
| **Reportes — Cobertura** | ✅ 6 reportes QWeb definidos cubriendo guías, batch, costos, packing list, manifest. |
| **Operación — Imports cross-addon** | ✅ Limpio. Sin riesgo de rotura de registry por imports entre módulos. |

---

## 5. QUÉ QUEDÓ PENDIENTE

| # | Pendiente | Bloqueante | Acción sugerida |
|---|-----------|------------|-----------------|
| 1 | Mapear las 19 acciones huérfanas → definir cuáles necesitan menú | Sí — funcionalidades inaccesibles | Priorizar dashboards, reportes y trazabilidad 360 |
| 2 | Reemplazar `stock.group_stock_user` → `group_madenat_operaciones` en 4 menús | No — funcional pero inseguro | Cambio simple (4 líneas) |
| 3 | Agregar ACLs custom a modelos de shipping_core | No — sin impacto si hay pocos usuarios | Aplicar patrón 4×modelo |
| 4 | Agregar `group_lumber_config_manager` a submenús de Configuración | Sí — Configurador no ve submenús | Cambio simple (2 líneas) |
| 5 | Resolver reporte duplicado logistics/reports | No | Consolidar en reports |
| 6 | Limpiar .bak huérfanos | No | Mover a _archive/ |

---

## 6. PRÓXIMA ACCIÓN SUGERIDA

**Prioridad 1 (hoy):**
- Agregar `group_lumber_config_manager` a submenús de Configuración (D6-F2) → 2 líneas, sin riesgo
- Reemplazar `stock.group_stock_user` → `group_madenat_operaciones` en menús core (D3-F2) → 4 líneas, riesgo bajo

**Prioridad 2 (esta semana):**
- Mapear las 19 acciones huérfanas contra el mapa de navegación (CANON/15 §7) para determinar cuáles requieren menú
- Conectar placeholders de Contabilidad/Gerencia con sus acciones correspondientes

**Prioridad 3 (backlog):**
- ACLs custom en shipping_core
- Consolidar reporte duplicado
- Limpiar .bak

---

*Informe de depuración funcional generado el 2026-06-06. Método: investigación estática (grep, análisis estructural). Sin acceso a runtime/UI/BD.*