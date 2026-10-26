# MADENAT — Resultado UAT B-01 Documental Bloqueante

```
Documento : UAT B-01 (Sub-bloque 3) — Zarpe con excepción B-01 (Política B)
Fase      : D — Validación operativa (UAT aislada y controlada)
Entorno   : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha     : 2026-10-04 (16:12Z precheck · 16:20Z runner · 16:21Z verificación)
Repo      : /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons
Rama/HEAD : feat/guia-correccion-documental-preservada-20261002 · 34c81272bb07d48db98d73a7734c81a2a8e384fa
Alcance   : SIN regularización física, SIN retorno, SIN costeo/facturación/pagos.
Dictamen  : A. UAT B-01 DOCUMENTAL BLOQUEANTE APROBADA — APTO PARA DISEÑAR REGULARIZACIÓN Y CIERRE
```

---

## 1. Fecha, entorno y usuarios

| Item | Valor |
|---|---|
| Base de datos | `madenat_test` |
| Contenedores | `odoo18_app` Up (127.0.0.1:8069) · `odoo18_db` healthy (postgres:15) |
| HTTP | 200 en `/web/login` |
| Método | ORM vía `odoo shell -d madenat_test --no-http` (stdin). SIN `sudo()`, SIN SQL de escritura, SIN `update/install`, SIN `uid 1` en las acciones. |
| Working tree | 28 entradas (`git status --porcelain`), idéntico antes y después; HEAD sin cambios |

**Usuarios (solo existentes; no se crearon usuarios):**

| Rol | uid | login | Grupos | Nota |
|---|---|---|---|---|
| Ejecutor autorizado | 2 | mauricio.seo@gmail.com | JEF=Ger=True, OPE=True, **base.group_system=True**, `env.su=False` | Único con Jefatura/Gerencia. Autorizado expresamente por el usuario para esta UAT (§12 limitación de segregación). No es `uid 1`. |
| Bloqueado (Operaciones) | 8 | cristhian.elguetag@gmail.com | Solo Operaciones (JEF/GER/AUD=False) | Se mantiene solo Operaciones. |
| Bloqueado (interno común) | 6 | leonardo@pinelli.com.mx | Sin roles MADENAT | Interno común. |
| Auditoría | — | — | `group_madenat_auditoria` **sin miembros** | NO disponible; no se creó usuario. |
| Superusuario | 1 | OdooBot | — | **NO usado.** |

---

## 2. Precheck y línea base

- **Identidad:** repo `custom_addons`, rama y HEAD confirmados; trabajos previos preservados (Rolleo + Borrador Seguro); 28 entradas esperadas.
- **Runtime:** `base, stock, account, mail, madenat_lumber_core, madenat_lumber_logistics, madenat_lumber_shipping_core, madenat_lumber_costing, madenat_lumber_billing, madenat_vendor_payment` instalados.
- **Implementación B-01 confirmada (solo lectura):** campos `b01_exception_state/_reason/_opened_at/_opened_by_id/_audit_id` presentes; guards `_assert_can_depart`, `_set_in_transit`, `action_set_in_transit`, `action_deliver`, `_create_b01_exception_audit`, `_assert_b01_write_authorized` presentes; `'b01_departure_exception'` en el Selection de `madenat.audit.log.action_type`.
- **Sin B-01 persistida previa:** `b01_departure_exception`=0, `deviation` con `[B-01]`=0, `b01_exception_state='open'`=0, `='resolved'`=0, embarques `UAT-B01-20261004`=0.

**Línea base (antes) → después:**

| Modelo | Antes | Después | Δ |
|---|---|---|---|
| stock.move | 142 | 142 | 0 |
| stock.move.line | 209 | 209 | 0 |
| stock.picking | 27 | 27 | 0 |
| stock.quant | 169 | 169 | 0 |
| stock.lot | 126 | 126 | 0 |
| stock.lot.cost.line | 53 | 53 | 0 |
| lumber.shipment.cost.line | 0 | 0 | 0 |
| lumber.export.shipment | 11 | **14** | **+3** |
| lumber.container | 11 | **15** | **+4** |
| lumber.shipment.line | 5 | 5 | 0 |
| shipping.vessel | 5 | **6** | **+1** |
| shipping.voyage | 1 | 1 | 0 |
| madenat.audit.log | 263 | **265** | **+2** |
| madenat.sv.operation | 1 | 1 | 0 |
| madenat.sv.imputation | 1 | 1 | 0 |
| lumber.billing.consolidation | 0 | 0 | 0 |
| account.move | 1 | 1 | 0 |
| account.payment | 0 | 0 | 0 |

