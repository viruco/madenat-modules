# 📊 INFORME DE AUDITORÍA — madenat_guia_processing — 2026-06-04

---

## 1. QUÉ HACE (descripción funcional completa)

### Flujo completo de negocio: Madera Procesada por Servicio Externo

1.  **Creación de Guía**: El usuario registra una guía de madera procesada por un aserradero externo, indicando proveedor, orden de compra (opcional), ubicación de patio y adjuntos (PDF de guía + Excel de packing list).
2.  **Carga y Verificación (action_verify_data)**: El sistema parsea el Excel de packing list y extrae líneas con dimensiones físicas (mm, m) y volumen. Crea registros de staging (`MadenatGuiaProcessingLine`) con validación visual pendiente. Opcionalmente parsea el PDF para extraer datos financieros (T/C, costo de servicio).
3.  **Asignación Comercial (action_assign_commercial_defaults)**: Botón manual que iguala el espesor nominal de compra al espesor físico cuando no hay OC definida. Esto permite que el volumen de compra se calcule automáticamente.
4.  **Procesamiento (action_process_from_staging → do_full_processing)**: Puente blindado que transforma las líneas de staging en lotes reales (`stock.lot`). Para cada línea: crea/encuentra el producto, genera un lote con dimensiones físicas y nominales, inyecta estados de trazabilidad, y acumula datos para la fase logística.
5.  **Sincronización con OC (_sync_purchase_order_lines)**: Si hay una Orden de Compra vinculada, el sistema agrupa los lotes por producto y actualiza/crea líneas de OC.
6.  **Creación de Albaranes (_create_picking_and_lines / _get_or_create_picking_unified)**: Motor unificado que garantiza 1 guía = 1 albarán de entrada (`stock.picking` tipo incoming). Genera movimientos de stock (`stock.move` y `stock.move.line`) asociando los lotes físicos al albarán.
7.  **Validación (action_validate)**: Fase final. Autorrepara productos consumibles forzándolos a almacenables. Recupera/crea el picking, confirma, asigna cantidades, inyecta volúmenes nominales en los movimientos y ejecuta `button_validate` (con manejo de backorder wizard). Marca la guía como 'validated' y los lotes como 'recepcionado'.
8.  **Cancelación Forzada (action_force_cancel)**: Bloquea cancelación si hay contenedores activos, costos financieros comprometidos o albaranes ya completados. Limpia pickings, lotes y líneas de staging de forma segura.
9.  **Eliminación (unlink)**: Solo permite borrar guías en estado 'draft' o 'cancelled'. Incluye limpieza en cascada de `stock.move` huérfanos mediante ORM con savepoint.

### State Machine

| Estado       | Descripción                              | Transiciones desde             |
|-------------|------------------------------------------|--------------------------------|
| `draft`     | Borrador — recién creada                 | → verified, cancelled          |
| `verified`  | 🔍 Por Verificar — staging cargado       | → draft (reopen), processed    |
| `processed` | 📦 Procesada — lotes y picking creados   | → validated, cancelled, draft  |
| `validated` | ✅ Validada — stock confirmado           | — (terminal)                   |
| `cancelled` | ❌ Cancelada                              | → draft (reopen)               |

### Modelos involucrados (touch points del archivo)

- `madenat.guia.processing` — cabecera
- `madenat.guia.processing.line` — staging (líneas de verificación)
- `stock.lot` — lotes generados
- `stock.picking` — albaranes de recepción
- `stock.move` / `stock.move.line` — movimientos de inventario
- `purchase.order` — órdenes de compra asociadas
- `product.product` / `product.template` — productos de madera
- `res.partner` — proveedores
- `res.currency` — moneda y tipo de cambio
- `ir.attachment` — archivos adjuntos
- `madenat.subproducto` — clasificación FAS/S2S/Rough
- `madenat.ingestion.config` — configuración paramétrica (Fase 2)
- `lumber.ingestion.format` — formato de ingesta (Fase 3)
- `validation.checklist.mixin` — mixin de checklist
- `madenat.lumber.ingest.mixin` — mixin de ingesta compartido
- `stock.lot.cost.line` — líneas de costo por lote

