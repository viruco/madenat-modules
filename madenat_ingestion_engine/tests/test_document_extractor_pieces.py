# -*- coding: utf-8 -*-
"""Piezas declaradas por línea: contrato del motor de extracción.

Regla auditada (separación dato real vs. marcador técnico):

* ``pieces`` es un ENTERO ≥ 0 **solo** cuando el documento declara una columna
  explícita de piezas inequívoca (familia «piezas» en la ruta genérica de PDF;
  familia «piezas/cantidad/pzas/unidades/qty/pcs» en los perfiles de packing
  list, convención MADENAT ya vigente en
  `madenat_lumber_core/models/excel_table_detection.py`).
* ``None`` significa «el documento no declara piezas por línea». El marcador
  técnico histórico de la ruta genérica (``pieces: 1``) fue eliminado: ya no
  existe ningún valor fabricado que un consumidor pueda persistir por error.
* Las filas de subtotal/total no son líneas de detalle y se omiten.
* Valores ambiguos o negativos no se informan (no se inventa cantidad).

Todos los fixtures son SINTÉTICOS (palabras con coordenadas y Excel en
memoria): no hay datos reales de clientes/proveedores.
"""
import io
from unittest import mock

from openpyxl import Workbook

from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    extract_document,
    _extract_generic_pdf_table,
)


def _word(text, x, top, width=20.0):
    return {
        "text": text, "x0": x, "x1": x + width,
        "top": top, "bottom": top + 8.0,
    }


def _patch_pdf_words(words_by_page):
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


def _build_words(header, data_rows, gap=20.0):
    words = [_word(t, x, 0.0) for (t, x) in header]
    for index, row in enumerate(data_rows, start=1):
        for (text, x) in row:
            if text in (None, ""):
                continue
            words.append(_word(text, x, index * gap))
    return words


# Cabecera tipo Guía de Despacho: «Cant.» es VOLUMEN (m³), no piezas.
GUIA_HEADER = [
    ("Codigo", 40.0), ("Detalle", 200.0), ("Cant.", 320.0), ("U/M", 400.0),
    ("Lote", 460.0), ("Precio", 530.0), ("Total", 590.0),
]

# Cabecera tipo Anexo de Guía / packing list: columna explícita «Piezas».
ANEXO_HEADER = [
    ("Material", 40.0), ("Lote", 140.0), ("Espesor", 220.0),
    ("Ancho", 280.0), ("Largo", 340.0), ("Piezas", 420.0),
    ("Volumen", 500.0),
]


