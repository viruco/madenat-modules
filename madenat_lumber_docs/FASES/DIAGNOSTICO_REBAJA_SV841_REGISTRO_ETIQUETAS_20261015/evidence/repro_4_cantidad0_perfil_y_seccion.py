# Transaccion revertida. No toca IMP04823/IMP02220.
Guia = env['madenat.guia.processing'].browse(1198); Imp = env['madenat.sv.imputation']; Wiz = env['madenat.sv.imputation.wizard']
WLine = env['madenat.sv.imputation.wizard.line']; SLine = env['madenat.sv.imputation.wizard.sv.line']
print('--- PASO 1: seleccionar 2 etiquetas + destino SV con CANTIDAD 0 (SAVE-05) ---')
w = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w._onchange_guia_processing_id()
for l in w.line_ids[:2]: l.selected = True
SLine.create({'wizard_id': w.id, 'wizard_line_id': w.line_ids[0].id, 'sv_lot_id': 10215, 'imputed_volume_m3': 0.0})
print('  firma ->', repr(w._i2_signature())[:70])
print('  clave que se usara ->', Imp._i2_build_documentary_key(Guia, None, w._i2_signature()))
imp = w._i2_guarded_build()
print('  documento:', imp.name, '| state:', imp.state, '| LINEAS:', len(imp.line_ids), '| repartos persistidos:', len(imp.sv_line_ids), '| work_sv_lot_id:', imp.work_sv_lot_id.id)
print()
print('--- PASO 2: guardar de nuevo SIN seleccion (misma firma vacia) ---')
w2 = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w2._onchange_guia_processing_id()
print('  el asistente reconstruye', len(w2.line_ids), 'lineas; seleccionadas:', len(w2.line_ids.filtered('selected')))
w2.imputation_id = imp.id; w2.expected_edit_version = imp.edit_version or 1
imp2 = w2._i2_guarded_build()
print('  LINEAS tras guardar sin seleccion:', len(imp2.line_ids), '| mismo documento:', imp2.id == imp.id)
print()
print('--- PASO 3: la seccion del SV mostraria el documento? ---')
lot = env['stock.lot'].browse(10215)
print('  sv_assignment_work_imputation_ids ->', lot.sv_assignment_work_imputation_ids.ids, '| contador:', lot.sv_assignment_work_count)
env.cr.rollback(); print('ROLLBACK (sin cambios)')
