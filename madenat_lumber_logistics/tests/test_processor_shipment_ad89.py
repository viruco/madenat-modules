# -*- coding: utf-8 -*-
"""AD-89 / AD-90 — Envío a procesador: parcial, reservas y backorder.

Pruebas que DEFINEN la regla (CANON/19 §16; AD-89 D-I1-03/D-I1-04; AD-90):

* T1  Envío manual parcial sin propuesta: válido **sin motivo**; un solo
  picking/movimiento y un solo ``processor_shipment``; **sin** ``deviation``.
* T2  Máximo libre: solicitar exactamente el libre valida.
* T3  Reserva ajena: solicitado > libre ⇒ **rechazo** con físico/reservado/
  libre/solicitado; la reserva ajena queda **intacta**.
* T4  Disponible libre: solicitado == libre valida **sin** alterar la reserva
  ajena.
* T5  Desviación real: **no aplica** en I1 (el asistente no persiste ninguna
  referencia previa y no se inventa una propuesta artificial).
* T6  Idempotencia: reintentar no duplica picking/movimientos/auditoría.
* T7  Backorder: comportamiento **nativo** de Odoo reproducido y explicado.
* T8  Permisos: Operaciones/Jefatura/Gerencia; sin grupo ⇒ rechazo.

Datos 100% aislados (TransactionCase).
"""
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestProcessorShipmentAD89(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'AD89 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'AD89 Supplier', 'is_company': True})
        cls.processor = cls.env['res.partner'].create({
            'name': 'AD89 Planta', 'is_company': True, 'is_processor': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Wizard = cls.env['madenat.processor.shipment.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']

        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [
                    cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('ad89_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_plain = _mk('ad89_plain', ['base.group_user'])

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name):
        return self.Guia.create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-10-02'})

    def _new_product(self, name):
        return self.env['product.product'].create({
            'name': name, 'is_storable': True, 'tracking': 'lot',
            'uom_id': self.uom_m3.id, 'uom_po_id': self.uom_m3.id})

    def _make_sv_lot(self, guia, label, volume, disponible, product=None):
        product = product or self.product
        lot = self.StockLot.create({
            'name': label, 'product_id': product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'volume_purchase_m3': volume, 'vol_shipment_m3': volume})
        if disponible:
            self.env['stock.quant']._update_available_quantity(
                product, self.stock_loc, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _qty_in(self, lot, location):
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id), ('location_id', '=', location.id),
            ('company_id', '=', self.company.id)])
        return sum(quants.mapped('quantity'))

    def _reserved_in(self, lot, location):
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id), ('location_id', '=', location.id),
            ('company_id', '=', self.company.id)])
        return sum(quants.mapped('reserved_quantity'))

    def _availability(self, lot, location=None):
        return self.Wizard._availability(lot, location or self.stock_loc)

    def _make_wizard(self, lot, quantity, source=None, reason=None):
        return self.Wizard.create({
            'processor_id': self.processor.id,
            'source_location_id': (source or self.stock_loc).id,
            'reason': reason,
            'line_ids': [(0, 0, {
                'lot_id': lot.id,
                'source_location_id': (source or self.stock_loc).id,
                'quantity': quantity,
            })],
        })

    def _send(self, lot, quantity, source=None, reason=None):
        processor_loc = self.processor._get_or_create_processor_location()
        wizard = self._make_wizard(lot, quantity, source=source, reason=reason)
        res = wizard.action_send()
        return processor_loc, res, wizard

    def _internal_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.company.id)], limit=1)

    def _reserve_other(self, lot, qty, product=None):
        """Reserva nativa de un lote por OTRO picking (reserva ajena)."""
        product = product or self.product
        ptype = self._internal_type()
        dest = self.env['stock.location'].create({
            'name': 'AD89-OTHER', 'usage': 'internal',
            'location_id': self.stock_loc.id, 'company_id': self.company.id})
        picking = self.env['stock.picking'].create({
            'picking_type_id': ptype.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': dest.id,
            'company_id': self.company.id})
        self.env['stock.move'].create({
            'name': lot.name, 'product_id': product.id,
            'product_uom_qty': qty, 'product_uom': self.uom_m3.id,
            'picking_id': picking.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': dest.id,
            'company_id': self.company.id,
        })
        picking.action_confirm()
        picking.action_assign()
        self.assertTrue(picking.move_line_ids.filtered('lot_id'))
        return picking

    def _shipment_events(self, picking):
        return self.AuditLog.search([
            ('action_type', '=', 'processor_shipment'),
            ('batch_id', '=', picking.name)])

    # ── T1 ───────────────────────────────────────────────────────────────
    def test_t1_envio_manual_parcial_sin_motivo(self):
        """Parcial manual sin propuesta ⇒ válido sin motivo; sin deviation."""
        guia = self._make_guia('AD89-T1')
        lot = self._make_sv_lot(guia, 'AD89-SV-T1', 10.0, 10.0)
        processor_loc, res, _wiz = self._send(lot, 3.0)  # sin motivo
        picking = self.env['stock.picking'].browse(res['res_id'])
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(len(picking.move_line_ids), 1)
        self.assertAlmostEqual(
            sum(picking.move_line_ids.mapped('quantity')), 3.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 7.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 3.0, 3)
        events = self._shipment_events(picking)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events.audit_hash), 64)
        self.assertFalse(self.AuditLog.search([
            ('action_type', '=', 'deviation'),
            ('batch_id', '=', picking.name)]))

    # ── T2 ───────────────────────────────────────────────────────────────
    def test_t2_maximo_libre_valida(self):
        """Solicitar exactamente el libre valida."""
        guia = self._make_guia('AD89-T2')
        lot = self._make_sv_lot(guia, 'AD89-SV-T2', 10.0, 10.0)
        self.assertAlmostEqual(self._availability(lot)['free'], 10.0, 3)
        processor_loc, res, _wiz = self._send(lot, 10.0)
        picking = self.env['stock.picking'].browse(res['res_id'])
        self.assertEqual(picking.state, 'done')
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 0.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 10.0, 3)

    # ── T3 ───────────────────────────────────────────────────────────────
    def test_t3_reserva_ajena_rechaza_y_permanece_intacta(self):
        """Solicitado > libre ⇒ rechazo con físico/reservado/libre/solicitado."""
        guia = self._make_guia('AD89-T3')
        lot = self._make_sv_lot(guia, 'AD89-SV-T3', 10.0, 10.0)
        other = self._reserve_other(lot, 4.0)
        avail = self._availability(lot)
        self.assertAlmostEqual(avail['physical'], 10.0, 3)
        self.assertAlmostEqual(avail['reserved'], 4.0, 3)
        self.assertAlmostEqual(avail['free'], 6.0, 3)
        with self.assertRaises(ValidationError) as ctx:
            self._send(lot, 7.0)
        msg = str(ctx.exception)
        for token in ('Físico', 'Reservado', 'Libre', 'Solicitado',
                      '10.000', '4.000', '6.000', '7.000'):
            self.assertIn(token, msg)
        # Reserva ajena intacta y origen sin cambios.
        self.assertAlmostEqual(self._reserved_in(lot, self.stock_loc), 4.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 10.0, 3)
        self.assertTrue(other.move_line_ids)

    # ── T4 ───────────────────────────────────────────────────────────────
    def test_t4_libre_valida_sin_alterar_reserva_ajena(self):
        """Solicitado == libre valida y NO modifica la reserva ajena."""
        guia = self._make_guia('AD89-T4')
        lot = self._make_sv_lot(guia, 'AD89-SV-T4', 10.0, 10.0)
        other = self._reserve_other(lot, 4.0)
        processor_loc, res, _wiz = self._send(lot, 6.0)
        picking = self.env['stock.picking'].browse(res['res_id'])
        self.assertEqual(picking.state, 'done')
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 4.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 6.0, 3)
        # La reserva ajena (4) sigue reservada.
        self.assertAlmostEqual(self._reserved_in(lot, self.stock_loc), 4.0, 3)
        self.assertTrue(other.move_line_ids)

    # ── T5 ───────────────────────────────────────────────────────────────
    def test_t5_desviacion_real_no_aplica_en_i1(self):
        """I1 no persiste referencia previa ⇒ T5 no aplica (sin motivo)."""
        guia = self._make_guia('AD89-T5')
        lot = self._make_sv_lot(guia, 'AD89-SV-T5', 10.0, 10.0)
        wizard = self._make_wizard(lot, 4.0)
        line = wizard.line_ids
        # No hay propuesta/planificación/reserva/cantidad previa persistida.
        self.assertIsNone(wizard._get_deviation_reference(line))
        res = wizard.action_send()  # sin motivo
        picking = self.env['stock.picking'].browse(res['res_id'])
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self._shipment_events(picking)), 1)
        self.assertFalse(self.AuditLog.search([
            ('action_type', '=', 'deviation'),
            ('batch_id', '=', picking.name)]))

    # ── T6 ───────────────────────────────────────────────────────────────
    def test_t6_idempotencia(self):
        """Reintentar la acción/validación no duplica nada."""
        guia = self._make_guia('AD89-T6')
        lot = self._make_sv_lot(guia, 'AD89-SV-T6', 10.0, 10.0)
        _loc, res, wizard = self._send(lot, 4.0)
        picking = self.env['stock.picking'].browse(res['res_id'])
        # Reintento de la acción principal: devuelve el mismo picking.
        res2 = wizard.action_send()
        self.assertEqual(res2['res_id'], picking.id)
        self.assertEqual(wizard.picking_id, picking)
        pickings = self.env['stock.picking'].search([
            ('move_line_ids.lot_id', '=', lot.id)])
        self.assertEqual(len(pickings), 1)
        self.assertEqual(pickings, picking)
        self.assertEqual(len(pickings.move_ids), 1)
        self.assertEqual(len(pickings.move_line_ids), 1)
        self.assertEqual(len(self._shipment_events(picking)), 1)
        # Reintento de la validación nativa: sin efecto (ya está done).
        picking.button_validate()
        self.assertEqual(len(self._shipment_events(picking)), 1)

    # ── T7 ───────────────────────────────────────────────────────────────
    def test_t7_backorder_nativo(self):
        """Comportamiento nativo de backorders reproducido y explicado."""
        # (a) El asistente NO forma backorder: quantity == demand y picked.
        guia = self._make_guia('AD89-T7')
        lot = self._make_sv_lot(guia, 'AD89-SV-T7', 10.0, 10.0)
        _loc, res, _wiz = self._send(lot, 3.0)
        picking = self.env['stock.picking'].browse(res['res_id'])
        self.assertEqual(picking.state, 'done')
        self.assertFalse(picking.backorder_ids)
        self.assertIn('"backorders": []',
                      self._shipment_events(picking).audit_snapshot)

        # (b) Picking interno NATIVO con entrega parcial: Odoo crea backorder.
        #     Producto/lote DEDICADOS para aislar la reserva nativa (FIFO).
        prod_b = self._new_product('AD89 Native B')
        guia2 = self._make_guia('AD89-T7B')
        lot2 = self._make_sv_lot(guia2, 'AD89-SV-T7B', 10.0, 10.0,
                                 product=prod_b)
        ptype = self._internal_type()
        ptype.create_backorder = 'always'
        dest = self.env['stock.location'].create({
            'name': 'AD89-T7-DEST', 'usage': 'internal',
            'location_id': self.stock_loc.id, 'company_id': self.company.id})
        native = self.env['stock.picking'].create({
            'picking_type_id': ptype.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': dest.id,
            'company_id': self.company.id})
        self.env['stock.move'].create({
            'name': lot2.name, 'product_id': prod_b.id,
            'product_uom_qty': 10.0, 'product_uom': self.uom_m3.id,
            'picking_id': native.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': dest.id,
            'company_id': self.company.id})
        native.action_confirm()
        native.action_assign()
        self.assertAlmostEqual(
            sum(native.move_line_ids.mapped('quantity')), 10.0, 3)
        native.move_line_ids.write({'quantity': 4.0, 'picked': True})
        native.button_validate()
        self.assertEqual(native.state, 'done')
        self.assertTrue(native.backorder_ids)
        self.assertAlmostEqual(
            sum(native.backorder_ids.move_ids.mapped('product_uom_qty')),
            6.0, 3)
        self.assertAlmostEqual(self._qty_in(lot2, self.stock_loc), 6.0, 3)

        # (c) Disponibilidad que CAMBIA antes de validar: el asistente rechaza
        # por integridad (solicitado > libre). No mueve de más ni toca reservas.
        prod_c = self._new_product('AD89 Native C')
        guia3 = self._make_guia('AD89-T7C')
        lot3 = self._make_sv_lot(guia3, 'AD89-SV-T7C', 10.0, 10.0,
                                 product=prod_c)
        wizard = self._make_wizard(lot3, 10.0)
        self._reserve_other(lot3, 5.0, product=prod_c)  # el libre baja a 5
        with self.assertRaises(ValidationError):
            wizard.action_send()
        self.assertAlmostEqual(self._qty_in(lot3, self.stock_loc), 10.0, 3)
        self.assertAlmostEqual(self._reserved_in(lot3, self.stock_loc), 5.0, 3)

    # ── T8 ───────────────────────────────────────────────────────────────
    def test_t8_permisos(self):
        """Operaciones accede; usuario sin grupo no puede ejecutar el envío."""
        with self.assertRaises(AccessError):
            self.Wizard.with_user(self.user_plain).create({
                'processor_id': self.processor.id,
                'source_location_id': self.stock_loc.id})
        self.Wizard.with_user(self.user_oper).check_access_rights('create')
