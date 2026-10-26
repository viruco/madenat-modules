# INFORME FASE 10 — Corrección del registro de etiquetas en la rebaja SV (S2, S3, S1)

**Fecha:** 2026-10-15 · **Entorno:** LOCAL `madenat_test` (+ base temporal de instalación) · **Módulo:**
`madenat_lumber_logistics`
**Repositorio:** `custom_addons/` · **Rama:** `feat/guia-correccion-documental-preservada-20261002`
**HEAD inicial:** `677294b7cdc3e0cfbe1cdaef441efcb2234f8681` · **HEAD final:** `ee7b7c681a936775d181ebf3e215900884b941ba`
**Referencia:** `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/INFORME_DIAGNOSTICO.md`
**Alcance:** corregir los defectos **F1/F2/F3** (S2 → S3 → S1) con TDD, commitear 3 correcciones + 1 commit de
documentación, validar (regresión por nombre, escenario real revertido, instalación desde cero) y **NO**
desplegar. Sin push, sin ramas, sin reset/clean/stash/rebase/amend, sin `-u all`, sin cambios en datos reales,
sin tocar `IMP04823`/`IMP02220`.

---

## 0. Resumen ejecutivo

| Criterio de cierre | Estado |
|---|---|
| Preparar etiquetas con una selección válida **las registra** aunque exista un documento aplicado/reversado/anulado de la misma guía | ✅ verificado (escenario real revertido, `IMP12849` con 2 etiquetas) |
| La lista y el contador de «Trabajo en preparación» **excluyen** los estados terminales | ✅ verificado (SV 10215: campo `[]`, contador `0` con `IMP04823` anulado) |
| **No** se pueden guardar documentos **vacíos** | ✅ verificado (`UserError` de negocio, sin documento creado) |
| Documentos y firmas **históricas intactos** | ✅ hashes de `IMP02220`/`IMP04823` idénticos antes/después; receta base de la clave byte a byte |
| **0 fallas nuevas** por nombre; datos reales sin cambios | ✅ 4 failed/0 error en las 3 corridas (mismo subconjunto del baseline); conteos y WIP idénticos |

---

## 1. Baseline y garantía de no-cambios

**Antes (y después) de TODO el trabajo:**

```
rama   = feat/guia-correccion-documental-preservada-20261002
HEAD   = 677294b7cdc3e0cfbe1cdaef441efcb2234f8681   (inicial)
git status --porcelain → 11 entradas (10 costing + 1 menú de reports)   [antes y después]
sha256(WIP 11 archivos) = 1068038214c2fcbfa5a3c80334397005f518462aee444310d0a62ffa366afe21  (idéntico antes/después)
madenat_test: guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1   (idéntico antes/después)
IMP02220(1189) applied  key=IMP-1198-E95825AAF94E58AD  2 líneas
IMP04823(2733) cancelled key=IMP-1198-A87816E2021EC9AA  0 líneas  work_sv_lot_id=10215
md5(filas 1189+2733)=987223f30299a910fd49653dafe77c20 · md5(líneas)=4cf7b8d016236d4dbb4206f697ee1af3
```

**Respaldo previo** (`pre/`, fuera del repositorio): `custom_addons_worktree.tar.gz` (`gzip -t` OK),
`madenat_test_pre_fase10.dump.gz` (`gzip -t` OK), `wip_tracked_HEAD.diff`, `wip_sha256_before.txt`,
`db_counts_before.txt`, `imputations_before.txt`, `imputation_hashes_before.txt`.

**Respaldo posterior** (`post/`): `git bundle create … HEAD` → `bundle verify` = «The bundle records a complete
history» · `custom_addons_worktree_after.tar.gz` (`gzip -t` OK) · `SHA256SUMS.txt` ·
`wip_sha256_after.txt` (idéntico al previo) · `db_counts_after.txt` (idéntico) · `imputation_hashes_after.txt`
(idéntico).

---

## 2. Investigación previa (solo lectura)

1. **Informe de diagnóstico** releído íntegro (F1/F2/F3, E1–E8, T1–T7) + los 7 scripts `repro_1..7` reutilizados
   como base de las pruebas.
