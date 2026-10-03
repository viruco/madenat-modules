# Reporte de implementación: lotes repetidos en packing de recepción directa

## 1. Resumen ejecutivo

Se corrigió `LumberReceptionService` (flujo de Recepción directa) para que varias filas de staging que comparten el mismo número de lote generen **un único `stock.lot`** y **una `stock.move.line` por fila de staging**, preservando el detalle físico (largo, piezas, volumen) de cada fila sin violar la unicidad estándar de Odoo `UNIQUE(product_id, name, company_id)`.

La causa raíz era un índice local (`existing_index`) construido una sola vez y nunca actualizado tras cada `stock.lot.create()`, lo que hacía que dos filas con la misma clave `(name, product_id)` intentaran crear dos `stock.lot` idénticos dentro de la misma transacción → `IntegrityError`.

## 2. Estado Git antes / después

- **Rama:** `backup/wip-20260819-intake-alignment` (sin cambios).
- **Antes:** cambios sin commitear preexistentes de sesiones anteriores (`madenat_lumber_intake`, `madenat_lumber_logistics`, `madenat_lumber_purchasing`, docs, `madenat_ingestion_engine/` sin trackear). **No se sobrescribió nada.**
- **Después (solo esta tarea):**
  - `madenat_lumber_core/models/reception_service.py` (modificado)
  - `madenat_lumber_core/tests/test_lumber_reception.py` (modificado, tests 15–20 agregados)

## 3. Causa raíz (confirmada, con archivo:línea)

`LumberReceptionService.create_lots_from_staging` (`reception_service.py`, método que arrancaba en la línea 17) construía `existing_index` una sola vez a partir de los lotes ya persistidos (vacío para recepción nueva) y **no lo actualizaba** tras `StockLot.create(lot_vals)` dentro del bucle. Dos líneas con la misma clave `(lot_name, product_id)` caían ambas en `create` → colisión `UNIQUE` de `stock.lot`.

## 4. Comportamiento funcional implementado

- **Normalización de nombre** sin alterar el valor guardado/mostrado: `(line.lot_name or '').strip()`.
- **Clave de identidad explícita:** `(product_id, normalized_lot_name, company_id)`.
- **Agrupación previa** de staging por clave y **validación de compatibilidad** de atributos de nivel de lote (espesor, ancho, nominales, subproducto) antes de escribir stock.
- **Create-or-get idempotente** por grupo, acotado a `reception_id = self.id`, con `savepoint` + `flush`/`invalidate` + re-búsqueda ante `IntegrityError`/`ValidationError`.
- **Auditoría** por lote en `madenat.audit.log` (`lot_creation` / `lot_update`), usando el contrato de recepción (`reception_id` + `batch_id`).
- **`create_stock_picking`**: una `stock.move` por lote (cantidad total) y **una `stock.move.line` por fila de staging** (cantidad por fila), todas con el mismo `lot_id`.
- Totales consolidados del lote: `piezas = suma`, `volume_purchase_m3 = suma`, `vol_shipment_m3 = suma`; `largo_m` queda como valor representativo de la primera fila (limitación documentada del modelo, el detalle vive en staging + move.lines).

## 5. Comparación con Procesados

- **Reutilizado (principios):** búsqueda previa con `flush_model`, `savepoint` + `invalidate` + re-búsqueda tras colisión, reutilización (`write`), auditoría de outcome.
- **Deliberadamente NO copiado:** filtro `reception_id=False` y exclusividad `guia_processing_id`↔`reception_id` (específicos de Procesados). En Recepción el discriminador canónico es `reception_id = self.id`.

## 6. Archivos modificados y justificación

| Archivo | Cambio | Justificación |
|---|---|---|
| `madenat_lumber_core/models/reception_service.py` | Reescritura de `create_lots_from_staging` + 4 helpers + `create_stock_picking` | Punto mínimo del Gate 3 que crea lotes/moves; arregla la colisión y preserva detalle |
| `madenat_lumber_core/tests/test_lumber_reception.py` | Tests 15–20 | Regresión del caso y de las protecciones |

## 7. Diferencia funcional antes / después

| | Antes | Después |
|---|---|---|
| Dos filas mismo lote | `IntegrityError` (2 × `stock.lot.create`) | 1 `stock.lot` + 2 `stock.move.line` |
| Detalle por fila | 1 `move.line` por lote (colapsado) | 1 `move.line` por fila (volumen por fila) |
| Colisión concurrente | sin manejo | `savepoint` + re-búsqueda + reutilización |
| Auditoría por lote | solo GB-1 | `lot_creation`/`lot_update` por lote |

## 8. Diagrama de secuencia (Gate 3 con lote repetido)

