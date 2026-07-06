# AUDITORÍA PROFUNDA — `madenat_guia_processing`

**Fecha:** 2026-07-01
**Alcance:** Análisis técnico y documental sin modificación de código
**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Archivo principal:** `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`

---

# 1. Inventario técnico

## 1.1 Archivos implicados (eje central + dependencias directas)

| Archivo | Líneas | Rol |
|---|---|---|
| `models/madenat_guia_processing.py` | **4,390** | Modelo principal: 2 clases, 63 métodos, 75 campos |
| `views/guia_processing_views.xml` | 1,075 | Vista form (8 pestañas), vista list, header con botones |
| `views/guia_processing_list_search.xml` | ~80 | Vista search/filtros |
| `views/lumber_core_menu.xml` | ~180 | Menú raíz con `action_guia_processing_list` |
| `tests/test_guia_processing.py` | 212 | 15 tests (13 cabecera + 2 línea) |
| `wizard/madenat_guia_mass_update.py` | 122 | Wizard de actualización masiva de espesor/subproducto/producto |
| `wizard/madenat_guia_mass_update_views.xml` | ~60 | Vista del wizard |
| `migrations/18.0.5.3.0/post-migrate.py` | ~120 | Corrección post-migración de `technical_validation` en lotes huérfanos |
| `migrations/18.0.5.3.0/pre-migrate.py` | ~40 | Pre-migración de constraint SQL |
| `models/mixin_lumber_ingest.py` | 347 | Mixin compartido con `lumber_reception` (productos, volúmenes) |
| `models/ingestion_gate.py` | 257 | Gates 0+1 de validación de ingesta |
| `models/validation_checklist_mixin.py` | 453 | Mixin de checklist de validación (usa `guia_id`) |
| `models/stock_lot.py` | ~600 | Lotes: campos `guia_processing_id`, `reception_type='processed'` |
| `models/reception_parser.py` | ~600 | Parser compartido PDF/Excel — detección de duplicados en `madenat.guia.processing` |
| `models/lumber_reception.py` | ~3,500 | Campo `origin_processing_id → madenat.guia.processing` |
| `madenat_toll_processing/models/guia_processing_integration.py` | 161 | `_inherit` que extiende `action_validate` para toll processing |
| `madenat_toll_processing/models/toll_processing_order.py` | 447 | Campo `guia_ids` One2many → `madenat.guia.processing` |
| `madenat_lumber_costing/models/lumber_cost_distribution.py` | ~200 | Campo `reception_id → madenat.guia.processing` |
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | ~300 | Usa `madenat.guia.processing` para lookup de origen |
| `madenat_lumber_logistics/wizards/lumber_container_lot_wizard.py` | ~200 | Verifica `technical_validation='approved'` para lotes disponibles |
| `madenat_lumber_docs/CANON/12_FLUJOS_INGESTA.md` | — | Documenta flujo 1: guía procesada |
| `madenat_lumber_docs/CANON/00_ARQUITECTURA.md` | — | Sección 4.3 describe `madenat.guia.processing` |

**Total combinado estimado:** ~13,000 líneas distribuidas en 22+ archivos.

## 1.2 Métricas del archivo principal (`madenat_guia_processing.py`)

| Métrica | Valor |
|---|---|
| Líneas totales | **4,390** |
| Clases definidas | 2 (`MadenatGuiaProcessingLine` + `MadenatGuiaProcessing`) |
| Métodos top-level | **63** |
| Métodos `action_*` | **13** (8 botones UI + 5 helpers de adjuntos) |
| Campos definidos | **75** (25 línea staging + 50 cabecera) |
| Llamadas `.write()` | **33** |
| Llamadas `.search()` | **44** |
| Llamadas `.create()` | **14** |
| Llamadas `.unlink()` | **8** |
| Método más largo | `action_force_cancel` (~290 líneas, L3717–L4006) |
| Segundo más largo | `_parse_dispatch_pdf` (~315 líneas, L2128–L2442) |
| Tercero más largo | `action_validate` (~242 líneas, L1606–L1847) |
| Cuarto más largo | `_create_or_get_lot` (~199 líneas, L3381–L3579) |
| Quinto más largo | `do_full_processing` (~150 líneas, L1007–L1155) |
| Densidad `action_*` | 20.6% de los métodos son acciones de UI |

