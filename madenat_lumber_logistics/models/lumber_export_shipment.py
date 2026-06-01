# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import io
import base64
from itertools import groupby
# 🚀 SOPORTE PARA EXCEL PROFESIONAL
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None
_logger = logging.getLogger(__name__)

class LumberExportShipment(models.Model):
    _name = 'lumber.export.shipment'
    _description = 'Embarque de Exportación de Madera' 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
# ==============================================================================
# 🛡️ CONSTITUCIÓN TÉCNICA DE VOLÚMENES - MÓDULO LOGÍSTICA
# ------------------------------------------------------------------------------
# En este contexto (Exportación), las verdades se definen así:
#
# 1. VOLUMEN FÍSICO (Stock Real): Se mapea al campo NOMINAL (total_volume_purchase_m3).
#    Es lo que Odoo descuenta de los racks y lo que afecta el valor de inventario.
#
# 2. VOLUMEN DE EMBARQUE (Exportación): Se mapea al campo REAL (volume_m3).
#    Es el metraje geométrico neto que se declara en el Manifiesto y BL.
# ==============================================================================
    # === CONFIGURACIÓN Y REGLAS ===
    shipping_rule_id = fields.Many2one(
        'lumber.shipping.rule',
        string='Regla de Cubicación',
        required=False,
        default=lambda self: self.env.ref('madenat_lumber_logistics.rule_usa_scant', raise_if_not_found=False) or \
                             self.env['lumber.shipping.rule'].search([], limit=1)
    )
  
    # === MONEDA Y COSTOS (ARREGLO OWL ERROR) ===
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    total_shipment_costs_usd = fields.Monetary(
        string='Costos Totales Embarque (USD)', 
        compute='_compute_cost_totals', 
        store=True, 
        currency_field='currency_id'
    )
    
    total_cost_per_m3 = fields.Monetary(
        string='Costo por m³ (USD)', 
        compute='_compute_cost_totals', 
        store=True, 
        currency_field='currency_id'
    )
    
    cost_line_ids = fields.One2many(
        'lumber.shipment.cost.line', 
        'shipment_id', 
        string='Líneas de Costo'
    )
    
    cost_distribution_state = fields.Selection(
        [('pending','Pendiente'),('distributed','Distribuido')], 
        default='pending', 
        string='Estado Distribución'
    )

    
