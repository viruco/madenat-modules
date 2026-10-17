# -*- coding: utf-8 -*-
import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionResult,
)
from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeProfileCoherence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)

    def _b64(self, raw=b'fake bytes'):
        return base64.b64encode(raw).decode()

    def _make_wizard(self, profile='metric', tipo='producto', state='draft'):
        return self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': tipo,
            'state': state,
            'ingestion_profile': profile,
            'excel_file': self._b64(b'excel-content'),
            'excel_filename': 'packing.xlsx',
            'pdf_file': self._b64(b'%PDF-content'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })

    def test_01_route_procesado_transfers_ingestion_profile(self):
        """_route_procesado debe transferir ingestion_profile a madenat.guia.processing."""
        wizard = self._make_wizard(profile='f1550', tipo='procesado')
        guia_model = self.env['madenat.guia.processing']
        with patch.object(type(guia_model), 'action_verify_data', return_value=None):
            wizard.action_route_document()
        guia = self.Guia.search([('excel_filename', '=', 'packing.xlsx')], order='id desc', limit=1)
        self.assertTrue(guia)
        self.assertEqual(guia.ingestion_profile, 'f1550')

    def test_02_profile_f5085_with_metric_lengths_warns_and_requires_confirm(self):
        """Perfil f5085 con largos métricos estándar sin pies debe advertir y requerir confirmación."""
        wizard = self._make_wizard(profile='f5085', tipo='procesado')
        mock_result = DocumentExtractionResult(
            header={},
            lines=[
                {'thickness_value_raw': '37', 'width_value_raw': '125', 'length_value_raw': '3.70', 'length_unit': 'm', 'pieces': 100},
                {'thickness_value_raw': '37', 'width_value_raw': '125', 'length_value_raw': '4.05', 'length_unit': 'm', 'pieces': 100},
            ],
            warnings=[]
        )
        with patch.object(intake_wizard_module, 'extract_document', return_value=mock_result):
            # 1. Sin confirmación -> lanza UserError de advertencia con el mensaje explicativo
            with self.assertRaises(UserError) as ctx:
                wizard.action_route_document()
            self.assertIn('ADVERTENCIA DE COHERENCIA DE PERFIL', str(ctx.exception))
            self.assertIn('f5085', str(ctx.exception))

            # 2. Con confirmación explícita -> procede normalmente
            wizard.confirm_profile_mismatch = True
            guia_model = self.env['madenat.guia.processing']
            with patch.object(type(guia_model), 'action_verify_data', return_value=None):
                wizard.action_route_document()
            self.assertEqual(wizard.state, 'routed')

    def test_03_profile_metric_with_fractional_widths_warns_and_requires_confirm(self):
        """Perfil metric con anchos fraccionarios en pulgadas debe advertir y requerir confirmación."""
        wizard = self._make_wizard(profile='metric', tipo='procesado')
        mock_result = DocumentExtractionResult(
            header={},
            lines=[
                {'thickness_value_raw': '1 1/2', 'width_value_raw': '5 5/8', 'length_value_raw': '10', 'length_unit': 'ft', 'pieces': 100},
            ],
            warnings=[]
        )
        with patch.object(intake_wizard_module, 'extract_document', return_value=mock_result):
            # 1. Sin confirmación -> lanza UserError de advertencia con el mensaje explicativo
            with self.assertRaises(UserError) as ctx:
                wizard.action_route_document()
            self.assertIn('ADVERTENCIA DE COHERENCIA DE PERFIL', str(ctx.exception))
            self.assertIn('Métrico', str(ctx.exception))

            # 2. Con confirmación explícita -> procede normalmente
            wizard.confirm_profile_mismatch = True
            guia_model = self.env['madenat.guia.processing']
            with patch.object(type(guia_model), 'action_verify_data', return_value=None):
                wizard.action_route_document()
            self.assertEqual(wizard.state, 'routed')

    def test_04_preview_document_sets_profile_warning_message(self):
        """Al leer documento (preview), si hay discrepancia de perfil se setea profile_warning_message."""
        wizard = self._make_wizard(profile='metric', tipo='producto')
        mock_result = DocumentExtractionResult(
            header={},
            lines=[
                {'thickness_value_raw': '1 1/2', 'width_value_raw': '5 5/8', 'length_value_raw': '10', 'length_unit': 'ft', 'pieces': 100},
            ],
            warnings=[]
        )
        with patch.object(intake_wizard_module, 'extract_document', return_value=mock_result), \
             patch.object(type(wizard), '_classify_normal_document', return_value=None):
            wizard.action_preview_document()
            self.assertTrue(wizard.profile_warning_message)
            self.assertIn('Métrico', wizard.profile_warning_message)
            self.assertIn(wizard.profile_warning_message, wizard.preview_warnings)

    def test_05_profile_coherent_passes_without_warning(self):
        """Perfil coherente pasa directamente sin advertencia ni bloqueo."""
        wizard = self._make_wizard(profile='metric', tipo='procesado')
        mock_result = DocumentExtractionResult(
            header={},
            lines=[
                {'thickness_value_raw': '37', 'width_value_raw': '125', 'length_value_raw': '3.70', 'length_unit': 'm', 'pieces': 100},
            ],
            warnings=[]
        )
        guia_model = self.env['madenat.guia.processing']
        with patch.object(intake_wizard_module, 'extract_document', return_value=mock_result), \
             patch.object(type(guia_model), 'action_verify_data', return_value=None):
            wizard.action_route_document()
            self.assertEqual(wizard.state, 'routed')
            self.assertFalse(wizard.profile_warning_message)
