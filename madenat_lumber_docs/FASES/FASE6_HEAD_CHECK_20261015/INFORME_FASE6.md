# FASE 6 — VERIFICACIÓN DEL HEAD LIMPIO + INVESTIGACIÓN D18/P2-2 + RUNBOOK — INFORME

**Proyecto:** MADENAT — Odoo 18 CE · **Fecha:** 2026-10-15
**Repo:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` · **Rama:**
`feat/guia-correccion-documental-preservada-20261002` · **HEAD verificado:** `ed42df5`
**Expediente (fuera del repo):** `FASE6_HEAD_CHECK_20261015/`
**Entorno:** LOCAL (repo + bases locales). **Nada se ejecutó contra el remoto.**

**Resultado en una línea:** el HEAD `ed42df5` **NO es autosuficiente**: `madenat_lumber_shipping_core`,
`madenat_lumber_core` e `ingestion_engine`/`purchasing` instalan, pero **`madenat_lumber_logistics` falla al
cargar** porque el CSV de ACL commiteado referencia `model_lumber_shipment_rebaja_wizard_line`, un modelo que
**solo existe** en el archivo excluido **D18-2**. Sin cerrar D18 no hay despliegue posible.

---

## 0. BASELINE (antes/después)

| Dato | Valor |
|---|---|
| `git status` | **16 entradas** (13 `M` + 3 `??`) — idénticas al cierre de FASE 5 |
| HEAD / rama | `ed42df54dab62beea0780337971d3657b4232ac1` / `feat/guia-correccion-documental-preservada-20261002` |
| SHA256 del WIP | `sha256sum` de los 16 archivos → `logs/f6_sha_before.txt` (**huella global**
  `35e6808f91c84ee368da14d36a7ba8893863da4b8fcfb459ecd30814fd455e37`) |
| `madenat_test` (solo lectura) | guías **13** · recepciones **8** · usuarios **12** · lotes **151** · bitácora **327** · imputaciones **3** |
| `madenat_test` demo | `base/stock/account/sale/purchase` con `demo=false` ⇒ la base temporal se creó con `--without-demo=all` |

---

## 1. V1 — VERIFICACIÓN DEL HEAD LIMPIO

### 1.1 Procedimiento

1. `git clone --no-hardlinks <repo local> FASE6_HEAD_CHECK_20261015/clone` (sin el WIP: `git status` del clon = **0**).
2. **Comprobación de que el clon no contiene el WIP:** de las 16 entradas excluidas, las **13 modificadas**
   existen **con el contenido del commit** (`git show HEAD:<ruta>` = byte a byte) y las **3 nuevas** están
   **ausentes** ⇒ **16/16 correcto**.
3. Clon copiado al contenedor en `/tmp/fase6_clone`; `--addons-path=/tmp/fase6_clone,<addons del core>` ⇒
   **el `custom_addons` de trabajo NO está en la ruta de addons** (verificado en el log).
4. Base temporal **nueva y única** `madenat_head_check` (nunca se tocó `madenat_test`); instalación desde cero
   `-i madenat_lumber_shipping_core,madenat_lumber_core,madenat_lumber_logistics,madenat_lumber_intake`,
   `--without-demo=all --test-enable --stop-after-init --http-port=9998 --max-cron-threads=0` (sin `-u all`).
5. Cierre por grafo de `depends` (transitividad verificada): la instalación **no** arrastra `costing` ni
   `reports` (ningún módulo del conjunto depende de ellos).

### 1.2 Resultado — pase 1 (instalación completa del conjunto)

| Orden | Módulo | ¿Instala? | Evidencia |
|---|---|---|---|
| 26/71 | `madenat_lumber_shipping_core` | **SÍ** | `Module … loaded in 0.56s, 288 queries`; **sin** `ParseError` |
| 58/71 | `madenat_lumber_core` | **SÍ** | `loaded`; 4 errores de test (no relacionados con los commits, ver 1.4) |
| 65/71 | `madenat_ingestion_engine` | **SÍ** | instalado (dependencia de intake) |
| 66/71 | `madenat_lumber_purchasing` | **SÍ** | instalado (dependencia de toll/purchasing) |
| 68/71 | `madenat_lumber_reception_improvements` | **SÍ** | cargado |
| 69/71 | **`madenat_lumber_logistics`** | **NO** | **`Failed to load registry` → `Failed to initialize database` (exit 255)** |
| 70-71 | `madenat_lumber_intake` (+ `toll_processing`) | **no evaluable** | nunca se alcanzó (aborta el registro) |

**Causa exacta (log, `logs/v1_install.log`):**

```
Exception: Module loading madenat_lumber_logistics failed:
  file madenat_lumber_logistics/security/ir.model.access.csv could not be processed:
