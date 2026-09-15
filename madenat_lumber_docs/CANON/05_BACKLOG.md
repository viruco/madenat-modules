# MADENAT — Backlog Canónico

**Versión documental:** 7.0.0
**Fecha de actualización:** 2026-09-15
**Estado:** ACTIVO — Frente principal: implementación de AD-65 (Recepción a Granel + Balance de Masa + Consolidación Administrativa), bloqueada por el gap de consumo parcial de pool (AD-64).

---

## Regla de uso

Este backlog solo debe contener trabajo pendiente, prioridades activas y criterios de cierre.
Si un tema ya quedó fijado como regla, debe vivir en `04_DECISION_LOG.md`.
Si un tema ya quedó validado como estado, debe vivir en `02_CONTINUIDAD.md`.
Si un tema ya quedó evidenciado, debe vivir en `03_TESTS.md`.

---

## Resumen de cambios desde v6.3.0 (2026-06-16)

- **Cerrado:** BT-01, BT-02, BT-03, BT-04 (integridad de escritura a `stock.lot`, todos 2026-08-16).
- **Cerrado:** C1-C4 de Observaciones Cristhian, incluyendo C3 (deduction_factor 0.0625, confirmado por evidencia Excel).
- **Cerrado:** AD-51 a AD-55 (puerta única de ingreso `madenat_lumber_intake`, homologación de política de OC Producto/Procesados, homologación UX "Modificar origen").
- **Nuevo frente activo (máxima prioridad):** AD-65 — diseño aprobado, implementación pendiente.
- **Nuevo prerequisito bloqueante:** AD-64 — gap de consumo parcial de pool en `_get_or_create_consumption_picking`.
- **Nuevo hallazgo abierto:** AD-63 — `madenat_ingestion_engine` sin trazabilidad CANON/git, gaps de extracción PDF.
- **Nueva deuda técnica explícita:** AD-56 — `origin_scope` pendiente en `lumber.profile.subproduct.rule`.
- **Persiste sin resolver desde 2026-06-16:** `reception_id` no poblado consistentemente en algunos lotes de recepción directa.

---

*(Nota: Las Fases 0.5 a 3 se encuentran 100% completadas y su estado está documentado en `02_CONTINUIDAD.md`)*

---

## FRENTE PRINCIPAL — AD-65: Recepción a Granel + Balance de Masa + Consolidación Administrativa

**Estado:** Diseño aprobado (2026-09-12, Mauricio, Arquitecto/Tech Lead). Implementación pendiente.

### Prerequisito bloqueante

- [ ] Extender `_get_or_create_consumption_picking` para soportar consumo de una **cantidad parcial** del pool de volumen del patio, en lugar de `qty = lot.volumen_m3` completo (gap AD-64).

### Tareas de implementación (una vez resuelto el prerequisito)

- [ ] Extender `madenat_ingestion_engine`: tabla PDF de columnas fijas configurables -> subtotales por grupo -> total de encabezado mínimo garantizado.
- [ ] Selección manual de tipo de detalle (línea por línea vs. agregado) en el wizard de intake.
- [ ] Wizard `intake.tipo_ingreso.reclassify.wizard` con registro en `madenat.audit_log`, disponible solo antes de Gate 3.
- [ ] Registro de "Patio" como `stock.location` nativo bajo demanda (sin modelo propio).
- [ ] Consolidación administrativa: pantalla única con guías candidatas, saldo disponible, asignación con un clic.
- [ ] Menú Toll para Operaciones: campo "Enviar a proceso" + selección de procesador + botón único.
- [ ] Ajustar `ir.model.access.csv` de `madenat_toll_processing` para Operaciones.
- [ ] Extender `madenat_lumber_reports` con reporte de conciliación informativo.

### Criterio de salida

No se libera ninguna pieza de AD-65 sin verificar que el sistema no valide ni exija correspondencia de detalle entre lo enviado a proceso y lo retornado.

### No se toca en esta implementación

Gates 0-3, `reception_parser.py`, lógica interna de `madenat_toll_processing`, esquema de `stock.lot` más allá de lo necesario para consumo parcial. Ningún módulo nuevo.

---

## FASE 4 — REFACTOR MODULAR

- [ ] Separación final de `LumberReceptionLine` a archivo propio. `lumber_reception.py` mantiene 3,054 líneas y 5 responsabilidades concentradas.

### Criterio de salida

Cerrar este punto solo si el refactor final no rompe instalación, pruebas ni continuidad.

---

## FASE 5 — CALIDAD Y ESTABILIDAD

