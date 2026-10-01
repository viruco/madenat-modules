# -*- coding: utf-8 -*-
"""Utilidades compartidas para las pruebas del Programa SV (etiquetas SV).

Todos los registros son aislados (TransactionCase): no se usan ni modifican la
Guía 4495589, el lote SV00000000008 (id 3772) ni ningún dato histórico.
"""
import base64


class SvTestCommon:
    """Mixin con fábricas de datos SV aisladas."""

    @classmethod
    def _sv_setup_base(cls):
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        cls.customer_loc = cls.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1)
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SV Test Lumber',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'SV Test Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Quant = cls.env['stock.quant']
        # Usuario de pruebas con los perfiles funcionales de aprobación: permite
        # ejercitar el flujo completo (el bloqueo por escalamiento se prueba en
        # test_sv_escalation_security.py con usuarios restringidos).
        cls.approval_groups = (
            cls.env.ref('madenat_lumber_core.group_madenat_auditoria')
            | cls.env.ref('madenat_lumber_core.group_madenat_contabilidad')
        )
        cls.env.user.sudo().write({
            'groups_id': [(4, group.id) for group in cls.approval_groups],
        })

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _sv_make_guia(self, name='SV-GUIA-TEST', pdf_volume=40.315,
                      declared_pieces=0, packing_pieces=0, **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.internal_loc.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared',
            'guide_pdf_file': base64.b64encode(b'%PDF-fake'),
            'guide_pdf_filename': 'guia.pdf',
            'volume_pdf_m3': pdf_volume,
            'piezas_declaradas': declared_pieces,
            'packing_pieces_declared': packing_pieces,
        }
        vals.update(extra)
        return self.Guia.create(vals)

    def _sv_make_lot(self, guia, label='SV00000000091', volume=40.300,
                     add_to_guide=True):
        """Lote SV aislado con la identidad documental del flujo Volumen."""
        lot = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'guia_processing_id': guia.id,
            'piezas': 1,
            'volume_purchase_m3': volume,
            'vol_shipment_m3': volume,
            'volumen_m3': volume,
        })
        if add_to_guide:
            guia.write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv_add_quant(self, lot, quantity, location=None):
        self.Quant._update_available_quantity(
            lot.product_id, location or self.internal_loc, quantity,
            lot_id=lot)
        return lot

    def _sv_move_done(self, lot, quantity, src, dest, origin=False):
        """Movimiento done genérico con lot_id explícito (pruebas aisladas)."""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming' if dest.usage == 'internal' else 'outgoing'),
            ('warehouse_id', '=', self.warehouse.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'origin': origin or False,
            'partner_id': self.partner.id,
        })
        move = self.env['stock.move'].create({
            'name': lot.name,
            'product_id': lot.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': lot.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
        })
        self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': lot.product_id.id,
            'lot_id': lot.id,
            'quantity': quantity,
            'product_uom_id': lot.product_id.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
        })
        picking.action_confirm()
        picking.with_context(
            skip_backorder=True, skip_immediate=True,
            immediate_transfer=True, force_validate=True,
        ).button_validate()
        return picking

    def _sv_receipt(self, guia, lot, quantity, dest_location=None):
        """Recepción done del lote (move + move line con lot_id explícito)."""
        return self._sv_move_done(
            lot, quantity, self.supplier_loc,
            dest_location or self.internal_loc, origin=guia.name)

    def _sv_outgoing(self, lot, quantity, dest_location=None):
        """Salida done del lote (para vaciar el quant interno en pruebas)."""
        return self._sv_move_done(
            lot, quantity, self.internal_loc,
            dest_location or self.supplier_loc)

    # ── Operaciones SV ────────────────────────────────────────────────────
    def _sv_rebaja(self, lot, volume, reason='Rebaja de prueba', **extra):
        vals = {
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': volume,
            'reason': reason,
        }
        vals.update(extra)
        operation = self.Operation.create(vals)
        operation.action_apply()
        return operation

    def _sv_regularize(self, lot, new_volume, evidence='RESPALDO-001', **extra):
        vals = {
            'lot_id': lot.id,
            'action_type': 'regularize_volume',
            'new_volume_m3': new_volume,
            'reason': 'Regularización documental de prueba',
            'evidence_reference': evidence,
        }
        vals.update(extra)
        operation = self.Operation.create(vals)
        operation.action_apply()
        return operation
