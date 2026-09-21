# MADENAT — Backlog Canónico

**Versión documental:** 7.2.0
**Fecha de actualización:** 2026-09-21
**Estado:** ACTIVO — AD-68/AD-69 cerrados (ruta granel en intake + fix disparo BT-04); higiene de `reception_workflow.py` cerrada (2026-09-21). Frente principal AD-65 sigue pendiente de las tareas de UI/wizard.

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
- **Discrepancia menor de índice:** `INDICE_DOCUMENTACION.md:26` sigue listando `05_BACKLOG.md` como v6.3.0.
- **Discrepancia interna en README:** `madenat_ingestion_engine/README.md:246-248` afirma "solo depende de base", mientras `__manifest__.py:22` declara `depends: ['base', 'madenat_lumber_core']`.

---

*(Nota: Las Fases 0.5 a 3 se encuentran 100% completadas y su estado está documentado en `02_CONTINUIDAD.md`)*

---

## FRENTE PRINCIPAL — AD-65: Recepción a Granel + Balance de Masa + Consolidación Administrativa

**Estado:** Diseño aprobado (2026-09-12). Prerequisito AD-64 con diseño ya auditado y aprobado (2026-09-20), pendiente de implementación de código.

### Prerequisito AD-64 — diseño aprobado, con 3 ajustes obligatorios antes de codificar

- [ ] Implementar modelo nuevo `madenat.guia.processing.source.lot.line` (`guia_processing_id` M2O cascade, `lot_id` M2O `stock.lot` required, `qty_to_consume` Float `digits=(16,3)` required), expuesto como `source_lot_line_ids` (One2many) en `madenat.guia.processing`, junto al `source_lot_ids` (M2M) existente sin reemplazarlo.
- [ ] Ajuste 1 — Validación de rango: exigir `0 < qty_to_consume <= lot.volumen_m3` en la nueva rama de `_get_or_create_consumption_picking()`.
- [ ] Ajuste 2 — Documentar la doble fuente de verdad como transitoria: `source_lot_ids` (M2M, legacy/fallback) y `source_lot_line_ids` (O2M, vía nueva) coexisten deliberadamente, preservando compatibilidad con `madenat_toll_processing` y con `TestGuiaProcessingConsumptionBT04`.
- [ ] Ajuste 3 — No confundir volumen con costeo: este diseño resuelve el consumo parcial a nivel de stock, pero el prorrateo de `wood_cost_usd`/`total_cost_usd` sigue siendo brecha separada (diferida a Costeo por AD-65 §1.9).
- [ ] Modificar `_get_or_create_consumption_picking()` (`madenat_guia_processing.py:3852`) con rama condicional: `source_lot_line_ids` con datos → usar `qty_to_consume` por línea; vacío → fallback a `qty = lot.volumen_m3`.
- [ ] No modificar `_reverse_consumption_picking()` ni `action_force_cancel()` — ambos ya leen `qty = move.quantity or move.product_uom_qty` (líneas ~4026 y ~4313), agnósticos a consumo parcial.
- [ ] Agregar ACL para el nuevo modelo en `madenat_lumber_core/security/ir.model.access.csv`.
- [ ] Agregar tests nuevos en `test_guia_processing.py` (clase separada, sin tocar `TestGuiaProcessingConsumptionBT04`): consumo parcial por línea, bloqueo por `qty > volumen_m3`, fallback sin líneas.
- [ ] Verificar que `madenat_toll_processing/models/guia_processing_integration.py:37-40` sigue funcionando con el fallback (solo verificación, sin modificación en esta etapa).

### Prerequisito adicional detectado — tercera derivación en intake

- [ ] Diseñar (no implementar todavía) una tercera derivación en `intake_wizard.py` para el flujo de recepción a granel que NO fije `intake_direct_stock=True`, permitiendo que la guía resultante pueble `source_lot_line_ids` para envío parcial a proceso vía Balance de Masa.

### Tareas de implementación de AD-65 (una vez resuelto el prerequisito AD-64)

- [ ] Extender `madenat_ingestion_engine` con el motor de "mejor esfuerzo" en cascada: tabla PDF de columnas fijas configurables → subtotales por grupo → total de encabezado mínimo garantizado.
- [ ] Implementar selección manual de tipo de detalle (línea por línea vs. agregado) en el wizard de intake.
- [ ] Implementar wizard `intake.tipo_ingreso.reclassify.wizard` con registro en `madenat.audit_log`, disponible solo antes de Gate 3.
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
| 5 fallos en `test_supplier_resolution.py` y `test_reception_supplier_rut_extraction.py` | Sesión 2026-09-21, misma investigación de regresión | Sospecha de contaminación de datos entre corridas de test (IDs de partner cambiantes) | No re-verificado — mismo patrón que hallazgo anterior, sin aislamiento confirmado |

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
- [x] AD-68/AD-69: ruta granel en intake + fix disparo BT-04 (2026-09-21)
- [x] Higiene: migrar `palabras_proceso` duplicado en reception_workflow.py a madenat.ingestion.config (2026-09-21, post-AD-68)
