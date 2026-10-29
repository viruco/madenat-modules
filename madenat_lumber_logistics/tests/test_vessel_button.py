# -*- coding: utf-8 -*-
"""Tests for logistics vessel button visibility.
Tag: logistics_vessel_button
"""
from odoo.tests import TransactionCase, tagged

@tagged('logistics_vessel_button')
class TestVesselButtonVisibility(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a vessel record
        self.Vessel = self.env['shipping.vessel'].create({
            'name': 'Test Vessel',
        })
        # Create a user (placeholder groups)
        self.User = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_logistics',
        })
        self.env = self.env(user=self.User)

    def test_button_visible_when_logistics_installed(self):
        """Button should be present when logistics module is installed."""
        self.assertTrue(self.env['ir.module.module'].search([('name', '=', 'madenat_lumber_logistics'), ('state', '=', 'installed')]))
        self.assertTrue(hasattr(self.Vessel, 'action_open_vessel_shipments'))

    def test_button_not_visible_without_logistics(self):
        """Button should be absent if logistics module is not installed."""
        module = self.env['ir.module.module'].search([('name', '=', 'madenat_lumber_logistics')])
        if module:
            module.button_immediate_uninstall()
        self.env.cr.flush()
        Vessel = self.env['shipping.vessel']
        self.assertFalse(hasattr(Vessel, 'action_open_vessel_shipments'))

    def test_button_action_opens_correct_view(self):
        """Button should return act_window targeting shipments."""
        action = self.Vessel.action_open_vessel_shipments()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'lumber.export.shipment')
        self.assertIn('domain', action)
        self.assertIn('name', action)
