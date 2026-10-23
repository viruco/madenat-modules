# -*- coding: utf-8 -*-
"""Protege el contrato UI/XML del wizard de Intake sobre documentos.

- Volúmenes: pdf_file no debe tener required duro (comparte la condición de
  Excel: obligatorio solo en Ingreso normal).
- Ingreso normal: PDF/Guía y Excel siguen siendo obligatorios.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeWizardViewDocuments(TransactionCase):

    def _field_required(self, name):
        view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_wizard_form')
        root = etree.fromstring(view.arch)
        fields = root.xpath("//field[@name='%s']" % name)
        self.assertEqual(len(fields), 1, 'Campo %s no encontrado en la vista' % name)
        return fields[0].get('required')

    def test_volume_pdf_no_required_duro(self):
        """pdf_file en Volúmenes no exige PDF de forma incondicional."""
        self.assertEqual(
            self._field_required('pdf_file'), "intake_modality == 'normal'")

    def test_normal_pdf_y_excel_obligatorios(self):
        """Ingreso normal conserva PDF/Guía y Excel obligatorios."""
        self.assertEqual(
            self._field_required('pdf_file'), "intake_modality == 'normal'")
        self.assertEqual(
            self._field_required('excel_file'), "intake_modality == 'normal'")

    # ── Fase 2A: marca de advertencia y totales del packing ───────────────
    def _arch(self, xmlid):
        return etree.fromstring(self.env.ref(xmlid).arch)

    def test_marca_advertencia_visible_en_formulario(self):
        """La marca se muestra en el formulario (icono + texto), sin popup."""
        root = self._arch(
            'madenat_lumber_intake.view_madenat_lumber_intake_wizard_form')
        self.assertTrue(root.xpath("//field[@name='reading_warning']"))
        self.assertTrue(root.xpath("//field[@name='has_reading_warning']"))

    def test_totales_packing_en_vistas_de_fachada(self):
        """sum= en volumen de compra/exportación, MBF y costo (vistas intake)."""
        cases = (
            ('madenat_lumber_intake.view_lumber_reception_intake_facade_form',
             ('vol_purchase_m3', 'vol_shipment_m3', 'vol_mbf', 'cost_clp_unit')),
            ('madenat_lumber_intake.view_madenat_guia_processing_intake_facade_form',
             ('vol_purchase_m3', 'vol_shipment_m3')),
            ('madenat_lumber_intake.view_madenat_lumber_intake_console_form',
             ('vol_purchase_m3', 'vol_shipment_m3')),
        )
        for xmlid, fields in cases:
            root = self._arch(xmlid)
            for name in fields:
                nodes = root.xpath("//list//field[@name='%s'][@sum]" % name)
                self.assertTrue(nodes, '%s sin sum= en %s' % (name, xmlid))

