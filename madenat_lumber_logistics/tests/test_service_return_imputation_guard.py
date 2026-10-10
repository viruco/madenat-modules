# -*- coding: utf-8 -*-
"""Reglas I2 de identificación de retorno de servicio (2026-10-07).

Cubre, sobre el mecanismo I2 existente y SIN efectos en stock:

* ALCANCE B: `action_apply` exige que la guía DESTINO esté marcada como retorno
  de servicio ("Sí"). No se exige al guardar borrador/pendiente; no se marca la
  guía automáticamente.
* ALCANCE A: con imputaciones SV `applied`, no se puede cambiar la
  identificación a "No" ni vaciarla; la corrección exige primero reversar.

TransactionCase: nada se persiste.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestServiceReturnImputationGuard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'Guard Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Guard Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']

        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('guard_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk('guard_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _guia(self, name, confirm='yes', tipo='granel'):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': tipo,
            'service_return_confirmation': confirm or False,
            'date_emission': '2026-10-07'})

    def _etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, label, nominal):
        return self.StockLot.sudo().create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})

    def _imputation(self, guia, etiqueta, sv, vol):
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': etiqueta.id,
            'nominal_volume_m3': etiqueta.volume_purchase_m3})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})
        return imp

    def _stock_snapshot(self):
        quants = self.env['stock.quant'].search(
            [('company_id', '=', self.company.id)])
        return {
            'qty': round(sum(quants.mapped('quantity')), 3),
            'moves': self.env['stock.move'].search_count(
                [('company_id', '=', self.company.id)]),
            'pickings': self.env['stock.picking'].search_count(
                [('company_id', '=', self.company.id)]),
        }

    # ALCANCE B ───────────────────────────────────────────────────────────
    def _apply_case(self, name, confirm):
        digits = ''.join(ch for ch in name if ch.isdigit()) or '1'
        sv_label = 'SV%011d' % int(digits)
        guia = self._guia(name, confirm=confirm)
        e = self._etiqueta(guia, '%s-E' % name, 10.0)
        sv = self._sv(guia, sv_label, 100.0)
        imp = self._imputation(guia, e, sv, 10.0)
        return guia, imp

    def test_01_apply_ok_con_si(self):
        guia, imp = self._apply_case('GUARD-01', 'yes')
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')

    def test_02_apply_rechaza_vacio(self):
        guia, imp = self._apply_case('GUARD-02', None)
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')

    def test_03_apply_rechaza_no(self):
        guia, imp = self._apply_case('GUARD-03', 'no')
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')

    def test_04_pending_no_exige_si(self):
        """Dejar pendiente NO exige 'Sí' (solo se exige al aplicar)."""
        guia, imp = self._apply_case('GUARD-04', None)
        imp.with_user(self.user_oper).action_pending()
        self.assertEqual(imp.state, 'pending')

    # ALCANCE A ───────────────────────────────────────────────────────────
    def test_05_cambio_a_no_rechazado_con_aplicada(self):
        guia, imp = self._apply_case('GUARD-05', 'yes')
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(UserError):
            guia.sudo().write({'service_return_confirmation': 'no'})
        with self.assertRaises(UserError):
            guia.sudo().write({'service_return_confirmation': False})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')

    def test_06_cambio_a_no_permitido_tras_reversa(self):
        guia, imp = self._apply_case('GUARD-06', 'yes')
        imp.with_user(self.user_oper).action_apply()
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        guia.sudo().write({'service_return_confirmation': 'no'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'no')

    def test_07_cambio_a_no_permitido_con_solo_borrador(self):
        guia = self._guia('GUARD-07', confirm='yes')
        e = self._etiqueta(guia, 'GUARD-07-E', 10.0)
        sv = self._sv(guia, 'SV00000009077', 100.0)
        self._imputation(guia, e, sv, 10.0)  # draft (sin aplicar)
        guia.sudo().write({'service_return_confirmation': 'no'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'no')

    def test_08_sin_efectos_stock(self):
        before = self._stock_snapshot()
        guia, imp = self._apply_case('GUARD-08', 'yes')
        imp.with_user(self.user_oper).action_apply()
        with self.assertRaises(UserError):
            guia.sudo().write({'service_return_confirmation': False})
        self.assertEqual(self._stock_snapshot(), before)
        self.assertEqual(
            self.env['madenat.sv.operation'].search_count(
                [('action_type', '=', 'imputacion')]), 0)


    # 09 ── Cristhian por login (si la base lo contiene): Jefatura real, su=False.
    def test_09_cristhian_aplica_revierte_y_cambia_no(self):
        user = self.env['res.users'].search(
            [('login', '=', 'cristhian.elguetag@gmail.com')], limit=1)
        if not user or user.id == self.env.ref('base.user_root').id:
            self.skipTest('Cristhian no representativo en esta base.')
        guia, imp = self._apply_case('GUARD-09', 'yes')
        imp.with_user(user).action_apply()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(UserError):
            guia.sudo().write({'service_return_confirmation': 'no'})
        imp.with_user(user).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        guia.sudo().write({'service_return_confirmation': 'no'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'no')