> Única variación = registros UAT autorizados (3 Embarques, 4 Contenedores, 1 Motonave) + 2 eventos de auditoría de UAT-B01-2. Cero movimiento de stock/costos/finanzas/SV.

**Criterio de detención:** no se activó por datos. Se activó la **confirmación obligatoria** por único ejecutor Jefatura/Gerencia = `uid 2` con `base.group_system`; con autorización explícita del usuario se procedió (ver §12).

---

## 3. Datos UAT creados

Prefijo único `UAT-B01-20261004-`. Fixture mínimo (sin lote, sin línea, sin picking, sin movimiento de stock):

| Registro | Modelo | ID | Detalle |
|---|---|---|---|
| UAT-B01-20261004-CUSTOMER | res.partner | 14120 | Consignatario UAT |
| UAT-B01-20261004-VESSEL | shipping.vessel | 746 | Motonave UAT |
| UAT-B01-20261004-NORMAL | lumber.export.shipment | 1867 | `confirmed` → `in_transit`; b01=none |
| UAT-B01-20261004-CONT-NORMAL | lumber.container | 1868 | `state='rebajado'` → `shipped` |
| UAT-B01-20261004-EXCEPTION | lumber.export.shipment | 1868 | `confirmed` → `in_transit`; b01=open |
| UAT-B01-20261004-CONT-REB | lumber.container | 1869 | `rebajado` → `shipped` |
| UAT-B01-20261004-CONT-PENDING | lumber.container | 1870 | `loaded` **conservado** |
| UAT-B01-20261004-PERM | lumber.export.shipment | 1869 | `confirmed` (sin zarpe); b01=none |
| UAT-B01-20261004-CONT-PERM-PEND | lumber.container | 1871 | `loaded` (pendiente de permisos) |

**"Rebajado físico" UAT:** representado por el **estado propio del contenedor `state='rebajado'`** (estado AD-82/CANON-18 §3.2, evidencia real aceptada por `_is_container_rebajado_fisico`). **No** se crean lote, línea, picking ni movimiento de stock → Opción A del mandato cumplida SIN SQL, SIN sudo, SIN movimiento físico.

> *Desviación mínima documentada:* se creó `UAT-B01-20261004-CONT-PERM-PEND` (no listado) por el `UNIQUE(name)` de `lumber.container`, requerido para el escenario de permisos.

---

## 4. UAT-B01-1 — Zarpe normal (todos rebajados)

Comando: `s_normal.with_user(2).action_set_in_transit()`.

| Campo | Antes | Después |
|---|---|---|
| shipment.state | `confirmed` | **`in_transit`** |
| shipment.actual_departure | — | timestamp presente |
| shipment.b01_exception_state | `none` | `none` |
| shipment.b01_exception_audit_id | — | vacío |
| CONT-NORMAL.state | `rebajado` | **`shipped`** |

- Auditoría B-01 creada = **0**; eventos `b01_departure_exception` = **0**.
- Chatter de zarpe normal presente (`Zarpe Confirmado`): 1 mensaje.
- Δ stock/costos/finanzas/SV = **0** (stock.move, move.line, picking, quant, lot, lot.cost.line, shipment.cost.line, account.move, account.payment, sv.operation, sv.imputation, billing.consolidation). No se creó movimiento/picking/quant/lote/costo/factura/pago/SV adicional.

**Resultado: PASS.** `N1_CHECK` = {state_in_transit, container_shipped, b01_none, b01_audit_empty, no_b01_audit, no_extra_stock, no_extra_cost_fin_sv, no_extra_audit} = todos `true`.

---

## 5. UAT-B01-2 — Excepción documental B-01

Comando: wizard `lumber.shipment.zarpe.wizard` (id 87; `pending_count=1`, `pending_names=UAT-B01-20261004-CONT-PENDING`) + `action_zarpar_con_excepcion()` como uid 2.
Motivo (exacto): `Contenedor pendiente de rebaja física por contingencia documental UAT.`

| Campo | Valor |
|---|---|
| shipment.state | **`in_transit`** |
| shipment.actual_departure | presente |
| b01_exception_state | **`open`** |
| b01_exception_reason | motivo exacto (`reason_exact=True`) |
| b01_exception_opened_at | `2026-10-04 16:20:39` |
| b01_exception_opened_by_id | **2** (ejecutor) |
| b01_exception_audit_id | **19890** |
| CONT-PENDING.state | **`loaded`** (igual al previo) |
| CONT-REB.state | **`shipped`** (rebajado→shipped) |

