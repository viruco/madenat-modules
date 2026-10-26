#!/usr/bin/env python3
"""Auditoría de trazabilidad de lotes — usando subprocess como run_audit.py

v2.0 (2026-06-16): Eliminada dependencia de lumber_reception_id legacy.
   reception_id es la FK canónica única.
"""
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

# 1. Columnas en stock_lot
out, err, rc = run_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='stock_lot' AND column_name IN ('reception_id','guia_processing_id','reception_type') ORDER BY column_name;")
output_lines.append(f"=== 1. COLUMNAS EN stock_lot (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 2. Distribución de lotes
out, err, rc = run_sql("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_id, COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_processing_id, COUNT(*) FILTER (WHERE reception_id IS NULL AND guia_processing_id IS NULL) AS no_origin_fk FROM stock_lot;")
output_lines.append(f"\n=== 2. DISTRIBUCION DE LOTES (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 3. reception_type
out, err, rc = run_sql("SELECT reception_type, COUNT(*) AS cnt FROM stock_lot GROUP BY reception_type ORDER BY cnt DESC;")
output_lines.append(f"\n=== 3. RECEPTION TYPE (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 4. Lotes raw sin FK
out, err, rc = run_sql("SELECT id, name, reception_id, guia_processing_id, reception_type FROM stock_lot WHERE reception_type = 'raw' AND reception_id IS NULL LIMIT 15;")
output_lines.append(f"\n=== 4. LOTES RAW SIN FK (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 5. Lotes processed
out, err, rc = run_sql("SELECT COUNT(*) AS cnt, COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_fk FROM stock_lot WHERE reception_type = 'processed';")
output_lines.append(f"\n=== 5. LOTES PROCESSED (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 6. Containers
out, err, rc = run_sql("SELECT COUNT(*) AS total_containers FROM lumber_container;")
output_lines.append(f"\n=== 6. CONTAINERS (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 7. Lots in containers
out, err, rc = run_sql("SELECT COUNT(DISTINCT lot_id) AS lots_in_containers FROM lumber_container_lot_rel;")
output_lines.append(f"\n=== 7. LOTS IN CONTAINERS (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 8. Sample raw lots
out, err, rc = run_sql("SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number FROM stock_lot WHERE reception_type = 'raw' LIMIT 10;")
output_lines.append(f"\n=== 8. SAMPLE RAW LOTS (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 9. Sample processed lots
out, err, rc = run_sql("SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number FROM stock_lot WHERE reception_type = 'processed' LIMIT 10;")
output_lines.append(f"\n=== 9. SAMPLE PROCESSED LOTS (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

# 10. reception_id IS NOT NULL but reception_type IS NULL
out, err, rc = run_sql("SELECT id, name, reception_id, guia_processing_id, reception_type FROM stock_lot WHERE reception_id IS NOT NULL AND reception_type IS NULL LIMIT 15;")
output_lines.append(f"\n=== 10. RECEPTION_ID NOT NULL BUT TYPE NULL (rc={rc}) ===")
output_lines.append(out if out else "(empty stdout)")
if err: output_lines.append(f"STDERR: {err}")

text = '\n'.join(output_lines)
print(text)

with open('/home/viruco/dev-stack/odoo/odoo-18-ce/audit_trazabilidad_result.txt', 'w') as f:
    f.write(text)