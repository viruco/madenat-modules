# CANON/08_COSTEO — FLUJO CANÓNICO DE COSTEO END-TO-END
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Última revisión: 2026-08-19  <!-- actualizado: 2026-08-19 — §9.5 actualizada por AD-54 (diferencia Procesados/Producto resuelta) -->
## Estado: DOCUMENTO CANÓNICO (creado cierre Fase A)
## Versión: 1.5.0
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

## 1.3 Nota — Contrato Producto/Subproducto en costeo

- `product_id` es el **producto maestro por tipo de ingreso** (configurable, no derivado del Excel).
- `subproducto_id` contiene la **clasificación comercial** proveniente del Excel.
- El costeo conserva `product_id` como dimensión estable; los análisis de detalle futuros deben exponer `subproducto_id` como clasificador.

---

# 2. MODELOS Y CAMPOS MONETARIOS (FASE A — SANEADO)

## 2.1 `stock.lot` (madenat_lumber_core)

| Campo | Tipo | Moneda | Descripción |
|-------|------|--------|-------------|
| `currency_id` | Many2one→res.currency | USD | Moneda base del lote |
| `wood_cost_usd` | Float | USD | **Fuente de verdad**: costo base madera. ⚠️ Pendiente migración a Monetary (AD-38) |
| `purchase_cost_usd` | Float (DEPRECATED) | USD | Legacy. Usar `wood_cost_usd` |
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
- **Modelo implementado** (módulo v18.0.1.2.0): `vendor.payment.order` (órdenes de pago), `lumber.shipment.cost` extendido con `partner_id`, `supplier_category`, `invoice_id`/`invoice_ref`/`invoice_date`, `payment_state` (Sin Pagar / Parcial / Pagado), `state` de validación, `allocation_level` (embarque/contenedor/lote) y `validated_by_id`/`validated_date`.
- **Rol en cierre financiero:** vinculación de `lumber.shipment.cost.line` → proveedor (`partner_id`) e `invoice_id`, control de `payment_state`, flujo Validación → Facturación → Pago y aprobaciones por montos.
- La afirmación previa de "Placeholder — sin cambios en esta fase" queda reemplazada por la realidad del modelo (evidencia: `custom_addons/madenat_vendor_payment/models/`).

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

1. **Contabilidad real**: `stock.lot.cost.line` tiene `account_id` (campo existe) pero falta mapping contable completo a `account.move`
2. **Valuation layers**: `stock.landed.cost` integrado parcialmente (commits `81c3373`, `4372dec`) — pendiente validación end-to-end en staging
3. ~~**vendor_payment**: Modelo placeholder~~ → **SUPERADO (2026-08-19)**: módulo implementado v18.0.1.2.0 (`vendor.payment.order`, `lumber.shipment.cost` con `payment_state`/`invoice_id`). Ver §5.5.
4. **Reportes financieros**: Migrar reportes legacy a usar Monetary nativo
5. **Pruebas automatizadas**: Existen suites C2 (cost_distribution), C3 (landed_cost_integration), C4 (module_compatibility) — ver `03_TESTS.md` sección 7. Pendiente ejecución formal en staging.

<!-- actualizado: 2026-08-19 — vendor_payment implementado; pendiente validación end-to-end -->

---

## 8. Criterio normativo de intervención en costeo

Toda operación que afecte costos debe respetar esta secuencia.

1. **Escribir en la fuente de verdad.**  
   El costo base de madera se asigna en `stock.lot.wood_cost_usd`.  
   Los costos adicionales se registran mediante `stock.lot.cost.line`, nunca
   mediante escritura directa en totales.

2. **Garantizar trazabilidad mínima.**  
   Cada `stock.lot.cost.line` debe contener: `cost_type`, `date`, `partner_id`.  
   Estos campos son obligatorios para que el costo sea auditable.

3. **Preservar reversibilidad.**  
   Toda distribución ejecutada desde `lumber.cost.distribution` debe poder
   deshacerse mediante `action_reverse_costs()` sin pérdida de datos ni
   efectos laterales en lotes no involucrados.

4. **Proteger costos ya confirmados.**  
   El `@api.constrains` `_check_cost_modification_if_billed()` impide
   modificar `wood_cost_usd` o `purchase_cost_usd` en lotes cuyo estado
   de facturación no permita cambios. Cualquier corrección posterior
   requiere una acción correctiva explícita compatible con las restricciones
   del flujo de facturación.

---

## 9. Punto de control de OC en Costeo/Valorización

> Regla funcional derivada de AD-52 (2026-08-19): la OC pendiente **no bloquea** la ingesta preliminar ni el envío operativo inicial a stock. La exigencia de OC resuelta corresponde a **esta fase** (Costeo y Valorización / cierre financiero), no a Operaciones.

