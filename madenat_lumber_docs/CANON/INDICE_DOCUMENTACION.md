# Índice de Documentación — MADENAT Lumber Core

**Versión documental:** 12.33.0
**Fecha de actualización:** 2026-10-15  <!-- actualizado: 2026-10-15 (1) — **alta `04` AD-106** (supuesto de **UNA sola compañía**: sin `company_id` ni `ir.rule` de compañía en `madenat.guia.processing`, con condición de reapertura; conservación de los 3 usuarios inactivos `@madenat.test`, D7 = CONSERVAR). Sincroniza `04` 12.22.0 y `05` 8.27.0; índice 12.32.0 → 12.33.0. Commit local ① (FASE 5); sin push ni despliegue. | 2026-10-12 (9) — **FASE 4 (cierre de brechas H1–H6)**: `04` **AD-105** (H1 motivo obligatorio en toda vía —la vía directa se bloquea con mensaje que guía al asistente—; H2 rol **jefatura/sistema** en lugar del grupo técnico `stock.group_stock_manager`; H3/**H-SEC-5** bitácora `madenat.audit.log` **APPEND-ONLY** por ORM —`write`/`unlink` bloqueados incluso con `sudo`— con bypass test-only inerte y **límite honesto frente a SQL/DBA declarado**; H4 escenario (f) de costos; H6 fixtures `*_oper` sin residuo). Core 18.0.6.8.0 → **18.0.6.9.0**; intake 18.0.0.14.0 → **18.0.0.15.0**; logistics 18.0.1.26.0 → **18.0.1.27.0**. Pruebas nuevas en verde (36/36 H1–H3; 7/7 reclasificación AD-73) y regresión **6/4 de 1448** con el **mismo conjunto de 10 fallas** (0 nuevas). Saneamiento local H5: 48 socios de prueba eliminados por IDs explícitos; bitácora y usuarios `@madenat.test` intactos. Versión `04` 12.20.0 → **12.21.0**; índice 12.31.0 → **12.32.0**. Expediente `AUDITORIA_INTEGRAL_20261012/fase4/`. Sin commit/push. | 2026-10-12 (8) — **FASE 3 (guardas G1/G2)**: `04` **AD-104** (guardas de eliminación de guía D-G1..D-G4 + fixture G2). Core 18.0.6.7.0 → **18.0.6.8.0**; intake 18.0.0.13.0 → **18.0.0.14.0**. Escenarios a–m en verde; regresión sin fallas nuevas; H-SEC-5 sigue **pendiente**. Versión `04` 12.19.0 → **12.20.0**; índice 12.30.0 → **12.31.0**. Expediente `AUDITORIA_INTEGRAL_20261012/fase3/`. Sin commit/push. | 2026-10-12 (7) — **FASE 2 limitada (higiene)**: D13 restituye los **cuerpos literales** de `02` §17.16.19…§17.16.29 desde los expedientes (26/26 referencias resueltas; sin modificar líneas existentes); D14 indexa los snapshots de `madenat_lumber_docs` (fuente canónica = `custom_addons/madenat_lumber_docs`) y añade `SNAPSHOT.md` a las 19 copias; `02` 12.39.0 → **12.40.0**; índice 12.29.0 → **12.30.0**. Expediente `AUDITORIA_INTEGRAL_20261012/fase2/`. Sin commit/push. | 2026-10-12 (6) — **HOTFIX OWL chatter**: Odoo 18 CE ya no compila `div.oe_chatter`; los campos del chatter se filtraban como listas o2m editables (`mail.message`/`mail.followers`) con «Agregar una línea» y `OwlError` en `get urlRelation`. Corrección mínima de vistas (`<chatter/>`) en `sv_imputation`/`processor_return_link`. `19` §19.33, `02` §17.16.30, `03` §30, `05`. Módulo `madenat_lumber_logistics` **18.0.1.25.0 → 18.0.1.26.0**; VIEW-01..05 servidor 5/5; regresión sin fallas nuevas; **navegador pendiente**. Versiones: `19` **1.31.0**, `02` **12.39.0**, `03` **6.38.0**, `05` **8.26.0**; índice **12.29.0**. **Alineación:** `02` renumerada (§17.16.19 → §17.16.30; estaba reservada) y versiones alineadas con el último registro (02 12.38.0, 03 6.37.0). Sin commit/push. | 2026-10-10 (1) — **CIERRE FUNCIONAL DE PENDIENTES (P0–P4)** documentado en `02_CONTINUIDAD.md` **§17.16** y `03_TESTS.md` **§14**; `05_BACKLOG.md` actualiza el estado de Q1–Q4. Versiones: 02 **12.16.0**, 03 **6.16.0**, 05 **8.15.0**; índice **12.10.0**. Entorno de ejecución: `madenat_test` / `localhost:8069` (contenedor `odoo18_app`), sin commit/push ni despliegue remoto. | 2026-10-08 (5) — REVALIDACIÓN (2.ª pasada) con la **biblioteca externa de muestras** `muestras_documentos_ingreso` (ruta real: `…/odoo-18-ce/muestras_documentos_ingreso`, **fuera** de `custom_addons`): **02 §17.15** (matriz R01–R16 **revalidada**, correcciones C1–C10 a la 1.ª pasada, conciliación por línea de Ferramenta, local↔remoto), **03 §13.5–13.6** (relación prueba↔etapa↔resultado con niveles A–F), **05** «REVALIDACIÓN 2026-10-08 (2.ª pasada)». Antecedente incorporado: **Mauricio confirma que se probaron todos los ingresos**. Evidencia reconstruida: registros reales en el respaldo de la base **local** (`BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump`) — `26270` con **17 lotes** y adjuntos, `19846/19827/19826`, `4495589` (granel), `95806` (granel), `39519` (producto) — más **1 fixture byte-idéntico** (Arauco) y **fixtures derivados** (Byc, Fátima, JCE). Se rectifican: «ninguno de los 5 formatos fue probado», «48,009 es un error», «JCE no se lee», «Arauco exige Excel», «operación no válida = paráfrasis» y la atribución del `OwlError` (**reportado por Mauricio**). Versiones: 02 **12.15.0**, 03 **6.15.0**, 05 **8.14.0**; índice **12.9.0**. | 2026-10-08 (4) — sincronización por la auditoría de las solicitudes de Cristhian (2026-09-02/07): **02 §17.14** (síntesis, entornos verificados, matriz consolidada R01–R16 y hallazgos), **03 §13** (relación requisito → evidencia → resultado), **05** «Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08». Versiones: 02 12.14.0, 03 6.14.0, 05 8.13.0; índice 12.8.0. Entornos: código local (rama `feat/guia-correccion-documental-preservada-20261002`, HEAD `e302c48`, 62 modificados + 14 sin seguimiento) **y** TEST remoto inspeccionado solo lectura (314 archivos con 0 discrepancias de hash; 39 archivos legado solo en el remoto). Sin cambios de código, datos ni servicios. | 2026-10-08 (3) — 02 §17.13 / 03 §12.6 / 05 «Retorno de servicio (AD-102)»: **A/B aplicado en el desarrollo existente** (`madenat_test` / `http://localhost:8069`) + **reorganización de la UI de Ingreso de Madera** (resumen 2 columnas, «Aplicar cambios» debajo de los campos, línea de retorno a todo el ancho, Evidencia documental 3 columnas con encabezado único, packing list a todo el ancho); dirigidas **88/88** en verde **sobre `madenat_test`** (incl. Cristhian uid 8, `su=False`); respaldos verificados en `BACKUP_AB_APPLY_20261008/`; **aislamiento temporal retirado** (`srvretab_web`/8070, volumen `srvretab_web_data`, bases `srvretab_*_20261007`, `/tmp/{gate,ab_dryrun,iso_*}`); **V3 (navegador) pendiente**. 02 12.13.0, 03 6.13.0, 05 8.12.0; índice 12.7.0. | 2026-10-08 (2) — 02 §17.12bis / 03 §12.5: entorno aislado **recreado** (autorizado; workcopy `:ro`, sin aplicar diffs; filestore repoblado desde el stack en `:ro`); 02 12.12.1, 03 6.12.2, 05 8.11.1. **V3 pendiente de evidencia manual.** Índice 12.6.4. | 2026-10-08 (1) — retoma de SOLO LECTURA (2026-10-08): 02 §17.12, 03 §12.5, 05 8.11.0. Revalidación conforme (rama/HEAD Git; SHA-256 de A/B/AB = checkpoint; workcopy = árbol activo + 15 archivos de `AB_completo.diff`; `patch --dry-run` limpio; A/B ausente del código activo y de `madenat_test`). **Entorno aislado NO conservado** tras el reinicio del host (contenedor `srvretab_web` inexistente, puerto 8070 cerrado, `/tmp/gate` vacío; base `srvretab_gate_20261007` intacta) ⇒ **V3 sigue pendiente**; recrear el aislamiento pendiente de autorización. Índice 12.6.3. | 2026-10-07 (4) — checkpoint de pausa (02 §17.11, 05 8.10.0): A/B solo en aislamiento; gate sobre copia del activo con cambios locales 45/45; dirigidas 88/88 incl. Cristhian (uid 8, su=False, grupos intactos); V3 pendiente; A/B no aplicados; entorno aislado conservado. Índice 12.6.2. | 2026-10-07 (3) — gate previo A/B sobre COPIA del árbol activo con cambios locales (byte a byte = workcopy; diffs sin documentación): 88/88 dirigidas en verde incl. usuario real Cristhian (su=False, grupos intactos); servidor aislado de navegador `http://127.0.0.1:8070` (V3 PENDIENTE, sin navegador). 02 §17.10, 03 6.12.0 (§12.4); índice 12.6.1. | 2026-10-07 (2) — AD-102 (retorno de servicio: identificación no bloqueante + reglas de imputación I2; implementado/probado en copia aislada `IMPL_SERVICE_RETURN_AB_20261007/`, NO aplicado). Sincroniza 02 12.10.0, 03 6.11.0, 04 (AD-102), 05 8.9.0, 12 1.8.0 §11.9, 19 1.7.0 §19.9; índice 12.6.0. | 2026-10-07 — §17 de `02_CONTINUIDAD.md`: auditoría de retoma de la «confirmación de retorno de servicio» al enviar a stock (NO aplicada; especificación solo en el antecedente `IMPL_SERVICE_RETURN_20261006/`). Sincroniza 02 12.9.0 (§17) y 05 8.8.0; índice 12.5.6. | AD-101 (búsqueda, filtros y agrupaciones de la Consola de Intake; aplicada en `madenat_test`): sincronización de versiones 00 7.18.0 (§4.10), 02 12.8.0 (§16), 03 6.10.0 (§11), 04 12.18.0 (AD-101), 05 8.7.0; índice 12.5.5. | 2026-10-02 (6) — sincroniza índice con AD-90 (semántica de inventario en procesador y pendiente de consolidación documental) y versiones 04 12.15.0, 05_BACKLOG 8.5.0, 19 1.5.0; índice 12.4.0; (7) — AD-91: I2 documental (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`), sin efecto en stock; salida nativa + ledger a I3; tres saldos separados (físico / `sv_available_m3` / documental); cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; costo I5; merma/cierre posterior. Versiones 04 12.16.0, 05_BACKLOG 8.6.0, 19 1.6.0; índice 12.5.0; (8) — precisa el nombre del campo de clave documental de I2: `documentary_key` (implementado en `madenat_lumber_logistics`, AD-91); 19 1.6.1; índice 12.5.1; (9) — precisa la semántica de estados de I2 (reserva documental temporal de capacidad nominal de etiqueta `I2_ACTIVE_STATES` vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`; `pending` mantiene la reserva temporal; sin cambio funcional). Versiones 04 12.16.1, 05_BACKLOG 8.6.1, 19 1.6.2; índice 12.5.2; (10) — §4.2 de 00: política de corrección/reset de recepción no bloqueante y trazable (reversión por movimientos nativos; sin borrado de stock.quant/lotes/pickings/movimientos); AD-80 precisa el alcance del principio de no-borrado (límite: el reset de guía action_reopen_to_draft permanece pendiente). Versiones 00 7.14.0, 04 12.16.2; índice 12.5.3; (11) — G1: reapertura de guía procesada no bloqueante y trazable (00 §4.3; AD-80 actualizado): wizard + reversión nativa del consumo BT-04; conservación de historia física sin vínculo fuerte; sin escribir/borrar `stock.quant` ni mutar `origin`; auditoría `deviation` + chatter. G2/G3 pendientes. Versiones 00 7.15.0, 04 12.16.3; índice 12.5.4 -->
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
<!-- actualizado: 2026-10-10 (10) — **REDISEÑO OPERATIVO DEL ASISTENTE «REGISTRAR REBAJA»**: `19` **§19.18**, `02` §17.16.16, `03` §20, `05`. Versiones: 19 **1.15.0**, 02 **12.24.0**, 03 **6.24.0**, 05 **8.23.0**; índice **12.18.0**. Módulo `madenat_lumber_logistics` **18.0.1.13.0**. Interfaz anterior **rechazada por Mauricio**; se rediseña el MISMO asistente: tabla de material del packing list (Etiqueta=`stock.lot.ref`, SKU/dimensiones declaradas por la regla de promoción, producto, subproducto, dimensiones técnicas, piezas, volumen documental), documental avanzada en columnas opcionales, formulario amplio (`o_xxl_form_view`, `target=current`), cabecera con saldo documental del SV, granularidad por lote sin doble conteo. Guía real 19827: **17/17** mapeados. Suite `test_sv_rebaja_material.py` = **8/8**; regresión **342 pruebas, 4 fallas preexistentes, 0 errores**. **Aceptación visual de Mauricio pendiente**. Sin commit/push. -->


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
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma (incluye §14 Gestión Operativa de Etiquetas SV, §15 Fase 2, §16 Búsqueda/filtros de la Consola de Intake y §17 Auditoría de retoma — confirmación de retorno de servicio al enviar a stock; §17.10 identificación no bloqueante + imputación posterior, AD-102; §17.11 checkpoint de pausa 2026-10-07→08; §17.12 retoma 2026-10-08 — solo lectura y entorno aislado recreado; **§17.13 A/B aplicado en el desarrollo existente `madenat_test` + reorganización de la UI de Ingreso de Madera + retiro del aislamiento (V3 pendiente)**; §17.14 auditoría de las solicitudes de Cristhian 2026-09-02/07 — matriz R01–R16, entornos verificados (local inoperativo desde la distro; TEST remoto solo lectura) y hallazgos H-1..H-7**; **§17.15 REVALIDACIÓN con la biblioteca externa de muestras: matriz R01–R16 revalidada, correcciones C1–C10 a la 1.ª pasada, conciliación por línea de Ferramenta y correspondencia local↔remoto**) | 12.19.0 | 2026-10-10 | ✅ Vigente |
| `03_TESTS.md` | Matriz de validación funcional y técnica (incluye §9 cobertura de la suite `sv` y §11 búsqueda/filtros/agrupaciones de la Consola de Intake; §12 retorno de servicio / imputación posterior, AD-102; §12.4 gate histórico sobre copia del árbol activo; §12.5 retoma 2026-10-08 — V3 no ejecutada; **§12.6 A/B + UI aplicados y probados en `madenat_test` — 88/88 dirigidas, V3 pendiente**); §13 relación requisito→evidencia→resultado de las solicitudes de Cristhian (R01–R16) y §13.3 ausencias de evidencia declaradas**; **§13.5–13.6 reconstrucción de pruebas con la biblioteca de muestras (niveles A–F, correspondencia con V0–V3, fuerza de la evidencia)**) | 6.19.0 | 2026-10-10 | ✅ Vigente |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación (AD-80; AD-81 PROPUESTA; **AD-82 y AD-84 APROBADAS e implementadas**; **AD-83 REEMPLAZADA por AD-87**; AD-85..86 PROPUESTA; **AD-87 (imputación etiqueta→SV) y AD-88 (advertir/motivar/auditar) APROBADAS**; **AD-89 (saldo por procesador: fuente física `stock.quant` y dos niveles; envío parcial ≠ desviación; riesgo de reservas/backorders) APROBADA**; **AD-90 (semántica de inventario en procesador y pendiente de consolidación documental) APROBADA**; **AD-91 (modelo documental de imputación SV por guía procesada, I2: modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`; I2 sin efecto en stock; salida nativa + ledger a I3; tres saldos separados; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; costo I5; merma/cierre posterior; precisión de estados I2: reserva documental temporal de etiqueta `I2_ACTIVE_STATES` vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`) APROBADA**; **AD-101 (2026-10-07, búsqueda/filtros/agrupaciones de la Consola de Intake — OC documental/vinculada, `guide_date_kind`, modalidades, producto real por líneas, procesador por Orden de Procesamiento) APLICADA en `madenat_test`**; **AD-102 (2026-10-07, retorno de servicio — identificación no bloqueante + reglas de imputación I2) IMPLEMENTADA EN COPIA AISLADA**) | 12.19.0 | 2026-10-07 | ✅ Vigente |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases (incluye deuda T1–T7, «Rebaja de contenedor/nave (AD-82/84/83) — IMPLEMENTADO», «Rebaja — Endurecimiento y AD-88 (I0) — IMPLEMENTADO», «Auditoría 2026-10-01 — pendientes por área» e «Imputación SV y Procesadores (AD-87/88) — PLAN (fases I1..I6; I1 ✅ IMPLEMENTADO 2026-10-02; decisiones post-I1 D-I1-01..D-I1-05 / AD-89 / AD-90)» e «Búsqueda/filtros/agrupaciones de la Consola de Intake (2026-10-07, AD-101) — APLICADO», «Retorno de servicio — identificación no bloqueante + imputación posterior (AD-102) — **APLICADO EN `madenat_test` + UI de Ingreso de Madera reorganizada (2026-10-08)**; V3 pendiente»; nueva sección «Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08» con R01–R16 clasificados: **acreditados R02/R12/R13**, acreditados parcialmente R14/R16 y **abiertos los 5 formatos de proveedor**; **sección «REVALIDACIÓN 2026-10-08 (2.ª pasada) — pruebas reconstruidas con la biblioteca de muestras»: R02/R03/R06/R09/R11 verificados con muestra real, R05/R07/R08 en alcance parcial y pendientes Q1–Q8**) | 8.18.0 | 2026-10-10 | ✅ Vigente |
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
| `19_IMPUTACION_SV_Y_PROCESADORES.md` | **NUEVO** — Imputación declarada etiqueta→SV y saldo por procesador: glosario, ciclo por tipo de compra (C1 SV / C2 procesado), modelo de datos mínimo (`madenat.sv.imputation`, ledger `imputacion`, ubicaciones `Procesadores/<X>`, costo), estados, reglas, alertas, roles, UX (propuesta por proveedor/producto/antigüedad), casos límite, migración, riesgos, clasificación de bloqueos (§14, con estado del bloque I0) y plan de pruebas T-01..T-12; backlog por fases I0..I6 (§16, con **I0 e I1 implementados** — I1 el 2026-10-02; **AD-89 / D-I1-01..04**: `stock.quant` y las ubicaciones internas como **fuente física de verdad**; saldo en **dos niveles** (resumen agregado implementado y **detalle por lote planificado** para después de la imputación SV→etiqueta); **envío parcial ≠ desviación** — motivo solo ante diferencia con propuesta/planificación/reserva; **corrección implementada 2026-10-02**; **riesgo pre-producción**: validar disponibilidad frente a **reservas/backorders**; **AD-90 / D-I1-05**: semántica de inventario en procesador — **custodia operativa** MADENAT, **SV pendiente de consolidación documental**, **cuatro categorías de saldo**, **dos órdenes temporales**; **I2 sigue pendiente**; **AD-91 / D-I2-11..19**: I2 **documental sin efecto en stock** (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; tres saldos separados; costo I5; merma/cierre posterior); **salida nativa + ledger a I3**; **I2 sigue PENDIENTE**; precisión de estados: reserva documental temporal de etiqueta `I2_ACTIVE_STATES` (draft/pending/applied, techo duro) vs saldo documental aplicado de SV `I2_DOCUMENTAL_STATES`; `pending` mantiene la reserva temporal) y preguntas Q-19 (§17, resueltas 2026-10-01: 1/2/5/8; §19.9 estado de I2 (código presente) + reglas de identificación de retorno, AD-102; §19.10 flujo operativo de imputación confirmado en código, controles y brechas); **§19.14 (2026-10-10): operación manual de asignaciones centrada en SV** (acción Logística → Asignaciones SV sobre `stock.lot` volumen con vistas dedicadas; alta desde el SV; selección explícita de etiquetas; conservación del borrador por *upsert*; integridad etiqueta–guía D10; coherencia de volumen D10/D11) | 1.11.0 | 2026-10-10 | ✅ Vigente |
| `INDICE_DOCUMENTACION.md` | Este archivo. Mapa maestro | 12.13.0 | 2026-10-10 | ✅ Vigente |

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
