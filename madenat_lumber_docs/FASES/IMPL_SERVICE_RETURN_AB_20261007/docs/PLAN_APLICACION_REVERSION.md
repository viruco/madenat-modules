# PLAN DE APLICACIÓN Y REVERSIÓN — A/B Retorno de servicio (2026-10-07)

## Base de referencia

- Rama: `feat/guia-correccion-documental-preservada-20261002`
- **HEAD:** `e302c488321c276af7e07f1abeecc8bc261a89f4`
- `git status` (custom_addons): 53 modificados + varios sin seguimiento (previos a esta tarea;
  **no** tocados por A/B).

## Artefactos y hashes (sha256)

| Archivo | sha256 |
|---|---|
| `patch/A_identificacion_no_bloqueante.diff` | `3d5115e9eadf1ca72634609c88140a583d5255cad3dac2aab406bce18123799d` |
| `patch/B_imputacion_posterior.diff` | `5d23ea02a37e9f9469b821ab9e0030f3fd79319fe4f809e91c40bc367479ee94` |
| `patch/AB_completo.diff` | `a4131812b238ecb98cb393f27dc8502cc6375050cd6e46af57db1189a6aaa282` |

Verificado (gate 2026-10-07): aplicar **A y luego B** a una **copia del árbol activo con sus cambios
locales** reproduce **byte a byte** el workcopy `addons/` (**45/45** archivos). `A` y `B` van
separados por hunks; **B depende de A** sólo por la relación inversa `sv_imputation_ids` (el filtro
la referencia). Los diffs **no** incluyen `madenat_lumber_docs/` (la documentación ya actualizada no
se sobrescribe con los diffs).

## Archivos afectados por A

- `madenat_lumber_core/models/madenat_guia_processing.py` (campo)
- `madenat_lumber_core/views/guia_processing_views.xml`, `…/guia_processing_list_search.xml` (radio + filtros)
- `madenat_lumber_intake/models/intake_console.py` (proxy compute+inverse)
- `madenat_lumber_intake/views/intake_console_views.xml`, `…/intake_guia_processing_facade_views.xml` (radio)
- `madenat_lumber_intake/tests/__init__.py`, `…/test_service_return_confirmation.py` (nuevo)
- `madenat_lumber_logistics/models/madenat_sv_imputation.py` (**parte A:** clase
  `MadenatGuiaProcessingServiceReturn` = `sv_imputation_ids` + guard Sí→No)

## Archivos afectados por B

- `madenat_lumber_logistics/models/madenat_sv_imputation.py` (**parte B:** `_i2_check_destination_is_service_return` + llamada en `action_apply`)
- `madenat_lumber_logistics/views/madenat_sv_imputation_views.xml` (filtro)
- `madenat_lumber_logistics/tests/__init__.py`, `…/test_service_return_pending_filter.py`,
  `…/test_service_return_imputation_guard.py` (nuevos); `…/test_sv_imputation_i2.py`,
  `…/test_sv_imputation_candidates.py` (fixtures con destino «Sí»)

## Documentación (ya aplicada en `custom_addons/madenat_lumber_docs/`)

`12_FLUJOS_INGESTA.md` §11.9 (§1.8.0) · `19_IMPUTACION_SV_Y_PROCESADORES.md` §19.9 (§1.7.0) ·
`04_DECISION_LOG.md` **AD-102** · `03_TESTS.md` §12 (§6.11.0) · `05_BACKLOG.md` (§8.9.0) ·
`02_CONTINUIDAD.md` §17.10 (§12.10.0) · `INDICE_DOCUMENTACION.md` (§12.6.0).

## Aplicación — **EJECUTADA** el 2026-10-08 en el desarrollo existente (`madenat_test`)

**Destino real:** `http://localhost:8069/` · base **`madenat_test`** · contenedor `odoo18_app`
(imagen `odoo-18-ce-web:latest`) · addons `custom_addons` → `/mnt/extra-addons`.
**No** se crearon bases, contenedores ni ramas nuevas.

1. **Respaldo previo verificado** (`BACKUP_AB_APPLY_20261008/`): árbol completo con `.git`
   (`code/custom_addons_full_20261008_092958.tar.gz`, 25 MB), cambios locales
   (`code/custom_addons_local_changes_antes.patch` + `git_status_antes.txt` + `HEAD.txt`),
   base (`db/madenat_test_20261008_092958.dump`, 11,3 MB, TOC 13.325 entradas),
   filestore (`filestore/odoo-web-data_20261008_092958.tar.gz`, 109 MB) y `config/`.
2. `cd custom_addons && patch -p1 < …/patch/AB_completo.diff` — **una sola vez** (con copias
   `.pre_ab_20261008` movidas a `BACKUP_AB_APPLY_20261008/pre_patch_files/`). Resultado: los **15**
   archivos **byte a byte** idénticos al workcopy (`IDENTICAL=15 MISMATCH=0`). **No** se copió el
   workcopy ni se trasladaron `.pyc`/cachés.
