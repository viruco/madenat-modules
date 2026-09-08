# -*- coding: utf-8 -*-
"""Tests de aislamiento — clasificación de tipo_ingreso por CONTENIDO.

Bug documentado: `_onchange_suggest_tipo_ingreso` clasifica por NOMBRE DE
ARCHIVO (keywords sobre excel_filename/pdf_filename) y NO por el CONTENIDO
del documento. La guía real 26270 (cuya glosa es "SERVICIO DE CEPILLADO")
cae a Producto porque el nombre de archivo no trae keyword.

Estos tests codifican el CONTRATO DESEADO (clasificación por contenido) y
deben FALLAR contra el código actual, confirmando el bug antes del fix.

NO modifican producción.
"""
import base64
import io

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


def _safe_winansi(text):
    """Sanitiza el texto para la fuente Helvetica (cp1252) de reportlab."""
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


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake',
        'madenat_tipo_ingreso_content')
class TestIntakeTipoIngresoContent(TransactionCase):
    """Clasificación de tipo_ingreso por contenido del documento."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.lumber.intake.wizard']

    def _make_wizard(self, pdf_lines, excel_filename='26270.xlsx',
                     pdf_filename='26270.pdf'):
        return self.Wizard.create({
            'excel_filename': excel_filename,
            'pdf_filename': pdf_filename,
            'excel_file': base64.b64encode(b'fake bytes'),
            'pdf_file': base64.b64encode(_build_pdf(pdf_lines)),
        })

    # ── 1. Clasifica procesado por CONTENIDO, no por nombre de archivo ─────
    def test_clasifica_procesado_por_contenido_no_por_nombre_archivo(self):
        # Nombres sin keyword, pero el contenido real trae "SERVICIO DE CEPILLADO".
        wizard = self._make_wizard(['SFABR00017 SERVICIO DE CEPILLADO MADENAT'])
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(
            wizard.tipo_ingreso, 'procesado',
            'Debe clasificar como procesado por el contenido, no por el nombre',
        )

    # ── 2. NO clasifica por proveedor histórico ────────────────────────────
    def test_no_clasifica_por_proveedor_historico(self):
        # Documento de FERRAMENTA (RUT 77066489-6, mismo proveedor de las 3
        # guías Procesado) cuyo contenido es una VENTA DE MADERA, sin keyword
        # de servicio. No debe inferir 'procesado' por el RUT del proveedor.
        wizard = self._make_wizard(
            ['VENTA DE MADERA ASERRADA', 'RUT: 77066489-6'],
            excel_filename='ferramenta-venta.xlsx',
            pdf_filename='ferramenta-venta.pdf',
        )
        wizard._onchange_suggest_tipo_ingreso()
        self.assertNotEqual(
            wizard.tipo_ingreso, 'procesado',
            'No debe forzar procesado por historial/RUT del proveedor (77066489-6)',
        )

    # ── 3. Sin keyword NO asume producto silenciosamente ───────────────────
    def test_sin_keyword_no_asume_producto_silenciosamente(self):
        # Redacción no cubierta por las 4 keywords actuales.
        wizard = self._make_wizard(
            ['SECADO DE MADERA A TERCEROS'],
            excel_filename='documento.xlsx',
            pdf_filename='documento.pdf',
        )
        result = wizard._onchange_suggest_tipo_ingreso()
        self.assertTrue(
            result and isinstance(result, dict) and 'warning' in result,
            'Debe emitir advertencia visible y no asumir tipo por defecto',
        )

    # ── 4. Regresión guías Procesado reales existentes ─────────────────────
    def test_clasifica_procesado_guias_reales_existentes(self):
        # service_product_name real de las guías 19846 / 19827 / 19826.
        for content in ['SERVICIO DE CEPILLADO MADENAT']:
            wizard = self._make_wizard([content])
            wizard._onchange_suggest_tipo_ingreso()
            self.assertEqual(
                wizard.tipo_ingreso, 'procesado',
                'Las guías Procesado reales deben seguir clasificando como procesado',
            )

    # ── 5. Regresión guía 26270 (contenido real) ───────────────────────────
    def test_fixture_regresion_26270(self):
        wizard = self._make_wizard([
            'RUT: 77066489-6',
            'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA',
            'SFABR00017 SERVICIO DE CEPILLADO MADENAT 57,8400 Metros Cubicos',
        ])
        wizard._onchange_suggest_tipo_ingreso()
        self.assertEqual(
            wizard.tipo_ingreso, 'procesado',
            'La guía 26270 (servicio de cepillado) debe clasificar como procesado',
        )
