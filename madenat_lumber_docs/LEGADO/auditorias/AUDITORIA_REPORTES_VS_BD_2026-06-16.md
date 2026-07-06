# AUDITORÍA: COHERENCIA REPORTES VS ESTRUCTURA REAL DE BD

**Proyecto:** MADENAT Lumber — Odoo 18 CE  
**Fecha:** 2026-06-16  
**Versión:** 1.0.0  
**Alcance:** Todos los reportes XLSX, PDF, vistas tree y acciones server del proyecto  
**Tipo:** Auditoría técnica de coherencia reportes ↔ base de datos  
**Nivel de confianza:** ALTO — basado en inspección completa del código fuente de todos los módulos

---

## 1. RESUMEN EJECUTIVO

### Hallazgo principal

**El documento canónico `CANON/12_FLUJOS_INGESTA.md` está desalineado con la implementación real del código.** El documento declara `lumber_reception_id` como campo discriminador canónico para el flujo de recepción directa, pero **todo el código operativo de `stock_lot.py`, los reportes de stock real, los reportes de recepción y la lógica de negocio usan `reception_id`**. El campo `lumber_reception_id` existe en el modelo pero **no es usado por ningún reporte, vista, constraint, compute method ni flujo operativo**. Es un campo huérfano poblado en cero.

### Nivel de confianza

**ALTO (95%)**. La verificación se realizó por inspección directa del código fuente de todos los módulos del proyecto. No se requiere acceso a la BD en vivo para confirmar los hallazgos de código, aunque los datos poblacionales de `lumber_reception_id = 0` ya fueron verificados en auditorías previas.

### Naturaleza del problema

| Tipo | Severidad | Descripción |
|---|---|---|
| **Documentación** | 🔴 ALTA | CANON/12_FLUJOS_INGESTA.md referencia `lumber_reception_id`; el código real usa `reception_id` |
| **Código (reportes)** | 🟡 BAJA | R7 XLSX y R1 PDF usan `purchase_order` (Char) en vez de `purchase_id` (Many2one) |
| **Datos** | 🟡 MEDIA | `lumber_reception_id` es un campo huérfano no poblado; no afecta reportes porque ningún reporte lo usa |

---

## 2. INVENTARIO DE REPORTES AUDITADOS

### 2.1 Reportes XLSX (Python)

| ID | Reporte | Módulo | Modelo base | Tipo | Propósito |
|---|---|---|---|---|---|
| R1 | Detalle por Patio — Todos Productos | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Inventario recepción detallado por patio |
| R2 | Resumen por Patio — Todos Productos | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Inventario recepción resumido por patio |
| R3 | Detalle por Patio — Tipo Producto | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Detalle por patio + tipo producto |
| R4 | Resumen por Patio — Tipo Producto | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Resumen por patio + tipo producto |
| R5 | Detalle por Proveedor | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Detalle agrupado por proveedor |
| R6 | Resumen por Proveedor | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Resumen agrupado por proveedor |
| R7 | Detalle por Orden de Compra | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Detalle agrupado por OC |
| R8 | Resumen por Orden de Compra | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Resumen agrupado por OC |
| R9 | Detalle por Producto | `madenat_lumber_reports` | `lumber.reception.line` | XLSX | Detalle agrupado por producto |
| R1s | Detalle por Patio — Stock Real | `madenat_lumber_reports` | `stock.quant` | XLSX | Stock físico real por patio |
| R2s | Resumen por Patio — Stock Real | `madenat_lumber_reports` | `stock.quant` | XLSX | Stock físico real resumido por patio |
| R5s | Detalle por Proveedor — Stock Real | `madenat_lumber_reports` | `stock.quant` | XLSX | Stock físico real por proveedor |
| R7s | Detalle por OC — Stock Real | `madenat_lumber_reports` | `stock.quant` | XLSX | Stock físico real por OC |
| R9s | Detalle por Producto — Stock Real | `madenat_lumber_reports` | `stock.quant` | XLSX | Stock físico real por producto |

### 2.2 Reportes PDF (QWeb)

