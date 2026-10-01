# -*- coding: utf-8 -*-
"""Programa SV — ledger append-only `madenat.sv.operation`."""

from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvOperationLedger(SvTestCommon, TransactionCase):
    """Historial SV: firma, chatter y protección append-only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def _rename_via_operation(self, lot, label, reason='Corrección de tipeo'):
        operation = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rename',
            'new_label': label,
            'reason': reason,
        })
        operation.action_apply()
        return operation

    def test_01_rename_genera_evento_firmado(self):
        guia = self._sv_make_guia('SV-LEDGER-01')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        operation = self._rename_via_operation(lot, 'SV00000000092')

        self.assertEqual(operation.state, 'applied')
        self.assertEqual(operation.prior_label, 'SV00000000091')
        self.assertEqual(operation.new_label, 'SV00000000092')
        self.assertTrue(operation.audit_hash)
        self.assertTrue(operation.snapshot_json)
        self.assertEqual(operation.executed_by_id, self.env.user)
        self.assertTrue(operation.execution_date)
        self.assertEqual(lot.name, 'SV00000000092')
        # Trazabilidad en el chatter del lote y de la Guía.
        self.assertTrue(lot.message_ids)
        self.assertTrue(guia.message_ids)
        # Espejo en la bitácora de auditoría MADENAT.
        audit = self.env['madenat.audit.log'].search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'sv_operation'),
        ])
        self.assertTrue(audit)

    def test_02_operacion_aplicada_no_se_edita_ni_elimina(self):
        guia = self._sv_make_guia('SV-LEDGER-02')
        lot = self._sv_make_lot(guia, label='SV00000000093')
        operation = self._sv_rebaja(lot, 5.0)

        with self.assertRaises(ValidationError):
            operation.write({'reason': 'Intento de cambio posterior'})
        with self.assertRaises(ValidationError):
            operation.write({'rebaja_volume_m3': 1.0})
        with self.assertRaises(ValidationError):
            operation.unlink()
        # El borrador sí puede corregirse.
        draft = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Borrador',
        })
        draft.write({'reason': 'Borrador corregido'})
        draft.unlink()

    def test_03_transiciones_de_estado_controladas(self):
        guia = self._sv_make_guia('SV-LEDGER-03')
        lot = self._sv_make_lot(guia, label='SV00000000094')
        operation = self._sv_rebaja(lot, 2.0)

        with self.assertRaises(ValidationError):
            operation.write({'state': 'draft'})
        with self.assertRaises(ValidationError):
            operation.write({'state': 'rejected'})

        draft = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Rechazable',
        })
        draft.action_reject()
        self.assertEqual(draft.state, 'rejected')
        with self.assertRaises(UserError):
            draft.action_apply()

    def test_04_motivo_obligatorio_y_lote_sv_exigido(self):
        guia = self._sv_make_guia('SV-LEDGER-04')
        lot = self._sv_make_lot(guia, label='SV00000000095')
        with self.assertRaises(ValidationError):
            self.Operation.create({
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 1.0,
                'reason': '   ',
            })
        no_sv_lot = self.StockLot.create({
            'name': 'NO-SV-LOT-01',
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.Operation.create({
                'lot_id': no_sv_lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 1.0,
                'reason': 'Lote no SV',
            })

    def test_05_historial_multiple_cronologico(self):
        guia = self._sv_make_guia('SV-LEDGER-05')
        lot = self._sv_make_lot(guia, label='SV00000000096')
        self._sv_regularize(lot, 41.0)
        rebaja = self._sv_rebaja(lot, 3.0)
        reverse = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja_reverse',
            'origin_operation_id': rebaja.id,
            'reason': 'Reversa de prueba',
        })
        reverse.action_apply()

        history = lot.sv_operation_ids
        self.assertEqual(len(history), 3)
        self.assertEqual(lot.sv_operation_count, 3)
        rebaja.invalidate_recordset()
        self.assertEqual(rebaja.state, 'reversed')
        self.assertEqual(rebaja.reversed_operation_id, reverse)
