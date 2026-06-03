# -*- coding: utf-8 -*-
"""
Extensión del modelo stock.lot para manejar especificaciones técnicas de madera
Versión: 4.0.1 - CORRECCIÓN MÉTODO UNIFICADO _compute_product_display

Cambios v4.0.1 (2024-12-04):
✅ AGREGADO: Método unificado _compute_product_display()
✅ MANTENIDO: Métodos legacy por compatibilidad
✅ MEJORADO: store=True en product_code_only y product_name_only

Cambios v4.0:
- Agregado: Sistema de genealogía de lotes (parent-child relationships)
- Agregado: Campos external_labels (etiquetas externas de proveedores)
- Agregado: Nivel de generación automático
- Agregado: origin_type (purchase/processing/split/merge)
- Agregado: action_view_lot_genealogy (vista de árbol genealógico)
- Mejorado: Estado trazabilidad incluye 'procesado'
- Mejorado: Cálculo automático de pérdida por procesamiento
- Mejorado: Manejo robusto de errores con try/except
"""

import re
import math
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from .utils_uom import INCH_SQ_METERS_TO_M3, get_s2s_adjustment, r3, r4, BLANK_CLEAR_FACTOR, MM_PER_INCH, FT_TO_M, M_TO_FT


_logger = logging.getLogger(__name__)


