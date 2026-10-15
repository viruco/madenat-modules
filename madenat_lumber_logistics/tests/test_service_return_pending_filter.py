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
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.partner = cls.env['res.partner'].create({
            'name': 'SrvRet Pend', 'is_company': True})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        # FASE 11 (A-1/B-1): los estados se alcanzan con las acciones OFICIALES,
        # que exigen payload mínimo válido y rol funcional.
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'PEND Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.user_oper = cls._mk('pend_oper', [
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('pend_jef', [
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.test' % name,
            'company_id': cls.env.company.id,
            'company_ids': [(6, 0, [cls.env.company.id])],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id]
                              + [cls.env.ref(g).id for g in groups])]})

    def _guia(self, name, confirm='yes', tipo='service', state='validated'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo, 'state': state,
            'service_return_confirmation': confirm or False,
        })

    def _imp(self, guia, state='draft'):
        """Crea la imputación y alcanza el estado pedido por VÍAS OFICIALES.

        FASE 11 (A-1/B-1): la escritura directa de `state` está prohibida; cada
        estado se obtiene con su acción (con un payload mínimo válido —etiqueta
        + reparto positivo a un SV— cuando la acción lo exige).
        """
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        if state == 'draft':
            return imp
        if state == 'cancelled':
            imp.with_user(self.user_oper).action_cancel(
                reason='PEND: anulación de prueba')
            imp.invalidate_recordset()
            return imp
        etq = self.env['stock.lot'].sudo().create({
            'name': 'PEND-E-%s' % guia.id, 'product_id': self.product.id,
            'company_id': self.env.company.id, 'lot_flow_type': 'tarja',
            'ref': 'PEND-E-%s' % guia.id, 'volume_purchase_m3': 10.0,
            'vol_shipment_m3': 10.0})
        guia.sudo().write({'lot_ids': [(4, etq.id)]})
        sv = self.env['stock.lot'].sudo().create({
            'name': 'SVPEND%s' % guia.id, 'product_id': self.product.id,
            'company_id': self.env.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': 100.0,
            'vol_shipment_m3': 100.0})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': etq.id,
            'nominal_volume_m3': 10.0})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 10.0})
        if state == 'pending':
            imp.with_user(self.user_oper).action_pending()
        elif state == 'applied':
            imp.with_user(self.user_oper).action_apply()
        elif state == 'reversed':
            imp.with_user(self.user_oper).action_apply()
            imp.with_user(self.user_jef).action_reverse(
                reason='PEND: reversa de prueba')
        imp.invalidate_recordset()
        return imp

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
