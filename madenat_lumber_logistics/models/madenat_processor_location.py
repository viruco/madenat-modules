# -*- coding: utf-8 -*-
"""I1 canónico (CANON/19 §5.4 y §16) — Ubicaciones y saldo por procesador.

- ``res.partner.processor_location_id``: ubicación interna
  ``Procesadores/<PROCESADOR>`` creada **bajo demanda** e **idempotente**
  desde ``res.partner``.
- ``stock.location.processor_partner_id``: vínculo inverso (procesador dueño
  de la sub-ubicación), usado como eje del saldo por procesador.
- ``stock.quant``: campos de agrupación (procesador y tipo de lote) para la
  vista de solo lectura «Saldo por Procesador».

Todas las ubicaciones son ``usage='internal'``: **el inventario sigue siendo
de MADENAT** (CANON/19 §5.4). No se crea grupo nuevo (§9).
"""
from odoo import api, fields, models, _

PROCESSOR_ROOT_NAME = 'Procesadores'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    processor_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación del procesador',
        domain="[('usage', '=', 'internal')]",
        copy=False,
        index=True,
        help='Ubicación interna «Procesadores/<PROCESADOR>» que representa el '
             'inventario de MADENAT en poder de este procesador. Se crea bajo '
             'demanda (CANON/19 §5.4).',
    )

    @api.model
    def _madenat_processor_root_location(self):
        """Devuelve (creándola si falta) la ubicación padre «Procesadores»."""
        Location = self.env['stock.location']
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company.id)], limit=1)
        parent = warehouse.lot_stock_id or self.env.ref(
            'stock.stock_location_stock')
        # Idempotencia: se busca antes de crear (nunca se duplica).
        root = Location.search([
            ('name', '=', PROCESSOR_ROOT_NAME),
            ('location_id', '=', parent.id),
            ('usage', '=', 'internal'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not root:
            root = Location.create({
                'name': PROCESSOR_ROOT_NAME,
                'location_id': parent.id,
                'usage': 'internal',
                'company_id': company.id,
            })
        return root

    def _get_or_create_processor_location(self):
        """Ubicación interna ``Procesadores/<partner>`` idempotente."""
        self.ensure_one()
        Location = self.env['stock.location']
        root = self._madenat_processor_root_location()
        location = self.processor_location_id
        if not location:
            location = Location.search([
                ('name', '=', self.name),
                ('location_id', '=', root.id),
                ('usage', '=', 'internal'),
            ], limit=1)
        if not location:
            location = Location.create({
                'name': self.name,
                'location_id': root.id,
                'usage': 'internal',
                'company_id': root.company_id.id,
                'processor_partner_id': self.id,
            })
        if location.processor_partner_id != self:
            location.processor_partner_id = self.id
        if self.processor_location_id != location:
            self.processor_location_id = location.id
        return location

    def action_get_or_create_processor_location(self):
        """Botón: crea/actualiza la ubicación del procesador (idempotente)."""
        for partner in self:
            partner._get_or_create_processor_location()
        return True


class StockLocation(models.Model):
    _inherit = 'stock.location'

    processor_partner_id = fields.Many2one(
        'res.partner',
        string='Procesador',
        index=True,
        copy=False,
        ondelete='set null',
        help='Procesador (res.partner) cuyo inventario MADENAT reside en esta '
             'sub-ubicación de «Procesadores» (CANON/19 §5.4).',
    )


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    madenat_processor_id = fields.Many2one(
        'res.partner',
        string='Procesador',
        related='location_id.processor_partner_id',
        store=True,
        index=True,
        help='Procesador titular de la ubicación del quant (solo quant en '
             '«Procesadores/<X>»).',
    )
    madenat_lot_flow_type = fields.Selection(
        related='lot_id.lot_flow_type',
        string='Tipo de lote',
        store=True,
        help='Tipo de flujo del lote (tarja / volumen) para agrupar el saldo.',
    )
