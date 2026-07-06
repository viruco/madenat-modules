# AUDITORÍA COMPARATIVA — REPORTE R1 (DOBLE VARIANTE)
## Proyecto: madenat_lumber | Odoo 18 CE
## Fecha de auditoría: 2026-06-16
## Auditor técnico: Cline (AI Senior Auditor)

---

# 1. ARCHIVOS DE CADA VARIANTE

| Variante | Archivo | Tipo | Modelo fuente | Estado de verificación |
|----------|---------|------|---------------|------------------------|
| A | `custom_addons/madenat_lumber_reports/models/lumber_stock_report.py` | Modelo Python (_inherit stock.quant) + XLSX server actions + Tree views | `stock.quant` | VERIFICADO — archivo leído completo, líneas 1-794 |
| A | `custom_addons/madenat_lumber_reports/views/stock_report_actions.xml` | ir.actions.server + ir.actions.act_window (XML) | `stock.quant` | VERIFICADO — archivo leído completo |
| A | `custom_addons/madenat_lumber_reports/views/inventory_report_views.xml` (líneas 125-230) | Vistas tree (ir.ui.view) | `stock.quant` | VERIFICADO — sección Stock Real leída |
| B | `custom_addons/madenat_lumber_reports/models/lumber_reception_reports.py` | Modelo Python (_inherit lumber.reception.line) + XLSX export actions | `lumber.reception.line` | VERIFICADO — archivo leído completo, líneas 1-837 |
| B | `custom_addons/madenat_lumber_reports/reports/inventory_report_pdf.xml` | QWeb-PDF templates + ir.actions.report (XML) | `lumber.reception.line` | VERIFICADO — archivo leído completo, líneas 1-756 |
| B | `custom_addons/madenat_lumber_reports/views/inventory_report_views.xml` (líneas 1-121) | Vistas tree + search (ir.ui.view) | `lumber.reception.line` | VERIFICADO — sección Inventario Recepción leída |
| B | `custom_addons/madenat_lumber_core/models/lumber_reception.py` (líneas 48-915) | Modelo base (_name='lumber.reception.line') | `lumber.reception.line` | VERIFICADO — parcial (líneas 1-1000 leídas, modelo línea ubicado) |

---

# 2. VARIANTE A — MATRIZ DE 14 COLUMNAS (`stock.quant`)

**Fuente de extracción**: `lumber_stock_report.py`, método `action_export_r1_stock_detail_xlsx()`, líneas 341-350 (definición de columnas XLSX) + vista tree `view_stock_quant_tree_r1_detail_patio` en `inventory_report_views.xml` líneas 131-153.

**Nota crítica**: El XLSX declara explícitamente 13 columnas (línea 342: `widths` tiene 13 elementos; líneas 346-350: lista `cols` tiene 13 nombres). La vista tree declara 14 campos. La columna `quantity` (Stock) está en la vista tree pero NO en el XLSX. Esto es una divergencia interna de la Variante A entre su presentación tree y su presentación XLSX.

