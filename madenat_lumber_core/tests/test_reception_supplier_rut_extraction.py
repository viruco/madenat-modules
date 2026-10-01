# -*- coding: utf-8 -*-
"""Tests de aislamiento — extracción de RUT del proveedor (flujo Producto).

Contrato vigente tras el cierre de T1 (Fase 2):
- reception_parser.parse_dispatch_guide() reconoce RUT con puntos y sin puntos
  (AD del 2026-09-08) y devuelve supplier_rut=None cuando el PDF no lo trae.
- lumber_reception._find_or_create_po_intelligent() NO bloquea por RUT ausente:
  la captura documental es flexible (§2.1). Sin RUT no se busca por VAT vacío,
  no se asocia proveedor arbitrario ni se crea proveedor: el proveedor queda
  PENDIENTE DE ASIGNACIÓN MANUAL y el pipeline no termina en state='error'.
- Con proveedor seleccionado por el usuario, se conserva y la búsqueda de OC se
  restringe a ese partner.
- La exigencia definitiva de proveedor identificable ocurre en el envío
  irreversible a stock (action_confirm_reception), antes de crear lotes,
  picking, movimientos o quants.

Estos tests no modifican datos históricos ni crean partners innecesarios.
"""
import io
import uuid

# T4 — token único por corrida: los nombres de recepción son UNIQUE(name) en
# `lumber.reception`, de modo que no deben depender de datos preexistentes.
_RUN = uuid.uuid4().hex[:8].upper()
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

    def _make_reception(self, name='RUT-TEST', with_supplier=True):
        return self.Reception.create({
            'name': '%s-%s' % (name, _RUN),
            'supplier_id': self.partner.id if with_supplier else False,
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

    # ── 9. T1 — sin RUT, sin proveedor: no bloquea, no inventa, no crea ────
    def test_sin_rut_no_crea_ni_asocia_proveedor(self):
        """Sin RUT y sin proveedor seleccionado: no se busca VAT vacío, no se
        asocia partner arbitrario, no se crea partner y el flujo no bloquea."""
        partner_count = self.env['res.partner'].search_count([])
        reception = self._make_reception('RUT-SIN-PARTNER', with_supplier=False)
        dg_data = {
            'supplier_rut': None,
            'supplier_name_detected': (
                'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA'),
            'po_ref': 'MC-1106-11',
        }
        self._assert_no_user_error(
            lambda: reception._find_or_create_po_intelligent(dg_data, None),
            'Captura sin RUT y sin proveedor seleccionado',
        )
        self.assertFalse(
            reception.supplier_id,
            'No debe asociarse un proveedor arbitrario sin RUT documental')
        self.assertEqual(
            self.env['res.partner'].search_count([]), partner_count,
            'No debe crearse ningún proveedor sin RUT documental')
        self.assertEqual(
            reception.manual_po_name,
            self.Parser.normalize_po_display('MC-1106-11'),
            'La referencia documental de OC debe quedar disponible para el usuario')
        self.assertEqual(reception.oc_match_status, 'not_found')
        self.assertIn(
            'PENDIENTE DE ASIGNACIÓN', reception.oc_match_note or '',
            'Debe quedar registro explícito del proveedor pendiente')

    # ── 10. T1 — sin RUT con proveedor manual: se conserva ─────────────────
    def test_sin_rut_con_supplier_manual_se_conserva(self):
        """Con proveedor elegido por el usuario y sin RUT: se conserva y no se
        crea ni reemplaza ningún partner."""
        partner_count = self.env['res.partner'].search_count([])
        reception = self._make_reception('RUT-MANUAL-SUPPLIER')
        dg_data = {
            'supplier_rut': None,
            'supplier_name_detected': (
                'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA'),
            'po_ref': 'MC-1106-11',
        }
        self._assert_no_user_error(
            lambda: reception._find_or_create_po_intelligent(dg_data, None),
            'Captura sin RUT con proveedor seleccionado manualmente',
        )
        self.assertEqual(
            reception.supplier_id, self.partner,
            'El proveedor seleccionado por el usuario nunca se reemplaza')
        self.assertEqual(
            self.env['res.partner'].search_count([]), partner_count,
            'No debe crearse ni duplicarse ningún proveedor')

    # ── 11. T1 — punto irreversible: proveedor identificable obligatorio ───
    def _make_verified_reception(self, name):
        """Recepción 'verified' con staging completo (sin flujo de stock)."""
        product = self.env['product.product'].create({
            'name': 'T1 Guard Product',
            'is_storable': True,
            'tracking': 'lot',
        })
        subproduct = self.env['madenat.subproducto'].create({
            'name': 'T1 Guard Subproducto',
            'code': 'T1GUARD',
        })
        reception = self.Reception.create({
            'name': '%s-%s' % (name, _RUN),
            'ingestion_profile': 'metric',
        })
        self.env['lumber.reception.line'].create({
            'reception_id': reception.id,
            'lot_name': 'T1-GUARD-LOT',
            'product_id': product.id,
            'subproduct_id': subproduct.id,
            'thickness': 37.0, 'width': 100.0, 'length': 2.0, 'pieces': 10,
            'thickness_nominal': 37.0, 'width_nominal': 100.0,
        })
        reception.write({'state': 'verified'})
        return reception

    def test_confirmacion_sin_proveedor_bloquea_antes_de_stock(self):
        """Sin proveedor identificable el envío a stock bloquea antes de crear
        stock.lot, picking, movimientos o quants, con registro de auditoría.

        Nota: la excepción se captura manualmente (try/except) en lugar de usar
        `self.assertRaises` porque el framework de tests envuelve `assertRaises`
        en un savepoint que revierte los cambios de BD efectuados antes de la
        excepción; eso ocultaría el registro de auditoría (omission) que el
        método escribe inmediatamente antes de bloquear.
        """
        reception = self._make_verified_reception('RUT-GUARD')
        self.assertFalse(reception.supplier_id)

        try:
            reception.action_confirm_reception()
            self.fail('El envío a stock debe bloquearse sin proveedor identificable')
        except UserError as exc:
            self.assertIn('PROVEEDOR NO IDENTIFICADO', str(exc))

        self.assertEqual(
            self.env['stock.lot'].search_count(
                [('reception_id', '=', reception.id)]), 0,
            'No debe crearse ningún lote antes del bloqueo')
        self.assertFalse(reception.picking_id)
        self.assertEqual(
            self.env['madenat.audit.log'].search_count([
                ('reception_id', '=', reception.id),
                ('action_type', '=', 'omission'),
            ]), 1,
            'Debe quedar registro de auditoría (omission) del bloqueo')
