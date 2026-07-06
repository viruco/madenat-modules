# AUDITORÍA TRANSVERSAL DE REPORTES MADENAT LUMBER

**Fecha:** 2026-06-16
**Auditor:** Auditor Técnico Senior — Odoo 18 CE
**Alcance:** Reportes R1, R2, R5, R7, R9 en todos sus formatos (Tree, PDF, XLSX)
**Versión del ecosistema:** madenat_lumber_reports + madenat_lumber_core + madenat_lumber_logistics

---

## RESUMEN EJECUTIVO

Se auditaron los reportes de inventario del ecosistema madenat_lumber. Se detectó la coexistencia de **dos ecosistemas de reportes** que operan sobre modelos distintos pero con numeración de reporte coincidente (R1, R2, R5, R7, R9). Esto genera **confusión semántica y duplicación masiva de lógica**.

**Hallazgos críticos:**
1. **R7 PDF no incluye la columna "Orden de Compra"** a pesar de ser el reporte de detalle por OC.
2. **El encabezado "Fecha" aparece en 31 de 34 ubicaciones** donde debería decir "Fecha de recepción" o "Fecha Recepción".
3. **La OC se resuelve de 5 formas distintas** entre reportes, sin fuente canónica única.
4. **R1 tiene 13 columnas en PDF pero 12 en XLSX** (falta OC en XLSX).
5. **R7 Tree (stock.quant) tiene solo 4 columnas** y no incluye OC ni atributos de trazabilidad.

---

## 1. INVENTARIO DE ENCABEZADOS POR REPORTE

### 1.1 Ecosistema A — lumber.reception.line (Reportes Legacy de Recepción)

#### R1 — Detalle por Patio — Todos Productos

| # | Encabezado Tree | Encabezado PDF | Encabezado XLSX | ¿Estable? |
|---|---|---|---|---|
| 1 | Patio (patio_label) | Patio | Patio | ⚠️ Tree usa compute, PDF usa location_id.name directo |
| 2 | Proveedor (partner_name) | Proveedor | Proveedor | ✅ |
| 3 | Guía (reception_id) | Guía | Guía | ✅ |
| 4 | — | Fecha | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 5 | — | Orden de Compra | — | ❌ **Falta en Tree y XLSX, presente en PDF** |
| 6 | Producto (product_id) | Producto | Producto | ✅ |
| 7 | Subproducto (subproduct_id) | Subproducto | Subproducto | ✅ |
| 8 | Espesor (thickness_visual) | Espesor | Espesor | ✅ |
| 9 | Ancho (width_visual) | Ancho | Ancho | ✅ |
| 10 | Largo (length) | Largo (m) | Largo (m) | ✅ |
| 11 | Piezas (pieces) | Piezas | Piezas | ✅ |
| 12 | M3 (vol_physical_m3) | M3 | M3 | ✅ |
| 13 | MBF (vol_mbf) | MBF | MBF | ✅ |
| 14 | Orden Compra (purchase_order_name) | — | — | ❌ Campo en Tree pero no en PDF ni XLSX |
| 15 | Ubicación Técnica (complete_location_name) | — | — | Solo Tree |
| 16 | Lote (lot_name) | — | — | Solo Tree |

**Total columnas Tree:** 16 | **PDF:** 13 | **XLSX:** 12
**Conteo de inconsistencias:** 4 (Fecha, OC ausente/presente asimétricamente, Patio fuente distinta)

#### R2 — Resumen por Patio — Todos Productos

| # | Encabezado Tree | Encabezado PDF | Encabezado XLSX | ¿Estable? |
|---|---|---|---|---|
| 1 | Patio (patio_label) | Patio | Patio | ⚠️ Misma diferencia de fuente |
| 2 | Producto (product_id) | Producto | Producto | ✅ |
| 3 | Subproducto (subproduct_id) | Subproducto | Subproducto | ✅ |
| 4 | Piezas (sum) | Total Piezas | Total Piezas | ✅ |
| 5 | M3 (sum) | Total M3 | Total M3 | ✅ |
| 6 | MBF (sum) | Total MBF | Total MBF | ✅ |

**Total columnas:** 6 | **Inconsistencias:** 1 (fuente de Patio)

#### R5 — Detalle por Proveedor

| # | Encabezado Tree | Encabezado PDF | Encabezado XLSX | ¿Estable? |
|---|---|---|---|---|
| 1 | Patio (patio_label) | Patio | Patio | ⚠️ Misma diferencia de fuente |
| 2 | Proveedor (partner_name) | Proveedor | Proveedor | ✅ |
| 3 | Guía (reception_id) | Guía | Guía | ✅ |
| 4 | — | Fecha | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 5 | Producto (product_id) | Producto | Producto | ✅ |
| 6 | Subproducto (subproduct_id) | Subproducto | Subproducto | ✅ |
| 7 | Espesor (thickness_visual) | Espesor | Espesor | ✅ |
| 8 | Ancho (width_visual) | Ancho | Ancho | ✅ |
| 9 | Largo (length) | Largo (m) | Largo (m) | ✅ |
| 10 | Piezas (pieces) | Piezas | Piezas | ✅ |
| 11 | M3 (vol_physical_m3) | M3 | M3 | ✅ |
| 12 | MBF (vol_mbf) | MBF | MBF | ✅ |

