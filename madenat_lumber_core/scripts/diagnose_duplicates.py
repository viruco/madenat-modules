#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🩺 DIAGNÓSTICO FORENSE DE DUPLICADOS — madenat_lumber_core
===========================================================
NO DESTRUCTIVO. Solo lectura. Exporta CSV con hallazgos.

Uso:
    python3 diagnose_duplicates.py --db <nombre_db> [--output <archivo.csv>]

Claves naturales analizadas:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Tabla                  | Clave Natural                          | Check |
|------------------------|----------------------------------------|-------|
| lumber.reception       | name + company_id                      | ✅     |
| madenat.guia.processing| name + partner_id + company_id          | ✅     |
| stock.lot (recepción)  | name + product_id + reception_id       | ✅     |
| stock.lot (guía proc)  | name + product_id + guia_processing_id | ✅     |
| stock.lot.cost.line    | lot_id + name + cost_type              | ✅     |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ No borra, no modifica, no muta. Solo reporta.
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict

# ─────────────────────────────────────────────────────────────
# UTILIDADES DE REPORTE
# ─────────────────────────────────────────────────────────────

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def format_count(n):
    return f"{n:,}" if n is not None else "N/A"


# ─────────────────────────────────────────────────────────────
# CONSULTAS SQL (READ-ONLY)
# ─────────────────────────────────────────────────────────────

QUERY_LUMBER_RECEPTION_DUPS = """
WITH grouped AS (
    SELECT name, company_id, COUNT(*) AS cnt
    FROM lumber_reception
    GROUP BY name, company_id
    HAVING COUNT(*) > 1
)
SELECT lr.id, lr.name, lr.state, lr.supplier_id, lr.create_date,
       rp.name AS supplier_name
FROM lumber_reception lr
JOIN grouped g ON lr.name = g.name AND lr.company_id = g.company_id
LEFT JOIN res_partner rp ON lr.supplier_id = rp.id
ORDER BY lr.name, lr.id
"""

QUERY_GUIA_PROCESSING_DUPS = """
WITH grouped AS (
    SELECT name, partner_id, company_id, COUNT(*) AS cnt
    FROM madenat_guia_processing
    GROUP BY name, partner_id, company_id
    HAVING COUNT(*) > 1
)
SELECT mgp.id, mgp.name, mgp.state, mgp.partner_id, mgp.create_date,
       rp.name AS partner_name
FROM madenat_guia_processing mgp
JOIN grouped g ON mgp.name = g.name AND mgp.partner_id = g.partner_id
                   AND mgp.company_id = g.company_id
LEFT JOIN res_partner rp ON mgp.partner_id = rp.id
ORDER BY mgp.name, mgp.id
"""

QUERY_STOCK_LOT_RECEPTION_DUPS = """
WITH grouped AS (
    SELECT sl.name, sl.product_id, sl.reception_id, COUNT(*) AS cnt
    FROM stock_lot sl
    WHERE sl.reception_id IS NOT NULL
    GROUP BY sl.name, sl.product_id, sl.reception_id
    HAVING COUNT(*) > 1
)
SELECT sl.id, sl.name, sl.product_id, sl.reception_id, sl.create_date,
       pt.name AS product_name, lr.name AS reception_name
FROM stock_lot sl
JOIN grouped g ON sl.name = g.name AND sl.product_id = g.product_id
               AND sl.reception_id = g.reception_id
LEFT JOIN product_template pt ON sl.product_id = pt.id
LEFT JOIN lumber_reception lr ON sl.reception_id = lr.id
ORDER BY sl.reception_id, sl.name, sl.id
"""

QUERY_STOCK_LOT_GUIA_DUPS = """
WITH grouped AS (
    SELECT sl.name, sl.product_id, sl.guia_processing_id, COUNT(*) AS cnt
    FROM stock_lot sl
    WHERE sl.guia_processing_id IS NOT NULL
    GROUP BY sl.name, sl.product_id, sl.guia_processing_id
    HAVING COUNT(*) > 1
)
SELECT sl.id, sl.name, sl.product_id, sl.guia_processing_id, sl.create_date,
       pt.name AS product_name, mgp.name AS guia_name
FROM stock_lot sl
JOIN grouped g ON sl.name = g.name AND sl.product_id = g.product_id
               AND sl.guia_processing_id = g.guia_processing_id
LEFT JOIN product_template pt ON sl.product_id = pt.id
LEFT JOIN madenat_guia_processing mgp ON sl.guia_processing_id = mgp.id
ORDER BY sl.guia_processing_id, sl.name, sl.id
"""

QUERY_COST_LINE_DUPS = """
WITH grouped AS (
    SELECT lot_id, name, cost_type, COUNT(*) AS cnt
    FROM stock_lot_cost_line
    GROUP BY lot_id, name, cost_type
    HAVING COUNT(*) > 1
)
SELECT slcl.id, slcl.lot_id, slcl.name, slcl.cost_type,
       slcl.amount_usd, slcl.create_date,
       sl.name AS lot_name
FROM stock_lot_cost_line slcl
JOIN grouped g ON slcl.lot_id = g.lot_id AND slcl.name = g.name
               AND slcl.cost_type = g.cost_type
LEFT JOIN stock_lot sl ON slcl.lot_id = sl.id
ORDER BY slcl.lot_id, slcl.name, slcl.id
"""

# ─────────────────────────────────────────────────────────────
# MOTOR PRINCIPAL
# ─────────────────────────────────────────────────────────────

