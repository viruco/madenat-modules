# PRE-02 / F3.1 — Formalización Local y Validación Post-Commit

MADENAT / Odoo 18 CE
Timestamp de formalización: `20261003_173553` (host) · 2026-10-03T20:35Z (UTC)
Repo git: `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`
Nota de rutas: el workspace NO es el repositorio; el repo root es `custom_addons`.
Las rutas del encargo `custom_addons/madenat_lumber_core/...` se resuelven como
rutas repo-relativas `madenat_lumber_core/...`.

---

## 1. Identidad inicial, HEAD base, rama y estado de Git

| Elemento | Valor |
|---|---|
| Rama actual | `feat/p0-r-core-sv-foundation-remediation-20261002` |
| HEAD (base autorizado) | `4aa40113c029fc0a871ae3368e08593bb771774d` — *fix(core): completa recepción service y fixtures* |
| HEAD^ (parent de la base) | `1df283e3cff10d6b5dae582183a054ad10958ca2` |
| origin/main | `b862415c5e177a869c38acf574b8cd77b236ab06` |
| merge-base(HEAD, origin/main) | `b862415c5e177a869c38acf574b8cd77b236ab06` |

- HEAD coincide **exactamente** con el base autorizado.
- `git status --short` inicial:
  ```
   M madenat_lumber_core/models/madenat_guia_processing.py
   M madenat_lumber_core/tests/test_granel_route.py
  ```
- Exactamente los 2 archivos autorizados. **Sin staged, sin untracked, sin submódulos** (sin `.gitmodules`).
- `git diff --check` → **exit=0** (sin errores de whitespace).
- `git diff --stat` → 2 files changed, **193 insertions(+), 56 deletions(-)**.
- `git diff --name-only` → los 2 archivos autorizados.

---

## 2. Integridad del informe y hashes del working tree / staged

- Informe de cierre `FASES/oracle_f31_audit/20261003_165538/INFORME_FINAL_F31.md`
  SHA-256 = `ea9a37f365364b481f915a966049e8fe551c37d96f1015297cb351b897d41e41` → **COINCIDE**.

| Archivo | SHA-256 working tree | SHA-256 staged (`git show :path`) | Baseline autorizado |
|---|---|---|---|
| `madenat_lumber_core/models/madenat_guia_processing.py` | `7f8c530b2984ae4adeb288c426b9c48a7869412d7ad7ccacd9dea9b3c0cf517e` | idéntico | `7f8c530b…0cf517e` ✅ |
| `madenat_lumber_core/tests/test_granel_route.py` | `d05a7d48c2f08a73699941bf616aba49efe8cdd977677af6302d090e37f05e18` | idéntico | `d05a7d48…e37f05e18` ✅ |

El diff de working tree es **byte-idéntico** al diff validado por el Oráculo
Integral F3.1 (`preflight_model.diff` ≡ `/tmp/pre02_model.diff`;
`preflight_test.diff` ≡ `/tmp/pre02_test.diff`).

Índice tras el stage restringido (`git diff --cached`):
- `--name-only`: los 2 archivos autorizados.
- `--stat`: 193 insertions / 56 deletions (idéntico al working tree).
- `--check`: exit=0.
- Working tree restante: vacío (sin cambios adicionales).

---

## 3. Diff revisado: archivos, líneas y verificación de ausencia de hardcode/bypass

Archivos y magnitud:
- `madenat_lumber_core/models/madenat_guia_processing.py` → 174 líneas (±).
- `madenat_lumber_core/tests/test_granel_route.py` → 75 líneas (±).
- Total: **193 insertions(+), 56 deletions(-)**.

Escaneo de patrones prohibidos sobre las **líneas añadidas** del diff:

| Patrón | Ocurrencias |
|---|---|
| `skip_sanity_check` | 0 |
| `cr.execute` (SQL directo) | 0 |
| `INSERT/UPDATE/DELETE/SELECT` | 0 |
| `sudo(` / `.sudo()` | 0 |
| `env.ref(...)` | 1 → `self.env.ref('uom.product_uom_cubic_meter')` (UoM **estándar** de Odoo, no fixture) |

