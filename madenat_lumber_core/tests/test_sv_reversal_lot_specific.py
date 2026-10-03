# -*- coding: utf-8 -*-
"""Programa SV — reversa/cancelación específica por lote SV (regresión).

Reproduce el defecto histórico (Guía 4495589: dos devoluciones por una sola
recepción, la segunda consumiendo quants de otros lotes) con datos AISLADOS.
No se usa ni modifica la Guía 4495589, el lote SV00000000008 (id 3772) ni los
movimientos históricos.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

NO_BALANCE_MSG = ('No existe saldo disponible del lote SV asociado para '
                  'realizar la reversa.')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvReversalLotSpecific(SvTestCommon, TransactionCase):
    """La reversa de Volumen devuelve SOLO el lote SV de la Guía."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def _unrelated_lot_with_stock(self, label, quantity):
        """Lote no-SV con stock en la misma ubicación interna (señuelo)."""
        other = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        self._sv_add_quant(other, quantity)
        return other

    def test_01_cancelacion_devuelve_solo_el_lote_sv(self):
        guia = self._sv_make_guia('SV-REV-01', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000101', volume=40.3)
        receipt = self._sv_receipt(guia, lot, 40.3)
        other = self._unrelated_lot_with_stock('OTHER-LOT-REV-01', 40.3)

        guia.action_force_cancel()

        returns = self.env['stock.picking'].search([
            ('origin', '=', 'Return of %s' % receipt.name)])
        self.assertEqual(
            len(returns), 1,
            'Debe existir exactamente UNA devolución para la recepción SV')
        return_lines = returns.move_line_ids
        self.assertEqual(len(return_lines), 1)
        self.assertEqual(return_lines.lot_id, lot)
        self.assertAlmostEqual(return_lines.quantity, 40.3, places=3)
        self.assertAlmostEqual(
            sum(lot.quant_ids.mapped('quantity')), 0.0, places=3)
        # El lote ajeno permanece intacto (defecto histórico corregido).
        other.invalidate_recordset()
        self.assertAlmostEqual(
            sum(other.quant_ids.mapped('quantity')), 40.3, places=3)
        self.assertEqual(
            self.env['stock.move'].search_count([
                ('origin_returned_move_id', '=', receipt.move_ids.id),
                ('state', '=', 'done')]), 1)
        self.assertEqual(guia.state, 'cancelled')
        lot.invalidate_recordset()
        self.assertEqual(lot.technical_validation, 'rejected')

    def test_02_reversa_idempotente_sin_segunda_devolucion(self):
        guia = self._sv_make_guia('SV-REV-02', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000102', volume=40.3)
        receipt = self._sv_receipt(guia, lot, 40.3)
        self._unrelated_lot_with_stock('OTHER-LOT-REV-02', 40.3)

        guia.action_force_cancel()
        guia.action_force_cancel()  # segundo intento

        returns = self.env['stock.picking'].search([
            ('origin', '=', 'Return of %s' % receipt.name)])
        self.assertEqual(
            len(returns), 1,
            'Un segundo intento no puede duplicar la devolución')
        self.assertEqual(
            self.env['stock.move'].search_count([
                ('origin_returned_move_id', 'in', receipt.move_ids.ids),
                ('state', '!=', 'cancel')]), 1)

    def test_03_sin_saldo_sv_se_bloquea_con_mensaje_exacto(self):
        guia = self._sv_make_guia('SV-REV-03', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000103', volume=40.3)
        receipt = self._sv_receipt(guia, lot, 40.3)
        other = self._unrelated_lot_with_stock('OTHER-LOT-REV-03', 40.3)
        # Se vacía el saldo interno del lote SV.
        self._sv_outgoing(lot, 40.3)
        lot.invalidate_recordset()
        self.assertAlmostEqual(
            sum(lot.quant_ids.mapped('quantity')), 0.0, places=3)

        with self.assertRaises(ValidationError) as error:
            guia.action_force_cancel()
        self.assertIn(NO_BALANCE_MSG, str(error.exception))
        self.assertFalse(self.env['stock.picking'].search([
            ('origin', '=', 'Return of %s' % receipt.name)]))
        # Ningún lote ajeno fue consumido y la guía sigue sin cancelar.
        other.invalidate_recordset()
        self.assertAlmostEqual(
            sum(other.quant_ids.mapped('quantity')), 40.3, places=3)
        guia.invalidate_recordset()
        self.assertNotEqual(guia.state, 'cancelled')
