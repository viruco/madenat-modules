# AUDITORÍA PROFUNDA — `lumber_reception`

**Fecha:** 2026-07-01
**Alcance:** Análisis técnico y documental sin modificación de código
**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Archivo principal:** `custom_addons/madenat_lumber_core/models/lumber_reception.py`

---

# 1. Inventario técnico

## 1.1 Archivos implicados (eje central + dependencias directas)

| Archivo | Líneas | Rol |
|---|---|---|
| `models/lumber_reception.py` | **3,118** | Modelo principal: 2 clases, 70 métodos, 97 campos |
| `models/reception_parser.py` | 722 | AbstractModel — Parseo de Excel y PDFs (guía despacho + OC) |
| `models/reception_service.py` | 218 | Servicio desacoplado — creación de lotes, stock picking, cleanup |
| `models/reception_workflow.py` | ~150 | Workflow desacoplado — pipeline de ingesta Gate 0→3 (referenciado, no auditado en detalle) |
| `models/mixin_lumber_ingest.py` | 347 | Mixin compartido con `madenat.guia.processing` (productos, volúmenes) |
| `models/ingestion_gate.py` | 257 | Gates 0+1+2+3 de validación de ingesta |
| `models/validation_checklist_mixin.py` | 453 | Mixin de checklist de validación (usa `reception_id`) |
| `models/stock_lot.py` | ~600 | `reception_id`, `reception_type='direct'` |
| `models/stock_picking.py` | ~100 | Campo `reception_id` en picking |
| `models/madenat_audit_log.py` | ~100 | `reception_id → lumber.reception` |
| `views/lumber_reception_views.xml` | 787 | Vista form + list |
| `views/lumber_reception_kanban_views.xml` | ~200 | Vista kanban |
| `wizard/lumber_reception_mass_update.py` | 416 | Wizard de asignación masiva de nominales y subproducto |
| `wizard/lumber_reception_mass_update_views.xml` | ~80 | Vista del wizard |
| `tests/test_lumber_reception.py` | 425 | 14 tests (T01–T14) |
| `tests/test_length_uom_and_subproducto.py` | 127 | Tests de naming length y subproducto |
| `tests/test_duplicate_validation.py` | ~200 | Tests de validación anti-duplicado |
| `madenat_lumber_purchasing/models/lumber_reception.py` | ~350 | `_inherit` que extiende OC matching con compras |
| `madenat_lumber_purchasing/models/purchase_order.py` | ~400 | Campos `lumber_reception_ids`, `action_view_receptions()` |
| `madenat_toll_processing/models/lumber_reception.py` | ~50 | `_inherit` para toll processing |
| `madenat_lumber_reports/models/lumber_reception_reports.py` | ~100 | `_inherit` de `lumber.reception.line` para reportes |
| `madenat_lumber_reports/models/report_helpers.py` | ~300 | Helpers de reporte que leen `lumber.reception.line` |
| `madenat_lumber_docs/CANON/12_FLUJOS_INGESTA.md` | — | Documenta flujo 2: recepción directa |
| `madenat_lumber_docs/CANON/00_ARQUITECTURA.md` | — | Sección 4.2 describe `lumber.reception` |

**Total combinado:** ~9,000 líneas distribuidas en 20+ archivos en 5 módulos.

## 1.2 Métricas del archivo principal (`lumber_reception.py`)

| Métrica | Valor |
|---|---|
| Líneas totales | **3,118** |
| Modelos en el archivo | **2** (`LumberReceptionLine` L48–L922, `LumberReception` L924–L3118) |
| Métodos top-level | **70** |
| Métodos `action_*` | **9** (6 botones UI + 3 helpers) |
| Campos definidos | **97** (40 línea staging + 57 cabecera) |
| Llamadas `.write()` | **25** |
| Llamadas `.search()` | **13** |
| Llamadas `.create()` | **15** |
| Llamadas `.unlink()` | **13** |
| Método más largo | `action_reset_to_draft` (~163 líneas, L1406–L1568) |
| Segundo más largo | `_find_or_create_po_intelligent` (~153 líneas, L2278–L2430) |
| Tercero más largo | `create_po_from_oc_data` (~149 líneas, L2433–L2581) |
| Cuarto más largo | `action_confirm_reception` (~138 líneas, L2754–L2891) |
| Quinto más largo | `_compute_reception_summary` (~122 líneas, L1583–L1704) |
| Densidad `action_*` | 12.9% de los métodos son acciones de UI |

