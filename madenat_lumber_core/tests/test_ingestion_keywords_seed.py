# -*- coding: utf-8 -*-
"""FASE 1 — Semilla de keywords de clasificación de tipo de ingreso.

Verifica la PARIDAD entre la configuración persistente sembrada por XML
(`madenat.tipo_ingreso_keywords`, noupdate=1) y el fallback Python histórico
de `madenat.ingestion.config.get_tipo_ingreso_keywords()`, **sin retirar**
todavía dicho fallback y sin alterar clasificación, parsers ni guards.

Cobertura T-KEY-01..06. Usa TransactionCase: nada se persiste.
"""
import io
import json
import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from odoo.addons.base.models.ir_config_parameter import IrConfigParameter

PARAM_KEY = 'madenat.tipo_ingreso_keywords'
SEED_XMLID_NAME = 'param_tipo_ingreso_keywords'

# Fallback Python histórico = equivalencia esperada. NO se elimina en Fase 1.
LEGACY_PROCESADO = ['cepillado', 'servicio', 'proceso', 'maquila']
LEGACY_GRANEL = ['granel', 'volumen total', 'a granel', 'sin desglose']


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core')
class TestIngestionKeywordsSeed(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env['madenat.ingestion.config']
        cls.Param = cls.env['ir.config_parameter'].sudo()

    def _param(self):
        return self.Param.search([('key', '=', PARAM_KEY)], limit=1)

    # ── T-KEY-01 ───────────────────────────────────────────────────────────
    def test_t_key_01_config_equals_legacy(self):
        """La config seed devuelve la MISMA lista normalizada que el hardcode."""
        self.assertTrue(self._param(), 'El seed %s debe existir' % PARAM_KEY)
        self.assertEqual(
            self.Config.get_tipo_ingreso_keywords('procesado'),
            LEGACY_PROCESADO)
        self.assertEqual(
            self.Config.get_tipo_ingreso_keywords('granel'),
            LEGACY_GRANEL)
        # 'producto' no tiene clave → [] (misma semántica que el hardcode).
        self.assertEqual(self.Config.get_tipo_ingreso_keywords('producto'), [])

    # ── T-KEY-02 ───────────────────────────────────────────────────────────
    def test_t_key_02_intake_classification_uses_seed(self):
        """Intake clasifica como Procesado con las keywords seed (por contenido)."""
        if not self.env['ir.module.module'].search_count([
                ('name', '=', 'madenat_lumber_intake'),
                ('state', '=', 'installed')]):
            self.skipTest('madenat_lumber_intake no está instalado.')
        from odoo.addons.madenat_lumber_intake.models import intake_wizard as iw
        wizard = self.env['madenat.lumber.intake.wizard'].create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
        })
        with patch.object(iw, '_extract_pdf_text',
                          return_value='SERVICIO DE CEPILLADO MADENAT'):
            wizard._classify_normal_document()
        self.assertEqual(wizard.tipo_ingreso, 'procesado')
        self.assertTrue(wizard.tipo_ingreso_auto_detectado)
        self.assertEqual(wizard.classification_result, 'Procesado')

    # ── T-KEY-03 ───────────────────────────────────────────────────────────
    def test_t_key_03_core_guard_still_blocks(self):
        """El guard Core sigue bloqueando Procesado por su contrato actual."""
        from odoo.addons.madenat_lumber_core.models.reception_workflow import (
            LumberReceptionWorkflow)
        wf = LumberReceptionWorkflow(self.env)
        blocked = self.env['lumber.reception'].new({
            'pdf_filename': 'guia cepillado.pdf',
            'excel_filename': 'packing.xlsx',
        })
        with self.assertRaises(UserError):
            wf._check_file_integrity(blocked)
        neutral = self.env['lumber.reception'].new({
            'pdf_filename': 'guia madera.pdf',
            'excel_filename': 'packing.xlsx',
        })
        self.assertIsNone(wf._check_file_integrity(neutral))

    # ── T-KEY-04 ───────────────────────────────────────────────────────────
    def test_t_key_04_update_does_not_overwrite_admin_change(self):
        """noupdate=1 ⇒ una actualización NO sobrescribe la edición admin.

        Si la política fuese 'la actualización restituye el valor canónico'
        (noupdate=0) este test NO aplicaría y el incremento debía detenerse.
        """
        imd = self.env['ir.model.data'].search([
            ('module', '=', 'madenat_lumber_core'),
            ('name', '=', SEED_XMLID_NAME),
        ], limit=1)
        self.assertTrue(imd, 'Debe existir el ir.model.data del seed')
        self.assertEqual(imd.model, 'ir.config_parameter')
        self.assertEqual(imd.res_id, self._param().id)
        # Mecanismo: noupdate=True ⇒ el loader omite el record en update.
        self.assertTrue(imd.noupdate, 'El seed debe ser noupdate=1 (editable)')

        # Simulación funcional: recargar el MISMO xmlid con OTRO valor y
        # noupdate="1" (mode='update') no debe tocar la edición admin.
        from odoo.tools import convert
        param = self._param()
        admin_value = '{"procesado": ["ADMIN"], "granel": ["ADMIN"]}'
        param.write({'value': admin_value})
        xml = (
            '<odoo><data noupdate="1">'
            '<record id="%s" model="ir.config_parameter">'
            '<field name="key">%s</field>'
            '<field name="value">{"procesado": ["SEED2"], "granel": ["SEED2"]}'
            '</field></record></data></odoo>'
        ) % (SEED_XMLID_NAME, PARAM_KEY)
        stream = io.StringIO(xml)
        stream.name = 'test_seed_reload.xml'
        convert.convert_xml_import(
            self.env, 'madenat_lumber_core', stream, mode='update')
        param.invalidate_recordset()
        self.assertEqual(
            self._param().value, admin_value,
            'noupdate=1 no debe sobrescribir la edición administrativa')

    # ── T-KEY-05 ───────────────────────────────────────────────────────────
    def test_t_key_05_seed_json_valid_and_typed(self):
        """JSON válido, tipo dict, claves y normalización correctas."""
        raw = self._param().value
        data = json.loads(raw)
        self.assertIsInstance(data, dict)
        self.assertEqual(set(data.keys()), {'procesado', 'granel'})
        for key in ('procesado', 'granel'):
            self.assertIsInstance(data[key], list)
            self.assertTrue(data[key])
            for kw in data[key]:
                self.assertIsInstance(kw, str)
                self.assertEqual(kw, kw.lower())
        # Equivalencia exacta (mismo orden y casing) con el hardcode.
        self.assertEqual(data['procesado'], LEGACY_PROCESADO)
        self.assertEqual(data['granel'], LEGACY_GRANEL)

    # ── T-KEY-06 ───────────────────────────────────────────────────────────
    def test_t_key_06_absence_keeps_fallback(self):
        """Ausencia de parámetro: fallback intacto (transición, sin cambios)."""
        from odoo.addons.madenat_lumber_core.models.reception_workflow import (
            LumberReceptionWorkflow)
        with patch.object(IrConfigParameter, 'get_param',
                          lambda self, key, default='': ''):
            self.assertEqual(
                self.Config.get_tipo_ingreso_keywords('procesado'),
                LEGACY_PROCESADO)
            self.assertEqual(
                self.Config.get_tipo_ingreso_keywords('granel'),
                LEGACY_GRANEL)
            # El guard Core sigue bloqueando con el fallback (transición).
            wf = LumberReceptionWorkflow(self.env)
            blocked = self.env['lumber.reception'].new({
                'pdf_filename': 'guia cepillado.pdf',
                'excel_filename': 'packing.xlsx',
            })
            with self.assertRaises(UserError):
                wf._check_file_integrity(blocked)