- [ ] Formalizar tolerancias por tipo de madera.
- [ ] Limpiar warnings XML.
- [ ] Resolver constraint `stock_lot_check_cost_positive`.
- [ ] BT-05: Parseo disperso en `madenat_guia_processing.py` — 9 métodos sin dispatcher equivalente a `reception_parser.py`.
- [ ] Diagnóstico `reception_id` no poblado: revisar creación de `stock.lot` en Gate 3, determinar si es bug sistemático, agregar validación en Gate 3 que rechace lotes sin FK de origen. No aplicar scripts destructivos sin diagnóstico confirmado.
- [ ] `origin_scope` en `lumber.profile.subproduct.rule` (AD-56): el catálogo no distingue si una regla aplica a Producto o Procesados.
- [ ] Gate de OC en Costeo: `action_apply_costs()` no valida OC resuelta pese a la política documentada. Refuerzo debe vivir en `madenat_lumber_costing`, nunca en `madenat_lumber_core`.
- [ ] Alinear test T13 con `deduction_factor = 0.0625` ya confirmado.

### Criterio de salida

No avanzar a consolidaciones mayores mientras la base técnica siga generando riesgos.

---

## FASE 6 — VALIDACIÓN FUNCIONAL (UAT)

- [ ] UAT end-to-end de Producto y Procesados.
- [ ] Validación operacional con datos de prueba de la genealogía padre-hijo (`parent_lot_id`/`child_lot_ids`/`generation_level`).
- [ ] T29-T32 sin evidencia formal.
- [ ] Validación end-to-end en staging de `stock.landed.cost`.
- [ ] Ejecución formal en staging de las suites C2, C3, C4.

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

| Ítem | Origen | Naturaleza |
|---|---|---|
| `madenat_ingestion_engine` sin trazabilidad CANON/git | AD-63 | Módulo instalado con consumidor activo, nunca commiteado |
| `core_utils.py` código muerto | Auditoría 2026-07-08 | 0 referencias, no archivado |
| `product_template.py` huérfano | Auditoría 2026-07-08 | Extensión nunca desplegada |
| `lumber_reception_id` campo legacy | `12_FLUJOS_INGESTA.md` | No usar en nuevos desarrollos |
| `purchase_cost_usd` deprecado | `08_COSTEO.md` | Solo compatibilidad histórica |

---

## RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
|---|---|---|---|
| Recepción a granel + Balance de Masa + Consolidación administrativa | Alta | Implementar AD-65 | DISEÑO APROBADO, IMPLEMENTACIÓN PENDIENTE |
| Costeo sin prorrateo por consumo parcial | Alta | Resolver gap AD-64 | ABIERTO |
| Constraint `stock_lot_check_cost_positive` | Alta | Revisar data/modelo | ABIERTO |
| `reception_id` no poblado | Alta | Diagnosticar causa raíz en Gate 3 | ABIERTO desde 2026-06-16 |
| `madenat_ingestion_engine` sin trazabilidad | Media | Formalizar en CANON | ABIERTO — AD-63 |
| BT-05 — Parseo disperso | Media | Refactor posterior a integridad | ABIERTO |
| Monolito parcial en `lumber_reception.py` | Media | Refactor futuro | ABIERTO |
| Tolerancias no formalizadas | Media | Parametrizar | ABIERTO |
| `origin_scope` no implementado | Media | Evaluar propagación por origen | ABIERTO — AD-56 |
| Gate de OC no implementado | Media | Evaluar gate y estado de cierre | ABIERTO |
| T29-T32 sin evidencia formal | Media | Evidenciar en `03_TESTS.md` | PENDIENTE |

---

## REGLA DE PRIORIZACIÓN

No abrir un frente mayor nuevo mientras existan bloqueos de instalación o pruebas pendientes sin evidenciar en `03_TESTS.md`. AD-65 es la excepción vigente, aprobada en sesión de diseño (2026-09-12); su prerequisito AD-64 debe resolverse antes de iniciar su implementación.

---

## INVESTIGACIÓN FUTURA (no aprobada)

- [ ] Evaluar unificación de Bruta y Procesado en un único flujo de ingesta con staging común. Fuera de alcance actual (AD-ING-001/AD-ING-002 no la habilitan). AD-63 confirma que el escenario "granel sin detalle" requiere modelado nuevo.

---

## Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 6.3.0 | 2026-06-16 | Última versión previa. |
| 7.0.0 | 2026-09-15 | Reconstrucción completa contra los 5 documentos canónicos. Cierre de BT-01 a BT-04 y C1-C4 reflejado. Frente principal AD-65 incorporado con prerequisito AD-64. Deuda técnica AD-56, AD-63 y hallazgo `reception_id` incorporados. Fase 7 deslindada de módulos ya implementados. |
