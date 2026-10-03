# -*- coding: utf-8 -*-
"""P0-R (F-02) — Retorno físico SV limpio y trazable.

Remediación verificable del hallazgo ALTO F-02: `_sv_create_volume_return()`
creaba y validaba manualmente `stock.picking`/`stock.move`/`stock.move.line`
con tipo de operación heurístico y contexto inerte
(`force_validate`/`skip_immediate`/`immediate_transfer`), no consumido por el
flujo de stock de Odoo 18 auditado.

Cubre T-P0R-RET-01 .. T-P0R-RET-10. Datos aislados (TransactionCase).
"""
import inspect

from odoo.addons.madenat_lumber_core.models.madenat_guia_processing import (
    MadenatGuiaProcessing,
)
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

NO_BALANCE_MSG = ('No existe saldo disponible del lote SV asociado para '
                  'realizar la reversa.')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'sv', 'p0r')
class TestP0rSvReturn(SvTestCommon, TransactionCase):
    """Retorno de recepción SV: trazabilidad, tipo, lote, idempotencia."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    # ── Utilidades ────────────────────────────────────────────────────────
    def _return_picking(self, receipt):
        return self.env['stock.picking'].search([
            ('origin', '=', 'Return of %s' % receipt.name)])

    def _reverse(self, guia, receipt):
        guia.action_force_cancel()
        returns = self._return_picking(receipt)
        self.assertEqual(len(returns), 1, 'Debe existir UNA devolución SV')
        return returns

    def _internal_available(self, lot):
        return self.Quant._get_available_quantity(
            lot.product_id, self.internal_loc, lot_id=lot)

    def _unrelated_lot(self, label, quantity):
        """Lote ajeno (no-SV) con quant propio; devuelve el recordset creado.

        F-P0R-G: antes no retornaba el registro, por lo que los tests que lo
        usaban (`test_04`, `test_09`) recibían ``None`` y fallaban con
        ``'NoneType' object has no attribute 'invalidate_recordset'``.
        """
        other = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        self._sv_add_quant(other, quantity)
        return other

    # ── T-P0R-RET-01 ──────────────────────────────────────────────────────
    def test_01_retorno_trazable_relacion_nativa(self):
        """La reversión liga el retorno al movimiento origen (relación nativa)."""
        guia = self._sv_make_guia('P0R-RET-01')
        lot = self._sv_make_lot(guia, label='SV00000000601')
        receipt = self._sv_receipt(guia, lot, 40.3)

        return_picking = self._reverse(guia, receipt)

        return_moves = return_picking.move_ids
        self.assertEqual(len(return_moves), 1)
        self.assertEqual(return_moves.origin_returned_move_id, receipt.move_ids)
        self.assertIn(return_moves, receipt.move_ids.returned_move_ids)
        self.assertEqual(return_picking.return_id, receipt)

    # ── T-P0R-RET-02 ──────────────────────────────────────────────────────
    def test_02_tipo_y_ubicaciones_nativos(self):
        """Tipo de operación y ubicaciones derivados de la configuración nativa."""
        guia = self._sv_make_guia('P0R-RET-02')
        lot = self._sv_make_lot(guia, label='SV00000000602')
        receipt = self._sv_receipt(guia, lot, 40.3)

        expected_type = receipt.picking_type_id.return_picking_type_id
        expected_dest = (
            expected_type.default_location_dest_id
            if expected_type and expected_type.code == 'incoming'
            else receipt.location_id)
        return_picking = self._reverse(guia, receipt)

        self.assertEqual(
            return_picking.picking_type_id,
            expected_type or receipt.picking_type_id)
        self.assertEqual(return_picking.location_id, receipt.location_dest_id)
        self.assertEqual(return_picking.location_dest_id, expected_dest)
        self.assertEqual(return_picking.location_id.usage, 'internal')
        self.assertEqual(return_picking.location_dest_id.usage, 'supplier')

    # ── T-P0R-RET-03 ──────────────────────────────────────────────────────
    def test_03_sin_claves_de_contexto_inertes(self):
        """El retorno no depende de claves no consumidas por Odoo 18."""
        source = inspect.getsource(
            MadenatGuiaProcessing._sv_create_volume_return)
        self.assertIn('skip_backorder=True', source)
        self.assertNotIn('force_validate=True', source)
        self.assertNotIn('skip_immediate=True', source)
        self.assertNotIn('immediate_transfer=True', source)

    # ── T-P0R-RET-04 ──────────────────────────────────────────────────────
    def test_04_estados_y_quants_exactos(self):
        """Moves/picking done; solo el lote SV baja por la cantidad devuelta."""
        guia = self._sv_make_guia('P0R-RET-04')
        lot = self._sv_make_lot(guia, label='SV00000000603')
        receipt = self._sv_receipt(guia, lot, 40.3)
        other = self._unrelated_lot('OTHER-P0R-RET-04', 40.3)

        return_picking = self._reverse(guia, receipt)

        self.assertEqual(return_picking.state, 'done')
        self.assertTrue(all(
            move.state == 'done' for move in return_picking.move_ids))
        self.assertAlmostEqual(self._internal_available(lot), 0.0, places=3)
        other.invalidate_recordset()
        self.assertAlmostEqual(
            self._internal_available(other), 40.3, places=3)
        # Solo los movimientos del retorno (ningún movimiento ajeno).
        self.assertEqual(self.env['stock.move'].search_count([
            ('origin', '=', 'Return of %s' % receipt.name)]), 1)

        return other


    # ── T-P0R-RET-05 ──────────────────────────────────────────────────────
    def test_05_idempotencia_sin_duplicar(self):
        """Una segunda reversión no crea picking, move ni move line."""
        guia = self._sv_make_guia('P0R-RET-05')
        lot = self._sv_make_lot(guia, label='SV00000000604')
        receipt = self._sv_receipt(guia, lot, 40.3)
        self._unrelated_lot('OTHER-P0R-RET-05', 40.3)

        return_picking = self._reverse(guia, receipt)
        moves_before = return_picking.move_ids
        lines_before = return_picking.move_line_ids

        guia.action_force_cancel()  # segundo intento

        self.assertEqual(len(self._return_picking(receipt)), 1)
        self.assertEqual(return_picking.move_ids, moves_before)
        self.assertEqual(return_picking.move_line_ids, lines_before)
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(
            moves_before.origin_returned_move_id, receipt.move_ids)

    # ── T-P0R-RET-06 ──────────────────────────────────────────────────────
    def test_06_sin_saldo_no_crea_nada(self):
        """Sin saldo del lote SV: sin picking/move/move line y error claro."""
        guia = self._sv_make_guia('P0R-RET-06')
        lot = self._sv_make_lot(guia, label='SV00000000605')
        receipt = self._sv_receipt(guia, lot, 40.3)
        self._sv_outgoing(lot, 40.3)  # se vacía el saldo interno del lote SV
        lot.invalidate_recordset()
        moves_before = self.env['stock.move'].search_count([])

        with self.assertRaises(ValidationError) as error:
            guia.action_force_cancel()
        self.assertIn(NO_BALANCE_MSG, str(error.exception))
        self.assertFalse(self._return_picking(receipt))
        self.assertEqual(self.env['stock.move'].search_count([]), moves_before)
        guia.invalidate_recordset()
        self.assertNotEqual(guia.state, 'cancelled')

    # ── T-P0R-RET-07 ──────────────────────────────────────────────────────
    def test_07_valorizacion_nativa_sin_duplicar(self):
        """El retorno pide reembolso nativo y no duplica capas de valoración."""
        guia = self._sv_make_guia('P0R-RET-07')
        lot = self._sv_make_lot(guia, label='SV00000000606')
        receipt = self._sv_receipt(guia, lot, 40.3)

        return_picking = self._reverse(guia, receipt)
        self.assertTrue(
            all(move.to_refund for move in return_picking.move_ids),
            'El retorno debe solicitar el reembolso de valoración nativo.')

        layer_model = self.env.get('stock.valuation.layer')
        if layer_model is None:
            self.skipTest('stock_account no disponible: sin valoración.')
        layers = layer_model.sudo().search([
            ('stock_move_id', 'in', return_picking.move_ids.ids)])
        self.assertLessEqual(
            len(layers), len(return_picking.move_ids),
            'No debe duplicarse la capa de valoración del retorno.')

    # ── T-P0R-RET-08 ──────────────────────────────────────────────────────
    def test_08_usuario_no_autorizado_no_eleva(self):
        """Sin grupo de stock no se ejecuta la ruta física ni con contexto."""
        guia = self._sv_make_guia('P0R-RET-08')
        lot = self._sv_make_lot(guia, label='SV00000000607')
        self._sv_receipt(guia, lot, 40.3)
        user = self.env['res.users'].create({
            'name': 'p0r_plain_08',
            'login': 'p0r_plain_08',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            guia.with_user(user).action_force_cancel()
        with self.assertRaises(AccessError):
            guia.with_user(user).with_context(
                force_validate=True, skip_immediate=True,
                immediate_transfer=True).action_force_cancel()

    # ── T-P0R-RET-09 ──────────────────────────────────────────────────────
    def test_09_transaccion_atomica_ante_fallo(self):
        """Ante fallo de validación no queda estado parcial ni auditoría."""
        guia = self._sv_make_guia('P0R-RET-09')
        lot = self._sv_make_lot(guia, label='SV00000000608')
        receipt = self._sv_receipt(guia, lot, 40.3)
        other = self._unrelated_lot('OTHER-P0R-RET-09', 40.3)
        ops_before = self.Operation.search_count([('lot_id', '=', lot.id)])
        # Sin saldo del lote SV: el guard previo bloquea ANTES de crear nada.
        self._sv_outgoing(lot, 40.3)

        with self.assertRaises(ValidationError):
            guia.action_force_cancel()

        self.assertFalse(self._return_picking(receipt))
        self.assertEqual(
            self.Operation.search_count([('lot_id', '=', lot.id)]),
            ops_before)
        receipt.invalidate_recordset()
        self.assertEqual(receipt.state, 'done')
        other.invalidate_recordset()
        self.assertAlmostEqual(
            self._internal_available(other), 40.3, places=3)
        guia.invalidate_recordset()
        self.assertNotEqual(guia.state, 'cancelled')

    # ── T-P0R-RET-10 ──────────────────────────────────────────────────────
    def test_10_sin_segunda_puerta_de_ingreso(self):
        """La reversión no abre un segundo ingreso ni toca Intake."""
        guia = self._sv_make_guia('P0R-RET-10')
        lot = self._sv_make_lot(guia, label='SV00000000609')
        receipt = self._sv_receipt(guia, lot, 40.3)

        return_picking = self._reverse(guia, receipt)

        # El retorno es una SALIDA física (interno → proveedor), nunca un
        # segundo tipo de recepción.
        self.assertNotEqual(return_picking.picking_type_id.code, 'incoming')
        # No se crea otro picking con el origen de la guía (única puerta de
        # ingreso: la recepción original).
        self.assertEqual(self.env['stock.picking'].search_count([
            ('origin', '=', guia.name)]), 1)

    # ── T-P0R-FINAL-01 ────────────────────────────────────────────────────
    def test_11_helper_lote_ajeno_devuelve_recordset(self):
        """`_unrelated_lot()` devuelve un `stock.lot` válido y no toca el SV."""
        guia = self._sv_make_guia('P0R-RET-11')
        lot = self._sv_make_lot(guia, label='SV00000000610')
        other = self._unrelated_lot('OTHER-P0R-RET-11', 12.5)

        self.assertTrue(other, 'El helper debe devolver un recordset truthy')
        self.assertIsInstance(other, type(self.StockLot))
        self.assertEqual(other._name, 'stock.lot')
        self.assertNotEqual(other, lot)
        # Permite invalidar caché (era el fallo original F-P0R-G).
        other.invalidate_recordset()
        self.assertEqual(other.product_id, self.product)
        self.assertEqual(other.company_id, self.company)
        self.assertAlmostEqual(self._internal_available(other), 12.5, places=3)
        # El lote SV no se altera.
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.volumen_m3, 40.300, places=3)
