# -*- coding: utf-8 -*-
"""Sub-bloque 4A (2026-10-04) — Regularización B-01 (R1) y cierre (R4).

Datos 100% aislados (TransactionCase, se revierten). Cubre T-R1-1..9 y
T-R4-1..12:

* R1: rebaja extemporánea REAL desde B-01 open (picking/lote/volumen/auditoría).
* R4: cierre open → resolved controlado (Gerencia, sin pendientes residuales).
"""
import hashlib
import json

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestB01Regularization(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        if 'stock_move_email_validation' in cls.company._fields:
            cls.company.stock_move_email_validation = False
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.customers = cls.env.ref('stock.stock_location_customers')
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'B01R Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.partner = cls.env['res.partner'].create({
            'name': 'B01R Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Container = cls.env['lumber.container']
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Wizard = cls.env['lumber.b01.regularization.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']

        def _mk_user(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('b01r_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('b01r_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('b01r_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk_user('b01r_plain', ['base.group_user'])
        cls.user_audit = _mk_user('b01r_audit', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_auditoria'])

    REASON = 'Excepción documental B-01: pendiente de rebaja al zarpe.'
    R1_REASON = 'Rebaja extemporánea autorizada por Gerencia tras auditoría.'
    APPROVAL = 'Aprobado por Gerencia: se regulariza con evidencia física real.'

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-10-04'})

    def _make_lot(self, guia, label, vol, disponible):
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id,
            'guia_processing_id': guia.id,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': vol, 'vol_shipment_m3': vol})
        if disponible > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_shipment(self, name, state='confirmed'):
        # Fix fixture R1/R4 (AD-94): el zarpe/B-01 exige `vessel_id`, por lo que
        # el Embarque de prueba necesita una Motonave. Se crea una Motonave de
        # prueba determinista y única (sin `sudo`, sin movimientos de stock). El
        # `voyage_id` puede quedar vacío: AD-94 no lo exige.
        vessel = self.env['shipping.vessel'].create({
            'name': 'R1R4 VESSEL %s' % name})
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'booking_reference': 'B-%s' % name, 'state': state,
            'vessel_id': vessel.id})

    def _make_container(self, name, shipment, lot, state='loaded'):
        container = self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id})
        container.with_context(madenat_sv_rebaja_per_lot=0.0).write(
            {'lot_ids': [(4, lot.id)]})
        container.write({'state': state})
        container.invalidate_recordset()
        return container

    def _open_b01(self, shipment, container=None, reason=None):
        """Zarpa con excepción B-01 (Jefatura) exigiendo >=1 pendiente."""
        shipment.with_user(self.user_jef)._set_in_transit(
            exception_reason=reason or self.REASON, is_b01=True)
        shipment.invalidate_recordset()
        return shipment

    def _regularize(self, shipment, containers, reason=None, approval=None,
                    user=None):
        wiz = self.Wizard.with_user(user or self.user_ger).create({
            'shipment_id': shipment.id,
            'selected_container_ids': [(6, 0, containers.ids)],
            'regularization_reason': reason or self.R1_REASON,
            'approval_reason': approval or self.APPROVAL})
        return wiz.action_regularize_rebaja()

    # ── Utilidades de medición ───────────────────────────────────────────
    def _quant_of(self, lot):
        lot.invalidate_recordset()
        return sum(self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id.usage', '=', 'internal')]).mapped('quantity'))

    def _customer_quant_of(self, lot):
        return sum(self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.customers.id)]).mapped('quantity'))

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

    def _assert_no_change(self, before, after):
        for key in ('move', 'move_line', 'picking', 'quant', 'lot',
                    'cost_line', 'ship_cost_line', 'account_move', 'payment',
                    'sv_operation', 'sv_imputation', 'audit'):
            self.assertEqual(after[key], before[key], key)

    def _regularization_audits(self, shipment):
        return self.AuditLog.search([
            ('action_type', '=', 'b01_regularization'),
            ('batch_id', '=', str(shipment.id))])

    def _resolution_audits(self, shipment):
        return self.AuditLog.search([
            ('action_type', '=', 'b01_resolution'),
            ('batch_id', '=', str(shipment.id))])

    # ══════════════════════════════════════════════════════════════════════
    # T-R1 — Rebaja extemporánea R1
    # ══════════════════════════════════════════════════════════════════════
    def test_r1_1_real_rebaja_lote_picking_audit(self):
        """R1 crea rebaja real: picking done, lote preservado, quant interno
        baja, Clientes sube, línea/contenedor rebajados y auditoría firmada."""
        guia = self._make_guia('B01R-1')
        lot = self._make_lot(guia, 'B01R-1-L', 3.0, 3.0)
        shipment = self._make_shipment('B01R-1')
        container = self._make_container('B01R-1-C', shipment, lot)
        self._open_b01(shipment, container)
        internal_before = self._quant_of(lot)
        cust_before = self._customer_quant_of(lot)
        self._regularize(shipment, container)
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(line.rebaja_state, 'rebajado')
        self.assertTrue(line.rebaja_picking_id)
        self.assertEqual(line.rebaja_picking_id.state, 'done')
        self.assertAlmostEqual(line.rebaja_qty_m3, 3.0, places=3)
        self.assertAlmostEqual(
            internal_before - self._quant_of(lot), 3.0, places=3)
        self.assertAlmostEqual(
            self._customer_quant_of(lot) - cust_before, 3.0, places=3)
        # La excepción NO se cierra automáticamente con R1.
        self.assertEqual(shipment.b01_exception_state, 'open')
        audits = self._regularization_audits(shipment)
        self.assertEqual(len(audits), 1)
        snap = json.loads(audits.audit_snapshot)
        self.assertEqual(snap['operation']['subtype'], 'late_rebaja')
        self.assertEqual(snap['operation']['approver']['role'], 'gerencia')
        self.assertTrue(snap['invariants']['departure_not_backdated'])
        self.assertTrue(snap['invariants']['physical_stock_moved_by_rebaja'])
        self.assertEqual(
            audits.audit_hash,
            hashlib.sha256(audits.audit_snapshot.encode('utf-8')).hexdigest())

    def test_r1_2_loading_blocked(self):
        """R1 sobre un Contenedor pendiente en 'loading' queda bloqueada."""
        guia = self._make_guia('B01R-2')
        lot = self._make_lot(guia, 'B01R-2-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-2')
        container = self._make_container('B01R-2-C', shipment, lot,
                                         state='loading')
        self._open_b01(shipment, container)
        before = self._counts()
        with self.assertRaises(UserError):
            self._regularize(shipment, container)
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(container.state, 'loading')
        self.assertEqual(container.line_ids.rebaja_state, 'pending')
        self.assertFalse(container.line_ids.rebaja_picking_id)
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertEqual(self._counts(), before)

    def test_r1_3_permissions(self):
        """Sólo Gerencia ejecuta R1; Jefatura abre pero no confirma."""
        guia = self._make_guia('B01R-3')
        lot = self._make_lot(guia, 'B01R-3-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-3')
        container = self._make_container('B01R-3-C', shipment, lot)
        self._open_b01(shipment, container)
        vals = {'shipment_id': shipment.id,
                'selected_container_ids': [(6, 0, [container.id])],
                'regularization_reason': self.R1_REASON,
                'approval_reason': self.APPROVAL}
        for user in (self.user_oper, self.user_audit, self.user_plain):
            with self.assertRaises(AccessError):
                self.Wizard.with_user(user).create(vals)
        wiz_jef = self.Wizard.with_user(self.user_jef).create(vals)
        with self.assertRaises(AccessError):
            wiz_jef.action_regularize_rebaja()
        with self.assertRaises(AccessError):
            container.with_user(self.user_jef)._assert_can_regularize_b01_rebaja(
                shipment, self.R1_REASON, self.APPROVAL)
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(shipment.b01_exception_state, 'open')

    def test_r1_4_insufficient_reason(self):
        """Motivo o aprobación < 20 caracteres → UserError sin cambios."""
        guia = self._make_guia('B01R-4')
        lot = self._make_lot(guia, 'B01R-4-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-4')
        container = self._make_container('B01R-4-C', shipment, lot)
        self._open_b01(shipment, container)
        before = self._counts()
        with self.assertRaises(UserError):
            self._regularize(shipment, container, reason='corto')
        with self.assertRaises(UserError):
            self._regularize(shipment, container, approval='corto')
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(self._counts(), before)

    def test_r1_5_out_of_scope(self):
        """R1 bloqueada fuera del Embarque / con B-01 none / resolved."""
        guia = self._make_guia('B01R-5')
        lot_a = self._make_lot(guia, 'B01R-5-A', 2.0, 2.0)
        lot_b = self._make_lot(guia, 'B01R-5-B', 2.0, 2.0)
        ship_a = self._make_shipment('B01R-5A')
        ship_b = self._make_shipment('B01R-5B')
        cont_a = self._make_container('B01R-5A-C', ship_a, lot_a)
        cont_b = self._make_container('B01R-5B-C', ship_b, lot_b)
        self._open_b01(ship_a, cont_a)
        # (a) Contenedor de OTRO Embarque.
        with self.assertRaises(UserError):
            self._regularize(ship_a, cont_b)
        # (b) B-01 none (Embarque confirmado sin excepción).
        with self.assertRaises(UserError):
            self._regularize(ship_b, cont_b)
        cont_b.invalidate_recordset()
        self.assertEqual(cont_b.state, 'loaded')
        # (c) B-01 resolved (tras R1 + cierre).
        self._regularize(ship_a, cont_a)
        ship_a.with_user(self.user_ger).action_resolve_b01_exception()
        ship_a.invalidate_recordset()
        self.assertEqual(ship_a.b01_exception_state, 'resolved')
        with self.assertRaises(UserError):
            self._regularize(ship_a, cont_a)

    def test_r1_6_no_backdating(self):
        """R1 no retrofecha actual_departure ni la fecha de los movimientos."""
        guia = self._make_guia('B01R-6')
        lot = self._make_lot(guia, 'B01R-6-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-6')
        container = self._make_container('B01R-6-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        departure = shipment.actual_departure
        self.assertTrue(departure)
        self._regularize(shipment, container)
        shipment.invalidate_recordset()
        container.invalidate_recordset()
        self.assertEqual(shipment.actual_departure, departure)
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        picking = line.rebaja_picking_id
        self.assertTrue(picking.date_done)
        self.assertGreaterEqual(picking.date_done, departure)
        for move in picking.move_ids:
            self.assertTrue(move.date)
            self.assertGreaterEqual(move.date, departure)

    # ══════════════════════════════════════════════════════════════════════
    # T-R4 — Cierre controlado open → resolved
    # ══════════════════════════════════════════════════════════════════════
    def test_r4_1_residual_pending_blocks(self):
        """B-01 open con pendiente residual → cierre bloqueado."""
        guia = self._make_guia('B01R-7')
        lot_a = self._make_lot(guia, 'B01R-7-A', 2.0, 2.0)
        lot_b = self._make_lot(guia, 'B01R-7-B', 2.0, 2.0)
        shipment = self._make_shipment('B01R-7')
        cont_a = self._make_container('B01R-7-A', shipment, lot_a)
        self._make_container('B01R-7-B', shipment, lot_b)
        self._open_b01(shipment, cont_a)
        self._regularize(shipment, cont_a)
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertFalse(self._resolution_audits(shipment))

    def test_r4_2_resolution_ok(self):
        """Tras R1 de todos los pendientes, Gerencia cierra resolved."""
        guia = self._make_guia('B01R-8')
        lot = self._make_lot(guia, 'B01R-8-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-8')
        container = self._make_container('B01R-8-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        original_audit = shipment.b01_exception_audit_id
        original_reason = shipment.b01_exception_reason
        opened_at = shipment.b01_exception_opened_at
        opened_by = shipment.b01_exception_opened_by_id
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self.assertTrue(shipment.b01_exception_resolved_at)
        self.assertEqual(shipment.b01_exception_resolved_by_id, self.user_ger)
        # Campos originales conservados (no se reescribe la B-01 original).
        self.assertEqual(shipment.b01_exception_reason, original_reason)
        self.assertEqual(shipment.b01_exception_opened_at, opened_at)
        self.assertEqual(shipment.b01_exception_opened_by_id, opened_by)
        self.assertEqual(shipment.b01_exception_audit_id, original_audit)
        audits = self._resolution_audits(shipment)
        self.assertEqual(len(audits), 1)
        self.assertEqual(shipment.b01_exception_resolution_audit_id, audits)
        self.assertEqual(
            audits.audit_hash,
            hashlib.sha256(audits.audit_snapshot.encode('utf-8')).hexdigest())
        snap = json.loads(audits.audit_snapshot)
        self.assertEqual(snap['shipment']['b01_before'], 'open')
        self.assertEqual(snap['shipment']['b01_after'], 'resolved')
        self.assertEqual(
            snap['operation']['original_b01_audit_id'], original_audit.id)
        self.assertTrue(shipment.message_ids)

    def test_r4_3_resolved_locked(self):
        """resolved bloquea write directo, reintento de cierre y nuevo zarpe."""
        guia = self._make_guia('B01R-9')
        lot = self._make_lot(guia, 'B01R-9-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-9')
        container = self._make_container('B01R-9-C', shipment, lot)
        self._open_b01(shipment, container)
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'b01_exception_state': 'resolved'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'b01_exception_state': 'open'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'b01_exception_reason':
                 'intento de reescritura B-01 no autorizado'})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).action_resolve_b01_exception()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef)._set_in_transit()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_set_in_transit()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self.assertEqual(len(self._resolution_audits(shipment)), 1)

    def test_r4_4_delivery_gates(self):
        """action_deliver: open bloquea; resolved deja de bloquear por B-01."""
        guia = self._make_guia('B01R-10')
        lot = self._make_lot(guia, 'B01R-10-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-10')
        container = self._make_container('B01R-10-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        self.assertTrue(shipment._b01_blocks_delivery())
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_deliver()
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertFalse(shipment._b01_blocks_delivery())
        # No se ejecuta la Entrega real (otros gates/alcance): basta probar
        # que B-01 ya no la bloquea.

    def test_r4_5_composition_frozen(self):
        """No se añaden/quitan/reasignan Contenedores en in_transit/B-01."""
        guia = self._make_guia('B01R-11')
        lot_a = self._make_lot(guia, 'B01R-11-A', 2.0, 2.0)
        lot_b = self._make_lot(guia, 'B01R-11-B', 2.0, 2.0)
        shipment = self._make_shipment('B01R-11')
        cont_a = self._make_container('B01R-11-A', shipment, lot_a)
        other = self._make_shipment('B01R-11X')
        cont_x = self._make_container('B01R-11-X', other, lot_b)
        self._open_b01(shipment, cont_a)
        shipment.invalidate_recordset()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'container_ids': [(4, cont_x.id)]})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'container_ids': [(3, cont_a.id)]})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'container_ids': [(6, 0, [cont_x.id])]})
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).with_context(
                bypass_b01=True, active_model='lumber.export.shipment').write(
                    {'container_ids': [(4, cont_x.id)]})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.container_ids, cont_a)
        # Reasignación de Contenedor congelada (origen/destino).
        with self.assertRaises(UserError):
            cont_a.with_user(self.user_ger).write({'shipment_id': other.id})
        with self.assertRaises(UserError):
            cont_a.with_user(self.user_ger).with_context(
                b01_regularization=True).write({'shipment_id': other.id})
        cont_a.invalidate_recordset()
        self.assertEqual(cont_a.shipment_id, shipment)

    def test_r4_6_draft_and_rollover_blocked(self):
        """Borrador y Rolleo bloqueados por B-01 open (y tras resolved)."""
        guia = self._make_guia('B01R-12')
        lot = self._make_lot(guia, 'B01R-12-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-12')
        container = self._make_container('B01R-12-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_draft()
        with self.assertRaises(UserError):
            container.with_user(self.user_oper)._assert_rollover_eligible()
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        container.invalidate_recordset()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_jef).action_draft()
        with self.assertRaises(UserError):
            container.with_user(self.user_oper)._assert_rollover_eligible()

    def test_r4_7_audits_integrity(self):
        """Auditorías R1/R4: hash, batch, original relacionado, idempotencia."""
        guia = self._make_guia('B01R-13')
        lot = self._make_lot(guia, 'B01R-13-L', 2.0, 2.0)
        shipment = self._make_shipment('B01R-13')
        container = self._make_container('B01R-13-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        original_b01 = shipment.b01_exception_audit_id
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        reg = self._regularization_audits(shipment)
        res = self._resolution_audits(shipment)
        self.assertEqual(len(reg), 1)
        self.assertEqual(len(res), 1)
        for audit in (reg | res):
            self.assertEqual(audit.batch_id, str(shipment.id))
            self.assertEqual(
                audit.audit_hash,
                hashlib.sha256(
                    audit.audit_snapshot.encode('utf-8')).hexdigest())
        reg_snap = json.loads(reg.audit_snapshot)
        self.assertEqual(
            reg_snap['shipment']['original_b01_audit_id'], original_b01.id)
        res_snap = json.loads(res.audit_snapshot)
        self.assertEqual(
            res_snap['operation']['regularization_audit_ids'], reg.ids)
        # Idempotencia: reintento de cierre bloqueado, sin nueva auditoría.
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).action_resolve_b01_exception()
        self.assertEqual(len(self._resolution_audits(shipment)), 1)

    # ══════════════════════════════════════════════════════════════════════
    # Sub-bloque 4A (2026-10-04) — Cobertura adicional
    # T-R1-07..09 / T-R4-08..12
    # ══════════════════════════════════════════════════════════════════════
    def _b01_shipment(self, name, state='confirmed', with_voyage=False):
        """Embarque Confirmado con Motonave (y Viaje opcional).

        Apoyo de T-R1-07..09 / T-R4-08..12: el guard de zarpe
        (`_assert_departure_context`) exige `vessel_id`, por lo que la B-01 no
        puede abrirse sin Motonave.
        """
        vessel = self.env['shipping.vessel'].create(
            {'name': 'B01R-V-%s' % name})
        vals = {
            'name': name, 'customer_id': self.partner.id,
            'booking_reference': 'B-%s' % name, 'state': state,
            'vessel_id': vessel.id}
        if with_voyage:
            voyage = self.env['shipping.voyage'].create({
                'vessel_id': vessel.id,
                'voyage_reference': 'B01R-VOY-%s' % name,
                'port_of_loading': 'Coronel, CL',
                'port_of_discharge': 'Shanghai',
                'etd': '2026-10-20'})
            vals['voyage_id'] = voyage.id
        return self.Shipment.create(vals)

    def _physical_counts(self):
        """Conteo físico/financiero (sin `audit`, que R4 sí incrementa)."""
        e = self.env
        return {
            'move': e['stock.move'].search_count([]),
            'move_line': e['stock.move.line'].search_count([]),
            'picking': e['stock.picking'].search_count([]),
            'quant': e['stock.quant'].search_count([]),
            'lot': e['stock.lot'].search_count([]),
            'container': e['lumber.container'].search_count([]),
            'cost_line': e['stock.lot.cost.line'].search_count([]),
            'ship_cost_line': e['lumber.shipment.cost.line'].search_count([]),
            'account_move': e['account.move'].search_count([]),
            'payment': e['account.payment'].search_count([]),
        }

    def _assert_physical_no_change(self, before, after):
        for key in before:
            self.assertEqual(after[key], before[key], key)

    # ── T-R1-07: Contenedor ya rebajado no se puede regularizar ──────────
    def test_r1_7_already_rebajado_blocked(self):
        """T-R1-07: un Contenedor con rebaja física no es elegible para R1."""
        guia = self._make_guia('B01R-14')
        lot = self._make_lot(guia, 'B01R-14-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-14')
        container = self._make_container('B01R-14-C', shipment, lot)
        self._open_b01(shipment, container)
        # Rebaja física directa (fuera de R1): el Contenedor queda rebajado.
        shipment.invalidate_recordset()
        container._rebajar_container()
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(container.state, 'rebajado')
        before = self._counts()
        with self.assertRaises(UserError):
            self._regularize(shipment, container)
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertFalse(self._regularization_audits(shipment))
        self._assert_no_change(before, self._counts())

    # ── T-R1-08: R1 repetido sobre el mismo Contenedor ───────────────────
    def test_r1_8_repeat_blocked(self):
        """T-R1-08: la segunda R1 sobre el mismo Contenedor queda bloqueada."""
        guia = self._make_guia('B01R-15')
        lot = self._make_lot(guia, 'B01R-15-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-15')
        container = self._make_container('B01R-15-C', shipment, lot)
        self._open_b01(shipment, container)
        self._regularize(shipment, container)
        shipment.invalidate_recordset()
        container.invalidate_recordset()
        self.assertEqual(len(self._regularization_audits(shipment)), 1)
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        first_picking = line.rebaja_picking_id
        self.assertTrue(first_picking)
        pickings_before = self.env['stock.picking'].search_count([])
        with self.assertRaises(UserError):
            self._regularize(shipment, container)
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        line.invalidate_recordset()
        self.assertEqual(len(self._regularization_audits(shipment)), 1)
        self.assertEqual(line.rebaja_picking_id, first_picking)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), pickings_before)
        self.assertEqual(shipment.b01_exception_state, 'open')

    # ── T-R1-09: fallo parcial → rollback total ──────────────────────────
    def test_r1_9_multi_failure_rolls_back(self):
        """T-R1-09: si un Contenedor falla, toda la acción R1 se revierte."""
        guia = self._make_guia('B01R-16')
        lot_ok = self._make_lot(guia, 'B01R-16-A', 2.0, 2.0)
        lot_bad = self._make_lot(guia, 'B01R-16-B', 2.0, 0.0)  # sin quant
        shipment = self._b01_shipment('B01R-16')
        cont_ok = self._make_container('B01R-16-A', shipment, lot_ok)
        cont_bad = self._make_container('B01R-16-B', shipment, lot_bad)
        self._open_b01(shipment, cont_ok)
        before = self._counts()
        with self.assertRaises(UserError):
            self._regularize(shipment, cont_ok | cont_bad)
        cont_ok.invalidate_recordset()
        cont_bad.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertEqual(cont_ok.state, 'loaded')
        self.assertEqual(cont_bad.state, 'loaded')
        self.assertFalse(cont_ok.line_ids.rebaja_picking_id)
        self.assertFalse(cont_bad.line_ids.rebaja_picking_id)
        self.assertFalse(self._regularization_audits(shipment))
        self.assertEqual(shipment.b01_exception_state, 'open')
        self._assert_no_change(before, self._counts())

    # ── T-R4-08: sólo Gerencia cierra la B-01 ────────────────────────────
    def test_r4_8_non_gerencia_blocked(self):
        """T-R4-08: Operaciones/Jefatura/Auditoría/Contabilidad no cierran."""
        guia = self._make_guia('B01R-17')
        lot = self._make_lot(guia, 'B01R-17-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-17')
        container = self._make_container('B01R-17-C', shipment, lot)
        self._open_b01(shipment, container)
        self._regularize(shipment, container)
        shipment.invalidate_recordset()
        user_conta = self.env['res.users'].create({
            'name': 'b01r_conta', 'login': 'b01r_conta',
            'email': 'b01r_conta@madenat.cl',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_contabilidad').id])]})
        before = self._counts()
        for user in (self.user_oper, self.user_jef, self.user_audit,
                     user_conta):
            with self.assertRaises(AccessError):
                shipment.with_user(user).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertFalse(self._resolution_audits(shipment))
        self._assert_no_change(before, self._counts())

    # ── T-R4-09: el cierre exige evidencia R1 ────────────────────────────
    def test_r4_9_requires_regularization_evidence(self):
        """T-R4-09: sin auditoría b01_regularization el cierre se bloquea."""
        guia = self._make_guia('B01R-18')
        lot = self._make_lot(guia, 'B01R-18-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-18')
        container = self._make_container('B01R-18-C', shipment, lot)
        self._open_b01(shipment, container)
        # Rebaja física directa (sin R1): cero pendientes, sin evidencia R1.
        shipment.invalidate_recordset()
        container._rebajar_container()
        container.invalidate_recordset()
        shipment.invalidate_recordset()
        self.assertFalse(self._regularization_audits(shipment))
        before = self._counts()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertFalse(self._resolution_audits(shipment))
        self._assert_no_change(before, self._counts())

    # ── T-R4-10: R4 no altera stock ni finanzas ──────────────────────────
    def test_r4_10_no_stock_financial_mutation(self):
        """T-R4-10: R4 deja stock, contenedores y finanzas en Δ0."""
        guia = self._make_guia('B01R-19')
        lot = self._make_lot(guia, 'B01R-19-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-19')
        container = self._make_container('B01R-19-C', shipment, lot)
        self._open_b01(shipment, container)
        self._regularize(shipment, container)
        shipment.invalidate_recordset()
        before = self._physical_counts()
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self._assert_physical_no_change(before, self._physical_counts())

    # ── T-R4-11: R4 no cambia Zarpe, Motonave ni Viaje ───────────────────
    def test_r4_11_zarpe_untouched(self):
        """T-R4-11: R4 conserva state, actual_departure, Motonave y Viaje."""
        guia = self._make_guia('B01R-20')
        lot = self._make_lot(guia, 'B01R-20-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-20', with_voyage=True)
        container = self._make_container('B01R-20-C', shipment, lot)
        self._open_b01(shipment, container)
        shipment.invalidate_recordset()
        departure = shipment.actual_departure
        vessel = shipment.vessel_id
        voyage = shipment.voyage_id
        self.assertTrue(departure)
        self.assertTrue(vessel)
        self.assertTrue(voyage)
        self._regularize(shipment, container)
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(shipment.actual_departure, departure)
        self.assertEqual(shipment.vessel_id, vessel)
        self.assertEqual(shipment.voyage_id, voyage)

    # ── T-R4-12: write/contexto/RPC directos bloqueados ──────────────────
    def test_r4_12_direct_write_and_context_blocked(self):
        """T-R4-12: `resolved` no se alcanza por write, contexto ni RPC."""
        guia = self._make_guia('B01R-21')
        lot = self._make_lot(guia, 'B01R-21-L', 2.0, 2.0)
        shipment = self._b01_shipment('B01R-21')
        container = self._make_container('B01R-21-C', shipment, lot)
        self._open_b01(shipment, container)
        self._regularize(shipment, container)
        shipment.invalidate_recordset()
        before = self._counts()
        # (a) write directo.
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'b01_exception_state': 'resolved'})
        # (b) contexto falso.
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).with_context(
                bypass_b01=True, b01_resolution=True,
                active_model='lumber.export.shipment').write(
                    {'b01_exception_state': 'resolved'})
        # (c) RPC simulada (sudo + contexto).
        with self.assertRaises(UserError):
            shipment.sudo().with_context(force_b01_resolve=True).write(
                {'b01_exception_state': 'resolved'})
        # (d) los intentos falsos no dejaron token vivo.
        with self.assertRaises(UserError):
            shipment.with_user(self.user_ger).write(
                {'b01_exception_state': 'resolved'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertFalse(self._resolution_audits(shipment))
        self._assert_no_change(before, self._counts())
        # El camino autorizado sigue disponible (token íntegro).
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        self.assertEqual(len(self._resolution_audits(shipment)), 1)
