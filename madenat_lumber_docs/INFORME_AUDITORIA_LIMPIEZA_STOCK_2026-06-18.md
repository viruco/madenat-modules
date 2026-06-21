# INFORME DE AUDITORÍA COMPLETA DE STOCK — LIMPIEZA CONTROLADA
## Fecha: 2026-06-18 | BD: madenat_test

---

## 1. RESUMEN EJECUTIVO

### Diagnóstico

La base de datos `madenat_test` tiene **38 lotes huérfanos** en `stock_lot` — ninguno tiene `reception_id` ni `guia_processing_id` poblados. Estos lotes provienen de **dos ejecuciones consecutivas** del flujo de la guía `19846`:

| Lote | IDs | Cantidad | technical_validation | create_date | Origen |
|------|-----|----------|---------------------|-------------|--------|
| Batch 1 (reversado) | 1605–1623 | 19 | `pending` | 2026-04-03 | Procesamiento original, luego revertido |
| Batch 2 (reprocesado) | 1993–2011 | 19 | `approved` | 2026-06-18 | Reprocesamiento post-reversa |

### Hallazgos críticos

1. **38 lotes huérfanos**: Ninguno tiene FK de origen (`reception_id` o `guia_processing_id`).
2. **10 quants con stock positivo** (47.15 m³ en WH/Stock/Bodega Tepornac) de los lotes 1614-1623.
3. **19 cost lines** asociadas a lotes huérfanos.
4. **Stock moves/move_lines duplicados** en picking `EMB-00132` (28 moves para 10 lotes distintos — algunos lotes tienen hasta 5 moves).
5. **3 pickings con REVERTIDO/ANULADO**: EMB-00113 (done), EMB-00136 (done), EMB-00133 (cancel).
6. **137 moves done sin origin** — residuos de flujos de retorno (Return of).
7. **La guía 19846 está en `draft`** con contadores a cero, lista para reprocesar.

### Decisión

- **NO hay trazabilidad válida que conservar** en ninguno de los 38 lotes: todos son huérfanos.
- La BD está en un estado de testing, sin operación real en curso.
- La limpieza completa de los 38 lotes y sus registros asociados es segura y no rompe ninguna cadena de trazabilidad válida.

---

## 2. CLASIFICACIÓN COMPLETA

### 2A. Tabla de clasificación — stock.lot

