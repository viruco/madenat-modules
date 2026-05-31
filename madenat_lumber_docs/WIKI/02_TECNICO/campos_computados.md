# Campos Computados — @api.depends en MADENAT

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Listar y documentar los campos computados (`@api.depends`) verificados en los módulos MADENAT, su lógica de cálculo y las dependencias que activan su recálculo.

---

## Contexto

Los campos computados son puntos críticos de rendimiento. Un `@api.depends` mal configurado causa recálculos innecesarios o valores stale. Este registro solo incluye campos verificados en el código fuente.

---

## stock.lot (extendido) — stock_lot.py

### Identidad del producto

| Campo | Depende de | Lógica |
|---|---|---|
| `product_code_only` | `product_id.default_code`, `product_id.name` | Extrae código del producto (ej: "2X4") |
| `product_name_only` | `product_id.default_code`, `product_id.name` | Extrae nombre sin código (ej: "Pino Oregón 2x4\" - 3.66m") |

### Clasificación y origen

| Campo | Depende de | Lógica |
|---|---|---|
| `reception_type` | `reception_id`, `guia_processing_id` | `'raw'` si viene de recepción, `'processed'` si viene de guía de procesamiento |
| `escuadria` | `espesor_inch_frac`, `ancho_inch_frac`, `largo_ft_frac` | Formato "1 1/4 x 4 x 10'" desde fracciones |
| `generation_level` | `parent_lot_id`, `parent_lot_id.generation_level` | 0 = original, 1 = primera transformación, etc. (recursive) |

### Volumen de embarque

| Campo | Depende de | Lógica |
|---|---|---|
| `vol_shipment_m3` | `product_id.use_commercial_standard`, `product_id.commercial_thickness_mm`, `product_id.commercial_width_mm`, `product_id.commercial_length_m`, `espesor_mm`, `ancho_mm`, `largo_m`, `largo_ft_frac`, `piezas`, `reception_id`, `volume_purchase_m3`, `volumen_m3` | Regla de Oro: volumen comercial con Factor 1550/5085 + recargo S2S. Si reception_id y vol > 0, preserva dato original |
| `volumen_m3` | `volume_purchase_m3`, `vol_shipment_m3`, `espesor_mm`, `ancho_mm`, `largo_m`, `piezas`, `espesor_inch_frac`, `ancho_inch_frac`, `largo_ft_frac` | Jerarquía: volume_purchase_m3 → cálculo métrico → fallback 0. Respeta asignación manual |
| `volumen_mbf` | `volumen_m3` (indirecto) | `volumen_m3 / 2.36` o cálculo desde fracciones si no hay métricas |

### Métricas y dimensiones

| Campo | Depende de | Lógica |
|---|---|---|
| `metric_dimensions` (inverse) | `espesor_inch_frac`, `ancho_inch_frac`, `largo_ft_frac` | Convierte fracciones a mm/m: fracción → decimal → × 25.4 (mm) o × 0.3048 (m) |

### Estado y trazabilidad

| Campo | Depende de | Lógica |
|---|---|---|
| `estado_trazabilidad` | `reception_id`, `parent_lot_id`, `guia_processing_id`, `subproducto_id` | `'recepcionado'` → `'en_patio'` → `'procesado'` → `'consolidado'` → `'embarcado'` |
| `processing_loss_pct` | `volume_purchase_m3`, `vol_shipment_m3` | `(compra - embarque) / compra × 100` |

### Valorización

| Campo | Depende de | Lógica |
|---|---|---|
| `purchase_amount_usd` | `volumen_m3`, `purchase_price_usd_per_m3` | `volumen_m3 × precio_unitario` |
| `purchase_amount_clp` | `purchase_amount_usd`, `purchase_exchange_rate` | `usd × tipo_cambio` |
| `sale_amount_usd` | `volumen_mbf`, `sale_price_usd_per_mbf` | `volumen_mbf × precio_venta` |
| `margin_usd` | `sale_amount_usd`, `cost_line_ids.amount_usd` | `venta - costo_total` |
| `margin_percent` | `margin_usd`, `sale_amount_usd` | `margen / venta × 100` |
| `cost_per_m3_usd` | `cost_line_ids.amount_usd`, `volumen_m3` | `costo_total / volumen_m3` |
| `cost_per_mbf_usd` | `cost_line_ids.amount_usd`, `volumen_mbf` | `costo_total / volumen_mbf` |
| `total_cost_usd` | `wood_cost_usd`, `purchase_cost_usd`, `cost_line_ids.amount_usd` | `base_cost + lines_cost` |

