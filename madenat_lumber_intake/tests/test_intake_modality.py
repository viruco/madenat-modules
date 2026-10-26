# -*- coding: utf-8 -*-
"""Modalidad de Ingesta en el wizard: 'normal' vs 'volume'.

La modalidad decide el flujo; el Patio es solo destino físico. El tipo de
ingreso (autodetectado) decide producto/procesado únicamente en modalidad
normal; la modalidad 'volume' deriva directo a Granel.
"""
import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionResult,
)
from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module
from .intake_reading_helpers import mark_previewed


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeModality(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Reception = cls.env['lumber.reception']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)
        cls.assertTrue(cls.location, 'Se requiere un stock.location interno')

    def _b64(self, raw=b'fake bytes'):
        return base64.b64encode(raw).decode()

    def _make_wizard(self, modality='normal', tipo='producto', state='draft',
                     excel=True, pdf=True, location=None):
        vals = {
            'intake_modality': modality,
            'tipo_ingreso': tipo,
            'state': state,
        }
        if excel:
            vals['excel_file'] = self._b64(b'excel-bytes')
            vals['excel_filename'] = 'packing.xlsx'
        if pdf:
            vals['pdf_file'] = self._b64(b'%PDF-fake')
            vals['pdf_filename'] = 'guia.pdf'
        vals['assignment_location_id'] = (location or self.location).id
        wizard = self.Wizard.create(vals)
        if state == 'previewed':
            # Lectura simulada vigente (FASE 13/2D): estado 'previewed' con la
            # huella de los datos actuales, sin ejecutar el motor.
            mark_previewed(wizard)
        return wizard

    def _pdf_result(self, total_volume_m3=10.0):
        return DocumentExtractionResult(
            header={'total_volume_m3': total_volume_m3, 'guide_number': 'G-1'},
            lines=[], warnings=[])

    # 1. default normal
    def test_01_default_normal(self):
        wizard = self.Wizard.create({'assignment_location_id': self.location.id})
        self.assertEqual(wizard.intake_modality, 'normal')

    # 2. normal + PDF sin Excel → bloquea
    def test_02_normal_pdf_sin_excel_bloquea(self):
        wizard = self._make_wizard(modality='normal', tipo='producto',
                                   state='previewed', excel=False)
        with self.assertRaises(UserError):
            wizard.action_route_document()

    # 3. normal + producto → _route_producto
    def test_03_normal_producto_route(self):
        wizard = self._make_wizard(modality='normal', tipo='producto',
                                   state='previewed')
        reception_model = self.env['lumber.reception']
        with patch.object(type(reception_model), 'action_process_documents',
                          return_value=True):
            wizard.action_route_document()
        self.assertEqual(wizard.target_model, 'lumber.reception')
        self.assertEqual(len(self.Reception.search(
            [('excel_filename', '=', 'packing.xlsx')])), 1)

    # 4. normal + procesado → _route_procesado
    def test_04_normal_procesado_route(self):
        wizard = self._make_wizard(modality='normal', tipo='procesado')
        mark_previewed(wizard)
        guia_model = self.env['madenat.guia.processing']
        with patch.object(type(guia_model), 'action_verify_data', return_value=None):
            wizard.action_route_document()
        guia = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'service')

    # 5. normal + tipo no producto/procesado → bloquea
    def test_05_normal_tipo_no_clasificable_bloquea(self):
        wizard = self._make_wizard(modality='normal', tipo='granel')
        mark_previewed(wizard)
        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()
        self.assertIn('tipo de ingreso', str(ctx.exception))

    # 6. volume + PDF sin Excel → _route_granel
    def test_06_volume_pdf_sin_excel_granel(self):
        wizard = self._make_wizard(modality='volume', tipo='granel', excel=False)
        mark_previewed(wizard)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(wizard.target_model, 'madenat.guia.processing')

    # 7. volume + PDF + Excel → _route_granel
    def test_07_volume_pdf_excel_granel(self):
        wizard = self._make_wizard(modality='volume', tipo='granel', excel=True)
        mark_previewed(wizard)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')

    # 8. cualquier patio interno sirve para ambas modalidades
    def test_08_patio_interno_acepta_ambas_modalidades(self):
        guia_model = self.env['madenat.guia.processing']
        w1 = self._make_wizard(modality='normal', tipo='procesado')
        mark_previewed(w1)
        with patch.object(type(guia_model), 'action_verify_data', return_value=None):
            w1.action_route_document()

        w2 = self._make_wizard(modality='volume', tipo='granel', excel=False)
        mark_previewed(w2)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(5.0)):
            w2.action_route_document()

        guias = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guias), 2)

    # 9. patio ausente o no interno → bloquea
    def test_09_patio_ausente_bloquea(self):
        wizard = self._make_wizard(modality='normal', tipo='producto',
                                   state='previewed')
        wizard.assignment_location_id = False
        with self.assertRaises(UserError):
            wizard.action_route_document()

    def test_09_patio_no_interno_bloquea(self):
        loc = self.env['stock.location'].search(
            [('usage', '!=', 'internal')], limit=1)
        if not loc:
            self.skipTest('No hay ubicación no interna disponible')
        wizard = self._make_wizard(modality='normal', tipo='producto',
                                   state='previewed', location=loc)
        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()
        self.assertIn('interna', str(ctx.exception))

    # 10. perfil de lectura independiente de modalidad
    def test_10_perfil_independiente_de_modalidad(self):
        w = self._make_wizard(modality='normal', tipo='producto')
        self.assertEqual(w.ingestion_profile, 'metric')
        w.intake_modality = 'volume'
        self.assertEqual(w.ingestion_profile, 'metric')

    # 11. sin referencias a intake_mode / intake_config_status
    def test_11_sin_referencias_intake_mode(self):
        self.assertNotIn('intake_mode', self.env['stock.location']._fields)
        self.assertNotIn('intake_config_status', self.env['stock.location']._fields)
        self.assertNotIn('intake_mode', self.env['madenat.lumber.intake.wizard']._fields)

    # 12. volume + PDF sin Excel: preview no bloquea y permite granel
    def test_12_volume_preview_pdf_sin_excel(self):
        wizard = self._make_wizard(modality='volume', tipo='producto', excel=False)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_preview_document()
        self.assertEqual(wizard.state, 'previewed')
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')

    # 13. volume + PDF + Excel: preview no lanza error
    def test_13_volume_preview_pdf_excel(self):
        wizard = self._make_wizard(modality='volume', tipo='producto', excel=True)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_preview_document()
        self.assertEqual(wizard.state, 'previewed')

    # 14. normal + PDF sin Excel: preview sigue lanzando error
    def test_14_normal_preview_pdf_sin_excel_bloquea(self):
        wizard = self._make_wizard(modality='normal', tipo='producto', excel=False)
        with self.assertRaises(UserError):
            wizard.action_preview_document()

    # 15. normal + PDF + Excel: conserva lectura
    def test_15_normal_preview_pdf_excel(self):
        wizard = self._make_wizard(modality='normal', tipo='producto', excel=True)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_preview_document()
        self.assertEqual(wizard.state, 'previewed')

    # 16. mensaje técnico para volume sin "Procesados"/"varios paquetes"/"N° de lote"
    def test_16_volume_mensaje_sin_procesados(self):
        w = self._make_wizard(modality='volume', tipo='granel', excel=False)
        msg = w.requirements_info
        self.assertNotIn('Procesados', msg)
        self.assertNotIn('varios paquetes', msg)
        self.assertNotIn('N° de lote', msg)

    # 17. texto exacto de requisitos según modalidad
    def test_17_requirements_info_texto(self):
        normal = self._make_wizard(modality='normal', tipo='producto')
        self.assertEqual(
            normal.requirements_info,
            'Requisitos obligatorios: Guía/PDF, Archivo Excel y Patio de Asignación.')
        volume = self._make_wizard(modality='volume', tipo='granel', excel=False)
        self.assertEqual(
            volume.requirements_info,
            'Requisito obligatorio: Patio de Asignación. '
            'Adjunte al menos una evidencia documental: Guía/PDF, '
            'Archivo Excel o ambos.')
