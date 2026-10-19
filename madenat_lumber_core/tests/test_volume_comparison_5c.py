# -*- coding: utf-8 -*-
"""Pruebas unitarias para Bloque 5C (AD-126): Comparativo de los Tres Volúmenes.

Verifica:
  1. Cálculo de métricas: vol_diff_pct (% Dif.Vol) con fórmula ((Export - Compra) / Compra) * 100.
  2. Resaltado de excepciones: is_export_greater_nominal = True cuando exportación > nominal.
  3. Casos métricos / idénticos: is_export_greater_nominal = False cuando exportación == nominal.
  4. Carga exitosa de vistas: tree (readonly con create=false, edit=false), pivot y search.
  5. Configuración de acción y menú: permisos para Operaciones, Auditoría y Contabilidad.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat_lumber_core')
class TestVolumeComparison5C(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lot = cls.env['stock.lot']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Test 5C',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.product'].create({
            'name': 'Pino Test 5C',
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
        })

    def test_01_metrics_computation_and_percentages(self):
        """Cálculo de porcentaje de diferencia de volumen entre exportación y compra."""
        lot = self.Lot.create({
            'name': 'LOT-5C-NORMAL',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 1,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100,
            'largo_m': 4.0,
            'vol_purchase_m3': 0.018,
            'vol_shipment_m3': 0.015,
        })
        lot.flush_recordset()

        self.assertEqual(lot.physical_status, 'calculado')
        # (0.015 - 0.018) / 0.018 * 100 = -16.6666... -> -16.67
        self.assertAlmostEqual(lot.vol_diff_pct, -16.67, places=2)
        self.assertFalse(lot.is_export_greater_nominal, "Exportación es menor que nominal, no debe alertar")

    def test_02_resaltado_excepcion_exportacion_mayor_que_nominal(self):
        """Resalta cualquier línea donde la exportación supere al nominal de compra."""
        # Caso anómalo: Exportación (1.200 m3) > Compra Nominal (1.000 m3)
        lot_anomalo = self.Lot.create({
            'name': 'LOT-5C-ANOMALO',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 100,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100,
            'largo_m': 4.0,
            'vol_purchase_m3': 1.000,
            'vol_shipment_m3': 1.200,
        })
        lot_anomalo.flush_recordset()
        self.assertEqual(lot_anomalo.physical_status, 'calculado')
        self.assertTrue(lot_anomalo.is_export_greater_nominal, "Debe activar bandera de alerta cuando export > nominal")
        self.assertEqual(lot_anomalo.vol_diff_pct, 20.0)

        # Caso métrico / idéntico: Exportación == Nominal
        lot_metrico = self.Lot.create({
            'name': 'LOT-5C-METRICO',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 100,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100,
            'largo_m': 4.0,
            'vol_purchase_m3': 1.000,
            'vol_shipment_m3': 1.000,
        })
        lot_metrico.flush_recordset()
        self.assertEqual(lot_metrico.physical_status, 'calculado')
        self.assertFalse(lot_metrico.is_export_greater_nominal, "Exportación igual a nominal no debe alertar")
        self.assertEqual(lot_metrico.vol_diff_pct, 0.0)

    def test_03_view_definitions_and_actions_load(self):
        """Comprueba que las vistas comparativas (tree, pivot, search) y la acción cargan sin error."""
        tree_view = self.env.ref('madenat_lumber_core.view_stock_lot_volume_comparison_tree')
        pivot_view = self.env.ref('madenat_lumber_core.view_stock_lot_volume_comparison_pivot')
        search_view = self.env.ref('madenat_lumber_core.view_stock_lot_volume_comparison_search')
        action = self.env.ref('madenat_lumber_core.action_stock_lot_volume_comparison')

        self.assertTrue(tree_view.exists(), "La vista tree debe existir")
        self.assertTrue(pivot_view.exists(), "La vista pivot debe existir")
        self.assertTrue(search_view.exists(), "La vista search debe existir")
        self.assertTrue(action.exists(), "La acción de ventana debe existir")

        # Verificar que el modo de vista y contexto sean de solo lectura
        self.assertIn('create', action.context)
        self.assertIn("'create': False", action.context)

        # Carga estructural vía get_views
        views_dict = self.Lot.get_views([(tree_view.id, 'list'), (pivot_view.id, 'pivot')])
        self.assertIn('views', views_dict)
        self.assertIn('list', views_dict['views'])
        self.assertIn('pivot', views_dict['views'])

    def test_04_menu_permissions_and_hierarchy(self):
        """Comprueba que el menú existe bajo Control de Lotes y posee los grupos autorizados."""
        menu = self.env.ref('madenat_lumber_core.menu_stock_lot_volume_comparison')
        self.assertTrue(menu.exists(), "El menuitem comparativo debe existir")

        group_ops = self.env.ref('madenat_lumber_core.group_madenat_operaciones')
        group_audit = self.env.ref('madenat_lumber_core.group_madenat_auditoria')
        group_contab = self.env.ref('madenat_lumber_core.group_madenat_contabilidad')

        menu_groups = menu.groups_id
        self.assertIn(group_ops, menu_groups, "Operaciones debe tener acceso al menú")
        self.assertIn(group_audit, menu_groups, "Auditoría debe tener acceso al menú")
        self.assertIn(group_contab, menu_groups, "Contabilidad debe tener acceso al menú")

    def test_05_physical_status_and_empty_percentage_when_not_calculated(self):
        """R3 (AD-126): physical_status y porcentaje vacío cuando no es calculado.

        1. Línea con mapeo: status 'calculado', F3 calculado, vol_diff_pct no vacío.
        2. Línea sin mapeo: status 'sin_mapeo', F3 = 0.0, vol_diff_pct vacío (False).
        3. Blanks directo a stock: status 'no_aplica', F3 = 0.0, vol_diff_pct vacío (False).
        4. Vectores previos intactos (38.1 × 100 × 4.05 × 250 / 1.000.000 = 3.858 m3).
        """
        # 1. Línea con mapeo: 6/4 (38.1 mm) × 100 mm × 4.05 m × 250 piezas = 3.858 m3
        lot_calculado = self.Lot.create({
            'name': 'LOT-5D-CALCULADO',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 250,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'vol_purchase_m3': 4.556,
            'vol_shipment_m3': 3.800,
        })
        lot_calculado.flush_recordset()
        self.assertEqual(lot_calculado.physical_status, 'calculado')
        self.assertAlmostEqual(lot_calculado.vol_physical_real_m3, 3.858, places=3)
        self.assertTrue(lot_calculado.vol_diff_pct is not False)
        self.assertAlmostEqual(lot_calculado.vol_physical_diff_pct, -15.32, places=2)

        # 2. Línea sin mapeo: escuadría inexistente
        lot_sin_mapeo = self.Lot.create({
            'name': 'LOT-5D-SIN-MAPEO',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 250,
            'thickness_visual': '99/99',
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'vol_purchase_m3': 4.556,
            'vol_shipment_m3': 3.800,
        })
        lot_sin_mapeo.flush_recordset()
        self.assertEqual(lot_sin_mapeo.physical_status, 'sin_mapeo')
        self.assertEqual(lot_sin_mapeo.vol_physical_real_m3, 0.0)
        # % Dif.Vol (compra frente a embarque) disponible aunque real físico no esté calculado
        self.assertAlmostEqual(lot_sin_mapeo.vol_diff_pct, -16.59, places=2)
        # % contra el real físico debe quedar vacío (False) cuando no hay mapeo
        self.assertFalse(lot_sin_mapeo.vol_physical_diff_pct, "% real físico debe quedar vacío (False) cuando no hay mapeo")

        # 3. Blanks directo a stock (largo_ft_frac presente)
        lot_blanks = self.Lot.create({
            'name': 'LOT-5D-BLANKS',
            'product_id': self.product.id,
            'supplier_id': self.partner.id,
            'location_id': self.location.id,
            'piezas': 250,
            'thickness_visual': '6/4',
            'ancho_nominal_mm': 100.0,
            'largo_ft_frac': '16',
            'vol_purchase_m3': 4.778,
            'vol_shipment_m3': 4.778,
        })
        lot_blanks.flush_recordset()
        self.assertEqual(lot_blanks.physical_status, 'no_aplica')
        self.assertEqual(lot_blanks.vol_physical_real_m3, 0.0)
        self.assertEqual(lot_blanks.vol_diff_pct, 0.0)
        self.assertFalse(lot_blanks.vol_physical_diff_pct, "% real físico debe quedar vacío (False) para Blanks directo a stock")

        # Verificación equivalente en madenat.guia.processing.line
        guia = self.env['madenat.guia.processing'].create({
            'name': 'GUIA-5D-TEST',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'ingestion_profile': 'f1550',
        })
        line_calc = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'LINE-5D-CALC',
            'product_id': self.product.id,
            'thickness_visual': '6/4',
            'espesor_nominal_mm': 45.0,
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'pieces': 250,
        })
        line_calc.flush_recordset()
        self.assertEqual(line_calc.physical_status, 'calculado')
        self.assertAlmostEqual(line_calc.vol_physical_real_m3, 3.858, places=3)
        self.assertTrue(line_calc.vol_diff_pct is not False)
        self.assertTrue(line_calc.vol_physical_diff_pct is not False)

        line_no_map = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'LINE-5D-NOMAP',
            'product_id': self.product.id,
            'thickness_visual': '88/88',
            'espesor_nominal_mm': 45.0,
            'ancho_nominal_mm': 100.0,
            'largo_m': 4.05,
            'pieces': 250,
        })
        line_no_map.flush_recordset()
        self.assertEqual(line_no_map.physical_status, 'sin_mapeo')
        self.assertEqual(line_no_map.vol_physical_real_m3, 0.0)
        self.assertTrue(line_no_map.vol_diff_pct is not False)
        self.assertFalse(line_no_map.vol_physical_diff_pct)

        guia_blanks = self.env['madenat.guia.processing'].create({
            'name': 'GUIA-5D-BLANKS',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'ingestion_profile': 'f5085',
        })
        line_blanks = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia_blanks.id,
            'lot_name': 'LINE-5D-BLANKS',
            'product_id': self.product.id,
            'thickness_visual': '6/4',
            'espesor_nominal_mm': 45.0,
            'ancho_nominal_mm': 100.0,
            'length_ft': 16.0,
            'pieces': 250,
        })
        line_blanks.flush_recordset()
        self.assertEqual(line_blanks.physical_status, 'no_aplica')
        self.assertEqual(line_blanks.vol_physical_real_m3, 0.0)
        self.assertTrue(line_blanks.vol_diff_pct is not False)
        self.assertFalse(line_blanks.vol_physical_diff_pct)