| ID | Reporte | Módulo | Modelo base | Archivo |
|---|---|---|---|---|
| R1-PDF | Detalle por Patio — Todos Productos | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R2-PDF | Resumen por Patio — Todos Productos | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R3-PDF | Detalle por Patio — Tipo Producto | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R4-PDF | Resumen por Patio — Tipo Producto | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R5-PDF | Detalle por Proveedor | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R6-PDF | Resumen por Proveedor | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R7-PDF | Detalle por Orden de Compra | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R8-PDF | Resumen por Orden de Compra | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| R9-PDF | Detalle por Producto | `madenat_lumber_reports` | `lumber.reception.line` | `inventory_report_pdf.xml` |
| PL | Packing List de Contenedor | `madenat_lumber_reports` | `lumber.container` | `report_packing_list.xml` |
| SM | Manifiesto de Embarque | `madenat_lumber_reports` | `lumber.export.shipment` | `report_shipment_manifest.xml` |

### 2.3 Vistas Tree/List

| Vista | Modelo | Columnas relevantes | Archivo |
|---|---|---|---|
| Tree Detail (R1 legado) | `lumber.reception.line` | patio_label, partner_name, reception_id, product_id, subproduct_id, pieces, vol_physical_m3, vol_mbf, purchase_order_name | `inventory_report_views.xml` |
| Tree Summary (R2 legado) | `lumber.reception.line` | patio_label, product_id, subproduct_id, pieces, vol_physical_m3, vol_mbf | `inventory_report_views.xml` |
| Tree R1 Stock | `stock.quant` | location_name, lot_id, lot_reception_date, lot_guia_number, lot_purchase_order, lot_supplier, product_id, lot_subproducto, lot_escuadria, lot_largo_m, lot_piezas, lot_volumen_m3, quantity, lot_container_name | `inventory_report_views.xml` |
| Tree R2 Stock | `stock.quant` | location_name, product_id, lot_id, quantity | `inventory_report_views.xml` |
| Tree R5 Stock | `stock.quant` | location_name, lot_id, product_id, quantity | `inventory_report_views.xml` |
| Tree R7 Stock | `stock.quant` | lot_id, location_name, product_id, quantity | `inventory_report_views.xml` |
| Tree R9 Stock | `stock.quant` | product_id, location_name, lot_id, quantity | `inventory_report_views.xml` |

---

## 3. MATRIZ DE VALIDACIÓN: REPORTES VS BD

### 3.1 Reportes sobre `lumber.reception.line` (XLSX + PDF legacy)

| Campo usado en reporte | ¿Existe en modelo? | Campo real en BD | ¿Coincide? | Riesgo | Decisión |
|---|---|---|---|---|---|
| `reception_id.name` | ✅ | `lumber_reception.name` (Char) | ✅ | Ninguno | Correcto |
| `reception_id.reception_date` | ✅ | `lumber_reception.reception_date` (Datetime) | ✅ | Ninguno | Correcto |
| `reception_id.location_id` | ✅ | `lumber_reception.location_id` via StockLotExtended | ✅ | Ninguno | Correcto |
| `reception_id.supplier_id` | ✅ | `lumber_reception.supplier_id` (Many2one) | ✅ | Ninguno | Correcto |
| `reception_id.purchase_id` | ✅ | `lumber_reception.purchase_id` (Many2one) | ✅ | Ninguno | Correcto |
| `reception_id.purchase_order` (R7 XLSX L638, R1 PDF L97) | ⚠️ | `lumber_reception.purchase_order` es Char computado, NO Many2one | ⚠️ | BAJO — funciona como string pero rompe trazabilidad del objeto purchase.order | **Corregir a `purchase_id.name`** |
| `patio_label` | ✅ | Computado en `lumber_reception_reports.py` L33-38 | ✅ | Ninguno | Correcto |
| `partner_name` | ✅ | Computado en `lumber_reception_reports.py` L44-48 | ✅ | Ninguno | Correcto |
| `subproduct_name` | ✅ | Computado en `lumber_reception_reports.py` L55-59 | ✅ | Ninguno | Correcto |
| `subproduct_id` | ✅ | `madenat.subproducto` (Many2one en línea) | ✅ | Ninguno | Correcto |
| `product_id` | ✅ | `product.product` (Many2one en línea) | ✅ | Ninguno | Correcto |
| `thickness_visual` | ✅ | `Char` en `lumber.reception.line` | ✅ | Ninguno | Correcto |
| `width_visual` | ✅ | `Char` en `lumber.reception.line` | ✅ | Ninguno | Correcto |
| `length` | ✅ | `Float` en `lumber.reception.line` | ✅ | Ninguno | Correcto |
| `pieces` | ✅ | `Integer` en mixin | ✅ | Ninguno | Correcto |
| `vol_physical_m3` | ✅ | `Float` computado en `lumber.reception.line` | ✅ | Ninguno | Correcto |
| `vol_mbf` | ✅ | `Float` computado en `lumber.reception.line` | ✅ | Ninguno | Correcto |
| `purchase_order_name` (vista tree) | ✅ | `Char` related a `reception_id.manual_po_name` | ✅ | Ninguno | Correcto |

