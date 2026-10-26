# ORÁCULO INTEGRAL F3.1 — Cierre PRE-01 / PRE-02

MADENAT / Odoo 18 CE — Dictamen de cierre controlado
Identificador de corrida: `oracle_f31_20261003_165538`
Base de cierre autoritativa: `oracle_f31_cierre_test_20261003_165538`
Fecha: 2026-10-03 (host) · 20:30Z (UTC)

---

## 1. Identidad de Git, hashes completos y aislamiento

Repo: `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`
Rama activa: `feat/p0-r-core-sv-foundation-remediation-20261002`

| Elemento | Valor |
|---|---|
| HEAD | `4aa40113c029fc0a871ae3368e08593bb771774d` |
| HEAD^ (parent) | `1df283e3cff10d6b5dae582183a054ad10958ca2` |
| origin/main | `b862415c5e177a869c38acf574b8cd77b236ab06` |
| merge-base(HEAD, origin/main) | `b862415c5e177a869c38acf574b8cd77b236ab06` |
| Estado vs ref | `[origin/main: ahead 16]` |

Cambios sin commit (`git status --porcelain`), **únicamente** los autorizados:
```
 M madenat_lumber_core/models/madenat_guia_processing.py
 M madenat_lumber_core/tests/test_granel_route.py
```
`git diff --check` → **exit=0** (sin errores de whitespace). `git status` no
reporta archivos untracked. No hay stash.

### Hashes SHA-256 (completos) — coinciden con la validación PRE-02

| Archivo autorizado | SHA-256 | Baseline PRE-02 |
|---|---|---|
| `madenat_lumber_core/models/madenat_guia_processing.py` | `7f8c530b2984ae4adeb288c426b9c48a7869412d7ad7ccacd9dea9b3c0cf517e` | `7f8c530b…0cf517e` ✅ |
| `madenat_lumber_core/tests/test_granel_route.py` | `d05a7d48c2f08a73699941bf616aba49efe8cdd977677af6302d090e37f05e18` | `d05a7d48…e37f05e18` ✅ |

Los mismos hashes se verificaron **dentro de la copia aislada** del addon en el
contenedor (`/tmp/oracle_f31_20261003_165538/…`) antes de arrancar Odoo. Los
hashes **no cambiaron durante la corrida** (verificación final idéntica).

---

## 2. Recursos nuevos creados y no intervención en F3.1 / PRE-02

Recursos NUEVOS (identificador `oracle_f31_<timestamp>`):

| Recurso | Ruta / nombre | Existía antes |
|---|---|---|
| Worktree Git de validación | `/home/viruco/dev-stack/odoo/odoo-18-ce/oracle_f31_20261003_165538` (detached 4aa4011) | NO |
| Copia de addon en contenedor | `/tmp/oracle_f31_20261003_165538` (odoo:odoo) | NO |
| Base 1 (oráculo no-test) | `oracle_f31_20261003_165538` | NO |
| Base 2 (corrección, `test`) | `oracle_f31_test_20261003_165538` | NO |
| Base 3 (CIERRE, `test`) | `oracle_f31_cierre_test_20261003_165538` | NO |
| Filestore 1 | `/var/lib/odoo/filestore/oracle_f31_20261003_165538` | NO |
| Filestore 2 | `/var/lib/odoo/filestore/oracle_f31_test_20261003_165538` | NO |
| Filestore 3 (cierre) | `/var/lib/odoo/filestore/oracle_f31_cierre_test_20261003_165538` | NO |
| Directorio de logs | `/home/viruco/dev-stack/odoo/odoo-18-ce/oracle_f31_audit/20261003_165538` | NO |

Confirmación de **no intervención** en recursos históricos (verificado al cierre):
`f31_test_20261003_1410`, `pre02_test_20261003_1541`, `madenat_test` — sus DB,
filestores, worktrees y copias `/tmp` siguen presentes e intactos. No se
actualizó, borró, restauró ni limpió ningún recurso histórico.

---

## 3. Módulos instalados, DB, filestore, copy-path y contenedores

- **Módulos instalados desde cero** (mínimos): `-i madenat_lumber_core`
  (arrastra dependencias del manifiesto: `stock, product, purchase, sale,
  account, mail, sms`). Instalación limpia sobre base vacía
  (`createdb -T template0`). Resultado: `madenat_lumber_core = installed`, exit=0.
  No se tocó ningún módulo fuera de `madenat_lumber_core` salvo sus dependencias.
