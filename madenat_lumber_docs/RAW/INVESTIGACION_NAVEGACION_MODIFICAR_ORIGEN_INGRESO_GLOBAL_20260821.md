# Investigación — Navegación “Modificar origen” → “Ingreso Global”

## Resumen ejecutivo
El problema es **mixto** (acciones backend + stack del cliente), con causa raíz principal en dos métodos de retorno de `madenat_lumber_intake`: `action_open_source` (consola) y `action_back_to_intake_console` (fachadas) retornan `ir.actions.act_window` con `target='current'` y **nombres/contextos distintos**, acumulando un stack de breadcrumbs sobre el mismo `res_id=543`. El dropdown mezcla `19827` (entrada previa al despliegue del nuevo `display_name`) y `19827 · ... · ID 543` (entradas posteriores) porque es la pila del action manager del web client.

## Alcance y restricciones
Solo lectura; no se modificó Python, XML, JS, datos, vistas ni acciones. Solo se usaron `SELECT` y lectura de código.

## Evidencia visual
Dropdown con: `19827` (etiqueta antigua, histórico del stack previo al `display_name` enriquecido) y varias `19827 · ... · ID 543` (mismo registro apilado tras ir y volver).

## Mapa de navegación
| Paso UI | Botón/acción | Tipo | Archivo:línea | Modelo destino | Acción retornada | Riesgo |
|---|---|---|---|---|---|---|
| Ingreso Global lista | `action_open_source` (botón) | object | intake_console_views.xml:67 | `source_model` (guia.processing) | `act_window` form `target:'current'`, `res_id=543`, `view_id=view_..._intake_facade_form` | Alto |
| Ficha “Modificar origen” | `action_back_to_intake_console` (botón) | object | intake_guia_processing.py:15 | `madenat.lumber.intake.console` | `act_window` form `name='Ingreso Global'`, `res_id=900000000+543`, `target:'current'` | Alto |
| Volver | — | — | intake_guia_processing_facade_views.xml:42 | — | — | — |

## Acciones y retornos auditados
- `action_open_source` (intake_console.py:421-447): `{'type':'ir.actions.act_window','res_model':self.source_model,'res_id':self.source_res_id,'view_mode':'form','target':'current','view_id':...facade}` — sin `name` (usa display_name del modelo).
- `action_back_to_intake_console` (intake_guia_processing.py:15-38): `{'type':'ir.actions.act_window','name':_('Ingreso Global'),'res_model':'madenat.lumber.intake.console','res_id':900000000+self.id,'view_id':...console_form,'target':'current'}` — `name` hardcodeado.

Ambos con `target='current'` y `res_id` distintos. `res_id` de consola es `900000000+id` (id canónico de la vista SQL); no colisiona con `543` pero **apila** entradas nuevas en el action manager cada vez que se navega.

## Validación de datos vs navegación
- `SELECT id,name,partner_id FROM madenat_guia_processing WHERE id=543` → **1 fila** (543 | 19827 | 676).
- `search_count([('name','=','19827')])` → **1 fila**.
- `display_name` Odoo para 543 → `19827 · COMERCIALIZADORA... · 02/10/2025 · Servicio Externo (...) · ID 543`.
- No hay duplicados de datos; el dropdown repite el **mismo ID 543** → confirmado problema de navegación/pila.

## Breadcrumbs y web client
Con la restricción de lectura se verificó que no existe JS custom de navegación en el addon (solo Python/XML). El dropdown del action manager del web client mantiene una pila; `target:'current'` reemplaza la vista actual pero **aparece** en breadcrumb como entry de historial; volver a “Ingreso Global” genera otra entrada. Esto explica la mezcla de etiquetas: la entrada antigua conserva el nombre previo (`19827`) y las posteriores el nuevo display_name.

## Hipótesis ordenadas
| Hipótesis | Evidencia a favor | En contra | Probabilidad | Acción futura |
|---|---|---|---|---|
| Stack/breadcrumb: el mismo `res_id=543` se apila con nombres distintos al ir/volver | `name` hardcode en `action_back_to_intake_console`; display_name nuevo en la fachada | — | Alta | Reemplazar el stack con `replace_last_action`/volver a menú canónico |
| Acciones inconsistentes | `action_open_source` sin `name`, `back_to` con `name` fijo | — | Alta | Unificar retorno |
| Datos duplicados | — | 1 fila id=543 | Baja (descartada) | — |
| JS custom/UI | sin JS encontrado | — | Baja | — |

## Alternativas de corrección
| Alternativa | Resuelve | Riesgo | Impacto | Recomendación |
|---|---:|---|---|---|
| A: Usar `target:'current'` sin `name` en `action_back_to_intake_console` y retornar el menú canónico de consola | ✔ | Bajo | Medio | ✔ recomendada |
| B: Unificar `action_open_source` con `name` igual al display_name del origen | ✔ parcial | Bajo | Medio | Complemento A |
| C: No modificar; solo limpiar breadcrumbs manualmente | ✖ | — | — | ✖ |
| D: JS custom para limpiar stack | ✖ | Alto | — | ✖ |

## Veredicto
**Opción 3 — Problema mixto**, con causa raíz backend confirmada: `action_open_source` y `action_back_to_intake_console` generan entradas de navegación inconsistentes (nombres distintos, `target:'current'`, `res_id` distintos) que el action manager del web client apila, produciendo el dropdown con mezcla de etiqueta vieja/nueva para el mismo registro 543.

## Próximos pasos propuestos
1. (Correctivo) Unificar retorno de “Volver a Ingreso Global” con una única acción canónica que abra la consola sin `name` hardcodeado.
2. (Consistencia) Hacer que `action_open_source` y `action_back_to_intake_console` produzcan el mismo nombre de breadcrumb (usando `display_name` del origen o el nombre de la acción de menú).
3. Opcionalmente usar `target:'current'` con `replace_last_action` para no apilar entradas al volver.

## Anexos — consultas SELECT ejecutadas
- `SELECT id,name,partner_id FROM madenat_guia_processing WHERE id=543` → 1 fila (543 | 19827 | 676).
- `search_count(name='19827')` → 1.
- display_name Odoo para 543 → etiqueta enriquecida (confirmada vía shell readonly con rollback).
- Código auditado: intake_console.py:421-447; intake_guia_processing.py:15-38; intake_guia_processing_facade_views.xml:42-45; intake_console_views.xml:67-70.