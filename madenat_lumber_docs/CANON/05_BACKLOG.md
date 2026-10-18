# MADENAT — Backlog Canónico

**Versión documental:** 8.40.0
**Fecha de actualización:** 2026-10-18  <!-- actualizado: 2026-10-18 — Cierre Definitivo Bloque 4J (AD-122): anti-copia absoluta de tabla S2S en todo el código productivo madenat_*, eliminación de doble redondeo de volúmenes y MBF con r3(), y suite final. Versión 05 8.39.0 → 8.40.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — Bloque 4I (AD-121): registro de deuda técnica TD-122 para rangos heurísticos en intake_wizard.py:314, normalización de script de salud y pruebas oficiales de integridad. Versión 05 8.38.0 → 8.39.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — Bloque 4H (AD-121): corrección de citas de decisiones diferidas (D5 para Bloque 5 y fitosanitario/motonave), descripción formal del Bloque 5 real (volumen físico real, tabla nominal->espesor real, tres listados y fitosanitario configurable), coherencia exacta S2S <= 0.001" (H3). Versión 05 8.37.0 → 8.38.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — Bloque 4G (AD-120) CERRADO EN LOCAL: G1 retiro copia hardcode _BLANKS_NOMINAL_MAP; G2 vectores f5085 y vol_documental; G3 health check OK/ADVERTENCIA/CRITICO; G4 hashes MD5 fijados y redondeados; G5 UserError S2S acotado a imperial; G6 1.533 tests reconciliados; G7 simulacion solo lectura; G8 edicion S2S por UI con trazabilidad y coherencia; G9 runbook borrador en CANON/02; G10 backlog diferido (Bloque 5, fitosanitario, patios, motonave, 26270). Versión 05 8.36.0 → 8.37.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — Bloque 4F (AD-119) IMPLEMENTADO en local: F1 tabla S2S sin copia en código y UserError ante tabla vacía; F2 Blanks y retiro limpio de deduction_factor; F3 constante única 1550.003; F4 auditoría de literales; F5 hashes MD5 dual; F6 correcciones de texto y citas; F7 pre-deploy health check; F8/F9 planes de patios y despliegue. Versión 05 8.35.0 → 8.36.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — Bloque 4E (AD-118) IMPLEMENTADO en local: E1 direct_width_min_mm y out_of_table_behavior; E2 parámetros en data XML con noupdate="1"; E3 sincronización 15 anchos activos (115 mm); E4 señal explícita is_s2s_inches sin heurística; E5 corrección total Guía 26270 con manual 5 5/8" (47,801 m³); E6 auditoría de literales. E7-E10 en análisis/propuesta. Versión 05 8.34.0 → 8.35.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-17 (3) — Bloque 4 (AD-116/AD-117) IMPLEMENTADO en local: BK-F12-S2S regla por datos, BK-F12-BLANKS-STOCK y FORMULA sin 1/16", BK-F12-PATIOS-UI marcador y filtros, BK-F12-SECADO campos y constraint dinámico. F3 rotulado como FALTA en código. Fitosanitario y datos históricos NO autorizados. Versión 05 8.33.0 → 8.34.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-17 (2) — alta Bloque 4 (AD-116): alineación de especificaciones con Cristhian Elgueta (BK-F12-S2S rango 75–155 mm, BK-F12-BLANKS directo a stock y sin deducción 1/16", BK-F12-PATIOS-UI, BK-F12-SECADO fitosanitario y BK-F12-MBF-EDIT). Versión 05 8.32.0 → 8.33.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-17 — FASE 12: Bloque 1 (AD-111: WP-C, WP-B rótulos, D-E0-3) y Bloque 2 (AD-112: WP-F P1–P5, WP-E plantilla métrica, WP-G alineación) CERRADOS en LOCAL. FASE 11 (AD-110) cerrada. Versión 05 8.30.0 → 8.31.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-10 (2) — nueva sección «Conciliación envío–retorno (Bloque A/B/C) — IMPLEMENTADO (2026-10-10)»: modelo `madenat.processor.return.link`, cierra la brecha (a) de CANON/19 §19.10; Bloque D cuantitativo PENDIENTE. Versión 05 8.16.0 → 8.17.0. Sin commit/push. -->
<!-- actualizado: 2026-10-10 (3) — sección «Conciliación envío–retorno (Bloque A/B/C)»: **ajuste de integridad** (`19` §19.13): reversa vs. procedencia, reimputación con historia, consistencia de compañía + regla de registro, elegibilidad dura (done/tipo interno), volúmenes N:M referenciales (`aggregator=False`). Módulo `madenat_lumber_logistics` **18.0.1.8.0**. Versión 05 8.17.0 → 8.18.0. Bloque D fuera de alcance. Sin commit/push. -->
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
- **Ajuste de integridad (2026-10-10, `19` §19.13) — IMPLEMENTADO.** Reversa de imputación **no**
  revierte la procedencia (vigencia `documentary_status`/`requires_reimputation` derivadas); reimputación
  con `previous_imputation_id` + rastro; **consistencia de compañía** (constraint + **regla de registro**
  multi-compañía); **elegibilidad dura** `state='done'`/tipo interno; **volúmenes N:M referenciales**
  (`aggregator=False`). Pruebas T13–T22 = **22/22**; `03_TESTS.md` §15.5–15.6. **Bloque D sigue fuera.**
- **Cierre versionado:** `madenat_lumber_logistics` **18.0.1.8.0** · `madenat_lumber_core` **18.0.6.6.0**.
- **Bloque D:** **NO implementado** (decisión «opción 3»; `linked` = vínculo registrado). Diseño: `19` §19.12.
- **Pendiente de evidencia manual:** navegador real (V3 *pixel*); concurrencia; base limpia.

---

## Operación manual de asignaciones centrada en SV (2026-10-10) — IMPLEMENTADO (`madenat_test`)

Continúa la conciliación envío–retorno (Bloque A/B/C). Reordena I2 alrededor del **SV** sin crear
documento de negocio, ledger ni motor de saldos nuevos. `CANON/19` **§19.14**; `02` §17.16.12;
`03` §16.

- **Entrada/consulta (A):** acción **Logística → Asignaciones SV** sobre `stock.lot`
  (`lot_flow_type='volume'`) con vistas dedicadas; cabecera con guía de procedencia, procesador,
  nominal, total imputado **aplicado** y **saldo documental I2**; detalle con imputación/guía/
  etiqueta/volumen/estado/fecha/usuario y acceso al documento.
