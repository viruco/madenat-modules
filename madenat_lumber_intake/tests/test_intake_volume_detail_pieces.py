# -*- coding: utf-8 -*-
"""Piezas declaradas por línea: extracción real y persistencia (Volumen).

Cubre de punta a punta, SIN mocks del motor (se ejecuta el extractor real):

1. Guía de Despacho real (fixture del repo) SIN columna de piezas: las 12
   líneas documentales se persisten con ``pieces = 0`` — nunca con el marcador
   técnico histórico — y el volumen oficial no cambia.
2. Packing list con columna de piezas inequívoca («Cantidad», convención
   MADENAT auditada): las piezas se persisten por línea (se verifican sobre las
   propias líneas del detalle). El contador «Piezas declaradas en líneas» de la
   consola NO las cuenta: suma solo las filas DECLARADAS de la grilla
   (cabecera/manual), no las documentales del PDF/Excel.
3. Valor ambiguo o no numérico: no se persiste cantidad y se informa.
4. Re-procesamiento idempotente: aplicar dos veces el mismo documento no
   duplica líneas ni cantidades.
5. Corrección manual: el ajuste del operador marca ``manually_adjusted`` y
   sobrevive a un nuevo procesamiento.

TransactionCase: nada se persiste. No se tocan guías/lotes/pickings reales.
"""

import base64
import io
import os
import uuid
from unittest.mock import patch

from openpyxl import Workbook

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
)
from odoo.addons.madenat_lumber_intake.models import (
    intake_wizard as intake_wizard_module,
)
from .intake_reading_helpers import mark_previewed

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
GUIA_PDF = os.path.join(FIXTURES, 'HLZF75_4495589.pdf')
CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'

PACKING_HEADER = [
    "Item", "Codigo Interno", "Producto", "Espesor", "Ancho", "Largo",
    "Cantidad", "M3", "Embalaje", "N° LOTE", "Producción",
]
PACKING_ROWS = [
    [1, "PCLAT03301253700", "PINO CEP. SECO LATERAL", 37, 125, 3700, 264,
     4.5177, "Taco", "D8828", "2026-09-01"],
    [2, "PCLAT03301254050", "PINO CEP. SECO LATERAL", 37, 125, 4050, 197,
     3.69005625, "Taco", "D8840", "2026-09-01"],
    [3, "PCLAT03301303700", "PINO CEP. SECO LATERAL", 37, 130, 3700, 134,
     2.293075, "Taco", "D8834", "2026-09-03"],
]
AMBIGUOUS_ROWS = [
    [1, "PCLAT03301253700", "PINO CEP. SECO LATERAL", 37, 125, 3700, "N/A",
     4.5177, "Taco", "D8828", "2026-09-01"],
    [2, "PCLAT03301254050", "PINO CEP. SECO LATERAL", 37, 125, 4050, 197,
     3.69005625, "Taco", "D8840", "2026-09-01"],
]


