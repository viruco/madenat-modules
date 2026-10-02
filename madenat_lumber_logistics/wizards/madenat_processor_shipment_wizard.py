# -*- coding: utf-8 -*-
"""I1 canónico (CANON/19 §16) — Asistente «Envío a procesador».

Crea una **transferencia interna nativa** desde una ubicación interna de
MADENAT (bodega) hacia la ubicación del procesador ``Procesadores/<X>``, con
``lot_id`` por línea. La cantidad es **editable hacia abajo** (envío parcial);
nunca puede exceder el disponible real del lote en el origen.

Si el operador se **desvía** de la propuesta (envío parcial) se exige motivo y
se audita (AD-88, ``_guard_deviation``). El evento se registra siempre en
``madenat.audit.log`` con el tipo ADITIVO ``processor_shipment``.

Es una transferencia interna: **no** es exportación, venta ni rebaja. La
madera sigue siendo inventario de MADENAT (CANON/19 §5.4).
"""
import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round


class MadenatProcessorShipmentWizard(models.TransientModel):
    _name = 'madenat.processor.shipment.wizard'
    _description = 'Envío a procesador (transferencia interna nativa)'
    _inherit = ['madenat.deviation.mixin']

    processor_id = fields.Many2one(
        'res.partner', string='Procesador', required=True,
        domain="[('is_processor', '=', True)]")
    source_location_id = fields.Many2one(
        'stock.location', string='Origen', required=True,
        domain="[('usage', '=', 'internal')]")
    destination_location_id = fields.Many2one(
        'stock.location', string='Destino (procesador)', readonly=True)
    line_ids = fields.One2many(
        'madenat.processor.shipment.line', 'wizard_id', string='Lotes')
    reason = fields.Text(
        string='Motivo de la desviación',
        help='Obligatorio cuando la cantidad enviada es menor que la '
             'disponible (envío parcial). AD-88.')
    note = fields.Text(string='Observaciones')

    # ── Defaults y onchange ──────────────────────────────────────────────
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'source_location_id' in fields_list and not res.get(
                'source_location_id'):
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.company.id)], limit=1)
            if warehouse and warehouse.lot_stock_id:
                res['source_location_id'] = warehouse.lot_stock_id.id
        # «Asistente desde lotes»: si viene de stock.lot, precarga las líneas.
        if 'line_ids' in fields_list and not res.get('line_ids'):
            active_model = self.env.context.get('active_model')
            active_ids = self.env.context.get('active_ids') or []
            if active_model == 'stock.lot' and active_ids:
                source = res.get('source_location_id') or (
                    self.env['stock.warehouse'].search(
                        [('company_id', '=', self.env.company.id)],
                        limit=1).lot_stock_id.id)
                lines = []
                for lot in self.env['stock.lot'].browse(active_ids):
                    lines.append((0, 0, {
                        'lot_id': lot.id,
                        'source_location_id': source,
                    }))
                res['line_ids'] = lines
        return res

    @api.onchange('processor_id')
    def _onchange_processor_id(self):
        for wizard in self:
            wizard.destination_location_id = (
                wizard.processor_id.processor_location_id)

    @api.onchange('source_location_id')
    def _onchange_source_location_id(self):
        for wizard in self:
            for line in wizard.line_ids:
                line.source_location_id = wizard.source_location_id
                line.quantity = line.available_qty

    # ── Helpers ──────────────────────────────────────────────────────────
    @api.model
    def _available_qty(self, lot, location):
        """Disponible REAL del lote en la ubicación de origen (Σ quants)."""
        if not lot or not location:
            return 0.0
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', location.id),
            ('company_id', '=', self.env.company.id),
        ])
        return sum(quants.mapped('quantity'))

    # ── Acción principal ─────────────────────────────────────────────────
    def action_send(self):
        self.ensure_one()
        if not self.processor_id.is_processor:
            raise ValidationError(_(
                'El partner %s no está marcado como procesador.')
                % self.processor_id.name)
        if not self.line_ids:
            raise UserError(_('Debe seleccionar al menos un lote para enviar.'))
        destination = self.processor_id._get_or_create_processor_location()

        deviations = []
        prepared = []
        for line in self.line_ids:
            if not line.lot_id:
                continue
            if float_compare(line.quantity, 0.0,
                             precision_rounding=0.001) <= 0:
                raise ValidationError(_(
                    'La cantidad a enviar del lote %s debe ser mayor que cero.')
                    % line.lot_id.name)
            available = line.available_qty
            compare = float_compare(
                line.quantity, available, precision_rounding=0.001)
            if compare > 0:
                # Integridad técnica: duro (no puede exceder el disponible real).
                raise ValidationError(_(
                    'La cantidad del lote %s (%.3f m³) excede el disponible '
                    'real en el origen (%.3f m³).')
                    % (line.lot_id.name, line.quantity, available))
            if compare < 0:
                deviations.append(line)
            prepared.append(line)
        if not prepared:
            raise UserError(_('Debe seleccionar al menos un lote para enviar.'))

        # AD-88: el envío parcial es una desviación blanda (motivo + auditoría).
        if deviations:
            self._guard_deviation(
                'PROC-01',
                _('Envío parcial a %s: %d lote(s) por debajo de su disponible.')
                % (self.processor_id.name, len(deviations)),
                reason=self.reason, hard=False,
                extra={
                    'processor_id': self.processor_id.id,
                    'lots': [{
                        'lot': l.lot_id.name,
                        'sent': l.quantity,
                        'available': l.available_qty,
                    } for l in deviations],
                })

        picking = self._create_internal_picking(destination, prepared)
        self._audit_processor_shipment(picking, prepared)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Traslado interno'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_internal_picking(self, destination, lines):
        """Transferencia interna nativa: origen MADENAT → Procesadores/<X>."""
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.env.company.id),
        ], limit=1)
        if not picking_type:
            raise UserError(_(
                'No se encontró un tipo de operación de traslado interno '
                'para la compañía actual.'))

        picking = self.env['stock.picking'].create({
            'partner_id': self.processor_id.id,
            'picking_type_id': picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': destination.id,
            'origin': _('Envío a procesador: %s') % self.processor_id.name,
            'company_id': self.env.company.id,
        })

        Move = self.env['stock.move']
        MoveLine = self.env['stock.move.line']
        for line in lines:
            lot = line.lot_id
            qty = float_round(line.quantity, precision_digits=3)
            uom = lot.product_id.uom_id
            move_vals = {
                'name': _('Lote: %s') % lot.name,
                'product_id': lot.product_id.id,
                'product_uom_qty': qty,
                'product_uom': uom.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'company_id': self.env.company.id,
            }
            if 'picked' in Move._fields:
                move_vals['picked'] = True
            move = Move.create(move_vals)
            ml_vals = {
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': lot.product_id.id,
                'lot_id': lot.id,
                'quantity': qty,
                'product_uom_id': uom.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            }
            if 'picked' in MoveLine._fields:
                ml_vals['picked'] = True
            MoveLine.create(ml_vals)

        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        return picking

    def _audit_processor_shipment(self, picking, lines):
        """Evento de auditoría ADITIVO (``processor_shipment``)."""
        self.ensure_one()
        payload = {
            'processor_id': self.processor_id.id,
            'processor': self.processor_id.name,
            'picking': picking.name,
            'source': self.source_location_id.complete_name,
            'destination': picking.location_dest_id.complete_name,
            'lots': [{
                'lot': line.lot_id.name,
                'sent': line.quantity,
                'available': line.available_qty,
            } for line in lines],
            'reason': self.reason or '',
            'note': self.note or '',
            'user': self.env.user.id,
            'timestamp': fields.Datetime.now().isoformat(),
        }
        snapshot = json.dumps(payload, sort_keys=True, default=str)
        self.env['madenat.audit.log'].sudo().create({
            'action_type': 'processor_shipment',
            'description': _(
                'Envío a procesador %s: %d lote(s) → %s'
            ) % (self.processor_id.name, len(lines),
                 picking.location_dest_id.complete_name),
            'batch_id': picking.name,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })


