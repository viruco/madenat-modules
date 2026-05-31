## [2.4.0] - 2025-12-13
### Added
- **Constraint Inteligente:** `_check_shipment_change_with_distributed_costs` para proteger integridad financiera.
- **Trazabilidad de Costos:** Campos `is_distributed` y lógica de distribución detallada.

### Changed
- **Distribución de Costos:** Reingeniería de `action_distribute_costs` para soportar escritura en `stock.lot.cost.line` y campos legacy (Dual Write).
- **Estándar:** Alineación con arquitectura de costos SAP/Oracle.

