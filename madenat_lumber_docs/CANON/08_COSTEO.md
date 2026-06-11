# CANON/08_COSTEO — FLUJO CANÓNICO DE COSTEO END-TO-END
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Estado: DOCUMENTO CANÓNICO (creado cierre Fase A)
## Refs: FASE-A, AD-XX-MONETARIO, Anexo de Saneamiento Monetario 2026-06-04

---

# 1. ARQUITECTURA DE COSTEO (FUENTE DE VERDAD)

## 1.1 Modelo canónico de costo por lote

```
                    ┌─────────────────────────────────────────────────┐
                    │        stock.lot (datos base)                   │
                    │  wood_cost_usd          ← Costo madera (USD)    │
                    │  purchase_price_usd_per_m3 ← Precio unitario    │
                    │  purchase_amount_usd     ← Derivado (compute)   │
                    │  purchase_amount_clp     ← Derivado (compute)   │
                    ├─────────────────────────────────────────────────┤
                    │  cost_line_ids (O2M) ← Desglose granular        │
                    │  → stock.lot.cost.line                          │
                    │     amount_usd, cost_type, date, partner_id     │
                    ├─────────────────────────────────────────────────┤
                    │  total_cost_usd (compute, store=False)          │
                    │     = wood_cost_usd + Σ(cost_line_ids)          │
                    ├─────────────────────────────────────────────────┤
                    │  cost_per_m3_usd  = total_cost_usd / volumen_m3 │
                    │  cost_per_mbf_usd = total_cost_usd / volumen_mbf│
                    └─────────────────────────────────────────────────┘
```

## 1.2 Jerarquía de verdad monetaria

| Prioridad | Fuente | Campo | Modelo |
|-----------|--------|-------|--------|
| 1 (base) | Manual / ingesta | `wood_cost_usd` | `stock.lot` |
| 2 (adicional) | Líneas de costo | `amount_usd` en `stock.lot.cost.line` | `stock.lot.cost.line` |
| 3 (total) | Compute | `total_cost_usd` | `stock.lot` |
| 4 (unitario) | Compute | `cost_per_m3_usd`, `cost_per_mbf_usd` | `stock.lot` |

---

# 2. MODELOS Y CAMPOS MONETARIOS (FASE A — SANEADO)

## 2.1 `stock.lot` (madenat_lumber_core)

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | USD | Moneda base del lote |
| `wood_cost_usd` | Monetary | USD | **Fuente de verdad**: costo base madera |
| `purchase_cost_usd` | Monetary (DEPRECATED) | USD | Legacy. Usar `wood_cost_usd` |
| `purchase_amount_usd` | Monetary (compute) | USD | Derivado: volumen_m3 × purchase_price |
| `purchase_amount_clp` | Monetary (compute) | USD | Derivado: USD × exchange_rate |
| `total_cost_usd` | Monetary (compute) | USD | wood + Σ(cost_line_ids) |
| `cost_per_m3_usd` | Monetary (compute) | USD | total / volumen_m3 |
| `cost_per_mbf_usd` | Monetary (compute) | USD | total / volumen_mbf |
| `sale_amount_usd` | Monetary (compute) | USD | volumen_mbf × sale_price |
| `margin_usd` | Monetary (compute) | USD | sale - total_cost |

**NO migrados** (tasas, precios unitarios, porcentajes):
- `purchase_price_usd_per_m3` — Float (precio unitario)
- `purchase_exchange_rate` — Float (tasa)
- `sale_price_usd_per_mbf` — Float (precio unitario)
- `margin_percent` — Float (porcentaje)

## 2.2 `stock.lot.cost.line` (madenat_lumber_core)

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | USD | Moneda del costo |
| `amount_usd` | Monetary | USD | Monto en USD |

## 2.3 `lumber.reception` (madenat_lumber_core)

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | CLP | Moneda base CLP |
| `usd_currency_id` | Many2one→res.currency | USD | Moneda USD |
| `total_amount_clp` | Monetary | CLP | Monto facturado |
| `total_amount_usd` | Monetary (compute) | USD | = CLP / exchange_rate |
| `exchange_rate` | Float | — | Tasa de cambio |

## 2.4 `lumber.cost.distribution` (madenat_lumber_costing)

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | USD | Moneda base |
| `amount_total_usd` | Monetary (compute) | USD | Total a inyectar |

## 2.5 `lumber.cost.distribution.line`

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | Variable | Moneda origen |
| `amount_original` | Monetary | Variable | Monto original |
| `amount_usd` | Monetary (compute) | Variable | Equivalente USD |

---

# 3. FLUJO DE COSTEO END-TO-END

## 3.1 Ingreso de costo base (madera)

```
1. Recepción → staging (lumber.reception.line)
2. Confirmación → creación de stock.lot
3. Operador asigna wood_cost_usd en el lote
4. Opcional: purchase_price_usd_per_m3 para valorización derivada
```

