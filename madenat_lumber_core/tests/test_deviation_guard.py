# -*- coding: utf-8 -*-
"""AD-88 — Mixin transversal «advertir, motivar, auditar».

Verifica que el helper común exista y que `madenat.audit.log` acepte el tipo de
acción `deviation`. La semántica hard/blando se prueba end-to-end en la suite
de logística (`test_rebaja_contenedor.TestRebajaContenedor`), donde hay un
modelo concreto que hereda el mixin.
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core')
class TestDeviationMixin(TransactionCase):
    """El mixin AD-88 existe y es consumible."""

    def test_01_mixin_existe_y_expone_helper(self):
        mixin = self.env['madenat.deviation.mixin']
        self.assertTrue(hasattr(mixin, '_guard_deviation'))
        self.assertTrue(hasattr(mixin, '_deviation_snapshot'))
        self.assertTrue(hasattr(mixin, 'DEVIATION_HARD_CODES'))

    def test_02_audit_log_acepta_deviation(self):
        log = self.env['madenat.audit.log'].sudo().create({
            'action_type': 'deviation',
            'description': 'Prueba de tipo deviation (AD-88).',
        })
        self.assertEqual(log.action_type, 'deviation')
