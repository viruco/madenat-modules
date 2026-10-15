# -*- coding: utf-8 -*-
"""FASE 11 — Integridad del ciclo de vida de las imputaciones SV.

Cubre el endurecimiento del ciclo documental de ``madenat.sv.imputation`` tras
la auditoría ``AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015`` (§1.2 y §7):

* **A-1**: ``write()`` público (ORM/RPC) NO cambia ``state`` ni las marcas de
  transición (firma, snapshot, ejecutor, fechas, motivos y metadata de
  anulación/reversa/reapertura). Sólo las acciones oficiales, por la vía privada
  ``_i2_write_protected_state`` (``super().write``).
* **B-1**: ``create()`` no nace en estado terminal ni con marcas fabricadas.
* **M-2b**: una segunda reversa no sobrescribe las marcas de la primera
  («último gana»); la concurrencia real con lock externo vive en
  ``TestSvImputationReverseLocks``.
* **M-4**: la nueva operación sobre una guía con imputación terminal enlaza
  ``origin_imputation_id`` (y la terminal recibe el recíproco al aplicarse).
* **B-2**: líneas y repartos inmutables fuera de ``draft``/``pending``.
* **B-3**: ``action_cancel`` exige motivo y lo registra (metadata + bitácora).

Datos 100 % transaccionales (``TransactionCase``, rollback). NO se tocan
registros históricos (IMP02220/IMP04823).
"""
from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase, TransactionCase

