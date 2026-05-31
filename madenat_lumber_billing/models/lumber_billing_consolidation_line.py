# -*- coding: utf-8 -*-
"""
Líneas de consolidación de facturación.
Detalle por producto/lote con costos desglosados para auditoría.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LumberBillingConsolidationLine(models.Model):
    """
    Línea individual de consolidación de facturación.
    Cada línea representa un producto/lote con desglose de costos.
    """
    _name = 'lumber.billing.consolidation.line'
    _description = 'Línea de Consolidación de Facturación'
    _order = 'consolidation_id, sequence, id'

    # ============================================================================
    # CAMPOS BÁSICOS
    # ============================================================================
    
    consolidation_id = fields.Many2one(
        comodel_name='lumber.billing.consolidation',
        string='Consolidación',
        required=True,
        ondelete='cascade',
        index=True,
        help='Consolidación a la que pertenece esta línea'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización en la lista'
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='consolidation_id.currency_id',
        store=True,
        readonly=True
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        related='consolidation_id.company_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # TRAZABILIDAD DESDE LOGÍSTICA
    # ============================================================================
    
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lote/Tarja',
        help='Lote desde el cual se origina esta línea'
    )
    
    container_id = fields.Many2one(
        comodel_name='lumber.container',
        string='Contenedor',
        help='Contenedor al que pertenece el lote'
    )
    
    shipment_id = fields.Many2one(
        comodel_name='lumber.export.shipment',
        string='Embarque',
        related='consolidation_id.shipment_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # PRODUCTO Y CANTIDADES
    # ============================================================================
    
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto',
        required=True,
        domain="[('type', '=', 'product')]",
        help='Producto madera a facturar'
    )
    
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Categoría',
        related='product_id.categ_id',
        store=True,
        readonly=True
    )
    
    name = fields.Char(
        string='Descripción',
        required=True,
        help='Descripción de la línea que aparecerá en la factura'
    )
    
    volume_m3 = fields.Float(
        string='Volumen m³',
        digits='Product Unit of Measure',
        help='Volumen en metros cúbicos'
    )
    
    quantity = fields.Float(
        string='Cantidad',
        default=1.0,
        digits='Product Unit of Measure',
        help='Cantidad a facturar (puede ser piezas, m³, etc.)'
    )
    
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unidad de Medida',
        related='product_id.uom_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # DESGLOSE DE COSTOS - AUDITORÍA FELIPE
    # ============================================================================
    
    wood_cost_usd = fields.Monetary(
        string='Costo Madera USD',
        currency_field='currency_id',
        help='Costo de compra de la madera'
    )
    
    logistic_cost_usd = fields.Monetary(
        string='Costo Logística USD',
        currency_field='currency_id',
        help='Costo de logística y transporte'
    )
    
    process_cost_usd = fields.Monetary(
        string='Costo Procesamiento USD',
        currency_field='currency_id',
        help='Costo de procesamiento y manipulación'
    )
    
    other_cost_usd = fields.Monetary(
        string='Otros Costos USD',
        currency_field='currency_id',
        help='Otros costos adicionales'
    )
    
    cost_usd = fields.Monetary(
        string='Costo Total USD',
        compute='_compute_cost_usd',
        store=True,
        currency_field='currency_id',
        help='Suma de todos los costos'
    )

    # ============================================================================
    # PRECIO DE VENTA Y MARGEN
    # ============================================================================
    
    price_unit_usd = fields.Monetary(
        string='Precio Unitario USD',
        currency_field='currency_id',
        help='Precio de venta por unidad'
    )
    
    price_usd = fields.Monetary(
        string='Precio Total USD',
        compute='_compute_price_usd',
        store=True,
        currency_field='currency_id',
        help='Precio total de venta (cantidad × precio unitario)'
    )
    
    margin_usd = fields.Monetary(
        string='Margen USD',
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
        help='Diferencia entre precio de venta y costo'
    )
    
    margin_percent = fields.Float(
        string='% Margen',
        compute='_compute_margin',
        store=True,
        digits=(12, 2),
        help='Porcentaje de margen sobre el costo'
    )

    # ============================================================================
    # INFORMACIÓN ADICIONAL
    # ============================================================================
    
    notes = fields.Text(
        string='Notas',
        help='Observaciones adicionales sobre esta línea'
    )
    
    state = fields.Selection(
        string='Estado',
        related='consolidation_id.state',
        store=True,
        readonly=True
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    
    @api.depends('wood_cost_usd', 'logistic_cost_usd', 'process_cost_usd', 'other_cost_usd')
    def _compute_cost_usd(self):
        """Calcula el costo total sumando todos los componentes."""
        for line in self:
            # REFACTORIZADO: Usar total maestro del lote
            if line.lot_id:
                line.cost_usd = line.lot_id.total_cost_usd
            else:
                line.cost_usd = (
                    line.wood_cost_usd + 
                    line.logistic_cost_usd + 
                    line.process_cost_usd + 
                    line.other_cost_usd
                )
    
    @api.depends('quantity', 'price_unit_usd')
    def _compute_price_usd(self):
        """Calcula el precio total multiplicando cantidad por precio unitario."""
        for line in self:
            line.price_usd = line.quantity * line.price_unit_usd
    
    @api.depends('price_usd', 'cost_usd')
    def _compute_margin(self):
        """Calcula margen en USD y porcentaje."""
        for line in self:
            line.margin_usd = line.price_usd - line.cost_usd
            line.margin_percent = (
                (line.margin_usd / line.cost_usd * 100)
                if line.cost_usd else 0.0
            )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Autocompleta descripción al seleccionar producto."""
        if self.product_id:
            self.name = self.product_id.display_name
            self.quantity = 1.0
            # Sugerir precio de venta desde lista de precios
            if self.product_id.list_price:
                self.price_unit_usd = self.product_id.list_price
    
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Autocompleta datos desde el lote si existe.
        Carga costos reales desde el lote/tarja.
        """
        if self.lot_id:
            self.product_id = self.lot_id.product_id
            self.volume_m3 = getattr(self.lot_id, 'volumen_m3', 0.0)
            self.quantity = self.volume_m3
            
            # Cargar costos desde el lote
            self.wood_cost_usd = getattr(self.lot_id, 'wood_cost_usd', 0.0)
            self.logistic_cost_usd = getattr(self.lot_id, 'logistic_cost_usd', 0.0)
            self.process_cost_usd = getattr(self.lot_id, 'process_cost_usd', 0.0)
            
            # Descripción desde lote
            if hasattr(self.lot_id, 'name'):
                self.name = f"{self.lot_id.name} - {self.product_id.display_name}"

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    
    @api.constrains('quantity')
    def _check_quantity(self):
        """Valida que la cantidad sea positiva."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_(
                    "La cantidad debe ser mayor a cero.\n"
                    "Línea: %s"
                ) % line.name)
    
    @api.constrains('price_unit_usd')
    def _check_price_unit(self):
        """Valida que el precio unitario sea positivo."""
        for line in self:
            if line.price_unit_usd < 0:
                raise ValidationError(_(
                    "El precio unitario no puede ser negativo.\n"
                    "Línea: %s"
                ) % line.name)
    
    @api.constrains('cost_usd')
    def _check_cost(self):
        """Valida que el costo total sea positivo."""
        for line in self:
            if line.cost_usd < 0:
                raise ValidationError(_(
                    "El costo total no puede ser negativo.\n"
                    "Línea: %s"
                ) % line.name)

    # ============================================================================
    # DISPLAY NAME
    # ============================================================================
    
    def name_get(self):
        """Display name personalizado para la línea."""
        result = []
        for line in self:
            name = f"{line.product_id.display_name}"
            if line.volume_m3:
                name += f" ({line.volume_m3:.2f} m³)"
            result.append((line.id, name))
        return result
