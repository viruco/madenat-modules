# -*- coding: utf-8 -*-
"""Programa SV — guarda de eliminación de la etiqueta SV con existencias.

Diagnóstico 2026-10-12 (`stock_quant_lot_id_fkey`): el usuario intentó **eliminar**
desde el visor estándar de lotes la etiqueta SV `SV000000841`, que tiene existencia
física (+40.315 m³ en `WH/Stock`). La BD lo bloqueó con la FK
`stock_quant_lot_id_fkey` (ON DELETE RESTRICT) y Odoo mostró el mensaje técnico.

Estas pruebas cubren la corrección de robustez (no de la causa raíz):

* Opción 2 — la guarda server-side `_sv_guard_unlink()` bloquea la etiqueta SV de
  volumen con filas en `stock.quant` (mismo criterio exacto que la FK) con un
  mensaje de negocio; y permite eliminarla si no tiene existencias ni historial.
* Opción 1 — la violación de integridad se traduce a mensaje de negocio en
  `stock.lot.unlink()`, **sin** alterar el invariante (el lote sigue sin poder
  eliminarse).
* El bypass test-only por marcador (`madenat.sv.internal.marker`) se conserva.

Todos los registros son aislados (TransactionCase): no se usa ni modifica la Guía
4495589, el lote SV000000841 (id 10215) ni ningún dato histórico.
"""

import uuid

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvLotUnlinkGuard(SvTestCommon, TransactionCase):
    """La etiqueta SV con existencias no se elimina (mensaje de negocio)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()
        cls.Marker = cls.env['madenat.sv.internal.marker']

    # ── Opción 2: guarda proactiva de la etiqueta SV de volumen ───────────
    def test_01_lote_sv_volumen_con_existencias_bloquea(self):
        """Con quant: se bloquea ANTES de la BD, con mensaje de negocio."""
        guia = self._sv_make_guia('SV-UNLINK-01', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000181', volume=40.3)
        self._sv_add_quant(lot, 40.3)
        self.assertGreater(
            self.Quant.search_count([('lot_id', '=', lot.id)]), 0,
            'El fixture debe tener existencia (quant)')

        with self.assertRaisesRegex(ValidationError, 'existencias'):
            lot.unlink()

        # El invariante se mantiene: ni el lote ni su existencia desaparecen.
        self.assertTrue(lot.exists())
        self.assertGreater(
            self.Quant.search_count([('lot_id', '=', lot.id)]), 0)

    def test_02_lote_sv_volumen_sin_existencias_permitido(self):
        """Sin quant ni historial: el caso legítimo sigue permitido."""
        guia = self._sv_make_guia('SV-UNLINK-02', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000182', volume=40.3)
        self.assertEqual(
            self.Quant.search_count([('lot_id', '=', lot.id)]), 0)
        lot_id = lot.id

        lot.unlink()

        self.assertFalse(self.StockLot.browse(lot_id).exists())

    # ── Bypass test-only intacto ──────────────────────────────────────────
    def test_03_cleanup_test_only_intacto_con_existencias(self):
        """El marcador de pruebas sigue pudiendo limpiar lote + quant."""
        guia = self._sv_make_guia('SV-UNLINK-03', pdf_volume=40.3)
        lot = self._sv_make_lot(guia, label='SV00000000183', volume=40.3)
        self._sv_add_quant(lot, 40.3)
        quant = self.Quant.search([('lot_id', '=', lot.id)])
        self.assertTrue(quant)

        token = 'svunlink-%s' % uuid.uuid4().hex
        self.Marker.sudo()._sv_test_mark(token, lot)
        self.Marker.sudo()._sv_test_mark(token, quant)
        removed = self.Marker.sudo()._sv_test_cleanup(token)

        self.assertGreaterEqual(removed, 2)
        self.assertFalse(self.StockLot.browse(lot.id).exists())
        self.assertFalse(self.Quant.browse(quant.ids).exists())

    # ── Opción 1: traducción de la violación de integridad ────────────────
    def test_04_lote_no_sv_con_existencias_traduce_el_mensaje(self):
        """Cualquier lote con existencia: la FK se traduce a mensaje de negocio."""
        lot = self.StockLot.create({
            'name': 'NO-SV-UNLINK-04',
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        self._sv_add_quant(lot, 10.0)
        self.assertGreater(
            self.Quant.search_count([('lot_id', '=', lot.id)]), 0)

        with self.assertRaisesRegex(ValidationError, 'no puede eliminarse'):
            lot.unlink()

        self.assertTrue(lot.exists())
        self.assertGreater(
            self.Quant.search_count([('lot_id', '=', lot.id)]), 0)
