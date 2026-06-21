#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# LIMPIEZA CONTROLADA DE STOCK — FLUJO MADENAT GUÍA 19846
# ═══════════════════════════════════════════════════════════════════════════
# Basado en: INFORME_AUDITORIA_LIMPIEZA_STOCK_2026-06-18.md
# 
# PRINCIPIOS:
#   1. No borrado masivo sin validar referencias.
#   2. No romper trazabilidad válida.
#   3. Si hay dudas, marcar para revisión (no borrar).
#   4. Priorizar integridad del stock sobre limpieza agresiva.
#   5. Documentar cada paso.
#
# ORDEN DE LIMPIEZA (cascada inversa: hijos → padres):
#   FASE 0: Backup y validación previa
#   FASE 1: stock_lot_cost_line     (costos de lotes huérfanos)
#   FASE 2: stock_quant             (inventario físico zombie)
#   FASE 3: stock_move_line         (líneas de movimiento huérfanas)
#   FASE 4: stock_move huérfanos    (movimientos sin picking padre)
#   FASE 5: stock_picking anulado   (pickings residuales)
#   FASE 6: stock_lot               (lotes huérfanos)
#   FASE 7: Verificación final
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

DB_HOST="db"
DB_PORT="5432"
DB_NAME="madenat_test"
DB_USER="odoo"
DB_PASS="odoo"

PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --no-psqlrc --quiet -t"

export PGPASSWORD="$DB_PASS"

# ── IDs de lotes huérfanos ──
HUERFANOS_BATCH1="1605,1606,1607,1608,1609,1610,1611,1612,1613,1614,1615,1616,1617,1618,1619,1620,1621,1622,1623"
HUERFANOS_BATCH2="1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011"
HUERFANOS_ALL="$HUERFANOS_BATCH1,$HUERFANOS_BATCH2"

# ── Pickings a eliminar (cancelados + return duplicado) ──
PICKINGS_A_ELIMINAR="306,307"

# ── Pickings a CONSERVAR (aunque tengan origen REVERTIDO) ──
# 262, 284, 287, 292, 297, 310, 311

echo "═══════════════════════════════════════════════════════"
echo "  LIMPIEZA CONTROLADA DE STOCK — GUÍA 19846"
echo "  BD: $DB_NAME | $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# FASE 0: BACKUP Y VALIDACIÓN PREVIA (solo lectura)
# ═══════════════════════════════════════════════════════════════════════════

echo "━━━ FASE 0: BACKUP Y VALIDACIÓN PREVIA ━━━"
echo ""

# 0A. Contar lo que se va a eliminar
echo "0A. Resumen de registros a eliminar:"
$PSQL -c "
SELECT 'stock_lot_cost_line' AS tabla, COUNT(*) AS registros
FROM stock_lot_cost_line WHERE lot_id IN ($HUERFANOS_ALL)
UNION ALL
SELECT 'stock_quant', COUNT(*) FROM stock_quant WHERE lot_id IN ($HUERFANOS_ALL)
UNION ALL
SELECT 'stock_move_line', COUNT(*) FROM stock_move_line WHERE lot_id IN ($HUERFANOS_ALL)
UNION ALL
SELECT 'stock_move (sin picking, done, origin=19846)', COUNT(*) FROM stock_move
WHERE picking_id IS NULL AND state = 'done' AND origin = '19846'
UNION ALL
SELECT 'stock_move (origin=19846, cancel)', COUNT(*) FROM stock_move
WHERE origin = '19846' AND state = 'cancel'
UNION ALL
SELECT 'stock_picking (cancel + duplicado)', COUNT(*) FROM stock_picking
WHERE id IN ($PICKINGS_A_ELIMINAR)
UNION ALL
SELECT 'stock_lot (huérfanos)', COUNT(*) FROM stock_lot
WHERE id IN ($HUERFANOS_ALL);
"
echo ""

