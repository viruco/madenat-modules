# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 9.0.0
**Fecha de actualización:** 2026-06-04
**Estado:** ACTIVO — Mapa maestro de documentación canónica

---

## 1. Principio rector

`CANON/` es la **única fuente de verdad técnica y operativa** del proyecto MADENAT.
Cualquier otro documento fuera de esta carpeta es auxiliar, histórico o de conveniencia operativa, y cede ante CANON en caso de contradicción.

---

## 2. Documentos canónicos activos

| Archivo | Propósito | Versión | Fecha |
|---|---|---|---|
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones | 7.0.0 | 2026-05-28 |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados | 4.0.0 | 2026-06-02 |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma | 8.0.0 | 2026-06-02 |
| `03_TESTS.md` | Matriz de validación funcional y técnica | 6.4.0 | 2026-06-02 |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación | 7.0.0 | 2026-06-02 |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases | 7.0.0 | 2026-06-02 |
| `06_CHECKLIST.md` | Checklist operativo de sesión, validación y cierre | 5.0.0 | 2026-06-02 |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.1.0 | 2026-05-28 |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado, checklist canónico, huecos, riesgos, índice y orden de trabajo futuro | 1.0.0 | 2026-06-04 |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 9.0.0 | 2026-06-04 |

## 3. Documentos WIKI operativa

| Archivo | Propósito |
|---|---|
| `WIKI/QUICK_START.md` | Onboarding rápido para retomar trabajo |

## 4. Documentos de CONTEXT

`CONTEXT/` redirige a CANON como fuente de verdad. No contiene contenido canónico propio.

## 5. Documentos en LEGADO

Todo el material histórico, auditorías antiguas, snapshots y versiones reemplazadas reside en `LEGADO/`. No debe usarse como fuente principal de trabajo.

---

## 6. Criterio de verdad ante contradicción

1. Documento canónico del tema en `CANON/`.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Histórico solo como evidencia contextual.

---

## 7. Regla de mantenimiento

- Cada archivo canónico declara su versión, fecha y estado en el encabezado.
- Si un cambio afecta a más de un archivo, todos se actualizan en la misma sesión.
- No se crean documentos paralelos para temas que ya tienen dueño canónico.