# =========================================================
    # 🛡️ PARTE 1: EL CANDADO DE BASE DE DATOS (SQL)
    # =========================================================
    # Garantiza que no existan dos embarques con el mismo número.
    # El campo name se genera automáticamente por secuencia (EMB00001...).
    # Esta constraint es la última línea de defensa ante duplicados manuales.
    _sql_constraints = [
        ('name_uniq', 
         'unique(name)', 
         '¡Error! Ya existe un embarque con este número. Verifique la secuencia.')
    ]

    # =========================================================
    # 🛡️ PARTE 2: EL FILTRO INTELIGENTE (Para evitar el OwlError)
    # =========================================================
    # Este es el código que arregla tu error "Cannot read properties of null".
    # Odoo a veces intenta agregar un contenedor que YA está en la lista.
    # Este código revisa la lista antes de guardar y borra los duplicados.
    def write(self, vals):
        # ¿Están intentando modificar la lista de contenedores?
        if 'container_ids' in vals:
            clean_cmds = []
            
            # Recorremos las instrucciones que vienen de la interfaz/wizard
            for cmd in vals['container_ids']:
                # El comando 4 significa "Vincular registro existente"
                # cmd[1] es el ID del contenedor
                if cmd[0] == 4 and cmd[1] in self.container_ids.ids:
                    # SI EL CONTENEDOR YA ESTÁ EN EL EMBARQUE...
                    # ¡IGNORAMOS ESTE COMANDO! Así evitamos el duplicado visual.
                    continue 
                
                # Si es nuevo, lo dejamos pasar
                clean_cmds.append(cmd)
            
            # Reemplazamos la lista sucia por la lista limpia
            vals['container_ids'] = clean_cmds

        # Dejamos que Odoo continúe con su trabajo normal
        return super(LumberExportShipment, self).write(vals)
    
    # === DATOS GENERALES ===
    name = fields.Char('Número Embarque', required=False, default='/', tracking=True)
    bl_number = fields.Char('N° Bill of Lading', tracking=True)
    booking_reference = fields.Char('N° Booking/Reserva', tracking=True)
    vessel_id = fields.Many2one(
        'shipping.vessel', 
        string='Motonave (Barco)',
        tracking=True,
        index=True,
        help="Nave física asignada. Puede cambiarse manualmente."
    )
    # === RUTA Y LOGÍSTICA (Nombres Claros) ===
    
    # Cambiamos el string de 'Viaje' a algo más operativo
    voyage_id = fields.Many2one(
        'shipping.voyage', 
        string='N° Viaje (Referencia)', 
        tracking=True,
        help="Código del trayecto asignado por la naviera (ej: 402E)"
    )
    
    port_loading = fields.Char('Puerto de Carga', tracking=True)
    port_discharge = fields.Char('Puerto de Descarga', tracking=True)
    port_destination = fields.Char('Destino Final', tracking=True)
    estimated_departure = fields.Datetime('ETD - Fecha Zarpe', tracking=True)
    actual_departure = fields.Datetime('Fecha Real Zarpe', tracking=True)
    estimated_arrival = fields.Datetime('ETA - Fecha Llegada', tracking=True)

    customer_id = fields.Many2one('res.partner', 'Cliente/Consignatario', tracking=True)
    container_ids = fields.One2many('lumber.container', 'shipment_id', 'Contenedores')
    shipment_line_ids = fields.One2many('lumber.shipment.line', 'shipment_id', string='Líneas de Auditoría')
    document_ids = fields.One2many('lumber.shipment.document', 'shipment_id', string='Documentos')
    
    # === TOTALES CALCULADOS (Actualizados) ===
    container_count = fields.Integer('Total Contenedores', compute='_compute_totals', store=True)
    
    total_volume_m3 = fields.Float('Volumen de Embarque (m³)', compute='_compute_totals', store=True, digits=(16,3))
    
    # ✅ NUEVO: Total Nominal para Análisis
    total_nominal_volume_m3 = fields.Float(
        'Volumen Físico (m³)', 
        compute='_compute_totals', 
        store=True, 
        digits=(16,3),
        help="Suma del volumen físico real de todos los contenedores."
    )

    # 🟢 INSERTO 1: Definimos el campo de MBF para el resumen de la Motonave
    total_volume_mbf = fields.Float(
        'Volumen MBF Total', 
        compute='_compute_totals', 
        store=True, 
        digits=(16,3),
        help="Suma del volumen comercial (MBF) de todos los contenedores."
    )
    
    total_weight_kg = fields.Float('Peso Total Kg', compute='_compute_totals', store=True, digits=(16,1))
    total_packages = fields.Integer('Total Paquetes', compute='_compute_totals', store=True)
    lot_count = fields.Integer('Total Lotes', compute='_compute_lot_totals', store=True)

    state = fields.Selection([
        ('draft','Borrador'),
        ('confirmed','Confirmado'),
        ('in_transit','Embarcado'), # ✏️ CAMBIO VISUAL AQUÍ
        ('delivered','Entregado'),
        ('cancelled','Cancelado')
    ], default='draft', tracking=True)
    
    notes = fields.Text('Observaciones')

    # === CHECKLIST DOCUMENTAL ===
    booking_confirmed = fields.Boolean('Booking Confirmado', tracking=True)
    booking_date = fields.Date('Fecha Booking', tracking=True)

    vgm_submitted = fields.Boolean('VGM Enviado', tracking=True)
    vgm_date = fields.Date('Fecha Envío VGM', tracking=True)
    vgm_total_weight = fields.Float('Peso Total VGM (kg)', digits=(16,1))

    bl_received = fields.Boolean('BL Recibido', tracking=True)
    bl_date = fields.Date('Fecha BL', tracking=True)

    customs_cleared = fields.Boolean('Aduana Despachada', tracking=True)
    customs_date = fields.Date('Fecha Despacho Aduana', tracking=True)
    customs_reference = fields.Char('Referencia Aduanera', tracking=True)

    invoice_issued = fields.Boolean('Factura Emitida', tracking=True)
    invoice_date = fields.Date('Fecha Facturación', tracking=True)
    invoice_number = fields.Char('N° Factura', tracking=True)

    container_seals = fields.Text('Sellos de Contenedores')
   
    document_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('partial', 'Parcial'),
        ('complete', 'Completo'),
    ], string='Estado Documental', compute='_compute_document_status', store=True)

    document_completion = fields.Float(
        string='Progreso Doc.', 
        compute='_compute_document_status', 
        store=True
    )

    picking_count = fields.Integer(compute='_compute_picking_count')

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])

    def action_view_picking(self):
        """ 🚚 CABLE: Salta directo al albarán de salida """
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.env['stock.picking'].search([('origin', '=', self.name)])
        if len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', 'in', pickings.ids)]
        return action

    # 🟢 INSERTO 2: Lógica del Smart Button para el "Detalle por Motonave"
    def action_view_shipment_lots(self):
        """ Abre la vista de todos los lotes asignados a este embarque, permitiendo el filtrado y Pivot """
        self.ensure_one()
        # Buscamos todos los lotes que pertenezcan a los contenedores de este embarque
        lot_ids = self.container_ids.mapped('lot_ids').ids
        return {
            'name': f'Tarjas del Embarque {self.name}',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,pivot,form', # Pivot incluido para análisis
            'res_model': 'stock.lot',
            'domain': [('id', 'in', lot_ids)],
            'context': {
                'create': False, # No se crean lotes desde aquí
                'group_by': ['product_id', 'supplier_id'] # Agrupación solicitada por el PM
            }
        }

    # === MÉTODOS COMPUTADOS ===
