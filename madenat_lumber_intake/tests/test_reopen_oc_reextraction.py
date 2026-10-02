# -*- coding: utf-8 -*-
"""Re-extracción de la OC documental al reabrir una guía a borrador (Tarea B-1).

Contrato verificado (Diseño B — B-min + B2, 2026-09-28):

1. `action_reopen_to_draft()` sigue limpiando la trazabilidad OC, pero
   INMEDIATAMENTE la re-extrae del documento adjunto: `oc_reference_raw` no
   puede quedar vacío si el PDF adjunto declara la OC.
2. Con `purchase.order` coincidente, el match (B2) vuelve a dejar `order_id`
   vinculado y `oc_match_status = 'single_match'`.
3. FAIL-SOFT: con un documento ilegible el reset se completa SIN excepción,
   `oc_reference_raw` queda vacío y el chatter lo informa (nunca silencioso).

Usa el PDF real de referencia (`fixtures/HLZF75_4495589.pdf`, el mismo
documento de la guía 4495589). TransactionCase: todo se revierte.
"""
import base64
import os

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

FIXTURE_PDF = os.path.join(
    os.path.dirname(__file__), 'fixtures', 'HLZF75_4495589.pdf')
OC_RAW = '2708-327-02'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestReopenOcReextraction(TransactionCase):
    """Re-apertura a borrador: la OC documental se re-deriva del PDF adjunto."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Reapertura OC', 'is_company': True})
        with open(FIXTURE_PDF, 'rb') as handle:
            cls.pdf_bytes = handle.read()

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, pdf_bytes):
        """Guía 'verified' con documento adjunto y OC documental vigente."""
        guia = self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-07',
            'volume_pdf_m3': 40.315,
            'guide_pdf_file': base64.b64encode(pdf_bytes),
            'guide_pdf_filename': 'HLZF75_4495589.pdf',
        })
        guia.write({'oc_reference_raw': OC_RAW})
        return guia

    def _chatter(self, guia):
        return '\n'.join(guia.message_ids.mapped('body') or [])

    # ── 1. Re-extracción exitosa desde el PDF real ─────────────────────────
    def test_reopen_to_draft_reextrae_oc_desde_pdf_real(self):
        """Tras el reset la OC se re-deriva del PDF adjunto y se re-vincula."""
        guia = self._make_guia('B1-OC-REEXTRACT', self.pdf_bytes)
        self.assertEqual(guia.oc_reference_raw, OC_RAW)
        # El único PO que puede coincidir es el de este proveedor (partner
        # creado en el test), por lo que el match es determinista.
        po = self.env['purchase.order'].create({
            'name': OC_RAW,
            'partner_id': self.partner.id,
        })

        self.env['madenat.guia.processing.reopen.wizard'].create(
            {'guia_processing_id': guia.id,
             'reason': 'Reapertura de prueba'}).action_confirm()
        guia.invalidate_recordset()

        self.assertEqual(guia.state, 'draft')
        self.assertEqual(
            guia.oc_reference_raw, OC_RAW,
            'La OC documental debe re-extraerse del PDF adjunto, no quedar vacía')
        # B2 — re-vinculación de purchase.order con la OC re-extraída.
        self.assertEqual(guia.order_id, po, 'La OC debe quedar re-vinculada')
        self.assertEqual(guia.oc_match_status, 'single_match')
        self.assertIn(
            'OC re-extraída automáticamente tras el reset', self._chatter(guia))

    # ── 2. Fail-soft ante documento ilegible ───────────────────────────────
    def test_reopen_to_draft_fail_soft_ante_documento_corrupto(self):
        """Un adjunto ilegible no puede romper el reset (fail-soft + aviso)."""
        guia = self._make_guia('B1-OC-FAILSOFT', b'%PDF-fake no legible')
        # Camino «fallo SIN valor previo» (Tarea B-1, Opción 3): sin OC previa
        # el resguardo no aplica y el campo queda vacío. El camino «fallo CON
        # valor previo» lo cubre el test del failsafe.
        guia.write({'oc_reference_raw': False})

        self.env['madenat.guia.processing.reopen.wizard'].create(
            {'guia_processing_id': guia.id,
             'reason': 'Reapertura de prueba'}).action_confirm()  # no debe propagar ninguna excepción
        guia.invalidate_recordset()

        self.assertEqual(guia.state, 'draft')
        self.assertFalse(guia.oc_reference_raw)
        self.assertFalse(guia.order_id)
        chatter = self._chatter(guia)
        self.assertIn('No fue posible re-extraer la OC documental', chatter)
        self.assertNotIn('Traceback', chatter)

    # ── 3. Opción 3 — failsafe del valor previo ────────────────────────────
    def test_reopen_to_draft_failsafe_valor_previo_ante_fallo_extraccion(self):
        """Sin re-extracción posible y con OC previa, se conserva el resguardo."""
        guia = self._make_guia('B1-OC-FAILSAFE', b'%PDF-fake no legible')
        guia.write({'oc_reference_raw': 'OC-TEST-999'})

        self.env['madenat.guia.processing.reopen.wizard'].create(
            {'guia_processing_id': guia.id,
             'reason': 'Reapertura de prueba'}).action_confirm()
        guia.invalidate_recordset()

        self.assertEqual(guia.state, 'draft')
        self.assertEqual(
            guia.oc_reference_raw, 'OC-TEST-999',
            'El failsafe debe conservar el valor previo como resguardo')
        chatter = self._chatter(guia)
        self.assertIn('se conservó el valor previo', chatter)
        self.assertIn('OC-TEST-999', chatter)
        # El resguardo NO finge una vinculación de OC no re-confirmada.
        self.assertFalse(guia.order_id)
        self.assertEqual(guia.oc_match_status, 'not_found')