Verificación de la lógica (coincide con el propósito autorizado):
- **FASE A** ahora determina trazabilidad por las move lines reales:
  `tiene_lote = any(line.lot_id for line in move.move_line_ids)` → elimina el
  `stock.move` fantasma que sobrevivía por el campo calculado `move.lot_ids`.
- **FASE C.1 (PRE-02)** delega en `_ensure_reception_move_lines()`:
  - `_reception_source_line(lot)` resuelve la línea de guía por vínculo directo
    (`volume_source_line_id`), luego por producto, luego por volumen real.
  - `_reception_line_quantity(lot, uom)` deriva la cantidad con la precedencia
    efectiva `vol_purchase_m3 → vol_physical_m3 → vol_shipment_m3` (fallback
    trazable al lote solo si la línea no aporta) y convierte con
    `m3._compute_quantity(qty_m3, uom, round=False)` (conversión UoM estándar).
  - Reutiliza la move line existente del lote (idempotente) y solo crea una si
    faltase, tomando producto/lote/ubicaciones/compañía del propio
    movimiento/picking (nunca valores fijos).
- **Prueba**: `test_08_integracion_granel_luego_service` cubre granel → service,
  trazabilidad (1 move line con lote), cantidad derivada de la línea, UoM,
  ubicaciones, compañía e **idempotencia** (`_ensure_reception_move_lines` re-ejecutado).
- No hay IDs fijos ni cantidades, productos, lotes, ubicaciones o compañías
  codificados para el fixture. No se introducen contextos de evasión de ACL.

---

## 4. Commit local: SHA, parent, mensaje, archivos y estado Git

Comando: `git commit -F pre02_formalization_audit/20261003_173553/commit_message.txt`
(sin `--amend`, sin `--no-verify`; sin hooks activos).

| Campo | Valor |
|---|---|
| Nuevo SHA | `bee61e7ee3b829376e261ea37b3f38a9202f2bbd` |
| Parent | `4aa40113c029fc0a871ae3368e08593bb771774d` → **COINCIDE** con el base autorizado |
| Archivos incluidos | exactamente los 2 autorizados |
| Estado `git status --short` | **vacío** (árbol limpio) |
| `git diff HEAD` | vacío |
| origin/main | `b862415c5e177a869c38acf574b8cd77b236ab06` (sin cambios → sin push) |
| Rama | `feat/p0-r-…` ahora `[origin/main: ahead 17]` (era ahead 16) |

Mensaje completo del commit:
```
fix(core): garantiza cantidades reales en recepción service

Corrige PRE-02 en el flujo granel → service.

- Elimina movimientos fantasma detectando lotes desde move lines reales.
- Garantiza una move line trazable con cantidad derivada de la guía y UoM
  estándar antes de la validación nativa del picking.
- Mantiene idempotencia y evita bypass de validación de stock.
- Añade cobertura de regresión para granel → service, trazabilidad e
  idempotencia.

Validación previa:
- Oráculo integral F3.1: 73 passed, 0 failed.
- Regresión guia_processing,sv,-f31: 204 tests, 0 failed, 0 errors.
- F3.1: 13 tests, 0 failed, 0 errors.

Evidencia:
oracle_f31_audit/20261003_165538/INFORME_FINAL_F31.md
SHA-256: ea9a37f365364b481f915a966049e8fe551c37d96f1015297cb351b897d41e41
```

**GATE 2: VERDE** (parent correcto, 2 archivos, mensaje exacto; sin amend/reset/rebase/cherry-pick/retry).

---

## 5. Recursos post-commit creados, aislamiento e históricos preservados

Identificador: `pre02_postcommit_test_20261003_173746` (`test` incluido → cumple
la invariante `'test' in dbname` de la infraestructura SV).

