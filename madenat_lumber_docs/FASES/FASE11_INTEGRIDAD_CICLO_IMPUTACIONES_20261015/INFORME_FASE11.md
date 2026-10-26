# INFORME FASE 11 — Integridad del ciclo de vida de las imputaciones SV (A-1, B-1, M-2, M-4, B-2, B-3)

**Fecha:** 2026-10-15 · **Entorno:** LOCAL `madenat_test` (+ base temporal de instalación limpia) ·
**Módulo:** `madenat_lumber_logistics` **18.0.1.32.0 → 18.0.1.36.0**
**Repositorio:** `custom_addons/` · **Rama:** `feat/guia-correccion-documental-preservada-20261002`
**HEAD inicial:** `ee7b7c681a936775d181ebf3e215900884b941ba` · **HEAD final:** `254e6d3`
**Referencia:** `FASES/AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/INFORME_AUDITORIA.md` (§1.2 y §7)
**Alcance:** proteger el ciclo de vida documental (A-1, B-1, M-2, M-4, B-2, B-3) con TDD, commitear y validar. Sin
push, sin ramas, sin reset/clean/stash/rebase/amend, sin `-u all`, sin cambios en datos reales, sin tocar
`IMP04823`/`IMP02220`, sin `costing` ni menú de `reports`. **NO se ha desplegado.**

---

## 0. Resumen ejecutivo

| Criterio de cierre | Estado |
|---|---|
| El estado y las marcas de transición sólo cambian por los métodos oficiales; `write`/`create` públicos los rechazan (también con `sudo()` y contexto) | ✅ verificado (17 pruebas + escenarios D/E/F/G) |
| No se puede fabricar un `applied` sin firma ni un `cancelled` sin rastro | ✅ verificado (A-1/B-1 + B-3) |
| La reversa es segura ante concurrencia (locks + revalidación, sin «último gana») | ✅ verificado (M-2/M-2b, lock externo real) |
| Cadena reversa/anulada → nueva enlazada (`origin_imputation_id` / `reversed_imputation_id`) | ✅ verificado (M-4 + ESC-1 real: `origen: IMP14161`) |
| Líneas y repartos inmutables en estados terminales | ✅ verificado (B-2) |
| **0 fallas nuevas por nombre**; datos reales sin cambios | ✅ 4 failed/0 error de 536 (mismo baseline); conteos y hashes idénticos |

**Desviación declarada (commits).** El plan pedía **5 commits** (4 de código por concern + 1 de documentación) con
versiones `18.0.1.33.0 → 18.0.1.36.0`. Los seis arreglos viven en el **mismo archivo** y en el **mismo conjunto de
métodos** (`madenat_sv_imputation.py`), de modo que separarlos exigía un troceado manual de hunks (riesgo de
commits intermedios rotos, no corregibles con `amend`). Se entregaron **2 commits atómicos** (código +
documentación) con la **versión final 18.0.1.36.0**. Se reporta explícitamente por la regla «ante la duda, no
commitear y reportar».

---

## 1. Baseline y garantía de no-cambios

**Antes:** respaldo con el procedimiento de A1 (`pre/`): `custom_addons_worktree.tar.gz`, `wip_tracked_HEAD.diff`,
`wip_sha256_before.txt` + `wip_combined_sha256_before.txt`, `head_before.txt`, `branch_before.txt`,
`git_status_before.txt` (11 entradas), `madenat_test_pre_fase11.dump.gz` (`gzip -t` OK),
`imputations_before.txt`, hashes de fila y de líneas.

```
HEAD   = ee7b7c681a936775d181ebf3e215900884b941ba
rama   = feat/guia-correccion-documental-preservada-20261002
git status --porcelain -> 11 entradas (10 costing + 1 menu de reports)   [identico antes/despues]
madenat_test -> guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1 sv_op=1
md5(filas 1189+2733)=987223f30299a910fd49653dafe77c20 · md5(lineas)=fcd56adec11b20e0417fb39b4be4f01a
```

**Después:** conteos y hashes **idénticos** (`post/db_counts_after.txt`, `post/imputation_rows_md5_after.txt`,
`post/imputation_lines_md5_after.txt`, `post/imputations_after.txt`). `IMP00946`, `IMP02220` e `IMP04823`
conservan estado, firma, clave y `write_date`.

---

## 2. Investigación y diseño final por cambio (I1 a I6)

Archivo base: `madenat_lumber_logistics/models/madenat_sv_imputation.py` (**M**);
asistente `wizards/madenat_sv_imputation_wizard.py` (**W**); vista `views/madenat_sv_imputation_views.xml` (**V**).

### I1/I2 — A-1 y B-1 (hallazgo ALTA)

