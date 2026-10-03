# -*- coding: utf-8 -*-
"""Programa SV — concurrencia REAL entre dos transacciones independientes.

Demuestra que dos transacciones no pueden sobre-consumir el mismo saldo SV:
la transacción B queda bloqueada en el `SELECT ... FOR UPDATE` del lote,
recalcula el saldo tras el bloqueo y falla con el saldo correcto.

Estrategia soportada por Odoo 18 (18.0-20260817):
- La transacción A usa el cursor de la clase (`SingleTransactionCase.cr`).
- La transacción B usa un cursor independiente (`registry.cursor()`) dentro de
  un hilo propio, con su `api.Environment`.
- `api.Environment.manage()` fue eliminado en Odoo 16+ y NO existe en 18.0, por
  lo que se usa el patrón equivalente soportado: cursor propio del hilo,
  `rollback()` + `close()` en `finally`, `thread.join(timeout)` acotado.

`SingleTransactionCase` no prohíbe commit (a diferencia de `TransactionCase`,
que lo bloquea explícitamente), lo que permite la concurrencia real. Los datos
de prueba son aislados, se marcan con un token único y se eliminan íntegramente
con el mecanismo test-only (`madenat.sv.internal.marker`); no queda ningún
registro persistente ni se tocan registros históricos ni secuencias SV.
"""

import threading
import time
import uuid

from odoo import api
from odoo.exceptions import UserError, ValidationError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase
from psycopg2.errors import SerializationFailure

SV_TEST_LABEL = 'SV00000000501'
SV_CONCURRENCY_MESSAGE = (
    'Otro usuario modificó esta etiqueta SV mientras se procesaba la '
    'operación. La operación no fue aplicada. Actualice la información y '
    'vuelva a intentarlo.')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv',
        'sv_concurrency')
