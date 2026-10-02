# -*- coding: utf-8 -*-
"""Reset de recepción no bloqueante y trazable (reversión por movimientos).

Cubre T-RESET-REC-01..10. TransactionCase: todo se revierte. No se usa
`stock.quant` de forma directa: la reversión se hace con un return picking
nativo atribuido por `stock.picking.reception_id`.
"""
import inspect

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core')
class TestReceptionResetTraceable(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reception = cls.env['lumber.reception']
        cls.Lot = cls.env['stock.lot']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.Wizard = cls.env['lumber.reception.reset.wizard']
        cls.Audit = cls.env['madenat.audit.log']
        cls.company = cls.env.company
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.picking_type_in = cls.env.ref('stock.picking_type_in')
        cls.supplier_loc = cls.picking_type_in.default_location_src_id
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Reset Test', 'is_company': True,
            'supplier_rank': 1})
        cls.product = cls.env['product.product'].create({
            'name': 'Reset Test Lumber', 'is_storable': True,
            'tracking': 'lot', 'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Helpers ───────────────────────────────────────────────────────────
    def _make_reception(self, name, with_picking=True, shared_lot=None):
        reception = self.Reception.create({
            'name': name, 'supplier_id': self.partner.id,
            'location_id': self.internal.id, 'ingestion_profile': 'metric',
            'state': 'done' if with_picking else 'verified',
        })
        lot = shared_lot or self.Lot.create({
            'name': 'LOT-%s' % name, 'product_id': self.product.id,
            'reception_id': reception.id})
        picking = False
        if with_picking:
            picking = self.Picking.create({
                'picking_type_id': self.picking_type_in.id,
                'partner_id': self.partner.id,
                'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal.id,
                'origin': reception.name, 'reception_id': reception.id,
            })
            move = self.Move.create({
                'name': 'M-%s' % name, 'product_id': self.product.id,
                'product_uom_qty': 5.0, 'product_uom': self.uom.id,
                'picking_id': picking.id, 'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal.id,
            })
            picking.action_confirm()
            picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
            self.MoveLine.create({
                'move_id': move.id, 'picking_id': picking.id,
                'product_id': self.product.id, 'lot_id': lot.id,
                'quantity': 5.0, 'product_uom_id': self.uom.id,
                'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal.id, 'picked': True,
            })
            move.picked = True
            move._action_done()
            picking.write({'state': 'done'})
        return reception, lot, picking

    def _confirm(self, reception, reason=None):
        wiz = self.Wizard.with_context(
            default_reception_id=reception.id).create(
            {'reception_id': reception.id, 'reason': reason})
        return wiz, wiz.action_confirm()


    # ── T-RESET-REC-01 ────────────────────────────────────────────────────
    def test_t_reset_rec_01_done_picking_opens_wizard_and_returns(self):
        rec, lot, picking = self._make_reception('RESET-R1')
        action = rec.action_reset_to_draft()
        self.assertEqual(action['res_model'], 'lumber.reception.reset.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(rec.state, 'done')  # el método público no resetea

        wiz, _ = self._confirm(rec, reason='Corrección de prueba')
        self.assertTrue(wiz.has_physical_effect)
        self.assertEqual(rec.state, 'draft')
        ret = self.Picking.search([('return_id', '=', picking.id)])
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret.state, 'done')
        self.assertTrue(picking.exists(), 'El picking origen se preserva')
        self.assertTrue(lot.exists())
        src = inspect.getsource(type(rec).action_reset_to_draft)
        self.assertNotIn('stock.quant', src)
        src2 = inspect.getsource(type(rec)._reset_to_draft_confirmed)
        self.assertNotIn("stock.quant", src2)

    # ── T-RESET-REC-02 ────────────────────────────────────────────────────
    def test_t_reset_rec_02_return_preserves_data_excludes_other_reception(self):
        rec_a, lot_a, pick_a = self._make_reception('RESET-R2A')
        rec_b, _, pick_b = self._make_reception('RESET-R2B', shared_lot=lot_a)
        moves_b_before = len(pick_b.move_ids)

        self._confirm(rec_a, reason='Reversión A')
        ret = self.Picking.search([('return_id', '=', pick_a.id)])
        rmove = ret.move_ids
        self.assertEqual(rmove.product_id, self.product)
        self.assertEqual(rmove.move_line_ids.lot_id, lot_a)
        self.assertEqual(rmove.company_id, pick_a.company_id)
        self.assertEqual(rmove.location_id, pick_a.location_dest_id)
        self.assertEqual(rmove.location_dest_id, pick_a.location_id)
        self.assertAlmostEqual(rmove.product_uom_qty, 5.0, places=3)
        self.assertEqual(pick_b.state, 'done')
        self.assertEqual(len(pick_b.move_ids), moves_b_before)
        self.assertFalse(self.Picking.search([('return_id', '=', pick_b.id)]))

    # ── T-RESET-REC-03 ────────────────────────────────────────────────────
    def test_t_reset_rec_03_retry_does_not_duplicate_return(self):
        rec, lot, picking = self._make_reception('RESET-R3')
        self._confirm(rec, reason='Primera')
        self.assertEqual(len(self.Picking.search([('return_id', '=', picking.id)])), 1)
        rec.write({'state': 'done'})
        self._confirm(rec, reason='Segunda')
        self.assertEqual(
            len(self.Picking.search([('return_id', '=', picking.id)])), 1)

    # ── T-RESET-REC-04 ────────────────────────────────────────────────────
    def test_t_reset_rec_04_no_picking_documental_reset_preserves_stock(self):
        rec, lot, _ = self._make_reception('RESET-R4', with_picking=False)
        qbefore = self.env['stock.quant'].search_count([('lot_id', '=', lot.id)])
        wiz, _ = self._confirm(rec)  # sin motivo: no hay efecto físico
        self.assertFalse(wiz.has_physical_effect)
        self.assertEqual(rec.state, 'draft')
        self.assertTrue(lot.exists())
        self.assertEqual(
            self.env['stock.quant'].search_count([('lot_id', '=', lot.id)]),
            qbefore)
        self.assertTrue(self.Audit.search([
            ('reception_id', '=', rec.id), ('action_type', '=', 'deviation')]))

    # ── T-RESET-REC-05 ────────────────────────────────────────────────────
    def test_t_reset_rec_05_not_done_picking_cancels_and_frees_reservation(self):
        rec = self.Reception.create({
            'name': 'RESET-R5', 'supplier_id': self.partner.id,
            'location_id': self.internal.id, 'ingestion_profile': 'metric',
            'state': 'verified'})
        lot = self.Lot.create({
            'name': 'LOT-RESET-R5', 'product_id': self.product.id,
            'reception_id': rec.id})
        self.env['stock.quant']._update_available_quantity(
            self.product, self.internal, 5.0, lot_id=lot)
        picking = self.Picking.create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'partner_id': self.partner.id, 'location_id': self.internal.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'origin': rec.name, 'reception_id': rec.id})
        self.Move.create({
            'name': 'M-R5', 'product_id': self.product.id,
            'product_uom_qty': 5.0, 'product_uom': self.uom.id,
            'picking_id': picking.id, 'location_id': self.internal.id,
            'location_dest_id': picking.location_dest_id.id})
        picking.action_confirm()
        picking.action_assign()
        wiz = self.Wizard.create(
            {'reception_id': rec.id, 'reason': 'Liberar reserva'})
        self.assertTrue(wiz.has_physical_effect)
        wiz.action_confirm()
        self.assertEqual(picking.state, 'cancel')
        self.assertTrue(lot.exists())
        self.assertGreaterEqual(self.env['stock.quant'].search_count(
            [('lot_id', '=', lot.id)]), 1)

    # ── T-RESET-REC-06 ────────────────────────────────────────────────────
    def test_t_reset_rec_06_physical_effect_requires_reason(self):
        rec, lot, picking = self._make_reception('RESET-R6')
        wiz = self.Wizard.create({'reception_id': rec.id, 'reason': False})
        self.assertTrue(wiz.has_physical_effect)
        with self.assertRaises(UserError):
            wiz.action_confirm()
        # Nada se alteró (el wizard queda abierto para capturar el motivo).
        self.assertEqual(rec.state, 'done')
        self.assertTrue(picking.exists())
        self.assertFalse(self.Picking.search([('return_id', '=', picking.id)]))

    # ── T-RESET-REC-07 ────────────────────────────────────────────────────
    def test_t_reset_rec_07_warnings_do_not_block(self):
        rec, lot, picking = self._make_reception('RESET-R7')
        wiz = self.Wizard.create({'reception_id': rec.id, 'reason': 'con aviso'})
        self.assertTrue(wiz.warning_text, 'Debe advertir por picking DONE')
        # La advertencia no bloquea: confirma con motivo.
        wiz.action_confirm()
        self.assertEqual(rec.state, 'draft')

    # ── T-RESET-REC-08 ────────────────────────────────────────────────────
    def test_t_reset_rec_08_rpc_direct_cannot_evade(self):
        rec, lot, picking = self._make_reception('RESET-R8')
        # La acción pública solo devuelve el wizard; no resetea.
        action = rec.action_reset_to_draft()
        self.assertEqual(action['res_model'], 'lumber.reception.reset.wizard')
        self.assertEqual(rec.state, 'done')
        self.assertFalse(self.Picking.search([('return_id', '=', picking.id)]))
        # El ejecutor es privado (prefijo '_') ⇒ no invocable por RPC.
        self.assertTrue(hasattr(type(rec), '_reset_to_draft_confirmed'))
        self.assertTrue('_reset_to_draft_confirmed'.startswith('_'))

    # ── T-RESET-REC-09 ────────────────────────────────────────────────────
    def test_t_reset_rec_09_history_preserved_after_reset(self):
        rec, lot, picking = self._make_reception('RESET-R9')
        move = picking.move_ids[:1]
        line = move.move_line_ids[:1]
        self._confirm(rec, reason='Preservar historial')
        for record in (lot, picking, move, line):
            self.assertTrue(record.exists(),
                            'El historial físico no debe borrarse')

    # ── T-RESET-REC-10 ────────────────────────────────────────────────────
    def test_t_reset_rec_10_audit_and_chatter(self):
        rec, lot, picking = self._make_reception('RESET-R10')
        self._confirm(rec, reason='Motivo auditado')
        log = self.Audit.search([
            ('reception_id', '=', rec.id), ('action_type', '=', 'deviation')],
            order='id desc', limit=1)
        self.assertTrue(log)
        self.assertIn('Motivo auditado', log.audit_snapshot or '')
        self.assertTrue(log.audit_hash)
        self.assertEqual(len(log.audit_hash), 64)
        self.assertIn('returns_created', log.audit_snapshot or '')
        chatter = '\n'.join(rec.message_ids.mapped('body') or [])
        self.assertIn('Reapertura trazable', chatter)