2. **S2 — lecturas del O2M y del contador.** `stock.lot.sv_assignment_work_imputation_ids` era un `One2many`
   con `domain` declarativo (que el ORM **no aplica** al leer) y `_compute_sv_assignment_work` contaba con
   `len(...)` de ese mismo campo; único consumidor además del modelo: la vista
   `views/madenat_sv_imputation_views.xml` (sección «Trabajo en preparación» + botón «Continuar»). En cada
   estado: `draft`/`pending` = trabajo; `applied`/`reversed`/`cancelled` = terminal (no deben aparecer).
3. **S3 — caminos que crean/actualizan líneas.** Todos pasan por `_i2_build_imputation` (`action_prepare`,
   `action_pending`, `action_apply` vía `_i2_guarded_build`); el borrado de líneas no incluidas está en el
   propio `_i2_build_imputation`. **Ninguno de los flujos legítimos dependientes de «guardar vacío» existe**:
   `action_cancel`, `action_reopen_to_draft`, `action_back_to_draft` y `action_reverse` se invocan desde el
   **documento** y **no** pasan por el asistente ⇒ no dependen de él. Confirmado con evidencia (SG-04).
4. **S1 — firma y clave.** La firma (`_i2_signature`, wizard) sólo contenía los repartos SV; la clave
   (`_i2_build_documentary_key`, modelo) es `IMP-<guia>-<sha256('I2|guia|processor|signature')[:16]>` y
   `documentary_key` es **UNIQUE**. La firma **no se persiste**: sólo se usa para *construir* claves, por lo que
   incluir la selección **no altera la verificación** de documentos históricos (que se apoya en `audit_hash`).
   `_i2_get_or_create` buscaba por clave **sin filtrar estado**. Conclusión: se puede ampliar la firma y acotar
   la reutilización, conservando la receta base para el caso `signature=''` (retrocompatible byte a byte).
5. **Unicidad.** La clave nueva se construye con un **discriminador** determinista (id del documento que ocupa la
   clave) que entra en el material hasheado ⇒ clave distinta sin romper UNIQUE ni la trazabilidad (reconstruible).
6. **Pruebas existentes dependientes de la firma/clave actual:** inventariadas por `grep` — `_i2_signature`,
   `_i2_get_or_create`, `_i2_build_documentary_key` sólo se usan en el wizard/modelo; las únicas aserciones
   impactadas fueron SAVE-13 y FLOW-02 (esperaban `UserError` de «Continuar»), actualizadas con la ruta operativa.

**Ningún punto contradijo las decisiones de diseño aprobadas.**


---

## 3. Diseño final de S2, S3 y S1

### 3.1 S2 — Filtro efectivo de «Trabajo en preparación» (F2)

* **`stock.lot.sv_assignment_work_imputation_ids`**: de `One2many('madenat.sv.imputation','work_sv_lot_id',
  domain=…)` a **`Many2many` calculado NO almacenado** (`store=False`, relación explícita
  `stock_lot_madenat_sv_imputation_work_rel`, `column1='lot_id'`, `column2='imputation_id'`; **sin tabla**).
  El compute hace **búsqueda explícita**: `search([('work_sv_lot_id','=',lot.id), ('state','in',('draft','pending'))])`.
  Sin `sudo` (respeta compañía y reglas de registro, igual que `sv_assignment_imputation_ids`).
  Nombre y semántica **sin cambios**.
* **`_compute_sv_assignment_work`**: `sv_assignment_work_count = len(work)` (la misma búsqueda) y
  `sv_assignment_work_m3` = Σ repartos positivos de las líneas de documentos en trabajo (sin cambios).
  Se retira la dependencia `sv_assignment_work_imputation_ids.state` (ahora es un calculado, no almacenado).
* **`action_continue_preparation`**: sólo `draft`/`pending` abren el asistente. Estado terminal ⇒
  `ir.actions.client` / `display_notification` con mensaje operativo (anulado ⇒ «Volver a borrador»;
  aplicado/reversado ⇒ reversa). **No** es un error técnico.
* **Riesgo:** bajo (cambio de tipo de campo calculado; verificado con la suite completa del módulo). *Pruebas:*
  WF-01..07 (T2, T3).

