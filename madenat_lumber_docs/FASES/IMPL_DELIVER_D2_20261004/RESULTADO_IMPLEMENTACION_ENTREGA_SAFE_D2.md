# MADENAT — Resultado Implementación Entrega Segura D2

- **Sub-bloque 5 — Entrega y Cierre seguro de Embarque. Política D2 (Entrega logística controlada).**
- **Fases B/C:** implementación + update + tests. **Sin UAT, sin Costeo, sin Facturación, sin Pagos, sin R3.**
- **Método:** edición de archivos autorizados → `git diff --check` → `-u madenat_lumber_core,madenat_lumber_logistics`
  (`--stop-after-init --no-http`) → ejecución exclusiva de `TestShipmentDeliverySafe`.
- **Fecha:** 2026-10-04. Evidencia en `IMPL_DELIVER_D2_20261004/` (`00_precheck_impl.txt`, `01_update.log`,
  `02_tests.log`, `03_test_results.txt`, `04_git_integrity.txt`).

---

## 1. Precheck y conservación (`00_precheck_impl.txt`)
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree | **33 = 24 M + 9 ??** (antes de editar) |
| `git diff --check` | **CLEAN** |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · DB `madenat_test` |
| Rol uid 8 (Cristhian) | Operaciones + Jefatura; sin Gerencia/Contabilidad/System |
| Rol uid 6 (Leonardo) | lectura/reportes (sin grupos MADENAT) |
| Estados | **delivered = 0** · doc `pending` 16 · costos `distributed` 0 |
| P0 confirmados | write directo a `delivered` posible; `action_deliver` sin audit; `action_confirm` sin guard |

## 2. Política D2 implementada
`in_transit → delivered` **sólo** con: gate físico/B-01 + gate documental aprobado (o waiver de Gerencia
auditado) + rol autorizado + exclusivamente por `action_deliver`. **No** exige `cost_distribution_state`,
factura, pago ni consolidación (se registran como pendientes en el snapshot). Helper documental
`_delivery_document_status()` (READ-ONLY) devuelve `status ∈ {approved,pending,missing,not_configured}` y
las listas de ids. Como el modelo documental no expone aprobación humana separada, se usa la **evidencia
real** (`state ∈ attached/verified`) y, en su ausencia, el **waiver** — **no se simula aprobación**.

## 3. Guard físico/documental/B-01 — `_assert_can_deliver()`
Orden (sin escribir, sin `sudo()`):
1. `_assert_departure_group()` → **Jefatura o Gerencia**.
2. `_assert_no_rebaja_inconsistency()` → P0 (`reversed` sin retorno total).
3. `state == 'in_transit'` (bloquea draft/confirmed/delivered/cancelled).
4. `_b01_blocks_delivery()` → bloquea B-01 **open** (permite **resolved** sin pendientes).
5. `_classify_departure_containers()` → bloquea **pendientes** de rebaja física.
6. `_delivery_document_status()` ≠ `approved` **y** sin waiver válido → **bloqueado**.

## 4. Waiver de Gerencia
Campos nuevos en `lumber.export.shipment` (readonly): `delivery_waiver_state`,
`delivery_waiver_reason`, `delivery_waiver_approved_at`, `delivery_waiver_approved_by_id`,
`delivery_waiver_audit_id`. Acción `action_approve_delivery_waiver(reason=False)`: **sólo Gerencia**;
exige `in_transit`, sin B-01 open, sin pendientes, sin inconsistencias, **motivo ≥ 20** caracteres;
**no** cambia `state`; produce auditoría `delivery_waiver` (SHA-256) + chatter. Un waiver válido habilita
la Entrega cuando el gate documental no está aprobado.

## 5. Protección de writes (P0-1)
En `write()`: `state='delivered'` → `_assert_delivery_write_authorized()`; `state='confirmed'` →
`_assert_confirm_write_authorized()`; campos waiver → `_assert_delivery_waiver_write_authorized()`.
Tokens **efímeros de proceso** (`_DELIVERY_WRITE_TOKENS`, `_DELIVERY_WAIVER_TOKENS`, `_CONFIRM_WRITE_TOKENS`)
acuñados SÓLO tras el guard y consumidos una vez. `with_context(allow_delivery=True)` **no elude**
(el token es un set en memoria, no un contexto). **Nota de diseño:** el superusuario (`env.su`, código
interno/tests) conserva la vía de escape estándar de Odoo; la protección aplica a **todo actor RPC/real**
(`su=False`) — así se preservan los suites aprobados (R1/R2/B-01/Rolleo/Borrador) que fijan estado como
superusuario sin romper su comportamiento.