# 🔌 AUTOMATIZACIÓN: Si eligen viaje, sugerimos barco (pero no obligamos)
    @api.onchange('voyage_id')
    def _onchange_voyage(self):
        if self.voyage_id and self.voyage_id.vessel_id:

            self.vessel_id = self.voyage_id.vessel_id

    # Ubicación: ./madenat_lumber_logistics/models/lumber_export_shipment.py

    # ✅ Campo para el análisis de eficiencia del PM
    yield_variance_m3 = fields.Float(
        'Diferencia de Volumen (m³)', 
        compute='_compute_yield_analysis',
        store=True,
        help="Diferencia entre volumen nominal (compra) y físico (embarque)"
    )
    
    yield_efficiency_pct = fields.Float(
        'Eficiencia de Cubicación (%)',
        compute='_compute_yield_analysis',
        store=True,
        help="Porcentaje de aprovechamiento del volumen"
    )

    def action_print_packing_list(self):
        """ 
        📄 Imprime el Packing List Consolidado.
        CORRECCIÓN: Pasamos los contenedores del embarque, no el embarque mismo.
        """
        self.ensure_one()
        
        # 1. Validamos que existan contenedores
        if not self.container_ids:
            raise UserError("⚠️ No se puede imprimir: El embarque no tiene contenedores vinculados.")

        # 2. Identificamos la acción del reporte
        report_action = 'madenat_lumber_logistics.action_report_lumber_container_packing_list'
        
        # 🚀 EL CAMBIO CLAVE:
        # En lugar de (self), pasamos (self.container_ids). 
        # Así Odoo recibirá la lista de contenedores reales y el MissingError desaparecerá.
        return self.env.ref(report_action).report_action(self.container_ids)
    # ==============================================================================
    # 🚀 REGLA DE ORO DE EXPORTACIÓN (CORREGIDA)
    # ------------------------------------------------------------------------------
    # total_nominal_volume_m3: 'Volumen Físico de Compra'. 
    #    Es el INPUT. Lo que sacamos del inventario (Verdad de Stock).
    #
    # total_volume_m3: 'Volumen Físico de Embarque'. 
    #    Es el OUTPUT. Lo que entra a la nave (Verdad de Exportación).
    # ==============================================================================

    @api.depends('total_volume_m3', 'total_nominal_volume_m3')
    def _compute_yield_analysis(self):
        for rec in self:
            # La varianza es lo que "perdemos" o se ajusta al embarcar
            rec.yield_variance_m3 = rec.total_volume_m3 - rec.total_nominal_volume_m3
            
            if rec.total_nominal_volume_m3 > 0:
                # Yield = (Embarque / Compra) * 100
                rec.yield_efficiency_pct = (rec.total_volume_m3 / rec.total_nominal_volume_m3) * 100
            else:
                rec.yield_efficiency_pct = 0.0
    
    # ✅ MODIFICADO: Suma ambos volúmenes
    @api.depends('container_ids', 'container_ids.volume_m3', 'container_ids.total_volume_purchase_m3', 
                 'container_ids.gross_weight_kg', 'container_ids.tare_weight_kg', 'container_ids.packages',
                 'container_ids.volume_mbf') # <-- Agregado dependencia MBF
    def _compute_totals(self):
        for rec in self:
            rec.container_count = len(rec.container_ids)
            rec.total_volume_m3 = sum(rec.container_ids.mapped('volume_m3'))
            rec.total_nominal_volume_m3 = sum(rec.container_ids.mapped('total_volume_purchase_m3'))
            
            # 🟢 INSERTO 3: Sumamos el MBF de todos los contenedores para el Dashboard
            rec.total_volume_mbf = sum(rec.container_ids.mapped('volume_mbf'))
            
            # 🔌 CABLE RECONECTADO: Usamos gross_weight_kg que es el que tiene el dato
            rec.total_weight_kg = sum(rec.container_ids.mapped('gross_weight_kg'))
            rec.total_packages = sum(rec.container_ids.mapped('packages'))
            
            # ⚡ AUTOMATIZACIÓN: Cálculo de VGM (Peso Carga + Tara de todos los contenedores)
            total_tara = sum(rec.container_ids.mapped('tare_weight_kg'))
            rec.vgm_total_weight = rec.total_weight_kg + total_tara

    @api.depends('container_ids.lot_ids')
    def _compute_lot_totals(self):
        for rec in self:
            rec.lot_count = len(rec.container_ids.mapped('lot_ids'))

    @api.depends('cost_line_ids.amount_usd', 'total_volume_m3')
    def _compute_cost_totals(self):
        for rec in self:
            rec.total_shipment_costs_usd = sum(rec.cost_line_ids.mapped('amount_usd'))
            rec.total_cost_per_m3 = (rec.total_shipment_costs_usd / rec.total_volume_m3) if rec.total_volume_m3 else 0.0

    @api.depends('booking_confirmed','vgm_submitted','bl_received','customs_cleared','invoice_issued')
    def _compute_document_completion(self):
        for rec in self:
            total = 5
            done = sum([
                rec.booking_confirmed,
                rec.vgm_submitted,
                rec.bl_received,
                rec.customs_cleared,
                rec.invoice_issued
            ])
            rec.document_completion = (done/total)*100

    @api.depends('document_completion')
    def _compute_document_status(self):
        for rec in self:
            if rec.document_completion >= 100:
                rec.document_status = 'complete'
            elif rec.document_completion >= 50:
                rec.document_status = 'partial'
            else:
                rec.document_status = 'pending'

    @api.constrains('estimated_departure','estimated_arrival')
    def _check_dates(self):
        for rec in self:
            if rec.estimated_departure and rec.estimated_arrival and rec.estimated_arrival <= rec.estimated_departure:
                raise ValidationError(_("La fecha ETA debe ser posterior al ETD"))

    # === ACCIONES DE FLUJO ===

    def action_confirm(self):
        """ ✅ CONFIRMACIÓN: Valida datos mínimos logísticos """
        self.ensure_one()
        if not self.container_ids:
            raise ValidationError(_("⛔ No se puede confirmar un embarque sin contenedores."))
        
        if not self.booking_reference:
            raise ValidationError(_("⛔ Falta el N° de Booking/Reserva de la naviera."))
            
        if not self.vessel_id:
             raise ValidationError(_("⛔ Debe asignar una Motonave antes de confirmar."))

        self.write({'state': 'confirmed'})
        self.message_post(body=_("✅ <b>Embarque Confirmado:</b> Listo para iniciar carga."))

    def action_set_in_transit(self):
        """ 
        🚀 ZARPE SEGURO (Blindaje Logístico)
        1. Valida que todos los contenedores estén 'sealed'.
        2. Genera el albarán de salida.
        3. Pasa contenedores a estado 'shipped'.
        """
        self.ensure_one()
        
        # 1. 🛡️ VALIDACIÓN DE SEGURIDAD CORREGIDA (Alineada al Negocio)
        # Prohíbe zarpar si el contenedor está vacío ('empty') o a medio cargar ('loading').
        # PERMITE zarpar si está terminado ('loaded' = consolidado) o si ya le pusieron sello ('sealed').
        invalid_containers = self.container_ids.filtered(lambda c: c.state in ['empty', 'loading'])
        if invalid_containers:
            names = "\n- ".join(invalid_containers.mapped('name'))
            raise ValidationError(_(
                "⛔ ACCIÓN DENEGADA: Carga Incompleta\n\n"
                "No se puede rematar la nave porque hay contenedores Vacíos o en proceso de Carga.\n"
                "Debe marcar la carga como 'Completada' (Consolidado) en los siguientes contenedores:\n\n- %s"
            ) % names)

        # 2. 📉 REBAJE DE STOCK (Tu lógica original)
        self._action_reduce_stock()

        # 3. 🔄 SINCRONIZACIÓN DE ESTADOS (Padre -> Hijos)
        # Al zarpar, los contenedores viajan con el barco -> Estado 'shipped'
        self.container_ids.write({'state': 'shipped'})

        # 4. 📝 CAMBIO DE ESTADO EMBARQUE
        self.write({
            'state': 'in_transit', 
            'actual_departure': fields.Datetime.now()
        })
        
        # Log en el chatter para auditoría
        self.message_post(body=_("🚢 <b>Zarpe Confirmado:</b> La nave ha sido rematada. Stock rebajado y contenedores en tránsito."))
        self._compute_yield_analysis() # Forzamos el cálculo del rendimiento final
        self.message_post(body=f"📊 Rendimiento Final de Nave: {self.yield_efficiency_pct}%")
        return True
        
    def _action_reduce_stock(self):
            """ 🔌 RECONEXIÓN (Multi-Puerto): Valida el stock automáticamente buscando la ubicación física real """
            lots = self.container_ids.mapped('lot_ids')
            if not lots:
                raise UserError(_("No hay lotes asignados para rebajar stock."))

            # 🟢 INSERTO QUIRÚRGICO 1: Buscamos dónde están físicamente guardados los lotes hoy
            quants = self.env['stock.quant'].search([
                ('lot_id', 'in', lots.ids),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal')
            ])
            
            # Agrupamos los lotes según su puerto/bodega real
            lots_by_location = {}
            for lot in lots:
                lot_quant = quants.filtered(lambda q: q.lot_id == lot)[:1]
                if not lot_quant:
                    # 🛡️ Protección mejorada: Si alguien sacó el lote a mano, avisamos antes de que Odoo explote
                    raise UserError(_("El lote %s no tiene stock físico disponible en ninguna bodega interna.") % lot.name)
                
                loc = lot_quant.location_id
                if loc not in lots_by_location:
                    lots_by_location[loc] = self.env['stock.lot']
                lots_by_location[loc] |= lot

            pickings = self.env['stock.picking']

            # 🟢 INSERTO QUIRÚRGICO 2: Iteramos sobre cada bodega real encontrada y aplicamos SU código original
            for source_location, loc_lots in lots_by_location.items():
                
                # Buscamos el Almacén que es dueño de esta ubicación específica
                warehouse = source_location.warehouse_id or self.env['stock.warehouse'].search([('view_location_id', 'parent_of', source_location.id)], limit=1)
                
                # 🛡️ Su validación de seguridad original:
                if not warehouse:
                    raise UserError(_("No se encontró un almacén configurado para la ubicación %s.") % source_location.display_name)

                # ==============================================================================
                # A PARTIR DE AQUÍ ES EXACTAMENTE SU CÓDIGO (Solo cambiamos warehouse.lot_stock_id.id por source_location.id)
                # ==============================================================================
                picking = self.env['stock.picking'].create({
                    'picking_type_id': warehouse.out_type_id.id,
                    'location_id': source_location.id, # ✅ Adaptado al puerto real
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    'origin': self.name,
                })

                for lot in loc_lots: # Iteramos solo los lotes de este puerto
                    move = self.env['stock.move'].create({
                        'name': f"Salida {self.name}",
                        'product_id': lot.product_id.id,
                        'product_uom_qty': 1,
                        'product_uom': lot.product_id.uom_id.id,
                        'picking_id': picking.id,
                        'location_id': source_location.id, # ✅ Adaptado
                        'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    })
                    # Odoo 18: Movemos el lote directamente
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': lot.product_id.id,
                        'lot_id': lot.id,
                        'quantity': 1, # 'quantity' reemplaza a 'qty_done' en v18
                        'product_uom_id': lot.product_id.uom_id.id,
                        'location_id': source_location.id, # ✅ Adaptado
                        'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                        'picking_id': picking.id,
                    })

                picking.action_confirm()
                picking.action_assign()
                picking.button_validate() # 🚀 AQUÍ ESTÁ LA AUTOMATIZACIÓN REAL
                pickings |= picking

            return pickings
            
    def action_deliver(self):
        if self.state!='in_transit':
            raise ValidationError(_("Solo un embarque en tránsito puede entregarse"))
        self.write({'state':'delivered'})
        self.message_post(body=_("Embarque entregado"))

    def action_distribute_costs(self):
        """
        🚀 DISTRIBUCIÓN AVANZADA DE COSTOS (Versión 3.1 Soporte Dual)
        """
        self.ensure_one()
        
        # 1. Validaciones
        if not self.cost_line_ids:
            raise ValidationError(_("No hay líneas de costo para distribuir"))
        
        lots = self.container_ids.mapped('lot_ids')
        if not lots:
            raise ValidationError(_("No hay lotes en los contenedores del embarque"))
            
        # ✅ CAMBIO: Usamos volumen físico (shipment) o legacy si no existe
        # Esto asegura que distribuimos sobre el espacio real ocupado (lógica flete)
        total_vol = sum(lots.mapped(lambda l: l.vol_shipment_m3 or l.volumen_m3)) or 1.0
        total_weight = sum(lots.mapped('weight_kg')) or 1.0
        lot_count = len(lots) or 1
        
        # 2. Limpieza de costos previos
        previous_costs = self.env['stock.lot.cost.line'].search([
            ('source_shipment_cost_line_id', 'in', self.cost_line_ids.ids)
        ])
        
        if previous_costs:
            _logger.info(f"♻️ Revirtiendo {len(previous_costs)} líneas de costo previas...")
            sql_revert = """
                UPDATE stock_lot 
                SET logistic_cost_usd = GREATEST(0, logistic_cost_usd - sub.amount)
                FROM (
                    SELECT lot_id, SUM(amount_usd) as amount 
                    FROM stock_lot_cost_line 
                    WHERE id IN %s 
                    GROUP BY lot_id
                ) AS sub
                WHERE stock_lot.id = sub.lot_id
            """
            self.env.cr.execute(sql_revert, (tuple(previous_costs.ids),))
            previous_costs.unlink()
            
        # 3. Preparación de Datos
        vals_list = []
        lot_updates = {}
        count_distributed_costs = 0
        
        for cost_line in self.cost_line_ids:
            amount = cost_line.amount_usd
            method = cost_line.distribution_method or 'volume'
            
            factor = 0.0
            if method == 'volume':
                if total_vol <= 0: raise UserError(_("Volumen total es 0, imposible distribuir"))
                factor = amount / total_vol
            elif method == 'weight':
                if total_weight <= 0: raise UserError(_("Peso total es 0, imposible distribuir"))
                factor = amount / total_weight
            elif method == 'equal':
                factor = amount / lot_count
            
            for lot in lots:
                allocated_amount = 0.0
                if method == 'volume':
                    # ✅ CAMBIO: Usamos el volumen físico específico del lote
                    v_lote = lot.vol_shipment_m3 or lot.volumen_m3
                    allocated_amount = v_lote * factor
                elif method == 'weight':
                    allocated_amount = lot.weight_kg * factor
                elif method == 'equal':
                    allocated_amount = factor
                
                if allocated_amount < 0.01: continue
                    
                vals_list.append({
                    'lot_id': lot.id,
                    'cost_type': 'logistic',
                    'amount_usd': allocated_amount,
                    'name': f"{cost_line.cost_type}: {cost_line.description or 'Distribuido'}",
                    'source_shipment_cost_line_id': cost_line.id,
                    'date': fields.Date.today(),
                    'partner_id': cost_line.partner_id.id if hasattr(cost_line, 'partner_id') and cost_line.partner_id else False,
                })
                lot_updates[lot.id] = lot_updates.get(lot.id, 0.0) + allocated_amount
                
            count_distributed_costs += 1

        # 4. Ejecución (SQL Bulk Insert para velocidad)
        if vals_list:
            _logger.info(f"🚀 Insertando {len(vals_list)} líneas de costo...")
            self.env['stock.lot.cost.line'].create(vals_list)
            
            _logger.info(f"🚀 Actualizando campo legacy en {len(lot_updates)} lotes...")
            update_values = [(lot_id, amount) for lot_id, amount in lot_updates.items()]
            query = """
                UPDATE stock_lot AS t
                SET logistic_cost_usd = t.logistic_cost_usd + c.amount
                FROM (VALUES %s) AS c(id, amount) 
                WHERE c.id = t.id
            """
            from psycopg2.extras import execute_values
            execute_values(self.env.cr, query, update_values)

        # 5. Finalizar
        self.write({'cost_distribution_state': 'distributed'})
        
        self.message_post(body=_(
            "✅ <b>Distribución de Costos Finalizada</b><br/>"
            "• Costos procesados: %d<br/>"
            "• Líneas generadas: %d"
        ) % (count_distributed_costs, len(vals_list)))
        
        return True

    @api.constrains('container_ids')
    def _check_containers(self):
        for rec in self:
            names = rec.container_ids.mapped('name')
            if len(names) != len(set(names)):
                raise ValidationError(_("Contenedores duplicados"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name','/')=='/':
                vals['name'] = self.env['ir.sequence'].next_by_code('lumber.export.shipment') or '/'
        return super().create(vals_list)
    
    def action_export_shipment_xlsx(self):
        """ 
        🚀 EXPORTACIÓN CONSOLIDADA PROFESIONAL (ESTILO DUAL TABLE)
        Replica la estructura del contenedor individual, pero iterando para todos
        los contenedores del embarque en una sola hoja continua.
        """
        if not xlsxwriter:
            raise UserError(_("La librería xlsxwriter no está instalada."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(f'CONSOLIDADO_{self.name}')

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
            sheet.set_column(offset, offset, 15)     # Embarcador
            sheet.set_column(offset+1, offset+1, 20) # Producto
            sheet.set_column(offset+2, offset+2, 15) # Planta
            sheet.set_column(offset+3, offset+3, 15) # Etiqueta
            sheet.set_column(offset+4, offset+4, 6)  # Pqts
            sheet.set_column(offset+5, offset+5, 10) # Subprod
            sheet.set_column(offset+6, offset+8, 8)  # Medidas
            sheet.set_column(offset+9, offset+9, 6)  # Pzas
            sheet.set_column(offset+10, offset+10, 9) # M3
            sheet.set_column(offset+11, offset+12, 10) # Guía/Fecha
        sheet.set_column(13, 13, 2) # Separador

        row = 0

        # --- ITERACIÓN POR CONTENEDORES ---
        for container in self.container_ids:
            
            # Datos de Cabecera por Contenedor
            # Prioridad: 1. Nombre del Barco Real, 2. Nombre del Embarque
            nombre_barco = self.vessel_id.name if self.vessel_id else False
            nave = nombre_barco or self.name or 'S/N'
            reserva = self.booking_reference or 'S/N'
            
            for offset in [0, 14]:
                # Título Principal
                sheet.merge_range(row, offset, row, offset+9, f'MN {nave}', title_fmt)
                sheet.write(row, offset+10, 'TARJA', header_fmt)
                sheet.write(row, offset+11, 1, header_fmt)
                
                # Fila 2: Etiquetas
                sheet.merge_range(row+1, offset+1, row+1, offset+2, 'Contenedor', header_fmt)
                sheet.write(row+1, offset+3, 'Sello', header_fmt)
                sheet.write(row+1, offset+4, 'Peso', header_fmt)
                sheet.write(row+1, offset+5, 'Tara', header_fmt)
                sheet.merge_range(row+1, offset+6, row+1, offset+7, 'RESERVA', header_fmt)
                
                # Fila 3: Datos Contenedor
                sheet.merge_range(row+2, offset+1, row+2, offset+2, container.name or '', header_fmt)
                sheet.write(row+2, offset+3, container.seal_number or '', header_fmt)
                sheet.write(row+2, offset+4, container.gross_weight_kg or 0, data_int_fmt)
                sheet.write(row+2, offset+5, container.tare_weight_kg or 0, data_int_fmt)
                sheet.merge_range(row+2, offset+6, row+2, offset+7, reserva, header_fmt)
                
                # Fila 4: Columnas Tabla
                cols = ['Embarcador', 'Producto', 'Planta', 'Etiqueta', 'Pqts', 'Subprod.', 'Espesor', 'Ancho', 'Largo', 'Pzas', 'M3', 'Guia', 'Fecha']
                for i, c in enumerate(cols):
                    sheet.write(row+3, offset+i, c, header_fmt)

            # --- AGRUPACIÓN Y DATOS ---
            # Ordenamos por etiqueta para agrupar paquetes iguales
            sorted_lots = sorted(container.lot_ids, key=lambda x: x.ref or 'zzzz')
            grouped_lots = groupby(sorted_lots, key=lambda x: x.ref or 'S/N')

            data_row = row + 4
            tot_pqts, tot_m3_emb, tot_m3_nom = 0, 0.0, 0.0

            for ref, group in grouped_lots:
                lots = list(group)
                span = len(lots)
                tot_pqts += 1 # Contamos 1 paquete por grupo de etiquetas iguales

                for i, lot in enumerate(lots):
                    # --- Lógica de Apodo / Planta ---
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

                    # TABLA IZQUIERDA (Volumen Embarque)
                    off = 0
                    sheet.write(data_row+i, off+0, embarcador, data_str_fmt)
                    sheet.write(data_row+i, off+1, prod, data_str_fmt)
                    sheet.write(data_row+i, off+2, planta, data_str_fmt)
                    sheet.write(data_row+i, off+5, sub, data_str_fmt)
                    sheet.write(data_row+i, off+6, lot.espesor_inch_frac or '', data_str_fmt)
                    sheet.write(data_row+i, off+7, lot.ancho_inch_frac or '', data_str_fmt)
                    sheet.write(data_row+i, off+8, lot.largo_m or 0, data_num_3_fmt)
                    sheet.write(data_row+i, off+9, lot.piezas or 0, data_int_fmt)
                    sheet.write(data_row+i, off+10, lot.vol_shipment_m3 or 0, data_num_3_fmt)
                    sheet.write(data_row+i, off+11, guia, data_str_fmt)
                    sheet.write(data_row+i, off+12, fecha, data_str_fmt)

                    # TABLA DERECHA (Volumen Nominal/Compra)
                    off = 14
                    v_nom = getattr(lot, 'volumen_m3', 0.0)
                    sheet.write(data_row+i, off+0, embarcador, data_str_fmt)
                    sheet.write(data_row+i, off+1, prod, data_str_fmt)
                    sheet.write(data_row+i, off+2, planta, data_str_fmt)
                    sheet.write(data_row+i, off+5, sub, data_str_fmt)
                    sheet.write(data_row+i, off+6, lot.espesor_mm or 0, data_num_fmt)
                    sheet.write(data_row+i, off+7, lot.ancho_mm or 0, data_num_fmt)
                    sheet.write(data_row+i, off+8, lot.largo_m or 0, data_num_3_fmt)
                    sheet.write(data_row+i, off+9, lot.piezas or 0, data_int_fmt)
                    sheet.write(data_row+i, off+10, v_nom, data_num_3_fmt)
                    sheet.write(data_row+i, off+11, guia, data_str_fmt)
                    sheet.write(data_row+i, off+12, fecha, data_str_fmt)

                    tot_m3_emb += (lot.vol_shipment_m3 or 0)
                    tot_m3_nom += v_nom

                # Fusión de Celdas para Etiqueta y Paquete (Merge)
                for off in [0, 14]:
                    if span > 1:
                        sheet.merge_range(data_row, off+3, data_row+span-1, off+3, ref, data_str_fmt)
                        sheet.merge_range(data_row, off+4, data_row+span-1, off+4, 1, data_int_fmt)
                    else:
                        sheet.write(data_row, off+3, ref, data_str_fmt)
                        sheet.write(data_row, off+4, 1, data_int_fmt)
                
                data_row += span

            # --- TOTALES POR CONTENEDOR ---
            for off in [0, 14]:
                sheet.write(data_row, off+4, tot_pqts, footer_fmt)
            sheet.write(data_row, 10, tot_m3_emb, footer_fmt)
            sheet.write(data_row, 24, tot_m3_nom, footer_fmt)

            # Salto para el siguiente contenedor
            row = data_row + 3 

        workbook.close()
        output.seek(0)
        
        attachment = self.env['ir.attachment'].create({
            'name': f'Tarja_Consolidada_{self.name}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    def action_draft(self):
            """ 
            🔄 RESET MAESTRO (Stock + Finanzas + Estados)
            """
            self.ensure_one()
            
            # ====================================================================
            # 1. 📦 LIMPIEZA DE STOCK (Blindada contra Albaranes validados)
            # ====================================================================
            pickings = self.env['stock.picking'].search([
                ('origin', '=', self.name),
                ('state', '!=', 'cancel') # 🚀 BLINDAJE: Atrapamos también los 'done'
            ])
            
            for picking in pickings:
                # Si el albarán ya salió de la bodega, frenamos el proceso
                if picking.state == 'done':
                    from odoo.exceptions import UserError # Aseguramos la importación local
                    raise UserError(_(
                        "⛔ ERROR DE STOCK: El Albarán %s ya fue validado.\n"
                        "Debe realizar un 'Return' manual antes de resetear el embarque."
                    ) % picking.name)
                
                # Si no está validado, lo cancelamos con seguridad
                picking.action_cancel()

            # ====================================================================
            # 2. 💰 LIMPIEZA FINANCIERA (madenat_lumber_costing)
            # ====================================================================
            # Al volver a borrador, el costo logístico del viaje se anula en los lotes
            all_lots = self.container_ids.mapped('lot_ids')
            if all_lots:
                # Lo ponemos en 0.0 porque el prorrateo actual ya no es válido
                all_lots.write({'logistic_cost_usd': 0.0})

            # ====================================================================
            # 3. 🔄 RESET DE ESTADOS (Contenedores y Embarque)
            # ====================================================================
            self.container_ids.write({'state': 'loading'})
            self.write({
                'state': 'draft',
                'actual_departure': False,
            })
            
            # ====================================================================
            # 4. 📝 LOG Y REFRESCO DE INTERFAZ
            # ====================================================================
            self.message_post(body=_("🔄 <b>Reset Administrativo:</b> Se cancelaron movimientos de stock y se limpiaron costos logísticos."))
            
            # Retornamos el reload para que el usuario vea el cambio al instante
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
class LumberShipmentCostLine(models.Model):

    _name = 'lumber.shipment.cost.line'
    _description = 'Línea de Costo de Embarque'

    # === CAMPOS CLAVE ===
    shipment_id = fields.Many2one('lumber.export.shipment', 'Embarque', required=False, ondelete='cascade')
    
    # NUEVO CAMPO MONEDA (Relacionado al embarque)
    currency_id = fields.Many2one(
        related='shipment_id.currency_id', 
        store=True, 
        string='Moneda',
        readonly=True
    )
    
    # CAMPO MONETARIO UNIFICADO (Sin duplicados Float)
    amount_usd = fields.Monetary(
        string='Monto (USD)',
        required=False,
        currency_field='currency_id',
    )

    cost_type = fields.Selection([
        ('freight','Flete Internacional'),
        ('inland_freight','Flete Interno'),
        ('port_charges','Gastos Portuarios'),
        ('customs','Gastos de Aduana'),
        ('insurance','Seguro'),
        ('documentation','Documentación'),
        ('inspection','Inspección'),
        ('handling','Manipulación'),
        ('storage','Almacenaje'),
        ('other','Otros')
    ], default='other', string='Tipo de Costo')
    
    description = fields.Char('Descripción', required=False)
    
    distribution_method = fields.Selection([
        ('volume','Por Volumen'),
        ('weight','Por Peso'),
        ('packages','Por Paquetes'),
        ('equal','Igual')
    ], default='volume', string='Método')

class StockLot(models.Model):
    _inherit = 'stock.lot'

    # 1. Definimos el campo base (Many2one)
    container_id = fields.Many2one(
        'lumber.container',
        string='Contenedor Actual',
        index=True,
        tracking=True,
        help="Si este campo tiene valor, el lote no aparecerá en el buscador de otros contenedores."
    )

    # 2. Definimos el campo relacionado
    export_shipment_id = fields.Many2one(
        'lumber.export.shipment', 
        related='container_id.shipment_id', 
        string='Embarque Actual', 
        store=True,
        index=True
    )
    def action_traceability_360(self):
        """ 🚀 BOTÓN QUIRÚRGICO: Reporte rápido en el Chatter """
        self.ensure_one()
        msg = f"🔍 <b>Trazabilidad Etiqueta: {self.ref or self.name}</b><br/>"
        msg += f"• Origen: {self.reception_id.name if hasattr(self, 'reception_id') and self.reception_id else 'Sin registro'}<br/>"
        if self.export_shipment_id:
            msg += f"• 🚢 <b>Embarcada en: {self.export_shipment_id.name}</b>"
        else:
            msg += "• Status: 🏭 En Inventario"
        return self.message_post(body=msg)
    
    def action_remove_lot_granular(self):
        """
        Acción llamada desde el botón 'papelera' en la vista de lista del contenedor.
        Quita el lote del contenedor sin borrar el lote.
        """
        for lot in self:
            lot.container_id = False # Desvincula el lote del contenedor
        return True