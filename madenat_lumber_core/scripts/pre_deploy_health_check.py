# -*- coding: utf-8 -*-
"""
Script de comprobacion previa al despliegue (SOLO LECTURA, inocuo).
Proyecto: MADENAT — Odoo 18 CE (AD-120 / Bloque 4G)

Niveles de resultado:
  OK         — condicion nominal cumplida.
  ADVERTENCIA — discrepancia no fatal; codigo de salida 0.
  CRITICO    — falla estructural; codigo de salida 1.

CRITICO solo ante:
  - Tabla S2S vacia (0 registros activos).
  - Modulo no instalado (state != 'installed').
  - Estado to_upgrade pendiente en modulos madenat_*.

ADVERTENCIA (se reportan, no se corrigen, D1/D2):
  - madenat.out_of_table_behavior = 'direct' en lugar del canonico 'warning'.
  - is_patio = False en MARVAL, PUERTO CORONEL, Bodega Tepornac.
  - Parametro deprecado madenat.s2s_exclusion_widths presente en BD.
  - Desviacion de version instalada vs. manifiesto.

Garantia de solo lectura:
  env.cr.rollback() ejecutado al finalizar. Sin INSERT/UPDATE/DELETE.
  Sin llamadas a .write(), .create(), .unlink() ni .commit().

Uso:
  docker exec -i <container> odoo shell -c /etc/odoo/odoo.conf -d <db> --no-http \\
    < madenat_lumber_core/scripts/pre_deploy_health_check.py
"""

import sys
import os

# Tabla canonica de 15 anchos S2S (AD-113 / AD-116 / AD-117 / AD-119 — datos Cristhian Elgueta)
# Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx
# NO modificar sin autorizacion de Cristhian Elgueta (D6).
CANONICAL_S2S_15 = {
    75:  (2.6250, '2 5/8'),
    85:  (2.8750, '2 7/8'),
    90:  (3.1250, '3 1/8'),
    95:  (3.3750, '3 3/8'),
    100: (3.6250, '3 5/8'),
    105: (3.8750, '3 7/8'),
    110: (3.8750, '3 7/8'),   # stair-step: mismo que 105
    115: (4.3750, '4 3/8'),   # CRITICO: no debe ser 4.125
    120: (4.3750, '4 3/8'),   # stair-step: mismo que 115
    125: (4.6250, '4 5/8'),
    130: (4.8750, '4 7/8'),
    140: (4.8750, '4 7/8'),   # stair-step: mismo que 130
    145: (5.3750, '5 3/8'),
    150: (5.6250, '5 5/8'),
    155: (5.8750, '5 7/8'),
}

# Modulos a inspeccionar (incluidos madenat_lumber_intake y shipping_core)
MODULES_TO_CHECK = [
    'madenat_lumber_core',
    'madenat_lumber_intake',
    'madenat_lumber_logistics',
    'madenat_lumber_billing',
    'madenat_lumber_costing',
    'madenat_lumber_purchasing',
    'madenat_lumber_reception_improvements',
    'madenat_lumber_reports',
    'madenat_lumber_shipping_core',
    'madenat_ingestion_engine',
    'madenat_toll_processing',
    'madenat_vendor_payment',
]

# Ubicaciones de patio a verificar (D2: marcado pendiente, solo ADVERTENCIA)
PATIO_LOCATIONS = ['MARVAL', 'PUERTO CORONEL', 'Bodega Tepornac']

# Parametro canonico vs. valor en madenat_test (D1)
PARAM_CANONICAL = {
    'madenat.out_of_table_behavior': 'warning',
    'madenat.direct_width_min_mm': '170.0',
    'madenat.s2s_overwidth_inches': '0.125',
}


def _sep(char='=', n=90):
    return char * n


