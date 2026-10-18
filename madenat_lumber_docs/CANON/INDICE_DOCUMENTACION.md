# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 12.45.0
**Fecha de actualización:** 2026-10-18  <!-- actualizado: 2026-10-18 — **Bloque 4J (AD-122)**: cierre definitivo Bloque 4; anti-copia absoluta de tabla S2S en todo el código madenat_* con eliminación de S2S_WIDTH_LOOKUP y S2S_WIDTH_MAP (J1); eliminación de doble redondeo de volúmenes y MBF con r3() ROUND_HALF_UP único y TDD (J2); suite y reconciliación final (J3); precisión de IDs reales de stock.location 17, 18, 19 (J4); diffs de desacople sin aplicar (J5); correcciones documentales y ratificación D4 (J6). Versiones `02` 12.43.0 → 12.44.0, `04` 12.39.0 → 12.40.0, `05` 8.39.0 → 8.40.0, `17` 1.10.0 → 1.11.0; índice 12.44.0 → 12.45.0. Sin push ni despliegue. | Bloque 4I (AD-121). -->
<!-- actualizado: 2026-10-18 — **Bloque 4I (AD-121)**: cierre definitivo Bloque 4; suite oficial en 1.540 pruebas (+4 de G8) y reconciliación de 1.876 stats (I1); clasificación de datos en código y registro TD-122 (I2); script pre_deploy normalizado con consultas oficiales B y A.2 e informativa write_date con TDD (I3); fila residuo TEST-LOT-EX documentada (I4); auditoría 3 decimales en vistas, reportes y Excel (I5); método de entrega no definido D4 en CANON/02 §18 (I6). Versiones `02` 12.42.0 → 12.43.0, `04` 12.38.0 → 12.39.0, `05` 8.38.0 → 8.39.0, `17` 1.9.0 → 1.10.0; índice 12.43.0 → 12.44.0. Sin push ni despliegue. | Bloque 4H (AD-121). -->
<!-- actualizado: 2026-10-18 — **Bloque 4H (AD-121)**: verificación de evidencias reales H1-H6; fijación de línea base única stock_lot (H1); regresión baseline 1.536 tests con 10 fallas conocidas (H2); coherencia exacta S2S <= 0.001" con TDD (H3); corrección de decisiones D4/D5 y naturaleza de Consulta B (H4); evidencias G1/G2/G3 (H5); verificación estricta de regla 3 decimales en volúmenes (H6). Módulo `madenat_lumber_core` 18.0.6.16.0 → 18.0.6.17.0. Versiones `02` 12.41.0 → 12.42.0, `04` 12.37.0 → 12.38.0, `05` 8.37.0 → 8.38.0, `17` 1.8.0 → 1.9.0; índice 12.42.0 → 12.43.0. Sin push ni despliegue. | Bloque 4G (AD-120). -->
<!-- actualizado: 2026-10-18 — **Bloque 4G (AD-120)**: decisiones Mauricio D1 a D6; retiro de _BLANKS_NOMINAL_MAP (G1); verificación de vectores f5085 y vol_documental (G2); pre_deploy_health_check.py reescrito con 3 niveles (G3); consultas fijadas MD5 invariantes (G4); UserError de tabla S2S acotado a perfil imperial (G5); conteo de 1.533 tests (G6); simulacion_embarques_solo_lectura_remoto.py inocuo (G7); tabla S2S editable por interfaz con tracking, coherencia y sin recálculo histórico (G8); runbook borrador en CANON/02 (G9); backlog técnico diferido a-e (G10). Módulo `madenat_lumber_core` 18.0.6.15.0 → 18.0.6.16.0. Versiones `02` 12.40.0 → 12.41.0, `04` 12.36.0 → 12.37.0, `05` 8.36.0 → 8.37.0, `12` 1.13.0 → 1.14.0, `17` 1.7.0 → 1.8.0; índice 12.41.0 → 12.42.0. Sin push ni despliegue. | 2026-10-18: Cierre Bloque 4F (AD-119). -->
<!-- actualizado: 2026-10-11 (1) — **AUDITORÍA INTEGRAL Y BLINDAJE DEL CICLO DE REBAJA DE ETIQUETAS
<!-- actualizado: 2026-10-11 (2) — **CIERRE PROBATORIO DEL CICLO DE REBAJA DE ETIQUETAS
<!-- actualizado: 2026-10-11 (3) — **CONTRATO DE APLICACIÓN SIN REPARTO (propuesta, NO aprobada)**: `19`
<!-- actualizado: 2026-10-11 (4) — **CONTRATO DE APLICACIÓN APROBADO E IMPLEMENTADO**: `19` §19.23
<!-- actualizado: 2026-10-11 (5) — **PERSISTENCIA Y RECUPERACIÓN DEL TRABAJO (SAVE)**: `19` §19.24,
<!-- actualizado: 2026-10-11 (6) — **ACCIONES VISIBLES DEL ASISTENTE «REGISTRAR REBAJA» (UI)**: `19`
<!-- actualizado: 2026-10-11 (7) — **SIMPLIFICACIÓN OPERATIVA (recorrido de DOS acciones)**: `19` §19.26,
<!-- actualizado: 2026-10-11 (8) — **VOLVER A BORRADOR Y REASIGNAR (RESET)**: `19` §19.27, `02`
§17.16.25, `03` §29. Transición **cancelled → draft** controlada (motivo, permisos, capacidad, conflicto,
locks); write no la elude; applied/reversed excluidos; trazabilidad de anulación/reapertura. Suite RESET
14/14. Expediente `RESET_REBAJA_20261011/`. Módulos `madenat_lumber_logistics` **18.0.1.20.0 → 18.0.1.21.0**
(+ `madenat_lumber_core` audit log); `19` **1.25.0**, `02` **12.34.0**, `03` **6.33.0**; índice **12.28.0**.
Concurrencia RESET-16/17 pendiente. Sin commit/push. -->

