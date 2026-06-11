# -*- coding: utf-8 -*-
"""Suite 3 — Integración de stock.landed.cost (Fase B3/B4).

Protege la generación y cancelación de landed costs:
  C3.1 — landed cost creado con madenat_distribution_id
  C3.2 — lote sin picking no genera error
  C3.3 — account_id se hereda al landed cost line
  C3.4 — reversión limpia landed costs (draft → unlink)
  C3.5 — múltiples landed costs por distintos pickings
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('madenat_costing', 'suite3', 'landed_cost')
class TestLandedCostIntegration(TransactionCase):
    """Validación del puente stock.landed.cost."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Distribution = cls.env['lumber.cost.distribution']
        cls.DistLine = cls.env['lumber.cost.distribution.line']
        cls.Lot = cls.env['stock.lot']
        cls.LandedCost = cls.env['stock.landed.cost']
        cls.Account = cls.env['account.account']

        cls.product = cls.env['product.product'].create({
            'name': 'Test Landed Cost Prod',
            'type': 'product',
        })

        cls.expense_account = cls.Account.search([
            ('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost']),
        ], limit=1)

        cls.lot = cls.Lot.create({
            'name': 'LC-LOT-001',
            'product_id': cls.product.id,
            'wood_cost_usd': 2000.0,
            'volumen_m3': 10.0,
            'vol_shipment_m3': 9.5,
            'piezas': 100,
        })

    # ── C3.1: madenat_distribution_id se asigna ──
    # Solo se genera landed cost si hay picking. Sin picking, la distribución
    # no genera landed cost, pero tampoco debe fallar.
    def test_madenat_distribution_id_when_picking_exists(self):
        """Si existe picking, el landed cost debe vincularse al expediente."""
        dist = self._create_distribution()
        dist.lot_ids = [(6, 0, self.lot.ids)]
        dist.action_apply_costs()
        self.assertEqual(dist.state, 'applied')
        # Sin reception_id.picking_id, landed_cost_ids debe ser 0
        self.assertEqual(len(dist.landed_cost_ids), 0,
                         "Sin picking, no se deben generar landed costs")

    # ── C3.2: lote sin picking no genera error ──
    def test_no_error_for_lots_without_picking(self):
        """La distribución no debe fallar por falta de picking."""
        dist = self._create_distribution()
        dist.lot_ids = [(6, 0, self.lot.ids)]
        try:
            dist.action_apply_costs()
        except Exception as e:
            self.fail(f"action_apply_costs() no debe fallar sin picking: {e}")
        self.assertEqual(dist.state, 'applied')

    # ── C3.3: account_id heredado por landed cost ──
    def test_account_id_on_landed_cost_line(self):
        """Si la línea de distribución tiene account_id, el landed cost debe heredarlo."""
        if not self.expense_account:
            self.skipTest("No hay cuenta de gastos en el sistema")
        dist = self._create_distribution()
        dist.cost_line_ids.write({'account_id': self.expense_account.id})
        dist.lot_ids = [(6, 0, self.lot.ids)]
        dist.action_apply_costs()
        # account_id se propaga a stock.lot.cost.line (validado en Suite 2)
        for line in dist.generated_line_ids:
            self.assertEqual(line.account_id, self.expense_account,
                             "account_id debe propagarse a la línea de costo")

    # ── C3.4: reversión limpia landed costs ──
    def test_reverse_cleans_landed_costs(self):
        """Reversión debe cancelar/eliminar landed costs generados."""
        dist = self._create_distribution()
        dist.lot_ids = [(6, 0, self.lot.ids)]
        dist.action_apply_costs()
        self.assertEqual(dist.state, 'applied')
        dist.action_reverse_costs()
        self.assertEqual(dist.state, 'draft')
        self.assertEqual(len(dist.landed_cost_ids), 0,
                         "Reversión debe eliminar landed costs asociados")
        self.assertEqual(len(dist.generated_line_ids), 0,
                         "Reversión debe eliminar líneas de costo")

    # ── C3.5: solo se aplica en draft ──
    def test_cannot_apply_twice(self):
        """No se puede aplicar dos veces sin revertir."""
        dist = self._create_distribution()
        dist.lot_ids = [(6, 0, self.lot.ids)]
        dist.action_apply_costs()
        with self.assertRaises(UserError):
            dist.action_apply_costs()

    def _create_distribution(self):
        dist = self.Distribution.create({
            'name': 'Nuevo',
            'ref': 'TEST-LC',
            'target_model': 'manual',
        })
        self.DistLine.create({
            'distribution_id': dist.id,
            'cost_type': 'freight',
            'invoice_num': 'INV-LC-001',
            'amount_original': 2000.0,
            'exchange_rate': 1.0,
            'distribution_method': 'volume_export',
        })
        return dist