# -*- coding: utf-8 -*-
"""Script de SOLO LECTURA para simulación de 3 números por línea de embarque (WP-B Fase 12).

Permite a Mauricio inspeccionar el impacto sobre lumber.shipment.line y lumber.export.shipment
en cualquier entorno (local o TEST remoto) SIN modificar ningún registro ni escribir en la BD.

Uso en servidor Odoo:
    odoo shell -d <nombre_bd> --no-http < simulacion_embarques_solo_lectura_remoto.py

O ejecutar directamente:
    python3 simulacion_embarques_solo_lectura_remoto.py
"""

import sys

def get_s2s_width_inches(ancho_mm, env=None):
    """Obtiene el ancho S2S en pulgadas usando WidthMappingTable o tabla canónica estática."""
    if env and 'lumber.width.s2s.map' in env:
        try:
            from odoo.addons.madenat_lumber_core.models.width_mapping import WidthMappingTable
            val = WidthMappingTable.get_value(ancho_mm, format_type='decimal', env=env)
            if val:
                return float(val)
        except Exception:
            pass

    # Tabla canónica AD-113 / Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx (15 registros activos)
    CANONICAL_S2S = {
        75.0: 2.6250,   # 2 5/8"
        85.0: 2.8750,   # 2 7/8"
        90.0: 3.1250,   # 3 1/8"
        95.0: 3.3750,   # 3 3/8"
        100.0: 3.6250,  # 3 5/8"
        105.0: 3.8750,  # 3 7/8"
        110.0: 3.8750,  # 3 7/8" (stair-step)
        115.0: 4.3750,  # 4 3/8"
        120.0: 4.3750,  # 4 3/8" (stair-step)
        125.0: 4.6250,  # 4 5/8"
        130.0: 4.8750,  # 4 7/8"
        140.0: 4.8750,  # 4 7/8" (stair-step)
        145.0: 5.3750,  # 5 3/8" (VALOR CRÍTICO COMERCIAL)
        150.0: 5.6250,  # 5 5/8"
        155.0: 5.8750,  # 5 7/8"
    }
    w_key = round(float(ancho_mm), 1)
    if w_key in CANONICAL_S2S:
        return CANONICAL_S2S[w_key]
    # Fuera de rango o 135 mm: división directa
    return round(float(ancho_mm) / 25.4, 4)

def run_simulation(env):
    print("=" * 125)
    print("SIMULACIÓN DE IMPACTO WP-B EN LÍNEAS DE EMBARQUE (SOLO LECTURA)")
    print("=" * 125)

    ShipmentLine = env['lumber.shipment.line']
    lines = ShipmentLine.search([], order='shipment_id, container_id, id')

    print(f"Total de líneas de embarque encontradas: {len(lines)}\n")
    print(f"{'ID':<6} | {'Embarque':<22} | {'Contenedor':<24} | {'Lote':<20} | {'(i) Almacenado':<14} | {'(ii) Actual':<12} | {'(iii) Propuesto':<15}")
    print("-" * 125)

    total_i = 0.0
    total_ii = 0.0
    total_iii = 0.0

    for l in lines:
        lot = l.lot_id
        stored_val = round(l.export_volume_m3 or 0.0, 3)

        # 1. Fórmula Actual hoy de lumber.shipment.line._compute_export_volume
        rule = l.shipment_id.shipping_rule_id
        w_mm = lot.ancho_mm or 0.0
        t_mm = lot.espesor_mm or 0.0
        l_m = lot.largo_m or 0.0
        pzas = lot.piezas or 0
        final_w = w_mm

        if rule and rule.calculation_method == 'nominal_plus_allowance':
            nom_in = l._parse_nominal_inches(lot)
            if nom_in > 0:
                final_w = (nom_in + (rule.allowance_inches or 0.0)) * 25.4

        if t_mm and final_w and l_m and pzas:
            actual_val = round((t_mm * final_w * l_m * pzas) / 1_000_000.0, 3)
        else:
            actual_val = round(l.physical_volume_m3 or 0.0, 3)

        # 2. Fórmula Propuesta (S2S Canónica con Factor 1550 o consumo directo de lot.vol_shipment_m3)
        if w_mm > 0 and t_mm > 0 and l_m > 0 and pzas > 0:
            e_in = t_mm / 25.4
            s2s_in = get_s2s_width_inches(w_mm, env=env)
            prop_val = round((e_in * s2s_in * l_m * pzas) / 1550.003, 3)
        else:
            prop_val = round(lot.vol_shipment_m3 or lot.volume_purchase_m3 or l.physical_volume_m3 or 0.0, 3)

        c_name = l.container_id.name if l.container_id else 'Sin Contenedor'
        s_name = l.shipment_id.name if l.shipment_id else 'Sin Embarque'

        total_i += stored_val
        total_ii += actual_val
        total_iii += prop_val

        diff_str = ""
        if abs(prop_val - stored_val) >= 0.001:
            diff_str = f" [CAMBIO: {prop_val - stored_val:+.3f} m³]"

        print(f"{l.id:<6} | {s_name[:22]:<22} | {c_name[:24]:<24} | {lot.name[:20]:<20} | {stored_val:<14.3f} | {actual_val:<12.3f} | {prop_val:<15.3f}{diff_str}")

    print("-" * 125)
    print(f"{'TOTAL':<6} | {'':<22} | {'':<24} | {'':<20} | {total_i:<14.3f} | {total_ii:<12.3f} | {total_iii:<15.3f} [NETO: {total_iii - total_i:+.3f} m³]")
    print("=" * 125)

if __name__ == '__main__':
    try:
        # Modo odoo shell
        if 'env' in locals() or 'env' in globals():
            run_simulation(env)
        else:
            # Modo script python independiente
            import odoo
            odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'madenat_test'])
            from odoo import api, SUPERUSER_ID
            registry = odoo.modules.registry.Registry('madenat_test')
            with registry.cursor() as cr:
                env_standalone = api.Environment(cr, SUPERUSER_ID, {})
                run_simulation(env_standalone)
    except Exception as e:
        print(f"Error al ejecutar simulación: {e}", file=sys.stderr)
        raise
