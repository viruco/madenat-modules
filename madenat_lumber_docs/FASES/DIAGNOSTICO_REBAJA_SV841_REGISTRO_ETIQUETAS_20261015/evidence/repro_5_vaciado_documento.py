# Transaccion revertida. No toca IMP04823/IMP02220.
Guia = env['madenat.guia.processing'].browse(1198); Imp = env['madenat.sv.imputation']; Wiz = env['madenat.sv.imputation.wizard']
SLine = env['madenat.sv.imputation.wizard.sv.line']
# Crear un documento con lineas (firma no vacia con cantidad 0)
w = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w._onchange_guia_processing_id()
for l in w.line_ids[:3]: l.selected = True
SLine.create({'wizard_id': w.id, 'wizard_line_id': w.line_ids[0].id, 'sv_lot_id': 10215, 'imputed_volume_m3': 0.0})
imp = w._i2_guarded_build()
print('creado:', imp.name, '| lineas:', len(imp.line_ids), '| clave:', imp.documentary_key)
print()
print('--- VIA A: quitar el reparto de cantidad 0 y guardar (firma pasa a vacia) ---')
w2 = Wiz.create({'guia_processing_id': 1198, 'sv_lot_id': 10215}); w2._onchange_guia_processing_id()
w2.imputation_id = imp.id; w2.expected_edit_version = imp.edit_version or 1
print('  lineas reconstruidas:', len(w2.line_ids), '| seleccionadas:', len(w2.line_ids.filtered('selected')), '| repartos asistente:', len(w2.sv_line_ids))
w2.sv_line_ids.unlink()                      # el usuario borra el destino previsto sin cantidad
w2.line_ids.write({'selected': False})       # y desmarca las etiquetas
imp2 = w2._i2_guarded_build()
print('  LINEAS tras guardar:', len(imp2.line_ids), '(documento VACIO, sigue en la seccion del SV)')
lot = env['stock.lot'].browse(10215)
print('  seccion del SV ->', lot.sv_assignment_work_imputation_ids.ids, '| contador:', lot.sv_assignment_work_count)
print('  ¿se puede anular? state:', imp2.state, '-> action_cancel exige draft/pending:', imp2.state in ('draft','pending'))
env.cr.rollback(); print('ROLLBACK (sin cambios)')
