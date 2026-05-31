# -*- coding: utf-8 -*-
"""
Wizard para generación de facturas desde consolidaciones aprobadas.
Integración nativa con account.move de Odoo 18 CE.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LumberBillingInvoiceWizard(models.TransientModel):
    """
    Wizard para crear facturas de cliente desde consolidaciones aprobadas.
    Solo María Victoria puede acceder después de la aprobación de Felipe.
    """
    _name = 'lumber.billing.invoice.wizard'
    _description = 'Wizard de Generación de Facturas'

    # ============================================================================
    # CAMPOS PRINCIPALES
    # ============================================================================
    
    consolidation_id = fields.Many2one(
        comodel_name='lumber.billing.consolidation',
        string='Consolidación',
        required=True,
        readonly=True,
        help='Consolidación desde la cual se generará la factura'
    )
    
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        related='consolidation_id.customer_id',
        readonly=True
    )
    
    shipment_id = fields.Many2one(
        comodel_name='lumber.export.shipment',
        string='Embarque',
        related='consolidation_id.shipment_id',
        readonly=True
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.ref('base.USD'),
        help='Moneda de la factura'
    )
    
    invoice_date = fields.Date(
        string='Fecha Factura',
        required=True,
        default=fields.Date.context_today,
        help='Fecha de emisión de la factura'
    )
    
    invoice_date_due = fields.Date(
        string='Fecha Vencimiento',
        help='Fecha de vencimiento de pago (opcional)'
    )
    
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Términos de Pago',
        help='Términos de pago que se aplicarán a la factura'
    )
    
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Diario Contable',
        required=True,
        domain="[('type', '=', 'sale')]",
        help='Diario contable donde se registrará la factura'
    )

    # ✅ NUEVO: Posición Fiscal para manejar impuestos (Exportación vs Nacional)
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Posición Fiscal',
        help='Define el tratamiento de impuestos (ej: Exportación = Sin IVA)',
        compute='_compute_fiscal_position',
        store=True,
        readonly=False
    )
    
    invoice_origin = fields.Char(
        string='Origen',
        compute='_compute_invoice_origin',
        help='Referencia de origen de la factura'
    )
    
    notes = fields.Text(
        string='Notas Internas',
        help='Notas que aparecerán en la factura'
    )
    
    # Líneas editables
    line_ids = fields.One2many(
        comodel_name='lumber.billing.invoice.wizard.line',
        inverse_name='wizard_id',
        string='Líneas de Factura',
        help='Líneas editables antes de generar la factura'
    )
    
    # Totales
    total_amount = fields.Monetary(
        string='Total',
        compute='_compute_totals',
        currency_field='currency_id',
        help='Total de la factura'
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    
    @api.depends('customer_id')
    def _compute_fiscal_position(self):
        """Calcula la posición fiscal apropiada para la factura.

        Este método busca la posición fiscal nativa de Odoo asociada al cliente. Si
        no existe una posición definida y el cliente es extranjero, intenta detectar
        una posición de exportación activa.

        Nota:
            La posición fiscal se utiliza automáticamente para ajustar impuestos en
            facturas de exportación dentro de Odoo 18 CE.

        Returns:
            None: Actualiza el campo `fiscal_position_id` del wizard.
        """
        for wizard in self:
            fp = False
            if wizard.customer_id:
                # 1. Intentar obtener la posición fiscal nativa de Odoo para el cliente
                fp = self.env['account.fiscal.position']._get_fiscal_position(
                    wizard.customer_id
                )
                
                # 2. Fallback: Si es cliente extranjero y no tiene posición, buscar 'Export'
                if not fp and wizard.customer_id.country_id != self.env.company.country_id:
                    export_pos = self.env['account.fiscal.position'].search([
                        ('name', 'ilike', 'export'),
                        ('company_id', '=', self.env.company.id),
                        ('active', '=', True)
                    ], limit=1)
                    if export_pos:
                        fp = export_pos
            
            wizard.fiscal_position_id = fp

    @api.depends('consolidation_id', 'shipment_id')
    def _compute_invoice_origin(self):
        """Genera la referencia de origen para la factura.

        Construye el campo `invoice_origin` concatenando la consolidación y el
        embarque asociado.

        Returns:
            None: Actualiza el campo `invoice_origin` del wizard.
        """
        for wizard in self:
            if wizard.consolidation_id and wizard.shipment_id:
                wizard.invoice_origin = f"{wizard.consolidation_id.name} / {wizard.shipment_id.name}"
            else:
                wizard.invoice_origin = False
    
    @api.depends('line_ids.price_subtotal')
    def _compute_totals(self):
        """Calcula el total de la factura.

        Suma los subtotales de todas las líneas del wizard para presentar el total
        de la factura antes de su creación.

        Returns:
            None: Actualiza el campo `total_amount` del wizard.
        """
        for wizard in self:
            wizard.total_amount = sum(wizard.line_ids.mapped('price_subtotal'))

    # ============================================================================
    # DEFAULT GET
    # ============================================================================
    
    @api.model
    def default_get(self, fields_list):
        """Carga valores iniciales cuando se abre el wizard.

        Valida que la consolidación esté en estado `ready_billing`, que tenga líneas
        y un cliente asignado. Genera las líneas del wizard a partir de las líneas de
        consolidación existentes.

        Args:
            fields_list (list): Lista de campos solicitados en la carga inicial.

        Returns:
            dict: Valores por defecto para los campos del wizard.

        Raises:
            UserError: Si la consolidación no está en estado correcto, no tiene líneas
                o no tiene cliente asignado.
        """
        res = super().default_get(fields_list)
        
        consolidation_id = res.get('consolidation_id') or self.env.context.get('default_consolidation_id')
        if not consolidation_id:
            return res
        
        consolidation = self.env['lumber.billing.consolidation'].browse(consolidation_id)
        
        if consolidation.state != 'ready_billing':
            raise UserError(_("Solo se pueden facturar consolidaciones en estado 'Listo para Facturar'."))
            
        if not consolidation.line_ids:
            raise UserError(_("La consolidación no tiene líneas."))
            
        if not consolidation.customer_id:
            raise UserError(_("La consolidación no tiene cliente asignado."))
        
        lines = []
        for line in consolidation.line_ids:
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
                'price_unit': line.price_unit_usd,
                'consolidation_line_id': line.id,
            }))
        
        res['line_ids'] = lines
        
        default_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if default_journal:
            res['journal_id'] = default_journal.id
        
        return res

    # ============================================================================
    # ACTION CREATE INVOICE
    # ============================================================================
    
    def action_create_invoice(self):
        """Genera la factura nativa de Odoo desde el wizard.

        Crea un registro `account.move` con las líneas definidas en el wizard,
        aplica la posición fiscal calculada y actualiza la consolidación para marcarla
        como facturada.

        Returns:
            dict: Acción para abrir la factura recién creada en pantalla.

        Raises:
            UserError: Si no existen líneas en el wizard.

        Nota:
            Esta acción integra el wizard con `account.move` nativo de Odoo 18 CE.
            La posición fiscal automática para exportaciones se aplica a los impuestos
            mapeando las tasas correspondientes.
        """
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Debe tener al menos una línea."))
        
        invoice_lines = []
        for line in self.line_ids:
            
            # ✅ APLICAR POSICIÓN FISCAL A LOS IMPUESTOS
            taxes = line.product_id.taxes_id
            if self.fiscal_position_id:
                taxes = self.fiscal_position_id.map_tax(taxes)
            
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'product_uom_id': line.uom_id.id,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, taxes.ids)], # Impuestos ya mapeados (ej: vacíos si es exportación)
            }))
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': self.invoice_date,
            'invoice_date_due': self.invoice_date_due,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'invoice_origin': self.invoice_origin,
            'invoice_payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'fiscal_position_id': self.fiscal_position_id.id if self.fiscal_position_id else False, # ✅ Guardar en factura
            'narration': self.notes,
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.consolidation_id.write({
            'invoice_id': invoice.id,
            'state': 'billed',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        
        self.consolidation_id.message_post(
            body=_("Factura %s generada por %s") % (invoice.name, self.env.user.name)
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura Generada'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_move_type': 'out_invoice'}
        }

class LumberBillingInvoiceWizardLine(models.TransientModel):
    _name = 'lumber.billing.invoice.wizard.line'
    _description = 'Línea de Wizard de Factura'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('lumber.billing.invoice.wizard', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    consolidation_line_id = fields.Many2one('lumber.billing.consolidation.line')
    product_id = fields.Many2one('product.product', required=True)
    name = fields.Char(required=True)
    quantity = fields.Float(required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', required=True)
    price_unit = fields.Float(required=True)
    price_subtotal = fields.Monetary(compute='_compute_price_subtotal', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='wizard_id.currency_id')

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        """Calcula el subtotal de cada línea del wizard.

        Multiplica la cantidad por el precio unitario para obtener el subtotal.

        Returns:
            None: Actualiza el campo `price_subtotal` de la línea.
        """
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza valores de la línea al cambiar el producto.

        Ajusta el nombre, la unidad de medida y el precio unitario según el
        producto seleccionado.

        Returns:
            None: Actualiza los campos de la línea en la vista del wizard.
        """
        if self.product_id:
            self.name = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            if self.product_id.list_price:
                self.price_unit = self.product_id.list_price