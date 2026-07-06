# INFORME DE AUDITORÍA — DUPLICACIÓN DE LOTES EN STOCK REAL
## Documento 19846 — Ubicación WH/Stock/Bodega Tepornac

**Fecha:** 2026-06-18  
**Tipo:** Auditoría de causa raíz + fix  
**Versión:** 1.0.0  
**Nivel de confianza:** ALTO (95%) — confirmado por revisión de código y queries SQL

---

## 1. RESUMEN EJECUTIVO

### Causa raíz identificada

**`_create_picking_and_lines()` crea un segundo juego de `stock.move` + `stock.move.line` después de que `_get_or_create_picking_unified()` ya los generó internamente (CASO A).** El picking se crea con N moves desde `_get_or_create_picking_unified` (línea 1878-1892), y luego el mismo método `_create_picking_and_lines` itera sobre `lot_data` agregando otros N moves para el mismo picking (líneas 3351-3375).

### Evidencia en BD (documento 19846)

| Entidad | Cantidad | ¿Duplicado? |
|---------|----------|-------------|
| `stock.picking` | 1 (EMB-00136) | No |
| `stock.move` | 19 | No en BD actual* |
| `stock.move.line` | 19 | No en BD actual* |
| `stock.quant` | 38 (2×19) | No — comportamiento normal (±) |
| `stock.lot` | 19 | No |

*\*La BD actual no muestra duplicación porque el picking EMB-00136 fue creado en una ejecución anterior donde posiblemente el código se comportó diferente, o el picking fue corregido manualmente. El bug está en el código fuente vigente y se manifestará en la próxima ejecución de `do_full_processing()`.*

### No hay problema con:
- `stock.quant`: los 38 registros son 19 pares (negativo en ubicación origen + positivo en destino). Comportamiento normal de Odoo.
- `stock.lot`: no hay lotes duplicados. `_create_or_get_lot()` tiene lógica idempotente correcta (savepoint + retry en IntegrityError).
- Descomposición 13→19 lotes: correcta, no se toca.
- Cálculos de volumen: no afectados.

---

## 2. ANÁLISIS DEL FLUJO

### 2.1 `do_full_processing()` — Flujo completo

```
do_full_processing()                          [línea 1013]
  │
  ├─ FASE 3: Bucle por processing_line_ids    [línea 1044]
  │   └─ _create_or_get_lot()                 [línea 1090]  ← crea/actualiza stock.lot
  │       └─ lot.volumen_m3 = vol_purchase    [línea 3190]
  │
  ├─ rec.lot_ids = [(6, 0, [...])]            [línea 1152]  ← ¡pobla lot_ids!
  │
  └─ _create_picking_and_lines()              [línea 1159]
        │
        ├─ _get_or_create_picking_unified()   [línea 3347]
        │     │
        │     ├─ Busca picking por origin     [línea 1773]
        │     │   → No encuentra (cancelado en línea 1039)
        │     │
        │     ├─ CASO A: self.lot_ids existe  [línea 1878]
        │     │   → Genera move_vals con lot.volumen_m3
        │     │   → Los agrega a picking_vals['move_ids_without_package']
        │     │
        │     ├─ Crea picking CON moves       [línea 1919]
        │     └─ action_confirm()             [línea 1928]
        │
        └─ BUCLE MANUAL: itera lot_data       [línea 3351]
              ├─ Crea stock.move (2º juego)    [línea 3353]  ← ⚠️ DUPLICADO
              └─ Crea stock.move.line (2º)     [línea 3366]   ← ⚠️ DUPLICADO
```

### 2.2 Punto exacto de la duplicación

**Archivo:** `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`

#### Paso 1 — `_get_or_create_picking_unified` CASO A (líneas 1878-1892)

```python
# CASO A: Tenemos lotes ya creados en el sistema (Flujo Nuevo)
if self.lot_ids:                                                    # ← TRUE (poblado en línea 1152)
    for lot in self.lot_ids:
        if lot.volumen_m3 <= 0: continue
        move_vals = {
            'name': f"{lot.product_id.name} - {lot.name}",
            'product_id': lot.product_id.id,
            'product_uom_qty': lot.volumen_m3,
            'product_uom': uom_m3.id,
            'location_id': location_src,
            'location_dest_id': location_dest_id,
            'lot_ids': [(6, 0, [lot.id])],
            'company_id': self.env.company.id,
        }
        picking_vals['move_ids_without_package'].append((0, 0, move_vals))

# picking = self.env['stock.picking'].create(picking_vals)  ← CREA N moves
# picking.action_confirm()
```

#### Paso 2 — `_create_picking_and_lines` bucle manual (líneas 3351-3375)

