# -*- coding: utf-8 -*-
"""Tests de aislamiento — extracción de RUT del proveedor (flujo Producto).

Diagnóstico del bug guía 26270 (sesión de solo lectura, sin fix):
- reception_parser.parse_dispatch_guide() (L565) usa UN solo regex de RUT que
  solo admite formato CON PUNTOS:  \\d{1,2}\\.\\d{3}\\.\\d{3}-[\\dkK]
- Contraste ya funcional en madenat_guia_processing._parse_dispatch_pdf()
  (L2372-2375): DOS patrones (con puntos Y sin puntos \\d{7,8}-[\\dkK]).
- lumber_reception._find_or_create_po_intelligent() (L2302-2306) lanza
  UserError bloqueante cuando supplier_rut está vacío.

Estos tests codifican el CONTRATO DESEADO. Contra el código actual se espera
que fallen: rut_sin_puntos, sin_rut_visible_no_crashea,
find_or_create_po_intelligent_sin_rut_no_bloquea y fixture_regresion_26270.

NO modifican código de producción.
"""
import io
import logging
import os

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
_FIXTURE_26270 = os.path.join(_FIXTURE_DIR, '26270.txt')


def _safe_winansi(text):
    """Sanitiza el texto para la fuente Helvetica (cp1252) usada por reportlab."""
    return text.encode('cp1252', 'replace').decode('cp1252')


def _build_pdf(lines):
    """Construye un PDF de una página legible por pdfplumber."""
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 780
    for line in lines:
        c.drawString(40, y, _safe_winansi(line))
        y -= 18
    c.save()
    return buf.getvalue()


@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'madenat_rut_extraction')
class TestReceptionSupplierRutExtraction(TransactionCase):
    """Extracción de RUT del proveedor en la guía de despacho (flujo Producto)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Parser = cls.env['madenat.reception.parser']
        cls.Reception = cls.env['lumber.reception']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Test RUT',
            'is_company': True,
            'supplier_rank': 1,
        })

    def _parse(self, lines):
        """Ejecuta el parser REAL sobre un PDF construido con las líneas dadas."""
        return self.Parser.parse_dispatch_guide(_build_pdf(lines), default_name='')

    def _make_reception(self, name='RUT-TEST'):
        return self.Reception.create({
            'name': name,
            'supplier_id': self.partner.id,
            'ingestion_profile': 'metric',
        })

    def _assert_no_user_error(self, fn, label):
        """Falla si fn lanza UserError (contrato deseado: no bloquear)."""
        try:
            fn()
        except UserError as exc:
            self.fail('%s NO debe lanzar UserError, pero lanzó: %s' % (label, exc))

    # ── 1. RUT con puntos y guion ──────────────────────────────────────────
    def test_parse_dispatch_guide_rut_con_puntos_y_guion(self):
        data = self._parse(['RUT: 77.066.489-6', 'GUÍA DE DESPACHO ELECTRÓNICA'])
        self.assertEqual(data['supplier_rut'], '77.066.489-6')

    # ── 2. RUT sin puntos ──────────────────────────────────────────────────
    def test_parse_dispatch_guide_rut_sin_puntos(self):
        data = self._parse(['RUT: 77066489-6', 'GUÍA DE DESPACHO ELECTRÓNICA'])
        self.assertEqual(data['supplier_rut'], '77066489-6')

    # ── 3. Dígito verificador K mayúscula ──────────────────────────────────
    def test_parse_dispatch_guide_rut_dv_k_mayuscula(self):
        data = self._parse(['RUT: 77.066.489-K'])
        self.assertEqual(data['supplier_rut'], '77.066.489-K')

    # ── 4. Dígito verificador k minúscula ──────────────────────────────────
    def test_parse_dispatch_guide_rut_dv_k_minuscula(self):
        data = self._parse(['RUT: 77.066.489-k'])
        self.assertEqual(data['supplier_rut'], '77.066.489-k')

    # ── 5. Prefijo R.U.T. puntuado ─────────────────────────────────────────
    def test_parse_dispatch_guide_rut_con_prefijo_rut_puntuado(self):
        data = self._parse(['R.U.T.: 77.066.489-6'])
        self.assertEqual(data['supplier_rut'], '77.066.489-6')

    # ── 6. PDF sin RUT visible no debe crashear el flujo ───────────────────
    def test_parse_dispatch_guide_sin_rut_visible_no_crashea(self):
        # PDF con OC pero SIN RUT: caso legítimo que no debe tumbar el flujo.
        dg_data = self._parse([
            'GUÍA DE DESPACHO ELECTRÓNICA',
            'Orden de Compra MC-1106-11',
        ])
        # El extractor no debe crashear: devuelve supplier_rut=None.
        self.assertIsNone(dg_data['supplier_rut'])
        # El flujo completo (_find_or_create_po_intelligent) tampoco debe bloquear.
        reception = self._make_reception('RUT-NO-CRASH')
        self._assert_no_user_error(
            lambda: reception._find_or_create_po_intelligent(dg_data, None),
            'El flujo sin RUT visible',
        )

    # ── 7. _find_or_create_po_intelligent no debe bloquear sin RUT ─────────
    def test_find_or_create_po_intelligent_sin_rut_no_bloquea(self):
        reception = self._make_reception('RUT-NO-BLOCK')
        dg_data = {
            'supplier_rut': None,
            'supplier_name_detected': 'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA',
            'po_ref': 'MC-1106-11',
        }
        self._assert_no_user_error(
            lambda: reception._find_or_create_po_intelligent(dg_data, None),
            '_find_or_create_po_intelligent sin RUT',
        )

    # ── 8. Regresión guía 26270 (fixture real) ─────────────────────────────
    def test_fixture_regresion_26270(self):
        with open(_FIXTURE_26270, 'r', encoding='utf-8') as fh:
            texto = fh.read()
        # Documenta el formato real extraído del PDF (RUT sin puntos).
        self.assertIn('RUT: 77066489-6', texto)
        lines = [l for l in texto.split('\n') if l.strip()]
        data = self._parse(lines)
        self.assertEqual(data['supplier_rut'], '77066489-6')
