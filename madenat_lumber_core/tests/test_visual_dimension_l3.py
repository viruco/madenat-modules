# -*- coding: utf-8 -*-
"""
Pruebas de Resolución Visual de Anchos Basada en Datos (Bloque 4L / L3 / AD-124).
"""

from decimal import Decimal
from odoo.tests.common import TransactionCase
from odoo.addons.madenat_lumber_core.models.utils_uom import r3, MBF_TO_M3


class TestVisualDimensionL3(TransactionCase):
    """Pruebas unitarias para la resolución visual basada en lumber.width.s2s.map."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.S2SMap = cls.env['lumber.width.s2s.map']

    def test_01_resolucion_150mm_da_fraccion_s2s(self):
        """L3: 150 mm resuelve a su fracción S2S '5 5/8', eliminando la asimetría."""
        visual = self.Guia._compute_visual_dimension(150.0, 'width')
        self.assertEqual(visual, '5 5/8', "150 mm debe resolver a '5 5/8'")

    def test_02_anchos_tabla_mantienen_fraccion(self):
        """L3: 100, 125, 145 y 155 mm mantienen su fracción S2S canónica."""
        expected = {
            100: '3 5/8',
            125: '4 5/8',
            145: '5 3/8',
            155: '5 7/8',
        }
        for mm, frac in expected.items():
            visual = self.Guia._compute_visual_dimension(float(mm), 'width')
            self.assertEqual(visual, frac, f"{mm} mm debe resolver a '{frac}'")

    def test_03_anchos_fuera_de_tabla_quedan_en_mm(self):
        """L3: 160, 170, 175, 180, 195 y 200 mm quedan como 'Nmm'."""
        out_widths = [160, 170, 175, 180, 195, 200]
        for mm in out_widths:
            visual = self.Guia._compute_visual_dimension(float(mm), 'width')
            self.assertEqual(visual, f"{mm}mm", f"{mm} mm debe resolver a '{mm}mm'")

    def test_04_edicion_de_tabla_cambia_calculo_nuevo(self):
        """L3: Una edición en lumber.width.s2s.map altera inmediatamente cálculos nuevos."""
        new_rec = self.S2SMap.create({
            'rough_mm': 160,
            's2s_decimal': 6.2500,
            's2s_label': '6 1/4',
            'active': True,
        })
        visual_160 = self.Guia._compute_visual_dimension(160.0, 'width')
        self.assertEqual(visual_160, '6 1/4', "Cálculo nuevo debe reflejar la entrada creada en tabla")
        new_rec.unlink()
        visual_160_after = self.Guia._compute_visual_dimension(160.0, 'width')
        self.assertEqual(visual_160_after, '160mm', "Tras eliminar entrada, cálculo nuevo vuelve a '160mm'")

    def test_05_coherencia_mbf_fracciones_vs_m3_s2s(self):
        """L3: MBF por fracciones coincide con MBF desde m³ (dif < 0.001) para anchos S2S."""
        active_recs = self.S2SMap.search([('active', '=', True)], order='rough_mm')
        self.assertGreaterEqual(len(active_recs), 14, "Deben existir al menos 14 anchos activos")

        pieces = Decimal('100')
        thick_in = Decimal('1.5')
        length_m = Decimal('4.0')
        const_1550 = Decimal('1550.003')
        factor_mbf_m3 = MBF_TO_M3
        length_ft = length_m / Decimal('0.3048')

        for r in active_recs:
            w_exp = Decimal(str(r.s2s_decimal)) + Decimal('0.125')
            # MBF fraccional exportación
            mbf_frac = (thick_in * w_exp * length_ft / Decimal('12')) / Decimal('1000') * pieces
            # Vol m3 exportación
            vol_m3 = (pieces * thick_in * w_exp * length_m) / const_1550
            # MBF obtenido a partir del m3
            mbf_from_m3 = vol_m3 / factor_mbf_m3

            diff = abs(r3(mbf_frac) - r3(mbf_from_m3))
            self.assertLess(
                diff, 0.001,
                f"Para {r.rough_mm}mm ({r.s2s_label}), dif MBF ({r3(mbf_frac)}) vs ({r3(mbf_from_m3)}) debe ser < 0.001"
            )
