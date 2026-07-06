# GUÍA OPERATIVA DE IMPLEMENTACIÓN — MADENAT Lumber
## Ejecución controlada del plan A-01 a A-19
### Derivado de PLAN_ACCION_EJECUTABLE.md (2026-06-05)

**Fecha:** 2026-06-05
**Tipo:** Guía operativa paso a paso para el equipo técnico en DEV
**Base:** PLAN_ACCION_EJECUTABLE.md (19 acciones, 4 fases, 39.5h)
**Entorno:** DEV — madenat_test (Docker: odoo18_app + odoo18_db)

---

# 1. MAPA OPERATIVO DE EJECUCIÓN

## 1.1 Punto de arranque real

El equipo puede iniciar **hoy mismo** con 5 acciones independientes (Fase 0). La Fase 1 (desbloqueo runtime) requiere primero resolver DF-01.

```
FASE 0 (ARRANQUE INMEDIATO — sin dependencias)
  ├── A-09  account_id en stock.lot.cost.line
  ├── A-13  verificar seed lumber.export.formula
  ├── A-17  hardcodes 25.4 → MM_PER_INCH
  ├── A-19  tests madenat_guia_processing (paralelo, developer independiente)
  └── A-11  verificar vol_shipment_m3 (si hay datos de embarque)

BLOQUEO: DF-01 (origen de wood_cost_usd) ─── REUNIÓN FUNCIONAL REQUERIDA

FASE 1 (DESBLOQUEO RUNTIME — requiere DF-01 resuelta)
  ├── A-02  asignar wood_cost_usd > 0
  ├── A-03  crear booking + contenedor + lotes
  ├── A-04  vincular booking a CD-2026-0002
  ├── A-05  action_apply_costs()
  ├── A-06  verificar stock.landed.cost generado
  └── A-07  button_validate() → account.move

FASE 2 (PERSISTENCIA Y CÁLCULOS)
  ├── A-08  total_cost_usd store=True + backfill
  ├── A-12  validar cost_per_m3_usd / cost_per_mbf_usd
  ├── A-10  refactor logistics → cost_line_ids
  └── A-18  total_cost_usd en UI de lote

FASE 3 (CALIDAD Y NORMALIZACIÓN)
  ├── A-14  auditar doble conteo en costing
  ├── DF-02 decisión fuente de verdad costo base
  └── A-16  limpiar purchase_cost_usd del reporte
```

## 1.2 Acciones bloqueadas hasta resolver DF-01

| Acción | Qué bloquea | Por qué |
|--------|------------|---------|
| A-02 | Asignar `wood_cost_usd` | Sin definición funcional del origen, no se sabe qué valor ni de dónde tomar el dato |
| A-03 | Crear booking + contenedor | Depende de A-02 (lotes con wood_cost_usd) |
| A-04 | Vincular booking a CD | Depende de A-03 |
| A-05 | action_apply_costs() | Depende de A-04 |
| A-06 | Verificar landed cost | Depende de A-05 |
| A-07 | button_validate() | Depende de A-06 |

**Conclusión:** Sin DF-01, 6 de 19 acciones (31%) están bloqueadas. Son las de mayor impacto.

## 1.3 Acciones bloqueadas hasta resolver DF-02

| Acción | Qué bloquea | Por qué |
|--------|------------|---------|
| A-16 | Limpiar `purchase_cost_usd` del reporte | Sin definición de cuál es la fuente de verdad, no se sabe qué columna mostrar |

DF-02 no es urgente — puede resolverse en Fase 3 sin detener Fase 1 ni Fase 2.

## 1.4 Agrupación por fases

| Fase | Acciones | Esfuerzo | Depende de | Entregable |
|------|---------|----------|------------|------------|
| **Fase 0** — Arranque inmediato | A-09, A-13, A-17, A-19, A-11 | 16.5h | Ninguna | Deuda técnica reducida, seed data verificada |
| **Fase 1** — Desbloqueo runtime | A-02, A-03, A-04, A-05, A-06, A-07 | 6h | DF-01 | Primer `account.move` desde MADENAT |
| **Fase 2** — Persistencia y cálculos | A-08, A-12, A-10, A-18 | 7.5h | Fase 1 completada | `total_cost_usd` store, logistics refactorizado |
| **Fase 3** — Calidad y normalización | A-14, DF-02, A-16 | 3h | Fase 2 completada + DF-02 | Sin doble conteo, reporte limpio |

---

# 2. GUÍA DE EJECUCIÓN POR ACCIÓN

## FASE 0 — ARRANQUE INMEDIATO (ejecutar hoy)

### A-09 — Agregar `account_id` a `stock.lot.cost.line`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Permitir imputación contable por tipo de costo en líneas de distribución |
| **Prioridad** | P2 |
| **Dependencias** | Ninguna |
| **Archivo/Modelo** | `custom_addons/madenat_lumber_core/models/stock_lot_cost_line.py` |
| **Tipo** | Patch de modelo + vista XML |
| **Esfuerzo** | 1.5h |

**Pasos concretos:**

1. Abrir `stock_lot_cost_line.py`. Agregar tras los campos existentes:
```python
account_id = fields.Many2one(
    'account.account',
    string='Cuenta Contable',
    help="Cuenta contable para imputar este costo. Si se deja vacío, Odoo usará "
         "la cuenta de inventario del producto (property_stock_account_input)."
)
```

2. Actualizar `__init__.py` si el campo requiere import adicional (no debería; `account.account` es estándar).

3. Agregar el campo a la vista de línea de costo. Verificar si existe `stock_lot_cost_line_views.xml`. Si no existe, crear vista tree+form mínima o heredar la vista por defecto de Odoo.

