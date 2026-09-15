# -*- coding: utf-8 -*-
"""Tests del flujo manual de creación de OC provisional (FIX 2026-08-21).

Cubre: partner resuelto/ausente/inactivo, líneas 1:1, draft siempre, UoM m³
con conversión MBF explícita, price_unit=0 + nota, doble llamada idempotente,
y bloqueo por multi_match / needs_review.
Usa TransactionCase: nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import uuid


@tagged('post_install', '-at_install', 'madenat', 'purchasing')
class TestPOCreationFromGuide(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guia_model = cls.env['madenat.guia.processing']
        cls.product = cls.env['product.product'].create({
            'name': 'MADERA GENERICA TEST',
            'default_code': 'MADERA_GENERICA_TEST',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.env.ref('uom.product_uom_cubic_meter').id,
            'uom_po_id': cls.env.ref('uom.product_uom_cubic_meter').id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Test PO',
            'is_company': True,
            'supplier_rank': 1,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        ) or cls.env['stock.location'].search([], limit=1)

    def _make_guia(self, partner=False, status='not_found', oc_ref='MC-2506-01'):
        guia = self.guia_model.create({
            'name': 'GUIA-TEST-PO-%s' % uuid.uuid4().hex[:8],
            'partner_id': partner.id if partner else False,
            'assignment_location_id': self.location.id,
            'oc_reference_raw': oc_ref,
            'oc_match_status': status,
        })
        if partner:
            line = self.env['madenat.guia.processing.line'].create({
                'processing_id': guia.id,
                'product_id': self.product.id,
                'pieces': 10,
                'vol_purchase_m3': 5.0,
                'vol_shipment_m3': 5.0,
                'espesor_nominal_mm': 50,
                'ancho_nominal_mm': 100,
                'largo_nominal_m': 2.0,
                'lot_name': 'LOTE-TEST-1',
            })
            guia.processing_line_ids = [(6, 0, [line.id])]
        return guia

    def test_create_po_with_partner_resolved_creates_draft(self):
        guia = self._make_guia(self.partner)
        res = guia.action_create_purchase_order_from_document()
        po = self.env['purchase.order'].browse(res['res_id'])
        self.assertTrue(po.exists())
        self.assertEqual(po.state, 'draft')
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(guia.order_id.id, po.id)

    def test_create_po_without_partner_blocks(self):
        guia = self._make_guia(False)
        before = self.env['purchase.order'].search_count([])
        with self.assertRaises(UserError):
            guia.action_create_purchase_order_from_document()
        self.assertEqual(self.env['purchase.order'].search_count([]), before)

    def test_create_po_with_inactive_partner_blocks(self):
        partner = self.partner.copy()
        partner.active = False
        guia = self._make_guia(partner)
        before = self.env['purchase.order'].search_count([])
        with self.assertRaises(UserError):
            guia.action_create_purchase_order_from_document()
        self.assertEqual(self.env['purchase.order'].search_count([]), before)

    def test_create_po_multiple_lines_maps_1to1(self):
        guia = self._make_guia(self.partner)
        line2 = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'product_id': self.product.id,
            'pieces': 20,
            'vol_purchase_m3': 3.0,
            'vol_shipment_m3': 3.0,
            'espesor_nominal_mm': 40,
            'ancho_nominal_mm': 80,
            'largo_nominal_m': 1.5,
            'lot_name': 'LOTE-TEST-2',
        })
        guia.processing_line_ids = [(4, line2.id)]
        res = guia.action_create_purchase_order_from_document()
        po = self.env['purchase.order'].browse(res['res_id'])
        self.assertEqual(len(po.order_line), 2)  # mapeo 1:1 (2 líneas origen → 2 líneas PO)
        self.assertTrue(all(q > 0 for q in po.order_line.mapped('product_qty')),
                        "Todas las líneas deben tener cantidad volumétrica > 0 "
                        "(el gatekeeper reconvierte a la UoM de compra del producto).")

    def test_po_always_draft_even_if_policy_requests_other_state(self):
        result = self.env['purchase.order'].validate_or_create_po(
            {
                'partner_id': self.partner.id,
                'partner_ref': 'MC-2506-01',
                'ingestion_source_ref': 'madenat.guia.processing,999999',
                'lines': [{'product_id': self.product.id,
                           'product_qty': 5.0,
                           'product_uom': self.env.ref('uom.product_uom_cubic_meter').id,
                           'price_unit': 0.0}],
            },
            {'auto_create': True, 'provisional': False},  # pide sent, debe quedar draft
        )
        self.assertTrue(result['success'])
        po = self.env['purchase.order'].browse(result['po_id'])
        self.assertEqual(po.state, 'draft')

    def test_lines_use_m3_uom_and_convert_mbf_explicitly(self):
        m3 = self.env.ref('uom.product_uom_cubic_meter')
        mbf_to_m3 = 2.36  # Regla de Oro MADENAT (utils_uom)
        result = self.env['purchase.order'].validate_or_create_po(
            {
                'partner_id': self.partner.id,
                'partner_ref': 'MC-2506-01',
                'ingestion_source_ref': 'madenat.guia.processing,888888',
                'lines': [{'product_id': self.product.id,
                           'product_qty': 10 * mbf_to_m3,  # 10 MBF → m³
                           'product_uom': m3.id,
                           'price_unit': 0.0}],
            },
            {'auto_create': True, 'provisional': True},
        )
        self.assertTrue(result['success'])
        po = self.env['purchase.order'].browse(result['po_id'])
        line = po.order_line[0]
        self.assertEqual(line.product_uom.id, m3.id)
        self.assertNotEqual(line.product_uom.id, self.env.ref('uom.product_uom_unit').id)
        self.assertAlmostEqual(line.product_qty, 10 * mbf_to_m3, places=2)

    def test_price_unit_is_zero_and_provisional_note_is_recorded(self):
        guia = self._make_guia(self.partner)
        res = guia.action_create_purchase_order_from_document()
        po = self.env['purchase.order'].browse(res['res_id'])
        self.assertEqual(po.order_line[0].price_unit, 0.0)
        self.assertTrue(any('provisional' in (m.body or '').lower()
                            for m in po.message_ids))

    def test_double_call_no_duplicate_po(self):
        guia = self._make_guia(self.partner)
        res1 = guia.action_create_purchase_order_from_document()
        res2 = guia.action_create_purchase_order_from_document()
        self.assertEqual(res1['res_id'], res2['res_id'])
        dup = self.env['purchase.order'].search_count([
            ('ingestion_source_ref', '=', 'madenat.guia.processing,%s' % guia.id)
        ])
        self.assertEqual(dup, 1)

    def test_multi_match_and_needs_review_block_creation(self):
        for status in ('multi_match', 'needs_review'):
            guia = self._make_guia(self.partner, status=status)
            before = self.env['purchase.order'].search_count([])
            with self.assertRaises(UserError):
                guia.action_create_purchase_order_from_document()
            self.assertEqual(self.env['purchase.order'].search_count([]), before,
                             "No debe crear PO en estado %s" % status)

    def test_existing_po_by_ingestion_source_ref_is_reused(self):
        # PO previa con el mismo origen → el gatekeeper no crea otra
        guia = self._make_guia(self.partner)
        source = 'madenat.guia.processing,%s' % guia.id
        payload = {
            'partner_id': self.partner.id,
            'partner_ref': 'MC-2506-01',
            'ingestion_source_ref': source,
            'lines': [{'product_id': self.product.id,
                       'product_qty': 5.0,
                       'product_uom': self.env.ref('uom.product_uom_cubic_meter').id,
                       'price_unit': 0.0}],
        }
        # 1ra llamada crea la PO con el origen
        first = self.env['purchase.order'].validate_or_create_po(
            payload, {'auto_create': True, 'provisional': True})
        self.assertTrue(first['success'])
        existing = self.env['purchase.order'].browse(first['po_id'])
        # 2da llamada con el mismo origen: debe reutilizar (idempotente)
        result = self.env['purchase.order'].validate_or_create_po(
            payload, {'auto_create': True, 'provisional': True})
        self.assertTrue(result['success'])
        self.assertEqual(result['po_id'], existing.id, "Debe reutilizar la PO existente")
        count = self.env['purchase.order'].search_count([
            ('ingestion_source_ref', '=', source),
        ])
        self.assertEqual(count, 1, "No debe crear una segunda PO")

    def test_multiple_pos_same_ingestion_source_ref_blocks(self):
        guia = self._make_guia(self.partner)
        source = 'madenat.guia.processing,%s' % guia.id
        self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'ingestion_source_ref': source,
            'state': 'draft',
        })
        self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'ingestion_source_ref': source,
            'state': 'draft',
        })
        result = self.env['purchase.order'].validate_or_create_po(
            {
                'partner_id': self.partner.id,
                'ingestion_source_ref': source,
                'lines': [{'product_id': self.product.id,
                           'product_qty': 5.0,
                           'product_uom': self.env.ref('uom.product_uom_cubic_meter').id,
                           'price_unit': 0.0}],
            },
            {'auto_create': True, 'provisional': True},
        )
        self.assertFalse(result['success'], "Debe bloquear ante múltiples OCs del mismo origen")
        self.assertIn('múltiples OCs', result.get('error', ''))
        count = self.env['purchase.order'].search_count([
            ('ingestion_source_ref', '=', source),
        ])
        self.assertEqual(count, 2, "No debe crear una tercera PO")

    def test_origin_with_order_id_existing_reuses_linked_po(self):
        guia = self._make_guia(self.partner)
        existing = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'partner_ref': 'MC-2506-01',
            'ingestion_source_ref': 'madenat.guia.processing,%s' % guia.id,
            'state': 'draft',
        })
        guia.order_id = existing.id
        res = guia.action_create_purchase_order_from_document()
        self.assertEqual(res['res_id'], existing.id, "Debe abrir la OC ya vinculada")
        count = self.env['purchase.order'].search_count([
            ('ingestion_source_ref', '=', 'madenat.guia.processing,%s' % guia.id),
        ])
        self.assertEqual(count, 1, "No debe crear una OC adicional")