### 9.1 Estado actual de implementación

- **`action_apply_costs` NO valida OC resuelta.** El método `lumber.cost.distribution.action_apply_costs()` (evidencia: `madenat_lumber_costing/models/lumber_cost_distribution.py:137-228`) solo valida `state=='draft'` y la existencia de `lot_ids`/`cost_line_ids`. **No existe ninguna comprobación de `purchase_id`/`order_id` ni de referencia de OC.**
- **`purchase_id` es solo un filtro de selección de lotes.** En `lumber.cost.distribution` el campo `purchase_id` (L41) se usa únicamente como origen de alcance (`target_model='purchase'`) para localizar lotes por `purchase_order_id` (L119-121). No interviene en validaciones de distribución.
- **No existe estado "cerrado/valorizado" con gate.** El estado de `lumber.cost.distribution` es `draft`/`applied`/`cancelled` (L15-19). No hay transición a `closed` ni a `valorized` con validación de OC.
- **La política documentada es una recomendación de control futuro, no un gate implementado.** Lo declarado en §9.0/intro como "la exigencia final de OC resuelta" corresponde a la intención de diseño, no al comportamiento actual del código.

### 9.2 Riesgos de la brecha

- **Trazabilidad comercial sin OC:** se pueden distribuir costos (flete, puerto, seguro, costo base madera) con `purchase_id` vacío, dificultando la auditoría comercial y la imputación a la OC correcta.
- **Distribución de costos sin validación de proveedor comercial:** `action_apply_costs` no valida `commercial_partner_id` ni compañía; el `partner_id` de la línea de costo es informativo (L210-212).
- **Posible imputación a proveedores erróneos:** sin validación de `partner_id`/`commercial_partner_id`, un expediente puede crear `stock.lot.cost.line` con proveedor distinto al proveedor comercial del lote/recepción.

### 9.3 Próximos pasos (sin diseñar solución)

- Evaluar un gate de OC en `action_apply_costs` para los costos que requieren OC (costo base madera, flete, puerto, seguro), distinguiendo de los costos de proceso/guía que ya portan su vínculo por `guia_processing_id`.
- Evaluar un estado de cierre/valorización con validación de OC (por ejemplo `applied → valorized/closed`) que exija OC resuelta antes del cierre financiero.
- Mantener **sin bloqueo** stock, lotes, pickings, movimientos ni volúmenes (la inyección de `stock.lot.cost.line` es costeo, no inventario físico).
- Respetar la operativa de ingesta de Intake: la OC pendiente **no bloquea** la captura preliminar ni el envío operativo a stock (AD-52/AD-53).
- El refuerzo técnico, cuando se autorice, debe vivir en `madenat_lumber_costing` (no en `madenat_lumber_core` ni en Intake).

### 9.4 Trazabilidad

Toda vinculación manual de OC realizada en Intake queda registrada en `purchase_id`, `oc_match_status='manual'`, `oc_match_note` y chatter (origen: "vinculación manual desde Intake"), preservando `oc_reference_raw` y `manual_po_name`. Esta información es la base de auditoría para el futuro punto de control de esta fase (aún no implementado como gate).

### 9.5 Nota — Diferencia en Procesados: RESUELTA por AD-54

- **Histórico (AD-53):** Procesados (core) tenía un blindaje más temprano: `madenat.guia.processing.action_validate()` bloqueaba el envío a stock si existía `oc_reference_raw` sin `order_id` (evidencia `madenat_guia_processing.py:1552-1559`), a diferencia de Producto/Intake que no bloqueaba (AD-52).
- **Resolución (AD-54, 2026-08-19):** se autorizó de forma puntual eliminar ese bloqueo en `madenat_lumber_core`, convirtiéndolo en advertencia no bloqueante. Ambos modos de ingesta (Producto y Procesados) comparten ahora la misma política: **"OC pendiente no bloquea"** la ingesta ni el envío a stock.
- La exigencia final de OC resuelta **sigue perteneciendo exclusivamente a esta fase** (Costeo/Valorización/cierre financiero), de forma consistente para ambos modos.
- La excepción AD-54 es **puntual y autorizada explícitamente**; no constituye precedente. La regla general de no modificar `madenat_lumber_core` sigue vigente para cualquier otro caso.
- Ver `02_CONTINUIDAD` §9 (resuelta), `04_DECISION_LOG` AD-53/AD-54.

---

*Documento creado: 2026-06-05 — Cierre Fase A — Saneamiento Monetario*
*Versión: 1.5.0*
