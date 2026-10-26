#!/usr/bin/env python3
"""Check 19846 data directly via psycopg2 to Odoo DB."""
import subprocess, sys, os

os.chdir("/home/viruco/dev-stack/odoo/odoo-18-ce")

def run_psql(sql):
    """Run SQL via docker compose exec -T db, capturing output."""
    proc = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-U", "odoo", "-d", "madenat_test", "-c", sql],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "SSH_AUTH_SOCK": "", "SSH_AGENT_PID": ""}
    )
    return proc.stdout + proc.stderr

print("=== GUIA 19846 ===")
print(run_psql("""
SELECT id, name, order_id, oc_reference_raw, oc_reference_norm, oc_match_status, oc_match_note
FROM madenat_guia_processing
WHERE name = '19846'
ORDER BY id DESC
LIMIT 3;
"""))

print("=== VISTA FORM XML ID ===")
print(run_psql("""
SELECT ir_ui_view.id, ir_ui_view.name, ir_ui_view.inherit_id, ir_ui_view.mode
FROM ir_ui_view
JOIN ir_model ON ir_ui_view.model = ir_model.model
WHERE ir_ui_view.model = 'madenat.guia.processing'
  AND ir_ui_view.type = 'form'
  AND ir_ui_view.active = true
ORDER BY ir_ui_view.priority ASC, ir_ui_view.id ASC;
"""))

print("=== oc_reference_norm IN VIEW ARCH ===")
print(run_psql("""
SELECT id, name,
       (arch_db::text LIKE '%oc_reference_norm%') AS has_norm,
       (arch_db::text LIKE '%oc_reference_raw%') AS has_raw,
       (arch_db::text LIKE '%order_id%') AS has_order_id
FROM ir_ui_view
WHERE model = 'madenat.guia.processing'
  AND type = 'form'
  AND inherit_id IS NULL
  AND active = true
ORDER BY priority ASC, id ASC
LIMIT 1;
"""))