- **Alta desde el SV (B):** botón «Asignar retorno» → asistente existente con `sv_lot_id` (contexto
  orientador; sin reparto/cantidades/aplicación automática). Reutiliza la imputación de trabajo.
- **Selección explícita (C):** `selected` + «Seleccionar todas»/«Quitar selección»; operación nueva
  sin auto-inclusión. Pestañas: «Etiquetas del retorno», «Asignación a SV», «Envíos relacionados»,
  «Motivo / reversa».
- **Conservación del borrador (D):** reconciliación (**upsert**) por etiqueta y por (línea, SV);
  reabrir conserva selección y reparto; bloqueo de cambio de guía. **No** es el Bloque D cuantitativo.
- **Integridad etiqueta–guía (E):** constraint de modelo + apply; **0** inconsistencias históricas.
- **Coherencia de volumen (F):** `0 < Σ reparto ≤ nominal`; parciales admitidos; techo duro de lote y
  exceso blando SV-side conservados.
- **Pruebas:** `T-MAN-01..12` = **12/12**; regresión `madenat_lumber_logistics` = **286 pruebas,
  4 fallas** (las mismas preexistentes/ambientales), **0 errores**.
- **Cierre versionado:** `madenat_lumber_logistics` **18.0.1.9.0**; `19` **1.11.0**.
- **Pendiente de evidencia manual:** navegador real (V3 *pixel*). Guion:
  `IMPL_ASSIGN_SV_20261010_165247/docs/GUION_MANUAL_NAVEGADOR.md`.
- **Bloque D (conciliación cuantitativa):** **NO implementado** (`19` §19.12). **Sin** commit/push.

---

## Corrección de duplicidad de accesos SV — «Rebaja de etiquetas» (2026-10-10)

**Estado:** IMPLEMENTADO EN DESARROLLO (`madenat_test`). Cierra la **duplicidad de navegación** que
reproducía la misma operación documental en «Asignaciones SV» e «Imputaciones documentales SV».
`CANON/19` **§19.15**; `02` §17.16.13; `03` §17.

- **Único acceso:** **«Rebaja de etiquetas»** (menú `menu_madenat_sv_assignment` reutilizado) sobre
  `stock.lot` volumen. «Imputaciones documentales SV» **retirado de la navegación**
  (`ir.ui.menu` 542 `active=False`), preservando la acción (867 → «Historial de rebajas»).
- **Navegación interna:** «Registrar rebaja», «Historial de rebajas» (por SV) y «Ver historial
  completo» **dentro** del recorrido; **sin** segundo menú.
- **Sin cambios en:** «Rebajar por Motonave», «Consolidación», ingesta, modelo/asistente/`apply`/
  `reverse`/saldos/permisos/auditoría.
- **Pruebas:** NAV-01..12 = **11/11**; regresión 298 pruebas, 4 fallas (las mismas preexistentes),
  0 errores. La **2.ª** `-u` verifica NAV-10 (sin reaparición del menú).
- **Versión:** `madenat_lumber_logistics` **18.0.1.10.0**; `19` **1.12.0**.
- **Pendiente mínimo:** **V3 *pixel*** (navegador real) — guion manual. **Sin** commit/push.

<!-- actualizado: 2026-10-10 (4) — sección «Corrección de duplicidad de accesos SV — Rebaja de
etiquetas»: cierra la duplicidad de navegación con evidencia (NAV-01..12, 2.ª `-u`). Versión 05
8.19.0 → 8.20.0. Sin commit/push. -->

---

## Operación y blindaje «Rebaja de etiquetas» (2026-10-10)

**Estado:** IMPLEMENTADO EN DESARROLLO (`madenat_test`). Mejora de inicio a fin de la operación
existente. `CANON/19` **§19.16**; `02` §17.16.14; `03` §18.

- **Elegibilidad:** sólo guías `service_return_confirmation='yes'` y no canceladas; rechazo de
  selección forzada en modelo (onchange + antes de construir), sin estados parciales; históricos
  consultables.
- **Cantidades:** nominal / rebajado aplicado / reservado / disponible documental, con exclusión del
  documento en curso (sin doble conteo). N:M no duplica totales.
- **Listado/búsqueda:** columnas separadas y filtros documentales buscables (agregados `store=True`);
  «En stock» opcional; columnas opcionales de retorno en guías.
- **Concurrencia:** advisory lock de **etiqueta + SV** en orden determinista (cierre de CON-01).
- **Pruebas:** `test_sv_rebaja_operativa.py` = **20/20**; regresión **318 pruebas, 4 fallas**
  (preexistentes), 0 errores.
- **Pendiente mínimo:** **V3 *pixel*** (navegador). **Sin** commit/push. **Bloque D** cuantitativo
  fuera de alcance.

**Pendientes específicos conservados:** Bloque D cuantitativo (§19.12); V3 de navegador; la búsqueda
por proveedor en el listado SV usa un `filter_domain` combinado «Guía/Proveedor» (la ruta punteada
`volume_source_guia_id.partner_id` no es válida como campo de búsqueda; alternativa sustentada).

<!-- actualizado: 2026-10-10 (5) — sección «Operación y blindaje Rebaja de etiquetas»: elegibilidad,
cantidades, filtros buscables y concurrencia con evidencia (20/20; regresión 318). Versión 05
8.20.0 → 8.21.0. Sin commit/push. -->

---

## Corrección de «Seleccionar todas» y asignación explícita (2026-10-10)

**Estado:** **CORREGIDO EN DESARROLLO** (`madenat_test`), con causa demostrada y pruebas. `CANON/19`
**§19.17**; `02` §17.16.15; `03` §19. El fallo reportado por Mauricio se **cierra con evidencia**;
la **aceptación visual sigue pendiente**.

- **Causa:** subcampo `readonly` de x2many sin `force_save` ⇒ el cliente no enviaba
  `processed_lot_id` (Odoo 18 `record.js::_getChanges`). **Corrección:** `force_save="1"`; sin tocar
  `required` ni usar `sudo`.
- **Flujo:** Seleccionar ≠ asignar ≠ aplicar. Acción explícita «Asignar seleccionadas al SV de
  trabajo» (volumen 0) + «Usar disponible»; resumen «X etiquetas · Y m³ preparados …».
- **Pruebas:** `test_sv_rebaja_seleccion_asignacion.py` = **16/16**; regresión **334 pruebas, 4 fallas**
  (preexistentes), 0 errores.
