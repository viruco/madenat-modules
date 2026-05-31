# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LumberCostDistribution(models.Model):
    _name = 'lumber.cost.distribution'
    _description = 'Expediente de Liquidación de Costos (Landed Costs)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === 1. CABECERA Y ESTADO ===
    name = fields.Char(string='Folio de Expediente', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador (Staging)'),
        ('applied', 'Liquidado (En Inventario)'),
        ('cancelled', 'Anulado/Revertido')
    ], string='Estado', default='draft', tracking=True)
    
    date = fields.Date(string="Fecha Expediente", default=fields.Date.context_today, required=True, tracking=True)
    ref = fields.Char(string="Referencia Operativa", required=True, tracking=True, help="Ej: Nave MSC ELENOIRE / Booking FA543R")
    partner_id = fields.Many2one('res.partner', string="Proveedor Principal (Opcional)")

    # === 2. ALCANCE LOGÍSTICO ===
    target_model = fields.Selection([
        ('booking', 'Reserva/BL (Booking)'),
        ('container', 'Contenedor Específico'),
        ('reception', 'Guía de Recepción'),
        ('purchase', 'Orden de Compra'),
        ('manual', 'Selección Manual')
    ], string="Origen de Datos", default='booking', required=True)

    booking_id = fields.Many2one('lumber.export.shipment', string="Embarque / Booking")
    
    # NUEVO: Almacena los contenedores reales del embarque para el prorrateo exacto
    container_ids = fields.Many2many('lumber.container', string="Contenedores Reales", readonly=True)
    container_id = fields.Many2one('lumber.container', string="Buscar Contenedor")
    
    reception_id = fields.Many2one('madenat.guia.processing', string="Guía de Recepción")
    purchase_id = fields.Many2one('purchase.order', string="Orden de Compra")
    
    lot_ids = fields.Many2many('stock.lot', string="Lotes Detectados")
    
    # === 3. MATRIZ FINANCIERA Y TRAZABILIDAD DUAL ===
    cost_line_ids = fields.One2many('lumber.cost.distribution.line', 'distribution_id', string="Documentos de Gasto")
    
    # Auditoría Dual Confirmada en BD
    total_volumen_fisico = fields.Float(string="Total Físico (m³)", compute="_compute_previews", store=True)
    total_volumen_export = fields.Float(string="Total Exportación (m³)", compute="_compute_previews", store=True)
    amount_total_usd = fields.Float(string="Total a Inyectar (USD)", compute="_compute_previews", store=True)
    
    # Auditoría de Paquetes vs Etiquetas lógicas
    package_count = fields.Integer(string="N° Paquetes Físicos", compute="_compute_previews", store=True)
    lot_count = fields.Integer(string="N° Etiquetas", compute="_compute_previews", store=True)
    
    currency_id = fields.Many2one('res.currency', string="Moneda Base", default=lambda self: self.env.ref('base.USD', raise_if_not_found=False))

    # === 4. HISTORIAL Y COSTOS BASE ===
    generated_line_ids = fields.One2many('stock.lot.cost.line', 'distribution_id', string='Historial Inyectado', readonly=True)
    existing_cost_line_ids = fields.Many2many('stock.lot.cost.line', compute='_compute_existing_costs', string="Costos Base Ya Aplicados")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                # Secuencia profesional asignada
                vals['name'] = self.env['ir.sequence'].next_by_code('lumber.cost.distribution') or 'CD-ERR'
        return super().create(vals_list)

    @api.depends('lot_ids', 'cost_line_ids.amount_usd')
    def _compute_previews(self):
        """ Precisión absoluta mapeada a la realidad de la BD Odoo """
        for r in self:
            # volumen_m3 = Físico Real (El Mayor)
            r.total_volumen_fisico = sum((l.volumen_m3 or 0.0) for l in r.lot_ids)
            # vol_shipment_m3 = Exportación (El Menor, Reglas de Cristhian)
            r.total_volumen_export = sum((l.vol_shipment_m3 or 0.0) for l in r.lot_ids)
            
            r.amount_total_usd = sum(r.cost_line_ids.mapped('amount_usd'))
            r.lot_count = len(r.lot_ids)
            r.package_count = len(set(r.lot_ids.mapped('ref'))) if r.lot_ids else 0

    @api.depends('lot_ids')
    def _compute_existing_costs(self):
        """ Busca en la BD los costos previos (ej. Secado/Cepillado) de estos lotes """
        for r in self:
            if r.lot_ids:
                r.existing_cost_line_ids = self.env['stock.lot.cost.line'].search([('lot_id', 'in', r.lot_ids.ids)])
            else:
                r.existing_cost_line_ids = False

    @api.onchange('target_model', 'booking_id', 'container_id', 'reception_id', 'purchase_id')
    def _onchange_target(self):
        """ 
        Búsqueda estricta, mapeo logístico y limpieza de basura residual.
        Se encarga de localizar los lotes correctos según el criterio de operación seleccionado,
        y filtra registros fantasma (con volumen cero o sin referencia) para proteger el prorrateo financiero.
        """
        # 1. Inicializamos recordsets vacíos para evitar errores de variable no definida
        lots = self.env['stock.lot']
        found_containers = self.env['lumber.container']

        # 2. ÁRBOL DE DECISIÓN SEGÚN EL MODELO OBJETIVO SELECCIONADO
        if self.target_model == 'booking' and self.booking_id:
            # 🛡️ CORRECCIÓN ARQUITECTÓNICA: El modelo padre es lumber.export.shipment.
            # Se busca la relación por 'shipment_id' para garantizar que recupere los contenedores.
            found_containers = self.env['lumber.container'].search([('shipment_id', '=', self.booking_id.id)])
            lots = found_containers.mapped('lot_ids')
            
        elif self.target_model == 'container' and self.container_id:
            found_containers = self.container_id
            lots = self.container_id.lot_ids
            
        elif self.target_model == 'reception' and self.reception_id:
            # Búsqueda directa sobre el histórico de inyección de la guía
            lots = self.env['stock.lot'].search([('guia_processing_id', '=', self.reception_id.id)])
            
        elif self.target_model == 'purchase' and self.purchase_id:
            # Búsqueda directa de los lotes nacidos desde esta Orden de Compra
            lots = self.env['stock.lot'].search([('purchase_order_id', '=', self.purchase_id.id)])

        # 3. ASIGNACIÓN Y BLINDAJE DE DATOS (Se omite si el usuario elige cargar a mano)
        if self.target_model != 'manual':
            # Asignamos los contenedores detectados a la interfaz (Comando 6: Reemplaza todo con estos IDs)
            self.container_ids = [(6, 0, found_containers.ids)]
            
            # 🛡️ BLINDAJE ANTI-BASURA: Filtro estricto de integridad
            # - l.ref: Garantiza que el lote tenga una etiqueta física real asignada.
            # - (volumen_m3 > 0 or vol_shipment_m3 > 0): Garantiza que exista materia prima costeable.
            # Esto evita prorratear dólares a mermas vacías o registros residuales del staging.
            clean_lots = lots.filtered(lambda l: l.ref and (l.volumen_m3 > 0 or l.vol_shipment_m3 > 0))
            
            # Inyectamos los lotes sanitizados al expediente
            self.lot_ids = [(6, 0, clean_lots.ids)]

    def action_apply_costs(self):
            """ 
            🚀 Motor de Prorrateo Simplificado (Lógica Comercial de Felipe) 
            El reparto maestro SIEMPRE es por la proporción de m3 / Peso del paquete 
            sobre el total de la motonave.
            """
            self.ensure_one()
            if self.state != 'draft': 
                raise UserError("Solo se puede liquidar en estado Borrador.")
            if not self.lot_ids or not self.cost_line_ids:
                raise UserError("Faltan lotes o documentos de costo en el expediente.")

            # 1. Obtenemos los Totales Globales de la Motonave / Embarque
            tot_fisico = self.total_volumen_fisico
            tot_export = self.total_volumen_export
            # Usa peso_neto si existe, si no asume 0
            tot_peso = sum(getattr(l, 'peso_neto', 0.0) for l in self.lot_ids)
            tot_pzas = sum(l.piezas or 0 for l in self.lot_ids)
            
            # 🚢 LÓGICA DE MOTONAVE: Contamos cuántos contenedores únicos hay en este viaje
            unique_containers = len(self.lot_ids.mapped('container_id'))
            if unique_containers == 0 and self.container_ids:
                unique_containers = len(self.container_ids)
            elif unique_containers == 0:
                unique_containers = 1 # Fallback de seguridad para evitar multiplicar por 0

            vals_list = []
            for line in self.cost_line_ids:
                if line.amount_usd <= 0: 
                    continue

                # 2. EL CEREBRO DE FELIPE: ¿Costo Fijo o Costo por Contenedor?
                base_amount = line.amount_usd
                if line.distribution_method == 'container':
                    # Si Felipe pone $1,498 "Por Contenedor", el sistema calcula el Total de la Motonave
                    base_amount = line.amount_usd * unique_containers

                for lot in self.lot_ids:
                    factor = 0.0
                    
                    # 3. BASE DE REPARTO (La tajada de la torta que paga este paquete)
                    if line.distribution_method in ('volume_export', 'container'):
                        # Ambos métodos terminan usando los m3 de exportación para prorratear
                        if tot_export > 0:
                            factor = (lot.vol_shipment_m3 or 0.0) / tot_export
                            
                    elif line.distribution_method == 'volume_physical':
                        if tot_fisico > 0:
                            factor = (lot.volumen_m3 or 0.0) / tot_fisico
                            
                    elif line.distribution_method == 'weight':
                        if tot_peso > 0:
                            lote_peso = getattr(lot, 'peso_neto', 0.0)
                            factor = lote_peso / tot_peso
                            
                    elif line.distribution_method == 'pieces':
                        if tot_pzas > 0:
                            factor = (lot.piezas or 0) / tot_pzas
                            
                    elif line.distribution_method == 'equal':
                        factor = 1.0 / len(self.lot_ids)

                    # 4. Cálculo final en USD
                    amt_to_inject = base_amount * factor
                    
                    if amt_to_inject > 0:
                        # Obtenemos el nombre legible del costo para el registro
                        cost_type_label = dict(line._fields['cost_type'].selection).get(line.cost_type, str(line.cost_type))
                        
                        vals_list.append({
                            'lot_id': lot.id,
                            'distribution_id': self.id,
                            'name': f"{cost_type_label} | Doc:{line.invoice_num or 'S/N'}",
                            'cost_type': line.cost_type,
                            'amount_usd': amt_to_inject,
                            'partner_id': line.partner_id.id or self.partner_id.id,
                            'date': line.invoice_date,
                            'notes': f"Folio: {self.name} | Base: {line.distribution_method} | Factor: {factor:.4f}"
                        })

            if vals_list:
                # Inyectamos en la base de datos de una sola vez (Atómico)
                self.env['stock.lot.cost.line'].create(vals_list)
                
                # Recalculamos totales si el modelo lote tiene la función
                if hasattr(self.lot_ids, '_compute_total_cost_usd'):
                    self.lot_ids._compute_total_cost_usd()
                    
                self.write({'state': 'applied'})
                self.message_post(body=f"✅ Expediente Liquidado. Contenedores detectados en la Motonave: {unique_containers}. Reparto realizado proporcionalmente.")
            else:
                raise UserError("El sistema no pudo generar líneas de inyección. Verifique los volúmenes o pesos de los lotes.")

    def action_reverse_costs(self):
        self.ensure_one()
        self.generated_line_ids.unlink()
        self.lot_ids._compute_total_cost_usd()
        self.write({'state': 'draft'})
        self.message_post(body="⛔ Liquidación Revertida: El historial de costos ha sido limpiado y devuelto a Staging.")