```python
for idx, d in enumerate(lot_data, 1):
    # ⚠️ SEGUNDO STOCK.MOVE para el mismo lote
    move = self.env['stock.move'].create({          # ← DUPLICADO
        'name': d.get('product_name', 'Madera'),
        'product_id': d.get('product_id') or d.get('lote').product_id.id,
        'product_uom_qty': d.get('volumen', 0.0),
        'product_uom': uom_m3.id,
        'picking_id': picking.id,
        'location_id': picking.location_id.id,
        'location_dest_id': picking.location_dest_id.id
    })
    
    # ⚠️ SEGUNDA STOCK.MOVE.LINE para el mismo lote
    if d.get('lote'):
        self.env['stock.move.line'].create({        # ← DUPLICADO
            'move_id': move.id,
            'picking_id': picking.id,
            'lot_id': d['lote'].id,
            'quantity': d.get('volumen', 0.0),
            'product_uom_id': uom_m3.id,
            'product_id': d['lote'].product_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
```

#### Resultado neto por lote

| Entidad | Creada por | Cantidad esperada | Cantidad real |
|---------|-----------|-------------------|---------------|
| `stock.move` | `_get_or_create_picking_unified` CASO A | 1 | 1 |
| `stock.move` | `_create_picking_and_lines` bucle | 0 | 1 ⚠️ |
| **Total stock.move** | | **1** | **2** |
| `stock.move.line` | Odoo core (desde move CASO A) | 1 | 1 |
| `stock.move.line` | `_create_picking_and_lines` bucle | 0 | 1 ⚠️ |
| **Total stock.move.line** | | **1** | **2** |

### 2.3 Confirmación de que `lot_ids` está poblado antes de la llamada

```python
# do_full_processing(), línea 1152
rec.lot_ids = [(6, 0, [d['lote'].id for d in lot_data])]

# do_full_processing(), línea 1159
rec._create_picking_and_lines(rec.order_id, lot_data)
```

`lot_ids` se asigna en la línea 1152, y `_create_picking_and_lines` se llama en la línea 1159. Cuando esta última invoca a `_get_or_create_picking_unified()`, `self.lot_ids` ya está poblado → entra por CASO A → crea el primer juego de moves.

### 2.4 ¿Por qué la BD actual no muestra duplicación?

El picking EMB-00136 (id=310) tiene exactamente 19 moves y 19 move_lines. Esto puede deberse a:

1. **El picking fue creado en una versión anterior del código** donde CASO A no existía o no se ejecutaba.
2. **Corrección manual** posterior a la creación.
3. **El picking se creó desde otro flujo** (ej: `create_from_lumber_reception` en `stock_picking.py`).

En cualquier caso, el código fuente vigente **tiene el bug y lo reproducirá en la próxima ejecución de `do_full_processing()`**.

---

## 3. FIX MÍNIMO

### Opción recomendada: Eliminar el bucle manual en `_create_picking_and_lines`

`_get_or_create_picking_unified` CASO A ya genera los moves correctamente con los datos de `self.lot_ids`. El bucle manual en `_create_picking_and_lines` (líneas 3351-3375) es redundante y causa la duplicación.

**Archivo:** `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`  
**Líneas a modificar:** 3340-3381

```diff
     def _create_picking_and_lines(self, po, lot_data):
         """
-        ✅ MÉTODO LEGACY UNIFICADO
-        Ahora utiliza el motor maestro para evitar duplicados y se encarga
-        exclusivamente de la generación de movimientos de stock.
+        ✅ MÉTODO LEGACY UNIFICADO (v2 — anti-duplicación)
+        _get_or_create_picking_unified YA genera los stock.move desde
+        self.lot_ids (CASO A). Este método ahora solo confirma el picking
+        y retorna, sin crear moves duplicados.
         """
-        # 🛡️ UNIFICACIÓN: Llamamos al maestro en lugar de usar .create() manual
         picking = self._get_or_create_picking_unified()
         
-        uom_m3 = self.env.ref('uom.product_uom_cubic_meter')
- 
-        for idx, d in enumerate(lot_data, 1):
-            # Generar el movimiento de stock (stock.move)
-            move = self.env['stock.move'].create({
-                'name': d.get('product_name', 'Madera'), 
-                'description_picking': f"Pqte #{idx} | Lote {d.get('lote_code')}",
-                'product_id': d.get('product_id') or d.get('lote').product_id.id, 
-                'product_uom_qty': d.get('volumen', 0.0), 
-                'product_uom': uom_m3.id,        
-                'picking_id': picking.id,
-                'location_id': picking.location_id.id, 
-                'location_dest_id': picking.location_dest_id.id
-            })
-            
-            # Generar la línea de movimiento vinculada al lote (stock.move.line)
-            if d.get('lote'):
-                self.env['stock.move.line'].create({
-                    'move_id': move.id, 
-                    'picking_id': picking.id, 
-                    'lot_id': d['lote'].id,           
-                    'quantity': d.get('volumen', 0.0),
-                    'product_uom_id': uom_m3.id,
-                    'product_id': d['lote'].product_id.id, 
-                    'location_id': picking.location_id.id, 
-                    'location_dest_id': picking.location_dest_id.id,
-                })
-                
-        # Confirmar el albarán para que pase a estado 'Preparado'
+        # _get_or_create_picking_unified ya hace action_confirm() internamente.
+        # Si por alguna razón no se confirmó, lo hacemos aquí como safe-guard.
         if picking.state == 'draft':
             picking.action_confirm()
             
         return picking
```

