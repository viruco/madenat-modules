# -*- coding: utf-8 -*-
"""Extracción de partes documentales (emisor/proveedor vs receptor/cliente).

La extracción es genérica: separa emisor y receptor por contexto (etiquetas,
membrete y posición relativa de los RUT), sin hardcodear RUT, nombre, guía ni
archivo.
"""
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    _extract_pdf_parties,
    _extract_pdf_header,
)


class TestPdfParties(TransactionCase):

    def test_caso_a_emisor_receptor_separados(self):
        text = (
            "Emisor: Maderas Arauco S.A.\n"
            "R.U.T.: 96.510.970-6\n"
            "Receptor: MADENAT CHILE LIMITADA\n"
            "R.U.T.: 76.103.087-6\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['supplier_name'], 'Maderas Arauco S.A.')
        self.assertEqual(parties['supplier_rut'], '96.510.970-6')
        self.assertEqual(parties['customer_name'], 'MADENAT CHILE LIMITADA')
        self.assertEqual(parties['customer_rut'], '76.103.087-6')
        self.assertNotEqual(parties['supplier_name'], parties['customer_name'])
        self.assertNotEqual(parties['supplier_rut'], parties['customer_rut'])
        self.assertEqual(parties['supplier_confidence'], 'high')

    def test_caso_b_emisor_en_membrete(self):
        text = (
            "Maderas Arauco S.A.\n"
            "R.U.T.: 96.510.970-6\n"
            "GIRO: Industrialización de Productos Forestales\n"
            "RUT : 76.103.087-6 FECHA : 07-Sep-2026\n"
            "SEÑOR(ES) :MADENAT CHILE LIMITADA CLI / DOC : 563009795\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['supplier_name'], 'Maderas Arauco S.A.')
        self.assertEqual(parties['supplier_rut'], '96.510.970-6')
        self.assertEqual(parties['customer_name'], 'MADENAT CHILE LIMITADA')
        self.assertEqual(parties['customer_rut'], '76.103.087-6')

    def test_caso_c_transportista_no_es_proveedor(self):
        text = (
            "Maderas Arauco S.A.\n"
            "R.U.T.: 96.510.970-6\n"
            "Cliente : MADENAT CHILE LTDA\n"
            "R.U.T. : 76.103.087-6\n"
            "Destino : BOD. TEPORSUR, CALLE N°1\n"
            "Transportista: SALAZAR REYES CAMILO\n"
            "R.U.T. Trans. : 08.057.842-3\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['supplier_rut'], '96.510.970-6')
        self.assertNotEqual(parties['supplier_rut'], '08.057.842-3')
        self.assertNotEqual(parties['customer_rut'], '08.057.842-3')

    def test_caso_d_rut_proveedor_sin_nombre(self):
        text = (
            "R.U.T.: 96.547.890-6\n"
            "GUÍA DE DESPACHO ELECTRÓNICA\n"
            "Cliente : MADENAT CHILE LTDA\n"
            "R.U.T. : 76.103.087-6\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['supplier_rut'], '96.547.890-6')
        self.assertIsNone(parties['supplier_name'])
        self.assertEqual(parties['supplier_confidence'], 'medium')

    def test_caso_e_nombre_proveedor_sin_rut(self):
        text = (
            "Maderas Arauco S.A.\n"
            "Cliente : MADENAT CHILE LTDA\n"
            "R.U.T. : 76.103.087-6\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['supplier_name'], 'Maderas Arauco S.A.')
        self.assertIsNone(parties['supplier_rut'])
        self.assertEqual(parties['supplier_confidence'], 'low')

    def test_no_primer_rut_arbitrario(self):
        # El cliente aparece PRIMERO; el emisor después. No debe usar el
        # primer RUT como proveedor.
        text = (
            "Cliente : MADENAT CHILE LTDA\n"
            "R.U.T. : 76.103.087-6\n"
            "Emisor: Maderas Arauco S.A.\n"
            "R.U.T.: 96.510.970-6\n"
        )
        parties = _extract_pdf_parties(text)
        self.assertEqual(parties['customer_rut'], '76.103.087-6')
        self.assertEqual(parties['supplier_rut'], '96.510.970-6')

    def test_header_expone_partes(self):
        text = (
            "Maderas Arauco S.A.\n"
            "R.U.T.: 96.510.970-6\n"
            "SEÑOR(ES) :MADENAT CHILE LIMITADA\n"
            "RUT : 76.103.087-6\n"
        )
        header = _extract_pdf_header(text)
        self.assertEqual(header.get('supplier_name'), 'Maderas Arauco S.A.')
        self.assertEqual(header.get('supplier_rut'), '96.510.970-6')
        self.assertEqual(header.get('customer_name'), 'MADENAT CHILE LIMITADA')
        self.assertEqual(header.get('customer_rut'), '76.103.087-6')
        self.assertIn('supplier_confidence', header)
        self.assertIn('customer_confidence', header)

    def test_sin_partes_no_crashea(self):
        parties = _extract_pdf_parties("Solo un texto sin partes documentales.")
        self.assertEqual(parties.get('supplier_confidence'), 'none')
        self.assertEqual(parties.get('customer_confidence'), 'none')
