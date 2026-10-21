# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from ..models.utils_uom import (
    MM_PER_INCH,
    ROUGH_THICKNESS_6_4_MM,
    NOMINAL_EXPORT_THICKNESS_6_4_INCHES,
    CONST_M3_TO_IN2_M,
    calculate_volume_metric_m3,
)

class TestResolveExportWidthAPI(TransactionCase):
    """Pruebas unitarias para la API única de resolución de ancho de exportación (H4 / AD-130)."""

    def setUp(self):
        super().setUp()
        self.config = self.env['madenat.ingestion.config']
        self.map_model = self.env['lumber.width.s2s.map']

    def test_01_width_in_table_returns_full_details(self):
        """Ancho en tabla (150 mm) devuelve nominal, sobreancho y cálculo coherente."""
        details = self.config.resolve_export_width_details(150.0)
        self.assertEqual(details['nominal_width_display'], '5 5/8')
        self.assertAlmostEqual(details['nominal_width_inches'], 5.625, places=4)
        self.assertAlmostEqual(details['overwidth_inches'], 0.125, places=4)
        self.assertAlmostEqual(details['calc_width_inches'], 5.750, places=4)
        self.assertFalse(details['is_out_of_table'])
        self.assertEqual(details['out_of_table_status'], 'ok')

        # Compatibilidad con resolve_export_width
        calc_width = self.config.resolve_export_width(150.0)
        self.assertAlmostEqual(calc_width, details['calc_width_inches'], places=4)

    def test_02_width_out_of_table_gte_170mm(self):
        """Ancho >= 170 mm fuera de tabla (170 mm) usa conversión directa métrica sin sobreancho."""
        details = self.config.resolve_export_width_details(170.0)
        expected_in = 170.0 / float(MM_PER_INCH)
        self.assertEqual(details['nominal_width_display'], '170 mm')
        self.assertAlmostEqual(details['nominal_width_inches'], expected_in, places=4)
        self.assertEqual(details['overwidth_inches'], 0.0)
        self.assertAlmostEqual(details['calc_width_inches'], expected_in, places=4)
        self.assertTrue(details['is_out_of_table'])
        self.assertEqual(details['out_of_table_status'], 'out_of_table_confirm')

        # Con 150 piezas, 4.0m, espesor 1.5":
        vol = (float(NOMINAL_EXPORT_THICKNESS_6_4_INCHES) * details['calc_width_inches'] * 4.0 * 150) / float(CONST_M3_TO_IN2_M)
        self.assertAlmostEqual(round(vol, 3), 3.886, places=3)

    def test_03_width_out_of_table_lt_170mm_warning(self):
        """Ancho < 170 mm fuera de tabla (160 mm) con política warning retorna sin sobreancho y marcado."""
        self.env['ir.config_parameter'].sudo().set_param('madenat.out_of_table_behavior', 'warning')
        details = self.config.resolve_export_width_details(160.0)
        expected_in = 160.0 / float(MM_PER_INCH)
        self.assertAlmostEqual(details['calc_width_inches'], expected_in, places=4)
        self.assertEqual(details['overwidth_inches'], 0.0)
        self.assertTrue(details['is_out_of_table'])
        self.assertEqual(details['out_of_table_status'], 'out_of_table_confirm')

    def test_04_width_out_of_table_lt_170mm_block(self):
        """Ancho < 170 mm fuera de tabla con política block levanta ValidationError."""
        self.env['ir.config_parameter'].sudo().set_param('madenat.out_of_table_behavior', 'block')
        try:
            with self.assertRaises(ValidationError):
                self.config.resolve_export_width_details(160.0)
        finally:
            self.env['ir.config_parameter'].sudo().set_param('madenat.out_of_table_behavior', 'warning')

    def test_05_explicit_s2s_inches_signal(self):
        """Señal documental explícita is_s2s_inches aplica sobreancho directo."""
        details = self.config.resolve_export_width_details(150.0, is_s2s_inches=True)
        expected_nom = 150.0 / float(MM_PER_INCH)
        self.assertAlmostEqual(details['nominal_width_inches'], expected_nom, places=4)
        self.assertAlmostEqual(details['overwidth_inches'], 0.125, places=4)
        self.assertAlmostEqual(details['calc_width_inches'], expected_nom + 0.125, places=4)
        self.assertFalse(details['is_out_of_table'])

    def test_06_manual_override_respected(self):
        """Override manual en record tiene máxima prioridad y sobreancho cero."""
        class MockRecord:
            export_width_manual_inches = 5.250
            export_width_manual_display = '5 1/4'

        rec = MockRecord()
        details = self.config.resolve_export_width_details(150.0, record=rec)
        self.assertEqual(details['calc_width_inches'], 5.250)
        self.assertEqual(details['nominal_width_inches'], 5.250)
        self.assertEqual(details['nominal_width_display'], '5 1/4')
        self.assertEqual(details['overwidth_inches'], 0.0)
        self.assertEqual(details['out_of_table_status'], 'manual_override')

    def test_07_row_level_overwidth_applied(self):
        """Sobreancho opcional por fila en lumber.width.s2s.map tiene precedencia sobre el global."""
        rec_100 = self.map_model.search([('rough_mm', '=', 100), ('active', '=', True)], limit=1)
        self.assertTrue(rec_100)
        orig_overwidth = rec_100.overwidth_inches
        try:
            # Fijamos 0.250" (1/4") solo a la fila de 100 mm
            rec_100.write({'overwidth_inches': 0.250})
            details = self.config.resolve_export_width_details(100.0)
            self.assertAlmostEqual(details['overwidth_inches'], 0.250, places=4)
            # 3.625 + 0.250 = 3.875
            self.assertAlmostEqual(details['calc_width_inches'], 3.875, places=4)
        finally:
            rec_100.write({'overwidth_inches': orig_overwidth})

    def test_08_constants_and_metric_volume(self):
        """Validar constantes físicas en utils_uom y divisor en calculate_volume_metric_m3."""
        self.assertEqual(float(ROUGH_THICKNESS_6_4_MM), 45.0)
        self.assertEqual(float(NOMINAL_EXPORT_THICKNESS_6_4_INCHES), 1.5)
        # 45 mm x 100 mm x 4.0 m x 200 pzas = 3.6 m3
        vol = calculate_volume_metric_m3(float(ROUGH_THICKNESS_6_4_MM), 100.0, 4.0, 200)
        self.assertEqual(vol, 3.6)

    def test_09_acl_permissions_s2s_map(self):
        """Punto 2.9: Escritura en lumber.width.s2s.map solo para group_lumber_config_manager."""
        from odoo.exceptions import AccessError
        group_user = self.env.ref('base.group_user')
        group_oper = self.env.ref('madenat_lumber_core.group_madenat_operaciones')
        group_audit = self.env.ref('madenat_lumber_core.group_madenat_auditoria')
        group_config = self.env.ref('madenat_lumber_core.group_lumber_config_manager')

        user_oper = self.env['res.users'].create({
            'name': 'Operaciones ACL User',
            'login': 'oper_acl_user_h4',
            'groups_id': [(6, 0, [group_user.id, group_oper.id])],
        })
        user_audit = self.env['res.users'].create({
            'name': 'Auditoria ACL User',
            'login': 'audit_acl_user_h4',
            'groups_id': [(6, 0, [group_user.id, group_audit.id])],
        })
        user_config = self.env['res.users'].create({
            'name': 'Config Manager ACL User',
            'login': 'config_acl_user_h4',
            'groups_id': [(6, 0, [group_user.id, group_config.id])],
        })

        rec_100 = self.map_model.search([('rough_mm', '=', 100), ('active', '=', True)], limit=1)
        self.assertTrue(rec_100)

        # Operaciones: puede leer, pero NO escribir ni crear
        recs_oper = self.map_model.with_user(user_oper).search([('rough_mm', '=', 100)])
        self.assertTrue(recs_oper)
        with self.assertRaises(AccessError):
            rec_100.with_user(user_oper).write({'s2s_label': '3 5/8'})
        with self.assertRaises(AccessError):
            self.map_model.with_user(user_oper).create({
                'rough_mm': 999, 's2s_decimal': 10.0, 's2s_label': '10'
            })

        # Auditoria: puede leer, pero NO escribir ni crear
        recs_audit = self.map_model.with_user(user_audit).search([('rough_mm', '=', 100)])
        self.assertTrue(recs_audit)
        with self.assertRaises(AccessError):
            rec_100.with_user(user_audit).write({'s2s_label': '3 5/8'})
        with self.assertRaises(AccessError):
            self.map_model.with_user(user_audit).create({
                'rough_mm': 998, 's2s_decimal': 10.0, 's2s_label': '10'
            })

        # Config Manager: puede leer y escribir
        rec_100.with_user(user_config).write({'s2s_label': '3 5/8'})

    def test_10_blanks_subproducto_family_invariants(self):
        """Punto 2.4: Blanks por configuración en madenat.subproducto; compra = exportación."""
        Subproducto = self.env['madenat.subproducto']
        Subproducto._init_calculation_families()

        sub_blank = Subproducto.search([('code', '=', 'BLANK-CLEAR')], limit=1)
        if not sub_blank:
            sub_blank = Subproducto.create({
                'name': 'BLANK CLEAR TEST',
                'code': 'BLANK-CLEAR-TEST',
                'calculation_family': 'blank',
            })
        self.assertEqual(sub_blank.calculation_family, 'blank')

        # Verificación en StockLot
        product = self.env['product.product'].search([], limit=1)
        lot = self.env['stock.lot'].create({
            'name': 'LOT-TEST-BLANK-H4',
            'product_id': product.id,
            'subproducto_id': sub_blank.id,
            'espesor_mm': 45.0,
            'ancho_mm': 92.075,
            'largo_m': 4.8768,
            'largo_ft_frac': "16'",
            'piezas': 250,
        })
        lot._compute_vol_shipment_m3()
        # En Blanks: compra = exportación con una sola fuente (f5085 con +1/8")
        # 1.5" x 3.750" x 16' x 250 / 5085.312 = 4.4245... -> 4.425 m³
        self.assertAlmostEqual(lot.vol_shipment_m3, 4.425, places=3)

    def test_11_blanks_metric_mapping_with_tolerance(self):
        """Punto 2.4: Mapeo de Blanks en métrico a fracción estándar con tolerancia paramétrica."""
        from ..models.utils_uom import map_metric_to_blank_fraction

        # Caso exacto: 92.075 mm = 3.625" (3 5/8)
        std_in, frac_str, needs_review = map_metric_to_blank_fraction(92.075, env=self.env)
        self.assertAlmostEqual(std_in, 3.625, places=4)
        self.assertEqual(frac_str, "3 5/8")
        self.assertFalse(needs_review)

        # Caso dentro de tolerancia (92.5 mm ≈ 3.6417", diff = 0.0167" <= 0.03125")
        std_in, frac_str, needs_review = map_metric_to_blank_fraction(92.5, env=self.env)
        self.assertAlmostEqual(std_in, 3.625, places=4)
        self.assertEqual(frac_str, "3 5/8")
        self.assertFalse(needs_review)

        # Caso fuera de tolerancia (94.0 mm ≈ 3.7008", diff = 0.0758" > 0.03125")
        std_in, frac_str, needs_review = map_metric_to_blank_fraction(94.0, env=self.env)
        self.assertTrue(needs_review, "Dimensión métrica fuera de 1/32\" debe marcarse para revisión humana.")
    def test_12_packing_control_vol_documental_and_reconciliation(self):
        """Punto 2.5: Control del packing con vol_documental_m3 por fila y estado de conciliación."""
        product = self.env['product.product'].search([], limit=1)

        # Lote representativo GD 97183 paquete A1M2602499 (5 5/8" x 16 ft x 182 pcs = 4.939 m³ calculado)
        # En el packing viene declarado con 6 decimales: 4.938930 m³
        lot_match = self.env['stock.lot'].create({
            'name': 'A1M2602499',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 142.875,  # 5.625"
            'largo_ft_frac': "16'",
            'piezas': 182,
            'vol_documental_m3': 4.938930,
        })
        lot_match._compute_vol_shipment_m3()
        lot_match._compute_reconciliation_status()

        # El valor calculado oficial es 4.939 m³ (no es reemplazado por el documental)
        self.assertAlmostEqual(lot_match.vol_shipment_m3, 4.939, places=3)
        self.assertEqual(lot_match.vol_documental_m3, 4.938930)
        self.assertEqual(lot_match.reconciliation_status, 'match', "Diferencia < 0.001 m³ debe clasificar como 'match'")

        # Caso diferencia dentro de tolerancia (ej: declarado 4.945 vs calculado 4.939 -> diff = 0.006 <= 0.010)
        lot_tol = self.env['stock.lot'].create({
            'name': 'LOT-TOLERANCE-TEST',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 142.875,
            'largo_ft_frac': "16'",
            'piezas': 182,
            'vol_documental_m3': 4.945000,
        })
        lot_tol._compute_vol_shipment_m3()
        lot_tol._compute_reconciliation_status()
        self.assertEqual(lot_tol.reconciliation_status, 'tolerance')

        # Caso revisar (ej: declarado 5.200 vs calculado 4.939 -> diff = 0.261 > 0.010)
        lot_rev = self.env['stock.lot'].create({
            'name': 'LOT-REVIEW-TEST',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 142.875,
            'largo_ft_frac': "16'",
            'piezas': 182,
            'vol_documental_m3': 5.200000,
        })
        lot_rev._compute_vol_shipment_m3()
        lot_rev._compute_reconciliation_status()
        self.assertEqual(lot_rev.reconciliation_status, 'review')

    def test_13_out_of_table_status_and_display_s2s(self):
        """Puntos 2.6 y 2.8: Estado visible 'ancho fuera de tabla: confirmar' y display nominal S2S."""
        product = self.env['product.product'].search([], limit=1)

        # 1. En tabla: 150 mm -> nominal display '5 5/8', estado 'in_table'
        lot_in = self.env['stock.lot'].create({
            'name': 'LOT-S2S-150-IN',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 150.0,
            'largo_m': 4.0,
            'piezas': 175,
        })
        lot_in._compute_out_of_table_status()
        lot_in._compute_ancho_export_display()
        lot_in._compute_vol_shipment_m3()
        self.assertEqual(lot_in.out_of_table_status, 'in_table')
        self.assertFalse(lot_in.is_out_of_table)
        self.assertEqual(lot_in.ancho_export_display, '5 5/8')
        # Volumen calculado usa +1/8" (5.750"): 1.5 x 5.75 x 4.0 x 175 / 1550.003 = 3.895 m³
        self.assertAlmostEqual(lot_in.vol_shipment_m3, 3.895, places=3)

        # 2. Fuera de tabla: 170 mm -> estado 'out_of_table', is_out_of_table=True
        lot_out = self.env['stock.lot'].create({
            'name': 'LOT-S2S-170-OUT',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 170.0,
            'largo_m': 4.0,
            'piezas': 150,
        })
        lot_out._compute_out_of_table_status()
        lot_out._compute_ancho_export_display()
        lot_out._compute_vol_shipment_m3()
        self.assertTrue(lot_out.is_out_of_table)
        self.assertEqual(lot_out.out_of_table_status, 'out_of_table')
        self.assertEqual(lot_out.ancho_export_display, '170 mm')
        # Volumen de 170 mm fuera de tabla (regla d / métrico sin +1/8"): 3.886 m³
        self.assertAlmostEqual(lot_out.vol_shipment_m3, 3.886, places=3)

    def test_14_manual_override_validation_and_propagation(self):
        """Puntos 2.6 y 2.7: Validación obligatoria de motivo ante captura manual y propagación a embarque."""
        product = self.env['product.product'].search([], limit=1)

        # 1. Validación en stock.lot: ancho manual > 0 sin motivo lanza ValidationError
        with self.assertRaises(ValidationError):
            self.env['stock.lot'].create({
                'name': 'LOT-FAIL-NO-REASON',
                'product_id': product.id,
                'espesor_mm': 45.0,
                'ancho_mm': 170.0,
                'export_width_manual_inches': 6.693,
                'export_width_manual_reason': '   ',  # Vacío
            })

        # 2. Captura manual válida con motivo en stock.lot
        lot_manual = self.env['stock.lot'].create({
            'name': 'LOT-MANUAL-CONFIRMED',
            'product_id': product.id,
            'espesor_mm': 45.0,
            'ancho_mm': 170.0,
            'largo_m': 4.0,
            'piezas': 150,
            'export_width_manual_inches': 6.75,
            'export_width_manual_reason': 'Ancho especial cliente exportación',
        })
        lot_manual._compute_out_of_table_status()
        lot_manual._compute_ancho_export_display()
        lot_manual._compute_vol_shipment_m3()
        self.assertEqual(lot_manual.out_of_table_status, 'confirmed')
        self.assertTrue(lot_manual.is_out_of_table)
        self.assertTrue(lot_manual.export_width_manual_user_id)

        # 3. Validación en madenat.guia.processing.line
        guia = self.env['madenat.guia.processing'].create({'name': 'GUIA-TEST-OVERRIDE'})
        with self.assertRaises(ValidationError):
            self.env['madenat.guia.processing.line'].create({
                'processing_id': guia.id,
                'product_id': product.id,
                'lot_name': 'LOTE-GUIA-FAIL',
                'ancho_mm': 170.0,
                'export_width_manual_inches': 6.693,
                'export_width_manual_reason': '   ',
            })

        line_valid = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'product_id': product.id,
            'lot_name': 'LOTE-GUIA-OK',
            'ancho_mm': 170.0,
            'export_width_manual_inches': 6.75,
            'export_width_manual_reason': 'Ancho manual justificado',
        })
        line_valid._compute_out_of_table_status()
        self.assertEqual(line_valid.out_of_table_status, 'confirmed')

        # 4. Propagación a línea de embarque si el modelo está en registry
        if 'lumber.export.shipment' in self.env:
            partner = self.env['res.partner'].create({'name': 'Cliente Test Emb'})
            shipment = self.env['lumber.export.shipment'].create({
                'name': 'EXP-TEST-OVERRIDE',
                'customer_id': partner.id,
            })
            container = self.env['lumber.container'].create({
                'name': 'CONT-TEST-01',
                'shipment_id': shipment.id,
            })
            ship_line = self.env['lumber.shipment.line'].create({
                'shipment_id': shipment.id,
                'container_id': container.id,
                'lot_id': lot_manual.id,
            })
            ship_line._compute_export_dims()

            # Verifica related fields y resolución vía API única
            self.assertAlmostEqual(ship_line.export_width_manual_inches, 6.75, places=3)
            self.assertEqual(ship_line.export_width_manual_reason, 'Ancho especial cliente exportación')
            self.assertEqual(ship_line.out_of_table_status, 'confirmed')
            self.assertAlmostEqual(ship_line.export_width_inches, 6.75, places=3)

