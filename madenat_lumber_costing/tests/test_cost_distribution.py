# -*- coding: utf-8 -*-
"""Suite 2 — Regresión de distribución de costos (lumber.cost.distribution).

Protege bugs corregidos en Fase A, B1, B2, B3:
  C2.1 — action_apply_costs crea stock.lot.cost.line correctas
  C2.2 — account_id se propaga a las líneas de lote
  C2.3 — total_cost_usd se recalcula tras aplicar
  C2.4 — landed cost generado (si hay picking)
  C2.5 — action_reverse_costs limpia correctamente
"""
from odoo.tests import TransactionCase, tagged


@tagged('madenat_costing', 'suite2', 'cost_distribution')
class TestCostDistribution(TransactionCase):
    """Validación del motor de distribución de costos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Modelos
        cls.Distribution = cls.env['lumber.cost.distribution']
        cls.DistLine = cls.env['lumber.cost.distribution.line']
        cls.Lot = cls.env['stock.lot']
        cls.CostLine = cls.env['stock.lot.cost.line']
        cls.Account = cls.env['account.account']

        # Moneda
        cls.USD = cls.env.ref('base.USD', raise_if_not_found=False)

        # Producto
        cls.product = cls.env['product.product'].create({
            'name': 'Test Lumber Cost Dist',
            # Odoo 18: 'product' ya no es un tipo válido. Se usa 'consu'
            # (Goods) con is_storable=True para conservar el comportamiento
            # de bien almacenable que esperan los lotes de madera.
            'type': 'consu',
            'is_storable': True,
        })

        # Cuenta contable opcional
        cls.expense_account = cls.Account.search([
            ('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost']),
        ], limit=1)

        # Lotes de prueba
        cls.lot1 = cls.Lot.create({
            'name': 'CD-LOT-001',
            'product_id': cls.product.id,
            'wood_cost_usd': 3000.0,
            'volumen_m3': 5.0,
            'vol_shipment_m3': 4.8,
            'piezas': 50,
        })
        cls.lot2 = cls.Lot.create({
            'name': 'CD-LOT-002',
            'product_id': cls.product.id,
            'wood_cost_usd': 4000.0,
            'volumen_m3': 7.0,
            'vol_shipment_m3': 6.5,
            'piezas': 70,
        })

    # ── C2.1: action_apply_costs crea líneas correctas ──
    def test_apply_creates_cost_lines(self):
        """Al aplicar, se deben crear stock.lot.cost.line."""
        dist = self._create_draft_distribution()
        dist.lot_ids = [(6, 0, (self.lot1 | self.lot2).ids)]
        dist.action_apply_costs()
        self.assertEqual(dist.state, 'applied')
        self.assertTrue(len(dist.generated_line_ids) > 0,
                        "Debe generar al menos una línea de costo")
        for line in dist.generated_line_ids:
            self.assertGreater(line.amount_usd, 0,
                               f"Línea {line.name} debe tener amount_usd > 0")

    # ── C2.2: account_id propagado ──
    def test_account_id_propagated(self):
        """Si la línea de distribución tiene account_id, debe propagarse."""
        if not self.expense_account:
            self.skipTest("No hay cuenta de gastos configurada en el sistema")
        dist = self._create_draft_distribution()
        dist.cost_line_ids.write({'account_id': self.expense_account.id})
        dist.lot_ids = [(6, 0, (self.lot1 | self.lot2).ids)]
        dist.action_apply_costs()
        for line in dist.generated_line_ids:
            self.assertEqual(line.account_id, self.expense_account,
                             f"Línea {line.name} debe heredar account_id de la distribución")

    # ── C2.3: total_cost_usd recalculado ──
    def test_total_recalculated_after_apply(self):
        """total_cost_usd debe reflejar wood + cost_lines después de aplicar."""
        dist = self._create_draft_distribution()
        dist.lot_ids = [(6, 0, self.lot1.ids)]
        dist.action_apply_costs()
        generated = sum(dist.generated_line_ids.mapped('amount_usd'))
        expected = self.lot1.wood_cost_usd + generated
        self.assertAlmostEqual(self.lot1.total_cost_usd, expected, places=0,
                               msg=f"total debe ser {expected} (wood + lines) tras aplicar")

    # ── C2.4: landed cost generado ──
    # Nota: solo se generan landed costs si el lote tiene reception_id.picking_id
    def test_landed_cost_not_generated_without_picking(self):
        """Sin picking asociado, NO debe generar landed cost (no debe fallar)."""
        dist = self._create_draft_distribution()
        dist.lot_ids = [(6, 0, (self.lot1 | self.lot2).ids)]
        dist.action_apply_costs()
        self.assertEqual(dist.state, 'applied')
        # Sin reception → sin picking → sin landed cost
        self.assertEqual(len(dist.landed_cost_ids), 0,
                         "Sin picking, no debe generar landed costs")

    # ── C2.5: action_reverse_costs limpia correctamente ──
    def test_reverse_cleans_cost_lines(self):
        """Reversión debe eliminar líneas y volver a draft."""
        dist = self._create_draft_distribution()
        dist.lot_ids = [(6, 0, self.lot1.ids)]
        dist.action_apply_costs()
        self.assertEqual(dist.state, 'applied')
        dist.action_reverse_costs()
        self.assertEqual(dist.state, 'draft')
        self.assertEqual(len(dist.generated_line_ids), 0,
                         "Reversión debe eliminar todas las líneas generadas")

    # ── C0: regresión del bug `partnerid` (campo real en Odoo 18) ──
    def test_apply_with_partner_does_not_raise_invalid_field(self):
        """`action_apply_costs` de punta a punta con proveedor.

        Regresión: al propagar el proveedor se usaba `partner_id`, que NO es
        un campo de `stock.lot.cost.line` en Odoo 18 (el campo real es
        `partnerid`), provocando `ValueError: Invalid field 'partner_id'`.
        """
        partner = self.env['res.partner'].create({
            'name': 'Cost Supplier (regresión partnerid)',
            'supplier_rank': 1,
        })
        dist = self._create_draft_distribution()
        dist.partner_id = partner
        dist.cost_line_ids.write({'partner_id': partner.id})
        dist.lot_ids = [(6, 0, (self.lot1 | self.lot2).ids)]

        # Antes: ValueError: Invalid field 'partner_id' on 'stock.lot.cost.line'
        dist.action_apply_costs()

        self.assertEqual(dist.state, 'applied')
        self.assertTrue(
            dist.generated_line_ids,
            "action_apply_costs debe generar líneas de costo")
        for line in dist.generated_line_ids:
            self.assertEqual(
                line.partnerid, partner,
                "El proveedor debe propagarse al campo `partnerid`")

    def _create_draft_distribution(self):
        """Helper: crea una distribución en draft con una línea de costo."""
        dist = self.Distribution.create({
            'name': 'Nuevo',
            'ref': 'TEST-DIST',
            'target_model': 'manual',
        })
        self.DistLine.create({
            'distribution_id': dist.id,
            'cost_type': 'freight',
            'invoice_num': 'INV-TEST-001',
            'amount_original': 1500.0,
            'exchange_rate': 1.0,
            'distribution_method': 'volume_export',
        })
        return dist