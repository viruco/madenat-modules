# Investigación Forense — Controller Stack, Router y Breadcrumbs Odoo 18

## Resumen ejecutivo
La acumulación de entradas en el dropdown/breadcrumb no es un defecto de datos ni del router por sí solo: es el comportamiento estándar del **action stack** del web client. `action_service.js` asigna a cada acción un `action.jsId` único incremental (`action_${++id}`, L403) y **no deduplica por `res_model+res_id`**; por tanto, cada apertura de la misma ficha (`res_id=543`) crea un controller nuevo con `jsId` distinto (L376). El label se congela en la creación (`displayName: action.display_name || action.name || ""`, L759), lo que explica las entradas `19827` (pre-enriquecimiento) y `19827 · … · ID 543` (post-enriquecimiento).

## Alcance y restricciones
Solo lectura. No se modificaron Python/XML/JS/datos. Evidencia obtenida del código local del contenedor `web` y consultas SELECT previas.

## Síntoma reproducido
Ciclo `Ingreso Global → Abrir origen → Modificar origen → Volver` x3 produce en el dropdown: `19827`, `19827 · … · ID 543`, `Ingreso Global`, repetidos por la acumulación de controllers.

## Datos descartados
- id=543 única fila; name='19827' única; sin duplicados de base.
- No se descarta el `display_name` enriquecido; se descarta como causa de **acumulación** (solo explica diferencia de etiquetas).

## Inventario del flujo MADENAT
| Evento | Botón/método | Acción | target | jsId nuevo | Controller nuevo |
|---|---|---|---|---|---|
| Ingreso Global menú | `action_madenat_lumber_intake_console` | act_window | list,form | sí | sí |
| Abrir origen | `action_open_source` (intake_console.py:421) | act_window facade | current | sí | sí |
| Modificar origen | botón facade (tipo object) | act_window fachada | current | sí | sí |
| Volver | `_get_intake_console_action` (intake_guia_processing.py:15) | act_window consola | current | sí | sí |

## Acciones backend y payloads
Payloads normalizados auditados (sin `context` actual):
- `action_open_source`: `{type, res_model, res_id, view_mode:'form', view_id:facade, target:'current'}` — sin `context.no_breadcrumbs`.
- `_get_intake_console_action`: `{type, name:canonic.name, res_model:'madenat.lumber.intake.console', res_id:900000000+id, view_mode:'form', view_id:consola_form, target:'current'}` — sin `context.no_breadcrumbs`.

## Controller Stack del web client
- `_makeController` (L370-376): `jsId = "controller_" + (++id)`; cada acción genera controller único.
- `_preprocessAction` (L393-403): `action.jsId = "action_" + (++id)` — **sin dedupe por res_id**.
- `_computeStackIndex` (L770-800):
  - `options.clearBreadcrumbs` → `return 0` (vacía stack del contexto);
  - `options.stackPosition === "replaceCurrentAction"` → reemplaza la actual;
  - `options.stackPosition === "replacePreviousAction"` → reemplaza la anterior.
  - Estas opciones son **solo frontend** (`ActionOptions` de `doAction`), no se pueden expresar desde un action dict backend.
- `action.jsId` es la identidad usada para dedupe/restore (L777-793, L931-949).

## Router y Browser History
No se encontró `router.pushState`/`history.pushState` directo en el flujo auditado; el router usa `pushState()` dentro de `updateActionState` (L730-734) para `target !== 'new'`. Cada acción con jsId nuevo produce una entrada de historial/state.

## Dropdown y origen de etiquetas
- Label = `displayName` del controller (L759): `action.display_name || action.name || ""`.
- Entrada `19827` simple: controller creado **antes** del despliegue del `_compute_display_name` (label congelado) o con `name` sin `display_name`.
- Entrada `19827 · … · ID 543`: controller creado **después** del despliegue (label enriquecido).
- Entrada `Ingreso Global`: retorno a consola (`name=canonic`).
- Repeticiones del mismo `ID 543`: cada `action_open_source` genera `action.jsId` nuevo → controller nuevo.

## Auditoría de Modificar origen
- Botón tipo `object` en `intake_guia_processing_facade_views.xml`; ejecuta `action_back_to_intake_console` → act_window consola.
- No se detectaron acciones secundarias, `ir.actions.server`, redirects ni JS custom en el flujo (revisados módulos MADENAT).

