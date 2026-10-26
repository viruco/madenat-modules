# MADENAT — Resultado UAT Borrador Seguro

```
Documento : UAT-DRAFT-20261004_RESULTADO
Feature   : Volver a Borrador Seguro en lumber.export.shipment (Sub-bloque 2)
Fase      : D (validación operativa aislada — sin rebaja, sin reversa, sin zarpe,
            sin movimiento de inventario)
Entorno   : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha     : 2026-10-04 (15:17–15:25 UTC)
Ejecutor  : uid 2 mauricio.seo@gmail.com — Gerencia / Jefatura de Operaciones (env su=False)
Evidencia : ./UAT_DRAFT_20261004/00..05*.txt
Dictamen  : A. UAT BORRADOR SEGURO APROBADA — APTO PARA CONTINUAR CON B-01
```

---

## 1. Fecha, entorno y usuarios ejecutores

- **Fecha/hora:** 2026-10-04, 15:17–15:25 UTC.
- **Entorno:** `madenat_test`; `odoo18_app` Up; `odoo18_db` healthy (postgres:15); HTTP 200.
- **Método:** ORM vía `odoo shell -d madenat_test --no-http`. Acciones con `env(user=2)`
  (`su=False`). **Sin `sudo()`** en el runner, **sin SQL de escritura**, **sin update/install**
  de módulos, **sin edición** de código/XML/CSV/manifest/tests/ACL/docs. Se usó `cr.commit()`
  (commit de base de datos) para persistir la UAT — no es commit de git.
- **Usuarios:**
  - **Ejecutor (permitido):** uid 2 `mauricio.seo@gmail.com` — grupos Operaciones,
    Jefatura de Operaciones y Gerencia. `env(user=2).su = False` (no es el superusuario).
  - **Bloqueado — Operaciones:** uid 8 `cristhian.elguetag@gmail.com` (solo Operaciones).
  - **Bloqueado — interno común:** uid 6 `leonardo@pinelli.com.mx` (sin Jef/Ger/Oper).
  - **Auditoría funcional** (`group_madenat_auditoria`, id 298): **sin usuarios** → no disponible.
  - Superusuario uid 1 (`__system__`/OdooBot) **no usado**.

> **Observación de control (importante).** El único usuario existente con Jefatura/Gerencia
> es la cuenta semilla **uid 2, cuyo nombre es «Administrator»** y que además posee
> `base.group_system`. No existe en la base ningún usuario Jefatura/Gerencia que no sea esa
> cuenta, y la UAT prohíbe crear usuarios. La ejecución se hizo con `su=False` y la resolución
> de permisos del guard es **por pertenencia real a grupo** (demostrado porque los uid 8/6
> reciben `AccessError`). Se recomienda, antes de producción, un re-run confirmatorio con un
> usuario **Jefatura de Operaciones dedicado y sin `group_system`**. Si el responsable considera
> «cuenta Administrator» una exclusión dura, los escenarios D1/D2/D3 deben repetirse con ese
> usuario dedicado.

---

## 2. Precheck y línea base

- **Identidad:** repo `/custom_addons`; rama `feat/guia-correccion-documental-preservada-20261002`;
  HEAD `34c81272bb07d48db98d73a7734c81a2a8e384fa`; `git status --porcelain` = **25 entradas
  (21 M + 4 ??)**, idénticas antes y después (solo Rolleo de Motonave + Borrador Seguro).
- **Runtime:** Core + Logistics + Shipping Core + Costing + Billing + Vendor Payment instalados.
- **Contrato verificado en código:** `action_draft` exige `state='confirmed'`;
  `_assert_can_return_to_draft()` existe; `write({'state':'draft'})` protegido por token efímero
  de proceso; botón visible solo Jefatura/Gerencia y solo en Confirmado;
  `shipment_return_to_draft` presente en el Selection de `madenat.audit.log`.
- **Línea base (antes):** stock.move 142 · move.line 209 · picking 27 · quant 169 · lot 126 ·
  shipment 7 · container 8 · shipment.line 5 · vessel 5 · voyage 1 · audit 262 · sv.operation 1 ·
  sv.imputation 1 · lot.cost.line 53 · shipment.cost.line 0 · consolidation 0 · account.move 1 ·
  payment 0.
