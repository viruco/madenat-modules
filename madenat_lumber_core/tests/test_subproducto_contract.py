# -*- coding: utf-8 -*-
"""
TESTS: Contrato Producto/Subproducto (Fase 2)

Cobertura:
  1. Helper find_or_create_lumber_subproducto:
     - autocrea subproducto inexistente;
     - reutiliza sin duplicar;
     - crea/reutiliza varios textos (RIP S2S, RIP Rough, Blank Clear);
     - texto vacío → recordset vacío.
  2. Bruta: _fill_staging_table resuelve producto fijo + subproducto.
  3. Procesado: action_verify_data resuelve producto fijo + subproducto.
"""
import base64
import logging

from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'madenat_subproducto_contract')
class TestSubproductoContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Mixin = cls.env['madenat.lumber.ingest.mixin']
        cls.Subproducto = cls.env['madenat.subproducto']
        cls.Rule = cls.env['madenat.lumber.product.default']
        cls.Product = cls.env['product.product']
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')

        cls.product_fijo = cls.Product.create({
            'name': 'Producto Maestro Fase2',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Fase2',
            'is_company': True,
            'supplier_rank': 1,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        # Aislar las reglas sembradas por el XML del módulo.
        cls.Rule.search([]).write({'active': False})

    # ── Helper ────────────────────────────────────────────────────────────
    def test_01_autocrea_subproducto_inexistente(self):
        """Texto inexistente → crea subproducto sin UserError."""
        res = self.Mixin.find_or_create_lumber_subproducto('MADERA SECA CEPILLADA')
        self.assertTrue(res)
        self.assertEqual(res.name, 'MADERA SECA CEPILLADA')
        self.assertEqual(res.code, 'MADERA-SECA-CEPILLADA')

    def test_02_reutiliza_sin_duplicar(self):
        """El mismo texto dos veces reutiliza el subproducto, sin duplicar."""
        res1 = self.Mixin.find_or_create_lumber_subproducto('RIP Rough')
        res2 = self.Mixin.find_or_create_lumber_subproducto('  rip rough ')
        self.assertEqual(res1, res2)
        count = self.Subproducto.search_count([('name', '=ilike', 'RIP Rough')])
        self.assertEqual(count, 1)

    def test_03_autocrea_varios_textos(self):
        """RIP S2S, RIP Rough y Blank Clear se crean/reutilizan correctamente."""
        s2s = self.Mixin.find_or_create_lumber_subproducto('RIP S2S')
        rough = self.Mixin.find_or_create_lumber_subproducto('RIP Rough')
        blank = self.Mixin.find_or_create_lumber_subproducto('Blank Clear')
        self.assertTrue(s2s and rough and blank)
        # Reutiliza el mismo registro al repetir el texto.
        self.assertEqual(self.Mixin.find_or_create_lumber_subproducto('RIP S2S'), s2s)
        self.assertEqual(self.Mixin.find_or_create_lumber_subproducto('RIP Rough'), rough)
        self.assertEqual(self.Mixin.find_or_create_lumber_subproducto('Blank Clear'), blank)

    def test_04_subproducto_texto_vacio(self):
        res = self.Mixin.find_or_create_lumber_subproducto('')
        self.assertFalse(res)
        self.assertFalse(self.Mixin.find_or_create_lumber_subproducto('   '))

    # ── Bruta ─────────────────────────────────────────────────────────────
    def test_05_bruta_fill_staging_producto_fijo_y_subproducto(self):
        self.Rule.create({'tipo_ingreso': 'bruta', 'product_id': self.product_fijo.id})
        sub = self.Subproducto.create({'name': 'ROUGH TEST', 'code': 'ROUGH-TEST'})

        reception = self.env['lumber.reception'].create({
            'name': 'TEST-BRUTA-F2',
            'supplier_id': self.partner.id,
            'ingestion_profile': 'metric',
        })
        pl_data = {'lines': [{
            'product_code': 'LOT1',
            'product_name': 'ROUGH TEST',
            'package_no': '1',
            'pieces': 10,
            'volume_m3': 1.5,
            'thickness_mm': 25.0,
            'width_mm': 100.0,
            'length_m': 3.0,
        }]}
        reception._fill_staging_table(pl_data)

        line = reception.reception_line_ids[0]
        self.assertEqual(line.product_id, self.product_fijo)
        self.assertEqual(line.subproduct_id, sub)
        self.assertEqual(line.excel_product_name, 'ROUGH TEST')

    # ── Procesado ─────────────────────────────────────────────────────────
    def test_06_procesado_verify_data_producto_fijo_y_subproducto(self):
        self.Rule.create({'tipo_ingreso': 'procesado', 'product_id': self.product_fijo.id})
        sub = self.Subproducto.create({'name': 'RIP S2S TEST', 'code': 'RIP-S2S-TEST'})

        guia = self.env['madenat.guia.processing'].create({
            'name': 'TEST-PROC-F2',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'ingestion_profile': 'f1550',
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx',
        })
        packing_data = {'lineas': [{
            'Codigo Interno': 'X100',
            'N° LOTE': 'L1',
            'Cantidad': 1,
            'Volumen': 1.0,
            'Espesor': 45,
            'Ancho': 125,
            'Largo': 2.0,
            'product_name': 'RIP S2S TEST',
            'espesor_nominal_mm': 0.0,
        }]}
        guia.with_context(force_packing_data=packing_data).action_verify_data()

        line = guia.processing_line_ids[0]
        self.assertEqual(line.product_id, self.product_fijo)
        self.assertEqual(line.subproducto_id, sub)
        self.assertEqual(line.product_name_original, 'RIP S2S TEST')
        # espesor_nominal_mm se alimenta del físico (Fase 2).
        self.assertEqual(line.espesor_nominal_mm, 45.0)
