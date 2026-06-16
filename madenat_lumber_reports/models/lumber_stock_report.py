# -*- coding: utf-8 -*-
"""
📊 REPORTES DE STOCK REAL — FASE 4: stock.quant como fuente física
Modelo: stock.quant (existencias reales en ubicaciones internas)
Capa de enriquecimiento: stock.lot (proveedor, OC, dimensiones, subproducto)

Diseño:
  - stock.quant con quantity > 0 en ubicaciones internas = existencia física real
  - stock.lot proporciona atributos: proveedor, guía, OC, subproducto, dimensiones
  - Filtro de existencia: quantity > 0 AND location_id.usage = 'internal'
  - Ningún campo documental (estado_trazabilidad, reception_id) se usa como filtro

Arquitectura:
  - Dataset: stock.quant filtrado por existencias reales
  - Lot enrichment: quant.lot_id → todos los campos de StockLotExtended
  - Agregación: read_group() nativo de Odoo (GROUP BY SQL)
  - Salida: XLSX con formato Calibri 11pt

Qué NO hace este archivo:
  - No toca lumber.reception.line
  - No modifica reportes R3/R4/R6/R8
  - No crea vistas ni PDFs
  - No mezcla stock con embarques
"""

import io
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LumberStockReport(models.Model):
    """
    Reportes de inventario real basados en stock.quant.
    _inherit = 'stock.quant' → stock.quant + lot_id → lot attributes.
    """
    _inherit = 'stock.quant'

    # ──────────────────────────────────────────────────────
    # CAMPO COMPUTADO: nombre de ubicación (atributo del quant)
    # ──────────────────────────────────────────────────────
    location_name = fields.Char(
        string='Nombre Ubicación',
        compute='_compute_location_name',
        store=True,
        readonly=True,
        index=True,
        help="Nombre de la ubicación física del quant."
    )

    @api.depends('location_id', 'location_id.name')
    def _compute_location_name(self):
        for q in self:
            if q.location_id and q.location_id.name:
                q.location_name = q.location_id.name
            else:
                q.location_name = _('Sin Patio')

    # ──────────────────────────────────────────────────────
    # CAMPOS DE NEGOCIO ENRIQUECIDOS DESDE stock.lot
    # Se exponen en stock.quant para vista tree R1 y export XLSX.
    # ──────────────────────────────────────────────────────

    lot_reception_date = fields.Datetime(
        string='Fecha Recepción',
        related='lot_id.reception_id.reception_date',
        store=True,
        readonly=True,
        help="Fecha de recepción del lote asociado."
    )

    lot_guia_number = fields.Char(
        string='N° Guía',
        related='lot_id.guia_number',
        store=True,
        readonly=True,
        help="Número de guía del lote."
    )

    lot_purchase_order = fields.Char(
        string='N° Orden',
        compute='_compute_lot_purchase_order',
        store=True,
        readonly=True,
        help="Número de orden de compra del lote."
    )

    @api.depends('lot_id.purchase_order_id', 'lot_id.purchase_order_id.name')
    def _compute_lot_purchase_order(self):
        for q in self:
            if q.lot_id and q.lot_id.purchase_order_id:
                q.lot_purchase_order = q.lot_id.purchase_order_id.name or ''
            else:
                q.lot_purchase_order = ''

    lot_supplier = fields.Char(
        string='Proveedor',
        compute='_compute_lot_supplier',
        store=True,
        readonly=True,
        help="Proveedor del lote."
    )

    @api.depends('lot_id.supplier_id', 'lot_id.supplier_id.name')
    def _compute_lot_supplier(self):
        for q in self:
            if q.lot_id and q.lot_id.supplier_id:
                q.lot_supplier = q.lot_id.supplier_id.name or ''
            else:
                q.lot_supplier = ''

    lot_subproducto = fields.Char(
        string='Subproducto',
        related='lot_id.subproducto_id.name',
        store=True,
        readonly=True,
        help="Subproducto asociado al lote."
    )

    lot_escuadria = fields.Char(
        string='Escuadría',
        related='lot_id.escuadria',
        store=True,
        readonly=True,
        help="Escuadría del lote (espesor x ancho)."
    )

    lot_largo_m = fields.Float(
        string='Largo (m)',
        related='lot_id.largo_m',
        store=True,
        readonly=True,
        digits=(16, 3),
        help="Largo en metros del lote."
    )

    lot_volumen_m3 = fields.Float(
        string='Volumen (m³)',
        related='lot_id.volumen_m3',
        store=True,
        readonly=True,
        digits=(16, 3),
        help="Volumen en m³ del lote."
    )

    lot_piezas = fields.Integer(
        string='Piezas',
        related='lot_id.piezas',
        store=True,
        readonly=True,
        help="Cantidad de piezas del lote."
    )

    lot_container_name = fields.Char(
        string='Contenedor',
        compute='_compute_lot_container_name',
        store=True,
        readonly=True,
        help="Contenedor asociado al lote, si existe."
    )

    @api.depends('lot_id')
    def _compute_lot_container_name(self):
        for q in self:
            if not q.lot_id:
                q.lot_container_name = ''
                continue
            try:
                container = self.env['lumber.container'].sudo().search(
                    [('lot_ids', 'in', q.lot_id.id)], limit=1
                )
                q.lot_container_name = container.name if container else ''
            except Exception:
                q.lot_container_name = ''

    # ──────────────────────────────────────────────────────
    # HELPERS: leer atributos del lote desde quant.lot_id
    # ──────────────────────────────────────────────────────

    def _lot_name(self, field_name, default=''):
        """Lee un campo Char del lote asociado sin duplicar en stock.quant."""
        self.ensure_one()
        lot = self.lot_id
        if not lot:
            return default
        return getattr(lot, field_name, None) or default

    def _lot_m2o_name(self, field_name, default=''):
        """Lee el display_name de un Many2one del lote asociado."""
        self.ensure_one()
        lot = self.lot_id
        if not lot:
            return default
        obj = getattr(lot, field_name, None)
        return obj.display_name if obj else default

    # ──────────────────────────────────────────────────────
    # ESTILOS XLSX (Calibri 11pt — mismo formato que legacy)
    # ──────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────
    # FILTRO CANÓNICO DE STOCK FÍSICO REAL
    # ──────────────────────────────────────────────────────

    def _domain_stock_real(self):
        """Dominio que representa existencia física real en ubicaciones internas."""
        return [
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ]

    def _filtered_stock_real(self):
        """Filtra el recordset actual para conservar solo stock físico real.
        Excluye quants sin lote: sin trazabilidad no hay atributos de negocio."""
        return self.filtered(
            lambda q: q.quantity > 0
            and q.location_id.usage == 'internal'
            and q.lot_id
        )

    # ──────────────────────────────────────────────────────
    # R1 — DETALLE POR PATIO — INFORME OPERATIVO TRAZABLE
    # ──────────────────────────────────────────────────────

    def _get_container_name(self, lot):
        """Busca el contenedor asociado al lote, si existe."""
        if not lot:
            return ''
        try:
            container = self.env['lumber.container'].sudo().search(
                [('lot_ids', 'in', lot.id)], limit=1
            )
            return container.name if container else ''
        except Exception:
            return ''

    def _clean_lot_label(self, lot):
        """Devuelve la etiqueta del lote sin prefijos técnicos."""
        if not lot:
            return ''
        name = lot.name or ''
        # Si la etiqueta es un número largo con padding, mantenerla tal cual
        return name.strip()

    def _build_escuadria(self, lot):
        """Construye la escuadría legible: espesor x ancho."""
        if not lot:
            return ''
        if lot.escuadria and lot.escuadria.strip():
            return lot.escuadria.strip()
        thick = lot.thickness_visual or ''
        wide = lot.width_visual or ''
        if thick and wide:
            return f'{thick} x {wide}'
        if thick:
            return thick
        if wide:
            return wide
        return ''

    def action_export_r1_stock_detail_xlsx(self):
        _logger.info("━━━ 📊 R1 — DETALLE POR PATIO (INFORME OPERATIVO) ━━━")

        if not self:
            raise UserError(_("No hay quants seleccionados."))

        quants = self._filtered_stock_real()
        if not quants:
            raise UserError(_("Ninguno de los quants seleccionados tiene existencias reales en ubicaciones internas."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter (pip install xlsxwriter)."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R1_Stock_Real_Patio')
        sty = self._xlsx_styles(workbook)

        # 13 columnas en el orden especificado
        widths = [22, 18, 14, 18, 18, 24, 28, 20, 18, 10, 8, 12, 18]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = [
            'Patio', 'Etiqueta Lote', 'Fecha Recepción', 'N° Guía',
            'N° Orden', 'Proveedor', 'Producto', 'Subproducto',
            'Escuadría', 'Largo (m)', 'Piezas', 'Vol. Stock (m³)', 'Contenedor',
        ]
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R1 — Detalle por Patio — Stock Real', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # ── Agrupación por patio ──
        patios = {}
        for q in quants:
            loc = q.location_name or _('Sin Patio')
            if loc not in patios:
                patios[loc] = []
            patios[loc].append(q)

        row = 2
        grand_pieces, grand_m3 = 0, 0.0
        patio_order = sorted(patios.keys())

        for pi, patio_name in enumerate(patio_order):
            qs = patios[patio_name]
            # Ordenar por etiqueta de lote dentro del patio
            qs_sorted = sorted(qs, key=lambda x: (x.lot_id.name or '') if x.lot_id else '')

            # ── Cabecera de patio ──
            sheet.merge_range(row, 0, row, len(cols) - 1,
                              f'📍 {patio_name}', sty['header'])
            row += 1

            patio_pieces, patio_m3 = 0, 0.0
            for q in qs_sorted:
                lot = q.lot_id
                label = self._clean_lot_label(lot)
                date = ''
                if lot and lot.reception_id and lot.reception_id.reception_date:
                    date = lot.reception_id.reception_date.strftime('%Y-%m-%d')
                guide = lot.guia_number if lot and lot.guia_number else ''
                oc = lot.purchase_order_id.name if lot and lot.purchase_order_id else ''
                supplier = lot.supplier_id.name if lot and lot.supplier_id else ''
                product = q.product_id.name or ''
                sub = lot.subproducto_id.name if lot and lot.subproducto_id else ''
                escuadria = self._build_escuadria(lot)
                length = lot.largo_m if lot else 0
                pieces = lot.piezas if lot else 0
                m3 = round(lot.volumen_m3, 3) if lot and lot.volumen_m3 else 0.0
                container = self._get_container_name(lot)

                sheet.write(row, 0, patio_name, sty['data_str'])
                sheet.write(row, 1, label, sty['data_str'])
                sheet.write(row, 2, date, sty['data_str'])
                sheet.write(row, 3, guide, sty['data_str'])
                sheet.write(row, 4, oc, sty['data_str'])
                sheet.write(row, 5, supplier, sty['data_str'])
                sheet.write(row, 6, product, sty['data_str'])
                sheet.write(row, 7, sub, sty['data_str'])
                sheet.write(row, 8, escuadria, sty['data_str'])
                sheet.write(row, 9, length, sty['data_num'])
                sheet.write(row, 10, pieces, sty['data_int'])
                sheet.write(row, 11, m3, sty['data_num'])
                sheet.write(row, 12, container, sty['data_str'])

                patio_pieces += pieces
                patio_m3 += m3
                row += 1

            # ── Subtotal de patio ──
            sheet.write(row, 0, f'SUB {patio_name}', sty['footer'])
            for c in range(1, 10):
                sheet.write(row, c, '', sty['footer'])
            sheet.write(row, 10, patio_pieces, sty['footer_int'])
            sheet.write(row, 11, patio_m3, sty['footer_num'])
            sheet.write(row, 12, '', sty['footer'])
            grand_pieces += patio_pieces
            grand_m3 += patio_m3
            row += 1

            if pi < len(patio_order) - 1:
                row += 1  # línea vacía entre patios

        # ── Total general ──
        sheet.write(row, 0, 'TOTAL GENERAL', sty['footer'])
        for c in range(1, 10):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 10, grand_pieces, sty['footer_int'])
        sheet.write(row, 11, grand_m3, sty['footer_num'])
        sheet.write(row, 12, '', sty['footer'])

        _logger.info("📊 R1: %d patios, %d quants, %d piezas totales",
                     len(patio_order), len(quants), grand_pieces)
        return self._create_xlsx_attachment(workbook, output, 'R1_Detalle_Patio_Stock_Real.xlsx')

    # ──────────────────────────────────────────────────────
    # R2 — RESUMEN POR PATIO — TODOS PRODUCTOS
    # ──────────────────────────────────────────────────────

    def action_export_r2_stock_summary_location_xlsx(self):
        _logger.info("━━━ 📊 R2 STOCK FÍSICO — RESUMEN POR PATIO ━━━")

        if not self:
            raise UserError(_("No hay quants seleccionados."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter (pip install xlsxwriter)."))

        quants = self._filtered_stock_real()
        if not quants:
            raise UserError(_("Sin existencias reales en ubicaciones internas."))

        # Agregación manual por (location, product, subproducto) desde lot_id
        agg = {}
        for q in quants:
            lot = q.lot_id
            loc = q.location_name or _('Sin Patio')
            prod = q.product_id.name or _('Sin Producto')
            sub = lot.subproducto_id.name if lot and lot.subproducto_id else _('Sin Subproducto')
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += (lot.piezas if lot else 0)
            agg[key]['m3'] += (lot.volumen_m3 if lot else 0.0)
            agg[key]['mbf'] += (lot.volumen_mbf if lot else 0.0)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R2_Resumen_Patio_Stock')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 20, 14, 14, 14]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Producto', 'Subproducto', 'Total Piezas', 'Total M3', 'Total MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R2 — Resumen por Patio — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

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

        _logger.info("📊 R2 STOCK FÍSICO: %d grupos exportados", len(agg))
        return self._create_xlsx_attachment(workbook, output, 'R2_Resumen_Patio_Stock_Real.xlsx')

    # ──────────────────────────────────────────────────────
    # R5 — DETALLE POR PROVEEDOR
    # ──────────────────────────────────────────────────────

    def action_export_r5_stock_detail_partner_xlsx(self):
        _logger.info("━━━ 📊 R5 STOCK FÍSICO — DETALLE POR PROVEEDOR ━━━")

        if not self:
            raise UserError(_("No hay quants seleccionados."))

        quants = self._filtered_stock_real()
        if not quants:
            raise UserError(_("Sin existencias reales en ubicaciones internas."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R5_Detalle_Proveedor_Stock')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 18, 12, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R5 — Detalle por Proveedor — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces, tot_m3, tot_mbf = 0, 0.0, 0.0
        for q in quants.sorted(key=lambda x: (
            x.lot_id.supplier_id.name if x.lot_id and x.lot_id.supplier_id else '',
            x.product_id.name or ''
        )):
            lot = q.lot_id
            supplier = lot.supplier_id.name if lot and lot.supplier_id else ''
            loc = q.location_name or ''
            guide = lot.guia_number if lot and lot.guia_number else ''
            date = ''
            if lot and lot.reception_id and lot.reception_id.reception_date:
                date = lot.reception_id.reception_date.strftime('%Y-%m-%d')
            product = q.product_id.name or ''
            sub = lot.subproducto_id.name if lot and lot.subproducto_id else ''
            thick = lot.thickness_visual if lot else ''
            width = lot.width_visual if lot else ''
            length = lot.largo_m if lot else 0
            pieces = lot.piezas if lot else 0
            m3 = lot.volumen_m3 if lot else 0.0
            mbf = lot.volumen_mbf if lot else 0.0

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, supplier, sty['data_str'])
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

        _logger.info("📊 R5 STOCK FÍSICO: %d quants exportados", len(quants))
        return self._create_xlsx_attachment(workbook, output, 'R5_Detalle_Proveedor_Stock_Real.xlsx')

    # ──────────────────────────────────────────────────────
    # R7 — DETALLE POR ORDEN DE COMPRA
    # ──────────────────────────────────────────────────────

    def action_export_r7_stock_detail_purchase_xlsx(self):
        _logger.info("━━━ 📊 R7 STOCK FÍSICO — DETALLE POR OC ━━━")

        if not self:
            raise UserError(_("No hay quants seleccionados."))

        quants = self._filtered_stock_real()
        if not quants:
            raise UserError(_("Sin existencias reales en ubicaciones internas."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R7_Detalle_OC_Stock')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 18, 12, 25, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha', 'Orden de Compra', 'Producto',
                'Subproducto', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R7 — Detalle por Orden de Compra — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces, tot_m3, tot_mbf = 0, 0.0, 0.0
        for q in quants.sorted(key=lambda x: (
            x.lot_id.purchase_order_id.name if x.lot_id and x.lot_id.purchase_order_id else 'SIN ORDEN',
            x.product_id.name or ''
        )):
            lot = q.lot_id
            supplier = lot.supplier_id.name if lot and lot.supplier_id else ''
            loc = q.location_name or ''
            guide = lot.guia_number if lot and lot.guia_number else ''
            date = ''
            if lot and lot.reception_id and lot.reception_id.reception_date:
                date = lot.reception_id.reception_date.strftime('%Y-%m-%d')
            product = q.product_id.name or ''
            sub = lot.subproducto_id.name if lot and lot.subproducto_id else ''
            thick = lot.thickness_visual if lot else ''
            width = lot.width_visual if lot else ''
            length = lot.largo_m if lot else 0
            pieces = lot.piezas if lot else 0
            m3 = lot.volumen_m3 if lot else 0.0
            mbf = lot.volumen_mbf if lot else 0.0
            oc = lot.purchase_order_id.name if lot and lot.purchase_order_id else 'SIN ORDEN'

            sheet.write(row, 0, loc, sty['data_str'])
            sheet.write(row, 1, supplier, sty['data_str'])
            sheet.write(row, 2, guide, sty['data_str'])
            sheet.write(row, 3, date, sty['data_str'])
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

        _logger.info("📊 R7 STOCK FÍSICO: %d quants exportados", len(quants))
        return self._create_xlsx_attachment(workbook, output, 'R7_Detalle_OC_Stock_Real.xlsx')

    # ──────────────────────────────────────────────────────
    # R9 — DETALLE POR PRODUCTO
    # ──────────────────────────────────────────────────────

    def action_export_r9_stock_detail_product_xlsx(self):
        _logger.info("━━━ 📊 R9 STOCK FÍSICO — DETALLE POR PRODUCTO ━━━")

        if not self:
            raise UserError(_("No hay quants seleccionados."))

        quants = self._filtered_stock_real()
        if not quants:
            raise UserError(_("Sin existencias reales en ubicaciones internas."))

        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Instale xlsxwriter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R9_Detalle_Producto_Stock')
        sty = self._xlsx_styles(workbook)

        widths = [20, 25, 12, 25, 18, 12, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Producto', 'Subproducto', 'Patio', 'Proveedor',
                'Guía', 'Fecha', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R9 — Detalle por Producto — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        agg = {}
        order = []
        for q in quants:
            lot = q.lot_id
            supplier = lot.supplier_id.name if lot and lot.supplier_id else ''
            prod = q.product_id.name or 'Sin Producto'
            sub = lot.subproducto_id.name if lot and lot.subproducto_id else 'Sin Subproducto'
            loc = q.location_name or ''
            guide = lot.guia_number if lot and lot.guia_number else ''
            date = ''
            if lot and lot.reception_id and lot.reception_id.reception_date:
                date = lot.reception_id.reception_date.strftime('%Y-%m-%d')
            thick = lot.thickness_visual if lot else ''
            width = lot.width_visual if lot else ''
            length = lot.largo_m if lot else 0
            pieces = lot.piezas if lot else 0
            m3 = lot.volumen_m3 if lot else 0.0
            mbf = lot.volumen_mbf if lot else 0.0

            key = (prod, sub)
            if key not in agg:
                agg[key] = {'rows': [], 'tot_p': 0, 'tot_m3': 0.0, 'tot_mbf': 0.0}
                order.append(key)
            agg[key]['rows'].append((loc, supplier, guide, date, thick, width,
                                     length, pieces, m3, mbf))
            agg[key]['tot_p'] += pieces
            agg[key]['tot_m3'] += m3
            agg[key]['tot_mbf'] += mbf

        row = 2
        grand_p, grand_m3, grand_mbf = 0, 0.0, 0.0
        for i, (prod, sub) in enumerate(order):
            group = agg[(prod, sub)]
            sheet.merge_range(row, 0, row, len(cols) - 1,
                              f'{prod} — {sub}', sty['header'])
            row += 1
            for (loc, supplier, guide, date, thick, width,
                 length, pieces, m3, mbf) in group['rows']:
                sheet.write(row, 0, prod, sty['data_str'])
                sheet.write(row, 1, sub, sty['data_str'])
                sheet.write(row, 2, loc, sty['data_str'])
                sheet.write(row, 3, supplier, sty['data_str'])
                sheet.write(row, 4, guide, sty['data_str'])
                sheet.write(row, 5, date, sty['data_str'])
                sheet.write(row, 6, thick, sty['data_str'])
                sheet.write(row, 7, width, sty['data_str'])
                sheet.write(row, 8, length, sty['data_num'])
                sheet.write(row, 9, pieces, sty['data_int'])
                sheet.write(row, 10, m3, sty['data_num'])
                sheet.write(row, 11, mbf, sty['data_num'])
                row += 1
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
            if i < len(order) - 1:
                row += 1

        sheet.write(row, 0, 'TOTALES', sty['footer'])
        for c in range(1, 9):
            sheet.write(row, c, '', sty['footer'])
        sheet.write(row, 9, grand_p, sty['footer_int'])
        sheet.write(row, 10, grand_m3, sty['footer_num'])
        sheet.write(row, 11, grand_mbf, sty['footer_num'])

        _logger.info("📊 R9 STOCK FÍSICO: %d grupos, %d quants exportados", len(order), len(quants))
        return self._create_xlsx_attachment(workbook, output, 'R9_Detalle_Producto_Stock_Real.xlsx')