### 3.2 Reportes sobre `stock.quant` (Stock Real XLSX + Vistas)

| Campo usado en reporte | ¿Existe en modelo? | Campo real / Ruta | ¿Coincide? | Riesgo | Decisión |
|---|---|---|---|---|---|
| `location_name` | ✅ | Computado en `lumber_stock_report.py` L45-51 | ✅ | Ninguno | Correcto |
| `lot_id` | ✅ | `stock.quant.lot_id` (Many2one nativo) | ✅ | Ninguno | Correcto |
| `lot_reception_date` | ✅ | Related: `lot_id.reception_id.reception_date` | ✅ | MEDIO — vacío para lotes de guía procesada sin `reception_id` | Aceptable (atributo condicional) |
| `lot_guia_number` | ✅ | Related: `lot_id.guia_number` (Char computado en `stock_lot.py`) | ✅ | Ninguno | Correcto |
| `lot_purchase_order` | ✅ | Computado: `lot_id.purchase_order_id.name` | ✅ | Ninguno | Correcto |
| `lot_supplier` | ✅ | Computado: `lot_id.supplier_id.name` | ✅ | Ninguno | Correcto |
| `lot_subproducto` | ✅ | Related: `lot_id.subproducto_id.name` | ✅ | Ninguno | Correcto |
| `lot_escuadria` | ✅ | Related: `lot_id.escuadria` (Char computado en `stock_lot.py`) | ✅ | Ninguno | Correcto |
| `lot_largo_m` | ✅ | Related: `lot_id.largo_m` (Float) | ✅ | Ninguno | Correcto |
| `lot_piezas` | ✅ | Related: `lot_id.piezas` (Integer) | ✅ | Ninguno | Correcto |
| `lot_volumen_m3` | ✅ | Related: `lot_id.volumen_m3` (Float computado) | ✅ | Ninguno | Correcto |
| `lot_container_name` | ✅ | Computado vía search en `lumber.container` | ✅ | Ninguno | Correcto |
| `quantity` | ✅ | `stock.quant.quantity` (Float nativo) | ✅ | Ninguno | Correcto |
| `lot.volumen_mbf` (R2s XLSX) | ✅ | Related implícito vía `lot.volumen_mbf` (Float computado en `stock_lot.py`) | ✅ | Ninguno | Correcto |

### 3.3 Reportes de Embarque

| Campo usado | ¿Existe en modelo? | Campo real | ¿Coincide? | Riesgo |
|---|---|---|---|---|
| `lot.name` (packing list) | ✅ | `stock.lot.name` | ✅ | Ninguno |
| `lot.product_id.name` | ✅ | `product.product` via `stock.lot` | ✅ | Ninguno |
| `lot.piezas` | ✅ | `stock.lot.piezas` | ✅ | Ninguno |
| `lot.volumen_m3` | ✅ | `stock.lot.volumen_m3` | ✅ | Ninguno |
| `lot.weight` | ✅ | `stock.lot.weight` (nativo Odoo) | ✅ | Ninguno |
| `container.name`, `seal_number`, `container_type` | ✅ | `lumber.container` | ✅ | Ninguno |
| `shipment.vessel_name`, `port_loading`, etc. | ✅ | `lumber.export.shipment` | ✅ | Ninguno |

