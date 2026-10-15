# -*- coding: utf-8 -*-
"""Simplificación operativa de la rebaja (SIMPLE/CLIENT, 2026-10-11).

Recorrido de DOS acciones en la MISMA ventana: seleccionar → indicar m³ →
**Guardar** (continuar después) o **Aplicar** (ejecutar la rebaja). Sin
«Preparar asignación» obligatorio, sin Guardar previo y sin abrir el documento.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
from lxml import etree

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSimple(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SIM Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'SIM Supplier', 'is_company': True})
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.view = cls.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        cls.user_oper = cls.env['res.users'].create({
            'name': 'sim_oper', 'login': 'sim_oper',
            'email': 'sim_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        cls.user_jef = cls.env['res.users'].create({
            'name': 'sim_jef', 'login': 'sim_jef',
            'email': 'sim_jef@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_jefatura_operaciones'
                ).id])]})

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

    def _alloc(self, wiz, lot, sv, vol):
        return self.env['madenat.sv.imputation.wizard.sv.line'].sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': self._wline(wiz, lot).id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    # ── SIMPLE-01 / CLIENT-02/03: botonera de dos acciones ────────────────
    def test_simple_01_botonera_dos_acciones(self):
        root = etree.fromstring(self.view.arch.encode())
        header = root.find('.//header')
        names = {b.get('name') for b in header.findall('button')}
        # Botonera: dos acciones de trabajo + Volver + «Volver a borrador»
        # (sólo visible en estado anulado) + «Recargar versión actual» (LOCK,
        # recuperación del conflicto de edición concurrente).
        self.assertEqual(
            names, {'action_prepare', 'action_apply', 'action_discard_changes',
                    'action_wizard_reopen', 'action_reload_current'})
        self.assertIsNone(root.find('.//footer'))
        for btn in header.findall('button'):
            expr = btn.get('invisible') or ''
            self.assertNotIn('wizard_id', expr)
            self.assertNotIn('parent.', expr)

    # ── SIMPLE-02: seleccionar → cantidad → Aplicar (sin Guardar ni Preparar) ─
    def test_simple_02_aplicar_sin_guardar_ni_preparar(self):
        guia = self._guia('SIM-02')
        e = self._etq(guia, 'SIM-02-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM002', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0   # CLIENT-01: inverse
        # No se pulsa «Preparar asignación» ni «Guardar».
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'applied')
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(
            self.Imputation._i2_lot_applied_m3(e), 10.0, 3)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 10.0, 3)
        self.assertIn(imp.name, wiz.apply_result or '')
        self.assertIn('aplicada', wiz.apply_result or '')

    # ── SIMPLE-03: seleccionar → cantidad → Guardar (misma ventana) ──────
    def test_simple_03_guardar_misma_ventana(self):
        guia = self._guia('SIM-03')
        e = self._etq(guia, 'SIM-03-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM003', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        res = wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertEqual(res['res_model'], wiz._name)   # permanece
        self.assertIn(imp.name, wiz.save_result or '')
        self.assertIn('reserva documental', wiz.save_result or '')

    # ── SIMPLE-04: Guardar → salir → Continuar ────────────────────────────
    def test_simple_04_guardar_salir_continuar(self):
        guia = self._guia('SIM-04')
        e = self._etq(guia, 'SIM-04-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM004', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz.unlink()                            # salir
        wiz2 = self._wizard(guia, sv)           # Continuar
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertAlmostEqual(
            self._wline(wiz2, e).cantidad_asignar_m3, 4.0, 3)
        self.assertIn(imp, self.Imputation.search(
            [('work_sv_lot_id', '=', sv.id)]))

    # ── SIMPLE-05: borrador → Aplicar desde el asistente (sin Abrir) ──────
    def test_simple_05_borrador_aplicar_sin_abrir(self):
        guia = self._guia('SIM-05')
        e = self._etq(guia, 'SIM-05-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM005', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 6.0
        wiz.action_prepare()                    # borrador
        imp = wiz.imputation_id
        res = wiz.with_user(self.user_oper).action_apply()  # sin «Abrir documento»
        self.assertEqual(wiz.imputation_id, imp)
        self.assertEqual(imp.state, 'applied')
        self.assertEqual(res['res_model'], wiz._name)

    # ── SIMPLE-06/07: repetir Guardar/Aplicar no duplica ──────────────────
    def test_simple_06_07_repetir_no_duplica(self):
        guia = self._guia('SIM-07')
        e = self._etq(guia, 'SIM-07-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM007', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 5.0
        wiz.action_prepare()
        wiz.action_prepare()                    # repetir Guardar
        imp = wiz.imputation_id
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)
        wiz.with_user(self.user_oper).action_apply()
        wiz.with_user(self.user_oper).action_apply()   # repetir Aplicar
        self.assertEqual(imp.state, 'applied')
        # El REPARTO al SV (5 m³) se aplicó una sola vez (el nominal de la
        # etiqueta es 10; «applied» etiqueta-side = nominal, por diseño).
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 5.0, 3)
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(imp.imputed_total_m3, 5.0, 3)

    # ── SIMPLE-08: cero guarda (draft) pero no aplica ─────────────────────
    def test_simple_08_cero_guarda_no_aplica(self):
        guia = self._guia('SIM-08')
        e = self._etq(guia, 'SIM-08-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM008', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()            # fila a 0.0
        wiz.action_prepare()                    # permitido (no aplica)
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.sv_line_ids)
        with self.assertRaises(UserError) as cm:
            wiz.with_user(self.user_oper).action_apply()
        self.assertIn('Indica los m³', str(cm.exception))
        self.assertEqual(imp.state, 'draft')    # sin efecto parcial

    # ── SIMPLE-09: negativo/exceso ⇒ rechazo claro, sin efectos ───────────
    def test_simple_09_negativo_y_exceso(self):
        guia = self._guia('SIM-09')
        e = self._etq(guia, 'SIM-09-E', 5.0)
        sv = self._sv(guia, 'SV0000SIM009', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        row = self._alloc(wiz, e, sv, -1.0)
        with self.assertRaises(UserError):
            wiz._i2_build_imputation()          # negativo
        row.imputed_volume_m3 = 6.0             # exceso > nominal 5
        with self.assertRaises(ValidationError):
            wiz._i2_build_imputation()
        self.assertFalse(self.Imputation.search(
            [('guia_processing_id', '=', guia.id)]))

    # ── SIMPLE-10: sin disponibilidad ⇒ causa concreta ────────────────────
    def test_simple_10_sin_disponibilidad(self):
        guia = self._guia('SIM-10')
        e = self._etq(guia, 'SIM-10-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM010', 100.0)
        d1 = self._wizard(guia, sv)
        self._wline(d1, e).selected = True
        self._wline(d1, e).cantidad_asignar_m3 = 10.0
        d1.with_user(self.user_oper).action_apply()      # consume la etiqueta
        wiz = self._wizard(guia, sv)                     # nueva operación
        line = self._wline(wiz, e)
        self.assertLessEqual(line.etiqueta_disponible_m3, 0.0)
        line.selected = True
        with self.assertRaises(UserError) as cm:
            wiz.with_user(self.user_oper).action_apply()
        self.assertIn('no tienen disponibilidad', str(cm.exception))

    # ── SIMPLE-11: repartos a otros SV se conservan ───────────────────────
    def test_simple_11_otros_sv_se_conservan(self):
        guia = self._guia('SIM-11')
        e = self._etq(guia, 'SIM-11-E', 10.0)
        sv1 = self._sv(guia, 'SV0000SIM011A', 100.0)
        sv2 = self._sv(guia, 'SV0000SIM011B', 100.0)
        wiz = self._wizard(guia, sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 4.0)
        self._alloc(wiz, e, sv2, 3.0)
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv1)          # continuar; cero en SV trabajo
        self._wline(wiz2, e).cantidad_asignar_m3 = 0.0
        wiz2.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertEqual(imp.sv_line_ids.sv_lot_id, sv2)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 3.0, 3)

    # ── SIMPLE-12: «Usar disponible» no sobrescribe lo editado ────────────
    def test_simple_12_usar_disponible_no_sobrescribe(self):
        guia = self._guia('SIM-12')
        e1 = self._etq(guia, 'SIM-12-E1', 10.0)
        e2 = self._etq(guia, 'SIM-12-E2', 10.0)
        sv = self._sv(guia, 'SV0000SIM012', 100.0)
        wiz = self._wizard(guia, sv)
        for e in (e1, e2):
            self._wline(wiz, e).selected = True
        wiz.action_assign_selected()            # 2 filas a 0
        self._wline(wiz, e1).cantidad_asignar_m3 = 7.0
        wiz.action_use_available()
        self.assertAlmostEqual(
            self._wline(wiz, e1).cantidad_asignar_m3, 7.0, 3)   # intacto
        self.assertAlmostEqual(
            self._wline(wiz, e2).cantidad_asignar_m3, 10.0, 3)  # rellenado

    # ── SIMPLE-13: descartar cambios posteriores conserva el guardado ─────
    def test_simple_13_descartar_conserva_guardado(self):
        guia = self._guia('SIM-13')
        e = self._etq(guia, 'SIM-13-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM013', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e).cantidad_asignar_m3 = 9.0
        wiz2.unlink()                           # descartar
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)

    # ── SIMPLE-14: tras aplicar, resultado y bloqueo de edición ───────────
    def test_simple_14_resultado_y_bloqueo(self):
        guia = self._guia('SIM-14')
        e = self._etq(guia, 'SIM-14-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM014', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.with_user(self.user_oper).action_apply()
        self.assertEqual(wiz.imputation_state, 'applied')
        self.assertIn('aplicada', wiz.apply_result or '')
        self.assertIn('10.000 m³', wiz.apply_result or '')
        # Las tablas quedan en sólo lectura al aplicado.
        self.assertIn('readonly="imputation_state in', self.view.arch)

    # ── SIMPLE-15: permisos y compañía (sin sudo) ─────────────────────────
    def test_simple_15_permisos_y_compania(self):
        guia = self._guia('SIM-15')
        e = self._etq(guia, 'SIM-15-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM015', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        plain = self.env['res.users'].create({
            'name': 'sim_plain', 'login': 'sim_plain',
            'email': 'sim_plain@madenat.cl', 'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            imp.with_user(plain).read(['name'])
        with self.assertRaises(AccessError):
            wiz.with_user(plain).action_apply()
        self.assertEqual(imp.state, 'draft')
        c_b = self.env['res.company'].sudo().create({'name': 'SIM B'})
        u_b = self.env['res.users'].create({
            'name': 'sim_b', 'login': 'sim_b', 'email': 'sim_b@madenat.cl',
            'company_id': c_b.id, 'company_ids': [(6, 0, [c_b.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        self.assertNotIn(imp.id, self.Imputation.with_user(u_b).search([]).ids)

    # ── SIMPLE-16: aplicar → revertir → nueva → aplicar ───────────────────
    def test_simple_16_cadena_reversion(self):
        guia = self._guia('SIM-16')
        e = self._etq(guia, 'SIM-16-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM016', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id
        imp.reversal_reason = 'SIM-16 reversa.'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_available_for_m3(e), 10.0, 3)
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e).cantidad_asignar_m3 = 6.0
        wiz2.with_user(self.user_oper).action_apply()
        imp2 = wiz2.imputation_id
        self.assertNotEqual(imp2, imp)
        self.assertEqual(imp2.state, 'applied')
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'reversed')

    # ── SIMPLE-17: sin efectos físicos ────────────────────────────────────
    def test_simple_17_sin_efectos_fisicos(self):
        def snap():
            return (
                self.env['stock.move'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.move.line'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.picking'].search_count(
                    [('company_id', '=', self.company.id)]))
        before = snap()
        guia = self._guia('SIM-17')
        e = self._etq(guia, 'SIM-17-E', 10.0)
        sv = self._sv(guia, 'SV0000SIM017', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        wiz.with_user(self.user_oper).action_apply()
        self.assertEqual(snap(), before)

    # ── CLIENT-01: la cantidad editada llega al reparto sin salir de pestaña ─
    def test_client_01_cantidad_editada_al_reparto(self):
        guia = self._guia('SIM-CLI')
        e = self._etq(guia, 'SIM-CLI-E', 10.0)
        sv = self._sv(guia, 'SV0000SIMCLI', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0   # pestaña Materiales
        allocs = wiz.sv_line_ids.filtered(lambda a: a.sv_lot_id == sv)
        self.assertEqual(len(allocs), 1)
        self.assertAlmostEqual(allocs.imputed_volume_m3, 4.0, 3)
