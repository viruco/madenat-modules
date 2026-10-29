# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'madenat', 'shipping_security')
class TestShippingSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        group_user = cls.env.ref('base.group_user')
        group_ship_user = cls.env.ref('madenat_lumber_shipping_core.group_shipping_user')
        group_system = cls.env.ref('base.group_system')

        # 1. Usuario Shipping User (Solo Lectura)
        cls.user_shipping_read = cls.env['res.users'].create({
            'name': 'User Shipping Read Test',
            'login': 'user_ship_read_test',
            'email': 'ship_read@test.com',
            'groups_id': [(6, 0, [group_user.id, group_ship_user.id])],
        })

        # 2. Usuario No Access (estrictamente sin grupos de stock, shipping ni madenat)
        cls.user_no_access = cls.env['res.users'].create({
            'name': 'User No Access Test',
            'login': 'user_no_acc_test',
            'email': 'no_access@test.com',
            'groups_id': [(6, 0, [group_user.id])],
        })

        # 3. Usuario Administrador del Sistema
        cls.user_admin = cls.env['res.users'].create({
            'name': 'User Admin Test',
            'login': 'user_admin_test',
            'email': 'admin_test@test.com',
            'groups_id': [(6, 0, [group_user.id, group_system.id])],
        })

        # Registro maestro creado en setUpClass
        cls.vessel = cls.env['shipping.vessel'].create({
            'name': 'MSC TEST VESSEL',
        })

    def test_01_shipping_user_read_only(self):
        """Usuario shipping_user puede leer pero no puede escribir ni crear."""
        vessel_read = self.vessel.with_user(self.user_shipping_read).name
        self.assertEqual(vessel_read, 'MSC TEST VESSEL')

        with self.assertRaises(AccessError):
            self.vessel.with_user(self.user_shipping_read).write({'name': 'MODIFIED NAME'})

        with self.assertRaises(AccessError):
            self.env['shipping.voyage'].with_user(self.user_shipping_read).create({
                'vessel_id': self.vessel.id,
                'voyage_reference': 'VOY-READ-FAIL',
                'etd': '2026-11-01',
            })

    def test_02_no_group_user_gets_access_error(self):
        """Usuario estrictamente base (sin shipping ni operaciones) recibe AccessError al leer o crear."""
        with self.assertRaises(AccessError):
            self.vessel.with_user(self.user_no_access).read(['name'])

        with self.assertRaises(AccessError):
            self.env['shipping.voyage'].with_user(self.user_no_access).create({
                'vessel_id': self.vessel.id,
                'voyage_reference': 'VOY-NO-ACC',
                'etd': '2026-11-01',
            })

    def test_03_admin_system_full_access(self):
        """Usuario base.group_system tiene acceso total: crear, modificar y borrar."""
        voyage = self.env['shipping.voyage'].with_user(self.user_admin).create({
            'vessel_id': self.vessel.id,
            'voyage_reference': 'VOY-ADMIN-01',
            'port_of_discharge': 'Callao, PE',
            'etd': '2026-11-01',
        })
        self.assertTrue(voyage.id)
        voyage.with_user(self.user_admin).write({'voyage_reference': 'VOY-ADMIN-UPDATED'})
        self.assertEqual(voyage.voyage_reference, 'VOY-ADMIN-UPDATED')
        voyage.with_user(self.user_admin).unlink()
        self.assertFalse(voyage.exists())
