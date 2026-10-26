#!/bin/bash
# Auditoría de columna lot_reception_date
OUTFILE="/home/viruco/dev-stack/odoo/odoo-18-ce/audit_check_output.txt"
exec > "$OUTFILE" 2>&1

echo "=== AUDITORÍA DE COLUMNA lot_reception_date ==="
echo "Hora: $(date)"
echo ""

echo "--- Paso 1: Estado del módulo ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT name, state, latest_version, to_char(write_date, 'YYYY-MM-DD HH24:MI:SS') as write_date
FROM ir_module_module 
WHERE name = 'madenat_lumber_reports';
"

echo ""
echo "--- Paso 2: Columnas store=True en stock_quant ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name='stock_quant' 
  AND column_name IN ('lot_reception_date','lot_guia_number','lot_purchase_order','lot_supplier','lot_subproducto','lot_escuadria','lot_largo_m','lot_volumen_m3','lot_piezas','lot_container_name','location_name')
ORDER BY column_name;
"

echo ""
echo "--- Paso 3: Todas las columnas lot_% en stock_quant ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name='stock_quant' 
  AND column_name LIKE 'lot_%'
ORDER BY column_name;
"

echo ""
echo "--- Paso 4: Versión del módulo en código ---"
grep "'version'" /mnt/extra-addons/madenat_lumber_reports/__manifest__.py || echo "No se leyó manifest"

echo ""
echo "=== FIN AUDITORÍA ==="