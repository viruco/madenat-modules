# INCIDENTE MADENAT — RECUPERACIÓN CÓDIGO ↔ DB

Fecha: 2026-10-03 (UTC) · Incidente: realineación código bind-mount `/mnt/extra-addons` ↔ DB `madenat_test`
Auditoría: `/home/viruco/dev-stack/odoo/odoo-18-ce/incident_recovery_audit/20261003_181143/`

## 1. Identidad inicial y Gate 0 (solo lectura) — PASA
- Worktree vivo: `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (git dir `.git`).
- `git status --short`: VACÍO.
- Rama actual: `feat/p0-r-core-sv-foundation-remediation-20261002`.
- HEAD: `bee61e7ee3b829376e261ea37b3f38a9202f2bbd`.
- Ref destino existe: `feat/guia-correccion-documental-preservada-20261002`.
- `git rev-parse <ref>` = `106d0010ec6cc7924046c50029b95ecd10677896` (short `106d001`) → COINCIDE.
- Sin operación Git en curso: `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REBASE_HEAD`, `revert-merge/HEAD`, `index.lock`, `HEAD.lock` → TODOS ausentes.
- Registrado en `pre_switch.txt`.

## 2. Ref destino, SHA, versiones y modelos verificados (lectura por `git show`/`git grep` en `106d001`)
- core `madenat_lumber_core/__manifest__.py` → `'version': '18.0.6.5.0'`.
- logistics `madenat_lumber_logistics/__manifest__.py` → `'version': '18.0.1.6.0'`.
- Modelos en destino:
  - `madenat_lumber_logistics/models/madenat_sv_imputation.py:53` → `_name = 'madenat.sv.imputation'`
  - `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard.py:13` → `_name = 'lumber.shipment.rebaja.wizard'`
  - `madenat_lumber_logistics/wizards/madenat_processor_shipment_wizard.py:36` → `_name = 'madenat.processor.shipment.wizard'`
- Estado pre-switch (montado, HEAD `bee61e7`): core `18.0.6.3.0`, logistics `18.0.1.2.0`; los 3 modelos AUSENTES (`git grep` vacío).

## 3. Resultado del `git switch`
- Comando único ejecutado: `git switch feat/guia-correccion-documental-preservada-20261002`.
- `switch_exit_code = 0`.
- `git branch --show-current` = `feat/guia-correccion-documental-preservada-20261002`.
- `git rev-parse HEAD` = `106d0010ec6cc7924046c50029b95ecd10677896`.
- `git status --short` tras el switch: VACÍO (árbol limpio).
- Montado ahora: core `18.0.6.5.0`, logistics `18.0.1.6.0`; los 3 modelos presentes.
- Imports verificados: `models/__init__.py:20 → from . import madenat_sv_imputation`; `wizards/__init__.py:4 → lumber_shipment_rebaja_wizard`, `:9 → madenat_processor_shipment_wizard`.
- Registrado en `post_switch.txt`. Ningún archivo editado durante/tras la recarga.

## 4. Evidencia de autoreload (sin actualización de módulos)
`--dev=reload,qweb,werkzeug`; watcher `AutoReload watcher running with watchdog` sobre `/mnt/extra-addons`.
Secuencia tras el switch (UTC):
- `21:12:49,280 odoo.service.server: autoreload: python code updated, autoreload activated`
- `21:12:49,292 Initiating server reload`
- `21:12:55,551 Watching addons folder /mnt/extra-addons`
- `21:13:00,966 AutoReload watcher running with watchdog`
- `21:13:03,817 88 modules loaded in 2.60s, 0 queries (+0 extra)`  ← **0 queries ⇒ sin update de módulos, sin DDL, sin escrituras**
- `21:13:04,122 Modules loaded.` · `21:13:04,163 Registry loaded in 3.194s`
- No se usó `-u/--update/-i/--init`.

## 5. Resultado HTTP y de las cuatro acciones (modo lectura)
- HTTP `GET /web/login`: **200** (antes y después del switch).
- Las tres acciones afectadas (definición XML en `106d001`) resuelven modelos ahora existentes:
  - `action_lumber_shipment_rebaja_wizard` → `lumber.shipment.rebaja.wizard`
  - `action_madenat_processor_shipment_wizard` → `madenat.processor.shipment.wizard`
  - `action_madenat_sv_imputation` → `madenat.sv.imputation`
- `Operaciones → Ingreso de Madera`: acción `madenat.lumber.intake.console` cargada con `HTTP 200` en el cliente (`POST /web/dataset/call_kw/madenat.lumber.intake.console/get_views 200`, 20:58:22) y módulo sin cambios; tras la recarga sin errores.
- Evidencia runtime no invasiva: tras la recarga, `0` ocurrencias de `Missing model`, `0` de `unknown comodel_name` para los 3 modelos y `0` líneas de nivel ERROR ⇒ las tres acciones ya no disparan la pantalla roja por modelo ausente.
- LIMITACIÓN DECLARADA: la apertura interactiva autenticada de los menús no se ejecutó desde el agente porque crear una sesión de login implicaría escribir en DB (`res_users.login_date`) y en el filestore (sesión), expresamente prohibido. La comprobación interactiva read-only queda para la sesión ya autenticada del operador (navegación = solo lectura, sin escrituras).

## 6. `Missing model` / Traceback / `ALTER TABLE … stock_lot` — antes vs después
| Métrica | ANTES | DESPUÉS (tras switch) |
|---|---|---|
| `Missing model` (los 3 modelos) | **3** (`2026-10-03 20:58:09.791` → rebaja.wizard, sv.imputation, processor.shipment.wizard) | **0** |
| `ALTER TABLE` (global) / `stock_lot` | 0 / 0 | 0 / 0 |
| Líneas nivel ERROR/CRITICAL | — | **0** (el único match case-insensitive es el substring de `psycopg2.InterfaceError`) |
| Cabeceras `Traceback` | 568 (histórico acumulado) | **1** benigno: `Exception in thread odoo.service.cron.cron0 … psycopg2.InterfaceError: connection already closed` (cierre de conexión cron durante TODO reload; clase ya presente antes). NO es traceback de carga de módulos. |

- Bloque al final del slice clasificado: `WARNING py.warnings … UserWarning: Field 'madenat.lumber.intake.console.volume_detail_line_ids' … should be searchable`. Es ruido CRÓNICO PRE-EXISTENTE (74,226 ocurrencias relacionadas `is_modifying_relations/_update_bus_presence` y 17,360 `resolve_depends` en el log ANTES), disparado por la presencia websocket del navegador; NO relacionado con los 3 modelos y NO es regresión.

## 7. Confirmación de ausencia de escrituras en DB/filestore
- Recarga con `0 queries (+0 extra)` ⇒ ningún update de módulo, DDL, migración ni escritura de datos de negocio.
- `0` ejecuciones de `ALTER TABLE` en todo el log.
- No se ejecutó SQL, Odoo shell, tests ni migraciones; no se usó `-u/-i`.
- Contenedores NO reiniciados/recreados: `RestartCount=0`, `StartedAt` sin cambios (`2026-10-03T18:38:26Z`).
- Única interacción de red generada por el agente: `GET /web/login` (200), mandatado por el propio procedimiento. Ningún cambio en datos de negocio, tablas, quants ni filestore por parte del agente.

## 8. Estado final de Git y contenedores
- Rama: `feat/guia-correccion-documental-preservada-20261002` · HEAD `106d0010ec6cc7924046c50029b95ecd10677896`.
- `git status --short`: VACÍO · `git stash list`: VACÍO · reflog HEAD@{0} = `checkout: moving from feat/p0-r-core-sv-foundation-remediation-20261002 to feat/guia-correccion-documental-preservada-20261002` (única operación; sin commit/push/reset/rebase/amend/cherry-pick/stash).
- Contenedores: `odoo18_app` Up (StartedAt 2026-10-03T18:38:26Z, RestartCount=0), `odoo18_db` Up (healthy). Sin recreación.
- `GET /web/login` final: **200**.

## 9. Rollback disponible
`git switch feat/p0-r-core-sv-foundation-remediation-20261002` → vuelve a `bee61e7ee3b829376e261ea37b3f38a9202f2bbd` (core 18.0.6.3.0 / logistics 18.0.1.2.0). (No ejecutado; se conserva por instrucción.)

## 10. Dictamen único
**SERVICIO RESTAURADO.**
Código bind-montado realineado con `madenat_test`: core `18.0.6.5.0`, logistics `18.0.1.6.0`, y los tres modelos (`lumber.shipment.rebaja.wizard`, `madenat.processor.shipment.wizard`, `madenat.sv.imputation`) presentes y cargados. Tras el autoreload: `0 Missing model`, `0 ERROR`, `0 ALTER TABLE`, HTTP `/web/login` 200, sin actualización de módulos (`0 queries`), sin reinicio de contenedores y árbol Git limpio.

---
### Evidencia clave (hashes)
- Origen: `bee61e7ee3b829376e261ea37b3f38a9202f2bbd`
- Destino: `106d0010ec6cc7924046c50029b95ecd10677896`
- merge-base: `b862415c5e177a869c38acf574b8cd77b236ab06`
### Artefactos de auditoría
`pre_switch.txt`, `post_switch.txt`, `before_analysis.txt`, `after_analysis.txt`, `analysis_final.txt`, `before_docker_logs.txt`, `after_slice.txt`, `after_slice2.txt`.
