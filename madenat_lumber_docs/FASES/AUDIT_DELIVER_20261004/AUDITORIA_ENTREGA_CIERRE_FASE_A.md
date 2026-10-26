# MADENAT — Auditoría Entrega y Cierre Seguro

- **Sub-bloque 5 — Entrega y Cierre seguro de Embarque. FASE A — Auditoría read-only y diseño de contrato.**
- **Sin implementación, sin UAT, sin movimiento de inventario, sin cambios de roles/ACL/código.**
- **Método:** inspección de código (`custom_addons`) + lectura de BD vía `odoo shell` read-only.
  No se ejecutó `action_deliver` ni ningún flujo de negocio; no se usó `sudo()` ni SQL de escritura.
- **Fecha:** 2026-10-04. Evidencia: `00_precheck_audit.txt`, `_precheck_audit_deliver.py`.

---

## 1. Precheck e identidad (`00_precheck_audit.txt`)
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree / `diff --check` | **33 = 24 M + 9 ??** / **CLEAN** |
| Runtime / DB / HTTP | `odoo18_app` Up · `odoo18_db` healthy · HTTP **200** · `madenat_test` |
| Rol Cristhian (uid 8) | Operaciones + Jefatura; **sin** Gerencia/Contabilidad/account_manager/System |
| Rol Leonardo (uid 6) | Sin grupos MADENAT (reportería/lectura); conserva `account_manager` preexistente |
| Estados de embarque | draft 7 · confirmed 3 · in_transit 6 · **delivered 0** · cancelled 0 |
| B-01 | none 14 · open 1 · resolved 1 |
| `cost_distribution_state` | pending 16 · distributed 0 |
| `document_status` | **pending 16 · partial 0 · complete 0** |
| Billing / Pagos | consolidaciones 0 · órdenes de pago 0 |
| Línea base | move 145 · mline 212 · picking 30 · quant 173 · lot 128 · lot.cost.line 53 · shipment.cost.line 0 · shipment 16 · container 17 · shipment.line 7 · vessel 8 · voyage 2 · audit 273 · sv.operation 1 · sv.imputation 1 · account.move 1 · account.payment 0 · shipment.document 96 |
| Protegidos UAT | R2 2128[2129/921] · R1 1885[1888] · B-01 1868 · histórica 1537/1528 → **intactos** |

> **Hechos duros:** hoy **no existe ningún Embarque `delivered`**, **ninguna** consolidación/orden de pago
> y **ningún** embarque con documentación completa. `delivered` es un estado **nunca ejercido** en este stack.

## 2. Contrato actual de `action_deliver`
**Archivo:** `madenat_lumber_logistics/models/lumber_export_shipment.py:1131-1156`.

Orden exacto de guardas (todas en servidor, sin `sudo()`):
1. `_assert_departure_group()` (`:551`) → exige **Jefatura o Gerencia** (`DEPARTURE_CONFIRM_GROUPS`, `:40-43`).
2. `_assert_no_rebaja_inconsistency()` (`:601`) → **P0**: bloquea si algún contenedor está
   `reversed` **sin** retorno físico total validado.
3. `state != 'in_transit'` → `ValidationError("Solo un embarque en tránsito puede entregarse")`.
4. `_b01_blocks_delivery()` (`:1123`) → bloquea si `b01_exception_state == 'open'`.
5. `_classify_departure_containers()` (`:619`) → **pendientes** = contenedores **sin rebaja física
   activa**; si hay pendientes → `UserError`.
6. `self.write({'state': 'delivered'})` (`:1155`) + `message_post("Embarque entregado")` (`:1156`).

**Entradas/expuestos:**
- **UI:** único botón `action_deliver` en `views/lumber_export_shipment_views.xml:46-48`
  (`groups=jefatura|gerencia`, `invisible="state != 'in_transit'"`).
- **RPC:** `action_deliver` es método del modelo; el guard de grupo es la defensa real.
- **Server actions / imports / wizards:** **no existen** otras rutas a `delivered`.

**Efectos reales:** escribe **sólo** `state` (campo `Selection` `tracking=True`, `:282-288`) y postea
chatter. **No** escribe `madenat.audit.log` (sin hash), **no** toca contenedores, **no** toca stock/lotes/
quants, **no** toca B-01, **no** toca costos/facturas/pagos. Devuelve `None` (el botón depende del reload del cliente).

