# Implementación — OC provisional desde guía (FIX 2026-08-21)

## 1. Objetivo
Creación manual, provisional, trazable e idempotente de `purchase.order` desde `madenat.guia.processing` cuando `oc_match_status='not_found'`, delegando en el gatekeeper `validate_or_create_po` de `madenat_lumber_purchasing`.

## 2. Archivos modificados
| Archivo | Razón |
|---|---|
| `madenat_lumber_purchasing/models/purchase_order.py` | Gatekeeper endurecido: `state='draft'` forzado (~392), `partner.exists()+active` (342-345), rechazo `product_uom_unit` para volumen>0 (~572) |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `action_create_purchase_order_from_document` (3175+) delegador |
| `madenat_lumber_core/views/guia_processing_views.xml` | Botón "Crear OC provisional" |
| `madenat_lumber_purchasing/tests/__init__.py` (nuevo) | Registro |
| `madenat_lumber_purchasing/tests/test_po_creation_from_guide.py` (nuevo) | 9 tests |

## 3. Flujo
Botón (not_found + sin order_id) → valida estados → valida partner → payload (partner_ref=oc_reference_raw, origin="Guía #N", ingestion_source_ref="madenat.guia.processing,<id>", lines 1:1 m³ price 0) → `validate_or_create_po(payload,{auto_create:True,provisional:True})` → nota "provisional/precios pendientes" → adjunta PDF → vincula order_id='created' → abre PO draft.

## 4. Seguridad
- SIEMPRE draft; partner activo; líneas 1:1 qty>0 m³; prohibido product_uom_unit; price 0; bloqueo multi_match/needs_review; idempotente por order_id; solo manual.

## 5. UoM
Conversión MBF→m³ con `MBF_TO_M3` (utils_uom.py:84) validada en tests; gatekeeper conserva UoM del producto (m³).

## 6. Anti-duplicado
Capa A: `if order_id: return action_open_po()`. Capa B: `test_double_call` verifica 1 sola PO por ingestion_source_ref.

## 7. Trazabilidad
origin, partner_ref, ingestion_source_ref, nota chatter, oc_match_note.

## 8. Tests
| Suite | Resultado |
|---|---|
| `madenat_lumber_purchasing:TestPOCreationFromGuide` | **9/9 PASS — EXIT=0** |
| `madenat_lumber_core:TestSupplierResolution` | 3 FAIL preexistentes (ver §9) |

## 9. Riesgos
- 3 fallos preexistentes de TestSupplierResolution (`_resolve_or_create_supplier`) por residuo en BD (partner id=676, VAT 77066489-6, activo de corrida previa sin rollback 15:13) — ajeno al flujo OC provisional.
- Conversión MBF interna en gatekeeper: diferida a decisión humana.
- `action_send_to_stock`, parsers, cron y costeo NO modificados.

## 10. Operación manual
Guía not_found + proveedor → botón "Crear OC provisional" → PO draft con líneas m³, precio 0, nota revisión. Confirmar precios/proveedor manualmente antes de confirmar.