## 1.3 Dependencias principales (imports + herencia)

```
MadenatGuiaProcessing._inherit = [
    'mail.thread',              # Chatter
    'mail.activity.mixin',       # Actividades
    'madenat.lumber.ingest.mixin',  # find_or_create_lumber_product, validate_product_lumber_config
    'validation.checklist.mixin',   # Checklist de validación pre-stock
]

MadenatGuiaProcessingLine._inherit = [
    'madenat.lumber.ingest.line.mixin',  # Campos: pieces, vol_shipment_m3, vol_purchase_m3
]

Dependencias de negocio:
- stock.lot         (creación, actualización, costos)
- stock.picking     (creación, confirmación, validación, retorno)
- stock.move        (creación, cancelación, limpieza huérfanos)
- stock.move.line   (líneas de picking con lote)
- stock.quant       (limpieza residual en reversa)
- purchase.order    (creación, matching, vinculación)
- ir.attachment     (storage de PDFs y Excels)
- res.partner       (proveedor, búsqueda por RUT)
- toll.processing.order  (extensión vía _inherit)
```

---

# 2. Flujo real del módulo

## 2.1 Diagrama de estados y transiciones

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA DE UNA GUÍA PROCESADA                    │
│                                                                          │
│  ┌─────────┐    action_verify_data()    ┌───────────┐                    │
│  │  draft  │ ─────────────────────────→ │ verified  │                    │
│  │ (New)   │    (parsea PDF + Excel,    │           │                    │
│  │         │     crea staging lines,    │           │                    │
│  │         │     match OC)              │           │                    │
│  └────┬────┘                           └─────┬─────┘                    │
│       │                                      │                           │
│       │ action_force_cancel()                │ action_validate()         │
│       │ (desde draft)                        │ (orquesta:                │
│       │                                      │  do_full_processing()     │
│       │                                      │  → lotes + picking +      │
│       │                                      │    validación stock)      │
│       ▼                                      ▼                           │
│  ┌──────────┐                        ┌───────────┐                      │
│  │ cancelled│                        │ validated │                      │
│  │          │◄───────────────────────│           │                      │
│  └──────────┘  action_force_cancel() └─────┬─────┘                      │
│       ▲         (reversa simétrica         │                             │
│       │          de stock + quants)        │ action_reopen_to_draft()    │
│       │                                    │ (solo si no hay             │
│       │                                    │  movimientos externos)      │
│       │                                    ▼                             │
│       │                              ┌─────────┐                        │
│       └──────────────────────────────│  draft  │ (re-ciclo)             │
│                                      └─────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Paso a paso operativo

### Fase A — Creación (draft)
1. **Usuario crea registro** desde menú "Guías Procesadas" → estado `draft`
2. **Sube archivos**: PDF Guía (`guide_pdf_file`), Excel Packing (`excel_file`), opcionalmente PDF OC (`oc_pdf_file`)
3. **`write()` hook** (L2513): al subir Excel, intenta extraer número de guía del binario y auto-asignarlo a `name`