**Idempotencia/concurrencia:** 2ª llamada → `ValidationError` (state ya no es `in_transit`): seguro y
bloqueante, pero **no** devuelve un resultado idempotente. **Sin lock** (a diferencia de la reversa R2,
que usa `_rebaja_reverse_lock`). Dos llamadas concurrentes ambas pasarían el guard; el write final es
"last-wins" benigno (mismo valor).

## 3. Estados, campos y efectos terminales
- `state` (draft/confirmed/in_transit/delivered/cancelled), default `draft`.
- **`action_confirm` (`:530-543`) NO tiene guard de grupo** y valida sólo: ≥1 contenedor, `booking_reference`,
  `vessel_id`. Escribe `state='confirmed'`. (Cualquier usuario interno con write en el modelo puede
  confirmar.)
- `actual_departure` se fija en el zarpe (`_set_in_transit`, `:749`).
- **Efecto en trazabilidad de lote:** `stock.lot._compute…` (`stock_lot.py:1079`) marca `embarcado` si
  el embarque está en `('in_transit','delivered')` → `delivered` **no añade semántica** sobre `in_transit`.
- **Campos nunca escritos por `action_deliver`:** `document_status`, `cost_distribution_state`,
  `invoice_issued`, `bl_received`, `customs_cleared`, `actual_arrival` (no existe).

---

## 4. Precondiciones físicas (condiciones reales de código)
| # | Condición | Fuente (código) | Enforcement actual | Prioridad |
|---|---|---|---|---|
| F1 | Embarque `in_transit` | `action_deliver:1142` | **Sí (P0)** | P0 |
| F2 | Sin inconsistencia de rebaja (`reversed` sin retorno total) | `_assert_no_rebaja_inconsistency:601` + `_container_rebaja_classification:557` | **Sí (P0)** | P0 |
| F3 | Sin B-01 `open` | `_b01_blocks_delivery:1123` | **Sí (P0)** | P0 |
| F4 | Sin contenedores pendientes (rebaja física activa en todos) | `_classify_departure_containers:619` + `_is_container_rebajado_fisico:591` | **Sí (P0)** | P0 |
| F5 | Cadena OUT→IN coherente por `origin_returned_move_id` | `_rebaja_return_total_complete:1222` / `_rebaja_move_return_complete:1210` | **Pasiva** (vía F2/F4) | P0 |
| F6 | `container.state` ∈ {rebajado,shipped} con línea `rebajado` | `_container_rebaja_classification:569` | **Pasiva** (vía F4) | P0 |
| F7 | `line.rebaja_picking_id.state == 'done'` | `_container_rebaja_classification:580-586` | **Pasiva** | P1 |
| F8 | Quants internos/Customers vs `state_before_rebaja` | — | **NO comprobado** en Entrega | P1 |
| F9 | `cost_distribution_state` (costos) | `:648`, `:1505` (solo zarpe/borrador) | **NO comprobado** en Entrega | P1 |
| F10 | Documentos/checklist | `lumber_document_checklist.py` | **NO comprobado** en Entrega | P1 |
| F11 | Consolidaciones de facturación / pagos | `:652-659` (solo zarpe) | **NO comprobado** en Entrega | P1 |
| F12 | Movimientos `pending`/`cancel` inesperados | — | **NO comprobado** | P2 |
| F13 | `state_before_rebaja` | — | **NO comprobado** | P2 |

> **Clasificación:** F1–F6 = **P0 bloqueante** (ya en código); F7/F8/F9/F10/F11 = **P1** (deben decidirse);
> F12/F13 = **P2 informativo**.

## 5. B-01 / R1 / R2 y consistencia de retorno
- **B-01 `open`:** bloquea Entrega (F3). `resolved` **NO** bloquea: `_b01_blocks_delivery` sólo mira `'open'` (`:1129`).
- **B-01 `resolved` sin pendientes:** tras R1 todos los contenedores quedan `rebajado` → F4 = 0 pendientes
  → **Entrega permitida**. (La política de si `resolved` debe exigir un paso adicional es **decisión de negocio**.)
- **R2 (retorno total):** la reversa deja el contenedor en `loaded` y la línea en `reversed` →
  clasificación **`compensated`** → `_is_container_rebajado_fisico=False` → **cuenta como PENDIENTE** →
  **Entrega BLOQUEADA** hasta re-rebajar. **Semántica correcta** (el stock volvió a bodega interna: no se
  puede entregar), pero **no documentada** y no diferenciada de un "pendiente nunca rebajado".
- **Clasificación física (`_container_rebaja_classification`):** `active` (línea `rebajado`, o OUT `done`
  sin retorno) · `compensated` (retorno total validado) · `inconsistent` (`reversed` sin retorno → P0) · `none`.
