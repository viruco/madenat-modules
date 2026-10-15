# -*- coding: utf-8 -*-
"""S2 — «Trabajo en preparación»: filtro EFECTIVO por estado (FASE 10, 2026-10-15).

Defecto **F2** del diagnóstico
``DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015``: el campo
``sv_assignment_work_imputation_ids`` declaraba
``domain="[('state','in',('draft','pending'))]"``, pero el ORM **no aplica** el
``domain`` de un ``One2many`` al leer. La sección del SV listaba y **contaba**
documentos ANULADOS/APLICADOS/REVERSADOS como «trabajo en preparación» y ofrecía
«Continuar», que fallaba con ``UserError``.

Cubre:

* **T2** — la lista y el contador excluyen los estados terminales
  (``applied``/``reversed``/``cancelled``).
* **T3** — «Continuar» sobre un estado terminal **no** falla con un error
  técnico: devuelve un mensaje operativo con la ruta disponible.

Datos 100 % transaccionales (``TransactionCase``, rollback); no queda residuo
alguno tras el rollback.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaWorkFilter(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'WF Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'WF Supplier', 'is_company': True})
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'wf_oper', 'login': 'wf_oper',
            'email': 'wf_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})
        cls.user_jef = cls.env['res.users'].create({
            'name': 'wf_jef', 'login': 'wf_jef',
            'email': 'wf_jef@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_jefatura_operaciones'
                ).id])]})

    # ── Fábricas (datos propios; limpieza por rollback de la clase) ────────
    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-15'})

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

    def _draft_work(self, guia, sv, etq, vol):
        """Crea un borrador (trabajo) con una etiqueta incluida y reparto."""
        wiz = self._wizard(guia, sv)
        line = self._wline(wiz, etq)
        line.selected = True
        line.cantidad_asignar_m3 = vol
        wiz.action_prepare()
        return wiz.imputation_id

    # ── T2: la lista y el contador excluyen los estados terminales ─────────
    def test_wf_01_borrador_aparece_y_cuenta(self):
        guia = self._guia('WF-01')
        e = self._etq(guia, 'WF-01-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0001', 100.0)
        imp = self._draft_work(guia, sv, e, 4.0)
        self.assertEqual(imp.state, 'draft')
        sv.invalidate_recordset()
        self.assertEqual(sv.sv_assignment_work_imputation_ids, imp)
        self.assertEqual(sv.sv_assignment_work_count, 1)

    def test_wf_02_anulada_no_aparece_ni_cuenta(self):
        guia = self._guia('WF-02')
        e = self._etq(guia, 'WF-02-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0002', 100.0)
        imp = self._draft_work(guia, sv, e, 4.0)
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        # El vínculo de trabajo SIGUE existiendo (trazabilidad)…
        self.assertEqual(imp.work_sv_lot_id, sv)
        self.assertIn(imp, self.Imputation.search(
            [('work_sv_lot_id', '=', sv.id)]))
        # …pero NO se lista ni se cuenta como «trabajo en preparación».
        sv.invalidate_recordset()
        self.assertFalse(sv.sv_assignment_work_imputation_ids)
        self.assertEqual(sv.sv_assignment_work_count, 0)

    def test_wf_03_aplicada_y_reversada_no_aparecen_ni_cuentan(self):
        guia = self._guia('WF-03')
        e = self._etq(guia, 'WF-03-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0003', 100.0)
        imp = self._draft_work(guia, sv, e, 10.0)
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertEqual(imp.work_sv_lot_id, sv)
        sv.invalidate_recordset()
        self.assertFalse(sv.sv_assignment_work_imputation_ids)
        self.assertEqual(sv.sv_assignment_work_count, 0)
        # Reversada: tampoco es trabajo en preparación.
        imp.reversal_reason = 'WF-03 reversa de control.'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        sv.invalidate_recordset()
        self.assertFalse(sv.sv_assignment_work_imputation_ids)
        self.assertEqual(sv.sv_assignment_work_count, 0)

    def test_wf_04_contador_solo_cuenta_el_trabajo_tras_un_terminal(self):
        """Una anulada previa NO debe «contar» junto al borrador nuevo."""
        guia = self._guia('WF-04')
        e1 = self._etq(guia, 'WF-04-E1', 10.0)
        sv = self._sv(guia, 'SV0000WF0004', 100.0)
        imp1 = self._draft_work(guia, sv, e1, 4.0)
        imp1.with_user(self.user_oper).action_cancel()
        guia2 = self._guia('WF-04B')
        e2 = self._etq(guia2, 'WF-04-E2', 10.0)
        imp2 = self._draft_work(guia2, sv, e2, 5.0)
        sv.invalidate_recordset()
        self.assertEqual(sv.sv_assignment_work_imputation_ids, imp2)
        self.assertEqual(sv.sv_assignment_work_count, 1)

    # ── T3: «Continuar» sobre estados terminales (sin error técnico) ───────
    def test_wf_05_continuar_sobre_anulada_da_mensaje_operativo(self):
        guia = self._guia('WF-05')
        e = self._etq(guia, 'WF-05-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0005', 100.0)
        imp = self._draft_work(guia, sv, e, 4.0)
        imp.with_user(self.user_oper).action_cancel()
        res = imp.action_continue_preparation()      # NO debe lanzar UserError
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'display_notification')
        message = (res.get('params') or {}).get('message') or ''
        self.assertIn('Volver a borrador', message)
        self.assertIn(imp.name, message)

    def test_wf_06_continuar_sobre_aplicada_da_mensaje_operativo(self):
        guia = self._guia('WF-06')
        e = self._etq(guia, 'WF-06-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0006', 100.0)
        imp = self._draft_work(guia, sv, e, 10.0)
        imp.with_user(self.user_oper).action_apply()
        res = imp.action_continue_preparation()      # NO debe lanzar UserError
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('tag'), 'display_notification')
        self.assertIn(imp.name, (res.get('params') or {}).get('message') or '')

    def test_wf_07_continuar_sobre_borrador_abre_el_asistente(self):
        guia = self._guia('WF-07')
        e = self._etq(guia, 'WF-07-E', 10.0)
        sv = self._sv(guia, 'SV0000WF0007', 100.0)
        imp = self._draft_work(guia, sv, e, 1.0)
        action = imp.action_continue_preparation()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(
            action['context']['default_guia_processing_id'], guia.id)
        self.assertEqual(
            action['context']['default_sv_lot_id'], sv.id)