## 6. Auditoría / hash / chatter (P0-2)
- `madenat.audit.log.action_type` **+** `('shipment_delivery','Entrega de Embarque')` y
  `('delivery_waiver','Waiver de Entrega')` (aditivo).
- Helpers `_delivery_snapshot()`, `_audit_delivery()`, `_delivery_waiver_snapshot()`, `_audit_delivery_waiver()`
  con `json.dumps(payload, sort_keys=True, default=str)` y `hashlib.sha256(...).hexdigest()`.
- El snapshot de Entrega incluye operation/actor, shipment (state_before/after, vessel, voyage, B-01,
  document status, waiver state), containers (state + clasificación + pending), `physical_checks`
  (no_b01_open, no_pending, no_inconsistency, return_chain_consistent), `financial_status`
  (cost/month,invoices,payments,consolidations) y `write=['state']`.
- Se crea con `.sudo().create()` **sólo** para la auditoría; si algo falla, la transacción revierte completa.

## 7. UI (`lumber_export_shipment_views.xml`)
- Botón **Entregar** (Jefatura/Gerencia, `invisible state != 'in_transit'`) con `confirm` claro.
- Botón **Aprobar Waiver de Entrega** (sólo Gerencia, `in_transit`, sin B-01 open) con `confirm` claro.
- Panel readonly **🔒 Entrega Segura (D2)**: B-01, waiver (estado/motivo/fecha/usuario/audit) y aviso si
  no hay documentación aprobada. Sintaxis Odoo 18 (`invisible=`, `readonly=`); **sin** `attrs=`/`states=`/`<tree>`.

## 8. Resultado update (`01_update.log`)
`-u madenat_lumber_core,madenat_lumber_logistics --stop-after-init --no-http` → **OK**:
`Modules loaded.` · `Registry loaded in 26.033s` · `Initiating shutdown`. **Sin** `ERROR`/`CRITICAL`/
`Traceback`/`ParseError`. Verificado post-update: selección con los 2 valores nuevos; 5 campos waiver
presentes; `delivered=0`; auditorías nuevas=0; conteos intactos.

---

## 9. Resultado de tests — `TestShipmentDeliverySafe` (`02_tests.log`, `03_test_results.txt`)
**`0 failed, 0 error(s) of 13 tests`** (13/13 PASS):

| Test | Qué valida | Resultado |
|---|---|---|
| **T-DLV-1** `dlv_01` | in_transit + física limpia + doc aprobado → **delivered**; audit `shipment_delivery` con SHA-256 + chatter; sin cambios físicos/financieros | **PASS** |
| **T-DLV-2** `dlv_02` | B-01 **open** → bloqueado (sigue `in_transit`, sin audit) | **PASS** |
| **T-DLV-3** `dlv_03` | B-01 **resolved** sin pendientes + doc aprobado → permitido | **PASS** |
| **T-DLV-4** `dlv_04` | física **pendiente** y rebaja **inconsistente** → bloqueado | **PASS** |
| **T-DLV-5** `dlv_05` | `document_status` pending/missing sin waiver → bloqueado | **PASS** |
| **T-DLV-6** `dlv_06` | waiver Gerencia (motivo válido) → `approved` + audit SHA-256 + chatter; **Jefatura** puede entregar | **PASS** |
| **T-DLV-7** `dlv_07` | Operaciones/Jefatura **no** pueden aprobar waiver (`AccessError`) | **PASS** |
| **T-DLV-8** `dlv_08` | usuario no autorizado (plain/Operaciones) → `AccessError` | **PASS** |
| **T-DLV-9** `dlv_09` | `write({'state':'delivered'})` directo **y** con contexto falso → bloqueado | **PASS** |
| **T-DLV-10** `dlv_10` | write directo de campos waiver (con contexto) → bloqueado | **PASS** |
| **T-DLV-11** `dlv_11` | `action_confirm`: draft→confirmed por Operaciones OK; write directo confirmed bloqueado; terminal/B-01 bloqueado; usuario sin rol bloqueado | **PASS** |
| **T-DLV-12** `dlv_12` | Entrega **no** modifica stock/picking/quant/lote/costos/finanzas/SV | **PASS** |
| **T-DLV-13** `dlv_13` | reintento sobre `delivered` → bloqueado; **sin** audit/chatter adicional | **PASS** |

