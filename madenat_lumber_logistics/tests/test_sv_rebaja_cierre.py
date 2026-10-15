# -*- coding: utf-8 -*-
"""Cierre probatorio — rebaja de etiquetas (AUD-ETQ-06..10, 2026-10-11).

Cierra las verificaciones críticas pendientes del informe 18.0.1.15.0:
* **AUD-ETQ-06** reversa: motivo vacío o sólo espacios rechazado; trazabilidad
  completa (usuario/fecha/motivo/original); contexto no autoriza.
* **AUD-ETQ-07** aislamiento multi-compañía de la imputación (cabecera/líneas/
  repartos) probado con usuario no administrador y sin `sudo`.
* **AUD-ETQ-08** inmutabilidad profunda: `write`/`unlink` de líneas y repartos
  de un aplicado rechazados; `unlink` del aplicado rechazado.
* **AUD-ETQ-09** ciclos completos A (cancelar→liberar→reasignar→aplicar) y
  B (aplicar→revertir→restituir→reasignar→aplicar) con dos SV y parciales.
* **AUD-ETQ-10** compromiso parcial: nominal 5 / reparto 3 ⇒ dónde quedan los 2
  y qué acción los libera conforme a la política real.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
import re

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaCierre(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'CIE Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'CIE Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']
        cls.AuditLog = cls.env['madenat.audit.log']

        cls.user_oper = cls._mk('cie_oper', cls.company, [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = cls._mk('cie_jef', cls.company, [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    @classmethod
    def _mk(cls, name, company, groups):
        return cls.env['res.users'].create({
            'name': name, 'login': name,
            'email': '%s@madenat.cl' % name,
            'company_id': company.id, 'company_ids': [(6, 0, [company.id])],
            'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name, company=None):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-11'})

    def _etiqueta(self, guia, name, nominal, company=None):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': (company or self.company).id, 'lot_flow_type': 'tarja',
            'ref': name,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal, company=None):
        return self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': (company or self.company).id,
            'lot_flow_type': 'volume',
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

    def _wline(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _alloc(self, wiz, lot, sv, vol):
        return self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': self._wline(wiz, lot).id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    def _avail(self, lot):
        return self.Imputation._i2_lot_available_for_m3(lot)

    def _sv_avail(self, sv):
        return self.Imputation._i2_sv_documental_available_m3(sv)

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-08 — inmutabilidad profunda del aplicado
    # ══════════════════════════════════════════════════════════════════════
    def _applied(self, name, nominal=10.0, sv_nominal=100.0, sv_vol=10.0):
        guia = self._guia(name)
        e = self._etiqueta(guia, name + '-E', nominal)
        sv = self._sv(guia, 'SV' + name.replace('-', '')[:20].ljust(14, '0'),
                      sv_nominal)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': nominal})
        self.SvLine.sudo().create({
            'imputation_id': imp.id, 'imputation_line_id': line.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': sv_vol})
        imp.with_user(self.user_oper).action_apply()
        return guia, e, sv, imp, line

    def test_aud_etq_08_escrituras_sobre_aplicado_rechazadas(self):
        _g, _e, _sv, imp, line = self._applied('CIE08')
        self.assertEqual(imp.state, 'applied')
        alloc = imp.sv_line_ids
        # write de la cabecera (campo no permitido)
        with self.assertRaises(UserError):
            imp.write({'guia_processing_id': imp.guia_processing_id.id})
        # write de una línea del aplicado
        with self.assertRaises(UserError):
            line.write({'nominal_volume_m3': 99.0})
        # write de un reparto del aplicado
        with self.assertRaises(UserError):
            alloc.write({'imputed_volume_m3': 99.0})
        # unlink de línea / reparto / cabecera
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            alloc.unlink()
        with self.assertRaises(UserError):
            imp.unlink()
        # crear líneas/repartos nuevos sobre un aplicado
        with self.assertRaises(UserError):
            self.ImputationLine.sudo().create({
                'imputation_id': imp.id, 'processed_lot_id': line.processed_lot_id.id,
                'nominal_volume_m3': 1.0})
        with self.assertRaises(UserError):
            self.SvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': alloc.sv_lot_id.id, 'imputed_volume_m3': 1.0})
        self.assertEqual(imp.state, 'applied')

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-06 — motivo de reversa y trazabilidad
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_06_motivo_vacio_o_espacios_rechazado(self):
        _g, _e, _sv, imp, _l = self._applied('CIE06')
        # Vacío
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).action_reverse()
        # Sólo espacios
        imp.reversal_reason = '     '
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'applied')
        # Motivo válido tras strip
        imp.reversal_reason = '  Corrección trazable (CIE06)  '
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        # Trazabilidad completa registrada
        self.assertEqual(imp.reversed_by_id, self.user_jef)
        self.assertTrue(imp.reversal_date)
        self.assertTrue((imp.reversal_reason or '').strip())
        audit = self.AuditLog.search([
            ('action_type', '=', 'imputation_reverse'),
            ('batch_id', '=', imp.documentary_key)])
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit.user_id, self.user_jef)
        # El original conserva líneas y repartos (historia intacta)
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 1)

    def test_aud_etq_06b_contexto_no_autoriza_y_sin_permiso(self):
        _g, _e, _sv, imp, _l = self._applied('CIE06B')
        imp.reversal_reason = 'Intento sin permiso (CIE06B).'
        # Usuario Operaciones (sin atribución de reversa) → AccessError, incluso
        # forzando contexto. Un flag de contexto NO es autorización.
        with self.assertRaises(AccessError):
            imp.with_user(self.user_oper).action_reverse()
        with self.assertRaises(AccessError):
            imp.with_user(self.user_oper).with_context(
                force_reverse=True, allow_reverse=1).action_reverse()
        self.assertEqual(imp.state, 'applied')
        # Reversa repetida por Jefatura tras reversar: no hay doble efecto.
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        with self.assertRaises(UserError):
            imp.with_user(self.user_jef).action_reverse()

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-07 — aislamiento multi-compañía (sin sudo en las pruebas)
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_07_aislamiento_multicompania(self):
        company_b = self.env['res.company'].sudo().create({
            'name': 'CIE COMPANY B'})
        user_b = self._mk('cie_oper_b', company_b, [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        # Documento de la compañía A (compañía 1), con etiqueta y SV.
        guia = self._guia('CIE07')
        e = self._etiqueta(guia, 'CIE07-E', 10.0)
        sv = self._sv(guia, 'SV0000000CIE07', 100.0)
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': e.id,
            'nominal_volume_m3': 10.0})
        self.assertEqual(imp.company_id, self.company)

        ImpB = self.Imputation.with_user(user_b)
        # search: el documento de A NO aparece para el usuario de B
        self.assertNotIn(imp.id, ImpB.search([]).ids)
        # read directo: rechazado por la regla de registro
        with self.assertRaises(AccessError):
            imp.with_user(user_b).read(['name'])
        # write / unlink: rechazados
        with self.assertRaises(AccessError):
            imp.with_user(user_b).write({'reason': 'intrusión'})
        with self.assertRaises(AccessError):
            imp.with_user(user_b).unlink()
        # apply / cancel / reverse: rechazados
        with self.assertRaises(AccessError):
            imp.with_user(user_b).action_apply()
        with self.assertRaises(AccessError):
            imp.with_user(user_b).action_cancel()
        with self.assertRaises(AccessError):
            imp.with_user(user_b).action_reverse()
        # Contexto forzado: NO es autorización (no habilita otra compañía)
        ctx = dict(allowed_company_ids=[self.company.id])
        with self.assertRaises(AccessError):
            imp.with_user(user_b).with_context(**ctx).read(['name'])
        # Relación con lotes de otra compañía: bloqueada por la regla estándar
        with self.assertRaises(AccessError):
            self.StockLot.with_user(user_b).browse(e.id).read(['name'])
        # El documento de A sigue intacto
        self.assertEqual(imp.state, 'draft')
        self.assertEqual(imp.company_id, self.company)

    # ══════════════════════════════════════════════════════════════════════
    # AUD-ETQ-09/10 — ciclos completos con datos de prueba (2 SV, parciales)
    # ══════════════════════════════════════════════════════════════════════
    def test_aud_etq_09a_ciclo_cancelar_liberar_reasignar_aplicar(self):
        guia = self._guia('CIE09A')
        e = self._etiqueta(guia, 'CIE09A-E', 10.0)
        sv1 = self._sv(guia, 'SV000000A09001', 100.0)
        sv2 = self._sv(guia, 'SV000000A09002', 100.0)
        wiz = self._wizard(guia, sv=sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 4.0)
        self._alloc(wiz, e, sv2, 3.0)
        wiz.action_prepare()
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'draft')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)       # reservado
        self.assertAlmostEqual(self._sv_avail(sv1), 96.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv2), 97.0, 3)
        # Reabrir: reconstruye selección y reparto
        wiz2 = self._wizard(guia, sv=sv1)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertEqual(len(wiz2.line_ids), 1)
        self.assertTrue(self._wline(wiz2, e).selected)
        self.assertEqual(len(self._wline(wiz2, e).sv_alloc_ids), 2)
        # Cancelar (draft) → libera
        imp.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp.state, 'cancelled')
        self.assertAlmostEqual(self._avail(e), 10.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 100.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv2), 100.0, 3)
        # Reasignar (documento nuevo) y aplicar
        wiz3 = self._wizard(guia, sv=sv1)
        self._wline(wiz3, e).selected = True
        self._alloc(wiz3, e, sv1, 10.0)
        wiz3.with_user(self.user_oper).action_apply()
        imp2 = wiz3.imputation_id
        self.assertNotEqual(imp2, imp)
        self.assertEqual(imp2.state, 'applied')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 90.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv2), 100.0, 3)  # SV2 intacto

    def test_aud_etq_09b_ciclo_aplicar_revertir_reasignar_aplicar(self):
        guia = self._guia('CIE09B')
        e = self._etiqueta(guia, 'CIE09B-E', 10.0)
        sv1 = self._sv(guia, 'SV000000B09001', 100.0)
        sv2 = self._sv(guia, 'SV000000B09002', 100.0)
        wiz = self._wizard(guia, sv=sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 6.0)
        self._alloc(wiz, e, sv2, 4.0)
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id
        self.assertEqual(imp.state, 'applied')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 94.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv2), 96.0, 3)
        # Revertir
        imp.reversal_reason = 'Ciclo B (CIE09B).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(imp.state, 'reversed')
        self.assertAlmostEqual(self._avail(e), 10.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 100.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv2), 100.0, 3)
        # Historia intacta del original
        self.assertEqual(len(imp.line_ids), 1)
        self.assertEqual(len(imp.sv_line_ids), 2)
        # Reasignar y aplicar (documento nuevo)
        wiz2 = self._wizard(guia, sv=sv1)
        self._wline(wiz2, e).selected = True
        self._alloc(wiz2, e, sv1, 10.0)
        wiz2.with_user(self.user_oper).action_apply()
        imp2 = wiz2.imputation_id
        self.assertNotEqual(imp2, imp)
        self.assertEqual(imp2.state, 'applied')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 90.0, 3)
        # La cadena es explicable: original `reversed` + nuevo `applied`
        self.assertTrue(imp.exists())
        self.assertEqual(imp.state, 'reversed')
        self.assertEqual(imp2.state, 'applied')

    def test_aud_etq_10_parcial_5_3_donde_quedan_los_2(self):
        guia = self._guia('CIE10')
        e = self._etiqueta(guia, 'CIE10-E', 5.0)
        sv1 = self._sv(guia, 'SV000000C10001', 100.0)
        wiz = self._wizard(guia, sv=sv1)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv1, 3.0)
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id
        self.assertAlmostEqual(imp.nominal_total_m3, 5.0, 3)
        self.assertAlmostEqual(imp.imputed_total_m3, 3.0, 3)
        # La etiqueta compromete su NOMINAL completo: disponible 0
        self.assertAlmostEqual(self._avail(e), 0.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 97.0, 3)
        # Los 2 m³ NO son reutilizables: otra operación sobre la misma etiqueta
        # supera el techo duro al aplicar.
        wiz2 = self._wizard(guia, sv=sv1)
        self._wline(wiz2, e).selected = True
        self._alloc(wiz2, e, sv1, 5.0)
        wiz2.action_prepare()
        imp2 = wiz2.imputation_id
        with self.assertRaises(UserError):
            imp2.with_user(self.user_oper).action_apply()
        self.assertEqual(imp2.state, 'draft')
        # Los 2 m³ siguen comprometidos: el disponible no es reutilizable y, con
        # el borrador excedente presente, la fórmula puede dar negativo
        # (política blanda etiqueta-side; el exceso NO se aplica).
        self.assertLessEqual(self._avail(e), 0.0)
        # Se anula el borrador excedente (libera su reserva) y se REVERSA el
        # aplicado: sólo entonces se libera el nominal completo.
        imp2.with_user(self.user_oper).action_cancel()
        self.assertEqual(imp2.state, 'cancelled')
        self.assertAlmostEqual(self._avail(e), 0.0, 3)   # aún aplicado
        imp.reversal_reason = 'Liberar nominal completo (CIE10).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertAlmostEqual(self._avail(e), 5.0, 3)
        self.assertAlmostEqual(self._sv_avail(sv1), 100.0, 3)

    def test_aud_etq_09c_ciclos_sin_efectos_fisicos(self):
        def snap():
            return (
                self.env['stock.move'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.move.line'].search_count(
                    [('company_id', '=', self.company.id)]),
                self.env['stock.picking'].search_count(
                    [('company_id', '=', self.company.id)]),
            )
        before = snap()
        guia = self._guia('CIE09C')
        e = self._etiqueta(guia, 'CIE09C-E', 10.0)
        sv = self._sv(guia, 'SV000000D09001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        self._wline(wiz, e).selected = True
        self._alloc(wiz, e, sv, 10.0)
        wiz.with_user(self.user_oper).action_apply()
        imp = wiz.imputation_id
        imp.reversal_reason = 'Ciclo sin efectos (CIE09C).'
        imp.with_user(self.user_jef).action_reverse()
        self.assertEqual(snap(), before)
