# Fix — Cabecera de Guía Origen (botón "Nuevo" en ficha)

## Evidencia visual
- **Referencia (ficha procesada)**: `19827` + `1 / 1` + flechas, sin "Nuevo".
- **A corregir (guía origen)**: `[Nuevo] 19827 · COMERCIALIZADORA... [⚙] 1 / 1 [<] [>]`.

## Diferencia técnica entre acciones
`action_open_source()` (intake_console.py):
- `view_mode='form'`, `view_id`=fachada (1879), `views=[(1879,'form')]`, `res_id=543`, `target='current'`, `name=None` (usa display_name del modelo), **sin contexto**.
- La fachada `<form>` (intake_guia_processing_facade_views.xml L16) **no define `create="false"`** en el form raíz; el modelo `madenat.guia.processing` es creable → el header muestra "Nuevo".

## Causa de la cabecera distinta
`create` habilitado por defecto en la ficha de origen (modelo creable + fachada sin `create=false`). La pantalla de referencia oculta la creación; la apertura de la guía no la desactivaba.

## Cambio mínimo aplicado
En `action_open_source()` se añadió (solo apertura de guía, NO retorno):
```python
if not terminal:
    ctx = dict(action.get('context') or {})
    ctx['create'] = 0
    action['context'] = ctx
```
Preserva: edición, paginador `1 / 1`, flechas, título/display_name, pestañas y botones de negocio. `_get_intake_console_action()` intacto (form operativo de Ingreso Global).

## Pruebas ejecutadas
- `TestIntakeNavigationActions`: **4/4 PASS** (test apertura valida `context['create']==0`).
- Regresión `TestIntakeWizard`: **7/7 PASS**.
- `py_compile` OK; JS, XML, retorno a Ingreso Global y core sin cambios.

## Resultado esperado en UAT
Ficha de guía origen sin botón "Nuevo" (header consistente con la referencia `19827 1/1 [<][>]`), conservando Verificar Datos / Volver a Ingreso Global / pestañas (Guía y comercial, Proceso, Packing). Retorno a Ingreso Global → formulario operativo.

## Límites
- La validación final del header en UI real queda para UAT; los tests backend validan el contexto `create=0`.
- No se reintrodujo `no_breadcrumbs`, no se tocó `replaceCurrentAction`, no se sacrificó el formulario de Ingreso Global.