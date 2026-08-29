# -*- coding: utf-8 -*-
"""Cobertura de cancelación/reapertura centralizadas (intake_reception + intake_console).

Validación directa sobre lumber.reception (helpers y actions) y delegación
desde la consola (madenat.lumber.intake.console) hacia el registro origen real.
Usa TransactionCase: nada se persiste.
"""
import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeCancelReopen(TransactionCase):
    """Guías Producto: cancelación y reapertura con guardas centralizadas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Producto = cls.env['product.product']
        cls.Reception = cls.env['lumber.reception']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Cancel Reopen Test',
            'is_company': True,
        })
        cls.product = cls.Producto.create({
            'name': 'Producto Test Cancel Reopen',
        })
        cls.internal_loc = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        cls.supplier_loc = cls.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1
        )
        cls.picking_type = cls.env['stock.picking.type'].search(
            [('code', '=', 'incoming')], limit=1
        )
        cls.assertTrue(cls.internal_loc, 'Se requiere stock.location interno')
        cls.assertTrue(cls.supplier_loc, 'Se requiere stock.location supplier')
        cls.assertTrue(cls.picking_type, 'Se requiere stock.picking.type incoming')

    @classmethod
    def _make_reception(cls, state='verified'):
        return cls.Reception.create({
            'supplier_id': cls.partner.id,
            'state': state,
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx',
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
            'ingestion_profile': 'metric',
        })

    # ── Cancelación: flujo directo (lumber.reception) ─────────────────────
    def test_cancel_reception_already_cancelled_raises(self):
        rec = self._make_reception(state='cancel')
        with self.assertRaises(UserError) as ctx:
            rec.action_cancel_intake()
        self.assertIn('El ingreso ya se encuentra cancelado.', str(ctx.exception))

    def test_cancel_reception_done_raises_same_message(self):
        rec = self._make_reception(state='done')
        with self.assertRaises(UserError) as ctx:
            rec.action_cancel_intake()
        self.assertIn(
            'El ingreso ya avanzó (enviado a stock). No se puede '
            'cancelar de forma preliminar.',
            str(ctx.exception),
        )

    def test_cancel_reception_with_lots_raises(self):
        rec = self._make_reception(state='verified')
        lot = self.env['stock.lot'].create({
            'name': 'LOTE-CANCEL-1',
            'product_id': self.product.id,
            'reception_id': rec.id,
        })
        self.assertEqual(rec.lot_ids.ids, [lot.id])
        with self.assertRaises(UserError) as ctx:
            rec.action_cancel_intake()
        self.assertIn(
            'El ingreso ya avanzó (enviado a stock). No se puede '
            'cancelar de forma preliminar.',
            str(ctx.exception),
        )

    def test_cancel_reception_with_picking_raises(self):
        rec = self._make_reception(state='verified')
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
            'picking_type_id': self.picking_type.id,
            'move_type': 'direct',
        })
        rec.write({'picking_id': picking.id})
        self.assertEqual(rec.picking_id.id, picking.id)
        with self.assertRaises(UserError) as ctx:
            rec.action_cancel_intake()
        self.assertIn(
            'El ingreso ya avanzó (enviado a stock). No se puede '
            'cancelar de forma preliminar.',
            str(ctx.exception),
        )

    def test_cancel_reception_valid_opens_wizard(self):
        rec = self._make_reception(state='verified')
        action = rec.action_cancel_intake()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.cancel')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context'].get('default_reception_id'), rec.id)

    # ── Reapertura: flujo directo (lumber.reception) ──────────────────────
    def test_reopen_reception_not_cancelled_raises(self):
        rec = self._make_reception(state='verified')
        with self.assertRaises(UserError) as ctx:
            rec.action_reopen_cancelled_intake()
        self.assertIn(
            'Solo se puede reabrir un registro en estado "Cancelado".',
            str(ctx.exception),
        )

    def test_reopen_reception_cancelled_returns_facade(self):
        rec = self._make_reception(state='cancel')
        action = rec.action_reopen_cancelled_intake()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'lumber.reception')
        self.assertEqual(action['res_id'], rec.id)
        self.assertEqual(action['target'], 'current')
        self.assertEqual(action['view_id'], self.env.ref(
            'madenat_lumber_intake.view_lumber_reception_intake_facade_form').id)
        self.assertEqual(rec.state, 'draft')

    # ── Consola: delegación hacia el registro origen real ─────────────────
    def test_console_cancel_for_product_blocked_by_source(self):
        rec = self._make_reception(state='cancel')
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with self.assertRaises(UserError) as ctx:
            console.action_cancel_intake()
        self.assertIn('El ingreso ya se encuentra cancelado.', str(ctx.exception))

    def test_console_cancel_for_product_opens_wizard(self):
        rec = self._make_reception(state='verified')
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        action = console.action_cancel_intake()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.cancel')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context'].get('default_reception_id'), rec.id)

    def test_console_reopen_for_product_delegates_to_source(self):
        rec = self._make_reception(state='cancel')
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        action = console.action_reopen_intake()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'lumber.reception')
        self.assertEqual(action['res_id'], rec.id)
        self.assertEqual(action['target'], 'current')
        self.assertEqual(action['view_id'], self.env.ref(
            'madenat_lumber_intake.view_lumber_reception_intake_facade_form').id)
        self.assertEqual(rec.state, 'draft')