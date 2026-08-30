# -*- coding: utf-8 -*-
from odoo import models, fields, api  # ✅ AGREGAR: api

class MadenatAuditLog(models.Model):
    _name = 'madenat.audit.log'
    _description = 'Logs de Auditoría MADENAT'
    _order = 'timestamp desc'

    reception_id = fields.Many2one('lumber.reception', string='Recepción', ondelete='cascade')
    # ══════════════════════════════════════════════════════════════════════════
    # BT-01 (2026-08-16): vínculo canónico al flujo de guías procesadas.
    # ondelete='set null' conserva la evidencia firmada si la guía se elimina;
    # NO replica 'cascade' para no destruir la bitácora inmutable.
    # ══════════════════════════════════════════════════════════════════════════
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía de Procesamiento',
        ondelete='set null',
        index=True,
        help='Evento de auditoría originado en una guía procesada.'
    )
    action_type = fields.Selection([
        ('creation', 'Creación Producto'),
        ('omission', 'Omisión Producto'),
        ('lot_creation', 'Creación Lote'),
        ('lot_update', 'Actualización Lote'),
        # BT-04: salida controlada del material crudo hacia proceso (solo service).
        ('consumption', 'Salida a Proceso'),
        # BT-01: firma criptográfica de un ciclo de validación de guía procesada.
        ('validation_signature', 'Firma de Validación'),
    ], string='Tipo de Acción', required=True)
    # ══════════════════════════════════════════════════════════════════════════
    # BT-01: evidencia firmada. La bitácora es la fuente de verdad inmutable.
    # Recepción no los escribe (NULL por defecto); guías procesadas sí.
    # ══════════════════════════════════════════════════════════════════════════
    audit_snapshot = fields.Text(string='Snapshot JSON', readonly=True)
    audit_hash = fields.Char(string='Firma SHA-256', readonly=True)
    description = fields.Text(string='Descripción', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    batch_id = fields.Char(string='ID de Lote')
    month = fields.Char(string='Mes (YYYY-MM)', compute='_compute_month', store=True)

    @api.depends('timestamp')
    def _compute_month(self):
        for log in self:
            log.month = log.timestamp.strftime('%Y-%m') if log.timestamp else False