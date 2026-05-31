from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestBillingConsolidation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Consolidation = self.env['lumber.billing.consolidation']
        self.Shipment = self.env['lumber.export.shipment']
        self.customer = self.env['res.partner'].create({
            'name': 'Cliente Test Internacional',
        })
        self.shipment = self.Shipment.create({
            'name': 'SHIP-TEST-001',
            'customer_id': self.customer.id,
            'state': 'delivered',
        })

    def test_01_flujo_auditoria_aprobacion(self):
        """Flujo completo: ready_audit -> in_audit -> audit_approved -> ready_billing"""
        consolidation = self.Consolidation.create({
            'shipment_id': self.shipment.id,
            'state': 'ready_audit',
        })

        consolidation.action_start_audit()
        self.assertEqual(consolidation.state, 'in_audit')
        self.assertEqual(consolidation.auditor_id, self.env.user)

        consolidation.action_approve_audit()
        self.assertEqual(consolidation.state, 'audit_approved')

        consolidation.action_send_to_billing()
        self.assertEqual(consolidation.state, 'ready_billing')

    def test_02_no_duplicar_consolidacion(self):
        """No se puede crear segunda consolidación activa para el mismo embarque"""
        self.Consolidation.create({
            'shipment_id': self.shipment.id,
            'state': 'draft',
        })

        with self.assertRaises(Exception):
            self.Consolidation.create({
                'shipment_id': self.shipment.id,
                'state': 'draft',
            })

    def test_03_server_action_rechaza_shipment_no_completed(self):
        """El server action debe rechazar embarques no completados"""
        shipment_draft = self.Shipment.create({
            'name': 'SHIP-TEST-DRAFT',
            'customer_id': self.customer.id,
            'state': 'draft',
        })

        server_action = self.env.ref(
            'madenat_lumber_billing.action_create_consolidation_from_shipment'
        )

        with self.assertRaises(Exception):
            server_action.with_context(
                active_model='lumber.export.shipment',
                active_ids=[shipment_draft.id],
                active_id=shipment_draft.id,
            ).run()
