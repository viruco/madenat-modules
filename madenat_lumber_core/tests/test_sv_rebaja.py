# -*- coding: utf-8 -*-
"""Programa SV — rebaja, reversa, saldo, concurrencia y piezas."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvRebaja(SvTestCommon, TransactionCase):
    """Rebaja/reversa: saldo no negativo, historial y piezas documentales."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def test_01_rebaja_valida_actualiza_saldo_y_ledger(self):
        guia = self._sv_make_guia('SV-REB-01')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        operation = self._sv_rebaja(
            lot, 25.0, destination_reference='Contenedor TEST-01')

        lot.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')
        self.assertAlmostEqual(operation.prior_volume_m3, 40.300, places=3)
        self.assertAlmostEqual(operation.new_volume_m3, 15.300, places=3)
        self.assertAlmostEqual(operation.rebaja_volume_m3, 25.0, places=3)
        self.assertAlmostEqual(operation.volume_diff_m3, -25.0, places=3)
        self.assertAlmostEqual(lot.sv_rebajado_m3, 25.0, places=3)
        self.assertAlmostEqual(lot.sv_available_m3, 15.300, places=3)
        self.assertEqual(operation.destination_reference, 'Contenedor TEST-01')
        self.assertEqual(operation.executed_by_id, self.env.user)

    def test_02_rebajas_invalidas_sin_operacion(self):
        guia = self._sv_make_guia('SV-REB-02')
        lot = self._sv_make_lot(guia, label='SV00000000092')
        for value in (0.0, 40.301):
            operation = self.Operation.create({
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': value,
                'reason': 'Rebaja inválida',
            })
            with self.assertRaises(ValidationError):
                operation.action_apply()
            operation.invalidate_recordset()
            self.assertEqual(operation.state, 'draft')
        # Valor negativo: la validación funcional lo bloquea ya en el alta.
        with self.assertRaises(ValidationError):
            self.Operation.create({
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': -3.0,
                'reason': 'Rebaja negativa',
            })
        # Sin motivo no se crea la operación.
        with self.assertRaises(Exception):
            self.Operation.create({
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 1.0,
            })
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 40.300, places=3)

    def test_03_reversa_restaura_saldo_y_no_borra_original(self):
        guia = self._sv_make_guia('SV-REB-03')
        lot = self._sv_make_lot(guia, label='SV00000000093')
        rebaja = self._sv_rebaja(lot, 12.0)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 28.300, places=3)

        reverse = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Devolución del volumen asignado',
        })
        reverse.action_submit()

        lot.invalidate_recordset()
        rebaja.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 40.300, places=3)
        self.assertAlmostEqual(lot.sv_rebajado_m3, 0.0, places=3)
        self.assertEqual(rebaja.state, 'reversed')
        self.assertTrue(rebaja.reversed_operation_id)
        # La rebaja original conserva sus datos.
        self.assertAlmostEqual(rebaja.rebaja_volume_m3, 12.0, places=3)
        self.assertEqual(rebaja.reason, 'Rebaja de prueba')

    def test_04_segunda_reversa_bloqueada(self):
        guia = self._sv_make_guia('SV-REB-04')
        lot = self._sv_make_lot(guia, label='SV00000000094')
        rebaja = self._sv_rebaja(lot, 5.0)
        first = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Primera reversa',
        })
        first.action_submit()
        second = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Segunda reversa',
        })
        with self.assertRaises(ValidationError):
            second.action_submit()

    def test_05_sobreconsumo_bloqueado_y_saldo_final(self):
        guia = self._sv_make_guia('SV-REB-05', pdf_volume=40.315)
        lot = self._sv_make_lot(
            guia, label='SV00000000095', volume=40.315)
        rebaja_a = self._sv_rebaja(lot, 25.000)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 15.315, places=3)
        self.assertEqual(rebaja_a.state, 'applied')

        stamp = lot.sv_available_m3  # valor previo (no debe confiarse)
        rebaja_b = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 20.000,
            'reason': 'Rebaja B excedida',
        })
        with self.assertRaises(ValidationError):
            rebaja_b.action_apply()

        lot.invalidate_recordset()
        rebaja_b.invalidate_recordset()
        self.assertEqual(rebaja_b.state, 'draft')
        self.assertAlmostEqual(lot.sv_available_m3, 15.315, places=3)
        self.assertAlmostEqual(lot.sv_rebajado_m3, 25.000, places=3)
        self.assertGreaterEqual(lot.sv_available_m3, 0.0)
        self.assertAlmostEqual(stamp, 15.315, places=3)

    def test_06_bloqueo_transaccional_del_lote_sv(self):
        guia = self._sv_make_guia('SV-REB-06')
        lot = self._sv_make_lot(guia, label='SV00000000096')
        lot._lock_sv_lot_for_operation()
        query = self.env.cr.query or b''
        if isinstance(query, bytes):
            query = query.decode('utf-8', 'ignore')
        self.assertIn('FOR UPDATE', query.upper())
        # El saldo se recalcula después del bloqueo (nuevos eventos incluidos).
        self._sv_rebaja(lot, 10.0)
        balances = lot._lock_sv_lot_for_operation()._sv_locked_balance_values()
        self.assertAlmostEqual(balances['rebajado'], 10.0, places=3)
        self.assertAlmostEqual(balances['available'], 30.300, places=3)

    def test_07_saldo_cero_permitido_sin_borrar_etiqueta(self):
        guia = self._sv_make_guia('SV-REB-07')
        lot = self._sv_make_lot(guia, label='SV00000000097')
        operation = self._sv_rebaja(lot, 40.300)
        lot.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')
        self.assertAlmostEqual(lot.sv_available_m3, 0.0, places=3)
        self.assertTrue(lot.exists())
        self.assertEqual(self.StockLot.search_count([
            ('id', '=', lot.id)]), 1)

    def test_08_piezas_no_habilitadas_por_paquetes_ni_placeholder(self):
        guia = self._sv_make_guia(
            'SV-REB-08', declared_pieces=0,
            packing_package_count_declared=12)
        lot = self._sv_make_lot(guia, label='SV00000000098')
        self.assertEqual(lot.piezas, 1)  # placeholder técnico
        self.assertFalse(lot.sv_pieces_enabled)
        self.assertEqual(lot.sv_available_pieces, 0)
        operation = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'rebaja_pieces': 12,
            'reason': 'Intento de rebajar paquetes como piezas',
        })
        with self.assertRaises(ValidationError):
            operation.action_apply()

    def test_09_piezas_documentales_habilitadas_y_limitadas(self):
        guia = self._sv_make_guia('SV-REB-09', declared_pieces=100)
        lot = self._sv_make_lot(guia, label='SV00000000099')
        self.assertTrue(lot.sv_pieces_enabled)
        self.assertEqual(lot.sv_available_pieces, 100)

        self._sv_rebaja(lot, 10.0, rebaja_pieces=40)
        lot.invalidate_recordset()
        self.assertEqual(lot.sv_available_pieces, 60)

        operation = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 5.0,
            'rebaja_pieces': 70,
            'reason': 'Excede piezas documentales',
        })
        with self.assertRaises(ValidationError):
            operation.action_apply()
