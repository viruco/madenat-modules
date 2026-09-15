# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`
**Versión documental:** `7.7.0`
**Fecha de actualización:** 2026-09-12
**Estado:** ✅ Vigente — Se documenta el flujo de recepción a granel + Balance de Masa + consolidación administrativa (AD-65, diseño aprobado, pendiente de implementación) en §4.6. Sin cambios de código.
**Compatibilidad objetivo:** Odoo 18 CE

---

## 1. Propósito

Este módulo implementa el flujo operativo de MADENAT para:
- Ingesta de documentos (Excel, PDF) vía `lumber.reception` y `madenat.guia.processing`.
- Staging documental en `lumber.reception.line` antes de cualquier escritura en inventario.
- Análisis comercial, cálculo volumétrico y validación por gates (0–3 + GB-1).
- Persistencia controlada a `stock.lot` exclusivamente a través de Gate 3 (AD-04).

---

## 2. Posición funcional

El módulo no opera en un pipeline vertical estricto: actúa como **núcleo de ingesta y staging** que alimenta a los módulos de dominio.

- **Upstream:** `madenat_lumber_purchasing` extiende `purchase.order` y enriquece el contexto de compra.
- **Consumidores:** `madenat_lumber_logistics` (contenedores/embarques), `madenat_lumber_costing` (costeo), `madenat_lumber_billing` (facturación), `madenat_lumber_reports` (reportes).
- **Dependencia funcional documentada:** `madenat_lumber_shipping_core` define modelos de motonaves/viajes/reservas pero los menús los construye `madenat_lumber_logistics`. Si logistics no está instalado, shipping_core es invisible en la UI. `shipping_core/__manifest__.py` tiene `shipping_menus.xml` comentado con nota "ELIMINADO - Menús migrados a logistics". `shipping_core` no declara `depends` sobre `logistics` → dependencia funcional, no técnica. Documentado como riesgo M-R2 en `02_CONTINUIDAD.md` y formalizado en `04_DECISION_LOG.md` AD-37.

---

## 3. Estado real de la arquitectura

**Modular parcial.** Se han extraído componentes del monolito original pero `lumber_reception.py` (~3118 líneas) todavía concentra `LumberReceptionLine`, `LumberReception`, computes de staging y normalizaciones.

### 3.1 Archivos clave desacoplados

| Archivo | Responsabilidad |
|---|---|
| `ingestion_gate.py` | Gates 0–3: PreUpload, DocumentReconciliation, CommercialAnalysis, PreCommit |
| `reception_parser.py` | Dispatcher multi-formato (Excel por perfil, PDF, CSV) |
| `reception_service.py` | Escritura a `stock.lot` vía `LumberReceptionService._create_lots_from_packing()` |
| `reception_workflow.py` | Clase de orquestación de estados vía import inline (`from .reception_workflow import LumberReceptionWorkflow` en lumber_reception.py:2694). No es un mixin de herencia Odoo. |
| `validation_checklist_mixin.py` | Mixin de checklist de validación para líneas de ingesta |
| `mixin_lumber_ingest.py` | Mixin de cálculo volumétrico (regla de oro compartida) + `find_or_create_lumber_subproducto` (Fase 2) |
| `stock_lot.py` | Extensión de `stock.lot`: `vol_shipment_m3`, `_compute_estado_trazabilidad`, `_compute_processing_loss` |
| `stock_lot_cost_line.py` | Extensión de `stock.lot.cost.line` con cálculos de costeo |
| `stock_picking.py` | Extensión de `stock.picking` para recepciones de lumber |
| `stock_move.py` | Extensión de `stock.move` con trazabilidad de movimientos de lumber |
| `product_product.py` | Extensión de `product.product` con atributos comerciales de lumber |
| `utils_uom.py` | Constantes y conversiones volumétricas + utilidad de parseo de fracciones imperiales compartida (`parse_fraction_to_decimal_inch`, AD-41) |
| `width_mapping.py` | Tabla Rough→S2S + helper `get_s2s_adjustment()` |
| `core_utils.py` | ❌ CÓDIGO MUERTO — 0 referencias, fuera de `__init__.py` (confirmado 2026-07-08). No fue archivado por AD-39 (ese AD solo cubrió el método `_cleanup_orphan_moves`). |
| `product_template.py` | ❌ HUÉRFANO NO ARCHIVADO — extensión de `product.template` nunca desplegada, pendiente de mover a `_archive/` (confirmado 2026-07-08). |
| `madenat_ingestion_engine` (módulo hermano) | Motor de extracción/normalización de documentos de ingreso (Excel/PDF) agnóstico del destino. Consumido por `madenat_lumber_intake` (`extract_document()` para preview/perfil; `_extract_pdf_text()` para auto-clasificación Producto/Procesado). Estado verificado: `installed` en `madenat_test` (18.0.1.0.0). Gaps: extracción PDF solo cabecera por regex (tablas con layout configurable NO cubiertas); `ingestion_column_profile.py` es esqueleto de 4 campos sin layout. Ver AD-63. |

