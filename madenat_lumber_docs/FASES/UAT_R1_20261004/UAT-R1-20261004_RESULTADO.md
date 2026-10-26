# MADENAT — Resultado UAT R1 y Cierre B-01

```
Documento : UAT Sub-bloque 4A — Regularización B-01 por rebaja extemporánea (R1) y cierre explícito
Fase      : D — Validación operativa (UAT aislada y controlada, con rebaja física real)
Entorno   : madenat_test · odoo18_app Up (127.0.0.1:8069) · odoo18_db healthy (postgres:15) · HTTP 200
Fecha     : 2026-10-04 (17:11–17:18 UTC · 14:11–14:18 -03:00)
Repo      : /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons
Rama/HEAD : feat/guia-correccion-documental-preservada-20261002 · 34c81272bb07d48db98d73a7734c81a2a8e384fa
Alcance   : R1 (rebaja física extemporánea) + cierre open→resolved. SIN R2, SIN retorno, SIN R3/SV,
            SIN entrega, SIN costeo/facturación/pagos/consolidación.
Dictamen  : A. UAT R1 Y CIERRE B-01 APROBADA — APTO PARA DISEÑAR R2/R3 Y ENTREGA
```

---

## 1. Fecha, entorno y usuarios

| Ítem | Valor |
|---|---|
| Base de datos | `madenat_test` |
| Contenedores | `odoo18_app` Up · `odoo18_db` healthy (postgres:15) · HTTP 200 en `/web/login` |
| Método | ORM vía `odoo shell -d madenat_test --no-http` (stdin). SIN `sudo()`, SIN SQL de escritura, SIN `update/install`, SIN `uid 1` en las acciones de contrato |
| Working tree | 31 entradas (`git status --porcelain`: 23 `M` + 8 `??`), idéntico antes y después; HEAD sin cambios |

**Usuarios (solo existentes; no se crearon usuarios):**

| Rol | uid | login | Grupos relevantes | Nota |
|---|---|---|---|---|
| Ejecutor Gerencia | 2 | mauricio.seo@gmail.com | GER=JEF=OPE=True, **base.group_system=True**, `env.su=False` | **Autorizado explícitamente** por el usuario para esta UAT (único con Gerencia). NO es `uid 1`. |
| Bloqueado — Operaciones | 8 | cristhian.elguetag@gmail.com | Solo Operaciones | Rechazado en R1 y cierre (AccessError). |
| Bloqueado — interno común | 6 | leonardo@pinelli.com.mx | Sin roles MADENAT | Rechazado en R1 y cierre (AccessError). |
| Auditoría | — | — | `group_madenat_auditoria` **sin miembros** | NO disponible; no se creó usuario. |
| Superusuario | 1 | OdooBot (`__system__`, inactivo) | — | **NO usado.** |

---

## 2. Precheck y línea base

- **Identidad:** repo, rama y HEAD confirmados; trabajos previos preservados (Rolleo, Borrador Seguro, UAT B-01 previa).
- **B-01 de partida:** 0 `resolved`; única `open` = UAT previa **Shipment 1868**; `b01_regularization`/`b01_resolution` persistidas = 0.
- **Línea base global** (`BASE0`, evidencia `00`):

```
stock.move 142 | stock.move.line 209 | stock.picking 27 | stock.quant 169 | stock.lot 126
stock.lot.cost.line 53 | lumber.shipment.cost.line 0 | lumber.export.shipment 14
lumber.container 15 | lumber.shipment.line 5 | shipping.vessel 6 | shipping.voyage 1
madenat.audit.log 265 | madenat.sv.operation 1 | madenat.sv.imputation 1
lumber.billing.consolidation 0 | account.move 1 | account.payment 0
```

- **Registros protegidos** verificados antes (histórica, UAT Rolleo, UAT Borrador Seguro, UAT B-01 previa) y confirmados sin cambio tras la UAT (`PROT_ALL_UNCHANGED = True`).

