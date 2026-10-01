# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 12.0.0
**Fecha de actualización:** 2026-10-01  <!-- actualizado: 2026-10-01 (2) — alta de CANON/19 (imputación SV y saldo por procesador); AD-87 y AD-88 (APROBADAS); AD-83 reemplazada por AD-87; AD-82/AD-84 alineadas; 12/13/17/18 ampliados -->
**Estado:** ACTIVO — Mapa maestro de documentación canónica
**Responsable revisión:** 2026-10-01 — Alta del documento canónico `18_CONSOLIDACION_Y_REBAJA.md` (especificación de consolidación y rebaja de contenedores y naves, BORRADOR/PROPUESTA) y de AD-85 y AD-86 en estado PROPUESTA; actualización de versiones/índice.

---

## 1. Principio rector

`CANON/` es la **única fuente de verdad técnica y operativa** del proyecto MADENAT.
Cualquier otro documento fuera de esta carpeta es auxiliar, histórico o de conveniencia operativa, y cede ante CANON en caso de contradicción.

---

## 2. Documentos canónicos activos

| Archivo | Propósito | Versión | Fecha | Estado |
|---|---|---|---|---|
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones (incluye §4.8 Gestión Operativa de Etiquetas SV y §4.9 Modo A autoservicio) | 7.13.0 | 2026-09-28 | ✅ Vigente |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados — ARCHIVADO en LEGADO | 4.0.0 | 2026-05-13 | 🏷️ ARCHIVADO — absorbido por 00 y 12_FLUJOS_INGESTA |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma (incluye §14 Gestión Operativa de Etiquetas SV) | 12.7.0 | 2026-09-28 | ✅ Vigente |
| `03_TESTS.md` | Matriz de validación funcional y técnica (incluye §9 cobertura de la suite `sv`) | 6.9.0 | 2026-09-28 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación (AD-80; AD-81 PROPUESTA; **AD-82 y AD-84 APROBADAS e implementadas**; **AD-83 REEMPLAZADA por AD-87**; AD-85..86 PROPUESTA; **AD-87 (imputación etiqueta→SV) y AD-88 (advertir/motivar/auditar) APROBADAS**) | 12.13.0 | 2026-10-01 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases (incluye deuda T1–T7, «Rebaja de contenedor/nave (AD-82/84/83) — IMPLEMENTADO», «Rebaja — Endurecimiento (I0) y AD-88 (I1) — IMPLEMENTADO», «Auditoría 2026-10-01 — pendientes por área» e «Imputación SV y Procesadores (AD-87/88) — PLAN (fases I1..I6)») | 8.1.0 | 2026-10-01 | ✅ Vigente |
| `05_AUDITORIA_XML_IDS.md` | Auditoría de XML IDs — R1 Stock Detail | 1.1.0 | 2026-09-25 | ✅ Vigente |
| `06_CHECKLIST.md` | Checklist operativo de sesión — ARCHIVADO en LEGADO | 4.2.0 | 2026-06-30 | 🏷️ ARCHIVADO — reemplazado por checklist A-F en este índice |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.3.0 | 2026-07-01 | ✅ Vigente |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end (§7 corregido 2026-10-01: `account_id` no existe) | 1.7.0 | 2026-10-01 | ✅ Vigente |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado — ARCHIVADO, checklist migrado a este índice | 1.1.0 | 2026-06-16 | 🏷️ ARCHIVADO — checklist A-F consolidado en Anexo A |
| `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria Fase A — ARCHIVADO en LEGADO/auditorias | — | 2026-06-04 | 🏷️ ARCHIVADO — Fase A completada, evidencia histórica |
| `11_FASE_E_VALIDACION.md` | Validación end-to-end, CI pipeline, runbook operativo | 1.1.0 | 2026-06-16 | ✅ Derivado vigente |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta de madera y discriminación operativa (incluye §11.5 volumen oficial de Recepción por Volumen y §11.8 imputación SV etiqueta→SV) | 1.7.0 | 2026-10-01 | ✅ Vigente |
| `12_ARQUITECTURA_OPERATIVA_PERFILES.md` | Arquitectura operativa y perfiles — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md` | Arquitectura técnica de implementación — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `14_GUIA_EJECUCION_INCREMENTAL.md` | Guía de ejecución incremental — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — plan no ejecutado |
| `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación actual | 1.1.0 | 2026-06-06 | ✅ Derivado vigente |
| `13_CONSOLIDACION_OPERATIVA.md` | Consolidación operativa: ingesta (Producto/Procesados), reglas, trazabilidad, matriz de hallazgos, contradicciones, matriz operativa de Etiquetas SV (§13) e imputación SV / merma documental (§11) | 2.0.0 | 2026-10-01 | ✅ Vigente |
| `16_AUDITORIA_20261001.md` | **NUEVO** — Auditoría 2026-10-01: hallazgos H-01..H-16 y N-01..N-10, clasificados por área (Operaciones / Contabilidad-Auditoría-Facturación / Logística / Fase 6); resueltos, pendientes, parámetro `dev_cleanup_enabled` y mapeo de grupos huérfanos | 1.0.0 | 2026-10-01 | ✅ Vigente |
| `17_CONSTITUCION_VOLUMENES.md` | Constitución de Volúmenes: definiciones NOMINAL / DISPONIBLE / EXPORTACIÓN / OFICIAL (acordadas 2026-10-01), reglas de uso por proceso, reglas acordadas para diseño futuro (ACORDADO), glosario de etiquetas, conciliación documental (modelo_despachos:449 / AD-67); §6 F-01/F-02 RESUELTOS; §2.8 reescrita (SV nunca se exporta; salida por imputación, AD-87) | 1.2.0 | 2026-10-01 | ✅ Vigente |
| `18_CONSOLIDACION_Y_REBAJA.md` | Consolidación y rebaja de contenedores y naves: alcance y glosario (tres usos de «consolidación»), puntos acordados (2026-10-01), modelo/estados, reglas de rebaja, vía SV e invariantes, pantallas (incl. §7.5 imputación SV fuera de la exportación), permisos, plan de pruebas, migración, preguntas abiertas, riesgos y §14 Estado de implementación + §14.6 clasificación de bloqueos (AD-88) | 1.2.0 | 2026-10-01 | 🟢 EN IMPLEMENTACIÓN |
| `19_IMPUTACION_SV_Y_PROCESADORES.md` | **NUEVO** — Imputación declarada etiqueta→SV y saldo por procesador: glosario, ciclo por tipo de compra (C1 SV / C2 procesado), modelo de datos mínimo (`madenat.sv.imputation`, ledger `imputacion`, ubicaciones `Procesadores/<X>`, costo), estados, reglas, alertas, roles, UX (propuesta por proveedor/producto/antigüedad), casos límite, migración, riesgos, clasificación de bloqueos (§14, con estado I0/I1) y plan de pruebas T-01..T-12; backlog por fases I1..I6 (§16) y preguntas Q-19 (§17, resueltas 2026-10-01: 1/2/5/8) | 1.1.0 | 2026-10-01 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 12.0.0 | 2026-10-01 | ✅ Vigente |

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
- **Etiquetas de fase en tests (T5, 2026-09-26):** toda clase de test de un módulo con dependientes debe declarar
  su fase explícitamente (`@tagged('post_install', '-at_install', …)`). Sin esa declaración, Odoo aplica
  `standard`/`at_install` y la clase corre durante la carga del grafo, sobre un registro parcial donde los campos
  aportados por módulos dependientes (p. ej. `conciliation_status` de Intake) todavía no existen.
- **Independencia de módulos base (T6, 2026-09-26):** un módulo base no puede referenciar XML IDs declarados
  únicamente por un módulo que depende de él; el punto de extensión se declara en el módulo superior mediante
  herencia de vista (ver `00_ARQUITECTURA.md` §3.4).