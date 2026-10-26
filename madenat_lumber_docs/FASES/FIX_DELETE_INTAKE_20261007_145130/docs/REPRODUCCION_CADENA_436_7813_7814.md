# ATRIBUCIÓN MATERIAL DE LA CADENA 436 → 7813 → 7814

Evidencia obtenida por **lectura** (SELECT) en la copia aislada `delint_test_20261007`
(que contiene la cadena real; idéntica a `madenat_test`). **No** se modificó ningún dato.

## Datos base

| Documento | id | name | origin | state | reception_id | guia_processing_id | tipo |
|---|---|---|---|---|---|---|---|
| Receipt | 436 | EMB-00227 | `15183` | done | **1369** | — | incoming |
| Retorno | 7813 | EMB-04201 | `Return of EMB-00227` | done | — | **33152** | incoming |
| Devolución | 7814 | WH/OUT/02754 | `Devolución de EMB-04201` | done | — | — | outgoing |

* Recepción **1369**: `name = '15183'`, `guia_numero = '15183'`, state `verified`.
* Guía **33152**: `name = '15183'`, state `cancelled`, **`tipo_recepcion = 'service'`**,
  `partner_id = 1052`, `consumption_picking_id` **vacío**, **0 lotes propios**.

### Movimientos y lotes

| Move | picking | nombre | qty | `origin_returned_move_id` | loc |
|---|---|---|---|---|---|
| 6420 | 436 | Lote: 0000000000439 | 50.863 | — | 4→18 |
| 14542 | 7813 | Return of Lote: 0000000000439 | 50.863 | **6420** | 18→4 |
| 14543 | 7814 | WH/OUT/02754 | 50.863 | **14542** | 4→18 |

Los tres moves llevan **los mismos 12 lotes (2614–2625)**. Todos esos lotes tienen
**`reception_id = 1369`** y **`guia_processing_id` NULL** → pertenecen a la **recepción**,
no a la guía.

## Respuestas a los puntos A–E

* **A. Qué documento originó materialmente cada operación.**
  436 = recepción **1369**. 7813 = **reversión de 436** (`origin_returned_move_id=6420`).
  7814 = **reversión de 7813** (`origin_returned_move_id=14542`). **Ninguna** operación se
  originó en la guía 33152.
* **B. ¿La guía tuvo movimientos propios antes de la cancelación?** **NO.** 0 lotes propios,
  0 pickings propios (`origin='15183'` solo devuelve 436, que es de la recepción),
  0 `stock.move` con `origin='15183'`, `consumption_picking_id` vacío.
* **C. ¿Modo B seleccionó un picking ajeno por origin compartido?** **SÍ.** El único
  candidato con `origin='15183'` es 436 (recepción 1369); `action_force_cancel` lo revirtió
  → **7813**. Defecto real de atribución textual (corregido en `03_modo_b_selection.diff`).
* **D. ¿El retorno heredó `guia_processing_id` exclusivamente del contexto?** **SÍ.** El
  `create` del retorno no fija `guia_processing_id`; el `env` del asistente arrastra
  `default_guia_processing_id`, y `default_get` lo inyecta (`models.py:1660-1665`,
  reproducido en `test_l` y `test_l_context_...`). Único origen del FK.
* **E. ¿Otras relaciones que vinculen el retorno a la guía?** **NO.** 7813 no tiene
  `reception_id`; sus lotes son de la recepción; su `origin` es `Return of EMB-00227`.
  El FK es la **única** relación con la guía, y es **espuria**.

## Dependencias de la guía 33152 (lectura)

| Categoría | Cantidad |
|---|---|
| lotes propios | 0 |
| pickings propios | 0 |
| movimientos con `origin='15183'` (propios) | 0 |
| `madenat.sv.operation` | 0 |
| `stock.lot.cost.line` (`Servicio 15183`) | 0 |
| `stock.valuation.layer` (lotes guía) | 0 |
| `stock.quant` (lotes guía) | 0 |
| `mail.message` (evidencia) | 5 |
| `ir.attachment` (evidencia) | 4 |
| **vínculo directo FK (retorno 7813)** | **1** |

> **Conclusión material:** la guía 33152 **no tiene ninguna dependencia material ni
> financiera propia.** El **único** bloqueador es el **FK espurio** del retorno 7813.
> La evidencia (5 mensajes + 4 adjuntos) es **documental** (se relaja solo en Modo A en
> entorno de test; en producción bloquearía).

## Clasificación del vínculo (ni “incorrecto porque impide borrar” ni “válido porque existe”)

El FK **no** se declara incorrecto por conveniencia: se declara incorrecto porque (1) el
retorno **no** es un ingreso de producción de la guía (doctrina G2: el FK es exclusivo del
ingreso de producción), (2) su cadena material pertenece a la **recepción 1369**, y (3) su
origen operativo es una reversión de un albarán **ajeno** (436). Es exactamente el caso F
del matriz (`vínculo directo aparentemente contradictorio`).
