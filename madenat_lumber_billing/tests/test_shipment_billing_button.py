# -*- coding: utf-8 -*-
"""T6 — El botón de Consolidación de Facturación se aporta desde Billing.

La funcionalidad se conserva mediante una vista heredada PROPIEDAD DE BILLING
sobre la vista de Embarque de Logistics, sin crear dependencia
Logistics → Billing (que sería un ciclo).

La prueba valida la arquitectura de forma semántica: Odoo puede conservar el
XML ID literal del botón (`%(xmlid)d`) o representarlo por el ID numérico de la
acción en la arquitectura fusionada; ambas formas deben resolver exactamente a
`madenat_lumber_billing.action_create_consolidation_from_shipment`.
"""
from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_ACTION_XMLID = 'madenat_lumber_billing.action_create_consolidation_from_shipment'
_INHERITED_VIEW_XMLID = (
    'madenat_lumber_billing.view_lumber_billing_shipment_form_billing_button')
_BASE_VIEW_XMLID = 'madenat_lumber_logistics.view_lumber_export_shipment_form'
_BUTTON_LABEL = 'Crear Consolidación'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_billing',
        't6_module_independence')
class TestShipmentBillingButton(TransactionCase):
    """Botón de Consolidación aportado por Billing sobre la vista de Embarque."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ShipmentModel = cls.env['lumber.export.shipment']
        cls.action = cls.env.ref(_ACTION_XMLID)
        cls.inherited_view = cls.env.ref(_INHERITED_VIEW_XMLID)
        cls.base_view = cls.env.ref(_BASE_VIEW_XMLID)

    def _merged_arch_root(self):
        arch = self.ShipmentModel.get_view(
            view_id=self.base_view.id, view_type='form')['arch']
        return etree.fromstring(
            arch if isinstance(arch, bytes) else arch.encode('utf-8'))

    def _resolve_button_action(self, name):
        """Resuelve el `name` de un botón type=action a la acción referida.

        Acepta el XML ID literal (vista fuente) o el ID numérico ya resuelto
        (arquitectura fusionada). Nunca asume una representación concreta.
        """
        if not name:
            return self.env['ir.actions.actions']
        if name.startswith('%(') and name.endswith((')d', ')s')):
            return self.env.ref(name[2:-2])
        if name.isdigit():
            return self.env['ir.actions.actions'].browse(int(name)).exists()
        return self.env['ir.actions.actions']

    def test_01_vista_heredada_registrada(self):
        """La vista heredada existe y pertenece a Billing."""
        self.assertTrue(self.inherited_view, 'Falta la vista heredada de Billing')
        self.assertEqual(self.inherited_view.inherit_id, self.base_view)
        self.assertEqual(self.inherited_view.mode, 'extension')
        self.assertEqual(self.inherited_view.model, 'lumber.export.shipment')

    def test_02_boton_presente_y_resuelve_a_la_accion(self):
        """El botón 'Crear Consolidación' está presente, es type=action,
        resuelve exactamente a la acción de Billing y conserva su visibilidad."""
        root = self._merged_arch_root()
        buttons = [
            node for node in root.xpath('//button')
            if _BUTTON_LABEL in (node.get('string') or '')
        ]
        self.assertEqual(
            len(buttons), 1,
            'La vista de Embarque debe exponer un único botón Consolidación')
        button = buttons[0]
        self.assertEqual(button.get('type'), 'action')
        resolved = self._resolve_button_action(button.get('name'))
        self.assertTrue(
            resolved.exists(),
            'El botón debe resolver a una acción existente (name=%s)'
            % button.get('name'))
        self.assertEqual(
            resolved.id, self.action.id,
            'El botón debe apuntar exactamente a %s' % _ACTION_XMLID)
        self.assertEqual(
            button.get('invisible'), "state != 'delivered'",
            'El botón debe seguir visible solo en embarques entregados')

    def test_03_accion_vinculada_al_modelo(self):
        """La acción de Consolidación sigue definida y vinculada por Billing."""
        self.assertEqual(self.action.state, 'code')
        self.assertEqual(self.action.model_id.model, 'lumber.export.shipment')
        self.assertEqual(
            self.action.binding_model_id.model, 'lumber.export.shipment')
        self.assertEqual(self.action.binding_view_types, 'form')
