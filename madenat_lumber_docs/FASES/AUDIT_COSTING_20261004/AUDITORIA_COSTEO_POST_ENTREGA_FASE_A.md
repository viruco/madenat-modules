# MADENAT — Auditoría Costeo y Valorización Post-Entrega

- **Sub-bloque 6 — Costeo y Valorización post-Entrega. FASE A — Auditoría read-only y diseño de contrato.**
- **Sin implementación, sin UAT, sin movimiento de inventario, sin cambios de código/roles/ACL/documentación.**
- **Método:** inspección de código (`custom_addons`) + lectura de BD vía `odoo shell` read-only (`_precheck_audit_costing.py`).
  No se ejecutó `action_distribute_costs`, `action_apply_costs`, `action_reverse_costs`, ni ningún flujo de negocio; no se usó `sudo()` funcional ni SQL de escritura.
- **Fecha:** 2026-10-04. Evidencia: `00_precheck_audit.txt`, `_precheck_audit_costing.py`.

---

## 1. Precheck e identidad (`00_precheck_audit.txt`)

| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree / `git diff --check` | **34 = 24 M + 10 ??** (baseline sub-bloque 5) / **CLEAN** |
| Runtime / DB / HTTP | `odoo18_app` Up 8h · `odoo18_db` healthy · HTTP **200** · `madenat_test` |
| Módulos | `madenat_lumber_costing` 18.0.1.0.0 · `madenat_lumber_logistics` 18.0.1.6.0 · `madenat_lumber_core` 18.0.6.5.0 |
| Estados de embarque | `draft` 8 · `confirmed` 3 · `in_transit` 8 · **`delivered` 2** (sólo UAT D2) · `cancelled` 0 |
| `cost_distribution_state` | **`pending` 21 · `distributed` 0** |
| `delivered` existentes | `2189 UAT-DLV-D2-…-CLEAN` · `2190 UAT-DLV-D2-…-DOCS` (únicamente UAT D2) |
| Línea base costeo | `stock.lot.cost.line` **53** (todas `processing`) · `lumber.shipment.cost.line` **0** · `lumber.cost.distribution` **2** (draft `CD-2026-0002` c/4 líneas; applied `CD-DEV-0001` c/1 línea, 0 inyectadas) · `lumber.cost.distribution.line` **5** · `stock.landed.cost` **1** (`LC/2026/0003` draft, sin vínculo MADENAT) |
| Agregados de costo | `Σ logistic_cost_usd` lote = **0.0** · `stock.lot.cost.line` con `source_shipment_cost_line_id` = **0** · con `distribution_id` = **0** |
| `costing_state` lote | `pending` 79 · `partial` 53 · `complete` 0 |
| Financiero | `account.move` 1 · `account.payment` 0 · `lumber.billing.consolidation` 0 · SV 1/1 |
| Auditoría | `madenat.audit.log` 278; **no existe** ningún `action_type` de costeo |
| Protegidos | Histórica / Rolleo / Borrador / B-01 / R1 / R2 / **D2** intactos (mismos ids/estados del cierre del sub-bloque 5) |

> **Hechos duros:** **ningún** embarque tiene `cost_distribution_state='distributed'`; **no existe** ninguna línea de costo de embarque (`lumber.shipment.cost.line`=0); el costeo **nunca** se ha distribuido a lotes (0 líneas con origen embarque); **no hay** auditoría de costeo. El `delivered` es la única evidencia "aguas abajo" de la Entrega D2 (UAT).

---

## 2. Modelos, campos y estados

### 2.1 `stock.lot.cost.line` — libreta única de costo por lote
- **Base:** `madenat_lumber_core/models/stock_lot_cost_line.py` (83 líneas). Campos: `name`, `lot_id` (required, cascade), `cost_type` (`wood`,`logistic`,`processing`,`internalfreight`,`portcost`,`customsagent`,`insurance`,`administrative`,`other`), `amount_usd` (16,2), `partnerid` (M2o proveedor — **nótese: `partnerid`, no `partner_id`**), `date`, `notes`.
- **Ext. logística** (`madenat_lumber_logistics/models/stock_lot_cost_line.py`): `source_shipment_cost_line_id` → `lumber.shipment.cost.line` (`ondelete='restrict'`, index). Es la traza "costo de embarque → costo de lote".
- **Ext. costeo** (`madenat_lumber_costing/models/stock_lot_costing.py` y `lumber_cost_distribution.py`): `distribution_id` → `lumber.cost.distribution`; `lot_name_clean` (related `lot_id.ref`, store); `cost_type` `selection_add` (`freight`,`ocean_freight`,`port`,`customs`,`processing`,`insurance`,`other`).
- **No** tiene `invoice_id` ni `payment_state` (verificado en BD: `False`).

