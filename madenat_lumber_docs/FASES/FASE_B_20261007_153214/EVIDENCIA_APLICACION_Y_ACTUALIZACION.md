# EVIDENCIA — Aplicación del parche y actualización (Fase B)

## 1. Revalidación previa (idéntica a lo auditado)

- Raíz Git: `custom_addons`; rama `feat/guia-correccion-documental-preservada-20261002`.
- HEAD (antes): `e302c488321c276af7e07f1abeecc8bc261a89f4`.
- Archivos objetivo: `tracked-unmodified` (sin cambios locales).
- `git stash list`: vacío.

Hashes SHA-256 (antes):
```
6baa7b84549ffe805f6532a681888702dbc6f222ae74687dd6ce2d43ee93aed9  madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py
b86230d2f3043f82c1ac555d82a2dc683b63a5d74f207deadddbaac36ada3596  madenat_lumber_core/models/madenat_guia_processing.py
5a11e3de13f5aa99ba36a432fd2ae6a3b871cfd23acbb25cf1ba7eb250a9143d  madenat_lumber_intake/views/intake_guide_lifecycle_wizard_views.xml
3361a28c6b15243502f217cd91a215b806e0b30b317eb2377ca7eebb99b7f46f  madenat_lumber_intake/tests/__init__.py
```

## 2. Aplicación (desde la raíz Git, `-p1`)

Orden y códigos de salida (`git apply --check` + `git apply`), todos `=0`:

| Paso | Diff | check | apply |
|---|---|---|---|
| 1 | `patch/02_preventive_return_fk.diff` | 0 | 0 |
| 2 | `patch/03_modo_b_selection.diff` | 0 | 0 |
| 3 | `patch/01_delete_attribution.diff` | 0 | 0 |

Warnings cosméticos de `git apply` (línea en blanco al EOF en 01), sin efecto.

## 3. Hashes resultantes == artefacto probado

| Archivo | SHA-256 después | ¿== workcopy probado? |
|---|---|---|
| `intake_guide_lifecycle_wizard.py` | `b632d79db784225a16894186e77f2963baf3a5ea5316d7e8ad8fffffe65eea9c` | ✔ |
| `madenat_guia_processing.py` | `5d69049256522f5014098aa57e4273acf43bcc29496153feb594987bd9496ae2` | ✔ |
| `intake_guide_lifecycle_wizard_views.xml` | `f2360106c9534daef756df1462adbb03fd2e419ccd9701e7c90f5eb90cb3d46b` | ✔ |
| `tests/__init__.py` | `ba5b8d34c7db11407f1a221d56503d866de6f85ed020e6aeed8732c768d435f7` | ✔ |

Tests nuevos presentes: `test_guide_lifecycle_delete_attribution.py`, `test_guide_lifecycle_phase2.py`.

## 4. Actualización de módulos

Proceso controlado (contenedor one-shot `madenat_phaseb_update`, red
`odoo-18-ce_internal_backend`, `--max-cron-threads=0 --workers=0 --stop-after-init
--no-http`), con `odoo18_app` **detenido** (sin otro Odoo sobre `madenat_test`).

```
odoo -u madenat_lumber_core,madenat_lumber_intake -d madenat_test ...
```

Resultado: `Modules loaded.` · `Registry loaded in 29.584s` · **0 ERROR/CRITICAL/Traceback** (log: `update.log`).

Post-condición (registro):

| Módulo | state | latest_version | write_date (UTC) |
|---|---|---|---|
| madenat_lumber_core | installed | 18.0.6.5.0 | 2026-10-07 18:36:54 |
| madenat_lumber_intake | installed | 18.0.0.11.0 | 2026-10-07 18:37:03 |

- Campo `attribution_notes` registrado (id 20664, `ttype=text`).
- Vista `madenat.lumber.intake.guide.lifecycle.form` (id 2069) referencia `attribution_notes`.

## 5. Servicio normal

`docker start odoo18_app` → Up; `Registry loaded in 2.893s`; `HTTP /web/login = 200`.
Errores atribuibles a la intervención: **0** (los errores del historial son de Oct 4/6 y
uno de las 18:33 UTC durante el apagado previo).
