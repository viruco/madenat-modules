from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'madenat',
        'madenat_lumber_logistics', 'logistics_vessel_button')
class TestVesselButton(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vessel = cls.env['shipping.vessel'].create(
            {'name': 'Motonave Test Botón'} )
        cls.base_view = cls.env.ref(
            'madenat_lumber_shipping_core.view_shipping_vessel_form')
        cls.inherit_view = cls.env.ref(
            'madenat_lumber_logistics.'
            'view_shipping_vessel_form_inherit_logistics')

    def test_01_action_opens_vessel_shipments(self):
        action = self.vessel.action_open_vessel_shipments()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'lumber.export.shipment')
        self.assertEqual(
            action['domain'], [('vessel_id', '=', self.vessel.id)])

    def test_02_button_lives_in_logistics_inherit_view(self):
        self.assertEqual(self.inherit_view.inherit_id, self.base_view)
        self.assertIn(
            'action_open_vessel_shipments', self.inherit_view.arch_db)

    def test_03_core_view_has_no_button(self):
        self.assertNotIn(
            'action_open_vessel_shipments', self.base_view.arch_db)
        self.assertIn('<header', self.base_view.arch_db)
