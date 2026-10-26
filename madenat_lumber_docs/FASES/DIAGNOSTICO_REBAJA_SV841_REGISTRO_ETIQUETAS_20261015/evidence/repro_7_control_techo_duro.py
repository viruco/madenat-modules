# Control negativo (E8): etiqueta YA consumida por IMP02220 -> techo duro al aplicar.
# Transaccion revertida. No toca IMP04823/IMP02220.
Guia = env['madenat.guia.processing'].browse(1198)
Imp = env['madenat.sv.imputation']; Wiz = env['madenat.sv.imputation.wizard']
SLine = env['madenat.sv.imputation.wizard.sv.line']
LOTE_CONSUMIDO = 18368  # 'D7632 PCLAT04201252900 19827': 3.263 m3 ya imputados por IMP02220 (applied)
w = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w._onchange_guia_processing_id()
linea = w.line_ids.filtered(lambda l: l.processed_lot_id.id == LOTE_CONSUMIDO)[0]
linea.selected = True
SLine.create({'wizard_id': w.id, 'wizard_line_id': linea.id, 'sv_lot_id': 10215,
              'imputed_volume_m3': linea.nominal_volume_m3})
print('etiqueta:', linea.processed_lot_id.name, '| nominal:', linea.nominal_volume_m3)
imp = w._i2_guarded_build()
print('documento:', imp.name, '| lineas:', len(imp.line_ids), '| repartos:', len(imp.sv_line_ids))
try:
    imp.with_user(env['res.users'].browse(8)).action_apply()
    print('APLICADA (inesperado: el techo duro NO se activo)')
except Exception as err:
    print('CONTROL NEGATIVO OK ->', type(err).__name__, ':', str(err)[:110])
env.cr.rollback()
print('ROLLBACK (sin cambios)')
