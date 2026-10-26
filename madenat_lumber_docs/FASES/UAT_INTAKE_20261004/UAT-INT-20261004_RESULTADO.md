# MADENAT — Resultado UAT Ingreso de Madera, Inventario y Bodega

```
Documento   : UAT-INT-20261004_RESULTADO
Feature     : Ingreso de Madera → Guías → Lotes → Stock Interno (Recepción/Inventario/Bodega)
Fase        : Validación operativa aislada pre-financiera (Costeo/Billing/Pagos CONGELADOS)
Entorno     : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha       : 2026-10-04
Ejecutor    : uid 8 Cristhian Elgueta — Operaciones + Jefatura (su=False, sin Gerencia/System/Contab.)
Prefijo UAT : UAT-INT-20261004-
Método      : ORM/acciones de servidor vía `odoo shell` como uid 8 (operativa) y uid 6 (bloqueo).
              Commit ÚNICO tras INT-1..3; UAT-INT-4 revertida con rollback (no persiste).
              SIN sudo() funcional, SIN SQL de escritura, SIN uid 1 como actor, SIN update/install.
Evidencia   : ./UAT_INTAKE_20261004/00_precheck_baseline.txt, 01_uat_intake.txt, 02_final_validation.txt
              (crudos: 00_precheck_raw.txt, 01_uat_intake_raw.txt; harness: _uat_intake.py)
Dictamen    : B. UAT BLOQUEADA O FALLIDA — INDICAR ESCENARIO Y ACCIÓN.
              Núcleo operativo UAT-INT-1/2/3 + CDP-V1 APROBADO; UAT-INT-4 con hallazgo de ACL.
```

> **Resultado en una línea:** el núcleo operativo (Guía/Packing → **recepción validada** →
> **lote/tarja** → **stock interno** con picking IN `done`, quant interno positivo, trazabilidad
> proveedor/guía/ubicación/volumen, **corrección documental CDP-V1 sin tocar stock** y
> **backlog documental no bloqueante**) quedó **APROBADO** end-to-end con el actor **uid 8**.
> El escenario **UAT-INT-4 (Permisos)** **NO** se cumple en su criterio literal: la puerta oficial
> de ingreso bloquea al usuario sin Operaciones (AccessError, sin registros), pero una **validación
> directa por ORM/RPC de una guía existente NO se bloquea**, porque `madenat.guia.processing`
> concede `create/write` a `base.group_user` y los usuarios internos no-Operaciones disponibles
> (uid 6/7/9) **son stock users**. Se indica escenario y acción (§7, §11).

---

## 1. Fecha, entorno y rol

- **Fecha/hora de ejecución:** 2026-10-04 (ventana ~00:26 UTC, ≈ 20:26 hora local) · **precheck:** ~00:22 UTC.
- **Entorno:** base `madenat_test`; `odoo18_app` Up; `odoo18_db` healthy (postgres:15); HTTP 200.
- **Git (repo `/custom_addons`):** rama `feat/guia-correccion-documental-preservada-20261002`,
  HEAD `34c81272bb07d48db98d73a7734c81a2a8e384fa`; working tree 47 entradas (33 M + 14 ??) —
  **sin cambios de código/XML/ACL/roles/tests** por parte de esta UAT; **no** commit/push/stash.
- **Actor ejecutor (operativo):** **uid 8** `cristhian.elguetag@gmail.com` «Cristhian Elgueta»
  — `group_madenat_operaciones` + `group_madenat_jefatura_operaciones`, `su=False`,
  `group_madenat_gerencia=False`, `group_system=False`, `group_madenat_contabilidad=False`.
- **Actor bloqueado (probado):** **uid 6** `leonardo@pinelli.com.mx` «Leonardo Rodriguez» —
  **sin** grupos MADENAT operativos (`Operaciones=False`), `su=False`.
- **Aislamiento:** no se usó uid 1 como actor de datos ni `sudo()` funcional (el único `.sudo()`
  presente es **interno al código aprobado** — p. ej. escritura de `madenat.audit.log` — y no es un
  bypass del ejecutor UAT). No SQL de escritura; no `-u`/`-i`.

## 2. Precheck / línea base

