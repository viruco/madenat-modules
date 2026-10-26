# Índice de documentos RAW — `madenat_lumber_docs/RAW/`

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Origen:** consolidación documental FASE 2, etapa E6. Inventario de los 33 documentos `.md` de `RAW/`
más el fixture Excel no versionado. La columna *Referencias* se calculó con `grep -rl` sobre todo
`custom_addons/` (excluyendo el propio archivo y los manifiestos de `FASES/`).

**Naturaleza de `RAW/`:** notas de investigación, implementación y auditoría de una sola sesión.
No son canónicas: la verdad vive en `CANON/`. Se conservan como evidencia y trazabilidad.

---

| # | Archivo | Fecha | Tema | Tipo | Estado | Referencias | Bytes |
|---|---|---|---|---|---|---|---|
| 1 | `ADDENDUM_IDEMPOTENCIA_OC_PROVISIONAL_20260821.md` | 2026-08-21 | Addendum — Idempotencia OC provisional (FIX guard anti-duplicado) | Nota técnica (RAW) | Sin referencias externas | — | 3,228 |
| 2 | `ANALISIS_IMPACTO_OC_PROVISIONAL_20260821.md` | 2026-08-21 | Análisis de Impacto — OC Provisional desde Guía | Nota técnica (RAW) | Sin referencias externas | — | 4,226 |
| 3 | `AUDITORIA_ARQUITECTONICA_LUMBER_CORE_ECOSISTEMA_20260701.md` | 2026-07-01 | AUDITORÍA ARQUITECTÓNICA COMPLETA — `madenat_lumber_core` Y ECOSISTEMA | Nota técnica (RAW) | Sin referencias externas | — | 40,036 |
| 4 | `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` | 2026-07-06 | AUDITORÍA DE ASIMETRÍA DOCUMENTAL — INGESTA DE DOCUMENTOS | Nota técnica (RAW) | Referenciado en 4 archivo(s) | `madenat_lumber_core/_archive/_cleanup_orphan_moves.py`, `madenat_lumber_core/CHANGELOG.md`, `madenat_lumber_docs/CANON/04_DECISION_LOG.md` (+1) | 54,602 |
| 5 | `AUDITORIA_DEDUCTION_FACTOR_0_0625_BLANK_20260815.md` | 2026-08-15 | AUDITORÍA ACOTADA — `deduction_factor = 0.0625` / Flujo Blank (`f5085`) | Nota técnica (RAW) | Sin referencias externas | — | 8,069 |
| 6 | `AUDITORIA_PROFUNDA_GUIA_PROCESSING_20260701.md` | 2026-07-01 | AUDITORÍA PROFUNDA — `madenat_guia_processing` | Nota técnica (RAW) | Sin referencias externas | — | 29,417 |
| 7 | `AUDITORIA_PROFUNDA_LUMBER_RECEPTION_20260701.md` | 2026-07-01 | AUDITORÍA PROFUNDA — `lumber_reception` | Nota técnica (RAW) | Sin referencias externas | — | 28,729 |
| 8 | `AUDITORIA_RECONCILIACION_BLANK_TARJAS_MSC_VIRGO_20260815.md` | 2026-08-15 | AUDITORÍA DE RECONCILIACIÓN — VOLUMEN BLANK / TARJAS MSC VIRGO | Nota técnica (RAW) | Sin referencias externas | — | 11,422 |
| 9 | `FIX_BOTON_NUEVO_INGRESO_GLOBAL_20260822.md` | 2026-08-22 | Fix — Botón Nuevo en Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 3,560 |
| 10 | `FIX_CABECERA_GUIA_ORIGEN_20260822.md` | 2026-08-22 | Fix — Cabecera de Guía Origen (botón "Nuevo" en ficha) | Nota técnica (RAW) | Sin referencias externas | — | 2,099 |
| 11 | `FIX_CLIENT_ACTION_VIEWS_PAYLOAD_20260822.md` | 2026-08-22 | Fix — Payload `views` para Client Action de Reemplazo | Nota técnica (RAW) | Sin referencias externas | — | 2,969 |
| 12 | `FIX_OCULTAR_DUPLICAR_INGRESO_GLOBAL_20260822.md` | 2026-08-22 | Fix — Ocultar Duplicar en Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 2,960 |
| 13 | `FIX_QWEB_KEYERROR_O_REPORTE_GUIA_20260822.md` | 2026-08-22 | Fix — QWeb KeyError 'o' en reporte de guía | Nota técnica (RAW) | Sin referencias externas | — | 1,748 |
| 14 | `FIX_RECUPERAR_NUEVO_INGRESO_GLOBAL_20260822.md` | 2026-08-22 | Fix — Recuperar botón Nuevo en Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 2,625 |
| 15 | `FIX_TITULO_ACTIVO_INGRESO_GLOBAL_20260822.md` | 2026-08-22 | Fix — Título Activo de Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 3,058 |
| 16 | `IMPLEMENTACION_DISPLAY_NAME_GUIAS_PROCESADOS_20260821.md` | 2026-08-21 | Implementación — Identidad Visual de Guías Procesados | Nota técnica (RAW) | Sin referencias externas | — | 4,813 |
| 17 | `IMPLEMENTACION_IDENTIFICACION_OPERATIVA_LOTES_R1_20260925.md` | 2026-09-25 | Implementación — Identificación operativa y trazabilidad visible de lotes en R1 (Programación 1, 2026-09-25) | Nota técnica (RAW) | Referenciado en 2 archivo(s) | `madenat_lumber_docs/CANON/04_DECISION_LOG.md`, `madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md` | 9,953 |
| 18 | `IMPLEMENTACION_NO_BREADCRUMBS_RETORNO_INGRESO_GLOBAL_20260821.md` | 2026-08-21 | Implementación — Ocultar Breadcrumb del Retorno a Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 4,020 |
| 19 | `IMPLEMENTACION_OC_PROVISIONAL_DESDE_GUIA_20260821.md` | 2026-08-21 | Implementación — OC provisional desde guía (FIX 2026-08-21) | Nota técnica (RAW) | Sin referencias externas | — | 2,666 |
| 20 | `IMPLEMENTACION_REPLACE_CURRENT_ACTION_BREADCRUMBS_20260822.md` | 2026-08-22 | Implementación — Reemplazo de Controller Actual para Breadcrumbs | Nota técnica (RAW) | Sin referencias externas | — | 4,692 |
| 21 | `INVESTIGACION_3_ALERTAS_POST_UPDATE_20260621.md` | 2026-06-21 | Investigación: 3 Alertas Preexistentes Post-Update | Nota técnica (RAW) | Sin referencias externas | — | 8,798 |
| 22 | `INVESTIGACION_CREACION_OC_DESDE_GUIA_20260821.md` | 2026-08-21 | Investigación — Creación/vinculación de `purchase.order` desde guía/recepción cuando no existe OC coincidente | Nota técnica (RAW) | Sin referencias externas | — | 7,574 |
| 23 | `INVESTIGACION_EDICION_INDIVIDUAL_20260622.md` | 2026-06-22 | INVESTIGACIÓN: Edición Individual de Líneas | Nota técnica (RAW) | Sin referencias externas | — | 15,245 |
| 24 | `INVESTIGACION_FORENSE_CONTROLADOR_STACK_RUTER_BREADCRUMBS_ODOO18_20260821.md` | 2026-08-21 | Investigación Forense — Controller Stack, Router y Breadcrumbs Odoo 18 | Nota técnica (RAW) | Sin referencias externas | — | 11,794 |
| 25 | `INVESTIGACION_GATEKEEPER_VALIDATE_OR_CREATE_PO_20260821.md` | 2026-08-21 | Investigación del Gatekeeper `validate_or_create_po` | Nota técnica (RAW) | Sin referencias externas | — | 17,006 |
| 26 | `INVESTIGACION_NAVEGACION_MODIFICAR_ORIGEN_INGRESO_GLOBAL_20260821.md` | 2026-08-21 | Investigación — Navegación “Modificar origen” → “Ingreso Global” | Nota técnica (RAW) | Sin referencias externas | — | 5,898 |
| 27 | `INVESTIGACION_NOMINALES_HOMOLOGACION_20260622.md` | 2026-06-22 | INVESTIGACIÓN: Homologación Asignación Masiva + Nominales + Producto | Nota técnica (RAW) | Referenciado en 1 archivo(s) | `madenat_lumber_core/wizard/lumber_reception_mass_update.py` | 14,088 |
| 28 | `INVESTIGACION_OC_HOMOLOGACION_20260621.md` | 2026-06-21 | INVESTIGACIÓN: Homologación OC lumber_reception ↔ guia_processing | Nota técnica (RAW) | Sin referencias externas | — | 34,381 |
| 29 | `INVESTIGACION_PROFUNDA_ACTION_STACK_BREADCRUMBS_ODOO18_20260821.md` | 2026-08-21 | Investigación Profunda — Action Stack y Breadcrumbs Odoo 18 | Nota técnica (RAW) | Sin referencias externas | — | 8,611 |
| 30 | `INVESTIGACION_REPETICION_GUIAS_19827_20260821.md` | 2026-08-21 | Investigación — Repetición de Guías “19827” en Navegación | Nota técnica (RAW) | Sin referencias externas | — | 8,545 |
| 31 | `INVESTIGACION_VIABILIDAD_REPLACE_CURRENT_ACTION_ODOO18_20260821.md` | 2026-08-21 | Investigación de Viabilidad — Reemplazo de Action Stack Odoo 18 | Nota técnica (RAW) | Sin referencias externas | — | 7,666 |
| 32 | `LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx` | — | Fixture Excel: listado y tarjas MSC VIRGO FA610R | Fixture binario (gitignored) | Fixture — no versionado (`.gitignore`: `madenat_lumber_docs/RAW/*.xlsx`) | `madenat_lumber_core/tests/test_lumber_reception.py`, `madenat_lumber_logistics/tests/test_consolidation_import_wizard.py`, `madenat_lumber_docs/CANON/02_CONTINUIDAD.md` | 41,357 |
| 33 | `ROLLBACK_LIST_VIEW_RETORNO_INGRESO_GLOBAL_20260822.md` | 2026-08-22 | Rollback — Vista Lista en Retorno a Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 2,856 |
| 34 | `ROLLBACK_NO_BREADCRUMBS_RETORNO_INGRESO_GLOBAL_20260821.md` | 2026-08-21 | Rollback — no_breadcrumbs en retorno a Ingreso Global | Nota técnica (RAW) | Sin referencias externas | — | 2,735 |

**Total:** 34 entradas (33 `.md` + 1 binario).

## Criterio de estado

- **Referenciado en N archivo(s):** el nombre exacto del archivo aparece citado en N documentos o
  scripts fuera de sí mismo; esas citas son la evidencia de que el documento sigue vivo.
- **Sin referencias externas:** no lo cita nadie. No implica que sea inútil: muchos son la única
  evidencia de una sesión de corrección. Se listan aquí para que sean localizables.
- **Fixture:** binario necesario para pruebas (no versionado por `.gitignore`).
