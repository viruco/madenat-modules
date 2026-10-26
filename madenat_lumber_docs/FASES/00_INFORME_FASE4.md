# FASE 4 — CIERRE SEGURO (informe de ejecución)

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Rama:** `fase13-2a-lectura`
**Estado:** nada borrado, nada movido a cuarentena, nada empujado al remoto.
Este documento no autoriza nada: registra la evidencia de los 7 puntos encargados.

| # | Punto | Resultado | Estado |
|---|---|---|---|
| 1 | Respaldo externo | `origin` correcto; **el repositorio es PÚBLICO**; `fase13-2a-lectura` **no existe** en el remoto; respaldo 1.163.365.900 B (1,1 GiB, 95 archivos) | Sin push; **respaldo movido a `G:` y verificado 95/95** (2026-10-26) |
| 2 | Carpetas ambiguas | `config` = **dependencia viva** (excluida); `postgresql.conf` = vacía (apta); `appointment_crm` = shim no cargable (apta con reserva) | Decidido con evidencia |
| 3 | `run_regression.sh:11` | Diff con `${MADENAT_LOG_DIR:-…}`; `bash -n` OK y prueba funcional con `docker` simulado | **Sin aplicar** (espera OK) |
| 4 | `conciliation_status` | **No hay deriva de esquema**: es una etiqueta de test faltante; reproducido y propuesto el arreglo mínimo | **Sin aplicar** |
| 5 | `.clinerules` | §6 añadida y «Cierre» renumerado a §7; copia previa con sha256 | **Aplicado** (fuera de git) |
| 6 | Cuarentena | Script `FASES/00_CUARENTENA_20261026.py` con dry-run, verificación, guarda de montaje y reversión | Sin ejecutar (92/0/2) |
| 7 | Punteros a artefactos | 26 citas → 16 artefactos, 16/16 localizados en su `.tar.gz`; `FASES/00_INDICE_FASES.md` §4 | Aplicado |

---

## 1. Respaldo externo (solo lectura)

**Remoto configurado.**

```
$ git remote -v
origin  git@github.com:viruco/madenat-modules.git (fetch)
origin  git@github.com:viruco/madenat-modules.git (push)
```

**`git ls-remote --heads origin` no se pudo completar por SSH:**

```
ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory
git@github.com: Permission denied (publickey).
```

Causa exacta [VERIFICADO — `ssh -T` con cada clave]:

| Clave | Resultado |
|---|---|
| `~/.ssh/id_ed25519_viruco` (la que usa `~/.ssh/config` para `github.com`) | `Permission denied (publickey)` |
| `~/.ssh/id_ed25519` | `Hi viruco-sys! You've successfully authenticated` |

Es decir: el `git push` por SSH fallaría en este entorno, y la única clave que autentica pertenece a **otra
cuenta** (`viruco-sys`). `gh` sí está autenticado como `viruco` con protocolo **https**
[VERIFICADO — `gh auth status`].

**¿Existe `fase13-2a-lectura` en el remoto? NO.**

| Comprobación | Resultado |
|---|---|
| `GET /repos/viruco/madenat-modules/branches/fase13-2a-lectura` (anónimo) | `404` |
| `gh api …/branches/fase13-2a-lectura` (token del propietario) | `Branch not found (HTTP 404)` |
| Ramas remotas existentes (4) | `main` `b862415`, `feature/intake-volume-routing` `b862415` (misma punta), `feat/guia-correccion-documental-preservada-20261002` `e302c48`, `feat/p0-r-core-sv-foundation-remediation-20261002` `bee61e7` |
| Referencias remotas cacheadas en el clon | solo `origin/main` y `origin/feat/guia-correccion…` |

**¿El repositorio es privado? NO — es PÚBLICO.**

```
$ curl -s -o /dev/null -w '%{http_code}' https://api.github.com/repos/viruco/madenat-modules
200
$ gh api repos/viruco/madenat-modules --jq '{private,visibility,default_branch,size,pushed_at}'
{"private":false,"visibility":"public","default_branch":"main","size":3668,"pushed_at":"2026-10-06T00:24:44Z"}
```

[VERIFICADO — API anónima devuelve `200` y el token del propietario confirma `private:false`,
`visibility:public`; además `main` **no** tiene protección de rama (`Branch not protected`, 404).]

