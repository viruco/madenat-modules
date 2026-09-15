# Fix — Ocultar Duplicar en Ingreso Global

## Objetivo
Mantener el botón estándar **Nuevo** en la pantalla principal de Ingreso Global y ocultar **Duplicar** del menú de engranaje, solo en la vista form principal de la consola.

## Evidencia funcional
- Con `create="true"` (fix previo) el header mostraba "Nuevo" y, automáticamente, "Duplicar" en el engranaje.
- Duplicar una guía procesada/lista para stock produce una copia inconsistente; debe ocultarse.

## Vista afectada
`view_madenat_lumber_intake_console_form` (modelo `madenat.lumber.intake.console`), `intake_console_views.xml` L54.

## Cambio aplicado
```xml
<form string="Ingreso Global — Revisión" create="true" duplicate="false" edit="false">
```
(create="true" preservado; duplicate="false" incorporado; **delete NO se agregó** al form.)

## Comportamiento preservado
- Botón estándar **Nuevo visible** (create="true").
- "Duplicar **oculto**" (duplicate="false").
- Edit="false" intacto (la vista de revisión no edita en modo directo).
- Botones de negocio (Enviar a Stock, Modificar origen), menú de engranaje (Packing List / Guía Técnica) y navegación: sin cambios.
- Ficha de origen: `context['create']=0` preservada → sin "Nuevo" y, al no tener create=1, sin "Duplicar" automático; sin cambios.

## Comportamiento explícitamente no modificado
- `delete` NO se configuró: el form principal no declara delete; solo los `<list>` internos (L184/L198) mantienen `delete="false"` (comportamiento previo, documentado). **No se ocultó Eliminar** en esta tarea (requiere aprobación posterior).
- `action_open_source()`, `_get_intake_console_action()`, `action_back_to_intake_console()`, `replace_current_action.js`, `stackPosition`, `no_breadcrumbs`, res_id sintético: intactos.

## Validaciones técnicas
- XML válido (`ElementTree.parse`).
- Metadata de vista verificada por script: `CREATE=true | DUPLICATE=false | DELETE=None | EDIT=false`.
- `LISTS_DELETE_FALSE: False` (los list internos no declaran delete uniformemente — se documenta, no se modifica).
- Suites `TestIntakeNavigationActions` (4) y `TestIntakeWizard` (7): **todas PASS — EXIT=0**.

## Resultado esperado en UAT
1. "Nuevo" visible en Ingreso Global.
2. Engranaje sin "Duplicar".
3. "Packing List / Guía Técnica" disponible.
4. "Enviar a Stock" / "Modificar origen" visibles y funcionales.
5. Ficha de origen sin "Nuevo" (create=0).
6. Volver → formulario operativo + "Nuevo".
7. Tres ciclos + Back/Forward sin duplicados ni pantalla vacía.

## Riesgos y límites
- **Eliminar**: no fue modificado; si el menú expone "Eliminar" en la consola, validar en UAT el riesgo (eliminar una guía proyectada por la vista SQL tendría implicaciones) y decidir si ocultarlo en una tarea futura aprobada.
- La validación visual del engranaje (Duplicar oculto) queda para UAT; los tests/metadata validan el contrato de la vista.
- Solo XML de la vista de consola modificado; JavaScript y core intactos.