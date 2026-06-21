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
    _inherit = 'stock.quant' + 'report.helper.mixin' → stock.quant + lot_id → lot attributes.
    """
    _name = 'stock.quant'
    _inherit = ['stock.quant', 'report.helper.mixin']

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
    # HELPERS LEGACY (mantenidos por compatibilidad)
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
    # NOTA: _xlsx_styles() y _create_xlsx_attachment()
    # ahora se heredan de report.helper.mixin.
    # Se elimina la duplicación previa de ~54 líneas.
    # ──────────────────────────────────────────────────────

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
    # HELPERS LOCALES (delegados al mixin canónico cuando aplica)
    # ──────────────────────────────────────────────────────
    # NOTA (2026-06-16): _clean_lot_label y _build_escuadria fueron reemplazados
    # por los helpers canónicos del mixin report.helper.mixin:
    #   - _clean_lot_label → _report_get_canonical_lot_label
    #   - _build_escuadria   → _report_get_canonical_thickness + _report_get_canonical_width

    # ──────────────────────────────────────────────────────
    # R1 — DETALLE POR PATIO — INFORME OPERATIVO TRAZABLE
    # ──────────────────────────────────────────────────────

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
        sty = self._report_xlsx_styles(workbook)

        # 13 columnas — anchos compactos al estilo embarque
        widths = [16, 22, 14, 16, 16, 22, 24, 18, 16, 10, 8, 13, 16]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = [
            'Patio', 'Etiqueta Lote', 'Fecha Recepción', 'N° Guía',
            'N° Orden', 'Proveedor', 'Producto', 'Subproducto',
            'Escuadría', 'Largo (m)', 'Piezas', 'Vol. (m³)', 'Contenedor',
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

            # ── Cabecera de patio (estilo suave diferenciado de headers) ──
            sheet.merge_range(row, 0, row, len(cols) - 1,
                              f'📍 {patio_name}', sty['patio_header'])
            row += 1

            patio_pieces, patio_m3 = 0, 0.0
            for qi, q in enumerate(qs_sorted):
                lot = q.lot_id
                alt = qi % 2 == 1  # zebra striping

                # Resolver campos alineados con la vista Tree R1:
                # usar los mismos related/compute fields de stock.quant
                # que el Tree despliega directamente.
                label = lot.name.strip() if (lot and lot.name) else ''
                date = q.lot_reception_date.strftime('%Y-%m-%d') if q.lot_reception_date else ''
                guide = q.lot_guia_number or ''
                oc = q.lot_purchase_order or ''
                supplier = q.lot_supplier or ''
                product = q.product_id.name or ''
                sub = q.lot_subproducto or ''
                escuadria = q.lot_escuadria or ''
                length = q.lot_largo_m or 0.0
                pieces = q.lot_piezas or 0
                m3 = q.lot_volumen_m3 or 0.0
                container = q.lot_container_name or ''

                s_str = sty['data_str_alt'] if alt else sty['data_str']
                s_num = sty['data_num_alt'] if alt else sty['data_num']
                s_int = sty['data_int_alt'] if alt else sty['data_int']

                sheet.write(row, 0, patio_name, s_str)
                sheet.write(row, 1, label, s_str)
                sheet.write(row, 2, date, s_str)
                sheet.write(row, 3, guide, s_str)
                sheet.write(row, 4, oc, s_str)
                sheet.write(row, 5, supplier, s_str)
                sheet.write(row, 6, product, s_str)
                sheet.write(row, 7, sub, s_str)
                sheet.write(row, 8, escuadria, s_str)
                sheet.write(row, 9, length, s_num)
                sheet.write(row, 10, pieces, s_int)
                sheet.write(row, 11, m3, s_num)
                sheet.write(row, 12, container, s_str)

                patio_pieces += pieces
                patio_m3 += m3
                row += 1

            # ── Subtotal de patio ──
            sheet.write(row, 0, f'Subtotal {patio_name}', sty['footer'])
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

        # ── Total general (resaltado con borde doble) ──
        sheet.write(row, 0, 'TOTAL GENERAL', sty['grand_footer'])
        for c in range(1, 10):
            sheet.write(row, c, '', sty['grand_footer'])
        sheet.write(row, 10, grand_pieces, sty['grand_footer_int'])
        sheet.write(row, 11, grand_m3, sty['grand_footer_num'])
        sheet.write(row, 12, '', sty['grand_footer'])

        _logger.info("📊 R1: %d patios, %d quants, %d piezas totales",
                     len(patio_order), len(quants), grand_pieces)
        return self._report_create_xlsx_attachment(workbook, output, 'R1_Detalle_Patio_Stock_Real.xlsx')

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

        # Agregación manual por (location, product, subproducto) usando helpers canónicos
        # Para Producto se prefiere el nombre limpio del lote (sin [CÓDIGO])
        agg = {}
        for q in quants:
            loc = self._report_get_canonical_patio_label(q)
            lot = q.lot_id
            prod = (lot.product_name_only or self._report_get_canonical_product_name(q)) if lot else self._report_get_canonical_product_name(q)
            sub = self._report_get_canonical_subproduct_name(q)
            key = (loc, prod, sub)
            if key not in agg:
                agg[key] = {'pieces': 0, 'm3': 0.0, 'mbf': 0.0}
            agg[key]['pieces'] += self._report_get_canonical_pieces(q)
            agg[key]['m3'] += self._report_get_canonical_volume_m3(q)
            agg[key]['mbf'] += self._report_get_canonical_mbf(q)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('R2_Resumen_Patio_Stock')
        sty = self._report_xlsx_styles(workbook)

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
        return self._report_create_xlsx_attachment(workbook, output, 'R2_Resumen_Patio_Stock_Real.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 18, 16, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción', 'Producto',
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
            data = self._report_build_detail_row(q, include_oc=False)
            # Usar volumen_m3 del lote directamente (stock real)
            lot = q.lot_id
            m3 = lot.volumen_m3 if lot else 0.0
            mbf = lot.volumen_mbf if lot else 0.0

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
            sheet.write(row, 10, m3, sty['data_num'])
            sheet.write(row, 11, mbf, sty['data_num'])

            tot_pieces += data['piezas']
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
        return self._report_create_xlsx_attachment(workbook, output, 'R5_Detalle_Proveedor_Stock_Real.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 18, 16, 18, 25, 20, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Patio', 'Proveedor', 'Guía', 'Fecha de recepción',
                'Orden de Compra', 'Producto', 'Subproducto',
                'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R7 — Detalle por Orden de Compra — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        row = 2
        tot_pieces, tot_m3, tot_mbf = 0, 0.0, 0.0
        for q in quants.sorted(key=lambda x: (
            self._report_get_canonical_purchase_order(x),
            x.product_id.name or ''
        )):
            lot = q.lot_id
            data = self._report_build_detail_row(q, include_oc=True)
            m3 = lot.volumen_m3 if lot else 0.0
            mbf = lot.volumen_mbf if lot else 0.0

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
            sheet.write(row, 11, m3, sty['data_num'])
            sheet.write(row, 12, mbf, sty['data_num'])

            tot_pieces += data['piezas']
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
        return self._report_create_xlsx_attachment(workbook, output, 'R7_Detalle_OC_Stock_Real.xlsx')

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
        sty = self._report_xlsx_styles(workbook)

        widths = [20, 25, 12, 25, 18, 16, 10, 10, 10, 9, 12, 12]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

        cols = ['Producto', 'Subproducto', 'Patio', 'Proveedor',
                'Guía', 'Fecha de recepción', 'Espesor', 'Ancho', 'Largo (m)',
                'Piezas', 'M3', 'MBF']
        sheet.merge_range(0, 0, 0, len(cols) - 1,
                          'R9 — Detalle por Producto — Stock Real (stock.quant)', sty['title'])
        for i, c in enumerate(cols):
            sheet.write(1, i, c, sty['header'])

        # Usar helper genérico de agrupación R9
        structure = self._report_build_r9_structure(quants, include_oc=False)
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

        _logger.info("📊 R9 STOCK FÍSICO: %d grupos, %d quants exportados", len(structure['order']), len(quants))
        return self._report_create_xlsx_attachment(workbook, output, 'R9_Detalle_Producto_Stock_Real.xlsx')