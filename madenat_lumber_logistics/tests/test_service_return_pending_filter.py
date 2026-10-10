# -*- coding: utf-8 -*-
"""Filtro «Retornos sin imputación aplicada» (2026-10-07).

Deriva "pendiente" de la relación real con `madenat.sv.imputation` y su estado:
sólo una imputación APLICADA cuenta como imputación aplicada
(`I2_DOCUMENTAL_STATES = ('applied',)`, D-I2-13). Los estados borrador,
pendiente, anulada y reversada NO cuentan.

LIMITACIÓN documentada: el filtro detecta "sin imputación aplicada" y NO evalúa
la cobertura PARCIAL del volumen (una imputación aplicada que no cubra todo el
nominal no se marca pendiente). TransactionCase: nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestServiceReturnPendingFilter(TransactionCase):
    """Separación retorno/no retorno/no confirmado y «sin imputación aplicada»."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.partner = cls.env['res.partner'].create({
            'name': 'SrvRet Pend', 'is_company': True})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)

    def _guia(self, name, confirm='yes', tipo='service', state='validated'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo, 'state': state,
            'service_return_confirmation': confirm or False,
        })

    def _imp(self, guia, state='draft'):
        return self.Imputation.sudo().create({
            'guia_processing_id': guia.id, 'state': state})

    def _pending(self):
        return self.Guia.search([
            ('tipo_recepcion', '=', 'service'),
            ('service_return_confirmation', '=', 'yes'),
            ('sv_imputation_ids', 'not any', [('state', '=', 'applied')]),
        ])

    def test_01_sin_imputacion_es_pendiente(self):
        g = self._guia('PEND-01')
        self.assertIn(g.id, self._pending().ids)

    def test_02_borrador_no_es_aplicada(self):
        g = self._guia('PEND-02')
        self._imp(g, 'draft')
        self.assertIn(g.id, self._pending().ids)

    def test_03_anulada_no_es_aplicada(self):
        g = self._guia('PEND-03')
        self._imp(g, 'cancelled')
        self.assertIn(g.id, self._pending().ids)

    def test_04_reversada_no_es_aplicada(self):
        g = self._guia('PEND-04')
        self._imp(g, 'reversed')
        self.assertIn(g.id, self._pending().ids)

    def test_05_aplicada_no_es_pendiente(self):
        g = self._guia('PEND-05')
        self._imp(g, 'applied')
        self.assertNotIn(g.id, self._pending().ids)

    def test_06_no_retorno_no_entra(self):
        g = self._guia('PEND-06', confirm='no')
        self.assertNotIn(g.id, self._pending().ids)

    def test_07_sin_confirmar_no_entra(self):
        g = self._guia('PEND-07', confirm=None)
        self.assertNotIn(g.id, self._pending().ids)

    def test_08_compra_fuera_de_alcance(self):
        g = self._guia('PEND-08', tipo='compra')
        self.assertNotIn(g.id, self._pending().ids)

    def test_09_help_declara_limite_parcial(self):
        view = self.env.ref(
            'madenat_lumber_logistics.'
            'view_madenat_guia_processing_search_service_return')
        arch = (view.arch or '').lower()
        self.assertIn('filter_service_return_pending_imputation', arch)
        self.assertIn('cobertura parcial', arch)