### 2.2 `stock.lot` — valorización del lote
- **Core** (`stock_lot.py`): `wood_cost_usd` (costo TOTAL del lote, AD-38), `purchase_cost_usd`, `cost_line_ids` (O2M), `total_cost_usd` (`compute`, `store=True` = `wood + purchase + Σ cost_line_ids.amount_usd`), `cost_per_m3_usd`, `cost_per_mbf_usd`, `margin_usd`. SQL `CHECK(total_cost_usd >= 0)`.
- **Ext. costeo** (`stock_lot_costing.py`): `logistic_cost_usd`, `process_cost_usd`, `other_cost_usd` (**compute, store, digits (16,2)**), `total_cost_clp`, `exchange_rate`, `costing_state` (`pending`/`partial`/`complete`), `shipment_id`/`booking_ref` (related).
- **Riesgo de doble conteo (N-02):** `_compute_total_cost_usd` de costeo llama `super()` (que ya suma **todas** las `cost_line_ids`) y luego **vuelve a sumar** `logistic_cost_usd + process_cost_usd + other_cost_usd` (que son subconjuntos de esas mismas líneas). El total queda inflado para los costos logísticos/proceso. Confirmado en `08_COSTEO.md` como hallazgo N-02.

### 2.3 `lumber.shipment.cost.line` — costo de embarque
- **Base** (`lumber_export_shipment.py:2130`): `shipment_id`, `currency_id` (related), `amount_usd` (Monetary), `cost_type` (`freight`,`inland_freight`,`port_charges`,`customs`,`insurance`,`documentation`,`inspection`,`handling`,`storage`,`other`), `description`, `distribution_method` (`volume`,`weight`,`packages`,`equal`).
- **Ext. vendor/payment** (`madenat_vendor_payment/models/lumber_shipment_cost.py`): `partner_id` (**required**, domain `supplier_rank>0`), `supplier_category` (required), `partner_type`, `allocation_level`, `container_id`/`lot_id`, `invoice_id` (→ `account.move`), `state`/`payment_state`, y acciones `action_register_payment`, `action_view_invoice`, `action_mark_as_paid`.
- **Ext. costeo** (`lumber_shipment_costing.py`): `is_distributed` (compute, no store).

### 2.4 `lumber.cost.distribution` (expediente de landed cost)
- Modelo `madenat_lumber_costing/models/lumber_cost_distribution.py`. Cabecera: `name` (secuencia, readonly), `state` (`draft`/`applied`/`cancelled`), `date`, `ref`, `partner_id`.
- Alcance: `target_model` (`booking`→`lumber.export.shipment`, `container`, `reception`→`madenat.guia.processing`, `purchase`, `manual`), `booking_id`, `container_ids`/`container_id`, `reception_id`, `purchase_id`, `lot_ids`.
- Matriz: `cost_line_ids` (→ `lumber.cost.distribution.line`), `generated_line_ids` (→ `stock.lot.cost.line`, readonly), `existing_cost_line_ids`; totales `total_volumen_fisico`, `total_volumen_export`, `amount_total_usd`, `package_count`, `lot_count` (compute store); `currency_id` (USD).
- Línea `lumber.cost.distribution.line`: `cost_type`, `invoice_num`, `invoice_date`, `partner_id`, `currency_id`, `amount_original`, `exchange_rate`, `amount_usd` (compute), `distribution_method` (`volume_export`,`volume_physical`,`weight`,`pieces`,`equal`,`container`).

### 2.5 `stock.landed.cost` (puente nativo Odoo)
- `madenat_lumber_costing/models/stock_landed_cost.py`: sólo añade `madenat_distribution_id` (readonly, `ondelete='set null'`). **Ningún código lo asigna** (búsqueda en repo: sólo la definición y un test con `skipTest`). El puente landed-cost **no está cableado** (hallazgo N-04).

