# Addendum — Idempotencia OC provisional (FIX guard anti-duplicado)

**Fecha:** 2026-08-21
**Alcance:** Corrección focalizada de producción (guard anti-duplicado). No rediseña UoM ni toca parsers/cron/action_verify_data.

## 1. Problema corregido
Con `auto_create=True`, `validate_or_create_po` podía crear una segunda `purchase.order` para el mismo origen porque la búsqueda previa por `ingestion_source_ref` estaba condicionada a `not auto_create`. La brecha fue identificada en `ANALISIS_IMPACTO_OC_PROVISIONAL_20260821.md`.

## 2. Archivos modificados
| Archivo | Cambio |
|---|---|
| `madenat_lumber_purchasing/models/purchase_order.py` | Búsqueda **incondicional** por `ingestion_source_ref` (draft/sent/purchase/done) antes de `create`; >1 coincidencia → bloqueo (`UserError`); 1 coincidencia → retorno `linked` idempotente sin importar `auto_create` |
| `madenat_lumber_purchasing/tests/test_po_creation_from_guide.py` | 3 tests nuevos: `test_existing_po_by_ingestion_source_ref_is_reused`, `test_multiple_pos_same_ingestion_source_ref_blocks`, `test_origin_with_order_id_existing_reuses_linked_po` |

## 3. Estrategia idempotente implementada
- **Capa A (origen):** `if self.order_id: return action_open_po()` — no duplica la guía ya vinculada.
- **Capa B (compra):** antes de `create`, búsqueda por `ingestion_source_ref` incondicional. `search` sin `limit=1`; usa `len()` para detectar múltiples:
  - 0 → crear.
  - 1 → retornar `{'success': True, 'po_id': existing.id, 'state': 'linked', ...}` (idempotente).
  - >1 → `return {'success': False, 'error': ...}` con nombres de las OCs encontradas.
- **Retorno:** se preserva el `dict` `{success, po_id, state, message, po_name}`; la conexión de la guía con `order_id` permanece intacta.

## 4. Casos cubiertos por tests (12 total)
- **9 originales** (draft, partner activo/inactivo, líneas 1:1, UoM m³, price 0, doble llamada, multi_match/needs_review).
- **3 nuevos:** reuso por `ingestion_source_ref`; bloqueo ante 2 OCs del mismo origen; reuso con `order_id` ya vinculado.

## 5. Resultado de pruebas (aislado, `--stop-after-init --http-port=8899`)
| Suite | Resultado |
|---|---|
| `madenat_lumber_purchasing:TestPOCreationFromGuide` | **12/12 PASS — EXIT=0** ("0 failed, 0 error(s) of 12 tests") |
| Verificación SELECT | **0 OCs provisionales residuales, 0 duplicados por origen** (rollback de tests correcto) |

## 6. Riesgo residual de concurrencia
- No se agregó constraint SQL (inviable hoy porque `ingestion_source_ref` no es único global).
- Entre `search` y `create` persiste una **ventana de concurrencia** teórica (dos requests simultáneos podrían crear ambas POs antes de commitear).
- Mitigación parcial: la lógica retorna `linked` idempotente para la primera coincidencia y bloquea >1; la protección real definitiva requeriría `FOR UPDATE`/advisory lock o constraint parcial — documentado como deuda técnica, no bloqueante para QA/entorno con flujo manual de un solo operador.

## 7. Veredicto actualizado
**QA:** Apto. **Producción:** Apto con control operativo (flujo manual monousuario por guía; sin constraint). El riesgo de concurrencia quedaría mitigado en la práctica por el uso manual del botón.