4. Actualizar módulo:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --stop-after-init
```

5. Verificar en UI: abrir un `stock.lot.cost.line` (si existe) o crear uno y confirmar que el campo `account_id` aparece.

**Evidencia esperada:** Screenshot del formulario de `stock.lot.cost.line` mostrando el campo `account_id`.

**Criterio de aceptación:** `account_id` visible y funcional en formulario. `SELECT column_name FROM information_schema.columns WHERE table_name='stock_lot_cost_line' AND column_name='account_id'` → 1 fila.

---

### A-13 — Verificar seed data de `lumber.export.formula`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Confirmar que los 3 perfiles de fórmula están activos en BD |
| **Prioridad** | P2 |
| **Dependencias** | Ninguna |
| **Archivo/Modelo** | `lumber.export.formula` — seed: `custom_addons/madenat_lumber_core/data/ingestion_seed_fase3.xml` |
| **Tipo** | Validación SQL + carga manual si falta |
| **Esfuerzo** | 0.5h |

**Pasos concretos:**

1. Verificar en PostgreSQL:
```sql
SELECT id, profile, formula_kind, active FROM lumber_export_formula ORDER BY profile;
```

2. Si hay 3 filas con `active=true` → **OK, acción cerrada.**

3. Si faltan, cargar desde Odoo shell:
```python
# Verificar primero si el seed XML se ejecutó
# Si no, crear manualmente:
formulas = [
    {'profile': 'f5085', 'formula_kind': 'blank_clear', 'unit_mode': 'imperial_feet',
     'principal_factor': 5085.312, 'deduction_factor': 0.0625, 's2s_adjustment_mode': 'none'},
    {'profile': 'f1550', 'formula_kind': 's2s_imperial', 'unit_mode': 'imperial_meters',
     'principal_factor': 1550.003, 'deduction_factor': 0.0, 's2s_adjustment_mode': 'per_width'},
    {'profile': 'metric', 'formula_kind': 'metric_direct', 'unit_mode': 'metric_mm',
     'principal_factor': 1000000.0, 'deduction_factor': 0.0, 's2s_adjustment_mode': 'none'},
]
for f in formulas:
    existing = env['lumber.export.formula'].search([('profile', '=', f['profile'])])
    if not existing:
        env['lumber.export.formula'].create({**f, 'mbf_divisor': 12000.0, 'active': True})
env.cr.commit()
```

**Evidencia esperada:** `SELECT profile, active FROM lumber_export_formula` → 3 filas con `active=t`.

**Criterio de aceptación:** 3 registros activos.

---

### A-17 — Reemplazar hardcodes `25.4` por `MM_PER_INCH`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Centralizar constantes de conversión imperial en `utils_uom.py` |
| **Prioridad** | P4 |
| **Dependencias** | Ninguna |
| **Archivos afectados** | `lumber_shipment_line.py:78,123`, `lumber_reception_mass_update.py:114`, `utils_uom.py:132` |
| **Tipo** | Reemplazo de literales |
| **Esfuerzo** | 1h |

**Pasos concretos:**

1. `custom_addons/madenat_lumber_logistics/models/lumber_shipment_line.py`:
   - Línea ~78: `line.lot_id.ancho_mm / 25.4` → `line.lot_id.ancho_mm / MM_PER_INCH`
   - Línea ~123: `adjusted_width_inch * 25.4` → `adjusted_width_inch * MM_PER_INCH`
   - Agregar al inicio: `from odoo.addons.madenat_lumber_core.models.utils_uom import MM_PER_INCH`

2. `custom_addons/madenat_lumber_core/wizard/lumber_reception_mass_update.py`:
   - Línea ~114: `return round(inches * 25.4, 2)` → `return round(inches * MM_PER_INCH, 2)`
   - Agregar import: `from ..models.utils_uom import MM_PER_INCH`

3. `custom_addons/madenat_lumber_core/models/utils_uom.py`:
   - Línea ~132: `float(decimal_value) * 25.4` → `float(decimal_value) * float(MM_PER_INCH)`

4. Verificar que no quedan hardcodes:
```bash
grep -rn "25\.4" custom_addons/madenat_lumber_core/models/ custom_addons/madenat_lumber_logistics/models/
```
Debe aparecer **solo** en la definición de `MM_PER_INCH = 25.4` en `utils_uom.py`.

5. Ejecutar tests de regresión:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core,madenat_lumber_logistics --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "PASS|FAIL"
```

**Evidencia esperada:** Output del grep mostrando solo `MM_PER_INCH = 25.4` en `utils_uom.py`.

**Criterio de aceptación:** Cero hardcodes `25.4` fuera de la definición de la constante. Tests pasando.

---

### A-19 — Crear test suite para `madenat_guia_processing`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Cobertura de tests para modelo de 3465 líneas sin tests |
| **Prioridad** | P4 |
| **Dependencias** | Ninguna |
| **Archivos** | Nuevo: `custom_addons/madenat_lumber_core/tests/test_guia_processing.py` |
| **Tipo** | Desarrollo de tests |
| **Esfuerzo** | 12h |

**Pasos concretos:**

1. Crear archivo `test_guia_processing.py` en `custom_addons/madenat_lumber_core/tests/`.

2. Casos mínimos requeridos (12):
   - TC01: Crear guía en estado `draft`
   - TC02: `action_verify_data()` — parseo de Excel simulado
   - TC03: `action_assign_commercial_defaults()` — nominales asignados
   - TC04: `action_process_from_staging()` → staging → lotes
   - TC05: `do_full_processing()` — creación de `stock.lot` con dimensiones
   - TC06: `action_validate()` — picking creado, movimientos confirmados
   - TC07: Flujo completo `draft → verified → processed → validated`
   - TC08: `action_force_cancel()` con estado `processed`
   - TC09: `unlink()` solo permite `draft` y `cancelled`
   - TC10: Cálculo de volúmenes (`vol_comercial`, `vol_fisico`, diferencias)
   - TC11: `_sync_purchase_order_lines()` — sincronización con OC
   - TC12: `_get_or_create_picking_unified()` — no duplica pickings

3. Registrar en `tests/__init__.py`:
```python
from . import test_guia_processing
```

