# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class TollProcessingOrder(models.Model):
    _name = 'toll.processing.order'
    _description = 'Orden Procesamiento Terceros'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_sent desc, name desc'
    
    # === CABECERA ===
    name = fields.Char(
        string='Número Orden', 
        required=True, 
        default=lambda self: _('New'), 
        copy=False, 
        readonly=True, 
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviado a Procesador'),
        ('in_process', 'En Proceso'),
        ('completed', 'Completado'), # Operativamente listo
        ('invoiced', 'Facturado'),   # Financieramente cerrado
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True, copy=False)
    
    # === ORIGEN Y ENVÍO ===
    source_type = fields.Selection([
        ('from_stock', 'Desde Stock Existente'),
        ('from_drop_ship', 'Drop Shipment Directo'),
    ], string='Tipo Origen', default='from_stock', required=True, tracking=True)
    
    source_lot_ids = fields.Many2many(
        'stock.lot', 
        'toll_order_lot_rel', 
        'toll_order_id', 
        'lot_id', 
        string='Lotes Origen',
        domain="[('toll_order_id', '=', False), ('volumen_m3', '>', 0), ('product_id.name', 'not ilike', 'CEPILLADO'), ('product_id.name', 'not ilike', 'CEP.')]",
        help="Muestra solo materia prima disponible (con volumen, sin procesar, no asignada)."
    )
    
    source_reception_id = fields.Many2one('lumber.reception', string='Recepción Origen')
    
    # === PROCESADOR Y SERVICIO ===
    processor_id = fields.Many2one(
        'res.partner', 
        string='Procesador', 
        required=True, 
        domain="[('is_processor', '=', True)]", 
        tracking=True
    )
    
    processor_location = fields.Char(
        string='Ubicación Planta',
        compute='_compute_processor_location',
        store=True,
        readonly=True
    )

    # Producto para facturación del servicio (Ej: "Servicio de Secado")
    service_product_id = fields.Many2one(
        'product.product',
        string='Producto Servicio',
        domain="[('type', '=', 'service')]",
        help="Producto de tipo servicio utilizado para generar la factura de proveedor.",
        required=False
    )
    
    # === DETALLES DE PROCESO ===
    process_type = fields.Selection([
        ('planing', 'Cepillado'),
        ('drying', 'Secado'),
        ('planing_drying', 'Cepillado + Secado'),
        ('treatment', 'Tratamiento Químico'),
        ('other', 'Otro'),
    ], string='Tipo Proceso', required=True, default='planing_drying', tracking=True)
    
    process_description = fields.Text(string='Descripción Proceso')
    
    # === FECHAS ===
    date_sent = fields.Date(string='Fecha Envío', tracking=True)
    date_expected_return = fields.Date(string='Fecha Est. Retorno', compute='_compute_expected_return_date', store=True)
    date_actual_return = fields.Date(string='Fecha Real Retorno', tracking=True)
    lead_time_days = fields.Integer(string='Lead Time (días)', default=7)
    
    # === COSTOS ===
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.ref('base.USD'), required=True)
    
    process_cost_per_m3 = fields.Monetary(string='Costo Proceso /m³', currency_field='currency_id')
    
    total_process_cost = fields.Monetary(
        string='Costo Total Estimado', 
        compute='_compute_total_cost', 
        store=True, 
        currency_field='currency_id'
    )

    actual_process_cost = fields.Monetary(
        string='Costo Real a Facturar',
        compute='_compute_actual_cost',
        store=True,
        currency_field='currency_id',
        help="Costo final basado en el volumen realmente retornado."
    )
    
    # === METRICAS Y RETORNO (INTEGRACION GUIA PROCESSING) ===
    expected_volume_m3 = fields.Float(string='Volumen Esperado (m³)', compute='_compute_volumes', store=True, digits=(16, 3))
    
    # Integración con Guías de Retorno
    return_guide_ids = fields.One2many(
        'madenat.guia.processing', 
        'toll_order_id', 
        string='Guías de Retorno'
    )
    
    return_guide_count = fields.Integer(compute='_compute_return_guide_count')

    actual_return_volume_m3 = fields.Float(
        string='Volumen Real Retorno (m³)', 
        compute='_compute_return_volume', 
        store=True, 
        digits=(16, 3),
        help="Suma del volumen de los lotes recibidos en las guías asociadas."
    )
    
    expected_yield_pct = fields.Float(string='Yield Esperado (%)', default=87.0)
    
    actual_yield_pct = fields.Float(
        string='Yield Real (%)', 
        compute='_compute_actual_yield', 
        store=True, 
        digits=(5, 2)
    )
    
    notes = fields.Text(string='Notas')

    # === FACTURACIÓN ===
    invoice_ids = fields.One2many('account.move', 'toll_order_id', string='Facturas')
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    # === CONSUMO DE MATERIA PRIMA (NUEVO) ===
    consumption_picking_id = fields.Many2one(
        'stock.picking', 
        string='Consumo Materia Prima',
        readonly=True,
        help="Albarán de salida generado automáticamente para dar de baja la materia prima procesada."
    )

    # ==============================================================================================
    #                                     MÉTODOS COMPUTADOS
    # ==============================================================================================

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)

    @api.depends('processor_id')
    def _compute_processor_location(self):
        for order in self:
            if order.processor_id and hasattr(order.processor_id, 'processor_location'):
                order.processor_location = order.processor_id.processor_location
            else:
                order.processor_location = False

    @api.depends('date_sent', 'lead_time_days')
    def _compute_expected_return_date(self):
        for order in self:
            if order.date_sent and order.lead_time_days:
                order.date_expected_return = order.date_sent + timedelta(days=order.lead_time_days)
            else:
                order.date_expected_return = False

    @api.depends('source_lot_ids.volumen_m3', 'source_reception_id.commercial_volume_m3')
    def _compute_volumes(self):
        for order in self:
            if order.source_lot_ids:
                order.expected_volume_m3 = sum(order.source_lot_ids.mapped('volumen_m3'))
            elif order.source_reception_id:
                order.expected_volume_m3 = order.source_reception_id.commercial_volume_m3
            else:
                order.expected_volume_m3 = 0.0

    @api.depends('expected_volume_m3', 'process_cost_per_m3')
    def _compute_total_cost(self):
        for order in self:
            order.total_process_cost = order.expected_volume_m3 * order.process_cost_per_m3

    @api.depends('actual_return_volume_m3', 'process_cost_per_m3')
    def _compute_actual_cost(self):
        for order in self:
            order.actual_process_cost = order.actual_return_volume_m3 * order.process_cost_per_m3

    @api.depends('return_guide_ids')
    def _compute_return_guide_count(self):
        for order in self:
            order.return_guide_count = len(order.return_guide_ids)

    @api.depends('return_guide_ids.state', 'return_guide_ids.lot_ids') 
    def _compute_return_volume(self):
        """Calcula el volumen real basado en los lotes generados por las guías de retorno validadas."""
        for order in self:
            total_vol = 0.0
            valid_guides = order.return_guide_ids.filtered(lambda g: g.state != 'cancelled')
            for guide in valid_guides:
                if guide.lot_ids:
                    total_vol += sum(guide.lot_ids.mapped('volumen_m3'))
            order.actual_return_volume_m3 = total_vol

    @api.depends('expected_volume_m3', 'actual_return_volume_m3')
    def _compute_actual_yield(self):
        for order in self:
            if order.expected_volume_m3 > 0:
                order.actual_yield_pct = (order.actual_return_volume_m3 / order.expected_volume_m3) * 100
            else:
                order.actual_yield_pct = 0.0

    # ==============================================================================================
    #                                     ACCIONES Y LÓGICA
    # ==============================================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('toll.processing.order') or _('New')
        return super().create(vals_list)
    
    @api.constrains('source_lot_ids', 'source_reception_id')
    def _check_source(self):
        for order in self:
            if order.state != 'draft' and not order.source_lot_ids and not order.source_reception_id:
                raise ValidationError("La orden debe tener origen: lotes existentes O recepción drop shipment")
    
    
    def action_mark_sent(self):
        self._check_source()
        self.write({'state': 'sent', 'date_sent': fields.Date.today()})
        self.message_post(body=f"Material enviado a procesador {self.processor_id.name}", subject="Material Enviado")
    
    def action_mark_in_process(self):
        self.write({'state': 'in_process'})
    
    def action_mark_completed(self):
        """Finaliza el ciclo operativo sin facturar aún"""
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.ensure_one()
        if self.state in ('completed', 'invoiced'):
            raise UserError("No puede cancelar una orden ya completada o facturada.")
        self.write({'state': 'cancelled'})
        self.message_post(body="Orden cancelada", subject="Orden Cancelada")

    def action_view_source_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lotes Origen'),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.source_lot_ids.ids)],
            'context': {'group_by': 'origin_reception_id'}, # AQUÍ SÍ FUNCIONA
        }


    def action_view_return_guides(self):
        """Abre las guías de procesamiento asociadas"""
        self.ensure_one()
        return {
            'name': _('Guías de Retorno'),
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.guia.processing',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.return_guide_ids.ids)],
            'context': {
                'default_toll_order_id': self.id,
                'default_partner_id': self.processor_id.id,
                'default_tipo_recepcion': 'servicio',
                'create': True,
            }
        }

    # === LÓGICA DE CONSUMO AUTOMÁTICO (CIERRE DE CICLO) ===
    def _get_lot_consumption_sources(self, lot, required_qty):
        """
        Determina las ubicaciones internas físicas de donde consumir el lote y la
        cantidad a descontar de cada una, respetando disponibilidad real (libre),
        categoría de unidad de medida (volumen) y compañía.

        :param lot: registro stock.lot
        :param required_qty: float (volumen a consumir en m³)
        :return: list of tuples (stock.location, qty_to_consume)
        :raises: UserError si no hay disponibilidad suficiente, quants válidos o unidad no es volumen
        """
        company = getattr(self, 'company_id', False) or self.env.company
        uom_m3 = self.env.ref('uom.product_uom_cubic_meter')
        product_uom = lot.product_id.uom_id

        # 1. Validación de categoría de unidad de medida (garantía de volumen)
        if product_uom.category_id != uom_m3.category_id:
            raise UserError(_(
                "El producto %(prod)s del lote %(lot)s tiene la unidad de medida '%(uom)s' "
                "(categoría: %(cat)s), la cual no pertenece a la categoría de Volumen. "
                "Toda la madera en MADENAT debe medirse en volumen."
            ) % {
                'prod': lot.product_id.display_name,
                'lot': lot.display_name,
                'uom': product_uom.name,
                'cat': product_uom.category_id.name,
            })

        # Conversión de la cantidad requerida a la UoM del producto (si difiere de m³)
        if product_uom != uom_m3:
            required_product_qty = uom_m3._compute_quantity(
                required_qty, product_uom, rounding_method='HALF-UP'
            )
        else:
            required_product_qty = required_qty

        uom_rounding = product_uom.rounding or 0.001
        required_product_qty = float_round(required_product_qty, precision_rounding=uom_rounding)

        # 2. Buscar todos los quants internos del lote para la compañía
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('product_id', '=', lot.product_id.id),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', company.id),
            ('quantity', '>', 0),
        ], order='id asc')

        if not quants:
            raise UserError(_(
                "No se encontraron existencias en ubicaciones internas para el lote %(lot)s "
                "(Producto: %(prod)s, Compañía: %(comp)s)."
            ) % {
                'lot': lot.display_name,
                'prod': lot.product_id.display_name,
                'comp': company.display_name,
            })

        # Extraer ubicaciones únicas preservando orden
        locations = self.env['stock.location']
        for q in quants:
            if q.location_id not in locations:
                locations |= q.location_id

        sources = []
        remaining = required_product_qty
        total_available = 0.0

        for loc in locations:
            # Disponibilidad libre real (físico - reservado para otros movimientos)
            # _get_available_quantity retorna en la UoM del producto (product_uom)
            free_qty = self.env['stock.quant']._get_available_quantity(
                lot.product_id, loc, lot_id=lot, strict=True
            )
            free_qty = float_round(max(free_qty, 0.0), precision_rounding=uom_rounding)
            total_available = float_round(total_available + free_qty, precision_rounding=uom_rounding)

            if float_compare(remaining, 0.0, precision_rounding=uom_rounding) <= 0:
                continue

            if float_compare(free_qty, 0.0, precision_rounding=uom_rounding) > 0:
                take_qty = float_round(min(remaining, free_qty), precision_rounding=uom_rounding)
                sources.append((loc, take_qty))
                remaining = float_round(remaining - take_qty, precision_rounding=uom_rounding)

        if float_compare(remaining, 0.0, precision_rounding=uom_rounding) > 0:
            raise UserError(_(
                "Disponibilidad insuficiente para consumir el lote %(lot)s. "
                "Requerido: %(req).3f %(uom)s, disponible para reservar: %(avail).3f %(uom)s "
                "(Compañía: %(comp)s)."
            ) % {
                'lot': lot.display_name,
                'req': required_product_qty,
                'avail': total_available,
                'uom': product_uom.name,
                'comp': company.display_name,
            })

        return sources

    def _create_consumption_picking(self):
        """
        🚀 Genera el albarán de consumo (Salida a Producción) para los lotes de origen
        desde su ubicación física real.
        Regla de Oro: Consumir lo que salió para evitar duplicidad de inventario.
        """
        self.ensure_one()
        
        # Validación de estado previo (idempotencia)
        if self.consumption_picking_id and self.consumption_picking_id.state != 'cancel':
            _logger.info("Orden %s ya tiene consumo activo (%s, estado %s)", self.name, self.consumption_picking_id.name, self.consumption_picking_id.state)
            return self.consumption_picking_id
            
        if not self.source_lot_ids:
            _logger.warning("Orden %s sin lotes de origen para consumir.", self.name)
            return None

        company = getattr(self, 'company_id', False) or self.env.company

        # 1. Determinar fuentes de consumo por lote y ubicación física real
        consumption_plan = []  # list of (lot, location, qty)

        for lot in self.source_lot_ids:
            req_qty = float_round(lot.volumen_m3, precision_digits=3)
            if float_compare(req_qty, 0.0, precision_rounding=0.001) <= 0:
                continue
            sources = self._get_lot_consumption_sources(lot, req_qty)
            for loc, qty in sources:
                consumption_plan.append((lot, loc, qty))

        if not consumption_plan:
            _logger.warning("No hay volumen positivo para consumir en orden %s.", self.name)
            return None

        _logger.info("🔄 Iniciando consumo automático para Orden Toll %s con %d asignaciones", self.name, len(consumption_plan))

        # 2. Configuración de Albarán y Ubicaciones
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not warehouse:
            raise UserError(_("No se encontró un almacén configurado para la compañía %s.") % company.display_name)

        prod_loc = self.env['stock.location'].search([
            ('usage', '=', 'production'),
            ('company_id', 'in', (False, company.id))
        ], limit=1)
        if not prod_loc:
            prod_loc = self.env.ref('stock.stock_location_production', raise_if_not_found=False)
        if not prod_loc:
            raise UserError(_("No se encontró una ubicación de producción virtual para el consumo."))
        location_dest_id = prod_loc.id

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', warehouse.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_("No se encontró un tipo de operación de salida válido para generar el consumo."))

        source_locs = {loc.id for _, loc, _ in consumption_plan}
        header_location_id = list(source_locs)[0] if len(source_locs) == 1 else warehouse.lot_stock_id.id

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': header_location_id,
            'location_dest_id': location_dest_id,
            'origin': f"Consumo Maquila: {self.name}",
            'partner_id': self.processor_id.id,
            'move_type': 'direct',
            'company_id': company.id,
        })

        # 3. Crear Movimientos y Líneas Detalladas por Lote y Ubicación Física
        for lot, loc, qty in consumption_plan:
            product_uom = lot.product_id.uom_id
            move = self.env['stock.move'].create({
                'name': f"Consumo {lot.name}",
                'product_id': lot.product_id.id,
                'product_uom_qty': qty,
                'product_uom': product_uom.id,
                'picking_id': picking.id,
                'location_id': loc.id,
                'location_dest_id': location_dest_id,
                'origin': picking.origin,
                'company_id': company.id,
                'picked': True,
            })

            self.env['stock.move.line'].create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': lot.product_id.id,
                'lot_id': lot.id,
                'quantity': qty,
                'picked': True,
                'product_uom_id': product_uom.id,
                'location_id': loc.id,
                'location_dest_id': location_dest_id,
                'company_id': company.id,
            })

        # 4. Confirmar y Validar automáticamente
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

        self.consumption_picking_id = picking.id

        self.message_post(body=_(
            "✅ Materia prima consumida automáticamente en albarán: %(picking)s (%(count)d asignaciones)",
            picking=picking.name,
            count=len(consumption_plan)
        ))
        _logger.info("✅ Consumo creado y validado: %s", picking.name)
        return picking

    # === LÓGICA FINANCIERA (Fase 5) ===
    def action_create_bill(self):
        """Genera la factura de proveedor por el servicio de maquila"""
        self.ensure_one()
        if not self.service_product_id:
            raise UserError(_("Configure el 'Producto Servicio' antes de facturar."))
        if self.actual_return_volume_m3 <= 0:
            raise UserError(_("No hay volumen procesado (retorno) para facturar."))

        # Datos de la factura
        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.processor_id.id,
            'invoice_date': fields.Date.today(),
            'currency_id': self.currency_id.id,
            'toll_order_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.service_product_id.id,
                'name': f"{self.service_product_id.name} - Orden {self.name}",
                'quantity': self.actual_return_volume_m3, # Cantidad = m3 procesados
                'price_unit': self.process_cost_per_m3,   # Precio = tarifa pactada
                'tax_ids': [(6, 0, self.service_product_id.supplier_taxes_id.ids)],
            })]
        }
        
        invoice = self.env['account.move'].create(bill_vals)
        self.write({'state': 'invoiced'})
        
        return {
            'name': _('Factura Proveedor'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def action_view_invoices(self):
        return {
            'name': _('Facturas'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_move_type': 'in_invoice'}
        }

# Extensión de Account Move para trazabilidad inversa
class AccountMove(models.Model):
    _inherit = 'account.move'
    toll_order_id = fields.Many2one('toll.processing.order', string='Orden de Maquila', readonly=True)