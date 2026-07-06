# madenat_lumber_logistics — Arquitectura y flujo

## Objetivo del módulo

Gestionar la consolidación de lotes de madera en contenedores de exportación, desde la asignación individual hasta el sellado y zarpe, con control de capacidad, costos y documentación.

## Conceptos principales

### Lote (`stock.lot`)

Unidad mínima de inventario de madera. Contiene dimensiones físicas, volumen, subproducto comercial y estado de trazabilidad. Se origina en `lumber.reception` (compra) o `madenat.guia.processing` (transformación).

### Embarque (`lumber.export.shipment`)

Agrupación de nivel superior que contiene uno o más contenedores. Centraliza el análisis de rendimiento (yield), la distribución de costos y la rentabilidad financiera.

### Contenedor (`lumber.container`)

Unidad física de consolidación. Controla peso, volumen, lotes asignados, estado operativo y sello naviero. Tiene límites de capacidad configurables (peso máximo y volumen máximo).

### Línea de embarque (`lumber.shipment.line`)

Relación entre un contenedor y un lote individual. Se crea automáticamente al asignar un lote a un contenedor y se elimina al retirar el lote.

### Estado de trazabilidad (`estado_trazabilidad`)

Estado logístico computado en `stock.lot` que refleja la posición del lote en el flujo operativo. Se calcula automáticamente a partir de indicadores de origen y transformación. No se escribe manualmente.

### Ubicación física (`location_id`)

Ubicación del lote en el almacén (PATIO, ALMACÉN SECO, etc.). Es un campo almacenado independiente. No determina disponibilidad para contenedor por sí solo.

## Flujo de datos

### Recepción

1. `lumber.reception` procesa archivos PDF y Excel del proveedor.
2. Las líneas de staging (`lumber.reception.line`) validan los datos importados.
3. `LumberReceptionService.create_lots_from_staging()` crea registros `stock.lot` con nombre, referencia, subproducto, dimensiones, volúmenes y enlace a la recepción.
4. Al confirmar la recepción, se crea un albarán (`stock.picking`) con movimientos de inventario que validan la entrada física.

### Guía procesada

1. `madenat.guia.processing` procesa guías de aserradero externo.
2. El parser lee PDF y Excel, extrae dimensiones y crea líneas de staging.
3. `_create_or_get_lot()` busca o crea registros `stock.lot` con dimensiones físicas, nominales, visuales, subproducto y ubicación de patio asignada.
4. Los lotes procesados se enlazan al lote original mediante `parent_lot_id` o se marcan con `guia_processing_id`.

### Wizard de contenedores

1. El usuario abre el wizard desde un contenedor en estado `'empty'` o `'loading'`.
2. `_compute_available_lots()` filtra los lotes disponibles según la regla canónica.
3. El usuario selecciona lotes desde la lista filtrada.
4. `_compute_validation_status()` valida que el peso y volumen totales no excedan los límites del contenedor.
5. Al confirmar, `action_assign()` escribe los lotes en el contenedor, actualiza la trazabilidad y registra en el chatter del contenedor.

## Regla de disponibilidad

Un lote es asignable a un contenedor si cumple todas las siguientes condiciones:

- `estado_trazabilidad` en `['en_patio', 'procesado', 'recepcionado']`
- `technical_validation = 'approved'`
- No estar asignado a otro contenedor activo
- `product_id.type` en `['product', 'consu']`

Los estados `'consolidado'` y `'embarcado'` excluyen al lote de la disponibilidad.

### Cálculo de `estado_trazabilidad`

El método `_compute_estado_trazabilidad()` en `stock_lot.py` determina el estado según esta prioridad:

1. Si `_is_processed_lot()` retorna True → `'procesado'`
2. Si el lote está en un contenedor con embarque → según estado del embarque (`'embarcado'`, `'consolidado'`, `'en_patio'`)
3. Si el lote está en un contenedor sin embarque → `'consolidado'`
4. Si la recepción de origen está en estado `'done'` → `'en_patio'`
5. En cualquier otro caso → `'recepcionado'`

### Indicadores de procesamiento (`_is_processed_lot()`)

Un lote se considera procesado si cumple al menos uno de estos indicadores:

- Tiene `guia_processing_id` asociado (transformación por guía de procesamiento).
- Tiene `parent_lot_id` asociado (transformación por split/merge de lotes).
- Tiene `thickness_final_inch` o `width_final_inch` mayores que cero (dimensiones post-procesamiento).
- Tiene `vol_shipment_m3` diferente de `volume_purchase_m3` (volumen de embarque distinto al de compra).

**Nota:** `subproducto_id` por sí solo no es indicador de procesamiento. Es clasificación comercial.

## Validaciones

### Capacidad del contenedor

- **Peso máximo:** `max_weight_kg`. Si el peso total supera este valor, se rechaza la asignación.
- **Volumen máximo:** `max_volume_m3`. Si el volumen total supera este valor, se rechaza la asignación.
- **Factor limitante:** el porcentaje de llenado se calcula como el máximo entre peso y volumen. El factor que alcanza el 100% primero determina la capacidad efectiva.

### Sellado

- Requiere sello naviero (`seal_number`) configurado.
- Requiere peso bruto (VGM) mayor que cero.
- Requiere al menos un lote o paquete asignado.
- No permite sellado si el contenedor tiene errores de validación pendientes.

### Checklist documental

- Controla la presencia de documentos SOLAS/VGM, Bill of Lading y factura comercial.
- El estado del checklist se calcula automáticamente según los documentos adjuntos.

## Riesgos conocidos

### Hardcodeo de estados en el wizard

El dominio de disponibilidad del wizard contiene valores literales de `estado_trazabilidad`. Si se agregan o modifican estados en el futuro, el filtro debe actualizarse manualmente para reflejar la regla canónica de negocio.

### Dependencia de `_is_processed_lot()` para el estado

Si se modifica `_is_processed_lot()` sin actualizar `_compute_estado_trazabilidad()`, los lotes pueden quedar clasificados incorrectamente. Ambos métodos están acoplados y deben modificarse en conjunto.

### Duplicación de lógica de capacidad

La validación de capacidad existe tanto en el wizard como en el modelo del contenedor. Si se modifica un límite en un lado, debe actualizarse en el otro para mantener coherencia.

## Puntos de mantenimiento

### Modificar la regla de disponibilidad

Si el negocio cambia los criterios de disponibilidad:

1. Actualizar el dominio en `_compute_available_lots()` del wizard.
2. Verificar que los nuevos estados estén contemplados en `_compute_estado_trazabilidad()`.
3. Actualizar este documento.

### Agregar nuevos estados de trazabilidad

1. Agregar el estado a la selección `estado_trazabilidad` en `stock_lot.py`.
2. Agregar la lógica de transición en `_compute_estado_trazabilidad()`.
3. Si el estado debe ser disponible para contenedor, agregarlo al dominio del wizard.
4. Actualizar este documento.

### Modificar indicadores de procesamiento

Si se agregan o eliminan indicadores en `_is_processed_lot()`:

1. Verificar que `_compute_estado_trazabilidad()` siga siendo coherente.
2. Verificar que el wizard de contenedores siga filtrando correctamente.
3. Actualizar este documento.
