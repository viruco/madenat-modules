# -*- coding: utf-8 -*-
"""Cobertura del modo de recepción directa a stock de Intake (sin BT-04).

Verifica que la marca ``intake_direct_stock`` de las guías creadas por Intake
omite la salida a proceso (BT-04) sin modificar el comportamiento del core
para guías fuera de Intake. Usa TransactionCase: nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeDirectStock(TransactionCase):
    """Recepción directa a stock desde Intake sin consumo de materia prima."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Direct Stock Test',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )

    def _make_service_guia(self, name, intake_direct_stock=False):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'service',
            'rate_usd': 800.0,
            'intake_direct_stock': intake_direct_stock,
        }
        return self.Guia.create(vals)

    def test_intake_direct_stock_omite_bt04(self):
        """Guía Intake sin source_lot_ids: no bloquea ni crea consumo."""
        guia = self._make_service_guia('DIRECT-STOCK-INTAKE', intake_direct_stock=True)
        result = guia._get_or_create_consumption_picking()
        self.assertFalse(result)
        self.assertFalse(guia.consumption_picking_id)

    def test_fuera_intake_mantiene_bt04(self):
        """Guía fuera de Intake sin source_lot_ids: BT-04 sigue bloqueando."""
        guia = self._make_service_guia('DIRECT-STOCK-CORE', intake_direct_stock=False)
        with self.assertRaises(UserError):
            guia._get_or_create_consumption_picking()

    def test_intake_direct_stock_idempotente(self):
        """Guía Intake: llamadas repetidas no crean consumo ni duplican."""
        guia = self._make_service_guia('DIRECT-STOCK-IDEMP', intake_direct_stock=True)
        r1 = guia._get_or_create_consumption_picking()
        r2 = guia._get_or_create_consumption_picking()
        self.assertFalse(r1)
        self.assertFalse(r2)
        self.assertFalse(guia.consumption_picking_id)
