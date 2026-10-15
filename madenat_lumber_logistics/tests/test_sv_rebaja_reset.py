# -*- coding: utf-8 -*-
"""Volver a borrador y reasignar rebajas (RESET, 2026-10-11).

Transición controlada **cancelled → draft** autorizada por Mauricio: reabrir un
documento anulado para corregir y continuar. NO se permite applied/reversed →
draft; no borra historia; no libera capacidad ajena.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaReset(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'RESET Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'RESET Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.user_oper = cls._mk('res_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('res_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name,
            'email': '%s@madenat.cl' % name, 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-11'})

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

    def _draft(self, name, nominal=10.0, vol=10.0, sv_nominal=100.0):
        guia = self._guia(name)
        e = self._etq(guia, name + '-E', nominal)
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:18].ljust(18, '0'),
                      sv_nominal)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = vol
        wiz.action_prepare()
        return guia, e, sv, wiz, wiz.imputation_id

    def _avail(self, lot):
        return self.Imputation._i2_lot_available_for_m3(lot)

    # ── RESET-01/03: draft → cancelar → reabrir (misma referencia + historia) ─
    def test_reset_01_03_reabrir_conserva_referencia_e_historia(self):
        guia, e, sv, wiz, imp = self._draft('RESET-01')
        ref = imp.name
        key = imp.documentary_key
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        self.assertEqual(imp.cancelled_by_id, self.user_oper)
        self.assertTrue(imp.cancellation_date)
        self.assertAlmostEqual(self._avail(e), 10.0, 3)   # reserva liberada
        imp.reopen_reason = 'Corregir cantidades'
        imp.with_user(self.user_jef).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(imp.name, ref)                   # misma referencia
        self.assertEqual(imp.documentary_key, key)
        self.assertEqual(imp.reopened_by_id, self.user_jef)
        self.assertTrue(imp.reopen_date)
        self.assertAlmostEqual(self._avail(e), 0.0, 3)    # reserva de nuevo
        self.assertEqual(len(imp.line_ids), 1)            # historia intacta
        self.assertEqual(len(imp.sv_line_ids), 1)
        for action in ('imputation_cancel', 'imputation_reopen'):
            self.assertTrue(self.AuditLog.search([
                ('batch_id', '=', key), ('action_type', '=', action)]))

    # ── RESET-02/03: pending → cancelar → reabrir (reservas correctas) ──────
    def test_reset_02_pending_reabrir_reservas(self):
        guia, e, sv, wiz, imp = self._draft('RESET-02')
        imp.with_user(self.user_oper).action_pending()
        self.assertEqual(imp.state, 'pending')
        imp.with_user(self.user_oper).action_cancel()
        self.assertAlmostEqual(self._avail(e), 10.0, 3)
        imp.reopen_reason = 'Reactivar para corregir'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)    # reserva una sola vez

    # ── RESET-04: repetir reapertura no duplica efectos ─────────────────────
    def test_reset_04_repetir_no_duplica(self):
        guia, e, sv, wiz, imp = self._draft('RESET-04')
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Motivo'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        audits = self.AuditLog.search_count([
            ('batch_id', '=', imp.documentary_key),
            ('action_type', '=', 'imputation_reopen')])
        imp.with_user(self.user_oper).action_reopen_to_draft()   # repetir
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(self.AuditLog.search_count([
            ('batch_id', '=', imp.documentary_key),
            ('action_type', '=', 'imputation_reopen')]), audits)
        self.assertAlmostEqual(self._avail(e), 0.0, 3)

    # ── RESET-05: capacidad consumida por otro documento ⇒ rechazo ──────────
    def test_reset_05_capacidad_consumida(self):
        guia, e, sv, wiz, imp = self._draft('RESET-05')
        imp.with_user(self.user_oper).action_cancel()          # libera
        guia2 = self._guia('RESET-05B')
        guia2.sudo().write({'lot_ids': [(4, e.id)]})
        sv2 = self._sv(guia2, 'SV0000RESET05B', 100.0)
        d2 = self.Imputation.sudo().create({'guia_processing_id': guia2.id})
        l2 = self.env['madenat.sv.imputation.line'].sudo().create({
            'imputation_id': d2.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        self.env['madenat.sv.imputation.sv.line'].sudo().create({
            'imputation_id': d2.id, 'imputation_line_id': l2.id,
            'sv_lot_id': sv2.id, 'imputed_volume_m3': 10.0})
        d2.with_user(self.user_oper).action_apply()
        imp.reopen_reason = 'Intentar reabrir'
        with self.assertRaises(UserError) as cm:
            imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertIn('comprometida', str(cm.exception))
        self.assertEqual(imp.state, 'cancelled')               # intacto
        self.assertEqual(d2.state, 'applied')                  # intacto

    # ── RESET-06: otro trabajo activo de la misma guía ⇒ conflicto ──────────
    def test_reset_06_conflicto_trabajo_activo(self):
        guia, e, sv, wiz, imp = self._draft('RESET-06')
        imp.with_user(self.user_oper).action_cancel()
        e2 = self._etq(guia, 'RESET-06-E2', 5.0)
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e2).selected = True
        self._wline(wiz2, e2).cantidad_asignar_m3 = 5.0
        wiz2.action_prepare()                                  # nuevo draft
        imp.reopen_reason = 'Motivo'
        with self.assertRaises(UserError) as cm:
            imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertIn('Ya existe trabajo en preparación', str(cm.exception))
        self.assertEqual(imp.state, 'cancelled')

    # ── RESET-07/10: permisos, compañía y motivo obligatorio ────────────────
    def test_reset_07_10_permisos_compania_motivo(self):
        guia, e, sv, wiz, imp = self._draft('RESET-07')
        imp.with_user(self.user_oper).action_cancel()
        # Motivo vacío / sólo espacios.
        imp.reopen_reason = '   '
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'cancelled')
        imp.reopen_reason = 'Motivo'
        plain = self.env['res.users'].create({
            'name': 'res_plain', 'login': 'res_plain',
            'email': 'res_plain@madenat.cl', 'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            imp.with_user(plain).action_reopen_to_draft()
        c_b = self.env['res.company'].sudo().create({'name': 'RESET B'})
        u_b = self._mk('res_b', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        u_b.write({'company_id': c_b.id, 'company_ids': [(6, 0, [c_b.id])]})
        with self.assertRaises(AccessError):
            imp.with_user(u_b).action_reopen_to_draft()
        self.assertEqual(imp.state, 'cancelled')

    # ── RESET-08: write directo no elude la transición controlada ───────────
    def test_reset_08_write_directo_no_elude(self):
        guia, e, sv, wiz, imp = self._draft('RESET-08')
        imp.with_user(self.user_oper).action_cancel()
        with self.assertRaises(UserError):
            imp.write({'state': 'draft'})
        with self.assertRaises(UserError):
            imp.write({'state': 'draft',
                       'reopened_by_id': self.user_oper.id})   # sin motivo
        with self.assertRaises(UserError):
            imp.with_context(i2_reopen=True).write({'state': 'draft'})
        self.assertEqual(imp.state, 'cancelled')

    # ── AUD-ETQ-07: write directo CON campos + contexto tampoco elude ───────
    def test_reset_08b_write_con_campos_y_contexto_no_elude(self):
        """Opción A: la vía directa se RECHAZA; exige la acción controlada.

        Enviar `state='draft'` junto con `reopened_by_id`, `reopen_reason` y
        los campos de fecha (y aun forzando contexto) NO autoriza la
        transición: la identidad del cliente no se acepta y el auditor de
        reapertura no se escribe.
        """
        guia, e, sv, wiz, imp = self._draft('RESET-08B')
        imp.with_user(self.user_oper).action_cancel()
        key = imp.documentary_key
        before = self.AuditLog.search_count([
            ('batch_id', '=', key), ('action_type', '=', 'imputation_reopen')])
        vals = {
            'state': 'draft',
            'reopened_by_id': self.user_oper.id,
            'reopen_reason': 'Forzado por el cliente',
            'reopen_date': '2026-10-12 00:00:00',
            'cancellation_date': '2026-10-12 00:00:00',
        }
        with self.assertRaises(UserError):
            imp.write(vals)
        with self.assertRaises(UserError):
            imp.sudo().write(dict(vals))               # ni siquiera sudo directo
        with self.assertRaises(UserError):
            imp.with_context(i2_reopen=True).write(dict(vals))
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        self.assertFalse(imp.reopened_by_id)
        self.assertFalse(imp.reopen_date)
        self.assertEqual(self.AuditLog.search_count([
            ('batch_id', '=', key), ('action_type', '=', 'imputation_reopen')]),
            before)
        # La acción controlada sí reabre (misma sesión).
        imp.reopen_reason = 'Reapertura autorizada'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'draft')

    # ── AUD-ETQ-08/10: coherencia de atributos de los campos sv_assignment_* ─
    def test_aud_etq_08_atributos_compute_coherentes(self):
        """Los campos que comparten cálculo deben tener `store` y
        `compute_sudo` coherentes. Los agregados ALMACENADOS son canónicos
        (`compute_sudo=True`, mismo valor para todos); la proyección no
        almacenada es por usuario (`compute_sudo=False`)."""
        Lot = self.env['stock.lot']
        stored = ['sv_assignment_nominal_m3', 'sv_assignment_applied_m3',
                  'sv_assignment_applied_count',
                  'sv_assignment_documental_balance_m3']
        live = ['sv_assignment_imputation_ids', 'sv_assignment_processor_id']
        for name in stored:
            field = Lot._fields[name]
            self.assertTrue(field.store, '%s debe ser almacenado' % name)
            self.assertTrue(field.compute_sudo, '%s debe ser canónico' % name)
            self.assertEqual(field.compute, '_compute_sv_assignment', name)
        for name in live:
            field = Lot._fields[name]
            self.assertFalse(field.store, '%s no debe ser almacenado' % name)
            self.assertFalse(field.compute_sudo, '%s no debe usar sudo' % name)
            self.assertEqual(
                field.compute, '_compute_sv_assignment_live', name)

    # ── RESET-09: applied/reversed NO vuelven a borrador ────────────────────
    def test_reset_09_aplicado_reversado_no_borrador(self):
        guia, e, sv, wiz, imp = self._draft('RESET-09')
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(imp.state, 'applied')
        imp.reversal_reason = 'RESET-09'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        with self.assertRaises(UserError):
            imp.write({'state': 'draft'})
        self.assertEqual(imp.state, 'reversed')

    # ── RESET-11: asistente abierto + cancelación externa ⇒ salida clara ────
    def test_reset_11_asistente_desactualizado(self):
        guia, e, sv, wiz, imp = self._draft('RESET-11')
        imp.with_user(self.user_oper).action_cancel()      # cancelación externa
        with self.assertRaises(UserError) as cm:
            wiz.action_prepare()
        self.assertIn('fue anulado', str(cm.exception))
        self.assertIn('Vuelve a borrador', str(cm.exception))
        wiz.reopen_reason = 'Reabrir desde el asistente'
        wiz.with_user(self.user_oper).action_wizard_reopen()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        self.assertIn('reabierto', wiz.save_result or '')

    # ── RESET-12: reabrir → cambiar cantidad → Guardar → Continuar ──────────
    def test_reset_12_reabrir_corregir_continuar(self):
        guia, e, sv, wiz, imp = self._draft('RESET-12', vol=4.0)
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Corregir'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)
        wiz2 = self._wizard(guia, sv)
        self.assertEqual(wiz2.imputation_id, imp)
        self._wline(wiz2, e).cantidad_asignar_m3 = 7.0
        wiz2.action_prepare()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 7.0, 3)
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)

    # ── RESET-13: reabrir → reasignar → Aplicar ─────────────────────────────
    def test_reset_13_reabrir_reasignar_aplicar(self):
        guia, e, sv, wiz, imp = self._draft('RESET-13', vol=4.0)
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Reasignar'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e).cantidad_asignar_m3 = 6.0
        wiz2.with_user(self.user_oper).action_apply()
        self.assertEqual(wiz2.imputation_id, imp)          # mismo documento
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(imp.imputed_total_m3, 6.0, 3)

    # ── RESET-14/18: varios SV y no reutilizar cancelado como nuevo ─────────
    def test_reset_14_18_varios_sv_y_nueva_operacion(self):
        guia = self._guia('RESET-14')
        e = self._etq(guia, 'RESET-14-E', 10.0)
        sv1 = self._sv(guia, 'SV0000RESET14A', 100.0)
        sv2 = self._sv(guia, 'SV0000RESET14B', 100.0)
        wiz = self._wizard(guia, sv1)
        self._wline(wiz, e).selected = True
        SvWizLine = self.env['madenat.sv.imputation.wizard.sv.line']
        SvWizLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': self._wline(wiz, e).id,
            'sv_lot_id': sv1.id, 'imputed_volume_m3': 4.0})
        SvWizLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': self._wline(wiz, e).id,
            'sv_lot_id': sv2.id, 'imputed_volume_m3': 3.0})
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Reabrir'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        wiz2 = self._wizard(guia, sv1)
        self._wline(wiz2, e).cantidad_asignar_m3 = 0.0     # cero en SV trabajo
        wiz2.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(len(imp.sv_line_ids), 1)          # sv2 conservado
        self.assertEqual(imp.sv_line_ids.sv_lot_id, sv2)
        # RESET-18: una apertura nueva NO reutiliza el (ex)cancelado.
        imp.with_user(self.user_oper).action_cancel()
        wiz3 = self._wizard(guia, sv1)
        self.assertFalse(wiz3.imputation_id)

    # ── RESET-15: fallo intermedio ⇒ atomicidad (guía no elegible) ──────────
    def test_reset_15_fallo_intermedio_atomico(self):
        guia, e, sv, wiz, imp = self._draft('RESET-15')
        imp.with_user(self.user_oper).action_cancel()
        guia.sudo().write({'service_return_confirmation': 'no'})
        imp.reopen_reason = 'Motivo'
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)

    # ── PHY-01: sin efectos físicos en todo el ciclo ────────────────────────
    def test_phy_01_sin_efectos_fisicos(self):
        def snap():
            return (
                self.env['stock.move'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.move.line'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.picking'].search_count(
                    [('company_id', '=', self.company.id)]))
        before = snap()
        guia, e, sv, wiz, imp = self._draft('RESET-PHY')
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Ciclo'
        imp.with_user(self.user_oper).action_reopen_to_draft()
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(snap(), before)
