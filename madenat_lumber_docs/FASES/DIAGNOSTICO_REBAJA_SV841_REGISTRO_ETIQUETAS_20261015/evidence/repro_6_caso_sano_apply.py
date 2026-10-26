# Transaccion revertida. No toca IMP04823/IMP02220.
Guia = env['madenat.guia.processing'].browse(1198); Imp = env['madenat.sv.imputation']; Wiz = env['madenat.sv.imputation.wizard']
SLine = env['madenat.sv.imputation.wizard.sv.line']
usadas = {18368, 18372}  # ya imputadas por IMP02220 (applied)
w = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w._onchange_guia_processing_id()
linea = w.line_ids.filtered(lambda l: l.processed_lot_id.id not in usadas)[0]
vol = linea.nominal_volume_m3
linea.selected = True
SLine.create({'wizard_id': w.id, 'wizard_line_id': linea.id, 'sv_lot_id': 10215, 'imputed_volume_m3': vol})
print('--- CASO SANO: etiqueta', linea.processed_lot_id.name, '| nominal', vol, '| destino SV00000000841 ---')
print('  firma ->', repr(w._i2_signature()), '| clave ->', Imp._i2_build_documentary_key(Guia, None, w._i2_signature()))
imp = w._i2_guarded_build(); print('  documento:', imp.name, '| lineas:', len(imp.line_ids), '| repartos:', len(imp.sv_line_ids))
u8 = env['res.users'].browse(8)
imp.with_user(u8).action_apply(); imp.invalidate_recordset()
print('  tras APLICAR -> state:', imp.state, '| firma SHA-256:', bool(imp.audit_hash))
sv = env['stock.lot'].browse(10215)
print('  SV00000000841 -> asignaciones aplicadas:', len(sv.sv_assignment_sv_line_ids), '| rebajado documental:', sv.sv_assignment_applied_m3, '| trabajo:', sv.sv_assignment_work_count)
print('  reparto:', [(l.imputation_name, l.processed_lot_id.name, l.imputed_volume_m3, l.imputation_state) for l in sv.sv_assignment_sv_line_ids])
env.cr.rollback(); print('ROLLBACK (sin cambios)')