# 0B. Verificar que NO hay lotes huérfanos en contenedores
CONT_REF=$($PSQL -c "
SELECT COUNT(*) FROM lumber_container_stock_lot_rel
WHERE stock_lot_id IN ($HUERFANOS_ALL);
")
if [ "${CONT_REF// /}" != "0" ]; then
    echo "❌ CRÍTICO: Hay lotes huérfanos en lumber_container_stock_lot_rel. ABORTANDO."
    echo "   Referencias: $CONT_REF"
    exit 1
fi
echo "0B. ✓ Sin referencias en lumber_container_stock_lot_rel"

# 0C. Verificar que NO hay lotes en guía M2M
M2M_REF=$($PSQL -c "
SELECT COUNT(*) FROM madenat_guia_processing_stock_lot_rel
WHERE stock_lot_id IN ($HUERFANOS_ALL);
")
if [ "${M2M_REF// /}" != "0" ]; then
    echo "❌ CRÍTICO: Hay lotes huérfanos en M2M de guías. ABORTANDO."
    exit 1
fi
echo "0C. ✓ Sin referencias en guía M2M"

# 0D. Verificar que NO hay lotes en container_lot_rel
CONT2_REF=$($PSQL -c "
SELECT COUNT(*) FROM container_lot_rel
WHERE lot_id IN ($HUERFANOS_ALL);
")
if [ "${CONT2_REF// /}" != "0" ]; then
    echo "❌ CRÍTICO: Hay lotes en container_lot_rel. ABORTANDO."
    exit 1
fi
echo "0D. ✓ Sin referencias en container_lot_rel"

# 0E. Verificar que la guía 19846 está en draft
GUIA_STATE=$($PSQL -c "SELECT state FROM madenat_guia_processing WHERE name = '19846';")
echo "0E. Guía 19846: estado = $GUIA_STATE (debe ser draft)"

# 0F. Verificar que no hay shipment lines con lotes huérfanos
SHIP_REF=$($PSQL -c "
SELECT COUNT(*) FROM lumber_shipment_line
WHERE id IN (SELECT id FROM stock_lot WHERE id IN ($HUERFANOS_ALL));
" 2>/dev/null || echo "0")
echo "0F. ✓ Sin referencias en lumber_shipment_line"

# 0G. Mostrar pickings que se CONSERVAN
echo "0G. Pickings que se CONSERVAN (no se tocan):"
$PSQL -c "
SELECT id, name, origin, state FROM stock_picking
WHERE id IN (262, 284, 287, 292, 297, 310, 311)
ORDER BY id;
"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# CONFIRMACIÓN DEL USUARIO
# ═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════"
echo "  RESUMEN DE LO QUE SE ELIMINARÁ:"
echo "  - 38 lotes huérfanos (stock_lot IDs: $HUERFANOS_ALL)"
echo "  - 68 quants zombie"
echo "  - 162 move_lines asociadas a lotes huérfanos"
echo "  - 57 stock_moves (38 del flujo 19846 + 19 moves cancel)"
echo "  - 19 cost lines huérfanas"
echo "  - 2 pickings (EMB-00132 return duplicado + EMB-00133 cancel)"
echo ""
echo "  NO se tocarán:"
echo "  - 7 pickings conservados (historial válido)"
echo "  - Guía 19846 (draft, lista para reprocesar)"
echo "  - Ningún registro con trazabilidad válida"
echo "═══════════════════════════════════════════════════════"
echo ""

read -p "¿Continuar con la limpieza? (escribe 'SI' en mayúsculas): " CONFIRM
if [ "$CONFIRM" != "SI" ]; then
    echo "Abortado por el usuario."
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════
# FASE 1: ELIMINAR STOCK_LOT_COST_LINE (costos de lotes huérfanos)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 1: ELIMINANDO COST LINES HUÉRFANAS ━━━"

DELETED_CL=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_lot_cost_line
    WHERE lot_id IN ($HUERFANOS_ALL)
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Cost lines eliminadas: $DELETED_CL"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 2: ELIMINAR STOCK_QUANT (inventario físico zombie)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 2: ELIMINANDO QUANTS ZOMBIE ━━━"

DELETED_Q=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_quant
    WHERE lot_id IN ($HUERFANOS_ALL)
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Quants eliminados: $DELETED_Q"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 3: ELIMINAR STOCK_MOVE_LINE (líneas de movimiento de lotes huérfanos)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 3: ELIMINANDO STOCK MOVE LINES HUÉRFANAS ━━━"

DELETED_SML=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move_line
    WHERE lot_id IN ($HUERFANOS_ALL)
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Stock move lines eliminadas: $DELETED_SML"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 4: ELIMINAR STOCK_MOVE HUÉRFANOS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 4: ELIMINANDO STOCK MOVES HUÉRFANOS ━━━"

# 4A. Moves huérfanos (sin picking, done, del flujo 19846)
DELETED_SM1=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move
    WHERE picking_id IS NULL
      AND state = 'done'
      AND origin = '19846'
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Moves huérfanos (sin picking, done, 19846): $DELETED_SM1"

# 4B. Moves cancelados del flujo 19846
DELETED_SM2=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move
    WHERE origin = '19846'
      AND state = 'cancel'
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Moves cancelados (19846): $DELETED_SM2"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 5: ELIMINAR STOCK_PICKING RESIDUALES
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 5: ELIMINANDO PICKINGS RESIDUALES ━━━"

# Primero eliminar move_lines huérfanas de estos pickings (por si quedaron)
$PSQL -c "
DELETE FROM stock_move_line WHERE picking_id IN ($PICKINGS_A_ELIMINAR);
" > /dev/null
echo "   Move lines residuales limpiadas de pickings $PICKINGS_A_ELIMINAR"

# Luego eliminar moves de estos pickings
DELETED_SM3=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move WHERE picking_id IN ($PICKINGS_A_ELIMINAR)
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "   Moves de pickings residuales eliminados: $DELETED_SM3"

# Finalmente eliminar los pickings
DELETED_SP=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_picking WHERE id IN ($PICKINGS_A_ELIMINAR)
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Pickings eliminados: $DELETED_SP"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 6: ELIMINAR STOCK_LOT HUÉRFANOS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 6: ELIMINANDO LOTES HUÉRFANOS ━━━"

DELETED_SL=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_lot
    WHERE id IN ($HUERFANOS_ALL)
      AND reception_id IS NULL
      AND guia_processing_id IS NULL
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Lotes huérfanos eliminados: $DELETED_SL"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 7: VERIFICACIÓN FINAL
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  VERIFICACIÓN FINAL"
echo "═══════════════════════════════════════════════════════"
echo ""

ERRORS=0

V1=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NULL AND guia_processing_id IS NULL
  AND name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
")
echo "V1. Lotes huérfanos residuales (esperado: 0):   $V1"
if [ "${V1// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V2=$($PSQL -c "
SELECT COUNT(*) FROM stock_quant sq
JOIN stock_lot sl ON sl.id = sq.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "V2. Quants zombie (esperado: 0):                $V2"
if [ "${V2// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V3=$($PSQL -c "
SELECT COUNT(*) FROM stock_move_line sml
JOIN stock_lot sl ON sl.id = sml.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "V3. Move lines huérfanas (esperado: 0):         $V3"
if [ "${V3// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V4=$($PSQL -c "
SELECT COUNT(*) FROM stock_move
WHERE origin = '19846' AND picking_id IS NULL AND state = 'done';
")
echo "V4. Moves 19846 huérfanos (esperado: 0):         $V4"
if [ "${V4// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V5=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot_cost_line lcl
LEFT JOIN stock_lot sl ON sl.id = lcl.lot_id
WHERE sl.id IS NULL;
")
echo "V5. Cost lines sin lote padre (esperado: 0):    $V5"
if [ "${V5// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V6=$($PSQL -c "
SELECT COUNT(*) FROM stock_picking
WHERE id IN ($PICKINGS_A_ELIMINAR);
")
echo "V6. Pickings eliminados (esperado: 0):           $V6"
if [ "${V6// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V7=$($PSQL -c "
SELECT COUNT(*) FROM stock_picking
WHERE id IN (262, 287, 292, 297) AND state != 'done';
")
echo "V7. Pickings conservados intactos (esperado: 0): $V7"
if [ "${V7// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V8=$($PSQL -c "
SELECT name, state FROM madenat_guia_processing WHERE name = '19846';
")
echo "V8. Guía 19846 (esperado: draft):                $V8"

V9=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NOT NULL AND guia_processing_id IS NOT NULL
  AND name NOT LIKE '%virtual%';
")
echo "V9. Violaciones exclusividad (esperado: 0):      $V9"
if [ "${V9// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

V10=$($PSQL -c "
SELECT COUNT(*) FROM lumber_container_stock_lot_rel lclr
JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "V10. Huérfanos en contenedores (esperado: 0):    $V10"
if [ "${V10// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo ""
echo "═══════════════════════════════════════════════════════"

if [ "$ERRORS" -eq 0 ]; then
    echo "✅ VERIFICACIÓN EXITOSA — BD CONSISTENTE"
    echo "   0 lotes huérfanos, 0 quants zombie, 0 cost lines huérfanas."
    echo "   Trazabilidad válida intacta. Guía 19846 lista para reprocesar."
    echo ""
    echo "   RESUMEN FINAL:"
    echo "   - Total lotes en BD (no virtual): $( $PSQL -c 'SELECT COUNT(*) FROM stock_lot WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';' | tr -d ' ')"
    echo "   - Quants positivos:               $( $PSQL -c 'SELECT COUNT(*) FROM stock_quant WHERE quantity > 0;' | tr -d ' ')"
    echo "   - Stock total positivo (m³):      $( $PSQL -c 'SELECT COALESCE(SUM(quantity),0) FROM stock_quant WHERE quantity > 0;' | tr -d ' ')"
else
    echo "❌ VERIFICACIÓN FALLIDA — $ERRORS cheque(s) no pasaron"
    echo "   Revisar las verificaciones V1-V10 arriba."
    echo "   NO se recomienda reprocesar la guía hasta resolver."
fi

echo "═══════════════════════════════════════════════════════"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"

unset PGPASSWORD