### 3.2 Modelos persistentes (Fase 2 + Fase 3 — AD-29, AD-30)

El runtime actual incluye modelos para reglas de ingesta parametrizables con UI de mantenimiento:

| Modelo | Propósito | AD |
|---|---|---|
| `lumber.blank.nominal.map` | Mapa físico→nominal blanks (8 registros) | AD-29 |
| `lumber.width.s2s.map` | Tabla Rough→S2S (15 registros) | AD-29 |
| `lumber.thickness.visual.rule` | Rangos espesor→visual (4 reglas) | AD-29 |
| `lumber.profile.subproduct.rule` | Reglas perfil↔subproducto (7 reglas) | AD-29 |
| `lumber.export.formula` | Fórmulas exportación por perfil (3 registros: f5085, f1550, metric) | AD-30 |
| `lumber.ingestion.format` | Formatos ingesta/parsing por perfil (4 registros) | AD-30 |
| `madenat.ingestion.config` | Helper AbstractModel con cadena de fallback de 3 niveles + `get_default_product()` | AD-29, AD-ING-001 |
| `madenat.lumber.product.default` | Producto maestro por tipo de ingreso (perfil/compañía) | AD-ING-001 |

### 3.3 Componente aún concentrado

`models/lumber_reception.py` mantiene:
- `LumberReceptionLine` (modelo de staging)
- `LumberReception` (cabecera)
- computes de staging (`_compute_volume_purchase`, `_compute_export_values`, `_compute_visual_defaults`, etc.)
- normalizaciones y comportamiento UI

**Conclusión arquitectónica:** el refactor estructural está avanzado y funcional, pero no está completada la separación total de línea/cabecera a archivos independientes.

**⚠️ PARSEO DISPERSO en `madenat_guia_processing.py`:** 9 métodos de extracción de datos sin dispatcher equivalente a `reception_parser.py` tras extracción de `_parse_fraction` (AD-41) (`_parse_dispatch_pdf` L2128, `_parse_packing_excel` L2445, `_parse_excel_data_core` L2524, `_find_oc_reference_in_excel` L2834, `_parse_float_value` L2639, `_get_nominal_dimension` L2678, entre otros). El archivo concentra ~4,330 líneas y 8 responsabilidades con parseo disperso, frente a `reception_parser.py` que está desacoplado como dispatcher dedicado. `_parse_fraction` ahora vive como `parse_fraction_to_decimal_inch` en `utils_uom.py` (función pura compartida). Esta asimetría no estaba documentada en versiones previas. Confirmado en auditoría 2026-07-08. Ver riesgo relacionado en `02_CONTINUIDAD.md` sección 5.

**Regla de diseño a preservar:** La lógica de negocio S2S vs Blank está correctamente aislada en `_compute_vol_shipment_m3` (L476-538, bifurcación en L510-516), separada del parseo. Cualquier intervención futura sobre los 9 métodos de parseo restantes NO debe tocar ni fusionar esta lógica.

---

## 4. Modelos funcionales

### 4.1 `lumber.reception.line`

Modelo de staging (`_name = 'lumber.reception.line'`, `_inherit = ['madenat.lumber.ingest.line.mixin']`).

