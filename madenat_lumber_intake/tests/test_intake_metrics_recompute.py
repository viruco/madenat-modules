# -*- coding: utf-8 -*-
"""P2 — Recomputación REAL de las métricas de la consola de intake
(AUD-ETQ-08, 2026-10-12).

Verifica que, al crear / modificar / eliminar una línea del detalle documental,
las métricas calculadas de la consola (`_compute_review_metrics` y derivados) se
actualicen:

(a) en el **MISMO entorno**, después de una lectura previa (el defecto
    confirmado era que la caché de la consola no se invalidaba al cambiar el
    detalle: sólo un entorno nuevo reflejaba el cambio); y
(b) desde una **transacción NUEVA** (cursor independiente).

`SingleTransactionCase` (permite `commit`, necesario para leer desde otra
conexión). Datos de prueba aislados; se eliminan íntegramente en la limpieza.
No se llama manualmente al compute ni se invalida caché en la prueba.
"""
import uuid

from odoo import api
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeMetricsRecompute(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.lumber.volume.detail.line']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.token = 'p2-%s' % uuid.uuid4().hex
        cls._guia_ids = []
        cls._partner_ids = []
        cls.partner = cls.env['res.partner'].create({
            'name': 'P2 %s' % cls.token, 'is_company': True})
        cls._partner_ids.append(cls.partner.id)

    @classmethod
    def tearDownClass(cls):
        cls._cleanup()
        super().tearDownClass()

    @classmethod
    def _cleanup(cls):
        try:
            cls.env.invalidate_all()
            cr = cls.env.cr
            if cls._guia_ids:
                cr.execute(
                    'DELETE FROM madenat_guia_processing WHERE id = ANY(%s)',
                    (cls._guia_ids,))
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
            cls._guia_ids = []
            cls._partner_ids = []

    def _guia(self):
        guia = self.Guia.create({
            'name': 'P2-G-%s' % self.token, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'granel', 'state': 'verified',
            'date_emission': '2026-10-12', 'volume_pdf_m3': 40.0})
        self._guia_ids.append(guia.id)
        return guia

    def _console(self, guia):
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id)], limit=1)

    def _read_new_tx(self, console_id, field):
        """Lee un campo de la consola desde una TRANSACCIÓN nueva (cursor
        independiente): caché limpia, recomputa desde cero."""
        conn = db_connect(self.env.cr.dbname)
        cr = conn.cursor()
        try:
            cr.transaction = api.Transaction(self.registry)
            env2 = api.Environment(cr, self.env.uid, {})
            console = env2['madenat.lumber.intake.console'].browse(console_id)
            return console[field]
        finally:
            cr.rollback()
            cr.close()

    def test_p2_recompute_same_env_and_new_tx(self):
        try:
            guia = self._guia()
            self.cr.commit()
            console = self._console(guia)
            self.assertTrue(console, 'Debe existir la fila de consola del origen')
            # 1) Lectura inicial.
            self.assertAlmostEqual(console.volume_detail_m3, 0.0, 3)
            self.assertAlmostEqual(console.official_volume_m3, 40.0, 3)
            # 2) Crear detalle + leer de nuevo (MISMO entorno).
            line = self.Line.create(
                {'guia_id': guia.id, 'volume_m3': 5.0, 'origin': 'pdf'})
            self.assertAlmostEqual(
                console.volume_detail_m3, 5.0, 3,
                msg='La consola debe recomputar en el MISMO entorno (create)')
            self.assertAlmostEqual(guia.volume_detail_m3, 5.0, 3)
            # 3) Modificar volume_m3 + leer de nuevo (MISMO entorno).
            line.volume_m3 = 9.0
            self.assertAlmostEqual(
                console.volume_detail_m3, 9.0, 3,
                msg='La consola debe recomputar en el MISMO entorno (write)')
            self.assertAlmostEqual(console.official_vs_detail_diff_m3, 31.0, 3)
            # 4) Nueva transacción.
            self.cr.commit()
            self.assertAlmostEqual(
                self._read_new_tx(console.id, 'volume_detail_m3'), 9.0, 3)
            # 5) Eliminar detalle + leer de nuevo (MISMO entorno).
            line.unlink()
            self.assertAlmostEqual(
                console.volume_detail_m3, 0.0, 3,
                msg='La consola debe recomputar en el MISMO entorno (unlink)')
            self.cr.commit()
            self.assertAlmostEqual(
                self._read_new_tx(console.id, 'volume_detail_m3'), 0.0, 3)
        finally:
            self._cleanup()