---

## 2. ESTRUCTURA DEL CÓDIGO

### Clases: 2
| Clase | Línea | _name | Descripción |
|-------|-------|-------|-------------|
| `MadenatGuiaProcessingLine` | 90 | `madenat.guia.processing.line` | Línea de staging/verificación con doble sistema de dimensiones |
| `MadenatGuiaProcessing` | 783 | `madenat.guia.processing` | Cabecera orquestadora de recepción de madera procesada |

### Herencia de MadenatGuiaProcessing
`_inherit = ['mail.thread', 'mail.activity.mixin', 'madenat.lumber.ingest.mixin', 'validation.checklist.mixin']`

### Métodos: 47 (41 en cabecera + 6 en línea staging)

| Método | Línea | Descripción |
|--------|-------|-------------|
| `_inverse_length_ft` | 239 | Inverso: actualiza largo_m desde length_ft |
| `_compute_default_length` | 284 | Valor por defecto de largo |
| `_compute_default_width` | 291 | Valor por defecto de ancho |
| `_compute_vol_purchase_m3` (line) | 301/424 | Calcula volumen de compra desde dimensiones nominales |
| `_compute_imperial_values` | 321 | Calcula valores imperiales (ft, MBF) desde métrico |
| `_find_closest_standard` | 380 | Busca dimensión estándar más cercana en LUMBER_DIMENSION_MAP |
| `_compute_vol_physical_m3` | 416 | Calcula volumen físico desde dimensiones reales |
| `_get_industry_width_map` | 440 | Mapeo de anchos industriales |
| `_compute_vol_mbf` | 465 | Convierte m³ a MBF |
| `_compute_vol_shipment_m3` | 533 | Calcula volumen de embarque |
| `_get_fraction_text` | 597 | Convierte decimal a fracción imperial |
| `_parse_fraction` | 661 | Parsea fracción imperial a decimal |
| `_check_imperial_fractions` | 722 | Valida octavos imperiales |
| `_compute_all_totals` | 989 | Suma inteligente de volúmenes (m³, MBF, diferencias) |
| `_compute_package_stats` | 1044 | Calcula conteo de paquetes y lotes únicos |
| `do_full_processing` | 1069 | **ORQUESTADOR PRINCIPAL**: staging → lotes reales (V9.1) |
| `_sync_purchase_order_lines` | 1215 | Sincroniza líneas de OC agrupando lotes por producto |
| `action_assign_commercial_defaults` | 1256 | Botón: iguala espesor nominal al físico en líneas vacías |
| `action_verify_data` | 1288 | Carga Excel/PDF → staging + extracción datos financieros |
| `action_process_from_staging` | 1450 | **PUENTE BLINDADO v5.0**: staging → do_full_processing |
| `action_validate` | 1535 | **VALIDACIÓN v23.0**: autorreparación + inyección nominal + validación picking |
| `_create_stock_picking_from_guia` | 1708 | Helper: crea picking desde guía (usa motor unificado) |
| `_get_or_create_picking_unified` | 1755 | **MOTOR ÚNICO v7.1**: búsqueda/creación de albaranes sin duplicados |
| `_parse_dispatch_pdf` | 1929 | Parsea PDF de guía de despacho |
| `_parse_packing_excel` | 2076 | Parsea Excel de packing list |
| `_parse_excel_data_core` | 2110 | Core de parseo Excel con detección de columnas |
| `_parse_float_value` | 2225 | Conversión segura de valores numéricos |
| `_get_nominal_dimension` | 2264 | Resuelve dimensión nominal desde física |
| `_validar_y_enriquecer_lineas` (v1) | 2297 | Validación y enriquecimiento de líneas parseadas |
| `_calculate_fractional_approximation` | 2354 | Aproximación fraccional imperial |
| `_validar_y_enriquecer_lineas` (v2) | 2405 | Segunda versión del validador |
| `_find_oc_reference_in_excel` | 2474 | Búsqueda de referencia OC en Excel |
| `_generate_lot_details_json` | 2516 | Genera JSON para vista de detalles de lotes |
| `_assert_ready_to_validate` | 2582 | Validación previa: monto > 0 exige volumen > 0 |
| `_create_basic_purchase_order` | 2587 | Crea OC básica si no existe |
| `_assign_costs_to_generated_lots` | 2596 | Distribuye costos de servicio a lotes |
| `_create_or_get_lot` | 2617 | **CREACIÓN INTELIGENTE v8.0**: busca/crea lotes con estados y visuales |
| `find_or_create_product` | 2801 | Delegación al mixin de ingesta |
| `_create_picking_and_lines` | 2814 | **LEGACY**: genera movimientos de stock (usa motor unificado) |
| `_obtener_precio_desde_oc` | 2857 | Obtiene precio unitario desde OC |
| `_obtener_precio_por_defecto` | 2862 | Precio por defecto = 0.0 |
| `_mm_a_pulgadas_frac` | 2865 | Convierte mm a texto de pulgadas |
| `_compute_lineas_procesadas` | 2876 | Cuenta lotes procesados |
| `_compute_can_process` | 2883 | Habilita botón procesar (draft + archivos adjuntos) |
| `_compute_can_validate` | 2896 | **UNIFICADO**: checklist + volumen físico + estado 'processed' |
| `_compute_can_cancel` | 2927 | Habilita cancelar (draft, processed) |
| `_compute_can_reopen` | 2932 | Habilita reabrir (verified, cancelled, processed) |
| `action_open_po` | 2941 | Navega a la OC vinculada |
| `action_force_cancel` | 2973 | **CANCELACIÓN SEGURA v2.0**: escudos logístico + financiero |
| `action_reopen_to_draft` | 3258 | Reabre guía a borrador |
| `_store_binary_as_attachment` | 3371 | Helper: binary → ir.attachment |
| `action_attach_oc_pdf` | 3381 | Adjunta PDF de OC |
| `action_attach_guide_pdf` | 3387 | Adjunta PDF de guía |
| `action_attach_excel` | 3393 | Adjunta Excel de packing |
| `unlink` | 3398 | **BLINDAJE**: solo draft/cancelled + limpieza moves |
| `_cleanup_orphan_moves_guia` | 3417 | Elimina stock.moves huérfanos via ORM con savepoint |

