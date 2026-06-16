# Reportes de Inventario Recepción

**Módulo:** `madenat_lumber_reports` (v18.0.2.0.0)  
**Modelo base:** `lumber.reception.line` (heredado vía `_inherit`)  
**Base de datos:** `madenat_test`

---

## 1. Descripción General

Se implementaron 8 reportes de inventario de recepción agrupados en el menú **📦 Inventario Recepción** (sequence 39), ubicado bajo `Reportes MADENAT > 📦 Inventario Recepción`.

Cada reporte tiene **3 capas de salida**:
1. **Vista lista (tree)** — `ir.actions.act_window` con filtros y agrupaciones preconfiguradas
2. **📄 Imprimir PDF** — `ir.actions.report` con plantillas QWeb
3. **📊 Exportar XLSX** — Método Python usando librería `xlsxwriter`

---

## 2. Los 8 Reportes

| ID | Nombre | Dimensión | Tipo | Seq | Agrupación default |
|----|--------|-----------|------|-----|-------------------|
| R1 | Detalle por Patio — Todos Productos | `location_id` | Detalle | 40 | `reception_id__location_id` |
| R2 | Resumen por Patio — Todos Productos | `location_id` | Resumen | 41 | `reception_id__location_id` |
| R3 | Detalle por Patio — Tipo Producto | `location_id` + `subproduct_id` | Detalle | 42 | `reception_id__location_id` |
| R4 | Resumen por Patio — Tipo Producto | `location_id` + `subproduct_id` | Resumen | 43 | `reception_id__location_id` |
| R5 | Detalle por Proveedor | `partner_id` (vía PO) | Detalle | 44 | Sin agrupación default |
| R6 | Resumen por Proveedor | `partner_id` (vía PO) | Resumen | 45 | Sin agrupación default |
| R7 | Detalle por Orden de Compra | `purchase_id` | Detalle | 46 | Sin agrupación default |
| R8 | Resumen por Orden de Compra | `purchase_id` | Resumen | 47 | Sin agrupación default |

### Columnas DETALLE (R1, R3, R5, R7)
| Patio | Proveedor | Guía | Fecha | Producto | Subproducto | Espesor | Ancho | Largo (m) | Piezas | M3 | MBF |

### Columnas RESUMEN (R2, R4, R6, R8)
| [Dimensión agrupadora] | Producto | Subproducto | Total Piezas | Total M3 | Total MBF |

R6: dimensión = Proveedor  
R8: dimensión = Orden de Compra

---

## 3. Campos Fuente de Cada Dimensión

| Dimensión | Campo Odoo | Acceso |
|-----------|-----------|--------|
| **Patio** | `reception_id.location_id.name` | Vía FK: `lumber.reception.line` → `lumber.reception` → `stock.location` |
| **Proveedor** | `reception_id.purchase_id.partner_id.name` | Vía FK doble: `lumber.reception.line` → `lumber.reception` → `purchase.order` → `res.partner` |
| **Orden de Compra** | `reception_id.purchase_id.name` | Vía FK: `lumber.reception.line` → `lumber.reception` → `purchase.order` |
| **Producto** | `product_id.name` | FK directa en `lumber.reception.line` |
| **Subproducto** | `subproduct_id.name` | FK directa en `lumber.reception.line` → `madenat.subproducto` |

⚠️ **Restricción:** El subproducto usa el modelo `madenat.subproducto` (tabla `lumber_profile_subproduct_rule` en BD). El campo en la línea de recepción es `subproduct_id` (NO `lumber_subproduct`).

---

## 4. Filtro de Recepciones Canceladas

Todos los reportes aplican el dominio:
```
[('reception_id.state', '!=', 'cancelled')]
```
Esto excluye líneas cuyas recepciones están en estado `cancelled`.

---

## 5. Arquitectura de Archivos

```
madenat_lumber_reports/
├── __manifest__.py                          ← v18.0.2.0.0 + 3 nuevos data files
├── models/
│   ├── __init__.py                          ← agregado: from . import lumber_reception_reports
│   └── lumber_reception_reports.py          ← herencia + 8 métodos XLSX
├── reports/
│   ├── report_packing_list.xml              ← (existente, no se toca)
│   ├── report_shipment_manifest.xml         ← (existente, no se toca)
│   └── inventory_report_pdf.xml             ← NUEVO: 8 templates QWeb + 8 ir.actions.report
├── views/
│   ├── lumber_reports_menu.xml              ← (existente, no se toca)
│   ├── menu_remapping.xml                   ← MODIFICADO: +9 menuitems
│   ├── inventory_report_actions.xml         ← NUEVO: 8 ir.actions.act_window
│   └── inventory_report_views.xml           ← NUEVO: 2 tree views + 1 search view
```

