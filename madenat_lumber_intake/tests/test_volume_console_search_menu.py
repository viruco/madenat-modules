# -*- coding: utf-8 -*-
"""Pruebas para WP-C — Filtro, búsqueda y menú 'Ingresos por Volúmenes'.

FASE 12 — Bloque 1 (WP-C):
- Filtro y menú "Ingresos por Volúmenes" con búsqueda por guía, proveedor y estado.
- Acción dedicada pre-filtrada por modalidad volumen.
- Menú integrado bajo Gestión de Entradas (madenat_lumber_core.menu_ops_reception_cat).
"""
from lxml import etree
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeConsoleSearchMenu(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.search_view = cls.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_search'
        )

    def test_search_view_contains_guide_partner_state_and_volume_filter(self):
        """Verifica que la vista de búsqueda de la consola contenga los campos

        requeridos: guía, proveedor y estado, y el filtro 'Ingresos por Volúmenes'.
        """
        arch = self.search_view.arch
        tree = etree.fromstring(arch)

        # Campos de búsqueda
        fields_in_search = {
            f.attrib.get('name'): f.attrib.get('string', '')
            for f in tree.xpath('//search/field')
        }
        self.assertIn('guide_name', fields_in_search, "Debe existir búsqueda por Guía")
        self.assertIn('partner_id', fields_in_search, "Debe existir búsqueda por Proveedor")
        self.assertIn('state', fields_in_search, "Debe existir búsqueda por Estado")

        # Filtro de modalidad volumen
        vol_filters = tree.xpath("//search/filter[@name='type_volume']")
        self.assertTrue(vol_filters, "Debe existir el filtro type_volume")
        vol_filter = vol_filters[0]
        self.assertEqual(
            vol_filter.attrib.get('string'),
            'Ingresos por Volúmenes',
            "El rótulo del filtro debe ser 'Ingresos por Volúmenes'",
        )
        self.assertEqual(
            vol_filter.attrib.get('domain'),
            "[('ingestion_type', '=', 'volume')]",
            "El dominio del filtro debe ser [('ingestion_type', '=', 'volume')]",
        )

    def test_action_volume_intake_configured(self):
        """Verifica la existencia y configuración de la acción de ventana

        dedicada para 'Ingresos por Volúmenes'.
        """
        action = self.env.ref(
            'madenat_lumber_intake.action_madenat_lumber_intake_console_volume'
        )
        self.assertEqual(action.name, 'Ingresos por Volúmenes')
        self.assertEqual(action.res_model, 'madenat.lumber.intake.console')
        self.assertIn("'ingestion_type', '=', 'volume'", action.domain or '')
        self.assertIn("'search_default_type_volume': 1", action.context or '')

    def test_menu_volume_intake_configured(self):
        """Verifica la existencia y configuración del menú 'Ingresos por Volúmenes'."""
        menu = self.env.ref(
            'madenat_lumber_intake.menu_madenat_lumber_intake_volume'
        )
        self.assertEqual(menu.name, 'Ingresos por Volúmenes')
        expected_parent = self.env.ref('madenat_lumber_core.menu_ops_reception_cat')
        self.assertEqual(menu.parent_id, expected_parent)

        action = self.env.ref(
            'madenat_lumber_intake.action_madenat_lumber_intake_console_volume'
        )
        self.assertEqual(menu.action, action)

        expected_group = self.env.ref('madenat_lumber_core.group_madenat_operaciones')
        self.assertIn(expected_group, menu.groups_id)

    def test_console_orm_search_by_guide_partner_and_state(self):
        """Verifica que la consola admita búsquedas ORM por guide_name, partner_id y state."""
        records = self.Console.search([('ingestion_type', '=', 'volume')], limit=5)
        if records:
            rec = records[0]
            # Búsqueda por guía
            by_guide = self.Console.search([('guide_name', '=', rec.guide_name)])
            self.assertIn(rec, by_guide)

            # Búsqueda por proveedor
            if rec.partner_id:
                by_partner = self.Console.search([('partner_id', '=', rec.partner_id.id)])
                self.assertIn(rec, by_partner)

            # Búsqueda por estado
            by_state = self.Console.search([('state', '=', rec.state)])
            self.assertIn(rec, by_state)