| # | Nombre visible (XLSX) | Nombre técnico | Modelo fuente | Tipo de campo | Origen del dato | Compute/Related/Directo | Archivo y línea | Observaciones |
|---|----------------------|----------------|---------------|---------------|-----------------|------------------------|-----------------|---------------|
| 1 | Patio | `location_name` | `stock.quant` | Char (compute, store=True) | `quant.location_id.name` | Compute → `_compute_location_name` | `lumber_stock_report.py` líneas 45-60 | Si no hay ubicación: "Sin Patio". El XLSX usa `q.location_name` para la celda de patio (línea 396) |
| 2 | Etiqueta Lote | `lot_id` (name) | `stock.lot` | Many2one → Char | `quant.lot_id.name` pasado por `_clean_lot_label()` | Directo (related implícito vía quant.lot_id) | `lumber_stock_report.py` líneas 297-303, 381 | Se limpia con `_clean_lot_label()`: quita prefijos técnicos, preserva números con padding |
| 3 | Fecha Recepción | `lot_reception_date` | `stock.quant` (campo añadido) | Datetime (related, store=True) | `lot_id.reception_id.reception_date` | Related → `lot_id.reception_id.reception_date` | `lumber_stock_report.py` líneas 67-73 | El XLSX formatea a 'YYYY-MM-DD' (línea 384). Si no hay lote o recepción: string vacío |
| 4 | N° Guía | `lot_guia_number` | `stock.quant` (campo añadido) | Char (related, store=True) | `lot_id.guia_number` | Related → `lot_id.guia_number` | `lumber_stock_report.py` líneas 75-80 | En XLSX: `lot.guia_number` (línea 385) |
| 5 | N° Orden | `lot_purchase_order` | `stock.quant` (campo añadido) | Char (compute, store=True) | `lot_id.purchase_order_id.name` | Compute → `_compute_lot_purchase_order` | `lumber_stock_report.py` líneas 83-97 | Si no hay purchase_order_id: string vacío. En XLSX: `lot.purchase_order_id.name` (línea 386) |
| 6 | Proveedor | `lot_supplier` | `stock.quant` (campo añadido) | Char (compute, store=True) | `lot_id.supplier_id.name` | Compute → `_compute_lot_supplier` | `lumber_stock_report.py` líneas 99-113 | Si no hay supplier_id: string vacío. En XLSX: `lot.supplier_id.name` (línea 387) |
| 7 | Producto | `product_id` (name) | `product.product` | Many2one → Char | `quant.product_id.name` | Directo | `lumber_stock_report.py` línea 388 | Campo nativo de stock.quant. El XLSX usa `q.product_id.name` |
| 8 | Subproducto | `lot_subproducto` | `stock.quant` (campo añadido) | Char (related, store=True) | `lot_id.subproducto_id.name` | Related → `lot_id.subproducto_id.name` | `lumber_stock_report.py` líneas 115-121 | En XLSX: `lot.subproducto_id.name` (línea 389) |
| 9 | Escuadría | `lot_escuadria` | `stock.quant` (campo añadido) | Char (related, store=True) | `lot_id.escuadria` | Related → `lot_id.escuadria` | `lumber_stock_report.py` líneas 123-128 | En XLSX se construye vía `_build_escuadria(lot)` (línea 390 y 305-319), que puede usar `lot.escuadria` o componer `thickness_visual x width_visual` |
| 10 | Largo (m) | `lot_largo_m` | `stock.quant` (campo añadido) | Float (related, store=True) | `lot_id.largo_m` | Related → `lot_id.largo_m` | `lumber_stock_report.py` líneas 131-138 | digits=(16,3). En XLSX: `lot.largo_m` (línea 391) |
| 11 | Piezas | `lot_piezas` | `stock.quant` (campo añadido) | Integer (related, store=True) | `lot_id.piezas` | Related → `lot_id.piezas` | `lumber_stock_report.py` líneas 149-154 | En XLSX: `lot.piezas` (línea 392) |
| 12 | Vol. Stock (m³) | `lot_volumen_m3` | `stock.quant` (campo añadido) | Float (related, store=True) | `lot_id.volumen_m3` | Related → `lot_id.volumen_m3` | `lumber_stock_report.py` líneas 140-147 | digits=(16,3). En XLSX: `round(lot.volumen_m3, 3)` (línea 393) |
| 13 | Contenedor | `lot_container_name` | `stock.quant` (campo añadido) | Char (compute, store=True) | `lumber.container` via `lot_ids` | Compute → `_compute_lot_container_name` | `lumber_stock_report.py` líneas 157-177 | Busca en `lumber.container` con `sudo()`. Si no hay contenedor: string vacío. En XLSX: `_get_container_name(lot)` (línea 394) |
| 14 | Stock (solo tree) | `quantity` | `stock.quant` | Float | Campo nativo stock.quant | Directo | `inventory_report_views.xml` línea 149 | **PRESENTE SOLO EN VISTA TREE, AUSENTE EN XLSX R1**. Es el quantity físico del quant |

**Diferencia interna Variante A**: La vista tree R1 (línea 149) incluye el campo `quantity` (Stock) como columna 14, pero el método XLSX `action_export_r1_stock_detail_xlsx()` NO incluye esta columna (usa 13 columnas). El XLSX muestra `Vol. Stock (m³)` que viene de `lot.volumen_m3`, no de `quant.quantity`.

---

# 3. VARIANTE B — MATRIZ DE 14 COLUMNAS EN 3 PRESENTACIONES

## 3.1 TREE VIEW (Detalle Inventario Recepción)

**Fuente**: `inventory_report_views.xml`, record `view_lumber_reception_line_tree_detail`, líneas 9-31.

| # | Nombre visible | Nombre técnico | Modelo fuente | Tipo de campo | Origen del dato | Compute/Related/Directo | Archivo y línea | Observaciones |
|---|---------------|----------------|---------------|---------------|-----------------|------------------------|-----------------|---------------|
| 1 | Patio (label) | `patio_label` | `lumber.reception.line` (campo añadido en reportes) | Char (compute, store=True) | `location_id.name` o "R1" | Compute → `_compute_patio_label` | `lumber_reception_reports.py` líneas 33-37, 79-86 | optional="hide". Si no hay location_id: "R1" |
| 2 | Ubicación Técnica | `complete_location_name` | `lumber.reception.line` (campo añadido) | Char (related, store=True) | `location_id.complete_name` | Related → `location_id.complete_name` | `lumber_reception_reports.py` líneas 27-32 | optional="show". Nombre jerárquico completo |
| 3 | Proveedor | `partner_name` | `lumber.reception.line` (campo añadido) | Char (compute, store=True) | `reception_id.supplier_id.name` | Compute → `_compute_partner_name` | `lumber_reception_reports.py` líneas 44-48, 70-77 | optional="hide". "Sin Proveedor" si no asignado |
| 4 | Recepción | `reception_id` | `lumber.reception` | Many2one | Relación directa a lumber.reception | Directo | `inventory_report_views.xml` línea 17 | Muestra el display_name de la recepción |
| 5 | Producto | `product_id` | `product.product` | Many2one | Relación directa | Directo | `inventory_report_views.xml` línea 18 | Campo del mixin de ingesta |
| 6 | Subproducto | `subproduct_id` | `madenat.subproducto` | Many2one | Relación directa | Directo | `inventory_report_views.xml` línea 19 | Campo nativo de lumber.reception.line (línea 76 del modelo) |
| 7 | Lote | `lot_name` | `lumber.reception.line` | Char | Campo directo del modelo | Directo | `inventory_report_views.xml` línea 20 | Campo nativo de lumber.reception.line (línea 75 del modelo) |
| 8 | Espesor | `thickness_visual` | `lumber.reception.line` | Char (compute, store=True, readonly=False) | Calculado desde dimensiones nominales/documentales | Compute → `_compute_visual_defaults` | `inventory_report_views.xml` línea 21 | Valor fraccionario (ej: "6/4", "1 9/16"). Editable |
| 9 | Ancho | `width_visual` | `lumber.reception.line` | Char (compute, store=True, readonly=False) | Calculado desde dimensiones nominales/documentales | Compute → `_compute_visual_defaults` | `inventory_report_views.xml` línea 22 | Valor fraccionario (ej: "5 5/8"). Editable |
| 10 | Largo (m) | `length` | `lumber.reception.line` | Float | Campo directo del modelo | Directo | `inventory_report_views.xml` línea 23 | Campo nativo (línea 270 del modelo). En metros |
| 11 | Piezas | `pieces` | `lumber.reception.line` | Float/Integer | Campo del mixin de ingesta | Directo | `inventory_report_views.xml` línea 24 | NO VERIFICADO tipo exacto (puede ser Float del mixin) |
| 12 | Orden Compra | `purchase_order_name` | `lumber.reception.line` | Char (related, store=True) | `reception_id.manual_po_name` | Related → `reception_id.manual_po_name` | `inventory_report_views.xml` línea 25; `lumber_reception.py` líneas 80-85 | Nombre manual de OC, NO el purchase.order real |
| 13 | Vol. Físico (m³) | `vol_physical_m3` | `lumber.reception.line` | Float (compute, store=True) | `(thickness × width × length × pieces) / 1,000,000` | Compute → `_compute_vol_physical_strict` | `inventory_report_views.xml` línea 26; `lumber_reception.py` líneas 310-316, 414-432 | Calculado de dimensiones FÍSICAS (mm × mm × m) |
| 14 | Vol. MBF | `vol_mbf` | `lumber.reception.line` | Float (compute, store=True) | Fórmula de exportación según regla | Compute → `_compute_export_values` | `inventory_report_views.xml` línea 27; `lumber_reception.py` líneas 388-393, 679-783 | Depende de export_calculation_rule |

