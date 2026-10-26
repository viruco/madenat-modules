# ===== REPRODUCCION CONTROLADA - TODO DENTRO DE UNA TRANSACCION QUE SE REVIERTE =====
# No se toca IMP04823 ni IMP02220. Solo guia 1198 + SV 10215 en transaccion.
Guia = env['madenat.guia.processing'].browse(1198)
Wiz = env['madenat.sv.imputation.wizard']
SV = env['stock.lot'].browse(10215)
Imp = env['madenat.sv.imputation']
print('candidatas (lotes no-volumen de la guia):', len(env['madenat.sv.imputation.wizard']._i2_processed_lots(Guia)))

print('\n--- ESCENARIO 1: abrir y GUARDAR BORRADOR sin seleccionar nada ---')
w1 = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215})
w1._onchange_guia_processing_id()
print('  lineas del asistente:', len(w1.line_ids), '| seleccionadas:', len(w1.line_ids.filtered('selected')))
imp1 = w1._i2_guarded_build()
print('  documento:', imp1.name, '| state:', imp1.state, '| LINEAS:', len(imp1.line_ids), '| repartos:', len(imp1.sv_line_ids))

print('\n--- ESCENARIO 2: SELECCIONAR TODAS y guardar ---')
w2 = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215})
w2._onchange_guia_processing_id()
w2.action_select_all()
print('  seleccionadas:', len(w2.line_ids.filtered('selected')))
imp2 = w2._i2_guarded_build()
print('  documento:', imp2.name, '| state:', imp2.state, '| LINEAS:', len(imp2.line_ids), '| reparto a SV:', len(imp2.sv_line_ids))

print('\n--- ESCENARIO 3: guardar de nuevo SIN seleccion sobre el mismo documento (borrado silencioso?) ---')
w3 = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215})
w3._onchange_guia_processing_id()
w3.imputation_id = imp2.id; w3.expected_edit_version = imp2.edit_version or 1
print('  lineas traidas al asistente:', len(w3.line_ids), '| seleccionadas:', len(w3.line_ids.filtered('selected')))
imp3 = w3._i2_guarded_build()
print('  LINEAS tras guardar sin seleccion:', len(imp3.line_ids), '| repartos:', len(imp3.sv_line_ids))

print('\n--- ESCENARIO 4: reutilizacion por clave documental de un documento ANULADO ---')
sig = w3._i2_signature()
key = Imp._i2_build_documentary_key(Guia, w3.processor_id, sig)
print('  clave calculada:', key, '| ya existe doc con esa clave:', Imp.search([('documentary_key','=',key)]).mapped('name'))
print('  _i2_find_work_for_guia:', Imp._i2_find_work_for_guia(Guia).ids)
env.cr.rollback()
print('\nROLLBACK: transaccion revertida (sin cambios persistidos)')