**Propósito:** Reflejar la información cargada desde documentos antes de Gate 3. Preservar triple capa (visual, física, nominal). Superficie de corrección operativa previa a stock. Base para cálculos volumétricos.

**Campos funcionales (verificados contra código):**
- `reception_id` — Many2one → `lumber.reception`, cascade delete
- `lot_name` — Char, requerido
- `product_id` — Many2one → `product.product`
- `subproduct_id` — Many2one → `madenat.subproducto`
- `product_code`, `product_name` — Char
- `pieces` — Integer
- `thickness_visual`, `width_visual` — Char (representación imperial: "6/4", "5 5/8")
- `thickness_nominal`, `width_nominal` — Float (mm)
- `length` — Float (metros, fuente de verdad para cálculos volumétricos)
- `length_input_raw` — Float (valor crudo digitado por operador en la unidad `lengthuom`)
- `lengthuom` — Selection: `m` / `mm` / `ft`
- `vol_physical_m3` — Float, compute/store
- `vol_purchase_m3` — Float, compute/store, inverse habilitado (editable en staging)
- `vol_shipment_m3` — Float, compute/store (volumen de exportación)
- `vol_mbf` — Float, compute/store
- `export_calculation_rule` — Char
- `audit_snapshot` — Text, readonly, copy=False (JSON inmutable generado por Gate3)
- `audit_hash` — Char, SHA-256, readonly, copy=False

**Política de largo (AD-12 a AD-17):**
- `length` = valor normalizado en metros. Base de todo cálculo volumétrico.
- `length_input_raw` = valor de entrada del operador (preservado sin modificar).
- `lengthuom` = unidad de entrada. Desacoplada del perfil de ingesta (AD-14).
- Normalización: `_compute_lengthm` → `@api.depends('length_input_raw', 'lengthuom', 'length')`.
- Conversión: ft → `raw * FT_TO_M`, mm → `raw * 0.001`, m → valor directo.
- El naming correcto es `length_input_raw` (con underscores), consistente con el código.

### 4.2 `lumber.reception`

Cabecera del flujo (`_name = 'lumber.reception'`).

**Responsabilidades:** Gestionar estado del proceso, orquestar gates y transiciones, centralizar recepción documental, controlar cuándo una recepción puede procesarse/reabrirse/cancelarse, vincular staging → snapshot → inventario.

**Campos relevantes:**
- `reception_line_ids` — One2many → `lumber.reception.line`
- `state` — Selection: draft / processing / verified / done / cancel / error / pending_link
- `ingestion_profile` — Selection: f5085 / f1550 / metric (nota: `blanks_clear` es el rótulo semántico del flujo Blank; el valor real del selector es `f5085`. Diagnóstico 2026-08-15.)
- `audit_snapshot`, `audit_hash`
- `can_process_reception`, `can_reopen_reception`, `can_cancel_reception` (compute desde `reception_workflow.py`)
- `guia_numero` (Char), `guia_fecha` (Date)
- `supplier_id` — Many2one → `res.partner`
- `order_id` / `purchase_id` — Many2one → `purchase.order`
- `oc_reference_raw` — Char (readonly, copy=False): referencia documental de OC extraída de la Guía/PDF. Nunca se sobrescribe al vincular una `purchase.order`.
- `oc_reference_norm` — Char (compute, store): clave normalizada para matching (`parser.normalize_po_key`).
- `oc_match_status` — Selection: `not_found` / `single_match` / `multi_match` / `manual` / `created`. Estado de resolución de OC.
- `oc_match_note` — Text: bitácora de reconciliación de OC.
- `po_missing_alert` — Html (compute, sanitize=False): alerta visual de OC ausente o con referencia manual, NO bloqueante.

**Métodos arquitectónicos clave:**
- `action_confirm_reception()` → GB-1 → Gate2 → Gate3 → `LumberReceptionService._create_lots_from_packing()`.
- `action_reopen_to_draft()` → revierte estado preservando lotes en BD y desvinculando pickings.

### 4.3 `madenat.guia.processing`

