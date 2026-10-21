# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from ..models.utils_uom import r3

class TestH5NominalWidthAndStockNotice(TransactionCase):
    """Pruebas para corrección E3 (ancho nominal en exportación) y aviso E4 (chatter en lote) (H5-C)."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].search([], limit=1)
        self.Subproducto = self.env['madenat.subproducto']
        self.Subproducto._init_calculation_families()

        self.sub_s2s = self.Subproducto.search([('calculation_family', '=', 's2s')], limit=1)
        self.sub_blank = self.Subproducto.search([('calculation_family', '=', 'blank')], limit=1)

        self.reception = self.env['lumber.reception'].create({
            'name': 'TEST-REC-H5',
        })
        self.guia_proc = self.env['madenat.guia.processing'].create({
            'name': 'TEST-PROC-H5',
        })

    def test_01_processing_line_nominal_width_edit_recalculates_export(self):
        """E3: Edición de ancho nominal 150 -> 140 mm recalcula compra (4.410) y exportación (3.387)."""
        line = self.env['madenat.guia.processing.line'].create({
            'lot_name': 'TEST-LOT-01',
            'processing_id': self.guia_proc.id,
            'product_id': self.product.id,
            'subproducto_id': self.sub_s2s.id,
            'espesor_mm': 45.0,
            'ancho_mm': 150.0,
            'largo_m': 4.0,
            'pieces': 175,
        })
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        line._compute_out_of_table_status()

        self.assertAlmostEqual(line.vol_purchase_m3, 4.725, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 3.895, places=3)
        self.assertFalse(line.is_out_of_table)

        # Editar 150 -> 140 mm
        line.ancho_nominal_mm = 140.0
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        line._compute_out_of_table_status()

        self.assertAlmostEqual(line.vol_purchase_m3, 4.410, places=3,
                               msg="Compra con ancho nominal 140 mm debe ser 4.410 m³")
        self.assertAlmostEqual(line.vol_shipment_m3, 3.387, places=3,
                               msg="Exportación con ancho nominal 140 mm debe ser 3.387 m³")

        # Volver a 150 mm
        line.ancho_nominal_mm = 150.0
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        self.assertAlmostEqual(line.vol_purchase_m3, 4.725, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 3.895, places=3)

    def test_02_processing_line_out_of_table_160mm_and_fallback(self):
        """E3: Ancho 160 mm fuera de tabla con exportación métrica y fallback a ancho_mm cuando vacío."""
        self.env['ir.config_parameter'].sudo().set_param('madenat.out_of_table_behavior', 'warning')
        line = self.env['madenat.guia.processing.line'].create({
            'lot_name': 'TEST-LOT-01',
            'processing_id': self.guia_proc.id,
            'product_id': self.product.id,
            'subproducto_id': self.sub_s2s.id,
            'espesor_mm': 45.0,
            'ancho_mm': 150.0,
            'largo_m': 4.0,
            'pieces': 175,
        })
        # Editar a 160 mm
        line.ancho_nominal_mm = 160.0
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        line._compute_out_of_table_status()

        self.assertTrue(line.is_out_of_table, "160 mm debe marcar fuera de tabla")
        self.assertEqual(line.out_of_table_status, 'out_of_table')
        self.assertAlmostEqual(line.vol_shipment_m3, 4.267, places=3,
                               msg="160 mm métrico directo debe dar 4.267 m³")

        # Ancho nominal vacío -> respaldo a ancho_mm (150.0)
        line.ancho_nominal_mm = 0.0
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        line._compute_out_of_table_status()
        self.assertFalse(line.is_out_of_table)
        self.assertAlmostEqual(line.vol_purchase_m3, 4.725, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 3.895, places=3)

    def test_03_processing_line_manual_override_prevails(self):
        """E3: Override manual de exportación prevalece sobre ancho nominal y ancho bruto."""
        line = self.env['madenat.guia.processing.line'].create({
            'lot_name': 'TEST-LOT-01',
            'processing_id': self.guia_proc.id,
            'product_id': self.product.id,
            'subproducto_id': self.sub_s2s.id,
            'espesor_mm': 45.0,
            'ancho_mm': 170.0,
            'ancho_nominal_mm': 160.0,
            'largo_m': 4.0,
            'pieces': 175,
            'export_width_manual_inches': 5.25,
            'export_width_manual_reason': 'Calibrado por control de calidad',
        })
        line._compute_imperial_values()
        line._compute_vol_purchase_m3()
        line._compute_vol_shipment_m3()
        line._compute_out_of_table_status()

        self.assertEqual(line.out_of_table_status, 'confirmed')
        # 1.5 * 5.25 * 4.0 * 175 / 1550.003 = 3.556
        self.assertAlmostEqual(line.vol_shipment_m3, 3.556, places=3)

    def test_04_blanks_unaffected(self):
        """E3: Blanks conservan compra = exportación (4.939 y 5.399)."""
        rec_blank = self.env['lumber.reception'].create({
            'name': 'TEST-REC-BLANKS-97183',
            'ingestion_profile': 'f5085',
        })
        # A1M2602499 = 4.939
        line_blank1 = self.env['lumber.reception.line'].create({
            'lot_name': 'A1M2602499',
            'reception_id': rec_blank.id,
            'product_id': self.product.id,
            'subproduct_id': self.sub_blank.id,
            'thickness': 45.0,
            'width': 142.875,
            'length': 4.88,
            'length_input_raw': 16.0,
            'pieces': 182,
            'thickness_visual': '6/4',
            'width_visual': '5 5/8',
            'export_calculation_rule': 'f5085',
        })
        line_blank1._compute_export_values()
        line_blank1._compute_volume_purchase()
        self.assertAlmostEqual(line_blank1.vol_purchase_m3, 4.939, places=3)
        self.assertAlmostEqual(line_blank1.vol_shipment_m3, 4.939, places=3)
        self.assertEqual(line_blank1.vol_purchase_m3, line_blank1.vol_shipment_m3)

        # A1F2692869 = 5.399 (416 pcs, 2 5/8", 16 ft)
        line_blank2 = self.env['lumber.reception.line'].create({
            'lot_name': 'A1F2692869',
            'reception_id': rec_blank.id,
            'product_id': self.product.id,
            'subproduct_id': self.sub_blank.id,
            'thickness': 45.0,
            'width': 66.675,
            'length': 4.88,
            'length_input_raw': 16.0,
            'pieces': 416,
            'thickness_visual': '6/4',
            'width_visual': '2 5/8',
            'export_calculation_rule': 'f5085',
        })
        line_blank2._compute_export_values()
        line_blank2._compute_volume_purchase()
        self.assertAlmostEqual(line_blank2.vol_purchase_m3, 5.399, places=3)
        self.assertAlmostEqual(line_blank2.vol_shipment_m3, 5.399, places=3)
        self.assertEqual(line_blank2.vol_purchase_m3, line_blank2.vol_shipment_m3)

    def test_05_stock_lot_post_intake_edit_triggers_chatter_notice(self):
        """E4: Modificación de piezas o ancho en lote pos-envío no recalcula y registra en chatter."""
        lot = self.env['stock.lot'].create({
            'name': 'TEST-LOT-H5-E4',
            'product_id': self.product.id,
            'subproducto_id': self.sub_s2s.id,
            'reception_id': self.reception.id,
            'espesor_mm': 45.0,
            'ancho_mm': 150.0,
            'largo_m': 4.0,
            'piezas': 175,
            'volume_purchase_m3': 4.725,
            'volumen_m3': 4.725,
            'vol_shipment_m3': 3.895,
        })
        initial_vol = lot.vol_shipment_m3

        # Modificar piezas a 200
        lot.write({'piezas': 200})

        # Volumen debe permanecer invariable por la salvaguarda de staging
        self.assertEqual(lot.vol_shipment_m3, initial_vol, "Volumen no debe recalcularse pos-envío")

        # Debe registrar aviso en el chatter
        expected_phrase = "dimensiones modificadas después del ingreso; el volumen no se recalculó"
        found = any(expected_phrase in (msg.body or '') for msg in lot.message_ids)
        self.assertTrue(found, f"Debe encontrarse '{expected_phrase}' en el chatter del lote")

    def test_06_reception_line_nominal_width_support(self):
        """Verifica que lumber.reception.line ya soporta width_nominal."""
        rec_s2s = self.env['lumber.reception'].create({
            'name': 'TEST-REC-S2S',
            'ingestion_profile': 'f1550',
        })
        line = self.env['lumber.reception.line'].create({
            'lot_name': 'TEST-REC-01',
            'reception_id': rec_s2s.id,
            'product_id': self.product.id,
            'subproduct_id': self.sub_s2s.id,
            'thickness': 45.0,
            'width': 150.0,
            'length': 4.0,
            'pieces': 175,
            'export_calculation_rule': 'f1550',
        })
        line._compute_export_values()
        line._compute_volume_purchase()
        self.assertAlmostEqual(line.vol_purchase_m3, 4.725, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 3.895, places=3)

        line.width_nominal = 140.0
        line._compute_export_values()
        line._compute_volume_purchase()
        self.assertAlmostEqual(line.vol_purchase_m3, 4.410, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 3.387, places=3)