- **Zarpe:** `_assert_departure_context` recolecta `_warn_legacy_b01_evidence` (advertencia B-01 textual histórica).

## 6. Documentos / checklist
- **Modelos reales:**
  - `lumber.document.checklist` (`lumber_document_checklist.py`): catálogo (`name`, `is_required`, `active`).
  - `lumber.shipment.document`: `shipment_id`, `checklist_id`, `file_data`, `state`
    (`missing`/`attached`/`verified` — **computado** desde `file_data`, `verified` sticky manual).
  - En el embarque: `document_ids` (O2M) + `document_status` (`pending`/`partial`/`complete`) +
    `document_completion` (% ... ) — **compute/store** (`_compute_document_status`).
- **Auto-creación:** al crear un embarque se generan los documentos de **todos** los checklist activos
  (hoy 96 docs / 16 embarques = **6 tipos**).
- **Gate:** `action_deliver` **NO** consulta `document_status`. Estado actual: **16/16 = `pending`** (0 adjuntos).
  → Un gate duro por documentos **bloquearía el 100%** de los embarques hoy (incl. toda la UAT previa).
- **Confiabilidad:** el estado documental es **calculado por archivo adjunto**, no por aprobación humana
  (no hay firma/usuario/fecha de verificación ni ACL por documento) → **aún no** es un gate fiable.

## 7. Costeo / Billing / Pagos
| Dominio | Modelo/Clave | Guard de Entrega | Independencia |
|---|---|---|---|
| Costeo | `cost_distribution_state`, `stock.lot.cost.line`, `lumber.shipment.cost.line`, `action_distribute_costs:1158` | **ninguno** (no mira estado) | `action_distribute_costs` **sin guard de grupo** y **sin** guard de estado → ejecutable incluso tras `delivered` |
| Distribución | Zarpe/R1/Borrador **sí** bloquean si `cost_distribution_state=='distributed'` (`:648`, `:1015`, `:1505`) | — | Entrega **no** |
| Facturación | `lumber.billing.consolidation` (state: draft→audit→billing→`billed`; `invoice_id`) | **ninguno** | `create` sólo controla duplicado no-cancelado por embarque (`:493-514`); **no** mira `shipment.state` |
| Pagos | `vendor.payment.order` (draft/approved/paid), `lumber.shipment.cost.invoice_id`/`payment_state` | **ninguno** | Independiente |

**Hallazgos:** `delivered` **no** depende de Costeo/Billing/Pagos, y Costeo/Billing/Pagos **no** dependen de
`delivered`. El único bloqueo financiero existente (costos distribuidos) vive en **Zarpe/R1/Borrador**, no en Entrega.

---

## 8. Roles y rutas UI/RPC
**Guard de rol efectivo:** `_assert_departure_group()` = `DEPARTURE_CONFIRM_GROUPS` = **(Jefatura, Gerencia)**.
Por tanto **Operaciones puro NO puede entregar** (ni vía botón ni vía `action_deliver`), **Auditoría no**, **Contabilidad no**.

**ACL del modelo** (`madenat_lumber_logistics/security/ir.model.access.csv`):
`access_lumber_export_shipment_user` → `base.group_user` `1,1,1,0` (read/write/create),
`…_manager` → `stock.group_stock_manager` `1,1,1,1`. **No hay reglas de registro (`ir.rule`)** para el modelo
(no existen XML de reglas; sólo ACL).

> 🔴 **RUTA LATERAL P0 (bypass):** el `write()` del modelo (`:173-220`) **sólo** protege con token
> `state == 'draft'` (y los campos B-01). **No existe token para `delivered`.** Como `base.group_user` tiene
> **write** en el modelo, **cualquier usuario interno podría ejecutar `write({'state': 'delivered'})` por RPC
> saltándose** `_assert_departure_group`, `_assert_no_rebaja_inconsistency`, la comprobación de `in_transit`,
> la de B-01 y la de pendientes. Lo mismo aplica a `state ∈ {'confirmed','in_transit','cancelled'}`.
> El único estado protegido contra write directo es `draft`.

