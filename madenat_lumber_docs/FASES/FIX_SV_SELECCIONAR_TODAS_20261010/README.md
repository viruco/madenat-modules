# FIX_SV_SELECCIONAR_TODAS_20261010 — Evidencia (corrección «Seleccionar todas» + asignación explícita)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia**. La doctrina vive en `madenat_lumber_docs/CANON/`
(`19 §19.17`, `02 §17.16.15`, `03 §19`, `05`, `INDICE`).

## 1. Causa exacta del fallo (demostrada, no supuesta)
Al pulsar **«Seleccionar todas»** en una apertura nueva, el `create` de
`madenat.sv.imputation.wizard.line` fallaba por campo obligatorio `processed_lot_id`. **Causa:** el
cliente Odoo 18 **omite** los subcampos `readonly` de una x2many salvo `force_save="1"`
(`web/static/src/model/relational_model/record.js::_getChanges`, líneas 629-640). El campo
`processed_lot_id` era `readonly="1"` **sin** `force_save`, por lo que los comandos CREATE de las
filas llegaban sin el identificador. **No** era `required`, ni un comando concreto, ni un problema de
`sudo`.

## 2. Corrección implementada
- `views`/`wizards/…_wizard_views.xml`: `processed_lot_id` → `readonly="1" force_save="1"`.
- `sv_line_ids` del asistente → `create="false"` (las filas se crean por acción explícita; evita
  filas sin `wizard_line_id`).
- **No** se quitó `required`, **no** se añadió etiqueta ficticia, **no** se capturó la excepción,
  **no** se usó `sudo`, **no** se exigió guardar antes.

## 3. Flujo simplificado (Seleccionar ≠ asignar ≠ aplicar)
Elegir guía de retorno → **seleccionar** etiquetas («Seleccionar todas» sólo marca) →
**«Asignar seleccionadas al SV de trabajo»** (fila por etiqueta con el SV de trabajo y **volumen 0**)
→ introducir volumen o **«Usar disponible»** → revisar **resumen** («X etiquetas · Y m³ preparados
para SV…») → **Guardar** o **Aplicar**. Sólo `action_apply` registra la rebaja documental.

## 4. Acciones nuevas y efectos
- `action_assign_selected`: no aplica, no mueve stock, no crea otro documento, no duplica filas, no
  sobrescribe cantidades y **no borra repartos a otros SV**.
- `action_use_available`: autorrelleno **explícito** = `min(disponible documental, nominal
  comprometido)`.
- `action_select_all`: sólo cambia la selección.
- `assigned_summary` y `etiqueta_pendiente_m3` (nominal comprometido − reparto del documento).
- `_i2_build_imputation`: rechaza con mensaje claro una fila asignada con volumen 0 (sin estados
  parciales). `action_propose_fifo` ya no borra todo el reparto (sólo rehace lo seleccionado).

## 5. Identificadores visibles y su fuente
- **Etiqueta proveedor** = `stock.lot.external_labels` (opcional; si vacío, se usa el interno).
- **Lote interno** = `stock.lot.name` (`processed_lot_id`).
- Secundarias: Capacidad nominal (`_i2_lot_nominal_m3`), Rebajado etiqueta aplicado
  (`_i2_lot_applied_m3`), Reservado (`_i2_lot_reserved_m3`), Disponible (`_i2_lot_available_for_m3`),
  Pendiente de reparto (nominal comprometido − reparto). No se renombra `display_name`.

## 6. Fórmulas y caso parcial (VOL-01)
Nominal 5 (comprometido) con reparto 3 al SV → **Pendiente = 2**; `imp.nominal_total_m3 = 5` (lado
etiqueta) y `imp.imputed_total_m3 = 3` (lado SV). No se presenta «5 rebajado».

## 7. Pruebas ejecutadas
- `--test-tags /madenat_lumber_logistics:TestSvRebajaSeleccionAsignacion` → **0 failed, 0 error(s) of
  16 tests** (EXIT 0) — `logs_fix_tests1.log`.
- `--test-tags /madenat_lumber_logistics` → **4 failed, 0 error(s) of 334 tests** (EXIT 1) —
  `logs_fix_regression.log`. Fallas = las 4 preexistentes (`test_processor_locations.test_09`,
  `test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.
- Ciclo de formulario (ERR): apertura (`default_get`) → elección de guía (`onchange`) → acción, sobre
  líneas **no persistidas previamente**; ERR-01 comprueba `force_save="1"` en el arch.

## 8. Versión aplicada
`odoo --database=madenat_test --update=madenat_lumber_logistics --stop-after-init --no-http
--http-port=8079 --log-level=info` → **EXIT 0** (`logs_fix_update_final.log`). Versión
**18.0.1.11.0 → 18.0.1.12.0**. Sin `-u all`; sin despliegue.

## 9. Documentación
`CANON/19` **1.14.0** §19.17; `CANON/02` **12.23.0** §17.16.15; `CANON/03` **6.23.0** §19;
`CANON/05` **8.22.0**; `INDICE` **12.17.0**; `CHANGELOG` `[18.0.1.12.0]`.

## 10. Respaldos y recuperación
`db/madenat_test_pre.dump`, `db/filestore_pre.tar.gz`, `code/modules_pre.tar.gz`. Recuperación:
extraer tarball → `-u madenat_lumber_logistics` → restaurar dump/filestore.

## 11. Aceptación visual
**Pendiente** (V3 *pixel*). Guion: `docs/GUION_MANUAL_NAVEGADOR.md`. No se declara aceptado por
Mauricio.

## 12. Pendientes mínimos
Aceptación visual (V3); Bloque D cuantitativo fuera de alcance.

## 13. Propuesta de commit (no ejecutado)
`fix(logistics): corrige «Seleccionar todas» (force_save) y añade asignación explícita al SV
(CANON/19 §19.17)` — `madenat_lumber_logistics` 18.0.1.12.0 +
`tests/test_sv_rebaja_seleccion_asignacion.py` + CANON/02/03/05/19/INDICE.