- **Histórica protegida:** verificada antes/después, **sin cambios** (ver §10).
- **Criterio de detención:** no activado.

---

## 3. IDs/nombres de los datos UAT nuevos

| Tipo | ID | Nombre | Estado final |
|---|---:|---|---|
| Shipment | 1704 | `UAT-DRAFT-20261004-OK` | **draft** |
| Container | 1678 | `UAT-DRAFT-20261004-CONT-OK` | loading |
| Shipment | 1705 | `UAT-DRAFT-20261004-PHYS-BLOCK` | confirmed |
| Container | 1679 | `UAT-DRAFT-20261004-CONT-PHYS-BLOCK` | rebajado (fixture) |
| Shipment | 1706 | `UAT-DRAFT-20261004-PERM-BLOCK` | confirmed |
| Shipment | 1707 | `UAT-DRAFT-20261004-TERM-BLOCK` | in_transit |
| Container | 1680 | `UAT-DRAFT-20261004-CONT-TERM-BLOCK` | loading |
| Audit log | 19742 | `shipment_return_to_draft` (batch_id=1704) | append-only |

No se creó Motonave/Viaje/Booking/lote/picking/movimiento/quant/guía/SV/costo/factura/pago.

---

## 4. UAT-D1 — retorno permitido `confirmed → draft`

- Ejecutado por uid 2. `action_draft()` devolvió `{'tag':'reload'}`.
- `shipment.state='draft'`, `actual_departure=False`; contenedor 1678 intacto (`loading`,
  shipment_id=1704).
- **Auditoría:** exactamente **1** evento `shipment_return_to_draft` (id 19742), actor=uid 2,
  hash SHA-256 correcto, snapshot `state_before='confirmed'` / `state_after='draft'`.
- **Chatter:** 1 mensaje «Retorno seguro a borrador».
- **Delta:** solo `madenat.audit.log +1`; resto 0.
- **Re-ejecución** sobre el mismo embarque ya `draft` → `UserError` (transición no permitida) y
  **0** auditoría adicional.

## 5. UAT-D2 — bloqueo físico

- Fixture (alternativa A): contenedor 1679 `loading → rebajado` por ORM, **sin** movimiento de
  inventario, sin picking, sin stock, sin SV, sin costo.
- `action_draft()` → **`UserError`** con sección **`[Rebaja física / salida]`**
  («Contenedores rebajados/embarcados: UAT-DRAFT-20261004-CONT-PHYS-BLOCK»).
- `shipment.state='confirmed'` sin cambio; contenedor sin cambio; **0** auditoría; **0** chatter
  de éxito; delta de inventario/costos/SV/auditoría = 0.

## 6. UAT-D3 — bloqueo terminal

- `in_transit` sin rebaja (decisión documentada: NO se usó `action_set_in_transit`/zarpe porque
  el flujo estándar exige rebaja física o B-01, ambos prohibidos, y publica chatter; el dato se
  creó directo por ORM, sin efectos, igual que el test T-D7).
- `action_draft()` → **`UserError`** «la única transición permitida es Confirmado → Borrador
  (estado actual: Embarcado)».
- `shipment.state='in_transit'` sin cambio; contenedor 1680 sin cambio; **0** auditoría;
  **0** chatter; delta = 0.

## 7. UAT-D4 — bloqueo de permisos y RPC/write directo

- `action_draft()` como **Operaciones (uid 8)** y como **interno común (uid 6)** → **`AccessError`**
  («Se requiere el rol de Jefatura de Operaciones o Gerencia»).
- `write({'state':'draft'})` como uid 8 y uid 6 → **`UserError`** (vía lateral cerrada).
- `with_context(allow_draft=True).write({'state':'draft'})` como uid 8 → **`UserError`**
  (el contexto RPC no otorga token; token efímero de proceso).
- `write({'state':'draft'})` como uid 2 (autorizado, sin `action_draft`) → **`UserError`**
  (puerta lateral cerrada también al autorizado).
- `shipment.state='confirmed'` sin cambio; **0** auditoría; **0** chatter; delta = 0.
- Auditoría funcional: **sin usuarios** → no probada directamente (cubierta por contrato de grupo).

