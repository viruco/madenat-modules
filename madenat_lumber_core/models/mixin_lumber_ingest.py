from .utils_uom import r3, r4
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class LumberIngestMixin(models.AbstractModel):
    """
    Mixin para operaciones comunes de ingesta de productos de madera.
    
    RESPONSABILIDADES:
    - Validación de productos (tipo, tracking, UoM)
    - Creación de productos con configuración correcta
    - Corrección automática cuando es seguro
    - CÁLCULO INTELIGENTE DE VOLÚMENES (Real vs Nominal)
    
    USADO POR:
    - lumber.reception (Recepción Nacional)
    - madenat.guia.processing (Recepción de Guías Procesadas)
    """
    _name = 'madenat.lumber.ingest.mixin'
    _description = 'Mixin para Ingesta de Madera'

    # ========================================================================
    # MÉTODOS PÚBLICOS DE GESTIÓN DE PRODUCTO (LEGACY + MEJORAS)
    # ========================================================================

   # ==========================================================================
    # 1. FUNCIÓN DE AUTO-REPARACIÓN (EL EXPERTO BLINDADO)
    # ==========================================================================
    @api.model
    def validate_product_lumber_config(self, product):
        """
        🛡️ BLINDAJE DE PRODUCTO (V3 - ROBUST):
        Valida y REPARA la configuración técnica (Storable + Lotes).
        Usa privilegios de superusuario para evitar bloqueos de permisos.
        """
        changes = {}
        
        # A. VERIFICACIÓN TÉCNICA
        # Odoo 18: Para mover stock, debe ser 'consu' + 'is_storable=True'
        if not product.is_storable or product.type != 'consu':
            changes['is_storable'] = True
            changes['type'] = 'consu'
            
        # B. VERIFICACIÓN DE TRAZABILIDAD
        # Sin 'lot', no podemos asignar las etiquetas del Excel (000086016...)
        if product.tracking != 'lot':
            changes['tracking'] = 'lot'
        
        # C. ADVERTENCIA DE UNIDAD DE MEDIDA
        vol_category = self.env.ref('uom.product_uom_categ_vol', raise_if_not_found=False)
        if vol_category and product.uom_id.category_id != vol_category:
             _logger.warning(f"⚠️ ALERTA DE DATOS: {product.name} no usa unidad de volumen.")

        # D. APLICACIÓN DE CORRECCIONES (AUTO-HEALING)
        if changes:
            _logger.info(f"🔧 Reparando configuración de {product.name} | Cambios: {changes}")
            try:
                # Usamos sudo() para que el sistema se auto-corrija 
                # aunque el usuario sea un Operador de Bodega.
                product.sudo().write(changes)
                _logger.info(f"✅ [AUTO-HEAL] Producto '{product.name}' reparado exitosamente.")
                
            except Exception as e:
                # E. DIAGNÓSTICO INTELIGENTE (Si falla el sudo)
                err_msg = str(e).lower()
                # Si falla porque ya hay stock histórico sin lotes:
                if "quant" in err_msg or "stock" in err_msg or "move" in err_msg:
                    raise UserError(
                        f"🛑 BLOQUEO DE INTEGRIDAD DE DATOS:\n\n"
                        f"El producto '{product.name}' tiene stock antiguo SIN lotes.\n"
                        f"Odoo impide activar la trazabilidad ahora.\n\n"
                        f"SOLUCIÓN: Archive este producto y vuelva a subir la guía."
                    )
                else:
                    _logger.error(f"🛑 Error crítico reparando {product.name}: {e}")
                    raise UserError(f"🛑 ERROR ARQUITECTÓNICO: No se pudo reparar {product.name}.\nError: {e}")
        
        return True

    # ==========================================================================
    # 2. FUNCIÓN DE INGESTA (EL EMBUDO HÍBRIDO)
    # ==========================================================================
    @api.model
    def find_or_create_lumber_product(self, code, name=None):
        """
        EMBUDO DE INGESTA INTEGRADO:
        1. Decide QUÉ producto usar (Nombre Real vs Genérico).
        2. Llama a validate_product_lumber_config para asegurar CÓMO está configurado.
        """
        code_str = str(code).strip().upper()
        name_str = str(name).strip() if name else ""
        
        uom_m3 = self.env.ref("uom.product_uom_cubic_meter")
        
        # --- LÓGICA DE IDENTIFICACIÓN ---
        import re
        is_numeric_package = bool(re.match(r'^\d+(\.0)?$', code_str))
        
        # CASO A: INGESTA EXCEL (Prioridad Nombre)
        if len(name_str) > 3 and any(x in name_str.upper() for x in ['MADERA', 'PINO', 'TABLA']):
            target_code = name_str.replace(" ", "_").replace(".", "").upper()[:30]
            target_name = name_str
            is_generic = False

        # CASO B: SCANNER/LUMBER (Prioridad Código -> Genérico)
        elif is_numeric_package:
            target_code = "MADERA_BRUTA_RECEPCION"
            target_name = "Madera Bruta (Recepción Genérica)"
            is_generic = True

        # CASO C: CÓDIGOS REALES
        else:
            target_code = code_str
            target_name = self._sanitize_product_name(name, code_str)
            is_generic = False

        # --- BÚSQUEDA ---
        prod = self.env["product.product"].search([("default_code", "=", target_code)], limit=1)
        
        if not prod and not is_generic:
             prod = self.env["product.product"].search([("name", "=", target_name)], limit=1)

        # --- VALIDACIÓN Y REPARACIÓN (CRÍTICO) ---
        if prod:
            # AQUÍ CONECTAMOS AMBAS FUNCIONES
            # Delegamos la reparación al experto blindado
            self.validate_product_lumber_config(prod)
            return prod

        else:
            # --- CREACIÓN BLINDADA (Producto Nuevo) ---
            _logger.info(f"🆕 Creando producto nuevo: {target_name}")
            try:
                return self.env["product.product"].create({
                    "name": target_name,
                    "default_code": target_code,
                    "type": "consu",     
                    "is_storable": True, # ✅ Requisito 1
                    "tracking": "lot",   # ✅ Requisito 2 (Lo que fallaba recién)
                    "categ_id": self.env.ref("product.product_category_all").id,
                    "uom_id": uom_m3.id,
                    "uom_po_id": uom_m3.id,
                    "purchase_ok": True,
                    "sale_ok": True,
                })
            except Exception as e:
                # Fallback de emergencia
                _logger.error(f"❌ Falló creación, usando genérico. Error: {e}")
                fallback = self.env["product.product"].search([("default_code", "=", "MADERA_BRUTA_RECEPCION")], limit=1)
                # Aseguramos que el fallback también esté sano
                if fallback: self.validate_product_lumber_config(fallback)
                return fallback
    # ========================================================================
    # NUEVA LÓGICA DE CÁLCULO (Nominal vs Real)
    # ========================================================================

    @api.model
    def calculate_normalized_volumes(self, product, raw_val, unit_hint='m3'):
        """
        Calcula volúmenes Real y Nominal normalizados a m³.
        
        Args:
            product: recordset product.product (para buscar reglas de negocio)
            raw_val: float (valor crudo del Excel)
            unit_hint: str ('m3', 'mbf', 'inch') - Pista sobre la unidad de origen
            
        Returns:
            dict: {
                'vol_shipment_m3': float (3 decimales) -> REAL (Verdad de Auditoría)
                'volume_purchase_m3': float (3 decimales) -> NOMINAL (Verdad Comercial/Stock)
                'method': str (Explicación para auditoría)
            }
        """
        if not raw_val:
            return {'vol_shipment_m3': 0.0, 'volume_purchase_m3': 0.0, 'method': 'Cero'}

        # 1. Normalizar Entrada a m³ (Manejo de MBF/Pulgadas)
        try:
            val_float = float(raw_val)
        except (ValueError, TypeError):
            return {'vol_shipment_m3': 0.0, 'volume_purchase_m3': 0.0, 'method': 'Error Valor'}

        shipment_m3 = val_float
        conversion_note = ""

        # Factor Regla de Oro: 1 MBF = 2.36 m³
        hint = str(unit_hint).lower()
        if 'mbf' in hint:
            shipment_m3 = val_float * 2.36
            conversion_note = "[MBF->m3]"
        elif 'inch' in hint or 'pulg' in hint or 'pt' in hint:
            # Si el Excel traía pies tablares (PT) en la columna volumen
            # Asumimos PT / 1000 * 2.36
            shipment_m3 = (val_float / 1000.0) * 2.36
            conversion_note = "[PT->m3]"

        shipment_m3 = r3(shipment_m3)

        # 2. Calcular Nominal (Regla de Negocio / Regla de Oro)
        # 🚀 REGLA DE ORO: El stock operativo se rige por el Nominal Comercial
        purchase_m3 = shipment_m3
        method = f'Identidad {conversion_note}'

        if product:
            # Buscar si el producto tiene espesor comercial vs real definido
            # Campos esperados en product.product: commercial_thickness_mm, thickness_mm
            # Usamos getattr para no romper si el campo no existe en una versión limpia
            c_thick = getattr(product, 'commercial_thickness_mm', 0.0)
            r_thick = getattr(product, 'thickness_mm', 0.0)
            
            if c_thick > 0 and r_thick > 0:
                factor = c_thick / r_thick
                # Aplicar factor si la desviación es significativa (>1%)
                if abs(factor - 1.0) > 0.01:
                    purchase_m3 = shipment_m3 * factor
                    method = f'Factor Espesor ({c_thick}/{r_thick}) {conversion_note}'

        return {
            'vol_shipment_m3': shipment_m3,
            'volume_purchase_m3': r3(purchase_m3),
            'method': method
        }

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    @api.model
    def _sanitize_product_name(self, name, code_str):
        """Sanitiza el nombre del producto."""
        if name and str(name).lower() not in ["nan", "none", ""] and len(str(name)) > 3:
            return str(name).strip()
        return f"Producto {code_str}"

    @api.model
    def _safe_float(self, value, default=0.0):
        """Coerción numérica segura sin NaN (Desacoplada)"""
        if value is None or str(value).strip() == '':
            return default
        try:
            return float(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return default

    @api.model
    def _safe_int(self, value, default=0):
        """Coerción entera segura (Desacoplada)"""
        if value is None or str(value).strip() == '':
            return default
        try:
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default


class LumberIngestLineMixin(models.AbstractModel):
    """
    Mixin para la línea de detalle (Staging).
    Heredada por 'madenat.guia.processing.line' and 'lumber.reception.line'.
    
    Esta tabla intermedia permite al usuario revisar y corregir los volúmenes
    Nominales vs Reales antes de comprometer los datos en el inventario.
    """
    _name = 'madenat.lumber.ingest.line.mixin'
    _description = 'Línea Abstracta de Verificación de Ingesta'

    lot_name = fields.Char('Etiqueta/Lote', required=True)
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    
    # IMPORTANTE: 3 Decimales por regla de negocio
    vol_shipment_m3 = fields.Float('Vol. Físico (Real)', digits=(16, 3), 
                                   help="Volumen Geométrico Real (Facturación/Logística)")
    
    vol_purchase_m3 = fields.Float('Vol. Nominal (Compra)', digits=(16, 3), 
                                   help="Volumen Comercial Pagado (Costeo)")
    
    pieces = fields.Integer('Piezas')
    
    # Trazabilidad de origen
    raw_dims = fields.Char('Dimensiones (Origen)', help="Dimensiones originales leídas del Excel (ej: pulgadas)")
    calc_method = fields.Char('Método Calc.', readonly=True)
    
    # Control de Calidad del Dato
    is_modified = fields.Boolean('Manual', help="Marcado si el usuario editó los valores")
    warning_msg = fields.Char('Alerta', compute='_compute_warning', store=True)

    @api.depends('vol_shipment_m3', 'vol_purchase_m3')
    def _compute_warning(self):
        for rec in self:
            rec.warning_msg = False
            # Validar integridad básica
            if rec.vol_shipment_m3 <= 0:
                rec.warning_msg = "Volumen Físico es 0 o negativo"
                continue
                
            # Validar desviación Nominal vs Real
            if rec.vol_purchase_m3 > 0:
                diff = abs(rec.vol_purchase_m3 - rec.vol_shipment_m3)
                pct = (diff / rec.vol_shipment_m3) * 100
                if pct > 10: # Umbral de tolerancia parametrizable
                    rec.warning_msg = f"Diferencia significativa ({pct:.1f}%)"

    @api.onchange('vol_shipment_m3', 'vol_purchase_m3')
    def _on_change_volumes(self):
        self.is_modified = True

    @api.model
    def _sanitize_lot_name(self, val):
        """Limpia y normaliza identidad de lote a 13 dígitos EAN-13."""
        if not val:
            return ""
        v = str(val).strip().upper()
        if v.endswith('.0'):
            v = v[:-2]
        if '-' in v or len(v) > 13:
            return v
        return v.zfill(13)

    @api.model
    def _is_valid_volume(self, vol):
        """Valida rango de volumen físico/comercial aceptable."""
        try:
            v = float(vol)
            return 0.1 <= v <= 2000.0
        except (ValueError, TypeError):
            return False

    @api.model
    def _validate_lot_dimensions(self, thickness, width, length):
        """Valida rangos coherentes para dimensiones de madera bruta."""
        errors = []
        if not (1 <= float(thickness) <= 500):
            errors.append(f"Espesor inválido: {thickness} mm (rango 1-500)")
        if not (10 <= float(width) <= 500):
            errors.append(f"Ancho inválido: {width} mm (rango 10-500)")
        if not (0.1 <= float(length) <= 20):
            errors.append(f"Largo inválido: {length} m (rango 0.1-20)")
        
        if errors:
            from odoo.exceptions import ValidationError
            raise ValidationError("\n".join(errors))
    
 