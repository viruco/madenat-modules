# -*- coding: utf-8 -*-
"""Cobertura de la ruta Core `_parse_excel_data_core` por formato binario.

- XLS legacy OLE2 → pandas engine='xlrd' (nunca openpyxl).
- XLSX            → openpyxl (load_workbook), sin pandas.
- El error "File is not a zip file" de openpyxl sobre OLE2 no se propaga.
"""

import io
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

from odoo.addons.madenat_lumber_core.models import madenat_guia_processing as gp_module


def _build_xls_bytes():
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    header = ['Codigo', 'Producto', 'Cantidad', 'M3', 'LOTE',
              'Espesor', 'Ancho', 'Largo']
    row = ['C001', 'MADERA', 150, 3.8862, 'L1', 38.1, 170, 4.05]
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for col, val in enumerate(row):
        ws.write(1, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xlsx_bytes():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(['Codigo', 'Producto', 'Cantidad', 'M3', 'LOTE',
               'Espesor', 'Ancho', 'Largo'])
    ws.append(['C001', 'MADERA', 150, 3.8862, 'L1', 38.1, 170, 4.05])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xls_blanks_bytes():
    """XLS OLE2 con encabezado abreviado (tipo 95083) y decimales con coma."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    header = ['Nº Ticket', '', 'Producto', 'Marca', 'Calidad', 'Estado', 'Terminación',
              'Orden de Producción', 'Esp.', 'Anc.', 'Lar.', 'Pzas Paq.',
              'Volumen Paq.', 'Cantidad Paquetes', 'CERTFOR', 'Defecto']
    row = ['TKT-0001', 'BLANKS', '', '', 'BLANKS A', 'SE', 'BLANKS', 'OP-1234',
           '31,75', '146,1', '4,877', 231, 5.226, 1, 'NO CERTIFICADO', 'S/D']
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for col, val in enumerate(row):
        ws.write(1, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xls_nota_venta_bytes():
    """XLS OLE2 tipo Nota de Venta/Packing: dimensiones combinadas (Esc. Fact)
    sin Espesor/Ancho/Largo separados, con precio y moneda."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet('NOTA VENTA')
    header = ['Etiqueta', '', 'Cat.Certific.', 'Esc. Fact', '', 'Pzas', 'VOL.',
              'Producto', 'Est.', 'Orden', 'Item', 'Marca', 'Precio', 'Moneda']
    row = ['FG-0001', '', 'SIN FSC', '5/4x5.3/8x16', '', 231, 4.997,
           'BLANKS 5/4X5.3/8', 'SE', 21176, 4, 'REF-1', 430, 'US$/M3']
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for col, val in enumerate(row):
        ws.write(1, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xls_multi_no_lote_bytes():
    """XLS OLE2: códigos distintos y SIN columna de lote explícito."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    header = ['Codigo', 'Producto', 'Cantidad', 'M3', 'Espesor', 'Ancho', 'Largo']
    rows = [
        ['C001', 'MADERA', 150, 3.8862, 38.1, 170, 4.05],
        ['C002', 'MADERA', 120, 2.5000, 38.1, 170, 4.05],
        ['C003', 'MADERA', 100, 1.8000, 38.1, 170, 4.05],
    ]
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for r, row in enumerate(rows, start=1):
        for col, val in enumerate(row):
            ws.write(r, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xls_multi_lote_block_bytes():
    """XLS OLE2: lote explícito solo en la primera fila (celda fusionada)."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    header = ['Codigo', 'Producto', 'Cantidad', 'M3', 'LOTE', 'Espesor', 'Ancho', 'Largo']
    rows = [
        ['C001', 'MADERA', 150, 3.8862, 'L-BLOCK', 38.1, 170, 4.05],
        ['C002', 'MADERA', 120, 2.5000, '', 38.1, 170, 4.05],
        ['C003', 'MADERA', 100, 1.8000, '', 38.1, 170, 4.05],
    ]
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for r, row in enumerate(rows, start=1):
        for col, val in enumerate(row):
            ws.write(r, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestGuiaProcessingExcelParser(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.partner = cls.env['res.partner'].create({'name': 'Excel Parser Supplier'})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)

    def _make_guia(self, name):
        return self.GuiaModel.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'compra',
            'rate_usd': 800.0,
        })

    def _attachment_from_bytes(self, content, name):
        """Crea un pseudo-attachment cuyo _full_path apunta a un archivo real."""
        suffix = os.path.splitext(name)[1]
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as fh:
            fh.write(content)
        att = SimpleNamespace(store_fname=os.path.basename(path))
        att._full_path = lambda sf: path
        return att

    def test_xls_ole2_usa_engine_xlrd(self):
        """XLS OLE2 se lee con pandas engine='xlrd', nunca openpyxl."""
        guia = self._make_guia('XLS-95083')
        attachment = self._attachment_from_bytes(_build_xls_bytes(), '95083.xls')

        engines = []
        real_read = gp_module.pd.read_excel

        def spy(*args, **kwargs):
            engines.append(kwargs.get('engine'))
            return real_read(*args, **kwargs)

        with patch.object(gp_module.pd, 'read_excel', side_effect=spy):
            result = guia._parse_excel_data_core(attachment)

        self.assertEqual(engines, ['xlrd'])
        self.assertEqual(len(result['lineas']), 1)

    def test_xlsx_usa_openpyxl_sin_pandas(self):
        """XLSX se lee con openpyxl (load_workbook), sin pandas."""
        guia = self._make_guia('XLSX-95083')
        attachment = self._attachment_from_bytes(_build_xlsx_bytes(), '95083.xlsx')

        with patch.object(gp_module.pd, 'read_excel') as mock_read:
            result = guia._parse_excel_data_core(attachment)

        mock_read.assert_not_called()
        self.assertEqual(len(result['lineas']), 1)

    def test_xls_ole2_no_file_is_not_zip(self):
        """El error 'File is not a zip file' de openpyxl sobre OLE2 no se propaga."""
        guia = self._make_guia('XLS-NOZIP')
        attachment = self._attachment_from_bytes(_build_xls_bytes(), '95083.xls')

        result = guia._parse_excel_data_core(attachment)

        self.assertEqual(len(result['lineas']), 1)
        self.assertEqual(result['lineas'][0]['Codigo Interno'], 'C001')
        self.assertAlmostEqual(result['lineas'][0]['Volumen'], 3.8862, places=4)

    def test_xls_blanks_abbreviated_headers(self):
        """Encabezado abreviado (Nº Ticket / Esp. / Pzas Paq. / Volumen Paq.)
        con decimales con coma se detecta genéricamente y produce una línea."""
        guia = self._make_guia('XLS-BLANKS')
        attachment = self._attachment_from_bytes(_build_xls_blanks_bytes(), 'blanks.xls')

        result = guia._parse_excel_data_core(attachment)

        self.assertEqual(len(result['lineas']), 1)
        line = result['lineas'][0]
        self.assertEqual(line['Codigo Interno'], 'TKT-0001')
        self.assertEqual(line['Cantidad'], 231)
        self.assertAlmostEqual(line['Volumen'], 5.226, places=3)
        self.assertAlmostEqual(line['Espesor'], 31.75, places=2)
        self.assertAlmostEqual(line['Ancho'], 146.1, places=1)
        self.assertAlmostEqual(line['Largo'], 4.877, places=3)

    def test_nota_venta_dimensions_raw_rejected_with_diagnostic(self):
        """Dimensiones combinadas (dimensions_raw) + identificador + cantidad +
        volumen documental: se sigue descartando con diagnóstico explícito y
        no se invoca cálculo geométrico (Opción C)."""
        guia = self._make_guia('XLS-NOTA-VENTA')
        attachment = self._attachment_from_bytes(
            _build_xls_nota_venta_bytes(), 'nota_venta.xls')

        result = guia._parse_excel_data_core(attachment)

        self.assertEqual(len(result['lineas']), 1)
        line = result['lineas'][0]
        self.assertEqual(line['Codigo Interno'], 'FG-0001')
        self.assertEqual(line['Cantidad'], 231)
        self.assertGreater(line['Volumen'], 0)
        self.assertEqual(line['dimensions_raw'], '5/4x5.3/8x16')
        self.assertEqual(line['Espesor'], 0)
        self.assertEqual(line['Ancho'], 0)
        self.assertEqual(line['Largo'], 0)

        # La validación descarta con REQUIERE_DIMENSIONES_SEPARADAS.
        rechazos = []
        validas = guia._validar_y_enriquecer_lineas(result['lineas'], rechazos)
        self.assertEqual(validas, [])
        self.assertEqual(len(rechazos), 1)
        self.assertEqual(rechazos[0]['rule'], 'REQUIERE_DIMENSIONES_SEPARADAS')
        self.assertEqual(rechazos[0]['fields'], ['Espesor', 'Ancho', 'Largo'])

        # Diagnóstico estructurado, no opaco.
        msg = guia._build_rejection_diagnostic(rechazos, len(result['lineas']))
        self.assertIn('REQUIERE_DIMENSIONES_SEPARADAS', msg)
        self.assertIn('dimensiones crudas: 5/4x5.3/8x16', msg)
        self.assertIn('volumen documental', msg)
        self.assertIn('No se creó ninguna línea', msg)

    def test_metric_dimensions_still_validate_and_create(self):
        """Regresión: un packing métrico con dimensiones separadas sigue
        validando y devolviendo vol_shipment_m3 calculado geométricamente."""
        guia = self._make_guia('XLS-METRIC-OK')
        lineas = [{
            'Codigo Interno': 'C001',
            'N° LOTE': 'L1',
            'Cantidad': 150,
            'Volumen': 3.8862,
            'Espesor': 38.1,
            'Ancho': 170.0,
            'Largo': 4.05,
        }]
        validas = guia._validar_y_enriquecer_lineas(lineas)
        self.assertEqual(len(validas), 1)
        self.assertIn('vol_shipment_m3', validas[0])
        self.assertGreater(validas[0]['vol_shipment_m3'], 0)

    def test_vol_documental_m3_written(self):
        """El volumen documental del detector se escribe en vol_documental_m3,
        sin tocar Volumen (comportamiento existente)."""
        guia = self._make_guia('XLS-VOLDOC')
        attachment = self._attachment_from_bytes(_build_xls_blanks_bytes(), 'blanks.xls')

        result = guia._parse_excel_data_core(attachment)

        line = result['lineas'][0]
        self.assertAlmostEqual(line['vol_documental_m3'], 5.226, places=3)
        self.assertAlmostEqual(line['Volumen'], 5.226, places=3)
        self.assertIsNone(result['declared_totals'])

    def test_packing_declared_totals_persisted(self):
        """Los totales de Packing (kind total) se persisten en los campos
        documentales planos y no tocan vol_comercial_pdf."""
        guia = self._make_guia('XLS-DECTOT')

        guia._persist_packing_declared_totals({
            'volume_m3': 42.132, 'pieces': 2244, 'package_count': 8,
            'kind': 'total', 'sheet': 'S1', 'row_index': 26,
        })

        self.assertAlmostEqual(guia.packing_volume_declared_m3, 42.132, places=3)
        self.assertEqual(guia.packing_pieces_declared, 2244)
        self.assertEqual(guia.packing_package_count_declared, 8)
        self.assertEqual(guia.vol_comercial_pdf, 0.0)

    def test_packing_declared_totals_subtotal_not_persisted(self):
        """Un subtotal NO se persiste como total de Packing."""
        guia = self._make_guia('XLS-SUBTOT')

        guia._persist_packing_declared_totals({
            'volume_m3': 9.0, 'pieces': 300, 'package_count': None,
            'kind': 'subtotal', 'sheet': 'S1', 'row_index': 4,
        })

        self.assertEqual(guia.packing_volume_declared_m3, 0.0)
        self.assertEqual(guia.packing_pieces_declared, 0)
        self.assertEqual(guia.packing_package_count_declared, 0)

    def test_documentary_lines_collected_not_dropped(self):
        """Una línea documental (identificador + piezas + volumen documental,
        sin dimensiones) se conserva como documental en lugar de descartarse."""
        guia = self._make_guia('XLS-COLLECT')
        lineas = [{
            'Codigo Interno': 'DOC-001',
            'N° LOTE': 'L1',
            'Cantidad': 100,
            'Volumen': 5.0,
            'vol_documental_m3': 5.0,
            'dimensions_raw': '5/4x5.3/8x16',
            'Espesor': 0.0,
            'Ancho': 0.0,
            'Largo': 0.0,
        }]
        documentales = []
        validas = guia._validar_y_enriquecer_lineas(lineas, None, documentales)
        self.assertEqual(validas, [])
        self.assertEqual(len(documentales), 1)
        self.assertEqual(documentales[0]['vol_documental_m3'], 5.0)
        self.assertEqual(documentales[0]['dimensions_raw'], '5/4x5.3/8x16')

    def test_documentary_pending_not_promoted(self):
        """Una línea documental pendiente en staging no se promueve a lote/stock
        y action_validate la rechaza."""
        guia = self._make_guia('XLS-DOCPEND')
        guia.state = 'verified'
        product = self.env['product.product'].search([], limit=1)
        self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'LOTE-DOC',
            'sku_original': 'DOC-001',
            'product_name_original': 'BLANKS',
            'product_id': product.id,
            'pieces': 100,
            'vol_documental_m3': 5.0,
            'espesor_mm': 0.0,
            'ancho_mm': 0.0,
            'largo_m': 0.0,
        })
        self.assertEqual(len(guia._documentary_pending_lines()), 1)
        with self.assertRaises(ValidationError):
            guia.action_validate()
        # No se creó ningún lote a partir de la línea documental.
        self.assertFalse(
            self.env['stock.lot'].search([('name', 'ilike', 'LOTE-DOC')]))

    def test_mixed_document_only_geometric_promoted(self):
        """Documento mixto: la línea geométrica se valida y la documental queda
        como pendiente (no se mezclan)."""
        guia = self._make_guia('XLS-MIXED')
        lineas = [
            {
                'Codigo Interno': 'GEO-001',
                'N° LOTE': 'L-GEO',
                'Cantidad': 150,
                'Volumen': 3.8862,
                'vol_documental_m3': 3.8862,
                'Espesor': 38.1,
                'Ancho': 170.0,
                'Largo': 4.05,
            },
            {
                'Codigo Interno': 'DOC-001',
                'N° LOTE': 'L-DOC',
                'Cantidad': 100,
                'Volumen': 5.0,
                'vol_documental_m3': 5.0,
                'Espesor': 0.0,
                'Ancho': 0.0,
                'Largo': 0.0,
            },
        ]
        documentales = []
        validas = guia._validar_y_enriquecer_lineas(lineas, None, documentales)
        self.assertEqual(len(validas), 1)
        self.assertEqual(validas[0]['Codigo Interno'], 'GEO-001')
        self.assertEqual(len(documentales), 1)
        self.assertEqual(documentales[0]['Codigo Interno'], 'DOC-001')

    def _make_documental_line(self, guia, code, vol_doc):
        product = self.env['product.product'].search([], limit=1)
        return self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'LOTE-%s' % code,
            'sku_original': code,
            'product_id': product.id,
            'pieces': 10,
            'vol_documental_m3': vol_doc,
            'espesor_mm': 0.0,
            'ancho_mm': 0.0,
            'largo_m': 0.0,
        })

    def test_sum_vol_documental_m3(self):
        """Suma el volumen documental por línea sin tocar totales geométricos."""
        guia = self._make_guia('XLS-SUMDOC')
        for code, vol in (('DOC-1', 2.0), ('DOC-2', 3.0), ('DOC-3', 4.0)):
            self._make_documental_line(guia, code, vol)
        guia.flush_recordset()
        self.assertAlmostEqual(guia.sum_vol_documental_m3, 9.0, places=3)
        self.assertEqual(guia.vol_comercial, 0.0)
        self.assertEqual(guia.vol_fisico, 0.0)
        self.assertEqual(guia.vol_total_m3, 0.0)

    def test_diff_pdf_packing_m3(self):
        """Diferencia PDF vs Packing; no toca diff_m3/diff_pct/diff_mbf."""
        guia = self._make_guia('XLS-DIFFPDF')
        guia.write({'vol_comercial_pdf': 60.0, 'packing_volume_declared_m3': 50.0})
        guia.flush_recordset()
        self.assertAlmostEqual(guia.diff_pdf_packing_m3, 10.0, places=3)
        self.assertEqual(guia.diff_m3, 0.0)
        self.assertEqual(guia.diff_pct, 0.0)

    def test_diff_packing_lineas_m3(self):
        """Diferencia Packing vs suma de líneas documentales."""
        guia = self._make_guia('XLS-DIFFPL')
        self._make_documental_line(guia, 'DOC-1', 30.0)
        guia.packing_volume_declared_m3 = 40.0
        guia.flush_recordset()
        self.assertAlmostEqual(guia.diff_packing_lineas_m3, 10.0, places=3)

    def test_no_documental_sources_geometric_unaffected(self):
        """Sin fuentes documentales: flujo geométrico y diferencias neutras."""
        guia = self._make_guia('XLS-NODOC')
        lineas = [{
            'Codigo Interno': 'C001',
            'N° LOTE': 'L1',
            'Cantidad': 150,
            'Volumen': 3.8862,
            'Espesor': 38.1,
            'Ancho': 170.0,
            'Largo': 4.05,
        }]
        validas = guia._validar_y_enriquecer_lineas(lineas)
        self.assertEqual(len(validas), 1)
        guia.flush_recordset()
        self.assertEqual(guia.sum_vol_documental_m3, 0.0)
        self.assertEqual(guia.diff_pdf_packing_m3, 0.0)
        self.assertEqual(guia.diff_packing_lineas_m3, 0.0)

    def test_documental_conciliation_state_not_available(self):
        guia = self._make_guia('XLS-CONC-NA')
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'not_available')

    def test_documental_conciliation_state_partial(self):
        guia = self._make_guia('XLS-CONC-PARTIAL')
        guia.write({'vol_comercial_pdf': 50.0})
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'partial')

    def test_documental_conciliation_state_two_sources_partial(self):
        guia = self._make_guia('XLS-CONC-PARTIAL2')
        guia.write({'vol_comercial_pdf': 50.0, 'packing_volume_declared_m3': 50.0})
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'partial')

    def test_documental_conciliation_state_consistent(self):
        guia = self._make_guia('XLS-CONC-OK')
        self._make_documental_line(guia, 'DOC-1', 50.0)
        guia.write({'vol_comercial_pdf': 50.0, 'packing_volume_declared_m3': 50.0})
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'consistent')
        # No afecta el estado operativo ni los diff geométricos.
        self.assertEqual(guia.state, 'draft')
        self.assertEqual(guia.diff_m3, 0.0)
        self.assertEqual(guia.diff_pct, 0.0)

    def test_documental_conciliation_state_difference(self):
        guia = self._make_guia('XLS-CONC-DIFF')
        self._make_documental_line(guia, 'DOC-1', 50.0)
        guia.write({'vol_comercial_pdf': 50.0, 'packing_volume_declared_m3': 60.0})
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'difference')
        # No modifica los diff documentales ni geométricos.
        self.assertAlmostEqual(guia.diff_pdf_packing_m3, -10.0, places=3)
        self.assertAlmostEqual(guia.diff_packing_lineas_m3, 10.0, places=3)
        self.assertEqual(guia.vol_comercial, 0.0)
        self.assertEqual(guia.vol_fisico, 0.0)
        self.assertEqual(guia.vol_total_m3, 0.0)

    def test_lote_sintetico_por_fila_no_se_propaga(self):
        """Códigos distintos sin lote explícito: cada línea recibe LOTE-{propio}."""
        guia = self._make_guia('XLS-LOTE-SYN')
        attachment = self._attachment_from_bytes(
            _build_xls_multi_no_lote_bytes(), 'multi_no_lote.xls')

        result = guia._parse_excel_data_core(attachment)

        self.assertEqual(len(result['lineas']), 3)
        lotes = [l['N° LOTE'] for l in result['lineas']]
        self.assertEqual(lotes, ['LOTE-C001', 'LOTE-C002', 'LOTE-C003'])

    def test_lote_explicito_forward_fill_preservado(self):
        """Lote explícito en primera fila se propaga a filas sin lote propio."""
        guia = self._make_guia('XLS-LOTE-FF')
        attachment = self._attachment_from_bytes(
            _build_xls_multi_lote_block_bytes(), 'multi_lote_block.xls')

        result = guia._parse_excel_data_core(attachment)

        self.assertEqual(len(result['lineas']), 3)
        lotes = [l['N° LOTE'] for l in result['lineas']]
        self.assertEqual(lotes, ['L-BLOCK', 'L-BLOCK', 'L-BLOCK'])