`02` §17.16.24, `03` §28. Ventana **[Guardar] [Aplicar] [Volver]**; sin «Preparar asignación» obligatorio,
sin Guardar previo y sin abrir el documento; opciones avanzadas en «Más opciones»; mensajes por problema
real; tablas en sólo lectura tras aplicar. Suite SIMPLE-01..17 + CLIENT-01..03. Expediente
`SIMPLE_REBAJA_20261011/`. Módulo `madenat_lumber_logistics` **18.0.1.19.0 → 18.0.1.20.0**; `19` **1.24.0**,
`02` **12.33.0**, `03` **6.32.0**; índice **12.27.0**. **Aceptación en navegador pendiente.** Sin commit/push. -->

§19.25, `02` §17.16.23, `03` §27. Causa: `<footer>` no renderizado en `target=current` ⇒ acciones
invisibles; corrección: `<header>` nativo + «Abrir documento» + «Descartar y volver» + confirmación con
referencia. Expediente `UI_SAVE_REBAJA_20261011/`. Módulo `madenat_lumber_logistics`
**18.0.1.18.0 → 18.0.1.19.0**; `19` **1.23.0**, `02` **12.32.0**, `03` **6.31.0**; índice **12.26.0**.
**Aceptación en navegador pendiente.** Sin commit/push. -->

`02` §17.16.22, `03` §26. Causa C1 (cantidad 0 bloqueaba «Guardar borrador») + C2 (descubrimiento desde
el SV); corrección mínima (`work_sv_lot_id`, «Trabajo en preparación», `action_continue_preparation`,
cero no bloquea / negativo rechazado). Suite SAVE-01..14 + FLOW-01..03 + PHY-01 = **18/18**. Expediente
`SAVE_REBAJA_20261011/`. Módulo `madenat_lumber_logistics` **18.0.1.17.0 → 18.0.1.18.0**; `19` **1.22.0**,
`02` **12.31.0**, `03` **6.30.0**; índice **12.25.0**. **Aceptación en navegador pendiente.** Sin commit/push. -->

