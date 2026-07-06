# PLAN DE DEPURACIÓN PRIORIZADO — MADENAT Lumber
## Reporte de Valorización Exportadora
### Convertido desde Matriz de Cumplimiento Funcional + Evidencia Consolidada de Auditorías

**Fecha:** 2026-06-05
**Base de evidencia:** 7 auditorías (2026-06-03 a 2026-06-05), CANON/08_COSTEO, CANON/10_AUDITORIA_MONETARIA_FASE_A, CANON/11_FASE_E_VALIDACION, runtime diag
**Fase A monetaria:** ✅ COMPLETADA (17 campos Monetary migrados)
**Entorno:** DEV (madenat_test)

---

# 1. RESUMEN EJECUTIVO

## 1.1 Cobertura funcional estimada del reporte de valorización exportadora

| Bloque funcional | Cobertura | Estado |
|------------------|-----------|--------|
| Dimensiones y volúmenes (físico/export) | ~85% | Parcial — datos existen en lotes, cálculo de volumen de embarque incompleto |
| Costo base (wood_cost_usd) | ~10% | No asignado en runtime (0.00 en todos los lotes) |
| Costos adicionales (landed costs) | ~30% | Código implementado, no ejecutado en runtime (0 stock.lot.cost.line) |
| Trazabilidad operacional | ~75% | Lotes ↔ recepción ↔ picking correcto; booking↔distribución roto |
| Integración contable (stock.landed.cost → account.move) | ~5% | Código puente existe, nunca disparado en runtime |
| Totales y KPIs del reporte | ~20% | Dependen de costos no asignados |
| **Cobertura global ponderada** | **~35%** | El sistema puede generar estructura del reporte (columnas dimensionales) pero no valores monetarios ni totales |

## 1.2 Brechas críticas (bloquean el informe)

| # | Brecha | Impacto |
|---|--------|---------|
| B1 | `wood_cost_usd = 0` en todos los lotes | Sin costo base, el reporte no tiene valores monetarios |
| B2 | `booking_id = NULL` en distribución CD-2026-0002 | Sin booking, el onchange no carga lotes → distribución no aplica |
| B3 | `action_apply_costs()` nunca ejecutado exitosamente | Sin cost_line_ids inyectados, el costo total de cada lote está incompleto |
| B4 | `_generate_landed_costs()` nunca disparado | Sin stock.landed.cost, sin button_validate, sin account.move |
| B5 | `total_cost_usd` es `store=False` | No persiste — impide reportes históricos y auditoría |
| B6 | `cost_per_m3_usd` excluía `wood_cost_usd` | ✅ CORREGIDO en Fase A — usa `total_cost_usd` ahora |

## 1.3 Bloque del sistema más débil

**Puente Costeo → Contabilidad** (Tramo 4-6 del flujo end-to-end). El código está implementado y los tests unitarios pasan (23 tests), pero en runtime real nunca se ha ejecutado el flujo completo: `lumber.cost.distribution (applied) → stock.lot.cost.line → stock.landed.cost → account.move`.

## 1.4 ¿Puede el sistema generar una versión parcial del informe?

**Sí** — una versión estructural con columnas dimensionales (nombre lote, especie, dimensiones, volumen_m3, vol_shipment_m3, piezas, subproducto, trazabilidad). Pero **no** puede generar columnas monetarias (costo base USD, costo total USD, costo por m³, costo por MBF, margen) porque `wood_cost_usd = 0` en runtime y `total_cost_usd` no persiste.

---

# 2. PLAN DE DEPURACIÓN PRIORIZADO

## 2.1 Prioridad 1 — BLOQUEANTES: impiden la generación del informe o destruyen trazabilidad crítica

