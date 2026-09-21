# -*- coding: utf-8 -*-
"""AD-68: cobertura de la ruta 'granel' en el core (madenat.guia.processing).

- tipo_recepcion='granel' es aceptado por _get_or_create_consumption_picking().
- _assign_costs_to_generated_lots() NO se ejecuta para 'granel' aunque additional_cost > 0.
- _create_granel_summary_line() puebla processing_line_ids con el volumen agregado.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestGranelRouteCore(TransactionCase):
    """Ruta granel en el core: guard de consumo + línea de resumen + costeo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.SourceLotLineModel = cls.env['madenat.guia.processing.source.lot.line']
        cls.Quant = cls.env['stock.quant']
        cls.StockLot = cls.env['stock.lot']

        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.location = cls.warehouse.lot_stock_id

        cls.partner = cls.env['res.partner'].create({'name': 'AD68 Processor'})

        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'AD68 Lumber Storable',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': uom_m3.id,
            'uom_po_id': uom_m3.id,
        })

    def _make_source_lot(self, name='AD68-SRC', qty=10.0):
        lot = self.StockLot.create({
            'name': name,
            'product_id': self.product.id,
            'volumen_m3': qty,
            'company_id': self.company.id,
        })
        self.Quant._update_available_quantity(
            self.product, self.location, qty, lot_id=lot
        )
        return lot

    def _make_granel_guia(self, name='AD68-GRANEL', source_lot=None, qty=None):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'granel',
            'rate_usd': 800.0,
        }
        guia = self.GuiaModel.create(vals)
        if source_lot and qty is not None:
            self.SourceLotLineModel.create({
                'guia_processing_id': guia.id,
                'lot_id': source_lot.id,
                'qty_to_consume': qty,
            })
        return guia

    def test_01_guard_acepta_granel(self):
        """_get_or_create_consumption_picking() acepta tipo_recepcion='granel'."""
        source_lot = self._make_source_lot(qty=10.0)
        guia = self._make_granel_guia(source_lot=source_lot, qty=3.0)
        picking = guia._get_or_create_consumption_picking()
        self.assertTrue(picking, "El consumo debe funcionar para tipo 'granel'")
        self.assertTrue(guia.consumption_picking_id)

    def test_02_assign_costs_no_ejecuta_para_granel(self):
        """_assign_costs_to_generated_lots() retorna 0 para 'granel' aunque additional_cost > 0."""
        guia = self._make_granel_guia()
        guia.additional_cost = 500.0
        guia.rate_usd = 800.0
        lot = self._make_source_lot(qty=5.0)
        lot_data = [{
            'lote': lot,
            'volumen': 5.0,
            'lote_code': 'X',
            'producto_codigo': 'P',
            'cantidad': 1,
        }]
        result = guia._assign_costs_to_generated_lots(
            lot_data, {'total_volumen': 5.0})
        self.assertEqual(result, 0)
        lines = self.env['stock.lot.cost.line'].search([('lot_id', '=', lot.id)])
        self.assertEqual(len(lines), 0)

    def test_03_create_granel_summary_line(self):
        """La línea de resumen puebla processing_line_ids con el volumen agregado."""
        guia = self._make_granel_guia()
        line = guia._create_granel_summary_line(12.345)
        self.assertTrue(line)
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertAlmostEqual(line.vol_purchase_m3, 12.345, places=3)
        self.assertAlmostEqual(line.vol_shipment_m3, 12.345, places=3)
        # Producto maestro + subproducto presentes para satisfacer los gates.
        self.assertTrue(line.product_id)
        self.assertTrue(line.subproducto_id)
        # Espesor nominal placeholder (> 0) para el gate de validación nominal.
        self.assertGreater(line.espesor_nominal_mm, 0.0)

    def test_04_guard_rechaza_compra(self):
        """El guard sigue rechazando tipo_recepcion='compra' (sin regresión)."""
        guia = self.GuiaModel.create({
            'name': 'AD68-COMPRA',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'compra',
        })
        with self.assertRaises(UserError):
            guia._get_or_create_consumption_picking()

    def test_05_do_full_processing_con_linea_sintetica(self):
        """La línea sintética permite a do_full_processing() crear lotes sin error."""
        guia = self._make_granel_guia()
        guia._create_granel_summary_line(10.0)
        guia.write({'state': 'verified'})
        # No debe lanzar error por processing_line_ids vacío (gate :972).
        guia.do_full_processing()
        self.assertTrue(guia.lot_ids, "do_full_processing debe crear al menos un lote")
        self.assertAlmostEqual(guia.vol_total_m3, 10.0, places=3)

    def _make_service_guia(self, name='AD69-SERVICE', source_lot=None, qty=None):
        """Guía service con línea de processing válida (y origen opcional)."""
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'service',
            'rate_usd': 800.0,
        }
        guia = self.GuiaModel.create(vals)
        # Línea de processing para pasar el gate de do_full_processing().
        guia._create_granel_summary_line(5.0)
        if source_lot and qty is not None:
            self.SourceLotLineModel.create({
                'guia_processing_id': guia.id,
                'lot_id': source_lot.id,
                'qty_to_consume': qty,
            })
        return guia

    def _lot_qty_at_stock(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.location.id),
        ])
        return sum(quants.mapped('quantity'))

    # ── AD-69 ──────────────────────────────────────────────────────────────
    def test_06_granel_puro_sin_origen_valida_sin_consumo(self):
        """Granel sin origen valida sin error y NO crea picking de consumo."""
        guia = self._make_granel_guia()
        guia._create_granel_summary_line(10.0)
        guia.write({'state': 'verified'})

        guia.action_validate()

        self.assertEqual(guia.state, 'validated')
        self.assertFalse(guia.consumption_picking_id,
                         "Granel puro no debe crear un picking de consumo")
        self.assertTrue(guia.lot_ids, "Debe quedar un lote de patio creado")
        self.assertAlmostEqual(guia.lot_ids[0].volumen_m3, 10.0, places=3)

    def test_07_service_sin_origen_sigue_bloqueando(self):
        """Service sin origen sigue lanzando UserError al validar (no-regresión)."""
        guia = self._make_service_guia()
        guia.write({'state': 'verified'})

        with self.assertRaises(UserError):
            guia.action_validate()

    def test_08_integracion_granel_luego_service(self):
        """Paso 1 granel crea lote de patio; paso 2 service consume ese lote."""
        # Paso 1: granel puro → done, lote de patio con volumen 10 m³.
        granel = self._make_granel_guia()
        granel._create_granel_summary_line(10.0)
        granel.write({'state': 'verified'})
        granel.action_validate()
        self.assertEqual(granel.state, 'validated')
        granel_lot = granel.lot_ids[0]
        self.assertAlmostEqual(self._lot_qty_at_stock(granel_lot), 10.0, places=3)

        # Paso 2: service declara ese lote como origen y consume 3 m³.
        service = self._make_service_guia(source_lot=granel_lot, qty=3.0)
        service.write({'state': 'verified'})
        service.action_validate()
        self.assertEqual(service.state, 'validated')
        self.assertTrue(service.consumption_picking_id,
                        "La guía service debe invocar _get_or_create_consumption_picking()")

        # El volumen descontado coincide con lo declarado en source_lot_line_ids.
        self.assertAlmostEqual(self._lot_qty_at_stock(granel_lot), 7.0, places=3)

    # ── AD-72: selección manual de detalle (línea por línea vs agregado) ──
    def test_09_detail_lines_crea_lineas_por_lote(self):
        """3 líneas con volumen y lot_number → 3 líneas con lot_name propio."""
        guia = self._make_granel_guia()
        lines = guia._create_granel_detail_lines([
            {'lot_number': 'LOTE-A', 'volume_m3': 4.0, 'pieces': 10,
             'product_name_original': 'MADERA', 'product_code': 'C1'},
            {'lot_number': 'LOTE-B', 'volume_m3': 6.0, 'pieces': 15,
             'product_name_original': 'MADERA', 'product_code': 'C2'},
            {'lot_number': 'LOTE-C', 'volume_m3': 2.5, 'pieces': 5,
             'product_name_original': 'MADERA', 'product_code': 'C3'},
        ])
        self.assertEqual(len(lines), 3)
        self.assertEqual(set(lines.mapped('lot_name')),
                         {'LOTE-A', 'LOTE-B', 'LOTE-C'})
        bruta = self.env['madenat.ingestion.config'].get_default_product('bruta')
        self.assertTrue(all(l.product_id == bruta for l in lines))
        self.assertAlmostEqual(sum(l.vol_purchase_m3 for l in lines), 12.5, places=3)

    def test_10_detail_lines_sin_lot_number_fallback(self):
        """Línea sin lot_number → lot_name cae a 'GRANEL'."""
        guia = self._make_granel_guia()
        lines = guia._create_granel_detail_lines([
            {'lot_number': '', 'volume_m3': 4.0, 'pieces': 10},
        ])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.lot_name, 'GRANEL')

    def test_11_detail_lines_volumen_invalido_excluido(self):
        """Líneas con volume_m3 0/ausente se excluyen sin excepción."""
        guia = self._make_granel_guia()
        lines = guia._create_granel_detail_lines([
            {'lot_number': 'LOTE-A', 'volume_m3': 4.0},
            {'lot_number': 'LOTE-B', 'volume_m3': 0},
            {'lot_number': 'LOTE-C'},  # sin volume_m3
        ])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.lot_name, 'LOTE-A')

    def test_12_detail_lines_todas_invalidas_error(self):
        """Sin ninguna línea con volumen válido → UserError."""
        guia = self._make_granel_guia()
        with self.assertRaises(UserError):
            guia._create_granel_detail_lines([
                {'lot_number': 'LOTE-A', 'volume_m3': 0},
                {'lot_number': 'LOTE-B'},  # sin volume
            ])

    def test_13_detail_lines_pieces_fallback(self):
        """pieces ausente → fallback a 1."""
        guia = self._make_granel_guia()
        lines = guia._create_granel_detail_lines([
            {'lot_number': 'LOTE-A', 'volume_m3': 4.0},
        ])
        self.assertEqual(lines.pieces, 1)