> Los tests usan `TransactionCase` con fixtures aislados; **nada se persiste**. (13 tests = T-DLV-1..13.)

## 10. Integridad stock/finanzas/SV/UAT (post-update y post-tests)
Conteos idénticos a la línea base (delta **0**): `stock.move`=145 · `stock.move.line`=212 · `stock.picking`=30 ·
`stock.quant`=173 · `stock.lot`=128 · `stock.lot.cost.line`=53 · `lumber.shipment.cost.line`=0 ·
`lumber.export.shipment`=16 · `lumber.container`=17 · `shipping.vessel`=8 · `account.move`=1 ·
`account.payment`=0 · `lumber.billing.consolidation`=0 · `madenat.sv.operation`=1 · `madenat.sv.imputation`=1 ·
`madenat.audit.log`=273.
**`delivered` = 0 · filas con waiver = 0 · auditorías `shipment_delivery`/`delivery_waiver` = 0.**
UAT histórica/Rolleo/Borrador/B-01/R1/R2 **no tocadas**. Rol/ACL sin cambios.

## 11. Exclusiones (no ejecutadas)
R3 / imputación SV · retorno parcial · Costeo · Facturación · Pagos · consolidación · BT-04/Maquila ·
Entrega real · UAT. No se usó `sudo()` funcional, ni SQL de escritura, ni scripts de reparación, ni
migraciones; no se creó UAT ni se modificaron roles.

## 12. Archivos y control de alcance
| Archivo | Tipo |
|---|---|
| `madenat_lumber_core/models/madenat_audit_log.py` | **M** (autorizado) — 2 `action_type` nuevos |
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | **M** (autorizado) — D2: campos, guards, actions, auditoría |
| `madenat_lumber_logistics/views/lumber_export_shipment_views.xml` | **M** (autorizado) — botones + panel D2 |
| `madenat_lumber_logistics/tests/__init__.py` | **M** (autorizado) — import del test |
| `madenat_lumber_logistics/tests/test_shipment_delivery_safe.py` | **??** (autorizado, nuevo) |

Git: rama/HEAD **sin cambios**; `git diff --check` **CLEAN**; WT 33→**34** (sólo +1 archivo nuevo). Los demás
archivos `M` del árbol ya venían modificados del baseline (sub-bloques previos) y **no** fueron tocados aquí.

## 13. Dictamen

### **A. `ENTREGA SEGURA D2 IMPLEMENTADA — APTO PARA SOLICITAR UAT`**

- **P0-1** cerrado: `delivered`/`confirmed`/waiver sólo por acción autorizada (token de proceso; RPC directo
  bloqueado, `with_context` no elude).
- **P0-2** cerrado: auditoría append-only con snapshot determinista + SHA-256 para `shipment_delivery` y
  `delivery_waiver`, más chatter.
- **P0-3** cerrado: `action_confirm` restringido (Operaciones/Jefatura/Gerencia), sólo `draft → confirmed`,
  bloquea terminal/B-01 y write directo.
- Gate físico/B-01 + gate documental + **waiver de Gerencia** implementados; UI clara; 13 tests aislados
  **13/13 PASS**; integridad intacta; update limpio.

**Riesgos residuales (para la UAT):**
1. **Waiver sin wizard:** el motivo se aporta por la acción autorizada (`action_approve_delivery_waiver(reason=...)`);
   un `wizard/` dedicado queda como mejora futura (wizards no autorizados en este bloque).
2. **`create()` con `state='delivered'`:** la protección cubre `write()` (foco P0-1); crear un embarque
   directamente en `delivered` no está bloqueado por `create()` (residual; puede requerir guard futuro).
3. **Documento "aprobado" = evidencia cargada** (`attached`/`verified`); no hay aprobación humana firmada
   por documento — el waiver cubre la ausencia.
4. **Gerencia en runtime:** la UAT deberá definir un usuario Gerencia (no se creó ninguno en este bloque).

*Se detiene aquí. No se creó UAT. No se ejecutó Entrega real. No se modificaron roles. Sin commit/push.
Fin del informe.*