| Prioridad | Brecha | Columna del informe afectada | Modelo MADENAT afectado | Tipo de problema | Impacto funcional | Dependencias | Esfuerzo est. | Acción técnica recomendada | Estado objetivo |
|-----------|--------|------------------------------|-------------------------|-------------------|-------------------|-------------|---------------|----------------------------|-----------------|
| **P1** | `wood_cost_usd = 0` en todos los lotes | Costo Base Madera (USD), Costo Total (USD), Costo/m³, Costo/MBF | `stock.lot` | Dato maestro faltante | **Crítico**: sin costo base no hay valorización posible. El reporte no puede mostrar ninguna columna monetaria | Ninguna (es dato de entrada) | 1h | Asignar `wood_cost_usd > 0` a lotes con `reception_id.picking_id`. Usar wizard de actualización masiva o script SQL. **Requiere decisión funcional**: ¿el costo base viene de la OC, de la guía de despacho, o se ingresa manual? | `wood_cost_usd > 0` en ≥ 1 lote con picking y booking |
| **P1** | `booking_id = NULL` en distribución | Todas las columnas de costos adicionales | `lumber.cost.distribution` | Relación rota | **Crítico**: sin booking, el onchange no puede encontrar contenedores ni lotes. La distribución no puede aplicar | Requiere booking real con contenedores y lotes asignados | 2h | Asignar `booking_id` a CD-2026-0002 (o crear nueva distribución con booking real que tenga contenedores con lotes en `en_patio`). Verificar que el booking tenga `container_ids` con `lot_ids` poblados | `booking_id` apunta a booking con ≥ 1 contenedor con lotes |
| **P1** | `action_apply_costs()` nunca ejecutado | Costo Flete, Costo Puerto, Costo Seguro, Costo Total | `lumber.cost.distribution` → `stock.lot.cost.line` | Flujo no ejecutado | **Crítico**: sin cost_line_ids, el `total_cost_usd` de cada lote solo contiene `wood_cost_usd`. Los costos adicionales (flete, puerto, seguro) no se reflejan | Depende de B1 (wood_cost_usd) y B2 (booking_id) | 1h | Tras resolver B1 y B2, ejecutar `action_apply_costs()` y verificar: (a) crea `stock.lot.cost.line` con `amount_usd > 0`, (b) `cost_type` asignado, (c) `distribution_id` trazable | CD en estado `applied`, ≥ 1 `stock.lot.cost.line` creado por lote |
| **P1** | `_generate_landed_costs()` nunca disparado | Integración contable (todas las columnas monetarias) | `stock.landed.cost` (Odoo nativo + herencia MADENAT) | Puente no ejecutado | **Crítico**: sin `stock.landed.cost` no hay `button_validate`, sin `button_validate` no hay `account.move`. La valorización contable no existe | Depende de B3 (action_apply_costs). Requiere que el lote tenga `reception_id.picking_id` | 2h | Verificar que `_generate_landed_costs()` se dispara como side-effect de `action_apply_costs()`. Validar que crea `stock.landed.cost` con `madenat_distribution_id` y `picking_ids` poblados. Si el lote no tiene `reception_id.picking_id`, documentar como limitación de diseño (C3.2) | ≥ 1 `stock.landed.cost` con `madenat_distribution_id` y `state='draft'` |
| **P1** | `button_validate` nunca ejecutado sobre landed cost | Asiento contable (todas las columnas monetarias) | `stock.landed.cost` → `account.move` | Paso manual no ejecutado | **Crítico**: último eslabón del flujo. Sin esto, el sistema nunca generó contabilidad real desde MADENAT | Depende de B4 (landed cost creado) | 1h | Ejecutar `button_validate()` sobre el `stock.landed.cost` generado. Verificar: (a) `account.move` en estado `posted`, (b) `stock.valuation.layer` vinculado al landed cost, (c) Debe/Haber balanceado | ≥ 1 `account.move` en estado `posted` desde landed cost, ≥ 1 `stock.valuation.layer` con `stock_landed_cost_id` |
| **P1** | `total_cost_usd` es `store=False` | Costo Total (USD) en reportes históricos | `stock.lot` | Campo no persistente | **Crítico**: el campo se calcula on-the-fly pero no se guarda. Cualquier reporte histórico, exportación o auditoría lee 0 o valor stale. La constraint `stock_lot_check_cost_positive` es inefectiva | Ninguna | 3h | Cambiar `total_cost_usd` a `store=True`. Agregar `@api.depends('wood_cost_usd', 'cost_line_ids.amount_usd')` correcto (ya existe). **Riesgo**: migración de datos para lotes existentes requiere script de backfill | `total_cost_usd` persiste en BD y se recalcula automáticamente |

## 2.2 Prioridad 2 — CAMPOS OBLIGATORIOS Y CÁLCULOS CLAVE