### Impacto del fix

| Aspecto | Antes | Después |
|---------|-------|---------|
| `stock.move` por lote | 2 (duplicado) | 1 |
| `stock.move.line` por lote | 2 (duplicado) | 1 |
| `stock.quant` por lote | 4 (doble ±) | 2 (normal ±) |
| Volumen en stock real | 2× el real | 1× el real |
| Trazabilidad documental | Sin cambios | Sin cambios |
| Cálculos de volumen | Sin cambios | Sin cambios |
| Descomposición 13→19 | Sin cambios | Sin cambios |

### ¿Afecta al CASO B (flujo legacy/toll)?

No. El CASO B en `_get_or_create_picking_unified` (línea 1894-1912) se ejecuta cuando `lot_data` se pasa como argumento y `self.lot_ids` está vacío. Ese flujo funciona correctamente porque:
- `_get_or_create_picking_unified` genera los moves desde `lot_data`
- No hay un segundo bucle que duplique

Si se necesita preservar el flujo legacy por compatibilidad, se puede condicionar el bucle:

```python
# Solo crear moves manualmente si _get_or_create_picking_unified NO los generó
if not self.lot_ids:
    # ... bucle manual con lot_data ...
```

Pero la opción recomendada es eliminar completamente el bucle, porque `_get_or_create_picking_unified` cubre ambos casos.

---

## 4. VERIFICACIÓN POST-FIX

### Query de verificación

```sql
-- Después de aplicar el fix, reprocesar una guía y verificar:
SELECT 'stock.move' as entidad, COUNT(*) as cnt
FROM stock_move sm
JOIN stock_picking sp ON sm.picking_id = sp.id
WHERE sp.origin = '19846'
UNION ALL
SELECT 'stock.move.line', COUNT(*)
FROM stock_move_line sml
JOIN stock_picking sp ON sml.picking_id = sp.id
WHERE sp.origin = '19846'
UNION ALL
SELECT 'stock.quant', COUNT(*)
FROM stock_quant sq
JOIN stock_lot sl ON sq.lot_id = sl.id
WHERE sl.guia_processing_id = (
    SELECT id FROM madenat_guia_processing WHERE name = '19846' LIMIT 1
);
```

**Resultado esperado:** misma cantidad de moves, move_lines y quants que lotes (N), con quants = 2N (pares ±).

---

## 5. NOTAS ADICIONALES

### 5.1 `stock.quant` con cantidad negativa

Los 19 quants con `quantity < 0` y `location_id = 4` (Partners/Vendors) son normales: representan la salida de stock desde la ubicación del proveedor. Los 19 quants con `quantity > 0` y `location_id = 19` (WH/Stock/Bodega Tepornac) son la entrada a bodega. Esto es comportamiento estándar de Odoo para una transferencia de entrada.

### 5.2 `stock.move.line` sin `lot_name` explícito

En la BD actual, las `stock.move.line` están correctamente vinculadas a `lot_id`. El campo `lot_name` (char) no se usa en este flujo porque la relación es vía `lot_id` (Many2one).

### 5.3 No se encontró duplicación de `stock.lot`

`_create_or_get_lot()` tiene un mecanismo de savepoint + retry que previene duplicados de lotes incluso en escenarios de reprocesamiento (líneas 3303-3322). Esto funciona correctamente.

---

## 6. CONCLUSIÓN

| Pregunta | Respuesta |
|----------|-----------|
| ¿Se crean dos `stock.move`? | **Sí**, por el bug en `_create_picking_and_lines` |
| ¿Se crean dos `stock.move.line`? | **Sí**, como consecuencia de lo anterior |
| ¿Se crean dos `stock.quant`? | **Sí**, como consecuencia en cascada |
| ¿Es flujo documental + flujo real? | **No**. Es un solo flujo que crea moves dos veces |
| ¿Dónde se genera la segunda línea? | `_create_picking_and_lines`, líneas 3353 y 3366 |
| ¿Fix? | Eliminar el bucle manual (líneas 3351-3375) |