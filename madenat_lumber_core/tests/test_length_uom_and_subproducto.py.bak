# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
import logging

_logger = logging.getLogger(__name__)

FACTOR_FT_TO_M = 0.3048
FACTOR_MM_TO_M = 0.001

DEFAULT_THICKNESS_MM = 25.0
DEFAULT_WIDTH_MM = 100.0
DEFAULT_LENGTH_M = 4.5
DEFAULT_PIECES = 10
DEFAULT_LOT_NAME = 'TEST-LOT-001'


class TestLengthUomAndSubproducto(TransactionCase):
    """
    Suite para validar:
    - conversión de largo ingresado en ft/mm/m hacia metros normalizados
    - persistencia del campo calculado lengthm
    - asignación de subproducto en una línea de recepción

    Convención activa del modelo lumber.reception.line:
    - length_input_raw
    - lengthuom
    - lengthm
    """

    def setUp(self):
        super().setUp()
        self.LumberReception = self.env['lumber.reception']
        self.LumberReceptionLine = self.env['lumber.reception.line']
        self.Product = self.env['product.template']
        self.Subproduct = self.env['madenat.subproducto']
        self.Partner = self.env['res.partner']

        self.supplier = self.Partner.create({
            'name': 'Proveedor Test SA',
            'vat': '76.123.456-7',
            'supplier_rank': 1,
        })

        self.product = self.Product.search([], limit=1)
        self.assertTrue(
            self.product,
            "Precondición fallida: no hay product.template disponible en la BD de test."
        )

        self.subproduct = self.Subproduct.create({
            'name': 'Subproducto Test',
            'code': 'TESTUOM',
        })

        self.reception = self.LumberReception.create({
            'name': 'TEST-UOM',
            'supplier_id': self.supplier.id,
            'ingestion_profile': 'metric',
        })

    def _make_line(self, length_raw=DEFAULT_LENGTH_M, length_uom='m', lot_name=DEFAULT_LOT_NAME):
        """
        Crea una línea mínima válida para probar conversiones de largo.
        """
        vals = {
            'reception_id': self.reception.id,
            'product_id': self.product.id,
            'lot_name': lot_name,
            'thickness': DEFAULT_THICKNESS_MM,
            'width': DEFAULT_WIDTH_MM,
            'length': DEFAULT_LENGTH_M,
            'length_input_raw': float(length_raw),
            'lengthuom': length_uom,
            'pieces': DEFAULT_PIECES,
            'export_calculation_rule': 'metric',
        }
        line = self.LumberReceptionLine.create(vals)
        self.assertTrue(line.id, "No se pudo crear la línea de recepción de prueba.")
        return line

    def test_29_length_ft_to_m(self):
        line = self._make_line(length_raw=8.0, length_uom='ft', lot_name='TEST-LOT-029')
        expected = round(8.0 * FACTOR_FT_TO_M, 6)
        self.assertAlmostEqual(
            line.lengthm,
            expected,
            places=4,
            msg=f"T29 FAIL: esperado {expected}, obtenido {line.lengthm}"
        )

    def test_30_length_mm_to_m(self):
        line = self._make_line(length_raw=3660.0, length_uom='mm', lot_name='TEST-LOT-030')
        expected = round(3660.0 * FACTOR_MM_TO_M, 6)
        self.assertAlmostEqual(
            line.lengthm,
            expected,
            places=4,
            msg=f"T30 FAIL: esperado {expected}, obtenido {line.lengthm}"
        )

    def test_31_length_m_default_unchanged(self):
        line = self._make_line(length_raw=4.5, length_uom='m', lot_name='TEST-LOT-031')
        self.assertAlmostEqual(
            line.lengthm,
            4.5,
            places=4,
            msg=f"T31 FAIL: esperado 4.5, obtenido {line.lengthm}"
        )

    def test_32_quickcreate_subproducto_desde_wizard(self):
        line = self._make_line(lot_name='TEST-LOT-032')

        nuevo_grado = self.Subproduct.create({
            'name': 'GRADO-TEST-T32',
            'code': 'T32',
        })
        self.assertTrue(
            nuevo_grado.id,
            "T32 FAIL: madenat.subproducto no se creó"
        )

        line.write({'subproduct_id': nuevo_grado.id})
        self.assertEqual(
            line.subproduct_id.id,
            nuevo_grado.id,
            "T32 FAIL: subproduct_id no se asignó correctamente"
        )
        _logger.info("T32 PASS: subproducto %s asignado a línea %s", nuevo_grado.code, line.lot_name)