### 2.1 Identidad, runtime y módulos
| Ítem | Valor |
|---|---|
| Repo | `custom_addons` (`/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`) |
| Rama / HEAD | `feat/guia-correccion-documental-preservada-20261002` / `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · **HTTP 200** · `madenat_test` |
| Instalados | core 18.0.6.5.0 · intake 18.0.0.11.0 · reception_improvements 18.0.1.0.0 · logistics 18.0.1.6.0 · ingestion_engine 18.0.1.1.0 · toll 18.0.1.0.0 · costing 18.0.1.0.0 · billing 18.0.1.0.0 · vendor_payment 18.0.1.2.0 |
| CDP-V1/Intake runtime | campos `intake_direct_stock`, `volume_pdf_m3`, `volume_detail_line_ids`, `detalle_aplicado` (guía); `criticality`, `responsible_id`, `due_date`, `backlog_state`, `backlog_overdue`, `backlog_attention` (`lumber.shipment.document`); wizard `madenat.guia.processing.documental.correction.wizard` cargado. |

### 2.2 Línea base global (SELECT count, `madenat_test`)
| Modelo | Base0 | Modelo | Base0 |
|---|---:|---|---:|
| `stock.move` | 145 | `madenat.guia.processing` | 9 (draft 1 · verified 2 · validated 6) |
| `stock.move.line` | 212 | `madenat.guia.processing.line` | 72 |
| `stock.picking` | 30 | `lumber.reception` | 7 (done 5 · verified 2) |
| `stock.quant` | 168 | `lumber.export.shipment` | 21 (delivered 2) |
| `stock.lot` | 132 | `lumber.container` | 22 |
| `stock.lot.cost.line` | 53 | `shipping.vessel` / `voyage` | 9 / 2 |
| `madenat.audit.log` | 278 | `lumber.document.checklist` | 6 (required 5) |
| `madenat.sv.operation` / `imputation` | 1 / 1 | `lumber.shipment.document` | 126 |
| `lumber.billing.consolidation` | 0 | `lumber.cost.distribution` | 2 (`is_c2=True`: **0**) |
| `lumber.shipment.cost.line` | 0 | `account.move` / `payment` | 1 / **0** |
| `ir.attachment` | 165 | `res.partner` / `product.product` | 22 / 18 |

### 2.3 Congelamientos financieros verificados (línea base)
`shipment.cost_distribution_state='distributed'` = **0** · `lumber.cost.distribution is_c2=True` = **0** ·
`lumber.shipment.cost.line` = **0** · `account.payment` = **0** · `lumber.billing.consolidation` = **0**.

### 2.4 Premisa de usuarios (hallazgo temprano)
Los **únicos** usuarios internos no-Operaciones son **uid 6 (stock user + stock manager)**,
**uid 7 (stock user)** y **uid 9 (stock user + stock manager)**. **No existe** usuario interno activo
“sin Operaciones **y sin permisos de stock**”. La premisa del mandato “Leonardo uid 6: lectura”
**no se cumple** en este entorno (uid 6 opera stock). Esto condiciona el escenario INT-4 (§7).

## 3. Datos UAT (prefijo `UAT-INT-20261004-`)

| Rol UAT | Modelo | ID | Nombre / valor | Creado por |
|---|---|---:|---|---|
| Proveedor | `res.partner` | 14247 | `UAT-INT-20261004-SUPPLIER` (is_company) | uid 8 |
| Producto | `product.product` | 5341 | `UAT-INT-20261004-PRODUCT` (storable, tracking=lot, UoM m³) | uid 8 |
| Guía / Recepción | `madenat.guia.processing` | 32689 | `UAT-INT-20261004-RECEPTION` (compra, f5085, rate_usd 900) | uid 8 |
| Documento Guía (PDF) | `ir.attachment` | 63623 | `UAT-INT-20261004-GUIA.pdf` | uid 8 |
| Documento Packing (XLSX) | `ir.attachment` | 63624 | `UAT-INT-20261004-PACKING.xlsx` | uid 8 |
| Lote / Tarja | `stock.lot` | 16694 | `UAT-INT-20261004-LOT-01 UATSKU 20261004` | uid 8 (flujo guía) |
| Picking IN | `stock.picking` | 7406 | `EMB-04081` (tipo **`Recepciones`/incoming**, `done`) | uid 8 (flujo guía) |
| Documento backlog | `lumber.shipment.document` | 13420 | `UAT-INT-20261004-PACKING` (missing · backlog completed) | uid 8 |

Se creó **un** lote, **un** picking IN y **un** documento de backlog UAT; **no** se reutilizó guía,
proveedor, lote, picking, cuant ni stock de UAT anteriores o históricos. El prefijo estaba **libre**
(0 coincidencias en el precheck). La “recepción UAT” es la guía `…-RECEPTION`; el “documento Guía/
Packing” son los adjuntos `…-GUIA.pdf` / `…-PACKING.xlsx`.

---

## 4. Recepción física (UAT-INT-1)

**Flujo estándar ejecutado por uid 8:** `create` guía → adjuntar Guía/Packing → línea de staging
(`compra`, dimensiones + nominal) → `state=verified` → `action_validate()`.
Resultado: `ACTION_VALIDATE NO_ERROR`; **`state` = `validated`**.

| Verificación | Resultado | Evidencia |
|---|---|---|
| Lote UAT creado | ✔ `stock.lot` **16694** = `UAT-INT-20261004-LOT-01 UATSKU 20261004` | `01_uat_intake.txt` |
| Picking IN `done` | ✔ `stock.picking` **7406** `EMB-04081` · tipo **`Recepciones` (code=incoming)** · `state=done` | idem |
| Origen/destino | ✔ `supplier` (usage) → `WH/Stock` (usage=internal, id 8) | idem |
| stock.move / move.line con lote UAT | ✔ 1 move + 1 move.line, `lot_id=16694` | idem |
| stock.quant interno positivo | ✔ quant interno **4.0 m³** en `WH/Stock` (id 128) · contrapartida `-4.0` en `supplier` | idem / `02_final_validation.txt` |
| Volumen real coherente | ✔ línea `vol_purchase=4.0`, `vol_shipment=4.003`, `vol_phys=4.0`; lote `volumen_m3=4.0`; move qty 4.0 | idem |
| Proveedor / guía / ubicación trazables | ✔ `partner_id=UAT-INT-20261004-SUPPLIER`; `origin=UAT-INT-20261004-RECEPTION`; `assignment_location=WH/Stock`; `lot.guia_processing_id=32689` | idem |
| Auditoría / chatter | ✔ `madenat.audit.log` **lot_creation** (20379) + **validation_signature** (20380, SHA-256); 3 mensajes de chatter | idem |
| Sin embarque/contenedor/finanzas | ✔ Δ0 `lumber.export.shipment` / `lumber.container` / `account.move` / `account.payment` / cost lines | idem |

## 5. Documentación tardía NO bloqueante (UAT-INT-2)

**Backlog documental** (`lumber.shipment.document`, registro UAT **13420** `UAT-INT-20261004-PACKING`):

| Verificación | Resultado |
|---|---|
| documento = missing → backlog open | ✔ `state=missing`, `backlog_state=open` (al crear) |
| criticidad / responsable / fecha configurables | ✔ `criticality` medium→**high**, `responsible_id=8`, `due_date=2026-12-31`; `backlog_attention=True` |
| escalamiento sin UserError | ✔ `action_backlog_escalate()` → `in_progress`, `escalated_by_id=8` |
| cierre sin UserError | ✔ `action_backlog_complete()` → `completed` |
| **no UserError físico por el pendiente** | ✔ la recepción física **validó** con documentación pendiente |
| OC pendiente no bloqueante (regla AD-54) | ✔ 1 mensaje de chatter «OC pendiente (no bloqueante)» en la guía |
| **stock/lote/picking permanecen coherentes** | ✔ `INT2_DELTA`: solo `lumber.shipment.document +1`; **Δ0** en move/move.line/picking/quant/lot/cost |

> Nota de alcance: para **no** crear un Embarque (prohibido por el mandato), el documento de backlog
> se registró **sin** `shipment_id` (registro UAT aislado). El comportamiento de backlog
> (`missing→open→…→completed`, criticidad/responsable/fecha, escalamiento) es idéntico al del test
> canónico `test_documentary_backlog.py`; el pendiente documental **no** bloquea la operación física.

## 6. Corrección documental CDP-V1 (UAT-INT-3)

Sobre la guía **32689 ya `validated`**, mediante el asistente
`madenat.guia.processing.documental.correction.wizard` (id 63) y el ejecutor
`_cdp_apply_documental_correction` (motivo obligatorio):

| Verificación | Antes | Después | Resultado |
|---|---|---|---|
| Versión documental (PDF) cambia | att **63623** | att **63626** `UAT-INT-20261004-GUIA-v2.pdf` | ✔ `CDP_PDF_CHANGED=True` |
| Versión anterior preservada | — | att 63623 **viva** | ✔ `CDP_OLD_PDF_ALIVE` |
| Estado físico | `validated` | `validated` | ✔ `CDP_STATE_UNCHANGED=True` |
| Lotes | `[16694]` | `[16694]` | ✔ `CDP_LOTS_UNCHANGED=True` |
| Pickings | `[7406]` | `[7406]` | ✔ `CDP_PICKS_UNCHANGED=True` |
| Picking/move/move.line/quant/lot/cost | — | sin cambio | ✔ `CDP_PHYS_UNCHANGED=True` |
| Auditoría `deviation` + snapshot/hash | — | 1 fila, `audit_hash` **64** chars, `hash_ok=True` | ✔ tokens `CDP-V1`, `before`, `after`, `edited_fields`, `attachments` |
| Notas/documento corregidos | `notes=False` | `notes='UAT-INT-20261004 nota corregida CDP-V1'` | ✔ |


---

## 7. Permisos (UAT-INT-4)  ⚠️ HALLAZGO

Actor: **uid 6** (Leonardo, **sin Operaciones**, pero con `stock.group_stock_user`/`manager`).
El escenario se ejecutó **sin persistir** (rollback al final).

| Probe (uid 6) | Esperado | Observado |
|---|---|---|
| `check_access_rights('create')` **Consola Ingreso de Madera** | AccessError | ✔ **AccessError** |
| `check_access_rights('create')` **Wizard Ingreso de Madera** | AccessError | ✔ **AccessError** |
| `check_access_rights('create')` `stock.picking` | AccessError | ✖ **NO error** (uid 6 es stock user) |
| `check_access_rights('write')` `madenat.guia.processing` | AccessError | ✖ **NO error** (`base.group_user` 1,1,1,0) |
| **`action_validate()` sobre guía existente** (uid 6) | AccessError/UserError | ✖ **NO error** → creó lote, picking, moves y quants |

`U6_RESIDUE_DELTA` (efecto de uid 6, luego **revertido**):
`stock.lot +1 · stock.picking +1 · stock.move +1 · stock.move.line +1 · stock.quant +2 · madenat.audit.log +2`.
`ROLLBACK_OK` → **FINAL_VS_COMMITTED = Δ0** (nada persistió).

**Diagnóstico.** La **puerta oficial de ingreso** (Consola + Wizard “Ingreso de Madera”, ACL solo
Operaciones) **sí bloquea** al usuario sin Operaciones (AccessError, sin registros) — el control de
negocio funciona. Sin embargo, la ACL de **`madenat.guia.processing` concede `create/write` a
`base.group_user`**, de modo que un usuario interno no-Operaciones **con permisos de stock** puede
**procesar/validar una recepción por RPC/ORM directo** (y el menú/formulario no es, por sí solo, la
barrera). Además, la premisa “uid 6 = lectura” **no se cumple**: uid 6 es *stock manager*. No existe
en el entorno un usuario interno activo “sin Operaciones y sin permisos de stock” para reproducir el
bloqueo esperado. La deuda de ACL es **conocida** (la suite `test_acl_sod_intake_and_costs.py`
documenta que `lumber.reception`, `stock.lot`, `madenat.audit.log` y afines heredan `base.group_user`).

## 8. Stock, lote, ubicación y volumen

- **Lote/tarja:** `stock.lot` **16694** = `UAT-INT-20261004-LOT-01 UATSKU 20261004` ·
  `product_id=UAT-INT-20261004-PRODUCT` · `guia_processing_id=32689` · `estado_trazabilidad=recepcionado`.
- **Ubicación interna:** quant del lote en **`WH/Stock` (id 8, usage=internal)** = **+4.0 m³**;
  contrapartida de proveedor `-4.0 m³` (usage=supplier). Ninguna ubicación externa/cliente/tránsito tocada.
- **Volumen:** línea `vol_purchase_m3=4.0` (10 pzas × 0.1 m × 1.0 m × 4.0 m), `vol_physical_m3=4.0`,
  `vol_shipment_m3=4.003`; lote `volumen_m3=4.0`; `stock.move.product_uom_qty=4.0` (`m³`).
- **Picking/movimiento:** `EMB-04081` (incoming / `Recepciones`) `done`, 1 `stock.move` + 1 `stock.move.line`
  con `lot_id=16694`.
- **Trazabilidad:** proveedor → guía → lote → ubicación interna → quant → movimiento, toda enlazada
  (`stock.lot.guia_processing_id`, `stock.picking.origin/guia_processing_id`, `stock.move.lot_ids`).


---

## 9. Integridad de UAT / histórica

- **Deltas BASE0 → tras UAT (INT-1..3):**
  `ir.attachment +3 · lumber.shipment.document +1 · madenat.audit.log +3 · madenat.guia.processing +1 ·
  madenat.guia.processing.line +1 · stock.lot +1 · stock.move +1 · stock.move.line +1 ·
  stock.picking +1 · stock.quant +2`.
  **Δ0** en: `stock.lot.cost.line`, `lumber.shipment.cost.line`, `lumber.cost.distribution`,
  `lumber.billing.consolidation`, `lumber.export.shipment`, `lumber.container`, `shipping.vessel`,
  `shipping.voyage`, `madenat.sv.operation`, `madenat.sv.imputation`, `account.move`, `account.payment`.
- **UAT-INT-4 revertida:** `FINAL_VS_COMMITTED` = **Δ0** en todos los modelos → nada persistió.
- **Protegidos intactos:** `PROT_ALL_INTACT = True` (0 `missing`, 0 `changed`) sobre
  `lumber.export.shipment`, `lumber.container`, `shipping.vessel`, `shipping.voyage`,
  `madenat.guia.processing`, `lumber.reception`, `madenat.sv.operation`, `madenat.sv.imputation`
  (todo lo pre-existente conserva id+estado/nombre).
- **Congelados financieros finales:** `distributed=0`, `cost.distribution is_c2=True=0`,
  `lumber.shipment.cost.line=0`, `account.payment=0`, `billing.consolidation=0`.
- **No se ejecutó:** contenedor, embarque, rolleo, rebaja, zarpe, B-01, R1/R2, entrega, costeo,
  billing, pagos, R3, retorno parcial; **no** update/install de módulos; **no** commit/push; **no** uid 1.

## 10. Evidencia

Carpeta: `/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_INTAKE_20261004/`

| Archivo | Contenido |
|---|---|
| `00_precheck_baseline.txt` | Precheck read-only formateado (git, runtime, baseline, congelados, usuarios). |
| `00_precheck_raw.txt` | Salida cruda del precheck (`odoo shell`). |
| `01_uat_intake.txt` | Evidencia UAT filtrada (`UAT| …`) de los 4 escenarios + commit + final. |
| `01_uat_intake_raw.txt` | Salida cruda completa del runner. |
| `02_final_validation.txt` | Verificación final read-only de los registros persistidos. |
| `_precheck_intake.py`, `_uat_intake.py` | Harness reproducible (idempotencia / re-ejecución en UAT-INT-2). |
| `UAT-INT-20261004_RESULTADO.md` | Este informe. |

## 11. Dictamen

> **B. `UAT BLOQUEADA O FALLIDA — INDICAR ESCENARIO Y ACCIÓN`.**
>
> **Escenario con hallazgo: UAT-INT-4 (Permisos).** El usuario sin Operaciones **NO** es bloqueado al
> **procesar/validar una recepción por ORM/RPC directo** — se crearon lote, picking, moves y quants
> (revertidos con rollback). Causa: `madenat.guia.processing` concede `create/write` a
> `base.group_user` y los internos no-Operaciones disponibles (uid 6/7/9) son *stock users*; además la
> premisa “uid 6 = lectura” resulta falsa (uid 6 es *stock manager*). La **puerta oficial**
> (Consola/Wizard “Ingreso de Madera”, ACL solo Operaciones) **sí bloquea** (AccessError, sin registros).
>
> **Acción requerida:** (1) **restringir la ACL** de `madenat.guia.processing` (y las acciones de
> validación/recepción) de `base.group_user` a **Operaciones/Jefatura**, alineándola con la Consola y
> el Wizard de Intake; (2) disponer de un usuario interno **realmente de solo lectura** (sin
> Operaciones **y sin permisos de stock**) y **re-ejecutar UAT-INT-4** para confirmar
> `AccessError/UserError` y **Δ0** de recepción/lote/picking/move/quant/backlog.
>
> **Núcleo operativo (UAT-INT-1/2/3 + CDP-V1): APROBADO** — recepción validada, lote/tarja, picking IN
> `done`, quant interno positivo, trazabilidad proveedor/guía/ubicación/volumen, backlog documental
> no bloqueante y corrección documental CDP-V1 sin alterar stock, con integridad de UAT/histórica y
> congelamiento financiero conservados.