def run_diagnosis(cr, output_file=None):
    """
    Ejecuta todas las consultas de diagnóstico y genera reporte.
    
    Args:
        cr: cursor de base de datos (psycopg2)
        output_file: ruta opcional para exportar CSV
    
    Returns:
        dict con resumen de hallazgos
    """
    results = {}
    rows_written = 0
    
    checks = [
        ("lumber.reception (cabeceras guía bruta)",
         QUERY_LUMBER_RECEPTION_DUPS,
         ["id", "name", "state", "supplier_id", "create_date", "supplier_name"]),
        
        ("madenat.guia.processing (cabeceras guía procesada)",
         QUERY_GUIA_PROCESSING_DUPS,
         ["id", "name", "state", "partner_id", "create_date", "partner_name"]),
        
        ("stock.lot → lumber.reception (lotes duplicados en recepción)",
         QUERY_STOCK_LOT_RECEPTION_DUPS,
         ["id", "name", "product_id", "reception_id", "create_date",
          "product_name", "reception_name"]),
        
        ("stock.lot → madenat.guia.processing (lotes duplicados en guía procesada)",
         QUERY_STOCK_LOT_GUIA_DUPS,
         ["id", "name", "product_id", "guia_processing_id", "create_date",
          "product_name", "guia_name"]),
        
        ("stock.lot.cost.line (líneas de costo duplicadas)",
         QUERY_COST_LINE_DUPS,
         ["id", "lot_id", "name", "cost_type", "amount_usd", "create_date", "lot_name"]),
    ]
    
    csv_writer = None
    csv_file = None
    
    if output_file:
        csv_file = open(output_file, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["TABLA", "ID", "CLAVE_NATURAL", "DETALLE", "FECHA_CREACION"])
    
    total_dups = 0
    
    for label, query, columns in checks:
        print_section(f"🔍 Analizando: {label}")
        
        try:
            cr.execute(query)
            rows = cr.fetchall()
        except Exception as e:
            print(f"  ⚠️ Error ejecutando consulta: {e}")
            results[label] = {"count": None, "error": str(e)}
            continue
        
        if not rows:
            print(f"  ✅ Sin duplicados detectados.")
            results[label] = {"count": 0}
            continue
        
        # Agrupar por clave natural
        groups = defaultdict(list)
        for row in rows:
            record = dict(zip(columns, row))
            # Construir clave natural según el tipo de consulta
            if "guia_processing_id" in record:
                key = f"{record.get('name')}|{record.get('product_id')}|{record.get('guia_processing_id')}"
            elif "reception_id" in record:
                key = f"{record.get('name')}|{record.get('product_id')}|{record.get('reception_id')}"
            elif "lot_id" in record and "cost_type" in record:
                key = f"{record.get('lot_id')}|{record.get('name')}|{record.get('cost_type')}"
            elif "partner_id" in record:
                key = f"{record.get('name')}|{record.get('partner_id')}"
            else:
                key = f"{record.get('name')}"
            groups[key].append(record)
        
        count_groups = len(groups)
        count_rows = len(rows)
        total_dups += count_rows
        
        print(f"  ⚠️  {count_groups} grupo(s) con duplicados ({count_rows} registros totales):")
        
        for key, recs in groups.items():
            ids = [str(r['id']) for r in recs]
            fechas = [str(r.get('create_date', 'N/A')) for r in recs]
            print(f"     └─ {key}: {len(recs)} registros → IDs: {', '.join(ids)}")
            
            if csv_writer:
                for rec in recs:
                    csv_writer.writerow([
                        label,
                        rec['id'],
                        key,
                        str({k: v for k, v in rec.items() if k != 'id'}),
                        str(rec.get('create_date', 'N/A'))
                    ])
        
        results[label] = {"count": count_rows, "groups": count_groups}
    
    # ── RESUMEN FINAL ──
    print_section("📊 RESUMEN DE DIAGNÓSTICO")
    for label, info in results.items():
        if info.get("error"):
            print(f"  ❌ {label}: ERROR — {info['error']}")
        elif info["count"] == 0:
            print(f"  ✅ {label}: limpio")
        else:
            print(f"  ⚠️  {label}: {info['count']} registros duplicados en {info['groups']} grupos")
    
    print(f"\n  📋 Total general de registros duplicados: {format_count(total_dups)}")
    
    if output_file and csv_writer:
        csv_file.close()
        print(f"\n  💾 Reporte CSV exportado a: {output_file}")
    
    print("\n⚠️  RECOMENDACIÓN: No elimine registros automáticamente.")
    print("   Revise cada grupo duplicado y decida manualmente cuál conservar.")
    print("   Considere: trazabilidad, costos asociados, movimientos de stock vinculados.\n")
    
    return results


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🩺 Diagnóstico forense de duplicados en madenat_lumber_core"
    )
    parser.add_argument(
        "--db", required=True,
        help="Nombre de la base de datos Odoo"
    )
    parser.add_argument(
        "--output", default=None,
        help="Archivo CSV de salida (opcional)"
    )
    parser.add_argument(
        "--host", default="localhost",
        help="Host de PostgreSQL (default: localhost)"
    )
    parser.add_argument(
        "--port", default="5432",
        help="Puerto de PostgreSQL (default: 5432)"
    )
    parser.add_argument(
        "--user", default="odoo",
        help="Usuario de PostgreSQL (default: odoo)"
    )
    
    args = parser.parse_args()
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname=args.db,
            host=args.host,
            port=args.port,
            user=args.user
        )
        conn.autocommit = True
        cr = conn.cursor()
    except ImportError:
        print("❌ Se requiere psycopg2. Instálelo con: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)
    
    try:
        run_diagnosis(cr, args.output)
    finally:
        cr.close()
        conn.close()


if __name__ == "__main__":
    main()