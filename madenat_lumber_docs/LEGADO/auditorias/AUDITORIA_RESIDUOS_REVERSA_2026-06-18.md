# AUDITORÍA DE RESIDUOS POST-REVERSA DE GUÍA
## Guía auditada: `19846` — Fecha: 2026-06-18

---

## 1. MAPA DE RESIDUOS EN BD

### 1.1 Panorama general de `stock_lot`

| Métrica | Valor |
|---|---|
| Total lotes (no virtual/default) | **19** |
| Con `guia_processing_id` poblado | **0** |
| Con `reception_id` poblado | **0** |
| Sin FK de origen (huérfanos) | **19** (100%) |
| `technical_validation='rejected'` | **0** |
| `technical_validation='pending'` | **19** |
| `technical_validation='approved'` | **0** |

### 1.2 Distribución de los 19 lotes huérfanos

| ID | Nombre | Validación | Estado trazabilidad | Vol. m³ | Piezas | Producto |
|---|---|---|---|---|---|---|
| 1605 | D7731 PCLAT04201253250 19846 | pending | procesado | 3.656 | 200 | PINO_CEP__SECO_LATERAL |
| 1606 | D7739 PCLAT04201453250 19846 | pending | procesado | 0.276 | 13 | PINO_CEP__SECO_LATERAL |
| 1607 | D7739 PCLAT04201453200 19846 | pending | procesado | 0.752 | 36 | PINO_CEP__SECO_LATERAL |
| 1608 | D7739 PCLAT04201452900 19846 | pending | procesado | 2.384 | 126 | PINO_CEP__SECO_LATERAL |
| 1609 | D7732 PCLAT04201453250 19846 | pending | procesado | 3.711 | 175 | PINO_CEP__SECO_LATERAL |
| 1610 | D7602 PCLAT04201003250 19846 | pending | procesado | 1.843 | 126 | PINO_CEP__SECO_LATERAL |
| 1611 | D7602 PCLAT04201002900 19846 | pending | procesado | 1.618 | 124 | PINO_CEP__SECO_LATERAL |
| 1612 | D7733 PCLAT04201453250 19846 | pending | procesado | 3.711 | 175 | PINO_CEP__SECO_LATERAL |
| 1613 | D7734 PCLAT04201453250 19846 | pending | procesado | 3.711 | 175 | PINO_CEP__SECO_LATERAL |
| 1614 | D7633 PCLAT04201454050 19846 | pending | procesado | 4.625 | 175 | PINO_CEP__SECO_LATERAL |
| 1615 | D7735 PCLAT04201403250 19846 | pending | procesado | 3.583 | 175 | PINO_CEP__SECO_LATERAL |
| 1616 | D7736 PCLAT04201403250 19846 | pending | procesado | 3.583 | 175 | PINO_CEP__SECO_LATERAL |
| 1617 | D7730 PCLAT04200752500 19846 | pending | procesado | 2.742 | 325 | PINO_CEP__SECO_LATERAL |
| 1618 | D7738 PCLAT04201203250 19846 | pending | procesado | 1.685 | 96 | PINO_CEP__SECO_LATERAL |
| 1619 | D7738 PCLAT04201203200 19846 | pending | procesado | 1.797 | 104 | PINO_CEP__SECO_LATERAL |
| 1620 | D7737 PCLAT04201403700 19846 | pending | procesado | 2.121 | 91 | PINO_CEP__SECO_LATERAL |
| 1621 | D7737 PCLAT04201403250 19846 | pending | procesado | 1.720 | 84 | PINO_CEP__SECO_LATERAL |
| 1622 | D7630 PCLAT04201253250 19846 | pending | procesado | 2.194 | 120 | PINO_CEP__SECO_LATERAL |
| 1623 | D7630 PCLAT04201253200 19846 | pending | procesado | 1.440 | 80 | PINO_CEP__SECO_LATERAL |

**Totales:** 19 lotes · 47.152 m³ · 2,575 piezas

---

## 2. HALLAZGOS CONCRETOS

### H1: 19 lotes huérfanos con stock real (CRÍTICO)

- **Descripción:** Tras la reversa de la guía 19846, los 19 lotes quedaron con `guia_processing_id=NULL` y `reception_id=NULL`.
- **Estado:** `technical_validation='pending'`, `estado_trazabilidad='procesado'` (residuo del estado previo a la reversa).
- **Impacto operacional:**
  - 10 de los 19 lotes tienen stock disponible en `WH/Stock/Bodega Tepornac` por un total de **47.15 m³**.
  - Los otros 9 lotes (ID 1605-1613) no tienen quants > 0, pero existen como registros.
