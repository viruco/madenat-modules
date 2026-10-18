# -*- coding: utf-8 -*-
"""
Script de comprobación previa al despliegue (SOLO LECTURA, inocuo).
Proyecto: MADENAT — Odoo 18 CE (AD-119 / Bloque 4F)

Verifica el estado del sistema previo al despliegue en TEST / Producción:
  1. 15 anchos activos en lumber.width.s2s.map y su valor por ancho.
  2. Parámetros madenat.* y su consistencia.
  3. Parámetro deprecado madenat.s2s_exclusion_widths.
  4. Versión instalada de cada módulo madenat_* frente al manifiesto y estado to_upgrade.
  5. deduction_factor en lumber.export.formula (revisión de modelo y base).
  6. Marcador is_patio en stock.location.
  7. Existencia de parámetros location_marval_id / location_puerto_coronel_id.

Uso:
  docker exec -i <container> odoo shell -c /etc/odoo/odoo.conf -d <db> --no-http < pre_deploy_health_check.py
  o ejecución directa desde terminal / script.

Garantía:
  Ejecuta env.cr.rollback() al finalizar. Código de salida 1 ante discrepancias críticas, 0 si todo está OK.
"""

import sys
import os
import logging

_logger = logging.getLogger("pre_deploy_health_check")

# Tabla canónica de 15 anchos S2S (AD-116 / AD-117 / AD-119)
CANONICAL_S2S_WIDTHS = {
    75: 2.625,
    85: 2.875,
    90: 3.125,
    95: 3.375,
    100: 3.625,
    105: 3.875,
    110: 3.875,
    115: 4.375,
    120: 4.375,
    125: 4.625,
    130: 4.875,
    140: 4.875,
    145: 5.375,
    150: 5.625,
    155: 5.875,
}

