# -*- coding: utf-8 -*-
"""Backlog documental NO bloqueante y auditado (AD-100, 2026-10-05).

Suite `TestDocumentaryBacklog`.

Mantiene los seis tests originales (T-DOC-1..T-DOC-6) y agrega la cobertura
BL-01..BL-18 del workflow no bloqueante:

* Roles server-side: Operaciones gestiona datos; Jefatura/Gerencia escalan;
  Gerencia cierra o exonera (falta de permiso ⇒ ``AccessError``).
* Token de proceso anti-RPC (no eludible por ``with_context``).
* Idempotencia (no-op sin auditoría ni chatter).
* Auditoría SHA-256 (``madenat.audit.log``) y chatter.
* Separación B2/D2 y Δ0 en stock/B-01/R1/R2/R4/Costeo/Finanzas/SV.

Datos 100% aislados (TransactionCase); nada se persiste.
"""
import base64
import hashlib
import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestDocumentaryBacklog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Document = cls.env['lumber.shipment.document']
        cls.Checklist = cls.env['lumber.document.checklist']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.partner = cls.env['res.partner'].create({'name': 'DOC Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'DOC Lumber', 'is_storable': True, 'tracking': 'lot'})
        cls.vessel = cls.env['shipping.vessel'].create({'name': 'DOC VESSEL'})
        cls.voyage = cls.env['shipping.voyage'].create({
            'vessel_id': cls.vessel.id, 'voyage_reference': 'DOC-VOY',
            'etd': fields.Date.today(),
            'port_of_discharge': 'San Antonio, CL'})

        def _mk_user(login, groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'email': '%s@madenat.cl' % login,
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('doc_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('doc_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('doc_ger', [
            'base.group_user', 'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk_user('doc_plain', ['base.group_user'])
        if not cls.Checklist.search_count([]):
            cls.Checklist.create({'name': 'DOC B/L', 'is_required': True})

    def _mk_shipment(self, name, state='draft'):
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'vessel_id': self.vessel.id, 'voyage_id': self.voyage.id,
            'state': state})

    # T-DOC-1 — documento missing → backlog open, sin afectar Embarque
    def test_doc_01_missing_creates_open_backlog(self):
        shipment = self._mk_shipment('DOC-01')
        docs = shipment.document_ids
        self.assertTrue(docs)
        for doc in docs:
            self.assertEqual(doc.state, 'missing')
            self.assertEqual(doc.backlog_state, 'open')
        self.assertEqual(shipment.state, 'draft')

    # T-DOC-2 — asignar responsible/due_date/criticality (trazable)
    def test_doc_02_assign_responsible_due_criticality(self):
        shipment = self._mk_shipment('DOC-02')
        doc = shipment.document_ids[0]
        doc.write({
            'responsible_id': self.user_oper.id,
            'due_date': '2026-10-10',
            'criticality': 'high',
        })
        doc.invalidate_recordset()
        self.assertEqual(doc.responsible_id, self.user_oper)
        self.assertEqual(doc.criticality, 'high')
        self.assertTrue(doc.backlog_attention)  # high + open
        self.assertEqual(shipment.state, 'draft')

    # T-DOC-3 — attached/completed conserva historia
    def test_doc_03_attached_completes_backlog_history(self):
        shipment = self._mk_shipment('DOC-03')
        doc = shipment.document_ids[0]
        doc.file_data = base64.b64encode(b'file').decode('utf-8')
        doc.invalidate_recordset()
        self.assertEqual(doc.state, 'attached')
        doc.action_backlog_complete()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'completed')
        self.assertIn(shipment.document_status,
                      ('missing', 'pending', 'partial', 'attached',
                       'verified', 'not_configured'))

    # T-DOC-4 — overdue/high → advertencia; escalar sin UserError
    def test_doc_04_overdue_attention_no_usererror(self):
        shipment = self._mk_shipment('DOC-04')
        doc = shipment.document_ids[0]
        doc.write({'due_date': '2020-01-01', 'criticality': 'low'})
        doc.invalidate_recordset()
        self.assertTrue(doc.backlog_overdue)
        self.assertTrue(doc.backlog_attention)
        doc.action_backlog_escalate()  # manual, no lanza UserError
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'in_progress')
        self.assertTrue(doc.escalated_at)
        self.assertEqual(doc.escalated_by_id, self.env.user)
        self.assertEqual(shipment.state, 'draft')

    # T-DOC-5 — el backlog no puede cambiar el estado físico
    def test_doc_05_backlog_cannot_change_physical_state(self):
        shipment = self._mk_shipment('DOC-05')
        doc = shipment.document_ids[0]
        e = self.env
        before = {
            'move': e['stock.move'].search_count([]),
            'quant': e['stock.quant'].search_count([]),
            'picking': e['stock.picking'].search_count([]),
        }
        doc.write({'backlog_state': 'completed', 'criticality': 'critical'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'draft')
        self.assertEqual(e['stock.move'].search_count([]), before['move'])
        self.assertEqual(e['stock.quant'].search_count([]), before['quant'])
        self.assertEqual(e['stock.picking'].search_count([]),
                         before['picking'])

    # T-DOC-6 — document_status compute ÚNICO y determinista
    def test_doc_06_document_status_single_compute(self):
        shipment = self._mk_shipment('DOC-06')
        docs = shipment.document_ids
        required = docs.filtered(lambda d: d.checklist_id.is_required)
        target = required if required else docs
        for doc in docs:
            doc.file_data = base64.b64encode(b'x').decode('utf-8')
        shipment.invalidate_recordset()
        # Todos los objetivos adjuntos, ninguno verificado → 'attached'.
        self.assertEqual(shipment.document_verified_count, 0)
        self.assertEqual(shipment.document_missing_count, 0)
        self.assertEqual(shipment.document_pending_count, len(target))
        self.assertEqual(shipment.document_status, 'attached')
        # Uno de los requeridos verificado → 'partial'.
        target[0].state = 'verified'
        shipment.invalidate_recordset()
        self.assertEqual(shipment.document_verified_count, 1)
        self.assertEqual(shipment.document_status, 'partial')

    # ══════════════════════════════════════════════════════════════════════
    # Helpers AD-100
    # ══════════════════════════════════════════════════════════════════════
    def _counts(self):
        e = self.env
        return {
            'shipment': e['lumber.export.shipment'].search_count([]),
            'document': e['lumber.shipment.document'].search_count([]),
            'container': e['lumber.container'].search_count([]),
            'shipment_line': e['lumber.shipment.line'].search_count([]),
            'quant': e['stock.quant'].search_count([]),
            'move': e['stock.move'].search_count([]),
            'move_line': e['stock.move.line'].search_count([]),
            'picking': e['stock.picking'].search_count([]),
            'lot': e['stock.lot'].search_count([]),
            'sv_operation': e['madenat.sv.operation'].search_count([]),
            'audit': e['madenat.audit.log'].search_count([]),
            'lot_cost_line': e['stock.lot.cost.line'].search_count([]),
            'account_move': e['account.move'].search_count([]),
            'payment': e['account.payment'].search_count([]),
            'consolidation': e['lumber.billing.consolidation'].search_count([]),
        }

    def _assert_no_business_change(self, before, after):
        for key in before:
            self.assertEqual(after[key], before[key], key)

    def _backlog_audits(self, doc, action):
        return self.AuditLog.search([
            ('action_type', '=', 'documentary_backlog_%s' % action),
            ('batch_id', '=', 'doc:%s' % doc.id)])

    def _assert_hash_ok(self, log):
        self.assertTrue(log)
        self.assertEqual(len(log.audit_hash or ''), 64)
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

    def _msg_count(self, doc):
        return self.env['mail.message'].search_count([
            ('model', '=', 'lumber.shipment.document'),
            ('res_id', '=', doc.id)])

    def _mk_container(self, name, shipment, state='rebajado',
                      line_state='rebajado'):
        container = self.env['lumber.container'].create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id, 'state': state})
        lot = self.env['stock.lot'].create({
            'name': 'DOCLOT-%s' % name, 'product_id': self.product.id})
        self.env['lumber.shipment.line'].create({
            'container_id': container.id, 'shipment_id': shipment.id,
            'lot_id': lot.id, 'rebaja_state': line_state})
        container.invalidate_recordset()
        return container


    # ══════════════════════════════════════════════════════════════════════
    # BL-01..BL-18 — Workflow no bloqueante y auditado (AD-100)
    # ══════════════════════════════════════════════════════════════════════

    # BL-01 — estado inicial abierto
    def test_bl_01_initial_state_open(self):
        shipment = self._mk_shipment('BL-01')
        docs = shipment.document_ids
        self.assertTrue(docs)
        for doc in docs:
            self.assertEqual(doc.backlog_state, 'open')

    # BL-02 — criticidad
    def test_bl_02_criticality(self):
        doc = self._mk_shipment('BL-02').document_ids[0]
        self.assertEqual(doc.criticality, 'medium')
        doc.with_user(self.user_oper).write({'criticality': 'high'})
        doc.invalidate_recordset()
        self.assertEqual(doc.criticality, 'high')

    # BL-03 — responsable/fecha/nota por Operaciones
    def test_bl_03_operaciones_manages_fields(self):
        doc = self._mk_shipment('BL-03').document_ids[0]
        doc.with_user(self.user_oper).write({
            'responsible_id': self.user_oper.id,
            'due_date': '2026-12-31',
            'backlog_note': 'Pendiente de recibir B/L original del cliente.',
        })
        doc.invalidate_recordset()
        self.assertEqual(doc.responsible_id, self.user_oper)
        self.assertEqual(str(doc.due_date), '2026-12-31')
        self.assertIn('B/L original', doc.backlog_note)

    # BL-04 — flags de vencimiento/atención
    def test_bl_04_overdue_attention_flags(self):
        doc = self._mk_shipment('BL-04').document_ids[0]
        doc.write({'due_date': '2020-01-01', 'criticality': 'low'})
        doc.invalidate_recordset()
        self.assertTrue(doc.backlog_overdue)
        self.assertTrue(doc.backlog_attention)
        doc.write({'criticality': 'high', 'due_date': False})
        doc.invalidate_recordset()
        self.assertFalse(doc.backlog_overdue)
        self.assertTrue(doc.backlog_attention)

    # BL-05 — escalamiento Jefatura/Gerencia
    def test_bl_05_escalate_authorized(self):
        for user in (self.user_jef, self.user_ger):
            doc = self._mk_shipment('BL-05-%s' % user.login).document_ids[0]
            doc.with_user(user).action_backlog_escalate()
            doc.invalidate_recordset()
            self.assertEqual(doc.backlog_state, 'in_progress')
            self.assertTrue(doc.escalated_at)
            self.assertEqual(doc.escalated_by_id, user)

    # BL-06 — escalamiento no autorizado bloqueado (AccessError)
    def test_bl_06_escalate_denied(self):
        for user in (self.user_oper, self.user_plain):
            doc = self._mk_shipment('BL-06-%s' % user.login).document_ids[0]
            before = self._counts()
            with self.assertRaises(AccessError):
                doc.with_user(user).action_backlog_escalate()
            doc.invalidate_recordset()
            self.assertEqual(doc.backlog_state, 'open')
            self.assertFalse(doc.escalated_at)
            self._assert_no_business_change(before, self._counts())


    # BL-07 — cierre Gerencia
    def test_bl_07_complete_authorized(self):
        doc = self._mk_shipment('BL-07').document_ids[0]
        doc.with_user(self.user_ger).action_backlog_complete()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'completed')
        # No cambia el estado documental (dimensión distinta).
        self.assertEqual(doc.state, 'missing')

    # BL-08 — cierre no autorizado bloqueado (AccessError)
    def test_bl_08_complete_denied(self):
        for user in (self.user_oper, self.user_jef, self.user_plain):
            doc = self._mk_shipment('BL-08-%s' % user.login).document_ids[0]
            with self.assertRaises(AccessError):
                doc.with_user(user).action_backlog_complete()
            doc.invalidate_recordset()
            self.assertEqual(doc.backlog_state, 'open')

    # BL-09 — escalamiento repetido no cambia escalated_* ni duplica evidencia
    def test_bl_09_escalate_idempotent(self):
        doc = self._mk_shipment('BL-09').document_ids[0]
        doc.with_user(self.user_jef).action_backlog_escalate()
        doc.invalidate_recordset()
        at_first, by_first = doc.escalated_at, doc.escalated_by_id
        aud = len(self._backlog_audits(doc, 'escalation'))
        msg = self._msg_count(doc)
        doc.with_user(self.user_ger).action_backlog_escalate()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'in_progress')
        self.assertEqual(doc.escalated_at, at_first)
        self.assertEqual(doc.escalated_by_id, by_first)
        self.assertEqual(len(self._backlog_audits(doc, 'escalation')), aud)
        self.assertEqual(self._msg_count(doc), msg)

    # BL-10 — cierre repetido no genera auditoría/chatter adicional
    def test_bl_10_complete_idempotent(self):
        doc = self._mk_shipment('BL-10').document_ids[0]
        doc.with_user(self.user_ger).action_backlog_complete()
        aud = len(self._backlog_audits(doc, 'completion'))
        msg = self._msg_count(doc)
        doc.with_user(self.user_ger).action_backlog_complete()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'completed')
        self.assertEqual(len(self._backlog_audits(doc, 'completion')), aud)
        self.assertEqual(self._msg_count(doc), msg)

    # BL-11 — write directo/context/RPC no altera backlog_state/escalated_*
    def test_bl_11_direct_write_blocked(self):
        doc = self._mk_shipment('BL-11').document_ids[0]
        cases = (
            {'backlog_state': 'completed'},
            {'escalated_at': fields.Datetime.now()},
            {'escalated_by_id': self.user_jef.id},
        )
        for vals in cases:
            with self.assertRaises(UserError):
                doc.with_user(self.user_jef).write(vals)
        with self.assertRaises(UserError):
            doc.with_user(self.user_ger).with_context(
                backlog_internal=True, allow_backlog=True).write(
                    {'backlog_state': 'completed'})
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'open')
        self.assertFalse(doc.escalated_at)
        self.assertFalse(doc.escalated_by_id)

    # BL-12 — no modifica B2
    def test_bl_12_no_modify_b2(self):
        shipment = self._mk_shipment('BL-12')
        doc = shipment.document_ids[0]
        shipment.invalidate_recordset()
        before = (shipment.document_status, shipment.document_verified_count,
                  shipment.document_missing_count,
                  shipment.document_pending_count)
        doc.with_user(self.user_jef).action_backlog_escalate()
        doc.with_user(self.user_ger).action_backlog_complete()
        shipment.invalidate_recordset()
        after = (shipment.document_status, shipment.document_verified_count,
                 shipment.document_missing_count,
                 shipment.document_pending_count)
        self.assertEqual(after, before)


    # BL-13 — el backlog no bloquea ni modifica D2
    def test_bl_13_d2_not_blocked(self):
        shipment = self._mk_shipment('BL-13', state='in_transit')
        self._mk_container('BL-13C', shipment)
        doc = shipment.document_ids[0]
        # Backlog abierto NO bloquea la Entrega.
        doc.with_user(self.user_jef).action_backlog_escalate()
        doc.invalidate_recordset()
        backlog_before = doc.backlog_state
        shipment.with_user(self.user_jef).action_deliver()
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'delivered')
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, backlog_before)

    # BL-14 — Δ0 en stock/B-01/R1/R2/R4/Costeo/Finanzas/SV
    def test_bl_14_delta_zero_domains(self):
        shipment = self._mk_shipment('BL-14')
        doc = shipment.document_ids[0]
        before = self._counts()
        doc.with_user(self.user_jef).action_backlog_escalate()
        doc.with_user(self.user_ger).action_backlog_complete()
        after = self._counts()
        for key in before:
            if key == 'audit':
                # Sólo la bitácora crece (2 eventos: escalamiento + cierre).
                self.assertEqual(after[key], before[key] + 2)
            else:
                self.assertEqual(after[key], before[key], key)
        shipment.invalidate_recordset()
        self.assertEqual(shipment.state, 'draft')
        self.assertFalse(shipment.b01_exception_state == 'resolved')

    # BL-15 — auditoría SHA-256 + chatter correcto
    def test_bl_15_audit_and_chatter(self):
        shipment = self._mk_shipment('BL-15')
        doc = shipment.document_ids[0]
        doc.with_user(self.user_jef).action_backlog_escalate()
        log = self._backlog_audits(doc, 'escalation')
        self.assertEqual(len(log), 1)
        self._assert_hash_ok(log)
        payload = json.loads(log.audit_snapshot)
        self.assertEqual(payload['document']['backlog_state_after'],
                         'in_progress')
        self.assertEqual(payload['document']['document_id'], doc.id)
        self.assertEqual(payload['document']['shipment_id'], shipment.id)
        self.assertIn('document_status', payload['shipment'])
        self.assertEqual(log.user_id, self.user_jef)
        self.assertGreater(self._msg_count(doc), 0)

    # BL-16 — rollback total si falla la auditoría o el write
    def test_bl_16_rollback_on_failure(self):
        # a) Fallo en la creación de auditoría.
        doc = self._mk_shipment('BL-16a').document_ids[0]
        before = self._counts()
        with patch.object(
                type(doc), '_create_backlog_audit',
                side_effect=UserError('fallo inducido')):
            with self.assertRaises(UserError):
                doc.with_user(self.user_jef).action_backlog_escalate()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'open')
        self.assertFalse(doc.escalated_at)
        self._assert_no_business_change(before, self._counts())
        # b) Fallo en el write del workflow.
        doc2 = self._mk_shipment('BL-16b').document_ids[0]
        before2 = self._counts()
        with patch.object(
                type(doc2), 'write',
                side_effect=UserError('fallo inducido en write')):
            with self.assertRaises(UserError):
                doc2.with_user(self.user_jef).action_backlog_escalate()
        doc2.invalidate_recordset()
        self.assertEqual(doc2.backlog_state, 'open')
        self.assertFalse(doc2.escalated_at)
        self._assert_no_business_change(before2, self._counts())


    # BL-17 — exoneración: sólo Gerencia, motivo >= 20, idempotencia
    def test_bl_17_waive_rules(self):
        reason = 'Documento no aplicable para este destino según contrato.'
        # Operaciones/Jefatura denegado (AccessError) sin mutar.
        for user in (self.user_oper, self.user_jef):
            doc = self._mk_shipment('BL-17-%s' % user.login).document_ids[0]
            doc.write({'backlog_note': reason})
            with self.assertRaises(AccessError):
                doc.with_user(user).action_backlog_waive()
            doc.invalidate_recordset()
            self.assertEqual(doc.backlog_state, 'open')
        # Gerencia con motivo < 20 caracteres → UserError.
        doc = self._mk_shipment('BL-17-short').document_ids[0]
        doc.write({'backlog_note': 'corto'})
        with self.assertRaises(UserError):
            doc.with_user(self.user_ger).action_backlog_waive()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'open')
        # Gerencia con motivo válido → waived + nota trazable + auditoría.
        doc2 = self._mk_shipment('BL-17-ok').document_ids[0]
        doc2.write({'backlog_note': reason})
        doc2.with_user(self.user_ger).action_backlog_waive()
        doc2.invalidate_recordset()
        self.assertEqual(doc2.backlog_state, 'waived')
        self.assertIn(reason, doc2.backlog_note)
        self.assertIn('Exonerado', doc2.backlog_note)
        log = self._backlog_audits(doc2, 'waiver')
        self._assert_hash_ok(log)
        aud = len(log)
        msg = self._msg_count(doc2)
        # Idempotencia: repetir no genera auditoría/chatter adicional.
        doc2.with_user(self.user_ger).action_backlog_waive()
        doc2.invalidate_recordset()
        self.assertEqual(doc2.backlog_state, 'waived')
        self.assertEqual(len(self._backlog_audits(doc2, 'waiver')), aud)
        self.assertEqual(self._msg_count(doc2), msg)

    # BL-18 — no se puede exonerar un backlog completed
    def test_bl_18_cannot_waive_completed(self):
        doc = self._mk_shipment('BL-18').document_ids[0]
        doc.write({
            'backlog_note': 'Motivo suficientemente largo para exonerar.'})
        doc.with_user(self.user_ger).action_backlog_complete()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'completed')
        aud = len(self._backlog_audits(doc, 'waiver'))
        with self.assertRaises(UserError):
            doc.with_user(self.user_ger).action_backlog_waive()
        doc.invalidate_recordset()
        self.assertEqual(doc.backlog_state, 'completed')
        self.assertEqual(len(self._backlog_audits(doc, 'waiver')), aud)
