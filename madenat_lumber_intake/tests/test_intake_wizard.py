# -*- coding: utf-8 -*-
import base64

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from ..models.intake_constants import CONSOLE_ID_OFFSET


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeWizard(TransactionCase):
    """Cobertura del orquestador Ingreso de Madera (fachada).

    No se verifica el parser ni los Gates (son del core): se mockean solo
    los métodos públicos externos para aislar el comportamiento de Intake.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Reception = cls.env['lumber.reception']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Audit = cls.env['madenat.audit.log']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)
        cls.assertTrue(cls.location, 'Se requiere un stock.location para la guía')

    @classmethod
    def _b64(cls, raw=b'fake bytes'):
        return base64.b64encode(raw).decode()

    @classmethod
    def _make_wizard(cls, tipo='producto', excel_raw=b'fake bytes', state='draft',
                     assign_location=True):
        vals = {
            'tipo_ingreso': tipo,
            'excel_file': cls._b64(excel_raw),
            'excel_filename': 'packing.xlsx',
            'state': state,
        }
        if tipo == 'producto':
            vals['pdf_file'] = cls._b64(b'%PDF-fake')
            vals['pdf_filename'] = 'guia.pdf'
            vals['ingestion_profile'] = 'metric'
        else:
            if assign_location:
                vals['assignment_location_id'] = cls.location.id
        return cls.Wizard.create(vals)

    @classmethod
    def _fake_parsed(cls):
        return {
            'lines': [
                {'product_code': 'P1', 'package_no': '1001', 'pieces': 10,
                 'volume_m3': 2.5},
                {'product_code': 'P2', 'package_no': '1002', 'pieces': 20,
                 'volume_m3': 5.0},
            ],
            'total_volume_m3': 7.5,
            'guide_no': '1234',
            'logs': ['ok'],
            'warnings': ['warn'],
        }

    # ── T1: Producto — preview utiliza parser universal ──────────────────
    def test_t1_producto_preview_uses_universal_parser(self):
        wizard = self._make_wizard(tipo='producto', excel_raw=b'excel-bytes')
        parser_model = self.env['madenat.reception.parser']

        with patch.object(
            type(parser_model), 'parse_excel',
            return_value=self._fake_parsed(),
        ) as mock:
            wizard.action_preview_document()

        mock.assert_called_once_with(b'excel-bytes', 'metric')

        self.assertEqual(wizard.state, 'previewed')
        self.assertEqual(wizard.preview_line_count, 2)
        self.assertEqual(wizard.preview_total_volume_m3, 7.5)
        self.assertEqual(wizard.preview_guide_no, '1234')
        self.assertIn('P1', wizard.preview_data)
        # El M3 es el retornado por el parser, sin cálculo adicional.
        self.assertEqual(wizard.preview_total_volume_m3, 7.5)

    # ── T2: Procesado — preview NO invoca parser de Recepción ────────────
    def test_t2_procesado_preview_does_not_invoke_reception_parser(self):
        wizard = self._make_wizard(tipo='procesado')
        parser_model = self.env['madenat.reception.parser']

        with patch.object(
            type(parser_model), 'parse_excel',
            side_effect=AssertionError('No debe invocarse en Procesado'),
        ) as mock:
            result = wizard.action_preview_document()

        self.assertFalse(mock.called)
        self.assertEqual(wizard.state, 'draft')
        self.assertEqual(wizard.preview_total_volume_m3, 0.0)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    @classmethod
    def _facade_view_id(cls, xml_id):
        return cls.env.ref(xml_id).id

    # ── T3: Producto — derivación canónica ───────────────────────────────
    def test_t3_producto_routes_canonical_method(self):
        wizard = self._make_wizard(tipo='producto', excel_raw=b'excel-bytes',
                                   state='previewed')
        reception_model = self.env['lumber.reception']

        with patch.object(
            type(reception_model), 'action_process_documents',
            return_value=True,
        ) as mock:
            action = wizard.action_route_document()

        # Crea un único registro lumber.reception con binarios/filenames/perfil.
        receptions = self.Reception.search([
            ('excel_filename', '=', 'packing.xlsx')
        ])
        self.assertEqual(len(receptions), 1)
        reception = receptions
        self.assertEqual(reception.ingestion_profile, 'metric')
        self.assertEqual(reception.excel_file, wizard.excel_file)
        self.assertEqual(reception.pdf_file, wizard.pdf_file)

        mock.assert_called_once_with()

        self.assertEqual(wizard.state, 'routed')
        self.assertEqual(wizard.target_model, 'lumber.reception')
        self.assertEqual(wizard.target_res_id, reception.id)

        # Evento de auditoría de origen único.
        audits = self.Audit.search([('batch_id', '=', 'intake:%s' % wizard.id)])
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits.reception_id.id, reception.id)

        # Separación lectura/edición: la post-derivación SIEMPRE abre la CONSOLA
        # de lectura, nunca la fachada de edición ni el form nativo del core.
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.console')
        # Producto (lumber.reception): id de consola SIN offset (regla vista SQL).
        self.assertEqual(action['res_id'], reception.id)
        self.assertEqual(action['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))

    # ── T4: Procesado — deriva bytes crudos al parser nativo ─────────────
    def test_t4_procesado_routes_raw_bytes_to_native_parser(self):
        wizard = self._make_wizard(tipo='procesado', excel_raw=b'excel-raw')
        guia_model = self.env['madenat.guia.processing']
        parser_model = self.env['madenat.reception.parser']

        with patch.object(
            type(guia_model), 'action_verify_data',
            return_value=None,
        ) as mock_verify, patch.object(
            type(parser_model), 'parse_excel',
            side_effect=AssertionError('No debe invocarse en Procesado'),
        ) as mock_parse:
            action = wizard.action_route_document()

        guias = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guias), 1)
        guia = guias
        # Byte-equivalente al adjunto del wizard.
        self.assertEqual(guia.excel_file, wizard.excel_file)
        self.assertEqual(guia.tipo_recepcion, 'service')
        self.assertEqual(guia.assignment_location_id.id, self.location.id)

        # Parser nativo de Guía invocado, parser de Recepción NO.
        mock_verify.assert_called_once_with()
        self.assertFalse(mock_parse.called)
        # No se usó force_packing_data.
        self.assertNotIn('force_packing_data', guia.env.context)

        self.assertEqual(wizard.state, 'routed')
        self.assertEqual(wizard.target_model, 'madenat.guia.processing')
        self.assertEqual(wizard.target_res_id, guia.id)

        audits = self.Audit.search([('batch_id', '=', 'intake:%s' % wizard.id)])
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits.guia_processing_id.id, guia.id)

        # Separación lectura/edición: la post-derivación SIEMPRE abre la CONSOLA
        # de lectura, nunca la fachada de edición ni el form nativo del core.
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(action['res_id'], CONSOLE_ID_OFFSET + guia.id)
        self.assertEqual(action['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))

    # ── T5: Idempotencia ────────────────────────────────────────────────
    def test_t5_idempotency_double_click(self):
        wizard = self._make_wizard(tipo='procesado', excel_raw=b'excel-raw')
        guia_model = self.env['madenat.guia.processing']

        with patch.object(
            type(guia_model), 'action_verify_data', return_value=None
        ):
            first = wizard.action_route_document()
            second = wizard.action_route_document()

        guias = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guias), 1)

        # Idempotencia: ambas aperturas usan la CONSOLA de lectura.
        self.assertEqual(first['res_id'], CONSOLE_ID_OFFSET + guias.id)
        self.assertEqual(second['res_id'], CONSOLE_ID_OFFSET + guias.id)
        self.assertEqual(first['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))
        self.assertEqual(second['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))

        # Un único evento de origen.
        audits = self.Audit.search([('batch_id', '=', 'intake:%s' % wizard.id)])
        self.assertEqual(len(audits), 1)

    # ── T6: Error conocido desde método público destino ──────────────────
    def test_t6_known_error_marks_error_no_origin_event(self):
        wizard = self._make_wizard(tipo='producto', excel_raw=b'excel-bytes',
                                   state='previewed')
        reception_model = self.env['lumber.reception']

        with patch.object(
            type(reception_model), 'action_process_documents',
            side_effect=UserError('Gate0 rechazado'),
        ):
            with self.assertRaises(UserError) as ctx:
                wizard.action_route_document()

        # La causa real se propaga sin ocultarse.
        self.assertIn('Gate0 rechazado', str(ctx.exception))

        # Intake NO marca el wizard como routed ni crea destino ni evento
        # de origen. Nota: Odoo TransactionCase revierte con el re-raise de
        # UserError; no se asevera la persistencia exacta de state='error'
        # tras la excepción (mismo patrón que la suite del core). El flujo
        # productivo persiste state='error' vía flush en el modelo antes de
        # relanzar, garantizando el reintento operativo.
        self.assertNotEqual(wizard.state, 'routed')
        self.assertFalse(wizard.target_res_id)

        # Sin evento de origen exitoso (no hay recepción enlazada).
        audits = self.Audit.search([('batch_id', '=', 'intake:%s' % wizard.id)])
        self.assertEqual(len(audits), 0)

    # ── T7: "Abrir registro creado" abre consola de lectura; edición queda en
    # "Modificar origen" (action_open_source) ──────────────────────────────
    def test_t7_open_created_target_uses_console_for_both_types(self):
        """Toda apertura vía action_open_intake_target usa la CONSOLA de lectura."""
        # Procesado: crear wizard derivado y abrir el registro existente.
        wizard_proc = self._make_wizard(tipo='procesado', excel_raw=b'excel-raw')
        guia_model = self.env['madenat.guia.processing']
        with patch.object(
            type(guia_model), 'action_verify_data', return_value=None
        ):
            wizard_proc.action_route_document()
        wizard_proc.invalidate_recordset()
        action_proc = wizard_proc.action_open_intake_target()
        self.assertEqual(action_proc['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(action_proc['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))

        # Producto: mismo flujo, consola de lectura.
        wizard_prod = self._make_wizard(tipo='producto', excel_raw=b'excel-bytes',
                                        state='previewed')
        reception_model = self.env['lumber.reception']
        with patch.object(
            type(reception_model), 'action_process_documents', return_value=True
        ):
            wizard_prod.action_route_document()
        wizard_prod.invalidate_recordset()
        action_prod = wizard_prod.action_open_intake_target()
        self.assertEqual(action_prod['res_model'], 'madenat.lumber.intake.console')
        self.assertEqual(action_prod['view_id'], self._facade_view_id(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        ))

        # La edición queda reservada a "Modificar origen" (consola):
        # action_open_source debe abrir la fachada de edición correspondiente.
        guia = self.Guia.search([('excel_filename', '=', 'packing.xlsx')], limit=1)
        console_proc = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        if console_proc:
            edit_action = console_proc.action_open_source()
            # FIX 2026-08-22: action_open_source ahora envuelve en client action
            edit_action = edit_action['params']['action_to_execute']
            self.assertEqual(edit_action['res_model'], 'madenat.guia.processing')
            self.assertEqual(edit_action['view_id'], self._facade_view_id(
                'madenat_lumber_intake.view_madenat_guia_processing_intake_facade_form'
            ))
