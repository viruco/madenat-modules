# -*- coding: utf-8 -*-
"""AD-68: cobertura de la ruta 'granel' en el wizard de intake."""

import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionResult,
)
from ..models import intake_wizard as intake_wizard_module


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestGranelRouteIntake(TransactionCase):
    """Ruta granel en el wizard: routing, keywords, respaldo y candados Excel."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Config = cls.env['madenat.ingestion.config']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )

    def _b64(self, raw=b'fake bytes'):
        return base64.b64encode(raw).decode()

    def _make_wizard(self, tipo='granel', excel=True, pdf=True, assign_location=True):
        vals = {'tipo_ingreso': tipo}
        if excel:
            vals['excel_file'] = self._b64(b'excel-bytes')
            vals['excel_filename'] = 'packing.xlsx'
        if pdf:
            vals['pdf_file'] = self._b64(b'%PDF-fake')
            vals['pdf_filename'] = 'guia.pdf'
        if assign_location:
            vals['assignment_location_id'] = self.location.id
        return self.Wizard.create(vals)

    def _pdf_result(self, total_volume_m3=10.0):
        return DocumentExtractionResult(
            header={'total_volume_m3': total_volume_m3, 'guide_number': 'GRANEL-1'},
            lines=[],
            warnings=[],
        )

    # ── Ruta granel ────────────────────────────────────────────────────────
    def test_01_route_granel_crea_guia_y_linea(self):
        wizard = self._make_wizard(tipo='granel', excel=False, pdf=True)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_route_document()

        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(guia.state, 'verified')
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 10.0, places=3)

    # ── Clasificación por keywords migradas a config ────────────────────────
    def test_02_config_keywords_procesado(self):
        kw = self.Config.get_tipo_ingreso_keywords('procesado')
        self.assertIn('cepillado', kw)
        self.assertIn('servicio', kw)
        self.assertIn('proceso', kw)
        self.assertIn('maquila', kw)

    def test_03_config_keywords_granel(self):
        kw = self.Config.get_tipo_ingreso_keywords('granel')
        self.assertIn('granel', kw)
        self.assertIn('volumen total', kw)

    def test_04_onchange_procesado_por_filename(self):
        wizard = self._make_wizard(tipo='producto', excel=True, pdf=True)
        wizard.pdf_filename = 'guia servicio.pdf'
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'procesado')
        self.assertTrue(wizard.tipo_ingreso_auto_detectado)

    def test_05_onchange_granel_por_filename(self):
        wizard = self._make_wizard(tipo='producto', excel=True, pdf=True)
        wizard.pdf_filename = 'recepcion granel.pdf'
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'granel')
        self.assertTrue(wizard.tipo_ingreso_auto_detectado)

    # ── Señal de respaldo: sin Excel + PDF con total_volume_m3 ──────────────
    def test_06_onchange_respaldo_granel_sin_excel(self):
        wizard = self._make_wizard(tipo='producto', excel=False, pdf=True)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            result = wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'granel')
        self.assertTrue(wizard.tipo_ingreso_auto_detectado)
        self.assertIsNone(result)

    # ── Candados de excel_file ──────────────────────────────────────────────
    def test_07_excel_obligatorio_producto(self):
        wizard = self._make_wizard(tipo='producto', excel=False, pdf=True)
        with self.assertRaises(UserError):
            wizard.action_route_document()

    def test_08_excel_obligatorio_procesado(self):
        wizard = self._make_wizard(tipo='procesado', excel=False, pdf=True)
        with self.assertRaises(UserError):
            wizard.action_route_document()

    def test_09_excel_opcional_granel(self):
        wizard = self._make_wizard(tipo='granel', excel=False, pdf=True)
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):
            wizard.action_route_document()  # no debe lanzar UserError
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)

    # ── AD-72: selección manual de detalle ─────────────────────────────────
    def _pdf_result_lines(self):
        return DocumentExtractionResult(
            header={'total_volume_m3': 10.0, 'guide_number': 'GRANEL-1'},
            lines=[
                {'lot_number': 'LOTE-A', 'volume_m3': 4.0, 'pieces': 10,
                 'product_name_original': 'MADERA', 'product_code': 'C1'},
                {'lot_number': 'LOTE-B', 'volume_m3': 6.0, 'pieces': 15,
                 'product_name_original': 'MADERA', 'product_code': 'C2'},
            ],
            warnings=[],
        )

    def test_10_linea_por_linea_con_detalle(self):
        """linea_por_linea con PDF que trae líneas → N líneas de detalle."""
        wizard = self._make_wizard(tipo='granel', excel=False, pdf=True)
        wizard.tipo_detalle_granel = 'linea_por_linea'
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result_lines()):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(len(guia.processing_line_ids), 2)
        self.assertEqual(set(guia.processing_line_ids.mapped('lot_name')),
                         {'LOTE-A', 'LOTE-B'})

    def test_11_linea_por_linea_sin_tabla_degrade_a_agregado(self):
        """linea_por_linea sin tabla (Nivel 4) → degrada a resumen agregado + mensaje."""
        wizard = self._make_wizard(tipo='granel', excel=False, pdf=True)
        wizard.tipo_detalle_granel = 'linea_por_linea'
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(10.0)):  # lines=[]
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertEqual(guia.processing_line_ids.lot_name, 'GRANEL')
        self.assertTrue(any('agregado' in (m.body or '') for m in guia.message_ids))

    def test_12_agregado_default_ignora_detalle(self):
        """Modo 'agregado' (default) crea 1 línea sintética aunque el PDF traiga detalle."""
        wizard = self._make_wizard(tipo='granel', excel=False, pdf=True)
        # tipo_detalle_granel queda en default 'agregado'
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result_lines()):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertEqual(guia.processing_line_ids.lot_name, 'GRANEL')
