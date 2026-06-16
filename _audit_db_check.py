#!/usr/bin/env python3
"""
Script de auditoría: Verifica estado del módulo y columnas en stock_quant.
Se ejecuta DENTRO del contenedor odoo18_app, que tiene acceso a la BD vía host=db.
Resultado se escribe en /mnt/extra-addons/_audit_result.json
"""
import psycopg2
import json

OUTFILE = "/mnt/extra-addons/_audit_result.json"

results = {}

try:
    conn = psycopg2.connect(host="db", port=5432, dbname="madenat_test", user="odoo", password="odoo")
    cur = conn.cursor()
    
    # Paso 1: Estado del módulo
    cur.execute("SELECT name, state, latest_version FROM ir_module_module WHERE name = 'madenat_lumber_reports';")
    results["module_state"] = [list(r) for r in cur.fetchall()]
    
    # Paso 2: Columnas lot_% en stock_quant
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='stock_quant' AND column_name LIKE 'lot_%' ORDER BY column_name;")
    results["lot_columns"] = [list(r) for r in cur.fetchall()]
    
    # Paso 3: location_name
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='stock_quant' AND column_name='location_name';")
    results["location_name_exists"] = bool(cur.fetchall())
    
    conn.close()
except Exception as e:
    results["error"] = str(e)

with open(OUTFILE, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(json.dumps(results, indent=2, ensure_ascii=False))