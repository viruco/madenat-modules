# PLAN DE ACCIÓN EJECUTABLE — MADENAT Lumber
## Continuidad de Depuración: Reporte de Valorización Exportadora
### Derivado de PLAN_DEPURACION_PRIORIZADO.md (2026-06-05)

**Fecha:** 2026-06-05
**Tipo:** Plan de trabajo técnico — accionable por el equipo de desarrollo
**Base:** PLAN_DEPURACION_PRIORIZADO.md (18 brechas, 4 niveles de prioridad, 4 fases)
**Entorno:** DEV (madenat_test)

---

# 1. RESUMEN EJECUTIVO

## 1.1 Estado actual del sistema

| Capa | Estado | Evidencia |
|------|--------|-----------|
| Recepción y staging | ✅ Funcional | 5 pickings done, 39 lotes con `reception_id` y `volumen_m3` |
| Trazabilidad de lotes | ✅ Funcional | `reception_id` ↔ `stock.lot` ↔ `stock.picking` correcto |
| Guías de procesamiento | ✅ Funcional | Código implementado, estados correctos |
| Base monetaria (Fase A) | ✅ Completada | 17 campos `fields.Monetary` migrados en `stock.lot`, `stock.lot.cost.line`, `lumber.reception`, `lumber.cost.distribution` |
| Cálculo de costos unitarios | ✅ Corregido | `cost_per_m3_usd` y `cost_per_mbf_usd` ya usan `total_cost_usd` (Fase A) |
| Costo base (`wood_cost_usd`) | ❌ No asignado | 0.00 en 39/39 lotes |
| Distribución de costos | ❌ No ejecutada | CD-2026-0002 en `draft`, `booking_id=NULL`, 0 `stock.lot.cost.line` |
| Landed cost Odoo | ❌ No generado | 0 `stock.landed.cost` |
| Contabilidad (`account.move`) | ❌ No generada | 0 `account.move` desde landed cost |
| Persistencia de `total_cost_usd` | ❌ No persiste | `store=False` |
| Reporte de valorización | ❌ No viable | Sin datos monetarios el informe solo muestra columnas dimensionales |

## 1.2 Qué está listo para usar hoy

- El pipeline de recepción (`lumber.reception`) genera lotes con dimensiones y volúmenes correctos.
- El motor de distribución de costos (`lumber.cost.distribution`) está implementado con 6 métodos de prorrateo.
- El puente `_generate_landed_costs()` existe en código y pasa tests unitarios.
- Los 23 tests de costeo pasan en CI.
- Las fórmulas de exportación (`lumber.export.formula`) tienen seed data y fallback a `utils_uom`.

## 1.3 Qué está bloqueando la continuidad

| Bloqueo | Tipo | Resuelve |
|---------|------|----------|
| `wood_cost_usd = 0` en todos los lotes | Dato maestro faltante | Asignación manual o script |
| `booking_id = NULL` en CD-2026-0002 | Relación no establecida | Vincular booking con contenedores y lotes |
| `total_cost_usd` no-store | Campo no persistente | Cambio de modelo + backfill |
| `_deprecated_action_distribute_costs` bypassea trazabilidad | Escritura directa a `stock.lot` sin `cost_line_ids` | Refactor en `lumber_shipment_costing.py` |

## 1.4 Decisiones funcionales pendientes (bloquean tareas técnicas)

| # | Decisión requerida | Bloquea | Quién decide | Urgencia |
|---|-------------------|---------|-------------|----------|
| DF-01 | ¿De dónde se obtiene `wood_cost_usd`? Opciones: (a) `purchase.order.price_unit`, (b) PDF de guía de despacho parseado, (c) ingreso manual por operador | Toda la Fase 1 del plan | Negocio / Operaciones | **INMEDIATA** |
| DF-02 | ¿Fuente de verdad para costo base en el reporte? Opciones: (a) `wood_cost_usd` (manual/asignado), (b) `purchase_amount_usd` (derivado de `volumen_m3 × purchase_price_usd_per_m3`) | Configuración del reporte y vistas | Negocio / Finanzas | Fase 3 |

---

# 2. PLAN DE ACCIÓN PRIORIZADO

## 2.1 Acciones Bloqueantes (ejecutar en orden)

