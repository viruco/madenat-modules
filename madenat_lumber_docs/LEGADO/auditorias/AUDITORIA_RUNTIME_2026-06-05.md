# AUDITORÍA FUNCIONAL RUNTIME — MADENAT Lumber
## Flujo: Recepción → Landed Cost → Account Move
### Fecha: 2026-06-05 | Tipo: Auditoría sin intervención | Base: madenat_test

<!--
  NOTA DE REVISIÓN 2026-06-16:
  Este documento es un snapshot histórico de la base `madenat_test` al 2026-06-05.
  Los hallazgos fueron veraces en esa fecha.

  Cambios posteriores relevantes:
  - stock.landed.cost override integrado (commits 81c3373, 4372dec, 2026-06-10+)
  - test_landed_cost_integration.py creado (5 tests, C3.1–C3.5)
  - stock.lot.cost.line.account_id campo existe (C4.1)
  - Sección 3 (Pasos para habilitar flujo) parcialmente abordada

  Pendiente: re-ejecutar esta auditoría en staging para verificar estado actual (2026-06-16).
-->

---

# 1. RESUMEN EJECUTIVO

## Pregunta central de la auditoría:
**¿El sistema genera realmente `account.move` desde `button_validate` en el entorno actual, con datos reales?**

## Respuesta: **NO. El flujo NO llega a contabilidad real en este entorno.**

### Evidencia concluyente:

| Objeto | Esperado | Real | Estado |
|--------|----------|------|--------|
| `stock.landed.cost` | ≥ 1 (generado por `action_apply_costs`) | **0** | ❌ INEXISTENTE |
| `stock.lot.cost.line` | ≥ 1 (inyectado a lotes) | **0** | ❌ INEXISTENTE |
| `account.move` desde landed cost | ≥ 1 (vía `button_validate`) | **0** | ❌ INEXISTENTE |
| `lumber.cost.distribution` en `applied` | 1 | **0** (el único está en `draft`) | ❌ NO APLICADO |
| `stock.valuation.layer` por landed cost | ≥ 1 | **0** | ❌ INEXISTENTE |

### Conclusión inequívoca:
La distribución `CD-2026-0002` existe en estado **draft**, con `booking_id = NULL`, sin lotes asignados efectivamente, y `action_apply_costs()` **nunca fue ejecutada exitosamente**. El puente `_generate_landed_costs()` **nunca se disparó**. No hay `stock.landed.cost` creado. No hay `button_validate` que validar. No hay `account.move` generado desde este flujo.

**El código existe, la documentación lo describe, los tests unitarios lo cubren — pero en el entorno runtime actual, el flujo nunca llegó a contabilización real.**

---

# 2. EVIDENCIA TÉCNICA

## 2.1 Recepción

| Atributo | Valor |
|----------|-------|
| `stock.picking` totales | 5 (4 Recepciones, 1 Entrega) |
| Pickings en estado `done` | 5/5 |
| Recepción IDs | WH/IN/00091, EMB-00112, EMB-00113, EMB-00114 |
| `stock.lot` totales | 39 |
| Lotes con `reception_id` | Varios (IDs 1860-1887+) |
| `wood_cost_usd` en lotes | **0.00 en todos los lotes** |
| `volumen_m3` en lotes | Entre 3.6 y 4.9 m³ |

**Hallazgo:** Recepciones ejecutadas y lotes creados correctamente. Sin embargo, ningún lote tiene `wood_cost_usd > 0`. El costo base de madera NO fue asignado.

## 2.2 Landed Cost

| Atributo | Valor |
|----------|-------|
| `stock.landed.cost` | **0 registros** |
| `stock.lot.cost.line` | **0 registros** |
| `lumber.cost.distribution` | 1 registro: `CD-2026-0002` |
| Estado de CD-2026-0002 | **draft** |
| `target_model` de CD-2026-0002 | `booking` |
| `booking_id` de CD-2026-0002 | **NULL** |
| `amount_total_usd` de CD-2026-0002 | 172.028 |
| Líneas de distribución | Existen (con `cost_type`, `amount_usd`, `distribution_method`) |
| `account_id` en líneas | Posiblemente asignado (por confirmar en UI) |

**Hallazgo:** La distribución existe pero está en draft. `booking_id` es NULL → el `onchange` no pudo cargar lotes automáticamente. `action_apply_costs()` NUNCA fue llamado exitosamente. Sin `stock.lot.cost.line` creado, sin `_generate_landed_costs()` ejecutado, sin `stock.landed.cost` generado.

