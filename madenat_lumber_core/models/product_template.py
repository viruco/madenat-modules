# -*- coding: utf-8 -*-
"""
Extensión de product.template para validaciones de UoM en industria maderera.
Soporte para Estándar Comercial vs Físico.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    # =========================================================================
    # CONFIGURACIÓN DIMENSIONAL (Arquitectura Dual)
    # =========================================================================
    
    use_commercial_standard = fields.Boolean(
        string="Usar Estándar Comercial",
        help="Si se activa, el Volumen de Embarque se calculará usando las dimensiones nominales abajo definidas, ignorando las medidas físicas reales."
    )

    commercial_thickness_mm = fields.Float(string="Espesor Comercial (mm)", default=0.0)
    commercial_width_mm = fields.Float(string="Ancho Comercial (mm)", default=0.0)
    commercial_length_m = fields.Float(string="Largo Comercial (m)", default=0.0)

    # =========================================================================
    # CONSTRAINT: Validación de UoM para productos de madera
    # =========================================================================
    
    @api.constrains('uom_id', 'type', 'categ_id')
    def _check_lumber_uom_category(self):
        """
        ✅ VALIDACIÓN PROFESIONAL: UoM compatible con Volume
        
        Solo valida productos que claramente son madera:
        - type = 'consu' o 'product' (no servicios)
        - Código contiene palabras clave de madera
        
        Raises:
            ValidationError: Si UoM no es de categoría Volume
        """
        # NO HARDCODING: Obtenemos keywords desde configuración del sistema
        # Si no existe el parámetro, usamos un fallback mínimo seguro
        keywords_param = self.env['ir.config_parameter'].sudo().get_param(
            'madenat.lumber.keywords', 
            'pino,pine,eucalipto,eucalyptus,madera,lumber,wood,timber,tarja,lote,lot,batch,m3,mbf,volumen,volume'
        )
        lumber_keywords = [k.strip().lower() for k in keywords_param.split(',')]
        
        # UoM de categoría Volume permitida
        volume_category = self.env.ref('uom.product_uom_categ_vol', raise_if_not_found=False)
        
        if not volume_category:
            _logger.warning("No se encontró categoría UoM 'Volume'. Saltando validación.")
            return
        
        for product in self:
            # Solo validar productos almacenables/consumibles (no servicios)
            if product.type not in ('consu', 'product'):
                continue
            
            # Verificar si el nombre o código sugiere que es madera
            product_text = f"{product.name or ''} {product.default_code or ''}".lower()
            is_lumber = any(keyword in product_text for keyword in lumber_keywords)
            
            if not is_lumber:
                continue  # No es madera, no validar
            
            # VALIDACIÓN CRÍTICA
            if product.uom_id.category_id != volume_category:
                raise ValidationError(_(
                    "❌ ERROR DE UNIDAD DE MEDIDA\n\n"
                    "El producto '%(product)s' parece ser un producto de MADERA, "
                    "pero tiene una UoM incorrecta.\n\n"
                    "🔍 Detectado:\n"
                    "   • Nombre/Código: %(name)s\n"
                    "   • UoM actual: %(uom)s (Categoría: %(category)s)\n\n"
                    "✅ Requerido:\n"
                    "   • UoM debe ser de categoría 'Volume' (m³, MBF, etc.)\n\n"
                    "🔧 SOLUCIÓN:\n"
                    "   1. Cambie 'Unidad de Medida' a 'm³' o 'MBF'\n"
                    "   2. Si NO es madera, cambie el nombre/código para que no incluya "
                    "palabras como: %(keywords)s\n"
                ) % {
                    'product': product.display_name,
                    'name': product.default_name,
                    'uom': product.uom_id.name,
                    'category': product.uom_id.category_id.name,
                    'keywords': ', '.join(lumber_keywords[:5]) + '...',
                })
    
    @api.onchange('uom_id')
    def _onchange_uom_id_lumber_warning(self):
        """
        ⚠️ ADVERTENCIA PROACTIVA: Alerta al usuario al cambiar UoM
        """
        if not self.uom_id:
            return
        
        volume_category = self.env.ref('uom.product_uom_categ_vol', raise_if_not_found=False)
        
        if not volume_category:
            return
        
        # NO HARDCODING: Misma lógica desde parámetros
        keywords_param = self.env['ir.config_parameter'].sudo().get_param(
            'madenat.lumber.keywords', 
            'pino,pine,eucalipto,madera,lumber,wood,m3,mbf'
        )
        lumber_keywords = [k.strip().lower() for k in keywords_param.split(',')]

        product_text = f"{self.name or ''} {self.default_code or ''}".lower()
        is_lumber = any(keyword in product_text for keyword in lumber_keywords)
        
        if is_lumber and self.uom_id.category_id != volume_category:
            return {
                'warning': {
                    'title': _('⚠️ Advertencia de UoM'),
                    'message': _(
                        'Este producto parece ser MADERA pero la UoM seleccionada '
                        '(%s) no es de categoría "Volume".\n\n'
                        'Para productos de madera, use m³ o MBF.'
                    ) % self.uom_id.name
                }
            }
