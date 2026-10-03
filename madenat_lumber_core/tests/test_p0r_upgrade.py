# -*- coding: utf-8 -*-
"""P0-R — Upgrade y calidad de la fundación Core/SV.

Cubre T-P0R-UPG-01 (recompute de campos `store=True` sin tocar inventario) y
T-P0R-UPG-02 (secuencias SV/SVO íntegras, con XML ID y sin colisión).
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

STORED_EVIDENCE_FIELDS = (
    'sum_vol_documental_m3',
    'diff_pdf_packing_m3',
    'diff_packing_lineas_m3',
    'documental_conciliation_state',
)
STOCK_MODELS = (
    'stock.picking', 'stock.move', 'stock.move.line', 'stock.quant',
    'stock.lot',
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'sv', 'p0r')
class TestP0rUpgrade(SvTestCommon, TransactionCase):
    """Recompute documental y secuencias tras instalar/actualizar."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def _stock_snapshot(self):
        return {
            model: self.env[model].sudo().search_count([])
            for model in STOCK_MODELS
        }

    # ── T-P0R-UPG-01 ──────────────────────────────────────────────────────
    def test_01_recompute_store_sin_tocar_stock(self):
        """Los campos store=True recomputan sobre guías sin alterar stock."""
        guia = self._sv_make_guia('P0R-UPG-01')
        guia.write({
            'vol_comercial_pdf': 40.315,
            'packing_volume_declared_m3': 40.315,
        })
        before = self._stock_snapshot()

        # Simula el recompute de upgrade sobre el registro existente.
        for fname in STORED_EVIDENCE_FIELDS:
            field = self.env['madenat.guia.processing']._fields[fname]
            self.env.add_to_compute(field, guia)
        guia.flush_recordset()

        self.assertEqual(
            before, self._stock_snapshot(),
            'El recompute documental no debe modificar inventario')

        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.diff_pdf_packing_m3, 0.0, places=3)
        self.assertEqual(guia.documental_conciliation_state, 'partial')

        guia.write({'packing_volume_declared_m3': 40.0})
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.diff_pdf_packing_m3, 0.315, places=3)
        self.assertEqual(self._stock_snapshot(), before)

    # ── T-P0R-UPG-02 ──────────────────────────────────────────────────────
    def test_02_secuencias_sv_y_svo_integras(self):
        """SVO (ledger) y SV (lote) existen, no colisionan y son únicas."""
        seq_model = self.env['ir.sequence']
        seq_op = self.env.ref('madenat_lumber_core.seq_madenat_sv_operation')
        seq_lot = self.env.ref('madenat_lumber_core.seq_madenat_volume_lot')

        self.assertEqual(seq_op.code, 'madenat.sv.operation')
        self.assertEqual(seq_lot.code, 'madenat.volume.lot')
        self.assertEqual(seq_op.prefix, 'SVO')
        self.assertEqual(seq_lot.prefix, 'SV')
        # Compañía según definición aprobada: identidad global (sin compañía).
        self.assertFalse(seq_op.company_id)
        self.assertFalse(seq_lot.company_id)
        # Sin colisión de códigos.
        self.assertEqual(seq_model.search_count(
            [('code', '=', 'madenat.sv.operation')]), 1)
        self.assertEqual(seq_model.search_count(
            [('code', '=', 'madenat.volume.lot')]), 1)
        # Generan valores únicos.
        op_a = seq_model.next_by_code('madenat.sv.operation')
        op_b = seq_model.next_by_code('madenat.sv.operation')
        lot_a = seq_model.next_by_code('madenat.volume.lot')
        lot_b = seq_model.next_by_code('madenat.volume.lot')
        self.assertNotEqual(op_a, op_b)
        self.assertNotEqual(lot_a, lot_b)
        self.assertTrue(op_a.startswith('SVO'))
        self.assertTrue(lot_a.startswith('SV'))