| Prioridad | Brecha | Columna del informe afectada | Modelo MADENAT afectado | Tipo de problema | Impacto funcional | Dependencias | Esfuerzo est. | Acción técnica recomendada | Estado objetivo |
|-----------|--------|------------------------------|-------------------------|-------------------|-------------------|-------------|---------------|----------------------------|-----------------|
| **P2** | `stock.lot.cost.line` sin `account_id` | Cuenta contable en asiento | `stock.lot.cost.line` | Campo opcional faltante | **Alto**: Odoo usará fallback de la cuenta del producto, lo cual puede ser incorrecto para ciertos costos (flete vs seguro vs puerto). La imputación contable será genérica | Ninguna | 2h | Agregar `account_id` (Many2one → `account.account`) opcional a `stock.lot.cost.line`. Exponer en vistas de línea de costo. Documentar que si no se asigna, Odoo usa `property_stock_account_input` del producto | `account_id` disponible en UI de línea de costo |
| **P2** | `_deprecated_action_distribute_costs` bypassea `cost_line_ids` | Costo Logístico en reporte | `lumber_shipment_costing.py` en `madenat_lumber_logistics` | Escritura directa al lote | **Alto**: los costos logísticos del embarque se escriben directo a `stock.lot` (campo `logistic_cost_usd`) sin pasar por `stock.lot.cost.line`. Rompe la trazabilidad de fuente única de verdad | Depende de P1 (cost_line_ids funcional) | 3h | Refactorizar `_deprecated_action_distribute_costs` para crear `stock.lot.cost.line` con `cost_type='logistic'` en lugar de escribir directo a `stock.lot.logistic_cost_usd`. Mantener el campo `logistic_cost_usd` como compute desde `cost_line_ids` filtrado por tipo | Costos logísticos trazables vía `cost_line_ids` |
| **P2** | `vol_shipment_m3` cálculo dependiente de `lumber_shipment_line` | Volumen Embarque (m³) | `stock.lot`, `lumber_shipment_line` | Cálculo parcial | **Alto**: el volumen de embarque es clave para valorización exportadora y prorrateo de costos logísticos. Si no está calculado correctamente, el costo por m³ exportado será incorrecto | Requiere que el lote esté asignado a un `lumber.shipment.line` con dimensiones de embarque | 4h | Verificar pipeline completo: `stock.lot` → `lumber.container` → `lumber.shipment.line` → `vol_shipment_m3`. Validar que `_compute_vol_shipment_m3` en `lumber_shipment_line.py` se dispara correctamente y propaga al lote | `vol_shipment_m3 > 0` en lotes asignados a embarque |
| **P2** | `cost_per_m3_usd` y `cost_per_mbf_usd` — bug corregido en Fase A pero sin validación runtime | Costo/m³, Costo/MBF | `stock.lot` | Bug corregido, no verificado | **Alto**: la Fase A corrigió el cálculo (ahora usa `total_cost_usd` en vez de solo `cost_line_ids`), pero sin `wood_cost_usd > 0` en runtime, la corrección no puede validarse con datos reales | Depende de P1 (wood_cost_usd > 0) | 1h | Tras asignar `wood_cost_usd > 0`, verificar que `cost_per_m3_usd = total_cost_usd / volumen_m3` y `cost_per_mbf_usd = total_cost_usd / volumen_mbf`. Validar con ≥ 3 lotes de distintos volúmenes | Cálculo verificado con datos reales |
| **P2** | `lumber_export_formula` — seed data sin perfiles activos | Columnas de fórmula y factor | `lumber.export.formula` | Configuración no desplegada | **Alto**: el motor de cálculo de `_compute_export_values` depende de registros en `lumber.export.formula`. Si no hay perfiles activos, usa fallback de `utils_uom`. El reporte de valorización exportadora debe indicar qué fórmula se aplicó | Ninguna | 1h | Verificar que `ingestion_seed_fase3.xml` cargó los 3 perfiles (f5085, f1550, metric) con `active=True`. Si no, cargar manualmente. Agregar columna `formula_aplicada` al reporte | 3 registros activos en `lumber.export.formula` |

## 2.3 Prioridad 3 — CALIDAD DE DATOS, NORMALIZACIÓN Y ENRIQUECIMIENTO