```
action_confirm_reception (lumber_reception.py:2741)
  → _create_lots_from_packing (2842) → LumberReceptionService.create_lots_from_staging
      ├─ agrupar staging por (producto, lote normalizado, compañía)
      ├─ validar compatibilidad de atributos de nivel lote (UserError si difieren)
      ├─ por grupo: _create_or_get_reception_lot (search reception_id + savepoint + re-search)
      └─ _audit_lot (lot_creation / lot_update)
  → create_stock_picking
      ├─ por grupo: 1 stock.move (qty total)
      └─ por fila de staging: 1 stock.move.line (qty de la fila, mismo lot_id)
```

## 9. Invariantes de seguridad y trazabilidad comprobados

1. Unicidad estándar `UNIQUE(product_id, name, company_id)` **intacta** (no se tocó `stock.lot.create()` global).
2. `stock.lot.reception_id` sigue siendo el vínculo canónico; nunca `guia_processing_id`.
3. Un lote de otra recepción o de Procesados **no** se reutiliza ni sobrescribe (fail-safe por re-búsqueda acotada a `reception_id`).
4. Escritura de stock solo en Gate 3.
5. Idempotencia: reproceso reutiliza el lote de la misma recepción sin duplicar.
6. Compatibilidad: atributos de nivel de lote incompatibles → `UserError` sin residuos.

## 10. Casos de prueba, comandos y resultados

**Comando (base temporal/aislada, no `madenat_test`):**

```bash
docker compose run --rm web odoo -c /etc/odoo/odoo.conf -d madenat_test_lotes_tmp \
  -i madenat_lumber_core --test-enable --test-tags=madenat_lumber_core \
  --stop-after-init --workers=0 --log-level=info
```

**Resultados (test_lumber_reception):**

| Test | Resultado |
|---|---|
| `test_15_repeated_lot_single_lot_two_move_lines` | PASS (1 lote, 2 move.lines mismo lot_id) |
| `test_16_repeated_lot_incompatible_width_raises` | PASS (UserError sin residuos) |
| `test_17_reception_does_not_reuse_other_reception_lot` | PASS (fail-safe) |
| `test_18_reception_does_not_reuse_guia_lot` | PASS (protección entre flujos) |
| `test_19_distinct_lots_remain_two_lots` | PASS (regresión) |
| `test_20_repeated_lot_idempotent_reprocess` | PASS (idempotencia) |

`madenat_lumber_core` → **0 failures, 0 errors** en `test_lumber_reception`. El run completo (106 tests) reportó 3 errores **preexistentes** en `test_guia_processing.py` (`TestGuiaProcessingIngestionProfileLock.test_03/04/05`, `product_id` NOT NULL en `madenat_guia_processing_line`), **ajenos a este cambio**.

## 11. Riesgos residuales y decisiones pendientes

- **Semántica física de lote/tarja:** confirmar con negocio si "mismo `lot_name` + distinto largo/piezas" es UNA tarja con dos medidas (asumido por evidencia dimensional) o DOS tarjas. La regla de compatibilidad actual lo permite solo si espesor/ancho/subproducto coinciden.
- **`stock.lot.largo_m`/`piezas` en lote multi-fila:** se consolidan `piezas`/volúmenes (suma) y `largo_m` queda representativo (primera fila). La verdad de detalle vive en staging + `stock.move.line`. Requiere confirmación si reportes/costeo leen `largo_m` como único valor.

## 12. Plan de rollback

Revertir el diff de `madenat_lumber_core/models/reception_service.py` y `madenat_lumber_core/tests/test_lumber_reception.py` restaura el comportamiento previo. No hubo migraciones ni cambios de esquema.

## 13. Confirmación de no-modificación de datos de negocio

No se ejecutó `action_confirm_reception` ni `create`/`write`/`unlink` sobre la recepción 15183 u otros registros de `madenat_test`. No se ejecutó SQL de escritura. La validación se realizó sobre la base temporal `madenat_test_lotes_tmp`, eliminada al final.

## 14. Extractos relevantes del diff

**`reception_service.py`** — imports:
```python
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round
from psycopg2.errors import IntegrityError
```

**`reception_service.py`** — nuevo flujo de `create_lots_from_staging` (agrupación + create-or-get) y helpers `_check_lot_compatibility`, `_build_lot_vals`, `_create_or_get_reception_lot`, `_audit_lot`; y `create_stock_picking` emitiendo una `stock.move.line` por fila de staging.

**`test_lumber_reception.py`** — tests `test_15` a `test_20` (detalle en el propio archivo).

---

```text
IMPLEMENTACIÓN COMPLETADA.
UNICIDAD ESTÁNDAR DE ODOO: PRESERVADA.
RECEPCIÓN DIRECTA: MANTIENE SU ORIGEN CANÓNICO reception_id.
PROCESADOS: NO MODIFICADO.
DETALLE POR FILA DEL PACKING: PRESERVADO EN stock.move.line.
DATOS DE NEGOCIO EN madenat_test: NO MODIFICADOS DURANTE LA IMPLEMENTACIÓN.
PRUEBAS FOCALES: 6/6 PASS (test_lumber_reception) en base temporal.
ACTUALIZACIÓN DE MÓDULO/UI: NO EJECUTADA.
```
