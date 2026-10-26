# MADENAT — Resultado Implementación B-01 Documental Bloqueante

```
Documento : RESULTADO_B01 (Sub-bloque 3 - Zarpe con excepción B-01, Política B)
Fase      : B/C — Implementación + Update + Tests (sin UAT, sin regularización
            física, sin movimiento de inventario)
Entorno   : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha     : 2026-10-04 (15:47–15:52 UTC)
Dictamen  : A. B-01 DOCUMENTAL BLOQUEANTE IMPLEMENTADO — APTO PARA SOLICITAR UAT
```

---

## 1. Precheck final y conservación del working tree
- Repo `/custom_addons`; rama `feat/guia-correccion-documental-preservada-20261002`;
  HEAD `34c81272bb07d48db98d73a7734c81a2a8e384fa` (sin cambios).
- **Antes de editar:** `git status --porcelain` = 25 (21 M + 4 ??). Roles de Rolleo y
  Borrador Seguro preservados sin revertir.
- **Después:** 28 entradas = 23 M (21 previos + 2 autorizados nuevos:
  `wizards/lumber_shipment_zarpe_wizard.py`, `wizards/lumber_shipment_zarpe_wizard_views.xml`)
  + 5 ?? (4 previos + `tests/test_shipment_b01_exception.py` nuevo). Ningún archivo fuera
  de la lista autorizada. Sin commit/push/PR/reset/checkout/rebase/stash/branch.
- P0 activo confirmado antes (`lumber_export_shipment.py:507`); 0 eventos B-01/deviation
  persistidos antes de empezar.

## 2. Archivos modificados y propósito
| Archivo | Propósito |
|---|---|
| `models/lumber_export_shipment.py` | Campos B-01; guard `_assert_can_depart`; `_set_in_transit` seguro (P0); `action_set_in_transit`; `action_deliver` con gates; auditoría B-01; protección write/import |
| `wizards/lumber_shipment_zarpe_wizard.py` | Guardas de grupo; flujo normal vs. B-01; motivo >= 20 |
| `views/lumber_export_shipment_views.xml` | Botón zarpe (Jefatura/Gerencia, sin B-01); bloque B-01 readonly; botón Entregar restringido |
| `wizards/lumber_shipment_zarpe_wizard_views.xml` | Advertencia B-01 + confirmación explícita |
| `tests/test_shipment_b01_exception.py` | T-B01-1..12 (nuevo) |
| `tests/__init__.py` | Registro del test |
| `madenat_lumber_core/models/madenat_audit_log.py` | Valor `b01_departure_exception` al Selection |

**No modificados** (excluidos): `lumber_container.py`, `lumber_shipment_line.py`,
`lumber_vessel_rollover_wizard.py`, `security/*`, `__manifest__.py`, `shipping_core/*`,
`costing/*`, `billing/*`, `vendor_payment/*`, `toll_processing/*`.

## 3. Corrección demostrada del P0 `shipped` sin rebaja
- **Eliminado** `self.container_ids.write({'state': 'shipped'})`
  (`grep` → `NO_P0`).
- Reemplazado por clasificación por evidencia física real
  (`_is_container_rebajado_fisico`: `state='rebajado'` o `line.rebaja_state='rebajado'`
  o picking de rebaja `done`) y **sólo** los rebajados pasan a `shipped`:
  `rebajados.write({'state': 'shipped'})` (línea 646). Los **pendientes no se tocan**.
- Evidencia por tests: T-B01-3 (contenedor pendiente conserva `loaded`), T-B01-1 (rebajado→shipped),
  T-B01-11 (Δ0 stock).

## 4. Contrato de zarpe normal vs. B-01
- **Normal** (`_set_in_transit()`, Jefatura/Gerencia): exige 0 pendientes; rebajados→`shipped`;
  `shipment.state='in_transit'`; `actual_departure=now`; `b01_exception_state='none'`; sin B-01.
- **B-01** (`_set_in_transit(is_b01=True)`, Jefatura/Gerencia): exige ≥1 pendiente y motivo ≥20;
  rebajados→`shipped`; **pendientes conservan su estado**; `in_transit`; se abre B-01 `open`
  (motivo/fecha/usuario/audit) + auditoría; gates bloqueados. `action_set_in_transit` requiere
  rol de apertura, valida contexto y, con pendientes, abre el asistente (no zarpa solo).

## 5. Campos operativos B-01 y protección contra writes directos
- Campos añadidos SÓLO a `lumber.export.shipment`: `b01_exception_state`
  (`none`/`open`/`resolved`, default `none`, index), `b01_exception_reason`, `b01_exception_opened_at`,
  `b01_exception_opened_by_id`, `b01_exception_audit_id` (readonly, copy=False).
