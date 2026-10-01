# -*- coding: utf-8 -*-
"""A-3 / AC-5: el asistente de asignación usa el DISPONIBLE base nominal.

Cubre el caso del lote 2585 (volumen de origen 4,939 m³ pero disponible real
4,358 m³) y la exclusión de lotes sin disponible.

Datos 100% aislados (no toca contenedores, embarques ni lotes históricos).
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestContainerLotWizardDisponible(TransactionCase):
    """El wizard mide disponibilidad/capacidad en disponible nominal."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'WIZ Disponible Lumber',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'WIZ Disponible Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Container = cls.env['lumber.container']
        cls.Wizard = cls.env['lumber.container.lot.wizard']

    def _make_guia(self, name):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
        })

    def _make_lot(self, guia, label, ref_volume, disponible):
        lot = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'guia_processing_id': guia.id,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': ref_volume,
            'vol_shipment_m3': ref_volume,
        })
        if disponible > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_container(self, name):
        shipment = self.env['lumber.export.shipment'].create({
            'name': 'EMB-%s' % name,
            'customer_id': self.partner.id,
        })
        return self.Container.create({
            'name': name,
            'container_type': '40HC',
            'shipment_id': shipment.id,
        })

    def test_01_totales_usan_disponible_no_volumen_origen(self):
        """Lote 2585-style: disponible 4,358 < origen 4,939."""
        guia = self._make_guia('WIZ-DISP-01')
        lot = self._make_lot(guia, 'WIZ-LOT-01', ref_volume=4.939,
                             disponible=4.358)
        self.assertAlmostEqual(lot.volumen_m3, 4.939, places=3)
        self.assertAlmostEqual(lot.volumen_restante_m3, 4.358, places=3)

        container = self._make_container('CONT-WIZ-01')
        wizard = self.Wizard.create({
            'container_id': container.id,
            'selected_lot_ids': [(6, 0, [lot.id])],
        })
        # El total proyectado usa DISPONIBLE (4,358), no el origen (4,939).
        self.assertAlmostEqual(wizard.new_total_volume_m3, 4.358, places=3)

    def test_02_disponible_acumula_contenedor_mas_seleccion(self):
        """El total = disponible ya consolidado + disponible seleccionado."""
        guia = self._make_guia('WIZ-DISP-02')
        lot_a = self._make_lot(guia, 'WIZ-LOT-02A', 2.0, 2.0)
        lot_b = self._make_lot(guia, 'WIZ-LOT-02B', 3.0, 3.0)

        container = self._make_container('CONT-WIZ-02')
        wizard = self.Wizard.create({
            'container_id': container.id,
            'selected_lot_ids': [(6, 0, [lot_a.id, lot_b.id])],
        })
        self.assertAlmostEqual(wizard.new_total_volume_m3, 5.0, places=3)

    def test_03_available_excluye_lote_sin_disponible(self):
        """Un lote con disponible <= 0 no se ofrece en available_lot_ids."""
        guia = self._make_guia('WIZ-DISP-03')
        con_stock = self._make_lot(guia, 'WIZ-LOT-03A', 3.0, 3.0)
        sin_stock = self._make_lot(guia, 'WIZ-LOT-03B', 3.0, 0.0)

        container = self._make_container('CONT-WIZ-03')
        wizard = self.Wizard.create({'container_id': container.id})
        available = wizard.available_lot_ids
        self.assertIn(con_stock, available)
        self.assertNotIn(sin_stock, available)