### A-01 — [DECISIÓN FUNCIONAL] Definir origen de `wood_cost_usd`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 — Bloquea Fase 1 completa |
| **Objetivo** | El negocio define si `wood_cost_usd` se toma de la OC, del PDF, o es ingreso manual |
| **Modelo/Archivo** | `stock.lot` / decisión operativa |
| **Dependencia** | Ninguna |
| **Esfuerzo** | 0h técnica (reunión funcional) |
| **Tipo** | Decisión funcional |
| **Criterio de aceptación** | Respuesta documentada en CANON/08_COSTEO.md §1.2 con la fuente de dato elegida |

### A-02 — [SCRIPT] Asignar `wood_cost_usd > 0` a lotes existentes

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | Poblar `wood_cost_usd` en ≥ 10 lotes con `reception_id.picking_id` no nulo |
| **Modelo/Archivo** | `stock.lot` (`custom_addons/madenat_lumber_core/models/stock_lot.py`) |
| **Dependencia** | DF-01 resuelta |
| **Esfuerzo** | 1h |
| **Tipo** | Script Python (Odoo shell o wizard) |
| **Criterio de aceptación** | `SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0 AND reception_id IS NOT NULL` → ≥ 10 |

**Método de ejecución:**
```python
# Ejecutar en Odoo shell (docker exec odoo18_app odoo shell -d madenat_test)
lots = env['stock.lot'].search([('reception_id', '!=', False), ('picking_ids', '!=', False)], limit=20)
# Opción A: desde purchase.order
for lot in lots:
    po_line = lot.reception_id.order_id.order_line.filtered(lambda l: l.product_id == lot.product_id)
    if po_line:
        lot.wood_cost_usd = po_line.price_unit * lot.volumen_m3
# Opción B: valor fijo de prueba
# for lot in lots:
#     lot.wood_cost_usd = 620.0
env.cr.commit()
```

### A-03 — [SCRIPT] Crear booking + contenedor + asignar lotes

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | Tener un booking con ≥ 1 contenedor que contenga lotes en estado `en_patio` o `recepcionado` |
| **Modelo/Archivo** | `shipping.booking`, `lumber.container`, `stock.lot` (`madenat_lumber_shipping_core`, `madenat_lumber_logistics`) |
| **Dependencia** | A-02 completada (lotes con `wood_cost_usd > 0`) |
| **Esfuerzo** | 1.5h |
| **Tipo** | Script Python (Odoo shell) |
| **Criterio de aceptación** | `SELECT count(*) FROM lumber_container WHERE booking_id IS NOT NULL AND lot_ids IS NOT NULL` → ≥ 1 |

**Método de ejecución:**
```python
# Odoo shell
booking = env['shipping.booking'].create({'name': 'EMB-DEV-0001', 'partner_id': 1})
container = env['lumber.container'].create({
    'name': 'CONT-DEV-001',
    'booking_id': booking.id,
    'lot_ids': [(6, 0, lots.ids[:5])],  # primeros 5 lotes con wood_cost_usd > 0
})
```

### A-04 — [SCRIPT] Vincular booking a distribución de costos existente

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | CD-2026-0002 (o nueva) con `booking_id` que apunte a booking con contenedores y lotes |
| **Modelo/Archivo** | `lumber.cost.distribution` (`custom_addons/madenat_lumber_costing/models/lumber_cost_distribution.py`) |
| **Dependencia** | A-03 completada |
| **Esfuerzo** | 0.5h |
| **Tipo** | Script Python (Odoo shell) |
| **Criterio de aceptación** | `SELECT booking_id, state FROM lumber_cost_distribution WHERE booking_id IS NOT NULL` → ≥ 1 registro con `state='draft'` |

**Método de ejecución:**
```python
cd = env['lumber.cost.distribution'].search([('name', '=', 'CD-2026-0002')], limit=1)
if not cd:
    cd = env['lumber.cost.distribution'].create({
        'name': 'CD-2026-0002',
        'target_model': 'booking',
        'booking_id': booking.id,
        'cost_line_ids': [(0, 0, {
            'cost_type': 'freight',
            'amount_original': 500.0,
            'distribution_method': 'volume_physical',
            'invoice_num': 'FAC-TEST-001',
            'invoice_date': fields.Date.today(),
        })]
    })
else:
    cd.booking_id = booking.id
```

