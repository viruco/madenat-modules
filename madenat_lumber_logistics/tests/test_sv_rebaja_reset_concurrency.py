# -*- coding: utf-8 -*-
"""RESET-16/17 — concurrencia REAL de la reapertura ``cancelled → draft``.

Dos transacciones PostgreSQL **independientes** (conexiones distintas) que se
coordinan con eventos (barrera) y timeouts. NO se acredita simultaneidad con
pruebas secuenciales: la transacción A ejecuta la reapertura y **mantiene su
bloqueo advisory de transacción** (``pg_try_advisory_xact_lock``, ``_i2_lock_
resources``) mientras B intenta su operación antes de que A confirme.

* **RESET-16**: dos sesiones intentan reabrir el MISMO anulado → una sola
  transición efectiva, sin doble reserva ni doble auditoría; la perdedora falla
  de forma controlada con el mensaje funcional (sin error técnico de PostgreSQL).
* **RESET-17**: reapertura concurrente con OTRA operación que consume la MISMA
  capacidad (etiqueta) → sin sobreconsumo; la perdedora hace rollback íntegro.

``SingleTransactionCase`` (permite ``commit``, requisito para publicar los
fixtures a la segunda conexión). Fixtures con token único; se eliminan
íntegramente en la limpieza. NO se tocan registros históricos (IMP02220/IMP04823).
"""
import threading
import time
import uuid

from odoo import api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase

LOCK_MESSAGE_FRAGMENT = 'Otra operación está modificando'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaResetConcurrency(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.token = 'ressync-%s' % uuid.uuid4().hex
        cls._imp_ids = []
        cls._lot_ids = []
        cls._guia_ids = []
        cls._product_ids = []
        cls._partner_ids = []
        cls._user_ids = []
        cls._audit_keys = set()
        cls.product = cls.env['product.product'].create({
            'name': 'CONC Lumber %s' % cls.token, 'is_storable': True,
            'tracking': 'lot', 'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})
        cls._product_ids.append(cls.product.id)
        cls.supplier = cls.env['res.partner'].create({
            'name': 'CONC Supplier %s' % cls.token, 'is_company': True})
        cls._partner_ids.append(cls.supplier.id)
        cls.user_oper = cls.env['res.users'].create({
            'name': 'conc_oper', 'login': 'conc_oper_%s' % cls.token,
            'email': 'conc_oper@madenat.cl', 'company_id': cls.company.id,
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

    # ── Fixtures y limpieza ───────────────────────────────────────────────
    @classmethod
    def _cleanup_class(cls):
        """Limpia los fixtures de CLASE (producto/proveedor/usuario) tras los
        tests. Se ejecuta SOLO en `tearDownClass` para no romper los tests que
        comparten estos registros."""
        cls._cleanup_run()
        try:
            cr = cls.env.cr
            if cls._user_ids:
                # H6 (FASE 4): `res.users.create` genera un partner homónimo
                # (`conc_oper`) que NO se elimina con el usuario. Se captura por
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
        """Limpia los datos POR PRUEBA (guías, etiquetas, imputaciones,
        auditoría). NO toca los fixtures de clase (producto/proveedor/usuario)."""
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

    def _mk_guia(self, name):
        guia = self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})
        self._guia_ids.append(guia.id)
        return guia

    def _mk_etq(self, guia, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': name, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        self._lot_ids.append(lot.id)
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _mk_sv(self, guia, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        self._lot_ids.append(lot.id)
        return lot

    def _mk_draft(self, guia, etq, sv, vol):
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etq)
        line.selected = True
        line.cantidad_asignar_m3 = vol
        wiz.action_prepare()
        imp = wiz.imputation_id
        self._imp_ids.append(imp.id)
        self._audit_keys.add(imp.documentary_key)
        return imp

    # ── RESET-16: dos reaperturas del mismo anulado ───────────────────────
    def test_reset_16_dos_reaperturas_mismo_anulado(self):
        guia = self._mk_guia('CONC-16-%s' % self.token)
        etq = self._mk_etq(guia, 'CONC16-E', 10.0)
        sv = self._mk_sv(guia, 'CONC16-SV', 100.0)
        imp = self._mk_draft(guia, etq, sv, 6.0)
        imp.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')
        imp.reason = 'RESET-16 A'
        self.cr.commit()

        result = {}
        steps = []
        b_ready = threading.Event()
        b_start = threading.Event()
        b_done = threading.Event()

        def _txn_b():
            cr_b = None
            try:
                conn = db_connect(self.env.cr.dbname)
                cr_b = conn.cursor()
                cr_b.transaction = api.Transaction(self.registry)
                env_b = api.Environment(cr_b, self.env.uid, {})
                imp_b = env_b['madenat.sv.imputation'].browse(imp.id)
                imp_b.with_user(self.user_oper).reason = 'RESET-16 B'
                steps.append('B listo')
                b_ready.set()
                if not b_start.wait(timeout=30):
                    return
                started = time.monotonic()
                try:
                    imp_b.with_user(
                        self.user_oper).action_reopen_to_draft()
                    result['ok'] = True
                except (UserError, AccessError, ValidationError) as error:
                    result['ok'] = False
                    result['error'] = str(error)
                result['elapsed'] = time.monotonic() - started
                steps.append('B intento terminado')
                cr_b.rollback()
            except Exception as error:  # pragma: no cover - defensivo
                result['thread_error'] = '%s: %s' % (
                    type(error).__name__, error)
            finally:
                if cr_b is not None:
                    try:
                        cr_b.close()
                    except Exception:
                        pass
                b_done.set()

        thread = threading.Thread(target=_txn_b, daemon=True)
        thread.start()
        try:
            self.assertTrue(b_ready.wait(timeout=30),
                            'B no se preparó (steps=%s)' % steps)
            # A (cursor del test): reabre y MANTIENE el advisory lock.
            imp.with_user(self.user_oper).action_reopen_to_draft()
            self.assertEqual(imp.state, 'draft')
            self.env.flush_all()
            b_start.set()
            self.assertTrue(b_done.wait(timeout=30),
                            'B no terminó (steps=%s)' % steps)
            thread.join(timeout=30)
            self.assertFalse(thread.is_alive())
            self.cr.commit()
            # ── Resultado (antes de la limpieza) ──────────────────────────
            self.assertNotIn(
                'thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'),
                             'La segunda reapertura no debe efectuarse')
            self.assertIn(LOCK_MESSAGE_FRAGMENT, result.get('error') or '')
            for forbidden in ('psycopg2', 'SerializationFailure', 'Traceback'):
                self.assertNotIn(forbidden, result.get('error') or '')
            # Una sola transición, sin duplicar historia ni auditoría.
            imp.sudo().invalidate_recordset()
            self.assertEqual(imp.state, 'draft')
            self.assertTrue(imp.reopened_by_id)
            self.assertEqual(len(imp.line_ids), 1)
            self.assertEqual(len(imp.sv_line_ids), 1)
            self.assertEqual(self.AuditLog.sudo().search_count([
                ('batch_id', '=', imp.documentary_key),
                ('action_type', '=', 'imputation_reopen')]), 1)
            # La etiqueta queda reservada por su nominal completo (10 m³):
            # disponible documental = 0 (reserva tomada EXACTAMENTE una vez).
            self.assertAlmostEqual(
                self.Imputation._i2_lot_available_for_m3(etq), 0.0, 3)
        finally:
            if not b_done.is_set():
                b_start.set()
            b_done.wait(timeout=30)
            thread.join(timeout=30)
            self._cleanup_run()

    # ── RESET-17: reapertura ∥ consumo de la MISMA capacidad ──────────────
    def test_reset_17_reapertura_concurrente_con_consumo(self):
        # Dos etiquetas DISTINTAS comparten la MISMA capacidad documental del SV
        # destino: la reapertura (A) y la aplicación (B) compiten por el mismo
        # recurso (namespace 2 = saldo documental del SV) y se serializan.
        guia = self._mk_guia('CONC-17A-%s' % self.token)
        etq_a = self._mk_etq(guia, 'CONC17A-E', 10.0)
        guia2 = self._mk_guia('CONC-17B-%s' % self.token)
        etq_b = self._mk_etq(guia2, 'CONC17B-E', 10.0)
        sv = self._mk_sv(guia, 'CONC17-SV', 100.0)
        imp_a = self._mk_draft(guia, etq_a, sv, 6.0)
        imp_a.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')
        imp_a.reason = 'RESET-17 A'
        imp_b = self._mk_draft(guia2, etq_b, sv, 6.0)
        self.assertEqual(len(imp_b.sv_line_ids), 1)
        self.cr.commit()

        result = {}
        b_ready = threading.Event()
        b_start = threading.Event()
        b_done = threading.Event()

        def _txn_b():
            cr_b = None
            try:
                conn = db_connect(self.env.cr.dbname)
                cr_b = conn.cursor()
                cr_b.transaction = api.Transaction(self.registry)
                env_b = api.Environment(cr_b, self.env.uid, {})
                imp_b2 = env_b['madenat.sv.imputation'].browse(imp_b.id)
                imp_b2.sv_line_ids.read(['imputed_volume_m3'])
                b_ready.set()
                if not b_start.wait(timeout=30):
                    return
                try:
                    imp_b2.with_user(self.user_oper).action_apply()
                    result['ok'] = True
                except (UserError, AccessError, ValidationError) as error:
                    result['ok'] = False
                    result['error'] = str(error)
                cr_b.rollback()
            except Exception as error:  # pragma: no cover - defensivo
                result['thread_error'] = '%s: %s' % (
                    type(error).__name__, error)
            finally:
                if cr_b is not None:
                    try:
                        cr_b.close()
                    except Exception:
                        pass
                b_done.set()

        thread = threading.Thread(target=_txn_b, daemon=True)
        thread.start()
        try:
            self.assertTrue(b_ready.wait(timeout=30), 'B no se preparó')
            # A: reabre y mantiene el advisory lock sobre la etiqueta y el SV.
            imp_a.with_user(self.user_oper).action_reopen_to_draft()
            self.assertEqual(imp_a.state, 'draft')
            self.env.flush_all()
            b_start.set()
            self.assertTrue(b_done.wait(timeout=30), 'B no terminó')
            thread.join(timeout=30)
            self.assertFalse(thread.is_alive())
            self.cr.commit()
            # ── Resultado (antes de la limpieza) ──────────────────────────
            self.assertNotIn(
                'thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'),
                             'La aplicación concurrente no debe efectuarse')
            self.assertIn(LOCK_MESSAGE_FRAGMENT, result.get('error') or '')
            imp_a.sudo().invalidate_recordset()
            imp_b.sudo().invalidate_recordset()
            # A reabrió; B sigue en borrador (sin aplicación parcial).
            self.assertEqual(imp_a.state, 'draft')
            self.assertEqual(imp_b.state, 'draft')
            # Sin auditoría del evento rechazado.
            self.assertEqual(self.AuditLog.sudo().search_count([
                ('batch_id', '=', imp_b.documentary_key),
                ('action_type', '=', 'imputation')]), 0)
            # Cada etiqueta reserva su propio nominal (≤ 10) y el saldo
            # documental compartido del SV (6 + 6 = 12) no se sobreconsume.
            active_a = self.Imputation._i2_lot_active_imputed_m3(etq_a)
            self.assertLessEqual(active_a, 10.0)
            self.assertGreaterEqual(
                self.Imputation._i2_lot_available_for_m3(etq_a), 0.0)
            assigned_sv = self.Imputation._i2_sv_documental_assigned_m3(sv)
            self.assertAlmostEqual(assigned_sv, 12.0, 3)
            self.assertLessEqual(
                assigned_sv, self.Imputation._i2_sv_nominal_m3(sv))
        finally:
            if not b_done.is_set():
                b_start.set()
            b_done.wait(timeout=30)
            thread.join(timeout=30)
            self._cleanup_run()

    # ── Verificación: sin registros de prueba persistentes ────────────────
    def test_reset_sin_registros_de_prueba_persistentes(self):
        self._cleanup_run()
        self.env.invalidate_all()
        token = self.token
        self.assertFalse(self.env['stock.lot'].sudo().search([
            ('name', 'in', ('CONC16-E', 'CONC16-SV',
                            'CONC17A-E', 'CONC17B-E', 'CONC17-SV'))]))
        self.assertFalse(self.env['madenat.guia.processing'].sudo().search([
            ('name', 'like', '%' + token)]))
        self.assertFalse(self.env['madenat.sv.imputation'].sudo().search([
            ('guia_processing_id.name', 'like', '%' + token)]))
        # Los fixtures de CLASE (usuario/producto/proveedor) se eliminan en
        # `tearDownClass`; aquí solo se verifica que NO queden datos por prueba.
        self.assertTrue(self.env['res.users'].sudo().search([
            ('login', 'like', 'conc_oper_%s' % token)]))