| ID | Lote | Validación | Vol (m³) | Piezas | Stock (quants) | Clasificación | Motivo |
|----|------|-----------|---------|--------|----------------|--------------|--------|
| 1605 | D7731 PCLAT04201253250 19846 | pending | 3.656 | 200 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1606 | D7739 PCLAT04201453250 19846 | pending | 0.276 | 13 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1607 | D7739 PCLAT04201453200 19846 | pending | 0.752 | 36 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1608 | D7739 PCLAT04201452900 19846 | pending | 2.384 | 126 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1609 | D7732 PCLAT04201453250 19846 | pending | 3.711 | 175 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1610 | D7602 PCLAT04201003250 19846 | pending | 1.843 | 126 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1611 | D7602 PCLAT04201002900 19846 | pending | 1.618 | 124 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1612 | D7733 PCLAT04201453250 19846 | pending | 3.711 | 175 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1613 | D7734 PCLAT04201453250 19846 | pending | 3.711 | 175 | 0.000 | Huérfano | Batch 1 post-reversa, sin FK de origen |
| 1614 | D7633 PCLAT04201454050 19846 | pending | 4.625 | 175 | 5.425 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1615 | D7735 PCLAT04201403250 19846 | pending | 3.583 | 175 | 7.163 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1616 | D7736 PCLAT04201403250 19846 | pending | 3.583 | 175 | 7.163 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1617 | D7730 PCLAT04200752500 19846 | pending | 2.742 | 325 | 5.482 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1618 | D7738 PCLAT04201203250 19846 | pending | 1.685 | 96 | 3.375 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1619 | D7738 PCLAT04201203200 19846 | pending | 1.797 | 104 | 3.597 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1620 | D7737 PCLAT04201403700 19846 | pending | 2.121 | 91 | 4.241 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1621 | D7737 PCLAT04201403250 19846 | pending | 1.720 | 84 | 3.440 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1622 | D7630 PCLAT04201253250 19846 | pending | 2.194 | 120 | 4.384 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1623 | D7630 PCLAT04201253200 19846 | pending | 1.440 | 80 | 2.880 | Huérfano + Residuo | Con quants zombie (stock falso) |
| 1993 | D7731 PCLAT04201253250 19846 | approved | 3.656 | 200 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1605 |
| 1994 | D7739 PCLAT04201453250 19846 | approved | 0.276 | 13 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1606 |
| 1995 | D7739 PCLAT04201453200 19846 | approved | 0.752 | 36 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1607 |
| 1996 | D7739 PCLAT04201452900 19846 | approved | 2.384 | 126 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1608 |
| 1997 | D7732 PCLAT04201453250 19846 | approved | 3.711 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1609 |
| 1998 | D7602 PCLAT04201003250 19846 | approved | 1.843 | 126 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1610 |
| 1999 | D7602 PCLAT04201002900 19846 | approved | 1.618 | 124 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1611 |
| 2000 | D7733 PCLAT04201453250 19846 | approved | 3.711 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1612 |
| 2001 | D7734 PCLAT04201453250 19846 | approved | 3.711 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1613 |
| 2002 | D7633 PCLAT04201454050 19846 | approved | 4.625 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1614 |
| 2003 | D7735 PCLAT04201403250 19846 | approved | 3.583 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1615 |
| 2004 | D7736 PCLAT04201403250 19846 | approved | 3.583 | 175 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1616 |
| 2005 | D7730 PCLAT04200752500 19846 | approved | 2.742 | 325 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1617 |
| 2006 | D7738 PCLAT04201203250 19846 | approved | 1.685 | 96 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1618 |
| 2007 | D7738 PCLAT04201203200 19846 | approved | 1.797 | 104 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1619 |
| 2008 | D7737 PCLAT04201403700 19846 | approved | 2.121 | 91 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1620 |
| 2009 | D7737 PCLAT04201403250 19846 | approved | 1.720 | 84 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1621 |
| 2010 | D7630 PCLAT04201253250 19846 | approved | 2.194 | 120 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1622 |
| 2011 | D7630 PCLAT04201253200 19846 | approved | 1.440 | 80 | 0.000 | Duplicado | Batch 2 — mismo nombre que 1623 |

### 2B. Tabla de clasificación — stock.picking

| ID | Nombre | Origen | Estado | Clasificación | Motivo |
|----|--------|--------|--------|--------------|--------|
| 262 | WH/IN/00091 | Return of WH/IN/00090 | done | Conservado | Flujo de entrada válido (anterior) |
| 284 | EMB-00113 | REVERTIDO-19846 | done | Anulado | Picking original revertido |
| 287 | WH/OUT/00036 | Devolución de WH/IN/00091 | done | Conservado | Flujo de devolución válido (anterior) |
| 292 | EMB-00118 | P00003 | done | Conservado | Flujo independiente |
| 297 | EMB-00123 | P00008 | done | Conservado | Flujo independiente |
| 306 | EMB-00132 | Return of EMB-00113 | done | Duplicado | Contiene moves/lines duplicados (28 para 10 lotes) |
| 307 | EMB-00133 | ANULADO-19846 | cancel | Anulado | Picking cancelado en flujo |
| 310 | EMB-00136 | REVERTIDO-19846 | done | Anulado | Picking reprocesado revertido |
| 311 | EMB-00137 | Return of EMB-00136 | done | Residuo técnico | Retorno de picking ya revertido |

### 2C. Tabla de clasificación — stock.move (resumen)

