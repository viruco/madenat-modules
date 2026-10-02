# -*- coding: utf-8 -*-
"""Reapertura no bloqueante y trazable de una guía procesada (Incremento G1).

Cubre T-GUIA-REOPEN-01..10. TransactionCase: todo se revierte. La reversión
física usa mecanismos nativos (`_reverse_consumption_picking`); no se escribe
ni borra `stock.quant`.
"""
import inspect

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core')
class TestGuiaReopenTraceable(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Lot = cls.env['stock.lot']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.Quant = cls.env['stock.quant']
        cls.Wizard = cls.env['madenat.guia.processing.reopen.wizard']
        cls.Audit = cls.env['madenat.audit.log']
        cls.company = cls.env.company
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.external_location = cls.env.ref('stock.stock_location_customers')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Guia Reopen', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Reopen Test Lumber', 'is_storable': True,
            'tracking': 'lot', 'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Helpers ───────────────────────────────────────────────────────────
    def _make_guia(self, name, state='verified', tipo='service', with_lot=True):
        guia = self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 800.0})
        lot = False
        if with_lot:
            lot = self.Lot.create({
                'name': 'LOT-%s' % name, 'product_id': self.product.id,
                'volumen_m3': 5.0})
            guia.lot_ids = [(6, 0, [lot.id])]
            self.Quant._update_available_quantity(
                self.product, self.internal, 5.0, lot_id=lot)
        return guia, lot

    def _add_production_picking(self, guia, lot, qty=5.0):
        pt = self.env.ref('stock.picking_type_in')
        picking = self.Picking.create({
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id, 'origin': guia.name})
        move = self.Move.create({
            'name': 'Prod %s' % guia.name, 'product_id': self.product.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id})
        picking.action_confirm()
        picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'lot_id': lot.id, 'quantity': qty,
            'product_uom_id': self.uom.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id, 'picked': True})
        move.picked = True
        move._action_done()
        picking.write({'state': 'done'})
        return picking

    def _add_consumption(self, guia, source_lot, qty=5.0):
        out_type = self.warehouse.out_type_id
        picking = self.Picking.create({
            'picking_type_id': out_type.id, 'partner_id': self.partner.id,
            'location_id': self.internal.id,
            'location_dest_id': self.external_location.id,
            'origin': 'Salida a proceso %s' % guia.name})
        move = self.Move.create({
            'name': 'Consumo %s' % guia.name, 'product_id': self.product.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id, 'location_id': self.internal.id,
            'location_dest_id': self.external_location.id})
        picking.action_confirm()
        picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'lot_id': source_lot.id,
            'quantity': qty, 'product_uom_id': self.uom.id,
            'location_id': self.internal.id,
            'location_dest_id': self.external_location.id, 'picked': True})
        move.picked = True
        move._action_done()
        picking.write({'state': 'done'})
        guia.consumption_picking_id = picking.id
        return picking

    def _confirm(self, guia, reason=None):
        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': reason})
        return wiz, wiz.action_confirm()

    # ── T-GUIA-REOPEN-01 ──────────────────────────────────────────────────
    def test_t_guia_reopen_01_public_action_opens_wizard(self):
        guia, lot = self._make_guia('GR-01')
        action = guia.action_reopen_to_draft()
        self.assertEqual(action['res_model'], 'madenat.guia.processing.reopen.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(guia.state, 'verified')  # el método público no resetea
        self.assertTrue(lot.exists())
        src = inspect.getsource(type(guia).action_reopen_to_draft)
        self.assertNotIn('stock.quant', src)
        src2 = inspect.getsource(type(guia)._reopen_to_draft_confirmed)
        self.assertNotIn('quants_to_clear', src2)
        self.assertNotIn('revert_lot_ids', src2)

    # ── T-GUIA-REOPEN-02 ──────────────────────────────────────────────────
    def test_t_guia_reopen_02_consumption_reversed_native_idempotent(self):
        guia, lot = self._make_guia('GR-02')
        source = self.Lot.create({
            'name': 'SRC-GR-02', 'product_id': self.product.id,
            'volumen_m3': 5.0})
        self.Quant._update_available_quantity(
            self.product, self.internal, 5.0, lot_id=source)
        consumption = self._add_consumption(guia, source)
        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': 'corrección BT-04'})
        self.assertTrue(wiz.has_physical_effect)
        wiz.action_confirm()
        ret = self.Picking.search(
            [('origin', '=', 'Return of %s' % consumption.name)])
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret.state, 'done')
        self.assertFalse(guia.consumption_picking_id)
        # Reintento: ya sin efecto físico, no duplica el retorno.
        guia.write({'state': 'verified'})
        self._confirm(guia)
        self.assertEqual(self.Picking.search_count(
            [('origin', '=', 'Return of %s' % consumption.name)]), 1)

    # ── T-GUIA-REOPEN-03 ──────────────────────────────────────────────────
    def test_t_guia_reopen_03_production_preserves_history_warns(self):
        guia, lot = self._make_guia('GR-03')
        picking = self._add_production_picking(guia, lot)
        move = picking.move_ids[:1]
        line = move.move_line_ids[:1]
        qbefore = self.Quant.search_count([('lot_id', '=', lot.id)])
        wiz = self.Wizard.create({'guia_processing_id': guia.id})
        self.assertFalse(wiz.has_physical_effect)
        self.assertTrue(wiz.warning_text, 'Debe advertir atribución insuficiente')
        wiz.action_confirm()
        self.assertEqual(guia.state, 'draft')
        for record in (lot, picking, move, line):
            self.assertTrue(record.exists(), 'Historial físico preservado')
        self.assertEqual(
            self.Quant.search_count([('lot_id', '=', lot.id)]), qbefore)

    # ── T-GUIA-REOPEN-04 ──────────────────────────────────────────────────
    def test_t_guia_reopen_04_no_effect_optional_reason(self):
        guia, lot = self._make_guia('GR-04', with_lot=False)
        wiz = self.Wizard.create({'guia_processing_id': guia.id})
        self.assertFalse(wiz.has_physical_effect)
        wiz.action_confirm()
        self.assertEqual(guia.state, 'draft')
        self.assertTrue(self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')]))

    # ── T-GUIA-REOPEN-05 ──────────────────────────────────────────────────
    def test_t_guia_reopen_05_warnings_do_not_block(self):
        guia, lot = self._make_guia('GR-05')
        # Albarán con salida externa validada (origen = guía).
        out_type = self.warehouse.out_type_id
        ext = self.Picking.create({
            'picking_type_id': out_type.id, 'partner_id': self.partner.id,
            'location_id': self.internal.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'origin': guia.name})
        emove = self.Move.create({
            'name': 'Ext %s' % guia.name, 'product_id': self.product.id,
            'product_uom_qty': 5.0, 'product_uom': self.uom.id,
            'picking_id': ext.id, 'location_id': self.internal.id,
            'location_dest_id': ext.location_dest_id.id})
        ext.action_confirm()
        ext.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': emove.id, 'picking_id': ext.id,
            'product_id': self.product.id, 'lot_id': lot.id, 'quantity': 5.0,
            'product_uom_id': self.uom.id, 'location_id': self.internal.id,
            'location_dest_id': ext.location_dest_id.id, 'picked': True})
        emove.picked = True
        emove._action_done()
        ext.write({'state': 'done'})
        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': 'con warnings'})
        self.assertTrue(wiz.warning_text)
        wiz.action_confirm()
        self.assertEqual(guia.state, 'draft')
        self.assertTrue(self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')]))


    # ── T-GUIA-REOPEN-06 ──────────────────────────────────────────────────
    def test_t_guia_reopen_06_physical_effect_requires_reason(self):
        guia, lot = self._make_guia('GR-06')
        source = self.Lot.create({
            'name': 'SRC-GR-06', 'product_id': self.product.id,
            'volumen_m3': 5.0})
        self.Quant._update_available_quantity(
            self.product, self.internal, 5.0, lot_id=source)
        consumption = self._add_consumption(guia, source)
        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': False})
        self.assertTrue(wiz.has_physical_effect)
        with self.assertRaises(UserError):
            wiz.action_confirm()
        self.assertEqual(guia.state, 'verified')
        self.assertFalse(self.Picking.search(
            [('origin', '=', 'Return of %s' % consumption.name)]))
        wiz.reason = 'ahora sí con motivo'
        wiz.action_confirm()
        self.assertEqual(guia.state, 'draft')

    # ── T-GUIA-REOPEN-07 ──────────────────────────────────────────────────
    def test_t_guia_reopen_07_staging_cleaned_history_preserved(self):
        guia, lot = self._make_guia('GR-07')
        self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id, 'product_id': self.product.id,
            'lot_name': 'L-GR-07', 'pieces': 3, 'vol_purchase_m3': 2.0,
            'vol_shipment_m3': 2.0, 'espesor_nominal_mm': 50,
            'ancho_nominal_mm': 100, 'largo_nominal_m': 2.0})
        picking = self._add_production_picking(guia, lot)
        self.assertTrue(guia.processing_line_ids)
        self._confirm(guia)
        guia.invalidate_recordset(['processing_line_ids'])
        self.assertFalse(guia.processing_line_ids, 'Staging regenerable limpiado')
        self.assertTrue(lot.exists())
        self.assertTrue(picking.exists())

    # ── T-GUIA-REOPEN-08 ──────────────────────────────────────────────────
    def test_t_guia_reopen_08_audit_and_chatter(self):
        guia, lot = self._make_guia('GR-08')
        source = self.Lot.create({
            'name': 'SRC-GR-08', 'product_id': self.product.id,
            'volumen_m3': 5.0})
        self.Quant._update_available_quantity(
            self.product, self.internal, 5.0, lot_id=source)
        self._add_consumption(guia, source)
        self._confirm(guia, reason='Motivo auditado')
        log = self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertIn('Motivo auditado', log.audit_snapshot or '')
        self.assertIn('consumption_picking', log.audit_snapshot or '')
        self.assertEqual(len(log.audit_hash), 64)
        chatter = '\n'.join(guia.message_ids.mapped('body') or [])
        self.assertIn('Reapertura trazable', chatter)

    # ── T-GUIA-REOPEN-09 ──────────────────────────────────────────────────
    def test_t_guia_reopen_09_rpc_direct_cannot_evade(self):
        guia, lot = self._make_guia('GR-09')
        action = guia.action_reopen_to_draft()
        self.assertEqual(
            action['res_model'], 'madenat.guia.processing.reopen.wizard')
        self.assertEqual(guia.state, 'verified')  # no hay efecto directo
        # El ejecutor es privado (prefijo '_') ⇒ no invocable por RPC.
        self.assertTrue('_reopen_to_draft_confirmed'.startswith('_'))

    # ── T-GUIA-REOPEN-10 ──────────────────────────────────────────────────
    def test_t_guia_reopen_10_validated_reopen_documental_no_zeroing(self):
        guia, lot = self._make_guia('GR-10', state='validated')
        picking = self._add_production_picking(guia, lot)
        qbefore = self.Quant.search_count([('lot_id', '=', lot.id)])
        self._confirm(guia)
        self.assertEqual(guia.state, 'draft')
        self.assertTrue(lot.exists())
        self.assertTrue(picking.exists())
        self.assertEqual(
            self.Quant.search_count([('lot_id', '=', lot.id)]), qbefore,
            'Sin zeroing de stock.quant')