### A-05 — [EJECUCIÓN] action_apply_costs()

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | Ejecutar `action_apply_costs()` y verificar creación de `stock.lot.cost.line` |
| **Modelo/Archivo** | `lumber.cost.distribution` (`custom_addons/madenat_lumber_costing/models/lumber_cost_distribution.py`) |
| **Dependencia** | A-04 completada |
| **Esfuerzo** | 0.5h |
| **Tipo** | Ejecución en Odoo shell |
| **Criterio de aceptación** | CD `state='applied'` + `SELECT count(*) FROM stock_lot_cost_line WHERE amount_usd > 0` → ≥ 1 |

```python
cd.action_apply_costs()
env.cr.commit()
# Verificar
print(cd.state)  # debe ser 'applied'
print(env['stock.lot.cost.line'].search_count([('distribution_id', '=', cd.id)]))
```

### A-06 — [VALIDACIÓN] Verificar generación de stock.landed.cost

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | Confirmar que `_generate_landed_costs()` se disparó y creó `stock.landed.cost` |
| **Modelo/Archivo** | `stock.landed.cost` con herencia MADENAT (`custom_addons/madenat_lumber_costing/models/stock_landed_cost.py`) |
| **Dependencia** | A-05 completada |
| **Esfuerzo** | 0.5h |
| **Tipo** | Validación SQL + Odoo shell |
| **Criterio de aceptación** | `SELECT count(*) FROM stock_landed_cost WHERE madenat_distribution_id IS NOT NULL` → ≥ 1 |

```python
lc = env['stock.landed.cost'].search([('madenat_distribution_id', '=', cd.id)])
print(len(lc), lc.state)  # debe ser ≥1, state='draft'
```

### A-07 — [EJECUCIÓN] button_validate() sobre stock.landed.cost

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | Validar landed cost y verificar `account.move` + `stock.valuation.layer` |
| **Modelo/Archivo** | `stock.landed.cost` → `account.move` → `stock.valuation.layer` |
| **Dependencia** | A-06 completada |
| **Esfuerzo** | 0.5h |
| **Tipo** | Ejecución en Odoo shell |
| **Criterio de aceptación** | `SELECT count(*) FROM account_move am JOIN stock_landed_cost slc ON am.stock_landed_cost_id = slc.id WHERE am.state='posted'` → ≥ 1 |

```python
# ⚠️ Pre-requisito: verificar cuentas contables configuradas
product = lots[0].product_id
print(product.property_stock_account_input.id)  # debe existir
print(product.categ_id.property_stock_account_input.id)  # fallback

lc.button_validate()
env.cr.commit()
print(lc.state)  # debe ser 'done'
```

### A-08 — [PATCH] Cambiar `total_cost_usd` a store=True

| Campo | Valor |
|-------|-------|
| **Prioridad** | P1 |
| **Objetivo** | `total_cost_usd` persiste en BD y se recalcula automáticamente |
| **Modelo/Archivo** | `stock.lot` — archivo: `custom_addons/madenat_lumber_core/models/stock_lot.py` |
| **Dependencia** | A-02 completada (datos existen para backfill) |
| **Esfuerzo** | 3h |
| **Tipo** | Patch de modelo + script de backfill SQL |
| **Criterio de aceptación** | `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NOT NULL AND total_cost_usd >= 0` → 100% de lotes |

**Pasos técnicos:**

1. Localizar la definición de `total_cost_usd` en `stock_lot.py`:
```
total_cost_usd = fields.Monetary(
    currency_field='currency_id',
    compute='_compute_total_cost_usd',
    store=False,  # ← cambiar a True
    ...
)
```

2. Cambiar `store=False` → `store=True`.

3. Verificar que `@api.depends` incluye `'wood_cost_usd', 'cost_line_ids.amount_usd'`.

4. Actualizar el módulo: `docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --stop-after-init`.

5. Ejecutar backfill SQL para lotes existentes:
```sql
UPDATE stock_lot
SET total_cost_usd = wood_cost_usd + (
    SELECT COALESCE(SUM(slcl.amount_usd), 0)
    FROM stock_lot_cost_line slcl
    WHERE slcl.lot_id = stock_lot.id
)
WHERE total_cost_usd IS NULL OR total_cost_usd = 0;
```

