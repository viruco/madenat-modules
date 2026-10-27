# -*- coding: utf-8 -*-
"""
Pruebas de descarte de fila de totales sin etiqueta (Regla V1) — Fase 2E.

Todos los fixtures son 100% SINTÉTICOS en memoria (openpyxl y xlwt),
sin datos reales ni rutas absolutas.
"""
import io
import re

from openpyxl import Workbook

try:
    import xlwt
    HAS_XLWT = True
except ImportError:
    HAS_XLWT = False

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
)

METRIC_HEADER = [
    "N°", "CODIGOS", "PRODUCTO", "LOTE", "ESPESOR", "ANCHO",
    "LARGO", "FILAS", "COLUMNAS", "PIEZAS", "VOLUMEN",
]


def _to_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _to_xls(rows):
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Hoja1")
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if val is not None:
                ws.write(r_idx, c_idx, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_synthetic_12_rows():
    """Genera 12 filas sintéticas métricas con la distribución de volumen de 40030:
    Filas 1-2: 3.8862
    Filas 3-4: 4.0005
    Filas 5-10: 3.81
    Fila 11: 3.81
    Fila 12: 3.71475
    Suma acumulada = 46.15815
    """
    rows = [METRIC_HEADER]
    volumes = [
        (1, 150, 38.1, 170, 4.0, 3.8862),
        (2, 150, 38.1, 170, 4.0, 3.8862),
        (3, 175, 38.1, 150, 4.0, 4.0005),
        (4, 175, 38.1, 150, 4.0, 4.0005),
        (5, 200, 38.1, 125, 4.0, 3.8100),
        (6, 200, 38.1, 125, 4.0, 3.8100),
        (7, 200, 38.1, 125, 4.0, 3.8100),
        (8, 200, 38.1, 125, 4.0, 3.8100),
        (9, 200, 38.1, 125, 4.0, 3.8100),
        (10, 200, 38.1, 125, 4.0, 3.8100),
        (11, 250, 38.1, 100, 4.0, 3.8100),
        (12, 325, 38.1, 75, 4.0, 3.71475),
    ]
    for pkg, pzas, esp, anc, lar, vol in volumes:
        rows.append([
            str(pkg), "0000000095950", "MADERA SECA CEPILLADA", "LOTE-001",
            esp, anc, lar, 25, 10, pzas, vol,
        ])
    return rows


@tagged("post_install", "-at_install", "madenat", "madenat_ingestion_engine")
class TestDocumentExtractorTotalsRow(TransactionCase):

    def test_01_synthetic_12_packages_unlabeled_closing_total_row_xlsx_and_xls(self):
        """Caso 1: 12 paquetes + fila de cierre sin etiqueta con volumen = suma
        -> 12 líneas, suma 46.15815 y warning presente en XLSX y XLS.
        """
        for ext, to_bytes in [("xlsx", _to_xlsx), ("xls", _to_xls)]:
            with self.subTest(format=ext):
                if ext == "xls" and not HAS_XLWT:
                    self.skipTest("xlwt no está instalado en este entorno")
                rows = _build_synthetic_12_rows()
                # Fila 13: cierre sin etiqueta
                rows.append([None, None, None, None, None, None, None, None, None, None, 46.15815])
                file_bytes = to_bytes(rows)
                res = extract_document(file_bytes, f"test.{ext}")
                self.assertEqual(len(res.lines), 12)
                vol_sum = round(sum(l["volume_m3"] for l in res.lines), 5)
                self.assertEqual(vol_sum, 46.15815)
                # Advertencia presente
                expected_warning = (
                    "Fila 14: fila de totales sin etiqueta omitida "
                    "(volumen 46.15815 ≈ suma acumulada 46.15815)"
                )
                totals_warnings = [w for w in res.warnings if "fila de totales sin etiqueta omitida" in w]
                self.assertEqual(len(totals_warnings), 1)
                self.assertEqual(totals_warnings[0], expected_warning)

    def test_02_totals_row_with_total_label(self):
        """Caso 2: Misma estructura con fila 'TOTAL:' -> sigue descartada por filtro
        actual _TOTALS_ROW_RE (document_extractor.py:446) sin generar el warning nuevo.
        """
        rows = _build_synthetic_12_rows()
        rows.append(["TOTAL:", None, None, None, None, None, None, None, None, None, 46.15815])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 12)
        # Descartada por _TOTALS_ROW_RE: aviso exacto de document_extractor.py:446
        expected_warning = "Fila 14: se omitió una fila de totales ('total: 46.15815')."
        self.assertIn(expected_warning, res.warnings)
        self.assertFalse(any("sin etiqueta omitida" in w for w in res.warnings))

    def test_03_no_totals_row(self):
        """Caso 3: Sin fila de totales -> no se descarta nada."""
        rows = _build_synthetic_12_rows()
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 12)
        self.assertFalse(any("totales" in w.lower() for w in res.warnings))

    def test_04_row_with_package_no_matching_sum_not_discarded(self):
        """Caso 4: Fila con solo package_no cuyo volumen coincide con la suma -> NO se descarta."""
        rows = _build_synthetic_12_rows()
        # Fila 13 tiene package_no declarado
        rows.append(["13", None, None, None, None, None, None, None, None, None, 46.15815])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 13)
        self.assertEqual(res.lines[12]["package_no"], "13")
        self.assertFalse(any("sin etiqueta omitida" in w for w in res.warnings))

    def test_05_row_with_pieces_matching_sum_not_discarded(self):
        """Caso 5: Fila con solo pieces cuyo volumen coincide con la suma -> NO se descarta."""
        rows = _build_synthetic_12_rows()
        # Fila 13 tiene piezas declaradas
        rows.append([None, None, None, None, None, None, None, None, None, 100, 46.15815])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 13)
        self.assertEqual(res.lines[12]["pieces"], 100)
        self.assertFalse(any("sin etiqueta omitida" in w for w in res.warnings))

    def test_06_first_row_without_identifiers_not_discarded(self):
        """Caso 6: Primera fila del documento sin identificadores (acumulador 0) -> NO se descarta."""
        rows = [
            METRIC_HEADER,
            [None, None, None, None, None, None, None, None, None, None, 5.0],
            _build_synthetic_12_rows()[1],
        ]
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 2)
        self.assertEqual(res.lines[0]["volume_m3"], 5.0)
        self.assertFalse(any("sin etiqueta omitida" in w for w in res.warnings))

    def test_07_tolerance_boundary(self):
        """Caso 7: Tolerancia (TOTAL_ROW_TOLERANCE_M3 = 0.01).
        Diferencia de 0.009 -> se descarta.
        Diferencia de 0.011 -> se conserva.
        """
        # 7.a: Diferencia de 0.009 (46.15815 + 0.009 = 46.16715) -> se descarta
        rows_discard = _build_synthetic_12_rows()
        rows_discard.append([None, None, None, None, None, None, None, None, None, None, 46.16715])
        res_discard = extract_document(_to_xlsx(rows_discard), "test.xlsx")
        self.assertEqual(len(res_discard.lines), 12)
        self.assertTrue(any("sin etiqueta omitida" in w for w in res_discard.warnings))

        # 7.b: Diferencia de 0.011 (46.15815 + 0.011 = 46.16915) -> se conserva
        rows_keep = _build_synthetic_12_rows()
        rows_keep.append([None, None, None, None, None, None, None, None, None, None, 46.16915])
        res_keep = extract_document(_to_xlsx(rows_keep), "test.xlsx")
        self.assertEqual(len(res_keep.lines), 13)
        self.assertEqual(res_keep.lines[12]["volume_m3"], 46.16915)

    def test_08_two_consecutive_unlabeled_closing_rows(self):
        """Caso 8: Dos filas de cierre consecutivas sin etiqueta con el mismo volumen -> ambas descartadas."""
        rows = _build_synthetic_12_rows()
        rows.append([None, None, None, None, None, None, None, None, None, None, 46.15815])
        rows.append([None, None, None, None, None, None, None, None, None, None, 46.15815])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 12)
        totals_warnings = [w for w in res.warnings if "fila de totales sin etiqueta omitida" in w]
        self.assertEqual(len(totals_warnings), 2)
        self.assertIn("Fila 14: fila de totales sin etiqueta omitida", totals_warnings[0])
        self.assertIn("Fila 15: fila de totales sin etiqueta omitida", totals_warnings[1])

    def test_09_warning_format_matches_ingestion_document_regex(self):
        r"""Caso 9 (Ajuste 1): Formato del aviso debe empezar exactamente con 'Fila {N}: '
        cumpliendo con ^Fila (\d+): para parseo en ingestion_document.py:159-168.
        """
        rows = _build_synthetic_12_rows()
        rows.append([None, None, None, None, None, None, None, None, None, None, 46.15815])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        totals_warnings = [w for w in res.warnings if "fila de totales sin etiqueta omitida" in w]
        self.assertEqual(len(totals_warnings), 1)
        msg = totals_warnings[0]
        match = re.match(r"^Fila (\d+):", msg)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 14)
        expected_text = "Fila 14: fila de totales sin etiqueta omitida (volumen 46.15815 ≈ suma acumulada 46.15815)"
        self.assertEqual(msg, expected_text)

    def test_10_discarded_row_does_not_pollute_forward_fill_or_emit_lot_warning(self):
        """Caso 10 (Ajuste 2): La fila descartada no debe actualizar forward_fill_state
        ni emitir su aviso de lote heredado (document_extractor.py:511).
        """
        # Filas donde la primera declara LOTE y las demás lo heredan
        rows = [METRIC_HEADER]
        rows.append(["1", "0000000095950", "MADERA", "LOTE-HEREDADO", 38.1, 170, 4.0, 25, 10, 150, 10.0])
        rows.append(["2", "0000000095950", "MADERA", None, 38.1, 170, 4.0, 25, 10, 150, 10.0])
        # Fila 3: cierre sin etiqueta (volumen = 20.0)
        rows.append([None, None, None, None, None, None, None, None, None, None, 20.0])
        res = extract_document(_to_xlsx(rows), "test.xlsx")
        self.assertEqual(len(res.lines), 2)
        # Fila 3 hereda lote: aviso exacto de document_extractor.py:511
        expected_lot_warning = (
            "Fila 3: 'lot_number' no informado, heredado (forward-fill) de la fila anterior."
        )
        self.assertIn(expected_lot_warning, res.warnings)
        # Fila 4 (cierre): solo emite el aviso de totales sin etiqueta, NO emite 'lot_number' no informado ni heredado
        self.assertFalse(any("Fila 4: 'lot_number'" in w for w in res.warnings))
        expected_totals_warning = (
            "Fila 4: fila de totales sin etiqueta omitida (volumen 20.0 ≈ suma acumulada 20.0)"
        )
        self.assertIn(expected_totals_warning, res.warnings)