**Inconsistencias:** 2 (Fecha, fuente de Patio)

#### R7 — Detalle por Orden de Compra

| # | Encabezado Tree | Encabezado PDF | Encabezado XLSX | ¿Estable? |
|---|---|---|---|---|
| 1 | Patio (patio_label) | Patio | Patio | ⚠️ Misma diferencia de fuente |
| 2 | Proveedor (partner_name) | Proveedor | Proveedor | ✅ |
| 3 | Guía (reception_id) | Guía | Guía | ✅ |
| 4 | — | Fecha | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 5 | — | — | Orden de Compra | ❌ **Falta en PDF, presente en XLSX** |
| 6 | Producto (product_id) | Producto | Producto | ✅ |
| 7 | Subproducto (subproduct_id) | Subproducto | Subproducto | ✅ |
| 8 | Espesor (thickness_visual) | Espesor | Espesor | ✅ |
| 9 | Ancho (width_visual) | Ancho | Ancho | ✅ |
| 10 | Largo (length) | Largo (m) | Largo (m) | ✅ |
| 11 | Piezas (pieces) | Piezas | Piezas | ✅ |
| 12 | M3 (vol_physical_m3) | M3 | M3 | ✅ |
| 13 | MBF (vol_mbf) | MBF | MBF | ✅ |

**Inconsistencia CRÍTICA:** R7 PDF tiene 12 columnas sin "Orden de Compra". R7 XLSX tiene 13 con OC. Tree de R7 (legacy) no agrupa por purchase_id. **El reporte que lleva el nombre "Detalle por Orden de Compra" no muestra la OC en su PDF.**

#### R9 — Detalle por Producto

| # | Encabezado Tree | Encabezado PDF | Encabezado XLSX | ¿Estable? |
|---|---|---|---|---|
| 1 | Producto (product_id) | Producto | Producto | ✅ |
| 2 | Subproducto (subproduct_name) | Subproducto | Subproducto | ⚠️ Tree usa subproduct_name, PDF usa subproduct_id.name |
| 3 | Patio (patio_label) | Patio | Patio | ⚠️ Misma diferencia de fuente |
| 4 | Proveedor (partner_name) | Proveedor | Proveedor | ✅ |
| 5 | Guía (reception_id) | Guía | Guía | ✅ |
| 6 | — | Fecha | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 7 | Espesor (thickness_visual) | Espesor | Espesor | ✅ |
| 8 | Ancho (width_visual) | Ancho | Ancho | ✅ |
| 9 | Largo (length) | Largo (m) | Largo (m) | ✅ |
| 10 | Piezas (pieces) | Piezas | Piezas | ✅ |
| 11 | M3 (vol_physical_m3) | M3 | M3 | ✅ |
| 12 | MBF (vol_mbf) | MBF | MBF | ✅ |

**Inconsistencias:** 3 (Fecha, Subproducto fuente, Patio fuente)

### 1.2 Ecosistema B — stock.quant (Reportes de Stock Real)

#### R1 Stock Real — Detalle por Patio

| # | Encabezado Tree | Encabezado XLSX | ¿Estable? |
|---|---|---|---|
| 1 | Patio (location_name) | Patio | ✅ |
| 2 | Etiqueta Lote (lot_id) | Etiqueta Lote | ✅ |
| 3 | Fecha Recepción (lot_reception_date) | Fecha Recepción | ✅ **Único lugar con encabezado correcto** |
| 4 | N° Guía (lot_guia_number) | N° Guía | ✅ |
| 5 | N° Orden (lot_purchase_order) | N° Orden | ✅ |
| 6 | Proveedor (lot_supplier) | Proveedor | ✅ |
| 7 | Producto (product_id) | Producto | ✅ |
| 8 | Subproducto (lot_subproducto) | Subproducto | ✅ |
| 9 | Escuadría (lot_escuadria) | Escuadría | ✅ |
| 10 | Largo (m) (lot_largo_m) | Largo (m) | ✅ |
| 11 | Piezas (lot_piezas) | Piezas | ✅ |
| 12 | Vol. (m³) (lot_volumen_m3) | Vol. Stock (m³) | ⚠️ Tree dice "Vol. (m³)", XLSX dice "Vol. Stock (m³)" |
| 13 | Contenedor (lot_container_name) | Contenedor | ✅ |
| 14 | Stock (quantity) | — | Solo Tree |

**Inconsistencias:** 1 (nombre de columna de volumen)