---

## 4. HALLAZGOS CONFIRMADOS (HECHOS PROBADOS)

### H1 — DESALINEACIÓN DOCUMENTAL CRÍTICA: `lumber_reception_id` vs `reception_id`

| Elemento | CANON/12_FLUJOS_INGESTA.md | Código real (`stock_lot.py`) | Evidencia |
|---|---|---|---|
| Campo discriminador recepción | `lumber_reception_id` | `reception_id` | `stock_lot.py:209-214` |
| Constraint de exclusividad | `lumber_reception_id` vs `guia_processing_id` | `reception_id` vs `guia_processing_id` | `stock_lot.py:259-272` |
| `_compute_reception_type` | `lumber_reception_id` → `'raw'` | `reception_id` → `'raw'` | `stock_lot.py:248-257` |
| `_compute_guia_number` | `lumber_reception_id.name` | `reception_id.name` | `stock_lot.py:274-290` |
| `_compute_purchase_info` | `lumber_reception_id.purchase_id` | `reception_id.purchase_id` | `stock_lot.py:854-881` |

**Conclusión:** El CANON está documentando `lumber_reception_id` como si fuera el campo operativo, pero el código real nunca lo usa. `reception_id` es el campo real, poblado y activo. `lumber_reception_id` es un campo legacy/huérfano que aparece en cero en BD.

### H2 — INCONSISTENCIA MENOR: `purchase_order` vs `purchase_id` en reportes

| Reporte | Línea | Campo usado | Campo correcto | Impacto |
|---|---|---|---|---|
| R7 XLSX | `lumber_reception_reports.py:638` | `line.reception_id.purchase_order` | `line.reception_id.purchase_id.name` | Funciona (ambos son strings) pero `purchase_order` es Char computado sin FK |
| R1 PDF | `inventory_report_pdf.xml:97` | `l.reception_id.purchase_order` | `l.reception_id.purchase_id.name` | Ídem |

`purchase_order` en `lumber.reception` es un campo **Char computado** (línea ~1119 del modelo) que prioriza `purchase_id.name` con fallback a `manual_po_name`. Usarlo como display es funcionalmente correcto pero semánticamente inferior: no permite navegar al objeto `purchase.order` desde el reporte.

### H3 — `lumber_reception_id` NO ES USADO POR NINGÚN REPORTE

Se verificaron **todos** los archivos de reportes, vistas y acciones:

| Archivo | ¿Usa `lumber_reception_id`? |
|---|---|
| `lumber_reception_reports.py` (837 líneas) | ❌ No |
| `lumber_stock_report.py` (794 líneas) | ❌ No |
| `inventory_report_pdf.xml` (756 líneas) | ❌ No |
| `inventory_report_views.xml` (232 líneas) | ❌ No |
| `stock_report_actions.xml` (111 líneas) | ❌ No |
| `report_packing_list.xml` | ❌ No |
| `report_shipment_manifest.xml` | ❌ No |

**Conclusión:** `lumber_reception_id` es un campo huérfano. Existe en el modelo `stock.lot` pero no es poblado, no es verificado por constraints, no es usado por computes y no es referenciado por ningún reporte. El campo operativo real es `reception_id`.

### H4 — LOS REPORTES DE STOCK REAL NO DISCRIMINAN POR ORIGEN DE LOTE

Los reportes de `stock.quant` (R1s-R9s en `lumber_stock_report.py`) usan el dominio:
```python
[('quantity', '>', 0), ('location_id.usage', '=', 'internal')]
```
y el filtro adicional:
```python
lambda q: q.quantity > 0 and q.location_id.usage == 'internal' and q.lot_id
```

Esto significa que **incluyen lotes de ambos flujos** (recepción directa y guía procesada) siempre que tengan existencia física en ubicaciones internas. Esto es **correcto** para un reporte de stock físico: no debe discriminar por origen. Sin embargo, los campos `lot_reception_date` y cualquier atributo que dependa de `reception_id` estarán **vacíos** para lotes de guía procesada.

### H5 — LOS REPORTES DE RECEPCIÓN (LEGACY) SOLO VEN LOTES DE RECEPCIÓN DIRECTA

