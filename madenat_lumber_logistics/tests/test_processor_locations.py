# -*- coding: utf-8 -*-
"""I1 canónico (CANON/19 §5.4/§16) — Ubicaciones, saldo y envío a procesador.

Cubre: idempotencia de ubicaciones (sin duplicados), envío de SV (quants
antes/después), envío parcial manual sin motivo (AD-89) y rechazo por exceso,
recepción directa en la ubicación del procesador, saldo coherente con los
quants, lote en procesador asignado en contenedor, permisos y auditoría.
Datos 100% aislados.
"""
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestProcessorLocations(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'PROC Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'PROC Supplier', 'is_company': True})
        cls.processor = cls.env['res.partner'].create({
            'name': 'PROC Planta Uno', 'is_company': True,
            'is_processor': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Wizard = cls.env['madenat.processor.shipment.wizard']

        # Usuarios por perfil (sin crear grupos nuevos — CANON/19 §9).
        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [
                    cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('proc_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk('proc_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk('proc_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_plain = _mk('proc_plain', ['base.group_user'])

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name):
        return self.Guia.create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-10-02'})

    def _make_sv_lot(self, guia, label, volume, disponible):
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'volume_purchase_m3': volume, 'vol_shipment_m3': volume})
        if disponible:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.stock_loc, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_procesado_lot(self, guia, label, volume, disponible):
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id,
            'guia_processing_id': guia.id,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': volume, 'vol_shipment_m3': volume})
        if disponible:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.stock_loc, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _qty_in(self, lot, location):
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id), ('location_id', '=', location.id),
            ('company_id', '=', self.company.id)])
        return sum(quants.mapped('quantity'))

    def _send(self, lot, quantity, source=None, reason=None):
        processor_loc = self.processor._get_or_create_processor_location()
        wizard = self.Wizard.create({
            'processor_id': self.processor.id,
            'source_location_id': (source or self.stock_loc).id,
            'reason': reason,
            'line_ids': [(0, 0, {
                'lot_id': lot.id,
                'source_location_id': (source or self.stock_loc).id,
                'quantity': quantity,
            })],
        })
        res = wizard.action_send()
        return processor_loc, res

    # ── Pruebas ──────────────────────────────────────────────────────────
    def test_01_ubicaciones_idempotentes(self):
        """La ubicación del procesador se crea bajo demanda y no se duplica."""
        loc1 = self.processor._get_or_create_processor_location()
        loc2 = self.processor._get_or_create_processor_location()
        self.assertEqual(loc1, loc2)
        self.assertEqual(loc1.usage, 'internal')
        root = loc1.location_id
        self.assertEqual(root.name, 'Procesadores')
        self.assertEqual(root.usage, 'internal')
        self.assertEqual(self.processor.processor_location_id, loc1)
        dups = self.env['stock.location'].search([
            ('name', '=', self.processor.name),
            ('location_id', '=', root.id),
            ('usage', '=', 'internal')])
        self.assertEqual(len(dups), 1)

    def test_02_envio_sv_quants_antes_y_despues(self):
        """Envío de SV: el quant sale del origen y entra en el procesador."""
        guia = self._make_guia('PROC-02')
        lot = self._make_sv_lot(guia, 'PROC-SV-02', 10.0, 10.0)
        processor_loc = self.processor._get_or_create_processor_location()
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 10.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 0.0, 3)
        self._send(lot, 10.0)
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 0.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 10.0, 3)

    def test_03_envio_parcial_sin_motivo(self):
        """El envío parcial manual NO es desviación: válido sin motivo (AD-89)."""
        guia = self._make_guia('PROC-03')
        lot = self._make_sv_lot(guia, 'PROC-SV-03', 10.0, 10.0)
        processor_loc = self.processor._get_or_create_processor_location()
        self._send(lot, 4.0)  # parcial sin motivo: operación normal
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 6.0, 3)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 4.0, 3)

    def test_04_envio_exceso_rechazado(self):
        """No se puede enviar más que el disponible real (integridad)."""
        guia = self._make_guia('PROC-04')
        lot = self._make_sv_lot(guia, 'PROC-SV-04', 10.0, 10.0)
        with self.assertRaises(ValidationError):
            self._send(lot, 15.0, reason='intento de exceso')
        # El origen queda intacto.
        self.assertAlmostEqual(self._qty_in(lot, self.stock_loc), 10.0, 3)

    def test_05_sv_recibido_directo_en_procesador(self):
        """Recepción directa en la ubicación del procesador (sin traslado)."""
        processor_loc = self.processor._get_or_create_processor_location()
        guia = self._make_guia('PROC-05')
        lot = self.StockLot.create({
            'name': 'PROC-SV-05', 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'volume_purchase_m3': 5.0, 'vol_shipment_m3': 5.0})
        ptype = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.company.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.supplier.id,
            'picking_type_id': ptype.id,
            'location_id': ptype.default_location_src_id.id,
            'location_dest_id': processor_loc.id,
            'company_id': self.company.id})
        move_vals = {
            'name': lot.name, 'product_id': self.product.id,
            'product_uom_qty': 5.0, 'product_uom': self.uom_m3.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'company_id': self.company.id}
        if 'picked' in self.env['stock.move']._fields:
            move_vals['picked'] = True
        move = self.env['stock.move'].create(move_vals)
        ml_vals = {
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'lot_id': lot.id,
            'quantity': 5.0, 'product_uom_id': self.uom_m3.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id}
        if 'picked' in self.env['stock.move.line']._fields:
            ml_vals['picked'] = True
        self.env['stock.move.line'].create(ml_vals)
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 5.0, 3)
        quant = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id), ('location_id', '=', processor_loc.id)])
        self.assertEqual(quant.madenat_processor_id, self.processor)

    def test_06_saldo_coherente_con_quants(self):
        """El saldo por procesador coincide con la suma de quants."""
        guia = self._make_guia('PROC-06')
        lot = self._make_sv_lot(guia, 'PROC-SV-06', 8.0, 8.0)
        processor_loc = self.processor._get_or_create_processor_location()
        self._send(lot, 8.0)
        quants = self.env['stock.quant'].search([
            ('madenat_processor_id', '=', self.processor.id),
            ('madenat_lot_flow_type', '=', 'volume')])
        self.assertAlmostEqual(
            sum(quants.mapped('quantity')),
            self._qty_in(lot, processor_loc), 3)
        self.assertAlmostEqual(sum(quants.mapped('quantity')), 8.0, 3)

    def test_07_lote_en_procesador_asignado_en_contenedor(self):
        """El asistente de contenedores toma lotes en ubicaciones de procesador."""
        guia = self._make_guia('PROC-07')
        lot = self._make_procesado_lot(guia, 'PROC-LOT-07', 5.0, 5.0)
        processor_loc, _ = self._send(lot, 5.0)
        self.assertAlmostEqual(self._qty_in(lot, processor_loc), 5.0, 3)
        shipment = self.env['lumber.export.shipment'].create({
            'name': 'PROC-EMB-07', 'customer_id': self.supplier.id})
        container = self.env['lumber.container'].create({
            'name': 'PROC-CONT-07', 'container_type': '40HC',
            'shipment_id': shipment.id})
        wizard = self.env['lumber.container.lot.wizard'].create({
            'container_id': container.id})
        self.assertIn(lot, wizard.available_lot_ids)

    def test_08_permisos_por_grupo(self):
        """Operaciones/Jefatura/Gerencia acceden; sin grupo no (ACL dura)."""
        with self.assertRaises(AccessError):
            self.Wizard.with_user(self.user_plain).create({
                'processor_id': self.processor.id,
                'source_location_id': self.stock_loc.id})
        for user in (self.user_oper, self.user_jef, self.user_ger):
            self.Wizard.with_user(user).check_access_rights('create')

    def test_09_auditoria_envio_normal(self):
        """El envío (aun parcial) se audita como operación normal, sin deviation."""
        guia = self._make_guia('PROC-09')
        lot = self._make_sv_lot(guia, 'PROC-SV-09', 10.0, 10.0)
        _loc, res = self._send(lot, 6.0)  # parcial sin motivo
        picking = self.env['stock.picking'].browse(res['res_id'])
        events = self.env['madenat.audit.log'].search([
            ('action_type', '=', 'processor_shipment'),
            ('batch_id', '=', picking.name)])
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events.audit_hash), 64)
        deviations = self.env['madenat.audit.log'].search([
            ('action_type', '=', 'deviation')])
        self.assertFalse(deviations)

