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
