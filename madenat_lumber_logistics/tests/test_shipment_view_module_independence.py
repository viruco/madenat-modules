# -*- coding: utf-8 -*-
"""T6 — Independencia de módulos: Logistics no referencia XML IDs de Billing.

`madenat_lumber_logistics` es módulo base respecto de `madenat_lumber_billing`
(Billing depende de Logistics). Un módulo base NUNCA debe referenciar XML IDs
declarados únicamente por su dependiente: hacerlo impide la instalación limpia
de Logistics sin Billing.

El defecto histórico era el botón de Consolidación en la vista de Embarque
(`name="%(madenat_lumber_billing.action_create_consolidation_from_shipment)d"`).
La funcionalidad se trasladó a una vista heredada propiedad de Billing.
"""
import os

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics',
        't6_module_independence')
class TestShipmentViewModuleIndependence(TransactionCase):
    """Independencia XML de Logistics frente a Billing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ShipmentModel = cls.env['lumber.export.shipment']
        cls.view = cls.env.ref(
            'madenat_lumber_logistics.view_lumber_export_shipment_form')

    def _source_xml_path(self):
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(module_dir, 'views', 'lumber_export_shipment_views.xml')

    def test_01_xml_fuente_sin_referencia_billing(self):
        """El XML fuente de Logistics no puede citar XML IDs de Billing."""
        path = self._source_xml_path()
        self.assertTrue(os.path.exists(path), 'Falta el XML fuente de Embarques')
        with open(path, 'r', encoding='utf-8') as fh:
            source = fh.read()
        self.assertNotIn(
            'madenat_lumber_billing', source,
            'La vista de Embarque de Logistics no debe referenciar XML IDs de Billing')

    def test_02_vista_registrada_sin_referencia_billing(self):
        """La vista almacenada en BD (propiedad de Logistics) no cita Billing."""
        arch_db = self.view.arch_db or ''
        if isinstance(arch_db, dict):  # campo traducible leído como dict
            arch_db = ' '.join(str(v) for v in arch_db.values())
        self.assertNotIn(
            'madenat_lumber_billing', arch_db,
            'La vista raíz de Logistics no debe contener referencias a Billing')

    def test_03_vista_form_renderiza_y_valida(self):
        """La vista de Embarque se valida/renderiza.

        Es la misma ruta que abortaba la instalación limpia cuando el XML ID de
        Billing no existía en el sistema.
        """
        arch = self.ShipmentModel.get_view(
            view_id=self.view.id, view_type='form')['arch']
        self.assertTrue(arch)
        root = etree.fromstring(
            arch if isinstance(arch, bytes) else arch.encode('utf-8'))
        self.assertEqual(root.tag, 'form')
