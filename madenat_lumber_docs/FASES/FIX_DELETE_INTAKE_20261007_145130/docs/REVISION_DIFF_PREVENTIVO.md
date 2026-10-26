# REVISIÓN DEL DIFF PREVENTIVO DE RETORNOS (por ruta)

`02_preventive_return_fk.diff` añade `'guia_processing_id': False` a **tres** `create` de
retorno. Se revisa cada uno **por separado**. Doctrina de referencia: **G2/G3**
(CANON/04 §4.3) — `stock.picking.guia_processing_id` es la llave **exclusiva del ingreso de
producción**; «nunca se propaga a consumos (BT-04), retornos, recepción, rebaja, contenedor,
exportación ni inventario».

| Ruta | Método | Albarán creado | ¿Corresponde guía explícita? | Veredicto |
|---|---|---|---|---|
| **BT-04** | `_reverse_consumption_picking` | Retorno **entrante** del consumo de salida a proceso | **No** (es un retorno, no un ingreso de producción) | `False` correcto |
| **SV** | `_sv_reverse_*` (bloque `return_picking` del reversal por lote SV) | Retorno del receipt SV | **No** | `False` correcto |
| **Modo B** | `action_force_cancel` | Retorno de cancelación del ingreso | **No** | `False` correcto |

## Regla aplicada (para las tres)

* **Cuándo corresponde guía explícita:** solo al **crear el ingreso de producción** en
  `_get_or_create_picking_unified` (ya lo hace: `'guia_processing_id': self.id`).
* **Cuándo no corresponde ninguna:** en **todo** retorno (espejo de un picking), consumo,
  rebaja, contenedor, exportación o inventario → `guia_processing_id = False`.
* **Cómo impedir defaults accidentales sin perder atribución válida:** forzar el valor
  **explícito** `False` en `create`. El `False` explícito **gana** al `default_*` del
  contexto (Odoo solo rellena campos **ausentes**: `_add_missing_default_values` /
  `default_get`), así que neutraliza la fuga **sin** tocar el ingreso de producción.

## Por qué NO un cambio genérico

Se evaluó poner `default_guia_processing_id=False` en el `env` del asistente (Modo B). Se
**descartó** porque: (a) afectaría a **cualquier** `create` dentro del flujo (incluido el
ingreso de producción legítimo si algún flujo lo creara desde el asistente), y (b) no cubre
las rutas que no pasan por el asistente. El `False` **explícito y local** a cada retorno es
más seguro y no pierde atribución válida.

## Selección del picking original (hallazgo adicional)

Corregir solo el FK del retorno **no bastaba**: `action_force_cancel` seleccionaba los
albaranes a revertir por `origin == guia.name`, y podía revertir un **documento ajeno**
(caso real: receipt 436 de la recepción 1369). Se corrige en
`03_modo_b_selection.diff` con `_picking_is_foreign_document` (mismo criterio fuerte que la
eliminación: `reception_id` o lotes de otra recepción). Sin evidencia de pertenencia ajena,
el albarán **no** se descarta (no se pierde atribución válida por `origin`).

## Pruebas asociadas (ver `RESULTADOS_PRUEBAS.md`)

* `test_modo_b_does_not_reverse_foreign_picking` (ajeno, nº compartido).
* `test_modo_b_reverses_own_picking_without_fk_leak` (propio + contexto contaminado).
* `test_own_return_with_fk_still_blocks_modo_a` (retorno propio protegido).
* `test_l_context_default_leak_reproduced_and_prevented` (Fase 1: contexto limpio/contaminado).