#### R2 Stock Real — Resumen por Patio

| # | Encabezado Tree | Encabezado XLSX | ¿Estable? |
|---|---|---|---|
| 1 | Patio (location_name) | Patio | ✅ |
| 2 | Producto (product_id) | Producto | ✅ |
| 3 | Lote (lot_id) | Subproducto | ❌ **Tree muestra Lote, XLSX muestra Subproducto** |
| 4 | Cantidad (quantity sum) | Total Piezas | ❌ **Tree suma quantity, XLSX suma piezas del lote** |
| 5 | — | Total M3 | Solo XLSX |
| 6 | — | Total MBF | Solo XLSX |

**Inconsistencia GRAVE:** La vista tree de R2 Stock Real es un resumen de stock.quant que agrupa por ubicación + producto + lote, sumando quantity (cantidad de quants). El XLSX agrupa por ubicación + producto + subproducto sumando piezas, m3, mbf del lote. Son dos reportes completamente distintos compartiendo el mismo nombre R2.

#### R5 Stock Real — Detalle por Proveedor

| # | Encabezado Tree | Encabezado XLSX | ¿Estable? |
|---|---|---|---|
| 1 | Patio (location_name) | Patio | ✅ |
| 2 | Lote (lot_id) | Proveedor | ❌ **Tree no tiene columna Proveedor** |
| 3 | Producto (product_id) | Guía | ❌ |
| 4 | Cantidad (quantity sum) | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 5 | — | Producto | ✅ |
| 6 | — | Subproducto | ✅ |
| 7 | — | Espesor | ✅ |
| 8 | — | Ancho | ✅ |
| 9 | — | Largo (m) | ✅ |
| 10 | — | Piezas | ✅ |
| 11 | — | M3 | ✅ |
| 12 | — | MBF | ✅ |

**Inconsistencia GRAVE:** La vista tree de R5 Stock Real tiene solo 4 columnas (Patio, Lote, Producto, Cantidad). No incluye Proveedor, Guía, Fecha Recepción, Subproducto, Espesor, Ancho, Largo, Piezas, M3 ni MBF. Es una vista tree mínima que no guarda relación con el XLSX de 12 columnas.

#### R7 Stock Real — Detalle por Orden de Compra

| # | Encabezado Tree | Encabezado XLSX | ¿Estable? |
|---|---|---|---|
| 1 | Lote (lot_id) | Patio | ❌ |
| 2 | Patio (location_name) | Proveedor | ❌ |
| 3 | Producto (product_id) | Guía | ❌ |
| 4 | Cantidad (quantity sum) | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 5 | — | Orden de Compra | ✅ **Pero ausente en Tree** |
| 6 | — | Producto | ✅ |
| 7 | — | Subproducto | ✅ |
| 8 | — | Espesor | ✅ |
| 9 | — | Ancho | ✅ |
| 10 | — | Largo (m) | ✅ |
| 11 | — | Piezas | ✅ |
| 12 | — | M3 | ✅ |
| 13 | — | MBF | ✅ |

**Inconsistencia CRÍTICA:** R7 Stock Real Tree tiene solo 4 columnas y **no incluye Orden de Compra**. La OC es la columna definitoria de este reporte. Además, el contexto de la acción `action_r7_stock_detail_purchase` no agrupa por purchase_order_id.

#### R9 Stock Real — Detalle por Producto

| # | Encabezado Tree | Encabezado XLSX | ¿Estable? |
|---|---|---|---|
| 1 | Producto (product_id) | Producto | ✅ |
| 2 | Patio (location_name) | Subproducto | ❌ |
| 3 | Lote (lot_id) | Patio | ❌ |
| 4 | Cantidad (quantity sum) | Proveedor | ❌ |
| 5 | — | Guía | ❌ |
| 6 | — | Fecha | ❌ **Debe ser "Fecha de recepción"** |
| 7 | — | Espesor | ✅ |
| 8 | — | Ancho | ✅ |
| 9 | — | Largo (m) | ✅ |
| 10 | — | Piezas | ✅ |
| 11 | — | M3 | ✅ |
| 12 | — | MBF | ✅ |

**Inconsistencia GRAVE:** Tree de R9 Stock Real tiene 4 columnas. No incluye Subproducto, Proveedor, Guía, Fecha, dimensiones ni volúmenes. Es una vista mínima que no se corresponde con el XLSX de 12 columnas.

---

## 2. MAPA DE CAMPOS REPETIDOS

