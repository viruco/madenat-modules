# -*- coding: utf-8 -*-
"""Sub-bloque 2 (2026-10-04) — Borrador Seguro de Embarque (AD-93).

Cubre el retorno administrativo confirmed → draft:
* permitido sólo sin evidencia física/terminal/financiera/histórica;
* bloqueado con rebaja física, picking done, contenedor rebajado/shipped,
  stock en Clientes, SV rebaja aplicada, rebaja histórica reversada,
  estado no-confirmed (draft/in_transit/delivered/cancelled), viaje terminal,
  costos distribuidos, cost line y factura/consolidación facturada;
* permisos (Jefatura/Gerencia; no Operaciones/Auditoría/común);
* cierre de la puerta lateral write({'state':'draft'}) incluso con contexto.

Bloque autónomo: gates por evidencia real y por estado del Embarque/Viaje, sin
acoplamiento a campos de sub-bloques posteriores. Datos 100% aislados
(TransactionCase).
"""
import hashlib

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestShipmentReturnToDraft(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.customers = cls.env.ref('stock.stock_location_customers')
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SB2 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.partner = cls.env['res.partner'].create({
            'name': 'SB2 Partner', 'is_company': True})
        cls.Vessel = cls.env['shipping.vessel']
        cls.Voyage = cls.env['shipping.voyage']
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Container = cls.env['lumber.container']
        cls.Line = cls.env['lumber.shipment.line']
        cls.StockLot = cls.env['stock.lot']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Consolidation = cls.env['lumber.billing.consolidation']

        def _mk_user(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('sb2_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('sb2_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('sb2_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk_user('sb2_plain', ['base.group_user'])
        cls.user_audit = _mk_user('sb2_audit', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_auditoria'])

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_vessel(self, name):
        return self.Vessel.create({'name': name})

    def _make_voyage(self, vessel, ref, state='draft'):
        return self.Voyage.create({
            'vessel_id': vessel.id, 'voyage_reference': ref,
            'port_of_loading': 'Coronel, CL', 'port_of_discharge': 'Shanghai',
            'etd': '2026-10-15', 'state': state})

    def _make_shipment(self, name, state='confirmed', vessel=None, voyage=None):
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'vessel_id': vessel.id if vessel else False,
            'voyage_id': voyage.id if voyage else False,
            'state': state, 'booking_reference': 'BOOK-%s' % name})

    def _make_container(self, name, shipment, state='loading'):
        return self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': state})

    def _make_lot(self, label):
        return self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 1.0, 'vol_shipment_m3': 1.0})

    def _make_line(self, container, rebaja_state='pending', picking=None):
        lot = self._make_lot('SB2-LOT-%s' % container.name)
        return self.Line.create({
            'container_id': container.id,
            'shipment_id': container.shipment_id.id,
            'lot_id': lot.id, 'rebaja_state': rebaja_state,
            'rebaja_picking_id': picking.id if picking else False})

    def _make_guia(self, name):
        return self.env['madenat.guia.processing'].create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24'})

    def _make_sv_rebaja(self, container, tag):
        """Fixture: operación SV de rebaja aplicada (sin movimiento físico)."""
        guia = self._make_guia('SB2-GUIA-%s' % tag)
        lot = self.StockLot.create({
            'name': 'SB2-SVLOT-%s' % tag, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'volume_purchase_m3': 1.0, 'vol_shipment_m3': 1.0})
        return self.env['madenat.sv.operation'].create({
            'lot_id': lot.id, 'action_type': 'rebaja', 'state': 'applied',
            'reason': 'Fixture T-D10 (sin movimiento físico).',
            'destination_container_id': container.id,
            'destination_shipment_id': container.shipment_id.id,
            'rebaja_volume_m3': 1.0})

    def _done_picking(self, origin):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.customers.id, 'origin': origin})
        picking.write({'state': 'done'})
        return picking

    def _counts(self):
        return {
            'move': self.env['stock.move'].search_count([]),
            'move_line': self.env['stock.move.line'].search_count([]),
            'picking': self.env['stock.picking'].search_count([]),
            'quant': self.env['stock.quant'].search_count([]),
            'lot': self.env['stock.lot'].search_count([]),
            'account_move': self.env['account.move'].search_count([]),
            'audit': self.AuditLog.search_count([]),
        }

    def _return_audit(self, shipment):
        return self.AuditLog.search([
            ('action_type', '=', 'shipment_return_to_draft'),
            ('batch_id', '=', str(shipment.id))])

    def _assert_blocked(self, shipment, user=None, expected_state='confirmed'):
        user = user or self.user_jef
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(user).action_draft()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, expected_state)
        self.assertFalse(self._return_audit(shipment))
        self.assertEqual(self._counts(), before)

    # ── T-D1: confirmed sin contenedores → permitido ─────────────────────
    def test_01_confirmed_without_containers_allowed(self):
        shipment = self._make_shipment('SB2-EMB-01')
        before = self._counts()
        result = shipment.with_user(self.user_jef).action_draft()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'draft')
        self.assertFalse(shipment.actual_departure)
        self.assertEqual(result['tag'], 'reload')
        logs = self._return_audit(shipment)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs.audit_hash,
            hashlib.sha256(logs.audit_snapshot.encode('utf-8')).hexdigest())
        self.assertTrue(shipment.message_ids)
        after = self._counts()
        for key in ('move', 'move_line', 'picking', 'quant', 'lot',
                    'account_move'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['audit'], before['audit'] + 1)

    # ── T-D2: confirmed con contenedor sin rebaja → permitido ────────────
    def test_02_confirmed_container_without_rebaja_allowed(self):
        shipment = self._make_shipment('SB2-EMB-02')
        container = self._make_container(
            'SB2-CONT-02', shipment, state='loading')
        line = self._make_line(container)
        lot = line.lot_id
        before = self._counts()
        shipment.with_user(self.user_ger).action_draft()
        shipment.invalidate_recordset(); container.invalidate_recordset()
        line.invalidate_recordset(); lot.invalidate_recordset()
        self.assertEqual(shipment.state, 'draft')
        self.assertEqual(container.state, 'loading')
        self.assertEqual(line.rebaja_state, 'pending')
        self.assertFalse(line.rebaja_picking_id)
        self.assertFalse(container.state_before_rebaja)
        self.assertEqual(line.container_id, container)
        after = self._counts()
        for key in ('move', 'move_line', 'picking', 'quant', 'lot',
                    'account_move'):
            self.assertEqual(after[key], before[key])

    # ── T-D3: línea rebajada → bloqueado ─────────────────────────────────
    def test_03_rebajada_line_blocks(self):
        shipment = self._make_shipment('SB2-EMB-03')
        container = self._make_container(
            'SB2-CONT-03', shipment, state='loaded')
        self._make_line(container, rebaja_state='rebajado')
        self._assert_blocked(shipment)

    # ── T-D4: picking de rebaja done → bloqueado ─────────────────────────
    def test_04_done_rebaja_picking_blocks(self):
        shipment = self._make_shipment('SB2-EMB-04')
        container = self._make_container(
            'SB2-CONT-04', shipment, state='loaded')
        picking = self._done_picking('SB2-REB-04')
        self._make_line(container, picking=picking)
        self._assert_blocked(shipment)

    # ── T-D5: contenedor rebajado → bloqueado ────────────────────────────
    def test_05_rebajado_container_blocks(self):
        shipment = self._make_shipment('SB2-EMB-05')
        container = self._make_container(
            'SB2-CONT-05', shipment, state='loaded')
        self._make_line(container)
        container.write({'state': 'rebajado'})
        self._assert_blocked(shipment)

    # ── T-D6: contenedor shipped → bloqueado ─────────────────────────────
    def test_06_shipped_container_blocks(self):
        shipment = self._make_shipment('SB2-EMB-06')
        container = self._make_container(
            'SB2-CONT-06', shipment, state='sealed')
        self._make_line(container)
        container.write({'state': 'shipped'})
        self._assert_blocked(shipment)

    # ── T-D7: embarque in_transit → bloqueado ────────────────────────────
    def test_07_in_transit_blocks(self):
        shipment = self._make_shipment('SB2-EMB-07', state='in_transit')
        self._assert_blocked(shipment, expected_state='in_transit')

    # ── T-D8: embarque delivered / cancelled → bloqueado ─────────────────
    def test_08_delivered_cancelled_block(self):
        for i, state in enumerate(('delivered', 'cancelled')):
            shipment = self._make_shipment('SB2-EMB-08%s' % i, state=state)
            self._assert_blocked(shipment, expected_state=state)

    # ── T-D9: costos distribuidos → bloqueado ────────────────────────────
    def test_09_distributed_costs_block(self):
        shipment = self._make_shipment('SB2-EMB-09')
        shipment.write({'cost_distribution_state': 'distributed'})
        self._assert_blocked(shipment)

    # ── T-D10: SV rebaja aplicada → bloqueado ────────────────────────────
    def test_10_sv_rebaja_applied_blocks(self):
        shipment = self._make_shipment('SB2-EMB-10')
        container = self._make_container(
            'SB2-CONT-10', shipment, state='loaded')
        op = self._make_sv_rebaja(container, '10')
        self.assertEqual(op.state, 'applied')
        self._assert_blocked(shipment)

    # ── T-D11: permisos → AccessError en servidor ────────────────────────
    def test_11_permissions_block(self):
        shipment = self._make_shipment('SB2-EMB-11')
        before = self._counts()
        for user in (self.user_oper, self.user_plain, self.user_audit):
            with self.assertRaises(AccessError):
                shipment.with_user(user).action_draft()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_plain).write({'state': 'draft'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertFalse(self._return_audit(shipment))
        self.assertEqual(self._counts(), before)

    # ── T-D12: puerta lateral write({'state':'draft'}) → bloqueada ───────
    def test_12_lateral_write_blocked(self):
        shipment = self._make_shipment('SB2-EMB-12')
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write({'state': 'draft'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).with_context(
                allow_draft=True, state='draft').write({'state': 'draft'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(self._counts(), before)

    # ── T-D13: viaje terminal → bloqueado ────────────────────────────────
    def test_13_terminal_voyage_blocks(self):
        vessel = self._make_vessel('SB2-VESSEL-13')
        voyage = self._make_voyage(vessel, 'SB2-VOY-13', state='cancel')
        shipment = self._make_shipment(
            'SB2-EMB-13', vessel=vessel, voyage=voyage)
        self._assert_blocked(shipment)

    # ── T-D14: consolidación facturada → bloqueado ───────────────────────
    def test_14_billed_consolidation_blocks(self):
        shipment = self._make_shipment('SB2-EMB-14')
        self.Consolidation.create({
            'shipment_id': shipment.id, 'state': 'billed'})
        self._assert_blocked(shipment)

    # ── T-D15: el error NO modifica nada ─────────────────────────────────
    def test_15_error_leaves_everything_intact(self):
        shipment = self._make_shipment('SB2-EMB-15')
        container = self._make_container(
            'SB2-CONT-15', shipment, state='loaded')
        line = self._make_line(container, rebaja_state='rebajado')
        picking = self._done_picking('SB2-REB-15')
        line.write({'rebaja_picking_id': picking.id})
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_draft()
        shipment.invalidate_recordset(); container.invalidate_recordset()
        line.invalidate_recordset(); picking.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(line.rebaja_state, 'rebajado')
        self.assertEqual(line.rebaja_picking_id, picking)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self._counts(), before)
        self.assertFalse(self._return_audit(shipment))

    # ── T-D16 (BSD-02): draft → UserError; sin side effects ──────────────
    def test_16_draft_state_blocked(self):
        shipment = self._make_shipment('SB2-EMB-16', state='draft')
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_draft()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'draft')
        self.assertFalse(self._return_audit(shipment))
        self.assertEqual(self._counts(), before)

    # ── T-D17 (BSD-05): viaje terminal departed/arrived → bloqueado ──────
    def test_17_terminal_voyage_departed_arrived_block(self):
        for i, vstate in enumerate(('departed', 'arrived')):
            vessel = self._make_vessel('SB2-VESSEL-17%s' % i)
            voyage = self._make_voyage(
                vessel, 'SB2-VOY-17%s' % i, state=vstate)
            shipment = self._make_shipment(
                'SB2-EMB-17%s' % i, vessel=vessel, voyage=voyage)
            self._assert_blocked(shipment)

    # ── T-D18 (BSD-06): rebaja histórica reversada → bloqueado ───────────
    def test_18_historical_reversed_rebaja_blocks(self):
        shipment = self._make_shipment('SB2-EMB-18')
        container = self._make_container('SB2-CONT-18', shipment, state='loaded')
        self._make_line(container, rebaja_state='reversed')
        self._assert_blocked(shipment)

    # ── T-D19 (BSD-06): picking de rebaja originado (no done) → bloqueado ─
    def test_19_historical_originated_picking_blocks(self):
        shipment = self._make_shipment('SB2-EMB-19')
        container = self._make_container('SB2-CONT-19', shipment, state='loaded')
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.customers.id, 'origin': 'SB2-REB-19'})
        self._make_line(container, rebaja_state='pending', picking=picking)
        self._assert_blocked(shipment)

    # ── T-D20 (BSD-11): el token no persiste tras fallo ni tras éxito ────
    def test_20_token_not_persisted(self):
        from odoo.addons.madenat_lumber_logistics.models \
            import lumber_export_shipment as mod
        shipment = self._make_shipment('SB2-EMB-20')
        container = self._make_container('SB2-CONT-20', shipment, state='loaded')
        self._make_line(container, rebaja_state='rebajado')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_draft()
        self.assertFalse(mod._RETURN_TO_DRAFT_TOKENS)
        clean = self._make_shipment('SB2-EMB-20B')
        clean.with_user(self.user_jef).action_draft()
        self.assertFalse(mod._RETURN_TO_DRAFT_TOKENS)
        with self.assertRaises(UserError):
            clean.with_user(self.user_jef).write({'state': 'draft'})

    # ── T-D21 (BSD-12): Backlog documental se conserva ───────────────────
    def test_21_backlog_document_preserved(self):
        shipment = self._make_shipment('SB2-EMB-21')
        doc = self.env['lumber.shipment.document'].create({
            'shipment_id': shipment.id, 'name': 'SB2-DOC-21'})
        before_state = doc.state
        shipment.with_user(self.user_jef).action_draft()
        doc.invalidate_recordset()
        self.assertTrue(doc.exists())
        self.assertEqual(doc.shipment_id, shipment)
        self.assertEqual(doc.state, before_state)

    # ── T-D22 (BSD-13): otro Embarque y sus Contenedores intactos ────────
    def test_22_other_shipment_untouched(self):
        other = self._make_shipment('SB2-EMB-22-OTHER')
        other_container = self._make_container(
            'SB2-CONT-22-OTHER', other, state='sealed')
        target = self._make_shipment('SB2-EMB-22')
        target.with_user(self.user_jef).action_draft()
        other.invalidate_recordset()
        other_container.invalidate_recordset()
        self.assertEqual(other.state, 'confirmed')
        self.assertEqual(other_container.state, 'sealed')
