# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class LumberShipmentLine(models.Model):
    """
    Representa el detalle de cada lote asignado a un embarque.
    Calcula volúmenes comerciales (exportación) basados en reglas de cubicación dinámicas.
    """
    _name = 'lumber.shipment.line'
    _description = 'Línea de Detalle de Embarque (Packing List Item)'
    _order = 'container_id, id'

    # --- Relaciones Principales ---
    shipment_id = fields.Many2one(
        'lumber.export.shipment', 
        string='Embarque', 
        required=True, 
        ondelete='cascade',
        index=True
    )
    container_id = fields.Many2one(
        'lumber.container', 
        string='Contenedor', 
        ondelete='cascade',
        index=True
    )
    lot_id = fields.Many2one(
        'stock.lot', 
        string='Lote/Tarja', 
        required=True,
        index=True
    )
    
    # --- Datos Físicos (Espejo de stock.lot - INMUTABLES) ---
    physical_volume_m3 = fields.Float(
        related='lot_id.volumen_m3', 
        string='Vol. Físico (m³)', 
        store=True, 
        readonly=True,
        help="Volumen real calculado con dimensiones milimétricas exactas."
    )
    
    # --- Datos Comerciales (Cálculo Dinámico) ---
    export_width_inches = fields.Float(
        string='Ancho Nom. (Plg)', 
        compute='_compute_export_dims', 
        store=True,
        digits=(16, 3),
        help="Ancho físico convertido a pulgadas para referencia visual."
    )
    
    export_volume_m3 = fields.Float(
        string='Vol. Embarque (m³)', 
        compute='_compute_export_volume', 
        store=True, 
        digits=(16, 3),
        help="Volumen comercial calculado según la Regla de Cubicación del Embarque."
    )

    display_label = fields.Char(
        string='N° Etiqueta', 
        compute='_compute_display_label', 
        store=True, 
        readonly=True,
        help="Identificador simplificado del lote (Etiqueta de proveedor o sufijo interno)."
    )

    # --- Cálculos y Lógica ---

    @api.depends('lot_id', 'lot_id.ancho_mm')
    def _compute_export_dims(self):
        """Conversión informativa de ancho milimétrico a pulgadas."""
        for line in self:
            if line.lot_id and line.lot_id.ancho_mm:
                line.export_width_inches = line.lot_id.ancho_mm / 25.4
            else:
                line.export_width_inches = 0.0

    @api.depends('lot_id', 'shipment_id.shipping_rule_id', 'shipment_id.state',
                 'lot_id.espesor_mm', 'lot_id.largo_m', 'lot_id.piezas')
    def _compute_export_volume(self):
        """
        Calcula el volumen de exportación basado en reglas de negocio.
        Implementa lógica híbrida: respeta dimensiones métricas o aplica recargos (allowance) 
        si el producto tiene dimensiones nominales en pulgadas.
        """
        for line in self:
            # 1. Protección de Histórico: No recalcular si el embarque está finalizado
            if line.shipment_id.state in ['done', 'sealed', 'shipped']:
                continue

            # 2. Validación de consistencia
            if not line.lot_id or not line.shipment_id:
                line.export_volume_m3 = 0.0
                continue
            
            # 3. Obtención de Regla (Corrección de UnboundLocalError)
            rule = line.shipment_id.shipping_rule_id
            if not rule:
                # Fallback: Si no hay regla, el volumen de embarque es igual al físico
                line.export_volume_m3 = line.physical_volume_m3 or 0.0
                continue
            
            # 4. Datos Base del Lote
            width_mm = getattr(line.lot_id, 'ancho_mm', 0.0)
            thickness_mm = getattr(line.lot_id, 'espesor_mm', 0.0)
            length_m = getattr(line.lot_id, 'largo_m', 0.0)
            pieces = getattr(line.lot_id, 'piezas', 0)
            
            final_width_mm = width_mm

            # 5. Lógica de Cubicación (Métrico vs Imperial Nominal)
            if rule.calculation_method == 'nominal_plus_allowance':
                nominal_inches = self._parse_nominal_inches(line.lot_id)
                
                if nominal_inches > 0:
                    # Lote con ADN Imperial: Aplicar recargo (Ej: +1/8")
                    allowance = rule.allowance_inches or 0.0
                    adjusted_width_inch = nominal_inches + allowance
                    final_width_mm = adjusted_width_inch * 25.4
                else:
                    # Lote Métrico Puro: Respetar dimensiones físicas
                    final_width_mm = width_mm

            # 6. Cálculo Matemático Final
            if thickness_mm and final_width_mm and length_m and pieces:
                vol = (thickness_mm * final_width_mm * length_m * pieces) / 1_000_000.0
                line.export_volume_m3 = vol
            else:
                line.export_volume_m3 = 0.0

    def _parse_nominal_inches(self, lot):
        """
        Convierte texto de fracciones de pulgada a valores decimales float.
        Soporta formatos: '5 5/8', '6', '1/2'.
        """
        # Campo dinámico dependiendo del core
        field_name = 'ancho_inch_frac'
        if not hasattr(lot, field_name) or not getattr(lot, field_name):
            return 0.0
        
        try:
            text = str(getattr(lot, field_name)).strip().replace('"', '').replace("'", "")
            if not text: 
                return 0.0
            
            # Caso fracción compuesta: "5 5/8"
            if ' ' in text:
                parts = text.split()
                whole = float(parts[0])
                if '/' in parts[1]:
                    num, den = parts[1].split('/')
                    return whole + (float(num) / float(den))
                return whole
            
            # Caso fracción simple: "5/8"
            elif '/' in text:
                num, den = text.split('/')
                return float(num) / float(den)
            
            # Caso entero o decimal: "6"
            return float(text)
        except Exception as e:
            _logger.warning(f"Error parseando pulgadas nominales para el lote {lot.name}: {e}")
            return 0.0

   # --- Lógica de Etiquetado con Protección de Integridad ---

    @api.depends('lot_id', 'lot_id.name')
    def _compute_display_label(self):
        """
        Calcula la etiqueta simplificada para el Packing List.
        Se eliminó la dependencia directa de 'supplier_label' para evitar KeyErrors
        si el campo no está presente en el modelo stock.lot.
        """
        for line in self:
            lot = line.lot_id
            if not lot:
                line.display_label = ''
                continue
            
            # 1. Verificación dinámica de supplier_label (evita caídas si el campo falta)
            supplier_label = getattr(lot, 'supplier_label', False)
            if supplier_label:
                line.display_label = str(supplier_label).strip()
            
            # 2. Lotes de Recepción Interna: Extraer sufijo (ej: "39181-123" -> "123")
            elif getattr(lot, 'origin_type', False) == 'lumber_reception' and '-' in (lot.name or ''):
                line.display_label = lot.name.split('-')[-1].strip()
            
            # 3. Fallback: Nombre completo del sistema
            else:
                line.display_label = lot.name or ''

    display_label = fields.Char(
        string='N° Etiqueta', 
        compute='_compute_display_label', 
        store=True, 
        readonly=True,
        help="Identificador simplificado del lote para el Packing List."
    )
