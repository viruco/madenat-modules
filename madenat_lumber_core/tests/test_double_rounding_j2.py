# -*- coding: utf-8 -*-
"""
Pruebas unitarias para J2 (AD-122 / Bloque 4J):
Auditoría y corrección del doble redondeo en volúmenes y MBF.
Garantiza redondeo único con r3() (ROUND_HALF_UP, Decimal) sobre el valor final.
"""
from decimal import Decimal
import unittest
from odoo.tests.common import TransactionCase
from odoo.addons.madenat_lumber_core.models.utils_uom import r3, calculate_volume_imperial_to_m3


class TestDoubleRoundingJ2(TransactionCase):

    def test_01_boundary_case_anti_double_rounding(self):
        """J2: Caso límite 3.7424999 vs 3.7425 demostrando prevención de doble redondeo."""
        val_sub_half = Decimal('3.7424999')
        val_exact_half = Decimal('3.7425')

        # Con doble redondeo defectuoso: round(x, 4) -> round(x, 3)
        double_rounded = r3(round(float(val_sub_half), 4))
        # Con redondeo canónico directo único:
        single_rounded = r3(val_sub_half)

        # 3.7424999 está estrictamente por debajo de la mitad; debe ser 3.742, NO 3.743
        self.assertEqual(single_rounded, 3.742,
                         "Redondeo único r3() de 3.7424999 debe ser 3.742")
        self.assertEqual(double_rounded, 3.743,
                         "Doble redondeo introducía sesgo alcista erróneo (3.743)")

        # En cambio, 3.7425 exacto sí sube a 3.743 por ROUND_HALF_UP
        self.assertEqual(r3(val_exact_half), 3.743,
                         "3.7425 exacto con ROUND_HALF_UP debe subir a 3.743")

    def test_02_vector_planilla_s2s_unchanged(self):
        """J2: Vector canónico S2S de la planilla permanece intacto (1.742 m³)."""
        # 100 piezas, 1.5" x 4.500" x 4.0 m
        vol_exact = (Decimal('100') * Decimal('1.5') * Decimal('4.500') * Decimal('4.0')) / Decimal('1550.003')
        vol_r3 = r3(vol_exact)
        self.assertEqual(vol_r3, 1.742,
                         "El volumen S2S canónico para 100 pzas debe ser exactamente 1.742 m³")

    def test_03_vector_blanks_clear_unchanged(self):
        """J2: Vector Blanks Clear (fórmula f5085) permanece idéntico."""
        # 100 piezas, espesor 1.25" (-1/16" deducción = 1.1875), ancho 4" (+1/8" = 4.125), largo 10 ft
        vol_blank = (Decimal('1.1875') * Decimal('4.125') * Decimal('10.0') * Decimal('100')) / Decimal('5085.312')
        vol_r3 = r3(vol_blank)
        self.assertEqual(vol_r3, 0.963,
                         "El volumen Blanks Clear debe redondearse a 0.963 m³")

    def test_04_mbf_lot_single_rounding(self):
        """J2: MBF en lote se calcula sin redondeo intermedio espurio."""
        Lot = self.env['stock.lot']
        # Simular cálculo fraccional: 1.5" x 3.625" x 10' x 100 piezas
        # board_feet = (1.5 * 3.625 * 10 * 100) / 12 = 453.125
        # mbf = 453.125 / 1000 = 0.453125
        mbf_raw = Lot._calculate_mbf_from_fractions('1 1/2', '3 5/8', "10'", 100)
        # El retorno debe ser float sin truncar/redondear a 4 decimales
        self.assertAlmostEqual(mbf_raw, 0.453125, places=5)
        # Y r3() en el lote lo lleva al valor final de negocio:
        self.assertEqual(r3(mbf_raw), 0.453)
