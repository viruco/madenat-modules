#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SANEAMIENTO SEGURO POST-REVERSA — Guía 19846
# ═══════════════════════════════════════════════════════════════════════════
# Orden de limpieza:
#   1. VALIDACIÓN PREVIA  → listar todo lo afectado sin borrar
#   2. QUANTS             → eliminar stock físico zombie
#   3. STOCK.MOVE.LINE    → eliminar líneas de movimiento huérfanas
#   4. STOCK.MOVE         → eliminar movimientos done sin picking padre
#   5. STOCK.LOT          → eliminar lotes huérfanos
#   6. STOCK.PICKING      → cancelar/limpiar pickings residuales (opcional)
#   7. VERIFICACIÓN FINAL → confirmar 0 residuos
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

DB_HOST="db"
DB_PORT="5432"
DB_NAME="madenat_test"
DB_USER="odoo"
DB_PASS="odoo"

PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --no-psqlrc --quiet -t"

export PGPASSWORD="$DB_PASS"

echo "═══════════════════════════════════════════════════════"
echo "  SANEAMIENTO POST-REVERSA GUÍA 19846"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# FASE 0: IDENTIFICACIÓN DE RESIDUOS (solo lectura, no modifica)
# ═══════════════════════════════════════════════════════════════════════════

echo "━━━ FASE 0: IDENTIFICACIÓN DE RESIDUOS ━━━"
echo ""

echo "0A. Lotes huérfanos (guia_processing_id IS NULL AND reception_id IS NULL):"
$PSQL -c "
SELECT sl.id, sl.name,
       CASE WHEN sq.lot_id IS NOT NULL THEN 'CON STOCK' ELSE 'sin stock' END AS stock_status,
       COALESCE(sq.qty, 0) AS stock_m3,
       sl.technical_validation, sl.estado_trazabilidad
FROM stock_lot sl
LEFT JOIN (
    SELECT lot_id, SUM(quantity) AS qty
    FROM stock_quant
    WHERE quantity > 0
    GROUP BY lot_id
) sq ON sq.lot_id = sl.id
WHERE sl.reception_id IS NULL
  AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%'
  AND sl.name NOT LIKE '%default%'
ORDER BY stock_m3 DESC, sl.id;
"
echo ""

echo "0B. Quants zombie (stock físico de lotes huérfanos):"
$PSQL -c "
SELECT sq.id AS quant_id, sq.lot_id, sl.name AS lot_name,
       sq.quantity, sq.location_id,
       sloc.complete_name AS location
FROM stock_quant sq
JOIN stock_lot sl ON sl.id = sq.lot_id
LEFT JOIN stock_location sloc ON sloc.id = sq.location_id
WHERE sq.quantity > 0
  AND sl.reception_id IS NULL
  AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%'
  AND sl.name NOT LIKE '%default%'
ORDER BY sq.quantity DESC;
"
echo ""

echo "0C. Stock move lines huérfanas (de lotes huérfanos):"
$PSQL -c "
SELECT sml.id AS move_line_id, sml.move_id,
       sl.name AS lot_name, sml.quantity, sml.state,
       sm.state AS move_state, sm.origin
FROM stock_move_line sml
JOIN stock_lot sl ON sl.id = sml.lot_id
LEFT JOIN stock_move sm ON sm.id = sml.move_id
WHERE sl.reception_id IS NULL
  AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%'
  AND sl.name NOT LIKE '%default%'
ORDER BY sml.id;
"
echo ""

echo "0D. Stock moves huérfanos (done, sin picking padre, origin='19846'):"
$PSQL -c "
SELECT sm.id AS move_id, sm.name, sm.origin, sm.state,
       sm.product_uom_qty, sm.picking_id
FROM stock_move sm
WHERE sm.picking_id IS NULL
  AND sm.state = 'done'
  AND sm.origin = '19846'
ORDER BY sm.id;
"
echo ""

echo "0E. Pickings relacionados con la guía 19846:"
$PSQL -c "
SELECT sp.id, sp.name, sp.origin, sp.state,
       spt.name AS picking_type,
       sp.create_date, sp.date_done
