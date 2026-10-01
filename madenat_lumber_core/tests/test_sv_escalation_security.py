# -*- coding: utf-8 -*-
"""Programa SV — escalamiento funcional y seguridad server-side."""

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvEscalationSecurity(SvTestCommon, TransactionCase):
    """Operaciones directas, escalamiento a Auditoría/Contabilidad y bypass."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()
        cls.group_oper = cls.env.ref(
            'madenat_lumber_core.group_madenat_operaciones')
        cls.group_audit = cls.env.ref(
            'madenat_lumber_core.group_madenat_auditoria')
        cls.group_cont = cls.env.ref(
            'madenat_lumber_core.group_madenat_contabilidad')
        cls.group_user = cls.env.ref('base.group_user')

    def _make_user(self, login, groups):
        return self.env['res.users'].create({
            'name': login,
            'login': login,
            'groups_id': [(6, 0, [self.group_user.id]
                           + [group.id for group in groups])],
        })

    def _add_cost_line(self, lot, amount=100.0):
        return self.env['stock.lot.cost.line'].create({
            'name': 'Costo de prueba SV',
            'lot_id': lot.id,
            'cost_type': 'wood',
            'amount_usd': amount,
        })

    def test_01_operacion_rutinaria_directa_por_operaciones(self):
        guia = self._sv_make_guia('SV-SEC-01')
        lot = self._sv_make_lot(guia, label='SV00000000111')
        user_oper = self._make_user('sv_oper_01', [self.group_oper])

        operation = self.Operation.with_user(user_oper).create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 10.0,
            'reason': 'Rebaja operativa rutinaria',
        })
        self.assertFalse(operation._sv_pending_approval_groups())
        operation.with_user(user_oper).action_apply()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')

    def test_02_costo_exige_contabilidad(self):
        guia = self._sv_make_guia('SV-SEC-02')
        lot = self._sv_make_lot(guia, label='SV00000000112')
        self._add_cost_line(lot)
        user_oper = self._make_user('sv_oper_02', [self.group_oper])
        user_cont = self._make_user('sv_cont_02', [self.group_cont])

        operation = self.Operation.with_user(user_oper).create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 5.0,
            'reason': 'Rebaja con costo registrado',
        })
        self.assertIn('contabilidad', operation._sv_required_approval_groups())
        with self.assertRaises(AccessError):
            operation.with_user(user_oper).action_apply()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'draft')
        # Contabilidad sí puede aprobar y aplicar.
        operation.with_user(user_cont).action_apply()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')
        self.assertEqual(operation.approved_by_id, user_cont)

    def test_03_alza_de_baseline_exige_auditoria(self):
        guia = self._sv_make_guia('SV-SEC-03')
        lot = self._sv_make_lot(guia, label='SV00000000113')
        user_oper = self._make_user('sv_oper_03', [self.group_oper])
        user_audit = self._make_user('sv_audit_03', [self.group_audit])

        operation = self.Operation.with_user(user_oper).create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 45.0,
            'reason': 'Alza documental',
            'evidence_reference': 'RESP-03',
        })
        self.assertIn('auditoria', operation._sv_required_approval_groups())
        with self.assertRaises(AccessError):
            operation.with_user(user_oper).action_apply()
        operation.with_user(user_audit).action_apply()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_regularized_baseline_m3, 45.0, places=3)

    def test_04_auditoria_y_contabilidad_por_dos_personas(self):
        guia = self._sv_make_guia('SV-SEC-04')
        lot = self._sv_make_lot(guia, label='SV00000000114')
        self._add_cost_line(lot, 50.0)
        user_audit = self._make_user('sv_audit_04', [self.group_audit])
        user_cont = self._make_user('sv_cont_04', [self.group_cont])
        user_oper = self._make_user('sv_oper_04', [self.group_oper])

        operation = self.Operation.with_user(user_audit).create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 44.0,
            'reason': 'Alza documental con costo',
            'evidence_reference': 'RESP-04',
        })
        required = operation._sv_required_approval_groups()
        self.assertIn('auditoria', required)
        self.assertIn('contabilidad', required)

        operation.with_user(user_audit).action_register_approval()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'draft')
        self.assertEqual(operation.approved_by_id, user_audit)
        # Con una sola aprobación nadie (ni Operaciones) puede aplicar.
        with self.assertRaises(AccessError):
            operation.with_user(user_oper).action_apply()
        # La segunda aprobación funcional completa y aplica.
        operation.with_user(user_cont).action_apply()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, 'applied')
        self.assertEqual(operation.approved_by_id_secondary, user_cont)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_regularized_baseline_m3, 44.0, places=3)

    def test_05_bypass_orm_y_acl_del_historial(self):
        guia = self._sv_make_guia('SV-SEC-05')
        lot = self._sv_make_lot(guia, label='SV00000000115')
        user_oper = self._make_user('sv_oper_05', [self.group_oper])

        # Escritura directa de campos protegidos: bloqueada server-side.
        with self.assertRaises(ValidationError):
            lot.write({'name': 'SV00000000116'})
        with self.assertRaises(ValidationError):
            lot.write({'volumen_m3': 99.0})
        with self.assertRaises(ValidationError):
            lot.write({'piezas': 99})

        # Historial aplicado: no editable ni eliminable.
        operation = self._sv_rebaja(lot, 1.0)
        with self.assertRaises(ValidationError):
            operation.write({'rebaja_volume_m3': 2.0})
        with self.assertRaises(ValidationError):
            operation.unlink()

        # ACL: Operaciones no puede eliminar borradores del ledger.
        draft = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Borrador de prueba',
        })
        with self.assertRaises(AccessError):
            draft.with_user(user_oper).unlink()
        acl = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'madenat.sv.operation'),
            ('group_id', '=', self.group_oper.id)], limit=1)
        self.assertTrue(acl)
        self.assertFalse(acl.perm_unlink)