3. **Actualización controlada** (`odoo18_app` **detenido** durante el cambio de esquema; contenedor
   *one-shot* `--rm`, **solo** `madenat_test`, sin `-u all` y sin `--test-enable`):
   `odoo --config /etc/odoo/odoo.conf -d madenat_test -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics --stop-after-init --no-http --max-cron-threads=0`
   → `Modules loaded.` con **0 ERROR / 0 CRITICAL**
   (`FASES/APPLY_AB_UI_20261008/` (artefacto `update_modules_20261008_093223.log` en `logs/`, fuera de git)).
4. **Reorganización de la UI de Ingreso de Madera** en `madenat_lumber_intake/views/intake_console_views.xml`
   (vista primaria `view_madenat_lumber_intake_console_form`): resumen en 2 columnas, «Aplicar cambios»
   debajo, línea de identificación de retorno a todo el ancho, Evidencia documental en 3 columnas con
   encabezado único, detalle del packing list a todo el ancho. Recarga controlada:
   `-u madenat_lumber_intake` (mismo patrón; `APPLY_AB_UI_20261008/logs/update_ui_*.log`).
5. **Pruebas dirigidas sobre `madenat_test`:** **`0 failed, 0 error(s) of 88 tests`** (misma nómina de
   8 clases del gate histórico; incl. Cristhian uid 8, `su=False`). Log:
   `FASES/APPLY_AB_UI_20261008/` (artefacto `tests_directed_madenat_test_20261008_093825.log` en `logs/`, fuera de git).

## Reversión

### Código

- **Reversa de ficheros:** `cd custom_addons && patch -R -p1 < …/patch/AB_completo.diff` (o las copias
  `.pre_ab_20261008` conservadas en `BACKUP_AB_APPLY_20261008/pre_patch_files/`) restaura HEAD
  `e302c488321c276af7e07f1abeecc8bc261a89f4`. Para la **UI** basta revertir el bloque de comentarios
  «reorganización 2026-10-08» de `intake_console_views.xml` a la estructura previa.
- **Sin migración destructiva:** el campo `service_return_confirmation` es un Selection sin uso
  histórico previo (las guías anteriores quedan legibles con valor vacío); la relación inversa
  `sv_imputation_ids` es virtual (sin columna). Revertir el módulo deja el campo huérfano en BD
  (inofensivo) o se elimina con la reversa del módulo.
- **No** toca `stock.quant`, lotes, pickings, ledger, facturación ni valorización.

### Datos (si hubiera que recuperar el estado previo)

1. `docker stop odoo18_app`.
2. `docker exec odoo18_db dropdb -U odoo --if-exists madenat_test` y recrear:
   `createdb -U odoo -O odoo madenat_test` + `pg_restore -U odoo -d madenat_test < db/madenat_test_20261008_092958.dump`.
3. Restaurar el filestore del volumen `odoo-18-ce_odoo-web-data` desde
   `filestore/odoo-web-data_20261008_092958.tar.gz`.
4. `docker start odoo18_app`.

> **Aviso:** la reversión de código **no** equivale a restaurar base ni filestore. **No** restaurar
> una base sobre trabajo posterior sin advertirlo y obtener aprobación.

## Criterios de aceptación

- **88/88** dirigidas en verde sobre `madenat_test`; **0 regresiones** atribuibles a A/B o a la UI.
- **Estructura verificada** (read-only): resumen 2 columnas; **un** encabezado «Evidencia documental»
  con `col="3"`; `Aplicar cambios`; radio e `in_scope`; orden `resumen → botón → radio → evidencia →
  packing`.
- **Navegador (V3): PENDIENTE** — radio Sí/No visible y editable en Consola (Procesado de servicio);
  `action_apply` rechaza destino sin «Sí»; Sí→No bloqueado con imputación aplicada; nueva disposición
  visible. Guion: `docs/GUION_VERIFICACION_NAVEGADOR.md` (actualizado a 8069 / `madenat_test`).
- Sin efectos de stock/contabilidad.

## Estado de ejecución (2026-10-08)

- [x] **Aprobación** del alcance A/B y del destino de desarrollo: **concedida** (orden de trabajo del
      2026-10-08).
- [x] Aplicación en `madenat_test` + actualización controlada de módulos.
- [x] Reorganización de la UI de Ingreso de Madera.
- [x] Pruebas dirigidas (88/88) sobre `madenat_test`.
- [x] **Retiro del aislamiento temporal** (contenedor, volumen, bases y `/tmp`; dumps conservados en
      `APPLY_AB_UI_20261008/retired/db/`).
- [ ] **Verificación en navegador (V3)** con el usuario real Cristhian — **NO ejecutada** (sin
      navegador). No se declara completada.
- [ ] Instalación en **base limpia** (la corrida fue sobre `madenat_test`, con esquema previo).
