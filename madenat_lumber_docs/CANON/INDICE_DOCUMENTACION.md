# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 12.12.0
**Fecha de actualización:** 2026-10-10  <!-- actualizado: 2026-10-10 (1) — **CIERRE FUNCIONAL DE PENDIENTES (P0–P4)** documentado en `02_CONTINUIDAD.md` **§17.16** y `03_TESTS.md` **§14**; `05_BACKLOG.md` actualiza el estado de Q1–Q4. Versiones: 02 **12.16.0**, 03 **6.16.0**, 05 **8.15.0**; índice **12.10.0**. Entorno de ejecución: `madenat_test` / `localhost:8069` (contenedor `odoo18_app`), sin commit/push ni despliegue remoto. | 2026-10-08 (5) — REVALIDACIÓN (2.ª pasada) con la **biblioteca externa de muestras** `muestras_documentos_ingreso` (ruta real: `…/odoo-18-ce/muestras_documentos_ingreso`, **fuera** de `custom_addons`): **02 §17.15** (matriz R01–R16 **revalidada**, correcciones C1–C10 a la 1.ª pasada, conciliación por línea de Ferramenta, local↔remoto), **03 §13.5–13.6** (relación prueba↔etapa↔resultado con niveles A–F), **05** «REVALIDACIÓN 2026-10-08 (2.ª pasada)». Antecedente incorporado: **Mauricio confirma que se probaron todos los ingresos**. Evidencia reconstruida: registros reales en el respaldo de la base **local** (`BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump`) — `26270` con **17 lotes** y adjuntos, `19846/19827/19826`, `4495589` (granel), `95806` (granel), `39519` (producto) — más **1 fixture byte-idéntico** (Arauco) y **fixtures derivados** (Byc, Fátima, JCE). Se rectifican: «ninguno de los 5 formatos fue probado», «48,009 es un error», «JCE no se lee», «Arauco exige Excel», «operación no válida = paráfrasis» y la atribución del `OwlError` (**reportado por Mauricio**). Versiones: 02 **12.15.0**, 03 **6.15.0**, 05 **8.14.0**; índice **12.9.0**. | 2026-10-08 (4) — sincronización por la auditoría de las solicitudes de Cristhian (2026-09-02/07): **02 §17.14** (síntesis, entornos verificados, matriz consolidada R01–R16 y hallazgos), **03 §13** (relación requisito → evidencia → resultado), **05** «Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08». Versiones: 02 12.14.0, 03 6.14.0, 05 8.13.0; índice 12.8.0. Entornos: código local (rama `feat/guia-correccion-documental-preservada-20261002`, HEAD `e302c48`, 62 modificados + 14 sin seguimiento) **y** TEST remoto inspeccionado solo lectura (314 archivos con 0 discrepancias de hash; 39 archivos legado solo en el remoto). Sin cambios de código, datos ni servicios. | 2026-10-08 (3) — 02 §17.13 / 03 §12.6 / 05 «Retorno de servicio (AD-102)»: **A/B aplicado en el desarrollo existente** (`madenat_test` / `http://localhost:8069`) + **reorganización de la UI de Ingreso de Madera** (resumen 2 columnas, «Aplicar cambios» debajo de los campos, línea de retorno a todo el ancho, Evidencia documental 3 columnas con encabezado único, packing list a todo el ancho); dirigidas **88/88** en verde **sobre `madenat_test`** (incl. Cristhian uid 8, `su=False`); respaldos verificados en `BACKUP_AB_APPLY_20261008/`; **aislamiento temporal retirado** (`srvretab_web`/8070, volumen `srvretab_web_data`, bases `srvretab_*_20261007`, `/tmp/{gate,ab_dryrun,iso_*}`); **V3 (navegador) pendiente**. 02 12.13.0, 03 6.13.0, 05 8.12.0; índice 12.7.0. | 2026-10-08 (2) — 02 §17.12bis / 03 §12.5: entorno aislado **recreado** (autorizado; workcopy `:ro`, sin aplicar diffs; filestore repoblado desde el stack en `:ro`); 02 12.12.1, 03 6.12.2, 05 8.11.1. **V3 pendiente de evidencia manual.** Índice 12.6.4. | 2026-10-08 (1) — retoma de SOLO LECTURA (2026-10-08): 02 §17.12, 03 §12.5, 05 8.11.0. Revalidación conforme (rama/HEAD Git; SHA-256 de A/B/AB = checkpoint; workcopy = árbol activo + 15 archivos de `AB_completo.diff`; `patch --dry-run` limpio; A/B ausente del código activo y de `madenat_test`). **Entorno aislado NO conservado** tras el reinicio del host (contenedor `srvretab_web` inexistente, puerto 8070 cerrado, `/tmp/gate` vacío; base `srvretab_gate_20261007` intacta) ⇒ **V3 sigue pendiente**; recrear el aislamiento pendiente de autorización. Índice 12.6.3. | 2026-10-07 (4) — checkpoint de pausa (02 §17.11, 05 8.10.0): A/B solo en aislamiento; gate sobre copia del activo con cambios locales 45/45; dirigidas 88/88 incl. Cristhian (uid 8, su=False, grupos intactos); V3 pendiente; A/B no aplicados; entorno aislado conservado. Índice 12.6.2. | 2026-10-07 (3) — gate previo A/B sobre COPIA del árbol activo con cambios locales (byte a byte = workcopy; diffs sin documentación): 88/88 dirigidas en verde incl. usuario real Cristhian (su=False, grupos intactos); servidor aislado de navegador `http://127.0.0.1:8070` (V3 PENDIENTE, sin navegador). 02 §17.10, 03 6.12.0 (§12.4); índice 12.6.1. | 2026-10-07 (2) — AD-102 (retorno de servicio: identificación no bloqueante + reglas de imputación I2; implementado/probado en copia aislada `IMPL_SERVICE_RETURN_AB_20261007/`, NO aplicado). Sincroniza 02 12.10.0, 03 6.11.0, 04 (AD-102), 05 8.9.0, 12 1.8.0 §11.9, 19 1.7.0 §19.9; índice 12.6.0. | 2026-10-07 — §17 de `02_CONTINUIDAD.md`: auditoría de retoma de la «confirmación de retorno de servicio» al enviar a stock (NO aplicada; especificación solo en el antecedente `IMPL_SERVICE_RETURN_20261006/`). Sincroniza 02 12.9.0 (§17) y 05 8.8.0; índice 12.5.6. | AD-101 (búsqueda, filtros y agrupaciones de la Consola de Intake; aplicada en `madenat_test`): sincronización de versiones 00 7.18.0 (§4.10), 02 12.8.0 (§16), 03 6.10.0 (§11), 04 12.18.0 (AD-101), 05 8.7.0; índice 12.5.5. | 2026-10-02 (6) — sincroniza índice con AD-90 (semántica de inventario en procesador y pendiente de consolidación documental) y versiones 04 12.15.0, 05_BACKLOG 8.5.0, 19 1.5.0; índice 12.4.0; (7) — AD-91: I2 documental (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`), sin efecto en stock; salida nativa + ledger a I3; tres saldos separados (físico / `sv_available_m3` / documental); cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; costo I5; merma/cierre posterior. Versiones 04 12.16.0, 05_BACKLOG 8.6.0, 19 1.6.0; índice 12.5.0; (8) — precisa el nombre del campo de clave documental de I2: `documentary_key` (implementado en `madenat_lumber_logistics`, AD-91); 19 1.6.1; índice 12.5.1; (9) — precisa la semántica de estados de I2 (reserva documental temporal de capacidad nominal de etiqueta `I2_ACTIVE_STATES` vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`; `pending` mantiene la reserva temporal; sin cambio funcional). Versiones 04 12.16.1, 05_BACKLOG 8.6.1, 19 1.6.2; índice 12.5.2; (10) — §4.2 de 00: política de corrección/reset de recepción no bloqueante y trazable (reversión por movimientos nativos; sin borrado de stock.quant/lotes/pickings/movimientos); AD-80 precisa el alcance del principio de no-borrado (límite: el reset de guía action_reopen_to_draft permanece pendiente). Versiones 00 7.14.0, 04 12.16.2; índice 12.5.3; (11) — G1: reapertura de guía procesada no bloqueante y trazable (00 §4.3; AD-80 actualizado): wizard + reversión nativa del consumo BT-04; conservación de historia física sin vínculo fuerte; sin escribir/borrar `stock.quant` ni mutar `origin`; auditoría `deviation` + chatter. G2/G3 pendientes. Versiones 00 7.15.0, 04 12.16.3; índice 12.5.4 -->
<!-- actualizado: 2026-10-10 (2) — **ACEPTACIÓN VISUAL (guía 19827) + FLUJO SV CONFIRMADO**: 02 §17.16.8/§17.16.9, 03 §14.4, 05 «Aceptación visual …», 19 §19.10. Versiones: 02 **12.17.0**, 03 **6.17.0**, 05 **8.16.0**, 19 **1.8.0**; índice **12.11.0**. Solo documentación; sin cambios de código, base ni servicios. -->
<!-- actualizado: 2026-10-10 (3) — **CONCILIACIÓN ENVÍO–RETORNO (Bloque A/B/C)**: `19` §19.11 (modelo `madenat.processor.return.link`) y §19.12 (Bloque D, diseño requerido, NO implementado), `02` §17.16.10, `03` §15/§15.4/§15.5 (evidencia web por niveles + controles), `05` «Conciliación envío–retorno (Bloque A/B/C) — IMPLEMENTADO». Versiones: 19 **1.9.0**, 02 **12.18.0**, 03 **6.18.0**, 05 **8.17.0**; índice **12.12.0**. Módulos: `madenat_lumber_logistics` **18.0.1.7.0**, `madenat_lumber_core` **18.0.6.6.0**. Cierra la brecha (a) de `19` §19.10. Bloque D NO implementado. Evidencia web por niveles: (a) integración web/RPC con sesión — **ejecutada**; (b) lectura de arquitecturas de vistas y metadatos — **verificada**; (c) renderizado e interacción en navegador real — **pendiente** ((a)+(b) **no** sustituyen a (c); V3 no acreditada). Controles/acreditación: `03` §15.5. Entorno `madenat_test`; sin commit/push. Evidencia: `CONCILIACION_ENVIO_RETORNO_20261010/`. -->

