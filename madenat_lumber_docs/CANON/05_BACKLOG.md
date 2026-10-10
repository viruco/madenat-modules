# MADENAT — Backlog Canónico

**Versión documental:** 8.17.0
**Fecha de actualización:** 2026-10-10  <!-- actualizado: 2026-10-10 (1) — nueva sección al final de «REVALIDACIÓN 2026-10-08 (2.ª pasada)»: **cierre funcional 2026-10-10** — Q1 (presentación de volúmenes) y Q2 (Nota de Venta JCE) **IMPLEMENTADOS EN DESARROLLO**; Q3 (packing PDF Arauco) **DECISIÓN FUNCIONAL** (ruta de Volúmenes); Q4 (ingresos reales `41994`/`95083`) **EJECUTADO EN DESARROLLO sin stock**; Q5 (V3) y Q6 (OwlError) **pendientes/no reproducidos**; Q7/Q8 **pendientes**. Ver `02_CONTINUIDAD.md` §17.16 y `03_TESTS.md` §14. | 2026-10-08 (5) — nueva sección «**REVALIDACIÓN 2026-10-08 (2.ª pasada) — pruebas reconstruidas con la biblioteca de muestras**»: antecedente incorporado (**Mauricio confirma que se probaron todos los ingresos**; formatos en `muestras_documentos_ingreso`, fuera de `custom_addons`). Rectifica la 1.ª pasada: **cerrado con evidencia reconstruida** R02 (11 ingresos reales), R03 (subproducto 100 % de líneas), R06 (26270: adjuntos + **17 lotes** + picking + réplica en TEST remoto), R09 (95806 guía por Volúmenes), R11 (4495589 guía, fixture byte-idéntico + motor real); **parcial**: R05 (equivalencia con `39519`), R08 (fixture derivado «investigación 95083»), R07 (**48,009 = volumen de embarque, no un error**); **pendientes** Q1–Q8 (presentación de volúmenes, Nota de Venta JCE, packing PDF Arauco, ingresos reales de 41994/95083, V3, OwlError, réplica remota, fixtures). Límites conservados. Ver `02_CONTINUIDAD.md` §17.15 y `03_TESTS.md` §13.5–13.6. | 2026-10-08 (4) — nueva sección «Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08»: se clasifican R01–R16 con evidencia; **solo R02, R12, R13, R14 (parcial) y R16 (parcial) quedan acreditadas**; R03/R04/R05/R06/R07/R08/R09/R10/R11/R15 permanecen ABIERTAS. No se cierra ningún requisito de proveedor: **ninguno** tiene evidencia de ingesta real (la base `madenat_test` del TEST remoto contiene **1** registro en `madenat_guia_processing`: guía **26270** Ferramenta, `validated`, `packing_volume_declared_m3` **vacío**, `documental_conciliation_state='partial'`). Ver `02_CONTINUIDAD.md` §17.14 y `03_TESTS.md` §13. | 2026-10-08 (3) — sección «Retorno de servicio — identificación no bloqueante + imputación posterior (AD-102)» pasa a **APLICADO EN EL DESARROLLO EXISTENTE (`madenat_test`)** + reorganización de la UI de Ingreso de Madera; dirigidas **88/88** sobre `madenat_test` (incl. Cristhian uid 8, `su=False`); aislamiento temporal **retirado**; **V3 (navegador) sigue pendiente**. | 2026-10-08 (2) — entorno aislado RECREADO (autorizado; workcopy `:ro`, sin diffs; filestore repoblado); **V3 pendiente de evidencia manual**. | 2026-10-08 (1) — RETOMA (SOLO LECTURA): revalidación conforme (rama/HEAD Git, SHA-256 de A/B/AB = checkpoint, workcopy = activo + 15 archivos de `AB_completo.diff`, `--dry-run` limpio, A/B ausente del activo y de `madenat_test`); **entorno aislado NO conservado** (reinicio del host: `srvretab_web` inexistente, puerto 8070 cerrado, `/tmp/gate` vacío; base `srvretab_gate_20261007` intacta) ⇒ **V3 sigue pendiente**; recrear el aislamiento pendiente de autorización. Ver 02 §17.12. | 2026-10-07 (3) — PAUSA (reanuda 2026-10-08): sección «Retorno de servicio…» marca la pausa; gate sobre copia del activo con cambios locales 45/45; dirigidas 88/88 (incl. Cristhian uid 8, su=False); V3 pendiente; A/B no aplicados. Ver 02 §17.11. | 2026-10-07 (2) — sección «Retorno de servicio — identificación no bloqueante + imputación posterior» actualizada a IMPLEMENTADO EN AISLAMIENTO (AD-102; copia `IMPL_SERVICE_RETURN_AB_20261007/`; 85/85 pruebas dirigidas; 0 regresiones). | nueva entrada «Confirmación de retorno de servicio (2026-10-07) — PENDIENTE (NO aplicado)» (antecedente `IMPL_SERVICE_RETURN_20261006/`; retoma en `02_CONTINUIDAD.md` §17). | nueva sección «Búsqueda, filtros y agrupaciones de la Consola de Intake (2026-10-07, AD-101) — APLICADO (madenat_test)» con sus pendientes (V3, instalación en base limpia, volumen numérico, otros orígenes de procesador, Abiertos/Finalizados). Ver 00 §4.10 y 03 §11. | 2026-10-02 (7) — AD-90 / D-I1-05: semántica SV en procesador (custodia operativa MADENAT, pendiente de consolidación documental); refinamiento de I2 a consolidación/imputación documental etiquetas→SV (no producción ni genealogía); cuatro categorías de saldo y dos órdenes temporales; I2 sigue PENDIENTE. Ver 19_IMPUTACION_SV_Y_PROCESADORES.md §2/§3/§5.4/§7.3/§16; (8) — corrección AD-89 D-I1-03/D-I1-04 IMPLEMENTADA (rama feat/procesadores-guardas-20261002): parcial manual sin motivo, libre = físico − reservado ajeno (reserva ajena intacta) y backorder nativo documentado; (9) — AD-91: I2 con alcance cerrado documental (modelo aditivo madenat.sv.imputation/.line/.sv.line; cabecera por guía, inmutabilidad/reversa, idempotencia por clave documental propia; duro etiqueta-side / blando SV-side; sin efecto en stock, sin ledger, sin costo); salida nativa + ledger a I3; costo a I5; merma/cierre posterior; I2 sigue PENDIENTE. Ver CANON/19 §4/§5/§6/§7/§13.2/§16; (10) — precisa la reserva documental temporal de etiqueta (I2_ACTIVE_STATES: draft/pending/applied, techo duro) frente al saldo documental aplicado de SV (I2_DOCUMENTAL_STATES: applied); pending mantiene la reserva temporal; draft/pending sin efecto en stock/ledger; sin cambio funcional ni de estado. Ver CANON/19 §6/§7.3. -->
<!-- actualizado: 2026-10-10 (2) — nueva sección «Conciliación envío–retorno (Bloque A/B/C) — IMPLEMENTADO (2026-10-10)»: modelo `madenat.processor.return.link`, cierra la brecha (a) de CANON/19 §19.10; Bloque D cuantitativo PENDIENTE. Versión 05 8.16.0 → 8.17.0. Sin commit/push. -->
**Estado:** ACTIVO — Se incorpora la clasificación por área de la auditoría del 2026-10-01 (Operaciones / Contabilidad-Auditoría-Facturación / Logística / Fase 6). El orden de trabajo vigente del usuario (AD-81 PROPUESTA) es: ingreso a stock → consolidación → mantenimiento → logística y exportación; lo contable, la auditoría y la facturación quedan **diferidos**. AD-74 (Ingreso por Volúmenes), AD-75 (asignación manual de proveedor) y AD-80 (UX de volumen oficial, bloque SV visible y ciclo de vida de guías, 2026-09-28) cerrados. Frente principal AD-65 conserva pendientes de UI/wizard. La **rebaja/reversa de Etiquetas SV y la asignación logística SV** están implementadas y validadas (AD-79) y **visibles y ejecutables desde la Consola y la Guía** (AD-80); la rebaja/registro físico de stock por Volúmenes **fuera** del flujo SV sigue no implementada. El **archivado (`active`) de guías queda diferido** a una fase separada. Programación 1 (AD-77) conserva pendientes de validación visual de R1, exportaciones XLSX y test automatizado.

---

## Regla de uso

Este backlog solo debe contener trabajo pendiente, prioridades activas y criterios de cierre.
Si un tema ya quedó fijado como regla, debe vivir en `04_DECISION_LOG.md`.
Si un tema ya quedó validado como estado, debe vivir en `02_CONTINUIDAD.md`.
Si un tema ya quedó evidenciado, debe vivir en `03_TESTS.md`.

---

## Resumen de cambios desde v7.0.0 (2026-09-15)

- **Diseño AD-64 validado por auditoría de código:** `source_lot_line_ids` + `qty_to_consume` con fallback — APROBADO CON AJUSTES, no aprobación simple.
- **Corrección a AD-63:** `madenat_ingestion_engine` ya está trackeado en git desde el commit `843ed0d` (2026-09-15, 22 archivos). La afirmación "nunca commiteado" quedó obsoleta; solo persiste la brecha de trazabilidad canónica.
- **Corrección de mapeo de dependencias:** se había reportado "cero referencias en otros módulos" para `source_lot_ids`; existe un consumidor cross-módulo real en `madenat_toll_processing` (`guia_processing_integration.py:37-40`, `stock_lot.py:62`).
- **Nueva pieza pendiente detectada para AD-65:** el wizard de intake fuerza `intake_direct_stock=True` en la ruta Procesado (`intake_wizard.py:413`), lo que salta BT-04 por completo. El flujo "granel → patio → Balance de Masa" de AD-65 necesita una tercera derivación que hoy no existe.
- **Deuda de higiene reconfirmada:** los directorios `backups_20260819_2013/` y `backups_20260819_2040/` siguen presentes en `madenat_lumber_core/` con copias completas de `madenat_guia_processing.py`.
- **Discrepancia de índice — CERRADA (2026-09-26):** `INDICE_DOCUMENTACION.md` lista `05_BACKLOG.md` con la versión vigente de este archivo; la entrada obsoleta (v6.3.0) quedó corregida en la sincronización documental de Gestión SV.
- **Discrepancia interna en README:** `madenat_ingestion_engine/README.md:246-248` afirma "solo depende de base", mientras `__manifest__.py:22` declara `depends: ['base', 'madenat_lumber_core']`.