**Causa raíz.** El `write()` público sólo guardaba los estados TERMINALES: no había rama para
`rec.state in ('draft','pending')`, así que `write({'state': X})` aceptaba **cualquier** destino desde un
borrador/pendiente (A-1), y `create()` tampoco validaba el estado (B-1). Efecto: fabricar un `applied` **sin
firma/snapshot/ejecutor/bitácora** saltándose el techo duro y los locks —la huella exacta de `IMP04823`— o un
`reversed` de algo que nunca se aplicó.

**Diseño aplicado (decisión de Mauricio: opción B).**
- Nuevo `I2_TRANSITION_MARK_FIELDS` (frozenset): `state`, `audit_hash`, `snapshot_json`, `executed_by_id`,
  `execution_date`, `reversed_by_id`, `reversal_date`, `reversal_reason`, `reversed_imputation_id`,
  `cancelled_by_id`, `cancellation_date`, `cancellation_reason`, `reopened_by_id`, `reopen_date`,
  `reopen_reason`.
- `write()` público: **rechaza** cualquier intersección con esas marcas con `UserError` de negocio (nombra los
  campos). Sin excepción para `sudo()` ni `with_context(...)`.
- `create()`: normaliza `state='draft'`, **rechaza** cualquier otro estado y cualquier marca fabricada.
- `I2_APPLIED_WRITABLE` se reduce a la **entrada del motivo** (`reason`), el token de concurrencia
  (`edit_version`, que el formulario envía con `force_save` para poder guardar el motivo antes de la acción) y el
  chatter.
- Las acciones oficiales escriben por la **vía privada** `_i2_write_protected_state` (`super().write` + bump):
  `action_pending`, `action_back_to_draft`, `action_apply`, `action_cancel`, `action_reverse`,
  `action_reopen_to_draft` y el **sello recíproco** de la cadena.
- **Sin bandera de contexto** (rechazado en el diseño aprobado): el contexto RPC lo controla el cliente.
- **Motivo**: se captura en `reason` (o como parámetro de la acción) y la acción lo congela en su marca. En la
  vista, `reversal_reason`/`cancellation_reason`/`reopen_reason` y `origin_imputation_id` pasan a **sólo lectura**.
- `_i2_build_snapshot(extra=None)` permite adjuntar datos al evento firmado sin alterar los demás snapshots.

### I3 — M-2

`action_reverse` ahora llama a `_i2_lock_resources()` (etiquetas ns 3 + SV ns 2, mismo orden determinista que
`action_apply`) y **revalida el estado** (`invalidate_recordset(['state'])`) tras el bloqueo: si otra conexión
tiene el lock o el documento ya no está `applied`, falla de forma controlada (sin cambios, sin bitácora, sin
sobrescribir usuario/fecha/firma). No se añade reintento automático (mismo patrón que `apply`/`reopen`).

### I4 — M-4

En `_i2_get_or_create`, cuando la clave base está ocupada por una imputación **terminal** (mismo alcance:
guía/procesador/firma), la nueva operación nace con `origin_imputation_id` apuntando al último eslabón terminal;
al aplicarse, `action_apply` sella el recíproco `reversed_imputation_id`. No cambian documentos ni claves
existentes.

### I5 — B-2

Nuevo helper `_i2_check_children_editable(what)` y constante `I2_CHILD_EDITABLE_STATES = ('draft','pending')`:
`create`/`write`/`unlink` de `madenat.sv.imputation.line` y `.sv.line` se rechazan en `applied`, `reversed` y
`cancelled` (antes sólo en `applied`) con mensaje de negocio.

### I6 — B-3

`action_cancel` exige motivo no vacío (tras `strip`; parámetro o `reason`), lo escribe en `cancellation_reason`
(metadata) y lo incorpora al payload firmado del evento `imputation_cancel` (`{'motivo': …}`). Sin cambio de
grupos.

### Ajustes en pruebas y fixtures (documentados)

| Archivo | Ajuste | Motivo |
|---|---|---|
| `test_sv_imputation_lifecycle_integrity.py` | **NUEVO** (17 pruebas) | TDD de A-1/B-1/M-2/M-2b/M-4/B-2/B-3 + matriz por grupos + invariantes |
| `test_sv_rebaja_blindaje.py`, `test_sv_rebaja_operativa.py`, `test_sv_rebaja_ui_limpia.py`, `test_service_return_pending_filter.py` | fixtures que escribían `state` → transiciones OFICIALES | A-1 / B-1 |
| `test_sv_assignment_user_rights.py` | `write({'state':'applied'})` → `action_apply()` con usuario de jefatura | A-1 |
| `test_sv_rebaja_documentary_key.py` | `create(state='cancelled')` → `create` + `action_cancel(reason=…)` | B-1 |
| 18 archivos de pruebas | `.reversal_reason`/`.reopen_reason` → `.reason` (entrada) y `action_cancel(reason=…)` | B-3 + entrada del motivo |
| `wizards/madenat_sv_imputation_wizard.py` | `imp.reopen_reason = reason` → `action_reopen_to_draft(reason=reason)` | A-1 (no escribir la marca por vía pública) |