---

## 3. Datos UAT creados (prefijo `UAT-R1-20261004-`)

| Registro | ID | Nombre / valor |
|---|---|---|
| Motonave | 747 | `UAT-R1-20261004-VESSEL` |
| Embarque | 1885 | `UAT-R1-20261004-SHIP` (`confirmed`→`in_transit`) |
| Contenedor | 1888 | `UAT-R1-20261004-CONT-PENDING` (`sealed`→`rebajado`) |
| Lote | 16312 | `UAT-R1-20261004-LOT-01` (volumen 3.0 m³) |
| Producto | 5314 | `UAT-R1-20261004-PRODUCT` (storable, tracking lot, UoM m³) |
| Cliente | 14127 | `UAT-R1-20261004-CUSTOMER` |
| Línea de embarque | 2208 | `lumber.shipment.line` (container 1888 / lot 16312) |
| Picking OUT | 7238 | `WH/OUT/02347` (`done`, internal→Clientes) |
| Movimiento | 13973 | `stock.move` (`done`) |
| Línea de movimiento | 12417 | `stock.move.line` (lot 16312, qty 3.0) |

> **Decisión de alcance:** no se creó `UAT-R1-20261004-CONT-SECOND` (opcional). Un segundo contenedor pendiente habría bloqueado el cierre B-01 (pendiente residual) sin aportar valor al objetivo. Se cumplió «crear sólo los registros imprescindibles».

---

## 4. B-01 open (evidencia `01`)

- Zarpe por wizard `lumber.shipment.zarpe.wizard.action_zarpar_con_excepcion()` (Gerencia uid 2), motivo:
  `Regularización UAT: rebaja pendiente por contingencia documental.`
- Resultado: `shipment.state = in_transit`; `b01_exception_state = open`; `b01_exception_reason` exacto; `opened_by_id = 2`; audit `b01_departure_exception` id 19942 (hash SHA-256 válido); audit `deviation` de compatibilidad id 19941.
- Contenedor 1888 conserva `sealed`; stock interno del lote = 3.0 m³ sin cambio; Clientes = 0; sin picking de rebaja; sin movimiento de stock; sin cambios financieros/SV (delta audit +2).
- Chatter «Zarpe con excepción B-01» presente.

---

## 5. Cierre bloqueado con pendiente (evidencia `02`)

- `shipment.action_resolve_b01_exception()` como Gerencia → **UserError**: *«…quedan Contenedores pendientes de rebaja física (UAT-R1-20261004-CONT-PENDING). Regularícelos mediante la rebaja extemporánea R1.»*
- Post-intento: B-01 sigue `open`; `in_transit`; 0 audits `b01_resolution`; sin chatter de cierre; delta de todas las tablas = 0.

---

## 6. Permisos y composición congelada (evidencia `03`)

| Intento | Actor | Resultado |
|---|---|---|
| Abrir wizard R1 | uid 8 / uid 6 | **AccessError** «…requiere el rol de Gerencia.» |
| Crear/ejecutar wizard R1 | uid 8 / uid 6 | **AccessError** (ACL de `lumber.b01.regularization.wizard`) |
| Cerrar B-01 | uid 8 / uid 6 | **AccessError** «…requiere el rol de Gerencia.» |
| `write({'container_ids': [(3, cont)]})` | Gerencia | **UserError** (congelado in_transit/B-01) |
| `write({'container_ids': [(4, cont)]})` | Gerencia | **UserError** (congelado) |
| Igual con contexto `allow_b01_regularization/b01_internal` | Gerencia | **UserError** (sin bypass por contexto) |
| `container.write({'shipment_id': otro})` | Gerencia | **UserError** (guard de reasignación) |
| Igual con contexto `b01_regularization=True` | Gerencia | **UserError** |

- Verificación final: B-01 sigue `open`; composición intacta (solo 1888); `container.shipment_id` sin cambio; embarque destino 1869 intacto; sin auditoría/chatter/stock/finanzas.

