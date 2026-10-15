# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tools import float_compare  # R2: comparación de cantidades por UoM
import hashlib
import json
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

# ════════════════════════════════════════════════════════════════════════════
# Sub-bloque 2 (2026-10-04) — BORRADOR SEGURO (AD-93)
# Retorno administrativo confirmed → draft sólo cuando NO existe evidencia
# física de salida, terminalidad de viaje, cierre financiero ni traza histórica
# de rebaja. Bloque autónomo: los gates se basan en evidencia real y en el
# estado del Embarque/Viaje, sin acoplarse a campos de sub-bloques posteriores.
# ════════════════════════════════════════════════════════════════════════════
RETURN_TO_DRAFT_GROUPS = (
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
RETURN_TO_DRAFT_TERMINAL_VOYAGE_STATES = ('cancel', 'departed', 'arrived')
RETURN_TO_DRAFT_WRITE_FIELDS = frozenset({'state', 'actual_departure'})
# Token efímero de proceso (no un context RPC): clave (dbname, uid, shipment_id).
# Se crea SÓLO en `action_draft` tras superar el guard y se consume UNA vez en
# `write()`.
_RETURN_TO_DRAFT_TOKENS = set()

# ============================================================================
# Sub-bloque 3 (2026-10-04) - ZARPE CON EXCEPCION B-01 (Politica B)
# Excepcion DOCUMENTAL bloqueante: el Embarque pasa a in_transit aunque existan
# Contenedores sin rebaja fisica, pero los pendientes CONSERVAN su estado real,
# no se mueve inventario y se abre una B-01 trazable que bloquea Entrega/Cierre
# y procesos posteriores hasta su regularizacion autorizada.
# ============================================================================
DEPARTURE_CONFIRM_GROUPS = (
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
DEPARTURE_OPEN_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
DEPARTURE_TERMINAL_VOYAGE_STATES = ('cancel', 'departed', 'arrived')
B01_EXCEPTION_MIN_REASON = 20
# Sub-bloque 4A (2026-10-04): motivos mínimos de la regularización R1.
B01_REGULARIZATION_MIN_REASON = 20
B01_WRITE_FIELDS = (
    'b01_exception_state',
    'b01_exception_reason',
    'b01_exception_opened_at',
    'b01_exception_opened_by_id',
    'b01_exception_audit_id',
    'b01_exception_resolved_at',
    'b01_exception_resolved_by_id',
    'b01_exception_resolution_audit_id',
)
# Token efimero de proceso (no falsificable por contexto RPC): los campos B-01
# SOLO se escriben desde _set_in_transit (patron identico a Borrador Seguro).
_B01_WRITE_TOKENS = set()
# Sub-bloque 4A (2026-10-04): token efimero que autoriza ÚNICAMENTE el cierre
# open → resolved desde `action_resolve_b01_exception` (no falsificable por RPC).
_B01_RESOLVE_TOKENS = set()

# ════════════════════════════════════════════════════════════════════════════
# Sub-bloque 5 (2026-10-04) — ENTREGA SEGURA (POLÍTICA D2, AD-98)
# Hito LOGÍSTICO controlado: in_transit → delivered. NO mueve stock, NO ejecuta
# Rebaja/R2, NO ejecuta Costeo/Billing/Pagos, NO modifica B-01. La documentación
# (B2) es evidencia informativa, no gate. Sin waiver.
# ════════════════════════════════════════════════════════════════════════════
DELIVERY_GROUPS = (
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
# Roles operativos autorizados a confirmar (draft → confirmed).
CONFIRM_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
# Estados terminales de `shipping.voyage` que bloquean la Entrega (sólo lectura).
DELIVERY_TERMINAL_VOYAGE_STATES = ('cancel', 'departed', 'arrived')
# Token efímero de PROCESO (set en memoria, no un context RPC — no falsificable
# por `with_context(...)`). Autoriza únicamente la transición `delivered` y la
# escritura de los campos de Entrega; se consume UNA vez en `write()`.
_DELIVERY_WRITE_TOKENS = set()


class LumberExportShipment(models.Model):
    _name = 'lumber.export.shipment'
    _description = 'Embarque de Exportación de Madera' 
    _inherit = ['mail.thread', 'mail.activity.mixin', 'madenat.deviation.mixin']
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

    # -- Sub-bloque 3 (2026-10-04) - Excepcion documental B-01 ---------------
    b01_exception_state = fields.Selection([
        ('none', 'Sin excepción B-01'),
        ('open', 'B-01 Abierta'),
        ('resolved', 'B-01 Regularizada'),
    ], string='Estado excepción B-01', default='none', copy=False, index=True)
    b01_exception_reason = fields.Text(
        string='Motivo excepción B-01', copy=False, readonly=True)
    b01_exception_opened_at = fields.Datetime(
        string='Fecha apertura B-01', copy=False, readonly=True)
    b01_exception_opened_by_id = fields.Many2one(
        'res.users', string='Abierta por', copy=False, readonly=True)
    b01_exception_audit_id = fields.Many2one(
        'madenat.audit.log', string='Auditoría B-01', copy=False,
        readonly=True)
    # Sub-bloque 4A (2026-10-04): cierre controlado open → resolved (R4).
    b01_exception_resolved_at = fields.Datetime(
        string='Fecha cierre B-01', copy=False, readonly=True)
    b01_exception_resolved_by_id = fields.Many2one(
        'res.users', string='Cerrada por', copy=False, readonly=True)
    b01_exception_resolution_audit_id = fields.Many2one(
        'madenat.audit.log', string='Auditoría de cierre B-01', copy=False,
        readonly=True)


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
        # ── Sub-bloque 2 (2026-10-04) — Borrador Seguro ─────────────────────
        # Cierra la puerta lateral: un write {'state': 'draft'} sólo se admite
        # cuando proviene de `action_draft` (token efímero de proceso), nunca
        # de un contexto aportado por RPC.
        if vals.get('state') == 'draft':
            self._assert_draft_write_authorized()
        # ── Sub-bloque 5 (2026-10-04) — Entrega Segura D2 (AD-98) ───────────
        # Puerta lateral cerrada: `state='delivered'` y los campos de Entrega
        # sólo se escriben desde `action_deliver` mediante token efímero de
        # proceso. `with_context(...)` NO elude.
        if vals.get('state') == 'delivered' or any(
                f in vals for f in ('delivery_at', 'delivery_by_id',
                                    'delivery_audit_id')):
            self._assert_delivery_write_authorized()
        # -- Sub-bloque 3 (2026-10-04) - Campos B-01 ---------------------------
        # Sólo _set_in_transit (token efímero de proceso) puede escribir los
        # campos B-01. Se bloquea cualquier write directo (RPC/import/cliente) y
        # se prohíbe fijar 'resolved' por esta vía.
        if any(f in vals for f in B01_WRITE_FIELDS):
            self._assert_b01_write_authorized(vals)
        # -- Sub-bloque 4A (2026-10-04) - Congelación de composición ----------
        # La lista de Contenedores queda CONGELADA cuando el Embarque está
        # Embarcado (in_transit) o tiene B-01 open/resolved. No hay bypass por
        # contexto RPC: se rechaza cualquier alta, baja o reasignación.
        if 'container_ids' in vals:
            frozen = self.filtered(
                lambda s: s.state == 'in_transit'
                or s.b01_exception_state in ('open', 'resolved'))
            if frozen:
                raise UserError(_(
                    'No se pueden añadir, quitar ni reasignar Contenedores en '
                    'un Embarque Embarcado (in_transit) o con excepción B-01 '
                    '(%s). Esta protección es de servidor y no admite '
                    'excepción.') % ', '.join(frozen.mapped('name')))
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
   
    # ══════════════════════════════════════════════════════════════════════
    # Fuente ÚNICA documental (corrección B2). El cómputo efectivo canónico
    # vive en `lumber_document_checklist.py::_compute_document_status` y se
    # basa en `document_ids` + `checklist_id.is_required` (evidencia real),
    # NO en los 5 booleanos informativos de abajo. Esos booleanos
    # (booking_confirmed, vgm_submitted, bl_received, customs_cleared,
    # invoice_issued) quedan como indicadores informativos/de transición y ya
    # no compiten por `document_status`.
    # Importante: `document_status` NUNCA es gate de operación física
    # (documentación tardía no bloquea rebaja/zarpe/B-01/R1/R2/Entrega).
    # ══════════════════════════════════════════════════════════════════════
    document_status = fields.Selection([
        ('not_configured', 'Sin configurar'),
        ('missing', 'Sin evidencia'),
        ('pending', 'Pendiente'),
        ('partial', 'Verificación parcial'),
        ('attached', 'Adjuntado'),
        ('verified', 'Verificado'),
    ], string='Estado Documental', compute='_compute_document_status',
        store=True)

    document_completion = fields.Float(
        string='Progreso Doc.',
        compute='_compute_document_status',
        store=True
    )

    document_pending_count = fields.Integer(
        string='Documentos Pendientes',
        compute='_compute_document_status', store=True)
    document_missing_count = fields.Integer(
        string='Documentos Faltantes',
        compute='_compute_document_status', store=True)
    document_verified_count = fields.Integer(
        string='Documentos Verificados',
        compute='_compute_document_status', store=True)

    def _document_status_summary(self):
        """Contrato de lectura B2 (read-only) del estado documental.

        Deriva EXCLUSIVAMENTE del compute canónico (`document_status` y los
        contadores almacenados). No escribe, no reclasifica ni consulta
        Costeo/B-01/R1/R2/R4/D2/Backlog. `document_status` es un indicador
        INFORMATIVO: nunca es gate de operación física.
        """
        self.ensure_one()
        return {
            'status': self.document_status,
            'configured': self.document_status != 'not_configured',
            'total_required': (
                self.document_pending_count + self.document_verified_count),
            'verified_count': self.document_verified_count,
            'pending_count': self.document_pending_count,
            'missing_count': self.document_missing_count,
        }

    # ══════════════════════════════════════════════════════════════════════
    # Sub-bloque 5 (2026-10-04) — ENTREGA SEGURA D2 (AD-98): campos persistentes
    # de la Entrega. Readonly; los escribe SÓLO `action_deliver` (token de
    # proceso, no falsificable por RPC/import/context). El estado canónico de la
    # Entrega es `state == 'delivered'` (no se crea `delivery_state`).
    # ══════════════════════════════════════════════════════════════════════
    delivery_at = fields.Datetime(
        string='Fecha de Entrega', readonly=True, copy=False, index=True)
    delivery_by_id = fields.Many2one(
        'res.users', string='Entregado por', readonly=True, copy=False,
        index=True)
    delivery_audit_id = fields.Many2one(
        'madenat.audit.log', string='Auditoría de Entrega', readonly=True,
        copy=False, index=True)

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

    # === ANÁLISIS COMERCIAL (Márgenes por Embarque) ===
    total_revenue_usd = fields.Monetary(
        string='Ingreso Total (USD)',
        compute='_compute_commercial_totals',
        store=True,
        currency_field='currency_id',
        help="Suma del ingreso por venta (sale_amount_usd) de todos los lotes del embarque."
    )

    gross_margin_usd = fields.Monetary(
        string='Margen Bruto (USD)',
        compute='_compute_commercial_totals',
        store=True,
        currency_field='currency_id',
        help="Ingreso Total - Costos de Embarque - Costo Madera."
    )

    gross_margin_pct = fields.Float(
        string='Margen Bruto (%)',
        compute='_compute_commercial_totals',
        store=True,
        digits=(16, 2),
        help="(Margen Bruto / Ingreso Total) × 100."
    )

    @api.depends(
        'container_ids.lot_ids.sale_amount_usd',
        'container_ids.lot_ids.wood_cost_usd',
        'total_shipment_costs_usd'
    )
    def _compute_commercial_totals(self):
        for shipment in self:
            lots = shipment.container_ids.mapped('lot_ids')
            revenue = sum(lots.mapped('sale_amount_usd'))
            wood_cost = sum(lots.mapped('wood_cost_usd'))
            shipment.total_revenue_usd = revenue
            shipment.gross_margin_usd = revenue - shipment.total_shipment_costs_usd - wood_cost
            if revenue > 0:
                shipment.gross_margin_pct = (shipment.gross_margin_usd / revenue) * 100
            else:
                shipment.gross_margin_pct = 0.0
    
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

    # ══════════════════════════════════════════════════════════════════════
    # NOTA (corrección B2): el cómputo de `document_status`,
    # `document_completion` y los contadores documentales
    # (`document_pending_count` / `document_missing_count` /
    # `document_verified_count`) es ÚNICO y vive en
    # `lumber_document_checklist.py::_compute_document_status`, basado en
    # `document_ids` + `checklist_id.is_required`. Se elimina aquí el cómputo
    # histórico basado en 5 booleanos (definición duplicada que dejaba la
    # semántica ambigua). Los booleanos quedan como indicadores informativos.
    # ══════════════════════════════════════════════════════════════════════

    @api.constrains('estimated_departure','estimated_arrival')
    def _check_dates(self):
        for rec in self:
            if rec.estimated_departure and rec.estimated_arrival and rec.estimated_arrival <= rec.estimated_departure:
                raise ValidationError(_("La fecha ETA debe ser posterior al ETD"))

    # === ACCIONES DE FLUJO ===

    def action_confirm(self):
        """Confirmación controlada (draft → confirmed).

        Sólo Operaciones/Jefatura/Gerencia. Bloquea estados no-draft y B-01
        open/resolved. La transición queda además protegida contra write directo
        (token de proceso). No modifica inventario.
        """
        self.ensure_one()
        if not any(self.env.user.has_group(g) for g in CONFIRM_GROUPS):
            raise AccessError(_(
                'No tiene permisos para confirmar el Embarque %s. Se requiere '
                'el rol de Operaciones, Jefatura de Operaciones o Gerencia.'
            ) % self.name)
        if self.state != 'draft':
            raise UserError(_(
                'Sólo se puede confirmar un Embarque en Borrador (draft). '
                'Estado actual: %s.') % dict(
                    self._fields['state'].selection).get(self.state, self.state))
        if self.b01_exception_state in ('open', 'resolved'):
            raise UserError(_(
                'No se puede confirmar el Embarque %s: tiene una excepción '
                'B-01 (%s).') % (self.name, self.b01_exception_state))
        if not self.container_ids:
            raise ValidationError(_("⛔ No se puede confirmar un embarque sin contenedores."))
        
        if not self.booking_reference:
            raise ValidationError(_("⛔ Falta el N° de Booking/Reserva de la naviera."))
            
        if not self.vessel_id:
             raise ValidationError(_("⛔ Debe asignar una Motonave antes de confirmar."))

        self.write({'state': 'confirmed'})
        self.message_post(body=_("✅ <b>Embarque Confirmado:</b> Listo para iniciar carga."))

    def _assert_departure_open_group(self):
        if not any(self.env.user.has_group(g) for g in DEPARTURE_OPEN_GROUPS):
            raise AccessError(_(
                'No tiene permisos para operar el zarpe. Se requiere el rol de '
                'Operaciones, Jefatura de Operaciones o Gerencia.'))

    def _assert_departure_group(self, groups=DEPARTURE_CONFIRM_GROUPS):
        if not any(self.env.user.has_group(g) for g in groups):
            raise AccessError(_(
                'No tiene permisos para confirmar el zarpe. Se requiere el rol '
                'de Jefatura de Operaciones o Gerencia.'))

    def _container_rebaja_classification(self, container):
        """Clasificador de rebaja física (R2). SÓLO lectura. 4 estados.

        - 'none': sin evidencia de rebaja.
        - 'active': salida (OUT) `done` SIN retorno físico total válido, o
          evidencia legacy AD-94 (línea `rebajado` sin picking de rebaja y
          Contenedor en `rebajado`/`shipped`).
        - 'compensated': salida `done` + retorno IN `done` TOTAL, enlazado por
          `origin_returned_move_id`, con lotes y cantidades exactos, y línea
          marcada `reversed` (rebaja físicamente anulada por R2).
        - 'inconsistent': evidencia contradictoria/parcial/no enlazada (línea
          `reversed` sin retorno total, línea `rebajado` con retorno total ya
          existente, o OUT no `done`, o mezcla `rebajado`+`reversed`).

        No depende de Costeo/Entrega y no escribe nada.
        """
        container.ensure_one()
        lines = container.line_ids
        out_pickings = lines.mapped('rebaja_picking_id')
        done_outs = out_pickings.filtered(lambda p: p.state == 'done')
        rebajado_lines = lines.filtered(lambda l: l.rebaja_state == 'rebajado')
        reversed_lines = lines.filtered(lambda l: l.rebaja_state == 'reversed')

        def _total_return_ok(picking):
            """Retorno físico TOTAL y enlazado para una salida OUT `done`."""
            if not picking or picking.state != 'done':
                return False
            moves = picking.move_ids.filtered(lambda m: m.state == 'done')
            if not moves:
                return False
            for move in moves:
                ret = self.env['stock.move'].search([
                    ('origin_returned_move_id', '=', move.id),
                    ('state', '=', 'done')])
                if not ret:
                    return False
                rounding = move.product_uom.rounding or 0.001
                if float_compare(
                        sum(ret.mapped('quantity')),
                        move.quantity or move.product_uom_qty,
                        precision_rounding=rounding) != 0:
                    return False
                if set(move.move_line_ids.mapped('lot_id').ids) != set(
                        ret.move_line_ids.mapped('lot_id').ids):
                    return False
            return True

        # 1) Evidencia por líneas (fuente primaria).
        if rebajado_lines and reversed_lines:
            return 'inconsistent'
        if rebajado_lines:
            # 1a) Compatibilidad legacy AD-94: líneas `rebajado` SIN picking de
            # rebaja (fixtures documentales, sin salida OUT real). Se aceptan
            # como Rebaja ACTIVA sólo si el Contenedor ya está en
            # `rebajado`/`shipped` (evidencia física consistente); si el estado
            # del Contenedor no lo respalda, siguen siendo inconsistencia. Se
            # evalúa ANTES de exigir `rebaja_picking_id.state == 'done'`.
            legacy = rebajado_lines.filtered(lambda l: not l.rebaja_picking_id)
            if legacy and len(legacy) == len(rebajado_lines):
                if container.state in ('rebajado', 'shipped'):
                    return 'active'
                return 'inconsistent'
            if any(not l.rebaja_picking_id or l.rebaja_picking_id.state != 'done'
                   for l in rebajado_lines):
                return 'inconsistent'
            if any(_total_return_ok(l.rebaja_picking_id)
                   for l in rebajado_lines):
                return 'inconsistent'
            return 'active'
        if reversed_lines:
            if all(_total_return_ok(l.rebaja_picking_id)
                   for l in reversed_lines):
                return 'compensated'
            return 'inconsistent'

        # 2) Evidencia física sin líneas explícitas (compatibilidad AD-94).
        if done_outs or container.state in ('rebajado', 'shipped'):
            return 'active'
        lots = lines.mapped('lot_id')
        customers = self.env.ref(
            'stock.stock_location_customers', raise_if_not_found=False)
        if lots and customers:
            if self.env['stock.move'].search([
                    ('state', '=', 'done'),
                    ('location_dest_id', '=', customers.id),
                    ('move_line_ids.lot_id', 'in', lots.ids)], limit=1):
                return 'active'
            if self.env['stock.quant'].search([
                    ('lot_id', 'in', lots.ids),
                    ('location_id', '=', customers.id),
                    ('quantity', '>', 0)], limit=1):
                return 'active'
            if self.env['madenat.sv.operation'].search([
                    ('action_type', '=', 'rebaja'),
                    ('state', '=', 'applied'),
                    ('lot_id', 'in', lots.ids)], limit=1):
                return 'active'
        return 'none'

    def _is_container_rebajado_fisico(self, container):
        """Evidencia de rebaja física ACTIVA (R2): clasificación == 'active'."""
        return self._container_rebaja_classification(container) == 'active'

    def _assert_no_rebaja_inconsistency(self):
        """R2: bloquea si algún Contenedor tiene rebaja INCONSISTENTE.

        Se invoca desde el Zarpe (`_assert_departure_context`) y la Entrega
        (`_assert_can_deliver`).
        SÓLO lectura: no altera B-01, stock, Costeo ni Finanzas.
        """
        self.ensure_one()
        bad = self.container_ids.filtered(
            lambda c: self._container_rebaja_classification(c) == 'inconsistent')
        if bad:
            raise UserError(_(
                'El Embarque %s tiene evidencia de rebaja física INCONSISTENTE '
                'en los Contenedores: %s. Ejecute el retorno físico total (R2) '
                'o corrija la inconsistencia antes de continuar.') % (
                    self.name, ', '.join(bad.mapped('name'))))
        return True

    def _classify_departure_containers(self):
        """(rebajados, pendientes) por evidencia fisica real."""
        rebajados = self.container_ids.filtered(
            self._is_container_rebajado_fisico)
        return rebajados, (self.container_ids - rebajados)

    def _assert_departure_context(self):
        """Guardas de contexto del zarpe. NO escribe."""
        self.ensure_one()
        self._assert_no_rebaja_inconsistency()
        if self.state != 'confirmed':
            raise UserError(_(
                'Sólo se puede zarpar un Embarque Confirmado (estado actual: '
                '%s).') % dict(self._fields['state'].selection).get(
                    self.state, self.state))
        if not self.vessel_id:
            raise UserError(_(
                'No se puede zarpar el Embarque %s: falta asignar una '
                'Motonave.') % self.name)
        if self.b01_exception_state == 'open':
            raise UserError(_(
                'El Embarque %s ya tiene una B-01 abierta. Regularice la '
                'excepción antes de un nuevo zarpe.') % self.name)
        if self.b01_exception_state == 'resolved':
            raise UserError(_(
                'El Embarque %s tiene una B-01 regularizada; este flujo no '
                'permite un nuevo zarpe hasta aprobar la política posterior.'
            ) % self.name)
        voyage = self.voyage_id
        if voyage and voyage.state in DEPARTURE_TERMINAL_VOYAGE_STATES:
            raise UserError(_(
                'No se puede zarpar: el Viaje %s está en estado terminal (%s).'
            ) % (voyage.name, voyage.state))
        if self.cost_distribution_state == 'distributed':
            raise UserError(_(
                'No se puede zarpar/confirmar B-01: los costos del Embarque ya '
                'fueron distribuidos.'))
        billed = False
        if 'lumber.billing.consolidation' in self.env:
            consolidations = self.env[
                'lumber.billing.consolidation'].search([
                    ('shipment_id', '=', self.id),
                    ('state', '!=', 'cancelled')])
            billed = consolidations.filtered(
                lambda c: c.invoice_id or c.state == 'billed')
        if billed:
            raise UserError(_(
                'No se puede zarpar/confirmar B-01: existe una consolidación '
                'de facturación incompatible.'))
        self._warn_legacy_b01_evidence()

    def _warn_legacy_b01_evidence(self):
        """AD-88 compat: advierte (no bloquea) si hay B-01 historica textual."""
        logs = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'deviation')])
        legacy = logs.filtered(
            lambda lg: '[B-01]' in (lg.description or '')
            and str(self.id) in (lg.batch_id or '').split(','))
        if legacy and self.b01_exception_state == 'none':
            _logger.warning(
                'B-01 historica textual para el Embarque %s sin campo '
                'relacional migrado (se trata como advertencia).', self.name)

    def _assert_can_depart(self, allow_b01=False, exception_reason=False):
        """Guard privado de zarpe. NO escribe. Devuelve (rebajados, pendientes)."""
        self.ensure_one()
        self._assert_departure_group()
        self._assert_departure_context()
        rebajados, pendientes = self._classify_departure_containers()
        if pendientes:
            if not allow_b01:
                raise UserError(_(
                    'Zarpe BLOQUEADO: existen Contenedores SIN rebaja física '
                    '(%s).\n\nRealice la rebaja física o use la excepción '
                    'documental B-01 (Jefatura/Gerencia) con motivo.'
                ) % ', '.join(pendientes.mapped('name')))
            reason = (exception_reason or '').strip()
            if len(reason) < B01_EXCEPTION_MIN_REASON:
                raise UserError(_(
                    'El motivo de la excepción B-01 es obligatorio y debe '
                    'tener al menos %d caracteres.') % B01_EXCEPTION_MIN_REASON)
        elif allow_b01:
            raise UserError(_(
                'No se puede abrir una B-01: el Embarque no tiene Contenedores '
                'pendientes de rebaja.'))
        return rebajados, pendientes

    def action_set_in_transit(self):
        """ZARPE (Jefatura/Gerencia). Sin pendientes zarpa directo; con
        pendientes abre el asistente (rebajar o excepción B-01). NO mueve stock.
        """
        self.ensure_one()
        self._assert_departure_open_group()
        self._assert_departure_context()
        _rebajados, pendientes = self._classify_departure_containers()
        if pendientes:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Zarpe con contenedores pendientes de rebaja'),
                'res_model': 'lumber.shipment.zarpe.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_shipment_id': self.id},
            }
        return self._set_in_transit()

    def _set_in_transit(self, exception_reason=False, is_b01=False):
        """Ejecuta el zarpe (sin mover stock). Con is_b01=True abre una
        excepción documental B-01 BLOQUEANTE: los Contenedores pendientes
        CONSERVAN su estado físico real (nunca pasan a shipped/rebajado).
        Sólo Jefatura/Gerencia."""
        self.ensure_one()
        rebajados, pendientes = self._assert_can_depart(
            allow_b01=is_b01, exception_reason=exception_reason)
        state_before = self.state
        now = fields.Datetime.now()

        # 1) Sólo los contenedores con REBAJA FÍSICA pasan a shipped.
        if rebajados:
            rebajados.write({'state': 'shipped'})
        # 2) Los pendientes NO se tocan: conservan su estado físico real.

        audit = False
        if is_b01:
            # AD-88: se conserva la desviación textual (compatibilidad).
            self._guard_deviation(
                'B-01',
                _('Zarpe con excepción B-01: contenedores SIN rebajar (%s) '
                  'conservan su estado físico; no hubo salida de inventario.'
                ) % ', '.join(pendientes.mapped('name')),
                reason=exception_reason,
                hard=False,
                extra={'pending_containers': pendientes.mapped('name')},
            )
            audit = self._create_b01_exception_audit(
                exception_reason, state_before, rebajados, pendientes)

        # 3) Cambio de estado del Embarque (sin tocar inventario).
        self.write({'state': 'in_transit', 'actual_departure': now})

        # 4) Persistir campos B-01 con token efímero (no falsificable por RPC).
        if is_b01:
            key = (self.env.cr.dbname, self.env.uid, self.id)
            _B01_WRITE_TOKENS.add(key)
            try:
                self.write({
                    'b01_exception_state': 'open',
                    'b01_exception_reason': exception_reason,
                    'b01_exception_opened_at': now,
                    'b01_exception_opened_by_id': self.env.user.id,
                    'b01_exception_audit_id': audit.id if audit else False,
                })
            finally:
                _B01_WRITE_TOKENS.discard(key)

        # 5) Chatter.
        if is_b01:
            self.message_post(body=_(
                '⚠️ <b>Zarpe con excepción B-01</b><br/>'
                'Motivo: %s<br/>'
                'Contenedores pendientes (conservan su estado físico, sin '
                'rebaja ni salida de inventario): %s<br/>'
                'El Embarque queda BLOQUEADO para Borrador, Rolleo, '
                'Entrega/Cierre, Costeo y procesos financieros hasta su '
                'regularización autorizada.'
            ) % (exception_reason, ', '.join(pendientes.mapped('name'))))
        else:
            self.message_post(body=_(
                '🚢 <b>Zarpe Confirmado:</b> La nave ha sido rematada. '
                'Contenedores en tránsito (sin movimiento de stock: ya '
                'rebajado).'))
        self._compute_yield_analysis()
        self.message_post(body=_(
            '📊 Rendimiento Final de Nave: %s%%') % self.yield_efficiency_pct)
        return True

    def _b01_container_snapshot(self, containers):
        return [
            {'id': c.id, 'name': c.name, 'state': c.state,
             'lines': [
                 {'lot': ln.lot_id.name or False,
                  'rebaja_state': ln.rebaja_state,
                  'rebaja_picking_id': ln.rebaja_picking_id.id or False,
                  'rebaja_picking_state': ln.rebaja_picking_id.state or False}
                 for ln in c.line_ids]}
            for c in containers]

    def _b01_snapshot(self, reason, state_before, rebajados, pendientes):
        """Snapshot determinista de la excepcion B-01 (JSON, sort_keys)."""
        self.ensure_one()
        payload = {
            'operation': {
                'action_type': 'b01_departure_exception',
                'timestamp': fields.Datetime.now().isoformat(),
                'actor': {'id': self.env.user.id, 'name': self.env.user.name},
                'reason': reason,
            },
            'shipment': {
                'id': self.id, 'name': self.name,
                'state_before': state_before, 'state_after': 'in_transit',
                'vessel': self.vessel_id.name or False,
                'voyage': self.voyage_id.name or False,
            },
            'containers_rebajados': self._b01_container_snapshot(rebajados),
            'containers_pendientes': self._b01_container_snapshot(pendientes),
            'physical_invariants': {
                'no_stock_movement': True,
                'no_quant_change': True,
                'no_picking_created': True,
            },
            'exception': {
                'state': 'open',
                'gates': {
                    'draft': 'blocked', 'rollover': 'blocked',
                    'delivery': 'blocked', 'costing': 'blocked',
                    'billing': 'blocked', 'payments': 'blocked',
                },
            },
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _create_b01_exception_audit(self, reason, state_before, rebajados, pendientes):
        """Crea la auditoria append-only B-01 (sudo SOLO para audit.log)."""
        self.ensure_one()
        snapshot = self._b01_snapshot(reason, state_before, rebajados, pendientes)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'b01_departure_exception',
            'description': _(
                'Zarpe con excepción B-01 del Embarque %s | Motivo: %s'
            ) % (self.name, (reason or '')[:180]),
            'batch_id': str(self.id),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })
        
    # ══════════════════════════════════════════════════════════════════════
    # Sub-bloque 4A (2026-10-04) — REGULARIZACIÓN B-01 (R1) y CIERRE (R4)
    # La rebaja extemporánea mueve inventario REAL con fecha efectiva actual
    # (no retrofecha). El cierre open → resolved sólo procede cuando no queda
    # ningún Contenedor pendiente y existe evidencia de regularización.
    # ══════════════════════════════════════════════════════════════════════
    def _b01_regularization_audits(self):
        """Auditorías de regularización B-01 (R1) del Embarque."""
        self.ensure_one()
        return self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'b01_regularization'),
            ('batch_id', '=', str(self.id))])

    def _b01_regularization_container_snapshot(self, container):
        """Evidencia física/lote/picking de un Contenedor regularizado."""
        rebaja_batch = ','.join(str(i) for i in container.line_ids.ids)
        rebaja_audits = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'rebaja'),
            ('batch_id', '=', rebaja_batch)]).ids
        return {
            'id': container.id,
            'name': container.name,
            'state_before': container.state_before_rebaja or False,
            'state_after': container.state,
            'lines': [
                {
                    'line_id': ln.id,
                    'lot': ln.lot_id.name or False,
                    'lot_id': ln.lot_id.id or False,
                    'quantity': round(ln.rebaja_qty_m3 or 0.0, 3),
                    'rebaja_state': ln.rebaja_state or False,
                    'rebaja_picking_id': ln.rebaja_picking_id.id or False,
                    'rebaja_picking_name': ln.rebaja_picking_id.name or False,
                    'rebaja_picking_state': ln.rebaja_picking_id.state or False,
                }
                for ln in container.line_ids.sorted('id')
            ],
            'rebaja_audit_ids': rebaja_audits,
        }

    def _b01_regularization_snapshot(self, containers, reason, approval_reason):
        """Snapshot determinista JSON (sort_keys) de la R1 ejecutada."""
        self.ensure_one()
        now = fields.Datetime.now()
        payload = {
            'operation': {
                'action_type': 'b01_regularization',
                'subtype': 'late_rebaja',
                'timestamp': now.isoformat(),
                'effective_at': now.isoformat(),
                'executor': {
                    'id': self.env.user.id, 'name': self.env.user.name},
                'approver': {
                    'id': self.env.user.id, 'name': self.env.user.name,
                    'role': 'gerencia'},
                'reason': reason,
                'approval_reason': approval_reason,
            },
            'shipment': {
                'id': self.id,
                'name': self.name,
                'b01_state': self.b01_exception_state,
                'original_b01_audit_id': self.b01_exception_audit_id.id or False,
            },
            'containers': [
                self._b01_regularization_container_snapshot(c)
                for c in containers.sorted('id')
            ],
            'invariants': {
                'departure_not_backdated': True,
                'physical_stock_moved_by_rebaja': True,
            },
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _create_b01_regularization_audit(self, containers, reason,
                                         approval_reason):
        """Crea la auditoría append-only de la R1 (sudo SÓLO para audit.log)."""
        self.ensure_one()
        snapshot = self._b01_regularization_snapshot(
            containers, reason, approval_reason)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'b01_regularization',
            'description': _(
                'Regularización B-01 (rebaja extemporánea R1) del Embarque %s '
                '| Contenedores: %s | Motivo: %s'
            ) % (self.name, ', '.join(containers.mapped('name')),
                 (reason or '')[:180]),
            'batch_id': str(self.id),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def action_open_b01_regularization_wizard(self):
        """Abre el asistente de regularización R1 (sólo Gerencia)."""
        self.ensure_one()
        if not self.env.user.has_group(
                'madenat_lumber_core.group_madenat_gerencia'):
            raise AccessError(_(
                'La regularización B-01 (R1) requiere el rol de Gerencia.'))
        if self.state != 'in_transit' or self.b01_exception_state != 'open':
            raise UserError(_(
                'Sólo se puede regularizar un Embarque En Tránsito con una '
                'excepción B-01 ABIERTA (actual: %s / %s).') % (
                    self.state, self.b01_exception_state))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Regularización B-01 (rebaja extemporánea)'),
            'res_model': 'lumber.b01.regularization.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_shipment_id': self.id},
        }

    def action_view_b01_audits(self):
        """Muestra las auditorías B-01 (apertura, R1 y cierre) del Embarque."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Auditorías B-01 — %s') % self.name,
            'res_model': 'madenat.audit.log',
            'view_mode': 'list,form',
            'domain': [
                ('batch_id', '=', str(self.id)),
                ('action_type', 'in', [
                    'b01_departure_exception', 'b01_regularization',
                    'b01_resolution']),
            ],
            'context': {'create': False},
        }


    def _assert_can_resolve_b01_exception(self):
        """Guard del cierre B-01 (R4). NO escribe, sin sudo.

        Autorizable sólo por Gerencia cuando: Embarque in_transit, B-01 open,
        todos los Contenedores están rebajados físicamente (sin pendiente
        residual), no hay costo/factura/pago incompatible y existe al menos una
        auditoría de regularización B-01 (la exclusión formal no se implementa).
        """
        self.ensure_one()
        if not self.env.user.has_group(
                'madenat_lumber_core.group_madenat_gerencia'):
            raise AccessError(_(
                'El cierre de la excepción B-01 requiere el rol de Gerencia.'))
        if self.state != 'in_transit':
            raise UserError(_(
                'Sólo se puede cerrar la B-01 de un Embarque Embarcado '
                '(in_transit). Estado actual: %s.') % self.state)
        if self.b01_exception_state == 'resolved':
            raise UserError(_(
                'El Embarque %s ya tiene la excepción B-01 regularizada '
                '(resolved).') % self.name)
        if self.b01_exception_state != 'open':
            raise UserError(_(
                'El Embarque %s no tiene una excepción B-01 abierta.') % self.name)
        if not self.container_ids:
            raise UserError(_(
                'No se puede cerrar la B-01: el Embarque no tiene '
                'Contenedores.'))
        _rebajados, pendientes = self._classify_departure_containers()
        if pendientes:
            raise UserError(_(
                'No se puede cerrar la B-01 del Embarque %s: quedan '
                'Contenedores pendientes de rebaja física (%s). Regularícelos '
                'mediante la rebaja extemporánea R1.') % (
                    self.name, ', '.join(pendientes.mapped('name'))))
        if self.cost_distribution_state == 'distributed':
            raise UserError(_(
                'No se puede cerrar la B-01: los costos del Embarque ya fueron '
                'distribuidos.'))
        consolidations = self.env['lumber.billing.consolidation'].search([
            ('shipment_id', '=', self.id), ('state', '!=', 'cancelled')])
        if consolidations.filtered(
                lambda c: c.invoice_id or c.state == 'billed'):
            raise UserError(_(
                'No se puede cerrar la B-01: existe una consolidación de '
                'facturación incompatible.'))
        if not self._b01_regularization_audits():
            raise UserError(_(
                'No se puede cerrar la B-01 del Embarque %s: no existe '
                'evidencia de regularización (R1) ni exclusión formal.'
            ) % self.name)
        return True

    def _b01_resolution_snapshot(self, regularization_audit_ids):
        """Snapshot determinista JSON del cierre open → resolved."""
        self.ensure_one()
        now = fields.Datetime.now()
        payload = {
            'operation': {
                'action_type': 'b01_resolution',
                'timestamp': now.isoformat(),
                'actor': {'id': self.env.user.id, 'name': self.env.user.name},
                'original_b01_audit_id': self.b01_exception_audit_id.id or False,
                'regularization_audit_ids': list(regularization_audit_ids),
            },
            'shipment': {
                'id': self.id, 'name': self.name, 'state': self.state,
                'b01_before': 'open', 'b01_after': 'resolved',
            },
            'containers': [
                self._b01_regularization_container_snapshot(c)
                for c in self.container_ids.sorted('id')
            ],
            'gates': {
                'delivery_eligible_after_resolution': True,
                'draft_still_blocked': True,
                'rollover_still_blocked': True,
            },
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _create_b01_resolution_audit(self, regularization_audit_ids):
        """Auditoría append-only del cierre B-01 (sudo SÓLO para audit.log)."""
        self.ensure_one()
        snapshot = self._b01_resolution_snapshot(regularization_audit_ids)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'b01_resolution',
            'description': _(
                'Cierre de excepción B-01 (open → resolved) del Embarque %s.'
            ) % self.name,
            'batch_id': str(self.id),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def action_resolve_b01_exception(self):
        """Cierra la excepción B-01 open → resolved (sólo Gerencia).

        No modifica la B-01 original (motivo/apertura). Usa token de proceso no
        falsificable; la misma transacción escribe estado, evidencia y
        auditoría append-only. Idempotente por bloqueo de reintento.
        """
        self.ensure_one()
        self._assert_can_resolve_b01_exception()
        reg_audits = self._b01_regularization_audits()
        audit = self._create_b01_resolution_audit(reg_audits.ids)
        now = fields.Datetime.now()
        key = (self.env.cr.dbname, self.env.uid, self.id)
        _B01_RESOLVE_TOKENS.add(key)
        try:
            self.write({
                'b01_exception_state': 'resolved',
                'b01_exception_resolved_at': now,
                'b01_exception_resolved_by_id': self.env.user.id,
                'b01_exception_resolution_audit_id': audit.id,
            })
        finally:
            _B01_RESOLVE_TOKENS.discard(key)
        self.message_post(body=_(
            '✅ <b>Excepción B-01 cerrada (resolved)</b> por %s.<br/>'
            'Todos los Contenedores quedaron rebajados físicamente (R1). '
            'El Embarque deja de estar bloqueado por B-01 para la '
            'Entrega/Cierre (los gates normales siguen aplicando). '
            'Auditoría de cierre: %s.'
        ) % (self.env.user.display_name, audit.id))
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_open_rebaja_wizard(self):
        """Abre el asistente «Rebajar por nave» con el alcance del embarque."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rebajar por nave'),
            'res_model': 'lumber.shipment.rebaja.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_vessel_id': self.vessel_id.id,
                'default_voyage_id': self.voyage_id.id,
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # AD-92 (2026-10-05) — ROLLEO CENTRADO EN EMBARQUE
    # Reprograma la salida marítima de ESTE Embarque (sólo vessel_id/voyage_id).
    # Sólo Operaciones/Jefatura/Gerencia y sólo en Borrador/Confirmado. El guard
    # de servidor del asistente revalida rol, estado, destino y exclusiones.
    # ══════════════════════════════════════════════════════════════════════
    def action_open_shipment_rollover_wizard(self):
        """Abre el asistente de Rolleo centrado en este Embarque."""
        self.ensure_one()
        if not any(self.env.user.has_group(g) for g in CONFIRM_GROUPS):
            raise AccessError(_(
                'No tiene permisos para reprogramar la salida marítima del '
                'Embarque %s. Se requiere el rol de Operaciones, Jefatura de '
                'Operaciones o Gerencia.') % self.name)
        if self.state not in ('draft', 'confirmed'):
            raise UserError(_(
                'El Rolleo de Embarque sólo aplica en Borrador o Confirmado. '
                'Estado actual: %s.') % dict(
                    self._fields['state'].selection).get(
                        self.state, self.state))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rollover de Embarque'),
            'res_model': 'lumber.vessel.rollover.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_shipment_id': self.id},
        }

    def _b01_blocks_delivery(self):
        """Sub-bloque 4A (2026-10-04): la Entrega sólo queda bloqueada por B-01
        mientras la excepción esté 'open'. Con 'resolved' la excepción deja de
        bloquear; los gates normales (Contenedores pendientes, terminal,
        financiero) siguen aplicándose por separado."""
        self.ensure_one()
        return self.b01_exception_state == 'open'

    def action_deliver(self):
        """Entrega Segura (POLÍTICA D2, AD-98): hito LOGÍSTICO controlado.

        Jefatura/Gerencia. `in_transit → delivered`. Gates: rol, sin
        inconsistencia física (R2), sin B-01 `open`, Viaje no terminal y sin
        Contenedores físicamente pendientes. La documentación (B2) es evidencia
        informativa: NO bloquea. NO mueve stock, NO ejecuta Rebaja/R2/Costeo/
        Billing/Pagos, NO modifica B-01. Único camino admitido hacia `delivered`.
        """
        self.ensure_one()
        self._assert_can_deliver()
        audit = self._audit_delivery()
        key = (self.env.cr.dbname, self.env.uid, self.id)
        _DELIVERY_WRITE_TOKENS.add(key)
        try:
            self.write({
                'state': 'delivered',
                'delivery_at': fields.Datetime.now(),
                'delivery_by_id': self.env.user.id,
                'delivery_audit_id': audit.id,
            })
        finally:
            _DELIVERY_WRITE_TOKENS.discard(key)
        self.message_post(body=_(
            '✅ <b>Embarque entregado</b> (hito logístico D2).<br/>'
            'Fecha: %(at)s · Usuario: %(by)s · Auditoría: %(aud)s (SHA-256).'
        ) % {
            'at': fields.Datetime.now(),
            'by': self.env.user.name,
            'aud': audit.id,
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _assert_delivery_group(self):
        """Autorización de Entrega (AD-98): Jefatura de Operaciones o Gerencia."""
        if not any(self.env.user.has_group(g) for g in DELIVERY_GROUPS):
            raise AccessError(_(
                'No tiene permisos para entregar el Embarque. Se requiere el '
                'rol de Jefatura de Operaciones o Gerencia.'))

    def _assert_can_deliver(self):
        """Guard de servidor (NO escribe, sin sudo): valida la Entrega D2."""
        self.ensure_one()
        self._assert_delivery_group()
        self._assert_no_rebaja_inconsistency()
        if self.state != 'in_transit':
            raise UserError(_(
                'Sólo se puede entregar un Embarque Embarcado (in_transit). '
                'Estado actual: %s.') % dict(
                    self._fields['state'].selection).get(self.state, self.state))
        if self._b01_blocks_delivery():
            raise UserError(_(
                'No se puede entregar el Embarque %s: tiene una excepción B-01 '
                'abierta. Regularice y cierre la excepción antes de la '
                'Entrega/Cierre.') % self.name)
        if self.voyage_id and \
                self.voyage_id.state in DELIVERY_TERMINAL_VOYAGE_STATES:
            raise UserError(_(
                'No se puede entregar el Embarque %s: el Viaje %s está en un '
                'estado terminal incompatible (%s).') % (
                    self.name, self.voyage_id.display_name or self.voyage_id.id,
                    self.voyage_id.state))
        # ── Puerta física D2 (AD-98) ────────────────────────────────────────
        # Semántica propia de la Entrega (SIN alterar el contrato de Zarpe):
        # un Contenedor sólo es "pendiente físico" si requiere Rebaja (no está
        # `active` en el contrato vigente) y su clasificación es `none`.
        # D2: un retorno R2 total (`compensated`) no es pendiente físico.
        pending = self.env['lumber.container']
        for container in self.container_ids:
            classification = self._container_rebaja_classification(container)
            if classification == 'inconsistent':
                raise UserError(_(
                    'No se puede entregar el Embarque %s: evidencia de rebaja '
                    'física INCONSISTENTE en el Contenedor %s.'
                ) % (self.name, container.name))
            if classification in ('active', 'compensated'):
                continue
            if not self._is_container_rebajado_fisico(container):
                pending |= container
        if pending:
            raise UserError(_(
                'No se puede entregar el Embarque %s: existen Contenedores '
                'pendientes de rebaja física (%s).'
            ) % (self.name, ', '.join(pending.mapped('name'))))
        # La documentación (B2) es evidencia informativa: NO bloquea la Entrega.
        return True

    # ── Puertas laterales (write directo) ──────────────────────────────────
    # Nota de diseño: el superusuario (env.su, código interno/tests) mantiene la
    # vía de escape estándar de Odoo; la protección con token aplica a TODO
    # actor RPC/real (su=False) y no es eludible por `with_context(...)` porque
    # el token es un set en memoria del proceso, no un contexto.
    def _assert_delivery_write_authorized(self):
        """Bloquea write directo de `state='delivered'` / campos D2 sin token."""
        for rec in self:
            if rec.env.su:
                continue
            key = (rec.env.cr.dbname, rec.env.uid, rec.id)
            if key not in _DELIVERY_WRITE_TOKENS:
                raise UserError(_(
                    'La Entrega del Embarque %s sólo puede ejecutarse mediante '
                    'la acción autorizada «Entregar».') % (rec.name or rec.id))
            _DELIVERY_WRITE_TOKENS.discard(key)

    # ── Auditoría de Entrega (append-only, SHA-256) ────────────────────────
    def _delivery_snapshot(self):
        """Snapshot determinista de la Entrega (sólo lectura; sin secretos)."""
        self.ensure_one()
        containers = self.container_ids
        _rebajados, pendientes = self._classify_departure_containers()
        bad = containers.filtered(
            lambda c: self._container_rebaja_classification(c) == 'inconsistent')
        cost_lines = self.cost_line_ids
        consolidations = self.env['lumber.billing.consolidation'].search([
            ('shipment_id', '=', self.id), ('state', '!=', 'cancelled')])
        return {
            'operation': {
                'action_type': 'shipment_delivery',
                'timestamp': fields.Datetime.now().isoformat(),
                'actor': {'id': self.env.user.id, 'name': self.env.user.name},
            },
            'shipment': {
                'id': self.id, 'name': self.name,
                'state_before': 'in_transit', 'state_after': 'delivered',
                'customer_id': self.customer_id.id or False,
                'vessel_id': self.vessel_id.id or False,
                'vessel': self.vessel_id.name or False,
                'voyage_id': self.voyage_id.id or False,
                'voyage': self.voyage_id.name or False,
                'voyage_state': self.voyage_id.state or False,
                'actual_departure': (
                    self.actual_departure.isoformat()
                    if self.actual_departure else False),
                'delivery_at': fields.Datetime.now().isoformat(),
                'delivery_by_id': self.env.user.id,
                'b01_exception_state': self.b01_exception_state,
                'b01_resolution_audit_id': (
                    self.b01_exception_resolution_audit_id.id or False),
            },
            'document': self._document_status_summary(),
            'containers': [
                {'id': c.id, 'name': c.name, 'state': c.state,
                 'classification': self._container_rebaja_classification(c),
                 'rebajado_fisico': self._is_container_rebajado_fisico(c)}
                for c in containers.sorted('id')],
            'physical_checks': {
                'no_b01_open': not self._b01_blocks_delivery(),
                'no_pending': not pendientes,
                'no_inconsistency': not bad,
            },
            'financial_status': {
                'cost_distribution_state': self.cost_distribution_state,
                'cost_lines': len(cost_lines),
                'invoices': len(cost_lines.filtered(
                    lambda cl: getattr(cl, 'invoice_id', False))),
                'payments': len(cost_lines.filtered(
                    lambda cl: getattr(cl, 'payment_state', 'not_paid')
                    not in (False, 'not_paid'))),
                'consolidations': len(consolidations),
            },
        }

    def _audit_delivery(self):
        """Crea la auditoría append-only (SHA-256) de la Entrega."""
        self.ensure_one()
        snapshot = json.dumps(
            self._delivery_snapshot(), sort_keys=True, default=str)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'shipment_delivery',
            'description': 'Entrega · %s' % (self.name or self.id),
            'batch_id': str(self.id),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

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
            # ── Sub-bloque 5 (2026-10-04) — Micro-parche P0 (puerta `create()`) ──
            # Contrato de creación EXTERNA: state='draft', sin campos de Entrega
            # ni B-01. Las transiciones (confirmed/in_transit/delivered/
            # cancelled) y los campos de excepción/Entrega sólo se alcanzan por
            # acciones autorizadas y auditadas. La protección aplica a todo
            # actor RPC/import (su=False); el superusuario interno (código/
            # tests) conserva la vía estándar de Odoo. `with_context(...)` NO elude.
            if not self.env.su:
                state = vals.get('state')
                if state and state != 'draft':
                    raise UserError(_(
                        'No se puede crear un Embarque directamente en estado '
                        '%s. Cree el Embarque en borrador y utilice el flujo '
                        'operativo autorizado para confirmar, zarpar o '
                        'entregar.') % state)
                if any(f in vals for f in (
                        'delivery_at', 'delivery_by_id', 'delivery_audit_id')):
                    raise UserError(_(
                        'Los campos de Entrega sólo pueden ser establecidos '
                        'por la acción operativa autorizada y auditada.'))
                if any(f in vals for f in B01_WRITE_FIELDS):
                    raise UserError(_(
                        'Los campos de excepción B-01 sólo pueden ser '
                        'establecidos por la acción operativa autorizada y '
                        'auditada.'))
            for field_name in B01_WRITE_FIELDS:
                if field_name in vals and vals.get(field_name):
                    raise UserError(_(
                        'Los campos de excepción B-01 no pueden fijarse al '
                        'crear el Embarque. Use el flujo autorizado de zarpe.'))
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
    def _return_to_draft_assert_group(self):
        if not any(self.env.user.has_group(g) for g in RETURN_TO_DRAFT_GROUPS):
            raise AccessError(_(
                'No tiene permisos para volver un Embarque a borrador. Se '
                'requiere el rol de Jefatura de Operaciones o Gerencia.'))

    def _return_to_draft_evidence(self):
        """Recolecta SÓLO lectura la evidencia bloqueante del Embarque."""
        self.ensure_one()
        containers = self.container_ids
        lines = containers.line_ids
        lots = lines.mapped('lot_id')
        customers = self.env.ref(
            'stock.stock_location_customers', raise_if_not_found=False)

        # ── Evidencia física ───────────────────────────────────────────────
        reb_containers = containers.filtered(
            lambda c: c.state in ('rebajado', 'shipped'))
        reb_lines = lines.filtered(lambda l: l.rebaja_state == 'rebajado')
        reb_pickings = lines.mapped('rebaja_picking_id').filtered(
            lambda p: p.state == 'done')
        exit_moves = reb_pickings.move_ids.filtered(
            lambda m: m.state == 'done'
            and m.location_dest_id.usage == 'customer')
        cust_quants = self.env['stock.quant'].browse()
        if customers and lots:
            cust_quants = self.env['stock.quant'].search([
                ('lot_id', 'in', lots.ids),
                ('location_id', '=', customers.id),
                ('quantity', '>', 0)])
        sv_ops = self.env['madenat.sv.operation'].search([
            ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied'),
            '|', ('destination_container_id', 'in', containers.ids),
            ('lot_id', 'in', lots.ids)])

        # ── Evidencia terminal ─────────────────────────────────────────────
        voyage = self.voyage_id
        voyage_terminal = bool(
            voyage and voyage.state in RETURN_TO_DRAFT_TERMINAL_VOYAGE_STATES)

        # ── Evidencia financiera ───────────────────────────────────────────
        distributed = self.cost_distribution_state == 'distributed'
        lot_cost_lines = self.env['stock.lot.cost.line'].browse()
        if self.cost_line_ids:
            lot_cost_lines = self.env['stock.lot.cost.line'].search([
                ('source_shipment_cost_line_id', 'in', self.cost_line_ids.ids)])
        invoiced_lines = self.cost_line_ids.filtered(
            lambda cl: getattr(cl, 'invoice_id', False))
        paid_lines = self.cost_line_ids.filtered(
            lambda cl: getattr(cl, 'payment_state', 'not_paid')
            not in (False, 'not_paid'))
        billed_consolidations = []
        if 'lumber.billing.consolidation' in self.env:
            consolidations = self.env[
                'lumber.billing.consolidation'].search([
                    ('shipment_id', '=', self.id),
                    ('state', '!=', 'cancelled')])
            billed_consolidations = consolidations.filtered(
                lambda c: c.invoice_id or c.state == 'billed')

        # ── Evidencia histórica (rebaja ocurrida y eventualmente revertida) ─
        # Traza persistente aunque el saldo externo ya se haya revertido.
        hist_lines = lines.filtered(lambda l: l.rebaja_state == 'reversed')
        hist_pickings = lines.mapped('rebaja_picking_id')

        return {
            'containers': reb_containers,
            'lines': reb_lines,
            'pickings': reb_pickings,
            'exit_moves': exit_moves,
            'cust_quants': cust_quants,
            'sv_ops': sv_ops,
            'voyage_terminal': voyage_terminal,
            'distributed': distributed,
            'lot_cost_lines': lot_cost_lines,
            'invoiced_lines': invoiced_lines,
            'paid_lines': paid_lines,
            'billed_consolidations': billed_consolidations,
            'hist_lines': hist_lines,
            'hist_pickings': hist_pickings,
        }
    def _assert_can_return_to_draft(self):
        """Guard de servidor: bloquea el retorno a borrador con evidencia."""
        self.ensure_one()
        self._return_to_draft_assert_group()
        if self.state != 'confirmed':
            raise UserError(_(
                'No se puede volver el Embarque %s a borrador: la única '
                'transición permitida es Confirmado → Borrador (estado actual: '
                '%s).') % (
                self.name,
                dict(self._fields['state'].selection).get(
                    self.state, self.state)))

        ev = self._return_to_draft_evidence()
        physical = []
        if ev['containers']:
            physical.append('Contenedores rebajados/embarcados: %s.' % ', '.join(
                ev['containers'].mapped('name')))
        if ev['lines']:
            physical.append('Líneas con rebaja aplicada: %s.' % ', '.join(
                'L-%s' % i for i in ev['lines'].ids))
        if ev['pickings']:
            physical.append('Picking de rebaja validado: %s.' % ', '.join(
                ev['pickings'].mapped('name')))
        if ev['exit_moves']:
            physical.append(
                'Movimientos de salida a Clientes confirmados: %s.' % ', '.join(
                    ev['exit_moves'].mapped('name')))
        if ev['cust_quants']:
            physical.append(
                'Saldo positivo en la ubicación Clientes para lotes del '
                'Embarque (%d).' % len(ev['cust_quants']))
        if ev['sv_ops']:
            physical.append('Operación SV de rebaja aplicada: %s.' % ', '.join(
                ev['sv_ops'].mapped('name')))

        terminal = []
        if ev['voyage_terminal']:
            terminal.append('El Viaje %s está en estado terminal (%s).' % (
                self.voyage_id.name, self.voyage_id.state))

        financial = []
        if ev['distributed']:
            financial.append('Los costos del Embarque ya fueron distribuidos.')
        if ev['lot_cost_lines']:
            financial.append(
                'Existen líneas de costo de lote atribuibles al Embarque (%d).'
                % len(ev['lot_cost_lines']))
        if ev['invoiced_lines']:
            financial.append('Hay líneas de costo con factura vinculada.')
        if ev['paid_lines']:
            financial.append('Hay líneas de costo con pago registrado.')
        if ev['billed_consolidations']:
            financial.append(
                'Existe una consolidación de facturación facturada para el '
                'Embarque.')

        historical = []
        if ev['hist_lines']:
            historical.append('Líneas de rebaja reversadas: %s.' % ', '.join(
                'L-%s' % i for i in ev['hist_lines'].ids))
        if ev['hist_pickings'] and not ev['pickings']:
            historical.append(
                'Picking(s) de rebaja originados: %s.' % ', '.join(
                    ev['hist_pickings'].mapped('name')))

        if not (physical or terminal or financial or historical):
            return True

        parts = [
            _('No se puede volver el Embarque %s a borrador.') % self.name, '',
            _('Existen evidencias que impiden el retorno:'), '']
        for title, items in (
                (_('[Rebaja física / salida]'), physical),
                (_('[Estado terminal]'), terminal),
                (_('[Cierre financiero]'), financial),
                (_('[Rebaja histórica]'), historical)):
            if items:
                parts.append(title)
                parts.extend('- %s' % x for x in items)
                parts.append('')
        parts.append(_('Acción requerida:'))
        parts.append(_(
            'Ejecute la reversa física autorizada («Revertir rebaja» por '
            'contenedor) o resuelva la evidencia indicada antes de cambiar la '
            'planificación.'))
        raise UserError('\n'.join(parts))
    def _return_to_draft_snapshot(self, state_before):
        """Snapshot determinista del retorno seguro (convención audit.log)."""
        self.ensure_one()
        payload = {
            'operation': {
                'action_type': 'shipment_return_to_draft',
                'timestamp': fields.Datetime.now().isoformat(),
                'user': {'id': self.env.user.id, 'name': self.env.user.name},
            },
            'shipment': {
                'id': self.id, 'name': self.name,
                'state_before': state_before, 'state_after': 'draft'},
            'voyage': {
                'id': self.voyage_id.id or False,
                'name': self.voyage_id.name or False,
                'state': self.voyage_id.state or False},
            'containers': [
                {'id': c.id, 'name': c.name, 'state': c.state}
                for c in self.container_ids],
            'lines': [
                {'id': l.id, 'lot': l.lot_id.name or False,
                 'rebaja_state': l.rebaja_state,
                 'rebaja_picking': l.rebaja_picking_id.name or False,
                 'rebaja_picking_state': l.rebaja_picking_id.state or False}
                for l in self.container_ids.line_ids],
            'checks_passed': ['physical', 'terminal', 'financial',
                              'historical'],
            'write': {'fields': sorted(RETURN_TO_DRAFT_WRITE_FIELDS)},
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _audit_return_to_draft(self, snapshot):
        """Registra el evento append-only (sudo SÓLO para madenat.audit.log)."""
        self.ensure_one()
        self.env['madenat.audit.log'].sudo().create({
            'action_type': 'shipment_return_to_draft',
            'description': _(
                'Retorno seguro a borrador del Embarque %s.') % self.name,
            'batch_id': str(self.id),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _assert_b01_write_authorized(self, vals):
        """Cierra la puerta lateral: los campos B-01 sólo se escriben desde
        _set_in_transit (o, para el cierre, desde `action_resolve_b01_exception`)
        mediante un token efímero de proceso, no falsificable por RPC.

        Sub-bloque 4A (2026-10-04): la única transición admitida hacia
        'resolved' es el token de cierre; 'open'/'none' y el resto de campos
        originales quedan reservados al token de zarpe B-01.
        """
        for rec in self:
            key = (rec.env.cr.dbname, rec.env.uid, rec.id)
            if vals.get('b01_exception_state') == 'resolved':
                if key not in _B01_RESOLVE_TOKENS:
                    raise UserError(_(
                        'La regularización B-01 (estado «resolved») del '
                        'Embarque %s sólo puede ejecutarse mediante la acción '
                        'autorizada «Cerrar B-01».') % (rec.name or rec.id))
                _B01_RESOLVE_TOKENS.discard(key)
            else:
                if key not in _B01_WRITE_TOKENS:
                    raise UserError(_(
                        'Los campos de excepción B-01 del Embarque %s sólo '
                        'pueden escribirse mediante el flujo autorizado de '
                        'zarpe B-01.') % (rec.name or rec.id))
                _B01_WRITE_TOKENS.discard(key)

    def _assert_draft_write_authorized(self):
        """Impide write({'state':'draft'}) fuera de action_draft autorizado.

        La autorización es un token efímero de proceso (no un context RPC que
        el cliente pueda falsificar).
        """
        for rec in self:
            key = (rec.env.cr.dbname, rec.env.uid, rec.id)
            if key not in _RETURN_TO_DRAFT_TOKENS:
                raise UserError(_(
                    'No se puede cambiar el Embarque %s a borrador por esta '
                    'vía. Use la acción autorizada «Volver a Borrador».'
                ) % (rec.name or rec.id))
            _RETURN_TO_DRAFT_TOKENS.discard(key)

    def action_draft(self):
        """Volver a Borrador SEGURO — Sub-bloque 2 (2026-10-04).

        Única transición permitida: confirmed → draft. Exige Jefatura/Gerencia
        y ausencia total de evidencia física, terminal, financiera u operativa.
        No cancela pickings, no reescribe contenedores, no borra costos ni mueve
        inventario. Sólo escribe state y actual_departure.
        """
        self.ensure_one()
        self._assert_can_return_to_draft()
        state_before = self.state
        key = (self.env.cr.dbname, self.env.uid, self.id)
        _RETURN_TO_DRAFT_TOKENS.add(key)
        try:
            self.write({'state': 'draft', 'actual_departure': False})
        finally:
            _RETURN_TO_DRAFT_TOKENS.discard(key)
        snapshot = self._return_to_draft_snapshot(state_before)
        self._audit_return_to_draft(snapshot)
        self.message_post(body=_(
            '↩️ <b>Retorno seguro a borrador</b> autorizado por %s.<br/>'
            'Validaciones físicas, terminales, financieras y operativas '
            'superadas.') % self.env.user.display_name)
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


class MadenatSvOperationLogistics(models.Model):
    """Vínculo del ledger SV con embarque/contenedor (asignación logística)."""

    _inherit = 'madenat.sv.operation'

    destination_shipment_id = fields.Many2one(
        'lumber.export.shipment',
        string='Embarque destino',
        ondelete='set null',
        index=True,
        help='Embarque al que se asignó el volumen rebajado (si aplica).',
    )
    destination_container_id = fields.Many2one(
        'lumber.container',
        string='Contenedor destino',
        ondelete='set null',
        index=True,
        help='Contenedor al que se asignó el volumen rebajado (si aplica).',
    )
