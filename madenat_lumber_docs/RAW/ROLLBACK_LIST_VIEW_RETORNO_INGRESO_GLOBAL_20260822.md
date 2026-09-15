# Rollback — Vista Lista en Retorno a Ingreso Global

## Motivo del rollback
El cambio previo a `view_mode='list,form'` (para recuperar el botón "Nuevo") hizo que Odoo abriera la **lista** como vista inicial del retorno, **perdiendo la ficha/formulario operativa de Ingreso Global** que el usuario necesita para enviar a stock. UAT confirmó que la fachada/formulario es la vista funcional crítica.

## Comportamiento incorrecto detectado
- `view_mode='list,form'`, `view_id`=lista y `views=[(lista,'list'),(form,'form')]` hicieron que la primera vista (lista) fuera la inicial del retorno.
- Resultado: se recuperó "Nuevo" pero se perdió la pantalla/formulario de Ingreso Global para operar y enviar a stock.

## Contrato de formulario restaurado
`_get_intake_console_action()` (`intake_guia_processing.py`) ahora retorna:
```python
{
    'type': 'ir.actions.act_window',
    'name': canonic.name,               # 'Ingreso Global'
    'res_model': 'madenat.lumber.intake.console',
    'res_id': 900000000 + self.id,
    'view_mode': 'form',
    'view_id': console_form_view.id,
    'views': [(console_form_view.id, 'form')],
    'target': 'current',
}
```
Eliminados solo los elementos introducidos para forzar la lista: `list_view_id` como vista principal, `view_mode='list,form'`, `views` con lista al inicio, `search_view_id`, `help` y `limit`. `views` se mantiene (requerido por la client action para evitar el error `.map`).

## Client Action preservada
- Wrapper `ir.actions.client` con tag `madenat_lumber_intake.replace_current_action` y `params.action_to_execute` — intacto.
- `stackPosition: "replaceCurrentAction"` — intacto.
- Sin `no_breadcrumbs`; sin modal; título canónico "Ingreso Global"; JS y core Odoo sin cambios.

## Pruebas ejecutadas
- `TestIntakeNavigationActions` (4, actualizados al contrato form: `view_mode='form'`, `view_id`=form consola, `views=[(view_id,'form')]`, `'list' not in view_mode`): **4/4 PASS — EXIT=0**.
- Regresión `TestIntakeWizard` (7): **7/7 PASS — EXIT=0**.
- `py_compile` OK en modelo y tests.

## UAT manual requerido
```
Sesión nueva:
1. Abrir Ingreso Global.
2. Abrir una guía desde la consola.
3. Volver a Ingreso Global.
4. Confirmar que reaparece la ficha/formulario original de Ingreso Global (no la lista).
5. Confirmar que el flujo de envío a stock funciona y que no hay pantalla vacía.
6. Repetir tres ciclos.
7. Confirmar que no se acumulan breadcrumbs y que el título sigue siendo "Ingreso Global".
```

## Riesgo funcional pendiente
- El botón "Nuevo" queda **pendiente de una solución futura** que no sacrifique la fachada/formulario de Ingreso Global (por ejemplo, botón "Nuevo" en el header del form o en la fachada, fuera del alcance de este rollback).
- No se debe reintentar `view_mode='list,form'` en el retorno sin un rediseño que preserve la vista operativa.