## 8. Auditoría append-only, hash y chatter

- Evento 19742: `action_type='shipment_return_to_draft'`, `batch_id='1704'`,
  `user_id=2` (= ejecutor), `audit_hash` = `sha256(audit_snapshot)` (**True**).
- Snapshot incluye `operation`, `shipment{id,name,state_before='confirmed',state_after='draft'}`,
  `voyage`, `containers[]`, `lines[]`, `checks_passed`, `write.fields`.
- Chatter de éxito en shipment 1704: 1. (El `author_id` resuelve al partner 3 «Administrator»,
  partner ligado al uid 2; el actor autoritativo en auditoría es uid 2.)

## 9. Evidencia de cero movimiento físico y cero cambio financiero

`stock.move`, `stock.move.line`, `stock.picking`, `stock.quant`, `stock.lot`,
`stock.lot.cost.line`, `lumber.shipment.cost.line`, `lumber.billing.consolidation`,
`account.move`, `account.payment`, `madenat.sv.operation`, `madenat.sv.imputation`: **Δ0**.
Únicos cambios: +4 shipment, +3 container, +1 audit.

## 10. Integridad de UAT histórica y UAT Rolleo

`PROT_UNCHANGED = True` para: Shipment 1537 (in_transit) · Container 1509 (shipped) ·
Picking 7065 (done) · Líneas 1880/1881 (rebajado) · Lotes 15970/15971 (internal=0,
Customers=+0.144) · Guías 32298/32300 · Lotes 15892/15894 · Container 1500 (rebajado) ·
Shipment 1528 (draft) · SV op 5822 · Imputación 492 · Picking 7062 (done) ·
UAT Rolleo: Vessels 619/620, Voyage 565, Shipments 1644/1645/1646, Containers 1629/1630/1631,
Audit logs 19699–19704.

## 11. Evidencia persistida

Directorio `./UAT_DRAFT_20261004/`: `00_precheck_baseline.txt`, `01_uat_d1_allowed.txt`,
`02_uat_d2_physical_block.txt`, `03_uat_d3_terminal_block.txt`,
`04_uat_d4_permissions_block.txt`, `05_final_validation.txt`, este `RESULTADO.md`,
`raw_run.txt` (salida cruda) y los runners (`.py.txt`). Verificación post-commit en proceso
independiente: shipment 1704 draft / 1705 confirmed / 1706 confirmed / 1707 in_transit;
audit 19742 presente con hash OK.

## 12. Riesgos residuales

1. **Reversa física parcial:** la UAT no ejecutó reversa; el bloqueo físico se validó por estado de
   contenedor (fixture), no por picking/stock reales. La reversa física queda **sin validar aquí**.
2. **B-01:** no ejecutado. Pendiente la UAT de B-01 (próximo bloque).
3. **Entrega/Cierre:** no ejecutado/sin validar.
4. **Retorno físico / SV:** no ejecutado/sin validar.
5. **Identidad del ejecutor:** único usuario Jefatura/Gerencia = cuenta «Administrator» (uid 2,
   con `group_system`). Re-run confirmatorio recomendado con usuario Jefatura dedicado (§1).
6. **D3 – método de creación:** el dato terminal se creó por ORM directo (no por el botón de
   zarpe) para evitar rebaja física/B-01; sujeto a confirmación del responsable.
7. **Línea base «viva»:** repetir el precheck antes de cualquier re-ejecución.

## 13. Dictamen único

> **A. `UAT BORRADOR SEGURO APROBADA — APTO PARA CONTINUAR CON B-01`.**
>
> Los cuatro escenarios se comportaron exactamente según el contrato: D1 permitido con
> confirmed→draft, con 1 evento audit firmado y 1 chatter; D2 bloqueado por rebaja física;
> D3 bloqueado por estado terminal; D4 bloqueado por permisos y por la puerta lateral
> `write`, incluso con contexto `allow_draft`. Cero movimiento de inventario, cero cambio
> financiero, histórica y UAT Rolleo intactas.
>
> **Condición:** dar por aceptada la cuenta uid 2 como ejecutor Jefatura/Gerencia **o** ejecutar
> un re-run confirmatorio con un usuario Jefatura de Operaciones dedicado (no-Administrator).