## 2.3 Valorización

| Atributo | Valor |
|----------|-------|
| `stock.valuation.layer` totales | **1,480** |
| Origen de valuation layers | Pickings de recepción/entrega (stock moves normales) |
| Valuation layers por landed cost | **0** (no puede haber sin `stock.landed.cost` validado) |
| `stock.valuation.layer` con `stock_landed_cost_id` | **0** |

**Hallazgo:** Los 1,480 valuation layers provienen exclusivamente de movimientos de stock normales (entradas/salidas de inventario), no de landed costs.

## 2.4 Contabilización

| Atributo | Valor |
|----------|-------|
| `account.move` totales | **1** |
| `account.move` desde `stock.landed.cost` | **0** |
| Origen del único `account.move` | Setup/demo (no relacionado con MADENAT) |
| `account.move.line` desde landed cost | **0** |

**Hallazgo:** El único `account.move` en la BD no proviene del flujo MADENAT. No existe contabilización de landed costs.

## 2.5 Reversión

No aplica — no hay nada que revertir porque nunca se aplicó la distribución.

---

# 3. DIFERENCIAS ENTRE DOCUMENTACIÓN Y RUNTIME

## 3.1 Coincidencias

| Documento | Afirmación | Verificación |
|-----------|------------|--------------|
| `08_COSTEO.md` §7 | "Contabilidad real: pendiente" | ✅ La documentación ya lo declara pendiente |
| `08_COSTEO.md` §7 | "Valuation layers: Odoo no recibe landed costs automáticamente" | ✅ Confirmado — 0 valuation layers de landed cost |
| `11_FASE_E_VALIDACION.md` §1.5 G-01 | "Generación real de account.move desde stock.landed.cost — No validado" | ✅ La documentación lo reconoce como GAP |
| `03_TESTS.md` §8 | "Flujo completo con recepción real + picking + landed cost + button_validate" como GAP | ✅ La documentación lo identifica |
| `02_CONTINUIDAD.md` | "Próximo paso: Fase D — Integración contable" | ✅ Correcto, la Fase D es necesaria |

## 3.2 Contradicciones

| Documento | Afirmación | Realidad Runtime | Severidad |
|-----------|------------|------------------|-----------|
| `11_FASE_E_VALIDACION.md` §1.3 Tramo 4 | "✅ Funcional — validado por Suite 3 (C3.1–C3.5)" | C3.1-C3.5 son **tests unitarios**, no validación runtime. En runtime: 0 landed costs | **ALTA** |
| `11_FASE_E_VALIDACION.md` §1.3 Tramo 5 | "✅ Funcional — validado por C2.5 y C3.4" | Tests unitarios pasan, pero nunca se ejerció reversión sobre datos reales | MEDIA |
| `11_FASE_E_VALIDACION.md` §4.2 | "Landed cost generado por picking — ✅ Completado — C3.1" | C3.1 prueba la generación en test, NO en runtime. Runtime: 0 | **ALTA** |
| `11_FASE_E_VALIDACION.md` §5.1 | "Flujo de negocio: Documentado y validado en código desde compra hasta reversión" | Validado en código ≠ validado en runtime. El runtime no tiene el flujo completo | **ALTA** |

## 3.3 Gaps

| Gap | Documentado | Runtime | Acción requerida |
|-----|-------------|---------|-----------------|
| `button_validate` sobre `stock.landed.cost` | Documentado como G-01 | **Nunca ejecutado** | Ejecutar en runtime |
| `account.move` desde landed cost | Documentado como G-01 | **No existe** | Validar tras button_validate |
| `wood_cost_usd` asignado a lotes | Documentado §3.1 paso 3 | **0 en todos los lotes** | Asignar costo base |
| `booking_id` en distribución | Documentado como target `booking` | **NULL** — sin booking asignado | Asignar booking real |
| `action_apply_costs()` | Documentado §3.2 paso 4 | **Nunca ejecutado** | Ejecutar con datos reales |
| `_generate_landed_costs()` | Implementado en código (línea 263-321) | **Nunca disparado** | Depende de action_apply_costs |
| `stock.valuation.layer` por landed cost | Documentado como G-03 | **0 registros** | Requiere button_validate |
| Flujo end-to-end con datos reales | Documentado como GAP en `03_TESTS.md` §8 | **No verificado** | Pendiente |

---