(política **aprobada por Mauricio**, validación backend en `_i2_validate_payload`, `NO_SV_CANDIDATE`
informativo, `etiqueta_pendiente_m3`), `02` §17.16.21, `03` §25 (POL-01..08 = 8/8). Expediente
`CONTRATO_APLICACION_20261011/` (dry-run IMP02220, guion de navegador A–I). Módulo `madenat_lumber_logistics`
**18.0.1.16.0 → 18.0.1.17.0**; `19` **1.21.0**, `02` **12.30.0**, `03` **6.29.0**; índice **12.24.0**.
**Aceptación en navegador pendiente.** Sin commit/push. -->

§19.23, `02` §17.16.21; expediente `CONTRATO_APLICACION_20261011/` (propuesta de política, validación
backend prevista, pruebas POL-01..08 en borrador, dry-run de IMP02220, guion de navegador A–I). **Contrato
NO modificado; bloqueado por decisión de negocio.** `19` **1.20.0**, `02` **12.29.0**; índice **12.23.0**.
Módulo `madenat_lumber_logistics` **18.0.1.16.0** (sin cambio). Sin commit/push. -->

(AUD-ETQ-06..10)**: `19` §19.22 (diagnóstico IMP02220, contrato de «aplicación sin reparto» **bloqueado**,
concurrencia real OK, seguridad multi-compañía con nueva `ir.rule`, motivo de reversa con strip, ciclos con
balances); `02` §17.16.20; `03` §24; expediente `AUDIT_REBAJA_ETIQUETAS_20261011/`. Versiones: `19`
**1.19.0**, `02` **12.28.0**, `03` **6.28.0**; índice **12.22.0**. Módulo `madenat_lumber_logistics`
**18.0.1.15.0 → 18.0.1.16.0**. Sin commit/push. -->

(AUD-ETQ-01..05)**: `19` §19.21 (inmutabilidad real del aplicado, reversa con motivo obligatorio, mapa
lote↔packing sin elección arbitraria, causa del saldo concreta y trazable); `02` §17.16.19; `03` §23;
expediente `AUDIT_REBAJA_ETIQUETAS_20261011/` (raíz del workspace). Versiones: `19` **1.18.0**,
`02` **12.27.0**, `03` **6.27.0**; índice **12.21.0**. Módulo `madenat_lumber_logistics`
**18.0.1.14.1 → 18.0.1.15.0**. Sin commit/push. -->

