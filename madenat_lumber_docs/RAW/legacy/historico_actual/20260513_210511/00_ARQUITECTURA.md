# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`
**Versión:** `18.0.5.0.0`
**Fecha auditoría:** 2026-05-08
**Estado:** AUDITORÍA COMPLETADA - Arquitectura modular operativa
**Tests:** ✅ 14 tests

---

## Propósito

Este módulo es el motor central de MADENAT para la ingesta de madera bruta y procesada, la validación documental y la generación de lotes contables. Agrupa el flujo de recepción nacional (`lumber.reception`) y la recepción de guías procesadas (`madenat.guia.processing`) con staging, validaciones, checklists y generación de stock/picking.

## Posición en la Cadena

```
madenat_lumber_shipping_core → [madenat_lumber_core] → madenat_lumber_logistics
```

## Modelos Definidos

### `lumber.reception.line`
**Archivo:** `models/lumber_reception.py`
**Descripción:** Línea de staging utilizada para validar y corregir datos de recepción antes de crear lotes definitivos.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `reception_id` | Many2one | Recepción padre | → `lumber.reception` |
| `lot_name` | Char | Identificador del lote/staging | — |
| `subproduct_id` | Many2one | Subproducto comercial | → `madenat.subproducto` |
| `product_name_clean` | Char | Nombre del producto limpio | → `product.product` (related) |
| `quality` | Selection | Calidad del producto | — |
| `export_calculation_rule` | Selection | Regla de cálculo de exportación | — |
| `thickness_nominal` | Float | Espesor nominal para costeo | — |
| `width_nominal` | Float | Ancho nominal para costeo | — |
| `thickness_visual` | Char | Espesor comercial/visual | — |
| `width_visual` | Char | Ancho comercial/visual | — |
| `vol_shipment_m3` | Float | Volumen físico para embarque | — |
| `vol_purchase_m3` | Float | Volumen nominal de compra | — |
| `pieces` | Integer | Piezas totales | — |
| `audit_snapshot` | Text | Snapshot JSON de auditoría | — |
| `audit_hash` | Char | SHA-256 del snapshot | — |

**Métodos de negocio:**
- `_sanitize_lot_name()` — normaliza la etiqueta del lote a formato fijo EAN-13.

### `lumber.reception`
**Archivo:** `models/lumber_reception.py`
**Descripción:** Cabecera del proceso de recepción de madera bruta, con estados, reglas de ingestión y controles de validación.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `reception_line_ids` | One2many | Líneas de staging | → `lumber.reception.line` |
| `state` | Selection | Estado del flujo de recepción | — |
| `ingestion_profile` | Selection | Perfil de cálculo de ingestión | — |
| `audit_snapshot` | Text | Snapshot JSON | — |
| `audit_hash` | Char | SHA-256 de validación | — |
| `can_process_reception` | Boolean | Flag de disponibilidad para procesar | — |
| `can_reopen_reception` | Boolean | Flag para reabrir | — |
| `can_cancel_reception` | Boolean | Flag para cancelar | — |
| `guia_numero` | Char | Número de guía | — |
| `guia_fecha` | Date | Fecha de guía | — |

**Métodos de negocio:**
- `_compute_can_process_reception()` — define si la recepción puede avanzar.
- `_compute_can_reopen_reception()` — controla reapertura de la recepción.
- `_compute_can_cancel_reception()` — controla cancelación segura.

### `madenat.guia.processing.line`
**Archivo:** `models/madenat_guia_processing.py`
**Descripción:** Línea de staging para recepción de guías procesadas y servicios de transformación.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `processing_id` | Many2one | Cabecera de guía procesada | → `madenat.guia.processing` |
| `lot_name` | Char | Identificador del lote | — |
| `product_id` | Many2one | Producto de madera | → `product.product` |
| `vol_shipment_m3` | Float | Volumen físico real | — |
| `vol_purchase_m3` | Float | Volumen de compra nominal | — |
| `pieces` | Integer | Piezas | — |
| `warning_msg` | Char | Mensaje de advertencia | — |

**Métodos de negocio:**
- `_compute_warning()` — detecta desviaciones entre volúmenes físicos y nominales.