> **Hallazgo que exige decisión del usuario (no se ha tocado nada).** Un `git push` a `origin` publica
> `git@github.com:viruco/madenat-modules.git` en Internet, sin revisión obligatoria y sin protección de `main`.
> Hoy el remoto está en `b862415` (2026-10-06), 3.668 KB y 4 ramas; la rama de trabajo `fase13-2a-lectura`
> (`9017b3f`) no está publicada. Antes de empujar conviene decidir: pasar el repositorio a privado, o empujar
> a un remoto privado distinto, o aceptar la publicación expresa.

**Tamaño del respaldo.**

| Métrica | Valor |
|---|---|
| Ruta | `/mnt/g/madenat_respaldos/consolidacion_20261026/` (= `G:\madenat_respaldos\consolidacion_20261026\`) |
| Ruta original (hasta 2026-10-26) | `/home/viruco/dev-stack/backups/consolidacion_20261026/` — eliminada tras verificar la copia |
| `du -sb` | **1.163.365.900 B** (1,1 GiB) |
| `du -sh` | `1.1G` |
| Entradas | **95** (94 `.tar.gz` de carpetas + 1 bundle del repo) |
| Espacio libre en `/` | 926 G disponibles (sin presión) |

**Movido a disco externo (2026-10-26, después del cierre de esta fase).** La carpeta completa se copió a
`/mnt/g/madenat_respaldos/consolidacion_20261026/` (= `G:\madenat_respaldos\consolidacion_20261026\`; unidad
`G:` «DEV», ST500LM030 SATA HDD, disco físico distinto del sistema y del disco virtual de WSL) con
`rsync -a --checksum --partial`: **EXIT=0**, 95 archivos creados, **0 borrados**, 1.163.365.900 B transferidos
(62,9 MB/s). Verificación en destino: **95/95** archivos con el mismo tamaño en bytes y el mismo `sha256` que
`FASE13_20261023/evidencias/SHA256_BACKUPS_CONSOLIDACION.csv`; `git bundle verify` = «records a complete
history» (56 refs); 3 `.tar.gz` al azar con `tar -tzf` OK; nombres idénticos origen/destino; **0 diferencias**.
Solo entonces se eliminó el origen (`rm -r`, EXIT=0) y en su lugar quedó
`~/dev-stack/backups/LEEME_RESPALDO_MOVIDO.txt` con la ruta nueva, la fecha, los 95 archivos y las
instrucciones de restauración (`rsync`, `robocopy`, `tar -xzf`, `git clone` del bundle).

> **Dependencia del montaje.** `/mnt/g` es la unidad `G:` de Windows montada por 9p: **si el disco no está
> montado, esa ruta no existe** y toda verificación de los `.tar.gz` falla. `00_CUARENTENA_20261026.py` lo
> comprueba al arrancar (`respaldo_montado`) y **aborta sin mover nada** si `G:` no está montado. Antes de un
> `--ejecutar`, confirmar: `ls /mnt/g/madenat_respaldos/consolidacion_20261026 | wc -l` → **95**.

---

## 2. Las tres carpetas ambiguas (solo lectura)

| Carpeta | Contenido real | mtime | Decisión |
|---|---|---|---|
| `config/` | 1 archivo, `odoo.conf`, **517 B** | 2026-05-18 19:21 | **EXCLUIDA — dependencia viva** |
| `postgresql.conf/` | **vacía** (0 archivos, 0 B, solo el directorio) | 2025-12-26 14:00 | **APTA** (Tanda A) |
| `appointment_crm/` | 2 archivos, `__init__.py` (0 B) + `__manifest__.py` (257 B) | 2025-12-26 23:10 | **APTA con reserva** (Tanda A) |

### 2.1 `config/` — dependencia viva, excluida

**Contenido** (`sha256 79b3847461a0b0e6db5fde2c55d1eb798e28ed938d236b2df2ba316101885235`; resumen fiel de
las 517 B, no una transcripción literal): un
`odoo.conf` de 517 B con `addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons`,
`db_name = madenat_test`, `db_filter = ^madenat_test$`, `list_db = False`, `workers = 0`,
`max_cron_threads = 1`, límites de memoria (`2684354560`/`1610612736`), `db_host = db`, `db_port = 5432`,
`db_user = odoo`, `db_password = odoo`, `log_level = info`, `logfile = False`.

**Quién la usa** [VERIFICADO por cuatro vías independientes]:

1. `docker-compose.yml:17` → `- ./config:/etc/odoo` (bind mount del **directorio**, con el comentario del FIX
   2026-08-15 que explica por qué no se monta el archivo suelto).
2. `docker-compose.yml` → `command: --config /etc/odoo/odoo.conf --database madenat_test --dev=reload,qweb,werkzeug`.
3. `docker inspect odoo18_app` → `/home/viruco/dev-stack/odoo/odoo-18-ce/config -> /etc/odoo (bind, rw=true)`.
4. Dentro del contenedor, `/proc/self/mountinfo` muestra el mismo bind, y
   `sha256sum /etc/odoo/odoo.conf` = `79b3847…` = **idéntico** al del host.

**Conclusión:** `config/` **no es una carpeta de fase**: es la configuración viva del stack. Moverla o borrarla
deja al contenedor sin `odoo.conf` (deja de arrancar o pierde `addons_path`, `db_filter` y credenciales).
**Excluida de toda tanda.** El script de cuarentena la bloquea de forma fija (`EXCLUIDAS_FIJAS`), no por
configuración opcional.

> **Corrección a la FASE 3.** La fila B35 de `00_PROPUESTA_BORRADO_C2.md` decía «contiene `odoo.conf`
> históricos, no la config viva (`/home/viruco/dev-stack/odoo/odoo-18-ce/config/`)». Esa frase **se
> contradecía**: la ruta que citaba como «viva» es exactamente la carpeta listada para borrar. La medición
> de FASE 4 la desmiente; `config/` sale de la Tanda B.

### 2.2 `postgresql.conf/` — carpeta de fase vacía, apta

**Contenido exacto:** ninguno. `find postgresql.conf` devuelve solo el directorio; `du -sb` = 0; el `.tar.gz`
de D7 contiene una única entrada de directorio (`postgresql.conf/`). Inodo 1435, mtime 2025-12-26 14:00.

**Quién la usa:** **nadie**. Se buscó en:

| Comprobación | Resultado |
|---|---|
| `grep -rn 'postgresql\.conf'` en `odoo-18-ce` (`*.py`, `*.sh`, `*.yml`, `*.conf`, `*.md`, `*.sql`, sin `.git` ni `backups/`) | 2 coincidencias, **ambas en los documentos de consolidación** (`00_PROPUESTA_BORRADO_C2.md`, `00_INDICE_FASES.md`) |
| `docker-compose.yml` | no aparece; el servicio `db` es `postgres:15` con volumen `odoo-db-data:/var/lib/postgresql/data` |
| `docker inspect odoo18_app` / `odoo18_db` | ningún montaje apunta a esta carpeta |
| `crontab -l` | solo una tarea de `wordpress`, ajena |
| `/etc/systemd/system`, `~/.config/systemd` | ninguna unidad menciona `odoo-18-ce` |

**Conclusión:** resto de un `psql`/`docker cp` mal dirigido (el nombre es un archivo de configuración, no una
carpeta). Cero bytes, cero dependencias, cero citas. **Apta.**

### 2.3 `appointment_crm/` — shim no cargable, apta con reserva

**Contenido exacto:** `__init__.py` vacío y `__manifest__.py` de 257 B: name «Appointment CRM Bridge (Legacy
Support)», version `18.0.1.0.0`, category `Hidden`, summary «Módulo fantasma para compatibilidad con Odoo 18»,
`depends: ['crm']`, `installable: True`, `auto_install: False`.

**Quién la usa** [VERIFICADO]:

| Comprobación | Resultado |
|---|---|
| `addons_path` efectivo dentro del contenedor | `/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons` → **no incluye la raíz de `odoo-18-ce`** |
| `grep 'appointment_crm'` en `*.py`/`*.xml`/`*.csv` de `custom_addons` | 0 coincidencias fuera de los CSV de consolidación |
| `ir_module_module` en `madenat_test` | no existe la fila `appointment_crm`; solo `appointment` (`uninstallable`, addon estándar de Odoo) |
| Montajes de contenedor | ninguno |

**Conclusión:** es un módulo fantasma creado a mano que **hoy no puede cargarse** (no está en `addons_path`,
ningún manifiesto lo declara como dependencia y no está registrado en la base). No es dependencia viva.
Se clasifica **apta**, con la reserva de que su propósito declarado («compatibilidad») es intencional: si el
usuario prefiere máxima cautela, el script permite `--excluir appointment_crm` sin tocar código.

---

## 3. `run_regression.sh:11` — propuesta sin aplicar

**Diff propuesto** (`madenat_lumber_core/scripts/run_regression.sh`, una línea):

```diff
@@ -8,7 +8,7 @@
 set -e

 TS=$(date +%Y%m%d_%H%M%S)
-LOG_DIR="/home/viruco/dev-stack/odoo/odoo-18-ce/FASE12_REQUERIMIENTOS_OPERACIONES_20261017/logs"
+LOG_DIR="${MADENAT_LOG_DIR:-/home/viruco/dev-stack/logs/regression}"
 mkdir -p "$LOG_DIR"
 LOG_FILE="${LOG_DIR}/regresion_7_modulos_${TS}.log"
 EXIT_FILE="${LOG_DIR}/regresion_7_modulos_${TS}.exit"
```

**Sintaxis:** `bash -n` sobre el original → `OK`; sobre el propuesto → `OK` (`shellcheck` no está instalado).

**Prueba funcional** (no ejecuta Odoo: se intercepta `docker` con un shim en `/tmp/shim/docker` que registra
los argumentos y devuelve el código pedido):

| Caso | Comando | Resultado |
|---|---|---|
| A. Ruta por defecto | `bash run_regression_propuesto.sh` | `Destino log: /home/viruco/dev-stack/logs/regression/regresion_7_modulos_20261026_184834.log`; crea `.log` (38 B) y `.exit` (`0`); `rc=0` |
| B. Override | `MADENAT_LOG_DIR=/tmp/f4_logs/override bash run_regression_propuesto.sh` | escribe en `/tmp/f4_logs/override/`; `.log` + `.exit`; `rc=0` |
| C. Fallo simulado | `SHIM_RC=3 … bash run_regression_propuesto.sh` | `rc=3` y **solo** el `.log`: el `.exit` **no** se escribe |

**Hallazgo adicional (bug preexistente, no corregido).** En el caso C se ve que `RET=$?` (línea 27) es código
muerto: con `set -e`, si `docker exec` devuelve distinto de cero el script aborta antes de escribir
`$EXIT_FILE`. El `.exit` solo existe en ejecuciones exitosas. Arreglo opcional, en un hunk aparte **no aplicado**:
envolver la llamada con `set +e` / `set -e` alrededor de `docker exec … > "$LOG_FILE" 2>&1`.

**Estado:** ninguno de los dos hunks está aplicado; el archivo del repo conserva `LOG_DIR` apuntando a
`FASE12_REQUERIMIENTOS_OPERACIONES_20261017/logs`. Los artefactos de la prueba se crearon en `/tmp` y el
directorio `/home/viruco/dev-stack/logs/regression` que dejó el caso A se eliminó después.

---

## 4. `conciliation_status` — origen, reproducción y corrección mínima

### 4.1 Lo que hay hoy en la base y en el código

| Fuente | Valor |
|---|---|
| `information_schema.columns` (`madenat_test`, `madenat_guia_processing`) | `conciliation_status character varying`, `is_nullable = NO`, `column_default = NULL` |
| `ir_model_fields` (id 17297, modelo `madenat.guia.processing`) | `ttype = selection`, `required = t`, `state = base` |
| Código (`madenat_lumber_intake/models/intake_guia_processing.py:159`) | `fields.Selection([...], string='Estado de conciliación', default='not_compared', required=True, …)` |
| Datos | 13 guías, todas con `conciliation_status = 'not_compared'` |
| Versiones | `madenat_lumber_intake 18.0.0.22.0` instalada = versión del manifiesto actual |

**La columna es coherente con el campo**: `required=True` ⇒ `NOT NULL`; el default es de ORM (`'not_compared'`),
no de base. No falta ni sobra nada en el esquema.

### 4.2 Historia del campo (`git log -S` / `-G` / `log -p`)

| Hecho | Commit | Fecha | Versión del módulo |
|---|---|---|---|
| Se **crea** el campo (con `default='not_compared', required=True`) | `cdf2ea8` (y `230ee73`, misma tanda) | 2026-10-01 | `18.0.0.11.0` |
| Se **consume** en el asistente (`_conciliate_documents`) y en el wizard (`'conciliation_status': …`) | `cdf2ea8` / `ed42df5` | 2026-10-01 / 2026-10-15 | `18.0.0.11.0` / `18.0.0.15.0` |
| Campo **nunca eliminado**: sigue en `intake_guia_processing.py` y en `intake_console.py` | — | — | — |

**Cómo se buscó.** `git log --all -G'^[[:space:]]*conciliation_status[[:space:]]*='` devuelve exactamente los dos
commits de creación. Dos pickaxes anteriores dieron **falsos positivos**: `-S'conciliation_status = fields'`
también casa con `reconciliation_status = fields` (subcadena) y `-S'conciliation_status'` casa con todos los
usos del campo homónimo de la consola; además, el `grep` inicial en el árbol de trabajo estaba truncado a 20
líneas y por eso pareció que el campo había desaparecido del código.

### 4.3 Reproducción sobre copia, con rollback

Copia lógica `madenat_f4_probe` (`pg_dump -Fc` + `pg_restore`: 615 tablas, 88 módulos, 13 guías, `rc=0`),
`odoo shell -d madenat_f4_probe --no-http`, todo con `env.cr.rollback()` y base eliminada después:

```
1) CAMPO_EN_EL_REGISTRO=True required=True default=<lambda>
2) CREADA id=101153 conciliation_status=not_compared
3) CAMPO_QUITADO_DEL_REGISTRO=True (simula la fase at_install)
4) ERROR_TIPO=psycopg2.errors.NotNullViolation
4) ERROR_TEXTO=null value in column "conciliation_status" of relation
   "madenat_guia_processing" violates not-null constraint
