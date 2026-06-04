## [Unreleased]

### Refactored
- TD-009: Centralizar `LUMBER_DIMENSION_MAP` en `utils_uom.py` (2026-06-04). Dict movido sin modificaciones desde `madenat_guia_processing.py:22-61` a `utils_uom.py:733`. Import extendido en `guia_processing.py:63-75`. Preparatorio para TD-010 (migración a modelos ORM configurables). 43 líneas eliminadas de `guia_processing.py`. Comportamiento funcional idéntico.

### Research
- TD-006: Investigación de parametrización de reglas comerciales (`+1/8"`, `1550.003096`, `5085.312`) — conclusión: NO parametrizable. Las 6 fuentes de evidencia (código, git log, docs, modelo de configuración) confirman que las reglas son fijas para todo MADENAT. Sin evidencia de variación por cliente/perfil/subproducto. Documentado en WIKI y CANON con condiciones de reapertura.

### Documentation
- TD-005.1: Comentario explicativo expandido en `INCH_SQ_METERS_TO_M3 = 1550.003096` documentando origen dimensional exacto (NIST), fórmula de derivación, y uso en cubicación comercial de embarque. Nota complementaria en WIKI TD-005.

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_reception_mass_update.py:114`
- TD-005: Clasificación y parametrización de reglas de negocio comercial. Documentado inventario completo de constantes: `M3_DIVISOR` (1000000), `FACTOR_EMBARQUE` (1550.003), `FACTOR_BLANK` (5085.312), `MBF_DIVISOR` (12000), `S2S_WIDTH_ADJUSTMENT_INCH` (0.125). Todas ya centralizadas en `utils_uom.py`. Corrección menor: `lumber_shipment_line.py:131` usaba `1_000_000.0` literal → `float(M3_DIVISOR)`.

## [1.5.0] - 2025-12-13
### Added
- **Trazabilidad:** Nuevo campo `source_shipment_cost_line_id` en `stock.lot.cost.line` para vincular costos con su origen en embarques.