# -*- coding: utf-8 -*-
"""S3 — No persistir/borrar en silencio un documento de rebaja VACÍO (FASE 10).

Defecto **F3** del diagnóstico
``DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015``: «Guardar borrador»
(``_i2_build_imputation``) **no** exigía ninguna etiqueta incluida; sólo
``action_apply`` lo exigía. Guardar sin seleccionar (o desmarcar todo lo ya
registrado) dejaba/borraba líneas **en silencio**, produciendo el documento vacío
vinculado al SV que hoy explica `IMP04823`.

Cubre **T6**: guardar sin etiquetas ⇒ ``UserError`` de negocio en español; guardar
con una etiqueta ⇒ OK; la anulación y el «Volver a borrador» siguen funcionando;
y un guardado rechazado **no** pierde las líneas ya registradas.

Datos 100 % transaccionales (``TransactionCase``, rollback).
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaEmptyGuard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SG Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'SG Supplier', 'is_company': True})
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'sg_oper', 'login': 'sg_oper',
            'email': 'sg_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-15'})

    def _etq(self, guia, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': name, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal):
        return self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})

    def _wizard(self, guia, sv):
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        return wiz

    def _wline(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _expect_user_error(self, func, *args, **kwargs):
        """Ejecuta ``func`` esperando ``UserError`` **sin** el savepoint de
        ``assertRaises`` (que revierte los efectos del bloque y ocultaría la
        creación o el borrado silencioso que esta suite debe detectar)."""
        try:
            func(*args, **kwargs)
        except UserError as exc:
            return str(exc)
        raise AssertionError('Se esperaba UserError y no se produjo')

    # ── T6: guardar sin etiquetas ⇒ bloqueo de negocio en español ──────────
    def test_sg_01_guardar_sin_etiquetas_bloquea(self):
        guia = self._guia('SG-01')
        self._etq(guia, 'SG-01-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0001', 100.0)
        wiz = self._wizard(guia, sv)
        self.assertTrue(wiz.line_ids)                 # candidatas listadas
        self.assertFalse(wiz.line_ids.filtered('selected'))
        message = self._expect_user_error(wiz.sudo().action_prepare)
        self.assertIn('al menos una etiqueta', message)
        # Sin documento creado para la guía (no queda un vacío silencioso).
        self.assertFalse(self.Imputation.sudo().search(
            [('guia_processing_id', '=', guia.id)]))
        self.assertFalse(wiz.imputation_id)

    def test_sg_02_guardar_con_una_etiqueta_ok(self):
        guia = self._guia('SG-02')
        e = self._etq(guia, 'SG-02-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0002', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.sudo().action_prepare()
        imp = wiz.imputation_id
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.line_ids), 1)

    def test_sg_03_no_se_pierden_lineas_por_un_guardado_rechazado(self):
        guia = self._guia('SG-03')
        e = self._etq(guia, 'SG-03-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0003', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.sudo().action_prepare()
        imp = wiz.imputation_id
        self.assertEqual(len(imp.line_ids), 1)
        # Reabrir y DESMARCAR todo: el guardado se rechaza y NO borra nada.
        wiz2 = self._wizard(guia, sv)
        self.assertEqual(wiz2.imputation_id, imp)
        wiz2.line_ids.write({'selected': False})
        self.assertFalse(wiz2._i2_included_lines())
        self._expect_user_error(wiz2.sudo().action_prepare)
        imp.invalidate_recordset()
        self.assertEqual(len(imp.line_ids), 1)        # sin borrado silencioso
        self.assertEqual(imp.state, 'draft')

    def test_sg_04_anular_y_volver_a_borrador_siguen_funcionando(self):
        guia = self._guia('SG-04')
        e = self._etq(guia, 'SG-04-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0004', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.sudo().action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        imp.reopen_reason = 'SG-04 reapertura de control.'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')
        # Un documento reabierto conserva sus líneas (no es un vacío).
        self.assertEqual(len(imp.line_ids), 1)

    def test_sg_05_aplicar_sin_etiquetas_tambien_bloquea(self):
        guia = self._guia('SG-05')
        self._etq(guia, 'SG-05-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0005', 100.0)
        wiz = self._wizard(guia, sv)
        message = self._expect_user_error(
            wiz.with_user(self.user_oper).action_apply)
        self.assertIn('al menos una etiqueta', message)
        self.assertFalse(self.Imputation.sudo().search(
            [('guia_processing_id', '=', guia.id)]))

    def test_sg_06_destino_sv_sin_cantidad_sigue_permitido(self):
        """SAVE-05 se conserva: una fila de destino a 0 NO se bloquea."""
        guia = self._guia('SG-06')
        e = self._etq(guia, 'SG-06-E', 10.0)
        sv = self._sv(guia, 'SV0000SG0006', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()                  # fila a 0.0
        wiz.sudo().action_prepare()                   # permitido (no aplica)
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.line_ids), 1)
        self.assertFalse(imp.sv_line_ids)