- **Causa raíz:** El método `action_reverse_to_draft()` en `madenat_guia_processing.py` (línea 3879) desvincula `guia_processing_id=False` y limpia el M2M (`lot_ids = [(5,0,0)]`), pero **no elimina los lotes de `stock_lot`**.

### H2: Stock moves huérfanos sin picking (MEDIO)

- **Descripción:** 10 movimientos de stock (`stock_move` IDs 5010-5019) en estado `done` con `origin='19846'` y `picking_id=NULL`.
- **Causa:** El picking EMB-00113 fue desvinculado (origen cambiado a `REVERTIDO-19846`) pero los moves asociados quedaron como `done` sin picking padre. Posiblemente la cancelación del picking en la reversa borró el picking pero no los moves ya confirmados.
- **Riesgo:** Estos moves fantasmas pueden interferir con valoración de inventario o reportes contables.

### H3: Pickings desalineados (BAJO)

| ID | Nombre | Origen | Estado | Fecha |
|---|---|---|---|---|
| 284 | EMB-00113 | REVERTIDO-19846 | done | 2026-06-05 |
| 307 | EMB-00133 | ANULADO-19846 | cancel | — |

- **EMB-00113** está en `done` con origen `REVERTIDO-19846`. Esto es correcto según el código de reversión: desvincula el origen para que la guía pueda reprocesarse.
- **EMB-00133** está cancelado con origen `ANULADO-19846`. Fue cancelado por el flujo `do_full_processing()` al detectar un picking existente.

**Ambos pickings son residuos esperados del flujo de reversión, no son errores.**

### H4: 38 stock.move.lines en estado `done` (MEDIO)

- Existen 38 líneas de movimiento (`stock_move_line`) vinculadas a los 19 lotes huérfanos, todas en estado `done`.
- Estas líneas confirman que el picking se validó exitosamente antes de la reversa, generando quants.
- **Problema:** No hay un mecanismo que revierta estas líneas al cancelar/desvincular el picking. Los quants quedaron como residuo físico del proceso original.

### H5: Guía 19846 en draft con contadores a cero (CORRECTO)

- Estado: `draft`, todos los contadores en 0.0, sin líneas de staging ni lotes vinculados vía M2M.
- **Esto es correcto:** La reversa limpió correctamente los contadores y el M2M de la guía.
- **Pero la inconsistencia es lógica:** La guía está "limpia" para reprocesar, pero los 19 lotes de su procesamiento anterior aún existen en `stock_lot`.

### H6: Sin violaciones de exclusividad (CORRECTO)

- `violaciones_exclusividad` = vacío. Ningún lote tiene simultáneamente `reception_id` y `guia_processing_id`.
- El constraint `_check_reception_guia_exclusivity` está funcionando.

### H7: Sin lotes en contenedores logísticos (CORRECTO)

- Ninguno de los 19 lotes huérfanos está asignado a un `lumber_container`.
- Esto es positivo: el residuo no ha contaminado la cadena logística.

---

## 3. CLASIFICACIÓN DE LOTES HUÉRFANOS

### Criterios de clasificación

| Categoría | Criterio | Cantidad en BD |
|---|---|---|
| **Zombie con stock** | `guia=NULL AND reception=NULL AND quants>0` | 10 lotes |
| **Zombie sin stock** | `guia=NULL AND reception=NULL AND quants=0` | 9 lotes |
| **Rejected activo** | `technical_validation='rejected'` | 0 lotes |
| **Rejected con stock** | `rejected AND quants>0` | 0 lotes |
| **Exclusividad rota** | `reception_id AND guia_processing_id` | 0 lotes |

### Los 10 lotes "zombie con stock" (detalle)