import uuid


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationLifecycleIntegrity(TransactionCase):
    """A-1, B-1, M-2b, M-4, B-2 y B-3 (FASE 11)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'F11 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'F11 Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.user_oper = cls._mk('f11_oper', [
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('f11_jef', [
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = cls._mk('f11_ger', [
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_aud = cls._mk('f11_aud', [
            'madenat_lumber_core.group_madenat_auditoria'])
        cls.user_none = cls._mk('f11_none', [])
        cls._seq = 0

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.test' % name,
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id]
                              + [cls.env.ref(g).id for g in groups])]})


    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.Guia.sudo().create({
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

    def _prepare(self, guia, sv, etq, vol):
        wiz = self._wizard(guia, sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        line.selected = True
        line.cantidad_asignar_m3 = vol
        wiz.action_prepare()
        return wiz.imputation_id

    def _doc(self, tag, state='draft', vol=10.0, sv_name=None):
        """Crea un documento y lo lleva al estado pedido por vías OFICIALES."""
        self._seq += 1
        guia = self._guia('F11-%s' % tag)
        etq = self._etq(guia, 'F11-%s-E' % tag, vol)
        sv = self._sv(guia, sv_name or ('SVF11%05d' % self._seq), 100.0)
        imp = self._prepare(guia, sv, etq, vol)
        if state == 'pending':
            imp.with_user(self.user_oper).action_pending()
        elif state == 'applied':
            imp.with_user(self.user_oper).action_apply()
        elif state == 'reversed':
            imp.with_user(self.user_oper).action_apply()
            imp.with_user(self.user_jef).action_reverse(
                reason='%s: reversa' % tag)
        elif state == 'cancelled':
            imp.with_user(self.user_oper).action_cancel(
                reason='%s: anulación' % tag)
        imp.invalidate_recordset()
        return guia, etq, sv, imp

    def _audit_count(self, imp, action):
        return self.AuditLog.sudo().search_count([
            ('batch_id', '=', imp.documentary_key),
            ('action_type', '=', action)])

    def _msg_count(self, imp):
        return self.env['mail.message'].sudo().search_count([
            ('model', '=', 'madenat.sv.imputation'), ('res_id', '=', imp.id)])


    # ══════════════════════════════════════════════════════════════════════
    # A-1 — la vía pública no fabrica estado ni marcas
    # ══════════════════════════════════════════════════════════════════════
    def test_a1_write_terminal_state_from_draft_blocked(self):
        guia, etq, sv, imp = self._doc('A1A', sv_name='SV0000A1A001')
        docs_before = self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)])
        audit_cancel = self._audit_count(imp, 'imputation_cancel')
        msgs = self._msg_count(imp)
        for bad_state in ('cancelled', 'applied', 'reversed', 'pending'):
            with self.assertRaises(UserError, msg=bad_state):
                imp.write({'state': bad_state})
            with self.assertRaises(UserError, msg=bad_state):
                imp.sudo().write({'state': bad_state})
            with self.assertRaises(UserError, msg=bad_state):
                imp.with_context(i2_transition=True).write(
                    {'state': bad_state})
        imp.invalidate_recordset()
        sv.invalidate_recordset()
        # Estado intacto, sin documento anulado huérfano y sin rastro fabricado.
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.cancelled_by_id)
        self.assertFalse(imp.cancellation_date)
        self.assertFalse(imp.cancellation_reason)
        self.assertFalse(imp.audit_hash)
        self.assertFalse(imp.snapshot_json)
        self.assertFalse(imp.executed_by_id)
        self.assertFalse(imp.execution_date)
        self.assertFalse(imp.reversed_by_id)
        self.assertEqual(self._audit_count(imp, 'imputation_cancel'),
                         audit_cancel)
        self.assertEqual(self._audit_count(imp, 'imputation'), 0)
        self.assertEqual(self._msg_count(imp), msgs)
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 0.0, 3)
        self.assertEqual(sv.sv_assignment_applied_count, 0)
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)]), docs_before)
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id),
             ('state', '=', 'cancelled')]), 0)

    def test_a1b_write_terminal_state_from_pending_blocked(self):
        guia, etq, sv, imp = self._doc(
            'A1B', state='pending', sv_name='SV0000A1B001')
        for bad_state in ('cancelled', 'applied', 'reversed'):
            with self.assertRaises(UserError, msg=bad_state):
                imp.write({'state': bad_state})
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'pending')
        self.assertFalse(imp.audit_hash)
        self.assertFalse(imp.cancelled_by_id)

    def test_a1c_marks_blocked_on_draft(self):
        guia, etq, sv, imp = self._doc('A1C', sv_name='SV0000A1C001')
        bogus = {
            'audit_hash': 'DEADBEEF',
            'snapshot_json': '{"fabricado": true}',
            'executed_by_id': self.user_oper.id,
            'execution_date': '2026-10-15 00:00:00',
            'reversal_reason': 'motivo fabricado',
            'reversal_date': '2026-10-15 00:00:00',
            'reversed_by_id': self.user_oper.id,
            'reversed_imputation_id': imp.id,
            'cancellation_reason': 'motivo fabricado',
            'cancellation_date': '2026-10-15 00:00:00',
            'cancelled_by_id': self.user_oper.id,
            'reopen_reason': 'motivo fabricado',
            'reopen_date': '2026-10-15 00:00:00',
            'reopened_by_id': self.user_oper.id,
        }
        for fname, value in bogus.items():
            with self.assertRaises(UserError, msg=fname):
                imp.write({fname: value})
        imp.invalidate_recordset()
        for fname in bogus:
            self.assertFalse(
                imp[fname], 'La marca %s no debe escribirse por la vía '
                'pública' % fname)
        self.assertEqual(imp.state, 'draft')

    # ══════════════════════════════════════════════════════════════════════
    # B-1 — create() no nace en estado terminal ni con marcas
    # ══════════════════════════════════════════════════════════════════════
    def test_b1_create_rejects_terminal_state_and_marks(self):
        guia = self._guia('F11-B1')
        base = {'guia_processing_id': guia.id}
        for state in ('applied', 'cancelled', 'reversed', 'pending'):
            with self.assertRaises(UserError, msg=state):
                self.Imputation.sudo().create(dict(base, state=state))
        with self.assertRaises(UserError):
            self.Imputation.sudo().create(dict(base, audit_hash='FABRICADA'))
        with self.assertRaises(UserError):
            self.Imputation.sudo().create(dict(
                base, cancellation_reason='fabricado'))
        self.assertFalse(self.Imputation.sudo().search(
            [('guia_processing_id', '=', guia.id)]))
        # Nacer en borrador (explícito o por defecto) sigue permitido.
        ok = self.Imputation.sudo().create(dict(base, state='draft'))
        self.assertEqual(ok.state, 'draft')
        guia2 = self._guia('F11-B1-2')
        ok2 = self.Imputation.sudo().create(
            {'guia_processing_id': guia2.id})
        self.assertEqual(ok2.state, 'draft')

    def test_b1b_wizard_creates_draft_and_is_idempotent(self):
        guia = self._guia('F11-B1B')
        etq = self._etq(guia, 'F11-B1B-E', 10.0)
        sv = self._sv(guia, 'SV0000B1B001', 100.0)
        imp = self._prepare(guia, sv, etq, 4.0)
        self.assertEqual(imp.state, 'draft')
        imp2 = self._prepare(guia, sv, etq, 4.0)
        self.assertEqual(imp2, imp)          # idempotente (mismo borrador)
        self.assertEqual(imp2.state, 'draft')

    # ══════════════════════════════════════════════════════════════════════
    # Caminos oficiales intactos (bitácora, firma y recomputes)
    # ══════════════════════════════════════════════════════════════════════
    def test_official_paths_still_work_with_audit_and_recompute(self):
        guia, etq, sv, imp = self._doc('OFF', sv_name='SV0000OFF001')
        imp.with_user(self.user_oper).action_pending()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'pending')
        imp.with_user(self.user_jef).action_back_to_draft()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        # APLICAR
        sv.invalidate_recordset()
        self.assertAlmostEqual(sv.sv_assignment_nominal_m3, 100.0, 3)
        imp.with_user(self.user_oper).action_apply()
        imp.invalidate_recordset()
        sv.invalidate_recordset()
        self.assertEqual(imp.state, 'applied')
        self.assertTrue(imp.audit_hash)
        self.assertTrue(imp.snapshot_json)
        self.assertEqual(imp.executed_by_id, self.user_oper)
        self.assertTrue(imp.execution_date)
        self.assertEqual(self._audit_count(imp, 'imputation'), 1)
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 10.0, 3)
        self.assertEqual(sv.sv_assignment_applied_count, 1)
        self.assertAlmostEqual(
            sv.sv_assignment_documental_balance_m3, 90.0, 3)
        # APLICAR dos veces: idempotente (sin doble efecto).
        imp.with_user(self.user_oper).action_apply()
        imp.invalidate_recordset()
        sv.invalidate_recordset()
        self.assertEqual(self._audit_count(imp, 'imputation'), 1)
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 10.0, 3)
        # REVERSAR
        imp.with_user(self.user_jef).action_reverse(reason='OFF reversa')
        imp.invalidate_recordset()
        sv.invalidate_recordset()
        self.assertEqual(imp.state, 'reversed')
        self.assertEqual(imp.reversed_by_id, self.user_jef)
        self.assertTrue(imp.reversal_date)
        self.assertEqual(imp.reversal_reason, 'OFF reversa')
        self.assertTrue(imp.audit_hash)
        self.assertEqual(self._audit_count(imp, 'imputation_reverse'), 1)
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 0.0, 3)
        self.assertEqual(sv.sv_assignment_applied_count, 0)
        # ANULAR + VOLVER A BORRADOR
        guia2, etq2, sv2, imp2 = self._doc('OFF2', sv_name='SV0000OFF002')
        imp2.with_user(self.user_oper).action_cancel(reason='OFF2 anular')
        imp2.invalidate_recordset()
        self.assertEqual(imp2.state, 'cancelled')
        imp2.with_user(self.user_oper).action_reopen_to_draft(
            reason='OFF2 reabrir')
        imp2.invalidate_recordset()
        self.assertEqual(imp2.state, 'draft')
        self.assertEqual(imp2.reopen_reason, 'OFF2 reabrir')
        self.assertEqual(self._audit_count(imp2, 'imputation_cancel'), 1)
        self.assertEqual(self._audit_count(imp2, 'imputation_reopen'), 1)
        self.assertEqual(len(imp2.line_ids), 1)
        self.assertEqual(len(imp2.sv_line_ids), 1)

    # ══════════════════════════════════════════════════════════════════════
    # M-2b — una segunda reversa no sobrescribe las marcas de la primera
    # ══════════════════════════════════════════════════════════════════════
    def test_m2b_second_reverse_no_last_wins(self):
        guia, etq, sv, imp = self._doc(
            'M2B', state='applied', sv_name='SV0000M2B001')
        imp.with_user(self.user_jef).action_reverse(reason='primera reversa')
        imp.invalidate_recordset()
        first = (imp.reversed_by_id.id, imp.reversal_date,
                 imp.reversal_reason, imp.audit_hash, imp.snapshot_json)
        self.assertEqual(imp.state, 'reversed')
        with self.assertRaises(UserError):
            imp.with_user(self.user_ger).action_reverse(reason='segunda')
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'reversed')
        self.assertEqual(
            (imp.reversed_by_id.id, imp.reversal_date,
             imp.reversal_reason, imp.audit_hash, imp.snapshot_json), first)
        self.assertEqual(self._audit_count(imp, 'imputation_reverse'), 1)

    # ══════════════════════════════════════════════════════════════════════
    # M-4 — cadena de corrección (origin_imputation_id)
    # ══════════════════════════════════════════════════════════════════════
    def test_m4_new_after_reversed_links_origin_and_reciprocal(self):
        guia = self._guia('F11-M4A')
        etq = self._etq(guia, 'F11-M4A-E', 10.0)
        sv = self._sv(guia, 'SV0000M4A001', 100.0)
        imp1 = self._prepare(guia, sv, etq, 10.0)
        imp1.with_user(self.user_oper).action_apply()
        imp1.with_user(self.user_jef).action_reverse(reason='M4A reversa')
        imp1.invalidate_recordset()
        self.assertEqual(imp1.state, 'reversed')
        imp2 = self._prepare(guia, sv, etq, 10.0)
        self.assertNotEqual(imp2, imp1)
        self.assertNotEqual(imp2.documentary_key, imp1.documentary_key)
        self.assertEqual(imp2.state, 'draft')
        self.assertEqual(imp2.origin_imputation_id, imp1)
        # La reversada NO cambia por el solo hecho de crear la nueva.
        imp1.invalidate_recordset()
        self.assertEqual(imp1.state, 'reversed')
        self.assertFalse(imp1.reversed_imputation_id)
        # Al aplicarse la nueva se sella el recíproco.
        imp2.with_user(self.user_oper).action_apply()
        imp1.invalidate_recordset()
        imp2.invalidate_recordset()
        self.assertEqual(imp2.state, 'applied')
        self.assertEqual(imp1.reversed_imputation_id, imp2)

    def test_m4b_new_after_cancelled_links_origin(self):
        guia = self._guia('F11-M4B')
        etq = self._etq(guia, 'F11-M4B-E', 10.0)
        sv = self._sv(guia, 'SV0000M4B001', 100.0)
        imp1 = self._prepare(guia, sv, etq, 6.0)
        imp1.with_user(self.user_oper).action_cancel(reason='M4B anular')
        imp1.invalidate_recordset()
        self.assertEqual(imp1.state, 'cancelled')
        imp2 = self._prepare(guia, sv, etq, 6.0)
        self.assertNotEqual(imp2, imp1)
        self.assertNotEqual(imp2.documentary_key, imp1.documentary_key)
        self.assertEqual(imp2.origin_imputation_id, imp1)
        # La anulada queda intacta.
        imp1.invalidate_recordset()
        self.assertEqual(imp1.state, 'cancelled')
        self.assertEqual(imp1.cancellation_reason, 'M4B anular')

    def test_m4c_no_terminal_no_origin(self):
        guia = self._guia('F11-M4C')
        etq = self._etq(guia, 'F11-M4C-E', 10.0)
        sv = self._sv(guia, 'SV0000M4C001', 100.0)
        imp = self._prepare(guia, sv, etq, 4.0)
        self.assertFalse(imp.origin_imputation_id)

    # ══════════════════════════════════════════════════════════════════════
    # B-2 — líneas y repartos inmutables fuera de preparación
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_content_locked_in_terminal_states(self):
        cases = (
            ('B2A', 'applied', 'SV0000B2A001'),
            ('B2B', 'reversed', 'SV0000B2B001'),
            ('B2C', 'cancelled', 'SV0000B2C001'),
        )
        for tag, state, sv_name in cases:
            guia, etq, sv, imp = self._doc(
                tag, state=state, sv_name=sv_name)
            line = imp.line_ids
            alloc = imp.sv_line_ids
            self.assertEqual(len(line), 1)
            self.assertEqual(len(alloc), 1)
            with self.assertRaises(UserError, msg='%s write linea' % state):
                line.write({'nominal_volume_m3': 1.0})
            with self.assertRaises(UserError, msg='%s unlink linea' % state):
                line.unlink()
            with self.assertRaises(UserError, msg='%s create linea' % state):
                self.ImputationLine.sudo().create({
                    'imputation_id': imp.id, 'processed_lot_id': etq.id,
                    'nominal_volume_m3': 1.0})
            with self.assertRaises(UserError, msg='%s write reparto' % state):
                alloc.write({'imputed_volume_m3': 1.0})
            with self.assertRaises(UserError, msg='%s unlink reparto' % state):
                alloc.unlink()
            with self.assertRaises(UserError, msg='%s create reparto' % state):
                self.SvLine.sudo().create({
                    'imputation_id': imp.id, 'imputation_line_id': line.id,
                    'sv_lot_id': sv.id, 'imputed_volume_m3': 1.0})
            imp.invalidate_recordset()
            self.assertEqual(len(imp.line_ids), 1)
            self.assertEqual(len(imp.sv_line_ids), 1)
            self.assertAlmostEqual(imp.line_ids.nominal_volume_m3, 10.0, 3)
            self.assertAlmostEqual(
                imp.sv_line_ids.imputed_volume_m3, 10.0, 3)

    def test_b2b_reopen_restores_editable_content(self):
        guia, etq, sv, imp = self._doc(
            'B2D', state='cancelled', sv_name='SV0000B2D001')
        with self.assertRaises(UserError):
            imp.line_ids.write({'nominal_volume_m3': 9.0})
        imp.with_user(self.user_oper).action_reopen_to_draft(
            reason='B2D reabrir')
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        imp.line_ids.write({'nominal_volume_m3': 10.0})   # permitido
        self.assertAlmostEqual(imp.line_ids.nominal_volume_m3, 10.0, 3)
        self.assertEqual(len(imp.sv_line_ids), 1)

    # ══════════════════════════════════════════════════════════════════════
    # B-3 — motivo obligatorio y trazable en la anulación
    # ══════════════════════════════════════════════════════════════════════
    def test_b3_cancel_requires_reason(self):
        guia, etq, sv, imp = self._doc('B3A', sv_name='SV0000B3A001')
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_cancel()
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_cancel(reason='   ')
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.cancelled_by_id)
        self.assertEqual(self._audit_count(imp, 'imputation_cancel'), 0)

    def test_b3b_cancel_records_reason_metadata_and_audit(self):
        guia, etq, sv, imp = self._doc('B3B', sv_name='SV0000B3B001')
        motivo = 'Motivo B-3B verificable'
        imp.with_user(self.user_oper).action_cancel(reason=motivo)
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        self.assertEqual(imp.cancellation_reason, motivo)
        self.assertEqual(imp.cancelled_by_id, self.user_oper)
        self.assertTrue(imp.cancellation_date)
        audit = self.AuditLog.sudo().search([
            ('batch_id', '=', imp.documentary_key),
            ('action_type', '=', 'imputation_cancel')])
        self.assertEqual(len(audit), 1)
        self.assertIn(motivo, audit.audit_snapshot)
        self.assertTrue(audit.audit_hash)
        msgs = self.env['mail.message'].sudo().search([
            ('model', '=', 'madenat.sv.imputation'),
            ('res_id', '=', imp.id)])
        self.assertTrue(any(motivo in (m.body or '') for m in msgs))

    # ══════════════════════════════════════════════════════════════════════
    # Invariantes documentales tras un ciclo completo
    # ══════════════════════════════════════════════════════════════════════
    def test_invariants_after_full_cycle(self):
        guia, etq, sv, imp1 = self._doc(
            'INV', state='reversed', sv_name='SV0000INV001')
        imp2 = self._prepare(guia, sv, etq, 10.0)
        imp2.with_user(self.user_oper).action_apply()
        sv.invalidate_recordset()
        imp2.invalidate_recordset()
        self.assertEqual(imp2.state, 'applied')
        # applied_m3 == Σ real de repartos aplicados hacia el SV.
        applied_lines = self.SvLine.sudo().search([
            ('sv_lot_id', '=', sv.id),
            ('imputation_id.state', '=', 'applied')])
        self.assertAlmostEqual(
            sv.sv_assignment_applied_m3,
            sum(applied_lines.mapped('imputed_volume_m3')), 3)
        self.assertEqual(sv.sv_assignment_applied_count, len(applied_lines))
        # Saldo documental no negativo y coherente con el nominal del SV.
        self.assertGreaterEqual(
            sv.sv_assignment_documental_balance_m3, -1e-6)
        self.assertAlmostEqual(
            sv.sv_assignment_documental_balance_m3,
            sv.sv_assignment_nominal_m3 - sv.sv_assignment_applied_m3, 3)
        # Ninguna aplicada sin firma; la reversada ya no cuenta como aplicada.
        applied = self.Imputation.sudo().search([
            ('state', '=', 'applied'), ('id', 'in', (imp1 | imp2).ids)])
        self.assertEqual(applied, imp2)
        self.assertFalse(applied.filtered(lambda i: not i.audit_hash))
        # El conteo de documentos de la guía es exactamente 2 (cadena).
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)]), 2)

    # ══════════════════════════════════════════════════════════════════════
    # Seguridad por grupo en cada transición
    # ══════════════════════════════════════════════════════════════════════
    def test_groups_matrix_each_transition(self):
        target = {'apply': 'applied', 'reverse': 'reversed',
                  'reopen': 'draft', 'cancel': 'cancelled'}
        matrix = (
            ('apply', ((self.user_oper, True), (self.user_jef, True),
                       (self.user_ger, True), (self.user_aud, False),
                       (self.user_none, False))),
            ('reverse', ((self.user_oper, False), (self.user_jef, True),
                         (self.user_ger, True), (self.user_aud, False),
                         (self.user_none, False))),
            ('reopen', ((self.user_oper, True), (self.user_jef, True),
                        (self.user_ger, True), (self.user_aud, False),
                        (self.user_none, False))),
            ('cancel', ((self.user_oper, True), (self.user_jef, True),
                        (self.user_ger, True), (self.user_aud, False),
                        (self.user_none, False))),
        )
        idx = 0
        for operation, cases in matrix:
            initial = 'applied' if operation == 'reverse' else (
                'cancelled' if operation == 'reopen' else 'draft')
            for user, allowed in cases:
                idx += 1
                guia, etq, sv, imp = self._doc(
                    'GRP%02d' % idx, state=initial,
                    sv_name='SVGRP%05d' % idx)
                label = '%s/%s' % (operation, user.login)
                if operation == 'apply':
                    call = lambda: imp.with_user(user).action_apply()
                elif operation == 'reverse':
                    call = lambda: imp.with_user(user).action_reverse(
                        reason='GRP')
                elif operation == 'reopen':
                    call = lambda: imp.with_user(user).action_reopen_to_draft(
                        reason='GRP')
                else:
                    call = lambda: imp.with_user(user).action_cancel(
                        reason='GRP')
                if allowed:
                    call()
                    imp.invalidate_recordset()
                    self.assertEqual(imp.state, target[operation], label)
                else:
                    with self.assertRaises(AccessError, msg=label):
                        call()
                    imp.sudo().invalidate_recordset()
                    self.assertEqual(imp.state, initial, label)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationReverseLocks(SingleTransactionCase):
    """M-2 (FASE 11): la REVERSA toma los locks de capacidad (ns 3/2).

    ``SingleTransactionCase`` para poder CONFIRMAR el fixture aplicado y liberar
    así los advisory locks de transacción del propio test: una conexión EXTERNA
    retiene entonces el lock del SV y se comprueba que ``action_reverse`` falla
    de forma CONTROLADA (sin marcas de «último gana»), y que al liberarse la
    reversa procede una sola vez. Limpieza por IDs (comparar conteos).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.token = 'f11lk%s' % uuid.uuid4().hex[:8]
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls._imp_ids = []
        cls._lot_ids = []
        cls._guia_ids = []
        cls._audit_keys = set()
        cls.product = cls.env['product.product'].create({
            'name': 'F11LK %s' % cls.token, 'is_storable': True,
            'tracking': 'lot', 'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'F11LK Supplier %s' % cls.token, 'is_company': True})
        cls.user_oper = cls._mk('f11lk_oper_%s' % cls.token, [
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('f11lk_jef_%s' % cls.token, [
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.test' % name,
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id]
                              + [cls.env.ref(g).id for g in groups])]})

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_run()
        cls._cleanup_class()
        super().tearDownClass()

    @classmethod
    def _cleanup_run(cls):
        """Borra los datos POR PRUEBA (imputación, etiquetas, guía, bitácora)."""
        try:
            cls.env.invalidate_all()
            cr = cls.env.cr
            if cls._audit_keys:
                cr.execute(
                    'DELETE FROM madenat_audit_log WHERE batch_id = ANY(%s)',
                    (list(cls._audit_keys),))
            if cls._imp_ids:
                cr.execute(
                    "DELETE FROM mail_message WHERE model = "
                    "'madenat.sv.imputation' AND res_id = ANY(%s)",
                    (cls._imp_ids,))
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
            cr.commit()
            cls.env.invalidate_all()
        except Exception:  # pragma: no cover - limpieza defensiva
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._imp_ids = []
            cls._lot_ids = []
            cls._guia_ids = []
            cls._audit_keys = set()

    @classmethod
    def _cleanup_class(cls):
        """Borra los fixtures de CLASE (usuario, producto, proveedor)."""
        try:
            cr = cls.env.cr
            user_ids = [cls.user_oper.id, cls.user_jef.id]
            cr.execute(
                'SELECT partner_id FROM res_users WHERE id = ANY(%s)',
                (user_ids,))
            partner_ids = [r[0] for r in cr.fetchall() if r[0]]
            partner_ids.append(cls.supplier.id)
            cr.execute('DELETE FROM mail_message WHERE author_id = ANY(%s)',
                       (partner_ids,))
            cr.execute('DELETE FROM res_users WHERE id = ANY(%s)', (user_ids,))
            cr.execute('DELETE FROM res_partner WHERE id = ANY(%s)',
                       (partner_ids,))
            cr.execute(
                'DELETE FROM product_template WHERE id IN (SELECT '
                'product_tmpl_id FROM product_product WHERE id = %s)',
                (cls.product.id,))
            cr.execute('DELETE FROM product_product WHERE id = %s',
                       (cls.product.id,))
            cr.commit()
            cls.env.invalidate_all()
        except Exception:  # pragma: no cover - limpieza defensiva
            try:
                cls.env.cr.rollback()
            except Exception:
                pass

    # ── Fixture APLICADO (publicado por el test) ──────────────────────────
    def _fixture_applied(self):
        guia = self.env['madenat.guia.processing'].sudo().create({
            'name': 'F11LK-%s' % self.token, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-15'})
        self._guia_ids.append(guia.id)
        etq = self.env['stock.lot'].sudo().create({
            'name': 'F11LK-E-%s' % self.token, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': 'F11LK-E-%s' % self.token, 'volume_purchase_m3': 10.0,
            'vol_shipment_m3': 10.0})
        self._lot_ids.append(etq.id)
        guia.sudo().write({'lot_ids': [(4, etq.id)]})
        sv = self.env['stock.lot'].sudo().create({
            'name': 'SVF11LK%s' % self.token[:6],
            'product_id': self.product.id, 'company_id': self.company.id,
            'lot_flow_type': 'volume', 'volume_source_guia_id': guia.id,
            'volume_purchase_m3': 100.0, 'vol_shipment_m3': 100.0})
        self._lot_ids.append(sv.id)
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        line.selected = True
        line.cantidad_asignar_m3 = 10.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self._imp_ids.append(imp.id)
        self._audit_keys.add(imp.documentary_key)
        imp.with_user(self.user_oper).action_apply()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'applied')
        return etq, sv, imp

    def test_m2_reverse_takes_locks_and_reports_controlled_conflict(self):
        etq, sv, imp = self._fixture_applied()
        # Publicar el fixture: se liberan los advisory locks del test.
        self.cr.commit()
        before = self.Imputation.sudo().search_count([])
        cr2 = None
        try:
            conn = db_connect(self.env.cr.dbname)
            cr2 = conn.cursor()
            cr2.transaction = api.Transaction(self.registry)
            # Conexión EXTERNA retiene los locks de capacidad (ns 2 SV,
            # ns 3 etiqueta) con el mismo espacio que `_i2_lock_resources`.
            cr2.execute('SELECT pg_advisory_lock(2, %s)', (sv.id,))
            cr2.execute('SELECT pg_advisory_lock(3, %s)', (etq.id,))
            imp.invalidate_recordset()
            with self.assertRaises(UserError) as cm:
                imp.with_user(self.user_jef).action_reverse(reason='M2 bloqueo')
            self.assertIn(
                'Otra operación está modificando', str(cm.exception))
            # Bloqueo CONTROLADO: sin marcas de «último gana» ni bitácora.
            imp.invalidate_recordset()
            self.assertEqual(imp.state, 'applied')
            self.assertFalse(imp.reversed_by_id)
            self.assertFalse(imp.reversal_date)
            self.assertFalse(imp.reversal_reason)
            self.assertEqual(self.AuditLog.sudo().search_count([
                ('batch_id', '=', imp.documentary_key),
                ('action_type', '=', 'imputation_reverse')]), 0)
            cr2.execute('SELECT pg_advisory_unlock_all()')
        finally:
            if cr2 is not None:
                cr2.rollback()
                cr2.close()
        # Liberado el lock, la reversa procede UNA sola vez y firma.
        imp.invalidate_recordset()
        imp.with_user(self.user_jef).action_reverse(reason='M2 libre')
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'reversed')
        self.assertEqual(imp.reversal_reason, 'M2 libre')
        self.assertTrue(imp.reversed_by_id)
        self.assertEqual(self.AuditLog.sudo().search_count([
            ('batch_id', '=', imp.documentary_key),
            ('action_type', '=', 'imputation_reverse')]), 1)
        self.cr.commit()
        # Sin residuos: el conteo de documentos no cambia con la prueba.
        self.assertEqual(self.Imputation.sudo().search_count([]), before)
