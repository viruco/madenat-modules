# -*- coding: utf-8 -*-
"""P3 — Saldos ALMACENADOS canónicos e independencia del usuario (AUD-ETQ-10).

Semántica:
* `sv_assignment_nominal_m3` / `_applied_m3` / `_applied_count` /
  `_documental_balance_m3` = **agregados canónicos ALMACENADOS** (`store=True`,
  `compute_sudo=True`): el MISMO valor para todos los usuarios, independiente de
  quién dispare el recompute.
* `sv_assignment_imputation_ids` / `sv_assignment_processor_id` = proyección NO
  almacenada **por usuario** (`store=False`, `compute_sudo=False`).

Se verifica que un usuario con acceso a `stock.lot` pero SIN acceso a
`madenat.sv.imputation` (ACL por rol) pueda disparar la recomputación **sin**
`AccessError` y **sin** corromper el saldo canónico, y que no haya exposición
entre compañías. `TransactionCase` (rollback).
"""
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvAssignmentUserRights(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'P3 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'P3 Supplier', 'is_company': True})
        cls.user_restricted = cls.env['res.users'].create({
            'name': 'p3_restricted', 'login': 'p3_restricted',
            'email': 'p3r@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('stock.group_stock_user').id])]})
        cls.user_jef = cls.env['res.users'].create({
            'name': 'p3_jef', 'login': 'p3_jef', 'email': 'p3j@madenat.cl',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_jefatura_operaciones'
                ).id])]})

    def _applied(self, tag='P3'):
        guia = self.env['madenat.guia.processing'].create({
            'name': '%s-G' % tag, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})
        etq = self.env['stock.lot'].create({
            'name': '%s-E' % tag, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': 10.0})
        guia.write({'lot_ids': [(4, etq.id)]})
        sv = self.env['stock.lot'].create({
            'name': '%s-SV' % tag, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': 100.0})
        imp = self.env['madenat.sv.imputation'].create({
            'guia_processing_id': guia.id, 'company_id': self.company.id})
        line = self.env['madenat.sv.imputation.line'].create({
            'imputation_id': imp.id, 'processed_lot_id': etq.id,
            'nominal_volume_m3': 6.0})
        self.env['madenat.sv.imputation.sv.line'].create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 6.0})
        # FASE 11 (A-1): el estado `applied` se alcanza por la acción OFICIAL
        # (la escritura directa de `state` está prohibida).
        imp.with_user(self.user_jef).action_apply()
        imp.invalidate_recordset()
        sv.invalidate_recordset()
        return sv

    def test_p3_stored_canonical_independiente_del_usuario(self):
        sv = self._applied()
        field = self.env['stock.lot']._fields['sv_assignment_applied_m3']
        # 1) Valor canónico inicial.
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 6.0, 3)
        self.assertEqual(sv.sv_assignment_applied_count, 1)
        # 2) El usuario restringido NO lee las imputaciones (ACL por rol)...
        with self.assertRaises(AccessError):
            self.env['madenat.sv.imputation'].with_user(
                self.user_restricted).search_count([('id', '>', 0)])
        # ...ni puede escribir el lote SV (guard del core): NO existe una vía
        #    normal por la que un usuario parcial dispare el recompute.
        with self.assertRaises(ValidationError):
            sv.with_user(self.user_restricted).write(
                {'volume_purchase_m3': 100.0})
        # 3) Forzando el recompute del ORM bajo el usuario restringido
        #    (`add_to_compute` + lectura, igual que haría un write), el saldo se
        #    mantiene CANÓNICO (compute_sudo=True) y SIN AccessError.
        sv_r = sv.with_user(self.user_restricted)
        sv_r.env.add_to_compute(field, sv_r)
        sv_r.invalidate_recordset(['sv_assignment_applied_m3'])
        self.assertAlmostEqual(
            sv_r.sv_assignment_applied_m3, 6.0, 3,
            msg='El saldo almacenado debe ser canónico (mismo para todos)')
        self.assertEqual(sv_r.sv_assignment_applied_count, 1)
        # 4) La proyección NO almacenada es POR USUARIO: el restringido recibe
        #    AccessError (no se filtra el documento); el autorizado la lee.
        with self.assertRaises(AccessError):
            sv_r.sv_assignment_imputation_ids
        self.assertTrue(sv.sv_assignment_imputation_ids)
        # 5) El recompute tras una transición AUTORIZADA (reversa) sí actualiza
        #    el saldo canónico (refleja la realidad documental).
        imp = self.env['madenat.sv.imputation'].search(
            [('sv_line_ids.sv_lot_id', '=', sv.id)], limit=1)
        imp.reason = 'P3'
        imp.with_user(self.user_jef).action_reverse()
        sv.invalidate_recordset()
        self.assertAlmostEqual(sv.sv_assignment_applied_m3, 0.0, 3)
        self.assertEqual(sv.sv_assignment_applied_count, 0)

    def test_p3_sin_exposicion_entre_companias(self):
        sv = self._applied('P3B')
        company_b = self.env['res.company'].create({'name': 'P3 Compañía B'})
        user_b = self.env['res.users'].create({
            'name': 'p3_company_b', 'login': 'p3_company_b',
            'email': 'p3b@madenat.cl', 'company_id': company_b.id,
            'company_ids': [(6, 0, [company_b.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('stock.group_stock_user').id])]})
        self.assertEqual(self.env['stock.lot'].with_user(user_b).search_count(
            [('id', '=', sv.id)]), 0)
        with self.assertRaises(AccessError):
            self.env['stock.lot'].with_user(user_b).browse(sv.id).read(
                ['sv_assignment_applied_m3'])
