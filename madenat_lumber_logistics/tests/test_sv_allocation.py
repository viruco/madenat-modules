# -*- coding: utf-8 -*-
"""Programa SV — asignación de etiquetas SV a contenedor/embarque.

Cubre: rebaja explícita vinculada, tope acumulado, una SV en varios embarques,
un embarque con varias SV, liberación con reversa y regresión de lotes no-SV.
Datos 100% aislados (no toca contenedores, embarques ni lotes históricos).
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics',
        'sv')
class TestSvAllocation(TransactionCase):
    """Integración SV-only de la asignación logística."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SV Logistics Lumber',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'SV Logistics Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Container = cls.env['lumber.container']

    # ── Fábricas aisladas ─────────────────────────────────────────────────
    def _make_guia(self, name='SV-LOG-GUIA'):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
        })

    def _make_sv_lot(self, guia, label, volume=40.300):
        return self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'piezas': 1,
            'volume_purchase_m3': volume,
            'vol_shipment_m3': volume,
            'volumen_m3': volume,
        })

    def _make_shipment(self, name='EMB-SV-TEST'):
        return self.env['lumber.export.shipment'].create({
            'name': name,
            'customer_id': self.partner.id,
        })

    def _make_container(self, name='CONT-SV-TEST', shipment=None):
        shipment = shipment or self._make_shipment(
            'EMB-%s' % (name or 'SV'))
        return self.Container.create({
            'name': name,
            'container_type': '40HC',
            'shipment_id': shipment.id,
        })

    def _allocate(self, container, lot, volume=0.0):
        container.with_context(
            madenat_sv_rebaja_per_lot=volume,
        ).write({'lot_ids': [(4, lot.id)]})

    def _applied_rebajas(self, lot):
        return self.Operation.search([
            ('lot_id', '=', lot.id),
            ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied'),
        ])

    # ── Pruebas ───────────────────────────────────────────────────────────
    def test_01_asignacion_crea_rebaja_vinculada(self):
        guia = self._make_guia('SV-LOG-01')
        lot = self._make_sv_lot(guia, 'SV00000000201')
        container = self._make_container('CONT-SV-01')

        self._allocate(container, lot, volume=10.0)

        rebajas = self._applied_rebajas(lot)
        self.assertEqual(len(rebajas), 1)
        self.assertEqual(rebajas.destination_container_id, container)
        self.assertEqual(rebajas.destination_shipment_id, container.shipment_id)
        self.assertAlmostEqual(rebajas.rebaja_volume_m3, 10.0, places=3)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 30.300, places=3)
        self.assertEqual(lot.container_id, container)

    def test_02_tope_acumulado_bloqueado(self):
        guia = self._make_guia('SV-LOG-02')
        lot = self._make_sv_lot(guia, 'SV00000000202')
        container_a = self._make_container('CONT-SV-02A')
        container_b = self._make_container('CONT-SV-02B')
        self._allocate(container_a, lot, volume=30.0)

        with self.assertRaises(ValidationError):
            self._allocate(container_b, lot, volume=20.0)

        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 10.300, places=3)
        self.assertEqual(len(self._applied_rebajas(lot)), 1)
        self.assertGreaterEqual(lot.sv_available_m3, 0.0)

    def test_03_una_sv_en_varios_embarques_con_trazabilidad(self):
        """Regla real: un lote no puede estar en dos contenedores activos.

        La trazabilidad multi-embarque se logra liberando (reversa) la
        asignación anterior antes de asignar la nueva, quedando ambas rebajas
        vinculadas a su contenedor/embarque en el ledger.
        """
        guia = self._make_guia('SV-LOG-03')
        lot = self._make_sv_lot(guia, 'SV00000000203')
        container_a = self._make_container('CONT-SV-03A')
        container_b = self._make_container('CONT-SV-03B')

        # 1) Asignación parcial al embarque A.
        self._allocate(container_a, lot, volume=10.0)
        # 2) Mientras siga en A, la regla de contenedores impide duplicarlo.
        with self.assertRaises(ValidationError):
            self._allocate(container_b, lot, volume=5.0)
        # 3) Liberación de A (reversa de la rebaja) y reasignación a B.
        container_a.with_context(
            madenat_sv_rebaja_per_lot=0.0,
        ).write({'lot_ids': [(3, lot.id)]})
        self._allocate(container_b, lot, volume=25.0)

        # Trazabilidad: 2 rebajas ligadas a contenedores distintos; la primera
        # quedó reversada y la segunda activa.
        rebajas = self.Operation.search([
            ('lot_id', '=', lot.id), ('action_type', '=', 'rebaja')])
        self.assertEqual(len(rebajas), 2)
        self.assertEqual(
            set(rebajas.mapped('destination_container_id').ids),
            {container_a.id, container_b.id})
        reversed_rebajas = rebajas.filtered(lambda op: op.state == 'reversed')
        self.assertEqual(len(reversed_rebajas), 1)
        self.assertEqual(
            reversed_rebajas.destination_container_id, container_a)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 15.300, places=3)

    def test_04_un_embarque_con_varias_sv(self):
        guia_a = self._make_guia('SV-LOG-04A')
        guia_b = self._make_guia('SV-LOG-04B')
        lot_a = self._make_sv_lot(guia_a, 'SV00000000204')
        lot_b = self._make_sv_lot(guia_b, 'SV00000000205')
        container = self._make_container('CONT-SV-04')

        self._allocate(container, lot_a, volume=5.0)
        self._allocate(container, lot_b, volume=7.0)

        self.assertEqual(len(self._applied_rebajas(lot_a)), 1)
        self.assertEqual(len(self._applied_rebajas(lot_b)), 1)
        self.assertEqual(
            self._applied_rebajas(lot_a).destination_container_id, container)
        self.assertEqual(
            self._applied_rebajas(lot_b).destination_container_id, container)

    def test_05_liberacion_reversa_la_rebaja(self):
        guia = self._make_guia('SV-LOG-05')
        lot = self._make_sv_lot(guia, 'SV00000000206')
        container = self._make_container('CONT-SV-05')
        self._allocate(container, lot, volume=12.0)
        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 28.300, places=3)

        container.with_context(
            madenat_sv_rebaja_per_lot=0.0,
        ).write({'lot_ids': [(3, lot.id)]})

        lot.invalidate_recordset()
        self.assertAlmostEqual(lot.sv_available_m3, 40.300, places=3)
        rebaja = self._applied_rebajas(lot)
        self.assertFalse(rebaja, 'La rebaja liberada queda reversada')

    def test_06_lotes_no_sv_sin_cambios_funcionales(self):
        legacy = self.StockLot.create({
            'name': 'LEGACY-LOT-01',
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        container = self._make_container('CONT-SV-06')

        self._allocate(container, legacy, volume=0.0)

        legacy.invalidate_recordset()
        self.assertEqual(legacy.container_id, container)
        self.assertEqual(legacy.estado_trazabilidad, 'consolidado')
        self.assertFalse(self.Operation.search([('lot_id', '=', legacy.id)]))
        self.assertTrue(container.line_ids.filtered(
            lambda line: line.lot_id == legacy))
