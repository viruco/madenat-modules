# -*- coding: utf-8 -*-
"""Asignaciones SV — operación manual centrada en SV (CANON/19 §19.14).

Cubre los bloques A–G de la intervención 2026-10-10: entrada/consulta por SV,
alta desde el SV, selección explícita de etiquetas, conservación del borrador,
integridad etiqueta–guía y coherencia de volumen documental. Datos 100 %
transaccionales (TransactionCase, rollback): no asume BD vacía ni borra datos.
"""
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationManual(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'MAN Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'MAN Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

        cls.user_oper = cls.env['res.users'].create({
            'name': 'man_oper', 'login': 'man_oper',
            'email': 'man_oper@madenat.cl',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-10'})

    def _etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
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

    def _add_alloc(self, wiz, wline, sv, vol):
        return self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wline.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    # ── T-MAN-01 (Bloques A/B): contexto SV, sin auto-inclusión ──
    def test_man_01_contexto_sv_no_autoincluye(self):
        guia = self._guia('MAN-T01')
        self._etiqueta(guia, 'MAN-T01-E', 10.0)
        sv = self._sv(guia, 'SV00000002001', 100.0)
        defaults = self.Wizard.with_context(
            active_model='stock.lot', active_id=sv.id).default_get(
                ['sv_lot_id', 'guia_processing_id', 'line_ids'])
        self.assertEqual(defaults.get('sv_lot_id'), sv.id)
        self.assertFalse(defaults.get('guia_processing_id'))
        self.assertFalse(defaults.get('line_ids'))

    # ── T-MAN-02 (Bloque C): selección explícita ──
    def test_man_02_seleccion_explicita(self):
        guia = self._guia('MAN-T02')
        self._etiqueta(guia, 'MAN-T02-E1', 10.0)
        self._etiqueta(guia, 'MAN-T02-E2', 5.0)
        wiz = self._wizard(guia)
        self.assertEqual(len(wiz.line_ids), 2)
        self.assertFalse(any(wiz.line_ids.mapped('selected')))
        with self.assertRaises(UserError):
            wiz.action_propose_fifo()  # sin selección no propone nada
        wiz.action_select_all()
        self.assertTrue(all(wiz.line_ids.mapped('selected')))
        self.assertEqual(wiz.selected_line_count, 2)
        wiz.action_clear_selection()
        self.assertFalse(any(wiz.line_ids.mapped('selected')))

    # ── T-MAN-03 (Bloques B/C/G): subconjunto aplica ──
    def test_man_03_subconjunto_aplica(self):
        guia = self._guia('MAN-T03')
        e1 = self._etiqueta(guia, 'MAN-T03-E1', 10.0)
        self._etiqueta(guia, 'MAN-T03-E2', 8.0)
        sv = self._sv(guia, 'SV00000002031', 100.0)
        wiz = self._wizard(guia, sv=sv)
        wline = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e1)
        wline.selected = True
        self._add_alloc(wiz, wline, sv, 6.0)
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id   # SIMPLE: Aplicar permanece en el asistente
        self.assertEqual(imp.state, 'applied')
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(imp.line_ids.processed_lot_id, e1)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 6.0, 3)

    # ── T-MAN-04 (Bloque D): reapertura conserva selección y reparto ──
    def test_man_04_reapertura_conserva(self):
        guia = self._guia('MAN-T04')
        e1 = self._etiqueta(guia, 'MAN-T04-E1', 10.0)
        self._etiqueta(guia, 'MAN-T04-E2', 5.0)
        sv_a = self._sv(guia, 'SV00000002041', 100.0)
        sv_b = self._sv(guia, 'SV00000002042', 100.0)
        wiz = self._wizard(guia)
        wl1 = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e1)
        wl1.selected = True
        self._add_alloc(wiz, wl1, sv_a, 4.0)
        self._add_alloc(wiz, wl1, sv_b, 6.0)
        imp = wiz._i2_build_imputation()
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 2)
        # Reabrir por default_get reproduce selección y reparto guardados.
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids',
                 'sv_line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.line_ids), 1)
        self.assertTrue(wiz2.line_ids.selected)
        self.assertEqual(len(wiz2.line_ids.sv_alloc_ids), 2)
        self.assertAlmostEqual(
            sum(wiz2.line_ids.sv_alloc_ids.mapped('imputed_volume_m3')),
            10.0, 3)
        # Volver a construir no duplica líneas ni reparto.
        imp2 = wiz2._i2_build_imputation()
        self.assertEqual(imp2, imp)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 2)

    # ── T-MAN-05 (D3 / criterio de aceptación): dos guías, un SV ──
    def test_man_05_dos_guias_un_sv(self):
        g1 = self._guia('MAN-T05-A')
        g2 = self._guia('MAN-T05-B')
        e1 = self._etiqueta(g1, 'MAN-T05-EA', 10.0)
        e2 = self._etiqueta(g2, 'MAN-T05-EB', 12.0)
        sv = self._sv(g1, 'SV00000002051', 100.0)
        for guia, etiqueta, vol in ((g1, e1, 4.0), (g2, e2, 6.0)):
            wiz = self._wizard(guia, sv=sv)
            wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etiqueta)
            wl.selected = True
            self._add_alloc(wiz, wl, sv, vol)
            wiz.with_user(self.user_oper).action_apply()
        self.assertEqual(len(sv.sv_assignment_sv_line_ids), 2)
        self.assertEqual(sv.sv_assignment_applied_count, 2)
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 10.0, 3)
        self.assertAlmostEqual(
            sv.sv_assignment_documental_balance_m3, 90.0, 3)

    # ── T-MAN-06 (Bloque E): etiqueta ajena a la guía rechazada ──
    def test_man_06_etiqueta_ajena_rechazada(self):
        g1 = self._guia('MAN-T06-A')
        g2 = self._guia('MAN-T06-B')
        ajena = self._etiqueta(g2, 'MAN-T06-EXT', 10.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': g1.id})
        with self.assertRaises(ValidationError):
            self.ImputationLine.sudo().create({
                'imputation_id': imp.id, 'processed_lot_id': ajena.id,
                'nominal_volume_m3': 10.0})
        self.assertFalse(imp.line_ids)

    # ── T-MAN-07 (Bloque F): el reparto no supera el nominal ──
    def test_man_07_reparto_supera_nominal(self):
        guia = self._guia('MAN-T07')
        e = self._etiqueta(guia, 'MAN-T07-E', 10.0)
        sv = self._sv(guia, 'SV00000002071', 100.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        with self.assertRaises(ValidationError):
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': 11.0})
        # Varias líneas del mismo documento tampoco eluden el límite.
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 6.0})
        with self.assertRaises(ValidationError):
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': 5.0})

    # ── T-MAN-08 (D11): reparto parcial admitido ──
    def test_man_08_parcial_admitido(self):
        guia = self._guia('MAN-T08')
        e = self._etiqueta(guia, 'MAN-T08-E', 10.0)
        sv = self._sv(guia, 'SV00000002081', 100.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 4.0})
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 4.0, 3)

    # ── T-MAN-09 (Bloque F): edición del nominal no elude la capacidad ──
    def test_man_09_nominal_no_elude(self):
        guia = self._guia('MAN-T09')
        e = self._etiqueta(guia, 'MAN-T09-E', 10.0)
        sv = self._sv(guia, 'SV00000002091', 100.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 8.0})
        with self.assertRaises(ValidationError):
            line.write({'nominal_volume_m3': 5.0})  # 8 > 5
        # El nominal tampoco supera el del lote (techo duro existente).
        line.write({'nominal_volume_m3': 12.0})
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()

    # ── T-MAN-10 (Bloque B/D): documento multi-SV no pierde reparto ──
    def test_man_10_multisv_no_se_pierde(self):
        guia = self._guia('MAN-T10')
        e1 = self._etiqueta(guia, 'MAN-T10-E1', 10.0)
        sv_a = self._sv(guia, 'SV00000002101', 100.0)
        sv_b = self._sv(guia, 'SV00000002102', 100.0)
        wiz = self._wizard(guia)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e1)
        wl.selected = True
        self._add_alloc(wiz, wl, sv_a, 4.0)
        self._add_alloc(wiz, wl, sv_b, 6.0)
        imp = wiz._i2_build_imputation()
        self.assertEqual(len(imp.sv_line_ids), 2)
        # Reabrir y volver a guardar: conserva el reparto a otros SV.
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().create(defaults)
        wiz2.sv_lot_id = sv_a.id
        imp2 = wiz2._i2_build_imputation()
        self.assertEqual(imp2, imp)
        self.assertEqual(len(imp.sv_line_ids), 2)
        self.assertEqual(
            sorted(imp.sv_line_ids.mapped('sv_lot_id').ids),
            sorted([sv_a.id, sv_b.id]))

    # ── T-MAN-11 (Regresión): sin efecto en stock ni ledger ──
    def test_man_11_sin_efecto_stock(self):
        guia = self._guia('MAN-T11')
        e = self._etiqueta(guia, 'MAN-T11-E', 10.0)
        sv = self._sv(guia, 'SV00000002111', 100.0)
        before_quant = self.env['stock.quant'].search_count([])
        before_move = self.env['stock.move'].search_count([])
        ledger = self.env['madenat.sv.operation'].search_count(
            [('lot_id', '=', sv.id)])
        wiz = self._wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        self._add_alloc(wiz, wl, sv, 10.0)
        wiz.with_user(self.user_oper).action_apply()
        self.assertEqual(
            self.env['stock.quant'].search_count([]), before_quant)
        self.assertEqual(
            self.env['stock.move'].search_count([]), before_move)
        self.assertEqual(
            self.env['madenat.sv.operation'].search_count(
                [('lot_id', '=', sv.id)]), ledger)

    # ── T-MAN-12 (Bloque D): reapertura por onchange reproduce el borrador ──
    def test_man_12_onchange_reabre_borrador(self):
        guia = self._guia('MAN-T12')
        e1 = self._etiqueta(guia, 'MAN-T12-E1', 10.0)
        sv = self._sv(guia, 'SV00000002121', 100.0)
        wiz = self._wizard(guia)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e1)
        wl.selected = True
        self._add_alloc(wiz, wl, sv, 5.0)
        imp = wiz._i2_build_imputation()
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({'guia_processing_id': guia.id})
        wiz2._onchange_guia_processing_id()
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.line_ids), 1)
        self.assertTrue(wiz2.line_ids.selected)
        self.assertAlmostEqual(
            sum(wiz2.line_ids.sv_alloc_ids.mapped('imputed_volume_m3')),
            5.0, 3)




