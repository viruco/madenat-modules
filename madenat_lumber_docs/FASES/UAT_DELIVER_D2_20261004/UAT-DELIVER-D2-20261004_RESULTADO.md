# MADENAT — Resultado UAT Entrega Segura D2

```
Documento : UAT Entrega Segura D2 (Sub-bloque 5) — Entrega y Cierre seguro de Embarque (Política D2)
Fase      : D — Validación operativa (UAT aislada y controlada)
Entorno   : madenat_test (odoo18_app Up · odoo18_db healthy)
Fecha     : 2026-10-04 (precheck · runner · verificación en una sola ejecución)
Repo      : /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons
Rama/HEAD : feat/guia-correccion-documental-preservada-20261002 · 34c81272bb07d48db98d73a7734c81a2a8e384fa
Alcance   : SÓLO Entrega logística D2. SIN retorno físico, SIN SV/imputación, SIN costeo,
            SIN facturación, SIN pagos, SIN consolidación, SIN Rolleo, SIN Borrador, SIN B-01 nuevo.
Dictamen  : A. UAT ENTREGA SEGURA D2 APROBADA — APTO PARA CONTINUAR CON EL CIERRE DEL SUB-BLOQUE 5
```

---

## 1. Fecha, entorno y usuarios

| Item | Valor |
|---|---|
| Base de datos | `madenat_test` |
| Contenedores | `odoo18_app` Up · `odoo18_db` healthy (postgres:15) |
| Método | ORM vía `odoo shell -d madenat_test --no-http` (stdin). SIN `sudo()` funcional, SIN SQL de escritura, SIN `update/install`, SIN `uid 1` en ninguna acción de contrato. |
| Working tree | 34 entradas (`git status --porcelain`), idéntico antes y después; HEAD/rama sin cambios; `git diff --check` CLEAN |

**Usuarios (solo existentes; no se crearon usuarios):**

| Rol | uid | login | JEF | GER | OPE | SYS | Nota |
|---|---|---|---|---|---|---|---|
| Gerencia (aprobador waiver) + Jefatura | 2 | mauricio.seo@gmail.com | Sí | Sí | Sí | Sí | Único con Gerencia; es administrador (`base.group_system`). `env.su=False`. NO es `uid 1`. |
| Jefatura + Operaciones (entregador autorizado) | 8 | cristhian.elguetag@gmail.com | Sí | No | Sí | No | **No administrador**. Entrega la UAT-DLV-1/DLV-5 y no puede aprobar waiver. |
| Interno común (no autorizado) | 6 | leonardo@pinelli.com.mx | No | No | No | No | Sin roles MADENAT. |
| Superusuario | 1 | OdooBot | — | — | — | — | **NO usado** para ninguna acción de contrato. |

---

## 2. Precheck y línea base (`00_precheck_baseline.txt`)

- **Implementación D2 confirmada (solo lectura):** campos `delivery_waiver_state/_reason/_approved_at/_approved_by_id/_audit_id` presentes; acciones `action_deliver`, `action_confirm`, `action_approve_delivery_waiver` y helpers `_assert_can_deliver`, `_delivery_document_status` presentes; `action_type` incluye `shipment_delivery` y `delivery_waiver`.
- **Estado de partida:** `delivered=0` · `waiver_rows=0` · auditorías `shipment_delivery`/`delivery_waiver`=0 · B-01 `open`=1 (previa, ajena a esta UAT) · documentos `missing`=96.
- **Checklist documental:** 6 documentos, 5 obligatorios.

**Línea base (antes) → después (`03_final_validation.txt`):**

| Modelo | Antes | Después | Δ |
|---|---|---|---|
| stock.move | 145 | 145 | 0 |
| stock.move.line | 212 | 212 | 0 |
| stock.picking | 30 | 30 | 0 |
| stock.quant | 173 | 173 | 0 |
| stock.lot | 128 | 132 | **+4** (fixtures de rebaja) |
| stock.lot.cost.line | 53 | 53 | 0 |
| lumber.shipment.cost.line | 0 | 0 | 0 |
| lumber.export.shipment | 16 | 21 | **+5** (fixtures UAT) |
| lumber.container | 17 | 22 | **+5** (fixtures UAT) |
| lumber.shipment.line | 7 | 11 | **+4** (fixtures de rebaja) |
| shipping.vessel | 8 | 9 | **+1** (fixture UAT) |
| shipping.voyage | 2 | 2 | 0 |
| madenat.audit.log | 273 | 278 | **+5** (2 zarpe B-01 + 3 Entrega/waiver) |
| madenat.sv.operation | 1 | 1 | 0 |
| madenat.sv.imputation | 1 | 1 | 0 |
| lumber.billing.consolidation | 0 | 0 | 0 |
| account.move | 1 | 1 | 0 |
| account.payment | 0 | 0 | 0 |

> El único crecimiento fuera de los fixtures UAT son las **5 auditorías append-only** de la propia UAT (2 por el zarpe B-01 del fixture, 1 por la Entrega limpia, 1 por el waiver y 1 por la Entrega con waiver). **Cero** movimiento de inventario, costos, facturas o pagos.