## Contextos y acciones invisibles
- `context.no_breadcrumbs` es el único flag core confirmado para ocultar breadcrumb (L417-419 → L740).
- No hay `clear_breadcrumbs`, `replace_last_action`, `history_back` consumidos por el core local (grep sin resultados).
- `context.active_id`, `source_model`/`source_res_id` no provocan navegación adicional (solo datos para los métodos).

## Vistas y acciones duplicadas
- 1 vista form principal de Procesados (core), 1 fachada de Intake, 1 de Producto; la consola usa 1 definición.
- 1 acción canónica de consola (`action_madenat_lumber_intake_console`); sin acciones server distintas para el ciclo.

## Sesión, assets y caché
- La mezcla `19827` simple vs enriquecido corresponde a controllers creados antes/después del despliegue del `_compute_display_name`, ambos coexistiendo en el stack de la misma sesión (comportamiento normal del stack: no re-deriva labels viejos).
- Sin Service Worker/instancias múltiples detectadas; no se realiza validación en incógnito por restricción.

## Secuencias aisladas A/B/C (sesión nueva)
**Hallazgo estructural**: "Modificar origen" es la **pantalla** de la fachada (`intake_guia_processing_facade_views.xml`), no un botón con lógica propia. El **único botón** de la fachada es "Volver a Ingreso Global" (líneas 42-45) → `action_back_to_intake_console`.

| Secuencia | Pasos | Controllers nuevos esperados | Atribución |
|---|---|---|---|
| A | menú → abrir origen (`action_open_source`) | 1 guía enriquecida | `action_open_source` |
| B | A + pantalla fachada (sin botón extra) | 0 adicionales (fachada = misma vista) | ninguno |
| C | B + botón "Volver" (`action_back_to_intake_console`) | 1 consola "Ingreso Global" | `action_back` |

Cada ciclo completo agrega **exactamente 2 controllers** (guía + consola); el botón "Volver" solo es el generador de la entrada de consola. No hay tercera acción oculta.

## Payload RPC real (capturado con rollback en odoo shell)
```python
# action_open_source() sobre consola sin\'tética 900000543
ACT_ {'type': 'ir.actions.act_window', 'res_model': 'madenat.guia.processing',
      'res_id': 543, 'name': '-', 'target': 'current', 'view_mode': 'form'}
CTX_ (sin context)

# action_back_to_intake_console() sobre guía 543
ACT_ {'type': 'ir.actions.act_window', 'res_model': 'madenat.lumber.intake.console',
      'res_id': 900000543, 'name': 'Ingreso Global', 'target': 'current', 'view_mode': 'form'}
CTX_ (sin context)
SRC_NO_BREADCRUMBS_BD: False False
```
**Conclusión RPC**: `no_breadcrumbs` **no llega al cliente** porque el backend **no lo emite** (ambos payloads carecen de `context`; confirmado `False False`). No se pierde ni se reescribe en ninguna capa intermedia: simplemente no existe en el payload actual. El core lo procesaría intacto si se agregara (verificado en L417-419 de `action_service.js`).

## Línea temporal instrumentada
| Paso | URL/hash | Entrada nueva | Etiqueta | Causa (jsId) |
|---|---|---|---|---|
| 1. menú consola | hash consola | sí | `Ingreso Global` | `action_N` |
| 2. abrir origen | hash guia | sí | `19827 · … · ID 543` | `action_N+1` |
| 3. pantalla fachada | hash guia | no | (misma vista) | — |
| 4. volver | hash consola | sí | `Ingreso Global` (segunda) | `action_N+2` |
| 5-8. ciclo x2 | repetido | 2 entradas por ciclo | repetidas | `action_N+3..+6` |

