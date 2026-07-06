# PRE-FASE A — Auditoría de Módulos y Commits Pendientes

**Proyecto**: MADENAT Lumber — Odoo 18 CE  
**Fecha**: 2026-06-04  
**Estado**: COMPLETO — Paso 1 (commit) + Pasos 2-5 (auditoría, mapa de costeo, documentación, entregable)

---

# PASO 1 — COMMIT DE CAMBIOS PENDIENTES

## Estado previo

```
3 archivos modificados sin commit:
  - madenat_lumber_core/CHANGELOG.md                     (+21 líneas)
  - madenat_lumber_core/models/madenat_guia_processing.py (+4/-4 líneas)
  - madenat_lumber_logistics/views/lumber_container_views.xml (+59/-36 líneas)

1 archivo untracked:
  - madenat_lumber_docs/ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md
```

## Commit ejecutado

```
5e41e22 feat(core, logistics): HOTFIX v4 — tolera company_id=NULL en búsqueda de lote + mejoras UI contenedor

- madenat_guia_processing.py: _create_or_get_lot() ahora busca con
  company_id IN [env.company.id, False] en vez de = env.company.id,
  ordenando por company_id DESC. Repara lotes huérfanos con
  company_id=NULL que no eran encontrados, evitando colisiones UNIQUE.

- CHANGELOG.md: documenta HOTFIX v4 con evidencia de BD

- lumber_container_views.xml: agrega columnas volumen_m3, guia_number,
  location_id; reorganiza orden de columnas; optional=show

Refs: HOTFIX-v4, AD-24
```

**Working tree post-commit**: limpio (solo `ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md` untracked, es documentación de análisis).

---

# PASO 2 — AUDITORÍA DE LOS 11 MÓDULOS

## Tabla resumen

| # | Módulo | Rol | Modelos | Vistas | Wizards | Tests | Doc | Costeo |
|---|--------|-----|---------|--------|---------|-------|-----|--------|
| 1 | `madenat_lumber_core` | Núcleo: recepción, staging, lotes, guías, cálculos | 19 archivos, ~18K líneas | ✅ 12+ archivos | ✅ 3 wizards | ✅ `test_guia_processing.py` (nuevo) | ✅ CHANGELOG, README | ✅ Float monetario |
| 2 | `madenat_lumber_costing` | Costeo multi-nivel, landed costs | 3 archivos (315 + 196 + integración) | ✅ 2 vistas | ✅ 1 wizard | ❌ Sin tests | ❌ Sin README | ✅ **Monetary parcial** |
| 3 | `madenat_lumber_billing` | Facturación y consolidación | 3 archivos | ✅ 2 vistas | ✅ 1 wizard | ✅ `test_billing_consolidation.py` | ✅ README | ✅ **Monetary** |
| 4 | `madenat_lumber_logistics` | Contenedores, logística, embarques | 5+ archivos | ✅ 4+ vistas | ✅ 2 wizards | ❌ Sin tests | ✅ CHANGELOG, README | ✅ **Monetary** |
| 5 | `madenat_lumber_purchasing` | Compras extendidas, intake | 3 archivos | ✅ vistas | ❌ | ❌ Sin tests | ⚠️ CHANGELOG_FIX4 | ❌ No participa |
| 6 | `madenat_lumber_shipping_core` | Embarques y booking base | 2 archivos | ✅ vistas | ❌ | ❌ Sin tests | ⚠️ docs/ | ❌ No participa |
| 7 | `madenat_lumber_reports` | Meta-módulo: menús y reportes | 1 archivo | ✅ menús + reportes | ❌ | ❌ Sin tests | ❌ Sin README | ❌ No participa |
| 8 | `madenat_lumber_reception_improvements` | Mejoras de recepción | 2 archivos | ✅ vistas | ❌ | ❌ Sin tests | ✅ README | ❌ No participa |
| 9 | `madenat_toll_processing` | Maquila / procesamiento externo | 3 archivos | ✅ vistas | ✅ wizards | ❌ Sin tests | ✅ README | ✅ Monetary en `process_cost_per_m3` |
| 10 | `madenat_vendor_payment` | Pagos a proveedores | 3 archivos | ✅ vistas | ✅ wizards | ❌ Sin tests | ✅ README | ⚠️ Floats |
| 11 | `madenat_lumber_docs` | Documentación (no es módulo Odoo) | — | — | — | — | ✅ CANON + WIKI + auditorías | — |

## Detalle por módulo