### 2.6 `lumber.export.shipment.cost_distribution_state`
- `Selection([('pending','Pendiente'),('distributed','Distribuido')])`, default `pending`. Declarado en `lumber_export_shipment.py:162` y re-declarado idéntico en `lumber_shipment_costing.py:52`.

---

## 3. Flujo actual de distribución de costos (dos motores)

Existen **dos** caminos de distribución, con dueños distintos:

### 3.1 `lumber.export.shipment.action_distribute_costs()` — Logística (el vigente)
**Archivo:** `madenat_lumber_logistics/models/lumber_export_shipment.py:1518-1629`. El módulo de costeo **delega** aquí (`madenat_lumber_costing/models/lumber_shipment_costing.py:20-36`). El botón UI `action_distribute_costs` vive en `lumber_export_shipment_views.xml:337` (página "💰 Gestión Financiera", `groups=account.group_account_manager`; botón `invisible state=='draft'`).

Orden observado (sin ningún gate de estado/rol/auditoría):
1. Exige `cost_line_ids` y lotes (`container_ids.mapped('lot_ids')`).
2. Base de reparto: `total_vol = Σ (vol_shipment_m3 or volumen_m3)`, `total_weight = Σ weight_kg`, `lot_count`.
3. **Reversa implícita previa (SQL crudo):** busca `stock.lot.cost.line` con `source_shipment_cost_line_id in cost_line_ids`; ejecuta `UPDATE stock_lot SET logistic_cost_usd = GREATEST(0, logistic_cost_usd - sub.amount) …` y luego `previous_costs.unlink()`.
4. Reparte `amount / total_vol|weight|lot_count` por lote y arma `vals_list` con **`'partner_id': cost_line.partner_id.id …`**.
5. **`stock.lot.cost.line`.create(vals_list)**.
6. **`UPDATE stock_lot … SET logistic_cost_usd = logistic_cost_usd + c.amount`** vía `psycopg2.extras.execute_values` (**SQL masivo** escribiendo un campo `compute store`).
7. `self.write({'cost_distribution_state': 'distributed'})` + `message_post`.

**Defectos P0 detectados (sólo lectura):**
- **P0-A — campo inexistente:** `vals_list` usa `partner_id`, pero `stock.lot.cost.line` **no tiene** `partner_id` (sólo `partnerid`). El `.create(vals_list)` lanzará `ValueError: Invalid field 'partner_id'` en cuanto el embarque tenga líneas de costo → **el motor vigente está roto** (nunca ejercido: `lumber.shipment.cost.line`=0).
- **P0-B — SQL de escritura:** dos `UPDATE` masivos directos sobre `stock_lot.logistic_cost_usd`, campo `compute store`. Bypassea ORM/`_compute_cost_breakdown`, puede desincronizar `logistic_cost_usd` respecto de `Σ cost_line_ids` y **contradice la Regla de Oro** ("el costeo nunca usa SQL de escritura").
- **P0-C — sin gating ni auditoría:** no valida `delivered`, B-01, R1/R2, retorno, ni rol; **no** firma auditoría; no es idempotente por sí mismo (sólo un borrado+recálculo ciego).

### 3.2 `lumber.cost.distribution.action_apply_costs()` — Costeo (expediente/landed cost)
**Archivo:** `madenat_lumber_costing/models/lumber_cost_distribution.py:137-230`. Botones UI: `action_apply_costs` (Validar y Liquidar) y `action_reverse_costs` (Revertir a Borrador) en `views/lumber_cost_distribution_views.xml:9-10`.

Orden observado:
1. `state` debe ser `draft`; exige `lot_ids` y `cost_line_ids`.
2. Totales globales del "expediente": `total_volumen_fisico`, `total_volumen_export`, peso (`peso_neto`), piezas; `unique_containers` (conteo).
3. Por cada línea: `base_amount = amount_usd`; si `distribution_method=='container'` → `base_amount = amount_usd * unique_containers`.
4. Factor por lote según `volume_export`/`container` (→`vol_shipment_m3`), `volume_physical` (→`volumen_m3`), `weight` (`peso_neto`), `pieces`, `equal`.
5. `stock.lot.cost.line.create(vals_list)` (usa correctamente `partnerid`) con `distribution_id`, y `_compute_total_cost_usd()`.
6. `self.write({'state':'applied'})` + `message_post`.
7. **Reversa** (`action_reverse_costs`, L232-237): `generated_line_ids.unlink()`, recompute, `state='draft'`, chatter. **Sin versionado/historial**: borra físicamente las líneas.

