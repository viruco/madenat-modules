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
from odoo.exceptions import UserError, ValidationError
import logging
import io          # <-- Para el Excel
import base64      # <-- Para el Excel

_logger = logging.getLogger(__name__)

class LumberContainer(models.Model):
    _name = 'lumber.container'
    _description = 'Contenedor de Exportación'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
        'Vol. Físico Real (Facturable)', 
        compute='_compute_volume_totals', 
        store=True,
        digits=(16, 3),
        help="Volumen geométrico real. Base para la FACTURACIÓN de exportación y cálculo de espacio."
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
        'Volumen m³ (Total)',
        compute='_compute_volume_totals', 
        store=True,
        digits=(16, 3),
        help="Volumen total ocupado (Alias de Vol. Físico)."
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
    def action_remove_lot_granular(self):
            """ ✂️ OPERACIÓN DE REVERSIÓN TOTAL (Granular) """
            self.ensure_one() # 'self' es el registro del lote (stock.lot)
            
            # Obtenemos el contenedor desde el contexto
            container_id = self.env.context.get('active_id')
            container = self.env['lumber.container'].browse(container_id)
            
            if not container:
                return True

            # 1. 💰 REVERSIÓN FINANCIERA (madenat_lumber_costing)
            # Si el lote tiene costos logísticos, los limpiamos porque ya no pertenece al viaje
            if hasattr(self, 'logistic_cost_usd'):
                self.write({
                    'logistic_cost_usd': 0.0,
                    # Si tienes otros campos de costo del viaje, agrégalos aquí
                })

            # 2. 🚮 DESVINCULACIÓN FÍSICA
            # Quitamos el lote de la relación con el contenedor
            container.write({
                'lot_ids': [(3, self.id)] 
            })

            # 3. 🔄 RECALCULAR EMBARQUE
            # Actualizamos los totales de m3 y kilos del padre inmediatamente
            if container.shipment_id:
                container.shipment_id._compute_totals()
                
            return True
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
            """
            for container in self:
                # 1. Identificar el estado actual en la DB vs el estado deseado
                current_lots_in_db = container.line_ids.mapped('lot_id')
                target_lots_from_wizard = container.lot_ids
                
                # 2. LOTES AGREGADOS: Marcar dueño, crear línea Y cambiar estado
                lots_to_add = target_lots_from_wizard - current_lots_in_db
                for lot in lots_to_add:
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
                    lots_to_remove.write({
                        'container_id': False,
                        'estado_trazabilidad': 'en_patio' # 👈 Liberación automática
                    })
                    lines_to_delete = container.line_ids.filtered(lambda l: l.lot_id in lots_to_remove)
                    lines_to_delete.unlink()

    def action_open_rollover_wizard(self):
            """ 🔌 PUENTE SEGURO: Abre el wizard de rollover sin errores de XMLID """
            self.ensure_one()
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
    
    # [MÉTODO ACTUALIZADO] Lógica consolidada de volumen dual
    @api.depends(
        'line_ids', 
        'lot_ids.vol_shipment_m3', 
        'lot_ids.volume_purchase_m3',
        'lot_ids.volumen_m3' # Dependencia legacy por seguridad
    )
    def _compute_volume_totals(self):
        for container in self:
            lots = container.lot_ids
            
            # 1. Sumar desde la fuente (Stock.Lot)
            # Usamos getattr/sum con fallback para seguridad
            v_real = sum(getattr(l, 'vol_shipment_m3', 0.0) for l in lots)
            v_nom = sum(getattr(l, 'volume_purchase_m3', 0.0) for l in lots)
            
            # 2. Lógica de Respaldo (Fallback)
            if v_real == 0 and lots:
                # Si no hay shipment_m3, usamos el campo legacy 'volumen_m3'
                v_real = sum(l.volumen_m3 for l in lots)
            
            if v_nom == 0:
                # Si no hay nominal, asumimos que Nominal = Real
                v_nom = v_real

            # 3. Asignación de valores
            container.total_vol_shipment_m3 = v_real
            container.total_volume_purchase_m3 = v_nom
            
            # 4. Mapeo al campo estructural (Físico es el que ocupa espacio)
            container.volume_m3 = v_real 
            
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

            # --- ESTILOS (Arial 10pt, sin negrita) ---
            title_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            header_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            data_str_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00'})
            data_num_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '#,##0.00'})
            data_num_3_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '#,##0.000'})
            data_int_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'num_format': '0'})
            footer_fmt = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})

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
            nave = self.shipment_id.name if self.shipment_id else 'S/N'
            reserva = self.shipment_id.name if self.shipment_id else 'S/N'
            
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

                    tot_m3_emb += (lot.vol_shipment_m3 or 0)
                    tot_m3_nom += v_nom

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
            sheet.write(row, 10, tot_m3_emb, footer_fmt)
            sheet.write(row, 24, tot_m3_nom, footer_fmt)

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