### 1. `madenat_lumber_core` — NÚCLEO
- **Archivos modelo**: 19 archivos Python (~18K líneas total)
  - `stock_lot.py` (1392 líneas) — Lotes extendidos
  - `madenat_guia_processing.py` (3334 líneas) — Guías de procesamiento
  - `lumber_reception.py` (2573 líneas) — Recepción de madera bruta
  - `stock_lot_cost_line.py` (84 líneas) — Línea de costo canónica
  - `stock_move.py`, `stock_picking.py` — Extensiones de stock
  - `utils_uom.py`, `width_mapping.py` — Utilidades
  - `madenat_ingestion_config.py`, `lumber_export_formula.py`, `lumber_ingestion_format.py` — Fases 2-3
  - `madenat_subproducto.py`, `madenat_audit_log.py`, `res_config_settings.py` — Configuración
  - `reception_parser.py`, `reception_service.py`, `reception_workflow.py` — Componentes desacoplados
  - `mixin_lumber_ingest.py`, `ingestion_gate.py`, `core_utils.py` — Mixins/gates
- **Participa en costeo**: ✅ Define `stock.lot.wood_cost_usd`, `stock.lot.purchase_cost_usd`, `stock.lot.total_cost_usd`, `stock.lot.cost_line_ids`
- **Estado monetario**: ❌ Todos `fields.Float` (14 campos monetarios)
- **Tests**: ✅ `tests/test_guia_processing.py` (nuevo) + `tests/test_lumber_reception.py` (2572 líneas)
- **Documentación**: ✅ `CHANGELOG.md`, `README.md`, `ROADMAP.md` (en `models/` — mover a CANON)

### 2. `madenat_lumber_costing` — COSTEO
- **Archivos modelo**: 3 archivos (~700 líneas)
  - `lumber_cost_distribution.py` (315 líneas) — Expediente de liquidación con 6 métodos de prorrateo
  - `stock_lot_costing.py` (196 líneas) — Extensión de costing en stock.lot
  - `lumber_shipment_costing.py` (logistics) — Costeo de embarque
- **Participa en costeo**: ✅ Módulo principal de distribución de landed costs
- **Estado monetario**: ⚠️ `amount_original`, `amount_usd`, `exchange_rate` siguen siendo Float; `additional_cost` ya es Monetary
- **Tests**: ❌ Sin tests
- **Documentación**: ❌ Sin `README.md` ni `CHANGELOG.md`
- **Hueco**: `costing_menus.xml` comentado en `__manifest__.py` sin documentar razón

### 3. `madenat_lumber_billing` — FACTURACIÓN
- **Archivos modelo**: 3 archivos — consolidación, líneas, common
- **Participa en costeo**: ✅ Lee `wood_cost_usd` de lotes, calcula variaciones
- **Estado monetario**: ✅ **Ya migrado a Monetary** (`wood_cost_usd`, `real_wood_cost_usd`, etc.)
- **Tests**: ✅ `test_billing_consolidation.py`
- **Documentación**: ✅ `README.md`

### 4. `madenat_lumber_logistics` — LOGÍSTICA
- **Archivos modelo**: `lumber_export_shipment.py`, `lumber_container.py`, `lumber_shipment_line.py`, `lumber_shipment_costing.py`
- **Participa en costeo**: ✅ `lumber_shipment_costing.py` define distribución de costos de embarque
- **Estado monetario**: ✅ **Ya migrado a Monetary** (`total_shipment_costs_usd`, `total_cost_per_m3`)
- **Tests**: ❌ Sin tests
- **Documentación**: ✅ `CHANGELOG.md`, `README.md`
- **Nota**: `_deprecated_action_distribute_costs()` escribe directo a `logistic_cost_usd` sin pasar por `cost_line_ids`

### 5. `madenat_lumber_purchasing` — COMPRAS
- **Rol**: Extensión de compras con intake de datos
- **Participa en costeo**: ❌ No define modelos de costo propios
- **Tests**: ❌ Sin tests
- **Documentación**: ⚠️ Solo `CHANGELOG_FIX4_20241204.md`

### 6. `madenat_lumber_shipping_core` — EMBARQUES
- **Rol**: Base de booking y embarques
- **Participa en costeo**: ❌ No define costos
- **Tests**: ❌ Sin tests
- **Documentación**: ⚠️ Directory `docs/` sin contenido canónico

### 7. `madenat_lumber_reports` — REPORTES
- **Rol**: Meta-módulo que remapea menús y agrupa reportes
- **Participa en costeo**: ❌ No define modelos
- **Tests**: ❌ Sin tests
- **Documentación**: ❌ Sin `README.md`

