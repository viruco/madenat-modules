#!/usr/bin/env python3
"""Ejecuta auditoría SQL y guarda resultados en audit_result.txt"""
import subprocess
import os

def run_sql(query):
    """Ejecuta una consulta SQL contra PostgreSQL y retorna salida"""
    env = {k: v for k, v in os.environ.items() if not k.startswith('SSH_')}
    env.pop('SSH_AGENT_PID', None)
    env.pop('SSH_AUTH_SOCK', None)
    env.pop('SSH_ASKPASS', None)
    env.pop('GIT_SSH', None)
    env.pop('GIT_SSH_COMMAND', None)
    
    cmd = [
        'docker', 'exec', 'odoo18_db',
        'psql', '-U', 'odoo', '-d', 'madenat_test',
        '-c', query
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
    return {
        'stdout': result.stdout,
        'stderr': result.stderr,
        'rc': result.returncode
    }

output_lines = []
output_lines.append("=" * 60)
output_lines.append("AUDITORÍA DE XML IDs - R1 STOCK DETAIL")
output_lines.append("=" * 60)

# Paso 1: IDs nuevos
output_lines.append("\n--- PASO 1: IDs NUEVOS (deben existir 5) ---")
r = run_sql("""
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
""")
output_lines.append(f"RC={r['rc']}")
output_lines.append(r['stdout'] if r['stdout'] else "(empty)")
if r['stderr']:
    output_lines.append(f"STDERR: {r['stderr']}")

# Paso 2: IDs viejos
output_lines.append("\n--- PASO 2: IDs VIEJOS view_stock_lot_* (deben ser 0) ---")
r = run_sql("""
SELECT module, name, model, res_id 
FROM ir_model_data 
WHERE name LIKE 'view_stock_lot_%'
ORDER BY module, name;
""")
output_lines.append(f"RC={r['rc']}")
output_lines.append(r['stdout'] if r['stdout'] else "(empty)")
if r['stderr']:
    output_lines.append(f"STDERR: {r['stderr']}")

# Paso 3: Búsqueda extra
output_lines.append("\n--- PASO 3: Cualquier stock_lot residual ---")
r = run_sql("""
SELECT module, name, model, res_id 
FROM ir_model_data 
WHERE name ILIKE '%stock_lot%'
ORDER BY module, name;
""")
output_lines.append(f"RC={r['rc']}")
output_lines.append(r['stdout'] if r['stdout'] else "(empty)")
if r['stderr']:
    output_lines.append(f"STDERR: {r['stderr']}")

output_lines.append("\n" + "=" * 60)
output_lines.append("FIN AUDITORÍA")

text = '\n'.join(output_lines)
print(text)

# Escribir a archivo
with open('/home/viruco/dev-stack/odoo/odoo-18-ce/audit_result.txt', 'w') as f:
    f.write(text)