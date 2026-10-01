# -*- coding: utf-8 -*-
"""AD-82 / CANON/18 — Rebaja de inventario por contenedor y por nave.

Cubre: quants antes/después, idempotencia, SV parcial, contenedor mixto,
rebaja por nave con un fallo, reversa (y bloqueo), zarpe sin/con rebaja y
permisos por grupo. Datos 100% aislados.
"""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

import hashlib


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestRebajaContenedor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # El albarán de rebaja es outgoing; se desactiva el correo de
        # confirmación (requiere remitente configurado en el entorno de test).
        if 'stock_move_email_validation' in cls.company._fields:
            cls.company.stock_move_email_validation = False
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.customers = cls.env.ref('stock.stock_location_customers')
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'REB Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'REB Partner', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Container = cls.env['lumber.container']
        cls.Shipment = cls.env['lumber.export.shipment']

        # Usuarios por perfil (sin crear grupos nuevos — CANON/18 §8).
        def _mk_user(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower().replace(' ', '_'),
                'email': '%s@madenat.cl' % name.lower().replace(' ', '_'),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk_user('reb_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk_user('reb_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_plain = _mk_user('reb_plain', ['base.group_user'])
        # AD-88 (B-03/B-06): Gerencia puede autorizar el override de reversa.
        cls.user_ger = _mk_user('reb_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
        })

    def _make_lot(self, guia, label, ref_volume, disponible):
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id,
            'guia_processing_id': guia.id,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': ref_volume, 'vol_shipment_m3': ref_volume,
        })
        if disponible > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_sv_lot(self, guia, label, volume, disponible=None):
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
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

    def _make_shipment(self, name, vessel=None, voyage=None):
        vals = {'name': name, 'customer_id': self.partner.id}
        if vessel:
            vals['vessel_id'] = vessel.id
        if voyage:
            vals['voyage_id'] = voyage.id
        return self.Shipment.create(vals)

    def _make_vessel_voyage(self, tag):
        vessel = self.env['shipping.vessel'].create({'name': 'VESSEL-%s' % tag})
        voyage = self.env['shipping.voyage'].create({
            'vessel_id': vessel.id, 'voyage_reference': 'V-%s' % tag,
            'port_of_loading': 'Coronel, CL', 'port_of_discharge': 'Shanghai',
            'etd': '2026-10-10',
        })
        return vessel, voyage

    def _make_container(self, name, shipment):
        return self.Container.create({
            'name': name, 'container_type': '40HC', 'shipment_id': shipment.id})

    def _assign(self, container, lot, sv_volume=0.0):
        container.with_context(
            madenat_sv_rebaja_per_lot=sv_volume,
        ).write({'lot_ids': [(4, lot.id)]})
        lot.invalidate_recordset()
        container.invalidate_recordset()

    def _quant_of(self, lot):
        lot.invalidate_recordset()
        return sum(self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('location_id.usage', '=', 'internal')]).mapped('quantity'))

    # ── Pruebas ──────────────────────────────────────────────────────────
    def _rebajable_container(self, tag, lots):
        vessel, voyage = self._make_vessel_voyage(tag)
        shipment = self._make_shipment('EMB-%s' % tag, vessel, voyage)
        container = self._make_container('CONT-%s' % tag, shipment)
        for lot, sv_vol in lots:
            self._assign(container, lot, sv_vol)
        container.write({'state': 'loaded'})
        container.invalidate_recordset()
        return container, shipment

    def test_01_lote_normal_quant_antes_despues(self):
        guia = self._make_guia('REB-01')
        lot = self._make_lot(guia, 'REB-LOT-01', 5.0, 4.5)
        container, _ = self._rebajable_container('01', [(lot, 0.0)])
        before = self._quant_of(lot)
        self.assertAlmostEqual(before, 4.5, places=3)
        container.with_user(self.user_oper).action_rebajar()
        after = self._quant_of(lot)
        self.assertAlmostEqual(after, 0.0, places=3)
        self.assertAlmostEqual(before - after, 4.5, places=3)
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        self.assertAlmostEqual(line.rebaja_qty_m3, 4.5, places=3)
        self.assertEqual(line.rebaja_state, 'rebajado')
        self.assertEqual(container.state, 'rebajado')

    def test_02_idempotencia_no_duplica(self):
        guia = self._make_guia('REB-02')
        lot = self._make_lot(guia, 'REB-LOT-02', 3.0, 3.0)
        container, _ = self._rebajable_container('02', [(lot, 0.0)])
        container.with_user(self.user_oper).action_rebajar()
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        picking = line.rebaja_picking_id
        picking_count = self.env['stock.picking'].search_count(
            [('origin', '=', picking.origin)])
        after1 = self._quant_of(lot)
        # Segunda ejecución: idempotente (mismo picking, sin nuevo descuento).
        container.with_user(self.user_oper).action_rebajar()
        after2 = self._quant_of(lot)
        self.assertAlmostEqual(after1, after2, places=3)
        self.assertEqual(
            line.rebaja_picking_id, picking, 'No debe crear otro picking')
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('origin', '=', picking.origin)]), picking_count)
        self.assertEqual(container.state, 'rebajado')

    def test_03_sv_parcial_venta_exacta(self):
        # NOTA: un mismo lote no puede estar en dos contenedores activos a la
        # vez (_check_lot_duplication). Se prueban dos etiquetas SV parciales
        # en dos contenedores: cada rebaja vende EXACTAMENTE lo asignado.
        guia = self._make_guia('REB-03')
        lot_a = self._make_sv_lot(guia, 'SV00000000301', 40.0, disponible=40.0)
        lot_b = self._make_sv_lot(guia, 'SV00000000302', 20.0, disponible=20.0)
        shipment = self._make_shipment('EMB-03')
        cont_a = self._make_container('CONT-03A', shipment)
        cont_b = self._make_container('CONT-03B', shipment)
        self._assign(cont_a, lot_a, sv_volume=10.0)
        self._assign(cont_b, lot_b, sv_volume=5.0)
        cont_a.write({'state': 'loaded'})
        cont_b.write({'state': 'loaded'})
        qa0 = self._quant_of(lot_a)
        qb0 = self._quant_of(lot_b)
        cont_a.with_user(self.user_oper).action_rebajar()
        cont_b.with_user(self.user_oper).action_rebajar()
        self.assertAlmostEqual(qa0 - self._quant_of(lot_a), 10.0, places=3)
        self.assertAlmostEqual(qb0 - self._quant_of(lot_b), 5.0, places=3)
        la = cont_a.line_ids.filtered(lambda l: l.lot_id == lot_a)
        lb = cont_b.line_ids.filtered(lambda l: l.lot_id == lot_b)
        self.assertAlmostEqual(la.rebaja_qty_m3, 10.0, places=3)
        self.assertAlmostEqual(lb.rebaja_qty_m3, 5.0, places=3)
        lot_a.invalidate_recordset()
        lot_b.invalidate_recordset()
        self.assertAlmostEqual(lot_a.sv_available_m3, 30.0, places=3)
        self.assertAlmostEqual(lot_b.sv_available_m3, 15.0, places=3)

    def test_04_contenedor_mixto(self):
        guia = self._make_guia('REB-04')
        normal = self._make_lot(guia, 'REB-LOT-04N', 2.0, 2.0)
        sv = self._make_sv_lot(guia, 'SV00000000302', 20.0, disponible=20.0)
        shipment = self._make_shipment('EMB-04')
        container = self._make_container('CONT-04', shipment)
        self._assign(container, normal, 0.0)
        self._assign(container, sv, sv_volume=7.0)
        container.write({'state': 'loaded'})
        n_before = self._quant_of(normal)
        sv_before = self._quant_of(sv)
        container.with_user(self.user_oper).action_rebajar()
        self.assertAlmostEqual(n_before - self._quant_of(normal), 2.0, places=3)
        self.assertAlmostEqual(sv_before - self._quant_of(sv), 7.0, places=3)

    def test_05_rebaja_por_nave_un_fallo(self):
        guia = self._make_guia('REB-05')
        good = self._make_lot(guia, 'REB-LOT-05G', 2.0, 2.0)
        bad = self._make_lot(guia, 'REB-LOT-05B', 2.0, 0.0)
        vessel, voyage = self._make_vessel_voyage('05')
        shipment = self._make_shipment('EMB-05', vessel, voyage)
        c_good = self._make_container('CONT-05G', shipment)
        c_bad = self._make_container('CONT-05B', shipment)
        self._assign(c_good, good)
        self._assign(c_bad, bad)
        c_good.write({'state': 'loaded'})
        c_bad.write({'state': 'loaded'})
        wizard = self.env['lumber.shipment.rebaja.wizard'].with_user(
            self.user_jef).create({
                'vessel_id': vessel.id, 'voyage_id': voyage.id,
                'container_ids': [(6, 0, [c_good.id, c_bad.id])]})
        wizard.action_rebajar()
        self.assertEqual(c_good.state, 'rebajado', wizard.result_message)
        self.assertEqual(c_bad.state, 'loaded', wizard.result_message)
        self.assertIn('CONT-05B', wizard.result_message)


    def test_06_reversa_y_reversa_bloqueada(self):
        guia = self._make_guia('REB-06')
        lot = self._make_lot(guia, 'REB-LOT-06', 3.0, 3.0)
        container, shipment = self._rebajable_container('06', [(lot, 0.0)])
        container.with_user(self.user_oper).action_rebajar()
        self.assertAlmostEqual(self._quant_of(lot), 0.0, places=3)
        container.with_user(self.user_jef).action_reverse_rebaja()
        lot.invalidate_recordset()
        container.invalidate_recordset()
        self.assertAlmostEqual(self._quant_of(lot), 3.0, places=3)
        self.assertEqual(container.state, 'loaded')
        container.with_user(self.user_oper).action_rebajar()
        shipment.state = 'delivered'
        with self.assertRaises(UserError):
            container.with_user(self.user_jef).action_reverse_rebaja()

    def test_07_zarpe_abre_asistente_sin_rebaja_y_no_mueve_stock(self):
        guia = self._make_guia('REB-07')
        lot = self._make_lot(guia, 'REB-LOT-07', 3.0, 3.0)
        container, shipment = self._rebajable_container('07', [(lot, 0.0)])
        shipment.state = 'confirmed'
        # B-01 (AD-88): zarpe sin rebajar ya NO bloquea: abre el asistente.
        action = shipment.action_set_in_transit()
        self.assertIsInstance(action, dict)
        self.assertEqual(
            action.get('res_model'), 'lumber.shipment.zarpe.wizard')
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(container.state, 'loaded')
        # Con el contenedor rebajado, el zarpe es directo y no mueve stock.
        container.with_user(self.user_oper).action_rebajar()
        moves_before = self.env['stock.move'].search_count([])
        pickings_before = self.env['stock.picking'].search_count(
            [('origin', 'ilike', shipment.name)])
        result = shipment.action_set_in_transit()
        self.assertTrue(result)
        self.assertEqual(container.state, 'shipped')
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(self.env['stock.move'].search_count([]), moves_before)
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('origin', 'ilike', shipment.name)]), pickings_before)

    def test_08_permisos_por_grupo(self):
        guia = self._make_guia('REB-08')
        lot = self._make_lot(guia, 'REB-LOT-08', 3.0, 3.0)
        container, _ = self._rebajable_container('08', [(lot, 0.0)])
        with self.assertRaises(AccessError):
            container.with_user(self.user_plain).action_rebajar()
        container.with_user(self.user_oper).action_rebajar()
        self.assertEqual(container.state, 'rebajado')
        with self.assertRaises(AccessError):
            container.with_user(self.user_oper).action_reverse_rebaja()
        container.with_user(self.user_jef).action_reverse_rebaja()
        self.assertEqual(container.state, 'loaded')

    def test_09_rebaja_por_nave_requiere_jefatura(self):
        vessel, voyage = self._make_vessel_voyage('09')
        wizard = self.env['lumber.shipment.rebaja.wizard'].with_user(
            self.user_oper).create({
                'vessel_id': vessel.id, 'voyage_id': voyage.id})
        with self.assertRaises(AccessError):
            wizard.action_rebajar()

    def test_10_rebaja_con_email_confirmacion_activo(self):
        """I0.2: «Rebajar contenedor» funciona con el correo de confirmación
        de albaranes ACTIVO (no debe romper por el picking outgoing)."""
        self.company.stock_move_email_validation = True
        try:
            guia = self._make_guia('REB-10')
            lot = self._make_lot(guia, 'REB-LOT-10', 3.0, 3.0)
            container, _ = self._rebajable_container('10', [(lot, 0.0)])
            container.with_user(self.user_oper).action_rebajar()
            self.assertEqual(container.state, 'rebajado')
            self.assertAlmostEqual(self._quant_of(lot), 0.0, places=3)
        finally:
            self.company.stock_move_email_validation = False

    # ══════════════════════════════════════════════════════════════════════
    # I0 / I1 — Endurecimiento y ablandamiento (2026-10-01)
    # ══════════════════════════════════════════════════════════════════════

    def _make_sv_lot_wizard(self, guia, label, disponible):
        """Etiqueta SV que SÍ cumple el dominio del asistente (guía viva)."""
        lot = self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'guia_processing_id': guia.id,
            'volume_source_guia_id': guia.id, 'piezas': 1,
            'technical_validation': 'approved',
            'estado_trazabilidad': 'procesado',
            'volume_purchase_m3': disponible, 'vol_shipment_m3': disponible,
        })
        if disponible > 0:
            self.env['stock.quant']._update_available_quantity(
                self.product, self.location, disponible, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def test_11_sv_oculto_por_defecto_con_filtro(self):
        """I1.8 (D9): los lotes SV se ocultan por defecto; el check los muestra."""
        guia = self._make_guia('REB-11')
        sv_lot = self._make_sv_lot_wizard(guia, 'SV00000000311', 10.0)
        normal_lot = self._make_lot(guia, 'REB-LOT-11', 3.0, 3.0)
        shipment = self._make_shipment('EMB-11')
        container = self._make_container('CONT-11', shipment)
        wizard = self.env['lumber.container.lot.wizard'].create(
            {'container_id': container.id})
        self.assertNotIn(sv_lot, wizard.available_lot_ids)
        self.assertIn(normal_lot, wizard.available_lot_ids)
        wizard.show_sv_lots = True
        self.assertIn(sv_lot, wizard.available_lot_ids)
        self.assertIn(normal_lot, wizard.available_lot_ids)

    def test_12_auditoria_rebaja_con_snapshot_y_hash(self):
        """I0.3: rebaja y reversa dejan snapshot + SHA-256 en madenat.audit.log."""
        guia = self._make_guia('REB-12')
        lot = self._make_lot(guia, 'REB-LOT-12', 3.0, 3.0)
        container, _ = self._rebajable_container('12', [(lot, 0.0)])
        container.with_user(self.user_oper).action_rebajar()
        self._assert_audit_signed(container, 'rebaja')
        container.with_user(self.user_jef).action_reverse_rebaja()
        self._assert_audit_signed(container, 'rebaja_reverse')

    def _assert_audit_signed(self, container, action_type):
        batch = ','.join(str(i) for i in container.line_ids.ids)
        log = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', action_type),
            ('batch_id', '=', batch)], order='id desc', limit=1)
        self.assertTrue(log, 'Falta evento %s' % action_type)
        self.assertTrue(log.audit_snapshot, 'Falta snapshot')
        self.assertEqual(len(log.audit_hash or ''), 64, 'Hash inválido')
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

    def test_13_rolleo_no_actua_sobre_rebajado(self):
        """I0.1: el rolleo rechaza un contenedor «rebajado» con ruta clara."""
        guia = self._make_guia('REB-13')
        lot = self._make_lot(guia, 'REB-LOT-13', 3.0, 3.0)
        container, _ = self._rebajable_container('13', [(lot, 0.0)])
        container.with_user(self.user_oper).action_rebajar()
        self.assertEqual(container.state, 'rebajado')
        wizard = self.env['lumber.container.rollover.wizard'].create({
            'container_id': container.id, 'motive': 'logistics',
            'note': 'Prueba de guarda de rolleo sobre contenedor rebajado.',
            'new_seal': 'SEAL-NEW-13'})
        with self.assertRaises(UserError) as cm:
            wizard.action_confirm_rollover()
        self.assertIn('Revertir rebaja', str(cm.exception))

    def test_14_zarpe_wizard_excepcion_registra_desviacion(self):
        """I1.6 (B-01): zarpe con excepción exige motivo y audita."""
        guia = self._make_guia('REB-14')
        lot = self._make_lot(guia, 'REB-LOT-14', 3.0, 3.0)
        container, shipment = self._rebajable_container('14', [(lot, 0.0)])
        shipment.state = 'confirmed'
        wizard = self.env['lumber.shipment.zarpe.wizard'].create(
            {'shipment_id': shipment.id})
        self.assertEqual(wizard.pending_count, 1)
        with self.assertRaises(UserError):
            wizard.action_zarpar_con_excepcion()
        wizard.reason = 'Autorizado: zarpe urgente por corte de booking.'
        wizard.action_zarpar_con_excepcion()
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(container.state, 'shipped')
        log = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertIn('B-01', log.description)
        self.assertEqual(len(log.audit_hash or ''), 64)

    def test_15_zarpe_wizard_rebajar_y_zarpar(self):
        """I1.6 (B-01): «Rebajar y zarpar» rebaja y zarpa sin excepción."""
        guia = self._make_guia('REB-15')
        lot = self._make_lot(guia, 'REB-LOT-15', 3.0, 3.0)
        container, shipment = self._rebajable_container('15', [(lot, 0.0)])
        shipment.state = 'confirmed'
        wizard = self.env['lumber.shipment.zarpe.wizard'].with_user(
            self.user_oper).create({'shipment_id': shipment.id})
        wizard.action_rebajar_y_zarpar()
        self.assertEqual(container.state, 'shipped')
        self.assertEqual(shipment.state, 'in_transit')
        self.assertAlmostEqual(self._quant_of(lot), 0.0, places=3)

    def test_16_reversa_override_gerencia(self):
        """I1.7 (B-03): reversa con embarque entregado exige Gerencia + motivo."""
        guia = self._make_guia('REB-16')
        lot = self._make_lot(guia, 'REB-LOT-16', 3.0, 3.0)
        container, shipment = self._rebajable_container('16', [(lot, 0.0)])
        container.with_user(self.user_oper).action_rebajar()
        shipment.state = 'delivered'
        # Jefatura (sin Gerencia) → bloqueado.
        with self.assertRaises(UserError):
            container.with_user(self.user_jef).action_reverse_rebaja()
        # Gerencia → abre el wizard de override.
        action = container.with_user(self.user_ger).action_reverse_rebaja()
        self.assertEqual(
            action.get('res_model'),
            'lumber.container.rebaja.reverse.wizard')
        wizard = self.env[
            'lumber.container.rebaja.reverse.wizard'].with_user(
            self.user_ger).create({
                'container_id': container.id,
                'reason': 'Cliente autorizó devolución posterior a entrega.'})
        wizard.action_confirm_override()
        container.invalidate_recordset()
        self.assertEqual(container.state, 'loaded')
        log = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertIn('B-03', log.description)

    def test_17_guard_deviation_hard_y_blando(self):
        """I1.5 (AD-88): helper común _guard_deviation hard/blando."""
        guia = self._make_guia('REB-17')
        lot = self._make_lot(guia, 'REB-LOT-17', 3.0, 3.0)
        container, _ = self._rebajable_container('17', [(lot, 0.0)])
        # Duro → bloquea.
        with self.assertRaises(UserError):
            container._guard_deviation(
                'B-02', 'Mensaje duro.', reason='x', hard=True)
        # Blando sin motivo → bloquea por falta de motivo.
        with self.assertRaises(UserError):
            container._guard_deviation(
                'B-01', 'Mensaje blando.', reason='', hard=False)
        # Blando con motivo → audita y continúa.
        self.assertTrue(container._guard_deviation(
            'B-01', 'Mensaje blando.', reason='Motivo válido de prueba.'))
        log = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertIn('B-01', log.description)
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

