# -*- coding: utf-8 -*-
"""Cierre de avisos y compatibilidad de la validación de guías (2026-10-07).

Cubre:
  - Aviso no bloqueante de homónimo en la ruta de **Recepción** (equivalente al
    de Procesado), en ambos sentidos.
  - **Prevención de avisos repetidos**: sin cambio de identidad no hay nuevo aviso.
  - **Compatibilidad** de los llamadores de ``_check_guide_duplicate`` (C1).

Aislado, usuario operativo real, sin superusuario. ``TransactionCase``.
"""
import base64
import logging

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.addons.madenat_lumber_core.models.reception_workflow import (
    LumberReceptionWorkflow)

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'guide_duplicate_warnings')
class TestGuideDuplicateWarnings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Parser = cls.env['madenat.reception.parser']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Reception = cls.env['lumber.reception']
        cls.location = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1).lot_stock_id
        if not cls.location:
            cls.location = cls.env['stock.location'].search(
                [('usage', '=', 'internal')], limit=1)
        cls.pa = cls.env['res.partner'].create(
            {'name': 'WARN-PA', 'is_company': True})
        cls.pb = cls.env['res.partner'].create(
            {'name': 'WARN-PB', 'is_company': True})
        cls.pc = cls.env['res.partner'].create(
            {'name': 'WARN-PC', 'is_company': True})
        cls.u_ops = new_test_user(
            cls.env, login='gwarn_ops',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_operaciones')
        cls.wf = LumberReceptionWorkflow(cls.env)

    # ── Helpers ───────────────────────────────────────────────────────────
    def _guia(self, name, partner=None):
        return self.Guia.create({
            'name': name, 'partner_id': (partner or self.pa).id,
            'assignment_location_id': self.location.id,
            'date_emission': '2026-06-11'})

    def _guia_incomplete(self, partner=None, user=None):
        model = self.Guia if user is None else self.Guia.with_user(user)
        vals = {'assignment_location_id': self.location.id,
                'date_emission': '2026-06-11'}
        if partner is not None:
            vals['partner_id'] = partner.id
        return model.create(vals)

    def _reception(self, name=None):
        vals = {'pdf_file': base64.b64encode(b'%PDF-1.4 dummy'),
                'excel_file': base64.b64encode(b'dummy'),
                'excel_filename': 'packing.xlsx', 'pdf_filename': 'guia.pdf',
                'supplier_id': self.pa.id}
        if name:
            vals['name'] = name
        return self.Reception.create(vals)

    @staticmethod
    def _homonym_msgs(rec):
        return rec.message_ids.filtered(
            lambda m: 'coincidente' in (m.body or ''))

    # ── Avisos en ambos sentidos ──────────────────────────────────────────
    def test_w1_guia_homonym_warns_reception(self):
        """Guía cuyo N° coincide con una recepción → avisa 'Recepción directa'."""
        self._reception('WR-01')
        g = self._guia_incomplete(user=self.u_ops)
        g.with_user(self.u_ops).write(
            {'name': 'WR-01', 'partner_id': self.pb.id})
        warns = self._homonym_msgs(g)
        self.assertTrue(warns, "La guía debe advertir el homónimo con la recepción")
        self.assertIn('Recepción directa', warns[0].body or '')
        self.assertEqual(g.name, 'WR-01')  # no bloqueó

    def test_w2_reception_homonym_warns_guia(self):
        """Recepción cuyo N° coincide con una guía de emisor DISTINTO → avisa
        'Guía Procesada' (homónimo legítimo, no bloquea)."""
        self._guia('WG-01', self.pb)                 # emisor distinto al de la recepción
        r = self._reception()                        # supplier_id = self.pa
        self.wf._check_duplicate_and_warn(r, 'WG-01')
        warns = self._homonym_msgs(r)
        self.assertTrue(warns, "La recepción debe advertir el homónimo con la guía")
        self.assertIn('Guía Procesada', warns[0].body or '')

    # ── Prevención de avisos repetidos ────────────────────────────────────
    def test_w3_guia_warning_not_repeated_without_change(self):
        """Guardar/releer un campo ajeno sin cambio de identidad no repite el aviso."""
        self._guia('GD-01', self.pa)
        g = self._guia_incomplete(self.pb, user=self.u_ops)
        g.with_user(self.u_ops).write({'name': 'GD-01', 'partner_id': self.pb.id})
        self.assertEqual(len(self._homonym_msgs(g)), 1)
        g.with_user(self.u_ops).write({'name': 'GD-01'})            # sin cambio
        g.with_user(self.u_ops).write({'date_emission': '2026-06-30'})  # campo ajeno
        self.assertEqual(len(self._homonym_msgs(g)), 1)

    def test_w4_guia_warning_on_real_identity_change(self):
        """Cambio real de identidad → nuevo aviso pertinente."""
        self._guia('GD-02', self.pa)
        g = self._guia_incomplete(self.pb, user=self.u_ops)
        g.with_user(self.u_ops).write({'name': 'GD-02', 'partner_id': self.pb.id})
        self.assertEqual(len(self._homonym_msgs(g)), 1)
        g.with_user(self.u_ops).write({'partner_id': self.pc.id})   # cambio real
        self.assertEqual(len(self._homonym_msgs(g)), 2)

    def test_w5_reception_warning_not_repeated_when_number_unchanged(self):
        """Recepción: guardar/releer el mismo número no repite el aviso (emisor
        distinto → homónimo no bloqueante)."""
        self._guia('RN-01', self.pb)                 # emisor distinto al de la recepción
        r = self._reception()                        # supplier_id = self.pa
        self.wf._check_duplicate_and_warn(r, 'RN-01')
        self.assertEqual(len(self._homonym_msgs(r)), 1)
        r.write({'name': 'RN-01'})                 # el número queda almacenado
        self.wf._check_duplicate_and_warn(r, 'RN-01')   # relectura/reintento
        self.assertEqual(len(self._homonym_msgs(r)), 1)

    # ── Compatibilidad y seguridad ────────────────────────────────────────
    def test_w6_reception_confirmed_duplicate_still_blocks(self):
        """Compatibilidad: el duplicado confirmado (mismo modelo) sigue bloqueando."""
        self._reception('CD-01')
        r2 = self._reception()
        with self.assertRaises(UserError):
            self.wf._check_duplicate_and_warn(r2, 'CD-01')

    def test_w7_warning_does_not_leak_other_record_data(self):
        """El aviso no expone datos del otro documento (sólo el N° conocido)."""
        reception = self._reception('LK-01')       # supplier_id = WARN-PA
        g = self._guia_incomplete(self.pb, user=self.u_ops)
        g.with_user(self.u_ops).write({'name': 'LK-01', 'partner_id': self.pb.id})
        warns = self._homonym_msgs(g)
        self.assertTrue(warns)
        body = warns[0].body or ''
        self.assertNotIn(str(reception.id), body)
        self.assertNotIn('WARN-PA', body)

    def test_w8_warning_rolls_back_with_operation(self):
        """Atomicidad: si la operación falla, el aviso no queda registrado (emisor
        distinto → homónimo no bloqueante)."""
        self._guia('RB-01', self.pb)                 # emisor distinto al de la recepción
        r = self._reception()
        try:
            with self.env.cr.savepoint():
                self.wf._check_duplicate_and_warn(r, 'RB-01')
                raise UserError('fallo posterior simulado')
        except UserError:
            pass
        n = self.env['mail.message'].search_count([
            ('model', '=', 'lumber.reception'), ('res_id', '=', r.id),
            ('body', 'like', 'coincidente')])
        self.assertEqual(n, 0)

    def test_w9_shared_warning_on_both_models(self):
        """El aviso vive en el mixin compartido por Recepción y Guía."""
        self.assertTrue(hasattr(self.env['lumber.reception'],
                                '_warn_guide_homonym'))
        self.assertTrue(hasattr(self.env['madenat.guia.processing'],
                                '_warn_guide_homonym'))

    def test_w10_caller_contract_reception_default(self):
        """Compatibilidad de C1: la ruta de Recepción (por defecto) NO bloquea un
        homónimo de guía; SÍ bloquea su propio duplicado confirmado."""
        self._guia('CO-01', self.pa)
        self.Parser._check_guide_duplicate('CO-01')      # homónimo → no bloquea
        self._reception('CO-02')
        with self.assertRaises(UserError):
            self.Parser._check_guide_duplicate('CO-02')  # mismo modelo → bloquea

