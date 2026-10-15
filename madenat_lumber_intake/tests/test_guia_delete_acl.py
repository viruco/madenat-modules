# -*- coding: utf-8 -*-
"""Fallo de acceso omitido en la eliminación (Modo A) — ACL real.

Reproduce el rechazo observado con el **usuario operativo y `su=False`**:

    No puede eliminar registros 'Recepción de Guías Procesadas'
    (madenat.guia.processing). Ningún grupo permite esta operación.

Causa: la ACL `ir.model.access` de `madenat.guia.processing` no concedía
`perm_unlink` a NINGÚN grupo (0 en las tres filas). El asistente (Modo A) llama
`guia.unlink()` como el usuario de la sesión; el override del core ejecuta sus
guardas y termina en `super().unlink()`, donde Odoo 18 hace
`check_access('unlink')` (`models.py`), que al no hallar grupo devuelve el
`AccessError` reportado.

Estas pruebas se ejecutan **sin `sudo`** (`with_user(...)`, `su=False`) y con el
usuario operativo, que es lo que la suite anterior omitía (corría como
superusuario, con la ACL de `unlink` puenteada por `env.su`).
"""

import uuid

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestGuiaDeleteAcl(TransactionCase):
    """ACL de `unlink` sobre `madenat.guia.processing` con el usuario real."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env['madenat.lumber.intake.guide.lifecycle']
        cls.AuditLog = cls.env['madenat.audit.log']
        grp_oper = cls.env.ref(
            'madenat_lumber_core.group_madenat_operaciones')
        grp_jef = cls.env.ref(
            'madenat_lumber_core.group_madenat_jefatura_operaciones')
        grp_mgr = cls.env.ref('stock.group_stock_manager')
        suffix = uuid.uuid4().hex[:8]

        def _mk_user(label, groups):
            return cls.env['res.users'].create({
                'name': 'ACL %s' % label,
                'login': 'acl_%s_%s@test.local' % (label, suffix),
                'groups_id': [(6, 0, [g.id for g in groups])],
            })

        # Autorizado: Jefatura (ACL unlink) + Inventario/Administrador (guarda core).
        cls.user_authorized = _mk_user(
            'auth', [cls.env.ref('base.group_user'), grp_oper, grp_jef, grp_mgr])
        # Sin ACL de unlink: Operaciones + Inventario/Administrador (pasa la
        # guarda del core pero NO tiene el permiso de borrado).
        cls.user_no_acl = _mk_user(
            'noacl', [cls.env.ref('base.group_user'), grp_oper, grp_mgr])
        # Sin guarda del core: Operaciones (sin Jefatura ni stock_manager).
        cls.user_no_stock = _mk_user(
            'nostock', [cls.env.ref('base.group_user'), grp_oper])

        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor ACL Borrado', 'is_company': True})

    def _make_guia(self, name, state='cancelled'):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.warehouse.lot_stock_id.id,
            'state': state,
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared',
            'volume_pdf_m3': 40.315,
        })

    def _wizard(self, user, guia, mode='A', **extra):
        vals = {
            'guia_processing_id': guia.id,
            'mode': mode,
            'reason': 'Prueba de ACL de eliminación',
        }
        vals.update(extra)
        return self.Wizard.with_user(user).create(vals)

    # ── 1. La ACL concede el permiso al rol correcto y solo a él ──────────
    def test_01_acl_grants_unlink_to_jefatura_only(self):
        Guia = self.Guia
        self.assertTrue(
            Guia.with_user(self.user_authorized).has_access('unlink'),
            'Jefatura de Operaciones debe tener unlink tras la corrección')
        self.assertFalse(
            Guia.with_user(self.user_no_acl).has_access('unlink'),
            'Operaciones/Administrador sin Jefatura NO debe tener unlink')

    # ── 2. Usuario autorizado: asistente → action_run → unlink (su=False) ──
    def test_02_authorized_user_deletes_eligible_guide(self):
        guia = self._make_guia('ACL-02')
        wizard = self._wizard(
            self.user_authorized, guia, acknowledge=True)
        self.assertFalse(wizard.blockers, wizard.blockers)
        self.assertTrue(wizard.requirements_ok)

        action = wizard.action_run()

        self.assertFalse(
            self.Guia.search([('id', '=', guia.id)]),
            'La guía elegible debe eliminarse con el usuario autorizado')
        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')
        logs = self.AuditLog.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('description', 'ilike', 'ACL-02'),
        ])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.user_id, self.user_authorized)

    # ── 3. Usuario sin ROL ni ACL: el servidor rechaza (H2) ───────────────
    def test_03_direct_unlink_without_acl_is_denied(self):
        # H2 (FASE 4): la guarda de ROL (jefatura/sistema) se evalúa ANTES de
        # la ACL, así que un usuario sin jefatura ni ACL recibe un `UserError`
        # de negocio (antes de H2: `AccessError` de `ir.model.access`).
        guia = self._make_guia('ACL-03')
        with self.assertRaises(UserError) as ctx:
            guia.with_user(self.user_no_acl).unlink()
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(
            self.Guia.search([('id', '=', guia.id)]),
            'La guía debe sobrevivir al rechazo de acceso')
        self.assertFalse(self.AuditLog.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('description', 'ilike', 'ACL-03'),
        ]), 'Un rechazo de acceso no debe dejar auditoría de éxito')

    # ── 4. El asistente informa la falta de permiso ANTES de ejecutar ─────
    def test_04_wizard_reports_missing_permission_upfront(self):
        guia = self._make_guia('ACL-04')
        wizard = self._wizard(
            self.user_no_acl, guia, acknowledge=True)
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('permiso', wizard.blockers or '')
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(self.Guia.search([('id', '=', guia.id)]))
        self.assertFalse(self.AuditLog.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('description', 'ilike', 'ACL-04'),
        ]))

    # ── 5. Guarda de ROL del core (H2) preservada ─────────────────────────
    def test_05_core_stock_manager_guard_preserved(self):
        # H2 (FASE 4): la guarda exige «Jefatura de Operaciones» (o sistema),
        # NO el grupo técnico «Inventario / Administrador».
        guia = self._make_guia('ACL-05')
        with self.assertRaises(UserError) as ctx:
            guia.with_user(self.user_no_stock).unlink()
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', guia.id)]))

    # ── 6. Protección de estado del core preservada (llamada directa) ─────
    def test_06_core_state_guard_preserved_on_direct_call(self):
        guia = self._make_guia('ACL-06', state='processed')
        with self.assertRaises(UserError) as ctx:
            guia.with_user(self.user_authorized).unlink()
        self.assertIn('SEGURIDAD MADENAT', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', guia.id)]))

    # ── 7. Alcance: la llamada directa de un usuario autorizado funciona ──
    def test_07_authorized_direct_unlink_scope(self):
        # H1 (FASE 4): la vía directa exige MOTIVO explícito (H1).
        guia = self._make_guia('ACL-07')
        guia.with_user(self.user_authorized).with_context(
            madenat_guia_delete_reason='ACL-07 limpieza de prueba').unlink()
        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))

