# -*- coding: utf-8 -*-
"""Suite 4 — Compatibilidad entre módulos tras saneamiento monetario y puente contable.

Protege contra regresiones en la interacción entre módulos:
  C4.1 — billing puede leer total_cost_usd y margin_usd del lote
  C4.2 — logistics puede leer wood_cost_usd y sale_amount_usd
  C4.3 — costing no rompe la herencia de stock.lot
  C4.4 — campos Monetary son accesibles como floats (compatibilidad)
  C4.5 — purchase_cost_usd existe pero no afecta cálculos
  C4.6 — account_id es opcional en líneas nuevas
"""
from odoo.tests import TransactionCase, tagged


@tagged('madenat_costing', 'suite4', 'module_compatibility')
class TestModuleCompatibility(TransactionCase):
    """Validación de compatibilidad entre módulos dependientes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Lot = cls.env['stock.lot']
        cls.CostLine = cls.env['stock.lot.cost.line']
        cls.Account = cls.env['account.account']

        cls.product = cls.env['product.product'].create({
            'name': 'Compat Test Product',
            'type': 'product',
        })

        cls.lot = cls.Lot.create({
            'name': 'COMPAT-LOT-001',
            'product_id': cls.product.id,
            'wood_cost_usd': 5000.0,
            'volumen_m3': 10.0,
            'volumen_mbf': 4.237,
            'piezas': 100,
            'sale_price_usd_per_mbf': 2000.0,
        })

        cls.expense_account = cls.Account.search([
            ('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost']),
        ], limit=1)

    # ── C4.1: billing puede leer campos del lote ──
    def test_billing_reads_lot_fields(self):
        """Campos que billing consume deben ser accesibles."""
        fields_to_check = ['total_cost_usd', 'margin_usd', 'wood_cost_usd',
                           'margin_percent', 'volumen_mbf']
        for fname in fields_to_check:
            self.assertTrue(hasattr(self.lot, fname),
                            f"stock.lot debe tener campo '{fname}' para billing")
            val = getattr(self.lot, fname)
            self.assertIsNotNone(val, f"El campo '{fname}' no debe ser None")
            if fname in ('total_cost_usd', 'margin_usd', 'wood_cost_usd'):
                self.assertGreaterEqual(float(val) if val else 0.0, 0.0,
                                        f"Campo monetario '{fname}' debe ser >= 0")

    # ── C4.2: logistics puede leer wood_cost_usd y sale_amount_usd ──
    def test_logistics_reads_lot_fields(self):
        """Campos que logistics consume deben ser accesibles."""
        fields_to_check = ['wood_cost_usd', 'sale_amount_usd', 'vol_shipment_m3',
                           'volumen_m3']
        for fname in fields_to_check:
            self.assertTrue(hasattr(self.lot, fname),
                            f"stock.lot debe tener campo '{fname}' para logistics")
            val = getattr(self.lot, fname)
            self.assertIsNotNone(val, f"El campo '{fname}' no debe ser None")

    # ── C4.3: costing no rompe herencia de stock.lot ──
    def test_costing_inheritance_intact(self):
        """La herencia de madenat_lumber_costing sobre stock.lot debe ser funcional."""
        # Campos definidos en stock_lot_costing.py
        costing_fields = ['logistic_cost_usd', 'process_cost_usd', 'other_cost_usd',
                          'total_cost_clp', 'exchange_rate', 'costing_state']
        for fname in costing_fields:
            self.assertTrue(hasattr(self.lot, fname),
                            f"stock.lot debe tener campo '{fname}' (costing)")
            val = getattr(self.lot, fname)
            self.assertIsNotNone(val, f"El campo '{fname}' no debe ser None")

    # ── C4.4: campos Monetary son accesibles como float ──
    def test_monetary_fields_accessible_as_float(self):
        """Campos Monetary deben ser legibles como float para compatibilidad."""
        self.CostLine.create([
            {'lot_id': self.lot.id, 'name': 'Freight', 'cost_type': 'freight',
             'amount_usd': 1000.0, 'date': '2026-06-01'},
        ])
        total = self.lot.total_cost_usd
        margin = self.lot.margin_usd
        cost_m3 = self.lot.cost_per_m3_usd
        self.assertIsInstance(float(total), float,
                              "total_cost_usd debe ser convertible a float")
        self.assertIsInstance(float(margin), float,
                              "margin_usd debe ser convertible a float")
        self.assertIsInstance(float(cost_m3), float,
                              "cost_per_m3_usd debe ser convertible a float")

    # ── C4.5: purchase_cost_usd existe pero no afecta cálculos ──
    def test_purchase_cost_usd_exists_but_inert(self):
        """purchase_cost_usd debe existir (compatibilidad) pero no participa."""
        self.assertTrue(hasattr(self.lot, 'purchase_cost_usd'),
                        "purchase_cost_usd debe existir para compatibilidad")
        before = self.lot.total_cost_usd
        self.lot.write({'purchase_cost_usd': 99999.0})
        self.lot.flush()
        after = self.lot.total_cost_usd
        self.assertAlmostEqual(before, after, places=2,
                               msg="purchase_cost_usd NO debe cambiar total_cost_usd")

    # ── C4.6: account_id es opcional ──
    def test_cost_line_without_account(self):
        """Crear línea de costo sin account_id no debe fallar."""
        line = self.CostLine.create({
            'lot_id': self.lot.id,
            'name': 'Test without account',
            'cost_type': 'other',
            'amount_usd': 100.0,
            'date': '2026-06-01',
        })
        self.assertTrue(line.exists(), "Línea sin account_id debe crearse")
        self.assertFalse(line.account_id, "account_id debe ser False si no se asigna")

    def test_cost_line_with_account(self):
        """Crear línea de costo con account_id debe guardarlo."""
        if not self.expense_account:
            self.skipTest("No hay cuenta de gastos en el sistema")
        line = self.CostLine.create({
            'lot_id': self.lot.id,
            'name': 'Test with account',
            'cost_type': 'freight',
            'amount_usd': 500.0,
            'date': '2026-06-01',
            'account_id': self.expense_account.id,
        })
        self.assertEqual(line.account_id, self.expense_account,
                         "account_id debe persistir correctamente")