## 1.3 Modelos en el archivo

```
L48–L922:   LumberReceptionLine  (models.Model)
              _inherit: madenat.lumber.ingest.line.mixin
              ~40 campos, ~23 métodos

L924–L3118: LumberReception     (models.Model)
              _inherit: mail.thread, mail.activity.mixin, madenat.lumber.ingest.mixin
              ~57 campos, ~47 métodos
```

## 1.4 Dependencias principales

**Internas (mismo módulo):**
```
reception_parser.py (MadenatReceptionParser)     — AbstractModel, parseo PDF/Excel
reception_service.py (LumberReceptionService)    — Clase Python pura, creación lotes/picking
reception_workflow.py (LumberReceptionWorkflow)  — Pipeline Gate 0→3
mixin_lumber_ingest.py                           — find_or_create_lumber_product
ingestion_gate.py                                — Gates 0,1,2,3
validation_checklist_mixin.py                    — Checklist validación
width_mapping.py (WidthMappingTable)             — Tabla de anchos rough→S2S
```

**Externas (módulos cruzados):**
```
stock.lot              — reception_id FK
stock.picking          — reception_id FK
stock.move / move.line — creación y limpieza
purchase.order         — purchase_id FK, lumber_reception_ids O2M
madenat.guia.processing — origin_processing_id FK
madenat.audit.log      — reception_id FK
madenat_lumber_purchasing — _inherit de lumber_reception (OC matching extendido)
madenat_lumber_reports — _inherit de lumber.reception.line (reportes)
madenat_toll_processing — _inherit de lumber_reception (toll processing)
```

---

# 2. Flujo real del módulo (Gate por Gate)

## 2.1 Diagrama de estados

