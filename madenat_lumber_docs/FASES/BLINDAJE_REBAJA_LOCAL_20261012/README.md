# BLINDAJE LOCAL Y ESTABILIZACIÓN DEL FLUJO DE REBAJAS — ENTREGA (2026-10-12)

**Entorno:** `madenat_test` **LOCAL** (`odoo18_app` / `odoo18_db`) · **Documentación:** `madenat_lumber_docs`
**Regla de la intervención cumplida:** **SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE
· SIN REPARACIÓN HISTÓRICA.**

---

## 0. Baseline y respaldo (§1)
- **Repositorio:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/.git`
- **Rama:** `feat/guia-correccion-documental-preservada-20261002`
- **HEAD:** `b1d2d1911648f3264bf629c8eccf79a1c140eaf3`
- **WIP previo (preservado):** 84 entradas en `git status --porcelain` → `code/wip_status.txt`,
  `code/wip_uncommitted.diff`, `code/wip_diffstat.txt`.
- **Respaldo real previo:** `code/` (diff + pre-copias de los archivos tocados), `db/madenat_test_pre.dump`
  (`pg_dump -Fc`), `filestore/madenat_test_filestore_pre.tgz`.
- **Versiones locales antes:** logistics `18.0.1.21.0`, intake `18.0.0.11.0`, core `18.0.6.6.0`.

## 1. Hallazgos y causas (§1/§2/§4/§5)
1. **Vía directa de `write` (`cancelled → draft`)**: `write()` autorizaba la transición aceptando una
   **identidad suministrada por el cliente** (`reopened_by_id` + `reopen_reason`), **sin** ejecutar las mismas
   garantías que `action_reopen_to_draft` (no corría `_i2_validate_reopen`, ni locks, ni auditoría). **Causa:**
   el autorizador era un campo del `vals`, no el entorno de ejecución.
2. **Advertencia `stock.lot` `sv_assignment_*`**: 6 campos compartían `_compute_sv_assignment` con `store`
   mixto (4 con `store=True`, 2 con `store=False`) ⇒ Odoo advertía `inconsistent 'store'` e
   `inconsistent 'compute_sudo'` (`compute_sudo` por defecto = `store`). **Causa:** un mismo método compute
   para campos almacenados y no almacenados.
3. **Advertencia consola de intake**: `_compute_review_metrics` dependía de `volume_detail_line_ids.volume_m3`,
   donde `volume_detail_line_ids` es un proxy **Many2many VIRTUAL** (compute+inverse, `store=False`, **no
   buscable**) ⇒ «should be searchable» en cada campo calculado. **Causa:** dependencia sobre un campo no
   buscable en un compute no almacenado.
4. **Sobrescritura de borradores**: persistía «la última escritura gana» (riesgo conocido, sin cambios).

## 2. Correcciones (§2/§4/§5)
- **AUD-ETQ-07 (logistics, `models/madenat_sv_imputation.py`)**: token efímero de **PROCESO**
  (`_I2_REOPEN_TOKENS`, clave `(dbname, uid, imputation_id)`). `action_reopen_to_draft` lo añade antes de su
  `write` (y lo descarta en `finally`); la guarda de `write` **rechaza** cualquier `cancelled → draft` sin
  token. **No** es flag de contexto; **no** acepta identidad del cliente; `sudo()` directo tampoco elude.
  `applied → draft` y `reversed → draft` siguen **prohibidos**.
- **AUD-ETQ-08a (logistics)**: separación `_compute_sv_assignment` (4 campos `store=True`) /
  `_compute_sv_assignment_live` (2 campos no almacenados) y `compute_sudo=False` explícito → elimina los dos
  avisos; **sin sudo** (no expone datos de otra compañía).
- **AUD-ETQ-08b (intake, `models/intake_console.py`)**: dependencia de `_compute_review_metrics` corregida a
  `('source_model', 'source_res_id', 'ingestion_type')` (identidad del origen). Sin `search` ficticio, sin
  cambio de `store`, sin recomputación global.
- **Docs**: `CANON/19 §19.28`, `CANON/02 §17.16.26`, `CANON/03 §29`, `CHANGELOG` de ambos módulos.

## 3. Pruebas directas de `write` (§2, opción A = RECHAZO)
`test_sv_rebaja_reset.py::test_reset_08b_write_con_campos_y_contexto_no_elude`: sobre un anulado, un
`write({'state':'draft','reopened_by_id':…,'reopen_reason':…,'reopen_date':…,'cancellation_date':…})` —y su
variante con `with_context(i2_reopen=True)` y con `sudo()`— **lanza `UserError`**; el estado sigue
`cancelled`; **sin** `reopened_by_id`/`reopen_date`; **sin** auditoría `imputation_reopen`. La **acción
controlada** sí reabre en la misma sesión. (`RESET-08`, `RESET-09` intactos.)

## 4. Concurrencia RESET-16/17 y balances (§3)
`test_sv_rebaja_reset_concurrency.py` (**SingleTransactionCase**; **conexiones PostgreSQL independientes**
vía `db_connect`, `api.Environment` propio por hilo, **eventos/barrera + timeout**, rollback/close en
`finally`). **No** se acredita simultaneidad con pruebas secuenciales.
- **RESET-16** — dos sesiones reabren el MISMO anulado: **A** ejecuta `action_reopen_to_draft` y **mantiene el
  advisory lock de transacción**; **B** es rechazada por el lock con el mensaje funcional («Otra operación
  está modificando…»), **sin** error técnico de PostgreSQL. Balance final: **una** transición `draft`,
  **1** evento `imputation_reopen`, `line_ids`/`sv_line_ids` **sin duplicar**, disponible documental **0**
  (reserva tomada **una sola vez**).
- **RESET-17** — reapertura (A) ∥ aplicación (B) que consumen la **misma capacidad documental del SV** (dos
  etiquetas distintas → mismo SV): la perdedora falla de forma controlada y hace **rollback íntegro**;
  **sin sobreconsumo** (asignado al SV `12,000` ≤ nominal `100`), **sin** auditoría del evento rechazado;
  cada etiqueta reserva su propio nominal (`≤ 10`).
- **Limpieza**: `test_reset_sin_registros_de_prueba_persistentes` verifica que **no** quedan guías/lotes/
  imputaciones de prueba; verificado además en BD (`CONC-%`=0, `CONC1%`=0).

## 5. Advertencias eliminadas y valores preservados (§4/§5)
- Verificación en log de arranque dirigido: `inconsistent` = **0**, `should be searchable` = **0** (antes:
  presentes en cada carga). `stock.lot` y consola de intake **sin** advertencias de cálculo.
- **Sin cambios de valor**: los agregados `sv_assignment_*` conservan su semántica (mismos campos, mismos
  valores); la consola mantiene la misma proyección. **Sin** cambios de `store` indiscriminados; **sin**
  acceso a datos de otra compañía (compute **no** corre como superusuario).
- **Sin** cambios en ingesta ni en la política de volumen.

## 6. Regresión (§7/§8)
- **Suites dirigidas (verde):**
  - `TestSvRebajaReset` + `TestSvRebajaResetConcurrency` (logistics): **0 failed / 0 error**.
  - `TestIntakeConsoleComputeDepends` (intake): **0 failed / 0 error**.
- **Regresión amplia** (`madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics`): **1217** tests,
  `madenat_lumber_intake` **464 tests verde**; fallas **solo** en `madenat_lumber_core` (**no modificado**) y
  en el **conjunto preexistente** de `madenat_lumber_logistics`.
- **Comparabilidad (evidencia directa):** la regresión **solo-logistics** (mismo alcance que la base
  documentada) dio **444 tests, `4 failed, 0 error`** — las **mismas 4 fallas preexistentes** de
  `RESET_REBAJA_20261011` (*4 failed, 0 error de 439*): `TestProcessorLocations.test_09_auditoria_envio_normal`
  y `TestProcessorShipmentAD89.test_t1/t5/t6`. **Ninguna falla nueva** por esta intervención.
  Las fallas de `madenat_lumber_core` (`test_guia_picking_link`, `test_sv_concurrency`,
  `test_sv_escalation_security`, `test_orphan_move_cleanup_savepoint`) son **preexistentes**: el diff de esta
  intervención **no toca** `madenat_lumber_core`. **No** se debilitó ninguna prueba.
- Logs: `logs/step1..5.log` (dirigidas), `logs/regression.log` (amplia), `logs/regression_logistics.log`.

## 7. Propuesta de sobrescritura de borradores (PENDIENTE de decisión) (§6)
`docs/PROPUESTA_SOBRESCRITURA_BORRADORES.md`: versión lógica del documento (`edit_version`), detección de
edición obsoleta en Guardar/Aplicar, mensaje al usuario, conservación de cambios locales, recarga/reintento,
compatibilidad con Guardar/Aplicar. **NO implementada**; requiere **aprobación explícita de Mauricio**.

## 8. Versiones locales (§8)
- `madenat_lumber_logistics`: **18.0.1.21.0 → 18.0.1.22.0**
- `madenat_lumber_intake`: **18.0.0.11.0 → 18.0.0.12.0**
- `madenat_lumber_core`: **18.0.6.6.0** (sin cambios)
- Docs: `19` 1.25.0 → **1.26.0**; `03` 6.33.0 → **6.34.0**; `02` 12.34.0 → **12.35.0**.
- Actualización **solo** de módulos locales afectados (`-u madenat_lumber_logistics,madenat_lumber_intake`).
  **No** `-u all`.

## 9. Archivos y WIP preservado (§1/§8)
- **Modificados por esta intervención:** `madenat_lumber_logistics/models/madenat_sv_imputation.py`,
  `.../tests/test_sv_rebaja_reset.py`, `.../tests/__init__.py`, `.../__manifest__.py`, `.../CHANGELOG.md`;
  `madenat_lumber_intake/models/intake_console.py`, `.../tests/__init__.py`, `.../__manifest__.py`;
  `madenat_lumber_docs/CANON/19,02,03`.
- **Nuevos:** `madenat_lumber_logistics/tests/test_sv_rebaja_reset_concurrency.py`,
  `madenat_lumber_intake/tests/test_intake_console_compute_depends.py`, `madenat_lumber_intake/CHANGELOG.md`.
- **WIP ajeno preservado:** el resto de archivos modificados/no rastreados del árbol quedan **intactos**
  (ver `code/wip_status.txt`). **Sin commit/push.**

## 10. Pendientes reales (§6/§9/§10)
1. **Aceptación de Cristhian**: **pendiente**; sin resultado suyo **no** se declara aceptación
   (`docs/CRISTHIAN_INCIDENCIAS.md`). El «listado remoto vacío» se registra como incidencia a diagnosticar
   (datos/dominio/permisos, **solo lectura**) **antes** de crear o modificar registros remotos.
2. **Sobrescritura de borradores**: propuesta registrada; **pendiente de autorización** de Mauricio.
3. **Evidencia de navegador**: no ejecutada en esta intervención (guion en `docs/`).
4. `IMP02220`/`IMP04823` e históricos **intactos** (no reabiertos ni revertidos).

---
**SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA.**