### Campos principales de MadenatGuiaProcessing (cabecera): 55+

| Grupo | Campos |
|-------|--------|
| Identidad | `name` (Número Guía), `date_emission`, `partner_id`, `order_id` |
| Adjuntos | `pdf_attachment_id`, `excel_attachment_id`, `oc_pdf_file`, `guide_pdf_file`, `excel_file` + filenames |
| Relaciones | `processing_line_ids` (One2many), `lot_ids` (Many2many), `carrier_id`, `assignment_location_id` |
| Monetario | `additional_cost`, `currency_id`, `rate_date`, `rate_usd` |
| Servicio | `service_product_name`, `service_volume_m3`, `service_unit_price_clp`, `service_date`, `service_code` |
| KPIs | `total_paquetes`, `total_lotes_unicos`, `lineas_procesadas` |
| Volúmenes (m³) | `vol_comercial`, `vol_fisico`, `vol_shipment_m3`, `vol_total_m3`, `vol_comercial_pdf` |
| Volúmenes (MBF) | `vol_comercial_mbf`, `vol_fisico_mbf`, `vol_total_mbf` |
| Diferencias | `diff_m3`, `diff_pct`, `diff_mbf` |
| Estado/Permisos | `state`, `can_process`, `can_validate`, `can_cancel`, `can_reopen`, `cancel_reason` |
| Metadatos | `notes`, `date_processed`, `_raw_pdf_text`, `lot_details_data`, `grouping_details_json` |

