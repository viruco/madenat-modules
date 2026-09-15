# Investigación — Creación/vinculación de `purchase.order` desde guía/recepción cuando no existe OC coincidente

**Fecha:** 2026-08-21
**Modalidad:** Solo lectura. Única escritura: este documento.
**Regla de negocio innegociable:** "El sistema no debe inventar ni crear automáticamente una purchase.order sin trazabilidad suficiente."

## 1. Métodos localizados

### 1.1 `madenat_guia_processing.py` (Procesados)

| Método | Línea | Propósito |
|---|---|---|
| `_create_basic_purchase_order(ref, ingestion_source_ref='')` | 3043 | PO mínima en `draft` con `partner_id`, `currency_id`, `date_order`; preserva `ingestion_source_ref` |
| `action_create_purchase_order_from_document()` | 3175 | Manual-asistido: valida `oc_reference_raw` y `partner_id`, extrae del PDF de OC, crea PO draft, adjunta PDF, vincula `order_id` con `oc_match_status='created'`. NO confirma. NO crea líneas. |

Bloque desactivado `lumber_reception.py:2372-2377` (PATCH 2026-06-18): autocreación automática deshabilitada por generar OCs sin supervisión, valores hardcode y sin trazabilidad. Fallback activo: `manual_po_name` + `oc_match_status='not_found'`.

### 1.2 `lumber_reception.py` (Producto)

| Método | Línea | Propósito |
|---|---|---|
| `_find_or_create_po_intelligent(dg_data, oc_data)` | 2251-2400 | Extrae `po_ref`, normaliza, persiste `oc_reference_raw`, **bloquea sin partner/supplier_rut** (2291-2300), busca PO por `partner_ref` OR `name` normalizado. NO crea PO (bloque desactivado). |

### 1.3 `madenat_lumber_purchasing`

| Archivo | Clase | Destacado |
|---|---|---|
| `purchase_order.py` | `PurchaseOrderLumber` (`_inherit='purchase.order'`) | Campos madera, `ingestion_source_ref`, `provisional`. **`validate_or_create_po(payload, policy)` = GATEKEEPER** (289): valida partner, busca por `partner_ref+partner_id+company_id`, crea `draft` provisional. `_create_po_lines_with_validation` (498). |
| `lumber_reception.py` | `LumberReceptionPurchasing` | `_find_po_and_supplier` (17), `_create_supplier_from_guide` (121), `_create_po_from_guide` (132, **DEPRECATED**). |
| `purchase_intake.py` | `PurchaseIntake` (AbstractModel) | `ensure_master_product()` (MADERA_GENERICA, uom m³, tracking lot). |

## 2. Comparativa de matching

| Aspecto | Procesados (`_match_purchase_order`) | Producto (`_find_or_create_po_intelligent`) |
|---|---|---|
| Campo PO comparado | **solo `name`** normalizado | **`partner_ref` OR `name`** |
| Dominio | `state in [draft,sent,purchase,done]` + `partner_id` si resuelto | `partner_id` + `state in [draft,sent,to approve,purchase,done]` |
| Partner ausente | `needs_review` (no auto-vincula) | `UserError` (2291-2300) |
| Multi-match | `multi_match`, sin vínculo | `[:1]` (riesgo) |
| Cero match | `not_found` | `manual_po_name` + `not_found` |
| Creación PO | NO (manual) | NO (desactivada) |

## 3. Dependencias para PO válida

| Campo PO | Origen MADENAT |
|---|---|
| `partner_id` | `guia.partner_id` / `reception.supplier_id` |
| `date_order` | `now` |
| `currency_id` | `guia.currency_id` / company |
| `state` | **SIEMPRE `draft`** (provisional) |

Mapeo de líneas: `processing_line_ids`/`reception_line_ids` → `product_id`, `product_qty` (vol), `price_unit` (derivado de `additional_cost/service_volume_m3`), `product_uom` (m³). Método existente `_create_po_from_guide` usa `uom.product_uom_unit` con m³ (inconsistencia a corregir).
## 4. Evaluación de opciones arquitectónicas

| Criterio | a) Método en guia_processing | b) Wizard en madenat_lumber_purchasing | c) Wizard en Intake |
|---|---|---|---|
| Trazabilidad | Buena | **Excelente** (`ingestion_source_ref`+`provisional`) | Buena |
| Regla no-autocreación | Cumple (duplica líneas) | **Cumple** (gatekeeper exige partner/líneas) | Cumple |
| Reutilización | Baja | **Alta** | Media |
| Esfuerzo | Bajo/medio | **Medio** | Alto |
| Riesgo tests | Medio | **Bajo** | Medio |

