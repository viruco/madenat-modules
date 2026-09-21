# -*- coding: utf-8 -*-
"""AD-73: wizard de reclasificación de tipo de ingreso (pre-Gate-3)."""

import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeReclassifyWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.reclassify.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Reception = cls.env['lumber.reception']
        cls.Audit = cls.env['madenat.audit.log']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.partner = cls.env['res.partner'].create({'name': 'AD73 Partner'})
        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'AD73 Storable',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': uom_m3.id,
            'uom_po_id': uom_m3.id,
        })

    def _make_guia(self, name='AD73-GUIA', state='draft'):
        return self.Guia.create({
            'name': name,
            'state': state,
            'tipo_recepcion': 'service',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })

    def _make_reception(self, name='AD73-REC', state='draft'):
        return self.Reception.create({
            'name': name,
            'state': state,
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'excel_file': base64.b64encode(b'fake').decode(),
        })

    def _make_wizard(self, model, res_id, tipo='granel'):
        return self.Wizard.create({
            'source_model': model,
            'source_res_id': res_id,
            'tipo_ingreso_correcto': tipo,
        })

    def test_01_reclassify_guia_draft_success(self):
        guia = self._make_guia(name='RECLASS-GUIA-1', state='draft')
        wizard = self._make_wizard('madenat.guia.processing', guia.id, 'granel')
        action = wizard.action_confirm_reclassify()

        # unlink confirmado.
        self.assertFalse(guia.exists())
        # evento de auditoría persiste (guia_processing_id ondelete=set null).
        event = self.Audit.search([
            ('action_type', '=', 'reclassification'),
            ('description', 'ilike', 'RECLASS-GUIA-1'),
        ], limit=1)
        self.assertTrue(event)
        self.assertFalse(event.guia_processing_id)
        # wizard nuevo con tipo correcto.
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.wizard')
        new_wizard = self.env['madenat.lumber.intake.wizard'].browse(action['res_id'])
        self.assertEqual(new_wizard.tipo_ingreso, 'granel')

    def test_02_reclassify_guia_validated_blocked(self):
        guia = self._make_guia(name='RECLASS-GUIA-2', state='validated')
        wizard = self._make_wizard('madenat.guia.processing', guia.id, 'granel')
        with self.assertRaises(UserError):
            wizard.action_confirm_reclassify()
        self.assertTrue(guia.exists())
        self.assertEqual(self.Audit.search_count([
            ('action_type', '=', 'reclassification'),
            ('description', 'ilike', 'RECLASS-GUIA-2'),
        ]), 0)

    def test_03_reclassify_guia_with_lot_blocked(self):
        guia = self._make_guia(name='RECLASS-GUIA-3', state='draft')
        lot = self.StockLot.create({
            'name': 'LOT-X',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })
        guia.lot_ids = [(6, 0, [lot.id])]
        wizard = self._make_wizard('madenat.guia.processing', guia.id, 'granel')
        with self.assertRaises(UserError):
            wizard.action_confirm_reclassify()
        self.assertTrue(guia.exists())

    def test_04_reclassify_reception_pre_gate3_success(self):
        reception = self._make_reception(name='RECLASS-REC-1', state='draft')
        wizard = self._make_wizard('lumber.reception', reception.id, 'procesado')
        action = wizard.action_confirm_reclassify()
        self.assertFalse(reception.exists())
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.wizard')
        new_wizard = self.env['madenat.lumber.intake.wizard'].browse(action['res_id'])
        self.assertEqual(new_wizard.tipo_ingreso, 'procesado')

    def test_05_reclassify_reception_verified_pre_gate3_success(self):
        """'verified' es pre-Gate-3: action_confirm_reception lo exige."""
        reception = self._make_reception(
            name='RECLASS-REC-VERIFIED', state='verified')
        wizard = self._make_wizard(
            'lumber.reception', reception.id, 'procesado')

        action = wizard.action_confirm_reclassify()

        self.assertFalse(reception.exists())
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.wizard')
        new_wizard = self.env['madenat.lumber.intake.wizard'].browse(
            action['res_id'])
        self.assertEqual(new_wizard.tipo_ingreso, 'procesado')

    def test_06_reclassify_reception_post_gate3_blocked(self):
        reception = self._make_reception(name='RECLASS-REC-2', state='done')
        wizard = self._make_wizard('lumber.reception', reception.id, 'procesado')
        with self.assertRaises(UserError):
            wizard.action_confirm_reclassify()
        self.assertTrue(reception.exists())

    def test_07_button_invisible_domain(self):
        """El botón de reclasificar usa el dominio invisible correcto por modelo."""
        reception_view = self.env['ir.ui.view'].search([
            ('name', '=', 'lumber.reception.intake.facade.form')], limit=1)
        self.assertTrue(reception_view)
        self.assertIn(
            "invisible=\"state not in ('draft', 'processing', 'verified')\"",
            reception_view.arch)
        guia_view = self.env['ir.ui.view'].search([
            ('name', '=', 'madenat.guia.processing.intake.facade.form')], limit=1)
        self.assertTrue(guia_view)
        self.assertIn(
            "invisible=\"state not in ('draft', 'verified')\"",
            guia_view.arch)
