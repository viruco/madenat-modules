# -*- coding: utf-8 -*-
"""P0-R (F-01) — ACL mínimas y segregación funcional del Programa SV.

Remediación del hallazgo bloqueante F-01: `madenat.sv.operation` y los cuatro
asistentes SV carecían de ACL y resultaban inaccesibles para cualquier usuario
no superusuario.

Cubre T-P0R-ACL-01 .. T-P0R-ACL-06. Datos aislados; no se toca la Guía 4495589
ni la etiqueta SV00000000008.
"""
import os

from odoo.exceptions import AccessError, ValidationError
from odoo.modules.module import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

SV_LEDGER = 'madenat.sv.operation'
SV_WIZARDS = (
    'madenat.sv.rename.wizard',
    'madenat.sv.volume.regularize.wizard',
    'madenat.sv.rebaja.wizard',
    'madenat.sv.rebaja.reverse.wizard',
)
INTERNAL_MODELS = (
    'madenat.sv.internal.capability',
    'madenat.sv.internal.marker',
)
# Módulos que P0-R NO puede tocar en ACL (paquetes P1..P10 y vecinos).
OUT_OF_SCOPE_TOKENS = (
    'madenat_lumber_costing', 'madenat_lumber_intake', 'madenat_lumber_billing',
    'madenat_lumber_purchasing', 'madenat_lumber_logistics',
    'madenat_ingestion_engine', 'madenat_lumber_reports',
    'madenat_toll_processing',
)
# Grupos admitidos por las ACL del Programa SV (P0-R).
SV_ALLOWED_GROUPS = {
    'base.group_user', 'base.group_system',
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_auditoria',
    'madenat_lumber_core.group_madenat_contabilidad',
}


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'sv', 'p0r')
class TestP0rAcl(SvTestCommon, TransactionCase):
    """ACL mínimas por grupo funcional y blindaje de modelos internos."""

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

    # ── Utilidades ────────────────────────────────────────────────────────
    def _make_user(self, login, groups):
        return self.env['res.users'].create({
            'name': login,
            'login': login,
            'groups_id': [(6, 0, [self.group_user.id]
                           + [group.id for group in groups])],
        })

    def _acl(self, model, group):
        return self.env['ir.model.access'].sudo().search([
            ('model_id.model', '=', model),
            ('group_id', '=', group.id),
        ])


    # ── T-P0R-ACL-01 ──────────────────────────────────────────────────────
    def test_01_operaciones_usa_ledger_y_wizards(self):
        """Operaciones abre/crea el ledger y usa cada asistente SV."""
        guia = self._sv_make_guia('P0R-ACL-01')
        lot = self._sv_make_lot(guia, label='SV00000000501')
        user = self._make_user('p0r_oper_01', [self.group_oper])

        # Lectura del ledger.
        self.Operation.with_user(user).search([('lot_id', '=', lot.id)])

        # Creación + aplicación de una operación permitida por el flujo.
        op = self.Operation.with_user(user).create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Rebaja P0-R ACL-01',
        })
        op.with_user(user).action_apply()
        op.invalidate_recordset()
        self.assertEqual(op.state, 'applied')

        # Asistente de rebaja.
        wizard = self.env['madenat.sv.rebaja.wizard'].with_user(user).create({
            'lot_id': lot.id,
            'rebaja_volume_m3': 1.0,
            'reason': 'Wizard rebaja P0-R',
        })
        wizard.with_user(user).action_submit()

        # Asistente de regularización (sin alza de baseline → sin aprobación).
        reg = self.env[
            'madenat.sv.volume.regularize.wizard'].with_user(user).create({
                'lot_id': lot.id,
                'new_volume_m3': 39.0,
                'reason': 'Regularización P0-R',
                'evidence_reference': 'RESP-P0R-01',
            })
        reg.with_user(user).action_submit()

        # Asistente de rename.
        rename = self.env['madenat.sv.rename.wizard'].with_user(user).create({
            'lot_id': lot.id,
            'new_label': 'SV00000000502',
            'reason': 'Rename P0-R',
        })
        rename.with_user(user).action_submit()
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000502')

        # Asistente de reversa de rebaja (sobre una rebaja aplicada).
        rebaja = self._sv_rebaja(lot, 2.0)
        reverse = self.env[
            'madenat.sv.rebaja.reverse.wizard'].with_user(user).create({
                'origin_operation_id': rebaja.id,
                'reason': 'Reversa P0-R',
            })
        reverse.with_user(user).action_submit()
        rebaja.invalidate_recordset()

    # ── T-P0R-ACL-02 ──────────────────────────────────────────────────────
    def test_02_auditoria_solo_acciones_permitidas(self):
        """Auditoría aprueba/aplica lo suyo; no elimina ni bypass de estado."""
        guia = self._sv_make_guia('P0R-ACL-02')
        lot = self._sv_make_lot(guia, label='SV00000000503')
        user_audit = self._make_user('p0r_audit_02', [self.group_audit])

        # Alza de baseline documental: exige Auditoría.
        op = self.Operation.with_user(user_audit).create({
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': 45.0,
            'reason': 'Alza documental P0-R',
            'evidence_reference': 'RESP-P0R-02',
        })
        self.assertIn('auditoria', op._sv_required_approval_groups())
        op.with_user(user_audit).action_apply()
        op.invalidate_recordset()
        self.assertEqual(op.state, 'applied')

        # Auditoría puede leer el ledger pero no eliminarlo.
        acl = self._acl(SV_LEDGER, self.group_audit)
        self.assertTrue(acl)
        self.assertTrue(acl.perm_read)
        self.assertFalse(acl.perm_unlink)
        draft = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Borrador P0-R',
        })
        with self.assertRaises(AccessError):
            draft.with_user(user_audit).unlink()

    # ── T-P0R-ACL-03 ──────────────────────────────────────────────────────
    def test_03_contabilidad_conserva_restricciones(self):
        """Contabilidad no obtiene permisos no autorizados sobre stock."""
        guia = self._sv_make_guia('P0R-ACL-03')
        self._sv_make_lot(guia, label='SV00000000504')
        user_cont = self._make_user('p0r_cont_03', [self.group_cont])

        acl = self._acl(SV_LEDGER, self.group_cont)
        self.assertTrue(acl)
        self.assertFalse(acl.perm_unlink)
        # Contabilidad no tiene permiso de creación de stock nativo.
        with self.assertRaises(AccessError):
            self.env['stock.picking'].with_user(user_cont).create({
                'picking_type_id': self.warehouse.out_type_id.id,
                'location_id': self.internal_loc.id,
                'location_dest_id': self.customer_loc.id,
            })

    # ── T-P0R-ACL-04 ──────────────────────────────────────────────────────
    def test_04_usuario_sin_grupo_no_ejecuta_ni_forja(self):
        """Interno sin grupo funcional no ejecuta ni falsifica contexto."""
        guia = self._sv_make_guia('P0R-ACL-04')
        lot = self._sv_make_lot(guia, label='SV00000000505')
        user = self._make_user('p0r_plain_04', [])

        # Sin grupo funcional no puede crear operaciones del ledger.
        with self.assertRaises(AccessError):
            self.Operation.with_user(user).create({
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 1.0,
                'reason': 'Intento no autorizado',
            })
        # Contexto forjado no habilita la escritura protegida del lote.
        for context in ({'force_validate': True},
                        {'skip_immediate': True, 'immediate_transfer': True},
                        {'madenat_sv_rename': True}):
            with self.assertRaises(ValidationError):
                lot.with_context(**context).write({'name': 'SV00000000599'})

    # ── T-P0R-ACL-05 ──────────────────────────────────────────────────────
    def test_05_modelos_internos_sin_acceso_publico(self):
        """capability/marker sin ACL, vista, acción ni menú públicos."""
        for model in INTERNAL_MODELS:
            self.assertFalse(self.env['ir.model.access'].sudo().search([
                ('model_id.model', '=', model)]),
                '%s no debe tener ACL' % model)
            self.assertFalse(self.env['ir.actions.act_window'].sudo().search([
                ('res_model', '=', model)]),
                '%s no debe tener acción' % model)
            self.assertFalse(self.env['ir.ui.view'].sudo().search([
                ('model', '=', model)]),
                '%s no debe tener vista' % model)
        user = self._make_user('p0r_plain_05', [])
        with self.assertRaises(AccessError):
            self.env['madenat.sv.internal.capability'].with_user(
                user).search([])
        with self.assertRaises(AccessError):
            self.env['madenat.sv.internal.marker'].with_user(user).search([])

    # ── T-P0R-ACL-06 ──────────────────────────────────────────────────────
    def test_06_sin_acl_ni_dependencias_fuera_de_core(self):
        """El manifiesto y el CSV de Core no arrastran módulos fuera de P0-R."""
        module_path = get_module_path('madenat_lumber_core')
        self.assertTrue(module_path)
        with open(os.path.join(
                module_path, 'security', 'ir.model.access.csv')) as handle:
            csv_text = handle.read()
        for token in OUT_OF_SCOPE_TOKENS:
            self.assertNotIn(
                token, csv_text,
                'ACL fuera de alcance en P0-R: %s' % token)
        # Las ACL del Programa SV referencian SOLO grupos funcionales de Core.
        sv_rows = [
            line.split(',') for line in csv_text.splitlines()[1:]
            if line.strip() and 'madenat_sv' in line.split(',')[2]
        ]
        self.assertEqual(len(sv_rows), 17)
        # CSV estándar Odoo: id,name,model_id:id,group_id:id,perm_*.
        # F-P0R-C: el grupo es la columna 3; antes se leía `perm_read` (cols[4]).
        for cols in sv_rows:
            self.assertIn(
                cols[3], SV_ALLOWED_GROUPS,
                'Grupo fuera de alcance en ACL SV: %s' % cols[3])
        # Las ACL mínimas requeridas están presentes.
        for model in (SV_LEDGER,) + SV_WIZARDS:
            self.assertTrue(self.env['ir.model.access'].sudo().search([
                ('model_id.model', '=', model)]),
                'Falta ACL de %s' % model)
        # El manifiesto no depende de paquetes P1..P10.
        manifest = self.env['ir.module.module'].sudo().search_read(
            [('name', '=', 'madenat_lumber_core')],
            ['dependencies_id'])[0]
        depends = self.env['ir.module.module.dependency'].sudo().browse(
            manifest['dependencies_id']).mapped('name')
        for name in depends:
            self.assertNotIn(name, OUT_OF_SCOPE_TOKENS)
