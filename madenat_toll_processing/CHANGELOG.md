# CHANGELOG — madenat_toll_processing

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)

## [18.0.1.1.0] - 2026-10-29
### Added
- **Suite de pruebas de preentrega (DISC-OP-09, DISC-OP-10)**:
  - Archivo `tests/test_toll_consumption_and_processor.py` con 9 casos de prueba:
    1. `test_01_lot_in_specific_yard`: Consumo en patio físico específico (`MARVAL`).
    2. `test_02_material_distributed_across_locations`: Material distribuido entre dos patios físicos sin duplicar movimientos.
    3. `test_03_insufficient_availability`: Disponibilidad insuficiente por reservas externas (rechazo con `UserError`).
    4. `test_04_incompatible_company`: Aislamiento multi-compañía (rechazo ante quants de otra compañía).
    5. `test_05_processor_distinct_from_supplier`: Procesador distinto al proveedor en creación de orden Toll.
    6. `test_06_processor_selection_conserved_through_lifecycle`: Conservación del procesador en el ciclo (`sent`, `in_process`, consumo y facturación).
    7. `test_07_no_duplicate_move_creation`: Idempotencia en llamadas consecutivas sin duplicación.
    8. `test_08_idempotency_cancelled_picking_allows_recreation`: Idempotencia distinguiendo albarán previo cancelado (permite recrear consumo activo).
    9. `test_09_uom_validation_and_conversion`: Validación de categoría Volumen en UoM del producto, rechazo de unidades incompatibles y conversión canónica de cantidades con redondeo nativo de la unidad.
  - **Ejecución dinámica aislada**: Ejecución sobre base temporal `tmp_lote6_toll_20261029` tras resolver el orden de carga en `madenat_lumber_core` (18.0.6.25.3). Resultado: 9 tests ejecutados, 0 fallos, 0 errores, código de salida 0. Base temporal y filestore eliminados y verificados. Validado en entorno aislado; no desplegado en `madenat_test`; UAT operativa pendiente.

### Fixed
- **Consumo físico desde ubicación real del lote (DISC-OP-10)**:
  - Implementado `_get_lot_consumption_sources(lot, required_qty)` para resolver dinámicamente las ubicaciones internas físicas donde residen los quants del lote.
  - Reemplazado hardcode de origen en `warehouse.lot_stock_id` por la ubicación específica de cada quant (p. ej. patios específicos `WH/Stock/MARVAL` o `WH/Stock/PUERTO CORONEL`), evitando quants negativos en la ubicación raíz y descuadres de existencias.
  - Coherencia estricta de unidad de medida utilizando la UoM del producto o metro cúbico.
  - Validación de disponibilidad real (libre) mediante `stock.quant._get_available_quantity(..., strict=True)`.
  - Soporte para consumo fraccionado si el lote está repartido entre múltiples ubicaciones internas.
  - Idempotencia estricta en `_create_consumption_picking` distinguiendo estados activos de cancelados.

### Verified
- **Independencia y conservación de maquilador (DISC-OP-09)**:
  - Verificado que `processor_id` es un valor por defecto sugerido en `lumber.reception.action_create_toll_order` pero plenamente editable en borrador.
  - Se confirmó estáticamente que la selección se conserva a lo largo del ciclo (`sent`, `in_process`, consumo y facturación de proveedor) sin forzar equivalencia proveedor = procesador.

## [18.0.1.0.3] - 2026-10-29
### Changed
- **Navegación y reparentado de menú (DISC-OP-05, commit 6e945cb)**:
  - Reparentado de `menu_toll_processing_root` bajo `madenat_lumber_core.menu_ops_inventory` (Control de Lotes / Operaciones) con rótulo "Procesamiento Externo" y secuencia 20.
  - Eliminado `web_icon` para integrarse a la estructura canónica sin generar icono raíz independiente en la barra de aplicaciones.

## [18.0.1.0.2] - 2026-10-28
- Añadidos permisos r/w/c para Operaciones en toll.processing.order y corregida resolución de lotes origen en stock.lot.

## [18.0.1.0.0] - 2026-07-01
- Versión base registrada durante la auditoría forense documental 2026-07-01.
- Sin CHANGELOG previo.
