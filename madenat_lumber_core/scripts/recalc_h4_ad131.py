#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT CONTROLADO DE SIMULACIÓN Y RECÁLCULO AD-131 (FASE 5 / H4)
Proyecto: MADENAT — Odoo 18 CE (base: madenat_test)

Uso:
  # 1. Simulación (Solo lectura / Dry-run):
  python3 recalc_h4_ad131.py --dry-run

  # 2. Aplicación real (ORM con bypass de staging y chatter):
  python3 recalc_h4_ad131.py --apply
"""

import os
import sys
import argparse
from decimal import Decimal

ODOO_CONF = "/etc/odoo/odoo.conf"
DB_NAME = "madenat_test"

def calc_expected_shipment_vol(lot, config):
    if getattr(lot, 'lot_flow_type', False) == 'volume':
        return lot.vol_shipment_m3 or 0.0

    is_std = getattr(lot.product_id, 'use_commercial_standard', False)
    comm_t = getattr(lot.product_id, 'commercial_thickness_mm', 0.0) if is_std else 0.0
    comm_w = getattr(lot.product_id, 'commercial_width_mm', 0.0) if is_std else 0.0

    e_mm = (
        lot.espesor_nominal_mm if lot.espesor_nominal_mm > 0
        else (comm_t if comm_t > 0 else lot.espesor_mm)
    )
    a_mm = (
        lot.ancho_nominal_mm if lot.ancho_nominal_mm > 0
        else (comm_w if comm_w > 0 else lot.ancho_mm)
    )
    if not e_mm or not a_mm or not lot.piezas:
        return lot.vol_shipment_m3 or 0.0

    subprod = lot.subproducto_id
    family = getattr(subprod, 'calculation_family', False)
    is_blank = (family == 'blank' or bool(lot.largo_ft_frac))

    from odoo.addons.madenat_lumber_core.models.utils_uom import (
        parse_fraction_to_decimal_inch, ROUGH_THICKNESS_6_4_MM,
        NOMINAL_EXPORT_THICKNESS_6_4_INCHES, MM_PER_INCH, FT_TO_M,
        BLANK_CLEAR_FACTOR, M3_DIVISOR, INCH_SQ_METERS_TO_M3, r3
    )

    if lot.thickness_visual:
        t_exp_in = parse_fraction_to_decimal_inch(lot.thickness_visual)
    elif lot.reception_thickness_in > 0:
        t_exp_in = lot.reception_thickness_in
    elif abs(e_mm - float(ROUGH_THICKNESS_6_4_MM)) < 1.0:
        t_exp_in = float(NOMINAL_EXPORT_THICKNESS_6_4_INCHES)
    else:
        t_exp_in = e_mm / float(MM_PER_INCH)

    is_s2s = getattr(lot, 'is_s2s_inches', False) or is_blank
    details = config.resolve_export_width_details(
        rough_mm=a_mm,
        record=lot,
        is_s2s_inches=is_s2s,
    )
    ancho_calculo = details['calc_width_inches']

    if is_blank:
        if lot.largo_ft_frac:
            largo_ft = float(str(lot.largo_ft_frac).replace("'", "").strip())
        else:
            l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
            largo_ft = l_m / float(FT_TO_M) if l_m else 0.0
        vol_gold = (t_exp_in * ancho_calculo * largo_ft * lot.piezas) / float(BLANK_CLEAR_FACTOR)
    elif family == 'rough':
        l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
        if not l_m:
            return lot.vol_shipment_m3 or 0.0
        vol_gold = (e_mm * a_mm * l_m * lot.piezas) / float(M3_DIVISOR)
    else:
        l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
        if not l_m:
            return lot.vol_shipment_m3 or 0.0
        vol_gold = (t_exp_in * ancho_calculo * l_m * lot.piezas) / float(INCH_SQ_METERS_TO_M3)

    return r3(vol_gold)

def run_recalc(apply_changes=False):
    import odoo
    from odoo import api, SUPERUSER_ID

    odoo.tools.config.parse_config(['-c', ODOO_CONF, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("=" * 80)
        print(f"=== INICIANDO AD-131: RECÁLCULO CONTROLADO (Modo: {'APLICACIÓN' if apply_changes else 'SIMULACIÓN SOLO LECTURA'}) ===")
        print("=" * 80)

        LotModel = env['stock.lot']
        ReceptionLineModel = env['lumber.reception.line']
        ShipmentLineModel = env['lumber.shipment.line']
        GuiaLineModel = env['madenat.guia.processing.line']
        CostLineModel = env.get('stock.lot.cost.line')
        config = env['madenat.ingestion.config']

        all_lots = LotModel.search([('vol_shipment_m3', '>', 0.0), ('lot_flow_type', '!=', 'volume')])
        print(f"Total lotes analizados en BD (excluyendo Lotes Volumen SV): {len(all_lots)}")

        lots_to_recalc = []
        blank_lots_affected = []

        total_vol_old = 0.0
        total_vol_new = 0.0

        for lot in all_lots:
            vol_actual = lot.vol_shipment_m3 or 0.0
            family = getattr(lot.subproducto_id, 'calculation_family', False)
            is_blank = (family == 'blank' or bool(lot.largo_ft_frac))

            vol_simulado = calc_expected_shipment_vol(lot, config)
            diff = round(vol_simulado - vol_actual, 3)

            if abs(diff) > 0.0001:
                if is_blank:
                    blank_lots_affected.append((lot.id, lot.name, vol_actual, vol_simulado, diff))
                else:
                    lots_to_recalc.append({
                        'lot': lot,
                        'id': lot.id,
                        'name': lot.name,
                        'family': family or 's2s',
                        'ancho_mm': lot.ancho_mm,
                        'piezas': lot.piezas,
                        'vol_actual': vol_actual,
                        'vol_nuevo': vol_simulado,
                        'diff': diff,
                    })
                    total_vol_old += vol_actual
                    total_vol_new += vol_simulado

        print(f"\nGATE CHECK: Lotes Blanks afectados por recálculo: {len(blank_lots_affected)}")
        if blank_lots_affected:
            print("🚨 ERROR CRÍTICO GATE: El recálculo afecta lotes Blanks que deben permanecer intactos:")
            for b in blank_lots_affected[:10]:
                print(f"  - Lote {b[1]} (ID {b[0]}): actual={b[2]:.3f}, simulado={b[3]:.3f}, diff={b[4]:.3f}")
            print("DETENIENDO EJECUCIÓN (Regla Inamovible D1 / Gate 5.2).")
            return False

        print(f"Lotes cepillados S2S que NO coinciden y requieren recálculo: {len(lots_to_recalc)}")
        print(f"Total Volumen Actual en lotes a recalcular: {total_vol_old:.3f} m³")
        print(f"Total Volumen Nuevo en lotes a recalcular:  {total_vol_new:.3f} m³")
        print(f"Diferencia neta total:                      {total_vol_new - total_vol_old:.3f} m³")

        print("\nDetalle de lotes que difieren (primeros 20):")
        for item in lots_to_recalc[:20]:
            print(f"  Lote {item['name']:<18} | A:{item['ancho_mm']:>5.1f}mm | Pzas:{item['piezas']:>4} | Actual:{item['vol_actual']:>6.3f} | Nuevo:{item['vol_nuevo']:>6.3f} | Diff:{item['diff']:>+6.3f} m³")

        # 5.4 Reporte de Costing dependiente de lotes recalculados (sin tocarlos)
        recalc_lot_ids = [item['id'] for item in lots_to_recalc]
        recalc_lot_names = [item['name'] for item in lots_to_recalc]
        new_vol_by_name = {item['name']: item['vol_nuevo'] for item in lots_to_recalc}

        costing_count = 0
        if CostLineModel and recalc_lot_ids:
            costing_count = CostLineModel.search_count([('lot_id', 'in', recalc_lot_ids)])
        print(f"\n[5.4] Registros de costing (stock.lot.cost.line) dependientes de lotes a recalcular: {costing_count} (NO TOCADOS)")

        if not apply_changes:
            print("\n[SIMULACIÓN CONCLUIDA] No se realizaron cambios en la base de datos (Dry-run).")
            return True

        # 5.3 Aplicación por el ORM
        print("\n[5.3] APLICANDO RECÁLCULO POR EL ORM CON BYPASS DE SALVAGUARDA...")
        updated_lots = 0
        for item in lots_to_recalc:
            lot = item['lot'].with_context(bypass_staging_safeguard=True)
            new_vol = item['vol_nuevo']
            old_vol = item['vol_actual']
            diff = item['diff']
            print(f"  -> Recalculando Lote {lot.name} (ID {lot.id}): {lot.espesor_mm}x{lot.ancho_mm}x{lot.largo_m}m, {lot.piezas} pzas | Ant: {old_vol:.3f} m³ -> Nvo: {new_vol:.3f} m³ | Diff: {diff:+.3f} m³")
            lot.write({'vol_shipment_m3': new_vol})
            if hasattr(lot, 'message_post'):
                lot.message_post(body="recalculado por AD-131")
            updated_lots += 1

        print(f"Registros actualizados en stock.lot: {updated_lots}")

        # Sincronización en líneas de recepción
        updated_receptions = 0
        if recalc_lot_names and ReceptionLineModel:
            reception_lines = ReceptionLineModel.search([('lot_name', 'in', recalc_lot_names)])
            for rline in reception_lines:
                new_v = new_vol_by_name.get(rline.lot_name)
                if new_v is not None:
                    rline.vol_shipment_m3 = new_v
                    updated_receptions += 1
        print(f"Registros sincronizados en lumber.reception.line: {updated_receptions}")

        # Sincronización en líneas de guía processing
        updated_guia_lines = 0
        if recalc_lot_names and GuiaLineModel:
            guia_lines = GuiaLineModel.search([('lot_name', 'in', recalc_lot_names)])
            for gline in guia_lines:
                new_v = new_vol_by_name.get(gline.lot_name)
                if new_v is not None:
                    gline.vol_shipment_m3 = new_v
                    updated_guia_lines += 1
        print(f"Registros sincronizados en madenat.guia.processing.line: {updated_guia_lines}")

        # Sincronización en líneas de embarque
        updated_shipments = 0
        if recalc_lot_ids and ShipmentLineModel:
            shipment_lines = ShipmentLineModel.search([('lot_id', 'in', recalc_lot_ids)])
            for sline in shipment_lines:
                sline._compute_export_dims()
                sline._compute_export_volume()
                updated_shipments += 1
        print(f"Registros sincronizados en lumber.shipment.line: {updated_shipments}")

        cr.commit()
        print("\n✅ RECÁLCULO AD-131 APLICADO Y COMMITEADO EN BASE DE DATOS.")
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script de recálculo controlado AD-131 (H4)")
    parser.add_argument('--apply', action='store_true', help="Aplica los cambios en BD. Por defecto es dry-run.")
    parser.add_argument('--dry-run', action='store_true', help="Solo simula sin modificar BD.")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    success = run_recalc(apply_changes=apply)
    sys.exit(0 if success else 1)
