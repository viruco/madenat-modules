# -*- coding: utf-8 -*-
"""Pruebas unitarias para Bloque 4D-1 (AD-116 / F6): Parámetros de Secado en Horno en stock.lot."""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date


@tagged('post_install', '-at_install')
class TestDryingLotF6(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockLot = cls.env['stock.lot']
        cls.product = cls.env['product.product'].create({
            'name': 'Pino Radiata Secado Horno Test',
            'type': 'consu',
        })

    def test_01_drying_fields_optional(self):
        """Campos de secado son estrictamente opcionales: lote sin secado se crea sin error."""
        lot = self.StockLot.create({
            'name': 'LOTE-NO-DRYING-01',
            'product_id': self.product.id,
        })
        self.assertFalse(lot.drying_temp_c)
        self.assertFalse(lot.drying_duration_hours)
        self.assertFalse(lot.drying_date)

    def test_02_drying_valid_defaults(self):
        """Valores dentro de rangos por defecto (50-90 °C y 50-80 h) se guardan correctamente."""
        today = date.today()
        lot = self.StockLot.create({
            'name': 'LOTE-DRYING-VALID-01',
            'product_id': self.product.id,
            'drying_temp_c': 70.0,
            'drying_duration_hours': 65.0,
            'drying_date': today,
        })
        self.assertEqual(lot.drying_temp_c, 70.0)
        self.assertEqual(lot.drying_duration_hours, 65.0)
        self.assertEqual(lot.drying_date, today)

    def test_03_temp_out_of_range_raises_validation_error(self):
        """Temperatura fuera de rango (menor a 50 o mayor a 90) dispara ValidationError."""
        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'LOTE-DRYING-TEMP-LOW',
                'product_id': self.product.id,
                'drying_temp_c': 45.0,
            })

        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'LOTE-DRYING-TEMP-HIGH',
                'product_id': self.product.id,
                'drying_temp_c': 95.0,
            })

    def test_04_duration_out_of_range_raises_validation_error(self):
        """Duración fuera de rango (menor a 50 o mayor a 80) dispara ValidationError."""
        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'LOTE-DRYING-DUR-LOW',
                'product_id': self.product.id,
                'drying_duration_hours': 40.0,
            })

        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'LOTE-DRYING-DUR-HIGH',
                'product_id': self.product.id,
                'drying_duration_hours': 85.0,
            })

    def test_05_anti_hardcode_h4_dynamic_drying_parameters(self):
        """H4 Anti-hardcode: cambiar el parámetro de configuración altera la validación."""
        param_obj = self.env['ir.config_parameter'].sudo()
        # Ampliamos temporalmente el rango mínimo a 40.0 °C
        param_obj.set_param('madenat.drying_temp_min_c', '40.0')

        # Ahora 45.0 °C es aceptado
        lot = self.StockLot.create({
            'name': 'LOTE-DRYING-DYNAMIC-45C',
            'product_id': self.product.id,
            'drying_temp_c': 45.0,
        })
        self.assertEqual(lot.drying_temp_c, 45.0)

        # Restauramos valor por defecto
        param_obj.set_param('madenat.drying_temp_min_c', '50.0')