- **Base de cierre**: `oracle_f31_cierre_test_20261003_165538`.
- **Filestore**: `/var/lib/odoo/filestore/oracle_f31_cierre_test_20261003_165538` (nuevo).
- **copy-path del addon** (contenedor): `/tmp/oracle_f31_20261003_165538`
  (`--addons-path='/tmp/oracle_f31_20261003_165538,/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons'`).
- **Contenedores utilizados**: únicamente los ya activos `odoo18_app` (web) y
  `odoo18_db` (postgres:15). No se arrancó ni detuvo ningún contenedor nuevo.
- **`--db-filter='^<DB>$'`** explícito por corrida (aislamiento). Sin
  `skip_sanity_check`, sin `sudo()` como bypass de ACL y sin contextos de evasión.

### Nota de integridad de entorno (transparencia)
La infraestructura de pruebas SV documenta una **invariante dura**: el nombre de
la base debe contener `'test'` (`madenat_sv_internal._sv_test_enable_strict()`;
idéntico en `docker-compose.yml`). La corrida se inició con el nombre literal
`oracle_f31_20261003_165538` (sin `test`). Ese hecho, y no un fallo de código,
determinó los resultados intermedios 03 y 06_testdb (ver §8). El **cierre
autoritativo** se obtuvo en bases aisladas NUEVAS que sí contienen `test`
(`oracle_f31_test_…` y, definitivamente, `oracle_f31_cierre_test_…`), siguiendo
la convención ya usada por los recursos históricos `f31_test_…` y `pre02_test_…`.

---

## 4. Matriz de invariantes del oráculo (73 aserciones, todas PASS)

Script ORM reproducible: `oracle_f31_audit/20261003_165538/oracle_f31.py`,
ejecutado vía `odoo shell` como usuario del contenedor (`odoo`), entorno
superusuario solo para **crear** datos y usuarios; las comprobaciones de ACL se
ejecutan con `with_user(<usuario>)` (sin `sudo`). Datos 100 % propios (partner
`OF31 Oracle Partner`, productos `OF31-A/B/C`, compañía activa `env.company`).

| # | Escenario | Datos creados | Aserción | Resultado |
|---|---|---|---|---|
| A1 | 1 línea elegible | Guía `OF31-A1` + línea 18.5 m³ | estado `validated`; **exactamente 1 SV**; `lot_flow_type='volume'`; etiqueta `SV###########`; `volume_source_line_id` 1:1; producto y compañía correctos | PASS (n=1, `SV00000000001`) |
| A2 | 3 líneas elegibles | Guía `OF31-A2` (10.0 / 12.5 / 8.0) | **3 SV**, un producto por línea, 3 líneas-origen distintas, sin cruces | PASS (n=3) |
| A3 | 1 elegible + 1 no elegible | Guía `OF31-A3` | solo la elegible genera SV; aviso trazable "no generaron etiqueta SV" | PASS |
| A4 | 0 líneas elegibles | Guía `OF31-A4` (vol 0) | `ValidationError`; sin lotes; sin firma de auditoría; estado ≠ validated | PASS |
| A5 | Reproceso idempotente | Guía `OF31-A5` + `do_full_processing()` ×2 | misma SV, 1 sola; 1 picking activo antes/después; validación posterior mantiene 1 SV y 1 incoming `done` | PASS |
| B | Identidad y compañía | 6 SV + cruce `OF31-B1`/`OF31-B2` | todas las SV en la compañía de recepción; validar B2 **no altera** nombre/volumen/origen de B1 | PASS |
| C | Inmutabilidad de origen | `OF31-A1` vs `OF31-A2` | `volume_source_guia_id` conservado; reasignar a otra guía → `ValidationError`; 1 línea-origen única por SV, sin duplicados | PASS |
| D | Stock granel → service | `OF31-D1` (granel) + `OF31-D2` (service) | ver §5 | PASS |
| E | Seguridad y auditoría | usuarios `of31_plain_…` / `of31_ops_…` | ver §6 | PASS |
| F | Rebaja / rollback / residuo | SV `OF31-A1` + guía `OF31-R1` | ver §6 | PASS |

---

## 5. Evidencia específica granel → service (invariante 4)

Guía granel `OF31-D1` (10.0 m³) validada y, después, guía service `OF31-D2`
(paso `_create_granel_summary_line(5.0)`, consume 3.0 m³ del lote granel por
`source_lot_line_ids`).

