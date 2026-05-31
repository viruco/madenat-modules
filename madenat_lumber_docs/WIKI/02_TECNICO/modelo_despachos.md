# Modelo de Despachos — lumber.export.shipment

**Módulo:** madenat_lumber_logistics
**Categoría:** Técnico
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar los 8 modelos del módulo de logística de exportación MADENAT: embarques, contenedores, líneas de detalle, checklist documental, reglas de cubicación y distribución de costos.

---

## lumber.export.shipment (modelo principal)

### Herencia usada

```python
class LumberExportShipment(models.Model):
    _name = 'lumber.export.shipment'
    _description = 'Embarque de Exportación de Madera'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
```

**SQL constraint:** `name_uniq` (unique name)

### Estados del flujo

| Estado | Valor | Descripción |
|---|---|---|
| Borrador | `draft` | Embarque creado, sin contenedores |
| Confirmado | `confirmed` | Contenedores asignados, booking registrado |
| Embarcado | `in_transit` | Zarpe confirmado, stock rebajado |
| Entregado | `delivered` | Embarque finalizado en destino |
| Cancelado | `cancelled` | Embarque anulado |

### Campos de identidad y ruta

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char | Número Embarque (secuencia, default='/', tracking) |
| `bl_number` | Char | N° Bill of Lading |
| `booking_reference` | Char | N° Booking/Reserva |
| `voyage_id` | Many2one → shipping.voyage | N° Viaje (referencia) |
| `vessel_id` | Many2one → shipping.vessel | Motonave/Barco |
| `port_loading` | Char | Puerto de Carga |
| `port_discharge` | Char | Puerto de Descarga |
| `port_destination` | Char | Destino Final |
| `estimated_departure` | Datetime | ETD — Fecha Zarpe estimada |
| `actual_departure` | Datetime | Fecha Real Zarpe |
| `estimated_arrival` | Datetime | ETA — Fecha Llegada estimada |
| `customer_id` | Many2one → res.partner | Cliente/Consignatario |
| `notes` | Text | Observaciones |
| `state` | Selection | Estado del flujo (ver tabla anterior) |

### Relaciones

| Campo | Tipo | Descripción |
|---|---|---|
| `container_ids` | One2many → lumber.container | Contenedores del embarque |
| `shipment_line_ids` | One2many → lumber.shipment.line | Líneas de auditoría/detalle |
| `document_ids` | One2many → lumber.shipment.document | Documentos adjuntos |
| `cost_line_ids` | One2many → lumber.shipment.cost.line | Líneas de costo |
| `shipping_rule_id` | Many2one → lumber.shipping.rule | Regla de cubicación |

### Totales calculados

| Campo | Tipo | Descripción |
|---|---|---|
| `container_count` | Integer | Cantidad de contenedores |
| `total_volume_m3` | Float (16,3) | Volumen de embarque (geométrico neto, ver Manifiesto/BL) |
| `total_nominal_volume_m3` | Float (16,3) | Volumen físico de compra (verdad de stock) |
| `total_volume_mbf` | Float (16,3) | Volumen comercial total en MBF |
| `total_weight_kg` | Float (16,1) | Peso bruto total de la carga |
| `total_packages` | Integer | Total de paquetes/tarjas |
| `lot_count` | Integer | Total de lotes únicos en todos los contenedores |
| `yield_variance_m3` | Float | Diferencia: `total_volume_m3 - total_nominal_volume_m3` |
| `yield_efficiency_pct` | Float | Eficiencia: `(embarque / compra) × 100` |

### Costos

| Campo | Tipo | Descripción |
|---|---|
| `currency_id` | Many2one → res.currency | Moneda (default: compañía) |
| `total_shipment_costs_usd` | Monetary | Suma de todas las líneas de costo |
| `total_cost_per_m3` | Monetary | `total_shipment_costs_usd / total_volume_m3` |
| `cost_distribution_state` | Selection | `pending` / `distributed` |

### Checklist documental

| Campo | Tipo | Descripción |
|---|---|
| `booking_confirmed` | Boolean + `booking_date` | Booking confirmado |
| `vgm_submitted` | Boolean + `vgm_date`, `vgm_total_weight` | VGM (SOLAS) enviado |
| `bl_received` | Boolean + `bl_date` | Bill of Lading recibido |
| `customs_cleared` | Boolean + `customs_date`, `customs_reference` | Aduana despachada |
| `invoice_issued` | Boolean + `invoice_date`, `invoice_number` | Factura emitida |
| `container_seals` | Text | Sellos de contenedores |
| `document_status` | Selection | `pending` / `partial` / `complete` (computed) |
| `document_completion` | Float % | Progreso documental (computed) |