<!-- actualizado: 2026-10-10 (2) — **ACEPTACIÓN VISUAL (guía 19827) + FLUJO SV CONFIRMADO**: 02 §17.16.8/§17.16.9, 03 §14.4, 05 «Aceptación visual …», 19 §19.10. Versiones: 02 **12.17.0**, 03 **6.17.0**, 05 **8.16.0**, 19 **1.8.0**; índice **12.11.0**. Solo documentación; sin cambios de código, base ni servicios. -->
<!-- actualizado: 2026-10-10 (4) — **AJUSTE DE INTEGRIDAD A/B/C**: `19` §19.13, `02` §17.16.11, `03` §15.5–15.6, `05`. Versiones: 19 **1.10.0**, 02 **12.19.0**, 03 **6.19.0**, 05 **8.18.0**; índice **12.13.0**. Módulo `madenat_lumber_logistics` **18.0.1.8.0**. Controles acreditados: reversa vs. procedencia, reimputación, compañía + regla de registro, elegibilidad dura, volúmenes N:M referenciales (`aggregator=False`). Regresión: 275 pruebas, 4 fallas (3 preexistentes + 1 ambiental por evidencia V3 7973), 0 errores. Bloque D cuantitativo fuera de alcance. Sin commit/push. -->
<!-- actualizado: 2026-10-10 (6) — **OPERACIÓN MANUAL DE ASIGNACIONES CENTRADA EN SV**: `19` **§19.14** (bloques A–G: entrada/consulta por SV, alta desde el SV, selección explícita, conservación del borrador, integridad etiqueta–guía D10 y coherencia de volumen D10/D11), `02` §17.16.12, `03` §16. Versiones: 19 **1.11.0**, 02 **12.20.0**, 03 **6.20.0**, 05 **8.19.0**; índice **12.14.0**. Módulo `madenat_lumber_logistics` **18.0.1.9.0**. Suite nueva `test_sv_imputation_manual.py` T-MAN-01..12 = **12/12**; regresión **286 pruebas, 4 fallas** (las mismas preexistentes/ambientales del `deviation` histórico), **0 errores**. Integración web/RPC: menú «Asignaciones SV» visible + `default_get` SV OK; **V3 *pixel* pendiente**. Bloque D cuantitativo fuera de alcance. Sin commit/push. -->
<!-- actualizado: 2026-10-10 (7) — **UNIFICACIÓN DE ACCESO «REBAJA DE ETIQUETAS»**: `19` **§19.15**, `02` §17.16.13, `03` §17, `05`. Versiones: 19 **1.12.0**, 02 **12.21.0**, 03 **6.21.0**, 05 **8.20.0**; índice **12.15.0**. Módulo `madenat_lumber_logistics` **18.0.1.10.0**. Un único enlace operativo («Rebaja de etiquetas», menú `menu_madenat_sv_assignment` reutilizado); «Imputaciones documentales SV» retirado de navegación (`ir.ui.menu` 542 `active=False`, acción 867 preservada como historial interno); «Rebajar por Motonave» y «Consolidación» sin cambios; ingesta sin nuevas pantallas. Suite NAV-01..12 = **11/11**; regresión **298 pruebas, 4 fallas preexistentes, 0 errores**; **2.ª `-u`** acredita NAV-10. **V3 *pixel* pendiente**. Sin commit/push. -->
<!-- actualizado: 2026-10-17 — **ALINEACIÓN CANÓNICA CON INSTRUCCIONES DE OPERACIONES (CRISTHIAN ELGUETA / AD-116)**: Fórmulas canónicas F1 a F7, rango S2S 75–155 mm con sobreancho 1/8", transición milimétrica desde 170 mm, Blanks sin deducción 1/16" y pase directo a stock, patios creables (MARVAL, Ferramenta, Puerto Coronel). Versiones: `04` **12.32.0**, `05` **8.33.0**, `12` **1.9.0**, `17` **1.3.0**; índice **12.29.0**. Sin cambios de código ni datos. -->
<!-- actualizado: 2026-10-10 (10) — **REDISEÑO OPERATIVO DEL ASISTENTE «REGISTRAR REBAJA»**: `19` **§19.18**, `02` §17.16.16, `03` §20, `05`. Versiones: 19 **1.15.0**, 02 **12.24.0**, 03 **6.24.0**, 05 **8.23.0**; índice **12.18.0**. Módulo `madenat_lumber_logistics` **18.0.1.13.0**. Interfaz anterior **rechazada por Mauricio**; se rediseña el MISMO asistente: tabla de material del packing list (Etiqueta=`stock.lot.ref`, SKU/dimensiones declaradas por la regla de promoción, producto, subproducto, dimensiones técnicas, piezas, volumen documental), documental avanzada en columnas opcionales, formulario amplio (`o_xxl_form_view`, `target=current`), cabecera con saldo documental del SV, granularidad por lote sin doble conteo. Guía real 19827: **17/17** mapeados. Suite `test_sv_rebaja_material.py` = **8/8**; regresión **342 pruebas, 4 fallas preexistentes, 0 errores**. **Aceptación visual de Mauricio pendiente**. Sin commit/push. -->


