# Investigación Profunda — Action Stack y Breadcrumbs Odoo 18

## Resumen ejecutivo
El defecto de apilamiento de breadcrumbs en el ciclo Consola → Fachada → Volver tiene causa en el **action_service del web client**: cada acción `ir.actions.act_window` con `target != 'new'` y sin `_noBreadcrumbs` contribuye al historial/breadcrumb del controlador. La mitigación de nombre canónico no basta. El mecanismo **estándar y soportado por la instalación local** es el flag de contexto `no_breadcrumbs: True`, procesado por `action_service.js` (líneas 417-419 → `action._noBreadcrumbs` → línea 740 `viewProps.noBreadcrumbs`).

## Alcance y restricciones
Solo lectura. No se modificaron Python/XML/JS/datos; sin pruebas ni correcciones. Toda la evidencia proviene del código fuente local del contenedor `web`.

## Síntoma y evidencia visual
Dropdown con entradas alternadas:
`19827` (historial pre-enriquecimiento) y `19827 · … · ID 543` (post-enriquecimiento) más `Ingreso Global`, correspondientes al mismo `res_id=543` apilado por el router.

## Datos descartados como causa
- `SELECT id,name FROM madenat_guia_processing WHERE id=543` → 1 fila (543|19827).
- `search_count(name='19827')` → 1.
- No hay duplicados de base; el defecto es del cliente/stack.

## Mapa real de navegación MADENAT
| Paso | Pantalla | Modelo | res_id | Acción/Método | target | name |
|---|---:|---|---|---|---|---|
| 1 | Ingreso Global | `madenat.lumber.intake.console` | (SQL) | menú `action_madenat_lumber_intake_console` | — | Ingreso Global |
| 2 | Consola | idem | sintético | form consola | — | — |
| 3 | Fachada fuente | `madenat.guia.processing` | `source_res_id` (ej. 543) | `action_open_source` (intake_console.py:421) | current | display_name |
| 4 | Modificar origen | idem | 543 | botón facade | current | — |
| 5 | Volver | consola | `900000000+id` | `_get_intake_console_action` (intake_guia_processing.py:15) | current | canónico |

## Acciones backend auditadas
- `action_open_source`: `act_window` `target='current'`, sin `context` ni `no_breadcrumbs`.
- `action_back_to_intake_console`/`_get_intake_console_action`: `act_window` `target='current'`, con `name=canonic.name`, sin `context.no_breadcrumbs`.

## Arquitectura del web client Odoo 18
Archivo clave local: `/usr/lib/python3/dist-packages/odoo/addons/web/static/src/webclient/actions/action_service.js`
- `action.target = action.target || "current"` (L405): default.
- `viewProps.noBreadcrumbs = "_noBreadcrumbs" in action ? action._noBreadcrumbs : target === "new"` (L740): el controlador omite breadcrumb si `_noBreadcrumbs=true` o si es diálogo.
- `if ("no_breadcrumbs" in action.context) { action._noBreadcrumbs = action.context.no_breadcrumbs; delete action.context.no_breadcrumbs; }` (L417-419): **el backend puede enviar el flag vía context**.

## Semántica de target y breadcrumbs
| target | Breadcrumb | Stack | Uso |
|---|---|---|---|
| `current` (default) | Se muestra | Se acumula entrada | acción normal |
| `new` | `[]` (vacío) | Diálogo sin breadcrumb | modal |
| `main` | **NO SOPORTADO localmente** (sin coincidencias en action_service.js) | — | descartado |

`target='current'` **no evita el apilamiento**: reemplaza el contenido del contenedor actual pero el controlador sigue registrando la acción en el historial del router.

## Acciones, tags y flags soportados
- `context={'no_breadcrumbs': True}` → **confirmado en core** (L417-419 → L740): la acción no muestra breadcrumb.
- `replace_last_action`, `clear_breadcrumbs`, `clear_breadcrumb`, `history_back` → **sin evidencia en el código local** (grep sin resultados).
- `ir.actions.act_window_close` → existe como tipo en el core backend; su consumo JS no se verificó para `target='current'`; se aplica típicamente a diálogos.
- `home`, `display_notification`, `soft_reload` → fuera del alcance del defecto; no relevantes.

## Navegación atrás y cierre de acciones
No hay API backend estándar confirmada para "volver atrás" en esta instalación (sin `history_back` en el código local). El patrón estándar de Odoo para cerrar un diálogo es `ir.actions.act_window_close`; para una vista `target='current'` la vía limpia es **omitir breadcrumb** con `context.no_breadcrumbs`.