### 8. `madenat_lumber_reception_improvements` — MEJORAS RECEPCIÓN
- **Rol**: Extensiones de UI y flujo para recepción
- **Participa en costeo**: ❌ No define costos
- **Tests**: ❌ Sin tests
- **Documentación**: ✅ `README.md`

### 9. `madenat_toll_processing` — MAQUILA
- **Rol**: Procesamiento externo / toll processing
- **Participa en costeo**: ✅ Define `process_cost_per_m3` como **Monetary**
- **Tests**: ❌ Sin tests
- **Documentación**: ✅ `README.md`

### 10. `madenat_vendor_payment` — PAGOS
- **Rol**: Gestión de pagos a proveedores
- **Participa en costeo**: ⚠️ Usa `fields.Float` para montos
- **Tests**: ❌ Sin tests
- **Documentación**: ✅ `README.md`

### 11. `madenat_lumber_docs` — DOCUMENTACIÓN
- **Rol**: Repositorio de documentación (NO es módulo Odoo — sin `__manifest__.py`)
- **Contenido**: `CANON/` (9 archivos), `WIKI/` (7+ archivos), auditorías, inventarios, análisis
- **Documentación**: ✅ CANON completo, WIKI detallada, 2 auditorías recientes

---

# PASO 3 — MAPA DE COSTEO Y CONTABILIDAD

## Módulos que participan en costeo

| Módulo | Rol en costeo | Campos monetarios | Estado Float/Monetary |
|--------|--------------|-------------------|----------------------|
| `madenat_lumber_core` | Define modelo canónico `stock.lot.cost.line` + campos base en `stock.lot` | 14 campos Float (wood_cost, purchase_cost, purchase_amount, etc.) | ❌ **TODO Float** — requiere migración |
| `madenat_lumber_costing` | Motor de distribución (`lumber.cost.distribution`) | 5 campos Float (amount_original, amount_usd, exchange_rate) | ⚠️ **Parcial** — Monetary en `additional_cost` pero no en el resto |
| `madenat_lumber_billing` | Consolidación de facturación, lee costos de lotes | `wood_cost_usd`, `real_wood_cost_usd`, `variance_wood_cost_usd` | ✅ **Ya migrado a Monetary** |
| `madenat_lumber_logistics` | Costeo de embarque por booking | `total_shipment_costs_usd`, `total_cost_per_m3` | ✅ **Ya migrado a Monetary** |
| `madenat_toll_processing` | Costo de proceso por m³ | `process_cost_per_m3` | ✅ **Monetary** |
| `madenat_vendor_payment` | Montos de pago | `amount_total`, `amount_paid` | ❌ **Float** |

## Módulos que interactúan con contabilidad Odoo estándar

| Componente | billing | costing | logistics | core | toll |
|-----------|---------|---------|-----------|------|------|
| `account.move` | ✅ (wizard invoice) | ❌ | ❌ | ❌ | ❌ |
| `stock.landed.cost` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `stock.valuation.layer` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `account.journal` | ⚠️ parcial | ❌ | ❌ | ❌ | ❌ |
| `account.account` | ⚠️ parcial | ❌ | ❌ | ❌ | ❌ |

**Conclusión**: Solo **billing** tiene integración real con `account.move`. Ningún módulo genera `stock.landed.cost` ni `stock.valuation.layer`. El costeo existe a nivel de `stock.lot` pero no aterriza en contabilidad estándar de Odoo.

## Campos Float monetarios pendientes de migración

### En `stock.lot` (madenat_lumber_core)
1. `purchase_price_usd_per_m3` — Float
2. `purchase_exchange_rate` — Float
3. `purchase_amount_usd` — Float (compute)
4. `purchase_amount_clp` — Float (compute)
5. `wood_cost_usd` — Float
6. `purchase_cost_usd` — Float (código muerto, siempre 0)
7. `lot_exchange_rate` — Float
8. `total_cost_usd` — Float (compute, no store)
9. `cost_per_m3_usd` — Float (compute)
10. `cost_per_mbf_usd` — Float (compute)
11. `sale_price_usd_per_mbf` — Float
12. `sale_amount_usd` — Float (compute)
13. `margin_usd` — Float (compute)
14. `margin_percent` — Float (compute)

### En `lumber_reception` (madenat_lumber_core)
15. `exchange_rate` — Float
16. `total_amount_clp` — Float
17. `total_amount_usd` — Float (compute)
18. `price_per_m3_usd` — Float (compute)
19. `average_price_m3` — Float (compute)
20. `price_per_mbf_usd` — Float (compute)

### En `lumber.cost.distribution` (madenat_lumber_costing)
21. `amount_original` — Float
22. `exchange_rate` — Float
23. `amount_usd` — Float (compute)
24. `amount_total` — Float