**Estado:** ACTIVO — Mapa maestro de documentación canónica
**Responsable revisión:** 2026-10-01 — Alta del documento canónico `18_CONSOLIDACION_Y_REBAJA.md` (especificación de consolidación y rebaja de contenedores y naves, BORRADOR/PROPUESTA) y de AD-85 y AD-86 en estado PROPUESTA; actualización de versiones/índice. **2026-10-02:** alta de AD-91 (modelo documental de imputación SV por guía procesada, I2) — I2 acotado a documental sin efecto en stock; salida nativa + ledger a I3; tres saldos; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; costo I5; merma/cierre posterior — y sincronización de versiones 04/05/19.

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
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma (incluye §14 Gestión Operativa de Etiquetas SV, §15 Fase 2, §16 Búsqueda/filtros de la Consola de Intake y §17 Auditoría de retoma — confirmación de retorno de servicio al enviar a stock; §17.10 identificación no bloqueante + imputación posterior, AD-102; §17.11 checkpoint de pausa 2026-10-07→08; §17.12 retoma 2026-10-08 — solo lectura y entorno aislado recreado; **§17.13 A/B aplicado en el desarrollo existente `madenat_test` + reorganización de la UI de Ingreso de Madera + retiro del aislamiento (V3 pendiente)**; §17.14 auditoría de las solicitudes de Cristhian 2026-09-02/07 — matriz R01–R16, entornos verificados (local inoperativo desde la distro; TEST remoto solo lectura) y hallazgos H-1..H-7**; **§17.15 REVALIDACIÓN con la biblioteca externa de muestras: matriz R01–R16 revalidada, correcciones C1–C10 a la 1.ª pasada, conciliación por línea de Ferramenta y correspondencia local↔remoto**) | 12.18.0 | 2026-10-10 | ✅ Vigente |
| `03_TESTS.md` | Matriz de validación funcional y técnica (incluye §9 cobertura de la suite `sv` y §11 búsqueda/filtros/agrupaciones de la Consola de Intake; §12 retorno de servicio / imputación posterior, AD-102; §12.4 gate histórico sobre copia del árbol activo; §12.5 retoma 2026-10-08 — V3 no ejecutada; **§12.6 A/B + UI aplicados y probados en `madenat_test` — 88/88 dirigidas, V3 pendiente**); §13 relación requisito→evidencia→resultado de las solicitudes de Cristhian (R01–R16) y §13.3 ausencias de evidencia declaradas**; **§13.5–13.6 reconstrucción de pruebas con la biblioteca de muestras (niveles A–F, correspondencia con V0–V3, fuerza de la evidencia)**) | 6.18.0 | 2026-10-10 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación (AD-80; AD-81 PROPUESTA; **AD-82 y AD-84 APROBADAS e implementadas**; **AD-83 REEMPLAZADA por AD-87**; AD-85..86 PROPUESTA; **AD-87 (imputación etiqueta→SV) y AD-88 (advertir/motivar/auditar) APROBADAS**; **AD-89 (saldo por procesador: fuente física `stock.quant` y dos niveles; envío parcial ≠ desviación; riesgo de reservas/backorders) APROBADA**; **AD-90 (semántica de inventario en procesador y pendiente de consolidación documental) APROBADA**; **AD-91 (modelo documental de imputación SV por guía procesada, I2: modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`; I2 sin efecto en stock; salida nativa + ledger a I3; tres saldos separados; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; costo I5; merma/cierre posterior; precisión de estados I2: reserva documental temporal de etiqueta `I2_ACTIVE_STATES` vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`) APROBADA**; **AD-101 (2026-10-07, búsqueda/filtros/agrupaciones de la Consola de Intake — OC documental/vinculada, `guide_date_kind`, modalidades, producto real por líneas, procesador por Orden de Procesamiento) APLICADA en `madenat_test`**; **AD-102 (2026-10-07, retorno de servicio — identificación no bloqueante + reglas de imputación I2) IMPLEMENTADA EN COPIA AISLADA**) | 12.19.0 | 2026-10-07 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases (incluye deuda T1–T7, «Rebaja de contenedor/nave (AD-82/84/83) — IMPLEMENTADO», «Rebaja — Endurecimiento y AD-88 (I0) — IMPLEMENTADO», «Auditoría 2026-10-01 — pendientes por área» e «Imputación SV y Procesadores (AD-87/88) — PLAN (fases I1..I6; I1 ✅ IMPLEMENTADO 2026-10-02; decisiones post-I1 D-I1-01..D-I1-05 / AD-89 / AD-90)» e «Búsqueda/filtros/agrupaciones de la Consola de Intake (2026-10-07, AD-101) — APLICADO», «Retorno de servicio — identificación no bloqueante + imputación posterior (AD-102) — **APLICADO EN `madenat_test` + UI de Ingreso de Madera reorganizada (2026-10-08)**; V3 pendiente»; nueva sección «Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08» con R01–R16 clasificados: **acreditados R02/R12/R13**, acreditados parcialmente R14/R16 y **abiertos los 5 formatos de proveedor**; **sección «REVALIDACIÓN 2026-10-08 (2.ª pasada) — pruebas reconstruidas con la biblioteca de muestras»: R02/R03/R06/R09/R11 verificados con muestra real, R05/R07/R08 en alcance parcial y pendientes Q1–Q8**) | 8.17.0 | 2026-10-10 | ✅ Vigente |
| `05_AUDITORIA_XML_IDS.md` | Auditoría de XML IDs — R1 Stock Detail | 1.1.0 | 2026-09-25 | ✅ Vigente |
| `06_CHECKLIST.md` | Checklist operativo de sesión — ARCHIVADO en LEGADO | 4.2.0 | 2026-06-30 | 🏷️ ARCHIVADO — reemplazado por checklist A-F en este índice |
| `07_TRABAJO_CON_IA.md` | Protocolo de trabajo con IA | 7.3.0 | 2026-07-01 | ✅ Vigente |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end (§7 corregido 2026-10-01: `account_id` no existe) | 1.7.0 | 2026-10-01 | ✅ Vigente |
| `09_FASE_DOCUMENTAL_MAESTRA.md` | Mapa maestro consolidado — ARCHIVADO, checklist migrado a este índice | 1.1.0 | 2026-06-16 | 🏷️ ARCHIVADO — checklist A-F consolidado en Anexo A |
| `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria Fase A — ARCHIVADO en LEGADO/auditorias | — | 2026-06-04 | 🏷️ ARCHIVADO — Fase A completada, evidencia histórica |
| `11_FASE_E_VALIDACION.md` | Validación end-to-end, CI pipeline, runbook operativo | 1.1.0 | 2026-06-16 | ✅ Derivado vigente |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta de madera y discriminación operativa (incluye §11.5 volumen oficial de Recepción por Volumen y §11.8 imputación SV etiqueta→SV y §11.9 identificación no bloqueante de retorno de servicio) | 1.8.0 | 2026-10-07 | ✅ Vigente |
| `12_ARQUITECTURA_OPERATIVA_PERFILES.md` | Arquitectura operativa y perfiles — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md` | Arquitectura técnica de implementación — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — diseño no implementado |
| `14_GUIA_EJECUCION_INCREMENTAL.md` | Guía de ejecución incremental — ARCHIVADO en LEGADO/diseno | 1.0.0 | 2026-06-05 | 🏷️ ARCHIVADO — plan no ejecutado |
| `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación actual | 1.1.0 | 2026-06-06 | ✅ Derivado vigente |
| `13_CONSOLIDACION_OPERATIVA.md` | Consolidación operativa: ingesta (Producto/Procesados), reglas, trazabilidad, matriz de hallazgos, contradicciones, matriz operativa de Etiquetas SV (§13) e imputación SV / merma documental (§11) | 2.0.0 | 2026-10-01 | ✅ Vigente |
| `16_AUDITORIA_20261001.md` | **NUEVO** — Auditoría 2026-10-01: hallazgos H-01..H-16 y N-01..N-10, clasificados por área (Operaciones / Contabilidad-Auditoría-Facturación / Logística / Fase 6); resueltos, pendientes, parámetro `dev_cleanup_enabled` y mapeo de grupos huérfanos | 1.0.0 | 2026-10-01 | ✅ Vigente |
| `17_CONSTITUCION_VOLUMENES.md` | Constitución de Volúmenes: definiciones NOMINAL / DISPONIBLE / EXPORTACIÓN / OFICIAL (acordadas 2026-10-01), reglas de uso por proceso, reglas acordadas para diseño futuro (ACORDADO), glosario de etiquetas, conciliación documental (modelo_despachos:449 / AD-67); §6 F-01/F-02 RESUELTOS; §2.8 reescrita (SV nunca se exporta; salida por imputación, AD-87) | 1.2.0 | 2026-10-01 | ✅ Vigente |
| `18_CONSOLIDACION_Y_REBAJA.md` | Consolidación y rebaja de contenedores y naves: alcance y glosario (tres usos de «consolidación»), puntos acordados (2026-10-01), modelo/estados, reglas de rebaja, vía SV e invariantes, pantallas (incl. §7.5 imputación SV fuera de la exportación), permisos, plan de pruebas, migración, preguntas abiertas, riesgos y §14 Estado de implementación + §14.6 clasificación de bloqueos (AD-88) | 1.2.0 | 2026-10-01 | 🟢 EN IMPLEMENTACIÓN |
| `19_IMPUTACION_SV_Y_PROCESADORES.md` | **NUEVO** — Imputación declarada etiqueta→SV y saldo por procesador: glosario, ciclo por tipo de compra (C1 SV / C2 procesado), modelo de datos mínimo (`madenat.sv.imputation`, ledger `imputacion`, ubicaciones `Procesadores/<X>`, costo), estados, reglas, alertas, roles, UX (propuesta por proveedor/producto/antigüedad), casos límite, migración, riesgos, clasificación de bloqueos (§14, con estado del bloque I0) y plan de pruebas T-01..T-12; backlog por fases I0..I6 (§16, con **I0 e I1 implementados** — I1 el 2026-10-02; **AD-89 / D-I1-01..04**: `stock.quant` y las ubicaciones internas como **fuente física de verdad**; saldo en **dos niveles** (resumen agregado implementado y **detalle por lote planificado** para después de la imputación SV→etiqueta); **envío parcial ≠ desviación** — motivo solo ante diferencia con propuesta/planificación/reserva; **corrección implementada 2026-10-02**; **riesgo pre-producción**: validar disponibilidad frente a **reservas/backorders**; **AD-90 / D-I1-05**: semántica de inventario en procesador — **custodia operativa** MADENAT, **SV pendiente de consolidación documental**, **cuatro categorías de saldo**, **dos órdenes temporales**; **I2 sigue pendiente**; **AD-91 / D-I2-11..19**: I2 **documental sin efecto en stock** (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; tres saldos separados; costo I5; merma/cierre posterior); **salida nativa + ledger a I3**; **I2 sigue PENDIENTE**; precisión de estados: reserva documental temporal de etiqueta `I2_ACTIVE_STATES` (draft/pending/applied, techo duro) vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`; `pending` mantiene la reserva temporal) y preguntas Q-19 (§17, resueltas 2026-10-01: 1/2/5/8; §19.9 estado de I2 (código presente) + reglas de identificación de retorno, AD-102; §19.10 flujo operativo de imputación confirmado en código, controles y brechas) | 1.9.0 | 2026-10-10 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 12.12.0 | 2026-10-10 | ✅ Vigente |

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
  herencia de vista (ver `00_ARQUITECTURA.md` §3.4).