```

**Lectura.** Con el registro completo, una guía de Procesado **se crea hoy sin problema** (paso 2: el default
`not_compared` entra solo). El error aparece **solo** cuando el campo no está en el registro (paso 3), que es
exactamente la situación de la fase `at_install`: el módulo `madenat_lumber_intake` —el que aporta el campo y
su default— **todavía no está cargado** cuando corren los tests `at_install` de `madenat_lumber_core`.

### 4.4 Causa raíz de los 8 rojos

Los dos archivos que fallan **no llevan `@tagged`**, así que Odoo les aplica las etiquetas por defecto
(`standard`, `at_install`):

| Archivo | Test | Etiqueta |
|---|---|---|
| `madenat_lumber_core/tests/test_h5_nominal_width_and_stock_notice.py` | `test_01`…`test_06` (6 errores) | sin `@tagged` |
| `madenat_lumber_core/tests/test_resolve_export_width_api.py` | `test_14` (`create({'name': 'GUIA-TEST-OVERRIDE'})`, línea 339) | sin `@tagged` |

Los otros **48** archivos de test de `madenat_lumber_core` ya declaran `post_install`, y el propio repo documenta
el motivo en `test_lumber_reception.py:15-22`: «con `at_install` … los módulos que dependen de
`madenat_lumber_core` (p. ej. `madenat_lumber_intake`, que aporta el campo requerido `conciliation_status`)
todavía no están cargados ⇒ NotNullViolation al crear una Guía».

### 4.5 Corrección mínima propuesta (NO aplicada)

Añadir la etiqueta a las dos clases (una línea por archivo, sin tocar lógica ni datos):

```diff
+from odoo.tests import tagged
+
+@tagged('post_install', '-at_install', 'madenat')
 class TestH5NominalWidthAndStockNotice(TransactionCase):
