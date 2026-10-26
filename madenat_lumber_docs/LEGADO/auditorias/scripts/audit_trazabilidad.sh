#!/bin/bash
OUTFILE="/home/viruco/dev-stack/odoo/odoo-18-ce/audit_trazabilidad_output.txt"
unset SSH_AUTH_SOCK SSH_AGENT_PID SSH_ASKPASS
exec > "$OUTFILE" 2>&1

echo "=== AUDITORIA TRAZABILIDAD LOTES ==="
echo "Hora: $(date)"
echo ""

echo "--- 1. Columnas en stock_lot ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='stock_lot' AND column_name IN ('reception_id','guia_processing_id','reception_type') ORDER BY column_name;"

echo ""
echo "--- 2. Distribucion de lotes ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_id, COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_processing_id, COUNT(*) FILTER (WHERE reception_id IS NULL AND guia_processing_id IS NULL) AS no_origin_fk FROM stock_lot;"

echo ""
echo "--- 3. reception_type distribution ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT reception_type, COUNT(*) AS cnt FROM stock_lot GROUP BY reception_type ORDER BY cnt DESC;"

echo ""
echo "--- 4. Lotes raw sin FK ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT id, name, reception_id, guia_processing_id, reception_type FROM stock_lot WHERE reception_type = 'raw' AND reception_id IS NULL LIMIT 15;"

echo ""
echo "--- 5. Lotes processed ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT COUNT(*) AS cnt, COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_fk FROM stock_lot WHERE reception_type = 'processed';"

echo ""
echo "--- 6. lumber_container count ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT COUNT(*) AS total_containers FROM lumber_container;"

echo ""
echo "--- 7. Lots in containers ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT COUNT(DISTINCT lot_id) AS lots_in_containers FROM lumber_container_lot_rel;"

echo ""
echo "--- 8. Sample raw lots with reception_id ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number FROM stock_lot WHERE reception_type = 'raw' LIMIT 10;"

echo ""
echo "--- 9. Sample processed lots ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number FROM stock_lot WHERE reception_type = 'processed' LIMIT 10;"

echo ""
echo "--- 10. Lots with reception_id but reception_type is NULL ---"
docker exec odoo18_db psql -U odoo -d madenat_test -c "SELECT id, name, reception_id, guia_processing_id, reception_type FROM stock_lot WHERE reception_id IS NOT NULL AND reception_type IS NULL LIMIT 15;"

echo ""
echo "=== FIN AUDITORIA ==="