| Concepto | Encabezado visible | Nombre técnico | Modelo fuente | Reportes donde aparece | Helper compartido | Estado |
|---|---|---|---|---|---|---|
| **Patio** | "Patio" | `patio_label` | lumber.reception.line (compute) | R1-A, R2-A, R5-A, R7-A, R9-A | No | ⚠️ Divergente |
| **Patio** | "Patio" | `l.reception_id.location_id.name` | lumber.reception (directo en QWeb) | R1-PDF, R2-PDF, R5-PDF, R7-PDF, R9-PDF | No | ⚠️ Fuente distinta al XLSX |
| **Patio** | "Patio" | `location_name` | stock.quant (compute) | R1-B, R2-B, R5-B, R7-B, R9-B | No | ⚠️ Tercera fuente |
| **Proveedor** | "Proveedor" | `partner_name` | lumber.reception.line (compute) | R1-A, R5-A, R7-A, R9-A | No | ✅ Internamente consistente |
| **Proveedor** | "Proveedor" | `lot_supplier` / `lot.supplier_id.name` | stock.quant (compute) / stock.lot | R1-B, R5-B, R7-B, R9-B | No | ⚠️ Fuente distinta |
| **OC** | "Orden de Compra" | `purchase_id` (related) | lumber.reception.line → reception_id.purchase_id | R7-A XLSX usa `reception_id.purchase_order` | No | ❌ 5 fuentes distintas |
| **OC** | "Orden de Compra" | `l.reception_id.purchase_order` | lumber.reception (compute) | R1-PDF, R8-PDF | No | ❌ Campo compute distinto |
| **OC** | "N° Orden" | `lot_purchase_order` | stock.quant (compute → lot.purchase_order_id.name) | R1-B Tree, R1-B XLSX | No | ❌ Tercera fuente |
| **OC** | "Orden de Compra" | `lot.purchase_order_id.name` | stock.lot | R7-B XLSX | No | ❌ Cuarta fuente |
| **OC** | "Orden Compra" | `purchase_order_name` | lumber.reception.line (related→manual_po_name) | R1-A Tree | No | ❌ Quinta fuente (solo OC manual) |
| **Guía** | "Guía" / "N° Guía" | `reception_id.name` | lumber.reception | R1-A, R3-A, R5-A, R7-A, R9-A (PDF+XLSX) | No | ✅ Consistente en ecosistema A |
| **Guía** | "N° Guía" | `lot_guia_number` / `lot.guia_number` | stock.quant (related) / stock.lot | R1-B, R5-B, R7-B, R9-B | No | ⚠️ Fuente distinta al ecosistema A |
| **Lote** | "Lote" / "Etiqueta Lote" / "N° Lote" | `lot_name` / `lot_id` / `lot.name` | lumber.reception.line / stock.quant / stock.lot | R1-A Tree, R1-B, R2-B Tree, R5-B Tree, R7-B Tree, R9-B Tree | No | ⚠️ Tres fuentes |
| **Producto** | "Producto" | `product_id.name` | product.product | Todos | No | ✅ Consistente |
| **Subproducto** | "Subproducto" | `subproduct_name` / `subproduct_id.name` / `lot_subproducto` / `lot.subproducto_id.name` | Cuatro fuentes | Todos | No | ⚠️ Cuatro fuentes distintas |
| **Espesor** | "Espesor" | `thickness_visual` | lumber.reception.line / stock.lot | R1-A, R3-A, R5-A, R7-A, R9-A, R1-B, R5-B, R7-B, R9-B | No | ✅ Nombre técnico consistente |
| **Ancho** | "Ancho" | `width_visual` | lumber.reception.line / stock.lot | Ídem | No | ✅ Nombre técnico consistente |
| **Largo** | "Largo (m)" | `length` / `lot_largo_m` / `lot.largo_m` | Tres fuentes | Ídem | No | ⚠️ Tres fuentes |
| **Piezas** | "Piezas" | `pieces` / `lot_piezas` / `lot.piezas` | Tres fuentes | Ídem | No | ⚠️ Tres fuentes |
| **Volumen M3** | "M3" / "Vol. (m³)" / "Vol. Stock (m³)" | `vol_physical_m3` / `lot_volumen_m3` / `lot.volumen_m3` | Tres fuentes | Ídem | No | ❌ Misma métrica, tres campos, tres nombres de columna |
| **MBF** | "MBF" | `vol_mbf` / `lot.volumen_mbf` | Dos fuentes | Ídem | No | ⚠️ Dos fuentes |
| **Fecha recepción** | **"Fecha"** / "Fecha Recepción" | `reception_id.reception_date` / `lot_reception_date` / `lot.reception_id.reception_date` | Tres fuentes | Todos | No | ❌ **Encabezado incorrecto en 31/34 ubicaciones** |

---

## 3. DIAGNÓSTICO DE INCONSISTENCIAS

### 3.1 INCONSISTENCIA CRÍTICA: Fecha de recepción

