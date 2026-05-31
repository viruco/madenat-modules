# -*- coding: utf-8 -*-
"""
Wizard: Asignar Lotes a Contenedor
Validación inteligente de capacidad en tiempo real

REGLA DE ORO - CONSISTENCIA:
Este wizard DEBE usar la misma lógica de llenado que lumber.container
para evitar discrepancias entre vista previa y realidad.

Última modificación: 2024-12-04 (Auditoría Técnica - Fase 3)
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging


_logger = logging.getLogger(__name__)



class LumberContainerLotWizard(models.TransientModel):
    _name = 'lumber.container.lot.wizard'
    _description = 'Asistente para Asignar Lotes a Contenedor'
    
    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto del wizard"""
        res = super(LumberContainerLotWizard, self).default_get(fields_list)
        
        container_id = self.env.context.get('default_container_id')
        if container_id:
            res['container_id'] = container_id
            _logger.info(f"Wizard inicializado con contenedor ID: {container_id}")
        
        return res
    
    container_id = fields.Many2one(
        'lumber.container',
        'Contenedor',
        required=True,
        readonly=True
    )
    
    # ========================================
    # INFORMACIÓN DEL CONTENEDOR (READONLY)
    # ========================================
    container_name = fields.Char(related='container_id.name', readonly=True)
    container_type = fields.Selection(related='container_id.container_type', readonly=True)
    current_weight_kg = fields.Float(related='container_id.weight_kg', readonly=True)
    max_weight_kg = fields.Float(related='container_id.max_weight_kg', readonly=True)
    remaining_weight_kg = fields.Float(related='container_id.remaining_weight_kg', readonly=True)
    current_volume_m3 = fields.Float(related='container_id.volume_m3', readonly=True)
    max_volume_m3 = fields.Float(related='container_id.max_volume_m3', readonly=True)
    remaining_volume_m3 = fields.Float(related='container_id.remaining_volume_m3', readonly=True)
    
    # ========================================
    # LOTES DISPONIBLES Y SELECCIONADOS
    # ========================================
    available_lot_ids = fields.Many2many(
        'stock.lot',
        'wizard_available_lot_rel',
        'wizard_id',
        'lot_id',
        'Lotes Disponibles',
        compute='_compute_available_lots',
        readonly=True
    )
    
    selected_lot_ids = fields.Many2many(
        'stock.lot',
        'wizard_selected_lot_rel',
        'wizard_id',
        'lot_id',
        'Lotes a Asignar',
        domain="[('id', 'in', available_lot_ids)]"
    )
    
    # ========================================
    # VALIDACIÓN EN TIEMPO REAL (NUEVOS CAMPOS)
    # ========================================
    new_total_weight_kg = fields.Float(
        'Nuevo Peso Total',
        compute='_compute_new_totals',
        help='Peso total después de asignar lotes seleccionados'
    )
    
    new_total_volume_m3 = fields.Float(
        'Nuevo Volumen Total',
        compute='_compute_new_totals',
        help='Volumen total después de asignar lotes seleccionados'
    )
    
    # 🆕 NUEVO: Porcentaje de llenado proyectado (consistente con contenedor)
    projected_fill_percentage = fields.Float(
        'Llenado Proyectado (%)',
        compute='_compute_validation_status',
        help='Porcentaje de llenado basado en el factor limitante (peso o volumen)'
    )
    
    weight_exceeds = fields.Boolean(
        'Excede Peso',
        compute='_compute_validation_status'
    )
    
    volume_exceeds = fields.Boolean(
        'Excede Volumen',
        compute='_compute_validation_status'
    )
    
    validation_message = fields.Html(
        'Estado de Validación',
        compute='_compute_validation_status'
    )
    def action_confirm(self):
        """
        1. Guarda los lotes en el contenedor.
        2. Fuerza al Embarque (Padre) a recalcular sus totales.
        3. Recarga la pantalla (F5 automático).
        """
        self.ensure_one()
        
        # 1. GUARDAR: Escribimos los lotes seleccionados en el contenedor
        # (Usamos el comando (6, 0, IDs) para reemplazar la lista existente)
        self.container_id.write({
            'lot_ids': [(6, 0, self.lot_ids.ids)]
        })

        # 2. RECALCULAR PADRE: Si el contenedor tiene embarque, forzamos la suma
        if self.container_id.shipment_id:
            # Aquí llamamos al método _compute_totals DEL EMBARQUE (no del contenedor)
            # Asegúrate que el modelo 'lumber.export.shipment' tenga este método público
            self.container_id.shipment_id._compute_totals()

        # 3. RECARGAR INTERFAZ: La magia que actualiza la vista web
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    # ========================================
    # MÉTODOS COMPUTADOS
    # ========================================
    @api.model
    def _get_available_lots_domain(self):
        """ 
        🔍 FILTRO INTELIGENTE: 
        Excluye lotes que ya están en contenedores activos (no enviados).
        """
        # 1. Buscar todos los lotes que están en contenedores "en proceso"
        # (loading, loaded, sealed). Los 'shipped' ya se fueron, así que técnicamente
        # sus lotes ya no están en patio, pero igual los excluiremos por seguridad.
        active_containers = self.env['lumber.container'].search([
            ('state', 'in', ['loading', 'loaded', 'sealed'])
        ])
        
        # Obtenemos los IDs de los lotes ocupados
        busy_lot_ids = active_containers.mapped('lot_ids').ids
        
        # 2. Retornar dominio: Lotes en stock Y que NO estén en la lista de ocupados
        return [
            ('quant_ids.quantity', '>', 0),       # Que existan físicamente
            ('id', 'not in', busy_lot_ids)        # Que no estén en otro contenedor
        ]

    # Aplicar este dominio al campo Many2many del wizard
    lot_ids = fields.Many2many(
        'stock.lot', 
        domain=_get_available_lots_domain,  # <--- AQUÍ ESTÁ LA MAGIA
        string="Lotes a Agregar"
    )
    
    @api.depends('container_id')
    def _compute_available_lots(self):
            """
            Obtener lotes disponibles para asignar con filtro estricto de calidad.
            """
            for wizard in self:
                if not wizard.container_id:
                    wizard.available_lot_ids = [(5, 0, 0)]
                    continue
                
                # 1. Detectar lotes ocupados en OTROS contenedores activos
                occupied_lines = self.env['lumber.shipment.line'].search([
                    ('container_id', '!=', False),
                    ('container_id', '!=', wizard.container_id.id),
                ])
                occupied_lot_ids = occupied_lines.mapped('lot_id.id')
                
                # 2. DOMINIO BLINDADO: Solo lo que está en patio y APROBADO
                domain = [
                    ('estado_trazabilidad', '=', 'en_patio'),
                    ('technical_validation', '=', 'approved'), # 👈 Solo calidad certificada
                    ('id', 'not in', wizard.container_id.lot_ids.ids),
                    ('id', 'not in', occupied_lot_ids),
                    ('product_id.type', 'in', ['product', 'consu']),
                ]
                
                # 3. Ejecutar y asignar
                found_lots = self.env['stock.lot'].search(domain)
                wizard.available_lot_ids = found_lots
                
                _logger.info(f"Wizard {wizard.container_id.name}: {len(found_lots)} lotes disponibles para exportación.")



    @api.depends('selected_lot_ids', 'selected_lot_ids.volumen_m3')
    def _compute_new_totals(self):
        """
        Calcular totales proyectados si se asignan los lotes seleccionados.
        
        REGLA DE ORO - SUMA DEFENSIVA:
        - Validar existencia de campos antes de mapear
        - Manejar casos donde lotes no tienen peso (usar 0.0)
        - Volumen es obligatorio (volumen_m3 siempre existe)
        """
        for wizard in self:
            # Suma de peso (defensiva: algunos lotes pueden no tener peso)
            selected_weight = 0.0
            if 'weight_kg' in wizard.selected_lot_ids._fields:
                selected_weight = sum(wizard.selected_lot_ids.mapped('weight_kg'))
            
            # Suma de volumen (siempre existe)
            selected_volume = sum(wizard.selected_lot_ids.mapped('volumen_m3'))
            
            wizard.new_total_weight_kg = wizard.current_weight_kg + selected_weight
            wizard.new_total_volume_m3 = wizard.current_volume_m3 + selected_volume
    
    @api.depends('new_total_weight_kg', 'new_total_volume_m3', 'container_id')
    def _compute_validation_status(self):
        """
        Validar capacidad y generar mensaje visual.
        
        🔥 REGLA DE ORO - CONSISTENCIA CON CONTENEDOR:
        Este método DEBE usar la misma lógica que lumber.container._compute_fill_percentage()
        para calcular el porcentaje de llenado proyectado.
        
        Fórmula:
        - weight_pct = (new_weight / max_weight) * 100
        - volume_pct = (new_volume / max_volume) * 100
        - projected_fill = max(weight_pct, volume_pct)  ← FACTOR LIMITANTE
        """
        for wizard in self:
            # ============================================
            # 1. DEFINICIÓN SEGURA DE VARIABLES (FIXED)
            # ============================================
            # Protegemos contra False/None usando "or 0.0"
            total_weight = wizard.new_total_weight_kg or 0.0
            total_volume = wizard.new_total_volume_m3 or 0.0
            
            max_weight = wizard.container_id.max_weight_kg or 0.0
            max_volume = wizard.container_id.max_volume_m3 or 0.0

            # ============================================
            # 2. CALCULAR PORCENTAJES INDIVIDUALES
            # ============================================
            weight_pct = (total_weight / max_weight * 100) if max_weight > 0 else 0.0
            volume_pct = (total_volume / max_volume * 100) if max_volume > 0 else 0.0
            
            # ============================================
            # 3. CALCULAR LLENADO PROYECTADO (FACTOR LIMITANTE)
            # ============================================
            
            # 🔥 FIX: Try/Except ATÓMICO + fallback seguro
            try:
                metrics = self.env['lumber.container']._calculate_capacity_metrics(
                    total_weight, max_weight, total_volume, max_volume
                )
                wizard.projected_fill_percentage = metrics.get('fill_pct', max(weight_pct, volume_pct))
            except (AttributeError, KeyError, TypeError):
                wizard.projected_fill_percentage = max(weight_pct, volume_pct)

            # ============================================
            # 4. VALIDAR LÍMITES
            # ============================================
            # Usamos tolerancia de 0.01 para evitar errores de redondeo flotante
            weight_exceeds = total_weight > (max_weight + 0.01)
            volume_exceeds = total_volume > (max_volume + 0.01)
            
            wizard.weight_exceeds = weight_exceeds
            wizard.volume_exceeds = volume_exceeds
            
            # ============================================
            # 5. GENERAR MENSAJE HTML DINÁMICO
            # ============================================
            if not wizard.selected_lot_ids:
                # Sin lotes seleccionados
                wizard.validation_message = '<p class="text-muted">Selecciona lotes para ver validación</p>'
                
            elif weight_exceeds or volume_exceeds:
                # ❌ CAPACIDAD EXCEDIDA
                limiting_factor = 'VOLUMEN' if volume_exceeds else 'PESO'
                
                msg = '<div class="alert alert-danger" role="alert">'
                msg += '<h5>⚠️ Capacidad Excedida</h5>'
                
                if weight_exceeds:
                    excess_kg = total_weight - max_weight
                    msg += f'<p><b>❌ Peso:</b> {total_weight:.1f} kg supera máximo {max_weight:.1f} kg '
                    msg += f'(exceso: <span class="text-danger">{excess_kg:.1f} kg</span>)</p>'
                
                if volume_exceeds:
                    excess_m3 = total_volume - max_volume
                    msg += f'<p><b>❌ Volumen:</b> {total_volume:.2f} m³ supera máximo {max_volume:.2f} m³ '
                    msg += f'(exceso: <span class="text-danger">{excess_m3:.2f} m³</span>)</p>'
                
                msg += f'<hr/>'
                msg += f'<p><b>Factor limitante:</b> <span class="badge badge-danger">{limiting_factor}</span></p>'
                msg += '</div>'
                wizard.validation_message = msg
                
            else:
                # ✅ ASIGNACIÓN VÁLIDA
                limiting_factor = 'VOLUMEN' if volume_pct > weight_pct else 'PESO' if weight_pct > volume_pct else 'BALANCEADO'
                
                msg = '<div class="alert alert-success" role="alert">'
                msg += '<h5>✅ Asignación Válida</h5>'
                msg += f'<p><b>Lotes seleccionados:</b> {len(wizard.selected_lot_ids)}</p>'
                
                msg += '<hr/>'
                
                # Mostrar ambos porcentajes pero resaltar el limitante
                weight_badge = 'badge-warning' if weight_pct > volume_pct else 'badge-secondary'
                volume_badge = 'badge-warning' if volume_pct > weight_pct else 'badge-secondary'
                
                msg += f'<p><b>📊 Peso:</b> {total_weight:.1f} / {max_weight:.1f} kg '
                msg += f'<span class="badge {weight_badge}">{weight_pct:.1f}%</span></p>'
                
                msg += f'<p><b>📦 Volumen:</b> {total_volume:.2f} / {max_volume:.2f} m³ '
                msg += f'<span class="badge {volume_badge}">{volume_pct:.1f}%</span></p>'
                
                msg += '<hr/>'
                
                # 🔥 MOSTRAR LLENADO PROYECTADO (FACTOR LIMITANTE)
                fill_color = 'success' if wizard.projected_fill_percentage < 50 else 'warning' if wizard.projected_fill_percentage < 90 else 'danger'
                msg += f'<h6><b>🎯 Llenado proyectado:</b> '
                msg += f'<span class="badge badge-{fill_color}" style="font-size: 14px;">{wizard.projected_fill_percentage:.1f}%</span></h6>'
                msg += f'<p class="text-muted small">Factor limitante: <b>{limiting_factor}</b></p>'
                
                msg += '</div>'
                wizard.validation_message = msg

    
    # ========================================
    # ACCIONES
    # ========================================
    
    def action_assign(self):
        """
        Asignar lotes al contenedor después de validar.
        
        REGLA DE ORO - VALIDACIÓN ESTRICTA:
        1. Al menos un lote seleccionado
        2. No exceder peso máximo
        3. No exceder volumen máximo  ← AHORA VALIDADO
        4. Actualizar estado del contenedor
        5. Actualizar trazabilidad de lotes
        6. Registrar en chatter con métricas
        
        Returns:
            dict: Acción de cierre de wizard
        
        Raises:
            UserError: Si no hay lotes seleccionados
            ValidationError: Si excede capacidad de peso o volumen
        """
        self.ensure_one()
        
        # ============================================
        # 1. VALIDACIÓN: Lotes seleccionados
        # ============================================
        if not self.selected_lot_ids:
            raise UserError(_('Debe seleccionar al menos un lote'))
        
        # ============================================
        # 2. VALIDACIÓN: Capacidad de peso Y volumen
        # ============================================
        if self.weight_exceeds or self.volume_exceeds:
            error_msg = _('No se puede asignar: La capacidad del contenedor sería excedida.\n\n')
            
            if self.weight_exceeds:
                error_msg += _('❌ Peso: %.1f / %.1f kg (exceso: %.1f kg)\n') % (
                    self.new_total_weight_kg, 
                    self.max_weight_kg,
                    self.new_total_weight_kg - self.max_weight_kg
                )
            
            if self.volume_exceeds:
                error_msg += _('❌ Volumen: %.2f / %.2f m³ (exceso: %.2f m³)\n') % (
                    self.new_total_volume_m3, 
                    self.max_volume_m3,
                    self.new_total_volume_m3 - self.max_volume_m3
                )
            
            error_msg += _('\n💡 Sugerencia: Selecciona menos lotes o usa otro contenedor.')
            
            raise ValidationError(error_msg)
        
        # ============================================
        # 3. ASIGNACIÓN: Vincular lotes al contenedor
        # ============================================
        self.container_id.write({
            'lot_ids': [(4, lot.id) for lot in self.selected_lot_ids]
        })
        
        # ============================================
        # 4. CAMBIAR ESTADO: empty → loading
        # ============================================
        if self.container_id.state == 'empty':
            self.container_id.state = 'loading'
        
        # ============================================
        # 5. ACTUALIZAR TRAZABILIDAD: Lotes → consolidado
        # ============================================
        self.selected_lot_ids.write({
            'estado_trazabilidad': 'consolidado'
        })
        
        # ============================================
        # 6. REGISTRO EN CHATTER: Auditoría
        # ============================================
        # Identificar factor limitante para el mensaje
        weight_pct = (self.container_id.weight_kg / self.container_id.max_weight_kg * 100) if self.container_id.max_weight_kg else 0
        volume_pct = (self.container_id.volume_m3 / self.container_id.max_volume_m3 * 100) if self.container_id.max_volume_m3 else 0
        limiting_factor = '📦 VOLUMEN' if volume_pct > weight_pct else '⚖️ PESO'
        
        self.container_id.message_post(
            body=_(
                '✅ <b>Asignados %d lotes al contenedor</b><br/><br/>'
                '<b>📊 Métricas actualizadas:</b><br/>'
                '📦 Paquetes: %d<br/>'
                '📐 Volumen: %.2f m³ (%.1f%%)<br/>'
                '⚖️ Peso: %.1f kg (%.1f%%)<br/>'
                '<b>🎯 Llenado: %.1f%%</b> (Factor limitante: %s)'
            ) % (
                len(self.selected_lot_ids), 
                self.container_id.packages,
                self.container_id.volume_m3,
                volume_pct,
                self.container_id.weight_kg,
                weight_pct,
                self.container_id.fill_percentage,
                limiting_factor
            )
        )
        
        # ============================================
        # 7. LOG DE AUDITORÍA
        # ============================================
        _logger.info(
            f"✅ Asignados {len(self.selected_lot_ids)} lotes a contenedor {self.container_id.name}. "
            f"Llenado: {self.container_id.fill_percentage:.1f}% (Factor: {limiting_factor})"
        )
        
        # ============================================
        # 8. CERRAR WIZARD
        # ============================================
        return {'type': 'ir.actions.act_window_close'}