> El expediente NO lee el `cost_distribution_state` del embarque, NO está atado a `delivered`, y NO deja auditoría firmada. Su "alcance" (`booking_id`/`container`) es **sólo un selector de lotes** (`_onchange_target` L93-135).

---

## 4. Prorrateo y lotes

| Motor | Métodos | Base | Lotes considerados |
|---|---|---|---|
| Logística `action_distribute_costs` | `volume` (default), `weight`, `equal` | `vol_shipment_m3 or volumen_m3`; `weight_kg` | `container_ids.mapped('lot_ids')` (todos los del embarque) |
| Costeo `action_apply_costs` | `volume_export`/`container`, `volume_physical`, `weight`, `pieces`, `equal` | `vol_shipment_m3`, `volumen_m3`, `peso_neto`, `piezas` | `lot_ids` del expediente (filtrados por `ref` no vacío y volumen>0; `_onchange_target`) |
| Wizard `lumber.cost.distribution.wizard` | `volume`, `pieces`, `equal` | `volumen_m3 or volume_purchase_m3`; `piezas` | selección manual/reception/purchase/container/booking |

**Comportamiento frente a casos límite (leído, no ejecutado):**
- **Volumen vs tarja:** todos los motores usan **volumen físico** (`volumen_m3`) o **export** (`vol_shipment_m3`) — ninguno usa tarja/piezas por defecto salvo el método explícito `pieces`. Los decimales no se redondean ni se distribuye residual: el factor `amount/total` por lote puede dejar un **centavo residual** no reconciliado (no hay ajuste de cola).
- **Lotes rebajados / reversed / retornados (R2):** el prorrateo **no distingue** estado físico del lote. Un lote con rebaja `reversed`/compensada por retorno R2 **sigue recibiendo costo** si pertenece al embarque/expediente; no hay exclusión ni reclasificación.
- **B-01 open/resolved:** no interviene en el prorrateo.
- **Contenedores pendientes:** el motor de logística reparte sobre `container_ids.lot_ids` sin mirar `_classify_departure_containers`; un contenedor pendiente (B-01 open) con lotes podría recibir costo.
- **Rebajas activas/compensadas:** indiferente al cálculo.
- **Múltiples contenedores:** costo `container` **multiplica por `unique_containers`** (nº de contenedores únicos del embarque) y luego reparte por m³ — admite costo fijo "por contenedor".
- **Precisión/redondeo:** `amount_usd` a 2 decimales; sin política de residual ni redondeo determinista por lote.
- **Idempotencia:** logística revierte (SQL) y re-crea; costeo **bloquea** re-aplicar (`state` distinto de `draft`) pero `action_reverse_costs` permite reapertura → ciclos apply/reverse repetibles sin historial.

---

## 5. Gates B-01 / R1 / R2 / Entrega frente al Costeo

El **único acoplamiento** entre la operación logística y el costeo es el flag `cost_distribution_state == 'distributed'`, que **bloquea logística en 5 puntos** (una vez distribuido, no se puede volver atrás por los flujos):

| Punto | Archivo:línea | Efecto |
|---|---|---|
| Zarpe / confirmar B-01 | `lumber_export_shipment.py:739` | Bloquea `_set_in_transit`/confirm si `distributed` |
| Cierre B-01 (R4) | `lumber_export_shipment.py:1106` | Bloquea `open→resolved` si `distributed` |
| Retorno a Borrador | `lumber_export_shipment.py` (`_return_to_draft_evidence`/guards) | Evidencia financiera = `distributed` + líneas atribuibles + facturas/pagos |
| R1 (rebaja extemporánea) | `lumber_container.py:874` | Bloquea regularización si `distributed` |
| R2 (retorno físico total) | `lumber_container.py:1343` | Bloquea reversa de rebaja si `distributed` o hay `stock.lot.cost.line` atribuibles |

**Inversamente, el Costeo NO exige nada de la operación:** ni `delivered`, ni B-01 `resolved`, ni cero pendientes, ni retorno R2 coherente, ni documentos aprobados. **No hay reciprocidad.**

> Consecuencia de diseño actual: el costo es el **último eslabón y punto de no-retorno** de la operación. Distribuir antes de tiempo **congela** Borrador/Rolleo/R1/R2/B-01/Entrega. Como la Entrega D2 es explícitamente un hito **logístico** (no un cierre financiero), esto es coherente con **C2**, pero hoy el gate no exige que la Entrega haya ocurrido.