def _to_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDetailPieces(TransactionCase):
    """Piezas declaradas: extracción real, persistencia y protección manual."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.lumber.volume.detail.line']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')

    # ── Helpers ────────────────────────────────────────────────────────────
    def _extract_unique_guide(self, file_bytes, filename, column_profile=None):
        """Motor REAL de extracción; sólo neutraliza el folio de la guía real.

        El fixture es el PDF de una guía real ya existente en la base, y la
        guía tiene restricción única (nombre + proveedor): se reescribe el
        folio extraído para no colisionar con ese registro. Las líneas, piezas,
        volúmenes y advertencias provienen del motor real sin cambios.
        """
        result = extract_document(
            file_bytes, filename, column_profile=column_profile)
        if result.header.get('guide_number') == '4495589':
            result.header['guide_number'] = 'UX-PIEZAS-%s' % uuid.uuid4().hex[:8]
        return result

    def _ingest(self, excel_rows=None, excel_name='packing.xlsx'):
        """Ingesta real (extractor real) de guía PDF + packing opcional."""
        with open(GUIA_PDF, 'rb') as fh:
            pdf_b64 = base64.b64encode(fh.read()).decode()
        vals = {
            'intake_modality': 'volume',
            'tipo_ingreso': 'granel',
            'assignment_location_id': self.location.id,
            'pdf_file': pdf_b64,
            'pdf_filename': 'anexo_guia.pdf',
        }
        if excel_rows is not None:
            vals['excel_file'] = base64.b64encode(
                _to_xlsx(excel_rows)).decode()
            vals['excel_filename'] = excel_name
        wizard = self.Wizard.create(vals)
        mark_previewed(wizard)
        with patch.object(intake_wizard_module, 'extract_document',
                          side_effect=self._extract_unique_guide):
            wizard.action_route_document()
        guia = self.Guia.search(
            [('guide_pdf_filename', '=', 'anexo_guia.pdf')], limit=1)
        self.assertTrue(guia, 'La ingesta debe crear la guía')
        return guia

    def _console(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id)], limit=1)

    def _excel_rows_for(self, guia=None):
        """Vuelve a extraer el packing y arma las filas de transporte."""
        wizard = self.Wizard.new({
            'intake_modality': 'volume',
            'tipo_ingreso': 'granel',
        })
        result = extract_document(_to_xlsx([PACKING_HEADER] + PACKING_ROWS),
                                  'packing.xlsx')
        self.assertEqual(result.detected_profile_code,
                         'packing_metrico_aserrada')
        return wizard._build_volume_detail_vals(result.lines, 'excel')

    # ── 1. Guía real sin columna de piezas ────────────────────────────────
    def test_01_guia_real_sin_piezas_no_inventa(self):
        """12 líneas documentales reales: `pieces` = 0 (sin fabricar)."""
        guia = self._ingest()
        lines = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'pdf')
        self.assertEqual(len(lines), 12, 'El PDF real aporta 12 líneas')
        self.assertEqual(sorted(lines.mapped('pieces')), [0] * 12)
        self.assertFalse(any(lines.mapped('manually_adjusted')))
        self.assertAlmostEqual(
            sum(lines.mapped('volume_m3')), 40.3, places=3)
        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertEqual(guia.official_volume_source, 'Guía PDF')
        console = self._console(guia)
        self.assertEqual(console.declared_lines_pieces, 0)
        self.assertAlmostEqual(
            console.declared_lines_volume_m3, 40.3, places=3)

    # ── 2. Packing list con columna de piezas inequívoca ──────────────────
    def test_02_packing_excel_persiste_piezas_documentales(self):
        """«Cantidad» del packing list se persiste por línea y suma bien."""
        guia = self._ingest([PACKING_HEADER] + PACKING_ROWS)
        lines = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel')
        self.assertEqual(len(lines), 3)
        self.assertEqual(
            sorted(lines.mapped('pieces')), [134, 197, 264])
        self.assertEqual(
            sorted(lines.mapped('origin')), ['excel'] * 3)
        self.assertFalse(
            any(lines.mapped('manually_adjusted')),
            'Un dato documental no es un ajuste manual')
        self.assertEqual(
            sorted(lines.mapped('source_line_no')), [1, 2, 3])
        self.assertEqual(
            sorted(lines.mapped('lot_or_package')),
            ['D8828', 'D8834', 'D8840'])
        self.assertEqual(
            sorted(lines.mapped('thickness_declared')), ['37'] * 3)
        console = self._console(guia)
        self.assertEqual(
            console.declared_lines_pieces, 0,
            'La grilla declarada solo contabiliza sus filas (header/manual): '
            'las piezas documentales del Excel quedan en las líneas del detalle')
        # El volumen oficial sigue siendo el documental de la guía PDF.
        self.assertAlmostEqual(console.official_volume_effective_m3,
                               40.315, places=3)
        self.assertEqual(console.official_volume_effective_source, 'Guía PDF')

    # ── 3. Valor ambiguo: no se persiste ni bloquea ───────────────────────
    def test_03_valor_ambiguo_no_persiste_y_reporta(self):
        """Celda no numérica: 0 piezas, advertencia en chatter, sin error."""
        guia = self._ingest([PACKING_HEADER] + AMBIGUOUS_ROWS)
        lines = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel'
            and line.lot_or_package == 'D8828')
        self.assertEqual(len(lines), 1)
        self.assertEqual(
            lines.pieces, 0, 'Un valor ambiguo no se convierte en cantidad')
        other = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel'
            and line.lot_or_package == 'D8840')
        self.assertEqual(other.pieces, 197)
        messages = self.env['mail.message'].search([
            ('model', '=', 'madenat.guia.processing'),
            ('res_id', '=', guia.id),
        ])
        self.assertTrue(
            any("'pieces' con valor no numérico" in (message.body or '')
                for message in messages),
            'La incidencia debe quedar advertida en el chatter')
        console = self._console(guia)
        self.assertEqual(
            console.declared_lines_pieces, 0,
            'El contador de la grilla no cuenta las filas documentales del Excel')

    # ── 4. Re-procesamiento idempotente ───────────────────────────────────
    def test_04_reprocesamiento_no_duplica(self):
        """Aplicar dos veces el mismo documento no duplica líneas ni piezas."""
        guia = self._ingest([PACKING_HEADER] + PACKING_ROWS)
        rows = self._excel_rows_for(guia)
        lines = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel')
        ids_before = sorted(lines.ids)
        pieces_before = sorted(lines.mapped('pieces'))

        first = lines._apply_documental_pieces(rows)
        second = lines._apply_documental_pieces(rows)
        self.env.invalidate_all()
        lines = self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel')

        self.assertEqual(sorted(lines.ids), ids_before, 'Sin duplicados')
        self.assertEqual(
            sorted(lines.mapped('pieces')), pieces_before,
            'Las cantidades no se duplican ni se alteran')
        self.assertEqual(first['applied'] + second['applied'], 0)
        self.assertEqual(first['protected'] + second['protected'], 0)
        self.assertEqual(len(lines), 3)

    # ── 5. Corrección manual protegida ────────────────────────────────────
    def test_05_correccion_manual_persiste_tras_reprocesar(self):
        """La corrección del operador marca el ajuste y no se sobrescribe."""
        guia = self._ingest([PACKING_HEADER] + PACKING_ROWS)
        lines = guia.volume_detail_line_ids.filtered(
            lambda line: line.origin == 'excel')
        target = lines.filtered(
            lambda line: line.lot_or_package == 'D8828')
        self.assertEqual(target.pieces, 264)

        # Corrección manual del operador (como la grilla de la consola).
        target.write({'pieces': 999})
        self.env.invalidate_all()
        target = self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.lot_or_package == 'D8828')
        self.assertEqual(target.pieces, 999)
        self.assertTrue(
            target.manually_adjusted,
            'La edición manual debe marcar `manually_adjusted`')

        # Re-procesamiento del mismo documento: la corrección persiste.
        rows = self._excel_rows_for(guia)
        summary = self.Guia.browse(
            guia.id).volume_detail_line_ids._apply_documental_pieces(rows)
        self.env.invalidate_all()
        target = self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.lot_or_package == 'D8828')
        self.assertEqual(
            target.pieces, 999, 'El ajuste manual nunca se sobrescribe')
        self.assertTrue(target.manually_adjusted)
        self.assertEqual(summary['protected'], 1)

    # ── 6. UX: trazabilidad del ajuste manual en la grilla existente ──────
    def test_06_vista_muestra_origen_y_ajuste_manual(self):
        """La grilla declarada distingue dato documental de dato corregido."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(self.env.ref(CONSOLE_FORM).arch)
        nodes = root.findall(".//field[@name='declared_piece_line_ids']")
        self.assertEqual(len(nodes), 1)
        columns = [field.get('name') for field in
                   nodes[0].findall('.//list/field')]
        self.assertIn('origin', columns)
        self.assertIn('manually_adjusted', columns)
        for name in ('origin', 'manually_adjusted'):
            node = nodes[0].find(".//list/field[@name='%s']" % name)
            self.assertEqual(
                node.get('readonly'), '1',
                '%s debe ser de solo lectura (evidencia/trazabilidad)' % name)
