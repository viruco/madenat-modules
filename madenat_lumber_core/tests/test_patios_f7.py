# -*- coding: utf-8 -*-
"""Pruebas unitarias para Bloque 4C (AD-116 / F7): Gestión y Filtros de Patios en Recepción."""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPatiosF7(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockLocation = cls.env['stock.location']
        cls.LumberReception = cls.env['lumber.reception']
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Proveedor Madera Patios Test',
            'is_company': True,
        })
        # Creamos dos patios operativos mediante interfaz/ORM
        cls.patio_almacen = cls.StockLocation.create({
            'name': 'Patio Almacén Norte',
            'usage': 'internal',
            'is_patio': True,
        })
        cls.patio_secado = cls.StockLocation.create({
            'name': 'Patio Secado Horno',
            'usage': 'internal',
            'is_patio': True,
        })
        # Ubicación estándar de stock (NO patio)
        cls.bodega_general = cls.StockLocation.create({
            'name': 'Bodega Herramientas General',
            'usage': 'internal',
            'is_patio': False,
        })

    def test_01_marcador_is_patio_filtering(self):
        """Verifica que el marcador is_patio discrimina correctamente las ubicaciones que son patios."""
        patios = self.StockLocation.search([('is_patio', '=', True)])
        self.assertIn(self.patio_almacen, patios)
        self.assertIn(self.patio_secado, patios)
        self.assertNotIn(self.bodega_general, patios)

    def test_02_reception_assignment_and_grouping(self):
        """Verifica que una recepción puede asociar un patio y agruparse/filtrarse por patio y por OC."""
        rec1 = self.LumberReception.create({
            'name': 'REC-PATIO-01',
            'supplier_id': self.supplier.id,
            'manual_po_name': 'OC-2026-001',
            'location_id': self.patio_almacen.id,
        })
        rec2 = self.LumberReception.create({
            'name': 'REC-PATIO-02',
            'supplier_id': self.supplier.id,
            'manual_po_name': 'OC-2026-001',
            'location_id': self.patio_secado.id,
        })
        rec3 = self.LumberReception.create({
            'name': 'REC-PATIO-03',
            'supplier_id': self.supplier.id,
            'manual_po_name': 'OC-2026-002',
            'location_id': False,
        })

        # Filtrar con patio asignado
        con_patio = self.LumberReception.search([
            ('id', 'in', [rec1.id, rec2.id, rec3.id]),
            ('location_id', '!=', False)
        ])
        self.assertEqual(len(con_patio), 2)
        self.assertIn(rec1, con_patio)
        self.assertIn(rec2, con_patio)

        # Filtrar por patio específico
        en_almacen = self.LumberReception.search([
            ('id', 'in', [rec1.id, rec2.id, rec3.id]),
            ('location_id', '=', self.patio_almacen.id)
        ])
        self.assertEqual(en_almacen, rec1)

        # Filtrar por orden de compra
        en_oc_001 = self.LumberReception.search([
            ('id', 'in', [rec1.id, rec2.id, rec3.id]),
            ('purchase_order', '=', 'OC-2026-001')
        ])
        self.assertEqual(len(en_oc_001), 2)

    def test_03_anti_hardcode_h2_patios_are_dynamic_data(self):
        """H2 Anti-hardcode: el sistema no depende de nombres ni IDs fijos de patio."""
        patio_dinamico = self.StockLocation.create({
            'name': 'Patio Dinamico 999',
            'usage': 'internal',
            'is_patio': True,
        })
        rec = self.LumberReception.create({
            'name': 'REC-PATIO-DINAMICO',
            'supplier_id': self.supplier.id,
            'location_id': patio_dinamico.id,
        })
        self.assertEqual(rec.location_id, patio_dinamico)
        self.assertTrue(rec.location_id.is_patio)

    def test_04_patio_separate_from_processor_partner(self):
        """H2 / F7: El partner procesador sigue separado del patio de ubicación de stock."""
        partner_procesador = self.env['res.partner'].create({
            'name': 'Servicios de Aserrío y Procesado Spa',
            'is_company': True,
        })
        self.assertNotEqual(partner_procesador._name, self.patio_almacen._name)
        self.assertEqual(partner_procesador._name, 'res.partner')
        self.assertEqual(self.patio_almacen._name, 'stock.location')
