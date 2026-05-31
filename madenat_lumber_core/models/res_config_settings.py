# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_product_creation = fields.Boolean(
        string='Permitir creación automática de productos al importar',
        config_parameter='madenat.allow_product_creation',
        default=False,
        help='Si está activado, el sistema creará productos automáticamente cuando no existan en el packing list'
    )

    omission_threshold = fields.Integer(
        string='Umbral máximo de omisiones por importación',
        config_parameter='madenat.omission_threshold',
        default=5,
        help='Número máximo de productos que pueden omitirse antes de detener el procesamiento'
    )

    import_product_id = fields.Many2one(
        'product.product',
        string='Producto por Defecto para Importación',
        config_parameter='madenat.import_product_id',
        help='Producto que se asignará por defecto a los nuevos lotes creados desde el importador de valoraciones'
    )

    stock_sms_confirmation_template_id = fields.Many2one(
        'sms.template',
        string='Plantilla SMS de Confirmación',
        config_parameter='madenat.stock_sms_confirmation_template_id',
        help='Plantilla para mensajes SMS de confirmación de movimientos de stock'
    )

    stock_move_sms_validation = fields.Boolean(
        string='Validación SMS en Movimiento de Stock',
        config_parameter='madenat.stock_move_sms_validation',
        default=False,
        help='Activar validación SMS en movimientos de stock'
    )
        # ====================================================================
    # CONFIGURACIÓN DE VALIDACIÓN DE VOLÚMENES
    # Agregado: 2025-12-01 - Mejoras de robustez
    # ====================================================================
    
    volume_variance_warning_threshold = fields.Float(
        string='Umbral Advertencia Diferencia Volumen (%)',
        config_parameter='madenat_lumber_core.volume_variance_warning_threshold',
        default=5.0,
        help='Porcentaje de diferencia entre volumen comercial y físico '
             'que dispara advertencia visual (decoración amarilla).'
    )
    
    volume_variance_critical_threshold = fields.Float(
        string='Umbral Crítico Diferencia Volumen (%)',
        config_parameter='madenat_lumber_core.volume_variance_critical_threshold',
        default=10.0,
        help='Porcentaje de diferencia que dispara alerta crítica (decoración roja) '
             'y puede requerir justificación obligatoria.'
    )