class MadenatProcessorShipmentLine(models.TransientModel):
    _name = 'madenat.processor.shipment.line'
    _description = 'Línea de envío a procesador'

    wizard_id = fields.Many2one(
        'madenat.processor.shipment.wizard', required=True,
        ondelete='cascade')
    source_location_id = fields.Many2one(
        'stock.location', string='Origen',
        domain="[('usage', '=', 'internal')]")
    lot_id = fields.Many2one('stock.lot', string='Lote', required=True)
    product_id = fields.Many2one(
        'product.product', related='lot_id.product_id', readonly=True)
    lot_flow_type = fields.Selection(
        related='lot_id.lot_flow_type', string='Tipo', readonly=True)
    uom_id = fields.Many2one(
        'uom.uom', related='lot_id.product_id.uom_id', readonly=True)
    available_qty = fields.Float(
        string='Disponible (m³)', compute='_compute_available_qty',
        digits=(16, 3))
    quantity = fields.Float(
        string='A enviar (m³)', digits=(16, 3),
        help='Editable hacia abajo. Nunca puede exceder el disponible real.')

    @api.depends('lot_id', 'source_location_id', 'wizard_id.source_location_id')
    def _compute_available_qty(self):
        for line in self:
            location = (line.source_location_id
                        or line.wizard_id.source_location_id)
            line.available_qty = line.wizard_id._available_qty(
                line.lot_id, location)

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for line in self:
            if line.lot_id:
                if not line.source_location_id:
                    line.source_location_id = line.wizard_id.source_location_id
                line.quantity = line.available_qty
