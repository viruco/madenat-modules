# MADENAT — Resultado UAT Rolleo de Motonave

```
Documento   : UAT-VR-20261004_RESULTADO
Feature     : Rolleo de Motonave / Cambio de Planificación Marítima
Fase        : D (Gate Y — UAT aislada, sin rebaja, sin zarpe, sin movimiento de inventario)
Entorno     : madenat_test (odoo18_app + odoo18_db)
Fecha       : 2026-10-04
Ejecutor    : Cristhian Elgueta — uid 8 (cristhian.elguetag@gmail.com)
Rol         : madenat_lumber_core.group_madenat_operaciones (Operaciones)
Evidencia   : ./UAT_VR_20261004/00..04*.txt
Dictamen    : A. UAT ROLLEO DE MOTONAVE APROBADA — APTO PARA DOCUMENTAR Y OPERAR
```

---

## 1. Fecha, entorno y usuario ejecutor

- **Fecha/hora de ejecución:** 2026-10-04, ventana 03:52 UTC (≈ 23:52 hora local).
- **Entorno:** base `madenat_test`; contenedores `odoo18_app` (Up) y `odoo18_db`
  (healthy, postgres:15); modules `madenat_lumber_core`, `madenat_lumber_shipping_core`
  y `madenat_lumber_logistics` instalados.
- **Método de ejecución:** métodos de **servidor** del asistente
  `lumber.vessel.rollover.wizard` invocados vía ORM bajo el **usuario Operaciones**
  (`env(user=8)`, es decir `su=False`). No se usó Administrador, ni `with_user(1)`,
  ni SQL de escritura. No se editó código/XML/ACL/manifests/tests/documentación.
  - *Nota de transparencia:* el propio asistente escribe la bitácora con
    `madenat.audit.log.sudo()` **dentro de su código ya aprobado**
    (`_audit_create`); no es un bypass del ejecutor UAT. El actor registrado en
    cada evento es `uid=8`.
- **Usuario ejecutor:** `8 Cristhian Elgueta`, con el grupo
  `group_madenat_operaciones`. No pertenece a `group_madenat_auditoria`.

### 1.1 Git (repo `/custom_addons`)
- Rama: `feat/guia-correccion-documental-preservada-20261002`
- HEAD: `34c81272bb07d48db98d73a7734c81a2a8e384fa`
- Cambios locales: los **20 archivos modificados + 3 sin seguimiento** que
  constituyen la implementación Rolleo de Motonave (Fase C/D). No hay cambios
  fuera de lo aprobado. **No** se hizo commit/push/PR/reset/checkout/rebase/stash/branch.

---

## 2. Línea base y conservación de la UAT histórica

### 2.1 Línea base global (antes → después)

| Modelo | Antes | Después | Δ | Esperado |
|---|---:|---:|---:|:--:|
| `stock.move` | 142 | 142 | 0 | ✔ |
| `stock.move.line` | 209 | 209 | 0 | ✔ |
| `stock.picking` | 27 | 27 | 0 | ✔ |
| `stock.quant` | 169 | 169 | 0 | ✔ |
| `stock.lot` | 126 | 126 | 0 | ✔ |
| `account.move` | 1 | 1 | 0 | ✔ |
| `account.payment` | 0 | 0 | 0 | ✔ |
| `madenat.sv.operation` | 1 | 1 | 0 | ✔ |
| `madenat.sv.imputation` | 1 | 1 | 0 | ✔ |
| `stock.lot.cost.line` | 53 | 53 | 0 | ✔ (0 filas nuevas desde inicio UAT) |
| `lumber.shipment.cost.line` | 0 | 0 | 0 | ✔ |
| `lumber.export.shipment` | 4 | 7 | **+3** | ✔ |
| `lumber.container` | 5 | 8 | **+3** | ✔ |
| `shipping.vessel` | 3 | 5 | **+2** | ✔ |
| `shipping.voyage` | 0 | 1 | **+1** | ✔ |
| `madenat.audit.log` | 256 | 262 | **+6** | ✔ (2 maestras + 4 ítem) |

