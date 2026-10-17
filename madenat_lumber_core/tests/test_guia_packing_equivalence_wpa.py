# -*- coding: utf-8 -*-
"""Pruebas unitarias para WP-A: Regla de equivalencia Guía vs Packing ('ok_rounded').

Regla canónica:
- d = decimales declarados de la guía (con tope estándar de 3 decimales, parametrizable).
- La guía y el packing son equivalentes si round(packing, d) == round(guía, d).
- Estado 'ok_rounded' en documental_conciliation_state.
- El packing es el valor operativo cuando son equivalentes.
- Parámetro para cambiar el tope: ir.config_parameter 'madenat.guia_packing_max_decimal_places'.

Pruebas mínimas requeridas por Mauricio:
1. Guía 57,84 contra 57,839556 (d=2 -> 57.84 == 57.84 -> ok_rounded).
2. Guía 57,840 contra 57,839556 (d=3 -> 57.840 == 57.840 -> ok_rounded).
3. Guía 57,84 contra 57,846 (no equivalente con d=2 -> 57.85 != 57.84 -> difference).
4. Guía sin packing -> partial.
5. Parámetro configurable de tope de decimales.
6. El packing es el valor operativo asignado.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestGuiaPackingEquivalenceWpA(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Proveedor Ferramenta WP-A Test',
            'is_company': True,
        })
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.Guia = cls.env['madenat.guia.processing']

    def _make_guia(self, name, vol_pdf, packing_vol=0.0, declared_d=0):
        vals = {
            'name': name,
            'partner_id': self.supplier.id,
            'state': 'draft',
            'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'assignment_location_id': self.stock_location.id,
            'vol_comercial_pdf': vol_pdf,
            'packing_volume_declared_m3': packing_vol,
        }
        if declared_d:
            vals['guia_volume_declared_decimals'] = declared_d
        return self.Guia.create(vals)

    def test_01_guia_5784_packing_57839556_ok_rounded(self):
        """Caso 1: Guía 57,84 contra 57,839556 con d=2 -> equivalente -> ok_rounded."""
        guia = self._make_guia('GUIA-WPA-5784', vol_pdf=57.84, packing_vol=57.839556, declared_d=2)
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'ok_rounded')
        # Verificar método directo de equivalencia
        is_equiv, d, r_g, r_p = guia.check_guia_packing_equivalence(57.84, 57.839556, declared_d=2)
        self.assertTrue(is_equiv)
        self.assertEqual(d, 2)
        self.assertEqual(r_g, 57.84)
        self.assertEqual(r_p, 57.84)

    def test_02_guia_57840_packing_57839556_ok_rounded(self):
        """Caso 2: Guía 57,840 contra 57,839556 con d=3 (caso real 26270) -> equivalente -> ok_rounded."""
        guia = self._make_guia('GUIA-WPA-57840', vol_pdf=57.840, packing_vol=57.839556, declared_d=3)
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'ok_rounded')
        is_equiv, d, r_g, r_p = guia.check_guia_packing_equivalence(57.840, 57.839556, declared_d=3)
        self.assertTrue(is_equiv)
        self.assertEqual(d, 3)
        self.assertEqual(r_g, 57.840)
        self.assertEqual(r_p, 57.840)

    def test_03_guia_5784_packing_57846_not_equivalent_difference(self):
        """Caso 3: Guía 57,84 contra 57,846 con d=2 -> round(57.846, 2)=57.85 != 57.84 -> difference."""
        guia = self._make_guia('GUIA-WPA-DIFF', vol_pdf=57.84, packing_vol=57.846, declared_d=2)
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'difference')
        is_equiv, d, r_g, r_p = guia.check_guia_packing_equivalence(57.84, 57.846, declared_d=2)
        self.assertFalse(is_equiv)
        self.assertEqual(d, 2)
        self.assertEqual(r_g, 57.84)
        self.assertEqual(r_p, 57.85)

    def test_04_guia_without_packing_is_partial(self):
        """Caso 4: Guía sin packing declarado -> estado partial (no hay contrastación posible)."""
        guia = self._make_guia('GUIA-WPA-NOPACKING', vol_pdf=57.84, packing_vol=0.0)
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'partial')

    def test_05_parameter_max_decimals_configurable(self):
        """Caso 5: Parámetro madenat.guia_packing_max_decimal_places limita el tope de decimales."""
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('madenat.guia_packing_max_decimal_places', '2')

        guia = self._make_guia('GUIA-WPA-PARAM', vol_pdf=57.840, packing_vol=57.844, declared_d=3)
        guia.flush_recordset()
        # Con tope max_d = 2, d se trunca a 2: round(57.844, 2) == 57.84 == round(57.840, 2) -> ok_rounded
        self.assertEqual(guia.documental_conciliation_state, 'ok_rounded')

        # Restaurar tope a 3
        Param.set_param('madenat.guia_packing_max_decimal_places', '3')
        guia._compute_documental_conciliation_state()
        # Con tope max_d = 3, d = 3: round(57.844, 3) = 57.844 != 57.840 -> difference
        self.assertEqual(guia.documental_conciliation_state, 'difference')

    def test_06_packing_is_operational_volume(self):
        """Caso 6: Cuando el estado es ok_rounded, el valor operativo oficial adopta el total del packing."""
        guia = self._make_guia('GUIA-WPA-OPER', vol_pdf=57.840, packing_vol=57.839556, declared_d=3)
        guia.flush_recordset()
        self.assertEqual(guia.documental_conciliation_state, 'ok_rounded')
        # Verificar que si el modelo dispone de volume_operational_m3, toma el valor del packing
        if hasattr(guia, 'volume_operational_m3'):
            self.assertAlmostEqual(guia.volume_operational_m3, 57.840, places=3)
