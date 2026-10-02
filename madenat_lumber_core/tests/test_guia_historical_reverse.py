# -*- coding: utf-8 -*-
"""H1 — Reversión física ASISTIDA de producción histórica (sin llave fuerte G2).

Cubre T-H1-01..11. `TransactionCase`: todo se revierte. H1 NO sustituye a
G1/G2/G3/BT-04/SV/granel. La reversión es nativa total por picking, idempotente
y preserva la historia (nunca `stock.quant.write/unlink` ni borrado de lotes,
pickings, moves o move lines; `lot_ids` intacto).
"""
import inspect

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'h1')
class TestGuiaHistoricalReverse(TransactionCase):
    """T-H1-01..11 — reversión histórica asistida (selección explícita)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.Audit = cls.env['madenat.audit.log']
        cls.Wizard = cls.env[
            'madenat.guia.processing.historical.reverse.wizard']
        cls.Candidate = cls.env[
            'madenat.guia.processing.historical.reverse.candidate']
        cls.ReopenWizard = cls.env['madenat.guia.processing.reopen.wizard']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.partner = cls.env['res.partner'].create({
            'name': 'H1 Proveedor', 'is_company': True, 'supplier_rank': 1})
        cls.product = cls.env['product.product'].create({
            'name': 'H1 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='service', state='validated',
                   with_lot=True):
        guia = self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 1.0})
        lot = False
        if with_lot:
            lot = self._make_lot('LOT-%s' % name, 5.0)
            guia.lot_ids = [(6, 0, [lot.id])]
        return guia, lot

    def _make_lot(self, name, volumen=5.0):
        return self.StockLot.create({
            'name': name, 'product_id': self.product.id,
            'volumen_m3': volumen})

    def _make_production_picking(self, guia, lot, qty=5.0, with_fk=False,
                                 origin=None):
        """Ingreso de producción DONE que referencia `lot`.

        Atribuido por la llave fuerte G2 solo si `with_fk=True` (histórico en
        caso contrario).
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
            'name': 'Prod %s' % guia.name, 'product_id': lot.product_id.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id})
        picking.action_confirm()
        picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': lot.product_id.id, 'lot_id': lot.id,
            'quantity': qty, 'product_uom_id': self.uom.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id, 'picked': True})
        move.picked = True
        move._action_done()
        picking.write({'state': 'done'})
        return picking

    def _make_out_picking(self, guia, lot, qty=5.0, origin=None):
        out_type = self.warehouse.out_type_id
        picking = self.Picking.create({
            'picking_type_id': out_type.id, 'partner_id': self.partner.id,
            'location_id': self.internal.id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'origin': origin if origin is not None else guia.name})
        self.Move.create({
            'name': 'Salida %s' % guia.name, 'product_id': lot.product_id.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id, 'location_id': self.internal.id,
            'location_dest_id': picking.location_dest_id.id})
        return picking

    def _candidate_for(self, guia, picking):
        wiz = self.Wizard.create({'guia_processing_id': guia.id})
        return wiz, wiz.candidate_ids.filtered(
            lambda c: c.picking_id == picking)

    # ── T-H1-01 — Categoría A: preselecciona y revierte total nativo ──────
    def test_t_h1_01_categoria_a_preselecciona_y_revierte(self):
        guia, lot = self._make_guia('H1-01')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)
        self.assertAlmostEqual(self._lot_qty_internal(lot), 5.0, places=3)

        wiz, cand = self._candidate_for(guia, picking)
        self.assertEqual(len(cand), 1)
        self.assertEqual(cand.category, 'A')
        self.assertTrue(cand.eligible)
        self.assertTrue(cand.selected, 'Categoría A viene preseleccionada')

        wiz.reason = 'corrección histórica categoría A'
        wiz.action_confirm()

        returns = self.Picking.search([('return_id', '=', picking.id)])
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns.state, 'done')
        self.assertAlmostEqual(self._lot_qty_internal(lot), 0.0, places=3)

    # ── T-H1-02 — Categoría B: visible, no preseleccionado ───────────────
    def test_t_h1_02_categoria_b_no_preseleccionado(self):
        guia, lot = self._make_guia('H1-02')
        # Picking con origen exacto pero lote AJENO a la guía → evidencia B.
        other = self._make_lot('H1-02-OTRO', 3.0)
        picking = self._make_production_picking(
            guia, other, qty=3.0, with_fk=False)

        wiz, cand = self._candidate_for(guia, picking)
        self.assertEqual(cand.category, 'B')
        self.assertTrue(cand.eligible)
        self.assertFalse(cand.selected, 'Categoría B no se preselecciona')

        # Sin selección: reapertura documental sin efecto físico.
        wiz.action_confirm()
        self.assertFalse(self.Picking.search([('return_id', '=', picking.id)]))
        self.assertEqual(guia.state, 'validated')
        self.assertTrue(lot.exists())

    # ── T-H1-03 — Categoría C: no seleccionable + granel no ofrecida ─────
    def test_t_h1_03_categoria_c_no_seleccionable(self):
        guia, lot = self._make_guia('H1-03')
        hist = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False, origin='REVERTIDO-H1-03')
        wiz, cand = self._candidate_for(guia, hist)
        self.assertEqual(cand.category, 'C')
        self.assertFalse(cand.eligible)
        self.assertFalse(cand.selected)
        self.assertTrue(cand.exclusion_reason)
        # Forzar selección de un inelegible → no se permite confirmar.
        cand.selected = True
        with self.assertRaises(UserError):
            wiz.action_confirm()

    def test_t_h1_03b_granel_no_ofrecida(self):
        guia = self.Guia.create({
            'name': 'H1-03B', 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': 'granel', 'state': 'validated', 'rate_usd': 1.0})
        self.assertFalse(guia.can_historical_reverse)
        with self.assertRaises(UserError):
            guia._h1_confirm_historical_reverse(
                self.env['stock.picking'], reason='x')

    # ── T-H1-04 — Retorno total conserva atributos y trazabilidad ────────
    def test_t_h1_04_retorno_preserva_atributos(self):
        guia, lot = self._make_guia('H1-04')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)
        src_move = picking.move_ids[:1]
        src_line = src_move.move_line_ids[:1]

        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': 'preserva atributos'})
        wiz.action_confirm()

        ret = self.Picking.search([('return_id', '=', picking.id)], limit=1)
        self.assertTrue(ret)
        ret_line = ret.move_line_ids[:1]
        self.assertEqual(ret_line.product_id, src_line.product_id)
        self.assertEqual(ret_line.product_uom_id, src_line.product_uom_id)
        self.assertEqual(ret_line.lot_id, src_line.lot_id)
        self.assertEqual(ret_line.owner_id, src_line.owner_id)
        self.assertEqual(ret_line.package_id, src_line.package_id)
        self.assertEqual(ret_line.quantity, src_line.quantity)
        self.assertEqual(ret.location_id, picking.location_dest_id)
        self.assertEqual(ret.location_dest_id, picking.location_id)
        self.assertEqual(ret.company_id, picking.company_id)
        self.assertTrue(ret.move_ids.mapped('origin_returned_move_id'))

    # ── Helper: stock interno del lote ────────────────────────────────────
    def _lot_qty_internal(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.internal.id)])
        return sum(quants.mapped('quantity'))

    # ── T-H1-05 — Idempotencia: no duplica retorno ───────────────────────
    def test_t_h1_05_idempotencia(self):
        guia, lot = self._make_guia('H1-05')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)

        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': 'primera reversión'})
        wiz.action_confirm()
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1)

        # Reintento: el picking ya no se propone como elegible.
        wiz2, cand = self._candidate_for(guia, picking)
        self.assertEqual(cand.category, 'C')
        self.assertFalse(cand.eligible)
        self.assertTrue(cand.exclusion_reason)
        # Doble confirmación por API interna → reutiliza, no duplica.
        ret2 = guia._h1_reverse_picking_total(picking)
        self.assertTrue(ret2)
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1)

    # ── T-H1-06 — Exclusiones duras (no proponibles) ─────────────────────
    def test_t_h1_06_exclusiones(self):
        # 1) FK G2 → pertenece a G3; guía deja de ser elegible para H1.
        guia, lot = self._make_guia('H1-06')
        alt = self._make_lot('H1-06-FK', 5.0)
        fk_pick = self._make_production_picking(
            guia, alt, qty=5.0, with_fk=True)
        self.assertFalse(guia.can_historical_reverse)
        _wiz, cand = self._candidate_for(guia, fk_pick)
        self.assertEqual(cand.category, 'C')
        self.assertFalse(cand.eligible)

        # 2) Prefijo histórico en `origin` → excluido (evidencia débil).
        guia2, lot2 = self._make_guia('H1-06B')
        hist = self._make_production_picking(
            guia2, lot2, qty=5.0, origin='ANULADO-H1-06B')
        _wiz2, cand2 = self._candidate_for(guia2, hist)
        self.assertEqual(cand2.category, 'C')
        self.assertFalse(cand2.eligible)

        # 3) Picking NO DONE (no reversible) → excluido.
        guia3, lot3 = self._make_guia('H1-06C')
        pt = self.env.ref('stock.picking_type_in')
        draft = self.Picking.create({
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id, 'origin': guia3.name})
        _wiz3, cand3 = self._candidate_for(guia3, draft)
        self.assertEqual(cand3.category, 'C')
        self.assertFalse(cand3.eligible)

        # 4) Consumo BT-04 (llave fuerte) → guía no elegible para H1.
        guia4, lot4 = self._make_guia('H1-06D')
        out = self._make_out_picking(guia4, lot4, qty=5.0)
        guia4.consumption_picking_id = out.id
        self.assertFalse(guia4.can_historical_reverse)
        self.assertFalse(guia4._h1_is_historical_production())

    # ── T-H1-07 — Preservación de la historia física y documental ────────
    def test_t_h1_07_preservacion(self):
        guia, lot = self._make_guia('H1-07')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)
        move = picking.move_ids[:1]
        line = move.move_line_ids[:1]
        lot_ids_before = guia.lot_ids

        wiz = self.Wizard.create(
            {'guia_processing_id': guia.id, 'reason': 'preservación'})
        wiz.action_confirm()

        # `lot_ids` y la historia física permanecen intactos.
        self.assertEqual(guia.lot_ids, lot_ids_before)
        self.assertTrue(lot.exists())
        for record in (picking, move, line):
            self.assertTrue(record.exists())
        self.assertEqual(picking.state, 'done', 'El original sigue DONE')
        # La reversión es nativa: no escribe ni borra stock.quant.
        src = inspect.getsource(type(guia)._h1_reverse_picking_total)
        self.assertNotIn('stock.quant', src)
        self.assertNotIn('.unlink(', src)

    # ── T-H1-08 — Motivo obligatorio solo con efecto físico ──────────────
    def test_t_h1_08_motivo(self):
        guia, lot = self._make_guia('H1-08')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)

        # Categoría A preseleccionada sin motivo → exige trazabilidad.
        wiz = self.Wizard.create({'guia_processing_id': guia.id})
        self.assertTrue(wiz.has_selection)
        with self.assertRaises(UserError):
            wiz.action_confirm()
        self.assertFalse(self.Picking.search([('return_id', '=', picking.id)]))
        wiz.reason = 'ahora sí con motivo'
        wiz.action_confirm()
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', picking.id)]), 1)

        # Sin selección: motivo opcional y sin efecto físico.
        guia2, lot2 = self._make_guia('H1-08B')
        wiz2 = self.Wizard.create({'guia_processing_id': guia2.id})
        self.assertFalse(wiz2.has_selection)
        wiz2.action_confirm()
        self.assertEqual(guia2.state, 'validated')
        self.assertTrue(lot2.exists())

    # ── T-H1-09 — Auditoría (snapshot + hash) y chatter ──────────────────
    def test_t_h1_09_auditoria(self):
        guia, lot = self._make_guia('H1-09')
        picking = self._make_production_picking(
            guia, lot, qty=5.0, with_fk=False)
        wiz = self.Wizard.create({
            'guia_processing_id': guia.id, 'reason': 'Motivo H1 auditado'})
        wiz.action_confirm()

        log = self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertTrue(log)
        snapshot = log.audit_snapshot or ''
        self.assertIn('Motivo H1 auditado', snapshot)
        self.assertIn('selection', snapshot)
        self.assertIn('returns', snapshot)
        self.assertIn('warnings', snapshot)
        self.assertIn(picking.name, snapshot)
        self.assertEqual(len(log.audit_hash), 64)
        chatter = '\n'.join(guia.message_ids.mapped('body') or [])
        self.assertIn('Reversión histórica asistida', chatter)

    # ── T-H1-10 — Sin candidatos: reapertura documental, sin efecto ──────
    def test_t_h1_10_sin_candidatos(self):
        guia, lot = self._make_guia('H1-10')
        wiz = self.Wizard.create({'guia_processing_id': guia.id})
        self.assertFalse(wiz.candidate_ids.filtered('eligible'))
        self.assertFalse(wiz.has_selection)
        wiz.action_confirm()
        # Historia física/documental conservada.
        self.assertTrue(lot.exists())
        self.assertEqual(guia.state, 'validated')
        self.assertIn(lot, guia.lot_ids)

    # ── T-H1-11 — No regresión G1/G2/G3 ni BT-04 ─────────────────────────
    def test_t_h1_11_no_regresion_g3(self):
        guia, lot = self._make_guia('H1-11', state='verified')
        alt = self._make_lot('H1-11-FK', 5.0)
        fk = self._make_production_picking(
            guia, alt, qty=5.0, with_fk=True)
        # H1 no se ofrece (producción con llave fuerte G2).
        self.assertFalse(guia.can_historical_reverse)
        # La ruta G1/G3 sigue intacta: reversión automática por FK.
        reopen = self.ReopenWizard.create(
            {'guia_processing_id': guia.id, 'reason': 'G3 intacto'})
        reopen.action_confirm()
        self.assertEqual(
            self.Picking.search_count([('return_id', '=', fk.id)]), 1)