## 3.2 Costos adicionales (logística, puerto, seguro, etc.)

```
1. Operador crea lumber.cost.distribution (Expediente de Liquidación)
2. Selecciona origen: booking / container / reception / purchase
3. Agrega líneas de costo (lumber.cost.distribution.line)
4. Ejecuta action_apply_costs()
5. Sistema crea stock.lot.cost.line por cada lote + línea de costo
6. Los totales se recalculan en los lotes automáticamente
```

## 3.3 Métodos de prorrateo disponibles

- `volume_export` — Por m³ de exportación
- `volume_physical` — Por m³ físico
- `weight` — Por peso (kg)
- `pieces` — Por número de piezas
- `equal` — Equitativo entre lotes
- `container` — Costo por contenedor × N contenedores

## 3.4 Reversión

```
action_reverse_costs() elimina las líneas inyectadas y vuelve a draft.
```

---

# 4. CONSISTENCIA MONETARIA (POST-FASE A)

## 4.1 Campos Monetary (17 migrados)

Todos los campos que representan montos de dinero usan `fields.Monetary` con `currency_field` explícito.

## 4.2 Campos Float (no migrados, correcto)

Tasas de cambio, precios unitarios, porcentajes — son ratios, no montos.

## 4.3 Separación USD/CLP

- **USD**: `wood_cost_usd`, `total_cost_usd`, `cost_per_m3_usd`, `cost_per_mbf_usd`, `sale_amount_usd`, `margin_usd`
- **CLP**: `total_amount_clp` en recepción, `cost_clp_unit` en línea de recepción
- **Variable**: `amount_original` en línea de distribución respeta la moneda de la factura origen

## 4.4 No hay mezcla

Cada campo Monetary tiene su `currency_field` explícito. No hay ambigüedad USD/CLP.

---

# 5. MÓDULOS DEPENDIENTES (COMPATIBILIDAD)

## 5.1 `madenat_lumber_billing`
- Usa `wood_cost_usd`, `total_cost_usd`, `margin_usd` como Monetary
- Lectura de `lot_id.total_cost_usd` (compute) — compatible
- Sin impacto por migración Float→Monetary

## 5.2 `madenat_lumber_logistics`
- Lee `wood_cost_usd`, `sale_amount_usd` de lotes
- Cálculo de margen bruto (`gross_margin_usd`) — ya usa Monetary
- Distribución de costos logísticos — cálculo en USD, compatible

## 5.3 `madenat_lumber_costing`
- Motor de distribución: escribe `stock.lot.cost.line.amount_usd` (Monetary)
- Lee volúmenes (`volumen_m3`, `vol_shipment_m3`) — sin cambios
- Totalmente compatible

## 5.4 `madenat_toll_processing`
- SIN impacto detectado (no consume campos monetarios de lotes directamente)

## 5.5 `madenat_vendor_payment`
- Placeholder — sin cambios en esta fase

---

# 6. CORRECCIONES APLICADAS EN FASE A

## 6.1 Bug corregido: `cost_per_m3_usd` y `cost_per_mbf_usd`
- **Antes**: Solo sumaban `cost_line_ids.amount_usd`, ignorando `wood_cost_usd`
- **Ahora**: Usan `total_cost_usd` que incluye `wood_cost_usd` + `cost_line_ids`

## 6.2 Simplificación: `_compute_total_cost_usd`
- **Antes**: `wood_cost_usd + purchase_cost_usd + cost_line_ids`
- **Ahora**: `wood_cost_usd + cost_line_ids` (purchase_cost_usd deprecado)

## 6.3 Deprecación: `purchase_cost_usd`
- Campo mantenido como Monetary (compatibilidad histórica)
- Marcado DEPRECATED en help text
- Eliminado de vistas activas
- Report `lumber_cost_report.py` lo lee como fallback de compatibilidad

---

# 7. QUÉ QUEDÓ PENDIENTE (FASE B+)

1. **Contabilidad real**: `stock.lot.cost.line` no tiene `account_id` para mapping contable
2. **Valuation layers**: Odoo no recibe los landed costs automáticamente en `stock.valuation.layer`
3. **vendor_payment**: Modelo placeholder sin implementación real
4. **Reportes financieros**: Migrar reportes legacy a usar Monetary nativo
5. **Pruebas automatizadas**: Tests unitarios para flujos de costeo

---

# 8. REGLA DE ORO DEL COSTEO

1. **Fuente única de verdad**: `wood_cost_usd` para costo base, `cost_line_ids` para adicionales
2. **Monetary siempre**: Todo monto en dinero usa `fields.Monetary`
3. **Trazabilidad total**: Cada costo tiene `cost_type`, `date`, `partner_id`
4. **Reversibilidad**: `action_reverse_costs()` permite deshacer distribución
5. **Protección**: Lotes facturados no permiten modificar costos

---

*Documento creado: 2026-06-05 — Cierre Fase A — Saneamiento Monetario*
*Versión: 1.0.0*