Los reportes R1-R9 sobre `lumber.reception.line` solo ven datos del flujo de recepción directa, porque `lumber.reception.line` está vinculado exclusivamente a `lumber.reception`. **No ven lotes de guía procesada.** Esto es correcto por diseño: son reportes de staging/recepción, no de inventario consolidado.

---

## 5. HALLAZGOS DESALINEADOS (DISCREPANCIAS REALES)

### D1 — CANON/12_FLUJOS_INGESTA.md: Campo discriminador incorrecto

| Línea del CANON | Texto actual | Debería decir |
|---|---|---|
| 26 | `lumber_reception_id` → `lumber.reception` | `reception_id` → `lumber.reception` |
| 33-38 | Constraint sobre `lumber_reception_id` | Constraint sobre `reception_id` |
| 96 | `lumber_reception_id IS NOT NULL` | `reception_id IS NOT NULL` |
| 99, 107-108 | Referencias a `lumber_reception_id` | Referencias a `reception_id` |
| 121-122, 127-128 | Múltiples referencias | Múltiples referencias |

**Severidad:** ALTA. Cualquier desarrollador que lea el CANON y escriba un reporte nuevo usando `lumber_reception_id` producirá resultados vacíos o incorrectos.

### D2 — R7 XLSX y R1 PDF: `purchase_order` en vez de `purchase_id`

Ver H2 arriba. Severidad: BAJA. No rompe funcionalidad pero es inconsistente con R8 XLSX (que sí usa `purchase_id`).

---

## 6. HALLAZGOS PENDIENTES (NO VERIFICADOS COMPLETAMENTE)

### P1 — ¿`lumber_reception_id` debe eliminarse o renombrarse?

El campo `lumber_reception_id` en `stock_lot.py:201-206`:
- Es `readonly=True`
- No tiene lógica de población automática
- No es usado por ningún compute
- Aparece en cero en BD

**Decisión pendiente:** ¿Se elimina, se renombra a `reception_id` (si se unifica), o se mantiene como alias documental? Esto requiere decisión de arquitectura.

### P2 — ¿Los reportes de costeo usan `reception_id` o `lumber_reception_id`?

Los modelos de costeo (`lumber_cost_distribution.py`, `stock_lot_costing.py`) no fueron auditados en profundidad en esta sesión. Una revisión rápida muestra que operan sobre `stock.lot.cost.line` y `lumber.cost.distribution`, que se vinculan a `stock.lot` vía `lot_id`. Si los costos se asignan usando `reception_id` como filtro, son correctos. Si alguien introduce `lumber_reception_id` como filtro en el futuro, los costos no se asignarán.

**Recomendación:** Auditoría específica de reportes de costeo en sesión separada.

### P3 — Impacto de `lot_reception_date` vacío en reportes de stock para lotes de guía procesada

El campo `lot_reception_date` (related: `lot_id.reception_id.reception_date`) estará vacío para lotes de guía procesada. Si un usuario filtra el reporte R1 de stock por fecha de recepción, los lotes de guía procesada desaparecerán del resultado. Esto puede ser comportamiento deseado o un bug, dependiendo de la expectativa del usuario.

**Recomendación:** Documentar este comportamiento en la ayuda del campo o agregar una columna de origen (`reception_type`) al reporte.

---

## 7. DECISIÓN TÉCNICA

### 7.1 Conclusión principal

**Los reportes están alineados con la estructura real de BD.** Los reportes de stock real (`stock.quant`) y los reportes de recepción (`lumber.reception.line`) usan correctamente `reception_id` como puente hacia `lumber.reception`. Ningún reporte usa `lumber_reception_id`.

**El problema es exclusivamente documental.** `CANON/12_FLUJOS_INGESTA.md` documenta `lumber_reception_id` como discriminador canónico, pero el sistema real opera con `reception_id`. Esto debe corregirse en la documentación para evitar que futuros desarrollos introduzcan bugs por referencia al campo equivocado.

### 7.2 ¿Qué está alineado?