| Elemento | Valor observado |
|---|---|
| Picking incoming granel (`origin=OF31-D1`) | exactamente **1**, `state=done`, compañía `My Company (San Francisco)` |
| Move lines trazables granel | **1** |
| Stock físico granel tras recepción | quant `=10.0 m³` en `WH/Stock` |
| Picking incoming service (`origin=OF31-D2`) | exactamente **1**, `state=done`, compañía correcta |
| Movimientos del service | exactamente **1** (`stock.move`) |
| Move line trazable service | exactamente **1** (`lot_id` presente) |
| Lote de la move line | ∈ `service.lot_ids` (`GRANEL GRANEL 312`) |
| Cantidad procesada | `5.0` (positiva), **coincide** con `line.vol_purchase_m3` (5.0) vía conversión estándar m³ |
| Producto | el de la línea de guía (`MADERA_ASERRADA_SECA`) |
| UoM | `m³`, igual a la UoM del movimiento |
| Ubicaciones | `Partners/Vendors → WH/Stock`, las del picking |
| `button_validate()` | sin `skip_sanity_check` (evidencia estática: el método `action_validate` no incluye ese flag; resultó `done` sin backorder) |
| Idempotencia de recepción | `_ensure_reception_move_lines()` re-ejecutado: mismas move lines (`[55]→[55]`), misma cantidad (5.0), 1 picking, 1 lote — **sin duplicar** |
| Picking de consumo (salida a proceso) | `WH/OUT/00012`, `state=done` |
| Stock granel tras consumo | quant `=7.0 m³` (10.0 − 3.0) |

El flujo granel → service completa la recepción incoming estándar, genera
**exactamente un** move y **una** move line trazable, y la cantidad procesada es
positiva y derivada de la línea de guía.

---

## 6. Evidencia ACL y auditoría, incluyendo usuario/rol y ausencia de bypass

### 6.1 Seguridad (sin rol vs con rol)
Usuario `of31_plain_20261003_165538` (solo `base.group_user`) vs
`of31_ops_20261003_165538` (`base.group_user` + `group_madenat_operaciones`).

| Aserción | Mecanismo | Resultado |
|---|---|---|
| Usuario **sin** rol Operaciones no puede crear una operación SV | `madenat.sv.operation.with_user(plain).create(...)` | `AccessError` (denegado) ✅ |
| Usuario **sin** rol no puede alterar datos protegidos | `lot.with_user(plain).write({'volumen_m3': 1.0})` | `ValidationError` (guarda server-side `_sv_guard_write`) ✅ |
| Usuario **con** rol Operaciones ejecuta el flujo permitido | `with_user(ops).create(...)` + `action_apply()` de rebaja | `state='applied'` ✅ |

No se usó `sudo()` para evadir los controles evaluados: las pruebas de ACL se
ejecutan con `with_user`. El `sudo()` presente en el oráculo es únicamente el de
la app (`action_validate`, `_register_lot_audit`) y el de **setup** (crear
usuarios), nunca para sortear las ACL comprobadas.

### 6.2 Auditoría (`madenat.audit.log`)
| Evento | Verificación | Resultado |
|---|---|---|
| `validation_signature` (guía `OF31-A1`) | `user_id` y `timestamp` presentes; `audit_hash` (64 char) y `audit_snapshot` (228 char) no vacíos | PASS `[(True,True,64,228)]` |
| `lot_creation` (guía `OF31-A1`) | ≥1 registro | PASS |
| `consumption` (guía `OF31-D2`) | ≥1 registro (salida a proceso) | PASS |
| `sv_operation` (rebaja de `OF31-A1`) | ≥1 registro; `user_id` = actor `of31_ops_20261003_165538`; `batch_id` = etiqueta SV | PASS |

Actor, fecha, acción, origen (`guia_processing_id`) y entidad (`batch_id`) son
consistentes con el modelo `madenat.audit.log`.

