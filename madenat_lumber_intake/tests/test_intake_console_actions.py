# -*- coding: utf-8 -*-
"""Cobertura unitaria de acciones de consola: envío a stock y descargas.

Valida el contrato observable de las acciones de `madenat.lumber.intake.console`
sin reimplementar sus condiciones internas:
  - action_send_to_stock (delegación Producto/Procesado + bloqueos);
  - action_download_guide_pdf / action_download_packing_excel (Producto y
    Procesado, contrato `ir.actions.act_url` con `/web/content/...?download=true`).
Usa TransactionCase: nada se persiste.
"""
import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from ..models.intake_constants import CONSOLE_ID_OFFSET


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeConsoleActions(TransactionCase):
    """Acciones de consola: envío a stock y descargas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reception = cls.env['lumber.reception']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Producto = cls.env['product.product']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Console Actions Test',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        cls.partner_pro = cls.env['res.partner'].create({
            'name': 'Proveedor Procesado Console',
            'is_company': True,
        })
        cls.product = cls.Producto.create({
            'name': 'Producto Console Actions Test',
        })
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')

    @classmethod
    def _b64(cls, raw=b'fake'):
        return base64.b64encode(raw).decode()

    @classmethod
    def _make_reception(cls, state='verified', guide_name='G-41471'):
        return cls.Reception.create({
            'name': guide_name,
            'supplier_id': cls.partner.id,
            'state': state,
            'excel_file': cls._b64(),
            'excel_filename': 'packing.xlsx',
            'pdf_file': cls._b64(b'%PDF-fake'),
            'pdf_filename': 'guia.pdf',
            'ingestion_profile': 'metric',
        })

    @classmethod
    def _make_reception_with_line(cls, state='verified'):
        rec = cls._make_reception(state=state)
        cls.env['lumber.reception.line'].create({
            'reception_id': rec.id,
            'product_id': cls.product.id,
            'lot_name': 'LOTE-CONS-1',
            'lengthuom': 'm',
        })
        return rec

    @classmethod
    def _make_guia(cls, state='verified'):
        return cls.Guia.create({
            'name': 'G-PROC-CONS-1',
            'partner_id': cls.partner_pro.id,
            'assignment_location_id': cls.location.id,
            'tipo_recepcion': 'service',
            'state': state,
        })

    @classmethod
    def _make_guia_with_doc_and_line(cls, state='verified'):
        """Ambos documentos (PDF guía + Excel packing) + línea de staging."""
        guia = cls._make_guia(state=state)
        guia.write({
            'guide_pdf_file': cls._b64(b'%PDF-fake'),
            'excel_file': cls._b64(),
            'excel_filename': 'packing.xlsx',
        })
        cls.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'product_id': cls.product.id,
            'lot_name': 'LOTE-PROC-CONS-1',
        })
        return guia

    @classmethod
    def _make_guia_excel_only_and_line(cls, state='verified'):
        """Solo Excel packing + línea de staging; PDF de guía AUSENTE (opcional)."""
        guia = cls._make_guia(state=state)
        guia.write({
            'excel_file': cls._b64(),
            'excel_filename': 'packing.xlsx',
        })
        cls.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'product_id': cls.product.id,
            'lot_name': 'LOTE-PROC-CONS-1',
        })
        return guia

    @classmethod
    def _console_for(cls, rec, source_model):
        rec.invalidate_recordset()
        return cls.Console.search([
            ('source_model', '=', source_model),
            ('source_res_id', '=', rec.id),
        ], limit=1)

    # ── action_send_to_stock ─────────────────────────────────────────────
    def test_send_to_stock_product_delegates_and_returns_warning_contract(self):
        rec = self._make_reception_with_line(state='verified')
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with patch.object(
            type(rec), 'action_confirm_reception', return_value={'done': True}
        ) as mocked:
            result = console.action_send_to_stock()
        # La delegación canónica ocurrió (contrato real del método).
        mocked.assert_called_once_with()
        # Sin OC vinculada el fixture produce la advertencia no bloqueante y el
        # retorno observable es la notificación (no el resultado del origen).
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['title'],
                         'Enviado a stock con advertencias')
        self.assertIn('No se detectó OC vinculada ni referencia de OC.',
                      result['params']['message'])
        # Trazabilidad posteada en el chatter del origen.
        self.assertTrue(rec.message_ids, 'Debe postearse la trazabilidad')

    def test_send_to_stock_processed_delegates_action_validate(self):
        guia = self._make_guia_with_doc_and_line(state='verified')
        console = self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        with patch.object(type(guia), 'action_validate',
                          return_value={'done': True}) as mocked:
            result = console.action_send_to_stock()
        # Delegación canónica ocurrió.
        mocked.assert_called_once_with()
        # Sin OC: contrato observable = notificación de advertencia.
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['title'],
                         'Enviado a stock con advertencias')
        self.assertIn('No se detectó OC vinculada ni referencia de OC.',
                      result['params']['message'])
        self.assertTrue(guia.message_ids, 'Debe postearse la trazabilidad')

    def test_send_to_stock_product_without_lines_raises(self):
        rec = self._make_reception(state='verified')  # sin líneas
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with self.assertRaises(UserError) as ctx:
            console.action_send_to_stock()
        self.assertIn('No hay líneas de staging verificadas.', str(ctx.exception))

    def test_send_to_stock_processed_no_pdf_excel_present_delegates(self):
        """Regla canónica 2026-08-22: Procesado con Excel presente y PDF ausente
        debe delegar en action_validate (el PDF no bloquea el envío a stock)."""
        guia = self._make_guia_excel_only_and_line(state='verified')
        console = self._console_for(guia, 'madenat.guia.processing')
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        with patch.object(type(guia), 'action_validate',
                          return_value={'done': True}) as mocked:
            result = console.action_send_to_stock()
        mocked.assert_called_once_with()
        # Sin OC: notificación de advertencia (contrato observable ya validado).
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('No se detectó OC vinculada ni referencia de OC.',
                      result['params']['message'])
        self.assertTrue(guia.message_ids, 'Debe postearse la trazabilidad')

    def test_send_to_stock_processed_sin_excel_bloquea(self):
        """Regla canónica 2026-08-22: Procesado sin Excel debe bloquear el envío
        a stock; el PDF no es sustituto del Excel."""
        guia = self._make_guia(state='verified')
        guia.write({'guide_pdf_file': self._b64(b'%PDF-fake')})
        cls_line = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'product_id': self.product.id,
            'lot_name': 'LOTE-PROC-NOEXCEL',
        })
        self.assertTrue(cls_line)
        console = self._console_for(guia, 'madenat.guia.processing')
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        with self.assertRaises(UserError) as ctx:
            console.action_send_to_stock()
        self.assertIn('Falta el archivo Excel de Packing.', str(ctx.exception))

    def test_send_to_stock_processed_state_draft_raises(self):
        guia = self._make_guia(state='draft')
        console = self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        with self.assertRaises(UserError) as ctx:
            console.action_send_to_stock()
        self.assertIn('La guía debe estar "Verificada" para enviarse a stock.', str(ctx.exception))

    def test_send_to_stock_product_done_raises(self):
        rec = self._make_reception(state='done')
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with self.assertRaises(UserError) as ctx:
            console.action_send_to_stock()
        self.assertIn('La recepción ya fue enviada a stock.', str(ctx.exception))

    # ── action_download_guide_pdf / action_download_packing_excel ────────
    def test_download_guide_pdf_product_returns_act_url(self):
        rec = self._make_reception(state='verified')
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        action = console.action_download_guide_pdf()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(
            action['url'],
            '/web/content/lumber.reception/%s/pdf_file?download=true' % rec.id,
        )
        self.assertEqual(action['target'], 'self')

    def test_download_guide_pdf_product_missing_field_raises(self):
        # Blindaje documental: no se genera URL si el binario requerido está vacío.
        rec = self._make_reception(state='verified')
        rec.write({'pdf_file': False})
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with self.assertRaises(UserError) as ctx:
            console.action_download_guide_pdf()
        self.assertIn(
            'La guía PDF es obligatoria para esta operación.',
            str(ctx.exception),
        )
        # Contrato de descarga no debe producirse ante el blindaje.
        self.assertFalse(hasattr(ctx.exception, 'url'))

    def test_download_packing_excel_product_returns_act_url(self):
        rec = self._make_reception(state='verified')
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        action = console.action_download_packing_excel()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(
            action['url'],
            '/web/content/lumber.reception/%s/excel_file?download=true' % rec.id,
        )
        self.assertEqual(action['target'], 'self')

    def test_download_packing_excel_product_missing_field_raises(self):
        # Blindaje documental: no se genera URL si el binario requerido está vacío.
        rec = self._make_reception(state='verified')
        rec.write({'excel_file': False})
        console = self.Console.search([
            ('source_model', '=', 'lumber.reception'),
            ('source_res_id', '=', rec.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la recepción creada')
        with self.assertRaises(UserError) as ctx:
            console.action_download_packing_excel()
        self.assertIn(
            'El archivo de Packing Excel es obligatorio para esta operación.',
            str(ctx.exception),
        )

    def test_download_guide_pdf_processed_returns_act_url(self):
        guia = self._make_guia_with_doc_and_line(state='verified')
        console = self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        action = console.action_download_guide_pdf()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(
            action['url'],
            '/web/content/madenat.guia.processing/%s/guide_pdf_file?download=true' % guia.id,
        )
        self.assertEqual(action['target'], 'self')

    def test_download_packing_excel_processed_returns_act_url(self):
        guia = self._make_guia_with_doc_and_line(state='verified')
        console = self._console_for(guia, 'madenat.guia.processing')
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        action = console.action_download_packing_excel()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(
            action['url'],
            '/web/content/madenat.guia.processing/%s/excel_file?download=true' % guia.id,
        )
        self.assertEqual(action['target'], 'self')