---

## 6. Cómo Agregar un Reporte Nuevo Siguiendo el Mismo Patrón

### Paso 1: Método XLSX (en `lumber_reception_reports.py`)
```python
def action_export_rN_nombre_xlsx(self):
    if not self:
        raise UserError(_("No hay líneas para exportar."))
    try:
        import xlsxwriter
    except ImportError:
        raise UserError(_("Instale xlsxwriter."))
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet('Nombre_Hoja')
    sty = self._xlsx_styles(workbook)
    # ... escribir datos ...
    return self._create_xlsx_attachment(workbook, output, 'Nombre_Archivo.xlsx')
```

### Paso 2: Plantilla QWeb PDF (en `inventory_report_pdf.xml`)
```xml
<template id="report_rN_nombre_pdf">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="line">
            <t t-call="web.external_layout">
                <div class="page" style="font-family: 'Calibri', 'Segoe UI', 'Arial', sans-serif; font-size: 11px;">
                    <!-- ... tabla ... -->
                </div>
            </t>
        </t>
    </t>
</template>
<record id="action_report_rN_nombre" model="ir.actions.report">
    <field name="name">RN: Nombre (PDF)</field>
    <field name="model">lumber.reception.line</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">madenat_lumber_reports.report_rN_nombre_pdf</field>
    <field name="report_file">madenat_lumber_reports.report_rN_nombre_pdf</field>
    <field name="binding_model_id" ref="model_lumber_reception_line"/>
</record>
```

### Paso 3: Acción de Ventana (en `inventory_report_actions.xml`)
```xml
<record id="action_rN_nombre" model="ir.actions.act_window">
    <field name="name">RN: Nombre</field>
    <field name="res_model">lumber.reception.line</field>
    <field name="view_mode">tree</field>
    <field name="domain">[('reception_id.state', '!=', 'cancelled')]</field>
    <field name="context">{'search_default_filter_active': True}</field>
    <field name="view_id" ref="view_lumber_reception_line_tree_detail"/>
</record>
```

### Paso 4: Menú (en `menu_remapping.xml`)
```xml
<menuitem id="menu_rN_nombre"
          name="RN: Nombre"
          parent="menu_inventory_reports_section"
          action="madenat_lumber_reports.action_rN_nombre"
          sequence="XX"/>
```

---

## 7. Restricciones Técnicas

| Restricción | Detalle |
|-------------|---------|
| **Modelo** | Solo herencia `_inherit = 'lumber.reception.line'`. NO crear `_name` nuevos. |
| **Librería XLSX** | `xlsxwriter` exclusivamente (NO `openpyxl`) |
| **Fuente** | Calibri 11pt en todos los formatos |
| **PDF QWeb** | `<t t-call="web.html_container">` + `<t t-call="web.external_layout">` |
| **PDF thead** | Fondo oscuro `#343a40` con texto blanco |
| **Volúmenes** | Siempre formato `'%.3f'` (3 decimales) |
| **Proveedor** | Siempre vía `reception_id.purchase_id.partner_id` (no campo directo) |
| **Subproducto** | Modelo `madenat.subproducto` (tabla `lumber_profile_subproduct_rule`) |
| **Menús existentes** | Los menús sequence 10, 20, 30 en `menu_remapping.xml` no se modifican |
| **Archivos existentes** | `report_packing_list.xml`, `report_shipment_manifest.xml`, `lumber_reports_menu.xml` no se tocan |

---

## 8. Validación

```bash
cd ~/dev-stack/odoo/odoo-18-ce
docker compose -f docker-compose.dev.yml run --rm odoo \
  -d madenat_test -u madenat_lumber_reports --stop-after-init 2>&1 | tail -20
```

Debe terminar sin ERROR. Verificar en UI:
- Menú "📦 Inventario Recepción" visible con 8 sub-menús (seq 40-47)
- Los 3 menús anteriores (Comercial, Físico, Embarque) siguen presentes (seq 10, 20, 30)
- R1 muestra filas con datos de recepciones existentes
- Botón XLSX descarga archivo sin traceback

---

## 9. Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 18.0.1.0.0 | Original | Menús base + remapeo |
| 18.0.2.0.0 | 2026-06-11 | 8 reportes de inventario recepción (R1-R8) |