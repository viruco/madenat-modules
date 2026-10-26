# UNIFY_SV_REBAJA_MENU_20261010 — Evidencia (único acceso «Rebaja de etiquetas»)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / contenedor `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia** (no doctrinal). La doctrina vive en
`custom_addons/madenat_lumber_docs/CANON/` (`19 §19.15`, `02 §17.16.13`, `03 §17`, `05`, `INDICE`).

## Objetivo
Consolidar «Asignaciones SV» e «Imputaciones documentales SV» en **un único** enlace operativo
**«Rebaja de etiquetas»**, reutilizando modelos, documentos, asistente, aplicación, reversa y auditoría
existentes. **No** se crea otra operación, documento, rebaja ni saldo; **no** se recalcula historia.

## Artefactos de evidencia
- `code/diff_unify_sv_rebaja.diff` — **diff de ESTA intervención** (reconstruido contra el estado
  pre-intervención 18.0.1.9.0: `git archive HEAD` + `changes_assign_sv_20261010.diff`); incluye sólo
  los 11 archivos tocados. **No** contiene el trabajo ajeno previo.
- `code/git_status_pre.txt` / `code/git_status_after.txt` — estado Git antes/después (cambios ajenos
  preservados).
- `logs_update_1.log` / `logs_update_2.log` / `logs_update_3.log` — actualizaciones (exit 0; la 2.ª
  acredita NAV-10; la 3.ª sincroniza el rótulo del campo). `logs_navtests_final.log` — suite dirigida
  NAV (11/11, re-ejecutada tras el cambio de rótulo). `logs_regression_full.log` — regresión 298.
- `menu_metadata_after.txt` — estado real de `ir.ui.menu` bajo Logística Exportación.

## Baseline
- Rama `feat/guia-correccion-documental-preservada-20261002`; HEAD **`b1d2d19`**
  (`fix(logistics): integridad del vínculo envío-retorno`).
- **Cambios locales ajenos preservados** (44 modificados + 12 sin seguimiento). Ver
  `code/git_status_pre.txt` y `code/modules_pre.tar.gz`. **Sin** commit/push, **sin** `git reset -hard`
  ni `git clean`.

## Decisión funcional (CANON/19 §19.15)
**«Rebaja de etiquetas» es el ÚNICO acceso operativo a la asignación documental SV.** La pantalla de
etiquetas SV y los documentos de imputación son **vistas del mismo mecanismo**, no dos operaciones
independientes. La navegación anterior se **sustituye**; no se añade una tercera entrada.

## Cambios de código
- **`views/madenat_sv_imputation_views.xml`**
  - Menú `menu_madenat_sv_assignment`: **«Asignaciones SV» → «Rebaja de etiquetas»** (reutilizado).
  - Acción `action_madenat_sv_assignment`: «Rebaja de etiquetas» (`stock.lot`,
    `domain=[('lot_flow_type','=','volume')]`); `search_view_id` dedicado.
  - Listado/formulario: **«Etiquetas SV» / «Etiqueta SV»**; encabezados **Volumen documental /
    Rebajado documental / Saldo documental**; ayuda de efecto **documental**.
  - **Búsqueda dedicada** `view_madenat_sv_assignment_search` (Etiqueta SV, Guía de procedencia,
    Producto; «En stock» **opcional/removible**); sin panel técnico de ubicaciones/partners.
  - **Navegación interna:** «Registrar rebaja» (asistente), «Historial de rebajas» (por SV),
    «Ver historial completo» (todos los documentos); lista de asignaciones con «Abrir documento».
  - Menú `menu_madenat_sv_imputation`: **retirado de navegación** (`active=False`, `record` posterior
    al `menuitem` ⇒ no reaparece al reaplicar `-u`; reversible).
  - Acción `action_madenat_sv_imputation`: «Historial de rebajas» (**preservada**).
  - Vistas del historial con estado tipo *badge* y filtros **Vigentes/Históricos** +
    Borrador/Pendiente/Aplicada/Reversada/Anulada.
