# -*- coding: utf-8 -*-
"""Pruebas de permisos de acceso ir.model.access.csv (H0-A) en madenat_lumber_logistics."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics', 'security', 'h0')
class TestH0SecurityPermissionsLogistics(TransactionCase):
    """Verificación de acceso por mínimo privilegio para modelos y asistentes H0-A."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_oper = cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        cls.group_ger = cls.env.ref('madenat_lumber_core.group_madenat_gerencia')

        cls.user_ger = cls.env['res.users'].create({
            'name': 'H0 Gerencia Logística',
            'login': 'h0_ger_user_log',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_ger.id])],
        })

        cls.user_oper = cls.env['res.users'].create({
            'name': 'H0 Operaciones Logística',
            'login': 'h0_oper_user_log',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_oper.id])],
        })

        cls.user_restricted = cls.env['res.users'].create({
            'name': 'H0 Restringido Logística',
            'login': 'h0_restricted_user_log',
            'groups_id': [(6, 0, [cls.group_user.id])],
        })

        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Test H0'})
        cls.shipment = cls.env['lumber.export.shipment'].create({
            'name': 'EXP-H0-001',
            'customer_id': cls.partner.id,
        })

    def test_lumber_consolidation_import_wizard_access(self):
        """Usuario Operaciones puede abrir wizard; usuario restringido recibe AccessError."""
        wiz = self.env['lumber.consolidation.import.wizard'].with_user(self.user_oper).create({
            'shipment_id': self.shipment.id,
            'file_data': b'dummy_content',
            'file_name': 'test.xlsx',
        })
        self.assertTrue(wiz)

        with self.assertRaises(AccessError):
            self.env['lumber.consolidation.import.wizard'].with_user(self.user_restricted).create({
                'shipment_id': self.shipment.id,
                'file_data': b'dummy_content',
                'file_name': 'test.xlsx',
            })

    def test_lumber_b01_regularization_wizard_access(self):
        """Gerencia puede crear wizard B-01; Operaciones (solo lectura) recibe AccessError en creación."""
        wiz = self.env['lumber.b01.regularization.wizard'].with_user(self.user_ger).create({
            'shipment_id': self.shipment.id,
            'regularization_reason': 'Motivo justificado de más de 20 caracteres para regularización.',
            'approval_reason': 'Aprobación formal por parte de Gerencia para regularización.',
        })
        self.assertTrue(wiz)

        with self.assertRaises(AccessError):
            self.env['lumber.b01.regularization.wizard'].with_user(self.user_oper).create({
                'shipment_id': self.shipment.id,
                'regularization_reason': 'Motivo justificado de más de 20 caracteres para regularización.',
                'approval_reason': 'Aprobación formal por parte de Gerencia para regularización.',
            })
