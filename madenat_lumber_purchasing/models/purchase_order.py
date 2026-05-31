# -*- coding: utf-8 -*-
"""
Extensión de purchase.order para compras de madera - Odoo 18 CE
VERSIÓN 5.1.0 CORREGIDA: Respetando Regla de Oro - Sin dependencias circulares
Ownership (Regla de Oro): Purchasing es el gatekeeper de PO y del maestro MADERA_GENERICA.
Compatibilidad CE: vistas usan <list> y atributos booleanos directos.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json

_logger = logging.getLogger(__name__)


class PurchaseOrderLumber(models.Model):
    _inherit = 'purchase.order'

    # ==================== RELACIONES DE RECEPCIÓN (TRAZABILIDAD) ====================
    reception_ids = fields.One2many(
        'lumber.reception',
        'purchase_id',
        string='Guías de Despacho Asociadas',
        readonly=True,
        help="Todas las guías de despacho procesadas para esta OC"
    )

    reception_count = fields.Integer(
        'Nº Guías Recibidas',
        compute='_compute_reception_stats',
        store=True
    )

    # LEGACY: Mantener compatibilidad
    lumber_reception_ids = fields.One2many(
        'lumber.reception',
        'purchase_id',
        string='Recepciones de Guía (Legacy)',
        readonly=True
    )

    lumber_reception_id = fields.Many2one(
        'lumber.reception',
        'Recepción Asociada (Legacy)',
        readonly=True
    )

    # ✅ CORRECCIÓN REGLA DE ORO: Referencia sin dependencia circular
    ingestion_source_ref = fields.Char(
        'Referencia de Ingesta',
        help="Referencia al documento de ingesta origen (Ej: ING-001)"
    )

    # ==================== INFORMACIÓN BÁSICA MADERA ====================
    lumber_quality = fields.Selection([
        ('col_a', 'Calidad Col A'),
        ('col_b', 'Calidad Col B'),
        ('industrial', 'Industrial'),
        ('premium', 'Premium')
    ], string='Calidad de Madera')

    wood_type = fields.Selection([
        ('pine', 'Pino Radiata'),
        ('eucalyptus', 'Eucalipto'),
        ('other', 'Otra')
    ], string='Especie Maderera', default='pine')

    treatment = fields.Selection([
        ('kiln_dried', 'Seco Cepillado'),
        ('green', 'Verde'),
        ('treated', 'Tratado')
    ], string='Tratamiento', default='kiln_dried')

    thickness_mm = fields.Float('Espesor (mm)', digits=(8, 2))

    lumber_volume_m3 = fields.Float(
        'Volumen Total m³',
        digits=(16, 3),
        compute='_compute_lumber_volume',
        store=True
    )

    # ==================== SEGUIMIENTO DE RECEPCIÓN ====================
    received_volume_m3 = fields.Float(
        'Volumen Recibido (m³)',
        compute='_compute_reception_stats',
        store=True,
        digits=(16, 3),
        help="Volumen físico total recibido de todas las guías"
    )

    received_commercial_m3 = fields.Float(
        'Volumen Comercial Recibido (m³)',
        compute='_compute_reception_stats',
        store=True,
        digits=(16, 3),
        help="Volumen comercial según guías de despacho"
    )

    variance_commercial_physical = fields.Float(
        'Diferencia Comercial vs Físico (%)',
        compute='_compute_reception_stats',
        store=True,
        digits=(5, 2),
        help="Diferencia porcentual entre volumen comercial y físico"
    )

    pending_volume_m3 = fields.Float(
        'Volumen Pendiente (m³)',
        compute='_compute_reception_stats',
        store=True,
        digits=(16, 3)
    )

    percent_completed = fields.Float(
        '% Completado',
        compute='_compute_reception_stats',
        store=True,
        digits=(5, 2)
    )

    total_lots_count = fields.Integer(
        'Total Lotes',
        compute='_compute_reception_stats',
        store=True,
        help="Número total de lotes/paquetes recibidos"
    )

    monto_recibido_usd = fields.Float(
        'Monto Recibido (USD)',
        compute='_compute_reception_stats',
        store=True,
        digits=(16, 2)
    )

    # LEGACY: Mantener compatibilidad
    volume_received_m3 = fields.Float(
        'Volumen Recibido (m³) Legacy',
        digits=(16, 3),
        compute='_compute_reception_metrics_legacy',
        store=True
    )

    reception_percentage = fields.Float(
        '% Recepcionado Legacy',
        digits=(16, 2),
        compute='_compute_reception_metrics_legacy',
        store=True
    )

    amount_received_usd = fields.Float(
        'Monto Recibido (USD) Legacy',
        digits=(16, 2),
        compute='_compute_reception_metrics_legacy',
        store=True
    )

    remaining_volume_m3 = fields.Float(
        'Volumen Pendiente (m³) Legacy',
        digits=(16, 3),
        compute='_compute_reception_metrics_legacy',
        store=True
    )

    # ==================== ESPECIFICACIONES TÉCNICAS ====================
    min_thickness_mm = fields.Float('Espesor Mínimo (mm)', digits=(8, 2))
    max_thickness_mm = fields.Float('Espesor Máximo (mm)', digits=(8, 2))
    min_width_mm = fields.Float('Ancho Mínimo (mm)', digits=(8, 2))
    max_width_mm = fields.Float('Ancho Máximo (mm)', digits=(8, 2))
    min_length_m = fields.Float('Largo Mínimo (m)', digits=(8, 2))
    max_length_m = fields.Float('Largo Máximo (m)', digits=(8, 2))

    surface_finish = fields.Selection([
        ('s2s', 'S2S - Dos caras cepilladas'),
        ('s4s', 'S4S - Cuatro caras cepilladas'),
        ('rough', 'Rough - Sin cepillar')
    ], string='Terminación Superficial')

    drying_method = fields.Selection([
        ('kiln', 'Secado en Cámara'),
        ('air', 'Secado Natural'),
        ('mixed', 'Mixto')
    ], string='Método de Secado')

    humidity_min = fields.Float('Humedad Mínima (%)', digits=(5, 2))
    humidity_max = fields.Float('Humedad Máxima (%)', digits=(5, 2))

    thickness_tolerance_min = fields.Float('Tol. Espesor Mín (mm)', digits=(8, 2))
    thickness_tolerance_max = fields.Float('Tol. Espesor Máx (mm)', digits=(8, 2))
    width_tolerance_min = fields.Float('Tol. Ancho Mín (mm)', digits=(8, 2))
    width_tolerance_max = fields.Float('Tol. Ancho Máx (mm)', digits=(8, 2))
    length_tolerance_min = fields.Float('Tol. Largo Mín (m)', digits=(8, 3))
    length_tolerance_max = fields.Float('Tol. Largo Máx (m)', digits=(8, 3))

    # ==================== CONTROL DE CALIDAD ====================
    accepts_pencil_wane = fields.Boolean('Acepta Canto Muerto/Pencil Wane', default=False)
    accepts_blue_stain = fields.Boolean('Acepta Mancha Azul', default=False)
    accepts_drying_cracks = fields.Boolean('Acepta Grietas de Secado', default=False)
    accepts_splits = fields.Boolean('Acepta Rajaduras/Partiduras', default=False)

    free_bark = fields.Boolean('Libre de Cortezas', default=True)
    no_warping = fields.Boolean('Sin Alabeos', default=True)
    ht_certification_required = fields.Boolean('Certificación HT Requerida', default=False)

    # ==================== EMBALAJE Y LOGÍSTICA ====================
    packaging_type = fields.Selection([
        ('strapped', 'Con Zuncho'),
        ('wrapped', 'Envuelto'),
        ('loose', 'Suelto')
    ], string='Tipo de Embalaje')

    strapping_material = fields.Selection([
        ('steel', 'Acero'),
        ('plastic', 'Plástico'),
        ('none', 'Sin Zuncho')
    ], string='Material de Zuncho')

    delivery_period = fields.Char('Plazo de Entrega')
    validity_date = fields.Date('Fecha de Vigencia')
    contract_number = fields.Char('Número de Contrato')
    delivery_instructions = fields.Text('Instrucciones de Entrega')
    payment_terms = fields.Text('Términos de Pago')

    # ==================== ESTADOS OPERATIVOS ====================
    provisional = fields.Boolean(string='Provisional', default=False)

    # ==================== MÉTODOS COMPUTADOS ====================
    @api.depends('order_line.product_qty')
    def _compute_lumber_volume(self):
        """Calcular volumen total desde líneas de OC"""
        for order in self:
            total_volume = sum(order.order_line.mapped('product_qty'))
            order.lumber_volume_m3 = round(total_volume, 3)

    @api.depends(
        'reception_ids',
        'reception_ids.state',
        'reception_ids.physical_volume_m3',
        'reception_ids.commercial_volume_m3',
        'reception_ids.total_amount_usd',
        'reception_ids.total_packages',
        'order_line.product_qty'
    )
    def _compute_reception_stats(self):
        """Calcular estadísticas de recepción - consolidado de recepciones 'done'"""
        for order in self:
            completed_receptions = order.reception_ids.filtered(lambda r: r.state == 'done')

            order.reception_count = len(completed_receptions)
            total_received_m3 = sum(completed_receptions.mapped('physical_volume_m3'))
            order.received_volume_m3 = total_received_m3
            total_commercial_m3 = sum(completed_receptions.mapped('commercial_volume_m3'))
            order.received_commercial_m3 = total_commercial_m3

            order.variance_commercial_physical = (
                ((total_received_m3 - total_commercial_m3) / total_commercial_m3) * 100
                if total_commercial_m3 > 0 else 0.0
            )

            order.monto_recibido_usd = sum(completed_receptions.mapped('total_amount_usd'))
            total_ordered = sum(order.order_line.mapped('product_qty')) if order.order_line else 0.0
            order.pending_volume_m3 = max(0.0, total_ordered - total_received_m3)
            order.percent_completed = (total_received_m3 / total_ordered) * 100 if total_ordered > 0 else 0.0
            order.total_lots_count = sum(completed_receptions.mapped('total_packages'))

    @api.depends(
        'lumber_reception_ids', 'lumber_reception_ids.state',
        'lumber_reception_ids.commercial_volume_m3', 'lumber_reception_ids.total_amount_usd'
    )
    def _compute_reception_metrics_legacy(self):
        """Calcular métricas de seguimiento de recepciones (LEGACY)"""
        for order in self:
            receptions_done = order.lumber_reception_ids.filtered(lambda r: r.state == 'done')
            total_volume = sum(r.commercial_volume_m3 for r in receptions_done)
            total_amount = sum(r.total_amount_usd for r in receptions_done)

            order.volume_received_m3 = total_volume
            order.amount_received_usd = total_amount

            if order.lumber_volume_m3 > 0:
                order.reception_percentage = min(100.0, (total_volume / order.lumber_volume_m3) * 100)
            else:
                order.reception_percentage = 0.0

            order.remaining_volume_m3 = max(0.0, order.lumber_volume_m3 - total_volume)

    # ==================== GATEKEEPER API - REGLA DE ORO ====================
    @api.model
    def validate_or_create_po(self, payload, policy):
        """
        ✅ GATEKEEPER API: Único punto de entrada para creación/validación de POs
        Implementa la Regla de Oro - Ownership Único
        
        ============================================================================
        REGLA DE ORO - FIX #4 (2024-12-04):
        ============================================================================
        ✅ Manejo robusto de errores en creación de líneas
        ✅ Feedback detallado al usuario sobre fallos parciales
        ✅ Logging mejorado para debugging
        ✅ Validación temprana para evitar OCs “vacías”
        
        Args:
            payload (dict): Datos de la PO
                - partner_id (int): ID del proveedor (requerido)
                - partner_ref (str): Referencia del proveedor
                - currency_id (int): Moneda (opcional)
                - lines (list): Lista de líneas con product_id, qty, price, etc.
                - origin (str): Origen de la solicitud
                - ingestion_source_ref (str): Referencia externa
            
            policy (dict): Políticas de creación
                - auto_create (bool): Crear automáticamente si no existe
                - provisional (bool): Marcar como provisional
        
        Returns:
            dict: {
                'success': bool,
                'po_id': int (si success=True),
                'state': str ('created', 'created_provisional', 'linked'),
                'message': str (mensaje descriptivo),
                'po_name': str (nombre de la PO),
                'error': str (si success=False)
            }
        """
        try:
            # Normalizar policy para evitar None
            policy = policy or {}
            auto_create = bool(policy.get('auto_create', False))
            provisional = bool(policy.get('provisional', True))

            # ================================================================
            # VALIDACIÓN 1: Partner requerido
            # ================================================================
            if not payload.get('partner_id'):
                return {
                    'success': False,
                    'error': _('Se requiere ID del Proveedor (partner_id)')
                }

            # ================================================================
            # REGLA DE ORO: Asegurar que MADERA_GENERICA existe
            # ================================================================
            self._get_master_product_strict()

            # ================================================================
            # VALIDACIÓN 2: Buscar PO existente (si no es auto_create)
            # ================================================================
            existing_po = None
            partner_ref = payload.get('partner_ref')
            partner_id = payload.get('partner_id')

            if (not auto_create) and partner_ref and partner_id:
                existing_po = self.search([
                    ('partner_ref', '=', partner_ref),
                    ('partner_id', '=', partner_id),
                    ('company_id', '=', self.env.company.id),
                ], limit=1)

            lines_payload = payload.get('lines') or []

            # ================================================================
            # VALIDACIÓN 3: ¿Se requieren líneas?
            # - Si se va a CREAR una nueva PO (auto_create o no hay existente)
            #   y no hay líneas, no tiene sentido crear nada.
            # ================================================================
            if (auto_create or not existing_po) and not lines_payload:
                return {
                    'success': False,
                    'error': _('Se requieren líneas de orden de compra para crear la OC.')
                }

            # ================================================================
            # RAMA 1: CREAR NUEVA PO
            # ================================================================
            if auto_create or not existing_po:
                po_vals = {
                    'partner_id': partner_id,
                    'partner_ref': partner_ref or _('ING-%s') % payload.get('ingestion_source_ref', ''),
                    'currency_id': payload.get('currency_id', self.env.company.currency_id.id),
                    'date_order': fields.Datetime.now(),
                    'origin': payload.get('origin', ''),
                    'ingestion_source_ref': payload.get('ingestion_source_ref', ''),
                    'state': 'draft' if provisional else 'sent',
                    'provisional': provisional,
                }

                # Crear PO
                new_po = self.create(po_vals)
                _logger.info(f"📦 PO creada: {new_po.name} (partner_id={partner_id})")

                # ============================================================
                # REGLA DE ORO - FIX #4: Crear líneas con manejo de errores
                # ============================================================
                result = self._create_po_lines_with_validation(
                    new_po,
                    lines_payload,
                    policy,
                )

                lines_created = result['lines_created']
                lines_failed = result['lines_failed']
                errors = result['errors']

                # ============================================================
                # VALIDACIÓN 4: ¿Se creó al menos una línea?
                # (si llegamos aquí sin líneas es porque venían pero todas fallaron)
                # ============================================================
                if lines_created == 0:
                    _logger.error(
                        f"❌ PO {new_po.name} eliminada: no se pudo crear ninguna línea"
                    )
                    # Intentamos eliminar; si falla, dejamos el error subir
                    new_po.unlink()

                    error_detail = '\n'.join(errors) if errors else _('Error desconocido')
                    return {
                        'success': False,
                        'error': _(
                            'No se pudieron crear líneas de orden de compra.\n'
                            'Errores detectados:\n%s'
                        ) % error_detail
                    }

                # ============================================================
                # RESULTADO: PO creada (con o sin errores parciales)
                # ============================================================
                result_po = new_po
                estado_final = 'created_provisional' if provisional else 'created'

                if lines_failed > 0:
                    # Hay errores parciales - informar al usuario
                    mensaje = _(
                        '⚠️ OC creada con advertencias: %s\n\n'
                        '✅ Líneas exitosas: %d\n'
                        '⚠️ Líneas fallidas: %d\n\n'
                        'Primeros errores:\n%s'
                    ) % (
                        new_po.name,
                        lines_created,
                        lines_failed,
                        '\n'.join(f"• {err}" for err in errors[:5]),
                    )

                    _logger.warning(
                        f"⚠️ PO {new_po.name} creada con errores parciales: "
                        f"{lines_created} OK, {lines_failed} FAIL"
                    )
                else:
                    # Todo exitoso
                    mensaje = _(
                        '✅ OC creada exitosamente: %s\n'
                        'Líneas procesadas: %d'
                    ) % (new_po.name, lines_created)

                    _logger.info(
                        f"✅ PO {new_po.name} creada exitosamente con {lines_created} líneas"
                    )

            # ================================================================
            # RAMA 2: VINCULAR A PO EXISTENTE
            # ================================================================
            else:
                result_po = existing_po
                estado_final = 'linked'
                mensaje = _('🔗 Vinculado a OC existente: %s') % existing_po.name

                _logger.info(
                    f"🔗 Vinculación exitosa a PO existente: {existing_po.name}"
                )

            # ================================================================
            # RETORNO EXITOSO
            # ================================================================
            return {
                'success': True,
                'po_id': result_po.id,
                'state': estado_final,
                'message': mensaje,
                'po_name': result_po.name,
            }

        except Exception as e:
            # ================================================================
            # MANEJO DE ERRORES CRÍTICOS (no esperados)
            # ================================================================
            error_msg = str(e)
            _logger.error(
                f"❌ Error crítico en Gatekeeper validate_or_create_po: {error_msg}",
                exc_info=True,
            )

            return {
                'success': False,
                'error': _("Error crítico en procesamiento de Purchasing:\n%s") % error_msg,
            }


    def _create_po_lines_with_validation(self, purchase_order, lines_payload, policy):
        """
        VALIDACIÓN CENTRALIZADA de líneas de PO
        
        ============================================================================
        REGLA DE ORO - FIX #4 (2024-12-04):
        ============================================================================
        ✅ Acumula errores en lugar de silenciarlos
        ✅ Continúa procesamiento pero registra fallos
        ✅ Retorna información completa para feedback al usuario
        ✅ Distingue entre errores de validación y errores técnicos
        
        Args:
            purchase_order: Orden de compra donde agregar líneas
            lines_payload: Lista de dicts con datos de líneas
            policy: Política de validación (no usado actualmente)
        
        Returns:
            dict: {
                'lines_created': int - Líneas creadas exitosamente,
                'lines_failed': int - Líneas que fallaron,
                'errors': list - Lista de mensajes de error descriptivos,
                'success': bool - True si al menos una línea fue creada
            }
        
        Example:
            >>> result = self._create_po_lines_with_validation(po, lines, 'strict')
            >>> if result['lines_failed'] > 0:
            >>>     raise UserError("\\n".join(result['errors']))
        """
        lines_created = 0
        lines_failed = 0
        errors = []
        
        for idx, line_data in enumerate(lines_payload, start=1):
            try:
                # ============================================================
                # VALIDACIÓN 1: Resolución de producto
                # ============================================================
                product_id = self._resolve_product_with_fallback(
                    line_data.get('product_id'),
                    line_data.get('name', '')
                )
                
                if not product_id:
                    lines_failed += 1
                    error_msg = (
                        f"Línea #{idx}: Producto no encontrado "
                        f"'{line_data.get('name', 'Sin nombre')}'"
                    )
                    _logger.warning(f"⚠️ {error_msg}")
                    errors.append(error_msg)
                    continue
                
                # ============================================================
                # VALIDACIÓN 2: Unidad de medida
                # ============================================================
                product_uom = line_data.get('product_uom')
                if not product_uom:
                    product = self.env['product.product'].browse(product_id)
                    product_uom = product.uom_po_id.id or product.uom_id.id
                
                # ============================================================
                # VALIDACIÓN 3: Cantidad y precio
                # ============================================================
                try:
                    product_qty = float(line_data.get('product_qty', 1))
                    price_unit = float(line_data.get('price_unit', 0))
                except (ValueError, TypeError) as e:
                    lines_failed += 1
                    error_msg = (
                        f"Línea #{idx}: Valores numéricos inválidos - "
                        f"Cantidad: {line_data.get('product_qty')}, "
                        f"Precio: {line_data.get('price_unit')} - "
                        f"{line_data.get('name', '')}"
                    )
                    _logger.warning(f"⚠️ {error_msg}")
                    errors.append(error_msg)
                    continue
                
                if product_qty <= 0:
                    lines_failed += 1
                    error_msg = (
                        f"Línea #{idx}: Cantidad inválida ({product_qty}) - "
                        f"{line_data.get('name', 'Sin nombre')}"
                    )
                    _logger.warning(f"⚠️ {error_msg}")
                    errors.append(error_msg)
                    continue
                
                # ============================================================
                # CREACIÓN DE LÍNEA
                # ============================================================
                line_vals = {
                    'order_id': purchase_order.id,
                    'product_id': product_id,
                    'name': line_data.get('name', ''),
                    'product_qty': product_qty,
                    'price_unit': price_unit,
                    'product_uom': product_uom,
                    'date_planned': fields.Datetime.now(),
                }
                
                self.env['purchase.order.line'].create(line_vals)
                lines_created += 1
                _logger.info(
                    f"✅ Línea #{idx} creada: {line_data.get('name', '')} "
                    f"({product_qty} unidades)"
                )
                
            except Exception as e:
                # ============================================================
                # MANEJO DE ERRORES TÉCNICOS (no de validación)
                # ============================================================
                lines_failed += 1
                error_msg = (
                    f"Línea #{idx}: Error técnico - {str(e)} - "
                    f"{line_data.get('name', 'Sin nombre')}"
                )
                _logger.error(f"❌ {error_msg}", exc_info=True)
                errors.append(error_msg)
                continue  # ✅ Continuar con siguiente línea
        
        # ============================================================
        # RESUMEN Y RETORNO
        # ============================================================
        result = {
            'lines_created': lines_created,
            'lines_failed': lines_failed,
            'errors': errors,
            'success': lines_created > 0
        }
        
        # Log de resumen
        if lines_failed > 0:
            _logger.warning(
                f"⚠️ Procesamiento de líneas completado con errores: "
                f"{lines_created} creadas, {lines_failed} fallidas"
            )
        else:
            _logger.info(
                f"✅ Todas las líneas procesadas exitosamente: {lines_created} creadas"
            )
        
        return result


    def _resolve_product_with_fallback(self, product_id, product_name):
        """RESOLUCIÓN CON FALLBACK: Implementa la estrategia MADERA_GENERICA"""
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.exists():
                return product.id
        
        if product_name and product_name.strip():
            product = self.env['product.product'].search([
                ('name', 'ilike', product_name.strip())
            ], limit=1)
            if product:
                return product.id
        
        generic_product = self.env['product.product'].search([
            ('default_code', '=', 'MADERA_GENERICA')
        ], limit=1)
        
        if generic_product:
            _logger.info("🔄 Usando MADERA_GENERICA para: %s", product_name)
            return generic_product.id
        
        _logger.error("❌ MADERA_GENERICA no encontrada")
        return False

    
    def _get_master_product_strict(self):
        """
        Recupera el producto maestro de madera de forma estricta.
        No crea datos. Solo lee configuración. (Audit Compliance)
        """
        # 1. Intentar por parámetro de sistema (Best Practice)
        param_key = 'madenat.import_product_id'
        product_id = int(self.env['ir.config_parameter'].sudo().get_param(param_key, 0))
        
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.exists():
                return product
                
        # 2. Fallback de lectura (Legacy support)
        # Buscamos por referencia interna conocida, pero SIN CREAR.
        product = self.env['product.product'].search([('default_code', '=', 'MADERA_GENERICA')], limit=1)
        if product:
            _logger.warning("Usando producto MADERA_GENERICA por código. Configure 'madenat.import_product_id'.")
            return product
            
        # 3. Fallo Controlado
        raise UserError(_(
            "Error de Configuración Crítica: No se encuentra el producto 'MADERA_GENERICA'. "
            "Por favor configure el producto maestro o el parámetro del sistema."
        ))

    def _deprecated_ensure_master_product_v2(self):
            """
            Obtiene el producto maestro con estrategia de fallback inteligente.
            
            LÓGICA HÍBRIDA (Transición Segura):
            1. Intenta leer la configuración oficial (Lo ideal).
            2. Si falla, busca el producto 'MADERA_GENERICA' existente (Compatibilidad).
            3. Si lo encuentra, AUTO-REPARA la configuración para la próxima vez.
            4. Si no existe, lanza error (No creamos basura automáticamente).
            """
            # 1. Intentar vía Configuración (Ruta Feliz)
            param_key = 'madenat.import_product_id'
            product_id_str = self.env['ir.config_parameter'].sudo().get_param(param_key)
            
            if product_id_str:
                try:
                    product = self.env['product.product'].browse(int(product_id_str))
                    if product.exists():
                        return product
                except (ValueError, TypeError):
                    pass # Si el parámetro está corrupto, continuamos al fallback

            # 2. Ruta de Compatibilidad (Legacy Fallback)
            # Si no está configurado, buscamos si ya existe el producto histórico
            _logger.info("⚠️ Configuración 'madenat.import_product_id' no encontrada. Buscando producto legacy...")
            
            product = self.env['product.product'].search([
                ('default_code', '=', 'MADERA_GENERICA')
            ], limit=1)

            if product:
                # 3. AUTO-REPARACIÓN (Self-Healing)
                # Si encontramos el producto legacy, guardamos la configuración automáticamente
                # para que la próxima vez entre por el paso 1.
                _logger.info(f"✅ Producto Legacy encontrado (ID: {product.id}). Auto-configurando sistema...")
                self.env['ir.config_parameter'].sudo().set_param(param_key, product.id)
                return product

            # 4. Falla Controlada (Solo si realmente no hay nada)
            raise UserError(_(
                "⛔ Error Crítico: Producto Maestro no encontrado.\n\n"
                "No se encontró configuración en 'Ajustes' ni existe un producto con código 'MADERA_GENERICA'.\n"
                "Por favor cree el producto manualmente o selecciónelo en la configuración."
            ))




    # ==================== ACCIONES DE USUARIO ====================
    def action_view_receptions(self):
        """Abrir vista de guías de despacho asociadas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Guías de Despacho - {self.name}',
            'res_model': 'lumber.reception',
            'view_mode': 'list,form',
            'domain': [('purchase_id', '=', self.id)],
            'context': {
                'default_purchase_id': self.id,
                'default_supplier_id': self.partner_id.id,
            },
        }

    def action_view_lots(self):
        """Abrir vista de lotes asociados a esta OC"""
        self.ensure_one()
        lot_ids = self.reception_ids.mapped('lot_ids').ids
        return {
            'type': 'ir.actions.act_window',
            'name': f'Lotes - {self.name}',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', lot_ids)],
            'context': {'group_by': 'reception_id'},
        }

    def action_create_lumber_reception(self):
        """Crear nueva recepción de guía"""
        self.ensure_one()
        reception = self.env['lumber.reception'].create({
            'name': f"REC-{self.name}",
            'supplier_id': self.partner_id.id,
            'purchase_id': self.id,
            'state': 'draft',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.reception',
            'res_id': reception.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_update_reception_data(self):
        """Refrescar datos de seguimiento de recepciones"""
        self.ensure_one()
        self._compute_reception_stats()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualizado'),
                'message': _('Datos de recepción actualizados correctamente'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_review_provisional(self):
        """Revisión de PO provisional para permitir confirmación"""
        for po in self:
            po.provisional = False
        return True

    # ==================== VALIDACIONES ====================
    @api.constrains('lumber_volume_m3')
    def _check_volume_positive(self):
        """Validar que el volumen sea positivo"""
        for order in self:
            if order.lumber_volume_m3 < 0:
                raise ValidationError(_('El volumen de madera no puede ser negativo.'))

    # ==================== UTILIDADES ====================
    def is_reception_complete(self):
        """Verificar si la recepción está completa"""
        self._compute_reception_stats()
        return self.percent_completed >= 99.9

    def get_reception_status(self):
        """Obtener estado de recepción"""
        self._compute_reception_stats()
        if self.percent_completed == 0:
            return 'pending'
        if self.percent_completed >= 99.9:
            return 'completed'
        return 'partial'