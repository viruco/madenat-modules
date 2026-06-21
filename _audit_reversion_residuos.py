#!/usr/bin/env python3
"""
AUDITORÍA DE RESIDUOS POST-REVERSA DE GUÍA
───────────────────────────────────────────
Evalúa la BD tras una reversa de madenat.guia.processing para detectar:
  1. Lotes huérfanos (guia_processing_id=NULL) provenientes de guía revertida
  2. Lotes con technical_validation='rejected' aún utilizables
  3. Incoherencias entre estado de guía y estado de sus lotes
  4. Pickings/movimientos desalineados tras la reversa
  5. Contadores/totales en guía que no coinciden con la realidad de la BD

Output: JSON escrito en /mnt/extra-addons/_audit_reversion_residuos.json
"""

import psycopg2
import json

OUTFILE = "/tmp/_audit_reversion_residuos.json"

results = {}

try:
    conn = psycopg2.connect(
        host="db", port=5432, dbname="madenat_test",
        user="odoo", password="odoo"
    )
    cur = conn.cursor()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: PANORAMA GENERAL — lotes por FK de origen y validación técnica
    # ═══════════════════════════════════════════════════════════════════════════
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS con_guia,
            COUNT(*) FILTER (WHERE guia_processing_id IS NULL) AS sin_guia,
            COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS con_recepcion,
            COUNT(*) FILTER (WHERE reception_id IS NULL AND guia_processing_id IS NULL) AS sin_origen,
            COUNT(*) FILTER (WHERE technical_validation = 'rejected') AS rejected,
            COUNT(*) FILTER (WHERE technical_validation = 'approved') AS approved,
            COUNT(*) FILTER (WHERE technical_validation = 'pending') AS pending
        FROM stock_lot
        WHERE name NOT LIKE '%virtual%' AND name NOT LIKE '%default%';
    """)
    results["panorama_general"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: LOTES REVERTIDOS — technical_validation='rejected'
    # ═══════════════════════════════════════════════════════════════════════════

    # 2A. Cuántos lotes rejected hay y su distribución por guia_processing_id
    cur.execute("""
        SELECT
            COUNT(*) AS rejected_total,
            COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS rejected_con_guia,
            COUNT(*) FILTER (WHERE guia_processing_id IS NULL) AS rejected_sin_guia
        FROM stock_lot
        WHERE technical_validation = 'rejected'
          AND name NOT LIKE '%virtual%';
    """)
    results["rejected_distribution"] = [list(r) for r in cur.fetchall()]

    # 2B. Lista detallada de lotes rejected
    cur.execute("""
        SELECT
            sl.id,
            sl.name,
            sl.technical_validation,
            sl.estado_trazabilidad,
            sl.guia_processing_id,
            sl.reception_id,
            sl.volumen_m3,
            sl.piezas,
            sl.product_id,
            COALESCE(pt.default_code, 'N/A') AS product_code
        FROM stock_lot sl
        LEFT JOIN product_product pp ON sl.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE sl.technical_validation = 'rejected'
          AND sl.name NOT LIKE '%virtual%'
        ORDER BY sl.id;
    """)
    results["rejected_lotes_detalle"] = [list(r) for r in cur.fetchall()]

    # 2C. Lotes rejected que tienen stock disponible (quants > 0)
    cur.execute("""
        SELECT
            sl.id,
            sl.name,
            sl.technical_validation,
            sl.estado_trazabilidad,
            sl.guia_processing_id,
            SQ.quantity,
            SQ.location_id,
            SLOC.complete_name AS location_name
        FROM stock_lot sl
        JOIN stock_quant SQ ON SQ.lot_id = sl.id AND SQ.quantity > 0
        LEFT JOIN stock_location SLOC ON SQ.location_id = SLOC.id
        WHERE sl.technical_validation = 'rejected'
          AND sl.name NOT LIKE '%virtual%'
        ORDER BY SQ.quantity DESC;
    """)
    results["rejected_con_stock_disponible"] = [list(r) for r in cur.fetchall()]

    # 2D. Lotes rejected que están en contenedores logísticos
    cur.execute("""
        SELECT
            sl.id,
            sl.name,
            sl.technical_validation,
            sl.guia_processing_id,
            lc.name AS container_name,
            lc.state AS container_state,
            les.name AS shipment_name,
            les.state AS shipment_state
        FROM stock_lot sl
        JOIN lumber_container_stock_lot_rel lclr ON lclr.stock_lot_id = sl.id
        JOIN lumber_container lc ON lc.id = lclr.lumber_container_id
        LEFT JOIN lumber_export_shipment les ON les.id = lc.shipment_id
        WHERE sl.technical_validation = 'rejected'
        ORDER BY lc.name, sl.name;
    """)
    results["rejected_en_contenedores"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: LOTES HUÉRFANOS — sin guia_processing_id ni reception_id
    # ═══════════════════════════════════════════════════════════════════════════

    # 3A. Distribución de huérfanos
    cur.execute("""
        SELECT
            COUNT(*) AS total_huerfanos,
            COUNT(*) FILTER (WHERE technical_validation = 'rejected') AS huerfanos_rejected,
            COUNT(*) FILTER (WHERE technical_validation = 'pending') AS huerfanos_pending,
            COUNT(*) FILTER (WHERE technical_validation = 'approved') AS huerfanos_approved,
            SUM(volumen_m3) AS volumen_total,
            SUM(piezas) AS piezas_total
        FROM stock_lot
        WHERE reception_id IS NULL
          AND guia_processing_id IS NULL
          AND name NOT LIKE '%virtual%'
          AND name NOT LIKE '%default%';
    """)
    results["huerfanos_resumen"] = [list(r) for r in cur.fetchall()]

    # 3B. Detalle de huérfanos con más info
    cur.execute("""
        SELECT
            sl.id,
            sl.name,
            sl.technical_validation,
            sl.estado_trazabilidad,
            sl.reception_type,
            sl.volumen_m3,
            sl.piezas,
            sl.create_date,
            COALESCE(pt.default_code, 'N/A') AS product_code
        FROM stock_lot sl
        LEFT JOIN product_product pp ON sl.product_id = pp.id
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
        ORDER BY sl.create_date DESC
        LIMIT 100;
    """)
    results["huerfanos_detalle"] = [list(r) for r in cur.fetchall()]

    # 3C. Huérfanos con stock disponible
    cur.execute("""
        SELECT
            sl.id,
            sl.name,
            sl.technical_validation,
            sl.estado_trazabilidad,
            SQ.quantity,
            SLOC.complete_name AS location_name
        FROM stock_lot sl
        JOIN stock_quant SQ ON SQ.lot_id = sl.id AND SQ.quantity > 0
        LEFT JOIN stock_location SLOC ON SQ.location_id = SLOC.id
        WHERE sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%'
        ORDER BY SQ.quantity DESC;
    """)
    results["huerfanos_con_stock"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: GUIAS — coherencia entre estado de guía y estado de lotes
    # ═══════════════════════════════════════════════════════════════════════════

    # 4A. Resumen de guías por estado
    cur.execute("""
        SELECT state, COUNT(*) AS cnt
        FROM madenat_guia_processing
        GROUP BY state
        ORDER BY cnt DESC;
    """)
    results["guias_por_estado"] = [list(r) for r in cur.fetchall()]

    # 4B. Guías con lotes asignados (relación Many2many) vs número real de lotes
    #     con esa guia_processing_id
    cur.execute("""
        SELECT
            mgp.id,
            mgp.name,
            mgp.state,
            mgp.total_lotes_unicos,
            mgp.total_paquetes,
            mgp.vol_comercial,
            mgp.vol_fisico,
            mgp.vol_total_m3,
            mgp.vol_shipment_m3,
            COUNT(mgpr.stock_lot_id) AS lotes_via_m2m,
            (
                SELECT COUNT(*) FROM stock_lot sl2
                WHERE sl2.guia_processing_id = mgp.id
                  AND sl2.name NOT LIKE '%virtual%'
            ) AS lotes_via_fk_real
        FROM madenat_guia_processing mgp
        LEFT JOIN madenat_guia_processing_stock_lot_rel mgpr ON mgpr.madenat_guia_processing_id = mgp.id
        GROUP BY mgp.id, mgp.name, mgp.state, mgp.total_lotes_unicos, mgp.total_paquetes,
                 mgp.vol_comercial, mgp.vol_fisico, mgp.vol_total_m3, mgp.vol_shipment_m3
        ORDER BY mgp.name;
    """)
    results["guias_lotes_coherencia"] = [list(r) for r in cur.fetchall()]

    # 4C. Guías que están en 'draft' o 'cancelled' pero aún tienen lotes con guia_processing_id
    cur.execute("""
        SELECT
            mgp.id,
            mgp.name,
            mgp.state,
            COUNT(sl.id) AS lotes_huerfanos_vinculados
        FROM madenat_guia_processing mgp
        JOIN stock_lot sl ON sl.guia_processing_id = mgp.id
        WHERE mgp.state IN ('draft', 'cancelled')
          AND sl.name NOT LIKE '%virtual%'
        GROUP BY mgp.id, mgp.name, mgp.state
        ORDER BY mgp.name;
    """)
    results["guias_draft_cancelled_con_lotes_fk"] = [list(r) for r in cur.fetchall()]

    # 4D. Guías 'processed'/'validated' y si sus lotes referenciados están rejected
    cur.execute("""
        SELECT
            mgp.id,
            mgp.name,
            mgp.state,
            COUNT(sl.id) AS total_lotes,
            COUNT(sl.id) FILTER (WHERE sl.technical_validation = 'rejected') AS lotes_rejected,
            COUNT(sl.id) FILTER (WHERE sl.technical_validation = 'approved') AS lotes_approved,
            COUNT(sl.id) FILTER (WHERE sl.technical_validation = 'pending') AS lotes_pending
        FROM madenat_guia_processing mgp
        JOIN stock_lot sl ON sl.guia_processing_id = mgp.id
        WHERE mgp.state IN ('processed', 'validated')
          AND sl.name NOT LIKE '%virtual%'
        GROUP BY mgp.id, mgp.name, mgp.state
        ORDER BY mgp.name;
    """)
    results["guias_activas_lotes_validation"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: PICKINGS — desalineados tras la reversa
    # ═══════════════════════════════════════════════════════════════════════════

    # 5A. Pickings con origen REVERTIDO-
    cur.execute("""
        SELECT
            sp.id,
            sp.name,
            sp.origin,
            sp.state,
            sp.picking_type_id,
            spt.name AS picking_type_name,
            sp.create_date,
            sp.date_done
        FROM stock_picking sp
        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        WHERE sp.origin LIKE 'REVERTIDO-%'
        ORDER BY sp.id DESC;
    """)
    results["pickings_revertido"] = [list(r) for r in cur.fetchall()]

    # 5B. Pickings con origen ANULADO-
    cur.execute("""
        SELECT
            sp.id,
            sp.name,
            sp.origin,
            sp.state,
            sp.picking_type_id,
            spt.name AS picking_type_name
        FROM stock_picking sp
        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        WHERE sp.origin LIKE 'ANULADO-%'
        ORDER BY sp.id DESC;
    """)
    results["pickings_anulado"] = [list(r) for r in cur.fetchall()]

    # 5C. Stock moves huérfanos (sin picking o con picking cancelado)
    cur.execute("""
        SELECT
            sm.id,
            sm.name,
            sm.origin,
            sm.state,
            sm.product_uom_qty,
            sm.picking_id,
            sm.lot_ids,
            sp.state AS picking_state
        FROM stock_move sm
        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
        WHERE (sm.picking_id IS NULL OR sp.state = 'cancel')
          AND sm.state != 'cancel'
          AND sm.origin IS NOT NULL
        LIMIT 100;
    """)
    results["stock_moves_huerfanos"] = [list(r) for r in cur.fetchall()]

    # 5D. Movimientos con lotes rejected asociados
    cur.execute("""
        SELECT
            sm.id AS move_id,
            sm.name AS move_name,
            sm.state AS move_state,
            sm.origin AS move_origin,
            sp.name AS picking_name,
            sp.state AS picking_state,
            sl.id AS lot_id,
            sl.name AS lot_name,
            sl.technical_validation
        FROM stock_move sm
        JOIN stock_move_line sml ON sml.move_id = sm.id
        JOIN stock_lot sl ON sl.id = sml.lot_id
        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
        WHERE sl.technical_validation = 'rejected'
          AND sm.state NOT IN ('cancel', 'done')
        ORDER BY sp.name, sm.id
        LIMIT 200;
    """)
    results["moves_con_lotes_rejected"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 6: VOLÚMENES Y CONTADORES — coherencia guía vs realidad BD
    # ═══════════════════════════════════════════════════════════════════════════

    # 6A. Suma de volúmenes por guía desde stock_lot vs lo que dice la guía
    cur.execute("""
        SELECT
            mgp.id,
            mgp.name,
            mgp.state,
            mgp.vol_comercial AS guia_vol_comercial,
            mgp.vol_fisico AS guia_vol_fisico,
            mgp.vol_total_m3 AS guia_vol_total_m3,
            mgp.vol_shipment_m3 AS guia_vol_shipment,
            mgp.total_lotes_unicos AS guia_total_lotes,
            mgp.total_paquetes AS guia_total_paquetes,
            COALESCE(
                (SELECT SUM(sl.volumen_m3) FROM stock_lot sl
                 WHERE sl.guia_processing_id = mgp.id AND sl.name NOT LIKE '%virtual%'),
                0.0
            ) AS lotes_volumen_m3_sum,
            COALESCE(
                (SELECT SUM(sl.vol_shipment_m3) FROM stock_lot sl
                 WHERE sl.guia_processing_id = mgp.id AND sl.name NOT LIKE '%virtual%'),
                0.0
            ) AS lotes_vol_shipment_sum,
            COALESCE(
                (SELECT COUNT(*) FROM stock_lot sl
                 WHERE sl.guia_processing_id = mgp.id AND sl.name NOT LIKE '%virtual%'),
                0
            ) AS lotes_count_real
        FROM madenat_guia_processing mgp
        ORDER BY mgp.name;
    """)
    results["guias_volumenes_coherencia"] = [list(r) for r in cur.fetchall()]

    # 6B. Guías donde los totales no cuadran (diferencia > 0.01 m³)
    cur.execute("""
        SELECT
            mgp.id,
            mgp.name,
            mgp.state,
            mgp.vol_total_m3 AS guia_vol_total_m3,
            COALESCE(SUM(sl.volumen_m3), 0.0) AS lotes_volumen_m3_sum,
            ROUND((mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0.0))::numeric, 3) AS delta_m3
        FROM madenat_guia_processing mgp
        LEFT JOIN stock_lot sl ON sl.guia_processing_id = mgp.id
            AND sl.name NOT LIKE '%virtual%'
        GROUP BY mgp.id, mgp.name, mgp.state, mgp.vol_total_m3
        HAVING ABS(mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0.0)) > 0.01
        ORDER BY ABS(mgp.vol_total_m3 - COALESCE(SUM(sl.volumen_m3), 0.0)) DESC;
    """)
    results["guias_con_delta_volumen"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 7: CONTENEDORES — lotes rejected en la cadena logística
    # ═══════════════════════════════════════════════════════════════════════════

    cur.execute("""
        SELECT
            lc.id AS container_id,
            lc.name AS container_name,
            lc.state AS container_state,
            les.name AS shipment_name,
            les.state AS shipment_state,
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
        HAVING COUNT(lclr.stock_lot_id) FILTER (
            WHERE sl.technical_validation = 'rejected'
        ) > 0
           OR COUNT(lclr.stock_lot_id) FILTER (
            WHERE sl.guia_processing_id IS NULL AND sl.reception_id IS NULL
        ) > 0
        ORDER BY lotes_rejected DESC, lotes_huerfanos DESC;
    """)
    results["contenedores_con_lotes_problematicos"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 8: QUANTS — inventario de lotes rejected u huérfanos
    # ═══════════════════════════════════════════════════════════════════════════

    cur.execute("""
        SELECT
            'rejected' AS categoria,
            COUNT(DISTINCT SQ.id) AS quants_count,
            SUM(SQ.quantity) AS total_quantity,
            COUNT(DISTINCT SQ.lot_id) AS lotes_afectados
        FROM stock_quant SQ
        JOIN stock_lot sl ON sl.id = SQ.lot_id
        WHERE sl.technical_validation = 'rejected'
          AND SQ.quantity > 0
          AND sl.name NOT LIKE '%virtual%'
        UNION ALL
        SELECT
            'huerfano' AS categoria,
            COUNT(DISTINCT SQ.id),
            SUM(SQ.quantity),
            COUNT(DISTINCT SQ.lot_id)
        FROM stock_quant SQ
        JOIN stock_lot sl ON sl.id = SQ.lot_id
        WHERE sl.reception_id IS NULL
          AND sl.guia_processing_id IS NULL
          AND SQ.quantity > 0
          AND sl.name NOT LIKE '%virtual%'
          AND sl.name NOT LIKE '%default%';
    """)
    results["quants_problematicos_resumen"] = [list(r) for r in cur.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 9: VIOLACIÓN DE EXCLUSIVIDAD reception_id + guia_processing_id
    # ═══════════════════════════════════════════════════════════════════════════

    cur.execute("""
        SELECT
            id,
            name,
            reception_id,
            guia_processing_id,
            reception_type,
            technical_validation,
            estado_trazabilidad
        FROM stock_lot
        WHERE reception_id IS NOT NULL
          AND guia_processing_id IS NOT NULL
          AND name NOT LIKE '%virtual%'
        LIMIT 30;
    """)
    results["violaciones_exclusividad"] = [list(r) for r in cur.fetchall()]

    conn.close()

except Exception as e:
    results["error"] = str(e)

with open(OUTFILE, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(json.dumps(results, indent=2, ensure_ascii=False, default=str))