```

```diff
+@tagged('post_install', '-at_install', 'madenat')
 class TestResolveExportWidthAPI(TransactionCase):
```

**Lo que NO hace falta:** migración, `ALTER TABLE … DROP NOT NULL`, default en base ni restaurar el campo (nunca
se eliminó). Ejecutar `-u` no cambiaría nada: el esquema ya coincide con el código.

**Riesgo latente del mismo tipo:** otros archivos de test de core usan `madenat.guia.processing` sin
`post_install` (`test_double_rounding_j2.py`, `test_ingestion_gate.py`, `test_pre_deploy_health_check.py`,
`test_visual_dimension_l3.py`, `test_volume_labels_6c.py`). Hoy no fallan porque no crean guías en
`at_install`; conviene revisarlos en el mismo commit si se autoriza el arreglo.

---

## 5. `.clinerules` — diff aplicado

**Copia previa** (fuera del repo, junto a los respaldos de D7):

```
/home/viruco/dev-stack/backups/clinerules_20261026/madenat-regla-de-oro.md.pre-20261026
sha256 f9b9b3426ff00bc4771ff2c3828cbaf32a2600a18a590ff6a534279a9dc1c2c1   ← idéntico al original en sitio
SHA256SUMS del directorio con esa misma huella
```

**Diff aplicado** (1 hunk; `git diff --no-index` entre la copia y el archivo en sitio):

```diff
@@ -39,7 +39,21 @@
 4. Levantar web y comprobar **HTTP 200** en `/web/login`.
 5. Comparar datos antes/después (md5 y conteos); solo registros **nuevos** pueden diferir.

