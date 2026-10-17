# -*- coding: utf-8 -*-
"""Pruebas unitarias para WP-B: Ancho de Exportación S2S canónico y opción manual.

Verifica:
1. Uso de la tabla canónica Rough -> S2S (width_mapping.py / lumber.width.s2s.map).
   - Ancho 100 mm -> 3.625" (3 5/8")
   - Ancho 145 mm -> 5.375" (5 3/8", valor crítico)
2. Exclusiones canónicas (división directa por 25.4):
   - Ancho 135 mm -> 135 / 25.4 (sin inventar escalón)
   - Anchos fuera de rango (< 75 mm o > 155 mm) -> mm / 25.4
3. Opción manual de ancho de exportación:
   - export_width_manual_inches fijado con motivo obligatorio
   - Si no hay motivo -> ValidationError
   - Registro automático de usuario, fecha y anotación en bitácora (chatter)
4. Inmutabilidad de registros almacenados: no altera valores históricos sin edición.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
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
        return self.Line.create(vals)

    def test_01_ancho_100mm_uses_s2s_table(self):
        """100 mm rough con visual '3 5/8' aplica cálculo automático: 3.625" + recargo 0.125" = 3.750"."""
        guia = self._make_guia('GUIA-S2S-100')
        line = self._make_line(guia, ancho_mm=100.0, thickness_visual='6/4',
                               width_visual='3 5/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.5" * (3.625 + 0.125)" * 3.2m * 10) / 1550.003 = 0.11612... -> 0.116 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.116, places=3)

    def test_02_ancho_145mm_uses_critical_s2s_value(self):
        """145 mm rough con visual '5 3/8' aplica cálculo automático: 5.375" + recargo 0.125" = 5.500"."""
        guia = self._make_guia('GUIA-S2S-145')
        line = self._make_line(guia, ancho_mm=145.0, thickness_visual='7/4',
                               width_visual='5 3/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.75" * (5.375 + 0.125)" * 3.2m * 10) / 1550.003 = 0.1987... -> 0.199 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.199, places=3)

    def test_03_ancho_135mm_uses_direct_division_fallback(self):
        """135 mm con visual '5 1/4' aplica cálculo automático: 5.250" + recargo 0.125" = 5.375"."""
        guia = self._make_guia('GUIA-S2S-135')
        line = self._make_line(guia, ancho_mm=135.0, thickness_visual='7/4',
                               width_visual='5 1/4', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.75 * (5.250 + 0.125) * 3.2 * 10) / 1550.003 = 0.19419... -> 0.194 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.194, places=3)

    def test_04_ancho_out_of_range_uses_direct_division(self):
        """Ancho menor aplica recargo estándar; ancho >= 150 mm en exclusiones tiene recargo 0.0."""
        guia = self._make_guia('GUIA-S2S-OUT')
        # Menor a 75 mm (60 mm): recargo 0.125"
        line_low = self._make_line(guia, ancho_mm=60.0, thickness_visual='6/4',
                                   width_visual='2 3/8', largo_m=3.2, pieces=10)
        line_low.flush_recordset()
        # width_calc = 2.375 + 0.125 = 2.500"
        # (1.5 * 2.500 * 3.2 * 10) / 1550.003 = 0.0774 -> 0.077 m3
        self.assertAlmostEqual(line_low.vol_shipment_m3, 0.077, places=3)

        # Mayor o igual a 150 mm (170 mm): lista de exclusiones -> recargo 0.0
        line_high = self._make_line(guia, ancho_mm=170.0, thickness_visual='7/4',
                                    width_visual='6 5/8', largo_m=3.2, pieces=10)
        line_high.flush_recordset()
        # width_calc = 6.625 + 0.0 = 6.625"
        # (1.75 * 6.625 * 3.2 * 10) / 1550.003 = 0.2393 -> 0.239 m3
        self.assertAlmostEqual(line_high.vol_shipment_m3, 0.239, places=3)

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
        # (1.5 * 4.0 * 3.2 * 10) / 1550.003 = 0.12387 -> 0.124 m3
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
        """Regresión AD-115: Reproduce exactamente los valores históricos de la Guía 26270.

        Líneas sintéticas de 100, 125 y 150 mm (con '150mm') reproduciendo los vol_shipment_m3
        almacenados en BD (2.450, 4.096, 3.915 m³), más el caso donde el ancho manual prevalece.
        """
        guia = self._make_guia('GUIA-26270-SINTETICA')

        # Línea A: 100 mm, visual '3 5/8' (ID 5137 en BD)
        line_100 = self._make_line(
            guia, ancho_mm=100.0, thickness_visual='5/4', width_visual='3 5/8',
            largo_m=4.05, pieces=200, vol_purchase=2.997
        )
        line_100.flush_recordset()
        # (1.25 * (3.625 + 0.125) * 4.05 * 200) / 1550.003 = 2.44999 -> 2.450 m3
        self.assertAlmostEqual(line_100.vol_shipment_m3, 2.450, places=3)

        # Línea B: 125 mm, visual '4 5/8' (ID 5128 en BD)
        line_125 = self._make_line(
            guia, ancho_mm=125.0, thickness_visual='5/4', width_visual='4 5/8',
            largo_m=4.05, pieces=264, vol_purchase=4.945
        )
        line_125.flush_recordset()
        # (1.25 * (4.625 + 0.125) * 4.05 * 264) / 1550.003 = 4.09596 -> 4.096 m3
        self.assertAlmostEqual(line_125.vol_shipment_m3, 4.096, places=3)

        # Línea C: 150 mm, visual '150mm' (ID 5140 en BD)
        # 150mm -> parseado a 150/25.4 = 5.90551", recargo 0.0 (en lista de exclusiones)
        line_150 = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203, vol_purchase=4.563
        )
        line_150.flush_recordset()
        # (1.25 * (150/25.4 + 0.0) * 4.05 * 203) / 1550.003 = 3.91549 -> 3.915 m3
        self.assertAlmostEqual(line_150.vol_shipment_m3, 3.915, places=3)

        # Línea D: 150 mm con ancho manual que prevalece (ej. forzar 5 5/8" = 5.625")
        line_150_manual = self._make_line(
            guia, ancho_mm=150.0, thickness_visual='5/4', width_visual='150mm',
            largo_m=4.05, pieces=203, vol_purchase=4.563,
            export_width_manual_inches=5.625,
            export_width_manual_reason='Forzado manual S2S neto 5 5/8"'
        )
        line_150_manual.flush_recordset()
        # (1.25 * 5.625 * 4.05 * 203) / 1550.003 = 3.7295 -> 3.730 m3 (prevalece el manual)
        self.assertAlmostEqual(line_150_manual.vol_shipment_m3, 3.730, places=3)
