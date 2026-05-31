#!/bin/bash
set -e

echo "A) action_distribute_costs fuera de costing"
grep -R --include="*.py" "action_distribute_costs" . | grep -v "madenat_lumber_costing" || true

echo ""
echo "B) Creación de producto/PO fuera de purchasing"
grep -R --include="*.py" -E "product\.product\(.+create|create\(.+model=.*product\.product" . | grep -v "madenat_lumber_purchasing" || true
grep -R --include="*.py" -E "purchase\.order\(.+create|create\(.+model=.*purchase\.order" . | grep -v "madenat_lumber_purchasing" || true

echo ""
echo "C) Hardcoding en Vendor Payment"
grep -R --include="*.py" -n "_get_expense_account" madenat_vendor_payment || true
grep -R --include="*.py" -n "account_mapping\s*=" madenat_vendor_payment || true

echo ""
echo "D) Hardcoding en Logistics (contenedores)"
grep -R --include="*.py" -n -E "tare_weights\s*=|capacities\s*=" madenat_lumber_logistics || true

echo ""
echo "E) Computes con search() en product.product (heurística)"
grep -R --include="*.py" -n "class\s\+ProductProduct" -n madenat_lumber_core || true
grep -R --include="*.py" -n "_compute" madenat_lumber_core | grep "search(" || true