6. Verificar: `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NULL OR total_cost_usd = 0` → 0.

### A-09 — [PATCH] Agregar `account_id` a `stock.lot.cost.line`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P2 |
| **Objetivo** | Permitir imputación contable por tipo de costo |
| **Modelo/Archivo** | `stock.lot.cost.line` — archivo: `custom_addons/madenat_lumber_core/models/stock_lot_cost_line.py` |
| **Dependencia** | Ninguna (independiente) |
| **Esfuerzo** | 1.5h |
| **Tipo** | Patch de modelo + vista XML |
| **Criterio de aceptación** | Campo `account_id` visible y funcional en formulario de línea de costo |

**Pasos técnicos:**

1. Agregar campo en `stock_lot_cost_line.py`:
```python
account_id = fields.Many2one(
    'account.account',
    string='Cuenta Contable',
    help="Cuenta contable para imputación de este costo. Si no se asigna, Odoo usa la cuenta del producto."
)
```

2. Agregar a la vista XML correspondiente (posiblemente `stock_lot_cost_line_views.xml` o heredar vista Odoo).

3. Actualizar módulo.

### A-10 — [REFACTOR] Redirigir `_deprecated_action_distribute_costs` a `cost_line_ids`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P2 |
| **Objetivo** | Unificar trazabilidad de costos logísticos vía `stock.lot.cost.line` |
| **Modelo/Archivo** | `lumber_shipment_costing.py` en `custom_addons/madenat_lumber_logistics/models/` |
| **Dependencia** | A-05 completada (cost_line_ids funcional confirmado) |
| **Esfuerzo** | 3h |
| **Tipo** | Refactor de método |
| **Criterio de aceptación** | `SELECT count(*) FROM stock_lot_cost_line WHERE cost_type='logistic'` → ≥ 1 tras ejecutar distribución |

**Pasos técnicos:**

1. Localizar `_deprecated_action_distribute_costs` en `lumber_shipment_costing.py`.

2. Reemplazar la escritura directa a `stock.lot.logistic_cost_usd` por creación de `stock.lot.cost.line`:
```python
# Antes (bypassea trazabilidad):
# lot.logistic_cost_usd = calculated_value

# Después (trazable):
self.env['stock.lot.cost.line'].create({
    'lot_id': lot.id,
    'amount_usd': calculated_value,
    'cost_type': 'logistic',
    'date': fields.Date.today(),
})
```

3. Cambiar `logistic_cost_usd` de `fields.Monetary` manual a compute desde `cost_line_ids` filtrado por `cost_type='logistic'`.

4. Limpiar valores legacy: `UPDATE stock_lot SET logistic_cost_usd = 0 WHERE id IN (SELECT lot_id FROM stock_lot_cost_line WHERE cost_type='logistic')`.

### A-11 — [VALIDACIÓN] Verificar pipeline `vol_shipment_m3`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P2 |
| **Objetivo** | `vol_shipment_m3` calculado correctamente para lotes en embarque |
| **Modelo/Archivo** | `stock.lot`, `lumber.shipment.line` — archivos: `stock_lot.py`, `lumber_shipment_line.py` |
| **Dependencia** | A-03 completada (contenedores con lotes) |
| **Esfuerzo** | 3h |
| **Tipo** | Validación + posible fix de cálculo |
| **Criterio de aceptación** | Lotes en contenedores de embarque tienen `vol_shipment_m3 > 0` y coincide con cálculo de `lumber_shipment_line` |

**Pasos técnicos:**

1. Verificar query: `SELECT sl.id, sl.vol_shipment_m3, lc.id as container_id FROM stock_lot sl JOIN lumber_container_lot_rel lclr ON sl.id = lclr.stock_lot_id JOIN lumber_container lc ON lc.id = lclr.lumber_container_id WHERE lc.booking_id IS NOT NULL`.

2. Si `vol_shipment_m3 = 0`, revisar `_compute_vol_shipment_m3` en `lumber_shipment_line.py` y verificar que el compute se dispara.

3. Documentar si el cálculo depende de dimensiones de embarque (ancho_embarque, largo_embarque) que deben estar pobladas en `lumber.shipment.line`.

### A-12 — [VALIDACIÓN] Verificar cost_per_m3_usd y cost_per_mbf_usd con datos reales