class StockLotExtended(models.Model):
    """
    Extensión de stock.lot para industria maderera con soporte de:
    - Dimensiones fraccionarias (pulgadas/pies) y métricas (mm/m)
    - Volumen dual (compra bruto vs embarque neto)
    - Genealogía de lotes (padre-hijo para procesamiento)
    - Trazabilidad de transformación (cepillado/reaserrado)
    - Costeo multi-nivel (compra + servicio + logística)
    - Valorización en m³ (compra) y MBF (venta)
    """
    _inherit = 'stock.lot'

    # ==========================================================================
    # 🛡️ BLINDAJE DE INTEGRIDAD DE DATOS (Regla de Oro Madenat)
    # ==========================================================================
    _sql_constraints = [
        ('check_volumen_m3_positive', 'CHECK(volumen_m3 >= 0)', 
         'El volumen m³ no puede ser negativo.'),
        ('check_piezas_positive', 'CHECK(piezas >= 0)', 
         'La cantidad de piezas no puede ser negativa.'),
        ('check_cost_positive', 'CHECK(total_cost_usd >= 0)', 
         'El costo total no puede ser negativo.')
    ]

       # === TRAZABILIDAD IMPERIAL ===
    reception_thickness_in = fields.Float("Espesor Origen (in)", help="Espesor en pulgadas al momento de la recepción", digits=(10, 3))
    reception_width_in = fields.Float("Ancho Origen (in)", digits=(10, 3))
    reception_length_ft = fields.Float("Largo Origen (ft)", digits=(10, 3))
    reception_board_feet = fields.Float("Board Feet Origen", digits=(12, 3))
    length_ft = fields.Float(string="Largo (Pies)", digits=(16, 3), help="Largo procesado (Exportación)")
     # === CAMPOS VISUALES PERSISTENTES (TRADER V2) ===
    # Para guardar "5 5/8" o "RW" corregido
    thickness_visual = fields.Char("Espesor Comercial", help="Ej: 6/4")
    width_visual = fields.Char("Ancho Comercial", help="Ej: 5 5/8, RW")
    
    # Campo para volumen físico REAL (el de embarque) si no existe 'vol_shipment_m3'
    # En su archivo veo 'volumeshipmentm3', usaremos ese si ya existe.


    # ============================================================================
    # ✅ CAMPOS COMPUTADOS PARA SEPARAR CÓDIGO Y NOMBRE
    # ============================================================================
    
    product_code_only = fields.Char(
        string='Código Producto',
        compute='_compute_product_display',  # ← Usa método unificado
        store=True,  # ← CRÍTICO: Permitir búsquedas y ordenamiento
        readonly=True,
        help='Código interno del producto (ej: 2X4, 2X6)'
    )
    
    product_name_only = fields.Char(
        string='Nombre Producto',
        compute='_compute_product_display',  # ← Usa método unificado
        store=True,  # ← CRÍTICO: Mismo motivo
        readonly=True,
        help='Nombre completo del producto sin código'
    )
    # ============================================================================
    # 🆕 MÉTODO UNIFICADO (v4.0.1) - REGLA DE ORO: EFICIENCIA
    # ============================================================================
    
    @api.depends('product_id', 'product_id.default_code', 'product_id.name')
    def _compute_product_display(self):
        """
        🔥 MÉTODO UNIFICADO: Calcular código y nombre del producto en un solo loop.
        
        REGLA DE ORO - EFICIENCIA:
        - Un solo método calcula AMBOS campos (product_code_only y product_name_only)
        - Evita loops duplicados y mejora performance
        - Mantiene lógica de limpieza existente
        
        Ejemplos:
        - Input:  product_id.display_name = "[2X4] Pino Oregón 2x4\" - 3.66m"
        - Output: product_code_only = "2X4"
                  product_name_only = "Pino Oregón 2x4\" - 3.66m"
        
        Versión: v4.0.1 (2024-12-04)
        Autor: Auditoría Técnica - Fase 5
        """
        for lot in self:
            if not lot.product_id:
                lot.product_code_only = ''
                lot.product_name_only = ''
                continue
            
            # ============================================
            # 1. EXTRAER CÓDIGO (desde default_code)
            # ============================================
            lot.product_code_only = lot.product_id.default_code or ''
            
            # ============================================
            # 2. LIMPIAR NOMBRE (remover código del inicio)
            # ============================================
            full_name = lot.product_id.name or ''
            
            # Caso 1: Producto con formato [CÓDIGO] Nombre
            if lot.product_code_only and full_name.startswith(f"[{lot.product_code_only}]"):
                # Remover "[CÓDIGO] " del inicio
                lot.product_name_only = full_name.replace(f"[{lot.product_code_only}] ", '', 1).strip()
            
            # Caso 2: Nombre con patrón genérico [xxx]
            elif full_name.startswith('[') and ']' in full_name:
                lot.product_name_only = full_name.split(']', 1)[1].strip()
            
            # Caso 3: Producto sin código o formato diferente
            else:
                lot.product_name_only = full_name

    # ============================================================================
    # 📦 MÉTODOS LEGACY (MANTENER POR COMPATIBILIDAD)
    # ============================================================================
    # NOTA: Estos métodos se mantienen para no romper código que los referencie
    # pero ya NO son llamados por los campos (que usan _compute_product_display)
    
    @api.depends('product_id', 'sku_original', 'note')
    def _compute_product_code_only(self):
        """
        ✅ MEJORADO: Prioriza el Código Interno del Excel (sku_original)
        para evitar redundancia visual en la vista de lista.
        """
        for record in self:
            # 1. Prioridad 1: Código Interno del Procesamiento (ej: PCLAT...)
            if hasattr(record, 'sku_original') and record.sku_original:
                record.product_code_only = record.sku_original
            
            # 2. Prioridad 2: Si no hay SKU pero hay una nota técnica útil
            elif record.note and ('PCLAT' in record.note or 'PBRUT' in record.note):
                record.product_code_only = record.note
            
            # 3. Fallback: Código genérico del producto maestro
            else:
                record.product_code_only = record.product_id.default_code or ''
    
    @api.depends('product_id')  
    def _compute_product_name_only(self):
        """
        ⚠️ LEGACY: Mantener por compatibilidad
        Usa _compute_product_display en su lugar
        """

        for record in self:
            name = record.product_id.name or ''
            # Limpiar nombre si tiene formato con código
            if name.startswith('[') and ']' in name:
                name = name.split(']', 1)[1].strip()
            record.product_name_only = name
    
    @api.depends('product_id')
    def _compute_product_code_display(self):
        """⚠️ LEGACY: Mantener por compatibilidad"""
        for record in self:
            record.product_code_display = record.product_id.default_code or ''
    
    @api.depends('product_id')
    def _compute_product_name_display(self):
        """⚠️ LEGACY: Mantener por compatibilidad"""
        for record in self:
            # Limpiar nombre si tiene código incluido
            name = record.product_id.name or ''
            if name.startswith('[') and ']' in name:
                name = name.split(']', 1)[1].strip()
            record.product_name_display = name

    # ==============================================================================
    # SECCIÓN 1: RELACIONES Y TRAZABILIDAD BÁSICA
    # ==============================================================================
        # === TRAZABILIDAD ORIGEN  ===
    lumber_reception_id = fields.Many2one(
        'lumber.reception', 
        string="Recepción de Origen",
        readonly=True,
        help="Enlace a la recepción donde se ingresó este paquete."
    )

    
    reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción de Compra',
        domain="[('state', '=', 'done')]",
        help="EXCLUSIVAMENTE para recepciones de compra de madera nueva - No usar para procesamiento interno"
    )
    
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía de Procesamiento',
        readonly=True,
        domain="[('state', '=', 'done')]",
        help="EXCLUSIVAMENTE para transformación interna (cepillado/reaserrado) - No usar para recepciones"
    )
    
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Orden de Compra',
        compute='_compute_purchase_info',
        store=True,
        readonly=False,
        help="OC origen del lote para trazabilidad y seguimiento"
    )
  
       
    espesor_nominal_mm = fields.Float(
        string='Espesor Nominal (mm)', 
        digits=(16, 3),
        help="Espesor comercial de compra (ej: 55mm). Pestaña 2."
    )
    # ==================== CLASIFICACIÓN ====================
    reception_type = fields.Selection([
        ('raw', 'Madera Bruta - Recepción desde Proveedor'),
        ('processed', 'Madera Procesada - Post-Transformación'),
    ], string='Tipo de Recepción', compute='_compute_reception_type', store=True, index=True,
       help="Identifica si el lote proviene de una compra (Bruta) o de un servicio (Procesada).")


 
    @api.depends('reception_id', 'guia_processing_id')
    def _compute_reception_type(self):
        """Determinar automáticamente el tipo de origen del lote"""
        for lot in self:
            if lot.reception_id:
                lot.reception_type = 'raw'
            elif lot.guia_processing_id:
                lot.reception_type = 'processed'
            else:
                lot.reception_type = False
      
    @api.constrains('reception_id', 'guia_processing_id')
    def _check_reception_guia_exclusivity(self):
        """
        REGLA DE ORO: Garantizar separación clara entre recepciones y procesamiento
        Un lote debe tener SOLO UNA de estas relaciones, nunca ambas
        """
        for lot in self:
            if lot.reception_id and lot.guia_processing_id:
                raise ValidationError(_(
                    "❌ CONFLICTO DE TRAZABILIDAD: El lote %s no puede tener simultáneamente:\n"
                    "• Recepción de Compra (madera nueva comprada) Y\n" 
                    "• Guía de Procesamiento (madera transformada internamente)\n\n"
                    "SOLUCIÓN: Use recepción para madera comprada, guía para madera procesada."
                ) % lot.name)
    
    @api.depends('reception_id', 'guia_processing_id')
    def _compute_guia_number(self):
        """
        ✅ REGLA DE ORO: Mostrar número de guía correcto según el origen
        - Recepción: número de guía de recepción  
        - Procesamiento: número de guía de procesamiento
        """
        for lot in self:
            if lot.reception_id:
                # Lote de compra directa → Mostrar guía de recepción
                lot.guia_number = lot.reception_id.name
            elif lot.guia_processing_id:
                # Lote de procesamiento → Mostrar guía de procesamiento
                lot.guia_number = lot.guia_processing_id.name
            else:
                # Lote sin origen claro
                lot.guia_number = False
        
    guia_number = fields.Char(
    string='N° de Guía',
    compute='_compute_guia_number',
    store=True,
    help="Muestra número de guía según origen: recepción o procesamiento"
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor',
        compute='_compute_purchase_info',
        store=True,
        readonly=True,
        help="Proveedor del lote"
    )
    # ==============================================================================
    # SECCIÓN 1.5: GENEALOGÍA DE LOTES (BATCH MANAGEMENT) ⭐ NUEVO
    # ==============================================================================
    
    parent_lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lote Padre',
        index=True,
        tracking=True,
        ondelete='set null',  # ✅ ROBUSTO
        help="Lote del cual se originó este lote (por procesamiento, división, etc.)"
    )
    child_lot_ids = fields.One2many(
        comodel_name='stock.lot',
        inverse_name='parent_lot_id',
        string='Lotes Derivados',
        help="Lotes generados desde este lote por transformación"
    )
    generation_level = fields.Integer(
        string='Nivel de Generación',
        compute='_compute_generation_level',
        store=True,
        recursive=True,
        help="0=Lote original, 1=Primera transformación, 2=Segunda, etc."
    )
    external_labels = fields.Char(
        string='Etiquetas Externas',
        index=True,
        help="Códigos de proveedores externos (D7731, CEPILLO-001, etc.) separados por coma"
    )
    origin_type = fields.Selection(
        selection=[
            ('purchase', 'Compra Directa'),
            ('processing', 'Procesamiento'),
            ('split', 'División de Lote'),
            ('merge', 'Fusión de Lotes'),
        ],
        string='Origen del Lote',
        help="Cómo se originó este lote"
    )
    # ==============================================================================
    # SECCIÓN 2: CLASIFICACIÓN Y ETIQUETADO
    # ==============================================================================
    
    subproducto_id = fields.Many2one(
        comodel_name='madenat.subproducto',
        string='Sub-producto',
        index=True,
        help="Categoría del producto terminado (ej: BLANK CLEAR, BLANK PANELEADO, RIP S2S)"
    )
    escuadria = fields.Char(
        string='Escuadría',
        compute='_compute_escuadria',
        store=True,
        help="Dimensiones en formato original ingresado (ej: 1 1/4 x 4 x 10')"
    )
    escuadria_excel = fields.Char(
        string='Escuadría Excel',
        help='Escuadría original del archivo Excel (no calculada) - Para trazabilidad exacta'
    )
    
    # ==============================================================================
    # SECCIÓN 3: DIMENSIONES FRACCIONARIAS (ENTRADA DE USUARIO)
    # ==============================================================================
    
    espesor_inch_frac = fields.Char(
        string='Espesor (pulg)',
        help='Formato: 1 1/4, 3/4, 2 (acepta fracciones y enteros)'
    )
    ancho_inch_frac = fields.Char(
        string='Ancho (pulg)',
        help='Formato: 4, 3 1/2, 5/8 (acepta fracciones y enteros)'
    )
    largo_ft_frac = fields.Char(
        string='Largo (pies)',
        help='Formato: 10, 8 1/2, 12 (acepta fracciones y enteros)'
    )
    # ==============================================================================
    # SECCIÓN 4: DIMENSIONES TÉCNICAS MÉTRICAS (CÁLCULO)
    # ==============================================================================
    
    espesor_mm = fields.Float(
        string='Espesor (mm)', 
        compute='_compute_metric_dimensions',
        inverse='_inverse_metric_dimensions',
        store=True,
        digits=(16, 3),
        help="Calculado desde fracciones O asignado directamente (ej: por importación Excel)"
    )
    ancho_mm = fields.Float(
        string='Ancho (mm)', 
        compute='_compute_metric_dimensions',
        inverse='_inverse_metric_dimensions',
        store=True,
        digits=(16, 3),
        help="Calculado desde fracciones O asignado directamente"
    )
    largo_m = fields.Float(
        string='Largo (m)', 
        compute='_compute_metric_dimensions',
        inverse='_inverse_metric_dimensions',
        store=True,
        digits=(16, 3),
        help="Calculado desde fracciones O asignado directamente"
    )
    piezas = fields.Integer(
        string='N° Piezas',
        help="Cantidad de piezas en el lote"
    )
    # ==============================================================================
    # SECCIÓN 5: VOLUMEN DUAL (COMPRA vs EMBARQUE) - CRÍTICO PARA COSTEO
    # ==============================================================================
    
  
    volume_purchase_m3 = fields.Float(
        string='Volumen Compra (m³)',
        digits=(16, 3),
        help="Volumen original al momento de compra (dimensiones brutas, pre-cepillado)."
    )

    # ==============================================================================
    # SECCIÓN NUEVA: CÁLCULO DE VOLUMEN DE EMBARQUE (COMERCIAL)
    # ==============================================================================
    
    # 🚀 CAMBIO 1: Nombre de variable corto (vol_shipment_m3)
    vol_shipment_m3 = fields.Float(
        string='Volumen Embarque (m³)',
        store=True, 
        readonly=False, # Permite edición manual si es necesario (flexibilidad)
        digits=(16, 3),
        help="Volumen calculado según regla comercial del producto (Nominal) o Físico si no hay regla."
    )

    @api.depends(
        'product_id.use_commercial_standard',
        'product_id.commercial_thickness_mm',
        'product_id.commercial_width_mm',
        'product_id.commercial_length_m',
        'espesor_mm', 'ancho_mm', 'largo_m',
        'largo_ft_frac', 'piezas', 'reception_id',
        'volume_purchase_m3', 'volumen_m3' # 🚀 CAMBIO 2: Dependencias del Salvavidas
    )
    def _compute_vol_shipment_m3(self): # 🚀 CAMBIO 3: Nombre de función corto
        """
        🛡️ ARQUITECTURA DE CÁLCULO MADENAT - VOLUMEN DE EMBARQUE (COMMERCIAL VOLUME)
        
        Esta función implementa la 'Regla de Oro' con soporte para Factores 1550 y 5085.
        Mantiene la integridad de datos mediante un patrón de Staging y prioriza 
        medidas comerciales sobre físicas según la configuración del Producto Maestro.
        """
        # Importación de constante centralizada (1550.003)
        
        # Factor específico para sistema Imperial (Pies/Ft) definido por PM
        FACTOR_BLANK_5085 = float(BLANK_CLEAR_FACTOR) 

        for lot in self:
            # 🚀 CAMBIO 4: Definimos el Salvavidas (Nominal) al inicio
            nominal = lot.volume_purchase_m3 or lot.volumen_m3 or 0.0

            # ====================================================================
            # 1. 🔒 PROTECCIÓN DE INTEGRIDAD (STAGING / MANUAL OVERRIDE)
            # ====================================================================
            # Si el registro proviene de una Recepción Certificada (Excel/PDF) y ya 
            # posee un volumen mayor a cero, preservamos el dato original de origen.
            if lot.reception_id and lot.vol_shipment_m3 > 0.001:
                continue

            # ====================================================================
            # 2. ⚙️ OBTENCIÓN Y NORMALIZACIÓN DE DIMENSIONES BASE
            # ====================================================================
            # Determinamos si el cálculo se basa en el 'Standard Comercial' del producto
            # o en las dimensiones físicas capturadas en la recepción.
            is_std = lot.product_id.use_commercial_standard
            
            # PRIORIDAD: nominal (wizard) > comercial estándar > físico
            e_mm = (
                lot.espesor_nominal_mm if lot.espesor_nominal_mm > 0
                else (lot.product_id.commercial_thickness_mm if is_std else lot.espesor_mm)
            )
            a_mm = (
                lot.ancho_nominal_mm if lot.ancho_nominal_mm > 0
                else (lot.product_id.commercial_width_mm if is_std else lot.ancho_mm)
            )
            
            # Validación de seguridad para evitar cálculos sobre registros incompletos
            if not e_mm or not a_mm or not lot.piezas:
                # 🚀 CAMBIO 5: Aplicamos Salvavidas en vez de 0.0
                lot.vol_shipment_m3 = nominal
                continue

            # ====================================================================
            # 3. 📐 CONVERSIÓN A SISTEMA IMPERIAL Y APLICACIÓN DE HOLGURA
            # ====================================================================
            # Conversión de precisión milimétrica a pulgadas (in)
            espesor_in = e_mm / float(MM_PER_INCH)
            ancho_in = a_mm / float(MM_PER_INCH)
            
            # REGLA DE HOLGURA (Overmeasure): 
            # Si el producto NO es Standard (ej. Madera Rough), sumamos 1/8" (0.125) 
            # al ancho para compensar la pérdida de volumen por cepillado.
            # Nominal fijado por wizard = valor comercial S2S → overmeasure cero
            using_nominal = (lot.espesor_nominal_mm > 0 or lot.ancho_nominal_mm > 0)
            overmeasure = 0.0 if (is_std or using_nominal) else float(get_s2s_adjustment(self.env, a_mm))
            ancho_calculo = ancho_in + overmeasure

            # ====================================================================
            # 4. 🚀 BIFURCACIÓN DE LÓGICA DE NEGOCIO (FACTOR 1550 vs 5085)
            # ====================================================================
            try:
                # 🎯 CASO A: MADERA CORTE IMPERIAL (BLANKS)
                # Si el registro posee largo en pies (largo_ft_frac), aplicamos Factor 5085.312
                if lot.largo_ft_frac:
                    # Limpieza y casting de la fracción (ej: "16'" -> 16.0)
                    largo_ft = float(lot.largo_ft_frac.replace("'", "").strip())
                    # BLANK: sin ajuste de cepillado (+1/8") — dimensiones exactas de ingesta (MADENAT-FIX-BLANK-2026-06-02)
                    vol_gold = (espesor_in * ancho_in * largo_ft * lot.piezas) / FACTOR_BLANK_5085
                
                # 🎯 CASO B: MADERA CORTE MÉTRICO (ESTÁNDAR)
                # Si no hay pies, utilizamos largo en metros y el Factor de Oro 1550.003
                else:
                    l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
                    if not l_m:
                        # 🚀 CAMBIO 6: Aplicamos Salvavidas en vez de 0.0
                        lot.vol_shipment_m3 = nominal
                        continue
                    vol_gold = (espesor_in * ancho_calculo * l_m * lot.piezas) / float(INCH_SQ_METERS_TO_M3)
                
                # ====================================================================
                # 5. ✅ CIERRE Y REDONDEO (3 DECIMALES ESTÁNDAR)
                # ====================================================================
                # 🚀 CAMBIO 7: Si por error vol_gold da 0, salvamos
                calculado = r3(vol_gold)
                lot.vol_shipment_m3 = calculado if calculado > 0 else nominal

            except (ValueError, TypeError, ZeroDivisionError):
                # Fallback de seguridad ante datos mal formateados en fracciones
                # 🚀 CAMBIO 8: Usamos Nominal en vez de 0.0
                lot.vol_shipment_m3 = nominal   

    # ==============================================================================
    # SECCIÓN 6: DIMENSIONES FINALES POST-PROCESO...
    # ==============================================================================
    espesor_nominal_mm = fields.Float(
     string='Espesor Nominal (mm)', 
     digits=(16, 3),
     help="Espesor comercial de compra (ej: 55mm). Pestaña 2."
    )

    ancho_nominal_mm = fields.Float(
        string='Ancho Nominal (mm)',
        digits=(16, 3),
        default=0.0,
        help="Ancho comercial de compra según OC. 0 = No aplica (RW - Random Width). Pestaña 2."
    )

    # ==================== CLASIFICACIÓN ====================


    thickness_final_inch = fields.Float(
        string='Espesor Final (pulg)',
        digits=(16, 3),
        help="Espesor después de cepillado/procesamiento (ej: 1.5 → 1.375)"
    )
    width_final_inch = fields.Float(
        string='Ancho Final (pulg)',
        digits=(16, 3),
        help="Ancho después de cepillado/procesamiento (ej: 5.5 → 5.25)"
    )
    # ==============================================================================
    # SECCIÓN 7: TRAZABILIDAD DE TRANSFORMACIÓN
    # ==============================================================================
    # ⚠️ TEMPORAL: Comentado hasta estabilizar metadata
  #  processing_order_id = fields.Many2one(
  #      comodel_name='lumber.processing.order',
  #      string='Orden de Procesamiento',
  #      index=True,
  #      ondelete='set null',  # ✅ ROBUSTO
  #      help="Orden de cepillado/reaserrado/secado que transformó este lote"
  #  )   
   
    processing_loss_pct = fields.Float(
        string='Pérdida por Proceso (%)',
        compute='_compute_processing_loss',
        store=True,
        digits=(16, 2),
        help="Porcentaje de pérdida dimensional: (volumen_compra - volumen_embarque) / volumen_compra × 100"
    )
    # ==============================================================================
    # SECCIÓN 8: VOLÚMENES ORIGINALES (COMPATIBILIDAD)
    # ==============================================================================
    
    volumen_m3 = fields.Float(
        string='Volumen m³', 
        compute='_compute_volumes', 
        store=True,
        digits=(16, 3),
        help="""Volumen para distribución de costos y análisis interno.
        Se calcula automáticamente según estado:
        - Pre-procesamiento: usa volume_purchase_m3
        - Post-procesamiento: usa vol_shipment_m3"""
    )
    volumen_mbf = fields.Float(
        string='Volumen MBF', 
        compute='_compute_volumes', 
        store=True,
        digits=(16, 3),
        help="UNIDAD DE FACTURACIÓN - Thousand Board Feet (1 MBF ≈ 2.36 m³)"
    )
    # ==============================================================================
    # SECCIÓN 9: TRAZABILIDAD DE ESTADO (ACTUALIZADA)
    # ==============================================================================
    
    estado_trazabilidad = fields.Selection(
        selection=[
            ('recepcionado', 'Recepcionado'),
            ('en_patio', 'En Patio'),
            ('procesado', 'Procesado/Listo Exportación'),
            ('consolidado', 'Consolidado'),
            ('embarcado', 'Embarcado')
        ],
        string='Estado Trazabilidad',
        compute='_compute_estado_trazabilidad',
        store=True,
        help="""Estado actual del lote en el flujo operativo:
        - Recepcionado: Ingresado al sistema
        - En Patio: Disponible en inventario
        - Procesado: Transformado (cepillado/reaserrado), listo para exportar
        - Consolidado: Asignado a contenedor
        - Embarcado: En tránsito o entregado""")
    # ==============================================================================
    # SECCIÓN 10.5: UBICACIÓN FÍSICA (NUEVA - TRAZABILIDAD PROFESIONAL)
    # ==============================================================================
    
    location_id = fields.Many2one(
        'stock.location',
        string='Ubicación Física',
        help='Ubicación actual del lote en el almacén (PATIO, ALMACÉN SECO, etc)',
        index=True,
    )
    # ==============================================================================
    # SECCIÓN 10: VALORIZACIÓN DE COMPRA (USD)
    # ==============================================================================
    
    purchase_price_usd_per_m3 = fields.Float(
        string='Precio Compra USD/m³',
        digits=(16, 3),
        help="Precio unitario pagado al proveedor"
    )
    purchase_exchange_rate = fields.Float(
        string='Tipo Cambio Compra',
        digits=(16, 4),
        help="Tasa CLP/USD al momento de la compra"
    )
    purchase_amount_usd = fields.Float(
        string='Monto Compra USD',
        compute='_compute_purchase_valuation',
        store=True,
        digits=(16, 2),
        help="volumen_m3 × purchase_price_usd_per_m3"
    )
    purchase_amount_clp = fields.Float(
        string='Monto Compra CLP',
        compute='_compute_purchase_valuation',
        store=True,
        digits=(16, 2),
        help="purchase_amount_usd × purchase_exchange_rate"
    )
    cost_per_m3_usd = fields.Float(
        string="Costo por m³ (USD)", 
        compute="_compute_cost_per_m3", 
        store=True,
        digits=(16, 2),
        help="Suma de los costos dividido por volumen m3"
    )
    cost_per_mbf_usd = fields.Float(
        string="Costo por MBF (USD)", 
        compute="_compute_cost_per_mbf", 
        store=True,
        digits=(16, 2),
        help="Suma de los costos dividido por volumen MBF"
    

    )
    # ==============================================================================
    # SECCIÓN 11: VALORIZACIÓN DE VENTA (USD - MBF)
    # ==============================================================================
    
    sale_price_usd_per_mbf = fields.Float(
        string='Precio Venta USD/MBF',
        digits=(16, 2),
        help="Precio de venta por MBF - Aprobado por Gerencia Comercial"
    )
    sale_amount_usd = fields.Float(
        string='Monto Venta USD',
        compute='_compute_sale_valuation',
        store=True,
        digits=(16, 2),
        help="volumen_mbf × sale_price_usd_per_mbf"
    )
    # ==============================================================================
    # SECCIÓN 12: ANÁLISIS DE MARGEN
    # ==============================================================================
    
    margin_usd = fields.Float(
        string='Margen USD',
        compute='_compute_margin',
        store=True,
        digits=(16, 2),
    )
    margin_percent = fields.Float(
        string='Margen %',
        compute='_compute_margin',
        store=True,
        digits=(16, 2),
        help="Porcentaje de margen sobre venta"
    )
    # ==============================================================================
    # SECCIÓN 13: GESTIÓN DE COSTOS
    # ==============================================================================
    
    cost_line_ids = fields.One2many(
        comodel_name='stock.lot.cost.line', 
        inverse_name='lot_id', 
        string='Líneas de Costo',
        help="Desglose detallado de costos asociados al lote"
    )
    
    # ==============================================================================
    # SECCIÓN 14: SISTEMA DE VALIDACIÓN
    # ==============================================================================
    
    technical_validation = fields.Selection(
        selection=[
            ('pending', 'Pendiente'),
            ('approved', 'Aprobado'),
            ('rejected', 'Rechazado')
        ],
        string='Validación Técnica', 
        default='pending', 
        tracking=True,
        help="Aprobación de calidad/especificaciones por Gerencia Operaciones"
    )
    financial_validation = fields.Selection(
        selection=[
            ('pending', 'Pendiente'),
            ('approved', 'Aprobado'),
            ('rejected', 'Rechazado')
        ],
        string='Validación Financiera', 
        default='pending', 
        tracking=True,
        help="Autorización de pago por Contabilidad"
    )
    
       # ============================================================================
    # CAMPO COMPUTADO: ESTADO DE FACTURACIÓN
    # ============================================================================
    
    is_billed = fields.Boolean(
        string='Facturado',
        compute='_compute_is_billed',
        store=False,
        help='Indica si este lote está incluido en una consolidación facturada'
    )
    
   
    @api.depends('name')  # Dummy depends - se recalcula cuando cambia el nombre
    def _compute_is_billed(self):
        """
        Determina si el lote está en una consolidación con estado 'billed'.
        Si está facturado, los costos NO pueden modificarse.
        
        NOTA: No usa One2many para evitar conflicto con campo inverso.
        """
        if 'lumber.billing.consolidation.line' not in self.env:
            for record in self:
                record.is_billed = False
            return

        BillingLine = self.env['lumber.billing.consolidation.line']
        
        for lot in self:
            # Buscar si existe una consolidación de facturación con este lote
            billed_consolidations = BillingLine.search([
                ('lot_id', '=', lot.id),
                ('consolidation_id.state', '=', 'billed')
            ], limit=1)
            
            lot.is_billed = bool(billed_consolidations)

  
    # ============================================================================
    # CAMPOS DE COSTOS (con protección contra edición si está facturado)
    # ============================================================================

   # Campos temporales para compatibilidad
    lot_exchange_rate = fields.Float("TC Lote", digits=(16, 3), default=0.0)
    wood_cost_usd = fields.Float(string='Costo Madera USD', default=0.0)
    purchase_cost_usd = fields.Float(string='Costo Compra USD', default=0.0)

    total_cost_usd = fields.Float(
        string="Costo Total (USD)",
        compute='_compute_total_cost_usd',
        store=False,  # ⚡ OPTIMIZACIÓN: No guardar en BD, calcular al vuelo
        help="Suma de costo madera + líneas de costo adicionales"
     )


    @api.depends('wood_cost_usd', 'purchase_cost_usd', 'cost_line_ids.amount_usd')
    def _compute_total_cost_usd(self):
        for lot in self:
            # 1. Costo Base (Madera o Compra)
            base_cost = lot.wood_cost_usd + lot.purchase_cost_usd
            
            # 2. Costos Adicionales (Líneas dinámicas)
            lines_cost = sum(lot.cost_line_ids.mapped('amount_usd'))
            
            # 3. Suma Total
            lot.total_cost_usd = base_cost + lines_cost
    
    @api.constrains('wood_cost_usd', 'purchase_cost_usd')
    def _check_cost_modification_if_billed(self):
        """
        Previene modificación de costos en lotes que ya fueron facturados.
        
        Raises:
            ValidationError: Si se intenta modificar costos de un lote facturado
        """
        for lot in self:
            if lot.is_billed:
                # Verificar si hubo cambios en los campos de costos
                if 'wood_cost_usd' in lot._origin or 'purchase_cost_usd' in lot._origin:
                    raise ValidationError(_(
                        "❌ MODIFICACIÓN BLOQUEADA\n\n"
                        "No se pueden modificar los costos del lote '%s' porque ya fue facturado.\n\n"
                        "Lote: %s\n"
                        "Estado: Facturado\n\n"
                        "Si necesita corregir costos, debe:\n"
                        "1. Cancelar la factura asociada\n"
                        "2. Modificar los costos\n"
                        "3. Volver a facturar\n\n"
                        "Contacte a Contabilidad para más información."
                    ) % (lot.name, lot.name))

    # ==============================================================================
    # MÉTODOS COMPUTADOS - SECCIÓN 1: ESCUADRÍA Y DIMENSIONES
    # ==============================================================================
      
    @api.depends('reception_id', 'guia_processing_id')
    def _compute_purchase_info(self):
        """✅ VERSIÓN SIMPLIFICADA - Solo para guías procesadas sin lote padre"""
        # Primero inicializar todos a False
        for lot in self:
            lot.purchase_order_id = False
            lot.supplier_id = False
        
        existing_lots = self.filtered(lambda l: l.id)
        if not existing_lots:
            return
        
        try:
            # 🎯 PRIORIDAD ÚNICA: Guía de procesamiento DIRECTA
            for lot in existing_lots.filtered(lambda l: l.guia_processing_id and l.guia_processing_id.order_id):
                lot.purchase_order_id = lot.guia_processing_id.order_id
                lot.supplier_id = lot.guia_processing_id.order_id.partner_id
                _logger.info(f"✅ Lote {lot.name} - OC asignada desde guía: {lot.guia_processing_id.order_id.name}")
            
            # 🎯 FALLBACK: Recepción directa (para otros casos)
            remaining_lots = existing_lots.filtered(lambda l: not l.purchase_order_id)
            for lot in remaining_lots.filtered(lambda l: l.reception_id and l.reception_id.purchase_id):
                lot.purchase_order_id = lot.reception_id.purchase_id
                lot.supplier_id = lot.reception_id.purchase_id.partner_id
                
        except Exception as e:
            _logger.warning("Error en _compute_purchase_info: %s", str(e))

    @api.depends('espesor_inch_frac', 'ancho_inch_frac', 'largo_ft_frac')
    def _compute_escuadria(self):
        """Generar escuadría en formato original ingresado"""
        for lot in self:
            parts = []
            if lot.espesor_inch_frac:
                parts.append(lot.espesor_inch_frac.strip())
            if lot.ancho_inch_frac:
                parts.append(lot.ancho_inch_frac.strip())
            if lot.largo_ft_frac:
                largo_text = lot.largo_ft_frac.strip()
                if largo_text and not largo_text.endswith("'"):
                    largo_text += "'"
                parts.append(largo_text)
            lot.escuadria = ' x '.join(parts) if parts else ''
    
    @api.depends('espesor_inch_frac', 'ancho_inch_frac', 'largo_ft_frac')
    def _compute_metric_dimensions(self):
        """Convertir dimensiones fraccionarias a métricas"""
        for lot in self:
            if lot.espesor_inch_frac:
                espesor_decimal = self._parse_fraction_to_decimal(lot.espesor_inch_frac)
                lot.espesor_mm = espesor_decimal * float(MM_PER_INCH) if espesor_decimal else 0.0
            else:
                lot.espesor_mm = 0.0
                
            if lot.ancho_inch_frac:
                ancho_decimal = self._parse_fraction_to_decimal(lot.ancho_inch_frac)
                lot.ancho_mm = ancho_decimal * float(MM_PER_INCH) if ancho_decimal else 0.0
            else:
                lot.ancho_mm = 0.0
                
            if lot.largo_ft_frac:
                largo_clean = lot.largo_ft_frac.replace("'", "").strip()
                largo_decimal = self._parse_fraction_to_decimal(largo_clean)
                lot.largo_m = largo_decimal * float(FT_TO_M) if largo_decimal else 0.0
            else:
                lot.largo_m = 0.0
    
    def _inverse_metric_dimensions(self):
        """Permitir asignación directa de dimensiones métricas"""
        pass
    
   
            
    @api.depends('volume_purchase_m3', 'vol_shipment_m3', 
             'espesor_mm', 'ancho_mm', 'largo_m', 'piezas',
             'espesor_inch_frac', 'ancho_inch_frac', 'largo_ft_frac')
    def _compute_volumes(self):
        """
        ✅ REGLA DE ORO CONSOLIDADA: Calcular m³ y MBF de forma robusta
        """
        for lot in self:
            # ====================================================================
            # 🆕 PASO 0: RESPETAR ASIGNACIÓN MANUAL (STAGING)
            # ====================================================================
            skip_compute = lot.volumen_m3 and lot.volumen_m3 > 0.0
            
            # ====================================================================
            # PASO 1 y 2: JERARQUÍA DE CÁLCULO
            # ====================================================================
            if not skip_compute:
                has_metric = all([
                    lot.espesor_mm and lot.espesor_mm > 0,
                    lot.ancho_mm and lot.ancho_mm > 0, 
                    lot.largo_m and lot.largo_m > 0,
                    lot.piezas and lot.piezas > 0
                ])

                if lot.volume_purchase_m3 and lot.volume_purchase_m3 > 0:
                    # 1ra Prioridad: Volumen de compra (Excel/PDF)
                    lot.volumen_m3 = lot.volume_purchase_m3
                elif has_metric:
                    # 2da Prioridad: Cálculo de dimensiones. 
                    # FIX: Uso de 1000.0 (float) para que 38.1mm no pierda precisión
                    vol_exacto = (lot.espesor_mm / 1000.0) * (lot.ancho_mm / 1000.0) * lot.largo_m * lot.piezas
                    lot.volumen_m3 = r3(vol_exacto)
                else:
                    # Fallback
                    lot.volumen_m3 = 0.0

            # ====================================================================
            # ✅ REGLA DE ORO: CALCULAR MBF
            # ====================================================================
            if lot.volumen_m3 > 0:
                lot.volumen_mbf = lot.volumen_m3 / 2.36
            else:
                has_fractions = all([
                    lot.espesor_inch_frac,
                    lot.ancho_inch_frac, 
                    lot.largo_ft_frac,
                    lot.piezas and lot.piezas > 0
                ])
                if has_fractions:
                    lot.volumen_mbf = self._calculate_mbf_from_fractions(
                        lot.espesor_inch_frac, lot.ancho_inch_frac, 
                        lot.largo_ft_frac, lot.piezas
                    )
                else:
                    lot.volumen_mbf = 0.0

            # ====================================================================
            # ✅ GARANTIZAR PRECISIÓN FINAL (3 Decimales)
            # ====================================================================
            if lot.volumen_m3 > 0:
                lot.volumen_m3 = r3(lot.volumen_m3)
            if lot.volumen_mbf > 0:
                lot.volumen_mbf = r3(lot.volumen_mbf)
    # ==============================================================================
    # MÉTODOS COMPUTADOS - SECCIÓN 2: GENEALOGÍA ⭐ NUEVO
    # ==============================================================================
    
    @api.depends('parent_lot_id', 'parent_lot_id.generation_level')
    def _compute_generation_level(self):
        """Calcular nivel jerárquico del lote"""
        for lot in self:
            if not lot.parent_lot_id:
                lot.generation_level = 0
            else:
                lot.generation_level = lot.parent_lot_id.generation_level + 1
    
    # ==============================================================================
    # MÉTODOS COMPUTADOS - SECCIÓN 3: VOLUMEN DUAL Y PÉRDIDA
    # ==============================================================================
    
    @api.depends('volume_purchase_m3', 'vol_shipment_m3')
    def _compute_processing_loss(self):
        """Calcular porcentaje de pérdida por procesamiento"""
        for lot in self:
            if lot.volume_purchase_m3 > 0:
                loss = lot.volume_purchase_m3 - lot.vol_shipment_m3
                lot.processing_loss_pct = (loss / lot.volume_purchase_m3) * 100
            else:
                lot.processing_loss_pct = 0.0
    
    # ==============================================================================
    # MÉTODOS COMPUTADOS - SECCIÓN 4: ESTADO Y TRAZABILIDAD
    # ==============================================================================
    @api.depends('reception_id', 'parent_lot_id', 'guia_processing_id', 'subproducto_id')
    def _compute_estado_trazabilidad(self):
        """✅ NUEVA LÓGICA ROBUSTA: Calcular estado considerando múltiples indicadores de procesado"""
        for lot in self:
            if not lot.reception_id:
                lot.estado_trazabilidad = False
                continue
            
            # ✅ REGLA DE ORO: Múltiples indicadores de "procesado" sin hardcode
            if lot._is_processed_lot():
                lot.estado_trazabilidad = 'procesado'
                continue
            
            # ✅ MANTENER funcionalidad existente de embarque/consolidación
            try:
                Container = self.env['lumber.container'].sudo()
                container = Container.search([
                    ('lot_ids', 'in', lot.id)
                ], limit=1)
                
                if container and container.shipment_id:
                    shipment_state = container.shipment_id.state
                    if shipment_state in ['in_transit', 'delivered']:
                        lot.estado_trazabilidad = 'embarcado'
                    elif shipment_state in ['confirmed', 'loading']:
                        lot.estado_trazabilidad = 'consolidado'
                    else:
                        lot.estado_trazabilidad = 'en_patio'
                elif container:
                    lot.estado_trazabilidad = 'consolidado'
                else:
                    try:
                        if lot.reception_id.state == 'done':
                            lot.estado_trazabilidad = 'en_patio'
                        else:
                            lot.estado_trazabilidad = 'recepcionado'
                    except AttributeError:
                        lot.estado_trazabilidad = 'en_patio'
            except KeyError:
                try:
                    if lot.reception_id.state == 'done':
                        lot.estado_trazabilidad = 'en_patio'
                    else:
                        lot.estado_trazabilidad = 'recepcionado'
                except AttributeError:
                    lot.estado_trazabilidad = 'recepcionado'
    def _is_processed_lot(self):
        """
        ✅ REGLA DE ORO: Detectar si un lote está procesado usando múltiples indicadores
        Sin hardcode, manteniendo flexibilidad para el negocio.

        CORRECCIÓN TD-006 (2026-05-31):
        - subproducto_id por sí solo NO indica procesamiento.
        - Un lote de recepción con subproducto (ej: BLANK CLEAR) sigue disponible para contenedor.
        - Solo guía_processing_id, parent_lot_id o dimensiones finales indican procesamiento real.
        """
        # Indicador 1: Tiene guía de procesamiento asociada
        if self.guia_processing_id:
            return True

        # Indicador 2: Tiene lote padre (transformación tradicional) - MANTENER compatibilidad
        if self.parent_lot_id:
            return True

        # Indicador 3: subproducto_id SOLAMENTE no indica procesamiento.
        # Un lote de recepción con subproducto (BLANK CLEAR, RIP, etc.) sigue en patio
        # y es asignable a contenedor. El subproducto es clasificación comercial, no estado.
        # ✅ REMOVIDO: "if self.subproducto_id: return True"

        # Indicador 4: Tiene dimensiones finales post-procesamiento
        if self.thickness_final_inch > 0 or self.width_final_inch > 0:
            return True

        # Indicador 5: Tiene volumen de embarque diferente al de compra
        if (self.vol_shipment_m3 > 0 and
            self.volume_purchase_m3 > 0 and
            self.vol_shipment_m3 != self.volume_purchase_m3):
            return True

        return False
    # ==============================================================================
    # MÉTODOS COMPUTADOS - SECCIÓN 5: VALORIZACIÓN Y COSTOS
    # ==============================================================================
    @api.depends('volumen_m3', 'purchase_price_usd_per_m3', 'purchase_exchange_rate')
    def _compute_purchase_valuation(self):
        """Calcular valorización de compra"""
        for lot in self:
            lot.purchase_amount_usd = lot.volumen_m3 * lot.purchase_price_usd_per_m3
            lot.purchase_amount_clp = lot.purchase_amount_usd * lot.purchase_exchange_rate

    @api.depends('volumen_mbf', 'sale_price_usd_per_mbf')
    def _compute_sale_valuation(self):
        """Calcular valorización de venta"""
        for lot in self:
            lot.sale_amount_usd = lot.volumen_mbf * lot.sale_price_usd_per_mbf

    @api.depends('sale_amount_usd', 'total_cost_usd')
    def _compute_margin(self):
        """Calcular margen de contribución"""
        for lot in self:
            lot.margin_usd = lot.sale_amount_usd - lot.total_cost_usd
            if lot.sale_amount_usd > 0:
                lot.margin_percent = (lot.margin_usd / lot.sale_amount_usd) * 100
            else:
                lot.margin_percent = 0.0

    @api.depends('cost_line_ids.amount_usd', 'cost_line_ids.cost_type', 'volumen_m3')
    def _compute_cost_per_m3(self):
        """Costo por metro cúbico"""
        for lot in self:
            total_cost = sum(line.amount_usd for line in lot.cost_line_ids)
            if lot.volumen_m3 > 0:
                lot.cost_per_m3_usd = total_cost / lot.volumen_m3
            else:
                lot.cost_per_m3_usd = 0.0

    @api.depends('cost_line_ids.amount_usd', 'cost_line_ids.cost_type', 'volumen_mbf')
    def _compute_cost_per_mbf(self):
        """Costo por MBF"""
        for lot in self:
            total_cost = sum(line.amount_usd for line in lot.cost_line_ids)
            if lot.volumen_mbf > 0:
                lot.cost_per_mbf_usd = total_cost / lot.volumen_mbf
            else:
                lot.cost_per_mbf_usd = 0.0

    def _parse_fraction_to_decimal(self, fraction_str):
            """
            🚀 PARSER INTELIGENTE (Bilingüe MM/Pulgadas):
            Evita que el motor multiplique milímetros como si fueran pulgadas gigantes.
            """
            if not fraction_str:
                return 0.0
                
            fraction_str = str(fraction_str).strip().lower()
            
            try:
                # 🛡️ INTERCEPCIÓN EXPLÍCITA: Si trae la etiqueta 'mm' (ej: "195mm")
                if 'mm' in fraction_str:
                    val = float(fraction_str.replace('mm', '').strip())
                    return val / float(MM_PER_INCH)  # Convertimos a pulgadas para la fórmula del motor
                    
                # Caso 1: Número decimal simple o entero (ej: "195" o "2.5")
                if '/' not in fraction_str and ' ' not in fraction_str:
                    val = float(fraction_str)
                    
                    # 🧠 HEURÍSTICA DE PROTECCIÓN (Sentido Común):
                    # Ninguna tabla de madera comercial mide más de 24 pulgadas (60cm) de ancho.
                    # Si el valor es mayor a 24, es ABSOLUTAMENTE SEGURO que son milímetros.
                    if val > 24:
                        return val / float(MM_PER_INCH)
                        
                    return val
                
                # Caso 2: Solo fracción ("5/8")
                if '/' in fraction_str and ' ' not in fraction_str:
                    numerator, denominator = fraction_str.split('/')
                    return float(numerator) / float(denominator)
                
                # Caso 3: Número mixto ("4 5/8")
                if ' ' in fraction_str and '/' in fraction_str:
                    parts = fraction_str.split(' ')
                    whole_part = float(parts[0])
                    num, den = parts[1].split('/')
                    return whole_part + (float(num) / float(den))
                    
            except Exception as e:
                # Silenciamos el logger para no ensuciar, retornamos 0 de forma segura
                return 0.0
    
    # ==============================================================================
    # UTILIDADES - CÁLCULO DE MBF
    # ==============================================================================
    
    def _calculate_mbf_from_fractions(self, thickness_frac, width_frac, length_frac, pieces):
        """Calcular MBF desde fracciones directamente (método más preciso)"""
        try:
            if not all([thickness_frac, width_frac, length_frac, pieces]):
                return 0.0
            
            thickness_inch = self._parse_fraction_to_decimal(thickness_frac)
            width_inch = self._parse_fraction_to_decimal(width_frac)
            length_clean = length_frac.replace("'", "").strip()
            length_feet = self._parse_fraction_to_decimal(length_clean)
            
            if not all([thickness_inch, width_inch, length_feet]):
                return 0.0
            
            board_feet = (thickness_inch * width_inch * length_feet * pieces) / 12
            mbf = board_feet / 1000
            
            return round(mbf, 4)
            
        except Exception as e:
            _logger.warning("Error calculando MBF desde fracciones: %s", str(e))
            return 0.0
    
    def _calculate_mbf_from_metrics(self, thickness_mm, width_mm, length_m, pieces):
        """Calcular MBF desde dimensiones métricas (método fallback)"""
        try:
            if not all([thickness_mm, width_mm, length_m, pieces]):
                return 0.0
                
            thickness_inch = thickness_mm / float(MM_PER_INCH)
            width_inch = width_mm / float(MM_PER_INCH)
            length_feet = length_m * float(M_TO_FT)
            
            board_feet = (thickness_inch * width_inch * length_feet * pieces) / 12
            mbf = board_feet / 1000
            
            return round(mbf, 4)
            
        except Exception as e:
            _logger.warning("Error calculando MBF desde métricas: %s", str(e))
            return 0.0

    # ==============================================================================
    # VALIDACIONES Y RESTRICCIONES
    # ==============================================================================
    
    @api.constrains('volumen_mbf')
    def _check_mbf_positive(self):
        """Validar que MBF sea positivo"""
        for lot in self:
            if lot.volumen_mbf < 0:
                raise ValidationError(
                    _("Lote %s: El volumen MBF no puede ser negativo") % lot.name
                )
    @api.constrains('purchase_price_usd_per_m3')
    def _check_purchase_price(self):
        """Validar precio de compra"""
        for lot in self:
            if lot.purchase_amount_usd > 0 and lot.purchase_price_usd_per_m3 <= 0:
                raise ValidationError(
                    _("Lote %s: Debe especificar un precio de compra USD/m³ válido") % lot.name
                )
    # ==============================================================================
    # MÉTODOS DE CICLO DE VIDA
    # ==============================================================================
    
    def unlink(self):
        """Limpiar líneas de costo antes de eliminar lotes"""
        for lot in self:
            if lot.cost_line_ids:
                lot.cost_line_ids.unlink()
        
        return super(StockLotExtended, self).unlink()

    # ==============================================================================
    # MÉTODOS DE ACCIÓN (BOTONES)
    # ==============================================================================
    
    def action_approve_technical(self):
        """Aprobar validación técnica"""
        self.write({'technical_validation': 'approved'})
        self.message_post(body=_("Validación técnica aprobada"), message_type='notification')
        return True

    def action_reject_technical(self):
        """Rechazar validación técnica"""
        self.write({'technical_validation': 'rejected'})
        self.message_post(body=_("Validación técnica rechazada"), message_type='notification')
        return True

    def action_approve_financial(self):
        """Aprobar validación financiera"""
        self.write({'financial_validation': 'approved'})
        self.message_post(body=_("Validación financiera aprobada"), message_type='notification')
        return True

    def action_reject_financial(self):
        """Rechazar validación financiera"""
        self.write({'financial_validation': 'rejected'})
        self.message_post(body=_("Validación financiera rechazada"), message_type='notification')
        return True

    def action_view_lot_genealogy(self):
        """Ver árbol genealógico del lote (padres, hijos y descendientes)"""
        self.ensure_one()
        
        # Recopilar todos los lotes relacionados
        all_lots = self | self.parent_lot_id | self.child_lot_ids
        
        # Buscar recursivamente todos los ancestros
        current = self.parent_lot_id
        while current:
            all_lots |= current
            current = current.parent_lot_id
        
        # Buscar recursivamente todos los descendientes
        def get_descendants(lot):
            descendants = lot.child_lot_ids
            for child in lot.child_lot_ids:
                descendants |= get_descendants(child)
            return descendants
        
        all_lots |= get_descendants(self)
        
        return {
            'name': _('Genealogía de Lotes'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', all_lots.ids)],
            'context': {'default_parent_lot_id': self.id},
        }
    
    # ==============================================================================
    # ✅ MEJORAS ADICIONALES PARA ROBUSTEZ - INSERTAR AQUÍ
    # ==============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """✅ MEJORA: Sobrescribir create para garantizar estado correcto en nuevos lotes"""
        new_lots = super().create(vals_list)
        
        for new_lot in new_lots:
            # ✅ SI es lote procesado y el estado no se computó correctamente
            if (new_lot.guia_processing_id or new_lot.parent_lot_id or new_lot.subproducto_id):
                if new_lot.estado_trazabilidad != 'procesado':
                    _logger.info("🔄 Ajustando estado a 'procesado' para nuevo lote %s", new_lot.name)
                    new_lot.estado_trazabilidad = 'procesado'
        
        return new_lots

    def write(self, vals):
        """✅ MEJORA: Manejar cambios que puedan afectar el estado de procesado"""
        result = super(StockLotExtended, self).write(vals)
        
        # ✅ SI se agregó indicador de procesado, actualizar estado
        if any(field in vals for field in ['guia_processing_id', 'parent_lot_id', 'subproducto_id']):
            processed_lots = self.filtered(lambda l: l._is_processed_lot())
            if processed_lots:
                processed_lots.write({'estado_trazabilidad': 'procesado'})
        
        return result



class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # --- CAMPOS DE AUDITORÍA MADENAT (Consolidados) ---
    
    reception_name = fields.Char(
        related='lot_id.reception_id.name',
        string='N° de Guía',
        readonly=True, store=False
    )

    reception_date = fields.Datetime(
        related='lot_id.reception_id.reception_date',
        string='Fecha Guía',
        readonly=True, store=False
    )

    supplier_id = fields.Many2one(
        related='lot_id.supplier_id',
        string='Proveedor',
        readonly=True, store=False
    )

    # 🚀 REGLA DE ORO: Sincronización de volumen real para evitar el error visual
    # Al ser un related de 'quantity', la columna "Diferencia" cuadrará perfecto.
    volumen_sistema_m3 = fields.Float(
        string='M3 Sistema',
        related='quantity', 
        readonly=True,
        store=False
    )

    subproducto_id = fields.Many2one(related='lot_id.subproducto_id', string='Subproducto', readonly=True)
    etiqueta_limpia = fields.Char(related='lot_id.ref', string='Etiqueta Lote', readonly=True)