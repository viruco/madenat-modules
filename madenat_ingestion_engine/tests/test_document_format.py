# -*- coding: utf-8 -*-
"""Detección de formato físico de documentos (PDF/XLS/XLSX) por contenido.

Cubre:
- detect_document_format (Core): pdf/xls/xlsx/zip_unknown/unknown.
- Gate0PreUpload (Core): valida por contenido, warning de extensión, bloqueo
  solo para unknown/corrupto.
- extract_document (Engine): despacha parser por formato binario real.
- Fixture equivalente a guía 95806 (PDF válido con nombre .xls).
"""

import io
import zipfile

from openpyxl import Workbook

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_core.models.document_format import (
    detect_document_format,
)
from odoo.addons.madenat_lumber_core.models.ingestion_gate import Gate0PreUpload
from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    extract_document,
)


def _build_pdf(lines):
    """Construye un PDF de una página legible por pdfplumber."""
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 780
    for line in lines:
        c.drawString(40, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


def _build_xlsx_bytes():
    """Genera un XLSX real con estructura xl/ (packing list mínimo)."""
    wb = Workbook()
    ws = wb.active
    ws.append(['N°', 'CODIGOS', 'PRODUCTO', 'LOTE', 'ESPESOR', 'ANCHO',
               'LARGO', 'FILAS', 'COLUMNAS', 'PIEZAS', 'VOLUMEN'])
    ws.append(['1', 'C1', 'MADERA', 'L1', 38.1, 170, 4.05, 25, 6, 150, 3.8862])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xls_bytes():
    """Genera un XLS legacy OLE2 real (packing list mínimo) con xlwt."""
    import xlwt

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    header = ['N°', 'CODIGOS', 'PRODUCTO', 'LOTE', 'ESPESOR', 'ANCHO',
              'LARGO', 'FILAS', 'COLUMNAS', 'PIEZAS', 'VOLUMEN']
    row = ['1', 'C1', 'MADERA', 'L1', 38.1, 170, 4.05, 25, 6, 150, 3.8862]
    for col, val in enumerate(header):
        ws.write(0, col, val)
    for col, val in enumerate(row):
        ws.write(1, col, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


@tagged('post_install', '-at_install', 'madenat', 'madenat_ingestion_engine')
class TestDocumentFormatDetection(TransactionCase):

    # ── detect_document_format ────────────────────────────────────────────
    def test_detect_pdf(self):
        self.assertEqual(detect_document_format(b"%PDF-1.4\nresto"), "pdf")

    def test_detect_xls_ole(self):
        self.assertEqual(detect_document_format(_OLE_MAGIC + b"\x00" * 64), "xls")

    def test_detect_xlsx_zip(self):
        self.assertEqual(detect_document_format(_build_xlsx_bytes()), "xlsx")

    def test_detect_zip_no_excel(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("hola.txt", "no es excel")
        self.assertEqual(detect_document_format(buf.getvalue()), "zip_unknown")

    def test_detect_unknown(self):
        self.assertEqual(detect_document_format(b"datos no reconocidos"), "unknown")
        self.assertEqual(detect_document_format(b""), "unknown")

    # ── Gate0PreUpload ────────────────────────────────────────────────────
    def test_gate0_pdf_con_nombre_xls_permite_con_warning(self):
        gate = Gate0PreUpload()
        res = gate.validate("GDE 95806.xls", _build_pdf(["GUIA 95806"]), "pdf")
        self.assertTrue(res.is_valid)
        self.assertFalse(any(e.code == "FILE_EXTENSION_INVALID" for e in res.errors))
        self.assertTrue(any(w.code == "FILE_EXTENSION_MISMATCH" for w in res.warnings))

    def test_gate0_xls_con_nombre_pdf_warning_no_error(self):
        gate = Gate0PreUpload()
        res = gate.validate("guia.pdf", _OLE_MAGIC + b"\x00" * 64, "excel")
        self.assertTrue(res.is_valid)
        self.assertFalse(any(e.code == "FILE_EXTENSION_INVALID" for e in res.errors))
        self.assertTrue(any(w.code == "FILE_EXTENSION_MISMATCH" for w in res.warnings))

    def test_gate0_xlsx_valido_sin_warning(self):
        gate = Gate0PreUpload()
        res = gate.validate("packing.xlsx", _build_xlsx_bytes(), "excel")
        self.assertTrue(res.is_valid)
        self.assertFalse(any(w.code == "FILE_EXTENSION_MISMATCH" for w in res.warnings))

    def test_gate0_zip_no_excel_bloquea(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("hola.txt", "no es excel")
        gate = Gate0PreUpload()
        res = gate.validate("packing.zip", buf.getvalue(), "excel")
        self.assertFalse(res.is_valid)
        self.assertTrue(any(e.code == "FILE_FORMAT_UNKNOWN" for e in res.errors))

    def test_gate0_corrupto_bloquea(self):
        gate = Gate0PreUpload()
        res = gate.validate("guia.pdf", b"basura corrupta", "pdf")
        self.assertFalse(res.is_valid)
        self.assertTrue(any(e.code == "FILE_FORMAT_UNKNOWN" for e in res.errors))

    def test_gate0_pdf_extension_correcta_sin_warning(self):
        gate = Gate0PreUpload()
        res = gate.validate("guia.pdf", _build_pdf(["GUIA 95806"]), "pdf")
        self.assertTrue(res.is_valid)
        self.assertFalse(any(w.code == "FILE_EXTENSION_MISMATCH" for w in res.warnings))

    # ── extract_document: despacho por formato binario ────────────────────
    def test_extract_pdf_con_nombre_xls(self):
        pdf = _build_pdf([
            "GUÍA DE DESPACHO ELECTRÓNICA Nº 95806",
            "Cliente : MADENAT CHILE LTDA Emitido : 21-AGO-2026",
            "R.U.T. : 76.103.087-6",
            "TIPO CAMBIO : 923.23 VOL.TOT. : 59.964",
            "Orden de Compra MC-0523-140 23-MAY-2026",
            "TOT.PAQ.:12 TOT PZAS.:2772",
        ])
        res = extract_document(pdf, "GDE 95806.xls")
        self.assertEqual(res.header.get("guide_number"), "95806")
        self.assertEqual(res.header.get("guide_date"), "2026-08-21")
        self.assertEqual(res.header.get("oc_reference"), "MC-0523-140")
        self.assertAlmostEqual(res.header.get("total_volume_m3") or 0.0, 59.964, places=3)

    def test_extract_xlsx_con_nombre_pdf(self):
        res = extract_document(_build_xlsx_bytes(), "packing.pdf")
        self.assertEqual(len(res.lines), 1)
        self.assertAlmostEqual(res.lines[0].get("volume_m3"), 3.8862, places=4)

    def test_detect_xls_ole_real(self):
        self.assertEqual(detect_document_format(_build_xls_bytes()), "xls")

    def test_extract_xls_legacy(self):
        """XLS legacy OLE2 se lee con xlrd, sin 'File is not a zip file'."""
        res = extract_document(_build_xls_bytes(), "95083.xls")
        self.assertEqual(len(res.lines), 1)
        self.assertAlmostEqual(res.lines[0].get("volume_m3"), 3.8862, places=4)
        self.assertEqual(res.detected_profile_code, "packing_metrico_aserrada")

    def test_extract_unknown_lanza_error(self):
        with self.assertRaises(DocumentExtractionError):
            extract_document(b"basura corrupta", "guia.pdf")

    def test_extract_zip_no_excel_lanza_error(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("hola.txt", "no es excel")
        with self.assertRaises(DocumentExtractionError):
            extract_document(buf.getvalue(), "packing.pdf")