- **Pendientes concretos:** **aceptación visual de Mauricio (V3)**; Bloque D cuantitativo fuera de
  alcance.

<!-- actualizado: 2026-10-10 (6) — sección «Corrección de Seleccionar todas y asignación explícita»:
causa force_save, acciones explícitas y evidencia (16/16; regresión 334). Versión 05 8.21.0 → 8.22.0.
Sin commit/push. -->

---

## Rediseño operativo del asistente «Registrar rebaja» (2026-10-10)

**Estado:** IMPLEMENTADO EN DESARROLLO (`madenat_test`). **Interfaz anterior rechazada por Mauricio;
rediseño operativo entregado para nueva revisión visual.** `CANON/19` **§19.18**; `02` §17.16.16;
`03` §20.

- **Material del packing list** en columnas separadas (etiqueta/`ref`, SKU, producto, subproducto,
  dimensiones, piezas, volumen) + documental avanzada en columnas **opcionales**.
- **SKU/dimensiones declaradas** por la regla de promoción (sin cortar el nombre); guía 19827 **17/17**.
- **Granularidad por lote** (etiqueta repetida = lotes distintos; sin doble conteo).
- **Formulario amplio** (`o_xxl_form_view`, `target=current`) del mismo asistente.
- **Cantidades:** «Cantidad preparada» solo lectura; edición en «Asignación a SV» (mismo mecanismo).
- **Pruebas:** `test_sv_rebaja_material.py` = **8/8**; regresión **342 pruebas, 4 fallas**
  (preexistentes), 0 errores.
- **Pendiente único relevante:** **aceptación visual de Mauricio (V3)**.

<!-- actualizado: 2026-10-10 (7) — sección «Rediseño operativo del asistente Registrar rebaja»:
material del packing list, granularidad y formulario amplio (8/8; regresión 342). Versión 05
8.22.0 → 8.23.0. Sin commit/push. -->

## Interfaz clara y concisa del asistente «Registrar rebaja» — ambas pestañas (2026-10-10)

**Estado:** IMPLEMENTADO EN DESARROLLO (`madenat_test`). **Aceptación visual de Mauricio pendiente.**
`CANON/19` **§19.19**; `02` §17.16.17; `03` §21.

- **Cabecera única** (SV, guía, saldo documental del SV, seleccionadas, con reparto preparado, total
  preparado para el SV); sin repetir el saldo completo del SV por fila.
- **Totales con nombre y unidad**; subtotal del SV de trabajo separado del total general con varios SV.
- **«A asignar (m³)» editable** en «Materiales del retorno» (mismo reparto; sin saldo paralelo).
- **Etiqueta limpia + medidas**; SKU/código técnico como información secundaria.
- **Asignación a SV** con 4 columnas en un solo SV; «SV destino» sólo con varios SV.
- **Acciones breves**; «Usar disponible» no sobrescribe lo editado; footer Revisar y aplicar.
- **Disponibilidad cero:** causa real (Aplicado/Reservado/Sin capacidad) + aviso de no asignables.
- **Pruebas:** `test_sv_rebaja_ui_limpia.py` = **13/13**; regresión **355 pruebas, 4 fallas
  (preexistentes), 0 errores**.
- **Pendiente único relevante:** **aceptación visual de Mauricio (V3)**.

<!-- actualizado: 2026-10-10 (11) — sección «Interfaz clara y concisa del asistente Registrar rebaja —
ambas pestañas»: cabecera única, totales con unidad, A asignar editable, identidad limpia + medidas,
causa real de disponibilidad cero (13/13; regresión 355). Versión 05 8.23.0 → 8.24.0. Sin commit/push. -->


## HOTFIX bloqueante — OwlError al abrir «Registrar rebaja» (2026-10-10)

**Estado:** CORREGIDO EN DESARROLLO (`madenat_test`) · **renderización real pendiente de comprobación
manual** · **aceptación pendiente**. `CANON/19` **§19.20**; `02` §17.16.18; `03` §22.

- **Error real del navegador (Mauricio):** `Can not evaluate python expression: (bool(not
  wizard_id.multi_sv))` — `Name 'wizard_id' is not defined` (`ListRenderer.evalColumnInvisible`).
- **Causa:** `column_invisible` se evalúa con el contexto del **formulario padre**; no admite campos de
  fila (`wizard_id`). **No** fue caché.
- **Corrección:** `column_invisible="not parent.multi_sv"` + `<field name="multi_sv" invisible="1"/>`
  en el padre. Sin tocar Owl/assets/core; sin capturar la excepción.
- **Pruebas:** casos A–E + invariantes de arch = **20/20**; regresión **362 pruebas, 4 fallas
  preexistentes, 0 errores**.
- **Pendiente único relevante:** **comprobación manual de renderización + aceptación visual de Mauricio**.

<!-- actualizado: 2026-10-10 (12) — sección «HOTFIX bloqueante — OwlError al abrir Registrar rebaja»:
`column_invisible` fuera de contexto (`wizard_id` → `parent.multi_sv`) + carga de `multi_sv`. Versión 05
8.24.0 → 8.25.0. Sin commit/push. -->

## HOTFIX OWL — «Agregar una línea» en el documento de rebaja (`div.oe_chatter`, 2026-10-12)

- **Síntoma:** en `madenat.sv.imputation` (p. ej. `IMP04823`), «Agregar una línea» ⇒ `OwlError`
  `TypeError: Cannot read properties of undefined (reading 'includes') at get urlRelation`.
- **Causa (demostrada):** Odoo 18 CE ya **no** compila `div.oe_chatter`; los campos del chatter se filtraban
  como listas o2m editables (`mail.message`/`mail.followers`). Ver `19` §19.33.
- **Corrección (mínima):** `div.oe_chatter` → `<chatter/>` en `view_madenat_sv_imputation_form` y
  `view_madenat_processor_return_link_form`. Módulo `madenat_lumber_logistics` **18.0.1.26.0**.
- **Pruebas:** VIEW-01..05 de servidor 5/5; logistics 4/506 (0 nuevas); core+intake+logistics 6/4 de 1284
  (0 nuevas). **Navegador PENDIENTE.**
- **Hallazgos (no corregidos):** `madenat_vendor_payment` (mismo `div.oe_chatter`, módulo no instalado);
  endurecer `create` por RPC de `mail.message`/`mail.followers` (**decisión separada**).

<!-- actualizado: 2026-10-12 (13) — HOTFIX OWL chatter (`div.oe_chatter` → `<chatter/>`). Versión 05
8.25.0 → 8.26.0. Sin commit/push/despliegue. -->


