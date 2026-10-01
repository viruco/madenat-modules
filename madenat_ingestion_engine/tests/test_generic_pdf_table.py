# -*- coding: utf-8 -*-
"""Tests del extractor genérico de tablas PDF.

El extractor ``_extract_generic_pdf_table`` detecta una tabla a partir de
coordenadas de palabras y sinónimos de cabecera, sin depender de guía,
proveedor, nombre de archivo ni número de líneas. Estas pruebas usan fixtures
sintéticos (palabras con coordenadas) que reproducen la estructura de los
documentos reales de regresión.
"""
import os
from unittest import mock

from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
    _extract_generic_pdf_table,
)


def _word(text, x, top, width=20.0):
    return {
        "text": text,
        "x0": x,
        "x1": x + width,
        "top": top,
        "bottom": top + 8.0,
    }


def _patch_pdf_words(words_by_page):
    """Mockea ``pdfplumber.open`` devolviendo palabras por página."""
    pages = []
    for words in words_by_page:
        page = mock.Mock()
        page.extract_words.return_value = words
        page.extract_text.return_value = ""
        page.extract_tables.return_value = []
        pages.append(page)
    fake_pdf = mock.Mock()
    fake_pdf.pages = pages
    fake_pdf.__enter__ = mock.Mock(return_value=fake_pdf)
    fake_pdf.__exit__ = mock.Mock(return_value=False)
    return mock.patch("pdfplumber.open", return_value=fake_pdf)


# Cabecera alineada a las columnas (sin ambigüedad de bordes).
_HEADER_ALIGNED = [
    ("Codigo", 40.0), ("Detalle", 200.0), ("Cant.", 320.0), ("U/M", 400.0),
    ("Lote", 460.0), ("Precio", 530.0), ("Total", 590.0),
]


def _build_words(header, data_rows):
    """Construye palabras para una cabecera + filas de datos.

    Cada fila es una lista de ``(texto, x)``. Se generan filas con
    separación vertical de 20 unidades.
    """
    words = [_word(t, x, 0.0) for (t, x) in header]
    for i, row in enumerate(data_rows, start=1):
        for (t, x) in row:
            if t in (None, ""):
                continue
            words.append(_word(t, x, i * 20.0))
    return words


