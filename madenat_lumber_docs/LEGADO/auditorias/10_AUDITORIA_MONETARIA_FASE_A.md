# FASE A — AUDITORÍA MONETARIA COMPLETA
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-04
## Última revisión: 2026-06-16  <!-- actualizado: 2026-06-16 -->
## Estado: COMPLETADA (Investigación + Implementación Subfases A1–A4)

---

# 1. MAPA DE CAMPOS MONETARIOS ACTUALES

## 1.1 — `stock.lot` (madenat_lumber_core/models/stock_lot.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `purchase_price_usd_per_m3` | Float | NO | Precio unitario (tasa/rate) | NO |
| `purchase_exchange_rate` | Float | NO | Tasa de cambio | NO |
| `purchase_amount_usd` | Float (compute) | SÍ | Monto compra USD | **SÍ → Monetary** |
| `purchase_amount_clp` | Float (compute) | SÍ | Monto compra CLP | **SÍ → Monetary** |
| `wood_cost_usd` | Float | SÍ | Costo madera USD (manual) | **SÍ → Monetary** |
| `purchase_cost_usd` | Float | SÍ | Costo compra USD (manual) | **SÍ → Monetary** |
| `lot_exchange_rate` | Float | NO | Tasa de cambio (legacy) | NO |
| `total_cost_usd` | Float (compute) | SÍ | Costo Total USD | **SÍ → Monetary** |
| `cost_per_m3_usd` | Float (compute) | SÍ | Costo por m³ USD | **SÍ → Monetary** |
| `cost_per_mbf_usd` | Float (compute) | SÍ | Costo por MBF USD | **SÍ → Monetary** |
| `sale_price_usd_per_mbf` | Float | NO | Precio unitario venta | NO |
| `sale_amount_usd` | Float (compute) | SÍ | Monto venta USD | **SÍ → Monetary** |
| `margin_usd` | Float (compute) | SÍ | Margen USD | **SÍ → Monetary** |
| `margin_percent` | Float (compute) | NO | Porcentaje | NO |

NOTA: `stock.lot` **NO tiene `currency_id`**. Se requiere agregarlo.

## 1.2 — `stock.lot.cost.line` (madenat_lumber_core/models/stock_lot_cost_line.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `amount_usd` | Float | SÍ | Monto costo USD | **SÍ → Monetary** |

NOTA: **NO tiene `currency_id`**. Se requiere agregarlo.

## 1.3 — `lumber.reception` (madenat_lumber_core/models/lumber_reception.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `exchange_rate` | Float | NO | Tasa de cambio | NO |
| `total_amount_clp` | Float | SÍ | Monto Total CLP | **SÍ → Monetary** |
| `total_amount_usd` | Float (compute) | SÍ | Monto Total USD | **SÍ → Monetary** |
| `price_per_m3_usd` | Float (compute) | NO | Precio unitario (tasa) | NO |
| `average_price_m3` | Float (compute) | NO | Precio unitario CLP/m³ (tasa) | NO |
| `price_per_mbf_usd` | Float (compute) | NO | Precio unitario (tasa) | NO |

NOTA: Ya tiene `currency_id` (CLP) y `usd_currency_id` (USD). Campos monetarios son Float aún.

## 1.4 — `lumber.reception.line` (madenat_lumber_core/models/lumber_reception.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `estimated_cost_usd` | Float | SÍ | Costo Est. USD (staging) | **SÍ → Monetary** |
| `cost_clp_unit` | Float (compute) | SÍ | Costo unitario CLP | **SÍ → Monetary** |

NOTA: Ya tiene `currency_id` (default CLP). Campos monetarios son Float aún.

## 1.5 — `lumber.cost.distribution` (madenat_lumber_costing/models/lumber_cost_distribution.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `amount_total_usd` | Float (compute) | SÍ | Total a Inyectar USD | **SÍ → Monetary** |

NOTA: Ya tiene `currency_id` (default USD).

## 1.6 — `lumber.cost.distribution.line` (madenat_lumber_costing/models/lumber_cost_distribution.py)

| Campo | Tipo Actual | ¿Monetario? | Clasificación | ¿Migrar? |
|-------|------------|------------|---------------|----------|
| `amount_original` | Float | SÍ | Monto Original (moneda origen) | **SÍ → Monetary** |
| `exchange_rate` | Float | NO | Tasa de cambio | NO |
| `amount_usd` | Float (compute) | SÍ | Monto USD | **SÍ → Monetary** |

NOTA: Ya tiene `currency_id`.

## 1.7 — `madenat_vendor_payment` 