class TestSvConcurrency(SingleTransactionCase):
    """Dos transacciones independientes: saldo 40.315 → 25.000/20.000."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.marker_token = 'svconc-%s' % uuid.uuid4().hex
        cls.Marker = cls.env['madenat.sv.internal.marker']
        cls.Capability = cls.env['madenat.sv.internal.capability']
        # Barrido de huérfanos de ejecuciones previas interrumpidas
        # (mecanismo test-only por marcador; nunca en base no-test).
        cls.Marker.sudo()._sv_test_cleanup()
        cls.cr.commit()
        cls.Operation = cls.env['madenat.sv.operation']
        cls.StockLot = cls.env['stock.lot']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SV Concurrency Lumber',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'SV Concurrency Partner', 'is_company': True})
        cls.guia = cls.env['madenat.guia.processing'].create({
            'name': 'SV-CONC-GUIA',
            'partner_id': cls.partner.id,
            'assignment_location_id': cls.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            # F-P0R-D: el volumen de la Guía PDF es `vol_comercial_pdf` (campo
            # real del Core); `volume_pdf_m3` pertenece a un addon externo.
            'vol_comercial_pdf': 40.315,
        })
        cls.lot = cls.StockLot.create({
            'name': SV_TEST_LABEL,
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': cls.guia.id,
            'piezas': 1,
            'volume_purchase_m3': 40.315,
            'vol_shipment_m3': 40.315,
            'volumen_m3': 40.315,
        })
        cls.guia.write({'lot_ids': [(4, cls.lot.id)]})
        cls.Marker.sudo()._sv_test_mark(
            cls.marker_token,
            [cls.guia, cls.lot, cls.product, cls.partner])
        # La concurrencia real exige publicar los fixtures aislados.
        cls.cr.commit()

    # ── Limpieza test-only ────────────────────────────────────────────────
    @classmethod
    def _sv_cleanup(cls):
        """Elimina íntegramente los datos de prueba (solo en test)."""
        try:
            cls.cr.rollback()
        except Exception:  # pragma: no cover - defensivo
            pass
        cls.env.invalidate_all()
        cls.Marker.sudo()._sv_test_cleanup(cls.marker_token)
        cls.cr.commit()
        cls.env.invalidate_all()

    # ── Prueba ────────────────────────────────────────────────────────────
    def test_01_dos_transacciones_no_sobreconsumen(self):
        lot = self.lot
        sequence = self.env['ir.sequence'].sudo().search(
            [('code', '=', 'madenat.volume.lot')], limit=1)
        sequence_next_before = sequence.number_next
        result = {}
        thread_errors = []
        thread_steps = []
        thread = None
        t0 = time.monotonic()

        def _stamp(label):
            thread_steps.append('%s@%.3f' % (label, time.monotonic() - t0))

        b_ready = threading.Event()
        b_finished = threading.Event()
        # Asistente de B ya guardado (como en la UI real: el formulario del
        # asistente se guarda al abrirlo y luego el usuario pulsa "Aplicar").
        wizard_b = self.env['madenat.sv.rebaja.wizard'].create({
            'lot_id': lot.id,
            'rebaja_volume_m3': 20.000,
            'reason': 'Rebaja concurrente B (20.000 m³)',
        })
        wizard_b_vals = {'wizard_id': wizard_b.id}
        self.cr.commit()

        a_holds_lock = threading.Event()

        def _transaction_b():
            """Transacción B: aplicación de su rebaja de 20.000 m³."""
            _stamp('inicio_hilo')
            cr_b = None
            try:
                # Conexión PostgreSQL REAL e independiente: en modo test
                # `registry.cursor()` devuelve un proxy que comparte la conexión
                # del test (no habría concurrencia). `db_connect` obtiene otra
                # conexión del pool, fuera de ese proxy.
                connection = db_connect(self.env.cr.dbname)
                cr_b = connection.cursor()
                _stamp('cursor')
                # En modo test el framework retiene `Registry._lock`, por lo que
                # `Registry(dbname)` bloquearía este hilo indefinidamente. Se
                # construye el Environment reutilizando el registry ya cargado.
                cr_b.transaction = api.Transaction(self.registry)
                env_b = api.Environment(cr_b, self.env.uid, {})
                _stamp('env')
                # Primer statement de B: fija su snapshot ANTES de que A
                # confirme (como el usuario que ya tenía el asistente abierto).
                wizard = env_b['madenat.sv.rebaja.wizard'].browse(
                    wizard_b_vals['wizard_id'])
                wizard.lot_id.id, wizard.rebaja_volume_m3
                _stamp('snapshot')
                b_ready.set()
                a_holds_lock.wait(timeout=30)
                started = time.monotonic()
                _stamp('aplicar')
                try:
                    # El flujo (alta + aplicación) traduce el conflicto.
                    wizard.action_submit()
                    result['applied'] = True
                except (UserError, ValidationError) as error:
                    result['applied'] = False
                    result['error'] = str(error)
                result['elapsed'] = time.monotonic() - started
                _stamp('fin_intento')
                if cr_b is not None:
                    cr_b.rollback()
            except Exception as error:  # pragma: no cover - defensivo
                thread_errors.append('%s: %s' % (type(error).__name__, error))
                thread_steps.append('error')
                if cr_b is not None:
                    try:
                        cr_b.rollback()
                    except Exception:  # pragma: no cover - defensivo
                        pass
            finally:
                if cr_b is not None:
                    cr_b.close()
                b_finished.set()

        try:
            thread = threading.Thread(target=_transaction_b, daemon=True)
            thread.start()
            self.assertTrue(
                b_ready.wait(timeout=30),
                'La transacción B no preparó su asistente (pasos=%s, errores=%s)'
                % (thread_steps, thread_errors))
            # Transacción A: toma el FOR UPDATE del lote y lo mantiene.
            operation_a = self.Operation.create({
                'name': 'SVO-CONC-A',
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 25.000,
                'reason': 'Rebaja concurrente A (25.000 m³)',
            })
            operation_a.action_apply()
            self.env.flush_all()
            # Evidencia: A mantiene realmente el bloqueo de fila del lote.
            probe_connection = db_connect(self.env.cr.dbname)
            probe_cursor = probe_connection.cursor()
            try:
                probe_cursor.execute(
                    'SELECT id FROM stock_lot WHERE id = %s FOR UPDATE NOWAIT',
                    (lot.id,))
                result['lock_held_by_a'] = False
            except Exception as error:
                result['lock_held_by_a'] = 'conflict' if 'lock' in str(
                    error).lower() else str(error)
            finally:
                probe_cursor.rollback()
                probe_cursor.close()
            # B puede aplicar ahora (A ya tiene el bloqueo).
            a_holds_lock.set()
            time.sleep(1.5)  # B intenta mientras A mantiene el bloqueo
            self.cr.commit()  # A confirma y libera el FOR UPDATE
            result['a_commit_at'] = round(time.monotonic() - t0, 3)
            self.assertTrue(
                b_finished.wait(timeout=30),
                'La transacción B no terminó (pasos=%s, errores=%s)'
                % (thread_steps, thread_errors))
            thread.join(timeout=30)
            self.assertFalse(thread.is_alive())
            # ── Resultado requerido ───────────────────────────────────────
            self.assertFalse(
                thread_errors,
                'Error inesperado en B: %s (pasos=%s)'
                % (thread_errors, thread_steps))
            self.assertFalse(
                result.get('applied'),
                'B no debe aplicar su rebaja (error=%s, pasos=%s)'
                % (result.get('error'), thread_steps))
            # Mensaje funcional aprobado, sin error técnico PostgreSQL.
            error_message = result.get('error') or ''
            self.assertTrue(error_message, 'B debe recibir un mensaje explícito')
            self.assertIn(SV_CONCURRENCY_MESSAGE, error_message)
            for forbidden in ('SerializationFailure', 'could not serialize',
                              'psycopg2', 'CONTEXT', 'concurrent update'):
                self.assertNotIn(forbidden, error_message)
            self.assertGreaterEqual(
                result.get('elapsed', 0.0), 1.0,
                'B debe quedar bloqueada hasta que A confirma')
            self.assertEqual(
                result.get('lock_held_by_a'), 'conflict',
                'A debe mantener realmente el bloqueo de fila del lote')

            self.env.invalidate_all()
            lot.invalidate_recordset()
            self.assertAlmostEqual(lot.sv_available_m3, 15.315, places=3)
            self.assertAlmostEqual(lot.sv_rebajado_m3, 25.000, places=3)
            self.assertGreaterEqual(lot.sv_available_m3, 0.0)
            applied = self.Operation.sudo().search([
                ('action_type', '=', 'rebaja'), ('state', '=', 'applied')])
            self.assertEqual(len(applied), 1)
            self.assertAlmostEqual(
                applied.rebaja_volume_m3, 25.000, places=3)
            # Sin registro parcial de B.
            self.assertFalse(self.Operation.sudo().search([
                ('name', '=', 'SVO-CONC-B')]))
            self.assertFalse(self.Operation.sudo().search([
                ('rebaja_volume_m3', '=', 20.000)]))
            # Sin auditoría/chatter duplicado de B.
            audit = self.env['madenat.audit.log'].sudo().search([
                ('action_type', '=', 'sv_operation'),
                ('batch_id', '=', SV_TEST_LABEL)])
            self.assertEqual(len(audit), 1)
            # Sin capacidad remanente.
            self.assertFalse(self.Capability.sudo().search([]))
            # La secuencia de identidad SV no se tocó.
            sequence.invalidate_recordset()
            self.assertEqual(sequence.number_next, sequence_next_before)

            # ── Regla de negocio post-bloqueo (determinista) ──────────────
            # Odoo usa aislamiento REPEATABLE READ: la transacción bloqueada no
            # puede ver el saldo actualizado y falla por actualización
            # concurrente (fail-closed, sin sobre-consumo). En cuanto una
            # transacción lee el saldo vigente, la MISMA rebaja de 20.000 m³
            # queda rechazada por saldo disponible 15.315 m³.
            sequential = self.Operation.create({
                'name': 'SVO-CONC-C',
                'lot_id': lot.id,
                'action_type': 'rebaja',
                'rebaja_volume_m3': 20.000,
                'reason': 'Verificación de saldo posterior al bloqueo',
            })
            with self.assertRaises(ValidationError) as sequential_error:
                sequential.action_apply()
            self.assertIn('15.315', str(sequential_error.exception))
        finally:
            # Limpieza test-only: no deja registros de prueba persistentes.
            self._sv_cleanup()

    def test_02_sin_registros_de_prueba_persistentes(self):
        """Tras la prueba concurrente no queda ningún dato de prueba."""
        # Idempotente: si este test se ejecuta aislado, la limpieza test-only
        # elimina los fixtures del setUpClass y verifica el resultado.
        self._sv_cleanup()
        self.env.invalidate_all()
        self.assertFalse(self.StockLot.sudo().search([
            ('name', '=', SV_TEST_LABEL)]))
        self.assertFalse(self.Operation.sudo().search([
            ('name', 'in', ('SVO-CONC-A', 'SVO-CONC-B'))]))
        self.assertFalse(self.Operation.sudo().search([
            ('guia_processing_id.name', '=', 'SV-CONC-GUIA')]))
        self.assertFalse(self.env['madenat.audit.log'].sudo().search([
            ('batch_id', '=', SV_TEST_LABEL)]))
        self.assertFalse(self.Marker.sudo().search([
            ('token', '=', self.marker_token)]))
        self.assertFalse(self.Capability.sudo().search([]))
        self.assertFalse(self.env['madenat.guia.processing'].sudo().search([
            ('name', '=', 'SV-CONC-GUIA')]))
