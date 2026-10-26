#!/usr/bin/env python3
"""Auditoría de columna lot_reception_date — v2 usando subprocess como run_audit.py"""
import subprocess
import os

def run_sql(query):
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
    return result.stdout, result.stderr, result.returncode

output_lines = []

q1 = "SELECT name, state, latest_version FROM ir_module_module WHERE name = 'madenat_lumber_reports';"
out, err, rc = run_sql(q1)
output_lines.append(f"=== STEP1: MODULE STATE (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

q2 = """SELECT column_name, data_type FROM information_schema.columns WHERE table_name='stock_quant' AND column_name LIKE 'lot_%' ORDER BY column_name;"""
out, err, rc = run_sql(q2)
output_lines.append(f"\n=== STEP2: lot_%% COLUMNS (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

q3 = "SELECT column_name FROM information_schema.columns WHERE table_name='stock_quant' AND column_name IN ('lot_reception_date','lot_guia_number','lot_purchase_order','lot_supplier','lot_subproducto','lot_escuadria','lot_largo_m','lot_volumen_m3','lot_piezas','lot_container_name','location_name') ORDER BY column_name;"
out, err, rc = run_sql(q3)
output_lines.append(f"\n=== STEP3: 11 STORE=TRUE COLUMNS CHECK (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

text = '\n'.join(output_lines)
print(text)

with open('/home/viruco/dev-stack/odoo/odoo-18-ce/audit_v2_result.txt', 'w') as f:
    f.write(text)