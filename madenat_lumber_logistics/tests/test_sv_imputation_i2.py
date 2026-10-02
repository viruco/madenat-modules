# -*- coding: utf-8 -*-
"""I2 — Imputación DOCUMENTAL SV (CANON/19 v1.6.0 §4/§5/§6/§7/§16; AD-91).

Cobertura T-I2-01..T-I2-12. Datos 100 % aislados (TransactionCase). Se verifica
que I2 **no** toca stock y que el saldo documental es una magnitud separada.
"""
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationI2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'I2 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'I2 Supplier', 'is_company': True})
        cls.processor = cls.env['res.partner'].create({
            'name': 'I2 Planta', 'is_company': True, 'is_processor': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Operation = cls.env['madenat.sv.operation']

        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('i2_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk('i2_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_ger = _mk('i2_ger', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_gerencia'])
        cls.user_aud = _mk('i2_aud', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_auditoria'])
        cls.user_plain = _mk('i2_plain', ['base.group_user'])

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _make_guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'date_emission': '2026-10-02'})

    def _make_etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _make_sv(self, guia, label, nominal):
        return self.StockLot.sudo().create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})

    def _make_imputation(self, guia, lines, reason=None, key=None):
        vals = {'guia_processing_id': guia.id, 'reason': reason}
        if key:
            vals['documentary_key'] = key
        imp = self.Imputation.sudo().create(vals)
        for etiqueta, allocs in lines:
            line = self.ImputationLine.sudo().create({
                'imputation_id': imp.id,
                'processed_lot_id': etiqueta.id,
                'nominal_volume_m3': etiqueta.volume_purchase_m3,
            })
            for sv, vol in allocs:
                self.SvLine.sudo().create({
                    'imputation_id': imp.id,
                    'imputation_line_id': line.id,
                    'sv_lot_id': sv.id,
                    'imputed_volume_m3': vol,
                })
        return imp

    def _stock_snapshot(self):
        quants = self.env['stock.quant'].search(
            [('company_id', '=', self.company.id)])
        return {
            'quant_qty': round(sum(quants.mapped('quantity')), 3),
            'reserved': round(sum(quants.mapped('reserved_quantity')), 3),
            'pickings': self.env['stock.picking'].search_count(
                [('company_id', '=', self.company.id)]),
            'moves': self.env['stock.move'].search_count(
                [('company_id', '=', self.company.id)]),
            'move_lines': self.env['stock.move.line'].search_count(
                [('company_id', '=', self.company.id)]),
        }

    # ── T-I2-01 ──────────────────────────────────────────────────────────
    def test_t_i2_01_etiqueta_distribuye_varios_sv(self):
        """Etiqueta nominal 10 → SV-A 3 + SV-B 7: aplica correctamente."""
        guia = self._make_guia('I2-T01')
        etiqueta = self._make_etiqueta(guia, 'I2-E01', 10.0)
        sv_a = self._make_sv(guia, 'SV00000000101', 100.0)
        sv_b = self._make_sv(guia, 'SV00000000102', 100.0)
        imp = self._make_imputation(guia, [(etiqueta, [(sv_a, 3.0),
                                                       (sv_b, 7.0)])])
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_documental_imputed_m3(etiqueta), 10.0, 3)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv_a), 3.0, 3)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv_b), 7.0, 3)

    # ── T-I2-02 ──────────────────────────────────────────────────────────
    def test_t_i2_02_techo_duro_etiqueta_rechaza(self):
        """Superar 10 (6+5) ⇒ rechazo DURO server-side."""
        guia = self._make_guia('I2-T02')
        etiqueta = self._make_etiqueta(guia, 'I2-E02', 10.0)
        sv = self._make_sv(guia, 'SV00000000201', 100.0)
        imp1 = self._make_imputation(guia, [(etiqueta, [(sv, 6.0)])])
        imp1.with_user(self.user_oper).action_apply()
        self.assertEqual(imp1.state, 'applied')
        imp2 = self._make_imputation(guia, [(etiqueta, [(sv, 5.0)])])
        with self.assertRaises(UserError):
            imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp2.state, 'draft')

    # ── T-I2-03 ──────────────────────────────────────────────────────────
    def test_t_i2_03_varias_etiquetas_un_sv(self):
        """Varias etiquetas de una guía contra un mismo SV: aplica."""
        guia = self._make_guia('I2-T03')
        e1 = self._make_etiqueta(guia, 'I2-E03a', 5.0)
        e2 = self._make_etiqueta(guia, 'I2-E03b', 5.0)
        sv = self._make_sv(guia, 'SV00000000301', 100.0)
        imp = self._make_imputation(guia, [(e1, [(sv, 5.0)]),
                                           (e2, [(sv, 5.0)])])
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 10.0, 3)

    # ── T-I2-04 ──────────────────────────────────────────────────────────
    def test_t_i2_04_un_sv_varias_guias(self):
        """Un SV puede intervenir en imputaciones de varias guías."""
        g1 = self._make_guia('I2-T04a')
        g2 = self._make_guia('I2-T04b')
        e1 = self._make_etiqueta(g1, 'I2-E04a', 4.0)
        e2 = self._make_etiqueta(g2, 'I2-E04b', 6.0)
        sv = self._make_sv(g1, 'SV00000000401', 100.0)
        imp1 = self._make_imputation(g1, [(e1, [(sv, 4.0)])])
        imp2 = self._make_imputation(g2, [(e2, [(sv, 6.0)])])
        imp1.with_user(self.user_oper).action_apply()
        imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp1.state, 'applied')
        self.assertEqual(imp2.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 10.0, 3)

    # ── T-I2-05 ──────────────────────────────────────────────────────────
    def test_t_i2_05_exceso_sv_side_blando(self):
        """Exceso SV-side: exige motivo y registra deviation, pero aplica."""
        guia = self._make_guia('I2-T05')
        etiqueta = self._make_etiqueta(guia, 'I2-E05', 20.0)
        sv = self._make_sv(guia, 'SV00000000501', 5.0)
        imp = self._make_imputation(guia, [(etiqueta, [(sv, 10.0)])])
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()  # sin motivo
        imp.reason = 'Exceso autorizado por Jefatura'
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        deviations = self.AuditLog.search([
            ('action_type', '=', 'deviation'),
            ('description', 'like', 'I2-SV-EXCESS')])
        self.assertEqual(len(deviations), 1)

    # ── T-I2-06 ──────────────────────────────────────────────────────────
    def test_t_i2_06_etiqueta_sin_sv_candidato(self):
        """Sin SV candidato: permite aplicar con motivo; no mueve stock."""
        guia = self._make_guia('I2-T06')
        etiqueta = self._make_etiqueta(guia, 'I2-E06', 8.0)
        imp = self._make_imputation(guia, [(etiqueta, [])])
        before = self._stock_snapshot()
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()  # sin motivo
        imp.reason = 'Sin SV candidato; se deja constancia documental'
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertIn('NO_SV_CANDIDATE', imp.deviation_flags or '')
        self.assertEqual(self._stock_snapshot(), before)

    # ── T-I2-07 ──────────────────────────────────────────────────────────
    def test_t_i2_07_idempotencia_reintento(self):
        """Reintento: no duplica cabecera, líneas, auditorías ni saldo."""
        guia = self._make_guia('I2-T07')
        etiqueta = self._make_etiqueta(guia, 'I2-E07', 10.0)
        sv = self._make_sv(guia, 'SV00000000701', 100.0)
        imp = self._make_imputation(
            guia, [(etiqueta, [(sv, 10.0)])], key='IMP-IDEMPOTENT-I2-T07')
        imp.with_user(self.user_oper).action_apply()
        imp.with_user(self.user_oper).action_apply()
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(
            self.Imputation.search_count(
                [('documentary_key', '=', 'IMP-IDEMPOTENT-I2-T07')]), 1)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)
        audits = self.AuditLog.search([
            ('action_type', '=', 'imputation'),
            ('batch_id', '=', imp.documentary_key)])
        self.assertEqual(len(audits), 1)
        self.assertAlmostEqual(
            self.Imputation._i2_lot_documental_imputed_m3(etiqueta), 10.0, 3)

    # ── T-I2-08 ──────────────────────────────────────────────────────────
    def test_t_i2_08_reversa_historia_intacta(self):
        """Reversa: estado reversed; historia intacta; saldo vuelve."""
        guia = self._make_guia('I2-T08')
        etiqueta = self._make_etiqueta(guia, 'I2-E08', 10.0)
        sv = self._make_sv(guia, 'SV00000000801', 100.0)
        imp = self._make_imputation(guia, [(etiqueta, [(sv, 10.0)])])
        imp.with_user(self.user_oper).action_apply()
        self.assertAlmostEqual(
            self.Imputation._i2_lot_documental_imputed_m3(etiqueta), 10.0, 3)
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_documental_imputed_m3(etiqueta), 0.0, 3)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertTrue(self.AuditLog.search([
            ('action_type', '=', 'imputation_reverse'),
            ('batch_id', '=', imp.documentary_key)]))

    # ── T-I2-09 ──────────────────────────────────────────────────────────
    def test_t_i2_09_orden_inverso_etiqueta_luego_sv(self):
        """Etiqueta primero, SV después: permite pendiente y aplicar luego."""
        guia = self._make_guia('I2-T09')
        etiqueta = self._make_etiqueta(guia, 'I2-E09', 10.0)
        imp = self._make_imputation(guia, [(etiqueta, [])])
        imp.with_user(self.user_oper).action_pending()
        self.assertEqual(imp.state, 'pending')
        sv = self._make_sv(guia, 'SV00000000901', 100.0)
        self.SvLine.sudo().create({
            'imputation_id': imp.id,
            'imputation_line_id': imp.line_ids.id,
            'sv_lot_id': sv.id,
            'imputed_volume_m3': 10.0,
        })
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 10.0, 3)

    # ── T-I2-10 ──────────────────────────────────────────────────────────
    def test_t_i2_10_permisos(self):
        """Operaciones/Jefatura aplican; Jefatura/Gerencia revierten."""
        guia = self._make_guia('I2-T10')
        etiqueta = self._make_etiqueta(guia, 'I2-E10', 10.0)
        sv = self._make_sv(guia, 'SV00000001001', 100.0)
        imp = self._make_imputation(guia, [(etiqueta, [(sv, 10.0)])])
        with self.assertRaises(AccessError):
            imp.with_user(self.user_plain).action_apply()
        with self.assertRaises(AccessError):
            imp.with_user(self.user_aud).action_apply()
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(AccessError):
            imp.with_user(self.user_oper).action_reverse()
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        imp2 = self._make_imputation(guia, [(etiqueta, [(sv, 10.0)])])
        imp2.with_user(self.user_jef).action_apply()
        self.assertEqual(imp2.state, 'applied')
        imp2.with_user(self.user_ger).action_reverse()
        self.assertEqual(imp2.state, 'reversed')

    # ── T-I2-11 ──────────────────────────────────────────────────────────
    def test_t_i2_11_no_stock(self):
        """Quants, pickings, moves y reservas idénticos antes/después."""
        guia = self._make_guia('I2-T11')
        etiqueta = self._make_etiqueta(guia, 'I2-E11', 10.0)
        sv = self._make_sv(guia, 'SV00000001101', 100.0)
        before = self._stock_snapshot()
        ledger_before = self.Operation.search_count([('lot_id', '=', sv.id)])
        imp = self._make_imputation(guia, [(etiqueta, [(sv, 10.0)])])
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(self._stock_snapshot(), before)
        self.assertEqual(
            self.Operation.search_count([('lot_id', '=', sv.id)]),
            ledger_before)
        self.assertEqual(
            self.Operation.search_count([('action_type', '=', 'imputacion')]),
            0)

    # ── T-I2-12 ──────────────────────────────────────────────────────────
    def test_t_i2_12_concurrencia_mismo_sv(self):
        """Concurrencia sobre el mismo SV: fallo controlado, sin parciales."""
        g1 = self._make_guia('I2-T12a')
        g2 = self._make_guia('I2-T12b')
        e1 = self._make_etiqueta(g1, 'I2-E12a', 10.0)
        e2 = self._make_etiqueta(g2, 'I2-E12b', 10.0)
        sv = self._make_sv(g1, 'SV00000001201', 100.0)
        _imp1 = self._make_imputation(g1, [(e1, [(sv, 5.0)])])
        imp2 = self._make_imputation(g2, [(e2, [(sv, 5.0)])])
        cr = self.env.registry.cursor()
        try:
            cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', (2, sv.id))
            with self.assertRaises(UserError):
                imp2.with_user(self.user_oper).action_apply()
            self.assertEqual(imp2.state, 'draft')
            self.assertEqual(len(imp2.line_ids), 1)
        finally:
            cr.close()
        imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp2.state, 'applied')

    # ── T-I2-13 (extra: smoke del asistente / FASE 3) ────────────────────
    def test_t_i2_13_wizard_aplica(self):
        """El asistente construye y aplica la imputación documental."""
        guia = self._make_guia('I2-T13')
        etiqueta = self._make_etiqueta(guia, 'I2-E13', 10.0)
        sv = self._make_sv(guia, 'SV00000001301', 100.0)
        Wizard = self.env['madenat.sv.imputation.wizard']
        wiz = Wizard.sudo().with_context(
            active_model='madenat.guia.processing', active_id=guia.id).create(
            {'guia_processing_id': guia.id})
        wiz._onchange_guia_processing_id()
        self.assertEqual(len(wiz.line_ids), 1)
        wline = wiz.line_ids
        self.env['madenat.sv.imputation.wizard.sv.line'].sudo().create({
            'wizard_id': wiz.id,
            'wizard_line_id': wline.id,
            'sv_lot_id': sv.id,
            'imputed_volume_m3': 10.0,
        })
        res = wiz.with_user(self.user_oper).action_apply()
        imp = self.Imputation.browse(res['res_id'])
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(
            self.Imputation._i2_lot_documental_imputed_m3(etiqueta), 10.0, 3)
