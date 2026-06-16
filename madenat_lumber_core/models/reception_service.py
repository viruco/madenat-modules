# -*- coding: utf-8 -*-
import logging
from odoo import _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

class LumberReceptionService:
    """
    🚀 SERVICIO DESACOPLADO: Creación de Lotes y Movimientos
    Extrae la complejidad de lumber_reception.py para mejorar mantenibilidad.
    """
    def __init__(self, env):
        self.env = env

    def create_lots_from_staging(self, reception):
        """
        Mueve los datos de lumber.reception.line (Staging) a stock.lot real.
        
        🛡️ IDEMPOTENCIA v2.0 (2026-06-11):
        - search-before-create por clave natural: name + reception_id + product_id
        - Si el lote ya existe para esta recepción, se reutiliza (actualiza) en vez de duplicar.
        - Si no existe, se crea.
        - Logging explícito de cada decisión para trazabilidad forense.
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'omitted': 0}
        
        # Pre-cargar todos los lotes existentes de esta recepción en un solo query
        StockLot = self.env['stock.lot']
        existing_lots = StockLot.search([
            ('reception_id', '=', reception.id)
        ])
        # Índice por (name, product_id) para lookup O(1)
        existing_index = {}
        for lot in existing_lots:
            key = (lot.name, lot.product_id.id)
            existing_index[key] = lot
        
        for line in reception.reception_line_ids:
            lot_name = line.lot_name
            product_id = line.product_id.id
            lookup_key = (lot_name, product_id)
            
            # ── BASE VALS (compartidos entre create y update) ──
            lot_vals = {
                'name': lot_name,
                'ref': lot_name,
                'product_id': product_id,
                'reception_id': reception.id,
                'subproducto_id': line.subproduct_id.id if line.subproduct_id else False,
                'piezas': line.pieces,
                'espesor_mm': line.thickness,
                'ancho_mm': line.width,
                'largo_m': line.length,
                'volume_purchase_m3': line.vol_purchase_m3,
                'volumen_m3': line.vol_purchase_m3,
                'vol_shipment_m3': line.vol_shipment_m3,
                'espesor_inch_frac': line.thickness_visual or '',
                'ancho_inch_frac': line.width_visual or '',
                'thickness_visual': line.thickness_visual or '',
                'width_visual': line.width_visual or '',
                'length_ft': line.length_input_raw if line.lengthuom == 'ft' else False,
            }
            
            existing = existing_index.get(lookup_key)
            
            if existing:
                # ♻️ REUTILIZAR: actualizar dimensiones y volúmenes
                _logger.info(
                    "♻️ LumberReceptionService: reutilizando lote existente "
                    "name=%s product_id=%s lot_id=%s reception=%s",
                    lot_name, product_id, existing.id, reception.name
                )
                existing.write(lot_vals)
                stats['updated'] += 1
            else:
                # ✨ CREAR: primer procesamiento de esta línea
                _logger.info(
                    "✨ LumberReceptionService: creando nuevo lote "
                    "name=%s product_id=%s reception=%s",
                    lot_name, product_id, reception.name
                )
                StockLot.create(lot_vals)
                stats['created'] += 1
        
        _logger.info(
            "📊 LumberReceptionService: resumen recepción %s — "
            "creados=%d actualizados=%d omitidos=%d",
            reception.name, stats['created'], stats['updated'], stats['omitted']
        )
        return stats

    def create_stock_picking(self, reception):
        """
        📦 MOTOR DE STOCK V5.4 (Desacoplado)
        Crea Albarán y Movimientos asegurando idéntica Demanda vs Hecho.
        """
        uom_cubic = self.env.ref('uom.product_uom_cubic_meter')
        
        # 1. Búsqueda de operación
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not picking_type:
            raise UserError("No se encontró tipo de operación 'Recepción'.")

        # 2. Cabecera del Albarán
        picking = self.env['stock.picking'].create({
            'partner_id': reception.supplier_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': reception.location_id.id or picking_type.default_location_dest_id.id,
            'origin': reception.name, 
            'reception_id': reception.id,
            'company_id': self.env.company.id,
        })

        # 3. Generación de Movimientos
        for lot in reception.lot_ids:
            safe_qty = float_round(lot.volume_purchase_m3, precision_digits=3)

            move = self.env['stock.move'].create({
                'name': f"Lote: {lot.name}",
                'product_id': lot.product_id.id,
                'product_uom_qty': safe_qty,
                'product_uom': uom_cubic.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'company_id': self.env.company.id,
                'picked': True, 
            })
            
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': lot.product_id.id,
                'lot_id': lot.id,
                'quantity': safe_qty,
                'product_uom_id': uom_cubic.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'picked': True,
            })

        # 4. VALIDACIÓN FINAL
        if picking.move_ids:
            picking.action_confirm()
            picking.action_assign()
            picking.button_validate()
            
        return picking

    def cleanup_orphan_moves(self, origins):
        """
        🧹 Elimina stock.moves huérfanos generados por estas recepciones.
        """
        # 🔒 TD-001: Guardia de grupo antes de eliminar stock.moves
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(
                "No tienes permisos para eliminar movimientos de stock huérfanos.\n"
                "Se requiere el grupo 'Inventario / Administrador'."
            )
        if not origins:
            return
            
        moves = self.env['stock.move'].sudo().search([
            ('origin', 'in', origins),
            ('picking_id', '=', False),
        ])
        if not moves:
            return

        _logger.info("🧹 MADENAT cleanup: eliminando %d stock.moves huérfanos para guías: %s", len(moves), origins)

        moves.sudo().mapped('move_line_ids').unlink()
        moves.sudo().write({'state': 'draft'})
        moves.sudo().unlink()