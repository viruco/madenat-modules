# -*- coding: utf-8 -*-
"""C2 — Ledger de costos por lote (destino de la distribución provisional).

Extiende `stock.lot.cost.line` (core) con la trazabilidad explícita que exige
la Política C2 de costeo provisional post-Entrega:

  - relación al Embarque y a la versión de distribución;
  - base de volumen logístico usada en el prorrateo;
  - monto asignado por lote (`allocated_cost_usd`) y su versión;
  - ciclo de vida append-only de la línea (`state`).

REGLAS DE ORO respetadas:
  - NO se usa SQL de escritura (todo por ORM).
  - NO se toca stock físico (move/quant/lote/cantidades).
  - `logistic_cost_usd` del lote NO se escribe aquí; lo recalcula el ORM
    (compute existente en `stock_lot_costing.py`) a partir de estas líneas.
  - El proveedor real de `stock.lot.cost.line` es `partnerid` (nunca
    `partner_id`).
"""
from odoo import models, fields, _
from odoo.exceptions import UserError


class StockLotCostLineC2(models.Model):
    _inherit = 'stock.lot.cost.line'

    # ── Trazabilidad logística C2 ─────────────────────────────────────────
    shipment_id = fields.Many2one(
        'lumber.export.shipment',
        string='Embarque (C2)',
        ondelete='set null',
        index=True,
        help='Embarque de exportación que originó este costeo provisional.',
    )

    version_number = fields.Integer(
        string='Versión de distribución (C2)',
        default=0,
        copy=False,
        index=True,
        help='Número de versión de la distribución de costos que originó la '
             'línea. Permite conservar el historial append-only.',
    )

    cost_category = fields.Char(
        string='Categoría de costo (C2)',
        copy=False,
        help='Categoría/concepto del costo de embarque de origen '
             '(traza informativa del prorrateo).',
    )

    volume_basis_m3 = fields.Float(
        string='Base de volumen (m³)',
        digits=(16, 3),
        copy=False,
        help='Volumen logístico final del lote usado como base de prorrateo.',
    )

    weight_basis_kg = fields.Float(
        string='Base de peso (kg)',
        digits=(16, 1),
        copy=False,
        help='Peso del lote registrado como referencia informativa del reparto.',
    )

    allocated_cost_usd = fields.Float(
        string='Costo asignado (USD)',
        digits=(16, 2),
        copy=False,
        help='Monto prorrateado asignado al lote en esta versión.',
    )

    state = fields.Selection(
        [
            ('applied', 'Aplicada'),
            ('superseded', 'Superada'),
            ('cancelled', 'Anulada'),
        ],
        string='Estado ledger (C2)',
        default='applied',
        copy=False,
        index=True,
        help='Ciclo de vida append-only del asiento de ledger C2. Una línea '
             'aplicada no se elimina; se marca superseded/cancelled.',
    )

    def unlink(self):
        """Impide el borrado de asientos de ledger C2 aplicados.

        El historial de costeo C2 es append-only. Las líneas de otras
        distribuciones (legacy, sin `is_c2`) conservan su comportamiento.
        """
        protected = self.filtered(
            lambda l: l.state == 'applied' and l.distribution_id.is_c2)
        if protected:
            raise UserError(_(
                'No se puede eliminar un asiento de ledger C2 aplicado '
                '(append-only). Marque la versión como superseded/cancelled.'))
        return super().unlink()
