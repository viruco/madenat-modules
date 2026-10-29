# -*- coding: utf-8 -*-
"""Sub-bloque 6 — Costeo provisional post-Entrega (Política C2).

Suite `TestShipmentCostingC2` (T-CST-1 .. T-CST-12).

Datos 100% aislados (TransactionCase); nada se persiste. No se ejecuta el
motor legado ni ningún flujo real (Costeo/Facturación/Pagos/R3/BT-04). No se
mueve inventario físico.
"""
import hashlib

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_logistics.models.lumber_export_shipment import (
    _B01_WRITE_TOKENS, _B01_RESOLVE_TOKENS)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_costing',
        'shipment_costing_c2')
class TestShipmentCostingC2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Container = cls.env['lumber.container']
        cls.ShipLine = cls.env['lumber.shipment.line']
        cls.Lot = cls.env['stock.lot']
        cls.CostLine = cls.env['lumber.shipment.cost.line']
        cls.Ledger = cls.env['stock.lot.cost.line']
        cls.Distribution = cls.env['lumber.cost.distribution']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.product = cls.env['product.product'].create({
            'name': 'C2 Test Lumber', 'type': 'consu', 'is_storable': True})
        cls.partner = cls.env['res.partner'].create({
            'name': 'C2 Supplier Naviera', 'supplier_rank': 1})

        def _mk_user(login, groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'email': '%s@madenat.cl' % login,
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('c2_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_costos = _mk_user('c2_costos', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_costos'])
        cls.user_conta = _mk_user('c2_conta', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_contabilidad'])

    # ══════════════════════════════════════════════════════════════════════
    # Fábricas aisladas (sin mover stock)
    # ══════════════════════════════════════════════════════════════════════
    def _mk_delivered(self, name, volumes=(1.0, 1.0, 1.0), state='delivered',
                      amount=100.00, cost_state='validated'):
        """Embarque con contenedor rebajado + lotes + línea de costo fuente."""
        shipment = self.Shipment.create({'name': name, 'state': state})
        container = self.Container.create({
            'name': '%s-C1' % name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': 'rebajado'})
        for idx, vol in enumerate(volumes):
            lot = self.Lot.create({
                'name': '%s-L%s' % (name, idx),
                'product_id': self.product.id,
                'vol_shipment_m3': vol,
                'volumen_m3': vol,
            })
            self.ShipLine.create({
                'shipment_id': shipment.id,
                'container_id': container.id,
                'lot_id': lot.id,
                'rebaja_state': 'rebajado',
            })
        cost = self.CostLine.create({
            'shipment_id': shipment.id,
            'partner_id': self.partner.id,
            'supplier_category': 'naviera',
            'cost_type': 'freight',
            'amount_usd': amount,
            'description': 'Flete C2 test',
            'state': cost_state,
            'allocation_level': 'shipment',
        })
        shipment.invalidate_recordset()
        return shipment, container, cost

    def _set_b01(self, shipment, state):
        """Fija el campo B-01 con el token de proceso (vía no pública)."""
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
            'account_move': e['account.move'].search_count([]),
            'payment': e['account.payment'].search_count([]),
            'consolidation': e['lumber.billing.consolidation'].search_count([]),
        }

    def _c2_ledger(self, shipment):
        return self.Ledger.search([('shipment_id', '=', shipment.id)])

    def _audit(self, shipment):
        return self.AuditLog.search([
            ('action_type', '=', 'shipment_cost_distribution'),
            ('batch_id', '=', str(shipment.id))])

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-1 — delivered limpio + costo aprobado → distribución + ledger
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_01_distribute_ok(self):
        shipment, _container, _cost = self._mk_delivered('CST-01')
        before = self._counts()
        shipment.with_user(self.user_conta).action_prepare_distribution()
        dist = self.Distribution.search([
            ('shipment_id', '=', shipment.id), ('is_c2', '=', True)])
        self.assertEqual(len(dist), 1)
        self.assertEqual(dist.state, 'draft')
        self.assertEqual(dist.version_number, 1)
        self.assertEqual(dist.basis, 'final_logistic_volume')
        shipment.with_user(self.user_conta).action_apply_distribution()
        dist.invalidate_recordset()
        self.assertEqual(dist.state, 'applied')
        ledger = self._c2_ledger(shipment)
        self.assertEqual(len(ledger), 3, 'Un asiento por (lote, fuente)')
        self.assertAlmostEqual(
            sum(ledger.mapped('allocated_cost_usd')), 100.00, places=2)
        # No se movió inventario físico ni finanzas.
        after = self._counts()
        for key in before:
            self.assertEqual(after[key], before[key], key)

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-2 — Embarque no entregado → bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_02_not_delivered_blocked(self):
        shipment, _c, _cost = self._mk_delivered('CST-02', state='in_transit')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()
        self.assertFalse(self.Distribution.search([
            ('shipment_id', '=', shipment.id)]))

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-3 — B-01 open → bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_03_b01_open_blocked(self):
        shipment, _c, _cost = self._mk_delivered('CST-03')
        self._set_b01(shipment, 'open')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()
        self.assertFalse(self._c2_ledger(shipment))

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-4 — B-01 resolved + R1/R2 coherente → permitido
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_04_b01_resolved_allowed(self):
        shipment, _c, _cost = self._mk_delivered('CST-04')
        self._set_b01(shipment, 'resolved')
        shipment.invalidate_recordset()
        shipment.with_user(self.user_conta).action_apply_distribution()
        dist = self.Distribution.search([
            ('shipment_id', '=', shipment.id), ('state', '=', 'applied')])
        self.assertEqual(len(dist), 1)
        self.assertTrue(self._c2_ledger(shipment))

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-5 — sin línea de costo aprobada → bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_05_no_approved_cost_blocked(self):
        shipment, _c, _cost = self._mk_delivered('CST-05', cost_state='draft')
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-6 — distribución repetida → no duplica ledger/versión
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_06_idempotent_no_duplicate(self):
        shipment, _c, _cost = self._mk_delivered('CST-06')
        shipment.with_user(self.user_conta).action_apply_distribution()
        ledger_n = len(self._c2_ledger(shipment))
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_apply_distribution()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()
        dist = self.Distribution.search([
            ('shipment_id', '=', shipment.id), ('is_c2', '=', True)])
        self.assertEqual(len(dist), 1)
        self.assertEqual(len(self._c2_ledger(shipment)), ledger_n)


    # ══════════════════════════════════════════════════════════════════════
    # T-CST-7 — volumen total 0 → bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_07_zero_volume_blocked(self):
        shipment, _c, _cost = self._mk_delivered(
            'CST-07', volumes=(0.0, 0.0, 0.0))
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-8 — redondeo/residual determinista; suma exacta
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_08_rounding_exact(self):
        shipment, _c, _cost = self._mk_delivered(
            'CST-08', volumes=(1.0, 1.0, 1.0), amount=100.00)
        shipment.with_user(self.user_conta).action_apply_distribution()
        ledger = self._c2_ledger(shipment)
        self.assertAlmostEqual(
            sum(ledger.mapped('allocated_cost_usd')), 100.00, places=2)
        dist = self.Distribution.search([
            ('shipment_id', '=', shipment.id), ('state', '=', 'applied')])
        self.assertAlmostEqual(dist.total_source_cost_usd, 100.00, places=2)
        self.assertAlmostEqual(dist.total_distributed_usd, 100.00, places=2)
        self.assertAlmostEqual(dist.residual_usd, 0.0, places=2)

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-9 — usuario no autorizado / motor legado → bloqueado
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_09_unauthorized_blocked(self):
        shipment, _c, _cost = self._mk_delivered('CST-09')
        with self.assertRaises(AccessError):
            shipment.with_user(self.user_oper).action_prepare_distribution()
        with self.assertRaises(AccessError):
            shipment.with_user(self.user_oper).action_apply_distribution()
        # Costos puede preparar (draft) pero NO aplicar (Contabilidad).
        with self.assertRaises(AccessError):
            shipment.with_user(self.user_costos).action_apply_distribution()
        # El motor legado está clausurado en cualquier vía.
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_distribute_costs()

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-10 — auditoría/hash; sin stock/move/quant/lote físico
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_10_audit_and_no_stock(self):
        shipment, _c, _cost = self._mk_delivered('CST-10')
        lots = self.Lot.search([('name', 'like', 'CST-10-L')])
        qty_before = {l.id: l.vol_shipment_m3 for l in lots}
        before = self._counts()
        shipment.with_user(self.user_conta).action_apply_distribution()
        after = self._counts()
        for key in before:
            self.assertEqual(after[key], before[key], key)
        for lot in lots:
            self.assertAlmostEqual(lot.vol_shipment_m3, qty_before[lot.id],
                                   places=3)
            # El valor derivado del lote se recalcula por ORM (no SQL).
            self.assertGreaterEqual(lot.logistic_cost_usd, 0.0)
        audit = self._audit(shipment)
        self.assertEqual(len(audit), 1)
        self.assertEqual(len(audit.audit_hash or ''), 64)
        self.assertEqual(
            audit.audit_hash,
            hashlib.sha256(audit.audit_snapshot.encode('utf-8')).hexdigest())

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-11 — partnerid real se usa; no partner_id
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_11_partnerid_real_field(self):
        fields = self.env['stock.lot.cost.line']._fields
        self.assertIn('partnerid', fields)
        self.assertNotIn('partner_id', fields)
        shipment, _c, _cost = self._mk_delivered('CST-11')
        shipment.with_user(self.user_conta).action_apply_distribution()
        ledger = self._c2_ledger(shipment)
        self.assertTrue(ledger)
        for line in ledger:
            self.assertEqual(line.partnerid, self.partner)

    # ══════════════════════════════════════════════════════════════════════
    # T-CST-12 — costo tardío no cambia la versión aplicada
    # ══════════════════════════════════════════════════════════════════════
    def test_cst_12_late_cost_requires_supersede(self):
        shipment, _c, _cost = self._mk_delivered('CST-12')
        shipment.with_user(self.user_conta).action_apply_distribution()
        dist = self.Distribution.search([
            ('shipment_id', '=', shipment.id), ('state', '=', 'applied')])
        self.assertEqual(dist.version_number, 1)
        ledger_n = len(self._c2_ledger(shipment))
        # Costo tardío APROBADO (no incluido en la versión aplicada).
        self.CostLine.create({
            'shipment_id': shipment.id,
            'partner_id': self.partner.id,
            'supplier_category': 'portuario',
            'cost_type': 'port_charges',
            'amount_usd': 50.0,
            'description': 'Gasto portuario tardío',
            'state': 'validated',
            'allocation_level': 'shipment',
        })
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_prepare_distribution()
        with self.assertRaises(UserError):
            shipment.with_user(self.user_conta).action_apply_distribution()
        # La versión aplicada y su ledger NO cambiaron.
        self.assertEqual(dist.version_number, 1)
        self.assertEqual(dist.state, 'applied')
        self.assertEqual(len(self._c2_ledger(shipment)), ledger_n)

