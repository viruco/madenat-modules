# -*- coding: utf-8 -*-
"""Reversa SV visible en la UI (Fase 2, AD-80).

Contrato verificado:

1. El botón «Reversar rebaja» del ledger (`madenat.sv.operation`) es visible
   SOLO para una rebaja aplicada y aún no reversada; la vista no es una
   guarda: la segunda reversa la bloquea el ledger.
2. El formulario de la Guía expone las acciones SV aprobadas
   (modificar etiqueta, regularizar volumen, rebajar etiqueta e historial)
   condicionadas a la existencia de la etiqueta SV (`volume_lot_id`).
3. La reversa crea una operación `rebaja_reverse` ligada a la original y
   ningún dominio de UI vuelve a ofrecer la rebaja como reversible.

Datos aislados (TransactionCase + SvTestCommon): no se toca la Guía 4495589 ni
la etiqueta SV00000000008.
"""

from lxml import etree

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

REVERSE_BUTTON = "action_open_reverse_wizard"
REVERSE_INVISIBLE = (
    "action_type != 'rebaja' or state != 'applied' or reversed_operation_id")


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvReverseUi(SvTestCommon, TransactionCase):
    """Visibilidad y vínculo de la reversa de rebaja SV."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    # ── 1. Arquitectura del ledger ────────────────────────────────────────
    def test_01_boton_reversa_solo_en_rebaja_aplicada_reversible(self):
        """El ledger expone la reversa con la condición exacta."""
        arch = self.env.ref(
            'madenat_lumber_core.view_madenat_sv_operation_list').arch
        root = etree.fromstring(arch)
        buttons = root.xpath("//button[@name='%s']" % REVERSE_BUTTON)
        self.assertEqual(len(buttons), 1, 'Falta el botón de reversa')
        button = buttons[0]
        self.assertEqual(button.get('type'), 'object')
        self.assertEqual(button.get('string'), 'Reversar rebaja')
        self.assertEqual(button.get('invisible'), REVERSE_INVISIBLE)
        # La lista del ledger sigue siendo de solo lectura del historial.
        self.assertEqual(root.get('create'), 'false')

    # ── 2. Acciones SV en el formulario de la Guía ────────────────────────
    def test_02_acciones_sv_en_formulario_de_guia(self):
        """La Guía expone las acciones SV condicionadas a la etiqueta SV."""
        arch = self.env.ref(
            'madenat_lumber_core.view_madenat_guia_processing_form_sv').arch
        root = etree.fromstring(arch)
        # Acciones de MUTACIÓN: exigen lote SV real y guía por Volumen.
        for name in ('action_sv_rename', 'action_sv_regularize_volume',
                     'action_sv_rebaja'):
            nodes = root.xpath("//button[@name='%s']" % name)
            self.assertEqual(len(nodes), 1, 'Falta el botón %s' % name)
            self.assertEqual(nodes[0].get('type'), 'object')
            invisible = nodes[0].get('invisible') or ''
            self.assertIn(
                "not volume_lot_id", invisible,
                'La acción %s debe depender de la etiqueta SV' % name)
            self.assertIn("tipo_recepcion != 'granel'", invisible)
        # El historial SV es una consulta: conserva su comportamiento previo
        # (visible con el grupo funcional; sin mutación).
        history = root.xpath("//button[@name='action_open_sv_history']")
        self.assertEqual(len(history), 1, 'Falta el historial SV')
        self.assertEqual(history[0].get('type'), 'object')
        self.assertFalse(
            history[0].get('invisible'),
            'El historial SV conserva su visibilidad previa')

    # ── 3. Reversa funcional: crea el evento ligado ───────────────────────
    def test_03_reversa_crea_evento_ligado_y_no_se_duplica(self):
        """La reversa liga la rebaja; una segunda queda bloqueada."""
        guia = self._sv_make_guia('SV-UI-REV-01')
        lot = self._sv_make_lot(guia, label='SV00000000351')
        rebaja = self._sv_rebaja(lot, 12.0)
        self.assertEqual(rebaja.state, 'applied')
        self.assertFalse(rebaja.reversed_operation_id)

        action = rebaja.action_open_reverse_wizard()
        self.assertEqual(
            action['res_model'], 'madenat.sv.rebaja.reverse.wizard')
        self.assertEqual(
            action['context']['default_origin_operation_id'], rebaja.id)
        self.assertEqual(action['context']['default_lot_id'], lot.id)

        reverse = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Reversa de prueba de UI',
        })
        reverse.action_submit()

        rebaja.invalidate_recordset()
        self.assertEqual(rebaja.state, 'reversed')
        self.assertTrue(rebaja.reversed_operation_id)
        self.assertEqual(rebaja.reversed_operation_id.action_type,
                         'rebaja_reverse')
        # El dominio de la UI ya no ofrece la rebaja como reversible.
        self.assertFalse(self.Operation.search([
            ('lot_id', '=', lot.id),
            ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied'),
            ('reversed_operation_id', '=', False),
        ]))
        # La segunda reversa la bloquea el ledger, no la vista.
        second = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Segunda reversa no permitida',
        })
        with self.assertRaises(ValidationError):
            second.action_submit()