| Recurso | Ruta / nombre | Existía antes |
|---|---|---|
| Base de datos | `pre02_postcommit_test_20261003_173746` | NO |
| Filestore | `/var/lib/odoo/filestore/pre02_postcommit_test_20261003_173746` | NO |
| Copia de addon (contenedor) | `/tmp/pre02_postcommit_test_20261003_173746` (odoo:odoo) | NO |
| Copia de addon (host) | `/home/viruco/dev-stack/odoo/odoo-18-ce/pre02_postcommit_test_20261003_173746` | NO |
| Logs | `pre02_formalization_audit/20261003_173553/postcommit/` | NO |

- La copia del addon se extrajo **desde el commit recién creado**
  (`git archive bee61e7 | tar -x`), no desde el working tree. Hashes de ambos
  archivos en la copia = mismos que el commit y que el baseline autorizado.
- Instalación limpia desde cero (`createdb -T template0` + `-i madenat_lumber_core`),
  exit=0, `madenat_lumber_core = installed`.

Recursos históricos **preservados** (no tocados): `madenat_test`,
`f31_test_20261003_1410`, `pre02_test_20261003_1541` (DB, filestore, worktrees,
copias `/tmp`) y los recursos del Oráculo F3.1. No se limpió ni eliminó nada.

---

## 6. Matriz de pruebas post-commit

Base: `pre02_postcommit_test_20261003_173746`. Orden obligatorio a → b → c → d.

| Etapa | Comando (`--test-tags`) | Tests | failed | errors | exit | wall |
|---|---|---|---|---|---|---|
| (a) focalizado | `/madenat_lumber_core:TestGranelRouteCore.test_08_integracion_granel_luego_service` | **1** | 0 | 0 | 0 | 33s |
| (b) clase granel | `/madenat_lumber_core:TestGranelRouteCore` | **14** | 0 | 0 | 0 | 39s |
| (c) regresión | `guia_processing,sv,-f31` | **204** | 0 | 0 | 0 | 77s |
| (d) F3.1 | `f31` | **13** | 0 | 0 | 0 | 42s |

Resúmenes exactos (`odoo.tests.result`):
- (a) `0 failed, 0 error(s) of 1 tests`
- (b) `0 failed, 0 error(s) of 14 tests`
- (c) `0 failed, 0 error(s) of 204 tests`
- (d) `0 failed, 0 error(s) of 13 tests`

Conteos de residuo post-suite idénticos a los baselines (solo datos de
instalación): `stock_lot=4`, `stock_picking=17`, `madenat_sv_operation=0`,
`madenat_sv_internal_marker=0`.

**Gates de pruebas: VERDE** — las cuatro etapas con `0 failed` y `0 errors`.

---

## 7. Errores nuevos vs baselines documentados

Baselines documentados antes del post-commit (idénticos al informe/registros
del Oráculo F3.1 y al log de instalación de PRE-02):
- `odoo.schema: unable to add constraint 'stock_lot_check_cost_positive' …` (condición previa sobre `stock_lot`).
- `WARNING … ir_ui_view: The group "group_madenat_costos/operaciones/gerencia" … does not exist`.
- `WARNING … The models ['madenat.sv.internal.capability','…marker'] have no access rules` (modelos internos por diseño).
- Errores **esperados de pruebas negativas** (capturados/aseridos): `null value in column "reason"` (rebaja/rename sin motivo), `could not serialize access due to concurrent update` y `could not obtain lock on row in relation "stock_lot"` (concurrencia SV), `Simulated integrity failure inside savepoint` (rollback de moves huérfanos).

Scan por etapa: `a_test08`, `b_class` y `d_f31` → **0 CRITICAL, 0 Traceback, 0 FAIL, 0 ERROR**. `c_regression` → 0 CRITICAL, 0 Traceback, 0 FAIL; 4 líneas `ERROR` repartidas en las firmas baseline anteriores.

Prueba de no-regresión: se extrajo el conjunto de **firmas de error normalizadas**
(se neutralizan timestamp/PID/IDs y el nombre de la base) de `c_regression.log`
y del log de referencia del Oráculo `oracle_f31_audit/.../06_regression.log`
(0 failed/0 errors). Resultado: **conjuntos IDÉNTICOS** (10 firmas cada uno,
`comm -13` vacío). **No hay errores nuevos** atribuibles al commit.

