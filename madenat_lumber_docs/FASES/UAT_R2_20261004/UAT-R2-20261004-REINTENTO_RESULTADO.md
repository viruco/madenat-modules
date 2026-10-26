# MADENAT — Resultado UAT R2 Total con Cristhian

- **Sub-bloque:** 4B — R2 «Retorno Físico Total robusto». **Fase D — Validación operativa.**
- **Ejecutor de negocio:** **Cristhian Elgueta (uid 8)**, sesión **`env(user=8, su=False)`**.
- **Rol efectivo:** Operaciones + Jefatura de Operaciones. **Sin** Gerencia, Contabilidad,
  `account_manager`, `account_invoice`, `base.group_system` ni `group_madenat_admin`.
- **Método:** `odoo shell` (proceso aparte). **Sin uid 1, sin uid 2 como ejecutor, sin
  `sudo()` propio, sin SQL de escritura, sin cambios de código/XML/CSV/ACL/manifest/tests,
  sin update/install, sin git mutante.** Toda la UAT (fixture, rebaja, reversa, idempotencia,
  intentos de permiso) se ejecutó bajo `env8 = env(user=8, su=False)`. Las auditorías internas
  del módulo (`madenat.audit.log`) usan el `sudo()` **propio del código**, no del ejecutor.
- **Fecha:** 2026-10-04.

---

## 1. Entorno, usuario y rol efectivo
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree / `diff --check` | **33 = 24 M + 9 ??** / **CLEAN** (idéntico antes y después) |
| Runtime / DB | `odoo18_app` Up · `odoo18_db` healthy · HTTP 127.0.0.1:8069 · `madenat_test` |
| Ejecutor | `uid=8` · `su=False` · `_is_internal()=True` · `uid != 1` |
| Operaciones / Jefatura | **True / True** |
| Gerencia / Contabilidad / account_manager / account_invoice | **False / False / False / False** |
| `base.group_system` / `group_madenat_admin` | **False / False** |

Evidencia: `14_precheck_r2_retry.txt`.

## 2. Precheck y línea base (`14_precheck_r2_retry.txt`)
- **No había UAT-R2 previa:** contenedores/embarques/lotes `UAT-R2-20261004-*` = **0**.
- **`rebaja_return_total` = 0 · `rebaja_reverse` = 0** · `rebaja` = 4.
- **B-01 = 13 none / 1 open / 1 resolved** (sin cambios, salvo el nuevo embarque `none`).
- **Conteos baseline** (uid 8): move 143 · mline 210 · picking 28 · quant 171 · lot 127 ·
  lot.cost.line 53 · shipment.cost.line 0 · shipment 15 · container 16 · shipment.line 6 ·
  vessel 7 · voyage 1 · audit 270 · sv.operation 1 · sv.imputation 1 · account.move 1 ·
  account.payment 0 · billing.consolidation 0 → **todos legibles como uid 8**.
- **Protegidos intactos** (histórica 1537/1509/7065/7062/1880/1881/1528/1500/SV5822/imp492,
  Rolleo, Borrador, B-01, R1).
- **Sin criterio de detención.** Se procede.

## 3. Datos UAT creados (prefijo `UAT-R2-20261004-`)
Ejecutados y persistidos por **uid 8** (`env8.cr.commit()`, `15_uat_r2_rebaja_source.txt`):

| Registro | ID | Nombre / estado |
|---|---:|---|
| Motonave | 921 | `UAT-R2-20261004-VESSEL` |
| Viaje | 813 | `UAT-R2-20261004-VOY-01` (Coronel→Shanghai) |
| Embarque | 2128 | `UAT-R2-20261004-SHIP` (draft / B-01 none / cost pending) |
| Contenedor | 2129 | `UAT-R2-20261004-CONT` (loaded) |
| Línea | 2415 | `lumber.shipment.line` (rebaja_state pending→…) |
| Lote | 16525 | `UAT-R2-20261004-LOT-01` (no volume/SV, flow_type vacío) |
| Partner / Producto | 14207 / 5331 | `UAT-R2-20261004-PARTNER` / `-PRODUCT` (storable, tracking lot) |
| Quant interno | — | 3.0 m³ en la ubicación interna de origen |

