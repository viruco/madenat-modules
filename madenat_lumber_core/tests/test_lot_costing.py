# -*- coding: utf-8 -*-
"""Suite 1 — Regresión de costeo de lotes (stock.lot).

Protege los bugs corregidos en Fase A y Fase B1:
  C1.1 — wood_cost_usd incluido en total_cost_usd
  C1.2 — Sin doble conteo de costos logísticos
  C1.3 — margin_usd refleja costo real
  C1.4 — purchase_cost_usd deprecado, no participa en el total
"""
from odoo.tests import TransactionCase, tagged


@tagged('madenat_costing', 'suite1', 'lot_costing')
class TestLotCosting(TransactionCase):
    """Validación del modelo stock.lot tras saneamiento monetario."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lot = cls.env['stock.lot']
        cls.CostLine = cls.env['stock.lot.cost.line']
        cls.USD = cls.env.ref('base.USD', raise_if_not_found=False)

        # Producto mínimo
        cls.product = cls.env['product.product'].create({
            'name': 'Test Lumber',
            'type': 'product',
        })

        # Lote base con dimensiones y costo madera
        cls.lot = cls.Lot.create({
            'name': 'TEST-LOT-001',
            'product_id': cls.product.id,
            'wood_cost_usd': 5000.0,
            'volumen_m3': 10.0,
            'volumen_mbf': 4.237,
            'piezas': 100,
            'sale_price_usd_per_mbf': 2000.0,
        })

    # ── C1.1: wood_cost_usd incluido en total_cost_usd ──
    def test_total_includes_wood_cost(self):
        """total_cost_usd debe contener wood_cost_usd aunque no haya líneas."""
        self.assertEqual(self.lot.total_cost_usd, 5000.0,
                         "total_cost_usd debe reflejar wood_cost_usd cuando no hay cost_line_ids")

    # ── C1.2: Sin doble conteo de costos logísticos ──
    def test_no_double_count_logistic_costs(self):
        """Al agregar líneas de costo, total debe ser wood + líneas, no 2x."""
        self.CostLine.create([
            {'lot_id': self.lot.id, 'name': 'Freight', 'cost_type': 'freight',
             'amount_usd': 1000.0, 'date': '2026-06-01'},
            {'lot_id': self.lot.id, 'name': 'Port', 'cost_type': 'port',
             'amount_usd': 500.0, 'date': '2026-06-01'},
        ])
        expected = 5000.0 + 1000.0 + 500.0
        self.assertEqual(self.lot.total_cost_usd, expected,
                         f"total_cost_usd debe ser {expected} (wood + freight + port), no el doble")

    # ── C1.3: margin_usd correcto ──
    def test_margin_uses_correct_total(self):
        """margin_usd debe ser sale_amount_usd − total_cost_usd corregido."""
        self.lot.write({
            'sale_price_usd_per_mbf': 2000.0,
            'volumen_mbf': 4.237,
        })
        self.CostLine.create([
            {'lot_id': self.lot.id, 'name': 'Logistics', 'cost_type': 'logistic',
             'amount_usd': 800.0, 'date': '2026-06-01'},
        ])
        expected_revenue = 4.237 * 2000.0
        expected_cost = 5000.0 + 800.0
        expected_margin = expected_revenue - expected_cost
        self.assertAlmostEqual(self.lot.sale_amount_usd, expected_revenue, places=0,
                               msg="sale_amount_usd debe ser volumen_mbf × sale_price")
        self.assertAlmostEqual(self.lot.margin_usd, expected_margin, places=0,
                               msg="margin_usd debe ser revenue − total_cost_usd (sin doble conteo)")

    # ── C1.4: purchase_cost_usd deprecado ──
    def test_purchase_cost_usd_deprecated(self):
        """purchase_cost_usd no debe participar en total_cost_usd."""
        self.lot.write({'purchase_cost_usd': 99999.0})
        self.lot.flush()
        self.assertEqual(self.lot.total_cost_usd, 5000.0,
                         "purchase_cost_usd está deprecado y NO debe sumarse al total")

    # ── C1.5: cost_per_m3_usd coherente ──
    def test_cost_per_m3_coherent(self):
        """cost_per_m3_usd debe ser total_cost_usd / volumen_m3."""
        self.lot.write({
            'wood_cost_usd': 5000.0,
            'volumen_m3': 10.0,
        })
        expected = 5000.0 / 10.0
        self.assertAlmostEqual(self.lot.cost_per_m3_usd, expected, places=2,
                               msg="cost_per_m3_usd debe ser total / volumen_m3")

    # ── C1.6: cost_per_mbf_usd coherente ──
    def test_cost_per_mbf_coherent(self):
        """cost_per_mbf_usd debe ser total_cost_usd / volumen_mbf."""
        self.lot.write({
            'wood_cost_usd': 5000.0,
            'volumen_mbf': 4.237,
        })
        expected = 5000.0 / 4.237
        self.assertAlmostEqual(self.lot.cost_per_mbf_usd, expected, places=2,
                               msg="cost_per_mbf_usd debe ser total / volumen_mbf")