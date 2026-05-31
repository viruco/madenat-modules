# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# ==============================================================================
# 1. MODELO HISTÓRICO DE COSTOS (La "Libreta" del Lote)
# Este modelo recibe los prorrateos desde el Wizard y desde Logística
# ==============================================================================
class StockLotCostLine(models.Model):
    _inherit = 'stock.lot.cost.line'

    # Único campo nuevo aportado por este módulo
    distribution_id = fields.Many2one(
        'lumber.cost.distribution',
        string='Expediente de Reparto',
        ondelete='cascade',
        index=True
    )


# ==============================================================================
# 2. EXTENSIÓN DEL LOTE (STOCK.LOT) - Unificado
# ==============================================================================
class StockLot(models.Model):
    _inherit = 'stock.lot'

    # === ENLACES LOGÍSTICOS MAESTROS (Auditoría de Origen) ===
    shipment_id = fields.Many2one(
        related='container_id.shipment_id',
        string='Embarque / Nave',
        store=True, 
        readonly=True,
        index=True
    )
    
    booking_ref = fields.Char(
        related='container_id.shipment_id.booking_reference',
        string='Booking (Ref)',
        store=True,
        readonly=True
    )

    # === HISTORIAL DE COSTOS DEL LOTE ===
    cost_line_ids = fields.One2many(
        'stock.lot.cost.line', 
        'lot_id', 
        string='Desglose de Costos Histórico'
    )

    # === CAMPOS EXTENDIDOS DE COSTEO ===
    logistic_cost_usd = fields.Float(
        'Costo Logístico (USD)',
        compute='_compute_cost_breakdown', 
        store=True, 
        digits=(16, 2),
        help="Suma de Fletes, Puerto, Aduana y Seguros prorrateados a este lote"
    )
    
    process_cost_usd = fields.Float(
        'Costo Proceso (USD)',
        compute='_compute_cost_breakdown', 
        store=True, 
        digits=(16, 2),
        help="Suma de costos de procesamiento y manufactura"
    )
    
    other_cost_usd = fields.Float(
        'Otros Costos (USD)',
        compute='_compute_cost_breakdown', 
        store=True, 
        digits=(16, 2),
        help="Suma de comisiones y otros costos adicionales"
    )

    # === TOTALES Y FINANZAS ===
    total_cost_clp = fields.Float(
        'Costo Total (CLP)',
        compute='_compute_total_costs_clp',
        store=True,
        digits=(16, 0)
    )
    
    exchange_rate = fields.Float(
        'Tipo de Cambio',
        digits=(16, 2),
        default=lambda self: self._get_default_exchange_rate(),
        help="Tipo de cambio referencial USD/CLP"
    )
    
    costing_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('partial', 'Parcial'),
        ('complete', 'Completo'),
    ], string='Estado Costeo', default='pending', compute='_compute_costing_state', store=True)


    # ==========================================================================
    # LÓGICA DE CÁLCULO Y COMPUTES
    # ==========================================================================

    @api.depends('cost_line_ids.amount_usd', 'cost_line_ids.cost_type')
    def _compute_cost_breakdown(self):
        """
        Suma y clasifica las líneas de costo inyectadas en el lote.
        Protege la integridad matemática (lo que ves es lo que hay en el historial).
        """
        for lot in self:
            logistic = 0.0
            process = 0.0
            other = 0.0
            
            for line in lot.cost_line_ids:
                if line.cost_type in ['freight', 'ocean_freight', 'port', 'customs', 'insurance']:
                    logistic += line.amount_usd
                elif line.cost_type in ['process', 'manufacture']: # Reservado para procesos
                    process += line.amount_usd
                else:
                    other += line.amount_usd
            
            lot.logistic_cost_usd = logistic
            lot.process_cost_usd = process
            lot.other_cost_usd = other

    @api.depends("logistic_cost_usd", "process_cost_usd", "other_cost_usd", "wood_cost_usd")
    def _compute_total_cost_usd(self):
        """
        Override: Sumar costos específicos de este módulo al total del Core.
        """
        # 1. Ejecuta el cálculo base (que probablemente suma wood_cost_usd)
        super()._compute_total_cost_usd() 
        
        # 2. Suma los costos logísticos calculados por este módulo
        for lot in self:
            added_value = lot.logistic_cost_usd + lot.process_cost_usd + lot.other_cost_usd
            if hasattr(lot, 'total_cost_usd'):
                lot.total_cost_usd += added_value

    @api.depends('total_cost_usd', 'exchange_rate')
    def _compute_total_costs_clp(self):
        """Convertir costo total a CLP de forma segura"""
        for lot in self:
            total_usd = getattr(lot, 'total_cost_usd', 0.0)
            lot.total_cost_clp = total_usd * lot.exchange_rate

    @api.depends('wood_cost_usd', 'cost_line_ids')
    def _compute_costing_state(self):
        """
        Determinar estado del costeo evaluando la base y el historial.
        """
        for lot in self:
            has_wood = (getattr(lot, 'wood_cost_usd', 0.0) > 0)
            has_logistics = len(lot.cost_line_ids) > 0
            
            if has_wood and has_logistics:
                lot.costing_state = 'complete'
            elif has_wood or has_logistics:
                lot.costing_state = 'partial'
            else:
                lot.costing_state = 'pending'

    def _get_default_exchange_rate(self):
        """Obtener tipo de cambio actual USD/CLP de forma segura"""
        try:
            usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            clp = self.env['res.currency'].search([('name', '=', 'CLP')], limit=1)
            if usd and clp and usd.rate:
                return clp.rate / usd.rate
            return 950.0
        except Exception:
            return 950.0

    # ==========================================================================
    # MÉTODOS DE ACCIÓN ORIGINALES (Mantenidos intactos)
    # ==========================================================================
    def action_calculate_wood_cost(self):
        """
        Calcular costo de madera desde la recepción.
        Actualiza el campo base del Core.
        """
        self.ensure_one()
        if not self.reception_id:
            raise ValidationError(_('El lote no tiene una recepción asociada'))
        
        reception = self.reception_id
        if not reception.total_amount_usd or not reception.physical_volume_m3:
            raise ValidationError(_('La recepción no tiene valores válidos'))
        
        if reception.physical_volume_m3 > 0:
            cost_per_m3 = reception.total_amount_usd / reception.physical_volume_m3
            # Escribimos en el campo del CORE
            self.wood_cost_usd = self.volumen_m3 * cost_per_m3
        
        return True