---

*(Nota: Las Fases 0.5 a 3 se encuentran 100% completadas y su estado está documentado en `02_CONTINUIDAD.md`)*

---

## FRENTE PRINCIPAL — AD-65: Recepción a Granel + Balance de Masa + Consolidación Administrativa

**Estado:** Diseño aprobado (2026-09-12). Prerequisito AD-64 implementado y validado como AD-66 (13/13 tests). Tercera derivación implementada como parte de AD-68/AD-69 (test de integración granel→service con descuento de volumen verificado). AD-65 queda sin prerequisitos pendientes; resta únicamente la sección "Tareas de implementación de AD-65".

### Prerequisito AD-64 — diseño aprobado, con 3 ajustes obligatorios antes de codificar

- [x] Implementar modelo nuevo `madenat.guia.processing.source.lot.line` (`guia_processing_id` M2O cascade, `lot_id` M2O `stock.lot` required, `qty_to_consume` Float `digits=(16,3)` required), expuesto como `source_lot_line_ids` (One2many) en `madenat.guia.processing`, junto al `source_lot_ids` (M2M) existente sin reemplazarlo.
- [x] Ajuste 1 — Validación de rango: exigir `0 < qty_to_consume <= lot.volumen_m3` en la nueva rama de `_get_or_create_consumption_picking()`.
- [x] Ajuste 2 — Documentar la doble fuente de verdad como transitoria: `source_lot_ids` (M2M, legacy/fallback) y `source_lot_line_ids` (O2M, vía nueva) coexisten deliberadamente, preservando compatibilidad con `madenat_toll_processing` y con `TestGuiaProcessingConsumptionBT04`.
- [x] Ajuste 3 — No confundir volumen con costeo: este diseño resuelve el consumo parcial a nivel de stock, pero el prorrateo de `wood_cost_usd`/`total_cost_usd` sigue siendo brecha separada (diferida a Costeo por AD-65 §1.9).
- [x] Modificar `_get_or_create_consumption_picking()` (`madenat_guia_processing.py:3852`) con rama condicional: `source_lot_line_ids` con datos → usar `qty_to_consume` por línea; vacío → fallback a `qty = lot.volumen_m3`.
- [x] No modificar `_reverse_consumption_picking()` ni `action_force_cancel()` — ambos ya leen `qty = move.quantity or move.product_uom_qty` (líneas ~4026 y ~4313), agnósticos a consumo parcial.
- [x] Agregar ACL para el nuevo modelo en `madenat_lumber_core/security/ir.model.access.csv`.
- [x] Agregar tests nuevos en `test_guia_processing.py` (clase separada, sin tocar `TestGuiaProcessingConsumptionBT04`): consumo parcial por línea, bloqueo por `qty > volumen_m3`, fallback sin líneas.
- [x] Verificar que `madenat_toll_processing/models/guia_processing_integration.py:37-40` sigue funcionando con el fallback (solo verificación, sin modificación en esta etapa).

### Prerequisito adicional detectado — tercera derivación en intake

- [x] Diseñar (no implementar todavía) una tercera derivación en `intake_wizard.py` para el flujo de recepción a granel que NO fije `intake_direct_stock=True`, permitiendo que la guía resultante pueble `source_lot_line_ids` para envío parcial a proceso vía Balance de Masa. (Implementado en `_route_granel`, AD-68/AD-69: `intake_direct_stock=False` + test de integración granel→service.)

### Tareas de implementación de AD-65 (una vez resuelto el prerequisito AD-64)

- [x] Extender `madenat_ingestion_engine` con el motor de "mejor esfuerzo" en cascada: tabla PDF de columnas fijas configurables → subtotales por grupo → total de encabezado mínimo garantizado. (Implementado como AD-71, 2026-09-21: cascada de 4 niveles — tabla con bordes → clustering de palabras → suma de líneas → regex de cabecera. 49/49 tests verdes.)
- [x] Implementar selección manual de tipo de detalle (línea por línea vs. agregado) en el wizard de intake. (Implementado como AD-72, 2026-09-21: campo `tipo_detalle_granel` + `_create_granel_detail_lines()`. 38/38 tests verdes.)
- [x] Implementar wizard `intake.tipo_ingreso.reclassify.wizard` con registro en `madenat.audit_log`, disponible solo antes de Gate 3. (Implementado como AD-73, 2026-09-21: wizard `madenat.lumber.intake.reclassify.wizard` + `action_type='reclassification'`. 94/94 tests verdes.)
- [ ] Implementar registro de "Patio" como `stock.location` nativo bajo demanda (sin modelo propio).
- [ ] Implementar consolidación administrativa: pantalla única con guías candidatas, saldo disponible, asignación con un clic.
- [ ] Implementar menú Toll para Operaciones: campo "Enviar a proceso" + selección de procesador + botón único.
- [ ] Ajustar `ir.model.access.csv` de `madenat_toll_processing` para Operaciones.
- [ ] Extender `madenat_lumber_reports` con reporte de conciliación informativo.

### Criterio de salida

No se libera ninguna pieza de AD-65 sin verificar la prohibición normativa §1.7: el sistema no debe validar ni exigir correspondencia de detalle entre lo enviado a proceso y lo retornado.

### No se toca en esta implementación

Gates 0-3, `reception_parser.py`, lógica interna de `madenat_toll_processing` (solo verificación), esquema de `stock.lot` más allá de lo necesario para el modelo de línea nuevo. Ningún módulo nuevo.

---

## FASE 4 — REFACTOR MODULAR

- [ ] Separación final de `LumberReceptionLine` a archivo propio. `lumber_reception.py` mantiene 3,041 líneas y múltiples responsabilidades concentradas.

### Criterio de salida

Cerrar este punto solo si el refactor final no rompe instalación, pruebas ni continuidad.

---

## FASE 5 — CALIDAD Y ESTABILIDAD

- [ ] Formalizar tolerancias por tipo de madera.
- [ ] Limpiar warnings XML.
- [ ] Resolver constraint `stock_lot_check_cost_positive`.
- [ ] BT-05: Parseo disperso en `madenat_guia_processing.py` — 9 métodos sin dispatcher equivalente a `reception_parser.py`.
- [ ] Diagnóstico `reception_id` no poblado: reconfirmado abierto (`12_FLUJOS_INGESTA.md:165-169`, `:208-218`), sin re-diagnóstico de causa raíz. No aplicar scripts destructivos sin diagnóstico confirmado.
- [ ] `origin_scope` en `lumber.profile.subproduct.rule` (AD-56): pendiente en documentación, no re-verificado en código en la auditoría 2026-09-20.
- [ ] Gate de OC en Costeo: `action_apply_costs()` no valida OC resuelta. Refuerzo debe vivir en `madenat_lumber_costing`, nunca en `madenat_lumber_core`.
- [ ] Alinear test T13 con `deduction_factor = 0.0625` ya confirmado.
- [ ] Corregir `madenat_ingestion_engine/README.md:246-248` — dice "solo depende de base" pero `__manifest__.py:22` declara `depends: ['base', 'madenat_lumber_core']`.
- [ ] Actualizar `INDICE_DOCUMENTACION.md:26`: sigue registrando `05_BACKLOG.md` como v6.3.0/2026-06-16; debe reflejar v7.1.0/2026-09-20.
- [ ] Actualizar AD-63 en `04_DECISION_LOG.md`: la afirmación "nunca commiteado" quedó obsoleta desde `843ed0d` (2026-09-15). Registrar la corrección sin borrar el historial de la decisión original.

### Criterio de salida

No avanzar a consolidaciones mayores mientras la base técnica siga generando riesgos de instalación o validación.

---

## FASE 6 — VALIDACIÓN FUNCIONAL (UAT)

- [ ] UAT end-to-end de Producto y Procesados.
- [ ] Validación operacional con datos de prueba de la genealogía padre-hijo (`parent_lot_id`/`child_lot_ids`/`generation_level`).
- [ ] T29-T32 sin evidencia formal.
- [ ] Validación end-to-end en staging de `stock.landed.cost`.
- [ ] Ejecución formal en staging de las suites C2, C3, C4.
- [ ] Ejecutar la suite `madenat_lumber_core` con `--test-enable` para validar en runtime real los tests nuevos de consumo parcial (AD-64).

### Nota de estado

Las tareas de staging de la versión anterior (commit `3ba43575`, kanban/dashboards/landed_cost) requieren confirmación: no hay evidencia de cierre explícito.

---

## FASE 7 — INTEGRACIÓN CONTABLE (Visión a largo plazo)

- [ ] Diseño e implementación de integración contable hacia `account.move`. `stock.lot.cost.line` ya tiene `account_id`, falta el mapping contable completo.
- [ ] Migrar reportes financieros legacy a `Monetary` nativo.

### Nota de alcance

No confundir con `madenat_lumber_billing` ni `madenat_vendor_payment`, ambos ya implementados.

---

## DEUDA TÉCNICA CATALOGADA

| Ítem | Origen | Naturaleza | Estado de verificación |
|---|---|---|---|
| `madenat_ingestion_engine` sin trazabilidad canónica (git ya resuelto) | AD-63, corregido 2026-09-20 | Módulo trackeado en git desde `843ed0d`; falta entrada propia en CANON | Verificado |
| `ingestion_column_profile.py` esqueleto de 4 campos | AD-63 | Sin campos de layout/posiciones/regex/unidades | Verificado |
| Extracción PDF sin tablas configurables | AD-63 | `_extract_pdf()` retorna `lines=[]` siempre | Verificado |
| `core_utils.py` código muerto | Auditoría 2026-07-08 | 0 referencias, no archivado | No re-verificado |
| `product_template.py` huérfano | Auditoría 2026-07-08 | Extensión nunca desplegada | No re-verificado |
| `lumber_reception_id` campo legacy | `12_FLUJOS_INGESTA.md` | No usar en nuevos desarrollos | No re-verificado |
| `purchase_cost_usd` deprecado | `08_COSTEO.md` | Solo compatibilidad histórica | No re-verificado |
| Backups `backups_20260819_2013/` y `backups_20260819_2040/` | Confirmado 2026-09-20 | Copias completas de `madenat_guia_processing.py` (231KB c/u) siguen presentes | Confirmado presentes; falta verificar si tracked por git |
| README de `madenat_ingestion_engine` contradice su manifest | Confirmado 2026-09-20 | README dice "solo base"; manifest declara ambas dependencias | Verificado |
| `test_validate_blocked_creates_no_audit_event` no bloquea guía con espesor 0 | Sesión 2026-09-21, investigación de regresión post-AD-68/69 | `ValidationError` esperada no se dispara en `action_validate()`; confirmado anterior a AD-67 (reproducido en commit `a00596d`) | Verificado — causalidad descartada (no es AD-68/69/Frente 3) |
| 5 fallos en `test_supplier_resolution.py` y `test_reception_supplier_rut_extraction.py` | Sesión 2026-09-21, misma investigación de regresión | **Re-verificado 2026-09-26:** 3 fallos de `TestSupplierResolution` son contaminación de datos compartidos (pasan en base limpia); los 2 de `TestReceptionSupplierRutExtraction` son contradicción test/implementación (fallan también en base limpia) | Verificado — detalle en T1/T4 de la deuda de Gestión SV |

