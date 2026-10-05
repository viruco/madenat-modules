# -*- coding: utf-8 -*-
"""D2 — Entrega Segura de Embarque (AD-98, Odoo 18 CE).

Suite `TestShipmentDeliverySafe` (T-D2-01 .. T-D2-20).

La Entrega es un hito LOGÍSTICO (`in_transit → delivered`). NO mueve stock, NO
ejecuta Rebaja/R2/Costeo/Billing/Pagos, NO modifica B-01, NO implementa Backlog
ni waiver. La documentación (B2) es evidencia informativa y no bloquea.

Datos 100% aislados (TransactionCase); nada se persiste. Para bloqueos/rollback
se mide Δ0; para éxito se miden sólo las mutaciones D2 esperadas.
"""
import hashlib
import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_logistics.models.lumber_export_shipment import (
    _B01_WRITE_TOKENS, _B01_RESOLVE_TOKENS)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestShipmentDeliverySafe(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'D2 Partner', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'D2 Lumber', 'is_storable': True, 'tracking': 'lot'})
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Container = cls.env['lumber.container']
        cls.Line = cls.env['lumber.shipment.line']
        cls.StockLot = cls.env['stock.lot']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.vessel = cls.env['shipping.vessel'].create({'name': 'D2 VESSEL'})
        cls.voyage = cls.env['shipping.voyage'].create({
            'vessel_id': cls.vessel.id, 'voyage_reference': 'D2-VOY',
            'etd': fields.Date.today(),
            'port_of_discharge': 'San Antonio, CL'})

        def _mk_user(login, groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'email': '%s@madenat.cl' % login,
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('d2_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('d2_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('d2_ger', [
            'base.group_user', 'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_aud = _mk_user('d2_aud', [
            'base.group_user', 'madenat_lumber_core.group_madenat_auditoria'])
        cls.user_conta = _mk_user('d2_conta', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_contabilidad'])
        cls.user_plain = _mk_user('d2_plain', ['base.group_user'])

    # ══════════════════════════════════════════════════════════════════════
    # Fábricas aisladas (sin mover stock)
    # ══════════════════════════════════════════════════════════════════════
    def _mk_shipment(self, name, state='in_transit'):
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'booking_reference': 'B-%s' % name, 'vessel_id': self.vessel.id,
            'voyage_id': self.voyage.id, 'state': state})

    def _mk_container(self, name, shipment, state='rebajado',
                      line_state='rebajado'):
        container = self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': state})
        lot = self.StockLot.create({
            'name': 'D2LOT-%s' % name, 'product_id': self.product.id})
        self.Line.create({
            'container_id': container.id, 'shipment_id': shipment.id,
            'lot_id': lot.id, 'rebaja_state': line_state})
        container.invalidate_recordset()
        return container

    def _mk_compensated_container(self, name, shipment, qty=1.0):
        """Contenedor con retorno físico total válido (R2 'compensated')."""
        container = self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': 'loaded'})
        lot = self.StockLot.create({
            'name': 'D2COMP-%s' % name, 'product_id': self.product.id})
        stock_loc = self.env.ref('stock.stock_location_stock')
        cust_loc = self.env.ref('stock.stock_location_customers')
        ptype = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')], limit=1)
        out = self.env['stock.picking'].create({
            'picking_type_id': ptype.id, 'location_id': stock_loc.id,
            'location_dest_id': cust_loc.id})
        out.write({'state': 'done'})
        out_move = self.env['stock.move'].create({
            'name': name, 'picking_id': out.id, 'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': qty, 'quantity': qty,
            'location_id': stock_loc.id, 'location_dest_id': cust_loc.id})
        out_move.write({'state': 'done'})
        ret_move = self.env['stock.move'].create({
            'name': '%s-RET' % name, 'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': qty, 'quantity': qty,
            'location_id': cust_loc.id, 'location_dest_id': stock_loc.id,
            'origin_returned_move_id': out_move.id})
        ret_move.write({'state': 'done'})
        self.Line.create({
            'container_id': container.id, 'shipment_id': shipment.id,
            'lot_id': lot.id, 'rebaja_state': 'reversed',
            'rebaja_picking_id': out.id})
        container.invalidate_recordset()
        return container

    def _healthy_shipment(self, name, state='in_transit'):
        shipment = self._mk_shipment(name, state=state)
        self._mk_container('%sC' % name, shipment)
        return shipment

    def _set_b01(self, shipment, state):
        """Fija B-01 con el token de proceso (no es una vía pública)."""
        key = (self.env.cr.dbname, self.env.uid, shipment.id)
        if state == 'resolved':
            _B01_RESOLVE_TOKENS.add(key)
        else:
            _B01_WRITE_TOKENS.add(key)
        shipment.write({'b01_exception_state': state})

    def _counts(self):
        e = self.env
        return {
            'move': e['stock.move'].search_count([]),
            'move_line': e['stock.move.line'].search_count([]),
            'picking': e['stock.picking'].search_count([]),
            'quant': e['stock.quant'].search_count([]),
            'lot': e['stock.lot'].search_count([]),
            'lot_cost_line': e['stock.lot.cost.line'].search_count([]),
            'ship_cost_line': e['lumber.shipment.cost.line'].search_count([]),
            'account_move': e['account.move'].search_count([]),
            'payment': e['account.payment'].search_count([]),
            'consolidation': e['lumber.billing.consolidation'].search_count([]),
            'sv_operation': e['madenat.sv.operation'].search_count([]),
            'sv_imputation': e['madenat.sv.imputation'].search_count([]),
        }

    def _assert_no_business_change(self, before, after):
        for key in before:
            self.assertEqual(after[key], before[key], key)

    def _audits(self, shipment, action_type):
        return self.AuditLog.search([
            ('action_type', '=', action_type),
            ('batch_id', '=', str(shipment.id))])

    def _assert_hash_ok(self, log):
        self.assertTrue(log)
        self.assertEqual(len(log.audit_hash or ''), 64)
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-01 — Entrega válida (in_transit → delivered + persistencia + audit)
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_01_deliver_ok(self):
        shipment = self._healthy_shipment('D2-01')
        before = self._counts()
        result = shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')
        self.assertTrue(shipment.delivery_at)
        self.assertEqual(shipment.delivery_by_id, self.user_jef)
        log = self._audits(shipment, 'shipment_delivery')
        self.assertEqual(len(log), 1)
        self.assertEqual(shipment.delivery_audit_id, log)
        self._assert_hash_ok(log)
        self.assertEqual(result.get('tag'), 'reload')
        msgs = self.env['mail.message'].search_count([
            ('model', '=', 'lumber.export.shipment'), ('res_id', '=', shipment.id)])
        self.assertGreater(msgs, 0)
        self._assert_no_business_change(before, self._counts())

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-02 — Roles: sólo Jefatura/Gerencia; resto AccessError
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_02_roles(self):
        for user in (self.user_oper, self.user_aud, self.user_conta,
                     self.user_plain):
            ship = self._healthy_shipment('D2-02-%s' % user.login)
            with self.assertRaises(AccessError):
                ship.with_user(user).action_deliver()
            ship.invalidate_recordset()
            self.assertEqual(ship.state, 'in_transit')
        for user in (self.user_jef, self.user_ger):
            ship = self._healthy_shipment('D2-02-ok-%s' % user.login)
            ship.with_user(user).action_deliver()
            ship.invalidate_recordset()
            self.assertEqual(ship.state, 'delivered')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-03 — Sólo in_transit
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_03_not_in_transit_blocked(self):
        for state in ('draft', 'confirmed', 'delivered', 'cancelled'):
            ship = self._mk_shipment('D2-03-%s' % state, state=state)
            with self.assertRaises(UserError):
                ship.with_user(self.user_jef).action_deliver()
            ship.invalidate_recordset()
            self.assertEqual(ship.state, state)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-04 — B-01 open bloquea sin mutar
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_04_b01_open_blocked(self):
        shipment = self._healthy_shipment('D2-04')
        self._set_b01(shipment, 'open')
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertFalse(shipment.delivery_audit_id)
        self.assertEqual(
            self._audits(shipment, 'shipment_delivery'), self.AuditLog)
        self._assert_no_business_change(before, self._counts())

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-05 — B-01 resolved permite y permanece resolved
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_05_b01_resolved_allowed(self):
        shipment = self._healthy_shipment('D2-05')
        self._set_b01(shipment, 'resolved')
        shipment.with_user(self.user_ger).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self._assert_hash_ok(self._audits(shipment, 'shipment_delivery'))

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-06 — R2 inconsistent bloquea sin mutar
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_06_r2_inconsistent_blocked(self):
        shipment = self._mk_shipment('D2-06')
        self._mk_container('D2-06C', shipment, state='loaded',
                           line_state='reversed')
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(
            self._audits(shipment, 'shipment_delivery'), self.AuditLog)
        self._assert_no_business_change(before, self._counts())

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-07 — R2 compensated permite
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_07_r2_compensated_allowed(self):
        shipment = self._mk_shipment('D2-07')
        container = self._mk_compensated_container('D2-07C', shipment)
        self.assertEqual(
            shipment._container_rebaja_classification(container),
            'compensated')
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-08 — Contenedor físicamente pendiente bloquea
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_08_physical_pending_blocked(self):
        shipment = self._mk_shipment('D2-08')
        self._mk_container('D2-08C', shipment, state='loaded',
                           line_state='pending')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-09 — Documentación informativa: missing/pending/partial/attached/
    #           not_configured permiten; snapshot registra el resumen B2
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_09_docs_informative(self):
        chk = self.env['lumber.document.checklist'].create({
            'name': 'D2-DOC', 'is_required': True, 'active': True})
        for doc_state in ('missing', 'attached', 'verified'):
            name = 'D2-09-%s' % doc_state
            ship = self._mk_shipment(name)
            self._mk_container('%sC' % name, ship)
            doc = ship.document_ids.filtered(
                lambda d: d.checklist_id == chk)[:1]
            self.assertTrue(doc)
            doc.write({'state': doc_state})
            ship.invalidate_recordset()
            ship.with_user(self.user_jef).action_deliver()
            ship.invalidate_recordset()
            self.assertEqual(ship.state, 'delivered')
            log = self._audits(ship, 'shipment_delivery')
            payload = json.loads(log.audit_snapshot)
            self.assertIn('document', payload)
            self.assertIn(
                payload['document']['status'],
                ('not_configured', 'missing', 'pending', 'partial',
                 'attached', 'verified'))
        # Sin documentos => not_configured y permite igual.
        ship_nc = self._mk_shipment('D2-09-nc')
        self._mk_container('D2-09-ncC', ship_nc)
        ship_nc.document_ids.unlink()
        ship_nc.invalidate_recordset()
        self.assertEqual(ship_nc.document_status, 'not_configured')
        ship_nc.with_user(self.user_jef).action_deliver()
        ship_nc.invalidate_recordset()
        self.assertEqual(ship_nc.state, 'delivered')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-10 — Viaje en estado terminal bloquea
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_10_voyage_terminal_blocked(self):
        for st in ('cancel', 'departed', 'arrived'):
            voyage = self.env['shipping.voyage'].create({
                'vessel_id': self.vessel.id,
                'voyage_reference': 'D2-10-%s' % st,
                'etd': fields.Date.today(),
                'port_of_discharge': 'San Antonio, CL'})
            ship = self.Shipment.create({
                'name': 'D2-10-%s' % st, 'customer_id': self.partner.id,
                'booking_reference': 'B-10-%s' % st,
                'vessel_id': self.vessel.id, 'voyage_id': voyage.id,
                'state': 'in_transit'})
            self._mk_container('D2-10C-%s' % st, ship)
            voyage.write({'state': st})
            ship.invalidate_recordset()
            with self.assertRaises(UserError):
                ship.with_user(self.user_jef).action_deliver()
            ship.invalidate_recordset()
            self.assertEqual(ship.state, 'in_transit')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-11 — No modifica actual_departure, Motonave, Viaje ni fecha Zarpe
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_11_no_change_departure_vessel_voyage(self):
        shipment = self._healthy_shipment('D2-11')
        shipment.write({'actual_departure': fields.Datetime.now()})
        ad, vs, vy = (shipment.actual_departure, shipment.vessel_id,
                      shipment.voyage_id)
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')
        self.assertEqual(shipment.actual_departure, ad)
        self.assertEqual(shipment.vessel_id, vs)
        self.assertEqual(shipment.voyage_id, vy)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-12 — No mueve stock (lotes, quants, pickings, moves, move lines)
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_12_no_stock_movement(self):
        shipment = self._healthy_shipment('D2-12')
        before = self._counts()
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')
        after = self._counts()
        for key in ('lot', 'quant', 'picking', 'move', 'move_line'):
            self.assertEqual(after[key], before[key], key)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-13 — No crea Costeo/consolidación/facturas/pagos ni SV
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_13_no_costing_billing_payments(self):
        shipment = self._healthy_shipment('D2-13')
        before = self._counts()
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        after = self._counts()
        for key in ('lot_cost_line', 'ship_cost_line', 'account_move',
                    'payment', 'consolidation', 'sv_operation',
                    'sv_imputation'):
            self.assertEqual(after[key], before[key], key)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-14 — Segundo intento bloqueado; sin auditoría/chatter duplicado
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_14_retry_blocked(self):
        shipment = self._healthy_shipment('D2-14')
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        aud_before = len(self._audits(shipment, 'shipment_delivery'))
        msg = [('model', '=', 'lumber.export.shipment'),
               ('res_id', '=', shipment.id)]
        msg_before = self.env['mail.message'].search_count(msg)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        self.assertEqual(shipment.state, 'delivered')
        self.assertEqual(
            len(self._audits(shipment, 'shipment_delivery')), aud_before)
        self.assertEqual(
            self.env['mail.message'].search_count(msg), msg_before)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-15 — write directo state='delivered' bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_15_direct_write_delivered_blocked(self):
        shipment = self._healthy_shipment('D2-15')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).write({'state': 'delivered'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-16 — write directo de delivery_at/by/audit bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_16_direct_write_delivery_fields_blocked(self):
        shipment = self._healthy_shipment('D2-16')
        cases = (
            {'delivery_at': fields.Datetime.now()},
            {'delivery_by_id': self.user_jef.id},
            {'delivery_audit_id': 1},
        )
        for vals in cases:
            with self.assertRaises(UserError):
                shipment.with_user(self.user_jef).write(vals)
        shipment.invalidate_recordset()
        self.assertFalse(shipment.delivery_at)
        self.assertFalse(shipment.delivery_by_id)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-17 — create directo con delivered / campos D2 bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_17_create_blocked(self):
        cases = (
            {'state': 'delivered'},
            {'state': 'in_transit'},
            {'delivery_at': fields.Datetime.now()},
            {'delivery_by_id': self.user_jef.id},
        )
        for i, extra in enumerate(cases):
            vals = {
                'name': 'D2-17-%s' % i, 'customer_id': self.partner.id,
                'booking_reference': 'B-17-%s' % i, 'vessel_id': self.vessel.id}
            vals.update(extra)
            with self.assertRaises(UserError):
                self.Shipment.with_user(self.user_plain).create(vals)

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-18 — context falso / RPC no eluden el token
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_18_context_no_bypass(self):
        shipment = self._healthy_shipment('D2-18')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).with_context(
                allow_delivery=True, delivery_internal=True).write(
                    {'state': 'delivered'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        # La acción legítima funciona aunque el contexto sea hostil.
        ok = self._healthy_shipment('D2-18b')
        ok.with_user(self.user_jef).with_context(
            allow_delivery=False).action_deliver()
        ok.invalidate_recordset()
        self.assertEqual(ok.state, 'delivered')

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-19 — Fallo inducido en auditoría => rollback total
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_19_rollback_on_failure(self):
        shipment = self._healthy_shipment('D2-19')
        before = self._counts()
        with patch.object(type(shipment), '_audit_delivery',
                          side_effect=UserError('fallo inducido')):
            with self.assertRaises(UserError):
                shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertFalse(shipment.delivery_at)
        self.assertFalse(shipment.delivery_by_id)
        self.assertFalse(shipment.delivery_audit_id)
        self.assertEqual(
            self._audits(shipment, 'shipment_delivery'), self.AuditLog)
        self._assert_no_business_change(before, self._counts())

    # ══════════════════════════════════════════════════════════════════════
    # T-D2-20 — Estado B2 canonical en la auditoría (sin complete/incomplete)
    # ══════════════════════════════════════════════════════════════════════
    def test_d2_20_audit_canonical_b2(self):
        canonical = {'not_configured', 'missing', 'pending', 'partial',
                     'attached', 'verified'}
        shipment = self._healthy_shipment('D2-20')
        shipment.with_user(self.user_jef).action_deliver()
        log = self._audits(shipment, 'shipment_delivery')
        self._assert_hash_ok(log)
        snap = log.audit_snapshot
        self.assertNotIn('complete', snap)
        self.assertNotIn('incomplete', snap)
        payload = json.loads(snap)
        self.assertIn(payload['document']['status'], canonical)
        self.assertEqual(payload['shipment']['state_after'], 'delivered')
