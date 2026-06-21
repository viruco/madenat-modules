#!/usr/bin/env python3
"""
Script de auditoría: Diagnóstico de trazabilidad de lotes.
Verifica:
1. Cuántos lotes tienen reception_id vs guia_processing_id
2. Cuántos lotes de cada flujo no tienen FK de origen
3. Si hay violaciones de exclusividad
4. Estado de contenedores respecto a lotes
5. Cobertura en reportes

v2.0 (2026-06-16): Eliminada dependencia de lumber_reception_id legacy.
   reception_id es la FK canónica única.
"""
import psycopg2
import json

OUTFILE = "/mnt/extra-addons/_audit_trazabilidad_result.json"

results = {}

try:
    conn = psycopg2.connect(host="db", port=5432, dbname="madenattest", user="odoo", password="odoo")
    cur = conn.cursor()
    
    # ── A. TABLA stock_lot: campos de origen ──
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='stock_lot' 
          AND column_name IN ('reception_id', 'guia_processing_id', 'reception_type')
        ORDER BY column_name;
    """)
    results["columns_stock_lot"] = [list(r) for r in cur.fetchall()]
    
    # ── B. Distribución de lotes por FK de origen ──
    cur.execute("""
        SELECT 
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_id,
            COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_processing_id,
            COUNT(*) FILTER (WHERE reception_id IS NOT NULL AND guia_processing_id IS NOT NULL) AS violates_exclusivity,
            COUNT(*) FILTER (WHERE reception_id IS NULL AND guia_processing_id IS NULL) AS no_origin_fk
        FROM stock_lot
        WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
    """)
    results["lot_distribution"] = [list(r) for r in cur.fetchall()]
    
    # ── C. Lotes con reception_type ──
    cur.execute("""
        SELECT reception_type, COUNT(*) AS cnt
        FROM stock_lot
        WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%'
        GROUP BY reception_type
        ORDER BY cnt DESC;
    """)
    results["reception_type_distribution"] = [list(r) for r in cur.fetchall()]
    
    # ── D. Lotes raw (recepción directa) sin reception_id ──
    cur.execute("""
        SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number
        FROM stock_lot
        WHERE reception_type = 'raw'
          AND reception_id IS NULL
        LIMIT 30;
    """)
    results["raw_lots_no_fk"] = [list(r) for r in cur.fetchall()]
    
    # ── E. Lotes processed (guía procesada) ──
    cur.execute("""
        SELECT COUNT(*) AS cnt,
               COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_fk,
               COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_fk
        FROM stock_lot
        WHERE reception_type = 'processed'
          AND name NOT LIKE '%virtual%';
    """)
    results["processed_lots_fk"] = [list(r) for r in cur.fetchall()]
    
    # ── F. Lotes que son recepción directa pero reception_type es NULL ──
    cur.execute("""
        SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number
        FROM stock_lot
        WHERE reception_id IS NOT NULL 
          AND reception_type IS NULL
        LIMIT 30;
    """)
    results["reception_lots_no_type"] = [list(r) for r in cur.fetchall()]
    
    # ── G. Lotes con reception_id poblado ──
    cur.execute("""
        SELECT 
            COUNT(*) AS cnt,
            COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_canonical_fk
        FROM stock_lot
        WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
    """)
    results["canonical_fk_coverage"] = [list(r) for r in cur.fetchall()]
    
    # ── H. Tabla lumber_container ──
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name LIKE '%container%' AND table_schema='public';
    """)
    results["container_tables"] = [list(r) for r in cur.fetchall()]
    
    # ── I. Cantidad de contenedores y lotes asignados ──
    try:
        cur.execute("""
            SELECT COUNT(*) AS total_containers FROM lumber_container;
        """)
        results["container_count"] = [list(r) for r in cur.fetchall()]
        
        cur.execute("""
            SELECT COUNT(DISTINCT lot_id) AS total_lots_in_containers 
            FROM lumber_container_lot_rel;
        """)
        results["lots_in_containers"] = [list(r) for r in cur.fetchall()]
    except Exception as e:
        results["container_error"] = str(e)
    
    # ── J. Muestra de lotes: 10 de cada flujo ──
    cur.execute("""
        SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number
        FROM stock_lot
        WHERE reception_type = 'raw' AND name NOT LIKE '%virtual%'
        LIMIT 10;
    """)
    results["sample_raw_lots"] = [list(r) for r in cur.fetchall()]
    
    cur.execute("""
        SELECT id, name, reception_id, guia_processing_id, reception_type, guia_number
        FROM stock_lot
        WHERE reception_type = 'processed' AND name NOT LIKE '%virtual%'
        LIMIT 10;
    """)
    results["sample_processed_lots"] = [list(r) for r in cur.fetchall()]
    
    conn.close()
except Exception as e:
    results["error"] = str(e)

with open(OUTFILE, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(json.dumps(results, indent=2, ensure_ascii=False, default=str))