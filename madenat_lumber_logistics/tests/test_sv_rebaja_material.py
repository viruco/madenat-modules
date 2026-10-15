# -*- coding: utf-8 -*-
"""Rediseño operativo «Registrar rebaja» — material del packing list (2026-10-10).

Verifica que el asistente presente el material del retorno (etiqueta, SKU,
dimensiones, piezas y volumen) a partir de campos reales, sin cortar el nombre
concatenado del lote, sin duplicar disponibilidad y sin crear un saldo paralelo.
Datos 100 % transaccionales.
"""
import re

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaMaterial(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'MAT Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'MAT Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.PackingLine = cls.env['madenat.guia.processing.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-10'})

    def _packing_line(self, guia, lot_name, sku, esp, anc, largo, pieces, vol):
        return self.PackingLine.sudo().create({
            'processing_id': guia.id, 'product_id': self.product.id,
            'lot_name': lot_name, 'sku_original': sku,
            'espesor_nominal_mm': esp, 'ancho_nominal_mm': anc,
            'largo_nominal_m': largo, 'pieces': pieces, 'vol_purchase_m3': vol})

    def _lot(self, guia, lot_name, sku, esp, anc, largo, pieces, vol):
        digits = re.sub(r'[^0-9]', '', guia.name or '')
        name = ' '.join(p for p in (lot_name, sku, digits) if p)
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': lot_name, 'espesor_mm': esp, 'ancho_mm': anc,
            'largo_m': largo, 'piezas': pieces,
            'volume_purchase_m3': vol, 'vol_shipment_m3': vol})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal):
        return self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})

    def _wizard(self, guia, sv=None):
        wiz = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({'guia_processing_id': guia.id})
        if sv:
            wiz.sv_lot_id = sv.id
        wiz._onchange_guia_processing_id()
        return wiz

    # ══════════════════════════════════════════════════════════════════════
    # MAP — mapeo de datos del packing list
    # ══════════════════════════════════════════════════════════════════════
    def test_map_01_material_mapeado(self):
        guia = self._guia('MAT-MAP01')
        self._packing_line(guia, 'D100', 'SKU-100', 45.0, 120.0, 3.0, 100, 5.0)
        self._lot(guia, 'D100', 'SKU-100', 45.0, 120.0, 3.0, 100, 5.0)
        wiz = self._wizard(guia)
        line = wiz.line_ids[0]
        self.assertEqual(line.etiqueta_ref, 'D100')
        self.assertEqual(line.sku_origen, 'SKU-100')
        self.assertAlmostEqual(line.espesor_mm, 45.0, 3)
        self.assertAlmostEqual(line.ancho_mm, 120.0, 3)
        self.assertAlmostEqual(line.largo_m, 3.0, 3)
        self.assertEqual(line.piezas_lote, 100)
        self.assertAlmostEqual(line.volumen_documental_m3, 5.0, 3)
        self.assertAlmostEqual(line.espesor_declarado_mm, 45.0, 3)
        self.assertAlmostEqual(line.largo_declarado_m, 3.0, 3)

    def test_map_02_etiqueta_repetida_no_se_deduplica(self):
        guia = self._guia('MAT-MAP02')
        self._packing_line(guia, 'D200', 'SKU-2A', 45.0, 145.0, 3.25, 165, 3.445)
        self._packing_line(guia, 'D200', 'SKU-2B', 45.0, 145.0, 3.2, 10, 0.212)
        self._lot(guia, 'D200', 'SKU-2A', 45.0, 145.0, 3.25, 165, 3.445)
        self._lot(guia, 'D200', 'SKU-2B', 45.0, 145.0, 3.2, 10, 0.212)
        wiz = self._wizard(guia)
        self.assertEqual(len(wiz.line_ids), 2)
        self.assertEqual(wiz.line_ids.mapped('etiqueta_ref'), ['D200', 'D200'])
        self.assertEqual(
            sorted(wiz.line_ids.mapped('sku_origen')), ['SKU-2A', 'SKU-2B'])

    def test_map_03_sin_linea_de_packing_no_inventa(self):
        guia = self._guia('MAT-MAP03')
        self._lot(guia, 'D300', 'SKU-INEXISTENTE', 45.0, 120.0, 3.0, 50, 2.0)
        wiz = self._wizard(guia)
        line = wiz.line_ids[0]
        self.assertFalse(line.sku_origen)
        self.assertAlmostEqual(line.espesor_declarado_mm, 0.0, 3)
        self.assertEqual(line.etiqueta_ref, 'D300')
        self.assertAlmostEqual(line.largo_m, 3.0, 3)

    def test_map_04_volumen_no_se_recalcula(self):
        guia = self._guia('MAT-MAP04')
        self._packing_line(guia, 'D400', 'SKU-400', 45.0, 120.0, 3.0, 100, 9.999)
        self._lot(guia, 'D400', 'SKU-400', 45.0, 120.0, 3.0, 100, 9.999)
        wiz = self._wizard(guia)
        self.assertAlmostEqual(
            wiz.line_ids[0].volumen_documental_m3, 9.999, 3)

    # ══════════════════════════════════════════════════════════════════════
    # GRAN — granularidad y disponibilidad
    # ══════════════════════════════════════════════════════════════════════
    def test_gran_01_disponibilidad_por_lote_sin_doble_conteo(self):
        guia = self._guia('MAT-GRAN01')
        e1 = self._lot(guia, 'D500', 'SKU-5A', 45.0, 120.0, 3.0, 60, 5.0)
        e2 = self._lot(guia, 'D500', 'SKU-5B', 45.0, 120.0, 2.5, 40, 5.0)
        self.assertAlmostEqual(
            self.Imputation._i2_lot_available_for_m3(e1), 5.0, 3)
        self.assertAlmostEqual(
            self.Imputation._i2_lot_available_for_m3(e2), 5.0, 3)
        wiz = self._wizard(guia)
        self.assertAlmostEqual(
            sum(wiz.line_ids.mapped('etiqueta_disponible_m3')), 10.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SEM — semántica y cantidad preparada
    # ══════════════════════════════════════════════════════════════════════
    def test_sem_01_cantidad_preparada_y_pendiente(self):
        guia = self._guia('MAT-SEM01')
        e = self._lot(guia, 'D600', 'SKU-600', 45.0, 120.0, 3.0, 100, 10.0)
        sv = self._sv(guia, 'SV00000110001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        line.nominal_volume_m3 = 5.0
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 3.0})
        self.assertAlmostEqual(line.cantidad_asignar_m3, 3.0, 3)
        self.assertAlmostEqual(line.etiqueta_pendiente_m3, 2.0, 3)
        self.assertIn('3.000', wiz.assigned_summary)
        self.assertAlmostEqual(line.volumen_documental_m3, 10.0, 3)

    def test_amt_01_cero_negativo_y_exceso(self):
        guia = self._guia('MAT-AMT01')
        e = self._lot(guia, 'D700', 'SKU-700', 45.0, 120.0, 3.0, 100, 5.0)
        sv = self._sv(guia, 'SV00000110002', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        alloc = self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 0.0})
        # SAVE (2026-10-11): cantidad 0 = destino previsto sin cantidad ⇒ NO
        # bloquea el guardado; se conserva la línea y NO se persiste reparto.
        imp = wiz._i2_build_imputation()
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.sv_line_ids)
        self.assertEqual(len(imp.line_ids), 1)
        # Cantidad negativa ⇒ rechazo (no es «sin cantidad»).
        alloc.imputed_volume_m3 = -1.0
        with self.assertRaises(UserError):
            wiz._i2_build_imputation()
        alloc.imputed_volume_m3 = 6.0           # exceso > nominal 5
        with self.assertRaises(ValidationError):
            wiz._i2_build_imputation()

    # ══════════════════════════════════════════════════════════════════════
    # ARCH — presentación (ancho) sin cambiar el mecanismo
    # ══════════════════════════════════════════════════════════════════════
    def test_arch_01_formulario_amplio_y_target(self):
        from lxml import etree
        form = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        root = etree.fromstring(form.arch.encode())
        self.assertIn('o_xxl_form_view', root.get('class') or '')
        action = self.env.ref(
            '%s.action_madenat_sv_imputation_wizard' % MOD)
        self.assertEqual(action.target, 'current')
