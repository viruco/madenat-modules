# -*- coding: utf-8 -*-
"""Cobertura del botón 'Aplicar cambios' de la consola Intake.

Valida que `action_apply_product_subproduct()` devuelve una acción modal que
abre el wizard masivo existente del core con defaults comunes, sin ejecutar
silenciosamente `wizard.action_apply()`.
"""
import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeApplyChanges(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reception = cls.env['lumber.reception']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Product = cls.env['product.product']
        cls.Subproducto = cls.env['madenat.subproducto']
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Apply Changes Test', 'is_company': True,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)

        cls.product = cls.Product.create({
            'name': 'Producto Apply Test',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })
        cls.sub = cls.Subproducto.create({
            'name': 'SUB APPLY TEST', 'code': 'SUB-APPLY-TEST',
        })

    @classmethod
    def _b64(cls, raw=b'fake'):
        return base64.b64encode(raw).decode()

    def _console_for(self, rec, source_model):
        return self.Console.search([
            ('source_model', '=', source_model),
            ('source_res_id', '=', rec.id),
        ], limit=1)

    # ── Bruta ─────────────────────────────────────────────────────────────
    def test_bruta_returns_modal_with_common_defaults(self):
        rec = self.Reception.create({
            'name': 'G-APPLY-BRUTA',
            'supplier_id': self.partner.id,
            'state': 'verified',
            'ingestion_profile': 'metric',
            'excel_file': self._b64(),
            'excel_filename': 'packing.xlsx',
        })
        for i in (1, 2):
            self.env['lumber.reception.line'].create({
                'reception_id': rec.id,
                'lot_name': 'LOTE-APPLY-%s' % i,
                'product_id': self.product.id,
                'subproduct_id': self.sub.id,
                'lengthuom': 'm',
            })
        console = self._console_for(rec, 'lumber.reception')
        self.assertTrue(console)

        action = console.action_apply_product_subproduct()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'lumber.reception.mass.update')
        self.assertEqual(action['target'], 'new')
        ctx = action['context']
        self.assertEqual(ctx['default_reception_id'], rec.id)
        self.assertEqual(ctx['default_ingestion_profile'], 'metric')
        self.assertEqual(ctx['default_product_id'], self.product.id)
        self.assertEqual(ctx['default_subproduct_id'], self.sub.id)

    def test_bruta_no_default_when_subproduct_mixed(self):
        rec = self.Reception.create({
            'name': 'G-APPLY-MIXED',
            'supplier_id': self.partner.id,
            'state': 'verified',
            'ingestion_profile': 'metric',
        })
        sub2 = self.Subproducto.create({'name': 'SUB MIXED 2', 'code': 'SUB-MIXED-2'})
        self.env['lumber.reception.line'].create({
            'reception_id': rec.id, 'lot_name': 'L1',
            'product_id': self.product.id, 'subproduct_id': self.sub.id,
            'lengthuom': 'm',
        })
        self.env['lumber.reception.line'].create({
            'reception_id': rec.id, 'lot_name': 'L2',
            'product_id': self.product.id, 'subproduct_id': sub2.id,
            'lengthuom': 'm',
        })
        console = self._console_for(rec, 'lumber.reception')

        action = console.action_apply_product_subproduct()
        ctx = action['context']

        # Producto común → default; subproducto mixto → sin default.
        self.assertEqual(ctx['default_product_id'], self.product.id)
        self.assertNotIn('default_subproduct_id', ctx)

    # ── Procesado ─────────────────────────────────────────────────────────
    def test_procesado_returns_modal_with_common_defaults(self):
        guia = self.Guia.create({
            'name': 'G-APPLY-PROC',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'service',
            'state': 'verified',
            'ingestion_profile': 'f1550',
        })
        self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'LOTE-PROC-1',
            'product_id': self.product.id,
            'subproducto_id': self.sub.id,
        })
        console = self._console_for(guia, 'madenat.guia.processing')
        self.assertTrue(console)

        action = console.action_apply_product_subproduct()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'madenat.guia.mass.update')
        self.assertEqual(action['target'], 'new')
        ctx = action['context']
        self.assertEqual(ctx['active_id'], guia.id)
        self.assertEqual(ctx['active_ids'], [guia.id])
        self.assertEqual(ctx['active_model'], 'madenat.guia.processing')
        self.assertEqual(ctx['default_product_id'], self.product.id)
        self.assertEqual(ctx['default_subproducto_id'], self.sub.id)

    def test_procesado_no_default_when_product_mixed(self):
        product2 = self.Product.create({
            'name': 'Producto Apply 2', 'type': 'consu',
            'uom_id': self.uom_m3.id, 'uom_po_id': self.uom_m3.id,
            'sale_line_warn': 'no-message', 'purchase_line_warn': 'no-message',
        })
        guia = self.Guia.create({
            'name': 'G-APPLY-PROC-MIXED',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'service',
            'state': 'verified',
        })
        self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id, 'lot_name': 'L1',
            'product_id': self.product.id, 'subproducto_id': self.sub.id,
        })
        self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id, 'lot_name': 'L2',
            'product_id': product2.id, 'subproducto_id': self.sub.id,
        })
        console = self._console_for(guia, 'madenat.guia.processing')

        action = console.action_apply_product_subproduct()
        ctx = action['context']

        # Producto mixto → sin default; subproducto común → default.
        self.assertNotIn('default_product_id', ctx)
        self.assertEqual(ctx['default_subproducto_id'], self.sub.id)
