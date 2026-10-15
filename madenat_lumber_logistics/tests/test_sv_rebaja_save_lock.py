# -*- coding: utf-8 -*-
"""BLINDAJE DE BORRADORES — protección contra sobrescritura concurrente (LOCK).

Contrato (aprobado por Mauricio, 2026-10-12): una edición basada en una versión
obsoleta del documento de rebaja se **rechaza de forma controlada**; nunca se
sobrescribe ni se fusiona trabajo ajeno. La versión (`edit_version`) pertenece al
documento persistente; el asistente la captura al abrir y Guardar/Aplicar la
comparan de forma atómica (advisory lock del documento + comparación + flush).

Datos 100 % transaccionales (TransactionCase, rollback).
"""
import threading

from unittest.mock import patch

from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase, TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSaveLock(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'LOCK Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'LOCK Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.user_oper = cls._mk('lock_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_oper2 = cls._mk('lock_oper2', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('lock_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.cl' % name,
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    # ── Helpers ───────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})

    def _etq(self, guia, name, nominal=10.0):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal=100.0):
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

    def _fixture(self, name):
        guia = self._guia(name)
        etq = self._etq(guia, name + '-E')
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:16].ljust(16, '0'))
        return guia, etq, sv

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-01 — dos sesiones no se sobrescriben
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_01_dos_sesiones_no_se_sobrescriben(self):
        guia, etq, sv = self._fixture('LOCK01')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        v1 = imp.edit_version
        # B abre DESPUÉS: captura la versión vigente y reconstruye el reparto.
        wiz_b = self._wizard(guia, sv)
        self.assertEqual(wiz_b.imputation_id, imp)
        self.assertEqual(wiz_b.expected_edit_version, v1)
        self.assertAlmostEqual(
            self._wline(wiz_b, etq).cantidad_asignar_m3, 4.0, 3)
        # A modifica y guarda (sube la versión).
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 7.0
        wiz_a.action_prepare()
        imp.invalidate_recordset()
        v2 = imp.edit_version
        self.assertGreater(v2, v1)
        # B intenta guardar desde su versión OBSOLETA → conflicto controlado.
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 2.0
        with self.assertRaises(UserError) as cm:
            wiz_b.action_prepare()
        self.assertIn('cambió desde que lo abriste', str(cm.exception))
        # Datos de A INTACTOS: sin sobrescritura ni fusión.
        imp.invalidate_recordset()
        self.assertEqual(imp.edit_version, v2)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 7.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-02 — Guardar vs Aplicar
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_02_guardar_frente_a_aplicar(self):
        guia, etq, sv = self._fixture('LOCK02')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 8.0
        wiz_a.action_prepare()
        with self.assertRaises(UserError) as cm:
            wiz_b.with_user(self.user_oper).action_apply()
        self.assertIn('cambió desde que lo abriste', str(cm.exception))
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')          # no se aplicó
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 8.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-03 — Aplicado no editable
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_03_aplicado_intacto(self):
        guia, etq, sv = self._fixture('LOCK03')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 5.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        wiz_b = self._wizard(guia, sv)                # B abre en borrador (v vigente)
        wiz_a.with_user(self.user_oper).action_apply()  # A aplica
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(UserError):
            wiz_b.action_prepare()                    # B no edita lo aplicado
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 5.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-04 — mismo usuario, dos asistentes
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_04_mismo_usuario_dos_asistentes(self):
        guia, etq, sv = self._fixture('LOCK04')
        u = self.user_oper
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.with_user(u).action_prepare()
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 9.0
        wiz_a.with_user(u).action_prepare()
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 1.0
        with self.assertRaises(UserError):
            wiz_b.with_user(u).action_prepare()
        imps = self.Imputation.search([('guia_processing_id', '=', guia.id)])
        self.assertEqual(len(imps), 1)
        self.assertAlmostEqual(imps.sv_line_ids.imputed_volume_m3, 9.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-05 — usuarios distintos autorizados
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_05_usuarios_distintos(self):
        guia, etq, sv = self._fixture('LOCK05')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.with_user(self.user_oper).action_prepare()
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 6.0
        wiz_a.with_user(self.user_jef).action_prepare()
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 2.0
        with self.assertRaises(UserError):
            wiz_b.with_user(self.user_oper2).action_prepare()

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-06 — cambio de LÍNEA hija invalida
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_06_cambio_de_linea_hija(self):
        guia, etq, sv = self._fixture('LOCK06')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        v1 = imp.edit_version
        wiz_b = self._wizard(guia, sv)
        # A escribe la LÍNEA hija directamente (edición directa del documento).
        imp.line_ids.filtered(
            lambda l: l.processed_lot_id == etq).write({'pieces': 3})
        imp.invalidate_recordset()
        self.assertGreater(imp.edit_version, v1)      # el hijo elevó la versión
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 1.0
        with self.assertRaises(UserError):
            wiz_b.action_prepare()

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-07 — eliminación de reparto no se reconstruye desde copia obsoleta
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_07_eliminacion_de_reparto(self):
        guia, etq, sv = self._fixture('LOCK07')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        wiz_b = self._wizard(guia, sv)                # B abre con reparto
        imp.sv_line_ids.unlink()                      # A elimina el reparto
        imp.invalidate_recordset()
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 4.0
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertFalse(imp.sv_line_ids)             # no se reconstruyó

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-08 — dos primeros guardados de la misma guía
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_08_dos_primeros_guardados(self):
        guia, etq, sv = self._fixture('LOCK08')
        wiz_a = self._wizard(guia, sv)                # A sin trabajo → v0
        wiz_b = self._wizard(guia, sv)                # B sin trabajo → v0
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        self._wline(wiz_b, etq).selected = True
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 6.0
        with self.assertRaises(UserError) as cm:
            wiz_b.action_prepare()                    # no adopta lo de A
        self.assertIn('Otra sesión creó un trabajo', str(cm.exception))
        imps = self.Imputation.search([('guia_processing_id', '=', guia.id)])
        self.assertEqual(len(imps), 1)                # sin duplicado
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 4.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-09 — guardado repetido en la misma sesión (sin falso conflicto)
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_09_guardar_repetido(self):
        guia, etq, sv = self._fixture('LOCK09')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        for vol in (2.0, 4.0, 6.0):
            self._wline(wiz, etq).cantidad_asignar_m3 = vol
            wiz.action_prepare()                      # sin excepción
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 6.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-10 — Guardar → Continuar → editar → Guardar
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_10_guardar_continuar_guardar(self):
        guia, etq, sv = self._fixture('LOCK10')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 3.0
        wiz.action_prepare()
        wiz2 = self._wizard(guia, sv)                 # «Continuar»
        self.assertEqual(wiz2.imputation_id, wiz.imputation_id)
        self._wline(wiz2, etq).cantidad_asignar_m3 = 5.0
        wiz2.action_prepare()
        imp = wiz2.imputation_id
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 5.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-11 — chatter/lectura no provoca conflicto
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_11_chatter_no_conflicto(self):
        guia, etq, sv = self._fixture('LOCK11')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        imp.invalidate_recordset()
        v = imp.edit_version
        imp.message_post(body='nota')
        imp.invalidate_recordset()
        self.assertEqual(imp.edit_version, v)         # chatter NO eleva versión
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 5.0
        wiz_b.action_prepare()                        # sin falso conflicto
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 5.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-12 — cancelar externamente → guardar desde asistente
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_12_cancelacion_externa(self):
        guia, etq, sv = self._fixture('LOCK12')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')  # cancelación externa
        imp.invalidate_recordset()
        with self.assertRaises(UserError) as cm:
            wiz.action_prepare()
        self.assertIn('anulado', str(cm.exception))    # mensaje operativo
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-13 — recargar versión vigente
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_13_recargar_versiones_vigentes(self):
        guia, etq, sv = self._fixture('LOCK13')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 7.0
        wiz_a.action_prepare()
        imp.invalidate_recordset()
        wiz_b.action_reload_current()
        wiz_b.invalidate_recordset()
        self.assertEqual(wiz_b.imputation_id, imp)
        self.assertEqual(wiz_b.expected_edit_version, imp.edit_version)
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 6.0
        wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 6.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-14 — el rechazo NO adopta la versión ajena en silencio
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_14_rechazo_no_actualiza_version(self):
        guia, etq, sv = self._fixture('LOCK14')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        wiz_b = self._wizard(guia, sv)
        v_b = wiz_b.expected_edit_version
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 7.0
        wiz_a.action_prepare()
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 2.0
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        wiz_b.invalidate_recordset()
        self.assertEqual(wiz_b.expected_edit_version, v_b)
        # (La conservación de las ediciones EN EL NAVEGADOR se declara como
        #  límite: requiere evidencia de cliente, no sólo ORM.)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-15 — fallo intermedio: rollback de contenido y versión
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_15_fallo_intermedio_rollback(self):
        guia, etq, sv = self._fixture('LOCK15')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        v0 = imp.edit_version
        try:
            with self.env.cr.savepoint():
                imp.line_ids.filtered(
                    lambda l: l.processed_lot_id == etq).write({'pieces': 5})
                raise ValueError('fallo simulado')
        except ValueError:
            pass
        imp.invalidate_recordset()
        self.assertEqual(imp.edit_version, v0)        # rollback íntegro

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-17 — edición frente a transición de estado
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_17_edicion_frente_a_transicion(self):
        guia, etq, sv = self._fixture('LOCK17')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        wiz_b = self._wizard(guia, sv)
        wiz_a.imputation_id.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')
        with self.assertRaises(UserError) as cm:
            wiz_b.with_user(self.user_oper).action_apply()
        self.assertIn('anulado', str(cm.exception))
        imp = wiz_b.imputation_id
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-18 — usuario sin permiso / otra compañía (sin fuga ni bypass)
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_18_usuario_sin_permiso(self):
        guia, etq, sv = self._fixture('LOCK18')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        plain = self._mk('lock_plain', ['base.group_user'])
        with self.assertRaises(AccessError):
            self.Imputation.with_user(plain).search_count([('id', '=', imp.id)])
        company_b = self.env['res.company'].create({'name': 'LOCK Compañía B'})
        user_b = self.env['res.users'].create({
            'name': 'lock_b', 'login': 'lock_b', 'email': 'lockb@madenat.cl',
            'company_id': company_b.id, 'company_ids': [(6, 0, [company_b.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        self.assertEqual(self.Imputation.with_user(user_b).search_count(
            [('id', '=', imp.id)]), 0)

    # ══════════════════════════════════════════════════════════════════════
    # LOCK-19 — la edición DIRECTA del documento también eleva la versión
    # ══════════════════════════════════════════════════════════════════════
    def test_lock_19_edicion_directa_eleva_version(self):
        guia, etq, sv = self._fixture('LOCK19')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        v0 = imp.edit_version
        imp.write({'reason': 'edición directa'})      # cabecera directa
        imp.invalidate_recordset()
        self.assertGreater(imp.edit_version, v0)
        v1 = imp.edit_version
        imp.sv_line_ids.write({'imputed_volume_m3': 3.0})   # reparto directo
        imp.invalidate_recordset()
        self.assertGreater(imp.edit_version, v1)

    # ══════════════════════════════════════════════════════════════════════
    # FLOW-01/02 — recorrido sencillo y Aplicar sin Guardar previo
    # ══════════════════════════════════════════════════════════════════════
    def test_flow_01_02_recorrido_sencillo(self):
        guia, etq, sv = self._fixture('FLOW01')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()                          # Guardar
        self.assertTrue(wiz.imputation_id)
        self.assertAlmostEqual(
            wiz.imputation_id.sv_line_ids.imputed_volume_m3, 4.0, 3)
        guia2, etq2, sv2 = self._fixture('FLOW02')
        wiz2 = self._wizard(guia2, sv2)
        self._wline(wiz2, etq2).selected = True
        self._wline(wiz2, etq2).cantidad_asignar_m3 = 3.0
        wiz2.with_user(self.user_oper).action_apply()  # sin Guardar previo
        imp2 = wiz2.imputation_id
        imp2.invalidate_recordset()
        self.assertEqual(imp2.state, 'applied')

    # ══════════════════════════════════════════════════════════════════════
    # FLOW-03 — Multi-SV conserva destinos no editados
    # ══════════════════════════════════════════════════════════════════════
    def test_flow_03_multi_sv_conserva_destinos(self):
        guia = self._guia('FLOW03')
        etq = self._etq(guia, 'FLOW03-E')
        sv1 = self._sv(guia, 'SV0000FLOW03A')
        sv2 = self._sv(guia, 'SV0000FLOW03B')
        wiz = self._wizard(guia, sv1)
        wl = self._wline(wiz, etq)
        wl.selected = True
        SvWizLine = self.env['madenat.sv.imputation.wizard.sv.line']
        SvWizLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv1.id, 'imputed_volume_m3': 4.0})
        SvWizLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv2.id, 'imputed_volume_m3': 3.0})
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        self.assertEqual(len(imp.sv_line_ids), 2)
        self.assertEqual(
            set(imp.sv_line_ids.mapped('sv_lot_id').ids), {sv1.id, sv2.id})

    # ══════════════════════════════════════════════════════════════════════
    # PHY-01 — sin movimientos físicos de stock
    # ══════════════════════════════════════════════════════════════════════
    def test_phy_01_sin_movimientos_fisicos(self):
        def snap():
            return (
                self.env['stock.move'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.move.line'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.picking'].search_count(
                    [('company_id', '=', self.company.id)]))
        before = snap()
        guia, etq, sv = self._fixture('PHY01')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.with_user(self.user_oper).action_apply()
        self.assertEqual(snap(), before)

    # ══════════════════════════════════════════════════════════════════════
    # REPRO — el DEFECTO original («la última escritura gana»)
    # ══════════════════════════════════════════════════════════════════════
    def test_repro_defecto_last_write_wins(self):
        """Reproduce la causa raíz: SIN la comprobación de versión (neutralizada
        aquí), la segunda sesión sobrescribe en silencio. Confirma que la
        protección es lo que impide el defecto (LOCK-01 lo acredita con la
        comprobación activa)."""
        guia, etq, sv = self._fixture('REPRO')
        wiz_a = self._wizard(guia, sv)
        self._wline(wiz_a, etq).selected = True
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 4.0
        wiz_a.action_prepare()
        imp = wiz_a.imputation_id
        wiz_b = self._wizard(guia, sv)
        self._wline(wiz_a, etq).cantidad_asignar_m3 = 7.0
        wiz_a.action_prepare()
        with patch.object(type(imp), '_i2_assert_edit_version',
                          lambda self, expected: None):
            self._wline(wiz_b, etq).cantidad_asignar_m3 = 2.0
            wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 2.0, 3)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSaveLockConcurrency(SingleTransactionCase):
    """LOCK-16 — concurrencia REAL: dos guardados con barrera/eventos.

    El guard del documento (advisory lock de transacción + comparación de
    versión) es ATÓMICO: una segunda transacción que compite por el mismo
    documento es rechazada de forma controlada (sin sobrescritura parcial)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'LOCK16 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'LOCK16 Supplier', 'is_company': True})
        cls._imp_ids = []
        cls._lot_ids = []
        cls._guia_ids = []
        cls._product_ids = [cls.product.id]
        cls._partner_ids = [cls.supplier.id]

    @classmethod
    def tearDownClass(cls):
        cls._cleanup()
        super().tearDownClass()

    @classmethod
    def _cleanup(cls):
        try:
            cr = cls.env.cr
            if cls._imp_ids:
                cr.execute(
                    'DELETE FROM madenat_sv_imputation WHERE id = ANY(%s)',
                    (cls._imp_ids,))
            if cls._lot_ids:
                cr.execute('DELETE FROM stock_lot WHERE id = ANY(%s)',
                           (cls._lot_ids,))
            if cls._guia_ids:
                cr.execute(
                    'DELETE FROM madenat_guia_processing WHERE id = ANY(%s)',
                    (cls._guia_ids,))
            if cls._product_ids:
                cr.execute(
                    'DELETE FROM product_template WHERE id IN (SELECT '
                    'product_tmpl_id FROM product_product WHERE id = ANY(%s))',
                    (cls._product_ids,))
                cr.execute('DELETE FROM product_product WHERE id = ANY(%s)',
                           (cls._product_ids,))
            if cls._partner_ids:
                cr.execute('DELETE FROM res_partner WHERE id = ANY(%s)',
                           (cls._partner_ids,))
            cr.commit()
        except Exception:  # pragma: no cover
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._imp_ids = []
            cls._lot_ids = []
            cls._guia_ids = []

    def _draft(self, name):
        guia = self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})
        self._guia_ids.append(guia.id)
        etq = self.env['stock.lot'].sudo().create({
            'name': name + '-E', 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': 10.0})
        self._lot_ids.append(etq.id)
        guia.sudo().write({'lot_ids': [(4, etq.id)]})
        sv = self.env['stock.lot'].sudo().create({
            'name': 'SV' + name.replace('-', '')[:16].ljust(16, '0'),
            'product_id': self.product.id, 'company_id': self.company.id,
            'lot_flow_type': 'volume', 'volume_source_guia_id': guia.id,
            'volume_purchase_m3': 100.0})
        self._lot_ids.append(sv.id)
        wiz = self.env['madenat.sv.imputation.wizard'].sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        wline = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        wline.selected = True
        wline.cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self._imp_ids.append(imp.id)
        self.cr.commit()
        return imp

    def test_lock_16_dos_guardados_concurrentes(self):
        imp = self._draft('LOCK16')
        v = imp.edit_version
        result = {}
        ready = threading.Event()
        start = threading.Event()
        done = threading.Event()

        def _txn():
            cr = None
            try:
                conn = db_connect(self.env.cr.dbname)
                cr = conn.cursor()
                cr.transaction = api.Transaction(self.registry)
                env = api.Environment(cr, self.env.uid, {})
                doc = env['madenat.sv.imputation'].browse(imp.id)
                ready.set()
                if not start.wait(timeout=30):
                    return
                try:
                    doc._i2_assert_edit_version(v)
                    result['ok'] = True
                except UserError as error:
                    result['ok'] = False
                    result['error'] = str(error)
                cr.rollback()
            except Exception as error:  # pragma: no cover
                result['thread_error'] = '%s: %s' % (
                    type(error).__name__, error)
            finally:
                if cr is not None:
                    try:
                        cr.close()
                    except Exception:
                        pass
                done.set()

        thread = threading.Thread(target=_txn, daemon=True)
        thread.start()
        try:
            self.assertTrue(ready.wait(timeout=30), 'B no se preparó')
            # A (cursor principal) adquiere y MANTIENE el guard del documento.
            imp._i2_assert_edit_version(v)
            imp.write({'reason': 'A'})
            self.env.flush_all()
            start.set()
            self.assertTrue(done.wait(timeout=30), 'B no terminó')
            thread.join(timeout=30)
            self.cr.commit()
            self.assertNotIn('thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'), 'B no debe adquirir el guard')
            self.assertIn(
                'cambió desde que lo abriste', result.get('error') or '')
            imp.sudo().invalidate_recordset()
            self.assertGreater(imp.edit_version, v)
            self.assertEqual(imp.reason, 'A')
        finally:
            if not done.is_set():
                start.set()
            done.wait(timeout=30)
            thread.join(timeout=30)
            self._cleanup()