def _to_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestDocumentExtractorPiezas(TransactionCase):
    """Contrato de `pieces` en el motor de extracción."""

    # ── Ruta genérica de PDF ──────────────────────────────────────────────
    def test_01_guia_sin_columna_piezas_no_inventa(self):
        """Guía con «Cant.» = volumen: `pieces` es None (sin marcador)."""
        data_rows = [
            [("997337", 40.0), ("MADERA ASERRADA", 200.0), ("2,92", 320.0),
             ("$/M3", 400.0), ("3540383149", 460.0), ("209.107", 530.0)],
            [("930803", 40.0), ("MADERA ASERRADA", 200.0), ("4,19", 320.0),
             ("$/M3", 400.0), ("PK45738", 460.0), ("209.107", 530.0)],
        ]
        words = _build_words(GUIA_HEADER, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "guia.pdf")

        self.assertEqual(len(lines), 2)
        self.assertEqual([line["pieces"] for line in lines], [None, None])
        self.assertAlmostEqual(lines[0]["volume_m3"], 2.92, places=3)
        self.assertAlmostEqual(lines[1]["volume_m3"], 4.19, places=3)
        self.assertEqual(lines[0]["lot_or_package_ref"], "3540383149")

    def test_02_anexo_con_columna_piezas_extrae_valor_real(self):
        """Columna «Piezas» explícita: se extrae el entero de la fila."""
        data_rows = [
            [("930802", 40.0), ("PK45310", 140.0), ("45", 220.0),
             ("120", 280.0), ("3660", 340.0), ("00168", 420.0),
             ("3,320", 500.0)],
            [("930802", 40.0), ("PK45547", 140.0), ("45", 220.0),
             ("170", 280.0), ("3660", 340.0), ("00144", 420.0),
             ("4,032", 500.0)],
        ]
        words = _build_words(ANEXO_HEADER, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "anexo.pdf")

        self.assertEqual(len(lines), 2)
        self.assertEqual([line["pieces"] for line in lines], [168, 144])
        self.assertAlmostEqual(lines[0]["volume_m3"], 3.32, places=3)
        self.assertAlmostEqual(lines[1]["volume_m3"], 4.032, places=3)
        self.assertEqual(lines[0]["lot_or_package_ref"], "PK45310")
        self.assertEqual(lines[0]["thickness_value_raw"], "45")
        self.assertEqual(lines[0]["length_value_raw"], "3660")

    def test_03_filas_de_totales_no_son_lineas(self):
        """Subtotales y total del documento no aportan líneas ni piezas."""
        data_rows = [
            [("930802", 40.0), ("PK45310", 140.0), ("45", 220.0),
             ("120", 280.0), ("3660", 340.0), ("00168", 420.0),
             ("3,320", 500.0)],
            [("TOTAL MATERIAL :", 40.0), ("00623", 420.0), ("17,942", 500.0)],
            [("930803", 40.0), ("PK45063", 140.0), ("45", 220.0),
             ("170", 280.0), ("3960", 340.0), ("00138", 420.0),
             ("4,181", 500.0)],
            [("TOTAL :", 40.0), ("00204", 420.0), ("40,315", 500.0)],
        ]
        words = _build_words(ANEXO_HEADER, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "anexo.pdf")

        self.assertEqual(len(lines), 2, "Los totales no deben ser líneas")
        self.assertEqual([line["pieces"] for line in lines], [168, 138])
        self.assertAlmostEqual(
            sum(line["volume_m3"] for line in lines), 7.501, places=3)

    def test_04_piezas_ambiguas_o_negativas_no_se_informan(self):
        """Valor no numérico o negativo: `pieces` None + advertencia."""
        data_rows = [
            [("930802", 40.0), ("PK45310", 140.0), ("45", 220.0),
             ("120", 280.0), ("3660", 340.0), ("N/A", 420.0),
             ("3,320", 500.0)],
            [("930802", 40.0), ("PK45547", 140.0), ("45", 220.0),
             ("170", 280.0), ("3660", 340.0), ("-5", 420.0),
             ("4,032", 500.0)],
        ]
        words = _build_words(ANEXO_HEADER, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "anexo.pdf")

        self.assertEqual([line["pieces"] for line in lines], [None, None])
        self.assertTrue(any(
            "Columna de piezas" in warning
            for warning in lines[0]["warnings"]))
        self.assertTrue(any(
            "negativo" in warning for warning in lines[1]["warnings"]))

    def test_05_fila_sin_referencia_de_linea_no_informa_piezas(self):
        """Fila de cabecera/etiqueta capturada por el clustering: sin piezas."""
        data_rows = [
            [("Centro : TD04", 40.0), ("0100", 420.0)],
            [("930802", 40.0), ("PK45310", 140.0), ("45", 220.0),
             ("120", 280.0), ("3660", 340.0), ("00168", 420.0),
             ("3,320", 500.0)],
        ]
        words = _build_words(ANEXO_HEADER, data_rows)
        with _patch_pdf_words([words]):
            lines = _extract_generic_pdf_table(b"pdf", "anexo.pdf")

        self.assertEqual([line["pieces"] for line in lines], [None, 168])

    # ── Perfiles de packing list (Excel / con dimensiones) ────────────────
    def test_06_packing_excel_cantidad_es_piezas(self):
        """Packing list MADENAT: «Cantidad» transporta las piezas por fila."""
        header = ["Item", "Codigo Interno", "Producto", "Espesor", "Ancho",
                  "Largo", "Cantidad", "M3", "Embalaje", "N° LOTE",
                  "Producción"]
        rows = [
            header,
            [1, "PCLAT03301253700", "PINO CEP. SECO LATERAL", 37, 125, 3700,
             264, 4.5177, "Taco", "D8828", "2026-09-01"],
            [2, "PCLAT03301254050", "PINO CEP. SECO LATERAL", 37, 125, 4050,
             197, 3.69005625, "Taco", "D8840", "2026-09-01"],
            [3, "PCLAT03301303700", "PINO CEP. SECO LATERAL", 37, 130, 3700,
             134, 2.293075, "Taco", "D8834", "2026-09-03"],
            ["", "", "", "", "", "TOTAL:", 595, 10.50183125, "", "", ""],
        ]
        result = extract_document(_to_xlsx(rows), "packing.xlsx")

        self.assertEqual(
            result.detected_profile_code, "packing_metrico_aserrada")
        self.assertEqual(len(result.lines), 3, "La fila TOTAL no es una línea")
        self.assertEqual(
            [line["pieces"] for line in result.lines], [264, 197, 134])
        self.assertEqual(
            [line["lot_number"] for line in result.lines],
            ["D8828", "D8840", "D8834"])
        self.assertEqual(result.lines[0]["thickness_value_raw"], "37")
        self.assertEqual(result.lines[0]["width_value_raw"], "125")
        self.assertEqual(result.lines[0]["length_value_raw"], "3700")
        self.assertTrue(any(
            "totales" in warning for warning in result.warnings))

    def test_07_packing_excel_valor_ambiguo(self):
        """Celda de piezas no numérica: no se persiste valor falso."""
        header = ["Item", "Codigo Interno", "Producto", "Espesor", "Ancho",
                  "Largo", "Cantidad", "M3", "N° LOTE"]
        rows = [
            header,
            [1, "PCLAT03301253700", "PINO", 37, 125, 3700, "N/A", 4.5177,
             "D8828"],
            [2, "PCLAT03301254050", "PINO", 37, 125, 4050, 197, 3.69005625,
             "D8840"],
        ]
        result = extract_document(_to_xlsx(rows), "packing.xlsx")

        self.assertEqual(
            [line["pieces"] for line in result.lines], [None, 197])

    def test_08_archivo_vacio_no_inventa_piezas(self):
        """Archivo vacío: error controlado (sin líneas ni piezas fabricadas)."""
        with self.assertRaises(DocumentExtractionError):
            extract_document(b"", "vacio.pdf")
