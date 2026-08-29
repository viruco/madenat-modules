# -*- coding: utf-8 -*-
"""Tests del retorno canónico a Ingreso de Madera (FIX 2026-08-21).

Verifica el contrato de acción, el flag `context.no_breadcrumbs` emitido por
backend, su propagación vía delegación, y la no-regresión de la apertura de
origen (que NO incorpora el flag de forma involuntaria).
Usa TransactionCase: nada se persiste.
"""
import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models.intake_constants import CONSOLE_ID_OFFSET


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeNavigationActions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guia_model = cls.env['madenat.guia.processing']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Nav Test',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        ) or cls.env['stock.location'].search([], limit=1)
        cls.guia = cls.guia_model.create({
            'name': 'NAV-TEST-1',
            'partner_id': cls.partner.id,
            'assignment_location_id': cls.location.id,
            'tipo_recepcion': 'service',
        })

    def test_get_intake_console_action_contract(self):
        action = self.guia._get_intake_console_action()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(action['res_id'], CONSOLE_ID_OFFSET + self.guia.id)
        self.assertEqual(action['target'], 'current')
        # FIX TITULO ACTIVO (2026-08-22): el name canónico del controller
        # activo final tras el replace debe ser exactamente el de la acción
        # de menú de Ingreso de Madera ('Ingreso de Madera'), no el display_name de
        # la guía. Evita que el header conserve el título de la ficha.
        # FIX ACCESO (2026-08-22): el name se fija literalmente para que el
        # helper no lea ir.actions.act_window (Operaciones carece de
        # base.group_system y env.ref provoca AccessError en el retorno).
        self.assertEqual(action['name'], 'Ingreso de Madera')
        # ROLLBACK 2026-08-22: contrato de FORMULARIO (fachada operativa de
        # Ingreso de Madera para envío a stock). Sin lista como vista inicial.
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(
            action['view_id'],
            self.env.ref(
                'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
            ).id,
        )
        self.assertEqual(
            action['views'], [(action['view_id'], 'form')])
        self.assertNotIn('list', action['view_mode'].split(','))

    def test_get_intake_console_action_does_not_emit_no_breadcrumbs(self):
        # Post-rollback: el retorno NO oculta breadcrumb (UAT: navegación
        # quedaba vacía/incorrecta con el flag). Contrato funcional intacto.
        action = self.guia._get_intake_console_action()
        self.assertNotIn('no_breadcrumbs', (action.get('context') or {}))

    def test_action_back_to_intake_console_wraps_in_client_action(self):
        result = self.guia.action_back_to_intake_console()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(
            result['tag'], 'madenat_lumber_intake.replace_current_action')
        inner = result['params']['action_to_execute']
        self.assertEqual(inner['type'], 'ir.actions.act_window')
        self.assertEqual(inner['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(inner['res_id'], CONSOLE_ID_OFFSET + self.guia.id)
        self.assertEqual(inner['target'], 'current')
        self.assertTrue(inner['name'])
        self.assertEqual(inner['view_mode'], 'form')
        self.assertEqual(inner['views'], [(inner['view_id'], 'form')])
        self.assertNotIn('list', inner['view_mode'].split(','))
        self.assertNotIn('no_breadcrumbs', inner.get('context', {}))

    def test_back_to_intake_console_as_operator_has_access(self):
        """Operaciones (sin base.group_system) no debe recibir AccessError
        al ejecutar el retorno a Ingreso de Madera desde Procesado."""
        operator = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Operador Intake Nav',
            'login': 'operator_intake_nav_test',
            'groups_id': [(6, 0, [self.env.ref(
                'madenat_lumber_core.group_madenat_operaciones').id])],
        })
        self.assertFalse(
            operator.has_group('base.group_system'),
            'El operador de prueba no debe pertenecer a base.group_system',
        )
        # Helper directo sin AccessError.
        action = self.guia.with_user(operator)._get_intake_console_action()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['name'], 'Ingreso de Madera')
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(action['res_id'], CONSOLE_ID_OFFSET + self.guia.id)
        self.assertEqual(action['target'], 'current')
        # Acción pública de retorno sin AccessError.
        wrapped = self.guia.with_user(operator).action_back_to_intake_console()
        self.assertEqual(wrapped['type'], 'ir.actions.client')
        self.assertEqual(wrapped['tag'], 'madenat_lumber_intake.replace_current_action')
        self.assertEqual(
            wrapped['params']['action_to_execute']['name'], 'Ingreso de Madera')

    def test_back_to_intake_console_product_wraps_in_client_action(self):
        """Producto replica el patrón de Procesado (espejo client action).

        El retorno desde lumber.reception debe envolver la acción interna en
        madenat_lumber_intake.replace_current_action y conservar el id de
        consola SIN offset (regla vista SQL para lumber.reception).
        """
        reception = self.env['lumber.reception'].create({
            'name': 'PROD-NAV-TEST-1',
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx',
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
            'ingestion_profile': 'metric',
        })
        action = reception.action_back_to_intake_console()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(
            action['tag'], 'madenat_lumber_intake.replace_current_action')
        inner = action['params']['action_to_execute']
        self.assertEqual(inner['type'], 'ir.actions.act_window')
        self.assertEqual(inner['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(inner['res_id'], reception.id)
        self.assertEqual(inner['target'], 'current')
        self.assertEqual(
            inner['view_id'],
            self.env.ref(
                'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
            ).id,
        )
        self.assertEqual(inner['views'], [(inner['view_id'], 'form')])

    def test_open_source_wraps_in_client_action(self):
        console = self.env['madenat.lumber.intake.console'].browse(
            CONSOLE_ID_OFFSET + self.guia.id)
        result = console.action_open_source()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(
            result['tag'], 'madenat_lumber_intake.replace_current_action')
        inner = result['params']['action_to_execute']
        self.assertEqual(inner['type'], 'ir.actions.act_window')
        self.assertEqual(inner['res_model'], 'madenat.guia.processing')
        self.assertEqual(inner['res_id'], self.guia.id)
        self.assertEqual(inner['target'], 'current')
        self.assertEqual(inner['views'], [(inner['view_id'], 'form')])
        # FIX CABECERA GUIA ORIGEN: la apertura desactiva SOLO la creación
        # (context create=0) para no mostrar botón "Nuevo" en el header;
        # sin no_breadcrumbs y sin tocar el retorno a Ingreso de Madera.
        self.assertEqual((inner.get('context') or {}).get('create'), 0)
        self.assertNotIn('no_breadcrumbs', inner.get('context', {}))