**RECOMENDACIÓN: opción b)** — delegar `action_create_purchase_order_from_document` (core 3175) al gatekeeper `validate_or_create_po` (purchasing 289), reutilizando `_create_po_lines_with_validation` (498). Mantiene ownership único, `draft`+provisional, y no toca core salvo delegación del método manual ya activo.

## 5. Flujo propuesto (diseño, sin implementar)

```text
[Botón manual en vista guía: "Crear OC desde documento" (draft/verified)]
  │
  ▼
1. Validación partner previa: guia.partner_id / reception.supplier_id
   (si falta → UserError claro, igual que 2291-2300)
  │
  ▼
2. Construir payload PO (en madenat_lumber_purchasing):
   { partner_id, partner_ref (oc_reference_raw|manual_po_name),
     currency_id, date_order=now, origin="Guía #{name}",
     ingestion_source_ref=oc_reference_raw,
     lines: 1:1 desde processing_line_ids|reception_line_ids
       {product_id, product_qty (vol), price_unit, product_uom (m³)} }
  │
  ▼
3. policy = {auto_create: True, provisional: True} → SIEMPRE draft
  │
  ▼
4. Llamar PurchaseIntake.validate_or_create_po(payload, policy)
  │
  ▼
5. Trazabilidad:
   - ingestion_source_ref = oc_reference_raw
   - Nota PO: "Creada desde Guía #{name}, requiere revisión manual"
   - Vínculo: guia.order_id = po.id | reception.purchase_id = po.id
   - oc_match_status = 'created'
  │
  ▼
6. Abrir formulario PO (draft) para revisión humana
```

Restricciones: estado SIEMPRE draft; punto de entrada manual (nunca en action_verify_data ni cron); guard anti-duplicado si order_id/purchase_id ya existe.

## 6. Tests nuevos requeridos (antes de implementar)

En `custom_addons/madenat_lumber_purchasing/tests/test_po_creation_from_guide.py`:

| Método propuesto | Caso |
|---|---|
| `test_create_po_with_partner_resolved_creates_draft` | Partner resuelto → PO `draft` con líneas, `oc_match_status='created'` |
| `test_create_po_without_partner_blocks` | Sin partner → `UserError`, sin PO creada |
| `test_create_po_multiple_lines_maps_1to1` | Varias líneas → N líneas en `purchase.order.line` |
| `test_double_call_no_duplicate_po` | Doble llamada → no duplica (guard por order_id existente) |
| `test_po_always_draft` | Nunca `purchase`/`sent` |
| `test_lines_use_m3_uom` | `product_uom` correcto (m³) |
| `test_ingestion_source_ref_preserved` | `ingestion_source_ref` = `oc_reference_raw` |

## 7. Archivos a modificar/crear (cuando se apruebe)

| Acción | Ruta | Cambio |
|---|---|---|
| Crear | `madenat_lumber_purchasing/models/po_creation_guide.py` | Método `_create_po_from_guia` en `PurchaseOrderLumber` (validaciones + payload + gatekeeper) |
| Modificar | `madenat_lumber_purchasing/models/purchase_order.py` | Extender `validate_or_create_po` para aceptar `lines` con `product_uom` explícito |
| Modificar | `madenat_lumber_core/models/madenat_guia_processing.py` | `action_create_purchase_order_from_document` (3175) → delegar al gatekeeper purchasing |
| Crear | `madenat_lumber_purchasing/views/po_creation_guide_views.xml` | Botón en guía + wizard (si aplica) |
| Modificar | `madenat_lumber_purchasing/models/__init__.py` | Registrar modelo |
| Crear | `madenat_lumber_purchasing/tests/test_po_creation_from_guide.py` | Tests sección 6 |
| Modificar | `madenat_lumber_purchasing/tests/__init__.py` | Registrar test |

## 8. Decisiones de diseño (humanas)

1. `TransientModel` vs método en `PurchaseOrderLumber` → recomendación: método + botón en guía.
2. `product_uom` m³ vs unidad → recomendación: m³ (`vol_purchase_m3`/`vol_shipment_m3`).
3. Precio de línea: derivar `additional_cost/service_volume_m3` si >0, si no `0` con nota.