```
┌────────────────────────────────────────────────────────────────────────────┐
│                 CICLO DE VIDA DE UNA RECEPCIÓN (GUÍA BRUTA)                  │
│                                                                             │
│  ┌─────────┐   action_process_documents()   ┌─────────────┐                 │
│  │  draft  │ ─────────────────────────────→ │ processing  │                 │
│  │         │    (workflow Gate 0→1:         │             │                 │
│  │         │     parse PDF+Excel,           │             │                 │
│  │         │     detect supplier+OC,        │             │                 │
│  └────┬────┘     fill staging)              └──────┬──────┘                 │
│       │                                            │                        │
│       │ action_cancel()                            │ action_verify_data()   │
│       │ (desde draft/processing)                   │ o continua automatic.  │
│       ▼                                            ▼                        │
│  ┌──────────┐                            ┌───────────┐                      │
│  │  cancel  │                            │ verified  │                      │
│  │          │                            │           │                      │
│  └──────────┘                            └─────┬─────┘                      │
│       ▲                                        │                             │
│       │                                        │ action_confirm_reception() │
│       │                                        │ (Gate 2→3:                 │
│       │                                        │  create lots,              │
│       │                                        │  create picking,           │
│       │                                        │  validate stock)           │
│       │                                        ▼                             │
│       │                                  ┌──────────┐                       │
│       │                                  │   done   │                       │
│       │                                  │          │                       │
│       │                                  └────┬─────┘                       │
│       │                                       │                              │
│       │                                       │ action_reset_to_draft()     │
│       │                                       │ (limpia quants → lotes →    │
│       │                                       │  pickings → staging)        │
│       │                                       ▼                              │
│       │                                  ┌─────────┐                        │
│       └──────────────────────────────────│  draft  │ (re-ciclo)             │
│                                          └─────────┘                        │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Paso a paso operativo por Gate

### Gate 0 — Ingesta Documental (draft → processing)
1. **Usuario crea registro**, sube PDF Guía + Excel Packing (+ opcional PDF OC)
2. **Botón "Procesar Documentos"** → `action_process_documents()` (L2688)
   - Delega al workflow `LumberReceptionWorkflow.run_ingestion_pipeline(self)`
   - El workflow orquesta: parseo → staging → OC matching

### Gate 1 — Parseo y Staging
3. **Workflow invoca parser** (`reception_parser.py`):
   - **3a. `_check_guide_duplicate()`** — Bloquea si la guía ya existe en `lumber.reception` o `madenat.guia.processing`
   - **3b. `parse_excel()`** — Lee Excel con heurística de columnas (scoring semántico), limpia datos, convierte unidades
   - **3c. `parse_dispatch_guide()`** — Lee PDF guía: extrae RUT, nombre, OC, número guía, TC, volumen, fecha
   - **3d. `parse_purchase_order()`** — Lee PDF OC (si existe): volumen, precio, calidad
4. **Workflow llena staging** → `_fill_staging_table()` (L2058):
   - Guardia anti-duplicado: bloquea si ya hay lotes reales
   - Limpia staging previo
   - Crea `lumber.reception.line` con dimensiones físicas, nominales, visuales
   - Busca/crea productos vía `madenat.lumber.ingest.mixin`

### Gate 2 — Matching de OC (processing → verified implícito)
5. **Workflow ejecuta OC matching** → `_find_or_create_po_intelligent()` (L2278):
   - Identifica proveedor por RUT (crea/actualiza si es necesario)
   - Busca purchase.order por clave normalizada
   - Si hay match: vincula (`purchase_id`, `oc_match_status='single_match'`)
   - Si no hay match: activa modo manual (`manual_po_name`, `oc_match_status='not_found'`)
   - **PATCH 2026-06-18**: Ya NO crea OC automáticamente (antes sí, con valores hardcode)

### Gate 3 — Confirmación y Stock (verified → done)
6. **Botón "Validar Recepción"** → `action_confirm_reception()` (L2754):
   - **6a. Validaciones**: estado `verified`, staging no vacío, sin lotes previos, nominales completos (Gate GB-1)
   - **6b. Gate 2 formal** (`ingestion_gate.Gate2CommercialAnalysis`): validación comercial final
   - **6c. Gate 3** (`ingestion_gate.Gate3PreCommit`): snapshot criptográfico (audit_snapshot + audit_hash)
   - **6d. Auto-reparación**: asegura `is_storable=True`, `tracking='lot'` en todos los productos
   - **6e. Creación de lotes**: `_create_lots_from_packing()` → delega a `LumberReceptionService.create_lots_from_staging()`
   - **6f. Creación de picking**: `LumberReceptionService.create_stock_picking()`
   - **6g. Validación de stock**: confirma, asigna, valida picking
   - **6h. Estado final**: `done`, lotes marcados `technical_validation='approved'`

### Gate 4 — Reversa/Reset (done → draft)
7. **Botón "Resetear a Borrador"** → `action_reset_to_draft()` (L1406):
   - Escudo: bloquea si lotes en contenedores o consolidados
   - En savepoint: elimina quants → desvincula/elimina pickings → elimina lotes → elimina staging
   - Limpia cabecera (volúmenes en cero, picking_id=False)
   - Requiere grupo `stock.group_stock_manager`

---

# 3. Responsabilidades mezcladas

## 3.1 Clasificación cuantificada

| Categoría | Métodos representativos | Líneas aprox. | % del modelo |
|---|---|---|---|
| **1. Negocio maderero** (dimensiones, fracciones, volúmenes, blanks/S2S) | `_compute_visual_defaults`, `_compute_export_values`, `_compute_volume_purchase`, `_get_trader_width_text`, `_apply_thickness_visual`, `_compute_volume_physical_real`, `_compute_vol_physical_strict`, `_parse_smart_dimension`, `_get_fraction_text`, `_compute_vol_purchase_m3`, `_compute_lengthm` | ~650 | 21% |
| **2. Inventario / Stock** (creación lotes, pickings, validación) | `_create_lots_from_packing`, `_create_stock_picking`, `action_confirm_reception` | ~300 | 10% |
| **3. Parseo / Ingesta** (lectura archivos) | `action_verify_data`, `action_process_documents`, `_fill_staging_table` | ~250 | 8% |
| **4. UI / Acciones usuario** (botones, notificaciones) | `action_process_documents`, `action_verify_data`, `action_confirm_reception`, `action_reset_to_draft`, `action_cancel`, `action_view_audit_logs`, `action_suggest_nominal_defaults` | ~200 | 6% |
| **5. OC / Compras / Matching** | `_find_or_create_po_intelligent`, `create_po_from_oc_data`, `_match_reception_purchase_order`, `_normalize_oc_key`, `_canonize_oc_display`, `_compute_oc_reference_norm`, `_update_po_reception_stats`, `_get_current_exchange_rate` | ~500 | 16% |
| **6. Costos / Finanzas** | `_assign_costs_to_lots`, `_compute_line_cost`, `_compute_average_price_clp`, `_compute_usd_amount`, `_compute_unit_prices` | ~200 | 6% |
| **7. Auditoría / Trazabilidad** | `_compute_reception_summary`, `_compute_totals`, `_compute_gate_duration_hours`, `_compute_nominal_status`, `_compute_omitted_count`, `_compute_po_missing_alert`, `_add_log`, `_log_excel_omissions` | ~350 | 11% |
| **8. Reversa / Cancelación / Cleanup** | `action_reset_to_draft`, `action_cancel`, `unlink`, `_cleanup_orphan_moves`, `validate_product_configuration` | ~300 | 10% |
| **9. Validación / Constraints** | `_check_required_documents`, `_validate_product_uom_for_lumber` | ~50 | 2% |

**Total modelo:** ~3,118 líneas (el resto son líneas de staging L48–L922)

## 3.2 Desacoples ya realizados — evaluación de efectividad

La documentación CANON indica que se realizaron desacoples de parser, workflow y service. Auditoría confirma:

| Desacople documentado | ¿Real? | ¿Efectivo? | Evidencia |
|---|---|---|---|
| **Parser → `reception_parser.py`** | ✅ Sí | ✅ Alto | 722 líneas extraídas. `parse_excel()`, `parse_dispatch_guide()`, `parse_purchase_order()`, `_check_guide_duplicate()` están en parser, no en el modelo |
| **Workflow → `reception_workflow.py`** | ✅ Sí | ✅ Medio | `action_process_documents()` solo tiene 10 líneas — delega al workflow. Pero el workflow no está en el scope auditado |
| **Service → `reception_service.py`** | ✅ Sí | ✅ Alto | 218 líneas. `create_lots_from_staging()`, `create_stock_picking()`, `cleanup_orphan_moves()` residen en el servicio |
| **Mixin → `mixin_lumber_ingest.py`** | ✅ Sí | ✅ Alto | 347 líneas. `find_or_create_lumber_product()`, `validate_product_lumber_config()`, `calculate_normalized_volumes()` |
| **Gates → `ingestion_gate.py`** | ✅ Sí | ✅ Medio | Gates 0,1,2,3 extraídos. Pero Gate 3 (snapshot) aún se invoca inline en `action_confirm_reception()` |
| **Width Map → `width_mapping.py`** | ✅ Sí | ✅ Alto | `WidthMappingTable` separado con su propia lógica de lookup |

**Conclusión sobre desacoples:** Los desacoples SON reales y efectivos. Sin ellos, el archivo principal tendría ~5,000+ líneas. El problema es que lo que quedó (3,118 líneas) sigue siendo un monolito parcial porque:

1. **`LumberReceptionLine` nunca se separó a archivo propio** (924 líneas de staging conviven con el modelo principal)
2. **OC/compras sigue 100% inline** (500 líneas, 16% del modelo): `_find_or_create_po_intelligent`, `create_po_from_oc_data`, `_match_reception_purchase_order`, `_update_po_reception_stats`
3. **Costos sigue inline** (200 líneas): `_assign_costs_to_lots`, computes financieros
4. **Reversa compleja sigue inline** (300 líneas): `action_reset_to_draft` con lógica de quants→lotes→pickings
5. **Resumen HTML inline** (122 líneas): `_compute_reception_summary` genera HTML dinámico con lógica de negocio de agrupación

---

# 4. Riesgos de mantenibilidad

## 4.1 Qué vuelve difícil modificarlo

| Factor | Evidencia | Severidad |
|---|---|---|
| **Dos modelos en un archivo** | `LumberReceptionLine` (876 líneas) + `LumberReception` (2,194 líneas) en el mismo archivo. Modificar la línea implica navegar 900 líneas antes de llegar al modelo principal | ALTA |
| **OC/compras completamente mezclada** | `_find_or_create_po_intelligent` (153 líneas) hace: búsqueda RUT, limpieza nombre, creación partner, búsqueda OC, cálculo de saldo, vinculación, fallback manual. Todo en un solo método | ALTA |
| **Reversa con side effects masivos** | `action_reset_to_draft` (163 líneas) toca 5 modelos en savepoint: quants, pickings, moves, lotes, staging. Si falla a mitad, el savepoint revierte todo — pero el diagnóstico es opaco | ALTA |
| **Duplicación de lógica de cleanup** | `_cleanup_orphan_moves` en el modelo (L3056) es casi idéntico a `LumberReceptionService.cleanup_orphan_moves`. Ambos tienen el FIX 2026-07-01 de protección de moves con quantity>0 | MEDIA |
| **Lógica financiera dispersa** | 5 métodos de compute para costos/precios: `_compute_average_price_clp`, `_compute_usd_amount`, `_compute_unit_prices`, `_compute_line_cost`, `_assign_costs_to_lots` — sin un service de costos unificado | MEDIA |
| **HTML inline** | `_compute_reception_summary` genera 122 líneas de HTML con lógica de agrupación por dimensión comercial. No es testeable sin BD | BAJA |
| **Fragilidad en reset** | `action_reset_to_draft` usa `force_delete` en contexto + `sudo()` para bypassear bloqueos de Odoo. Si Odoo 18 cambia la API de unlink, este método se rompe silenciosamente | ALTA |

## 4.2 Dónde hay mayor riesgo de regresión

| Zona | Por qué |
|---|---|
| `action_reset_to_draft()` (L1406–L1568) | Eliminación en cascada quants→lotes→pickings con savepoints anidados. Un cambio en el modelo de stock.quant rompe la reversa. |
| `_find_or_create_po_intelligent()` (L2278–L2430) | Lógica de matching de OC con normalización de claves y fallback manual. Si cambia el formato de OC chileno, el matching falla. |
| `action_confirm_reception()` (L2754–L2891) | Gate 2 y Gate 3 inline + creación de lotes + picking + validación. Si falla la firma criptográfica o el picking, todo el flujo se detiene. |
| `_compute_export_values()` (L693–L791) | Motor de cálculo con 3 fórmulas distintas (blank_clear, s2s_imperial, metric_direct) usando `lumber.export.formula`. Un cambio en los factores rompe todos los volúmenes. |

## 4.3 Zonas que requieren pruebas fuertes antes de tocar

1. **Flujo completo draft → processing → verified → done** con PDF + Excel reales
2. **Flujo con PDF de OC** — verificar extracción de precio, volumen, calidad
3. **Reset con quants existentes** — verificar que quants se eliminan y el reset no deja residuos
4. **OC matching con múltiples formatos** (MC 2506-01, MC-2506-01, 80123456)
5. **Flujo Blank Clear vs S2S** — verificar que `_compute_visual_defaults` y `_compute_export_values` aplican fórmulas correctas según `ingestion_profile`

---

# 5. Causas del tamaño

## 5.1 Explicación con evidencia concreta

### Causa 1: Dos modelos en un archivo (876 líneas de staging)
```
L48–L922:   LumberReceptionLine  (40 campos, 23 métodos)
L923–L3118: LumberReception     (57 campos, 47 métodos)
```
`LumberReceptionLine` ocupa el 28% del archivo. Si estuviera en archivo separado, el modelo principal serían ~2,200 líneas — comparable a `madenat_guia_processing` sin su línea staging (~3,667 líneas).

### Causa 2: OC/compras nunca se desacopló (500 líneas, 16%)
Pese a que parser y service sí se extrajeron, la lógica de órdenes de compra permanece 100% inline:
```
_find_or_create_po_intelligent()     → 153 líneas
create_po_from_oc_data()            → 149 líneas
_match_reception_purchase_order()   → 88 líneas
_normalize_oc_key + _canonize_oc_display + _compute_oc_reference_norm → 34 líneas
_update_po_reception_stats()        → 36 líneas
_get_current_exchange_rate()        → 42 líneas
```
Y `madenat_lumber_purchasing` extiende esta lógica con más `_inherit`.

### Causa 3: Reversa compleja con duplicación (300 líneas, 10%)
`action_reset_to_draft` (163 líneas) y `_cleanup_orphan_moves` (62 líneas) duplican lógica que también está en `LumberReceptionService.cleanup_orphan_moves` (50 líneas). Ambos archivos tienen el mismo FIX 2026-07-01 de protección de moves con quantity>0.

### Causa 4: Resumen HTML inline (122 líneas)
`_compute_reception_summary` (L1583–L1704) genera HTML de agrupación por dimensión comercial dentro del modelo. Esto es lógica de presentación pura que podría estar en un helper de reporte o widget QWeb.

### Causa 5: Crecimiento orgánico documentado
El archivo acumula parches visibles:
- "C4: VALIDACIÓN DOCUMENTAL POR TIPO DE PRODUCTO" (L980)
- "FASE 4: Campos de soporte para KPIs y Gates" (L1053)
- "HOMOLOGACIÓN OC 2026-06-21" (L1222)
- "PATCH 2026-06-18: DESACTIVADA autocreación automática de OC" (L2399)
- "FIX 2026-07-01: Protección de moves con cantidad recolectada" (L3080)

Cada patch agregó validaciones y lógica sin extraer responsabilidades existentes.

---

# 6. Comparación con `madenat_guia_processing.py`

| Métrica | `lumber_reception.py` | `madenat_guia_processing.py` | Diferencia |
|---|---|---|---|
| Líneas totales | 3,118 | 4,390 | -1,272 (29% menos) |
| Modelos en archivo | 2 | 2 | Igual |
| Métodos | 70 | 63 | +7 |
| Campos | 97 | 75 | +22 |
| `action_*` métodos | 9 | 13 | -4 |
| `.write()` calls | 25 | 33 | -8 |
| `.search()` calls | 13 | 44 | -31 (71% menos) |
| `.create()` calls | 15 | 14 | +1 |
| `.unlink()` calls | 13 | 8 | +5 |
| Método más largo | 163 líneas | 290 líneas | -127 |
| Responsabilidades mezcladas | 9 categorías | 8 categorías | +1 (validación) |
| **Desacople de parser** | ✅ Completo (722 líneas externas) | ❌ Inline (800 líneas) | Mejor |
| **Desacople de service** | ✅ Parcial (218 líneas externas) | ❌ Inexistente | Mejor |
| **Desacople de workflow** | ✅ Completo | ❌ Inexistente | Mejor |
| **OC/compras inline** | 500 líneas (16%) | 450 líneas (10%) | Similar |
| **Reversa inline** | 300 líneas (10%) | 550 líneas (13%) | Menos |
| **Línea staging inline** | 876 líneas (28%) | 722 líneas (16%) | Más |
| **Parseo inline residual** | ~250 líneas (8%) | ~800 líneas (18%) | Mucho menos |

**Conclusión comparativa:** `lumber_reception` está MEJOR desacoplado que `guia_processing` (parser, workflow y service extraídos), pero sigue siendo un monolito parcial por dos causas: OC inline + staging inline. El archivo es 29% más corto pero tiene 22 campos más porque maneja un modelo de datos más rico (finanzas, costos, múltiples perfiles de ingesta).

---

# 7. Mapa de refactor futuro

**ADVERTENCIA:** Propuesta de cortes lógicos. NO implementar sin tests de integración.

## 7.1 Qué podría ir a Service

| Responsabilidad | Destino sugerido | Métodos actuales |
|---|---|---|
| Gestión de OC (matching, creación, stats) | `services/reception_oc_service.py` | `_find_or_create_po_intelligent`, `create_po_from_oc_data`, `_match_reception_purchase_order`, `_normalize_oc_key`, `_canonize_oc_display`, `_update_po_reception_stats`, `_get_current_exchange_rate` |
| Costos y finanzas | `services/reception_cost_service.py` | `_assign_costs_to_lots`, `_compute_line_cost`, `_compute_average_price_clp`, `_compute_usd_amount`, `_compute_unit_prices` |
| Reversa unificada | `services/reception_reversal_service.py` | `action_reset_to_draft`, `_cleanup_orphan_moves` (unificar con `LumberReceptionService.cleanup_orphan_moves`) |
| Resumen HTML | `services/reception_summary_builder.py` | `_compute_reception_summary` |

## 7.2 Qué podría ir a Helper

| Responsabilidad | Destino |
|---|---|
| Conversión de fracciones imperiales | `_parse_smart_dimension`, `_get_fraction_text` → `utils_uom.py` (ya existe `decimal_inch_to_fraction_str`) |
| Naming de OC | `_normalize_oc_key`, `_canonize_oc_display` → mover a `reception_parser.py` donde ya existe `normalize_po_key`, `normalize_po_display` |

## 7.3 Qué podría ir a Mixin

| Responsabilidad | Nota |
|---|---|
| `_get_thickness_visual_ranges`, `_apply_thickness_visual` | Ya delegados a `madenat.ingestion.config` — correcto |
| Validación documental por tipo producto | `_check_required_documents` podría ser un constraint genérico en mixin |

## 7.4 Qué debería quedarse en el modelo

| Responsabilidad | Por qué |
|---|---|
| Definición de campos (97 campos) | Estructura de datos — deben quedarse |
| Constraint SQL anti-duplicado | Específico de `lumber.reception` |
| Botones `action_*` como puntos de entrada | Deben quedarse como métodos (delegando a services) |
| `create()`, `write()`, `unlink()` con hooks | Overrides del ORM |
| `_compute_*` simples | `_compute_can_process_reception`, `_compute_can_cancel_reception`, `_compute_can_reopen_reception`, `_compute_files_ready` |

## 7.5 Estrategia de extracción por fases

### Fase 1 — Separar LumberReceptionLine (bajo riesgo)
- Mover `LumberReceptionLine` (L48–L922) a `models/lumber_reception_line.py`
- 0 cambios de lógica, solo reubicación
- **Ganancia:** archivo principal → ~2,200 líneas

### Fase 2 — Extraer OC service (riesgo medio)
- Crear `services/reception_oc_service.py`
- Mover `_find_or_create_po_intelligent`, `create_po_from_oc_data`, helpers de OC
- El modelo delega a `ReceptionOCService(self.env).match_and_link(self, dg_data, oc_data)`
- Requiere tests de matching con golden records

### Fase 3 — Consolidar reversa (riesgo alto)
- Unificar `action_reset_to_draft` + `_cleanup_orphan_moves` + `LumberReceptionService.cleanup_orphan_moves`
- Crear `services/reception_reversal_service.py` con método único `hard_reset(reception)`
- **Requiere tests de integración completos**

### Fase 4 — Extraer costos (riesgo medio)
- Crear `services/reception_cost_service.py`
- Mover `_assign_costs_to_lots` y computes financieros

### Fase 5 — Extraer resumen HTML (riesgo bajo)
- Mover `_compute_reception_summary` a un helper dedicado
- Podría ser un widget QWeb en vez de HTML generado en Python

---

# 8. Texto para `02_CONTINUIDAD.md`

```markdown
### Auditoría profunda `lumber_reception` — 2026-07-01

