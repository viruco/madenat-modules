# MADENAT — Backlog Canónico

**Versión documental:** 6.3.0  
**Fecha de actualización:** 2026-05-23  
**Estado:** ACTIVO — Prioridad inmediata en estabilización documental y validación funcional de Fase 6

---

## Regla de uso

Este backlog solo debe contener trabajo pendiente, prioridades activas y criterios de cierre.  
Si un tema ya quedó fijado como regla, debe vivir en `04_DECISION_LOG.md`.  
Si un tema ya quedó validado como estado, debe vivir en `02_CONTINUIDAD.md`.  
Si un tema ya quedó evidenciado, debe vivir en `03_TESTS.md`.

---

*(Nota: Las Fases 0.5 a 3 se encuentran 100% completadas y su estado está documentado en `02_CONTINUIDAD.md`)*

---

## FASE 4 — REFACTOR MODULAR

- [ ] Separación final de `LumberReceptionLine` a archivo propio.

### Criterio de salida
Cerrar este punto solo si el refactor final no rompe instalación, pruebas ni continuidad.

---

## FASE 5 — CALIDAD Y ESTABILIDAD

- [ ] Formalizar tolerancias por tipo de madera.
- [ ] Limpiar warnings XML.
- [ ] Resolver constraint `stock_lot_check_cost_positive`.

### Criterio de salida
No avanzar a consolidaciones mayores mientras la base técnica siga generando riesgos de instalación o validación.

---

*(Nota: Las validaciones operativas pendientes de las Fases 5.1 y 6 pertenecen estrictamente a `03_TESTS.md` y su estado se consolida en `02_CONTINUIDAD.md`)*

---

## Observaciones Cristhian — 08-06-2026

| ID | Descripción | Estado | Bloqueo |
|----|-------------|--------|---------|
| C1 | Renombrar menú raíz "Ingreso de Guías Dentro de Recepción" | ✅ Cerrado — commit 2e0c7ca | — |
| C2 | Labels operativos tipo producto (Aserrada/Blank) visibles en Recepción | ⏳ Pendiente | — |
| C3 | Volúmenes Blank: confirmar deduction_factor 0.0625 vs 0.0 | 🔒 Bloqueado | Cristhian confirma regla negocio |
| C4 | Restricción documental Packing/Guía obligatorio por tipo producto | ⏳ Pendiente | Cristhian confirma regla |

**Estimado post-desbloqueo:**
- C2: 2 horas
- C3: 30 minutos (solo ajuste seed si aplica)
- C4: 4 horas

---

## FASE 7 — INTEGRACIÓN CONTABLE (Visión a largo plazo)

### Objetivo
Extender la madurez operativa hacia los módulos contables de Odoo.

### Tareas (Futuras)
- [ ] Diseño e implementación de integración contable hacia `account.move`.

---

## PRÓXIMAS TAREAS

1. Diseño conceptual de integración contable (FASE 7).
2. Parametrización de tolerancias (FASE 5).

---

## RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
|---|---|---|---|
| Constraint costo positivo | Alta | revisar data/modelo | ABIERTO |
| Monolito parcial | Media | refactor futuro | ABIERTO |
| Tolerancias no formalizadas | Media | parametrizar | ABIERTO |

---

## REGLA DE PRIORIZACIÓN

No abrir un frente mayor nuevo (Fase 7) mientras existan bloqueos de instalación, o pruebas pendientes sin evidenciar en la matriz canónica `03_TESTS.md`.