| ID | Lote | Stock (m³) | Ubicación |
|---|---|---|---|
| 1615 | D7735 PCLAT04201403250 19846 | 7.163 | WH/Stock/Bodega Tepornac |
| 1616 | D7736 PCLAT04201403250 19846 | 7.163 | WH/Stock/Bodega Tepornac |
| 1617 | D7730 PCLAT04200752500 19846 | 5.482 | WH/Stock/Bodega Tepornac |
| 1614 | D7633 PCLAT04201454050 19846 | 5.425 | WH/Stock/Bodega Tepornac |
| 1622 | D7630 PCLAT04201253250 19846 | 4.384 | WH/Stock/Bodega Tepornac |
| 1620 | D7737 PCLAT04201403700 19846 | 4.241 | WH/Stock/Bodega Tepornac |
| 1619 | D7738 PCLAT04201203200 19846 | 3.597 | WH/Stock/Bodega Tepornac |
| 1621 | D7737 PCLAT04201403250 19846 | 3.440 | WH/Stock/Bodega Tepornac |
| 1618 | D7738 PCLAT04201203250 19846 | 3.375 | WH/Stock/Bodega Tepornac |
| 1623 | D7630 PCLAT04201253200 19846 | 2.880 | WH/Stock/Bodega Tepornac |

**Total stock zombie: 47.15 m³ en 10 lotes.**

---

## 4. ACCIONES MÍNIMAS DE SANEAMIENTO

### Paso 1: Auditoría previa al saneamiento (verificación)

```sql
-- Verificar que los 10 lotes con stock no estén en ningún contenedor
SELECT COUNT(*) FROM lumber_container_stock_lot_rel
WHERE stock_lot_id IN (1614,1615,1616,1617,1618,1619,1620,1621,1622,1623);
-- Debe retornar 0

-- Verificar que no haya costos asociados
SELECT COUNT(*) FROM stock_lot_cost_line
WHERE lot_id IN (1605,1606,1607,1608,1609,1610,1611,1612,1613,
                 1614,1615,1616,1617,1618,1619,1620,1621,1622,1623);
```

### Paso 2: Eliminar quants (inventario físico)

```sql
-- Eliminar los quants de los 10 lotes zombie con stock
DELETE FROM stock_quant
WHERE lot_id IN (1614,1615,1616,1617,1618,1619,1620,1621,1622,1623)
  AND quantity > 0;
```

### Paso 3: Eliminar stock_move_lines huérfanas

```sql
-- Eliminar líneas de movimiento asociadas a los 19 lotes
DELETE FROM stock_move_line
WHERE lot_id IN (1605,1606,1607,1608,1609,1610,1611,1612,1613,
                 1614,1615,1616,1617,1618,1619,1620,1621,1622,1623);
```

### Paso 4: Eliminar stock_moves huérfanos

```sql
-- Eliminar moves huérfanos (sin picking, done, origin='19846')
DELETE FROM stock_move
WHERE id IN (5010,5011,5012,5013,5014,5015,5016,5017,5018,5019)
  AND picking_id IS NULL
  AND origin = '19846';
```

### Paso 5: Eliminar los 19 lotes huérfanos

```sql
-- Eliminar lotes zombie de stock_lot
DELETE FROM stock_lot
WHERE id IN (1605,1606,1607,1608,1609,1610,1611,1612,1613,
             1614,1615,1616,1617,1618,1619,1620,1621,1622,1623)
  AND reception_id IS NULL
  AND guia_processing_id IS NULL;
```

### Paso 6: Limpiar picking con origen ANULADO (opcional)

```sql
-- Si EMB-00133 es basura total y no se necesita trazabilidad:
DELETE FROM stock_picking WHERE id = 307 AND state = 'cancel';
-- O simplemente dejarlo como está; no causa problemas.
```

### Paso 7: Verificación posterior

```sql
-- Confirmar que no quedan lotes huérfanos
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NULL AND guia_processing_id IS NULL
  AND name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
-- Debe retornar 0

-- Confirmar que no quedan quants de lotes eliminados
SELECT COUNT(*) FROM stock_quant WHERE lot_id IS NULL AND quantity > 0;
-- No debería haber (los quants Odoo normales tienen lot_id NOT NULL)
```

---

## 5. RECOMENDACIÓN PARA EVITAR RECURRENCIA

### Problema detectado en `action_reverse_to_draft()` (líneas 3868-3888 de `madenat_guia_processing.py`)

El código actual hace:
1. Desvincula `guia_processing_id` de los lotes
2. Marca `technical_validation='rejected'` (o `pending` como quedó tras el cierre de fuga)
3. Limpia el M2M de la guía
4. Elimina las líneas de staging
5. Resetea la guía a `draft`

**Lo que NO hace:**
- No elimina los lotes de `stock_lot`
- No revierte los quants generados por la validación previa
- No limpia los `stock.move` y `stock.move.line` asociados

### Recomendación de código (mínima, no refactorización amplia)