4. Ejecutar:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "test_guia|PASS|FAIL"
```

**Evidencia esperada:** Output con 12 tests pasando.

**Criterio de aceptación:** ≥ 12 tests, todos PASS. Archivo `test_guia_processing.py` existe en el repositorio.

**Nota:** Esta acción es paralelizable con TODAS las demás. Puede asignarse a un developer independiente desde hoy.

---

### A-11 — Verificar pipeline `vol_shipment_m3`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Confirmar que `vol_shipment_m3` se calcula para lotes en embarque |
| **Prioridad** | P2 |
| **Dependencias** | Requiere datos de embarque (contenedores con lotes). Si no existen, no se puede ejecutar aún |
| **Archivos** | `stock_lot.py`, `lumber_shipment_line.py` |
| **Tipo** | Validación SQL + diagnóstico |
| **Esfuerzo** | 3h |

**Pasos concretos:**

1. Verificar si existen contenedores con lotes:
```sql
SELECT lc.id, lc.name, COUNT(lclr.stock_lot_id) AS lotes
FROM lumber_container lc
JOIN lumber_container_lot_rel lclr ON lc.id = lclr.lumber_container_id
GROUP BY lc.id, lc.name;
```

2. Si `lotes = 0` para todos, esta acción **no puede ejecutarse aún**. Pasa a estado "pendiente de datos" y retómala tras A-03.

3. Si hay lotes, verificar `vol_shipment_m3`:
```sql
SELECT sl.id, sl.name, sl.vol_shipment_m3, sl.volumen_m3
FROM stock_lot sl
JOIN lumber_container_lot_rel lclr ON sl.id = lclr.stock_lot_id
WHERE sl.vol_shipment_m3 IS NULL OR sl.vol_shipment_m3 = 0;
```

4. Si la query devuelve filas, el cálculo no se está disparando. Revisar `_compute_vol_shipment_m3` en `lumber_shipment_line.py` y verificar sus `@api.depends`.

**Evidencia esperada:** Query mostrando `vol_shipment_m3 > 0` para lotes en contenedores.

**Criterio de aceptación:** Lotes en embarque tienen `vol_shipment_m3 > 0`.

---

## FASE 1 — DESBLOQUEO RUNTIME (tras DF-01)

### ⚠️ PRERREQUISITO: DF-01 — Origen de `wood_cost_usd`

**Antes de ejecutar A-02, el negocio debe responder:**

> ¿De dónde se obtiene el valor de `wood_cost_usd` para cada lote?

| Opción | Fuente | Script en A-02 |
|--------|--------|----------------|
| A | `purchase.order.line.price_unit` × `volumen_m3` | Opción A del script |
| B | PDF de guía de despacho parseado | Requiere lógica adicional de parseo |
| C | Ingreso manual por operador en UI | Usar wizard `lumber_reception_mass_update` |

**Si el negocio no responde en 48h, usar Opción A como default técnico para continuidad.** Documentar la decisión temporal en `CANON/08_COSTEO.md`.

---

### A-02 — Asignar `wood_cost_usd > 0` a lotes existentes

| Campo | Valor |
|-------|-------|
| **Objetivo** | Poblar `wood_cost_usd > 0` en ≥ 10 lotes con recepción y picking |
| **Prioridad** | P1 |
| **Dependencias** | DF-01 resuelta |
| **Archivo/Modelo** | `stock.lot` — `custom_addons/madenat_lumber_core/models/stock_lot.py` |
| **Tipo** | Script Python (Odoo shell) |
| **Esfuerzo** | 1h |

**Pasos concretos:**

1. Entrar al shell de Odoo:
```bash
docker exec -it odoo18_app odoo shell -d madenat_test
```

2. Ejecutar script según la opción elegida en DF-01:

**Opción A (desde purchase.order):**
```python
lots = env['stock.lot'].search([
    ('reception_id', '!=', False),
    ('picking_ids', '!=', False),
    ('wood_cost_usd', '=', 0.0)
], limit=20)

updated = 0
for lot in lots:
    reception = lot.reception_id
    if reception.order_id:
        po_line = reception.order_id.order_line.filtered(
            lambda l: l.product_id == lot.product_id
        )
        if po_line:
            lot.wood_cost_usd = po_line.price_unit * lot.volumen_m3
            updated += 1

env.cr.commit()
print(f"Lotes actualizados: {updated}")
```

**Opción B (valor fijo de prueba — solo si Opción A no es viable):**
```python
lots = env['stock.lot'].search([
    ('reception_id', '!=', False),
    ('picking_ids', '!=', False),
    ('wood_cost_usd', '=', 0.0)
], limit=20)

for lot in lots:
    lot.wood_cost_usd = 620.0  # valor USD de prueba

env.cr.commit()
print(f"Lotes actualizados: {len(lots)}")
```

**Verificación post-ejecución:**
```sql
SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0 AND reception_id IS NOT NULL;
```

**Evidencia esperada:** Screenshot del tree view de `stock.lot` mostrando `wood_cost_usd > 0`. Query SQL con count ≥ 10.

**Criterio de aceptación:** ≥ 10 lotes con `wood_cost_usd > 0` y `reception_id` no nulo.

---

### A-03 — Crear booking + contenedor + asignar lotes

| Campo | Valor |
|-------|-------|
| **Objetivo** | Tener booking con ≥ 1 contenedor que contenga lotes con `wood_cost_usd > 0` |
| **Prioridad** | P1 |
| **Dependencias** | A-02 completada |
| **Archivos/Modelos** | `shipping.booking` (`madenat_lumber_shipping_core`), `lumber.container` (`madenat_lumber_logistics`) |
| **Tipo** | Script Python (Odoo shell) |
| **Esfuerzo** | 1.5h |

**Pasos concretos (Odoo shell, misma sesión que A-02):**

```python
# Usar los lotes ya actualizados en A-02
lots_with_cost = env['stock.lot'].search([
    ('wood_cost_usd', '>', 0),
    ('reception_id', '!=', False)
], limit=10)

# Crear booking
booking = env['shipping.booking'].create({
    'name': 'EMB-DEV-0001',
    'partner_id': lots_with_cost[0].reception_id.partner_id.id or 1,
})

# Crear contenedor con los lotes
container = env['lumber.container'].create({
    'name': 'CONT-DEV-001',
    'booking_id': booking.id,
    'lot_ids': [(6, 0, lots_with_cost.ids)],
})

