# -*- coding: utf-8 -*-
"""Pruebas de permisos de acceso ir.model.access.csv (H0-A) en madenat_lumber_core."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'security', 'h0')
class TestH0SecurityPermissionsCore(TransactionCase):
    """Verificación de acceso por mínimo privilegio para modelos y asistentes H0-A."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_oper = cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        cls.group_audit = cls.env.ref('madenat_lumber_core.group_madenat_auditoria')
        cls.group_cont = cls.env.ref('madenat_lumber_core.group_madenat_contabilidad')
        cls.group_ger = cls.env.ref('madenat_lumber_core.group_madenat_gerencia')

        cls.user_cont = cls.env['res.users'].create({
            'name': 'H0 Contabilidad',
            'login': 'h0_cont_user',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_cont.id])],
        })

        cls.user_oper = cls.env['res.users'].create({
            'name': 'H0 Operaciones',
            'login': 'h0_oper_user',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_oper.id])],
        })

        cls.user_restricted = cls.env['res.users'].create({
            'name': 'H0 Restringido',
            'login': 'h0_restricted_user',
            'groups_id': [(6, 0, [cls.group_user.id])],
        })

    def test_madenat_period_close_access(self):
        """Usuario Contabilidad puede abrir wizard; usuario restringido recibe AccessError."""
        wiz = self.env['madenat.period.close'].with_user(self.user_cont).create({
            'confirm': False,
        })
        self.assertTrue(wiz)

        with self.assertRaises(AccessError):
            self.env['madenat.period.close'].with_user(self.user_restricted).create({
                'confirm': False,
            })

    def test_madenat_reception_parser_access(self):
        """Usuario Operaciones tiene permiso de acceso al parser; usuario restringido no."""
        # Parser es AbstractModel/Dispatcher con ACL formal
        self.env['madenat.reception.parser'].with_user(self.user_oper).check_access('read')

        with self.assertRaises(AccessError):
            self.env['madenat.reception.parser'].with_user(self.user_restricted).check_access('write')
