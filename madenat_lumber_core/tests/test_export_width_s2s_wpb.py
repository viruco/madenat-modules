# -*- coding: utf-8 -*-
"""Pruebas unitarias para WP-B / Bloque 4A (AD-116 / AD-117): Ancho de Exportación S2S por Datos y Opción Manual.

Verifica:
1. Regla de ancho por datos (H2/H3):
   - 14 anchos de la planilla de cubicación (75 a 155 mm) en lumber.width.s2s.map con sobreancho +1/8".
   - Anchos ausentes de tabla (170, 175, 180, 195, 200 mm, y 135 mm) usan mm / 25.4 directo.
2. Comprobación exacta para 100 piezas (evita enmascaramiento de redondeo de 1 pieza).
3. Prueba anti-hardcode (H4):
   - Modificar un registro en lumber.width.s2s.map altera el cálculo.
   - Modificar el parámetro madenat.s2s_overwidth_inches altera el cálculo.
   - Parámetro madenat.out_of_table_behavior ('direct', 'warning', 'block').
4. Opción manual de exportación (AD-115):
   - export_width_manual_inches fijado prevalece sobre el cálculo automático.
   - Motivo obligatorio (ValidationError si vacío) y registro en chatter.
5. Regresión Guía 26270:
   - Líneas de 150 mm dan 3.812 y 0.480 m³ (total 4.292 m³).
   - Con ancho manual forzado a 5 5/8" (5.625") da 3.730 m³.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install', 'madenat_lumber_core')
class TestExportWidthS2SWpB(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Proveedor S2S Test',
            'is_company': True,
        })
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.product'].create({
            'name': 'Pino Aserrado S2S Test',
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
        })
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']

    def _make_guia(self, name='GUIA-WPB-TEST'):
        return self.Guia.create({
            'name': name,
            'partner_id': self.supplier.id,
            'state': 'draft',
            'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'assignment_location_id': self.stock_location.id,
        })

    def _make_line(self, guia, ancho_mm, thickness_visual='6/4', width_visual='3 5/8',
                   largo_m=3.2, pieces=10, vol_purchase=0.144, **kwargs):
        is_s2s = kwargs.pop('is_s2s_inches', False)
        vals = {
            'processing_id': guia.id,
            'product_id': self.product.id,
            'lot_name': f'LOTE-{ancho_mm}MM',
            'ancho_mm': ancho_mm,
            'thickness_visual': thickness_visual,
            'width_visual': width_visual,
            'largo_m': largo_m,
            'pieces': pieces,
            'vol_purchase_m3': vol_purchase,
        }
        vals.update(kwargs)
        return self.Line.with_context(is_s2s_inches=is_s2s).create(vals)

    def test_01_ancho_100mm_uses_s2s_table(self):
        """100 mm rough con visual '3 5/8' aplica cálculo por datos: 3.625" + recargo 0.125" = 3.750"."""
        guia = self._make_guia('GUIA-S2S-100')
        line = self._make_line(guia, ancho_mm=100.0, thickness_visual='6/4',
                               width_visual='3 5/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.5" * (3.625 + 0.125)" * 3.2m * 10) / 1550.0031 = 0.11612... -> 0.116 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.116, places=3)

    def test_02_ancho_145mm_uses_critical_s2s_value(self):
        """145 mm rough con visual '5 3/8' aplica cálculo por datos: 5.375" + recargo 0.125" = 5.500"."""
        guia = self._make_guia('GUIA-S2S-145')
        line = self._make_line(guia, ancho_mm=145.0, thickness_visual='7/4',
                               width_visual='5 3/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.75" * (5.375 + 0.125)" * 3.2m * 10) / 1550.0031 = 0.1987... -> 0.199 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.199, places=3)

    def test_03_ancho_135mm_absent_from_s2s_uses_direct_division(self):
        """135 mm ausente de tabla S2S: usa 135 / 25.4 = 5.31496" directo."""
        guia = self._make_guia('GUIA-S2S-135')
        line = self._make_line(guia, ancho_mm=135.0, thickness_visual='7/4',
                               width_visual='5 1/4', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.75 * (135/25.4) * 3.2 * 10) / 1550.0031 = 0.19202 -> 0.192 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.192, places=3)

    def test_04_ancho_absent_from_s2s_table_uses_direct_division(self):
        """Anchos ausentes de tabla S2S aplican conversión directa mm / 25.4 y advierten en chatter si son < direct_width_min_mm."""
        self.env['ir.config_parameter'].sudo().set_param('madenat.out_of_table_behavior', 'warning')
        guia = self._make_guia('GUIA-S2S-OUT')
        # Menor a 75 mm (60 mm): ausente de tabla y < 170 mm -> conversión directa + advertencia en chatter
        line_low = self._make_line(guia, ancho_mm=60.0, thickness_visual='6/4',
                                   width_visual='2 3/8', largo_m=3.2, pieces=10)
        line_low.flush_recordset()
        # (1.5 * (60/25.4) * 3.2 * 10) / 1550.0031 = 0.07315 -> 0.073 m3
        self.assertAlmostEqual(line_low.vol_shipment_m3, 0.073, places=3)

        # 170 mm: ausente de tabla pero >= 170 mm -> directo sin advertencia
        line_high = self._make_line(guia, ancho_mm=170.0, thickness_visual='7/4',
                                    width_visual='6 5/8', largo_m=3.2, pieces=10)
        line_high.flush_recordset()
        # (1.75 * (170/25.4) * 3.2 * 10) / 1550.0031 = 0.2418 -> 0.242 m3
        self.assertAlmostEqual(line_high.vol_shipment_m3, 0.242, places=3)

        messages = self.env['mail.message'].search([
            ('model', '=', 'madenat.guia.processing'),
            ('res_id', '=', guia.id),
        ])
        body_texts = ' '.join(m.body or '' for m in messages)
        self.assertIn('Advertencia Ancho S2S', body_texts)
        self.assertIn('60.0 mm', body_texts)
        self.assertNotIn('rough 170.0 mm', body_texts)

    def test_05_manual_export_width_override_and_bitacora(self):
        """Fijar ancho manual prevalece sobre el cálculo automático, exige motivo y registra en el chatter."""
        guia = self._make_guia('GUIA-S2S-MANUAL')
        line = self._make_line(
            guia, ancho_mm=100.0, thickness_visual='6/4', width_visual='3 5/8',
            largo_m=3.2, pieces=10,
            export_width_manual_inches=4.0,
            export_width_manual_reason='Ajuste contractual cliente USA',
        )
        line.flush_recordset()
        # width_calc = 4.0 manual (prevalece sobre 3.625 + 0.125 = 3.750)
        # (1.5 * 4.0 * 3.2 * 10) / 1550.0031 = 0.12387 -> 0.124 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.124, places=3)
        self.assertEqual(line.export_width_manual_user_id, self.env.user)
        self.assertTrue(line.export_width_manual_date)

        # Verificar mensaje en bitácora (chatter) de la guía
        messages = self.env['mail.message'].search([
            ('model', '=', 'madenat.guia.processing'),
            ('res_id', '=', guia.id),
        ])
        body_texts = ' '.join(m.body or '' for m in messages)
        self.assertIn('Ancho manual de exportación fijado', body_texts)
        self.assertIn('4.0', body_texts)
        self.assertIn('Ajuste contractual cliente USA', body_texts)

    def test_06_manual_export_width_without_reason_raises(self):
        """Fijar ancho manual sin motivo lanza ValidationError."""
        guia = self._make_guia('GUIA-S2S-ERR')
        with self.assertRaises(ValidationError):
            self._make_line(
                guia, ancho_mm=100.0,
                export_width_manual_inches=4.0,
                export_width_manual_reason='',  # Sin motivo obligatorio
            )

    def test_07_regression_guia_26270_synthetic_lines(self):
        """Regresión AD-116: Líneas de 150 mm dan 3.812 y 0.480 m³ (total 4.292), manual 5 5/8 da 3.730 m³."""
        guia = self._make_guia('GUIA-26270-SINTETICA')

        # Línea A: 100 mm, visual '3 5/8' (ID 5137 en BD)
        line_100 = self._make_line(
            guia, ancho_mm=100.0, thickness_visual='5/4', width_visual='3 5/8',
            largo_m=4.05, pieces=200, vol_purchase=2.997
        )
        line_100.flush_recordset()
        # (1.25 * (3.625 + 0.125) * 4.05 * 200) / 1550.0031 = 2.44999 -> 2.450 m3
        self.assertAlmostEqual(line_100.vol_shipment_m3, 2.450, places=3)

        # Línea B: 125 mm, visual '4 5/8' (ID 5128 en BD)
        line_125 = self._make_line(
            guia, ancho_mm=125.0, thickness_visual='5/4', width_visual='4 5/8',
            largo_m=4.05, pieces=264, vol_purchase=4.945
        )
        line_125.flush_recordset()
        # (1.25 * (4.625 + 0.125) * 4.05 * 264) / 1550.0031 = 4.09596 -> 4.096 m3
        self.assertAlmostEqual(line_125.vol_shipment_m3, 4.096, places=3)

        # Línea C1: 150 mm, visual '150mm' (ID 5140 en BD)
        # 150 mm en tabla S2S (5.625") + 0.125" = 5.750"
        line_150_1 = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203, vol_purchase=4.563
        )
        line_150_1.flush_recordset()
        # (1.25 * 5.750 * 4.05 * 203) / 1550.0031 = 3.8123 -> 3.812 m3
        self.assertAlmostEqual(line_150_1.vol_shipment_m3, 3.812, places=3)

        # Línea C2: 150 mm, visual '150mm' (ID 5141 en BD, 28 pzas, 3.70 m)
        line_150_2 = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=3.70, pieces=28, vol_purchase=0.575
        )
        line_150_2.flush_recordset()
        # (1.25 * 5.750 * 3.70 * 28) / 1550.0031 = 0.48023 -> 0.480 m3
        self.assertAlmostEqual(line_150_2.vol_shipment_m3, 0.480, places=3)
        self.assertAlmostEqual(line_150_1.vol_shipment_m3 + line_150_2.vol_shipment_m3, 4.292, places=3)

        # Línea D: 150 mm con ancho manual forzado a 5 5/8" (5.625")
        line_150_manual = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203, vol_purchase=4.563,
            export_width_manual_inches=5.625,
            export_width_manual_reason='Forzado manual S2S neto 5 5/8"'
        )
        line_150_manual.flush_recordset()
        # (1.25 * 5.625 * 4.05 * 203) / 1550.0031 = 3.7295 -> 3.730 m3
        self.assertAlmostEqual(line_150_manual.vol_shipment_m3, 3.730, places=3)

    def test_08_canonical_14_widths_s2s_spreadsheet_100_pieces(self):
        """Los 14 anchos de la planilla de Cristhian con espesor 6/4 (1.5\"), 4.0 m y 100 piezas."""
        guia = self._make_guia('GUIA-14-ANCHOS')
        # Datos: (rough_mm, esperado_m3)
        vectores = [
            (75, 1.065), (85, 1.161), (90, 1.258), (95, 1.355),
            (100, 1.452), (105, 1.548), (110, 1.548), (120, 1.742),
            (125, 1.839), (130, 1.935), (140, 1.935), (145, 2.129),
            (150, 2.226), (155, 2.323),
        ]
        for rough_mm, expected_m3 in vectores:
            line = self._make_line(
                guia, ancho_mm=float(rough_mm), thickness_visual='6/4',
                width_visual=f"{rough_mm}mm", largo_m=4.0, pieces=100
            )
            line.flush_recordset()
            self.assertAlmostEqual(
                line.vol_shipment_m3, expected_m3, places=3,
                msg=f"Fallo en ancho {rough_mm} mm: obtenido {line.vol_shipment_m3}, esperado {expected_m3}"
            )

    def test_09_direct_5_widths_spreadsheet_100_pieces(self):
        """Los 5 anchos directos milimétricos (>= 170 mm) con 1.5\", 4.0 m y 100 piezas."""
        guia = self._make_guia('GUIA-5-DIRECTOS')
        vectores_directos = [
            (170, 2.591), (175, 2.667), (180, 2.743),
            (195, 2.972), (200, 3.048),
        ]
        for rough_mm, expected_m3 in vectores_directos:
            line = self._make_line(
                guia, ancho_mm=float(rough_mm), thickness_visual='6/4',
                width_visual=f"{rough_mm}mm", largo_m=4.0, pieces=100
            )
            line.flush_recordset()
            self.assertAlmostEqual(
                line.vol_shipment_m3, expected_m3, places=3,
                msg=f"Fallo en ancho directo {rough_mm} mm: obtenido {line.vol_shipment_m3}, esperado {expected_m3}"
            )

    def test_10_anti_hardcode_dynamic_s2s_record_and_parameter_changes(self):
        """Regla Anti-Hardcode (H4): Modificar registros o parámetros altera el resultado dinámicamente."""
        guia = self._make_guia('GUIA-ANTI-HARDCODE')

        # 1. Modificar un registro en lumber.width.s2s.map (100 mm pasa de 3.625 a 3.750)
        rec_100 = self.env['lumber.width.s2s.map'].search([('rough_mm', '=', 100)], limit=1)
        original_s2s = rec_100.s2s_decimal
        try:
            rec_100.write({'s2s_decimal': 3.750})
            line = self._make_line(guia, ancho_mm=100.0, thickness_visual='6/4', largo_m=4.0, pieces=100)
            line.flush_recordset()
            # (1.5 * (3.750 + 0.125) * 4.0 * 100) / 1550.0031 = 2325 / 1550.0031 = 1.49999 -> 1.500 m3
            self.assertAlmostEqual(line.vol_shipment_m3, 1.500, places=3)
        finally:
            rec_100.write({'s2s_decimal': original_s2s})

        # 2. Modificar el parámetro sobreancho madenat.s2s_overwidth_inches a 0.250"
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('madenat.s2s_overwidth_inches', '0.250')
        try:
            line2 = self._make_line(guia, ancho_mm=100.0, thickness_visual='6/4', largo_m=4.0, pieces=100)
            line2.flush_recordset()
            # (1.5 * (3.625 + 0.250) * 4.0 * 100) / 1550.0031 = 2325 / 1550.0031 = 1.500 m3
            self.assertAlmostEqual(line2.vol_shipment_m3, 1.500, places=3)
        finally:
            param_obj.set_param('madenat.s2s_overwidth_inches', '0.125')

        # 3. Comportamiento 'block' para ancho fuera de tabla menor a direct_width_min_mm (160 mm < 170 mm)
        param_obj.set_param('madenat.out_of_table_behavior', 'block')
        try:
            with self.assertRaises(ValidationError):
                line3 = self._make_line(guia, ancho_mm=160.0, thickness_visual='6/4', largo_m=4.0, pieces=100)
                line3.flush_recordset()
        finally:
            param_obj.set_param('madenat.out_of_table_behavior', 'warning')

        # 4. Anti-hardcode: Modificar direct_width_min_mm altera el límite donde rige el comportamiento bloqueante
        param_obj.set_param('madenat.out_of_table_behavior', 'block')
        param_obj.set_param('madenat.direct_width_min_mm', '150.0')
        try:
            # 160 mm es >= 150.0 mm -> pasa directo sin error incluso con behavior='block'
            line4 = self._make_line(guia, ancho_mm=160.0, thickness_visual='6/4', largo_m=4.0, pieces=100)
            line4.flush_recordset()
            # (1.5 * (160 / 25.4) * 4.0 * 100) / 1550.0031 = 2.43839 -> 2.438 m3
            self.assertAlmostEqual(line4.vol_shipment_m3, 2.438, places=3)
        finally:
            param_obj.set_param('madenat.direct_width_min_mm', '170.0')
            param_obj.set_param('madenat.out_of_table_behavior', 'warning')

    def test_11_sweep_50_to_220mm_all_widths(self):
        """Barrido de anchos 50 a 220 mm en pasos de 5 mm más 115, 135, 160 y 165 mm con 1.5\", 4.0 m y 100 pzas."""
        guia = self._make_guia('GUIA-BARRIDO-50-220')
        config = self.env['madenat.ingestion.config']
        mapping = config.get_width_s2s_map()
        overwidth = config.get_s2s_overwidth_inches()

        # Lista completa ordenada sin duplicados
        anchos_set = set(range(50, 225, 5)).union({115, 135, 160, 165})
        anchos_lista = sorted(list(anchos_set))

        for w_mm in anchos_lista:
            line = self._make_line(
                guia, ancho_mm=float(w_mm), thickness_visual='6/4',
                width_visual=f"{w_mm}mm", largo_m=4.0, pieces=100
            )
            line.flush_recordset()
            w_key = int(round(w_mm))
            if w_key in mapping:
                s2s_in = mapping[w_key][0] + overwidth
            else:
                s2s_in = float(w_mm) / 25.4
            expected = round((1.5 * s2s_in * 4.0 * 100) / 1550.0031, 3)
            self.assertAlmostEqual(
                line.vol_shipment_m3, expected, places=3,
                msg=f"Barrido falló en {w_mm} mm: obtenido {line.vol_shipment_m3}, esperado {expected}"
            )

    def test_12_parameters_declared_in_data_xml_with_noupdate(self):
        """E2: Los parámetros (s2s_overwidth, out_of_table_behavior, direct_width_min_mm, drying) existen en XML con noupdate=1."""
        import os
        from xml.etree import ElementTree as ET
        xml_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ingestion_config.xml')
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Encontrar bloques data con noupdate="1"
        data_noupdate_nodes = [d for d in root.findall('data') if d.get('noupdate') == '1']
        self.assertTrue(data_noupdate_nodes, "Debe existir al menos un bloque <data noupdate='1'> en ingestion_config.xml")

        expected_records = {
            'param_s2s_overwidth_inches': 'madenat.s2s_overwidth_inches',
            'param_out_of_table_behavior': 'madenat.out_of_table_behavior',
            'param_direct_width_min_mm': 'madenat.direct_width_min_mm',
            'param_drying_temp_min_c': 'madenat.drying_temp_min_c',
            'param_drying_temp_max_c': 'madenat.drying_temp_max_c',
            'param_drying_duration_min_hours': 'madenat.drying_duration_min_hours',
            'param_drying_duration_max_hours': 'madenat.drying_duration_max_hours',
        }

        found_records = {}
        for d in data_noupdate_nodes:
            for rec in d.findall('record'):
                r_id = rec.get('id')
                if r_id in expected_records:
                    key_field = rec.find("./field[@name='key']")
                    if key_field is not None:
                        found_records[r_id] = key_field.text.strip()

        self.assertEqual(len(found_records), len(expected_records),
                         f"Faltan parámetros en <data noupdate='1'>. Esperados: {expected_records.keys()}, encontrados: {found_records.keys()}")
        for r_id, exp_key in expected_records.items():
            self.assertEqual(found_records.get(r_id), exp_key)

    def test_13_branch_resolution_order_all_four_branches(self):
        """E4: Demuestra las 4 ramas canónicas de resolución de ancho y su orden de prelación.
        
        Rama 1: Manual (export_width_manual_inches)
        Rama 2: Tabla S2S activa (lumber.width.s2s.map)
        Rama 3: Documental en pulgadas S2S (is_s2s_inches=True)
        Rama 4: Directo mm / 25.4
        """
        guia = self._make_guia('GUIA-4-RAMAS')

        # ── RAMA 1: MANUAL (Prevalece sobre tabla, documental y directo) ─────────
        # Ancho 150 mm en tabla daría 5.750", pero forzado manual a 5.625" (5 5/8)
        line_manual = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203,
            export_width_manual_inches=5.625,
            export_width_manual_reason='Ajuste manual comercial',
            is_s2s_inches=True,  # Incluso si tiene señal documental, prevalece manual
        )
        line_manual.flush_recordset()
        # (1.25 * 5.625 * 4.05 * 203) / 1550.0031 = 3.730 m3
        self.assertAlmostEqual(line_manual.vol_shipment_m3, 3.730, places=3)

        # ── RAMA 2: TABLA S2S ACTIVA (Prevalece sobre documental y directo) ──────
        # Ancho 150 mm sin manual: tabla S2S (5.625") + 0.125" = 5.750"
        line_table = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203,
        )
        line_table.flush_recordset()
        # (1.25 * 5.750 * 4.05 * 203) / 1550.0031 = 3.812 m3
        self.assertAlmostEqual(line_table.vol_shipment_m3, 3.812, places=3)

        # ── RAMA 3: DOCUMENTAL EN PULGADAS S2S (JCE 5/4x5.3/8x16) ───────────────
        # 5 3/8" = 136.525 mm (ausente de tabla como rough mm), con señal is_s2s_inches=True:
        # Aplica S2S overwidth una vez: 5.375" + 0.125" = 5.500"
        line_jce = self._make_line(
            guia, ancho_mm=136.525, thickness_visual='5/4', width_visual='5 3/8',
            largo_m=4.8768, pieces=231,
            is_s2s_inches=True,
        )
        line_jce.flush_recordset()
        # (1.25 * 5.500 * 4.8768 * 231) / 1550.0031 = 4.9969 -> 4.997 m3
        self.assertAlmostEqual(line_jce.vol_shipment_m3, 4.997, places=3)

        # ── RAMA 4: DIRECTO (Ausente de tabla y sin señal documental) ───────────
        # 135 mm ausente de tabla y sin is_s2s_inches -> 135 / 25.4 = 5.31496"
        line_direct = self._make_line(
            guia, ancho_mm=135.0, thickness_visual='7/4', width_visual='5 1/4',
            largo_m=3.2, pieces=10,
            is_s2s_inches=False,
        )
        line_direct.flush_recordset()
        # (1.75 * (135/25.4) * 3.2 * 10) / 1550.0031 = 0.19202 -> 0.192 m3
        self.assertAlmostEqual(line_direct.vol_shipment_m3, 0.192, places=3)

    def test_14_s2s_empty_table_raises_user_error(self):
        """F1: Si no hay registros activos en lumber.width.s2s.map, falla con UserError y log estructurado."""
        config = self.env['madenat.ingestion.config']
        s2s_records = self.env['lumber.width.s2s.map'].search([])
        orig_states = {rec.id: rec.active for rec in s2s_records}
        try:
            # Desactivar todos los registros
            s2s_records.write({'active': False})
            with self.assertRaises(UserError) as cm:
                config.get_width_s2s_map()
            self.assertIn("No existen registros activos", str(cm.exception))

            # Verificar que resolve_export_width también falla al no encontrar tabla
            with self.assertRaises(UserError):
                config.resolve_export_width(100.0)
        finally:
            for rec in s2s_records:
                rec.write({'active': orig_states[rec.id]})

    def test_15_s2s_width_115mm_resolution(self):
        """F1: 115 mm en lumber.width.s2s.map es 4.375 (4 3/8) + sobreancho 0.125 = 4.500 pulgadas."""
        config = self.env['madenat.ingestion.config']
        mapping = config.get_width_s2s_map()
        self.assertIn(115, mapping, "115 mm debe existir en lumber.width.s2s.map")
        dec, label = mapping[115]
        self.assertEqual(dec, 4.375, f"115 mm debe ser 4.375 (4 3/8), no 4.125. Obtenido {dec}")
        self.assertEqual(label, "4 3/8")

        resolved_w = config.resolve_export_width(115.0)
        self.assertAlmostEqual(resolved_w, 4.500, places=3,
                               msg=f"115 mm resuelto debe ser 4.375 + 0.125 = 4.500. Obtenido {resolved_w}")

        guia = self._make_guia('GUIA-115MM-TEST')
        line = self._make_line(
            guia, ancho_mm=115.0, thickness_visual='6/4', width_visual='115mm',
            largo_m=4.0, pieces=100
        )
        line.flush_recordset()
        # (1.5 * 4.500 * 4.0 * 100) / 1550.0031 = 1.7419... -> 1.742 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 1.742, places=3)

    def test_16_no_static_fallback_dictionary_in_code(self):
        """F1: No existe diccionario estático de respaldo en madenat_ingestion_config.py."""
        import inspect
        config = self.env['madenat.ingestion.config']
        method_source = inspect.getsource(type(config).get_width_s2s_map)
        self.assertNotIn("4.125", method_source, "No debe existir valor erróneo 4.125 en get_width_s2s_map")
        self.assertNotIn("2.625", method_source, "No debe existir diccionario estático con 2.625 en get_width_s2s_map")
        self.assertNotIn("hardcode legacy", method_source.lower(), "No debe existir mención de hardcode legacy")

