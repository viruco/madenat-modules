# -*- coding: utf-8 -*-
"""V3 — Transacción, SerializationFailure y ORDEN de bloqueos (TX-01..13).

Verifica que una operación rechazada por el guard del documento (lock ns 1 +
comparación de versión) revierte íntegramente y no deja el cursor inválido; que
el rechazo es por VERSIÓN cuando el lock ya está libre; que el orden de bloqueos
es determinista (1 documento → 2/3 capacidad); y que no hay reintento automático
ni efectos parciales (auditoría/reservas).
"""
import threading

from odoo import api
from odoo.exceptions import UserError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase, TransactionCase


class _TxBase(object):
    """Fixtures y helpers compartidos (guía/etiqueta/SV/asistente/documento)."""

    @classmethod
    def _setUpFixtures(cls):
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'V3 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'V3 Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'v3_oper', 'login': 'v3_oper', 'email': 'v3@madenat.cl',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})

    def _etq(self, guia, name, nominal=10.0):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal=100.0):
        return self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})

    def _wizard(self, guia, sv):
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        return wiz

    def _wline(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _draft(self, name):
        guia = self._guia(name)
        etq = self._etq(guia, name + '-E')
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:16].ljust(16, '0'))
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        return guia, etq, sv, wiz, imp


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSaveLockTx(TransactionCase, _TxBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setUpFixtures()

    # ── TX-01: fallo simulado tras escritura ⇒ rollback íntegro ───────────
    def test_tx_01_rollback_tras_fallo(self):
        guia, etq, sv, wiz, imp = self._draft('TX01')
        v0 = imp.edit_version
        n_lines = len(imp.line_ids)
        n_sv = len(imp.sv_line_ids)
        try:
            with self.env.cr.savepoint():
                imp.write({'reason': 'parcial'})
                imp.line_ids.write({'pieces': 7})
                raise ValueError('fallo simulado tras escritura')
        except ValueError:
            pass
        imp.invalidate_recordset()
        self.assertEqual(imp.edit_version, v0)
        self.assertFalse(imp.reason)
        self.assertEqual(len(imp.line_ids), n_lines)
        self.assertEqual(len(imp.sv_line_ids), n_sv)
        self.assertEqual(sum(imp.line_ids.mapped('pieces')), 0)

    # ── TX-02: cursor utilizable tras el conflicto controlado ─────────────
    def test_tx_02_cursor_utilizable_tras_conflicto(self):
        guia, etq, sv, wiz, imp = self._draft('TX02')
        wiz_b = self._wizard(guia, sv)
        v = imp.edit_version
        imp.write({'reason': 'A', 'edit_version': v})
        imp.invalidate_recordset()
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'A')
        imp.write({'reason': 'A2'})                 # la tx sigue usable
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'A2')

    # ── TX-03: reintento HUMANO con versión vigente ───────────────────────
    def test_tx_03_reintento_humano(self):
        guia, etq, sv, wiz, imp = self._draft('TX03')
        wiz_b = self._wizard(guia, sv)
        v = imp.edit_version
        imp.write({'reason': 'A', 'edit_version': v})
        imp.invalidate_recordset()
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        wiz_b.action_reload_current()
        wiz_b.invalidate_recordset()
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 5.0
        wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 5.0, 3)

    # ── TX-04: sin reintento automático que sobrescriba ───────────────────
    def test_tx_04_sin_reintento_automatico(self):
        guia, etq, sv, wiz, imp = self._draft('TX04')
        wiz_b = self._wizard(guia, sv)
        v = imp.edit_version
        imp.write({'reason': 'A', 'edit_version': v})
        imp.invalidate_recordset()
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'A')           # intacto (no sobrescribe)

    # ── TX-05: sin auditoría/reserva de una transición fallida ────────────
    def test_tx_05_sin_auditoria_de_transicion_fallida(self):
        guia, etq, sv, wiz, imp = self._draft('TX05')
        imp.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')
        key = imp.documentary_key
        guia.sudo().write({'service_return_confirmation': 'no'})
        imp.reason = 'x'
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_reopen_to_draft()
        self.assertEqual(self.AuditLog.search_count([
            ('batch_id', '=', key),
            ('action_type', '=', 'imputation_reopen')]), 0)
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')

    # ── TX-06: fallo DESPUÉS del flush ⇒ sin avance indebido ─────────────
    def test_tx_06_fallo_tras_flush(self):
        guia, etq, sv, wiz, imp = self._draft('TX06')
        v0 = imp.edit_version
        try:
            with self.env.cr.savepoint():
                imp.write({'reason': 'x'})
                self.env.flush_all()
                raise ValueError('fallo tras flush')
        except ValueError:
            pass
        imp.invalidate_recordset()
        self.assertEqual(imp.edit_version, v0)
        self.assertFalse(imp.reason)

    # ── TX-09: guardado normal repetido (sin falso conflicto) ─────────────
    def test_tx_09_guardado_secuencial_repetido(self):
        guia, etq, sv, wiz, imp = self._draft('TX09')
        for i in range(3):
            imp.invalidate_recordset()
            v = imp.edit_version
            imp.write({'reason': 'paso %s' % i, 'edit_version': v})
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'paso 2')

    # ── TX-11: cancelar con edición obsoleta ──────────────────────────────
    def test_tx_11_cancelar_con_edicion_obsoleta(self):
        guia, etq, sv, wiz, imp = self._draft('TX11')
        v = imp.edit_version
        imp.with_user(self.user_oper).action_cancel(reason='Anulación de prueba (FASE 11)')
        with self.assertRaises(UserError):
            imp.write({'reason': 'z', 'edit_version': v})
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        self.assertFalse(imp.reason)

    # ── TX-12: dos documentos (guards independientes) sin deadlock ────────
    def test_tx_12_dos_documentos_sin_deadlock(self):
        g1, e1, s1, w1, i1 = self._draft('TX12A')
        g2, e2, s2, w2, i2 = self._draft('TX12B')
        self.assertNotEqual(i1.id, i2.id)
        i1._i2_assert_edit_version(i1.edit_version)     # ns 1 doc1
        i2._i2_assert_edit_version(i2.edit_version)     # ns 1 doc2
        i1.write({'reason': 'A'})
        i2.write({'reason': 'B'})
        i1.invalidate_recordset()
        i2.invalidate_recordset()
        self.assertEqual(i1.reason, 'A')
        self.assertEqual(i2.reason, 'B')

    # ── TX-13: fallo del asistente en operación multietapa ⇒ sin parcial ──
    def test_tx_13_fallo_multietapa_sin_parcial(self):
        guia = self._guia('TX13')
        etq = self._etq(guia, 'TX13-E')
        sv = self._sv(guia, 'SV0000TX13')
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        try:
            with self.env.cr.savepoint():
                wiz.action_prepare()               # etapa 1: crea el documento
                self.assertTrue(wiz.imputation_id)
                raise ValueError('fallo etapa 2')
        except ValueError:
            pass
        # Rollback íntegro: sin documento parcial ni reserva.
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 0)
        self.assertEqual(self.Imputation._i2_lot_active_imputed_m3(etq), 0.0)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSaveLockTxConcurrency(SingleTransactionCase, _TxBase):
    """TX-07/08/10 — rechazo por VERSIÓN (lock libre) y por LOCK (ocupado)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setUpFixtures()
        cls._product_ids = [cls.product.id]
        cls._partner_ids = [cls.supplier.id]
        cls._user_ids = [cls.user_oper.id]
        cls._guia_ids = []
        cls._lot_ids = []
        cls._imp_ids = []

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
                # (`v3_oper`) que NO se elimina con el usuario; se captura por
                # ID y se borra explícitamente (misma técnica que T1).
                cr.execute(
                    'SELECT partner_id FROM res_users WHERE id = ANY(%s)',
                    (cls._user_ids,))
                user_partner_ids = [r[0] for r in cr.fetchall() if r[0]]
                cr.execute('DELETE FROM res_users WHERE id = ANY(%s)',
                           (cls._user_ids,))
                if user_partner_ids:  # pragma: no cover - limpieza defensiva
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
        except Exception:  # pragma: no cover
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._user_ids = []
            cls._product_ids = []
            cls._partner_ids = []

    @classmethod
    def _cleanup_run(cls):
        """Limpia solo los datos POR PRUEBA (guía/lotes/documento/bitácora)."""
        try:
            cr = cls.env.cr
            audit_keys = []
            if cls._imp_ids:
                # La bitácora de la imputación usa `batch_id` = clave documental;
                # se captura ANTES de borrar el documento (la FK se anula al
                # desaparecer la guía, por lo que no sirve para limpiar).
                cr.execute(
                    'SELECT documentary_key FROM madenat_sv_imputation '
                    'WHERE id = ANY(%s)', (cls._imp_ids,))
                audit_keys += [r[0] for r in cr.fetchall() if r[0]]
                cr.execute(
                    'DELETE FROM madenat_sv_imputation WHERE id = ANY(%s)',
                    (cls._imp_ids,))
            if cls._guia_ids:
                cr.execute(
                    'SELECT name FROM madenat_guia_processing '
                    'WHERE id = ANY(%s)', (cls._guia_ids,))
                audit_keys += [r[0] for r in cr.fetchall() if r[0]]
            if audit_keys:
                cr.execute(
                    'DELETE FROM madenat_audit_log WHERE batch_id = ANY(%s)',
                    (audit_keys,))
            if cls._lot_ids:
                cr.execute('DELETE FROM stock_lot WHERE id = ANY(%s)',
                           (cls._lot_ids,))
            if cls._guia_ids:
                cr.execute(
                    'DELETE FROM madenat_guia_processing WHERE id = ANY(%s)',
                    (cls._guia_ids,))
            cr.commit()
        except Exception:  # pragma: no cover
            try:
                cls.env.cr.rollback()
            except Exception:
                pass
        finally:
            cls._guia_ids = []
            cls._lot_ids = []
            cls._imp_ids = []

    def _draft_committed(self, name):
        guia = self._guia(name)
        etq = self._etq(guia, name + '-E')
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:16].ljust(16, '0'))
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self._guia_ids.append(guia.id)
        for rec in (etq, sv):
            self._lot_ids.append(rec.id)
        self._imp_ids.append(imp.id)
        self.cr.commit()
        return imp

    def _assert_in_new_tx(self, imp_id, version):
        """Intenta el guard del documento en una transacción INDEPENDIENTE.
        Devuelve (ok, error)."""
        conn = db_connect(self.env.cr.dbname)
        cr = conn.cursor()
        try:
            cr.transaction = api.Transaction(self.registry)
            env = api.Environment(cr, self.env.uid, {})
            doc = env['madenat.sv.imputation'].browse(imp_id)
            try:
                doc._i2_assert_edit_version(version)
                return True, None
            except UserError as error:
                return False, str(error)
        finally:
            cr.rollback()
            cr.close()

    # ── TX-07: rechazo por VERSIÓN con el lock LIBRE (A ya confirmó) ──────
    def test_tx_07_rechazo_por_version_tras_commit(self):
        imp = self._draft_committed('TX07')
        v = imp.edit_version
        imp._i2_assert_edit_version(v)
        imp.write({'reason': 'A'})
        self.cr.commit()                       # A confirma → lock LIBRE
        ok, error = self._assert_in_new_tx(imp.id, v)
        self.assertFalse(ok)
        self.assertIn('cambió desde que lo abriste', error or '')
        self._cleanup_run()

    # ── TX-08: lock OCUPADO por A ⇒ rechazo controlado, SIN escrituras ────
    def test_tx_08_lock_ocupado_rechazo_controlado(self):
        imp = self._draft_committed('TX08')
        v = imp.edit_version
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
                doc = env['madenat.sv.imputation'].browse(imp.id)
                ready.set()
                if not start.wait(timeout=30):
                    return
                try:
                    doc._i2_assert_edit_version(v)
                    result['ok'] = True
                except UserError as error:
                    result['ok'] = False
                    result['error'] = str(error)
                cr.rollback()
            except Exception as error:  # pragma: no cover
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
        try:
            self.assertTrue(ready.wait(timeout=30), 'B no se preparó')
            imp._i2_assert_edit_version(v)     # A mantiene el guard (sin escribir)
            start.set()
            self.assertTrue(done.wait(timeout=30), 'B no terminó')
            thread.join(timeout=30)
            self.cr.commit()
            self.assertNotIn('thread_error', result, result.get('thread_error'))
            self.assertFalse(result.get('ok'))
            self.assertIn('cambió', result.get('error') or '')
            imp.sudo().invalidate_recordset()
            self.assertEqual(imp.edit_version, v)   # A no escribió
        finally:
            if not done.is_set():
                start.set()
            done.wait(timeout=30)
            thread.join(timeout=30)
            self._cleanup_run()

    # ── TX-10: A APLICA (confirma); B obsoleto guarda ⇒ rechazo ───────────
    def test_tx_10_aplicar_y_guardar_concurrentes(self):
        imp = self._draft_committed('TX10')
        v = imp.edit_version
        imp.with_user(self.user_oper).action_apply()
        self.cr.commit()
        imp.sudo().invalidate_recordset()
        self.assertEqual(imp.state, 'applied')
        ok, error = self._assert_in_new_tx(imp.id, v)   # B obsoleto
        self.assertFalse(ok)
        self.assertIn('cambió desde que lo abriste', error or '')
        self._cleanup_run()