### Fase B — Verificación (draft → verified)
4. **Botón "Cargar y Verificar Datos"** → `action_verify_data()` (L1230)
   - **4a.** Elimina líneas staging previas (`processing_line_ids.unlink()`)
   - **4b.** Parsea Excel → `_parse_packing_excel()` → `_parse_excel_data_core()`
     - Detecta encabezados (Código, Cantidad, M3, LOTE, Espesor, Ancho, Largo)
     - Extrae dimensiones físicas en mm/m
     - Calcula dimensiones nominales imperiales (fracciones)
     - Busca OC en Excel → `_find_oc_reference_in_excel()`
   - **4c.** Crea líneas staging: `madenat.guia.processing.line.create()`
   - **4d.** Parsea PDF → `_parse_dispatch_pdf()` (L2128)
     - Extrae: número guía, OC documental, volumen comercial, costo neto, tipo de cambio USD, detalle servicio, RUT emisor, nombre emisor, fecha emisión
     - Resuelve proveedor por RUT (crea si no existe)
     - Extrae OC documental → `oc_reference_raw` (prioridad PDF > Excel)
   - **4e.** Persiste datos del PDF en la cabecera (campos financieros y de servicio)
   - **4f.** Ejecuta matching de OC → `_match_purchase_order()`
   - **4g.** Cambia estado a `verified`

### Fase C — Validación (verified → validated)
5. **Botón "Aprobar e Ingresar a Stock"** → `action_validate()` (L1606)
   - **5a. Validaciones previas** (bloqueantes):
     - Espesor nominal > 0 en todas las líneas
     - Subproducto asignado en todas las líneas
     - Tipo de cambio USD válido (no 0, no 1.0 para servicios)
     - OC vinculada si hay `oc_reference_raw`
   - **5b. Fase 0 — Auto-reparación**: asegura que todos los productos sean `is_storable=True`
   - **5c. Fase 1 — Procesamiento**: `do_full_processing()` (L1007)
     - Por cada línea staging: obtiene precio USD de OC, busca/crea producto, construye diccionario de dimensiones, crea/actualiza lote vía `_create_or_get_lot()`
     - Inyecta datos extra en cada lote (ref, length_ft, vol_shipment_m3, volumen_m3, width_visual, thickness_visual)
     - Asigna costos a lotes generados → `_assign_costs_to_generated_lots()`
     - Vincula lotes a la guía → `lot_ids = [(6, 0, [...])]`
     - Sincroniza líneas de OC → `_sync_purchase_order_lines()`
     - Crea picking → `_create_picking_and_lines()` → delega a `_get_or_create_picking_unified()`
   - **5d. Recupera/crea picking unificado**: `_get_or_create_picking_unified()` (L1900)
     - Anti-duplicados: busca por `origin = self.name`
     - Ubicación destino dinámica: asignación manual > config tipo operación > fallback "Stock"
     - Crea movimientos desde lotes o lot_data
   - **5e. Procesamiento de movimientos**: limpia fantasmas, inyecta volumen nominal, crea move_lines
   - **5f. Validación del picking**: confirma, asigna, valida con `skip_backorder=True`
   - **5g. Actualización final**: estado → `validated`, marca lotes como `recepcionado`

### Fase D — Cancelación segura
6. **Botón "Cancelar Guía"** → `action_force_cancel()` (L3717)
   - Escudo logístico: bloquea si lotes están en contenedores activos
   - Escudo financiero: bloquea si hay costos contables → cierre por integridad
   - Reversión simétrica de pickings done (crea return picking con tipo incoming no-EMB)
   - Cancelación ORM de pickings no-done
   - Desvincula lotes con `technical_validation='rejected'`
   - Resetea líneas staging
   - Pone volúmenes en cero, estado → `cancelled`

### Fase E — Reapertura
7. **Botón "Reabrir a Borrador"** → `action_reopen_to_draft()` (L4009)
   - Escudo logístico: bloquea si lotes en contenedores
   - Escudo de ubicación: bloquea si quants en ubicaciones externas
   - Escudo financiero: bloquea si hay costos asociados
   - Desvincula pickings internos done (cambia origin a `REVERTIDO-{name}`)
   - Cancela pickings draft/assigned
   - Limpia lotes con `technical_validation='rejected'`
   - Fase 3.5: pone quants residuales en cero
   - Fase 3.6: limpia stock.moves huérfanos
   - Limpia TODOS los campos (financieros, OC, servicio, volúmenes) → estado `draft`