class TestGenericPdfTable(TransactionCase):
    """Extractor genérico de tablas PDF (por coordenadas + sinónimos)."""

    def test_tabla_12_filas_lotes_mixtos(self):
        """Fixture A: 12 filas, códigos numéricos, lotes numéricos y PK."""
        vols = ["2,92", "2,70", "2,80", "2,64", "2,94",
                "4,19", "4,18", "3,87", "2,84", "3,87", "4,03", "3,32"]
        codes = (["997337"] * 5) + (["930803"] * 4) + (["930802"] * 3)
        lots = ["3540383149", "3540378642", "3540357930", "3540357236",
                "3540341717", "PK45738", "PK45063", "PK68793", "PK45891",
                "PK45721", "PK45547", "PK45310"]
        data_rows = []
        for i in range(12):
            data_rows.append([
                (codes[i], 40.0),
                ("MADERA ASERRADA", 200.0),
                (vols[i], 320.0),
                ("$/M3", 400.0),
                (lots[i], 460.0),
                ("209.107", 530.0),
            ])
        words = _build_words(_HEADER_ALIGNED, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "regresion.pdf")

        self.assertIsNotNone(lines)
        self.assertEqual(len(lines), 12)
        vol_sum = sum(l["volume_m3"] for l in lines if l["volume_m3"])
        self.assertAlmostEqual(vol_sum, 40.300, places=3)
        refs = [l["lot_or_package_ref"] for l in lines]
        self.assertIn("3540383149", refs)
        self.assertIn("PK45738", refs)
        self.assertEqual(lines[0]["material_code"], "997337")
        self.assertEqual(lines[5]["material_code"], "930803")

    def test_tabla_una_fila_volumen(self):
        """Fixture B: una fila, cabecera Código/Detalle/Cantidad/Unid/Total."""
        header = [("Codigo", 40.0), ("Detalle", 200.0), ("Cantidad", 320.0),
                  ("Unid.", 400.0), ("Precio", 530.0), ("Total", 590.0)]
        data_rows = [[
            ("MC-0523-140", 40.0),
            ("BLANKS 5/4X5.3/8", 200.0),
            ("59,964", 320.0),
            ("M3", 400.0),
            ("396.989", 530.0),
            ("23.805.042", 590.0),
        ]]
        words = _build_words(header, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "una-fila.pdf")

        self.assertIsNotNone(lines)
        self.assertEqual(len(lines), 1)
        self.assertAlmostEqual(lines[0]["volume_m3"], 59.964, places=3)
        self.assertEqual(lines[0]["material_code"], "MC-0523-140")
        self.assertEqual(lines[0]["uom"], "M3")
        self.assertAlmostEqual(lines[0]["line_amount"], 23805042.0, places=0)

    def test_orden_columnas_distinto_y_descripcion_multilinea(self):
        """Fixture C: orden de columnas distinto y descripción multilínea."""
        header = [("Detalle", 40.0), ("Codigo", 200.0), ("Cantidad", 320.0),
                  ("Unid.", 400.0), ("Total", 530.0)]
        data_rows = [
            [
                ("MADERA", 40.0), ("ASERRADA", 52.0), ("PRIMERA", 64.0),
                ("CODE-A", 200.0), ("1,50", 320.0), ("M3", 400.0),
                ("100.000", 530.0),
            ],
            [
                ("MADERA", 40.0), ("CEPILLADA", 52.0),
                ("CODE-B", 200.0), ("2,25", 320.0), ("M3", 400.0),
                ("150.000", 530.0),
            ],
        ]
        words = _build_words(header, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "reorden.pdf")

        self.assertIsNotNone(lines)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["material_code"], "CODE-A")
        self.assertIn("MADERA", lines[0]["description"])
        self.assertAlmostEqual(lines[1]["volume_m3"], 2.25, places=3)

    def test_tabla_incompleta_lineas_parciales_sin_bloquear(self):
        """Fixture D: tabla incompleta → líneas parciales con warnings."""
        header = [("Codigo", 40.0), ("Detalle", 200.0), ("Cantidad", 320.0),
                  ("Unid.", 400.0)]
        data_rows = [
            [("CODE-1", 40.0), ("DESC-1", 200.0), ("1,00", 320.0), ("M3", 400.0)],
            [("CODE-2", 40.0), ("DESC-2", 200.0), (None, 320.0), (None, 400.0)],
        ]
        words = _build_words(header, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "incompleta.pdf")

        self.assertIsNotNone(lines)
        self.assertEqual(len(lines), 2)
        self.assertIsNone(lines[1]["volume_m3"])
        self.assertEqual(lines[1]["material_code"], "CODE-2")
        self.assertTrue(any("sin valor numérico" in w for w in lines[1]["warnings"]))

    def test_extract_document_integra_lineas_genericas(self):
        """La cascada de extracción usa el extractor genérico como fallback."""
        header = [("Codigo", 40.0), ("Detalle", 200.0), ("Cantidad", 320.0),
                  ("Unid.", 400.0), ("Total", 530.0)]
        data_rows = [[
            ("CODE-1", 40.0), ("DESC-1", 200.0), ("59,964", 320.0),
            ("M3", 400.0), ("100.000", 530.0),
        ]]
        words = _build_words(header, data_rows)
        with _patch_pdf_words([words]):
            result = extract_document(b"%PDF-1.4", "integrada.pdf")
        self.assertAlmostEqual(result.header["total_volume_m3"], 59.964, places=3)
        self.assertEqual(len(result.lines), 1)
        self.assertEqual(result.lines[0]["volume_m3"], 59.964)

    def test_no_hardcodeo_documentos_conocidos(self):
        """No debe existir condición por guía/proveedor/archivo en el código."""
        module_dir = os.path.dirname(os.path.dirname(__file__))
        src_path = os.path.join(module_dir, "services", "document_extractor.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        for needle in ("4495589", "95806", "Arauco", "HLZF75", "MC-0523-140"):
            self.assertNotIn(needle, source)
