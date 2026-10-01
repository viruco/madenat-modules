# -*- coding: utf-8 -*-
"""Contrato operativo de Ingreso por Volúmenes: evidencia independiente,
conciliación, volumen operativo editable y stock sin geometría."""

import base64
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    DocumentExtractionResult,
)
from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeOperational(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.DetailLine = cls.env['madenat.lumber.volume.detail.line']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Picking = cls.env['stock.picking']
        cls.Quant = cls.env['stock.quant']
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'VolOps Proveedor S.A.', 'is_company': True,
        })

    # ── Helpers ────────────────────────────────────────────────────────────
    def _pdf_result(self, guide='VOL-PDF', total=10.0, rut='96.510.970-6',
                    lines=None):
        return DocumentExtractionResult(
            header={
                'total_volume_m3': total, 'guide_number': guide,
                'supplier_rut': rut, 'supplier_name': 'Proveedor PDF S.A.',
                'guide_date': '2026-09-24',
            },
            lines=lines or [], warnings=[])

    def _excel_result(self, guide='VOL-EXCEL', volumes=(10.0,), lines=None):
        if lines is None:
            lines = [
                {'volume_m3': v, 'product_code': 'C%d' % i, 'pieces': 1}
                for i, v in enumerate(volumes, start=1)
            ]
        return DocumentExtractionResult(
            header={'guide_number': guide, 'guide_date': '2026-09-24'},
            lines=lines, warnings=[])

    def _route(self, pdf_result=None, excel_result=None):
        vals = {
            'intake_modality': 'volume',
            'tipo_ingreso': 'granel',
            'assignment_location_id': self.location.id,
        }
        if pdf_result is not None:
            vals['pdf_file'] = base64.b64encode(b'%PDF-fake').decode()
            vals['pdf_filename'] = 'guia.pdf'
        if excel_result is not None:
            vals['excel_file'] = base64.b64encode(b'excel-bytes').decode()
            vals['excel_filename'] = 'packing.xlsx'
        wizard = self.Wizard.create(vals)

        def fake_extract(data, filename, *a, **kw):
            if filename.endswith('.pdf'):
                return pdf_result
            return excel_result

        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=fake_extract):
            wizard.action_route_document()
        return self.Guia.search([], order='id desc', limit=1)

    def _make_guia(self, name='VOL-1', operational=10.0, state='verified',
                   pdf=True, excel=False, conciliation='not_compared',
                   official_pdf=0.0):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': state,
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'volume_operational_m3': operational,
            'conciliation_status': conciliation,
        }
        # Volumen OFICIAL documental (Guía PDF). Es la única fuente de stock
        # para F3.1; el volumen operativo ya no lo sustituye.
        if official_pdf > 0:
            vals['volume_pdf_m3'] = official_pdf
        if pdf:
            vals['guide_pdf_file'] = base64.b64encode(b'%PDF-fake')
            vals['guide_pdf_filename'] = 'guia.pdf'
        if excel:
            vals['excel_file'] = base64.b64encode(b'excel-bytes')
            vals['excel_filename'] = 'packing.xlsx'
        return self.Guia.create(vals)

    def _lot_qty_at_stock(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id),
            ('location_id.usage', '=', 'internal'),
        ])
        return sum(q.quantity for q in quants)

    # ── 1. PDF solo → volumen operativo desde PDF ──────────────────────────
    def test_01_pdf_solo_prellena_operativo_desde_pdf(self):
        guia = self._route(pdf_result=self._pdf_result(total=40.315))
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(guia.volume_operational_m3, 40.315, places=3)
        self.assertEqual(guia.volume_operational_source, 'pdf')
        self.assertEqual(guia.conciliation_status, 'not_compared')

    # ── 2. Excel solo → volumen operativo desde Excel ──────────────────────
    def test_02_excel_solo_prellena_operativo_desde_excel(self):
        guia = self._route(excel_result=self._excel_result(
            guide='VOL-EXCEL', volumes=(5.0, 5.0)))
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertAlmostEqual(guia.volume_pdf_m3, 0.0, places=3)
        self.assertAlmostEqual(guia.volume_excel_m3, 10.0, places=3)
        self.assertAlmostEqual(guia.volume_operational_m3, 10.0, places=3)
        self.assertEqual(guia.volume_operational_source, 'excel')
        self.assertEqual(guia.conciliation_status, 'not_compared')

    # ── 3. PDF + Excel coherentes → auto_matched ───────────────────────────
    def test_03_pdf_excel_coherentes_auto_matched(self):
        guia = self._route(
            pdf_result=self._pdf_result(guide='VOL-1', total=10.0),
            excel_result=self._excel_result(guide='VOL-1', volumes=(10.0,)))
        self.assertEqual(guia.conciliation_status, 'auto_matched')

    # ── 4. PDF + Excel diferencia de volumen → matched_with_differences ────
    def test_04_pdf_excel_diferencia_volumen(self):
        guia = self._route(
            pdf_result=self._pdf_result(guide='VOL-1', total=10.0),
            excel_result=self._excel_result(guide='VOL-1', volumes=(12.0,)))
        self.assertEqual(guia.conciliation_status, 'matched_with_differences')
        self.assertIn('Volumen distinto', guia.conciliation_summary)

    # ── 5. PDF + Excel incompatibles → incompatible y stock bloqueado ──────
    def test_05_incompatible_bloquea_stock(self):
        guia = self._route(
            pdf_result=self._pdf_result(guide='VOL-A', total=10.0),
            excel_result=self._excel_result(guide='VOL-B', volumes=(10.0,)))
        self.assertEqual(guia.conciliation_status, 'incompatible')
        guia.write({'state': 'verified'})
        with self.assertRaises(ValidationError):
            guia.action_validate()
        self.assertFalse(guia.lot_ids)
        self.assertFalse(self.Picking.search([('origin', '=', guia.name)]))

    # ── 6. Resolución manual → manual_confirmed + chatter + audit ──────────
    def test_06_resolucion_manual_conciliacion(self):
        guia = self._make_guia(conciliation='incompatible')
        guia.action_confirm_conciliation('Confirmado por Operaciones.')
        self.assertEqual(guia.conciliation_status, 'manual_confirmed')
        self.assertEqual(
            guia.conciliation_manual_note, 'Confirmado por Operaciones.')
        self.assertTrue(guia.conciliation_manual_user_id)
        logs = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'conciliation_manual_confirm'),
        ])
        self.assertTrue(logs, 'Debe existir bitácora de confirmación')

    # ── 7. Edición controlada del volumen operativo ────────────────────────
    def test_07_set_volume_operational_con_auditoria(self):
        guia = self._make_guia(operational=10.0)
        guia.write({'volume_pdf_m3': 10.0, 'volume_excel_m3': 0.0})
        guia.set_volume_operational(12.5, 'manual', 'Corrección operativa.')
        self.assertAlmostEqual(guia.volume_operational_m3, 12.5, places=3)
        self.assertEqual(guia.volume_operational_source, 'manual')
        self.assertEqual(guia.volume_operational_note, 'Corrección operativa.')
        self.assertTrue(guia.volume_operational_user_id)
        self.assertTrue(guia.volume_operational_date)
        # Evidencia original intacta.
        self.assertAlmostEqual(guia.volume_pdf_m3, 10.0, places=3)
        self.assertAlmostEqual(guia.volume_excel_m3, 0.0, places=3)
        logs = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'volume_operational_update'),
        ])
        self.assertTrue(logs, 'Debe existir bitácora de actualización de volumen')

    def test_07b_set_volume_operational_exige_motivo(self):
        guia = self._make_guia(operational=10.0)
        with self.assertRaises(ValidationError):
            guia.set_volume_operational(12.0, 'manual')

    # ── 8-10. Detalle documental editable ──────────────────────────────────
    def test_08_detalle_documental_add_edit_delete(self):
        guia = self._make_guia(operational=10.0)
        l1 = self.DetailLine.create({
            'guia_id': guia.id, 'origin': 'pdf', 'volume_m3': 4.0,
        })
        l2 = self.DetailLine.create({
            'guia_id': guia.id, 'origin': 'excel', 'volume_m3': 6.0,
        })
        self.assertAlmostEqual(guia.volume_detail_m3, 10.0, places=3)
        l1.write({'volume_m3': 5.0, 'manually_adjusted': True})
        self.assertAlmostEqual(guia.volume_detail_m3, 11.0, places=3)
        l2.unlink()
        self.assertAlmostEqual(guia.volume_detail_m3, 5.0, places=3)

    def test_10_editar_detalle_no_pisa_operativo_manual(self):
        guia = self._make_guia(operational=10.0)
        guia.set_volume_operational(9.0, 'manual', 'Ajuste manual.')
        self.DetailLine.create({
            'guia_id': guia.id, 'origin': 'pdf', 'volume_m3': 7.0,
        })
        self.assertAlmostEqual(guia.volume_detail_m3, 7.0, places=3)
        self.assertAlmostEqual(guia.volume_operational_m3, 9.0, places=3)
        self.assertEqual(guia.volume_operational_source, 'manual')

    # ── 11. Sin volumen oficial documental bloquea stock ───────────────────
    def test_11_volumen_operativo_cero_bloquea(self):
        guia = self._make_guia(operational=0.0)
        with self.assertRaises(ValidationError) as ctx:
            guia.action_validate()
        self.assertIn(
            'No existe volumen documental oficial para enviar a stock.',
            str(ctx.exception))

    # ── 12-13. Stock sin espesor/subproducto + lote/picking/moves ──────────
    def test_13_stock_sin_geometria_crea_lote_picking_moves(self):
        guia = self._make_guia(operational=10.0, official_pdf=10.0)
        guia.action_validate()
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(len(guia.lot_ids), 1)
        lot = guia.lot_ids[0]
        self.assertAlmostEqual(lot.volumen_m3, 10.0, places=3)
        self.assertAlmostEqual(lot.espesor_nominal_mm, 0.0, places=3)
        self.assertFalse(lot.subproducto_id)
        pickings = self.Picking.search([('origin', '=', guia.name)])
        self.assertEqual(len(pickings), 1)
        picking = pickings[0]
        self.assertEqual(picking.picking_type_code, 'incoming')
        moves = picking.move_ids
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].product_uom.id, self.uom_m3.id)
        self.assertAlmostEqual(moves[0].product_uom_qty, 10.0, places=3)
        self.assertTrue(moves[0].move_line_ids)
        self.assertEqual(moves[0].move_line_ids.lot_id, lot)
        self.assertAlmostEqual(self._lot_qty_at_stock(lot), 10.0, places=3)
        # F1 — Post-condición: albarán y movimientos en 'done' y guía validada.
        self.assertEqual(picking.state, 'done')
        self.assertFalse(
            picking.move_ids.filtered(lambda move: move.state != 'done'))
        self.assertEqual(guia.state, 'validated')

    # ── 14. Segundo envío bloqueado / idempotencia ─────────────────────────
    def test_14_segundo_envio_bloqueado(self):
        guia = self._make_guia(operational=10.0, official_pdf=10.0)
        guia.action_validate()
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(self.Picking.search_count([('origin', '=', guia.name)]), 1)
        with self.assertRaises(ValidationError):
            guia.action_validate()
        self.assertEqual(
            self.Picking.search_count([('origin', '=', guia.name)]), 1)

    # ── 15. Volúmenes + Excel solo + parser sin cabecera → no bloquea ──────
    def test_15_excel_solo_sin_cabecera_no_bloquea(self):
        wizard = self.Wizard.create({
            'intake_modality': 'volume',
            'tipo_ingreso': 'granel',
            'assignment_location_id': self.location.id,
            'excel_file': base64.b64encode(b'excel-bytes').decode(),
            'excel_filename': 'packing.xlsx',
        })
        err = DocumentExtractionError(
            'No se detectó una cabecera de columnas reconocible en el archivo.')
        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=err):
            wizard.action_preview_document()  # no debe lanzar UserError
        self.assertEqual(wizard.state, 'previewed')
        self.assertIn('No fue posible extraer automáticamente',
                      wizard.preview_warnings or '')
        self.assertTrue(wizard.excel_file)

        # Ruteo: permite continuar con guía revisable (volumen operativo 0 manual).
        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=err):
            wizard.action_route_document()
        guia = self.Guia.search([('excel_filename', '=', 'packing.xlsx')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(guia.state, 'verified')
        self.assertAlmostEqual(guia.volume_operational_m3, 0.0, places=3)
        self.assertEqual(guia.volume_operational_source, 'manual')
        self.assertIn('No fue posible extraer automáticamente',
                      '\n'.join(m.body or '' for m in guia.message_ids))

    # ── 16. Volúmenes + PDF solo + clasificación no resuelta → prevalece ───
    def test_16_volume_clasificacion_auto_no_bloquea(self):
        wizard = self.Wizard.create({
            'intake_modality': 'volume',
            'assignment_location_id': self.location.id,
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
        })
        result = wizard._onchange_suggest_tipo_ingreso()
        self.assertIsNone(result)
        self.assertEqual(wizard.tipo_ingreso, 'granel')
        self.assertFalse(wizard.tipo_ingreso_auto_detectado)

    # ── 17. Ingreso normal conserva bloqueo por Excel sin cabecera ─────────
    def test_17_normal_excel_sin_cabecera_mantiene_bloqueo(self):
        wizard = self.Wizard.create({
            'intake_modality': 'normal',
            'tipo_ingreso': 'producto',
            'assignment_location_id': self.location.id,
            'excel_file': base64.b64encode(b'excel-bytes').decode(),
            'excel_filename': 'packing.xlsx',
        })
        err = DocumentExtractionError(
            'No se detectó una cabecera de columnas reconocible en el archivo.')
        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=err):
            with self.assertRaises(UserError):
                wizard.action_preview_document()

    # ── 18. Volúmenes sin PDF y sin Excel → sigue bloqueando ───────────────
    def test_18_volume_sin_documentos_bloquea(self):
        wizard = self.Wizard.create({
            'intake_modality': 'volume',
            'assignment_location_id': self.location.id,
        })
        with self.assertRaises(UserError):
            wizard.action_preview_document()

    # ── 19. F1: wizard/acción no procesable → UserError, guía no validada ──
    def test_19_button_validate_wizard_no_procesable_bloquea(self):
        """F1 — Si `button_validate` devuelve una acción/wizard que el flujo
        servidor no puede procesar, la validación debe fallar de forma
        cerrada (UserError) y la guía NO debe quedar Validada.

        This test proves that the guide validation write is not attempted.
        It does not prove persistence or rollback of stock records.
        """
        guia = self._make_guia(name='VOL-F1-WIZ', operational=10.0,
                               official_pdf=10.0)
        PickingModel = type(self.Picking)
        # Espía en memoria sobre el write real del modelo de la guía: prueba
        # que no se INTENTA la transición a Validada, sin depender de que los
        # registros creados en la ruta fallida sobrevivan al rollback.
        GuiaModel = type(self.Guia)
        real_write = GuiaModel.write
        writes = []

        def spy_write(recordset, vals, *args, **kwargs):
            writes.append(dict(vals))
            return real_write(recordset, vals, *args, **kwargs)

        # Acción/wizard cuyo res_model no existe en el registro de Odoo:
        # el flujo servidor no puede instanciarlo y re-empaqueta el error.
        with patch.object(PickingModel, 'button_validate', return_value={
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.wizard.inexistente.f1',
        }):
            with patch.object(GuiaModel, 'write', spy_write):
                with self.assertRaises(UserError):
                    guia.action_validate()
        self.assertTrue(writes, 'El espía de write no registró llamadas.')
        self.assertFalse(
            [vals for vals in writes if vals.get('state') == 'validated']
        )
        self.assertFalse(
            any(
                'validated_date' in vals or 'validated_by_id' in vals
                for vals in writes
            )
        )
        self.assertNotEqual(guia.state, 'validated')
        self.assertFalse(guia.validated_date)
        self.assertFalse(guia.validated_by_id)

    # ── 20. F1: picking no 'done' tras validar → UserError, no validada ────
    def test_20_picking_no_done_bloquea_validacion(self):
        """F1 — Si `button_validate` retorna normalmente pero el albarán queda
        en un estado distinto de 'done', la guía NO debe marcarse Validada y no
        debe persistirse ninguna escritura de estado 'validated'.

        This test proves that the guide validation write is not attempted.
        It does not prove persistence or rollback of stock records.
        """
        guia = self._make_guia(name='VOL-F1-NODONE', operational=10.0,
                               official_pdf=10.0)
        PickingModel = type(self.Picking)
        # Espía en memoria sobre el write real del modelo de la guía (misma
        # estrategia que test_19): prueba que no se INTENTA la transición a
        # Validada, sin asumir persistencia de stock tras el rollback.
        GuiaModel = type(self.Guia)
        real_write = GuiaModel.write
        writes = []

        def spy_write(recordset, vals, *args, **kwargs):
            writes.append(dict(vals))
            return real_write(recordset, vals, *args, **kwargs)

        with patch.object(PickingModel, 'button_validate', return_value=None):
            with patch.object(GuiaModel, 'write', spy_write):
                with self.assertRaises(UserError):
                    guia.action_validate()
        self.assertTrue(writes, 'El espía de write no registró llamadas.')
        self.assertFalse(
            [vals for vals in writes if vals.get('state') == 'validated']
        )
        self.assertFalse(
            any(
                'validated_date' in vals or 'validated_by_id' in vals
                for vals in writes
            )
        )
        self.assertNotEqual(guia.state, 'validated')
        self.assertFalse(guia.validated_date)
        self.assertFalse(guia.validated_by_id)