---

## 3. Tabla de commits

| Orden | Hash | Contenido | Archivos | Versión |
|---|---|---|---|---|
| 1 | `f597f75` | **Código**: A-1, B-1, M-2, M-4, B-2, B-3 + pruebas + vista + asistente | 30 (`1249 +`, `196 -`) | `18.0.1.32.0 → 18.0.1.36.0` |
| 2 | `254e6d3` | **Documentación**: AD-110 + `CANON/19 §19.35` + índice | 3 (`146 +`, `7 -`) | `04` 12.26.0 · `19` 1.33.0 · índice 12.37.0 |

`git add` con rutas explícitas (lista derivada de `git status` limitada a `madenat_lumber_logistics/` y a los
tres documentos canónicos): **nunca** `-A` ni `.`. `costing` (10 entradas) y el menú de `reports` (1) **no** se
commitearon. Barrido de credenciales sobre el diff: **sin hallazgos** (sólo correos de prueba `@madenat.cl` del
propio patrón del repo). `compileall` del módulo: OK.

---

## 4. Pruebas nuevas y regresión comparada con el baseline

**Baseline propio (antes de tocar código):** `logistics` completo → **4 failed / 0 error de 528**
(`TestProcessorLocations.test_09_auditoria_envio_normal`, `TestProcessorShipmentAD89.test_t1/t5/t6`).

**Suites nuevas (TDD):** `TestSvImputationLifecycleIntegrity` + `TestSvImputationReverseLocks` →
**0 failed / 0 error de 17** (`logs/t1_new_tests.log`). Cubren: A-1 en `draft`/`pending` y por `write`, `sudo()` y
contexto; marcas bloqueadas una por una (y valores intactos); B-1 (`create` en estado terminal y con marcas);
caminos oficiales con bitácora, firma y recomputes de `stock.lot`; M-2b (sin «último gana»); M-2 con **lock
externo real** (conexión independiente y limpieza por IDs); M-4 (enlace de origen y recíproco, sin tocar las
existentes, y sin enlace cuando no hay terminal); B-2 (contenido congelado y editable tras «Volver a borrador»);
B-3 (motivo obligatorio + metadata + bitácora + chatter); invariantes (`applied_m3` == Σ repartos aplicados,
saldo documental no negativo, ninguna aplicada sin firma); **matriz por grupos** operaciones/jefatura/gerencia/
auditoría/sin grupo.

**Regresión completa con el código final:** `logs/s2_logistics_full.log` → **4 failed / 0 error de 536** (el
mismo subconjunto del baseline) ⇒ **0 fallas nuevas por nombre**. La primera pasada (`logs/s1_logistics_full.log`)
detectó 3 errores en `test_service_return_pending_filter.py` (fixture que nacía con `state=`), corregidos en el
mismo ciclo antes de commitear.

---

## 5. Re-ejecución de los escenarios de la auditoría (con rollback)

Copias de los 7 scripts de la auditoría en `evidence/` y ejecución con `odoo shell` + `rollback` (nunca
`commit`). Los `exit=1` **son la evidencia buscada**: los scripts originales ejercitaban la vía pública y ahora
chocan con la protección.

| Esc. | Log | Resultado observado |
|---|---|---|
| 1–2 (A original) | `esc_A.log` | detiene en la primera escritura directa de marca (A-1 bloqueado) |
| 1 (A adaptado) | `esc_A_fase11.log` | crear → aplicar → **reversar** → nueva → aplicar; **`origen: IMP14161`** (M-4) |
| 1–2 (A adaptado v2) | `esc_A_fase11b.log` | ESC-1 completa + ESC-2: anulación **con metadata** (por/ fecha/ líneas/ repartos conservados), clave distinta, reapertura bloqueada por trabajo vigente, nueva aplicada |
| 3–4 (B) | `esc_B.log` | doble asignación bloqueada por techo duro; la anulación sin motivo choca con el guard **B-3** |
| C | `esc_C.log` | forense de sólo lectura: completo (`exit=0`) |
| 4 (D) | `esc_D.log` | `write({'state': …})` → **UserError A-1** («marcas de transición… usa las acciones oficiales») |
| 6 (E) | `esc_E.log` | **UserError A-1** en la escritura directa de `state` |
| 6 (F) | `esc_F.log` | **UserError A-1** |
| 7 (G original) | `esc_G.log` | **UserError A-1** al escribir `reversal_reason` |
| 7 (G adaptado) | `esc_G_fase11.log` | ciclo completo por vías oficiales (`exit=0`) |