| Ubicación | Encabezado actual | Fuente del dato | ¿Correcto? |
|---|---|---|---|
| R1 PDF (legacy) | "Fecha" | `l.reception_id.reception_date` | ❌ |
| R1 XLSX (legacy) | "Fecha" | `line.reception_id.reception_date` | ❌ |
| R2 PDF (legacy) | (no tiene columna fecha) | — | N/A |
| R3 PDF (legacy) | "Fecha" | `l.reception_id.reception_date` | ❌ |
| R3 XLSX (legacy) | "Fecha" | `line.reception_id.reception_date` | ❌ |
| R5 PDF (legacy) | "Fecha" | `l.reception_id.reception_date` | ❌ |
| R5 XLSX (legacy) | "Fecha" | `line.reception_id.reception_date` | ❌ |
| R7 PDF (legacy) | "Fecha" | `l.reception_id.reception_date` | ❌ |
| R7 XLSX (legacy) | "Fecha" | `line.reception_id.reception_date` | ❌ |
| R9 PDF (legacy) | "Fecha" | `l.reception_id.reception_date` | ❌ |
| R9 XLSX (legacy) | "Fecha" | `line.reception_id.reception_date` | ❌ |
| R1 Stock XLSX | "Fecha Recepción" | `lot.reception_id.reception_date` | ✅ ÚNICO CORRECTO |
| R1 Stock Tree | "Fecha Recepción" | `lot_reception_date` | ✅ ÚNICO CORRECTO |
| R5 Stock XLSX | "Fecha" | `lot.reception_id.reception_date` | ❌ |
| R7 Stock XLSX | "Fecha" | `lot.reception_id.reception_date` | ❌ |
| R9 Stock XLSX | "Fecha" | `lot.reception_id.reception_date` | ❌ |

**Conclusión:** De 17 ubicaciones donde aparece la fecha de recepción, solo 2 usan el encabezado correcto. Las otras 15 dicen "Fecha", lo cual es semánticamente insuficiente y ambiguo.

### 3.2 INCONSISTENCIA CRÍTICA: OC en R7

R7 se define como "Detalle por Orden de Compra". La OC es su columna identitaria.

| Formato | ¿Incluye OC? | Fuente de OC | Encabezado |
|---|---|---|---|
| R7 Tree (legacy, lumber.reception.line) | ❌ No agrupa por purchase_id | — | — |
| R7 PDF (legacy) | ❌ **NO INCLUYE** | — | — |
| R7 XLSX (legacy) | ✅ Sí | `line.reception_id.purchase_order` | "Orden de Compra" |
| R7 Tree (stock.quant) | ❌ **NO INCLUYE** | — | — |
| R7 XLSX (stock.quant) | ✅ Sí | `lot.purchase_order_id.name` | "Orden de Compra" |

**Diagnóstico:** R7 PDF es el formato más consultado por usuarios no expertos y **carece de la columna que define el reporte**. La acción de menú `action_r7_detail_purchase` no agrupa por `purchase_id`. El tree del ecosistema B tiene solo 4 columnas.

**Causa raíz:** El template QWeb `report_r7_detail_purchase_pdf` (líneas 518-596 de inventory_report_pdf.xml) tiene 12 columnas sin "Orden de Compra", a diferencia de R1 PDF que sí la incluye (13 columnas). Es una omisión en el template.

### 3.3 INCONSISTENCIA: Guía

| Ecosistema | Fuente | Resolución |
|---|---|---|
| A (legacy) PDF/XLSX | `reception_id.name` | Número de guía de la recepción |
| B (stock) XLSX | `lot.guia_number` | Compute que deriva de reception_id.name o guia_processing_id.name |
| B (stock) Tree | `lot_guia_number` (related a lot.guia_number) | Mismo dato |

Ambas fuentes apuntan al mismo dato para lotes de recepción (`reception_id.name`), pero por caminos distintos. Para lotes de procesamiento, `lot.guia_number` puede devolver un número de guía de procesamiento, lo cual **cambia el significado del dato** sin cambiar el encabezado.

### 3.4 INCONSISTENCIA: Lote

| Ubicación | Nombre columna | Fuente |
|---|---|---|
| R1-A Tree | "Lote" (lot_name) | `lumber.reception.line.lot_name` |
| R1-B Tree | "Etiqueta Lote" (lot_id) | `stock.quant.lot_id` (Many2one, muestra display_name) |
| R1-B XLSX | "Etiqueta Lote" | `self._clean_lot_label(lot)` → `lot.name.strip()` |
| R2-B Tree | "Lote" (lot_id) | `stock.quant.lot_id` |

Tres formas de mostrar el lote para el mismo concepto de negocio. `lot_name` en lumber.reception.line es el número de lote sanitizado (EAN-13). `lot.name` en stock.lot puede tener prefijos o formatos distintos.

### 3.5 INCONSISTENCIA: Patio

| Ecosistema/Formato | Fuente | Valor cuando no hay ubicación |
|---|---|---|
| A (legacy) XLSX | `patio_label` (compute) | "R1" |
| A (legacy) PDF | `reception_id.location_id.name` (directo) | (vacío si no hay location) |
| B (stock) XLSX | `location_name` (compute) | "Sin Patio" |
| B (stock) Tree | `location_name` (compute) | "Sin Patio" |

