# -*- coding: utf-8 -*-
"""Rebaja de etiquetas — operación y blindaje (RET/UX/VOL/SEC/REV/PHY/CON).

Intervención 2026-10-10 (§19.16). Cubre sobre el mecanismo I2 existente y **sin
efectos físicos**: elegibilidad de la guía de retorno, búsqueda y selección de
etiquetas, semántica de magnitudes documentales (nominal/aplicado/reservado/
disponible), límites entre documentos, permisos/compañía, reversa y ausencia de
movimientos de stock. Datos 100 % transaccionales (TransactionCase, rollback).
"""
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaOperativa(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'RET Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'RET Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

        cls.user_oper = cls._mk('ret_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('ret_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])
        cls.user_none = cls._mk('ret_none', ['base.group_user'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name,
            'email': '%s@madenat.cl' % name,
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name, confirm='yes', tipo='granel', state='verified'):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': state, 'tipo_recepcion': tipo,
            'service_return_confirmation': confirm or False,
            'date_emission': '2026-10-10'})

    def _etiqueta(self, guia, name, nominal, ext=None):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'external_labels': ext,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal):
        return self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})

    def _wizard(self, guia, sv=None):
        wiz = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({'guia_processing_id': guia.id})
        if sv:
            wiz.sv_lot_id = sv.id
        wiz._onchange_guia_processing_id()
        return wiz

    def _alloc(self, wiz, wline, sv, vol):
        return self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wline.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    def _imputation(self, guia, etiqueta, sv, vol, state=None, line_nominal=None):
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': etiqueta.id,
            'nominal_volume_m3': (line_nominal if line_nominal is not None
                                  else etiqueta.volume_purchase_m3)})
        if sv:
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': vol})
        if state:
            imp.write({'state': state})
        return imp

    def _snapshot(self):
        quants = self.env['stock.quant'].search(
            [('company_id', '=', self.company.id)])
        return {
            'qty': round(sum(quants.mapped('quantity')), 3),
            'moves': self.env['stock.move'].search_count(
                [('company_id', '=', self.company.id)]),
            'pickings': self.env['stock.picking'].search_count(
                [('company_id', '=', self.company.id)]),
        }

    # ══════════════════════════════════════════════════════════════════════
    # RET — elegibilidad de la guía de retorno
    # ══════════════════════════════════════════════════════════════════════
    def test_ret_01_dominio_solo_yes(self):
        domain = self.Imputation._i2_return_guide_domain()
        self.assertIn(('service_return_confirmation', '=', 'yes'), domain)
        self.assertIn(('state', '!=', 'cancelled'), domain)
        # El campo del asistente usa EXACTAMENTE el dominio canónico.
        field = self.Wizard._fields['guia_processing_id']
        self.assertEqual(
            field.domain(self.Wizard), domain)

    def test_ret_02_no_vacio_cancelada_excluidas(self):
        ok = self._guia('RET02-OK', confirm='yes')
        no = self._guia('RET02-NO', confirm='no')
        empty = self._guia('RET02-EMPTY', confirm=None)
        cancel = self._guia('RET02-CANCEL', confirm='yes', state='cancelled')
        found = self.Guia.search(self.Imputation._i2_return_guide_domain())
        self.assertIn(ok, found)
        self.assertNotIn(no, found)
        self.assertNotIn(empty, found)
        self.assertNotIn(cancel, found)

    def test_ret_03_seleccion_forzada_rechazada_sin_documento(self):
        guia = self._guia('RET03', confirm='no')
        self._etiqueta(guia, 'RET03-E', 10.0)
        wiz = self.Wizard.sudo().create({'guia_processing_id': guia.id})
        with self.assertRaises(UserError):
            wiz._i2_build_imputation()
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 0)

    def test_ret_04_historicos_consultables(self):
        guia = self._guia('RET04', confirm='yes')
        e = self._etiqueta(guia, 'RET04-E', 10.0)
        sv = self._sv(guia, 'SV00000091004', 100.0)
        imp = self._imputation(guia, e, sv, 5.0)
        # La guía deja de ser candidata para NUEVAS operaciones.
        guia.sudo().write({'service_return_confirmation': 'no'})
        self.assertNotIn(guia, self.Guia.search(
            self.Imputation._i2_return_guide_domain()))
        # El histórico sigue consultable y legible.
        self.assertIn(imp, self.Imputation.search(
            [('guia_processing_id', '=', guia.id)]))
        self.assertEqual(imp.state, 'draft')

    # ══════════════════════════════════════════════════════════════════════
    # UX — búsqueda, selección y conservación
    # ══════════════════════════════════════════════════════════════════════
    def test_ux_01_busqueda_por_numero_guia(self):
        guia = self._guia('RET-UX01-777')
        found = self.Guia.search(self.Imputation._i2_return_guide_domain()
                                 + [('name', 'ilike', 'RET-UX01-777')])
        self.assertIn(guia, found)

    def test_ux_02_busqueda_por_etiqueta(self):
        guia = self._guia('RET-UX02')
        e = self._etiqueta(guia, 'RET-UX02-INTERNO', 10.0, ext='D7739-PROV')
        self.assertIn(e, self.StockLot.search(
            [('external_labels', 'ilike', 'D7739-PROV')]))
        self.assertIn(e, self.StockLot.search(
            [('name', 'ilike', 'RET-UX02-INTERNO')]))

    def test_ux_03_seleccionar_guia_no_incluye_etiquetas(self):
        guia = self._guia('RET-UX03')
        self._etiqueta(guia, 'RET-UX03-E1', 10.0)
        self._etiqueta(guia, 'RET-UX03-E2', 20.0)
        wiz = self._wizard(guia)
        self.assertEqual(len(wiz.line_ids), 2)
        self.assertFalse(any(wiz.line_ids.mapped('selected')))
        self.assertEqual(wiz.selected_line_count, 0)

    def test_ux_04_seleccionar_todas_y_subconjunto(self):
        guia = self._guia('RET-UX04')
        self._etiqueta(guia, 'RET-UX04-E1', 10.0)
        self._etiqueta(guia, 'RET-UX04-E2', 20.0)
        wiz = self._wizard(guia)
        wiz.action_select_all()
        self.assertEqual(wiz.selected_line_count, 2)
        wiz.action_clear_selection()
        self.assertEqual(wiz.selected_line_count, 0)
        wiz.line_ids[0].selected = True
        self.assertEqual(wiz.selected_line_count, 1)
        self.assertAlmostEqual(wiz.selected_nominal_m3, 10.0, 3)

    def test_ux_05_guardar_reabrir_conserva(self):
        guia = self._guia('RET-UX05')
        e = self._etiqueta(guia, 'RET-UX05-E', 10.0)
        sv = self._sv(guia, 'SV00000091005', 100.0)
        wiz = self._wizard(guia)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        self._alloc(wiz, wl, sv, 5.0)
        imp = wiz._i2_build_imputation()
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertTrue(wiz2.line_ids.selected)
        self.assertAlmostEqual(
            sum(wiz2.line_ids.sv_alloc_ids.mapped('imputed_volume_m3')), 5.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # VOL — semántica y límites documentales
    # ══════════════════════════════════════════════════════════════════════
    def test_vol_01_semantica_magnitudes(self):
        guia = self._guia('RET-VOL01')
        e = self._etiqueta(guia, 'RET-VOL01-E', 10.0)
        sv = self._sv(guia, 'SV00000092001', 100.0)
        applied = self._imputation(guia, e, sv, 3.0, line_nominal=3.0)
        applied.with_user(self.user_oper).action_apply()
        self._imputation(guia, e, sv, 4.0, line_nominal=4.0)  # draft (reserva)
        I = self.Imputation
        self.assertAlmostEqual(I._i2_lot_nominal_m3(e), 10.0, 3)
        self.assertAlmostEqual(I._i2_lot_applied_m3(e), 3.0, 3)
        self.assertAlmostEqual(I._i2_lot_reserved_m3(e), 4.0, 3)
        self.assertAlmostEqual(I._i2_lot_available_for_m3(e), 3.0, 3)

    def test_vol_02_documento_actual_no_se_cuenta_dos_veces(self):
        guia = self._guia('RET-VOL02')
        e = self._etiqueta(guia, 'RET-VOL02-E', 10.0)
        sv = self._sv(guia, 'SV00000092002', 100.0)
        current = self._imputation(guia, e, sv, 5.0, line_nominal=5.0)
        I = self.Imputation
        self.assertAlmostEqual(I._i2_lot_available_for_m3(e), 5.0, 3)
        self.assertAlmostEqual(
            I._i2_lot_available_for_m3(e, exclude_imputation=current), 10.0, 3)

    def test_vol_03_reparto_parcial_permitido(self):
        guia = self._guia('RET-VOL03')
        e = self._etiqueta(guia, 'RET-VOL03-E', 10.0)
        sv = self._sv(guia, 'SV00000092003', 100.0)
        imp = self._imputation(guia, e, sv, 4.0, line_nominal=10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')

    def test_vol_04_exceso_capacidad_rechazado(self):
        guia = self._guia('RET-VOL04')
        e = self._etiqueta(guia, 'RET-VOL04-E', 10.0)
        sv = self._sv(guia, 'SV00000092004', 100.0)
        with self.assertRaises(ValidationError):
            self._imputation(guia, e, sv, 12.0, line_nominal=10.0)

    def test_vol_05_varios_documentos_no_eluden(self):
        guia = self._guia('RET-VOL05')
        e = self._etiqueta(guia, 'RET-VOL05-E', 10.0)
        sv = self._sv(guia, 'SV00000092005', 100.0)
        first = self._imputation(guia, e, sv, 6.0, line_nominal=6.0)
        first.with_user(self.user_oper).action_apply()
        second = self._imputation(guia, e, sv, 6.0, line_nominal=6.0)
        with self.assertRaises(UserError):
            second.with_user(self.user_oper).action_apply()
        self.assertEqual(second.state, 'draft')

    def test_vol_06_repartos_nm_no_duplican(self):
        guia = self._guia('RET-VOL06')
        e = self._etiqueta(guia, 'RET-VOL06-E', 10.0)
        sv1 = self._sv(guia, 'SV00000092006', 100.0)
        sv2 = self._sv(guia, 'SV00000092007', 100.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv1.id, 'imputed_volume_m3': 4.0})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv2.id, 'imputed_volume_m3': 6.0})
        self.assertAlmostEqual(imp.nominal_total_m3, 10.0, 3)
        self.assertAlmostEqual(imp.imputed_total_m3, 10.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SEC — permisos, compañía y atomicidad
    # ══════════════════════════════════════════════════════════════════════
    def test_sec_01_permisos_y_compania(self):
        guia = self._guia('RET-SEC01')
        e = self._etiqueta(guia, 'RET-SEC01-E', 10.0)
        sv = self._sv(guia, 'SV00000093001', 100.0)
        imp = self._imputation(guia, e, sv, 10.0, line_nominal=10.0)
        self.assertEqual(imp.company_id, self.env.company)
        with self.assertRaises(AccessError):
            imp.with_user(self.user_none).action_apply()
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')

    def test_sec_02_aplicacion_invalida_sin_estado_parcial(self):
        guia = self._guia('RET-SEC02', confirm='yes')
        e = self._etiqueta(guia, 'RET-SEC02-E', 10.0)
        sv = self._sv(guia, 'SV00000093002', 100.0)
        imp = self._imputation(guia, e, sv, 10.0, line_nominal=10.0)
        guia.sudo().write({'service_return_confirmation': 'no'})
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')
        self.assertFalse(imp.snapshot_json)
        self.assertFalse(imp.execution_date)

    # ══════════════════════════════════════════════════════════════════════
    # REV — reversa e historia
    # ══════════════════════════════════════════════════════════════════════
    def test_rev_01_reversa_conserva_historia_y_saldo(self):
        guia = self._guia('RET-REV01')
        e = self._etiqueta(guia, 'RET-REV01-E', 10.0)
        sv = self._sv(guia, 'SV00000094001', 100.0)
        I = self.Imputation
        before = I._i2_lot_applied_m3(e)
        imp = self._imputation(guia, e, sv, 10.0, line_nominal=10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertAlmostEqual(I._i2_lot_applied_m3(e), before + 10.0, 3)
        imp.reversal_reason = 'Reversa de prueba (RET-REV01).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertAlmostEqual(I._i2_lot_applied_m3(e), before, 3)
        self.assertTrue(imp.reversed_by_id)
        self.assertTrue(imp.snapshot_json)

    # ══════════════════════════════════════════════════════════════════════
    # PHY — ausencia de efectos físicos
    # ══════════════════════════════════════════════════════════════════════
    def test_phy_01_sin_efectos_fisicos(self):
        guia = self._guia('RET-PHY01')
        e = self._etiqueta(guia, 'RET-PHY01-E', 10.0)
        sv = self._sv(guia, 'SV00000095001', 100.0)
        snap = self._snapshot()
        avail = sv.sv_available_m3
        imp = self._imputation(guia, e, sv, 10.0, line_nominal=10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(self._snapshot(), snap)
        self.assertAlmostEqual(sv.sv_available_m3, avail, 3)
        self.assertEqual(self.env['madenat.sv.operation'].search_count(
            [('action_type', '=', 'imputacion')]), 0)

    # ══════════════════════════════════════════════════════════════════════
    # CON — concurrencia (protección transaccional verificable)
    # ══════════════════════════════════════════════════════════════════════
    def test_con_01_etiqueta_serializada_por_advisory_lock(self):
        guia = self._guia('RET-CON01')
        e = self._etiqueta(guia, 'RET-CON01-E', 10.0)
        sv = self._sv(guia, 'SV00000096001', 100.0)
        imp = self._imputation(guia, e, sv, 10.0, line_nominal=10.0)
        # Otra sesión posee el lock de la ETIQUETA (namespace 3) → la aplicación
        # debe fallar de forma controlada y sin estados parciales.
        cr2 = self.env.registry.cursor()
        try:
            cr2.execute('SELECT pg_advisory_lock(3, %s)', (e.id,))
            with self.assertRaises(UserError):
                imp.with_user(self.user_oper).action_apply()
            self.assertEqual(imp.state, 'draft')
        finally:
            cr2.execute('SELECT pg_advisory_unlock(3, %s)', (e.id,))
            cr2.close()
