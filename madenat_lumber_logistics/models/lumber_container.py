# -*- coding: utf-8 -*-
"""
Modelo: Contenedor de Exportación
Versión: 3.1.0 - Edición Enterprise (Consolidada con Dualidad de Volumen)
Características:
- Integridad Financiera (Bloqueo de cambios con costos distribuidos)
- Cálculo de Llenado basado en Factor Limitante (Peso vs Volumen)
- Validación VGM (SOLAS)
- Validación Operativa de Lotes
- [NUEVO] Soporte para Volumen Físico (Facturable) vs Nominal (Costo)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import float_compare
from psycopg2.errors import LockNotAvailable  # Sub-bloque 4B: lock transaccional
import logging
import io          # <-- Para el Excel
import base64      # <-- Para el Excel
import hashlib     # <-- I0.3: firma SHA-256 de auditoría de rebaja/reversa
import json        # <-- I0.3: snapshot determinista de auditoría

_logger = logging.getLogger(__name__)

class LumberContainer(models.Model):
    _name = 'lumber.container'
    _description = 'Contenedor de Exportación'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'madenat.deviation.mixin']
    _order = 'name'
    _sql_constraints = [
        ('seal_uniq', 'unique(seal_number, shipment_id)', '¡El número de sello ya existe en este embarque! Verifique duplicados.'),
    ]
    # ==================== IDENTIFICACIÓN ====================
    name = fields.Char(
        'Número Contenedor',
        required=True,
        tracking=True,
        help="Número único del contenedor (ej: CAIU7063234)"
    )
    
    shipment_id = fields.Many2one(
        'lumber.export.shipment', 
        'Embarque',
        required=False,
        ondelete='restrict',
        tracking=True,
        index=True,
        help="Embarque al que pertenece este contenedor. Se asigna durante la consolidación."
    )
    
    # ==================== TIPO Y CARACTERÍSTICAS ====================
    container_type = fields.Selection([
        ('20', "20' Estándar"),
        ('40', "40' Estándar"),
        ('40HC', "40' High Cube"),
        ('45', "45' High Cube")
    ], 
        required=True,
        default='40HC',
        tracking=True,
        help="Tipo de contenedor según estándar ISO"
    )
    
    seal_number = fields.Char(
        'Número Sello',
        tracking=True,
        copy=False,
        help="Sello de seguridad del contenedor"
    )
    
    sag_seal = fields.Char(
        'Sello SAG',
        tracking=True,
        copy=False,
        help="Número de precinto del SAG. Puede ingresarse posteriormente al zarpe."
    )
    # ==================== RELACIONES DE CONTENIDO (ARQUITECTURA) ====================
    
    # Fuente de verdad: Líneas de embarque
    line_ids = fields.One2many(
        'lumber.shipment.line', 
        'container_id', 
        string='Líneas de Embarque'
    )

    # Campo "Virtual" para compatibilidad y escritura directa de lotes
    lot_ids = fields.Many2many(
        'stock.lot',
        compute='_compute_lot_ids',
        inverse='_inverse_lot_ids',
        string='Lotes Físicos',
        help="Lotes asignados. Al escribir aquí, se crean/borran líneas automáticamente.",
        store=True
    )

    # ==================== PESOS (ESTÁNDAR ISO/SOLAS) ====================
    tare_weight_kg = fields.Float(
        'Peso Tara (Vacío) Kg',
        compute='_compute_tare_weight',
        store=True,
        digits=(16, 1),
        help="Peso del contenedor vacío según estándar ISO"
    )
    
    weight_kg = fields.Float(
        'Peso Neto Carga Kg',
        digits=(16, 1),
        help="Peso neto de la carga (sin contenedor)"
    )
    
    gross_weight_kg = fields.Float(
        'Peso Bruto Total (VGM) Kg',
        compute='_compute_gross_weight',
        store=True,
        digits=(16, 1),
        help="Verified Gross Mass (VGM) - Peso total verificado según SOLAS"
    )
    
    # ==================== VOLUMEN Y CANTIDADES (NUEVO DUAL) ====================
    
    # 1. Base de Facturación y Carga (El Real)
    total_vol_shipment_m3 = fields.Float(
        'Vol. Exportación (facturable)',
        compute='_compute_volume_totals', 
        store=True,
        digits=(16, 3),
        help="Volumen de exportación (documental). Base para la FACTURACIÓN de exportación y cálculo de espacio."
    )
    
    # 2. Referencia de Costos (El Nominal)
    total_volume_purchase_m3 = fields.Float(
        'Vol. Nominal (Ref. Costo)', 
        compute='_compute_volume_totals', 
        store=True,
        digits=(16, 3),
        help="Volumen nominal estándar. Usado para comparativas de costos y rendimiento."
    )
    
    # 3. Control de Calidad
    volume_variance_pct = fields.Float(
        'Desviación %',
        compute='_compute_volume_totals',
        store=True,
        digits=(16, 2),
        help="Diferencia entre Físico y Nominal. Positivo = Sobremedida (Regalas madera)."
    )

    # 4. Campo Estructural (Legacy/Core) - Mapeado al Físico
    volume_m3 = fields.Float(
        'Vol. Exportación (total)',
        compute='_compute_volume_totals', 
        store=True,
        digits=(16, 3),
        help="Alias de Vol. Exportación (documental, total)."
    )

    # Bloque 7.3: Merma dimensional total del contenedor
    total_merma_dimensional_m3 = fields.Float(
        'Total Merma Dimensional (m³)',
        compute='_compute_volume_totals',
        store=True,
        digits=(16, 3),
        help='Suma de la merma dimensional de los lotes del contenedor'
    )
    
    volume_mbf = fields.Float(
        'Volumen MBF',
        compute='_compute_volume_mbf_from_lots',
        store=True,
        digits=(16, 4),
        help="Volumen total en MBF"
    )
    
    packages = fields.Integer(
        'N° Paquetes/Tarjas',
        compute='_compute_packages_from_lots',
        store=True,
        help="Cantidad de paquetes/tarjas físicos"
    )
    
    total_pieces = fields.Integer(
        'Total Piezas',
        compute='_compute_total_pieces_from_lots',
        store=True,
        help="Total de piezas individuales (tablas)"
    )
    
    # ==================== CAPACIDADES TÉCNICAS ====================
    max_weight_kg = fields.Float(
        'Peso Máximo Carga Kg',
        compute='_compute_max_capacity',
        store=True,
        digits=(16, 1),
        help="Capacidad máxima de carga (payload)"
    )
    
    max_gross_weight_kg = fields.Float(
        'Peso Bruto Máximo Kg',
        compute='_compute_max_capacity',
        store=True,
        digits=(16, 1),
        help="Peso bruto máximo permitido según ISO"
    )
    
    max_volume_m3 = fields.Float(
        'Volumen Máximo m³',
        compute='_compute_max_capacity',
        store=True,
        help="Volumen máximo según tipo de contenedor"
    )
    
    # ==================== CAPACIDAD RESTANTE ====================
    remaining_volume_m3 = fields.Float(
        'Capacidad Restante m³',
        compute='_compute_remaining_capacity',
        store=True,
        digits=(16, 3),
        help="Volumen restante disponible"
    )
    
    remaining_weight_kg = fields.Float(
        'Capacidad Peso Restante Kg',
        compute='_compute_remaining_capacity',
        store=True,
        digits=(16, 1),
        help="Capacidad de peso restante"
    )
    
    # ==================== CAMPOS PARA VISTA KANBAN ====================
    fill_percentage = fields.Float(
        'Porcentaje de Llenado',
        compute='_compute_fill_percentage',
        store=True,
        help='Porcentaje de capacidad utilizada basado en peso o volumen'
    )
    
    status_color = fields.Integer(
        'Color de Estado',
        compute='_compute_status_color',
        store=True,
        help='Color del semáforo: 1=Verde, 2=Amarillo, 3=Naranja, 4=Rojo'
    )
    
    lot_count = fields.Integer(
        'Total Lotes',
        compute='_compute_lot_count',
        store=True
    )
    
    # ==================== ESTADO ====================
    state = fields.Selection([
        ('empty', 'Vacío'),
        ('loading', 'Cargando'),
        ('loaded', 'Cargado'),
        ('sealed', 'Sellado'),
        # AD-82 / CANON/18 §3.2: estado propio tras rebajar el inventario.
        ('rebajado', 'Rebajado'),
        ('shipped', 'Embarcado')
    ],
        string='Estado',
        default='empty',
        required=True,
        tracking=True,
        help="Estado del proceso de consolidación"
    )
    
    # ==================== FECHAS ====================
    loading_date = fields.Datetime('Fecha Carga', readonly=True, copy=False)
    sealing_date = fields.Datetime('Fecha Sellado', readonly=True, copy=False)
    state_before_rebaja = fields.Selection([
        ('loaded', 'Cargado'),
        ('sealed', 'Sellado'),
    ], string='Estado previo a rebaja', copy=False, readonly=True,
        help='Estado del contenedor antes de rebajar; se restaura al revertir.')
    # Sub-bloque 4B (2026-10-04) — R2: evidencia visible de la cadena de retorno
    # físico (salida OUT → retorno IN) para la reversa total por Contenedor.
    rebaja_origin_picking_names = fields.Char(
        'Salida de rebaja (OUT)', compute='_compute_rebaja_return_display',
        help='Picking(s) de salida de rebaja del contenedor (Customers).')
    rebaja_return_picking_names = fields.Char(
        'Retorno físico (IN)', compute='_compute_rebaja_return_display',
        help='Picking(s) de retorno físico validado (Customers → interno).')
    # Sub-bloque 4A (2026-10-04): estado B-01 del Embarque (sólo lectura). El
    # formulario avisa y la rebaja estándar post-zarpe queda bloqueada.
    b01_exception_state = fields.Selection(
        related='shipment_id.b01_exception_state',
        string='Excepción B-01 del Embarque', readonly=True)

    notes = fields.Text('Notas', help="Observaciones adicionales")
    
    # ==================== CONSTRAINTS SQL ====================
    _sql_constraints = [
        ('name_unique', 
         'UNIQUE(name)', 
         '⚠️ El número de contenedor ya existe en el sistema. Cada contenedor debe tener un número único.')
    ]
    vessel_id = fields.Many2one(
            related='shipment_id.vessel_id',
            string='Motonave (Barco)',
            store=True,
            readonly=True
    )
    # ==================== MÉTODOS COMPUTADOS ====================
    
    total_volume_m3 = fields.Float(
        string="Volumen Total", 
        compute="_compute_totals", 
        store=True,
        digits=(16, 3)
    )

    # 🚀 RESUMEN DE CARGA CON 3 DECIMALES Y CONTEO DINÁMICO
    @api.depends('lot_ids', 'lot_ids.ref', 'lot_ids.vol_shipment_m3')
    def _compute_totals(self):
        for rec in self:
            # Líneas físicas totales (Lotes)
            rec.lot_count = len(rec.lot_ids)
            
            # Paquetes reales (Etiquetas únicas)
            unique_tags = {l.ref for l in rec.lot_ids if l.ref}
            rec.packages = len(unique_tags)
            
            # Sumatorias con precisión de 3 decimales
            rec.total_pieces = sum(rec.lot_ids.mapped('piezas'))
            rec.total_volume_m3 = sum(rec.lot_ids.mapped('vol_shipment_m3'))

    @api.depends('line_ids')
    def _compute_lot_ids(self):
        """Sincroniza One2many -> Many2many para lectura"""
        for rec in self:
            rec.lot_ids = rec.line_ids.mapped('lot_id')

    def _inverse_lot_ids(self):
            """
            Sincroniza las líneas de embarque (O2M) y el estado del Lote (container_id).
            MEJORA: Agregada actualización automática de estado_trazabilidad.
            🛡️ PATCH 2026-06-18: Guarda anti-fuga de estado.
            Rechaza lotes cuyo guia_processing_id esté en estado 'draft' o
            cuyo estado_trazabilidad indique reversión, evitando que lotes
            huérfanos de una guía revertida se cuelen a logística.
            """
            for container in self:
                # 1. Identificar el estado actual en la DB vs el estado deseado
                current_lots_in_db = container.line_ids.mapped('lot_id')
                target_lots_from_wizard = container.lot_ids
                
                # 2. LOTES AGREGADOS: Marcar dueño, crear línea Y cambiar estado
                lots_to_add = target_lots_from_wizard - current_lots_in_db
                # 🏷️ PROGRAMA SV — los lotes Volumen exigen rebaja explícita
                # trazable (saldo validado) antes de su asignación.
                sv_lots_to_add = lots_to_add.filtered(
                    lambda l: l.lot_flow_type == 'volume')
                if sv_lots_to_add:
                    container._sv_allocate_lots(sv_lots_to_add)
                for lot in lots_to_add:
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # 🛡️ GUARDA ANTI-FUGA (2026-06-18):
                    # Defensa primaria: technical_validation='rejected'
                    # (estado persistente en el lote, sobrevive a la
                    # desvinculación de guia_processing_id).
                    # Defensa secundaria: guia_processing_id.state='draft'
                    # (para lotes con vínculo aún vivo a guía revertida).
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    if lot.technical_validation == 'rejected':
                        from odoo.exceptions import UserError
                        raise UserError(
                            "⛔ DENEGADO LOGÍSTICO - LOTE REVERTIDO\n\n"
                            f"El lote '{lot.name}' fue marcado como 'Rechazado' "
                            "porque su guía de origen fue devuelta a borrador.\n\n"
                            "No puede consolidar lotes de una guía revertida. "
                            "Vuelva a procesar la guía para regenerar lotes "
                            "válidos antes de usarlos en logística."
                        )
                    if lot.guia_processing_id and lot.guia_processing_id.state == 'draft':
                        from odoo.exceptions import UserError
                        raise UserError(
                            "⛔ DENEGADO LOGÍSTICO - GUÍA REVERTIDA\n\n"
                            f"El lote '{lot.name}' pertenece a la guía "
                            f"'{lot.guia_processing_id.name}' que se encuentra "
                            f"en estado 'Borrador' (revertida).\n\n"
                            "No puede consolidar lotes de una guía que ha sido "
                            "devuelta a borrador. Vuelva a procesar la guía "
                            "antes de usar estos lotes en logística."
                        )
                    lot.write({
                        'container_id': container.id,
                        'estado_trazabilidad': 'consolidado' # 👈 Sincronización de inventario
                    })
                    self.env['lumber.shipment.line'].create({
                        'container_id': container.id,
                        'lot_id': lot.id,
                        'shipment_id': container.shipment_id.id if container.shipment_id else False,
                    })
                
                # 3. LOTES ELIMINADOS: Liberar el lote, borrar línea Y devolver a patio
                lots_to_remove = current_lots_in_db - target_lots_from_wizard
                if lots_to_remove:
                    # 🏷️ PROGRAMA SV — liberar la rebaja de la asignación.
                    sv_lots_to_remove = lots_to_remove.filtered(
                        lambda l: l.lot_flow_type == 'volume')
                    if sv_lots_to_remove:
                        container._sv_release_lots(sv_lots_to_remove)
                    lots_to_remove.write({
                        'container_id': False,
                        'estado_trazabilidad': 'en_patio' # 👈 Liberación automática
                    })
                    lines_to_delete = container.line_ids.filtered(lambda l: l.lot_id in lots_to_remove)
                    lines_to_delete.unlink()

    # ══════════════════════════════════════════════════════════════════════
    # 🏷️ PROGRAMA SV — Asignación con rebaja explícita (solo lotes Volumen)
    # El comportamiento de lotes no-SV permanece intacto.
    # ══════════════════════════════════════════════════════════════════════
    def _sv_allocation_volume(self, lot):
        """Volumen SV a rebajar en la asignación.

        `madenat_sv_rebaja_per_lot` (contexto del asistente) permite indicar un
        volumen explícito; 0/vacío = saldo disponible completo de la etiqueta.
        """
        lot.ensure_one()
        requested = self.env.context.get('madenat_sv_rebaja_per_lot') or 0.0
        return requested if requested > 0 else lot.sv_available_m3

    def _sv_allocate_lots(self, lots):
        """Crea la rebaja SV vinculada al contenedor/embarque (valida saldo)."""
        Operation = self.env['madenat.sv.operation']
        for container in self:
            for lot in lots:
                volume = container._sv_allocation_volume(lot)
                if float_compare(
                        volume, 0.0, precision_rounding=0.001) <= 0:
                    raise ValidationError(_(
                        'La etiqueta SV %s no tiene saldo disponible para '
                        'asignar al contenedor %s.'
                    ) % (lot.name or lot.id, container.name or ''))
                Operation.sv_create_rebaja(
                    lot,
                    volume,
                    reason=_(
                        'Asignación de etiqueta SV al contenedor %s%s.'
                    ) % (
                        container.name or '',
                        ' · embarque %s' % container.shipment_id.name
                        if container.shipment_id else '',
                    ),
                    destination_container=container,
                    destination_shipment=container.shipment_id or None,
                    destination_reference=container.name or False,
                )

    def _sv_release_lots(self, lots):
        """Reversa la rebaja de asignación al liberar el lote (si existe)."""
        Operation = self.env['madenat.sv.operation']
        for container in self:
            for lot in lots:
                Operation.sv_reverse_allocation(
                    lot,
                    container=container,
                    reason=_(
                        'Liberación de etiqueta SV del contenedor %s.'
                    ) % (container.name or ''),
                )

    def action_open_rollover_wizard(self):
            """ 🔌 PUENTE SEGURO: Abre el wizard de rollover sin errores de XMLID """
            self.ensure_one()
            # P0 (2026-10-03): el rolleo normal se valida en servidor antes de
            # abrir el asistente (no se depende sólo de `invisible` en XML).
            self._assert_rollover_eligible()
            return {
                'name': _('Gestión de Rolleo'),
                'type': 'ir.actions.act_window',
                'res_model': 'lumber.container.rollover.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_container_id': self.id,
                    'default_current_shipment': self.shipment_id.id
                }
            }
    @api.depends('container_type')
    def _compute_tare_weight(self):
        tare_weights = {
            '20': 2280.0, '40': 3740.0, '40HC': 4150.0, '45': 4800.0
        }
        for container in self:
            container.tare_weight_kg = tare_weights.get(container.container_type, 0.0)
    
    @api.depends('container_type')
    def _compute_max_capacity(self):
        capacities = {
            '20': {'max_payload': 28200.0, 'max_gross': 30480.0, 'volume': 33.0},
            '40': {'max_payload': 26740.0, 'max_gross': 30480.0, 'volume': 67.0},
            '40HC': {'max_payload': 26330.0, 'max_gross': 30480.0, 'volume': 76.0},
            '45': {'max_payload': 24200.0, 'max_gross': 29000.0, 'volume': 86.0}
        }
        for container in self:
            capacity = capacities.get(container.container_type, 
                                    {'max_payload': 0.0, 'max_gross': 0.0, 'volume': 0.0})
            container.max_weight_kg = capacity['max_payload']
            container.max_gross_weight_kg = capacity['max_gross']
            container.max_volume_m3 = capacity['volume']
    
    # [MÉTODO ACTUALIZADO] Lógica consolidada de volumen dual y merma
    @api.depends(
        'line_ids', 
        'lot_ids.vol_shipment_m3', 
        'lot_ids.volume_purchase_m3',
        'lot_ids.volumen_m3',
        'lot_ids.merma_dimensional_m3'
    )
    def _compute_volume_totals(self):
        for container in self:
            lots = container.lot_ids
            
            # 1. Sumar desde la fuente (Stock.Lot)
            # Usamos getattr/sum con fallback para seguridad
            v_real = sum(getattr(l, 'vol_shipment_m3', 0.0) for l in lots)
            v_nom = sum(getattr(l, 'volume_purchase_m3', 0.0) for l in lots)
            v_merma = sum(getattr(l, 'merma_dimensional_m3', 0.0) for l in lots)
            
            # 2. Lógica de Respaldo (Fallback)
            if v_real == 0 and lots:
                # Si no hay shipment_m3, usamos el campo legacy 'volumen_m3'
                v_real = sum(l.volumen_m3 for l in lots)
            
            if v_nom == 0:
                # Si no hay nominal, asumimos que Nominal = Real
                v_nom = v_real

            # 3. Asignación de valores
            container.total_vol_shipment_m3 = round(v_real, 3)
            container.total_volume_purchase_m3 = round(v_nom, 3)
            container.total_merma_dimensional_m3 = round(v_merma, 3)
            
            # 4. Mapeo al campo estructural (Físico es el que ocupa espacio)
            container.volume_m3 = round(v_real, 3) 
            
            # 5. Cálculo de Desviación
            if v_nom > 0:
                container.volume_variance_pct = ((v_real - v_nom) / v_nom) * 100
            else:
                container.volume_variance_pct = 0.0
    
    @api.depends('lot_ids', 'lot_ids.volumen_mbf')
    def _compute_volume_mbf_from_lots(self):
        for container in self:
            container.volume_mbf = sum(container.lot_ids.mapped('volumen_mbf'))
    
  # 🚀 CORRECCIÓN: Contar paquetes reales (Etiquetas únicas)
    @api.depends('lot_ids', 'lot_ids.ref')
    def _compute_packages_from_lots(self):
        for container in self:
            # Obtenemos todas las etiquetas (ref) ignorando vacíos
            refs = [lot.ref for lot in container.lot_ids if lot.ref]
            
            # Usamos un set para contar solo valores únicos
            # Ejemplo: [83532, D7720, D7720, D7721, D7721, 97760] -> Cuenta 4
            unique_packages = len(set(refs))
            
            # Sumamos lotes que no tengan etiqueta (si los hay) como paquetes individuales
            orphan_lots = len(container.lot_ids) - len(refs)
            
            container.packages = unique_packages + orphan_lots

    # 🚀 MEJORA: Obtener el nombre corto del proveedor para el Excel
    def _get_supplier_nickname(self, partner):
        if not partner:
            return 'S/N'
        # Prioridad 1: Referencia Interna (FATIMA)
        # Prioridad 2: Primeras dos palabras del nombre
        if partner.ref:
            return partner.ref.upper()
        
        name_parts = partner.name.split()
        if len(name_parts) > 1:
            return f"{name_parts[0]} {name_parts[1]}".upper()
        return partner.name[:15].upper()
    @api.depends('lot_ids', 'lot_ids.piezas')
    def _compute_total_pieces_from_lots(self):
        for container in self:
            container.total_pieces = sum(container.lot_ids.mapped('piezas'))
    
    @api.depends('weight_kg', 'tare_weight_kg')
    def _compute_gross_weight(self):
        for container in self:
            container.gross_weight_kg = container.weight_kg + container.tare_weight_kg
    
    @api.depends('volume_m3', 'max_volume_m3', 'weight_kg', 'max_weight_kg')
    def _compute_remaining_capacity(self):
        for container in self:
            container.remaining_volume_m3 = max(0.0, container.max_volume_m3 - container.volume_m3)
            container.remaining_weight_kg = max(0.0, container.max_weight_kg - container.weight_kg)
    
    @api.depends('lot_ids')
    def _compute_lot_count(self):
        for container in self:
            container.lot_count = len(container.lot_ids)

    # ==================== MÉTODOS DE CAPACIDAD Y ESTADO ====================
    
    @api.model
    def _calculate_capacity_metrics(self, current_weight, max_weight, current_vol, max_vol):
        weight_pct = (current_weight / max_weight * 100) if max_weight > 0 else 0.0
        volume_pct = (current_vol / max_vol * 100) if max_vol > 0 else 0.0
        
        fill_pct = max(weight_pct, volume_pct)
        limiting_factor = 'weight' if weight_pct > volume_pct else 'volume'
        
        return {
            'weight_pct': weight_pct,
            'volume_pct': volume_pct,
            'fill_pct': fill_pct,
            'limiting_factor': limiting_factor
        }

    @api.depends('weight_kg', 'max_weight_kg', 'volume_m3', 'max_volume_m3')
    def _compute_fill_percentage(self):
        for container in self:
            metrics = self._calculate_capacity_metrics(
                container.weight_kg, container.max_weight_kg,
                container.volume_m3, container.max_volume_m3
            )
            container.fill_percentage = metrics['fill_pct']
    
    @api.depends('fill_percentage', 'state')
    def _compute_status_color(self):
        for container in self:
            if container.state == 'sealed':
                container.status_color = 4  # Rojo
            elif container.fill_percentage >= 90:
                container.status_color = 3  # Naranja
            elif container.fill_percentage >= 50:
                container.status_color = 2  # Amarillo
            else:
                container.status_color = 1  # Verde
    
    # ==================== MÉTODOS DE ACCIÓN ====================
    
    def action_start_loading(self):
        self.ensure_one()
        self.write({'state': 'loading', 'loading_date': fields.Datetime.now()})
        self.message_post(body=_('🔄 Carga iniciada'))
        return True
    
    def action_complete_loading(self):
        self.ensure_one()
        if not self.lot_ids:
            raise ValidationError(_("No se puede completar la carga sin lotes asignados"))
        
        self.write({'state': 'loaded'})
        self.message_post(
            body=_('✅ Carga completada<br/>📦 Paquetes: %d<br/>🔢 Piezas: %d<br/>📐 Volumen: %.2f m³') %
            (self.packages, self.total_pieces, self.volume_m3)
        )
        return True
    
    def action_assign_lots(self):
        self.ensure_one()
        wizard = self.env['lumber.container.lot.wizard'].create({'container_id': self.id})
        return {
            'name': _('Asignar Lotes a Contenedor'),
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.container.lot.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new'
        }
    
    def action_seal(self):
        """ 🔒 SELLADO SEGURO: Valida integridad física antes de cerrar """
        self.ensure_one()
        errors = []
        
        # 1. Validación de Sello Físico (Naviera)
        if not self.seal_number:
            errors.append("- Debe ingresar el N° de Sello Naviera.")
        # NOTA DE ARQUITECTURA: El Sello SAG no se exige aquí porque burocráticamente 
        # puede llegar hasta una semana después del zarpe.
        
        # 2. Validación de Peso (SOLAS/VGM)
        if self.gross_weight_kg <= 0:
            errors.append("- El peso bruto (VGM) no puede ser 0 kg. Ingrese el Peso Neto de la carga.")
        
        # 3. Validación de Contenido
        if not self.lot_ids and not self.packages:
            errors.append("- El contenedor está vacío (sin paquetes).")

        if errors:
            raise ValidationError(_("⛔ NO SE PUEDE SELLAR EL CONTENEDOR\n\n%s") % "\n".join(errors))

        self.write({'state': 'sealed', 'sealing_date': fields.Datetime.now()})
        
        # Mensaje de trazabilidad dinámico
        sag_info = f" | SAG: {self.sag_seal}" if self.sag_seal else " | SAG: (Pendiente)"
        self.message_post(body=_('🔒 Contenedor sellado físicamente (Naviera: %s%s)') % (self.seal_number, sag_info))
        return True
    
    # ══════════════════════════════════════════════════════════════════════
    # AD-82 / CANON/18 — REBAJA de inventario (salida nativa) y REVERSA
    # ══════════════════════════════════════════════════════════════════════
    REBAJA_ALLOWED_STATES = ('loaded', 'sealed')

    @api.depends('line_ids.rebaja_picking_id', 'line_ids.rebaja_state')
    def _compute_rebaja_return_display(self):
        """Nombres de la salida (OUT) y del retorno físico (IN) validado."""
        for container in self:
            out = container.line_ids.mapped('rebaja_picking_id')
            container.rebaja_origin_picking_names = ', '.join(
                out.mapped('name')) or False
            returns = out.mapped('return_ids').filtered(
                lambda p: p.state == 'done')
            container.rebaja_return_picking_names = ', '.join(
                sorted(returns.mapped('name'))) or False

    def _rebaja_require_group(self, *group_xmlids):
        if not any(self.env.user.has_group(g) for g in group_xmlids):
            raise AccessError(_(
                'No tiene permisos para esta operación. Se requiere uno de: %s.'
            ) % ', '.join(group_xmlids))

    # ══════════════════════════════════════════════════════════════════════
    # P0 (2026-10-03) — Guarda reutilizable del rolleo NORMAL.
    # Un contenedor ya rebajado/embarcado (o con embarque en tránsito,
    # entregado o cancelado) NO puede volver a rollear por la vía normal.
    # El flujo excepcional de reversa + reprogramación conserva su propio
    # camino autorizado y no se modifica aquí.
    # ══════════════════════════════════════════════════════════════════════
    ROLLOVER_ALLOWED_STATES = ('loading', 'loaded', 'sealed')
    ROLLOVER_TERMINAL_SHIPMENT_STATES = (
        'in_transit', 'delivered', 'cancelled')

    def _assert_rollover_eligible(self):
        """Valida, en servidor, que el contenedor pueda rollear (rolle normal).

        Rechaza cuando:
        - el usuario no pertenece a Operaciones/Jefatura/Gerencia;
        - no hay embarque asociado;
        - el embarque está `in_transit`, `delivered` o `cancelled`;
        - hay evidencia persistente de rebaja (estado `rebajado`/`shipped`,
          línea `rebaja_state='rebajado'` o picking de rebaja `done`);
        - el estado del contenedor no es Cargando/Cargado/Sellado.

        No sustituye la guarda de COSTOS DISTRIBUIDOS (B-07) del asistente,
        que sigue aplicándose por separado.
        """
        self.ensure_one()
        if not any(self.env.user.has_group(g) for g in (
                'madenat_lumber_core.group_madenat_operaciones',
                'madenat_lumber_core.group_madenat_jefatura_operaciones',
                'madenat_lumber_core.group_madenat_gerencia')):
            raise AccessError(_(
                'No tiene permisos para realizar el rolleo. Se requiere el '
                'rol de Operaciones, Jefatura de Operaciones o Gerencia.'))

        shipment = self.shipment_id
        if not shipment:
            raise UserError(_(
                'No se puede realizar el rolleo: el contenedor no está '
                'asociado a un embarque.'))

        if shipment.state in self.ROLLOVER_TERMINAL_SHIPMENT_STATES:
            raise UserError(_(
                'No se puede realizar el rolleo: el contenedor pertenece a un '
                'embarque en tránsito, entregado o cancelado. Esta operación '
                'requiere un flujo excepcional de reversa y reprogramación '
                'autorizado.'))

        # Sub-bloque 4A (2026-10-04): bloqueo EXPLÍCITO por excepción B-01
        # (además del bloqueo transitorio por in_transit ya existente).
        if shipment.b01_exception_state in ('open', 'resolved'):
            raise UserError(_(
                'No se puede realizar el rolleo: el embarque tiene una '
                'excepción B-01 (%s). Regularice o cierre la excepción antes '
                'de reprogramar.') % shipment.b01_exception_state)

        rebaja_applied = self.state in ('rebajado', 'shipped') or any(
            line.rebaja_state == 'rebajado'
            or (line.rebaja_picking_id
                and line.rebaja_picking_id.state == 'done')
            for line in self.line_ids)
        if rebaja_applied:
            raise UserError(_(
                'No se puede realizar el rolleo: el contenedor ya tiene una '
                'rebaja física aplicada. Ejecute primero la reversa formal de '
                'rebaja, si está autorizada.'))

        if self.state not in self.ROLLOVER_ALLOWED_STATES:
            raise UserError(_(
                'El rolleo sólo está permitido para contenedores sin rebaja '
                'en estado Cargando, Cargado o Sellado.'))
        return True

    def _rebaja_source_warehouse(self, location):
        warehouse = location.warehouse_id
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search(
                [('view_location_id', 'parent_of', location.id)], limit=1)
        return warehouse

    # ══════════════════════════════════════════════════════════════════════
    # Sub-bloque 4A (2026-10-04) — Regularización B-01 (R1, rebaja extemporánea)
    # Guard de servidor (NO escribe, sin sudo): autoriza la rebaja R1 sólo para
    # Gerencia, sobre un Contenedor pendiente de un Embarque in_transit con
    # B-01 abierta, con motivo y aprobación suficientes y sin bloqueos
    # físicos/financieros. Reutiliza el motor estándar `_rebajar_container`.
    # ══════════════════════════════════════════════════════════════════════
    B01_REGULARIZATION_MIN_REASON = 20

    def _assert_can_regularize_b01_rebaja(self, shipment, reason,
                                          approval_reason=None):
        """Valida (sin escribir) que el Contenedor pueda rebajarse por R1."""
        self.ensure_one()
        if not self.env.user.has_group(
                'madenat_lumber_core.group_madenat_gerencia'):
            raise AccessError(_(
                'La rebaja extemporánea B-01 (R1) sólo puede ejecutarla '
                'Gerencia.'))
        if not shipment:
            raise UserError(_(
                'La regularización B-01 requiere un Embarque.'))
        if shipment.state != 'in_transit':
            raise UserError(_(
                'Sólo se puede regularizar por R1 un Embarque Embarcado '
                '(in_transit). Estado actual: %s.') % shipment.state)
        if shipment.b01_exception_state != 'open':
            raise UserError(_(
                'El Embarque %s no tiene una excepción B-01 ABIERTA (actual: '
                '%s).') % (shipment.name, shipment.b01_exception_state))
        if self.shipment_id != shipment:
            raise UserError(_(
                'El Contenedor %s no pertenece al Embarque %s con B-01 '
                'abierta.') % (self.name, shipment.name))
        if self.state not in self.REBAJA_ALLOWED_STATES:
            raise UserError(_(
                'Sólo se pueden regularizar por R1 Contenedores Cargado o '
                'Sellado (estado actual del Contenedor %s: %s).') % (
                    self.name, self.state))
        if shipment._is_container_rebajado_fisico(self):
            raise UserError(_(
                'El Contenedor %s ya tiene evidencia de rebaja física; no '
                'requiere regularización R1.') % self.name)
        if not self.line_ids:
            raise UserError(_(
                'El Contenedor %s no tiene líneas/lotes consolidados para '
                'rebajar.') % self.name)
        for line in self.line_ids:
            quant = self.env['stock.quant'].search([
                ('lot_id', '=', line.lot_id.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal')], limit=1)
            if not quant:
                raise UserError(_(
                    'El lote %s del Contenedor %s no tiene stock físico '
                    'disponible en bodega interna.') % (
                        line.lot_id.name or line.lot_id.id, self.name))
        if shipment.cost_distribution_state == 'distributed':
            raise UserError(_(
                'No se puede regularizar por R1: los costos del Embarque ya '
                'fueron distribuidos.'))
        consolidations = self.env['lumber.billing.consolidation'].search([
            ('shipment_id', '=', shipment.id), ('state', '!=', 'cancelled')])
        if consolidations.filtered(
                lambda c: c.invoice_id or c.state == 'billed'):
            raise UserError(_(
                'No se puede regularizar por R1: existe una consolidación de '
                'facturación incompatible.'))
        if len((reason or '').strip()) < self.B01_REGULARIZATION_MIN_REASON:
            raise UserError(_(
                'El motivo de la regularización B-01 es obligatorio y debe '
                'tener al menos %d caracteres.'
            ) % self.B01_REGULARIZATION_MIN_REASON)
        if approval_reason is not None and len(
                (approval_reason or '').strip()
        ) < self.B01_REGULARIZATION_MIN_REASON:
            raise UserError(_(
                'La justificación de aprobación de Gerencia es obligatoria y '
                'debe tener al menos %d caracteres.'
            ) % self.B01_REGULARIZATION_MIN_REASON)
        return True

    def _assert_shipment_reassign_allowed(self, new_shipment_id):
        """Bloquea reasignar `shipment_id` si origen o destino está congelado.

        Congelado = Embarque in_transit o con excepción B-01 open/resolved.
        No admite bypass por contexto RPC.
        """
        dest = (self.env['lumber.export.shipment'].browse(new_shipment_id)
                if new_shipment_id else self.env['lumber.export.shipment'])
        for container in self:
            for shipment in (container.shipment_id | dest):
                if shipment and (
                        shipment.state == 'in_transit'
                        or shipment.b01_exception_state in ('open', 'resolved')):
                    raise UserError(_(
                        'No se puede reasignar el Contenedor %s: el Embarque '
                        '%s está Embarcado (in_transit) o tiene una excepción '
                        'B-01 (%s). Esta protección es de servidor y no admite '
                        'excepción.') % (
                            container.name, shipment.name,
                            shipment.b01_exception_state))
        return True

    def action_rebajar(self):
        """B2: rebaja de inventario del contenedor (salida nativa de stock).

        Sub-bloque 4A (2026-10-04): la rebaja estándar post-zarpe con B-01
        ABIERTA queda bloqueada (incluso para Gerencia): la única vía es la
        regularización R1 (`lumber.b01.regularization.wizard`), que controla
        motivo, aprobación de Gerencia y auditoría.
        """
        self.ensure_one()
        self._rebaja_require_group(
            'madenat_lumber_core.group_madenat_operaciones',
            'madenat_lumber_core.group_madenat_jefatura_operaciones',
            'madenat_lumber_core.group_madenat_gerencia')
        shipment = self.shipment_id
        if shipment and shipment.state == 'in_transit' \
                and shipment.b01_exception_state == 'open':
            raise UserError(_(
                'La rebaja estándar no está disponible: el Embarque %s tiene '
                'una excepción B-01 abierta. Use la regularización B-01 (R1) '
                'desde el Embarque (sólo Gerencia).') % shipment.name)
        self._rebajar_container()
        return True

    # ══════════════════════════════════════════════════════════════════════
    # Sub-bloque 4B (2026-10-04) — R2: RETORNO FÍSICO TOTAL / REVERSA ROBUSTA
    # Una reversa sólo actualiza estados logísticos, SV y auditoría DESPUÉS de
    # que exista un retorno físico total validado:
    #   Customers → ubicación interna original, mismo lote y
    #   `stock.move.origin_returned_move_id`, con idempotencia relacional.
    # ══════════════════════════════════════════════════════════════════════
    REBAJA_REVERSE_GROUPS = (
        # R2 (2026-10-05): sólo Gerencia autoriza el retorno físico total.
        'madenat_lumber_core.group_madenat_gerencia',
    )
    REBAJA_REVERSE_MIN_REASON = 20

    def action_reverse_rebaja(self):
        """B5/R2: reversa de la rebaja (retorno físico total + contrapartida SV).

        AD-88 / B-03 / B-06 (2026-10-01): si el embarque ya fue entregado, el
        viaje está cancelado o la excepción B-01 quedó regularizada (`resolved`),
        la reversa exige **override de Gerencia con motivo** (se abre el wizard).
        En caso contrario, revierte directo. La excepción B-01 `open` bloquea la
        reversa por completo (no se reabre en esta entrega).
        """
        self.ensure_one()
        self._rebaja_require_group(*self.REBAJA_REVERSE_GROUPS)
        shipment = self.shipment_id
        if shipment and shipment.b01_exception_state == 'open':
            raise UserError(_(
                'No se puede revertir la rebaja del Contenedor %s: el Embarque '
                '%s tiene una excepción B-01 ABIERTA. Cierre la excepción antes '
                'de revertir la rebaja física.') % (self.name, shipment.name))
        delivered = bool(shipment and shipment.state == 'delivered')
        voyage_cancelled = bool(
            shipment and shipment.voyage_id
            and shipment.voyage_id.state == 'cancel')
        b01_resolved = bool(
            shipment and shipment.b01_exception_state == 'resolved')
        if delivered or voyage_cancelled or b01_resolved:
            if not self.env.user.has_group(
                    'madenat_lumber_core.group_madenat_gerencia'):
                raise UserError(_(
                    'La reversa con %s requiere override de Gerencia con '
                    'motivo.') % (
                    'el embarque entregado' if delivered
                    else 'el viaje cancelado' if voyage_cancelled
                    else 'una excepción B-01 regularizada'))
            return {
                'type': 'ir.actions.act_window',
                'name': _('Reversa con override de Gerencia'),
                'res_model': 'lumber.container.rebaja.reverse.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_container_id': self.id},
            }
        self._reverse_rebaja_container()
        return True

    def _rebaja_planned_lines(self):
        """[(line, lot, qty, source_location, sv_op)] validado para rebajar."""
        self.ensure_one()
        plan = []
        for line in self.line_ids:
            lot = line.lot_id
            sv_op = self.env['madenat.sv.operation']
            if lot.lot_flow_type == 'volume':
                sv_op = self.env['madenat.sv.operation'].search([
                    ('lot_id', '=', lot.id),
                    ('action_type', '=', 'rebaja'),
                    ('state', '=', 'applied'),
                    ('destination_container_id', '=', self.id),
                ], order='id desc', limit=1)
                qty = sv_op.rebaja_volume_m3 if sv_op else 0.0
            else:
                qty = lot.volumen_restante_m3
            if float_compare(qty, 0.0, precision_rounding=0.001) <= 0:
                raise UserError(_(
                    'El lote %s no tiene disponible para rebajar (tipo %s). '
                    'Revise inventario o la asignación SV del contenedor.'
                ) % (lot.name or lot.id, lot.lot_flow_type or 'tarja'))
            quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ], limit=1)
            if not quant:
                raise UserError(_(
                    'El lote %s no tiene stock físico disponible en bodega '
                    'interna.') % (lot.name or lot.id))
            plan.append([line, lot, qty, quant.location_id, sv_op])
        return plan


    def _rebajar_container(self):
        self.ensure_one()
        # Idempotencia (CANON/18 §4.2): ya rebajado => no repetir salida.
        if self.state == 'rebajado':
            return self.line_ids.filtered('rebaja_picking_id')[:1].rebaja_picking_id
        if self.state not in self.REBAJA_ALLOWED_STATES:
            raise UserError(_(
                'Solo se puede rebajar un contenedor consolidado '
                '(Cargado o Sellado). Estado actual: %s.'
            ) % dict(self._fields['state'].selection).get(self.state, self.state))
        if not self.line_ids:
            raise UserError(_(
                'El contenedor no tiene lotes consolidados para rebajar.'))

        customers = self.env.ref('stock.stock_location_customers')
        previous_state = self.state
        plan = self._rebaja_planned_lines()
        source = plan[0][3]
        warehouse = self._rebaja_source_warehouse(source)
        if not warehouse:
            raise UserError(_(
                'No se encontró un almacén para la ubicación %s.'
            ) % source.display_name)

        # UN picking de salida por contenedor, una línea por lote.
        picking = self.env['stock.picking'].create({
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': source.id,
            'location_dest_id': customers.id,
            'origin': _('Rebaja %s') % self.name,
        })
        for line, lot, qty, src, sv_op in plan:
            move = self.env['stock.move'].create({
                'name': _('Rebaja %s') % self.name,
                'product_id': lot.product_id.id,
                'product_uom_qty': qty,
                'product_uom': lot.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': src.id,
                'location_dest_id': customers.id,
            })
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'product_id': lot.product_id.id,
                'lot_id': lot.id,
                'quantity': qty,
                'product_uom_id': lot.product_id.uom_id.id,
                'location_id': src.id,
                'location_dest_id': customers.id,
                'picking_id': picking.id,
            })
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

        now = fields.Datetime.now()
        for line, lot, qty, src, sv_op in plan:
            line.write({
                'rebaja_qty_m3': qty,
                'rebaja_merma_m3': lot.merma_dimensional_m3,
                'rebaja_picking_id': picking.id,
                'rebaja_date': now,
                'rebaja_user_id': self.env.user.id,
                'rebaja_sv_operation_id': sv_op.id if sv_op else False,
                'rebaja_state': 'rebajado',
            })
        self.write({
            'state': 'rebajado',
            'state_before_rebaja': previous_state,
        })
        self.message_post(body=_(
            '📉 <b>Rebaja de inventario</b><br/>Salida: %s<br/>Lotes: %d'
        ) % (picking.name, len(plan)))
        self._rebaja_audit('rebaja', picking)
        return picking


    def _reverse_rebaja_container(self, override_reason=None):
        """R2: retorno físico TOTAL validado y sólo entonces reversa lógica.

        Orquesta, en una única transacción: bloqueo de concurrencia, guard de
        elegibilidad, retorno físico por cada salida `done` (mismo lote y
        cantidad, `origin_returned_move_id`), verificación, reversa SV, estados,
        auditoría (`rebaja_reverse` + `rebaja_return_total`) y chatter. Si algo
        falla, todo se revierte: no se marca `reversed`, no se restaura el
        estado, no se revierte SV ni se registra auditoría de éxito.
        """
        self.ensure_one()
        self._rebaja_require_group(*self.REBAJA_REVERSE_GROUPS)
        # C: protección transaccional ANTES de crear cualquier retorno.
        self._rebaja_reverse_lock()

        # Idempotencia relacional: revertido y con retorno físico total → no-op.
        reversed_lines = self.line_ids.filtered(
            lambda l: l.rebaja_state == 'reversed')
        if self.state != 'rebajado' and reversed_lines:
            if all(self._rebaja_return_total_complete(l.rebaja_picking_id)
                   for l in reversed_lines if l.rebaja_picking_id):
                return self._rebaja_return_result(reversed_lines)

        # A: guard de elegibilidad (bloquea antes de crear retornos).
        self._assert_can_reverse_rebaja_total(override_reason=override_reason)

        lines = self.line_ids.filtered(lambda l: l.rebaja_state == 'rebajado')
        state_before = self.state
        origin_pickings = self.env['stock.picking']
        return_pickings = self.env['stock.picking']
        results = []
        for picking in lines.mapped('rebaja_picking_id'):
            with self.env.cr.savepoint():
                return_picking = self._reverse_rebaja_picking(picking)
                checks = self._assert_rebaja_return_valid(
                    picking, return_picking)
            origin_pickings |= picking
            return_pickings |= return_picking
            results.append((picking, return_picking, checks))

        # Retorno físico total verificado → recién ahora estados/SV/auditoría.
        for line in lines.filtered('rebaja_sv_operation_id'):
            self.env['madenat.sv.operation'].sv_reverse_allocation(
                line.lot_id, container=self,
                reason=_('Reversa de rebaja del contenedor %s.') % self.name)
        lines.write({
            'rebaja_state': 'reversed',
            'rebaja_merma_m3': 0.0,
        })
        new_state = self.state_before_rebaja or 'loaded'
        self.write({'state': new_state})
        self.message_post(body=_(
            '↩️ <b>Retorno físico total de rebaja</b> (%d lote(s)).<br/>'
            'Los lotes regresaron de <b>Clientes</b> a la ubicación interna de '
            'origen con el mismo lote; recién entonces se revirtieron estado, '
            'SV y auditoría.') % len(lines))
        self._rebaja_audit('rebaja_reverse')
        self._rebaja_return_total_audit(
            origin_pickings, return_pickings, results,
            state_before=state_before, state_after=new_state,
            override_reason=override_reason)
        return True

    def _rebaja_return_result(self, reversed_lines):
        """Resultado idempotente (sin nuevas escrituras) de una reversa ya hecha."""
        pickings = reversed_lines.mapped('rebaja_picking_id')
        return {
            'rebaja_state': 'reversed',
            'origin_pickings': pickings.mapped('name'),
            'return_pickings': pickings.mapped('return_ids').filtered(
                lambda p: p.state == 'done').mapped('name'),
        }

    # ══════════════════════════════════════════════════════════════════════
    # R2 — Helpers relacionales de elegibilidad, idempotencia y verificación.
    # ══════════════════════════════════════════════════════════════════════
    def _rebaja_reverse_lock(self):
        """Serializa la reversa física con bloqueo de fila (FOR UPDATE NOWAIT)."""
        self.ensure_one()
        self.flush_recordset()
        try:
            self.env.cr.execute(
                'SELECT id FROM lumber_container WHERE id = %s '
                'FOR UPDATE NOWAIT', (self.id,))
        except LockNotAvailable as error:
            _logger.warning(
                'Conflicto de concurrencia en reversa de rebaja (id %s): %s',
                self.id, error)
            raise UserError(_(
                'La reversa de rebaja del Contenedor %s está siendo procesada '
                'por otra transacción. Intente nuevamente.') % self.name)
        if not self.env.cr.fetchone():
            raise UserError(_(
                'El Contenedor (id %s) ya no existe.') % self.id)
        self.invalidate_recordset(['state', 'state_before_rebaja'])

    def _rebaja_return_moves_of(self, move):
        """Moves de retorno vinculados relacionalmente a `move` (no por texto)."""
        return self.env['stock.move'].search([
            ('origin_returned_move_id', '=', move.id),
        ])

    def _rebaja_move_return_complete(self, move):
        """True si la suma de retornos `done` iguala exactamente la salida."""
        if not move or move.state != 'done':
            return False
        returned = sum(
            m.quantity for m in self._rebaja_return_moves_of(move)
            if m.state == 'done')
        out_qty = move.quantity or move.product_uom_qty
        rounding = move.product_uom.rounding or 0.001
        return float_compare(
            returned, out_qty, precision_rounding=rounding) == 0

    def _rebaja_return_total_complete(self, picking):
        """True si TODOS los moves `done` del OUT tienen retorno total `done`."""
        if not picking or picking.state != 'done':
            return False
        moves = picking.move_ids.filtered(lambda m: m.state == 'done')
        if not moves:
            return False
        return all(self._rebaja_move_return_complete(m) for m in moves)

    def _rebaja_return_pickings_of(self, picking):
        """Pickings de retorno vinculados relacionalmente al OUT."""
        if not picking:
            return self.env['stock.picking']
        moves = picking.move_ids.filtered('returned_move_ids')
        return moves.mapped('returned_move_ids').mapped('picking_id')

    def _assert_reverse_reason(self, reason):
        """Override de Gerencia obligatorio y suficiente (≥ 20 caracteres)."""
        if len((reason or '').strip()) < self.REBAJA_REVERSE_MIN_REASON:
            raise UserError(_(
                'Debe indicar un motivo de reversa de al menos %d caracteres '
                'para autorizar esta operación.'
            ) % self.REBAJA_REVERSE_MIN_REASON)

    def _assert_can_reverse_rebaja_total(self, override_reason=None):
        """Guard de servidor (NO escribe) de la reversa R2 total.

        Bloquea antes de crear cualquier retorno si el contexto no es elegible:
        estado, líneas rebajadas, salidas `done`, retorno total previo, B-01,
        terminalidad, costos/facturación/pagos, consolidaciones y motivo de
        override. No usa texto `origin` como guard primario.
        """
        self.ensure_one()
        if not any(
                self.env.user.has_group(g) for g in self.REBAJA_REVERSE_GROUPS):
            raise AccessError(_(
                'No tiene permisos para revertir la rebaja. Se requiere el rol '
                'de Gerencia.'))
        if self.state != 'rebajado':
            raise UserError(_(
                'Sólo se puede revertir un contenedor rebajado (estado actual: '
                '%s).') % dict(self._fields['state'].selection).get(
                    self.state, self.state))
        lines = self.line_ids.filtered(lambda l: l.rebaja_state == 'rebajado')
        if not lines:
            raise UserError(_('No hay líneas rebajadas para revertir.'))

        # Cada OUT de rebaja debe estar `done`, con moves y lotes válidos.
        for line in lines:
            picking = line.rebaja_picking_id
            if not picking or picking.state != 'done':
                raise UserError(_(
                    'No se puede revertir: la salida de rebaja de la línea del '
                    'lote %s no está validada (estado: %s).') % (
                        line.lot_id.name or line.lot_id.id,
                        picking.state if picking else 'sin picking'))
            moves = picking.move_ids.filtered(lambda m: m.state == 'done')
            if not moves:
                raise UserError(_(
                    'No se puede revertir: la salida %s no tiene movimientos '
                    'validados.') % picking.name)
            if any(not ml.lot_id for ml in moves.move_line_ids):
                raise UserError(_(
                    'No se puede revertir: la salida %s tiene movimientos sin '
                    'lote (trazabilidad incompleta).') % picking.name)
            if not moves.mapped('location_dest_id').filtered(
                    lambda loc: loc.usage == 'customer'):
                raise UserError(_(
                    'No se puede revertir: la salida %s no despacha a Clientes '
                    '(Customers).') % picking.name)
            if self._rebaja_return_total_complete(picking):
                raise UserError(_(
                    'Ya existe un retorno físico total validado para la salida '
                    '%s. No se creará un segundo retorno.') % picking.name)

        shipment = self.shipment_id
        if shipment:
            self._assert_can_reverse_rebaja_context(shipment, override_reason)
            self._assert_can_reverse_rebaja_financial(shipment)
        return True

    def _assert_can_reverse_rebaja_context(self, shipment, override_reason):
        """Gates de B-01 y terminalidad (con override de Gerencia) del R2."""
        # ── B-01 (no se reabre ni se modifica en esta entrega) ─────────────
        if shipment.b01_exception_state == 'open':
            raise UserError(_(
                'No se puede revertir la rebaja: el Embarque %s tiene una '
                'excepción B-01 ABIERTA.') % shipment.name)
        if shipment.b01_exception_state == 'resolved':
            if not self.env.user.has_group(
                    'madenat_lumber_core.group_madenat_gerencia'):
                raise UserError(_(
                    'Revertir una rebaja sobre un Embarque con B-01 '
                    'regularizada sólo puede autorizarlo Gerencia, con motivo.'))
            self._assert_reverse_reason(override_reason)
        # ── Terminalidad (override de Gerencia existente) ──────────────────
        delivered = shipment.state == 'delivered'
        voyage_cancelled = bool(
            shipment.voyage_id and shipment.voyage_id.state == 'cancel')
        if delivered or voyage_cancelled:
            if not self.env.user.has_group(
                    'madenat_lumber_core.group_madenat_gerencia'):
                raise UserError(_(
                    'No se puede revertir la rebaja: %s. Requiere override de '
                    'Gerencia con motivo.') % (
                    'el embarque ya fue entregado' if delivered
                    else 'el viaje está cancelado'))
            self._assert_reverse_reason(override_reason)
            self._guard_deviation(
                'B-03' if delivered else 'B-06',
                _('Reversa de rebaja con %s (override de Gerencia).') % (
                    'embarque entregado' if delivered
                    else 'viaje cancelado'),
                reason=override_reason,
                hard=False,
                extra={'shipment': shipment.name if shipment else False},
            )
        return True

    def _assert_can_reverse_rebaja_financial(self, shipment):
        """Gates financieros (costos/facturación/pagos/consolidaciones) del R2."""
        if shipment.cost_distribution_state == 'distributed':
            raise UserError(_(
                'No se puede revertir la rebaja: los costos del Embarque %s ya '
                'fueron distribuidos.') % shipment.name)
        if 'stock.lot.cost.line' in self.env and shipment.cost_line_ids:
            lot_cost_lines = self.env['stock.lot.cost.line'].search([
                ('source_shipment_cost_line_id', 'in',
                 shipment.cost_line_ids.ids)])
            if lot_cost_lines:
                raise UserError(_(
                    'No se puede revertir la rebaja: existen %d costos atribuibles '
                    'al lote/embarque.') % len(lot_cost_lines))
        invoiced = shipment.cost_line_ids.filtered(
            lambda cl: getattr(cl, 'invoice_id', False)
            or getattr(cl, 'payment_state', 'not_paid')
            not in (False, 'not_paid'))
        if invoiced:
            raise UserError(_(
                'No se puede revertir la rebaja: existen costos con '
                'facturación o pago asociados al Embarque.'))
        if 'lumber.billing.consolidation' in self.env:
            consolidations = self.env['lumber.billing.consolidation'].search([
                ('shipment_id', '=', shipment.id), ('state', '!=', 'cancelled')])
            billed = consolidations.filtered(
                lambda c: c.invoice_id or c.state == 'billed')
            if billed:
                raise UserError(_(
                    'No se puede revertir la rebaja: existe una consolidación de '
                    'facturación incompatible para el Embarque %s.') % shipment.name)
        return True

    def _assert_rebaja_return_valid(self, picking, return_picking):
        """Verifica el retorno físico TOTAL; devuelve el dict de checks.

        Si el retorno no quedó `done`, no cubre la totalidad de cada move o no
        preserva el lote, bloquea (nunca se avanza a estados/SV/auditoría).
        """
        checks = {
            'origin_done': picking.state == 'done',
            'return_done': bool(
                return_picking and return_picking.state == 'done'),
            'quantities_total_match': True,
            'lots_match': True,
            'total_return_complete': False,
            'return_picking': return_picking.name if return_picking else False,
        }
        if not checks['return_done']:
            raise UserError(_(
                'El retorno físico de la salida %s no terminó validado '
                '(estado: %s).') % (
                    picking.name,
                    return_picking.state if return_picking else 'sin retorno'))
        for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
            if not self._rebaja_move_return_complete(move):
                checks['quantities_total_match'] = False
                raise UserError(_(
                    'El retorno físico no cubre la totalidad del movimiento '
                    '%s (producto %s).') % (
                        move.name, move.product_id.display_name))
            ret_moves = self._rebaja_return_moves_of(move).filtered(
                lambda m: m.state == 'done')
            origin_lots = move.move_line_ids.mapped('lot_id')
            ret_lots = ret_moves.move_line_ids.mapped('lot_id')
            if not origin_lots or set(origin_lots.ids) != set(ret_lots.ids):
                checks['lots_match'] = False
                raise UserError(_(
                    'El retorno físico de %s no preserva el lote de origen.'
                ) % move.name)
        checks['total_return_complete'] = self._rebaja_return_total_complete(
            picking)
        if not checks['total_return_complete']:
            raise UserError(_(
                'El retorno físico de la salida %s no quedó total.'
            ) % picking.name)
        return checks

    def _reverse_rebaja_picking(self, picking):
        """Retorno entrante inverso TOTAL (Customers → ubicación interna).

        Idempotente por RELACIÓN (`origin_returned_move_id` / `return_id`), nunca
        por texto. Requiere la salida `done`; si falta, bloquea (nunca `False`).
        """
        if not picking:
            raise UserError(_(
                'No se encontró la salida de rebaja a revertir.'))
        if picking.state != 'done':
            raise UserError(_(
                'No se puede revertir: la salida de rebaja %s no está '
                'validada (estado: %s).') % (picking.name, picking.state))

        # Idempotencia relacional: si el retorno total ya existe, se reutiliza.
        if self._rebaja_return_total_complete(picking):
            existing = self._rebaja_return_pickings_of(picking).filtered(
                lambda p: p.state == 'done')
            return existing[:1]

        return_type = picking.picking_type_id.return_picking_type_id
        if not return_type:
            warehouse = picking.picking_type_id.warehouse_id
            return_type = self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id),
                ('active', '=', True)], limit=1)
        if not return_type:
            raise UserError(_(
                'No existe un tipo de operación de Recepción para revertir.'))

        # Destino = ubicación interna ORIGINAL de cada move (por move, no por
        # cabecera). Cabecera: Customers → ubicación interna de la salida.
        return_picking = self.env['stock.picking'].create({
            'picking_type_id': return_type.id,
            'return_id': picking.id,
            'origin': _('Return of %s') % picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': picking.location_id.id,
        })
        for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
            if self._rebaja_move_return_complete(move):
                continue
            qty = move.quantity or move.product_uom_qty
            return_move = self.env['stock.move'].create({
                'name': _('Return of %s') % move.name,
                'product_id': move.product_id.id,
                'product_uom_qty': qty,
                'product_uom': move.product_uom.id,
                'picking_id': return_picking.id,
                'location_id': move.location_dest_id.id,
                'location_dest_id': move.location_id.id,
                'origin_returned_move_id': move.id,
                # `to_refund=True` no genera efecto contable en este flujo: los
                # movimientos de rebaja no están ligados a factura/SO.
                'to_refund': True,
            })
            for line in move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': return_move.id,
                    'picking_id': return_picking.id,
                    'product_id': line.product_id.id,
                    'lot_id': line.lot_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': move.location_id.id,
                })
        return_picking.action_confirm()
        return_picking.action_assign()
        return_picking.button_validate()
        return_picking.invalidate_recordset()
        if return_picking.state != 'done':
            raise UserError(_(
                'El retorno físico de la salida %s no terminó validado '
                '(estado: %s).') % (picking.name, return_picking.state))
        return return_picking

    def _rebaja_snapshot(self, action_type, picking=False):
        """Snapshot determinista de la rebaja/reversa (convención
        `madenat.audit.log`): mismos datos → mismo hash SHA-256."""
        self.ensure_one()
        payload = {
            'action_type': action_type,
            'container': self.name,
            'container_id': self.id,
            'state': self.state,
            'shipment': self.shipment_id.name or False,
            'shipment_id': self.shipment_id.id or False,
            # AD-82 / Rebaja por Motonave: nave/viaje DERIVADOS del embarque
            # (campos JSON aditivos; no se crean campos en madenat.audit.log).
            'vessel': self.shipment_id.vessel_id.name or False,
            'vessel_id': self.shipment_id.vessel_id.id or False,
            'voyage': self.shipment_id.voyage_id.name or False,
            'voyage_id': self.shipment_id.voyage_id.id or False,
            'picking': picking.name if picking else False,
            'picking_id': picking.id if picking else False,
            'lines': [
                {
                    'line_id': line.id,
                    'lot': line.lot_id.name or False,
                    'lot_id': line.lot_id.id or False,
                    'rebaja_qty_m3': round(line.rebaja_qty_m3 or 0.0, 3),
                    'rebaja_state': line.rebaja_state or False,
                }
                for line in self.line_ids.sorted('id')
            ],
            'user': self.env.user.id,
            'timestamp': fields.Datetime.now().isoformat(),
        }
        return json.dumps(payload, sort_keys=True)

    def _rebaja_audit(self, action_type, picking=False):
        self.ensure_one()
        snapshot = self._rebaja_snapshot(action_type, picking)
        self.env['madenat.audit.log'].sudo().create({
            'action_type': action_type,
            'description': '%s · %s · %s' % (
                action_type, self.name, picking.name if picking else ''),
            'batch_id': ','.join(str(i) for i in self.line_ids.ids),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _rebaja_return_total_snapshot(self, origin_pickings, return_pickings,
                                      results, state_before, state_after,
                                      override_reason=None):
        """Snapshot determinista JSON del retorno físico total (R2).

        Evidencia explícita de la cadena OUT → retorno IN, con la verificación
        y el estado físico resultante. Mismos datos → mismo hash SHA-256.
        """
        self.ensure_one()
        shipment = self.shipment_id
        moves = []
        for picking, _return_picking, _checks in results:
            for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                ret_moves = self._rebaja_return_moves_of(move).filtered(
                    lambda m: m.state == 'done')
                moves.append({
                    'origin_picking': picking.name,
                    'origin_move_id': move.id,
                    'return_move_id': ret_moves[:1].id or False,
                    'return_move_ids': ret_moves.ids,
                    'product': move.product_id.display_name,
                    'product_id': move.product_id.id,
                    'quantity': round(
                        move.quantity or move.product_uom_qty, 3),
                    'lot_id': move.move_line_ids[:1].lot_id.id or False,
                    'origin_returned_move_id': (
                        ret_moves[:1].origin_returned_move_id.id or False),
                })
        rebaja_active_after = bool(
            shipment and shipment._is_container_rebajado_fisico(self))
        payload = {
            'operation': {
                'action_type': 'rebaja_return_total',
                'timestamp': fields.Datetime.now().isoformat(),
                'actor': {'id': self.env.user.id, 'name': self.env.user.name},
                'reason': (override_reason or '').strip() or False,
                'override_reason': (override_reason or '').strip() or False,
            },
            'container': {
                'id': self.id,
                'name': self.name,
                'state_before': state_before,
                'state_after': state_after,
                'shipment': shipment.name or False,
                'shipment_id': shipment.id or False,
                'b01_state': (
                    shipment.b01_exception_state if shipment else False),
            },
            'origin_pickings': [
                {'id': p.id, 'name': p.name}
                for p in origin_pickings.sorted('id')],
            'return_pickings': [
                {'id': p.id, 'name': p.name,
                 'location_id': p.location_id.display_name,
                 'location_dest_id': p.location_dest_id.display_name}
                for p in return_pickings.sorted('id')],
            'moves': moves,
            'checks': {
                'origin_done': all(r[2]['origin_done'] for r in results),
                'return_done': all(r[2]['return_done'] for r in results),
                'quantities_total_match': all(
                    r[2]['quantities_total_match'] for r in results),
                'lots_match': all(r[2]['lots_match'] for r in results),
                'idempotency_status': 'total_return_created',
                'physical_rebaja_active_after': rebaja_active_after,
            },
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _rebaja_return_total_audit(self, origin_pickings, return_pickings,
                                   results, state_before, state_after,
                                   override_reason=None):
        """Registra el evento append-only `rebaja_return_total` (sudo audit.log)."""
        self.ensure_one()
        snapshot = self._rebaja_return_total_snapshot(
            origin_pickings, return_pickings, results,
            state_before, state_after, override_reason)
        batch = ','.join(
            [str(self.id)] + [str(i) for i in self.line_ids.ids])
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'rebaja_return_total',
            'description': _(
                'Retorno físico total de rebaja · %s · salida %s → retorno %s '
                '(Customers → interno).') % (
                    self.name,
                    ', '.join(origin_pickings.mapped('name')) or '—',
                    ', '.join(return_pickings.mapped('name')) or '—'),
            'batch_id': batch,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def action_view_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lotes - %s') % self.name,
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.lot_ids.ids)],
            'context': {'create': False}
        }
    
    def action_manage_rollover(self):
        self.ensure_one()
        # P0 (2026-10-03): guarda reutilizable antes de abrir el asistente.
        self._assert_rollover_eligible()
        if not self.shipment_id:
            raise UserError(_("Este contenedor no está asignado a ningún embarque."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Gestionar Rolleo de Contenedor'),
            'res_model': 'lumber.container.rollover.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_container_id': self.id, 'default_old_seal': self.seal_number or ''}
        }
  # 1. 🔄 TRIGGER AL CREAR UN CONTENEDOR
    @api.model_create_multi
    def create(self, vals_list):
        containers = super(LumberContainer, self).create(vals_list)
        for container in containers:
            if container.shipment_id:
                # Forzamos al embarque a recalcular sus totales inmediatamente
                container.shipment_id._compute_totals()
        return containers

    # 2. 🔄 TRIGGER AL MODIFICAR UN CONTENEDOR (Lo que pide tu Wizard)
    def write(self, vals):
        # Sub-bloque 4A (2026-10-04): no se puede reasignar `shipment_id` si el
        # Embarque de origen o destino está Embarcado (in_transit) o tiene una
        # excepción B-01 open/resolved. Sin bypass por contexto RPC.
        if 'shipment_id' in vals:
            self._assert_shipment_reassign_allowed(vals.get('shipment_id'))
        res = super(LumberContainer, self).write(vals)
        
        # Lista de campos "sensibles" que afectan al embarque
        trigger_fields = [
            'lot_ids',           # Si cambian los lotes
            'packages',          # Si cambia cant. paquetes
            'gross_weight_kg',   # Si cambia el peso
            'volume_m3',         # Si cambia el volumen
            'shipment_id',       # Si se mueve a otro embarque
            'state'              # Si se sella o abre
        ]
        
        # Si alguno de los campos modificados está en la lista...
        if any(key in vals for key in trigger_fields):
            for container in self:
                if container.shipment_id:
                    # A. Recalcular Totales (M3, Kg, Paquetes)
                    container.shipment_id._compute_totals()
                    
                    # B. Recalcular Costos (Si cambió el volumen, el costo unitario cambia)
                    container.shipment_id._compute_cost_totals()
                    
                    # C. Opcional: Escribir una "señal de vida" para refrescar vistas
                    # (Esto ayuda si la interfaz se queda pegada)
                    container.shipment_id.flush_recordset()

        return res
    # ---------------------------------------------------------
    # CORRECCIÓN 2: EXPORTACIÓN EXCEL (Con Apodo y Agrupación)
    # ---------------------------------------------------------
    def action_export_packing_list_xlsx(self):
            self.ensure_one()
            if not self.lot_ids:
                raise UserError(_("No hay lotes asignados."))

            import io
            import base64
            try:
                import xlsxwriter
            except ImportError:
                raise UserError(_("Instale xlsxwriter."))

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet(f'TARJA_{self.name}')

            # --- ESTILOS (Calibri 11pt; títulos/headers/totales en bold) ---
            title_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            header_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            data_str_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00'})
            data_num_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '#,##0.00'})
            data_num_3_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '#,##0.000'})
            data_int_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '0'})
            footer_fmt = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})

            # --- CONFIGURACIÓN COLUMNAS ---
            for offset in [0, 14]:
                sheet.set_column(offset, offset, 15)
                sheet.set_column(offset+1, offset+1, 20)
                sheet.set_column(offset+2, offset+2, 15)
                sheet.set_column(offset+3, offset+3, 15)
                sheet.set_column(offset+4, offset+4, 6)
                sheet.set_column(offset+5, offset+5, 10)
                sheet.set_column(offset+6, offset+8, 8)
                sheet.set_column(offset+9, offset+9, 6)
                sheet.set_column(offset+10, offset+10, 9)
                sheet.set_column(offset+11, offset+12, 10)
            sheet.set_column(13, 13, 2)

            # --- CABECERAS ---
            # A4: 'MN' muestra nave/viaje reales; 'RESERVA' muestra el booking
            # del embarque (antes ambas usaban shipment.name).
            if self.shipment_id:
                vessel = self.shipment_id.vessel_id.name or ''
                voyage = (self.shipment_id.voyage_id.voyage_reference
                          if self.shipment_id.voyage_id else '')
                nave = ' / '.join(p for p in (vessel, voyage) if p) or 'S/N'
                reserva = self.shipment_id.booking_reference or 'S/N'
            else:
                nave = 'S/N'
                reserva = 'S/N'
            
            for offset in [0, 14]:
                sheet.merge_range(0, offset, 0, offset+9, f'MN {nave}', title_fmt)
                sheet.write(0, offset+10, 'TARJA', header_fmt)
                sheet.write(0, offset+11, 1, header_fmt)
                sheet.merge_range(1, offset+1, 1, offset+2, 'Contenedor', header_fmt)
                sheet.write(1, offset+3, 'Sello', header_fmt)
                sheet.write(1, offset+4, 'Peso', header_fmt)
                sheet.write(1, offset+5, 'Tara', header_fmt)
                sheet.merge_range(1, offset+6, 1, offset+7, 'RESERVA', header_fmt)
                sheet.merge_range(2, offset+1, 2, offset+2, self.name or '', header_fmt)
                sheet.write(2, offset+3, self.seal_number or '', header_fmt)
                sheet.write(2, offset+4, self.gross_weight_kg or 0, data_int_fmt)
                sheet.write(2, offset+5, self.tare_weight_kg or 0, data_int_fmt)
                sheet.merge_range(2, offset+6, 2, offset+7, reserva, header_fmt)
                cols = ['Embarcador', 'Producto', 'Planta', 'Etiqueta', 'Pqts', 'Subprod.', 'Espesor', 'Ancho', 'Largo', 'Pzas', 'M3', 'Guia', 'Fecha']
                for i, c in enumerate(cols):
                    sheet.write(3, offset+i, c, header_fmt)

            # --- AGRUPACIÓN ---
            sorted_lots = sorted(self.lot_ids, key=lambda x: x.ref or 'zzzz')
            from itertools import groupby
            grouped_lots = groupby(sorted_lots, key=lambda x: x.ref or 'S/N')

            row = 4
            tot_pqts, tot_m3_emb, tot_m3_nom = 0, 0.0, 0.0

            for ref, group in grouped_lots:
                lots = list(group)
                span = len(lots)
                tot_pqts += 1

                for i, lot in enumerate(lots):
                    # 🚀 FIX APLICADO AQUÍ
                    prov = lot.supplier_id
                    if not prov and getattr(lot, 'parent_lot_id', False): 
                        prov = lot.parent_lot_id.supplier_id
                    if not prov and getattr(lot, 'reception_id', False): 
                        prov = getattr(lot.reception_id, 'supplier_id', False) or getattr(lot.reception_id, 'partner_id', False)
                    if not prov and getattr(lot, 'guia_processing_id', False):
                        prov = getattr(lot.guia_processing_id, 'partner_id', False)
                    
                    if prov:
                        planta = prov.ref.upper() if prov.ref else " ".join(prov.name.split()[:2]).upper()
                    else:
                        planta = 'S/N'

                    embarcador = self.env.company.name or 'MADENAT'
                    prod = lot.product_id.name
                    sub = lot.subproducto_id.name or 'RIP S2S'
                    guia = lot.guia_number or ''
                    fecha = lot.create_date.strftime('%d-%b') if lot.create_date else ''

                    # Tabla Izq
                    off = 0
                    sheet.write(row+i, off+0, embarcador, data_str_fmt)
                    sheet.write(row+i, off+1, prod, data_str_fmt)
                    sheet.write(row+i, off+2, planta, data_str_fmt)
                    sheet.write(row+i, off+5, sub, data_str_fmt)
                    sheet.write(row+i, off+6, lot.espesor_inch_frac or '', data_str_fmt)
                    sheet.write(row+i, off+7, lot.ancho_inch_frac or '', data_str_fmt)
                    sheet.write(row+i, off+8, lot.largo_m or 0, data_num_3_fmt)
                    sheet.write(row+i, off+9, lot.piezas or 0, data_int_fmt)
                    sheet.write(row+i, off+10, lot.vol_shipment_m3 or 0, data_num_3_fmt)
                    sheet.write(row+i, off+11, guia, data_str_fmt)
                    sheet.write(row+i, off+12, fecha, data_str_fmt)

                    # Tabla Der
                    off = 14
                    v_nom = getattr(lot, 'volumen_m3', 0.0)
                    sheet.write(row+i, off+0, embarcador, data_str_fmt)
                    sheet.write(row+i, off+1, prod, data_str_fmt)
                    sheet.write(row+i, off+2, planta, data_str_fmt)
                    sheet.write(row+i, off+5, sub, data_str_fmt)
                    sheet.write(row+i, off+6, lot.espesor_mm or 0, data_num_fmt)
                    sheet.write(row+i, off+7, lot.ancho_mm or 0, data_num_fmt)
                    sheet.write(row+i, off+8, lot.largo_m or 0, data_num_3_fmt)
                    sheet.write(row+i, off+9, lot.piezas or 0, data_int_fmt)
                    sheet.write(row+i, off+10, v_nom, data_num_3_fmt)
                    sheet.write(row+i, off+11, guia, data_str_fmt)
                    sheet.write(row+i, off+12, fecha, data_str_fmt)

                    tot_m3_emb = round(tot_m3_emb + round(lot.vol_shipment_m3 or 0.0, 3), 3)
                    tot_m3_nom = round(tot_m3_nom + round(v_nom or 0.0, 3), 3)

                for off in [0, 14]:
                    if span > 1:
                        sheet.merge_range(row, off+3, row+span-1, off+3, ref, data_str_fmt)
                        sheet.merge_range(row, off+4, row+span-1, off+4, 1, data_int_fmt)
                    else:
                        sheet.write(row, off+3, ref, data_str_fmt)
                        sheet.write(row, off+4, 1, data_int_fmt)
                row += span

            for off in [0, 14]:
                sheet.write(row, off+4, tot_pqts, footer_fmt)
            sheet.write(row, 10, round(tot_m3_emb, 3), footer_fmt)
            sheet.write(row, 24, round(tot_m3_nom, 3), footer_fmt)

            # Bloque 7.3: Línea de Merma Dimensional si existe diferencia
            merma_tot = self.total_merma_dimensional_m3 or round(tot_m3_nom - tot_m3_emb, 3)
            if merma_tot > 0.0005:
                row_m = row + 1
                for off in [0, 14]:
                    sheet.merge_range(row_m, off, row_m, off+3, 'MERMA DIMENSIONAL', footer_fmt)
                sheet.write(row_m, 10, round(merma_tot, 3), footer_fmt)
                sheet.write(row_m, 24, round(merma_tot, 3), footer_fmt)

            workbook.close()
            output.seek(0)
            attachment = self.env['ir.attachment'].create({
                'name': f'Tarja_{self.name}.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(output.read()),
                'res_model': self._name, 'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
            return {'type': 'ir.actions.act_url', 'url': f'/web/content/{attachment.id}?download=true', 'target': 'self'}
        
    # ==================== VALIDACIONES Y CONSTRAINTS ====================
    
    @api.constrains('weight_kg', 'max_weight_kg')
    def _check_weight_limit(self):
        for container in self:
            if container.weight_kg > container.max_weight_kg:
                raise ValidationError(_("⚠️ Peso de carga excede la capacidad máxima."))

    @api.constrains('gross_weight_kg', 'max_gross_weight_kg', 'state')
    def _check_gross_weight_limit(self):
        for container in self:
            if container.state == 'sealed' and container.gross_weight_kg > container.max_gross_weight_kg:
                raise ValidationError(_("🚨 VIOLACIÓN SOLAS: VGM excede el peso bruto máximo permitido."))

    @api.constrains('volume_m3', 'max_volume_m3')
    def _check_volume_limit(self):
        for container in self:
            # Solo advertencia suave, no bloqueante (a veces se sobrecarga visualmente)
            if container.volume_m3 > container.max_volume_m3:
                 pass # Se permite, pero el semáforo avisará

    @api.constrains('name')
    def _check_unique_container(self):
        for container in self:
            if container.name:
                existing = self.search([('name', '=', container.name), ('id', '!=', container.id)], limit=1)
                if existing:
                    raise ValidationError(_("⚠️ Ya existe un contenedor con número %s") % container.name)

    @api.constrains('shipment_id')
    def _check_financial_integrity_on_move(self):
        for container in self:
            if not container._origin.shipment_id:
                continue
            old = container._origin.shipment_id
            new = container.shipment_id
            if old == new: continue
            
            # Verificar si hay costos distribuidos
            costs = self.env['stock.lot.cost.line'].search_count([
                ('lot_id', 'in', container.lot_ids.ids),
                ('source_shipment_cost_line_id.shipment_id', '=', old.id)
            ])
            if costs > 0:
                raise ValidationError(_("⛔ BLOQUEO: No puede mover el contenedor porque ya tiene costos distribuidos."))

    @api.constrains('lot_ids')
    def _check_lot_duplication(self):
        """ 
        🛡️ BLINDAJE NIVEL 4: Unicidad de Lote
        Evita que un mismo paquete esté en dos contenedores activos al mismo tiempo.
        """
        for container in self:
            if not container.lot_ids: 
                continue
            
            # Buscamos si ALGUNO de mis lotes ya está en OTRO contenedor que no haya zarpado
            domain = [
                ('id', '!=', container.id),                # Que no sea yo mismo
                ('lot_ids', 'in', container.lot_ids.ids),  # Que tenga mis lotes
                ('state', '!=', 'shipped')                 # Que esté activo (no enviado)
            ]
            
            # Usamos sudo() por si un usuario tiene permisos limitados de vista pero debemos validar igual
            others = self.env['lumber.container'].sudo().search(domain)
            
            if others:
                # Mejora Profesional: Decir exactamente QUÉ lote y DÓNDE está duplicado
                duplicated_lots = container.lot_ids & others.mapped('lot_ids')
                lot_names = ", ".join(duplicated_lots.mapped('name'))
                container_names = ", ".join(others.mapped('name'))
                
                raise ValidationError(_(
                    "⛔ INTEGRIDAD VIOLADA: Duplicidad de Lotes\n\n"
                    "Los siguientes lotes ya están asignados al contenedor %s:\n"
                    "👉 %s\n\n"
                    "No puede asignar el mismo paquete a dos contenedores activos."
                ) % (container_names, lot_names))

    # =======================================================
    # 🧹 LIMPIEZA ATÓMICA AL BORRAR (Odoo 18 Ready)
    # =======================================================
    def unlink(self):
            """
            🛡️ DESCONSOLIDACIÓN AUTOMÁTICA AL BORRAR
            Este método se activa cuando se usa el botón de eliminar (basurero rojo).
            """
            for container in self:
                # Buscamos los lotes vinculados antes de que el contenedor desaparezca
                lotes = container.lot_ids
                if lotes:
                    _logger.info(f"🔄 Limpieza de seguridad: Liberando {len(lotes)} lotes del contenedor {container.name}")
                    # Importante: Escribimos directamente en el recordset de lotes
                    lotes.write({
                        'container_id': False,
                        'estado_trazabilidad': 'procesado'
                    })
            return super(LumberContainer, self).unlink()