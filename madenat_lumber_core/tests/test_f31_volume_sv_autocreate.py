# -*- coding: utf-8 -*-
"""F3.1 — Alta automática de etiquetas SV desde guías de volumen validadas.

Cubre T-F3.1-01 .. T-F3.1-13. Los tests activan el flujo PÚBLICO real
(``action_validate()`` sobre una guía ``tipo_recepcion='granel'``); nunca
construyen la etiqueta SV a mano para el alta.

Diseño implementado: el lote físico de cada línea elegible ES la etiqueta SV
del ingreso, con idempotencia por el vínculo ``volume_source_line_id`` y sin
movimientos de stock adicionales.

Datos aislados (TransactionCase): no se toca ninguna guía, lote ni secuencia
histórica.
"""

import base64

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'sv', 'f31')
class TestF31VolumeSvAutoCreate(TransactionCase):
    """Alta automática de etiquetas SV (una por línea elegible)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.AuditLog = cls.env['madenat.audit.log']

        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id

        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.products = cls.env['product.product']
        for code in ('F31-A', 'F31-B', 'F31-C'):
            cls.products |= cls.env['product.product'].create({
                'name': 'F31 Product %s' % code,
                'default_code': code,
                'is_storable': True,
                'tracking': 'lot',
                'uom_id': uom_m3.id,
                'uom_po_id': uom_m3.id,
            })

        cls.partner = cls.env['res.partner'].create({'name': 'F31 Partner'})
        cls.subproducto = cls.env['madenat.subproducto'].create({
            'name': 'F31 Subproducto', 'code': 'F31'})

        # Perfil funcional mínimo para operar el ledger SV en las pruebas.
        for xmlid in ('madenat_lumber_core.group_madenat_auditoria',
                      'madenat_lumber_core.group_madenat_contabilidad'):
            cls.env.user.sudo().write({
                'groups_id': [(4, cls.env.ref(xmlid).id)]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _make_granel_guia(self, name):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'granel',
            'rate_usd': 800.0,
            'date_emission': '2026-09-24',
            'guide_pdf_file': base64.b64encode(b'%PDF-fake'),
        })

    def _make_line(self, guia, product, volume, pieces=1):
        line = self.Line.create({
            'processing_id': guia.id,
            'lot_name': 'GRANEL',
            'sku_original': 'GRANEL',
            'product_name_original': 'Recepción a granel',
            'product_id': product.id,
            'subproducto_id': self.subproducto.id,
            'pieces': pieces,
            'espesor_nominal_mm': 0.0,
            'technical_validation': 'approved',
        })
        # El volumen de la guía es el volumen operativo de la línea (granel).
        line.write({
            'vol_purchase_m3': volume,
            'vol_shipment_m3': volume,
            'vol_physical_m3': volume,
        })
        return line

    def _validate(self, guia):
        guia.write({'state': 'verified'})
        guia.action_validate()
        return guia

    def _physical_counts(self):
        """Conteo de entidades físicas/valoración creadas en la transacción."""
        models = ['stock.picking', 'stock.move', 'stock.move.line',
                  'stock.quant', 'stock.valuation.layer']
        counts = {}
        for model_name in models:
            model = self.env.get(model_name)
            if model is not None:
                counts[model_name] = model.search_count([])
        return counts

    def _user_with(self, login, group_xmlids):
        groups = [(6, 0, [self.env.ref('base.group_user').id]
                   + [self.env.ref(x).id for x in group_xmlids])]
        return self.env['res.users'].create({
            'name': login, 'login': login, 'groups_id': groups})

    # ── T-F3.1-01 ─────────────────────────────────────────────────────────
    def test_01_una_linea_genera_una_sv(self):
        guia = self._make_granel_guia('F31-01')
        self._make_line(guia, self.products[0], 18.500)
        self._validate(guia)
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(len(guia.volume_lot_ids), 1)
        self.assertEqual(guia.volume_lot_ids.lot_flow_type, 'volume')

    # ── T-F3.1-02 ─────────────────────────────────────────────────────────
    def test_02_varias_lineas_generan_varias_sv(self):
        guia = self._make_granel_guia('F31-02')
        self._make_line(guia, self.products[0], 10.0)
        self._make_line(guia, self.products[1], 12.5)
        self._make_line(guia, self.products[2], 8.0)
        self._validate(guia)
        self.assertEqual(len(guia.volume_lot_ids), 3)
        self.assertEqual(
            set(guia.volume_lot_ids.mapped('product_id')), set(self.products))
        # Una etiqueta SV por línea (1:1 por el vínculo de línea).
        self.assertEqual(
            len(set(guia.volume_lot_ids.mapped('volume_source_line_id'))), 3)

    # ── T-F3.1-03 ─────────────────────────────────────────────────────────
    def test_03_volumen_inicial_es_el_de_la_guia(self):
        guia = self._make_granel_guia('F31-03')
        line = self._make_line(guia, self.products[0], 18.500)
        self._validate(guia)
        lot = guia.volume_lot_ids
        self.assertAlmostEqual(lot.volume_purchase_m3, 18.500, places=3)
        self.assertAlmostEqual(lot.sv_original_volume_m3, 18.500, places=3)
        self.assertAlmostEqual(lot.sv_available_m3, 18.500, places=3)
        self.assertEqual(lot, line.volume_lot_ids)

    # ── T-F3.1-04 ─────────────────────────────────────────────────────────
    def test_04_vinculo_guia_producto_compania_patio(self):
        guia = self._make_granel_guia('F31-04')
        self._make_line(guia, self.products[0], 5.0)
        self._validate(guia)
        lot = guia.volume_lot_ids
        self.assertEqual(lot.volume_source_guia_id, guia)
        self.assertEqual(lot.guia_processing_id, guia)
        self.assertEqual(lot.product_id, self.products[0])
        self.assertEqual(lot.company_id, self.company)
        self.assertEqual(lot.location_id, self.location)
        self.assertTrue(lot.volume_source_line_id)

    # ── T-F3.1-05 ─────────────────────────────────────────────────────────
    def test_05_etiqueta_usa_secuencia_sv(self):
        guia = self._make_granel_guia('F31-05')
        self._make_line(guia, self.products[0], 4.0)
        self._validate(guia)
        lot = guia.volume_lot_ids
        self.assertRegex(lot.name, r'^SV[0-9]{11}$')
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'madenat.volume.lot')])
        self.assertTrue(sequence, 'Debe existir la secuencia madenat.volume.lot')

    # ── T-F3.1-06 ─────────────────────────────────────────────────────────
    def test_06_reproceso_no_duplica(self):
        guia = self._make_granel_guia('F31-06')
        self._make_line(guia, self.products[0], 7.0)
        guia.write({'state': 'verified'})
        guia.do_full_processing()
        first = guia.volume_lot_ids
        self.assertEqual(len(first), 1)
        # Reproceso: recupera la etiqueta existente, no crea una segunda.
        guia.do_full_processing()
        self.assertEqual(guia.volume_lot_ids, first)
        # Validación completa posterior: sigue habiendo una sola SV.
        guia.write({'state': 'verified'})
        guia.action_validate()
        self.assertEqual(len(guia.volume_lot_ids), 1)
        self.assertEqual(guia.volume_lot_ids, first)

    # ── T-F3.1-07 ─────────────────────────────────────────────────────────
    def test_07_linea_invalida_no_genera_sv_y_deja_aviso(self):
        guia = self._make_granel_guia('F31-07')
        self._make_line(guia, self.products[0], 6.0)
        self._make_line(guia, self.products[1], 0.0)  # volumen no positivo
        self._validate(guia)
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(len(guia.volume_lot_ids), 1)
        self.assertEqual(guia.volume_lot_ids.product_id, self.products[0])
        warned = any(
            'no generaron etiqueta SV' in (message.body or '')
            for message in guia.message_ids)
        self.assertTrue(warned, 'Debe quedar una advertencia trazable')

    # ── T-F3.1-08 ─────────────────────────────────────────────────────────
    def test_08_sin_lineas_elegibles_no_crea_nada(self):
        guia = self._make_granel_guia('F31-08')
        self._make_line(guia, self.products[0], 0.0)
        guia.write({'state': 'verified'})
        with self.assertRaises(ValidationError):
            guia.action_validate()
        self.assertNotEqual(guia.state, 'validated')
        self.assertFalse(guia.volume_lot_ids)
        self.assertFalse(self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'validation_signature')]))

    # ── T-F3.1-09 ─────────────────────────────────────────────────────────
    def test_09_sv_de_otra_guia_permanece_inalterada(self):
        other = self._make_granel_guia('F31-09-B')
        self._make_line(other, self.products[1], 9.0)
        self._validate(other)
        other_lot = other.volume_lot_ids
        name_before = other_lot.name
        volume_before = other_lot.volume_purchase_m3

        guia = self._make_granel_guia('F31-09-A')
        self._make_line(guia, self.products[0], 3.0)
        self._validate(guia)

        other_lot.invalidate_recordset()
        self.assertEqual(other_lot.name, name_before)
        self.assertAlmostEqual(
            other_lot.volume_purchase_m3, volume_before, places=3)
        self.assertEqual(other_lot.volume_source_guia_id, other)

    # ── T-F3.1-10 ─────────────────────────────────────────────────────────
    def test_10_alta_sv_no_crea_movimientos_de_stock(self):
        guia = self._make_granel_guia('F31-10')
        self._make_line(guia, self.products[0], 4.0)
        guia.write({'state': 'verified'})
        line = guia._volume_eligible_lines()
        before = self._physical_counts()
        lot = guia._get_or_create_volume_sv_lot(
            item=line,
            product=line.product_id,
            vol_purchase=line.vol_purchase_m3,
            vol_shipment=line.vol_shipment_m3,
            lot_dims={
                'espesor_mm': 0.0, 'ancho_mm': 0.0, 'largo_m': 0.0,
                'espesor_nominal_mm': 0.0, 'ancho_nominal_mm': 0.0,
                'note': '', 'ref': ''},
            precio_usd=0.0,
            purchase_order=None,
        )
        after = self._physical_counts()
        self.assertEqual(
            before, after,
            'El alta de la etiqueta SV no debe crear movimientos de stock')
        self.assertEqual(lot.lot_flow_type, 'volume')
        self.assertEqual(line.volume_lot_ids, lot)

    # ── T-F3.1-11 ─────────────────────────────────────────────────────────
    def test_11_operaciones_visualiza_las_etiquetas_sv(self):
        guia = self._make_granel_guia('F31-11')
        self._make_line(guia, self.products[0], 5.0)
        self._validate(guia)
        lot = guia.volume_lot_ids
        user = self._user_with(
            'f31_ops_%s' % lot.id,
            ['madenat_lumber_core.group_madenat_operaciones'])
        visible = self.StockLot.with_user(user).search([('id', '=', lot.id)])
        self.assertEqual(visible, lot)
        self.assertEqual(visible.lot_flow_type, 'volume')
        self.assertTrue(self.env.ref(
            'madenat_lumber_core.action_madenat_sv_lots'))

    # ── T-F3.1-12 ─────────────────────────────────────────────────────────
    def test_12_contabilidad_lee_pero_no_muta_sv(self):
        guia = self._make_granel_guia('F31-12')
        self._make_line(guia, self.products[0], 5.0)
        self._validate(guia)
        lot = guia.volume_lot_ids
        user = self._user_with(
            'f31_cont_%s' % lot.id,
            ['madenat_lumber_core.group_madenat_contabilidad'])
        readonly_lot = self.StockLot.with_user(user).search(
            [('id', '=', lot.id)])
        self.assertEqual(readonly_lot, lot)
        # La mutación directa de una etiqueta SV se bloquea server-side.
        with self.assertRaises(ValidationError):
            readonly_lot.write({'volumen_m3': 1.0})

    # ── T-F3.1-13 ─────────────────────────────────────────────────────────
    def test_13_rebaja_conserva_saldo_documental_y_auditoria(self):
        guia = self._make_granel_guia('F31-13')
        self._make_line(guia, self.products[0], 18.500)
        self._validate(guia)
        lot = guia.volume_lot_ids
        self.assertAlmostEqual(lot.sv_original_volume_m3, 18.500, places=3)

        operation = self.env['madenat.sv.operation'].create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 3.0,
            'reason': 'F31 rebaja de prueba',
        })
        operation.action_apply()
        lot.invalidate_recordset()
        # El volumen documental inicial NO se muta; solo baja el saldo.
        self.assertAlmostEqual(lot.sv_original_volume_m3, 18.500, places=3)
        self.assertAlmostEqual(lot.sv_available_m3, 15.500, places=3)
        self.assertIn(operation, lot.sv_operation_ids)
        self.assertEqual(operation.state, 'applied')
        self.assertTrue(self.AuditLog.search([
            ('action_type', '=', 'sv_operation')]))
