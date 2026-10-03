# -*- coding: utf-8 -*-
"""Pruebas del detector genérico de tablas Excel (helper puro, sin ORM).

Cubre:
- Normalización y matching semántico (compuestos antes que simples).
- Estructura tipo 95083 (portada, encabezado con abreviaturas, filas vacías,
  decimales con coma, total desalineado) sin hardcodear 95083 ni filas/columnas.
- Encabezado de dos filas (N°|CODIGOS|… + PQTE.|mm.|…).
- Exclusión de totales/subtotales.
- Formato Procesado (tipo 26270).
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_core.models.excel_table_detection import (
    detect_excel_table,
    detect_excel_table_across_sheets,
    normalize_header,
    _match_field,
)


@tagged('post_install', '-at_install', 'madenat', 'excel_table_detection')
class TestExcelTableDetection(TransactionCase):

    def test_normalize_header(self):
        self.assertEqual(normalize_header('Nº Ticket'), 'n ticket')
        self.assertEqual(normalize_header('N° Ticket'), 'n ticket')
        self.assertEqual(normalize_header('No. Ticket'), 'n ticket')
        self.assertEqual(normalize_header('N. Ticket'), 'n ticket')
        self.assertEqual(normalize_header('Esp.'), 'esp')
        self.assertEqual(normalize_header('Anc.'), 'anc')
        self.assertEqual(normalize_header('Lar.'), 'lar')
        self.assertEqual(normalize_header('Pzas Paq.'), 'pzas paq')
        self.assertEqual(normalize_header('M³'), 'm3')
        self.assertEqual(normalize_header('Orden de Producción'), 'orden de produccion')

    def test_semantic_matching_compound_first(self):
        self.assertEqual(_match_field('pzas paq')[0], 'pieces')
        self.assertEqual(_match_field('cantidad paquetes')[0], 'package_count')
        self.assertEqual(_match_field('volumen paq')[0], 'volume_m3')
        self.assertEqual(_match_field('orden de produccion')[0], 'production_order')
        self.assertEqual(_match_field('esp')[0], 'thickness')
        self.assertEqual(_match_field('anc')[0], 'width')
        self.assertEqual(_match_field('lar')[0], 'length')
        self.assertEqual(_match_field('n ticket')[0], 'ticket_code')
        self.assertEqual(_match_field('codigo interno')[0], 'product_code')

    def _packing_list_blanks_rows(self):
        return [
            [None, None, None, None, None, None, 'PACKING LIST'],
            [None],
            [None, None, None, None, None, 'GUIA Nº:', 'G-0001'],
            [None],
            [None, None, None, None, 'CLIENTE:', None, 'COMPRADOR GENERICO'],
            [None, None, None, None, 'FECHA:', None, '01/01/2026'],
            [None],
            ['Nº Ticket', None, 'Producto', 'Marca', 'Calidad', 'Estado',
             'Terminación', 'Orden de Producción', 'Esp.', 'Anc.', 'Lar.',
             'Pzas Paq.', 'Volumen Paq.', 'Cantidad Paquetes', 'CERTFOR', 'Defecto'],
            [None],
            [None],
            ['TKT-0001', 'BLANKS', None, None, 'BLANKS A', 'SE', 'BLANKS',
             'OP-1234', '31,75', '146,1', '4,877', 231, 5.226, 1, 'NO CERTIFICADO', 'S/D'],
            ['TKT-0002', 'BLANKS', None, None, 'BLANKS A', 'SE', 'BLANKS',
             'OP-1234', '31,75', '146,1', '4,877', 231, 5.226, 1, 'NO CERTIFICADO', 'S/D'],
            [None],
            [None, None, None, None, None, None, None, 'TOTAL', 462, None, None, None,
             10.452, 2],
        ]


    def test_packing_list_blanks_structure(self):
        rows = self._packing_list_blanks_rows()
        res = detect_excel_table(rows, flow='procesado')

        self.assertEqual(res['confidence'], 'high')
        self.assertTrue(res['header_rows'])
        self.assertIn('ticket_code', res['field_columns'])
        self.assertIn('thickness', res['field_columns'])
        self.assertIn('pieces', res['field_columns'])
        self.assertIn('package_count', res['field_columns'])
        self.assertIn('production_order', res['field_columns'])

        self.assertEqual(len(res['lines']), 2)
        first = res['lines'][0]
        self.assertEqual(first['ticket_code'], 'TKT-0001')
        self.assertEqual(first['thickness'], 31.75)
        self.assertEqual(first['width'], 146.1)
        self.assertEqual(first['length'], 4.877)
        self.assertEqual(first['pieces'], 231.0)
        self.assertEqual(first['volume_m3'], 5.226)
        self.assertEqual(first['package_count'], 1.0)
        self.assertEqual(first['production_order'], 'OP-1234')

    def test_packing_list_blanks_no_fabricated_description(self):
        rows = self._packing_list_blanks_rows()
        res = detect_excel_table(rows, flow='procesado')
        first = res['lines'][0]
        self.assertNotIn('description', first)
        self.assertNotIn('product_code', first)

    def test_total_row_never_becomes_line(self):
        rows = self._packing_list_blanks_rows()
        res = detect_excel_table(rows, flow='procesado')
        codes = [l['ticket_code'] for l in res['lines']]
        self.assertEqual(codes, ['TKT-0001', 'TKT-0002'])

    def test_two_row_header(self):
        rows = [
            ['', '', '', '', 'CLIENTE', '', 'X'],
            ['', '', '', '', 'N°', 'CODIGOS', 'PRODUCTO', 'ESPESOR', 'ANCHO',
             'LARGO', 'FILAS', 'COLUMNAS', 'PIEZAS', 'VOLUMEN'],
            ['', '', '', '', 'PQTE.', '', '', 'mm.', 'mm', 'mm', '', '', '', 'M3'],
            ['', '', '', '', 1, '0000000134008', 'MADERA SECA CEPILLADA', 45,
             125, 4.0, 25, 8, 200, 4.5],
            ['', '', '', '', 2, '0000000133976', 'MADERA SECA CEPILLADA', 45,
             125, 4.0, 25, 8, 200, 4.5],
        ]
        res = detect_excel_table(rows, flow='producto')
        self.assertEqual(res['confidence'], 'high')
        self.assertEqual(len(res['header_rows']), 2)
        self.assertIn('lot_or_package', res['field_columns'])
        self.assertIn('product_code', res['field_columns'])
        self.assertIn('pieces', res['field_columns'])
        self.assertEqual(len(res['lines']), 2)
        self.assertEqual(res['lines'][0]['product_code'], '0000000134008')
        self.assertEqual(res['lines'][0]['pieces'], 200.0)

    def test_procesado_format(self):
        rows = [
            ['FACTURACION SERVICIO CEPILLADO'],
            ['ORDEN DE COMPRA', 'OC-1'],
            ['Cliente:', 'X'],
            ['N° Guía de Despacho:', 'G-0002'],
            ['Item', 'Codigo Interno', 'Producto', 'Espesor', 'Ancho', 'Largo',
             'Cantidad', 'M3', 'Embalaje', 'N° LOTE', 'Producción'],
            [1, 'PCLAT03301253700', 'PINO CEP. SECO LATERAL', 37, 125, 3700,
             264, 4.5177, 'Taco', 'D8828', '2026-09-01'],
            [2, 'PCLAT03301254050', 'PINO CEP. SECO LATERAL', 37, 125, 4050,
             264, 4.945, 'Taco', 'D8830', '2026-09-01'],
            ['TOTAL:', 528, 9.4627],
        ]
        res = detect_excel_table(rows, flow='procesado')
        self.assertEqual(res['confidence'], 'high')
        self.assertIn('product_code', res['field_columns'])
        self.assertIn('description', res['field_columns'])
        self.assertIn('lot_or_package', res['field_columns'])
        self.assertEqual(len(res['lines']), 2)
        self.assertEqual(res['lines'][0]['product_code'], 'PCLAT03301253700')
        self.assertEqual(res['lines'][0]['description'], 'PINO CEP. SECO LATERAL')
        self.assertEqual(res['lines'][0]['lot_or_package'], 'D8828')

    def test_no_table_low_confidence(self):
        rows = [['hola'], ['mundo'], [1, 2, 3]]
        res = detect_excel_table(rows, flow='procesado')
        self.assertEqual(res['confidence'], 'low')
        self.assertEqual(res['lines'], [])

    def test_across_sheets_picks_best(self):
        packing = [
            ['Item', 'Codigo Interno', 'Producto', 'Cantidad', 'M3', 'N° LOTE'],
            [1, 'C001', 'MADERA', 100, 3.0, 'L1'],
            [2, 'C002', 'MADERA', 100, 3.0, 'L2'],
        ]
        pivot = [['Codigo Interno', 'Cantidad'], ['C001', 100]]
        sheets = [('Resumen', pivot), ('Packing', packing)]
        res = detect_excel_table_across_sheets(sheets, flow='procesado')
        self.assertEqual(res['sheet'], 'Packing')
        self.assertEqual(res['confidence'], 'high')

    def test_nota_venta_concepts(self):
        """Conceptos de negocio de una Nota de Venta/Packing con dimensiones
        combinadas y precio/moneda, detectados por contenido (sin hardcode)."""
        rows = [
            ['NOTA DE VENTA INTERNA/PACKING LIST.'],
            ['Nº:', 'NV-0001'],
            ['Etiqueta', '', 'Cat.Certific.', 'Esc. Fact', '', 'Pzas', 'VOL.',
             'Producto', 'Est.', 'Orden', 'Item', 'Marca', 'Precio', 'Moneda'],
            ['FG-0001', '', 'SIN FSC', '5/4x5.3/8x16', '', 231, 4.997,
             'BLANKS 5/4X5.3/8', 'SE', 21176, 4, 'REF-1', 430, 'US$/M3'],
            ['FG-0002', '', 'SIN FSC', '5/4x5.3/8x16', '', 231, 4.997,
             'BLANKS 5/4X5.3/8', 'SE', 21176, 4, 'REF-1', 430, 'US$/M3'],
        ]
        res = detect_excel_table(rows, flow='procesado')
        self.assertEqual(res['confidence'], 'high')
        self.assertIn('dimensions_raw', res['field_columns'])
        self.assertIn('document_item', res['field_columns'])
        self.assertIn('reference', res['field_columns'])
        self.assertIn('currency_or_unit', res['field_columns'])
        self.assertIn('certificate', res['field_columns'])
        self.assertIn('price', res['field_columns'])
        self.assertNotIn('thickness', res['field_columns'])

        first = res['lines'][0]
        self.assertEqual(first['dimensions_raw'], '5/4x5.3/8x16')
        self.assertIsInstance(first['dimensions_raw'], str)
        self.assertEqual(first['certificate'], 'SIN FSC')
        self.assertEqual(first['currency_or_unit'], 'US$/M3')
        self.assertEqual(first['reference'], 'REF-1')
        self.assertEqual(first['price'], 430.0)

    def test_certificate_variants(self):
        """certificate se reconoce con variantes normalizadas (Cat. Certific.,
        CERTFOR, Certificación) sin romper el scoring."""
        for header, expected in (
            ('Cat.Certific.', 'certificate'),
            ('CERTFOR', 'certificate'),
            ('Certificación', 'certificate'),
        ):
            field, _score = _match_field(normalize_header(header))
            self.assertEqual(field, expected, header)

    def test_dimensions_raw_never_becomes_float(self):
        rows = [
            ['Esc. Fact', 'Pzas', 'VOL.'],
            ['5/4x5.3/8x16', 231, 4.997],
            ['5/4x5.3/8x16', 231, 4.997],
        ]
        res = detect_excel_table(rows, flow='procesado')
        first = res['lines'][0]
        self.assertIsInstance(first['dimensions_raw'], str)
        self.assertEqual(first['dimensions_raw'], '5/4x5.3/8x16')
        self.assertEqual(first['volume_m3'], 4.997)
        self.assertEqual(first['pieces'], 231.0)


    def test_declared_totals_aligned(self):
        """Total alineado a las columnas semánticas se captura en
        declared_totals y nunca se convierte en línea."""
        rows = [
            ['Producto', 'Cantidad', 'M3', 'N° LOTE'],
            ['MADERA', 100, 3.0, 'L1'],
            ['MADERA', 200, 6.0, 'L2'],
            ['TOTAL', 300, 9.0],
        ]
        res = detect_excel_table(rows, flow='procesado')
        self.assertEqual(res['confidence'], 'high')
        self.assertEqual(len(res['lines']), 2)
        self.assertEqual(res['declared_totals']['kind'], 'total')
        self.assertEqual(res['declared_totals']['volume_m3'], 9.0)
        self.assertEqual(res['declared_totals']['pieces'], 300)

    def test_declared_totals_subtotal_kind(self):
        rows = [
            ['Producto', 'Cantidad', 'M3'],
            ['MADERA', 100, 3.0],
            ['MADERA', 200, 6.0],
            ['SUBTOTAL', 300, 9.0],
        ]
        res = detect_excel_table(rows, flow='procesado')
        self.assertEqual(res['declared_totals']['kind'], 'subtotal')

    def test_declared_totals_ambiguous_warns(self):
        """Total desalineado con rótulo→valor intercalado: el valor ambiguo no
        se persiste y se emite warning."""
        rows = [
            ['Etiqueta', 'Pzas', 'VOL.', 'Producto'],
            ['FG-1', 231, 4.997, 'BLANKS'],
            ['FG-2', 231, 4.997, 'BLANKS'],
            [12, 'Reg.', 'TOTAL', 12, 'Pqts', 462, 'Piezas', 9.994, 'Volumen', 'M3'],
        ]
        res = detect_excel_table(rows, flow='procesado')
        self.assertIsNotNone(res['declared_totals'])
        self.assertEqual(res['declared_totals']['kind'], 'total')
        # package_count es ambiguo (12 y 462 como vecinos de 'Pqts') → None.
        self.assertIsNone(res['declared_totals']['package_count'])
        self.assertTrue(
            any('ambiguo' in w for w in res['warnings']))
