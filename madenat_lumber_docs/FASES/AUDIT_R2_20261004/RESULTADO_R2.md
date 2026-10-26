# MADENAT — Resultado Implementación R2 Retorno Físico Total

- **Sub-bloque:** 4B — R2 (reversa robusta de rebaja por retorno físico total).
- **Decisión aplicada:** R2-A (fortalecer el helper por Contenedor; **no** sustituir por `stock.return.picking`).
- **Alcance:** Fase B/C — implementación + update + tests. **Sin UAT, sin retorno parcial, sin imputación SV R3, sin Entrega, sin costeo/facturación/pagos.**
- **Fecha:** 2026-10-04.
- **Módulos foco:** `madenat_lumber_logistics`, `madenat_lumber_core` (ledger SV / audit log).
- **Runtime:** `madenat_test`, `odoo18_app` Up, `odoo18_db` healthy, HTTP operativo.

---

## 1. Precheck y conservación

| Ítem | Valor | Estado |
|---|---|---|
| Repo git | `custom_addons/` (raíz git; **NO** `odoo-18-ce/`) | ✅ |
| Rama | `feat/guia-correccion-documental-preservada-20261002` | ✅ |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` | ✅ |
| Working tree (pre) | **31 entradas** (23 ` M` + 8 `??`) | ✅ coincide |
| Working tree (post) | **33 entradas** (24 ` M` + 9 `??`) — +1 ` M` (wizard) +1 `??` (test) | ✅ sólo autorizados |
| Contenedores | `odoo18_app` Up, `odoo18_db` Up (healthy) | ✅ |

**Línea base global (read-only, idéntica antes y después):** `stock_move` 143 ·
`stock_move_line` 210 · `stock_picking` 28 · `stock_quant` 171 · `stock_lot`
127 · `lumber_export_shipment` 15 · `lumber_container` 16 ·
`lumber_shipment_line` 6 · `madenat_audit_log` 270 · `madenat_sv_operation` 1 ·
`madenat_sv_imputation` 1 · `stock_lot_cost_line` 53 ·
`lumber_shipment_cost_line` 0 · `lumber_billing_consolidation` 0 ·
`account_move` 1 · `account_payment` 0.

**Registros protegidos (intactos, sin modificar):** shipment `1885`
(`in_transit`/`resolved`), container `1888` (`rebajado`, `state_before_rebaja =
sealed`), lot `16312`, picking `7238` (`done`), move `13973` (`done`), audit
`19941` (`deviation` B-01) y `19945` (`b01_resolution`).

**Confirmaciones:** no `rebaja_reverse` persistida (0 filas); no retorno R2
persistido; `rebaja_state` en líneas = `{rebajado:5, pending:1}` (sin `reversed`);
helper actual y sus líneas auditadas presentes; ninguna UAT modificada.

---

## 2. Archivos modificados

Todos dentro de la lista autorizada:

| Archivo | Cambio |
|---|---|
| `madenat_lumber_core/models/madenat_audit_log.py` | + `action_type` aditivo `('rebaja_return_total', 'Retorno Físico Total de Rebaja')`. |
| `madenat_lumber_logistics/models/lumber_container.py` | Guard `_assert_can_reverse_rebaja_total` (+ `_context` / `_financial`), `_rebaja_reverse_lock` (FOR UPDATE NOWAIT), idempotencia relacional (`_rebaja_return_moves_of`, `_rebaja_move_return_complete`, `_rebaja_return_total_complete`, `_rebaja_return_pickings_of`), reescritura de `_reverse_rebaja_container` / `_reverse_rebaja_picking` / `action_reverse_rebaja`, verificación `_assert_rebaja_return_valid`, auditoría `_rebaja_return_total_snapshot/_audit`, campos `rebaja_origin_picking_names` / `rebaja_return_picking_names`. |
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | `_container_rebaja_classification` (active/compensated/inconsistent/none), `_is_container_rebajado_fisico` (evidencia activa), `_assert_no_rebaja_inconsistency` (P0) + invocación en `_assert_departure_context` y `action_deliver`. |
| `madenat_lumber_logistics/wizards/lumber_container_rebaja_reverse_wizard.py` | Contexto de retorno (estado, B-01, OUT/IN), help de motivo ≥ 20, mensaje de confirmación. |
| `madenat_lumber_logistics/views/lumber_container_views.xml` | Aviso B-01 `resolved`/gates, bloque OUT→IN, `confirm` reforzado del botón y vista heredada del asistente (contexto OUT/IN). |
| `madenat_lumber_logistics/tests/test_rebaja_return_total.py` | **Nuevo**: T-R2-1 … T-R2-12. |
| `madenat_lumber_logistics/tests/__init__.py` | Registro de `test_rebaja_return_total`. |

**Nota de alcance:** la vista del propio asistente
(`wizards/lumber_container_rebaja_reverse_wizard_views.xml`) **no** figura en la
lista autorizada, por lo que **no se modificó**: la UI del asistente (cadena
OUT→IN) se implementó como **vista heredada dentro del archivo autorizado**
`views/lumber_container_views.xml`, respetando «no cambios fuera de archivos
autorizados».

---

## 3. P0 corregidos

- **P0-1 (no-`done` silencioso):** `_reverse_rebaja_picking` ya **no** devuelve
  `False`; exige `picking.state == 'done'` y lanza `UserError`. Los estados de
  línea/contenedor se escriben **sólo después** del retorno físico total validado.
- **P0-2 (clasificación):** `_is_container_rebajado_fisico` usa evidencia
  **activa** (línea `rebajado` o OUT `done` **sin** retorno total validado por
  `origin_returned_move_id`); una rebaja compensada deja de clasificarse activa.
- **P0-3 (dobles retornos):** idempotencia **relacional**
  (`origin_returned_move_id` / `return_id`) + bloqueo de fila `FOR UPDATE NOWAIT`;
  reintento = no-op.
- **P0-4 (gates):** bloqueo por B-01 `open`, B-01 `resolved` (sólo Gerencia +
  motivo ≥ 20), costos distribuidos, costos atribuibles al lote, costos con
  factura/pago, consolidación facturada, delivered/viaje cancelado (override de
  Gerencia) y usuario no autorizado.

## 4. Contrato R2 total implementado

Contenedor `rebajado` + líneas con OUT `done` + sin retorno previo + autorización
+ sin gates incompatibles → `FOR UPDATE NOWAIT` → **guard** → por cada OUT `done`:
picking IN (`Customers` → ubicación interna de origen, `return_id`); un move por
move_origen con **mismo producto/UoM/cantidad/lote** y `origin_returned_move_id`,
`to_refund=True` (sin efecto contable en flujo sin factura/SO) →
confirm/assign/validate → **verificación** (`return_done`, cantidades totales,
lotes) → **sólo entonces**: `line.rebaja_state='reversed'`,
`container.state = state_before_rebaja or 'loaded'`, `sv_reverse_allocation` (si
aplica), auditoría `rebaja_reverse` + `rebaja_return_total`, chatter. **No** se
permite retorno parcial ni alteración manual de quants/lotes.

## 5. Idempotencia / concurrencia

- Dedupe **relacional**: `_rebaja_return_total_complete(out)`; si el retorno ya
  existe completo se reutiliza (no se crea un segundo picking).
- Reintento a nivel contenedor: si `state != 'rebajado'` y las líneas `reversed`
  tienen retorno total → **no-op idempotente** (`_rebaja_return_result`).
- Concurrencia: `SELECT id FROM lumber_container WHERE id=%s FOR UPDATE NOWAIT`;
  ante `LockNotAvailable` → `UserError` legible. Savepoint por retorno y rollback
  total ante error (patrón del ledger SV).
- **No** depende del texto `origin` (se conserva `'Return of …'` sólo como texto
  informativo).

## 6. Clasificación de rebaja física activa vs. compensada

`lumber.export.shipment._container_rebaja_classification(container)`:

| Resultado | Regla |
|---|---|
| `active` | línea `rebajado`, o OUT `done` **sin** retorno total validado. |
| `compensated` | OUT `done` + retorno total `done` (histórico y auditorías preservados). |
| `inconsistent` | `reversed` **sin** retorno total validado → **P0**. |
| `none` | sin evidencia de rebaja. |

`_is_container_rebajado_fisico` ⇒ `True` sólo para `active`/`inconsistent`;
`_assert_no_rebaja_inconsistency` bloquea los gates de zarpe y Entrega ante
`inconsistent`. No se pierde historia: OUT, retorno y auditorías permanecen.

## 7. B-01 / finanzas / terminalidad

- **B-01 `open`** → reversa bloqueada (incluso Gerencia), no se reabre.
- **B-01 `resolved`** → sólo Gerencia + motivo ≥ 20; se registra el impacto en la
  auditoría R2; **no** se reabre ni se altera `b01_exception_state`.
- **Costos distribuidos**, **`stock.lot.cost.line` atribuible**, **costo con
  factura/pago** y **consolidación facturada** → bloqueado.
- **Embarque `delivered`** o **viaje `cancel`** → override de Gerencia con motivo
  (auditado, `B-03`/`B-06`).

## 8. Auditoría / hash / chatter

- Nuevo `action_type` aditivo `rebaja_return_total` (retorno físico total) en
  `madenat.audit.log`; se conserva además `rebaja_reverse` (compatibilidad R1).
- Snapshot JSON **determinista** (`sort_keys`, `default=str`) con: `operation`
  (action_type, timestamp, actor, reason/override_reason), `container`
  (id/name, state_before/after, shipment, b01_state), `origin_pickings`,
  `return_pickings` (Customers → interno), `moves` (origin_move_id,
  return_move_id[s], product, quantity, lot_id, origin_returned_move_id) y
  `checks` (origin_done, return_done, quantities_total_match, lots_match,
  idempotency_status, physical_rebaja_active_after=false).
- Firma `audit_hash` = SHA-256 del snapshot; `batch_id` = container + line IDs;
  `user_id`. `.sudo().create()` **sólo** para `madenat.audit.log`.
- Emisión en la **misma transacción** posterior a la validación física; si algo
  falla → rollback completo. Chatter en el Contenedor.

## 9. Resultado update

```
docker exec odoo18_app odoo --config /etc/odoo/odoo.conf \
  --database madenat_test \
  -u madenat_lumber_core,madenat_lumber_logistics \
  --stop-after-init --no-http