### 2.2 UAT histórica protegida (intacta)
| Registro | Esperado | Verificado |
|---|---|---|
| Embarque 1537 `UAT-LOG-20261003-EMB-01` | `in_transit` | `in_transit` ✔ |
| Contenedor 1509 `UAT-LOG-20261003-CONT-01` | `shipped` | `shipped` ✔ |
| Contenedor 1500 `UAT-SV-20261003-CONT` | `rebajado` | `rebajado` ✔ |
| Embarque 1528 `UAT-SV-20261003-SHIP` | `draft` | `draft` ✔ |
| Picking 7065 `WH/OUT/02194` | `done` | `done` ✔ |
| Operación SV 5822 (`SVO005684`) | presente | presente ✔ |
| Imputación 492 (`IMP00946`) | presente | presente ✔ |
| Guías 32298 / 32300 | presentes | presentes ✔ |
| Lotes SV 15892 / 15894 | presentes | presentes ✔ |
| Lotes 15970 / 15971 | interno 0, Customers +0.144 | interno `WH/Stock/*` = 0.0000; `Partners/Customers` = +0.1440 ✔ |

**Nota de línea base (informativa, no bloqueante):** los lotes 15970/15971
presentan además `Partners/Vendors = -0.1440` (contrapartida histórica del
movimiento SV). Es un valor **previo** y **ajeno** a esta UAT; el requisito
“interno 0 / Customers +0.144” se cumple. No fue modificado.

---

## 3. IDs/nombres de todos los datos UAT nuevos

| Tipo | Modelo | ID | Nombre / Referencia |
|---|---|---:|---|
| Motonave origen | `shipping.vessel` | **619** | `UAT-VR-20261004-ORIG-VESSEL` |
| Motonave destino | `shipping.vessel` | **620** | `UAT-VR-20261004-DEST-VESSEL` |
| Viaje destino | `shipping.voyage` | **565** | `UAT-VR-20261004-DEST-VOY-01` (vessel 620, `draft`) |
| Embarque sin viaje | `lumber.export.shipment` | **1644** | `UAT-VR-20261004-SHIP-NOVOY` |
| Embarque con viaje | `lumber.export.shipment` | **1645** | `UAT-VR-20261004-SHIP-VOY` |
| Embarque bloqueado | `lumber.export.shipment` | **1646** | `UAT-VR-20261004-SHIP-BLOCK` |
| Contenedor sin viaje | `lumber.container` | **1629** | `UAT-VR-20261004-CONT-NOVOY` |
| Contenedor con viaje | `lumber.container` | **1630** | `UAT-VR-20261004-CONT-VOY` |
| Contenedor bloqueado | `lumber.container` | **1631** | `UAT-VR-20261004-CONT-BLOCK` |

No se creó ningún documento comercial, factura, pago, costo, lote ni dato SV.

---

## 4. Resultado UAT-1 — Rolleo exitoso SIN Viaje

- **Antes:** `SHIP-NOVOY` → `vessel_id=619`, `voyage_id=False`, `state=draft`,
  `booking=UAT-VR-20261004-BOOK-01`; `CONT-NOVOY` → `shipment_id=1644`, `state=loaded`,
  `vessel_id=619`; sin lotes.
- **Asistente abierto desde la Motonave origen (619)** con `action_open_vessel_rollover_wizard()`.
- **Previsualización (refresh):** sin bloqueos → `shipment_ids=[1644]`, `container_ids=[1629]`,
  `blocked_*=[]`, `block_summary=""`.
- **Confirmación** → acción `ir.actions.client` (notificación de éxito).
- **Después:** `vessel_id=620`, `voyage_id=False`, `state=draft`, `booking`
  **conservado**; `CONT-NOVOY` conserva `shipment_id=1644` y `state=loaded`;
  `container.vessel_id=620` (derivado de la relación).
- **Sin cambios** en stock / account / SV; auditoría y chatter publicados.

**Resultado: PASS.**

---

## 5. Resultado UAT-2 — Rolleo exitoso CON Viaje

- **Viaje destino** `565 UAT-VR-20261004-DEST-VOY-01` creado vía formulario/modelo estándar de Viajes,
  asociado a la Motonave destino 620 (`state=draft`).