| Prioridad | Brecha | Columna del informe afectada | Modelo MADENAT afectado | Tipo de problema | Impacto funcional | Dependencias | Esfuerzo est. | Acción técnica recomendada | Estado objetivo |
|-----------|--------|------------------------------|-------------------------|-------------------|-------------------|-------------|---------------|----------------------------|-----------------|
| **P3** | `purchase_cost_usd` es código muerto (deprecado en Fase A) | Costo Compra (legacy) | `stock.lot` | Campo redundante | **Medio**: dos campos para el mismo concepto genera confusión en el reporte. ¿Cuál mostrar? La Fase A deprecó `purchase_cost_usd` pero el campo sigue existiendo | Ninguna | 0.5h | Eliminar `purchase_cost_usd` de vistas del reporte. En el reporte, mostrar solo `wood_cost_usd`. Si el reporte legacy usaba `purchase_cost_usd`, migrar a `wood_cost_usd` | Reporte muestra solo `wood_cost_usd` |
| **P3** | `_compute_total_cost_usd` override en costing con posible doble conteo | Costo Total (USD) | `stock_lot_costing.py` en `madenat_lumber_costing` | Posible bug de doble suma | **Medio**: si `logistic_cost_usd` ya está en `cost_line_ids`, el override que suma `logistic_cost_usd` al total del core causaría doble conteo | Depende de P2 (refactor logistics) | 2h | Auditar `_compute_total_cost_usd` en `stock_lot_costing.py`. Verificar si `logistic_cost_usd` es un compute desde `cost_line_ids` (post-refactor P2) o un campo independiente. Si es independiente, mantener la suma. Si es compute, eliminar el override | Sin doble conteo verificado |
| **P3** | `wood_cost_usd` y `purchase_amount_usd` miden lo mismo | Costo Base vs Costo Compra Derivado | `stock.lot` | Dos campos para mismo concepto | **Medio**: `purchase_amount_usd = volumen_m3 × purchase_price_usd_per_m3` (derivado) vs `wood_cost_usd` (manual). Fuente de verdad ambigua para el reporte | Requiere **decisión funcional** | 1h | Decidir cuál es fuente de verdad para el reporte: (a) `wood_cost_usd` como valor manual/asignado, (b) `purchase_amount_usd` como derivado del precio. Documentar en CANON/08_COSTEO. Recomendación técnica: `wood_cost_usd` como fuente de verdad, `purchase_amount_usd` como informativo | Decisión documentada en CANON |
| **P3** | `madenat_vendor_payment` — modelo placeholder sin implementación | No aplica directamente al reporte de valorización | `vendor.payment.order` | Módulo incompleto | **Medio**: no afecta la generación del reporte pero impide la trazabilidad completa del ciclo compra→pago. Impacta auditoría financiera futura | Ninguna | 8h | Completar modelo `vendor.payment.order` con campos de monto, moneda, estado y vinculación a `purchase.order` o `lumber.reception`. Fuera del scope inmediato del reporte | Módulo funcional con README |

## 2.4 Prioridad 4 — MEJORAS OPCIONALES O DE PRESENTACIÓN

| Prioridad | Brecha | Columna del informe afectada | Modelo MADENAT afectado | Tipo de problema | Impacto funcional | Dependencias | Esfuerzo est. | Acción técnica recomendada | Estado objetivo |
|-----------|--------|------------------------------|-------------------------|-------------------|-------------------|-------------|---------------|----------------------------|-----------------|
| **P4** | Hardcode `25.4` en `lumber_shipment_line.py` y `lumber_reception_mass_update.py` | No afecta directamente; riesgo de inconsistencia en conversiones imperiales | `lumber_shipment_line.py`, `lumber_reception_mass_update.py` | Hardcode no centralizado | **Bajo**: si `MM_PER_INCH` cambia en `utils_uom.py`, estos hardcodes quedan desincronizados | Ninguna | 1h | Reemplazar `25.4` por `MM_PER_INCH` importado desde `utils_uom.py` | Cero hardcodes de conversión imperial fuera de `utils_uom.py` |
| **P4** | `mm_to_inch()` en `utils_uom.py` usa literal `25.4` en lugar de `MM_PER_INCH` | No afecta directamente | `utils_uom.py` | Hardcode en propio archivo de constantes | **Bajo**: la función de conversión en el archivo canónico de constantes usa el literal en vez de la constante | Ninguna | 0.5h | Cambiar `float(decimal_value) * 25.4` → `float(decimal_value) * float(MM_PER_INCH)` | `mm_to_inch()` usa `MM_PER_INCH` |
| **P4** | CERO tests para `madenat_guia_processing` (3465 líneas) | No afecta directamente; riesgo de regresión | `madenat_guia_processing.py` | Sin cobertura de tests | **Bajo** para el reporte inmediato, **Alto** para estabilidad del sistema | Ninguna | 12h | Crear `test_guia_processing.py` con casos: creación, flujo estados, staging→lotes, validación picking, cancelación, cálculo volúmenes | Test suite con ≥ 12 casos |
| **P4** | `lumber_export_formula` — añadir columna de fórmula al reporte | Fórmula aplicada | `lumber.export.formula` | Trazabilidad de cálculo | **Bajo**: el reporte no indica qué fórmula (f5085/f1550/metric) se usó para cada lote. Dificulta auditoría | Ninguna | 1h | Agregar `formula_aplicada` como columna en el reporte, resolviendo desde `lumber.export.formula._resolve_for_profile()` o desde el `subproducto_id.profile` del lote | Reporte muestra fórmula aplicada por línea |
| **P4** | `total_cost_usd` no se muestra en vistas de lote (UI) | No afecta; usabilidad | `stock.lot` views | Campo no visible | **Bajo**: el operador no puede ver el costo total del lote en la UI estándar | Ninguna | 0.5h | Agregar `total_cost_usd` al tree y form view de `stock.lot` (si no está ya). Usar `widget='monetary'` | `total_cost_usd` visible en UI de lote |