### Líneas totales: 3465

---

## 3. INTEGRACIONES

### Llama a (modelos externos):
- `stock.lot`, `stock.picking`, `stock.move`, `stock.move.line`
- `purchase.order`, `product.product`
- `res.partner`, `res.currency`, `res.users`
- `ir.attachment`
- `madenat.subproducto`
- `madenat.reception.parser` (AbstractModel usado por acción de verificación)
- `stock.lot.cost.line` (líneas de costo)
- `madenat.ingestion.config`, `lumber.ingestion.format` (Fases 2 y 3)
- `validation.checklist.mixin`, `madenat.lumber.ingest.mixin` (mixins heredados)
- `stock.picking.type`, `stock.location`

### Es llamado por (módulos externos):
- `madenat_toll_processing/models/guia_processing_integration.py` — hereda `MadenatGuiaProcessing` para extender `action_validate` con lógica de maquila/toll processing
- `madenat_lumber_core/wizard/madenat_guia_mass_update.py` — wizard de actualización masiva

### Vistas:
- `custom_addons/madenat_lumber_core/views/guia_processing_views.xml` — vista formulario principal
- `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml` — vista lista y búsqueda

### Wizards:
- `custom_addons/madenat_lumber_core/wizard/madenat_guia_mass_update.py` + `_views.xml`

### Reportes:
- `custom_addons/madenat_lumber_core/reports/madenat_guia_report.xml`
- `custom_addons/madenat_lumber_core/reports/madenat_guia_report_templates.xml`

### Crons: NO detectados en data/ específicos para guías

---

## 4. ESTADO EN BASE DE DATOS

### ⚠️ NOTA: Docker no estaba disponible durante la auditoría

No se pudo ejecutar el bloque D (consultas SQL). Se requiere verificación manual con:

```sql
SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%guia%';
SELECT state, COUNT(*) FROM madenat_guia_processing GROUP BY state;
SELECT id, name, state, create_date FROM madenat_guia_processing ORDER BY create_date DESC LIMIT 10;
SELECT id, name, state FROM madenat_guia_processing WHERE state IN ('error', 'draft') LIMIT 20;
```

---

## 5. COBERTURA DE TESTS

### Tests existentes:
- `custom_addons/madenat_lumber_core/tests/test_lumber_reception.py` — 2572 líneas, cubre `LumberReceptionLine` y `LumberReception`

### Tests específicos para guías: NO EXISTE archivo dedicado
- No hay `test_*guia*.py` ni `test_*ingesta*.py` en todo `custom_addons`
- El flujo `madenat_guia_processing` **carece de tests unitarios propios**

### Tests faltantes identificados:
1. Creación de guía con tipo 'compra' y 'service'
2. Flujo completo: draft → verified → processed → validated
3. Parseo de Excel con diferentes formatos de columna
4. Parseo de PDF de guía de despacho
5. Cálculo de volúmenes nominales vs físicos
6. Creación de lotes con `_create_or_get_lot`
7. Motor unificado de picking (`_get_or_create_picking_unified`)
8. Validación con autorreparación de productos consumibles
9. Cancelación forzada con escudos logístico/financiero
10. Eliminación segura con limpieza de moves huérfanos
11. Integridad de la máquina de estados
12. Cálculo de diferencias (m³, MBF, %)

### Cobertura estimada: **BAJA** (0 tests específicos para el modelo)

---

## 6. DEUDA TÉCNICA IDENTIFICADA

### Prioridad ALTA
- **Campos duplicados con conflictos de API**: `vol_total_m3` (líneas 938 y 977), `vol_comercial` (líneas 958 y 909), `vol_fisico` (líneas 966 y 910) y `can_process` (líneas 906 y 927) se definen **dos veces** con diferentes `compute` y `store`. Solo la última definición gana en Odoo ORM → las primeras son código muerto que confunde. → `madenat_guia_processing.py:933-982`
- **CERO tests para el modelo**: 3465 líneas sin un solo test unitario. Riesgo de regresión máximo ante cualquier cambio. → `tests/` sin `test_guia*.py`

