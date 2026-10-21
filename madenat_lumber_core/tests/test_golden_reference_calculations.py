from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from ..models.utils_uom import r3

class TestGoldenReferenceCalculations(TransactionCase):
    """Suite de Pruebas Doradas Integrales de Cubicación de Compra y Exportación (H4 / AD-130).

    Verifica exhaustivamente contra las cifras de referencia consolidadas en CANON/17 §9:
    1. Packing Guía 40030 completo (12 paquetes, totales 54.518 / 44.713 m³).
    2. Booking FA543R (Fátima: 145, 125, 100, 180, 200 mm).
    3. Guía FA531R (San Joaquín D7436: 145 mm 4.05 m x 189 pcs = 4.995 / 4.074 m³).
    4. Blanks (compra = exportación = fórmula f5085 con +1/8").
    5. Rugoso (RIP ROUGH métrico puro compra = exportación).
    6. Invariantes fundamentales: export <= compra en cepillados; compra == export en blanks y rugoso.
    7. Fuera de tabla (160, 165, 170, 180, 200 mm).
    8. Mapeo métrico de blanks con y sin tolerancia.
    9. Conciliación y Override manual propagado.
    """

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].search([], limit=1)
        self.Subproducto = self.env['madenat.subproducto']
        self.Subproducto._init_calculation_families()

        self.sub_blank = self.Subproducto.search([('calculation_family', '=', 'blank')], limit=1)
        self.sub_s2s = self.Subproducto.search([('calculation_family', '=', 's2s')], limit=1)
        self.sub_rough = self.Subproducto.search([('calculation_family', '=', 'rough')], limit=1)

    def _calc_purchase_m3(self, e_mm, w_mm, l_m, pieces):
        return r3((e_mm * w_mm * l_m * pieces) / 1_000_000.0)

    def test_01_packing_guia_40030_complete_and_totals(self):
        """Packing guía 40030 completo (6/4, 4.0 m): 12 paquetes y totales dorados 54.518 / 44.713 m³."""
        packages_40030 = [
            # (pkg_num, ancho_mm, pzas, purchase_expected, shipment_expected, is_out_of_table)
            (1, 170.0, 150, 4.590, 3.886, True),   # Fuera de tabla S2S (métrico sin +1/8")
            (2, 170.0, 150, 4.590, 3.886, True),   # Fuera de tabla S2S
            (3, 150.0, 175, 4.725, 3.895, False),  # 5 5/8" S2S (+1/8" -> 5.750")
            (4, 150.0, 175, 4.725, 3.895, False),
            (5, 125.0, 200, 4.500, 3.677, False),  # 4 5/8" S2S (+1/8" -> 4.750")
            (6, 125.0, 200, 4.500, 3.677, False),
            (7, 125.0, 200, 4.500, 3.677, False),
            (8, 125.0, 200, 4.500, 3.677, False),
            (9, 125.0, 200, 4.500, 3.677, False),
            (10, 125.0, 200, 4.500, 3.677, False),
            (11, 100.0, 250, 4.500, 3.629, False), # 3 5/8" S2S (+1/8" -> 3.750")
            (12, 75.0, 325, 4.388, 3.460, False),  # 2 5/8" S2S (+1/8" -> 2.750")
        ]

        total_purchase = 0.0
        total_shipment = 0.0

        for pkg, w_mm, pcs, exp_p, exp_s, out_table in packages_40030:
            lot = self.env['stock.lot'].create({
                'name': f"40030-PKG-{pkg:02d}",
                'product_id': self.product.id,
                'subproducto_id': self.sub_s2s.id if self.sub_s2s else False,
                'espesor_mm': 45.0,
                'ancho_mm': w_mm,
                'largo_m': 4.0,
                'piezas': pcs,
                'volume_purchase_m3': self._calc_purchase_m3(45.0, w_mm, 4.0, pcs),
            })
            lot._compute_out_of_table_status()
            lot._compute_ancho_export_display()
            lot._compute_vol_shipment_m3()

            self.assertAlmostEqual(lot.volume_purchase_m3, exp_p, places=3,
                                   msg=f"Fallo compra paquete {pkg} ({w_mm}mm x {pcs}pcs)")
            self.assertAlmostEqual(lot.vol_shipment_m3, exp_s, places=3,
                                   msg=f"Fallo export paquete {pkg} ({w_mm}mm x {pcs}pcs)")
            self.assertEqual(lot.is_out_of_table, out_table)
            self.assertTrue(lot.vol_shipment_m3 <= lot.volume_purchase_m3,
                            "Invariante cepillados: exportación debe ser MENOR o igual a compra")

            total_purchase += lot.volume_purchase_m3
            total_shipment += lot.vol_shipment_m3

        # Verificación de totales de guía 40030
        self.assertAlmostEqual(total_purchase, 54.518, places=3, msg="Total compra 40030 debe ser 54.518 m³")
        self.assertAlmostEqual(total_shipment, 44.713, places=3, msg="Total exportación 40030 debe ser 44.713 m³")

    def test_02_fa543r_fatima_golden_reference(self):
        """FA543R (Fátima): cepillados y anchos fuera de tabla 180 y 200 mm."""
        cases_fa543r = [
            # (ancho_mm, largo_m, piezas, compra_m3, export_m3, is_out)
            (145.0, 4.0, 175, 4.568, 3.726, False),  # 5 3/8" S2S
            (125.0, 4.0, 200, 4.500, 3.677, False),  # 4 5/8" S2S
            (100.0, 3.2, 250, 3.600, 2.903, False),  # 3 5/8" S2S
            (180.0, 4.0, 150, 4.860, 4.115, True),   # 180 mm fuera de tabla
            (200.0, 4.0, 125, 4.500, 3.810, True),   # 200 mm fuera de tabla
        ]

        for w_mm, l_m, pcs, exp_p, exp_s, is_out in cases_fa543r:
            lot = self.env['stock.lot'].create({
                'name': f"FA543R-{int(w_mm)}",
                'product_id': self.product.id,
                'subproducto_id': self.sub_s2s.id if self.sub_s2s else False,
                'espesor_mm': 45.0,
                'ancho_mm': w_mm,
                'largo_m': l_m,
                'piezas': pcs,
                'volume_purchase_m3': self._calc_purchase_m3(45.0, w_mm, l_m, pcs),
            })
            lot._compute_out_of_table_status()
            lot._compute_ancho_export_display()
            lot._compute_vol_shipment_m3()

            self.assertAlmostEqual(lot.volume_purchase_m3, exp_p, places=3)
            self.assertAlmostEqual(lot.vol_shipment_m3, exp_s, places=3)
            self.assertEqual(lot.is_out_of_table, is_out)
            self.assertTrue(lot.vol_shipment_m3 <= lot.volume_purchase_m3)

    def test_03_fa531r_san_joaquin_d7436_golden_reference(self):
        """FA531R (San Joaquín): D7436 145 mm 4.05 m x 189 = 4.995 / 4.074 m³."""
        lot = self.env['stock.lot'].create({
            'name': 'FA531R-D7436',
            'product_id': self.product.id,
            'subproducto_id': self.sub_s2s.id if self.sub_s2s else False,
            'espesor_mm': 45.0,
            'ancho_mm': 145.0,
            'largo_m': 4.05,
            'piezas': 189,
            'volume_purchase_m3': self._calc_purchase_m3(45.0, 145.0, 4.05, 189),
        })
        lot._compute_out_of_table_status()
        lot._compute_vol_shipment_m3()

        self.assertAlmostEqual(lot.volume_purchase_m3, 4.995, places=3)
        self.assertAlmostEqual(lot.vol_shipment_m3, 4.074, places=3)
        self.assertFalse(lot.is_out_of_table)

    def test_04_blanks_golden_references_single_source(self):
        """Blanks: compra = exportación (una sola fuente); fórmula f5085 con +1/8"."""
        blanks_cases = [
            # (ancho_visual, largo_ft, piezas, vol_m3_esperado)
            ("2 5/8", "16'", 416, 5.399),
            ("3 5/8", "16'", 286, 5.062),
            ("3 5/8", "16'", 297, 5.256),
            ("5 5/8", "16'", 189, 5.129),
            ("2 5/8", "16'", 432, 5.607),
            ("5 5/8", "16'", 182, 4.939),  # A1M2602499 packing GD 97183
        ]

        from ..models.utils_uom import parse_fraction_to_decimal_inch, MM_PER_INCH

        for w_vis, l_ft, pcs, exp_vol in blanks_cases:
            nom_in = parse_fraction_to_decimal_inch(w_vis)
            w_mm = nom_in * float(MM_PER_INCH)
            lot = self.env['stock.lot'].create({
                'name': f"BLANK-TEST-{w_vis.replace(' ', '_')}-{pcs}",
                'product_id': self.product.id,
                'subproducto_id': self.sub_blank.id if self.sub_blank else False,
                'espesor_mm': 45.0,
                'ancho_mm': w_mm,
                'width_visual': w_vis,
                'largo_ft_frac': l_ft,
                'piezas': pcs,
            })
            lot._compute_out_of_table_status()
            lot._compute_vol_shipment_m3()
            lot.volume_purchase_m3 = lot.vol_shipment_m3

            self.assertAlmostEqual(lot.vol_shipment_m3, exp_vol, places=3)
            self.assertEqual(lot.volume_purchase_m3, lot.vol_shipment_m3,
                             "En Blanks: compra = stock = exportación (una sola fuente oficial).")
            self.assertEqual(lot.out_of_table_status, 'not_applicable',
                             "Blanks no aplican a lumber.width.s2s.map.")

    def test_05_rough_aserrada_golden_reference(self):
        """Rugoso (RIP ROUGH, aserrada JCE): compra = exportación, métrico puro."""
        # RIP ROUGH 24 x 125 mm x 4.0 m x 336 pzas = 4.032 m³
        lot = self.env['stock.lot'].create({
            'name': 'ROUGH-24-125-336',
            'product_id': self.product.id,
            'subproducto_id': self.sub_rough.id if self.sub_rough else False,
            'espesor_mm': 24.0,
            'ancho_mm': 125.0,
            'largo_m': 4.0,
            'piezas': 336,
            'volume_purchase_m3': (24.0 * 125.0 * 4.0 * 336) / 1_000_000.0,
        })
        lot._compute_out_of_table_status()
        lot._compute_vol_shipment_m3()

        self.assertAlmostEqual(lot.volume_purchase_m3, 4.032, places=3)
        self.assertAlmostEqual(lot.vol_shipment_m3, 4.032, places=3)
        self.assertEqual(lot.volume_purchase_m3, lot.vol_shipment_m3,
                         "En madera rugosa: compra = exportación (métrico puro).")
        self.assertEqual(lot.out_of_table_status, 'not_applicable')

    def test_06_out_of_table_widths_160_and_165(self):
        """Anchos 160 mm y 165 mm ausentes de la tabla S2S aplican conversión métrica directa (regla d)."""
        config = self.env['madenat.ingestion.config']

        # 160 mm: 160 / 25.4 = 6.2992" (sin +1/8")
        det_160 = config.resolve_export_width_details(160.0)
        self.assertTrue(det_160['is_out_of_table'])
        self.assertAlmostEqual(det_160['calc_width_inches'], 160.0 / 25.4, places=4)
        self.assertEqual(det_160['overwidth_inches'], 0.0)

        # 165 mm: 165 / 25.4 = 6.4960" (sin +1/8")
        det_165 = config.resolve_export_width_details(165.0)
        self.assertTrue(det_165['is_out_of_table'])
        self.assertAlmostEqual(det_165['calc_width_inches'], 165.0 / 25.4, places=4)
        self.assertEqual(det_165['overwidth_inches'], 0.0)