- Auditorías: `b01_departure_exception`=1; `deviation` (compat AD-88, `[B-01]`)=1 → Δ `madenat.audit.log`=+2.
- Snapshot firma: `rebajados=[CONT-REB]`, `pendientes=[CONT-PENDING]`, `reason` exacto, `gates` = draft/rollover/delivery/costing/billing/payments = **blocked**, `physical_invariants` = no_stock_movement/no_quant_change/no_picking_created = true.
- Chatter: mensaje B-01 (`Zarpe con excepción B-01`) + mensaje de excepción textual (`Excepción registrada [B-01]`).
- Δ stock/costos/finanzas/SV = **0**.

**Resultado: PASS.** `E2_CHECK` = todos `true` (incluye `c_pen_conserved`, `c_reb_shipped`, `one_b01_audit`, `audit_delta_2`).

---

## 6. UAT-B01-3 — Entrega/Cierre bloqueada

Comando: `s_exc.with_user(2).action_deliver()` sobre el Embarque con B-01 `open`.

- Resultado: **`UserError`** → *"No se puede entregar el Embarque UAT-B01-20261004-EXCEPTION: tiene una excepción B-01 open. Regularice la excepción antes de la Entrega/Cierre."*
- `shipment.state` permanece **`in_transit`**.
- `b01_exception_state` permanece **`open`**.
- No nueva auditoría B-01 (Δ `b01_departure_exception`=0).
- No chatter de entrega exitosa (`Embarque entregado`=0).
- Δ stock/costos/facturas/pagos/SV = **0**.

**Resultado: PASS.** `D3_CHECK` = todos `true`.

---

## 7. UAT-B01-4 — Permisos y protección de escritura

Sobre `UAT-B01-20261004-PERM` (id 1869, `confirmed`) con contenedor pendiente.

| Intento | Usuario | Resultado observado |
|---|---|---|
| `_set_in_transit()` (confirmar zarpe) | uid 8 Operaciones | **AccessError** (requiere Jefatura/Gerencia) |
| `action_set_in_transit()` | uid 8 Operaciones | **Sin error** → devuelve acción del wizard (abrir/previsualizar) |
| wizard `action_zarpar_con_excepcion()` (B-01) | uid 8 Operaciones | **AccessError** |
| wizard `action_rebajar_y_zarpar()` | uid 8 Operaciones | **AccessError** |
| `action_deliver()` | uid 8 Operaciones | **AccessError** |
| `_set_in_transit()` | uid 6 interno común | **AccessError** |
| `action_set_in_transit()` | uid 6 interno común | **AccessError** (rol de operación de zarpe) |
| `write({'b01_exception_state':'open', 'b01_exception_reason':...})` | uid 8 | **UserError** (solo por flujo autorizado) |
| `with_context(allow_b01=True, b01_internal=True).write({'b01_exception_state':'open'})` | uid 8 | **UserError** (contexto no elude) |
| `with_context(allow_b01=True, b01_internal=True).write({'b01_exception_state':'open'})` | uid 6 | **UserError** |
| `write({'b01_exception_state':'open'})` (ejecutor, sin flujo) | uid 2 | **UserError** |
| `write({'b01_exception_state':'resolved'})` | uid 8 | **UserError** (regularización no habilitada) |
| Auditoría (rol) | — | **NO disponible** (grupo sin miembros); no se creó usuario |

Verificación final: shipment `state=confirmed`, `b01_exception_state=none`, contenedor `loaded`, 0 auditorías B-01, Δ físico/financiero = **0**.

**Resultado: PASS** (con una precisión de contrato): el mandato listaba `action_set_in_transit()` de Operaciones como "esperar AccessError"; el **contrato vigente** indica que Operaciones *puede abrir/previsualizar* pero **no confirmar** — y la implementación lo cumple: `action_set_in_transit()` de Operaciones devuelve el wizard (sin confirmar), mientras **toda** vía de confirmación (normal/B-01/rebaja) y la Entrega levantan `AccessError`. La protección de escritura de campos B-01 (`UserError`, token de proceso) resiste usuario bloqueado y contexto falso.

---

## 8. Auditoría / hash / chatter

