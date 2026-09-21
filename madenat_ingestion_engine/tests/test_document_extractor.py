# -*- coding: utf-8 -*-
"""
Tests reales de `extract_document()` — Fase 2.

Todos los fixtures son SINTÉTICOS (construidos en memoria con openpyxl o
texto mockeado para PDF), sin datos reales de clientes/proveedores.
"""
import io
from unittest import mock

from openpyxl import Workbook

from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.column_matching import (
    normalize_text,
    score_column_match,
)
from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    extract_document,
    _to_raw_text,
)
from odoo.addons.madenat_ingestion_engine.services.ingestion_profiles import (
    PACKING_IMPERIAL_BLANKS,
    PACKING_METRICO_ASERRADA,
)


METRIC_HEADER = ["N°", "CODIGOS", "PRODUCTO", "LOTE", "ESPESOR", "ANCHO",
                 "LARGO", "FILAS", "COLUMNAS", "PIEZAS", "VOLUMEN"]
IMPERIAL_HEADER = list(METRIC_HEADER)


def _metric_row(pkg, code, lote, product="MADERA DE PRUEBA", thickness=38.1):
    return [pkg, code, product, lote, thickness, 170, 4.05,
            25, 6, 150, 3.8862]


def _imperial_row(pkg, code, lote, product="MADERA DE PRUEBA IMPERIAL"):
    return [pkg, code, product, lote, 1.5625, 3.625, 16.0,
            26, 11, 286, 5.0616]


def _to_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _patch_pdf_text(text):
    fake_page = mock.Mock()
    fake_page.extract_text.return_value = text
    fake_pdf = mock.Mock()
    fake_pdf.pages = [fake_page]
    fake_pdf.__enter__ = mock.Mock(return_value=fake_pdf)
    fake_pdf.__exit__ = mock.Mock(return_value=False)
    return mock.patch("pdfplumber.open", return_value=fake_pdf)