class LumberCostDistributionLine(models.Model):
    _name = 'lumber.cost.distribution.line'
    _description = 'Línea de Factura de Gasto'

    distribution_id = fields.Many2one('lumber.cost.distribution', ondelete='cascade', string="Expediente")
    
    cost_type = fields.Selection([
        ('freight', 'Flete Marítimo'), 
        ('ocean_freight', 'Flete Nacional'),
        ('port', 'Puerto/THC/Grúas'), 
        ('customs', 'Aduana/Broker'),
        ('processing', 'Costo de Proceso (Servicio)'), 
        ('insurance', 'Seguros'), 
        ('other', 'Otros Gastos')
    ], string="Concepto de Costo", required=True)
    
    invoice_num = fields.Char(string="N° Factura / Guía", required=True)
    invoice_date = fields.Date(string="Fecha Doc.", default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string="Proveedor Gasto")
    
    currency_id = fields.Many2one('res.currency', string="Moneda", default=lambda self: self.env.company.currency_id)
    amount_original = fields.Float(string="Monto Original", required=True)
    exchange_rate = fields.Float(string="Tasa Cambio", default=1.0, digits=(12,4), help="Tasa a USD (Editable)")
    amount_usd = fields.Float(string="Monto USD", compute="_compute_amount_usd", store=True)

    distribution_method = fields.Selection([
        ('volume_export', 'Por Volumen Exportación (m³ comerciales)'),
        ('volume_physical', 'Por Volumen Físico Real (m³ reales)'),
        ('weight', 'Por Peso (kg)'),
        ('pieces', 'Por Piezas'),
        ('equal', 'Equitativo'),
        ('container', 'Por Contenedor (Multiplica Costo x Contenedores y reparte por m³)')
    ], default='volume_export', string="Base de Reparto", required=True)

    @api.onchange('currency_id', 'invoice_date')
    def _onchange_currency_id(self):
        for rec in self:
            if rec.currency_id:
                if rec.currency_id.name == 'USD':
                    rec.exchange_rate = 1.0
                elif rec.invoice_date:
                    usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
                    if usd_currency:
                        rec.exchange_rate = rec.currency_id._get_conversion_rate(usd_currency, rec.currency_id, self.env.company, rec.invoice_date)

    @api.depends('amount_original', 'exchange_rate', 'currency_id')
    def _compute_amount_usd(self):
        """ Tasa liberada para control del usuario """
        for rec in self:
            if not rec.currency_id or rec.currency_id.name == 'USD':
                rec.amount_usd = rec.amount_original
            else:
                rec.amount_usd = rec.amount_original / rec.exchange_rate if rec.exchange_rate > 0 else 0.0

class StockLotCostLine(models.Model):
    _inherit = 'stock.lot.cost.line'
    lot_name_clean = fields.Char(related='lot_id.ref', string='Etiqueta', store=True)
    cost_type = fields.Selection(
        selection_add=[
            ('freight', 'Flete Marítimo'),
            ('ocean_freight', 'Flete Nacional'),
            ('port', 'Puerto/THC/Grúas'),
            ('customs', 'Aduana/Broker'),
            ('processing', 'Costo de Proceso (Servicio)'),
            ('insurance', 'Seguros'),
            ('other', 'Otros Gastos'),
        ],
        ondelete={
            'freight': 'cascade',
            'ocean_freight': 'cascade',
            'port': 'cascade',
            'customs': 'cascade',
            'processing': 'cascade',
            'insurance': 'cascade',
            'other': 'cascade',
        }
    )
    