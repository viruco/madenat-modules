# -*- coding: utf-8 -*-
"""
Pruebas unitarias para pre_deploy_health_check.py (AD-121 / Bloque 4I).
TDD: normalización de versiones y definición de consultas oficiales B y A.2.
"""
import unittest
import os
import sys

# Permitir importación directa del script
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from odoo.tests.common import TransactionCase
from pre_deploy_health_check import (
    normalize_module_version,
    CANONICAL_HASH_B,
    CANONICAL_HASH_A2,
    BASELINE_WRITE_DATE_HASH,
)


class TestPreDeployHealthCheck(TransactionCase):
    """Pruebas unitarias para el script de comprobación pre-deploy."""

    def test_01_version_normalization(self):
        """Verifica que la normalización elimine el prefijo de serie Odoo (18.0.)."""
        # Caso madenat_lumber_billing: instalado '18.0.1.0.0' vs manifiesto '1.0.0'
        self.assertEqual(normalize_module_version('18.0.1.0.0'), '1.0.0')
        self.assertEqual(normalize_module_version('1.0.0'), '1.0.0')
        self.assertEqual(normalize_module_version('18.0.1.0.0'), normalize_module_version('1.0.0'))

        # Módulos con versión larga
        self.assertEqual(normalize_module_version('18.0.6.17.0'), '6.17.0')
        self.assertEqual(normalize_module_version('18.0.1.39.0'), '1.39.0')

        # Casos borde
        self.assertEqual(normalize_module_version(''), '')
        self.assertEqual(normalize_module_version(None), '')

    def test_02_canonical_hashes_defined(self):
        """Verifica que los hashes canónicos oficiales B y A.2 estén definidos según CANON/17."""
        # Consulta B (volúmenes de negocio redondeados a 4 decimales)
        self.assertEqual(CANONICAL_HASH_B['stock_lot'], '5c2152193194066e5585b383ffe3673a')
        self.assertEqual(CANONICAL_HASH_B['madenat_guia_processing_line'], '356e70066083febd59645c1212e11ece')
        self.assertEqual(CANONICAL_HASH_B['lumber_shipment_line'], 'bb5863f5850244b06b9235c2c595709b')

        # Consulta A.2 (nombre y volumen sin marcas temporales)
        self.assertEqual(CANONICAL_HASH_A2['stock_lot'], '6b1ec7d8dcd91cc6bd7ff90772759500')
        self.assertEqual(CANONICAL_HASH_A2['madenat_guia_processing_line'], 'e78e0265210add0676b240bed091921f')
        self.assertEqual(CANONICAL_HASH_A2['lumber_shipment_line'], 'b13357af2864a6cbeb3a386dff188a8e')

        # Línea base fijada de write_date (solo informativa)
        self.assertEqual(BASELINE_WRITE_DATE_HASH['stock_lot'], '6667a4bd9f3aeff24a8588d32da23ed2')


if __name__ == '__main__':
    unittest.main()
