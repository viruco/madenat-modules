# madenat_lumber_logistics

## Propósito

Módulo de gestión logística para la consolidación de lotes de madera en contenedores de exportación. Permite asignar lotes individuales a contenedores, validar capacidad física (peso y volumen), gestionar el sellado y zarpe, y controlar la documentación requerida para el embarque.

## Alcance funcional

- **Consolidación (Tarja):** asignación manual de lotes a contenedores con validación de peso y volumen en tiempo real.
- **Flujo de embarque:** gestión de estados del contenedor (vacío → carga → sellado → embarcado).
- **Inteligencia de negocio:** análisis de rendimiento (yield) y rentabilidad financiera por embarque.
- **Checklist documental:** control de documentos SOLAS/VGM, Bill of Lading y facturación.
- **Rolleo de contenedores:** transferencia de lotes entre contenedores con trazabilidad del sello.

## Flujo principal

1. **Recepción de materia prima:** `lumber.reception` ingresa lotes de madera desde proveedores. Cada lote se crea como `stock.lot` con dimensiones físicas, volumen y subproducto asignado.
2. **Guía de procesamiento (opcional):** `madenat.guia.processing` transforma lotes de madera bruta en lotes procesados (S2S, cepillado). Los lotes procesados se enlazan al lote original como lote padre.
3. **Asignación a contenedor:** el wizard `lumber.container.lot.wizard` filtra los lotes disponibles según la regla de disponibilidad canónica (ver abajo) y permite asignarlos a un contenedor vacío o en carga.
4. **Validación de capacidad:** el contenedor recalcula peso, volumen y porcentaje de llenado tras cada asignación. Se rechaza la asignación si excede los límites físicos.
5. **Sellado y zarpe:** una vez completada la carga, el contenedor se sella (registro de sello naviero), cambia su estado y el embarque padre actualiza sus totales financieros.

## Regla de disponibilidad canónica

Un lote de madera (`stock.lot`) es asignable a un contenedor si cumple todas las condiciones siguientes:

| Criterio | Condición | Razonamiento |
|---|---|---|
| Trazabilidad | `estado_trazabilidad` en `['en_patio', 'procesado', 'recepcionado']` | El lote está físicamente disponible para consolidación. |
| Validación técnica | `technical_validation = 'approved'` | El lote pasó el control técnico correspondiente. |
| Ocupación | No estar asignado a otro contenedor activo | Un lote solo puede pertenecer a un contenedor a la vez. |
| Tipo de producto | `product_id.type` en `['product', 'consu']` | Solo productos inventariables o consumibles válidos. |

### Estados de trazabilidad (`estado_trazabilidad`)

| Estado | Significado | ¿Disponible para contenedor? |
|---|---|---|
| `recepcionado` | Lote ingresado al sistema, recepción en curso | Sí |
| `en_patio` | Lote disponible en inventario físico | Sí |
| `procesado` | Lote transformado (guía de procesamiento), listo para exportación | Sí |
| `consolidado` | Lote asignado a un contenedor en carga | No |
| `embarcado` | Contenedor en tránsito o entregado | No |

### Distinción de conceptos clave

- `estado_trazabilidad` es un estado logístico derivado de reglas internas y refleja la posición operativa del lote.
- `location_id` representa la ubicación física del lote en el almacén y no determina disponibilidad por sí solo.
- `subproducto_id` es una clasificación comercial del lote y no debe confundirse con procesamiento logístico.

## Modelos relacionados

| Modelo | Función |
|---|---|
| `lumber.export.shipment` | Embarque de exportación. Agrupa contenedores, costos y análisis de rendimiento. |
| `lumber.container` | Contenedor físico. Controla peso, volumen, lotes asignados, estado y sello. |
| `lumber.shipment.line` | Línea de embarque. Relación entre contenedor y lotes individuales. |
| `lumber.shipment.cost.line` | Línea de costo. Desglose financiero de costos de embarque prorrateados. |
| `lumber.document.checklist` | Control de documentos requeridos para el embarque. |
| `lumber.shipment.document` | Documentos adjuntos asociados al embarque. |

## Wizards

### lumber.container.lot.wizard

Asigna lotes disponibles a un contenedor. Valida capacidad de peso y volumen en tiempo real. Rechaza la asignación si se excede algún límite.

### lumber.container.rollover.wizard

Transfiere lotes de un contenedor a otro (rolleo). Valida que los contenedores sean distintos y que los sellos sean diferentes. Permite registrar el motivo de la transferencia.

### lumber.consolidation.import.wizard

⚠️ **ARCHIVADO — NO ACTIVO**

Este archivo existe en el repositorio (`wizards/lumber_consolidation_import_wizard.py`) pero **no está importado, registrado ni expuesto** en el sistema. Fue diseñado para importar consolidación masiva desde Excel (formato LISTADO-TARJAS-MN), pero su lógica es incompatible con el modelo actual:

- Intenta escribir `container_id` en `stock.lot` (campo inexistente)
- Busca por `supplier_label` (no es campo de `stock.lot`)
- Duplica writes manuales de `estado_trazabilidad` que `_inverse_lot_ids()` ya maneja

**No usar en producción.** El flujo soportado para asignación de lotes a contenedores es `lumber.container.lot.wizard`.

## Consideraciones técnicas

- La disponibilidad de lotes para contenedor no depende de un único campo de estado. El filtro del wizard utiliza una combinación de `estado_trazabilidad`, `technical_validation`, ocupación en otros contenedores y tipo de producto.
- No hardcodear valores de `estado_trazabilidad` fuera del wizard sin validar con la regla de negocio vigente.
- Los lotes creados desde `lumber.reception` y desde `madenat.guia.processing` comparten el mismo modelo `stock.lot` y las mismas reglas de disponibilidad.
- `_is_processed_lot()` en `stock_lot.py` determina si un lote fue transformado. El campo `subproducto_id` por sí solo no es indicador de procesamiento; es clasificación comercial.

## Instalación

Dependencias declaradas en el manifiesto:

- `base`
- `stock`
- `mail`
- `madenat_lumber_core`
- `madenat_lumber_shipping_core`

Instalar mediante la interfaz de aplicaciones de Odoo o agregar `madenat_lumber_logistics` a la lista de módulos instalados en la configuración.

## Mantenimiento

- Al modificar el dominio de disponibilidad del wizard, verificar que la regla canónica de negocio se respete en su totalidad.
- Al agregar nuevos estados de trazabilidad, actualizar el filtro del wizard si corresponde.
- Al modificar `_is_processed_lot()` en `stock_lot.py`, verificar que los estados computados en `_compute_estado_trazabilidad()` sigan siendo coherentes.
- Los contenedores sellados (`state = 'sealed'`) no permiten modificación de lotes sin desellar primero.