FROM stock_picking sp
LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
WHERE sp.origin LIKE '%19846%'
   OR sp.id IN (
       SELECT sm.picking_id FROM stock_move sm
       JOIN stock_move_line sml ON sml.move_id = sm.id
       JOIN stock_lot sl ON sl.id = sml.lot_id
       WHERE sl.reception_id IS NULL
         AND sl.guia_processing_id IS NULL
         AND sl.name LIKE '%19846%'
   )
ORDER BY sp.id;
"
echo ""

echo "0F. VERIFICACIÓN DE EXCLUSIÓN — Lotes de otras guías (NO deben tocarse):"
$PSQL -c "
SELECT COUNT(*) AS lotes_de_otras_guias
FROM stock_lot
WHERE guia_processing_id IS NOT NULL
   OR reception_id IS NOT NULL;
"
echo ""

CONTENEDORES=$($PSQL -c "
SELECT COUNT(*) FROM lumber_container_stock_lot_rel lclr
JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name LIKE '%19846%';
")
echo "0G. Lotes huérfanos en contenedores: $CONTENEDORES (debe ser 0)"
if [ "$CONTENEDORES" != "0" ]; then
    echo "❌ ERROR: Hay lotes huérfanos en contenedores. Abortando."
    exit 1
fi
echo ""

COSTOS=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot_cost_line
WHERE lot_id IN (
    SELECT id FROM stock_lot
    WHERE reception_id IS NULL AND guia_processing_id IS NULL
      AND name LIKE '%19846%'
);
")
echo "0H. Costos asociados a lotes huérfanos: $COSTOS (debe ser 0)"
if [ "$COSTOS" != "0" ]; then
    echo "❌ ERROR: Hay costos asociados a lotes huérfanos. Abortando."
    exit 1
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# CONFIRMACIÓN DEL USUARIO
# ═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════"
echo "  RESUMEN DE LO QUE SE ELIMINARÁ:"
echo ""

$PSQL -c "
SELECT 'stock_quant' AS tabla, COUNT(*) AS registros FROM stock_quant sq
JOIN stock_lot sl ON sl.id = sq.lot_id
WHERE sq.quantity > 0 AND sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name LIKE '%19846%' AND sl.name NOT LIKE '%virtual%'
UNION ALL
SELECT 'stock_move_line', COUNT(*) FROM stock_move_line sml
JOIN stock_lot sl ON sl.id = sml.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL AND sl.name LIKE '%19846%'
UNION ALL
SELECT 'stock_move', COUNT(*) FROM stock_move sm
WHERE sm.picking_id IS NULL AND sm.state = 'done' AND sm.origin = '19846'
UNION ALL
SELECT 'stock_lot', COUNT(*) FROM stock_lot sl
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL AND sl.name LIKE '%19846%'
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%'
UNION ALL
SELECT 'stock_picking', COUNT(*) FROM stock_picking sp
WHERE sp.origin LIKE '%ANULADO-19846%' AND sp.state = 'cancel';
"

echo ""
echo "═══════════════════════════════════════════════════════"
echo ""

read -p "¿Continuar con el saneamiento? (escribe 'SI' en mayúsculas): " CONFIRM
if [ "$CONFIRM" != "SI" ]; then
    echo "Abortado por el usuario."
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════
# FASE 1: ELIMINAR QUANTS (stock físico zombie)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 1: ELIMINANDO QUANTS ZOMBIE ━━━"

DELETED_Q=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_quant
    WHERE lot_id IN (
        SELECT id FROM stock_lot
        WHERE reception_id IS NULL
          AND guia_processing_id IS NULL
          AND name LIKE '%19846%'
          AND name NOT LIKE '%virtual%'
          AND name NOT LIKE '%default%'
    )
    AND quantity > 0
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Quants eliminados: $DELETED_Q"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 2: ELIMINAR STOCK.MOVE.LINE (líneas de movimiento huérfanas)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 2: ELIMINANDO STOCK MOVE LINES ━━━"

DELETED_SML=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move_line
    WHERE lot_id IN (
        SELECT id FROM stock_lot
        WHERE reception_id IS NULL
          AND guia_processing_id IS NULL
          AND name LIKE '%19846%'
          AND name NOT LIKE '%virtual%'
          AND name NOT LIKE '%default%'
    )
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Stock move lines eliminadas: $DELETED_SML"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 3: ELIMINAR STOCK.MOVE (movimientos done sin picking padre)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 3: ELIMINANDO STOCK MOVES HUÉRFANOS ━━━"

DELETED_SM=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_move
    WHERE picking_id IS NULL
      AND state = 'done'
      AND origin = '19846'
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Stock moves eliminados: $DELETED_SM"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 4: ELIMINAR LOTES HUÉRFANOS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 4: ELIMINANDO LOTES HUÉRFANOS ━━━"

DELETED_SL=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_lot
    WHERE reception_id IS NULL
      AND guia_processing_id IS NULL
      AND name LIKE '%19846%'
      AND name NOT LIKE '%virtual%'
      AND name NOT LIKE '%default%'
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Lotes eliminados: $DELETED_SL"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 5: LIMPIAR PICKING ANULADO (opcional, seguro)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━ FASE 5: LIMPIANDO PICKING ANULADO ━━━"

DELETED_SP=$($PSQL -c "
WITH deleted AS (
    DELETE FROM stock_picking
    WHERE origin LIKE '%ANULADO-19846%'
      AND state = 'cancel'
    RETURNING id
)
SELECT COUNT(*) FROM deleted;
")
echo "✅ Pickings cancelados eliminados: $DELETED_SP"

echo ""
echo "✅ SANEAMIENTO COMPLETADO"

# ═══════════════════════════════════════════════════════════════════════════
# FASE 6: VERIFICACIÓN FINAL
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  VERIFICACIÓN FINAL"
echo "═══════════════════════════════════════════════════════"
echo ""

ERRORS=0

echo "V1. Lotes huérfanos residuales (debe ser 0):"
V1=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NULL AND guia_processing_id IS NULL
  AND name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
")
echo "   $V1"
if [ "${V1// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo "V2. Quants zombie (debe ser 0):"
V2=$($PSQL -c "
SELECT COUNT(*) FROM stock_quant sq
JOIN stock_lot sl ON sl.id = sq.lot_id
WHERE sq.quantity > 0 AND sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "   $V2"
if [ "${V2// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo "V3. Move lines huérfanas (debe ser 0):"
V3=$($PSQL -c "
SELECT COUNT(*) FROM stock_move_line sml
JOIN stock_lot sl ON sl.id = sml.lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "   $V3"
if [ "${V3// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo "V4. Moves huérfanos de guía 19846 (debe ser 0):"
V4=$($PSQL -c "
SELECT COUNT(*) FROM stock_move
WHERE picking_id IS NULL AND state = 'done' AND origin = '19846';
")
echo "   $V4"
if [ "${V4// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo "V5. Pickings con ANULADO-19846 (debe ser 0):"
V5=$($PSQL -c "
SELECT COUNT(*) FROM stock_picking
WHERE origin LIKE '%ANULADO-19846%' AND state = 'cancel';
")
echo "   $V5"
if [ "${V5// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo "V6. Guía 19846 — consistencia con estado draft:"
V6=$($PSQL -c "
SELECT name, state, vol_comercial, vol_fisico, vol_total_m3, vol_shipment_m3,
       total_lotes_unicos, total_paquetes
FROM madenat_guia_processing
WHERE name = '19846';
")
echo "   $V6"

echo "V7. Sin violaciones de exclusividad:"
V7=$($PSQL -c "
SELECT COUNT(*) FROM stock_lot
WHERE reception_id IS NOT NULL AND guia_processing_id IS NOT NULL
  AND name NOT LIKE '%virtual%';
")
echo "   $V7"

echo "V8. Sin lotes huérfanos en contenedores:"
V8=$($PSQL -c "
SELECT COUNT(*) FROM lumber_container_stock_lot_rel lclr
JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
WHERE sl.reception_id IS NULL AND sl.guia_processing_id IS NULL
  AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%';
")
echo "   $V8"
if [ "${V8// /}" != "0" ]; then ERRORS=$((ERRORS+1)); fi

echo ""
echo "═══════════════════════════════════════════════════════"

if [ "$ERRORS" -eq 0 ]; then
    echo "✅ VERIFICACIÓN EXITOSA — BD CONSISTENTE"
    echo "   0 residuos, 0 zombies, guía 19846 lista para reprocesar."
else
    echo "❌ VERIFICACIÓN FALLIDA — $ERRORS cheque(s) no pasaron"
    echo "   Revisar las verificaciones V1-V8 arriba."
fi

echo "═══════════════════════════════════════════════════════"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"

unset PGPASSWORD