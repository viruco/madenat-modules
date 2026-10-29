# CHANGELOG — madenat_lumber_costing

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)
> Flujo canónico de costeo: [../madenat_lumber_docs/CANON/08_COSTEO.md](../madenat_lumber_docs/CANON/08_COSTEO.md)

## [18.0.1.1.0] - 2026-10-29
### Added
- **Acceso de lectura a reservas navieras para Costos (DISC-LOG-04, commit 1c3ae12)**:
  - Asignación de permisos de solo lectura (`1,0,0,0`) para `madenat_lumber_core.group_madenat_costos` sobre `shipping.booking` (`madenat_lumber_shipping_core.model_shipping_booking`) en `ir.model.access.csv`.
  - Prueba unitaria `tests/test_costing_shipping_access.py` (tag: `costing_shipping_access`) verificando lectura permitida y bloqueo de escritura/creación para el usuario de costos.
  - *Nota de alcance / Fase 5*: El grupo `madenat_lumber_core.group_madenat_contabilidad` permanece sin acceso a `shipping.booking` (pendiente de evaluación al abordar la Fase 5 / Contabilidad y Facturación).
- **Tracking de costeo C2 de embarques (DISC-LOG-02, commit 8a43807)**:
  - Incorporación al control de versiones de los archivos preexistentes untracked de costeo C2: `models/stock_lot_cost_line.py`, `views/lumber_shipment_costing_views.xml`, y suite de pruebas `tests/test_shipment_costing_c2.py` (tag: `shipment_costing_c2`).
  - Habilitados en `models/__init__.py`, `views/` en `__manifest__.py` y `tests/__init__.py`.


## [18.0.1.0.0] - 2026-07-01
- Versión base registrada durante la auditoría forense documental 2026-07-01.
- Motor de costeo multi-nivel: `lumber.cost.distribution` (6 métodos de prorrateo).
- Integración con stock_landed_cost (override en `stock_landed_cost.py`).
- README y tests existentes. Sin CHANGELOG previo.