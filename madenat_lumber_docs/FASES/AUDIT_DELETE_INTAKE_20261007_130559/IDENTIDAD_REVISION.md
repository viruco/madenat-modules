# IDENTIDAD DE REVISIÓN Y ENTORNO
Auditoría de eliminación de ingresos desde Intake — MADENAT (Odoo 18 CE)
Fecha/hora de recopilación: **2026-10-07 13:03–13:06 (-03:00)**

## 1. Raíz y control de versiones

| Dato | Valor |
|---|---|
| Ruta del proyecto | `/home/viruco/dev-stack/odoo/odoo-18-ce` |
| ¿Raíz git? | **NO** — `fatal: not a git repository` |
| Raíz git real | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` |
| Rama actual | `feat/guia-correccion-documental-preservada-20261002` |
| Estado HEAD | adjunto a rama (no detached) |
| SHA HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` |
| Commit HEAD | 2026-10-05 21:21:37 -0300 · Mauricio Navarrete · `fix(core): desacopla vista core de contacts` |
| Cambios *staged* | **ninguno** (`git diff --cached --stat` vacío) |
| Cambios *unstaged* | **36 modificados + 3 no rastreados** (ver §2) |

## 2. Estado del árbol de trabajo (working tree)

**Modificados (M)** — 36 archivos: `madenat_lumber_core/models/madenat_audit_log.py`,
`madenat_lumber_core/views/lumber_core_menu.xml`, todo `madenat_lumber_costing/*`
(manifest, `__init__`, cost_distribution, shipment_costing, ACL, views, tests),
`madenat_lumber_docs/CANON/{00_ARQUITECTURA,04_DECISION_LOG,18_CONSOLIDACION_Y_REBAJA}.md`,
`madenat_lumber_docs/WIKI/03_OPERACION/despliegue_modulo.md`,
**`madenat_lumber_intake/views/intake_menus.xml`**, `madenat_lumber_logistics/*`
(container, export_shipment, ACL, tests, views, wizards rebaja/zarpe/rollover, CHANGELOG),
`madenat_lumber_reports/views/lumber_reports_menu.xml`, `madenat_lumber_shipping_core/*`.

**No rastreados (??)**: `madenat_lumber_costing/models/stock_lot_cost_line.py`,
`madenat_lumber_costing/tests/test_shipment_costing_c2.py`,
`madenat_lumber_costing/views/lumber_shipment_costing_views.xml`.

> **Relevancia para esta auditoría:** ninguno de los archivos que participa en la ruta de
> eliminación está *unstaged*. El wizard `intake_guide_lifecycle_wizard.py`, `intake_console.py`,
> `intake_console_sv.py`, `stock_picking.py` y `madenat_guia_processing.py` están
> **tracked-unmodified** (idénticos a HEAD). El único archivo de la ruta con cambios locales es
> `madenat_lumber_intake/views/intake_menus.xml` (solo visibilidad de menús).
> Los `.tar.gz` y los `pre02_*`/`f31_test_*`/`oracle_*`/`IMPL_*` **no** están versionados en este repo.

## 3. Versiones declaradas de los módulos

| Módulo | `version` |
|---|---|
| madenat_lumber_intake | 18.0.0.11.0 |
| madenat_lumber_core | 18.0.6.5.0 |
| madenat_lumber_logistics | 18.0.1.6.0 |
| madenat_lumber_costing | 18.0.1.0.0 |
| madenat_lumber_shipping_core | 18.0.1.0.0 |
| madenat_lumber_reports | 18.0.2.3.0 |
| madenat_toll_processing | 18.0.1.0.0 |
| madenat_lumber_billing | 1.0.0 |


## 4. Entorno Docker

| Contenedor | Imagen | Estado |
|---|---|---|
| `odoo18_app` | tdoo-18-ce-web | **Up** (127.0.0.1:8069→8069) |
| `odoo18_db` | postgres:15 | **Up (healthy)** |
| `odoo18_ui_work` | tdoo-18-ce-web | Exited (255) 4 h |
| `odoo18_level1_val` | tdoo-18-ce-web | Exited (255) 4 h |
| `odoo18_pgadmin` | dpage/pgadmin4 | Exited 13 d |

**Montajes de `odoo18_app`** (bind):
- `/home/viruco/dev-stack/odoo/odoo-18-ce/config` → `/etc/odoo` (rw)
- `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` → `/mnt/extra-addons` (rw)
- volumen `odoo-18-ce_odoo-web-data` → `/var/lib/odoo`

**Comando/parámetros de arranque** (PID 1):
`/usr/bin/python3 /usr/bin/odoo --config /etc/odoo/odoo.conf --database madenat_test --dev=reload,qweb,werkzeug`

**`/etc/odoo/odoo.conf` (saneado — sin secretos):**
```
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
db_name = madenat_test
db_filter = ^madenat_test$
list_db = False
workers = 0
admin_passwd = ***REDACTED***
db_user = odoo
db_password = ***REDACTED***
```
> `custom_addons` del host está **bind-mounteado** en `/mnt/extra-addons`, y ese path es el primer
> `addons_path`. Por construcción, *host == contenedor* para los módulos MADENAT.

## 5. Correspondencia host ↔ contenedor (SHA-256)

| Archivo (relativo) | SHA-256 (host == contenedor) |
|---|---|
| `madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` | `6baa7b84549ffe805f6532a681888702dbc6f222ae74687dd6ce2d43ee93aed9` ✔ |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `b86230d2f3043f82c1ac555d82a2dc683b63a5d74f207deadddbaac36ada3596` ✔ |
| `madenat_lumber_core/models/stock_picking.py` | `744fdc34ecf47a23ec7b014162bb9b8901a42500792863b93ac78f3f667a6368` ✔ |
| `madenat_lumber_intake/models/intake_console_sv.py` | `251f4112a3619f5fca336addeb7223dd1658685029b45791367fb327d2fbbcaa` ✔ |

Todos coinciden (corolario del bind mount). El inventario completo (50 archivos) está en `INVENTARIO.csv`.

## 6. Rutas duplicadas del mismo módulo (riesgo de carga)

Copias de `madenat_lumber_intake` / `madenat_lumber_core` en:
`/tmp/f31_test_20261003_1410`, `/tmp/oracle_f31_20261003_165538`, `/tmp/pre02_test_20261003_1541`,
`/tmp/pre02_postcommit_test_20261003_173746`, `/tmp/madenat_l0a_validation_ct`,
`/tmp/pre02_head_20261003_1541`, y `madenat_lumber_docs/LEGADO/backups_modulos/madenat_lumber_core`.

**Ninguna está en `addons_path`** → **no se cargan**. El único módulo activo es
`/mnt/extra-addons/<módulo>` (== `custom_addons/<módulo>`).

## 7. Límites de evidencia (declarados)

1. **Revisión cargada en memoria:** con `--dev=reload` el intérprete recarga Python al detectar
   cambios, pero **no es verificable qué bytecode exacto está cargado sin reiniciar** el proceso.
   No se reinició (prohibido). Se declara incertidumbre. Evidencia indirecta: hashes host==contenedor
   y proceso con ≈3 h 53 m de antigüedad (archivos sin cambios desde el arranque).
2. **UI real:** no hubo clic auditado; la ruta "Eliminar" estándar y el Modo A se infieren de
   XML/ACL/código (ver `MAPA_ELIMINACION.md`), no de una sesión de navegador.
3. **Datos:** solo lectura, transacción de consulta contra `madenat_test` (caso local confirmado).
