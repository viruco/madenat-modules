# -*- coding: utf-8 -*-
"""Pruebas para WP-B — Unificación de rótulos de volumen en Logística.

FASE 12 — Bloque 1 (WP-B rótulos):
- "Vol. Compra (m³)" para el volumen de compra por etiqueta y totales asociados.
- "Vol. Export (m³)" para el volumen de exportación/embarque.
- "Vol. Documental (m³)" claramente distinguido en las imputaciones documentales SV.
"""
from lxml import etree
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestVolumeLabelsUnification(TransactionCase):

    def _get_tree(self, xml_id):
        view = self.env.ref(xml_id)
        return etree.fromstring(view.arch)

    def test_01_container_tree_labels(self):
        """Verifica rótulos unificados en la vista lista de contenedores."""
        tree = self._get_tree('madenat_lumber_logistics.view_lumber_container_list')
        export_field = tree.xpath("//field[@name='total_vol_shipment_m3']")
        purchase_field = tree.xpath("//field[@name='total_volume_purchase_m3']")

        self.assertTrue(export_field, "Debe existir total_vol_shipment_m3")
        self.assertEqual(export_field[0].attrib.get('string'), 'Vol. Export (m³)')

        self.assertTrue(purchase_field, "Debe existir total_volume_purchase_m3")
        self.assertEqual(purchase_field[0].attrib.get('string'), 'Vol. Compra (m³)')

    def test_02_container_form_labels(self):
        """Verifica rótulos unificados en el formulario de contenedor."""
        tree = self._get_tree('madenat_lumber_logistics.view_lumber_container_form')
        labels = {l.attrib.get('for'): l.attrib.get('string') for l in tree.xpath('//label')}

        self.assertEqual(labels.get('total_vol_shipment_m3'), 'Vol. Export (m³)')
        self.assertEqual(labels.get('total_volume_purchase_m3'), 'Vol. Compra (m³)')

        # Grilla de lotes asignados dentro del contenedor
        lot_fields = {
            f.attrib.get('name'): f.attrib.get('string')
            for f in tree.xpath("//page[@string='Lotes Asignados']//field")
        }
        self.assertIn('volume_purchase_m3', lot_fields)
        self.assertEqual(lot_fields['volume_purchase_m3'], 'Vol. Compra (m³)')
        self.assertIn('vol_shipment_m3', lot_fields)
        self.assertEqual(lot_fields['vol_shipment_m3'], 'Vol. Export (m³)')

    def test_03_lot_wizard_list_labels(self):
        """Verifica rótulos unificados en el asistente de selección de lotes."""
        tree = self._get_tree('madenat_lumber_logistics.view_stock_lot_shipping_wizard_list')
        fields = {f.attrib.get('name'): f.attrib.get('string') for f in tree.xpath('//field')}

        self.assertIn('volume_purchase_m3', fields)
        self.assertEqual(fields['volume_purchase_m3'], 'Vol. Compra (m³)')
        self.assertIn('vol_shipment_m3', fields)
        self.assertEqual(fields['vol_shipment_m3'], 'Vol. Export (m³)')

    def test_04_export_shipment_views_labels(self):
        """Verifica rótulos unificados en vistas de embarque (lista, formulario, pivot)."""
        # Pivot
        tree_pivot = self._get_tree('madenat_lumber_logistics.view_lumber_export_shipment_pivot')
        pivot_measures = {
            f.attrib.get('name'): f.attrib.get('string')
            for f in tree_pivot.xpath("//field[@type='measure']")
        }
        self.assertEqual(pivot_measures.get('total_nominal_volume_m3'), 'Vol. Compra (m³)')
        self.assertEqual(pivot_measures.get('total_volume_m3'), 'Vol. Export (m³)')

        # Lista
        tree_list = self._get_tree('madenat_lumber_logistics.view_lumber_export_shipment_list')
        shipment_vol = tree_list.xpath("//field[@name='total_volume_m3']")
        self.assertEqual(shipment_vol[0].attrib.get('string'), 'Vol. Export (m³)')

        # Formulario
        tree_form = self._get_tree('madenat_lumber_logistics.view_lumber_export_shipment_form')
        kpi_fields = {
            f.attrib.get('name'): f.attrib.get('string')
            for f in tree_form.xpath("//group[@string='Totales y KPIs']//field")
        }
        self.assertEqual(kpi_fields.get('total_volume_m3'), 'Vol. Export (m³)')
        self.assertEqual(kpi_fields.get('total_nominal_volume_m3'), 'Vol. Compra (m³)')

        # Pestaña contenedores
        container_cols = {
            f.attrib.get('name'): f.attrib.get('string')
            for f in tree_form.xpath("//page[@name='containers']//field")
        }
        self.assertEqual(container_cols.get('total_volume_purchase_m3'), 'Vol. Compra (m³)')
        self.assertEqual(container_cols.get('volume_m3'), 'Vol. Export (m³)')

        # Pestaña auditoría de cálculo
        audit_cols = {
            f.attrib.get('name'): f.attrib.get('string')
            for f in tree_form.xpath("//page[@name='audit_lines']//field")
        }
        self.assertEqual(audit_cols.get('physical_volume_m3'), 'Vol. Compra (m³)')
        self.assertEqual(audit_cols.get('export_volume_m3'), 'Vol. Export (m³)')

    def test_05_sv_documental_labels(self):
        """Verifica que el volumen documental SV se rotule como 'Vol. Documental (m³)'."""
        tree = self._get_tree('madenat_lumber_logistics.view_madenat_sv_assignment_list')
        doc_vol = tree.xpath("//field[@name='sv_assignment_nominal_m3']")
        self.assertTrue(doc_vol, "Debe existir sv_assignment_nominal_m3")
        self.assertEqual(doc_vol[0].attrib.get('string'), 'Vol. Documental (m³)')


