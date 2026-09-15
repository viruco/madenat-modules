# Implementación — Reemplazo de Controller Actual para Breadcrumbs

## Objetivo
Eliminar la acumulación visual de breadcrumbs en el ciclo `Ingreso Global → Abrir origen → Fachada de guía → Volver a Ingreso Global` mediante `stackPosition: "replaceCurrentAction"`, sin patch global del web client.

## Alcance modificado
Solo `madenat_lumber_intake`:
- `__manifest__.py` (assets backend)
- `models/intake_console.py` (`action_open_source` envoltura)
- `models/intake_guia_processing.py` (`action_back_to_intake_console` envoltura)
- `static/src/js/replace_current_action.js` (nuevo)
- `tests/test_intake_navigation_actions.py`, `tests/test_intake_wizard.py` (actualizados)
- `madenat_lumber_docs/RAW/IMPLEMENTACION_REPLACE_CURRENT_ACTION_BREADCRUMBS_20260822.md`

## Diseño aplicado
- Client action única: `madenat_lumber_intake.replace_current_action`.
- Recibe un action dict en `params.action_to_execute`, valida su existencia y ejecuta una sola vez:
  ```js
  await env.services.action.doAction(actionToExecute, { stackPosition: "replaceCurrentAction" });
  ```
- Ni rectiva listeners globales, ni muta el action, ni hace RPC, ni monta UI persistente.

## Acción cliente creada
`static/src/js/replace_current_action.js` — módulo Odoo con `@odoo-module`, registrado vía `registry.category("actions")`, patrón idéntico a `display_notification`/`reload` del core local (funciones `(env, action)`).

## Registro de assets
`__manifest__.py` → `'assets': {'web.assets_backend': ['madenat_lumber_intake/static/src/js/replace_current_action.js']}`

## Cambios backend

### Apertura de origen (`intake_console.py:action_open_source`)
El `ir.actions.act_window` original se preserva íntegro y se envuelve:
```python
return {
    'type': 'ir.actions.client',
    'tag': 'madenat_lumber_intake.replace_current_action',
    'params': {'action_to_execute': action_window_original},
}
```

### Retorno a consola (`intake_guia_processing.py:action_back_to_intake_console`)
`_get_intake_console_action()` se mantiene como fuente canónica pura del `act_window` interno; el método público envuelve:
```python
inner = self._get_intake_console_action()
return {
    'type': 'ir.actions.client',
    'tag': 'madenat_lumber_intake.replace_current_action',
    'params': {'action_to_execute': inner},
}
```

## Contrato de acciones resultante
- Apertura: `ir.actions.client` con inner `act_window` (res_model, res_id, view_mode, view_id fachada, target current).
- Retorno: `ir.actions.client` con inner `act_window` consola (res_model `madenat.lumber.intake.console`, res_id `900000000+id`, view_id consola, target current, name canónico).
- Sin `no_breadcrumbs` en ninguna capa (verificado por tests).

## Pruebas creadas o actualizadas
`TestIntakeNavigationActions` (4): contrato apertura envuelta, contrato interno consola sin `no_breadcrumbs`, retorno público envuelto, contrato canónico.
`test_intake_wizard.py::test_t7` ajustado al inner del wrapper.

## Validación técnica
- `py_compile` OK (modelos + tests).
- `node --check` del JS: **OK**.
- `TestIntakeNavigationActions`: **4/4 PASS**.
- `TestIntakeWizard`: **7/7 PASS** (regresión verde tras ajustar t7 al wrapper).
- Sin `no_breadcrumbs`, sin modal, sin archivos fuera del alcance.

## UAT manual requerido
```
Sesión nueva. Abrir Ingreso Global → abrir guía 543 → Volver → repetir x3.
Esperado:
- dropdown sin acumulación de guías/consola repetidas por ciclo;
- consola abierta sin pantalla vacía;
- res_id 900000543 correcto;
- Back/Forward sin error crítico;
- formulario con cambios sin guardar conserva prompts estándar.
```

## Archivos modificados
- `madenat_lumber_intake/__manifest__.py`
- `madenat_lumber_intake/models/intake_console.py`
- `madenat_lumber_intake/models/intake_guia_processing.py`
- `madenat_lumber_intake/static/src/js/replace_current_action.js` (nuevo)
- `madenat_lumber_intake/tests/test_intake_navigation_actions.py`
- `madenat_lumber_intake/tests/test_intake_wizard.py`

## Archivos deliberadamente no modificados
- Core Odoo (ActionService, router, breadcrumbs), JS global, `madenat_lumber_core`, otros módulos.
- `display_name`, folios, `res_id` sintético, SQL view de consola, permisos, datos.

## Riesgos y limitaciones
- Back/Forward del navegador (UAT pendiente): `replaceCurrentAction` modifica la posición actual del historial; comportamiento similar al patrón nativo de stock/control_panel; se valida en UAT.
- Cambios sin guardar en la fachada: el reemplazo no omite protecciones; confirmar en UAT el flujo de save/discard.
- Se requiere UAT visual completa antes de declarar éxito funcional definitivo; los tests backend validan el contrato, no el dropdown.