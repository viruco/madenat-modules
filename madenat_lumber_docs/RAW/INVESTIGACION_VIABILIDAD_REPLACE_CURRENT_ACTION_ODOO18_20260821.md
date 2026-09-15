# Investigación de Viabilidad — Reemplazo de Action Stack Odoo 18

## Resumen ejecutivo
**Viable con frontend mínimo (acción cliente), sin patch global ni override de ActionService.** El core local expone `ActionOptions.stackPosition` (`"replaceCurrentAction" | "replacePreviousAction"`) y lo procesa en `_computeStackIndex()` (L771-800). Los patrones nativos están usados en al menos 4 archivos del código Odoo (control_panel.js, stock_forecasted.js, stock_orderpoint_list_controller.js). El backend no puede expresar estas opciones, por lo que un **`ir.actions.client` mínimo** puede recibir el action dict de apertura/retorno desde el método backend y llamar `actionService.doAction(action, {stackPosition: ...})` una sola vez.

## Alcance y restricciones
Solo lectura. No se implementó JS ni módulos. Evidencia del código local del contenedor `web`.

## Estado post-rollback
- `context.no_breadcrumbs` en retorno: **revertido** (falló UAT: navegación vacía).
- Retorno full-page funcional actual: `act_window` consola con `target='current'`, `res_id=900000000+id`.
- Repetición de guías persiste por `action.jsId` único por acción (causa raíz forense).

## API local de ActionService
- Firma pública: `actionService.doAction(action, options)`.
- Ejecución interna: L1581 `await doAction(action, options)` dentro de `executeAction`.
- `ActionOptions` (L68-74):
  - `clearBreadcrumbs: boolean`
  - `stackPosition: "replaceCurrentAction" | "replacePreviousAction"`
- Estas opciones **solo pueden provenir de una llamada JS** (`doAction`); el action dict backend no las transporta.

## ActionOptions y stackPosition
`_computeStackIndex(options)` (L768-800):
| Opción | Línea | Comportamiento |
|---|---|---|
| (ninguna) | 799-800 | `return controllerStack.length` → agrega al final (acumula) |
| `clearBreadcrumbs` | 771-772 | `return 0` → vacía el stack del contexto |
| `replaceCurrentAction` | 773-777 | `controllerStack.findIndex(ct => ct.action.jsId === currentController.action.jsId)` → **reemplaza el controller actual** |
| `replacePreviousAction` | 780-792 | Busca el jsId de la acción anterior distinta → la reemplaza |

## Simulación de stack por alternativa
Estado inicial: `[C0 consola]` → abrir guía → `[C0, G1 guía]`.

