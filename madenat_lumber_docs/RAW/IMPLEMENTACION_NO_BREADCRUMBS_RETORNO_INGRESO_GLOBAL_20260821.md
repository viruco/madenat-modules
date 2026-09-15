# Implementación — Ocultar Breadcrumb del Retorno a Ingreso Global

## Objetivo
Evitar que cada "Volver a Ingreso Global" agregue una entrada visual "Ingreso Global" al dropdown de breadcrumbs, emitiendo el flag core `context.no_breadcrumbs` desde la acción canónica de retorno, sin ocultar la apertura de origen (conservar orientación).

## Alcance modificado
Único archivo funcional: `custom_addons/madenat_lumber_intake/models/intake_guia_processing.py`
Suite de pruebas: `custom_addons/madenat_lumber_intake/tests/test_intake_navigation_actions.py` (nueva)
Registro: `custom_addons/madenat_lumber_intake/tests/__init__.py`

## Cambio aplicado
En `_get_intake_console_action()` (fuente única canónica del retorno), se agregó:

```python
'context': {'no_breadcrumbs': True},
```

El flag se emite desde backend; el core local de Odoo 18 lo consume en `action_service.js` (L417-419 → `_noBreadcrumbs` → L740 `viewProps.noBreadcrumbs`). No se tocó `action_open_source` ni la fachada.

## Contrato de acción resultante
```python
{
    'type': 'ir.actions.act_window',
    'name': <nombre de action_madenat_lumber_intake_console>,
    'res_model': 'madenat.lumber.intake.console',
    'res_id': 900000000 + self.id,
    'view_mode': 'form',
    'view_id': <view_madenat_lumber_intake_console_form>,
    'target': 'current',
    'context': {'no_breadcrumbs': True},
}
```
Invariantes preservadas: type, modelo, fórmula `res_id`, vista canónica, `target='current'`, nombre canónico.

## Pruebas creadas o actualizadas
`TestIntakeNavigationActions` (4 tests):
1. `test_get_intake_console_action_contract` — type/res_model/res_id/target/view/name.
2. `test_get_intake_console_action_emits_no_breadcrumbs` — `context['no_breadcrumbs'] is True`.
3. `test_action_back_to_intake_console_delegates_with_flag` — delegación pública con flag y contrato idéntico.
4. `test_open_source_does_not_inherit_no_breadcrumbs` — la apertura NO incorpora el flag.

## Validación técnica
- `py_compile` OK en modelo y tests.
- Suite nueva: **4/4 PASS (EXIT=0)**: "0 failed, 0 error(s) of 4 tests".
- Regresión `TestIntakeWizard`: **7/7 PASS (EXIT=0)**.
- Solo cambiaron los archivos autorizados del alcance.

## UAT manual requerido
```
Precondición: sesión nueva (cerrar pestaña anterior). Entradas históricas no se eliminan.
1. Abrir Ingreso Global.
2. Abrir una guía desde la consola.
3. Usar "Volver a Ingreso Global".
4. Repetir 2-3 tres veces.
5. Abrir dropdown de breadcrumb.
Resultado esperado:
- La guía conserva su referencia visual (apertura no oculta).
- Cada retorno NO agrega una nueva entrada "Ingreso Global".
- No se crean registros nuevos.
- La consola abre el mismo res_id sintético y la vista esperada.
```

## Archivos modificados
- `madenat_lumber_intake/models/intake_guia_processing.py` (1 línea: contexto en helper)
- `madenat_lumber_intake/tests/test_intake_navigation_actions.py` (nuevo)
- `madenat_lumber_intake/tests/__init__.py` (registro)
- `madenat_lumber_docs/RAW/IMPLEMENTACION_NO_BREADCRUMBS_RETORNO_INGRESO_GLOBAL_20260821.md` (este informe)

## Archivos deliberadamente no modificados
- `action_open_source` (`intake_console.py`): se conserva orientación de la ficha; el flag no se hereda.
- XML (vista/fachada), JS, router, `target='new'/'main'`, flags no confirmados (`clear_breadcrumbs`, `replace_last_action`, `history_back`).
- `display_name`, `name`, folios, consola SQL, datos de negocio, permisos, dominios.

## Riesgos y limitaciones
- `no_breadcrumbs` oculta la entrada visible del retorno, pero el controller sigue existiendo en el action stack; las entradas históricas previas al despliegue no se eliminan retrospectivamente (se limpian al recargar la sesión).
- Back/Forward del navegador podría restaurar controllers sin breadcrumb visible; no se aborda por estar fuera del alcance (deuda técnica documentada del web client).
- La corrección es solo de navegación; no elimina duplicación documental (inexistente: 1 fila id=543 y 1 guía `19827`).