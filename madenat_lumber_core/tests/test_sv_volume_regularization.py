# -*- coding: utf-8 -*-
"""Programa SV — regularización documental de volumen (sin inventario)."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvVolumeRegularization(SvTestCommon, TransactionCase):
    """Regularización: evidencia, límites y cero impacto en inventario."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def test_01_regularizacion_hacia_abajo_registra_historial(self):
        guia = self._sv_make_guia('SV-REG-01')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        self._sv_add_quant(lot, 40.300)
        quant_qty = sum(lot.quant_ids.mapped('quantity'))
        move_count = self.env['stock.move'].search_count([])

        operation = self.env['madenat.sv.volume.regularize.wizard'].create({
            'lot_id': lot.id,
            'new_volume_m3': 40.315,
            'reason': 'Iguala al volumen oficial de la Guía PDF',
            'evidence_reference': 'PDF-4495589-TEST',
        }).action_submit()

        lot.invalidate_recordset()
        op = self.Operation.search([('lot_id', '=', lot.id)])
        self.assertEqual(len(op), 1)
        self.assertEqual(op.action_type, 'regularize_volume')
        self.assertEqual(op.state, 'applied')
        self.assertAlmostEqual(op.prior_volume_m3, 40.300, places=3)
        self.assertAlmostEqual(op.new_volume_m3, 40.315, places=3)
        self.assertAlmostEqual(op.volume_diff_m3, 0.015, places=3)
        self.assertAlmostEqual(
            lot.sv_regularized_baseline_m3, 40.315, places=3)
        self.assertAlmostEqual(lot.sv_available_m3, 40.315, places=3)
        # Decisión 1: la regularización NO toca inventario ni campos históricos.
        self.assertAlmostEqual(lot.volume_purchase_m3, 40.300, places=3)
        self.assertAlmostEqual(lot.volumen_m3, 40.300, places=3)
        self.assertAlmostEqual(
            sum(lot.quant_ids.mapped('quantity')), quant_qty, places=3)
        self.assertEqual(
            self.env['stock.move'].search_count([]), move_count)
        self.assertIsInstance(operation, dict)

    def test_02_evidencia_y_motivo_obligatorios(self):
        guia = self._sv_make_guia('SV-REG-02')
        lot = self._sv_make_lot(guia, label='SV00000000092')
        wizard = self.env['madenat.sv.volume.regularize.wizard'].create({
            'lot_id': lot.id,
            'new_volume_m3': 30.0,
            'reason': 'Sin respaldo',
        })
        with self.assertRaises(ValidationError):
            wizard.action_submit()
        self.assertFalse(self.Operation.search([('lot_id', '=', lot.id)]))

    def test_03_regularizacion_bajo_rebajado_bloqueada(self):
        guia = self._sv_make_guia('SV-REG-03')
        lot = self._sv_make_lot(guia, label='SV00000000093')
        self._sv_rebaja(lot, 30.0)
        lot.invalidate_recordset()
        baseline_before = lot.sv_regularized_baseline_m3

        operation = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 20.0,
            'reason': 'Intento bajo el rebajado',
            'evidence_reference': 'X',
        })
        with self.assertRaises(ValidationError):
            operation.action_apply()
        lot.invalidate_recordset()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'draft')
        self.assertAlmostEqual(
            lot.sv_regularized_baseline_m3, baseline_before, places=3)
        self.assertAlmostEqual(lot.sv_available_m3, 10.300, places=3)

    def test_04_volumen_no_positivo_bloqueado(self):
        guia = self._sv_make_guia('SV-REG-04')
        lot = self._sv_make_lot(guia, label='SV00000000094')
        zero = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 0.0,
            'reason': 'Valor inválido',
            'evidence_reference': 'X',
        })
        with self.assertRaises(ValidationError):
            zero.action_apply()
        # Negativo: bloqueado en el alta por la validación funcional.
        with self.assertRaises(ValidationError):
            self.Operation.create({
                'lot_id': lot.id,
                'action_type': 'regularize_volume',
                'new_volume_m3': -5.0,
                'reason': 'Valor inválido',
                'evidence_reference': 'X',
            })

    def test_05_escalamiento_auditoria_solo_al_alza(self):
        guia = self._sv_make_guia('SV-REG-05')
        lot = self._sv_make_lot(guia, label='SV00000000095')
        lower = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 39.0,
            'reason': 'Ajuste a la baja',
            'evidence_reference': 'X',
            'company_id': self.company.id,
        })
        self.assertNotIn(
            'auditoria', lower._sv_required_approval_groups())
        upper = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 45.0,
            'reason': 'Ajuste al alza',
            'evidence_reference': 'X',
            'company_id': self.company.id,
        })
        self.assertIn('auditoria', upper._sv_required_approval_groups())

    def test_06_regularizacion_no_crea_pickings_ni_costos(self):
        guia = self._sv_make_guia('SV-REG-06')
        lot = self._sv_make_lot(guia, label='SV00000000096')
        picking_count = self.env['stock.picking'].search_count([])
        cost_count = self.env['stock.lot.cost.line'].search_count([])
        self._sv_regularize(lot, 38.5)
        lot.invalidate_recordset()
        self.assertAlmostEqual(
            lot.sv_regularized_baseline_m3, 38.5, places=3)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), picking_count)
        self.assertEqual(
            self.env['stock.lot.cost.line'].search_count([]), cost_count)
