# -*- coding: utf-8 -*-
"""
8 Reportes de Inventario Recepción — XLSX + PDF
Hereda de lumber.reception.line para agregar métodos de exportación.
"""

import io
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LumberReceptionLineReport(models.Model):
    _inherit = 'lumber.reception.line'

    # ──────────────────────────────────────────────
    # CAMPOS RELATED para group_by en vistas
    # ──────────────────────────────────────────────
    location_id = fields.Many2one(
        'stock.location', string='Patio',
        related='reception_id.location_id',
        store=True, readonly=True, index=True,
    )
    complete_location_name = fields.Char(
        string='Ubicación Técnica',
        related='location_id.complete_name',
        store=True, readonly=True,
        help="Nombre jerárquico completo de la ubicación (ej: WH/Stock/Bodega Tepornac)"
    )
    patio_label = fields.Char(
        string='Patio',
        compute='_compute_patio_label',
        store=True, readonly=True, index=True,
        help="Etiqueta de negocio para agrupación: nombre técnico de la ubicación o 'R1' cuando no está asignada."
    )
    partner_id = fields.Many2one(
        'res.partner', string='Proveedor',
        related='reception_id.supplier_id',
        store=True, readonly=True, index=True,
    )
    partner_name = fields.Char(
        string='Proveedor',
        compute='_compute_partner_name',
        store=True, readonly=True, index=True,
        help="Nombre del proveedor. 'Sin Proveedor' si no está asignado."
    )
    purchase_id = fields.Many2one(
        'purchase.order', string='Orden de Compra',
        related='reception_id.purchase_id',
        store=True, readonly=True, index=True,
    )
    subproduct_name = fields.Char(
        string='Subproducto',
        compute='_compute_subproduct_name',
        store=True, readonly=True, index=True,
        help="Nombre del subproducto. 'Sin Subproducto' si no está asignado."
    )

    @api.depends('subproduct_id', 'subproduct_id.name')
    def _compute_subproduct_name(self):
        for line in self:
            if line.subproduct_id and line.subproduct_id.name:
                line.subproduct_name = line.subproduct_id.name
            else:
                line.subproduct_name = _('Sin Subproducto')

    @api.depends('reception_id.supplier_id', 'reception_id.supplier_id.name')
    def _compute_partner_name(self):
        for line in self:
            supplier = line.reception_id.supplier_id
            if supplier and supplier.name:
                line.partner_name = supplier.name
            else:
                line.partner_name = _('Sin Proveedor')

    @api.depends('location_id', 'complete_location_name')
    def _compute_patio_label(self):
        for line in self:
            loc = line.location_id
            if loc:
                line.patio_label = loc.name or loc.complete_name
            else:
                line.patio_label = _('R1')

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def _get_location_name(self):
        """Patio vía reception_id.location_id"""
        self.ensure_one()
        if self.reception_id.location_id:
            return self.reception_id.location_id.name
        return ''

    def _get_subproduct_name(self):
        """Subproducto desde subproduct_id (madenat.subproducto)"""
        self.ensure_one()
        if self.subproduct_id:
            return self.subproduct_id.name
        return ''

    # ──────────────────────────────────────────────
    # ESTILOS XLSX (Calibri 11pt)
    # ──────────────────────────────────────────────

    def _xlsx_styles(self, workbook):
        return {
            'title': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'align': 'center', 'valign': 'vcenter', 'border': 1,
            }),
            'header': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': '#343a40', 'font_color': 'white',
            }),
            'data_str': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
            }),
            'data_num': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000',
            }),
            'data_int': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0',
            }),
            'footer': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
            }),
            'footer_num': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.000',
            }),
            'footer_int': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 11, 'bold': True,
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '0',
            }),
        }

    def _create_xlsx_attachment(self, workbook, output, filename):
        """Crea ir.attachment y retorna acción de descarga"""
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

    # ──────────────────────────────────────────────
    # R1 — DETALLE POR PATIO — TODOS PRODUCTOS
    # ──────────────────────────────────────────────

    def action_export_r1_detail_location_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R1_Detalle_Patio')
        sty = self._xlsx_styles(workbook)

        # Anchura columnas
        widths = [20, 25, 18, 12, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        # Cabecera
        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R1 — Detalle por Patio — Todos Productos', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces = 0
        tot_m3 = 0.0
        tot_mbf = 0.0
        for line in self:
            loc = line.patio_label or ''
            provider = line.partner_name or ''
            guide = line.reception_id.name or ''
            date = line.reception_id.reception_date.strftime('%Y-%m-%d') if line.reception_id.reception_date else ''
            product = line.product_id.name or ''
            sub = line.subproduct_id.name or ''
            thick = line.thickness_visual or ''
            width = line.width_visual or ''
            length = line.length or 0
            pieces = line.pieces or 0
            m3 = line.vol_physical_m3 or 0.0
            mbf = line.vol_mbf or 0.0

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, provider, sty['data_str'])
            sheet.write(row, 2, guide, sty['data_str'])
            sheet.write(row, 3, date, sty['data_str'])
            sheet.write(row, 4, product, sty['data_str'])
            sheet.write(row, 5, sub, sty['data_str'])
            sheet.write(row, 6, thick, sty['data_str'])
            sheet.write(row, 7, width, sty['data_str'])
            sheet.write(row, 8, length, sty['data_num'])
            sheet.write(row, 9, pieces, sty['data_int'])
            sheet.write(row, 10, m3, sty['data_num'])
            sheet.write(row, 11, mbf, sty['data_num'])

            tot_pieces += pieces
            tot_m3 += m3
            tot_mbf += mbf
            row += 1

        # Totales
        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, tot_pieces, sty['footer_int'])
        sheet.write(row, 10, tot_m3, sty['footer_num'])
        sheet.write(row, 11, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R1_Detalle_Patio.xlsx')

    # ──────────────────────────────────────────────
    # R2 — RESUMEN POR PATIO — TODOS PRODUCTOS
    # ──────────────────────────────────────────────

    def action_export_r2_summary_location_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R2_Resumen_Patio')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R2 — Resumen por Patio — Todos Productos', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # Agrupación
        agg = {}
        for line in self:
            loc = line.patio_label or 'Sin Patio'
            prod = line.product_id.name or 'Sin Producto'
            sub = line.subproduct_id.name or 'Sin Subproducto'
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += (line.pieces or 0)
            agg[key]['m3'] += (line.vol_physical_m3 or 0.0)
            agg[key]['mbf'] += (line.vol_mbf or 0.0)

        row = 2
        tot_p, tot_m3, tot_mbf = 0, 0.0, 0.0
        for (loc, prod, sub), vals in sorted(agg.items()):
            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, prod, sty['data_str'])
            sheet.write(row, 2, sub, sty['data_str'])
            sheet.write(row, 3, vals['pieces'], sty['data_int'])
            sheet.write(row, 4, vals['m3'], sty['data_num'])
            sheet.write(row, 5, vals['mbf'], sty['data_num'])
            tot_p += vals['pieces']
            tot_m3 += vals['m3']
            tot_mbf += vals['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        sheet.write(row, 1, '', sty['footer'])
        sheet.write(row, 2, '', sty['footer'])
        sheet.write(row, 3, tot_p, sty['footer_int'])
        sheet.write(row, 4, tot_m3, sty['footer_num'])
        sheet.write(row, 5, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R2_Resumen_Patio.xlsx')

    # ──────────────────────────────────────────────
    # R3 — DETALLE POR PATIO — TIPO PRODUCTO
    # ──────────────────────────────────────────────

    def action_export_r3_detail_location_sub_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R3_Detalle_Patio_Subprod')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 18, 12, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R3 — Detalle por Patio — Tipo Producto', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces = 0
        tot_m3 = 0.0
        tot_mbf = 0.0
        for line in self:
            loc = line.patio_label or ''
            provider = line.partner_name or ''
            guide = line.reception_id.name or ''
            date = line.reception_id.reception_date.strftime('%Y-%m-%d') if line.reception_id.reception_date else ''
            product = line.product_id.name or ''
            sub = line.subproduct_id.name or ''
            thick = line.thickness_visual or ''
            width = line.width_visual or ''
            length = line.length or 0
            pieces = line.pieces or 0
            m3 = line.vol_physical_m3 or 0.0
            mbf = line.vol_mbf or 0.0

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, provider, sty['data_str'])
            sheet.write(row, 2, guide, sty['data_str'])
            sheet.write(row, 3, date, sty['data_str'])
            sheet.write(row, 4, product, sty['data_str'])
            sheet.write(row, 5, sub, sty['data_str'])
            sheet.write(row, 6, thick, sty['data_str'])
            sheet.write(row, 7, width, sty['data_str'])
            sheet.write(row, 8, length, sty['data_num'])
            sheet.write(row, 9, pieces, sty['data_int'])
            sheet.write(row, 10, m3, sty['data_num'])
            sheet.write(row, 11, mbf, sty['data_num'])

            tot_pieces += pieces
            tot_m3 += m3
            tot_mbf += mbf
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, tot_pieces, sty['footer_int'])
        sheet.write(row, 10, tot_m3, sty['footer_num'])
        sheet.write(row, 11, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R3_Detalle_Patio_Subprod.xlsx')

    # ──────────────────────────────────────────────
    # R4 — RESUMEN POR PATIO — TIPO PRODUCTO
    # ──────────────────────────────────────────────

    def action_export_r4_summary_location_sub_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R4_Resumen_Patio_Subprod')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R4 — Resumen por Patio — Tipo Producto', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        agg = {}
        for line in self:
            loc = line.patio_label or 'Sin Patio'
            prod = line.product_id.name or 'Sin Producto'
            sub = line.subproduct_id.name or 'Sin Subproducto'
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += (line.pieces or 0)
            agg[key]['m3'] += (line.vol_physical_m3 or 0.0)
            agg[key]['mbf'] += (line.vol_mbf or 0.0)

        row = 2
        tot_p, tot_m3, tot_mbf = 0, 0.0, 0.0
        for (loc, prod, sub), vals in sorted(agg.items()):
            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, prod, sty['data_str'])
            sheet.write(row, 2, sub, sty['data_str'])
            sheet.write(row, 3, vals['pieces'], sty['data_int'])
            sheet.write(row, 4, vals['m3'], sty['data_num'])
            sheet.write(row, 5, vals['mbf'], sty['data_num'])
            tot_p += vals['pieces']
            tot_m3 += vals['m3']
            tot_mbf += vals['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        sheet.write(row, 1, '', sty['footer'])
        sheet.write(row, 2, '', sty['footer'])
        sheet.write(row, 3, tot_p, sty['footer_int'])
        sheet.write(row, 4, tot_m3, sty['footer_num'])
        sheet.write(row, 5, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R4_Resumen_Patio_Subprod.xlsx')

    # ──────────────────────────────────────────────
    # R5 — DETALLE POR PROVEEDOR
    # ──────────────────────────────────────────────

    def action_export_r5_detail_partner_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R5_Detalle_Proveedor')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 18, 12, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R5 — Detalle por Proveedor', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces = 0
        tot_m3 = 0.0
        tot_mbf = 0.0
        for line in self:
            loc = line.patio_label or ''
            provider = line.partner_name or ''
            guide = line.reception_id.name or ''
            date = line.reception_id.reception_date.strftime('%Y-%m-%d') if line.reception_id.reception_date else ''
            product = line.product_id.name or ''
            sub = line.subproduct_id.name or ''
            thick = line.thickness_visual or ''
            width = line.width_visual or ''
            length = line.length or 0
            pieces = line.pieces or 0
            m3 = line.vol_physical_m3 or 0.0
            mbf = line.vol_mbf or 0.0

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, provider, sty['data_str'])
            sheet.write(row, 2, guide, sty['data_str'])
            sheet.write(row, 3, date, sty['data_str'])
            sheet.write(row, 4, product, sty['data_str'])
            sheet.write(row, 5, sub, sty['data_str'])
            sheet.write(row, 6, thick, sty['data_str'])
            sheet.write(row, 7, width, sty['data_str'])
            sheet.write(row, 8, length, sty['data_num'])
            sheet.write(row, 9, pieces, sty['data_int'])
            sheet.write(row, 10, m3, sty['data_num'])
            sheet.write(row, 11, mbf, sty['data_num'])

            tot_pieces += pieces
            tot_m3 += m3
            tot_mbf += mbf
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, tot_pieces, sty['footer_int'])
        sheet.write(row, 10, tot_m3, sty['footer_num'])
        sheet.write(row, 11, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R5_Detalle_Proveedor.xlsx')

    # ──────────────────────────────────────────────
    # R6 — RESUMEN POR PROVEEDOR
    # ──────────────────────────────────────────────

    def action_export_r6_summary_partner_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R6_Resumen_Proveedor')
        sty = self._xlsx_styles(workbook)

        widths = [25, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Proveedor', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R6 — Resumen por Proveedor', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        agg = {}
        for line in self:
            provider = line.partner_name or 'Sin Proveedor'
            prod = line.product_id.name or 'Sin Producto'
            sub = line.subproduct_id.name or 'Sin Subproducto'
            key = (provider, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += (line.pieces or 0)
            agg[key]['m3'] += (line.vol_physical_m3 or 0.0)
            agg[key]['mbf'] += (line.vol_mbf or 0.0)

        row = 2
        tot_p, tot_m3, tot_mbf = 0, 0.0, 0.0
        for (provider, prod, sub), vals in sorted(agg.items()):
            sheet.write(row, 0, provider, sty['data_str'])
            sheet.write(row, 1, prod, sty['data_str'])
            sheet.write(row, 2, sub, sty['data_str'])
            sheet.write(row, 3, vals['pieces'], sty['data_int'])
            sheet.write(row, 4, vals['m3'], sty['data_num'])
            sheet.write(row, 5, vals['mbf'], sty['data_num'])
            tot_p += vals['pieces']
            tot_m3 += vals['m3']
            tot_mbf += vals['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        sheet.write(row, 1, '', sty['footer'])
        sheet.write(row, 2, '', sty['footer'])
        sheet.write(row, 3, tot_p, sty['footer_int'])
        sheet.write(row, 4, tot_m3, sty['footer_num'])
        sheet.write(row, 5, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R6_Resumen_Proveedor.xlsx')

    # ──────────────────────────────────────────────
    # R7 — DETALLE POR ORDEN DE COMPRA
    # ──────────────────────────────────────────────

    def action_export_r7_detail_purchase_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R7_Detalle_OC')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 18, 12, 25, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Orden de Compra', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R7 — Detalle por Orden de Compra', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces = 0
        tot_m3 = 0.0
        tot_mbf = 0.0
        for line in self:
            loc = line.patio_label or ''
            provider = line.partner_name or ''
            guide = line.reception_id.name or ''
            date = line.reception_id.reception_date.strftime('%Y-%m-%d') if line.reception_id.reception_date else ''
            product = line.product_id.name or ''
            sub = line.subproduct_id.name or ''
            thick = line.thickness_visual or ''
            width = line.width_visual or ''
            length = line.length or 0
            pieces = line.pieces or 0
            m3 = line.vol_physical_m3 or 0.0
            mbf = line.vol_mbf or 0.0

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, provider, sty['data_str'])
            sheet.write(row, 2, guide, sty['data_str'])
            sheet.write(row, 3, date, sty['data_str'])
            oc = line.reception_id.purchase_order or 'SIN ORDEN'
            sheet.write(row, 4, oc, sty['data_str'])
            sheet.write(row, 5, product, sty['data_str'])
            sheet.write(row, 6, sub, sty['data_str'])
            sheet.write(row, 7, thick, sty['data_str'])
            sheet.write(row, 8, width, sty['data_str'])
            sheet.write(row, 9, length, sty['data_num'])
            sheet.write(row, 10, pieces, sty['data_int'])
            sheet.write(row, 11, m3, sty['data_num'])
            sheet.write(row, 12, mbf, sty['data_num'])

            tot_pieces += pieces
            tot_m3 += m3
            tot_mbf += mbf
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 10):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 10, tot_pieces, sty['footer_int'])
        sheet.write(row, 11, tot_m3, sty['footer_num'])
        sheet.write(row, 12, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R7_Detalle_OC.xlsx')

    # ──────────────────────────────────────────────
    # R8 — RESUMEN POR ORDEN DE COMPRA
    # ──────────────────────────────────────────────

    def action_export_r8_summary_purchase_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R8_Resumen_OC')
        sty = self._xlsx_styles(workbook)

        widths = [25, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Orden de Compra', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R8 — Resumen por Orden de Compra', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        agg = {}
        for line in self:
            purchase = line.reception_id.purchase_id
            oc = purchase.name if purchase else 'Sin OC'
            prod = line.product_id.name or 'Sin Producto'
            sub = line.subproduct_id.name or 'Sin Subproducto'
            key = (oc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += (line.pieces or 0)
            agg[key]['m3'] += (line.vol_physical_m3 or 0.0)
            agg[key]['mbf'] += (line.vol_mbf or 0.0)

        row = 2
        tot_p, tot_m3, tot_mbf = 0, 0.0, 0.0
        for (oc, prod, sub), vals in sorted(agg.items()):
            sheet.write(row, 0, oc, sty['data_str'])
            sheet.write(row, 1, prod, sty['data_str'])
            sheet.write(row, 2, sub, sty['data_str'])
            sheet.write(row, 3, vals['pieces'], sty['data_int'])
            sheet.write(row, 4, vals['m3'], sty['data_num'])
            sheet.write(row, 5, vals['mbf'], sty['data_num'])
            tot_p += vals['pieces']
            tot_m3 += vals['m3']
            tot_mbf += vals['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        sheet.write(row, 1, '', sty['footer'])
        sheet.write(row, 2, '', sty['footer'])
        sheet.write(row, 3, tot_p, sty['footer_int'])
        sheet.write(row, 4, tot_m3, sty['footer_num'])
        sheet.write(row, 5, tot_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R8_Resumen_OC.xlsx')

    # ──────────────────────────────────────────────
    # R9 — DETALLE POR PRODUCTO
    # ──────────────────────────────────────────────

    def action_export_r9_detail_product_xlsx(self):
        if not self:
            raise UserError(_("No hay líneas para exportar."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R9_Detalle_Producto')
        sty = self._xlsx_styles(workbook)

        # Anchura columnas
        widths = [20, 25, 12, 25, 18, 12, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        # Cabecera
        cols = ['Producto', 'Subproducto', 'Patio', 'Proveedor',
                'Guía', 'Fecha', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R9 — Detalle por Producto', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # Agrupar por producto + subproducto para mantener orden y subtotales
        agg = {}
        order = []
        for line in self:
            prod = line.product_id.name or 'Sin Producto'
            sub = line.subproduct_id.name or 'Sin Subproducto'
            loc = line.patio_label or ''
            provider = line.partner_name or ''
            guide = line.reception_id.name or ''
            date = line.reception_id.reception_date.strftime('%Y-%m-%d') if line.reception_id.reception_date else ''
            thick = line.thickness_visual or ''
            width = line.width_visual or ''
            length = line.length or 0
            pieces = line.pieces or 0
            m3 = line.vol_physical_m3 or 0.0
            mbf = line.vol_mbf or 0.0

            key = (prod, sub)
            if key not in agg:
                agg[key] = {'rows': [], 'tot_p': 0, 'tot_m3': 0.0, 'tot_mbf': 0.0}
                order.append(key)
            agg[key]['rows'].append((loc, provider, guide, date, thick, width,
                                     length, pieces, m3, mbf))
            agg[key]['tot_p'] += pieces
            agg[key]['tot_m3'] += m3
            agg[key]['tot_mbf'] += mbf

        row = 2
        grand_p, grand_m3, grand_mbf = 0, 0.0, 0.0

        for i, (prod, sub) in enumerate(order):
            group = agg[(prod, sub)]

            # Fila de grupo (cabecera de producto)
            sheet.merge_range(row, 0, row, len(cols) - 1,
                              f'{prod} — {sub}', sty['header'])
            row += 1

            for (loc, provider, guide, date, thick, width,
                 length, pieces, m3, mbf) in group['rows']:
                sheet.write(row, 0, prod, sty['data_str'])
                sheet.write(row, 1, sub, sty['data_str'])
                sheet.write(row, 2, loc, sty['data_str'])
                sheet.write(row, 3, provider, sty['data_str'])
                sheet.write(row, 4, guide, sty['data_str'])
                sheet.write(row, 5, date, sty['data_str'])
                sheet.write(row, 6, thick, sty['data_str'])
                sheet.write(row, 7, width, sty['data_str'])
                sheet.write(row, 8, length, sty['data_num'])
                sheet.write(row, 9, pieces, sty['data_int'])
                sheet.write(row, 10, m3, sty['data_num'])
                sheet.write(row, 11, mbf, sty['data_num'])
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

        # Totales generales
        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, grand_p, sty['footer_int'])
        sheet.write(row, 10, grand_m3, sty['footer_num'])
        sheet.write(row, 11, grand_mbf, sty['footer_num'])

        return self._create_xlsx_attachment(workbook, output, 'R9_Detalle_Producto.xlsx')
