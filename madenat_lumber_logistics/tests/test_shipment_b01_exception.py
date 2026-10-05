# -*- coding: utf-8 -*-
"""Sub-bloque 3 (2026-10-04) - Zarpe con excepcion B-01 (Politica B).

Excepcion DOCUMENTAL bloqueante: el Embarque confirmed -> in_transit aunque
existan Contenedores sin rebaja fisica; los pendientes CONSERVAN su estado real
(nunca shipped/rebajado), no se mueve inventario y se abre una B-01 trazable que
bloquea Entrega/Cierre. Datos 100% aislados (TransactionCase).
"""
import hashlib
import json

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestShipmentB01Exception(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'B01 Partner', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'B01 Lumber', 'is_storable': True, 'tracking': 'lot'})
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Container = cls.env['lumber.container']
        cls.Line = cls.env['lumber.shipment.line']
        cls.StockLot = cls.env['stock.lot']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Wizard = cls.env['lumber.shipment.zarpe.wizard']
        cls.Vessel = cls.env['shipping.vessel']
        cls.vessel = cls.Vessel.create({'name': 'B01-VESSEL'})

        def _mk_user(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('b01_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('b01_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('b01_ger', [
            'base.group_user', 'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk_user('b01_plain', ['base.group_user'])
        cls.user_audit = _mk_user('b01_audit', [
            'base.group_user', 'madenat_lumber_core.group_madenat_auditoria'])

    REASON = 'Corte de booking: zarpe autorizado sin rebaja completa.'

    def _mk_shipment(self, name, state='confirmed', vessel=True):
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'booking_reference': 'B-%s' % name, 'state': state,
            'vessel_id': self.vessel.id if vessel else False})

    def _mk_container(self, name, shipment, state='loading'):
        return self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': state})

    def _mk_line(self, container, rebaja_state='pending'):
        lot = self.StockLot.create({
            'name': 'B01LOT-%s' % container.name,
            'product_id': self.product.id, 'company_id': self.company.id,
            'volume_purchase_m3': 1.0, 'vol_shipment_m3': 1.0})
        return self.Line.create({
            'container_id': container.id,
            'shipment_id': container.shipment_id.id,
            'lot_id': lot.id, 'rebaja_state': rebaja_state})

    def _rebajado_container(self, name, shipment):
        c = self._mk_container(name, shipment, state='rebajado')
        self._mk_line(c, rebaja_state='rebajado')
        return c

    def _pending_container(self, name, shipment):
        c = self._mk_container(name, shipment, state='loaded')
        self._mk_line(c, rebaja_state='pending')
        return c

    def _counts(self):
        e = self.env
        return {
            'move': e['stock.move'].search_count([]),
            'move_line': e['stock.move.line'].search_count([]),
            'picking': e['stock.picking'].search_count([]),
            'quant': e['stock.quant'].search_count([]),
            'lot': e['stock.lot'].search_count([]),
            'cost_line': e['stock.lot.cost.line'].search_count([]),
            'ship_cost_line': e['lumber.shipment.cost.line'].search_count([]),
            'account_move': e['account.move'].search_count([]),
            'payment': e['account.payment'].search_count([]),
            'sv_operation': e['madenat.sv.operation'].search_count([]),
            'sv_imputation': e['madenat.sv.imputation'].search_count([]),
            'audit': self.AuditLog.search_count([]),
        }

    def _b01_audits(self, shipment):
        return self.AuditLog.search([
            ('action_type', '=', 'b01_departure_exception'),
            ('batch_id', '=', str(shipment.id))])

    def _assert_no_non_audit_change(self, before, after):
        for key in ('move', 'move_line', 'picking', 'quant', 'lot',
                    'cost_line', 'ship_cost_line', 'account_move', 'payment',
                    'sv_operation', 'sv_imputation'):
            self.assertEqual(after[key], before[key], key)

    # -- T-B01-1: zarpe normal con todos rebajados ------------------------
    def test_01_normal_zarpe_all_rebajados(self):
        shipment = self._mk_shipment('B01-01')
        c = self._rebajado_container('B01-01C', shipment)
        before = self._counts()
        result = shipment.with_user(self.user_jef)._set_in_transit()
        shipment.invalidate_recordset(); c.invalidate_recordset()
        self.assertTrue(result)
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(c.state, 'shipped')
        self.assertEqual(shipment.b01_exception_state, 'none')
        after = self._counts()
        self._assert_no_non_audit_change(before, after)
        self.assertEqual(after['audit'], before['audit'])
        self.assertFalse(self._b01_audits(shipment))

    # -- T-B01-2: zarpe normal con pendiente -> bloqueado -----------------
    def test_02_normal_zarpe_with_pending_blocks(self):
        shipment = self._mk_shipment('B01-02')
        c = self._pending_container('B01-02C', shipment)
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit()
        action = shipment.with_user(self.user_jef).action_set_in_transit()
        self.assertEqual(
            action.get('res_model'), 'lumber.shipment.zarpe.wizard')
        shipment.invalidate_recordset(); c.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(c.state, 'loaded')
        self.assertEqual(shipment.b01_exception_state, 'none')
        self.assertEqual(self._counts(), before)
        self.assertFalse(self._b01_audits(shipment))

    # -- T-B01-3: B-01 con pendiente -------------------------------------
    def test_03_b01_with_pending(self):
        shipment = self._mk_shipment('B01-03')
        c_reb = self._rebajado_container('B01-03R', shipment)
        c_pen = self._pending_container('B01-03P', shipment)
        before = self._counts()
        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        shipment.invalidate_recordset()
        c_reb.invalidate_recordset(); c_pen.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(c_reb.state, 'shipped')
        self.assertEqual(c_pen.state, 'loaded')
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertEqual(shipment.b01_exception_reason, self.REASON)
        self.assertTrue(shipment.b01_exception_opened_at)
        self.assertEqual(shipment.b01_exception_opened_by_id, self.user_jef)
        audits = self._b01_audits(shipment)
        self.assertEqual(len(audits), 1)
        self.assertEqual(shipment.b01_exception_audit_id, audits)
        self.assertEqual(
            audits.audit_hash,
            hashlib.sha256(
                (audits.audit_snapshot or '').encode('utf-8')).hexdigest())
        snap = json.loads(audits.audit_snapshot)
        self.assertEqual(snap['shipment']['state_before'], 'confirmed')
        self.assertEqual(snap['shipment']['state_after'], 'in_transit')
        self.assertEqual(snap['exception']['state'], 'open')
        self.assertEqual(
            [x['name'] for x in snap['containers_pendientes']], [c_pen.name])
        after = self._counts()
        self._assert_no_non_audit_change(before, after)
        self.assertEqual(after['audit'], before['audit'] + 2)
        self.assertTrue(shipment.message_ids)

    # -- T-B01-4: B-01 sin pendiente -> bloqueado ------------------------
    def test_04_b01_without_pending_blocks(self):
        shipment = self._mk_shipment('B01-04')
        c = self._rebajado_container('B01-04C', shipment)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit(
                exception_reason=self.REASON, is_b01=True)
        shipment.invalidate_recordset(); c.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(c.state, 'rebajado')
        self.assertEqual(shipment.b01_exception_state, 'none')

    # -- T-B01-5: motivo ausente/corto -> bloqueado ----------------------
    def test_05_b01_short_reason_blocks(self):
        shipment = self._mk_shipment('B01-05')
        self._pending_container('B01-05C', shipment)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit(
                exception_reason='corto', is_b01=True)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit(
                exception_reason='', is_b01=True)
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(shipment.b01_exception_state, 'none')

    # -- T-B01-6: B-01 bloquea la Entrega --------------------------------
    def test_06_b01_blocks_delivery(self):
        shipment = self._mk_shipment('B01-06')
        self._pending_container('B01-06C', shipment)
        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')

    # -- T-B01-7: B-01 abierta bloquea reintento -------------------------
    def test_07_b01_open_blocks_retry(self):
        shipment = self._mk_shipment('B01-07')
        self._pending_container('B01-07C', shipment)
        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        shipment.invalidate_recordset()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit(
                exception_reason=self.REASON, is_b01=True)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_set_in_transit()
        self.assertEqual(len(self._b01_audits(shipment)), 1)

    # -- T-B01-8: permisos -----------------------------------------------
    def test_08_permissions(self):
        shipment = self._mk_shipment('B01-08')
        self._pending_container('B01-08C', shipment)
        for user in (self.user_oper, self.user_plain, self.user_audit):
            with self.assertRaises(AccessError):
                shipment.with_user(user)._set_in_transit()
        wiz = self.Wizard.with_user(self.user_jef).create(
            {'shipment_id': shipment.id})
        wiz.reason = self.REASON
        with self.assertRaises(AccessError):
            wiz.with_user(self.user_oper).action_zarpar_con_excepcion()
        with self.assertRaises(AccessError):
            shipment.with_user(self.user_oper).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(shipment.b01_exception_state, 'none')

    # -- T-B01-9: RPC/contexto no elude --------------------------------
    def test_09_rpc_context_cannot_bypass(self):
        shipment = self._mk_shipment('B01-09')
        self._pending_container('B01-09C', shipment)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).with_context(
                allow_b01=True)._set_in_transit()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write(
                {'b01_exception_state': 'open'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).with_context(
                allow_draft=True).write({
                    'b01_exception_state': 'open',
                    'b01_exception_reason': self.REASON})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'none')

    # -- T-B01-10: el error no modifica nada -----------------------------
    def test_10_error_leaves_everything_intact(self):
        shipment = self._mk_shipment('B01-10')
        c_reb = self._rebajado_container('B01-10R', shipment)
        c_pen = self._pending_container('B01-10P', shipment)
        line = c_pen.line_ids[:1]
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit(
                exception_reason='x', is_b01=True)
        shipment.invalidate_recordset(); c_reb.invalidate_recordset()
        c_pen.invalidate_recordset(); line.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(c_reb.state, 'rebajado')
        self.assertEqual(c_pen.state, 'loaded')
        self.assertEqual(line.rebaja_state, 'pending')
        self.assertFalse(line.rebaja_picking_id)
        self.assertEqual(self._counts(), before)
        self.assertFalse(self._b01_audits(shipment))

    # -- T-B01-11: sin efectos fisicos/financieros -----------------------
    def test_11_no_physical_or_financial_side_effects(self):
        s1 = self._mk_shipment('B01-11N')
        self._rebajado_container('B01-11NC', s1)
        b1 = self._counts()
        s1.with_user(self.user_jef)._set_in_transit()
        self._assert_no_non_audit_change(b1, self._counts())
        s2 = self._mk_shipment('B01-11B')
        self._pending_container('B01-11BC', s2)
        b2 = self._counts()
        s2.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        self._assert_no_non_audit_change(b2, self._counts())

    # -- T-B01-12: campos B-01 no editables directamente ----------------
    def test_12_b01_fields_not_directly_writable(self):
        shipment = self._mk_shipment('B01-12')
        self._pending_container('B01-12C', shipment)
        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        shipment.invalidate_recordset()
        audit_id = shipment.b01_exception_audit_id.id
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write(
                {'b01_exception_state': 'resolved'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write(
                {'b01_exception_reason': 'otro motivo con mas de 20 caracteres'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write(
                {'b01_exception_audit_id': False})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertEqual(shipment.b01_exception_reason, self.REASON)
        self.assertEqual(shipment.b01_exception_audit_id.id, audit_id)

    # -- T-B01-13 (ZB-02): estado != confirmed -> bloqueado, Δ0 -----------
    def test_13_wrong_state_blocks(self):
        for i, st in enumerate(('draft', 'in_transit', 'delivered',
                                'cancelled')):
            shipment = self._mk_shipment('B01-13-%s' % i, state=st)
            self._rebajado_container('B01-13R%s' % i, shipment)
            self._pending_container('B01-13P%s' % i, shipment)
            before = self._counts()
            with self.assertRaises(UserError):
                shipment.with_user(self.user_jef)._set_in_transit()
            with self.assertRaises(UserError):
                shipment.with_user(self.user_jef)._set_in_transit(
                    exception_reason=self.REASON, is_b01=True)
            shipment.invalidate_recordset()
            self.assertEqual(shipment.state, st)
            self.assertEqual(shipment.b01_exception_state, 'none')
            self.assertEqual(self._counts(), before)

    # -- T-B01-14 (ZB-03): sin Motonave / viaje terminal -> bloqueado -----
    def test_14_no_vessel_or_terminal_voyage_blocks(self):
        no_vessel = self._mk_shipment('B01-14-NV', vessel=False)
        self._rebajado_container('B01-14-NVC', no_vessel)
        with self.assertRaises(UserError):
            no_vessel.with_user(self.user_jef)._set_in_transit()
        for i, vst in enumerate(('cancel', 'departed', 'arrived')):
            shipment = self._mk_shipment('B01-14-%s' % i)
            self._rebajado_container('B01-14C%s' % i, shipment)
            voyage = self.env['shipping.voyage'].create({
                'vessel_id': self.vessel.id,
                'voyage_reference': 'B01-VOY-14%s' % i,
                'port_of_loading': 'Coronel, CL',
                'port_of_discharge': 'Shanghai',
                'etd': '2026-10-15', 'state': vst})
            shipment.voyage_id = voyage.id
            with self.assertRaises(UserError):
                shipment.with_user(self.user_jef)._set_in_transit()
            shipment.invalidate_recordset()
            self.assertEqual(shipment.state, 'confirmed')

    # -- T-B01-15 (ZB-11): aislamiento funcional de AD-94 (no ejecuta R1/R4) -
    def test_15_isolated_from_r1_r4(self):
        shipment = self._mk_shipment('B01-15')
        c_pen = self._pending_container('B01-15P', shipment)

        def _audit_count(action_type):
            return self.AuditLog.search_count([
                ('batch_id', '=', str(shipment.id)),
                ('action_type', '=', action_type)])

        before = self._counts()
        before_dep = _audit_count('b01_departure_exception')
        before_reg = _audit_count('b01_regularization')
        before_res = _audit_count('b01_resolution')

        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)

        shipment.invalidate_recordset()
        c_pen.invalidate_recordset()
        # B-01 abierta correctamente por AD-94.
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertNotEqual(shipment.b01_exception_state, 'resolved')
        # AD-94 emite SÓLO el evento de apertura; NO ejecuta R1/R4.
        self.assertEqual(
            _audit_count('b01_departure_exception'), before_dep + 1)
        self.assertEqual(_audit_count('b01_regularization'), before_reg)
        self.assertEqual(_audit_count('b01_resolution'), before_res)
        # Δ0 físico/financiero; los pendientes conservan su estado real.
        self.assertEqual(c_pen.state, 'loaded')
        after = self._counts()
        self._assert_no_non_audit_change(before, after)

    # -- T-B01-16 (ZB-14): otro Embarque y Contenedores intactos ----------
    def test_16_other_shipment_untouched(self):
        target = self._mk_shipment('B01-16-T')
        self._pending_container('B01-16-TC', target)
        other = self._mk_shipment('B01-16-O')
        other_c = self._rebajado_container('B01-16-OC', other)
        target.with_user(self.user_jef)._set_in_transit(
            exception_reason=self.REASON, is_b01=True)
        other.invalidate_recordset()
        other_c.invalidate_recordset()
        self.assertEqual(other.state, 'confirmed')
        self.assertEqual(other.b01_exception_state, 'none')
        self.assertEqual(other_c.state, 'rebajado')

    # -- T-B01-17 (ZB-15): Backlog documental no es gate y se preserva ----
    def test_17_backlog_is_not_gate_and_preserved(self):
        shipment = self._mk_shipment('B01-17')
        self._rebajado_container('B01-17C', shipment)
        doc = self.env['lumber.shipment.document'].create({
            'shipment_id': shipment.id, 'name': 'B01-DOC-17'})
        before_state = doc.state
        shipment.with_user(self.user_jef)._set_in_transit()
        doc.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertTrue(doc.exists())
        self.assertEqual(doc.state, before_state)