| Componente | Estado |
|---|---|
| Reportes XLSX de stock real (R1s-R9s) | ✅ ALINEADOS |
| Reportes XLSX de recepción legacy (R1-R9) | ✅ ALINEADOS (salvo H2) |
| Reportes PDF de recepción (R1-R9) | ✅ ALINEADOS (salvo H2) |
| Reportes de embarque (Packing List, Manifiesto) | ✅ ALINEADOS |
| Vistas tree/list de stock.quant | ✅ ALINEADAS |
| Vistas tree/list de lumber.reception.line | ✅ ALINEADAS |
| Filtros y dominios en acciones server | ✅ ALINEADOS |
| Campo `reception_id` como puente operativo | ✅ ALINEADO |

### 7.3 ¿Qué está desalineado?

| Componente | Estado | Severidad |
|---|---|---|
| CANON/12_FLUJOS_INGESTA.md — campo discriminador | ❌ Usa `lumber_reception_id` en vez de `reception_id` | 🔴 ALTA |
| R7 XLSX — `purchase_order` vs `purchase_id` | ⚠️ Usa Char computado en vez de Many2one | 🟡 BAJA |
| R1 PDF — `purchase_order` vs `purchase_id` | ⚠️ Ídem | 🟡 BAJA |
| Campo `lumber_reception_id` en modelo | ⚠️ Huérfano, no poblado, no usado | 🟡 MEDIA |

---

## 8. PRÓXIMO PASO MÍNIMO

**Una sola acción concreta y prioritaria:**

> **Actualizar `CANON/12_FLUJOS_INGESTA.md`** para reemplazar todas las referencias a `lumber_reception_id` por `reception_id`, alineando el documento canónico con la implementación real del código.

Esto incluye:
1. Corregir la tabla de la sección 2 (línea 26).
2. Corregir el constraint de exclusividad documentado (líneas 30-39).
3. Corregir las secciones 4.3, 4.5, 5.1, 5.2 y 5.3.
4. Agregar una nota explicativa sobre la existencia de `lumber_reception_id` como campo legacy/huérfano.
5. Actualizar la sección 6 (Hallazgos) para reflejar que el campo operativo es `reception_id`.

**Acción secundaria (opcional, baja prioridad):**
- Corregir R7 XLSX (`lumber_reception_reports.py:638`) y R1 PDF (`inventory_report_pdf.xml:97`) para usar `purchase_id.name` en vez de `purchase_order`.

---

## APÉNDICE A: EVIDENCIA DOCUMENTAL

### A.1 Campo `reception_id` en `stock_lot.py` (líneas 201-214)

```python
lumber_reception_id = fields.Many2one(   # ← huérfano, no usado
    'lumber.reception', 
    string="Recepción de Origen",
    readonly=True,
    help="Enlace a la recepción donde se ingresó este paquete."
)

reception_id = fields.Many2one(          # ← campo operativo real
    'lumber.reception',
    string='Recepción de Compra',
    domain="[('state', '=', 'done')]",
    help="EXCLUSIVAMENTE para recepciones de compra de madera nueva"
)
```

### A.2 `_compute_reception_type` usa `reception_id` (líneas 248-257)

```python
@api.depends('reception_id', 'guia_processing_id')
def _compute_reception_type(self):
    for lot in self:
        if lot.reception_id:
            lot.reception_type = 'raw'
        elif lot.guia_processing_id:
            lot.reception_type = 'processed'
        else:
            lot.reception_type = False
```

### A.3 `_compute_guia_number` usa `reception_id` (líneas 274-290)

```python
@api.depends('reception_id', 'guia_processing_id')
def _compute_guia_number(self):
    for lot in self:
        if lot.reception_id:
            lot.guia_number = lot.reception_id.name
        elif lot.guia_processing_id:
            lot.guia_number = lot.guia_processing_id.name
        else:
            lot.guia_number = False
```

### A.4 Constraint de exclusividad usa `reception_id` (líneas 259-272)

```python
@api.constrains('reception_id', 'guia_processing_id')
def _check_reception_guia_exclusivity(self):
    for lot in self:
        if lot.reception_id and lot.guia_processing_id:
            raise ValidationError(...)
```

---

*Informe generado: 2026-06-16 — Sesión de auditoría de coherencia reportes vs BD.*  
*Versión: 1.0.0*