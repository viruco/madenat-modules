# -*- coding: utf-8 -*-
"""A2: la ventana 'Consolidación de Contenedores' usa estados reales.

El dominio previo `[('state', '=', 'draft')]` era inválido (lumber.container no
tiene estado 'draft'), por lo que la ventana aparecía siempre vacía.
"""

import ast

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestConsolidationActionDomain(TransactionCase):

    def test_domain_uses_real_states(self):
        action = self.env.ref(
            'madenat_lumber_logistics.action_lumber_container_consolidation')
        domain = action.domain or ''
        self.assertNotIn(
            "'draft'", domain,
            "lumber.container no tiene estado 'draft'")

        real_states = set(dict(
            self.env['lumber.container']._fields['state'].selection).keys())

        parsed = ast.literal_eval(domain)
        for leaf in parsed:
            if leaf[0] == 'state':
                if leaf[1] in ('in', 'not in'):
                    self.assertTrue(
                        set(leaf[2]).issubset(real_states),
                        "El dominio referencia estados inexistentes: %s" % (leaf[2],))
                else:
                    self.assertIn(
                        leaf[2], real_states,
                        "El dominio referencia un estado inexistente: %s" % (leaf[2],))