### Facturación

| Campo | Depende de | Lógica |
|---|---|---|
| `is_billed` | `name` (dummy) | Busca en `lumber.billing.consolidation.line` si el lote está en una consolidación con estado `'billed'` |

---

## lumber.reception — lumber_reception.py

### Volúmenes y totales

| Método | Depende de | Computa |
|---|---|---|
| `_compute_totals` | `reception_line_ids`, `reception_line_ids.vol_purchase_m3`, `reception_line_ids.vol_physical_m3`, `reception_line_ids.vol_mbf` | `physical_volume_m3`, `commercial_volume_m3`, `total_volume_m3`, `total_packages`, `total_volume_mbf` |
| `_compute_volume_variance` | `commercial_volume_m3`, `physical_volume_m3` | `volume_variance_percent` (4 decimales, `r4`), `volume_variance_m3` (3 decimales, `r3`) |
| `_compute_tolerance_status` | `volume_variance_percent` | `tolerance_status`: `ok` (≤2%), `warning` (≤10%), `critical` (>10%) |

### Valorización

| Método | Depende de | Computa |
|---|---|---|
| `_compute_commercial_mbf_from_m3` | `commercial_volume_m3` | `commercial_volume_mbf` (`m3 / 2.36`) |
| `_compute_usd_amount` | `total_amount_clp`, `exchange_rate` | `total_amount_usd` (`clp / exchange_rate`, requiere TC > 0) |
| `_compute_unit_prices` | `total_amount_usd`, `physical_volume_m3`, `physical_volume_mbf` | `price_per_m3_usd`, `price_per_mbf_usd` |
| `_compute_average_price_clp` | `total_amount_clp`, `commercial_volume_m3` | `average_price_m3` (`total_clp / vol_comercial`) |

### Archivos y flags operativos

| Método | Depende de | Computa |
|---|---|---|
| `_compute_files_ready` | `pdf_file`, `excel_file`, `purchase_id`, `oc_pdf_file` | `files_ready`: si hay OC → solo PDF+Excel; si no hay OC → requiere también OC PDF |
| `_compute_can_process_reception` | `state`, `files_ready` | `can_process_reception`: `state == 'draft'` AND `files_ready` |
| `_compute_can_reopen_reception` | `state`, `lot_ids` | `can_reopen_reception`: `state in ('validated', 'done')` AND no hay lotes |
| `_compute_can_cancel_reception` | `state` | `can_cancel_reception`: `state in ('draft', 'processing')` |

### UI y alertas

| Método | Depende de | Computa |
|---|---|---|
| `_compute_reception_summary` | `lot_ids` | `reception_summary_html`: tabla HTML agrupada por dimensión comercial (espesor visual, ancho visual, largo) |
| `_compute_po_missing_alert` | `purchase_id`, `manual_po_name`, `state` | `po_missing_alert`: HTML de alerta si falta OC vinculada (2 niveles: referencia manual vs sin referencia) |

### Auditoría y display

| Método | Depende de | Computa |
|---|---|---|
| `_compute_omitted_count` | `audit_log_ids` | `omitted_count`: conteo de logs con `action_type == 'omission'` |
| `_compute_purchase_order_display` | `purchase_id`, `manual_po_name` | `purchase_order`: muestra `purchase_id.name` si existe, sino `manual_po_name` o 'SIN ORDEN' |

---

## lumber.reception.line — lumber_reception.py