| Modelo | Estado |
|--------|--------|
| `vendor.payment.order` | PLACEHOLDER — solo 16 líneas, solo `name` + `state`. Sin campos monetarios. |

**Conclusión**: No hay nada que migrar en vendor_payment hoy.

---

# 2. CLASIFICACIÓN POR TIPO FINANCIERO

## 2.1 — MONTOS MONETARIOS REALES (deben ser `fields.Monetary`)
Representan dinero en una moneda específica:

| Modelo | Campo | Moneda |
|--------|-------|--------|
| stock.lot | `purchase_amount_usd` | USD |
| stock.lot | `purchase_amount_clp` | CLP |
| stock.lot | `wood_cost_usd` | USD |
| stock.lot | `purchase_cost_usd` | USD |
| stock.lot | `total_cost_usd` | USD |
| stock.lot | `cost_per_m3_usd` | USD |
| stock.lot | `cost_per_mbf_usd` | USD |
| stock.lot | `sale_amount_usd` | USD |
| stock.lot | `margin_usd` | USD |
| stock.lot.cost.line | `amount_usd` | USD |
| lumber.reception | `total_amount_clp` | CLP |
| lumber.reception | `total_amount_usd` | USD |
| lumber.reception.line | `estimated_cost_usd` | USD |
| lumber.reception.line | `cost_clp_unit` | CLP |
| lumber.cost.distribution | `amount_total_usd` | USD |
| lumber.cost.distribution.line | `amount_original` | Variable (moneda origen) |
| lumber.cost.distribution.line | `amount_usd` | USD |

## 2.2 — TASAS DE CAMBIO (deben seguir como `fields.Float`)
No representan dinero, son factores de conversión:

| Modelo | Campo |
|--------|-------|
| stock.lot | `purchase_exchange_rate` |
| stock.lot | `lot_exchange_rate` (legacy) |
| lumber.reception | `exchange_rate` |
| lumber.cost.distribution.line | `exchange_rate` |

## 2.3 — PRECIOS UNITARIOS (deben seguir como `fields.Float`)
Son tasas/precios por unidad de medida:

| Modelo | Campo |
|--------|-------|
| stock.lot | `purchase_price_usd_per_m3` |
| stock.lot | `sale_price_usd_per_mbf` |
| lumber.reception | `price_per_m3_usd` |
| lumber.reception | `average_price_m3` |
| lumber.reception | `price_per_mbf_usd` |

## 2.4 — PORCENTAJES Y RATIOS (deben seguir como `fields.Float`)

| Modelo | Campo |
|--------|-------|
| stock.lot | `margin_percent` |
| stock.lot | `processing_loss_pct` |
| lumber.reception | `volume_variance_percent` |

---

# 3. FUENTE DE VERDAD MONETARIA POR MODELO

## 3.1 — `stock.lot`

### Estructura actual de costos (fragmentada):

```
┌─────────────────────────────────────────────────┐
│ wood_cost_usd (manual)                          │ ← Costo madera (legacy)
├─────────────────────────────────────────────────┤
│ purchase_cost_usd (manual)                      │ ← Costo compra (legacy)
├─────────────────────────────────────────────────┤
│ purchase_amount_usd (compute)                   │ ← volumen_m3 × purchase_price_usd_per_m3
├─────────────────────────────────────────────────┤
│ cost_line_ids → stock.lot.cost.line (manual)    │ ← Líneas de costo adicionales
├─────────────────────────────────────────────────┤
│ total_cost_usd (compute)                        │ ← wood + purchase + cost_lines
├─────────────────────────────────────────────────┤
│ cost_per_m3_usd (compute)                       │ ← SOLO cost_lines / volumen_m3 ⚠️
├─────────────────────────────────────────────────┤
│ cost_per_mbf_usd (compute)                      │ ← SOLO cost_lines / volumen_mbf ⚠️
└─────────────────────────────────────────────────┘
```

### ⚠️ BUG DETECTADO:
`_compute_cost_per_m3` y `_compute_cost_per_mbf` **solo suman `cost_line_ids.amount_usd`**, ignorando `wood_cost_usd` + `purchase_cost_usd`. 
Esto es inconsistente con `_compute_total_cost_usd` que sí los incluye.

### Fuente de verdad definida:

| Propósito | Campo fuente |
|-----------|-------------|
| **Costo base (madera)** | `wood_cost_usd` (se depreciará `purchase_cost_usd` como redundante) |
| **Costos adicionales** | `stock.lot.cost.line` (vía `cost_line_ids`) |
| **Costo total** | `total_cost_usd` = `wood_cost_usd` + `sum(cost_line_ids.amount_usd)` |
| **Costo por m³** | `cost_per_m3_usd` = `total_cost_usd / volumen_m3` |
| **Costo por MBF** | `cost_per_mbf_usd` = `total_cost_usd / volumen_mbf` |