### 6.3 Rebaja, rollback y residuo
| Aserción | Resultado |
|---|---|
| Rebaja conserva saldo documental: `sv_original_volume_m3` sigue **18.5** (inmutable) | PASS |
| `sv_available_m3` tras rebaja de 3.0 → **15.5** | PASS |
| Operación presente en el historial (`sv_operation_ids`), `state='applied'` | PASS |
| **Rollback** con fallo funcional controlado (service sin origen → `UserError` dentro de savepoint) | `failed=True` |
| Tras el rollback: 0 picking, 0 lote, 0 move, 0 auditoría, 0 quant de esa guía | `{picking:0, lot:0, sv_lot:0, audit:0, move:0}` ✅ |
| Estado de la guía tras el fallo | `verified` (sin efectos parciales) ✅ |
| Residuo por claves funcionales: datos finales válidos presentes y artefactos huérfanos ausentes | `{sv_lots:9, done_incoming:8, audit_signatures:8}` válidos; rollback todo en 0 ✅ |

El oráculo es **transaccional** (revierte al final): no deja datos persistentes
de prueba (verificado post-corrida en la base de cierre: `sv_lots=0`,
`of31_guias=0`, `sv_ops=0`, `audit=0`). Esto evita contaminar la regresión de
cierre que corre después en la misma base.

---

## 7. Resultado exacto de oráculo, regresión 204 y F3.1 13

Base de cierre: `oracle_f31_cierre_test_20261003_165538` (aislada, `test`).

| Etapa | Comando (resumen) | Resultado exacto | exit |
|---|---|---|---|
| 1. Oráculo integral | `odoo shell -d <DB> < oracle_f31.py` | **73 passed / 0 failed** · `ORACLE_RESULT=PASS` | 0 |
| 2. Regresión de cierre | `-u madenat_lumber_core --test-enable --test-tags 'guia_processing,sv,-f31'` | **204 post-tests · 0 failed · 0 error(s)** (17296 queries) | 0 |
| 3. F3.1 | `-u madenat_lumber_core --test-enable --test-tags 'f31'` | **13 post-tests · 0 failed · 0 error(s)** (3783 queries) | 0 |

Los 13 tests F3.1 ejecutados son `TestF31VolumeSvAutoCreate.test_01..test_13`
(T-F3.1-01 a T-F3.1-13). La cifra 204 coincide **exactamente** con el baseline
PRE-02 (mismo número de consultas: 17296).

---

## 8. Diferenciación entre warnings/baselines preexistentes y errores nuevos

**Baselines preexistentes** (idénticos al log de instalación de PRE-02; no son
defectos introducidos por los dos archivos autorizados):
- `WARNING … ir_ui_view: The group "group_madenat_costos/operaciones/gerencia" defined in view does not exist` (grupos definidos en otros addons).
- `WARNING … ir_ui_view: An alert (class alert-*) must have an alert… role` (accesibilidad de vista).
- `WARNING … The models ['madenat.sv.internal.capability','…marker'] have no access rules` (por diseño: modelos internos sin ACL).
- `ERROR … odoo.schema: unable to add constraint 'stock_lot_check_cost_positive' as CHECK(total_cost_usd >= 0)` (condición previa sobre `stock_lot`; baseline PRE-02).
- `ERROR/3`/`WARNING/2` de docutils sobre un docstring (formato RST), no bloqueante.

**Resultados intermedios atribuibles al entorno de nombres (NO fallos de código):**
- `03_regression.log` (base `oracle_f31_20261003_165538`, sin `test`): **202 tests · 2 failed · 1 error**.
  - `TestSvDevCleanupParam.test_02/test_04` → FAIL: dependen de `'test' in dbname`.
  - `TestSvConcurrency.setUpClass` → ERROR: `_sv_test_mark()` exige entorno estricto (`'test' in dbname`); sus 2 tests no se ejecutaron (204−2 = 202).
- `06_regression_testdb.log` (base `oracle_f31_test_…`, con `test`, pero con **datos del oráculo confirmados**): **204 tests · 1 failed · 0 errors**.
  - `TestSvConcurrency.test_01` → FAIL `2 != 1`: su aserción hace una búsqueda **global** de operaciones de rebaja aplicadas y colisiona con la rebaja **persistida** por el oráculo (que en esa corrida aún **confirmaba** transacción).

**Corrección de entorno/de diseño (sin tocar código ni tests):**
1. El oráculo pasó a ser **transaccional** (revierte): no persiste datos de prueba → no contamina la prueba de concurrencia.
2. El cierre se ejecutó en una base NUEVA que cumple la invariante `'test' in dbname`.

