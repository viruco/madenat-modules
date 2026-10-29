# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'madenat', 'logistics_shipping_access')
class TestShippingAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        group_user = cls.env.ref('base.group_user')
        group_oper = cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        group_jef = cls.env.ref('madenat_lumber_core.group_madenat_jefatura_operaciones')
        group_aud = cls.env.ref('madenat_lumber_core.group_madenat_auditoria')

        cls.user_oper = cls.env['res.users'].create({
            'name': 'User Operaciones Test',
            'login': 'user_oper_ship_test',
            'email': 'oper_ship@test.com',
            'groups_id': [(6, 0, [group_user.id, group_oper.id])],
        })

        cls.user_jef = cls.env['res.users'].create({
            'name': 'User Jefatura Test',
            'login': 'user_jef_ship_test',
            'email': 'jef_ship@test.com',
            'groups_id': [(6, 0, [group_user.id, group_jef.id])],
        })

        cls.user_aud = cls.env['res.users'].create({
            'name': 'User Auditoria Test',
            'login': 'user_aud_ship_test',
            'email': 'aud_ship@test.com',
            'groups_id': [(6, 0, [group_user.id, group_aud.id])],
        })

        cls.vessel = cls.env['shipping.vessel'].create({
            'name': 'MSC LOGISTICS ACCESS TEST',
        })

    def test_01_operaciones_can_read_vessel_and_create_voyage_no_unlink(self):
        """Operaciones puede leer buque y crear viaje/booking, pero no puede borrar viaje."""
        vessel_read = self.vessel.with_user(self.user_oper).name
        self.assertEqual(vessel_read, 'MSC LOGISTICS ACCESS TEST')

        voyage = self.env['shipping.voyage'].with_user(self.user_oper).create({
            'vessel_id': self.vessel.id,
            'voyage_reference': 'VOY-OPER-01',
            'port_of_discharge': 'Callao, PE',
            'etd': '2026-11-01',
        })
        self.assertTrue(voyage.id)

        # Operaciones NO puede borrar viajes (cambio de comportamiento DISC-LOG-04)
        with self.assertRaises(AccessError):
            voyage.with_user(self.user_oper).unlink()

    def test_02_jefatura_can_unlink_voyage(self):
        """Jefatura de Operaciones sí tiene permiso de unlink sobre viajes."""
        voyage = self.env['shipping.voyage'].create({
            'vessel_id': self.vessel.id,
            'voyage_reference': 'VOY-JEF-01',
            'port_of_discharge': 'Callao, PE',
            'etd': '2026-11-01',
        })
        voyage.with_user(self.user_jef).unlink()
        self.assertFalse(voyage.exists())

    def test_03_auditoria_read_only(self):
        """Auditoría puede leer buques/viajes pero no puede escribir ni crear."""
        vessel_read = self.vessel.with_user(self.user_aud).name
        self.assertEqual(vessel_read, 'MSC LOGISTICS ACCESS TEST')

        with self.assertRaises(AccessError):
            self.env['shipping.voyage'].with_user(self.user_aud).create({
                'vessel_id': self.vessel.id,
                'voyage_reference': 'VOY-AUD-FAIL',
                'etd': '2026-11-01',
            })
