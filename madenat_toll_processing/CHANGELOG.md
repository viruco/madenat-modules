# CHANGELOG — madenat_toll_processing

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)

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
