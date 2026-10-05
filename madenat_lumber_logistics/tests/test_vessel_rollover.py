# -*- coding: utf-8 -*-
"""AD-92 (2026-10-05) — Rolleo CENTRADO EN EMBARQUE (RL-01..RL-23).

La unidad del rolleo es EXACTAMENTE un `lumber.export.shipment`. Datos 100%
aislados (TransactionCase). Cobertura: apertura/rol (RL-01..03), estados
bloqueados (RL-04..06), validación de destino (RL-07..09), éxito y delta cero
(RL-10/14/15), otros Embarques e histórico intactos (RL-11/12), contenedores
(RL-13), auditoría y chatter (RL-16/17), backlog documental (RL-18),
atomicidad (RL-19) y no regresión (RL-20..23).
"""
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

import hashlib
import json

BACKLOG_DOC_NAME = 'Revisión documental por Rollover de Embarque'
COUNTER_MODELS = (
    'stock.move', 'stock.move.line', 'stock.picking', 'stock.quant',
    'stock.lot', 'lumber.shipment.cost.line', 'stock.lot.cost.line',
    'account.move', 'account.payment', 'lumber.container',
    'lumber.shipment.line',
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestShipmentRollover(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SR Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.partner = cls.env['res.partner'].create({
            'name': 'SR Partner', 'is_company': True})
        cls.Vessel = cls.env['shipping.vessel']
        cls.Voyage = cls.env['shipping.voyage']
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Container = cls.env['lumber.container']
        cls.Line = cls.env['lumber.shipment.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Wizard = cls.env['lumber.vessel.rollover.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']

        def mkuser(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = mkuser('sr_oper', [
            'base.group_user', 'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = mkuser('sr_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = mkuser('sr_ger', [
            'base.group_user', 'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = mkuser('sr_plain', ['base.group_user'])
        cls.user_audit = mkuser('sr_audit', [
            'base.group_user', 'madenat_lumber_core.group_madenat_auditoria'])

    # ── Fábricas y utilidades ────────────────────────────────────────────
    def _make_vessel(self, name):
        return self.Vessel.create({'name': name})

    def _make_voyage(self, vessel, ref, state='draft'):
        return self.Voyage.create({
            'vessel_id': vessel.id, 'voyage_reference': ref,
            'port_of_loading': 'Coronel, CL', 'port_of_discharge': 'Shanghai',
            'etd': '2026-10-15', 'state': state})

    def _make_shipment(self, name, vessel, voyage=None, state='draft',
                       booking=None, etd=None):
        vals = {
            'name': name, 'customer_id': self.partner.id,
            'vessel_id': vessel.id, 'state': state,
            'booking_reference': booking or ('BOOK-%s' % name)}
        if voyage:
            vals['voyage_id'] = voyage.id
        if etd:
            vals['estimated_departure'] = etd
        return self.Shipment.create(vals)

    def _make_container(self, name, shipment, state='loaded'):
        return self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': state})

    def _make_lot(self, label):
        return self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 1.0, 'vol_shipment_m3': 1.0})

    def _make_line(self, container, rebaja_state='pending', picking=None):
        lot = self._make_lot('SR-LOT-%s' % container.name)
        return self.Line.create({
            'container_id': container.id,
            'shipment_id': container.shipment_id.id,
            'lot_id': lot.id, 'rebaja_state': rebaja_state,
            'rebaja_picking_id': picking.id if picking else False})

    def _wizard(self, shipment, destination, voyage=None, user=None,
                motive='overbooking', note='Rolleo de prueba AD-92.',
                other_motive=None):
        vals = {
            'shipment_id': shipment.id,
            'destination_vessel_id': destination.id,
            'motive': motive, 'note': note}
        if voyage:
            vals['destination_voyage_id'] = voyage.id
        if other_motive is not None:
            vals['other_motive'] = other_motive
        return self.Wizard.with_user(user or self.user_oper).create(vals)

    def _counts(self):
        counts = {}
        for name in COUNTER_MODELS:
            try:
                model = self.env[name]
            except KeyError:
                continue
            counts[name] = model.search_count([])
        return counts

    def _audit_ids_before(self):
        return set(self.AuditLog.search([]).ids)

    def _new_audits(self, before, action_type=None):
        domain = [('id', 'not in', list(before))]
        if action_type:
            domain.append(('action_type', '=', action_type))
        return self.AuditLog.search(domain)

    def _backlog_docs(self, shipment):
        return shipment.document_ids.filtered(
            lambda d: d.name == BACKLOG_DOC_NAME)

    # ── RL-01/02: apertura desde Embarque y bloqueo post-zarpe ───────────
    def test_01_open_action_draft_confirmed_and_post_zarpe(self):
        vessel = self._make_vessel('SR-ORIG-01')
        draft = self._make_shipment('SR-EMB-01A', vessel, state='draft')
        self._make_container('SR-CONT-01A', draft)
        conf = self._make_shipment('SR-EMB-01B', vessel, state='confirmed')
        self._make_container('SR-CONT-01B', conf)
        tx = self._make_shipment('SR-EMB-01C', vessel, state='in_transit')
        self._make_container('SR-CONT-01C', tx)
        for ship in (draft, conf):
            action = ship.with_user(
                self.user_oper).action_open_shipment_rollover_wizard()
            self.assertEqual(action['res_model'],
                             'lumber.vessel.rollover.wizard')
            self.assertEqual(
                action['context']['default_shipment_id'], ship.id)
        with self.assertRaises(UserError):
            tx.with_user(self.user_oper).action_open_shipment_rollover_wizard()

    # ── RL-01: origen derivado y sólo lectura ────────────────────────────
    def test_02_origin_derived_and_readonly(self):
        vessel = self._make_vessel('SR-ORIG-02')
        voyage = self._make_voyage(vessel, '052W')
        ship = self._make_shipment('SR-EMB-02', vessel, voyage=voyage)
        self._make_container('SR-CONT-02', ship)
        wiz = self._wizard(ship, self._make_vessel('SR-DEST-02'))
        self.assertEqual(wiz.shipment_id, ship)
        self.assertEqual(wiz.origin_vessel_id, vessel)
        self.assertEqual(wiz.origin_voyage_id, voyage)
        self.assertTrue(self.Wizard._fields['origin_vessel_id'].readonly)
        self.assertTrue(self.Wizard._fields['origin_voyage_id'].readonly)

    # ── RL-10/14: éxito sobre UN Embarque, sin Viaje destino ─────────────
    def test_03_success_single_shipment_without_voyage(self):
        origin = self._make_vessel('SR-ORIG-03')
        dest = self._make_vessel('SR-DEST-03')
        ship = self._make_shipment('SR-EMB-03', origin, state='confirmed',
                                   booking='BOOK-KEEP-03')
        self._make_container('SR-CONT-03', ship, state='loaded')
        before = self._counts()
        audits_before = self._audit_ids_before()
        self._wizard(ship, dest).action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, dest)
        self.assertFalse(ship.voyage_id)
        self.assertEqual(ship.state, 'confirmed')
        self.assertEqual(ship.booking_reference, 'BOOK-KEEP-03')
        self.assertEqual(self._counts(), before)
        self.assertEqual(
            len(self._new_audits(audits_before, 'vessel_rollover')), 1)

    # ── RL-10: éxito con Viaje destino válido ────────────────────────────
    def test_04_success_with_destination_voyage(self):
        origin = self._make_vessel('SR-ORIG-04')
        dest = self._make_vessel('SR-DEST-04')
        dvoy = self._make_voyage(dest, '054W')
        ship = self._make_shipment('SR-EMB-04', origin)
        self._make_container('SR-CONT-04', ship)
        self._wizard(ship, dest, voyage=dvoy).action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, dest)
        self.assertEqual(ship.voyage_id, dvoy)

    # ── RL-07: destino igual a origen ────────────────────────────────────
    def test_05_destination_same_vessel_blocked(self):
        origin = self._make_vessel('SR-ORIG-05')
        ship = self._make_shipment('SR-EMB-05', origin)
        self._make_container('SR-CONT-05', ship)
        wiz = self._wizard(ship, origin)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)

    # ── RL-08: Viaje destino de otra Motonave ────────────────────────────
    def test_06_destination_voyage_other_vessel_blocked(self):
        origin = self._make_vessel('SR-ORIG-06')
        dest = self._make_vessel('SR-DEST-06')
        other = self._make_vessel('SR-OTHER-06')
        foreign = self._make_voyage(other, '999X')
        ship = self._make_shipment('SR-EMB-06', origin)
        self._make_container('SR-CONT-06', ship)
        wiz = self._wizard(ship, dest, voyage=foreign)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)

    # ── RL-09: Viaje destino cancelado ───────────────────────────────────
    def test_07_destination_voyage_cancel_blocked(self):
        origin = self._make_vessel('SR-ORIG-07')
        dest = self._make_vessel('SR-DEST-07')
        cvoy = self._make_voyage(dest, '077W', state='cancel')
        ship = self._make_shipment('SR-EMB-07', origin)
        self._make_container('SR-CONT-07', ship)
        wiz = self._wizard(ship, dest, voyage=cvoy)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)

    # ── RL-11: otro Embarque de la misma Motonave/Viaje intacto ──────────
    def test_08_other_shipment_same_vessel_intact(self):
        origin = self._make_vessel('SR-ORIG-08')
        dest = self._make_vessel('SR-DEST-08')
        voyage = self._make_voyage(origin, '081W')
        target = self._make_shipment('SR-EMB-08', origin, voyage=voyage)
        self._make_container('SR-CONT-08', target)
        sibling = self._make_shipment('SR-EMB-08B', origin, voyage=voyage)
        self._make_container('SR-CONT-08B', sibling)
        wiz = self._wizard(target, dest)
        self.assertIn(target, wiz.shipment_ids)
        self.assertNotIn(sibling, wiz.shipment_ids)
        self.assertNotIn(sibling, wiz.blocked_shipment_ids)
        wiz.action_confirm_rollover()
        target.invalidate_recordset()
        sibling.invalidate_recordset()
        self.assertEqual(target.vessel_id, dest)
        self.assertEqual(sibling.vessel_id, origin)
        self.assertEqual(sibling.voyage_id, voyage)

    # ── RL-12: Embarque histórico (3 meses) intacto y fuera de alcance ───
    def test_09_historical_shipment_untouched(self):
        origin = self._make_vessel('SR-ORIG-09')
        dest = self._make_vessel('SR-DEST-09')
        voyage = self._make_voyage(origin, '091W')
        target = self._make_shipment('SR-EMB-09', origin, voyage=voyage)
        self._make_container('SR-CONT-09', target)
        old = self._make_shipment(
            'SR-EMB-09-OLD', origin, voyage=voyage, state='confirmed',
            etd='2026-07-01 00:00:00')
        self._make_container('SR-CONT-09-OLD', old)
        wiz = self._wizard(target, dest)
        self.assertNotIn(old, wiz.shipment_ids)
        self.assertNotIn(old, wiz.blocked_shipment_ids)
        wiz.action_confirm_rollover()
        old.invalidate_recordset()
        self.assertEqual(old.vessel_id, origin)
        self.assertEqual(old.voyage_id, voyage)

    # ── RL-04/05/06: estados bloqueados ──────────────────────────────────
    def _assert_state_blocked(self, tag, state):
        origin = self._make_vessel('SR-ORIG-%s' % tag)
        dest = self._make_vessel('SR-DEST-%s' % tag)
        ship = self._make_shipment('SR-EMB-%s' % tag, origin, state=state)
        self._make_container('SR-CONT-%s' % tag, ship)
        before = self._counts()
        audits_before = self._audit_ids_before()
        wiz = self._wizard(ship, dest)
        self.assertIn(ship, wiz.blocked_shipment_ids)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)
        self.assertEqual(self._counts(), before)
        self.assertFalse(self._new_audits(audits_before, 'vessel_rollover'))

    def test_10_in_transit_blocked(self):
        self._assert_state_blocked('10', 'in_transit')

    def test_11_delivered_blocked(self):
        self._assert_state_blocked('11', 'delivered')

    def test_12_cancelled_blocked(self):
        self._assert_state_blocked('12', 'cancelled')

    # ── RL-13: contenedor rebajado bloquea TODO ──────────────────────────
    def test_13_rebajado_container_blocks(self):
        origin = self._make_vessel('SR-ORIG-13')
        dest = self._make_vessel('SR-DEST-13')
        ship = self._make_shipment('SR-EMB-13', origin)
        self._make_container('SR-CONT-13', ship, state='rebajado')
        wiz = self._wizard(ship, dest)
        self.assertIn(ship, wiz.blocked_shipment_ids)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)

    # ── RL-13: línea rebajada / picking done bloquea TODO ────────────────
    def test_14_rebajada_line_or_done_picking_blocks(self):
        origin = self._make_vessel('SR-ORIG-14')
        dest = self._make_vessel('SR-DEST-14')
        ship_a = self._make_shipment('SR-EMB-14A', origin)
        cont_a = self._make_container('SR-CONT-14A', ship_a)
        self._make_line(cont_a, rebaja_state='rebajado')
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id})
        picking.write({'state': 'done'})
        ship_b = self._make_shipment('SR-EMB-14B', origin)
        cont_b = self._make_container('SR-CONT-14B', ship_b)
        self._make_line(cont_b, rebaja_state='pending', picking=picking)
        wiz = self._wizard(ship_a, dest)
        self.assertIn(ship_a, wiz.blocked_shipment_ids)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship_a.invalidate_recordset()
        ship_b.invalidate_recordset()
        self.assertEqual(ship_a.vessel_id, origin)
        self.assertEqual(ship_b.vessel_id, origin)

    # ── RL-03: seguridad server-side (rol y RPC) ─────────────────────────
    def test_15_role_and_unauthorized_server_side(self):
        origin = self._make_vessel('SR-ORIG-15')
        dest = self._make_vessel('SR-DEST-15')
        ship = self._make_shipment('SR-EMB-15', origin)
        self._make_container('SR-CONT-15', ship)
        audits_before = self._audit_ids_before()
        for user in (self.user_plain, self.user_audit):
            with self.assertRaises(AccessError):
                ship.with_user(user).action_open_shipment_rollover_wizard()
            with self.assertRaises(AccessError):
                self.Wizard.with_user(user).create({
                    'shipment_id': ship.id,
                    'destination_vessel_id': dest.id,
                    'motive': 'overbooking', 'note': 'Intento no autorizado.'})
        for user in (self.user_jef, self.user_ger):
            action = ship.with_user(
                user).action_open_shipment_rollover_wizard()
            self.assertEqual(action['res_model'],
                             'lumber.vessel.rollover.wizard')
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)
        self.assertFalse(self._new_audits(audits_before, 'vessel_rollover'))

    # ── RL-10/14/16/17: integridad, auditoría SHA-256 y chatter ──────────
    def test_16_integrity_only_planning_fields(self):
        origin = self._make_vessel('SR-ORIG-16')
        dest = self._make_vessel('SR-DEST-16')
        ship = self._make_shipment('SR-EMB-16', origin, state='confirmed',
                                   booking='BOOK-KEEP-16')
        cont = self._make_container('SR-CONT-16', ship, state='loaded')
        line = self._make_line(cont)
        lot = line.lot_id
        lot.write({'container_id': cont.id})
        before = self._counts()
        audits_before = self._audit_ids_before()
        self._wizard(ship, dest).action_confirm_rollover()
        ship.invalidate_recordset()
        cont.invalidate_recordset()
        lot.invalidate_recordset()
        self.assertEqual(ship.vessel_id, dest)
        self.assertFalse(ship.voyage_id)
        self.assertEqual(ship.state, 'confirmed')
        self.assertEqual(ship.booking_reference, 'BOOK-KEEP-16')
        self.assertEqual(cont.shipment_id, ship)
        self.assertEqual(cont.vessel_id, dest)
        self.assertEqual(cont.state, 'loaded')
        self.assertEqual(lot.container_id, cont)
        self.assertEqual(self._counts(), before)
        master = self._new_audits(audits_before, 'vessel_rollover')
        self.assertEqual(len(master), 1)
        payload = json.loads(master.audit_snapshot)
        self.assertEqual(payload['origin']['vessel_id'], origin.id)
        self.assertEqual(payload['destination']['vessel_id'], dest.id)
        self.assertEqual(payload['summary']['shipments_reassigned'], 1)
        self.assertEqual(
            master.audit_hash,
            hashlib.sha256(
                master.audit_snapshot.encode('utf-8')).hexdigest())
        items = self._new_audits(audits_before, 'vessel_rollover_item')
        self.assertEqual(len(items), 2)
        for log in items:
            self.assertEqual(
                log.audit_hash,
                hashlib.sha256(
                    log.audit_snapshot.encode('utf-8')).hexdigest())
        self.assertTrue(ship.message_ids)
        self.assertTrue(origin.message_ids)
        self.assertTrue(dest.message_ids)

    # ── RL-13: contenedores conservan la pertenencia ─────────────────────
    def test_17_containers_keep_ownership(self):
        origin = self._make_vessel('SR-ORIG-17')
        dest = self._make_vessel('SR-DEST-17')
        ship = self._make_shipment('SR-EMB-17', origin)
        cont = self._make_container('SR-CONT-17', ship)
        self._wizard(ship, dest).action_confirm_rollover()
        cont.invalidate_recordset()
        self.assertEqual(cont.shipment_id, ship)
        self.assertEqual(cont.vessel_id, dest)

    # ── RL-18: backlog documental no bloqueante (crear y actualizar) ─────
    def test_18_documentary_backlog_created_and_updated(self):
        origin = self._make_vessel('SR-ORIG-18')
        dest1 = self._make_vessel('SR-DEST-18A')
        dest2 = self._make_vessel('SR-DEST-18B')
        ship = self._make_shipment('SR-EMB-18', origin)
        self._make_container('SR-CONT-18', ship)
        self._wizard(ship, dest1).action_confirm_rollover()
        docs = self._backlog_docs(ship)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs.backlog_state, 'open')
        self._wizard(ship, dest2).action_confirm_rollover()
        docs = self._backlog_docs(ship)
        self.assertEqual(len(docs), 1)
        self.assertIn(dest2.name, docs.backlog_note)

    # ── RL-19: atomicidad (exclusión ⇒ cero cambios, cero auditorías) ────
    def test_19_atomicity_no_partial_state(self):
        origin = self._make_vessel('SR-ORIG-19')
        dest = self._make_vessel('SR-DEST-19')
        ship = self._make_shipment('SR-EMB-19', origin, state='confirmed')
        self._make_container('SR-CONT-19', ship, state='rebajado')
        before = self._counts()
        audits_before = self._audit_ids_before()
        wiz = self._wizard(ship, dest)
        with self.assertRaises(UserError):
            wiz.action_confirm_rollover()
        ship.invalidate_recordset()
        self.assertEqual(ship.vessel_id, origin)
        self.assertEqual(ship.state, 'confirmed')
        self.assertEqual(self._counts(), before)
        self.assertFalse(self._new_audits(audits_before))

    # ── RL-23: Rolleo de Contenedor aislado (sin regresión) ──────────────
    def test_20_container_rollover_isolated(self):
        wiz_model = self.env['lumber.container.rollover.wizard']
        self.assertEqual(wiz_model._name, 'lumber.container.rollover.wizard')
        self.assertTrue(hasattr(self.Container, 'action_open_rollover_wizard'))
        self.assertTrue(hasattr(self.Container, '_assert_rollover_eligible'))
        self.assertNotIn('container_id', self.Wizard._fields)
        self.assertIn('shipment_id', self.Wizard._fields)

    # ── RL-20/21/22: Rebaja / Zarpe / B-01 sin regresión ─────────────────
    def test_21_no_regression_rebaja_zarpe_b01(self):
        for method in ('action_open_rebaja_wizard', 'action_set_in_transit',
                       'action_resolve_b01_exception', 'action_deliver',
                       'action_confirm',
                       'action_open_shipment_rollover_wizard'):
            self.assertTrue(
                hasattr(self.Shipment, method),
                'Falta el método %s en lumber.export.shipment' % method)
        self.assertTrue(
            hasattr(self.Vessel, 'action_open_vessel_shipments'))
        self.assertFalse(
            hasattr(self.Vessel, 'action_open_vessel_rollover_wizard'))