### 3.2 S3 — No permitir documentos vacíos (F3)

* En `_i2_build_imputation`, **antes** de crear/actualizar: `included = self._i2_included_lines()` y, si está
  vacío, `UserError` de negocio en español («No se puede guardar un documento de rebaja sin etiquetas…»).
* Al rechazar **antes** de escribir: no se crea documento (ni vacío) y **no** se pierde ninguna línea ya
  registrada (no hay borrado silencioso). El `included` calculado se reutiliza en el resto del método (una sola
  lectura).
* Flujos legítimos intactos: anular, «Volver a borrador», reabrir, reversa (no pasan por el asistente); SAVE-05
  (destino SV previsto con cantidad 0) sigue permitido; el techo duro y las validaciones de `action_apply`
  (`_i2_validate_payload`) no cambian.
* **Riesgo:** bajo. *Pruebas:* SG-01..06 (T6), con `try/except` propio para **no** quedar enmascaradas por el
  savepoint que Odoo interpone en `assertRaises`.

### 3.3 S1 — Clave documental con las etiquetas seleccionadas (F1)

* **`_i2_signature()`** (wizard): partes `L<lot_id>:<nominal>` de las **etiquetas incluidas**
  (`_i2_included_lines()` ordenadas por `processed_lot_id`) **más** las partes de reparto
  `'<lot>:<sv>:<vol>'` (como antes). Determinista.
* **`_i2_build_documentary_key(guia, processor, signature, discriminator='')`** (modelo): la receta base
  `'I2|guia|processor|signature'` **no cambia**; sólo si `discriminator` es no vacío se añade
  `'|<discriminator>'` al material antes de hashear. Con el valor por defecto (`''`) el resultado es
  **byte a byte** el histórico.
* **`_i2_get_or_create`**: sólo devuelve `draft`/`pending` por clave. Si la clave está tomada por un documento
  **`applied`** ⇒ `UserError` («Esta rebaja ya se aplicó con esta misma selección…»). Si está tomada por
  **`reversed`/`cancelled`** ⇒ se itera con `discriminator = str(doc.id)` (encadenado con `>` si hiciera falta)
  hasta hallar una clave libre y se crea un documento **NUEVO** con esa clave. Determinista (no depende de fecha
  ni de sesión) y **trazable** (reconstruible desde el documento que ocupaba la clave).
* **Una sola implementación central**: la receta y la reutilización viven en el modelo; el asistente sólo aporta
  la firma (`_i2_signature`) y llama a `_i2_get_or_create`.
* **Sin migraciones.** Las claves y firmas históricas no se tocan ni se recalculan.
* **Riesgo:** medio (cubre idempotencia, no duplicación y conservación de claves). *Pruebas:* DK-01..08 (T1, T4,
  T5, E7) + perfil `IMP04823`.

---

## 4. Tabla de commits

| # | Hash | Tipo | Archivos | Versión `madenat_lumber_logistics` |
|---|---|---|---|---|
| 1 | `19611d0` | `fix(logistics)` S2 | `models/madenat_sv_imputation.py`, `tests/test_sv_rebaja_work_filter.py` (nuevo), `tests/test_sv_rebaja_persistencia.py`, `tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md` | 18.0.1.29.0 → **18.0.1.30.0** |
| 2 | `e2d6b64` | `fix(logistics)` S3 | `wizards/madenat_sv_imputation_wizard.py`, `tests/test_sv_rebaja_empty_guard.py` (nuevo), `tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md` | 18.0.1.30.0 → **18.0.1.31.0** |
| 3 | `7ac1fcb` | `fix(logistics)` S1 | `models/madenat_sv_imputation.py`, `wizards/madenat_sv_imputation_wizard.py`, `tests/test_sv_rebaja_documentary_key.py` (nuevo), `tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md` | 18.0.1.31.0 → **18.0.1.32.0** |
| 4 | `ee7b7c6` | `docs(canon)` AD-109 | `CANON/04_DECISION_LOG.md` (12.24.0→12.25.0), `CANON/19_…md` (1.31.0→1.32.0), `CANON/05_BACKLOG.md` (8.29.0→8.30.0), `CANON/INDICE_DOCUMENTACION.md` (12.35.0→12.36.0) | — |


