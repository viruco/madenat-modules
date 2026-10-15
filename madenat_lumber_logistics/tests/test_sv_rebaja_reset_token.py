# -*- coding: utf-8 -*-
"""P4 — Aislamiento y limpieza de la autorización de reapertura (AUD-ETQ-09).

El diseño anterior usaba un registro global de tokens (`_I2_REOPEN_TOKENS`,
clave `(dbname, uid, id)`) que **no** distinguía transacción y dejaba una ventana
de autorización reutilizable. Se sustituyó por una **vía privada de transición**
(`_i2_write_protected_state`), método `_`-prefijado que **no** es invocable por
RPC y que escribe con `super().write`: no hay estado compartido ni ventana de
autorización. Estas pruebas acreditan TOK-01..09.
"""
import datetime

from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.service.model import get_public_method
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaResetToken(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'TOK Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'TOK Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.user_oper = cls._mk('tok_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('tok_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.cl' % name,
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})

    def _cancelled(self, name, nominal=10.0):
        guia = self._guia(name)
        etq = self.env['stock.lot'].sudo().create({
            'name': name + '-E', 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, etq.id)]})
        sv = self.env['stock.lot'].sudo().create({
            'name': ('SV' + name.replace('-', '')[:16].ljust(16, '0')),
            'product_id': self.product.id, 'company_id': self.company.id,
            'lot_flow_type': 'volume', 'volume_source_guia_id': guia.id,
            'volume_purchase_m3': 100.0})
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        wline = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        wline.selected = True
        wline.cantidad_asignar_m3 = nominal
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        return imp

    # ── TOK-01/04: reapertura exitosa no deja autorización residual ─────────
    def test_tok_01_04_sin_residual_tras_exito(self):
        imp = self._cancelled('TOK-01')
        imp.reopen_reason = 'Motivo TOK-01'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')
        # (4) Una escritura directa posterior NO aprovecha autorización alguna.
        other = self._cancelled('TOK-01B')
        with self.assertRaises(UserError):
            other.write({'state': 'draft'})
        # (1) No existe registro global de autorización a nivel de módulo.
        from odoo.addons.madenat_lumber_logistics.models import (
            madenat_sv_imputation as mod)
        self.assertFalse(hasattr(mod, '_I2_REOPEN_TOKENS'))

    # ── TOK-02: excepción en la transición ⇒ documento intacto, sin residual ─
    def test_tok_02_excepcion_deja_documento_intacto(self):
        imp = self._cancelled('TOK-02')
        imp.reopen_reason = 'Motivo TOK-02'
        with patch.object(type(imp), '_i2_write_protected_state',
                          side_effect=UserError('fallo simulado')):
            with self.assertRaises(UserError):
                imp.with_user(self.user_oper).action_reopen_to_draft()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        with self.assertRaises(UserError):
            imp.write({'state': 'draft'})

    # ── TOK-03: fallo de validación intermedio ⇒ sin transición ni residual ─
    def test_tok_03_fallo_intermedio_sin_residual(self):
        imp = self._cancelled('TOK-03')
        imp.reopen_reason = 'Motivo TOK-03'
        imp.guia_processing_id.sudo().write(
            {'service_return_confirmation': 'no'})
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        with self.assertRaises(UserError):
            imp.write({'state': 'draft'})

    # ── TOK-05/06: sin autorización cruzada; la vía privada no es RPC ───────
    def test_tok_05_06_sin_autorizacion_cruzada(self):
        imp = self._cancelled('TOK-05')
        with self.assertRaises(AccessError):
            get_public_method(self.env['madenat.sv.imputation'],
                              '_i2_write_protected_state')
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).write({'state': 'draft'})
        with self.assertRaises(UserError):
            imp.sudo().write({'state': 'draft'})
        with self.assertRaises(UserError):
            imp.with_context(i2_reopen=True).write({'state': 'draft'})

    # ── TOK-07: multi-registro, repetición (idempotencia) ──────────────────
    def test_tok_07_multi_registro_y_repeticion(self):
        a = self._cancelled('TOK-07A')
        b = self._cancelled('TOK-07B')
        imps = a | b
        imps.reopen_reason = 'Motivo TOK-07'
        imps.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(a.state, 'draft')
        self.assertEqual(b.state, 'draft')
        imps.with_user(self.user_oper).action_reopen_to_draft()  # repetir
        self.assertEqual(a.state, 'draft')
        self.assertEqual(b.state, 'draft')

    # ── TOK-08: autor y fecha se derivan del entorno ───────────────────────
    def test_tok_08_identidad_del_entorno(self):
        from odoo import fields
        imp = self._cancelled('TOK-08')
        with self.assertRaises(UserError):
            imp.write({
                'state': 'draft',
                'reopened_by_id': self.user_jef.id,
                'reopen_date': '2000-01-01 00:00:00',
                'reopen_reason': 'Falso',
            })
        self.assertFalse(imp.reopened_by_id)
        before = fields.Datetime.now()
        imp.reopen_reason = 'Motivo TOK-08'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        after = fields.Datetime.now()
        self.assertEqual(imp.reopened_by_id, self.user_oper)
        self.assertTrue(before <= imp.reopen_date <= after)

    # ── TOK-09: sin estado compartido (multi-proceso) ──────────────────────
    def test_tok_09_sin_estado_compartido(self):
        from odoo.addons.madenat_lumber_logistics.models import (
            madenat_sv_imputation as mod)
        mutable = [n for n, v in vars(mod).items()
                   if isinstance(v, (set, dict, list)) and 'TOKEN' in n.upper()]
        self.assertFalse(mutable, 'No debe existir registro global de tokens')
        imp = self._cancelled('TOK-09')
        imp.reopen_reason = 'Motivo TOK-09'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')
        other = self._cancelled('TOK-09B')
        with self.assertRaises(UserError):
            other.write({'state': 'draft'})
