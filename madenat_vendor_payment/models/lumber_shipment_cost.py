# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging


_logger = logging.getLogger(__name__)


class LumberShipmentCostLine(models.Model):
    _inherit = 'lumber.shipment.cost.line'
    
    # ================================================================
    # PROVEEDOR - CAMPOS MEJORADOS CON CATEGORÍAS
    # ================================================================
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor/Prestador',
        required=True,
        domain=[('supplier_rank', '>', 0)]
    )
    
    # NUEVO CAMPO: Categoría específica MADENAT
    supplier_category = fields.Selection([
        ('madera', '🌲 Proveedor de Madera'),
        ('transport', '🚚 Transportista'),
        ('consolidation', '📦 Empresa de Consolidación'),
        ('naviera', '🚢 Naviera'),
        ('aduana', '📋 Agencia Aduanal'),
        ('seguros', '🛡️ Aseguradora'),
        ('portuario', '🏗️ Servicios Portuarios'),
        ('otros', '⚙️ Otros Servicios')
    ], string='Categoría de Proveedor', required=True, default='otros')
    
    # Campo computado para mostrar icono en vistas
    category_display = fields.Char(string='Categoría', compute='_compute_category_display')
    
    partner_type = fields.Selection(
        [
            ('supplier', 'Proveedor Madera'),
            ('packing', 'Consolidación'),
            ('customs', 'Agencia Aduana'),
            ('freight', 'Naviera/Freight'),
            ('insurance', 'Seguro'),
            ('warehouse', 'Almacenaje'),
            ('transport', 'Transporte'),
            ('service', 'Otro Servicio'),
        ],
        string='Tipo',
        compute='_compute_partner_type',
        store=True
    )
    
    @api.depends('partner_id')
    def _compute_partner_type(self):
        """Obtener tipo de servicio del proveedor si existe"""
        for rec in self:
            if rec.partner_id and hasattr(rec.partner_id, 'vendor_service_type'):
                rec.partner_type = rec.partner_id.vendor_service_type
            else:
                rec.partner_type = False
    
    @api.depends('supplier_category')
    def _compute_category_display(self):
        category_icons = {
            'madera': '🌲 Madera',
            'transport': '🚚 Transporte', 
            'consolidation': '📦 Consolidación',
            'naviera': '🚢 Naviera',
            'aduana': '📋 Aduana',
            'seguros': '🛡️ Seguros',
            'portuario': '🏗️ Portuario',
            'otros': '⚙️ Otros'
        }
        for record in self:
            record.category_display = category_icons.get(record.supplier_category, '⚙️ Otros')
    
    # Método para asignar categoría automáticamente basado en el proveedor
    @api.onchange('partner_id')
    def _onchange_partner_auto_category(self):
        """Asignar categoría automáticamente basado en las categorías del proveedor"""
        if self.partner_id:
            # Mapeo de categorías externas a nuestras categorías
            category_mapping = {
                'category_supplier_madera': 'madera',
                'category_supplier_transport': 'transport', 
                'category_supplier_consolidation': 'consolidation',
                'category_supplier_naviera': 'naviera',
                'category_supplier_aduana': 'aduana',
                'category_supplier_seguros': 'seguros',
                'category_supplier_portuarios': 'portuario'
            }
            
            # Verificar categorías del proveedor
            for category in self.partner_id.category_id:
                external_id = category.get_external_id()
                if external_id:
                    for cat_key, cat_value in category_mapping.items():
                        if cat_key in external_id.values():
                            self.supplier_category = cat_value
                            return
    
    # ================================================================
    # FACTURACIÓN - VERSIÓN MEJORADA
    # ================================================================
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        domain=[('move_type', '=', 'in_invoice')]
    )
    
    invoice_ref = fields.Char('Nº Factura', related='invoice_id.ref', store=True)
    invoice_date = fields.Date('Fecha', related='invoice_id.invoice_date', store=True)
    
    # ================================================================
    # PAGOS
    # ================================================================
    
    payment_state = fields.Selection([
        ('not_paid', 'Sin Pagar'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagado'),
    ], compute='_compute_payment_state', store=True)
    
    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_payment_state(self):
        for rec in self:
            if not rec.invoice_id:
                rec.payment_state = 'not_paid'
            elif rec.invoice_id.payment_state == 'paid':
                rec.payment_state = 'paid'
            elif rec.invoice_id.payment_state in ('partial', 'in_payment'):
                rec.payment_state = 'partial'
            else:
                rec.payment_state = 'not_paid'
    
    # ================================================================
    # DOCUMENTOS
    # ================================================================
    
    attachment_count = fields.Integer('Documentos', compute='_compute_attachment_count')
    
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'lumber.shipment.cost.line'),
                ('res_id', '=', rec.id)
            ])
    
    # ================================================================
    # NIVEL DE ASIGNACIÓN
    # ================================================================
    
    allocation_level = fields.Selection([
        ('shipment', 'Embarque'),
        ('container', 'Contenedor'),
        ('lot', 'Lote'),
    ], default='shipment', required=True)
    
    container_id = fields.Many2one('lumber.container', 'Contenedor')
    lot_id = fields.Many2one('stock.lot', 'Lote')
    
    # ================================================================
    # ESTADO
    # ================================================================
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('paid', 'Pagado'),
    ], default='draft')
    
    validated_by_id = fields.Many2one('res.users', 'Validado por', readonly=True)
    validated_date = fields.Datetime('Fecha Validación', readonly=True)
    
    notes = fields.Text('Observaciones')
    
    # ================================================================
    # MÉTODOS DE FACTURACIÓN MEJORADOS
    # ================================================================
    
    def action_validate(self):
        """Validar la línea de costo antes de facturar"""
        for rec in self:
            if not rec.partner_id:
                raise ValidationError(_("❌ Debe especificar el proveedor."))
            
            if rec.amount_usd <= 0:
                raise ValidationError(_("❌ El monto debe ser mayor a cero."))
            
            rec.write({
                'state': 'validated',
                'validated_by_id': self.env.user.id,
                'validated_date': fields.Datetime.now(),
            })
            
            # Mensaje en el chatter
            rec.message_post(
                body=_("✅ Costo validado por %s") % self.env.user.name
            )
    
    def action_create_invoice(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError("Debe tener al menos una línea para generar la factura.")
        
        invoice_lines = []
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'product_uom_id': line.uom_id.id,
                'price_unit': line.price_unit,
                # CORRECCIÓN FISCAL: Mapeo dinámico de impuestos
                'tax_ids': [(6, 0, line.partner_id.property_account_position_id.map_tax(line.product_id.taxes_id).ids if (line.partner_id and line.partner_id.property_account_position_id) else line.product_id.taxes_id.ids)],
            }))
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': self.invoice_date,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        # ...

        
        # Vincular factura con la línea de costo
        self.write({'invoice_id': invoice.id})
        
        # Mensaje de confirmación
        message = _(
            "✅ Factura creada correctamente\n"
            "• Proveedor: %s\n"
            "• Categoría: %s\n"
            "• Monto: USD %.2f\n"
            "• Cuenta contable: %s (%s)\n"
            "• Referencia: %s"
        ) % (
            self.partner_id.name,
            self.category_display,
            self.amount_usd, 
            expense_account.name, 
            expense_account.code,
            invoice.name
        )
        
        # Mensaje en el chatter
        self.message_post(body=message)
        
        # Retornar acción para abrir la factura
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura de Proveedor'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_move_type': 'in_invoice',
                'create': False
            }
        }


    def _get_expense_account(self):
        """
        Obtener cuenta de gasto desde configuración del sistema.
        
        MIGRATION PATH (4 niveles de fallback):
        1. Leer desde res.config.settings (MÉTODO PREFERIDO)
        2. Buscar en account.expense.mapping (LEGACY - deprecado)
        3. Búsqueda por código hardcodeado (LEGACY - con WARNING)
        4. Cuenta genérica de gastos (ÚLTIMA OPCIÓN)
        
        Returns:
            account.account: Cuenta contable encontrada
        
        Raises:
            UserError: Si no se puede determinar ninguna cuenta
        """
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        
        # ================================================================
        # MAPEO DE CATEGORÍAS A PARÁMETROS DE CONFIGURACIÓN
        # ================================================================
        config_mapping = {
            'madera': 'madenat_vendor_payment.account_expense_lumber',
            'transport': 'madenat_vendor_payment.account_expense_transport',
            'consolidation': 'madenat_vendor_payment.account_expense_consolidation',
            'naviera': 'madenat_vendor_payment.account_expense_naviera',
            'aduana': 'madenat_vendor_payment.account_expense_aduana',
            'seguros': 'madenat_vendor_payment.account_expense_seguros',
            'portuario': 'madenat_vendor_payment.account_expense_portuario',
            'otros': 'madenat_vendor_payment.account_expense_otros',
        }
        
        # ================================================================
        # NIVEL 1: CONFIGURACIÓN DEL SISTEMA (MÉTODO PREFERIDO)
        # ================================================================
        config_key = config_mapping.get(
            self.supplier_category,
            'madenat_vendor_payment.account_expense_otros'
        )
        account_id = IrConfigParam.get_param(config_key, default=False)
        
        if account_id:
            try:
                account = self.env['account.account'].browse(int(account_id))
                if account.exists():
                    _logger.info(
                        f"[CONFIG] Cuenta encontrada desde configuración: "
                        f"{account.code} - {account.name} | "
                        f"Categoría: {self.supplier_category} | "
                        f"Proveedor: {self.partner_id.name} | "
                        f"Monto: USD {self.amount_usd:,.2f}"
                    )
                    return account
            except (ValueError, TypeError) as e:
                _logger.warning(
                    f"[CONFIG ERROR] ID de cuenta inválido en configuración: "
                    f"{account_id} para clave {config_key}: {e}"
                )
        
        # ================================================================
        # NIVEL 2: account.expense.mapping (LEGACY - DEPRECADO)
        # ================================================================
        mapping = self.env['account.expense.mapping'].search([
            ('vendor_category', '=', self.supplier_category),
            ('active', '=', True),
            ('expense_account_id', '!=', False)
        ], limit=1)
        
        if mapping and mapping.expense_account_id:
            _logger.warning(
                f"[DEPRECATION WARNING] Usando account.expense.mapping para "
                f"categoría '{self.supplier_category}'. "
                f"MIGRAR A: Contabilidad → Configuración → Ajustes → "
                f"Mapeo de Cuentas MADENAT"
            )
            return mapping.expense_account_id
        
        # ================================================================
        # NIVEL 3: CÓDIGO HARDCODEADO (LEGACY - CON WARNING)
        # ================================================================
        legacy_codes = {
            'madera': '610100',
            'transport': '624001',
            'consolidation': '624005',
            'naviera': '624010',
            'aduana': '624015',
            'seguros': '624020',
            'portuario': '624025',
            'otros': '624030',
        }
        
        legacy_code = legacy_codes.get(self.supplier_category, '624030')
        
        # Búsqueda exacta por código
        account = self.env['account.account'].search([
            ('code', '=', legacy_code)
        ], limit=1)
        
        if account:
            _logger.warning(
                f"[LEGACY MODE] Cuenta encontrada por código hardcodeado "
                f"'{legacy_code}' para categoría '{self.supplier_category}'. "
                f"⚠️ ACCIÓN REQUERIDA: Configurar en Contabilidad → "
                f"Configuración → Ajustes → Mapeo de Cuentas MADENAT"
            )
            return account
        
        # Búsqueda con LIKE (más flexible)
        account = self.env['account.account'].search([
            ('code', 'like', f'{legacy_code}%'),
            ('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])
        ], limit=1)
        
        if account:
            _logger.warning(
                f"[LEGACY MODE - FUZZY] Cuenta encontrada por búsqueda "
                f"aproximada '{account.code}' (buscaba '{legacy_code}') "
                f"para categoría '{self.supplier_category}'. "
                f"⚠️ Verificar que sea correcta."
            )
            return account

        raise UserError(_(
            "No se encontró configuración contable para la categoría %s. "
            "Configure en Ajustes > MADENAT > Mapeo de Gastos."
        ) % self.supplier_category)



    def _get_invoice_description(self):
        """Generar descripción detallada para la factura"""
        base_description = f"{self.category_display}: {self.name or 'Costo de embarque'}"
        
        # Agregar información contextual
        details = []
        
        if self.shipment_id:
            details.append(f"Embarque: {self.shipment_id.name}")
        
        if self.container_id:
            details.append(f"Contenedor: {self.container_id.name}")
        
        if self.lot_id:
            details.append(f"Lote: {self.lot_id.name}")
        
        if details:
            return f"{base_description} - {', '.join(details)}"
        
        return base_description


    # ================================================================
    # ACCIONES DE PAGO Y GESTIÓN
    # ================================================================
    
    def action_register_payment(self):
        """Registrar pago de la factura asociada"""
        self.ensure_one()
        
        if not self.invoice_id:
            raise ValidationError(_("❌ Debe crear primero la factura."))
        
        if self.invoice_id.payment_state == 'paid':
            raise ValidationError(_("❌ La factura ya está pagada."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrar Pago'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_ids': [self.invoice_id.id],
                'default_amount': self.invoice_id.amount_residual,
            },
        }
    
    def action_view_invoice(self):
        """Abrir la factura asociada"""
        self.ensure_one()
        
        if not self.invoice_id:
            raise ValidationError(_("No hay factura asociada."))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False}
        }
    
    def action_view_attachments(self):
        """Ver documentos adjuntos"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'domain': [
                ('res_model', '=', 'lumber.shipment.cost.line'), 
                ('res_id', '=', self.id)
            ],
            'view_mode': 'kanban,list,form',
            'name': _('Documentos'),
            'context': {
                'default_res_model': 'lumber.shipment.cost.line', 
                'default_res_id': self.id
            },
        }
    
    def action_mark_as_paid(self):
        """Marcar manualmente como pagado (para casos especiales)"""
        self.ensure_one()
        
        if not self.invoice_id:
            raise ValidationError(_("No hay factura asociada para marcar como pagada."))
        
        self.write({'state': 'paid'})
        
        self.message_post(
            body=_("💰 Costo marcado como pagado manualmente por %s") % self.env.user.name
        )


    # ================================================================
    # CONSTRAINTS Y VALIDACIONES
    # ================================================================
    
    @api.constrains('amount_usd')
    def _check_positive_amount(self):
        """Validar que el monto sea positivo"""
        for rec in self:
            if rec.amount_usd <= 0:
                raise ValidationError(_("❌ El monto debe ser mayor a cero."))
    
    @api.constrains('container_id', 'allocation_level')
    def _check_container_allocation(self):
        """Validar que si el nivel es contenedor, se especifique contenedor"""
        for rec in self:
            if rec.allocation_level == 'container' and not rec.container_id:
                raise ValidationError(
                    _("❌ Debe especificar un contenedor cuando el nivel de asignación es 'Contenedor'.")
                )
    
    @api.constrains('lot_id', 'allocation_level')
    def _check_lot_allocation(self):
        """Validar que si el nivel es lote, se especifique lote"""
        for rec in self:
            if rec.allocation_level == 'lot' and not rec.lot_id:
                raise ValidationError(
                    _("❌ Debe especificar un lote cuando el nivel de asignación es 'Lote'.")
                )