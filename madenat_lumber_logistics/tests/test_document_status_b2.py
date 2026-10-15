# -*- coding: utf-8 -*-
"""B2 — Fuente única de estado documental de Embarque (Odoo 18 CE).

Suite `TestDocumentStatusB2` (T-B2-01 .. T-B2-11).

Valida el contrato canónico de `document_status` y sus contadores
(`not_configured · missing · pending · partial · attached · verified`),
derivados EXCLUSIVAMENTE de `document_ids` + `checklist_id`
(activo/requerido). `document_status` es INFORMATIVO: nunca es gate de
operación física.

Datos 100% aislados (TransactionCase); nada se persiste. No depende de D2
(`action_deliver`/waiver), Backlog, Costeo, Billing/Pagos, B-01, Rebaja,
Rollover ni Zarpe. No mueve inventario ni genera efectos financieros.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestDocumentStatusB2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Document = cls.env['lumber.shipment.document']
        cls.Checklist = cls.env['lumber.document.checklist']
        cls.partner = cls.env['res.partner'].create({'name': 'B2 Partner'})
        cls.vessel = cls.env['shipping.vessel'].create({'name': 'B2 VESSEL'})

    # ══════════════════════════════════════════════════════════════════════
    # Fábricas aisladas (sin mover stock, sin efectos financieros)
    # ══════════════════════════════════════════════════════════════════════
    def _shipment(self, name):
        """Embarque nuevo en borrador con universo documental controlado.

        El alta auto-genera documentos a partir de los checklist activos; se
        limpian para partir de un universo determinista.
        """
        shipment = self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'vessel_id': self.vessel.id})
        if shipment.document_ids:
            shipment.document_ids.unlink()
        shipment.invalidate_recordset()
        return shipment

    def _checklist(self, name, required=True, active=True):
        return self.Checklist.create({
            'name': name, 'is_required': required, 'active': active})

    def _doc(self, shipment, checklist, state):
        doc = self.Document.create({
            'shipment_id': shipment.id,
            'checklist_id': checklist.id,
            'name': 'B2-%s' % state,
        })
        doc.write({'state': state})
        shipment.invalidate_recordset()
        return doc

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-01 — sin checklist/documentos → not_configured
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_01_not_configured(self):
        shipment = self._shipment('B2-01')
        self.assertEqual(shipment.document_status, 'not_configured')
        self.assertEqual(shipment.document_completion, 0.0)
        self.assertEqual(shipment.document_pending_count, 0)
        self.assertEqual(shipment.document_missing_count, 0)
        self.assertEqual(shipment.document_verified_count, 0)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-02 — requerido sin evidencia → missing
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_02_missing_required(self):
        shipment = self._shipment('B2-02')
        chk = self._checklist('B2-02 required')
        self._doc(shipment, chk, 'missing')
        self.assertEqual(shipment.document_status, 'missing')
        self.assertEqual(shipment.document_missing_count, 1)
        self.assertEqual(shipment.document_pending_count, 1)
        self.assertEqual(shipment.document_verified_count, 0)
        self.assertEqual(shipment.document_completion, 0.0)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-03 — adjunto parcial sin verificación → pending
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_03_pending_attached_partial(self):
        shipment = self._shipment('B2-03')
        chk = self._checklist('B2-03 required')
        self._doc(shipment, chk, 'attached')
        self._doc(shipment, chk, 'missing')
        self.assertEqual(shipment.document_status, 'pending')
        self.assertEqual(shipment.document_verified_count, 0)
        self.assertEqual(shipment.document_missing_count, 1)
        self.assertEqual(shipment.document_pending_count, 2)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-04 — verificación parcial → partial
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_04_partial_verified(self):
        shipment = self._shipment('B2-04')
        chk = self._checklist('B2-04 required')
        self._doc(shipment, chk, 'verified')
        self._doc(shipment, chk, 'attached')
        self.assertEqual(shipment.document_status, 'partial')
        self.assertEqual(shipment.document_verified_count, 1)
        self.assertEqual(shipment.document_missing_count, 0)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-05 — todos adjuntos sin verificación → attached
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_05_attached_all(self):
        shipment = self._shipment('B2-05')
        chk = self._checklist('B2-05 required')
        self._doc(shipment, chk, 'attached')
        self._doc(shipment, chk, 'attached')
        self.assertEqual(shipment.document_status, 'attached')
        self.assertEqual(shipment.document_completion, 100.0)
        self.assertEqual(shipment.document_verified_count, 0)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-06 — todos verificados → verified
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_06_verified_all(self):
        shipment = self._shipment('B2-06')
        chk = self._checklist('B2-06 required')
        self._doc(shipment, chk, 'verified')
        self._doc(shipment, chk, 'verified')
        self.assertEqual(shipment.document_status, 'verified')
        self.assertEqual(shipment.document_completion, 100.0)
        self.assertEqual(shipment.document_pending_count, 0)
        self.assertEqual(shipment.document_missing_count, 0)
        self.assertEqual(shipment.document_verified_count, 2)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-07 — documentos NO requeridos no degradan si existen requeridos
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_07_optional_docs_ignored_when_required_exists(self):
        shipment = self._shipment('B2-07')
        req = self._checklist('B2-07 required', required=True)
        opt = self._checklist('B2-07 optional', required=False)
        self._doc(shipment, req, 'verified')
        self._doc(shipment, opt, 'missing')
        self.assertEqual(shipment.document_status, 'verified')
        self.assertEqual(shipment.document_verified_count, 1)
        self.assertEqual(shipment.document_missing_count, 0)
        self.assertEqual(shipment.document_pending_count, 0)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-08 — contadores y completion exactos
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_08_counts_and_completion(self):
        shipment = self._shipment('B2-08')
        chk = self._checklist('B2-08 required')
        self._doc(shipment, chk, 'verified')
        self._doc(shipment, chk, 'attached')
        self._doc(shipment, chk, 'missing')
        self.assertEqual(shipment.document_status, 'partial')
        self.assertEqual(shipment.document_verified_count, 1)
        self.assertEqual(shipment.document_missing_count, 1)
        self.assertEqual(shipment.document_pending_count, 2)
        self.assertAlmostEqual(
            shipment.document_completion, 66.666, places=2)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-09 — cambiar el estado de un documento recalcula el Embarque
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_09_recompute_on_document_state_change(self):
        shipment = self._shipment('B2-09')
        chk = self._checklist('B2-09 required')
        d1 = self._doc(shipment, chk, 'verified')
        self._doc(shipment, chk, 'verified')
        self.assertEqual(shipment.document_status, 'verified')
        d1.write({'state': 'missing'})
        shipment.invalidate_recordset()
        self.assertEqual(shipment.document_status, 'partial')
        self.assertEqual(shipment.document_verified_count, 1)

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-10 — nunca aparecen los valores legacy complete/incomplete
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_10_no_legacy_status_values(self):
        canonical = {'not_configured', 'missing', 'pending', 'partial',
                     'attached', 'verified'}
        shipment = self._shipment('B2-10')
        chk = self._checklist('B2-10 required')
        for state in ('missing', 'attached', 'verified'):
            self._doc(shipment, chk, state)
            self.assertIn(shipment.document_status, canonical)
            self.assertNotIn(
                shipment.document_status, ('complete', 'incomplete'))

    # ══════════════════════════════════════════════════════════════════════
    # T-B2-11 — Δ0 en dominios ajenos (stock/auditoría/finanzas/SV)
    # ══════════════════════════════════════════════════════════════════════
    def test_b2_11_no_cross_domain_side_effects(self):
        e = self.env
        watched = (
            'stock.quant', 'stock.move', 'stock.move.line', 'stock.picking',
            'stock.lot', 'madenat.audit.log', 'stock.lot.cost.line',
            'account.move', 'account.payment', 'lumber.billing.consolidation',
        )
        before = {m: e[m].search_count([]) for m in watched}
        shipment = self._shipment('B2-11')
        req = self._checklist('B2-11 required')
        opt = self._checklist('B2-11 optional', required=False)
        d1 = self._doc(shipment, req, 'attached')
        self._doc(shipment, opt, 'missing')
        d1.write({'state': 'verified'})
        shipment.invalidate_recordset()
        summary = shipment._document_status_summary()
        self.assertEqual(summary['status'], shipment.document_status)
        after = {m: e[m].search_count([]) for m in watched}
        for m in watched:
            self.assertEqual(after[m], before[m], m)