**Estado:** ACTIVO — Mapa maestro de documentación canónica
**Responsable revisión:** 2026-10-17 — Alta de AD-116 y actualización canónica con las especificaciones de Cristhian Elgueta (F1 a F7, S2S 75-155 mm, Blanks sin deducción 1/16", patios creables). Sincronización monótona de versiones 04, 05, 12, 17 e índice.

---

## 1. Principio rector

`CANON/` es la **única fuente de verdad técnica y operativa** del proyecto MADENAT.
Cualquier otro documento fuera de esta carpeta es auxiliar, histórico o de conveniencia operativa, y cede ante CANON en caso de contradicción.

---

## 2. Documentos canónicos activos

| Archivo | Propósito | Versión | Fecha | Estado |
|---|---|---|---|---|
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones (incluye §4.8 Gestión Operativa de Etiquetas SV, §4.9 Modo A autoservicio y §4.10 Búsqueda/filtros/agrupaciones de la Consola de Intake) | 7.18.0 | 2026-10-07 | ✅ Vigente |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados — ARCHIVADO en LEGADO | 4.0.0 | 2026-05-13 | 🏷️ ARCHIVADO — absorbido por 00 y 12_FLUJOS_INGESTA |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma (incluye §14 Gestión Operativa de Etiquetas SV, §15 Fase 2, §16 Búsqueda/filtros Consola Intake, §17 Auditoría retoma retorno servicio y **§18 Procedimiento Operacional de Despliegue a TEST Remoto — borrador no ejecutado, AD-120 G9 / AD-121 H4**) | 12.42.0 | 2026-10-18 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación (AD-80..AD-120; **AD-121 (2026-10-18): Cierre Real y Verificación Bloque 4H — Diagnóstico stock_lot H1, regresión baseline 1.536 tests H2, coherencia exacta S2S H3, correcciones documentales H4, evidencias G1-G3 H5 y regla 3 decimales H6**) | 12.38.0 | 2026-10-18 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases (incluye deuda T1–T7, rebaja, auditorías, imputación SV; Bloque 4, 4E, 4F; Bloque 4G; **Backlog Técnico Diferido a-e — Bloque 5 real, fitosanitario, patios, motonave y 26270 — AD-120 G10 / AD-121 H4**) | 8.38.0 | 2026-10-18 | ✅ Vigente |
| `05_AUDITORIA_XML_IDS.md` | Auditoría de XML IDs — R1 Stock Detail | 1.1.0 | 2026-09-25 | ✅ Vigente |
| `06_CHECKLIST.md` | Checklist operativo de sesión — ARCHIVADO en LEGADO | 4.2.0 | 2026-06-30 | 🏷️ ARCHIVADO — reemplazado por checklist A-F en este índice |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.3.0 | 2026-07-01 | ✅ Vigente |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end (§7 corregido 2026-10-01: `account_id` no existe) | 1.7.0 | 2026-10-01 | ✅ Vigente |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado — ARCHIVADO, checklist migrado a este índice | 1.1.0 | 2026-06-16 | 🏷️ ARCHIVADO — checklist A-F consolidado en Anexo A |
| `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria Fase A — ARCHIVADO en LEGADO/auditorias | — | 2026-06-04 | 🏷️ ARCHIVADO — Fase A completada, evidencia histórica |
| `11_FASE_E_VALIDACION.md` | Validación end-to-end, CI pipeline, runbook operativo | 1.1.0 | 2026-06-16 | ✅ Derivado vigente |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta de madera y discriminación operativa (incluye §11.5 volumen oficial de Recepción, §11.8 imputación SV, §12 Reglas de Ingreso Directo, Blanks F4/F6, Patios F7, Secado en Horno, §12.4 Fuente única S2S sin copia en código — AD-119; y **§12.5 Cierre Técnico Final y Gobernanza de Anchos S2S — AD-120 G5/G8**) | 1.14.0 | 2026-10-18 | ✅ Vigente |
| `12_ARQUITECTURA_OPERATIVA_PERFILES.md` | Arquitectura operativa y perfiles — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md` | Arquitectura técnica de implementación — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `14_GUIA_EJECUCION_INCREMENTAL.md` | Guía de ejecución incremental — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — plan no ejecutado |
| `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación actual | 1.1.0 | 2026-06-06 | ✅ Derivado vigente |
| `13_CONSOLIDACION_OPERATIVA.md` | Consolidación operativa: ingesta (Producto/Procesados), reglas, trazabilidad, matriz de hallazgos, contradicciones, matriz operativa de Etiquetas SV (§13) e imputación SV / merma documental (§11) | 2.0.0 | 2026-10-01 | ✅ Vigente |
| `16_AUDITORIA_20261001.md` | **NUEVO** — Auditoría 2026-10-01: hallazgos H-01..H-16 y N-01..N-10, clasificados por área (Operaciones / Contabilidad-Auditoría-Facturación / Logística / Fase 6); resueltos, pendientes, parámetro `dev_cleanup_enabled` y mapeo de grupos huérfanos | 1.0.0 | 2026-10-01 | ✅ Vigente |
| `17_CONSTITUCION_VOLUMENES.md` | Constitución de Volúmenes: definiciones NOMINAL / DISPONIBLE / EXPORTACIÓN / OFICIAL; §9 Especificación Canónica de Operaciones (F1 a F7); y **§10 Consulta Canónica Fijada de Integridad MD5, Naturaleza Consulta B y Gobernanza S2S — AD-120 G4 / AD-121 H1/H3/H4** | 1.9.0 | 2026-10-18 | ✅ Vigente |
| `18_CONSOLIDACION_Y_REBAJA.md` | Consolidación y rebaja de contenedores y naves: alcance y glosario (tres usos de «consolidación»), puntos acordados (2026-10-01), modelo/estados, reglas de rebaja, vía SV e invariantes, pantallas (incl. §7.5 imputación SV fuera de la exportación), permisos, plan de pruebas, migración, preguntas abiertas, riesgos y §14 Estado de implementación + §14.6 clasificación de bloqueos (AD-88) | 1.2.0 | 2026-10-01 | 🟢 EN IMPLEMENTACIÓN |
| `19_IMPUTACION_SV_Y_PROCESADORES.md` | **NUEVO** — Imputación declarada etiqueta→SV y saldo por procesador | 1.33.0 | 2026-10-15 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 12.43.0 | 2026-10-18 | ✅ Vigente |

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

## 9. Evidencia de pruebas externa (fuera de `custom_addons`)

La evidencia de las pruebas de ingreso **no vive sólo en el repositorio**. Fuentes verificadas:

| Fuente | Ruta real | Uso |
|---|---|---|
| **Biblioteca de muestras** | `…/odoo-18-ce/muestras_documentos_ingreso` (hermana de `custom_addons`; **no** está versionada en el repo) | Documentos de ingreso: `07-09-2026/`, `Ejercicio Completo Cristhian Elgueta/`, `excel_packing/`, `guias_pdf/` — **63 archivos, 52 únicos por SHA-256** |
| **Respaldos de base** | `BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump` (base **local**), `APPLY_AB_UI_20261008/retired/db/srvretab_*.dump`, `backups/**/madenat_test*.dump`, `APPLY_BUSQUEDA_INTAKE_20261007/backup/madenat_test_pre.dump` | Registros de ingreso, adjuntos, lotes y pickings: **evidencia persistente** de las pruebas (se leen con `pg_restore` **sin** restaurar) |
| **Dump SQL histórico** | `madenat_test_antes_limpieza.sql` (2026-08-20) | Línea base anterior a las pruebas de septiembre |
| **Expedientes de prueba** | `AUDIT_*`, `UAT_*`, `IMPL_*`, `FIX_*`, `FASE_*`, `CIERRE_*`, `INCIDENTE_*`, `APPLY_*` | Parches, logs de corridas y verificación |
| **Fixtures con archivo real** | `custom_addons/madenat_lumber_intake/tests/fixtures/HLZF75_4495589.pdf` (byte-idéntico a la muestra) y `custom_addons/madenat_lumber_core/tests/fixtures/26270.txt` (transcripción) | Regresión automatizada |

> **Regla:** la biblioteca es **fuente de muestras**, no fuente de verdad doctrinal. La doctrina sigue
> siendo `CANON/`. La reconstrucción de pruebas y su trazabilidad están en `02_CONTINUIDAD.md` **§17.15**
> y `03_TESTS.md` **§13.5–13.6**. **No** crear una matriz paralela: la matriz R01–R16 vive en
> `02_CONTINUIDAD.md`.

---

## 10. Regla de mantenimiento

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

<!-- actualizado: 2026-10-10 (11) — **INTERFAZ CLARA Y CONCISA DE «REGISTRAR REBAJA» (AMBAS
PESTAÑAS)**: `19` **§19.19**, `02` §17.16.17, `03` §21, `05`. Versiones: 19 **1.16.0**, 02
**12.25.0**, 03 **6.25.0**, 05 **8.24.0**; índice **12.19.0**. Módulo `madenat_lumber_logistics`
**18.0.1.14.0**. Cabecera única, totales con unidad, «A asignar» editable, identidad limpia + medidas,
«SV destino» condicional, acciones breves y causa real de disponibilidad cero. Suite nueva
`test_sv_rebaja_ui_limpia.py` = **13/13**; regresión **355 pruebas, 4 fallas preexistentes, 0 errores**.
**V3 *pixel* pendiente.** Sin commit/push ni despliegue remoto. -->


<!-- actualizado: 2026-10-10 (12) — **HOTFIX BLOQUEANTE OwlError al abrir «Registrar rebaja»**:
`19` **§19.20**, `02` §17.16.18, `03` §22, `05`. Versiones: 19 **1.17.0**, 02 **12.26.0**, 03 **6.26.0**,
05 **8.25.0**; índice **12.20.0**. Módulo `madenat_lumber_logistics` **18.0.1.14.1**. Error real del
navegador `(bool(not wizard_id.multi_sv))` → `Name 'wizard_id' is not defined`: `column_invisible` se
evalúa con el contexto del PADRE; corrección a `not parent.multi_sv` + carga de `multi_sv` en el padre.
Casos A–E = **20/20**; regresión **362 pruebas, 4 fallas preexistentes, 0 errores**. **Renderización
real pendiente de comprobación manual** (sin navegador; no se afirma que las pruebas previas lo
detectaran). Sin commit/push. -->

  herencia de vista (ver `00_ARQUITECTURA.md` §3.4).

<!-- actualizado: 2026-10-12 (1) — **BLINDAJE LOCAL Y ESTABILIZACIÓN (AUD-ETQ-07/08)**: `19` **§19.28**,
`02` §17.16.26, `03` §29. Versiones: 19 **1.26.0**, 02 **12.35.0**, 03 **6.34.0**. Módulos
`madenat_lumber_logistics` **18.0.1.22.0** y `madenat_lumber_intake` **18.0.0.12.0** (core sin cambios).
(a) Reapertura `cancelled → draft` por **token de PROCESO**: la **vía directa de `write` se RECHAZA**
(no acepta identidad del cliente ni flag de contexto). (b) **Concurrencia REAL RESET-16/17** acreditada
(transacciones PostgreSQL independientes, advisory lock + revalidación; sin sobreconsumo ni doble auditoría).
(c) Advertencias de cálculo **eliminadas** (`stock.lot` `sv_assignment_*`; consola de intake
`volume_detail_line_ids`). Suites dirigidas **0 failed / 0 error**; regresión solo-logistics **444 tests,
4 fallas preexistentes** (mismas que la base). **Sobrescritura de borradores**: propuesta, **pendiente** de
autorización de Mauricio. **Sin commit/push/despliegue; TEST remoto intacto.** -->

<!-- actualizado: 2026-10-12 (2) — **VERIFICACIÓN PROBATORIA P1–P4**: `19` **§19.29**, `02` §17.16.27, `03` §29.
Versiones: 19 **1.27.0**, 02 **12.36.0**, 03 **6.35.0**. Módulos `madenat_lumber_logistics` **18.0.1.23.0** y
`madenat_lumber_intake` **18.0.0.13.0** (core sin cambios). (P1) concurrencia sobre la MISMA etiqueta retornada
(advisory lock + revalidación de capacidad; **sin cambio de código**). (P2) recomputación REAL de intake en el
MISMO entorno (defecto + corrección por invalidación dirigida). (P3) saldos almacenados **canónicos**
(`compute_sudo=True`) vs proyección por usuario; sin AccessError ni exposición entre compañías. (P4) **vía
privada de transición** (elimina el registro global de tokens). Suites dirigidas **0 failed / 0 error** (P1 3 +
P2 1 + P3 2 + P4 7). **Sobrescritura de borradores**: pendiente de autorización de Mauricio. **Sin
commit/push/despliegue; TEST remoto intacto.** -->

<!-- actualizado: 2026-10-12 (3) — **BLINDAJE DE BORRADORES (LOCK)**: `19` **§19.30**, `02` §17.16.28, `03` §29.
Versiones: 19 **1.28.0**, 02 **12.37.0**, 03 **6.36.0**. Módulo `madenat_lumber_logistics` **18.0.1.24.0** (core
sin cambios). `edit_version` + guard del documento (advisory ns 1 + comparación + flush) que **rechaza** la
edición obsoleta en Guardar/Aplicar (no sobrescribe ni fusiona); botón «Recargar versión actual»; líneas/repartos
y edición directa elevan la versión; sin adopción silenciosa del primer borrador ajeno. Suite `LOCK-01..19` +
FLOW + PHY ⇒ **0 failed / 0 error**. **Límite declarado:** form-vs-form directo (sin asistente). **Sin
commit/push/despliegue; TEST remoto intacto.** -->

<!-- actualizado: 2026-10-12 (4) — **CIERRE V1–V3 del blindaje de borradores**: `19` **§19.31**, `02` §17.16.29,
`03` §29. Versiones: 19 **1.29.0**, 02 **12.38.0**, 03 **6.37.0**. Módulo `madenat_lumber_logistics`
**18.0.1.25.0** (core sin cambios). V1 (edición directa): Alternativa A con `force_save` + guard atómico en
`write()` ⇒ matriz **C1–C8 ACREDITADA**; límite residual: escritura ORM/RPC sin `edit_version`. V2 (cliente):
**PENDIENTE** (sin navegador; guion entregado). V3 (transacción/bloqueos): **ACREDITADA** (TX-01..13; orden
`1→2→3`; rechazo por versión y por lock). **Sin commit/push/despliegue; TEST remoto intacto.** -->

<!-- actualizado: 2026-10-12 (5) — **INCIDENCIA `stock_quant_lot_id_fkey`**: `19` **§19.32**. Versión `19`
**1.30.0**. Módulo `madenat_lumber_core` **18.0.6.7.0**. Diagnóstico **solo lectura**: causa = intento de
**eliminar** desde el visor **estándar** de lotes la etiqueta SV `SV000000841` (con +40.315 m³ en `WH/Stock`); la
BD **protegió correctamente** el historial (NO es defecto del desarrollo; `stock.lot` no tiene `active` ⇒ no se
archiva). Corrección mínima de robustez: **guarda proactiva** de la etiqueta SV de volumen con filas en
`stock.quant` (`_sv_guard_unlink`) + **traducción** de la `ForeignKeyViolation` a mensaje de negocio
(`stock.lot.unlink`, con `savepoint`); **no** cambia qué se puede borrar. Pruebas
`test_sv_lot_unlink_guard.py` (4 → **0 failed/0 error**); regresión `core+intake+logistics` **1279 → 6 failed /
4 error** con el **mismo** conjunto de 10 fallos preexistentes (diff idéntico). Lote 10215 y quants 7840/7841
**intactos**. **Sin commit/push/despliegue; TEST remoto intacto.** -->