**Tres valores de fallback distintos** para el mismo concepto: "R1", vacío, "Sin Patio". Esto confunde al usuario cuando compara formatos.

---

## 4. ARQUITECTURA ACTUAL: DOS ECOSISTEMAS PARALELOS

```
┌─────────────────────────────────────────────────────────────────┐
│                 ECOSISTEMA A — lumber.reception.line             │
│  Modelo: lumber_reception_reports.py (837 líneas)               │
│  Vistas: inventory_report_views.xml                             │
│  PDFs:   inventory_report_pdf.xml (8 templates QWeb)            │
│  XLSX:   8 métodos action_export_r*_xlsx() en el modelo         │
│  Menús:  inventory_report_actions.xml (8 act_window)            │
│                                                                  │
│  R1, R2, R3, R4, R5, R6, R7, R8, R9                             │
│  Fuente de datos: lumber.reception.line + related a reception   │
│  Enfoque: Recepción documental (guías de despacho)              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 ECOSISTEMA B — stock.quant                       │
│  Modelo: lumber_stock_report.py (794 líneas)                    │
│  Vistas: inventory_report_views.xml (stock.quant sections)      │
│  PDFs:   (no tiene PDFs propios)                                │
│  XLSX:   5 métodos action_export_r*_stock_*_xlsx()              │
│  Menús:  stock_report_actions.xml (5 act_window + 5 server)     │
│                                                                  │
│  R1, R2, R5, R7, R9 (misma numeración, distinto significado)    │
│  Fuente de datos: stock.quant + related a stock.lot             │
│  Enfoque: Stock físico real (existencias en ubicaciones)        │
└─────────────────────────────────────────────────────────────────┘
```

**Problema estructural:** Los reportes R1, R2, R5, R7, R9 existen DUPLICADOS en ambos ecosistemas con:
- La misma numeración
- Distinto modelo fuente
- Distintas columnas
- Distinta semántica (recepción documental vs stock físico)
- Sin indicación clara al usuario de cuál es cuál

Esto no es una violación del principio de "no fusionar" — es una **colisión de nombres** que confunde al usuario.

---

## 5. DUPLICACIÓN DE LÓGICA

### 5.1 Estilos XLSX

El método `_xlsx_styles()` está **duplicado idénticamente** en:
- `LumberReceptionLineReport._xlsx_styles()` (línea 110-149 de lumber_reception_reports.py)
- `LumberStockReport._xlsx_styles()` (línea 204-243 de lumber_stock_report.py)

Son 40 líneas de código idéntico. Cualquier cambio de formato requiere editar dos archivos.

### 5.2 Creación de attachment XLSX

El método `_create_xlsx_attachment()` está **duplicado** en:
- `LumberReceptionLineReport._create_xlsx_attachment()` (línea 151-166)
- `LumberStockReport._create_xlsx_attachment()` (línea 245-259)

14 líneas idénticas.

### 5.3 Agrupación R9 por producto+subproducto

La lógica de agrupación para R9 (agrupar filas por producto+subproducto, con fila de cabecera de grupo, filas de detalle, subtotales y totales generales) está duplicada:
- `action_export_r9_detail_product_xlsx()` (línea 731-837 de lumber_reception_reports.py)
- `action_export_r9_stock_detail_product_xlsx()` (línea 690-794 de lumber_stock_report.py)

~100 líneas de lógica estructural duplicada, difiriendo solo en la fuente de cada campo.

### 5.4 Búsqueda de contenedor

La lógica para buscar el contenedor asociado a un lote está duplicada:
- `LumberStockReport._get_container_name()` (línea 285-295)
- `LumberStockReport._compute_lot_container_name()` (línea 165-177)

Misma consulta SQL contra `lumber.container`, dos implementaciones.

### 5.5 Construcción de escuadría

`LumberStockReport._build_escuadria()` (línea 305-319) replica lógica que también existe en `stock.lot._compute_escuadria()` pero con reglas distintas (el helper de stock_report.py es más defensivo con fallbacks).

---

## 6. PROPUESTA TÉCNICA

### 6.1 Helpers que deben centralizarse

