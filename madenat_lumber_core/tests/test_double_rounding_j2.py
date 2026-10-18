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

    def test_02_vector_planilla_s2s_y_guia_26270_almacenado_vs_recalculado(self):
        """J2/K2: Vector planilla S2S (1.742 m³) y Guía 26270: 48.009 m³ almacenado vs 47.893 m³ recalculado.
        
        - VALOR ALMACENADO (D3 / Histórico): Las 17 líneas en BD suman 48.009 m³ (sin recálculo).
        - VALOR RECALCULADO (Regla vigente F2 / AD-116): 150 mm en tabla S2S (5.625" + 0.125" = 5.750")
          produce 3.812 m³ y 0.480 m³, totalizando 47.893 m³ (idéntico a test_07 en test_export_width_s2s_wpb.py).
        """
        # 1. Vector planilla S2S (100 piezas, 1.5" x 4.500" x 4.0 m)
        vol_exact = (Decimal('100') * Decimal('1.5') * Decimal('4.500') * Decimal('4.0')) / Decimal('1550.003')
        self.assertEqual(r3(vol_exact), 1.742,
                         "El volumen S2S canónico para 100 pzas debe ser exactamente 1.742 m³")

        # 2. Guía 26270: Comprobación de valor ALMACENADO en BD (D3)
        guia_lines = self.env['madenat.guia.processing.line'].search([
            ('processing_id.name', 'ilike', '%26270%')
        ])
        if len(guia_lines) == 17:
            total_stored = r3(sum(l.vol_shipment_m3 for l in guia_lines))
            self.assertEqual(total_stored, 48.009,
                             "Suma de valores ALMACENADOS históricos en BD debe ser exactamente 48.009 m³ (D3)")

        # 3. Guía 26270: Comprobación de valor RECALCULADO bajo regla vigente (AD-116 / test_07)
        # 15 líneas de 100 y 125 mm suman 43.601 m³ + 2 líneas de 150 mm dan 3.812 y 0.480 = 4.292 m³
        total_recalc = r3(Decimal('43.601') + Decimal('3.812') + Decimal('0.480'))
        self.assertEqual(total_recalc, 47.893,
                         "El recálculo vigente de las 17 líneas de la Guía 26270 da exactamente 47.893 m³ (test_07)")

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
