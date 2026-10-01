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
        # AD-73: reclasificación de tipo de ingreso previa a Gate 3 (Intake).
        ('reclassification', 'Reclasificación de Tipo de Ingreso'),
        # Ingreso por Volúmenes: edición controlada del volumen operativo y
        # confirmación manual de conciliación documental (Intake).
        ('volume_operational_update', 'Actualización Volumen Operativo'),
        ('conciliation_manual_confirm', 'Confirmación Manual de Conciliación'),
        # Programa SV: operación del ledger de etiquetas SV (rename,
        # regularización de volumen, rebaja y reversa de rebaja).
        ('sv_operation', 'Operación de Etiqueta SV'),
        # Fase 2 (AD-80): ciclo de vida controlado de guías desde la Consola
        # de Ingreso de Madera. El bloqueo se registra SIEMPRE (incluso sin
        # borrado); la eliminación definitiva y la purga controlada dejan su
        # evento firmado y sobreviven al borrado de la guía
        # (`guia_processing_id` es `ondelete='set null'`).
        ('guia_delete_blocked', 'Eliminación de Guía Bloqueada'),
        ('guia_delete_permanent', 'Eliminación Definitiva de Guía'),
        ('guia_purged', 'Purga Controlada de Guía'),
        # AD-82 / CANON/18: rebaja de inventario de contenedor/embarque y su
        # reversa (salida nativa única y su retorno).
        ('rebaja', 'Rebaja de Contenedor'),
        ('rebaja_reverse', 'Reversa de Rebaja de Contenedor'),
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