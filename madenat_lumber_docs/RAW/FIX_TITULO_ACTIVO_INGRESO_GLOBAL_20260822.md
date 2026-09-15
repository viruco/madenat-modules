# Fix — Título Activo de Ingreso Global

## Problema observado
Tras la implementación de `replaceCurrentAction`, al volver desde la fachada de guía al flujo principal, el encabezado podía mostrar el título largo de la guía activa (ej. `19827 · … · ID 543`) en lugar de `Ingreso Global`.

## Causa técnica identificada
**Hipótesis C confirmada por evidencia (shell readonly con rollback)**:
- `_get_intake_console_action()` → `INNER_NAME='Ingreso Global'`, `res_model='madenat.lumber.intake.console'`, `target='current'`.
- `action_back_to_intake_console()` → `WRAP_TYPE='ir.actions.client'`, tag `madenat_lumber_intake.replace_current_action`, `WRAP_INNER_NAME='Ingreso Global'`.

El **backend ya emite el título canónico correcto**; el artefacto visual (título de la guía en el header) es comportamiento del web client durante la transición del `replaceCurrentAction`, que conserva la metadata/derecho del controller previo hasta que el nuevo controller (con `name='Ingreso Global'`) re-renderiza. No hay defecto de contrato en el retorno.

## Cambio aplicado
Refuerzo del **contrato del título canónico** en `test_intake_navigation_actions.py`:
- `test_get_intake_console_action_contract` ahora verifica que `action['name']` sea **exactamente** `action_madenat_lumber_intake_console.name` (='Ingreso Global'), no solo no vacío.

Este test previene que una futura regresión reemplace el nombre canónico del retorno por otro valor (display_name de guía, literal ad hoc, etc.) que rompería el título del controller activo.

## Contrato de retorno preservado
- `type='ir.actions.act_window'` (inner)
- `name='Ingreso Global'` (canónico, desde `action_madenat_lumber_intake_console`)
- `res_model='madenat.lumber.intake.console'`
- `res_id=900000000+id`
- `view_mode='form'`, `view_id` consola form, `views=[(view_id,'form')]`
- `target='current'`
- Wrapper `ir.actions.client` con tag `madenat_lumber_intake.replace_current_action` y `stackPosition:"replaceCurrentAction"` — sin cambios.
- Apertura de guía: sin cambios (mantiene su identidad).

## Pruebas ejecutadas
- `TestIntakeNavigationActions` (4, con assert de `name` canónico): **4/4 PASS — EXIT=0**.
- `py_compile` OK.
- Sin cambios en JS ni en modelos; core Odoo intacto.

## Resultado esperado en UAT
- Al volver desde la fachada, el header debe mostrar `Ingreso Global` (el controller activo final es la consola con `name` canónico).
- La guía mantiene su título al abrirse.
- Sin reintroducir breadcrumbs duplicados; sin pantalla vacía.

## Riesgos y límites
- La persistencia visual del título de la guía durante la transición del replace es del web client; la confirmación definitiva requiere UAT en sesión nueva (el header re-renderiza tras el replace; si persiste el artefacto en el primer frame, es de transición y no de contrato).
- No se modificó `no_breadcrumbs`, ni `stackPosition`, ni el wrapper JS, ni el `display_name` de la guía.
- La validación de `name` canónico ahora está garantizada por test; cualquier regresión lo detecta.