> **Nota de alcance:** además de lo mínimo exigido se creó **1 viaje, 1 partner y 1 producto**
> — registros de **soporte obligatorios** para un lote/quant y un embarque válidos. **No** se
> creó ninguna guía, SV, costo, factura, pago ni consolidación.

## 4. Escenario UAT-R2-1 — Rebaja UAT fuente (`15_uat_r2_rebaja_source.txt`)
Ejecutado por uid 8 con `container.action_rebajar()`:

| Verificación | Resultado |
|---|---|
| `container.state = rebajado` | **PASS** |
| `line.rebaja_state = rebajado` | **PASS** |
| OUT `WH/OUT/02466` `state = done` | **PASS** |
| OUT internal → Customers | **PASS** |
| OUT move/mline usan el lote UAT (move 14134 / mline 12574) | **PASS** |
| quant interno 3.0 → **0.0** | **PASS** |
| quant Customers 0.0 → **3.0** | **PASS** |
| audit `rebaja` presente, **SHA-256 válido** (id 20320, hash 64) | **PASS** |
| Embarque sin cambio (draft / none / pending) | **PASS** |
| Sin costo/factura/pago/SV | **PASS** |

`DELTA` exacto: +1 move, +1 mline, +1 picking, +2 quants, +1 lot, +1 shipment, +1 container,
+1 shipment.line, +1 vessel, +1 voyage, +1 audit.

## 5. Escenario UAT-R2-2 — Retorno físico total (`16_uat_r2_return_total.txt`)
Ejecutado por uid 8 con `container.action_reverse_rebaja()` → `True` (R2 **normal**, sin gates
de Gerencia):

| Verificación | Resultado |
|---|---|
| Return picking **`EMB-04080`** `state = done` | **PASS** |
| Retorno Customers → **misma** ubicación interna de salida | **PASS** |
| Mismo lote (mline 12575 → lote 16525) | **PASS** |
| Cada return move con `origin_returned_move_id` = move OUT (**14135 → 14134**) | **PASS** |
| Producto / UoM / cantidad idénticos | **PASS** |
| `line.rebaja_state = reversed` | **PASS** |
| `container.state = state_before_rebaja` (**loaded**) | **PASS** |
| quant interno vuelve a **3.0** | **PASS** |
| quant Customers vuelve a **0.0** | **PASS** |
| audit `rebaja_return_total` (id 20322) **SHA-256 válido**, y `rebaja_reverse` (id 20321) **SHA-256 válido** | **PASS** |
| Snapshot incluye OUT/IN/move origin/return move/lote/checks | **PASS** |
| Chatter de retorno/reversa (container msgs = 4) | **PASS** |
| Embarque sin cambio (draft / none / pending) | **PASS** |
| Sin cambios en costos/facturas/pagos/consolidación/SV/imputación/Entrega/B-01 | **PASS** |

`DELTA` exacto: **+1 move, +1 mline, +1 picking, +2 audits** (ningún quant nuevo: se reutilizan
los quants del caso).

## 6. Escenario UAT-R2-3 — Idempotencia (`17_uat_r2_idempotency.txt`)
Reintento de `action_reverse_rebaja()` por uid 8 sobre el contenedor ya revertido:

| Métrica | Antes | Después |
|---|---:|---:|
| pickings / moves / mlines / quants | 30 / 145 / 212 / 173 | **30 / 145 / 212 / 173** |
| returns de la OUT | 1 | **1** |
| audit rebaja / return_total / reverse | 5 / 1 / 1 | **5 / 1 / 1** |
| SV rebaja_reverse | 0 | **0** |
| quant interno | 3.0 | **3.0** |

