# -*- coding: utf-8 -*-
import base64
import io

from types import SimpleNamespace
from unittest.mock import patch

from openpyxl import Workbook

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from ..models.intake_constants import CONSOLE_ID_OFFSET
from odoo.addons.madenat_lumber_intake.models import intake_classifier
from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module


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
    def _packing_excel_bytes(cls, thickness):
        """Genera un packing list sintético de una sola línea con el espesor
        indicado (mm métrico si >= 10, pulgadas imperial si < 10)."""
        header = [
            'N°', 'CODIGOS', 'PRODUCTO', 'LOTE', 'ESPESOR', 'ANCHO',
            'LARGO', 'FILAS', 'COLUMNAS', 'PIEZAS', 'VOLUMEN',
        ]
        row = [
            '1', '0000000000001', 'MADERA DE PRUEBA', 'LOTE-1',
            thickness, 170, 4.05, 25, 6, 150, 3.8862,
        ]
        wb = Workbook()
        ws = wb.active
        ws.append(header)
        ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    @classmethod
    def _excel_rows_bytes(cls, rows):
        """Genera un XLSX en memoria a partir de una lista de filas."""
        wb = Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    @classmethod
    def _make_wizard(cls, tipo='producto', excel_raw=b'fake bytes', state='draft',
                     assign_location=True):
        vals = {
            'tipo_ingreso': tipo,
            'excel_file': cls._b64(excel_raw),
            'excel_filename': 'packing.xlsx',
            'state': state,
            'pdf_file': cls._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
        }
        if tipo == 'producto':
            vals['ingestion_profile'] = 'metric'
        if assign_location:
            vals['assignment_location_id'] = cls.location.id
        return cls.Wizard.create(vals)

    # ── T1: Producto — preview utiliza extract_document del motor ─────────
    def test_t1_producto_preview_uses_extract_document(self):
        excel_raw = self._packing_excel_bytes(38.1)
        wizard = self._make_wizard(tipo='producto', excel_raw=excel_raw)

        result = wizard.action_preview_document()

        self.assertEqual(wizard.state, 'previewed')
        self.assertEqual(wizard.preview_line_count, 1)
        self.assertAlmostEqual(wizard.preview_total_volume_m3, 3.8862, places=4)
        self.assertIn('0000000000001', wizard.preview_data)
        # Sin etiqueta "guía despacho" en el Excel → guide_no queda vacío.
        self.assertFalse(wizard.preview_guide_no)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    # ── T2: Procesado — preview NO invoca extract_document ───────────────
    def test_t2_procesado_preview_does_not_invoke_extract_document(self):
        wizard = self._make_wizard(tipo='procesado')

        with patch.object(
            intake_wizard_module, 'extract_document',
            side_effect=AssertionError('No debe invocarse en Procesado'),
        ) as mock, patch.object(
            intake_wizard_module, '_extract_pdf_text',
            return_value='SERVICIO DE CEPILLADO MADENAT',
        ):
            result = wizard.action_preview_document()

        self.assertFalse(mock.called)
        self.assertEqual(wizard.state, 'draft')
        self.assertEqual(wizard.preview_total_volume_m3, 0.0)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    # ── Producto — Excel sin cabecera reconocible → error controlado ─────
    def test_preview_producto_sin_cabecera_error(self):
        """Sin cabecera reconocible: DocumentExtractionError → UserError + state=error."""
        excel_raw = self._excel_rows_bytes([
            ['foo', 'bar', 'baz'],
            ['1', '2', '3'],
        ])
        wizard = self._make_wizard(tipo='producto', excel_raw=excel_raw)

        with patch.object(
            type(wizard), 'write', return_value=True
        ) as mock_write:
            with self.assertRaises(UserError) as ctx:
                wizard.action_preview_document()

        # La causa (cabecera no reconocible) llega al mensaje de error.
        self.assertIn('cabecera', str(ctx.exception))

        # El método intenta persistir state='error' + error_message antes de
        # relanzar. TransactionCase revierte la escritura tras el re-raise
        # (mismo patrón que T6), por eso se valida sobre la llamada a write.
        error_writes = []
        for call_obj in mock_write.call_args_list:
            args = call_obj.args
            if args and isinstance(args[0], dict) and args[0].get('state') == 'error':
                error_writes.append(args[0])

        self.assertTrue(error_writes)
        self.assertTrue(error_writes[0].get('error_message'))

    # ── tipo_ingreso: default e onchange (normal no clasifica al adjuntar) ──
    def test_tipo_ingreso_default_and_onchange_intact(self):
        """Adjuntar documentos NO cambia tipo_ingreso en modalidad normal;
        la clasificación Producto/Procesado ocurre al ejecutar Leer documento."""
        wizard = self.Wizard.create({
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'guia cepillado.xlsx',
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })

        self.assertEqual(wizard.tipo_ingreso, 'producto')

        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'producto')

    # ── Trazabilidad de unidades en la consola (valor declarado + mm/m) ──
    def test_console_view_exposes_declared_dimensions(self):
        """La vista de consola expone el valor declarado junto al convertido."""
        view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
        )
        arch = view.arch
        # Producto (lumber.reception.line): valor documental original.
        self.assertIn('thickness_document_display', arch)
        self.assertIn('width_document_display', arch)
        self.assertIn('length_input_raw', arch)
        # Procesado (madenat.guia.processing.line): visual/imperial original.
        self.assertIn('thickness_visual', arch)
        self.assertIn('width_visual', arch)
        self.assertIn('length_ft', arch)

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

    # ─── Validación común de requisitos: Excel, PDF, Patio ────────────────
    # ── TC1: Producto sin PDF debe fallar ───────────────────────────────
    def test_tc1_producto_fails_without_pdf(self):
        """Validación común: Producto requiere PDF."""
        wizard = self._make_wizard(tipo='producto', state='previewed',
                                   assign_location=True)
        wizard.pdf_file = False
        wizard.pdf_filename = False

        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()

        self.assertIn('Guía/PDF requerido', str(ctx.exception))
        # No debe crear recepción
        receptions = self.Reception.search([
            ('excel_filename', '=', 'packing.xlsx')
        ])
        self.assertEqual(len(receptions), 0)

    # ── TC2: Producto sin Patio debe fallar ──────────────────────────────
    def test_tc2_producto_fails_without_patio(self):
        """Validación común: Producto requiere Patio."""
        wizard = self._make_wizard(tipo='producto', state='previewed',
                                   assign_location=False)
        wizard.assignment_location_id = False

        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()

        self.assertIn('Patio de Asignación', str(ctx.exception))
        # No debe crear recepción
        receptions = self.Reception.search([
            ('excel_filename', '=', 'packing.xlsx')
        ])
        self.assertEqual(len(receptions), 0)

    # ── TC3: Procesado sin PDF debe fallar ───────────────────────────────
    def test_tc3_procesado_fails_without_pdf(self):
        """Validación común: Procesado requiere PDF."""
        wizard = self._make_wizard(tipo='procesado', assign_location=True)
        wizard.pdf_file = False
        wizard.pdf_filename = False

        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()

        self.assertIn('Guía/PDF requerido', str(ctx.exception))
        # No debe crear guía
        guias = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guias), 0)

    # ── TC4: Procesado sin Patio debe fallar ─────────────────────────────
    def test_tc4_procesado_fails_without_patio(self):
        """Validación común: Procesado requiere Patio."""
        wizard = self._make_wizard(tipo='procesado', assign_location=False)
        wizard.assignment_location_id = False

        with self.assertRaises(UserError) as ctx:
            wizard.action_route_document()

        self.assertIn('Patio de Asignación', str(ctx.exception))
        # No debe crear guía
        guias = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guias), 0)

    # ── TC5: Producto transfiere location_id ──────────────────────────────
    def test_tc5_producto_transfers_location_id(self):
        """Mapeo: Intake assignment_location_id → lumber.reception.location_id."""
        wizard = self._make_wizard(tipo='producto', state='previewed',
                                   assign_location=True)
        reception_model = self.env['lumber.reception']

        with patch.object(
            type(reception_model), 'action_process_documents', return_value=True
        ):
            wizard.action_route_document()

        receptions = self.Reception.search([
            ('excel_filename', '=', 'packing.xlsx')
        ])
        self.assertEqual(len(receptions), 1)
        reception = receptions
        # Verificar que location_id se transfirió
        self.assertEqual(reception.location_id.id, self.location.id)
        self.assertEqual(reception.location_id.id, wizard.assignment_location_id.id)

    # ── TC6: Procesado siempre transfiere PDF ────────────────────────────
    def test_tc6_procesado_always_transfers_pdf(self):
        """Mapeo: Intake pdf_file/pdf_filename → madenat.guia.processing.guide_pdf_file/guide_pdf_filename."""
        wizard = self._make_wizard(tipo='procesado', assign_location=True)
        guia_model = self.env['madenat.guia.processing']

        with patch.object(
            type(guia_model), 'action_verify_data', return_value=None
        ):
            wizard.action_route_document()

        guias = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guias), 1)
        guia = guias
        # Verificar que PDF se transfirió
        self.assertEqual(guia.guide_pdf_file, wizard.pdf_file)
        self.assertEqual(guia.guide_pdf_filename, wizard.pdf_filename)

    # ── Sugerencia asistida de perfil de lectura (ingestion_profile) ──────
    # El onchange analiza el Excel real con extract_document() y sugiere
    # metric / f5085 / f1550; el caso imperial sin palabra clave solo advierte.

    def test_suggest_profile_metric_excel(self):
        """Excel métrico (espesor >= 10 mm) sugiere 'metric'."""
        wizard = self._make_wizard(
            tipo='producto',
            excel_raw=self._packing_excel_bytes(38.1),
        )
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertIsNone(result)

    def test_suggest_profile_imperial_blank_keyword(self):
        """Excel imperial + 'blank' en nombre sugiere 'f5085'."""
        wizard = self._make_wizard(
            tipo='producto',
            excel_raw=self._packing_excel_bytes(1.5625),
        )
        wizard.excel_filename = 'packing blank.xlsx'
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'f5085')
        self.assertIsNone(result)

    def test_suggest_profile_imperial_s2s_keyword(self):
        """Excel imperial + 's2s' en nombre sugiere 'f1550'."""
        wizard = self._make_wizard(
            tipo='producto',
            excel_raw=self._packing_excel_bytes(1.5625),
        )
        wizard.excel_filename = 'packing s2s.xlsx'
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'f1550')
        self.assertIsNone(result)

    def test_suggest_profile_imperial_no_keyword_warns(self):
        """Excel imperial sin palabra clave no cambia el valor y retorna warning."""
        wizard = self._make_wizard(
            tipo='producto',
            excel_raw=self._packing_excel_bytes(1.5625),
        )
        wizard.excel_filename = 'packing.xlsx'
        wizard.ingestion_profile = 'metric'
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertIsNotNone(result)
        self.assertIn('warning', result)
        self.assertEqual(
            result['warning']['title'],
            'Verifique el perfil de lectura antes de continuar',
        )
        self.assertIn('pulgadas', result['warning']['message'])
        self.assertIn('no bloquea', result['warning']['message'])

    def test_suggest_profile_no_excel_file_noop(self):
        """Sin excel_file el onchange no lanza excepción ni modifica el perfil."""
        wizard = self._make_wizard(tipo='producto', excel_raw=b'excel-bytes')
        wizard.excel_file = False
        wizard.ingestion_profile = 'f1550'
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'f1550')
        self.assertIsNone(result)

    def test_suggest_profile_corrupt_excel_noop(self):
        """Excel corrupto: sin excepción visible y el perfil conserva su valor."""
        wizard = self._make_wizard(
            tipo='producto',
            excel_raw=b'not a valid excel at all',
        )
        wizard.ingestion_profile = 'metric'
        result = wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertIsNone(result)

    # ── Regresión UX: adjuntar documentos no debe alterar decisión manual ──
    def test_normal_excel_solo_no_clasifica_ni_oculta_perfil(self):
        """Normal + Excel: tipo_ingreso no cambia, perfil intacto, sin warning."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'ingestion_profile': 'metric',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'packing.xlsx',
            'assignment_location_id': self.location.id,
        })
        result = wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertIsNone(result)

    def test_normal_pdf_solo_total_no_asigna_granel(self):
        """Normal + PDF con volumen total: no se asigna granel."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertFalse(wizard.tipo_ingreso_auto_detectado)

    def test_normal_pdf_excel_perfil_visible_modalidad_normal(self):
        """Normal + PDF + Excel: perfil y patio intactos, modalidad normal."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'ingestion_profile': 'metric',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'packing.xlsx',
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertEqual(wizard.ingestion_profile, 'metric')
        self.assertEqual(wizard.intake_modality, 'normal')
        self.assertTrue(wizard.assignment_location_id)

    def test_leer_documento_normal_procesado_clasifica(self):
        """Leer documento en normal clasifica Procesado por contenido real."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'packing.xlsx',
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })
        with patch.object(intake_wizard_module, '_extract_pdf_text',
                          return_value='SERVICIO DE CEPILLADO MADENAT'):
            wizard.action_preview_document()
        self.assertEqual(wizard.tipo_ingreso, 'procesado')
        self.assertEqual(wizard.classification_result, 'Procesado')
        self.assertTrue(wizard.tipo_ingreso_auto_detectado)

    def test_volume_excel_no_ejecuta_onchange_perfil(self):
        """Volúmenes + Excel: granel técnico y sin onchange de perfil."""
        wizard = self.Wizard.create({
            'intake_modality': 'volume',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'packing.xlsx',
            'assignment_location_id': self.location.id,
        })
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(wizard.tipo_ingreso, 'granel')
        self.assertFalse(wizard.tipo_ingreso_auto_detectado)
        profile = wizard.ingestion_profile
        wizard._onchange_suggest_ingestion_profile()
        self.assertEqual(wizard.ingestion_profile, profile)

    # ── Fase 2A: clasificador por señales relevantes ─────────────────────
    def _classify_text(self, text, pdf_filename='guia.pdf',
                       excel_filename='packing.xlsx'):
        """Crea un wizard normal y ejecuta la clasificación con `text` como PDF."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': excel_filename,
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': pdf_filename,
            'assignment_location_id': self.location.id,
        })
        with patch.object(intake_wizard_module, '_extract_pdf_text',
                          return_value=text):
            wizard._classify_normal_document()
        return wizard

    def test_t2a_raiz_tildes_y_abreviaturas(self):
        """«Cepillada», «CEPILLADO», «PINO CEP. SECO LATERAL» → Procesado."""
        for text in ('Cepillada', 'CEPILLADO', 'PINO CEP. SECO LATERAL',
                     'SERVICIO CEPILLADO'):
            with self.subTest(text=text):
                wizard = self._classify_text(text)
                self.assertEqual(wizard.tipo_ingreso, 'procesado', text)
                self.assertTrue(wizard.tipo_ingreso_auto_detectado)
                self.assertEqual(wizard.classification_result, 'Procesado')
                self.assertFalse(wizard.has_reading_warning)

    def test_t2a_sin_senal_mantiene_default_y_marca(self):
        """Texto de producto sin señal: Producto + marca de advertencia."""
        wizard = self._classify_text(
            'MADERA ASERRADA BRUTA 2 X 4 X 3.2 100 1.234')
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertTrue(wizard.has_reading_warning)
        self.assertIn('Sin señal de tipo', wizard.reading_warning)

    def test_t2a_texto_legal_sii_no_clasifica_procesado(self):
        """«Servicio de Impuestos Internos» no es señal de servicio."""
        text = (
            'MADENAT SPA\n'
            'SERVICIO DE IMPUESTOS INTERNOS\n'
            'R.U.T.: 76.123.456-7\n'
            'GUIA DE DESPACHO ELECTRONICA N 1234\n'
            '10 2 X 3 MADERA ASERRADA BRUTA 1.234 5.678\n'
        )
        wizard = self._classify_text(text)
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertEqual(wizard.classification_result, 'Producto')

    def test_t2a_cepillada_en_glosa_es_senal_debil(self):
        """Prueba en seco 2A: «Cepillada» en la glosa NO cambia el tipo."""
        text = (
            'SOCIEDAD FORESTAL EJEMPLO LTDA\n'
            'R.U.T.: 77.245.870-3\n'
            'GUIA DE DESPACHO ELECTRONICA N 41471\n'
            '3322 M3 52,63 Madera de Pino Radiata Cepillada Calidad Col A '
            'de 45mm 221.973,6 0 11.682.471\n'
        )
        wizard = self._classify_text(text)
        self.assertEqual(wizard.tipo_ingreso, 'producto')
        self.assertTrue(wizard.has_reading_warning)
        self.assertIn('Posible servicio', wizard.reading_warning)

    def test_t2a_titulo_servicio_confirmado_en_la_fuente(self):
        """T2A-1 (reajustado 2A-1b): el servicio se decide por el TÍTULO.

        Se comprueba la fuente de la coincidencia, no solo el resultado: el
        vocabulario de servicio es decisivo en `pdf_title` (señal fuerte).
        """
        signals = intake_classifier.collect_signals(
            pdf_text='SERVICIO CEPILLADO', filenames=['guia.pdf'])
        outcome = intake_classifier.classify(
            signals,
            ['cepillado', 'servicio', 'proceso', 'maquila'],
            intake_classifier.WEAK_KEYWORDS_DEFAULT,
        )
        self.assertEqual(outcome['tipo'], 'procesado')
        self.assertTrue(outcome['matches'])
        self.assertEqual(
            {match['source'] for match in outcome['matches']}, {'pdf_title'})

    def test_t2a_fila_producto_nunca_es_titulo(self):
        """Fix 2A-1b: con cabeceras de 1, 2 y 3 líneas la glosa no es título.

        Antes, la fila de producto entraba en la ventana de título y su
        adjetivo de artículo («Cepillada») se promovía a señal fuerte.
        """
        product_row = (
            '3322 M3 52,63 Madera de Pino Radiata Cepillada Calidad Col A '
            'de 45mm 221.973,6 0 11.682.471')
        headers = (
            'PROVEEDOR EJEMPLO LTDA',
            'PROVEEDOR EJEMPLO LTDA\nGUIA DE DESPACHO ELECTRONICA N 41471',
            'PROVEEDOR EJEMPLO LTDA\nGUIA DE DESPACHO ELECTRONICA N 41471\n'
            'REFERENCIA MC-1812-248',
        )
        for header in headers:
            with self.subTest(header=header):
                wizard = self._classify_text(header + '\n' + product_row)
                self.assertEqual(wizard.tipo_ingreso, 'producto')
                self.assertTrue(wizard.has_reading_warning)
                self.assertIn('Posible servicio', wizard.reading_warning)

    def test_t2a_fila_producto_con_unidad_y_cantidad(self):
        """Una fila «M3 + cifra» (unidad y cantidad) tampoco es título."""
        signals = intake_classifier.collect_signals(
            pdf_text='PROVEEDOR EJEMPLO LTDA\nTOTAL M3 54,518',
            filenames=['guia.pdf'])
        self.assertEqual(signals['pdf_title'], 'PROVEEDOR EJEMPLO LTDA')

    def test_t2a_perfil_y_unidad_en_marca_de_advertencia(self):
        """Perfil distinto del elegido + unidad no reconocida → advertencia."""
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'ingestion_profile': 'f5085',
            'excel_file': self._b64(b'excel-bytes'),
            'excel_filename': 'packing.xlsx',
            'pdf_file': self._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'assignment_location_id': self.location.id,
        })
        result = SimpleNamespace(
            detected_profile_code='packing_metrico_aserrada',
            lines=[{
                'description': 'MADERA ASERRADA BRUTA',
                'thickness_value_raw': '38', 'thickness_unit': None,
                'width_value_raw': '170', 'width_unit': 'yard',
                'length_value_raw': '4.05', 'length_unit': 'm',
            }],
        )
        with patch.object(intake_wizard_module, '_extract_pdf_text',
                          return_value='MADERA ASERRADA BRUTA'):
            outcome, warning = wizard._reading_analysis(result=result)
        self.assertFalse(outcome['tipo'])
        self.assertIn('no coincide con el elegido', warning)
        self.assertIn('Unidad no reconocida', warning)
        self.assertIn('Sin señal de tipo', warning)