**Archivo principal:** `lumber_reception.py` — 3,118 líneas, 70 métodos, 97 campos, 2 modelos en 1 archivo.

**Hallazgo central:** El archivo está MEJOR desacoplado que `madenat_guia_processing.py`
(parser, workflow y service ya extraídos, 722+150+218 líneas fuera del modelo), pero
sigue siendo un monolito parcial con 9 responsabilidades mezcladas. Las principales
causas de tamaño remanente son: (1) `LumberReceptionLine` nunca se separó a archivo
propio (876 líneas, 28%), (2) OC/compras permanece 100% inline (500 líneas, 16%),
(3) reversa y cleanup duplicados entre modelo y service.

**Comparación con guia_processing:**
- 29% menos líneas totales (3,118 vs 4,390)
- 71% menos `.search()` calls (13 vs 44) — mejor aislamiento
- Parser YA extraído (a diferencia de guia_processing)
- OC igual de mezclada que en guia_processing

**Estrategia de refactor propuesta (5 fases, NO implementada):**
1. Separar `LumberReceptionLine` a archivo propio → ~2,200 líneas en modelo principal
2. Extraer OC service (matching, creación, stats)
3. Consolidar reversa (unificar modelo + service)
4. Extraer costos a service
5. Extraer resumen HTML a helper

**Documento completo:** `RAW/AUDITORIA_PROFUNDA_LUMBER_RECEPTION_20260701.md`
```

---

*Documento generado por auditoría técnica. No se modificó ningún archivo de código.*
*Referencias: `CANON/00_ARQUITECTURA.md`, `CANON/12_FLUJOS_INGESTA.md`, `CANON/02_CONTINUIDAD.md`, `CANON/03_TESTS.md`, `CANON/04_DECISION_LOG.md`*