### UI

| Campo | Tipo | Descripción |
|---|---|
| `picking_count` | Integer | Cantidad de albaranes de salida vinculados |

### Métodos computados

| Método | Depende de | Computa |
|---|---|---|
| `_compute_totals` | `container_ids.volume_m3`, `container_ids.total_volume_purchase_m3`, `container_ids.gross_weight_kg`, `container_ids.tare_weight_kg`, `container_ids.packages`, `container_ids.volume_mbf` | `container_count`, `total_volume_m3`, `total_nominal_volume_m3`, `total_volume_mbf`, `total_weight_kg`, `total_packages` |
| `_compute_lot_totals` | `container_ids.lot_ids` | `lot_count` |
| `_compute_cost_totals` | `cost_line_ids.amount_usd`, `total_volume_m3` | `total_shipment_costs_usd`, `total_cost_per_m3` |
| `_compute_yield_analysis` | `total_volume_m3`, `total_nominal_volume_m3` | `yield_variance_m3`, `yield_efficiency_pct` |
| `_compute_document_completion` | `booking_confirmed`, `vgm_submitted`, `bl_received`, `customs_cleared`, `invoice_issued` | `document_completion` |
| `_compute_document_status` | `document_completion` | `document_status` |
| `_compute_picking_count` | — (busca stock.picking por origin) | `picking_count` |

### Transiciones de estado

| Método | Transición | Detalle |
|---|---|---|
| `action_confirm` | draft → confirmed | Valida: contenedores asignados, `booking_reference` presente, `vessel_id` asignado |
| `action_set_in_transit` | confirmed → in_transit | Valida: contenedores no están en `empty`/`loading`. Ejecuta `_action_reduce_stock` (crea y valida pickings de salida). Pone contenedores en `shipped`. Registra `actual_departure`. Calcula rendimiento final |
| `action_deliver` | in_transit → delivered | Solo si está en tránsito |
| `action_print_packing_list` | — | Imprime packing list consolidado de contenedores |
| `action_view_shipment_lots` | — | Abre vista de lotes con pivot (list/pivot/form) |
| `action_view_picking` | — | Abre albaranes de salida asociados |

### `@api.constrains`
- `_check_dates`: `estimated_arrival` debe ser posterior a `estimated_departure`

### Comportamiento especial
- `write()` intercepta duplicados en `container_ids` (evita OwlError al vincular contenedores ya presentes)
- `create()` (override desde `lumber_document_checklist.py`): auto-genera documentos checklist para cada `lumber.document.checklist` activo
- `vgm_total_weight` se auto-calcula en `_compute_totals`: `total_weight_kg + suma de tare_weight_kg`
- `shipping.vessel` y `shipping.voyage` son modelos de `madenat_lumber_shipping_core` (dependencia externa)

---

## lumber.container

### Herencia usada

```python
class LumberContainer(models.Model):
    _name = 'lumber.container'
    _description = 'Contenedor de Exportación'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
```

**SQL constraints:** `name_unique`, `seal_uniq` (seal_number + shipment_id)

### Estados del flujo

| Estado | Valor | Descripción |
|---|---|---|
| Vacío | `empty` | Sin lotes asignados |
| Cargando | `loading` | Lotes siendo asignados |
| Cargado | `loaded` | Carga completada, pendiente sellado |
| Sellado | `sealed` | Sello naviera colocado |
| Embarcado | `shipped` | En tránsito con el embarque |

### Campos de identidad

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char (unique, required) | Número de contenedor (ej: CAIU7063234) |
| `shipment_id` | Many2one → lumber.export.shipment | Embarque padre (ondelete=restrict) |
| `container_type` | Selection | `20`, `40`, `40HC`, `45` (default=40HC) |
| `seal_number` | Char | Sello de seguridad naviera |
| `sag_seal` | Char | Sello SAG (puede ingresarse post-zarpe) |
| `vessel_id` | Many2one → shipping.vessel (related) | Motonave (desde shipment_id, readonly) |
| `notes` | Text | Observaciones adicionales |

### Relaciones

| Campo | Tipo | Descripción |
|---|---|
| `line_ids` | One2many → lumber.shipment.line | Líneas de embarque (fuente de verdad) |
| `lot_ids` | Many2many → stock.lot | Lotes físicos (computed/inverse, store=True) |

### Pesos

