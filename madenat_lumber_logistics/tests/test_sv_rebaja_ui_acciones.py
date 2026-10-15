# -*- coding: utf-8 -*-
"""Acciones visibles del asistente «Registrar rebaja» (UI/MAINT, 2026-10-11).

Incidencia: el asistente (formulario amplio, `target="current"`) tenía sus
acciones **sólo** en un `<footer>`, que Odoo no renderiza fuera de un diálogo ⇒
«Guardar borrador» / «Revisar y aplicar» / «Descartar» quedaban **invisibles**.
Corrección: acciones en el `<header>` nativo + «Abrir documento» + «Descartar y
volver» + confirmación con referencia.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaUiAcciones(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'UIACT Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'UIACT Supplier', 'is_company': True})
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.view = cls.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        cls.action = cls.env.ref(
            '%s.action_madenat_sv_imputation_wizard' % MOD)

    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-11'})

    def _etq(self, guia, name, nominal):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': name, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal):
        return self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})

    def _wizard(self, guia, sv):
        wiz = self.Wizard.sudo().with_context(
            active_model='stock.lot', active_id=sv.id,
            default_sv_lot_id=sv.id).create({
                'guia_processing_id': guia.id, 'sv_lot_id': sv.id})
        wiz._onchange_guia_processing_id()
        return wiz

    def _wline(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _root(self):
        return etree.fromstring(self.view.arch.encode())

    # ── UI-01: entrada real abre la vista correcta ────────────────────────
    def test_ui_01_entrada_abre_vista_correcta(self):
        self.assertEqual(self.action.res_model, 'madenat.sv.imputation.wizard')
        self.assertEqual(self.action.view_mode, 'form')
        self.assertEqual(self.action.target, 'current')
        self.assertEqual(self.action.view_id, self.view)
        arch = self.Wizard.get_view(view_id=self.view.id)['arch']
        self.assertIn('action_prepare', arch)

    # ── UI-02: acciones principales en el HEADER (no en footer) ───────────
    def test_ui_02_acciones_visibles_en_header(self):
        root = self._root()
        header = root.find('.//header')
        self.assertIsNotNone(header, 'El asistente debe tener <header>')
        self.assertIsNone(
            root.find('.//footer'),
            'Sin <footer>: no se renderiza en target=current')
        names = {b.get('name') for b in header.findall('button')}
        # Simplificación (2026-10-11): botonera principal de DOS acciones.
        for name in ('action_prepare', 'action_apply', 'action_discard_changes'):
            self.assertIn(name, names)
        # Las opciones avanzadas NO están en la botonera principal…
        for name in ('action_open_document', 'action_pending',
                     'action_propose_fifo'):
            self.assertNotIn(name, names)
        # …pero siguen disponibles en el grupo «Más opciones (avanzado)».
        arch = self.view.arch
        self.assertIn('Más opciones', arch)
        for name in ('action_open_document', 'action_pending',
                     'action_propose_fifo'):
            self.assertIn(name, arch)
        apply_btn = header.find("button[@name='action_apply']")
        self.assertIn('madenat_lumber_core.group_madenat_operaciones',
                      apply_btn.get('groups') or '')
        for name in ('action_prepare', 'action_apply'):
            btn = header.find("button[@name='%s']" % name)
            self.assertIn('imputation_state', btn.get('invisible') or '')
        self.assertIsNotNone(header.find("button[@name='action_discard_changes']"))
        # «Abrir documento» está en «Más opciones» (no en la botonera principal).
        abrir = etree.fromstring(self.view.arch.encode()).find(
            ".//button[@name='action_open_document']")
        self.assertIn('imputation_id', abrir.get('invisible') or '')

    # ── UI-03: los botones llaman a métodos de NEGOCIO ────────────────────
    def test_ui_03_botones_llaman_metodos_de_negocio(self):
        guia = self._guia('UIACT-03')
        e = self._etq(guia, 'UIACT-03-E', 10.0)
        sv = self._sv(guia, 'SV0000UIACT3', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        res = wiz.action_prepare()             # «Guardar borrador»
        imp = wiz.imputation_id
        self.assertTrue(imp.exists())          # documento persistente
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(res['res_model'], wiz._name)
        self.assertEqual(res['res_id'], wiz.id)
        opened = wiz.action_open_document()    # «Abrir documento»
        self.assertEqual(opened['res_model'], 'madenat.sv.imputation')
        self.assertEqual(opened['res_id'], imp.id)
        discard = wiz.action_discard_changes()  # «Descartar y volver»
        self.assertEqual(discard['res_model'], 'stock.lot')
        self.assertEqual(discard['res_id'], sv.id)
        self.assertTrue(imp.exists())          # no borra el documento guardado

    # ── UI-04/05: visibilidad coherente; sin Owl fuera de contexto ────────
    def test_ui_04_05_visibilidad_y_sin_owl_fuera_contexto(self):
        root = self._root()
        header = root.find('.//header')
        declared = {f.get('name') for f in root.findall('.//field')}
        self.assertIn('imputation_state', declared)
        self.assertIn('imputation_id', declared)
        for btn in header.findall('button'):
            expr = (btn.get('invisible') or '')
            self.assertNotIn('wizard_id', expr)
            self.assertNotIn('parent.', expr)
        eff = self.Wizard.get_view(view_id=self.view.id)['arch']
        self.assertIn('action_prepare', eff)

    # ── SAVE-04 (UI): confirmación con referencia real y estado ───────────
    def test_ui_conf_01_confirmacion_con_referencia(self):
        guia = self._guia('UIACT-CONF')
        e = self._etq(guia, 'UIACT-CONF-E', 10.0)
        sv = self._sv(guia, 'SV0000UIACTC', 100.0)
        wiz = self._wizard(guia, sv)
        self._wline(wiz, e).selected = True
        wiz.action_assign_selected()
        self._wline(wiz, e).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertIn(imp.name, wiz.save_result or '')
        self.assertIn('draft', wiz.save_result or '')
        self.assertIn('No se ha aplicado', wiz.save_result or '')
        # Sin documento guardado, «Abrir documento» es explícito y rechaza.
        guia2 = self._guia('UIACT-CONF2')
        sv2 = self._sv(guia2, 'SV0000UIACTD', 100.0)
        empty = self._wizard(guia2, sv2)
        with self.assertRaises(UserError):
            empty.action_open_document()
