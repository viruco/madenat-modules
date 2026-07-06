# CIERRE DF-01 — Guía de Reunión con Negocio
## Origen del costo base de madera (`wood_cost_usd`)

**Fecha:** 2026-06-05
**Duración estimada:** 30 minutos
**Participantes sugeridos:** Operaciones, Finanzas, Tech Lead
**Decisión requerida:** ¿De dónde se obtiene el valor de `wood_cost_usd` para cada lote?

---

# 1. OBJETIVO DE LA REUNIÓN

**Definir la fuente de dato para el costo base de madera (`wood_cost_usd`) que alimentará el reporte de valorización exportadora y todo el flujo contable.**

Decisión que debe salir cerrada: cuál de las 3 opciones (A, B o C) se adopta, o qué combinación.

**Qué desbloquea:** 6 acciones técnicas (~6h) que producen el primer asiento contable real desde MADENAT.

---

# 2. PROBLEMA A RESOLVER

## 2.1 En lenguaje funcional

Cada lote de madera que ingresa al sistema necesita un **costo base en dólares** (`wood_cost_usd`). Ese valor es el punto de partida de toda la cadena de valorización:

```
Costo base → + Flete → + Puerto → + Seguro → = Costo Total del lote
                                                      ↓
                                            Reporte de Valorización Exportadora
                                                      ↓
                                            Contabilidad (account.move)
```

Hoy, los 39 lotes del sistema tienen `wood_cost_usd = 0`. Sin ese dato, el reporte de valorización exportadora no puede mostrar ninguna columna monetaria.

## 2.2 Por qué es crítico

| Con `wood_cost_usd > 0` | Sin `wood_cost_usd` |
|--------------------------|---------------------|
| Reporte muestra costo base, costo total, costo/m³, costo/MBF, margen | Reporte solo muestra columnas dimensionales (nombre, especie, volumen) |
| El flujo contable llega hasta `account.move` (asiento contable) | El flujo se detiene antes de la contabilidad |
| La valorización exportadora es trazable y auditable | No hay valorización posible |

## 2.3 Riesgo de no decidir

- El equipo técnico no puede avanzar en el 31% de las acciones del plan.
- Cualquier valor que se asigne sin criterio de negocio será arbitrario y requerirá re-trabajo.
- El proyecto se detiene en el punto de mayor impacto funcional.

---

# 3. OPCIONES DE DECISIÓN

| | Opción A — Desde OC | Opción B — Desde guía PDF | Opción C — Manual |
|---|---|---|---|
| **Qué significa** | `wood_cost_usd = price_unit × volumen_m3`, tomado de la Orden de Compra | El sistema extrae el costo desde el PDF de la guía de despacho del proveedor | El operador ingresa manualmente el costo en cada lote |
| **Cuándo aplica** | Toda recepción tiene OC vinculada y el precio unitario refleja el costo real | Los PDFs de guía se adjuntan sistemáticamente y contienen el dato financiero | El costo varía por lote y no hay fuente automática confiable |
| **Impacto funcional** | Costo automático, sin intervención. Consistente con el precio de compra | Costo documental, trazable al documento físico del proveedor | Control total del valor. Puede diferir del precio de compra |
| **Impacto técnico** | Script de 1h. Usa `reception.order_id.order_line.price_unit` | Requiere verificar/implementar parseo del campo de costo en el PDF (~4h adicionales) | Usar wizard existente `lumber_reception_mass_update`. Sin desarrollo |
| **Riesgo** | Si la OC no refleja costos adicionales en origen, el costo base estará subestimado | Si el parser no extrae el dato correctamente, el costo será incorrecto | Depende de disciplina operativa. Riesgo de omisión o error de tipeo |
| **Evidencia para adoptarla** | Query: ¿cuántas recepciones tienen OC? ¿El `price_unit` es > 0? | ¿Los PDFs históricos contienen el dato de costo? ¿El parser actual lo extrae? | ¿Operaciones tiene capacidad y proceso para ingreso manual? |

## 3.1 Opción por defecto técnico (fallback controlado)

**Si el negocio no responde en 48h**, el equipo técnico adoptará la Opción A como default, documentándolo como temporal en CANON. Esto permite:

- Avanzar con la Fase 1 sin bloquear el proyecto.
- Generar el primer `account.move` con datos derivados de la OC.
- Reasignar `wood_cost_usd` posteriormente si el negocio elige otra fuente (~1-2h de re-trabajo).

---

# 4. PREGUNTAS CLAVE PARA NEGOCIO