| Campo | Valor |
|-------|-------|
| **Prioridad** | P2 |
| **Objetivo** | Validar que la corrección de Fase A produce valores correctos con datos reales |
| **Modelo/Archivo** | `stock.lot` — archivo: `stock_lot.py` |
| **Dependencia** | A-02 + A-05 completadas |
| **Esfuerzo** | 0.5h |
| **Tipo** | Validación SQL |
| **Criterio de aceptación** | `cost_per_m3_usd ≈ total_cost_usd / volumen_m3` (error ≤ 0.01) en ≥ 3 lotes |

```sql
SELECT
    id, name,
    total_cost_usd,
    volumen_m3,
    cost_per_m3_usd,
    ROUND(total_cost_usd::numeric / NULLIF(volumen_m3, 0), 4) AS expected,
    ABS(cost_per_m3_usd - ROUND(total_cost_usd::numeric / NULLIF(volumen_m3, 0), 4)) AS error
FROM stock_lot
WHERE total_cost_usd > 0 AND volumen_m3 > 0
LIMIT 10;
```

### A-13 — [VALIDACIÓN] Verificar seed data de lumber.export.formula

| Campo | Valor |
|-------|-------|
| **Prioridad** | P2 |
| **Objetivo** | Confirmar 3 perfiles activos (f5085, f1550, metric) |
| **Modelo/Archivo** | `lumber.export.formula` — seed: `custom_addons/madenat_lumber_core/data/ingestion_seed_fase3.xml` |
| **Dependencia** | Ninguna (independiente) |
| **Esfuerzo** | 0.5h |
| **Tipo** | Validación SQL + posible carga manual |
| **Criterio de aceptación** | `SELECT profile, active FROM lumber_export_formula` → 3 registros activos |

```sql
-- Si faltan, cargar desde seed:
-- Verificar que ingestion_seed_fase3.xml tiene forcecreate="True"
-- O crear manualmente en Odoo shell:
env['lumber.export.formula'].create({
    'profile': 'f5085', 'formula_kind': 'blank_clear', 'unit_mode': 'imperial_feet',
    'principal_factor': 5085.312, 'deduction_factor': 0.0625,
    's2s_adjustment_mode': 'none', 'mbf_divisor': 12000.0, 'active': True,
})
```

### A-14 — [AUDITORÍA] Verificar doble conteo en `_compute_total_cost_usd` de costing

| Campo | Valor |
|-------|-------|
| **Prioridad** | P3 |
| **Objetivo** | Confirmar que `total_cost_usd` no suma dos veces `logistic_cost_usd` |
| **Modelo/Archivo** | `stock_lot_costing.py` en `custom_addons/madenat_lumber_costing/models/` |
| **Dependencia** | A-10 completada (refactor logistics) |
| **Esfuerzo** | 1.5h |
| **Tipo** | Auditoría de código + test unitario |
| **Criterio de aceptación** | `total_cost_usd` = `wood_cost_usd` + `sum(cost_line_ids.amount_usd)` sin duplicación. Test: lote con `wood_cost_usd=100` + 2 cost_lines (50+30) → `total_cost_usd=180` |

### A-15 — [DECISIÓN FUNCIONAL] Fuente de verdad para costo base en el reporte

| Campo | Valor |
|-------|-------|
| **Prioridad** | P3 |
| **Objetivo** | Negocio define si el reporte muestra `wood_cost_usd` o `purchase_amount_usd` como costo base |
| **Modelo/Archivo** | Decisión documental — impacto en `stock.lot` views y reportes |
| **Dependencia** | Ninguna |
| **Esfuerzo** | 0h técnica (reunión funcional) |
| **Tipo** | Decisión funcional |
| **Criterio de aceptación** | Respuesta documentada en CANON/08_COSTEO.md §1.2 |

### A-16 — [LIMPIEZA] Eliminar `purchase_cost_usd` de vistas del reporte

| Campo | Valor |
|-------|-------|
| **Prioridad** | P3 |
| **Objetivo** | El reporte muestra `wood_cost_usd` (fuente de verdad), no `purchase_cost_usd` (deprecado) |
| **Modelo/Archivo** | Vistas de reporte y formulario de `stock.lot` |
| **Dependencia** | DF-02 resuelta |
| **Esfuerzo** | 0.5h |
| **Tipo** | Ajuste de vistas XML |
| **Criterio de aceptación** | Reporte generado sin columna `purchase_cost_usd` |

