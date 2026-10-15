# -*- coding: utf-8 -*-
"""Contrato de aplicación (POL-01..POL-08) — política APROBADA 2026-10-11.

Aplicar exige **≥ 1 reparto válido con cantidad positiva hacia un SV autorizado**
(validado en `madenat.sv.imputation._i2_validate_payload`). Sin reparto, el documento
sólo permanece en un estado **no aplicado**; una fila de volumen cero no satisface el
requisito. El reparto parcial mantiene el compromiso nominal con **pendiente explícito**.

Datos 100 % transaccionales (TransactionCase, rollback). Mismas fábricas que
`test_sv_rebaja_cierre.py`.
"""
import re

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaContratoAplicacion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'POL Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'POL Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'pol_oper', 'login': 'pol_oper',
            'email': 'pol_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        cls.user_jef = cls.env['res.users'].create({
            'name': 'pol_jef', 'login': 'pol_jef',
            'email': 'pol_jef@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_jefatura_operaciones').id])]})

    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes', 'date_emission': '2026-10-11'})

    def _etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': name, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal):
        return self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})

    def _imp(self, guia, label, nominal, sv=None, sv_vol=None):
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': label.id,
            'nominal_volume_m3': nominal})
        if sv is not None:
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': sv_vol})
        return imp, line

    def _avail(self, lot):
        return self.Imputation._i2_lot_available_for_m3(lot)

    def _wizard(self, guia, sv=None):
        Wizard = self.env['madenat.sv.imputation.wizard']
        wiz = Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({'guia_processing_id': guia.id})
        if sv:
            wiz.sv_lot_id = sv.id
        wiz._onchange_guia_processing_id()
        return wiz

    # ── POL-01: sin reparto → rechazo ─────────────────────────────────────
    def test_pol_01_sin_reparto_rechaza(self):
        guia = self._guia('POL01')
        e = self._etiqueta(guia, 'POL01-E', 10.0)
        self._sv(guia, 'SV0000POL0101', 100.0)
        imp, _l = self._imp(guia, e, 10.0)          # sin reparto
        before = self._avail(e)
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.snapshot_json)
        self.assertFalse(imp.execution_date)
        self.assertAlmostEqual(self._avail(e), before, 3)

    # ── POL-02: cantidad cero → rechazo ───────────────────────────────────
    def test_pol_02_cantidad_cero_rechaza(self):
        guia = self._guia('POL02')
        e = self._etiqueta(guia, 'POL02-E', 10.0)
        sv = self._sv(guia, 'SV0000POL0201', 100.0)
        imp, line = self._imp(guia, e, 10.0)
        with self.assertRaises(ValidationError):
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': 0.0})
        self.assertFalse(line.sv_allocation_ids)
        # Una imputación cuyo único reparto es cero/ausente no puede aplicarse.
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')

    # ── POL-03: reparto positivo válido → permitido ───────────────────────
    def test_pol_03_reparto_positivo_permite(self):
        guia = self._guia('POL03')
        e = self._etiqueta(guia, 'POL03-E', 10.0)
        sv = self._sv(guia, 'SV0000POL0301', 100.0)
        imp, _l = self._imp(guia, e, 10.0, sv, 10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')

    # ── POL-04: reparto parcial → pendiente comprometido explícito ────────
    def test_pol_04_parcial_pendiente_explicito(self):
        guia = self._guia('POL04')
        e = self._etiqueta(guia, 'POL04-E', 5.0)
        sv = self._sv(guia, 'SV0000POL0401', 100.0)
        imp, line = self._imp(guia, e, 5.0, sv, 3.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertAlmostEqual(imp.nominal_total_m3, 5.0, 3)
        self.assertAlmostEqual(imp.imputed_total_m3, 3.0, 3)
        self.assertAlmostEqual(line.etiqueta_pendiente_m3, 2.0, 3)
        self.assertAlmostEqual(self._avail(e), 0.0, 3)

    # ── POL-05: guardar/reabrir incompleto → conserva sin aplicar ─────────
    def test_pol_05_guardar_reabrir_incompleto(self):
        guia = self._guia('POL05')
        e = self._etiqueta(guia, 'POL05-E', 10.0)
        sv = self._sv(guia, 'SV0000POL0501', 100.0)
        wiz = self._wizard(guia, sv=sv)
        wline = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wline.selected = True
        wiz.action_prepare()                        # permitido (incompleto)
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.sv_line_ids)
        wiz2 = self._wizard(guia, sv=sv)            # reabrir
        self.assertEqual(wiz2.imputation_id, imp)
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.line_ids), 1)

    # ── POL-06: ORM/RPC directo sin reparto → mismo rechazo ───────────────
    def test_pol_06_orm_directo_rechaza(self):
        guia = self._guia('POL06')
        e = self._etiqueta(guia, 'POL06-E', 10.0)
        self._sv(guia, 'SV0000POL0601', 100.0)
        imp, _l = self._imp(guia, e, 10.0)
        # Sin pasar por el asistente: acceso directo al ORM.
        with self.assertRaises(UserError):
            self.Imputation.browse(imp.id).with_user(
                self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')

    # ── POL-07: repetición tras rechazo → sin efectos adicionales ─────────
    def test_pol_07_repeticion_sin_efectos(self):
        guia = self._guia('POL07')
        e = self._etiqueta(guia, 'POL07-E', 10.0)
        self._sv(guia, 'SV0000POL0701', 100.0)
        imp, _l = self._imp(guia, e, 10.0)
        before = self._avail(e)
        for _ in range(2):
            with self.assertRaises(UserError):
                imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.line_ids), 1)
        self.assertFalse(imp.sv_line_ids)
        self.assertFalse(imp.snapshot_json)
        self.assertAlmostEqual(self._avail(e), before, 3)

    # ── POL-08: aplicar→revertir→reasignar→aplicar ────────────────────────
    def test_pol_08_cadena_aplicar_revertir_reasignar(self):
        guia = self._guia('POL08')
        e = self._etiqueta(guia, 'POL08-E', 10.0)
        sv = self._sv(guia, 'SV0000POL0801', 100.0)
        imp, _l = self._imp(guia, e, 10.0, sv, 10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        imp.reversal_reason = 'POL08 (contrato).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertAlmostEqual(self._avail(e), 10.0, 3)
        self.assertEqual(len(imp.line_ids), 1)          # historia intacta
        self.assertEqual(len(imp.sv_line_ids), 1)
        imp2, _l2 = self._imp(guia, e, 10.0, sv, 10.0)
        imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp2.state, 'applied')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'reversed')
