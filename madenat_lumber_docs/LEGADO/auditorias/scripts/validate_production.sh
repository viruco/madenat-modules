#!/bin/bash
# Script de validación pre-producción para madenat_lumber_core

echo "🚀 VALIDACIÓN PRE-PRODUCCIÓN - MADENAT Lumber Core"
echo "=================================================="

# Verificar que el módulo esté instalado
echo "1. Verificando instalación del módulo..."
docker-compose exec web odoo --config=/etc/odoo/odoo.conf shell -d madenat_test -c "
from odoo import api, SUPERUSER_ID
env = api.Environment(api.Registry.managed('madenat_test').cursor(), SUPERUSER_ID, {})
module = env['ir.module.module'].search([('name', '=', 'madenat_lumber_core')])
print(f'Módulo encontrado: {module.name if module else \"NO ENCONTRADO\"}')
print(f'Estado: {module.state if module else \"N/A\"}')
"

echo ""
echo "2. Creando recepción de prueba..."
docker-compose exec web odoo --config=/etc/odoo/odoo.conf shell -d madenat_test -c "
from odoo import api, SUPERUSER_ID
env = api.Environment(api.Registry.managed('madenat_test').cursor(), SUPERUSER_ID, {})
partner = env['res.partner'].create({'name': 'Test Supplier', 'supplier_rank': 1})
reception = env['lumber.reception'].create({
    'name': 'VALIDATION-001',
    'supplier_id': partner.id,
    'commercial_volume_m3': 10.0,
    'state': 'draft'
})
print(f'Recepción creada: {reception.name}')
print(f'Estado: {reception.state}')
print(f'Volumen comercial: {reception.commercial_volume_m3}')
"

echo ""
echo "3. Probando cálculo volumétrico..."
docker-compose exec web odoo --config=/etc/odoo/odoo.conf shell -d madenat_test -c "
from odoo import api, SUPERUSER_ID
env = api.Environment(api.Registry.managed('madenat_test').cursor(), SUPERUSER_ID, {})
reception = env['lumber.reception'].search([('name', '=', 'VALIDATION-001')])
line = env['lumber.reception.line'].create({
    'reception_id': reception.id,
    'lot_name': 'TEST-001',
    'product_id': env['product.product'].create({'name': 'Test Product'}).id,
    'thickness': 25.0,
    'width': 100.0,
    'length': 2.0,
    'pieces': 1,
})
print(f'Línea creada: {line.lot_name}')
print(f'Volumen físico: {line.vol_physical_m3}')
print(f'Volumen comercial: {line.vol_purchase_m3}')
"

echo ""
echo "✅ VALIDACIÓN COMPLETADA"
echo "Revisa los resultados arriba. Si todo está OK, proceder con deployment."