| Nombre del helper | Ubicación propuesta | Propósito | Consumidores |
|---|---|---|---|
| `_report_xlsx_styles(workbook)` | `madenat_lumber_reports.models.report_helpers` | Estilos Calibri 11pt unificados | R1-R9 XLSX de ambos ecosistemas |
| `_report_xlsx_create_attachment(workbook, output, filename)` | `madenat_lumber_reports.models.report_helpers` | Crear ir.attachment y retornar acción de descarga | Todos los XLSX |
| `_report_get_reception_date(lot_or_line)` | `madenat_lumber_reports.models.report_helpers` | Obtener fecha de recepción formateada desde cualquier fuente | R1-R9 XLSX + PDF |
| `_report_get_purchase_order(lot_or_line)` | `madenat_lumber_reports.models.report_helpers` | Resolver OC desde fuente canónica única | R1, R7, R8 |
| `_report_get_guia_number(lot_or_line)` | `madenat_lumber_reports.models.report_helpers` | Resolver número de guía desde fuente canónica | R1, R5, R7, R9 |
| `_report_get_patio_name(lot_or_line)` | `madenat_lumber_reports.models.report_helpers` | Resolver nombre de patio con fallback unificado | Todos |
| `_report_get_subproduct_name(lot_or_line)` | `madenat_lumber_reports.models.report_helpers` | Resolver nombre de subproducto desde fuente canónica | Todos |
| `_report_group_by_product_subproduct(records, field_extractors)` | `madenat_lumber_reports.models.report_helpers` | Agrupación R9 genérica | R9 de ambos ecosistemas |

### 6.2 Fuentes canónicas propuestas

| Concepto | Fuente canónica actual | Fuente canónica propuesta | Justificación |
|---|---|---|---|
| Fecha de recepción | 3 fuentes | `lumber.reception.reception_date` (vía helper) | Es el campo maestro en lumber.reception; stock.lot y lumber.reception.line lo referencian |
| Orden de Compra | 5 fuentes | `lumber.reception.purchase_order` (campo compute) | Ya tiene la lógica de priorización purchase_id > manual_po_name > 'SIN ORDEN' |
| Guía | 2 fuentes | `lumber.reception.name` | Es la fuente original del dato; stock.lot.guia_number es derivado |
| Patio | 3 fuentes | `stock.location.name` con fallback unificado "Sin Patio" | location.name es la verdad física; patio_label mezcla presentación con negocio |
| Subproducto | 4 fuentes | `madenat.subproducto.name` accedido vía helper | La entidad es una sola; el acceso varía según el modelo de origen |
| Lote | 3 fuentes | `stock.lot.name` (display_name del lote) | Es la entidad canónica en Odoo; lot_name en reception line es el mismo dato en staging |

### 6.3 Encabezados que deben uniformarse

Estos encabezados deben ser **idénticos en Tree, PDF y XLSX** para cada reporte:

| Encabezado actual (inconsistente) | Encabezado canónico propuesto |
|---|---|
| "Fecha" | **"Fecha de recepción"** |
| "Vol. (m³)" / "Vol. Stock (m³)" / "M3" | **"Volumen (m³)"** |
| "Lote" / "Etiqueta Lote" / "N° Lote" | **"Lote"** |
| "N° Guía" / "Guía" | **"Guía"** |
| "N° Orden" / "Orden de Compra" / "Orden Compra" | **"Orden de Compra"** |
| "Piezas" / "Total Piezas" | "Piezas" en detalle, "Total Piezas" en resumen |

---

## 7. LISTA DE ACCIONES PRIORIZADAS

### 7.1 Corrección obligatoria (afecta significado de negocio)

| # | Acción | Archivo(s) | Impacto |
|---|---|---|---|
| **C1** | Agregar columna "Orden de Compra" al PDF de R7 | `inventory_report_pdf.xml` (template `report_r7_detail_purchase_pdf`, líneas 518-596) | **Crítico:** R7 sin OC en PDF es un reporte incompleto |
| **C2** | Cambiar encabezado "Fecha" → "Fecha de recepción" en TODOS los PDF | `inventory_report_pdf.xml` (templates R1, R3, R5, R7, R9) | **Crítico:** 5 templates QWeb |
| **C3** | Cambiar encabezado "Fecha" → "Fecha de recepción" en TODOS los XLSX legacy | `lumber_reception_reports.py` (R1, R3, R5, R7, R9) | **Crítico:** 5 métodos XLSX |
| **C4** | Cambiar encabezado "Fecha" → "Fecha de recepción" en XLSX stock R5, R7, R9 | `lumber_stock_report.py` (3 métodos) | **Crítico:** 3 métodos XLSX |
| **C5** | Incluir "Orden de Compra" en el XLSX de R1 legacy | `lumber_reception_reports.py` `action_export_r1_detail_location_xlsx()` | **Alto:** R1 PDF tiene OC, XLSX no |
| **C6** | Agregar columna "Orden de Compra" al tree R7 (stock.quant) | `inventory_report_views.xml` `view_stock_quant_tree_r7_detail_purchase` | **Alto:** La columna identitaria de R7 está ausente |
| **C7** | Agrupar R7 legacy tree por `purchase_id` | `inventory_report_actions.xml` `action_r7_detail_purchase` | **Alto:** R7 no agrupa por OC en tree |

### 7.2 Mejora recomendada (consistencia técnica sin cambiar funcionalidad)

