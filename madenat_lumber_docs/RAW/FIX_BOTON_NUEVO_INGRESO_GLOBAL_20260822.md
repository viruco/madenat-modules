# Fix — Botón Nuevo en Ingreso Global

## Problema observado
Tras el retorno a Ingreso Global (via `ir.actions.client` + `replaceCurrentAction`), la consola abría correctamente pero **no aparecía el botón "Nuevo"** que sí está presente al abrir el flujo desde el menú.

## Diferencia entre acción nativa y retorno
Evidencia por shell readonly (rollback):

| Atributo | Acción nativa (`action_madenat_lumber_intake_console`) | Retorno sintético (`_get_intake_console_action`, antes del fix) |
|---|---|---|
| `view_mode` | **`list,form`** | `form` |
| `view_id` | **lista consola** (1865) | form consola (1867) |
| `views` | (lista, form) | solo (form,) |
| `search_view_id` | 1866 | ausente |
| `help` | presente | ausente |
| `limit` | 80 | ausente |

## Causa técnica identificada
El retorno abría el **form** del registro sintético (`res_id=900000000+id`); la vista form tiene `create="false" edit="false"` (``intake_console_views.xml:54``). En la apertura desde menú, la consola arranca en **vista lista** (`view_mode='list,form'`), cuya toolbar de lista es la que expone el botón "Nuevo" (y permite el flujo de creación). El dict sintético no reproducía esa metadata funcional → Header sin "Nuevo".

## Cambio aplicado
`_get_intake_console_action()` (`intake_guia_processing.py`) ahora reproduce la metadata funcional de la acción nativa:
```python
'view_mode': 'list,form',
'view_id': console_list_view.id,
'views': [(console_list_view.id, 'list'), (console_form_view.id, 'form')],
'search_view_id': search_view.id,
'help': canonic.help,
'limit': canonic.limit or 80,
```
Se conservan: `type`, `name` canónico ("Ingreso Global"), `res_model`, `res_id=900000000+id`, `target='current'`. `res_id` se mantiene: la lista lo ignora como filtro (muestra las filas proyectadas por la vista SQL) y el form lo usa si el usuario abre un registro.

## Contrato final del retorno
- `type='ir.actions.act_window'` (inner del wrapper `ir.actions.client`).
- `name='Ingreso Global'` (canónico).
- `view_mode='list,form'`, `view_id`=lista, `views` mixtos, `search_view_id`, `help`, `limit=80`.
- `target='current'`, `res_id=900000000+id`.
- Wrapper: tag `madenat_lumber_intake.replace_current_action`, `stackPosition:"replaceCurrentAction"`.
- Sin `no_breadcrumbs`. Sin modal. Sin JS modificado. `replaceCurrentAction` intacto.

## Pruebas ejecutadas
- `TestIntakeNavigationActions` (4): **4/4 PASS — EXIT=0** (contract test verifica `view_mode='list,form'`, `view_id`=lista, `views[0]`=('list',), `search_view_id` y `limit`; wrapper test verifica inner con `view_mode='list,form'` y views mixtos).
- Regresión `TestIntakeWizard` (7): **7/7 PASS — EXIT=0**.
- `py_compile` OK en modelo y tests; JS sin cambios.

## Resultado esperado en UAT
- Al volver a Ingreso Global: header/UI indistinguible de la apertura desde menú.
- Botón **"Nuevo" presente** (toolbar de lista de la consola).
- Título "Ingreso Global"; sin breadcrumbs duplicados; sin pantalla vacía.
- La guía mantiene su identidad al abrirse desde consola.

## Riesgos y límites
- Si la lista de la consola (registo sintético) filtra por `res_id`, la lista podría mostrar solo ese registro; en el modelo SQL actual el `res_id=900000000+id` es el id canónico proyectado, el comportamiento es equivalente al menú (la vista SQL expone la fila). Confirmar en UAT.
- No se modificó XML de vistas, core Odoo, `display_name`, `stackPosition` ni el wrapper JS.
- Validación definitiva del botón en UI real queda para UAT (los tests backend validan el contrato de acciones).