#!/bin/bash
# Auditoría de XML IDs - Salida a archivo
OUTFILE="/home/viruco/dev-stack/odoo/odoo-18-ce/audit_output.txt"
exec > "$OUTFILE" 2>&1

echo "=== AUDITORÍA XML IDs ==="
echo "Hora: $(date)"
echo ""

echo "--- 1. Verificando IDs NUEVOS ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT module, name, model, res_id 
FROM ir_model_data 
WHERE name IN (
    'action_r1_stock_detail_patio',
    'action_server_r1_stock_detail_xlsx',
    'view_stock_quant_tree_r1_detail_patio',
    'menu_r1_detail_location',
    'action_export_r1_stock_detail_xlsx'
)
ORDER BY module, name;
"

echo ""
echo "--- 2. Verificando IDs VIEJOS (view_stock_lot_*) ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT module, name, model, res_id 
FROM ir_model_data 
WHERE name LIKE 'view_stock_lot_%'
ORDER BY module, name;
"

echo ""
echo "--- 3. Búsqueda extra: cualquier XML ID con 'stock_lot' ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT module, name, model, res_id 
FROM ir_model_data 
WHERE name ILIKE '%stock_lot%'
ORDER BY module, name;
"

echo ""
echo "=== FIN AUDITORÍA ==="