env.cr.commit()
print(f"Booking: {booking.name}, Contenedor: {container.name}, Lotes: {len(container.lot_ids)}")
```

**Verificación:**
```sql
SELECT lc.name AS contenedor, sb.name AS booking, COUNT(lclr.stock_lot_id) AS lotes
FROM lumber_container lc
JOIN shipping_booking sb ON lc.booking_id = sb.id
JOIN lumber_container_lot_rel lclr ON lc.id = lclr.lumber_container_id
GROUP BY lc.name, sb.name;
```

**Evidencia esperada:** Screenshot del contenedor en UI mostrando lotes asignados. Query con ≥ 1 contenedor con ≥ 1 lote.

**Criterio de aceptación:** Booking con ≥ 1 contenedor, contenedor con ≥ 1 lote con `wood_cost_usd > 0`.

---

### A-04 — Vincular booking a distribución de costos

| Campo | Valor |
|-------|-------|
| **Objetivo** | CD-2026-0002 con `booking_id` apuntando a booking con contenedores y lotes |
| **Prioridad** | P1 |
| **Dependencias** | A-03 completada |
| **Archivo/Modelo** | `lumber.cost.distribution` — `custom_addons/madenat_lumber_costing/models/lumber_cost_distribution.py` |
| **Tipo** | Script Python (Odoo shell) |
| **Esfuerzo** | 0.5h |

**Pasos concretos (misma sesión de shell):**

```python
cd = env['lumber.cost.distribution'].search([('name', '=', 'CD-2026-0002')], limit=1)

if cd:
    cd.write({
        'booking_id': booking.id,
        'target_model': 'booking',
    })
else:
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

env.cr.commit()
print(f"CD: {cd.name}, booking_id: {cd.booking_id.name}, state: {cd.state}")
print(f"Líneas de costo: {len(cd.cost_line_ids)}")
```

**Verificación:**
```sql
SELECT name, state, booking_id, target_model FROM lumber_cost_distribution WHERE booking_id IS NOT NULL;
```

**Evidencia esperada:** Screenshot de la distribución mostrando booking asignado.

**Criterio de aceptación:** CD con `booking_id` no nulo y `state='draft'`. Al menos 1 `cost_line_id` con `cost_type` y `amount_original > 0`.

---

### A-05 — Ejecutar `action_apply_costs()`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Aplicar distribución y crear `stock.lot.cost.line` |
| **Prioridad** | P1 |
| **Dependencias** | A-04 completada |
| **Archivo/Modelo** | `lumber.cost.distribution` → `stock.lot.cost.line` |
| **Tipo** | Ejecución en Odoo shell |
| **Esfuerzo** | 0.5h |

**Pasos concretos (misma sesión):**

```python
cd.action_apply_costs()
env.cr.commit()

# Verificaciones inmediatas
print(f"Estado CD: {cd.state}")  # debe ser 'applied'
cl_count = env['stock.lot.cost.line'].search_count([('distribution_id', '=', cd.id)])
print(f"Líneas de costo creadas: {cl_count}")

# Verificar que los lotes recibieron costos
for lot in cd.lot_ids[:3]:
    print(f"  Lote {lot.name}: cost_lines={len(lot.cost_line_ids)}, total_cost_usd={lot.total_cost_usd}")
```

**Qué hacer si falla:**
1. Verificar que `cd.lot_ids` no está vacío (debe cargarse vía onchange del booking).
2. Si `lot_ids` está vacío, asignar manualmente: `cd.write({'lot_ids': [(6, 0, container.lot_ids.ids)]})` y reintentar.
3. Si el error es de validación, leer el mensaje y corregir.

**Evidencia esperada:** `cd.state = 'applied'`. `stock.lot.cost.line` count ≥ 1.

**Criterio de aceptación:** CD en `applied`, ≥ 1 `stock.lot.cost.line` con `amount_usd > 0` creado por lote en la distribución.

---

### A-06 — Verificar generación de `stock.landed.cost`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Confirmar que `_generate_landed_costs()` se disparó y creó `stock.landed.cost` |
| **Prioridad** | P1 |
| **Dependencias** | A-05 completada |
| **Archivo/Modelo** | `stock.landed.cost` — `custom_addons/madenat_lumber_costing/models/stock_landed_cost.py` |
| **Tipo** | Validación en Odoo shell + SQL |
| **Esfuerzo** | 0.5h |

**Pasos concretos (misma sesión):**

```python
lc = env['stock.landed.cost'].search([('madenat_distribution_id', '=', cd.id)])
print(f"Landed costs generados: {len(lc)}")
for l in lc:
    print(f"  {l.name}: state={l.state}, pickings={l.picking_ids.mapped('name')}")
```

**Si `len(lc) == 0`:**
- Verificar que los lotes tienen `reception_id.picking_id`. Si no, esta es la limitación documentada C3.2 — lotes sin picking no generan landed cost.
- Opción: crear picking manualmente para esos lotes o aceptar la limitación.

**Verificación SQL:**
```sql
SELECT slc.id, slc.name, slc.state, slc.madenat_distribution_id,
       ARRAY_AGG(sp.name) AS pickings
FROM stock_landed_cost slc
LEFT JOIN stock_landed_cost_stock_picking_rel slcsp ON slc.id = slcsp.stock_landed_cost_id
LEFT JOIN stock_picking sp ON sp.id = slcsp.stock_picking_id
WHERE slc.madenat_distribution_id IS NOT NULL
GROUP BY slc.id;
```

**Evidencia esperada:** `stock.landed.cost` con `madenat_distribution_id` y `state='draft'`.

**Criterio de aceptación:** ≥ 1 `stock.landed.cost` generado con trazabilidad a la distribución.

---

### A-07 — Ejecutar `button_validate()` sobre `stock.landed.cost`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Validar landed cost → generar `account.move` posted + `stock.valuation.layer` |
| **Prioridad** | P1 |
| **Dependencias** | A-06 completada (landed cost existe) |
| **Archivo/Modelo** | `stock.landed.cost` → `account.move` → `stock.valuation.layer` |
| **Tipo** | Ejecución en Odoo shell |
| **Esfuerzo** | 0.5h |

**⚠️ PRECHECK obligatorio antes de validar:**

```python
# Verificar cuentas contables
product = cd.lot_ids[0].product_id
print(f"Producto: {product.name}")
print(f"  property_stock_account_input: {product.property_stock_account_input.id}")
print(f"  categ property_stock_account_input: {product.categ_id.property_stock_account_input.id}")

