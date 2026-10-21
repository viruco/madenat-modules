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
from odoo.exceptions import UserError, ValidationError
from psycopg2 import errors as psycopg2_errors
import logging
from .utils_uom import (
    INCH_SQ_METERS_TO_M3, r3, r4, BLANK_CLEAR_FACTOR,
    MM_PER_INCH, FT_TO_M, M_TO_FT, parse_fraction_to_decimal_inch,
    ROUGH_THICKNESS_6_4_MM, NOMINAL_EXPORT_THICKNESS_6_4_INCHES, M3_DIVISOR,
)
from .width_mapping import WidthMappingTable


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
    
    # === SECADO EN HORNO (Bloque 4D-1 / AD-116 / F6) ===
    drying_temp_c = fields.Float(
        string="Temp. Secado (°C)",
        copy=False,
        digits=(6, 1),
        help="Temperatura de secado en horno (rango parametrizable en madenat.drying_temp_min_c/max_c).",
    )
    drying_duration_hours = fields.Float(
        string="Duración Secado (h)",
        copy=False,
        digits=(6, 1),
        help="Duración del proceso de secado en horno en horas (rango parametrizable en madenat.drying_duration_min_hours/max_hours).",
    )
    drying_date = fields.Date(
        string="Fecha Secado",
        copy=False,
        help="Fecha en que se completó el ciclo de secado en horno.",
    )

    @api.constrains('drying_temp_c', 'drying_duration_hours')
    def _check_drying_parameters(self):
        config = self.env['madenat.ingestion.config']
        temp_min, temp_max = config.get_drying_temp_range()
        dur_min, dur_max = config.get_drying_duration_range()
        for lot in self:
            if lot.drying_temp_c and (lot.drying_temp_c < temp_min or lot.drying_temp_c > temp_max):
                raise ValidationError(_(
                    "Temperatura de secado fuera de rango permitido: %.1f °C (rango: %.1f - %.1f °C)."
                ) % (lot.drying_temp_c, temp_min, temp_max))
            if lot.drying_duration_hours and (lot.drying_duration_hours < dur_min or lot.drying_duration_hours > dur_max):
                raise ValidationError(_(
                    "Duración de secado fuera de rango permitido: %.1f h (rango: %.1f - %.1f h)."
                ) % (lot.drying_duration_hours, dur_min, dur_max))


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

    # 🏷️ F3.1 — Identidad DOCUMENTAL permanente del Lote Volumen.
    # Identifica la guía de ingreso por volumen que originó el lote. Es
    # inmutable (no se limpia ni se reasigna) y sobrevive a la reapertura de
    # la guía, a diferencia de `guia_processing_id` (relación operativa que
    # action_reopen_to_draft() limpia). `ondelete='restrict'` impide que la
    # eliminación de la guía destruya la identidad del lote.
    volume_source_guia_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía Origen de Volumen',
        readonly=True,
        copy=False,
        index=True,
        ondelete='restrict',
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
    # 🏷️ F3.1 — Tipo de flujo operativo persistente del lote.
    # 'tarja'  = lotes identificados por etiqueta física del proveedor (tarja).
    # 'volume' = Lotes Volumen del ingreso por volumen: identidad propia
    #            `stock.lot.name` = SV + 11 dígitos (secuencia
    #            `madenat.volume.lot`) y guía origen documental obligatoria.
    # Los lotes históricos (incluidos los `GRANEL <sufijo>`) quedan sin tipo.
    lot_flow_type = fields.Selection(
        [
            ('tarja', 'Tarja'),
            ('volume', 'Lote Volumen'),
        ],
        string='Tipo de flujo de lote',
        index=True,
        copy=False,
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

    # Bloque 5B (AD-126): Volumen Real Físico (Fórmula F3)
    vol_physical_real_m3 = fields.Float(
        string='Volumen Real Físico (m³)',
        compute='_compute_vol_physical_real_m3',
        store=True,
        digits=(16, 3),
        help="Volumen físico real (F3): Espesor real (mm) × Ancho nominal (mm) × Largo (m) × Piezas / 1.000.000"
    )
    # Bloque 5D (AD-126): Estado del cálculo de Real Físico
    physical_status = fields.Selection(
        selection=[
            ('calculado', 'Calculado (F3)'),
            ('sin_mapeo', 'Sin Mapeo'),
            ('no_aplica', 'No Aplica'),
        ],
        string="Estado Real Físico",
        compute='_compute_vol_physical_real_m3',
        store=True,
        default='no_aplica',
        help="Estado del cálculo de volumen real físico (F3): 'calculado' cuando existe mapeo, 'sin_mapeo' cuando falta espesor real, 'no_aplica' en blanks o perfiles sin F3."
    )

    # Bloque 5C (AD-126): Métricas Comparativas de Tres Volúmenes
    vol_purchase_m3 = fields.Float(
        string='Volumen Compra Nominal (m³)',
        compute='_compute_vol_purchase_alias',
        inverse='_inverse_vol_purchase_alias',
        digits=(16, 3),
        help="Alias de volume_purchase_m3 para compatibilidad y coherencia analítica"
    )
    vol_diff_pct = fields.Float(
        string="% Dif. Vol",
        compute='_compute_vol_comparison_metrics',
        store=True,
        digits=(16, 2),
        help="Diferencia porcentual entre Exportación y Compra Nominal: ((Exportación - Compra) / Compra) * 100"
    )
    vol_physical_diff_pct = fields.Float(
        string="% Dif. Real Físico",
        compute='_compute_vol_comparison_metrics',
        store=True,
        digits=(16, 2),
        help="Diferencia porcentual del volumen real físico respecto al nominal de compra: ((Real Físico - Compra) / Compra) * 100 si physical_status == 'calculado', de lo contrario False."
    )
    is_export_greater_nominal = fields.Boolean(
        string="Alerta: Exportación > Compra",
        compute='_compute_vol_comparison_metrics',
        store=True,
        index=True,
        help="Indica si el volumen de exportación supera al nominal de compra (inconsistencia potencial)"
    )
    motonave_name = fields.Char(
        string="Motonave",
        readonly=True,
        index=True,
        help="Nombre de la motonave o buque asignado cuando el dato exista"
    )

    # Punto 2.5 (AD-130): Control del packing a nivel de lote
    vol_documental_m3 = fields.Float(
        string='Volumen Documental (m³)',
        digits=(16, 6),
        help='Volumen declarado por línea en el Packing de origen.'
    )
    reconciliation_status = fields.Selection([
        ('none', 'Sin Dato Documental'),
        ('match', 'Coincide'),
        ('tolerance', 'Diferencia dentro de Tolerancia'),
        ('review', 'Revisar'),
    ], string='Conciliación Packing', compute='_compute_reconciliation_status', store=True,
       help='Estado de conciliación entre volumen documental declarado en packing y volumen de embarque')

    # Punto 2.6 - 2.8 (AD-130): Ancho manual, fuera de tabla y display S2S
    export_width_manual_inches = fields.Float(
        string='Ancho Manual Export (in)',
        digits=(16, 4),
        help='Ancho de exportación en pulgadas ingresado manualmente en caso de estar fuera de tabla.'
    )
    export_width_manual_reason = fields.Char(
        string='Motivo Ancho Manual',
        help='Motivo obligatorio por el cual se asigna un ancho manual de exportación.'
    )
    export_width_manual_user_id = fields.Many2one(
        'res.users',
        string='Usuario Ancho Manual',
        readonly=True,
    )
    export_width_manual_date = fields.Datetime(
        string='Fecha Ancho Manual',
        readonly=True,
    )
    is_out_of_table = fields.Boolean(
        string="Fuera de Tabla S2S",
        compute="_compute_out_of_table_status",
        store=True,
    )
    out_of_table_status = fields.Selection([
        ('in_table', 'En Tabla S2S'),
        ('out_of_table', 'ancho fuera de tabla: confirmar'),
        ('confirmed', 'Confirmado Manual'),
        ('not_applicable', 'No Aplica'),
    ], string="Estado S2S", compute="_compute_out_of_table_status", store=True)

    ancho_export_display = fields.Char(
        string='Ancho Export',
        compute='_compute_ancho_export_display',
        store=True,
        help="Ancho nominal de exportación S2S (ej: 150 mm → 5 5/8\")."
    )

    @api.constrains('export_width_manual_inches', 'export_width_manual_reason')
    def _check_manual_export_width(self):
        for lot in self:
            if (lot.export_width_manual_inches or 0.0) > 0:
                if not (lot.export_width_manual_reason and lot.export_width_manual_reason.strip()):
                    raise ValidationError(_(
                        "El motivo de captura manual de ancho es obligatorio cuando se especifica un ancho manual."
                    ))

    @api.depends('ancho_mm', 'ancho_nominal_mm', 'subproducto_id', 'largo_ft_frac',
                 'export_width_manual_inches', 'export_width_manual_reason')
    def _compute_out_of_table_status(self):
        config = self.env['madenat.ingestion.config']
        s2s_map = config.get_width_s2s_map(include_overwidth=False)
        for lot in self:
            family = getattr(lot.subproducto_id, 'calculation_family', False)
            if family in ('blank', 'rough') or bool(lot.largo_ft_frac):
                lot.out_of_table_status = 'not_applicable'
                lot.is_out_of_table = False
                continue

            w_mm = lot.ancho_nominal_mm or lot.ancho_mm or 0.0
            if not w_mm or w_mm <= 0:
                lot.out_of_table_status = 'not_applicable'
                lot.is_out_of_table = False
                continue

            w_key = int(round(w_mm))
            in_table = (w_key in s2s_map)

            if in_table:
                lot.out_of_table_status = 'in_table'
                lot.is_out_of_table = False
            else:
                lot.is_out_of_table = True
                manual_in = lot.export_width_manual_inches or 0.0
                manual_reason = lot.export_width_manual_reason or ''
                if manual_in > 0 and manual_reason.strip():
                    lot.out_of_table_status = 'confirmed'
                else:
                    lot.out_of_table_status = 'out_of_table'

    @api.depends('ancho_mm', 'ancho_nominal_mm', 'width_visual',
                 'export_width_manual_inches', 'subproducto_id', 'largo_ft_frac')
    def _compute_ancho_export_display(self):
        config = self.env['madenat.ingestion.config']
        for lot in self:
            w_mm = lot.ancho_nominal_mm or lot.ancho_mm or 0.0
            if w_mm > 0:
                details = config.resolve_export_width_details(
                    rough_mm=w_mm,
                    record=lot,
                    width_visual=lot.width_visual,
                )
                lot.ancho_export_display = details.get('nominal_width_display') or details.get('nominal_width_label') or f"{details.get('nominal_width_inches', 0.0):.3f}\""
            else:
                lot.ancho_export_display = ""

    @api.depends('vol_documental_m3', 'vol_shipment_m3')
    def _compute_reconciliation_status(self):
        for lot in self:
            v_doc = lot.vol_documental_m3 or 0.0
            v_calc = lot.vol_shipment_m3 or 0.0
            if v_doc <= 0.0001 or v_calc <= 0.0001:
                lot.reconciliation_status = 'none'
            else:
                diff = abs(v_doc - v_calc)
                if diff < 0.001:
                    lot.reconciliation_status = 'match'
                elif diff <= 0.010:
                    lot.reconciliation_status = 'tolerance'
                else:
                    lot.reconciliation_status = 'review'

    def _compute_vol_purchase_alias(self):
        for rec in self:
            rec.vol_purchase_m3 = rec.volume_purchase_m3 or rec.volumen_m3 or 0.0

    def _inverse_vol_purchase_alias(self):
        for rec in self:
            rec.volume_purchase_m3 = rec.vol_purchase_m3

    @api.depends(
        'product_id.use_commercial_standard',
        'product_id.commercial_thickness_mm',
        'product_id.commercial_width_mm',
        'product_id.commercial_length_m',
        'espesor_mm', 'ancho_mm', 'largo_m',
        'largo_ft_frac', 'piezas', 'reception_id',
        'export_width_manual_inches',
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
            # Salvaguarda de staging (R5/D6): registros de recepción con volumen preservados,
            # salvo bypass explícito controlado (AD-131 / Fase 5).
            if lot.reception_id and lot.vol_shipment_m3 > 0.001:
                if not self.env.context.get('bypass_staging_safeguard'):
                    continue

            # ====================================================================
            # 2. ⚙️ OBTENCIÓN Y NORMALIZACIÓN DE DIMENSIONES BASE
            # ====================================================================
            is_std = getattr(lot.product_id, 'use_commercial_standard', False)
            comm_t = getattr(lot.product_id, 'commercial_thickness_mm', 0.0) if is_std else 0.0
            comm_w = getattr(lot.product_id, 'commercial_width_mm', 0.0) if is_std else 0.0
            
            # PRIORIDAD: nominal (wizard) > comercial estándar > físico
            e_mm = (
                lot.espesor_nominal_mm if lot.espesor_nominal_mm > 0
                else (comm_t if comm_t > 0 else lot.espesor_mm)
            )
            a_mm = (
                lot.ancho_nominal_mm if lot.ancho_nominal_mm > 0
                else (comm_w if comm_w > 0 else lot.ancho_mm)
            )
            
            if not e_mm or not a_mm or not lot.piezas:
                lot.vol_shipment_m3 = nominal
                continue

            # ====================================================================
            # 3. 📐 RESOLUCIÓN DE ANCHO Y ESPESOR VÍA API ÚNICA (H4 / AD-130)
            # ====================================================================
            subprod = lot.subproducto_id
            family = getattr(subprod, 'calculation_family', False)
            is_blank = (family == 'blank' or bool(lot.largo_ft_frac))

            # Espesor de exportación en pulgadas (nominal 1.5" para 6/4 salvo especificación)
            if lot.thickness_visual:
                t_exp_in = parse_fraction_to_decimal_inch(lot.thickness_visual)
            elif lot.reception_thickness_in > 0:
                t_exp_in = lot.reception_thickness_in
            elif abs(e_mm - float(ROUGH_THICKNESS_6_4_MM)) < 1.0:
                t_exp_in = float(NOMINAL_EXPORT_THICKNESS_6_4_INCHES)
            else:
                t_exp_in = e_mm / float(MM_PER_INCH)

            config = self.env['madenat.ingestion.config']
            is_s2s = getattr(lot, 'is_s2s_inches', False) or is_blank
            details = config.resolve_export_width_details(
                rough_mm=a_mm,
                record=lot,
                is_s2s_inches=is_s2s,
            )
            ancho_calculo = details['calc_width_inches']

            # ====================================================================
            # 4. 🚀 BIFURCACIÓN DE LÓGICA DE NEGOCIO POR FAMILIA (H4)
            # ====================================================================
            try:
                # 🎯 CASO A: BLANKS (F5085 con +1/8", compra = exportación)
                if is_blank:
                    if lot.largo_ft_frac:
                        largo_ft = float(str(lot.largo_ft_frac).replace("'", "").strip())
                    else:
                        l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
                        largo_ft = l_m / float(FT_TO_M) if l_m else 0.0

                    vol_gold = (t_exp_in * ancho_calculo * largo_ft * lot.piezas) / FACTOR_BLANK_5085

                # 🎯 CASO B: RUGOSO / ASERRADA JCE (Métrico puro, compra = exportación)
                elif family == 'rough':
                    l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
                    if not l_m:
                        lot.vol_shipment_m3 = nominal
                        continue
                    vol_gold = (e_mm * a_mm * l_m * lot.piezas) / float(M3_DIVISOR)

                # 🎯 CASO C: CEPILLADO RIP S2S (F1550 con +1/8" según tabla S2S)
                else:
                    l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
                    if not l_m:
                        lot.vol_shipment_m3 = nominal
                        continue
                    vol_gold = (t_exp_in * ancho_calculo * l_m * lot.piezas) / float(INCH_SQ_METERS_TO_M3)

                # ====================================================================
                # 5. ✅ CIERRE Y REDONDEO (3 DECIMALES ESTÁNDAR)
                # ====================================================================
                calculado = r3(vol_gold)
                lot.vol_shipment_m3 = calculado if calculado > 0 else nominal

            except (ValueError, TypeError, ZeroDivisionError):
                lot.vol_shipment_m3 = nominal   

    @api.depends('thickness_visual', 'espesor_nominal_mm', 'espesor_mm', 'ancho_nominal_mm',
                 'ancho_mm', 'largo_m', 'largo_ft_frac', 'piezas')
    def _compute_vol_physical_real_m3(self):
        """Calcula el Volumen Real Físico (m³) para el lote según Fórmula F3 (AD-126 / Bloque 5B/5D).

        F3: espesor_real_mm × ancho_nominal_mm × largo_m × piezas / 1.000.000
        No se calcula para Blanks directo a stock ni para perfiles donde no aplique.
        Redondeado una sola vez con r3() (ROUND_HALF_UP).
        Registra physical_status: 'calculado', 'sin_mapeo', 'no_aplica'.
        """
        for lot in self:
            if lot.largo_ft_frac:
                lot.vol_physical_real_m3 = 0.0
                lot.physical_status = 'no_aplica'
                continue

            piezas = lot.piezas or 0
            if piezas <= 0:
                lot.vol_physical_real_m3 = 0.0
                lot.physical_status = 'no_aplica'
                continue

            # Ancho nominal en mm: prioridad ancho_nominal_mm > ancho_mm
            w_mm = lot.ancho_nominal_mm if lot.ancho_nominal_mm > 0 else lot.ancho_mm
            l_m = lot.largo_m
            if not w_mm or w_mm <= 0 or not l_m or l_m <= 0:
                lot.vol_physical_real_m3 = 0.0
                lot.physical_status = 'no_aplica'
                continue

            # Obtener espesor real en mm desde lumber.thickness.real.map
            e_real_mm = None
            thick_vis = getattr(lot, 'thickness_visual', None)
            if thick_vis:
                e_real_mm = self.env['madenat.ingestion.config'].get_thickness_real_mm(
                    thickness_visual=thick_vis
                )
            if not e_real_mm and lot.espesor_nominal_mm and lot.espesor_nominal_mm > 0:
                thick_in = lot.espesor_nominal_mm / 25.4
                e_real_mm = self.env['madenat.ingestion.config'].get_thickness_real_mm(
                    thickness_inches=thick_in
                )

            if not e_real_mm or e_real_mm <= 0:
                lot.vol_physical_real_m3 = 0.0
                lot.physical_status = 'sin_mapeo'
                continue

            vol_f3 = (e_real_mm * w_mm * l_m * piezas) / 1000000.0
            lot.vol_physical_real_m3 = r3(vol_f3)
            lot.physical_status = 'calculado'

    @api.depends('volume_purchase_m3', 'volumen_m3', 'vol_shipment_m3', 'vol_physical_real_m3', 'physical_status')
    def _compute_vol_comparison_metrics(self):
        """Calcula métricas de comparación (Bloque 5C / 5D):

        - vol_diff_pct: ((Exportación - Compra) / Compra) * 100 si nom > 0, disponible aunque
          el real físico no esté calculado (como en la planilla).
        - vol_physical_diff_pct: ((Real Físico - Compra) / Compra) * 100 si physical_status == 'calculado',
          de lo contrario False (vacía).
        - is_export_greater_nominal: Exportación > Compra (con tolerancia 0.0005 m3)
        """
        for rec in self:
            nom = rec.volume_purchase_m3 or rec.volumen_m3 or 0.0
            exp = rec.vol_shipment_m3 or 0.0
            real = rec.vol_physical_real_m3 or 0.0
            status = getattr(rec, 'physical_status', 'no_aplica')

            if nom > 0:
                rec.vol_diff_pct = round(((exp - nom) / nom) * 100.0, 2)
            else:
                rec.vol_diff_pct = False

            if status == 'calculado' and nom > 0:
                rec.vol_physical_diff_pct = round(((real - nom) / nom) * 100.0, 2)
            else:
                rec.vol_physical_diff_pct = False

            rec.is_export_greater_nominal = bool(exp > (nom + 0.0005))

    # ==============================================================================
    # SECCIÓN 6: DIMENSIONES FINALES POST-PROCESO...
    # ==============================================================================
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
    volumen_restante_m3 = fields.Float(
        string='Volumen Remanente (m³)',
        compute='_compute_volumen_restante_m3',
        store=True,
        digits=(16, 3),
        help='Volumen físico real disponible en stock, calculado desde stock.quant.quantity '
             '(no desde volumen_m3, que es el volumen documental de origen y no se ajusta '
             'tras consumos parciales — ver AD-67). Útil para distinguir volumen original '
             'de volumen realmente disponible tras un envío parcial a proceso (AD-66).'
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
      
    # HOMOLOGACIÓN OC 2026-06-21: depends extendido para reflejar dependencias reales del método
    @api.depends(
        'reception_id', 'reception_id.purchase_id', 'reception_id.supplier_id',
        'guia_processing_id', 'guia_processing_id.order_id',
    )
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
            for lot in remaining_lots.filtered(lambda l: l.reception_id):
                if lot.reception_id.purchase_id:
                    lot.purchase_order_id = lot.reception_id.purchase_id
                lot.supplier_id = lot.reception_id.supplier_id or (lot.reception_id.purchase_id and lot.reception_id.purchase_id.partner_id)
                
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

    @api.depends('quant_ids.quantity', 'quant_ids.location_id')
    def _compute_volumen_restante_m3(self):
        """Volumen físico remanente = suma de stock.quant.quantity en ubicaciones internas."""
        for lot in self:
            quants = lot.quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
            lot.volumen_restante_m3 = sum(quants.mapped('quantity'))
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
    @api.depends('reception_id', 'reception_id.state', 'parent_lot_id', 'guia_processing_id', 'subproducto_id')
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
        """Delega en la utilidad compartida parse_fraction_to_decimal_inch (utils_uom.py)."""
        return parse_fraction_to_decimal_inch(fraction_str)
    
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
            
            return float(mbf)
            
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
            
            return float(mbf)
            
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
        # 🏷️ Programa SV: la etiqueta SV con historial no se elimina.
        self._sv_guard_unlink()
        for lot in self:
            if lot.cost_line_ids:
                lot.cost_line_ids.unlink()

        try:
            # Savepoint: permite traducir la violación de integridad a un
            # mensaje de negocio y dejar la transacción utilizable (Odoo, por
            # defecto, deja el error técnico de PostgreSQL).
            with self.env.cr.savepoint():
                return super(StockLotExtended, self).unlink()
        except psycopg2_errors.ForeignKeyViolation as err:
            # 🛡️ La integridad referencial de la BD protege el lote (p. ej.
            # `stock_quant_lot_id_fkey`, ON DELETE RESTRICT). NO se altera el
            # invariante — el lote sigue sin poder eliminarse —: solo se
            # traduce el mensaje técnico a lenguaje de negocio.
            lot = self[:1]
            raise ValidationError(_(
                'La etiqueta/lote %s tiene existencias o documentos que lo '
                'referencian y no puede eliminarse. Use la reversión o la '
                'regularización de la guía/etiqueta SV correspondiente '
                '(\u00abRebajar etiqueta SV\u00bb / \u00abRegularizar volumen de '
                'etiqueta SV\u00bb) en lugar de eliminar el registro.'
            ) % (lot.name or lot.id)) from err

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

    # ==============================================================================
    # 🏷️ F3.1 — IDENTIDAD DE LOTE VOLUMEN (ETIQUETA SV)
    # ==============================================================================

    @api.model
    def _next_volume_lot_label(self):
        """Devuelve la siguiente etiqueta operativa SV para un Lote Volumen.

        La etiqueta (SV + 11 dígitos) proviene de la secuencia global
        `madenat.volume.lot` declarada en madenat_lumber_core/data/
        madenat_volume_lot_sequence.xml. Es única y no reutilizable: los
        huecos por rollback de transacción son aceptables.
        """
        label = self.env['ir.sequence'].next_by_code('madenat.volume.lot')
        if not label:
            raise UserError(
                _('No fue posible generar la etiqueta única para el Lote Volumen.')
            )
        return label

    @api.constrains('lot_flow_type', 'volume_source_guia_id')
    def _check_volume_source_guia(self):
        """Coherencia entre el tipo de flujo y la guía origen documental.

        - Un lote de flujo 'volume' exige su guía origen de volumen.
        - Una guía origen de volumen solo puede existir en un lote 'volume'.
        """
        for lot in self:
            if lot.lot_flow_type == 'volume' and not lot.volume_source_guia_id:
                raise ValidationError(_(
                    "El lote %s es de tipo 'Lote Volumen' y requiere una "
                    "Guía Origen de Volumen."
                ) % (lot.name or lot.id))
            if lot.volume_source_guia_id and lot.lot_flow_type != 'volume':
                raise ValidationError(_(
                    "El lote %s tiene Guía Origen de Volumen (%s) pero su tipo "
                    "de flujo no es 'Lote Volumen'."
                ) % (lot.name or lot.id, lot.volume_source_guia_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        """✅ MEJORA: Sobrescribir create para garantizar estado correcto en nuevos lotes"""
        for vals in vals_list:
            if vals.get('export_width_manual_inches'):
                vals.setdefault('export_width_manual_user_id', self.env.user.id)
                vals.setdefault('export_width_manual_date', fields.Datetime.now())
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
        if vals.get('export_width_manual_inches'):
            vals.setdefault('export_width_manual_user_id', self.env.user.id)
            vals.setdefault('export_width_manual_date', fields.Datetime.now())
        # 🏷️ Programa SV — Guarda server-side de etiquetas SV: bloquea cambios
        # directos de etiqueta/volumen/piezas fuera de las acciones controladas
        # (wizards de madenat.sv.operation). No afecta a lotes no-SV.
        self._sv_guard_write(vals)
        # 🏷️ F3.1 — La guía origen del Lote Volumen es INMUTABLE: no puede
        # limpiarse ni reasignarse a otra guía. Reescribir el mismo valor está
        # permitido (idempotencia), y la reapertura de la guía no la toca
        # porque action_reopen_to_draft() solo escribe guia_processing_id,
        # estado_trazabilidad y technical_validation.
        if 'volume_source_guia_id' in vals:
            raw_source = vals.get('volume_source_guia_id')
            new_source = (raw_source.id if hasattr(raw_source, 'id')
                          else (raw_source or False))
            for lot in self:
                if (lot.volume_source_guia_id.id or False) != new_source:
                    raise ValidationError(_(
                        "La Guía Origen de Volumen del lote %s es inmutable: "
                        "no puede limpiarse ni reasignarse a otra guía."
                    ) % (lot.name or lot.id))

        # 🪵 H5-C / AD-132: Aviso en chatter al modificar piezas o ancho en lote pos-envío
        dim_fields = {'piezas', 'ancho_mm', 'ancho_nominal_mm'}
        lots_to_notify = self.env['stock.lot']
        if dim_fields.intersection(vals.keys()):
            for lot in self:
                if lot.reception_id and ((lot.vol_shipment_m3 or 0.0) > 0.001 or (lot.volumen_m3 or 0.0) > 0.001):
                    if any(vals[f] != lot[f] for f in dim_fields.intersection(vals.keys())):
                        lots_to_notify |= lot

        result = super(StockLotExtended, self).write(vals)

        for lot in lots_to_notify:
            lot.message_post(body="dimensiones modificadas después del ingreso; el volumen no se recalculó")

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

    # 🌲 BLOQUE 6B & 6E — INVENTARIO POR PATIO
    patio_group = fields.Char(
        string='Patio',
        compute='_compute_patio_group',
        store=True,
        index=True,
    )
    lot_piezas = fields.Integer(
        string='Piezas',
        compute='_compute_lot_piezas',
        store=True,
        readonly=True,
    )
    vol_nominal_m3 = fields.Float(
        string='Vol. Compra (m³)',
        compute='_compute_vol_nominal_m3',
        digits=(16, 3),
        store=True,
        readonly=True,
    )
    guia_number = fields.Char(
        string='N° Guía',
        related='lot_id.guia_number',
        readonly=True,
    )
    is_patio = fields.Boolean(
        string='Es Patio',
        related='location_id.is_patio',
        readonly=True,
    )
    patio_type = fields.Selection(
        related='location_id.patio_type',
        string='Tipo de Patio',
        readonly=True,
    )

    @api.depends('location_id', 'location_id.is_patio', 'location_id.name')
    def _compute_patio_group(self):
        for quant in self:
            if quant.location_id and quant.location_id.is_patio:
                quant.patio_group = quant.location_id.name
            else:
                quant.patio_group = 'Sin patio'

    @api.depends('lot_id', 'lot_id.piezas')
    def _compute_lot_piezas(self):
        for quant in self:
            quant.lot_piezas = quant.lot_id.piezas if quant.lot_id else 0

    @api.depends('lot_id', 'lot_id.volume_purchase_m3', 'lot_id.volumen_m3')
    def _compute_vol_nominal_m3(self):
        for quant in self:
            lot = quant.lot_id
            quant.vol_nominal_m3 = (lot.volume_purchase_m3 or lot.volumen_m3 or 0.0) if lot else 0.0