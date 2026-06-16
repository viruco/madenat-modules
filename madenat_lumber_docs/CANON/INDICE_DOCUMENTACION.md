# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 9.2.0  <!-- actualizado: 2026-06-16 -->
**Fecha de actualización:** 2026-06-16
**Estado:** ACTIVO — Mapa maestro de documentación canónica
**Responsable revisión:** Sesión Cline — consolidación flujos de ingesta 2026-06-16

---

## 1. Principio rector

`CANON/` es la **única fuente de verdad técnica y operativa** del proyecto MADENAT.
Cualquier otro documento fuera de esta carpeta es auxiliar, histórico o de conveniencia operativa, y cede ante CANON en caso de contradicción.

---

## 2. Documentos canónicos activos

| Archivo | Propósito | Versión | Fecha | Estado |
|---|---|---|---|---|
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones | 7.0.0 | 2026-05-28 | ⚠️ Pendiente revisión |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados | 4.0.0 | 2026-06-02 | ⚠️ No verificado |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma | 8.1.0 | 2026-06-16 | ✅ Vigente |
| `03_TESTS.md` | Matriz de validación funcional y técnica | 6.4.0 | 2026-06-16 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación | 6.2.0 | 2026-06-16 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases | 6.3.0 | 2026-06-16 | ✅ Vigente |
| `06_CHECKLIST.md` | Checklist operativo de sesión, validación y cierre | 5.0.0 | 2026-06-02 | ⚠️ Pendiente revisión |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.1.0 | 2026-05-28 | ⚠️ Pendiente revisión |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end | 1.0.0 | 2026-06-05 | ✅ Vigente (revisado 2026-06-16) |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado, checklist canónico, huecos, riesgos, índice y orden de trabajo futuro | 1.1.0 | 2026-06-16 | ✅ Vigente |
| `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria Fase A — mapa de campos, migración Float→Monetary | 1.0.0 | 2026-06-05 | ✅ Completada (revisada 2026-06-16) |
| `11_FASE_E_VALIDACION.md` | Validación end-to-end, CI pipeline, runbook operativo | 1.1.0 | 2026-06-16 | ✅ Vigente |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta de madera y discriminación operativa | 1.0.0 | 2026-06-16 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 9.2.0 | 2026-06-16 | ✅ Vigente |

<!-- actualizado: 2026-06-16 — agregados 08, 10, 11, 12; columna Estado; fechas actualizadas -->

## 3. Documentos WIKI operativa

| Archivo | Propósito |
|---|---|
| `WIKI/QUICK_START.md` | Onboarding rápido para retomar trabajo |

## 4. Documentos de CONTEXT

`CONTEXT/` redirige a CANON como fuente de verdad. No contiene contenido canónico propio.

## 5. Auditorías y análisis

| Archivo | Propósito | Fecha | Estado |
|---|---|---|---|
| `AUDITORIA_RUNTIME_2026-06-05.md` | Auditoría funcional runtime sin intervención | 2026-06-05 | ✅ Snapshot histórico (revisado 2026-06-16) |
| `AUDITORIA_2026-06-03.md` | Auditoría general de 10 módulos | 2026-06-03 | ⚠️ Pendiente revisión |
| `AUDITORIA_2026-06-04.md` | Auditoría profunda de madenat_guia_processing | 2026-06-04 | ⚠️ Pendiente revisión |
| `AUDITORIA_MODULOS_COSTEO.md` | Auditoría de costeo y base monetaria | 2026-06-04 | ⚠️ Pendiente revisión |

<!-- actualizado: 2026-06-16 — sección auditorías agregada -->
## 6. Documentos en LEGADO

Todo el material histórico, auditorías antiguas, snapshots y versiones reemplazadas reside en `LEGADO/`. No debe usarse como fuente principal de trabajo.

<!-- renumerado por inserción de sección 5 -->

---

## 7. Criterio de verdad ante contradicción

1. Documento canónico del tema en `CANON/`.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Histórico solo como evidencia contextual.

---

## 8. Regla de mantenimiento

- Cada archivo canónico declara su versión, fecha y estado en el encabezado.
- Si un cambio afecta a más de un archivo, todos se actualizan en la misma sesión.
- No se crean documentos paralelos para temas que ya tienen dueño canónico.