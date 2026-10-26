# MADENAT — Resultado UAT Costeo C2

```
Documento   : UAT-C2-20261004_RESULTADO
Feature     : Costeo y Valorización post-Entrega — Política C2 (Costeo provisional versionado)
Sub-bloque  : 6 (Costeo C2) — Fase D (Validación operativa)
Entorno     : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha       : 2026-10-04
Método      : READ-ONLY de precheck + decisión de DETENCIÓN (stop-criterion).
              NO se ejecutó UAT: no se crearon datos, no hay movimiento de stock.
Evidencia   : ./UAT_COSTING_C2_20261004/00..06*.txt
Dictamen    : B. UAT BLOQUEADA — INDICAR ESCENARIO, EVIDENCIA Y ACCIÓN.
```

> **Resultado en una línea:** el motor C2 está **instalado y actualizado en runtime**, pero la UAT
> **no puede ejecutarse** porque se **dispara el criterio de detención**: (1) **no existe usuario
> no-administrador en el rol que APLICA C2 (Contabilidad)** — el único miembro es la cuenta
> *Administrator* (uid 2, con `group_system`); y (2) **no hay Embarque `delivered` reutilizable** —
> los únicos `delivered` son **2189/2190 (UAT D2)**, prohibidos como target, y obtener uno nuevo por
> el flujo **D2** exige **rebaja física (movimiento de inventario)** no autorizado (o escritura
> directa de `state`, prohibida). Conforme al mandato ("si no existe usuario Costos/Contabilidad
> no-administrador … detenerse y solicitar decisión. No crear UAT."), **no se creó UAT**.

---

## 1. Fecha, entorno y roles

- **Fecha:** 2026-10-04. **Entorno:** `madenat_test`; `odoo18_app` Up; `odoo18_db` healthy
  (postgres:15); HTTP 200.
- **Método:** solo lectura (git, `docker ps`, `psql SELECT`, inspección de código). **Sin** crear
  datos, **sin** SQL de escritura, **sin** `-u`/`-i`, **sin** `sudo()` funcional.
- **Módulos instalados:** `madenat_lumber_core` 18.0.6.5.0 · `madenat_lumber_logistics` 18.0.1.6.0 ·
  `madenat_lumber_shipping_core` 18.0.1.0.0 · `madenat_lumber_costing` 18.0.1.0.0 ·
  `madenat_lumber_billing` 18.0.1.0.0 · `madenat_vendor_payment` 18.0.1.2.0.

**Roles (grupos MADENAT reales, `res_groups_users_rel`):**

| Grupo | ID | Usuarios |
|---|---:|---|
| Operaciones | 256 | uid 8 (Cristhian), uid 2 |
| **Costos** | 257 | uid 8 (Cristhian), uid 2 |
| **Contabilidad** | 258 | **uid 2 únicamente** |
| Gerencia | 259 | uid 2 |
| Jefatura de Operaciones | 261 | uid 8, uid 2 |
| cost_auditor | 69 | uid 8, uid 9, uid 2 |
| cost_auditor_plus | 260 | uid 8 |
| **Auditoría** | 298 | **sin usuarios** |

- **uid 2** `mauricio.seo@gmail.com` = *Administrator*, con `group_system` / *Settings* /
  *Technical Features* → **cuenta administrador**.
- **uid 8** `Cristhian Elgueta` = Operaciones/Jefatura **pero también `group_madenat_costos` (257)**.
- **uid 6/7** = sin grupos MADENAT operativos. **uid 9** = `cost_auditor`.

**Roles del motor C2 (contrato de código):** `C2_COSTING_GROUPS` = Costos ∪ Contabilidad
(preparar); `C2_APPLY_GROUPS` = **Contabilidad** (aplicar).

---

## 2. Precheck / línea base

### 2.1 Identidad y runtime
| Ítem | Valor |
|---|---|
| Repo | `custom_addons` (`/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`) |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree | **44 entradas (34 M + 10 ??)** — incluye **todo el código C2 sin commitear** |
| Runtime/HTTP/DB | `odoo18_app` Up · `odoo18_db` healthy · HTTP 200 · `madenat_test` |
| Costing/Core/Logistics | instalados (ver §1) |

### 2.2 C2 presente en runtime (no sólo en disco)
- `lumber.cost.distribution` tiene las columnas C2: `is_c2`, `version_number`, `basis`,
  `distribution_date`, `total_source_cost_usd`, `total_distributed_usd`, `residual_usd`,
  `shipment_id`, `applied_by_id`.
- Vista `lumber.cost.distribution.form.c2` (id **2905**) presente.
- Métodos cargados: `action_prepare_distribution`, `action_apply_distribution`, `_c2_gate_checks`,
  `_assert_can_distribute_costs_c2`; legado `action_distribute_costs` **clausurado** (lanza `UserError`).
- Acciones de auditoría aditivas presentes: `shipment_cost_distribution`,
  `shipment_cost_distribution_supersede`, `shipment_cost_distribution_cancel`.

### 2.3 Línea base (SELECT count, `madenat_test`)
| Modelo | Valor |
|---|---:|
| `lumber.export.shipment` | draft 8 · confirmed 3 · in_transit 8 · **delivered 2** |
| `lumber.export.shipment` `delivered` | **2189** `UAT-DLV-D2-…-CLEAN`, **2190** `UAT-DLV-D2-…-DOCS` (b01=none, `cost_distribution_state=pending`) |
| `cost_distribution_state='distributed'` | **0** |
| `lumber.shipment.cost.line` | **0** |
| `stock.lot.cost.line` (ledger) | 53 (0 con `shipment_id`) |
| `lumber.cost.distribution` | 2 → `CD-2026-0002` (draft, **is_c2=null**), `CD-DEV-0001` (applied, **is_c2=null**) |
| `madenat.audit.log` de costeo | **0** |
| `stock.move` / `move.line` / `picking` / `quant` / `lot` | 145 / 212 / 30 / 168 / 132 |
| `account.move` / `account.payment` | 1 / 0 |
| `madenat.audit.log` (total) | 278 |

**Lecturas clave:** no hay C2 previo (`is_c2` nulo en las 2 distribuciones legadas) → **no hay C2
distribuido no explicado**; no hay cost lines; no hay ledger C2; no hay auditoría de costeo.

### 2.4 Stop-criterion → **DISPARADO**
1. **Sin usuario no-administrador en Contabilidad** (rol que APLICA C2): el único miembro es uid 2
   (Administrator, `group_system`).
2. **Sin Embarque `delivered` reutilizable**: los únicos `delivered` son 2189/2190 (UAT **D2**),
   expresamente prohibidos como target. Crear uno nuevo por el flujo **D2** exige **rebaja física**
   (movimiento de inventario, restringido salvo autorización específica) o **escribir `state`
   directamente** (prohibido).
3. **Desajuste de premisa de roles**: uid 8 (Cristhian) pertenece a `group_madenat_costos` (257), por
   lo que **no** queda bloqueado en "preparar" (el escenario UAT-C2-5, que asumía Cristhian bloqueado,
   no puede cumplirse tal cual).

Conforme al mandato, **se detiene antes de crear UAT**.

---

## 3. Datos UAT

**No creados.** El prefijo `UAT-C2-20261004-` (y sus registros previstos: `-VESSEL`, `-SHIP`,
`-CONT-01/02`, `-LOT-01/02`, `-COST-01`) **no fue utilizado**. Motivo: stop-criterion (§2.4).

Conforme al mandato "No usar Embarques 2189/2190 ni UAT anteriores como target de Costeo", no se
reutilizó ningún `delivered` protegido, y no se creó un `delivered` nuevo (exigiría rebaja física o
escritura directa de `state`, ambos fuera de alcance sin autorización específica).

## 4. Aplicación C2

**No ejecutada** (ver `01_uat_c2_apply.txt`). El motor existe y el contrato de servidor está
verificado; no se dispone de target `delivered` lícito ni de usuario Contabilidad no-administrador.
Secuencia del contrato (para cuando se desbloquee):

`action_prepare_distribution()` → crea/reutiliza versión C2 en `draft`
→ `action_apply_distribution()` → `_assert_can_distribute_costs_c2()` + `_c2_assert_user(C2_APPLY_GROUPS)`
→ `lumber.cost.distribution.action_apply_c2()` → `state=applied`, ledger C2 en `stock.lot.cost.line`,
auditoría `shipment_cost_distribution` (SHA-256), chatter; **sin** movimiento de inventario.

## 5. Gates

**No ejecutados** (ver `02_uat_c2_gates.txt`). Contrato verificado **estáticamente** en
`_assert_can_distribute_costs_c2()` / `_c2_gate_checks()`:

| Gate | Condición | Efecto |
|---|---|---|
| delivered | `state != 'delivered'` | `UserError` |
| no_b01_open | `b01_exception_state == 'open'` | `UserError` |
| no_inconsistency / no_return_incomplete | rebaja `reversed` sin retorno R2 | `UserError` |
| no_pending | contenedores pendientes de rebaja física | `UserError` |
| has_source_cost | sin líneas `validated`/`paid` | `UserError` |
| currency_ok | moneda/monto USD ≤ 0 | `UserError` |
| volumen > 0 | `total_volume <= 0` (en prepare) | `UserError` |
| idempotency | costos tardíos no cubiertos por versión applied | `UserError` (exige supersede) |

Están cubiertos además por `tests/test_shipment_costing_c2.py` (T-CST-1..T-CST-12).

## 6. Idempotencia (UAT-C2-3)

**No ejecutada** (ver `03_uat_c2_idempotency.txt`): sin versión `applied` previa no hay objeto.
Contrato: reintento de apply con distribución ya `applied` → `UserError` ("ya tiene una distribución
C2 aplicada … no se duplica"); `_c2_next_version()` no reutiliza versión; sin duplicar ledger; sin
nueva auditoría.

## 7. Costo tardío (UAT-C2-4)

**No ejecutado** (ver `04_uat_c2_late_cost.txt`). Contrato: un costo tardío aprobado no cubierto por
la versión `applied` → `UserError` en `action_prepare_distribution`/`action_apply_distribution`
("requiere redistribución formal (supersede) que no está disponible en esta entrega"); la versión
`applied` y su ledger **no cambian**. **Supersede NO implementado/NO ejecutado.**

## 8. Permisos / RPC (UAT-C2-5)

**No ejecutado** (ver `05_uat_c2_permissions.txt`); se documenta el **hallazgo read-only** que motiva
la detención:

- **PREPARAR** (Costos ∪ Contabilidad) disponible para uid 8 y uid 2.
- **APLICAR** (Contabilidad) disponible **solo** para **uid 2 (Administrator)** → **no existe usuario
  Contabilidad no-administrador** ⇒ **"habilitación mínima separada" requerida**.
- uid 8 (Cristhian) **no** está bloqueado en preparar (tiene Costos); sí bloqueado en aplicar
  (`_c2_assert_user` → `AccessError`).
- uid 6/7 (común) → `AccessError` en prepare/apply (contrato).
- `write({'state':'applied'})` / `shipment.write({'cost_distribution_state':'distributed'})` y
  contextos falsos: **no ejecutados** (serían escritura real si no fallaran); el contrato prevé
  bloqueo por ACL + token de proceso.

---

## 9. Auditoría / hash

**No generada** (no hubo aplicación). Contrato: al aplicar se crea **1** evento
`shipment_cost_distribution` (`batch_id = <id embarque>`), snapshot JSON determinista y
`audit_hash = SHA-256(audit_snapshot)`; eventos `..._supersede` / `..._cancel` reservados.
Conteo actual de auditoría de costeo: **0**.

## 10. Ledger / prorrateo / residual

**No generado.** Contrato verificado en código:
- **Ledger:** `stock.lot.cost.line` con `shipment_id`, `distribution_id`,
  `source_shipment_cost_line_id`, `partnerid` (**campo real `partnerid`, no `partner_id`**),
  `cost_type` mapeado (`freight`/`ocean_freight`/`port`/`customs`/`insurance`/`other`).
- **Base:** `C2_BASIS = 'final_logistic_volume'` — prorrateo por **volumen logístico final** del lote
  (`vol_shipment_m3` o `volumen_m3`), lotes elegibles = contenedores con rebaja física **activa**
  (excluye pendientes y líneas R2 `reversed`).
- **Residual:** `C2_RESIDUAL_RULE = 'largest_base_lot'` — ajuste determinista al lote de mayor base;
  tolerancia `C2_MONETARY_TOLERANCE = 0.01`.
- `total_source_cost_usd` = Σ `amount_usd` de líneas aprobadas; `total_distributed_usd` = Σ
  allocations; `residual_usd` = ajuste aplicado. Cota: **Σ allocations = total fuente**.
- `stock.lot.cost.line` con `shipment_id` = **0**; `logistic_cost_usd` no reescrito por SQL (compute ORM).

## 11. Stock / finanzas / SV

**Sin cambios** (Δ0 frente a la línea base):
`stock.move` 145 · `stock.move.line` 212 · `stock.picking` 30 · `stock.quant` 168 · `stock.lot` 132 ·
`stock.lot.cost.line` 53 (0 con `shipment_id`) · `lumber.shipment.cost.line` 0 ·
`account.move` 1 · `account.payment` 0 · `madenat.audit.log` 278 (0 de costeo).
No se ejecutó rebaja/zarpe/B-01/R1/R2/Entrega/SV/imputación ni retorno parcial.

## 12. Integridad UAT / histórica

Verificado **intacto** (revisión read-only):
- Histórica: ship 1537 `in_transit`, cont 1509 `shipped`, pick 7065 `done`.
- UAT Rolleo: vessel 619/620 · voyage 565 · ship 1644/1645/1646 · cont 1629/1630/1631 ·
  audit 19699..19704 (uid 8).
- UAT Borrador: 1704 `draft` · 1705/1706 `confirmed` · 1707 `in_transit`.
- UAT B-01: 1867 `in_transit/none` · 1868 `in_transit/open` · 1869 `confirmed/none`.
- UAT R1: 1885 `in_transit/resolved` · cont 1888 `rebajado`.
- UAT D2: 2189/2190 `delivered` (no reutilizadas).

Ningún registro protegido fue tocado. No se modificó código/roles/ACL/tests/XML/manifest; sin
commit/push.

## 13. Evidencia persistida

`/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_COSTING_C2_20261004/`:

| Archivo | Contenido |
|---|---|
| `00_precheck_baseline.txt` | Precheck read-only completo + stop-criterion |
| `01_uat_c2_apply.txt` | Escenario UAT-C2-1 — NO EJECUTADO |
| `02_uat_c2_gates.txt` | Escenario UAT-C2-2 (gates) — NO EJECUTADO |
| `03_uat_c2_idempotency.txt` | Escenario UAT-C2-3 — NO EJECUTADO |
| `04_uat_c2_late_cost.txt` | Escenario UAT-C2-4 — NO EJECUTADO |
| `05_uat_c2_permissions.txt` | Escenario UAT-C2-5 — hallazgo de roles (read-only) |
| `06_final_validation.txt` | Baseline sin cambios + integridad |
| `UAT-C2-20261004_RESULTADO.md` | Este informe |

## 14. Dictamen

> ### **B. `UAT BLOQUEADA — INDICAR ESCENARIO, EVIDENCIA Y ACCIÓN`.**
>
> **Escenario bloqueado:** PRECHECK (previo a UAT-C2-1..5). No se ejecutó ningún escenario; no se
> creó ningún dato UAT.
>
> **Evidencia:** `00_precheck_baseline.txt` §7/§9 (roles) y §6 (delivered=2189/2190); `05_uat_c2_permissions.txt`.
>
> **Acción requerida (para desbloquear, en una fase separada y autorizada):**
> 1. **Habilitar un usuario Costos/Contabilidad NO-administrador** — concretamente un usuario con
>    `group_madenat_contabilidad` sin `group_system`, dedicado a aplicar C2 (evitar uid 2 *Administrator*).
>    Alternativa: autorización expresa y documentada para ejecutar C2 con uid 2.
> 2. **Definir el target `delivered`:** autorizar (a) reutilizar 2189/2190 pese a ser UAT D2, **o**
>    (b) crear un Embarque UAT nuevo y llevarlo a `delivered` por el flujo D2 — lo que requiere
>    **autorización específica** para la rebaja física (movimiento de inventario) indispensable.
> 3. **Ajustar la premisa de la UAT-C2-5** (Cristhian pertenece a Costos; no está bloqueado en preparar).
>
> **Estado del motor:** el C2 está **implementado e instalado** (métodos, campos, vista, gates,
> ledger, residual, auditoría). El bloqueo es **de ROLES y de DATOS**, no de código.
>
> **No se avanzó** a Billing/Pagos/R3/retorno parcial. **Sin** cambios de stock/finanzas/SV.
> **Sin** commit/push. **Fin del informe.**
