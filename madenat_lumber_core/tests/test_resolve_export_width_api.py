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


