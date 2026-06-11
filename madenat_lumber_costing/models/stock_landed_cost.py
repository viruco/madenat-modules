# -*- coding: utf-8 -*-
"""FASE B3 — Herencia de stock.landed.cost para trazabilidad MADENAT."""
from odoo import models, fields


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    madenat_distribution_id = fields.Many2one(
        'lumber.cost.distribution',
        string='Expediente MADENAT',
        readonly=True,
        ondelete='set null',
        index=True,
        help='Expediente de liquidación MADENAT que originó este landed cost.',
    )