- Auditoría B-01 persistida: `madenat.audit.log` **id 19890**, `action_type='b01_departure_exception'`, `batch_id='1868'`, `user_id=2`.
- **SHA-256 verificado** (runner y proceso nuevo): `sha256(audit_snapshot) == audit_hash` → **True** (en ambos procesos).
- Desviación textual AD-88 persistida: id 19889, `action_type='deviation'`, `[B-01] ...`, hash válido → **True**.
- Snapshot identifica **rebajados** (`CONT-REB`) y **pendientes** (`CONT-PENDING`); gates de excepción coherentes; actor y motivo correctos.
- **Chatter** del Embarque EXCEPTION: mensaje B-01 + mensaje de excepción textual + rendimiento + alta; autor = partner 3 "Administrator" = **uid 2** (no uid 1).
- Recalculo de hash de **toda** auditoría B-01 persistida (`ALL_B01_AUDITS=1`): `hash_ok=True`.
- **Ningún** escenario fallido/permisos generó B-01: `b01_exception_state='open'` solo en `UAT-B01-20261004-EXCEPTION`; `resolved`=0.

---

## 9. Inventario, lotes, costos, finanzas y SV

Δ global (después − antes) tras **toda** la UAT:

| Dominio | Modelos | Δ |
|---|---|---|
| Inventario | stock.move, stock.move.line, stock.picking, stock.quant, stock.lot | **0** |
| Lotes/costos | stock.lot.cost.line, lumber.shipment.cost.line | **0** |
| SV | madenat.sv.operation, madenat.sv.imputation | **0** |
| Finanzas | account.move, account.payment, lumber.billing.consolidation | **0** |
| Registros UAT | lumber.export.shipment +3, lumber.container +4, shipping.vessel +1 | (autorizados) |
| Auditoría | madenat.audit.log +2 (deviation `[B-01]` + `b01_departure_exception`) | (generados por UAT-B01-2) |

El zarpe (normal y B-01) **no descuenta stock** (AD-82): no se creó ninguna rebaja, picking, movimiento ni quant. No se creó lote, línea, costo, factura, pago, consolidación, guía, operación o imputación SV. La rebaja física UAT se representó como **estado** del contenedor, sin mover inventario.

---

## 10. Integridad de UAT histórica, Rolleo y Borrador Seguro

`PROT_UNCHANGED` = **todos `true`** para las 39 claves verificadas antes y después:

- **Histórica logística:** Shipment 1537 `in_transit`; Container 1509 `shipped`; Picking 7065 `done`; Líneas 1880/1881 `rebajado`; Lotes 15970/15971 (internal=0.0, customer=+0.144).
- **Histórica SV:** Shipment 1528 `draft`; Container 1500 `rebajado`; Picking 7062 `done`; SV operation 5822 `SVO005684`; Imputation 492 `IMP00946`; Guías 32298/32300; Lotes 15892/15894.
- **UAT Rolleo:** Vessels 619/620; Voyage 565; Shipments 1644/1645/1646; Containers 1629/1630/1631; Audits 19699–19704.
- **UAT Borrador Seguro:** Shipments 1704/1705/1706/1707; Containers 1678/1679/1680; Audit 19742.

No se reutilizó ningún registro protegido como origen, destino, fixture, contenedor o evidencia. No se ejecutó Borrador, Rolleo, reversa, retorno, SV, costeo, facturación, pagos ni BT-04/Maquila.

---

## 11. Evidencia persistida

Directorio: `/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_B01_20261004/`

| Archivo | Contenido |
|---|---|
| `00_precheck_baseline.txt` | Precheck e línea base (identidad, runtime, conteos, protegidos, usuarios, STOP/confirmación) |
| `01_uat_b01_normal.txt` | UAT-B01-1 (before/after, Δ, checks) |
| `02_uat_b01_exception.txt` | UAT-B01-2 (before/after, motivo, auditoría, Δ, checks) |
| `03_uat_b01_delivery_block.txt` | UAT-B01-3 (error esperado, estado, Δ, checks) |
| `04_uat_b01_permissions.txt` | UAT-B01-4 (matriz de intentos/errores, checks) |
| `05_final_validation.txt` | Validación final (Δ, protegidos, hash, verificación post-commit) |
| `UAT-B01-20261004_RESULTADO.md` | Este informe |
| `runner_uat_b01_20261004.py.txt` | Runner ejecutado (ORM, sin sudo/uid1) |
| `verify_final_20261004.py.txt` | Verificación post-commit (proceso nuevo) |
| `precheck_runner.py.txt` | Script de precheck (solo lectura) |
| `raw_precheck.txt`, `raw_run.txt`, `raw_verify_final.txt` | Salidas crudas de `odoo shell` |

