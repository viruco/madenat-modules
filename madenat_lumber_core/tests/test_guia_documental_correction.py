# -*- coding: utf-8 -*-
"""CDP-V1 — Corrección Documental Preservada.

Permite corregir datos DOCUMENTALES de una guía existente (incluida
`validated` o con historia de retorno) SIN modificar estado, stock, lotes,
pickings, movimientos, retornos, costos, SV ni relaciones físicas.

Cobertura T-CDP-01..12. `TransactionCase`: todo se revierte. CDP-V1 es
aditivo: no sustituye ni modifica G1/G2/G3/H1/B1, Intake, BT-04 ni stock.
"""
import base64
import inspect

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'cdp')
class TestGuiaDocumentalCorrection(TransactionCase):
    """T-CDP-01..12 — corrección documental preservada (CDP-V1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env[
            'madenat.guia.processing.documental.correction.wizard']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.Attachment = cls.env['ir.attachment']
        cls.Audit = cls.env['madenat.audit.log']
        cls.CostLine = cls.env['stock.lot.cost.line']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.partner = cls.env['res.partner'].create({
            'name': 'CDP Proveedor', 'is_company': True, 'supplier_rank': 1})
        cls.carrier = cls.env['res.partner'].create({
            'name': 'CDP Transportista', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'CDP Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='compra', state='validated'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 1.0,
            'date_emission': '2026-09-01'})

    def _make_lot(self, name, guia, volumen=5.0):
        return self.StockLot.create({
            'name': name, 'product_id': self.product.id,
            'volumen_m3': volumen, 'guia_processing_id': guia.id})

    def _done_picking(self, lot, guia, qty=5.0, origin='CDP-EMB'):
        pt = self.env.ref('stock.picking_type_in')
        picking = self.Picking.create({
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal.id, 'origin': origin,
            'guia_processing_id': guia.id})
        move = self.Move.create({
            'name': 'CDP move', 'product_id': self.product.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal.id,
            'company_id': self.company.id})
        picking.action_confirm()
        picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'lot_id': lot.id, 'quantity': qty,
            'product_uom_id': self.uom.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal.id, 'picked': True})
        move.picked = True
        move._action_done()
        picking.write({'state': 'done'})
        return picking, move

    def _make_wizard(self, guia, reason='Corrección documental de prueba',
                     **over):
        # Emula `default_get` (el cliente precarga los campos de la guía).
        vals = {'guia_processing_id': guia.id, 'reason': reason}
        for name in guia.CDP_DOCUMENTAL_WHITELIST:
            field = self.Wizard._fields[name]
            value = guia[name]
            vals[name] = (value.id or False) \
                if field.type == 'many2one' else value
        vals.update(over)
        return self.Wizard.create(vals)

    def _physical_snapshot(self):
        return {
            'pickings': self.Picking.search_count([]),
            'moves': self.Move.search_count([]),
            'quants': self.Quant.search_count([]),
            'lots': self.StockLot.search_count([]),
            'costs': self.CostLine.search_count([]),
        }

    # ── T-CDP-01 — Acción secundaria abre wizard (sin G1/verify/validate) ─
    def test_t_cdp_01_accion_abre_wizard(self):
        guia = self._make_guia('CDP-01')
        before = self._physical_snapshot()
        action = guia.action_open_documental_correction_wizard()
        self.assertEqual(
            action['res_model'],
            'madenat.guia.processing.documental.correction.wizard')
        self.assertEqual(action['target'], 'new')
        src = inspect.getsource(
            type(guia).action_open_documental_correction_wizard)
        for forbidden in ('action_verify_data', 'action_validate',
                          'action_reopen_to_draft', 'do_full_processing'):
            self.assertNotIn(forbidden, src)
        self.assertEqual(self._physical_snapshot(), before)
        self.assertEqual(guia.state, 'validated')

    # ── T-CDP-02 — Motivo vacío: bloquea y no escribe ────────────────────
    def test_t_cdp_02_motivo_obligatorio(self):
        guia = self._make_guia('CDP-02')
        guia.write({'notes': 'Original'})
        wiz = self._make_wizard(guia, reason='   ', notes='Intento')
        with self.assertRaises(UserError):
            guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        self.assertEqual(guia.notes, 'Original')
        self.assertFalse(self.Audit.search_count([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')]))

    # ── T-CDP-03 — Solo campos documentales; físico intacto ──────────────
    def test_t_cdp_03_solo_documentales(self):
        guia = self._make_guia('CDP-03')
        lot = self._make_lot('CDP-03-LOT', guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(lot, guia, origin='EMB-CDP-03')
        alternate = self.env['stock.location'].search(
            [('usage', '=', 'internal'), ('id', '!=', self.internal.id)],
            limit=1) or self.internal
        before = self._physical_snapshot()
        lot_ids_before = guia.lot_ids.ids

        wiz = self._make_wizard(
            guia, notes='Nota corregida', date_emission='2026-09-15',
            oc_reference_raw='OC-CDP-03', carrier_id=self.carrier.id,
            assignment_location_id=alternate.id,
            packing_volume_declared_m3=12.5, packing_pieces_declared=42,
            packing_package_count_declared=7, vol_comercial_pdf=13.0,
            total_paquetes=8, total_lotes_unicos=9)
        guia._cdp_apply_documental_correction(wiz)

        guia.invalidate_recordset()
        self.assertEqual(guia.notes, 'Nota corregida')
        self.assertEqual(str(guia.date_emission), '2026-09-15')
        self.assertEqual(guia.oc_reference_raw, 'OC-CDP-03')
        self.assertEqual(guia.carrier_id, self.carrier)
        self.assertEqual(guia.assignment_location_id, alternate)
        self.assertAlmostEqual(guia.packing_volume_declared_m3, 12.5, 3)
        self.assertEqual(guia.packing_pieces_declared, 42)
        self.assertEqual(guia.packing_package_count_declared, 7)
        self.assertAlmostEqual(guia.vol_comercial_pdf, 13.0, 3)
        self.assertEqual(guia.total_paquetes, 8)
        self.assertEqual(guia.total_lotes_unicos, 9)
        # Físico intacto
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(guia.lot_ids.ids, lot_ids_before)
        self.assertEqual(self._physical_snapshot(), before)


    # ── T-CDP-04 — Campo fuera de lista blanca: no persiste ──────────────
    def test_t_cdp_04_fuera_lista_blanca(self):
        guia = self._make_guia('CDP-04')
        with self.assertRaises(UserError):
            guia._cdp_validate_whitelist(['partner_id'])
        wiz = self._make_wizard(guia, notes='ok')
        guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        # Campos prohibidos permanecen intactos.
        self.assertEqual(guia.partner_id, self.partner)
        self.assertEqual(guia.name, 'CDP-04')
        self.assertEqual(guia.tipo_recepcion, 'compra')

    # ── T-CDP-05 — Nueva versión PDF conserva la anterior ────────────────
    def test_t_cdp_05_pdf_versionado(self):
        guia = self._make_guia('CDP-05')
        old = self.Attachment.create({
            'name': 'guia_old.pdf', 'datas': base64.b64encode(b'OLD'),
            'res_model': guia._name, 'res_id': guia.id})
        guia.pdf_attachment_id = old.id
        lines_before = len(guia.processing_line_ids)
        wiz = self._make_wizard(
            guia, new_pdf_file=base64.b64encode(b'NEW').decode(),
            new_pdf_filename='guia_new.pdf')
        guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        self.assertTrue(old.exists(), 'La versión anterior NO se elimina')
        self.assertNotEqual(guia.pdf_attachment_id, old)
        self.assertTrue(guia.pdf_attachment_id.exists())
        self.assertEqual(guia.pdf_attachment_id.name, 'guia_new.pdf')
        self.assertEqual(len(guia.processing_line_ids), lines_before)
        self.assertEqual(guia.state, 'validated')

    # ── T-CDP-06 — Nueva versión Excel conserva la anterior ──────────────
    def test_t_cdp_06_excel_versionado(self):
        guia = self._make_guia('CDP-06')
        old = self.Attachment.create({
            'name': 'packing_old.xlsx',
            'datas': base64.b64encode(b'OLDXLS'),
            'res_model': guia._name, 'res_id': guia.id})
        guia.excel_attachment_id = old.id
        wiz = self._make_wizard(
            guia, new_excel_file=base64.b64encode(b'NEWXLS').decode(),
            new_excel_filename='packing_new.xlsx')
        guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        self.assertTrue(old.exists(), 'La versión anterior NO se elimina')
        self.assertNotEqual(guia.excel_attachment_id, old)
        self.assertEqual(guia.excel_attachment_id.name, 'packing_new.xlsx')
        self.assertEqual(guia.state, 'validated')

    # ── T-CDP-07 — Auditoría deviation + chatter ─────────────────────────
    def test_t_cdp_07_auditoria_y_chatter(self):
        guia = self._make_guia('CDP-07')
        wiz = self._make_wizard(
            guia, reason='OC mal digitada', oc_reference_raw='OC-NEW',
            new_pdf_file=base64.b64encode(b'PDFX').decode(),
            new_pdf_filename='nuevo.pdf')
        guia._cdp_apply_documental_correction(wiz)
        log = self.Audit.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'deviation')], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertEqual(len(log.audit_hash), 64)
        snap = log.audit_snapshot or ''
        for token in ('CDP-V1', '"before"', '"after"', 'edited_fields',
                      'attachments', 'OC mal digitada'):
            self.assertIn(token, snap)
        self.assertIn('oc_reference_raw', snap)
        chatter = '\n'.join(guia.message_ids.mapped('body') or [])
        self.assertIn('Corrección documental', chatter)


    # ── T-CDP-08 — Validada con ingreso no compensado: CDP sin B1 ────────
    def test_t_cdp_08_validada_no_dispara_b1(self):
        guia = self._make_guia('CDP-08')
        lot = self._make_lot('CDP-08-LOT', guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(lot, guia, origin='EMB-CDP-08')
        # B1 detecta el ingreso no compensado (evidencia intacta).
        self.assertTrue(
            guia._b1_revalidation_physical_effect_info()['block_revalidation'])
        before = self._physical_snapshot()
        wiz = self._make_wizard(guia, notes='Corrección en validada')
        guia._cdp_apply_documental_correction(wiz)  # NO dispara B1
        guia.invalidate_recordset()
        self.assertEqual(guia.notes, 'Corrección en validada')
        self.assertEqual(self._physical_snapshot(), before)
        self.assertEqual(guia.state, 'validated')

    # ── T-CDP-09 — Con retorno G3: no altera retorno ni movimientos ──────
    def test_t_cdp_09_con_retorno_g3(self):
        guia = self._make_guia('CDP-09')
        lot = self._make_lot('CDP-09-LOT', guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking, move = self._done_picking(lot, guia, origin='EMB-CDP-09')
        returned = guia._reverse_production_picking(picking)
        self.assertTrue(returned)
        returns_before = self.Picking.search(
            [('return_id', '=', picking.id)]).ids
        moves_before = self.Move.search_count([])
        wiz = self._make_wizard(guia, notes='Con retorno')
        guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        self.assertEqual(
            self.Picking.search([('return_id', '=', picking.id)]).ids,
            returns_before)
        self.assertEqual(self.Move.search_count([]), moves_before)
        self.assertTrue(returned.exists())
        self.assertEqual(guia.notes, 'Con retorno')

    # ── T-CDP-10 — Compute/derivados/financieros no expuestos ────────────
    def test_t_cdp_10_compute_no_expuestos(self):
        guia = self._make_guia('CDP-10')
        forbidden = [
            'state', 'processing_line_ids', 'lot_ids', 'partner_id', 'name',
            'tipo_recepcion', 'order_id', 'consumption_picking_id',
            'additional_cost', 'rate_usd', 'service_volume_m3',
            'vol_fisico', 'vol_comercial', 'vol_shipment_m3', 'vol_total_m3',
            'diff_m3', 'lineas_procesadas', 'date_processed',
            'source_lot_ids', 'lot_details_data']
        wl = set(guia.CDP_DOCUMENTAL_WHITELIST)
        for name in forbidden:
            self.assertNotIn(name, wl)
            self.assertNotIn(name, self.Wizard._fields)
            with self.assertRaises(UserError):
                guia._cdp_validate_whitelist([name])

    # ── T-CDP-11 — Adjuntos ausentes/inválidos: sin borrar evidencia ─────
    def test_t_cdp_11_adjuntos_ausentes(self):
        guia = self._make_guia('CDP-11')
        old = self.Attachment.create({
            'name': 'prev.pdf', 'datas': base64.b64encode(b'PREV'),
            'res_model': guia._name, 'res_id': guia.id})
        guia.pdf_attachment_id = old.id
        before = self._physical_snapshot()
        wiz = self._make_wizard(guia, notes='sin adjunto nuevo')
        guia._cdp_apply_documental_correction(wiz)
        guia.invalidate_recordset()
        self.assertTrue(old.exists())
        self.assertEqual(guia.pdf_attachment_id, old)
        self.assertFalse(wiz.new_pdf_file)
        self.assertEqual(self._physical_snapshot(), before)

    # ── T-CDP-12 — Executor privado exige wizard válido ──────────────────
    def test_t_cdp_12_executor_privado(self):
        guia = self._make_guia('CDP-12')
        other = self._make_guia('CDP-12-OTHER')
        with self.assertRaises(UserError):
            guia._cdp_apply_documental_correction(False)
        with self.assertRaises(UserError):
            guia._cdp_apply_documental_correction(self.Wizard)
        foreign = self._make_wizard(other, notes='x')
        with self.assertRaises(UserError):
            guia._cdp_apply_documental_correction(foreign)
        self.assertEqual(self.Audit.search_count([
            ('guia_processing_id', 'in', [guia.id, other.id]),
            ('action_type', '=', 'deviation')]), 0)
        # No acepta vals arbitrarios: el ejecutor solo lee la lista blanca.
        self.assertNotIn('vals', inspect.signature(
            type(guia)._cdp_apply_documental_correction).parameters)

