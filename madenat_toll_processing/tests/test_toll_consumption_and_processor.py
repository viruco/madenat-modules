# -*- coding: utf-8 -*-
"""
Pruebas focalizadas para OP-09 y OP-10 en madenat_toll_processing:
- OP-10: Consumo de materia prima desde ubicación física correcta (patios específicos,
  distribución entre ubicaciones, disponibilidad libre real, compañía e idempotencia).
- OP-09: Maquilador/procesador independiente del proveedor de compra, conservando
  la selección explícita a lo largo de todo el ciclo de vida de la orden.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


@tagged('post_install', '-at_install', 'madenat', 'madenat_toll_processing', 'toll_consumption_and_processor')
class TestTollConsumptionAndProcessor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')

        # Ubicación patio específica (hija de stock)
        cls.yard_marval = cls.env['stock.location'].create({
            'name': 'PATIO MARVAL TEST',
            'usage': 'internal',
            'location_id': cls.stock_loc.id,
            'company_id': cls.company.id,
        })
        cls.yard_coronel = cls.env['stock.location'].create({
            'name': 'PATIO CORONEL TEST',
            'usage': 'internal',
            'location_id': cls.stock_loc.id,
            'company_id': cls.company.id,
        })

        # Productos
        cls.product_raw = cls.env['product.product'].create({
            'name': 'Pino Radiata Aserrado Test',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.product_service = cls.env['product.product'].create({
            'name': 'Servicio Maquila Cepillado Test',
            'type': 'service',
            'uom_id': cls.uom_m3.id,
        })

        # Partners
        cls.supplier_a = cls.env['res.partner'].create({
            'name': 'Proveedor Compra A Ltda',
            'is_company': True,
            'supplier_rank': 1,
        })
        cls.processor_b = cls.env['res.partner'].create({
            'name': 'Maquilador B SpA',
            'is_company': True,
            'is_processor': True,
            'supplier_rank': 1,
        })

    def _create_lot_with_stock(self, name, volume, location, company=None):
        company = company or self.company
        lot = self.env['stock.lot'].create({
            'name': name,
            'product_id': self.product_raw.id,
            'company_id': company.id,
            'volume_purchase_m3': volume,
        })
        # Asignar existencia física mediante API nativa
        self.env['stock.quant']._update_available_quantity(
            self.product_raw, location, volume, lot_id=lot
        )
        lot.invalidate_recordset()
        return lot

    def _create_order(self, vals=None):
        order_vals = {
            'processor_id': self.processor_b.id,
            'source_type': 'from_stock',
            'service_product_id': self.product_service.id,
            'process_cost_per_m3': 45.0,
        }
        if vals:
            order_vals.update(vals)
        return self.env['toll.processing.order'].create(order_vals)

    # =========================================================================
    # OP-10: CONSUMO DESDE UBICACIÓN FÍSICA CORRECTA
    # =========================================================================

    def test_01_lot_in_specific_yard(self):
        """El consumo debe salir del patio físico real (MARVAL) y no de WH/Stock."""
        lot = self._create_lot_with_stock('LOTE-PATIO-01', 10.0, self.yard_marval)

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot.id])],
        })

        picking = order._create_consumption_picking()
        self.assertTrue(picking, "Debe generar albarán de consumo.")
        self.assertEqual(picking.state, 'done', "El albarán debe quedar validado.")
        self.assertEqual(order.consumption_picking_id.id, picking.id)

        # Verificar que el movimiento y la línea de movimiento apuntan al patio MARVAL
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(picking.move_ids.location_id.id, self.yard_marval.id)
        self.assertEqual(picking.move_line_ids.location_id.id, self.yard_marval.id)

        # Verificar existencias en quants
        quant_marval = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.yard_marval.id),
        ])
        self.assertAlmostEqual(sum(quant_marval.mapped('quantity')), 0.0, places=3,
                               msg="El stock en Patio Marval debe haberse consumido a 0.")

        quant_wh_stock = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.stock_loc.id),
        ])
        self.assertAlmostEqual(sum(quant_wh_stock.mapped('quantity')), 0.0, places=3,
                               msg="No deben existir quants negativos ni residuales en WH/Stock.")

    def test_02_material_distributed_across_locations(self):
        """Si el material del lote está distribuido, se debe consumir de cada ubicación sin duplicar."""
        lot = self.env['stock.lot'].create({
            'name': 'LOTE-DISTRIBUIDO-02',
            'product_id': self.product_raw.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 7.0,
        })
        # 4 m³ en MARVAL, 6 m³ en CORONEL (total físico 10 m³, requerido 7 m³)
        self.env['stock.quant']._update_available_quantity(
            self.product_raw, self.yard_marval, 4.0, lot_id=lot
        )
        self.env['stock.quant']._update_available_quantity(
            self.product_raw, self.yard_coronel, 6.0, lot_id=lot
        )

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot.id])],
        })

        picking = order._create_consumption_picking()
        self.assertTrue(picking)
        self.assertEqual(picking.state, 'done')

        # Se deben haber creado 2 líneas de movimiento con las cantidades correspondientes
        lines = picking.move_line_ids
        self.assertEqual(len(lines), 2, "Debe generar dos líneas de movimiento para cubrir las dos ubicaciones.")

        marval_line = lines.filtered(lambda l: l.location_id == self.yard_marval)
        coronel_line = lines.filtered(lambda l: l.location_id == self.yard_coronel)

        self.assertAlmostEqual(marval_line.quantity, 4.0, places=3)
        self.assertAlmostEqual(coronel_line.quantity, 3.0, places=3)

        # Saldos restantes
        q_marval = self.env['stock.quant'].search([('lot_id', '=', lot.id), ('location_id', '=', self.yard_marval.id)])
        q_coronel = self.env['stock.quant'].search([('lot_id', '=', lot.id), ('location_id', '=', self.yard_coronel.id)])
        self.assertAlmostEqual(sum(q_marval.mapped('quantity')), 0.0, places=3)
        self.assertAlmostEqual(sum(q_coronel.mapped('quantity')), 3.0, places=3)

    def test_03_insufficient_availability(self):
        """Si la disponibilidad libre es menor al volumen requerido, debe rechazar con UserError."""
        lot = self._create_lot_with_stock('LOTE-INSUFICIENTE-03', 10.0, self.yard_marval)

        # Reservar 8 m³ con otro movimiento ajeno
        other_picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', self.warehouse.id)
        ], limit=1)
        other_picking = self.env['stock.picking'].create({
            'picking_type_id': other_picking_type.id,
            'location_id': self.yard_marval.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        other_move = self.env['stock.move'].create({
            'name': 'Reserva externa',
            'product_id': self.product_raw.id,
            'product_uom_qty': 8.0,
            'product_uom': self.uom_m3.id,
            'picking_id': other_picking.id,
            'location_id': self.yard_marval.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        other_picking.action_confirm()
        # Reserva forzando el lote
        self.env['stock.move.line'].create({
            'move_id': other_move.id,
            'picking_id': other_picking.id,
            'product_id': self.product_raw.id,
            'lot_id': lot.id,
            'quantity': 8.0,
            'product_uom_id': self.uom_m3.id,
            'location_id': self.yard_marval.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot.id])],
        })

        # Intento de consumo de 10 m³ cuando solo quedan 2 m³ libres
        with self.assertRaises(UserError) as ctx:
            order._create_consumption_picking()

        self.assertIn("Disponibilidad insuficiente", str(ctx.exception))
        self.assertFalse(order.consumption_picking_id, "No debió crearse albarán de consumo.")

    def test_04_incompatible_company(self):
        """Quants de otra compañía no deben ser consumidos por la orden de la compañía activa."""
        other_company = self.env['res.company'].create({'name': 'Otra Compania Test SpA'})
        other_wh = self.env['stock.warehouse'].create({
            'name': 'Almacén Otra Cía',
            'code': 'AOC',
            'company_id': other_company.id,
        })
        other_stock_loc = other_wh.lot_stock_id

        lot_other = self._create_lot_with_stock(
            'LOTE-OTRA-CIA-04', 5.0, other_stock_loc, company=other_company
        )

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot_other.id])],
        })

        with self.assertRaises(UserError) as ctx:
            order._create_consumption_picking()

        self.assertIn("No se encontraron existencias en ubicaciones internas", str(ctx.exception))

    def test_07_no_duplicate_move_creation(self):
        """Llamadas repetidas a _create_consumption_picking deben ser idempotentes y no duplicar movimientos."""
        lot = self._create_lot_with_stock('LOTE-IDEMPOTENCIA-07', 5.0, self.yard_marval)

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot.id])],
        })

        p1 = order._create_consumption_picking()
        self.assertTrue(p1)
        moves_count_1 = len(p1.move_ids)

        # Segunda llamada consecutiva
        p2 = order._create_consumption_picking()
        self.assertEqual(p1.id, p2.id, "Debe retornar el albarán existente sin crear uno nuevo.")
        self.assertEqual(len(p2.move_ids), moves_count_1, "No debe duplicar movimientos en el albarán.")

    def test_08_idempotency_cancelled_picking_allows_recreation(self):
        """Si un albarán de consumo previo fue cancelado, debe permitirse recrear el consumo activo."""
        lot = self._create_lot_with_stock('LOTE-REINTENTO-08', 5.0, self.yard_marval)

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot.id])],
        })

        p1 = order._create_consumption_picking()
        self.assertTrue(p1)
        # Cancelar el picking previo simulando anulación operativa (en Odoo 18, picking 'done' requiere return o simular cancelación)
        p1.write({'state': 'cancel'})
        p1.move_ids.write({'state': 'cancel'})
        self.assertEqual(p1.state, 'cancel')

        # Reabastecer el lote en el patio para permitir el nuevo consumo
        self.env['stock.quant']._update_available_quantity(
            self.product_raw, self.yard_marval, 5.0, lot_id=lot
        )

        p2 = order._create_consumption_picking()
        self.assertTrue(p2, "Debe generar un nuevo albarán al estar el anterior cancelado.")
        self.assertNotEqual(p1.id, p2.id, "No debe reutilizar el albarán cancelado.")
        self.assertEqual(p2.state, 'done')
        self.assertEqual(order.consumption_picking_id.id, p2.id)

    # =========================================================================
    # OP-09: PROCESADOR DISTINTO DEL PROVEEDOR Y CONSERVACIÓN
    # =========================================================================

    def test_05_processor_distinct_from_supplier(self):
        """La orden de procesamiento debe permitir seleccionar un procesador distinto del proveedor."""
        reception = self.env['lumber.reception'].create({
            'name': 'REC-GUIA-TEST-05',
            'supplier_id': self.supplier_a.id,
            'location_id': self.yard_marval.id,
        })

        # Crear orden desde la recepción
        action = reception.action_create_toll_order()
        order = self.env['toll.processing.order'].browse(action['res_id'])

        # Por defecto sugiere el proveedor
        self.assertEqual(order.processor_id.id, self.supplier_a.id)

        # Modificación explícita a un procesador tercero distinto
        order.processor_id = self.processor_b.id
        self.assertEqual(order.processor_id.id, self.processor_b.id)
        self.assertNotEqual(order.processor_id.id, reception.supplier_id.id)

    def test_06_processor_selection_conserved_through_lifecycle(self):
        """El procesador seleccionado se conserva en confirmación, picking de consumo y factura."""
        lot = self._create_lot_with_stock('LOTE-PROCESADOR-06', 8.0, self.yard_marval)

        order = self.env['toll.processing.order'].create({
            'processor_id': self.processor_b.id,
            'source_type': 'from_stock',
            'source_lot_ids': [(6, 0, [lot.id])],
            'service_product_id': self.product_service.id,
            'process_cost_per_m3': 45.0,
        })

        # 1. Avance de estados
        order.action_mark_sent()
        self.assertEqual(order.state, 'sent')
        self.assertEqual(order.processor_id.id, self.processor_b.id)

        order.action_mark_in_process()
        self.assertEqual(order.state, 'in_process')
        self.assertEqual(order.processor_id.id, self.processor_b.id)

        # 2. Picking de consumo automático
        picking = order._create_consumption_picking()
        self.assertEqual(picking.partner_id.id, self.processor_b.id,
                         "El albarán de consumo debe heredar al procesador elegido.")

        # 3. Facturación por servicio de maquila
        order.actual_return_volume_m3 = 7.5
        bill_action = order.action_create_bill()
        bill = self.env['account.move'].browse(bill_action['res_id'])
        self.assertEqual(bill.partner_id.id, self.processor_b.id,
                         "La factura de proveedor debe emitirse al procesador elegido y no al proveedor original.")

    def test_09_uom_validation_and_conversion(self):
        """Verificar que el producto debe pertenecer a la categoría de Volumen y usar redondeo nativo de la UoM."""
        uom_unit = self.env.ref('uom.product_uom_unit')
        product_unit = self.env['product.product'].create({
            'name': 'Insumo No Volumen Test',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
        })
        lot_unit = self.env['stock.lot'].create({
            'name': 'LOTE-UNIT-09',
            'product_id': product_unit.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 5.0,
        })
        self.env['stock.quant']._update_available_quantity(
            product_unit, self.yard_marval, 5.0, lot_id=lot_unit
        )

        order = self._create_order({
            'source_lot_ids': [(6, 0, [lot_unit.id])],
        })

        with self.assertRaises(UserError) as ctx:
            order._create_consumption_picking()

        self.assertIn("no pertenece a la categoría de Volumen", str(ctx.exception))
