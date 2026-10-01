# -*- coding: utf-8 -*-
"""Programa SV — modificación controlada de etiqueta SV y alias histórico."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvRename(SvTestCommon, TransactionCase):
    """Rename: formato, unicidad, alias no reutilizable y guardas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def _wizard(self, lot, new_label, reason='Corrección de digitación'):
        return self.env['madenat.sv.rename.wizard'].create({
            'lot_id': lot.id,
            'new_label': new_label,
            'reason': reason,
        })

    def test_01_rename_valido_conserva_alias_y_no_toca_nada_mas(self):
        guia = self._sv_make_guia('SV-REN-01')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        seq = self.env['ir.sequence'].search(
            [('code', '=', 'madenat.volume.lot')], limit=1)
        next_before = seq.number_next

        self._wizard(lot, '  sv00000000097  ').action_submit()

        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000097')
        operation = self.Operation.search([('lot_id', '=', lot.id)])
        self.assertEqual(len(operation), 1)
        self.assertEqual(operation.action_type, 'rename')
        self.assertEqual(operation.prior_label, 'SV00000000091')
        self.assertEqual(operation.new_label, 'SV00000000097')
        self.assertEqual(operation.state, 'applied')
        # Sin cambios colaterales.
        self.assertAlmostEqual(lot.volume_purchase_m3, 40.300, places=3)
        self.assertAlmostEqual(lot.volumen_m3, 40.300, places=3)
        self.assertEqual(lot.piezas, 1)
        self.assertEqual(lot.volume_source_guia_id, guia)
        self.assertEqual(self.StockLot.search_count([
            ('volume_source_guia_id', '=', guia.id)]), 1)
        # No se consume ni consulta la secuencia de identidad SV.
        seq.invalidate_recordset()
        self.assertEqual(seq.number_next, next_before)

    def test_02_alias_historico_no_reutilizable(self):
        guia = self._sv_make_guia('SV-REN-02')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        self._wizard(lot, 'SV00000000098').action_submit()
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000098')

        with self.assertRaises(ValidationError):
            self._wizard(lot, 'SV00000000091').action_submit()

    def test_03_etiqueta_actual_de_otro_lote_no_reutilizable(self):
        guia_a = self._sv_make_guia('SV-REN-03A')
        guia_b = self._sv_make_guia('SV-REN-03B')
        lot_a = self._sv_make_lot(guia_a, label='SV00000000091')
        self._sv_make_lot(guia_b, label='SV00000000092')

        with self.assertRaises(ValidationError):
            self._wizard(lot_a, 'SV00000000092').action_submit()

    def test_04_formatos_invalidos_y_motivo_obligatorio(self):
        guia = self._sv_make_guia('SV-REN-04')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        for invalid in ('SV8', 'SV0008', 'LV00000000008', 'SV0000000000A',
                        'SV 00000000008'):
            with self.assertRaises(ValidationError):
                self._wizard(lot, invalid).action_submit()
        with self.assertRaises(ValidationError):
            self._wizard(lot, 'SV00000000091').action_submit()
        # Sin motivo no se puede construir el asistente.
        with self.assertRaises(Exception):
            self.env['madenat.sv.rename.wizard'].create({
                'lot_id': lot.id,
                'new_label': 'SV00000000099',
            })

    def test_05_escritura_directa_bloqueada(self):
        guia = self._sv_make_guia('SV-REN-05')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        with self.assertRaises(ValidationError):
            lot.write({'name': 'SV00000000100'})
        with self.assertRaises(ValidationError):
            lot.write({'volumen_m3': 10.0})
        with self.assertRaises(ValidationError):
            lot.write({'piezas': 5})
        # La identidad documental sigue inmutable.
        with self.assertRaises(ValidationError):
            lot.write({'volume_source_guia_id': False})

    def test_06_lote_sv_con_historial_no_se_elimina(self):
        guia = self._sv_make_guia('SV-REN-06')
        lot = self._sv_make_lot(guia, label='SV00000000091')
        self._wizard(lot, 'SV00000000101').action_submit()
        with self.assertRaises(ValidationError):
            lot.unlink()
