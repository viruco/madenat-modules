# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class LumberExportShipment(models.Model):
    _inherit = 'lumber.export.shipment'

    # -------------------------------------------------------------------------
    # REGLA DE ORO - Costeo de Embarque
    #  - Los totales de costo del embarque se calculan SOLO aquí.
    #  - La distribución a lotes se hace desde este método único.
    # -------------------------------------------------------------------------

    # MONEDA (Necesaria para campos Monetary)
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # Relación con líneas de costo (ya existe en logística; se redeclara compatible)
    cost_line_ids = fields.One2many(
        comodel_name='lumber.shipment.cost.line',
        inverse_name='shipment_id',
        string='Líneas de Costo',
    )

    # CAMBIO CRÍTICO: De Float a Monetary para corregir OwlError
    total_shipment_costs_usd = fields.Monetary(
        string='Costos Totales Embarque (USD)',
        compute='_compute_cost_totals',
        store=False,
        readonly=True,
        currency_field='currency_id', # <--- CLAVE
        help='Suma de todas las líneas de costo del embarque en USD.',
    )

    # CAMBIO CRÍTICO: De Float a Monetary para corregir OwlError
    total_cost_per_m3 = fields.Monetary(
        string='Costo por m³ (USD)',
        compute='_compute_cost_totals',
        store=False,
        readonly=True,
        currency_field='currency_id', # <--- CLAVE
        help='Costo logístico promedio por m³ del embarque.',
    )

    cost_distribution_state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('distributed', 'Distribuido'),
        ],
        string='Estado Distribución',
        default='pending',
        help='Indica si los costos del embarque ya fueron distribuidos a los lotes.',
    )

    @api.depends('cost_line_ids.amount_usd', 'total_volume_m3')
    def _compute_cost_totals(self):
        """Calcular totales de costos del embarque.

        Regla de Oro:
        - El total se obtiene SIEMPRE desde las líneas de costo.
        - El costo por m³ usa el volumen total del embarque.
        """
        for shipment in self:
            total_cost = sum(shipment.cost_line_ids.mapped('amount_usd')) or 0.0
            shipment.total_shipment_costs_usd = total_cost

            if shipment.total_volume_m3 > 0:
                shipment.total_cost_per_m3 = total_cost / shipment.total_volume_m3
            else:
                shipment.total_cost_per_m3 = 0.0

            _logger.debug(
                "Cost Totals computed for shipment %s: total_cost=%.2f, "
                "volume=%.3f, cost_per_m3=%.4f",
                shipment.name,
                shipment.total_shipment_costs_usd,
                shipment.total_volume_m3,
                shipment.total_cost_per_m3,
            )

    def _deprecated_action_distribute_costs(self): # REEMPLAZADO POR lumber_export_shipment.py
        """Distribuir costos del embarque a los lotes proporcionalmente.

        REGLA DE ORO aplicada:
        - Punto Único de distribución de costos logísticos de embarque.
        - Usa volumen 'dual' por lote:
          * vol_shipment_m3 (volumen neto de embarque) si existe,
          * si no, volumen_m3 (volumen físico estándar del lote).
        - Solo distribuye a lotes con volumen > 0.
        """
        self.ensure_one()

        # 1) Validaciones básicas
        if not self.cost_line_ids:
            raise UserError(_('No hay costos registrados para distribuir.'))

        # Costo total desde compute (Regla de Oro)
        total_cost_usd = self.total_shipment_costs_usd or 0.0
        if total_cost_usd <= 0:
            raise UserError(_('El costo total del embarque es cero. Verifique las líneas de costo.'))

        # Obtener lotes desde contenedores del embarque
        all_lots = self.container_ids.mapped('lot_ids')
        if not all_lots:
            raise UserError(_('No hay lotes asignados al embarque.'))

        # 2) Base de volumen para distribución (volumen dual)
        total_volume_for_distribution = 0.0
        for lot in all_lots:
            # Preferir volumen específico de embarque si existe
            volume_for_cost = getattr(lot, 'vol_shipment_m3', 0.0) or getattr(lot, 'volumen_m3', 0.0)
            if volume_for_cost > 0:
                total_volume_for_distribution += volume_for_cost

        if total_volume_for_distribution <= 0:
            raise UserError(_('El volumen total es cero. Verifique los lotes del embarque.'))

        cost_per_m3 = total_cost_usd / total_volume_for_distribution

        _logger.info(
            "Distribuyendo costos logísticos para embarque %s: "
            "total_cost_usd=%.2f, total_volume=%.3f, cost_per_m3=%.4f, lots=%d",
            self.name,
            total_cost_usd,
            total_volume_for_distribution,
            cost_per_m3,
            len(all_lots),
        )

        # 3) Distribuir a cada lote
        lots_updated = 0
        for lot in all_lots:
            volume_for_cost = getattr(lot, 'vol_shipment_m3', 0.0) or getattr(lot, 'volumen_m3', 0.0)
            if volume_for_cost <= 0:
                continue

            proportional_cost = cost_per_m3 * volume_for_cost
            current_logistic_cost = getattr(lot, 'logistic_cost_usd', 0.0) or 0.0
            new_logistic_cost = current_logistic_cost + proportional_cost

            lot.write({'logistic_cost_usd': new_logistic_cost})
            lots_updated += 1

        # 4) Marcar embarque como distribuido
        self.write({'cost_distribution_state': 'distributed'})

        # 5) Log detallado en chatter
        body = _(
            '<p><strong>Costos Distribuidos</strong></p>'
            '<ul>'
            '<li>Costo Logístico Total USD: %.2f</li>'
            '<li>Volumen Total para Distribución: %.3f m³</li>'
            '<li>Costo por m³: USD %.4f</li>'
            '<li>Lotes actualizados: %d</li>'
            '</ul>'
        ) % (total_cost_usd, total_volume_for_distribution, cost_per_m3, lots_updated)

        self.message_post(body=body)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Distribución Completada'),
                'message': _(
                    'Se distribuyeron USD %.2f entre %d lotes.'
                ) % (total_cost_usd, lots_updated),
                'type': 'success',
                'sticky': False,
            },
        }


