# Changelog

Todos los cambios notables de este módulo se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_shipment_line.py:78,123`
- TD-005: Centralización de divisor métrico `1_000_000.0` → `M3_DIVISOR` en `lumber_shipment_line.py:131`. Agregado import `M3_DIVISOR` desde `utils_uom`.
- Wizard de asignación de lotes: corregido el dominio de disponibilidad para incluir lotes con `estado_trazabilidad = 'procesado'` y `'recepcionado'`, además de `'en_patio'`. Anteriormente solo se mostraban lotes con estado `'en_patio'`, lo que excluía lotes válidos de guía procesada y recepciones en curso.
- Clasificación de lotes: corregido `_is_processed_lot()` en `stock_lot.py` para que `subproducto_id` por sí solo no marque un lote como procesado. El subproducto es clasificación comercial, no indicador de procesamiento. Solo `guia_processing_id`, `parent_lot_id` o dimensiones finales indican procesamiento real.

### Added

- Documentación técnica completa del módulo: README, arquitectura y reglas de disponibilidad.
- Definición formal de la regla canónica de disponibilidad para asignación de lotes a contenedores.
- Tabla de semántica de estados de trazabilidad (`estado_trazabilidad`).

### Changed

- UX de consolidación de contenedores alineada con dimensiones comerciales: wizard de asignación muestra E"/A"/L(ft) como principales, mm/m como opcionales. Pestaña "Lotes Asignados" del contenedor prioriza L(ft) sobre L(m).
- Wizard `lumber.consolidation.import.wizard` archivado como dead code documentado. El archivo existe en `wizards/lumber_consolidation_import_wizard.py` pero no está integrado (sin import, sin vista XML, sin acción). Su lógica era incompatible con el modelo actual (escribe campos inexistentes en `stock.lot`). El flujo canónico de asignación a contenedores es `lumber.container.lot.wizard`.
- Documentación del dominio del wizard para reflejar la regla de disponibilidad canónica.
- Comentario en `_is_processed_lot()` para documentar que `subproducto_id` no es indicador de procesamiento.

## [2026-05-31]

### Fixed

- Parche TD-006: corrección en dos pasos de la clasificación de lotes y disponibilidad para contenedor.
- Lotes de recepción con `subproducto_id` ahora se clasifican correctamente como `'en_patio'` en lugar de `'procesado'`.
- Wizard de contenedores muestra lotes de ambos orígenes (recepción y guía procesada) sin exclusión incorrecta.

## [2026-05-30]

### Fixed

- Campo `ref` en `stock.lot` ahora se escribe desde `lumber.reception` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente la etiqueta/código del lote.
- Campo `subproducto_id` en `stock.lot` ahora se escribe desde `lumber.reception.line.subproduct_id` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente el subproducto.
- Data migration: 20 lotes existentes actualizados con `ref` y `subproducto_id` desde las líneas de recepción correspondientes.

## [2.4.0] - 2025-12-13

### Added

- **Constraint Inteligente:** `_check_shipment_change_with_distributed_costs` para proteger integridad financiera.
- **Trazabilidad de Costos:** Campos `is_distributed` y lógica de distribución detallada.

### Changed

- **Distribución de Costos:** Reingeniería de `action_distribute_costs` para soportar escritura en `stock.lot.cost.line` y campos legacy (Dual Write).
- **Estándar:** Alineación con arquitectura de costos SAP/Oracle.