## Supuesto de una sola compañía (AD-106) y conservación de los usuarios de prueba inactivos — 2026-10-15

**Pendientes abiertos por la FASE 7 (AD-107):**
- **RESUELTO en FASE 8 (AD-108):** `madenat_lumber_logistics` no instala desde cero — el `<record
  id="menu_madenat_sv_imputation" model="ir.ui.menu">` quedó **sin `name`** al retirarse su `<menuitem>` en
  `ded5e89`; se **restituyó el `<menuitem>`** antes del `<record>` (commit `7d277e9`, `logistics`
  **18.0.1.29.0**) y una instalación desde cero de los 4 módulos termina con **exit 0**.
- **Despliegue:** no mezclar «BD con WIP» y «código sin WIP»: la vista de `costing` con `action_apply_c2`
  (solo en el WIP, **D1 no commiteado**) hace fallar la re-validación en un `-u`. Comprobar en el destino.
- **Defecto de prueba (K7) — RESUELTO en FASE 8** (commit `7c417ae`): el helper de longitudes usa ahora
  `product.product`.

**Pendientes abiertos por la FASE 8 (AD-108):**
- **Configuración no sembrada en el alta limpia:** una base nueva **no** reproduce la de `madenat_test`
  (precisión decimal `Product Unit of Measure` 2 vs 4 y `Product Price` 2 vs 3; 1 producto vs 20; parámetros
  `madenat.*` como `allow_product_creation`, `allow_subproduct_creation`, `omission_threshold`, umbrales de
  varianza). **Declarar el juego mínimo de configuración** o los cálculos y varias suites diferirán en el
  destino.
- **D1 `costing` (`REQUIERE_DECISIÓN`):** (a) commitear con versión + CHANGELOG y desplegar con `reports`;
  (b) mantenerlo fuera (estado actual); o (c) revertir el WIP en la base local. HEAD y WIP son coherentes por
  separado; lo que rompe es la mezcla.
- **Prueba dependiente de datos:** `TestServiceReturnImputationGuard.test_09…` exige que el usuario real
  Cristhian tenga Jefatura/Gerencia; en una base donde no la tenga, falla (`AccessError`).
- **VIEW-01/04 en navegador:** sigue pendiente de ejecución manual (checklist entregada).

**Supuesto de una sola compañía (AD-106):** vigente.

- **Supuesto vigente (decidido):** MADENAT opera con **una sola compañía**. `madenat.guia.processing` **no**
  implementa `company_id` ni `ir.rule` de compañía; el control de acceso es **por rol** (jefatura /
  operaciones / auditoría), según AD-103/AD-104/AD-105. Ver `04_DECISION_LOG.md` **AD-106**.
- **Pendiente condicionado (reabrir):** si se incorpora **una segunda compañía**, debe **reabrirse** la decisión
  (aislamiento por compañía de las guías) **antes** de operar guías compartidas entre compañías.
- **Conservado (decidido):** los **3 usuarios inactivos** de prueba `@madenat.test` (`v3_concil_oper@`,
  `v3_concil_jef@`, `impl_sv_check@`) se **conservan**; no se eliminan ni se anonimizan. El pendiente **D7**
  (FASE 1) queda **DECIDIDO = CONSERVAR**.
- **Fuera de alcance (no aprobado):** limpieza generalizada de la bitácora de pruebas de **todas** las suites
  que hacen `commit()`; trigger de base de datos o hash encadenado para la bitácora (sigue **propuesto y no
  implementado**); despliegue al TEST remoto.

**Evidencia:** `AUDITORIA_INTEGRAL_20261012/README.md` §4.3 (H-DATA-1) y §7 (D7); `fase4/README.md` §7, §9, §10.

<!-- actualizado: 2026-10-15 (1) — sección «Supuesto de una sola compañía (AD-106) y conservación de los usuarios de prueba inactivos». Versión 05 8.26.0 → 8.27.0. Commit local ① de la FASE 5 (commits ordenados, solo local); sin push ni despliegue. -->


---

## FASE 10 — Registro de etiquetas en la rebaja SV (AD-109)

**Estado:** correcciones **S2/S3/S1 IMPLEMENTADAS Y PROBADAS en LOCAL** (`madenat_lumber_logistics`
18.0.1.29.0 → 18.0.1.32.0; commits `19611d0`, `e2d6b64`, `7ac1fcb`). Ver `04` **AD-109** y `19` **§19.34**.

**Pendientes abiertos (fuera del alcance de la FASE 10):**

- **Pendiente REQUIERE_DECISION — `IMP04823` (guía 1198, anulada y vacía, con `work_sv_lot_id` al SV).** Es un
  **dato de origen**, no un defecto del flujo (no tiene metadata de anulación ni evento de bitácora). Opciones:
  (a) conservarla como historia anulada; (b) reabrir/rehacer la rebaja de la guía 1198 con el flujo corregido.
  **No ejecutado.**
- **Pendiente operativo — resolución de `SV00000000841` en datos reales.** Con el flujo corregido, preparar la
  selección correcta de etiquetas hacia el SV y aplicar (o reversar/rehacer). Requiere confirmación de Mauricio;
  **no** se tocaron datos reales.
- **Pendiente — verificación en el REMOTO** del comportamiento corregido (esta fase es **local**; sin push ni
  despliegue).
- **Hallazgo abierto — trigger/bitácora.** `IMP04823` no tiene evento `imputation` ni `imputation_cancel` en
  `madenat_audit_log` (su anulación no pasó por el código). El **trigger de base de datos o hash encadenado**
  propuesto sigue **no implementado** (se mantiene el límite declarado en AD-105/H-SEC-5).
- **Pendiente — `VIEW-01/04` en navegador** para el flujo de rebaja (checklist manual entregada a Mauricio).
- **D1 (`costing`)** sigue **fuera** según AD-108; **P2-2** (menú vacío de `reports`) sigue **fuera**.

**Evidencia:** expediente `FASE10_REBAJA_SV_ETIQUETAS_20261015/` (`INFORME_FASE10.md`, `RUNBOOK_FASE10.md`,
`CHECKLIST_MANUAL_MAURICIO.md`, `pre/`, `post/`, `logs/`, `evidence/`).

