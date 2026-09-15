# Rollback — no_breadcrumbs en retorno a Ingreso Global

## Motivo del rollback
La implementación de `context={'no_breadcrumbs': True}` en `_get_intake_console_action()` **falló en UAT**:
- al entrar a "Modificar origen", la guía seguía repitiéndose;
- al volver a "Ingreso Global", la entrada desaparecía y la navegación quedaba **vacía/incorrecta**.

Conclusión: el retorno no debe ocultarse con `no_breadcrumbs`; el cambio se revierte completamente.

## Cambio revertido
- Eliminado `'context': {'no_breadcrumbs': True}` del diccionario retornado por `_get_intake_console_action()` en `madenat_lumber_intake/models/intake_guia_processing.py`.
- No se añadió ningún flag alternativo ni se movió lógica a otros métodos.

## Contrato de acción restaurado
```python
{
    'type': 'ir.actions.act_window',
    'name': <nombre de action_madenat_lumber_intake_console>,
    'res_model': 'madenat.lumber.intake.console',
    'res_id': 900000000 + self.id,
    'view_mode': 'form',
    'view_id': <view_madenat_lumber_intake_console_form>,
    'target': 'current',
}
```
(El key `context` ya no se emite en el retorno.)

## Pruebas ejecutadas
| Suite | Resultado |
|---|---|
| `madenat_lumber_intake:TestIntakeNavigationActions` (4 tests) | **4/4 PASS — EXIT=0** |
| Regresión `madenat_lumber_intake:TestIntakeWizard` (7 tests) | **7/7 PASS — EXIT=0** |

Tests actualizados: `test_get_intake_console_action_does_not_emit_no_breadcrumbs` (verifica ausencia del flag), `test_action_back_to_intake_console_delegates_correctly` (contrato funcional sin flag), contrato de acción intacto y no-regresión de `action_open_source`.

## Resultado
- Modelo revertido a comportamiento pre-cambio: el retorno restaura la entrada "Ingreso Global" en el breadcrumb (sin dejar la navegación vacía).
- `no_breadcrumbs` **no se aplica** ni al retorno ni a la apertura en este estado.
- Sistema funcional: `py_compile` OK y suites verdes.

## Riesgos remanentes
- La **repetición visual persiste** al abrir/modificar origen: cada `action_open_source` genera un controller nuevo con `action.jsId` único (comportamiento estándar del web client), por lo que el dropdown seguirá acumulando entradas de la guía en ciclos repetidos.
- La consola vuelve a mostrar su entrada "Ingreso Global" en cada retorno (comportamiento original).

## Próximo frente de corrección
```
La repetición visual persiste al abrir/modificar origen.
El siguiente análisis/corrección debe centrarse en la acción de apertura de la ficha/fachada y no en el retorno a consola.
```
Referencia: `INVESTIGACION_FORENSE_CONTROLADOR_STACK_RUTER_BREADCRUMBS_ODOO18_20260821.md` (causa raíz: `action.jsId` único por acción, sin dedupe por `res_model+res_id`).