# -*- coding: utf-8 -*-
"""FASE 13/2D: procedencia del perfil y vigencia de la lectura.

Cubre las decisiones aprobadas H1–H4:
  * la sugerencia documental nunca pisa una elección explícita del operador
    (`profile_origin = 'chosen'`), sólo se registra en `profile_suggested` y
    se muestra como aviso no bloqueante;
  * cualquier cambio real en las entradas de la lectura invalida el preview
    (estado 'previewed' → 'draft') y exige volver a leer;
  * la derivación exige lectura vigente en las TRES modalidades (H2): sin
    'previewed' o con huella distinta, `action_route_document` bloquea;
  * «Leer documento» no se ejecuta sin los documentos requeridos y no escribe
    nada si faltan.
"""

import base64
from unittest.mock import patch

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionResult,
)
from odoo.addons.madenat_lumber_intake.models import (
    intake_wizard as intake_wizard_module,
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeProfileProvenance(TransactionCase):
    """Procedencia del perfil de lectura y vigencia de la lectura (FASE 13/2D)."""

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

    # ── Helpers ────────────────────────────────────────────────────────────
    def _b64(self, raw=b'fake bytes'):
        return base64.b64encode(raw).decode()

    def _make_wizard(self, modality='normal', tipo='producto', profile='metric',
                     excel=True, pdf=True):
        vals = {
            'intake_modality': modality,
            'tipo_ingreso': tipo,
            'ingestion_profile': profile,
            'assignment_location_id': self.location.id,
        }
        if excel:
            vals['excel_file'] = self._b64(b'excel-content')
            vals['excel_filename'] = 'packing.xlsx'
        if pdf:
            vals['pdf_file'] = self._b64(b'%PDF-content')
            vals['pdf_filename'] = 'guia.pdf'
        return self.Wizard.create(vals)

    def _result(self, total=10.0, lines=None, detected_profile=None,
                guide_number=None):
        return DocumentExtractionResult(
            header={'total_volume_m3': total,
                    'guide_number': guide_number or False},
            lines=lines or [],
            warnings=[],
            detected_profile_code=detected_profile,
        )

    def _preview(self, wizard, result=None):
        """Ejecuta 'Leer documento' con el motor simulado (sin red).

        En modalidad normal se neutraliza la clasificación por señales para que
        el tipo de ingreso del wizard (Producto/Procesado) sea el que decide el
        escenario de la prueba.
        """
        result = result if result is not None else self._result()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=result):
            if wizard.intake_modality == 'volume':
                wizard.action_preview_document()
            else:
                with patch.object(type(wizard), '_classify_normal_document',
                                  return_value=None):
                    wizard.action_preview_document()
        return wizard

    # ── T-2D-1: la sugerencia NO pisa la elección del operador ─────────────
    def test_t2d_1_sugerencia_no_pisa_eleccion_del_operador(self):
        wizard = self._make_wizard(profile='f1550')
        wizard.profile_origin = 'chosen'

        with patch.object(
            intake_wizard_module, 'extract_document',
            return_value=self._result(detected_profile='packing_metrico_aserrada'),
        ):
            wizard._onchange_suggest_ingestion_profile()

        self.assertEqual(wizard.ingestion_profile, 'f1550')
        self.assertEqual(wizard.profile_origin, 'chosen')
        self.assertEqual(wizard.profile_suggested, 'metric')
        self.assertTrue(wizard.profile_mismatch_hint)
        self.assertIn('Madera Aserrada S2S', wizard.profile_mismatch_hint)
        self.assertIn('Madera Bruta — Sistema Métrico',
                      wizard.profile_mismatch_hint)

    # ── T-2D-2: sin elección previa, la sugerencia se aplica ───────────────
    def test_t2d_2_sugerencia_se_aplica_sin_eleccion_previa(self):
        wizard = self._make_wizard(profile='f1550')
        self.assertEqual(wizard.profile_origin, 'default')

        with patch.object(
            intake_wizard_module, 'extract_document',
            return_value=self._result(detected_profile='packing_metrico_aserrada'),
        ):
            wizard._onchange_suggest_ingestion_profile()

        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertEqual(wizard.profile_origin, 'suggested')
        self.assertEqual(wizard.profile_suggested, 'metric')
        self.assertFalse(wizard.profile_mismatch_hint)

    # ── T-2D-3: coincidencia ≠ elección; elegir distinto sí es elección ────
    def test_t2d_3_coincidencia_no_es_eleccion(self):
        wizard = self._make_wizard(profile='metric')

        with patch.object(
            intake_wizard_module, 'extract_document',
            return_value=self._result(detected_profile='packing_metrico_aserrada'),
        ):
            wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertEqual(wizard.profile_origin, 'suggested')

        # Re-entrada del onchange sobre el mismo valor: sigue sin ser elección.
        wizard._onchange_mark_profile_chosen()
        self.assertEqual(wizard.profile_origin, 'suggested')

        # El operador elige otro perfil: pasa a 'chosen' y aparece el aviso.
        wizard.ingestion_profile = 'f5085'
        wizard._onchange_mark_profile_chosen()
        self.assertEqual(wizard.profile_origin, 'chosen')
        self.assertTrue(wizard.profile_mismatch_hint)

    # ── T-2D-4: cambiar una entrada de la lectura invalida el preview ──────
    def test_t2d_4_cambio_de_entrada_invalida_lectura(self):
        wizard = self._preview(self._make_wizard(profile='metric'))
        self.assertEqual(wizard.state, 'previewed')
        self.assertTrue(wizard.reading_signature)

    # ── T-2D-5: escribir el MISMO valor no invalida ────────────────────────
    def test_t2d_5_vals_identico_no_invalida(self):
        wizard = self._preview(self._make_wizard(profile='metric'))
        signature = wizard.reading_signature
        self.assertTrue(signature)

        wizard.write({
            'ingestion_profile': 'metric',
            'excel_filename': 'packing.xlsx',
            'pdf_filename': 'guia.pdf',
            'tipo_detalle_granel': 'agregado',
        })

        self.assertEqual(wizard.state, 'previewed')
        self.assertEqual(wizard.reading_signature, signature)

    # ── T-2D-6: sin lectura no hay derivación, en las TRES modalidades ─────
    def test_t2d_6_derivacion_sin_lectura_bloquea_en_tres_modalidades(self):
        casos = (
            ('normal', 'producto'),
            ('normal', 'procesado'),
            ('volume', 'granel'),
        )
        for modality, tipo in casos:
            wizard = self._make_wizard(modality=modality, tipo=tipo)
            self.assertEqual(wizard.state, 'draft')
            with self.assertRaises(UserError) as ctx:
                wizard.action_route_document()
            self.assertIn('Debe leer el documento', str(ctx.exception))
            self.assertEqual(wizard.state, 'draft')
            self.assertFalse(wizard.target_res_id)

        self.assertFalse(self.Reception.search(
            [('excel_filename', '=', 'packing.xlsx')]))
        self.assertFalse(self.Guia.search(
            [('guide_pdf_filename', '=', 'guia.pdf')]))

        # Tras leer, las TRES modalidades quedan en 'previewed' con huella.
        for modality, tipo in casos:
            wizard = self._preview(
                self._make_wizard(modality=modality, tipo=tipo),
                result=self._result(total=0.0))
            self.assertEqual(wizard.state, 'previewed')
            self.assertTrue(wizard.reading_signature)
            self.assertEqual(
                wizard.reading_signature, wizard._reading_signature())


        wizard.write({'ingestion_profile': 'f5085'})

        self.assertEqual(wizard.state, 'draft')
        self.assertFalse(wizard.reading_signature)
        self.assertFalse(wizard.preview_data)
        self.assertFalse(wizard.preview_guide_no)
        self.assertFalse(wizard.has_reading_warning)
        self.assertEqual(wizard.preview_line_count, 0)

    # ── T-2D-7: lectura rancia (datos cambiados sin invalidar) bloquea ─────
    def test_t2d_7_lectura_rancia_bloquea_y_preview_renueva(self):
        wizard = self._preview(self._make_wizard(profile='metric'))
        self.assertEqual(wizard.state, 'previewed')

        # Cambio de datos SIN pasar por write(): la huella deja de coincidir
        # (escenario de datos mutados por otra vía/servidor).
        wizard.pdf_filename = 'guia_corregida.pdf'
        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()
        self.assertIn('cambiaron después de la lectura', str(ctx.exception))

        # Volver a leer renueva la lectura y permite derivar.
        self._preview(wizard)
        self.assertEqual(wizard.state, 'previewed')
        reception_model = self.env['lumber.reception']
        with patch.object(type(reception_model), 'action_process_documents',
                          return_value=True):
            wizard.action_route_document()
        self.assertEqual(wizard.state, 'routed')

    # ── T-2D-8: leer sin documentos requeridos no escribe nada ─────────────
    def test_t2d_8_preview_sin_documentos_no_escribe_nada(self):
        sin_pdf = self._make_wizard(pdf=False)
        with self.assertRaises(UserError) as ctx:
            sin_pdf.action_preview_document()
        self.assertIn('Guía/PDF requerido para leer el documento',
                      str(ctx.exception))
        self.assertEqual(sin_pdf.state, 'draft')
        self.assertEqual(sin_pdf.tipo_ingreso, 'producto')
        self.assertFalse(sin_pdf.classification_result)
        self.assertFalse(sin_pdf.reading_warning)
        self.assertFalse(sin_pdf.reading_signature)

        sin_excel = self._make_wizard(excel=False)
        with self.assertRaises(UserError) as ctx:
            sin_excel.action_preview_document()
        self.assertIn('Archivo Excel requerido', str(ctx.exception))
        self.assertEqual(sin_excel.state, 'draft')
        self.assertFalse(sin_excel.reading_signature)

        volume_vacio = self._make_wizard(modality='volume', tipo='granel',
                                         excel=False, pdf=False)
        with self.assertRaises(UserError) as ctx:
            volume_vacio.action_preview_document()
        self.assertIn('al menos un documento', str(ctx.exception))
        self.assertEqual(volume_vacio.state, 'draft')
        self.assertFalse(volume_vacio.reading_signature)

    # ── T-2D-9: documentos requeridos por modalidad + contrato de vista ────
    def test_t2d_9_documentos_requeridos_y_contrato_de_vista(self):
        solo_pdf = self._make_wizard(excel=False)
        self.assertFalse(solo_pdf.has_required_documents)
        completo = self._make_wizard()
        self.assertTrue(completo.has_required_documents)
        volumen = self._make_wizard(modality='volume', tipo='granel',
                                    excel=False)
        self.assertTrue(volumen.has_required_documents)
        volumen_vacio = self._make_wizard(modality='volume', tipo='granel',
                                          excel=False, pdf=False)
        self.assertFalse(volumen_vacio.has_required_documents)

        root = etree.fromstring(self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_wizard_form').arch)
        boton = root.xpath("//button[@name='action_preview_document']")
        self.assertEqual(len(boton), 1)
        self.assertIn('has_required_documents', boton[0].get('invisible'))
        # Campos de procedencia y aviso visibles en el formulario.
        self.assertTrue(root.xpath("//field[@name='profile_origin']"))
        self.assertTrue(root.xpath("//field[@name='profile_suggested']"))
        self.assertTrue(root.xpath("//field[@name='profile_mismatch_hint']"))
        badge = root.xpath("//div[contains(@class, 'text-info')]")
        self.assertTrue(any(
            "profile_origin != 'suggested'" == node.get('invisible')
            for node in badge
        ))

