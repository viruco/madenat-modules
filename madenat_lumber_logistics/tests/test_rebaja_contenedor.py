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
        container.with_user(self.user_ger).action_reverse_rebaja()
        lot.invalidate_recordset()
        container.invalidate_recordset()
        self.assertAlmostEqual(self._quant_of(lot), 3.0, places=3)
        self.assertEqual(container.state, 'loaded')
        container.with_user(self.user_oper).action_rebajar()
        shipment.state = 'delivered'
        # R2 sólo Gerencia: Jefatura recibe AccessError.
        with self.assertRaises(AccessError):
            container.with_user(self.user_jef).action_reverse_rebaja()

    def test_07_zarpe_abre_asistente_sin_rebaja_y_no_mueve_stock(self):
        guia = self._make_guia('REB-07')
        lot = self._make_lot(guia, 'REB-LOT-07', 3.0, 3.0)
        container, shipment = self._rebajable_container('07', [(lot, 0.0)])
        shipment.state = 'confirmed'
        # B-01 (AD-88): zarpe sin rebajar ya NO bloquea: abre el asistente.
        # Confirmar el zarpe exige Jefatura/Gerencia (Operaciones sólo abre).
        action = shipment.with_user(self.user_jef).action_set_in_transit()
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
        result = shipment.with_user(self.user_jef).action_set_in_transit()
        self.assertTrue(result)
        shipment.invalidate_recordset()
        container.invalidate_recordset()
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
        container.with_user(self.user_ger).action_reverse_rebaja()
        self.assertEqual(container.state, 'loaded')

    def test_09_rebaja_por_motonave_contrato_permisos(self):
        """Contrato único: Operaciones/Jefatura/Gerencia pueden; un usuario sin
        rol operativo no puede ni abrir el asistente (ACL)."""
        vessel, voyage = self._make_vessel_voyage('09')
        # Operaciones ya NO se bloquea por rol (antes se exigía Jefatura).
        # Sin selección => UserError de validación, no AccessError.
        wizard_oper = self.env['lumber.shipment.rebaja.wizard'].with_user(
            self.user_oper).create({
                'vessel_id': vessel.id, 'voyage_id': voyage.id})
        with self.assertRaises(UserError):
            wizard_oper.action_rebajar()
        # Usuario sin rol operativo: ACL del wizard lo excluye al crear.
        with self.assertRaises(AccessError):
            self.env['lumber.shipment.rebaja.wizard'].with_user(
                self.user_plain).create({
                    'vessel_id': vessel.id, 'voyage_id': voyage.id})

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
        container.with_user(self.user_ger).action_reverse_rebaja()
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
        """I1.6 / B-01 (2026-10-04): el zarpe con excepción exige motivo, abre
        la B-01 y audita; el Contenedor pendiente CONSERVA su estado físico real
        (nunca `shipped`) y no se mueve inventario."""
        guia = self._make_guia('REB-14')
        lot = self._make_lot(guia, 'REB-LOT-14', 3.0, 3.0)
        container, shipment = self._rebajable_container('14', [(lot, 0.0)])
        shipment.state = 'confirmed'
        prev_state = container.state
        # El zarpe (normal o B-01) sólo lo confirma Jefatura/Gerencia.
        wizard = self.env['lumber.shipment.zarpe.wizard'].with_user(
            self.user_jef).create({'shipment_id': shipment.id})
        self.assertEqual(wizard.pending_count, 1)
        moves_before = self.env['stock.move'].search_count([])
        pickings_before = self.env['stock.picking'].search_count(
            [('origin', 'ilike', shipment.name)])
        quants_before = self.env['stock.quant'].search_count([])
        with self.assertRaises(UserError):
            wizard.action_zarpar_con_excepcion()
        wizard.reason = 'Autorizado: zarpe urgente por corte de booking.'
        wizard.action_zarpar_con_excepcion()
        shipment.invalidate_recordset()
        container.invalidate_recordset()
        # Contrato B-01: zarpa el Embarque; el pendiente NO pasa a shipped.
        self.assertEqual(shipment.state, 'in_transit')
        self.assertEqual(container.state, prev_state)
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(shipment.b01_exception_state, 'open')
        self.assertEqual(shipment.b01_exception_reason, wizard.reason)
        self.assertAlmostEqual(self._quant_of(lot), 3.0, places=3)
        # Sin efectos físicos: ni movimientos, ni albaranes, ni quants nuevos.
        self.assertEqual(
            self.env['stock.move'].search_count([]), moves_before)
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('origin', 'ilike', shipment.name)]), pickings_before)
        self.assertEqual(
            self.env['stock.quant'].search_count([]), quants_before)
        # Auditoría B-01 append-only con snapshot y SHA-256 exacto.
        log = self.env['madenat.audit.log'].search([
            ('action_type', '=', 'b01_departure_exception'),
            ('batch_id', '=', str(shipment.id))], order='id desc', limit=1)
        self.assertTrue(log, 'Falta la auditoría B-01 del zarpe')
        self.assertEqual(shipment.b01_exception_audit_id, log)
        self.assertIn('B-01', log.description)
        self.assertEqual(
            log.audit_hash,
            hashlib.sha256(log.audit_snapshot.encode('utf-8')).hexdigest())

    def test_15_zarpe_wizard_rebajar_y_zarpar(self):
        """I1.6 / B-01 (2026-10-04): «Rebajar y zarpar» sólo lo confirma
        Jefatura/Gerencia; Operaciones no puede confirmar el zarpe normal."""
        guia = self._make_guia('REB-15')
        lot = self._make_lot(guia, 'REB-LOT-15', 3.0, 3.0)
        container, shipment = self._rebajable_container('15', [(lot, 0.0)])
        shipment.state = 'confirmed'
        # Operaciones abre el asistente pero NO puede confirmar el zarpe.
        wizard_oper = self.env['lumber.shipment.zarpe.wizard'].with_user(
            self.user_oper).create({'shipment_id': shipment.id})
        with self.assertRaises(AccessError):
            wizard_oper.action_rebajar_y_zarpar()
        shipment.invalidate_recordset()
        container.invalidate_recordset()
        self.assertEqual(shipment.state, 'confirmed')
        self.assertEqual(container.state, 'loaded')
        self.assertAlmostEqual(self._quant_of(lot), 3.0, places=3)
        # Jefatura confirma el zarpe normal: rebaja todos y zarpa.
        wizard = self.env['lumber.shipment.zarpe.wizard'].with_user(
            self.user_jef).create({'shipment_id': shipment.id})
        wizard.action_rebajar_y_zarpar()
        container.invalidate_recordset()
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
        # Jefatura (sin Gerencia) → AccessError (R2 sólo Gerencia).
        with self.assertRaises(AccessError):
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

    # ══════════════════════════════════════════════════════════════════════
    # P0 (2026-10-03) — Guarda de rolleo seguro (post-rebaja / post-zarpe)
    # `lumber.container._assert_rollover_eligible()`.
    # ══════════════════════════════════════════════════════════════════════

    def _rollover_guard_container(self, tag, lot, state='loaded'):
        """Contenedor consolidado (draft) listo para probar la guarda."""
        container, shipment = self._rebajable_container(tag, [(lot, 0.0)])
        if state != container.state:
            container.write({'state': state})
            container.invalidate_recordset()
        return container, shipment

    def _stock_counts(self):
        """Contadores de stock/auditoría para probar que el guard no escribe."""
        env = self.env
        return {
            'picking': env['stock.picking'].search_count([]),
            'move': env['stock.move'].search_count([]),
            'move_line': env['stock.move.line'].search_count([]),
            'quant': env['stock.quant'].search_count([]),
            'audit': env['madenat.audit.log'].sudo().search_count([]),
        }

    def test_rollover_allowed_without_rebaja(self):
        """P0: contenedor cargado/sellado sin rebaja y embarque draft/confirmed
        es elegible para rollear (la guarda no lanza)."""
        guia = self._make_guia('ROLL-01')
        lot = self._make_lot(guia, 'ROLL-LOT-01', 3.0, 3.0)
        container, shipment = self._rollover_guard_container('R1', lot)
        # Embarque en borrador + contenedor cargado → permitido.
        self.assertTrue(container.with_user(
            self.user_oper)._assert_rollover_eligible())
        # Embarque confirmado + contenedor sellado → permitido.
        shipment.state = 'confirmed'
        container.write({'state': 'sealed'})
        container.invalidate_recordset()
        self.assertTrue(container.with_user(
            self.user_jef)._assert_rollover_eligible())

    def test_rollover_blocked_when_container_shipped(self):
        """P0: un contenedor `shipped` se bloquea por la ruta del asistente y
        no modifica shipment_id, estado, sello ni fecha de sellado."""
        guia = self._make_guia('ROLL-02')
        lot = self._make_lot(guia, 'ROLL-LOT-02', 3.0, 3.0)
        container, _ = self._rollover_guard_container('R2', lot, state='shipped')
        container.write({'seal_number': 'SEAL-SHIP-02'})
        container.invalidate_recordset()
        before = (
            container.shipment_id.id, container.state,
            container.seal_number, container.sealing_date)
        wizard = self.env['lumber.container.rollover.wizard'].with_user(
            self.user_oper).create({
                'container_id': container.id, 'motive': 'logistics',
                'note': 'Prueba P0: rolleo bloqueado en contenedor embarcado.',
                'new_seal': 'SEAL-NEW-ROLL-02'})
        with self.assertRaises(UserError):
            wizard.action_confirm_rollover()
        container.invalidate_recordset()
        self.assertEqual(
            (container.shipment_id.id, container.state,
             container.seal_number, container.sealing_date), before)

    def test_rollover_blocked_when_rebaja_line_exists(self):
        """P0: una línea con `rebaja_state='rebajado'` bloquea aunque el estado
        del contenedor parezca elegible, sin crear stock ni auditoría."""
        guia = self._make_guia('ROLL-03')
        lot = self._make_lot(guia, 'ROLL-LOT-03', 3.0, 3.0)
        container, _ = self._rollover_guard_container('R3', lot)
        container.with_user(self.user_oper).action_rebajar()
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        self.assertEqual(line.rebaja_state, 'rebajado')
        # Estado "inconsistente": contenedor Cargado pero línea rebajada.
        container.write({'state': 'loaded'})
        container.invalidate_recordset()
        counts = self._stock_counts()
        with self.assertRaises(UserError):
            container.with_user(self.user_oper)._assert_rollover_eligible()
        self.assertEqual(self._stock_counts(), counts)

    def test_rollover_blocked_when_rebaja_picking_done(self):
        """P0: una `rebaja_picking_id` en `done` bloquea aunque se manipule el
        estado de línea/contenedor, sin writes de negocio."""
        guia = self._make_guia('ROLL-04')
        lot = self._make_lot(guia, 'ROLL-LOT-04', 3.0, 3.0)
        container, _ = self._rollover_guard_container('R4', lot)
        container.with_user(self.user_oper).action_rebajar()
        line = container.line_ids.filtered(lambda l: l.lot_id == lot)
        self.assertEqual(line.rebaja_picking_id.state, 'done')
        # Se "oculta" la evidencia de estado para aislar la condición del picking.
        line.write({'rebaja_state': 'pending'})
        container.write({'state': 'loaded'})
        container.invalidate_recordset()
        counts = self._stock_counts()
        with self.assertRaises(UserError):
            container.with_user(self.user_oper)._assert_rollover_eligible()
        self.assertEqual(self._stock_counts(), counts)

    def test_rollover_blocked_when_shipment_in_transit(self):
        """P0: un embarque `in_transit` bloquea el rolleo sin tocar stock."""
        guia = self._make_guia('ROLL-05')
        lot = self._make_lot(guia, 'ROLL-LOT-05', 3.0, 3.0)
        container, shipment = self._rollover_guard_container('R5', lot)
        shipment.state = 'in_transit'
        quant_before = self._quant_of(lot)
        counts = self._stock_counts()
        with self.assertRaises(UserError):
            container.with_user(self.user_oper)._assert_rollover_eligible()
        container.invalidate_recordset()
        self.assertEqual(container.state, 'loaded')
        self.assertEqual(container.shipment_id, shipment)
        self.assertEqual(self._stock_counts(), counts)
        self.assertAlmostEqual(self._quant_of(lot), quant_before, places=3)

    def test_rollover_blocked_for_unauthorized_user(self):
        """P0: sin Operaciones/Jefatura/Gerencia el rolleo se rechaza por rol
        y no modifica nada."""
        guia = self._make_guia('ROLL-06')
        lot = self._make_lot(guia, 'ROLL-LOT-06', 3.0, 3.0)
        container, _ = self._rollover_guard_container('R6', lot)
        counts = self._stock_counts()
        with self.assertRaises(AccessError):
            container.with_user(self.user_plain)._assert_rollover_eligible()
        # La ruta de acción también queda protegida en servidor.
        with self.assertRaises(AccessError):
            container.with_user(self.user_plain).action_open_rollover_wizard()
        self.assertEqual(self._stock_counts(), counts)
        self.assertEqual(self._stock_counts(), counts)

    # ══════════════════════════════════════════════════════════════════════
    # Rebaja Inteligente por Motonave — asistente operativo (2026-10-03)
    # ══════════════════════════════════════════════════════════════════════

    def _wizard(self, vessel, voyage=None, containers=None, user=None):
        vals = {'vessel_id': vessel.id}
        if voyage:
            vals['voyage_id'] = voyage.id
        if containers is not None:
            vals['container_ids'] = [(6, 0, [c.id for c in containers])]
        wiz = self.env['lumber.shipment.rebaja.wizard']
        if user:
            wiz = wiz.with_user(user)
        return wiz.create(vals)

    def test_wz_01_motonave_obligatoria(self):
        self.assertTrue(
            self.env['lumber.shipment.rebaja.wizard']._fields[
                'vessel_id'].required)

    def test_wz_02_viaje_condicional_y_alcance(self):
        """El alcance carga EXCLUSIVAMENTE contenedores de la motonave; el viaje
        sólo filtra dentro de ella."""
        guia = self._make_guia('WZ-02')
        lot_a = self._make_lot(guia, 'WZ-02-A', 3.0, 3.0)
        lot_b = self._make_lot(guia, 'WZ-02-B', 3.0, 3.0)
        vessel_a, voyage_a = self._make_vessel_voyage('W2A')
        vessel_b, _voyage_b = self._make_vessel_voyage('W2B')
        ship_a = self._make_shipment('EMB-W2A', vessel_a, voyage_a)
        ship_b = self._make_shipment('EMB-W2B', vessel_b)
        c_a = self._make_container('CONT-W2A', ship_a)
        c_b = self._make_container('CONT-W2B', ship_b)
        self._assign(c_a, lot_a)
        self._assign(c_b, lot_b)
        c_a.write({'state': 'loaded'})
        c_b.write({'state': 'loaded'})
        wiz = self._wizard(vessel_a, voyage_a, user=self.user_oper)
        self.assertTrue(wiz.voyage_available)
        self.assertIn(c_a, wiz.available_container_ids)
        self.assertNotIn(c_b, wiz.available_container_ids)
        self.assertNotIn(c_b, wiz.line_ids.mapped('container_id'))
        self.assertIn(('vessel_id', '=', vessel_a.id),
                      wiz._get_selection_domain())

    def test_wz_03_clasifica_excluidos_con_motivo(self):
        guia = self._make_guia('WZ-03')
        good = self._make_lot(guia, 'WZ-03-G', 2.0, 2.0)
        nostock = self._make_lot(guia, 'WZ-03-N', 2.0, 0.0)
        vessel, voyage = self._make_vessel_voyage('W3')
        ship = self._make_shipment('EMB-W3', vessel, voyage)
        c_good = self._make_container('CONT-W3-G', ship)
        c_nostock = self._make_container('CONT-W3-N', ship)
        c_loading = self._make_container('CONT-W3-L', ship)
        self._assign(c_good, good)
        self._assign(c_nostock, nostock)
        c_good.write({'state': 'loaded'})
        c_nostock.write({'state': 'loaded'})
        c_loading.write({'state': 'loading'})
        wiz = self._wizard(vessel, voyage, user=self.user_oper)
        lines = {l.container_id: l for l in wiz.line_ids}
        self.assertTrue(lines[c_good].eligible)
        self.assertFalse(lines[c_nostock].eligible)
        reason = (lines[c_nostock].exclusion_reason or '').lower()
        self.assertTrue('stock' in reason or 'disponible' in reason, reason)
        self.assertFalse(lines[c_loading].eligible)
        self.assertIn('Cargando', lines[c_loading].exclusion_reason or '')
        self.assertEqual(wiz.container_count, 1)
        self.assertEqual(wiz.excluded_count, 2)

    def test_wz_04_totales_solo_sobre_seleccion(self):
        guia = self._make_guia('WZ-04')
        lot1 = self._make_lot(guia, 'WZ-04-1', 2.0, 2.0)
        lot2 = self._make_lot(guia, 'WZ-04-2', 5.0, 5.0)
        vessel, voyage = self._make_vessel_voyage('W4')
        ship = self._make_shipment('EMB-W4', vessel, voyage)
        c1 = self._make_container('CONT-W4-1', ship)
        c2 = self._make_container('CONT-W4-2', ship)
        self._assign(c1, lot1)
        self._assign(c2, lot2)
        c1.write({'state': 'loaded'})
        c2.write({'state': 'loaded'})
        wiz = self._wizard(vessel, voyage, [c1], user=self.user_oper)
        self.assertAlmostEqual(wiz.total_rebaja_m3, 2.0, places=3)
        self.assertAlmostEqual(wiz.total_physical_m3, 2.0, places=3)
        self.assertEqual(wiz.selected_count, 1)
        wiz.write({'container_ids': [(6, 0, [c1.id, c2.id])]})
        wiz.invalidate_recordset()
        self.assertAlmostEqual(wiz.total_rebaja_m3, 7.0, places=3)
        self.assertEqual(wiz.selected_count, 2)

    def test_wz_05_inyeccion_de_otra_motonave_bloqueada(self):
        """Un contenedor de otra motonave inyectado por RPC no se procesa."""
        guia = self._make_guia('WZ-05')
        lot_b = self._make_lot(guia, 'WZ-05-B', 3.0, 3.0)
        vessel_a, voyage_a = self._make_vessel_voyage('W5A')
        vessel_b, voyage_b = self._make_vessel_voyage('W5B')
        ship_b = self._make_shipment('EMB-W5B', vessel_b, voyage_b)
        c_b = self._make_container('CONT-W5B', ship_b)
        self._assign(c_b, lot_b)
        c_b.write({'state': 'loaded'})
        wiz = self._wizard(vessel_a, voyage_a, [c_b], user=self.user_oper)
        wiz.action_rebajar()
        c_b.invalidate_recordset()
        self.assertEqual(c_b.state, 'loaded')
        self.assertIn('CONT-W5B', wiz.result_message)
        self.assertAlmostEqual(self._quant_of(lot_b), 3.0, places=3)

    def test_wz_06_operaciones_confirma_y_audita_nave(self):
        """Operaciones confirma; el snapshot de auditoría incluye nave/viaje y
        el asistente NO se cierra automáticamente."""
        guia = self._make_guia('WZ-06')
        lot = self._make_lot(guia, 'WZ-06-L', 3.0, 3.0)
        vessel, voyage = self._make_vessel_voyage('W6')
        ship = self._make_shipment('EMB-W6', vessel, voyage)
        container = self._make_container('CONT-W6', ship)
        self._assign(container, lot)
        container.write({'state': 'loaded'})
        wiz = self._wizard(vessel, voyage, [container], user=self.user_oper)
        action = wiz.action_rebajar()
        container.invalidate_recordset()
        self.assertEqual(container.state, 'rebajado')
        self.assertAlmostEqual(self._quant_of(lot), 0.0, places=3)
        # No cierra: recarga el propio registro (target new), no act_window_close.
        self.assertNotEqual(action, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(action.get('res_model'),
                         'lumber.shipment.rebaja.wizard')
        # Snapshot aditivo con motonave/viaje derivados del embarque.
        batch = ','.join(str(i) for i in container.line_ids.ids)
        log = self.env['madenat.audit.log'].sudo().search([
            ('action_type', '=', 'rebaja'), ('batch_id', '=', batch)],
            order='id desc', limit=1)
        self.assertTrue(log)
        self.assertIn('vessel_id', log.audit_snapshot)
        self.assertIn(str(vessel.id), log.audit_snapshot)
        self.assertIn('voyage_id', log.audit_snapshot)

    def test_wz_07_sin_doble_rebaja(self):
        """Ejecutar de nuevo no crea otro picking ni descuenta stock de nuevo."""
        guia = self._make_guia('WZ-07')
        lot = self._make_lot(guia, 'WZ-07-L', 3.0, 3.0)
        vessel, voyage = self._make_vessel_voyage('W7')
        ship = self._make_shipment('EMB-W7', vessel, voyage)
        container = self._make_container('CONT-W7', ship)
        self._assign(container, lot)
        container.write({'state': 'loaded'})
        wiz = self._wizard(vessel, voyage, [container], user=self.user_oper)
        wiz.action_rebajar()
        container.invalidate_recordset()
        origin = container.line_ids.filtered(
            lambda l: l.lot_id == lot).rebaja_picking_id.origin
        picks = self.env['stock.picking'].search_count(
            [('origin', '=', origin)])
        # Segundo intento: contenedor ya rebajado => excluido, sin nuevo picking.
        wiz2 = self._wizard(vessel, voyage, [container], user=self.user_oper)
        wiz2.action_rebajar()
        self.assertEqual(self._quant_of(lot), 0.0)
        self.assertEqual(
            self.env['stock.picking'].search_count([('origin', '=', origin)]),
            picks)
        self.assertEqual(container.state, 'rebajado')

    def test_wz_08_resultado_parcial_sin_cerrar(self):
        """Un lote sin stock produce resultado parcial explícito por contenedor."""
        guia = self._make_guia('WZ-08')
        good = self._make_lot(guia, 'WZ-08-G', 2.0, 2.0)
        bad = self._make_lot(guia, 'WZ-08-B', 2.0, 0.0)
        vessel, voyage = self._make_vessel_voyage('W8')
        ship = self._make_shipment('EMB-W8', vessel, voyage)
        c_good = self._make_container('CONT-W8-G', ship)
        c_bad = self._make_container('CONT-W8-B', ship)
        self._assign(c_good, good)
        self._assign(c_bad, bad)
        c_good.write({'state': 'loaded'})
        c_bad.write({'state': 'loaded'})
        wiz = self._wizard(
            vessel, voyage, [c_good, c_bad], user=self.user_oper)
        action = wiz.action_rebajar()
        c_good.invalidate_recordset()
        c_bad.invalidate_recordset()
        self.assertEqual(c_good.state, 'rebajado')
        self.assertEqual(c_bad.state, 'loaded')
        self.assertIn('CONT-W8-B', wiz.result_message)
        self.assertEqual(action.get('res_model'),
                         'lumber.shipment.rebaja.wizard')