### `madenat.guia.processing`
**Archivo:** `models/madenat_guia_processing.py`
**Descripción:** Cabecera del documento de guía procesada con workflow, attachments y datos de servicios.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `processing_line_ids` | One2many | Líneas de staging | → `madenat.guia.processing.line` |
| `tipo_recepcion` | Selection | Compra o servicio | — |
| `state` | Selection | Estado del documento | — |
| `date_emission` | Date | Fecha emisión | — |
| `partner_id` | Many2one | Proveedor/transportista | → `res.partner` |
| `order_id` | Many2one | Orden de compra | → `purchase.order` |
| `lot_ids` | Many2many | Lotes relacionados | → `stock.lot` |
| `assignment_location_id` | Many2one | Patio de asignación | → `stock.location` |
| `currency_id` | Many2one | Moneda | → `res.currency` |
| `rate_usd` | Float | Tipo de cambio USD | — |
| `pdf_attachment_id` | Many2one | PDF guía | → `ir.attachment` |
| `excel_attachment_id` | Many2one | Excel packing | → `ir.attachment` |
| `service_product_name` | Char | Descripción del servicio | — |
| `service_volume_m3` | Float | Volumen del servicio | — |

**Métodos de negocio:**
- `do_full_processing()` — ejecuta el procesamiento completo desde staging.
- `_create_stock_picking_from_guia()` — crea picking de transferencia de stock.
- `_parse_dispatch_pdf()` — parseo específico del PDF de despacho.
- `_parse_packing_excel()` — parseo del Excel de packing list.
- `_assert_ready_to_validate()` — valida condiciones previas a la aprobación.
- `action_process_from_staging()` — gatilla el paso de staging a inventario.
- `action_validate()` — valida el documento para su cierre.

### `validation.checklist.mixin`
**Archivo:** `models/validation_checklist_mixin.py`
**Descripción:** Mixin abstracto que provee checklist de validación técnica y estados de validación.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `validation_checklist_ids` | One2many | Items de validación | → `validation.checklist.item` |
| `validation_status` | Selection | Estado del checklist | — |
| `can_validate` | Boolean | Flag para validar | — |

**Métodos de negocio:**
- `action_run_validation_checklist()` — ejecuta serie de validaciones en orden.
- `_validate_uom_consistency()` — comprueba que la UoM sea m³.
- `_compute_validation_status()` — agrega el resultado del checklist.

### `validation.checklist.item`
**Archivo:** `models/validation_checklist_mixin.py`
**Descripción:** Item individual de checklist con estado y bloqueo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `reception_id` | Many2one | Recepción asociada | → `lumber.reception` |
| `guia_id` | Many2one | Guía procesada asociada | → `madenat.guia.processing` |
| `check_type` | Selection | Tipo de validación | — |
| `status` | Selection | Resultado de la validación | — |
| `is_blocking` | Boolean | Si bloquea el proceso | — |
| `message` | Char | Mensaje de resultado | — |

### `madenat.lumber.ingest.mixin`
**Archivo:** `models/mixin_lumber_ingest.py`
**Descripción:** Mixin abstracto para normalizar la ingestión de productos y la reparación automática de configuración.

**Métodos de negocio:**
- `validate_product_lumber_config()` — auto-repara `product.product` para uso de lotes.
- `find_or_create_lumber_product()` — identifica y crea productos de madera con configuración técnica.
- `_safe_float()` / `_safe_int()` — coerción segura de valores numéricos.

### `madenat.lumber.ingest.line.mixin`
**Archivo:** `models/mixin_lumber_ingest.py`
**Descripción:** Mixin abstracto para las líneas de ingestión de staging.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `lot_name` | Char | Identificador de lote | — |
| `product_id` | Many2one | Producto | → `product.product` |
| `vol_shipment_m3` | Float | Volumen físico | — |
| `vol_purchase_m3` | Float | Volumen nominal | — |
| `warning_msg` | Char | Mensaje de alerta | — |

### Wizard: `lumber.reception.mass.update`
**Archivo:** `wizard/lumber_reception_mass_update.py`
**Propósito:** Asignación masiva de nominales y subproducto para una recepción.
**Modelos que modifica:** `lumber.reception`

### Wizard: `madenat.guia.mass.update`
**Archivo:** `wizard/madenat_guia_mass_update.py`
**Propósito:** Actualización masiva de espesor nominal y subproducto sobre la guía procesada.
**Modelos que modifica:** `madenat.guia.processing`

## Modelos Heredados