# Si ambos son None/False, button_validate va a fallar.
# Configurar cuenta mínima:
if not product.property_stock_account_input and not product.categ_id.property_stock_account_input:
    account = env['account.account'].search([('account_type', '=', 'asset_current')], limit=1)
    if account:
        product.categ_id.write({'property_stock_account_input': account.id})
        print(f"Cuenta configurada: {account.name}")
```

**Ejecutar validación:**

```python
lc = env['stock.landed.cost'].search([('madenat_distribution_id', '=', cd.id)], limit=1)
if lc and lc.state == 'draft':
    lc.button_validate()
    env.cr.commit()
    print(f"Landed cost state: {lc.state}")  # debe ser 'done'
else:
    print(f"LC no está en draft. State actual: {lc.state if lc else 'NO ENCONTRADO'}")
```

**Verificaciones post-validación:**

```python
# 1. Valuation layers
svl = env['stock.valuation.layer'].search([('stock_landed_cost_id', '=', lc.id)])
print(f"Valuation layers creados: {len(svl)}")

# 2. Account moves
am = svl.mapped('account_move_id')
print(f"Account moves: {len(am)}")
for m in am:
    print(f"  {m.name}: state={m.state}, date={m.date}, lines={len(m.line_ids)}")
    print(f"  Debe={sum(m.line_ids.mapped('debit'))}, Haber={sum(m.line_ids.mapped('credit'))}")
```

**Verificación SQL:**
```sql
SELECT am.name, am.state, am.date, COUNT(aml.id) AS lineas,
       SUM(aml.debit) AS debe, SUM(aml.credit) AS haber
FROM account_move am
JOIN account_move_line aml ON am.id = aml.move_id
WHERE am.stock_landed_cost_id IS NOT NULL
GROUP BY am.id;

SELECT count(*) FROM stock_valuation_layer WHERE stock_landed_cost_id IS NOT NULL;
```

**Evidencia esperada:** `account.move` en estado `posted`. `stock.valuation.layer` vinculado al landed cost. Debe = Haber.

**Criterio de aceptación:** ≥ 1 `account.move` posted desde landed cost. ≥ 1 `stock.valuation.layer` con `stock_landed_cost_id`. **Este es el hito H1 — flujo runtime desbloqueado.**

---

## FASE 2 — PERSISTENCIA Y CÁLCULOS (tras Fase 1)

### A-08 — Cambiar `total_cost_usd` a `store=True`

| Campo | Valor |
|-------|-------|
| **Objetivo** | `total_cost_usd` persiste en BD y se recalcula automáticamente |
| **Prioridad** | P1 |
| **Dependencias** | A-02 completada (datos existen para backfill) |
| **Archivo/Modelo** | `stock.lot` — `custom_addons/madenat_lumber_core/models/stock_lot.py` |
| **Tipo** | Patch de modelo + backfill SQL |
| **Esfuerzo** | 3h |

**Pasos concretos:**

1. Abrir `stock_lot.py`. Buscar definición de `total_cost_usd`. Cambiar `store=False` → `store=True`.

2. Verificar que `@api.depends` del método `_compute_total_cost_usd` incluye:
```python
@api.depends('wood_cost_usd', 'cost_line_ids.amount_usd')
```
Si no incluye `'cost_line_ids.amount_usd'`, agregarlo.

3. Actualizar módulo:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --stop-after-init
```

4. Ejecutar backfill SQL para lotes existentes (fuera de Odoo, directo en PostgreSQL):
```sql
BEGIN;
UPDATE stock_lot
SET total_cost_usd = wood_cost_usd + (
    SELECT COALESCE(SUM(slcl.amount_usd), 0)
    FROM stock_lot_cost_line slcl
    WHERE slcl.lot_id = stock_lot.id
)
WHERE total_cost_usd IS NULL OR total_cost_usd = 0;
COMMIT;
```

5. Verificar:
```sql
SELECT count(*) AS total,
       count(*) FILTER (WHERE total_cost_usd IS NULL) AS nulos,
       count(*) FILTER (WHERE total_cost_usd = 0) AS ceros
FROM stock_lot;
```
`nulos` y `ceros` deben ser 0.

6. Ejecutar tests de regresión:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "FAIL|ERROR"
```
Si aparecen FAIL, revisar si la constraint `stock_lot_check_cost_positive` está bloqueando. Relajar si es necesario:
```sql
ALTER TABLE stock_lot DROP CONSTRAINT IF EXISTS stock_lot_check_cost_positive;
ALTER TABLE stock_lot ADD CONSTRAINT stock_lot_check_cost_positive CHECK(total_cost_usd >= 0);
```

**Evidencia esperada:** Query mostrando 0 nulos y 0 ceros. Tests pasando.

**Criterio de aceptación:** `total_cost_usd` persiste. Backfill ejecutado sin errores. Tests pasando.

---

### A-12 — Validar `cost_per_m3_usd` y `cost_per_mbf_usd` con datos reales

| Campo | Valor |
|-------|-------|
| **Objetivo** | Confirmar que la corrección de Fase A produce cálculos correctos en runtime |
| **Prioridad** | P2 |
| **Dependencias** | A-02 + A-05 + A-08 completadas |
| **Archivo/Modelo** | `stock.lot` — `stock_lot.py` |
| **Tipo** | Validación SQL |
| **Esfuerzo** | 0.5h |

**Validación SQL:**
```sql
SELECT
    name,
    ROUND(total_cost_usd::numeric, 2) AS total_usd,
    ROUND(volumen_m3::numeric, 4) AS vol_m3,
    ROUND(cost_per_m3_usd::numeric, 2) AS cost_m3,
    ROUND((total_cost_usd / NULLIF(volumen_m3, 0))::numeric, 2) AS expected_m3,
    ABS(ROUND(cost_per_m3_usd::numeric, 2) - ROUND((total_cost_usd / NULLIF(volumen_m3, 0))::numeric, 2)) AS error_m3,
    ROUND(cost_per_mbf_usd::numeric, 2) AS cost_mbf,
    ROUND((total_cost_usd / NULLIF(volumen_mbf, 0))::numeric, 2) AS expected_mbf