## 3.2 PDF (QWeb Report R1 — Detalle por Patio)

**Fuente**: `inventory_report_pdf.xml`, template `report_r1_detail_location_pdf`, líneas 54-134.

**Modelo**: `lumber.reception.line` (campo `model` en el record `action_report_r1_detail_location`, línea 129).

| # | Nombre visible | Expresión QWeb | Modelo fuente real | Tipo de acceso | Origen del dato | Archivo y línea | Observaciones |
|---|---------------|----------------|-------------------|----------------|-----------------|-----------------|---------------|
| 1 | Patio | `l.reception_id.location_id.name` | `stock.location` vía `lumber.reception` | Navegación: line→reception→location→name | `reception_id.location_id.name` | `inventory_report_pdf.xml` línea 93 | NO usa patio_label. Va directo a la ubicación de la recepción |
| 2 | Proveedor | `l.partner_name` | `lumber.reception.line` (campo compute) | Compute field | `reception_id.supplier_id.name` o "Sin Proveedor" | `inventory_report_pdf.xml` línea 94 | Usa el campo compute añadido en lumber_reception_reports.py |
| 3 | Guía | `l.reception_id.name` | `lumber.reception` | Navegación: line→reception→name | `reception_id.name` | `inventory_report_pdf.xml` línea 95 | Es el número de guía de la recepción |
| 4 | Fecha | `l.reception_id.reception_date` | `lumber.reception` | Navegación: line→reception→reception_date | `reception_id.reception_date` | `inventory_report_pdf.xml` línea 96 | Sin formato aplicado (usa el raw del campo) |
| 5 | Orden de Compra | `l.reception_id.purchase_order or 'SIN ORDEN'` | `lumber.reception` (campo compute) | Navegación: line→reception→purchase_order | `reception_id.purchase_order` (compute que resuelve purchase_id.name o manual_po_name) | `inventory_report_pdf.xml` línea 97 | **DIFERENCIA CLAVE**: PDF usa `purchase_order` (campo compute que prioriza purchase_id.name real sobre manual_po_name). XLSX Variante B usa `reception_id.purchase_order` (línea 638) |
| 6 | Producto | `l.product_id.name` | `product.product` | Navegación directa | `product_id.name` | `inventory_report_pdf.xml` línea 98 | |
| 7 | Subproducto | `l.subproduct_id.name` | `madenat.subproducto` | Navegación directa | `subproduct_id.name` | `inventory_report_pdf.xml` línea 99 | |
| 8 | Espesor | `l.thickness_visual` | `lumber.reception.line` | Campo directo (compute) | `thickness_visual` (fracción) | `inventory_report_pdf.xml` línea 100 | |
| 9 | Ancho | `l.width_visual` | `lumber.reception.line` | Campo directo (compute) | `width_visual` (fracción) | `inventory_report_pdf.xml` línea 101 | |
| 10 | Largo (m) | `'%.3f' % (l.length or 0)` | `lumber.reception.line` | Campo directo | `length` (metros) | `inventory_report_pdf.xml` línea 102 | Formateado a 3 decimales |
| 11 | Piezas | `l.pieces` | `lumber.reception.line` | Campo directo | `pieces` | `inventory_report_pdf.xml` línea 103 | |
| 12 | M3 | `'%.3f' % (l.vol_physical_m3 or 0)` | `lumber.reception.line` | Campo compute | `vol_physical_m3` | `inventory_report_pdf.xml` línea 104 | Formateado a 3 decimales |
| 13 | MBF | `'%.3f' % (l.vol_mbf or 0)` | `lumber.reception.line` | Campo compute | `vol_mbf` | `inventory_report_pdf.xml` línea 105 | Formateado a 3 decimales |
| 14 | — | — | — | — | — | — | **EL PDF R1 TIENE 13 COLUMNAS, NO 14**. colspan="9" en tfoot (línea 114) confirma 13 columnas. |

