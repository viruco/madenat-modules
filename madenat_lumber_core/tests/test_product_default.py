# -*- coding: utf-8 -*-
"""
TESTS: Producto Maestro por Tipo de Ingreso (Fase 1)

Cobertura:
  1. Resolver producto global por `tipo_ingreso`.
  2. Preferir producto específico de compañía sobre el global.
  3. Preferir profile exacto sobre fallback sin profile.
  4. Lanzar UserError si no existe configuración.
  5. Validar que no se pueden crear reglas activas ambiguas.

No cubre parser de Excel, Intake ni facturación (fuera de alcance de Fase 1).
"""
import logging

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'madenat_product_default')
class TestMadenatLumberProductDefault(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env['madenat.ingestion.config']
        cls.Rule = cls.env['madenat.lumber.product.default']
        cls.Product = cls.env['product.product']

        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')

        cls.product_a = cls.Product.create({
            'name': 'Producto Fijo Test A',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })
        cls.product_b = cls.Product.create({
            'name': 'Producto Fijo Test B',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })

        # Aislar las reglas sembradas por el XML del módulo para que no
        # interfieran con las validaciones de esta suite.
        cls.Rule.search([]).write({'active': False})

    def _rule(self, tipo, product, profile=False, company=False, active=True):
        return self.Rule.create({
            'tipo_ingreso': tipo,
            'product_id': product.id,
            'ingestion_profile': profile or False,
            'company_id': company.id if company else False,
            'active': active,
        })

    def test_01_resolve_global_by_tipo(self):
        """Una regla global (sin compañía) resuelve por tipo de ingreso."""
        self._rule('bruta', self.product_a)

        prod = self.Config.get_default_product('bruta')

        self.assertEqual(prod, self.product_a)

    def test_02_prefer_company_over_global(self):
        """La regla de la compañía activa gana sobre la regla global."""
        self._rule('bruta', self.product_a)  # global
        self._rule('bruta', self.product_b, company=self.env.company)  # compañía

        prod = self.Config.get_default_product('bruta')

        self.assertEqual(prod, self.product_b)

    def test_03_prefer_profile_exact_over_fallback(self):
        """El perfil exacto gana sobre el fallback sin perfil."""
        self._rule('procesado', self.product_a)  # fallback (sin perfil)
        self._rule('procesado', self.product_b, profile='f1550')  # exacto

        prod_exacto = self.Config.get_default_product('procesado', profile='f1550')
        prod_fallback = self.Config.get_default_product('procesado')

        self.assertEqual(prod_exacto, self.product_b)
        self.assertEqual(prod_fallback, self.product_a)

    def test_04_user_error_when_missing(self):
        """Sin regla activa, debe lanzar UserError accionable."""
        with self.assertRaises(UserError):
            self.Config.get_default_product('bruta')

    def test_05_reject_ambiguous_active_rules(self):
        """No se pueden crear dos reglas activas para el mismo tipo/perfil/compañía."""
        self._rule('bruta', self.product_a)

        with self.assertRaises(ValidationError):
            self._rule('bruta', self.product_b)
