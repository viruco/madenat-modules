# -*- coding: utf-8 -*-
"""V1 — Cobertura de cruces con EDICIÓN DIRECTA (matriz C1–C8).

El formulario persistente del documento (`madenat.sv.imputation`) es
**editable** en `draft`/`pending` (guía, procesador, motivo, líneas con nominal y
repartos con volumen). Con el guard de versión (LOCK/V1) el formulario envía
`edit_version` (con `force_save`); el backend la compara de forma atómica y
**rechaza** una edición basada en una versión obsoleta — sin cambiar la
funcionalidad (los campos siguen editables).

Las pruebas simulan la escritura del formulario enviando `edit_version` (lo que
el cliente hace con `force_save`). Datos 100 % transaccionales.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaSaveLockDirect(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'V1 Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'V1 Supplier', 'is_company': True})
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'v1_oper', 'login': 'v1_oper', 'email': 'v1@madenat.cl',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    def _guia(self, name):
        return self.env['madenat.guia.processing'].sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id, 'state': 'verified',
            'tipo_recepcion': 'granel', 'service_return_confirmation': 'yes',
            'date_emission': '2026-10-12'})

    def _etq(self, guia, name, nominal=10.0):
        lot = self.env['stock.lot'].sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal=100.0):
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

    def _draft(self, name):
        guia = self._guia(name)
        etq = self._etq(guia, name + '-E')
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:16].ljust(16, '0'))
        wiz = self._wizard(guia, sv)
        self._wline(wiz, etq).selected = True
        self._wline(wiz, etq).cantidad_asignar_m3 = 4.0
        wiz.action_prepare()
        imp = wiz.imputation_id
        imp.invalidate_recordset()
        return guia, etq, sv, wiz, imp

    # ── C2: directo modifica → asistente obsoleto guarda ──────────────────
    def test_c2_directo_modifica_asistente_obsoleto(self):
        guia, etq, sv, wiz, imp = self._draft('C2')
        wiz_b = self._wizard(guia, sv)                # asistente obsoleto
        v = imp.edit_version
        imp.write({'reason': 'directo', 'edit_version': v})   # formulario directo
        imp.invalidate_recordset()
        self.assertGreater(imp.edit_version, v)
        self._wline(wiz_b, etq).cantidad_asignar_m3 = 9.0
        with self.assertRaises(UserError):
            wiz_b.action_prepare()
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'directo')

    # ── C3: asistente modifica → formulario directo obsoleto guarda ────────
    def test_c3_asistente_modifica_directo_obsoleto(self):
        guia, etq, sv, wiz, imp = self._draft('C3')
        v_form = imp.edit_version                      # versión que cargó el form
        self._wline(wiz, etq).cantidad_asignar_m3 = 7.0
        wiz.action_prepare()                           # el asistente cambia
        with self.assertRaises(UserError) as cm:
            imp.write({'reason': 'obsoleto', 'edit_version': v_form})
        self.assertIn('cambió desde que lo abriste', str(cm.exception))
        imp.invalidate_recordset()
        self.assertFalse(imp.reason)
        self.assertAlmostEqual(imp.sv_line_ids.imputed_volume_m3, 7.0, 3)

    # ── C4: formulario A → formulario B obsoleto ──────────────────────────
    def test_c4_form_a_form_b_obsoleto(self):
        guia, etq, sv, wiz, imp = self._draft('C4')
        v0 = imp.edit_version
        imp.write({'reason': 'A', 'edit_version': v0})        # formulario A
        imp.invalidate_recordset()
        with self.assertRaises(UserError):
            imp.write({'reason': 'B', 'edit_version': v0})    # formulario B obsoleto
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'A')

    # ── C5: edición directa de líneas → formulario padre obsoleto guarda ───
    def test_c5_linea_directa_padre_obsoleto(self):
        guia, etq, sv, wiz, imp = self._draft('C5')
        v_form = imp.edit_version
        imp.line_ids.write({'nominal_volume_m3': 8.0})   # otra sesión: línea
        imp.invalidate_recordset()
        self.assertGreater(imp.edit_version, v_form)
        with self.assertRaises(UserError):
            imp.write({'reason': 'X', 'edit_version': v_form})   # padre obsoleto
        imp.invalidate_recordset()
        self.assertFalse(imp.reason)

    # ── C6: edición directa → asistente obsoleto APLICA ───────────────────
    def test_c6_directo_modifica_asistente_aplica(self):
        guia, etq, sv, wiz, imp = self._draft('C6')
        wiz_b = self._wizard(guia, sv)
        v = imp.edit_version
        imp.write({'reason': 'directo', 'edit_version': v})
        with self.assertRaises(UserError):
            wiz_b.with_user(self.user_oper).action_apply()
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')            # no se aplicó

    # ── C7: asistente guarda → formulario directo obsoleto cambia estado ──
    def test_c7_asistente_directo_obsoleto_estado(self):
        guia, etq, sv, wiz, imp = self._draft('C7')
        v_form = imp.edit_version
        self._wline(wiz, etq).cantidad_asignar_m3 = 6.0
        wiz.action_prepare()                            # el asistente cambia
        # El cliente guarda el formulario ANTES de ejecutar el botón de estado
        # ⇒ envía el `edit_version` obsoleto → conflicto.
        with self.assertRaises(UserError):
            imp.write({'state': 'pending', 'edit_version': v_form})
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'draft')

    # ── C8: transición de estado → formulario directo obsoleto edita contenido
    def test_c8_transicion_directo_obsoleto_contenido(self):
        guia, etq, sv, wiz, imp = self._draft('C8')
        v_form = imp.edit_version
        imp.with_user(self.user_oper).action_cancel()   # transición de estado
        with self.assertRaises(UserError):
            imp.write({'reason': 'Y', 'edit_version': v_form})
        imp.invalidate_recordset()
        self.assertEqual(imp.state, 'cancelled')
        self.assertFalse(imp.reason)

    # ── Positivo: el formulario con versión VIGENTE funciona ──────────────
    def test_v1_directo_con_version_vigente_funciona(self):
        guia, etq, sv, wiz, imp = self._draft('V1POS')
        v = imp.edit_version
        imp.write({'reason': 'ok', 'edit_version': v})  # versión vigente
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'ok')
        self.assertEqual(imp.edit_version, v + 1)

    # ── RESIDUAL declarado: ORM/RPC sin `edit_version` ────────────────────
    def test_v1_residual_orm_sin_version(self):
        """LÍMITE declarado: una escritura ORM/RPC que NO envíe `edit_version`
        (p. ej. un script/automatización) no se compara; sólo la vía UI
        (formulario con `force_save` y asistente) envía la versión. La versión
        del documento SÍ avanza, de modo que los asistentes/formularios abiertos
        lo detectan después."""
        guia, etq, sv, wiz, imp = self._draft('V1RES')
        v = imp.edit_version
        imp.write({'reason': 'script'})                 # sin edit_version
        imp.invalidate_recordset()
        self.assertEqual(imp.reason, 'script')          # se aplicó (residual)
        self.assertGreater(imp.edit_version, v)         # la versión avanza
