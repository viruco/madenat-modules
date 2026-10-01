# -*- coding: utf-8 -*-
"""Modo A autoservicio — vía ALTERNATIVA por `ir.config_parameter`.

Contrato verificado del desacoplamiento de `--test-enable` (2026-09-28):

* Vía ESTRICTA (`_sv_test_enable_strict`), que protege el ledger SV
  (`_sv_test_cleanup_allowed`, `_sv_test_mark`, `_sv_test_cleanup`): depende
  SOLO de `--test-enable` real + BD de test. NUNCA del parámetro.
* Vía ALTERNATIVA (`_sv_dev_cleanup_enabled`), exclusiva del «Modo A
  autoservicio»: se habilita con
  `ir.config_parameter('madenat.dev_cleanup_enabled') == 'True'`.
* `_sv_test_environment_ok()` es la suma de ambas y la consume solo el Modo A.
* Invariante de las DOS vías: el nombre de la BD debe contener 'test'.

`TransactionCase`: todo se revierte y el parámetro se restaura en `cleanup`
(además se limpia la caché ORM, porque `ir.config_parameter._get_param` usa
`@ormcache` y la caché sobrevive al rollback de la prueba).
"""

from unittest.mock import patch

import odoo
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

DEV_CLEANUP_PARAM = 'madenat.dev_cleanup_enabled'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv',
        'sv_dev_cleanup')
class TestSvDevCleanupParam(TransactionCase):
    """Vías estricta y alternativa de `_sv_test_environment_ok`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Marker = cls.env['madenat.sv.internal.marker'].sudo()
        cls.Icp = cls.env['ir.config_parameter'].sudo()
        cls.previous_value = cls.Icp.get_param(DEV_CLEANUP_PARAM, False)

    def setUp(self):
        super().setUp()
        self.addCleanup(self._restore_param)
        # Estado de partida explícito: parámetro presente con valor 'False'.
        self.Icp.set_param(DEV_CLEANUP_PARAM, 'False')

    def _restore_param(self):
        """Devuelve el parámetro a su estado previo y limpia la caché ORM."""
        if self.previous_value is False:
            self.Icp.search([('key', '=', DEV_CLEANUP_PARAM)]).unlink()
        else:
            self.Icp.set_param(DEV_CLEANUP_PARAM, self.previous_value)
        self.env.registry.clear_cache()

    def _no_test_enable(self):
        """Simula el SERVIDOR REAL: sin `--test-enable` en el proceso."""
        return patch.dict(odoo.tools.config.options, {'test_enable': False})

    # ── 1. El ledger SV NO se relaja con el parámetro ─────────────────────
    def test_01_cleanup_no_se_relaja_via_config_parameter(self):
        """Con test_enable=False + parámetro 'True' el cleanup sigue denegado."""
        self.Icp.set_param(DEV_CLEANUP_PARAM, 'True')
        with self._no_test_enable():
            self.assertFalse(
                self.Marker._sv_test_enable_strict(),
                'La vía estricta no puede depender del parámetro')
            self.assertFalse(
                self.Marker.with_context(
                    madenat_sv_test_cleanup_token='token-de-prueba'
                )._sv_test_cleanup_allowed(
                    'madenat.guia.processing', [1]),
                'El parámetro no debe habilitar _sv_test_cleanup_allowed')
            with self.assertRaises(UserError):
                self.Marker._sv_test_mark('token-de-prueba', [])
            with self.assertRaises(UserError):
                self.Marker._sv_test_cleanup()

    # ── 2. La vía alternativa del Modo A SÍ se habilita ───────────────────
    def test_02_test_environment_ok_via_config_parameter(self):
        """test_enable=False + parámetro 'True' + BD de test → entorno OK."""
        self.Icp.set_param(DEV_CLEANUP_PARAM, 'True')
        with self._no_test_enable():
            self.assertTrue(self.Marker._sv_dev_cleanup_enabled())
            self.assertTrue(
                self.Marker._sv_test_environment_ok(),
                'El Modo A autoservicio debe habilitarse por parámetro')

    # ── 3. Candado 'test' in dbname: inviolable en ambas vías ─────────────
    def test_03_candado_dbname_obligatorio(self):
        """Ni la vía estricta ni la alternativa se activan fuera de 'test'."""
        self.Icp.set_param(DEV_CLEANUP_PARAM, 'True')
        with patch.object(self.env.cr, 'dbname', 'madenat_prod'):
            with self._no_test_enable():
                self.assertFalse(
                    self.Marker._sv_dev_cleanup_enabled(),
                    'El parámetro no puede activarse fuera de una BD *test*')
                self.assertFalse(
                    self.Marker._sv_test_environment_ok(),
                    "El candado 'test' in dbname es inviolable")
            # Incluso con `--test-enable` REAL, fuera de 'test' → False.
            self.assertFalse(
                self.Marker._sv_test_enable_strict(),
                'La vía estricta también exige el candado del nombre de BD')
            self.assertFalse(self.Marker._sv_test_environment_ok())

    # ── 4. La vía estricta ignora el parámetro ────────────────────────────
    def test_04_test_enable_strict_ignora_config_parameter(self):
        """Con test_enable real la vía estricta funciona aunque el parámetro esté en False."""
        self.Icp.set_param(DEV_CLEANUP_PARAM, 'False')
        self.assertTrue(
            self.Marker._sv_test_enable_strict(),
            'La vía estricta depende solo de test_enable + dbname')
        self.assertTrue(self.Marker._sv_test_environment_ok())
        # Y también con el parámetro ausente por completo.
        self.Icp.set_param(DEV_CLEANUP_PARAM, False)
        self.assertTrue(self.Marker._sv_test_enable_strict())
        self.assertTrue(self.Marker._sv_test_environment_ok())

    # ── 5. Fail-closed: solo el valor exacto 'True' habilita ──────────────
    def test_05_valor_no_canonico_no_habilita(self):
        """'true'/'1'/'yes'/'TRUE' NO habilitan la vía de desarrollo."""
        with self._no_test_enable():
            for value in ('true', '1', 'yes', 'TRUE', '', 'False'):
                self.Icp.set_param(DEV_CLEANUP_PARAM, value)
                self.assertFalse(
                    self.Marker._sv_dev_cleanup_enabled(),
                    'Valor no canónico %r no debe habilitar la vía' % value)
                self.assertFalse(self.Marker._sv_test_environment_ok())