class TestDocumentExtractor(TransactionCase):

    def test_excel_complete_rows_no_warnings(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1"),
                _metric_row("2", "0000000000002", "LOTE-2")]
        result = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.detected_profile_code, "packing_metrico_aserrada")
        self.assertEqual(result.lines[0]["package_no"], "1")
        self.assertEqual(result.lines[0]["lot_number"], "LOTE-1")
        self.assertEqual(result.lines[0]["pieces"], 150)
        self.assertEqual(result.lines[0]["volume_m3"], 3.8862)
        self.assertEqual(result.lines[0]["thickness_value_raw"], "38.1")
        self.assertEqual(result.lines[0]["width_value_raw"], "170")
        self.assertEqual(result.lines[0]["length_value_raw"], "4.05")
        self.assertEqual(result.lines[0]["thickness_unit"], "mm")
        self.assertEqual(result.lines[0]["width_unit"], "mm")
        self.assertEqual(result.lines[0]["length_unit"], "m")
        self.assertEqual(result.lines[0]["product_name_original"], "MADERA DE PRUEBA")

    def test_excel_missing_lot_synthesized_and_forward_filled(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", ""),
                _metric_row("2", "0000000000002", "")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertEqual(result.lines[0]["lot_number"], "LOTE-0000000000001")
        self.assertEqual(result.lines[1]["lot_number"], "LOTE-0000000000001")
        self.assertTrue(any("sintetizado" in w for w in result.warnings))
        self.assertTrue(any("heredado" in w for w in result.warnings))

    def test_excel_empty_row_skipped_without_warning(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1"),
                [None] * 11,
                _metric_row("2", "0000000000002", "LOTE-2")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.warnings, [])

    def test_excel_no_header_raises(self):
        rows = [["foo", "bar", "baz"], ["1", "2", "3"]]
        with self.assertRaises(DocumentExtractionError):
            extract_document(_to_xlsx(rows), "test.xlsx")

    def test_imperial_carrier_fields_in_header(self):
        metadata = [
            ["RUT", "11.111.111-1"],
            ["FONO", "912345678"],
            ["TRANS", "Transportista Ejemplo"],
        ]
        rows = metadata + [IMPERIAL_HEADER, _imperial_row("1", "A1M001", "LOTE-A")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_IMPERIAL_BLANKS
        )
        self.assertEqual(result.header.get("carrier_rut"), "11.111.111-1")
        self.assertEqual(result.header.get("carrier_phone"), "912345678")
        self.assertEqual(result.header.get("carrier_name"), "Transportista Ejemplo")

    def test_metric_without_carrier_fields(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertNotIn("carrier_rut", result.header)
        self.assertNotIn("carrier_phone", result.header)
        self.assertNotIn("carrier_name", result.header)
        self.assertEqual(result.warnings, [])

    def test_auto_detection(self):
        metric = extract_document(
            _to_xlsx([METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]),
            "m.xlsx",
        )
        self.assertEqual(metric.detected_profile_code, "packing_metrico_aserrada")
        imperial = extract_document(
            _to_xlsx([IMPERIAL_HEADER, _imperial_row("1", "A1M001", "LOTE-A")]),
            "i.xlsx",
        )
        self.assertEqual(imperial.detected_profile_code, "packing_imperial_blanks")

    def test_explicit_profile_no_auto_detection(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        target = ("odoo.addons.madenat_ingestion_engine.services."
                  "document_extractor.detect_profile")
        with mock.patch(target) as mock_detect:
            result = extract_document(
                _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
            )
            mock_detect.assert_not_called()
        self.assertEqual(result.detected_profile_code, "packing_metrico_aserrada")

    def test_pdf_header_extraction(self):
        text = (
            "GUIA DE DESPACHO Nº 12345\n"
            "27 de marzo de 2026\n"
            "R.U.T.: 11.111.111-1\n"
            "Señor(es): Cliente Ejemplo S.A.\n"
            "R.U.T.: 22.222.222-2\n"
            "Orden: OC-EJEMPLO-001\n"
            "Transportista: Transportista Ejemplo\n"
            "RUT Transportista: 33.333.333-3\n"
            "Patente: AA-BB-11\n"
            "Neto: $ 1.000.000\n"
            "19% I.V.A. $ 190.000\n"
            "Total: $ 1.190.000\n"
            "Destino: DESTINO-EJEMPLO\n"
        )
        with _patch_pdf_text(text):
            result = extract_document(b"x", "test.pdf")
        self.assertEqual(result.header["guide_number"], "12345")
        self.assertEqual(result.header["guide_date"], "2026-03-27")
        self.assertEqual(result.header["supplier_rut"], "11.111.111-1")
        self.assertEqual(result.header["customer_name"], "Cliente Ejemplo S.A.")
        self.assertEqual(result.header["customer_rut"], "22.222.222-2")
        self.assertEqual(result.header["oc_reference"], "OC-EJEMPLO-001")
        self.assertEqual(result.header["carrier_name"], "Transportista Ejemplo")
        self.assertEqual(result.header["carrier_rut"], "33.333.333-3")
        self.assertEqual(result.header["license_plate"], "AA-BB-11")
        self.assertEqual(result.header["net_total"], 1000000.0)
        self.assertEqual(result.header["total"], 1190000.0)
        self.assertEqual(result.header["destination_label"], "DESTINO-EJEMPLO")

    def test_pdf_no_labels_general_warning(self):
        with _patch_pdf_text("Documento sin etiquetas reconocibles."):
            result = extract_document(b"x", "test.pdf")
        self.assertEqual(result.header, {})
        self.assertTrue(any("guide_number" in w for w in result.warnings))

    def test_score_column_match(self):
        self.assertEqual(score_column_match("CODIGOS", ["codigos"]), 100)
        self.assertEqual(score_column_match("N°", ["n°"]), 100)
        self.assertEqual(score_column_match("ESPESOR MM", ["espesor"]), 80)
        self.assertEqual(score_column_match("LARGOMETRO", ["largo"]), 60)
        self.assertEqual(score_column_match("XYZCODIGOXYZ", ["codigo"]), 40)
        self.assertEqual(score_column_match("FOO", ["bar"]), 0)
        self.assertEqual(normalize_text("  ESPESOR  MM  "), "espesor mm")
        self.assertEqual(normalize_text("N°"), "n")

    def test_destination_label_absent_no_warning(self):
        rows = [METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertNotIn("destination_label", result.header)
        self.assertEqual(result.warnings, [])

    def test_source_units_metric_and_imperial(self):
        metric = extract_document(
            _to_xlsx([METRIC_HEADER, _metric_row("1", "0000000000001", "LOTE-1")]),
            "m.xlsx", column_profile=PACKING_METRICO_ASERRADA,
        )
        self.assertEqual(metric.lines[0]["thickness_unit"], "mm")
        self.assertEqual(metric.lines[0]["width_unit"], "mm")
        self.assertEqual(metric.lines[0]["length_unit"], "m")

        imperial = extract_document(
            _to_xlsx([IMPERIAL_HEADER, _imperial_row("1", "A1M001", "LOTE-A")]),
            "i.xlsx", column_profile=PACKING_IMPERIAL_BLANKS,
        )
        self.assertEqual(imperial.lines[0]["thickness_unit"], "inch")
        self.assertEqual(imperial.lines[0]["width_unit"], "inch")
        self.assertEqual(imperial.lines[0]["length_unit"], "ft")

    def test_fraction_preserved_as_string(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1", thickness="1 1/16")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertEqual(result.lines[0]["thickness_value_raw"], "1 1/16")
        self.assertEqual(result.lines[0]["thickness_unit"], "mm")

    def test_product_name_original_exact(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1",
                            product="Madera Prueba Césped Ñ")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertEqual(
            result.lines[0]["product_name_original"], "Madera Prueba Césped Ñ"
        )

    def test_empty_product_name_no_default(self):
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1", product="")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertIn(result.lines[0]["product_name_original"], (None, ""))
        self.assertEqual(result.warnings, [])

    def test_to_raw_text_numeric_cleaning(self):
        # Entero exacto (int o float) → sin sufijo ".0"
        self.assertEqual(_to_raw_text(16.0), "16")
        self.assertEqual(_to_raw_text(16), "16")
        # Ruido de punto flotante → limpiado a 6 decimales
        self.assertEqual(_to_raw_text(4.050000000000001), "4.05")
        # Decimal significativo real → preservado sin redondeo agresivo
        self.assertEqual(_to_raw_text(3.625), "3.625")
        # Texto/fracción → sin cambios (solo strip)
        self.assertEqual(_to_raw_text("1 1/16"), "1 1/16")
        self.assertEqual(_to_raw_text("  MADERA DE PRUEBA  "), "MADERA DE PRUEBA")
        # None → None
        self.assertIsNone(_to_raw_text(None))

    def test_numeric_integer_cell_no_decimal_suffix(self):
        rows = [IMPERIAL_HEADER, _imperial_row("1", "A1M001", "LOTE-A")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_IMPERIAL_BLANKS
        )
        self.assertEqual(result.lines[0]["length_value_raw"], "16")

    def test_imperial_unit_label_row_excluded_with_warning(self):
        """La fila fantasma de unidades (PQTE./mm./mm/M3) se excluye con aviso."""
        unit_row = ["PQTE.", None, None, None, "mm.", "mm", "mm",
                    None, None, None, "M3"]
        rows = [IMPERIAL_HEADER, unit_row,
                _imperial_row("1", "A1M001", "LOTE-A")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_IMPERIAL_BLANKS
        )
        self.assertEqual(len(result.lines), 1)
        self.assertEqual(result.lines[0]["package_no"], "1")
        self.assertTrue(any("unidades" in w for w in result.warnings))

    def test_imperial_no_unit_row_keeps_all_lines(self):
        """Sin fila fantasma no se excluye ninguna línea."""
        rows = [IMPERIAL_HEADER,
                _imperial_row("1", "A1M001", "LOTE-A"),
                _imperial_row("2", "A1M002", "LOTE-B")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_IMPERIAL_BLANKS
        )
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.warnings, [])

    def test_metric_no_unit_row_unchanged(self):
        """Archivo métrico normal: mismo comportamiento (sin exclusiones)."""
        rows = [METRIC_HEADER,
                _metric_row("1", "0000000000001", "LOTE-1"),
                _metric_row("2", "0000000000002", "LOTE-2")]
        result = extract_document(
            _to_xlsx(rows), "test.xlsx", column_profile=PACKING_METRICO_ASERRADA
        )
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.warnings, [])

    def test_partial_non_numeric_data_row_not_excluded(self):
        """Una fila real con un solo campo no numérico NO se excluye completa."""
        row = ["1", "A1M001", "MADERA DE PRUEBA", "LOTE-A",
               "N/A", 3.625, 16.0, 26, 11, 286, 5.0616]
        result = extract_document(
            _to_xlsx([IMPERIAL_HEADER, row]), "test.xlsx",
            column_profile=PACKING_IMPERIAL_BLANKS,
        )
        self.assertEqual(len(result.lines), 1)
        self.assertEqual(result.lines[0]["thickness_value_raw"], "N/A")
        self.assertFalse(any("unidades" in w for w in result.warnings))


def _patch_pdf_full(text, tables=None, words=None):
    """Mockea pdfplumber.open con extract_text + extract_tables + extract_words."""
    fake_page = mock.Mock()
    fake_page.extract_text.return_value = text
    fake_page.extract_tables.return_value = tables if tables is not None else []
    fake_page.extract_words.return_value = words if words is not None else []
    fake_pdf = mock.Mock()
    fake_pdf.pages = [fake_page]
    fake_pdf.__enter__ = mock.Mock(return_value=fake_pdf)
    fake_pdf.__exit__ = mock.Mock(return_value=False)
    return mock.patch("pdfplumber.open", return_value=fake_pdf)


def _table_to_words(rows):
    """Convierte una tabla (lista de filas) a palabras con x0/top regulares."""
    words = []
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell in (None, ""):
                continue
            words.append({"x0": c * 100.0, "top": r * 20.0, "text": str(cell)})
    return words


class TestPdfDetailCascade(TransactionCase):
    """Cascada de 4 niveles para detalle PDF (motor de mejor esfuerzo)."""

    def test_nivel1_tabla_bordes_metrica(self):
        table = [METRIC_HEADER,
                 _metric_row("1", "0000000000001", "LOTE-1"),
                 _metric_row("2", "0000000000002", "LOTE-2")]
        with _patch_pdf_full("N° 123456\nCliente: PROVEEDOR", tables=[table]):
            result = extract_document(b"pdf", "test.pdf")
        self.assertEqual(len(result.lines), 2)
        self.assertAlmostEqual(result.header["total_volume_m3"], 3.8862 * 2, places=3)
        self.assertEqual(result.detected_profile_code, "packing_metrico_aserrada")
        self.assertTrue(any("Nivel 1" in w for w in result.warnings))

    def test_nivel2_clustering_sin_bordes_mismo_resultado(self):
        table = [METRIC_HEADER,
                 _metric_row("1", "0000000000001", "LOTE-1"),
                 _metric_row("2", "0000000000002", "LOTE-2")]
        words = _table_to_words(table)
        with _patch_pdf_full("N° 123456\nCliente: PROVEEDOR", tables=[], words=words):
            result = extract_document(b"pdf", "test.pdf")
        self.assertEqual(len(result.lines), 2)
        self.assertAlmostEqual(result.header["total_volume_m3"], 3.8862 * 2, places=3)
        self.assertEqual(result.lines[0]["volume_m3"], 3.8862)
        self.assertTrue(any("Nivel 2" in w for w in result.warnings))

    def test_nivel4_regex_sin_tabla(self):
        with _patch_pdf_full("N° 123456\nTotal: 130 M3", tables=[], words=[]):
            result = extract_document(b"pdf", "test.pdf")
        self.assertEqual(result.lines, [])
        self.assertAlmostEqual(result.header["total_volume_m3"], 130.0, places=3)
        self.assertTrue(any("Nivel 4" in w for w in result.warnings))

    def test_discrepancia_suma_vs_regex_prioriza_suma(self):
        table = [METRIC_HEADER,
                 _metric_row("1", "0000000000001", "LOTE-1"),
                 _metric_row("2", "0000000000002", "LOTE-2")]
        with _patch_pdf_full("N° 123456\nTotal: 130 M3", tables=[table]):
            result = extract_document(b"pdf", "test.pdf")
        # Prioriza la suma de líneas (7.7724), no el regex (130).
        self.assertAlmostEqual(result.header["total_volume_m3"], 3.8862 * 2, places=3)
        self.assertTrue(any("Discrepancia" in w for w in result.warnings))

    def test_nivel1_imperial_segundo_perfil(self):
        table = [IMPERIAL_HEADER,
                 _imperial_row("1", "A1M001", "LOTE-A"),
                 _imperial_row("2", "A1M002", "LOTE-B")]
        with _patch_pdf_full("N° 123456\nCliente: PROVEEDOR", tables=[table]):
            result = extract_document(b"pdf", "test.pdf")
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.detected_profile_code, "packing_imperial_blanks")
        self.assertEqual(result.lines[0]["thickness_unit"], "inch")
        self.assertAlmostEqual(result.header["total_volume_m3"], 5.0616 * 2, places=3)

    def test_regresion_solo_regex_igual_que_antes(self):
        """Un PDF sin tabla sigue resolviendo el total vía regex (Nivel 4)."""
        with _patch_pdf_full("N° 123456\nTotal: 130 M3", tables=[], words=[]):
            result = extract_document(b"pdf", "test.pdf")
        self.assertAlmostEqual(result.header["total_volume_m3"], 130.0, places=3)
        self.assertEqual(result.lines, [])