---

## DEUDA VERIFICADA — GESTIÓN OPERATIVA DE ETIQUETAS SV (2026-09-26, AD-79)

Línea base: base limpia auxiliar `madenat_sv_baseline` (sin datos de negocio) versus `madenat_test`.
**Ninguno de estos ítems fue introducido por Gestión Operativa de Etiquetas SV.**

> **T1–T6 CERRADOS (2026-09-26, sesión de cierre de deuda técnica).** Cada ítem se resolvió con su causa
> raíz verificada en runtime (fases `at_install` vs `post_install`, MRO real de `action_validate`, hook de
> auto-nominal de Intake), pruebas focalizadas 72/72 PASS en `madenat_test` y —para T6— instalación limpia
> verificada en base desechable `madenat_clean_install_test` (instalada y eliminada en la misma sesión).
> Evidencia en `03_TESTS.md` §9.7. T7 (documental) permanece cerrado.

| ID | Módulo | Riesgo | Línea base verificada | Introducido por SV | Siguiente acción recomendada |
|---|---|---|---:|---|---|
| T1 | `madenat_lumber_core` | **CERRADO (2026-09-26).** La captura documental es no bloqueante: sin RUT no se busca VAT vacío/Falsy, no se asocia ni crea proveedor, se conserva el proveedor elegido manualmente y queda registro explícito de proveedor pendiente. La exigencia de proveedor identificable se traslada al envío irreversible (`action_confirm_reception`), antes de lotes/picking/movimientos/quants, con evidencia `omission` en `madenat.audit.log` | Verificado en `madenat_test` (fase post-install): `TestReceptionSupplierRutExtraction` 11/11 PASS | **NO** | Cerrado. Ver `03_TESTS.md` §9.7 |
| T2 | `madenat_lumber_core` | **CERRADO (2026-09-26).** La causa era doble: (a) en runtime core la validación dimensional de espesor nominal se aplicaba al flujo Volumen (`granel`), y (b) en runtime con Intake la prueba omitía el volumen oficial documental y asertaba `lot_ids` (detalle de la ruta core). El gate dimensional queda acotado a flujos dimensionales (compra/service); Volumen no inventa espesor y declara `volume_pdf_m3` positivo | Verificado en `madenat_test` (fase post-install): `TestGranelRouteCore` 14/14 PASS | **NO** | Cerrado. Ver `12_FLUJOS_INGESTA.md` §11.5 |
| T3 | `madenat_lumber_core` | **CERRADO (2026-09-26).** Odoo 18 no expone `Float.digits`: la precisión se lee con `get_digits(env)` (interno `_digits`). Defecto exclusivamente de test; el código productivo no usaba `.digits` | Verificado en `madenat_test`: `TestVolumeGuideHeader` 5/5 PASS | **NO** | Cerrado |
| T4 | `madenat_lumber_core` | **CERRADO (2026-09-26).** (a) `TestSupplierResolution` usaba VAT/nombre fijos que colisionaban con datos reales (partner con VAT `77066489-6`); ahora se generan identificadores únicos por corrida. (b) `test_validate_blocked_creates_no_audit_event` no era contaminación de datos: el hook de autocompletado de Intake rellenaba el nominal al crear la línea; el escenario se fuerza tras el create | Verificado en `madenat_test`: `TestSupplierResolution` 8/8 y `TestGuiaProcessingValidationSignature` 6/6 PASS | **NO** | Cerrado |
| T5 | `madenat_lumber_core` / `madenat_lumber_intake` | **CERRADO (2026-09-26).** Causal verificada (no era «columna legada»): `TestLumberReception` no declaraba etiquetas de fase, por lo que Odoo la ejecutaba en `at_install` — durante la carga del grafo, antes de que Intake registrara `conciliation_status` — y el INSERT omitía la columna NOT NULL. Se declaró `@tagged('post_install', '-at_install', …)`. El campo mantiene `required=True` + `default='not_compared'` (sin SQL default, sin migración, sin cambio productivo) | Verificado en `madenat_test` (fase post-install): `TestLumberReception` 21/21 PASS, incluida la regresión de creación mínima | **NO** | Cerrado |
| T6 | `madenat_lumber_logistics` / `madenat_lumber_billing` | **CERRADO (2026-09-26).** Se eliminó de Logistics el botón que referenciaba el XML ID de Billing y se aportó desde una vista heredada propiedad de Billing. Logistics instala sin Billing; la funcionalidad de facturación se conserva al instalar Billing (botón presente, resuelve a la acción y conserva `invisible="state != 'delivered'"`) | Verificado en base desechable `madenat_clean_install_test`: instalación Logistics-only OK; instalación posterior de Billing OK; prueba funcional de la acción OK | **NO** | Cerrado. Ver `00_ARQUITECTURA.md` §3.4 |
| T7 | Documentación CANON | Contradicción documental: el backlog declaraba la rebaja por Volúmenes como no implementada mientras el ledger SV ya implementa rebaja, reversa y asignación logística SV | Media — corregido en esta sincronización (`05_BACKLOG.md`, `02_CONTINUIDAD.md` §14) | **Sí (documental, ya corregido)** | Mantener la verificación al cerrar cada hito: documentación y código no deben divergir |


---

## DEUDA NUEVA DETECTADA EN EL CIERRE T1–T6 (2026-09-26)

Hallazgos verificados durante la sesión de cierre. **No fueron introducidos por el cierre**: se detectaron al
ejecutar la instalación limpia y las suites amplias. Ninguno fue corregido en esta sesión (archivos fuera del
alcance autorizado).

| ID | Módulo | Hallazgo verificado | Evidencia | Siguiente acción recomendada |
|---|---|---|---|---|
| T8 | `madenat_lumber_core` | `views/madenat_views_extensions.xml:143` referencia `contacts.menu_contacts` sin que `madenat_lumber_core` dependa de `contacts`: la instalación limpia de Logistics (con `contacts` no instalado) aborta con `AssertionError: The ID "contacts.menu_contacts" refers to an uninstalled module` | Log de instalación limpia de la sesión (`/tmp/ci_logistics.log`, ParseError en `madenat_views_extensions.xml:143`) | Misma clase de defecto que T6: eliminar la referencia o declarar la dependencia/guarda de módulo instalado |
| T9 | `madenat_lumber_billing` | `tests/test_billing_consolidation.py` no declara etiquetas de fase (corre en `at_install`) y `test_02_no_duplicar_consolidacion` espera una excepción por duplicado que el modelo no implementa (sin `_sql_constraints` ni `@api.constrains` de `shipment_id`) | Falla reproducida en aislamiento: 1 failed de 3 tests (`--test-tags=/madenat_lumber_billing:TestBillingConsolidation`) | Declarar `@tagged('post_install', '-at_install', …)` y decidir con negocio si el guard anti-duplicado debe existir (constraint o validación) |
| T10 | `madenat_lumber_logistics` | `views/logistics_views.xml` declara un XML ID duplicado (`view_lumber_export_shipment_form`, ya definido en `views/lumber_export_shipment_views.xml`) y **no** está listado en el manifiesto (archivo muerto); si alguien lo agrega a `data`, la carga falla por duplicado | Lectura de manifiesto y de ambos XML | Retirar el archivo muerto o renombrar su XML ID antes de incorporarlo al manifiesto |
| T11 | `madenat_lumber_intake` | `tests/test_volume_extraction.py` usa VAT fijos `96.510.970-6` / `96.510.970-3`; el primero pertenece a un partner real de `madenat_test` (`id 2045`, Maderas Arauco S.A.) — misma clase de colisión que T4 | Consulta de solo lectura sobre `res_partner` (VAT `96.510.970-6` → id 2045) | Tokenizar los identificadores del fixture en una sesión que autorice ese archivo |

---

## RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
|---|---|---|---|
| Recepción a granel + Balance de Masa + Consolidación administrativa | Alta | Implementar AD-65 | DISEÑO APROBADO, IMPLEMENTACIÓN PENDIENTE |
| Costeo sin prorrateo por consumo parcial | Alta | Resolver gap AD-64 (diseño ya aprobado, código pendiente) | DISEÑO AUDITADO Y APROBADO CON AJUSTES |
| Constraint `stock_lot_check_cost_positive` | Alta | Revisar data/modelo | ABIERTO |
| `reception_id` no poblado | Alta | Diagnosticar causa raíz en Gate 3 | ABIERTO desde 2026-06-16 |
| Falta tercera derivación en wizard de intake para Balance de Masa | Alta | Diseñar ruta que no fije `intake_direct_stock=True` | NUEVO — 2026-09-20 |
| `madenat_ingestion_engine` sin trazabilidad canónica | Media | Formalizar entrada propia en CANON | ABIERTO — AD-63 (parcial) |
| BT-05 — Parseo disperso | Media | Refactor posterior a integridad | ABIERTO |
| Monolito parcial en `lumber_reception.py` | Media | Refactor futuro | ABIERTO |
| Tolerancias no formalizadas | Media | Parametrizar | ABIERTO |
| `origin_scope` no implementado | Media | Evaluar propagación por origen | ABIERTO — AD-56 |
| Gate de OC no implementado | Media | Evaluar gate y estado de cierre | ABIERTO |
| Backups post-AD-26 sin mover a LEGADO | Media | Verificar tracking git y mover | NUEVO — 2026-09-20 |
| T29-T32 sin evidencia formal | Media | Evidenciar en `03_TESTS.md` | PENDIENTE |
| Discrepancias documentales (índice, README, backlog) | Baja | Corregir en cada documento fuente | NUEVO — 2026-09-20 |

