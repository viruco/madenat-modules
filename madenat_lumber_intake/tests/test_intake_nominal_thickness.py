# -*- coding: utf-8 -*-
"""
TESTS: Espesor nominal declarado por el documento (FASE 13/2B, Paso 2)

Cobertura:
  1. Helpers puros: glosa «de 45mm», aritmética del volumen, coherencia y
     plausibilidad del volumen declarado.
  2. Guía 40030 (packing 38,1 mm + guía «de 45mm»): escribe nominal 45 y la
     compra pasa a 54.518 m³ sin mover el embarque (44.713 m³).
  3. Packing que ya declara 45 mm: no escribe nada.
  4. Sin evidencia (sin glosa y sin volumen): no escribe y deja la marca.
  5. Valor del operador (nominal ≠ físico): prevalece.
  6. Glosa y aritmética incoherentes: no escribe y avisa.
"""
import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module
from odoo.addons.madenat_lumber_intake.models.intake_nominal import (
    nominal_from_text,
    nominal_from_volume,
    resolve_nominal,
    volume_is_plausible,
)


# (paquete, ancho_mm, piezas, volumen documental m³, embarque m³)
PACKAGES_40030 = (
    (1, 170.0, 150, 3.8862, 3.886),
    (2, 170.0, 150, 3.8862, 3.886),
    (3, 150.0, 175, 4.0005, 3.895),
    (4, 150.0, 175, 4.0005, 3.895),
    (5, 125.0, 200, 3.81, 3.677),
    (6, 125.0, 200, 3.81, 3.677),
    (7, 125.0, 200, 3.81, 3.677),
    (8, 125.0, 200, 3.81, 3.677),
    (9, 125.0, 200, 3.81, 3.677),
    (10, 125.0, 200, 3.81, 3.677),
    (11, 100.0, 250, 3.81, 3.629),
    (12, 75.0, 325, 3.71475, 3.460),
)

