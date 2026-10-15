# -*- coding: utf-8 -*-
"""Rebaja de etiquetas — unificación de acceso (NAV-01..12).

Verifica, con metadatos (menús/acciones/vistas) y datos 100 % transaccionales
(TransactionCase, rollback), que exista UN ÚNICO enlace operativo «Rebaja de
etiquetas» en Logística Exportación; que «Asignaciones SV» e «Imputaciones
documentales SV» no sean accesos paralelos; que la entrada abra el listado SV
existente y sus documentos se consulten DENTRO del recorrido; que consultar no
cree documentos ni altere saldos; y que aplicar/reversar reutilicen el asistente
y el modelo vigentes. No crea ni borra datos (rollback).

NAV-10 (una segunda actualización NO restaura el menú retirado) se acredita
fuera del test unitario reaplicando `-u madenat_lumber_logistics` y consultando
ir.ui.menu (evidencia de la intervención).
"""
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaNavigation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'NAV Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'NAV Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

        cls.user_oper = cls.env['res.users'].create({
            'name': 'nav_oper', 'login': 'nav_oper',
            'email': 'nav_oper@madenat.cl',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

        cls.Menu = cls.env['ir.ui.menu'].with_context(active_test=False)
        cls.menu_logistics = cls.env.ref('%s.menu_lumber_logistics' % MOD)
        cls.menu_assign = cls.env.ref('%s.menu_madenat_sv_assignment' % MOD)
        cls.menu_imputation = cls.env.ref('%s.menu_madenat_sv_imputation' % MOD)
        cls.action_assign = cls.env.ref(
            '%s.action_madenat_sv_assignment' % MOD)
        cls.action_imputation = cls.env.ref(
            '%s.action_madenat_sv_imputation' % MOD)

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-10'})

    def _etiqueta(self, guia, name, nominal):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
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

    def _add_alloc(self, wiz, wline, sv, vol):
        return self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wline.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    def _sv_linked_active_menus(self):
        children = self.Menu.search([
            ('parent_id', '=', self.menu_logistics.id),
            ('active', '=', True)])
        linked = self.Menu.browse()
        for menu in children:
            act = menu.action
            if (act and act._name == 'ir.actions.act_window'
                    and act.res_model in ('stock.lot', 'madenat.sv.imputation')):
                linked |= menu
        return children, linked

    # ── NAV-01: sólo un enlace operativo visible «Rebaja de etiquetas» ──
    def test_nav_01_unico_enlace(self):
        self.assertTrue(self.menu_assign.active)
        self.assertEqual(self.menu_assign.name, 'Rebaja de etiquetas')
        self.assertEqual(self.menu_assign.parent_id, self.menu_logistics)
        _, linked = self._sv_linked_active_menus()
        self.assertEqual(len(linked), 1)
        self.assertEqual(linked, self.menu_assign)

    # ── NAV-02: los accesos anteriores no son paralelos (retirados) ──
    def test_nav_02_sin_accesos_paralelos(self):
        self.assertFalse(self.menu_imputation.active)
        children, _ = self._sv_linked_active_menus()
        names = children.mapped('name')
        self.assertNotIn('Asignaciones SV', names)
        self.assertNotIn('Imputaciones documentales SV', names)

    # ── NAV-03: el enlace abre el listado SV existente (no un modelo nuevo) ──
    def test_nav_03_abre_listado_sv_existente(self):
        self.assertEqual(self.action_assign.res_model, 'stock.lot')
        self.assertEqual(
            self.action_assign.domain, "[('lot_flow_type', '=', 'volume')]")
        view_names = self.action_assign.view_ids.mapped('view_id.name')
        self.assertIn('madenat.sv.assignment.list', view_names)
        self.assertIn('madenat.sv.assignment.form', view_names)
        self.assertEqual(self.action_assign.view_ids[0].view_id.model,
                         'stock.lot')

    # ── NAV-04/05: documentos e historial accesibles dentro del recorrido ──
    def test_nav_04_05_documentos_dentro_del_recorrido(self):
        form = self.env.ref('%s.view_madenat_sv_assignment_form' % MOD)
        arch = form.arch
        self.assertIn('action_open_sv_rebajas', arch)
        self.assertIn('Ver historial completo', arch)
        self.assertIn('Abrir documento', arch)
        guia = self._guia('NAV-45')
        sv = self._sv(guia, 'SV00000003045', 100.0)
        action = sv.action_open_sv_rebajas()
        self.assertEqual(action['res_model'], 'madenat.sv.imputation')
        # SAVE (2026-10-11): el dominio incluye el trabajo NO aplicado del SV
        # (work_sv_lot_id) además de los repartos positivos hacia él.
        self.assertEqual(action['domain'],
                         ['|', ('sv_line_ids.sv_lot_id', '=', sv.id),
                          ('work_sv_lot_id', '=', sv.id)])
        # El historial completo reutiliza la MISMA acción de documentos.
        self.assertEqual(self.action_imputation.res_model,
                         'madenat.sv.imputation')
        self.assertFalse(self.menu_imputation.active)

    # ── NAV-06: consultar o navegar NO crea documentos ni altera saldos ──
    def test_nav_06_consultar_no_crea_ni_altera(self):
        guia = self._guia('NAV-06')
        self._etiqueta(guia, 'NAV-06-E', 10.0)
        sv = self._sv(guia, 'SV00000003006', 100.0)
        before_imp = self.Imputation.search_count([])
        before_lines = self.ImputationLine.search_count([])
        before_bal = sv.sv_assignment_documental_balance_m3
        sv.action_open_sv_rebajas()
        sv.read(['sv_assignment_applied_m3',
                 'sv_assignment_documental_balance_m3'])
        self.assertEqual(self.Imputation.search_count([]), before_imp)
        self.assertEqual(self.ImputationLine.search_count([]), before_lines)
        self.assertAlmostEqual(
            sv.sv_assignment_documental_balance_m3, before_bal, 3)

    # ── NAV-07: registrar utiliza el asistente y el modelo existentes ──
    def test_nav_07_registrar_usa_asistente_existente(self):
        guia = self._guia('NAV-07')
        etiqueta = self._etiqueta(guia, 'NAV-07-E', 10.0)
        sv = self._sv(guia, 'SV00000003007', 100.0)
        defaults = self.Wizard.with_context(
            active_model='stock.lot', active_id=sv.id).default_get(
                ['sv_lot_id', 'imputation_id'])
        self.assertEqual(defaults.get('sv_lot_id'), sv.id)
        wiz = self._wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etiqueta)
        wl.selected = True
        self._add_alloc(wiz, wl, sv, 5.0)
        imp = wiz._i2_build_imputation()
        self.assertEqual(imp._name, 'madenat.sv.imputation')
        self.assertEqual(len(imp.sv_line_ids), 1)

    # ── NAV-08: guardar y reabrir conserva selección y reparto ──
    def test_nav_08_reabrir_conserva(self):
        guia = self._guia('NAV-08')
        etiqueta = self._etiqueta(guia, 'NAV-08-E', 10.0)
        sv = self._sv(guia, 'SV00000003008', 100.0)
        wiz = self._wizard(guia)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etiqueta)
        wl.selected = True
        self._add_alloc(wiz, wl, sv, 5.0)
        imp = wiz._i2_build_imputation()
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.line_ids), 1)
        self.assertTrue(wiz2.line_ids.selected)
        self.assertAlmostEqual(
            sum(wiz2.line_ids.sv_alloc_ids.mapped('imputed_volume_m3')),
            5.0, 3)

    # ── NAV-09: aplicar y reversar conservan permisos y comportamiento ──
    def test_nav_09_aplicar_reversar_permisos(self):
        guia = self._guia('NAV-09')
        etiqueta = self._etiqueta(guia, 'NAV-09-E', 10.0)
        sv = self._sv(guia, 'SV00000003009', 100.0)
        wiz = self._wizard(guia, sv=sv)
        wl = wiz.line_ids.filtered(lambda l: l.processed_lot_id == etiqueta)
        wl.selected = True
        self._add_alloc(wiz, wl, sv, 10.0)
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id   # SIMPLE: Aplicar permanece en el asistente
        self.assertEqual(imp.state, 'applied')
        with self.assertRaises(AccessError):
            imp.with_user(self.user_oper).action_reverse()
        self.assertEqual(imp.state, 'applied')

    # ── NAV-10: el retiro del menú es reproducible (no se reactiva) ──
    # El menuitem conserva su definición (instalaciones nuevas) y el registro
    # de desactivación posterior fija active=False. En test unitario se acredita
    # el estado resultante; la segunda actualización se valida fuera del test
    # reaplicando `-u` (ver evidencia de la intervención).
    def test_nav_10_menuitem_retirado_no_reactivado(self):
        menu = self.Menu.browse(self.menu_imputation.id)
        self.assertFalse(menu.active)
        self.assertEqual(menu.action, self.action_imputation)
        # La acción sigue disponible (documentos preservados), sólo sin menú.
        self.assertEqual(self.action_imputation.res_model,
                         'madenat.sv.imputation')

    # ── NAV-11: «Rebajar por Motonave» y «Consolidación» no cambian ──
    def test_nav_11_flujos_ajenos_intactos(self):
        motonave = self.env.ref('%s.menu_lumber_shipment_rebaja' % MOD)
        consolidacion = self.env.ref(
            '%s.menu_lumber_container_consolidation' % MOD)
        self.assertEqual(motonave.name, 'Rebajar por Motonave')
        self.assertEqual(consolidacion.name, 'Consolidación')
        self.assertTrue(motonave.active)
        self.assertTrue(consolidacion.active)
        self.assertEqual(motonave.parent_id, self.menu_logistics)
        self.assertEqual(consolidacion.parent_id, self.menu_logistics)

    # ── NAV-12: la ingesta no recibe nuevas pantallas ni pasos ──
    def test_nav_12_ingesta_sin_nuevas_pantallas(self):
        children = self.Menu.search([
            ('parent_id', '=', self.menu_logistics.id),
            ('active', '=', True)])
        intake = [m for m in children
                  if m.action and m.action._name == 'ir.actions.act_window'
                  and 'intake' in (m.action.res_model or '')]
        self.assertFalse(intake)
        # La operación sigue apoyada sólo en stock.lot y madenat.sv.imputation.
        self.assertEqual(self.action_assign.res_model, 'stock.lot')
        self.assertEqual(self.action_imputation.res_model,
                         'madenat.sv.imputation')
