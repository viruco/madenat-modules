# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 10.9.0
**Fecha de actualización:** 2026-08-29
**Estado:** ACTIVO — Mapa maestro de documentación canónica
**Responsable revisión:** 2026-08-29 — Actualización de naming: "Ingreso Global" → "Ingreso de Madera", alineado con el renombrado de `madenat_lumber_intake`.

---

## 1. Principio rector

`CANON/` es la **única fuente de verdad técnica y operativa** del proyecto MADENAT.
Cualquier otro documento fuera de esta carpeta es auxiliar, histórico o de conveniencia operativa, y cede ante CANON en caso de contradicción.

---

## 2. Documentos canónicos activos

| Archivo | Propósito | Versión | Fecha | Estado |
|---|---|---|---|---|
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones | 7.5.0 | 2026-08-19 | ✅ Vigente |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados — ARCHIVADO en LEGADO | 4.0.0 | 2026-05-13 | 🏷️ ARCHIVADO — absorbido por 00 y 12_FLUJOS_INGESTA |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma | 11.7.0 | 2026-08-19 | ✅ Vigente |
| `03_TESTS.md` | Matriz de validación funcional y técnica | 6.4.0 | 2026-06-16 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación | 11.0.0 | 2026-08-19 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases | 6.3.0 | 2026-06-16 | ✅ Vigente |
| `05_AUDITORIA_XML_IDS.md` | Auditoría de XML IDs — R1 Stock Detail | — | 2026-06-15 | ✅ Vigente |
| `06_CHECKLIST.md` | Checklist operativo de sesión — ARCHIVADO en LEGADO | 4.2.0 | 2026-06-30 | 🏷️ ARCHIVADO — reemplazado por checklist A-F en este índice |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.3.0 | 2026-07-01 | ✅ Vigente |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end | 1.5.0 | 2026-08-19 | ✅ Vigente |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado — ARCHIVADO, checklist migrado a este índice | 1.1.0 | 2026-06-16 | 🏷️ ARCHIVADO — checklist A-F consolidado en Anexo A |
| `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria Fase A — ARCHIVADO en LEGADO/auditorias | — | 2026-06-04 | 🏷️ ARCHIVADO — Fase A completada, evidencia histórica |
| `11_FASE_E_VALIDACION.md` | Validación end-to-end, CI pipeline, runbook operativo | 1.1.0 | 2026-06-16 | ✅ Derivado vigente |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta de madera y discriminación operativa | 1.2.0 | 2026-06-16 | ✅ Vigente |
| `12_ARQUITECTURA_OPERATIVA_PERFILES.md` | Arquitectura operativa y perfiles — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md` | Arquitectura técnica de implementación — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `14_GUIA_EJECUCION_INCREMENTAL.md` | Guía de ejecución incremental — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — plan no ejecutado |
| `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación actual | 1.1.0 | 2026-06-06 | ✅ Derivado vigente |
| `13_CONSOLIDACION_OPERATIVA.md` | Consolidación operativa: ingesta (Producto/Procesados), reglas, trazabilidad, matriz de hallazgos y contradicciones | 1.5.0 | 2026-08-19 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 10.8.0 | 2026-08-19 | ✅ Vigente |

<!-- actualizado: 2026-06-30 — indexados 05_AUDITORIA_XML_IDS, 12-15; 06_CHECKLIST marcado LEGACY; 00 y 07 actualizados; 05_CONTINUIDAD_GLOBAL y AUDITORIA_TRAZABILIDAD_OC movidos a LEGADO -->

---

## 3. Documentos WIKI operativa

| Archivo | Propósito |
|---|---|
| `WIKI/00_INDICE.md` | Índice maestro de conocimiento WIKI |
| `WIKI/QUICK_START.md` | Onboarding rápido para retomar trabajo |
| `WIKI/GUIA_PRODUCCION_FINAL.md` | Guía de validación y criterio de deploy |
| `WIKI/HOJA_RUTA_EJECUTIVA.md` | Vista ejecutiva de estado, foco y prioridades |

---

## 4. Documentos de CONTEXT

`CONTEXT/` redirige a CANON como fuente de verdad. No contiene contenido canónico propio.

---

## 5. Auditorías y snapshots históricos

Todas las auditorías, informes de sesión, análisis y snapshots históricos residen en `LEGADO/auditorias/` (25 archivos). No deben usarse como fuente principal de trabajo.

**Auditorías clave (referencia histórica):**
| Archivo | Propósito | Fecha |
|---|---|---|
| `LEGADO/auditorias/AUDITORIA_2026-06-03.md` | Auditoría general de 10 módulos | 2026-06-03 |
| `LEGADO/auditorias/AUDITORIA_2026-06-04.md` | Auditoría profunda de madenat_guia_processing | 2026-06-04 |
| `LEGADO/auditorias/AUDITORIA_RUNTIME_2026-06-05.md` | Auditoría funcional runtime sin intervención | 2026-06-05 |
| `LEGADO/auditorias/AUDITORIA_MODULOS_COSTEO.md` | Auditoría de costeo y base monetaria | 2026-06-04 |

---

## 6. Documentos en LEGADO

Todo el material histórico, auditorías antiguas, snapshots, planes ejecutados, minutas y versiones reemplazadas reside en `LEGADO/`. No debe usarse como fuente principal de trabajo.

Estructura:
- `LEGADO/auditorias/` — 25 auditorías e informes históricos
- `LEGADO/planificacion/` — 4 planes de ejecución ya completados
- `LEGADO/minutas/` — 2 minutas de reuniones y talleres
- `LEGADO/` (raíz) — 4 archivos legacy antiguos (índice old, decisión log old, continuidad global, resumen old)

---

## 7. Documentos en RAW

`RAW/` contiene investigaciones vivas temporales (4 archivos, fechas 2026-06-21/22). No son fuente canónica.

---

## 8. Criterio de verdad ante contradicción

1. Documento canónico del tema en `CANON/`.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Código fuente (para verdad funcional).
5. Histórico solo como evidencia contextual.

---

## 9. Regla de mantenimiento

- Cada archivo canónico declara su versión, fecha y estado en el encabezado.
- Si un cambio afecta a más de un archivo, todos se actualizan en la misma sesión.
- No se crean documentos paralelos para temas que ya tienen dueño canónico.
- Las auditorías históricas van a `LEGADO/auditorias/`, no a CANON/ ni a la raíz.