| Campo | Depende de | Lógica |
|---|---|---|
| `lengthm` | `length_input_raw`, `lengthuom`, `length` | Conversión a metros: ft→×0.3048, mm→×0.001, m→×1.0 |
| `vol_physical_m3` | `thickness`, `width`, `length`, `pieces` | Fórmula métrica: `(mm × mm × m × pzas) / 1.000.000` |
| `vol_physical_real_m3` | `thickness`, `width`, `length`, `pieces`, `reception_id.ingestion_profile` | Cálculo físico con switch por perfil (f5085 convierte pies a metros) |
| `vol_purchase_m3` | `thickness_nominal`, `width_nominal`, `length_nominal`, `thickness`, `width`, `length`, `pieces`, `reception_id.ingestion_profile`, `vol_shipment_m3` | Volumen comercial: nominal manda, físico respalda. Escalado proporcional para Blanks |
| `vol_shipment_m3` | `thickness_visual`, `width_visual`, `length`, `pieces`, `export_calculation_rule`, `thickness`, `width` | Factor 5085 (Blanks) / Factor 1550 (S2S) / Métrico puro |
| `vol_mbf` | `thickness_visual`, `width_visual`, `length`, `pieces`, `export_calculation_rule` | `(t" × w" × l' × pzas) / 12000` |
| `board_feet` | `vol_mbf` | `vol_mbf × 1000` |
| `cost_clp_unit` | `reception_id.total_amount_clp`, `reception_id.commercial_volume_m3`, `vol_purchase_m3` | Prorrateo: `(total_clp / vol_comercial) × vol_linea` |
| `product_name_clean` | `product_id`, `product_id.name` | Nombre limpio del producto |

---

## madenat.guia.processing.line — madenat_guia_processing.py

| Campo | Depende de | Lógica |
|---|---|---|
| `vol_physical_m3` | `espesor_mm`, `ancho_mm`, `largo_m`, `pieces` | Fórmula métrica pura: `(mm × mm × m × pzas) / 1.000.000` |
| `vol_purchase_m3` | `espesor_nominal_mm`, `espesor_mm`, `ancho_nominal_mm`, `ancho_mm`, `largo_nominal_m`, `largo_m`, `pieces` | Volumen de compra: nominal manda, físico respalda |
| `vol_mbf` | `thickness_visual`, `width_visual`, `length_ft`, `pieces`, `espesor_nominal_mm`, `ancho_nominal_mm`, `largo_nominal_m`, `espesor_mm`, `ancho_mm`, `largo_m` | MBF desde visual: `(t" × w" × l' × pzas) / 12000`. Fallback desde mm si no hay visual |
| `vol_shipment_m3` | `thickness_visual`, `width_visual`, `length_ft`, `pieces`, `largo_m`, `largo_nominal_m`, `vol_purchase_m3` | Factor 5085 (pies) o Factor 1550 (metros). Blindaje: si falla cálculo, usa `vol_purchase_m3` |
| `thickness_visual` | `espesor_nominal_mm`, `espesor_mm` | Conversión mm → fracción visual (ej: "6/4"). Usa `LUMBER_DIMENSION_MAP` con tolerancia ±3mm |
| `width_visual` | `ancho_nominal_mm`, `ancho_mm` | Conversión mm → fracción visual (ej: "5 3/8"). Usa `LUMBER_DIMENSION_MAP` con tolerancia ±2mm |
| `length_ft` | `largo_m`, `largo_nominal_m` | `largo_m × 3.28084` |
| `default_width` (precompute) | `ancho_mm` | Pre-llena `ancho_nominal_mm` desde `ancho_mm` si está en 0 |
| `default_length` (precompute) | `largo_m` | Pre-llena `largo_nominal_m` desde `largo_m` si está en 0 |

---

## Restricciones conocidas

- Los campos `store=True` persisten en base de datos y se recalculan solo cuando cambian sus dependencias.
- Los campos sin `store=True` (como `total_cost_usd`, `is_billed`) se recalculan en cada lectura.
- `vol_shipment_m3` en `stock.lot` preserva el valor original si `reception_id` existe y el volumen ya es > 0.001 (protección contra sobreescritura).
- `volumen_m3` en `stock.lot` respeta asignación manual: si ya tiene un valor > 0, no lo recalcula.
- `_inverse_metric_dimensions` y `_inverse_length_ft` son métodos `inverse` vacíos (`pass`) que permiten edición manual sin que el `compute` sobrescriba.
- `madenat.guia.processing.line._compute_vol_shipment_m3` tiene blindaje: si el cálculo geométrico falla o faltan datos visuales, rescata `vol_purchase_m3` como fallback.

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/models/stock_lot.py`
- Archivo: `custom_addons/madenat_lumber_core/models/lumber_reception.py`
- Archivo: `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[modelo_lotes]]
- [[modelo_recepciones]]
- [[herencia_odoo_modelos]]
- [[00_ARQUITECTURA]]
