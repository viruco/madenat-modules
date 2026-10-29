# CHANGELOG — madenat_lumber_costing

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)
> Flujo canónico de costeo: [../madenat_lumber_docs/CANON/08_COSTEO.md](../madenat_lumber_docs/CANON/08_COSTEO.md)

## [18.0.1.1.0] - 2026-10-29
### Added
- **Tracking de costeo C2 de embarques (DISC-LOG-02, commit 8a43807)**:
  - Incorporación al control de versiones de los archivos preexistentes untracked de costeo C2: `models/stock_lot_cost_line.py`, `views/lumber_shipment_costing_views.xml`, y suite de pruebas `tests/test_shipment_costing_c2.py` (tag: `shipment_costing_c2`).
  - Habilitados en `models/__init__.py`, `views/` en `__manifest__.py` y `tests/__init__.py`.

## [18.0.1.0.0] - 2026-07-01
- Versión base registrada durante la auditoría forense documental 2026-07-01.
- Motor de costeo multi-nivel: `lumber.cost.distribution` (6 métodos de prorrateo).
- Integración con stock_landed_cost (override en `stock_landed_cost.py`).
- README y tests existentes. Sin CHANGELOG previo.