### Fase F — Eliminación
8. **`unlink()`** (L4284): solo permite draft/cancelled, limpia moves huérfanos antes

### Fase G — Toll Processing (extensión)
9. **`madenat_toll_processing` extiende `action_validate()`**:
   - Recalcula volumen de retorno y yield en la Toll Order
   - Dispara consumo de materia prima si no se había hecho
   - Hereda costos de lotes origen a lotes procesados (distribución proporcional por m³)

---

# 3. Responsabilidades mezcladas

El archivo de 4,390 líneas contiene DOS modelos que mezclan al menos **8 categorías de responsabilidad** distintas:

## 3.1 Clasificación de responsabilidades

| Categoría | Métodos involucrados | Líneas aprox. | % del total |
|---|---|---|---|
| **1. Negocio / Dominio** (dimensiones, fracciones, volúmenes madera) | `_compute_imperial_values`, `_get_fraction_text`, `_parse_fraction`, `_get_nominal_dimension`, `_calculate_fractional_approximation`, `_compute_vol_mbf`, `_compute_vol_shipment_m3`, `_compute_vol_physical_m3`, `_compute_vol_purchase_m3`, `_compute_all_totals`, `_validar_y_enriquecer_lineas`, `_check_imperial_fractions`, `_find_closest_standard`, `_get_industry_width_map` | ~700 | 16% |
| **2. Inventario / Stock** (creación lotes, pickings, movimientos, validación) | `do_full_processing`, `_create_or_get_lot`, `_get_or_create_picking_unified`, `_create_picking_and_lines`, `_create_stock_picking_from_guia`, `action_validate` | ~900 | 21% |
| **3. Ingesta documental / Parseo** (PDF, Excel) | `action_verify_data`, `_parse_dispatch_pdf`, `_parse_packing_excel`, `_parse_excel_data_core`, `_parse_float_value`, `_find_oc_reference_in_excel`, `_try_extract_guide_number_from_binary` | ~800 | 18% |
| **4. UI / Acciones de usuario** (botones, wizards, notificaciones) | `action_verify_data`, `action_validate`, `action_assign_commercial_defaults`, `action_process_from_staging`, `action_open_po`, `action_create_purchase_order_from_document`, `action_attach_oc_pdf`, `action_attach_guide_pdf`, `action_attach_excel` | ~500 | 11% |
| **5. Auditoría / Log / Trazabilidad** | `_generate_lot_details_json`, `_compute_package_stats`, `_compute_lineas_procesadas`, `_compute_can_process`, `_compute_can_cancel`, `_compute_can_reopen`, `_store_binary_as_attachment`, `write` | ~250 | 6% |
| **6. Recuperación / Reversa** | `action_force_cancel`, `action_reopen_to_draft`, `_cleanup_orphan_moves_guia`, `unlink` | ~550 | 13% |
| **7. OC / Compras / Matching** | `_match_purchase_order`, `_normalize_oc_key`, `_canonize_oc_name`, `_compute_oc_reference_norm`, `_is_plausible_oc_reference`, `_create_basic_purchase_order`, `_extract_po_draft_values_from_oc_pdf`, `action_create_purchase_order_from_document`, `_sync_purchase_order_lines`, `_obtener_precio_desde_oc` | ~450 | 10% |
| **8. Costos / Finanzas** | `_assign_costs_to_generated_lots` | ~50 | 1% |

## 3.2 Mezcla concreta de capas

**El mismo método `action_validate()` (L1606–L1847) ejecuta:**
- Validaciones de negocio (espesor nominal, subproducto, tipo de cambio)
- Auto-reparación de configuración de productos (stockable)
- Orquestación de creación de lotes
- Orquestación de creación de picking
- Manipulación directa de stock.move y stock.move.line
- Limpieza de movimientos fantasmas
- Inyección de volumen nominal en movimientos
- Validación de picking con contexto forzado (`skip_backorder`, `skip_immediate`)
- Manejo de wizard de backorder si aparece
- Escritura de estado final

