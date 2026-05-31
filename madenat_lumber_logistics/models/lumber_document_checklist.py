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
    ], string='Estado', default='missing', index=True, compute='_compute_state', store=True)
    
    notes = fields.Text('Notas Adicionales')

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

    @api.depends('document_ids.state', 'document_ids.checklist_id.is_required')
    def _compute_document_status(self):
        for shipment in self:
            # Si no hay documentos, todo está pendiente
            if not shipment.document_ids:
                shipment.document_status = 'pending'
                shipment.document_completion = 0.0
                continue

            # 1. Identificar documentos requeridos
            required_docs = shipment.document_ids.filtered(lambda d: d.checklist_id.is_required)
            
            # Si no hay obligatorios definidos, usamos todos como base
            target_docs = required_docs if required_docs else shipment.document_ids
            total_target = len(target_docs)

            if total_target == 0:
                shipment.document_status = 'complete'
                shipment.document_completion = 100.0
                continue

            # 2. Contar documentos cumplidos (Adjuntos o Verificados)
            fulfilled = target_docs.filtered(lambda d: d.state in ['attached', 'verified'])
            count_fulfilled = len(fulfilled)

            # 3. Calcular porcentaje y estado
            shipment.document_completion = (count_fulfilled / total_target) * 100

            if count_fulfilled == total_target:
                shipment.document_status = 'complete'
            elif count_fulfilled > 0:
                shipment.document_status = 'incomplete'
            else:
                shipment.document_status = 'pending'

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