-## 6. Cierre
+## 6. Documentación consolidada (FASE 13/2 y FASE 2)
+
+- **Una sola ubicación.** Toda la documentación vive en `custom_addons/madenat_lumber_docs/`. Prohibido crear
+  carpetas de fase (expedientes, auditorías, `FIX_*`, `APPLY_*`, `UAT_*`, `FASE*_*`) en la raíz del stack, en
+  `custom_addons/` ni en `backups/`: van a `madenat_lumber_docs/FASES/<CARPETA>/`.
+- **Rutas de destino.** `CANON/` para lo normativo vigente, `WIKI/` para guías y operación, `RAW/` para
+  insumos y auditorías sin dueño canónico, `FASES/` para expedientes de fase. `LEGADO/` es solo lectura.
+- **Citar siempre el nombre completo.** `CANON/20_AUDITORIA_XML_IDS.md`, nunca `CANON/20`, `CANON/05` ni «el
+  20»; igual con `RAW/…`, `WIKI/…` y `FASES/<CARPETA>/…`. Una cita ambigua se corrige al escribirla.
+- **Enlaces que se verifican.** Antes de cerrar un paso: 0 enlaces Markdown rotos y 0 rutas en backticks que
+  resuelvan solo en la raíz del stack (salvo rutas de módulos dentro de `custom_addons/`).
+- **Originales de la raíz.** No se borran hasta que el expediente esté consolidado, comprimido y verificado con
+  sha256; el borrado requiere autorización expresa y se hace por tandas.
+
+## 7. Cierre
```

**Verificación:** el archivo pasa de 6 a **7 secciones** (`## 1`…`## 7`), ninguna regla previa cambió;
`sha256` resultante `8f642a59ba0ab155f77511a747aaeedd093873499d7c37b64a8a3953b8025cc8`.

