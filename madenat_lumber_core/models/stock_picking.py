# REEMPLAZA todo el contenido del archivo con esto:
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ==========================================================================
    # --- RELACIÓN CON RECEPCIÓN MADENAT ---
    # ==========================================================================
    reception_id = fields.Many2one(
        'lumber.reception',
        'Recepción de Guía MADENAT',
        copy=False,
        index=True,
    )

    # El campo de lotes ahora es un 'related' a través de la recepción, mucho más eficiente.
    lumber_lot_ids = fields.One2many(
        related='reception_id.lot_ids',
        string='Lotes MADENAT en esta Recepción'
    )

    # --- SISTEMA DE VALIDACIÓN (CORREGIDO) ---
    # Se recalcula cuando cambian las validaciones de los lotes relacionados
    reception_technical_validation = fields.Selection(
        [('pending', 'Pendiente'), ('approved', 'Aprobado'), ('rejected', 'Rechazado')],
        string='Validación Técnica Recepción',
        compute='_compute_validation_status',
        store=True,
        default='pending',
        tracking=True
    )
    reception_financial_validation = fields.Selection(
        [('pending', 'Pendiente'), ('approved', 'Aprobado'), ('rejected', 'Rechazado')],
        string='Validación Financiera Recepción',
        compute='_compute_validation_status',
        store=True,
        default='pending',
        tracking=True
    )

    # ===========================
    # MÉTRICAS AGREGADAS POR RECEPCIÓN
    # ===========================
    total_volume_m3 = fields.Float(
        string='Volumen Total (m³)', 
        compute='_compute_reception_totals',
        store=True,
        digits=(16, 3)
    )
    
    total_volume_mbf = fields.Float(
        string='Volumen Total (MBF)', 
        compute='_compute_reception_totals',
        store=True,
        digits=(16, 3)
    )
    
    total_pieces = fields.Integer(
        string='Total Piezas', 
        compute='_compute_reception_totals',
        store=True
    )
    
    total_wood_cost_usd = fields.Float(
        string='Costo Madera Total (USD)', 
        compute='_compute_reception_totals',
        store=True,
        digits=(16, 2)
    )

    total_logistic_cost_usd = fields.Float(
    string='Costo Logístico Total (USD)', 
    compute='_compute_reception_totals',
    store=True,
    digits=(16, 2)
    )

    total_process_cost_usd = fields.Float(
        string='Costo Procesamiento Total (USD)', 
        compute='_compute_reception_totals',
        store=True,
        digits=(16, 2)
    )

    total_other_cost_usd = fields.Float(
        string='Otros Costos Total (USD)', 
        compute='_compute_reception_totals',
        store=True,
        digits=(16, 2)
    )

    # ===========================
    # CÁLCULOS AGREGADOS
    # ===========================
    @api.depends(
        'lumber_lot_ids.volumen_m3',
        'lumber_lot_ids.volumen_mbf',
        'lumber_lot_ids.piezas',
        'lumber_lot_ids.cost_line_ids.amount_usd',
        'lumber_lot_ids.cost_line_ids.cost_type',
        'move_ids.product_uom_qty' # 🚀 AGREGAMOS ESTA DEPENDENCIA
    )
    def _compute_reception_totals(self):
        """Calcula métricas agregadas para toda la recepción con Fallback seguro"""
        for picking in self:
            # 1. Intentamos sumar desde los Lotes (Si la Guía está conectada)
            valid_lots = picking.lumber_lot_ids.filtered(
                lambda l: l.espesor_mm > 0 and l.ancho_mm > 0 and l.largo_m > 0
            )
            
            if valid_lots:
                picking.total_volume_m3 = sum(valid_lots.mapped('volumen_m3'))
                picking.total_volume_mbf = sum(valid_lots.mapped('volumen_mbf'))
                picking.total_pieces = sum(valid_lots.mapped('piezas'))
            else:
                # 🚀 2. FALLBACK SEGURO: Si no hay guía conectada, sumamos los movimientos reales
                # Como comprobamos en SQL, move_ids.product_uom_qty tiene los 4.50 correctos
                picking.total_volume_m3 = sum(picking.move_ids.mapped('product_uom_qty'))
                picking.total_volume_mbf = picking.total_volume_m3 * 0.4237 # Factor de conversión
                picking.total_pieces = 0

            # Costeo modular para madera (Se mantiene igual):
            picking.total_wood_cost_usd = sum(
                line.amount_usd for lot in valid_lots for line in lot.cost_line_ids if line.cost_type == 'wood'
            )
            picking.total_logistic_cost_usd = sum(
                line.amount_usd for lot in valid_lots for line in lot.cost_line_ids if line.cost_type == 'logistic'
            )
            picking.total_process_cost_usd = sum(
                line.amount_usd for lot in valid_lots for line in lot.cost_line_ids if line.cost_type == 'process'
            )
            picking.total_other_cost_usd = sum(
                line.amount_usd for lot in valid_lots for line in lot.cost_line_ids if line.cost_type == 'other'
            )
    
    
    @api.depends('lumber_lot_ids.technical_validation', 'lumber_lot_ids.financial_validation')
    def _compute_validation_status(self):
        """Calcula el estado de validación agregado basado en los lotes hijos."""
        for picking in self:
            if not picking.lumber_lot_ids:
                picking.reception_technical_validation = 'pending'
                picking.reception_financial_validation = 'pending'
                continue
    
            # Lógica Técnica
            if all(l.technical_validation == 'approved' for l in picking.lumber_lot_ids):
                picking.reception_technical_validation = 'approved'
            elif any(l.technical_validation == 'rejected' for l in picking.lumber_lot_ids):
                picking.reception_technical_validation = 'rejected'
            else:
                picking.reception_technical_validation = 'pending'
    
            # Lógica Financiera
            if all(l.financial_validation == 'approved' for l in picking.lumber_lot_ids):
                picking.reception_financial_validation = 'approved'
            elif any(l.financial_validation == 'rejected' for l in picking.lumber_lot_ids):
                picking.reception_financial_validation = 'rejected'
            else:
                picking.reception_financial_validation = 'pending'
        
    # ===========================
    # ACCIONES DE VALIDACIÓN MASIVA
    # ===========================
    def action_validate_all_technical(self):
        """Valida técnicamente TODOS los lotes de la recepción"""
        self.ensure_one()
        pending_lots = self.lumber_lot_ids.filtered(lambda l: l.technical_validation == 'pending')
        
        if pending_lots:
            pending_lots.action_approve_technical()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validación Exitosa',
                    'message': f'Se validaron {len(pending_lots)} lotes técnicamente',
                    'type': 'success',
                    'sticky': False,
                }
            }
    
    def action_reject_all_technical(self):
        """Rechaza técnicamente TODOS los lotes de la recepción"""
        self.ensure_one()
        pending_lots = self.lumber_lot_ids.filtered(lambda l: l.technical_validation == 'pending')
        
        if pending_lots:
            pending_lots.action_reject_technical()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rechazo Exitoso',
                    'message': f'Se rechazaron {len(pending_lots)} lotes técnicamente',
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
    def action_validate_all_financial(self):
        """Valida financieramente TODOS los lotes de la recepción"""
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise ValidationError("Solo los gestores de inventario pueden realizar esta acción")
        
        pending_lots = self.lumber_lot_ids.filtered(lambda l: l.financial_validation == 'pending')
        
        if pending_lots:
            pending_lots.action_approve_financial()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validación Exitosa',
                    'message': f'Se validaron {len(pending_lots)} lotes financieramente',
                    'type': 'success',
                    'sticky': False,
                }
            }
    
    def action_open_lumber_lots(self):
        """Abre la vista de lotes MADENAT de esta recepción"""
        self.ensure_one()
        return {
            'name': f'Lotes MADENAT - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('reception_id', '=', self.reception_id.id)],
            'context': {
                'default_reception_id': self.reception_id.id,
                'search_default_technical_pending': 1
            }
        }
 # ===========================
    # MÉTODO: CREAR PICKING DESDE RECEPCIÓN MADENAT (RAÍZ SANEADA)
    # ===========================
    def create_from_lumber_reception(self, po, pl_data, location_dest_id, reception_id=False):
        """✅ Crea picking vinculando Lotes, Cantidades Hechas y la Recepción de Origen"""        
        try:
            picking_type = self.env.ref('stock.picking_type_in')
            if not picking_type:
                raise ValidationError("No se encontró tipo de albarán de entrada")
                
            # 1. CREACIÓN DEL ALBARÁN (Saneando la Orfandad)
            picking_vals = {
                'picking_type_id': picking_type.id,
                'partner_id': po.partner_id.id,
                'location_dest_id': location_dest_id,
                'location_id': picking_type.default_location_src_id.id,
                'origin': f"{po.name}",
            }
            # Si nos pasan la recepción, la enlazamos desde el nacimiento
            if reception_id:
                picking_vals['reception_id'] = reception_id
                
            picking = self.create(picking_vals)
            _logger.info(f"✅ Picking creado y vinculado: {picking.name}")
                
            # 2. CREACIÓN DE MOVIMIENTOS Y LÍNEAS DETALLADAS (La Verdad Comercial)
            for line in pl_data.get('lines', []):
                product_code = line.get('product_code')
                vol_nominal = float(line.get('volume_m3', 0))
                lot_name = line.get('lot_name') # Necesitamos saber qué lote es
                
                product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                
                if product:
                    # A. Creamos el Movimiento General (La Demanda)
                    move = self.env['stock.move'].create({
                        'picking_id': picking.id, 
                        'product_id': product.id,
                        'product_uom_qty': vol_nominal, # Demanda
                        'product_uom': self.env.ref('uom.product_uom_cubic_meter').id,
                        'location_id': picking.location_id.id, 
                        'location_dest_id': location_dest_id,
                        'name': f"Mov {product_code} - {vol_nominal} m³",
                    })
                    
                    # B. Buscamos el Lote Real que ya fue creado en la DB
                    lot = False
                    if lot_name and reception_id:
                        lot = self.env['stock.lot'].search([
                            ('name', '=', lot_name),
                            ('reception_id', '=', reception_id)
                        ], limit=1)
                    
                    # C. Creamos la Operación Detallada (El "Hecho" vinculado al Lote)
                    # ESTO ES LO QUE MATA EL 0.00 PARA SIEMPRE
                    if lot:
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'picking_id': picking.id,
                            'product_id': product.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'lot_id': lot.id, # VINCULACIÓN MAESTRA
                            'quantity': vol_nominal, # CANTIDAD HECHA (Done)
                        })
                        
            _logger.info(f"✅ Picking {picking.name} procesado con éxito y lotes enlazados.")
            return picking
                
        except Exception as e:
            _logger.error(f"❌ Error creando picking: {str(e)}")
            raise ValidationError(f"Error creando albarán: {str(e)}")