---

## 12. Riesgos residuales

1. **B-01 `open` sin resolución implementada.** No existe acción de regularización/cierre (`resolved` bloqueado por `_assert_b01_write_authorized` y por ausencia de UI). El Embarque `UAT-B01-20261004-EXCEPTION` permanece `in_transit` + B-01 `open` **por diseño**; su regularización requiere un sub-bloque posterior. *(No se resolvió B-01.)*
2. **Retorno físico / SV.** No implementado en esta entrega; no se ejecutó. La B-01 abierta implica que la reversa/retorno formará parte de la regularización futura.
3. **Entrega/Cierre.** Bloqueado por contrato (UserError) mientras la B-01 esté `open`/`resolved` o existan pendientes. Verificado. No hay flujo de cierre con B-01 abierta.
4. **Costeo/Billing/Pagos.** No implementados para B-01; no ejecutados. El snapshot marca `costing/billing/payments = blocked`.
5. **Revalidación futura de Borrador/Rolleo contra el campo relacional B-01 (hallazgo).** `_assert_can_return_to_draft` detecta la B-01 a través de la **desviación textual legacy** (`'[B-01]'` en logs `deviation`), **no** del campo relacional `b01_exception_state`. Hoy coincide porque el zarpe B-01 crea además la desviación textual; pero el campo relacional no es consultado. El guard de Rolleo (`_assert_rollover_eligible`) tampoco consulta el campo: el rolleo queda bloqueado de forma **transitiva** (el embarque B-01 está `in_transit`). **Recomendación:** en la fase de regularización, hacer que Borrador y Rolleo consulten explícitamente `b01_exception_state in ('open','resolved')`, para no depender de la evidencia textual.
6. **Limitación de segregación del ejecutor.** El único usuario con Jefatura/Gerencia es `uid 2` "Administrator", que además tiene `base.group_system`. La segregación **de confirmación** sí quedó validada con usuarios **no-administradores** (uid 8 Operaciones y uid 6 interno) bloqueados correctamente; pero no fue posible validar el **camino permitido** con un Jefatura/Gerencia **no**-administrador (no existe). Autorizado expresamente por el usuario para esta UAT. **Recomendación:** crear una cuenta de Jefatura dedicada no-administradora para futuras UAT.
7. **Auditoría no disponible.** `group_madenat_auditoria` sin miembros → el escenario "Auditoría bloqueada" no se pudo ejecutar con usuario real; se documenta la no disponibilidad (no se creó usuario).
8. **Observación estática (no ejecutada), fuera del alcance B-01.** El override `write()` sólo protege `state='draft'` y los campos B-01; un `write({'state':'in_transit'})` directo no atraviesa las guards de rol del flujo de zarpe. No se ejecutó para no contaminar los datos UAT. Se sugiere revisar en la fase de regularización.

---

## 13. Dictamen

> **A. `UAT B-01 DOCUMENTAL BLOQUEANTE APROBADA — APTO PARA DISEÑAR REGULARIZACIÓN Y CIERRE`.**

Fundamento:
- **UAT-B01-1 (PASS):** zarpe normal → Embarque `in_transit`, contenedor rebajado → `shipped`, B-01 `none`, sin auditoría, sin movimiento adicional de stock.
- **UAT-B01-2 (PASS):** B-01 → `in_transit`, rebajados `shipped`, **pendiente conserva su estado**, B-01 `open` con motivo/usuario/fecha/auditoría SHA-256 válida, gates bloqueados, chatter; sin rebaja/stock/costeo/cierre.
- **UAT-B01-3 (PASS):** Entrega bloqueada (`UserError`), Embarque sigue `in_transit`, B-01 sigue `open`, sin nuevos movimientos/costos/documentos.
- **UAT-B01-4 (PASS):** Operaciones/Interno no confirman zarpe normal ni B-01 (AccessError); escritura directa de campos B-01 bloqueada (UserError), incluso con contexto falso.
- Cero movimiento de inventario/costos/finanzas/SV; histórica, Rolleo y Borrador Seguro intactos; sin commit/push/PR; sin cambios de código/configuración/ACL.

---

**Fin del informe. No se resolvió B-01. No se avanzó a Retorno SV ni Entrega/Cierre. No se modificó código. Sin commit ni push.**