- **`models/madenat_sv_imputation.py`**: método `stock.lot.action_open_sv_rebajas()` — reutiliza la
  acción `action_madenat_sv_imputation` con dominio por SV (`sv_line_ids.sv_lot_id`). **No** crea
  registro, **no** aplica, **no** altera saldo (sólo lectura).
- **`wizards/madenat_sv_imputation_wizard_views.xml`**: acción/asistente **«Registrar rebaja»**.
- **`tests/test_sv_rebaja_navigation.py`** (nuevo) + registro en `tests/__init__.py`.
- **`__manifest__.py`**: `18.0.1.9.0 → 18.0.1.10.0`. **`CHANGELOG.md`**: sección `[18.0.1.10.0]`.

## Menú final y mecanismo de retiro
- **XML ID reutilizado:** `madenat_lumber_logistics.menu_madenat_sv_assignment` (id 545).
- **Menú retirado:** `menu_madenat_sv_imputation` (id 542) → `ir.ui.menu.active = False`.
  Se **conserva** el `menuitem` en XML (instalación nueva) y se desactiva con un `record` posterior;
  el `menuitem` no fija `active`, por lo que **no** se reactiva en la siguiente `-u`.

## Actualización en desarrollo
```
docker exec odoo18_app bash -lc "odoo --database=madenat_test --update=madenat_lumber_logistics \
  --stop-after-init --no-http --log-level=info"
```
- **Exit code 0** (`logs_update_1.log`). Ejecutada **dos veces** (`logs_update_2.log`) — la 2.ª
  acredita **NAV-10** (el menú retirado **no** reaparece). Sin `-u all`. Sin despliegue remoto.
- **Metadatos reales (`ir.ui.menu`):** 545 «Rebaja de etiquetas» **activo** (acción 874 →
  `stock.lot`); 542 «Imputaciones documentales SV» **inactivo** (acción 867 «Historial de rebajas» →
  `madenat.sv.imputation`). Ver `menu_metadata_after.txt`.

## Pruebas
- **Dirigidas NAV-01..12** (`--test-tags /madenat_lumber_logistics:TestSvRebajaNavigation`):
  **`0 failed, 0 error(s) of 11 tests`** (`logs_navtests_final.log`).
- **Regresión de módulo** (`--test-tags /madenat_lumber_logistics`): **`4 failed, 0 error(s) of 298
  tests`** (`logs_regression_full.log`). Las **4 fallas** son **exactamente** las mismas de la línea
  base 18.0.1.9.0 (`test_processor_locations.test_09_auditoria_envio_normal`,
  `test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 fallas nuevas, 0 errores**. **No** se modificó
  ningún test ajeno ni se borró evidencia.

## Respaldo / recuperación
- `code/modules_pre.tar.gz` — `madenat_lumber_logistics` + `madenat_lumber_docs` antes de la etapa.
- `db/madenat_test_pre.dump` — `pg_dump -Fc` (~11 MB).
- **Recuperación:** (1) código → extraer `modules_pre.tar.gz` sobre `custom_addons`;
  (2) esquema → `odoo -u madenat_lumber_logistics`; (3) base → restaurar `db/madenat_test_pre.dump`.
  **Recuperación de navegación:** poner `active=True` en `menu_madenat_sv_imputation` y volver a
  `-u` (revierte el retiro sin tocar documentos).

## Límites y pendientes mínimos
1. **V3 *pixel*** — navegador real **no** disponible; verificación por XML/metadatos/SQL/ORM. Guion
   manual en `docs/GUION_MANUAL_NAVEGADOR.md` (**no** se declara renderizado aprobado).
2. **Bloque D** cuantitativo — fuera de alcance (`19` §19.12).
3. Búsqueda por procesador: `sv_assignment_processor_id` es computado **no almacenado**; se muestra
   como columna pero **no** se ofrece como campo de búsqueda (no searchable) — mejora posterior.

## Propuesta de commit (NO ejecutado)
`refactor(logistics): unifica el acceso operativo en «Rebaja de etiquetas» (CANON/19 §19.15)` —
módulo `madenat_lumber_logistics` 18.0.1.10.0 + `tests/test_sv_rebaja_navigation.py` + docs
CANON/02/03/05/19/INDICE. **Mantener** los demás cambios locales ajenos (no incluidos en este commit).