GUIA_40030_TEXT = (
    'SOCIEDAD FORESTAL AGRICOLA COMERCIAL E\n'
    'GUIA DE DESPACHO ELECTRONICA\n'
    '3322 M3 54,518 Madera de Pino Radiata Cepillada Calidad Col A de 45mm\n'
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeNominalThickness(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rule = cls.env['madenat.lumber.product.default']
        cls.Product = cls.env['product.product']
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product_fijo = cls.Product.create({
            'name': 'Producto Maestro 2B Paso2',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor 2B Paso2',
            'is_company': True,
            'supplier_rank': 1,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.Rule.search([]).write({'active': False})
        cls.Rule.create({'tipo_ingreso': 'bruta', 'product_id': cls.product_fijo.id})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _create_reception(self):
        return self.env['lumber.reception'].create({
            'name': 'TEST-2B-NOM',
            'supplier_id': self.partner.id,
            'ingestion_profile': 'f1550',
            'excel_file': base64.b64encode(b'packing').decode(),
            'excel_filename': 'packing.xlsx',
        })

    def _fill_staging(self, reception, thickness, nominal):
        lines = []
        for package_no, width_mm, pieces, volumen, _embarque in PACKAGES_40030:
            lines.append({
                'product_code': 'PKG-%02d' % package_no,
                'product_name': 'MADERA SECA CEPILLADA',
                'package_no': package_no,
                'pieces': pieces,
                'volume_m3': volumen,
                'thickness_mm': thickness,
                'width_mm': width_mm,
                'length_m': 4.0,
                'thickness_nominal': nominal,
                'width_nominal': width_mm,
            })
        reception._fill_staging_table({'lines': lines})

    def _create_wizard(self):
        return self.env['madenat.lumber.intake.wizard'].create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'ingestion_profile': 'f1550',
            'excel_file': base64.b64encode(b'excel').decode(),
            'excel_filename': 'packing.xlsx',
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })

    def _apply(self, wizard, reception, guia_text, declared):
        with patch.object(
                intake_wizard_module.MadenatLumberIntakeWizard,
                '_extract_pdf_text_safe', return_value=guia_text), \
                patch.object(
                    intake_wizard_module.MadenatLumberIntakeWizard,
                    '_declared_purchase_volume', return_value=declared):
            return wizard._apply_document_nominal_thickness(reception)

    # ── Helpers puros ──────────────────────────────────────────────────────
    def test_01_glosa(self):
        self.assertEqual(nominal_from_text(GUIA_40030_TEXT), 45.0)
        self.assertEqual(nominal_from_text('MADERA DE 38,1 MM'), 38.1)
        self.assertIsNone(nominal_from_text('sin glosa'))
        self.assertIsNone(nominal_from_text('de 45mm y de 38mm'))

    def test_02_aritmetica_y_plausibilidad(self):
        geo = [
            {'width': width, 'length': 4.0, 'pieces': pieces}
            for _n, width, pieces, _v, _e in PACKAGES_40030
        ]
        self.assertAlmostEqual(nominal_from_volume(54.518, geo), 45.0, places=1)
        self.assertIsNone(nominal_from_volume(0.0, geo))
        self.assertTrue(volume_is_plausible(54.518, 46.158))
        self.assertFalse(volume_is_plausible(54.518, 0.0))
        self.assertFalse(volume_is_plausible(54.518, 20.0))

    def test_03_resolver(self):
        self.assertEqual(resolve_nominal(45.0, 45.0, 38.1), 45.0)
        self.assertEqual(resolve_nominal(None, 45.0, 38.1), 45.0)
        self.assertIsNone(resolve_nominal(38.0, 45.0, 38.1))
        self.assertIsNone(resolve_nominal(None, 30.0, 38.1))
        self.assertIsNone(resolve_nominal(None, None, 38.1))

    # ── Integración sobre el staging ───────────────────────────────────────
    def test_04_40030_escribe_nominal_y_compra_54518(self):
        reception = self._create_reception()
        self._fill_staging(reception, thickness=38.1, nominal=38.1)
        wizard = self._create_wizard()
        self.assertTrue(
            self._apply(wizard, reception, GUIA_40030_TEXT, 54.518))
        lines = reception.reception_line_ids
        self.assertEqual(set(lines.mapped('thickness_nominal')), {45.0})
        self.assertAlmostEqual(
            sum(lines.mapped('vol_purchase_m3')), 54.518, places=3)
        self.assertAlmostEqual(
            sum(lines.mapped('vol_shipment_m3')), 44.713, places=3)

    def test_05_packing_que_ya_trae_45_no_cambia(self):
        reception = self._create_reception()
        self._fill_staging(reception, thickness=45.0, nominal=45.0)
        wizard = self._create_wizard()
        self.assertFalse(
            self._apply(wizard, reception, GUIA_40030_TEXT, 47.152))
        self.assertEqual(
            set(reception.reception_line_ids.mapped('thickness_nominal')),
            {45.0})

    def test_06_sin_evidencia_no_escribe_y_marca(self):
        reception = self._create_reception()
        self._fill_staging(reception, thickness=38.1, nominal=38.1)
        wizard = self._create_wizard()
        self.assertFalse(self._apply(wizard, reception, '', 0.0))
        self.assertTrue(wizard.has_reading_warning)
        self.assertIn('Espesor nominal no resuelto', wizard.reading_warning)
        self.assertEqual(
            set(reception.reception_line_ids.mapped('thickness_nominal')),
            {38.1})

    def test_07_valor_del_operador_prevalece(self):
        reception = self._create_reception()
        self._fill_staging(reception, thickness=38.1, nominal=38.1)
        reception.reception_line_ids.write({'thickness_nominal': 50.0})
        wizard = self._create_wizard()
        self.assertFalse(
            self._apply(wizard, reception, GUIA_40030_TEXT, 54.518))
        self.assertEqual(
            set(reception.reception_line_ids.mapped('thickness_nominal')),
            {50.0})

    def test_08_glosa_incoherente_no_escribe(self):
        reception = self._create_reception()
        self._fill_staging(reception, thickness=38.1, nominal=38.1)
        wizard = self._create_wizard()
        self.assertFalse(
            self._apply(wizard, reception, 'Madera Cepillada de 38mm', 54.518))
        self.assertTrue(wizard.has_reading_warning)
        self.assertEqual(
            set(reception.reception_line_ids.mapped('thickness_nominal')),
            {38.1})
