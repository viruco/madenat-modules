# -*- coding: utf-8 -*-
"""G1 (FASE 3) — Guardas de eliminación de `madenat.guia.processing` (D-G1..D-G4).

Escenarios a–m del encargo. La guarda es ÚNICA (core `unlink()`), compartida
por la vía directa y por el asistente. Datos transaccionales (rollback).
"""
import uuid

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase, TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestGuiaDeleteGuards(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Audit = cls.env['madenat.audit.log']
        oper = cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        jef = cls.env.ref('madenat_lumber_core.group_madenat_jefatura_operaciones')
        mgr = cls.env.ref('stock.group_stock_manager')
        user = cls.env.ref('base.group_user')
        sfx = uuid.uuid4().hex[:8]

        def mk(label, groups):
            return cls.env['res.users'].create({
                'name': 'G3 %s' % label,
                'login': 'g3_%s_%s@test.local' % (label, sfx),
                'groups_id': [(6, 0, [g.id for g in groups])],
            })
        cls.user_ok = mk('ok', [user, oper, jef, mgr])
        cls.user_noacl = mk('noacl', [user, oper, mgr])
        # H2 (FASE 4) — matriz de roles.
        cls.user_oper = mk('oper', [user, oper])
        cls.user_audit = mk('audit', [user, cls.env.ref(
            'madenat_lumber_core.group_madenat_auditoria')])
        cls.user_plain = mk('plain', [user])
        cls.wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.loc = cls.wh.lot_stock_id
        cls.partner = cls.env['res.partner'].create({'name': 'G3 P'})
        cls.product = cls.env['product.product'].create({
            'name': 'G3 PROD', 'is_storable': True, 'tracking': 'lot'})

    # ── fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name, state='draft'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.loc.id, 'state': state,
            'tipo_recepcion': 'granel', 'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared', 'volume_pdf_m3': 1.0})

    def _lot(self, name, **kw):
        v = {'name': name, 'product_id': self.product.id,
             'company_id': self.env.company.id}
        v.update(kw)
        return self.env['stock.lot'].create(v)

    def _del(self, guia, user=None, reason='motivo de prueba G3'):
        u = user or self.user_ok
        return guia.with_user(u).with_context(
            madenat_guia_delete_reason=reason).unlink()

    def _audits(self, guia_name):
        return self.Audit.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('description', 'ilike', guia_name)])

    # ── (a) guía duplicada vacía: se elimina y deja registro ──────────────
    def test_a_empty_guide_deleted_with_audit(self):
        g = self._guia('G3-A')
        self._del(g, reason='duplicada sin dependencias')
        self.assertFalse(self.Guia.search([('id', '=', g.id)]))
        logs = self._audits('G3-A')
        self.assertEqual(len(logs), 1)
        self.assertIn('duplicada sin dependencias', logs.description)

    # ── (b) con líneas sin lotes: se elimina (CASCADE) ────────────────────
    def test_b_guide_with_lines_deleted(self):
        g = self._guia('G3-B')
        self.env['madenat.guia.processing.line'].create(
            {'processing_id': g.id, 'product_id': self.product.id,
             'lot_name': 'G3L-B'})
        self._del(g)
        self.assertFalse(self.Guia.search([('id', '=', g.id)]))

    # ── (c) lotes vacíos sin movimientos: se eliminan (sin huérfanos) ─────
    def test_c_empty_lot_removed_no_orphan(self):
        g = self._guia('G3-C')
        lot = self._lot('G3-LOT-C', guia_processing_id=g.id)
        self._del(g)
        self.assertFalse(self.Guia.search([('id', '=', g.id)]))
        self.assertFalse(
            self.env['stock.lot'].search([('id', '=', lot.id)]),
            'El lote vacío no debe quedar huérfano')

    # ── (d) lotes con existencias: bloqueo con mensaje de negocio ─────────
    def test_d_lot_with_quant_blocked(self):
        g = self._guia('G3-D')
        lot = self._lot('G3-LOT-D', guia_processing_id=g.id)
        self.env['stock.quant']._update_available_quantity(
            self.product, self.loc, 1.0, lot_id=lot)
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        self.assertIn('No se puede eliminar la guía', str(ctx.exception))
        self.assertIn('ANULE', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))
        self.assertTrue(lot.exists())
        self.assertFalse(self._audits('G3-D'))

    # ── (e) imputación / envío vinculado: bloqueo de negocio (no FK) ──────
    def test_e_dependency_blocked(self):
        g = self._guia('G3-E')
        # Envío vinculado directamente a la guía (`stock.picking`).
        self.env['stock.picking'].create({
            'picking_type_id': self.wh.in_type_id.id,
            'location_id': self.loc.id, 'location_dest_id': self.loc.id,
            'guia_processing_id': g.id})
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        self.assertIn('No se puede eliminar la guía', str(ctx.exception))
        self.assertIn('albarán', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))
        self.assertFalse(self._audits('G3-E'))

    # ── (e2) imputación de rebaja SV (logistics): bloqueo de negocio ─────
    def test_e2_imputation_blocked(self):
        if 'madenat.sv.imputation' not in self.env:
            self.skipTest('madenat_lumber_logistics no instalado')
        g = self._guia('G3-E2')
        try:
            self.env['madenat.sv.imputation'].create({
                'guia_processing_id': g.id,
                'company_id': self.env.company.id,
                'date': fields.Date.today(),
                'documentary_key': 'G3-E2-KEY'})
        except Exception as exc:
            self.skipTest('no fue posible crear la imputación mínima: %s'
                          % type(exc).__name__)
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        self.assertIn('No se puede eliminar la guía', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))

    # ── (g) historial SV (lote de volumen RESTRICT) ───────────────────────
    def test_g_volume_lot_blocked(self):
        g = self._guia('G3-G')
        self._lot('G3-LOT-G', volume_source_guia_id=g.id, lot_flow_type='volume')
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        self.assertIn('volumen', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))

    # ── (h) estado distinto de draft/cancelled: bloqueo previo ────────────
    def test_h_state_guard(self):
        g = self._guia('G3-H', state='verified')
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        self.assertIn('SEGURIDAD MADENAT', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))

    # ── (i) usuario sin ROL: rechazo de negocio (H2) ──────────────────────
    def test_i_user_without_acl_blocked(self):
        # H2 (FASE 4): `user_noacl` tiene Operaciones + Inventario pero NO
        # jefatura ⇒ la guarda de ROL rechaza con UserError (antes: AccessError
        # de la capa ir.model.access, hoy pre-emptada por la guarda de rol).
        g = self._guia('G3-I')
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=self.user_noacl)
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))
        self.assertFalse(self._audits('G3-I'))

    # ── (j) exactamente un registro de auditoría; fallida = ninguno ───────
    def test_j_exactly_one_audit(self):
        g = self._guia('G3-J')
        self._del(g, reason='razón única')
        self.assertEqual(len(self._audits('G3-J')), 1)
        g2 = self._guia('G3-J2')
        lot = self._lot('G3-LOT-J2', guia_processing_id=g2.id)
        self.env['stock.quant']._update_available_quantity(
            self.product, self.loc, 2.0, lot_id=lot)
        with self.assertRaises(UserError):
            self._del(g2)
        self.assertEqual(len(self._audits('G3-J2')), 0,
                         'La eliminación fallida no deja auditoría')

    # ── (l) sin movimientos físicos en ningún escenario ───────────────────
    def test_l_no_physical_moves(self):
        before = self.env['stock.move'].search_count([])
        g = self._guia('G3-L')
        self._lot('G3-LOT-L', guia_processing_id=g.id)
        self._del(g)
        self.assertEqual(self.env['stock.move'].search_count([]), before)

    # ── (m) vía directa ≡ vía asistente (misma guarda) ────────────────────
    def test_m_direct_and_wizard_same_outcome(self):
        # Directa: bloqueo por cuantía.
        g1 = self._guia('G3-M1')
        lot1 = self._lot('G3-LOT-M1', guia_processing_id=g1.id)
        self.env['stock.quant']._update_available_quantity(
            self.product, self.loc, 1.0, lot_id=lot1)
        with self.assertRaises(UserError) as c1:
            self._del(g1)
        # Asistente (Modo A): también bloquea con mensaje de negocio.
        wiz_model = self.env['madenat.lumber.intake.guide.lifecycle']
        wiz = wiz_model.with_user(self.user_ok).create({
            'guia_processing_id': g1.id, 'mode': 'A',
            'reason': 'prueba G3-M', 'acknowledge': True})
        with self.assertRaises(UserError) as c2:
            wiz.action_run()
        self.assertTrue(self.Guia.search([('id', '=', g1.id)]))
        # Ambas vías comparten el motivo de dependencia (misma guarda central).
        self.assertIn('No se puede eliminar la guía', str(c1.exception))
        self.assertTrue(str(c2.exception).strip())


    # ══════════════════════════════════════════════════════════════════════
    # H4 (FASE 4) — escenario (f): línea de coste sobre lote de la guía
    # ══════════════════════════════════════════════════════════════════════
    def test_f_cost_lines_blocked(self):
        g = self._guia('G4-F')
        lot = self._lot('G4-LOT-F', guia_processing_id=g.id)
        self.env['stock.lot.cost.line'].create({
            'name': 'G4 coste de prueba', 'lot_id': lot.id,
            'amount_usd': 10.0, 'cost_type': 'wood'})
        with self.assertRaises(UserError) as ctx:
            self._del(g)
        msg = str(ctx.exception)
        self.assertIn('No se puede eliminar la guía', msg)
        self.assertIn('coste', msg)
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))
        self.assertFalse(self._audits('G4-F'))
        # Control positivo: sin costes → permitido.
        g2 = self._guia('G4-F2')
        self._lot('G4-LOT-F2', guia_processing_id=g2.id)
        self._del(g2)
        self.assertFalse(self.Guia.search([('id', '=', g2.id)]))

    # ══════════════════════════════════════════════════════════════════════
    # H1 (FASE 4) — MOTIVO OBLIGATORIO en la vía directa
    # ══════════════════════════════════════════════════════════════════════
    def test_h1_direct_without_reason_blocked(self):
        g = self._guia('G4-H1-A')
        with self.assertRaises(UserError) as ctx:
            g.with_user(self.user_ok).unlink()  # sin motivo en el contexto
        self.assertIn('MOTIVO', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', g.id)]))
        self.assertFalse(self._audits('G4-H1-A'))

    def test_h1_blank_reason_blocked(self):
        g = self._guia('G4-H1-B')
        for bad in ('', '   ', '\t\n'):
            with self.assertRaises(UserError) as ctx:
                g.with_user(self.user_ok).with_context(
                    madenat_guia_delete_reason=bad).unlink()
            self.assertIn('MOTIVO', str(ctx.exception))
        self.assertTrue(g.exists())
        self.assertFalse(self._audits('G4-H1-B'))

    def test_h1_reason_text_recorded_once(self):
        g = self._guia('G4-H1-C')
        self._del(g, reason='razón H1 verificable')
        logs = self._audits('G4-H1-C')
        self.assertEqual(len(logs), 1)
        self.assertIn('razón H1 verificable', logs.description)

    def test_h1_wizard_and_direct_equivalent(self):
        g1 = self._guia('G4-H1-D1')
        g2 = self._guia('G4-H1-D2')
        self._del(g1, reason='equivalencia')
        wiz = self.env['madenat.lumber.intake.guide.lifecycle'].with_user(
            self.user_ok).create({
                'guia_processing_id': g2.id, 'mode': 'A',
                'reason': 'equivalencia', 'acknowledge': True})
        wiz.action_run()
        self.assertFalse(g1.exists())
        self.assertFalse(g2.exists())
        for name in ('G4-H1-D1', 'G4-H1-D2'):
            logs = self._audits(name)
            self.assertEqual(len(logs), 1)
            self.assertIn('equivalencia', logs.description)

    def test_h1_test_only_bypass_requires_token(self):
        g = self._guia('G4-H1-E')
        token = 'g4-%s' % uuid.uuid4().hex
        Marker = self.env['madenat.sv.internal.marker'].sudo()
        Marker._sv_test_mark(token, g)
        # Sin token en contexto → denegado.
        self.assertFalse(Marker._sv_test_cleanup_allowed(
            'madenat.guia.processing', [g.id]))
        # Token erróneo → denegado.
        self.assertFalse(Marker.with_context(
            madenat_sv_test_cleanup_token='otro')._sv_test_cleanup_allowed(
                'madenat.guia.processing', [g.id]))
        # Token correcto (solo bajo `--test-enable` real + BD de test) → sí.
        self.assertTrue(Marker.with_context(
            madenat_sv_test_cleanup_token=token)._sv_test_cleanup_allowed(
                'madenat.guia.processing', [g.id]))

    # ══════════════════════════════════════════════════════════════════════
    # H2 (FASE 4) — accesibilidad del permiso de jefatura
    # ══════════════════════════════════════════════════════════════════════
    def test_h2_jefatura_can_delete(self):
        g = self._guia('G4-H2-A')
        self._del(g, user=self.user_ok)
        self.assertFalse(self.Guia.search([('id', '=', g.id)]))
        self.assertEqual(len(self._audits('G4-H2-A')), 1)

    def test_h2_operaciones_cannot_delete(self):
        g = self._guia('G4-H2-B')
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=self.user_oper)
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(g.exists())

    def test_h2_auditoria_cannot_delete(self):
        g = self._guia('G4-H2-C')
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=self.user_audit)
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(g.exists())

    def test_h2_internal_user_cannot_delete(self):
        g = self._guia('G4-H2-D')
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=self.user_plain)
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(g.exists())

    def test_h2_stock_manager_without_jefatura_cannot_delete(self):
        # Resultado documentado (H2): tener `stock.group_stock_manager` NO
        # autoriza; la política exige jefatura (o sistema).
        g = self._guia('G4-H2-E')
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=self.user_noacl)  # oper + stock_manager
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(g.exists())

    def test_h2_other_company_user_without_jefatura_blocked(self):
        """Otra compañía SIN jefatura: bloqueado por la guarda de rol.

        NOTA HONESTA: `madenat.guia.processing` no declara `company_id` ni
        `ir.rule` de compañía, por lo que un usuario CON jefatura de otra
        compañía sí podría eliminar: riesgo residual documentado (fase4).
        """
        g = self._guia('G4-H2-F')
        co2 = self.env['res.company'].create({'name': 'G4 CO 2'})
        u = self.env['res.users'].create({
            'name': 'G4 user CO2', 'login': 'g4_user_co2@test.local',
            'company_id': co2.id, 'company_ids': [(6, 0, [co2.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        with self.assertRaises(UserError) as ctx:
            self._del(g, user=u)
        self.assertIn('Jefatura', str(ctx.exception))
        self.assertTrue(g.exists())


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestGuiaDeleteConcurrency(SingleTransactionCase):
    """(k) Dos eliminaciones sobre la MISMA guía ⇒ exactamente una gana.

    Las dos conexiones son REALES e independientes (no el proxy de test). El
    `DELETE` toma el bloqueo de fila de PostgreSQL, de modo que la segunda
    eliminación (ya sin fila) falla de forma controlada.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.env.user.sudo().write({'groups_id': [
            (4, cls.env.ref('stock.group_stock_manager').id)]})
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.partner = cls.env['res.partner'].create({'name': 'G3 CONC P'})
        cls.guia_name = 'G3-CONC'
        cls.guia = cls.Guia.create({
            'name': cls.guia_name, 'partner_id': cls.partner.id,
            'assignment_location_id': wh.lot_stock_id.id, 'state': 'draft',
            'tipo_recepcion': 'granel', 'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared', 'volume_pdf_m3': 1.0})
        cls.cr.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.cr.rollback()
        except Exception:  # pragma: no cover
            pass
        cls.env.invalidate_all()
        try:
            # La FK de la bitácora se ANULA (`ondelete='set null'`) al eliminar
            # la guía, de modo que el borrado por FK no encontraba el registro
            # y quedaba residuo (detectado en FASE 4). Se limpia por `batch_id`
            # (= nombre de la guía) y, por si acaso, por la FK aún viva.
            cls.cr.execute(
                'DELETE FROM madenat_audit_log WHERE batch_id = %s '
                'OR guia_processing_id = %s',
                (cls.guia_name, cls.guia.id))
            cls.cr.execute(
                'DELETE FROM madenat_guia_processing WHERE id = %s',
                (cls.guia.id,))
            cls.cr.execute(
                'DELETE FROM res_partner WHERE id = %s', (cls.partner.id,))
            cls.cr.commit()
        except Exception:  # pragma: no cover
            cls.cr.rollback()
        super().tearDownClass()

    def test_k_concurrent_delete_one_wins(self):
        from odoo.sql_db import db_connect
        conn2 = db_connect(self.env.cr.dbname)
        cr2 = conn2.cursor()
        results = []
        try:
            # Conexión A (cursor del test): elimina y confirma.
            try:
                self.Guia.browse(self.guia.id).with_context(
                    madenat_guia_delete_reason='k-A').unlink()
                self.cr.commit()
                results.append('A:ok')
            except Exception as exc:  # pragma: no cover
                results.append('A:%s' % type(exc).__name__)
            # Conexión B (independiente): la fila ya no existe ⇒ no borra nada.
            try:
                cr2.execute(
                    'DELETE FROM madenat_guia_processing WHERE id = %s',
                    (self.guia.id,))
                cr2.commit()
                cr2.execute(
                    'SELECT count(*) FROM madenat_guia_processing WHERE id = %s',
                    (self.guia.id,))
                left = cr2.fetchone()[0]
                results.append('B:left=%d' % left)
            except Exception as exc:  # pragma: no cover
                results.append('B:%s' % type(exc).__name__)
        finally:
            try:
                cr2.close()
            except Exception:  # pragma: no cover - defensivo
                pass
            close = getattr(conn2, 'close', None)
            if callable(close):
                close()
        self.assertIn('A:ok', results)
        # B no pudo borrar (la fila ya no existe): exactamente uno ganó.
        self.assertTrue(any(r.startswith('B:left=0') for r in results),
                        'La segunda eliminación no debe encontrar la fila: %s'
                        % results)