- **Protección write()**: `if any(f in vals for f in B01_WRITE_FIELDS): self._assert_b01_write_authorized(vals)`.
  Token efímero de proceso `_B01_WRITE_TOKENS` (clave `dbname,uid,id`), NO un contexto público.
  Bloquea `resolved` y cualquier write directo (RPC/import/cliente).
- **Protección create()**: rechaza fijar campos B-01 al crear el Embarque.
- Evidencia: T-B01-9 (contexto no elude), T-B01-12 (write directo a open/resolved/motivo/audit
  bloqueado).

## 6. Auditoría B-01 append-only con hash y chatter
- Nuevo `action_type='b01_departure_exception'` ("Zarpe con Excepción B-01") en `madenat.audit.log`.
- `_create_b01_exception_audit` usa `.sudo().create()` SÓLO para el modelo de bitácora; snapshot
  determinista JSON (`sort_keys=True`) con `operation` (action_type/timestamp/actor/reason),
  `shipment` (id/name/state_before='confirmed'/state_after='in_transit'/vessel/voyage),
  `containers_rebajados`, `containers_pendientes` (con lotes/rebaja_state/picking),
  `physical_invariants` (no_stock_movement/no_quant_change/no_picking_created = true) y
  `exception.state='open'` + `gates` (draft/rollover/delivery/costing/billing/payments = blocked).
- `audit_hash = sha256(snapshot)`; `batch_id = shipment.id`; se asigna a
  `b01_exception_audit_id`; se crea en la MISMA transacción (si falla, revierte).
- Compatibilidad AD-88: se conserva la desviación textual `deviation` (borrador seguro textual).
- Chatter explícito de la excepción + pendientes. Evidencia: T-B01-3 (hash, snapshot, chatter).

## 7. Gates implementados: zarpe y Entrega
- **Zarpe** (`action_set_in_transit`): rol de apertura (Oper/Jef/Ger) + contexto (estado
  `confirmed`, sin B-01 abierta/resolved, viaje no terminal, sin costos distribuidos ni
  consolidación facturada). `_set_in_transit`/`_assert_can_depart` exige **Jefatura/Gerencia**.
- **Entrega** (`action_deliver`): exige **Jefatura/Gerencia**; bloquea si `b01_exception_state in
  ('open','resolved')` o si hay Contenedores pendientes. Evidencia: T-B01-6, T-B01-8.
- **No** se modificaron Borrador Seguro ni Rolleo (la marca `b01_exception_state='open'` queda
  disponible para integraciones futuras).

## 8. Resultado de update
```
docker exec odoo18_app odoo --config /etc/odoo/odoo.conf --database madenat_test \\
  -u madenat_lumber_core,madenat_lumber_logistics --stop-after-init --no-http
```
- Resultado: `Modules loaded.` + `Registry loaded in 23.997s` + `Initiating shutdown`.
- **0** incidencias `ERROR/CRITICAL/Traceback`.
- Columnas B-01 creadas en `lumber_export_shipment`; vista del formulario recargada
  (1 `ir.ui.view` con `b01_exception_state`). Módulos en estado `installed`.
  (No se usó `-i`, ni SQL de escritura, ni migraciones, ni reinicio de contenedor.)

## 9. Resultado individual de T-B01-1 a T-B01-12
Comando: `odoo -d madenat_test --test-enable --test-tags
/madenat_lumber_logistics:TestShipmentB01Exception --stop-after-init --no-http`.
Resumen: **`0 failed, 0 error(s) of 12 tests`** (12 post-tests en 3.51s).

| Test | Propósito | Resultado |
|---|---|---|
| T-B01-1 `test_01_normal_zarpe_all_rebajados` | zarpe normal → in_transit; rebajados→shipped; B-01 none; Δ0 | PASS |
| T-B01-2 `test_02_normal_zarpe_with_pending_blocks` | normal con pendiente → UserError; sin cambios; sin B-01 | PASS |
| T-B01-3 `test_03_b01_with_pending` | B-01 → in_transit; rebajado shipped; pendiente conserva estado; B-01 open + campos + audit/hash/chatter; Δ0 | PASS |
| T-B01-4 `test_04_b01_without_pending_blocks` | B-01 sin pendiente → UserError | PASS |
| T-B01-5 `test_05_b01_short_reason_blocks` | motivo ausente/<20 → UserError | PASS |
| T-B01-6 `test_06_b01_blocks_delivery` | B-01 bloquea action_deliver; sigue in_transit | PASS |
| T-B01-7 `test_07_b01_open_blocks_retry` | B-01 abierta bloquea reintento de zarpe | PASS |
| T-B01-8 `test_08_permissions` | Operaciones/Auditoría/común → AccessError | PASS |
| T-B01-9 `test_09_rpc_context_cannot_bypass` | contexto/with_context y write directo no eluden | PASS |
| T-B01-10 `test_10_error_leaves_everything_intact` | error no modifica shipment/container/line/stock/audit | PASS |
| T-B01-11 `test_11_no_physical_or_financial_side_effects` | normal y B-01 Δ0 en stock/costos/facturas/pagos/SV | PASS |
| T-B01-12 `test_12_b01_fields_not_directly_writable` | campos B-01 no editables (open/resolved/motivo/audit) | PASS |

