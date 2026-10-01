# -*- coding: utf-8 -*-
"""Evidencia documental en la consola y fachada (Procesado).

Cubre:
- Proxies documentales read-only de la consola (FASE 2).
- Estado visual 'documental_pending' para guías 100% documentales (FASE 3).
- Guía mixta: review_state permanece 'ready' con documental_pending_count > 0.
- XML de consola/fachada contiene los campos documentales y de detalle.
"""
from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestDocumentalConsole(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.Product = cls.env['product.product']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Documental Console', 'is_company': True})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.product = cls.Product.search([], limit=1)

    def _make_guia(self, name='G-DOC-CONS'):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'service',
            'state': 'verified',
        })

    def _make_documental_line(self, guia, code, vol_doc, pieces=100):
        return self.Line.create({
            'processing_id': guia.id,
            'lot_name': 'LOTE-%s' % code,
            'sku_original': code,
            'product_id': self.product.id,
            'pieces': pieces,
            'vol_documental_m3': vol_doc,
            'espesor_mm': 0.0,
            'ancho_mm': 0.0,
            'largo_m': 0.0,
        })

    def _make_geometric_line(self, guia, code):
        return self.Line.create({
            'processing_id': guia.id,
            'lot_name': 'LOTE-%s' % code,
            'sku_original': code,
            'product_id': self.product.id,
            'pieces': 150,
            'vol_documental_m3': 0.0,
            'espesor_mm': 38.1,
            'ancho_mm': 170.0,
            'largo_m': 4.05,
            'espesor_nominal_mm': 25.0,
        })

    def _console_for(self, guia):
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])

    def _assert_view_has_fields(self, xmlid, field_names):
        view = self.env.ref(xmlid)
        root = etree.fromstring(view.arch)
        for name in field_names:
            self.assertTrue(
                root.xpath("//field[@name='%s']" % name),
                'Campo %s no encontrado en %s' % (name, xmlid))

    def test_console_proxies_reflect_source(self):
        """Los proxies documentales reflejan la guía origen sin escribirla."""
        guia = self._make_guia('G-DOC-PROXY')
        self._make_documental_line(guia, 'FG-001', 25.0)
        self._make_documental_line(guia, 'FG-002', 25.0)
        guia.write({
            'vol_comercial_pdf': 60.0,
            'packing_volume_declared_m3': 50.0,
            'packing_pieces_declared': 462,
            'packing_package_count_declared': 2,
        })
        guia.flush_recordset()

        console = self._console_for(guia)
        self.assertEqual(len(console), 1)
        self.assertEqual(console.ingestion_type, 'processed')
        self.assertAlmostEqual(console.vol_comercial_pdf, 60.0, places=3)
        self.assertAlmostEqual(console.packing_volume_declared_m3, 50.0, places=3)
        self.assertAlmostEqual(console.sum_vol_documental_m3, 50.0, places=3)
        self.assertAlmostEqual(console.diff_pdf_packing_m3, 10.0, places=3)
        self.assertAlmostEqual(console.diff_packing_lineas_m3, 0.0, places=3)
        self.assertEqual(console.documental_conciliation_state, 'difference')
        self.assertEqual(console.packing_pieces_declared, 462)
        self.assertEqual(console.packing_package_count_declared, 2)
        # Los proxies son read-only: la guía origen no cambió.
        self.assertAlmostEqual(guia.vol_comercial_pdf, 60.0, places=3)

    def test_console_100_documental_pending_state(self):
        """Guía 100% documental: review_state = documental_pending."""
        guia = self._make_guia('G-DOC-ALL')
        self._make_documental_line(guia, 'FG-001', 25.0)
        self._make_documental_line(guia, 'FG-002', 25.0)
        guia.flush_recordset()

        console = self._console_for(guia)
        self.assertEqual(len(console), 1)
        self.assertEqual(console.review_state, 'documental_pending')
        self.assertEqual(console.documental_pending_count, 2)
        # No altera la fuente: la guía sigue verified y sin lotes de stock.
        self.assertEqual(guia.state, 'verified')
        self.assertEqual(len(guia._documentary_pending_lines()), 2)

    def test_console_mixed_ready_with_pending_count(self):
        """Guía mixta: review_state permanece ready con pendientes > 0."""
        guia = self._make_guia('G-DOC-MIX')
        self._make_geometric_line(guia, 'GEO-001')
        self._make_documental_line(guia, 'DOC-001', 5.0)
        guia.flush_recordset()

        console = self._console_for(guia)
        self.assertEqual(len(console), 1)
        self.assertEqual(console.review_state, 'ready')
        self.assertEqual(console.documental_pending_count, 1)

    def test_console_view_contains_documental_fields(self):
        self._assert_view_has_fields(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form',
            ['vol_comercial_pdf', 'packing_volume_declared_m3',
             'sum_vol_documental_m3', 'diff_pdf_packing_m3',
             'diff_packing_lineas_m3', 'documental_conciliation_state',
             'packing_pieces_declared', 'packing_package_count_declared',
             'documental_pending_count', 'sku_original', 'raw_dims',
             'vol_documental_m3'])

    def test_facade_view_contains_documental_fields(self):
        self._assert_view_has_fields(
            'madenat_lumber_intake.view_madenat_guia_processing_intake_facade_form',
            ['vol_comercial_pdf', 'packing_volume_declared_m3',
             'sum_vol_documental_m3', 'diff_pdf_packing_m3',
             'diff_packing_lineas_m3', 'documental_conciliation_state',
             'packing_pieces_declared', 'packing_package_count_declared',
             'sku_original', 'raw_dims', 'vol_documental_m3'])
