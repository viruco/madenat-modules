# MADENAT — Resultado Micro-Parche P0 Create Entrega D2

- **Sub-bloque 5 — Entrega Segura D2. Micro-parche P0: cierre de la puerta lateral `create()`.**
- **Fase C.1:** seguridad + update + tests. **Sin UAT, sin Entrega real, sin movimiento de inventario.**
- **Método:** sólo 2 archivos autorizados → `git diff --check` → `-u madenat_lumber_logistics
  --stop-after-init --no-http` → ejecución exclusiva de `TestShipmentDeliverySafe`.
- **Fecha:** 2026-10-04. Evidencia en `IMPL_DELIVER_D2_C1_20261004/`.

---

## 1. Precheck e integridad (`00_precheck.txt`)
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree | **34 = 24 M + 10 ??** (esperado) |
| `git diff --check` | **CLEAN** |
| Runtime / DB | `odoo18_app` Up · `odoo18_db` healthy · `madenat_test` |
| Estado | **delivered=0 · waiver rows=0 · auditorías `shipment_delivery`/`delivery_waiver`=0** |
| UAT histórica/Rolleo/Borrador/B-01/R1/R2 | **intactas** |
| Stock/finanzas/SV | sin cambios (`move` 145 · `picking` 30 · `quant` 173 · `lot` 128 · `account.move` 1 · `payment` 0 · SV 1/1 · `audit` 273) |

## 2. Puerta lateral identificada
`lumber.export.shipment.create()` (`lumber_export_shipment.py:1639`) sólo bloqueaba los campos B-01
(truthy); **no** bloqueaba `state ∈ {confirmed, in_transit, delivered, cancelled}` ni los campos waiver →
RPC/import podía crear un Embarque directamente en un estado que exige guard, auditoría y transición.
Único caso de creación no-draft en el código: `madenat_lumber_billing/tests/test_billing_consolidation.py:14`
(`state='delivered'`, ejecutado como **superusuario** por `TransactionCase`).

## 3. Protección `create()` implementada
Se extendió `create()` (mismo patrón no falsificable por contextos que `write()`): para cada `vals` y para
**todo actor RPC/import** (`not self.env.su`):
1. `state` no vacío y ≠ `'draft'` → `UserError` (“...utilice el flujo operativo autorizado para confirmar,
   zarpar o entregar”).
2. Cualquier campo de `DELIVERY_WAIVER_FIELDS` → `UserError` (waiver sólo por acción autorizada).
3. Cualquier campo de `B01_WRITE_FIELDS` → `UserError` (excepción sólo por acción autorizada).

Se **permite**: `create` sin `state`, con `state='draft'`, y campos operativos normales. Se conserva el
bloqueo B‑01 existente. **`with_context(allow_create_terminal=True / allow_delivery=True / b01_internal=True)`
NO elude** (la decisión es `env.su`, no un contexto). **Nota de diseño:** el superusuario interno
(código/tests, `env.su=True`) conserva la vía estándar de Odoo —igual que en `write()`— para no romper los
suites aprobados (p. ej. `test_billing_consolidation`). **No** se tocó `action_deliver`, el waiver ni ningún
otro contrato.

## 4. Tests T-DLV-14 a T-DLV-21 (añadidos a `TestShipmentDeliverySafe`)
| Test | Caso | Acción externa (`with_user(user_plain)`) | Resultado esperado | Estado |
|---|---|---|---|---|
| **T-DLV-14** | `create({'state':'confirmed'})` | no-su | `UserError` | **PASS** |
| **T-DLV-15** | `create({'state':'in_transit'})` | no-su | `UserError` | **PASS** |
| **T-DLV-16** | `create({'state':'delivered'})` | no-su | `UserError` | **PASS** |
| **T-DLV-17** | `create({'state':'cancelled'})` | no-su | `UserError` | **PASS** |
| **T-DLV-18** | `create` con `delivery_waiver_state`/`_reason` | no-su | `UserError` | **PASS** |
| **T-DLV-19** | `create` con `b01_exception_state`/`_reason` | no-su | `UserError` | **PASS** |
| **T-DLV-20** | `create` sin `state` y con `state='draft'` | Operaciones | permitido → `state='draft'`; campos operativos conservados | **PASS** |
| **T-DLV-21** | `create` terminal/waiver/B‑01 con **contexto falso** | no-su + `allow_create_terminal/allow_delivery/b01_internal` | `UserError`; **no** crea registros | **PASS** |

Los tests verifican además: **no** nuevo shipment persistido, **no** auditoría, **no** chatter, **no**
stock/finanzas/SV.

## 5. Resultado completo `TestShipmentDeliverySafe` (`02_tests.log`, `03_test_results.txt`)
**`0 failed, 0 error(s) of 21 tests`** → **21/21 PASS** (T-DLV-1…13 previos + T-DLV-14…21 nuevos).

## 6. Update (`01_update.log`)
`-u madenat_lumber_logistics --stop-after-init --no-http` → **OK**: `Modules loaded.` ·
`Registry loaded in 16.716s` · shutdown. **0** `ERROR`/`CRITICAL`/`Traceback`/`ParseError`.

## 7. Integridad post-update/post-tests (`04_integrity.txt`, `05_git_integrity.txt`)
`delivered=0` · `waiver_rows=0` · auditorías `shipment_delivery`/`delivery_waiver`=0.
Conteos idénticos (delta **0**): `move`=145 · `mline`=212 · `picking`=30 · `quant`=173 · `lot`=128 ·
`lot.cost.line`=53 · `shipment.cost.line`=0 · `shipments`=16 · `containers`=17 · `vessels`=8 ·
`account.move`=1 · `account.payment`=0 · `billing.consolidation`=0 · `sv.operation`=1 ·
`sv.imputation`=1 · `audit`=273. UAT histórica/Rolleo/Borrador/B‑01/R1/R2 intactas.
Git: rama/HEAD **sin cambios**; WT **34** (sin archivos nuevos); `git diff --check` **CLEAN**.

### Archivos modificados (sólo autorizados)
| Archivo | Cambio |
|---|---|
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | guard `create()` (state/waiver/B‑01, no-su) |
| `madenat_lumber_logistics/tests/test_shipment_delivery_safe.py` | +T-DLV-14..21 (21 tests) |

No se modificaron `views/*`, `wizards/*`, `security/*`, `__manifest__.py`, `tests/__init__.py`,
`madenat_lumber_core/*` ni los módulos excluidos. No se alteró `action_deliver` ni el waiver.

## 8. Dictamen

### **A. `ENTREGA D2 SIN PUERTAS LATERALES — APTO PARA SOLICITAR UAT`**

- Puerta lateral `create()` **cerrada**: ningún actor RPC/import puede crear un Embarque en
  `confirmed/in_transit/delivered/cancelled` ni fijar campos waiver/B‑01; el contexto público no elude.
- Creación normal (`draft`) **permitida** y con campos operativos conservados.
- **21/21 tests PASS**; update limpio; integridad intacta (delta 0); Git/HEAD sin cambios.

*Se detiene aquí. No se creó UAT. No se ejecutó Entrega real. No se modificaron roles. Sin commit/push.
Fin del informe.*
