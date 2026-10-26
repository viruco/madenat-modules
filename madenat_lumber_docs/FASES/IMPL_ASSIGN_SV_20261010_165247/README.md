# IMPL_ASSIGN_SV_20261010 — Evidencia (Operación manual de asignaciones centrada en SV)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / contenedor `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia** (no doctrinal). La doctrina vive en
`custom_addons/madenat_lumber_docs/CANON/` (`19 §19.14`, `02 §17.16.12`, `03 §16`, `05`, `INDICE`).

## Baseline
- Rama `feat/guia-correccion-documental-preservada-20261002`; HEAD **`b1d2d19`**
  (`fix(logistics): integridad del vínculo envío-retorno`).
- **Cambios locales ajenos preservados** (44 archivos modificados + untracked). Ver `code/git_status.txt`,
  `code/wip_uncommitted.diff`, `code/wip_stat.txt`. Se verificó por md5 que los diffs de
  `views/logistics_menus.xml` y `security/ir.model.access.csv` son **idénticos** al baseline.
- **Sin commit, sin push, sin despliegue remoto.**

## Respaldo / recuperación
- `code/modules_pre.tar.gz` — `madenat_lumber_logistics` + `madenat_lumber_docs` antes de la etapa.
- `db/madenat_test_pre.dump` — `pg_dump -Fc` (~11 MB).
- **Filestore:** sin cambios en esta etapa (sólo modelo/vistas/docs); respaldo vigente del mismo día en
  `../CONCILIACION_ENVIO_RETORNO_20261010/filestore_pre.tar.gz`.
- **Recuperación:** (1) código → extraer `modules_pre.tar.gz` sobre `custom_addons`;
  (2) esquema → `odoo -u madenat_lumber_logistics`; (3) base → restaurar `db/madenat_test_pre.dump`.
  **No** restaurar el dump sobre trabajo posterior sin advertir el impacto.

## Cambios
- **`madenat_lumber_logistics` 18.0.1.8.0 → 18.0.1.9.0.**
- **Modelo** `models/madenat_sv_imputation.py`: constraints `_check_label_belongs_to_guia` (D10),
  `_check_reparto_within_nominal` y `_check_within_line_nominal` (D10/D11); campos de consulta en
  `.sv.line`; herencia `stock.lot` (consulta centrada en SV) + `_i2_validate_payload` reforzado.
- **Asistente** `wizards/madenat_sv_imputation_wizard.py`: `sv_lot_id`, selección `selected`,
  «Seleccionar todas»/«Quitar selección», reconstrucción del borrador, `_i2_build_imputation` por
  *upsert*, bloqueo de cambio de guía.
- **Vistas:** asistente (pestañas y mensaje de efecto) y `views/madenat_sv_imputation_views.xml`
  (pantalla «Asignaciones SV» + acción + menú). No se tocaron vistas ajenas de lotes.
- **Pruebas:** nuevo `tests/test_sv_imputation_manual.py` (T-MAN-01..12) + registro en `tests/__init__.py`.
- **Documentación:** `CANON/19` §19.14, `02` §17.16.12, `03` §16, `05`, `INDICE` (versiones anotadas).

## Actualización local (comando exacto)
```
docker exec odoo18_app bash -lc "odoo --database=madenat_test --update=madenat_lumber_logistics \
  --stop-after-init --no-http --log-level=info"
```
**Exit code 0** — `logs_update_1801009.log` (sin errores; avisos preexistentes). No `-u all`.

## Pruebas
- Suite dirigida: `--test-tags /madenat_lumber_logistics:TestSvImputationManual`
  → **`0 failed, 0 error(s) of 12 tests`** (`logs_tests_manual3.log`).
- Regresión de módulo: `--test-tags /madenat_lumber_logistics`
  → **`4 failed, 0 error(s) of 286 tests`** (`logs_tests_logistics_full.log`).
  Las **4 fallas** son **las mismas preexistentes/ambientales** documentadas (aserción global
  `deviation` sobre eventos históricos `19889/19941/20342/20381/21739`) ⇒ **0 fallas nuevas,
  0 errores**. **No** se modificó ningún test ajeno ni se borró evidencia.
- **Integración web/RPC (NO V3):** `rpc_integration_check.py` + `logs_rpc_integration_report.txt`
  (sesión autenticada de Operaciones; menú **«Asignaciones SV»** visible; `default_get` SV OK).
- **No ejecutado (fuera de alcance):** navegador real (V3 *pixel*); concurrencia real; base limpia;
  Bloque D cuantitativo.

## Registros de prueba
- Usuario temporal `impl_sv_check@madenat.test` (uid **3109**, Operaciones): **creado y desactivado**
  al cierre de la verificación RPC.
- SV de muestra existente: `SV00000000841` (id 10215).

## Pendientes mínimos
1. **V3 *pixel*** — guion manual en `docs/GUION_MANUAL_NAVEGADOR.md` (no hay navegador en el entorno).
2. **Bloque D** cuantitativo — fuera de alcance (`19` §19.12).
3. Regularización de históricos — **0** inconsistencias detectadas; procedimiento separado si se autoriza.

## Propuesta de commit (NO ejecutado)
`feat(logistics): operación manual de asignaciones centrada en SV (CANON/19 §19.14)` — módulo
`madenat_lumber_logistics` 18.0.1.9.0 + docs CANON/02/03/05/19/INDICE.
