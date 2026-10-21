# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestShipmentLineExportWidth(TransactionCase):
    """Pruebas unitarias de propagación de ancho de exportación y override manual en lumber.shipment.line (H4 / AD-130)."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Cliente Test Emb H4'})
        self.product = self.env['product.product'].search([], limit=1)
        self.shipment = self.env['lumber.export.shipment'].create({
            'name': 'EXP-TEST-OVERRIDE-LOG',
            'customer_id': self.partner.id,
        })
        self.container = self.env['lumber.container'].create({
            'name': 'CONT-TEST-01-LOG',
            'shipment_id': self.shipment.id,
        })

    def test_shipment_line_propagates_manual_override(self):
        """Punto 2.7: Respeta y propaga export_width_manual_inches y reason al embarque."""
        lot_manual = self.env['stock.lot'].create({
            'name': 'LOT-MANUAL-LOG-01',
            'product_id': self.product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 170.0,
            'largo_m': 4.0,
            'piezas': 150,
            'export_width_manual_inches': 6.75,
            'export_width_manual_reason': 'Override justificado para embarque',
        })
        lot_manual._compute_out_of_table_status()

        ship_line = self.env['lumber.shipment.line'].create({
            'shipment_id': self.shipment.id,
            'container_id': self.container.id,
            'lot_id': lot_manual.id,
        })
        ship_line._compute_export_dims()

        self.assertAlmostEqual(ship_line.export_width_manual_inches, 6.75, places=3)
        self.assertEqual(ship_line.export_width_manual_reason, 'Override justificado para embarque')
        self.assertEqual(ship_line.out_of_table_status, 'confirmed')
        self.assertAlmostEqual(ship_line.export_width_inches, 6.75, places=3)