### Redundancias detectadas:
- `purchase_cost_usd` ⇔ `wood_cost_usd` → se unifican bajo `wood_cost_usd`
- `purchase_amount_usd` (derivado) ⇔ `wood_cost_usd` (manual) → `wood_cost_usd` es fuente de verdad

---

## 3.2 — `lumber.reception`

### Fuente de verdad:
| Propósito | Campo fuente |
|-----------|-------------|
| Monto CLP facturado | `total_amount_clp` |
| Monto USD equivalente | `total_amount_usd` (compute desde CLP / exchange_rate) |
| Tipo de cambio | `exchange_rate` |

Moneda base: CLP (`currency_id`). Ya configurado.

---

## 3.3 — `lumber.cost.distribution`

### Fuente de verdad:
| Propósito | Campo fuente |
|-----------|-------------|
| Monto total USD a distribuir | `amount_total_usd` (suma de líneas) |
| Monto original (factura) | `amount_original` por línea |
| Monto equivalente USD | `amount_usd` por línea (compute) |

Moneda base: USD (`currency_id`). Ya configurado.

---

## 3.4 — `stock.lot.cost.line`

### Fuente de verdad:
- `amount_usd` — costo en USD a imputar al lote
- Es la tabla canónica de desglose de costos
- Se requiere `currency_id` + posiblemente `account_id` para futura contabilidad

---

# 4. LISTA DE MIGRACIONES A APLICAR

## 4.1 — `stock.lot` (madenat_lumber_core)
- [ ] Agregar `currency_id` (Many2one → res.currency, default USD)
- [ ] Migrar 9 campos Float → Monetary con `currency_field='currency_id'`:
  - `purchase_amount_usd`, `purchase_amount_clp`
  - `wood_cost_usd`, `purchase_cost_usd`
  - `total_cost_usd`
  - `cost_per_m3_usd`, `cost_per_mbf_usd`
  - `sale_amount_usd`, `margin_usd`
- [ ] Corregir `_compute_cost_per_m3` para usar `total_cost_usd` en vez de solo `cost_line_ids`
- [ ] Corregir `_compute_cost_per_mbf` para usar `total_cost_usd` en vez de solo `cost_line_ids`
- [ ] Depreciar `purchase_cost_usd` (redundante con `wood_cost_usd`) — marcar como deprecated en help
- [ ] Actualizar `_compute_total_cost_usd` para simplificar (solo `wood_cost_usd + cost_line_ids`)

## 4.2 — `stock.lot.cost.line` (madenat_lumber_core)
- [ ] Agregar `currency_id` (Many2one → res.currency, default USD)
- [ ] Migrar `amount_usd` Float → Monetary con `currency_field='currency_id'`

## 4.3 — `lumber.reception` (madenat_lumber_core)
- [ ] Migrar `total_amount_clp` Float → Monetary con `currency_field='currency_id'` (CLP)
- [ ] Migrar `total_amount_usd` Float → Monetary con `currency_field='usd_currency_id'` (USD)

## 4.4 — `lumber.reception.line` (madenat_lumber_core)
- [ ] Migrar `estimated_cost_usd` Float → Monetary con `currency_field='currency_id'` (compute/new)
- [ ] Migrar `cost_clp_unit` Float → Monetary con `currency_field='currency_id'`

## 4.5 — `lumber.cost.distribution` (madenat_lumber_costing)
- [ ] Migrar `amount_total_usd` Float → Monetary con `currency_field='currency_id'`

## 4.6 — `lumber.cost.distribution.line` (madenat_lumber_costing)
- [ ] Migrar `amount_original` Float → Monetary con `currency_field='currency_id'`
- [ ] Migrar `amount_usd` Float → Monetary con `currency_field='currency_id'`

## 4.7 — `madenat_vendor_payment`
- [ ] SIN CAMBIOS en esta fase (placeholder)

---

# 5. CAMPOS PENDIENTES O JUSTIFICADOS (NO MIGRAR)