**No genera commit:** `.clinerules/` vive en la raíz de `odoo-18-ce`, fuera del repositorio de módulos
(`custom_addons/.git`). `git status --porcelain` sigue mostrando solo los 3 archivos ajenos de
`madenat_lumber_costing/` que ya estaban antes de esta fase.

---

## 6. Cuarentena — script preparado, dry-run ejecutado

**Archivo:** `madenat_lumber_docs/FASES/00_CUARENTENA_20261026.py` (456 líneas, `python3 -m py_compile` OK).

**Antes de empezar** comprueba que el disco del respaldo esté montado (`respaldo_montado`): si `/mnt/g` no es
un punto de montaje —o no existe la carpeta de respaldos— sale con `rc=2` **sin listar ni mover nada**. Es la
guarda que impide que la verificación del `.tar.gz` se apoye en una ruta vacía.

**Qué hace, por carpeta, antes de mover nada** (si una condición falla, la carpeta se bloquea y el script
**no mueve ninguna**: fail-closed):

1. El `.tar.gz` de D7 existe, no está vacío y su **sha256 coincide** con `SHA256_BACKUPS_CONSOLIDACION.csv`.
2. El contenido del `.tar.gz` coincide con el original: se comparan **conjunto de rutas relativas y bytes**
   (`tarfile` vs `os.walk`), y se contrasta el conteo/bytes contra el CSV de D7.
3. Ningún proceso del host tiene `cwd`, `exe` o descriptores dentro de la carpeta (`/proc/*/{cwd,exe,fd}`).
4. La carpeta **no es origen de un bind mount** de ningún contenedor (`docker ps` + `docker inspect .Mounts`
   de todos los contenedores; es la comprobación que detecta `config/`).

**Movimiento:** `os.rename` al mismo sistema de archivos (no copia, no borra) a
`/home/viruco/dev-stack/odoo/odoo-18-ce/PENDIENTE_BORRADO_20261026/` (carpeta **visible**, sin punto inicial). Por
cada carpeta se escribe una línea en `_diario.jsonl` con origen, destino, fecha, archivos, bytes, `sha256` del
manifiesto de rutas, `.tar.gz` y su sha256.

**Reversión:** `--revertir [--ejecutar]` recorre el diario en orden inverso, **recalcula el manifiesto** de la
carpeta en cuarentena, lo compara con el registrado, comprueba que el origen esté libre y hace `os.rename` de
vuelta. Si algo no coincide, bloquea esa carpeta y no la mueve.

**Protecciones fijas en el código:** `config` (bind mount vivo) nunca se mueve; `FASE12_…` queda *postergada*
hasta que se aplique el fix de `run_regression.sh`; `--excluir` permite sacar cualquier otra.