<!-- actualizado: 2026-10-15 (4) — pendientes de la **FASE 10 (AD-109)**: S2/S3/S1 implementadas y probadas en
LOCAL (`logistics` 18.0.1.29.0 → 18.0.1.32.0; `19611d0`, `e2d6b64`, `7ac1fcb`); abiertos: decisión sobre
`IMP04823` (anulada y vacía), resolución de `SV00000000841` en datos reales, verificación en el remoto,
trigger/bitácora, VIEW-01/04 manual; **D1 `costing`** y **P2-2** siguen fuera. Versión 05 8.29.0 → 8.30.0.
Sin push ni despliegue. -->

---

## FASE 11 — Integridad del Ciclo de Vida de Imputaciones SV (AD-110)

**Estado:** 100% IMPLEMENTADA Y PROBADA en LOCAL (`madenat_lumber_logistics` 18.0.1.32.0 → 18.0.1.36.0).
- **A-1/B-1:** Estado y marcas de transición protegidas mediante `_i2_write_protected_state` (vía pública rechaza mutaciones sin acción oficial).
- **M-2 / M-4:** Reversa segura con bloqueo de recursos y cadena `origin_imputation_id` ↔ `reversed_imputation_id`.
- **B-2 / B-3:** Líneas inmutables fuera de preparación y anulación con motivo obligatorio.
- **Pendiente de Negocio:** Regularización de datos históricos `IMP02220` (0 repartos positivos) e `IMP04823` (anulada sin metadata).

---

## FASE 12 — Requerimientos de Operaciones (Cristhian) y Alineación del Sistema

**Estado:** Bloque 1 y Bloque 2 COMPLETADOS Y PROBADOS en LOCAL. Bloque 3 DETENIDO a la espera de autorización.

### Bloque 1 (AD-111) — CERRADO
- **WP-C (Consola y Menú 'Ingresos por Volúmenes'):** Búsqueda por estado, acción de ventana dedicada y menú en Gestión de Entradas (`madenat_lumber_intake` 18.0.0.16.0).
- **WP-B rótulos (Unificación de Rótulos de Volumen):** Homologación completa en vistas de Contenedor, Embarque e Imputación a «Vol. Compra (m³)», «Vol. Export (m³)» y «Vol. Documental (m³)».
- **D-E0-3 (Causa Raíz Guía 95806 / JCE -> "S.I.I. - LOS ANGELES"):** Documentada en informe de Bloque 1 sin alterar datos reales.

### Bloque 2 (AD-112) — CERRADO
- **WP-F (P1–P5) — Control de disponibilidad de etiquetas en imputación SV:**
  - P1: Campo `asignable` y toggle `selected` con `readonly="not asignable"`.
  - P2: `action_select_all()` restringe selección a etiquetas con saldo disponible, con notificación de advertencia.
  - P3: Pestaña `unavailable_material` («Sin disponibilidad») en el formulario del asistente con botón `action_open_consuming_documents`.
  - P4: Coherencia de resumen: campo `selectable_line_count` y desglose de etiquetas sin saldo en `assigned_summary`.
  - P5: Helper `_i2_lot_consuming_docs_detail(lot)` y error nominativo en `_i2_validate_hard_cap()` y payload.
  - Módulo: `madenat_lumber_logistics` 18.0.1.37.0 → 18.0.1.38.0.
- **WP-E — Plantilla estándar PACKING_METRICO_ASERRADA y guía de llenado:**
  - Plantilla Excel en `madenat_ingestion_engine/data/templates/PLANTILLA_PACKING_METRICO_ASERRADA.xlsx`.
  - Generador `generate_packing_template.py` y guía `docs/GUIA_LLENADO_PACKING_METRICO.md`.
  - Módulo: `madenat_ingestion_engine` 18.0.1.1.0 → 18.0.1.2.0.
- **WP-G — Alineación documental:**
  - Reconciliación de D-E0-1 (`_CAPSULA_CONTEXTO.md` actualizada al estado real: Fases 10 y 11 implementadas y probadas en local, pendientes de verificación manual de Mauricio y de despliegue al TEST).
  - Reconciliación de D-E0-2 (`HOJA_RUTA_EJECUTIVA.md` sincronizada con AD-110, AD-111, AD-112).
  - Backlog canónico actualizado.

### Bloque 3 — DETENIDO (Pendiente de Autorización de Mauricio)
- **WP-B ancho de exportación:** Uso de la tabla existente en `width_mapping.py` y `lumber.width.s2s.map`, simulación de solo lectura sobre embarques existentes sin recalcular valores almacenados, opción manual con usuario y fecha.
- **WP-A comparación guía vs packing:** A la precisión declarada de la guía con tope de 3 decimales, estado `ok_rounded`, parametrizable.
- **WP-D (patios):** Sigue EN ESPERA. No existe "conciliación documental" ni "imputación diferida" aprobadas.

