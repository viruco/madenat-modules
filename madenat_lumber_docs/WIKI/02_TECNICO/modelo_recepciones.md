# Modelo de Recepciones — lumber.reception

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar el modelo `lumber.reception` y su integración con `stock.picking` y `lumber.reception.line` para el registro de ingreso físico de madera al sistema MADENAT.

---

## Herencia usada

```python
class LumberReception(models.Model):
    _name = 'lumber.reception'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'madenat.lumber.ingest.mixin']
    _description = '📦 RECEPCIÓN DE MADERA BRUTA DESDE PROVEEDOR'
    _order = 'reception_date desc'
```

---

## Estados del flujo

| Estado | Valor | Descripción |
|---|---|---|
| Borrador | `draft` | Recepción creada, pendiente de archivos |
| Procesando | `processing` | Archivos cargados, en análisis |
| Verificado | `verified` | Validación completada |
| Recibido | `done` | Recepción finalizada, lotes creados |
| Cancelado | `cancel` | Recepción anulada |
| Error | `error` | Error durante el procesamiento |
| Pendiente OC | `pending_link` | Operando sin OC vinculada |

---

## Campos de identidad y core

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char | Número de Guía de Despacho |
| `state` | Selection | Estado del flujo (ver tabla anterior) |
| `reception_date` | Datetime | Fecha de recepción (default: now) |
| `supplier_id` | Many2one → res.partner | Proveedor de la madera |
| `purchase_id` | Many2one → purchase.order | OC vinculada en Odoo |
| `manual_po_name` | Char | Referencia manual de OC si no existe en Odoo |
| `purchase_order` | Char (computed) | Visual: muestra nombre de OC o referencia manual |
| `manual_entry` | Boolean | Activado si falla reconocimiento automático de PDF |
| `ingestion_profile` | Selection | `f5085` (Blacks/Pies), `f1550` (S2S/Métrico), `metric` (Bruta) |
| `location_id` | Many2one → stock.location | Patio de asignación |

---

## Relaciones

| Campo | Tipo | Descripción |
|---|---|---|
| `picking_id` | Many2one → stock.picking | Albarán de recepción generado |
| `invoice_id` | Many2one → account.move | Factura de proveedor vinculada |
| `lot_ids` | One2many → stock.lot | Lotes importados (readonly) |
| `reception_line_ids` | One2many → lumber.reception.line | Líneas de análisis comercial (staging) |
| `audit_log_ids` | One2many → madenat.audit.log | Logs de auditoría |
| `origin_processing_id` | Many2one → madenat.guia.processing | Referencia a guía de procesamiento origen |

---

## Campos de volumen

| Campo | Tipo | Descripción |
|---|---|---|
| `commercial_volume_m3` | Float (16,3) | Volumen declarado en guía de despacho |
| `commercial_volume_mbf` | Float (16,3) | Volumen comercial convertido a MBF (`m3 / 2.36`) |
| `physical_volume_m3` | Float (16,3) | Volumen según packing list (medición física) |
| `physical_volume_mbf` | Float (16,3) | Volumen físico en MBF |
| `total_volume_m3` | Float (16,3) | Volumen total = `commercial_volume_m3` (Regla de Oro) |
| `total_volume_mbf` | Float (16,3) | Suma de MBF de todas las líneas |
| `total_packages` | Integer | Conteo de paquetes (líneas) |
| `volume_variance_percent` | Float (16,2) | Diferencia %: `(físico - comercial) / comercial` |
| `volume_variance_m3` | Float (16,3) | Diferencia absoluta: `físico - comercial` |
| `tolerance_status` | Selection | `ok` (≤2%), `warning` (≤10%), `critical` (>10%) |

---

## Campos de valorización

| Campo | Tipo | Descripción |
|---|---|---|
| `currency_id` | Many2one → res.currency | Moneda local (default: CLP) |
| `usd_currency_id` | Many2one → res.currency | Moneda USD (default: USD) |
| `exchange_rate_date` | Date | Fecha del tipo de cambio |
| `exchange_rate` | Float (12,4) | Tipo de cambio USD/CLP |
| `total_amount_clp` | Float (16,2) | Monto total neto en CLP |
| `total_amount_usd` | Float (16,2) | Monto total en USD (`clp / exchange_rate`) |
| `price_per_m3_usd` | Float (16,2) | Precio unitario por m³ |
| `price_per_mbf_usd` | Float (16,2) | Precio unitario por MBF |
| `average_price_m3` | Float (12,0) | Precio promedio CLP/m³ (`total_clp / vol_comercial`) |

---

## Campos de archivos

| Campo | Tipo | Descripción |
|---|---|---|
| `pdf_file` | Binary (required) | PDF de Guía de Despacho |
| `excel_file` | Binary (required) | Excel Packing List con detalle de lotes |
| `oc_pdf_file` | Binary | PDF de Orden de Compra (requerido si no hay OC en Odoo) |
| `oc_pdf_filename` | Char | Nombre del archivo OC |
| `pdf_filename` | Char | Nombre del PDF guía |
| `excel_filename` | Char | Nombre del Excel |
| `files_ready` | Boolean (computed) | `True` si todos los archivos requeridos están cargados |