### Prioridad MEDIA
- **Método duplicado**: `_validar_y_enriquecer_lineas` definido en 2 lugares distintos (líneas 2297 y 2405). Solo la segunda definición tiene efecto. → `madenat_guia_processing.py:2297` y `:2405`
- **Método duplicado**: `_compute_vol_purchase_m3` en línea de staging definido en líneas 301 y 424 → `madenat_guia_processing.py:301` y `:424`
- **Parser en la cabecera vs AbstractModel**: `_parse_dispatch_pdf` y `_parse_packing_excel` están definidos en `MadenatGuiaProcessing` (3465 líneas) mientras que el parser canónico está en `MadenatReceptionParser` (AbstractModel separado). Hay lógica duplicada de parseo. → `madenat_guia_processing.py:1929-2110` vs `reception_parser.py`
- **Hardcode de mapa de dimensiones**: `LUMBER_DIMENSION_MAP` (línea 25-73) contiene hardcodes de espesores y anchos. Ya existe `lumber_blank_nominal_map.py` y `lumber_width_s2s_map.py` como modelos persistentes (Fase 2), pero el mapa persiste como diccionario Python en el archivo. → `madenat_guia_processing.py:25-73`
- **Múltiples importaciones duplicadas**: `import logging`, `from odoo import models`, `from odoo.exceptions import ValidationError` aparecen 2 veces en el mismo archivo (línea 13 y 84-87). → `madenat_guia_processing.py:13,84-87`

### Prioridad BAJA
- **Docstrings inconsistentes**: ~60% de métodos tienen docstring, 40% no. Algunos docstrings tienen emojis excesivos que no aportan valor técnico.
- **Uso inconsistente de `_logger`**: Algunas funciones usan `_logger` del scope global, otras redefinen `import logging; _logger = logging.getLogger(__name__)` localmente (ej: `_find_oc_reference_in_excel` línea 2474).
- **`_mm_a_pulgadas_frac`** (línea 2865) es un método trivial de 1 línea que podría estar en `utils_uom.py` en vez de en el modelo.
- **`service_unit_price_clp`** es `fields.Monetary` sin `currency_field` explícitamente definido (línea 865-868 usa `currency_field='currency_id'` pero el campo `currency_id` es Many2one a `res.currency`, no es un campo monetary. Posible bug semántico).

---

## 7. HALLAZGOS ESPECÍFICOS

### Patrón HF-001 (imports inválidos entre addons): **NO PRESENTE**
- Los 3 archivos auditados usan imports relativos (`from .utils_uom import ...`) o imports estándar de Odoo.
- Cero imports del tipo `from madenat_lumber_X import ...` entre addons.

### Hardcodes TD-004B: **MITIGADOS, NO ELIMINADOS**
- `MM_PER_INCH`, `M3_DIVISOR`, `MBF_DIVISOR`, `M_TO_FT`, `S2S_WIDTH_*`, `BLANK_CLEAR_*` → todos delegados a `utils_uom.py` desde donde se importan
- `LUMBER_DIMENSION_MAP` persiste como hardcode en `madenat_guia_processing.py:25-73`
- `reception_parser.py` tiene hardcodes de `_BLANKS_NOMINAL_MAP` (línea 17) y `_NOMINAL_TOLERANCE` (línea 26), aunque tiene fallback a modelos Fase 2

### TODOs/FIXMEs: **NINGUNO EXPLÍCITO**
- No hay `TODO`, `FIXME`, `HACK`, `XXX` marcados en los archivos auditados
- Hay documentación interna extensa con emojis y versionados, pero sin deuda marcada explícitamente

### Manejo de errores: **COMPLETO**
- `ValidationError` y `UserError` usados extensivamente con mensajes descriptivos en español
- `try/except` con `_logger.warning` en parseo de PDF (no bloqueante)
- `savepoint` para operaciones de borrado en `_cleanup_orphan_moves_guia`
- Validaciones preventivas en cada fase del state machine
- La mayoría de operaciones críticas usan `self.ensure_one()`