**El método `_parse_dispatch_pdf()` (L2128–L2442) contiene:**
- 7 secciones distintas de extracción (guía, OC, volumen, costo, TC, servicio, emisor)
- ~15 patrones regex distintos
- Lógica de diagnóstico temporal con hardcode de número de guía (`'19846'`)
- Búsqueda/creación de `res.partner` por RUT
- Parseo de fechas con múltiples formatos
- Un diccionario de retorno con 12 claves

---

# 4. Riesgos de mantenibilidad

## 4.1 Qué vuelve difícil modificarlo

| Factor | Evidencia | Severidad |
|---|---|---|
| **Métodos monolíticos** | `action_force_cancel`: 290 líneas. `_parse_dispatch_pdf`: 315 líneas. `action_validate`: 242 líneas. `_create_or_get_lot`: 199 líneas | ALTA |
| **Alta densidad de side effects** | `action_validate()` hace: writes a guía, lotes, moves, move_lines, picking, quants + validación de wizard. Una sola llamada toca 6 modelos. | ALTA |
| **Branching complejo** | `_compute_vol_shipment_m3` tiene 3 ramas de fallback + try/except. `_get_or_create_picking_unified` tiene 4 niveles de prioridad para ubicación destino. | MEDIA |
| **Acoplamiento a modelos Odoo** | 33 `.write()`, 44 `.search()`, 14 `.create()`, 8 `.unlink()` en un solo archivo. Dependencia fuerte de `stock.picking`, `stock.move`, `stock.move.line`, `stock.quant`, `stock.lot`, `purchase.order`, `res.partner`, `ir.attachment` | ALTA |
| **Lógica de diagnóstico hardcodeada** | `_parse_dispatch_pdf` contiene `if self.name and '19846' in str(self.name):` repetido 5 veces con logs de diagnóstico que nunca se limpiaron | MEDIA |
| **Código duplicado/comentado** | Líneas con "TD-007: v1 eliminada" indican versiones anteriores de métodos removidos pero referenciados en comentarios. `_compute_vol_purchase_m3` tiene 2 versiones en la historia del archivo. | BAJA |
| **Fragilidad transaccional** | `_create_or_get_lot` usa savepoint + excepción IntegrityError para manejar colisiones UNIQUE — si falla el savepoint, el estado de la BD es impredecible | ALTA |
| **Writes masivos sin chunking** | `action_force_cancel` escribe en hasta 6 modelos en un solo método. `action_reopen_to_draft` hace write de 30+ campos de una vez. | MEDIA |

## 4.2 Dónde hay mayor riesgo de regresión

| Zona | Por qué |
|---|---|
| `action_force_cancel()` (L3717–L4006) | Lógica de reversión simétrica de stock con creación de return picking + búsqueda de tipo de operación no-EMB. Un cambio en la configuración de almacenes rompe la reversa. |
| `_create_or_get_lot()` (L3381–L3579) | Savepoint + flush_model + invalidate_model + búsqueda post-colisión. La secuencia es frágil y depende del orden de escritura en BD. |
| `_compute_vol_shipment_m3()` (L476–L534) | Fórmula con bifurcación Blank vs S2S usando `get_s2s_adjustment()`. Un cambio en el factor `INCH_SQ_METERS_TO_M3` o `BLANK_CLEAR_FACTOR` impacta todos los volúmenes de exportación. |
| `action_validate()` (L1606–L1847) | Cualquier cambio en el flujo de validación de picking (Odoo 18 cambió `button_validate`) rompe el ingreso a stock. |
| `_get_or_create_picking_unified()` (L1900–L2065) | Motor único de creación de albaranes. Si falla la ubicación destino, todo el flujo se detiene. |

