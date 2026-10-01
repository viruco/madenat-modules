# -*- coding: utf-8 -*-
"""H-01 / H-02 — Segregación de funciones (ACL) verificada por HTTP/JSON-RPC.

A diferencia de una comprobación ORM (`check_access_rights`), estas pruebas
ejercitan la capa RPC real (`/web/dataset/call_kw`), que es la que gobierna
el cliente web y por la que atraviesan todos los botones de la interfaz.

Cobertura:
  * `stock.lot.cost.line` (H-02): read general; create/write/unlink sólo por
    los grupos funcionales (Costos/Contabilidad/Gerencia/Administración);
    Operaciones sólo create; usuario interno sin grupo MADENAT sin permisos
    de escritura.
  * `madenat.lumber.intake.console` y `madenat.lumber.volume.detail.line`
    (H-01): legibles por Auditoría y Contabilidad; sus altas/escrituras son
    rechazadas server-side para esos perfiles de solo lectura.
"""
from odoo.tests.common import HttpCase, JsonRpcException, new_test_user, tagged


@tagged('post_install', '-at_install', 'madenat_acl_sod')
class TestAclSodIntakeAndCosts(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def _mk(login, groups):
            return new_test_user(
                cls.env, login=login, password='test', groups=groups)

        cls.u_ops = _mk(
            'acl_ops',
            'base.group_user,madenat_lumber_core.group_madenat_operaciones')
        cls.u_audit = _mk(
            'acl_audit',
            'base.group_user,madenat_lumber_core.group_madenat_auditoria')
        cls.u_cont = _mk(
            'acl_cont',
            'base.group_user,madenat_lumber_core.group_madenat_contabilidad')
        cls.u_costos = _mk(
            'acl_costos',
            'base.group_user,madenat_lumber_core.group_madenat_costos')
        # Usuario interno SIN ningún grupo funcional MADENAT.
        cls.u_plain = _mk('acl_plain', 'base.group_user')

        # Un lote existente (o creado con tipo válido en Odoo 18: 'consu').
        lot = cls.env['stock.lot'].search([], limit=1)
        if not lot:
            product = cls.env['product.product'].create(
                {'name': 'ACL SOD product', 'type': 'consu'})
            lot = cls.env['stock.lot'].create(
                {'name': 'ACL-SOD-LOT', 'product_id': product.id})
        cls.lot = lot
        cls.cost_line = cls.env['stock.lot.cost.line'].create({
            'lot_id': cls.lot.id,
            'name': 'ACL SOD base line',
            'cost_type': 'other',
            'amount_usd': 1.0,
        })

    # ── Helpers ────────────────────────────────────────────────────────────
    def _as(self, user):
        """Autentica la sesión HTTP como el usuario dado."""
        self.authenticate(user.login, 'test')

    def _call(self, model, method, args=None, kwargs=None):
        return self.make_jsonrpc_request('/web/dataset/call_kw', {
            'model': model,
            'method': method,
            'args': args or [],
            'kwargs': kwargs or {},
        })

    def _expect_access_error(self, model, method, args=None, kwargs=None):
        with self.assertRaises(JsonRpcException) as ctx:
            self._call(model, method, args, kwargs)
        # JsonRpcException almacena el nombre de la excepción Odoo en str().
        self.assertIn('AccessError', str(ctx.exception))

    # ── H-02: stock.lot.cost.line ──────────────────────────────────────────
    def test_10_cost_line_read_all_groups(self):
        """Todos los perfiles leen líneas de costo (base.group_user)."""
        for user in (self.u_ops, self.u_audit, self.u_cont,
                     self.u_costos, self.u_plain):
            with self.subTest(user=user.login):
                self._as(user)
                res = self._call(
                    'stock.lot.cost.line', 'read',
                    [[self.cost_line.id], ['name', 'amount_usd']])
                self.assertEqual(res[0]['name'], 'ACL SOD base line')

    def test_11_cost_line_create_allowed_for_functional_groups(self):
        """Costos/Contabilidad (y por herencia Gerencia/Admin) crean."""
        for user in (self.u_costos, self.u_cont):
            with self.subTest(user=user.login):
                self._as(user)
                new_id = self._call('stock.lot.cost.line', 'create', [{
                    'lot_id': self.lot.id,
                    'name': 'acl %s' % user.login,
                    'cost_type': 'other',
                    'amount_usd': 2.0,
                }])
                self.assertTrue(new_id)

    def test_12_cost_line_create_allowed_for_operations(self):
        """Operaciones crea (recepción/procesado), pero no edita ni borra."""
        self._as(self.u_ops)
        new_id = self._call('stock.lot.cost.line', 'create', [{
            'lot_id': self.lot.id,
            'name': 'acl ops',
            'cost_type': 'wood',
            'amount_usd': 3.0,
        }])
        self.assertTrue(new_id)

    def test_13_cost_line_create_denied_for_plain_internal_user(self):
        """Un interno sin grupo MADENAT NO puede crear líneas de costo."""
        self._as(self.u_plain)
        self._expect_access_error('stock.lot.cost.line', 'create', [{
            'lot_id': self.lot.id,
            'name': 'acl plain',
            'cost_type': 'other',
            'amount_usd': 9.0,
        }])

    def test_14_cost_line_write_unlink_ops_denied_costos_allowed(self):
        """Operaciones sin write/unlink; Costos con ambos."""
        self._as(self.u_ops)
        self._expect_access_error(
            'stock.lot.cost.line', 'write',
            [[self.cost_line.id], {'amount_usd': 42.0}])
        self._expect_access_error(
            'stock.lot.cost.line', 'unlink', [[self.cost_line.id]])

        self._as(self.u_costos)
        self._call(
            'stock.lot.cost.line', 'write',
            [[self.cost_line.id], {'amount_usd': 42.0}])

    def test_15_cost_line_plain_cannot_write_nor_unlink(self):
        self._as(self.u_plain)
        self._expect_access_error(
            'stock.lot.cost.line', 'write',
            [[self.cost_line.id], {'amount_usd': 0.0}])
        self._expect_access_error(
            'stock.lot.cost.line', 'unlink', [[self.cost_line.id]])

    # ── H-01: consola y detalle declarado ──────────────────────────────────
    def test_20_console_create_denied_for_audit_and_contabilidad(self):
        """Auditoría/Contabilidad: la consola NO se crea."""
        for user in (self.u_audit, self.u_cont):
            with self.subTest(user=user.login):
                self._as(user)
                self._expect_access_error(
                    'madenat.lumber.intake.console', 'create',
                    [{'guide_name': 'ACL'}])

    def test_21_console_readable_by_audit_and_contabilidad(self):
        """Si hay filas en la consola, Auditoría/Contabilidad las lee."""
        console = self.env['madenat.lumber.intake.console'].search([], limit=1)
        if not console:
            self.skipTest('Sin registros en la consola para validar lectura.')
        for user in (self.u_audit, self.u_cont):
            with self.subTest(user=user.login):
                self._as(user)
                res = self._call(
                    'madenat.lumber.intake.console', 'read',
                    [[console.id], ['guide_name']])
                self.assertEqual(len(res), 1)
                self._expect_access_error(
                    'madenat.lumber.intake.console', 'write',
                    [[console.id], {'guide_name': 'ACL'}])

    def test_22_volume_detail_line_read_audit_cont_write_denied(self):
        """Auditoría/Contabilidad leen el detalle declarado, no lo editan."""
        guia = self.env['madenat.guia.processing'].search([], limit=1)
        if not guia:
            self.skipTest('Sin guía para validar el detalle declarado.')
        line = self.env['madenat.lumber.volume.detail.line'].create({
            'guia_id': guia.id,
            'lot_or_package': 'ACL',
        })
        for user in (self.u_audit, self.u_cont):
            with self.subTest(user=user.login):
                self._as(user)
                res = self._call(
                    'madenat.lumber.volume.detail.line', 'read',
                    [[line.id], ['lot_or_package']])
                self.assertEqual(res[0]['lot_or_package'], 'ACL')
                self._expect_access_error(
                    'madenat.lumber.volume.detail.line', 'create',
                    [{'guia_id': guia.id, 'lot_or_package': 'ACL-2'}])
                self._expect_access_error(
                    'madenat.lumber.volume.detail.line', 'write',
                    [[line.id], {'lot_or_package': 'X'}])