FROM stock_lot
WHERE total_cost_usd > 0 AND volumen_m3 > 0
LIMIT 10;
```

**Criterio:** `error_m3 ≤ 0.01` para ≥ 3 lotes.

**Evidencia esperada:** Output de la query con errores ≤ 0.01.

**Criterio de aceptación:** Cálculo validado en ≥ 3 lotes. Si hay discrepancias > 0.01, documentar y evaluar si es problema de redondeo o bug.

---

### A-10 — Refactorizar `_deprecated_action_distribute_costs` → `cost_line_ids`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Unificar trazabilidad: costos logísticos usan `stock.lot.cost.line` |
| **Prioridad** | P2 |
| **Dependencias** | A-05 completada (confirma que cost_line_ids funciona) |
| **Archivo/Modelo** | `lumber_shipment_costing.py` — `custom_addons/madenat_lumber_logistics/models/` |
| **Tipo** | Refactor de método + limpieza de datos legacy |
| **Esfuerzo** | 3h |

**Pasos concretos:**

1. Abrir `lumber_shipment_costing.py`. Localizar `_deprecated_action_distribute_costs`.

2. Reemplazar escritura directa:
```python
# ANTES (eliminar o comentar):
# lot.logistic_cost_usd = calculated_value

# DESPUÉS:
self.env['stock.lot.cost.line'].create({
    'lot_id': lot.id,
    'amount_usd': calculated_value,
    'cost_type': 'logistic',
    'date': fields.Date.today(),
    'distribution_id': self.id if hasattr(self, 'distribution_id') else False,
})
```

3. Cambiar `logistic_cost_usd` en `stock_lot_costing.py` de campo manual a compute:
```python
logistic_cost_usd = fields.Monetary(
    currency_field='currency_id',
    compute='_compute_logistic_cost_usd',
    store=True,
    help="Costo logístico total (compute desde cost_line_ids con cost_type='logistic')"
)

@api.depends('cost_line_ids.amount_usd', 'cost_line_ids.cost_type')
def _compute_logistic_cost_usd(self):
    for lot in self:
        lot.logistic_cost_usd = sum(
            lot.cost_line_ids.filtered(lambda l: l.cost_type == 'logistic').mapped('amount_usd')
        )
```

4. Limpiar valores legacy en lotes que ahora tienen cost_line_ids de tipo logistic:
```sql
UPDATE stock_lot
SET logistic_cost_usd = 0
WHERE id IN (
    SELECT DISTINCT lot_id FROM stock_lot_cost_line WHERE cost_type = 'logistic'
);
```

5. Actualizar módulos:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_logistics,madenat_lumber_costing --stop-after-init
```

6. Ejecutar tests:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_logistics,madenat_lumber_costing --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "FAIL|ERROR"
```

**Evidencia esperada:** `SELECT count(*) FROM stock_lot_cost_line WHERE cost_type='logistic'` → ≥ 1.

**Criterio de aceptación:** Costos logísticos trazables vía `cost_line_ids`. `logistic_cost_usd` es compute desde `cost_line_ids`. Tests pasando.

---

### A-18 — Agregar `total_cost_usd` a vistas de lote

| Campo | Valor |
|-------|-------|
| **Objetivo** | Operador ve costo total del lote en UI |
| **Prioridad** | P4 |
| **Dependencias** | A-08 completada (`total_cost_usd` store=True) |
| **Archivo** | `stock_lot_views.xml` — `custom_addons/madenat_lumber_core/views/` |
| **Tipo** | Ajuste de vista XML |
| **Esfuerzo** | 0.5h |

**Pasos concretos:**

1. Abrir `stock_lot_views.xml`. Buscar el `<tree>` y `<form>` de `stock.lot`.

2. Agregar en el tree (entre los campos existentes):
```xml
<field name="total_cost_usd" widget="monetary" optional="show" sum="Total"/>
```

3. Agregar en el form (en el grupo de costos):
```xml
<field name="total_cost_usd" widget="monetary"/>
```

4. Actualizar módulo.

**Evidencia esperada:** Screenshot del tree view mostrando columna `total_cost_usd` con widget monetary.

**Criterio de aceptación:** `total_cost_usd` visible en tree (con suma) y form de `stock.lot`.

---

## FASE 3 — CALIDAD Y NORMALIZACIÓN (tras Fase 2)

### A-14 — Auditar doble conteo en `_compute_total_cost_usd` de costing

| Campo | Valor |
|-------|-------|
| **Objetivo** | Confirmar que `total_cost_usd` no suma dos veces `logistic_cost_usd` |
| **Prioridad** | P3 |
| **Dependencias** | A-10 completada |
| **Archivo** | `stock_lot_costing.py` — `custom_addons/madenat_lumber_costing/models/` |
| **Tipo** | Auditoría de código + test unitario |
| **Esfuerzo** | 1.5h |

**Pasos concretos:**

1. Abrir `stock_lot_costing.py`. Localizar `_compute_total_cost_usd`.

2. Verificar qué suma:
   - Si suma `logistic_cost_usd` y `logistic_cost_usd` ya es compute desde `cost_line_ids` (tras A-10) → **DOBLE CONTEO. Eliminar la suma.**
   - Si `logistic_cost_usd` es campo independiente (no compute desde cost_line_ids) → mantener.

3. Crear test unitario (agregar a `test_lot_costing.py` o crear nuevo):
```python
def test_no_double_count_total_cost(self):
    """Verifica que total_cost_usd no duplica logistic_cost_usd."""
    lot = self.env['stock.lot'].create({
        'name': 'TEST-NO-DOUBLE',
        'product_id': self.product.id,
        'wood_cost_usd': 100.0,
        'volumen_m3': 5.0,
    })
    # Agregar dos cost_lines: uno freight, uno logistic
    self.env['stock.lot.cost.line'].create([
        {'lot_id': lot.id, 'amount_usd': 50.0, 'cost_type': 'freight'},
        {'lot_id': lot.id, 'amount_usd': 30.0, 'cost_type': 'logistic'},
    ])
    # total_cost_usd debe ser 180, no 210
    self.assertEqual(lot.total_cost_usd, 180.0)