## 4.3 Zonas que requieren pruebas fuertes antes de tocar

1. **Flujo completo draft → verified → validated** con PDF y Excel reales (guía 19846 como golden record)
2. **Cancelación con picking done** — verificar que el return picking se crea, confirma y valida correctamente
3. **Reapertura con quants residuales** — verificar que los quants se ponen en cero y los lotes quedan con `technical_validation='rejected'`
4. **Toll processing** — verificar que la herencia de costos y el consumo de materia prima funcionan tras `action_validate()` extendido
5. **Duplicados** — verificar que el `_sql_constraints` (unique name + partner_id) bloquea correctamente

---

# 5. Causas del tamaño

## 5.1 Explicación con evidencia concreta

El archivo tiene 4,390 líneas. No es un número arbitrario — es consecuencia directa de decisiones arquitectónicas acumuladas:

### Causa 1: Dos modelos en un archivo (723 líneas de línea staging)
```
L1–L722:   MadenatGuiaProcessingLine  (25 campos, 18 métodos de compute/constrain)
L723–L4390: MadenatGuiaProcessing     (50 campos, 45 métodos)
```
Las líneas L1–L722 son del modelo de staging. Si estuvieran en archivo separado, el modelo principal serían ~3,667 líneas — aún grande pero con separación clara de responsabilidades.

### Causa 2: Parseo documental inline (800+ líneas, 18% del archivo)
```
_parse_dispatch_pdf()          → 315 líneas (L2128–L2442)
_parse_packing_excel()         → 47 líneas (L2445–L2491)
_parse_excel_data_core()       → 110 líneas (L2524–L2633)
_parse_float_value()           → 37 líneas (L2639–L2675)
_find_oc_reference_in_excel()  → 41 líneas (L2834–L2874)
_extract_po_draft_values_from_oc_pdf() → 113 líneas (L2966–L3078)
```
Este es código de infraestructura pura (lectura de archivos, regex, pandas, pdfplumber). No es lógica de negocio de Odoo. Si se extrajera a un servicio/helper, el modelo perdería ~800 líneas.

### Causa 3: Lógica de OC y compras mezclada (450 líneas, 10%)
```
_match_purchase_order()                    → 103 líneas
_normalize_oc_key() + _compute_oc_reference_norm + _canonize_oc_name → 46 líneas
_is_plausible_oc_reference()               → 45 líneas
_create_basic_purchase_order()             → 14 líneas
_extract_po_draft_values_from_oc_pdf()     → 113 líneas
action_create_purchase_order_from_document() → 127 líneas
_sync_purchase_order_lines()               → 39 líneas
_obtener_precio_desde_oc()                 → 4 líneas
```
La gestión de órdenes de compra está completamente mezclada con el flujo de guías. El modelo no solo recibe madera: también crea OCs, hace matching, extrae datos de PDFs de OC, y sincroniza líneas.

### Causa 4: Reversa/cancelación duplicada (550 líneas, 13%)
```
action_force_cancel()       → 290 líneas (L3717–L4006)
action_reopen_to_draft()    → 244 líneas (L4009–L4252)
_cleanup_orphan_moves_guia() → 87 líneas (L4303–L4389)
unlink()                    → 19 líneas (L4284–L4301)
```
Dos métodos de reversa con lógica parcialmente solapada (ambos manejan lotes, pickings, quants, moves huérfanos). La duplicación es explícita: ambos escriben `technical_validation='rejected'`, ambos desvinculan lotes, ambos limpian.

### Causa 5: Comentarios y documentación inline abundante (est. 400+ líneas)
Docstrings extensos tipo "ARQUITECTURA", "CHANGELOG", "FIX", separadores visuales con `═══`. Esto es valioso para entender el código pero infla el conteo de líneas.