- **Antes:** `SHIP-VOY` → `vessel_id=619`, `voyage_id=False`, `state=draft`,
  `booking=UAT-VR-20261004-BOOK-02`; `CONT-VOY` → `state=loaded`, `vessel_id=619`.
- **Previsualización:** sin bloqueos (`shipment_ids=[1645]`, `container_ids=[1630]`).
- **Después:** `shipment.vessel_id=620`, `shipment.voyage_id=565`,
  `voyage.vessel_id=620`; estado `draft`, booking conservado, contenedor 1630 sin cambios
  de estado/asociación (`vessel_id` derivado = 620).
- **Sin cambios** en stock / account / SV; auditoría y chatter completos (incluye chatter en el Viaje).

**Resultado: PASS.**

---

## 6. Resultado UAT-3 — Bloqueo estricto

- **Setup:** `SHIP-BLOCK 1646` en la Motonave origen 619 con `state=in_transit`,
  `booking=UAT-VR-20261004-BOOK-03`; `CONT-BLOCK 1631` `state=loaded` (sin rebaja).
- **Estado de los 3 embarques UAT capturado antes** del intento.
- **Previsualización (refresh):**
  - `shipment_ids=[]`, `container_ids=[]`
  - `blocked_shipment_ids=[1646]`, `blocked_container_ids=[1631]`
  - `block_summary`:
    ```
    Embarque UAT-VR-20261004-SHIP-BLOCK: estado no rolleable (Embarcado).
    ```
- **Intento de confirmación → `UserError`:**
  ```
  Rolleo abortado: la operación es total y existe al menos un Embarque o
  Contenedor bloqueado.

  Embarque UAT-VR-20261004-SHIP-BLOCK: estado no rolleable (Embarcado).
  ```
- **Después = Antes** para los 3 embarques UAT y sus contenedores (ninguna nave/viaje cambió).
- **Sin auditoría de éxito** (eventos `vessel_rollover*` se mantienen en 6; ninguno referencia el ID 1646).
- **Sin chatter de éxito** (conteos de mensajes en origen/destino/embarque/contenedor sin variación).
- **Sin movimientos de stock.**

**Resultado: PASS.**

---

## 7. Auditorías creadas y verificación de hashes

6 eventos, todos con `SHA-256(audit_snapshot) == audit_hash` y `user_id=8`.

| ID | action_type | batch_id | hash_ok |
|---:|---|---|:--:|
| 19699 | `vessel_rollover` (maestra) | `VESSEL-ROLLOVER-20261004035203000000` | ✔ |
| 19700 | `vessel_rollover_item` (shipment 1644) | `VESSEL-ROLLOVER-20261004035203000000` | ✔ |
| 19701 | `vessel_rollover_item` (container 1629) | `VESSEL-ROLLOVER-20261004035203000000` | ✔ |
| 19702 | `vessel_rollover` (maestra) | `VESSEL-ROLLOVER-20261004035217000000` | ✔ |
| 19703 | `vessel_rollover_item` (shipment 1645) | `VESSEL-ROLLOVER-20261004035217000000` | ✔ |
| 19704 | `vessel_rollover_item` (container 1630) | `VESSEL-ROLLOVER-20261004035217000000` | ✔ |

Snapshot maestra (UAT-1): origen `{vessel_id:619}`, destino `{vessel_id:620, voyage_id:false}`,
`summary={shipments_reassigned:1, containers_reassigned:1, shipments_blocked:0, containers_blocked:0}`.
Snapshot maestra (UAT-2): origen `{vessel_id:619}`,
destino `{vessel_id:620, voyage_id:565, voyage_name:"UAT-VR-20261004-DEST-VESSEL / UAT-VR-20261004-DEST-VOY-01"}`.

En el escenario bloqueado **no** se creó evento `vessel_rollover` ni `vessel_rollover_item`
(ninguno referencia el embarque 1646).

---

## 8. Chatter y trazabilidad

9 mensajes de rolleo publicados (subject `Rollover de Motonave`):

