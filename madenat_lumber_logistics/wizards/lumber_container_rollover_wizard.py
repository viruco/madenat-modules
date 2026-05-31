# -*- coding: utf-8 -*-
"""
Wizard: Gestión de Rolleo de Contenedores
Versión: 1.2.0 - AUDIT 2026-01-27 [FIX-SEALS+FINANCIAL]
✅ AGREGADO: old_seal/new_seal fields visibles
✅ CORREGIDO: write() con dict completo (seal_number incluido)
✅ MEJORADO: UX validaciones + logging audit
✅ REGLA DE ORO: Mínimo impacto, máximo robustecimiento
Autor: MADENAT + Senior Odoo Architect
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class ContainerRolloverWizard(models.TransientModel):
    _name = 'lumber.container.rollover.wizard'
    _description = 'Wizard para Gestionar Rolleo de Contenedor'
    
    # ==================== CAMPOS ====================
    
    container_id = fields.Many2one(
        'lumber.container',
        string='Contenedor',
        readonly=True,
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.context.get('default_container_id'),
        help="Contenedor que será objeto del rolleo"
    )
    
    # Campos informativos del contenedor
    container_name = fields.Char(
        related='container_id.name',
        string='Número Contenedor',
        readonly=True
    )
    
    current_shipment = fields.Many2one(
        related='container_id.shipment_id',
        string='Embarque Actual',
        readonly=True
    )
    
    lot_count = fields.Integer(
        related='container_id.lot_count',
        string='Lotes Asignados',
        readonly=True
    )
    
    # Motivo del rolleo
    motive = fields.Selection(
        [
            ('overbooking', 'Sobreventa Naviera (Overbooking)'),
            ('technical', 'Falla Técnica del Contenedor'),
            ('customs', 'Revisión o Retención Aduanera'),
            ('commercial', 'Cambio Comercial del Cliente'),
            ('logistics', 'Problema Logístico Interno'),
            ('other', 'Otro Motivo')
        ],
        string='Motivo del Rolleo',
        required=True,
        help="Seleccione el motivo principal del rolleo"
    )
    
    other_motive = fields.Char(
        string='Especifique Otro Motivo',
        help="Campo obligatorio si selecciona 'Otro Motivo'"
    )
    
    note = fields.Text(
        string='Comentario Detallado',
        required=True,
        help="Describa en detalle las circunstancias del rolleo: qué, cuándo, por qué y acciones tomadas"
    )
    
    # ==================== SELLOS ✅ MEJORA APLICADA ====================
    old_seal = fields.Char(
        string='Sello Anterior',
        readonly=True, 
        required=True,
        related='container_id.seal_number',  # Auto-populate desde container
        help="Sello actual que será reemplazado"
    )
    
    new_seal = fields.Char(
        string='Nuevo Sello', 
        required=True,
        help="Nuevo número de sello de seguridad (ej: SEAL-2026-001)"
    )
    
    # ==================== VALIDACIONES (EXISTENTES + MEJORADAS) ====================
    
    @api.constrains('motive', 'other_motive')
    def _check_other_motive(self):
        for wizard in self:
            if wizard.motive == 'other' and not wizard.other_motive:
                raise ValidationError(_("Debe especificar el motivo cuando selecciona 'Otro Motivo'"))
    
    @api.constrains('new_seal', 'old_seal')
    def _check_different_seals(self):
        for wizard in self:
            if wizard.new_seal and wizard.old_seal:
                if wizard.new_seal.strip().upper() == wizard.old_seal.strip().upper():
                    raise ValidationError(_("El nuevo sello debe ser diferente al sello anterior"))
    
    @api.constrains('new_seal')
    def _check_seal_format(self):
        for wizard in self:
            if wizard.new_seal:
                seal = wizard.new_seal.strip()
                if len(seal) < 3:
                    raise ValidationError(_("El número de sello debe tener al menos 3 caracteres"))
    
    @api.constrains('note')
    def _check_note_length(self):
        for wizard in self:
            if wizard.note and len(wizard.note.strip()) < 20:
                raise ValidationError(_("El comentario debe tener al menos 20 caracteres. "
                                      "Por favor proporcione una descripción detallada del motivo del rolleo."))
    
    # ==================== MÉTODO PRINCIPAL ✅ FIX CRÍTICO APLICADO ====================
    
    def action_confirm_rollover(self):
        """
        Confirmar y ejecutar el rolleo del contenedor
        
        Proceso OPTIMIZADO v1.2.0:
        1. Validar contenedor + embarque
        2. ✅ INTEGRIDAD FINANCIERA (bloquea costos huérfanos)
        3. Registrar AUDIT completo en chatter
        4. ✅ WRITE COMPLETO con sellos (FIX 2026-01-27)
        5. Notificar embarque origen
        6. Success notification
        """
        self.ensure_one()
        
        # 1. Validaciones básicas
        if not self.container_id:
            raise ValidationError(_('Contenedor no encontrado'))
        
        if not self.current_shipment:
            raise UserError(_("El contenedor '%s' no está asignado a ningún embarque.\n"
                            "El rolleo solo aplica para contenedores ya consolidados.") % self.container_name)
        
        old_shipment = self.current_shipment
        
        # 2. ✅ REGLA DE ORO - INTEGRIDAD FINANCIERA
        lots = self.container_id.lot_ids
        if lots and old_shipment:
            distributed_costs = self.env['stock.lot.cost.line'].search([
                ('lot_id', 'in', lots.ids),
                ('source_shipment_cost_line_id.shipment_id', '=', old_shipment.id)
            ], limit=1)
            
            if distributed_costs:
                raise UserError(_(
                    "⛔ ACCIÓN BLOQUEADA POR SEGURIDAD FINANCIERA\n\n"
                    "Contenedor: %s\nEmbarque: %s\n\n"
                    "Tiene costos distribuidos. Revierte costos en embarque primero."
                ) % (self.container_name, old_shipment.name))
        
        # 3. Preparar motivo para audit
        motive_dict = dict(self._fields['motive'].selection)
        motive_text = motive_dict.get(self.motive, self.motive)
        if self.motive == 'other' and self.other_motive:
            motive_text = f"{motive_text}: {self.other_motive}"
        
        # 4. ✅ AUDIT COMPLETO - Chatter del contenedor
        rollover_message = _(
            "<div style='padding: 15px; background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%); "
            "border-left: 5px solid #ffc107; border-radius: 5px;'>"
            "<h4 style='margin: 0 0 10px; color: #856404; font-size: 16px;'>🔄 ROLLEO EJECUTADO</h4>"
            "<table style='width: 100%; border-collapse: collapse; font-size: 13px;'>"
            "<tr><td style='padding: 4px 8px; font-weight: bold; width: 35%;'>📦 Embarque:</td><td>%s</td></tr>"
            "<tr><td style='padding: 4px 8px; font-weight: bold;'>🎯 Motivo:</td><td>%s</td></tr>"
            "<tr><td style='padding: 4px 8px; font-weight: bold;'>🔒 Sello Anterior:</td><td style='color: #666;'>%s</td></tr>"
            "<tr><td style='padding: 4px 8px; font-weight: bold;'>✅ Sello Nuevo:</td><td style='color: #28a745; font-weight: bold;'>%s</td></tr>"
            "<tr><td style='padding: 4px 8px; font-weight: bold;'>📊 Lotes:</td><td>%d lotes</td></tr>"
            "<tr><td style='padding: 4px 8px; font-weight: bold;'>📝 Detalle:</td><td style='max-width: 300px;'>%s</td></tr>"
            "</table>"
            "<hr style='margin: 10px 0;'>"
            "<small style='color: #856404;'>Ejecutado: %s por %s</small>"
            "</div>"
        ) % (
            self.current_shipment.name,
            motive_text,
            self.old_seal or 'Sin sello',
            self.new_seal,
            self.lot_count,
            self.note[:200] + '...' if len(self.note) > 200 else self.note,
            fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
            self.env.user.name
        )
        
        self.container_id.message_post(body=rollover_message, subject=_('🔄 Rolleo de Contenedor'), message_type='comment')
        
        # 5. ✅ EXECUTAR ROLLEO - WRITE COMPLETO (FIX CRÍTICO)
        try:
            self.container_id.write({
                'seal_number': self.new_seal,     # ✅ FIX: Ahora SÍ se actualiza
                'state': 'loading',
                'shipment_id': False,
                'sealing_date': False            # Reset fecha sellado
            })
        except ValidationError as e:
            raise UserError(f"Error de validación modelo: {e.name}")
        except Exception as e:
            _logger.error(f"ROLLOVER ERROR técnico [{self.container_name}]: {e}", exc_info=True)
            raise UserError(_("Error técnico al ejecutar rolleo. Revise logs del servidor."))
        
        # 6. Notificar embarque origen
        if old_shipment:
            old_shipment.message_post(
                body=_(
                    "<div style='background: #d4edda; padding: 10px; border-left: 4px solid #28a745;'>"
                    "<strong>⚠️ Contenedor retirado:</strong> %s<br>"
                    "<em>Motivo:</em> %s<br>"
                    "<small>Usuario: %s | %s</small>"
                    "</div>"
                ) % (self.container_name, motive_text, self.env.user.name, fields.Datetime.now().strftime('%H:%M')),
                subject=_('Contenedor Rolleado')
            )
        
        # 7. AUDIT LOG + SUCCESS
        _logger.info(f"✅ ROLLOVER COMPLETADO: {self.container_name} ← {old_shipment.name if old_shipment else 'N/A'} "
                    f"[Motivo: {motive_text} | Usuario: {self.env.user.name}]")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Rolleo Completado'),
                'message': _('Contenedor <strong>%s</strong> rolleado exitosamente.<br>'
                           '<em>Nuevo sello: %s</em><br>'
                           'Listo para reasignar a nuevo embarque.') % (self.container_name, self.new_seal),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