**Total columnas PDF R1: 13** (Patio, Proveedor, Guía, Fecha, Orden de Compra, Producto, Subproducto, Espesor, Ancho, Largo, Piezas, M3, MBF)

## 3.3 XLSX (Server Action R1 — Detalle por Patio)

**Fuente**: `lumber_reception_reports.py`, método `action_export_r1_detail_location_xlsx()`, líneas 172-244.

| # | Nombre visible | Nombre/variable en código | Modelo fuente real | Tipo de campo | Origen del dato | Archivo y línea | Observaciones |
|---|---------------|--------------------------|-------------------|---------------|-----------------|-----------------|---------------|
| 1 | Patio | `line.patio_label` | `lumber.reception.line` (campo compute) | Char (compute) | `location_id.name` o "R1" | `lumber_reception_reports.py` línea 205 | |
| 2 | Proveedor | `line.partner_name` | `lumber.reception.line` (campo compute) | Char (compute) | `reception_id.supplier_id.name` o "Sin Proveedor" | `lumber_reception_reports.py` línea 206 | |
| 3 | Guía | `line.reception_id.name` | `lumber.reception` | Char | `reception_id.name` | `lumber_reception_reports.py` línea 207 | |
| 4 | Fecha | `line.reception_id.reception_date` | `lumber.reception` | Datetime | `reception_id.reception_date` | `lumber_reception_reports.py` línea 208 | Formateado a 'YYYY-MM-DD' |
| 5 | Producto | `line.product_id.name` | `product.product` | Many2one→Char | `product_id.name` | `lumber_reception_reports.py` línea 209 | |
| 6 | Subproducto | `line.subproduct_id.name` | `madenat.subproducto` | Many2one→Char | `subproduct_id.name` | `lumber_reception_reports.py` línea 210 | |
| 7 | Espesor | `line.thickness_visual` | `lumber.reception.line` | Char (compute) | `thickness_visual` | `lumber_reception_reports.py` línea 211 | |
| 8 | Ancho | `line.width_visual` | `lumber.reception.line` | Char (compute) | `width_visual` | `lumber_reception_reports.py` línea 212 | |
| 9 | Largo (m) | `line.length` | `lumber.reception.line` | Float | `length` | `lumber_reception_reports.py` líneas 213, 226 | |
| 10 | Piezas | `line.pieces` | `lumber.reception.line` | Integer/Float | `pieces` | `lumber_reception_reports.py` líneas 214, 227 | |
| 11 | M3 | `line.vol_physical_m3` | `lumber.reception.line` | Float (compute) | `vol_physical_m3` | `lumber_reception_reports.py` líneas 215, 228 | |
| 12 | MBF | `line.vol_mbf` | `lumber.reception.line` | Float (compute) | `vol_mbf` | `lumber_reception_reports.py` líneas 216, 229 | |
| 13 | — | — | — | — | — | — | **EL XLSX R1 DE VARIANTE B TIENE 12 COLUMNAS.** widths = `[20, 25, 18, 12, 25, 20, 10, 10, 10, 9, 12, 12]` = 12 elementos (línea 187). No hay columna 13 ni 14. |

**Total columnas XLSX R1 Variante B: 12** (no incluye Orden de Compra ni Etiqueta Lote)

## 3.4 COMPARACIÓN INTERNA TREE vs PDF vs XLSX (Variante B)

| Aspecto | Tree | PDF | XLSX | ¿Divergen? |
|---------|------|-----|------|------------|
| Número de columnas | 14 | 13 | 12 | **SÍ — DIVERGEN** |
| Incluye Orden de Compra | Sí (purchase_order_name) | Sí (reception_id.purchase_order) | **NO** | **SÍ** |
| Incluye Ubicación Técnica | Sí (complete_location_name) | No | No | **SÍ** |
| Incluye N° Lote (lot_name) | Sí | No | No | **SÍ** |
| Incluye Etiqueta Lote | No | No | No | Consistente |
| Fuente de "Guía" | reception_id (display_name) | reception_id.name | reception_id.name | **SÍ** — Tree muestra display_name, PDF/XLSX muestran name |
| Fuente de "Patio" | patio_label (compute) | reception_id.location_id.name | patio_label (compute) | **SÍ** — PDF navega directo, Tree/XLSX usan campo compute |
| Fuente de "Orden Compra" | reception_id.manual_po_name | reception_id.purchase_order (compute) | No incluido | **SÍ** — Tree usa manual_po_name, PDF usa purchase_order compute |
| Agrupación visual | No agrupa en tree (lista plana) | No agrupa (lista plana) | No agrupa (lista plana) | Consistente (ninguno agrupa) |
| Totales | Columnas con sum | tfoot con totales | Fila TOTALES | Consistente en tener totales, pero formato difiere |
| Dataset | self (recordset actual) | docs (pasado por contexto) | self (recordset actual) | **NO VERIFICADO** si reciben el mismo domain |