### `stock.lot`
**Archivo:** `models/stock_lot.py`
**Campos añadidos:**
- `container_id` (Many2one) — contenedor actual del lote.
- `product_code_only` (Char) — código de producto separado para búsqueda.
- `product_name_only` (Char) — nombre de producto separado para búsqueda.
- `is_billed` (Boolean) — indica si el lote está facturado.
- `wood_cost_usd` / `purchase_cost_usd` / `total_cost_usd` — costo en USD.
- `lot_exchange_rate` (Float) — tipo de cambio aplicado al lote.

**Métodos de negocio:**
- `_compute_is_billed()` — marca lotes presentes en consolidaciones facturadas.
- `_compute_product_display()` — unifica cálculo de código y nombre del producto.

### `stock.quant`
**Archivo:** `models/stock_lot.py`
**Campos añadidos:**
- `reception_name` (Char) — número de guía de recepción relacionada.
- `reception_date` (Datetime) — fecha de guía.
- `supplier_id` (Many2one) — proveedor del lote.
- `volumen_sistema_m3` (Float) — volumen del quant igual a quantity.
- `subproducto_id` (Many2one) — subproducto del lote.
- `etiqueta_limpia` (Char) — etiqueta de lote limpia.

## Relaciones con otros módulos MADENAT

| Campo | Modelo origen | Módulo | Tipo relación |
|-------|--------------|--------|---------------|
| `reception_id` | `lumber.reception.line` | Este módulo | Many2one |
| `subproduct_id` | `lumber.reception.line` | Este módulo | Many2one → `madenat.subproducto` |
| `processing_id` | `madenat.guia.processing.line` | Este módulo | Many2one |
| `lot_ids` | `madenat.guia.processing` | Odoo Core | Many2many → `stock.lot` |
| `order_id` | `madenat.guia.processing` | Odoo Core | Many2one → `purchase.order` |
| `assignment_location_id` | `madenat.guia.processing` | Odoo Core | Many2one → `stock.location` |
| `currency_id` | `madenat.guia.processing` | Odoo Core | Many2one → `res.currency` |
| `product_id` | `madenat.guia.processing.line` | Odoo Core | Many2one → `product.product` |
| `validation_checklist_ids` | `validation.checklist.mixin` | Este módulo | One2many → `validation.checklist.item` |

## Seguridad

| Modelo | Usuario | Acceso |
|--------|---------|--------|
| `stock.lot` | `base.group_user` | R/W/C |
| `lumber.reception` | `base.group_user` | R/W/C |
| `lumber.reception` | `stock.group_stock_manager` | R/W/C/U |
| `stock.lot.cost.line` | `base.group_user` | R |
| `stock.lot.cost.line` | `stock.group_stock_manager` | CRUD |
| `madenat.subproducto` | `base.group_user` | R/W/C |
| `madenat.subproducto` | `stock.group_stock_manager` | CRUD |
| `madenat.audit.log` | `base.group_user` | R/C |
| `madenat.audit.log` | `base.group_system` | CRUD |
| `madenat.guia.processing` | `base.group_user` | R/W/C |
| `madenat.guia.processing` | `stock.group_stock_manager` | CRUD |
| `validation.checklist.item` | `base.group_user` | R/W/C |
| `validation.checklist.item` | `stock.group_stock_manager` | CRUD |
| `lumber.reception.line` | `base.group_user` | CRUD |
| `lumber.reception.line` | `stock.group_stock_manager` | CRUD |
| `lumber.reception.mass.update` | `base.group_user` | CRUD |
| `madenat.guia.processing.line` | `base.group_user` | CRUD |
| `madenat.guia.mass.update` | `base.group_user` | CRUD |

## Tests

