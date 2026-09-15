# -*- coding: utf-8 -*-
import logging
from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round
from psycopg2.errors import IntegrityError

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

        IDEMPOTENCIA v3.0 (2026-09-02):
        - Agrupa el staging por clave de identidad (producto, lote normalizado,
          compañía) y valida compatibilidad de atributos de nivel de lote ANTES
          de cualquier escritura de stock.
        - Crea o reutiliza un único stock.lot por grupo, acotado a la misma
          recepción (reception_id) y con savepoint + re-búsqueda ante colisión
          UNIQUE (principios de _create_or_get_lot de Procesados, adaptados a
          recepción directa).
        - La composición por fila (largo, piezas, volumen) se preserva luego en
          stock.move.line, no en el lote.
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'omitted': 0}
        company = self.env.company

        # 1. Agrupar por clave de identidad y validar compatibilidad.
        groups = {}
        for line in reception.reception_line_ids:
            lot_name = (line.lot_name or '').strip()
            key = (line.product_id.id, lot_name, company.id)
            if key in groups:
                self._check_lot_compatibility(groups[key][0], line, lot_name)
                groups[key].append(line)
            else:
                groups[key] = [line]

        # 2. Un stock.lot por grupo (create-or-get idempotente).
        for (product_id, lot_name, company_id), lines in groups.items():
            lot_vals = self._build_lot_vals(reception, lines[0], lines)
            lot, created = self._create_or_get_reception_lot(
                reception, product_id, lot_name, company_id, lot_vals
            )
            stats['created' if created else 'updated'] += 1
            self._audit_lot(
                reception,
                'lot_creation' if created else 'lot_update',
                lot_name,
                lot,
                created,
            )

        _logger.info(
            "📊 LumberReceptionService: resumen recepción %s — "
            "creados=%d actualizados=%d omitidos=%d",
            reception.name, stats['created'], stats['updated'], stats['omitted']
        )
        return stats

    def _check_lot_compatibility(self, ref, line, lot_name):
        """Valida que dos filas del mismo lote compartan los atributos de nivel de
        lote. Las variaciones por fila (largo, piezas, volumen) se preservan en
        stock.move.line y no invalidan la reutilización del lote."""
        conflicts = []
        if float_compare(ref.thickness, line.thickness, precision_digits=6) != 0:
            conflicts.append('espesor')
        if float_compare(ref.width, line.width, precision_digits=6) != 0:
            conflicts.append('ancho')
        if float_compare(ref.thickness_nominal or 0.0, line.thickness_nominal or 0.0, precision_digits=6) != 0:
            conflicts.append('espesor nominal')
        if float_compare(ref.width_nominal or 0.0, line.width_nominal or 0.0, precision_digits=6) != 0:
            conflicts.append('ancho nominal')
        ref_sub = ref.subproduct_id.id if ref.subproduct_id else False
        line_sub = line.subproduct_id.id if line.subproduct_id else False
        if ref_sub != line_sub:
            conflicts.append('subproducto')
        if conflicts:
            raise UserError(
                _("El lote '%s' aparece en varias filas con atributos de nivel de "
                  "lote incompatibles (%s). Corrija las líneas %s y %s antes de "
                  "enviar a inventario.")
                % (lot_name, ', '.join(conflicts), ref.id, line.id)
            )

    def _build_lot_vals(self, reception, ref_line, lines):
        """Construye los vals del lote: atributos comunes de la primera fila y
        totales consolidados (piezas y volúmenes) del grupo completo."""
        total_pieces = int(sum((l.pieces or 0) for l in lines))
        total_purchase = sum((l.vol_purchase_m3 or 0.0) for l in lines)
        total_shipment = sum((l.vol_shipment_m3 or 0.0) for l in lines)
        lot_name = (ref_line.lot_name or '').strip()
        return {
            'name': lot_name,
            'ref': lot_name,
            'product_id': ref_line.product_id.id,
            'reception_id': reception.id,
            'subproducto_id': ref_line.subproduct_id.id if ref_line.subproduct_id else False,
            'piezas': total_pieces,
            'espesor_mm': ref_line.thickness,
            'ancho_mm': ref_line.width,
            'largo_m': ref_line.length,
            'volume_purchase_m3': total_purchase,
            'volumen_m3': total_purchase,
            'vol_shipment_m3': total_shipment,
            'espesor_inch_frac': ref_line.thickness_visual or '',
            'ancho_inch_frac': ref_line.width_visual or '',
            'thickness_visual': ref_line.thickness_visual or '',
            'width_visual': ref_line.width_visual or '',
            'length_ft': ref_line.length_input_raw if ref_line.lengthuom == 'ft' else False,
            'purchase_order_id': reception.purchase_id.id if reception.purchase_id else False,
            'supplier_id': reception.supplier_id.id if reception.supplier_id else False,
            'espesor_nominal_mm': ref_line.thickness_nominal or 0.0,
            'ancho_nominal_mm': ref_line.width_nominal or 0.0,
        }

    def _create_or_get_reception_lot(self, reception, product_id, lot_name,
                                     company_id, lot_vals):
        """Crea o recupera el stock.lot de esta recepción para la clave dada.

        Reutiliza los principios de _create_or_get_lot de Procesados, pero con el
        discriminador de origen correcto para recepción directa: reception_id.
        """
        StockLot = self.env['stock.lot']
        domain = [
            ('reception_id', '=', reception.id),
            ('name', '=', lot_name),
            ('product_id', '=', product_id),
            ('company_id', 'in', [company_id, False]),
        ]
        StockLot.flush_model(['name', 'product_id', 'company_id', 'reception_id'])
        lot = StockLot.search(domain, limit=1)
        if lot:
            lot.write(lot_vals)
            return lot, False
        try:
            with self.env.cr.savepoint():
                lot = StockLot.create(lot_vals)
            return lot, True
        except (IntegrityError, ValidationError):
            _logger.warning(
                "⚠️ Colisión UNIQUE en stock.lot para name=%s product_id=%s "
                "reception_id=%s — reutilizando lote de la misma recepción.",
                lot_name, product_id, reception.id
            )
            StockLot.flush_model(['name', 'product_id', 'company_id', 'reception_id'])
            StockLot.invalidate_model(['name', 'product_id', 'company_id', 'reception_id'])
            lot = StockLot.search(domain, limit=1)
            if lot:
                lot.write(lot_vals)
                return lot, False
            raise

    def _audit_lot(self, reception, action_type, lot_name, lot, created):
        """Registra en madenat.audit.log el outcome del lote (creación/reuso),
        siguiendo el contrato de auditoría de recepción (reception_id + batch_id)."""
        self.env['madenat.audit.log'].sudo().create({
            'reception_id': reception.id,
            'action_type': action_type,
            'description': (
                "Lote '%s' %s (stock.lot #%s) en la recepción %s."
                % (lot_name, 'creado' if created else 'reutilizado', lot.id, reception.name)
            ),
            'batch_id': lot_name,
            'user_id': self.env.user.id,
        })

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

        # 3. Generación de Movimientos: una stock.move.line por fila de staging.
        lots = self.env['stock.lot'].search([('reception_id', '=', reception.id)])
        lot_by_key = {(l.name, l.product_id.id): l for l in lots}

        groups = {}
        for line in reception.reception_line_ids:
            key = ((line.lot_name or '').strip(), line.product_id.id)
            groups.setdefault(key, []).append(line)

        for key, lines in groups.items():
            lot = lot_by_key.get(key)
            if not lot:
                continue
            total_qty = sum((l.vol_purchase_m3 or 0.0) for l in lines)

            move = self.env['stock.move'].create({
                'name': f"Lote: {lot.name}",
                'product_id': lot.product_id.id,
                'product_uom_qty': float_round(total_qty, precision_digits=3),
                'product_uom': uom_cubic.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'company_id': self.env.company.id,
                'picked': True,
            })

            for line in lines:
                line_qty = float_round(line.vol_purchase_m3 or 0.0, precision_digits=3)
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'picking_id': picking.id,
                    'product_id': lot.product_id.id,
                    'lot_id': lot.id,
                    'quantity': line_qty,
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

        _logger.info("🧹 MADENAT cleanup: %d stock.moves huérfanos encontrados para guías: %s", len(moves), origins)

        # 🛡️ FIX 2026-07-01: Protección de moves con cantidad recolectada (quantity > 0).
        # Odoo bloquea nativamente el unlink de stock.move/stock.move.line que ya tienen
        # cantidad recolectada. En vez de forzar y causar UserError, marcamos esos moves
        # como "HUERFANO-PROTEGIDO-" y los dejamos para revisión manual de Inventario.
        # Causa raíz: action_reopen_to_draft() FASE 3 desvincula pickings 'done'
        # cambiando su 'origin' pero sin cancelarlos, generando moves huérfanos con quantity>0.
        protected_moves = moves.filtered(
            lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)
        )
        cleanable_moves = moves - protected_moves

        if protected_moves:
            for pm in protected_moves:
                pm.origin = f"HUERFANO-PROTEGIDO-{pm.origin or ''}"
            _logger.warning(
                "🛡️ %d stock.move(s) con cantidad recolectada NO fueron eliminados "
                "(protegidos por integridad de Odoo). Marcados como huérfanos protegidos: %s",
                len(protected_moves), protected_moves.mapped('name'),
            )

        if not cleanable_moves:
            _logger.info(
                "🛡️ Todos los moves huérfanos están protegidos (tienen cantidad recolectada). "
                "No se eliminará ninguno."
            )
            return

        try:
            with self.env.cr.savepoint():
                # 1. Atacar las líneas de movimiento primero (stock.move.line)
                move_lines = cleanable_moves.mapped('move_line_ids')
                if move_lines:
                    move_lines.write({'state': 'draft'})
                    move_lines.unlink()

                # 2. Atacar los movimientos cabecera (stock.move)
                # Forzamos a borrador para intentar bypassear el estado 'done' de manera legal
                cleanable_moves.write({'state': 'draft'})

                # 3. Borrado físico usando el salvoconducto de contexto
                cleanable_moves.with_context(force_delete=True).unlink()

            _logger.info("✅ %d moves huérfanos eliminados limpiamente via ORM.", len(cleanable_moves))

        except Exception as e:
            _logger.error("❌ Error ORM eliminando moves huérfanos: %s", e)
            raise UserError(
                f"🛑 Seguridad Odoo: No se pudieron eliminar {len(cleanable_moves)} movimientos huérfanos.\n"
                f"Odoo ha bloqueado la eliminación porque estos movimientos ya afectaron la "
                f"valoración contable o tienen stock real (Quants) fuertemente asociado.\n\n"
                f"Detalle técnico: {e}"
            )