**Dry-run ejecutado** (`python3 00_CUARENTENA_20261026.py --tanda AB --workers 4`, salida completa en
`FASES/00_DRY_RUN_CUARENTENA_F4.txt`):

```
==============================================================================
CUARENTENA (DRY-RUN) — tanda AB — 94 candidatas
Origen : /home/viruco/dev-stack/odoo/odoo-18-ce
Destino: /home/viruco/dev-stack/odoo/odoo-18-ce/PENDIENTE_BORRADO_20261026
Respaldo: /mnt/g/madenat_respaldos/consolidacion_20261026
Montajes de contenedor considerados: 4
==============================================================================
[  1] APTA       FIX_GUIA_DUP_FINAL_20261007_171740              12323 arch.       99.9 MB  .tar.gz OK
...
[ 92] APTA       AUDIT_B01_20261004                                  1 arch.        0.0 MB  .tar.gz OK
------------------------------------------------------------------------------
[ -- ] EXCLUIDA   FASE12_REQUERIMIENTOS_OPERACIONES_20261017    postergada: run_regression.sh:11 escribe sus logs aquí (fix propuesto, no aplicado); moverla haría que el script recree la carpeta en la ruta vieja
[ -- ] EXCLUIDA   config                                        dependencia viva: bind mount ./config -> /etc/odoo en docker-compose.yml y --config /etc/odoo/odoo.conf en odoo18_app
------------------------------------------------------------------------------
Aptas: 92 (1441.5 MB) | Bloqueadas: 0 | Excluidas: 2 | Listadas: 94

DRY-RUN: no se movió nada. Para ejecutar: --ejecutar --tanda AB
```

**Resultado:** 92 aptas (1.441,5 MB), **0 bloqueadas**, 2 excluidas — idéntico al dry-run previo al renombrado
y al movimiento del respaldo. Ninguna carpeta se movió: el script está en modo simulación y no existe
`PENDIENTE_BORRADO_20261026/`.

---

## 7. Punteros a artefactos fuera de git (26 citas → 16 artefactos)

De las reescrituras de E8, **26 citas en 13 documentos** conservan un artefacto no versionado con la fórmula
«(artefacto `X` en `Y/`, fuera de git)». Se comprobó con `tar -tzf` que **los 16 artefactos distintos están
dentro de su `.tar.gz`** (rutas y bytes, 16/16).

| Carpeta de fase | Artefacto | `.tar.gz` de D7 | Citas |
|---|---|---|---|
| `APPLY_AB_UI_20261008/` | `logs/tests_directed_madenat_test_20261008_093825.log` | `APPLY_AB_UI_20261008.tar.gz` | 3 |
| `APPLY_AB_UI_20261008/` | `logs/update_modules_20261008_093223.log` | `APPLY_AB_UI_20261008.tar.gz` | 2 |
| `APPLY_BUSQUEDA_INTAKE_20261007/` | `backup/madenat_test_pre.dump` | `APPLY_BUSQUEDA_INTAKE_20261007.tar.gz` | 2 |
| `AUDIT_REBAJA_ETIQUETAS_20261011/` | `evidence/concurrency_probe.py` | `AUDIT_REBAJA_ETIQUETAS_20261011.tar.gz` | 2 |
| `BACKUP_AB_APPLY_20261008/` | `db/madenat_test_20261008_092958.dump` | `BACKUP_AB_APPLY_20261008.tar.gz` | 4 |
| `BLINDAJE_REBAJA_LOCAL_20261012/` | `logs/regression.log` | `BLINDAJE_REBAJA_LOCAL_20261012.tar.gz` | 3 |
| `BLINDAJE_REBAJA_LOCAL_20261012/` | `logs/regression_logistics.log` | `BLINDAJE_REBAJA_LOCAL_20261012.tar.gz` | 1 |
| `CIERRE_PENDIENTES_20261010/` | `db/madenat_test_pre_20261010.dump` | `CIERRE_PENDIENTES_20261010.tar.gz` | 1 |
| `CIERRE_PENDIENTES_20261010/` | `logs/tests_intake_20261010.log` | `CIERRE_PENDIENTES_20261010.tar.gz` | 1 |
| `CONTRATO_APLICACION_20261011/` | `evidence/POL_contrato_tests_draft.py` | `CONTRATO_APLICACION_20261011.tar.gz` | 1 |
| `CONTRATO_APLICACION_20261011/` | `logs_pol.log` | `CONTRATO_APLICACION_20261011.tar.gz` | 1 |
| `IMPL_SERVICE_RETURN_20261006/` | `logs/iso_run4.log` | `IMPL_SERVICE_RETURN_20261006.tar.gz` | 1 |
| `IMPL_SERVICE_RETURN_AB_20261007/` | `logs/gate_run2.log` | `IMPL_SERVICE_RETURN_AB_20261007.tar.gz` | 1 |
| `SIMPLE_REBAJA_20261011/` | `logs/regression.log` | `SIMPLE_REBAJA_20261011.tar.gz` | 1 |
| `UI_SAVE_REBAJA_20261011/` | `logs/regression.log` | `UI_SAVE_REBAJA_20261011.tar.gz` | 1 |
| `oracle_f31_audit/` | `20261003_165538/oracle_f31.py` | `oracle_f31_audit.tar.gz` | 1 |

