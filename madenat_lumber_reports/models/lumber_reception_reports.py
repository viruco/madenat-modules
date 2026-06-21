# -*- coding: utf-8 -*-
"""
8 Reportes de Inventario Recepción — XLSX + PDF
Hereda de lumber.reception.line y report.helper.mixin para métodos de exportación.
"""
# -*- coding: utf-8 -*-

import io
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LumberReceptionLineReport(models.Model):
    _name = 'lumber.reception.line'
    _inherit = ['lumber.reception.line', 'report.helper.mixin']

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
    # NOTA: _xlsx_styles() y _create_xlsx_attachment()
    # ahora se heredan de report.helper.mixin.
    # Se elimina la duplicación previa de ~54 líneas.
    # ──────────────────────────────────────────────
    # NOTA: _get_location_name() y _get_subproduct_name()
    # fueron eliminados (2026-06-16). No tenían referencias activas.
    # Usar _report_get_canonical_patio_label() y
    # _report_get_canonical_subproduct_name() del mixin en su lugar.
    # ──────────────────────────────────────────────

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
        sty = self._report_xlsx_styles(workbook)

        # Anchura columnas (13 columnas: +OC respecto al original)
        widths = [20, 25, 18, 16, 18, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        # Cabecera (encabezados corregidos: Fecha de recepción + OC)
        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción',
                'Orden de Compra', 'Producto', 'Subproducto',
                'Espesor', 'Ancho', 'Largo (m)',
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
            data = self._report_build_detail_row(line, include_oc=True)
            sheet.write(row, 0, data['patio'], sty['data_str'])
            sheet.write(row, 1, data['proveedor'], sty['data_str'])
            sheet.write(row, 2, data['guia'], sty['data_str'])
            sheet.write(row, 3, data['fecha_recepcion'], sty['data_str'])
            sheet.write(row, 4, data['oc'], sty['data_str'])
            sheet.write(row, 5, data['producto'], sty['data_str'])
            sheet.write(row, 6, data['subproducto'], sty['data_str'])
            sheet.write(row, 7, data['espesor'], sty['data_str'])
            sheet.write(row, 8, data['ancho'], sty['data_str'])
            sheet.write(row, 9, data['largo'], sty['data_num'])
            sheet.write(row, 10, data['piezas'], sty['data_int'])
            sheet.write(row, 11, data['m3'], sty['data_num'])
            sheet.write(row, 12, data['mbf'], sty['data_num'])

            tot_pieces += data['piezas']
            tot_m3 += data['m3']
            tot_mbf += data['mbf']
            row += 1

        # Totales
        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 10):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 10, tot_pieces, sty['footer_int'])
        sheet.write(row, 11, tot_m3, sty['footer_num'])
        sheet.write(row, 12, tot_mbf, sty['footer_num'])

        return self._report_create_xlsx_attachment(workbook, output, 'R1_Detalle_Patio.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R2 — Resumen por Patio — Todos Productos', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # Agrupación usando helpers canónicos
        agg = {}
        for line in self:
            loc = self._report_get_canonical_patio_label(line)
            prod = self._report_get_canonical_product_name(line)
            sub = self._report_get_canonical_subproduct_name(line)
            pieces = self._report_get_canonical_pieces(line)
            m3 = self._report_get_canonical_volume_m3(line)
            mbf = self._report_get_canonical_mbf(line)
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += pieces
            agg[key]['m3'] += m3
            agg[key]['mbf'] += mbf

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

        return self._report_create_xlsx_attachment(workbook, output, 'R2_Resumen_Patio.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 18, 16, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción', 'Producto',
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
            data = self._report_build_detail_row(line, include_oc=False)
            sheet.write(row, 0, data['patio'], sty['data_str'])
            sheet.write(row, 1, data['proveedor'], sty['data_str'])
            sheet.write(row, 2, data['guia'], sty['data_str'])
            sheet.write(row, 3, data['fecha_recepcion'], sty['data_str'])
            sheet.write(row, 4, data['producto'], sty['data_str'])
            sheet.write(row, 5, data['subproducto'], sty['data_str'])
            sheet.write(row, 6, data['espesor'], sty['data_str'])
            sheet.write(row, 7, data['ancho'], sty['data_str'])
            sheet.write(row, 8, data['largo'], sty['data_num'])
            sheet.write(row, 9, data['piezas'], sty['data_int'])
            sheet.write(row, 10, data['m3'], sty['data_num'])
            sheet.write(row, 11, data['mbf'], sty['data_num'])

            tot_pieces += data['piezas']
            tot_m3 += data['m3']
            tot_mbf += data['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, tot_pieces, sty['footer_int'])
        sheet.write(row, 10, tot_m3, sty['footer_num'])
        sheet.write(row, 11, tot_mbf, sty['footer_num'])

        return self._report_create_xlsx_attachment(workbook, output, 'R3_Detalle_Patio_Subprod.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

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
            loc = self._report_get_canonical_patio_label(line)
            prod = self._report_get_canonical_product_name(line)
            sub = self._report_get_canonical_subproduct_name(line)
            pieces = self._report_get_canonical_pieces(line)
            m3 = self._report_get_canonical_volume_m3(line)
            mbf = self._report_get_canonical_mbf(line)
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += pieces
            agg[key]['m3'] += m3
            agg[key]['mbf'] += mbf

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

        return self._report_create_xlsx_attachment(workbook, output, 'R4_Resumen_Patio_Subprod.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 18, 16, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción', 'Producto',
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
            data = self._report_build_detail_row(line, include_oc=False)
            sheet.write(row, 0, data['patio'], sty['data_str'])
            sheet.write(row, 1, data['proveedor'], sty['data_str'])
            sheet.write(row, 2, data['guia'], sty['data_str'])
            sheet.write(row, 3, data['fecha_recepcion'], sty['data_str'])
            sheet.write(row, 4, data['producto'], sty['data_str'])
            sheet.write(row, 5, data['subproducto'], sty['data_str'])
            sheet.write(row, 6, data['espesor'], sty['data_str'])
            sheet.write(row, 7, data['ancho'], sty['data_str'])
            sheet.write(row, 8, data['largo'], sty['data_num'])
            sheet.write(row, 9, data['piezas'], sty['data_int'])
            sheet.write(row, 10, data['m3'], sty['data_num'])
            sheet.write(row, 11, data['mbf'], sty['data_num'])

            tot_pieces += data['piezas']
            tot_m3 += data['m3']
            tot_mbf += data['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, tot_pieces, sty['footer_int'])
        sheet.write(row, 10, tot_m3, sty['footer_num'])
        sheet.write(row, 11, tot_mbf, sty['footer_num'])

        return self._report_create_xlsx_attachment(workbook, output, 'R5_Detalle_Proveedor.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

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
            provider = self._report_get_canonical_supplier_name(line)
            prod = self._report_get_canonical_product_name(line)
            sub = self._report_get_canonical_subproduct_name(line)
            pieces = self._report_get_canonical_pieces(line)
            m3 = self._report_get_canonical_volume_m3(line)
            mbf = self._report_get_canonical_mbf(line)
            key = (provider, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += pieces
            agg[key]['m3'] += m3
            agg[key]['mbf'] += mbf

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

        return self._report_create_xlsx_attachment(workbook, output, 'R6_Resumen_Proveedor.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 18, 16, 18, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción',
                'Orden de Compra', 'Producto', 'Subproducto',
                'Espesor', 'Ancho', 'Largo (m)',
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
            data = self._report_build_detail_row(line, include_oc=True)
            sheet.write(row, 0, data['patio'], sty['data_str'])
            sheet.write(row, 1, data['proveedor'], sty['data_str'])
            sheet.write(row, 2, data['guia'], sty['data_str'])
            sheet.write(row, 3, data['fecha_recepcion'], sty['data_str'])
            sheet.write(row, 4, data['oc'], sty['data_str'])
            sheet.write(row, 5, data['producto'], sty['data_str'])
            sheet.write(row, 6, data['subproducto'], sty['data_str'])
            sheet.write(row, 7, data['espesor'], sty['data_str'])
            sheet.write(row, 8, data['ancho'], sty['data_str'])
            sheet.write(row, 9, data['largo'], sty['data_num'])
            sheet.write(row, 10, data['piezas'], sty['data_int'])
            sheet.write(row, 11, data['m3'], sty['data_num'])
            sheet.write(row, 12, data['mbf'], sty['data_num'])

            tot_pieces += data['piezas']
            tot_m3 += data['m3']
            tot_mbf += data['mbf']
            row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 10):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 10, tot_pieces, sty['footer_int'])
        sheet.write(row, 11, tot_m3, sty['footer_num'])
        sheet.write(row, 12, tot_mbf, sty['footer_num'])

        return self._report_create_xlsx_attachment(workbook, output, 'R7_Detalle_OC.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

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
            oc = self._report_get_canonical_purchase_order(line)
            prod = self._report_get_canonical_product_name(line)
            sub = self._report_get_canonical_subproduct_name(line)
            pieces = self._report_get_canonical_pieces(line)
            m3 = self._report_get_canonical_volume_m3(line)
            mbf = self._report_get_canonical_mbf(line)
            key = (oc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += pieces
            agg[key]['m3'] += m3
            agg[key]['mbf'] += mbf

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

        return self._report_create_xlsx_attachment(workbook, output, 'R8_Resumen_OC.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        # Anchura columnas
        widths = [20, 25, 12, 25, 18, 16, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        # Cabecera (encabezado corregido: Fecha de recepción)
        cols = ['Producto', 'Subproducto', 'Patio', 'Proveedor',
                'Guía', 'Fecha de recepción', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R9 — Detalle por Producto', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # Usar helper genérico de agrupación R9
        structure = self._report_build_r9_structure(self, include_oc=False)
        row, grand_p, grand_m3, grand_mbf = self._report_write_r9_xlsx_body(
            sheet, sty, structure, start_row=2
        )

        # Totales generales
        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, grand_p, sty['footer_int'])
        sheet.write(row, 10, grand_m3, sty['footer_num'])
        sheet.write(row, 11, grand_mbf, sty['footer_num'])

        return self._report_create_xlsx_attachment(workbook, output, 'R9_Detalle_Producto.xlsx')