### Causa 6: Diagnóstico temporal no removido
Los bloques `if self.name and '19846' in str(self.name):` con `_logger.warning` en `_parse_dispatch_pdf` son 5 bloques (~40 líneas) de diagnóstico de producción que ya debieron eliminarse.

### Causa 7: Crecimiento orgánico sin refactor
Cada patch (2026-06-18 OC, 2026-06-30 emisor, 2026-06-30 TC, 2026-06-30 OC bloqueo, 2026-06-11 constraint SQL) agregó validaciones y lógica al mismo archivo sin extraer nada. La lista de CHANGELOG dentro del código muestra al menos 12 versiones/parches aplicados.

---

# 6. Mapa de refactor futuro

**ADVERTENCIA:** Esto es una propuesta de cortes lógicos. NO implementar sin antes:
1. Escribir tests de integración que cubran el flujo completo actual
2. Verificar que cada corte no rompe dependencias con `madenat_toll_processing`, `madenat_lumber_logistics`, `madenat_lumber_costing`, `madenat_lumber_reports`
3. Ejecutar migración en staging con golden records reales (guía 19846)

## 6.1 Qué podría ir a Service (capa de lógica de negocio pura)

| Responsabilidad | Archivo destino sugerido | Métodos actuales |
|---|---|---|
| Parseo de PDF (guía, servicio, OC) | `services/guia_pdf_parser.py` | `_parse_dispatch_pdf`, `_extract_po_draft_values_from_oc_pdf`, `_is_plausible_oc_reference` |
| Parseo de Excel (packing list) | `services/guia_excel_parser.py` | `_parse_packing_excel`, `_parse_excel_data_core`, `_parse_float_value`, `_find_oc_reference_in_excel`, `_try_extract_guide_number_from_binary` |
| Conversión de dimensiones (mm ↔ imperial) | `services/lumber_dimension_converter.py` | `_compute_imperial_values`, `_get_fraction_text`, `_parse_fraction`, `_get_nominal_dimension`, `_calculate_fractional_approximation`, `_find_closest_standard`, `_get_industry_width_map` |
| Cálculo de volúmenes | `services/lumber_volume_calculator.py` | `_compute_vol_physical_m3`, `_compute_vol_purchase_m3`, `_compute_vol_mbf`, `_compute_vol_shipment_m3`, `_compute_all_totals`, `_validar_y_enriquecer_lineas` |
| Gestión de OC (matching, creación) | `services/guia_oc_service.py` | `_match_purchase_order`, `_normalize_oc_key`, `_canonize_oc_name`, `_compute_oc_reference_norm`, `_create_basic_purchase_order`, `_sync_purchase_order_lines`, `_obtener_precio_desde_oc` |

## 6.2 Qué podría ir a Helper (utilidades sin estado)

| Responsabilidad | Destino |
|---|---|
| Fracciones imperiales | Ya está parcialmente en `utils_uom.py` — falta migrar `_get_fraction_text`, `_parse_fraction` |
| Normalización de floats | Ya está en `_parse_float_value` — mover a `utils_uom.py` |
| Constantes de ruido OCR | `_OC_HEADER_NOISE` → `utils_uom.py` o archivo de constantes |

## 6.3 Qué podría ir a Mixin (comportamiento compartido)

| Responsabilidad | Destino |
|---|---|
| Flujo de staging (verify → process → validate) | `mixin_lumber_ingest.py` ya existe pero solo cubre find_or_create_product. Ampliar para orquestación. |
| Checklist de validación | Ya está en `validation_checklist_mixin.py` |

## 6.4 Qué debería quedarse en el modelo

| Responsabilidad | Por qué |
|---|---|
| Definición de campos (75 campos) | Son la estructura de datos del modelo — deben quedarse |
| Constraint SQL anti-duplicado | Es específico de este modelo |
| Botones `action_*` como puntos de entrada | Deben quedarse como métodos del modelo (pero delegar a services) |
| `write()`, `unlink()` con hooks | Deben quedarse como overrides del ORM |
| `_compute_*` simples que solo agregan campos | `_compute_lineas_procesadas`, `_compute_can_process`, `_compute_can_cancel`, `_compute_can_reopen` |