---

## 6. Idempotencia, reversa y costos tardíos

| Pregunta | Hallazgo |
|---|---|
| ¿Existe reversa? | **Sí, dos:** logística = revertir por SQL + `unlink` y re-calcular; costeo = `action_reverse_costs` (`generated_line_ids.unlink()` → `draft`). |
| ¿Una distribución puede repetirse? | Logística: **sí** (borra y recrea ciegamente). Costeo: **no** mientras `applied` (exige `draft`), pero se puede `reverse` → `apply` en ciclo. |
| ¿Se puede agregar un costo tardío? | **No de forma formal.** Habría que reintroducir la línea de embarque y re-distribuir (logística) o crear un nuevo expediente (costeo). No hay "redistribución formal de costos tardíos". |
| ¿Cambia `logistic_cost_usd`? | **Sí**, por SQL en logística (`+`/`-`); por compute en costeo. Riesgo de desincronización (P0-B). |
| ¿Hay versionado/historial? | **No.** `action_reverse_costs` **borra** las líneas (`unlink`); no hay snapshot, versión ni auditoría firmada. `stock.lot.cost.line` no tiene `active`/versión. |
| Impacto en factura/pago | Ninguno automático: las acciones de costeo no tocan `account.move`/`account.payment`. |
| Impacto de R2 después de costeo | **Bloqueado**: R2 exige `cost_distribution_state != 'distributed'` y **cero** `stock.lot.cost.line` atribuibles (`lumber_container.py:1343-1355`). |
| Bloqueo de Borrador/Rolleo/Entrega | `distributed` bloquea Borrador (`:1979`), R1 (`:874`), R2 (`:1343`), B-01 (`:739`,`:1106`). Rolleo ya está bloqueado por embarque `in_transit/delivered`. |

---

## 7. Facturación / Pagos (dependencias)

- **Proveedor del costo de embarque:** `lumber.shipment.cost.line.partner_id` (required) + `supplier_category` (vendor_payment). La línea de **lote** (`stock.lot.cost.line`) guarda el proveedor en `partnerid`.
- **Factura/pago:** `lumber.shipment.cost.line.invoice_id` (→`account.move`) y `payment_state`/`state` (vendor_payment); acciones `action_register_payment`, `action_view_invoice`, `action_mark_as_paid`.
- **Consolidación de facturación:** `lumber.billing.consolidation` (state propio; `invoice_id`/`invoice_state`; acciones send_to_audit/start/approve/reject/send_to_billing/open_invoice_wizard). La línea de lote no referencia consolidación; el vínculo es por embarque.
- **Acoplamiento actual:** los guards de retorno a borrador / R2 **ya consultan** factura/pago/consolidación (`invoice_id`, `payment_state`, `consolidation.state=='billed'`). El costeo **no** los usa como precondición.
- **Qué debería ser precondición vs consecuencia:** el costeo debe ser **consecuencia** de la Entrega (D2) y de los costos de embarque, y **precondición** de la facturación final al cliente (una vez valorizado el lote, el margen es confiable). Hoy no existe ese ordenamiento.

---

## 8. Comparación de políticas C1 / C2 / C3

| Criterio | **C1** — Costeo al `delivered` con líneas completas | **C2** — Provisional post-entrega + redistribución formal de tardíos | **C3** — Sólo tras factura/pago final |
|---|---|---|---|
| Seguridad | Alta (exige completitud) — pero hoy **bloquearía todo** (0 cost lines, docs 0%) | Media-alta: entrega provisional + rediseño/reversión controlada | Alta para finanzas; **opaca** la operación (el lote queda sin costo hasta finanzas) |
| Operación | Rígida; ata la Entrega a la completitud documental/costo | **Ágil**: refleja el costo disponible y permite ajuste tardío | Muy tardía; el margen no está disponible en operación |
| Trazabilidad | Buena si hay versionado (no lo hay) | Buena **si** se implementa versionado + auditoría | Depende de finanzas |
| Finanzas | Cierre tardío | Cierre progresivo con ajuste auditado | Preciso pero lento |
| Idempotencia | Debe exigirse | Exige "redistribución formal" (token+audit) | — |
| Compat. B-01/R1/R2 | Choca con el bloqueo actual al distribuir temprano | **Compatible**: distribuir sólo post-Entrega, cuando B-01 ya no bloquea | Compatible |
| Estado del arte en MADENAT | No implementado | **Recomendado** | No implementado |

