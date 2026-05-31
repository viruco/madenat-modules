# MADENAT — Backlog Canónico

**Versión documental:** 6.1.0  
**Fecha de actualización:** 2026-05-23  
**Estado:** ACTIVO — Prioridad inmediata en reparación del feature largo/unidades

---

## FASE 0.5 — SANEAMIENTO CRÍTICO
- [x] Eliminación de campos duplicados
- [x] Consolidación de decoradores
- [x] Reparación de importaciones
- [x] Métodos base completados
- [x] Tabla centralizada de anchos
- [x] Servicio de recepción desacoplado
- [x] Validaciones de rango
- [x] Base T01–T14 consolidada

---

## FASE 1 — GATES Y BLINDAJE
- [x] Gate 0
- [x] Gate 1
- [x] Gate 2
- [x] Gate 3
- [x] Snapshot SHA-256
- [x] Write único en Gate 3

---

## FASE 2 — MULTIFORMATO Y TRIPLE CAPA
- [x] Dispatcher Standard / Blanks
- [x] Triple capa
- [x] Espejo documental
- [x] Regla de exportación por línea

---

## FASE 3 — FLUJO DE PACKING
- [x] Ruta documental → staging → bodega
- [x] Conciliación volumétrica
- [x] Propagación `package_no`
- [x] Picking controlado

---

## FASE 4 — REFACTOR MODULAR
- [x] Parser extraído
- [x] Workflow extraído
- [x] Servicio stock extraído
- [x] Helpers/mixins extraídos
- [ ] Separación final de `LumberReceptionLine` a archivo propio

---

## FASE 5 — CALIDAD Y ESTABILIDAD
- [x] Matriz T01–T14 consolidada
- [x] Saneamiento documental T15–T28
- [ ] Formalizar tolerancias por tipo de madera
- [ ] Limpiar warnings XML
- [ ] Resolver constraint `stock_lot_check_cost_positive`

---

## FASE 5.1 — LARGO Y UNIDADES
**Nueva prioridad operativa inmediata**

### Objetivo
Cerrar correctamente el feature de ingreso de largo con unidad seleccionable sin romper instalación.

### Tareas
- [ ] Localizar todas las referencias a `lengthinputraw`
- [ ] Sustituir por `length_input_raw` donde corresponda
- [ ] Revisar referencias a `lengthuom` / `length_uom`
- [ ] Alinear compute `_compute_lengthm`
- [ ] Reinstalar / actualizar módulo sin error de registry
- [ ] Ejecutar T29 ft→m
- [ ] Ejecutar T30 mm→m
- [ ] Ejecutar T31 m→m
- [ ] Ejecutar T32 quick-create subproducto
- [ ] Actualizar continuidad y checklist final tras validación real

### Criterio de cierre
La fase solo cierra cuando el módulo instala correctamente y T29–T32 quedan evidenciados.

---

## FASE 6 — INTEGRACIÓN FINANCIERA
**Frente ya iniciado, pero subordinado al cierre de Fase 5.1**

### Objetivo
Conectar `shipment -> consolidation` mediante acción manual y validar el flujo financiero extremo a extremo.

### Estado actual
- [x] Modelo `lumber.billing.consolidation.line` existe
- [x] Relación con `stock.lot` existe
- [x] Acción manual `action_create_consolidation_from_shipment` implementada
- [x] Botón visible en shipment cuando `state = delivered`
- [x] Upgrade limpio de `madenat_lumber_billing`
- [x] Upgrade limpio de `madenat_lumber_logistics`
- [ ] Validación funcional extremo a extremo en UI
- [ ] Confirmar creación real de consolidación y líneas
- [ ] Definir cobertura de tests para este flujo
- [ ] Revisar si `base_automation` seguirá siendo requerido o solo legado de compatibilidad
- [ ] Reporting financiero por guía/shipment

---

## RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
|---|---|---|---|
| Bug `@depends` largo | Crítica | corregir naming y computes | ABIERTO |
| Constraint costo positivo | Alta | revisar data/modelo | ABIERTO |
| Fase 6 parcialmente validada | Media | probar flujo real y tests | ABIERTO |
| Monolito parcial | Media | refactor futuro | ABIERTO |
| Tolerancias no formalizadas | Media | parametrizar | ABIERTO |

---

## REGLA DE PRIORIZACIÓN

No abrir un frente mayor nuevo mientras:
- el módulo no instale limpio,
- el feature de largo/unidades siga roto,
- o T29–T32 no estén validados.