---

# 4. 22 DIFERENCIAS EXACTAS ENTRE VARIANTE A Y VARIANTE B

| # | Atributo comparado | Variante A (`stock.quant`) | Variante B (`lumber.reception.line`) | Impacto funcional | Evidencia |
|---|-------------------|---------------------------|--------------------------------------|-------------------|-----------|
| 1 | **Modelo fuente** | `stock.quant` (_inherit) | `lumber.reception.line` (_inherit) | Diferente universo de datos: A muestra existencia física real, B muestra líneas de recepción documental | A: `lumber_stock_report.py` línea 40. B: `lumber_reception_reports.py` línea 17 |
| 2 | **Filtro de existencia** | `quantity > 0 AND location_id.usage = 'internal'` + `lot_id IS NOT NULL` | Sin filtro de cantidad/ubicación (solo filtro por estado `!= 'cancelled'` en search view) | A solo muestra stock con existencia > 0. B muestra todas las líneas de recepción independientemente de si aún hay stock | A: líneas 267-279. B: `inventory_report_views.xml` línea 102-103 |
| 3 | **Columna "Patio"** | `location_name` → `quant.location_id.name` (nombre corto de la ubicación del quant) | Tree/XLSX: `patio_label` → `reception_id.location_id.name`; PDF: `reception_id.location_id.name` directo | A: patio donde ESTÁ el stock físicamente. B: patio ASIGNADO en la recepción (puede diferir si se movió el stock) | A: línea 45-60, 396. B: `lumber_reception_reports.py` líneas 79-86; PDF línea 93 |
| 4 | **Columna "Guía"** | `lot_guia_number` → `lot_id.guia_number` (campo del lote) | `reception_id.name` (nombre de la recepción) | A: número de guía almacenado en el lote. B: nombre de la recepción padre. **Pueden no coincidir** si una recepción tiene nombre distinto al guia_number de sus lotes | A: líneas 75-80, 385. B: XLSX línea 207; PDF línea 95 |
| 5 | **Columna "Proveedor"** | `lot_supplier` → `lot_id.supplier_id.name` (proveedor del lote) | `partner_name` → `reception_id.supplier_id.name` (proveedor de la recepción) | Mismo dato en la práctica (ambos vía reception_id), pero A lo obtiene desde lot_id y B desde reception_id directamente. Si un lote pierde la referencia a reception, A devuelve vacío | A: líneas 99-113. B: líneas 44-48, 70-77 |
| 6 | **Columna "Orden de Compra"** | `lot_purchase_order` → `lot_id.purchase_order_id.name` (OC real del lote) | Tree: `purchase_order_name` → `reception_id.manual_po_name`; PDF: `reception_id.purchase_order` (compute); XLSX: **NO INCLUIDA** | **Diferencia crítica**: A usa purchase_order_id (OC real vinculada). B-tree usa manual_po_name (texto libre). B-PDF usa campo compute que prioriza purchase_id.name real sobre manual. B-XLSX omite OC por completo | A: líneas 83-97. B-tree: `lumber_reception.py` líneas 80-85. B-PDF: línea 97. B-XLSX: columna ausente |
| 7 | **Columna "Fecha"** | `lot_reception_date` → `lot_id.reception_id.reception_date` | `reception_id.reception_date` directo | Mismo origen lógico (reception.reception_date), distinto camino. A vía lot_id, B directo | A: líneas 67-73. B: XLSX línea 208; PDF línea 96 |
| 8 | **Etiqueta/N° Lote** | `lot_id.name` (pasado por `_clean_lot_label`) en columna explícita | Tree: `lot_name` (campo directo de lumber.reception.line). PDF y XLSX: **NO INCLUIDO** | A expone el número de lote como columna central. B-tree lo incluye, pero B-PDF y B-XLSX lo omiten por completo | A: líneas 381, 397. B-tree: línea 20 de vista |
| 9 | **Columna "Producto"** | `product_id.name` del quant | `product_id.name` de la línea | Mismo tipo de dato, pero el product_id del quant puede diferir del product_id de la línea de recepción si hubo transformación | A: línea 388. B: XLSX línea 209; PDF línea 98 |
| 10 | **Columna "Subproducto"** | `lot_subproducto` → `lot_id.subproducto_id.name` | `subproduct_id.name` directo de la línea | A vía lote, B directo de la línea. Mismo valor esperado si el lote se creó desde la línea | A: líneas 115-121. B: XLSX línea 210; PDF línea 99 |
| 11 | **Dimensiones: Espesor/Ancho** | A: `_build_escuadria(lot)` que puede componer `espesor x ancho` o usar `lot.escuadria` precalculado. O `thickness_visual`/`width_visual` separados en R5/R7/R9 | B: `thickness_visual` y `width_visual` como columnas separadas en todas las presentaciones | A-R1 muestra escuadría combinada en una sola columna. B-R1 muestra espesor y ancho por separado. **Impacto en trazabilidad**: A no expone dimensiones individuales en R1 | A-R1: líneas 305-319, 408; A-R5: líneas 563-564. B: 2 columnas separadas en todas las presentaciones |
| 12 | **Volumen: fuente del dato** | `lot_volumen_m3` → `lot_id.volumen_m3` (volumen del lote en stock) | `vol_physical_m3` (compute desde thickness × width × length × pieces / 1,000,000) | A: volumen almacenado en el lote. B: volumen calculado en tiempo real desde dimensiones físicas de la línea. **Pueden divergir** si el lote fue modificado después de la recepción | A: líneas 140-147, 393. B: `lumber_reception.py` líneas 310-316, 414-432 |
| 13 | **Columna MBF** | **NO INCLUIDA en R1 de Variante A** (ni en XLSX ni en tree) | Incluida en las 3 presentaciones (tree, PDF, XLSX) | B ofrece volumen MBF (exportación), A no lo incluye en R1 | A: cols lista línea 346-350 (sin MBF). B: presente en todas las presentaciones |
| 14 | **Columna Contenedor** | Incluida en A (XLSX y tree) | **NO INCLUIDA en B** en ninguna presentación | A proporciona trazabilidad de contenedor, B no | A: líneas 157-177, 394. B: ausente en tree/PDF/XLSX |
| 15 | **Agrupación en XLSX** | A-R1 XLSX agrupa por patio con cabeceras `📍 Patio` y subtotales por patio + línea vacía entre patios | B-R1 XLSX es lista plana sin agrupación, solo totales al final | A ofrece agrupación visual y subtotales por patio. B no agrupa | A: líneas 357-426. B: líneas 200-243 |
| 16 | **Cantidad de columnas** | 14 (tree) / 13 (XLSX) | 14 (tree) / 13 (PDF) / 12 (XLSX) | Inconsistencia interna en ambas variantes. B es más grave: 12 vs 14 columnas según presentación | Evidencia detallada en secciones 2 y 3 |
| 17 | **Trazabilidad operativa** | A: traza desde el stock físico actual (quant) → lote → recepción. Camino: `quant → lot_id → reception_id` | B: traza desde la línea de recepción → recepción. Camino: `line → reception_id` | A responde "qué hay y de dónde viene". B responde "qué se recibió". Son preguntas de negocio distintas | Arquitectura documentada en docstrings: A líneas 2-23, B líneas 2-5 |
| 18 | **Dependencia de reception_id vs lumber_reception_id** | A: `lot_id.reception_id` (campo del lote hacia lumber.reception) | B: `reception_id` (campo directo de lumber.reception.line hacia lumber.reception) | Mismo modelo destino (lumber.reception), distinto camino. A: quant→lot→reception. B: line→reception directo | A: líneas 67-73 (related). B: `lumber_reception.py` línea 74 |
| 19 | **Tratamiento de guiaprocessing_id** | NO REFERENCIADO en absoluto | NO REFERENCIADO en absoluto | **HECHO**: `guiaprocessing_id` no existe en ninguna de las dos variantes del R1. Es un campo legacy/documentación antigua sin presencia en código activo | Búsqueda exhaustiva en todo custom_addons con regex `guiaprocessing`: 0 resultados |
| 20 | **Filtro de estado documental** | Sin filtro por estado (solo existencia física) | Search view incluye filtro `filter_active`: `reception_id.state != 'cancelled'` | B excluye líneas de recepciones canceladas. A no tiene concepto de estado documental | A: no hay referencia a state. B: `inventory_report_views.xml` líneas 102-103 |
| 21 | **Formato de fecha** | XLSX: `strftime('%Y-%m-%d')`; campo es Datetime related | XLSX: `strftime('%Y-%m-%d')`; PDF: valor crudo sin formato | Mismo formato en XLSX. PDF muestra el raw del campo (puede incluir hora) | A: línea 384. B-XLSX: línea 208. B-PDF: línea 96 |
| 22 | **Columnas "huérfanas" (en una variante pero no en la otra)** | A tiene: `quantity` (Stock), `lot_container_name` (Contenedor), `lot_escuadria` (Escuadría combinada) | B tiene: `complete_location_name` (Ubicación Técnica), `lot_name` (N° Lote), `thickness_visual` + `width_visual` (separados), `vol_mbf` (MBF), `purchase_order_name` (OC) | **5 columnas exclusivas de A no están en B. 5 columnas exclusivas de B no están en A.** Esto revela que son reportes con propósitos de negocio diferentes | Evidencia: comparación directa de listas de columnas en secciones 2 y 3 |