---

## 8. VEREDICTO PROFESIONAL

### Estado general del módulo: **Funcional con deuda**

El módulo implementa un flujo de negocio completo y sofisticado para la recepción de madera procesada. La arquitectura de staging → procesamiento → validación es sólida conceptualmente. El motor unificado de pickings y la cancelación segura muestran madurez en el manejo de integridad de datos.

Sin embargo, la deuda técnica es significativa:
- 3465 líneas en un solo archivo (demasiado grande)
- Campos duplicados que generan confusión y código muerto
- CERO tests unitarios (riesgo máximo de regresión)
- Lógica de parseo duplicada entre la cabecera y el AbstractModel
- Hardcodes que ya deberían estar migrados a modelos Fase 2

### Confianza para producción: **Media**
Funciona, pero cualquier modificación es de alto riesgo sin tests. Los campos duplicados pueden causar comportamientos inesperados si se modifica el orden de definición.

### Riesgo de regresión: **Alto**
Sin tests automatizados, cualquier refactor o fix puede romper el flujo de staging→lotes→picking→validación sin ser detectado hasta producción.

---

## 9. PRÓXIMOS TDs PROPUESTOS (solo propuesta, sin ejecutar)

### TD-007: Limpieza de campos duplicados en MadenatGuiaProcessing — PRIORIDAD ALTA
Eliminar las definiciones duplicadas de `vol_total_m3` (línea 938), `vol_comercial` (línea 958), `vol_fisico` (línea 966) y `can_process` (línea 906) que son código muerto. Consolidar en una sola definición por campo.
**Riesgo**: Bajo (son definiciones shadowed)
**Archivos**: `madenat_guia_processing.py`

### TD-008: Test suite para madenat_guia_processing — PRIORIDAD ALTA
Crear `tests/test_guia_processing.py` con cobertura mínima de:
- Creación de guías con distintos tipos
- Flujo completo de estados
- Procesamiento de staging → lotes
- Validación con picking
- Cancelación forzada
- Cálculo de volúmenes y diferencias
**Riesgo**: Nulo (solo agrega tests)
**Archivos**: `tests/test_guia_processing.py` (nuevo)

### TD-009: Migrar LUMBER_DIMENSION_MAP a modelos Fase 2 — PRIORIDAD MEDIA
Reemplazar el diccionario hardcodeado `LUMBER_DIMENSION_MAP` (líneas 25-73) por consultas a `lumber_blank_nominal_map` y `lumber_width_s2s_map`. Completar la migración iniciada en Fase 2.
**Riesgo**: Medio (cambio de fuente de datos)
**Archivos**: `madenat_guia_processing.py`, `lumber_blank_nominal_map.py`, `lumber_width_s2s_map.py`

### TD-010: Unificar parseo Excel/PDF en MadenatReceptionParser — PRIORIDAD MEDIA
Eliminar `_parse_dispatch_pdf` y `_parse_packing_excel` de `MadenatGuiaProcessing` y delegar completamente al AbstractModel `MadenatReceptionParser`. Reducir duplicación de lógica.
**Riesgo**: Medio (refactor de métodos core)
**Archivos**: `madenat_guia_processing.py`, `reception_parser.py`

### TD-011: Refactor modular — extraer MadenatGuiaProcessingLine a archivo propio — PRIORIDAD BAJA
Las 693 líneas de la clase de staging (líneas 1-782) pueden vivir en su propio archivo `madenat_guia_processing_line.py`, reduciendo el archivo principal a ~2700 líneas.
**Riesgo**: Bajo (solo mover código)
**Archivos**: `madenat_guia_processing.py`, nuevo `madenat_guia_processing_line.py`, `__init__.py`

---

*Informe generado el 2026-06-04 — Auditoría de solo lectura — CERO modificaciones de código*