### `tests/test_ingestion_gate.py` (16 tests)
- `test_excel_valido()` — Gate0 acepta Excel válido.
- `test_pdf_valido()` — Gate0 acepta PDF válido.
- `test_extension_incorrecta_excel()` — Gate0 rechaza extensión incorrecta para Excel.
- `test_extension_incorrecta_pdf()` — Gate0 rechaza extensión incorrecta para PDF.
- `test_archivo_vacio()` — Gate0 rechaza archivo vacío.
- `test_archivo_muy_grande()` — Gate0 rechaza archivos > 20 MB.
- `test_reconciliacion_ok()` — Gate1 valida Excel vs PDF correctamente.
- `test_nroguia_mismatch()` — Gate1 detecta mismatch entre número de guía Excel/PDF.
- `test_nroguia_duplicado_en_bd()` — Gate1 detecta guía duplicada en base de datos.
- `test_tipo_cambio_cero()` — Gate1 rechaza tipo de cambio cero.
- `test_tipo_cambio_fuera_de_rango_genera_warning()` — Gate1 genera warning para TC fuera de rango.
- `test_volumen_mismatch_bloquea()` — Gate1 rechaza volumen fuera de tolerancia.
- `test_volumen_dentro_tolerancia()` — Gate1 acepta volumen dentro de tolerancia.
- `test_oc_no_existe()` — Gate1 falla si OC no existe.
- `test_oc_cancelada_bloquea()` — Gate1 rechaza OC cancelada.
- `test_sin_oc_no_verifica_oc()` — Gate1 no verifica OC cuando no se provee.

### `tests/test_lumber_reception.py` (14 tests)
- `test_01_suma_m3_por_linea()` — verifica suma de m³ por línea y total de recepción.
- `test_02_suma_mbf_por_linea()` — valida cálculo MBF sobre línea con perfil `f5085`.
- `test_03_triple_capa_blanks()` — valida triple capa y cálculo nominal/real.
- `test_04_lot_name_deduplication()` — normaliza `lot_name` y elimina sufijos no deseados.
- `test_05_sanitize_lot_name()` — asegura normalización EAN-13 de `lot_name`.
- `test_06_volume_calculations()` — comprueba volúmenes físicos y nominales con datos reales.
- `test_07_width_mapping_table()` — valida la tabla de anchos convictos.
- `test_08_reception_service()` — prueba creación de lotes desde staging, con fallback cuando falta `lumber.billing.consolidation.line`.
- `test_09_validation_ranges()` — rechaza dimensiones inválidas con `ValidationError`.
- `test_10_gate_3_commit()` — verifica que Gate3 commit crea lotes y picking.
- `test_11_recall_lote_trazabilidad()` — valida trazabilidad de lote tras reapertura.
- `test_12_conciliacion_comercial_bodega()` — valida conciliación comercial/bodega.
- `test_13_standard_blanks_sin_contaminacion()` — asegura que blanks estándar no se mezclen con otras reglas.
- `test_14_edge_cases_volumen_nulo_bloquea()` — rechaza volumen nulo en escenarios límite.

## Deuda Técnica

| ID | Severidad | Descripción | Fix estimado |
|----|-----------|-------------|-------------|
| DT-NEW-LC-001 | 🔴 Crítica | `models/madenat_guia_processing.py` define `name = fields.Char(...)` dos veces en `madenat.guia.processing`, lo que crea una definición duplicada y puede ocultar el primer campo. | 30 min |
| DT-NEW-LC-002 | 🟡 Importante | `tests/test_lumber_reception.py` omite el test de creación de lotes cuando falta el modelo `lumber.billing.consolidation.line`, lo que indica dependencia de facturación no aislada en la suite de pruebas. | 45 min |

## Decisiones de Diseño

- **Separación de contextos:** `lumber.reception` y `madenat.guia.processing` funcionan como dos canales de ingestión separados, compartiendo mixins de validación y cálculo.
- **Staging obligatorio:** Todas las líneas pasan por staging antes de materializarse en `stock.lot`, lo que reduce los riesgos de corrupción de datos y permite feedback manual.
- **Mixins como Shared Kernel:** `madenat.lumber.ingest.mixin` y `validation.checklist.mixin` encapsulan política de validación reutilizable entre recepción y guías procesadas.
- **Validaciones por Gate:** El flujo usa gates documentales (Gate0/1/2/3) para separar validación sin escritura de la persistencia real.
- **No hay puente a billing en este módulo:** La facturación ocurre en otro módulo, por lo que el core mantiene su foco en recepción y staging.

---
*Auditado: 2026-05-08 | Próxima revisión: 2026-05-15*


## Nota 2026-05-13 - Perfiles de ingesta y largo

- La interpretación del campo largo en staging depende del perfil de ingesta.
- `metric`, `s2s`, `blanks`, `f1550` y `f5085` no deben tratarse como equivalentes.
- Cualquier cambio en unidades de largo debe nacer desde el mapeo de perfiles y fórmulas, no desde la UI.
- La convivencia `Standard Blanks` y otras reglas ya fue validada en tests y no debe contaminarse por refactors apresurados.