---

## 7. Rebaja extemporánea física R1 (evidencia `04`)

- Wizard `lumber.b01.regularization.wizard` abierto desde el Embarque B-01 `open` (sólo Gerencia); selección exclusiva `CONT-PENDING`.
- Motivos (≥ 20 caracteres):
  `regularization_reason`: «Rebaja física extemporánea UAT tras zarpe B-01 documentado.»
  `approval_reason`: «Gerencia aprueba regularización física extemporánea UAT.»
- Resultado (Gerencia uid 2):
  - **Embarque:** permanece `in_transit`; B-01 permanece `open`; `actual_departure` sin cambio (no retrofechado).
  - **Contenedor 1888:** `sealed` → `rebajado`; `state_before_rebaja = 'sealed'`; `shipment_id` sin cambio.
  - **Lote 16312:** misma identidad; `volume_purchase_m3 = vol_shipment_m3 = 3.0` preservados; quant interno 3.0 → 0.0; quant Clientes 0.0 → 3.0 (simétrico).
  - **Rebaja física:** picking OUT **7238 `WH/OUT/02347` `done`** (origen interno → Clientes); `stock.move` 13973 y `stock.move.line` 12417 con `lot_id = 16312`; `picking.date_done (17:14:53) ≥ actual_departure (17:12:37)`.
  - **Línea 2208:** `rebaja_state='rebajado'`; `rebaja_picking_id=7238`; `rebaja_qty_m3=3.0`; `rebaja_date`/`rebaja_user_id=2` presentes.
  - **Auditoría:** audit normal `rebaja` id 19943 (hash válido) + **exactamente un** `b01_regularization` id 19944 (hash válido). Snapshot: `subtype='late_rebaja'`, `approver.role='gerencia'`, `original_b01_audit_id=19942`, `state_before='sealed'`, `state_after='rebajado'`, `rebaja_picking_id=7238`, `lot_id=16312`, `invariants.departure_not_backdated=true`, `invariants.physical_stock_moved_by_rebaja=true`.
  - **Chatter:** Embarque y Contenedor registran la regularización.
- **Invariantes:** sin embarque/contenedor/lote extra; sin cambios en costos/finanzas/SV; `actual_departure` sin cambio.


---

## 8. Cierre B-01 `resolved` (evidencia `05`)

- `shipment.action_resolve_b01_exception()` como Gerencia → **OK**.
- Resultado: `state` sigue `in_transit`; `b01_exception_state = resolved`; `resolved_at`/`resolved_by_id=2`/`resolution_audit_id` seteados; **se conservan** `b01_exception_reason`, `opened_at` (17:12:37), `opened_by_id=2` y audit original 19942; `actual_departure` sin cambio.
- **Exactamente un** audit `b01_resolution` id 19945 (hash SHA-256 válido). Snapshot: `b01_before='open'`, `b01_after='resolved'`, `original_b01_audit_id=19942`, `regularization_audit_ids=[19944]`, `gates.delivery_eligible_after_resolution=true`.
- Chatter de cierre «Excepción B-01 cerrada (resolved)» presente. Delta adicional = solo audit +1; sin cambios de stock/picking/lote/SV/costos/facturas/pagos.
- **Reintentos bloqueados (todos UserError, sin nueva auditoría):**
  - `action_resolve_b01_exception()` → «…ya tiene la excepción B-01 regularizada (resolved).»
  - `write({'b01_exception_state': 'resolved'})` → «…sólo puede ejecutarse mediante la acción autorizada «Cerrar B-01».»
  - `with_context(b01_resolve=True).write(...)` → **mismo bloqueo** (contexto no falsificable).
  - nueva R1 (`lumber.b01.regularization.wizard.action_regularize_rebaja`) → «…exige un Embarque En Tránsito con excepción B-01 ABIERTA.»
  - nuevo zarpe (`_set_in_transit` / `action_set_in_transit`) → «Sólo se puede zarpar un Embarque Confirmado (estado actual: Embarcado).»

