# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'madenat', 'costing_shipping_access')
class TestCostingShippingAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('base.group_user')
        group_costos = cls.env.ref('madenat_lumber_core.group_madenat_costos')

        cls.user_costos = cls.env['res.users'].create({
            'name': 'User Costos Test',
            'login': 'user_costos_ship_test',
            'email': 'costos_ship@test.com',
            'groups_id': [(6, 0, [group_user.id, group_costos.id])],
        })

        cls.vessel = cls.env['shipping.vessel'].create({
            'name': 'MSC COSTING ACCESS TEST',
        })
        cls.voyage = cls.env['shipping.voyage'].create({
            'vessel_id': cls.vessel.id,
            'voyage_reference': 'VOY-COSTOS-01',
            'port_of_discharge': 'Callao, PE',
            'etd': '2026-11-01',
        })
        cls.carrier = cls.env['res.partner'].create({
            'name': 'Test Shipping Line Ltd',
        })
        cls.booking = cls.env['shipping.booking'].create({
            'name': 'BKG-COSTOS-001',
            'shipping_line_id': cls.carrier.id,
            'voyage_id': cls.voyage.id,
        })

    def test_01_costos_can_read_shipping_booking_and_cannot_write(self):
        """Usuario con solo group_madenat_costos puede leer shipping.booking pero no escribir ni crear."""
        # 1. Lectura permitida
        booking_costos = self.booking.with_user(self.user_costos)
        self.assertEqual(booking_costos.name, 'BKG-COSTOS-001')

        # 2. Escritura bloqueada
        with self.assertRaises(AccessError):
            booking_costos.write({'notes': 'Modificacion no autorizada'})

        # 3. Creación bloqueada
        with self.assertRaises(AccessError):
            self.env['shipping.booking'].with_user(self.user_costos).create({
                'name': 'BKG-COSTOS-002',
                'shipping_line_id': self.carrier.id,
                'voyage_id': self.voyage.id,
            })
