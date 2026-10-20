# -*- coding: utf-8 -*-
"""G2 — Vínculo persistente entre una guía procesada y su picking de ingreso.

Cubre T-G2-01..10. `TransactionCase`: todo se revierte. El vínculo es
puramente documental (atribución): NO crea ni modifica `stock.quant`,
`stock.lot`, `stock.move`, `stock.move.line` ni capas de valoración.
No se infieren vínculos en pickings históricos; solo los nuevos lo reciben.

Intake sigue siendo la puerta única de ingesta; G2 NO es una vía de ingesta ni
implementa retornos automáticos (eso es G3, fuera de alcance).
"""
import inspect

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_core.models.reception_service import (
    LumberReceptionService,
)

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'g2')
class TestGuiaPickingLink(TransactionCase):
    """T-G2-01..10 sobre `stock.picking.guia_processing_id`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.ReopenWizard = cls.env['madenat.guia.processing.reopen.wizard']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.partner = cls.env['res.partner'].create({
            'name': 'G2 Proveedor', 'is_company': True, 'supplier_rank': 1})
        cls.product = cls.env['product.product'].create({
            'name': 'G2 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='compra', state='draft'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 1.0})

    def _make_lot(self, name, volumen=5.0):
        return self.StockLot.create({
            'name': name, 'product_id': self.product.id,
            'volumen_m3': volumen})

    def _make_source_lot(self, name, qty=10.0):
        lot = self.StockLot.create({
            'name': name, 'product_id': self.product.id,
            'volumen_m3': qty, 'company_id': self.company.id})
        self.Quant._update_available_quantity(
            self.product, self.internal, qty, lot_id=lot)
        return lot

    # ── T-G2-01 — Asignación correcta ─────────────────────────────────────
    def test_t_g2_01_asignacion_ingreso_produccion(self):
        guia = self._make_guia('G2-01')
        lot = self._make_lot('G2-01-LOT', 5.0)
        guia.lot_ids = [(6, 0, [lot.id])]

        picking = guia._get_or_create_picking_unified()

        self.assertTrue(picking)
        self.assertEqual(picking.guia_processing_id, guia)
        self.assertEqual(
            self.Picking.search_count(
                [('guia_processing_id', '=', guia.id)]), 1)
        # Recuperación en el mismo flujo: no duplica ni cambia el vínculo.
        picking2 = guia._get_or_create_picking_unified()
        self.assertEqual(picking2, picking)
        self.assertEqual(picking2.guia_processing_id, guia)

    # ── T-G2-02 — Exclusión de BT-04 (consumo) ────────────────────────────
    def test_t_g2_02_exclusion_bt04_consumo(self):
        source = self._make_source_lot('G2-02-SRC')
        guia = self._make_guia('G2-02', tipo='service')
        guia.source_lot_ids = [(6, 0, [source.id])]

        consumption = guia._get_or_create_consumption_picking()

        self.assertEqual(guia.consumption_picking_id, consumption)
        self.assertEqual(consumption.picking_type_code, 'outgoing')
        self.assertFalse(
            consumption.guia_processing_id,
            'El consumo BT-04 no debe recibir el vínculo de guía de producción')

    # ── T-G2-03 — Exclusión de retornos (consumo y SV) ────────────────────
    def test_t_g2_03_exclusion_retornos(self):
        source = self._make_source_lot('G2-03-SRC')
        guia = self._make_guia('G2-03', tipo='service')
        guia.source_lot_ids = [(6, 0, [source.id])]
        consumption = guia._get_or_create_consumption_picking()

        return_picking = guia._reverse_consumption_picking()

        self.assertTrue(return_picking)
        self.assertNotEqual(return_picking, consumption)
        self.assertFalse(return_picking.guia_processing_id)
        returns = self.Picking.search(
            [('origin', '=', 'Return of %s' % consumption.name)])
        self.assertTrue(returns)
        self.assertFalse(returns.guia_processing_id)
        # El creador de retorno SV tampoco asigna el vínculo.
        src = inspect.getsource(type(self.Guia)._sv_create_volume_return)
        self.assertIn("'guia_processing_id': False", src)


    # ── T-G2-04 — Exclusión de recepción normal ───────────────────────────
    def test_t_g2_04_exclusion_recepcion_normal(self):
        reception = self.env['lumber.reception'].create({
            'name': 'G2-04-REC', 'supplier_id': self.partner.id,
            'location_id': self.internal.id, 'ingestion_profile': 'metric'})
        picking = LumberReceptionService(self.env).create_stock_picking(
            reception)

        self.assertTrue(picking)
        self.assertEqual(picking.reception_id, reception)
        self.assertFalse(
            picking.guia_processing_id,
            'La recepción de compra mantiene reception_id y NO el vínculo G2')

    # ── T-G2-05 — Exclusión de logística (contenedor/rebaja/exportación) ──
    def test_t_g2_05_exclusion_logistica(self):
        guia = self._make_guia('G2-05')
        lot = self._make_lot('G2-05-LOT')
        guia.lot_ids = [(6, 0, [lot.id])]
        production = guia._get_or_create_picking_unified()
        self.assertEqual(production.guia_processing_id, guia)

        # Punto de asignación ÚNICO: solo el creador del ingreso de producción
        # asigna el vínculo; consumo, retornos y legacy NO lo hacen.
        GuiaCls = type(self.Guia)
        marker = "'guia_processing_id': self.id"
        self.assertIn(
            marker,
            inspect.getsource(GuiaCls._get_or_create_picking_unified))
        for method_name in (
                '_get_or_create_consumption_picking',
                '_reverse_consumption_picking',
                '_sv_create_volume_return',
                '_create_picking_and_lines'):
            self.assertNotIn(
                marker, inspect.getsource(getattr(GuiaCls, method_name)),
                '%s no debe asignar el vínculo de picking' % method_name)

        # Ningún picking de salida (contenedor/rebaja/exportación) porta el
        # vínculo; un picking logístico simulado tampoco lo recibe.
        self.assertFalse(self.Picking.search([
            ('guia_processing_id', '!=', False),
            ('picking_type_code', '=', 'outgoing')]))
        out_type = self.warehouse.out_type_id
        logistic = self.Picking.create({
            'picking_type_id': out_type.id, 'partner_id': self.partner.id,
            'location_id': self.internal.id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'origin': 'Rebaja CONT-G2-05 / EMB-G2-05'})
        self.assertFalse(logistic.guia_processing_id)


    # ── T-G2-06 — Lotes compartidos ───────────────────────────────────────
    def test_t_g2_06_lotes_compartidos(self):
        shared = self._make_lot('G2-06-SHARED', 5.0)
        g1 = self._make_guia('G2-06-A')
        g2 = self._make_guia('G2-06-B')
        g1.lot_ids = [(6, 0, [shared.id])]
        g2.lot_ids = [(6, 0, [shared.id])]

        p1 = g1._get_or_create_picking_unified()
        p2 = g2._get_or_create_picking_unified()

        self.assertNotEqual(p1, p2, 'Cada guía conserva su propio albarán')
        self.assertEqual(p1.guia_processing_id, g1)
        self.assertEqual(p2.guia_processing_id, g2)
        # El vínculo no se calcula por lot_id: lotes compartidos no confunden.
        self.assertNotEqual(p1.guia_processing_id, p2.guia_processing_id)

    # ── T-G2-07 — Estabilidad tras reapertura G1 ──────────────────────────
    def test_t_g2_07_estabilidad_tras_reopen(self):
        guia = self._make_guia('G2-07', state='verified')
        lot = self._make_lot('G2-07-LOT', 5.0)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking = guia._get_or_create_picking_unified()
        self.assertEqual(picking.guia_processing_id, guia)

        wiz = self.ReopenWizard.create(
            {'guia_processing_id': guia.id, 'reason': 'corrección G2'})
        wiz.action_confirm()

        self.assertEqual(guia.state, 'draft')
        self.assertTrue(picking.exists(), 'El albarán histórico se preserva')
        self.assertEqual(
            picking.guia_processing_id, guia,
            'La reapertura G1 no borra ni muta el vínculo del picking original')


    # ── T-G2-08 — Multi-company (comportamiento real) ─────────────────────
    def test_t_g2_08_multi_company_comportamiento_real(self):
        # Comportamiento real del modelo: la guía NO tiene company_id y el
        # campo NO impone check_company (patrón del proyecto). No se inventa
        # un constraint; se documenta la limitación.
        self.assertNotIn('company_id', self.Guia._fields)
        self.assertFalse(
            self.Picking._fields['guia_processing_id'].check_company)

        guia = self._make_guia('G2-08')
        lot = self._make_lot('G2-08-LOT')
        guia.lot_ids = [(6, 0, [lot.id])]
        picking = guia._get_or_create_picking_unified()

        # El picking se crea en la compañía del entorno del flujo (misma que
        # la guía en el punto de asignación).
        self.assertEqual(picking.company_id, self.company)
        self.assertEqual(picking.guia_processing_id, guia)

    # ── T-G2-09 — Sin efectos físicos ─────────────────────────────────────
    def test_t_g2_09_sin_efectos_fisicos(self):
        guia = self._make_guia('G2-09')
        lot = self._make_lot('G2-09-LOT', 5.0)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking = guia._get_or_create_picking_unified()

        quant_before = self.Quant.search_count([])
        lot_before = self.StockLot.search_count([])
        move_before = self.Move.search_count([])
        move_line_before = self.MoveLine.search_count([])
        has_vl = 'stock.valuation.layer' in self.env
        vl_before = (
            self.env['stock.valuation.layer'].search_count([]) if has_vl else 0)

        # Escribir el vínculo (idempotente, limpiar y reponer) no debe tocar
        # ningún objeto físico.
        picking.write({'guia_processing_id': guia.id})
        picking.write({'guia_processing_id': False})
        picking.write({'guia_processing_id': guia.id})

        self.assertEqual(self.Quant.search_count([]), quant_before)
        self.assertEqual(self.StockLot.search_count([]), lot_before)
        self.assertEqual(self.Move.search_count([]), move_before)
        self.assertEqual(self.MoveLine.search_count([]), move_line_before)
        if has_vl:
            self.assertEqual(
                self.env['stock.valuation.layer'].search_count([]), vl_before)
        lot.invalidate_recordset()
        self.assertAlmostEqual(
            sum(lot.quant_ids.mapped('quantity')), 0.0, places=3,
            msg='El vínculo no crea ni modifica stock.quant')


    # ── T-G2-10 — Históricos sin inferencia ───────────────────────────────
    def test_t_g2_10_historicos_no_inferidos(self):
        guia = self._make_guia('G2-10')
        pt = self.env.ref('stock.picking_type_in')
        # Picking "histórico": origin == guia.name, sin vínculo persistente.
        historical = self.Picking.create({
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': self.internal.id, 'origin': guia.name})
        self.assertFalse(historical.guia_processing_id)

        picked = guia._get_or_create_picking_unified()

        self.assertEqual(picked, historical, 'Se reutiliza, no se recrea')
        self.assertFalse(
            picked.guia_processing_id,
            'Los pickings históricos sin vínculo NO se infieren ni actualizan')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'g2')
class TestGuiaPickingLinkSvReturn(SvTestCommon, TransactionCase):
    """T-G2-03 (variante SV) — el retorno por lote SV no recibe el vínculo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def test_t_g2_03b_exclusion_retorno_sv(self):
        guia = self._sv_make_guia('G2-03B', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='G2SV000000001', volume=40.3)
        receipt = self._sv_receipt(guia, lot, 40.3)

        guia.action_force_cancel()

        returns = self.env['stock.picking'].search(
            [('origin', '=', 'Return of %s' % receipt.name)])
        self.assertTrue(returns, 'Debe generarse el retorno del lote SV')
        self.assertFalse(
            returns.guia_processing_id,
            'El retorno SV no debe copiar ni recibir guia_processing_id')