---

# 3. SECUENCIA DE IMPLEMENTACIÓN

## 3.1 Orden exacto de trabajo

### Fase 1 — Desbloqueo del flujo runtime (P1, ~7h)
**Objetivo:** Lograr que el flujo end-to-end se ejecute al menos una vez con datos reales.

| Orden | Tarea | Prioridad | Horas | ¿Por qué primero? |
|-------|-------|-----------|-------|-------------------|
| 1.1 | Asignar `wood_cost_usd > 0` a lotes con picking | P1 | 1h | Es el dato más básico. Sin costo base, nada tiene sentido. **Requiere decisión funcional previa** sobre el origen del dato |
| 1.2 | Asignar `booking_id` real a distribución (o crear nueva) | P1 | 2h | Desbloquea el onchange que carga lotes y contenedores. Sin esto, `action_apply_costs()` no puede ejecutarse correctamente |
| 1.3 | Ejecutar `action_apply_costs()` y verificar `stock.lot.cost.line` | P1 | 1h | Inyecta costos adicionales en los lotes. Depende de 1.1 y 1.2 |
| 1.4 | Verificar `_generate_landed_costs()` → `stock.landed.cost` creado | P1 | 2h | Si el lote tiene `reception_id.picking_id`, este paso es automático. Si no, requiere diagnóstico y posible fix |
| 1.5 | Ejecutar `button_validate()` → verificar `account.move` + `stock.valuation.layer` | P1 | 1h | Último eslabón. Solo tiene sentido tras 1.4 |

### Fase 2 — Persistencia y cálculos clave (P1+P2, ~12h)
**Objetivo:** Asegurar que los datos persisten y los cálculos son correctos.

| Orden | Tarea | Prioridad | Horas | ¿Por qué? |
|-------|-------|-----------|-------|-----------|
| 2.1 | Cambiar `total_cost_usd` a `store=True` + backfill | P1 | 3h | Imprescindible para reportes históricos. Sin store, cualquier reporte lee 0 |
| 2.2 | Agregar `account_id` a `stock.lot.cost.line` | P2 | 2h | Requerido para imputación contable correcta |
| 2.3 | Refactorizar `_deprecated_action_distribute_costs` → `cost_line_ids` | P2 | 3h | Unifica trazabilidad de costos. Debe hacerse después de 2.1 para que `total_cost_usd` (store) refleje los cambios |
| 2.4 | Verificar pipeline `vol_shipment_m3` | P2 | 4h | Requiere datos de embarque reales. Puede hacerse en paralelo con 2.2 y 2.3 si hay datos disponibles |

### Fase 3 — Validación, normalización y calidad (P2+P3, ~5.5h)
**Objetivo:** Corregir bugs, eliminar ambigüedades, verificar correcciones.

| Orden | Tarea | Prioridad | Horas | ¿Por qué? |
|-------|-------|-----------|-------|-----------|
| 3.1 | Validar `cost_per_m3_usd` y `cost_per_mbf_usd` con datos reales | P2 | 1h | Solo tiene sentido tras Fase 1 (datos existen) y Fase 2 (total_cost_usd store) |
| 3.2 | Verificar seed data `lumber.export.formula` | P2 | 1h | Independiente, puede adelantarse |
| 3.3 | Auditar `_compute_total_cost_usd` en costing (doble conteo) | P3 | 2h | Requiere que 2.3 esté completado |
| 3.4 | Decidir fuente de verdad para costo base (funcional) | P3 | 1h | **Requiere decisión de negocio** — no es técnica |
| 3.5 | Eliminar `purchase_cost_usd` de vistas del reporte | P3 | 0.5h | Cosmético, tras 3.4 |

### Fase 4 — Mejoras y hardening (P4, ~15h)
**Objetivo:** Eliminar deuda técnica, mejorar trazabilidad, preparar para producción.

| Orden | Tarea | Prioridad | Horas | Notas |
|-------|-------|-----------|-------|-------|
| 4.1 | Reemplazar hardcodes `25.4` | P4 | 1.5h | Incluye `lumber_shipment_line.py`, `lumber_reception_mass_update.py`, `utils_uom.py:mm_to_inch()` |
| 4.2 | Agregar columna `formula_aplicada` al reporte | P4 | 1h | Mejora de trazabilidad |
| 4.3 | Agregar `total_cost_usd` a vistas de lote | P4 | 0.5h | Mejora de usabilidad |
| 4.4 | Crear test suite para `madenat_guia_processing` | P4 | 12h | Alta inversión, alto retorno en estabilidad. **PUEDE PARALELIZARSE** con Fases 1-3 |

