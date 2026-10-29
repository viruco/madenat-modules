# CHANGELOG — madenat_lumber_shipping_core

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)

## [18.0.1.1.0] - 2026-10-29
### Changed
- **Seguridad y ACLs de modelos navieros (DISC-LOG-04, commit af6219b)**:
  - **Cambio de comportamiento**: Se retira el acceso total irrestricto concedido por defecto a `base.group_user`. Los usuarios internos sin rol asignado ya no pueden ver ni manipular buques, viajes ni reservas navieras.
  - Se define acceso de solo lectura para `group_shipping_user` (1,0,0,0).
  - Se otorga acceso total (1,1,1,1) a `group_shipping_manager` y al Administrador del sistema (`base.group_system`).
  - Se incorpora suite de pruebas unitarias `tests/test_shipping_security.py` (tag: `shipping_security`) validando los 3 perfiles.

## [18.0.1.0.0] - 2026-07-01
- Versión base registrada durante la auditoría forense documental 2026-07-01.
- Sin CHANGELOG previo.
