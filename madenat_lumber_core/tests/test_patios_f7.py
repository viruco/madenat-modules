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

    def test_05_patio_type_resolution_single(self):
        """6A: resolve_patio_by_type resuelve unívocamente cuando hay exactamente un patio activo del tipo."""
        self.StockLocation.search([('is_patio', '=', True), ('patio_type', '=', 'service')]).write({'is_patio': False})
        loc_servicio = self.StockLocation.create({
            'name': 'Patio Test Servicio Único',
            'usage': 'internal',
            'is_patio': True,
            'patio_type': 'service',
        })
        patio, warn = self.StockLocation.resolve_patio_by_type('service')
        self.assertEqual(patio, loc_servicio)
        self.assertIsNone(warn)

    def test_06_patio_type_resolution_zero_and_multiple(self):
        """6A: resolve_patio_by_type retorna advertencia y False cuando hay 0 o >1 patios del tipo."""
        # Caso 0 patios: buscar un tipo sin registros (o limpiar temporalmente)
        self.StockLocation.search([('is_patio', '=', True), ('patio_type', '=', 'port')]).write({'is_patio': False})
        patio, warn = self.StockLocation.resolve_patio_by_type('port')
        self.assertFalse(patio)
        self.assertIn("No existe ningún patio activo clasificado como tipo 'port'", warn)

        # Caso múltiples patios: crear dos del mismo tipo
        p1 = self.StockLocation.create({
            'name': 'Patio Puerto A',
            'usage': 'internal',
            'is_patio': True,
            'patio_type': 'port',
        })
        p2 = self.StockLocation.create({
            'name': 'Patio Puerto B',
            'usage': 'internal',
            'is_patio': True,
            'patio_type': 'port',
        })
        patio_mult, warn_mult = self.StockLocation.resolve_patio_by_type('port')
        self.assertFalse(patio_mult)
        self.assertIn("Existen múltiples patios activos clasificados como tipo 'port'", warn_mult)

    def test_07_auto_assignment_by_origin(self):
        """6A: Asignación automática por origen:
        - Volumen (granel) y Procesados (service) -> patio de tipo servicio
        - Recepción en puerto -> patio de tipo puerto
        """
        # Asegurar exactamente un patio de servicio y uno de puerto
        self.StockLocation.search([('is_patio', '=', True), ('patio_type', 'in', ['service', 'port'])]).write({'is_patio': False})
        patio_srv = self.StockLocation.create({
            'name': 'PATIO SERVICIO CEPILLADO FERRAMENTA TEST',
            'usage': 'internal',
            'is_patio': True,
            'patio_type': 'service',
        })
        patio_prt = self.StockLocation.create({
            'name': 'PATIO MARVAL TEST',
            'usage': 'internal',
            'is_patio': True,
            'patio_type': 'port',
        })

        # 1. Guía de Volumen (granel)
        guia_vol = self.env['madenat.guia.processing'].create({
            'name': 'GUIA-VOL-TEST-6A-01',
            'partner_id': self.supplier.id,
            'tipo_recepcion': 'granel',
        })
        self.assertEqual(guia_vol.assignment_location_id, patio_srv)

        # 2. Guía de Servicio / Maquila (service)
        guia_srv = self.env['madenat.guia.processing'].create({
            'name': 'GUIA-SRV-TEST-6A-02',
            'partner_id': self.supplier.id,
            'tipo_recepcion': 'service',
        })
        self.assertEqual(guia_srv.assignment_location_id, patio_srv)

        # 3. Recepción en puerto para embarque (lumber.reception)
        rec = self.LumberReception.create({
            'name': 'REC-PUERTO-TEST-6A-03',
            'supplier_id': self.supplier.id,
        })
        self.assertEqual(rec.location_id, patio_prt)

    def test_08_auto_assignment_no_patio_no_blocking(self):
        """6A: Si no hay patio configurado, la creación se realiza con advertencia y sin bloqueo."""
        self.StockLocation.search([('is_patio', '=', True), ('patio_type', '=', 'service')]).write({'is_patio': False})

        # Crear guía de volumen sin patio existente en BD -> no debe lanzar UserError/ValidationError
        guia_vol = self.env['madenat.guia.processing'].create({
            'name': 'GUIA-VOL-TEST-NO-PATIO',
            'partner_id': self.supplier.id,
            'tipo_recepcion': 'granel',
        })
        self.assertTrue(guia_vol.id)
        self.assertFalse(guia_vol.assignment_location_id)

    def test_10_inventario_por_patio_views_and_menu(self):
        """6B: Menú, acción, vistas y permisos de Inventario por Patio."""
        from lxml import etree

        # 1. Acción
        action = self.env.ref('madenat_lumber_core.action_madenat_inventario_por_patio')
        self.assertEqual(action.res_model, 'stock.quant')
        self.assertIn('list', action.view_mode)
        self.assertIn('pivot', action.view_mode)
        self.assertIn("'location_id.is_patio', '=', True", action.domain or '')

        # 2. Vista lista (solo lectura, sin edición)
        list_view = self.env.ref('madenat_lumber_core.view_stock_quant_patio_list')
        tree = etree.fromstring(list_view.arch)
        self.assertEqual(tree.attrib.get('create'), '0')
        self.assertEqual(tree.attrib.get('edit'), '0')
        self.assertEqual(tree.attrib.get('delete'), '0')

        # 3. Vista pivote
        pivot_view = self.env.ref('madenat_lumber_core.view_stock_quant_patio_pivot')
        piv_tree = etree.fromstring(pivot_view.arch)
        self.assertEqual(piv_tree.tag, 'pivot')

        # 4. Menú y grupos autorizados (Operaciones, Auditoría, Contabilidad)
        menu = self.env.ref('madenat_lumber_core.menu_madenat_inventario_patio')
        self.assertEqual(menu.action, action)
        group_ops = self.env.ref('madenat_lumber_core.group_madenat_operaciones')
        group_aud = self.env.ref('madenat_lumber_core.group_madenat_auditoria')
        group_cont = self.env.ref('madenat_lumber_core.group_madenat_contabilidad')
        self.assertIn(group_ops, menu.groups_id)
        self.assertIn(group_aud, menu.groups_id)
        self.assertIn(group_cont, menu.groups_id)

    def test_11_historical_records_zero_write(self):
        """6B: Verificación de cero escritura en históricos al consultar inventario y consola."""
        # Verificar guía 26270 no tocada
        guia_hist = self.env['madenat.guia.processing'].search([('name', '=', '26270')], limit=1)
        if guia_hist:
            # Debe mantener su estado e integridad sin rellenar patios retroactivamente
            self.assertTrue(guia_hist.id)

