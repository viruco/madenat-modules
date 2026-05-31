# -*- coding: utf-8 -*-
"""
Modelo principal de consolidación de facturación.
Separa el proceso de facturación del flujo logístico operativo.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
# 1. Importar el modelo de utilidades
from odoo.addons.madenat_lumber_billing.models.common import MadenatBillingCommon

class LumberBillingConsolidation(models.Model):
    """
    Consolidación de datos para facturación de embarques.
    
    Flujo:
    1. Logística crea consolidación desde embarque completado
    2. Auditoría (Felipe) revisa costos y aprueba/rechaza
    3. Contabilidad (María Victoria) genera factura
    """
    _name = 'lumber.billing.consolidation'
    _description = 'Consolidación de Facturación'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CAMPOS BÁSICOS
    # ============================================================================
    
    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        help='Número único de consolidación generado automáticamente'
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        help='Compañía a la que pertenece esta consolidación'
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env['madenat.billing.common'].get_usd_currency(),
        tracking=True,
        help='Moneda en que se facturará (típicamente USD)'
    )

    # ============================================================================
    # RELACIÓN CON LOGÍSTICA
    # ============================================================================
    
    shipment_id = fields.Many2one(
        comodel_name='lumber.export.shipment',
        string='Embarque',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Embarque de exportación desde el cual se genera la factura'
    )
    
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        related='shipment_id.customer_id',
        store=True,
        readonly=True,
        help='Cliente que recibirá la factura'
    )
    
    shipment_date = fields.Datetime(
        string='Fecha Embarque',
        related='shipment_id.actual_departure',
        store=True,
        readonly=True
    )

    # ============================================================================
    # ESTADO Y WORKFLOW
    # ============================================================================
    
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('ready_audit', 'Listo para Auditar'),
            ('in_audit', 'En Auditoría'),
            ('audit_approved', 'Aprobado por Auditoría'),
            ('audit_rejected', 'Rechazado por Auditoría'),
            ('ready_billing', 'Listo para Facturar'),
            ('billed', 'Facturado'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
        help='Estado actual en el proceso de facturación'
    )

    # ============================================================================
    # DATOS CONSOLIDADOS
    # ============================================================================
    
    line_ids = fields.One2many(
        comodel_name='lumber.billing.consolidation.line',
        inverse_name='consolidation_id',
        string='Líneas de Facturación',
        help='Líneas detalladas con productos y costos'
    )
    
    total_volume_m3 = fields.Float(
        string='Volumen Total m³',
        compute='_compute_totals',
        store=True,
        digits='Product Unit of Measure',
        help='Suma de volúmenes de todas las líneas'
    )
    
    total_cost_usd = fields.Monetary(
        string='Costo Total USD',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Suma de costos de todas las líneas'
    )
    
    total_price_usd = fields.Monetary(
        string='Precio Total USD',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Suma de precios de venta de todas las líneas'
    )
    
    margin_usd = fields.Monetary(
        string='Margen USD',
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
        help='Diferencia entre precio y costo total'
    )
    
    margin_percent = fields.Float(
        string='% Margen',
        compute='_compute_margin',
        store=True,
        digits=(12, 2),
        help='Porcentaje de margen sobre el costo'
    )

    # ============================================================================
    # CONTROL DE COSTOS - AUDITORÍA FELIPE
    # ============================================================================
    
    # Costos Reales Consolidados
    real_wood_cost_usd = fields.Monetary(
        string='Costo Madera Real USD',
        compute='_compute_real_costs',
        store=True,
        currency_field='currency_id',
        help='Costo real de madera sumado de todas las líneas'
    )
    
    real_logistic_cost_usd = fields.Monetary(
        string='Costo Logística Real USD',
        compute='_compute_real_costs',
        store=True,
        currency_field='currency_id',
        help='Costo real de logística sumado de todas las líneas'
    )
    
    real_process_cost_usd = fields.Monetary(
        string='Costo Procesamiento Real USD',
        compute='_compute_real_costs',
        store=True,
        currency_field='currency_id',
        help='Costo real de procesamiento sumado de todas las líneas'
    )
    
    # Costos Estimados (desde presupuesto inicial)
    estimated_wood_cost_usd = fields.Monetary(
        string='Costo Madera Estimado USD',
        currency_field='currency_id',
        help='Costo estimado de madera al iniciar el embarque'
    )
    
    estimated_logistic_cost_usd = fields.Monetary(
        string='Costo Logística Estimado USD',
        currency_field='currency_id',
        help='Costo estimado de logística al iniciar el embarque'
    )
    
    estimated_process_cost_usd = fields.Monetary(
        string='Costo Procesamiento Estimado USD',
        currency_field='currency_id',
        help='Costo estimado de procesamiento al iniciar el embarque'
    )
    
    # Variaciones (Real vs. Estimado)
    variance_wood_cost_usd = fields.Monetary(
        string='Variación Madera USD',
        compute='_compute_cost_variances',
        store=True,
        currency_field='currency_id',
        help='Diferencia entre costo real y estimado de madera'
    )
    
    variance_wood_cost_percent = fields.Float(
        string='% Variación Madera',
        compute='_compute_cost_variances',
        store=True,
        digits=(12, 2),
        help='Porcentaje de variación en costo de madera'
    )
    
    variance_logistic_cost_usd = fields.Monetary(
        string='Variación Logística USD',
        compute='_compute_cost_variances',
        store=True,
        currency_field='currency_id',
        help='Diferencia entre costo real y estimado de logística'
    )
    
    variance_logistic_cost_percent = fields.Float(
        string='% Variación Logística',
        compute='_compute_cost_variances',
        store=True,
        digits=(12, 2),
        help='Porcentaje de variación en costo de logística'
    )
    
    variance_process_cost_usd = fields.Monetary(
        string='Variación Procesamiento USD',
        compute='_compute_cost_variances',
        store=True,
        currency_field='currency_id',
        help='Diferencia entre costo real y estimado de procesamiento'
    )
    
    variance_process_cost_percent = fields.Float(
        string='% Variación Procesamiento',
        compute='_compute_cost_variances',
        store=True,
        digits=(12, 2),
        help='Porcentaje de variación en costo de procesamiento'
    )
    
    # Variación Total
    variance_total_cost_usd = fields.Monetary(
        string='Variación Total USD',
        compute='_compute_cost_variances',
        store=True,
        currency_field='currency_id',
        help='Suma de todas las variaciones de costos'
    )
    
    variance_total_cost_percent = fields.Float(
        string='% Variación Total',
        compute='_compute_cost_variances',
        store=True,
        digits=(12, 2),
        help='Porcentaje de variación total'
    )
    
    # Alertas de Control de Costos
    cost_alert_level = fields.Selection(
        selection=[
            ('green', 'Normal (< 5%)'),
            ('yellow', 'Atención (5-10%)'),
            ('red', 'Crítico (> 10%)'),
        ],
        string='Nivel de Alerta',
        compute='_compute_cost_alert_level',
        store=True,
        help='Nivel de alerta basado en variaciones de costos'
    )
    
    requires_cost_justification = fields.Boolean(
        string='Requiere Justificación',
        compute='_compute_cost_alert_level',
        store=True,
        help='Si las variaciones son significativas, requiere justificación'
    )
    
    cost_justification = fields.Text(
        string='Justificación de Variaciones',
        tracking=True,
        help='Explicación del auditor sobre variaciones significativas en costos'
    )

    # ============================================================================
    # AUDITORÍA (FELIPE)
    # ============================================================================
    
    auditor_id = fields.Many2one(
        comodel_name='res.users',
        string='Auditor',
        tracking=True,
        help='Usuario que realizó la auditoría'
    )
    
    audit_date = fields.Datetime(
        string='Fecha Auditoría',
        readonly=True,
        tracking=True,
        help='Fecha y hora en que se completó la auditoría'
    )
    
    audit_notes = fields.Text(
        string='Observaciones Auditoría',
        tracking=True,
        help='Comentarios del auditor sobre la consolidación'
    )

    # ============================================================================
    # APROBACIÓN CONTABLE (MARÍA VICTORIA)
    # ============================================================================
    
    approver_id = fields.Many2one(
        comodel_name='res.users',
        string='Aprobador Contable',
        tracking=True,
        help='Usuario que aprobó para facturación'
    )
    
    approval_date = fields.Datetime(
        string='Fecha Aprobación',
        readonly=True,
        tracking=True,
        help='Fecha y hora de aprobación contable'
    )

    # ============================================================================
    # FACTURA GENERADA (INTEGRACIÓN NATIVA ODOO)
    # ============================================================================
    
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Factura',
        readonly=True,
        copy=False,
        tracking=True,
        help='Factura generada en Odoo Accounting'
    )
    
    invoice_state = fields.Selection(
        string='Estado Factura',
        related='invoice_id.state',
        store=True,
        readonly=True
    )

    # ============================================================================
    # COMPUTED FIELDS - TOTALES
    # ============================================================================
    
    @api.depends('line_ids.volume_m3', 'line_ids.cost_usd', 'line_ids.price_usd')
    @api.depends_context('company_id')
    def _compute_totals(self):
        """Calcula totales de volumen, costo y precio."""
        for record in self:
            record.total_volume_m3 = sum(record.line_ids.mapped('volume_m3'))
            record.total_cost_usd = sum(record.line_ids.mapped('cost_usd'))
            record.total_price_usd = sum(record.line_ids.mapped('price_usd'))
    
    @api.depends('total_cost_usd', 'total_price_usd')
    def _compute_margin(self):
        """Calcula margen en USD y porcentaje."""
        for record in self:
            record.margin_usd = record.total_price_usd - record.total_cost_usd
            record.margin_percent = (
                (record.margin_usd / record.total_cost_usd * 100)
                if record.total_cost_usd else 0.0
            )
    @api.constrains('state')
    def _check_state_transitions(self):
        """Validar transiciones de estado permitidas"""
        allowed_transitions = {
            'draft': ['ready_audit', 'cancelled'],
            'ready_audit': ['in_audit', 'cancelled'],
            # ... completar transiciones
        }
    # ============================================================================
    # COMPUTED FIELDS - CONTROL DE COSTOS
    # ============================================================================
    
    @api.depends('line_ids.wood_cost_usd', 'line_ids.logistic_cost_usd', 'line_ids.process_cost_usd')
    def _compute_real_costs(self):
        """Calcula costos reales consolidados desde las líneas."""
        for record in self:
            record.real_wood_cost_usd = sum(record.line_ids.mapped('wood_cost_usd'))
            record.real_logistic_cost_usd = sum(record.line_ids.mapped('logistic_cost_usd'))
            record.real_process_cost_usd = sum(record.line_ids.mapped('process_cost_usd'))
    
    @api.depends(
        'real_wood_cost_usd', 'estimated_wood_cost_usd',
        'real_logistic_cost_usd', 'estimated_logistic_cost_usd',
        'real_process_cost_usd', 'estimated_process_cost_usd'
    )
    def _compute_cost_variances(self):
        """Calcula variaciones entre costos reales y estimados."""
        for record in self:
            # Variación Madera
            record.variance_wood_cost_usd = (
                record.real_wood_cost_usd - record.estimated_wood_cost_usd
            )
            record.variance_wood_cost_percent = (
                (record.variance_wood_cost_usd / record.estimated_wood_cost_usd * 100)
                if record.estimated_wood_cost_usd else 0.0
            )
            
            # Variación Logística
            record.variance_logistic_cost_usd = (
                record.real_logistic_cost_usd - record.estimated_logistic_cost_usd
            )
            record.variance_logistic_cost_percent = (
                (record.variance_logistic_cost_usd / record.estimated_logistic_cost_usd * 100)
                if record.estimated_logistic_cost_usd else 0.0
            )
            
            # Variación Procesamiento
            record.variance_process_cost_usd = (
                record.real_process_cost_usd - record.estimated_process_cost_usd
            )
            record.variance_process_cost_percent = (
                (record.variance_process_cost_usd / record.estimated_process_cost_usd * 100)
                if record.estimated_process_cost_usd else 0.0
            )
            
            # Variación Total
            record.variance_total_cost_usd = (
                record.variance_wood_cost_usd +
                record.variance_logistic_cost_usd +
                record.variance_process_cost_usd
            )
            
            total_estimated = (
                record.estimated_wood_cost_usd +
                record.estimated_logistic_cost_usd +
                record.estimated_process_cost_usd
            )
            
            record.variance_total_cost_percent = (
                (record.variance_total_cost_usd / total_estimated * 100)
                if total_estimated else 0.0
            )
    
    @api.depends('variance_total_cost_percent')
    def _compute_cost_alert_level(self):
        """Calcula nivel de alerta basado en variación total."""
        for record in self:
            abs_variance = abs(record.variance_total_cost_percent)
            
            if abs_variance < 5.0:
                record.cost_alert_level = 'green'
                record.requires_cost_justification = False
            elif abs_variance < 10.0:
                record.cost_alert_level = 'yellow'
                record.requires_cost_justification = True
            else:
                record.cost_alert_level = 'red'
                record.requires_cost_justification = True

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    
    @api.model_create_multi
    def create(self, vals_list):
            """Genera número de secuencia al crear."""
            for vals in vals_list:
                if vals.get('name', _('Nuevo')) == _('Nuevo'):
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'lumber.billing.consolidation'
                    ) or _('Nuevo')
            return super().create(vals_list)
    def unlink(self):
        """Proteger borrado de consolidaciones auditadas o facturadas."""
        for rec in self:
            if rec.state in ('audit_approved', 'billed'):
                raise UserError(_("No se puede eliminar consolidaciones en estado %s") % rec.state)
        return super().unlink()

    # ============================================================================
    # WORKFLOW METHODS
    # ============================================================================
    
    def action_send_to_audit(self):
        """Envía consolidación a auditoría."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No se pueden enviar consolidaciones sin líneas."))
        self.write({'state': 'ready_audit'})
        self.message_post(body=_("Consolidación enviada a auditoría."))
        return True
    
    def action_start_audit(self):
        """Auditor toma la consolidación para revisar."""
        self.ensure_one()
        self.write({
            'state': 'in_audit',
            'auditor_id': self.env.user.id,
        })
        self.message_post(body=_("Auditoría iniciada por %s") % self.env.user.name)
        return True
    
    def action_approve_audit(self):
        """Auditor aprueba la consolidación tras verificar costos."""
        self.ensure_one()
        
        # Validar justificación si hay variaciones significativas
        if self.requires_cost_justification and not self.cost_justification:
            raise UserError(_(
                "Las variaciones de costos son significativas (%.2f%%).\n"
                "Debe ingresar una justificación antes de aprobar."
            ) % self.variance_total_cost_percent)
        
        self.write({
            'state': 'audit_approved',
            'audit_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Consolidación aprobada por auditoría."))
        return True
    
    def action_reject_audit(self):
        """Auditor rechaza la consolidación."""
        self.ensure_one()
        self.write({
            'state': 'audit_rejected',
            'audit_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Consolidación rechazada. Revisar observaciones."))
        return True
    
    def action_send_to_billing(self):
        """Envía consolidación aprobada a contabilidad."""
        self.ensure_one()
        if self.state != 'audit_approved':
            raise UserError(_("Solo se pueden facturar consolidaciones aprobadas."))
        self.write({'state': 'ready_billing'})
        self.message_post(body=_("Consolidación lista para facturar."))
        return True
    
    def action_open_invoice_wizard(self):
        """Abre wizard para generar factura."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar Factura'),
            'res_model': 'lumber.billing.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consolidation_id': self.id,
            },
        }
    
    def action_view_invoice(self):
        """Abre la factura generada."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No hay factura generada para esta consolidación."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