### A-17 — [HARDCODE FIX] Reemplazar `25.4` por `MM_PER_INCH`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P4 |
| **Objetivo** | Centralizar constantes de conversión imperial |
| **Modelo/Archivo** | `lumber_shipment_line.py:78,123`, `lumber_reception_mass_update.py:114`, `utils_uom.py:132` |
| **Dependencia** | Ninguna (independiente) |
| **Esfuerzo** | 1h |
| **Tipo** | Reemplazo de literales |
| **Criterio de aceptación** | `grep -rn "25\.4" custom_addons/madenat_lumber_*/models/*.py` → solo debe aparecer en la definición de `MM_PER_INCH` en `utils_uom.py` |

### A-18 — [UI] Agregar `total_cost_usd` a vistas de lote

| Campo | Valor |
|-------|-------|
| **Prioridad** | P4 |
| **Objetivo** | Operador ve costo total del lote en UI |
| **Modelo/Archivo** | `stock_lot_views.xml` en `custom_addons/madenat_lumber_core/views/` |
| **Dependencia** | A-08 completada (total_cost_usd store=True) |
| **Esfuerzo** | 0.5h |
| **Tipo** | Ajuste de vista XML |
| **Criterio de aceptación** | `total_cost_usd` visible en tree y form de `stock.lot` con `widget='monetary'` |

### A-19 — [TESTS] Crear test suite para `madenat_guia_processing`

| Campo | Valor |
|-------|-------|
| **Prioridad** | P4 |
| **Objetivo** | Cobertura de tests para el modelo de 3465 líneas |
| **Modelo/Archivo** | `madenat_guia_processing.py` → nuevo archivo: `tests/test_guia_processing.py` |
| **Dependencia** | Ninguna (independiente, paralelizable) |
| **Esfuerzo** | 12h |
| **Tipo** | Desarrollo de tests |
| **Criterio de aceptación** | ≥ 12 casos de prueba cubriendo: creación, flujo estados, staging→lotes, validación picking, cancelación, cálculos |

---

# 3. SECUENCIA DE EJECUCIÓN

## 3.1 Orden estricto (dependencias secuenciales)

```
DF-01 (decisión funcional)
  │
  ▼
A-02 (asignar wood_cost_usd)
  │
  ▼
A-03 (crear booking + contenedor + lotes)
  │
  ▼
A-04 (vincular booking a distribución)
  │
  ▼
A-05 (action_apply_costs)
  │
  ├──────────────────────┐
  ▼                      ▼
A-06 (verificar          A-08 (total_cost_usd store=True)
  landed cost)             │
  │                      ▼
  ▼                      A-12 (validar cost_per_m3/mbf)
A-07 (button_validate)
  │
  ▼
A-10 (refactor logistics → cost_line_ids)
  │
  ▼
A-14 (auditar doble conteo en costing)
  │
  ▼
DF-02 (decisión funcional)
  │
  ▼
A-16 (limpiar purchase_cost_usd del reporte)
```

## 3.2 Tareas paralelizables (sin dependencia del flujo principal)

| Tarea | Puede empezar | Tipo de recurso |
|-------|--------------|-----------------|
| A-09 (account_id en cost_line) | Inmediato | Developer |
| A-13 (seed export formula) | Inmediato | Developer / DBA |
| A-17 (hardcodes 25.4) | Inmediato | Developer |
| A-18 (UI total_cost_usd) | Tras A-08 | Developer |
| A-19 (tests guia_processing) | Inmediato | Developer independiente |

## 3.3 Hitos de validación (puntos de control)

| Hito | Tras completar | Qué verificar |
|------|---------------|---------------|
| **H1** — Flujo runtime desbloqueado | A-07 | `account.move` posted desde landed cost, `stock.valuation.layer` creado |
| **H2** — Datos persistentes | A-08 + A-12 | `total_cost_usd` store, `cost_per_m3_usd` validado |
| **H3** — Trazabilidad unificada | A-10 + A-14 | `cost_line_ids` como fuente única, sin doble conteo |
| **H4** — Sistema listo para reporte | A-16 | Reporte de valorización generado con columnas monetarias pobladas |