# 4. DIAGNÓSTICO DE CAUSA RAÍZ

## ¿Por qué el flujo no llegó a contabilidad?

### Bloqueo en cascada:

```
CD-2026-0002 (draft, booking_id=NULL)
  → No se pudieron cargar lotes (sin booking)
  → action_apply_costs() nunca se llamó
  → stock.lot.cost.line nunca se creó (0 registros)
  → _generate_landed_costs() nunca se disparó
  → stock.landed.cost nunca se creó (0 registros)
  → button_validate() nunca tuvo un landed cost que validar
  → account.move nunca se generó desde landed cost
```

### Causa inmediata:
- `booking_id` es NULL en la distribución
- Sin booking, el `onchange` no puede encontrar contenedores ni lotes
- Los lotes no están vinculados a la distribución (`lot_ids` vacío o insuficiente)

### Causa subyacente:
- `wood_cost_usd = 0` en todos los lotes — el costo base nunca fue asignado
- No se ha completado el paso 3 del flujo documentado: "Operador asigna wood_cost_usd en el lote"
- La Fase D (integración contable) está declarada como "próximo paso" pero aún no ejecutada

---

# 5. ESTADO DE CIERRE

## Cerrado (verificado en runtime)
- ✅ Recepciones creadas con pickings en estado `done`
- ✅ Lotes generados con `volumen_m3` y `reception_id`
- ✅ `stock.valuation.layer` existe para movimientos de stock normales (1,480)
- ✅ Módulos `account`, `stock_account`, `stock_landed_costs` instalados
- ✅ Código de puente contable implementado (`_generate_landed_costs`, `stock_landed_cost` heredado)
- ✅ Tests unitarios (23) existen y pasan en CI

## Pendiente real (NO verificado en runtime)
- ❌ `wood_cost_usd > 0` en lotes (costo base no asignado)
- ❌ `lumber.cost.distribution` en estado `applied` (nunca aplicado)
- ❌ `stock.lot.cost.line` creado (0 registros)
- ❌ `stock.landed.cost` generado (0 registros)
- ❌ `button_validate` ejecutado sobre landed cost
- ❌ `account.move` generado desde landed cost
- ❌ `stock.valuation.layer` vinculado a landed cost
- ❌ Flujo end-to-end completo con datos reales

## Riesgo residual
| Riesgo | Nivel | Notas |
|--------|-------|-------|
| El puente contable nunca fue probado en runtime | **ALTO** | Requiere Fase D completa |
| `_generate_landed_costs` depende de `reception_id.picking_id` | **ALTO** | Si el lote no tiene picking, no se genera landed cost (documentado en C3.2, pero no verificado en runtime) |
| `account_id` opcional en cost lines | MEDIO | Si no se asigna, Odoo usa fallback del producto |
| `stock_lot_check_cost_positive` constraint | MEDIO | Podría bloquear si `wood_cost_usd = 0` y no se relaja |
| Sin `stock.valuation.layer` automático | MEDIO | Documentado como pendiente Fase D |

---

# 6. RECOMENDACIONES

## Para cerrar la auditoría satisfactoriamente, se requiere:

1. **Asignar `wood_cost_usd > 0`** a al menos un lote con `reception_id.picking_id`
2. **Asignar `booking_id`** a la distribución `CD-2026-0002` (o crear una nueva con booking real)
3. **Ejecutar `action_apply_costs()`** y verificar que:
   - Crea `stock.lot.cost.line` (cantidad > 0)
   - Llama a `_generate_landed_costs()`
   - Crea `stock.landed.cost` (cantidad > 0, con `madenat_distribution_id`)
4. **Ejecutar `button_validate()`** sobre el `stock.landed.cost` generado
5. **Verificar que se genera `account.move`** (estado `posted`, líneas contables)
6. **Verificar `stock.valuation.layer`** vinculado al landed cost

Solo tras completar estos 6 pasos con datos reales en este entorno, se podrá marcar el flujo como **verificado en runtime**.

---

# 7. REGLA DE ORO CUMPLIDA

Esta auditoría se realizó **sin modificar una sola línea de código**, sin añadir logs, sin cambiar configuración. Toda la evidencia se obtuvo por consulta directa a la base de datos PostgreSQL del entorno de prueba en ejecución.

---

*Auditoría ejecutada: 2026-06-05 02:05 AM (UTC-4)*
*Base de datos: madenat_test*
*Contenedor: odoo18_app (Up), odoo18_db (healthy)*