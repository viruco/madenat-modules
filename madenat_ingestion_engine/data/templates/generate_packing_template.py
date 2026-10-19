# -*- coding: utf-8 -*-
"""Generador de la plantilla estándar PACKING_ESTANDAR_MADENAT (Forestal Andes) para MADENAT.

Crea un archivo Excel .xlsx profesional, con cabecera de metadatos, columnas
homologadas según el formato de Forestal Andes, listas desplegables (validación
de datos para producto, subproducto y perfil), formato numérico de 3 decimales
para volumen, ejemplos prácticos (Arauco, JCE con dimensiones separadas, BYC, Fátima)
y pestaña de guía de llenado.
"""
import os
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


def generate_standard_madenat_template(output_path):
    wb = openpyxl.Workbook()

    # ══════════════════════════════════════════════════════════════════════
    # HOJA 1: PACKING LIST
    # ══════════════════════════════════════════════════════════════════════
    ws = wb.active
    ws.title = "PACKING LIST"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    title_font = Font(name="Calibri", size=14, bold=True, color="1F497D")
    meta_label_font = Font(name="Calibri", size=10, bold=True, color="595959")
    meta_val_font = Font(name="Calibri", size=10, color="000000")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    example_font = Font(name="Calibri", size=10, italic=True, color="333333")

    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    example_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    header_border = Border(
        left=Side(style="thin", color="FFFFFF"),
        right=Side(style="thin", color="FFFFFF"),
        top=Side(style="medium", color="16365C"),
        bottom=Side(style="medium", color="16365C"),
    )

    # Fila 1: Título
    ws.merge_cells("A1:M1")
    title_cell = ws["A1"]
    title_cell.value = "MADENAT — PACKING ESTÁNDAR (FORMATO FORESTAL ANDES)"
    title_cell.font = title_font
    title_cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 28

    # Fila 2: Metadatos del documento (reconocidos por _extract_excel_header)
    metadata = [
        ("A2", "CLIENTE", "B2", "MADENAT S.A."),
        ("D2", "GUIA DESPACHO", "E2", "40030"),
        ("G2", "FECHA", "H2", "2026-10-19"),
        ("J2", "ORDEN COMPRA", "K2", "OC-2026-001"),
        ("L2", "PROVEEDOR", "M2", "FORESTAL ANDES S.A."),
    ]
    for lbl_cell, lbl_val, val_cell, val_val in metadata:
        ws[lbl_cell] = lbl_val
        ws[lbl_cell].font = meta_label_font
        ws[lbl_cell].alignment = Alignment(horizontal="right", vertical="center")
        ws[val_cell] = val_val
        ws[val_cell].font = meta_val_font
        ws[val_cell].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 20

    # Fila 4: Encabezados de columnas (basadas en Forestal Andes / packing_metrico_aserrada)
    headers = [
        ("N°", "Número correlativo de tarja o paquete"),
        ("CODIGO", "Código de producto / SKU"),
        ("PRODUCTO", "Descripción comercial de la madera"),
        ("SUBPRODUCTO", "Subproducto / Calidad / Grado"),
        ("LOTE", "Identificador de lote o etiqueta de origen"),
        ("ESPESOR", "Espesor nominal en milímetros (mm)"),
        ("ANCHO", "Ancho nominal en milímetros (mm)"),
        ("LARGO", "Largo nominal en metros (m)"),
        ("FILAS", "Capas verticales en el paquete"),
        ("COLUMNAS", "Piezas por capa a lo ancho"),
        ("PIEZAS", "Total de piezas en el paquete"),
        ("VOLUMEN", "Volumen total en metros cúbicos (m³ a 3 decimales)"),
        ("PERFIL", "Perfil de cálculo o ingesta"),
    ]

    for col_idx, (col_name, col_desc) in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = header_border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[4].height = 26

    # Listas Desplegables (DataValidation)
    dv_producto = DataValidation(
        type="list",
        formula1='"PINO ASERRADO SECO KD,PINO ASERRADO VERDE,PINO CEPILLADO,BLANKS CLEAR"',
        allow_blank=True,
    )
    dv_subproducto = DataValidation(
        type="list",
        formula1='"CLEAR,COL,INDUSTRIAL,MILL RUN,SELECTO,ESTANDAR"',
        allow_blank=True,
    )
    dv_perfil = DataValidation(
        type="list",
        formula1='"packing_metrico_aserrada,f1550,f5085,blanks,metric"',
        allow_blank=True,
    )

    ws.add_data_validation(dv_producto)
    ws.add_data_validation(dv_subproducto)
    ws.add_data_validation(dv_perfil)

    dv_producto.add("C5:C500")
    dv_subproducto.add("D5:D500")
    dv_perfil.add("M5:M500")

    # Filas 5 a 8: Datos de ejemplo representativos de los 4 orígenes
    # 1. Forestal Andes: 38.1 x 170.0 x 4.05 m, 150 pzas -> 3.886 m3
    # 2. Arauco (sintético): 25.0 x 150.0 x 3.60 m, 120 pzas -> 1.620 m3
    # 3. JCE (sintético, dimensiones separadas): 45.0 x 125.0 x 3.60 m, 160 pzas -> 3.240 m3
    # 4. BYC / Fátima (sintético): 50.0 x 150.0 x 4.00 m, 90 pzas -> 2.700 m3
    sample_rows = [
        [1, "1000203040501", "PINO ASERRADO SECO KD", "CLEAR", "ETQ-ANDES-001", 38.1, 170.0, 4.05, 25, 6, 150, 3.886, "packing_metrico_aserrada"],
        [2, "1000203040502", "PINO ASERRADO VERDE", "INDUSTRIAL", "ETQ-ARAUCO-002", 25.0, 150.0, 3.60, 20, 6, 120, 1.620, "packing_metrico_aserrada"],
        [3, "1000203040503", "PINO ASERRADO SECO KD", "COL", "ETQ-JCE-003", 45.0, 125.0, 3.60, 20, 8, 160, 3.240, "packing_metrico_aserrada"],
        [4, "1000203040504", "PINO CEPILLADO", "MILL RUN", "ETQ-BYC-004", 50.0, 150.0, 4.00, 15, 6, 90, 2.700, "packing_metrico_aserrada"],
    ]

    for row_idx, row_data in enumerate(sample_rows, start=5):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = example_font
            cell.fill = example_fill
            cell.border = thin_border
            # Formatos de celda
            if col_idx in (1, 9, 10, 11):
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.number_format = "#,##0"
            elif col_idx in (2, 4, 5, 13):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 3:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_idx in (6, 7):
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "#,##0.0"
            elif col_idx == 8:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.00"
            elif col_idx == 12:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.000"
        ws.row_dimensions[row_idx].height = 20

    # Autoajuste de anchos de columna
    col_widths = {
        1: 8,    # N°
        2: 18,   # CODIGO
        3: 28,   # PRODUCTO
        4: 16,   # SUBPRODUCTO
        5: 18,   # LOTE
        6: 14,   # ESPESOR
        7: 14,   # ANCHO
        8: 12,   # LARGO
        9: 10,   # FILAS
        10: 12,  # COLUMNAS
        11: 12,  # PIEZAS
        12: 16,  # VOLUMEN
        13: 24,  # PERFIL
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # ══════════════════════════════════════════════════════════════════════
    # HOJA 2: INSTRUCCIONES DE LLENADO
    # ══════════════════════════════════════════════════════════════════════
    ws_info = wb.create_sheet(title="INSTRUCCIONES DE LLENADO")
    ws_info.views.sheetView[0].showGridLines = True

    info_title_cell = ws_info["A1"]
    info_title_cell.value = "GUÍA DE LLENADO — PACKING ESTÁNDAR MADENAT (FORESTAL ANDES)"
    info_title_cell.font = title_font

    instrucciones = [
        ("", ""),
        ("REGLAS GENERALES Y DECISIÓN DE OPERACIONES:", ""),
        ("1. Formato Único", "Por decisión de Operaciones (respuesta Cristhian 8-oct), no se siguen adaptando lectores individuales para Arauco, JCE, BYC ni Fátima. Todos los proveedores deben ingresar a través de este Packing Estándar MADENAT."),
        ("2. Dimensiones Separadas", "El espesor debe venir en mm (columna ESPESOR), el ancho en mm (columna ANCHO) y el largo en metros (columna LARGO). JCE y Arauco deben desglosar escuadrías compuestas en estas 3 columnas."),
        ("3. Precisión de Volumen", "El packing manda sobre la guía. Si la guía viene con 2 decimales, el packing se redondea rigurosamente a 3 decimales (ej: 57,839556 m³ → 57,840 m³)."),
        ("4. Listas Desplegables", "Utilice las opciones de las listas desplegables en PRODUCTO, SUBPRODUCTO y PERFIL para garantizar homologación directa en el inventario."),
        ("5. Trazabilidad de Tarjas", "Cada fila representa un paquete/tarja físico. El campo 'LOTE' preserva la etiqueta del proveedor de origen."),
        ("", ""),
        ("COLUMNA", "DESCRIPCIÓN Y VALORES VÁLIDOS"),
        ("N°", "Número correlativo de tarja (Ej: 1, 2, 3...)"),
        ("CODIGO", "Código SKU o referencia del producto (Ej: 1000203040501)"),
        ("PRODUCTO", "Seleccione de la lista: PINO ASERRADO SECO KD, PINO ASERRADO VERDE, PINO CEPILLADO, BLANKS CLEAR"),
        ("SUBPRODUCTO", "Seleccione de la lista: CLEAR, COL, INDUSTRIAL, MILL RUN, SELECTO, ESTANDAR"),
        ("LOTE", "Identificador único de la etiqueta o paquete (Ej: ETQ-001)"),
        ("ESPESOR", "Espesor nominal en mm (Ej: 25.0, 38.1, 45.0, 50.0)"),
        ("ANCHO", "Ancho nominal en mm (Ej: 100.0, 125.0, 150.0, 170.0)"),
        ("LARGO", "Largo nominal en metros (Ej: 3.20, 3.60, 4.00, 4.05)"),
        ("FILAS", "Capas verticales de madera en el paquete (Ej: 20, 25)"),
        ("COLUMNAS", "Piezas por capa a lo ancho (Ej: 6, 8)"),
        ("PIEZAS", "Total de piezas en el paquete (Ej: 120, 150, 160)"),
        ("VOLUMEN", "Volumen en m³ calculado a 3 decimales (Ej: 3.886)"),
        ("PERFIL", "Seleccione: packing_metrico_aserrada (estándar), f1550, f5085, blanks, metric"),
    ]

    for row_idx, (col1, col2) in enumerate(instrucciones, start=2):
        c1 = ws_info.cell(row=row_idx, column=1, value=col1)
        c2 = ws_info.cell(row=row_idx, column=2, value=col2)
        if "REGLAS" in col1 or col1 == "COLUMNA":
            c1.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
            c2.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
        else:
            c1.font = Font(name="Calibri", size=10, bold=bool(col1 and not col1.startswith("1.")), color="000000")
            c2.font = Font(name="Calibri", size=10, color="333333")

    ws_info.column_dimensions["A"].width = 24
    ws_info.column_dimensions["B"].width = 95

    wb.save(output_path)
    print(f"Plantilla estándar MADENAT generada exitosamente en: {output_path}")


def generate_template(output_path):
    """Genera la plantilla métrica original (PACKING_METRICO_ASERRADA)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PACKING LIST"
    ws.views.sheetView[0].showGridLines = True

    title_font = Font(name="Calibri", size=14, bold=True, color="1F497D")
    meta_label_font = Font(name="Calibri", size=10, bold=True, color="595959")
    meta_val_font = Font(name="Calibri", size=10, color="000000")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    example_font = Font(name="Calibri", size=10, italic=True, color="333333")

    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    example_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    header_border = Border(
        left=Side(style="thin", color="FFFFFF"),
        right=Side(style="thin", color="FFFFFF"),
        top=Side(style="medium", color="16365C"),
        bottom=Side(style="medium", color="16365C"),
    )

    ws.merge_cells("A1:K1")
    title_cell = ws["A1"]
    title_cell.value = "MADENAT — PLANTILLA ESTÁNDAR DE PACKING LIST (SISTEMA MÉTRICO)"
    title_cell.font = title_font
    title_cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 28

    metadata = [
        ("A2", "CLIENTE", "B2", "MADENAT S.A."),
        ("D2", "GUIA DESPACHO", "E2", "12345"),
        ("G2", "FECHA", "H2", "2026-10-17"),
        ("J2", "ORDEN COMPRA", "K2", "OC-2026-001"),
    ]
    for lbl_cell, lbl_val, val_cell, val_val in metadata:
        ws[lbl_cell] = lbl_val
        ws[lbl_cell].font = meta_label_font
        ws[lbl_cell].alignment = Alignment(horizontal="right", vertical="center")
        ws[val_cell] = val_val
        ws[val_cell].font = meta_val_font
        ws[val_cell].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 20

    headers = [
        ("N°", "Número de paquete / tarja correlativo"),
        ("CODIGO", "Código de producto (SKU o código de barras)"),
        ("PRODUCTO", "Descripción comercial o técnica de la madera"),
        ("LOTE", "Identificador del lote o etiqueta de origen"),
        ("ESPESOR", "Espesor nominal en milímetros (mm)"),
        ("ANCHO", "Ancho nominal en milímetros (mm)"),
        ("LARGO", "Largo nominal en metros (m)"),
        ("FILAS", "Número de filas de piezas en el paquete"),
        ("COLUMNAS", "Número de columnas de piezas en el paquete"),
        ("PIEZAS", "Total de piezas por paquete"),
        ("VOLUMEN", "Volumen total del paquete en metros cúbicos (m³)"),
    ]

    for col_idx, (col_name, col_desc) in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = header_border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[4].height = 26

    sample_rows = [
        [1, "1000203040501", "PINO ASERRADO SECO KD", "ETQ-001", 38.1, 170.0, 4.05, 25, 6, 150, 3.886],
        [2, "1000203040502", "PINO ASERRADO SECO KD", "ETQ-002", 45.0, 125.0, 3.60, 20, 8, 160, 3.240],
        [3, "1000203040503", "PINO ASERRADO VERDE", "ETQ-003", 25.0, 150.0, 3.60, 20, 6, 120, 1.620],
        [4, "1000203040504", "PINO ASERRADO VERDE", "ETQ-004", 50.0, 150.0, 4.00, 15, 6, 90, 2.700],
    ]

    for row_idx, row_data in enumerate(sample_rows, start=5):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = example_font
            cell.fill = example_fill
            cell.border = thin_border
            if col_idx in (1, 8, 9, 10):
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.number_format = "#,##0"
            elif col_idx in (2, 4):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 3:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_idx in (5, 6):
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "#,##0.0"
            elif col_idx == 7:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.00"
            elif col_idx == 11:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.000"
        ws.row_dimensions[row_idx].height = 20

    col_widths = {
        1: 8, 2: 18, 3: 28, 4: 16, 5: 14, 6: 14, 7: 12, 8: 10, 9: 12, 10: 12, 11: 16,
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws_info = wb.create_sheet(title="INSTRUCCIONES DE LLENADO")
    ws_info.views.sheetView[0].showGridLines = True
    info_title_cell = ws_info["A1"]
    info_title_cell.value = "GUÍA DE LLENADO — SISTEMA DE INGESTA MADENAT (MÉTRICO)"
    info_title_cell.font = title_font

    instrucciones = [
        ("", ""),
        ("REGLAS GENERALES:", ""),
        ("1. Unidades", "El sistema métrico aserrada asume Espesor en mm, Ancho en mm y Largo en metros (m)."),
        ("2. Volumen", "El volumen debe indicarse en metros cúbicos (m³). Fórmula típica: Espesor(mm)/1000 * Ancho(mm)/1000 * Largo(m) * Piezas."),
        ("3. Paquetes / Lotes", "Cada fila representa un paquete físico (tarja). 'N°' identifica el paquete correlativo y 'LOTE' la etiqueta única del proveedor."),
        ("4. Piezas", "Debe coincidir con Filas * Columnas cuando el paquete sea regular, o con el recuento manual de piezas."),
        ("5. Código / SKU", "Código de producto numérico o alfanumérico que identifica la escuadría y terminación."),
        ("", ""),
        ("COLUMNA", "DESCRIPCIÓN Y EJEMPLO"),
        ("N°", "Identificador correlativo del paquete (Ej: 1, 2, 3...)"),
        ("CODIGO", "Código de escuadría o SKU (Ej: 1000203040501)"),
        ("PRODUCTO", "Nombre descriptivo de la madera (Ej: PINO ASERRADO SECO KD)"),
        ("LOTE", "Número de etiqueta o lote asignado por el aserradero (Ej: ETQ-001)"),
        ("ESPESOR", "Espesor en milímetros. Rango típico métrico: >= 10 mm (Ej: 38.1, 45, 50)"),
        ("ANCHO", "Ancho en milímetros (Ej: 125, 150, 170)"),
        ("LARGO", "Largo nominal en metros (Ej: 3.60, 4.00, 4.05)"),
        ("FILAS", "Capas verticales de madera en el paquete (Ej: 20, 25)"),
        ("COLUMNAS", "Piezas por capa a lo ancho (Ej: 6, 8)"),
        ("PIEZAS", "Número total de piezas contenidas en el paquete (Ej: 150)"),
        ("VOLUMEN", "Volumen cúbico total del paquete en m³ (Ej: 3.886)"),
    ]

    for row_idx, (col1, col2) in enumerate(instrucciones, start=2):
        c1 = ws_info.cell(row=row_idx, column=1, value=col1)
        c2 = ws_info.cell(row=row_idx, column=2, value=col2)
        if "REGLAS" in col1 or col1 == "COLUMNA":
            c1.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
            c2.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
        else:
            c1.font = Font(name="Calibri", size=10, bold=bool(col1 and not col1.startswith("1.")), color="000000")
            c2.font = Font(name="Calibri", size=10, color="333333")

    ws_info.column_dimensions["A"].width = 24
    ws_info.column_dimensions["B"].width = 85

    wb.save(output_path)
    print(f"Plantilla generada exitosamente en: {output_path}")


if __name__ == "__main__":
    dir_path = os.path.dirname(__file__)
    out_std = os.path.join(dir_path, "PLANTILLA_PACKING_ESTANDAR_MADENAT.xlsx")
    generate_standard_madenat_template(out_std)

    out_legacy = os.path.join(dir_path, "PLANTILLA_PACKING_METRICO_ASERRADA.xlsx")
    generate_template(out_legacy)