---

# 4. RIESGOS Y MITIGACIONES

## 4.1 Riesgos funcionales

| Riesgo | Impacto | Probabilidad | Mitigación | Responsable |
|--------|---------|-------------|------------|-------------|
| DF-01 sin respuesta del negocio | Bloquea toda la Fase 1 | Alta | Escalar a liderazgo de proyecto. Definir un valor default temporal (`wood_cost_usd = purchase.order.price_unit`) solo para continuidad técnica | Project Manager |
| `button_validate` falla por falta de cuentas contables | Bloquea A-07 | Media | **Pre-check antes de A-07**: verificar `product.property_stock_account_input` y `product.categ_id.property_stock_account_input`. Si faltan, configurar antes de validar | Developer |
| Lotes sin `reception_id.picking_id` no generan landed cost | Limita alcance de A-06 | Media | Documentado como limitación de diseño (C3.2). Solo lotes de `lumber.reception` (no `guia.processing`) generan landed cost. Si se necesita para guías, extender `_generate_landed_costs()` | Tech Lead |

## 4.2 Riesgos técnicos

| Riesgo | Impacto | Probabilidad | Mitigación | Responsable |
|--------|---------|-------------|------------|-------------|
| Backfill de `total_cost_usd` store=True falla | Lotes con `total_cost_usd = 0` o NULL | Baja | Ejecutar en transacción con savepoint. Validar post-migración. Tener script de rollback listo | Developer |
| Refactor logistics (A-10) rompe `madenat_lumber_billing` | Billing lee costos de lote incorrectos | Baja | Billing ya usa `total_cost_usd` (compute) y Monetary. Verificar con test de billing post-refactor | Developer |
| Constraint `stock_lot_check_cost_positive` se activa tras store=True | Bloquea lotes legacy con costo 0 | Baja | Relajar constraint a `CHECK(total_cost_usd >= 0)` o aplicarla solo a lotes `recepcionado`. Ajustar en `stock_lot.py` | Developer |

## 4.3 Riesgos de validación

| Riesgo | Impacto | Probabilidad | Mitigación | Responsable |
|--------|---------|-------------|------------|-------------|
| Entorno DEV no tiene cuentas contables configuradas | A-07 no se puede ejecutar | Media | Instalar chart of accounts chileno (`l10n_cl`) o configurar manualmente cuentas mínimas. Verificar con `account.account` search | DevOps / Developer |
| Docker no disponible para validación SQL | No se pueden ejecutar queries de verificación | Baja | Tener acceso directo a PostgreSQL del contenedor `odoo18_db`. Alternativa: Odoo shell con `env.cr.execute()` | DevOps |

---

# 5. CHECKLIST DE VALIDACIÓN

## 5.1 Evidencia runtime requerida (por hito)

### H1 — Flujo runtime desbloqueado
- [ ] `SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0` → ≥ 10 — **Screenshot del tree view de lotes con wood_cost_usd > 0**
- [ ] `SELECT state FROM lumber_cost_distribution WHERE name='CD-2026-0002'` → `applied` — **Screenshot de la distribución en estado applied**
- [ ] `SELECT count(*) FROM stock_lot_cost_line WHERE amount_usd > 0` → ≥ 1 — **Screenshot de cost_line_ids en un lote**
- [ ] `SELECT count(*) FROM stock_landed_cost WHERE madenat_distribution_id IS NOT NULL` → ≥ 1 — **Screenshot del landed cost en UI**
- [ ] `SELECT count(*) FROM account_move WHERE stock_landed_cost_id IS NOT NULL AND state='posted'` → ≥ 1 — **Screenshot del account.move (asiento contable)**
- [ ] `SELECT count(*) FROM stock_valuation_layer WHERE stock_landed_cost_id IS NOT NULL` → ≥ 1 — **Screenshot del valuation layer**

### H2 — Datos persistentes
- [ ] `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NOT NULL AND total_cost_usd > 0` → = total de lotes — **Query de verificación**
- [ ] Validación de `cost_per_m3_usd ≈ total_cost_usd / volumen_m3` en ≥ 3 lotes — **Log del script de validación**