---

## 9. Gate de Entrega sin ejecutar entrega (evidencia `06`)

- **Antes (B-01 `open`):** documentado en `01`/`02` → `_b01_blocks_delivery() = True`.
- **Después (`resolved`):** `_b01_blocks_delivery() = False`; sin pendientes físicos; `cost_distribution_state='pending'`; consolidaciones = 0.
- **NO se invocó `action_deliver()`** (completaría la Entrega, fuera de alcance). Solo verificación de elegibilidad por guard.
- Verificación: `shipment.state` sigue `in_transit`; sin chatter «Embarque entregado»; sin movimiento, picking, auditoría ni documentación financiera (delta = 0).
- **Limitación documentada:** el único modo de comprobar el gate completo sería `action_deliver()`, que materializa la Entrega; por eso se verifica exclusivamente el guard `_b01_blocks_delivery()` y se deja la Entrega real fuera del alcance.

---

## 10. Auditoría / hash / chatter

| Audit | Tipo | ID | batch | actor | hash SHA-256 |
|---|---|---|---|---|---|
| Desviación compatibilidad | `deviation` | 19941 | 1885 | 2 | válido |
| Apertura B-01 | `b01_departure_exception` | 19942 | 1885 | 2 | válido |
| Rebaja normal | `rebaja` | 19943 | 2208 (línea) | 2 | válido |
| Regularización R1 | `b01_regularization` | 19944 | 1885 | 2 | válido |
| Cierre B-01 | `b01_resolution` | 19945 | 1885 | 2 | válido |

- Total de auditorías B-01 del embarque 1885: 1 apertura + 1 regularización + 1 cierre (más 1 `deviation`). Reintentos no generaron auditoría adicional.
- **Chatter:** Embarque (B-01 open, R1, cierre) y Contenedor (R1) con mensajes registrados.
- Todos los hashes verificados `hash(audit_snapshot) == audit_hash`.

---

## 11. Inventario / lote / volumen / costos / finanzas / SV

**Delta global (final − BASE0) vs esperado:**

```
                             real   esperado
stock.move                     1        1
stock.move.line                1        1
stock.picking                  1        1
stock.quant                    2        2
stock.lot                      1        1
lumber.shipment.line           1        1
lumber.export.shipment         1        1
lumber.container               1        1
shipping.vessel                1        1
madenat.audit.log              5        5
stock.lot.cost.line            0        0
lumber.shipment.cost.line      0        0
madenat.sv.operation           0        0
madenat.sv.imputation          0        0
lumber.billing.consolidation   0        0
account.move                   0        0
account.payment                0        0
```

- **Lote 16312:** identidad y volúmenes preservados; quant interno 3.0 → 0.0; quant Clientes 0.0 → 3.0 (diferencias simétricas y cuantificadas).
- **Sin R3/SV:** `madenat.sv.operation`/`madenat.sv.imputation` sin cambio.
- **Sin costos/facturas/pagos/consolidación** (todos delta 0).


---

## 12. Integridad histórica y UAT anteriores

- **PROT_ALL_UNCHANGED = True**: sin cambio en histórica (1528/1537, contenedores 1500/1509, pickings 7062/7065, líneas 1880/1881, lotes 15970/15971, SV 5822 / Imp. 492), UAT Rolleo (vessels 619/620, voyage 565, shipments 1644–1646, containers 1629–1631, audits 19699–19704), UAT Borrador Seguro (shipments 1704–1707, containers 1678–1680, audit 19742) y UAT B-01 previa (vessel 746, shipments 1867/1868/1869, containers 1868–1871, audit 19890).
- **Estado B-01 global post-UAT:** única `open` = UAT previa **Shipment 1868** (sin cambio); `resolved` = **Shipment 1885** (nuevo, esta UAT). No quedó ninguna B-01 `resolved` no explicada.
- **Git:** HEAD `34c81272…`, rama `feat/guia-correccion-documental-preservada-20261002` y working tree (31 entradas) idénticos antes y después. Sin commit/push/reset/checkout/rebase/stash.
- **Código/config/ACL/manifest/vistas/tests/docs:** sin modificar.

