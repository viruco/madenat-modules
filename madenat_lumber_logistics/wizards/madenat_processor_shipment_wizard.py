# -*- coding: utf-8 -*-
"""I1 canónico (CANON/19 §16) — Asistente «Envío a procesador» (AD-89/AD-90).

Crea una **transferencia interna nativa** desde una ubicación interna de
MADENAT (bodega) hacia la ubicación del procesador ``Procesadores/<X>``, con
``lot_id`` por línea. La cantidad es **editable hacia abajo** (envío parcial);
nunca puede exceder la **disponibilidad libre real** del lote en el origen
(físico − reservado por otros movimientos) — AD-89 D-I1-04.

**AD-89 D-I1-03:** un envío **parcial manual no es una desviación**. El motivo
(AD-88 ``_guard_deviation``) se exige **solo** cuando existe una
propuesta/planificación/reserva/cantidad previa **persistida y verificable**
para el lote y la cantidad ejecutada difiere de ella. En I1 el asistente **no**
persiste esa referencia (``_get_deviation_reference`` ⇒ ``None``): el parcial
manual se valida y se audita como **operación normal**, sin inventar una
propuesta artificial.

El evento se registra SIEMPRE en ``madenat.audit.log`` con el tipo ADITIVO
``processor_shipment`` (snapshot + SHA-256). Se añade un único ``deviation``
solo si hubo desviación **real** respecto de una referencia persistida.

**AD-90:** es una transferencia interna: **no** es exportación, venta, rebaja,
consumo, merma ni genealogía. La madera sigue siendo inventario de MADENAT
(CANON/19 §5.4).
"""
import hashlib
import json
from collections import defaultdict

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
    picking_id = fields.Many2one(
        'stock.picking', string='Traslado generado', readonly=True,
        help='Transferencia interna creada. Se conserva para garantizar la '
             'idempotencia: reintentar la acción no duplica el picking, los '
             'movimientos ni la auditoría.')
    reason = fields.Text(
        string='Motivo de la desviación',
        help='Opcional. Solo se exige cuando existe una referencia previa '
             'persistida (propuesta/planificación/reserva/cantidad previa) y '
             'la cantidad enviada difiere de ella. Un envío parcial manual '
             'NO requiere motivo (AD-89 D-I1-03).')
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

    # ── Helpers de disponibilidad (AD-89 D-I1-04) ────────────────────────
    @api.model
    def _quants_for(self, lot, location):
        """Quants del lote en la ubicación de origen exacta (producto + UoM)."""
        if not lot or not location:
            return self.env['stock.quant']
        return self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', location.id),
            ('company_id', '=', self.env.company.id),
        ])

    @api.model
    def _availability(self, lot, location):
        """Físico / reservado (por otros) / libre, por producto, lote,
        ubicación de origen y UoM — con APIs nativas de Odoo.

        * ``physical``: Σ ``quantity`` de los quants del lote en el origen.
        * ``reserved``: Σ ``reserved_quantity`` — reservas de **otros**
          movimientos (el picking propio aún no existe al validar; nunca se
          restan reservas del propio picking ni se alteran las ajenas).
        * ``free``: ``stock.quant._get_available_quantity(..., strict=True)``
          (API nativa) = disponible realmente reservable = físico − reservado.
        """
        if not lot or not location:
            return {'physical': 0.0, 'reserved': 0.0, 'free': 0.0}
        quants = self._quants_for(lot, location)
        physical = float_round(
            sum(quants.mapped('quantity')), precision_digits=3)
        reserved = float_round(
            sum(quants.mapped('reserved_quantity')), precision_digits=3)
        free = self.env['stock.quant']._get_available_quantity(
            lot.product_id, location, lot_id=lot, strict=True)
        return {
            'physical': physical,
            'reserved': reserved,
            'free': float_round(max(free, 0.0), precision_digits=3),
        }

    @api.model
    def _available_qty(self, lot, location):
        """Disponible **libre** del lote en el origen (AD-89).

        Compatibilidad: antes devolvía el físico (Σ quants). Desde AD-89
        devuelve el **libre** (físico − reservado ajeno), que es el techo real
        del envío.
        """
        return self._availability(lot, location)['free']

    def _get_deviation_reference(self, line):
        """Cantidad de referencia previa **persistida** para la línea, o None.

        AD-89 D-I1-03: el motivo obligatorio aplica solo frente a una
        propuesta, planificación, reserva o cantidad previa **persistida y
        verificable**. En I1 el asistente **no** persiste ninguna referencia
        (no se inventa una propuesta artificial), por lo que el envío parcial
        manual es válido sin motivo. Fases posteriores (p. ej. I4, propuesta de
        imputación) pueden sobreescribir este hook.
        """
        return None

    # ── Acción principal ─────────────────────────────────────────────────
    def action_send(self):
        self.ensure_one()
        # Idempotencia: reintentar no duplica picking/movimientos/auditoría.
        if self.picking_id:
            return self._picking_action(self.picking_id)

        if not self.processor_id.is_processor:
            raise ValidationError(_(
                'El partner %s no está marcado como procesador.')
                % self.processor_id.name)
        if not self.line_ids:
            raise UserError(_('Debe seleccionar al menos un lote para enviar.'))

        # Disponibilidad: consolidado por (lote, ubicación de origen). El techo
        # es el LIBRE real (físico − reservado ajeno); nunca el físico bruto.
        requested = defaultdict(float)
        reports = {}
        labels = {}
        for line in self.line_ids:
            if not line.lot_id:
                continue
            if float_compare(line.quantity, 0.0,
                             precision_rounding=0.001) <= 0:
                raise ValidationError(_(
                    'La cantidad a enviar del lote %s debe ser mayor que cero.')
                    % line.lot_id.name)
            location = line.source_location_id or self.source_location_id
            key = (line.lot_id.id, location.id)
            requested[key] += line.quantity
            reports[key] = self._availability(line.lot_id, location)
            labels[key] = (line.lot_id.name, location.display_name)

        for key, qty in requested.items():
            avail = reports[key]
            if float_compare(qty, avail['free'],
                             precision_rounding=0.001) > 0:
                lot_name, loc_name = labels[key]
                raise ValidationError(_(
                    'Disponibilidad insuficiente para el lote %(lot)s en '
                    '%(loc)s.\n'
                    'Físico: %(physical).3f m³ | Reservado por otros '
                    'movimientos: %(reserved).3f m³ | Libre: %(free).3f m³ | '
                    'Solicitado: %(requested).3f m³.\n'
                    'La cantidad solicitada excede el disponible libre. Ajuste '
                    'la cantidad: no se alteran las reservas de otros '
                    'movimientos (AD-89).') % {
                        'lot': lot_name, 'loc': loc_name,
                        'physical': avail['physical'],
                        'reserved': avail['reserved'],
                        'free': avail['free'],
                        'requested': qty})

        prepared = self.line_ids.filtered(lambda l: l.lot_id)
        if not prepared:
            raise UserError(_('Debe seleccionar al menos un lote para enviar.'))

        # AD-89 D-I1-03: solo hay desviación si existe una referencia previa
        # persistida y la cantidad difiere de ella. En I1 no existe ⇒ sin
        # motivo ni evento deviation (el parcial manual es operación normal).
        deviations = []
        for line in prepared:
            reference = self._get_deviation_reference(line)
            if reference is None:
                continue
            if float_compare(line.quantity, reference,
                             precision_rounding=0.001) != 0:
                deviations.append((line, reference))
        if deviations:
            self._guard_deviation(
                'PROC-01',
                _('Desviación respecto de la referencia previa al enviar a '
                  '%s.') % self.processor_id.name,
                reason=self.reason, hard=False,
                extra={
                    'processor_id': self.processor_id.id,
                    'lines': [{
                        'lot': l.lot_id.name,
                        'sent': l.quantity,
                        'reference': reference,
                    } for l, reference in deviations],
                })

        destination = self.processor_id._get_or_create_processor_location()
        picking = self._create_internal_picking(destination, prepared)
        self._audit_processor_shipment(picking, prepared)
        self.picking_id = picking.id
        return self._picking_action(picking)

    def _picking_action(self, picking):
        """Acción de ventana hacia el traslado generado (idempotente)."""
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
                'physical': line.physical_qty,
                'reserved': line.reserved_qty,
            } for line in lines],
            # Backorder nativo (si lo hubiere): se hace visible en la auditoría
            # sin duplicar el envío (AD-89 D-I1-04). Aquí no se forma porque
            # `quantity == product_uom_qty` y `picked=True` (ver T7).
            'backorders': picking.backorder_ids.mapped('name'),
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
    physical_qty = fields.Float(
        string='Físico (m³)', compute='_compute_available_qty',
        digits=(16, 3))
    reserved_qty = fields.Float(
        string='Reservado por otros (m³)', compute='_compute_available_qty',
        digits=(16, 3))
    available_qty = fields.Float(
        string='Libre (m³)', compute='_compute_available_qty',
        digits=(16, 3))
    quantity = fields.Float(
        string='A enviar (m³)', digits=(16, 3),
        help='Editable hacia abajo. Nunca puede exceder el disponible LIBRE '
             '(físico − reservado por otros). AD-89 D-I1-04.')

    @api.depends('lot_id', 'source_location_id', 'wizard_id.source_location_id')
    def _compute_available_qty(self):
        for line in self:
            location = (line.source_location_id
                        or line.wizard_id.source_location_id)
            avail = line.wizard_id._availability(line.lot_id, location)
            line.physical_qty = avail['physical']
            line.reserved_qty = avail['reserved']
            line.available_qty = avail['free']

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for line in self:
            if line.lot_id:
                if not line.source_location_id:
                    line.source_location_id = line.wizard_id.source_location_id
                line.quantity = line.available_qty
