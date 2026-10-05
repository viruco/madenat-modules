# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LumberDocumentChecklist(models.Model):
    _name = 'lumber.document.checklist'
    _description = 'Checklist Documental de Exportación'
    _order = 'sequence, id'

    name = fields.Char('Nombre Documento', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    is_required = fields.Boolean('Obligatorio', default=True)
    description = fields.Text('Instrucciones')
    active = fields.Boolean('Activo', default=True)


class LumberShipmentDocument(models.Model):
    _name = 'lumber.shipment.document'
    _description = 'Documento de Embarque'

    shipment_id = fields.Many2one('lumber.export.shipment', string='Embarque', ondelete='cascade')
    checklist_id = fields.Many2one('lumber.document.checklist', string='Tipo Documento')
    
    # Campo nombre autocompletado si está vacío, pero editable
    name = fields.Char('Referencia/Nombre', compute='_compute_name', store=True, readonly=False, required=True)
    
    file_data = fields.Binary('Archivo')
    file_name = fields.Char('Nombre Archivo')
    
    state = fields.Selection([
        ('missing', 'Pendiente'),
        ('attached', 'Adjunto'),
        ('verified', 'Verificado')
    ], string='Estado', default='missing', index=True, compute='_compute_state', store=True, readonly=False)
    
    notes = fields.Text('Notas Adicionales')

    # AD-92 (2026-10-05): pendiente documental NO bloqueante del Rolleo.
    criticality = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Criticidad', default='medium', index=True)
    backlog_state = fields.Selection([
        ('open', 'Abierto'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('waived', 'Exonerado'),
    ], string='Estado Backlog', default='open', index=True)
    backlog_note = fields.Text('Nota de Backlog')

    @api.depends('checklist_id')
    def _compute_name(self):
        for doc in self:
            if not doc.name and doc.checklist_id:
                doc.name = doc.checklist_id.name
            elif not doc.name:
                doc.name = 'Documento Nuevo'

    @api.depends('file_data')
    def _compute_state(self):
        for doc in self:
            # Lógica robusta: Si suben archivo -> Adjunto. Si lo borran -> Pendiente.
            # Respeta el estado 'verified' si ya fue verificado manualmente.
            if doc.file_data:
                if doc.state != 'verified':
                    doc.state = 'attached'
            else:
                doc.state = 'missing'

    @api.onchange('file_data')
    def _onchange_file_data(self):
        # Mejora UX: Feedback inmediato en interfaz antes de guardar
        if self.file_data:
            self.state = 'attached'


class LumberExportShipment(models.Model):
    _inherit = 'lumber.export.shipment'

    document_ids = fields.One2many('lumber.shipment.document', 'shipment_id', string='Documentos')

    @api.depends('document_ids.state',
                 'document_ids.checklist_id.is_required',
                 'document_ids.checklist_id.active')
    def _compute_document_status(self):
        """Fuente ÚNICA de la semántica documental (B2).

        Sólo se consideran documentos cuyo checklist esté ACTIVO. El universo
        (`target`) son los documentos requeridos activos; si no existe ninguno
        requerido, todos los documentos activos.

        Valores deterministas de `document_status`:
          not_configured · missing · pending · partial · attached · verified
        Indicador INFORMATIVO: nunca es gate de operación física. No usa los
        valores legacy `complete`/`incomplete`.
        """
        for shipment in self:
            active_docs = shipment.document_ids.filtered(
                lambda d: d.checklist_id.active)
            required = active_docs.filtered(
                lambda d: d.checklist_id.is_required)
            target = required if required else active_docs
            total = len(target)
            verified = len(target.filtered(lambda d: d.state == 'verified'))
            attached = len(target.filtered(lambda d: d.state == 'attached'))
            missing = len(target.filtered(lambda d: d.state == 'missing'))

            shipment.document_verified_count = verified
            shipment.document_missing_count = missing
            shipment.document_pending_count = total - verified
            shipment.document_completion = (
                ((verified + attached) / total) * 100.0) if total else 0.0

            if total == 0:
                shipment.document_status = 'not_configured'
            elif verified == total:
                shipment.document_status = 'verified'
            elif verified > 0:
                shipment.document_status = 'partial'
            elif attached == total:
                shipment.document_status = 'attached'
            elif attached > 0:
                shipment.document_status = 'pending'
            else:
                shipment.document_status = 'missing'

    @api.model_create_multi
    def create(self, vals_list):
        # Auto-generación de checklist al crear el embarque
        shipments = super(LumberExportShipment, self).create(vals_list)
        for shipment in shipments:
            # Buscar configuración activa
            checklists = self.env['lumber.document.checklist'].search([('active', '=', True)])
            if checklists:
                docs_vals = []
                for check in checklists:
                    docs_vals.append({
                        'shipment_id': shipment.id,
                        'checklist_id': check.id,
                        'name': check.name,
                        'state': 'missing'
                    })
                self.env['lumber.shipment.document'].create(docs_vals)
        return shipments