> **Nota AD-67 (2026-09-21):** para la fila "Costeo sin prorrateo por consumo parcial", la parte de **inventario/volumen** quedó resuelta por AD-67 (`stock.lot.volumen_restante_m3` + reporte de inventario corregido). El **costeo específico** (prorrateo de `wood_cost_usd`/`total_cost_usd`/`cost_per_m3_usd`) queda como **AD-70 pendiente** (renumerado desde AD-68 el 2026-09-21 por colisión: AD-68 fue asignado a la ruta granel de intake el mismo día), sujeto a revisión con Costeo/Auditoría (Felipe).

---

## REGLA DE PRIORIZACIÓN

No abrir un frente mayor nuevo mientras existan bloqueos de instalación o pruebas pendientes sin evidenciar en `03_TESTS.md`. AD-65 es la excepción vigente; su prerequisito AD-64 tiene diseño ya auditado y aprobado (2026-09-20) y debe implementarse con los 3 ajustes obligatorios antes de iniciar cualquier otra tarea de AD-65.

---

## PRÓXIMOS HITOS — INGRESO POR VOLÚMENES (2026-09-22)

- [ ] Validar **Excel sin PDF** como fuente única (escenario pendiente de prueba explícita; hoy el PDF/Guía es la fuente principal y el Excel es opcional).
- [x] **Rebaja/reversa de Etiquetas SV y asignación logística SV** — implementadas y validadas (AD-79, 2026-09-26; 56 pruebas 0 fallas/0 errores). Ver `02_CONTINUIDAD.md` §14 y `03_TESTS.md` §9.
- [ ] **Monto individual por etiqueta** en la asignación logística múltiple (hoy el asistente usa un monto escalar por operación).
- [ ] **Generalización de aprobaciones** a más de dos niveles, solo si negocio lo requiere (hoy admite dos aprobadores explícitos).
- [ ] Definir la **rebaja/registro físico de stock por Volúmenes fuera del flujo SV** (sigue NO implementada; no forma parte de AD-79).
- [ ] Reejecutar `madenat_lumber_core` por ruta/clase (la ejecución por tags devolvió 0 tests por descubrimiento del entorno).
- [ ] Validar en producción la resolución de partner por nombre sin RUT y las etiquetas "Transporte" en membrete.
- [ ] Resolver la deuda T1–T6 de la sección «Deuda verificada — Gestión Operativa de Etiquetas SV».

**Implementado (2026-09-26, AD-79):** rebaja SV · reversa SV · saldo disponible SV · seguridad
(guarda de escritura directa + escalamiento Auditoría/Contabilidad) · concurrencia fail-closed.

**Pendiente:** monto individual por etiqueta en asignación logística múltiple · generalización de
aprobaciones para más de dos aprobadores (si negocio lo requiere) · resolución de T1–T6.

---

## PRÓXIMOS HITOS — PROGRAMACIÓN 1: IDENTIFICACIÓN OPERATIVA EN R1 (2026-09-25)

> Estado: Programación 1 (AD-77) **implementada y desplegada** en `madenat_test` con validación
> técnica. Ninguno de los hitos siguientes está implementado. La rebaja/reversa de Etiquetas SV
> (AD-79) **sí** está implementada y validada; la rebaja/registro físico de stock por Volúmenes
> **fuera** del flujo SV sigue **no** implementada.

- [ ] Validar visualmente R1 y el filtro `Lotes Volumen` (`[('is_volume_lot', '=', True)]`) con un Lote Volumen real con saldo positivo en ubicación interna, sin crear stock artificial.
- [ ] Decidir e implementar, si se aprueba, la presentación `Lote Volumen` en las exportaciones XLSX R1/R2/R5/R7/R9 (hoy muestran el nombre técnico del lote).
- [ ] Agregar test automatizado en `madenat_lumber_reports/tests/` para el token técnico `GRANEL`, la etiqueta operativa y `is_volume_lot`.
- [ ] Revisión arquitectónica de las fuentes de fecha de ingreso en `stock.quant` (`lot_reception_date`, `lot_entry_datetime`, `reception_date` de Core y `lot_id.reception_id.reception_date`).
- [ ] Evaluar rendimiento de los campos compute almacenados y del índice `is_volume_lot` a escala de quants.

---

## INVESTIGACIÓN FUTURA (no aprobada)

- [ ] Evaluar unificación de Bruta y Procesado en un único flujo de ingesta con staging común. Fuera de alcance actual (AD-ING-001/AD-ING-002 no la habilitan).

---

## Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 6.3.0 | 2026-06-16 | Última versión previa a la reconstrucción. |
| 7.0.0 | 2026-09-15 | Reconstrucción completa contra los 5 documentos canónicos. Cierre de BT-01 a BT-04 y C1-C4 reflejado. |
| 7.1.0 | 2026-09-20 | Incorpora resultados de auditoría de código independiente: diseño AD-64 aprobado con 3 ajustes obligatorios, corrección de AD-63, corrección de mapeo de dependencias, nueva pieza detectada (tercera derivación de intake), deuda de higiene reconfirmada, discrepancias documentales registradas. |
| 7.2.0 | 2026-09-21 | Cierre de AD-68/AD-69 (ruta granel en intake, fix disparo BT-04) e higiene de reception_workflow.py. Catalogación de 2 hallazgos de deuda técnica (test BT-01 bloqueado no dispara, contaminación de datos en tests de proveedor). |
| 7.4.0 | 2026-09-25 | Programación 1 (AD-77) registrada como desplegada con validación técnica y pendientes explícitos: validación visual de R1/filtro `Lotes Volumen`, presentación `Lote Volumen` en exportaciones XLSX, test automatizado del token técnico, revisión de fuentes de fecha de ingreso y evaluación de rendimiento de campos almacenados. La rebaja por Volúmenes permanece no implementada. |
| 7.5.0 | 2026-09-26 | Gestión Operativa de Etiquetas SV (AD-79): se documenta la deuda verificada T1–T7 con línea base reproducible (base limpia `madenat_sv_baseline`), se cierra la contradicción documental de la rebaja por Volúmenes (implementada para Etiquetas SV con 56 pruebas 0/0; la rebaja física por Volúmenes fuera del flujo SV sigue no implementada), se registran los pendientes de monto por etiqueta y de aprobaciones de más de dos niveles, y se cierra la discrepancia de versión de este archivo frente a `INDICE_DOCUMENTACION.md`. |
| 7.6.0 | 2026-09-26 | Cierre de la deuda técnica T1–T6: T1 (captura no bloqueante de proveedor + bloqueo en el envío irreversible), T2 (gate dimensional acotado a compra/service; Volumen sin espesor inventado), T3 (`get_digits(env)` en lugar de `.digits`), T4 (identificadores únicos por corrida + escenario de nominal forzado tras el create), T5 (causa real: `TestLumberReception` sin etiquetas de fase → se declara `post_install`), T6 (botón de Billing aportado por vista heredada de Billing). Se añaden T8–T11 como deuda nueva detectada durante el cierre. |
| 7.8.0 | 2026-10-01 | Se incorpora la sección «Auditoría 2026-10-01 — pendientes por área» (hallazgos H-01..H-16 y N-01..N-10) clasificada en Operaciones / Contabilidad-Auditoría-Facturación / Logística / Fase 6, coherente con `16_AUDITORIA_20261001.md`. Se registran 4 hallazgos RESUELTOS (H-01, H-02, N-07, N-08/N-09) y se anotan los pendientes diferidos por el usuario. |
| 8.7.0 | 2026-10-07 | Se incorpora la sección «Búsqueda, filtros y agrupaciones de la Consola de Intake (2026-10-07, AD-101) — APLICADO (madenat_test)» con lo **cerrado** (OC documental/vinculada, origen de fecha, modalidades, producto real, procesador) y sus **pendientes** (V3 navegador, instalación en base limpia, volumen numérico, otros orígenes de procesador, Abiertos/Finalizados). Ver `00_ARQUITECTURA.md` §4.10 y `03_TESTS.md` §11. |
| 8.14.0 | 2026-10-08 | Sección «REVALIDACIÓN 2026-10-08 (2.ª pasada) — pruebas reconstruidas con la biblioteca de muestras»: antecedente incorporado (se probaron todos los ingresos; formatos en `muestras_documentos_ingreso`, fuera de `custom_addons`). Rectifica la 1.ª pasada: **cerrado con evidencia** R02/R03/R06/R09/R11; **parcial** R05/R07/R08 (el 48,009 es el volumen de embarque, no un error); **pendientes Q1–Q8**. Detalle en `02_CONTINUIDAD.md` §17.15 y `03_TESTS.md` §13.5–13.6. |
- [x] AD-68/AD-69: ruta granel en intake + fix disparo BT-04 (2026-09-21)
- [x] Higiene: migrar `palabras_proceso` duplicado en reception_workflow.py a madenat.ingestion.config (2026-09-21, post-AD-68)


---

## FASE 2 — UX DE VOLUMEN OFICIAL, BLOQUE SV Y CICLO DE VIDA (2026-09-28, AD-80)

### Cerrado

- [x] **Bloque SV visible en la Consola** (`ETIQUETA SV Y SALDO OPERATIVO`): etiqueta, volumen
      documental original, regularizado, rebajado, saldo, piezas (solo documentales) y
      advertencia documental, con placeholder `Se asignará al enviar a stock.` sin lote.
- [x] **Acciones SV autorizadas en Consola y Guía** (modificar etiqueta, regularizar volumen,
      rebajar, reversar rebaja y ver historial), por delegación a wizards y ledger. Deroga la
      regla anterior «sin acciones SV en la Consola» (aserciones positivas en
      `test_volume_official_volume.py`).
- [x] **Reversa SV visible**: botón solo para rebaja `applied` y reversible, en el ledger y en el
      bloque SV; la segunda reversa sigue bloqueada por el modelo.
- [x] **Jerarquía de volumen**: único volumen primario oficial, etiquetas exactas de los
      secundarios, detalle solo en control documental interno y sin agregado competidor
      `Volumen:` en el encabezado.
- [x] **Ciclo de vida controlado de guías (Modos A–D)** con diagnóstico de bloqueadores,
      auditoría firmada (`guia_delete_blocked`, `guia_delete_permanent`, `guia_purged`) y cero
      eliminación en el Modo D.

