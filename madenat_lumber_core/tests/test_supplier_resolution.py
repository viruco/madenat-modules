# -*- coding: utf-8 -*-
"""Tests para la resolución blindada de proveedor documental (FIX 2026-08-21).

Cubre los casos A-E de _resolve_or_create_supplier y la extracción de la
razón social con _find_emitter_company_name / _normalize_supplier_name.
Usa fixtures en transacción (TransactionCase): nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


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

    def _make_guia(self, partner):
        return self.GuiaModel.create({
            'name': 'SUP-RES-001',
            'partner_id': partner.id,
            'assignment_location_id': self.location.id,
        })

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
            'name': 'SUP-PDF-001',
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
            'name': 'SUP-PDF-002',
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia._find_emitter_company_name(lines), '')

    def test_normalize_supplier_name(self):
        guia = self.GuiaModel.create({
            'name': 'SUP-PDF-003',
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia._normalize_supplier_name('  Ferramenta SPA '), 'FERRAMENTASPA')
        self.assertEqual(guia._normalize_supplier_name(None), '')

    # ─── CASO A: proveedor existe con VAT ───────────────────────────────
    def test_resolver_por_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Proveedor VAT Test',
            'vat': '11111111-1',
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier('11111111-1', 'Proveedor VAT Test')
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_vat')

    # ─── CASO B: por nombre sin VAT → completar VAT ────────────────────
    def test_resolver_por_nombre_completa_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Ferramenta Test Unica SPA',
            'vat': False,
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier(
            '77066489-6', 'Ferramenta Test Unica SPA'
        )
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(guia.supplier_resolution_status, 'resolved_name')
        self.assertEqual(partner.vat, '77066489-6',
            "El VAT vacío debe completarse con el RUT del documento")

    # ─── CASO B: VAT contradictorio → NO sobrescribir ──────────────────
    def test_resolver_por_nombre_no_sobrescribe_vat_distinto(self):
        partner = self.env['res.partner'].create({
            'name': 'Ferramenta Conflicto Test SPA',
            'vat': '99999999-9',
            'is_company': True,
        })
        guia = self._make_guia(partner)
        resolved = guia._resolve_or_create_supplier(
            '77066489-6', 'Ferramenta Conflicto Test SPA'
        )
        self.assertEqual(resolved.id, partner.id)
        self.assertEqual(partner.vat, '99999999-9',
            "Un VAT existente distinto jamás se sobrescribe")
        self.assertIn('NO se sobrescribió', guia.supplier_resolution_note)

    # ─── CASO E: múltiples coincidencias → multi_match ─────────────────
    def test_resolver_multiples_coincidencias(self):
        self.env['res.partner'].create({'name': 'Proveedor Test Alfa SPA'})
        self.env['res.partner'].create({'name': 'PROVEEDOR TEST ALFA SPA'})
        guia = self.GuiaModel.create({
            'name': 'SUP-E-001',
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(None, 'Proveedor Test Alfa SPA')
        self.assertFalse(resolved, "No debe asignarse partner arbitrario")
        self.assertEqual(guia.supplier_resolution_status, 'multi_match')

    # ─── CASO C: auto-create con bandera ───────────────────────────────
    def test_resolver_crea_auto_con_bandera(self):
        guia = self.GuiaModel.create({
            'name': 'SUP-C-001',
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(
            '77066489-6', 'NUEVO PROVEEDOR TEST SPA'
        )
        self.assertTrue(resolved)
        self.assertTrue(resolved.is_auto_created,
            "El partner auto-creado debe quedar marcado para auditoría")
        self.assertEqual(resolved.supplier_rank, 1)
        self.assertEqual(guia.supplier_resolution_status, 'auto_created')

    # ─── CASO D: sin RUT ni nombre → needs_manual con nota ─────────────
    def test_resolver_sin_datos_nota_visible(self):
        guia = self.GuiaModel.create({
            'name': 'SUP-D-001',
            'assignment_location_id': self.location.id,
        })
        resolved = guia._resolve_or_create_supplier(None, None)
        self.assertFalse(resolved)
        self.assertEqual(guia.supplier_resolution_status, 'needs_manual')
        self.assertIn('Requiere asignación manual', guia.supplier_resolution_note)