# -*- coding: utf-8 -*-
"""H3 (FASE 4) — H-SEC-5: inmutabilidad mínima de `madenat.audit.log`.

La bitácora de auditoría es APPEND-ONLY: `write()` y `unlink()` lanzan un
`UserError` de NEGOCIO —incluso con `sudo()` y para el grupo de sistema—.

Única excepción: la limpieza test-only, que exige las TRES condiciones
(patrón inerte): token `madenat_sv_test_cleanup_token` en el contexto, entorno
de pruebas ESTRICTO (`--test-enable` real + BD de test) y token VIVO
(marcadores de limpieza existentes).

Las correcciones se hacen con registros NUEVOS, nunca editando.

LÍMITE HONESTO: esto NO impide la alteración por SQL directo ni por un
administrador de base de datos (ver CANON/04 AD-105).
"""
import uuid

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core')
class TestAuditLogImmutability(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Audit = cls.env['madenat.audit.log']
        sfx = uuid.uuid4().hex[:8]
        # Usuario normal (interno) y usuario de auditoría.
        cls.user_normal = cls.env['res.users'].create({
            'name': 'H3 normal', 'login': 'h3_normal_%s@test.local' % sfx,
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]})
        cls.user_audit = cls.env['res.users'].create({
            'name': 'H3 audit', 'login': 'h3_audit_%s@test.local' % sfx,
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_auditoria').id])]})
        cls.log = cls.Audit.sudo().create({
            'action_type': 'lot_creation',
            'description': 'H3: registro de prueba',
            'batch_id': 'H3-IMMUTABLE',
        })

    # ── create / read siguen funcionando ──────────────────────────────────
    def test_a_create_and_read_still_work(self):
        found = self.Audit.search([('batch_id', '=', 'H3-IMMUTABLE')])
        self.assertEqual(len(found), 1)
        self.assertTrue(found.description)

    # ── write bloqueado: normal, auditoría, sistema y sudo ────────────────
    def test_b_write_blocked_everywhere(self):
        victims = [
            self.user_normal,
            self.user_audit,
            self.env.ref('base.user_admin'),
        ]
        for user in victims:
            with self.assertRaises(UserError) as ctx:
                self.log.with_user(user).write({'description': 'alterado'})
            self.assertIn('APPEND-ONLY', str(ctx.exception))
        # `sudo()` tampoco evade la guarda de modelo.
        with self.assertRaises(UserError) as ctx:
            self.log.sudo().write({'description': 'alterado'})
        self.assertIn('APPEND-ONLY', str(ctx.exception))
        self.assertEqual(self.log.description, 'H3: registro de prueba')

    # ── unlink bloqueado: normal, auditoría, sistema y sudo ───────────────
    def test_c_unlink_blocked_everywhere(self):
        victims = [
            self.user_normal,
            self.user_audit,
            self.env.ref('base.user_admin'),
        ]
        for user in victims:
            with self.assertRaises(UserError) as ctx:
                self.log.with_user(user).unlink()
            self.assertIn('APPEND-ONLY', str(ctx.exception))
        with self.assertRaises(UserError) as ctx:
            self.log.sudo().unlink()
        self.assertIn('APPEND-ONLY', str(ctx.exception))
        self.assertTrue(self.log.exists())

    # ── ACL: sin write/unlink ni para el grupo de sistema ─────────────────
    def test_d_acl_write_unlink_removed(self):
        admin = self.env.ref('base.user_admin')
        Model = self.Audit.with_user(admin)
        self.assertFalse(
            Model.has_access('write'),
            'El grupo de sistema NO debe tener permiso de escritura')
        self.assertFalse(
            Model.has_access('unlink'),
            'El grupo de sistema NO debe tener permiso de borrado')
        # create/read siguen concedidos.
        self.assertTrue(Model.has_access('create'))
        self.assertTrue(Model.has_access('read'))

    # ── bypass test-only: token VIVO + entorno estricto ───────────────────
    def test_e_bypass_requires_live_token(self):
        # (1) Token arbitrario (sin marcadores) → bloqueado.
        with self.assertRaises(UserError):
            self.log.with_context(
                madenat_sv_test_cleanup_token='token-falso').sudo().unlink()
        self.assertTrue(self.log.exists())
        # (2) Token VIVO (marcadores existentes) + entorno estricto → permitido.
        token = 'h3-%s' % uuid.uuid4().hex
        self.env['madenat.sv.internal.marker']._sv_test_mark(token, self.log)
        self.log.with_context(
            madenat_sv_test_cleanup_token=token).sudo().unlink()
        self.assertFalse(self.log.exists())