| Campo | Razón |
|-------|-------|
| `purchase_price_usd_per_m3` | Precio unitario, no monto monetario |
| `purchase_exchange_rate` | Tasa de cambio, factor de conversión |
| `lot_exchange_rate` | Tasa de cambio, legacy |
| `sale_price_usd_per_mbf` | Precio unitario |
| `margin_percent` | Porcentaje |
| `exchange_rate` (reception) | Tasa de cambio |
| `price_per_m3_usd` (reception) | Precio unitario |
| `average_price_m3` (reception) | Precio unitario |
| `price_per_mbf_usd` (reception) | Precio unitario |
| `exchange_rate` (cost.distribution.line) | Tasa de cambio |
| `processing_loss_pct` | Porcentaje |
| `volume_variance_percent` | Porcentaje |

---

# 6. DEPENDENCIAS CRUZADAS (IMPACTO DE MIGRACIÓN)

## Módulos que consumen campos de stock.lot:
- `madenat_lumber_costing` → `lumber_cost_distribution.py` (lee `total_volumen_fisico`, `total_volumen_export`, `volumen_m3`, `vol_shipment_m3`)
- `madenat_lumber_logistics` → `lumber_shipment_costing.py` (lee `vol_shipment_m3`, `volumen_m3`)
- `madenat_lumber_billing` → `lumber_billing_consolidation_line.py` (lee costos de lote — ya usa Monetary)

## Vistas que muestran campos monetarios de stock.lot:
- `custom_addons/madenat_lumber_core/views/stock_lot_views.xml`

## Riesgos:
- **BAJO**: Cambiar Float → Monetary en Odoo 18 es seguro si se agrega `currency_id` y se usa `currency_field`
- **MEDIO**: La corrección de `_compute_cost_per_m3`/`_compute_cost_per_mbf` cambia valores si hay `wood_cost_usd > 0` y `cost_line_ids` vacíos (antes daba 0, ahora dará `wood_cost_usd / volumen`)
- **BAJO**: Las vistas existentes ya muestran el símbolo de moneda si se usa `widget='monetary'`

---

# 7. PLAN DE MIGRACIÓN (PRIORIZADO)

### Subfase A1 — `stock.lot.cost.line` (tabla canónica, sin dependencias complejas)
1. Agregar `currency_id`
2. Migrar `amount_usd` a Monetary

### Subfase A2 — `stock.lot` (modelo central, máxima visibilidad)
1. Agregar `currency_id`
2. Migrar 9 campos monetarios a Monetary
3. Corregir `_compute_cost_per_m3` y `_compute_cost_per_mbf`
4. Depreciar `purchase_cost_usd`

### Subfase A3 — `lumber.reception` + `lumber.reception.line`
1. Migrar `total_amount_clp`, `total_amount_usd`
2. Migrar `estimated_cost_usd`, `cost_clp_unit`

### Subfase A4 — `lumber.cost.distribution` + `lumber.cost.distribution.line`
1. Migrar `amount_total_usd`
2. Migrar `amount_original`, `amount_usd`

---

# 8. READINESS PARA SIGUIENTE SUBFASE

✅ Auditoría completada  
✅ Mapa de campos clasificados  
✅ Fuente de verdad definida por modelo  
✅ Redundancias identificadas  
✅ Bug en cálculo de costo por m³/MBF detectado  
✅ Plan de migración priorizado  
✅ Implementación de Subfases A1–A4  
⬜ Validación funcional en staging  
✅ Documentación actualizada — `08_COSTEO.md` creado 2026-06-05, revisado 2026-06-16  
✅ Commits — registrados en git log (2026-06-02 a 2026-06-05)  

<!-- actualizado: 2026-06-16 -->

---

## Implementaciones Realizadas (2026-06-05)

### Subfase A1 — `stock.lot.cost.line`
✅ `currency_id` agregado (default USD)  
✅ `amount_usd` Float → Monetary  

### Subfase A2 — `stock.lot`
✅ `currency_id` agregado (default USD)  
✅ 9 campos Float → Monetary  
✅ `_compute_cost_per_m3` corregido (usa total_cost_usd)  
✅ `_compute_cost_per_mbf` corregido (usa total_cost_usd)  
✅ `purchase_cost_usd` deprecado  
✅ `_compute_total_cost_usd` simplificado  

### Subfase A3 — `lumber.reception` + `lumber.reception.line`
✅ `total_amount_clp` → Monetary (CLP)  
✅ `total_amount_usd` → Monetary (USD)  
✅ `estimated_cost_usd` → Monetary  
✅ `cost_clp_unit` → Monetary  

### Subfase A4 — `lumber.cost.distribution` + `lumber.cost.distribution.line`
✅ `amount_total_usd` → Monetary  
✅ `amount_original` → Monetary  
✅ `amount_usd` → Monetary  

*Documento generado: 2026-06-04 — Fase A — Auditoría Monetaria*
*Última actualización: 2026-06-16 — Revisión documental, marcados entregables*
