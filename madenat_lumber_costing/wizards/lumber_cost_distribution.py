# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LumberCostDistributionWizard(models.TransientModel):
    _name = 'lumber.cost.distribution.wizard'
    _description = 'Distribución Avanzada de Costos (Landed Cost)'

    def _default_lots(self):
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        if active_model == 'stock.lot':
            return self.env['stock.lot'].browse(active_ids)
        return False

    # ====================================================================
    # 1. SELECCIÓN DE CRITERIO
    # ====================================================================
    target_model = fields.Selection([
        ('manual', '👉 Selección Manual de Lotes'),
        ('reception', '📄 Por Guía de Recepción'),
        ('purchase', '🛒 Por Orden de Compra'),
        ('container', '📦 Por Contenedor'),
        ('booking', '🚢 Por Reserva (Booking/BL)'),
    ], string="Aplicar Costo A", default='manual', required=True)

    reception_id = fields.Many2one('madenat.guia.processing', string="Guía de Origen")
    purchase_id = fields.Many2one('purchase.order', string="Orden de Compra")
    container_id = fields.Many2one('lumber.container', string="Contenedor")
    booking_id = fields.Many2one('shipping.booking', string="Reserva/Booking")

    lot_ids = fields.Many2many('stock.lot', string="Lotes Afectados", default=_default_lots)
    lot_count = fields.Integer(string="N° Lotes", compute="_compute_lot_count")
    
    # Validación de Facturación
    billed_lot_count = fields.Integer(string="Lotes Facturados", compute="_compute_billed_lots")
    has_billed_lots = fields.Boolean(string="Tiene Lotes Facturados", compute="_compute_billed_lots")
    warning_message = fields.Char(string="Mensaje de Advertencia", compute="_compute_billed_lots")
    total_volume_preview = fields.Float(string="Volumen Total m³", compute="_compute_previews")
    cost_per_unit_preview = fields.Float(string="Costo Proyectado USD/m³", compute="_compute_previews", digits=(12,4))
    # ====================================================================
    # 2. DATOS FINANCIEROS
    # ====================================================================
    cost_type = fields.Selection([
        ('freight', '🚚 Flete Nacional'),
        ('ocean_freight', '🌊 Flete Marítimo'),
        ('port', '⚓ Gastos Portuarios / THC'),
        ('customs', '🛃 Agenciamiento Aduana'),
        ('insurance', '🛡️ Seguros'),
        ('commission', '🤝 Comisiones'),
        ('other', '📎 Otros Gastos')
    ], string="Concepto", required=True)
    
    ref = fields.Char(string="N° Factura/Ref", required=True)
    partner_id = fields.Many2one('res.partner', string="Proveedor del Servicio")
    
    amount_total = fields.Float(string="Monto Total Factura", required=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True, 
                                 default=lambda self: self.env.company.currency_id)
    
    exchange_rate = fields.Float(string="Tasa Cambio (a USD)", default=1.0, digits=(12,4))
    
    distribution_method = fields.Selection([
        ('volume', 'Por Volumen (m³) - Estándar'),
        ('pieces', 'Por Cantidad de Piezas'),
        ('equal', 'Equitativo (Flat)')
    ], default='volume', string="Método Reparto", required=True)


    @api.depends('lot_ids', 'amount_total', 'exchange_rate', 'distribution_method')
    def _compute_previews(self):
        for r in self:
            # 🛡️ FILTRO DE INTEGRIDAD: Solo consideramos lotes que NO estén facturados
            active_lots = r.lot_ids.filtered(lambda l: not l.is_billed)
            
            # Sumamos volumen solo de los lotes activos para el costo
            vol = sum(active_lots.mapped(lambda l: l.vol_shipment_m3 or l.volumen_m3 or 0.0))
            r.total_volume_preview = vol
            
            # Cálculo de monto en USD
            amt_usd = r.amount_total
            if r.currency_id.name != 'USD' and r.exchange_rate > 0:
                amt_usd = r.amount_total / r.exchange_rate
            
            # La previsualización ahora es 100% HONESTA con lo que pasará al ejecutar
            if vol > 0 and r.distribution_method == 'volume':
                r.cost_per_unit_preview = amt_usd / vol
            else:
                r.cost_per_unit_preview = 0.0

    # MEJORA: Detectar desde dónde se abre el wizard
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        
        if active_model == 'lumber.export.shipment' and active_id:
            shipment = self.env[active_model].browse(active_id)
            res.update({
                'target_model': 'booking', # O el que prefieras por defecto
                'booking_id': shipment.booking_id.id if hasattr(shipment, 'booking_id') else False,
                'lot_ids': [(6, 0, shipment.container_ids.mapped('lot_ids').ids)]
            })
        return res
    # ====================================================================
    # MÉTODOS COMPUTADOS
    # ====================================================================
    @api.depends('lot_ids')
    def _compute_lot_count(self):
        for r in self: 
            r.lot_count = len(r.lot_ids)
    
    @api.depends('lot_ids')
    def _compute_billed_lots(self):
        for wizard in self:
            billed_lots = wizard.lot_ids.filtered(lambda lot: lot.is_billed)
            wizard.billed_lot_count = len(billed_lots)
            wizard.has_billed_lots = bool(billed_lots)
            
            if wizard.has_billed_lots:
                wizard.warning_message = (
                    f"⚠️ ADVERTENCIA: {len(billed_lots)} de {len(wizard.lot_ids)} lotes "
                    f"ya fueron facturados y serán EXCLUIDOS de la distribución."
                )
            else:
                wizard.warning_message = False

    @api.onchange('currency_id')
    def _onchange_currency(self):
        if self.currency_id.name == 'USD':
            self.exchange_rate = 1.0

    @api.onchange('target_model', 'reception_id', 'purchase_id', 'container_id', 'booking_id')
    def _onchange_target(self):
        lots = self.env['stock.lot']
        if self.target_model == 'reception' and self.reception_id:
            lots = self.env['stock.lot'].search([('guia_processing_id', '=', self.reception_id.id)])
        elif self.target_model == 'purchase' and self.purchase_id:
            lots = self.env['stock.lot'].search([('purchase_order_id', '=', self.purchase_id.id)])
        elif self.target_model == 'container' and self.container_id:
            lots = self.container_id.lot_ids
        elif self.target_model == 'booking' and self.booking_id:
            containers = self.env['lumber.container'].search([('booking_id', '=', self.booking_id.id)])
            lots = containers.mapped('lot_ids')

        if self.target_model != 'manual':
            self.lot_ids = [(6, 0, lots.ids)]

    # ====================================================================
    # EJECUCIÓN OPTIMIZADA (BATCH CREATE)
    # ====================================================================
    def action_distribute(self):
        self.ensure_one()
        
        # 1. Validaciones Básicas
        if not self.lot_ids:
            raise UserError("No hay lotes asociados al criterio seleccionado.")
        if self.amount_total <= 0:
            raise UserError("El monto debe ser mayor a cero.")
        
        # 2. Filtrado de Lotes (Excluir facturados)
        distributable_lots = self.lot_ids.filtered(lambda lot: not lot.is_billed)
        billed_lots = self.lot_ids - distributable_lots
        
        if billed_lots:
            _logger.warning(f"[COST DIST] Excluidos {len(billed_lots)} lotes facturados.")
            if not distributable_lots:
                raise UserError(_("Todos los lotes seleccionados ya fueron facturados."))

        working_lots = distributable_lots

        # 3. Validación de Consolidaciones Facturadas
        consolidation_issues = []
        for lot in working_lots:
            if lot.consolidation_id and lot.consolidation_id.state == 'billed':
                consolidation_issues.append(f"• {lot.name} (Consolidación Facturada)")
        
        if consolidation_issues:
            raise UserError(_("Lotes en consolidaciones facturadas:\n%s") % '\n'.join(consolidation_issues))

        # 4. Normalización de Moneda
        total_usd = self.amount_total
        if self.currency_id.name != 'USD':
            if self.exchange_rate <= 0: 
                raise UserError("Tasa de cambio inválida.")
            total_usd = self.amount_total / self.exchange_rate

        # 5. Cálculo de Base Total
        total_base = 0.0
        for lot in working_lots:
            if self.distribution_method == 'volume':
                total_base += (lot.volumen_m3 or lot.volume_purchase_m3 or 0.0)
            elif self.distribution_method == 'pieces':
                total_base += lot.piezas
            else:
                total_base += 1

        if total_base == 0: 
            raise UserError("Base de distribución cero (revise volúmenes).")

        # 6. PREPARACIÓN DE DATOS (BATCH) - REGLA DE ORO APLICADA AQUÍ
        CostLine = self.env['stock.lot.cost.line']
        vals_list = []
        cost_name = f"{dict(self._fields['cost_type'].selection).get(self.cost_type)} | {self.ref}"
        
        for lot in working_lots:
            # Cálculo de factor individual
            lot_base = 0.0
            if self.distribution_method == 'volume':
                lot_base = (lot.volumen_m3 or lot.volume_purchase_m3 or 0.0)
            elif self.distribution_method == 'pieces':
                lot_base = lot.piezas
            else:
                lot_base = 1
            
            factor = lot_base / total_base
            amount = total_usd * factor

            # Agregar a la lista de valores (NO CREAR AÚN)
            vals_list.append({
                'lot_id': lot.id,
                'name': cost_name,
                'cost_type': self.cost_type,
                'amount_usd': amount,
                'partner_id': self.partner_id.id,
                'date': fields.Date.context_today(self),
                'notes': f"Origen: {self.target_model} | Ref: {self.ref}"
            })

        # 7. EJECUCIÓN MASIVA (1 sola consulta SQL)
        if vals_list:
            CostLine.create(vals_list)
            
            # 8. RECÁLCULO MASIVO (Optimizado)
            # Odoo 18 maneja esto mejor si se llama sobre el recordset completo
            working_lots._compute_total_cost_usd()

        # 9. Notificación Final
        success_message = f'USD {total_usd:,.2f} distribuidos en {len(working_lots)} lotes.'
        if billed_lots:
            success_message += f'\n⚠️ Se excluyeron {len(billed_lots)} lotes facturados.'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Costos Asignados',
                'message': success_message,
                'type': 'success' if not billed_lots else 'warning',
                'sticky': bool(billed_lots),
            }
        }
