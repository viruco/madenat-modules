#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA DE STOCK — FASE 1 Y 2
═══════════════════════════════════════════════
Alcance: stock.picking, stock.move, stock.move.line, stock.quant, stock.lot,
         guiaprocessingid, receptionid, containerid, shipmentline

Genera:
  Fase 1: Auditoría completa — identifica todos los registros problemáticos
  Fase 2: Clasificación — Conservado / Anulado / Huérfano / Duplicado / Residuo técnico / Revisión manual

Output: JSON en /tmp/_audit_completa_stock.json
"""
import psycopg2
import json
from datetime import datetime

DB = {"host": "db", "port": 5432, "dbname": "madenat_test", "user": "odoo", "password": "odoo"}
OUTFILE = "/tmp/_audit_completa_stock.json"

results = {
    "meta": {
        "fecha": datetime.now().isoformat(),
        "database": DB["dbname"],
        "fases": ["auditoria", "clasificacion", "limpieza_segura"]
    }
}

try:
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN A — PANORAMA GENERAL DE STOCK
    # ═══════════════════════════════════════════════════════════════════

    # A1. stock.picking — distribución por estado
    cur.execute("""
        SELECT state, COUNT(*) AS cnt,
               COUNT(*) FILTER (WHERE origin LIKE '%19846%' OR origin LIKE '%REVERTIDO%' OR origin LIKE '%ANULADO%') AS problematicos
        FROM stock_picking
        GROUP BY state ORDER BY cnt DESC;
    """)
    results["A1_pickings_por_estado"] = [list(r) for r in cur.fetchall()]

    # A2. stock.move — distribución por estado
    cur.execute("SELECT state, COUNT(*) AS cnt FROM stock_move GROUP BY state ORDER BY cnt DESC;")
    results["A2_moves_por_estado"] = [list(r) for r in cur.fetchall()]

    # A3. stock.move.line — total y con/sin move asociado
    cur.execute("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE move_id IS NULL) AS sin_move,
               COUNT(*) FILTER (WHERE picking_id IS NULL) AS sin_picking,
               COUNT(*) FILTER (WHERE lot_id IS NULL) AS sin_lote
        FROM stock_move_line;
    """)
    results["A3_move_lines_resumen"] = [list(r) for r in cur.fetchall()]

    # A4. stock.quant — total, con stock positivo, ubicaciones
    cur.execute("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE quantity > 0) AS stock_positivo,
               COUNT(*) FILTER (WHERE quantity < 0) AS stock_negativo,
               COUNT(*) FILTER (WHERE lot_id IS NOT NULL) AS con_lote,
               COUNT(*) FILTER (WHERE lot_id IS NULL) AS sin_lote,
               SUM(quantity) FILTER (WHERE quantity > 0) AS total_cantidad_positiva
        FROM stock_quant;
    """)
    results["A4_quants_resumen"] = [list(r) for r in cur.fetchall()]

    # A5. stock.lot — distribución general
    cur.execute("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%') AS reales,
               COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS con_recepcion,
               COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS con_guia,
               COUNT(*) FILTER (WHERE reception_id IS NULL AND guia_processing_id IS NULL) AS sin_fk_origen,
               COUNT(*) FILTER (WHERE technical_validation = 'rejected') AS rejected,
               COUNT(*) FILTER (WHERE technical_validation = 'approved') AS approved,
               COUNT(*) FILTER (WHERE technical_validation = 'pending') AS pending
        FROM stock_lot;
    """)
    results["A5_lotes_resumen"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN B — REGISTROS HUÉRFANOS
    # ═══════════════════════════════════════════════════════════════════

    # B1. Lotes huérfanos (sin reception_id ni guia_processing_id)
    cur.execute("""
        SELECT sl.id, sl.name, sl.technical_validation, sl.estado_trazabilidad,
               sl.reception_type, sl.volumen_m3, sl.piezas,
               sl.create_date, sl.guia_number,
               COALESCE(pt.default_code, 'N/A') AS product_code,
               COALESCE(sq.qty, 0) AS stock_disponible
        FROM stock_lot sl
        LEFT JOIN product_product pp ON sl.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN (
            SELECT lot_id, SUM(quantity) AS qty FROM stock_quant WHERE quantity > 0 GROUP BY lot_id
        ) sq ON sq.lot_id = sl.id
        WHERE sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
        ORDER BY sl.id;
    """)
    results["B1_lotes_huerfanos"] = [list(r) for r in cur.fetchall()]

    # B2. Stock moves huérfanos (sin picking, no cancelados)
    cur.execute("""
        SELECT sm.id, sm.name, sm.origin, sm.state, sm.product_uom_qty,
               sm.picking_id, sm.create_date,
               COALESCE(pt.default_code, 'N/A') AS product_code
        FROM stock_move sm
        LEFT JOIN product_product pp ON sm.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE (sm.picking_id IS NULL OR sm.state = 'done')
          AND sm.state != 'cancel'
        ORDER BY sm.id;
    """)
    results["B2_moves_huerfanos"] = [list(r) for r in cur.fetchall()]

    # B3. Stock move.lines sin move padre o con move cancelado
    cur.execute("""
        SELECT sml.id AS move_line_id, sml.move_id, sml.picking_id,
               sml.lot_id, sl.name AS lot_name,
               sml.quantity, sml.state AS line_state,
               sm.state AS move_state, sm.origin AS move_origin,
               sp.state AS picking_state
        FROM stock_move_line sml
        LEFT JOIN stock_move sm ON sm.id = sml.move_id
        LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
        LEFT JOIN stock_lot sl ON sl.id = sml.lot_id
        WHERE sml.move_id IS NULL OR sm.state = 'cancel'
        ORDER BY sml.id;
    """)
    results["B3_move_lines_huerfanas"] = [list(r) for r in cur.fetchall()]

    # B4. Pickings con origen REVERTIDO o ANULADO
    cur.execute("""
        SELECT sp.id, sp.name, sp.origin, sp.state,
               spt.name AS picking_type,
               sp.create_date, sp.date_done
        FROM stock_picking sp
        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        WHERE sp.origin LIKE '%REVERTIDO%' OR sp.origin LIKE '%ANULADO%'
        ORDER BY sp.id;
    """)
    results["B4_pickings_revertido_anulado"] = [list(r) for r in cur.fetchall()]

    # B5. Quants de lotes huérfanos con stock positivo
    cur.execute("""
        SELECT sq.id AS quant_id, sq.lot_id, sl.name AS lot_name,
               sq.quantity, sq.location_id,
               sloc.complete_name AS location,
               sl.technical_validation, sl.estado_trazabilidad
        FROM stock_quant sq
        JOIN stock_lot sl ON sl.id = sq.lot_id
        LEFT JOIN stock_location sloc ON sloc.id = sq.location_id
        WHERE sq.quantity > 0
          AND sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
        ORDER BY sq.quantity DESC;
    """)
    results["B5_quants_de_huerfanos"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN C — DUPLICADOS (stock.move y stock.move.line por lote/picking)
    # ═══════════════════════════════════════════════════════════════════

    # C1. Pickings con más moves que lo esperado (posible duplicación)
    cur.execute("""
        SELECT sp.id AS picking_id, sp.name AS picking_name, sp.origin,
               sp.state,
               COUNT(sm.id) AS num_moves,
               COUNT(DISTINCT sml.lot_id) AS num_lotes_distintos,
               COUNT(sml.id) AS num_move_lines
        FROM stock_picking sp
        JOIN stock_move sm ON sm.picking_id = sp.id
        LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
        GROUP BY sp.id, sp.name, sp.origin, sp.state
        HAVING COUNT(sm.id) > COUNT(DISTINCT sml.lot_id) * 1.5
           OR COUNT(sm.id) != COUNT(sml.id)
        ORDER BY COUNT(sm.id) DESC;
    """)
    results["C1_pickings_con_posible_duplicacion"] = [list(r) for r in cur.fetchall()]

    # C2. stock.move duplicados (mismo lote, mismo picking, más de 1 move)
    cur.execute("""
        SELECT sp.name AS picking_name, sl.id AS lot_id, sl.name AS lot_name,
               COUNT(sm.id) AS moves_count,
               ARRAY_AGG(sm.id ORDER BY sm.id) AS move_ids
        FROM stock_move sm
        JOIN stock_picking sp ON sp.id = sm.picking_id
        JOIN stock_move_line sml ON sml.move_id = sm.id
        JOIN stock_lot sl ON sl.id = sml.lot_id
        GROUP BY sp.name, sl.id, sl.name
        HAVING COUNT(sm.id) > 1
        ORDER BY moves_count DESC;
    """)
    results["C2_moves_duplicados_por_lote"] = [list(r) for r in cur.fetchall()]

    # C3. stock.move.line duplicadas (mismo lote, mismo picking)
    cur.execute("""
        SELECT sp.name AS picking_name, sl.id AS lot_id, sl.name AS lot_name,
               COUNT(sml.id) AS lines_count,
               ARRAY_AGG(sml.id ORDER BY sml.id) AS line_ids
        FROM stock_move_line sml
        JOIN stock_picking sp ON sp.id = sml.picking_id
        JOIN stock_lot sl ON sl.id = sml.lot_id
        WHERE sl.name NOT LIKE '%virtual%'
        GROUP BY sp.name, sl.id, sl.name
        HAVING COUNT(sml.id) > 1
        ORDER BY lines_count DESC;
    """)
    results["C3_move_lines_duplicadas"] = [list(r) for r in cur.fetchall()]

    # C4. stock.quant duplicados (mismo lote, misma ubicación, misma cantidad -> residuo)
    cur.execute("""
        SELECT sq.lot_id, sl.name AS lot_name, sq.location_id,
               sloc.complete_name AS location,
               COUNT(*) AS cnt, SUM(sq.quantity) AS total_qty,
               ARRAY_AGG(sq.id ORDER BY sq.id) AS quant_ids
        FROM stock_quant sq
        JOIN stock_lot sl ON sl.id = sq.lot_id
        LEFT JOIN stock_location sloc ON sloc.id = sq.location_id
        WHERE sq.quantity > 0
          AND sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%'
        GROUP BY sq.lot_id, sl.name, sq.location_id, sloc.complete_name,
                 sq.quantity
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC;
    """)
    results["C4_quants_duplicados"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN D — VÍNCULOS CON RECEPCIÓN / GUÍA / CONTENEDOR / SHIPMENT
    # ═══════════════════════════════════════════════════════════════════

    # D1. Guías de procesamiento — estado y lotes vinculados vs FK real
    cur.execute("""
        SELECT mgp.id, mgp.name, mgp.state,
               mgp.total_lotes_unicos, mgp.vol_total_m3,
               COUNT(mgpr.stock_lot_id) AS lotes_m2m,
               (SELECT COUNT(*) FROM stock_lot sl
                WHERE sl.guia_processing_id = mgp.id AND sl.name NOT LIKE '%virtual%') AS lotes_fk_real
        FROM madenat_guia_processing mgp
        LEFT JOIN madenat_guia_processing_stock_lot_rel mgpr ON mgpr.madenat_guia_processing_id = mgp.id
        GROUP BY mgp.id, mgp.name, mgp.state, mgp.total_lotes_unicos, mgp.vol_total_m3
        ORDER BY mgp.name;
    """)
    results["D1_guias_lotes_coherencia"] = [list(r) for r in cur.fetchall()]

    # D2. Guías en draft/cancelled que aún tienen lotes FK
    cur.execute("""
        SELECT mgp.id, mgp.name, mgp.state,
               COUNT(sl.id) AS lotes_vinculados
        FROM madenat_guia_processing mgp
        JOIN stock_lot sl ON sl.guia_processing_id = mgp.id
        WHERE mgp.state IN ('draft', 'cancelled')
          AND sl.name NOT LIKE '%virtual%'
        GROUP BY mgp.id, mgp.name, mgp.state;
    """)
    results["D2_guias_draft_cancelled_con_lotes"] = [list(r) for r in cur.fetchall()]

    # D3. Recepciones — lotes vinculados vs FK real
    cur.execute("""
        SELECT lr.id, lr.name, lr.state,
               COUNT(lrl.stock_lot_id) AS lotes_m2m,
               (SELECT COUNT(*) FROM stock_lot sl
                WHERE sl.reception_id = lr.id AND sl.name NOT LIKE '%virtual%') AS lotes_fk_real
        FROM lumber_reception lr
        LEFT JOIN lumber_reception_stock_lot_rel lrl ON lrl.lumber_reception_id = lr.id
        GROUP BY lr.id, lr.name, lr.state
        ORDER BY lr.name;
    """)
    results["D3_recepciones_lotes_coherencia"] = [list(r) for r in cur.fetchall()]

    # D4. Lotes en contenedores — verificación
    cur.execute("""
        SELECT lc.id AS container_id, lc.name AS container_name, lc.state,
               les.name AS shipment_name, les.state AS shipment_state,
               COUNT(lclr.stock_lot_id) AS total_lotes,
               COUNT(lclr.stock_lot_id) FILTER (
                   WHERE sl.technical_validation = 'rejected'
               ) AS lotes_rejected,
               COUNT(lclr.stock_lot_id) FILTER (
                   WHERE sl.guia_processing_id IS NULL AND sl.reception_id IS NULL
               ) AS lotes_huerfanos
        FROM lumber_container lc
        JOIN lumber_container_stock_lot_rel lclr ON lclr.lumber_container_id = lc.id
        JOIN stock_lot sl ON sl.id = lclr.stock_lot_id
        LEFT JOIN lumber_export_shipment les ON les.id = lc.shipment_id
        GROUP BY lc.id, lc.name, lc.state, les.name, les.state
        ORDER BY lc.name;
    """)
    results["D4_contenedores_lotes"] = [list(r) for r in cur.fetchall()]

    # D5. Lotes con reception_id y guia_processing_id simultáneos (violación de exclusividad)
    cur.execute("""
        SELECT id, name, reception_id, guia_processing_id, reception_type,
               technical_validation, estado_trazabilidad
        FROM stock_lot
        WHERE reception_id IS NOT NULL AND guia_processing_id IS NOT NULL
          AND name NOT LIKE '%virtual%';
    """)
    results["D5_violaciones_exclusividad"] = [list(r) for r in cur.fetchall()]

    # D6. Lotes rejected con stock disponible
    cur.execute("""
        SELECT sl.id, sl.name, sl.technical_validation,
               SUM(sq.quantity) FILTER (WHERE sq.quantity > 0) AS stock_disponible,
               sloc.complete_name AS ubicacion
        FROM stock_lot sl
        JOIN stock_quant sq ON sq.lot_id = sl.id
        LEFT JOIN stock_location sloc ON sloc.id = sq.location_id
        WHERE sl.technical_validation = 'rejected'
          AND sl.name NOT LIKE '%virtual%'
        GROUP BY sl.id, sl.name, sl.technical_validation, sloc.complete_name
        HAVING SUM(sq.quantity) FILTER (WHERE sq.quantity > 0) > 0
        ORDER BY stock_disponible DESC;
    """)
    results["D6_lotes_rejected_con_stock"] = [list(r) for r in cur.fetchall()]

    # D7. Moves con lotes rejected
    cur.execute("""
        SELECT sm.id AS move_id, sm.name, sm.state, sm.origin,
               sp.name AS picking_name, sp.state AS picking_state,
               sl.id AS lot_id, sl.name AS lot_name, sl.technical_validation
        FROM stock_move sm
        JOIN stock_move_line sml ON sml.move_id = sm.id
        JOIN stock_lot sl ON sl.id = sml.lot_id
        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
        WHERE sl.technical_validation = 'rejected'
          AND sm.state NOT IN ('cancel', 'done')
        ORDER BY sp.name, sm.id;
    """)
    results["D7_moves_con_lotes_rejected"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN E — RESIDUOS TÉCNICOS (quants con balance inconsistente)
    # ═══════════════════════════════════════════════════════════════════

    # E1. Quants con quantity > 0 de lotes que NO aparecen en ningún move activo
    cur.execute("""
        SELECT sq.id AS quant_id, sq.lot_id, sl.name AS lot_name,
               sq.quantity, sq.location_id,
               sloc.complete_name AS location,
               sl.technical_validation,
               COALESCE(move_ref.move_count, 0) AS active_moves
        FROM stock_quant sq
        JOIN stock_lot sl ON sl.id = sq.lot_id
        LEFT JOIN stock_location sloc ON sloc.id = sq.location_id
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS move_count FROM stock_move_line sml
            JOIN stock_move sm ON sm.id = sml.move_id
            WHERE sml.lot_id = sl.id AND sm.state NOT IN ('cancel', 'done')
        ) move_ref ON true
        WHERE sq.quantity > 0
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
        ORDER BY COALESCE(move_ref.move_count, 0), sq.quantity DESC
        LIMIT 100;
    """)
    results["E1_quants_sin_moves_activos"] = [list(r) for r in cur.fetchall()]

    # E2. Balance de stock por lote: quants vs move_lines
    cur.execute("""
        SELECT sl.id AS lot_id, sl.name AS lot_name,
               sl.technical_validation,
               COALESCE(sq.total_in, 0) AS quant_in,
               COALESCE(sq.total_out, 0) AS quant_out,
               COALESCE(sq.total_in, 0) - COALESCE(sq.total_out, 0) AS quant_balance,
               COALESCE(move_qty.move_in, 0) AS move_qty_in,
               COALESCE(move_qty.move_out, 0) AS move_qty_out
        FROM stock_lot sl
        LEFT JOIN (
            SELECT lot_id,
                   SUM(quantity) FILTER (WHERE quantity > 0) AS total_in,
                   SUM(quantity) FILTER (WHERE quantity < 0) AS total_out
            FROM stock_quant GROUP BY lot_id
        ) sq ON sq.lot_id = sl.id
        LEFT JOIN (
            SELECT sml.lot_id,
                   SUM(sml.quantity) FILTER (WHERE sm.location_dest_id IS NOT NULL) AS move_in,
                   SUM(sml.quantity) FILTER (WHERE sm.location_id IS NOT NULL) AS move_out
            FROM stock_move_line sml
            JOIN stock_move sm ON sm.id = sml.move_id AND sm.state = 'done'
            GROUP BY sml.lot_id
        ) move_qty ON move_qty.lot_id = sl.id
        WHERE sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%'
        ORDER BY ABS(COALESCE(sq.total_in, 0) - COALESCE(sq.total_out, 0) -
                     COALESCE(move_qty.move_in, 0) + COALESCE(move_qty.move_out, 0)) DESC
        LIMIT 50;
    """)
    results["E2_balance_quants_vs_moves"] = [list(r) for r in cur.fetchall()]

    # E3. stock.move.line en estado 'done' sin quants asociados
    cur.execute("""
        SELECT sml.id AS move_line_id, sml.lot_id, sl.name AS lot_name,
               sml.quantity, sml.state,
               sm.state AS move_state, sp.name AS picking_name,
               COALESCE(sq.quant_count, 0) AS quants_count
        FROM stock_move_line sml
        JOIN stock_lot sl ON sl.id = sml.lot_id
        JOIN stock_move sm ON sm.id = sml.move_id
        LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS quant_count FROM stock_quant
            WHERE lot_id = sml.lot_id AND quantity != 0
        ) sq ON true
        WHERE sml.state = 'done'
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
          AND COALESCE(sq.quant_count, 0) = 0
        ORDER BY sml.id
        LIMIT 100;
    """)
    results["E3_move_lines_done_sin_quants"] = [list(r) for r in cur.fetchall()]

    # E4. Lotes con costo pero sin stock ni FK de origen
    cur.execute("""
        SELECT sl.id, sl.name, sl.technical_validation,
               sl.volumen_m3, sl.piezas,
               lcl.id AS cost_line_id, lcl.cost_amount
        FROM stock_lot sl
        JOIN stock_lot_cost_line lcl ON lcl.lot_id = sl.id
        WHERE sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%';
    """)
    results["E4_lotes_con_costo_sin_origen"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN F — VÍNCULOS GUIA PROCESSING / RECEPTION
    # ═══════════════════════════════════════════════════════════════════

    # F1. Volúmenes: guía vs lotes reales
    cur.execute("""
        SELECT mgp.id, mgp.name, mgp.state,
               mgp.vol_comercial, mgp.vol_fisico, mgp.vol_total_m3,
               COALESCE(SUM(sl.volumen_m3), 0) AS lotes_volumen_sum,
               ROUND((mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0))::numeric, 3) AS delta_m3
        FROM madenat_guia_processing mgp
        LEFT JOIN stock_lot sl ON sl.guia_processing_id = mgp.id AND sl.name NOT LIKE '%virtual%'
        GROUP BY mgp.id, mgp.name, mgp.state, mgp.vol_comercial, mgp.vol_fisico, mgp.vol_total_m3
        HAVING ABS(mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0)) > 0.01
           OR COALESCE(SUM(sl.volumen_m3), 0) > 0
        ORDER BY ABS(mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0)) DESC;
    """)
    results["F1_guias_delta_volumen"] = [list(r) for r in cur.fetchall()]

    # F2. Lotes por reception_id con detalle
    cur.execute("""
        SELECT sl.id, sl.name, sl.reception_id, lr.name AS reception_name,
               sl.reception_type, sl.technical_validation,
               sl.volumen_m3, sl.piezas
        FROM stock_lot sl
        LEFT JOIN lumber_reception lr ON lr.id = sl.reception_id
        WHERE sl.reception_id IS NOT NULL
          AND sl.name NOT LIKE '%virtual%'
        ORDER BY sl.id;
    """)
    results["F2_lotes_con_recepcion"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN G — INFORME DE REPORTES (shipment lines, bookings, etc.)
    # ═══════════════════════════════════════════════════════════════════

    # G1. Lumber export shipment lines
    try:
        cur.execute("""
            SELECT les.id AS shipment_id, les.name AS shipment_name, les.state,
                   COUNT(lesl.id) AS shipment_lines
            FROM lumber_export_shipment les
            LEFT JOIN lumber_export_shipment_line lesl ON lesl.shipment_id = les.id
            GROUP BY les.id, les.name, les.state
            ORDER BY les.name;
        """)
        results["G1_shipments"] = [list(r) for r in cur.fetchall()]
    except Exception as e:
        results["G1_shipments_error"] = str(e)

    # G2. Lotes en shipment lines con estado de validación consistente
    try:
        cur.execute("""
            SELECT lesl.id AS line_id, les.name AS shipment_name, les.state AS shipment_state,
                   sl.id AS lot_id, sl.name AS lot_name, sl.technical_validation,
                   sl.volumen_m3
            FROM lumber_export_shipment_line lesl
            JOIN stock_lot sl ON sl.id = lesl.lot_id
            LEFT JOIN lumber_export_shipment les ON les.id = lesl.shipment_id
            WHERE sl.technical_validation = 'rejected'
               OR (sl.guia_processing_id IS NULL AND sl.reception_id IS NULL)
            ORDER BY les.name, sl.name;
        """)
        results["G2_shipment_lines_lotes_problematicos"] = [list(r) for r in cur.fetchall()]
    except Exception as e:
        results["G2_shipment_lines_error"] = str(e)

    # G3. Booking IDs/Container IDs — si existen tablas específicas
    try:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND (table_name LIKE '%booking%' OR table_name LIKE '%container%')
            ORDER BY table_name;
        """)
        results["G3_tablas_booking_container"] = [list(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public'
              AND column_name IN ('bookingid', 'booking_id', 'containerid', 'container_id',
                                  'shipmentline', 'shipment_line_id', 'guiaprocessingid',
                                  'guia_processing_id', 'receptionid', 'reception_id',
                                  'lot_ids')
            ORDER BY table_name, column_name;
        """)
        results["G3_columnas_de_interes"] = [list(r) for r in cur.fetchall()]
    except Exception as e:
        results["G3_error"] = str(e)

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN H — LOTES VÁLIDOS (CONSERVAR)
    # ═══════════════════════════════════════════════════════════════════

    # H1. Lotes con trazabilidad completa (reception_id + guia + approved)
    cur.execute("""
        SELECT sl.id, sl.name, sl.reception_id, sl.guia_processing_id,
               sl.reception_type, sl.technical_validation, sl.estado_trazabilidad,
               sl.volumen_m3, sl.piezas,
               mgp.name AS guia_name,
               COALESCE(sq.qty, 0) AS stock_disponible
        FROM stock_lot sl
        LEFT JOIN madenat_guia_processing mgp ON mgp.id = sl.guia_processing_id
        LEFT JOIN (
            SELECT lot_id, SUM(quantity) AS qty FROM stock_quant
            WHERE quantity > 0 GROUP BY lot_id
        ) sq ON sq.lot_id = sl.id
        WHERE sl.name NOT LIKE '%virtual%' AND sl.name NOT LIKE '%default%'
          AND (sl.reception_id IS NOT NULL OR sl.guia_processing_id IS NOT NULL)
        ORDER BY sl.id;
    """)
    results["H1_lotes_con_trazabilidad"] = [list(r) for r in cur.fetchall()]

    conn.close()

except Exception as e:
    results["error"] = str(e)
    import traceback
    results["traceback"] = traceback.format_exc()

with open(OUTFILE, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(json.dumps(results, indent=2, ensure_ascii=False, default=str))