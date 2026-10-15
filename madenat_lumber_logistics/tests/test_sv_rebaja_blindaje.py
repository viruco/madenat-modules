# -*- coding: utf-8 -*-
"""Rebaja de etiquetas — blindaje del ciclo documental (AUD-ETQ, 2026-10-11).

Cubre los hallazgos confirmados en la auditoría integral del ciclo:
* **AUD-ETQ-01** inmutabilidad real de una imputación aplicada (no puede volver
  a borrador/pendiente ni anularse por ``write``; la reversa exige la acción).
* **AUD-ETQ-02** la reversa exige motivo (trazabilidad; misma política que la
  relación de conciliación envío↔retorno).
* **AUD-ETQ-03** el mapa lote↔packing no elige una línea arbitrariamente ante
  colisión (queda vacío).
* **AUD-ETQ-04** la causa del saldo documental es concreta y trazable, y ofrece
  acceso a los documentos que la explican.
* **AUD-ETQ-05** cancelar un borrador libera exactamente su reserva; repetir no
  produce efectos; una aplicada no se anula.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
import re

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaBlindaje(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'AUD Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'AUD Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.PackingLine = cls.env['madenat.guia.processing.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']

        cls.user_oper = cls._mk('aud_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('aud_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name,
            'email': '%s@madenat.cl' % name,
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-11'})

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

    def _etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': name,
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

    def _line(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _imputation(self, guia, etiqueta, sv, vol, state='draft'):
        if etiqueta not in guia.lot_ids:
            guia.sudo().write({'lot_ids': [(4, etiqueta.id)]})
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': etiqueta.id,
            'nominal_volume_m3': etiqueta.volume_purchase_m3 or 0.0})
        if sv:
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': vol})
        if state and state != 'draft':
            imp.write({'state': state})
        return imp

    def _apply(self, imp):
        imp.with_user(self.user_oper).action_apply()
        return imp

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-01 — inmutabilidad real de una imputación aplicada
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_01_aplicado_no_vuelve_a_borrador(self):
        guia = self._guia('AUD-01')
        e = self._etiqueta(guia, 'AUD-01-E', 10.0)
        sv = self._sv(guia, 'SV00000011001', 100.0)
        imp = self._apply(self._imputation(guia, e, sv, 10.0))
        self.assertEqual(imp.state, 'applied')
        for bad_state in ('draft', 'pending', 'cancelled'):
            with self.assertRaises(UserError):
                imp.write({'state': bad_state})
        # Reversa directa por escritura (sin usuario de reversa): rechazada.
        with self.assertRaises(UserError):
            imp.write({'state': 'reversed'})
        self.assertEqual(imp.state, 'applied')
        # La reversa por la acción con motivo sí procede (historia intacta).
        imp.reversal_reason = 'Corrección trazable (AUD-ETQ-01).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-02 — la reversa exige motivo y queda auditada
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_02_reversa_exige_motivo(self):
        guia = self._guia('AUD-02')
        e = self._etiqueta(guia, 'AUD-02-E', 10.0)
        sv = self._sv(guia, 'SV00000011002', 100.0)
        imp = self._apply(self._imputation(guia, e, sv, 10.0))
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'applied')
        imp.reversal_reason = 'Motivo de reversa trazable (AUD-ETQ-02).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertTrue(self.AuditLog.search([
            ('action_type', '=', 'imputation_reverse'),
            ('batch_id', '=', imp.documentary_key)]))
        # Reversa repetida: sin doble efecto (ya no está aplicada).
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).action_reverse()

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-03 — el mapa lote↔packing no elige arbitrariamente
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_03_colision_mapa_no_elige(self):
        guia = self._guia('AUD03')
        # Dos líneas de packing con la MISMA clave (lot_name + SKU): colisión.
        self._packing_line(
            guia, 'D900', 'SKU-900', 45.0, 120.0, 3.0, 100, 5.0)
        self._packing_line(
            guia, 'D900', 'SKU-900', 45.0, 120.0, 2.5, 40, 2.0)
        col = self._lot(guia, 'D900', 'SKU-900', 45.0, 120.0, 3.0, 100, 5.0)
        # Una etiqueta sin colisión acredita que el mapa normal sigue vigente.
        self._packing_line(
            guia, 'D901', 'SKU-901', 45.0, 120.0, 3.0, 10, 1.0)
        ok = self._lot(guia, 'D901', 'SKU-901', 45.0, 120.0, 3.0, 10, 1.0)
        wiz = self._wizard(guia)
        self.assertFalse(self._line(wiz, col).packing_line_id)
        self.assertEqual(
            self._line(wiz, ok).packing_line_id.sku_original, 'SKU-901')

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-04 — causa del saldo concreta y trazable (documentos)
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_04_causa_aplicada_trazable(self):
        guia = self._guia('AUD04')
        e = self._etiqueta(guia, 'AUD-04-E', 10.0)
        sv = self._sv(guia, 'SV00000011004', 100.0)
        # Consumo aplicado de la MISMA guía (escenario de la captura).
        imp = self._apply(self._imputation(guia, e, sv, 10.0))
        wiz = self._wizard(guia, sv=sv)
        line = self._line(wiz, e)
        self.assertEqual(line.disponibilidad_estado, 'applied')
        self.assertIn(imp.name, line.disponibilidad_detalle)
        self.assertIn(imp, line.disponibilidad_imputacion_ids)
        self.assertEqual(line.disponibilidad_documentos_count, 1)
        # Sólo lectura: acceso al documento que explica el saldo.
        res = line.action_open_consuming_documents()
        self.assertEqual(res['res_model'], 'madenat.sv.imputation')
        self.assertIn(imp.id, res['domain'][0][2])
        # El resumen de la operación nombra la causa concreta.
        wiz.action_select_all()
        self.assertIn(imp.name, wiz.no_availability_note)

    def test_aud_etq_04b_causa_reservada_y_sin_capacidad(self):
        guia = self._guia('AUD04B')
        e_res = self._etiqueta(guia, 'AUD-04B-RES', 4.0)
        e_zero = self._etiqueta(guia, 'AUD-04B-ZERO', 0.0)
        sv = self._sv(guia, 'SV00000011014', 100.0)
        # Reserva por otro documento (borrador de otra guía; lot_ids es M2M).
        guia_res = self._guia('AUD04B-RES')
        imp_res = self._imputation(guia_res, e_res, sv, 4.0, state='draft')
        wiz = self._wizard(guia, sv=sv)
        line_res = self._line(wiz, e_res)
        self.assertEqual(line_res.disponibilidad_estado, 'reserved')
        self.assertIn(imp_res.name, line_res.disponibilidad_detalle)
        self.assertIn('borrador', line_res.disponibilidad_detalle)
        line_zero = self._line(wiz, e_zero)
        self.assertEqual(line_zero.disponibilidad_estado, 'no_capacity')
        self.assertIn('Sin capacidad', line_zero.disponibilidad_detalle)
        # Acceso a los documentos de las etiquetas sin disponibilidad.
        wiz.action_select_all()
        res = wiz.action_open_no_availability_docs()
        self.assertIn(imp_res.id, res['domain'][0][2])

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-05 — cancelación: libera reserva, repetir no altera, aplicada no
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_05_cancelacion_libera_reserva(self):
        guia = self._guia('AUD-05')
        e = self._etiqueta(guia, 'AUD-05-E', 10.0)
        sv = self._sv(guia, 'SV00000011005', 100.0)
        I = self.Imputation
        imp = self._imputation(guia, e, sv, 10.0, state='draft')
        self.assertAlmostEqual(I._i2_lot_available_for_m3(e), 0.0, 3)
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        self.assertAlmostEqual(I._i2_lot_available_for_m3(e), 10.0, 3)
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_cancel()
        self.assertAlmostEqual(I._i2_lot_available_for_m3(e), 10.0, 3)

    def test_aud_etq_05b_aplicada_no_se_anula(self):
        guia = self._guia('AUD05B')
        e = self._etiqueta(guia, 'AUD-05B-E', 10.0)
        sv = self._sv(guia, 'SV00000011015', 100.0)
        imp = self._apply(self._imputation(guia, e, sv, 10.0))
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'applied')
