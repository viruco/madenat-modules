# -*- coding: utf-8 -*-
"""Pruebas para la plantilla estándar PACKING_METRICO_ASERRADA (WP-E).

Verifica que el archivo Excel modelo `PLANTILLA_PACKING_METRICO_ASERRADA.xlsx`
se lea y procese correctamente mediante el motor de ingesta:
1. Detección automática del perfil `packing_metrico_aserrada`.
2. Extracción correcta de metadatos de cabecera (cliente, guía, fecha).
3. Normalización precisa de líneas, dimensiones (mm / m), piezas y volumen m³.
"""
import os
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
)


@tagged("post_install", "-at_install", "madenat", "madenat_ingestion_engine")
class TestPackingMetricoTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "templates",
            "PLANTILLA_PACKING_METRICO_ASERRADA.xlsx",
        )
        cls.template_path = os.path.abspath(template_path)
        with open(cls.template_path, "rb") as f:
            cls.file_bytes = f.read()

    def test_01_template_file_exists_and_readable(self):
        """Verifica que el archivo de plantilla exista y contenga bytes válidos."""
        self.assertTrue(
            os.path.exists(self.template_path),
            f"La plantilla no existe en {self.template_path}",
        )
        self.assertGreater(len(self.file_bytes), 1000, "El archivo XLSX está vacío o corrupto")

    def test_02_template_extraction_profile_and_header(self):
        """Verifica detección de perfil y extracción de cabecera."""
        res = extract_document(self.file_bytes, "PLANTILLA_PACKING_METRICO_ASERRADA.xlsx")
        self.assertEqual(
            res.detected_profile_code,
            "packing_metrico_aserrada",
            "La plantilla debe autodetectarse como packing_metrico_aserrada",
        )
        self.assertEqual(res.header.get("customer_name"), "MADENAT S.A.")
        self.assertEqual(res.header.get("guide_number"), "12345")
        self.assertEqual(res.header.get("guide_date"), "2026-10-17")

    def test_03_template_lines_data_and_units(self):
        """Verifica la extracción normalizada de las 4 líneas de ejemplo."""
        res = extract_document(self.file_bytes, "PLANTILLA_PACKING_METRICO_ASERRADA.xlsx")
        self.assertEqual(len(res.lines), 4, "Debe extraer exactamente las 4 filas de ejemplo")

        # Fila 1: 38.1 x 170 x 4.05, 150 piezas, 3.886 m3
        l1 = res.lines[0]
        self.assertEqual(l1["package_no"], "1")
        self.assertEqual(l1["product_code"], "1000203040501")
        self.assertEqual(l1["product_name_original"], "PINO ASERRADO SECO KD")
        self.assertEqual(l1["lot_number"], "ETQ-001")
        self.assertEqual(l1["thickness_value_raw"], "38.1")
        self.assertEqual(l1["width_value_raw"], "170")
        self.assertEqual(l1["length_value_raw"], "4.05")
        self.assertEqual(l1["thickness_unit"], "mm")
        self.assertEqual(l1["width_unit"], "mm")
        self.assertEqual(l1["length_unit"], "m")
        self.assertEqual(l1["pieces"], 150)
        self.assertAlmostEqual(l1["volume_m3"], 3.886, places=3)

        # Fila 2: 45 x 125 x 3.60, 160 piezas, 3.240 m3
        l2 = res.lines[1]
        self.assertEqual(l2["package_no"], "2")
        self.assertEqual(l2["lot_number"], "ETQ-002")
        self.assertEqual(l2["pieces"], 160)
        self.assertAlmostEqual(l2["volume_m3"], 3.240, places=3)

    def test_04_synthetic_data_roundtrip_accepted(self):
        """Demuestra que el extractor de packing_metrico_aserrada acepta la plantilla
        llenada con datos sintéticos (ida y vuelta: escritura en plantilla -> extracción).
        """
        import io
        import openpyxl

        # Cargar la plantilla base en memoria
        wb = openpyxl.load_workbook(io.BytesIO(self.file_bytes))
        ws = wb.active

        # Escribir cabecera sintética
        ws["B2"] = "PROVEEDOR SINTETICO S.A."
        ws["E2"] = "GUIA-SINT-999"
        ws["H2"] = "2026-11-01"

        # Sobrescribir filas de datos con datos sintéticos
        ws["A5"] = 101
        ws["B5"] = "PRD-SYNTH-1"
        ws["C5"] = "PINO RADIATA ASERRADO"
        ws["D5"] = "LOTE-SYNTH-001"
        ws["E5"] = 25.4
        ws["F5"] = 100.0
        ws["G5"] = 3.20
        ws["H5"] = 20
        ws["I5"] = 10
        ws["J5"] = 200
        ws["K5"] = 1.626

        ws["A6"] = 102
        ws["B6"] = "PRD-SYNTH-2"
        ws["C6"] = "PINO VERDE DIMENSIONADO"
        ws["D6"] = "LOTE-SYNTH-002"
        ws["E6"] = 50.0
        ws["F6"] = 150.0
        ws["G6"] = 4.00
        ws["H6"] = 10
        ws["I6"] = 8
        ws["J6"] = 80
        ws["K6"] = 2.400

        # Eliminar filas 7 y 8 que tenían ejemplos en la plantilla original
        ws.delete_rows(7, 2)

        buf = io.BytesIO()
        wb.save(buf)
        synth_bytes = buf.getvalue()

        # Extraer usando el lector oficial de producción
        res = extract_document(synth_bytes, "PACKING_SINTETICO.xlsx")

        self.assertEqual(res.detected_profile_code, "packing_metrico_aserrada")
        self.assertEqual(res.header.get("customer_name"), "PROVEEDOR SINTETICO S.A.")
        self.assertEqual(res.header.get("guide_number"), "GUIA-SINT-999")
        self.assertEqual(res.header.get("guide_date"), "2026-11-01")
        self.assertEqual(len(res.lines), 2)

        l1 = res.lines[0]
        self.assertEqual(l1["package_no"], "101")
        self.assertEqual(l1["lot_number"], "LOTE-SYNTH-001")
        self.assertEqual(l1["thickness_value_raw"], "25.4")
        self.assertEqual(l1["width_value_raw"], "100")
        self.assertEqual(l1["length_value_raw"], "3.2")
        self.assertEqual(l1["pieces"], 200)
        self.assertAlmostEqual(l1["volume_m3"], 1.626, places=3)

        l2 = res.lines[1]
        self.assertEqual(l2["package_no"], "102")
        self.assertEqual(l2["lot_number"], "LOTE-SYNTH-002")
        self.assertEqual(l2["thickness_value_raw"], "50")
        self.assertEqual(l2["width_value_raw"], "150")
        self.assertEqual(l2["length_value_raw"], "4")
        self.assertEqual(l2["pieces"], 80)
        self.assertAlmostEqual(l2["volume_m3"], 2.400, places=3)