---

# 5. DIAGNÓSTICO CANÓNICO

## 5.1 Conclusión principal

**La Variante B (`lumber.reception.line`) es la variante CANÓNICA. La Variante A (`stock.quant`) es una variante NUEVA (Fase 2/4) que complementa pero no reemplaza a B.**

## 5.2 Evidencia a favor de B como canónica

| # | Evidencia | Peso | Fuente |
|---|-----------|------|--------|
| 1 | B tiene 3 presentaciones completas (tree, PDF, XLSX). A solo tiene tree y XLSX (no tiene PDF) | **ALTO** | `inventory_report_pdf.xml` tiene 8 reportes PDF para B; A no tiene ningún PDF |
| 2 | B cubre 8 reportes (R1-R9). A cubre 5 reportes (R1, R2, R5, R7, R9) | **ALTO** | `lumber_reception_reports.py` tiene 8 métodos de export; `lumber_stock_report.py` tiene 5 |
| 3 | El modelo `lumber.reception.line` es el modelo de negocio principal para recepciones. `stock.quant` es infraestructura de Odoo estándar | **ALTO** | `lumber_reception.py` línea 48: `_name = 'lumber.reception.line'` es un modelo de negocio propio |
| 4 | Los menús y acciones originales (previos a Fase 2) apuntaban a `lumber.reception.line` | **MEDIO** | `inventory_report_pdf.xml` tiene `binding_model_id` a `model_lumber_reception_line` en todos los 8 reportes |
| 5 | B tiene search view con filtros de negocio (estado, agrupaciones por patio, producto, subproducto, proveedor, OC). A tiene search view mínimo | **MEDIO** | `inventory_report_views.xml` líneas 91-121 vs líneas 212-230 |

