# HOTFIX_OWL_COLUMN_INVISIBLE_20261010 — Evidencia (OwlError al abrir «Registrar rebaja»)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia** de la incidencia bloqueante de renderización. La doctrina
vive en `madenat_lumber_docs/CANON/` (`19 §19.20`, `02 §17.16.18`, `03 §22`, `05`, `INDICE`).

## 1. Error real del navegador (reportado por Mauricio)
```
EvalError: Can not evaluate python expression: (bool(not wizard_id.multi_sv))
Name 'wizard_id' is not defined
Origen: ListRenderer.evalColumnInvisible
```

## 2. Vista efectiva y estructura de contenedores
- Vista: `madenat_lumber_logistics.view_madenat_sv_imputation_wizard_form` (arch embebido en
  `wizards/madenat_sv_imputation_wizard_views.xml`).
- Contenedor inmediato del listado `sv_line_ids`: `<page>` → `<notebook>` → `<form>` del asistente
  (`madenat.sv.imputation.wizard`). **No hay herencias** de esta vista (ninguna `inherit_id` la
  referencia), por lo que el contenedor inmediato es el propio formulario.
- La lista es de `madenat.sv.imputation.wizard.sv.line` y `wizard_id` es un campo de ESAS filas.
- Evidencia: `code/effective_view.txt`.

## 3. Causa demostrada
En Odoo 18 `column_invisible` se evalúa con el **contexto del formulario contenedor**:
`web/static/src/views/list/list_renderer.js::evalColumnInvisible` →
`evaluateBooleanExpr(columnInvisible, this.props.list.evalContext)`. Para listas embebidas,
`web/static/src/model/relational_model/record.js` expone `evalContext.parent → parentRecord.evalContext`;
los campos de cada fila **no** están disponibles. Por eso `wizard_id` no está definido.
**No** fue un problema de caché.

## 4. Corrección
- `column_invisible="not parent.multi_sv"` (patrón canónico de Odoo core; p. ej. `account.move.line` →
  `column_invisible="parent.move_type …"`).
- `<field name="multi_sv" invisible="1"/>` en el formulario padre (carga explícita del flag). Ya estaba
  implicado por los modificadores `invisible`; se declara explícitamente (no se añade `wizard_id` como
  columna: `column_invisible` no se evalúa con los valores de cada fila).
- Revisión acotada: es el **único** `column_invisible` del asistente.

## 5. Defecto adicional detectado al verificar el Caso E (guardar/reabrir)
Al reabrir un borrador, `_i2_reconstruct_commands` reconstruía el reparto anidado
(`line_ids[*].sv_alloc_ids`) **sin** `wizard_id`, por lo que `wiz.sv_line_ids` quedaba vacío ⇒
`multi_sv=False` (columna «SV destino» oculta), totales de cabecera en 0 y pestaña «Asignación a SV» sin
filas. Corregido en el mismo hotfix: `_i2_reconstruct_commands` incluye `wizard_id` cuando el asistente
ya existe y `create()` enlaza el reparto anidado tras crear el asistente. Evidencia:
`code/verify_reopen_orm.out` (antes/después). Sin reglas de negocio nuevas.

## 6. Preservado
Cantidad editable desde Materiales, reparto como fuente de verdad, repartos a otros SV,
identidad/descripción del material, `processed_lot_id` obligatorio + `force_save`, disponibilidad,
reservas, aplicación, reversa, permisos, atomicidad e idempotencia. Sin nuevos modelos, menús ni
mecanismos.

## 7. Pruebas ejecutadas
- `TestSvRebajaUiLimpia` + `TestSvRebajaOwlColumnInvisible` (casos A–E + invariantes de arch) =
  **20/20** (EXIT 0) — `logs_tests_owl.log`.
- Regresión `madenat_lumber_logistics` = **4 failed, 0 error(s) of 362 tests** (EXIT 1) —
  `logs_regression.log`. Fallas = **las mismas 4 preexistentes** (`test_processor_locations.test_09`,
  `test_processor_shipment_ad89.test_t1/t5/t6`).
- Casos: A apertura sin reparto · B sólo SV de trabajo (columna oculta) · C varios SV (columna visible
  con destinos) · D 1↔varios SV sin pérdida · E guardar/reabrir conserva datos y visibilidad.

## 8. Límite de navegador
No hay navegador en el entorno: **corrección implementada; renderización pendiente de comprobación
manual**. Una validación XML/ORM **no** demuestra la evaluación de la expresión en el cliente Owl. El
fallo **apareció en la comprobación real del navegador**; **no** se afirma que las pruebas previas lo
detectaran.

## 9. Versión y actualización
`odoo --database=madenat_test --update=madenat_lumber_logistics --stop-after-init --no-http
--http-port=8079 --log-level=info` → **EXIT 0** (`logs_update.log`, `update.exit`). Versión
**18.0.1.14.0 → 18.0.1.14.1**.

## 10. Documentación
`CANON/19` **1.17.0** §19.20; `CANON/02` **12.26.0** §17.16.18; `CANON/03` **6.26.0** §22;
`CANON/05` **8.25.0**; `INDICE` **12.20.0**; `CHANGELOG` `[18.0.1.14.1]`.

## 11. Respaldos y recuperación
`code/modules_pre_hotfix.tar.gz` (estado previo al hotfix = 18.0.1.14.0). Recuperación: extraer el
tarball → `-u madenat_lumber_logistics`. Las pruebas son **transaccionales** (sin datos residuales).

## 12. Estado
**Incidencia bloqueante de renderización; aceptación pendiente.** Sin commit, push ni despliegue remoto.

## 13. Entrega
- `code/diff_hotfix_owl.diff` — **diff puntual** del hotfix.
- `code/effective_view.txt` — estructura de la **vista efectiva** (pestañas, columnas, `column_invisible`,
  carga de `multi_sv` en el padre).
- `code/verify_reopen_orm.out` — evidencia ORM de **guardar/reabrir** + `wizard_id`.
- `logs_update.log`, `update.exit`, `logs_tests_owl.log`, `logs_regression.log`, `regression.exit`.
- `docs/GUION_MANUAL_NAVEGADOR.md` — comprobación manual de renderización (pendiente).