### Tareas que pueden ejecutarse en paralelo

| Grupo A (depende de datos) | Grupo B (independiente) |
|---------------------------|------------------------|
| Fase 1 completa | 3.2 — Verificar seed data `lumber.export.formula` |
| Fase 2: 2.1, 2.2, 2.3 | 4.1 — Hardcodes `25.4` |
| Fase 3: 3.1, 3.3, 3.5 | 4.2 — Columna `formula_aplicada` |
| | 4.3 — `total_cost_usd` en UI |
| | 4.4 — Tests `madenat_guia_processing` (requiere developer independiente) |

---

# 4. RIESGOS DE IMPLEMENTACIÓN

## 4.1 Riesgos funcionales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| **Origen de `wood_cost_usd` no definido** | ALTA | ALTO — sin definición funcional, el equipo técnico no sabe de dónde tomar el dato | **Pre-requisito**: antes de iniciar Fase 1, el negocio debe definir si `wood_cost_usd` viene de la OC (`price_unit`), de la guía de despacho (PDF parseado), o es ingreso manual. Documentar en CANON/08_COSTEO |
| **Lotes sin `reception_id.picking_id`** | MEDIA | ALTO — `_generate_landed_costs()` requiere picking en el lote. Si el lote se creó por guía de procesamiento (`guia_processing_id`) o manualmente, no tendrá picking y no se generará `stock.landed.cost` | Documentado como limitación aceptada (C3.2). Si es un problema real, extender `_generate_landed_costs()` para buscar el picking por otras vías |
| **`button_validate` sobre `stock.landed.cost` requiere configuración contable previa** | MEDIA | ALTO — Odoo necesita cuentas contables configuradas en producto, categoría, y diario. Si faltan, `button_validate` fallará | Antes de 1.5, verificar: `product.property_stock_account_input`, `product.categ_id.property_stock_account_input`, `stock.landed.cost` con `account_journal_id` |
| **Divergencia entre `wood_cost_usd` y `purchase_amount_usd`** | BAJA | MEDIO — si el operador asigna `wood_cost_usd` manualmente y difiere del cálculo derivado `purchase_amount_usd`, el reporte mostrará dos valores distintos para "costo base" | La decisión funcional en 3.4 debe resolver esto. Si se elige `wood_cost_usd` como fuente de verdad, `purchase_amount_usd` debe marcarse como informativo/estimado |

## 4.2 Riesgos de integridad de datos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| **Migración `total_cost_usd` a `store=True`** | BAJA | ALTO — si el script de backfill falla o se interrumpe, lotes existentes quedarán con `total_cost_usd = 0` o null | Ejecutar backfill en transacción con savepoint. Validar con `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NULL OR total_cost_usd = 0` post-migración |
| **Refactor `_deprecated_action_distribute_costs`** | MEDIA | MEDIO — si la migración a `cost_line_ids` no limpia los valores legacy en `logistic_cost_usd`, habrá doble contabilización | Script de limpieza: poner `logistic_cost_usd = 0` en lotes donde se migró a `cost_line_ids`. Agregar constraint que `logistic_cost_usd` solo se compute desde `cost_line_ids` |
| **Constraint `stock_lot_check_cost_positive`** | BAJA | BAJO — actualmente es inefectiva porque `total_cost_usd` es no-store. Tras migrar a store, la constraint se activará y podría bloquear lotes legacy con costo cero | Relajar constraint a `>= 0` en lugar de `> 0`, o aplicarla solo a lotes en estado `recepcionado` o posterior |

## 4.3 Riesgos de compatibilidad con flujo ya validado

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| **Cambios en `stock.lot` afectan tests existentes (23 tests)** | MEDIA | MEDIO — si `total_cost_usd` store=True cambia comportamiento de tests que asumían no-store | Ejecutar suite completa de tests (`test_lot_costing`, `test_cost_distribution`, `test_landed_cost_integration`, `test_module_compatibility`) después de cada cambio en Fase 2 |
| **Refactor de logistics (`cost_line_ids`) rompe `madenat_lumber_billing`** | BAJA | MEDIO — billing lee costos de lotes. Si la fuente de verdad cambia, billing debe adaptarse | Billing ya usa Monetary y lee `wood_cost_usd` + `total_cost_usd`. Si `logistic_cost_usd` se mueve a `cost_line_ids`, verificar que `total_cost_usd` lo refleje (ya lo hace vía `_compute_total_cost_usd`) |
| **Módulo `madenat_vendor_payment` placeholder** | ALTA | BAJO — es un modelo vacío que no afecta el flujo. Pero si se intenta usar en runtime, fallará | No incluir en scope del reporte de valorización. Marcar como fuera de alcance hasta que el módulo se complete |