### Bloque 4 — Alineación con Instrucciones de Cristhian (AD-116 / AD-117) — IMPLEMENTADO EN LOCAL (Commits 73439ed, 8d18d49, ef39ef2, 6676d6f)
- [x] **BK-F12-S2S (Rango S2S 75–155 mm y Regla por Datos H1–H5):**
  - **Estado:** **IMPLEMENTADO** (Commit `73439ed`).
  - Tabla S2S guiada exclusivamente por datos en `lumber.width.s2s.map` (14 anchos activos según planilla de Cristhian).
  - Sobreancho configurable vía `madenat.s2s_overwidth_inches` (0,125" por defecto). Anchos ausentes aplican `mm / 25.4` directo.
  - Parámetro de comportamiento fuera de tabla `madenat.out_of_table_behavior` ('direct', 'warning', 'block') para zona 155–170 mm.
  - Parámetro `s2s_exclusion_widths` deprecado formalmente. Prevalencia de ancho manual (`AD-115`) y chatter preservados.
  - Suite `test_export_width_s2s_wpb.py` (10 tests PASS, incluyendo verificación sobre 100 piezas y anti-hardcode).
- [x] **BK-F12-BLANKS-STOCK (Pase Directo a Stock para Blanks Clear):**
  - **Estado:** **IMPLEMENTADO** (Commit `8d18d49`).
  - Blanks que pasan directo a stock conservan volumen documental declarado (`vol_documental_m3`) sin recálculo.
- [x] **BK-F12-BLANKS-FORMULA (Fórmula Exportación F4 sin Deducción de Espesor):**
  - **Estado:** **IMPLEMENTADO** (Commit `8d18d49`).
  - Deducción de $1/16"$ eliminada en `lumber.export.formula` (`deduction_factor = 0.0`) y `lumber.reception`.
  - Vectores F4 certificados: $16\text{ ft} \times 250 = 4,425\text{ m³}$; $16\text{ ft} \times 270 = 4,778\text{ m³}$ ($1,5" \times (3\text{ }5/8 + 1/8) \times 16 \times \text{pzas} / 5085,312$).
- [x] **BK-F12-PATIOS-UI (Gestión de Patios en Recepción y Consola):**
  - **Estado:** **IMPLEMENTADO** (Commit `ef39ef2`).
  - Marcador `is_patio` en `stock.location`, acción, menú, filtros y agrupadores por Patio y OC en `lumber.reception`.
  - Seed con `noupdate="1"` para Patio Ferramenta. Sin IDs ni nombres hardcodeados (regla H2).
- [x] **BK-F12-SECADO-LOT (Campos y Validación de Secado en Horno):**
  - **Estado:** **IMPLEMENTADO** (Commit `6676d6f`).
  - Campos opcionales `drying_temp_c`, `drying_duration_hours`, `drying_date` en `stock.lot`. Constraint dinámico validado contra parámetros de configuración (`madenat.drying_temp_min_c/max_c` [50–90 °C] y `madenat.drying_duration_min_hours/max_hours` [50–80 h]).
- [ ] **BK-F12-SECADO-FITOSANITARIO (Descripción Fitosanitaria de Blanks):**
  - **Estado:** **EN ESPERA** (no autorizado en este bloque hasta identificar qué documento o campo del sistema la genera).
- [ ] **BK-F12-F3-FISICO (Fórmula F3 Real Físico 38,1 mm):**
  - **Estado:** **FALTA** en código (no existe campo ni función que la calcule).
- [ ] **BK-F12-MBF-EDIT (Edición Manual Justificada de Volumen y MBF):**
  - **Estado:** **EN ESPERA** (no autorizado en este bloque).

### Bloque 4E — Ajustes Finales (AD-118) — IMPLEMENTADO EN LOCAL (Commits ec4f968, 6221a60, d65089a, 9be38c8)
- [x] **E1 — Parametrización Umbral Ancho Directo (AD-118 / Commit `ec4f968`):**
  - **Estado:** **IMPLEMENTADO**.
  - Eliminado literal `155 < rough_mm < 170` de `madenat_ingestion_config.py`. Definidos `madenat.direct_width_min_mm` (170.0) y `madenat.out_of_table_behavior` ('warning').
  - Regla: ancho en tabla S2S activa $\to$ S2S + sobreancho; ausente y $< 170$ mm $\to$ comportamiento configurado ('warning' con log y chatter de guía, 'block', 'direct'); ausente $\ge 170$ mm $\to$ directo $\text{mm}/25,4$ sin advertencia.
- [x] **E2 — Valores por Defecto en DATA XML (AD-118 / Commit `6221a60`):**
  - **Estado:** **IMPLEMENTADO**.
  - Declarados en `data/ingestion_config.xml` con `noupdate="1"`: `param_s2s_overwidth_inches`, `param_out_of_table_behavior`, `param_direct_width_min_mm` y parámetros de secado.
- [x] **E3 — Sincronización Ancho 115 mm (AD-118 / Commit `d65089a`):**
  - **Estado:** **IMPLEMENTADO**.
  - Revertido `active=False` de `seed_s2s_115` en `data/ingestion_seed_fase2.xml` (15 anchos activos sincronizados en base limpia y `madenat_test`).
- [x] **E4 — get_s2s_adjustment sin Heurística (AD-118 / Commit `9be38c8`):**
  - **Estado:** **IMPLEMENTADO**.
  - Tolerancia numérica eliminada. Parámetro y señal explícita `is_s2s_inches` desde el normalizador de documentos. Orden de resolución canónico en 4 ramas validado.
- [x] **E5 — Corrección Aritmética Canónica Guía 26270 (AD-118):**
  - **Estado:** **DOCUMENTADO**.
  - Total Guía 26270 con ancho manual 5 5/8": **47,801 m³** (impacto de **-0,208 m³** vs almacenado 48,009 m³ y **-0,092 m³** vs F2 47,893 m³).
- [x] **E6 — Auditoría de Literales de Negocio (AD-118):**
  - **Estado:** **AUDITADO**.
  - Verificadas ocurrencias de 1550, 1.5 y 155 como constantes físicas nombradas, identificadores o datos de prueba. Cero literales de negocio hardcodeados.

### Bloque 4F — Cierre Técnico Previo al Despliegue (AD-119) — IMPLEMENTADO EN LOCAL (Commits 067d01c, 7cc5305, 7c2c07c, fefda73)
- [x] **F1 — Tabla S2S sin copia en código y UserError ante tabla vacía (AD-119 / Commit `067d01c`):**
  - **Estado:** **IMPLEMENTADO**.
  - Eliminado el diccionario estático de respaldo de `madenat_ingestion_config.py` (incluyendo la entrada errónea `115: (4.125, "4 1/8")`).
  - `lumber.width.s2s.map` es la fuente única de verdad. Si la tabla no contiene registros activos, se interrumpe el procesamiento con `UserError` y log estructurado `[MADENAT-S2S-EMPTY]`.
  - Pruebas unitarias añadidas y validadas: tabla vacía levanta `UserError`, 115 mm mapea a 4.375 + 0.125 = 4.500" (1.742 m³), y ausencia de fallback en código.
- [x] **F2 — Retiro de deduction_factor del modelo sin alterar base de datos (AD-119 / Commit `7cc5305`):**
  - **Estado:** **IMPLEMENTADO**.
  - Eliminado el campo `deduction_factor` de `lumber.export.formula` y de las vistas XML sin alterar las columnas ni filas en PostgreSQL.
  - En `lumber_reception.py` se dejó de leer `deduction_factor`, aplicando directamente la fórmula F4 limpia $(1,5 \times (\text{Ancho} + 0,125) \times \text{Largo}_{ft} \times \text{Piezas}) / 5085,312$.
  - Validación con registro real de BD `f5085` (id=1, que conserva su factor en BD): vectores 16 ft × 250 = 4.425 m³ y 16 ft × 270 = 4.778 m³ coinciden con precisión milimétrica.
- [x] **F3 — Constante única 1550.003 en utils_uom (AD-119 / Commit `7c2c07c`):**
  - **Estado:** **IMPLEMENTADO**.
  - Unificada `CONST_M3_TO_IN2_M = Decimal('1550.003')` e `INCH_SQ_METERS_TO_M3 = CONST_M3_TO_IN2_M` en `utils_uom.py`.
  - Se evaluó el impacto de la unificación entre `1550.003`, `1550.0031` y `1550.003096`: altera 0 volúmenes (0.000 m³ de diferencia en los 15 anchos, Guía 26270 y muestras JCE).
- [x] **F4 — Auditoría Exhaustiva de Literales en Código Python (AD-119):**
  - **Estado:** **AUDITADO**.
  - Auditoría sistemática archivo:línea en `madenat_*` (excluyendo `tests/` y docs) para `0.125`, `1550`, `1.5`, `38.1`, `5085.312`, `150`, `155`, `170`, `160`, `175`, `195`.
  - Justificadas nuevas apariciones: `1550.003` en `utils_uom.py:27`, `1.5` en `lumber_reception.py:821`. Cero literales de negocio espurios.
- [x] **F5 — Hashes MD5 con Doble Consulta (AD-119):**
  - **Estado:** **AUDITADO E INVARIANTE**.
  - Documentadas las dos consultas y sus hashes: Consulta A (texto crudo Parte 0) y Consulta B (numérica redondeada a 4 decimales Informe 4E). Ambas consultas conservan 100% de invariancia histórica en `stock_lot`, `madenat_guia_processing_line` y `lumber_shipment_line`.
- [x] **F6 — Precisiones Terminológicas y Citas de Código (AD-119):**
  - **Estado:** **DOCUMENTADO**.
  - Origen de 47,417 m³ clasificado como "no reconstruido" (aritméticamente inconsistente con 43,601 + 3,730 = 47,331 m³).
  - Citas de líneas de las 4 ramas en `madenat_ingestion_config.py` actualizadas: Rama 2 (160-165), Rama 3 (167-170), Rama 4 (172-203).
- [x] **F7 — Script de Comprobación Previa al Despliegue (AD-119 / Commit `fefda73`):**
  - **Estado:** **IMPLEMENTADO**.
  - `madenat_lumber_core/scripts/pre_deploy_health_check.py` ejecutable en `odoo shell`.
  - Modo estricto de solo lectura (`rollback()`), valida 15 anchos S2S, parámetros `madenat.*`, módulos instalados y perfil F4 (`f5085`).
- [ ] **F8 — Análisis y Plan Arquitectónico para Patios Operativos (AD-119 — Solo Análisis):**
  - **Estado:** **PLANIFICADO / NO IMPLEMENTADO**.
  - Identificación de IDs reales en BD: PUERTO CORONEL (id=17), MARVAL (id=18), Bodega Tepornac (id=19).
  - Propuesta: configuración mediante parámetros `madenat.location_marval_id` y `madenat.location_puerto_coronel_id` sin crear registros duplicados vía XML. Bodega Tepornac permanece como INFERENCIA.
- [ ] **F9 — Runbook Operacional de Despliegue Remoto (AD-119 — Solo Plan):**
  - **Estado:** **PLANIFICADO / NO IMPLEMENTADO**.
  - Procedimiento en 6 fases: pre-requisitos (git tag, dump), validación previa (script F7), actualización de código, actualización Odoo (`-u madenat_lumber_core`), validación post y plan de reversa.

### Bloque 4G — Cierre Técnico Final en Desarrollo (AD-120) — IMPLEMENTADO EN LOCAL

- [x] **G1 — Retiro de copia hardcode _BLANKS_NOMINAL_MAP de reception_parser (Commit `bbea0fd`):**
  - **Estado:** **IMPLEMENTADO**.
  - Retirada la constante a nivel de clase `_BLANKS_NOMINAL_MAP` y `_NOMINAL_TOLERANCE` en `reception_parser.py`. Delega canónicamente en `madenat.ingestion.config.get_blank_nominal_map()`.
- [x] **G2 — Verificación de Vectores Blanks en Registro Real f5085:**
  - **Estado:** **VERIFICADO Y AUDITADO**.
  - Verificados vectores sobre BD real: 100 mm (16 ft × 250 = 4.425 m³, × 270 = 4.778 m³) y 140 mm (16 ft × 250 = 5.899 m³, × 270 = 6.371 m³).
  - Discrepancia legacy de 1 milésima explicada por división directa `5085.312` vs pasos intermedios. Preservación estricta de `vol_documental_m3 > 0` acreditada.
- [x] **G3 — Script de Comprobación Previa al Despliegue con 3 Niveles (Commit `a022be5`):**
  - **Estado:** **IMPLEMENTADO Y VALIDADO**.
  - `pre_deploy_health_check.py` opera en modo estricto solo lectura con `rollback()`.
  - Niveles: OK, ADVERTENCIA (código 0, detecta `out_of_table_behavior = 'direct'` y patios `is_patio = False`), CRÍTICO (código 1). Chequeo de versiones de intake y shipping_core.
- [x] **G4 — Hashes MD5 con Consulta Fijada:**
  - **Estado:** **VERIFICADO E INVARIANTE**.
  - Medición en `madenat_test`: `madenat_guia_processing_line` (82 filas, `b43a26b6fd072ff96ed075ca1e2f585e`) y `lumber_shipment_line` (11 filas, `b048f9428859b4c960b83b9ddf1cc701`) 100% invariantes.
- [x] **G5 — Ámbito del UserError por Tabla S2S Vacía (Commit `2a5c8ef`):**
  - **Estado:** **IMPLEMENTADO Y CON TESTS**.
  - UserError acotado exclusivamente a perfiles imperiales con ancho < `direct_width_min_mm` (170 mm). Perfiles métricos y anchos directos no se bloquean aunque la tabla esté vacía.
- [x] **G6 — Reconciliación de Conteo de Pruebas:**
  - **Estado:** **VERIFICADO**.
  - Suite de export width pasa 19/19 tests unitarios (+ 4 tests G8 en suite dedicada = 23). Conteo total en módulos core reconciliado.
- [x] **G7 — Script de Simulación de Embarques de Solo Lectura Remoto (Commit `3efe7b5`):**
  - **Estado:** **IMPLEMENTADO**.
  - `madenat_lumber_core/scripts/simulacion_embarques_solo_lectura_remoto.py` verificado 100% inocuo de solo lectura (sin write, create, unlink ni commit).
- [x] **G8 — Tabla S2S: Edición por Interfaz, Trazabilidad y Coherencia (Commit `9134290`):**
  - **Estado:** **IMPLEMENTADO Y CON TESTS**.
  - `lumber.width.s2s.map` con tracking de campos (`mail.thread`), validación de coherencia decimal/etiqueta dentro de ±1/16" (0.0625), vistas con chatter y nota R5/D6, permisos para Auditoría y Operaciones, y suite de tests unitarios (`test_lumber_width_s2s_map_g8.py` 4/4 pasando).

---

### Backlog Técnico Diferido (G10 AD-120 / H4 AD-121 — Sin Código, Solo Documentado)

Las siguientes iniciativas quedan formalmente registradas como **DIFERIDAS**, sin impacto en código actual, con su diseño mínimo, utilidad esperada y criterio de cierre:

#### (a) Bloque 5: Tabla Nominal → Espesor Real como DATO, Volumen Físico Real, Tres Listados y Fitosanitario Configurable
- **Estado:** **DIFERIDO** (Decisión Mauricio — D5).
- **Utilidad Esperada:** Eliminar la ambigüedad operativa entre volumen nominal de compra, volumen comercial de embarque y volumen físico real métrico cubicado, permitiendo a Planta, Embarque y Facturación operar con tres listados independientes y exactos sin contaminar los cálculos aduaneros, integrando además la descripción fitosanitaria como texto configurable.
- **Diseño Mínimo:**
  - Modelo persistente `lumber.thickness.real.map` (espesor nominal comercial → espesor real físico en mm). Ejemplo: 1 1/2" nominal → 38.1 mm real; 1" nominal → 25.4 mm real.
  - Campo `vol_physical_real_m3` calculado como $(E_{real\_mm} \times A_{real\_mm} \times L_{m} \times Piezas) / 1.000.000$.
  - Generación de 3 listados/reportes nativos en Recepción y Embarque: (1) Según Compra, (2) De Embarque (exportación), (3) De Medidas Reales (físico).
  - Parámetro de texto fitosanitario configurable (`madenat.phytosanitary_default_text`) para leyendas de secado/tratamiento térmico sin texto fijo en código.
- **Criterio de Cierre:** Los tres listados cuadran con las guías de recepción y packing lists reales, sin alterar las fórmulas ni volúmenes históricos de `vol_shipment_m3`.

#### (b) Descripción Fitosanitaria como Campo Configurable
- **Estado:** **DIFERIDO** (Decisión Mauricio — D5 — Componente de Bloque 5).
- **Utilidad Esperada:** Flexibilizar la leyenda de secado/tratamiento térmico según el mercado de destino (SAG, NIMF-15) sin depender de cadenas de texto fijas en código.
- **Diseño Mínimo:**
  - Parámetro del sistema `madenat.phytosanitary_default_text` o campo en `lumber.export.formula` / ficha de producto.
  - Documento origen citado: Certificado Fitosanitario SAG y Orden de Despacho de Exportación.
  - Inyección en plantillas de factura y packing list si el producto tiene `is_kiln_dried = True`.
- **Criterio de Cierre:** El operador puede modificar la descripción desde Ajustes > Técnico > Parámetros del Sistema y el reporte impreso refleja el cambio dinámicamente.

#### (c) Marcado de Patios Operativos (MARVAL y PUERTO CORONEL) sin IDs Numéricos
- **Estado:** **DIFERIDO** (Decisión Mauricio — D2).
- **Utilidad Esperada:** Distinguir ubicaciones de patio frente a bodegas techadas para filtrado en Consola de Recepción sin acoplar código a IDs primarios de PostgreSQL.
- **Diseño Mínimo:**
  - Uso del mecanismo nativo ya presente: campo booleano `is_patio = fields.Boolean(string="Es Patio")` en `stock.location`.
  - Marcado manual por UI o script de post-despliegue mediante búsqueda determinista por nombre/código de ubicación: `env['stock.location'].search([('name', 'in', ['MARVAL', 'PUERTO CORONEL'])])`.
  - `Bodega Tepornac` (id=19) permanece documentada como **INFERENCIA** (no es patio principal; se clasifica según reglas de custodia).
- **Criterio de Cierre:** Las ubicaciones clave tienen `is_patio = True` sin haber introducido IDs numéricos en Python ni duplicado registros en XML.

#### (d) Filtro de Consolidación por Motonave
- **Estado:** **DIFERIDO** (Decisión Mauricio — D5).
- **Utilidad Esperada:** Permitir a Logística filtrar y agrupar lotes y contenedores consolidados directamente por el buque/motonave asignado para el embarque marítimo.
- **Diseño Mínimo:**
  - Agregar campo relacional o búsqueda en vistas de consolidación: `vessel_id` / `booking_id` en `lumber.container` o `lumber.export.shipment`.
  - Filtro predeterminado en `search` view: "Por Motonave".
- **Criterio de Cierre:** Búsqueda ágil de todos los contenedores y lotes vinculados a una nave en una sola vista.

#### (e) Corrección del Histórico de la Guía 26270: NO AUTORIZADA
- **Estado:** **DIFERIDO / NO AUTORIZADA** (Decisión Mauricio — D3 / R5).
- **Utilidad Esperada:** Preservar la inmutabilidad histórica legal y contable de los registros emitidos en producción.
- **Diseño Mínimo:**
  - Se mantiene la invariancia de los registros existentes de la Guía 26270.
  - Cualquier ajuste o re-liquidación comercial debe realizarse mediante documento de ajuste complementario (nota de débito/crédito o regularización de inventario), NUNCA modificando las líneas históricas de `madenat_guia_processing_line` ni `stock_lot`.
- **Criterio de Cierre:** 0 modificaciones a filas históricas; MD5 canónico permanece inalterado.

#### (f) Deuda Técnica I2 (TD-122): Rangos Heurísticos de Detección en intake_wizard.py:314
- **Estado:** **DEUDA TÉCNICA REGISTRADA (AD-121)**.
- **Utilidad Esperada:** Eliminar rangos numéricos hardcodeados `(1.5 <= val <= 6.5)` en la heurística de detección de discordancia de unidades (perfil `f5085` con largos métricos en `intake_wizard.py:314`).
- **Diseño Mínimo:**
  - Crear parámetro del sistema en `ir.config_parameter`: `madenat.metric_length_heuristic_range` (default: `'1.5-6.5'`).
  - Crear lector en `madenat.ingestion.config` o método helper en `intake_wizard.py` que lea los límites mínimo y máximo desde configuración con fallback seguro.
- **Criterio de Cierre:** Los límites de detección de largos métricos en el asistente de ingesta son configurables sin modificar código Python.

