# Prueba funcional con odoo shell sobre madenat_test con rollback garantizado

# 1. Caso 40030 (con fila de totales sin etiqueta)
w20556 = env['madenat.lumber.intake.wizard'].browse(20556)
print(f"=== WIZARD 20556 BASE ===")
print(f"Archivos: excel={w20556.excel_filename}, pdf={w20556.pdf_filename}")
print(f"Historico pre-2E: line_count={w20556.preview_line_count}, total_volume={w20556.preview_total_volume_m3}")

w_temp = env['madenat.lumber.intake.wizard'].create({
    'intake_modality': 'normal',
    'tipo_ingreso': 'producto',
    'excel_file': w20556.excel_file,
    'excel_filename': w20556.excel_filename,
    'pdf_file': w20556.pdf_file,
    'pdf_filename': w20556.pdf_filename,
})

# Boton «Leer documento» invoca action_preview_document()
w_temp.action_preview_document()

print(f"\n=== WIZARD TEMPORAL 40030 POST-DESPLIEGUE ===")
print(f"preview_line_count: {w_temp.preview_line_count}")
print(f"preview_total_volume_m3: {w_temp.preview_total_volume_m3}")
print("preview_warnings:")
print(w_temp.preview_warnings)

# 2. Caso 95083 (sin fila de cierre)
w3884 = env['madenat.lumber.intake.wizard'].browse(3884)
print(f"\n=== WIZARD 3884 BASE (95083) ===")
print(f"Archivos: excel={w3884.excel_filename}, pdf={w3884.pdf_filename}")

w_temp2 = env['madenat.lumber.intake.wizard'].create({
    'intake_modality': 'normal',
    'tipo_ingreso': 'procesado',
    'excel_file': w3884.excel_file,
    'excel_filename': w3884.excel_filename,
    'pdf_file': w3884.pdf_file,
    'pdf_filename': w3884.pdf_filename,
})

w_temp2.action_preview_document()

print(f"\n=== WIZARD TEMPORAL 95083 POST-DESPLIEGUE ===")
print(f"preview_line_count: {w_temp2.preview_line_count}")
print(f"preview_total_volume_m3: {w_temp2.preview_total_volume_m3}")
print("preview_warnings:")
print(w_temp2.preview_warnings)

# 3. Rollback garantizado
env.cr.rollback()
print("\n>>> env.cr.rollback() EJECUTADO EXITOSAMENTE. NINGUN CAMBIO PERSISTIDO. <<<")
