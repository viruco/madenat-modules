## [Unreleased]

### Documentation
- TD-005.1: Comentario explicativo expandido en `INCH_SQ_METERS_TO_M3 = 1550.003096` documentando origen dimensional exacto (NIST), fórmula de derivación, y uso en cubicación comercial de embarque. Nota complementaria en WIKI TD-005.

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_reception_mass_update.py:114`
- TD-005: Clasificación y parametrización de reglas de negocio comercial. Documentado inventario completo de constantes: `M3_DIVISOR` (1000000), `FACTOR_EMBARQUE` (1550.003), `FACTOR_BLANK` (5085.312), `MBF_DIVISOR` (12000), `S2S_WIDTH_ADJUSTMENT_INCH` (0.125). Todas ya centralizadas en `utils_uom.py`. Corrección menor: `lumber_shipment_line.py:131` usaba `1_000_000.0` literal → `float(M3_DIVISOR)`.

## [1.5.0] - 2025-12-13
### Added
- **Trazabilidad:** Nuevo campo `source_shipment_cost_line_id` en `stock.lot.cost.line` para vincular costos con su origen en embarques.

