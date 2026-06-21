# -*- coding: utf-8 -*-
"""
🔧 HELPERS COMPARTIDOS DE REPORTES — madenat_lumber_reports
==================================================================
Propósito: Centralizar la resolución de campos repetidos entre
los ecosistemas A (lumber.reception.line) y B (stock.quant)
para garantizar consistencia semántica entre Tree, PDF y XLSX.

Reglas de diseño:
- Una única fuente canónica por concepto de negocio.
- Un único helper por concepto, consumido por todos los formatos.
- Fallbacks unificados: mismo valor por defecto en todos los reportes.
- Sin dependencia circular: los helpers reciben el recordset, no lo heredan.
===================================================================
"""

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ReportHelperMixin(models.AbstractModel):
    """
    Mixin abstracto que proporciona helpers canónicos para resolución
    de campos repetidos en reportes de recepción y stock real.

    Uso:
        class LumberReceptionLineReport(models.Model):
            _inherit = ['lumber.reception.line', 'report.helper.mixin']

        class LumberStockReport(models.Model):
            _inherit = ['stock.quant', 'report.helper.mixin']
    """
    _name = 'report.helper.mixin'
    _description = 'Helpers canónicos para reportes de inventario'

    # ──────────────────────────────────────────────────────────────
    # ESTILOS XLSX (Calibri 11pt) — UNIFICADO
    # ──────────────────────────────────────────────────────────────

    def _report_xlsx_styles(self, workbook):
        """Diccionario de estilos Calibri 11pt para todos los XLSX."""
        return {
            'title': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 12, 'bold': True,
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': '#1B2A4A', 'font_color': 'white',
            }),
            'header': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': '#343a40', 'font_color': 'white',
            }),
            'patio_header': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'align': 'left', 'valign': 'vcenter', 'border': 1,
                'bg_color': '#D6E4F0', 'font_color': '#1B2A4A',
                'indent': 1,
            }),
            'data_str': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
            }),
            'data_str_alt': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'bg_color': '#F2F6FC',
            }),
            'data_num': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000',
            }),
            'data_num_alt': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000', 'bg_color': '#F2F6FC',
            }),
            'data_int': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0',
            }),
            'data_int_alt': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0', 'bg_color': '#F2F6FC',
            }),
            'footer': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'bg_color': '#E9ECEF',
            }),
            'footer_num': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000', 'bg_color': '#E9ECEF',
            }),
            'footer_int': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0', 'bg_color': '#E9ECEF',
            }),
            'grand_footer': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 2, 'align': 'center', 'valign': 'vcenter',
                'bg_color': '#343a40', 'font_color': 'white',
            }),
            'grand_footer_num': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 2, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000', 'bg_color': '#343a40',
                'font_color': 'white',
            }),
            'grand_footer_int': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 2, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0', 'bg_color': '#343a40',
                'font_color': 'white',
            }),
        }

    def _report_create_xlsx_attachment(self, workbook, output, filename):
        """Crea ir.attachment y retorna acción de descarga."""
        import base64
        workbook.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    # ──────────────────────────────────────────────────────────────
    # HELPERS CANÓNICOS — RESOLUCIÓN DE CAMPOS REPETIDOS
    # ──────────────────────────────────────────────────────────────

    def _report_get_canonical_reception_date(self, record):
        """
        Fuente canónica: lumber.reception.reception_date
        Formato: 'YYYY-MM-DD' (string)
        Fallback unificado: '' (cadena vacía)

        Acepta tanto lumber.reception.line (vía reception_id)
        como stock.quant (vía lot_id.reception_id).
        """
        reception = None
        if hasattr(record, 'reception_id') and record.reception_id:
            reception = record.reception_id
        elif hasattr(record, 'lot_id') and record.lot_id and record.lot_id.reception_id:
            reception = record.lot_id.reception_id

        if reception and reception.reception_date:
            return reception.reception_date.strftime('%Y-%m-%d')
        return ''

    def _report_get_canonical_purchase_order(self, record):
        """
        Fuente canónica: lumber.reception.purchase_order
        (campo compute que prioriza purchase_id.name > manual_po_name > 'SIN ORDEN')
        Fallback unificado: 'SIN ORDEN'

        Acepta tanto lumber.reception.line (vía reception_id)
        como stock.quant (vía lot_id → reception_id o lot_id.purchase_order_id).
        """
        # Prioridad 1: vía reception_id (ecosistema A)
        if hasattr(record, 'reception_id') and record.reception_id:
            return record.reception_id.purchase_order or _('SIN ORDEN')

        # Prioridad 2: vía lot_id.reception_id (ecosistema B)
        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.reception_id:
                return lot.reception_id.purchase_order or _('SIN ORDEN')
            # Fallback: purchase_order_id directo del lote
            if lot.purchase_order_id:
                return lot.purchase_order_id.name or _('SIN ORDEN')

        return _('SIN ORDEN')

    def _report_get_canonical_patio_label(self, record):
        """
        Fuente canónica: stock.location.name
        Fallback unificado: 'R1' (patio por defecto según estándar de negocio Madenat)

        Acepta lumber.reception.line y stock.quant.
        """
        loc = None
        # Ecosistema A: lumber.reception.line
        if hasattr(record, 'reception_id') and record.reception_id:
            if record.reception_id.location_id:
                loc = record.reception_id.location_id

        # Ecosistema B: stock.quant
        if not loc and hasattr(record, 'location_id') and record.location_id:
            loc = record.location_id

        if loc:
            return loc.name or _('R1')
        return _('R1')

    def _report_get_canonical_supplier_name(self, record):
        """
        Fuente canónica: res.partner.name vía reception_id.supplier_id
        Fallback unificado: 'Sin Proveedor'

        Acepta lumber.reception.line y stock.quant (vía lot_id).
        """
        supplier = None
        # Ecosistema A
        if hasattr(record, 'reception_id') and record.reception_id:
            supplier = record.reception_id.supplier_id
        # Ecosistema B
        elif hasattr(record, 'lot_id') and record.lot_id:
            supplier = record.lot_id.supplier_id

        if supplier and supplier.name:
            return supplier.name
        return _('Sin Proveedor')

    def _report_get_canonical_guia_number(self, record):
        """
        Fuente canónica: lumber.reception.name
        Fallback unificado: '' (cadena vacía)

        Para lotes de recepción: reception_id.name
        Para lotes de procesamiento: lot.guia_number (que deriva de guia_processing_id.name)
        """
        # Ecosistema A
        if hasattr(record, 'reception_id') and record.reception_id:
            return record.reception_id.name or ''

        # Ecosistema B
        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.reception_id:
                return lot.reception_id.name or ''
            if lot.guia_number:
                return lot.guia_number
            return ''

        return ''

    def _report_get_canonical_lot_label(self, record):
        """
        Fuente canónica: stock.lot.name (display_name)
        Fallback unificado: '' (cadena vacía)

        Acepta lumber.reception.line (vía lot_name)
        y stock.quant (vía lot_id.name).
        """
        # Ecosistema A: lumber.reception.line tiene lot_name
        if hasattr(record, 'lot_name') and record.lot_name:
            return record.lot_name.strip()

        # Ecosistema B: stock.quant tiene lot_id
        if hasattr(record, 'lot_id') and record.lot_id:
            name = record.lot_id.name or ''
            return name.strip()

        return ''

    def _report_get_canonical_product_name(self, record):
        """
        Fuente canónica: product.product.name
        Fallback unificado: 'Sin Producto'
        """
        product = None
        if hasattr(record, 'product_id') and record.product_id:
            product = record.product_id

        if product and product.name:
            return product.name
        return _('Sin Producto')

    def _report_get_canonical_subproduct_name(self, record):
        """
        Fuente canónica: madenat.subproducto.name
        Fallback unificado: 'Sin Subproducto'

        Acepta lumber.reception.line (vía subproduct_id)
        y stock.quant (vía lot_id.subproducto_id).
        """
        sub = None
        # Ecosistema A
        if hasattr(record, 'subproduct_id') and record.subproduct_id:
            sub = record.subproduct_id
        # Ecosistema B
        elif hasattr(record, 'lot_id') and record.lot_id:
            sub = record.lot_id.subproducto_id

        if sub and sub.name:
            return sub.name
        return _('Sin Subproducto')

    def _report_get_canonical_thickness(self, record):
        """
        Fuente canónica: thickness_visual (Char) del modelo de origen
        Fallback unificado: '' (cadena vacía)

        Acepta lumber.reception.line y stock.quant (vía lot_id).
        """
        if hasattr(record, 'thickness_visual') and record.thickness_visual:
            return record.thickness_visual

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.thickness_visual:
                return lot.thickness_visual

        return ''

    def _report_get_canonical_width(self, record):
        """
        Fuente canónica: width_visual (Char) del modelo de origen
        Fallback unificado: '' (cadena vacía)
        """
        if hasattr(record, 'width_visual') and record.width_visual:
            return record.width_visual

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.width_visual:
                return lot.width_visual

        return ''

    def _report_get_canonical_length(self, record):
        """
        Fuente canónica: length (Float) del modelo de origen
        Fallback unificado: 0.0

        Acepta lumber.reception.line (length)
        y stock.quant (vía lot_id.largo_m).
        """
        if hasattr(record, 'length') and record.length:
            return record.length

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.largo_m:
                return lot.largo_m

        return 0.0

    def _report_get_canonical_pieces(self, record):
        """
        Fuente canónica: pieces (Integer) del modelo de origen
        Fallback unificado: 0

        Acepta lumber.reception.line (pieces)
        y stock.quant (vía lot_id.piezas).
        """
        if hasattr(record, 'pieces') and record.pieces:
            return record.pieces

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.piezas:
                return lot.piezas

        return 0

    def _report_get_canonical_volume_m3(self, record):
        """
        Fuente canónica por ecosistema, resuelta por tipo de modelo:
        - Ecosistema A (lumber.reception.line): vol_physical_m3 (cálculo físico mm×mm×m)
        - Ecosistema B (stock.quant): lot_id.volumen_m3 (volumen del lote en stock real)
        Fallback unificado: 0.0
        """
        # Ecosistema A: lumber.reception.line → vol_physical_m3
        if record._name == 'lumber.reception.line':
            return record.vol_physical_m3 if record.vol_physical_m3 else 0.0

        # Ecosistema B: stock.quant → lot_id.volumen_m3
        if record._name == 'stock.quant':
            lot = record.lot_id
            if lot and lot.volumen_m3:
                return lot.volumen_m3
            return 0.0

        # Fallback genérico: intentar atributos directos o vía lote
        if hasattr(record, 'vol_physical_m3') and record.vol_physical_m3:
            return record.vol_physical_m3

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.volumen_m3:
                return lot.volumen_m3

        return 0.0

    def _report_get_canonical_mbf(self, record):
        """
        Fuente canónica por ecosistema, resuelta por tipo de modelo:
        - Ecosistema A (lumber.reception.line): vol_mbf (fórmula geométrica de exportación)
        - Ecosistema B (stock.quant): lot_id.volumen_mbf (conversión aproximada m³/2.36)
        Fallback unificado: 0.0
        """
        # Ecosistema A: lumber.reception.line → vol_mbf
        if record._name == 'lumber.reception.line':
            return record.vol_mbf if record.vol_mbf else 0.0

        # Ecosistema B: stock.quant → lot_id.volumen_mbf
        if record._name == 'stock.quant':
            lot = record.lot_id
            if lot and lot.volumen_mbf:
                return lot.volumen_mbf
            return 0.0

        # Fallback genérico
        if hasattr(record, 'vol_mbf') and record.vol_mbf:
            return record.vol_mbf

        if hasattr(record, 'lot_id') and record.lot_id:
            lot = record.lot_id
            if lot.volumen_mbf:
                return lot.volumen_mbf

        return 0.0

    def _report_get_canonical_container_name(self, lot):
        """
        Busca el contenedor asociado al lote.
        Fuente: lumber.container
        Fallback: '' (cadena vacía)
        """
        if not lot:
            return ''
        try:
            container = self.env['lumber.container'].sudo().search(
                [('lot_ids', 'in', lot.id)], limit=1
            )
            return container.name if container else ''
        except Exception:
            return ''

    # ──────────────────────────────────────────────────────────────
    # HELPERS COMPUESTOS — DICCIONARIO DE FILA COMPLETA
    # ──────────────────────────────────────────────────────────────

    def _report_build_detail_row(self, record, include_oc=False):
        """
        Construye un diccionario con todos los campos de una fila de detalle,
        resueltos desde las fuentes canónicas.

        Args:
            record: lumber.reception.line o stock.quant
            include_oc: si es True, incluye 'oc' en el diccionario

        Returns:
            dict con claves: patio, proveedor, guia, fecha_recepcion,
            producto, subproducto, espesor, ancho, largo, piezas, m3, mbf
            (y opcionalmente 'oc')
        """
        row = {
            'patio': self._report_get_canonical_patio_label(record),
            'proveedor': self._report_get_canonical_supplier_name(record),
            'guia': self._report_get_canonical_guia_number(record),
            'fecha_recepcion': self._report_get_canonical_reception_date(record),
            'producto': self._report_get_canonical_product_name(record),
            'subproducto': self._report_get_canonical_subproduct_name(record),
            'espesor': self._report_get_canonical_thickness(record),
            'ancho': self._report_get_canonical_width(record),
            'largo': self._report_get_canonical_length(record),
            'piezas': self._report_get_canonical_pieces(record),
            'm3': self._report_get_canonical_volume_m3(record),
            'mbf': self._report_get_canonical_mbf(record),
        }
        if include_oc:
            row['oc'] = self._report_get_canonical_purchase_order(record)
        return row

    def _report_build_r9_structure(self, records, include_oc=False):
        """
        Construye la estructura de agrupación para R9 (Detalle por Producto).

        Agrupa por (producto, subproducto), manteniendo el orden de aparición,
        y calcula subtotales por grupo.

        Args:
            records: recordset de lumber.reception.line o stock.quant
            include_oc: si es True, incluye 'oc' en cada fila

        Returns:
            dict con claves:
            - 'order': lista de tuplas (prod, sub) en orden
            - 'groups': dict {(prod, sub): {'rows': [...], 'tot_p': int, 'tot_m3': float, 'tot_mbf': float}}
        """
        agg = {}
        order = []
        for rec in records:
            row = self._report_build_detail_row(rec, include_oc=include_oc)
            prod = row['producto']
            sub = row['subproducto']
            key = (prod, sub)
            if key not in agg:
                agg[key] = {'rows': [], 'tot_p': 0, 'tot_m3': 0.0, 'tot_mbf': 0.0}
                order.append(key)
            agg[key]['rows'].append(row)
            agg[key]['tot_p'] += row['piezas']
            agg[key]['tot_m3'] += row['m3']
            agg[key]['tot_mbf'] += row['mbf']
        return {'order': order, 'groups': agg}

    def _report_write_r9_xlsx_body(self, sheet, sty, structure, start_row=2):
        """
        Escribe el cuerpo XLSX de R9 (agrupado por producto/subproducto)
        usando la estructura generada por _report_build_r9_structure.

        Args:
            sheet: worksheet de xlsxwriter
            sty: diccionario de estilos
            structure: dict retornado por _report_build_r9_structure
            start_row: fila inicial (0-based)

        Returns:
            tuple (row, grand_p, grand_m3, grand_mbf)
        """
        row = start_row
        grand_p, grand_m3, grand_mbf = 0, 0.0, 0.0
        order = structure['order']
        agg = structure['groups']
        num_cols = 12  # columnas fijas de R9

        for i, (prod, sub) in enumerate(order):
            group = agg[(prod, sub)]

            # Fila de grupo (cabecera de producto)
            sheet.merge_range(row, 0, row, num_cols - 1,
                              f'{prod} — {sub}', sty['header'])
            row += 1

            for data in group['rows']:
                sheet.write(row, 0, prod, sty['data_str'])
                sheet.write(row, 1, sub, sty['data_str'])
                sheet.write(row, 2, data['patio'], sty['data_str'])
                sheet.write(row, 3, data['proveedor'], sty['data_str'])
                sheet.write(row, 4, data['guia'], sty['data_str'])
                sheet.write(row, 5, data['fecha_recepcion'], sty['data_str'])
                sheet.write(row, 6, data['espesor'], sty['data_str'])
                sheet.write(row, 7, data['ancho'], sty['data_str'])
                sheet.write(row, 8, data['largo'], sty['data_num'])
                sheet.write(row, 9, data['piezas'], sty['data_int'])
                sheet.write(row, 10, data['m3'], sty['data_num'])
                sheet.write(row, 11, data['mbf'], sty['data_num'])
                row += 1

            # Subtotales del grupo
            sheet.write(row, 0, f'SUB {prod}', sty['footer'])
            for c in range(1, 9):
                sheet.write(row, c, '', sty['footer'])
            sheet.write(row, 9, group['tot_p'], sty['footer_int'])
            sheet.write(row, 10, group['tot_m3'], sty['footer_num'])
            sheet.write(row, 11, group['tot_mbf'], sty['footer_num'])
            grand_p += group['tot_p']
            grand_m3 += group['tot_m3']
            grand_mbf += group['tot_mbf']
            row += 1

            # Línea vacía entre grupos
            if i < len(order) - 1:
                row += 1

        return row, grand_p, grand_m3, grand_mbf