**Errores nuevos atribuibles a los dos archivos autorizados: NINGUNO.**
Las tres etapas de cierre quedan en verde (oráculo 73/0, regresión 204/0/0, F3.1 13/0/0).
Sin residuo nuevo: los conteos post-suite en la base de cierre son **idénticos**
a los baselines PRE-02 y F3.1 (`stock_lot=4`, `stock_picking=17` de datos de
instalación; `madenat_sv_operation=0`, `marker=0`).

---

## 9. Recursos preservados, hashes de logs y estado final de contenedores

No se limpió ni eliminó ningún recurso. Persisten:
- Worktree `oracle_f31_20261003_165538` (detached 4aa4011) + copia `/tmp/oracle_f31_20261003_165538`.
- Bases `oracle_f31_20261003_165538`, `oracle_f31_test_20261003_165538`,
  `oracle_f31_cierre_test_20261003_165538` y sus filestores.
- Directorio de evidencia `oracle_f31_audit/20261003_165538/` (script, corridas,
  JSON de resultado, hashes).
- Recursos históricos intactos: `f31_test_20261003_1410`,
  `pre02_test_20261003_1541`, `madenat_test` (DB, filestore, worktree y `/tmp`).

### Hashes SHA-256 de la evidencia principal
| Archivo | SHA-256 |
|---|---|
| `05_oracle_test.log` (oráculo cierre) | `76b7277f274425315d856388e1498a9678e74d73ceff0a8fe86f3c05aef1ee13` |
| `06_regression.log` (regresión 204) | `5f82ce58ded679e6843c6bb7cba5cc4907b0e4e3cfeb4184cfc04181f0aa29ca` |
| `07_f31.log` (F3.1 13) | `bd22b15d953767fab15abeebd9aaac37b65b397ffcb8506638fda9d714be7a9c` |
| `ORACLE_RESULT_closure.json` | `e5e6bd83b21984792dcc2974bd8958b351277732556ec5bd2405601c0ffdf492` |
| `02_oracle.log` (oráculo primer entorno) | `c0de20b66751d31572aeb04b4f8f473ea59879e15fb768f300d84d3d9205347d` |
| `03_regression.log` (intermedio sin `test`) | `cb3faf42f4614482f1cabbcadc02e5755226086ba17b6b6cc31f2e1c296d463a` |
| `06_regression_testdb.log` (intermedio `test`+datos) | `4000ae59f563492c48d0f457615ecf669a4c0e6fab46cfd4450db60609644e61` |
| `oracle_f31.py` (MD5, verificado en contenedor) | `1a7dd56a5dd9a7a085cb7531a669784e` |

### Estado final de contenedores (sin cambios)
- `odoo18_app` → **Up** (imagen `odoo-18-ce-web`).
- `odoo18_db` → **Up (healthy)** (postgres:15).
- No se arrancó ni detuvo ningún contenedor; la única lógica de arranque fue
  `docker exec` de procesos Odoo efímeros (`-i`, `shell`, `--stop-after-init`),
  ya terminados. No quedan procesos de prueba residuales (solo el servidor base).

---

## 10. Dictamen único

# ✅ CIERRE COMPLETO APROBADO

Las tres etapas quedan en verde sobre la base aislada de cierre
`oracle_f31_cierre_test_20261003_165538`:
- **Oráculo integral:** 73/73 PASS (`ORACLE_RESULT=PASS`).
- **Regresión 204:** 204 tests, 0 failed, 0 errors.
- **F3.1 13:** 13 tests, 0 failed, 0 errors.

El artefacto validado es exactamente el previamente probado (hashes SHA-256
idénticos al baseline PRE-02), sin modificación de código ni tests, sin parches,
sin SQL que altere datos, sin `skip_sanity_check`, sin bypass de ACL, sin
reutilizar datos históricos, y sin commits/push/PR/merge/rebase/amend.
Todos los recursos y la evidencia quedan preservados y los contenedores en su
estado original. No hubo errores nuevos atribuibles a los dos archivos
autorizados; los resultados intermedios observados se explican íntegramente por
la invariante de entorno `'test' in dbname` y por la persistencia transitoria de
evidencia del oráculo, ambos resueltos sin tocar el código bajo validación.

*Estado previo obligatorio — reproducido:* PRE-02 focalizado 1 test, `TestGranelRouteCore` 14 tests, regresión `guia_processing,sv,-f31` 204 tests y F3.1 13 tests quedan cubiertos y en verde en el cierre; HEAD `4aa40113c029fc0a871ae3368e08593bb771774d` sin cambios.