**Resultado:** `True` — **no-op idempotente**: sin picking/move/mline/quant/auditoría/SV
adicionales; `container=loaded`, `line=reversed`. **PASS**.

## 7. Escenario UAT-R2-4 — Permisos (`18_uat_r2_permissions.txt`)
El guard `_rebaja_require_group(REBAJA_REVERSE_GROUPS)` es la **primera** sentencia de
`action_reverse_rebaja` y es **100 % de grupo** (no depende de estado ni escribe). Requerimiento:
`('…jefatura_operaciones', '…gerencia')` — **excluye Operaciones**.

| Usuario | Operaciones/Jef/Ger | Intento | Resultado |
|---|---|---|---|
| uid 6 Leonardo (interno) | F/F/F | `action_reverse_rebaja` | **BLOCKED AccessError** |
| uid 7 María Victoria (interno) | F/F/F | `action_reverse_rebaja` | **BLOCKED AccessError** |
| uid 9 Felipe (admin+auditoría) | F/F/F | `action_reverse_rebaja` | **BLOCKED AccessError** |

- **No se creó un segundo caso UAT:** el guard es de grupo y ocurre antes de cualquier lectura
  de estado/escritura, por lo que se demuestra sin una nueva rebaja física.
- **No existe usuario interno con SOLO Operaciones** (distinto de uid 2/8). Por diseño del
  guard, un Operaciones puro **tampoco** podría revertir (el requerimiento lo excluye).
- **Sin escrituras:** conteos pickings/moves/mlines/audit idénticos antes/después.
- **PASS.**

## 8. Escenario UAT-R2-5 — B-01 (no operativo) (`19_final_validation_r2.txt`)
- `UAT-R2-20261004-SHIP.b01_exception_state = **none**`; campos B-01 (motivo/auditoría) **vacíos**.
- B-01 global: **none = 14** (13 previos + el nuevo embarque) · **open = 1** · **resolved = 1**.
- No se creó ni ejecutó B-01 (open/resolved son de Gerencia, fuera de alcance). **PASS.**

## 9. Auditoría / hash / chatter
| Acción | Contenido |
|---|---|
| `rebaja` | id **20320**, `audit_hash` SHA-256 (64 hex) verificado vs `sha256(audit_snapshot)` |
| `rebaja_return_total` | id **20322**, SHA-256 (64 hex) verificado |
| `rebaja_reverse` | id **20321**, SHA-256 (64 hex) verificado |
| Chatter | `mail.message` en el contenedor = **4** (rebaja + retorno) |

Totales: `rebaja` = **5** (4 baseline + 1 UAT) · `rebaja_return_total` = **1** ·
`rebaja_reverse` = **1**.

## 10. Inventario, lote, ubicaciones y movimientos
- OUT `WH/OUT/02466` (done): internal → Customers, move **14134** / mline **12574** (lote UAT).
- IN `EMB-04080` (done): Customers → internal, move **14135** (`origin_returned_move_id=14134`) /
  mline **12575** (mismo lote).
- **Estado final del lote UAT:** quant interno = **3.0 m³** (= inicial), Customers = **0.0**,
  **sin saldo residual**.
- `container.state = loaded` (= `state_before_rebaja`); `line.rebaja_state = reversed`.
- `stock.move` 143→**145**; `stock.move.line` 210→**212**; `stock.picking` 28→**30**;
  `stock.quant` 171→**173**; `stock.lot` 127→**128**.

---

## 11. Integridad de UAT / histórica (`19_final_validation_r2.txt`)
**Sin cambios** en todo lo protegido:

| Bloque | Evidencia |
|---|---|
| Histórica | ship1537[in_transit/none] · cont1509[shipped] · pick7065/7062[done] · lines1880/1881[rebajado] · ship1528[draft] · cont1500[rebajado] · SV5822[rebaja] · imp492[IMP00946] |
| UAT Rolleo | vessels 619/620 · voyage 565 · ships 1644/1645/1646 · conts 1629/1630/1631 · audits 19699–19704 |
| UAT Borrador | ships 1704–1707 · conts 1678/1679/1680 · audit 19742 |
| UAT B-01 | vessel 746 · ships 1867/1868/1869 · conts 1868–1871 · audit 19890 |
| UAT R1 | vessel 747 · ship1885[in_transit/resolved] · cont1888[rebajado] · lot16312 · pick7238 · move13973 · audits 19941–19945 |

**Sin cambios:** `stock.lot.cost.line`=53 · `lumber.shipment.cost.line`=0 · `madenat.sv.operation`=1 ·
`madenat.sv.imputation`=1 · `account.move`=1 · `account.payment`=0 · `lumber.billing.consolidation`=0.
**Git:** rama/HEAD idénticos; working tree **33 = 24 M + 9 ??**; `diff --check` **CLEAN**.

## 12. Evidencia persistida
En `/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_R2_20261004/`:
`14_precheck_r2_retry.txt`, `15_uat_r2_rebaja_source.txt`, `16_uat_r2_return_total.txt`,
`17_uat_r2_idempotency.txt`, `18_uat_r2_permissions.txt`, `19_final_validation_r2.txt`,
este `UAT-R2-20261004-REINTENTO_RESULTADO.md`, y los runners
`_precheck_r2_retry.py`, `_uat_r2_1_rebaja.py`, `_uat_r2_2_return.py`, `_uat_r2_3_idem.py`,
`_uat_r2_4_perms.py`, `_uat_r2_5_final.py`.

## 13. Riesgos residuales
1. **Retorno parcial:** no probado en esta UAT (sólo retorno **total**, por mandato).
2. **R3 / imputación SV:** no probado. El lote UAT no es volume/SV; `madenat.sv.operation`=1 e
   `imputation`=1 sin cambios.
3. **Entrega/Cierre:** no probado (fuera de alcance).
4. **Costeo / Billing / Pagos:** no probados. `shipment.cost.line`=0, `account.move`=1,
   `account.payment`=0, `billing.consolidation`=0 sin cambios.
5. **Grupos huérfanos `#61/#62/#63/#64`:** Cristhian sigue siendo miembro (ACL financieras fuera
   del modelo canónico). No modificados; decisión pendiente.
6. **Auditoría sin usuario asignado:** `group_madenat_auditoria` con 0 usuarios.
7. **Definición futura de Gerencia:** decidir acoplamiento `Gerencia→Contabilidad→account_manager`.
8. **Regla de negocio pendiente:** el require de reversa excluye Operaciones; un Operaciones puro
   no puede revertir (confirmado por diseño del guard).

## 14. Dictamen

### **A. `UAT R2 TOTAL APROBADA — APTO PARA DISEÑAR R3 Y ENTREGA`**

- **Cristhian (uid 8, Operaciones + Jefatura, sin Gerencia ni finanzas)** completó el ciclo R2
  normal íntegro y de forma segura: rebaja (internal→Customers) → reversa total (Customers→internal,
  mismo lote, `origin_returned_move_id`) → quant restituido, con auditorías `rebaja` /
  `rebaja_return_total` / `rebaja_reverse` firmadas por SHA-256 y chatter.
- **Idempotencia** verificada (reintento = no-op).
- **Permisos** verificados (usuarios no autorizados bloqueados con `AccessError`).
- **B-01 none** confirmado; sin excepciones ni operaciones financieras.
- Integridad total: protegidos intactos, delta acotado a los registros UAT, Git sin cambios.

**Cambios netos autorizados (únicos):** `UAT-R2-20261004-*` (vessel/voyage/shipment/container/lot),
2 pickings (OUT+IN) con sus moves/move lines, 2 quants, 3 auditorías y chatter; + 1 partner y
1 producto de soporte.

*Se detiene aquí. No se avanza a R3, retorno parcial ni Entrega/Cierre. No se modifica código.
Sin commit/push. Fin del informe.*