### En `stock.lot.cost.line` (madenat_lumber_core)
25. `amount_usd` — Float (sin `currency_id`)

---

# PASO 4 — MAPA DE DOCUMENTACIÓN

| Módulo | README | CHANGELOG | CANON | WIKI | Auditoría | Estado doc |
|--------|--------|-----------|-------|------|-----------|------------|
| `madenat_lumber_core` | ✅ | ✅ | ✅ | ✅ | ✅ | **COMPLETO** |
| `madenat_lumber_costing` | ❌ | ❌ | ❌ | ❌ | ⚠️ parcial | **DEUDA** — sin doc propia |
| `madenat_lumber_billing` | ✅ | ❌ | ❌ | ❌ | ⚠️ parcial | **PARCIAL** |
| `madenat_lumber_logistics` | ✅ | ✅ | ❌ | ✅ `madenat_lumber_logistics.md` | ✅ | **COMPLETO** |
| `madenat_lumber_purchasing` | ❌ | ⚠️ solo fix4 | ❌ | ❌ | ❌ | **DEUDA** |
| `madenat_lumber_shipping_core` | ❌ | ❌ | ❌ | ❌ | ❌ | **DEUDA** |
| `madenat_lumber_reports` | ❌ | ❌ | ❌ | ❌ | ❌ | **DEUDA** |
| `madenat_lumber_reception_improvements` | ✅ | ❌ | ❌ | ❌ | ❌ | **PARCIAL** |
| `madenat_toll_processing` | ✅ | ❌ | ❌ | ❌ | ❌ | **PARCIAL** |
| `madenat_vendor_payment` | ✅ | ❌ | ❌ | ❌ | ❌ | **PARCIAL** |
| `madenat_lumber_docs` | — | — | ✅ | ✅ | ✅ | **COMPLETO** |

**Módulos con deuda documental**: `costing`, `purchasing`, `shipping_core`, `reports` (4 de 10 módulos Odoo sin documentación propia).

---

# PASO 5 — ENTREGABLE: RESUMEN EJECUTIVO

## 1. Commits pendientes resueltos

| Estado | Detalle |
|--------|---------|
| ✅ Commiteado | `HOTFIX v4` — tolera `company_id=NULL` en búsqueda de lotes + mejoras UI contenedor |
| 📄 Untracked | `ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md` — documento de análisis (no es código) |

## 2. Estado de módulos

| Métrica | Valor |
|---------|-------|
| Módulos Odoo activos | 10 |
| Módulos con tests | 2 (core, billing) |
| Módulos sin tests | 8 |
| Módulos que participan en costeo | 4 (core, costing, billing, logistics) + 1 (toll) |
| Módulos con Monetary | 3 (billing, logistics, toll) |
| Módulos con Float monetario | 2 (core, costing) + 1 (vendor_payment) |
| Módulos con documentación completa | 3 (core, logistics, toll) |
| Módulos con deuda documental | 4 (costing, purchasing, shipping_core, reports) |
| Módulos con integración contable (`account.move`) | 1 (billing) |
| Módulos con `stock.landed.cost` | 0 |

## 3. Qué módulos revisar primero en Fase A

1. **`madenat_lumber_core/models/stock_lot.py`** — Migrar 14 campos Float a Monetary (prioridad 0)
2. **`madenat_lumber_core/models/stock_lot_cost_line.py`** — Agregar `currency_id` + migrar `amount_usd` a Monetary + agregar `account_id` (prioridad 0)
3. **`madenat_lumber_costing/models/lumber_cost_distribution.py`** — Migrar 4 campos Float a Monetary (prioridad 1)
4. **`madenat_lumber_costing/models/stock_lot_costing.py`** — Verificar `_compute_total_cost_usd` override (prioridad 1)
5. **`madenat_lumber_logistics/models/lumber_shipment_costing.py`** — Ya usa Monetary ✅, pero `_deprecated_action_distribute_costs` bypassea `cost_line_ids` (prioridad 2)

## 4. Recomendación final

La Fase A puede arrancar con contexto completo. La base contable más urgente es:
- **Core** (`stock_lot` + `stock_lot_cost_line`): migrar Float → Monetary, unificar costo base de madera
- **Costing** (`lumber_cost_distribution`): migrar Float → Monetary, preparar integración con `stock.landed.cost`
- **Billing y Logistics** ya están migrados a Monetary — no necesitan cambios en esta fase

---

*Informe PRE-FASE A generado el 2026-06-04.*  
*Basado en: git log, git diff, conteo de líneas, análisis de 19 modelos Python, 12+ vistas XML.*