Flujo complementario para guías procesadas. Modelos:
- `madenat.guia.processing` (cabecera)
- `madenat.guia.processing.line` (líneas)

Métodos: `do_full_processing()`, `action_validate()`, `_create_or_get_lot()`.

### 4.4 `stock.lot` extendido (`StockLotExtended` en `stock_lot.py`)

Extensión post-Gate3 de `stock.lot`. Campos y computes:
- `vol_shipment_m3` — Volumen de embarque con bifurcación blanks vs S2S (AD-27).
- `volume_purchase_m3` — Volumen nominal de compra.
- `_compute_estado_trazabilidad()` — Batch query de trazabilidad.
- `_compute_processing_loss()` — Pérdida entre compra y embarque.

### 4.5 Contrato Producto Maestro / Subproducto (AD-ING-001, AD-ING-002)

**Producto maestro** (`madenat.lumber.product.default`):
- Configuración persistente que resuelve `product_id` por tipo de ingreso (`bruta`/`procesado`), refinable por perfil y compañía.
- Único punto de resolución: `madenat.ingestion.config.get_default_product(tipo_ingreso, profile=None)`.
- El producto maestro **no** se deriva del texto del Excel ni se hardcodea en Python.

**Subproducto** (desde el Excel):
- La columna `Producto`/`Descripción`/`Especie`/`Subproducto` se asigna a:
  - Procesado: `subproducto_id` (`madenat.guia.processing.line`);
  - Bruta: `subproduct_id` (`lumber.reception.line`).
- Si no existe, se **autocrea** en `madenat.subproducto` (`find_or_create_lumber_subproducto`).
- Trazabilidad del texto original: `product_name_original` (Procesado) / `excel_product_name` (Bruta).

### 4.6 Recepción a Granel + Balance de Masa + Consolidación Administrativa (AD-65 — diseño aprobado, pendiente de implementación)

Flujo de diseño aprobado (no implementado) para madera que llega por **volumen total** a un patio sin desglose de piezas, destinada a procesamiento externo:

- **Extracción (AD-63/AD-65):** un único motor (extensión de `madenat_ingestion_engine`) degrada en cascada: tabla PDF de columnas fijas configurables → subtotales por grupo → total de encabezado (mínimo garantizado). Nunca bloquea; genera `ingestion_document_warning` no bloqueante.
- **Patio:** `stock.location` nativo (`location_id` en `lumber.reception`); se crea bajo demanda, nunca se elimina con stock. Sin modelo propio.
- **Envío a proceso (Balance de Masa, ISO 22095):** se resta una **cantidad** del pool de volumen del patio (no un lote completo) y el retorno se registra como stock nuevo independiente, **sin** genealogía `parent_lot_id`/`child_lot_ids` (alineado con DEC-002). Requiere extender `_get_or_create_consumption_picking` para consumo parcial (gap AD-64).
- **Consolidación administrativa:** manual y opcional; granularidad adaptativa (etiqueta/paquete/volumen) con volumen como denominador común. Complementa, no reemplaza, los discriminadores `reception_id`/`guia_processing_id` (ver `12_FLUJOS_INGESTA.md` §11).
- **Prohibición normativa:** no se valida correspondencia de detalle entre envío y retorno; la relación es balance agregado (texto íntegro en AD-65 §1.7).
- **Costeo:** fuera de esta etapa; el valor se entrega a Costeo/Auditoría.
- **Reporte de conciliación:** extensión de `madenat_lumber_reports`, informativo, factor de rendimiento configurable; uso exclusivo de Auditoría.

**Nominales:**
- Procesado: `espesor_mm` se usa como fallback de `espesor_nominal_mm` cuando el Excel no informa nominal.
- Bruta: conserva los defaults existentes desde dimensiones físicas. No hay lookup automático de ancho.

**Volúmenes (presentación):**
- `Volumen total (m³)` = Σ `vol_shipment_m3`.
- `Volumen stock (m³)` = Σ `vol_purchase_m3`.
- Toda salida volumétrica usa 3 decimales; no se muestran totales numéricos sin etiqueta.