```
→ `Modules loaded` · `Registry loaded in 27.446s` · **EXIT=0** · sin
`ERROR`/`CRITICAL`. Únicas trazas: `UserWarning` **preexistentes** de
`madenat.lumber.intake.console` (ajenas a R2).

## 10. Resultado T-R2-1 … T-R2-12

`--test-tags /madenat_lumber_logistics:TestRebajaReturnTotal` →
**`0 failed, 0 error(s) of 12 tests`** · **EXIT=0**.

| Test | Objetivo | Resultado |
|---|---|---|
| T-R2-1 | Retorno total real: quant interno +3, Customers 0, mismo lote, línea `reversed`, contenedor `loaded`, audit hash válido. | ✅ |
| T-R2-2 | `origin_returned_move_id` correcto; producto/UoM/cantidad/lote = origen; `Customers → destino interno`. | ✅ |
| T-R2-3 | Reintento no duplica pickings/moves/quants/SV/auditoría. | ✅ |
| T-R2-4 | OUT no `done` → `UserError`; estados sin cambio; nunca `return False`. | ✅ |
| T-R2-5 | Error inducido → rollback total (sin `reversed`, sin retorno, sin SV, sin audit de éxito). | ✅ |
| T-R2-6 | Usuario no autorizado → `AccessError`. | ✅ |
| T-R2-7 | B-01 `open` → bloqueado (Jefatura y Gerencia). | ✅ |
| T-R2-8 | B-01 `resolved` → sólo Gerencia + motivo ≥ 20; audit registra impacto; no reabre/altera B-01. | ✅ |
| T-R2-9 | costos distribuidos / costo atribuible / consolidación facturada → bloqueado. | ✅ |
| T-R2-10 | OUT `done` + retorno full + `reversed` ⇒ no activa; `reversed` sin retorno ⇒ inconsistencia (bloquea). | ✅ |
| T-R2-11 | Lote SV `volume`: retorno físico primero, **una** `rebaja_reverse`, `origin_operation_id` correcto, ledger `sv_rebajado_m3=0`. | ✅ |
| T-R2-12 | No modifica `shipment.state`, B-01, costo/factura/pago/entrega. | ✅ |

> Cobertura SV: el fixture técnico **sí** existe y se usó sin simular datos
> (no se requirió documentar límite).

## 11. Integridad de stock, SV, finanzas y UAT

Tras update + tests (TransactionCase, rollback): línea base **idéntica** (ver §1);
`rebaja_reverse` persistida = 0; retorno R2 persistido = 0; `rebaja_state` líneas
sin `reversed`; B-01 sin cambios; sin movimientos financieros/SV persistidos;
registros protegidos y UAT (histórica, Rolleo, Borrador, B-01, R1) intactos.

## 12. Exclusiones

- **Retorno parcial:** no implementado (contrato R2 total).
- **R3 / imputación SV documental:** no imputado en la reversa (fuera de alcance).
- **Entrega / Cierre:** no modificada (sólo se consume la nueva clasificación).
- **Costeo / Billing / Pagos:** no modificados (sólo gates de bloqueo).
- **BT-04:** intacto.
- **No** se tocó `shipment.state`, `b01_exception_state`, costos, facturas, pagos
  ni documentos de entrega.

## 13. Dictamen

### **A. `R2 TOTAL ROBUSTO IMPLEMENTADO — APTO PARA SOLICITAR UAT`**

Los cuatro P0 quedan cerrados; el contrato R2 total, la idempotencia/concurrencia
relacional, la clasificación activa vs. compensada, los gates B-01/financieros/
terminalidad y la auditoría firmada están implementados y verificados con 12/12
tests y update limpio. Sin cambios fuera de los archivos autorizados; sin
regresión de línea base ni UAT.

**Recomendación (UAT):** ejecutar también la suite de regresión de
`madenat_lumber_logistics` (incl. `TestRebajaContenedor`, B-01/R1, Rolleo,
Borrador) antes de promover. En esta entrega **no** se ejecutaron otros suites
por la restricción «Tests permitidos: exclusivamente `TestRebajaReturnTotal`».

*No se creó UAT. No commit/push. No se avanzó a retorno parcial, R3 ni
Entrega/Cierre. Fin del informe.*


