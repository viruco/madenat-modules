# -*- coding: utf-8 -*-
"""Tests para la resolución blindada de proveedor documental (FIX 2026-08-21).

Cubre los casos A-E de _resolve_or_create_supplier y la extracción de la
razón social con _find_emitter_company_name / _normalize_supplier_name.
Usa fixtures en transacción (TransactionCase): nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
import uuid

# T4 — Aislamiento de fixtures: todo identificador que pueda colisionar con
# datos reales de `madenat_test` (RUT/nombre) se genera por corrida. Los tests
# no dependen de partners ni de datos preexistentes.
_RUN_TOKEN = uuid.uuid4().hex[:8].upper()


def _token_label(salt):
    """Razón social única por corrida."""
    return 'FERRAMENTA %s%s SPA' % (salt.upper(), _RUN_TOKEN)


def _unique_vat(salt):
    """RUT sintético válido y único por corrida (cuerpo derivado del token).

    Formato chileno sin puntos con dígito verificador módulo 11, de modo que
    la unicidad frente a datos reales la aporta el token y no un literal fijo.
    """
    seed = int('%s%s' % (_RUN_TOKEN, salt.upper()), 36)
    body = (seed % 90000000) + 10000000  # 8 dígitos: 10.000.000 - 99.999.999
    total = 0
    for index, digit in enumerate(reversed(str(body))):
        total += int(digit) * (2 + (index % 6))
    dv_value = 11 - (total % 11)
    dv = 'K' if dv_value == 10 else ('0' if dv_value == 11 else str(dv_value))
    return '%s-%s' % (body, dv)


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestSupplierResolution(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)

    def _make_guia(self, partner=None, name=None):
        vals = {
            'name': name or 'SUP-RES-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        }
        if partner:
            vals['partner_id'] = partner.id
        return self.GuiaModel.create(vals)

    # ─── Extracción de razón social (helper del parser) ────────────────
    def test_emitter_name_en_lineas_posteriores_al_rut(self):
        """La razón social está en lines[2]; el helper debe encontrarla."""
        lines = [
            'RUT: 77066489-6',
            'GUÍA DE DESPACHO ELECTRÓNICA',
            'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA',
            'Venta al por mayor...',
        ]
        guia = self.GuiaModel.create({
            'name': 'SUP-PDF-001-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        nombre = guia._find_emitter_company_name(lines)
        self.assertEqual(
            nombre, 'COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA',
            "Debe extraerse la razón social real desde las líneas posteriores al RUT",
        )

    def test_emitter_name_sin_candidata_devuelve_vacio(self):
        """Sin candidata válida en 5 líneas → '' (luego se convierte a None)."""
        lines = [
            'RUT: 77066489-6',
            'GUÍA DE DESPACHO ELECTRÓNICA',
            'Fecha: 02/10/2025',
            'Total: 1000',
        ]
        guia = self.GuiaModel.create({
            'name': 'SUP-PDF-002-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia._find_emitter_company_name(lines), '')

    def test_normalize_supplier_name(self):
        guia = self.GuiaModel.create({
            'name': 'SUP-PDF-003-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia._normalize_supplier_name('  Ferramenta SPA '), 'FERRAMENTASPA')
        self.assertEqual(guia._normalize_supplier_name(None), '')

    # ─── CASO A: proveedor existe con VAT ───────────────────────────────
    def test_resolver_por_vat(self):
        vat = _unique_vat('VA')
        name = _token_label('VA')
        partner = self.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier(vat, name)
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_vat')

    # ─── CASO B: por nombre sin VAT → completar VAT ────────────────────
    def test_resolver_por_nombre_completa_vat(self):
        name = _token_label('NB')
        vat = _unique_vat('NB')
        partner = self.env['res.partner'].create({
            'name': name,
            'vat': False,
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier(vat, name)
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_name')
        self.assertEqual(partner.vat, vat,
            "El VAT vacío debe completarse con el RUT del documento")

    # ─── CASO B: VAT contradictorio → NO sobrescribir ──────────────────
    def test_resolver_por_nombre_no_sobrescribe_vat_distinto(self):
        name = _token_label('NC')
        vat_previo = _unique_vat('NC1')
        vat_documento = _unique_vat('NC2')
        partner = self.env['res.partner'].create({
            'name': name,
            'vat': vat_previo,
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier(vat_documento, name)
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(partner.vat, vat_previo,
            "Un VAT existente distinto jamás se sobrescribe")
        self.assertIn('NO se sobrescribió', guia.supplier_resolution_note)

    # ─── CASO E: múltiples coincidencias → multi_match ─────────────────
    def test_resolver_multiples_coincidencias(self):
        name = _token_label('E')
        self.env['res.partner'].create({'name': name})
        self.env['res.partner'].create({'name': name.upper()})
        guia = self.GuiaModel.create({
            'name': 'SUP-E-001-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(None, name)
        self.assertFalse(resolved, "No debe asignarse partner arbitrario")
        self.assertEqual(guia.supplier_resolution_status, 'multi_match')

    # ─── CASO C: auto-create con bandera ───────────────────────────────
    def test_resolver_crea_auto_con_bandera(self):
        vat = _unique_vat('CA')
        name = 'NUEVO PROVEEDOR %s SPA' % _RUN_TOKEN
        guia = self.GuiaModel.create({
            'name': 'SUP-C-001-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(vat, name)
        self.assertTrue(resolved)
        self.assertTrue(resolved.is_auto_created,
            "El partner auto-creado debe quedar marcado para auditoría")
        self.assertEqual(resolved.supplier_rank, 1)
        self.assertEqual(guia.supplier_resolution_status, 'auto_created')

    # ─── T4: mismo RUT tokenizado → un solo partner (sin duplicados) ────
    def test_resolver_reutiliza_partner_por_rut_tokenizado(self):
        """El mismo RUT generado resuelve siempre al mismo partner."""
        vat = _unique_vat('DU')
        name = _token_label('DU')
        guia_a = self._make_guia(name='SUP-REU-A-%s' % _RUN_TOKEN)
        guia_b = self._make_guia(name='SUP-REU-B-%s' % _RUN_TOKEN)
        first = guia_a._resolve_or_create_supplier(vat, name)
        second = guia_b._resolve_or_create_supplier(vat, name)
        self.assertTrue(first)
        self.assertEqual(first.id, second.id)
        self.assertEqual(
            self.env['res.partner'].search_count([('vat', '=', vat)]), 1,
            "No debe existir más de un partner para el mismo RUT")

    # ─── CASO D: sin RUT ni nombre → needs_manual con nota ─────────────
    def test_resolver_sin_datos_nota_visible(self):
        guia = self.GuiaModel.create({
            'name': 'SUP-D-001-%s' % _RUN_TOKEN,
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(None, None)
        self.assertFalse(resolved)
        self.assertEqual(guia.supplier_resolution_status, 'needs_manual')
        self.assertIn('Requiere asignación manual', guia.supplier_resolution_note)