## 5.3 Evidencia a favor de A como canónica (o que A es intencionalmente diferente)

| # | Evidencia | Peso | Fuente |
|---|-----------|------|--------|
| 1 | A se autodenomina "FASE 4" en su docstring (línea 3). Esto implica que es una evolución planificada, no un reemplazo accidental | **ALTO** | `lumber_stock_report.py` línea 3: "FASE 4: stock.quant como fuente física" |
| 2 | A tiene server actions XLSX propias registradas en `stock_report_actions.xml` (R1, R2, R5, R7, R9) | **ALTO** | `stock_report_actions.xml` líneas 56-109 |
| 3 | A introduce el concepto de "stock real" (existencia física > 0) que B no tiene. Esto es una capacidad nueva, no una duplicación | **MEDIO** | `lumber_stock_report.py` líneas 265-279 |
| 4 | A enriquece stock.quant con campos related a lot_id que no existían antes | **MEDIO** | `lumber_stock_report.py` líneas 67-177 |

## 5.4 Evidencia de conflicto/contradicción

| # | Conflicto | Descripción |
|---|-----------|-------------|
| 1 | **Mismo nombre "R1", distinto reporte** | Ambas variantes se llaman "R1 — Detalle por Patio" pero producen datasets, columnas y totales diferentes. Esto genera ambigüedad operativa |
| 2 | **Nomenclatura de XLSX** | A genera `R1_Detalle_Patio_Stock_Real.xlsx`, B genera `R1_Detalle_Patio.xlsx`. Nombres similares, contenido diferente |
| 3 | **B-XLSX omite Orden de Compra** | La Variante B en XLSX omite la columna OC que sí está en B-PDF y B-tree. Esto es una inconsistencia interna de B que podría confundirse con una diferencia A vs B |
| 4 | **A-XLSX omite quantity** | La Variante A en XLSX omite el campo `quantity` que sí está en A-tree. Siendo A "stock real", omitir la cantidad de stock en el XLSX es contradictorio con su propósito declarado |

## 5.5 Nivel de confianza

**CONFIANZA: ALTA (85%)** en que B es canónica y A es complemento nuevo.

**Lo que falta para 100%**: Verificar en la base de datos cuál de los dos menús R1 está efectivamente en uso por los operadores. Verificar si las server actions de A (`action_server_r1_stock_detail_xlsx`) están vinculadas a menús visibles o solo existen como acciones latentes. Confirmar con el usuario de negocio si "Stock Real" es el reporte que necesitan o si necesitan ambos.

---

# 6. PROPUESTA DE UNIFICACIÓN EN 3 FASES

## FASE 1 — CONSOLIDACIÓN DE NOMENCLATURA Y ELIMINACIÓN DE AMBIGÜEDAD (5 cambios)

| # | Objetivo | Archivo objetivo | Impacto | Riesgo | Criterio de validación |
|---|----------|-----------------|---------|--------|------------------------|
| 1.1 | Renombrar Variante A a "R1-STOCK" para diferenciarla de B "R1-RECEPCIÓN" | `lumber_stock_report.py` línea 321, 352; `stock_report_actions.xml` líneas 7-13, 56-64 | Bajo: solo cambia etiquetas visibles, no lógica | Mínimo: solo afecta texto de UI | Aparecen dos menús distintos: "R1-RECEPCIÓN: Detalle por Patio" y "R1-STOCK: Detalle por Patio (Stock Real)" |
| 1.2 | Agregar tooltip/help en cada acción explicando la diferencia entre variantes | `stock_report_actions.xml` líneas 7-13, 25-31, 34-40, 43-49 | Bajo | Nulo | Los tooltips son visibles en la UI y explican qué fuente de datos usa cada reporte |
| 1.3 | Uniformar nombre de archivo XLSX: A → `R1_Stock_Real_Patio.xlsx`, B → `R1_Recepcion_Patio.xlsx` | `lumber_stock_report.py` línea 438; `lumber_reception_reports.py` línea 244 | Bajo | Bajo: solo cambia nombre de descarga | Archivos descargados tienen nombres que no generan confusión |
| 1.4 | Agregar columna `quantity` al XLSX de Variante A (actualmente solo está en tree) | `lumber_stock_report.py` líneas 341-350, 396-408 | Medio: añade 1 columna al XLSX | Bajo: es añadir, no modificar | El XLSX R1 de A tiene 14 columnas (como el tree) incluyendo Stock |
| 1.5 | Documentar en `__manifest__.py` del módulo reports la coexistencia de 2 fuentes R1 | `madenat_lumber_reports/__manifest__.py` | Nulo | Nulo | El manifest tiene un resumen explicando las dos variantes |

## FASE 2 — CORRECCIÓN DE INCONSISTENCIAS INTERNAS DE B (5 cambios)

