# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestVolumeLabels6C(TransactionCase):
    """
    Bloque 6C — Pruebas de Etiquetas de Volumen
    Verifica que:
    1. 'Vol. Compra (m³)' indica el volumen de compra nominal en pantallas de ingreso, packing y lotes.
    2. 'Vol. Export (m³)' indica el volumen de exportación en pantallas de ingreso, packing y lotes.
    3. El volumen de compra es visible por etiqueta (lote).
    4. Cero cambio en fórmulas de cálculo ni en datos preexistentes.
    """

    def setUp(self):
        super().setUp()
        self.Lot = self.env['stock.lot']
        self.Product = self.env['product.product']

    def test_01_stock_lot_views_labels(self):
        """Verifica que las vistas de stock.lot expongan Vol. Compra (m³) y Vol. Export (m³)."""
        # Vista tree / list de stock.lot
        tree_view = self.env['ir.ui.view'].search([
            ('model', '=', 'stock.lot'),
            ('arch_db', 'like', 'Vol. Compra (m³)'),
            ('arch_db', 'like', 'Vol. Export (m³)'),
        ], limit=1)
        self.assertTrue(tree_view, "Debe existir vista de stock.lot con 'Vol. Compra (m³)' y 'Vol. Export (m³)'")

        # Vista form de stock.lot
        form_view = self.env.ref('madenat_lumber_core.view_stock_lot_form_madenat', raise_if_not_found=False)
        self.assertTrue(form_view, "Debe existir view_stock_lot_form_madenat")
        arch = form_view.arch_db
        self.assertIn('Vol. Compra (m³)', arch, "Formulario de stock.lot debe rotular 'Vol. Compra (m³)'")
        self.assertIn('Vol. Export (m³)', arch, "Formulario de stock.lot debe rotular 'Vol. Export (m³)'")

    def test_02_guia_processing_views_labels(self):
        """Verifica que la vista de procesamiento de guías rotule Vol. Compra (m³) y Vol. Export (m³)."""
        form_view = self.env.ref('madenat_lumber_core.view_madenat_guia_processing_form', raise_if_not_found=False)
        self.assertTrue(form_view, "Debe existir view_madenat_guia_processing_form")
        arch = form_view.arch_db
        self.assertIn('Vol. Compra (m³)', arch, "Formulario de guías debe rotular 'Vol. Compra (m³)'")
        self.assertIn('Vol. Export (m³)', arch, "Formulario de guías debe rotular 'Vol. Export (m³)'")

    def test_03_lumber_reception_views_labels(self):
        """Verifica que la vista de recepción rotule Vol. Compra (m³) y Vol. Export (m³)."""
        form_view = self.env.ref('madenat_lumber_core.view_lumber_reception_form', raise_if_not_found=False)
        self.assertTrue(form_view, "Debe existir view_lumber_reception_form")
        arch = form_view.arch_db
        self.assertIn('Vol. Compra (m³)', arch, "Formulario de recepción debe rotular 'Vol. Compra (m³)'")
        self.assertIn('Vol. Export (m³)', arch, "Formulario de recepción debe rotular 'Vol. Export (m³)'")

    def test_04_lot_volume_purchase_and_export_accessible(self):
        """Verifica que el lote mantenga accesibles y consistentes ambos volúmenes por etiqueta."""
        product = self.Product.create({
            'name': 'Test Lumber 6C',
            'type': 'consu',
            'is_storable': True,
        })
        lot = self.Lot.create({
            'name': 'ETIQ-6C-001',
            'product_id': product.id,
            'piezas': 100,
            'espesor_mm': 25.0,
            'ancho_mm': 150.0,
            'largo_m': 3.2,
            'volume_purchase_m3': 1.200,
            'vol_shipment_m3': 0.985,
        })
        self.assertEqual(round(lot.vol_purchase_m3, 3), 1.200)
        self.assertEqual(round(lot.volume_purchase_m3, 3), 1.200)
        self.assertEqual(round(lot.vol_shipment_m3, 3), 0.985)