## 6.5 Estrategia de extracción por fases (sugerida)

### Fase 1 — Separar modelo de staging (bajo riesgo)
- Mover `MadenatGuiaProcessingLine` a `models/madenat_guia_processing_line.py`
- 0 cambios de lógica, solo reubicación

### Fase 2 — Extraer parseo documental (riesgo medio)
- Crear `services/guia_pdf_parser.py` y `services/guia_excel_parser.py`
- Mover métodos de parseo sin cambiar firmas
- El modelo llama a los servicios: `self._parse_dispatch_pdf(attachment)` → `GuiaPdfParser.parse(attachment)`
- Requiere tests de regresión con PDFs y Excels reales

### Fase 3 — Extraer conversión de dimensiones (riesgo bajo)
- Crear `services/lumber_dimension_converter.py`
- Centralizar `_get_fraction_text`, `_parse_fraction`, `_get_nominal_dimension`, `_calculate_fractional_approximation`
- Estos métodos son funciones puras — no dependen de `self` más que para logs

### Fase 4 — Extraer gestión de OC (riesgo medio)
- Crear `services/guia_oc_service.py`
- `_match_purchase_order`, `action_create_purchase_order_from_document`, helpers de normalización
- Requiere tests de matching con golden records

### Fase 5 — Consolidar reversa (riesgo alto)
- Unificar `action_force_cancel` y `action_reopen_to_draft` en un servicio de reversa con modo (`hard` vs `soft`)
- Eliminar duplicación de lógica de limpieza de lotes/quants/moves
- **Requiere batería completa de tests de integración antes de tocar**

---

# 7. Texto para `02_CONTINUIDAD.md`

```markdown
### Auditoría profunda `madenat_guia_processing` — 2026-07-01

**Archivo principal:** `madenat_guia_processing.py` — 4,390 líneas, 63 métodos, 75 campos, 2 modelos en 1 archivo.

**Hallazgo central:** El archivo concentra 8 responsabilidades distintas (negocio maderero,
inventario, parseo documental, UI, trazabilidad, reversa, OC/compras, costos). Los métodos
más largos (`action_force_cancel`: 290 líneas, `_parse_dispatch_pdf`: 315 líneas,
`action_validate`: 242 líneas) mezclan validación, orquestación, side effects en múltiples
modelos y manejo de wizard en un solo método.

**Dependencias cruzadas:** 22 archivos en 5 módulos (`core`, `toll_processing`, `costing`,
`logistics`, `reports`) referencian o extienden `madenat.guia.processing`. Cualquier
refactor debe considerar el `_inherit` en `madenat_toll_processing` y los campos FK en
`stock.lot`, `lumber.cost.distribution`, `toll.processing.order`.

**Estrategia de refactor propuesta (5 fases, NO implementada):**
1. Separar `MadenatGuiaProcessingLine` a archivo propio
2. Extraer parseo PDF/Excel a services
3. Extraer conversión de dimensiones a service
4. Extraer gestión de OC a service
5. Consolidar reversa (unificar `action_force_cancel` + `action_reopen_to_draft`)

**Golden record:** Guía `19846` (ID=14 en test) — 19 lotes con `guia_processing_id=14`.
**Documento completo:** `RAW/AUDITORIA_PROFUNDA_GUIA_PROCESSING_20260701.md`
```

---

*Documento generado por auditoría técnica automatizada. No se modificó ningún archivo de código.*
*Referencias: `CANON/00_ARQUITECTURA.md`, `CANON/12_FLUJOS_INGESTA.md`, `CANON/02_CONTINUIDAD.md`, `CANON/03_TESTS.md`, `CANON/04_DECISION_LOG.md`*