**Recomendación FASE A: política C2** — el costeo se habilita **post-Entrega D2** (`state=='delivered'`), con **líneas de costo de embarque** existentes; admite costos tardíos mediante una **redistribución formal** (token de proceso + auditoría SHA-256 + versionado), nunca por SQL ni por overwrite del costo de lote. Con el tiempo puede endurecerse hacia C1.

---

## 9. Roles / seguridad

- **ACL actual** (`madenat_lumber_costing/security/ir.model.access.csv`): `lumber.cost.distribution`, `lumber.cost.distribution.line` y el wizard → **`base.group_user` con CRUD total (1,1,1,1)**. Cualquier usuario interno puede crear, aplicar y **revertir** costos.
- El botón de embarque `action_distribute_costs` está en la página con `groups=account.group_account_manager` (UI). Pero **no hay guard de servidor**: el método es invocable por RPC/import por cualquier usuario con acceso de escritura.
- Grupos MADENAT existentes relevantes (BD): `MADENAT: Costos` (id 257), `MADENAT: Auditor de Costos (Felipe)` (id 69), `MADENAT: Auditoría de Costos Avanzada` (id 260), `MADENAT: Contabilidad` (id 258). **No existe** un grupo `group_madenat_contabilidad` (el nombre real difiere).
- **Faltante para el contrato:** guard de rol (Costos/Contabilidad) en `action_distribute_costs`/`action_apply_costs`; separación entre quien **captura** el costo y quien **aprueba** la liquidación; gate de Auditoría (opcional).

---

## 10. Archivos potenciales de la FASE B (sin tocar en FASE A)

| Archivo | Rol |
|---|---|
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | `action_distribute_costs` (reescritura: gate delivered, token, audit, sin SQL, `partnerid`) |
| `madenat_lumber_logistics/models/lumber_shipment_costing.py` | campos `total_shipment_costs_usd`/`cost_distribution_state` + `is_distributed` |
| `madenat_lumber_logistics/models/stock_lot_cost_line.py` | `source_shipment_cost_line_id` (traza) |
| `madenat_lumber_costing/models/lumber_cost_distribution.py` | `action_apply_costs`/`action_reverse_costs` + línea de distribución |
| `madenat_lumber_costing/models/stock_lot_costing.py` | `logistic/process/other_cost_usd`, `costing_state`, doble conteo N-02 |
| `madenat_lumber_costing/models/stock_landed_cost.py` | puente `madenat_distribution_id` (a cablear, N-04) |
| `madenat_lumber_costing/security/ir.model.access.csv` | ACL (hoy `base.group_user` total) |
| `madenat_lumber_core/models/madenat_audit_log.py` | nuevos `action_type` de costeo (aditivos) |
| `madenat_lumber_core/models/stock_lot.py` | `total_cost_usd` (doble conteo N-02) |
| `madenat_vendor_payment/models/lumber_shipment_cost.py` | `partner_id`/`invoice_id`/`payment_state` del costo |
| `madenat_lumber_costing/views/lumber_cost_distribution_views.xml`, `madenat_lumber_logistics/views/lumber_export_shipment_views.xml` | botones/estado |

---

## 11. Riesgos priorizados

**P0 (bloquean la implementación):**
- **P0-1 — Motor vigente roto:** `action_distribute_costs` usa `partner_id` (campo inexistente) → `ValueError` al crear líneas. Debe reescribirse a `partnerid`.
- **P0-2 — SQL de escritura sobre campo `compute store`:** los `UPDATE stock_lot … logistic_cost_usd` bypassan el ORM y pueden desincronizar; violan la Regla de Oro ("el costeo nunca usa SQL de escritura").
- **P0-3 — Sin gating ni auditoría:** el costeo no exige `delivered`/B-01/R1/R2 ni rol, y no deja auditoría firmada. Debe añadirse gate + token de proceso + auditoría SHA-256.