---

## 3. Datos UAT nuevos (aislados, `FIXTURE_IDS`)

Prefijo `UAT-DLV-D2-20261004-`. Todos creados **sin** tocar stock real.

| Objeto | ID | Nombre | Estado inicial |
|---|---|---|---|
| Cliente | 14224 | UAT-DLV-D2-20261004-CUSTOMER | — |
| Producto | 5336 | UAT-DLV-D2-20261004-LUMBER | — |
| Motonave | 926 | UAT-DLV-D2-20261004-VESSEL | — |
| Embarque CLEAN | 2189 | UAT-DLV-D2-20261004-CLEAN | in_transit · docs `approved` |
| Contenedor | 2179 | …CONT-CLEAN | shipped (rebaja `active`) |
| Embarque DOCS | 2190 | UAT-DLV-D2-20261004-DOCS | in_transit · docs `missing` |
| Contenedor | 2180 | …CONT-DOCS | shipped (rebaja `active`) |
| Embarque B01 | 2191 | UAT-DLV-D2-20261004-B01 | in_transit · B-01 `open` |
| Contenedor rebajado | 2181 | …CONT-B01-REB | shipped (rebaja `active`) |
| Contenedor pendiente | 2182 | …CONT-B01-PEND | loaded (rebaja `none`) |
| Embarque WRITE | 2192 | UAT-DLV-D2-20261004-WRITE | in_transit · docs `missing` |
| Contenedor | 2183 | …CONT-WRITE | shipped (rebaja `active`) |
| Embarque CREATE-OK | 2193 | UAT-DLV-D2-20261004-CREATE-OK | draft (creación permitida) |

---

## 4. Escenarios ejecutados (`01_uat_deliver_d2.txt`)

| ID | Caso | Acción | Resultado observado | Estado |
|---|---|---|---|---|
| **UAT-DLV-1** | `in_transit` limpio + docs `approved` | Jefatura (uid 8) `action_deliver()` | **`delivered`**; 1 auditoría `shipment_delivery` SHA-256 + chatter; Δaudit=1; Δfísico/financiero=0 | **PASS** |
| **UAT-DLV-2** | `in_transit` + **B-01 open** | Jefatura (uid 8) `action_deliver()` | **`UserError`** (excepción B-01 abierta); sigue `in_transit`, B-01 `open`, sin auditoría/chatter | **PASS** |
| **UAT-DLV-3** | `in_transit` + docs `missing` sin waiver | Jefatura (uid 8) `action_deliver()` | **`UserError`** (documentación no aprobada); sigue `in_transit`, sin auditoría | **PASS** |
| **UAT-DLV-5** | waiver de **Gerencia** habilita la Entrega | Gerencia (uid 2) `action_approve_delivery_waiver(reason)` → Jefatura (uid 8) `action_deliver()` | Waiver **`approved`** + auditoría `delivery_waiver` SHA-256 + chatter; luego **`delivered`** + auditoría `shipment_delivery`; Δfísico/financiero=0 | **PASS** |
| **UAT-DLV-6** | permisos / segregación | uid 6 `action_deliver()`; uid 8 `action_approve_delivery_waiver()` | **`AccessError`** en ambos; estado y waiver sin cambios | **PASS** |
| **UAT-DLV-7** | write directo (puerta lateral P0-1) | uid 8 `write({'state':'delivered'})`, con contexto falso, `write({'state':'confirmed'})` y `write` de campos waiver | **`UserError`** en los 4 casos (el contexto `allow_delivery/allow_create_terminal` NO elude); estado/waiver sin cambios; Δaudit=0 | **PASS** |
| **UAT-DLV-8** | puerta lateral `create()` (micro-parche C1) | uid 6/no-su `create` con `state=confirmed/in_transit/delivered/cancelled`, campos waiver y B-01, y con contexto falso | **`UserError`** en los 7 casos; **no** se creó ningún Embarque ni auditoría; `create` en `draft` por Operaciones/Jefatura **permitido** (2193) | **PASS** |
| **UAT-DLV-9** | reintento sobre `delivered` | Jefatura (uid 8) `action_deliver()` | **`UserError`**; sigue `delivered`; sin auditoría ni chatter adicional | **PASS** |

**Fixtures verificados (`FIXTURE_STATE`):** `_delivery_document_status` = `approved` en CLEAN (5/5 requeridos) y `missing` en DOCS/B01/WRITE; clasificación de rebaja `active` para contenedores rebajados y `none` para el pendiente; el Embarque B-01 quedó `open` con motivo y auditoría firmada.

---

## 5. Auditoría append-only, hash y chatter