---

## 5. Pruebas: TDD, resultados y regresión comparada

### 5.1 TDD por corrección (rojo → verde)

| Corrección | Suite nueva | Rojo (contra el código anterior) | Verde (tras la corrección) |
|---|---|---|---|
| **S2** | `test_sv_rebaja_work_filter.py` (WF-01..07) | **3 failed + 2 errors de 7** (WF-02, WF-03, WF-04, WF-05, WF-06) | **25/25** (WF + `test_sv_rebaja_persistencia`), 0 failed / 0 error |
| **S3** | `test_sv_rebaja_empty_guard.py` (SG-01..06) | **2 failed de 6** (SG-01, SG-03; «UserError not raised») | verde en la corrida completa del módulo |
| **S1** | `test_sv_rebaja_documentary_key.py` (DK-01..08) | **2 failed + 3 errors de 9** (DK-01 firma vacía; DK-02 `discriminator` inexistente; DK-03b y DK-04 «fue anulado»; DK-05 «ya no admite preparación (estado applied)») | **9/9**, 0 failed / 0 error |

Las firmas de fallo del «rojo» reproducen **literalmente** los síntomas del diagnóstico F1/F2/F3.

### 5.2 Regresión completa del módulo (comparada POR NOMBRE)

Comando (mismo patrón que el baseline vigente, FASE 5):

```
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_logistics \
  --test-enable --test-tags=/madenat_lumber_logistics \
  --stop-after-init --http-port=9997 --max-cron-threads=0
```

| Corrida | Resultado | Conjunto de fallas |
|---|---|---|
| Baseline vigente (FASE 5, HEAD `677294b`, core+intake+logistics) | 6 failed + 4 error de 1448 | 10 (lista `FASE5_COMMITS_20261015/logs/baseline_10_fallas.txt`) |
| **S2** (`19611d0`) | **4 failed + 0 error de 513** | idéntico al subconjunto logístico del baseline |
| **S3** (`e2d6b64`) | **4 failed + 0 error de 519** | idéntico |
| **S1** (`7ac1fcb`) | **4 failed + 0 error de 528** | idéntico |

Fallas presentes en las tres corridas (las 4 del baseline para `logistics`; **0 nuevas por nombre**):
`TestProcessorLocations.test_09_auditoria_envio_normal`,
`TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo`,
`TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1`,
`TestProcessorShipmentAD89.test_t6_idempotencia`.
Registros por corrida: `logs/s2_logistics_full_failures.txt`, `logs/s3_logistics_full_failures.txt`,
`logs/s1_logistics_full_failures.txt`.

### 5.3 Metodología de validación de S2 (registro expreso)

Para no interferir con la corrida en curso y evitar bloqueos de la herramienta, la validación de S2 se hizo con
este protocolo, que quedó como método de la fase:

1. **Nunca se lanzó** una segunda corrida de Odoo contra `madenat_test` mientras hubiera una activa: antes de cada
   corrida se comprobó el proceso (`ps -eo args | grep 'odoo -d madenat_test'`) y la aparición de la línea final
   `odoo.tests.result` / `Initiating shutdown` en el log.
2. **Cada consulta de estado fue distinta y útil** —existencia de la línea de resultado, conteo de «Starting
   Test» (progreso), conteo y **nombres** de `FAIL:`/`ERROR:` y comprobación del proceso— en lugar de repetir la
   misma espera.

---

## 6. Escenario real con datos de prueba equivalentes (SIN tocar los registros reales)

Script: `evidence/escenario_real_sv841.py` (ejecutado con `odoo shell`, **transacción revertida** al final).
Salida literal: `logs/escenario_real_sv841.log`. Guía **1198** + SV `SV00000000841` (id 10215), con
`IMP02220` (aplicada) e `IMP04823` (anulada) presentes y **no** abiertos en modo escritura.

