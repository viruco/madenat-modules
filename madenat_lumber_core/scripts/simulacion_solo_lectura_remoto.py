# -*- coding: utf-8 -*-
"""Script de SOLO LECTURA para simulación de impacto de WP-B (Ancho S2S de Exportación).

Este script permite a Mauricio inspeccionar el impacto sobre la base de datos
(local o TEST remoto) SIN modificar ningún registro almacenado.

Uso en servidor Odoo:
    odoo shell -d <nombre_bd> --stop-after-init < simulacion_solo_lectura_remoto.py

O ejecutar con python directo:
    python3 simulacion_solo_lectura_remoto.py
"""

import sys

def run_simulation(env):
    print("=" * 80)
    print("SIMULACIÓN DE IMPACTO DE ANCHO DE EXPORTACIÓN S2S (SOLO LECTURA)")
    print("=" * 80)

    # 1. Mapeo Canónico S2S (width_mapping.py / lumber.width.s2s.map)
    S2S_WIDTH_MAP = {
        75: 2.625,   # 2 5/8" (66.675 mm)
        80: 2.750,   # 2 3/4" (69.850 mm)
        85: 2.9375,  # 2 15/16" (74.6125 mm)
        90: 3.125,   # 3 1/8" (79.375 mm)
        100: 3.625,  # 3 5/8" (92.075 mm)
        105: 3.750,  # 3 3/4" (95.250 mm)
        110: 4.000,  # 4" (101.600 mm)
        115: 4.125,  # 4 1/8" (104.775 mm)
        120: 4.375,  # 4 3/8" (111.125 mm)
        125: 4.500,  # 4 1/2" (114.300 mm)
        130: 4.750,  # 4 3/4" (120.650 mm)
        140: 5.125,  # 5 1/8" (130.175 mm)
        145: 5.375,  # 5 3/8" (136.525 mm) - Valor Crítico
        150: 5.500,  # 5 1/2" (139.700 mm)
        155: 5.750,  # 5 3/4" (146.050 mm)
    }

    def calc_s2s_vol(ancho_mm, espesor_mm, largo_m, pieces):
        if not (ancho_mm and espesor_mm and largo_m and pieces):
            return 0.0
        width_key = int(round(ancho_mm))
        if width_key in S2S_WIDTH_MAP:
            s2s_width_mm = S2S_WIDTH_MAP[width_key] * 25.4
        else:
            s2s_width_mm = ancho_mm
        return round((espesor_mm * s2s_width_mm * largo_m * pieces) / 1_000_000.0, 3)

    # 2. Análisis en madenat.guia.processing.line
    ProcessingLine = env['madenat.guia.processing.line']
    lines = ProcessingLine.search([('processing_id.state', '!=', 'cancel')])

    total_lines = len(lines)
    changed_lines = []
    unchanged_count = 0
    total_stored_vol = 0.0
    total_sim_vol = 0.0

    print(f"\n1. Líneas de Guía de Procesado (madenat.guia.processing.line):")
    print(f"Total líneas activas encontradas: {total_lines}")

    for l in lines:
        stored = l.vol_shipment_m3 or 0.0
        total_stored_vol += stored
        sim = calc_s2s_vol(l.ancho_mm, l.espesor_mm, l.largo_m, l.pieces)
        total_sim_vol += sim
        diff = sim - stored

        if abs(diff) >= 0.001:
            changed_lines.append({
                'id': l.id,
                'guia': l.processing_id.name or 'S/N',
                'lote': l.lot_name or l.lot_id.name or 'S/L',
                'espesor': l.espesor_mm,
                'ancho': l.ancho_mm,
                'largo': l.largo_m,
                'piezas': l.pieces,
                'almacenado': stored,
                'simulado': sim,
                'diff': diff,
            })
        else:
            unchanged_count += 1

    print(f"Líneas sin cambio: {unchanged_count}")
    print(f"Líneas con variación: {len(changed_lines)}")
    print(f"Volumen almacenado actual: {total_stored_vol:.3f} m³")
    print(f"Volumen simulado con S2S:  {total_sim_vol:.3f} m³")
    delta_total = total_sim_vol - total_stored_vol
    pct = (delta_total / total_stored_vol * 100.0) if total_stored_vol else 0.0
    print(f"Diferencia neta total:     {delta_total:+.3f} m³ ({pct:+.2f}%)")

    if changed_lines:
        print("\nDetalle de líneas con variación:")
        print(f"{'ID':<6} {'Guía':<18} {'Lote':<22} {'Dims (E x A x L)':<18} {'Pzs':<5} {'Almac.':<8} {'Sim. S2S':<9} {'Delta m³':<8}")
        print("-" * 100)
        for r in changed_lines:
            dims = f"{r['espesor']:.0f}x{r['ancho']:.0f}x{r['largo']:.2f}"
            print(f"{r['id']:<6} {r['guia']:<18} {r['lote']:<22} {dims:<18} {r['piezas']:<5} {r['almacenado']:<8.3f} {r['simulado']:<9.3f} {r['diff']:<+8.3f}")

    # 3. Análisis en stock.lot
    Lot = env['stock.lot']
    lots = Lot.search([('vol_shipment_m3', '>', 0)])
    print(f"\n2. Lotes de Inventario (stock.lot con vol_shipment_m3 > 0):")
    print(f"Total lotes analizados: {len(lots)}")
    changed_lots = 0
    lot_stored_total = 0.0
    lot_sim_total = 0.0
    for lot in lots:
        stored = lot.vol_shipment_m3 or 0.0
        lot_stored_total += stored
        sim = calc_s2s_vol(lot.ancho_mm, lot.espesor_mm, lot.largo_m, lot.pieces)
        lot_sim_total += sim
        if abs(sim - stored) >= 0.001:
            changed_lots += 1

    print(f"Lotes sin cambio: {len(lots) - changed_lots}")
    print(f"Lotes con variación potencial si se recalcularan: {changed_lots}")
    print(f"Volumen lotes almacenado: {lot_stored_total:.3f} m³")
    print(f"Volumen lotes simulado:   {lot_sim_total:.3f} m³ (Delta: {lot_sim_total - lot_stored_total:+.3f} m³)")
    print("\n[NOTA DE SEGURIDAD]: Ningún dato fue modificado. Este script es de SOLO LECTURA.")
    print("=" * 80)

# Punto de entrada si se ejecuta dentro del entorno Odoo (odoo shell)
if 'env' in locals():
    run_simulation(env)