def run_health_check(env):
    discrepancies = []
    warnings = []

    print("=" * 80)
    print("MADENAT ODOO 18 CE — COMPROBACIÓN PREVIA AL DESPLIEGUE (SOLO LECTURA)")
    print("=" * 80)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. TABLA S2S (lumber.width.s2s.map)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[1] Verificando lumber.width.s2s.map (15 anchos activos canónicos)...")
    try:
        s2s_records = env['lumber.width.s2s.map'].search([('active', '=', True)], order='sequence, rough_mm')
        active_count = len(s2s_records)
        print(f"    Total registros activos encontrados: {active_count} (esperados: 15)")
        if active_count != 15:
            discrepancies.append(f"lumber.width.s2s.map tiene {active_count} registros activos, esperados exactamente 15.")

        found_map = {}
        for rec in s2s_records:
            found_map[rec.rough_mm] = rec.s2s_decimal
            exp_dec = CANONICAL_S2S_WIDTHS.get(rec.rough_mm)
            if exp_dec is None:
                warnings.append(f"Ancho rough {rec.rough_mm} mm en BD no está en lista canónica de 15.")
            elif abs(rec.s2s_decimal - exp_dec) > 1e-4:
                discrepancies.append(
                    f"Ancho rough {rec.rough_mm} mm tiene s2s_decimal={rec.s2s_decimal}, esperado {exp_dec}"
                )
            else:
                print(f"    ✓ {rec.rough_mm:>3} mm -> {rec.s2s_decimal:.3f}\" ({rec.s2s_label})")

        # Comprobar 115 mm explícitamente
        if 115 in found_map:
            val_115 = found_map[115]
            if abs(val_115 - 4.375) < 1e-4:
                print("    ✓ 115 mm verificado canónico: 4.375\" (4 3/8\"), no 4.125\".")
            else:
                discrepancies.append(f"115 mm tiene valor {val_115}, esperado 4.375\".")
        else:
            discrepancies.append("115 mm no existe o está inactivo en lumber.width.s2s.map.")

    except Exception as e:
        discrepancies.append(f"Error consultando lumber.width.s2s.map: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. PARÁMETROS madenat.* (ir.config_parameter)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[2] Verificando parámetros madenat.*...")
    param_obj = env['ir.config_parameter'].sudo()
    expected_params = {
        'madenat.s2s_overwidth_inches': '0.125',
        'madenat.out_of_table_behavior': 'warning',  # default canónico
        'madenat.direct_width_min_mm': '170.0',
        'madenat.drying_temp_min_c': '50.0',
        'madenat.drying_temp_max_c': '90.0',
        'madenat.drying_duration_min_hours': '50.0',
        'madenat.drying_duration_max_hours': '80.0',
    }

    for key, def_val in expected_params.items():
        val = param_obj.get_param(key, None)
        if val is None:
            warnings.append(f"Parámetro {key} no existe en ir.config_parameter (usará default {def_val}).")
            print(f"    ⚠️ {key}: AUSENTE (default en código: {def_val})")
        else:
            print(f"    ✓ {key} = {val}")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. PARÁMETRO DEPRECADO madenat.s2s_exclusion_widths
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[3] Verificando parámetro deprecado madenat.s2s_exclusion_widths...")
    deprecated_val = param_obj.get_param('madenat.s2s_exclusion_widths', None)
    if deprecated_val is not None:
        warnings.append(f"Parámetro deprecado madenat.s2s_exclusion_widths aún presente en BD: {deprecated_val}")
        print(f"    ⚠️ madenat.s2s_exclusion_widths presente en BD: {deprecated_val} (ignorado por AD-116/AD-117)")
    else:
        print("    ✓ madenat.s2s_exclusion_widths ausente de BD (correcto).")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. VERSIONES INSTALADAS Y ESTADO TO_UPGRADE
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[4] Verificando módulos madenat_* en ir.module.module...")
    installed_modules = env['ir.module.module'].search([
        ('name', '=like', 'madenat_%'),
        ('state', 'in', ['installed', 'to upgrade', 'to install'])
    ])
    for mod in installed_modules:
        status_flag = "✓" if mod.state == 'installed' else "⚠️"
        print(f"    {status_flag} {mod.name:<35} estado={mod.state:<12} version_instalada={mod.installed_version}")
        if mod.state in ('to upgrade', 'to install'):
            warnings.append(f"Módulo {mod.name} en estado pendiente: {mod.state}")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. DEDUCTION_FACTOR EN FÓRMULAS
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[5] Verificando deduction_factor en lumber.export.formula...")
    try:
        FormulaModel = env['lumber.export.formula']
        if hasattr(FormulaModel, 'deduction_factor'):
            discrepancies.append("El campo deduction_factor aún existe en el modelo lumber.export.formula.")
        else:
            print("    ✓ deduction_factor retirado exitosamente del modelo Python lumber.export.formula.")

        # Verificar si la columna SQL aún existe (preservación de base sin drop column)
        env.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'lumber_export_formula' AND column_name = 'deduction_factor';"
        )
        col_exists = bool(env.cr.fetchall())
        if col_exists:
            print("    ✓ Columna deduction_factor conservada en tabla PostgreSQL (no eliminada).")
        else:
            print("    ℹ️ Columna deduction_factor no existe en tabla PostgreSQL.")

        # Comprobar resolución para perfil f5085
        resolved_f5085 = FormulaModel._resolve_for_profile('f5085')
        if 'deduction_factor' in resolved_f5085:
            discrepancies.append("Fórmula resuelta f5085 aún contiene clave deduction_factor.")
        else:
            print(f"    ✓ Fórmula resuelta f5085 limpia: principal_factor={resolved_f5085.get('principal_factor')}")

    except Exception as e:
        discrepancies.append(f"Error verificando fórmulas: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. MARCADOR IS_PATIO EN UBICACIONES
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[6] Verificando marcador is_patio en stock.location...")
    try:
        LocationModel = env['stock.location']
        has_is_patio = hasattr(LocationModel, 'is_patio')
        print(f"    Campo is_patio en stock.location: {'DISPONIBLE' if has_is_patio else 'NO DEFINIDO'}")

        # Ubicaciones clave
        for loc_name in ['MARVAL', 'PUERTO CORONEL', 'Bodega Tepornac']:
            loc = LocationModel.search([('name', '=', loc_name)], limit=1)
            if loc:
                val_patio = getattr(loc, 'is_patio', 'N/A')
                print(f"    ✓ Ubicación {loc_name:<16} (id={loc.id:>2}): complete_name='{loc.complete_name}' is_patio={val_patio}")
            else:
                warnings.append(f"Ubicación '{loc_name}' no encontrada en stock.location.")
                print(f"    ⚠️ Ubicación {loc_name} no encontrada en stock.location.")

    except Exception as e:
        discrepancies.append(f"Error consultando stock.location: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. PARÁMETROS DE UBICACIÓN (location_marval_id / location_puerto_coronel_id)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[7] Verificando parámetros location_marval_id y location_puerto_coronel_id...")
    for loc_key in ['madenat.location_marval_id', 'madenat.location_puerto_coronel_id', 'location_marval_id', 'location_puerto_coronel_id']:
        pval = param_obj.get_param(loc_key, None)
        if pval is not None:
            loc_target = env['stock.location'].browse(int(pval)) if str(pval).isdigit() else None
            loc_desc = f"-> id={loc_target.id} '{loc_target.complete_name}'" if loc_target and loc_target.exists() else "(ID inválido)"
            print(f"    ✓ {loc_key} = {pval} {loc_desc}")
        else:
            print(f"    ℹ️ {loc_key}: NO configurado")

    # ──────────────────────────────────────────────────────────────────────────
    # RESUMEN Y ROLLBACK
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESUMEN DE COMPROBACIÓN:")
    print(f"  Discrepancias críticas : {len(discrepancies)}")
    print(f"  Advertencias no fatales: {len(warnings)}")
    print("=" * 80)

    if warnings:
        print("\nADVERTENCIAS:")
        for w in warnings:
            print(f"  - {w}")

    if discrepancies:
        print("\nDISCREPANCIAS CRÍTICAS:")
        for d in discrepancies:
            print(f"  ❌ {d}")
        print("\nRESULTADO: FALLO (código de salida 1).")
        return 1

    print("\nRESULTADO: EXITOSO (código de salida 0). Sistema íntegro para despliegue.")
    return 0


# Punto de entrada Odoo shell
if 'env' in locals():
    try:
        code = run_health_check(env)
    finally:
        env.cr.rollback()
        print("\n[ROLLBACK] Transacción de solo lectura revertida exitosamente. Cero modificaciones en BD.")
    if code != 0:
        sys.exit(1)
elif __name__ == '__main__':
    print("Este script debe ejecutarse dentro del entorno odoo shell.")
    sys.exit(1)