| Campo | Tipo | Descripción |
|---|---|
| `tare_weight_kg` | Float (computed) | Peso tara vacío (según container_type: 20=2280, 40=3740, 40HC=4150, 45=4800) |
| `weight_kg` | Float | Peso neto de la carga |
| `gross_weight_kg` | Float (computed) | VGM: `weight_kg + tare_weight_kg` |
| `max_weight_kg` | Float (computed) | Capacidad máxima de carga (payload) |
| `max_gross_weight_kg` | Float (computed) | Peso bruto máximo ISO |

### Volúmenes

| Campo | Tipo | Descripción |
|---|---|
| `volume_m3` | Float (16,3) | Alias de `total_vol_shipment_m3` (volumen físico real) |
| `volume_mbf` | Float (16,4) | Suma de MBF de todos los lotes |
| `total_vol_shipment_m3` | Float (16,3) | Vol. Físico Real (Facturable) — base para facturación |
| `total_volume_purchase_m3` | Float (16,3) | Vol. Nominal (Referencia Costo) |
| `volume_variance_pct` | Float (16,2) | Desviación: `(físico - nominal) / nominal × 100` |
| `max_volume_m3` | Float (computed) | Capacidad máxima según tipo (20=33, 40=67, 40HC=76, 45=86) |

### Cantidades

| Campo | Tipo | Descripción |
|---|---|
| `packages` | Integer | Etiquetas únicas (`ref` distinct) del contenedor |
| `total_pieces` | Integer | Suma de piezas individuales (tablas) |
| `lot_count` | Integer | Cantidad de lotes asignados |

### Capacidad restante

| Campo | Tipo | Descripción |
|---|---|
| `remaining_volume_m3` | Float | `max_volume_m3 - volume_m3` (mínimo 0) |
| `remaining_weight_kg` | Float | `max_weight_kg - weight_kg` (mínimo 0) |

### UI / Kanban

| Campo | Tipo | Descripción |
|---|---|
| `fill_percentage` | Float | % llenado basado en factor limitante (peso vs volumen) |
| `status_color` | Integer | Semáforo: 1=verde(<50%), 2=amarillo(50-90%), 3=naranja(90-100%), 4=rojo(sellado) |

### Fechas

| Campo | Tipo | Descripción |
|---|---|
| `loading_date` | Datetime | Fecha inicio carga (readonly) |
| `sealing_date` | Datetime | Fecha sellado (readonly) |

### Métodos @api.depends

| Método | Depende de | Computa |
|---|---|---|
| `_compute_tare_weight` | `container_type` | `tare_weight_kg` |
| `_compute_max_capacity` | `container_type` | `max_weight_kg`, `max_gross_weight_kg`, `max_volume_m3` |
| `_compute_gross_weight` | `weight_kg`, `tare_weight_kg` | `gross_weight_kg` |
| `_compute_volume_totals` | `line_ids`, `lot_ids.vol_shipment_m3`, `lot_ids.volume_purchase_m3`, `lot_ids.volumen_m3` | `total_vol_shipment_m3`, `total_volume_purchase_m3`, `volume_m3`, `volume_variance_pct` |
| `_compute_volume_mbf_from_lots` | `lot_ids.volumen_mbf` | `volume_mbf` |
| `_compute_packages_from_lots` | `lot_ids.ref` | `packages` (etiquetas únicas) |
| `_compute_total_pieces_from_lots` | `lot_ids.piezas` | `total_pieces` |
| `_compute_lot_ids` | `line_ids` | `lot_ids` (sincroniza O2M → M2M) |
| `_compute_remaining_capacity` | `volume_m3`, `max_volume_m3`, `weight_kg`, `max_weight_kg` | `remaining_volume_m3`, `remaining_weight_kg` |
| `_compute_fill_percentage` | `weight_kg`, `max_weight_kg`, `volume_m3`, `max_volume_m3` | `fill_percentage` |
| `_compute_status_color` | `fill_percentage`, `state` | `status_color` |
| `_compute_lot_count` | `lot_ids` | `lot_count` |
| `_compute_totals` | `lot_ids`, `lot_ids.ref`, `lot_ids.vol_shipment_m3` | `lot_count`, `packages`, `total_pieces`, `total_volume_m3` |

### Transiciones de estado

| Método | Transición | Detalle |
|---|---|---|
| `action_start_loading` | empty → loading | Registra `loading_date` |
| `action_complete_loading` | loading → loaded | Valida: tiene lotes asignados. Registra `packages`, `total_pieces`, `volume_m3` en el mensaje |
| `action_seal` | loaded → sealed | Valida: `seal_number` ingresado, `gross_weight_kg > 0`, tiene lotes/paquetes. Registra `sealing_date` |
| `action_assign_lots` | — | Abre wizard `lumber.container.lot.wizard` |
| `action_manage_rollover` | — | Abre wizard `lumber.container.rollover.wizard` |
| `action_view_lots` | — | Abre vista de lotes asignados |
| `action_remove_lot_granular` | — | Desvincula un lote: revierte `logistic_cost_usd`, actualiza `estado_trazabilidad` → `en_patio`, recalcula embarque |
| `action_export_packing_list_xlsx` | — | Genera Excel del packing list con agrupación por proveedor |

