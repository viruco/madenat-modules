## Problema
En el flujo granel → service (PRE-02), la recepción posterior podía llegar a la
validación del picking con move lines en estado `picked` pero con cantidad cero,
y un `stock.move` fantasma podía sobrevivir porque la detección de trazabilidad
consultaba `move.lot_ids`, campo calculado que puede conservar un valor de caché
heredado del `create` del movimiento (sin move line real que lo respalde).

## Corrección
- Detección de lotes mediante las **move lines reales** (`move.move_line_ids`),
  no por el `move.lot_ids` calculado/cacheado (elimina el fantasma huérfano).
- Construcción/reutilización **por ORM** de la move line trazable de la
  recepción (producto, lote/tarja, move, picking, ubicaciones y compañía tomados
  del propio movimiento/picking), creando una sola si faltase.
- Derivación de la cantidad desde la línea real de guía
  (`vol_purchase_m3 → vol_physical_m3 → vol_shipment_m3`), con fallback trazable
  al lote solo cuando la línea no aporta, y conversión con UoM estándar de Odoo
  (`_compute_quantity`).
- Idempotencia: el reproceso no duplica move lines, movimientos, lotes, pickings
  ni relaciones de origen.
- La validación de stock se mantiene vía `button_validate()` estándar, sin
  omitir el sanity check nativo.

## Alcance
- `madenat_lumber_core/models/madenat_guia_processing.py`
- `madenat_lumber_core/tests/test_granel_route.py`
(+193 / −56; sin cambios en manifiestos, seguridad, XML, dependencias, migraciones
ni configuración.)

## Validación
- Oráculo integral F3.1: **73 passed / 0 failed**.
- PRE-02 focalizado: **1/1**.
- Clase granel (`TestGranelRouteCore`): **14/14**.
- Regresión `guia_processing,sv,-f31`: **204/204**.
- F3.1 (`--test-tags f31`): **13/13**.

## Garantías
- Sin `skip_sanity_check`.
- Sin SQL directo.
- Sin bypass de ACL.
- Sin hardcode de entidades de negocio (IDs, cantidades, productos, lotes,
  ubicaciones o compañías).
- Sin cambios a Costeo, Facturación, Pagos, B1, CDP-V1 ni CANON.

## Riesgo y rollback
Riesgo bajo y acotado a la creación/preparación de move lines de la recepción
service. Rollback: revertir únicamente
`bee61e7ee3b829376e261ea37b3f38a9202f2bbd`; la evidencia y los recursos
temporales permanecen preservados.