---

## 6. Evidencia de `IMP04823` e `IMP02220` sin cambios

```
id,name,state,audit_hash,documentary_key,write_date          (antes = despues)
492 |IMP00946|applied |33ec20ba…|IMP-32300-F76F2C611A9C9972|2026-10-03 22:18:19.409938
1189|IMP02220|applied |3164c42d…|IMP-1198-E95825AAF94E58AD|2026-10-10 22:30:45.455365
2733|IMP04823|cancelled|        |IMP-1198-A87816E2021EC9AA|2026-10-12 19:43:36.45072
md5(filas 1189+2733)=987223f30299a910fd49653dafe77c20  ·  md5(lineas)=fcd56adec11b20e0417fb39b4be4f01a  (identicos)
conteos: guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1 sv_op=1  (identicos)
```

---

## 7. Riesgos residuales y pendientes

1. **Datos heredados (fuera de alcance, sin tocar):** `IMP02220` (aplicada con 0 repartos positivos), `IMP04823`
   (anulada sin metadata, bitácora ni firma) y los eventos `imputation` de guías `TX10` sin
   `guia_processing_id`. Su regularización es una decisión de negocio.
2. **M-3** (régimen de acceso/`compute_sudo` de los campos vivos de `stock.lot`): documentado en AD-110, **no**
   corregido.
3. **Despliegue y verificación en el remoto:** no ejecutados (fuera de autorización). Ver `RUNBOOK_FASE11.md`.
4. **`origin_imputation_id` en el formulario** queda de sólo lectura (la cadena la gestiona el sistema); si se
   quisiera edición manual, sería una decisión nueva.
5. **Riesgo de la desviación de commits:** los 4 sub-lotes del plan quedaron en 1 commit de código; si se desea
   granularidad de despliegue por concern, requiere una fase de re-troceado (no se puede reescribir con `amend`).

---

## 8. Entrega

* `INFORME_FASE11.md` (este archivo), `RUNBOOK_FASE11.md`, `CHECKLIST_MANUAL_MAURICIO.md`.
* `pre/` y `post/`: respaldos, hashes, conteos y evidencia de no-cambios. `logs/`: baseline, suites, regresión y
  escenarios. `evidence/`: scripts de auditoría (originales y adaptados) y la suite nueva.
* **Sin push, sin ramas nuevas, sin reset/clean/stash/rebase/amend, sin despliegue, sin conexión al remoto.**

---

## 9. Validación en instalación limpia (base temporal)

Desde un **clon git limpio** de `custom_addons` (2 commits de la fase, `git status --porcelain` = **0 cambios**;
sin el WIP de `costing`/`reports`), copiado al contenedor y usado como **única** ruta de addons:

1. **Instalación desde cero** de `madenat_lumber_logistics` y sus dependencias en `madenat_fase11_install_test`
   (`--without-demo=all`): **exit 0** (`logs/clean_install.log`, `logs/clean_install.exit`).
2. **Suites del flujo tocado** en esa base (`logs/clean_suites_flow.log`): **0 failed / 8 errors de 137**, y las
   **17 pruebas nuevas en verde**. Los 8 errores son **ambientales/prexistentes**, no del flujo de imputación:
   `AttributeError: 'madenat.guia.processing' object has no attribute 'toll_order_id'` — campo aportado por un
   módulo que **no** se instala en el alta limpia—, en clases de otros recorridos (`TestSvRebajaBlindaje`,
   `TestSvRebajaCierre`, `TestSvImputationI2`) y en la ruta de
   `models/madenat_processor_return_link.py` (_guia_processor_), **archivo no modificado** por esta fase.
3. **Módulo completo** en la base limpia (`logs/clean_suites.log`): 1 failed + 142 errors, **todos** de la misma
   naturaleza (59 `toll_order_id`, 48 `KeyError: 'lumber.billing.consolidation'`, 28 «No se encontró un tipo de
   operación de traslado interno» por configuración no sembrada y 1 por precisión decimal 2 vs 4). Es el mismo
   tipo de brecha de **configuración no sembrada** ya documentada en la FASE 10 para el alta limpia; **no** es
   comparable con la corrida del módulo completo sobre `madenat_test` (4 failed / 0 error).
4. **Limpieza:** base `madenat_fase11_install_test` **eliminada**; copia del clon borrada del contenedor
   (`/var/lib/odoo/addons/18.0/fase11_clean`) y de `/tmp`. `madenat_test` **no** se tocó.