| Escenario | Modelo | res_id | Mensaje |
|---|---|---|---:|---|
| UAT-1 | `shipping.vessel` | 619 | Rolleo de planificación (origen) |
| UAT-1 | `shipping.vessel` | 620 | Recepción de planificación (destino) |
| UAT-1 | `lumber.export.shipment` | 1644 | Rolleo de planificación marítima |
| UAT-1 | `lumber.container` | 1629 | Rolleo derivado de su Embarque |
| UAT-2 | `shipping.vessel` | 619 | Rolleo de planificación (origen) |
| UAT-2 | `shipping.vessel` | 620 | Recepción de planificación (destino) |
| UAT-2 | `shipping.voyage` | 565 | Rolleo: ingreso al Viaje |
| UAT-2 | `lumber.export.shipment` | 1645 | Rolleo de planificación marítima |
| UAT-2 | `lumber.container` | 1630 | Rolleo derivado de su Embarque |

En UAT-3 **no** se publicó chatter de éxito.

---

## 9. Evidencia de cero movimiento de inventario

- `stock.move` 142→142, `stock.move.line` 209→209, `stock.picking` 27→27,
  `stock.quant` 169→169, `stock.lot` 126→126: **Δ0**.
- `stock.lot.cost.line`: 0 filas nuevas desde el inicio de la UAT;
  `lumber.shipment.cost.line` = 0.
- `account.move` 1→1, `account.payment` 0→0, `madenat.sv.operation` 1→1,
  `madenat.sv.imputation` 1→1: **Δ0**.
- No se ejecutó rebaja, reversa, zarpe, B-01, `action_draft`, entrega/cierre,
  retorno físico, imputación SV, costeo, facturación ni pagos.

---

## 10. Resumen de registros nuevos y no nuevos

**Nuevos (solo UAT nuevos autorizados):**
- +2 `shipping.vessel` (619, 620)
- +1 `shipping.voyage` (565)
- +3 `lumber.export.shipment` (1644, 1645, 1646)
- +3 `lumber.container` (1629, 1630, 1631)
- +6 `madenat.audit.log` (2 maestras + 4 ítem)
- Chatter de rolleo (9 mensajes) + mensajes de tracking propios de la creación

**No nuevos / sin cambios:** stock.move, stock.move.line, stock.picking, stock.quant,
stock.lot, stock.lot.cost.line, lumber.shipment.cost.line, account.move, account.payment,
madenat.sv.operation, madenat.sv.imputation, y toda la **UAT histórica protegida**.

---

## 11. Riesgos residuales

1. **Ejecución vía ORM de servidor, no cliqueo de UI.** Se invocaron exactamente los
   métodos de servidor que disparan los botones del formulario
   (`action_open_vessel_rollover_wizard` → `create` → `action_refresh_preview` →
   `action_confirm_rollover`). El render/UX del formulario no se valida aquí.
2. **`_audit_create` usa `sudo()` internamente** (código aprobado). El actor del evento
   sigue siendo `uid=8`. No confundir con ejecución UAT con sudo.
3. **Contrapartida histórica en `Partners/Vendors = -0.1440`** en lotes 15970/15971
   (pre-existente, no tocada). Confirmar con Operaciones que es el saldo esperado del ledger SV.
4. **Variación por línea base “viva”:** si el entorno recibe tráfico concurrente, repetir el
   precheck antes de cualquier re-ejecución.
5. **Aislamiento por Motonave origen:** el alcance del asistente es “todos los embarques de la
   Motonave origen”. Aquí las Motonaves origen fueron nuevas y exclusivas, por lo que el alcance
   quedó limitado a los embarques UAT. En producción, el rolleo afecta a **todos** los embarques
   `draft`/`confirmed` de la nave origen (comportamiento por diseño).
6. **El escenario de bloqueo usó `in_transit`** (caso seguro sin movimiento físico), según lo
   previsto por el procedimiento al no existir fixture de contenedor `rebajado` sin movimiento.
   No se probó el bloqueo por contenedor `rebajado` en esta UAT.

---

## 12. Dictamen único

> **A. `UAT ROLLEO DE MOTONAVE APROBADA — APTO PARA DOCUMENTAR Y OPERAR`.**