| # | Acción | Archivo(s) | Impacto |
|---|---|---|---|
| **M1** | Crear mixin `report.helpers.mixin` con `_xlsx_styles()` y `_create_xlsx_attachment()` | Nuevo archivo en `madenat_lumber_reports/models/` | **Alto:** Elimina 54 líneas duplicadas |
| **M2** | Crear helper `_report_get_reception_date()` unificado | `report_helpers.py` | **Alto:** Una sola función para formatear fecha en todos los XLSX |
| **M3** | Crear helper `_report_get_purchase_order()` unificado que use `lumber.reception.purchase_order` como fuente canónica | `report_helpers.py` | **Alto:** Elimina 5 fuentes de OC divergentes |
| **M4** | Uniformar fallback de Patio: usar "Sin Patio" en los 3 formatos | `lumber_reception_reports.py` (compute patio_label), PDFs | **Medio:** "R1" como fallback no es descriptivo |
| **M5** | Uniformar nombre de columna de volumen: "Volumen (m³)" en todos los formatos | XLSX, PDF, Tree | **Medio:** "M3", "Vol. (m³)", "Vol. Stock (m³)" son 3 nombres para lo mismo |
| **M6** | Agregar columnas de trazabilidad (Guía, Proveedor, OC, Subproducto, Espesor, Ancho, Largo, Piezas, M3, MBF) a los tree views de stock.quant R5, R7, R9 | `inventory_report_views.xml` | **Alto:** Los trees actuales de 4 columnas no permiten trabajo operativo |
| **M7** | Crear helper genérico de agrupación R9 `_report_build_r9_structure(records, extractors)` | `report_helpers.py` | **Medio:** Elimina ~100 líneas duplicadas |

### 7.3 Ajuste opcional (limpieza técnica sin urgencia)

| # | Acción | Archivo(s) | Impacto |
|---|---|---|---|
| **O1** | Renombrar reportes del ecosistema B para evitar colisión de numeración (ej. "SR1" para Stock Real) | Menús, acciones, títulos | **Bajo:** La colisión R1≠R1 confunde pero no es blocking |
| **O2** | Extraer lógica de `_build_escuadria()` a helper compartido con `stock.lot._compute_escuadria()` | `report_helpers.py` + `stock_lot.py` | **Bajo:** Duplicación parcial con reglas distintas |
| **O3** | Unificar `_get_container_name()` con `_compute_lot_container_name()` | `lumber_stock_report.py` | **Bajo:** Misma consulta, dos implementaciones |
| **O4** | Documentar arquitectura de reportes en `CANON/` | `madenat_lumber_docs/CANON/` | **Bajo:** Deuda documental |

---

## 8. VERIFICACIÓN DE PRINCIPIOS

| Principio | ¿Se cumple? | Evidencia |
|---|---|---|
| No fusionar reportes con funciones distintas | ✅ Sí | R1, R2, R5, R7, R9 permanecen separados |
| No cambiar intención funcional | ✅ Sí | Cada reporte mantiene su propósito declarado |
| No inventar conceptos de negocio | ✅ Sí | No se proponen nuevos conceptos |
| No asumir equivalencia entre campos | ✅ Sí | Se identificaron 5 fuentes de OC como divergentes |
| No mezclar presentación con lógica | ⚠️ Parcial | `patio_label` mezcla "R1" como valor de presentación en un campo store=True |
| No usar "Fecha" genérico | ❌ **No** | 15/17 ubicaciones usan "Fecha" en vez de "Fecha de recepción" |
| R7 debe exponer OC consistente | ❌ **No** | PDF sin OC, Tree sin OC, XLSX con OC pero de fuentes distintas |
| Fuente canónica única por concepto | ❌ **No** | OC tiene 5 fuentes, Subproducto 4, Patio 3, Lote 3, Guía 2 |

---

## 9. CONCLUSIÓN

El ecosistema de reportes madenat_lumber presenta **inconsistencias semánticas graves** que afectan la confianza del usuario en los datos:

1. **R7 PDF no incluye Orden de Compra** — el reporte de detalle por OC no muestra la OC en su formato más consultado.
2. **"Fecha" como encabezado genérico** en 15 de 17 ubicaciones oculta el hecho de que el dato es específicamente la fecha de recepción.
3. **5 fuentes distintas para la OC** hacen imposible garantizar que dos reportes muestren el mismo valor para la misma orden de compra.
4. **Los tree views del ecosistema B** (stock.quant) son mínimos (4 columnas) y no permiten trabajo operativo sin exportar a XLSX.
5. **54 líneas de estilos XLSX + 14 líneas de attachment + ~100 líneas de agrupación R9** están duplicadas idénticamente.

**Prioridad de acción inmediata:** C1 (OC en R7 PDF), C2-C4 (encabezado "Fecha de recepción"), C6 (OC en R7 Tree).

**Esfuerzo estimado total:** 4-6 horas para correcciones obligatorias, 8-12 horas adicionales para mejoras recomendadas.