### Comportamiento especial
- `_inverse_lot_ids()`: al escribir en `lot_ids`, crea/borra `lumber.shipment.line` automáticamente. Al agregar lote: setea `container_id` y `estado_trazabilidad = 'consolidado'`. Al quitar lote: libera `container_id` y `estado_trazabilidad = 'en_patio'`
- `create()` y `write()`: si se modifican campos sensibles (`lot_ids`, `packages`, `gross_weight_kg`, `volume_m3`, `shipment_id`, `state`), dispara recálculo de totales y costos del embarque padre
- `fill_percentage` usa el factor limitante: `max(peso%, volumen%)`

---

## lumber.shipment.line

### Herencia usada

```python
class LumberShipmentLine(models.Model):
    _name = 'lumber.shipment.line'
    _description = 'Línea de Detalle de Embarque (Packing List Item)'
    _order = 'container_id, id'
```

Sin estados propios. Sin `@api.constrains`.

### Campos

| Campo | Tipo | Descripción |
|---|---|---|
| `shipment_id` | Many2one → lumber.export.shipment | Embarque padre (required, ondelete=cascade) |
| `container_id` | Many2one → lumber.container | Contenedor (ondelete=cascade) |
| `lot_id` | Many2one → stock.lot | Lote/Tarja (required) |
| `physical_volume_m3` | Float (related → lot_id.volumen_m3) | Volumen real del lote (readonly) |
| `export_width_inches` | Float (computed) | Ancho en pulgadas: `ancho_mm / 25.4` |
| `export_volume_m3` | Float (computed) | Volumen comercial según `shipping_rule_id` |
| `display_label` | Char (computed) | Etiqueta simplificada: `supplier_label` o sufijo de `lot.name` |

### Métodos @api.depends

| Método | Depende de | Computa |
|---|---|---|
| `_compute_export_dims` | `lot_id`, `lot_id.ancho_mm` | `export_width_inches` |
| `_compute_export_volume` | `lot_id`, `shipment_id.shipping_rule_id`, `lot_id.espesor_mm`, `lot_id.largo_m`, `lot_id.piezas` | `export_volume_m3` |
| `_compute_display_label` | `lot_id`, `lot_id.name` | `display_label` |

### Lógica de `export_volume_m3`
- Si el embarque está finalizado (`done`/`sealed`/`shipped`): no recalcula
- Si no hay `shipping_rule_id`: usa `physical_volume_m3` como fallback
- Si `calculation_method = 'nominal_plus_allowance'`: aplica recargo (`allowance_inches`) al ancho nominal
- Calcula: `(espesor_mm × ancho_ajustado_mm × largo_m × piezas) / 1.000.000`

---

## lumber.document.checklist

### Herencia usada

```python
class LumberDocumentChecklist(models.Model):
    _name = 'lumber.document.checklist'
    _description = 'Checklist Documental de Exportación'
    _order = 'sequence, id'
```

Catálogo de tipos de documentos requeridos. No tiene estado propio.

### Campos

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char (required) | Nombre del documento (ej: "Bill of Lading", "VGM", "Factura") |
| `sequence` | Integer | Orden de visualización (default=10) |
| `is_required` | Boolean | Si es obligatorio (default=True) |
| `description` | Text | Instrucciones para el documento |
| `active` | Boolean | Si está activo (default=True) |

---

## lumber.shipment.document

### Herencia usada

```python
class LumberShipmentDocument(models.Model):
    _name = 'lumber.shipment.document'
    _description = 'Documento de Embarque'
```

### Estados

| Estado | Valor | Descripción |
|---|---|---|
| Pendiente | `missing` | Sin archivo adjunto |
| Adjunto | `attached` | Archivo subido |
| Verificado | `verified` | Verificado manualmente (no retrocede si se borra el archivo) |

### Campos

| Campo | Tipo | Descripción |
|---|---|
| `shipment_id` | Many2one → lumber.export.shipment | Embarque (ondelete=cascade) |
| `checklist_id` | Many2one → lumber.document.checklist | Tipo de documento |
| `name` | Char (computed, editable) | Nombre autocompletado desde `checklist_id.name` |
| `file_data` | Binary | Archivo adjunto |
| `file_name` | Char | Nombre del archivo |
| `state` | Selection (computed) | Estado del documento |
| `notes` | Text | Notas adicionales |

