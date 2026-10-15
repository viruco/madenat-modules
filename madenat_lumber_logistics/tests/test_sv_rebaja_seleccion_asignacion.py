# -*- coding: utf-8 -*-
"""Selección y asignación explícita — «Rebaja de etiquetas» (2026-10-10).

Cubre la corrección del fallo real de «Seleccionar todas» (campo
``processed_lot_id`` ausente en el payload del cliente) y la nueva acción
explícita «Asignar seleccionadas al SV de trabajo», SIN efectos físicos.
Datos 100 % transaccionales (TransactionCase, rollback).

Nota sobre la causa (demostrada, no supuesta): en el cliente Odoo 18
(``web/static/src/model/relational_model/record.js::_getChanges``) un subcampo
``readonly`` de una x2many NO se envía al servidor salvo ``force_save="1"``. El
campo ``processed_lot_id`` del listado del asistente era ``readonly="1"`` sin
``force_save``, por lo que el CREATE de cada fila llegaba sin el identificador.
"""
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSeleccionAsignacion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'SEL Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'SEL Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardLine = cls.env['madenat.sv.imputation.wizard.line']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

        cls.user_oper = cls._mk('sel_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_none = cls._mk('sel_none', ['base.group_user'])

    @classmethod
    def _mk(cls, name, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name, 'email': '%s@madenat.cl' % name,
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name, confirm='yes'):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
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

    def _open_wizard(self, guia, sv=None):
        """Simula la APERTURA + ELECCIÓN DE GUÍA del navegador (default_get+onchange)."""
        wiz = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({'guia_processing_id': guia.id})
        if sv:
            wiz.sv_lot_id = sv.id
        wiz._onchange_guia_processing_id()
        return wiz

    # ══════════════════════════════════════════════════════════════════════
    # ERR — el fallo real de «Seleccionar todas»
    # ══════════════════════════════════════════════════════════════════════
    def test_err_01_vista_fuerza_envio_del_identificador(self):
        """La fuente del fallo era el cliente: la fila readonly no se enviaba."""
        from lxml import etree
        arch = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD).arch
        root = etree.fromstring(arch.encode())
        node = root.find(".//field[@name='processed_lot_id']")
        self.assertIsNotNone(node)
        self.assertEqual(node.get('force_save'), '1')

    def test_err_02_ciclo_formulario_seleccionar_todas(self):
        """Apertura nueva → elegir guía → Seleccionar todas (sin guardar antes)."""
        guia = self._guia('SEL-ERR02')
        self._etiqueta(guia, 'SEL-ERR02-E1', 10.0)
        self._etiqueta(guia, 'SEL-ERR02-E2', 20.0)
        wiz = self._open_wizard(guia)
        self.assertEqual(len(wiz.line_ids), 2)
        self.assertTrue(all(wiz.line_ids.mapped('processed_lot_id')))
        wiz.action_select_all()
        self.assertTrue(all(wiz.line_ids.mapped('selected')))
        self.assertTrue(all(wiz.line_ids.mapped('processed_lot_id')))
        self.assertEqual(wiz.selected_line_count, 2)

    def test_err_03_guardar_reabrir_seleccionar_todas(self):
        guia = self._guia('SEL-ERR03')
        e = self._etiqueta(guia, 'SEL-ERR03-E', 10.0)
        sv = self._sv(guia, 'SV00000103001', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 4.0})
        imp = wiz._i2_build_imputation()
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        wiz2.action_select_all()
        self.assertTrue(all(wiz2.line_ids.mapped('processed_lot_id')))
        self.assertTrue(all(wiz2.line_ids.mapped('selected')))
        self.assertEqual(wiz2.imputation_id, imp)

    def test_err_04_cambiar_seleccion_no_pierde_identificador(self):
        guia = self._guia('SEL-ERR04')
        self._etiqueta(guia, 'SEL-ERR04-E1', 10.0)
        self._etiqueta(guia, 'SEL-ERR04-E2', 20.0)
        wiz = self._open_wizard(guia)
        ids_before = wiz.line_ids.mapped('processed_lot_id').ids
        wiz.action_select_all()
        wiz.action_clear_selection()
        wiz.line_ids[0].selected = True
        self.assertEqual(
            wiz.line_ids.mapped('processed_lot_id').ids, ids_before)

    # ══════════════════════════════════════════════════════════════════════
    # ASG — asignación explícita al SV de trabajo
    # ══════════════════════════════════════════════════════════════════════
    def test_asg_01_asignar_seleccionadas(self):
        guia = self._guia('SEL-ASG01')
        self._etiqueta(guia, 'SEL-ASG01-E1', 10.0)
        self._etiqueta(guia, 'SEL-ASG01-E2', 20.0)
        sv = self._sv(guia, 'SV00000104001', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wiz.action_select_all()
        wiz.action_assign_selected()
        self.assertEqual(len(wiz.sv_line_ids), 2)
        self.assertTrue(all(
            a.sv_lot_id == sv for a in wiz.sv_line_ids))
        # Volumen 0: el usuario debe introducirlo o usar «Usar disponible».
        self.assertTrue(all(
            abs(a.imputed_volume_m3) < 1e-6 for a in wiz.sv_line_ids))
        wiz.action_use_available()
        self.assertAlmostEqual(
            sum(wiz.sv_line_ids.mapped('imputed_volume_m3')), 30.0, 3)
        self.assertIn('2 etiquetas', wiz.assigned_summary)

    def test_asg_02_sin_seleccion_rechaza(self):
        guia = self._guia('SEL-ASG02')
        self._etiqueta(guia, 'SEL-ASG02-E', 10.0)
        sv = self._sv(guia, 'SV00000104002', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        with self.assertRaises(UserError):
            wiz.action_assign_selected()

    def test_asg_03_sin_cantidad_guarda_trabajo_incompleto(self):
        guia = self._guia('SEL-ASG03')
        self._etiqueta(guia, 'SEL-ASG03-E', 10.0)
        sv = self._sv(guia, 'SV00000104003', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wiz.action_select_all()
        wiz.action_assign_selected()
        # SAVE (2026-10-11): guardar trabajo SIN cantidad NO falla; queda en
        # borrador con la etiqueta conservada y sin reparto persistido.
        imp = wiz._i2_build_imputation()
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 1)
        self.assertFalse(imp.sv_line_ids)
        self.assertEqual(len(imp.line_ids), 1)

    def test_asg_04_repetir_no_duplica(self):
        guia = self._guia('SEL-ASG04')
        self._etiqueta(guia, 'SEL-ASG04-E', 10.0)
        sv = self._sv(guia, 'SV00000104004', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wiz.action_select_all()
        wiz.action_assign_selected()
        wiz.action_assign_selected()
        self.assertEqual(len(wiz.sv_line_ids), 1)

    def test_asg_05_conserva_reparto_a_otros_sv(self):
        guia = self._guia('SEL-ASG05')
        e = self._etiqueta(guia, 'SEL-ASG05-E', 10.0)
        sv1 = self._sv(guia, 'SV00000104005', 100.0)
        sv2 = self._sv(guia, 'SV00000104006', 100.0)
        wiz = self._open_wizard(guia, sv=sv1)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv2.id, 'imputed_volume_m3': 6.0})
        wiz.action_assign_selected()
        allocs = {(a.wizard_line_id.id, a.sv_lot_id.id): a
                  for a in wiz.sv_line_ids}
        self.assertIn((wl.id, sv2.id), allocs)   # se conserva
        self.assertIn((wl.id, sv1.id), allocs)   # se agrega el de trabajo

    def test_asg_06_no_aplica_ni_altera_saldos(self):
        guia = self._guia('SEL-ASG06')
        e = self._etiqueta(guia, 'SEL-ASG06-E', 10.0)
        sv = self._sv(guia, 'SV00000104007', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wiz.action_select_all()
        before = self.Imputation._i2_lot_applied_m3(e)
        wiz.action_assign_selected()
        wiz.action_use_available()
        self.assertFalse(wiz.imputation_id)
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 0)
        self.assertAlmostEqual(
            self.Imputation._i2_lot_applied_m3(e), before, 3)

    # ══════════════════════════════════════════════════════════════════════
    # VOL — semántica del caso parcial
    # ══════════════════════════════════════════════════════════════════════
    def test_vol_01_caso_parcial_semantica(self):
        """Nominal 5, reparto parcial 3: los indicadores no confunden magnitudes."""
        guia = self._guia('SEL-VOL01')
        e = self._etiqueta(guia, 'SEL-VOL01-E', 10.0)
        sv = self._sv(guia, 'SV00000105001', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        wl.nominal_volume_m3 = 5.0
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 3.0})
        self.assertAlmostEqual(wl.etiqueta_nominal_m3, 10.0, 3)   # capacidad
        self.assertAlmostEqual(wl.etiqueta_pendiente_m3, 2.0, 3)   # 5 − 3
        self.assertIn('3.000', wiz.assigned_summary)
        imp = wiz._i2_build_imputation()
        self.assertAlmostEqual(imp.nominal_total_m3, 5.0, 3)   # etiqueta
        self.assertAlmostEqual(imp.imputed_total_m3, 3.0, 3)   # reparto SV

    def test_vol_02_exceso_rechazado(self):
        guia = self._guia('SEL-VOL02')
        e = self._etiqueta(guia, 'SEL-VOL02-E', 10.0)
        sv = self._sv(guia, 'SV00000105002', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        wl.nominal_volume_m3 = 5.0
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 6.0})
        with self.assertRaises(ValidationError):
            wiz._i2_build_imputation()

    # ══════════════════════════════════════════════════════════════════════
    # PER — persistencia
    # ══════════════════════════════════════════════════════════════════════
    def test_per_01_guardar_reabrir_conserva(self):
        guia = self._guia('SEL-PER01')
        e = self._etiqueta(guia, 'SEL-PER01-E', 10.0)
        sv = self._sv(guia, 'SV00000106001', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        wl.nominal_volume_m3 = 7.0
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 3.5})
        imp = wiz._i2_build_imputation()
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        self.assertEqual(wiz2.imputation_id, imp)
        wl2 = wiz2.line_ids.filtered(lambda l: l.processed_lot_id == e)
        self.assertTrue(wl2.selected)
        self.assertAlmostEqual(wl2.nominal_volume_m3, 7.0, 3)
        self.assertAlmostEqual(
            sum(wl2.sv_alloc_ids.mapped('imputed_volume_m3')), 3.5, 3)

    # ══════════════════════════════════════════════════════════════════════
    # SEC — permisos, elegibilidad y selección forzada
    # ══════════════════════════════════════════════════════════════════════
    def test_sec_01_permisos_elegibilidad_forzada(self):
        field = self.Wizard._fields['guia_processing_id']
        self.assertEqual(
            field.domain(self.Wizard),
            self.Imputation._i2_return_guide_domain())
        guia = self._guia('SEL-SEC01', confirm='no')
        self._etiqueta(guia, 'SEL-SEC01-E', 10.0)
        wiz = self.Wizard.sudo().create({'guia_processing_id': guia.id})
        with self.assertRaises(UserError):
            wiz._i2_build_imputation()
        self.assertEqual(self.Imputation.search_count(
            [('guia_processing_id', '=', guia.id)]), 0)

    def test_sec_02_sin_permiso_no_aplica(self):
        guia = self._guia('SEL-SEC02')
        e = self._etiqueta(guia, 'SEL-SEC02-E', 10.0)
        sv = self._sv(guia, 'SV00000106002', 100.0)
        wiz = self._open_wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        wl.selected = True
        self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wl.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': 10.0})
        imp = wiz._i2_build_imputation()
        with self.assertRaises(AccessError):
            imp.with_user(self.user_none).action_apply()

    # ══════════════════════════════════════════════════════════════════════
    # PHY — sin efectos físicos
    # ══════════════════════════════════════════════════════════════════════
    def test_phy_01_sin_efectos_fisicos(self):
        guia = self._guia('SEL-PHY01')
        self._etiqueta(guia, 'SEL-PHY01-E', 10.0)
        sv = self._sv(guia, 'SV00000107001', 100.0)
        quants = self.env['stock.quant'].search(
            [('company_id', '=', self.company.id)])
        qty = round(sum(quants.mapped('quantity')), 3)
        moves = self.env['stock.move'].search_count(
            [('company_id', '=', self.company.id)])
        avail = sv.sv_available_m3
        wiz = self._open_wizard(guia, sv=sv)
        wiz.action_select_all()
        wiz.action_assign_selected()
        wiz.action_use_available()
        imp = wiz._i2_build_imputation()
        imp.with_user(self.user_oper).action_apply()
        quants2 = self.env['stock.quant'].search(
            [('company_id', '=', self.company.id)])
        self.assertEqual(round(sum(quants2.mapped('quantity')), 3), qty)
        self.assertEqual(self.env['stock.move'].search_count(
            [('company_id', '=', self.company.id)]), moves)
        self.assertAlmostEqual(sv.sv_available_m3, avail, 3)
