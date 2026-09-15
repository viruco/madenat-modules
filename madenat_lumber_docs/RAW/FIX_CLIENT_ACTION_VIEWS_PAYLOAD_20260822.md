# Fix — Payload `views` para Client Action de Reemplazo

## Error observado
Al ejecutar la client action `madenat_lumber_intake.replace_current_action` aparecía:

```text
UncaughtPromiseError > TypeError
Cannot read properties of undefined (reading 'map')
at _preprocessAction ...
```

Conclusión: el `actionToExecute` re-enviado a `actionService.doAction(...)` no tenía el key `views` (obligatorio en el contrato de `ir.actions.act_window` como lista de pares `(view_id, view_type)`), y `_preprocessAction` del core hace `action.views.map(...)`.

## Causa técnica
Los `act_window` internos construidos por backend incluían `view_id`/`view_mode` pero **no** el key `views`. Eran aceptados cuando el cliente lo resolvía desde la vista de acción servida por el backend, pero al re-enviar el dict vía client action → `doAction`, el preprocesador local espera `views` presente y explota al hacer `.map()` sobre `undefined`.

## Cambio aplicado
Solo backend (JS intacto — el problem era el payload):

`intake_console.py` → `action_open_source()`: el `act_window` interno ahora agrega
```python
action['views'] = [(action['view_id'], 'form')]
action['view_mode'] = action.get('view_mode', 'form')
```

`intake_guia_processing.py` → `_get_intake_console_action()`: el `act_window` canónico ahora incluye
```python
'views': [(console_form_view_id, 'form')],
```

## Contrato de acciones internas corregido
- Apertura: inner `act_window` con `type, res_model, res_id, view_mode='form', view_id=fachada, views=[(fachada,'form')], target='current'`.
- Retorno: inner `act_window` con `type, name canónico, res_model='madenat.lumber.intake.console', res_id=900000000+id, view_mode='form', view_id=consola_form, views=[(consola_form,'form')], target='current'`.
- Wrapper: `ir.actions.client` con tag `madenat_lumber_intake.replace_current_action` y `params.action_to_execute` — sin cambios.
- Sin `no_breadcrumbs` (verificado por tests).

## Pruebas ejecutadas
- `TestIntakeNavigationActions` (4): **4/4 PASS — EXIT=0** (asserts de `views` añadidos en apertura y retorno).
- Regresión `TestIntakeWizard` (7): **7/7 PASS — EXIT=0**.
- `py_compile` OK en modelos y tests; JS no modificado.

## Resultado
El payload interno de ambas acciones ahora cumple el contrato `ir.actions.act_window` y la client action puede re-ejecutarlo sin `TypeError: reading 'map'` en `_preprocessAction`. El mecanismo de reemplazo `stackPosition: "replaceCurrentAction"` se mantiene intacto.

## Riesgos remanentes
- Se requiere UAT visual del ciclo completo (ida/vuelta x3 + Back/Forward) para confirmar el comportamiento del dropdown; los tests backend validan el contrato, no el frontend.
- La client action depende de que cualquier action dict futuro que viaje por `params.action_to_execute` incluya `views` (contrato estándar de Odoo); documentado en el código.
- No se realizaron cambios a JS ni al mecanismo de reemplazo; el fix es exclusivamente del payload backend.