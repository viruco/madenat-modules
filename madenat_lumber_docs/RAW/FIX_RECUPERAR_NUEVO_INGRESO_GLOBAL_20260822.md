# Fix — Recuperar botón Nuevo en Ingreso Global

## Problema observado
La pantalla principal de Ingreso Global (ficha form de la consola, donde se ejecuta "Enviar a Stock") no mostraba el botón estándar **Nuevo**.

## Comparación entre pantalla principal y ficha de origen
| Aspecto | Pantalla principal de consola | Ficha de origen (guía) |
|---|---|---|
| Vista | `view_madenat_lumber_intake_console_form` | fachada `intake_guia_processing_facade_views.xml` |
| create en vista | **`create="false"`** (antes del fix) | sin `create="false"` en form raíz |
| create en contexto | ninguno | `context['create']=0` (fix previo, correcto) |

## Causa técnica
**Hipótesis B confirmada**: la vista **form principal de la consola** tenía `create="false"` (L54 de `intake_console_views.xml`). Ese atributo ocultaba el botón "Nuevo" en la pantalla principal por metadata de la vista, no por contexto ni por la client action. No se hereda `create=0` desde la ficha de origen (son vistas distintas).

## Cambio aplicado
`views/intake_console_views.xml` L54: `create="false"` → `create="true"` en el form principal de la consola.
- La ficha de **origen** (guía) sigue con `context['create']=0` en `action_open_source()` — **sin cambios**.
- El retorno a Ingreso Global (`_get_intake_console_action()`) queda intacto: `view_mode='form'`, `views=[(form,'form')]`, `res_id=900000000+id`, `target='current'`, sin `no_breadcrumbs`, sin `list,form`.

## Tests ejecutados
- `TestIntakeNavigationActions`: **4/4 PASS — EXIT=0** (incluye `test_open_source_wraps_in_client_action` con `context['create']==0` y `views` explícito).
- Regresión `TestIntakeWizard`: **7/7 PASS — EXIT=0**.
- `py_compile` OK en modelos; XML validado con `ElementTree.parse`.

## Resultado esperado en UAT
- Pantalla principal de Ingreso Global: botón estándar **"Nuevo" visible** (create habilitado en la vista form de consola).
- Ficha de origen: **sin "Nuevo"** (context `create=0` preservado).
- Retorno a Ingreso Global: formulario operativo + "Nuevo" visible.
- Sin breadcrumbs duplicados; sin pantalla vacía; `replaceCurrentAction` intacto.

## Riesgos y límites
- La creación desde la consola abrirá un registro nuevo del modelo consola (vista SQL); validar en UAT el comportamiento de "Nuevo" en una vista form SQL si corresponde (la vista form ya tiene `edit="false"`; `create="true"` permite el botón estándar).
- La validación visual del botón en UI real queda para UAT; los tests backend validan contrato de acciones y metadata de vista.
- No se tocó core Odoo, JS, `_get_intake_console_action()` ni `action_open_source()`.