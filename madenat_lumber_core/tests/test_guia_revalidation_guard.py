# -*- coding: utf-8 -*-
"""B1 — Guard server-side contra revalidación física duplicada.

`madenat.guia.processing` puede regresar documentalmente de `validated` a
`verified` (p. ej. `action_verify_data`) y, sin guard, `action_validate` /
`do_full_processing` volverían a materializar stock sobre lotes reutilizados
cuando ya existe un ingreso físico `done` NO compensado.

Cobertura T-B1-01..11. `TransactionCase`: todo se revierte. El guard es
solo lectura: NO escribe `stock.quant`, `stock.lot`, `stock.move`,
`stock.move.line`, `stock.picking` ni capas de valoración; no usa `origin`
textual ni `lot_id` aislado como llave; excluye granel/SV y BT-04.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'b1')
class TestGuiaRevalidationGuard(TransactionCase):
    """T-B1-01..11 — guard de revalidación física duplicada."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.Subproducto = cls.env['madenat.subproducto']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.Audit = cls.env['madenat.audit.log']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.internal = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')
        cls.uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.partner = cls.env['res.partner'].create({
            'name': 'B1 Proveedor', 'is_company': True, 'supplier_rank': 1})
        cls.product = cls.env['product.product'].create({
            'name': 'B1 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom.id, 'uom_po_id': cls.uom.id})

    # ── Fábricas ─────────────────────────────────────────────────────────
    def _make_guia(self, name, tipo='compra', state='verified'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal.id,
            'tipo_recepcion': tipo, 'state': state, 'rate_usd': 1.0})

    def _make_lot(self, name, volumen=5.0, guia=None):
        vals = {
            'name': name, 'product_id': self.product.id,
            'volumen_m3': volumen}
        if guia is not None:
            vals['guia_processing_id'] = guia.id
        return self.StockLot.create(vals)


    def _make_line(self, guia, lot_name, **over):
        subp = self.Subproducto.search([('code', '=', 'B1SUB')], limit=1)
        if not subp:
            subp = self.Subproducto.create(
                {'name': 'B1 Subproducto', 'code': 'B1SUB'})
        vals = {
            'processing_id': guia.id, 'lot_name': lot_name,
            'product_id': self.product.id, 'subproducto_id': subp.id,
            'pieces': 10, 'espesor_mm': 25.0, 'ancho_mm': 100.0,
            'largo_m': 2.0, 'espesor_nominal_mm': 25.0,
            'ancho_nominal_mm': 100.0, 'vol_purchase_m3': 5.0,
            'vol_shipment_m3': 5.0, 'vol_physical_m3': 5.0,
            'technical_validation': 'approved'}
        vals.update(over)
        return self.Line.create(vals)

    def _done_picking(self, lot, qty=5.0, direction='in', guia=None,
                      with_fk=False, company=None, origin=None):
        """Crea un picking `done` con un move/move_line vinculado al lote.

        `direction='in'`: supplier→internal (ingreso de producción).
        `direction='out'`: internal→supplier (egreso/retorno).
        """
        if direction == 'in':
            pt = self.env.ref('stock.picking_type_in')
            src, dest = self.supplier_loc, self.internal
        else:
            pt = self.warehouse.out_type_id or self.env.ref(
                'stock.picking_type_out')
            src, dest = self.internal, self.supplier_loc
        vals = {
            'picking_type_id': pt.id, 'partner_id': self.partner.id,
            'location_id': src.id, 'location_dest_id': dest.id,
            'origin': origin if origin is not None else
                (guia.name if guia else 'B1-ORIGIN'),
        }
        if company is not None:
            vals['company_id'] = company.id
        if with_fk and guia is not None:
            vals['guia_processing_id'] = guia.id
        picking = self.Picking.create(vals)
        move = self.Move.create({
            'name': 'B1 move', 'product_id': self.product.id,
            'product_uom_qty': qty, 'product_uom': self.uom.id,
            'picking_id': picking.id,
            'location_id': src.id, 'location_dest_id': dest.id,
            'company_id': (company or self.company).id})
        picking.action_confirm()
        picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': move.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'lot_id': lot.id, 'quantity': qty,
            'product_uom_id': self.uom.id,
            'location_id': src.id, 'location_dest_id': dest.id,
            'picked': True})
        move.picked = True
        move._action_done()
        picking.write({'state': 'done'})
        return picking, move

    def _lot_qty_internal(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id), ('location_id', '=', self.internal.id)])
        return sum(quants.mapped('quantity'))

    # ── T-B1-01 — FK fuerte sin retorno: bloquea ─────────────────────────
    def test_t_b1_01_fk_sin_retorno_bloquea(self):
        guia = self._make_guia('B1-01')
        lot = self._make_lot('B1-01-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking, move = self._done_picking(
            lot, guia=guia, with_fk=True, origin='EMB-B1-01')
        self.assertEqual(picking.state, 'done')

        info = guia._b1_revalidation_physical_effect_info()
        self.assertTrue(info['block_revalidation'])
        self.assertEqual(info['evidence_type'], 'fk')
        self.assertIn(picking, info['pickings'])

        self._make_line(guia, 'B1-01-LOT')
        picking_before = self.Picking.search_count([])
        move_before = self.Move.search_count([])
        quant_before = self.Quant.search_count([])

        with self.assertRaises(UserError) as ctx:
            guia.action_validate()
        self.assertIn('no compensado', str(ctx.exception))

        self.assertEqual(
            self.Picking.search_count(
                [('guia_processing_id', '=', guia.id)]), 1,
            'No debe crearse un segundo picking de ingreso')
        self.assertEqual(self.Picking.search_count([]), picking_before)
        self.assertEqual(self.Move.search_count([]), move_before)
        self.assertEqual(self.Quant.search_count([]), quant_before)

    # ── T-B1-02 — FK fuerte compensado: permite ──────────────────────────
    def test_t_b1_02_fk_compensado_permite(self):
        guia = self._make_guia('B1-02')
        lot = self._make_lot('B1-02-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking, move = self._done_picking(
            lot, guia=guia, with_fk=True, origin='EMB-B1-02')

        # Retorno nativo G3 (done) que compensa el ingreso.
        returned = guia._reverse_production_picking(picking)
        self.assertTrue(returned, 'Debe generarse retorno nativo G3')
        self.assertEqual(returned.state, 'done')

        info = guia._b1_revalidation_physical_effect_info()
        self.assertFalse(
            info['block_revalidation'],
            'Con retorno nativo done la revalidación física es legítima')

    # ── T-B1-03 — Histórico inequívoco: bloquea (deriva a H1) ────────────
    def test_t_b1_03_historico_inequivoco_bloquea(self):
        guia = self._make_guia('B1-03')
        lot = self._make_lot('B1-03-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        # Ingreso histórico: sin FK, lot ligado a la guía, supplier→internal.
        self._done_picking(lot, guia=guia, with_fk=False, origin='EMB-B1-03')

        info = guia._b1_revalidation_physical_effect_info()
        self.assertTrue(info['block_revalidation'])
        self.assertEqual(info['evidence_type'], 'historical')
        self.assertIn('Reversión histórica asistida', info['message'])
        self.assertTrue(info['moves'])

    # ── T-B1-04 — Histórico ambiguo: NO bloquea ──────────────────────────
    def test_t_b1_04_historico_ambiguo_no_bloquea(self):
        # Caso A: el lote de la guía aparece SOLO en un egreso/retorno.
        guia = self._make_guia('B1-04A')
        lot = self._make_lot('B1-04A-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(
            lot, guia=guia, direction='out', origin='Return of B1-04A')
        info = guia._b1_revalidation_physical_effect_info()
        self.assertFalse(info['block_revalidation'])

        # Caso B: lote compartido con otra guía → ambiguo, no bloquea.
        guia_b = self._make_guia('B1-04B')
        lot_b = self._make_lot('B1-04B-LOT', 5.0, guia=guia_b)
        guia_b.lot_ids = [(6, 0, [lot_b.id])]
        other = self._make_guia('B1-04B-OTHER')
        other.lot_ids = [(6, 0, [lot_b.id])]
        self._done_picking(
            lot_b, guia=guia_b, with_fk=False, origin='EMB-B1-04B')

        info_b = guia_b._b1_revalidation_physical_effect_info()
        self.assertFalse(
            info_b['block_revalidation'],
            'El lote compartido con otra guía es evidencia ambigua')
        self.assertEqual(info_b['evidence_type'], 'ambiguous')


    # ── T-B1-05 — No bloqueo documental ──────────────────────────────────
    def test_t_b1_05_no_bloquea_documental(self):
        import base64
        guia = self._make_guia('B1-05', state='validated')
        lot = self._make_lot('B1-05-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(lot, guia=guia, with_fk=True, origin='EMB-B1-05')
        guia.write({
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx'})

        picking_before = self.Picking.search_count([])
        quant_before = self.Quant.search_count([])
        packing = {'lineas': [{
            'Codigo Interno': 'X100', 'N° LOTE': 'B1-05-LOT',
            'Cantidad': 10, 'Volumen': 5.0, 'Espesor': 25, 'Ancho': 100,
            'Largo': 2.0, 'product_name': 'Madera Test'}]}

        guia.with_context(force_packing_data=packing).action_verify_data()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'verified',
                         'La corrección documental sigue permitida')
        self.assertEqual(self.Picking.search_count([]), picking_before)
        self.assertEqual(self.Quant.search_count([]), quant_before)
        # La evidencia física sigue presente → el guard seguía disponible.
        self.assertTrue(
            guia._b1_revalidation_physical_effect_info()['block_revalidation'])

    # ── T-B1-06 — Granel/SV excluido ─────────────────────────────────────
    def test_t_b1_06_granel_excluido(self):
        guia = self._make_guia('B1-06', tipo='granel', state='validated')
        lot = self._make_lot('B1-06-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(lot, guia=guia, with_fk=True, origin='EMB-B1-06')

        info = guia._b1_revalidation_physical_effect_info()
        self.assertFalse(
            info['block_revalidation'], 'Granel/SV está fuera de alcance')
        self.assertEqual(info['evidence_type'], 'none')

    # ── T-B1-07 — BT-04 excluido (ruta conservada) ───────────────────────
    def test_t_b1_07_bt04_excluido(self):
        guia = self._make_guia('B1-07', tipo='service', state='verified')
        source = self._make_lot('B1-07-SRC', 10.0)
        self.Quant._update_available_quantity(
            self.product, self.internal, 10.0, lot_id=source)
        guia.source_lot_ids = [(6, 0, [source.id])]

        consumption = guia._get_or_create_consumption_picking()
        self.assertTrue(consumption, 'La ruta BT-04 debe conservarse')
        self.assertEqual(guia.consumption_picking_id, consumption)
        # Idempotencia BT-04 intacta.
        self.assertEqual(
            guia._get_or_create_consumption_picking(), consumption)
        # El consumo (egreso) no se interpreta como evidencia de ingreso.
        info = guia._b1_revalidation_physical_effect_info()
        self.assertFalse(info['block_revalidation'])
        self.assertEqual(info['evidence_type'], 'none')


    # ── T-B1-08 — Rutas indirectas alcanzan el mismo guard ───────────────
    def test_t_b1_08_rutas_indirectas(self):
        guia = self._make_guia('B1-08')
        lot = self._make_lot('B1-08-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        # Origen textual distinto: el guard NO depende de `origin`.
        self._done_picking(lot, guia=guia, with_fk=True, origin='EMB-B1-08')
        self._make_line(guia, 'B1-08-LOT')

        with self.assertRaises(UserError):
            guia.do_full_processing()
        with self.assertRaises(UserError):
            guia.action_validate()
        with self.assertRaises(UserError):
            guia.action_process_from_staging()
        # Motor único (fuente de verdad de creación de picking/moves).
        with self.assertRaises(UserError):
            guia._get_or_create_picking_unified()

    # ── T-B1-09 — Compensación por move (sin picking.return_id) ──────────
    def test_t_b1_09_compensacion_por_move(self):
        guia = self._make_guia('B1-09')
        lot = self._make_lot('B1-09-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        picking, move = self._done_picking(
            lot, guia=guia, with_fk=True, origin='EMB-B1-09')

        # Retorno nativo a nivel de MOVE: origin_returned_move_id, done,
        # SIN setear picking.return_id.
        ret_picking = self.Picking.create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'partner_id': self.partner.id,
            'location_id': self.internal.id,
            'location_dest_id': self.supplier_loc.id,
            'origin': 'Return of %s' % picking.name})
        ret_move = self.Move.create({
            'name': 'Return of %s' % move.name,
            'product_id': self.product.id, 'product_uom_qty': 5.0,
            'product_uom': self.uom.id, 'picking_id': ret_picking.id,
            'location_id': self.internal.id,
            'location_dest_id': self.supplier_loc.id,
            'origin_returned_move_id': move.id})
        ret_picking.action_confirm()
        ret_picking.move_line_ids.filtered(lambda ml: not ml.lot_id).unlink()
        self.MoveLine.create({
            'move_id': ret_move.id, 'picking_id': ret_picking.id,
            'product_id': self.product.id, 'lot_id': lot.id, 'quantity': 5.0,
            'product_uom_id': self.uom.id,
            'location_id': self.internal.id,
            'location_dest_id': self.supplier_loc.id, 'picked': True})
        ret_move.picked = True
        ret_move._action_done()
        ret_picking.write({'state': 'done'})
        self.assertFalse(ret_picking.return_id)

        move.invalidate_recordset()
        self.assertTrue(
            guia._b1_move_is_compensated(move),
            'La compensación por origin_returned_move_id debe reconocerse')
        self.assertFalse(
            guia._b1_revalidation_physical_effect_info()['block_revalidation'])


    # ── T-B1-10 — Firma/auditoría: sin efectos al bloquear ───────────────
    def test_t_b1_10_sin_firma_ni_efectos(self):
        guia = self._make_guia('B1-10')
        lot = self._make_lot('B1-10-LOT', 5.0, guia=guia)
        guia.lot_ids = [(6, 0, [lot.id])]
        self._done_picking(lot, guia=guia, with_fk=True, origin='EMB-B1-10')
        self._make_line(guia, 'B1-10-LOT')

        sig_query = [('guia_processing_id', '=', guia.id),
                     ('action_type', '=', 'validation_signature')]
        sig_before = self.Audit.search_count(sig_query)
        picking_before = self.Picking.search_count([])
        move_before = self.Move.search_count([])
        quant_before = self.Quant.search_count([])

        with self.assertRaises(UserError):
            guia.action_validate()

        self.assertEqual(sig_before, 0)
        self.assertEqual(self.Audit.search_count(sig_query), 0)
        self.assertEqual(self.Picking.search_count([]), picking_before)
        self.assertEqual(self.Move.search_count([]), move_before)
        self.assertEqual(self.Quant.search_count([]), quant_before)

    # ── T-B1-11 — No uso de `origin` como llave ──────────────────────────
    def test_t_b1_11_no_usa_origin(self):
        # Sin vínculo FK ni lote ligado: `origin` textual no determina bloqueo.
        guia = self._make_guia('B1-11')
        lot_free = self._make_lot('B1-11-FREE', 5.0)  # sin guia_processing_id
        self._done_picking(
            lot_free, guia=guia, with_fk=False, origin=guia.name)
        self.assertFalse(
            guia._b1_revalidation_physical_effect_info()['block_revalidation'],
            'Sin FK ni lote ligado, el origin textual no debe bloquear')

        # Con FK y origin prefijado histórico, sí bloquea (llave fuerte).
        guia2 = self._make_guia('B1-11B')
        lot2 = self._make_lot('B1-11B-LOT', 5.0, guia=guia2)
        guia2.lot_ids = [(6, 0, [lot2.id])]
        self._done_picking(
            lot2, guia=guia2, with_fk=True, origin='REVERTIDO-B1-11B')
        self.assertTrue(
            guia2._b1_revalidation_physical_effect_info()['block_revalidation'])