### Pendiente (nuevo)

- [ ] **Archivado de guías (`active`)**: campo, filtro y efecto en la vista SQL de la Consola.
      Diferido a una fase separada porque la Console SQL view no filtra `active` y agregarlo sin
      el diseño completo produciría inconsistencias.
- [ ] **Validación visual** del bloque SV y del asistente de ciclo de vida con una recepción por
      Volumen real (en `madenat_test` no hay lote SV con historia material).
- [ ] **Evaluar** exponer el diagnóstico de ciclo de vida para `lumber.reception` (Producto),
      hoy fuera de alcance.

---

## AUDITORÍA 2026-10-01 — PENDIENTES POR ÁREA

**Fuente:** `16_AUDITORIA_20261001.md` (hallazgos H-01..H-16 y N-01..N-10). **Estado:** ✅ 4 RESUELTOS; el resto **PENDIENTE** y clasificado por área.

**Orden de trabajo vigente del usuario (AD-81 PROPUESTA, no aprobada):** ingreso a stock → consolidación (por contenedor y rebaja por motonave) → módulo de mantenimiento → logística y exportación. **Lo contable, la auditoría y la facturación quedan diferidos.**

### Resuelto (2026-10-01)

- [x] **H-01** ACL de solo lectura de la Consola de Ingreso de Madera y del detalle declarado para Auditoría/Contabilidad — commit `7191c92` (+`36d7bf4`).
- [x] **H-02** `stock.lot.cost.line`: matriz por grupos funcionales (Operaciones solo `create`; Costos/Contabilidad/Gerencia/Admin full; `base.group_user` read) — commit `7191c92`.
- [x] **N-07** Índice único parcial de consolidación por embarque + guarda `UserError` — commit `9ea7abc`.
- [x] **N-08 / N-09** `partnerid` (campo real) en costeo y `type='consu'`+`is_storable` en tests de costing — commit `39fc77d`.

### Operaciones

- [ ] **N-01** Migración de grupos huérfanos (61-64) + 34 ACL: **en modo seco, sin ejecutar**. Bloqueada por decisión sobre usuarios (`leonardo`, `cristhian`). Script: `/home/viruco/dev-stack/odoo/scripts/migrate_orphan_groups.py`. Detalle en `16_AUDITORIA_20261001.md` §9.
- [ ] **N-06** Over-privilegio: los usuarios operativos son `Administrador` (`base.group_erp_manager`) + `Características técnicas` (`base.group_system`). Revisar antes de cualquier endurecimiento de ACL.
- [ ] **H-08** 3.844 warnings «Non-stored field … should be searchable» por `volume_detail_line_ids` en `intake_console.py:322,616-617`.
- [ ] **H-10** Deuda técnica: `_deprecated_action_distribute_costs` (`logistics/models/lumber_shipment_costing.py:88`) y `backups_*` embebidos en `madenat_lumber_core`.
- [ ] **H-13** `is_billed` con `@api.depends('name')` dummy (`stock_lot.py:789-819`).
- [ ] **H-14** `madenat.dev_cleanup_enabled = True` en `madenat_test` (documentado; **no modificado**). Ver `16_AUDITORIA_20261001.md` §8.
- [ ] **H-16** `madenat_lumber_docs` dentro de `custom_addons`.
- [ ] **N-09** `type='product'` restante en `madenat_lumber_core/tests/test_lot_costing.py:27`.

### Contabilidad / Auditoría / Facturación (**diferido por el usuario**)

- [ ] **H-03** Reglas de aprobación de facturas y pagos (no implementadas).
- [ ] **H-04** `vendor.payment.order` y `vendor.payment.wizard` son placeholders.
- [ ] **H-06** `group_madenat_auditoria` con 0 usuarios (la migración en seco asigna `fmunoz`, sin ejecutar).
- [ ] **H-07** Grupos decorativos en `madenat_vendor_payment`.
- [ ] **H-09 / N-05** Cero `ir.rule`; integridad y visibilidad de `madenat.audit.log`.
- [ ] **H-12** Versión `'1.0.0'` del manifiesto de billing.
- [ ] **N-02** Doble conteo de `total_cost_usd` (corrección mínima propuesta: retirar el override en `stock_lot_costing.py:127-139`).
- [ ] **N-03** `account_id` inexistente en `stock.lot.cost.line` / `lumber.cost.distribution.line`.
- [ ] **N-04** `landed_cost_ids` inexistente en `lumber.cost.distribution`.
- [ ] **N-10** `flush()` obsoleto en un test de costing (Odoo 18: `flush_recordset()`).

### Logística y exportación

- [ ] **H-07** Grupos decorativos en `madenat_lumber_shipping_core`.
- [ ] **H-15** Nomenclatura `cancel`/`cancelled` entre `shipping.voyage` y `lumber.export.shipment`.

### Fase 6 — Inteligencia de negocio

- [ ] **H-05** Implementar BI real: filtros por `voyage_id`, rentabilidad por trayecto/nave/línea naviera.
- [ ] **H-11** `madenat_lumber_reports` sin `category` y con `post_init_hook`.

---

## Rebaja de contenedor / nave (AD-82 · AD-84 · AD-83, 2026-10-01) — IMPLEMENTADO

> Rama `feat/rebaja-contenedor-20261001` (BD `madenat_test`). Ver `18_CONSOLIDACION_Y_REBAJA.md` §14.

- [x] Salida única de stock al **rebajar**; el **zarpe no descuenta** (AD-82): `lumber.container.action_rebajar`
      / `_rebajar_container`; `lumber.export.shipment.action_set_in_transit` sin `_action_reduce_stock` (eliminado).
- [x] **Idempotencia por (contenedor, lote)** y causa única de descuento (AD-84): restricción única en `lumber.shipment.line`.
- [x] **Reversa** (retorno nativo + contrapartida SV). **Actualizado 2026-10-01 (I0.7):** con embarque entregado o viaje
      cancelado ya **no** es bloqueo duro sin salida: exige **override de Gerencia con motivo** (auditado).
- [x] Asistente **«Rebajar por nave»** con savepoint por contenedor e informe de éxitos/fallos.
- [x] Wizard de asignación con **DISPONIBLE base nominal** (F-02 / A-3); etiquetas de volumen alineadas a CANON/17 §4 (A3);
      cabecera de tarja XLSX con nave/viaje + reserva (A4); dominio del wizard sin token `product` (A5).
- [ ] **Q-07** Rebaja por nave: **permiso/alcance** (implementado **provisional** en Jefatura de Operaciones / Gerencia).
- [ ] **H-N1** `_check_lot_duplication` impide el **mismo lote en dos contenedores activos**; evaluar si el negocio lo requiere
      (bloquea la prueba literal de «un lote SV en dos contenedores»).
- [ ] Extracción del **módulo propio de rebaja SV**: **⛔ REEMPLAZADA por AD-87** (no se extrae módulo; el descuento por procesados es la **imputación**). Ver `19_IMPUTACION_SV_Y_PROCESADORES.md`.
- [ ] Fuera de alcance en esta fase: facturación, +1/8" (170/180 mm), **P.O. del comprador**, consignatarios, `booking_id`,
      armador/naviera, rolleo como evento, tarja por paquete.

---

## Rebaja — Endurecimiento y principio AD-88 (I0) — IMPLEMENTADO (2026-10-01)

> Rama `feat/imputacion-sv-i1-20261001` (desde `docs/imputacion-sv-20261001`; BD `madenat_test`). AD-88 (`04_DECISION_LOG.md`).
> **Numeración (decisión del usuario, 2026-10-01):** manda la de `19_IMPUTACION_SV_Y_PROCESADORES.md` §16. **Todo** lo hecho
> en esta rama (endurecimiento + helper AD-88 + ablandamiento + SV oculto) se registra como **bloque I0**. El **I1 canónico**
> (ubicaciones de procesadores, saldo por procesador y marcado) queda **PENDIENTE** con **alcance ampliado** (envío a procesador,
> recepción directa, contenedores con lotes en procesador) — ver la sección «PLAN (fases I1..I6)». **I2** (modelo de imputación) **sin cambios**.

### I0 — Endurecimiento de la rama de rebaja
- [x] **I0.1 Rolleo:** el asistente no actúa sobre contenedores `rebajado`; mensaje que indica usar «Revertir rebaja».
- [x] **I0.2 Correo:** prueba RPC de «Rebajar contenedor» con el correo de confirmación **activo** → **pasa sin cambios de código**
      (no se requirió solución mínima; ver informe de sesión).
- [x] **I0.3 Auditoría:** snapshot + SHA-256 en los eventos `rebaja` y `rebaja_reverse` (`_rebaja_audit`, patrón `madenat.audit.log`).
- [x] **I0.4 Costing:** `skip` con razón en tests de funcionalidad no implementada (N-02/N-03/N-04) y `flush()` → `flush_recordset()`.
      Sin tocar la lógica de costeo. Suite `madenat_lumber_costing` en verde (8 skip documentados).

### I0 (continuación) — Helper AD-88 y ablandamiento
- [x] **I0.5 Helper:** `madenat.deviation.mixin._guard_deviation(code, message, reason, hard)` con snapshot + SHA-256 y `deviation`
      en `madenat.audit.log`. Hard = bloquea; blando = exige motivo + audita + avisa (no bloquea).
- [x] **I0.6 B-01 Zarpe:** pasa a **advertencia con motivo**; asistente `lumber.shipment.zarpe.wizard` ofrece «Rebajar y zarpar»
      y «Zarpar con excepción» (motivo obligatorio + auditoría).
- [x] **I0.7 B-03/B-06 Reversa:** con embarque entregado o viaje cancelado exige **override de Gerencia con motivo**
      (`lumber.container.rebaja.reverse.wizard`; auditoría `deviation`).
- [x] **I0.8 SV oculto por defecto** en el asistente de contenedores (D9), con filtro «Mostrar etiquetas SV»; sin impedir nada.
- [ ] **I0.9 Fuera de alcance:** **NO** se implementa **B-04 (saldo SV)** ni la **imputación** (van en las fases I2/I3 del plan de `19`).
- [ ] **Q-19-3, Q-19-4, Q-19-6, Q-19-7** siguen **abiertas** (ver `19` §17).

---

## Imputación SV y Procesadores (AD-87 · AD-88 · AD-89 · AD-90 · AD-91) — PLAN (fases I1..I6)

