# -*- coding: utf-8 -*-
"""Extracción robusta de volumen para Ingreso por Volúmenes.

Cubre parse_localized_decimal, la extracción de total por etiqueta del header
del PDF y la propagación del volumen hasta la línea de resumen Granel.
"""
import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionResult,
    _extract_pdf_header,
    parse_localized_decimal,
)
from odoo.addons.madenat_lumber_intake.models import intake_wizard as intake_wizard_module


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeExtraction(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)

    # ── parse_localized_decimal ───────────────────────────────────────────
    def test_parse_localized_decimal_casos(self):
        self.assertEqual(parse_localized_decimal("40,315"), 40.315)
        self.assertEqual(parse_localized_decimal("2,92"), 2.92)
        self.assertEqual(parse_localized_decimal("1.234,56"), 1234.56)
        self.assertEqual(parse_localized_decimal("1234.56"), 1234.56)
        self.assertEqual(parse_localized_decimal("1,234.56"), 1234.56)

    def test_parse_localized_decimal_sin_separador(self):
        self.assertEqual(parse_localized_decimal("40"), 40.0)
        self.assertEqual(parse_localized_decimal(40), 40.0)
        self.assertEqual(parse_localized_decimal(40.315), 40.315)

    def test_parse_localized_decimal_invalido(self):
        self.assertIsNone(parse_localized_decimal("abc"))
        self.assertIsNone(parse_localized_decimal(""))

    # ── Header: total por etiqueta (reproduce el PDF real) ────────────────
    def test_header_total_ton_m3(self):
        header = _extract_pdf_header("VOLUMEN/TON PIEZAS: 0 TON/M3: 40,315")
        self.assertEqual(header.get('total_volume_m3'), 40.315)

    def test_header_total_volumen_ton(self):
        header = _extract_pdf_header("VOLUMEN/TON: 40,315")
        self.assertEqual(header.get('total_volume_m3'), 40.315)

    def test_header_total_m3(self):
        header = _extract_pdf_header("TOTAL M3: 40,315")
        self.assertEqual(header.get('total_volume_m3'), 40.315)

    def test_header_fecha_abreviada(self):
        header = _extract_pdf_header("FECHA : 07 - Sep - 2026")
        self.assertEqual(header.get('guide_date'), '2026-09-07')

    def test_header_oc_vs_origen_independientes(self):
        header = _extract_pdf_header(
            "O/C : 2708-327-02 PEDIDO/ORIGEN : 0006996299")
        self.assertEqual(header.get('oc_reference'), '2708-327-02')
        self.assertEqual(header.get('origin_reference'), '0006996299')
        self.assertNotEqual(
            header.get('oc_reference'), header.get('origin_reference'))

    def test_parse_localized_decimal_punto_y_coma(self):
        self.assertEqual(parse_localized_decimal("59.964"), 59.964)
        self.assertEqual(parse_localized_decimal("59,964"), 59.964)

    def test_header_formato_95806(self):
        text = (
            "GUÍA DE DESPACHO ELECTRÓNICA Nº 95806\n"
            "Cliente : MADENAT CHILE LTDA Emitido : 21-AGO-2026\n"
            "R.U.T. : 76.103.087-6\n"
            "TIPO CAMBIO : 923.23 VOL.TOT. : 59.964\n"
            "Orden de Compra MC-0523-140 23-MAY-2026\n"
            "TOT.PAQ.:12 TOT PZAS.:2772\n"
            "Monto Neto $ 23.805.042 I.V.A. (19%) 4.522.958 Total $ 28.328.000"
        )
        header = _extract_pdf_header(text)
        self.assertEqual(header.get('document_type'), 'Guía de Despacho Electrónica')
        self.assertEqual(header.get('guide_number'), '95806')
        self.assertEqual(header.get('guide_date'), '2026-08-21')
        self.assertEqual(header.get('customer_name'), 'MADENAT CHILE LTDA')
        self.assertEqual(header.get('exchange_rate'), 923.23)
        self.assertEqual(header.get('total_volume_m3'), 59.964)
        self.assertEqual(header.get('oc_reference'), 'MC-0523-140')
        self.assertEqual(header.get('total_packages'), 12)
        self.assertEqual(header.get('total_pieces'), 2772)
        self.assertEqual(header.get('net_amount'), 23805042.0)
        self.assertEqual(header.get('vat_amount'), 4522958.0)
        self.assertEqual(header.get('total_amount'), 28328000.0)

    # ── Propagación: preview + route con total 40.315 ────────────────────
    _DETAIL_LINES = [
        {'volume_m3': 2.92}, {'volume_m3': 2.70}, {'volume_m3': 2.80},
        {'volume_m3': 2.64}, {'volume_m3': 2.94}, {'volume_m3': 4.19},
        {'volume_m3': 4.18}, {'volume_m3': 3.87}, {'volume_m3': 2.84},
        {'volume_m3': 3.87}, {'volume_m3': 4.03}, {'volume_m3': 3.32},
    ]

    def _pdf_result(self, total=40.315, lines=None, warnings=None):
        return DocumentExtractionResult(
            header={'total_volume_m3': total, 'guide_number': '4495589'},
            lines=lines or [],
            warnings=warnings or [],
        )

    def _make_volume_wizard(self, excel=False):
        vals = {
            'intake_modality': 'volume',
            'tipo_ingreso': 'granel',
            'assignment_location_id': self.location.id,
            'pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'pdf_filename': 'guia.pdf',
        }
        if excel:
            vals['excel_file'] = base64.b64encode(b'excel-bytes').decode()
            vals['excel_filename'] = 'packing.xlsx'
        return self.Wizard.create(vals)

    def test_preview_volume_detecta_total(self):
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315)):
            wizard.action_preview_document()
        self.assertEqual(wizard.state, 'previewed')
        self.assertAlmostEqual(wizard.preview_total_volume_m3, 40.315, places=3)

    def test_preview_volume_resumen_documental(self):
        result = DocumentExtractionResult(
            header={
                'total_volume_m3': 59.964,
                'guide_number': '95806',
                'guide_date': '2026-08-21',
                'supplier_rut': '96.547.890-6',
                'oc_reference': 'MC-0523-140',
                'origin_reference': '0006996299',
                'exchange_rate': 923.23,
                'total_packages': 12,
            },
            lines=[],
            warnings=[],
        )
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=result):
            wizard.action_preview_document()
        self.assertEqual(wizard.state, 'previewed')
        self.assertEqual(wizard.preview_guide_no, '95806')
        self.assertEqual(wizard.preview_guide_date, '2026-08-21')
        self.assertEqual(wizard.preview_supplier, '96.547.890-6')
        self.assertEqual(wizard.preview_oc, 'MC-0523-140')
        self.assertEqual(wizard.preview_origin, '0006996299')
        self.assertAlmostEqual(wizard.preview_exchange_rate, 923.23, places=2)
        self.assertEqual(wizard.preview_total_packages, 12)
        self.assertFalse(wizard.preview_has_detail)

    def test_preview_volume_detalle_documental(self):
        result = DocumentExtractionResult(
            header={'total_volume_m3': 40.315, 'guide_number': '4495589'},
            lines=[
                {'lot_number': 'L1', 'product_code': 'C1',
                 'product_name_original': 'MADERA', 'pieces': 10,
                 'volume_m3': 2.92},
            ],
            warnings=[],
        )
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=result):
            wizard.action_preview_document()
        self.assertTrue(wizard.preview_has_detail)
        self.assertIn('#1', wizard.preview_document_lines)
        self.assertIn('L1', wizard.preview_document_lines)

    def test_route_granel_propaga_total(self):
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 40.315, places=3)

    def test_route_granel_fallback_suma_lineas(self):
        # Las 12 líneas del PDF real suman 40,30 (redondeo a 2 decimales);
        # el total explícito "40,315" tiene 3 decimales y es más preciso.
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(None, lines=self._DETAIL_LINES)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 40.3, places=3)

    def test_route_granel_sin_volumen_permite_manual(self):
        # Sin volumen válido: la guía se crea con volumen operativo 0 y fuente
        # 'manual'; el usuario completa el valor antes de enviar a stock.
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(None)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertAlmostEqual(guia.volume_operational_m3, 0.0, places=3)
        self.assertEqual(guia.volume_operational_source, 'manual')

    def test_route_granel_sin_detalle_registra_no_estructurado(self):
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        bodies = '\n'.join(m.body or '' for m in guia.message_ids)
        self.assertIn('Detalle documental no estructurado para este formato.', bodies)
        self.assertNotIn('líneas estructuradas disponibles', bodies)

    # ── Nivel de detalle: controla la creación de la recepción ────────────
    def test_detalle_line_by_line_con_lineas(self):
        wizard = self._make_volume_wizard()
        wizard.tipo_detalle_granel = 'linea_por_linea'
        lines = [{'volume_m3': 2.92}, {'volume_m3': 2.70}]
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(None, lines=lines)):
            wizard.action_preview_document()
        self.assertEqual(wizard.detalle_aplicado, 'line_by_line')
        self.assertEqual(wizard.preview_line_count, 2)
        self.assertAlmostEqual(wizard.preview_line_volume_m3, 5.62, places=3)
        self.assertFalse(wizard.detalle_motivo)

    def test_detalle_line_by_line_sin_lineas_fallback(self):
        wizard = self._make_volume_wizard()
        wizard.tipo_detalle_granel = 'linea_por_linea'
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315)):
            wizard.action_preview_document()
        self.assertEqual(wizard.detalle_aplicado, 'consolidated')
        self.assertEqual(wizard.detalle_motivo, 'Tabla PDF no reconocida')
        self.assertEqual(wizard.preview_line_count, 0)

    def test_detalle_consolidated_con_lineas(self):
        wizard = self._make_volume_wizard()  # default 'agregado' (consolidado)
        lines = [{'volume_m3': 2.92}]
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315, lines=lines)):
            wizard.action_preview_document()
        self.assertEqual(wizard.detalle_aplicado, 'consolidated')
        self.assertFalse(wizard.detalle_motivo)

    def test_route_line_by_line_crea_n_lineas(self):
        wizard = self._make_volume_wizard()
        wizard.tipo_detalle_granel = 'linea_por_linea'
        lines = [
            {'volume_m3': 2.92, 'lot_number': 'L1'},
            {'volume_m3': 2.70, 'lot_number': 'L2'},
        ]
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(None, lines=lines)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(len(guia.processing_line_ids), 2)

    def test_route_consolidado_con_detalle_una_linea(self):
        """Consolidado (default) con detalle → 1 línea de volumen total."""
        wizard = self._make_volume_wizard()
        with patch.object(
                intake_wizard_module, 'extract_document',
                return_value=self._pdf_result(40.315, lines=self._DETAIL_LINES)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(len(guia.processing_line_ids), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 40.315, places=3)
        # El volumen declarado en PDF se conserva como evidencia.
        self.assertAlmostEqual(guia.vol_comercial_pdf, 40.315, places=3)

    def test_route_granel_excel_fallback(self):
        wizard = self._make_volume_wizard(excel=True)

        def fake_extract(data, filename):
            if filename == 'packing.xlsx':
                return self._pdf_result(40.315)
            return self._pdf_result(None)

        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=fake_extract):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 40.315, places=3)

    def test_route_granel_total_y_suma_coincidentes_sin_warning(self):
        lines = [{'volume_m3': 20.1575}, {'volume_m3': 20.1575}]
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315, lines=lines)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        bodies = '\n'.join(m.body or '' for m in guia.message_ids)
        self.assertNotIn('Discrepancia de volumen', bodies)

    def test_route_granel_total_y_suma_distintos_warning(self):
        lines = [{'volume_m3': 30.0}]
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315, lines=lines)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertAlmostEqual(
            guia.processing_line_ids.vol_purchase_m3, 40.315, places=3)
        bodies = '\n'.join(m.body or '' for m in guia.message_ids)
        self.assertIn('Discrepancia de volumen', bodies)

    def test_route_granel_persiste_cabecera_y_detalle(self):
        result = DocumentExtractionResult(
            header={
                'total_volume_m3': 40.315,
                'guide_number': '4495589',
                'guide_date': '2026-09-07',
                'oc_reference': '2708-327-02',
                'origin_reference': '0006996299',
                'supplier_rut': '96.510.970-1',
            },
            lines=[
                {'lot_number': 'L1', 'product_code': '997337',
                 'pieces': 100, 'volume_m3': 2.92},
                {'lot_number': 'L2', 'product_code': '930803',
                 'pieces': 200, 'volume_m3': 4.19},
            ],
            warnings=[],
        )
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=result):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        self.assertEqual(guia.name, '4495589')
        self.assertEqual(str(guia.date_emission), '2026-09-07')
        self.assertEqual(guia.oc_reference_raw, '2708-327-02')
        # OC y Pedido/Origen NO se mezclan (negativo explícito).
        self.assertNotEqual(guia.oc_reference_raw, '0006996299')
        # Detalle documental conservado en el chatter (sin lotes físicos por línea).
        bodies = '\n'.join(m.body or '' for m in guia.message_ids)
        self.assertIn('Detalle documental: 2 líneas estructuradas disponibles.', bodies)
        self.assertIn('Pedido/Origen: 0006996299', bodies)
        # Solo una línea física Granel consolidada.
        self.assertEqual(len(guia.processing_line_ids), 1)

    # ── Consola: Ingreso por Volúmenes como tipo independiente ─────────────
    def _route_and_get_console(self):
        wizard = self._make_volume_wizard()
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        return guia, console

    def test_console_ingestion_type_volume(self):
        """La consola clasifica la guía Granel de Volúmenes como 'volume'."""
        _guia, console = self._route_and_get_console()
        self.assertEqual(len(console), 1)
        self.assertEqual(console.ingestion_type, 'volume')

    def test_console_volume_metrics_consolidado(self):
        """Consolidado sin líneas: stock = PDF, suma 0, diferencia 0."""
        _guia, console = self._route_and_get_console()
        self.assertAlmostEqual(console.volumen_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(console.volumen_suma_detalle, 0.0, places=3)
        self.assertAlmostEqual(console.volumen_stock_m3, 40.315, places=3)
        self.assertAlmostEqual(console.volumen_diff_m3, 0.0, places=3)
        self.assertEqual(console.volumen_fuente, 'PDF')

    def test_console_volume_aplicar_cambios_bloqueado(self):
        """'Aplicar cambios' (edición comercial) está bloqueado en Volúmenes."""
        _guia, console = self._route_and_get_console()
        with self.assertRaises(UserError):
            console.action_apply_product_subproduct()

    # ── Grilla editable de detalle documental ─────────────────────────────
    def _route_line_by_line_12(self):
        wizard = self._make_volume_wizard()
        wizard.tipo_detalle_granel = 'linea_por_linea'
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=self._pdf_result(40.315,
                                                        lines=self._DETAIL_LINES)):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        return guia

    def test_route_granel_guarda_detalle_documental(self):
        """El detalle PDF se persiste como grilla editable (12 filas)."""
        guia = self._route_line_by_line_12()
        self.assertEqual(len(guia.volume_detail_line_ids), 12)
        self.assertAlmostEqual(
            sum(l.volume_m3 for l in guia.volume_detail_line_ids), 40.30, places=3)

    def test_console_volume_linea_por_linea_metrics(self):
        """Línea por Línea: stock = suma grilla 40.300, diferencia 0.015."""
        guia = self._route_line_by_line_12()
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        self.assertEqual(len(console), 1)
        self.assertAlmostEqual(console.volumen_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(console.volumen_suma_detalle, 40.30, places=3)
        self.assertAlmostEqual(console.volumen_stock_m3, 40.30, places=3)
        self.assertAlmostEqual(console.volumen_diff_m3, 0.015, places=3)

    def test_editar_volumen_grilla_actualiza_metricas(self):
        """Editar una fila actualiza la suma de detalle; el volumen operativo
        (aprobado) NO se sobrescribe automáticamente."""
        guia = self._route_line_by_line_12()
        line = guia.volume_detail_line_ids[0]
        line.volume_m3 = 3.0  # antes 2.92 → suma pasa a 40.38
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        # Suma 40.30 + (3.0 - 2.92) = 40.38
        self.assertAlmostEqual(console.volumen_suma_detalle, 40.38, places=3)
        # El volumen operativo prellenado (40.30) NO se pisa al editar detalle.
        self.assertAlmostEqual(console.volumen_stock_m3, 40.30, places=3)
        self.assertAlmostEqual(console.volumen_diff_m3, 0.015, places=3)
        # El volumen PDF original NO cambia.
        self.assertAlmostEqual(console.volumen_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(guia.vol_comercial_pdf, 40.315, places=3)

    def test_console_volume_sin_lineas_stock_pdf_no_cero(self):
        """Sin líneas: volumen stock = volumen PDF (nunca 0)."""
        _guia, console = self._route_and_get_console()
        self.assertAlmostEqual(console.volumen_stock_m3, 40.315, places=3)
        self.assertNotEqual(console.volumen_stock_m3, 0.0)

    # ── Proveedor documental (emisor) y resolución ─────────────────────────
    def _route_with_header(self, header):
        wizard = self._make_volume_wizard()
        result = DocumentExtractionResult(header=header, lines=[], warnings=[])
        with patch.object(intake_wizard_module, 'extract_document',
                          return_value=result):
            wizard.action_route_document()
        guia = self.Guia.search([('guide_pdf_filename', '=', 'guia.pdf')])
        self.assertEqual(len(guia), 1)
        return guia

    def test_route_persiste_proveedor_documental(self):
        header = {
            'total_volume_m3': 40.315,
            'guide_number': '4495589',
            'supplier_name': 'Proveedor Documental Test S.A.',
            'supplier_rut': '96.510.970-2',
            'supplier_source': 'letterhead',
            'supplier_confidence': 'high',
            'customer_name': 'MADENAT CHILE LIMITADA',
            'customer_rut': '76.103.087-6',
        }
        guia = self._route_with_header(header)
        self.assertEqual(guia.supplier_name, 'Proveedor Documental Test S.A.')
        self.assertEqual(guia.supplier_rut, '96.510.970-2')
        self.assertEqual(guia.supplier_source, 'letterhead')
        self.assertEqual(guia.supplier_confidence, 'high')

    def test_route_resuelve_partner_existente_por_rut(self):
        partner = self.env['res.partner'].create({
            'name': 'Maderas Arauco S.A.',
            'vat': '96.510.970-6',
            'is_company': True,
        })
        header = {
            'total_volume_m3': 40.315,
            'guide_number': '4495589',
            'supplier_name': 'Maderas Arauco S.A.',
            'supplier_rut': '96.510.970-6',
            'supplier_confidence': 'high',
        }
        guia = self._route_with_header(header)
        self.assertEqual(guia.partner_id, partner)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_vat')

    def test_route_sin_proveedor_no_bloquea(self):
        header = {'total_volume_m3': 40.315, 'guide_number': '4495589'}
        guia = self._route_with_header(header)
        self.assertFalse(guia.partner_id)
        self.assertEqual(guia.supplier_resolution_status, 'needs_manual')
        self.assertEqual(guia.state, 'verified')

    def test_route_ambiguedad_no_crea_partner_incorrecto(self):
        self.env['res.partner'].create([
            {'name': 'Proveedor Ambigua Test S.A.', 'is_company': True},
            {'name': 'Proveedor Ambigua Test S.A.', 'is_company': True},
        ])
        header = {
            'total_volume_m3': 40.315,
            'guide_number': '4495589',
            'supplier_name': 'Proveedor Ambigua Test S.A.',
            'supplier_rut': '96.510.970-4',
            'supplier_confidence': 'high',
        }
        guia = self._route_with_header(header)
        self.assertEqual(guia.supplier_resolution_status, 'multi_match')
        self.assertFalse(guia.partner_id)

    def test_route_confianza_baja_no_crea_partner(self):
        header = {
            'total_volume_m3': 40.315,
            'guide_number': '4495589',
            'supplier_name': 'Proveedor Baja Test S.A.',
            'supplier_rut': '96.510.970-5',
            'supplier_confidence': 'low',
        }
        guia = self._route_with_header(header)
        self.assertFalse(guia.partner_id)
        self.assertEqual(guia.supplier_resolution_status, 'needs_manual')

    def test_console_muestra_partner_cuando_existe(self):
        partner = self.env['res.partner'].create({
            'name': 'Proveedor Consola Test S.A.', 'vat': '96.510.970-3',
            'is_company': True,
        })
        header = {
            'total_volume_m3': 40.315, 'guide_number': '4495589',
            'supplier_name': 'Proveedor Consola Test S.A.',
            'supplier_rut': '96.510.970-3',
            'supplier_confidence': 'high',
        }
        guia = self._route_with_header(header)
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        self.assertEqual(console.partner_id, partner)

    def test_console_muestra_proveedor_documental_pendiente(self):
        header = {
            'total_volume_m3': 40.315, 'guide_number': '4495589',
            'supplier_name': 'Proveedor Pendiente Test S.A.',
            'supplier_rut': '96.510.970-7',
            'supplier_confidence': 'low',
        }
        guia = self._route_with_header(header)
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        self.assertFalse(console.partner_id)
        self.assertEqual(console.supplier_documental_name, 'Proveedor Pendiente Test S.A.')
        self.assertEqual(console.supplier_documental_rut, '96.510.970-7')
        self.assertEqual(console.supplier_resolution_status, 'needs_manual')

    # ── Asignación manual de proveedor (Volúmenes) ─────────────────────────
    def test_action_assign_supplier_abre_wizard(self):
        """El botón 'Asignar proveedor' abre el wizard reutilizado."""
        guia = self._route_with_header({
            'total_volume_m3': 40.315, 'guide_number': 'ASIGN-1',
            'supplier_name': 'Proveedor Asign Uno S.A.',
            'supplier_rut': '96.510.970-8',
            'supplier_confidence': 'low',
        })
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ])
        action = console.action_assign_supplier()
        self.assertEqual(action['res_model'], 'madenat.lumber.intake.supplier.link')
        self.assertEqual(action['context']['default_guia_id'], guia.id)

    def test_asignar_proveedor_persiste_estado_y_chatter(self):
        """Asignar proveedor persiste vínculo, estado y trazabilidad."""
        guia = self._route_with_header({
            'total_volume_m3': 40.315, 'guide_number': 'ASIGN-2',
            'supplier_name': 'Proveedor Asign Dos S.A.',
            'supplier_rut': '96.510.970-9',
            'supplier_confidence': 'low',
        })
        partner = self.env['res.partner'].create({
            'name': 'Proveedor Asign Dos S.A.', 'is_company': True,
        })
        wizard = self.env['madenat.lumber.intake.supplier.link'].create({
            'guia_id': guia.id,
            'supplier_id': partner.id,
        })
        wizard.action_confirm_link()

        self.assertEqual(guia.partner_id, partner)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_manual')
        bodies = '\n'.join(m.body or '' for m in guia.message_ids)
        self.assertIn('Proveedor asignado manualmente', bodies)