| Alternativa | Transición | Opción | Stack antes | Stack después | Controller eliminado |
|---|---|---|---|---|---|
| A. Reemplazar apertura | consola → guía | `replaceCurrentAction` | `[C0]` | `[G1]` | **C0** (consola eliminada del breadcrumb) |
| B. Reemplazar retorno | guía → consola | `replaceCurrentAction` | `[C0, G1]` | `[C0, C1']` | G1 (guía eliminada); consola reemplazada |
| B'. Reemplazar retorno | guía → consola | `replacePreviousAction` | `[C0, G1]` | `[C1']` | C0 y G1 → C1' |
| C. Ambos extremos | ida y vuelta | `replaceCurrentAction` en ambos | `[C0]→[G1]`, `[G1]→[C1]` | `[C1]` | ninguno acumulado |
| D. Volver a la anterior | guía → consola | `replacePreviousAction` | `[C0, G1]` | `[C0→C1']` | G1 → C1' |

**C es la única que elimina la acumulación en ambos sentidos** sin dejar consola vacía: en cada ida la consola se reemplaza por la guía, y en cada vuelta la guía se reemplaza por la consola. Resultado final: `[C_N]` con una sola entrada, sin duplicados y sin breadcrumb vacío.

## Router, URL y Back/Forward
- El router usa `pushState()` dentro de `updateActionState` (L730-734, `target !== 'new'`); `replaceCurrentAction` reemplaza el controller en el índice actual → la URL/state refleja la transición en la misma "posición" de historial.
- Riesgo: Back/Forward del navegador podría restaurar states anteriores al reemplazo; el patrón nativo (stock_forecasted, control_panel) lo usa en navegación interna sin romper el flujo.
- `clearBreadcrumbs` (L1080) tiene guard `noEmptyTransition`: no deja la interfaz vacía si hay una transición de salida.

## Formularios, guardado y discard
- `replaceCurrentAction` no pasa por FormController discard: es un reemplazo de controller del action_manager. Si la guía tiene cambios sin guardar, el comportamiento es el del action manager estándar (sin confirmación automática en la investigación; se documenta para UAT).
- El retorno full-page se preserva: la acción resultante sigue siendo `act_window` consola con `target='current'`.

## Patrones nativos localizados
- `web/static/src/search/control_panel/control_panel.js` — usa `replaceCurrentAction` para reabrir búsquedas.
- `web/static/src/webclient/actions/action_service.js` — define y procesa `stackPosition`.
- `addons/stock/static/src/views/stock_orderpoint_list_controller.js` — usa `replaceCurrentAction`.
- `addons/stock/static/src/stock_forecasted/stock_forecasted.js` — usa `replacePreviousAction`.

Los 4 son **código nativo Odoo**, no addons externos: patrón confirmado y soportado.

## Diseño mínimo viable
1. Backend: un método (ej. en `madenat_lumber_intake`) retorna `ir.actions.client` con tag custom tipo:
   ```python
   {'type': 'ir.actions.client', 'tag': 'madenat.act_window_replace',
    'params': {'action': <act_window dict de apertura o retorno>}}
   ```
2. Frontend (solo módulo `madenat_lumber_intake`): una acción cliente Owl/JS registrada en `registry.category('actions')` que:
   - recibe `action.params.action`;
   - llama `this.actionService.doAction(actionDict, {stackPosition: 'replaceCurrentAction'})` **una sola vez**;
   - sin patch global, sin listeners globales, sin override de ActionService.
3. Aplica el patrón a **ambos** extremos (opción C): apertura (guía) y retorno (consola).
4. Registro de assets JS vía manifest de `madenat_lumber_intake` (sin tocar otros módulos).

## Riesgos y compatibilidad
- **Alto como diseño si se aplica solo a un extremo**: ida reemplaza la consola (ya no hay breadcrumb de consola) o vuelta reemplaza la guía (user pierde referencia); la **opción C (ambos)** es la que mantiene la simetría.
- **Medio-Back/Forward**: reemplazar la posición actual altera el historial; requiere UAT con navegación atrás.
- **Medio-FormController**: confirmar que el reemplazo no interfiera con discard/save del formulario de la fachada; los patrones nativos (control_panel/stock) demuestran viabilidad operativa.
- Requiere JS/OWL mínimo en `madenat_lumber_intake` (no parche del web client).

## Decisión arquitectónica
**Viabilidad confirmada — Alternativa C: reemplazo del controller actual en ambos extremos del ciclo** mediante una acción cliente mínima (`tag` propio + `actionService.doAction(action, {stackPosition: 'replaceCurrentAction'})`), limitada a `madenat_lumber_intake`, sin patch global ni override de ActionService. El retorno full-page se conserva.

## Plan de implementación posterior
1. Crear acción cliente `madenat.act_window_replace` en `madenat_lumber_intake` (JS mínimo, registry actions).
2. Métodos backend de apertura/retorno retornan `ir.actions.client` con el `act_window` real en `params.action`.
3. UAT del ciclo completo x3: dropdown sin acumulación; consola no vacía; guía conserva su entrada en la ficha.
4. Tests backend del contrato de `ir.actions.client` (type/tag/params) — sin modificar el frontend en la fase de tests.
5. Verificación Back/Forward y discard de la fachada.

## Anexos técnicos
- `action_service.js`: L68-74 (`ActionOptions` typedef), L1581 (`doAction(action, options)`), L768-800 (`_computeStackIndex`), L1080 (`clearBreadcrumbs + noEmptyTransition`), L730-740 (router/pushState).
- Patrones nativos: `control_panel.js`, `stock_orderpoint_list_controller.js`, `stock_forecasted.js`.
- Sin consultas SQL nuevas; sin cambios a Python/XML/JS en esta tarea.