### Métodos @api.depends

| Método | Depende de | Computa |
|---|---|---|
| `_compute_name` | `checklist_id` | `name` (autocompleta si está vacío) |
| `_compute_state` | `file_data` | `state`: `attached` si hay archivo, `missing` si no (respeta `verified`) |

---

## lumber.shipping.rule

### Herencia usada

```python
class LumberShippingRule(models.Model):
    _name = 'lumber.shipping.rule'
    _description = 'Regla de Cubicación de Exportación'
    _order = 'sequence, id'
```

Define cómo se calcula el volumen de embarque para cada lote.

### Campos

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char (required) | Nombre (ej: "Exportación USA (Nominal + 1/8)") |
| `sequence` | Integer | Orden (default=10) |
| `active` | Boolean | Activo (default=True) |
| `calculation_method` | Selection | `metric_actual`, `nominal_plus_allowance`, `nominal_exact` |
| `allowance_inches` | Float (default=0.125) | Sobreancho en pulgadas (ej: 1/8") |

### `@api.constrains`
- `_check_allowance`: `allowance_inches` no puede ser negativo

### Métodos de cálculo
- `metric_actual`: usa dimensiones físicas reales del lote
- `nominal_plus_allowance`: convierte ancho mm → pulgadas → aplica `allowance_inches` → convierte de vuelta a mm
- `nominal_exact`: usa dimensiones nominales sin recargo

---

## lumber.shipment.cost.line

### Herencia usada

```python
class LumberShipmentCostLine(models.Model):
    _inherit = 'lumber.shipment.cost.line'
```

Extiende el modelo base con campos de distribución de costos.

### Campos

| Campo | Tipo | Descripción |
|---|---|
| `shipment_id` | Many2one → lumber.export.shipment | Embarque (required, ondelete=cascade) |
| `distribution_method` | Selection | `volume` (default), `weight`, `packages`, `equal` |
| `is_distributed` | Boolean (computed) | True si existen `stock.lot.cost.line` referenciando esta línea |

### Método computed

| Método | Lógica |
|---|---|
| `_compute_is_distributed` | Busca `stock.lot.cost.line` con `source_shipment_cost_line_id = self.id`. Si count > 0: `True` |

---

## Restricciones conocidas del módulo

- `action_set_in_transit` **bloquea** el embarque si algún contenedor está en `empty` o `loading` — todos deben estar al menos `loaded` o `sealed`
- `seal_number` es único por embarque (SQL constraint `seal_uniq` en `lumber.container`)
- `name` del embarque es único (SQL constraint `name_uniq` en `lumber.export.shipment`)
- `shipping.voyage` y `shipping.vessel` son modelos de `madenat_lumber_shipping_core` (dependencia externa requerida)
- `lumber.shipment.line` se sincroniza automáticamente desde `container.lot_ids` (inverse `_inverse_lot_ids`)
- El checklist documental se auto-genera al crear un embarque (`create()` override en `lumber_document_checklist.py`)
- `volume_m3` del contenedor es alias de `total_vol_shipment_m3` (volumen físico real, no nominal)
- `status_color` del contenedor: 1=verde (<50%), 2=amarillo (50-90%), 3=naranja (90-100%), 4=rojo (sellado)
- `_action_reduce_stock` crea pickings de salida agrupados por ubicación física real de los lotes (multi-puerto)
- El campo `sag_seal` (Sello SAG) **no se exige** en el sellado — burocráticamente puede llegar hasta una semana después del zarpe
- `fill_percentage` usa el factor limitante entre peso y volumen (`max(peso%, volumen%)`)
- `vgm_total_weight` del embarque se auto-calcula: `total_weight_kg + suma(tare_weight_kg)` de todos los contenedores

---

## Evidencia

- Archivos: `custom_addons/madenat_lumber_logistics/models/` (6 archivos .py con 8 modelos)
- `lumber_export_shipment.py` → `LumberExportShipment`
- `lumber_container.py` → `LumberContainer`
- `lumber_shipment_line.py` → `LumberShipmentLine`
- `lumber_document_checklist.py` → `LumberDocumentChecklist`, `LumberShipmentDocument`, extiende `LumberExportShipment`
- `lumber_shipment_costing.py` → extiende `LumberExportShipment`, `LumberShipmentCostLine`
- `lumber_shipping_rule.py` → `LumberShippingRule`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[flujo_despacho_embarque]]
- [[modelo_lotes]]
- [[dependencias_modulos]]
- [[00_ARQUITECTURA]]