---

# 5. CRITERIOS DE CIERRE

## 5.1 Criterios por brecha

| Brecha | Criterio de cierre | Prueba runtime o reporte a ejecutar | Evidencia a registrar |
|--------|-------------------|--------------------------------------|-----------------------|
| **P1 — wood_cost_usd** | ≥ 1 lote con `wood_cost_usd > 0`, `reception_id.picking_id` no nulo, `booking_id` asignado vía contenedor | `SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0 AND reception_id IS NOT NULL` | Screenshot del lote en UI mostrando `wood_cost_usd` > 0 |
| **P1 — booking_id** | `booking_id` en CD apunta a booking con ≥ 1 contenedor con lotes en estado `en_patio` o `recepcionado` | `SELECT booking_id, state FROM lumber_cost_distribution WHERE name='CD-2026-0002'` | Screenshot de la distribución mostrando booking asignado y lotes cargados |
| **P1 — action_apply_costs** | CD en estado `applied`, ≥ 1 `stock.lot.cost.line` por lote con `amount_usd > 0` y `cost_type` asignado | `SELECT count(*) FROM stock_lot_cost_line WHERE amount_usd > 0` | Screenshot de `cost_line_ids` en el lote |
| **P1 — _generate_landed_costs** | ≥ 1 `stock.landed.cost` con `madenat_distribution_id` = CD-2026-0002, `state='draft'`, `picking_ids` poblado | `SELECT id, state, madenat_distribution_id FROM stock_landed_cost` | Screenshot del landed cost en UI |
| **P1 — button_validate** | ≥ 1 `account.move` en estado `posted` con origen `stock.landed.cost`, ≥ 1 `stock.valuation.layer` con `stock_landed_cost_id` | `SELECT count(*) FROM account_move am JOIN stock_landed_cost slc ON am.stock_landed_cost_id = slc.id WHERE am.state='posted'` | Screenshot del `account.move` (asiento contable) y `stock.valuation.layer` |
| **P1 — total_cost_usd store** | `total_cost_usd` persiste en BD, se recalcula on-write de `wood_cost_usd` o `cost_line_ids`, backfill ejecutado sin errores | `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NOT NULL AND total_cost_usd > 0` | Log del script de backfill + query de verificación |
| **P2 — account_id en cost_line** | Campo `account_id` visible en UI de `stock.lot.cost.line`, funcional en vista formulario | Crear una línea de costo con `account_id` asignado y verificar en BD | Screenshot de la vista con el campo |
| **P2 — refactor logistics** | `_deprecated_action_distribute_costs` eliminado o redirigido. Costos logísticos visibles en `cost_line_ids` con `cost_type='logistic'` | `SELECT count(*) FROM stock_lot_cost_line WHERE cost_type='logistic'` | Screenshot mostrando `cost_line_ids` con tipo logistic |
| **P2 — vol_shipment_m3** | Lotes en embarque tienen `vol_shipment_m3 > 0` y coincide con el cálculo de `lumber_shipment_line` | `SELECT count(*) FROM stock_lot WHERE vol_shipment_m3 > 0` | Pantalla de lote mostrando `vol_shipment_m3` |
| **P2 — validación cost_per_m3/mbf** | ≥ 3 lotes con `cost_per_m3_usd = total_cost_usd / volumen_m3` (margen error ≤ 0.01) | Script de validación comparando compute vs manual | Log del script con resultados |
| **P2 — seed export formula** | 3 registros activos en `lumber.export.formula` (f5085, f1550, metric) con `active=True` | `SELECT profile, active FROM lumber_export_formula` | Screenshot del tree view |
| **P3 — eliminación purchase_cost_usd del reporte** | Reporte no muestra `purchase_cost_usd`, solo `wood_cost_usd` | Generar reporte y verificar columnas | PDF del reporte generado |
| **P3 — doble conteo** | `total_cost_usd` = `wood_cost_usd` + `sum(cost_line_ids)` sin duplicación de `logistic_cost_usd` | Test unitario con lote que tiene `wood_cost_usd=100` + 2 cost_lines (50+30). Verificar `total_cost_usd=180` | Output del test |
| **P3 — fuente de verdad costo base** | Decisión documentada en CANON/08_COSTEO §1.2 | N/A (documental) | Commit con la actualización de CANON/08_COSTEO.md |

## 5.2 Criterios de cierre globales del plan

