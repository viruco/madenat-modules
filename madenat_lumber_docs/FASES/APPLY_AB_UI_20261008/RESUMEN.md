# APPLY_AB_UI_20261008 — Implementación A/B + reorganización de UI en `madenat_test` (2026-10-08)

**Destino real:** `http://localhost:8069/` · base **`madenat_test`** · contenedor `odoo18_app` ·
addons `custom_addons` → `/mnt/extra-addons` · PostgreSQL `odoo18_db`.
**Sin** bases, contenedores ni ramas nuevas. **Sin** commit ni push.

## 1. Artefacto aplicado

| Elemento | Valor |
|---|---|
| Fuente | `IMPL_SERVICE_RETURN_AB_20261007/patch/AB_completo.diff` |
| SHA-256 A / B / AB | `3d5115e9…`, `5d23ea02…`, `a4131812…` (checkpoint verificado) |
| Archivos | 15 (12 modificados + 3 nuevos) — **byte a byte** = workcopy (`IDENTICAL=15 MISMATCH=0`) |
| Aplicación | `patch -p1` **una sola vez**; copias `.pre_ab_20261008` movidas a `BACKUP_AB_APPLY_20261008/pre_patch_files/` |

## 2. Módulos y archivos modificados

- `madenat_lumber_core`: `models/madenat_guia_processing.py`, `views/guia_processing_views.xml`,
  `views/guia_processing_list_search.xml`
- `madenat_lumber_intake`: `models/intake_console.py`, `views/intake_console_views.xml` **(+ reorganización UI)**,
  `views/intake_guia_processing_facade_views.xml`, `tests/__init__.py`,
  `tests/test_service_return_confirmation.py` (nuevo)
- `madenat_lumber_logistics`: `models/madenat_sv_imputation.py`, `views/madenat_sv_imputation_views.xml`,
  `tests/__init__.py`, `tests/test_service_return_pending_filter.py` (nuevo),
  `tests/test_service_return_imputation_guard.py` (nuevo), `tests/test_sv_imputation_i2.py`,
  `tests/test_sv_imputation_candidates.py`
- Documentación: `madenat_lumber_docs/CANON/{02_CONTINUIDAD,03_TESTS,05_BACKLOG,INDICE_DOCUMENTACION}.md`

## 3. Comandos de actualización y resultado

```
# A/B (servicio detenido durante el cambio de esquema)
docker run --rm --name ab_update_20261008 --network odoo-18-ce_internal_backend \
  -v <root>/custom_addons:/mnt/extra-addons -v <root>/config:/etc/odoo \
  -v odoo-18-ce_odoo-web-data:/var/lib/odoo -e HOST=db -e USER=odoo -e PASSWORD=*** \
  odoo-18-ce-web:latest --config /etc/odoo/odoo.conf -d madenat_test \
  -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics \
  --stop-after-init --no-http --max-cron-threads=0
# => Modules loaded. | 0 ERROR | 0 CRITICAL

# UI
docker run --rm --name ab_update_ui_20261008 ... -u madenat_lumber_intake --stop-after-init --no-http
# => Modules loaded. | 0 ERROR | 0 CRITICAL
```

Logs: `logs/update_modules_20261008_093223.log`, `logs/update_ui_20261008_093651.log`.

## 4. Pruebas

| Corrida | Resultado | Log |
|---|---|---|
| Dirigidas del gate **sobre `madenat_test`** (8 clases) | **`0 failed, 0 error(s) of 88 tests`** | `logs/tests_directed_madenat_test_20261008_093825.log` |
| Gate histórico 88/88 (2026-10-07, base aislada) | Antecedente conservado | `IMPL_SERVICE_RETURN_AB_20261007/logs/gate_run2.log` |
| 9 fallas preexistentes | Idénticas sin el cambio | `logs/iso_full_run1.log`, `logs/base_targeted.log` |
| Regresiones nuevas | **0** | — |

## 5. Retiro del aislamiento temporal

- Dumps previos: `retired/db/{srvretab_gate,srvretab_base,srvretab_test}_20261007.dump` (~11,4 MB, `rc=0`).
- Temporales copiados: `retired/tmp/` (`iso_hashes.txt`, `iso_missing*.txt`, `att_all.txt`, `ab_dryrun/`).
- Eliminados: contenedor `srvretab_web` (liberó :8070), volumen `srvretab_web_data`, bases
  `srvretab_gate_20261007` / `srvretab_base_20261007` / `srvretab_test_20261007`,
  `/tmp/gate`, `/tmp/ab_dryrun`, `/tmp/iso_hashes.txt`, `/tmp/iso_missing*.txt`.
- **Límite:** `/tmp/gate` era un directorio **vacío** de `root`; no se pudo eliminar sin contraseña de
  `sudo` (desaparece al reiniciar el host).
- Verificado al cierre: 8069 **HTTP 200**, `madenat_test` accesible, **8070 cerrado**, 0 bases `srvretab%`.

## 6. Respaldo / recuperación

`BACKUP_AB_APPLY_20261008/`: `code/custom_addons_full_*` (25 MB, con `.git`),
`code/custom_addons_local_changes_antes.patch`, `code/git_status_antes.txt`, `code/HEAD.txt`,
`db/madenat_test_*.dump` (11,3 MB, TOC 13.325), `filestore/odoo-web-data_*.tar.gz` (109 MB),
`config/config_*/odoo.conf`, `pre_patch_files/`.

Procedimiento: `IMPL_SERVICE_RETURN_AB_20261007/docs/PLAN_APLICACION_REVERSION.md` §Reversión.

## 7. V3 (navegador) — PENDIENTE

No ejecutada (sin navegador disponible). **No** se afirma completada. Guion actualizado a 8069 /
`madenat_test`: `IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`.
Verificación estructural read-only sí ejecutada (resumen 2 columnas; **un** encabezado «Evidencia
documental»; `col="3"`; orden `resumen → botón → radio → evidencia → packing`).