**P1 (alto):**
- **P1-1 — Doble conteo `total_cost_usd` (N-02):** `_compute_total_cost_usd` suma dos veces los costos logísticos.
- **P1-2 — Reversa destructiva sin historial:** `action_reverse_costs` borra líneas; no hay versionado ni auditoría de reversa.
- **P1-3 — Segregación:** ACL total a `base.group_user`; sin rol Costos/Contabilidad ni aprobación.
- **P1-4 — Sin idempotencia formal ni residual:** redistribución ciega; sin política de redondeo/residual determinista.
- **P1-5 — Puente landed-cost no cableado (N-04).**
- **P1-6 — Falta fuente/completitud de costos:** `lumber.shipment.cost.line`=0 y gate de OC (CANON 08 §9) no implementado → no hay "costos completos" que exijan C1.

**P2 (informativo):**
- Dos motores de distribución con dueños distintos (logística vs costeo) — riesgo de divergencia ya materializado.
- Prerrateo indiferente a rebaja `reversed`/retorno R2/contenedor pendiente.
- `cost_distribution_state` re-declarado en dos archivos.
- Métodos del wizard y de la línea de distribución sin validación de compañía/proveedor comercial.

---

## 12. Diseño de tests / UAT futura (no ejecutados)

| ID | Caso | Resultado esperado (política C2) |
|---|---|---|
| **T-CST-1** | Embarque `delivered` limpio (B-01 none, sin pendientes) + líneas de costo → `action_distribute_costs` | Distribución por volumen correcta; `cost_distribution_state='distributed'`; líneas con `source_shipment_cost_line_id`; `partnerid` correcto |
| **T-CST-2** | B-01 `open` | **Bloqueado** (`UserError`) |
| **T-CST-3** | B-01 `resolved` + R1/R2 coherentes + `delivered` | **Permitido** |
| **T-CST-4** | Distribución repetida | Idempotente o bloqueada (token de proceso); sin duplicar líneas |
| **T-CST-5** | Redondeo/residual | Suma distribuida == total (± tolerancia) con ajuste de cola determinista |
| **T-CST-6** | Costo tardío | Redistribución **formal** (auditoría) o nuevo expediente; documentado |
| **T-CST-7** | Usuario no autorizado / RPC | `AccessError`; `action_distribute_costs` inaccesible sin rol |
| **T-CST-8** | No cambia stock | Δ=0 en move/picking/quant/lot/costos base |
| **T-CST-9** | Auditoría/hash | Evento append-only con snapshot + SHA-256; chatter |
| **T-CST-10** | Vínculo proveedor/factura/pago | `partner_id`/`invoice_id`/`payment_state` propagados/validados |

Pruebas unitarias ya existentes (regresión, `madenat_lumber_costing/tests/`): `test_cost_distribution.py` (C2.1/C2.3/C2.5 + regresión `partnerid`), `test_landed_cost_integration.py` (C3.x, con `skipTest` por N-04), `test_module_compatibility.py`. Ambas suites del motor de costeo pasan; **no hay** suite para `action_distribute_costs` (motor vigente roto).

---

## 13. Dictamen

### **A. `APTO PARA DISEÑAR E IMPLEMENTAR COSTEO`** (condicionado)

La auditoría está **completa** y el contrato actual está **plenamente caracterizado**. Es apto para pasar a diseño/implementación **si y sólo si** se cumplen estas precondiciones dentro del bloque de implementación:

1. **Ratificar la política C2** (costeo provisional post-Entrega + redistribución formal de costos tardíos).
2. **Cerrar los P0-1…P0-3** (reescritura del motor: `partnerid`, sin SQL de escritura, gate `delivered`+B-01/R1/R2, token de proceso, auditoría SHA-256).
3. **Definir la fuente/completitud de costos** del embarque (líneas de costo + puente OC, CANON 08 §9) y el gate de rol Costos/Contabilidad.
4. **Corregir P1-1** (doble conteo `total_cost_usd`) y dotar de **versionado/reversa auditada** (P1-2/P1-4).

**Recomendación de secuencia:** (Fase B) contrato + motor único idempotente y auditado → (Fase C) tests unitarios T-CST-1…T-CST-10 → (Fase D) UAT aislada post-Entrega.

---

*Read-only. No se ejecutó distribución de costos, landing, reversa ni ningún flujo de negocio. No se movió stock, lotes, pickings, moves, quants, costos, facturas, pagos, SV ni imputaciones. No se tocó ningún registro protegido ni la UAT D2. No se modificaron roles, grupos, ACL, XML, Python, tests, manifests ni documentación existente. Sin commit/push. Fin del informe.*
