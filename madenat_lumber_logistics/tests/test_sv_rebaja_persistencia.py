# -*- coding: utf-8 -*-
"""Persistencia y recuperación del trabajo de rebaja (SAVE/FLOW/PHY, 2026-10-11).

Cubre la incidencia «al preparar las asignaciones, estas no van quedando
guardadas»: el flujo **preparar → introducir cantidades → guardar borrador →
salir → localizar desde el SV → continuar**, sin aplicar la rebaja.

Causa corregida (SAVE-05): «Guardar borrador» fallaba con `UserError` si existía
alguna fila de reparto con cantidad 0 (las que crea «Preparar asignación»). Ahora
el destino previsto sin cantidad **no bloquea** el guardado (se conserva la
etiqueta/línea; no se persiste un reparto inválido).

Datos 100 % transaccionales (TransactionCase, rollback).
"""
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaPersistencia(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SAVE Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'SAVE Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'sav_oper', 'login': 'sav_oper',
            'email': 'sav_oper@madenat.cl', 'company_id': cls.company.id,
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

    def _found_from_sv(self, sv):
        """Dominio real de descubrimiento del SV (``action_open_sv_rebajas``)."""
        action = sv.action_open_sv_rebajas()
        return self.Imputation.search(action['domain'])

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-01: preparar → cantidad → guardar ⇒ persistente
    # ══════════════════════════════════════════════════════════════════════
    def test_save_01_preparar_cantidad_guardar(self):
        guia = self._guia('SAVE-01')
        e = self._etq(guia, 'SAVE-01-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE01', 100.0)
        wiz = self._wizard(guia, sv)
        wl = self._wline(wiz, e)
        wl.selected = True
        wiz.action_assign_selected()
        wl.cantidad_asignar_m3 = 4.0          # pestaña Materiales (inverse)
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(imp.work_sv_lot_id, sv)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)
        imp.invalidate_recordset()            # releído de base, no caché
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)
        self.assertEqual(imp.sv_line_ids.sv_lot_id, sv)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-02: salir → localizar desde el SV → reabrir
    # ══════════════════════════════════════════════════════════════════════
    def test_save_02_localizar_y_reabrir(self):
        guia = self._guia('SAVE-02')
        e = self._etq(guia, 'SAVE-02-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE02', 100.0)
        wiz = self._wizard(guia, sv)
        wl = self._wline(wiz, e)
        wl.selected = True
        wiz.action_assign_selected()
        wl.cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertIn(imp, self._found_from_sv(sv))
        wiz2 = self._wizard(guia, sv)          # nuevo asistente = nueva sesión
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.line_ids), 1)
        self.assertEqual(len(wiz2.sv_line_ids), 1)
        self.assertAlmostEqual(
            self._wline(wiz2, e).cantidad_asignar_m3, 4.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-03: modificar borrador → guardar ⇒ actualiza, no duplica
    # ══════════════════════════════════════════════════════════════════════
    def test_save_03_modificar_actualiza_sin_duplicar(self):
        guia = self._guia('SAVE-03')
        e = self._etq(guia, 'SAVE-03-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE03', 100.0)
        wiz = self._wizard(guia, sv)
        wl = self._wline(wiz, e)
        wl.selected = True
        wiz.action_assign_selected()
        wl.cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        # Continuar el MISMO trabajo y cambiar la cantidad.
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e).cantidad_asignar_m3 = 6.0
        wiz2.action_prepare()
        self.assertEqual(wiz2.imputation_id, imp)      # mismo documento
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 6.0, 3)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-04: guardar dos veces ⇒ sin duplicados ni efectos adicionales
    # ══════════════════════════════════════════════════════════════════════
    def test_save_04_guardar_dos_veces(self):
        guia = self._guia('SAVE-04')
        e = self._etq(guia, 'SAVE-04-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE04', 100.0)
        wiz = self._wizard(guia, sv)
        wl = self._wline(wiz, e)
        wl.selected = True
        wiz.action_assign_selected()
        wl.cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        writed_before = imp.write_date
        wiz.action_prepare()                   # reintento del MISMO asistente
        self.assertEqual(wiz.imputation_id, imp)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)
        self.assertEqual(imp.state, 'draft')
        self.assertTrue(writed_before)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-05: trabajo incompleto y cantidad cero ⇒ se guarda sin error
    # ══════════════════════════════════════════════════════════════════════
    def test_save_05_cantidad_cero_guarda_sin_error(self):
        guia = self._guia('SAVE-05')
        e1 = self._etq(guia, 'SAVE-05-E1', 10.0)
        e2 = self._etq(guia, 'SAVE-05-E2', 7.0)
        sv = self._sv(guia, 'SV0000SAVE05', 100.0)
        wiz = self._wizard(guia, sv)
        for e in (e1, e2):
            self._wline(wiz, e).selected = True
        wiz.action_assign_selected()           # 2 filas a 0.0
        self._wline(wiz, e1).cantidad_asignar_m3 = 3.0   # sólo una con cantidad
        wiz.action_prepare()                   # NO debe fallar
        imp = wiz.imputation_id
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'draft')
        # Se conservan AMBAS etiquetas (selección) y sólo el reparto positivo.
        self.assertEqual(len(imp.line_ids), 2)
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 3.0, 3)
        # Descubrible desde el SV aunque el doc no tuviera reparto alguno.
        self.assertIn(imp, self._found_from_sv(sv))

    def _alloc(self, wiz, lot, sv, vol):
        return self.env['madenat.sv.imputation.wizard.sv.line'].sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': self._wline(wiz, lot).id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-06: dos SV con repartos ⇒ conservación completa y subtotal
    # ══════════════════════════════════════════════════════════════════════
    def test_save_06_dos_sv_conservacion(self):
        guia = self._guia('SAVE-06')
        e = self._etq(guia, 'SAVE-06-E', 10.0)
        sv1 = self._sv(guia, 'SV0000SAVE06A', 100.0)
        sv2 = self._sv(guia, 'SV0000SAVE06B', 100.0)
        wiz = self._wizard(guia, sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 4.0)
        self._alloc(wiz, e, sv2, 3.0)
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertEqual(len(imp.sv_line_ids), 2)
        self.assertAlmostEqual(imp.imputed_total_m3, 7.0, 3)
        # Descubrible desde AMBOS destinos, sin duplicarse.
        self.assertIn(imp, self._found_from_sv(sv1))
        self.assertIn(imp, self._found_from_sv(sv2))

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-07: poner a cero sólo el SV de trabajo ⇒ otros repartos intactos
    # ══════════════════════════════════════════════════════════════════════
    def test_save_07_cero_solo_en_sv_de_trabajo(self):
        guia = self._guia('SAVE-07')
        e = self._etq(guia, 'SAVE-07-E', 10.0)
        sv1 = self._sv(guia, 'SV0000SAVE07A', 100.0)
        sv2 = self._sv(guia, 'SV0000SAVE07B', 100.0)
        wiz = self._wizard(guia, sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 4.0)
        self._alloc(wiz, e, sv2, 3.0)
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv1)         # continuar y cero en SV trabajo
        self._wline(wiz2, e).cantidad_asignar_m3 = 0.0
        wiz2.action_prepare()
        imp.invalidate_recordset()
        allocs = imp.sv_line_ids
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs.sv_lot_id, sv2)
        self.assertAlmostEqual(allocs.imputed_volume_m3, 3.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-08: descartar cambios posteriores ⇒ el último guardado permanece
    # ══════════════════════════════════════════════════════════════════════
    def test_save_08_descartar_cambios(self):
        guia = self._guia('SAVE-08')
        e = self._etq(guia, 'SAVE-08-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE08', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv)          # cambiar sin guardar y descartar
        self._wline(wiz2, e).cantidad_asignar_m3 = 9.0
        wiz2.unlink()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-09: limpieza del transitorio ⇒ documento persistente recuperable
    # ══════════════════════════════════════════════════════════════════════
    def test_save_09_transitorio_limpiado_recuperable(self):
        guia = self._guia('SAVE-09')
        e = self._etq(guia, 'SAVE-09-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE09', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz.unlink()                           # limpieza del TransientModel
        self.assertTrue(imp.exists())
        self.assertIn(imp, self._found_from_sv(sv))
        wiz2 = self._wizard(guia, sv)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.sv_line_ids), 1)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-10: fallo intermedio ⇒ atomicidad y borrador previo conservado
    # ══════════════════════════════════════════════════════════════════════
    def test_save_10_fallo_intermedio_atomico(self):
        guia = self._guia('SAVE-10')
        e = self._etq(guia, 'SAVE-10-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE10', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv)
        self._wline(wiz2, e).cantidad_asignar_m3 = 5.0
        guia.sudo().write({'service_return_confirmation': 'no'})  # rompe guía
        with self.assertRaises(UserError):
            wiz2.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-11: usuario sin permiso y otra compañía (sin sudo)
    # ══════════════════════════════════════════════════════════════════════
    def test_save_11_permisos_y_compania(self):
        guia = self._guia('SAVE-11')
        e = self._etq(guia, 'SAVE-11-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE11', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        # Usuario interno SIN grupos MADENAT: sin ACL ⇒ AccessError.
        plain = self.env['res.users'].create({
            'name': 'sav_plain', 'login': 'sav_plain',
            'email': 'sav_plain@madenat.cl', 'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            imp.with_user(plain).read(['name'])
        # Otra compañía: bloqueado por la regla de registro (sin sudo).
        company_b = self.env['res.company'].sudo().create({'name': 'SAVE B'})
        user_b = self.env['res.users'].create({
            'name': 'sav_b', 'login': 'sav_b', 'email': 'sav_b@madenat.cl',
            'company_id': company_b.id, 'company_ids': [(6, 0, [company_b.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        self.assertNotIn(imp.id, self.Imputation.with_user(user_b).search([]).ids)
        with self.assertRaises(AccessError):
            imp.with_user(user_b).read(['name'])

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-12: dos sesiones sobre el mismo borrador ⇒ sin duplicación y, con el
    # BLINDAJE DE BORRADORES (LOCK, 2026-10-12), se rechaza la edición OBSOLETA
    # (ya no aplica «última escritura gana»).
    # ══════════════════════════════════════════════════════════════════════
    def test_save_12_dos_sesiones_sin_duplicar(self):
        guia = self._guia('SAVE-12')
        e = self._etq(guia, 'SAVE-12-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE12', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        # Dos sesiones sobre el mismo borrador. Política APROBADA por Mauricio:
        # la sesión con versión OBSOLETA se RECHAZA; no se sobrescribe ni fusiona.
        s1 = self._wizard(guia, sv)
        s2 = self._wizard(guia, sv)
        self.assertEqual(s1.imputation_id, s2.imputation_id)
        self._wline(s1, e).cantidad_asignar_m3 = 4.0
        s1.action_prepare()
        self._wline(s2, e).cantidad_asignar_m3 = 7.0
        with self.assertRaises(UserError):
            s2.action_prepare()                          # edición obsoleta
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)   # sin duplicar
        imp.invalidate_recordset()
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-13: un documento aplicado NO se reabre como borrador editable
    # ══════════════════════════════════════════════════════════════════════
    def test_save_13_aplicado_no_reabre_como_borrador(self):
        guia = self._guia('SAVE-13')
        e = self._etq(guia, 'SAVE-13-E', 10.0)
        sv = self._sv(guia, 'SV0000SAVE13', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(UserError):
            imp.action_continue_preparation()
        wiz2 = self._wizard(guia, sv)          # no reutiliza el aplicado
        self.assertFalse(wiz2.imputation_id)
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'applied')

    # ══════════════════════════════════════════════════════════════════════
    # SAVE-14: firma vacía / cambios de firma ⇒ sin colisión ni reutilización
    # ══════════════════════════════════════════════════════════════════════
    def test_save_14_firma_sin_colision(self):
        guia1 = self._guia('SAVE-14-A')
        e1 = self._etq(guia1, 'SAVE-14-E1', 10.0)
        sv1 = self._sv(guia1, 'SV0000SAVE14A', 100.0)
        wiz1 = self._wizard(guia1, sv1)
        self._wline(wiz1, e1).selected = True
        wiz1.action_prepare()                  # firma VACÍA (sin reparto)
        imp1 = wiz1.imputation_id
        self.assertEqual(imp1.state, 'draft')
        self.assertFalse(imp1.sv_line_ids)
        guia2 = self._guia('SAVE-14-B')
        e2 = self._etq(guia2, 'SAVE-14-E2', 10.0)
        sv2 = self._sv(guia2, 'SV0000SAVE14B', 100.0)
        wiz2 = self._wizard(guia2, sv2)
        self._wline(wiz2, e2).selected = True
        wiz2.action_prepare()
        imp2 = wiz2.imputation_id
        self.assertNotEqual(imp1.documentary_key, imp2.documentary_key)
        # Cambiar la firma del MISMO trabajo NO crea otro documento.
        wiz3 = self._wizard(guia1, sv1)
        self._wline(wiz3, e1).cantidad_asignar_m3 = 5.0
        wiz3.action_prepare()
        self.assertEqual(wiz3.imputation_id, imp1)
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia1.id)]), 1)

    # ══════════════════════════════════════════════════════════════════════
    # FLOW-01: guardar → reabrir → aplicar → consultar resultado
    # ══════════════════════════════════════════════════════════════════════
    def test_flow_01_guardar_reabrir_aplicar(self):
        guia = self._guia('FLOW-01')
        e = self._etq(guia, 'FLOW-01-E', 10.0)
        sv = self._sv(guia, 'SV0000FLOW01', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        wiz2 = self._wizard(guia, sv)
        self.assertEqual(wiz2.imputation_id, imp)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_applied_m3(e), 10.0, 3)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 10.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # FLOW-02: cancelar borrador ⇒ reservas y trazabilidad
    # ══════════════════════════════════════════════════════════════════════
    def test_flow_02_cancelar_borrador(self):
        guia = self._guia('FLOW-02')
        e = self._etq(guia, 'FLOW-02-E', 10.0)
        sv = self._sv(guia, 'SV0000FLOW02', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertAlmostEqual(
            self.Imputation._i2_lot_available_for_m3(e), 0.0, 3)  # reservado
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_available_for_m3(e), 10.0, 3)  # liberado
        with self.assertRaises(UserError):
            imp.action_continue_preparation()

    # ══════════════════════════════════════════════════════════════════════
    # FLOW-03: aplicar → revertir → reasignar → guardar → reabrir → aplicar
    # ══════════════════════════════════════════════════════════════════════
    def test_flow_03_cadena_completa(self):
        guia = self._guia('FLOW-03')
        e = self._etq(guia, 'FLOW-03-E', 10.0)
        sv = self._sv(guia, 'SV0000FLOW03', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_apply()
        imp.reversal_reason = 'FLOW-03 reversa.'
        imp.with_user(self._jef()).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        wiz2 = self._wizard(guia, sv)          # reasignar + guardar + reabrir
        self._wline(wiz2, e).cantidad_asignar_m3 = 6.0
        wiz2.action_prepare()
        imp2 = wiz2.imputation_id
        self.assertNotEqual(imp2, imp)
        wiz3 = self._wizard(guia, sv)
        self.assertEqual(wiz3.imputation_id, imp2)
        imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp2.state, 'applied')
        self.assertAlmostEqual(imp2.imputed_total_m3, 6.0, 3)
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'reversed')

    def _jef(self):
        return self.env['res.users'].create({
            'name': 'sav_jef', 'login': 'sav_jef',
            'email': 'sav_jef@madenat.cl', 'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_jefatura_operaciones'
                ).id])]})

    # ══════════════════════════════════════════════════════════════════════
    # PHY-01: guardar y recuperar no provoca efectos físicos
    # ══════════════════════════════════════════════════════════════════════
    def test_phy_01_guardar_recuperar_sin_efectos_fisicos(self):
        def snap():
            return (
                self.env['stock.move'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.move.line'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.picking'].search_count(
                    [('company_id', '=', self.company.id)]))
        before = snap()
        guia = self._guia('PHY-01')
        e = self._etq(guia, 'PHY-01-E', 10.0)
        sv = self._sv(guia, 'SV0000PHY01', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        self._wizard(guia, sv)                 # reabrir (recuperar)
        self.assertEqual(snap(), before)