class LumberShipmentCostLine(models.Model):
    _inherit = 'lumber.shipment.cost.line'

    # -------------------------------------------------------------------------
    # REGLA DE ORO - Parámetros por línea de costo
    #  - Este campo permite definir la intención de distribución
    #    (actualmente la acción global usa volumen; está listo para futuras
    #    estrategias más avanzadas).
    # -------------------------------------------------------------------------

    shipment_id = fields.Many2one(
        comodel_name='lumber.export.shipment',
        string='Embarque',
        required=True,
        ondelete='cascade',
        index=True,  # FIX #8 - Índice para mejorar joins por embarque
    )

    distribution_method = fields.Selection(
        [
            ('volume', 'Por Volumen (m³)'),
            ('weight', 'Por Peso (Kg)'),
            ('packages', 'Por Paquetes'),
            ('equal', 'Igual para Todos'),
        ],
        string='Método de Distribución',
        default='volume',
        help=(
            'Define el criterio deseado para distribuir este costo. '
            'Actualmente la distribución global usa volumen en m³; '
            'este campo queda preparado para reglas más avanzadas.'
        ),
    )

    # ════════════════════════════════════════════════════════════════════════
    # ESTADO DE DISTRIBUCIÓN (Arquitectura Clase Mundial)
    # ════════════════════════════════════════════════════════════════════════
    # IMPLEMENTADO: 2025-12-13 (Migración a estándar SAP/Oracle/NetSuite)
    # PROPÓSITO: Rastrear si un costo de embarque ya fue distribuido a lotes
    # ════════════════════════════════════════════════════════════════════════
    
    is_distributed = fields.Boolean(
        string='Distribuido a Lotes',
        compute='_compute_is_distributed',
        store=False,
        help=(
            'Indica si este costo ya fue distribuido a los lotes del embarque.\n\n'
            'ESTADOS:\n'
            '- True: El costo fue distribuido. Existen stock.lot.cost.line\n'
            '  que referencian este costo (source_shipment_cost_line_id).\n'
            '- False: El costo está pendiente de distribución.\n\n'
            'USOS:\n'
            '- Prevenir redistribución accidental\n'
            '- Filtrar costos pendientes vs distribuidos\n'
            '- Auditoría de proceso de distribución\n\n'
            'ESTÁNDAR: SAP S/4HANA Cost Posting Status'
        ),
    )
    
    
    def _compute_is_distributed(self):
        """
        Verificar si este costo ya fue distribuido a lotes
        
        LÓGICA:
        - Busca stock.lot.cost.line con source_shipment_cost_line_id = self.id
        - Si encuentra al menos uno: is_distributed = True
        - Si no encuentra ninguno: is_distributed = False
        
        PERFORMANCE:
        - Usa search_count (más eficiente que search + len)
        - Campo store=False para evitar recálculos constantes
        
        ESTÁNDAR: SAP S/4HANA Cost Allocation Status Check
        """
        LotCostLine = self.env['stock.lot.cost.line']
        for line in self:
            distributed_count = LotCostLine.search_count([
                ('source_shipment_cost_line_id', '=', line.id)
            ])
            line.is_distributed = distributed_count > 0