| Origen | Estado | Cantidad | Clasificación |
|--------|--------|----------|--------------|
| NULL (sin origen) | done | 137 | Residuo técnico — moves sin trazabilidad de origen |
| 19846 | done | 38 | Duplicado/Residuo — asociados a lotes huérfanos |
| 19846 | cancel | 19 | Anulado — cancelados por flujo |
| P00003 | done | 1 | Conservado |
| P00008 | done | 1 | Conservado |
| (vacío) | cancel | 1 | Anulado |

### 2D. Tabla de clasificación — stock.move.line

| Vinculación | Cantidad | Clasificación |
|-------------|----------|--------------|
| Con picking EMB-00132 (10 lotes, 28 líneas) | 28 | Duplicado |
| Con picking EMB-00133 (cancel, sin lotes) | 0 | — |
| Con pickings válidos (WH/IN, WH/OUT, EMB-00113, EMB-00136, EMB-00137) | 95 | Conservado (parte de historial) |
| Sin picking | 37 | Residuo técnico |
| Sin lote | 39 | Residuo técnico (líneas sin lote asignado) |
| Con lotes huérfanos en pickings válidos | 19+19+19+19+19+28 | Mixto — revisar |

### 2E. Tabla de clasificación — stock.quant

| Ubicación | Cantidad | Qty total | Clasificación |
|-----------|----------|-----------|--------------|
| WH/Stock/Bodega Tepornac (loc 19) | 10 | +47.15 | Residuo técnico (stock zombie) |
| Partners/Vendors (loc 4) | 10 | -47.15 | Residuo técnico |
| Otras ubicaciones | 48 | variable | Conservado (historial válido) |

---

## 3. LÓGICA DE DECISIÓN (QUÉ SE BORRA Y QUÉ SE CONSERVA)

### Regla 1: Conservar → Lotes con FK de origen poblada
```
SI stock_lot.reception_id IS NOT NULL OR stock_lot.guia_processing_id IS NOT NULL
   → CONSERVAR (tiene trazabilidad)
```

**Resultado en BD actual: 0 lotes conservados** (todos son huérfanos).

### Regla 2: Huérfano → Lotes sin FK de origen
```
SI stock_lot.reception_id IS NULL AND stock_lot.guia_processing_id IS NULL
   AND stock_lot.name NOT LIKE '%virtual%' AND stock_lot.name NOT LIKE '%default%'
   → HUÉRFANO (marcar para eliminación)
```

**Resultado: 38 lotes huérfanos.**

### Regla 3: Duplicado → Mismo nombre de lote en dos registros distintos
```
SI existe más de un stock_lot con el mismo name (case-sensitive)
   → DUPLICADO (marcar para eliminación de ambos, o del más reciente si uno es válido)
```

**Resultado: 19 pares duplicados (Batch 1: 1605-1623, Batch 2: 1993-2011).**

### Regla 4: Residuo técnico → Quants sin respaldo de lote con trazabilidad
```
SI stock_quant.lot_id está en la lista de huérfanos
   Y stock_quant.quantity != 0
   → RESIDUO TÉCNICO (eliminar)
```

**Resultado: 68 quants asociados a los 38 lotes huérfanos (todos).**

### Regla 5: Residuo técnico → Move lines de lotes huérfanos
```
SI stock_move_line.lot_id está en la lista de huérfanos
   → RESIDUO TÉCNICO (eliminar la línea, no el move si es compartido)
```

### Regla 6: Residuo técnico → Cost lines de lotes huérfanos
```
SI stock_lot_cost_line.lot_id está en la lista de huérfanos
   → RESIDUO TÉCNICO (eliminar)
```

### Regla 7: Pickings → Solo eliminar si están cancelados Y son del flujo 19846
```
SI stock_picking.origin LIKE '%ANULADO-19846%' AND state = 'cancel'
   → ANULADO (eliminar)
SI stock_picking.origin LIKE '%REVERTIDO-19846%' AND state = 'done'
   → ANULADO (conservar como historial, no eliminar — ya están done y forman parte del historial contable)
```

