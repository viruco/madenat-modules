#!/bin/bash
set -e
cd /home/viruco/dev-stack/odoo/odoo-18-ce

echo "=== GUIA 19846 ==="
docker compose exec -T db psql -U odoo -d madenat_test -c "
SELECT id, name, order_id, oc_reference_raw, oc_reference_norm, oc_match_status, oc_match_note
FROM madenat_guia_processing
WHERE name = '19846'
ORDER BY id DESC
LIMIT 3;
"

echo ""
echo "=== PURCHASE.ORDER vinculada ==="
ORDER_ID=$(docker compose exec -T db psql -U odoo -d madenat_test -t -c "SELECT order_id FROM madenat_guia_processing WHERE name='19846' ORDER BY id DESC LIMIT 1;" 2>/dev/null | head -1 | tr -d ' ')
if [ -n "$ORDER_ID" ] && [ "$ORDER_ID" != "" ]; then
    docker compose exec -T db psql -U odoo -d madenat_test -c "
    SELECT id, name, state, partner_id, date_order
    FROM purchase_order
    WHERE id = $ORDER_ID;
    "
fi

echo ""
echo "=== VISTA FORM XML ID ==="
docker compose exec -T db psql -U odoo -d madenat_test -c "
SELECT ir_ui_view.id, ir_ui_view.name, ir_ui_view.inherit_id, ir_ui_view.mode
FROM ir_ui_view
JOIN ir_model ON ir_ui_view.model = ir_model.model
WHERE ir_ui_view.model = 'madenat.guia.processing'
  AND ir_ui_view.type = 'form'
  AND ir_ui_view.active = true
ORDER BY ir_ui_view.priority ASC, ir_ui_view.id ASC;
"

echo ""
echo "=== CAMPOS EN LA VISTA FORM PRIMARIA ==="
docker compose exec -T db psql -U odoo -d madenat_test -c "
SELECT id, name, arch_db::text LIKE '%oc_reference_norm%' AS has_norm,
       arch_db::text LIKE '%oc_reference_raw%' AS has_raw,
       arch_db::text LIKE '%oc_match_status%' AS has_status,
       arch_db::text LIKE '%order_id%' AS has_order_id
FROM ir_ui_view
WHERE model = 'madenat.guia.processing'
  AND type = 'form'
  AND inherit_id IS NULL
  AND active = true
ORDER BY priority ASC, id ASC
LIMIT 1;
"