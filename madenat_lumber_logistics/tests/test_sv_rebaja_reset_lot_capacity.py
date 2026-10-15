# -*- coding: utf-8 -*-
"""P1 — Concurrencia sobre la capacidad de la MISMA etiqueta retornada
(AUD-ETQ-11, 2026-10-12).

La prueba RESET-17 (saldo documental del SV, 12 ≤ 100) se conserva como caso
ADICIONAL en `test_sv_rebaja_reset_concurrency.py`. Aquí se acredita el caso
obligatorio: dos operaciones que compiten por la capacidad **insuficiente del
MISMO LOTE retornado**.

Escenario real construido con el mecanismo existente:

* Un lote retornado `E` con capacidad documental limitada (nominal 10).
* **A**: documento de la guía 1, `cancelled`, cuya línea compromete 6 m³ de `E`;
  al reabrir vuelve a **reservar** esos 6 m³.
* **B**: documento de la guía 2, `cancelled`, cuya línea compromete 6 m³ de la
  MISMA etiqueta `E`. (La unicidad `_check_single_work_per_guia` es por GUÍA, no
  por etiqueta: un mismo lote puede pertenecer a dos guías.)
* Cada operación es válida individualmente (6 ≤ 10); la SUMA (12) excede la
  capacidad del lote (10).
* SV destino con capacidad amplia (100) para que el límite relevante sea el LOTE,
  no el techo del SV.

**Cuándo se toma la reserva:** al existir la línea en estado activo
(`draft`/`pending`/`applied`) — en la creación del borrador y de nuevo en la
reapertura—. La reapertura de un `cancelled` SÍ toma capacidad.

Ejecución con conexiones independientes, `Environment` propio por hilo,
barreras/eventos y timeouts; se prueban los DOS órdenes (A primero / B primero) y
la revalidación de capacidad tras liberar el bloqueo. `SingleTransactionCase`
(permite `commit`); datos aislados y limpieza verificada.
"""
import threading
import time
import uuid

from unittest.mock import patch

from odoo import api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase

LOCK_FRAGMENT = 'Otra operación está modificando'
CAPACITY_FRAGMENT = 'ya está comprometida'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaResetLotCapacity(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.token = 'p1-%s' % uuid.uuid4().hex
        cls._imp_ids = []
        cls._lot_ids = []
        cls._guia_ids = []
        cls._product_ids = []
        cls._partner_ids = []
        cls._user_ids = []
        cls._audit_keys = set()
        cls.product = cls.env['product.product'].create({
            'name': 'P1 Lumber %s' % cls.token, 'is_storable': True,
            'tracking': 'lot', 'uom_id': uom.id, 'uom_po_id': uom.id})
        cls._product_ids.append(cls.product.id)
        cls.supplier = cls.env['res.partner'].create({
            'name': 'P1 Supplier %s' % cls.token, 'is_company': True})
        cls._partner_ids.append(cls.supplier.id)
        cls.user_oper = cls.env['res.users'].create({
            'name': 'p1_oper', 'login': 'p1_oper_%s' % cls.token,
            'email': 'p1_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        cls._user_ids.append(cls.user_oper.id)

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_class()
        super().tearDownClass()

    @classmethod
    def _cleanup_class(cls):
        cls._cleanup_run()
        try:
            cr = cls.env.cr
            if cls._user_ids:
                # H6 (FASE 4): `res.users.create` genera un partner homónimo
                # (`p1_oper`) que NO se elimina con el usuario. Se captura por
                # ID y se borra explícitamente (misma técnica que T1) para no
                # dejar residuo entre ejecuciones.
                cr.execute(
                    'SELECT partner_id FROM res_users WHERE id = ANY(%s)',
                    (cls._user_ids,))
                user_partner_ids = [r[0] for r in cr.fetchall() if r[0]]
                cr.execute(
                    'DELETE FROM mail_message WHERE author_id IN '
                    '(SELECT partner_id FROM res_users WHERE id = ANY(%s))',
                    (cls._user_ids,))
                cr.execute('DELETE FROM res_users WHERE id = ANY(%s)',
                           (cls._user_ids,))
                if user_partner_ids:
                    cr.execute(
                        'DELETE FROM mail_message WHERE author_id = ANY(%s)',
                        (user_partner_ids,))
                    cr.execute(
                        'DELETE FROM res_partner WHERE id = ANY(%s)',
                        (user_partner_ids,))
            if cls._product_ids:
                cr.execute(
                    'DELETE FROM product_template WHERE id IN (SELECT '
                    'product_tmpl_id FROM product_product WHERE id = ANY(%s))',
                    (cls._product_ids,))
                cr.execute('DELETE FROM product_product WHERE id = ANY(%s)',
                           (cls._product_ids,))
            if cls._partner_ids:
                cr.execute('DELETE FROM res_partner WHERE id = ANY(%s)',
                           (cls._partner_ids,))
            cr.commit()
            cls.env.invalidate_all()
        except Exception:  # pragma: no cover - limpieza defensiva
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._product_ids = []
            cls._partner_ids = []
            cls._user_ids = []

    @classmethod
    def _cleanup_run(cls):
        try:
            cls.env.invalidate_all()
            cr = cls.env.cr
            if cls._audit_keys:
                cr.execute(
                    'DELETE FROM madenat_audit_log WHERE batch_id = ANY(%s)',
                    (list(cls._audit_keys),))
            if cls._imp_ids:
                cr.execute(
                    "DELETE FROM mail_message WHERE model = "
                    "'madenat.sv.imputation' AND res_id = ANY(%s)",
                    (cls._imp_ids,))
                cr.execute(
                    'DELETE FROM madenat_sv_imputation WHERE id = ANY(%s)',
                    (cls._imp_ids,))
            if cls._lot_ids:
                cr.execute('DELETE FROM stock_lot WHERE id = ANY(%s)',
                           (cls._lot_ids,))
            if cls._guia_ids:
                cr.execute(
                    'DELETE FROM madenat_guia_processing WHERE id = ANY(%s)',
                    (cls._guia_ids,))
            cr.commit()
            cls.env.invalidate_all()
        except Exception:  # pragma: no cover - limpieza defensiva
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._imp_ids = []
            cls._lot_ids = []
            cls._guia_ids = []
            cls._audit_keys = set()

    # ── Fixtures ──────────────────────────────────────────────────────────
    def _mk_guia(self, name):
        guia = self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})
        self._guia_ids.append(guia.id)
        return guia

    def _mk_etq(self, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        self._lot_ids.append(lot.id)
        return lot

    def _mk_sv(self, guia, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        self._lot_ids.append(lot.id)
        return lot

    def _cancelled(self, guia, etq, sv, vol):
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        line.selected = True
        line.nominal_volume_m3 = vol
        line.cantidad_asignar_m3 = vol
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.with_user(self.user_oper).action_cancel()
        imp.reopen_reason = 'Reapertura P1'
        self._imp_ids.append(imp.id)
        self._audit_keys.add(imp.documentary_key)
        self.assertEqual(imp.state, 'cancelled')
        return imp

    def _fixture(self, tag):
        """Lote E(10) compartido por guía A y guía B; A y B cancelados (6 c/u)."""
        guia_a = self._mk_guia('P1A-%s-%s' % (tag, self.token))
        guia_b = self._mk_guia('P1B-%s-%s' % (tag, self.token))
        etq = self._mk_etq('P1-E-%s' % tag, 10.0)
        guia_a.sudo().write({'lot_ids': [(4, etq.id)]})
        guia_b.sudo().write({'lot_ids': [(4, etq.id)]})
        sv = self._mk_sv(guia_a, 'P1-SV-%s' % tag, 100.0)
        imp_a = self._cancelled(guia_a, etq, sv, 6.0)
        imp_b = self._cancelled(guia_b, etq, sv, 6.0)
        return etq, sv, imp_a, imp_b

    # ── Carrera: `first` mantiene el lock; `second` compite ────────────────
    def _run_race(self, first, second):
        """`first` reabre y MANTIENE el advisory lock (cursor del test);
        `second` intenta su reapertura en una transacción INDEPENDIENTE.
        Confirma `first` y devuelve el dict de resultado de `second`.
        NO limpia (lo hace el test en su `finally`)."""
        result = {}
        ready = threading.Event()
        start = threading.Event()
        done = threading.Event()

        def _txn():
            cr = None
            try:
                conn = db_connect(self.env.cr.dbname)
                cr = conn.cursor()
                cr.transaction = api.Transaction(self.registry)
                env = api.Environment(cr, self.env.uid, {})
                imp = env['madenat.sv.imputation'].browse(second.id)
                imp.with_user(self.user_oper).reopen_reason = 'Segundo P1'
                ready.set()
                if not start.wait(timeout=30):
                    return
                try:
                    imp.with_user(self.user_oper).action_reopen_to_draft()
                    result['ok'] = True
                except (UserError, AccessError, ValidationError) as error:
                    result['ok'] = False
                    result['error'] = str(error)
                cr.rollback()
            except Exception as error:  # pragma: no cover - defensivo
                result['thread_error'] = '%s: %s' % (
                    type(error).__name__, error)
            finally:
                if cr is not None:
                    try:
                        cr.close()
                    except Exception:
                        pass
                done.set()

        thread = threading.Thread(target=_txn, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(timeout=30), 'El segundo no se preparó')
        first.with_user(self.user_oper).action_reopen_to_draft()
        self.env.flush_all()
        start.set()
        self.assertTrue(done.wait(timeout=30), 'El segundo no terminó')
        thread.join(timeout=30)
        self.assertFalse(thread.is_alive())
        self.cr.commit()
        return result

    def _assert_lot_balance(self, etq, imp_win, imp_lose):
        active = self.Imputation._i2_lot_active_imputed_m3(etq)
        self.assertAlmostEqual(active, 6.0, 3)
        self.assertLessEqual(active, 10.0)
        self.assertEqual(self.AuditLog.sudo().search_count([
            ('batch_id', '=', imp_win.documentary_key),
            ('action_type', '=', 'imputation_reopen')]), 1)
        self.assertEqual(self.AuditLog.sudo().search_count([
            ('batch_id', '=', imp_lose.documentary_key),
            ('action_type', '=', 'imputation_reopen')]), 0)

    def test_p1_order_a_first(self):
        etq, sv, imp_a, imp_b = self._fixture('A')
        self.cr.commit()
        try:
            result = self._run_race(imp_a, imp_b)
            self.assertNotIn('thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'), 'B no debe reabrir')
            self.assertIn(LOCK_FRAGMENT, result.get('error') or '')
            imp_a.sudo().invalidate_recordset()
            imp_b.sudo().invalidate_recordset()
            self.assertEqual(imp_a.state, 'draft')
            self.assertEqual(imp_b.state, 'cancelled')
            self.assertEqual(len(imp_a.sv_line_ids), 1)
            self.assertEqual(len(imp_b.sv_line_ids), 1)
            self._assert_lot_balance(etq, imp_a, imp_b)
        finally:
            self._cleanup_run()

    def test_p1_order_b_first(self):
        etq, sv, imp_a, imp_b = self._fixture('B')
        self.cr.commit()
        try:
            result = self._run_race(imp_b, imp_a)
            self.assertNotIn('thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'), 'A no debe reabrir')
            self.assertIn(LOCK_FRAGMENT, result.get('error') or '')
            imp_a.sudo().invalidate_recordset()
            imp_b.sudo().invalidate_recordset()
            self.assertEqual(imp_b.state, 'draft')
            self.assertEqual(imp_a.state, 'cancelled')
            self._assert_lot_balance(etq, imp_b, imp_a)
        finally:
            self._cleanup_run()

    def test_p1_capacity_tras_bloqueo(self):
        """Revalidación de CAPACIDAD del LOTE posterior al bloqueo."""
        etq, sv, imp_a, imp_b = self._fixture('R')
        self.cr.commit()
        try:
            imp_a.with_user(self.user_oper).action_reopen_to_draft()
            self.cr.commit()
            self.assertEqual(imp_a.state, 'draft')
            # Aísla la REVALIDACIÓN posterior al bloqueo: neutraliza la 1ª
            # validación de B (como si hubiera corrido antes del compromiso de
            # A); la 2ª (tras adquirir el lock) revalida de verdad.
            calls = {'n': 0}
            orig = type(imp_b)._i2_validate_reopen

            def _patched(rec):
                calls['n'] += 1
                return True if calls['n'] == 1 else orig(rec)

            with patch.object(type(imp_b), '_i2_validate_reopen', _patched):
                with self.assertRaises(UserError) as cm:
                    imp_b.with_user(self.user_oper).action_reopen_to_draft()
            self.assertIn(CAPACITY_FRAGMENT, str(cm.exception))
            imp_b.sudo().invalidate_recordset()
            self.assertEqual(imp_b.state, 'cancelled')
            self.assertEqual(self.AuditLog.sudo().search_count([
                ('batch_id', '=', imp_b.documentary_key),
                ('action_type', '=', 'imputation_reopen')]), 0)
            active = self.Imputation._i2_lot_active_imputed_m3(etq)
            self.assertAlmostEqual(active, 6.0, 3)
            self.assertLessEqual(active, 10.0)
        finally:
            self._cleanup_run()