**Dónde quedó registrado:**

- `madenat_lumber_docs/FASES/00_INDICE_FASES.md` **§4** (nueva, versión 1.2.0): tabla carpeta → artefacto →
  `.tar.gz`, para que el artefacto sea localizable sin abrir 94 respaldos.
- `madenat_lumber_docs/FASES/00_PUNTEROS_ARTEFACTOS_F4.csv`: las **26** filas con `documento`, `carpeta`,
  `artefacto` y ruta completa del `.tar.gz`.
- Ruta de los respaldos: `/mnt/g/madenat_respaldos/consolidacion_20261026/<CARPETA>.tar.gz` (la del CSV de D7,
  `~/dev-stack/backups/consolidacion_20261026/`, quedó obsoleta al mover el respaldo el 2026-10-26; el CSV **no**
  se modificó).

Las 12 carpetas afectadas pertenecen todas a la Tanda B y todas conservan su `.tar.gz` verificado en D7, así que
la cita sigue siendo trazable después de la cuarentena.

---

## 8. Correcciones a la FASE 3 (declaradas)

1. **R-E8-1 «deriva de esquema» queda refutado.** El campo `conciliation_status` **nunca se eliminó del
   código**: está en `madenat_lumber_intake/models/intake_guia_processing.py:159` con `required=True` y
   `default='not_compared'`, y la columna `NOT NULL` es lo que corresponde. Los 7 errores vienen de tests
   `at_install` que crean guías antes de que `madenat_lumber_intake` esté cargado. El arreglo es una etiqueta
   de test, no una migración. (§4.)
2. **`config/` no es una carpeta de fase.** La fila B35 decía a la vez que `config/` era histórico y que la
   config viva estaba en esa misma ruta. Es la config viva (bind mount + `--config`), y queda **excluida**. (§2.1.)
3. **El recuento de Tanda A/B no cambia** (59 + 35), pero el número de carpetas realmente ejecutables baja a
   **92**: 93 sin `config` menos `FASE12_…` (postergada por el fix pendiente de `run_regression.sh`).
4. **`postgresql.conf/` está vacía** (0 B), no es un archivo de configuración ni contiene copias: el respaldo
   `.tar.gz` guarda solo la entrada de directorio.

---

## 9. Estado al cierre y pendientes

**No ejecutado (por instrucción):** borrado definitivo, `mv` real a cuarentena, `git push`, diff del skip de
xlsx (D6), fix de `run_regression.sh`, corrección de `conciliation_status`.

**Servicios y datos:** `madenat_test` intacta (13 guías, 88 módulos); `odoo18_app` y `odoo18_db` en marcha;
las 94 carpetas originales siguen en la raíz; no queda ninguna base temporal (`madenat_f4_probe` eliminada).

**Pendiente de autorización, en este orden:**

| # | Acción | Requiere |
|---|---|---|
| 1 | Decidir visibilidad del repositorio (hoy **público**) antes de cualquier `push` | Decisión del usuario |
| 2 | ~~Indicar destino de la copia externa~~ → **hecho el 2026-10-26**: movida a `/mnt/g/madenat_respaldos/consolidacion_20261026/` (unidad `G:`) y verificada 95/95. Queda decidir si además se duplica a un **medio USB extraíble** | Decisión del usuario |
| 3 | Aplicar el diff de `run_regression.sh` (punto 3) en commit aparte | OK explícito |
| 4 | Aplicar `@tagged('post_install', …)` en los 2 archivos de test (punto 4.5) | OK explícito |
| 5 | Ejecutar la cuarentena (`--ejecutar --tanda A`, luego `--tanda B`) | Orden explícita |
| 6 | Aplicar el diff del skip de xlsx (D6) | OK explícito |