---

## Campos de auditoría

| Campo | Tipo | Descripción |
|---|---|
| `audit_snapshot` | Text (readonly) | Snapshot JSON inmutable de datos comerciales |
| `audit_hash` | Char (readonly) | Firma SHA-256 del snapshot |
| `omitted_count` | Integer (computed) | Conteo de omisiones en los logs |
| `log_notes` | Text (readonly) | Registro timestamped del procesamiento |

---

## Campos UI / Flags

| Campo | Tipo | Descripción |
|---|---|
| `reception_summary_html` | Html (computed) | Tabla HTML agrupada por dimensión comercial |
| `po_missing_alert` | Html (computed) | Alerta visual si falta OC vinculada |
| `can_process_reception` | Boolean (computed) | `state == 'draft'` AND `files_ready` |
| `can_reopen_reception` | Boolean (computed) | `state in ('validated', 'done')` AND no hay lotes |
| `can_cancel_reception` | Boolean (computed) | `state in ('draft', 'processing')` |

---

## Métodos computados

| Método | Depende de | Computa |
|---|---|---|
| `_compute_files_ready` | `pdf_file`, `excel_file`, `purchase_id`, `oc_pdf_file` | `files_ready` |
| `_compute_totals` | `reception_line_ids.vol_purchase_m3`, `reception_line_ids.vol_physical_m3`, `reception_line_ids.vol_mbf` | `total_volume_m3`, `physical_volume_m3`, `commercial_volume_m3`, `total_packages`, `total_volume_mbf` |
| `_compute_volume_variance` | `commercial_volume_m3`, `physical_volume_m3` | `volume_variance_percent`, `volume_variance_m3` |
| `_compute_tolerance_status` | `volume_variance_percent` | `tolerance_status` |
| `_compute_usd_amount` | `total_amount_clp`, `exchange_rate` | `total_amount_usd` |
| `_compute_unit_prices` | `total_amount_usd`, `physical_volume_m3`, `physical_volume_mbf` | `price_per_m3_usd`, `price_per_mbf_usd` |
| `_compute_average_price_clp` | `total_amount_clp`, `commercial_volume_m3` | `average_price_m3` |
| `_compute_reception_summary` | `lot_ids` | `reception_summary_html` |
| `_compute_po_missing_alert` | `purchase_id`, `manual_po_name`, `state` | `po_missing_alert` |
| `_compute_purchase_order_display` | `purchase_id`, `manual_po_name` | `purchase_order` |
| `_compute_omitted_count` | `audit_log_ids` | `omitted_count` |
| `_compute_can_process_reception` | `state`, `files_ready` | `can_process_reception` |
| `_compute_can_reopen_reception` | `state`, `lot_ids` | `can_reopen_reception` |
| `_compute_can_cancel_reception` | `state` | `can_cancel_reception` |
| `_compute_commercial_mbf_from_m3` | `commercial_volume_m3` | `commercial_volume_mbf` |

---

## Transiciones de estado

| Método | Acción | Detalle |
|---|---|---|
| `action_reset_to_draft` | any → `draft` | Reseteo completo: elimina Quants → Lotes → Pickings → Staging en una transacción atómica. **Bloquea** si lotes están en contenedor o consolidados |
| `action_cancel` | any → `cancel` | Cancela recepción sin borrar datos |

---

## Restricciones conocidas

- `pdf_file` y `excel_file` son **required=True**: no se puede crear una recepción sin ellos.
- `files_ready` debe ser `True` antes de poder procesar (`can_process_reception`).
- No se puede ejecutar `action_reset_to_draft` si los lotes están en un contenedor (`container_id`) o consolidados (`is_consolidated`).
- El reseteo elimina físicamente (unlink) Quants, Pickings, Lotes y líneas de staging en una transacción con `savepoint()`.
- No hay `@api.constrains` en la cabecera; las validaciones se hacen con `raise UserError` dentro de los métodos `action_*`.
- `ingestion_profile` determina el factor de conversión: `f5085` usa Factor 5085.312 (pies), `f1550` usa Factor 1550.003 (métrico), `metric` usa cálculo volumétrico directo.
- `volume_variance_percent` se guarda con 4 decimales (`r4`) para que el porcentaje tenga 2 decimales visibles (ej: 0.1533 = 15.33%).
- El tipo de cambio se obtiene de las monedas de Odoo (`base.USD._get_conversion_rate`). Si no hay TC válido, el procesamiento se **bloquea** (política financiera).
- `commercial_volume_mbf` es editable manualmente (`readonly=False`) a pesar de ser computed, permitiendo correcciones manuales.

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/models/lumber_reception.py`
- Línea de clase cabecera: ~1100
- Wizard: `custom_addons/madenat_lumber_core/wizard/lumber_reception_mass_update.py`
- Vistas: `custom_addons/madenat_lumber_core/views/lumber_reception_views.xml`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[modelo_lotes]]
- [[flujo_recepcion_madera]]
- [[flujo_compra_madera]]
- [[campos_computados]]
- [[00_ARQUITECTURA]]