1. **Flujo end-to-end ejecutado**: recepción → lote con `wood_cost_usd > 0` → CD `applied` → `stock.lot.cost.line` creado → `stock.landed.cost` generado → `button_validate` → `account.move` posted → `stock.valuation.layer` creado
2. **Reporte de valorización exportadora generado**: al menos 1 lote con todas las columnas monetarias pobladas (costo base, costos adicionales, costo total, costo/m³, costo/MBF)
3. **Suite de tests pasando**: 23 tests existentes + tests de regresión para los cambios de Fase 2
4. **Documentación actualizada**: CANON/08_COSTEO con decisión de fuente de verdad, CHANGELOG de módulos afectados
5. **Sin regresiones en runtime**: el flujo de recepción de madera bruta y guías de procesamiento sigue funcionando

## 5.3 Métricas de éxito

| Métrica | Valor actual | Valor objetivo |
|---------|-------------|----------------|
| Lotes con `wood_cost_usd > 0` | 0 / 39 | ≥ 10 |
| `stock.lot.cost.line` creados | 0 | ≥ 1 por lote con costos adicionales |
| `stock.landed.cost` generados | 0 | ≥ 1 |
| `account.move` desde landed cost | 0 | ≥ 1 en estado `posted` |
| `stock.valuation.layer` desde landed cost | 0 | ≥ 1 |
| `total_cost_usd` persistido en BD | 0% (no-store) | 100% (store=True) |
| Cobertura de columnas monetarias en reporte | 0% | ≥ 80% |
| Tests pasando | 23/23 | 23/23 + nuevos tests sin regresión |

---

# 6. CONCLUSIÓN EJECUTIVA

## 6.1 ¿El sistema ya está listo para el reporte?

**NO.** El sistema puede generar la estructura del reporte (columnas dimensionales, trazabilidad de lotes, volúmenes), pero **no puede generar valores monetarios** porque:

- `wood_cost_usd = 0` en todos los lotes del entorno — el costo base de la madera nunca fue asignado
- El flujo de costeo adicional (`action_apply_costs`) nunca se ejecutó exitosamente en runtime
- El puente contable (`stock.landed.cost` → `account.move`) nunca se disparó
- `total_cost_usd` no persiste en base de datos (`store=False`)

El código está implementado, validado en tests unitarios, y la base monetaria fue saneada (Fase A completada). Pero **el sistema nunca fue operado con datos reales en este entorno.**

## 6.2 ¿Qué porcentaje falta para cobertura funcional completa?

| Estado | Cobertura |
|--------|-----------|
| Cobertura actual (columnas dimensionales y trazabilidad) | ~35% |
| Cobertura tras Fase 1 (flujo runtime desbloqueado) | ~65% |
| Cobertura tras Fase 2 (persistencia + cálculos corregidos) | ~85% |
| Cobertura tras Fase 3 (normalización y calidad) | ~92% |
| Cobertura tras Fase 4 (mejoras y hardening) | ~98% |

El 2% restante corresponde a: integración bancaria (`vendor_payment`), flujo de maquila, y validación con archivos físicos reales (PDF/Excel de proveedores).

## 6.3 Nivel de esfuerzo requerido

| Fase | Esfuerzo | Acumulado | Entregable principal |
|------|----------|-----------|----------------------|
| Fase 1 — Desbloqueo runtime | 7h | 7h | Flujo end-to-end ejecutado 1 vez |
| Fase 2 — Persistencia y cálculos | 12h | 19h | `total_cost_usd` store + refactor logistics |
| Fase 3 — Validación y calidad | 5.5h | 24.5h | Bugs corregidos, decisiones documentadas |
| Fase 4 — Mejoras y hardening | 15h | 39.5h | Cero hardcodes, tests, UI completa |
| **Total** | **39.5h** | — | **Sistema listo para reporte de valorización** |

**Conclusión:** Con ~40 horas de trabajo técnico priorizado, el sistema pasa de 35% a ~98% de cobertura funcional para el reporte de valorización exportadora. Las primeras 7 horas (Fase 1) son las de mayor impacto: desbloquean el flujo runtime y permiten generar una primera versión del informe con valores reales. La Fase 2 (12h) es donde se consolida la integridad de datos para que el reporte sea persistente y auditable. Las Fases 3 y 4 son de calidad y hardening.

**La Fase 1 puede iniciar inmediatamente**, con la salvedad de que la tarea 1.1 (`wood_cost_usd`) requiere una **decisión funcional previa** sobre el origen del dato de costo base.

---

*Plan generado: 2026-06-05 — basado en 7 auditorías (2026-06-03 a 2026-06-05), CANON/08_COSTEO, CANON/10_AUDITORIA_MONETARIA_FASE_A, CANON/11_FASE_E_VALIDACION, y diagnósticos runtime*
*Sin matriz de cumplimiento funcional columna-por-columna — las brechas fueron extraídas directamente de la evidencia documental y runtime*