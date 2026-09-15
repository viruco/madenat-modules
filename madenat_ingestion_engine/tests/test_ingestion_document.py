# -*- coding: utf-8 -*-
"""Tests del modelo `madenat.ingestion.document` (UI de ingesta).

Fixtures SINTÉTICOS construidos en memoria con openpyxl.
"""
import base64
import io

from openpyxl import Workbook

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.models.ingestion_document_line import (
    _decimal_inch_to_fraction_str,
)


METRIC_HEADER = ["N°", "CODIGOS", "PRODUCTO", "LOTE", "ESPESOR", "ANCHO",
                 "LARGO", "FILAS", "COLUMNAS", "PIEZAS", "VOLUMEN"]


def _metric_row(pkg, code, lote):
    return [pkg, code, "MADERA DE PRUEBA", lote, 38.1, 170, 4.05,
            25, 6, 150, 3.8862]


def _to_xlsx_b64(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class TestIngestionDocument(TransactionCase):

    def test_extract_without_file_raises(self):
        doc = self.env["madenat.ingestion.document"].create({})
        self.assertEqual(doc.state, "draft")
        with self.assertRaises(UserError):
            doc.action_extract()

    def test_extract_valid_excel(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", ""),
                _metric_row("2", "0000000000002", "LOTE-2")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        self.assertEqual(doc.state, "extracted")
        self.assertEqual(len(doc.line_ids), 2)
        self.assertEqual(doc.warning_count, len(doc.warning_ids))
        self.assertTrue(doc.warning_count > 0)

    def test_reprocess_extracted_raises(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        self.assertEqual(doc.state, "extracted")
        with self.assertRaises(UserError):
            doc.action_extract()

    def test_write_extracted_document_raises(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        with self.assertRaises(UserError):
            doc.write({"filename": "cambiado.xlsx"})

    def test_unlink_extracted_document_raises(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        with self.assertRaises(UserError):
            doc.unlink()

    def test_write_line_raises(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        line = doc.line_ids[0]
        with self.assertRaises(UserError):
            line.write({"package_no": "999"})

    def test_extract_error_state(self):
        rows = [["foo", "bar", "baz"], ["1", "2", "3"]]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()
        self.assertEqual(doc.state, "error")
        self.assertTrue(doc.error_message)

    def test_has_warning_matches_row(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", ""),
                _metric_row("2", "0000000000002", "LOTE-2")]
        doc = self.env["madenat.ingestion.document"].create({
            "file": _to_xlsx_b64(rows),
            "filename": "test.xlsx",
        })
        doc.action_extract()

        warning = doc.warning_ids
        self.assertEqual(len(warning), 1)
        self.assertEqual(warning.row_number, 2)

        warned_lines = doc.line_ids.filtered("has_warning")
        self.assertEqual(len(warned_lines), 1)
        self.assertEqual(warned_lines.source_row_number, 2)

    def test_decimal_inch_to_fraction_str_matches_core(self):
        """La réplica produce exactamente el mismo string que Core (mismos casos)."""
        cases = {
            "1.5625": "1 9/16",
            "2.625": "2 5/8",
            "3.625": "3 5/8",
            "4.625": "4 5/8",
            "5.625": "5 5/8",
            "1.25": "1 1/4",
            "1.5": "1 1/2",
            "2.0": "2",
        }
        for decimal, expected in cases.items():
            self.assertEqual(
                _decimal_inch_to_fraction_str(decimal), expected,
                f"{decimal} -> {expected}",
            )
        # Casos límite idénticos a Core: vacío / <=0 / basura.
        self.assertEqual(_decimal_inch_to_fraction_str(None), "")
        self.assertEqual(_decimal_inch_to_fraction_str(""), "")
        # 0 == False → cae en el primer `if`, igual que Core (retorna "").
        self.assertEqual(_decimal_inch_to_fraction_str(0), "")
        self.assertEqual(_decimal_inch_to_fraction_str(-1.5), "0")
        self.assertEqual(_decimal_inch_to_fraction_str("N/A"), "N/A")

    def test_line_display_imperial_fraction_and_metric_raw(self):
        """El campo display muestra fracción para pulgadas y crudo para mm."""
        doc = self.env["madenat.ingestion.document"].create({
            "file": base64.b64encode(b"x").decode(),
            "filename": "test.xlsx",
        })
        imperial = self.env["madenat.ingestion.document.line"].create({
            "document_id": doc.id,
            "thickness_value_raw": "1.5625",
            "thickness_unit": "inch",
            "width_value_raw": "3.625",
            "width_unit": "inch",
        })
        self.assertEqual(imperial.thickness_display, "1 9/16")
        self.assertEqual(imperial.width_display, "3 5/8")

        metric = self.env["madenat.ingestion.document.line"].create({
            "document_id": doc.id,
            "thickness_value_raw": "45",
            "thickness_unit": "mm",
            "width_value_raw": "75",
            "width_unit": "mm",
        })
        self.assertEqual(metric.thickness_display, "45")
        self.assertEqual(metric.width_display, "75")