### Regla 8: Stock moves → Eliminar solo los huérfanos (sin picking)
```
SI stock_move.picking_id IS NULL AND stock_move.state = 'done'
   → HUÉRFANO (eliminar)
SINO
   → CONSERVAR (tienen picking válido, aunque sea de flujo revertido)
```

### Regla 9: Precauciones adicionales
- **NO borrar** si el lote está en `lumber_container_stock_lot_rel` (verificado: 0)
- **NO borrar** si hay referencias en `lumber_export_shipment_line` (verificar antes)
- **NO borrar pickings** en estado `done` aunque su origen sea `REVERTIDO` — son historial
- **NO tocar** la guía `19846` (está en draft, correcta para reprocesar)

---

## 4. SCRIPT DE LIMPIEZA SEGURA

Ver archivo: `custom_addons/_cleanup_stock_completo.sh`

---

## 5. PLAN DE VALIDACIÓN POSTERIOR

### 5.1 Verificaciones inmediatas (SQL)

```sql
-- V1: Cero lotes huérfanos
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NULL AND guia_processing_id IS NULL
  AND name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
-- Esperado: 0

-- V2: Cero quants de lotes huérfanos
SELECT COUNT(*) FROM stock_quant sq
JOIN stock_lot sl ON sl.id = sq.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
-- Esperado: 0

-- V3: Cero move lines huérfanas
SELECT COUNT(*) FROM stock_move_line sml
JOIN stock_lot sl ON sl.id = sml.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
-- Esperado: 0

-- V4: Cero moves huérfanos con origin 19846
SELECT COUNT(*) FROM stock_move
WHERE origin = '19846' AND picking_id IS NULL AND state = 'done';
-- Esperado: 0

-- V5: Cero cost lines de huérfanos
SELECT COUNT(*) FROM stock_lot_cost_line lcl
WHERE lcl.lot_id NOT IN (SELECT id FROM stock_lot);
-- Esperado: 0 (integridad referencial)

-- V6: Pickings conservados intactos
SELECT id, name, origin, state FROM stock_picking
WHERE id IN (262, 287, 292, 297) AND state != 'done';
-- Esperado: 0 filas (todos siguen done)

-- V7: Guía 19846 sigue en draft
SELECT name, state FROM madenat_guia_processing WHERE name = '19846';
-- Esperado: 19846, draft

-- V8: Sin violaciones de exclusividad
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NOT NULL AND guia_processing_id IS NOT NULL
  AND name NOT LIKE '%virtual%';
-- Esperado: 0

-- V9: Sin lotes huérfanos en contenedores
SELECT COUNT(*) FROM lumber_container_stock_lot_rel lclr
JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL;
-- Esperado: 0

-- V10: Stock real visible en reportes limpio
SELECT location_id, SUM(quantity) FROM stock_quant
WHERE quantity > 0
GROUP BY location_id;
-- Solo deben verse ubicaciones con stock de lotes válidos
```

### 5.2 Verificación funcional

1. Abrir el reporte de inventario en Odoo → confirmar que WH/Stock/Bodega Tepornac no muestra 47.15 m³ falsos.
2. Abrir la guía 19846 → confirmar que está en draft y se puede reprocesar.
3. Ejecutar `do_full_processing()` sobre la guía 19846 → verificar que se crean 19 lotes nuevos (IDs nuevos), 19 moves, 19 move lines, y quants correctos (38 total: ±19).
4. Verificar que los IDs de los nuevos lotes NO colisionan con los eliminados (PostgreSQL no reusa IDs).

### 5.3 Rollback

Si algo sale mal, restaurar desde backup de BD previo a la limpieza. El script de limpieza hace backup automático en el paso 0.

---

**Conclusión:** Los 38 lotes son 100% huérfanos, sin trazabilidad válida. Eliminarlos junto con sus quants, move lines y cost lines asociados es seguro y no rompe ninguna cadena de historial contable/logístico válido. Los pickings EMB-00113, EMB-00136 (revertidos pero done) se conservan como historial. Solo EMB-00133 (cancel) y EMB-00132 (return duplicado) se eliminan.