- **`shipment_delivery`** (Entrega limpia, batch 2189, actor uid 8, audit 20344) y **`delivery_waiver`** (batch 2190, actor uid 2, audit 20345) + **`shipment_delivery`** (batch 2190, actor uid 8, audit 20346): `hash_ok = True` (SHA-256 del `audit_snapshot`).
- El snapshot de Entrega (D1) registra `physical_checks` (`no_b01_open`, `no_pending`, `no_inconsistency`, `return_chain_consistent` = true), clasificación de contenedores y `financial_status` (cost_distribution pending, 0 invoices/payments/consolidations) — la Entrega es un **hito logístico** que NO exige cierre financiero (Política D2).
- Chatter: 1 mensaje «Embarque entregado» por Entrega y 1 «Waiver de Entrega aprobado» por waiver. Los reintentos y bloqueos **no** generan chatter.
- Auditoría del fixture B-01 (zarpe con excepción): 2 eventos (`deviation` + `b01_departure_exception`) creados por el **setup** del escenario DLV-2 (no por la Entrega).

---

## 6. Cero movimiento físico / financiero

Δ = 0 en `stock.move`, `stock.move.line`, `stock.picking`, `stock.quant`, `stock.lot.cost.line`, `lumber.shipment.cost.line`, `account.move`, `account.payment`, `lumber.billing.consolidation`, `madenat.sv.operation`, `madenat.sv.imputation`. Las acciones de Entrega sólo escribieron `state` (+chatter) y la auditoría.

---

## 7. Integridad de UAT histórica protegida

`PROT_UNCHANGED = true` para todos los registros protegidos (histórica logística 1537/1509/7065/…, SV 1528/1500/…, Rolleo 619/620/1644-1646/1629-1631, Borrador 1704-1707/1678-1680, R1 1885, R2 2128, B-01 1867/1868). Ningún registro protegido fue origen, destino, fixture ni evidencia.

---

## 8. Evidencia persistida (`UAT_DELIVER_D2_20261004/`)

```
00_precheck_baseline.txt     (PRE) identidad, implementación D2, usuarios, checklist, línea base
01_uat_deliver_d2.txt        (UAT) trazas de todos los escenarios DLV-1..9 + FINAL
02_raw_run.txt               salida cruda completa del Odoo shell
03_final_validation.txt      conteos finales, delta global, protegidos, hash
_precheck_uat_deliver_d2.py  script de precheck READ-ONLY
_uat_deliver_d2.py(.txt)     runner de la UAT
_cleanup_failed_run.py / _cleanup.log  limpieza de un fixture de un intento previo abortado
```

---

## 9. Riesgos residuales (para el cierre del Sub-bloque 5)

1. **Gate de rebaja física (`pendientes`):** en la BD viva la condición «contenedor pendiente» sólo coexiste con **B-01 open** (el zarpe con pendientes exige B-01). En DLV-2 se observó la clasificación `pendientes=[CONT-B01-PEND]` y el bloqueo; la aislación del gate `pendientes` sin B-01 se cubre en la suite unitaria (`T-DLV-4`). No se forzó `in_transit` por superusuario para preservar la disciplina.
2. **Segregación del aprobador de waiver:** el único usuario con Gerencia es `uid 2` (además `base.group_system`). El camino **permitido** de Jefatura se validó con un usuario **no-administrador** (`uid 8`); el camino de **Gerencia** (waiver) no pudo validarse con un Gerencia no-administrador (no existe). Se recomienda crear una cuenta de Gerencia dedicada para futuras UAT.
3. **`document_status='approved'` = evidencia cargada** (`attached`/`verified`); no hay aprobación humana firmada por documento — el waiver de Gerencia cubre la ausencia (Política D2).
4. **Waiver sin wizard dedicado:** el motivo se aporta por la acción autorizada `action_approve_delivery_waiver(reason=...)`; un `wizard/` dedicado queda como mejora (no autorizado en este bloque).

---

## 10. Dictamen

> **A. `UAT ENTREGA SEGURA D2 APROBADA — APTO PARA CONTINUAR CON EL CIERRE DEL SUB-BLOQUE 5`.**

Fundamento:
- **DLV-1 (PASS):** `in_transit` limpio → `delivered` por Jefatura, con auditoría `shipment_delivery` SHA-256 y chatter; **cero** movimiento físico/financiero.
- **DLV-2/DLV-3 (PASS):** B-01 `open` y documentación `missing` **bloquean** la Entrega (UserError) sin efectos.
- **DLV-5 (PASS):** el waiver de **Gerencia** (auditado) habilita la Entrega cuando falta documentación.
- **DLV-6 (PASS):** segregación efectiva — usuario sin rol bloqueado (`AccessError`); Jefatura no puede aprobar waiver.
- **DLV-7/DLV-8 (PASS):** P0-1 (write directo) y puerta lateral `create()` cerradas; `with_context(...)` no elude; creación en `draft` permitida.
- **DLV-9 (PASS):** la Entrega es idempotente en bloqueo.
- Integridad: historial protegido intacto; sin cambios en stock/costos/finanzas/SV; sin cambios de código/configuración/ACL; Git/HEAD sin cambios; sin commit/push.

---

**Fin del informe. No se ejecutó retorno físico ni SV. No se avanzó a Costeo/Facturación/Pagos/consolidación. No se modificó código. Sin commit ni push.**
