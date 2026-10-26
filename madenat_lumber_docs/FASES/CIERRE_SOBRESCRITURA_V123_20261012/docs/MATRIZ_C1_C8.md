# V1 — Matriz de cruces con EDICIÓN DIRECTA (C1–C8)

**Fecha:** 2026-10-12 · **Entorno:** `madenat_test` LOCAL · **Pruebas:** `tests/test_sv_rebaja_save_lock_direct.py`.

## Cómo se abre el formulario persistente y qué es editable
- **Apertura:** `action_madenat_sv_imputation` (menú «Imputación SV» y `action_open_sv_rebajas` desde el SV) y
  `action_open_imputation` (desde el reparto). Vista `view_madenat_sv_imputation_form`.
- **Editable en `draft`/`pending` (verificado en la vista efectiva):** `guia_processing_id`, `processor_id`,
  `processor_location_id`, `date`, **líneas** (`processed_lot_id`, `nominal_volume_m3`) y **repartos**
  (`imputation_line_id`, `sv_lot_id`, `imputed_volume_m3`), más `reason`/`reversal_reason`.
- **Botones de estado** (`action_pending`, `action_apply`, `action_cancel`, `action_back_to_draft`,
  `action_reverse`, `action_reopen_to_draft`) en el header.
- **Conclusión:** el formulario persistente **NO es de sólo lectura**; es un editor real de contenido.

## Decisión de diseño
**Alternativa A** (la mínima que cubre los cruces reales **sin cambiar la funcionalidad**):
reutilizar `edit_version`; el formulario la envía con **`force_save="1"`** (atributo nativo de Odoo 18); el
`write()` compara de forma **atómica** (`_i2_assert_edit_version`: advisory ns 1 + comparación) y **rechaza** la
edición obsoleta. **No** usa `write_date`, ni flags de contexto, ni memoria global; **no** ofrece sobrescritura
forzada. Los campos **siguen editables** ⇒ **no** se retiran permisos ni se ocultan vías (no requeriría
autorización de Alternativa B).

Descartadas: **B** (restringir edición directa → cambia el acceso funcional ⇒ requeriría autorización aparte) y
**C** (dejar form-vs-form pendiente sin más, cuando A sí es viable).

## Matriz C1–C8
| # | Cruce | Estado inicial | Modifica | Esperado | Observado | Persistido | Evidencia |
|---|---|---|---|---|---|---|---|
| **C1** | Asistente A → asistente B obsoleto | draft (v) | A guarda (v+1); B guarda con v | B rechazado | **B rechazado** | datos de A | `test_sv_rebaja_save_lock.py::LOCK-01` |
| **C2** | Formulario directo → asistente obsoleto | draft (v) | form escribe (v+1); asistente (v) guarda | asistente rechazado | **rechazado** | ‘directo’ | `test_c2_…` |
| **C3** | Asistente → formulario directo obsoleto | draft (v) | asistente (v+1); form (v) guarda | form rechazado | **rechazado** | datos del asistente | `test_c3_…` |
| **C4** | Formulario A → formulario B obsoleto | draft (v0) | A escribe (v1); B (v0) escribe | B rechazado | **rechazado** | ‘A’ | `test_c4_…` |
| **C5** | Edición directa de línea → padre obsoleto | draft (v) | línea escribe (v+1); padre form (v) | padre rechazado | **rechazado** | sin cambio | `test_c5_…` |
| **C6** | Edición directa → asistente obsoleto aplica | draft (v) | form escribe (v+1); asistente (v) aplica | no aplica | **no aplica** | draft | `test_c6_…` |
| **C7** | Asistente guarda → form obsoleto cambia estado | draft (v) | asistente (v+1); form (v) guarda+estado | rechazado | **rechazado** | draft | `test_c7_…` |
| **C8** | Transición de estado → form obsoleto edita | draft (v) | cancelación (v+1); form (v) edita | rechazado | **rechazado** | cancelled | `test_c8_…` |

**Positivo:** el formulario con versión **vigente** guarda sin conflicto y la versión avanza
(`test_v1_directo_con_version_vigente_funciona`).

## Límite residual declarado (no ocultado)
Una escritura **ORM/RPC que NO envíe `edit_version`** (p. ej. un script/automatización o un cliente que no use el
formulario con `force_save`) **no** se compara (`test_v1_residual_orm_sin_version`): se aplica, **pero la versión
avanza**, de modo que todo asistente/formulario abierto lo detecta en su siguiente guardado. Es una vía
**programática** (no la UI). Se documenta como **residual**; para cerrarla del todo habría que **exigir**
`edit_version` en TODA escritura de contenido (refactor de las escrituras internas) — no es «mínimo» y no se
implementa sin decisión.

## Nota sobre C7 (botones de estado)
El cliente **guarda el formulario (con `edit_version`) antes** de ejecutar un botón de tipo objeto ⇒ el cruce C7
queda cubierto. Si el formulario **no está dirty**, no hay pre-save; en ese caso el botón opera sobre el contenido
**vigente** (leído de la BD), sin reemplazo silencioso de datos obsoletos.