```

**Evidencia esperada:** Test pasando con `total_cost_usd = 180`. O documentación de que no hay doble conteo.

**Criterio de aceptación:** Sin doble conteo verificado. Test unitario pasando.

---

### DF-02 — Decisión funcional: fuente de verdad para costo base en reporte

| Campo | Valor |
|-------|-------|
| **Objetivo** | Negocio define si el reporte muestra `wood_cost_usd` o `purchase_amount_usd` como costo base |
| **Prioridad** | P3 |
| **Dependencias** | Ninguna |
| **Tipo** | Decisión funcional |
| **Esfuerzo** | Reunión 1h |

**Pregunta al negocio:**

> En el reporte de valorización exportadora, ¿qué campo debe aparecer como "Costo Base"?
> - (a) `wood_cost_usd` — valor manual/asignado por operador
> - (b) `purchase_amount_usd` — derivado de `volumen_m3 × purchase_price_usd_per_m3`

Recomendación técnica: `wood_cost_usd` como fuente de verdad. `purchase_amount_usd` como columna informativa adicional.

**Criterio de aceptación:** Decisión documentada en `CANON/08_COSTEO.md`.

---

### A-16 — Eliminar `purchase_cost_usd` de vistas del reporte

| Campo | Valor |
|-------|-------|
| **Objetivo** | El reporte muestra `wood_cost_usd`, no `purchase_cost_usd` (deprecado) |
| **Prioridad** | P3 |
| **Dependencias** | DF-02 resuelta |
| **Archivos** | Vistas de reporte en `madenat_lumber_reports` y vistas de `stock.lot` |
| **Tipo** | Ajuste de vistas XML |
| **Esfuerzo** | 0.5h |

**Pasos concretos:**

1. Buscar referencias a `purchase_cost_usd` en vistas de reporte:
```bash
grep -rn "purchase_cost_usd" custom_addons/madenat_lumber_reports/
```

2. Reemplazar por `wood_cost_usd` donde corresponda.

3. Si el reporte usaba `purchase_cost_usd` como fallback, eliminar el fallback y usar solo `wood_cost_usd`.

**Evidencia esperada:** Reporte generado sin columna `purchase_cost_usd`.

**Criterio de aceptación:** `grep -rn "purchase_cost_usd" custom_addons/madenat_lumber_reports/` → sin resultados.

---

# 3. SECUENCIA DE CONTROL

## 3.1 Checkpoints intermedios

| Checkpoint | Tras acción | Qué validar antes de continuar | Si falla |
|------------|------------|-------------------------------|----------|
| **CP-1** | DF-01 | Decisión documentada en CANON/08_COSTEO.md | No avanzar a Fase 1. Usar default temporal solo si urgencia > 48h |
| **CP-2** | A-02 | `SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0` ≥ 10 | Revisar script, verificar lotes con `reception_id` |
| **CP-3** | A-05 | `cd.state = 'applied'` y `stock_lot_cost_line` count > 0 | Ver `cd.lot_ids`, asignar manualmente si vacío |
| **CP-4** | A-07 | `account.move` posted y `stock.valuation.layer` creado | Verificar cuentas contables (precheck de A-07). Si falla, no es error de código, es configuración contable |
| **CP-5** | A-08 | `total_cost_usd` sin nulos ni ceros en BD | Rollback y revisar script de backfill |
| **CP-6** | A-10 + A-14 | Sin doble conteo, tests pasando | Revisar override de `_compute_total_cost_usd` |

## 3.2 Cuándo pasar de una fase a otra

| Transición | Condición |
|------------|-----------|
| Fase 0 → Fase 1 | DF-01 resuelta (o default temporal aceptado). Fase 0 puede continuar en paralelo |
| Fase 1 → Fase 2 | H1 alcanzado: `account.move` posted desde landed cost |
| Fase 2 → Fase 3 | A-08 completado sin errores, A-12 validado, tests pasando |

## 3.3 Validaciones pre-continuación

Antes de cada acción que modifica modelo o ejecuta flujo:
1. **Backup mental**: saber qué query de reversión aplicar si falla.
2. **Pre-check**: verificar precondiciones (cuentas contables, datos necesarios).
3. **Evidencia**: capturar screenshot o query antes y después.
4. **Commit**: `env.cr.commit()` solo tras verificar que el resultado es correcto.

---

# 4. VALIDACIÓN Y CIERRE

## 4.1 Consultas SQL de verificación (resumen)

| # | Query | Verifica |
|---|-------|----------|
| Q1 | `SELECT count(*) FROM stock_lot WHERE wood_cost_usd > 0 AND reception_id IS NOT NULL` | Costo base asignado |
| Q2 | `SELECT state FROM lumber_cost_distribution WHERE name='CD-2026-0002'` | Distribución aplicada |
| Q3 | `SELECT count(*) FROM stock_lot_cost_line WHERE amount_usd > 0` | Líneas de costo inyectadas |
| Q4 | `SELECT count(*) FROM stock_landed_cost WHERE madenat_distribution_id IS NOT NULL` | Landed cost generado |
| Q5 | `SELECT count(*) FROM account_move WHERE stock_landed_cost_id IS NOT NULL AND state='posted'` | Contabilidad generada |
| Q6 | `SELECT count(*) FROM stock_valuation_layer WHERE stock_landed_cost_id IS NOT NULL` | Valuation layers |
| Q7 | `SELECT count(*) FROM stock_lot WHERE total_cost_usd IS NULL OR total_cost_usd = 0` | Persistencia (debe ser 0) |
| Q8 | `SELECT profile, active FROM lumber_export_formula` | Seed data |
| Q9 | `SELECT count(*) FROM stock_lot_cost_line WHERE cost_type='logistic'` | Trazabilidad logística |

## 4.2 Qué confirma que el flujo ya está operativo

El sistema está operativo cuando se cumple **H1**:
- Q1 ≥ 10, Q2 = 'applied', Q3 ≥ 1, Q4 ≥ 1, Q5 ≥ 1, Q6 ≥ 1

**Esto significa que el flujo completo se ejecutó:**
```
lote con wood_cost_usd > 0
  → CD applied
  → stock.lot.cost.line creado
  → stock.landed.cost generado
  → button_validate exitoso
  → account.move posted
  → stock.valuation.layer creado
