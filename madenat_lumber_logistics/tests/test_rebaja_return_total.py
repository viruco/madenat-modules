# -*- coding: utf-8 -*-
"""Sub-bloque 4B (2026-10-04) — R2: retorno físico TOTAL / reversa robusta.

Cubre: retorno total real (lote/quant/destino), `origin_returned_move_id`,
idempotencia relacional, bloqueo por salida no `done`, rollback total ante un
error inducido, permisos, gates B-01 / costos / facturación / consolidaciones,
clasificación rebaja activa vs. compensada, camino SV y no impacto en el
Embarque. Datos 100% aislados: se crean y se revierten en la transacción del
test (TransactionCase).
"""

import hashlib
from unittest import mock

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestRebajaReturnTotal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # El albarán de rebaja es outgoing; se desactiva el correo (entorno test).
        if 'stock_move_email_validation' in cls.company._fields:
            cls.company.stock_move_email_validation = False
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.customers = cls.env.ref('stock.stock_location_customers')
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'R2 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'R2 Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Container = cls.env['lumber.container']
        cls.Shipment = cls.env['lumber.export.shipment']
        cls.Line = cls.env['lumber.shipment.line']

        def _mk_user(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name,
                'email': '%s@madenat.cl' % name,
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('r2_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('r2_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk_user('r2_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk_user('r2_plain', ['base.group_user'])

    # ── Fábricas (100% aisladas) ─────────────────────────────────────────
    def _make_guia(self, name):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
        })

    def _make_lot(self, tag, volume, disponible=None):
        guia = self._make_guia('R2-GUIA-%s' % tag)
        lot = self.StockLot.create({
            'name': 'R2-LOT-%s' % tag, 'product_id': self.product.id,
            'company_id': self.company.id,
            'guia_processing_id': guia.id,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': volume, 'vol_shipment_m3': volume,
        })
        avail = volume if disponible is None else disponible
        if avail > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, avail, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_sv_lot(self, tag, volume, disponible=None):
        guia = self._make_guia('R2-SVGUIA-%s' % tag)
        lot = self.StockLot.create({
            'name': 'R2SV%s' % tag, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'volume_purchase_m3': volume, 'vol_shipment_m3': volume,
        })
        avail = volume if disponible is None else disponible
        if avail > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, avail, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_shipment(self, name):
        vessel = self.env['shipping.vessel'].create({'name': 'V-%s' % name})
        voyage = self.env['shipping.voyage'].create({
            'vessel_id': vessel.id, 'voyage_reference': 'VOY-%s' % name,
            'port_of_loading': 'Coronel, CL', 'port_of_discharge': 'Shanghai',
            'etd': '2026-10-10'})
        return self.Shipment.create({
            'name': name, 'customer_id': self.partner.id,
            'vessel_id': vessel.id, 'voyage_id': voyage.id})

    def _make_container(self, name, shipment, lots, sv_volume=0.0):
        container = self.Container.create({
            'name': name, 'container_type': '40HC',
            'shipment_id': shipment.id})
        for lot in lots:
            container.with_context(
                madenat_sv_rebaja_per_lot=sv_volume,
            ).write({'lot_ids': [(4, lot.id)]})
            lot.invalidate_recordset()
        container.write({'state': 'loaded'})
        container.invalidate_recordset()
        return container

    def _rebajable_container(self, tag, lots, sv_volume=0.0):
        shipment = self._make_shipment('EMB-%s' % tag)
        container = self._make_container(
            'CONT-%s' % tag, shipment, lots, sv_volume=sv_volume)
        return container, shipment

    def _rebajado_container(self, tag, lots, sv_volume=0.0):
        container, shipment = self._rebajable_container(
            tag, lots, sv_volume=sv_volume)
        container.with_user(self.user_oper).action_rebajar()
        container.invalidate_recordset()
        return container, shipment

    def _quant_at(self, lot, location):
        lot.invalidate_recordset()
        return sum(self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', location.id)]).mapped('quantity'))

    def _latest_audit(self, action_type):
        return self.env['madenat.audit.log'].sudo().search(
            [('action_type', '=', action_type)], order='id desc', limit=1)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-1 — Rebaja real total → reversa total (retorno físico real)
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_1_reversa_total_repone_stock(self):
        lot = self._make_lot('01', 3.0)
        container, _shipment = self._rebajable_container('01', [lot])
        container.with_user(self.user_oper).action_rebajar()
        container.invalidate_recordset()
        self.assertEqual(container.state, 'rebajado')
        out = container.line_ids.rebaja_picking_id
        self.assertTrue(out)
        out.invalidate_recordset()
        self.assertEqual(out.state, 'done')
        self.assertAlmostEqual(self._quant_at(lot, self.customers), 3.0, places=3)
        self.assertAlmostEqual(self._quant_at(lot, self.location), 0.0, places=3)

        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        # Cuant interno repuesto y Customers decrementado.
        self.assertAlmostEqual(self._quant_at(lot, self.location), 3.0, places=3)
        self.assertAlmostEqual(self._quant_at(lot, self.customers), 0.0, places=3)
        # Retorno `done` con el mismo lote.
        ret = out.return_ids.filtered(lambda p: p.state == 'done')
        self.assertTrue(ret, 'Debe existir el retorno físico validado')
        self.assertEqual(ret.move_line_ids.mapped('lot_id'), lot)
        # Línea revertida y contenedor restaurado.
        self.assertEqual(container.line_ids.rebaja_state, 'reversed')
        self.assertEqual(container.state, 'loaded')
        # Auditoría R2 firmada y verificable.
        log = self._latest_audit('rebaja_return_total')
        self.assertTrue(log, 'Falta auditoría rebaja_return_total')
        self.assertEqual(len(log.audit_hash or ''), 64)
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-2 — Cada move de retorno: producto/UoM/cantidad/lote y vínculo
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_2_return_moves_relations(self):
        lot = self._make_lot('02', 4.0)
        container, _shipment = self._rebajable_container('02', [lot])
        container.with_user(self.user_oper).action_rebajar()
        out = container.line_ids.rebaja_picking_id
        out_move = out.move_ids.filtered(lambda m: m.state == 'done')
        self.assertEqual(len(out_move), 1)

        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        ret_move = out_move.returned_move_ids.filtered(
            lambda m: m.state == 'done')
        self.assertEqual(len(ret_move), 1)
        self.assertEqual(ret_move.origin_returned_move_id, out_move)
        self.assertEqual(ret_move.product_id, out_move.product_id)
        self.assertEqual(ret_move.product_uom, out_move.product_uom)
        self.assertAlmostEqual(
            ret_move.quantity, out_move.quantity, places=3)
        self.assertEqual(
            ret_move.move_line_ids.mapped('lot_id'),
            out_move.move_line_ids.mapped('lot_id'))
        # Customers → ubicación interna de origen del move.
        self.assertEqual(ret_move.location_id.usage, 'customer')
        self.assertEqual(ret_move.location_dest_id, out_move.location_id)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-3 — Reintento no duplica retorno/moves/quants/SV/auditoría
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_3_reintento_no_duplica(self):
        lot = self._make_lot('03', 3.0)
        container, _shipment = self._rebajable_container('03', [lot])
        container.with_user(self.user_oper).action_rebajar()
        out = container.line_ids.rebaja_picking_id
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        returns_before = self.env['stock.picking'].search_count(
            [('return_id', '=', out.id)])
        pickings_before = self.env['stock.picking'].search_count([])
        moves_before = self.env['stock.move'].search_count([])
        audits_before = self.env['madenat.audit.log'].sudo().search_count(
            [('action_type', '=', 'rebaja_return_total')])
        sv_before = self.env['madenat.sv.operation'].search_count(
            [('action_type', '=', 'rebaja_reverse')])
        qty_before = self._quant_at(lot, self.location)

        # Reintento: contenedor ya revertido con retorno total → no-op.
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        self.assertEqual(container.state, 'loaded')
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('return_id', '=', out.id)]), returns_before)
        self.assertEqual(
            self.env['stock.picking'].search_count([]), pickings_before)
        self.assertEqual(
            self.env['stock.move'].search_count([]), moves_before)
        self.assertAlmostEqual(
            self._quant_at(lot, self.location), qty_before, places=3)
        self.assertEqual(
            self.env['madenat.audit.log'].sudo().search_count(
                [('action_type', '=', 'rebaja_return_total')]), audits_before)
        self.assertEqual(
            self.env['madenat.sv.operation'].search_count(
                [('action_type', '=', 'rebaja_reverse')]), sv_before)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-4 — Salida origen no `done` → UserError y estados sin cambio
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_4_out_no_done_bloquea(self):
        lot = self._make_lot('04', 3.0)
        container, _shipment = self._rebajable_container('04', [lot])
        # OUT ficticio en BORRADOR (no validado): simula rebaja sin salida real.
        draft = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.customers.id,
            'origin': 'R2-04-DRAFT',
        })
        self.env['stock.move'].create({
            'name': 'R2-04-DRAFT', 'product_id': self.product.id,
            'product_uom_qty': 3.0, 'product_uom': self.uom_m3.id,
            'picking_id': draft.id,
            'location_id': self.location.id,
            'location_dest_id': self.customers.id,
        })
        line = container.line_ids
        line.write({
            'rebaja_state': 'rebajado', 'rebaja_qty_m3': 3.0,
            'rebaja_picking_id': draft.id})
        container.write({'state': 'rebajado', 'state_before_rebaja': 'loaded'})
        self.env.invalidate_all()
        pickings_before = self.env['stock.picking'].search_count([])

        with self.assertRaises(UserError):
            container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(container.line_ids.rebaja_state, 'rebajado')
        self.assertEqual(
            self.env['stock.picking'].search_count([]), pickings_before)
        # `_reverse_rebaja_picking` NUNCA devuelve `False` silencioso.
        with self.assertRaises(UserError):
            container._reverse_rebaja_picking(draft)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-5 — Error inducido → rollback total (sin estados/auditoría parciales)
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_5_error_inducido_rollback_total(self):
        lot = self._make_lot('05', 3.0)
        container, _shipment = self._rebajable_container('05', [lot])
        container.with_user(self.user_oper).action_rebajar()
        out = container.line_ids.rebaja_picking_id
        # R2: línea base propia del test (no asumir conteos globales de clase).
        audit_baseline = self.env['madenat.audit.log'].sudo().search_count(
            [('action_type', '=', 'rebaja_return_total')])
        sv_baseline = self.env['madenat.sv.operation'].search_count(
            [('action_type', '=', 'rebaja_reverse')])
        Model = type(self.Container)

        def _boom(self_, picking, return_picking):
            # Fallo DESPUÉS de crear el retorno físico (antes de estados).
            raise UserError('Fallo inducido T-R2-5.')

        with mock.patch.object(Model, '_assert_rebaja_return_valid', _boom):
            with self.assertRaises(UserError):
                with self.env.cr.savepoint():
                    container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        # Rollback total: sin reversa, sin retorno persistido, sin auditoría.
        self.assertEqual(container.state, 'rebajado')
        self.assertTrue(all(
            l.rebaja_state == 'rebajado' for l in container.line_ids))
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('return_id', '=', out.id)]), 0)
        self.assertFalse(out.move_ids.filtered('returned_move_ids'))
        self.assertEqual(
            self.env['madenat.audit.log'].sudo().search_count(
                [('action_type', '=', 'rebaja_return_total')]),
            audit_baseline)
        self.assertEqual(
            self.env['madenat.audit.log'].sudo().search_count(
                [('action_type', '=', 'rebaja_reverse'),
                 ('batch_id', '=', str(container.line_ids.id))]), 0)
        # No se revirtió SV.
        self.assertEqual(
            self.env['madenat.sv.operation'].search_count(
                [('action_type', '=', 'rebaja_reverse')]), sv_baseline)
        # Tras retirar el fallo, la reversa sí completa.
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'loaded')

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-6 — Usuario no autorizado → AccessError
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_6_usuario_no_autorizado(self):
        lot = self._make_lot('06', 3.0)
        container, _shipment = self._rebajable_container('06', [lot])
        container.with_user(self.user_oper).action_rebajar()
        with self.assertRaises(AccessError):
            container.with_user(self.user_oper).action_reverse_rebaja()
        with self.assertRaises(AccessError):
            container.with_user(self.user_plain).action_reverse_rebaja()
        with self.assertRaises(AccessError):
            container.with_user(
                self.user_oper)._assert_can_reverse_rebaja_total()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')

    # ── Helper B-01: abre la excepción con el contenedor pendiente ────────
    def _open_b01_exception(self, container, shipment, reason):
        shipment.write({'state': 'confirmed'})
        shipment.with_user(self.user_jef)._set_in_transit(
            is_b01=True, exception_reason=reason)
        self.env.invalidate_all()

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-7 — B-01 `open` → reversa bloqueada (incluso Gerencia)
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_7_b01_open_bloquea(self):
        lot = self._make_lot('07', 3.0)
        container, shipment = self._rebajable_container('07', [lot])
        self._open_b01_exception(
            container, shipment,
            'Excepción documental de prueba R2 siete (B-01 open).')
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertEqual(container.state, 'loaded')
        # R1: Gerencia rebaja extemporánea; el Contenedor pasa a rebajado.
        container.with_user(self.user_ger)._rebajar_container()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(shipment.b01_exception_state, 'open')
        # Reversa bloqueada: Jefatura (AccessError, R2 sólo Gerencia) y
        # Gerencia (B-01 open → UserError).
        with self.assertRaises(AccessError):
            container.with_user(self.user_jef).action_reverse_rebaja()
        with self.assertRaises(UserError):
            container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(shipment.b01_exception_state, 'open')

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-8 — B-01 `resolved`: sólo Gerencia + motivo ≥ 20; no reabre B-01
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_8_b01_resolved_solo_gerencia(self):
        lot = self._make_lot('08', 3.0)
        container, shipment = self._rebajable_container('08', [lot])
        self._open_b01_exception(
            container, shipment,
            'Excepción documental de prueba R2 ocho (B-01 open).')
        # R1 (Gerencia) regulariza la rebaja extemporánea + auditoría.
        wiz = self.env['lumber.b01.regularization.wizard'].with_user(
            self.user_ger).create({
                'shipment_id': shipment.id,
                'selected_container_ids': [(6, 0, container.ids)],
                'regularization_reason':
                    'Contingencia documental: rebaja extemporánea R2 ocho.',
                'approval_reason':
                    'Aprobado por Gerencia: contingencia controlada R2 ocho.'})
        wiz.action_regularize_rebaja()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')
        # Cierre open → resolved (sólo Gerencia).
        shipment.with_user(self.user_ger).action_resolve_b01_exception()
        self.env.invalidate_all()
        self.assertEqual(shipment.b01_exception_state, 'resolved')

        # Jefatura sin Gerencia → AccessError (R2 sólo Gerencia).
        with self.assertRaises(AccessError):
            container.with_user(self.user_jef).action_reverse_rebaja()
        # Gerencia → abre el asistente de override.
        action = container.with_user(self.user_ger).action_reverse_rebaja()
        self.assertEqual(
            action.get('res_model'),
            'lumber.container.rebaja.reverse.wizard')
        Wiz = self.env['lumber.container.rebaja.reverse.wizard']
        # Motivo insuficiente → bloqueado.
        with self.assertRaises(UserError):
            Wiz.with_user(self.user_ger).create({
                'container_id': container.id,
                'reason': 'corto'}).action_confirm_override()
        # Motivo suficiente → reversa; la B-01 NO se reabre ni se altera.
        Wiz.with_user(self.user_ger).create({
            'container_id': container.id,
            'reason': 'Reversión autorizada por Gerencia por contingencia '
                      'documental ya regularizada.'}).action_confirm_override()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(shipment.b01_exception_state, 'resolved')
        log = self._latest_audit('rebaja_return_total')
        self.assertIn('b01_state', log.audit_snapshot)
        self.assertIn('resolved', log.audit_snapshot)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-9 — Gates financieros: costos / facturación / consolidaciones
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_9_gates_financieros(self):
        lot = self._make_lot('09', 3.0)
        container, shipment = self._rebajable_container('09', [lot])
        container.with_user(self.user_oper).action_rebajar()

        # 1) Costos distribuidos.
        shipment.cost_distribution_state = 'distributed'
        shipment.invalidate_recordset()
        with self.assertRaises(UserError):
            container.with_user(self.user_ger).action_reverse_rebaja()
        shipment.cost_distribution_state = 'pending'
        shipment.invalidate_recordset()

        # 2) Costos atribuibles al lote (stock.lot.cost.line).
        cost_line = self.env['lumber.shipment.cost.line'].create({
            'shipment_id': shipment.id, 'amount_usd': 10.0,
            'partner_id': self.partner.id})
        lot_cost = self.env['stock.lot.cost.line'].create({
            'name': 'R2-09 costo', 'lot_id': lot.id, 'amount_usd': 5.0,
            'source_shipment_cost_line_id': cost_line.id})
        with self.assertRaises(UserError):
            container.with_user(self.user_ger).action_reverse_rebaja()
        lot_cost.unlink()

        # 3) Consolidación de facturación facturada.
        consolidation = self.env['lumber.billing.consolidation'].create({
            'shipment_id': shipment.id, 'state': 'billed'})
        with self.assertRaises(UserError):
            container.with_user(self.user_ger).action_reverse_rebaja()
        consolidation.state = 'cancelled'
        consolidation.unlink()

        self.env.invalidate_all()
        self.assertEqual(container.state, 'rebajado')
        # Sin gates incompatibles, la reversa procede.
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()
        self.assertEqual(container.state, 'loaded')

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-10 — Clasificación: rebaja activa vs. compensada vs. inconsistente
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_10_clasificacion_activa_vs_compensada(self):
        # Parte 1: activa → compensada (OUT done + retorno total + reversed).
        lot = self._make_lot('10', 3.0)
        container, shipment = self._rebajable_container('10', [lot])
        container.with_user(self.user_oper).action_rebajar()
        self.assertEqual(
            shipment._container_rebaja_classification(container), 'active')
        self.assertTrue(shipment._is_container_rebajado_fisico(container))

        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()
        self.assertEqual(
            shipment._container_rebaja_classification(container),
            'compensated')
        self.assertFalse(shipment._is_container_rebajado_fisico(container))

        # Parte 2: `reversed` SIN retorno completo → inconsistencia (P0).
        lot2 = self._make_lot('10b', 2.0)
        container2, shipment2 = self._rebajable_container('10b', [lot2])
        container2.with_user(self.user_oper).action_rebajar()
        container2.line_ids.write({'rebaja_state': 'reversed'})
        container2.write({'state': 'loaded'})
        self.env.invalidate_all()
        self.assertEqual(
            shipment2._container_rebaja_classification(container2),
            'inconsistent')
        # R2: `inconsistent` no equivale a Rebaja activa; debe bloquear el flujo.
        self.assertFalse(shipment2._is_container_rebajado_fisico(container2))
        with self.assertRaises(UserError):
            shipment2._assert_no_rebaja_inconsistency()

        # Parte 3 (compatibilidad AD-94): línea `rebajado` SIN picking de rebaja
        # y Contenedor en `rebajado` => Rebaja ACTIVA (no inconsistencia).
        lot3 = self._make_lot('10c', 1.0)
        container3, shipment3 = self._rebajable_container('10c', [lot3])
        container3.line_ids.write({'rebaja_state': 'rebajado'})
        container3.write({'state': 'rebajado', 'state_before_rebaja': 'loaded'})
        self.env.invalidate_all()
        self.assertFalse(container3.line_ids.rebaja_picking_id)
        self.assertEqual(
            shipment3._container_rebaja_classification(container3), 'active')
        self.assertTrue(
            shipment3._is_container_rebajado_fisico(container3))

        # Parte 4: misma línea sin picking pero Contenedor NO compatible
        # (no `rebajado`/`shipped`) => inconsistencia (invariante preservado).
        container3.write({'state': 'loaded'})
        self.env.invalidate_all()
        self.assertEqual(
            shipment3._container_rebaja_classification(container3),
            'inconsistent')
        self.assertFalse(
            shipment3._is_container_rebajado_fisico(container3))
        with self.assertRaises(UserError):
            shipment3._assert_no_rebaja_inconsistency()

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-11 — Lote SV (volume): retorno físico primero, una sola reversa SV
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_11_sv_volume_reversa(self):
        lot = self._make_sv_lot('11', 40.0)
        container, _shipment = self._rebajable_container(
            '11', [lot], sv_volume=10.0)
        op = self.Operation.search([
            ('lot_id', '=', lot.id), ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied')], limit=1)
        self.assertTrue(op, 'La asignación SV debe crear la rebaja SV')

        container.with_user(self.user_oper).action_rebajar()
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        self.assertTrue(line.rebaja_sv_operation_id)

        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        # Retorno físico total validado (lote y quant restituidos).
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(
            container.line_ids.rebaja_state, 'reversed')
        self.assertAlmostEqual(
            self._quant_at(lot, self.location), 40.0, places=3)
        # Exactamente una rebaja_reverse, con origen correcto y ledger coherente.
        rev = self.Operation.search([
            ('lot_id', '=', lot.id), ('action_type', '=', 'rebaja_reverse')])
        self.assertEqual(len(rev), 1, 'Debe existir una sola rebaja_reverse')
        self.assertEqual(rev.origin_operation_id, op)
        self.assertAlmostEqual(lot.sv_rebajado_m3, 0.0, places=3)

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-12 — La reversa NO altera Embarque, B-01, costo/factura/pago/entrega
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_12_sin_efectos_colaterales(self):
        lot = self._make_lot('12', 3.0)
        container, shipment = self._rebajable_container('12', [lot])
        container.with_user(self.user_oper).action_rebajar()
        shipment.invalidate_recordset()
        before = {
            'shipment_state': shipment.state,
            'b01': shipment.b01_exception_state,
            'cost': shipment.cost_distribution_state,
            'actual_departure': shipment.actual_departure,
            'vessel': shipment.vessel_id.id,
            'voyage': shipment.voyage_id.id,
            'account_move': self.env['account.move'].search_count([]),
            'account_payment': self.env['account.payment'].search_count([]),
            'consolidation': self.env[
                'lumber.billing.consolidation'].search_count([]),
            'shipment_cost_line': self.env[
                'lumber.shipment.cost.line'].search_count([]),
        }
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.env.invalidate_all()

        self.assertEqual(shipment.state, before['shipment_state'])
        self.assertEqual(shipment.b01_exception_state, before['b01'])
        self.assertEqual(shipment.cost_distribution_state, before['cost'])
        self.assertEqual(
            shipment.actual_departure, before['actual_departure'])
        self.assertEqual(shipment.vessel_id.id, before['vessel'])
        self.assertEqual(shipment.voyage_id.id, before['voyage'])
        self.assertEqual(
            self.env['account.move'].search_count([]), before['account_move'])
        self.assertEqual(
            self.env['account.payment'].search_count([]),
            before['account_payment'])
        self.assertEqual(
            self.env['lumber.billing.consolidation'].search_count([]),
            before['consolidation'])
        self.assertEqual(
            self.env['lumber.shipment.cost.line'].search_count([]),
            before['shipment_cost_line'])
        # Única escritura permitida: el estado logístico del Contenedor.
        self.assertEqual(container.state, 'loaded')

    # ══════════════════════════════════════════════════════════════════════
    # T-R2-15 (T-R2-13) — RPC/contexto/sudo/directo no eluden el guard R2
    # ══════════════════════════════════════════════════════════════════════
    def test_tr2_13_elusion_no_permitida(self):
        """T-R2-15: contexto falso, sudo y llamada privada no evaden el guard."""
        lot = self._make_lot('13', 3.0)
        container, _shipment = self._rebajable_container('13', [lot])
        container.with_user(self.user_oper).action_rebajar()
        self.env.invalidate_all()
        pickings_before = self.env['stock.picking'].search_count([])
        # R2: línea base propia del test (no asumir conteos globales de clase).
        audit_baseline = self.env['madenat.audit.log'].sudo().search_count(
            [('action_type', '=', 'rebaja_return_total')])
        # Contexto falso: no habilita el rol.
        with self.assertRaises(AccessError):
            container.with_user(self.user_oper).with_context(
                bypass_rebaja_return=True).action_reverse_rebaja()
        # sudo conserva el usuario real (Operaciones) → sin grupo Gerencia.
        with self.assertRaises(AccessError):
            container.with_user(self.user_oper).sudo().action_reverse_rebaja()
        # Método privado invocado directamente: mismo guard.
        with self.assertRaises(AccessError):
            container.with_user(self.user_oper)._reverse_rebaja_container()
        with self.assertRaises(AccessError):
            container.with_user(
                self.user_plain)._assert_can_reverse_rebaja_total()
        self.env.invalidate_all()
        # Δ0: sin retorno, sin auditoría R2, estados intactos.
        self.assertEqual(container.state, 'rebajado')
        self.assertEqual(container.line_ids.rebaja_state, 'rebajado')
        self.assertEqual(
            self.env['stock.picking'].search_count([]), pickings_before)
        self.assertEqual(
            self.env['madenat.audit.log'].sudo().search_count(
                [('action_type', '=', 'rebaja_return_total')]),
            audit_baseline)