## 9. Acciones posteriores y su relación con `delivered`
| Acción | ¿Bloqueada tras `delivered`? | Evidencia |
|---|---|---|
| **Borrador Seguro** (`action_draft`) | **Sí** | exige `state=='confirmed'` (`:1546`); `write(draft)` con token |
| **Rolleo** (contenedor/motonave) | **Sí** | `ROLLOVER_TERMINAL_SHIPMENT_STATES=('in_transit','delivered','cancelled')` (`lumber_container.py:747`) |
| **Zarpe** (`action_set_in_transit`) | **Sí** | `_assert_departure_context` exige `confirmed` (`:629`) |
| **B-01 open** (`_set_in_transit`) | **Sí** | exige `confirmed` (`:629`) |
| **R1 rebaja extemporánea** | **Sí** | exige `in_transit` (`lumber_container.py:839`) |
| **R2 reversa** (`action_reverse_rebaja`) | **Parcial** | `delivered` → exige **override Gerencia** (`lumber_container.py:974-988`) |
| **Alta/baja de Contenedores** | ⚠️ **NO** | el congelamiento (`:190-199`) cubre `in_transit`/B-01 pero **no `delivered`** |
| **Costeo** (`action_distribute_costs`) | ⚠️ **NO** | sin guard de estado ni de grupo |
| **Billing / Pagos** | ⚠️ **NO** | sin dependencia de `shipment.state` |
| **Reportes / dashboards** | ⚠️ **NO** | menús sin `groups=`; sin gating por estado |

## 10. Políticas D1 / D2 / D3 (comparación)
| Criterio | **D1 mínima** | **D2 controlada** | **D3 financiera terminal** |
|---|---|---|---|
| F1 `in_transit` | Sí | Sí | Sí |
| F2 sin inconsistencia | Sí | Sí | Sí |
| F3 sin B-01 open | Sí | Sí | Sí |
| F4 sin pendientes físicos | Sí | Sí | Sí |
| Documentos aprobados (F10) | ✗ | **Sí** | Sí |
| Costo distribuido / no requerido (F9) | ✗ | **Sí (o waiver explícito)** | Sí |
| Consolidación facturada (F11) | ✗ | ✗ | **Sí** |
| Pagos (F11) | ✗ | ✗ | **Sí** |
| Rol | Jefatura/Gerencia | Jefatura **o** Gerencia (según umbral) | Gerencia/Contabilidad |
| Alineación con el código **actual** | próxima (ya cumple F1-F4) | media (faltan F9/F10) | lejana (finanzas hoy desacopladas) |
| Riesgo operativo | Bajo (permite entregar sin costear) | **Medio-bajo (recomendado)** | Alto (bloquearía 100% hoy) |
| Viabilidad hoy | **Inmediata** | Requiere poblar checklist y política de costo | **No** (0 consolidaciones/16 docs pending) |

> **No se elige aquí** (decisión de negocio). Base técnica recomendada para el diseño: **D2 con P0 corregido**,
> con **waiver documental/financiero explícito y auditado** cuando aplique, y **D3 como objetivo posterior** tras
> operar Billing/Pagos.

---

## 11. Lista de archivos potenciales (a tocar en la implementación futura — NADA modificado aquí)
| Archivo | Rol en el diseño |
|---|---|
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | `action_deliver` (`:1131`), `write()` (`:173`) para cerrar el bypass P0, guards F*, `action_confirm` (`:530`) |
| `madenat_lumber_logistics/views/lumber_export_shipment_views.xml` | botón `action_deliver` (`:46`), checklist (`:241`), posible vista de política/waiver |
| `madenat_lumber_logistics/models/lumber_document_checklist.py` | `document_status`/`document_completion`, gate documental |
| `madenat_lumber_logistics/models/lumber_container.py` | congelamiento de contenedores con `delivered`, R2 override |
| `madenat_lumber_billing/models/lumber_billing_consolidation.py` | dependencia (o no) de `delivered` |
| `madenat_lumber_costing/models/lumber_shipment_costing.py` | guard de costeo vs `delivered` |
| `madenat_vendor_payment/models/*` | pagos (fuera de alcance inmediato) |
| `madenat_lumber_logistics/security/ir.model.access.csv` | ACL (posible regla de escritura de estado) |
| `madenat_lumber_logistics/tests/test_shipment_*.py` | tests T-DLV |

## 12. Riesgos
**P0 (bloqueantes / seguridad y trazabilidad):**
- **P0-1 — Bypass de `delivered` por write directo.** Sin token en `write()`; `base.group_user` tiene write →
  cualquier interno puede saltarse **todas** las guardas de Entrega. (Evidencia: `:173-220` vs `:1131-1156`.)
- **P0-2 — Sin evidencia de auditoría de Entrega.** `action_deliver` **no** escribe `madenat.audit.log`
  (los demás flujos terminales sí, con hash SHA-256). Sólo `message_post`.
- **P0-3 — `action_confirm` sin guard de rol ni red de seguridad.** Cualquier interno confirma; no se valida B-01/estado.