```

## 4.3 Evidencia del primer ciclo completo

| Evidencia | Formato |
|-----------|---------|
| Screenshot tree view `stock.lot` mostrando `wood_cost_usd > 0` | PNG |
| Screenshot `lumber.cost.distribution` en estado `applied` | PNG |
| Screenshot `stock.lot.cost.line` tree view con registros | PNG |
| Screenshot `stock.landed.cost` form view | PNG |
| Screenshot `account.move` (asiento contable) en estado `posted` | PNG |
| Screenshot `stock.valuation.layer` vinculado a landed cost | PNG |
| Output de `run_tests.sh` con 23 tests pasando | TXT |
| PDF del reporte de valorización exportadora (si ya se generó) | PDF |

---

# 5. RIESGOS DE EJECUCIÓN

## 5.1 Riesgos funcionales

| Riesgo | Criticidad | Si ocurre | Acción |
|--------|-----------|-----------|--------|
| DF-01 sin respuesta | **CRÍTICO** — bloquea 6 acciones | Sin `wood_cost_usd` no hay valores monetarios | Escalar a PM. Usar Opción A como default técnico temporal tras 48h. Documentar |
| DF-02 postergado | Medio — solo afecta A-16 | Reporte muestra campo legacy `purchase_cost_usd` | Aceptable temporalmente. No bloquea Fases 0-2 |
| `button_validate` falla por cuentas contables | Alto — bloquea A-07 | `account.move` no se genera | **Pre-check obligatorio.** Configurar `property_stock_account_input` antes de validar |

## 5.2 Riesgos técnicos

| Riesgo | Criticidad | Si ocurre | Acción |
|--------|-----------|-----------|--------|
| Backfill `total_cost_usd` falla | Medio | Lotes con valor NULL o 0 | Rollback. Ejecutar en transacción. Verificar locks en BD |
| Refactor A-10 rompe `madenat_lumber_billing` | Bajo | Billing muestra costos incorrectos | Billing usa `total_cost_usd` (compute). Si `logistic_cost_usd` ya está en `cost_line_ids`, el total lo refleja automáticamente. Verificar con test post-refactor |
| Constraint `stock_lot_check_cost_positive` bloquea tras store=True | Bajo | No se pueden guardar lotes legacy | Relajar constraint a `>= 0`. Ajustar en `stock_lot.py` |

## 5.3 Riesgos de avanzar sin resolver DF-01

Si se avanza sin DF-01 usando la Opción A (default técnico):
- ✅ El flujo runtime se desbloquea
- ✅ Se puede generar el primer `account.move`
- ⚠️ Los valores de `wood_cost_usd` serán `price_unit × volumen_m3`, que puede no coincidir con el costo real si el negocio usa otro criterio
- ⚠️ Si el negocio luego decide otra fuente, habrá que reasignar `wood_cost_usd` y recalcular

**Conclusión:** Avanzar con default técnico es aceptable para continuidad. La reasignación posterior es un script de 1h.

---

# 6. CONCLUSIÓN EJECUTIVA

## 6.1 ¿El plan ya puede ejecutarse de inmediato?

**Sí — la Fase 0 puede arrancar hoy.** 5 acciones (A-09, A-13, A-17, A-19, A-11) no tienen dependencias y pueden ejecutarse en paralelo.

La Fase 1 (las 6 acciones de mayor impacto) está bloqueada únicamente por DF-01. Si el negocio responde hoy, la Fase 1 se completa en ~6h continuas y se alcanza el hito H1: primer `account.move` desde MADENAT.

## 6.2 Dependencia más crítica

**DF-01 — Origen de `wood_cost_usd`.** Es la única decisión que bloquea 6 de 19 acciones (31%) incluyendo todas las de la Fase 1. Sin ella, el sistema no puede generar valores monetarios reales.

## 6.3 Esfuerzo restante estimado

| Fase | Acciones | Esfuerzo | Puede empezar |
|------|---------|----------|---------------|
| Fase 0 | A-09, A-11, A-13, A-17, A-19 | 18h | **HOY** |
| Fase 1 | A-02 a A-07 | 6h | Tras DF-01 |
| Fase 2 | A-08, A-12, A-10, A-18 | 7.5h | Tras Fase 1 |
| Fase 3 | A-14, DF-02, A-16 | 3h | Tras Fase 2 |
| **Total** | **19 acciones** | **~34.5h** | |

## 6.4 Primeras 5 acciones inmediatas (para arrancar hoy)

| # | Acción | Esfuerzo | Tipo | ¿Lista? |
|---|--------|----------|------|---------|
| 1 | **DF-01** — Concertar reunión con negocio para definir origen de `wood_cost_usd` | 1h reunión | Decisión | 📅 Agendar hoy |
| 2 | **A-17** — Reemplazar hardcodes `25.4` por `MM_PER_INCH` | 1h | Código | ✅ Ejecutable ya |
| 3 | **A-13** — Verificar seed data `lumber.export.formula` | 0.5h | SQL | ✅ Ejecutable ya |
| 4 | **A-09** — Agregar `account_id` a `stock.lot.cost.line` | 1.5h | Código | ✅ Ejecutable ya |
| 5 | **A-19** — Iniciar test suite `madenat_guia_processing` | 12h | Código | ✅ Asignar a developer |

---

*Guía operativa generada: 2026-06-05 — basada en PLAN_ACCION_EJECUTABLE.md*
*Enfoque: ejecución disciplinada, verificable, con checkpoints y criterios de cierre concretos*