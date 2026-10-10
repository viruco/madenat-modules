# -*- coding: utf-8 -*-
"""Bloque A/B/C (CANON/19 §19.11, 2026-10-10) — Relación de conciliación
envío a procesador ↔ retorno.

Cubre, sin efectos en stock:

* T1  Envío con un retorno (relación registrada, un solo evento de auditoría).
* T2  Un envío con VARIOS retornos parciales (dos guías).
* T3  Un retorno asociado a VARIOS envíos.
* T4  Procesador incorrecto ⇒ rechazo.
* T5  Envío NO elegible (destino que no es de procesador) ⇒ rechazo.
* T6  Relación duplicada ⇒ rechazo; `_get_or_create_link` idempotente.
* T7  Doble aplicación ⇒ sin duplicar auditoría.
* T8  Reversa (append-only): `reversed`, no eliminable.
* T9  Permisos por ORM/RPC (sin grupo ⇒ AccessError; auditoría read-only).
* T10 Sin movimientos de stock duplicados.
* T11 Históricos sin asociación: estado `no_return` sin crear nada.
* T12 Integración con el asistente de imputación (aplica + registra relación).

Datos 100 % aislados (TransactionCase).
"""
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestProcessorReturnLink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'REL Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'REL Supplier', 'is_company': True})
        cls.processor = cls.env['res.partner'].create({
            'name': 'REL Planta', 'is_company': True, 'is_processor': True})
        cls.processor2 = cls.env['res.partner'].create({
            'name': 'REL Planta 2', 'is_company': True, 'is_processor': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Link = cls.env['madenat.processor.return.link']
        cls.ShipWizard = cls.env['madenat.processor.shipment.wizard']
        cls.ImpWizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Quant = cls.env['stock.quant']

        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('rel_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk('rel_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_aud = _mk('rel_aud', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_auditoria'])
        cls.user_plain = _mk('rel_plain', ['base.group_user'])

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _make_guia(self, name, processor=None, service_return='yes',
                   tipo='service'):
        processor = processor or self.processor
        return self.Guia.sudo().create({
            'name': name, 'partner_id': processor.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': tipo,
            'service_return_confirmation': service_return,
            'date_emission': '2026-10-10'})

    def _make_lot(self, label, qty, flow='volume'):
        lot = self.StockLot.sudo().create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': flow,
            'volumen_m3': qty, 'volume_purchase_m3': qty})
        if qty:
            self.Quant._update_available_quantity(
                self.product, self.stock_loc, qty, lot_id=lot)
        lot.invalidate_recordset()
        return lot

    def _make_etiqueta(self, guia, label, nominal):
        lot = self._make_lot(label, nominal, flow='tarja')
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _make_envio(self, qty=5.0, processor=None, label='REL-ENV'):
        processor = processor or self.processor
        # El envío transporta material físico (lote tipo tarja); no es un SV.
        lot = self._make_lot(label, qty, flow='tarja')
        wiz = self.ShipWizard.sudo().create({
            'processor_id': processor.id,
            'source_location_id': self.stock_loc.id,
            'line_ids': [(0, 0, {
                'lot_id': lot.id,
                'source_location_id': self.stock_loc.id,
                'quantity': qty,
            })]})
        res = wiz.action_send()
        return self.env['stock.picking'].browse(res['res_id'])

    def _make_link(self, picking, guia, state='draft'):
        link = self.Link.sudo().create({
            'picking_id': picking.id, 'guia_processing_id': guia.id})
        if state == 'linked':
            link.with_user(self.user_oper).action_link()
        return link

    def _audit(self, action, batch=None):
        domain = [('action_type', '=', action)]
        if batch:
            domain.append(('batch_id', '=', batch))
        return self.AuditLog.search(domain)

    def _stock_snapshot(self):
        return (
            self.Quant.search_count([]),
            self.env['stock.picking'].search_count([]),
            self.env['stock.move'].search_count([]),
            self.env['stock.move.line'].search_count([]),
        )

    # ── T1 ───────────────────────────────────────────────────────────────
    def test_t1_envio_con_un_retorno(self):
        guia = self._make_guia('REL-T1')
        picking = self._make_envio(qty=5.0)
        link = self._make_link(picking, guia)
        self.assertEqual(link.state, 'draft')
        self.assertEqual(link.processor_id, self.processor)
        link.with_user(self.user_oper).action_link()
        self.assertEqual(link.state, 'linked')
        self.assertEqual(link.linked_by_id, self.user_oper)
        events = self._audit('processor_return_link', batch=link.name)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events.audit_hash), 64)

    # ── T2 ───────────────────────────────────────────────────────────────
    def test_t2_envio_con_varios_retornos_parciales(self):
        picking = self._make_envio(qty=9.0)
        guia1 = self._make_guia('REL-T2a')
        guia2 = self._make_guia('REL-T2b')
        l1 = self._make_link(picking, guia1)
        l2 = self._make_link(picking, guia2)
        l1.with_user(self.user_oper).action_link()
        l2.with_user(self.user_oper).action_link()
        self.assertEqual(len(picking.madenat_processor_return_link_ids), 2)
        self.assertEqual(picking.madenat_return_link_state, 'linked')

    # ── T3 ───────────────────────────────────────────────────────────────
    def test_t3_retorno_con_varios_envios(self):
        guia = self._make_guia('REL-T3')
        p1 = self._make_envio(qty=3.0, label='REL-T3-A')
        p2 = self._make_envio(qty=4.0, label='REL-T3-B')
        self._make_link(p1, guia).with_user(self.user_oper).action_link()
        self._make_link(p2, guia).with_user(self.user_oper).action_link()
        self.assertEqual(len(guia.processor_return_link_ids), 2)
        self.assertEqual(guia.processor_return_link_state, 'linked')

    # ── T4 ───────────────────────────────────────────────────────────────
    def test_t4_procesador_incorrecto(self):
        guia = self._make_guia('REL-T4')  # procesador = self.processor
        picking = self._make_envio(qty=2.0, processor=self.processor2)
        with self.assertRaises(ValidationError):
            self.Link.sudo().create({
                'picking_id': picking.id, 'guia_processing_id': guia.id})

    # ── T5 ───────────────────────────────────────────────────────────────
    def test_t5_envio_no_elegible(self):
        guia = self._make_guia('REL-T5')
        dest = self.env['stock.location'].create({
            'name': 'REL-PLAIN-DEST', 'usage': 'internal',
            'location_id': self.stock_loc.id, 'company_id': self.company.id})
        ptype = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.company.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': ptype.id, 'location_id': self.stock_loc.id,
            'location_dest_id': dest.id, 'company_id': self.company.id})
        with self.assertRaises(ValidationError):
            self.Link.sudo().create({
                'picking_id': picking.id, 'guia_processing_id': guia.id})
        # No aparece como envío elegible.
        eligible = self.Link._eligible_shipment_pickings(
            guia, self.processor)
        self.assertNotIn(picking, eligible)

    # ── T6 ───────────────────────────────────────────────────────────────
    def test_t6_relacion_duplicada_e_idempotente(self):
        guia = self._make_guia('REL-T6')
        picking = self._make_envio(qty=2.0)
        link = self._make_link(picking, guia)
        with self.assertRaises(ValidationError):
            self.Link.sudo().create({
                'picking_id': picking.id, 'guia_processing_id': guia.id})
        again = self.Link._get_or_create_link(picking, guia)
        self.assertEqual(again, link)
        self.assertEqual(len(self.Link.search([
            ('picking_id', '=', picking.id),
            ('guia_processing_id', '=', guia.id)])), 1)

    # ── T7 ───────────────────────────────────────────────────────────────
    def test_t7_doble_aplicacion(self):
        guia = self._make_guia('REL-T7')
        picking = self._make_envio(qty=2.0)
        link = self._make_link(picking, guia)
        link.with_user(self.user_oper).action_link()
        link.with_user(self.user_oper).action_link()  # idempotente
        self.assertEqual(link.state, 'linked')
        self.assertEqual(
            len(self._audit('processor_return_link', batch=link.name)), 1)


    # ── T8 ───────────────────────────────────────────────────────────────
    def test_t8_reversa_append_only(self):
        guia = self._make_guia('REL-T8')
        picking = self._make_envio(qty=2.0)
        link = self._make_link(picking, guia, state='linked')
        # Operaciones NO puede reversar (solo Jefatura/Gerencia).
        with self.assertRaises(AccessError):
            link.with_user(self.user_oper).action_reverse()
        link.reversal_reason = 'error de digitación'
        link.with_user(self.user_jef).action_reverse()
        self.assertEqual(link.state, 'reversed')
        self.assertEqual(link.reversed_by_id, self.user_jef)
        self.assertEqual(
            len(self._audit('processor_return_link_reverse',
                            batch=link.name)), 1)
        # Append-only: la relación registrada/reversada no se elimina.
        with self.assertRaises(UserError):
            link.unlink()

    # ── T9 ───────────────────────────────────────────────────────────────
    def test_t9_permisos_orm_rpc(self):
        guia = self._make_guia('REL-T9')
        picking = self._make_envio(qty=2.0)
        # Sin grupo funcional: no puede crear la relación.
        with self.assertRaises(AccessError):
            self.Link.with_user(self.user_plain).create({
                'picking_id': picking.id, 'guia_processing_id': guia.id})
        # Auditoría: solo lectura ⇒ no puede registrar la conciliación.
        link = self._make_link(picking, guia)
        with self.assertRaises(AccessError):
            link.with_user(self.user_aud).action_link()
        # Operaciones sí puede.
        link.with_user(self.user_oper).action_link()
        self.assertEqual(link.state, 'linked')

    # ── T10 ──────────────────────────────────────────────────────────────
    def test_t10_sin_movimientos_de_stock(self):
        guia = self._make_guia('REL-T10')
        picking = self._make_envio(qty=2.0)
        before = self._stock_snapshot()
        link = self._make_link(picking, guia, state='linked')
        self.assertEqual(self._stock_snapshot(), before)
        self.assertEqual(
            self.env['madenat.sv.operation'].search_count(
                [('action_type', '=', 'imputacion')]), 0)
        self.assertTrue(link.exists())

    # ── T11 ──────────────────────────────────────────────────────────────
    def test_t11_historicos_sin_asociacion(self):
        guia = self._make_guia('REL-T11')
        picking = self._make_envio(qty=2.0)
        # No se crea ninguna relación automáticamente.
        self.assertEqual(self.Link.search_count([
            ('guia_processing_id', '=', guia.id)]), 0)
        self.assertEqual(guia.processor_return_link_state, 'no_return')
        self.assertEqual(picking.madenat_return_link_state, 'no_return')

    # ── T12 ──────────────────────────────────────────────────────────────
    def test_t12_asistente_imputacion_registra_relacion(self):
        guia = self._make_guia('REL-T12')
        etiqueta = self._make_etiqueta(guia, 'REL-T12-E', 10.0)
        sv = self.StockLot.sudo().create({
            'name': 'SV00000009999', 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volumen_m3': 100.0, 'volume_purchase_m3': 100.0})
        picking = self._make_envio(qty=6.0)
        wiz = self.ImpWizard.with_user(self.user_oper).with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({
                'guia_processing_id': guia.id,
                'shipment_picking_ids': [(6, 0, [picking.id])]})
        wiz._onchange_guia_processing_id()
        wline = wiz.line_ids
        self.assertEqual(wline.processed_lot_id, etiqueta)
        self.env['madenat.sv.imputation.wizard.sv.line'].with_user(
            self.user_oper).create({
                'wizard_id': wiz.id, 'wizard_line_id': wline.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': 10.0})
        res = wiz.with_user(self.user_oper).action_apply()
        imp = self.Imputation.browse(res['res_id'])
        self.assertEqual(imp.state, 'applied')
        self.assertEqual(len(imp.return_link_ids), 1)
        self.assertEqual(imp.return_link_ids.state, 'linked')
        self.assertEqual(imp.return_link_ids.picking_id, picking)
        self.assertEqual(imp.return_link_ids.imputation_id, imp)