**P1 (decisión/implementación requerida):**
- **P1-1 — Documentos no son gate** (y hoy 16/16 `pending`): requiere política + datos.
- **P1-2 — Costeo no es gate**: `action_distribute_costs` ejecutable tras entregar (y sin guard de grupo).
- **P1-3 — Billing no depende de `delivered`** ni viceversa.
- **P1-4 — `container_ids` no se congela con `delivered`.**
- **P1-5 — Semántica `compensated` (R2) = “pendiente”** no diferenciada en el mensaje de Entrega.
- **P1-6 — Sin lock de concurrencia** en Entrega (no bloqueante, pero inconsistente con R2).

**P2 (informativo):**
- **P2-1 — Reportes/ menús sin `groups=`** (lectura amplia).
- **P2-2 — `action_deliver` devuelve `None`** (UX: sin acción de reload explícita).
- **P2-3 — `delivered` no agrega semántica de trazabilidad** sobre `in_transit` (lote queda `embarcado` en ambos).

## 13. Diseño de tests / UAT futuro (no ejecutados)
| ID | Caso | Resultado esperado (política D2 + P0 corregido) |
|---|---|---|
| T-DLV-1 | `in_transit` limpio (todos rebajados, sin B-01, docs OK) | `delivered` **permitido** (Jefatura) |
| T-DLV-2 | B-01 `open` | **bloqueado** (`UserError`) |
| T-DLV-3 | B-01 `resolved` sin pendientes | permitido/bloqueado **según política** (D2: permitido; documentar) |
| T-DLV-4 | contenedor `active`/`inconsistent` | **bloqueado** |
| T-DLV-5 | retorno R2 coherente (compensado, sin pendientes) | **permitido** si el stock está disponible; si no, pendiente → bloqueado |
| T-DLV-6 | documentos incompletos | **bloquear o waiver auditado** (según política) |
| T-DLV-7 | costo no distribuido / finanzas | **waiver o bloqueo** (según D2/D3) |
| T-DLV-8 | usuario no autorizado (Operaciones/plano) vía RPC `action_deliver` | **`AccessError`** |
| T-DLV-9 | `write({'state':'delivered'})` directo por `base.group_user` | **`UserError`** (token) — *hoy FALLA* |
| T-DLV-10 | tras `delivered`: Borrador/Rolleo/Zarpe/B-01/R1 bloqueados; R2 exige Gerencia | **bloqueado / override** |

## 14. Dictamen

### **B. `BLOQUEADO — INDICAR EVIDENCIA O DECISIÓN FALTANTE`**

La auditoría está **completa** y el contrato actual está **plenamente caracterizado**, pero **no es apto
para implementar la Entrega/Cierre seguro sin decisiones y una corrección previa**:

1. **Decisión de negocio faltante (política D1/D2/D3):** no existe AD/matriz aprobada que defina si la
   Entrega exige **documentos** (F10) y/o **costeo** (F9) y/o **facturación/pagos** (F11). Hoy `delivered`
   es puramente logístico y estas dependencias están **desacopladas**.
2. **Evidencia/estado faltante para un gate financiero/documental:** `document_status` = pending en **16/16**
   embarques (0 adjuntos) y **0** consolidaciones/pagos → un gate D2/D3 estricto **bloquearía todo hoy**.
3. **P0 de seguridad de servidor:** `write({'state':'delivered'})` (y `confirmed`/`in_transit`/`cancelled`)
   **no** está protegido por token; cualquier `base.group_user` puede **saltarse** las guardas de Entrega.
   Debe cerrarse como parte del diseño (mismo patrón que `action_draft`/B-01).
4. **P0 de trazabilidad:** `action_deliver` **no** registra auditoría firmada (los pares R1/R2/B-01 sí).

**Recomendación para desbloquear:** (a) decisión de negocio sobre **D1/D2/D3** (base sugerida **D2** con
*waiver* auditado); (b) corregir **P0-1/P0-2/P0-3** (tokens + auditoría hash + guard de `action_confirm`);
(c) definir el **gate documental** (poblar checklist + usuario/fecha de verificación) y la **política de costo**.

*Read-only. No se ejecutó Entrega/B-01/R1/R2/Borrador/Rolleo/Zarpe. No se creó/movió stock, lotes, pickings,
moves, quants, costos, facturas, pagos, SV ni imputaciones. No se tocó ningún registro protegido. No se
modificaron roles, grupos, ACL, XML, Python, tests, manifests ni documentación existente. Sin commit/push.
Fin del informe.*

