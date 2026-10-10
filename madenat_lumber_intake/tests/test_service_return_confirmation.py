# -*- coding: utf-8 -*-
"""Confirmación de retorno de servicio — NO bloqueante (2026-10-07).

Cobertura de la identificación (`service_return_confirmation`) en
`madenat.guia.processing`, con semántica de TRES estados:

* vacío  = pendiente de identificación (NO equivale a 'no');
* 'yes'  = es retorno de servicio;
* 'no'   = no es retorno de servicio.

La identificación es NO bloqueante: NO impide la ingesta ni el envío a stock
por sí sola, no altera `tipo_recepcion`, stock ni costes, y no dispara
imputaciones (acto posterior, CANON/19 / AD-91). Alcance: ingreso Procesado de
servicio (`tipo_recepcion == 'service'`). TransactionCase: nada se persiste.
"""
import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, AccessError

# Mensaje del guard BLOQUEANTE del antecedente (NO debe aparecer): su ausencia
# demuestra que la identificación es no bloqueante.
MSG_RETURN = ('Antes de enviar a stock, indique si este ingreso '
              'es un retorno de servicio.')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestServiceReturnConfirmation(TransactionCase):
    """Identificación no bloqueante de retorno de servicio (Ingreso de Madera)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.partner = cls.env['res.partner'].create({
            'name': 'SrvRet Proveedor', 'is_company': True})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'SrvRet Producto', 'is_storable': True, 'tracking': 'lot'})

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='service', state='verified',
                   confirm=None, with_doc=False, with_line=False):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo,
            'state': state,
            'rate_usd': 800.0,
        }
        if confirm is not None:
            vals['service_return_confirmation'] = confirm
        if with_doc:
            vals['excel_file'] = base64.b64encode(b'fake-xls')
            vals['excel_filename'] = 'packing.xlsx'
        guia = self.Guia.create(vals)
        if with_line:
            self.Line.create({
                'processing_id': guia.id,
                'product_id': self.product.id,
                'lot_name': 'SRV-LOT-1',
            })
        return guia

    def _console_for(self, guia):
        guia.invalidate_recordset()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _oper_user(self, login):
        return self.env['res.users'].create({
            'name': login, 'login': login,
            'email': '%s@madenat.cl' % login,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id,
            ])]})
    # 1 ── Vacío = pendiente y NO bloquea; no se coacciona a 'no'.
    def test_01_vacio_pendiente_no_bloquea(self):
        guia = self._make_guia('SRV-01')
        self.assertFalse(guia.service_return_confirmation)
        # El guard bloqueante del antecedente NO existe.
        self.assertFalse(hasattr(self.Guia, '_assert_service_return_confirmed'))
        # action_validate NO falla por la confirmación (cualquier error es de
        # otra índole; nunca MSG_RETURN).
        try:
            guia.action_validate()
        except Exception as exc:  # noqa: BLE001
            self.assertNotIn(MSG_RETURN, str(exc))

    # 2 ── 'Sí' se conserva.
    def test_02_si_se_conserva(self):
        guia = self._make_guia('SRV-02', confirm='yes')
        self.assertEqual(guia.service_return_confirmation, 'yes')
        self.assertEqual(
            self.Guia.browse(guia.id).service_return_confirmation, 'yes')

    # 3 ── 'No' se conserva; no cambia el tipo de recepción.
    def test_03_no_se_conserva_sin_cambiar_tipo(self):
        guia = self._make_guia('SRV-03', confirm='no')
        self.assertEqual(guia.tipo_recepcion, 'service')
        self.assertEqual(guia.service_return_confirmation, 'no')

    # 4 ── Vacío ≠ No (estado distinto, sin coacción).
    def test_04_vacio_no_equivale_a_no(self):
        vacio = self._make_guia('SRV-04-V')
        no = self._make_guia('SRV-04-N', confirm='no')
        self.assertFalse(vacio.service_return_confirmation)
        self.assertNotEqual(vacio.service_return_confirmation, 'no')
        dom_vacio = [('tipo_recepcion', '=', 'service'),
                     ('service_return_confirmation', '=', False)]
        dom_no = [('tipo_recepcion', '=', 'service'),
                  ('service_return_confirmation', '=', 'no')]
        self.assertIn(vacio.id, self.Guia.search(dom_vacio).ids)
        self.assertNotIn(vacio.id, self.Guia.search(dom_no).ids)
        self.assertIn(no.id, self.Guia.search(dom_no).ids)

    # 5 ── Identificación posterior (completar más tarde).
    def test_05_identificacion_posterior(self):
        guia = self._make_guia('SRV-05')
        self.assertFalse(guia.service_return_confirmation)
        guia.write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(
            self.Guia.browse(guia.id).service_return_confirmation, 'yes')

    # 6 ── Permisos reales: Operaciones puede; usuario sin grupo no.
    def test_06_permisos_reales(self):
        guia = self._make_guia('SRV-06')
        user = self._oper_user('srvret_oper')
        guia.with_user(user).write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')
        plain = self.env['res.users'].create({
            'name': 'srvret plain', 'login': 'srvret_plain',
            'email': 'srvret_plain@madenat.cl',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            guia.with_user(plain).write({'service_return_confirmation': 'no'})

    # 7 ── Sin imputación automática ni efectos colaterales.
    def test_07_sin_imputacion_automatica(self):
        has_imp = 'madenat.sv.imputation' in self.env
        imp_before = (self.env['madenat.sv.imputation'].search_count([])
                      if has_imp else 0)
        lots_before = self.env['stock.lot'].search_count([])
        pick_before = self.env['stock.picking'].search_count([])
        po_before = self.env['purchase.order'].search_count([])
        for val in ('yes', 'no'):
            g = self._make_guia('SRV-07-%s' % val, confirm=val)
            self.assertFalse(g.consumption_picking_id)
            self.assertFalse(g.lot_ids)
            self.assertFalse(g.order_id)
        if has_imp:
            self.assertEqual(
                self.env['madenat.sv.imputation'].search_count([]), imp_before)
        self.assertEqual(self.env['stock.lot'].search_count([]), lots_before)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), pick_before)
        self.assertEqual(
            self.env['purchase.order'].search_count([]), po_before)


    # 8 ── Reintento de escritura NO duplica efectos (idempotente).
    def test_08_reenvio_no_duplica(self):
        guia = self._make_guia('SRV-08')
        lots_before = self.env['stock.lot'].search_count([])
        picks_before = self.env['stock.picking'].search_count([])
        for _ in range(3):
            guia.write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')
        self.assertEqual(self.env['stock.lot'].search_count([]), lots_before)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), picks_before)

    # 9 ── Fallo de la operación sin efectos parciales (vacío).
    def test_09_fallo_sin_efectos_parciales(self):
        guia = self._make_guia('SRV-09', with_doc=True, with_line=True)
        lots_before = self.env['stock.lot'].search_count([])
        picks_before = self.env['stock.picking'].search_count([])
        try:
            guia.action_validate()
        except Exception as exc:  # noqa: BLE001
            self.assertNotIn(MSG_RETURN, str(exc))
        guia.invalidate_recordset()
        self.assertFalse(guia.service_return_confirmation)
        self.assertFalse(guia.lot_ids)
        self.assertFalse(guia.consumption_picking_id)
        self.assertEqual(self.env['stock.lot'].search_count([]), lots_before)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), picks_before)

    # 10 ── Consola: "Enviar a Stock" NO bloquea por confirmación vacía.
    def test_10_console_send_to_stock_no_bloquea(self):
        guia = self._make_guia('SRV-10', with_doc=True, with_line=True)
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        try:
            console.action_send_to_stock()
        except Exception as exc:  # noqa: BLE001
            self.assertNotIn(MSG_RETURN, str(exc))

    # 11 ── Consola: proxy EDITABLE con el usuario operativo (inverse → guía).
    def test_11_console_proxy_editable_operativo(self):
        guia = self._make_guia('SRV-11')
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        self.assertTrue(console.service_return_in_scope)
        self.assertFalse(console.service_return_confirmation)
        user = self._oper_user('srvret_console')
        console.with_user(user).write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')
        self.assertEqual(
            self._console_for(guia).service_return_confirmation, 'yes')
        # Vaciar por consola con el usuario operativo (sin aplicadas → permitido).
        self._console_for(guia).with_user(user).write(
            {'service_return_confirmation': False})
        guia.invalidate_recordset()
        self.assertFalse(guia.service_return_confirmation)

    # 12 ── Consola: fuera de alcance (compra/granel) no expone el campo.
    def test_12_console_fuera_de_alcance(self):
        compra = self._make_guia('SRV-12-C', tipo='compra')
        self.assertFalse(self._console_for(compra).service_return_in_scope)
        granel = self._make_guia('SRV-12-G', tipo='granel')
        self.assertFalse(self._console_for(granel).service_return_in_scope)

    # 13 ── Vista operativa (consola) expone los campos de confirmación.
    def test_13_vista_consola_expone_campos(self):
        view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form')
        arch = view.arch or ''
        self.assertIn('service_return_confirmation', arch)
        self.assertIn('service_return_in_scope', arch)


    # 14 ── Cristhian por login (si la base lo contiene): permisos reales, su=False.
    def _cristhian_or_skip(self):
        user = self.env['res.users'].search(
            [('login', '=', 'cristhian.elguetag@gmail.com')], limit=1)
        if not user:
            self.skipTest('Cristhian no está en esta base aislada.')
        if user.id == self.env.ref('base.user_root').id:
            self.skipTest('Cristhian es root (no representativo).')
        return user

    def test_14_cristhian_marca_si_no_vacio(self):
        user = self._cristhian_or_skip()
        groups_before = set(user.groups_id.ids)
        guia = self._make_guia('SRV-14')
        guia.with_user(user).write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')
        guia.with_user(user).write({'service_return_confirmation': 'no'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'no')
        guia.with_user(user).write({'service_return_confirmation': False})
        guia.invalidate_recordset()
        self.assertFalse(guia.service_return_confirmation)
        # Grupos de Cristhian intactos.
        user.invalidate_recordset()
        self.assertEqual(set(user.groups_id.ids), groups_before)

    def test_15_cristhian_edita_desde_consola(self):
        user = self._cristhian_or_skip()
        guia = self._make_guia('SRV-15')
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        console.with_user(user).write({'service_return_confirmation': 'yes'})
        guia.invalidate_recordset()
        self.assertEqual(guia.service_return_confirmation, 'yes')
        self.assertEqual(
            self._console_for(guia).service_return_confirmation, 'yes')