## Árbol de causa raíz
```
Síntoma: entradas repetidas visuales del mismo res_id
├── A: action.jsId único por acción (L403) → nueva entrada por cada apertura
│   Evidencia: _preprocessAction asigna id incremental; sin dedupe por res_model+res_id
│   Estado: CONFIRMADA
├── B: displayName congelado (L759) → etiquetas viejas vs nuevas
│   Evidencia: displayName: action.display_name || action.name
│   Estado: CONFIRMADA
├── C: no_breadcrumbs (L417-419→L740) — no evita crear controller; solo oculta label
│   Estado: PROBABLE (limita visual, no stack)
├── D: dedupe/res_uso — no implementado en core
│   Estado: CONFIRMADA AUSENTE
└── Causa raíz final: TODO controller nuevo con jsId único se agrega al stack; el dropdown del breadcrumb lo representa. Sin dedupe por res_id y sin opción backend para replace/clear, cada ida/vuelta agrega entrada.
```

## Alternativas evaluadas
| Alternativa | Causa que corrige | Soporte local | Efecto stack | Riesgo UX | Riesgo técnico | Recomendación |
|---|---|---|---|---|---|---|
| `context.no_breadcrumbs` en retorno | oculta el label (no stack) | L417-419→L740 | reduce entradas visibles | Bajo | Bajo | Recomendada (complemento) |
| `context.no_breadcrumbs` en apertura y retorno | oculta ambos labels | idem | reduce visual duplicado a 0 entradas de este ciclo | Bajo | Bajo | **Principal** |
| `target='new'` (fachada modal) | genera controllers sin breadcrumb (L740) | confirmado (diálogo) | no agrega breadcrumb | Medio (layout) | Medio | Secundaria |
| Opciones `clearBreadcrumbs`/`replaceCurrentAction` | limpiar/reemplazar stack | solo JS `doAction` (no backend) | — | — | Alto (requiere JS custom/parche) | Descartada |
| JS custom/parche router | stack | — | — | — | Alto | Último recurso |
| `target='main'` | — | NO soportado (sin evidencia local) | — | — | — | Descartada |

## Decisión arquitectónica
Causa raíz confirmada: **cada acción genera `action.jsId` único y no hay dedupe por `res_model+res_id`**. La corrección mínima y sin JS es aplicar `context={'no_breadcrumbs': True}` a **ambas** acciones del ciclo (`action_open_source` y `_get_intake_console_action`), para que el dropdown del breadcrumb **no muestre entradas nuevas** de este ciclo. `no_breadcrumbs` no elimina controllers del stack ni entradas históricas previas; para el ciclo futuro queda sin entradas visuales duplicadas, y las previas desaparecen con la recarga.

## Plan de implementación posterior
1. Agregar `'context': {'no_breadcrumbs': True}` en `_get_intake_console_action` y en `action_open_source` (backend).
2. Tests backend: verificar que ambas acciones incluyen `context['no_breadcrumbs']`.
3. UAT del ciclo x3 en sesión nueva: dropdown sin entradas del ciclo; entradas previas se limpian con recarga.
4. Si UX exige limpiar el stack sin recarga, evaluar una acción `ir.actions.client` con tag estándar **después de validar su soporte local** o aceptar la limitación documentada.

## Riesgos y límites
- `no_breadcrumbs` oculta la entrada pero no elimina el controller del stack; Back/Forward del navegador podría restaurar controllers sin breadcrumb visible.
- No se pudo instrumentar URL/hash en DevTools (restricción de solo lectura); la línea temporal usa observación de código.

## Anexos técnicos
- Core: `action_service.js` — L370-376 (`_makeController`), L393-403 (`_preprocessAction`/`jsId`), L417-419 (`no_breadcrumbs`), L730-740 (`updateActionState`, `viewProps.noBreadcrumbs`), L759 (`displayName`), L770-800 (`_computeStackIndex`), L777-793, L931-949, L1199-1214.
- MADENAT: `intake_console.py:421-447`, `intake_guia_processing.py:15-49`, `intake_console_views.xml:272-280`, `intake_guia_processing_facade_views.xml:42-45`.
- Greps: `target.*main|target.*current|target.*new`, `clear_breadcrumb|replace_last_action|no_breadcrumbs`, `act_window_close`, `history_back`, `controllerStack`, `jsId`, `display_name` (resultados citados).
- SELECT: id=543 única; name='19827' única.
- Limitación: no se realizó instrumentación de navegador por restricción de solo lectura; no se auditaron addons OCA/Enterprise adicionales (no presentes/no aplicables en esta instalación).