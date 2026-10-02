# -*- coding: utf-8 -*-
"""G3 — Reversión física automática del ingreso de producción Procesada.

Solo aplica a la rama de Producción NUEVA con llave fuerte G2
(`stock.picking.guia_processing_id = madenat.guia.processing.id`). No infiere
ni toca históricos; no usa `origin` textual ni `lot_id` como criterio de
atribución.

Cubre T-G3-01..11. `TransactionCase`: todo se revierte. La reversión es nativa
(crea `stock.picking`/`stock.move`/`stock.move.line` invertidos y valida con
API nativa; NO escribe `stock.quant` directamente).
"""
import inspect

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'g3')
class TestGuiaProductionReverse(TransactionCase):
    """T-G3-01..11 — reversión nativa del ingreso de producción atribuido (FK)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.ReopenWizard = cls.env['madenat.guia.processing.reopen.wizard']
        cls.Audit = cls.env['madenat.audit.log']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.partner = cls.env['res.partner'].create({
            'name': 'G3 Proveedor', 'is_company': True, 'supplier_rank': 1})
        cls.product = cls.env['product.product'].create({
            'name': 'G3 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='compra', state='verified'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 1.0})

    def _make_lot(self, name, volumen=5.0):
        return self.StockLot.create({
            'name': name, 'product_id': self.product.id,
            'volumen_m3': volumen})

    def _make_done_production_picking(self, guia, lot, qty=5.0,
                                      with_fk=True, origin=None):
        """Ingreso de producción DONE.

        Atribuido por la llave fuerte G2 (`guia_processing_id`) salvo
        `with_fk=False` (picking histórico sin vínculo).
        """
        pt = self.env.ref('stock.picking_type_in')
        vals = {
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id,
            'origin': origin if origin is not None else guia.name,
        }
        if with_fk:
            vals['guia_processing_id'] = guia.id
        picking = self.Picking.create(vals)
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

    def _lot_qty_internal(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.internal.id)])
        return sum(quants.mapped('quantity'))

    def _reopen(self, guia, reason='corrección G3'):
        wiz = self.ReopenWizard.create(
            {'guia_processing_id': guia.id, 'reason': reason})
        wiz.action_confirm()
        return wiz

    # ── T-G3-01 — Reversión nativa del ingreso de producción DONE ─────────
    def test_t_g3_01_reversion_nativa_ingreso_done(self):
        guia = self._make_guia('G3-01')
        lot = self._make_lot('G3-01-LOT')
        picking = self._make_done_production_picking(guia, lot, qty=5.0)
        self.assertEqual(picking.state, 'done')
        self.assertAlmostEqual(self._lot_qty_internal(lot), 5.0, places=3)

        self._reopen(guia)

        returns = self.Picking.search([('return_id', '=', picking.id)])
        self.assertEqual(len(returns), 1, 'Debe existir UNA salida inversa')
        ret = returns
        self.assertEqual(ret.state, 'done')
        self.assertEqual(ret.picking_type_code, 'outgoing')
        self.assertEqual(ret.location_id, self.internal)
        self.assertEqual(ret.location_dest_id, picking.location_id)
        self.assertEqual(ret.location_dest_id.usage, 'supplier')
        # Reversión física neta: el stock del lote vuelve a 0.
        self.assertAlmostEqual(self._lot_qty_internal(lot), 0.0, places=3)

        # La reversión es nativa: no escribe stock.quant directamente y la
        # atribución es exclusiva por FK (no `origin` ni `lot_id`).
        src = inspect.getsource(type(self.Guia)._reverse_production_picking)
        self.assertNotIn('stock.quant', src)
        attr_src = inspect.getsource(
            type(self.Guia)._attributed_production_pickings)
        self.assertIn("('guia_processing_id', '=', self.id)", attr_src)
        self.assertNotIn("('origin'", attr_src)
        self.assertNotIn("('lot_id'", attr_src)

    # ── T-G3-02 — Idempotencia ────────────────────────────────────────────
    def test_t_g3_02_idempotente_sin_duplicar(self):
        guia = self._make_guia('G3-02')
        lot = self._make_lot('G3-02-LOT')
        picking = self._make_done_production_picking(guia, lot)

        self._reopen(guia)
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1)

        # Segundo intento: reabrir de nuevo NO duplica el retorno.
        guia.write({'state': 'verified'})
        self._reopen(guia)
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1,
            'La reversión debe ser idempotente (reutiliza el retorno nativo)')

    # ── T-G3-03 — El retorno NO porta el vínculo G2 ───────────────────────
    def test_t_g3_03_retorno_sin_vinculo_g2(self):
        guia = self._make_guia('G3-03')
        lot = self._make_lot('G3-03-LOT')
        picking = self._make_done_production_picking(guia, lot)

        self._reopen(guia)

        ret = self.Picking.search([('return_id', '=', picking.id)], limit=1)
        self.assertTrue(ret)
        self.assertFalse(
            ret.guia_processing_id,
            'El retorno no debe portar guia_processing_id (exclusión G2)')

    # ── T-G3-04 — Histórico sin FK NO se revierte ─────────────────────────
    def test_t_g3_04_historico_sin_fk_no_revertido(self):
        guia = self._make_guia('G3-04')
        lot = self._make_lot('G3-04-LOT')
        # Picking histórico: origin == guia.name, SIN llave fuerte G2.
        hist = self._make_done_production_picking(guia, lot, with_fk=False)
        self.assertFalse(hist.guia_processing_id)

        self._reopen(guia)

        self.assertFalse(
            self.Picking.search([('return_id', '=', hist.id)]),
            'Un histórico sin FK no debe revertirse')
        self.assertTrue(hist.exists(), 'El histórico se conserva intacto')
        self.assertAlmostEqual(self._lot_qty_internal(lot), 5.0, places=3)

    # ── T-G3-05 — Historia física preservada ──────────────────────────────
    def test_t_g3_05_historia_preservada(self):
        guia = self._make_guia('G3-05')
        lot = self._make_lot('G3-05-LOT')
        picking = self._make_done_production_picking(guia, lot)
        move = picking.move_ids[:1]
        line = move.move_line_ids[:1]

        self._reopen(guia)

        for record in (picking, move, line, lot):
            self.assertTrue(record.exists(), 'La historia física se preserva')
        self.assertEqual(picking.state, 'done', 'El original sigue DONE')


    # ── T-G3-06 — Efecto físico detectado + motivo obligatorio ────────────
    def test_t_g3_06_efecto_fisico_y_motivo_obligatorio(self):
        guia = self._make_guia('G3-06')
        lot = self._make_lot('G3-06-LOT')
        self._make_done_production_picking(guia, lot)

        wiz = self.ReopenWizard.create({'guia_processing_id': guia.id})
        self.assertTrue(wiz.has_physical_effect)
        self.assertIn('producción', (wiz.effect_summary or '').lower())

        # Sin motivo → no bloquea la UI, pero el ejecutor exige trazabilidad.
        with self.assertRaises(UserError):
            wiz.action_confirm()
        self.assertEqual(guia.state, 'verified', 'Sin motivo, no se ejecuta')

    # ── T-G3-07 — Trazabilidad (auditoría + chatter + snapshot) ───────────
    def test_t_g3_07_trazabilidad_audit_y_chatter(self):
        guia = self._make_guia('G3-07')
        lot = self._make_lot('G3-07-LOT')
        picking = self._make_done_production_picking(guia, lot)

        self._reopen(guia, reason='Motivo G3 auditado')

        ret = self.Picking.search([('return_id', '=', picking.id)], limit=1)
        self.assertTrue(ret)
        log = self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertIn('Motivo G3 auditado', log.audit_snapshot or '')
        self.assertIn('production_returns', log.audit_snapshot or '')
        self.assertIn(ret.name, log.audit_snapshot or '')
        self.assertEqual(len(log.audit_hash), 64)
        chatter = '\n'.join(guia.message_ids.mapped('body') or [])
        self.assertIn('Reapertura trazable', chatter)
        self.assertIn('Producción revertida', chatter)

    # ── T-G3-08 — Atribución por FK, NO por origin textual ────────────────
    def test_t_g3_08_atribucion_por_fk_no_origin(self):
        guia = self._make_guia('G3-08')
        lot = self._make_lot('G3-08-LOT')
        # FK presente pero `origin` DISTINTO del nombre de la guía.
        picking = self._make_done_production_picking(
            guia, lot, origin='OTRO-DOCUMENTO-XYZ')

        self.assertEqual(picking.guia_processing_id, guia)
        self.assertNotEqual(picking.origin, guia.name)

        self._reopen(guia)

        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1,
            'La atribución debe ser por FK, no por `origin` textual')

    # ── T-G3-09 — Atribución ajena a `lot_id` ─────────────────────────────
    def test_t_g3_09_atribucion_ignora_lot_id(self):
        guia = self._make_guia('G3-09')
        lot = self._make_lot('G3-09-LOT')
        picking = self._make_done_production_picking(guia, lot)
        # El lote NO está vinculado a la guía (`lot_ids` vacío): la atribución
        # del picking es exclusivamente por FK, nunca por `lot_id`.
        self.assertFalse(guia.lot_ids)

        self._reopen(guia)

        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1)

    # ── T-G3-10 — Pickings NO done no se revierten (solo retorno de DONE) ─
    def test_t_g3_10_no_revierte_picking_no_done(self):
        guia = self._make_guia('G3-10')
        pt = self.env.ref('stock.picking_type_in')
        draft = self.Picking.create({
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id,
            'origin': guia.name, 'guia_processing_id': guia.id})

        self._reopen(guia)

        self.assertFalse(
            self.Picking.search([('return_id', '=', draft.id)]),
            'Un picking no DONE no genera retorno')
        # El borrador queda cancelado por el flujo nativo (no revertido).
        self.assertEqual(draft.state, 'cancel')

    # ── T-G3-11 — Multi-picking DONE atribuido (una salida por picking) ───
    def test_t_g3_11_un_retorno_por_picking_done(self):
        guia = self._make_guia('G3-11')
        lot_a = self._make_lot('G3-11-A')
        lot_b = self._make_lot('G3-11-B')
        pa = self._make_done_production_picking(guia, lot_a)
        pb = self._make_done_production_picking(guia, lot_b)
        self.assertEqual(guia._attributed_production_pickings(), pa | pb)

        self._reopen(guia)

        self.assertEqual(
            self.Picking.search_count([('return_id', '=', pa.id)]), 1)
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', pb.id)]), 1)
        self.assertAlmostEqual(self._lot_qty_internal(lot_a), 0.0, places=3)
        self.assertAlmostEqual(self._lot_qty_internal(lot_b), 0.0, places=3)