---

## 13. Evidencia persistida

Directorio `/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_R1_20261004/`:

```
00_precheck_baseline.txt                  Precheck + línea base + protegidos + estado B-01
01_uat_r1_b01_open.txt                    Fixtures + zarpe B-01 (open)
02_uat_r1_close_blocked.txt               Cierre bloqueado por pendiente
03_uat_r1_permissions_composition.txt     Permisos (uid 8/6) + composición congelada
04_uat_r1_late_rebaja.txt                 R1 rebaja física real (picking/lote/quant/auditoría)
05_uat_r1_resolved.txt                    Cierre resolved + reintentos bloqueados
06_uat_r1_delivery_gate.txt               Gate de entrega (sin ejecutar entrega)
07_final_validation.txt                   Validación final vs línea base + protegidos
UAT-R1-20261004_RESULTADO.md              Este informe
scripts/                                  Runners reproducibles (odoo shell --no-http)
```

Cada evidencia incluye fecha/hora, usuario, IDs UAT, estado antes/después, errores esperados, delta de inventario, auditorías/hashes/chatter, estado B-01 y comprobación de registros protegidos.

---

## 14. Riesgos residuales

- **R2 (retorno total/parcial):** no probado. Falta UAT de `action_reverse_rebaja` / `_reverse_rebaja_container` / `_reverse_rebaja_picking` / `stock.return.picking` y su interacción B-01.
- **R3 (imputación SV):** no probado. Sin cobertura de `madenat.sv.operation`/`sv_reverse_allocation` durante/después de B-01.
- **Costeo / Billing / Pagos:** no probados. `cost_distribution_state`, `account.move`, `account.payment` y `lumber.billing.consolidation` quedaron en delta 0; falta UAT de sus gates con B-01 `resolved`.
- **Entrega / Cierre real:** no ejecutados. El gate se validó por guard; `action_deliver()` con todos los prerrequisitos sigue sin UAT end-to-end.
- **Segregación de funciones:** el ejecutor Gerencia fue uid 2 (Administrador con `base.group_system`). No existe usuario Gerencia no-administrador; la segregación real Gerencia/Administración no pudo aislarse (requiere definir una Gerencia no-Administrador). Bloqueo de Operaciones (uid 8) e interno (uid 6) sí quedó cubierto.

---

## 15. Dictamen

**A. `UAT R1 Y CIERRE B-01 APROBADA — APTO PARA DISEÑAR R2/R3 Y ENTREGA`**

Se validó, de extremo a extremo y con rebaja física real, el ciclo B-01 `open → R1 → pendientes=0 → resolved`:
- B-01 abre en zarpe documental sin mover inventario y conserva el estado físico del contenedor (apertura).
- El cierre se bloquea con pendiente residual (UserError, sin efectos).
- Permisos: sólo Gerencia ejecuta R1/cierre (Operaciones e interno rechazados); composición de contenedores congelada sin bypass por contexto.
- R1 ejecuta la rebaja extemporánea real (picking OUT `done`, interno→Clientes, lote/volumen preservados, quant simétrico), sin retrofechar, sin cerrar la excepción, con auditoría firmada.
- Cierre `resolved` idempotente por bloqueo, con conservación de la B-01 original y una única auditoría de cierre.
- Inventario/costos/finanzas/SV dentro del delta esperado; integridad histórica y de UAT previas intacta; git sin cambios.

> **Fin del informe.** No se ejecutó R2, R3 ni Entrega. Sin cambios de código. Sin commit/push.