## 10. Evidencia de cero movimiento físico y financiero
Línea base ANTES del update == DESPUÉS de update y tests (los tests son `TransactionCase`,
revierten):

| Modelo | Valor |
|---|---|
| stock.move | 142 |
| stock.move.line | 209 |
| stock.picking | 27 |
| stock.quant | 169 |
| stock.lot | 126 |
| lumber.export.shipment | 11 |
| lumber.container | 11 |
| lumber.shipment.line | 5 |
| madenat.audit.log | 263 |
| account.move | 1 |
| account.payment | 0 |
| madenat.sv.operation | 1 |
| madenat.sv.imputation | 1 |
| stock.lot.cost.line | 53 |
| lumber.billing.consolidation | 0 |

Sin filas nuevas de test: usuarios `b01_%`=0, embarques `B01-%`=0, audits `b01_departure_exception`=0,
`deviation`=0 tras la corrida. (T-B01-11 valida Δ0 explícitamente dentro de los tests.)

## 11. Integridad de UAT histórica, Rolleo y Borrador Seguro
- Shipment 1537 `in_transit`; Container 1509 `shipped`; Picking 7065 `done`; Línea 1880
  `rebajado` → intactos.
- UAT Rolleo (vessels 619/620, voyage 565, shipments 1644/1645/1646, containers 1629/1630/1631,
  audits 19699–19704) y UAT Borrador Seguro (shipments 1704–1707, containers 1678–1680,
  audit 19742) sin cambios (conteos globales idénticos).
- No se tocaron Borrador Seguro ni Rolleo de Motonave (código intacto).

## 12. Exclusiones confirmadas
- **Regularización B-01:** NO implementada (`resolved` bloqueado; sin acción UI).
- **Borrador Seguro, Rolleo de Motonave, Retorno SV, Costeo, Facturación, Pagos, BT-04:**
  no modificados.
- No se creó UAT; no se ejecutó rebaja física, zarpe real ni movimiento de inventario fuera de
  los tests aislados (que revierten).

### Nota de alcance — autorización complementaria pendiente (no bloqueante para este dictamen)
Dos tests preexistentes en `madenat_lumber_logistics/tests/test_rebaja_contenedor.py`
(**archivo NO autorizado en esta entrega**) codifican el comportamiento ANTERIOR a la Política B y,
por diseño, quedan obsoletos:
- `test_14_zarpe_wizard_excepcion_registra_desviacion` asserta `container.state == 'shipped'` tras
  B-01 (contradice la corrección del P0).
- `test_15_zarpe_wizard_rebajar_y_zarpar` ejecuta el zarpe normal como **Operaciones** (ahora
  requiere Jefatura/Gerencia).

No se modificaron (fuera de la lista autorizada). Se **solicita autorización complementaria** para
actualizar esas dos aserciones al nuevo contrato (medida: alinear `test_14` a «pendiente conserva su
estado» y `test_15` a ejecutar como Jefatura/Gerencia). La validación de esta entrega se ejecutó
únicamente con los tests B-01 (12/12 PASS), según lo indicado.

## 13. Dictamen
> **A. `B-01 DOCUMENTAL BLOQUEANTE IMPLEMENTADO — APTO PARA SOLICITAR UAT`.**
>
> P0 corregido (no se marca `shipped` a Contenedores pendientes); contrato normal vs. B-01
> implementado; campos B-01 con protección anti-write directo; auditoría append-only
> `b01_departure_exception` con snapshot/hash/chatter; gates de zarpe y Entrega; update limpio
> (0 errores) y **12/12 tests B-01 PASS**. Cero movimiento físico/financiero; histórica, Rolleo y
> Borrador Seguro intactos.
>
> Único pendiente (no bloqueante): autorización complementaria para actualizar 2 aserciones obsoletas
> en `test_rebaja_contenedor.py` (§12).

---

**No se creó UAT. No se avanzó a Retorno SV ni Entrega/Cierre. Sin commit/push/PR/reset/checkout/
rebase/stash/branch.**