No matching record found for external id 'model_lumber_shipment_rebaja_wizard_line' in field 'Model'
Missing required value for the field 'Model' (model_id)
```

⇒ El commit ④ (FASE 5) commiteó **3 filas de ACL** (`lumber.shipment.rebaja.wizard.line.{oper,jef,ger}`) cuyo
**modelo solo declara `wizards/lumber_shipment_rebaja_wizard.py`**, que quedó **fuera** (D18-2).
Escaneo estático del HEAD: es la **única** incoherencia ACL→modelo del repositorio.

### 1.3 Verificación del arreglo del XML de `shipping_core` (paso 8 de V1) — **VERIFICADO**

* El log carga `madenat_lumber_shipping_core/views/shipping_vessel_views.xml`, `shipping_voyage_views.xml` y
  `shipping_booking_views.xml` **sin errores de parseo**.
* Consulta a la base temporal: `shipping.vessel.form` y `shipping.voyage.form` tienen `<chatter` en `arch_db`
  y **no** contienen `hatter/>` ⇒ el arreglo del commit ③ **funciona desde una instalación limpia**.
* **Hallazgo colateral:** al instalar, `shipping_core` se carga **antes** que `core` (no depende de él) y sus
  vistas referencian grupos `madenat_lumber_core.group_madenat_*` ⇒ `WARNING … The group … does not exist!`
  (2 avisos, no bloqueantes). En un entorno donde `core` **ya** está instalado no aparece.

### 1.4 Resultado — pase 2 (`-i core,intake` con `--test-tags`, misma base temporal recreada)

| Orden | Módulo | ¿Instala? | Evidencia |
|---|---|---|---|
| … | `madenat_lumber_core`, `madenat_ingestion_engine`, `madenat_lumber_purchasing`, `madenat_lumber_reception_improvements`, `madenat_toll_processing` | **SÍ** | todos `loaded` |
| 69/69 | **`madenat_lumber_intake`** | **NO** | `ParseError` en `intake_console_views.xml:7` ⇒ `ValueError: External ID not found in the system: madenat_lumber_intake.action_madenat_lumber_intake_new` ⇒ `Failed to load registry` (exit 255) |

**Causa exacta y carácter pre-existente.** En `madenat_lumber_intake/views/intake_console_views.xml` el
`<button name="%(action_madenat_lumber_intake_new)d" …>` está en la **línea 20** y el `<record
id="action_madenat_lumber_intake_new" model="ir.actions.act_window">` se define en la **línea 1116** del
**mismo archivo**. Odoo procesa los registros de un archivo en orden ⇒ **referencia antes de definición**.
* El archivo **no está modificado** en el WIP: su último commit es `573a164` (2026-10-10) y **ya contiene el
  mismo par referencia/definición en `b1d2d19`** ⇒ **no lo introdujo la FASE 5**.
* Se mantiene **latente** porque en `madenat_test` el registro ya existe: la FASE 5 ejecutó
  `-u … madenat_lumber_intake` **con éxito** (`6 failed + 4 error de 1448`). Sólo se manifiesta al
  **instalar desde cero**.

⇒ **Hallazgo nuevo (pre-existente, fuera del alcance de los commits de FASE 5):** el repositorio **no es
instalable desde cero** para `madenat_lumber_intake`. Impacto directo en **recuperación ante desastres** y en
cualquier alta de base nueva; **no** afecta a una actualización (`-u`) de la base existente.

### 1.5 Contraste de suites (paso 6 de V1)

Como ninguna base limpia puede cargar `logistics` (D18-2) ni `intake` (defecto pre-existente), el contraste se
hizo con **instalación acotada de `madenat_lumber_core`** (`-i … --test-tags=/madenat_lumber_core`) sobre la
misma base temporal. Resultado: **`2 failed + 57 error de 398`** (`logs/v1d_*.log`).

**Interpretación (causa raíz demostrada, una por una):**

| Resultado | Nº | Causa raíz | ¿Nueva vs baseline? |
|---|---|---|---|
| `ERROR` masivos (`TestSvRpcBypass` 13, `TestSvRebaja` 9, `TestSvRename` 6, `TestSvVolumeRegularization` 6, `TestSvOperationLedger` 5, `TestSvEscalationSecurity` 5, `TestSvLotUnlinkGuard` 3, …) | **57** | **`ValueError: Invalid field 'conciliation_status' on model 'madenat.guia.processing'`**: el helper compartido `madenat_lumber_core/tests/sv_test_common.py:66` (`_sv_make_guia`) escribe `conciliation_status`, campo que **aporta `madenat_lumber_intake`** (`intake_console.py:441`, `intake_guia_processing.py:159`). `intake` **no puede instalarse** desde cero ⇒ el helper no funciona ⇒ **artefacto del alcance del pase**, no un defecto del HEAD | **No** (no comparables) |
| `FAIL: TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` | 1 | Falla **preexistente** del baseline | No |
| **`FAIL: TestDuplicateValidation.test_02_duplicate_in_guia_processing`** | 1 | **D18-1**: el test **antiguo** (commiteado) espera `UserError` para un **homónimo entre flujos**, pero el código commiteado en ② cambió la política (identidad por modelo). `test_duplicate_validation.py` **no** usa el helper ⇒ la falla es **genuina e independiente** | **SÍ — única falla nueva atribuible al split de la FASE 5** |

* `TestSvDevCleanupParam.test_02/test_04`, que fallaron en el pase sobre una base **sin** «test» en el nombre,
  **pasan** cuando el nombre contiene «test» ⇒ confirmado el artefacto del gate `_sv_test_enable_strict()`.
* **No fue posible medir** las suites de `logistics` (no carga por D18-2) ni de `intake` (no instala) en un
  HEAD limpio. La referencia válida de esas suites sigue siendo la regresión de la FASE 5 sobre `madenat_test`
  (`6 failed + 4 error de 1448`, **mismo conjunto de 10**).

### 1.6 Conclusión de V1 — **¿es `ed42df5` autosuficiente? → NO**

| Módulo | Instala desde cero | Suites comparables con el baseline | Fallas nuevas |
|---|---|---|---|
| `madenat_lumber_shipping_core` | **SÍ** (y el arreglo `<chatter/>` queda verificado en BD) | — (sin suites propias) | ninguna |
| `madenat_lumber_core` | **SÍ** | **Parcial** (57 errores son artefacto de alcance; helper dependiente de `intake`) | **1** (`TestDuplicateValidation.test_02`, por **D18-1**) |
| `madenat_lumber_logistics` | **NO** — `Failed to load registry` (ACL → modelo de **D18-2**) | **imposible** | — (bloqueo) |
| `madenat_lumber_intake` | **NO** — `ParseError` (orden interno del XML, **pre-existente**) | **imposible** | — (bloqueo) |

⇒ **`ed42df5` requiere el cierre de D18** (D18-1 en `core`; D18-2/3/4/5 en `logistics`) **antes** de poder
desplegarse, y **además** conviene resolver el defecto de orden de `intake` para recuperar la capacidad de
instalación desde cero (DR). El **contenido** entregado no está en duda (la regresión de FASE 5 sobre
`madenat_test` reproduce exactamente el baseline); lo que no está garantizado es la **autosuficiencia del
historial**.


---

## 2. V2 — INVESTIGACIÓN D18 / P2-2 (solo lectura)

Informe completo: **`INFORME_V2_D18_P2-2.md`** (ficha por archivo, con hechos, evidencia y riesgos).
Resumen de hallazgos:

| Ficha | Archivo | Atribución demostrada | Papel en el HEAD limpio | Recomendación |
|---|---|---|---|---|
| D18-1 | `core/tests/test_duplicate_validation.py` | **Sí** — CANON/12 §5.2/§6.2 + parámetro `exclude_model` introducido en el commit ②; mtime 2026-10-07 17:33 (2 min tras `FIX_GUIA_DUP_FINAL`) | Suite que contradice el código entregado (fallaría) | Incluir en cierre de `core` |
| D18-2 | `logistics/wizards/lumber_shipment_rebaja_wizard.py` | **Sí** — CANON/18 §7.3 y §14.1 describen el asistente (incl. `_rebaja_require_group`, resumen EXPORT/NOMINAL/SV, savepoint por contenedor) + `AUDIT_B01_20261004` cita `_classify`; mtime 2026-10-03 23:54 | **BLOQUEANTE** (ACL → modelo inexistente) | Incluir en cierre de `logistics` |
| D18-3 | `.../lumber_shipment_rebaja_wizard_views.xml` | **Sí** (idem D18-2; mtime 2026-10-03 23:55) | UI antigua del asistente | Incluir con D18-2 |
| D18-4 | `logistics/tests/test_rebaja_contenedor.py` | **Parcial** — CANON/18 §14.5 cita `TestRebajaContenedor`; las expectativas nuevas no están documentadas una a una | Suite antigua (coherente con el asistente antiguo) | Incluir con D18-2/3 |
| D18-5 | `logistics/tests/test_service_return_imputation_guard.py` | **Sí** — guard `reversal_reason` commiteado en ④ (AUD-ETQ-02/06, CANON/19); mtime 2026-10-10 21:11 | Ancestral: 2 tests fallarían | Incluir en cierre de `logistics` |
| P2-2 | `reports/views/lumber_reports_menu.xml` | **No demostrada** — «P2-2» solo existe en el comentario del propio cambio (sin CANON, CHANGELOG, commit ni test); mtime 2026-10-03 22:37 | Irrelevante (módulo fuera del despliegue) | **Mantener fuera** hasta que exista AD |

**Hechos adicionales de V2.**
* **El único enlace committed↔excluido con efecto duro** es la ACL de `logistics` (3 filas) → 3 modelos
  transitorios del asistente. Ningún otro archivo commiteado referencia campos/modelos exclusivos de D18
  (escaneo del HEAD: `voyage_available`, `excluded_container_ids`, `_rebuild_lines`, `_scope_containers` = 0
  referencias fuera de los archivos D18).
* **P2-2 es cosmético:** `menu_lumber_reports_root` es una **carpeta vacía** (sin `action` y sin hijos); la
  entrada oficial `madenat_lumber_core.menu_madenat_reports_main` («📊 Reportes y Listados») está commiteada y
  no se toca. `madenat_lumber_reports` depende de `madenat_lumber_costing` (D1 bloqueado).

---

## 3. V3 — RUNBOOK DE DESPLIEGUE AL TEST REMOTO

Entregable completo: **`RUNBOOK_DESPLIEGUE_TEST_REMOTO.md`** (232 líneas). **No se ejecutó nada contra el
remoto.** Contenido:

1. **§0 Hallazgos bloqueantes** (los dos de §1 de este informe) y **§1 Precondiciones** (D18 cerrado, P2-2
   decidido, HEAD verificado, respaldo remoto, ventana, responsables, navegador).
2. **§2 Respaldo previo remoto:** dump `-Fc` + verificación `pg_restore --list`, filestore, código
   (`tar` de los 4 módulos + `rev-parse HEAD`), manifiesto `sha256`. **Sin credenciales ni hosts reales.**
3. **§3 Verificación previa remota (solo lectura):** commit desplegado, versiones de módulos, **búsqueda del
   literal `hatter/>` en las vistas heredadas**, módulos instalados, existencia de `costing`, usuarios de
   prueba, cron.
4. **§4 Entrega del código:** comparación, mecanismo de sincronización, **exclusión explícita** de `costing` y
   del menú de `reports`, verificación por hashes.
5. **§5 Actualización:** `-u madenat_lumber_shipping_core,madenat_lumber_core,madenat_lumber_logistics,madenat_lumber_intake`
   en orden de `depends`, sin `-u all`, `--max-cron-threads=0`, log a archivo y vigía de errores.
   **Aviso expreso: la estrategia debe ser `-u` sobre la base existente (nunca instalación desde cero) por el
   defecto pre-existente de `intake`.**
6. **§6 Migraciones:** tabla con los cambios de ACL/`ir.rule`/versiones y su veredicto «no requiere script».
7. **§7 Humo funcional** (12 puntos: Motonave/Viaje, duplicados, borrado con motivo/rol, escenarios d/e/f/g,
   rebaja y reversa con motivo, rebaja por nave, bitácora APPEND-ONLY, VIEW-01/04 en navegador, menús de
   reportes) con evidencia exigida.
8. **§8 Aborto y reversa:** 6 señales de aborto (incl. *«bitácora con menos filas»*) y plan de reversa
   (código + `pg_restore` + filestore), 10–25 min.
9. **§9 Evidencia posterior** (logs, versiones, conteos, hash del commit) y **§10 lista explícita de lo que NO
   se despliega** · **§11 checklist**.

---

## 4. VALIDACIÓN FINAL (integridad de la FASE 6)

| Comprobación | Resultado |
|---|---|
| `git status` final | **16 entradas** = idénticas a `logs/f6_status_before.txt` |
| HEAD / rama | `ed42df54dab62beea0780337971d3657b4232ac1` / rama sin cambios |
| SHA256 del WIP (16) | **idéntico** a `logs/f6_sha_before.txt` (huella `35e6808f…`) ⇒ **0 archivos modificados** |
| `git stash` | vacío (nunca usado) |
| Base temporal V1 | **eliminada** (`madenat_head_check`, `madenat_head_check_test`) — 0 bases `madenat_head_check*` restantes |
| Clon temporal | **eliminado** en ambos entornos: host (`FASE6_HEAD_CHECK_20261015/clone/`) y contenedor (`/tmp/fase6_clone`). Evidencia conservada en `logs/clone_verification.txt` (HEAD, rama, `status=0`, los 5 commits, huella del listado) |
| `madenat_test` | **sin cambios**: guías 13 · recepciones 8 · usuarios 12 · lotes 151 · bitácora 327 · imputaciones 3 (mismos conteos antes/después; solo hubo consultas `SELECT`) |
| Repo de trabajo | **ningún archivo añadido, modificado ni borrado** (verificado por el manifiesto SHA256) |
| Remoto | **no contactado** (sin `fetch`/`push`/`ls-remote`) |

**Nota metodológica encontrada (útil para repetir esta verificación):** `_sv_test_enable_strict()`
(`madenat_sv_internal.py:185-187`) exige **`'test'` en el nombre de la base** además de `--test-enable`.
Una base temporal cuyo nombre no contenga «test» (p. ej. `madenat_head_check`) produce **~50 errores
espurios** en las suites del ledger/marcador SV (`TestSvOperationLedger`, `TestAuditLogImmutability`,
`TestSvRebaja`, `TestSvLotUnlinkGuard`…). Por eso el pase definitivo se ejecutó sobre
**`madenat_head_check_test`**.

---

## 5. RIESGOS RESIDUALES Y DECISIONES PARA MAURICIO

| # | Asunto | Decisión requerida |
|---|---|---|
| 1 | **D18 (5 archivos)** — bloquea el despliegue (`logistics` no carga) | Cerrar D18 con el commit de cierre (§6) |
| 2 | **P2-2 (menú 📈 Reportes MADENAT)** | ¿Inactivar (con AD) o dejar como está? Mientras: **fuera** |
| 3 | **Orden en `intake_console_views.xml`** (`action_…` definida 1.096 líneas después de su uso) | ¿Se corrige (cambio mínimo de orden) para habilitar instalaciones desde cero / DR? |
| 4 | **`costing` (D1/C2)** sigue bloqueado: no desplegable | Mantener bloqueado |
| 5 | **`test_length_uom_and_subproducto` (4 errores)** `MissingError: product.product(607)` en instalación desde cero (pasa en `madenat_test`) | Investigar dependencia de datos/orden (no lo introdujo la FASE 5) |
| 6 | **VIEW-01/04 en navegador** (chatter OWL) siguen **sin evidencia manual** | Aceptar el riesgo o agendar la comprobación |
| 7 | Trigger/hash de la bitácora · limpieza generalizada de suites con `commit()` (D5) · 10 fallas preexistentes de la regresión (D10) | Pendientes ya conocidos |
| 8 | **Supuesto de una compañía (AD-106)** | Vigente; reabrir si entra una segunda compañía |

---

## 6. PROPUESTA DE COMMITS DE CIERRE (**NO ejecutada**)

> Orden por dependencias. **Ninguno** se ha creado. Sujetos a la decisión de §5.

1. **`fix(core): alinea la prueba de homónimo guía↔recepción con la política por modelo (D18-1)`**
   * `madenat_lumber_core/tests/test_duplicate_validation.py`
   * Cuerpo: renombra `test_02` y ajusta la expectativa (homónimo **no** bloquea; identidad del **mismo
     modelo** sí), citando CANON/12 §5.2/§6.2 y el parámetro `exclude_model` entregado en `0ef4388`.
     *Evidencia:* V1 ⇒ `FAIL: TestDuplicateValidation.test_02_duplicate_in_guia_processing` en el HEAD limpio.

2. **`feat(logistics): asistente de rebaja por nave + adaptación al motivo de reversa (D18)`**
   * `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard.py`
   * `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard_views.xml`
   * `madenat_lumber_logistics/tests/test_rebaja_contenedor.py`
   * `madenat_lumber_logistics/tests/test_service_return_imputation_guard.py`
   * Cuerpo: cierra **D18**; el CSV de ACL ya commiteado (`ded5e89`) **exige**
     `lumber.shipment.rebaja.wizard.line`; diseño documentado en CANON/18 §7.3/§14.1 (referencia a
     `AD-82/AD-83/AD-86` y al expediente `AUDIT_B01_20261004`). *Evidencia:* `Failed to load registry` con
     `No matching record found for external id 'model_lumber_shipment_rebaja_wizard_line'`.
   * **Sugerido además** (opcional, `REQUIERE_DECISIÓN`): subir `version` a **18.0.1.28.0** + entrada de
     CHANGELOG, porque el módulo cambia de comportamiento.

3. **`fix(intake): define la acción «Nuevo Ingreso» antes de la vista que la usa`** *(solo si se aprueba §5-3)*
   * `madenat_lumber_intake/views/intake_console_views.xml` (mover el `<record>` de
     `action_madenat_lumber_intake_new` antes del `<record>` de la vista de consola)
   * Cuerpo: habilita la **instalación desde cero** (hoy imposible en `ed42df5` **y** en `b1d2d19`);
     mitiga el riesgo de DR. *Evidencia:* `ParseError … External ID not found:
     madenat_lumber_intake.action_madenat_lumber_intake_new`.

4. **`docs(canon): AD-107 — cierre de D18, decisión sobre P2-2 y hallazgos de instalación desde cero`**
   * `madenat_lumber_docs/CANON/04_DECISION_LOG.md` (AD-107; versión monótona 12.22.0 → 12.23.0)
   * `madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md` (12.33.0 → 12.34.0)
   * `madenat_lumber_docs/CANON/05_BACKLOG.md` si se decide mantener P2-2 pendiente
   * Cuerpo: registra (a) la atribución documental de D18, (b) el hallazgo de la ACL huérfana, (c) el defecto
     de orden de `intake` y la regla operativa «**desplegar por `-u`, nunca instalar desde cero**», (d) la
     dependencia del nombre de la base en el gate test-only.

5. **`chore(repo)` — commit ⑦ del expediente de auditoría**: sigue sin ejecutarse (el expediente
   `AUDITORIA_INTEGRAL_20261012` está fuera del repo y pesa 177 MB). Decisión aparte.




