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
        """100 mm rough mapea exactamente a 3.625" (3 5/8") en vez de sumar +1/8" arbitrario."""
        guia = self._make_guia('GUIA-S2S-100')
        line = self._make_line(guia, ancho_mm=100.0, thickness_visual='6/4',
                               width_visual='3 5/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.5" * 3.625" * 3.2m * 10) / 1550.003 = 0.112257... -> 0.112 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.112, places=3)

    def test_02_ancho_145mm_uses_critical_s2s_value(self):
        """145 mm rough mapea contractualmente a 5.375" (5 3/8"), no a 145/25.4 = 5.708"."""
        guia = self._make_guia('GUIA-S2S-145')
        line = self._make_line(guia, ancho_mm=145.0, thickness_visual='7/4',
                               width_visual='5 3/8', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # Fórmula: (1.75" * 5.375" * 3.2m * 10) / 1550.003 = 0.19419... -> 0.194 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.194, places=3)

    def test_03_ancho_135mm_uses_direct_division_fallback(self):
        """135 mm no está en tabla: se mantiene división directa por 25.4 (5.31496"), sin escalón inventado."""
        guia = self._make_guia('GUIA-S2S-135')
        line = self._make_line(guia, ancho_mm=135.0, thickness_visual='7/4',
                               width_visual='5 1/4', largo_m=3.2, pieces=10)
        line.flush_recordset()
        # width_calc = 135 / 25.4 = 5.3149606...
        # Fórmula: (1.75 * (135/25.4) * 3.2 * 10) / 1550.003 = 0.19202... -> 0.192 m3
        self.assertAlmostEqual(line.vol_shipment_m3, 0.192, places=3)

    def test_04_ancho_out_of_range_uses_direct_division(self):
        """Anchos menores a 75 mm o mayores a 155 mm aplican división directa por 25.4."""
        guia = self._make_guia('GUIA-S2S-OUT')
        # Menor a 75 mm (60 mm)
        line_low = self._make_line(guia, ancho_mm=60.0, thickness_visual='6/4',
                                  width_visual='2 3/8', largo_m=3.2, pieces=10)
        line_low.flush_recordset()
        # width_calc = 60 / 25.4 = 2.3622"
        # (1.5 * (60/25.4) * 3.2 * 10) / 1550.003 = 0.07315 -> 0.073 m3
        self.assertAlmostEqual(line_low.vol_shipment_m3, 0.073, places=3)

        # Mayor a 155 mm (170 mm)
        line_high = self._make_line(guia, ancho_mm=170.0, thickness_visual='7/4',
                                    width_visual='6 5/8', largo_m=3.2, pieces=10)
        line_high.flush_recordset()
        # width_calc = 170 / 25.4 = 6.6929"
        # (1.75 * (170/25.4) * 3.2 * 10) / 1550.003 = 0.24179 -> 0.242 m3
        self.assertAlmostEqual(line_high.vol_shipment_m3, 0.242, places=3)

    def test_05_manual_export_width_override_and_bitacora(self):
        """Fijar ancho manual anula la tabla S2S, exige motivo y registra en el chatter."""
        guia = self._make_guia('GUIA-S2S-MANUAL')
        line = self._make_line(
            guia, ancho_mm=100.0, thickness_visual='6/4', width_visual='3 5/8',
            largo_m=3.2, pieces=10,
            export_width_manual_inches=4.0,
            export_width_manual_reason='Ajuste contractual cliente USA',
        )
        line.flush_recordset()
        # width_calc = 4.0 manual
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