> Especificación y detalle por fase (dependencias, riesgos, criterios de aceptación): `19_IMPUTACION_SV_Y_PROCESADORES.md` §16.
> Decisiones D1–D10. El **bloque I0** (endurecimiento + AD-88) ya está **implementado**; esta tabla lista **I1..I6** pendientes.
> **AD-91 (2026-10-02):** **I2 queda acotado a documental sin efecto en stock** (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`); la **salida nativa + ledger** se materializan en **I3**, el **costo** en **I5** y la **merma/cierre** en fases posteriores.
> **Sin código en esta fase** (documental).

### I1 — Cimientos: ubicaciones y saldo por procesador — ✅ IMPLEMENTADO (2026-10-02)
- [x] `stock.location` **`Procesadores`** (interna) + hijas `Procesadores/<X>` bajo demanda e **idempotentes**
      (`usage='internal'`; inventario MADENAT); referencia `processor_location_id` y marcado según §16.
- [x] **Saldo por procesador:** vista de solo lectura (**lista y pivot** sobre `stock.quant`), por procesador y producto,
      con volumen por tipo de lote (`madenat_processor_id`, `madenat_lot_flow_type`). Menú en Logística.
- [x] Marcar procesadores (`res.partner.is_processor`).
- [x] **Evento «Envío a procesador»:** asistente desde lotes → **transferencia interna nativa** con `lot_id` por línea;
      cantidad editable hacia abajo con techo en el **libre real** (físico − reservado ajeno; rechazo si excede);
      **motivo** solo ante desviación real respecto de una **referencia previa persistida** (I1 no la persiste)
      + evento en `madenat.audit.log` (tipo aditivo `processor_shipment`, idempotente).
- [x] **Recepción directa en la ubicación del procesador:** verificada (SV/volumen vía albarán `incoming`); sin cambios de código.
- [x] **Contenedores con lotes en ubicaciones de procesador:** verificado que el asistente los toma.
- **Depende de:** AD-65 §1.5; helper AD-88 (bloque I0).
- **Aceptación:** T-09 + idempotencia de ubicaciones, envío parcial/exceso, recepción directa, saldo vs Σ quants, contenedor y ACL (Operaciones/Jefatura/Gerencia, sin grupos nuevos). **Suite Logistics: 51 (40 baseline + 11 nuevos), 0 fallas.**
- **Decisiones post-I1 (D-I1-01..D-I1-04, 2026-10-02; AD-89):**
  - **D-I1-01:** **sin** modelo persistente `madenat.processor.balance`; `stock.quant` + ubicaciones internas son la **fuente física de verdad** (modelo persistente **diferido a BI/cierre**).
  - **D-I1-02:** saldo en **dos niveles** — (a) resumen agregado *implementado*; (b) **detalle por lote** (nominal, disponible, ubicación/procesador, tipo de lote, fecha de ingreso, antigüedad en procesador, guía, proveedor, OC) **planificado para la fase posterior a la imputación SV→etiqueta**.
  - **D-I1-03:** **envío parcial ≠ desviación**; el motivo obligatorio aplica **solo** si la cantidad difiere de una **propuesta/planificación/reserva/cantidad previa**. ✅ **Corregido (2026-10-02, `feat/procesadores-guardas-20261002`):** sin referencia previa persistida ⇒ sin motivo ni `deviation`.
  - **D-I1-04:** **riesgo pre-producción** — validar disponibilidad frente a **reservas de otros pickings/backorders**. ✅ **Resuelto (2026-10-02):** físico/reservado/libre nativo; rechazo si solicitado > libre; reserva ajena intacta; backorder nativo documentado (T7).
  - **D-I1-05 (AD-90):** **semántica de inventario en procesador** — `Procesadores/<X>` es **custodia operativa** (inventario MADENAT, no consignación); un **SV** allí está **pendiente de consolidación documental**; la **recepción directa** y la **transferencia interna** son **rutas físicas equivalentes**; el envío **no** es venta/exportación/rebaja/consumo/merma/genealogía; se distinguen **cuatro categorías de saldo** y **dos órdenes temporales**; **I1 sin cambio de alcance**; **I2 sigue pendiente**. Solo documentación.
- **Desviaciones/dudas previas:** resueltas/reencuadradas por D-I1-01..03 (ver `19_IMPUTACION_SV_Y_PROCESADORES.md` §16).

### I2 — Consolidación / imputación documental (etiquetas procesadas → SV) — ⏳ PENDIENTE
- [ ] **`madenat.sv.imputation`** (+`.line`, +`.sv.line`) en **`madenat_lumber_logistics`** (modelo **documental aditivo**; AD-91, D-I2-11): **cabecera por guía** (`guia_processing_id`, **una** de trabajo `draft`/`pending` por guía); reparto **N:M** etiqueta↔SV con **volumen nominal editable**; estados `draft/pending/applied/reversed/cancelled`; motivo + `deviation_flags`; **idempotencia por clave documental propia** (no `picking_id`); **inmutabilidad** de `applied` (reversa + nueva imputación). **NO** es producción, retorno físico ni genealogía lote-a-lote.
- [ ] **Sin efecto en stock (D-I2-12):** no toca `stock.quant`/`stock.picking`/`stock.move`, **no** genera salida nativa, **no** añade `action_type='imputacion'` ni altera `sv_available_m3`/`_sv_balance_values`. La **salida nativa + ledger** van a **I3**; el **costo**, a **I5**; la **merma/cierre**, a fases posteriores.
- [ ] **Integridad (D-I2-16):** **duro** etiqueta-side (Σ imputaciones activas/aplicadas no revertidas ≤ volumen nominal editable; rechazo); **blando** SV-side (saldo documental superado ⇒ advertencia + motivo + `deviation`, permite aplicar). Sin tolerancias ni `AL-01..AL-07` en I2.
- [ ] **Saldo documental (D-I2-13):** computado **solo** desde imputaciones activas/aplicadas no revertidas del modelo nuevo; **distinto** de `stock.quant` (físico) y de `sv_available_m3` (ledger).
- **Depende de:** I1 (procesador, `processor_location_id`, ubicación interna, saldo físico); `madenat.guia.processing` y `stock.lot` (**sin moverlos de core**); semántica **AD-90 / D-I1-05**. **No** depende del ledger.
- **Aceptación:** T-01..T-03, T-06; CRUD con seguridad por rol; **sin efectos en stock**; **cuatro categorías de saldo** distinguibles (físico / documental pendiente / procesados pendientes de imputar / procesados ya imputados) **más** el **saldo documental** computado; válidos los **dos órdenes temporales** (etiquetas→consolidación y consolidación→etiquetas) sin bloqueo; **dura** etiqueta-side verificada; **blanda** SV-side con motivo + `deviation`; **idempotencia** documental propia; **inmutabilidad/reversa** de `applied`. **Precisión (AD-91):** se distinguen la **reserva documental temporal de capacidad nominal de etiqueta** (`I2_ACTIVE_STATES`: `draft`/`pending`/`applied`; techo duro) y el **saldo documental aplicado de SV** (solo `applied`); `pending` mantiene la reserva temporal hasta aplicar/cancelar/reversar; `draft`/`pending` no mueven stock ni alteran `sv_available_m3`/ledger. **Estado: PENDIENTE** (AD-90/AD-91 no lo declaran implementado).

### I3 — Salida nativa del SV + ledger `imputacion` + invariantes
> **Único punto de salida nativa del SV (AD-91):** el efecto físico (quant + ledger) se materializa aquí, **no** en I2.
- [ ] `action_type='imputacion'`; vínculo `imputation_id`; `stock.move` a `Virtual Locations/Production`; idempotencia `picking_id`.
- [ ] Invariantes AD-84 ampliados (`19` §7.3).
- **Depende de:** I2; AD-82/AD-84. **Aceptación:** T-01..T-05, T-07, T-11; sin regresiones.

### I4 — UX: asistente de imputación + propuesta automática
- [ ] Asistente al recibir la **guía de procesados**; propuesta por **proveedor / producto / antigüedad**.
- [ ] Ocultar lotes **SV** por defecto en el asistente de contenedores (D9); **motivo** obligatorio ante desviación.
- **Depende de:** I2/I3. **Aceptación:** T-06; SV seleccionables.

### I5 — Costo
- [ ] Costo por m3 editable; **promedio ponderado** de SV; `stock.lot.cost.line` (`wood`); **fuente del costo del SV** (brecha `19` §5.5).
- **Depende de:** I3. **Aceptación:** T-08.

### I6 — `parent_lot_id` opcional + auditoría/alertas + cierre de bloqueos
- [ ] `parent_lot_id` **opcional** (paso controlado, D10); alertas §8; clasificación de bloqueos §14 (zarpe / saldo SV → advertencia con motivo).
- **Depende de:** I1..I5. **Aceptación:** T-10, T-12.

**Preguntas abiertas (sin decidir por el usuario):** Q-19-1..Q-19-8 (`19` §17).

---

## Búsqueda, filtros y agrupaciones de la Consola de Intake (2026-10-07, AD-101) — APLICADO (madenat_test)

Aplicado en `madenat_test` (módulo `madenat_lumber_intake` 18.0.0.11.0); **no** desplegado a
producción. Comportamiento en `00_ARQUITECTURA.md` §4.10; decisión AD-101; pruebas en `03_TESTS.md` §11.

### Cerrado

- [x] **OC documental vs OC vinculada:** columna/búsqueda/agrupación; filtros OC vinculada,
      pendiente y no indicada; `purchase_reference` conservado por compatibilidad.
- [x] **Origen de fecha:** `guide_date_kind` (`emission`/`reception`) + columna «Origen fecha».
- [x] **Modalidades** Producto/Procesado/Volúmenes; filtros de estado «Procesada (legacy)» y «Error».
- [x] **Producto real** (`product_filter_id`, por líneas de ambos orígenes, sin duplicar) y
      **Procesador** (`processor_id`, por Orden de Procesamiento).

### Pendiente (nuevo)

- [ ] **V3 (navegador):** comprobar en UI OC documental/vinculada, fechas, producto real, procesador y
      combinaciones de filtros. Permanecerá pendiente hasta evidencia real.
- [ ] **Instalación en base limpia:** la vista de lista referencia `action_madenat_lumber_intake_new`
      definida más abajo en el mismo archivo (referencia hacia adelante preexistente); resolver
      reordenando sin semántica. Trabajo **separado**.
- [ ] **Volumen numérico:** exponer el campo oficial `official_volume_m3` (`official_volume_effective_m3`),
      **unidad m³**, con semántica «0 vs desconocido». **Decisión pendiente** (no implementar antes).
- [ ] **Otros orígenes de procesador:** hoy solo `toll.processing.order.processor_id`. **Decisión de
      negocio pendiente.**
- [ ] **Abiertos/Finalizados:** evaluar si se amplían a `processed`/`error` (hoy se añadieron filtros
      dedicados). **Decisión de doctrina pendiente.**

---

## Retorno de servicio — identificación no bloqueante + imputación posterior (AD-102) — APLICADO EN EL DESARROLLO EXISTENTE (`madenat_test`) + UI de Ingreso de Madera reorganizada (2026-10-08)

**Antecedente.** La confirmación **bloqueante** quedó como precedente técnico en
`IMPL_SERVICE_RETURN_20261006/` (copia aislada; `diff`, tests, logs `iso_run*.log`). **No aplicada.**

**Intervención aprobada y probada en aislamiento (2026-10-07, AD-102).** Identificación **no
bloqueante** (`service_return_confirmation`) + imputación posterior reutilizando el mecanismo **SV
(I2)**. Copia de trabajo `IMPL_SERVICE_RETURN_AB_20261007/`; base dedicada `srvretab_test_20261007`.
**85/85 pruebas dirigidas OK** (nuevas A/B + regresiones I2 y core/intake) y **0 regresiones** en la
corrida completa de las 3 suites (las 9 fallas observadas son **preexistentes**). **No aplicado** al
entorno activo. Reglas en `04_DECISION_LOG.md` **AD-102**; detalle y retoma en
`02_CONTINUIDAD.md` **§17.10**.

**PAUSA (2026-10-07) — reanuda 2026-10-08.** Checkpoint en `02_CONTINUIDAD.md` **§17.11**. Gate
sobre **copia del árbol activo con cambios locales**: artefacto reconstruido **45/45**; pruebas
dirigidas **88/88** (incl. **Cristhian uid 8**, `su=False`, grupos intactos). **V3 pendiente.**
**A/B no aplicados** (código activo, `madenat_test` y producción). Entorno aislado conservado
(`http://127.0.0.1:8070`, base `srvretab_gate_20261007`).

**APLICACIÓN EN EL DESARROLLO EXISTENTE (2026-10-08) — AD-102 + UI de Ingreso de Madera.**
`AB_completo.diff` aplicado **una sola vez** sobre `custom_addons` (15 archivos byte a byte = workcopy
validado) y actualizado de forma controlada **solo** en `madenat_test` (`-u
madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics`; **0 ERROR / 0 CRITICAL**; columna
`service_return_confirmation` presente). Se **reorganizó la UI de Ingreso de Madera**: resumen en **2
columnas**, «Aplicar cambios» debajo de los campos, línea de identificación de retorno a todo el
ancho, Evidencia documental en **3 columnas** con encabezado **único** y detalle del packing list a
todo el ancho. Pruebas dirigidas **88/88** en verde **sobre `madenat_test`** (misma nómina del gate;
incl. Cristhian uid 8, `su=False`). El **aislamiento temporal se retiró** (`srvretab_web`/8070,
volumen `srvretab_web_data`, bases `srvretab_*_20261007`, `/tmp/{gate,ab_dryrun,iso_*}`). Respaldos,
retiro y detalle: `02_CONTINUIDAD.md` §17.13 y `03_TESTS.md` §12.6.

### Pendiente

- [x] **Aprobar la aplicación** al entorno activo de desarrollo: **APROBADA Y EJECUTADA** (2026-10-08)
      sobre `madenat_test`; AD asignado = **AD-102**.
- [x] **Actualizar módulos** en base **no productiva**: **HECHO** en `madenat_test`
      (`madenat_lumber_core`, `madenat_lumber_intake`, `madenat_lumber_logistics`).
- [x] **Usuario real Cristhian** (`cristhian.elguetag@gmail.com`): **ACREDITADO** (`su=False`, grupos
      intactos, uid 8) en el gate histórico y en la corrida sobre `madenat_test`. Ver `03_TESTS.md`
      §12.4 / §12.6.
- [ ] **Verificación en navegador** (V3): guion actualizado en
      `IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md` → `http://localhost:8069`
      (base `madenat_test`, guía **19827**). **NO ejecutada** (sin navegador); incluye la comprobación
      **visual** del nuevo layout de Ingreso de Madera.
- [ ] **Decisión funcional pendiente:** el filtro «Retornos sin imputación aplicada» **no** evalúa
      cobertura parcial (identificación INCOMPLETA) — definir si se completa (no en esta intervención).
- [ ] **Concurrencia** no acreditada; **I3/I5** fuera de alcance; **9 fallas preexistentes**
      conservadas (ver `03_TESTS.md` §12.2 y §12.6.4).
- [ ] **Instalación en base limpia** de la funcionalidad (la corrida de esta intervención fue sobre
      `madenat_test`, que ya tenía el esquema previo).

---

## Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — AUDITORÍA 2026-10-08

**Origen.** Conversación del 2026-09-02 y hilo «PRUEBA DE SISTEMA» con los reportes del 2026-09-07
(cinco proveedores: **Fátima, Ferramenta, Byc, JCE y Arauco**). **Auditoría de solo lectura**: sin
cambios de código, datos ni servicios; **sin pruebas nuevas**; sin commit ni push. Matriz consolidada:
`02_CONTINUIDAD.md` **§17.14.2**; relación requisito→evidencia→resultado: `03_TESTS.md` **§13**.

### Acreditado

- [x] **R02 — Retiro de la selección inicial procesados/compra (en código).** `tipo_ingreso` oculto en
      el wizard (`intake_wizard_views.xml:48`) y clasificación **por contenido** (AD-61, 2026-09-08),
      cubierta por `test_intake_tipo_ingreso_content.py`. **V3 (navegador) pendiente.**
- [x] **R12 — Retorno de servicio Sí/No/vacío (V2).** `test_service_return_confirmation.py` (**13**);
      **88/88** sobre `madenat_test` (2026-10-08); guard bloqueante eliminado. **V3 pendiente.**
- [x] **R13 — Controles de aplicación y reversa de la imputación SV (V2).**
      `test_service_return_imputation_guard.py` (**8**) + `test_service_return_pending_filter.py` (**9**)
      + regresiones I2. **V3 pendiente; concurrencia y cobertura parcial siguen abiertas.**

### Acreditado parcialmente

- [x] **R14 — Reorganización de la UI (estructura).** Verificada de forma **estructural** y en la vista
      **cargada** del TEST remoto (id 1660). **Observación visual pendiente (`UI-1..UI-6`).**
- [x] **R16 — Correspondencia de código y esquema con el TEST remoto.** **314** archivos con **0
      discrepancias** de hash; módulos, columna `service_return_confirmation` y vistas nuevas presentes.
      **No** acredita que el remoto pase pruebas (la corrida 88/88 fue local) ni que el remoto tenga
      trazabilidad de versión (`custom_addons` sin repositorio git allí).

### Pendiente (no acreditado)

- [ ] **R01 — Simplificación del ingreso y retiro de mensajes de prueba.** Persiste el aviso «Verifique
      el perfil de lectura antes de continuar» (`intake_wizard.py:251-262`), que en Odoo **interrumpe**
      la acción hasta pulsar «OK». **Acción P0.1**: obtener el texto literal del mensaje que ve el usuario.
- [ ] **R03 — Corrección del subproducto.** La resolución/autocreación es de 2026-08-31
      (AD-ING-001/002); **no** acreditado que fuese el defecto reportado. Revisar además el rechazo por
      líneas sin subproducto al enviar a stock (`madenat_guia_processing.py:2194-2203`).
- [ ] **R04 — Packing en fracciones.** Conversión y wrapper (`_get_fraction_text`) existen; **no**
      acreditada la presentación en la Consola; `_check_imperial_fractions` solo escribe en log. **V3.**
- [ ] **R05 — Fátima (guía 41994 + `41994.xls`).** Sin fixture del par ni ingesta real.
- [ ] **R06 — Ferramenta (guía 26270).** Sin evidencia de un ingreso nuevo completo; el registro real
      existente está `validated` desde el 2026-10-06.
- [ ] **R07 — Ferramenta, ambos volúmenes.** Mecanismo y pruebas unitarias existen; el registro real
      tiene `packing_volume_declared_m3` **vacío** y `sum_vol_documental_m3=0`; el «Vol. Embarque»
      almacenado (**48,009**) no coincide con la guía (**57,8400**) ni con el packing (**57,839556**).
      **Causa del desvío NO determinada.**
- [ ] **R08 — Byc / Blocks & Cutstock S.A. (guía 95083).** Cubierto con fixture **sintético** y con los
      totales reales (42,132 m³ / 2244 pzs / 8 paq.), **no** con el archivo del proveedor.
- [ ] **R09 / R10 — JCE (guía 95806 + Nota de Venta 881333).** El formato de **dimensiones combinadas**
      se **rechaza por diseño** (`REQUIERE_DIMENSIONES_SEPARADAS`; «No se creó ninguna línea»).
      **Decisión funcional pendiente (P1.3).**
- [ ] **R11 — Arauco (guía 4495589 + packing PDF).** Ambigüedad de modalidad: el flujo Normal exige
      packing **Excel** y el del proveedor es **PDF**. **Decisión funcional pendiente (P1.4).**
- [ ] **R15 — OwlError / `Many2OneField.urlRelation`.** **NO REPRODUCIDO**; causa **NO confirmada**. La
      expresión «operación no válida» **no** existe literalmente en el código ni en las traducciones
      desplegadas (H-1) y la comprobación estática **no** halló campo huérfano en las vistas de la
      Consola. **Bloquea** invitar a probar el flujo afectado.

### Límites conservados

- **9 fallas preexistentes**, **concurrencia no acreditada**, **filtro sin cobertura parcial**,
  **I3/I5 fuera de alcance**, **V3 pendiente** e **instalación en base limpia pendiente**: sin cambios.
  Ver `03_TESTS.md` §12.2, §12.6.4 y §13.3.
- **No** se cierra ningún requisito de proveedor (R05–R11): **ninguno** tiene ingesta real acreditada.

---

## REVALIDACIÓN 2026-10-08 (2.ª pasada) — pruebas reconstruidas con la biblioteca de muestras

**Antecedente incorporado.** Mauricio confirma que **se probaron todos los ingresos** y que los formatos
probados están en la **biblioteca externa** `muestras_documentos_ingreso` (fuera de `custom_addons`).
La 1.ª pasada (sección anterior) concluyó «NO ACREDITADO» para los cinco proveedores **a partir de una
búsqueda incompleta**; esa conclusión **se rectifica** con la evidencia reconstruida. Detalle y matriz
revalidada: `02_CONTINUIDAD.md` **§17.15**; relación prueba↔etapa↔resultado: `03_TESTS.md` **§13.5–13.6**.

### Cerrado (con evidencia reconstruida)

- [x] **R02 — Clasificación por contenido**, verificada en **11 ingresos reales**
      (`service`: 19846/19827/19826/26270/900002 · `granel`: 4495589/95806/UAT-SV · `compra`:
      UAT-INT-20261004) **sin selección manual**. → **VERIFICADO CON MUESTRA REAL**.
- [x] **R03 — Subproducto**, con **subproducto asignado en el 100 % de las líneas** de los ingresos
      reales (17/17, 19/19, 17/17, 1/1, 1/1) y **un solo producto maestro por guía**.
      → **VERIFICADO CON MUESTRA REAL**.
- [x] **R06 — Ferramenta 26270**: adjuntos `26270.pdf` + `26270.xlsx` en `guia.processing` 1728,
      **17 lotes** con el N° de LOTE y los M3 del packing, 1 picking, `validated` (2026-09-08),
      **replicado en el TEST remoto**. → **VERIFICADO CON MUESTRA REAL** (A–E).
- [x] **R09 — JCE 95806 (guía)**: registro 33151 `granel`/`verified`, 59,964 m³ (2026-10-06) por la ruta
      de **Volúmenes**; fixtures derivados con los datos reales del documento. → **VERIFICADO CON MUESTRA REAL**.
- [x] **R11 — Arauco 4495589 (guía)**: **fixture byte-idéntico** + pruebas con el **motor real**,
      registro 15326 `granel`/`validated` 40,315 m³, lote `GRANEL 4495589`, pickings con purga y reversa.
      → **VERIFICADO CON MUESTRA REAL** (A–D).

### Acreditado parcialmente

- [x] **R05 — Fátima 41994**: fixture **derivado** (misma cabecera de 2 filas y 1.ª línea
      `0000000134008`) y **formato idéntico** a `39519 (1).xls`, que **sí se ingresó** (1161, `verified`).
      → **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** (falta el ingreso propio de 41994 o la aceptación
      formal de la equivalencia).
- [x] **R08 — Byc 95083**: el detector `excel_table_detection.py` se documenta como **«investigación
      95083»** y sus fixtures reproducen la cabecera y los valores de la 1.ª fila real; los totales
      42,132 / 2244 / 8 provienen de ese packing. → **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL**.
- [x] **R07 — Volúmenes de Ferramenta**: Σ líneas ⇒ `vol_purchase` **57,840** = guía **57,8400** =
      packing **57,839556**; `vol_shipment` **48,009** = fórmula de embarque (espesor nominal 5/4" y
      ancho +1/8"). **No es un error**: es otro volumen. → **VERIFICADO (cálculo) + PENDIENTE FUNCIONAL
      (presentación/semántica)**.

### Pendiente (funcional o de incidencia)

- [ ] **R07** — mostrar/rotular en la Consola el volumen de guía/packing **junto** al de embarque
      (**Q1**). `packing_volume_declared_m3` está vacío en el registro por ser campo **posterior**.
- [ ] **R10** — Nota de Venta (JCE): decidir normalización de `Esc. Fact` o mensaje explícito
      «packing no ingerible» (**Q2**).
- [ ] **R11** — packing **PDF** de Arauco en el flujo **Normal** (**Q3**).
- [ ] **R05/R08** — ingreso real de `41994` y `95083` en base de pruebas (**Q4**; requiere autorización).
- [ ] **V3 (navegador)** — R01, R12, R13, R14 (**Q5**); sigue sin acreditarse.
- [ ] **R15** — `OwlError` **abierto y no reproducido**; **reportado por Mauricio** (corrección de
      atribución) (**Q6**).
- [ ] **R16** — replicar en el TEST remoto los casos hoy sólo locales y **dar control de versión** a su
      `custom_addons` (**Q7**).
- [ ] **R02-bis / regresión** — promover a fixtures las muestras ya probadas (**Q8**).

### Límites conservados (sin cambios)

**9 fallas preexistentes**, **concurrencia no acreditada**, **filtro sin cobertura parcial**, **I3/I5
fuera de alcance**, **V3 pendiente** e **instalación en base limpia pendiente**. No se actualizan sin
evidencia nueva. Ver `03_TESTS.md` §12.2, §12.6.4 y §13.6.



### Cierre funcional 2026-10-10 (P0–P4)

Detalle y evidencia: `02_CONTINUIDAD.md` **§17.16**; corridas: `03_TESTS.md` **§14**.

- **Q1 (R07) — presentación de volúmenes: IMPLEMENTADO EN DESARROLLO.** La
  Consola muestra «Vol. PDF/Guía (m³)», «Vol. Packing (m³)», «Vol. compra (m³)»
  y «Vol. embarque (m³)» (Ferramenta 26270: 57,840 / 48,009). Observación en
  navegador pendiente (V3).
- **Q2 (R10) — Nota de Venta JCE: IMPLEMENTADO EN DESARROLLO.** Notación
  `5/4x5.3/8x16` normalizada (evidencia: `VOL.` del documento = 4,997); los
  patrones ambiguos siguen rechazados con diagnóstico.
- **Q3 (R11) — packing PDF Arauco: DECISIÓN FUNCIONAL PROPUESTA.** Ruta de
  **Volúmenes** (el flujo Normal exige Excel; el PDF aporta sólo volumen total).
- **Q4 (R05/R08) — ingresos reales `41994`/`95083`: EJECUTADO EN DESARROLLO
  sin stock** (`lumber.reception` 7950 `verified`; `madenat.guia.processing`
  33250 `verified`).
- **Q5 (V3):** pendiente (sin navegador). **Q6 (OwlError):** no reproducido;
  paso manual de captura. **Q7 (R16):** pendiente (requiere autorización).
  **Q8 (fixtures):** parcial.
- **Límites conservados:** concurrencia no acreditada, filtro sin cobertura
  parcial, I3/I5 fuera de alcance, instalación en base limpia pendiente.

### Aceptación visual 2026-10-10 (guía 19827) y flujo SV confirmado

- **Q1 (R07) — ACEPTACIÓN VISUAL DEL CASO OBSERVADO.** La presentación de la **guía 19827** (resumen en
  2 columnas, evidencia en 3 columnas, identificación de retorno visible, packing a todo el ancho) fue
  **confirmada por Mauricio** el **2026-10-10**. La aceptación cubre **solo** el caso observado; **no** se
  extiende a la persistencia Sí/No/vacío en pantalla ni a la aplicación/reversa de imputaciones. Ver
  `02_CONTINUIDAD.md` §17.16.8 y `03_TESTS.md` §14.4.
- **Q5 (V3) — PARCIAL.** Cubierto el caso **19827**; el resto de flujos de la Consola (Volúmenes,
  persistencia del radio en pantalla) sigue **sin** observación en navegador.
- **Flujo SV — CONFIRMADO EN CÓDIGO (2026-10-10).** Secuencia operativa y controles (origen · destino ·
  volumen · saldo · aplicación · reversa · permisos): `19_IMPUTACION_SV_Y_PROCESADORES.md` §19.10.
  **Brechas declaradas:** sin vínculo automático envío↔imputación, sin rendimiento/merma, filtro sin
  cobertura parcial, I3/I5 fuera de alcance, concurrencia pendiente.

### Conciliación envío–retorno (Bloque A/B/C) — IMPLEMENTADO (2026-10-10)

- **Brecha (a) de `CANON/19` §19.10 (vínculo envío↔imputación) — CERRADA en A/B/C.** Modelo persistente
  `madenat.processor.return.link`; enlaza **picking** (envío, **no** el wizard transitorio) ↔ **guía**
  (retorno) ↔ **imputación** SV. Estados `draft`/`linked`/`reversed`; N:M; unicidad por par activo;
  append-only; permisos por ORM/RPC; auditoría aditiva `processor_return_link`/`..._reverse`; pestañas en
  guía/picking/imputación; menú Logística; asistente de imputación **reutilizado**.
- **Bloque D (conciliación CUANTITATIVA) — PENDIENTE.** Requiere magnitudes y reglas no aprobadas
  (Q-19-3/Q-19-4). **No** se implementa saldo de proceso, rendimiento ni merma. Las magnitudes
  (enviado / retornado) se muestran **separadas**, sin resta.
- **Históricos:** sin asociación automática; estado `no_return` hasta declaración explícita.
- **Aplicación en `madenat_test`:** módulos `madenat_lumber_core` + `madenat_lumber_logistics`
  actualizados; respaldo previo verificado (`CONCILIACION_ENVIO_RETORNO_20261010/`). **Sin** commit/push.
- **Pruebas:** T1–T12 = **12/12**; regresión `madenat_lumber_logistics` = 3 failed, 0 error of 265
  (3 fallas **pre-existentes** por aserción global de `deviation`; **0 nuevas**). Ver `03_TESTS.md` §15.
- **Evidencia web (2026-10-10):** (a) integración web/RPC con sesión autenticada — **EJECUTADA**;
  (b) lectura de arquitecturas de vistas y metadatos — **VERIFICADA**; (c) renderizado e interacción en
  navegador real — **PENDIENTE**. **(a)+(b) NO sustituyen a (c).** `03_TESTS.md` §15.4.
  Controles y acreditación: §15.5 (reversa de imputación sobre el vínculo: **no acreditado**;
  consistencia de compañía: **parcial**; reparto N:M: **Bloque D**).
- **Cierre versionado:** `madenat_lumber_logistics` **18.0.1.7.0** · `madenat_lumber_core` **18.0.6.6.0**.
- **Bloque D:** **NO implementado** (decisión «opción 3»; `linked` = vínculo registrado). Diseño: `19` §19.12.
- **Pendiente de evidencia manual:** navegador real (V3 *pixel*); concurrencia; base limpia.