Agregar en `action_reverse_to_draft()`, después del bloque de limpieza de lotes (línea ~3888), lo siguiente:

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 LIMPIEZA DE RESIDUOS LOGÍSTICOS (2026-06-18)
# Eliminar quants, moves y lotes generados por esta guía
# para que la reversa sea completa y no deje zombies.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if rec.lot_ids or lotes_previamente_vinculados:
    # 1. Eliminar quants (inventario físico)
    quants = self.env['stock.quant'].search([
        ('lot_id', 'in', lotes_previamente_vinculados.ids)
    ])
    if quants:
        quants.unlink()

    # 2. Eliminar move lines
    move_lines = self.env['stock.move.line'].search([
        ('lot_id', 'in', lotes_previamente_vinculados.ids)
    ])
    if move_lines:
        move_lines.unlink()

    # 3. Eliminar moves huérfanos
    moves = self.env['stock.move'].search([
        ('origin', '=', rec.name),
        ('picking_id', '=', False),
    ])
    if moves:
        moves.unlink()

    # 4. Eliminar los lotes mismos (ya desvinculados de la guía)
    lotes_previamente_vinculados.unlink()
```

### Nota de seguridad:
- Este bloque DEBE ejecutarse ANTES de `rec.write({'lot_ids': [(5, 0, 0)]})` (línea 3884 actual), o capturar los lotes a eliminar antes del M2M clear.
- Solo aplica si `rec.state` estaba en `processed` o `validated` (cuando hay quants reales).
- Si la guía nunca llegó a `validated`, no hay quants que limpiar — solo lotes y líneas de staging.

---

## 6. CONFIRMACIÓN DE CONSISTENCIA POST-SANEAMIENTO

Una vez ejecutadas las acciones de saneamiento:

| Verificación | Resultado esperado |
|---|---|
| `SELECT COUNT(*) FROM stock_lot WHERE reception_id IS NULL AND guia_processing_id IS NULL AND name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';` | `0` |
| `SELECT COUNT(*) FROM stock_quant WHERE lot_id IN (1605-1623) AND quantity > 0;` | `0` |
| `SELECT COUNT(*) FROM stock_move WHERE origin='19846' AND picking_id IS NULL;` | `0` |
| `SELECT COUNT(*) FROM stock_move_line WHERE lot_id IN (1605-1623);` | `0` |
| Guía 19846 en estado `draft` con contadores en 0 | ✓ Correcto |
| Sin lotes huérfanos en inventario | ✓ Correcto |
| Logística (contenedores/embarques) sin lotes zombie | ✓ Correcto |

---

## 7. QUERIES SQL DE AUDITORÍA (REFERENCIA)

Las queries completas están en `/mnt/extra-addons/_audit_reversion_residuos.py`.

### Queries clave para monitoreo continuo:

```sql
-- Q1: Detectar lotes huérfanos con stock
SELECT sl.id, sl.name, SUM(sq.quantity) AS stock_m3
FROM stock_lot sl
JOIN stock_quant sq ON sq.lot_id = sl.id AND sq.quantity > 0
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%'
GROUP BY sl.id, sl.name;

-- Q2: Detectar guías en draft con lotes aún vinculados por FK
SELECT mgp.name, mgp.state, COUNT(sl.id) AS lotes_huerfanos
FROM madenat_guia_processing mgp
JOIN stock_lot sl ON sl.guia_processing_id = mgp.id
WHERE mgp.state IN ('draft', 'cancelled')
GROUP BY mgp.name, mgp.state;

-- Q3: Detectar stock_moves sin picking padre (huérfanos)
SELECT id, name, origin, state FROM stock_move
WHERE picking_id IS NULL AND state = 'done' AND origin IS NOT NULL;

-- Q4: Monitorear lotes rejected en contenedores
SELECT lc.name AS contenedor, COUNT(*) AS lotes_rejected
FROM lumber_container_stock_lot_rel lclr
JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
JOIN lumber_container lc ON lc.id = lclr.lumber_container_id
WHERE sl.technical_validation = 'rejected'
GROUP BY lc.name;
```

---

**Conclusión:** La fuga de estado fue cerrada correctamente (los lotes quedaron `pending` en vez de `rejected`), pero la reversa no elimina los lotes ni los quants generados. Esto deja residuos de inventario que deben limpiarse manualmente. Se recomienda la acción correctiva en `action_reverse_to_draft()` para futuras reversas.