## Evidencia empírica no invasiva
Diccionarios auditados (backend MADENAT) tal como retornan hoy:
- `_get_intake_console_action()`: `{'type':'ir.actions.act_window','name':canonic.name,'res_model':'madenat.lumber.intake.console','res_id':900000000+id,'view_mode':'form','view_id':...consola_form,'target':'current'}` — **sin `context`**.
- `action_open_source()`: `{'type':'ir.actions.act_window','res_model':...,'res_id':...,'view_mode':'form','view_id':...facade,'target':'current'}` — **sin `context`**.

## Matriz de alternativas
| Alternativa | Soporte local | Limpia breadcrumb | Conserva UX full-page | Riesgo | Recomendación |
|---|---:|---|---:|---|---|
| Retorno con `target='current'` (estado actual) | confirmado | No (UAT) | Sí | Alto | Descartada |
| Retorno con `context={'no_breadcrumbs': True}` | **confirmado (L417-419→L740)** | Sí | Sí | Bajo | **Candidata principal** |
| `target='main'` | NO soportado | — | — | — | Descartada (sin respaldo local) |
| Fachada con `target='new'` | confirmado (diálogo) | Sí (breadcrumb vacío) | No necesariamente | Medio | Secundaria |
| Flag de reemplazo / `history_back` | Sin evidencia | — | — | — | No recomendada |
| JS custom | — | — | — | Alto | Último recurso |

## Decisión arquitectónica
**Opción C/D — Reemplazo estándar de acción (mínima)**: agregar `'context': {'no_breadcrumbs': True}` a la acción de retorno `_get_intake_console_action` (fuente única), de modo que el web client local (que consume ese flag en `action_service.js:417-419` y `viewProps.noBreadcrumbs` en L740) **no genere una nueva entrada de breadcrumb** para esa vuelta. Conserva `target='current'`, full-page, `res_id=900000000+id`, vista canónica y sin JS.

Verificación de criterios:
1. `type == 'ir.actions.act_window'` ✔ (se mantiene)
2. `res_model` consola ✔
3. `res_id=900000000+id` ✔ (determinista; sin evidencia de que sea incorrecto)
4. Vista consola correcta ✔
5. Nombre desde canónica ✔ (ya aplicado)
6. Sin nombres contradictorios ✔
7. `display_name`, `name`, folios, datos y SQL view intactos ✔
8. Sin side effects ✔
9. Sin JS custom ✔
10. Navegación atrás/adelante: el historial anterior persiste solo si el usuario navega por URL; la nueva vuelta no agrega breadcrumb ✔

**Limitación documentada:** `no_breadcrumbs` evita que la acción agregue breadcrumb, pero **no vacía entradas históricas ya acumuladas** en la pila actual. Para limpiar las entradas previas acumuladas se necesitaría recargar la sesión o navegación manual; eso es una limitación del diseño del web client (sin API de limpieza confirmada localmente), no un defecto del flag.

## Riesgos y compatibilidad
- Riesgo bajo: `no_breadcrumbs` es un flag core confirmado; no afecta datos ni otras rutas.
- La combinación `target='new'` + `act_window_close` queda como alternativa secundaria si el producto exigiera mantener la ficha de la fachada sin breadcrumb (UX distinta).
- No usar `target='main'` (no existe en la instalación local; la documentación web no aplica como fuente).

## Próximos pasos
1. (Implementación futura, no en esta tarea) Agregar `'context': {'no_breadcrumbs': True}` en `_get_intake_console_action` y en `action_open_source` (si se desea que la fachada tampoco agregue breadcrumb).
2. Tests de navegación: verificar que `context['no_breadcrumbs']` esté presente y que `viewProps.noBreadcrumbs` sea `true` (validación estática del dict de acción).
3. UAT del ciclo completo x3 para confirmar la ausencia de nuevas entradas y evaluar si la limpieza de entradas históricas es necesaria.

## Anexos técnicos
- Archivos Odoo core revisados: `addons/web/static/src/webclient/actions/action_service.js` (L405, L411, L417-419, L613-614, L659, L676, L679, L687, L734, L740, L822, L829, L838).
- Búsquedas: `target.*main|target.*current|target.*new`, `clear_breadcrumb|replace_last_action|no_breadcrumbs`, `act_window_close`, `history_back` (sin coincidencias para `main`/`history_back`/`replace_last_action`).
- Archivos MADENAT auditados: `intake_console.py:421-447`, `intake_guia_processing.py:15-49`, `intake_console_views.xml:272-280`.
- Consultas SELECT: 1 fila id=543; 1 fila name='19827'.
- Flag confirmado: `context.no_breadcrumbs` → `_noBreadcrumbs` → `viewProps.noBreadcrumbs` (soporte total del core).