---

## 8. Estado de contenedores al inicio y fin

| Contenedor | Inicio | Fin |
|---|---|---|
| `odoo18_app` | Up | **Up** |
| `odoo18_db` | Up (healthy) | **Up (healthy)** |

No se reinició, recreó, borró ni alteró ningún contenedor. Los únicos procesos
lanzados fueron `docker exec` de Odoo efímeros (`-i`, `--stop-after-init`), ya
finalizados. No quedan procesos de prueba residuales.

---

## 9. Inventario de evidencia conservada y hashes

Directorio raíz: `pre02_formalization_audit/20261003_173553/`

| Archivo | SHA-256 |
|---|---|
| `00_preflight.txt` | `6c1cc53a71e3c120a1ae549698956c08bbda92e0811044563178b52d27c348cd` |
| `preflight_model.diff` | `c181a328532e20607e0d728a77652b119f379f2240fa0b1f2a9d8e97ebca04a9` |
| `preflight_test.diff` | `ff731d203dc641e70ec7db8a3dc959082b0e8e652f8114d97b892e203fe430d1` |
| `index_cached.diff` | `26dd456c867525809d497bf88f26e2099444debb77865db13f0036d70a0a784a` |
| `commit_message.txt` | `7599dd378d91026173e022b238e3cf6817b8d6f405abe28c0689d303feb9a569` |
| `commit_show.txt` | `dfeeb90654414c5d0e29c581c85db5abf29046790010edc416de8fef5397559b` |
| `postcommit/install.log` | `a17d90daae2686dc050184187260881871dee2fae84b34cfb1777bcad6adb6da` |
| `postcommit/a_test08.log` | `e33e327748986db51ce04ca4f2e9e75043e08caefb8297e3faf909b8dae6100f` |
| `postcommit/b_class.log` | `e1f2ca08e44a44c3e11f9fa73a11df3815dfd98c5d9b4fa2b87cdd8099c4ec61` |
| `postcommit/c_regression.log` | `86465ce2dec004974fabe608c8677dd920e3e2ce1bac9024221ec076246dd0f2` |
| `postcommit/d_f31.log` | `dcb01c085f00ba89e7868b579ca62ed6135aba57bfe8ce251f768334a3dfcbe0` |
| `postcommit/err_base.DBnorm.txt` / `err_postcommit.DBnorm.txt` | firmas de error (idénticas) |

Recursos conservados (no limpiados): base/filestore/copia host y contenedor
`pre02_postcommit_test_20261003_173746`; recursos del Oráculo F3.1; recursos
históricos `madenat_test`, `f31_test_20261003_1410`, `pre02_test_20261003_1541`.

---

## 10. Dictamen único

# ✅ COMMIT LOCAL VALIDADO — LISTO PARA REVISIÓN/PR

- Commit local atómico `bee61e7ee3b829376e261ea37b3f38a9202f2bbd`, parent
  `4aa40113c029fc0a871ae3368e08593bb771774d`, exactamente los **2 archivos
  autorizados**, working tree limpio, sin push ni operación remota.
- Artefacto idéntico al previamente validado por el Oráculo Integral F3.1
  (hashes SHA-256 coincidentes).
- Validación post-commit aislada sobre `pre02_postcommit_test_20261003_173746`
  instalada **desde el commit**: (a) 1/0/0, (b) 14/0/0, (c) 204/0/0, (d) 13/0/0.
- **Sin errores nuevos** (firmas de error idénticas a la referencia).
- Recursos preservados; contenedores en su estado inicial
  (`odoo18_app` Up, `odoo18_db` Up/healthy).

---

### Restricción final
Al completar este informe, **se detiene** y se espera una autorización separada
para cualquier PR, push, revisión remota, merge o limpieza de recursos. No se
ejecutó ninguna operación remota ni de limpieza.