def run_health_check(env):
    criticos = []    # Codigo de salida 1
    advertencias = []  # Codigo de salida 0
    ok_count = 0

    def ok(msg):
        nonlocal ok_count
        ok_count += 1
        print(f"  [OK]         {msg}")

    def warn(msg):
        advertencias.append(msg)
        print(f"  [ADVERTENCIA] {msg}")

    def critico(msg):
        criticos.append(msg)
        print(f"  [CRITICO]    {msg}")

    print(_sep())
    print("MADENAT ODOO 18 CE — PRE-DEPLOY HEALTH CHECK (AD-120 / Bloque 4G)")
    print("Solo lectura. Rollback al finalizar. Sin modificaciones en BD.")
    print(_sep())

    # ─────────────────────────────────────────────────────────────────────────
    # 1. TABLA S2S (lumber.width.s2s.map) — 15 anchos canonicos de Cristhian
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[1] Tabla S2S: lumber.width.s2s.map (15 anchos activos canonicos — datos Cristhian Elgueta)\n    Referencia: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx")
    try:
        s2s_recs = env['lumber.width.s2s.map'].sudo().search(
            [('active', '=', True)], order='sequence, rough_mm'
        )
        active_count = len(s2s_recs)
        print(f"    Registros activos encontrados: {active_count} (esperados: 15)")

        if active_count == 0:
            critico("Tabla S2S VACIA — lumber.width.s2s.map sin registros activos. Modulo no operativo.")
        elif active_count != 15:
            critico(f"Tabla S2S tiene {active_count} registros activos, esperados exactamente 15.")
        else:
            ok("Tabla S2S tiene exactamente 15 registros activos.")

        found_map = {}
        for rec in s2s_recs:
            found_map[rec.rough_mm] = (rec.s2s_decimal, rec.s2s_label)

        # Comparar contra tabla canonica de Cristhian
        for mm, (exp_dec, exp_label) in sorted(CANONICAL_S2S_15.items()):
            if mm not in found_map:
                critico(f"Ancho {mm} mm FALTA en lumber.width.s2s.map (esperado: {exp_dec}\" / {exp_label}).")
            else:
                got_dec, got_label = found_map[mm]
                diff = abs(got_dec - exp_dec)
                if diff > 1e-4:
                    critico(
                        f"Ancho {mm} mm: s2s_decimal={got_dec:.4f} DIFIERE del canonico "
                        f"{exp_dec:.4f} ({exp_label}). Diferencia={diff:.4f}\"."
                    )
                else:
                    ok(f"{mm:>3} mm -> {got_dec:.4f}\" ({got_label})")

        # Anchos extra en BD fuera del canonico de 15
        extra = [mm for mm in found_map if mm not in CANONICAL_S2S_15]
        if extra:
            warn(f"Anchos en BD fuera de la lista canonica de 15: {sorted(extra)} mm.")

        # Verificacion critica de 115 mm (caso historico 4.125 vs 4.375)
        if 115 in found_map:
            v115 = found_map[115][0]
            if abs(v115 - 4.375) < 1e-4:
                ok("115 mm verificado canonico: 4.375\" (4 3/8\"), no 4.125\" (AD-119).")
            else:
                critico(f"115 mm tiene s2s_decimal={v115:.4f}, esperado 4.375\" (4 3/8\").")

    except Exception as e:
        critico(f"Error consultando lumber.width.s2s.map: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. PARAMETROS madenat.* — diferencias reportadas como ADVERTENCIA (D1)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[2] Parametros madenat.* (diferencias del canonico = ADVERTENCIA, no se corrigen — D1)")
    param_obj = env['ir.config_parameter'].sudo()

    for key, canonical_val in PARAM_CANONICAL.items():
        val = param_obj.get_param(key, None)
        if val is None:
            warn(f"Parametro {key} AUSENTE en BD (default en codigo: '{canonical_val}').")
        elif val != canonical_val:
            warn(
                f"Parametro {key} = '{val}' (canonico esperado: '{canonical_val}'). "
                f"D1: se deja tal cual, no se corrige."
            )
        else:
            ok(f"{key} = '{val}' (canonico correcto).")

    # Parametros informativos adicionales
    info_params = [
        'madenat.drying_temp_min_c', 'madenat.drying_temp_max_c',
        'madenat.drying_duration_min_hours', 'madenat.drying_duration_max_hours',
        'madenat.nominal_tolerance',
    ]
    for key in info_params:
        val = param_obj.get_param(key, None)
        status = f"= '{val}'" if val is not None else "AUSENTE (usa default en codigo)"
        print(f"    [INFO]       {key} {status}")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. PARAMETRO DEPRECADO madenat.s2s_exclusion_widths
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[3] Parametro deprecado: madenat.s2s_exclusion_widths")
    deprecated_val = param_obj.get_param('madenat.s2s_exclusion_widths', None)
    if deprecated_val is not None:
        warn(
            f"Parametro deprecado madenat.s2s_exclusion_widths PRESENTE en BD: '{deprecated_val}'. "
            f"Ignorado por AD-116/AD-117 (resolve_export_width). Se puede eliminar de BD."
        )
    else:
        ok("madenat.s2s_exclusion_widths ausente de BD (correcto).")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. VERSIONES INSTALADAS (modulos madenat_* + shipping_core + intake)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[4] Versiones instaladas de modulos MADENAT (instalado vs. manifiesto)")
    custom_addons_path = None
    if '__file__' in globals() or '__file__' in locals():
        try:
            custom_addons_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception:
            pass
    if not custom_addons_path or not os.path.isdir(custom_addons_path):
        for candidate in ['/mnt/extra-addons', '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons']:
            if os.path.isdir(candidate):
                custom_addons_path = candidate
                break
    print(f"    custom_addons path inferido: {custom_addons_path}")

    for mod_name in MODULES_TO_CHECK:
        try:
            ir_mod = env['ir.module.module'].sudo().search([('name', '=', mod_name)], limit=1)
            if not ir_mod:
                warn(f"Modulo {mod_name} NO ENCONTRADO en ir.module.module.")
                continue

            installed_ver = ir_mod.installed_version or '(desconocida)'
            state = ir_mod.state

            # Leer version del manifiesto en disco
            manifest_path = os.path.join(custom_addons_path, mod_name, '__manifest__.py')
            manifest_ver = '(no leido)'
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                import re
                m = re.search(r"'version'\s*:\s*'([^']+)'", content)
                if m:
                    manifest_ver = m.group(1)

            if state == 'installed' and installed_ver == manifest_ver:
                ok(f"{mod_name:<40} state=installed  instalada={installed_ver}  manifiesto={manifest_ver}")
            elif state not in ('installed',):
                critico(
                    f"{mod_name}: estado={state} (esperado: installed). "
                    f"instalada={installed_ver} manifiesto={manifest_ver}."
                )
            elif installed_ver != manifest_ver:
                warn(
                    f"{mod_name}: version instalada '{installed_ver}' difiere del manifiesto '{manifest_ver}'. "
                    f"Puede requerir -u {mod_name}."
                )
            else:
                ok(f"{mod_name:<40} state={state}  instalada={installed_ver}  manifiesto={manifest_ver}")

        except Exception as e:
            warn(f"Error leyendo modulo {mod_name}: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. DEDUCTION_FACTOR EN lumber.export.formula
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[5] Retiro de deduction_factor en lumber.export.formula (AD-119 F2)")
    try:
        FormulaModel = env['lumber.export.formula']
        if hasattr(FormulaModel, 'deduction_factor'):
            critico("Campo deduction_factor TODAVIA PRESENTE en el modelo Python lumber.export.formula.")
        else:
            ok("Campo deduction_factor retirado exitosamente del modelo Python.")

        # Columna SQL (sin drop column por diseno — R5)
        env.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'lumber_export_formula' AND column_name = 'deduction_factor';"
        )
        col_exists = bool(env.cr.fetchall())
        if col_exists:
            ok("Columna deduction_factor conservada en PostgreSQL (sin DROP COLUMN — R5).")
        else:
            print("    [INFO]       Columna deduction_factor no existe en PostgreSQL.")

        # Inspeccion del valor residual (informativo)
        env.cr.execute(
            "SELECT id, deduction_factor FROM lumber_export_formula "
            "WHERE deduction_factor IS NOT NULL AND deduction_factor != 0 LIMIT 5;"
        ) if col_exists else None
        if col_exists:
            rows = env.cr.fetchall()
            if rows:
                warn(f"Fila(s) con deduction_factor != 0 en BD: {rows} (historico no tocado — R5).")
            else:
                ok("Todas las filas de lumber_export_formula tienen deduction_factor NULL o 0.")

        # Formula resuelta f5085
        resolved = FormulaModel._resolve_for_profile('f5085')
        print(f"    [INFO]       Formula resuelta f5085: principal_factor={resolved.get('principal_factor')} "
              f"formula_kind={resolved.get('formula_kind')} source={resolved.get('source')}")

    except Exception as e:
        warn(f"Error verificando lumber.export.formula: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. MARCADOR IS_PATIO EN UBICACIONES (D2 — solo ADVERTENCIA)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[6] Marcador is_patio en stock.location (D2: marcado pendiente — solo ADVERTENCIA)")
    try:
        LocationModel = env['stock.location'].sudo()
        has_is_patio = 'is_patio' in LocationModel._fields
        if not has_is_patio:
            warn("Campo is_patio NO definido en stock.location. Bloque 4C pendiente.")
        else:
            ok("Campo is_patio disponible en stock.location.")

        for loc_name in PATIO_LOCATIONS:
            locs = LocationModel.search([('name', '=', loc_name)], order='id')
            if not locs:
                warn(f"Ubicacion '{loc_name}' NO encontrada en stock.location.")
                continue
            for loc in locs:
                val_patio = getattr(loc, 'is_patio', None)
                full = getattr(loc, 'complete_name', loc.name)
                if has_is_patio and not val_patio:
                    warn(
                        f"Ubicacion '{loc_name}' (id={loc.id}, '{full}'): "
                        f"is_patio={val_patio} (D2: marcado pendiente, no se corrige)."
                    )
                elif has_is_patio and val_patio:
                    ok(f"Ubicacion '{loc_name}' (id={loc.id}, '{full}'): is_patio=True.")
                else:
                    print(f"    [INFO]       Ubicacion '{loc_name}' (id={loc.id}): campo is_patio no disponible.")

    except Exception as e:
        warn(f"Error consultando stock.location: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. PARAMETROS DE UBICACION POR NOMBRE (no IDs numericos — R3)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[7] Parametros de ubicacion en ir.config_parameter")
    loc_params = [
        'madenat.location_marval_id', 'madenat.location_puerto_coronel_id',
        'location_marval_id', 'location_puerto_coronel_id',
    ]
    for loc_key in loc_params:
        pval = param_obj.get_param(loc_key, None)
        if pval is not None:
            try:
                loc_id = int(pval)
                loc_target = env['stock.location'].sudo().browse(loc_id)
                loc_desc = f"-> id={loc_id} '{loc_target.complete_name}'" if loc_target.exists() else "(ID invalido/eliminado)"
            except (ValueError, TypeError):
                loc_desc = f"(valor no numerico: '{pval}')"
            print(f"    [INFO]       {loc_key} = '{pval}' {loc_desc}")
        else:
            print(f"    [INFO]       {loc_key}: NO configurado.")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. CONSULTA MD5 CANONICA (hashes de integridad — G4)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[8] Hashes MD5 canonicos de integridad (G4 AD-120)")
    MD5_KNOWN = {
        'stock_lot':                   '3871c02145712833e3ad9eea526405c5',
        'madenat_guia_processing_line': 'b43a26b6fd072ff96ed075ca1e2f585e',
        'lumber_shipment_line':         'b048f9428859b4c960b83b9ddf1cc701',
    }
    try:
        env.cr.execute("""
            SELECT 'stock_lot' AS tbl, COUNT(*) AS cnt,
              md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(name::text,''), ',' ORDER BY id)) AS hash
            FROM stock_lot
            UNION ALL
            SELECT 'madenat_guia_processing_line', COUNT(*),
              md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(vol_shipment_m3::text,''), ',' ORDER BY id))
            FROM madenat_guia_processing_line
            UNION ALL
            SELECT 'lumber_shipment_line', COUNT(*),
              md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(export_volume_m3::text,''), ',' ORDER BY id))
            FROM lumber_shipment_line;
        """)
        rows = env.cr.fetchall()
        for tbl, cnt, hsh in rows:
            known = MD5_KNOWN.get(tbl)
            if known and hsh == known:
                ok(f"{tbl:<40} cnt={cnt:<6} hash={hsh} (MATCH)")
            elif known:
                warn(
                    f"{tbl:<40} cnt={cnt:<6} hash={hsh}\n"
                    f"               referencia={known}\n"
                    f"               DIFERENCIA — verificar si hubo cambios en BD."
                )
            else:
                print(f"    [INFO]       {tbl:<40} cnt={cnt:<6} hash={hsh} (sin referencia previa)")
    except Exception as e:
        warn(f"Error ejecutando consulta MD5 canonica: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 9. VERIFICACION DE MAIL.THREAD en lumber.width.s2s.map (G8)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[9] Trazabilidad G8: mail.thread en lumber.width.s2s.map")
    try:
        S2SModel = env['lumber.width.s2s.map']
        has_msg = hasattr(S2SModel, 'message_ids')
        if has_msg:
            ok("lumber.width.s2s.map hereda mail.thread (trazabilidad de cambios activa).")
        else:
            warn("lumber.width.s2s.map NO hereda mail.thread aun. G8 requiere reinicio del servidor.")
    except Exception as e:
        warn(f"Error verificando mail.thread en lumber.width.s2s.map: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{_sep()}")
    print("RESUMEN FINAL:")
    print(f"  OK          : {ok_count}")
    print(f"  ADVERTENCIAS: {len(advertencias)} (codigo de salida 0 — D1/D2)")
    print(f"  CRITICOS    : {len(criticos)} (codigo de salida 1 si > 0)")
    print(_sep())

    if advertencias:
        print("\nADVERTENCIAS (no bloquean despliegue):")
        for i, w in enumerate(advertencias, 1):
            print(f"  [{i}] {w}")

    if criticos:
        print("\nDISCREPANCIAS CRITICAS (bloquean despliegue):")
        for i, d in enumerate(criticos, 1):
            print(f"  [{i}] CRITICO: {d}")
        print("\nRESULTADO: FALLO — codigo de salida 1.")
        return 1

    print("\nRESULTADO: EXITOSO — sistema integro para despliegue (codigo de salida 0).")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada: odoo shell o ejecucion directa
# ─────────────────────────────────────────────────────────────────────────────
if 'env' in dir():
    # Ejecutado desde odoo shell via pipe
    try:
        exit_code = run_health_check(env)  # noqa: F821
    finally:
        env.cr.rollback()  # noqa: F821
        print(
            "\n[ROLLBACK] Transaccion de solo lectura revertida. "
            "Cero modificaciones en BD."
        )
    if exit_code != 0:
        sys.exit(1)
elif __name__ == '__main__':
    print(
        "Uso: odoo shell -c /etc/odoo/odoo.conf -d <db> --no-http "
        "< madenat_lumber_core/scripts/pre_deploy_health_check.py"
    )
    sys.exit(1)