| Paso | Resultado observado |
|---|---|
| Estado de partida | `IMP02220` applied key `IMP-1198-E95825AAF94E58AD` (2 líneas) · `IMP04823` cancelled key `IMP-1198-A87816E2021EC9AA` (0 líneas, `work_sv_lot_id` = SV841) |
| **0** (F2) | `sv_assignment_work_imputation_ids` → **`[]`** y contador → **`0`**, aunque `IMP04823` sigue **vinculado** (`search`) ⇒ la anulada **no se lista ni cuenta** |
| **1** (F3) | Guardar **sin** etiquetas (17 candidatas, 0 seleccionadas) → **bloqueado** con «No se puede guardar un documento de rebaja sin etiquetas…»; documentos de la guía tras el rechazo: **`['IMP04823','IMP02220']`** (ninguno nuevo) |
| **2** (F1) | Preparar **con** 2 etiquetas seleccionadas (no imputadas por `IMP02220`) y destino SV sin cantidad → **documento NUEVO `IMP12849`**, `draft`, **2 etiquetas REGISTRADAS**, 0 repartos, clave nueva `IMP-1198-4FB38DC3512996AE`; firma `L18378:1.781|L18377:2.197`; **no** adoptó `IMP02220`/`IMP04823` |
| **3** (F2) | Sección del SV → `['IMP12849']`, contador **1** (la anulada sigue fuera) |
| **4** (T3) | «Continuar» sobre `IMP04823` → `ir.actions.client` / `display_notification` con «…está ANULADO… Usa "Volver a borrador"…» (**sin** error técnico) |
| Cierre | `env.cr.rollback()` ⇒ **cero residuos** (conteos y WIP reproducidos idénticos) |

---

## 7. Evidencia de que NADA cambió (documentos y firmas históricas)

```
WIP 11 archivos (sha256 combinado): idéntico antes/después  (1068038214c2fcbfa5a3c80334397005f518462aee444310d0a62ffa366afe21)
madenat_test: 13|8|12|151|327|3|3|1                        (idéntico antes/después)
md5(filas de IMP02220+IMP04823) = 987223f30299a910fd49653dafe77c20   (idéntico)
md5(líneas de IMP02220+IMP04823) = 4cf7b8d016236d4dbb4206f697ee1af3  (idéntico)
IMP02220: applied, key IMP-1198-E95825AAF94E58AD  → _i2_build_documentary_key(guia, None, '') idéntico
IMP04823: cancelled, key IMP-1198-A87816E2021EC9AA (intacta)
```

* **Clave/firma histórica:** con `discriminator=''` (valor por defecto) `_i2_build_documentary_key` produce
  **byte a byte** el resultado de la receta anterior ⇒ la verificación de firmas de documentos ya aplicados
  (p. ej. `IMP02220`) sigue funcionando exactamente igual (comprobado también en la suite DK-02).
* **Sin migraciones**: no se ejecutó ningún script de datos; ninguna clave ni firma histórica se recalculó.
* **Conteos de `madenat_test`** sin residuos tras todas las corridas y tras el escenario real revertido.
* **Instalación desde cero** en base temporal `madenat_fase10_install_test`: `-i madenat_lumber_logistics`
  completó («Module madenat_lumber_logistics loaded in 1.80s» · «Modules loaded.») y las tres suites nuevas

---

## 8. Riesgos residuales, pendientes y criterio de cierre

**Riesgos residuales**
* La corrección se validó **en local**; el comportamiento en el remoto no se ha verificado (fase local).
* El caso sano de la guía 1198 en **datos reales** exige ahora preparar una **selección** correcta (mejora
  buscada), pero implica una decisión operativa del usuario.
* `documentary_key` UNIQUE + `_check_single_work_per_guia` + bloqueo de recursos sostienen la unicidad; la
  concurrencia real a nivel de transacción sigue cubierta por `test_sv_rebaja_save_lock_tx` (no modificada).

**Pendientes (documentados en `CANON/05_BACKLOG.md`, sección FASE 10)**
1. **Decisión sobre `IMP04823`** (anulada y vacía, con vínculo al SV): conservarla como historia anulada o
   reabrir/rehacer la rebaja de la guía 1198 con el flujo corregido. **No ejecutado.**