| # | Pregunta | Prioridad |
|---|----------|-----------|
| 1 | ¿Toda recepción de madera tiene una Orden de Compra asociada? | **Alta** — define viabilidad de Opción A |
| 2 | ¿El precio unitario de la OC (`price_unit`) es el costo real de la madera o es un precio estimado/negociado que puede diferir? | **Alta** — define confiabilidad de Opción A |
| 3 | ¿El PDF de la guía de despacho del proveedor incluye el costo de la madera? | Media — define viabilidad de Opción B |
| 4 | ¿El operador que recibe la madera conoce el costo real de cada lote en el momento de la recepción? | Media — define viabilidad de Opción C |
| 5 | ¿El costo de la madera puede variar entre lotes de una misma recepción? | Media — si sí, Opción A no aplica a nivel lote |

---

# 5. CRITERIO DE DECISIÓN

## 5.1 Cómo decidir entre opciones

```
¿Toda recepción tiene OC con price_unit > 0?
  ├── SÍ → ¿El price_unit refleja el costo real?
  │         ├── SÍ → Opción A (automático desde OC)
  │         └── NO → ¿El PDF de guía contiene el costo?
  │                   ├── SÍ → Opción B (parseo de PDF)
  │                   └── NO → Opción C (manual)
  └── NO → ¿El PDF de guía contiene el costo?
            ├── SÍ → Opción B
            └── NO → Opción C
```

## 5.2 Criterio que manda si hay conflicto

Si dos fuentes existen pero difieren (ej: OC dice 620 USD, PDF dice 650 USD):

1. **Prevalece el PDF de guía de despacho** (documento del proveedor) como fuente primaria.
2. La OC se usa como referencia de conciliación.
3. El operador puede ajustar manualmente si ambas fuentes son inconsistentes.

## 5.3 Si negocio no responde a tiempo

Se adopta **Opción A como default técnico temporal**, documentado en CANON con vigencia de 2 semanas. Si en ese plazo el negocio define otra fuente, se reasigna.

---

# 6. PLANTILLA DE CIERRE

Copiar este bloque en `CANON/08_COSTEO.md` §1.2 y en `CANON/04_DECISION_LOG.md` una vez tomada la decisión:

```markdown
### DF-01 — Origen de wood_cost_usd (RESUELTO)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-XX |
| **Decisión adoptada** | [Opción A / B / C] |
| **Justificación** | [Razón principal en una frase] |
| **Responsable** | [Nombre y rol] |
| **Impacto sobre el plan** | Desbloquea Fase 1 (6 acciones, ~6h). El script A-02 usará [fuente] para poblar wood_cost_usd |
| **Acciones desbloqueadas** | A-02, A-03, A-04, A-05, A-06, A-07 |
| **Acciones que siguen bloqueadas** | Ninguna por DF-01. DF-02 (fuente de verdad en reporte) se resuelve en Fase 3 |
| **Excepciones** | [Si la Opción A no aplica a ciertas recepciones sin OC, indicar aquí el fallback] |
| **Revisión** | [Fecha de revisión si es default temporal] |
```

---

# 7. PRÓXIMOS PASOS

## 7.1 Inmediatamente después de cerrar DF-01

1. Documentar la decisión en `CANON/08_COSTEO.md` y `CANON/04_DECISION_LOG.md` usando la plantilla de §6.
2. Marcar el checkpoint CP-1 como aprobado en `EJECUCION_FASE0.md`.
3. Ejecutar A-02 a A-07 en secuencia (Odoo shell, ~6h continuas):

```
A-02 (asignar wood_cost_usd) → A-03 (booking + contenedor) → A-04 (vincular CD)
  → A-05 (action_apply_costs) → A-06 (verificar landed cost) → A-07 (button_validate)
                                                                        │
                                                            HITO H1: account.move posted
```

## 7.2 Checkpoint a aprobar

**CP-1:** DF-01 documentada en CANON. Evidencia: commit con la actualización de `CANON/08_COSTEO.md`.

## 7.3 Cómo usar la evidencia para pasar a Fase 1

| Evidencia | Ubicación |
|-----------|-----------|
| Decisión DF-01 documentada | `CANON/08_COSTEO.md` §1.2 |
| Entrada en decision log | `CANON/04_DECISION_LOG.md` → AD-XX |
| CP-1 marcado como cerrado | `EJECUCION_FASE0.md` §4.2 |

Con CP-1 cerrado, Fase 1 arranca. El primer `account.move` desde MADENAT se genera en ~6h.

---

*Guía preparada: 2026-06-05 — para reunión de cierre DF-01*
*Duración estimada de la reunión: 30 minutos*