**Separación de responsabilidades:**
- Core: configuración, mapeo y creación de catálogos.
- Intake: fachada, revisión operativa y presentación.
- Sin cambios en BT-04, Toll, `action_validate` e `intake_direct_stock`.
- La hipótesis de una ingesta unificada queda como investigación futura, fuera de alcance.

---

## 5. Gates y política de side effects

El sistema opera bajo 4 gates formales (`ingestion_gate.py`) + 1 guardia inline:

1. **Gate 0 — PreUpload** (`Gate0PreUpload`): Validación temprana de archivos (tipo, tamaño ≤20MB, estructura). Sin efectos en BD.
2. **Gate 1 — DocumentReconciliation** (`Gate1DocumentReconciliation`): Conciliación de líneas de packing vs guía. Sin efectos en BD.
3. **Gate 2 — CommercialAnalysis** (`Gate2CommercialAnalysis`): Análisis de nominales, tolerancias y reglas comerciales. Sin efectos en BD.
4. **GB-1** (inline en `action_confirm_reception()`): Guardia pre-Gate3 que verifica staging completo antes de permitir el commit.
5. **Gate 3 — PreCommit** (`Gate3PreCommit`): Notario criptográfico. Genera `audit_snapshot` (JSON) + `audit_hash` (SHA-256). **Único punto autorizado de escritura en inventario** (AD-04).

**Regla operativa:** Gates 0–2 + GB-1 son sin efectos en stock. Gate 3 es el único write autorizado a `stock.lot` y `stock.move`.

---

## 6. Wizards

- `lumber.reception.mass.update` — Asignación masiva de espesores/anchos/subproductos. Lee reglas desde `madenat.ingestion.config`.
- `madenat.guia.mass.update` — Ídem para guías de procesamiento.
- `madenat.period.close` — Cierre de período (staging, pendiente validación completa).

---

## 7. Criterio de alineación documental

Este documento se rige por la jerarquía de verdad definida en `INDICE_DOCUMENTACION.md` sección 8:
1. Documento canónico del tema en `CANON/`.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Código fuente (verdad funcional).

Si el código cambia en: layout de largo, campos de staging, gates, modularización, modelos Fase 2/3, o política de side effects, este archivo debe actualizarse en la misma sesión (AD-25).

---

## 8. Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 7.1.0 | 2026-06-30 | Auditoría documental. Consolidación post-limpieza. |
| 7.2.0 | 2026-07-01 | Validación cruzada contra código. Corrección de naming (`length_input_raw`), gates reales (0–3 + GB-1), modelos Fase 2/3 agregados, `stock_lot.py` y `ingestion_gate.py` documentados, wizards listados, cadena funcional ajustada a grafo horizontal. |
| 7.3.0 | 2026-07-08 | Corrección de vigencia post-auditoría: `core_utils.py` y `product_template.py` marcados como huérfanos/muertos, archivos faltantes agregados a tabla 3.1 (`validation_checklist_mixin`, `stock_lot_cost_line`, `stock_picking`, `stock_move`, `product_product`), parseo disperso de `madenat_guia_processing.py` documentado en sección 3.3. Sin cambios de código. |
| 7.5.0 | 2026-08-19 | Alineación con código: estados reales de `lumber.reception` (`draft/processing/verified/done/cancel/error/pending_link`) y campos canónicos de OC documentados en §4.2 (`oc_reference_raw`, `oc_reference_norm`, `oc_match_status`, `oc_match_note`, `po_missing_alert`). Sin cambios de código. |
| 7.6.0 | 2026-09-12 | Se documenta `madenat_ingestion_engine` (módulo consumido por `madenat_lumber_intake`) en §3.1: estado real verificado (`installed` 18.0.1.0.0) y gaps (extracción PDF de tablas no cubierta; perfil de columnas esqueleto). Sin cambios de código. |
| 7.7.0 | 2026-09-12 | Se documenta el flujo de recepción a granel + Balance de Masa + consolidación administrativa (AD-65, diseño aprobado, pendiente de implementación) en §4.6. Sin cambios de código. |