2. **Cómo resolver la rebaja de `SV00000000841` en datos reales** con el nuevo flujo (selección correcta).
3. **Verificación en el remoto** del comportamiento corregido.
4. **Trigger de bitácora:** `IMP04823` no tiene evento de creación ni de anulación en `madenat_audit_log` (su
   anulación no pasó por el código) — hallazgo abierto; el trigger está propuesto y **no** implementado.
5. `VIEW-01/04` (navegador) pendiente de confirmación manual; **D1 (`costing`)** y **P2-2** siguen fuera (AD-108).

**Criterio de cierre (de la solicitud)**

| Criterio | Estado |
|---|---|
| Preparar etiquetas con una selección válida las **registra** aunque exista documento aplicado/reversado/anulado | ✅ escenario real (paso 2) + DK-03/DK-03b/DK-04 |
| La lista y el contador de «Trabajo en preparación» **excluyen** los estados terminales | ✅ escenario real (pasos 0 y 3) + WF-02..04 |
| **No** se pueden guardar documentos vacíos | ✅ escenario real (paso 1) + SG-01/SG-03/SG-05 |
| Documentos y firmas históricas **intactos** | ✅ §7 (hashes y clave histórica) |
| **0 fallas nuevas** por nombre; datos reales sin cambios | ✅ §5.2 y §7 |

---

## 9. Anexo — comandos exactos

```bash
# Baseline / no-cambios
cd custom_addons && git status --porcelain | wc -l && git rev-parse HEAD
git status --porcelain | awk '{print $2}' | sort | xargs sha256sum

# Suite nueva (TDD) y regresión del módulo
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_logistics --test-enable \
  --test-tags=/madenat_lumber_logistics:TestSvRebajaWorkFilter --stop-after-init --http-port=9997 --max-cron-threads=0
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_logistics --test-enable \
  --test-tags=/madenat_lumber_logistics --stop-after-init --http-port=9997 --max-cron-threads=0

# Escenario real (transacción revertida; NUNCA commit)
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/escenario_real_sv841.py

# Instalación desde cero en base temporal (se elimina después)
docker exec odoo18_app odoo -d madenat_fase10_install_test --db-filter=^madenat_fase10_install_test$ \
  -i madenat_lumber_logistics --stop-after-init --http-port=9996 --max-cron-threads=0
docker exec odoo18_db dropdb -U odoo --if-exists madenat_fase10_install_test
```

**Archivos de evidencia:** `logs/` (`s2_tdd_before.log`, `s2_after.log`, `s3_tdd_before.log`,
`s1_tdd_before.log`, `s1_after.log`, `s*_logistics_full.log`, `*_failures.txt`, `escenario_real_sv841.log`,
`clean_install.log`, `clean_install_suites.log`) · `evidence/` (`check_sg05_no_doc.py`,
`escenario_real_sv841.py`) · `pre/` y `post/` (respaldos y hashes).

  quedaron **0 failed / 0 error de 22 tests**; la base temporal se **eliminó** después (`dropdb`). El único
  mensaje `<string>:38: (ERROR/3) Unexpected indentation.` durante la carga es **preexistente** (aparece igual
  en la instalación limpia de la FASE 8, que cerró con exit 0) y no es de este flujo.

3. La espera se hizo con `until … grep -q 'odoo.tests.result' … ; do sleep N; done` acotada por `timeout`, y con
   sondeos breves, en lugar de `sleep` largos repetidos.
4. Al terminar, se extrajo el resumen final («N failed, M error(s) de T tests») y la **lista de fallas por
   nombre**, y se comparó con el baseline; el resultado quedó guardado en `logs/` del expediente.
5. Si el proceso hubiera muerto sin resultado, se habría reportado con el último tramo del log **sin relanzar**.

`git status` final: **las mismas 11 entradas** (10 de `costing` + 1 del menú de `reports`), con **hashes
idénticos** a los del baseline. `git log` con los 4 commits encima de `677294b`; **sin** reset ni amend.
**Sin conexión al remoto.**

> **Nota de transparencia:** el cuerpo del mensaje del commit `e2d6b64` contiene un error tipográfico
> («tseleccionar»). No se corrige con `amend` (prohibido por la fase); queda registrado aquí.
