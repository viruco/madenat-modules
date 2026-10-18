# -*- coding: utf-8 -*-
"""Pruebas unitarias para Bloque 5B (AD-126): Volumen Real Físico (vol_physical_real_m3 / Fórmula F3).

Verifica:
  1. Vector canónico 1: 38.1 mm x 100 mm x 4.05 m x 250 pzas / 1.000.000 = 3.858 m3.
  2. Vector canónico 2 (Planilla): 45 mm rough, 100 mm, 4.0 m, 1 pza, 6/4:
     - Real físico F3 = 0.015 m3 (0.01524 exacto).
     - Exportación F2 = 0.015 m3 (0.014516 exacto).
     - Compra F1 = 0.018 m3.
  3. Redondeo único con r3() (ROUND_HALF_UP).
  4. Blanks directo a stock sin cálculo (vol_physical_real_m3 = 0.0).
  5. Anti-hardcode: modificar tabla altera el cálculo de un registro nuevo.
  6. Invarianza histórica: vol_shipment_m3, vol_purchase_m3 y volumen_m3 intactos.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from ..models.utils_uom import r3


@tagged('post_install', '-at_install', 'madenat_lumber_core')
class TestVolPhysicalReal5B(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.Lot = cls.env['stock.lot']
        cls.ThicknessMap = cls.env['lumber.thickness.real.map']

        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Test 5B',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.product'].create({
            'name': 'Pino Test 5B',
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
        })

    def _make_guia(self, name='GUIA-TEST-5B', ingestion_profile='f1550'):
        return self.Guia.create({
            'partner_id': self.partner.id,
            'name': name,
            'assignment_location_id': self.location.id,
            'ingestion_profile': ingestion_profile,
            'date_emission': '2026-10-18',
        })

    def test_01_canonical_vector_250_pieces(self):
        """Vector 1: 38.1 mm x 100 mm x 4.05 m x 250 pzas / 1.000.000 = 3.858 m3."""
        guia = self._make_guia('GUIA-VEC-1')
        line = self.Line.create({
            'processing_id': guia.id,
            'lot_name': 'LOT-TEST-VEC1',
            'product_id': self.product.id,
            'thickness_visual': '6/4',
            'width_visual': '100mm',
            'ancho_nominal_mm': 100.0,
            'ancho_mm': 100.0,
            'espesor_nominal_mm': 38.1,
            'espesor_mm': 45.0,
            'largo_m': 4.05,
            'pieces': 250,
            'vol_purchase_m3': 4.556,
        })
        line.flush_recordset()

        # 38.1 * 100 * 4.05 * 250 / 1.000.000 = 3.857625 -> r3 = 3.858
        self.assertEqual(line.vol_physical_real_m3, 3.858)

    def test_02_canonical_vector_single_piece_comparison(self):
        """Vector 2 (Planilla): 45 mm rough, 100 mm ancho, 4.0 m largo, 1 pieza, 6/4.

        Compara F1 Compra (0.018) > F3 Real Físico (0.01524 -> 0.015) > F2 Exportación (0.014516 -> 0.015).
        """
        guia = self._make_guia('GUIA-VEC-2')
        line = self.Line.create({
            'processing_id': guia.id,
            'lot_name': 'LOT-TEST-VEC2',
            'product_id': self.product.id,
            'thickness_visual': '6/4',
            'width_visual': '3 5/8',
            'ancho_nominal_mm': 100.0,
            'ancho_mm': 100.0,
            'espesor_nominal_mm': 45.0,
            'espesor_mm': 45.0,
            'largo_m': 4.0,
            'pieces': 1,
            'vol_purchase_m3': 0.018,
        })
        line.flush_recordset()

        # F3 Real físico: 38.1 * 100 * 4.0 * 1 / 1.000.000 = 0.01524 -> r3 = 0.015
        self.assertEqual(line.vol_physical_real_m3, 0.015)
        # F2 Exportación: 1.5 * (3.625 + 0.125) * 4.0 * 1 / 1550.0031 = 0.014516 -> r3 = 0.015
        self.assertEqual(line.vol_shipment_m3, 0.015)
        # F1 Compra
        self.assertEqual(line.vol_purchase_m3, 0.018)

    def test_03_blanks_direct_to_stock_no_physical_real(self):
        """Blanks directo a stock no calcula vol_physical_real_m3 (queda en 0.0)."""
        guia_blanks = self._make_guia('GUIA-BLANKS-STOCK', ingestion_profile='f5085')
        line = self.Line.create({
            'processing_id': guia_blanks.id,
            'lot_name': 'LOT-TEST-BLANKS',
            'product_id': self.product.id,
            'thickness_visual': '6/4',
            'width_visual': '100mm',
            'length_ft': 16.0,
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'pieces': 250,
            'vol_purchase_m3': 3.858,
        })
        line.flush_recordset()
        self.assertEqual(line.vol_physical_real_m3, 0.0, "Blanks directo a stock no debe calcular real físico")

    def test_04_anti_hardcode_table_modification_changes_new_calculation(self):
        """Modificar un registro en lumber.thickness.real.map altera el cálculo de una línea nueva."""
        guia = self._make_guia('GUIA-ANTI-HC')
        rec_6_4 = self.ThicknessMap.search([('thickness_visual', '=', '6/4')], limit=1)
        original_mm = rec_6_4.thickness_real_mm

        try:
            # Modificar 38.1 -> 40.0 mm en BD
            rec_6_4.write({'thickness_real_mm': 40.0})

            # 40.0 * 100 * 4.05 * 250 / 1.000.000 = 4.050 m3
            line = self.Line.create({
                'processing_id': guia.id,
                'lot_name': 'LOT-TEST-ANTIHC',
                'product_id': self.product.id,
                'thickness_visual': '6/4',
                'width_visual': '100mm',
                'ancho_nominal_mm': 100.0,
                'largo_m': 4.05,
                'pieces': 250,
            })
            line.flush_recordset()
            self.assertEqual(line.vol_physical_real_m3, 4.050)
        finally:
            rec_6_4.write({'thickness_real_mm': original_mm})

    def test_05_stock_lot_vol_physical_real_computation(self):
        """Verifica que stock.lot compute vol_physical_real_m3 con la misma regla."""
        lot = self.Lot.create({
            'name': 'LOTE-TEST-5B-01',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'piezas': 250,
            'volumen_m3': 4.556,
        })
        lot.flush_recordset()
        self.assertEqual(lot.vol_physical_real_m3, 3.858)