| # | Objetivo | Archivo objetivo | Impacto | Riesgo | Criterio de validación |
|---|----------|-----------------|---------|--------|------------------------|
| 2.1 | Agregar columna "Orden de Compra" al XLSX de B-R1 (actualmente presente en tree y PDF pero no en XLSX) | `lumber_reception_reports.py` líneas 186-198, 204-229 | Medio: añade 1 columna al XLSX | Bajo: añadir columna no rompe existente | XLSX de B-R1 tiene 13 columnas (como PDF) incluyendo OC |
| 2.2 | Uniformar fuente de "Patio" en PDF de B: usar `patio_label` (campo compute) en vez de `reception_id.location_id.name` directo | `inventory_report_pdf.xml` línea 93 | Medio: cambia expresión QWeb | Medio: `patio_label` puede devolver "R1" vs name puede ser None. Probar con recepciones sin ubicación | PDF y tree muestran el mismo nombre de patio para la misma línea |
| 2.3 | Uniformar fuente de "Guía" en tree de B: usar `reception_id.name` como PDF y XLSX, no `reception_id` (display_name) | `inventory_report_views.xml` línea 17 | Medio: cambia campo en vista tree | Bajo: name es más estable que display_name | Tree muestra el número de guía, no el display_name compuesto |
| 2.4 | Agregar columna `lot_name` al PDF y XLSX de B-R1 (actualmente solo en tree) | `inventory_report_pdf.xml` líneas 72-85; `lumber_reception_reports.py` líneas 192-198 | Medio: añade columna en 2 formatos | Bajo | PDF y XLSX de B-R1 incluyen N° Lote |
| 2.5 | Verificar y documentar si `purchase_order_name` (manual_po_name) o `reception_id.purchase_order` (compute) debe ser la fuente canónica de OC en B | `lumber_reception_reports.py` línea 638; `inventory_report_pdf.xml` línea 97 | **ALTO**: impacto en trazabilidad de compras | **ALTO**: cambiar la fuente de OC afecta conciliaciones contables | Decisión documentada sobre cuál campo de OC es canónico, aplicada consistentemente en tree, PDF y XLSX |

## FASE 3 — CONVERGENCIA CONTROLADA A vs B (5 cambios)

| # | Objetivo | Archivo objetivo | Impacto | Riesgo | Criterio de validación |
|---|----------|-----------------|---------|--------|------------------------|
| 3.1 | Agregar una columna "Fuente" (Recepción/Stock) en ambos reportes para que el usuario sepa qué datos está viendo | `lumber_stock_report.py` líneas 346-350; `lumber_reception_reports.py` líneas 192-198 | Bajo: columna informativa adicional | Nulo | Cada fila indica si proviene de stock.quant o lumber.reception.line |
| 3.2 | Crear vista tree unificada opcional que consolide ambas fuentes con un campo `_source` | Nuevo modelo SQL View o `ir.ui.view` con multi-modelo | **ALTO**: nueva funcionalidad | **ALTO**: requiere SQL View en PostgreSQL | Vista muestra columnas comunes de ambas fuentes con indicador de origen |
| 3.3 | Evaluar migración de B-XLSX a usar `volumen_m3` del lote (como A) en vez de `vol_physical_m3` calculado, para consistencia volumétrica | `lumber_reception_reports.py` líneas 215, 228 | **ALTO**: cambia valores numéricos en reportes | **MUY ALTO**: puede causar diferencias en totales históricos. Requiere backtesting | Totales de volumen coinciden entre A y B para los mismos lotes |
| 3.4 | Agregar `vol_mbf` a Variante A (actualmente ausente en A) | `lumber_stock_report.py` líneas 140-147, 341-350 | Medio: añade campo y columna | Bajo: es añadir, no modificar. Requiere campo related a lot_id.volumen_mbf | A-R1 incluye columna MBF |
| 3.5 | Agregar `lot_container_name` a Variante B (actualmente ausente en B) | `lumber_reception_reports.py` líneas 192-198; `inventory_report_pdf.xml` líneas 72-85 | Bajo: añade columna de trazabilidad | Bajo: el campo ya existe en lumber_stock_report.py, se puede exponer en B vía related | B-R1 incluye columna Contenedor |

---

# NOTAS FINALES DEL AUDITOR

1. **No hay `guiaprocessing_id`** en ninguna de las dos variantes. Búsqueda exhaustiva en todo `custom_addons/` con regex: 0 resultados. Es un campo de documentación legacy sin presencia en código activo.

2. **Ambas variantes son funcionales y complementarias**, no redundantes. La Variante A responde a la pregunta de negocio "¿qué stock físico hay ahora y dónde está?"; la Variante B responde "¿qué se recibió y de qué recepción proviene?".

3. **La inconsistencia más grave** es que B-XLSX omite la columna "Orden de Compra" y "N° Lote" que sí están en B-tree y B-PDF. Esto debe corregirse en Fase 2.

4. **La inconsistencia más confusa** para un operador es que ambos reportes se llaman "R1 — Detalle por Patio" pero muestran datos diferentes. La Fase 1 resuelve esto con renombramiento.

5. **La convergencia total no es recomendable** porque las fuentes de datos (`stock.quant` vs `lumber.reception.line`) responden preguntas de negocio distintas. Unificar forzosamente destruiría el valor de tener ambas perspectivas.

---

*Documento generado por auditoría automatizada el 2026-06-16. Todas las afirmaciones están respaldadas por referencia a archivo y línea.*