### H3 — Trazabilidad unificada
- [ ] `SELECT count(*) FROM stock_lot_cost_line WHERE cost_type='logistic'` → ≥ 1 — **Screenshot**
- [ ] Test unitario de doble conteo: `wood_cost_usd=100 + cost_lines(50+30) → total_cost_usd=180` — **Output del test**

### H4 — Sistema listo
- [ ] Reporte de valorización exportadora generado con ≥ 1 lote con columnas monetarias pobladas — **PDF del reporte**
- [ ] Reporte no muestra `purchase_cost_usd` — **PDF del reporte**
- [ ] 23 tests existentes pasando — **Output de `run_tests.sh`**

## 5.2 Evidencia documental requerida

- [ ] CANON/08_COSTEO.md actualizado con decisión DF-01 (origen de `wood_cost_usd`) — **Commit**
- [ ] CANON/08_COSTEO.md actualizado con decisión DF-02 (fuente de verdad costo base) — **Commit**
- [ ] CHANGELOG.md de `madenat_lumber_core` actualizado con cambio `total_cost_usd store=True` — **Commit**
- [ ] CHANGELOG.md de `madenat_lumber_logistics` actualizado con refactor de distribución de costos — **Commit**
- [ ] `stock_lot_cost_line.py` documentado: `account_id` agregado con help text — **Código**

## 5.3 Pruebas mínimas para considerar cerrada cada fase

| Fase | Prueba |
|------|--------|
| Fase 1 | Flujo end-to-end ejecutado 1 vez desde Odoo shell con `env.cr.commit()` exitoso |
| Fase 2 | `run_tests.sh` pasando (23 tests + tests de regresión) |
| Fase 3 | `cost_per_m3_usd` validado en ≥ 3 lotes, sin doble conteo verificado |
| Fase 4 | `grep -rn "25\.4" custom_addons/` → solo en definición de `MM_PER_INCH` |

---

# 6. CONCLUSIÓN EJECUTIVA

## 6.1 ¿El sistema ya puede seguir adelante?

**Sí**, con condiciones. El sistema tiene base técnica sólida: pipeline de recepción funcional, modelo de costos implementado, 17 campos Monetary migrados, 23 tests pasando. Lo que falta **no es código nuevo** — es operación: asignar datos reales y ejecutar los flujos ya implementados.

Las 7 primeras acciones (A-01 a A-07, ~6h de trabajo) desbloquean el flujo runtime completo y permiten generar el primer `account.move` desde MADENAT. Esto es el hito más importante del plan.

## 6.2 Qué falta para cerrar el ciclo completo

| Entregable | Acciones requeridas | Esfuerzo |
|------------|-------------------|----------|
| Flujo runtime | A-01 a A-07 | 6h |
| Datos persistentes | A-08 + A-12 | 3.5h |
| Trazabilidad unificada | A-09 + A-10 + A-14 | 6h |
| Decisiones funcionales | DF-01 + DF-02 | Reuniones |
| Reporte generable | A-13 + A-16 + A-18 | 1.5h |
| Hardening | A-17 + A-19 | 13h |
| **Total** | | **~30h + reuniones** |

## 6.3 Esfuerzo restante estimado

| Grupo | Horas |
|-------|-------|
| Acciones técnicas (ejecución inmediata) | 18h |
| Acciones de validación | 5h |
| Refactor + hardening | 14.5h |
| Decisiones funcionales | 2 reuniones (1h c/u) |
| **Total** | **~39.5h** |

## 6.4 Recomendación de ejecución inmediata

1. **Hoy**: Concertar reunión para resolver DF-01 (origen de `wood_cost_usd`). Sin esto, nada avanza.
2. **En paralelo**: Ejecutar A-09 (`account_id`), A-13 (seed export formula), A-17 (hardcodes).
3. **Tras DF-01**: Ejecutar A-02 a A-07 en secuencia (~5h continuas). Esto produce el primer `account.move` desde MADENAT.
4. **Siguiente sprint**: A-08 (`total_cost_usd` store) + A-10 (refactor logistics) + A-12 (validación cost_per).
5. **Deuda técnica**: A-19 (tests guia_processing, 12h) se puede paralelizar con un developer independiente durante todo el proceso.

---

*Plan de acción generado: 2026-06-05 — basado en PLAN_DEPURACION_PRIORIZADO.md*
*Enfoque: ejecución real, acciones concretas, scripts y comandos específicos*