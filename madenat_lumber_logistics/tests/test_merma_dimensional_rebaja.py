# -*- coding: utf-8 -*-
"""
Pruebas unitarias de Merma Dimensional y Rebaja (Bloque 7.3 / TDD).
Valida:
1. Prueba dorada con Packing 40030: compra 54,518, exportación 44,713, merma 9,805 m³.
2. Merma cero en Blanks y productos rugosos (compra == exportación).
3. Acumulación de merma total por contenedor y por embarque.
4. Registro de merma en la rebaja física (extinción completa del quant).
5. Reversa R2: restauración física del quant y reseteo de merma rebajada.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.madenat_lumber_core.models.utils_uom import r3


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestMermaDimensionalRebaja(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user_oper = cls.env.ref('base.user_admin')
        cls.user_oper.groups_id |= cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        cls.user_oper.groups_id |= cls.env.ref('madenat_lumber_core.group_madenat_jefatura_operaciones')
        cls.user_oper.groups_id |= cls.env.ref('madenat_lumber_core.group_madenat_gerencia')

        cls.uom_m3 = cls.env.ref('madenat_lumber_core.uom_m3', raise_if_not_found=False) or cls.env['uom.uom'].search([('name', '=', 'm³')], limit=1)
        if not cls.uom_m3:
            cls.uom_m3 = cls.env.ref('uom.product_uom_unit')

        cls.subprod_s2s = cls.env['madenat.subproducto'].search([('name', 'ilike', 'RIP S2S')], limit=1)
        if not cls.subprod_s2s:
            cls.subprod_s2s = cls.env['madenat.subproducto'].create({'name': 'RIP S2S', 'code': 'RIPS2S'})

        cls.subprod_blank = cls.env['madenat.subproducto'].search([('name', 'ilike', 'BLANK CLEAR')], limit=1)
        if not cls.subprod_blank:
            cls.subprod_blank = cls.env['madenat.subproducto'].create({'name': 'BLANK CLEAR', 'code': 'BC'})

        cls.product = cls.env['product.product'].create({
            'name': 'Pino Radiata Cepillado',
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Proveedor Packing 40030', 'ref': 'P40030'})

        cls.vessel = cls.env['shipping.vessel'].create({'name': 'MSC TEST VESSEL'})
        cls.shipment = cls.env['lumber.export.shipment'].create({
            'name': 'EXP-40030-TEST',
            'booking_reference': 'BKG-40030',
            'vessel_id': cls.vessel.id,
        })
        cls.location_stock = cls.env.ref('stock.stock_location_stock')

    def test_01_golden_packing_40030_shrinkage(self):
        """Prueba dorada Packing 40030: compra 54,518 m³, exportación 44,713 m³, merma 9,805 m³."""
        lot = self.env['stock.lot'].create({
            'name': 'LOT-40030',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'supplier_id': self.partner.id,
            'subproducto_id': self.subprod_s2s.id,
            'volumen_m3': 54.518,
            'vol_shipment_m3': 44.713,
            'piezas': 1000,
        })

        # 1. Merma por lote
        self.assertEqual(lot.merma_dimensional_m3, 9.805, "54.518 - 44.713 debe ser exactamente 9.805 m³")

        # 2. Total por contenedor
        container = self.env['lumber.container'].create({
            'name': 'CONT-40030',
            'shipment_id': self.shipment.id,
            'container_type': '40HC',
            'seal_number': 'SEAL-40030',
            'lot_ids': [(6, 0, [lot.id])],
        })
        self.assertEqual(container.total_merma_dimensional_m3, 9.805, "Merma total de contenedor debe ser 9.805 m³")

        # 3. Total por embarque
        self.assertEqual(self.shipment.total_merma_dimensional_m3, 9.805, "Merma total de embarque debe ser 9.805 m³")

    def test_02_blanks_and_rough_have_zero_shrinkage(self):
        """Blanks y productos rugosos donde compra == exportación tienen merma dimensional cero."""
        lot_blank = self.env['stock.lot'].create({
            'name': 'LOT-BLANK-ZERO',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'subproducto_id': self.subprod_blank.id,
            'volumen_m3': 5.399,
            'vol_shipment_m3': 5.399,
            'piezas': 416,
        })
        self.assertEqual(lot_blank.merma_dimensional_m3, 0.0, "Blanks debe tener merma dimensional 0")

        lot_rough = self.env['stock.lot'].create({
            'name': 'LOT-ROUGH-ZERO',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'volumen_m3': 4.500,
            'vol_shipment_m3': 4.500,
            'piezas': 200,
        })
        self.assertEqual(lot_rough.merma_dimensional_m3, 0.0, "Rugoso igual compra/export debe tener merma 0")

    def test_03_rebaja_and_reverse_r2_records_and_resets_merma(self):
        """La rebaja registra la merma dimensional y la reversa R2 la resetea restaurando el quant."""
        lot = self.env['stock.lot'].create({
            'name': 'LOT-REBAJA-MERMA',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'supplier_id': self.partner.id,
            'subproducto_id': self.subprod_s2s.id,
            'volumen_m3': 10.000,
            'vol_shipment_m3': 8.000,
            'piezas': 100,
        })
        self.assertEqual(lot.merma_dimensional_m3, 2.000)

        # Crear quant en inventario interno para permitir rebaja física
        quant = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location_stock.id,
            'lot_id': lot.id,
            'quantity': 10.000,
        })

        container = self.env['lumber.container'].create({
            'name': 'CONT-REBAJA-MERMA',
            'shipment_id': self.shipment.id,
            'container_type': '40HC',
            'seal_number': 'SEAL-REB',
            'lot_ids': [(6, 0, [lot.id])],
            'state': 'sealed',
        })

        # 1. Ejecutar rebaja
        container.with_user(self.user_oper).action_rebajar()
        self.assertEqual(container.state, 'rebajado')

        line = container.line_ids[:1]
        self.assertEqual(line.rebaja_state, 'rebajado')
        self.assertEqual(line.rebaja_merma_m3, 2.000, "Debe registrar la merma dimensional de 2.000 m³")
        self.assertEqual(line.rebaja_qty_m3, 10.000, "Debe extinguir el quant nominal completo de 10.000 m³")

        # Quant en ubicación interna debe haber quedado en 0
        rem_quant = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.location_stock.id)
        ])
        self.assertAlmostEqual(sum(rem_quant.mapped('quantity')), 0.0, places=3)

        # 2. Reversa R2
        container.with_user(self.user_oper).action_reverse_rebaja()
        self.assertEqual(container.state, 'sealed')
        self.assertEqual(line.rebaja_state, 'reversed')
        self.assertEqual(line.rebaja_merma_m3, 0.0, "La merma rebajada debe resetearse a 0 en la reversa")

        # Quant en ubicación interna debe haber sido restaurado a 10.000 m³
        restored_quant = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.location_stock.id)
        ])
        self.assertAlmostEqual(sum(restored_quant.mapped('quantity')), 10.000, places=3)
