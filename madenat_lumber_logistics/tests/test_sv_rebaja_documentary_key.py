# -*- coding: utf-8 -*-
"""S1 — Clave documental con las ETIQUETAS SELECCIONADAS (FASE 10, 2026-10-15).

Defecto **F1** (causa raíz) del diagnóstico
``DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015``: ``_i2_signature()``
sólo incluía los **repartos SV**, no las etiquetas seleccionadas, y
``_i2_get_or_create()`` buscaba por ``documentary_key`` **sin filtrar estado**
(``documentary_key`` es UNIQUE). Cualquier preparación de la guía 1198 **sin
reparto** colisionaba con el documento APLICADO ``IMP02220`` y terminaba en
``UserError``: las etiquetas nunca se registraban.

Cubre:

* **T1** — guía con documento aplicado/anulado previo y selección distinta ⇒ se
  crea un documento NUEVO y se registran las etiquetas (sin colisión).
* **T4** — idempotencia: repetir la preparación con la MISMA selección reutiliza
  el mismo borrador (sin duplicar).
* **T5** — selecciones distintas ⇒ claves distintas.
* **E7** — el caso sano sigue en verde («Rebajado documental» correcto).
* La **clave base histórica** (``signature=''``) conserva su receta exacta.

Datos 100 % transaccionales (``TransactionCase``, rollback).
"""
import hashlib

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaDocumentaryKey(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        wh = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        uom = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'DK Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom.id, 'uom_po_id': uom.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'DK Supplier', 'is_company': True})
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.user_oper = cls.env['res.users'].create({
            'name': 'dk_oper', 'login': 'dk_oper',
            'email': 'dk_oper@madenat.cl', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
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

    def _prepare(self, guia, sv, etq, vol):
        """Selecciona la etiqueta, fija el reparto y guarda el borrador."""
        wiz = self._wizard(guia, sv)
        line = self._wline(wiz, etq)
        line.selected = True
        line.cantidad_asignar_m3 = vol
        wiz.sudo().action_prepare()
        return wiz

    @staticmethod
    def _base_key_expected(guia):
        """Receta HISTÓRICA de la clave base (``signature=''``)."""
        raw = 'I2|%s|%s|%s' % (guia.id, 0, '')
        digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16].upper()
        return 'IMP-%s-%s' % (guia.id, digest)

    # ── T5 / F1: la firma incluye las etiquetas seleccionadas ──────────────
    def test_dk_01_firma_incluye_etiquetas_seleccionadas(self):
        guia = self._guia('DK-01')
        e1 = self._etq(guia, 'DK-01-E1', 10.0)
        e2 = self._etq(guia, 'DK-01-E2', 10.0)
        sv = self._sv(guia, 'SV0000DK0001', 100.0)
        wiz = self._wizard(guia, sv)
        # Sin reparto, la firma ya distingue QUÉ etiqueta se registra.
        self._wline(wiz, e1).selected = True
        sig1 = wiz._i2_signature()
        self.assertIn('L%s:' % e1.id, sig1)
        self.assertNotIn('L%s:' % e2.id, sig1)
        # Cambiar la selección CAMBIA la firma (antes quedaba vacía).
        self._wline(wiz, e1).selected = False
        self._wline(wiz, e2).selected = True
        sig2 = wiz._i2_signature()
        self.assertNotEqual(sig1, sig2)
        self.assertIn('L%s:' % e2.id, sig2)

    def test_dk_02_clave_base_historica_intacta(self):
        """La receta base (``signature=''``) NO cambia: clave histórica igual."""
        guia = self._guia('DK-02')
        expected = self._base_key_expected(guia)
        self.assertEqual(
            self.Imputation._i2_build_documentary_key(guia, None, ''), expected)
        # El parámetro nuevo del discriminador es OPCIONAL y por defecto vacío.
        self.assertEqual(
            self.Imputation._i2_build_documentary_key(
                guia, None, '', discriminator=''), expected)

    # ── T1 / E1-E2-E3: aplicado previo + selección distinta ⇒ nuevo doc ────
    def test_dk_03_aplicado_previo_seleccion_distinta_crea_documento(self):
        guia = self._guia('DK-03')
        e1 = self._etq(guia, 'DK-03-E1', 10.0)
        e2 = self._etq(guia, 'DK-03-E2', 10.0)
        sv = self._sv(guia, 'SV0000DK0003', 100.0)
        wiz = self._prepare(guia, sv, e1, 10.0)
        applied = wiz.imputation_id
        applied.with_user(self.user_oper).action_apply()
        self.assertEqual(applied.state, 'applied')
        # Selección DISTINTA para la misma guía: no colisiona con el aplicado.
        wiz2 = self._prepare(guia, sv, e2, 5.0)
        new_doc = wiz2.imputation_id
        self.assertNotEqual(new_doc, applied)
        self.assertEqual(new_doc.state, 'draft')
        self.assertEqual(new_doc.line_ids.processed_lot_id, e2)
        self.assertNotEqual(new_doc.documentary_key, applied.documentary_key)
        # El aplicado no se altera.
        applied.invalidate_recordset()
        self.assertEqual(applied.state, 'applied')

    def test_dk_03b_legacy_anulado_no_se_adopta_por_clave_base(self):
        """Perfil IMP04823: documento ANULADO con la clave base (firma vacía).

        Antes de S1, preparar la misma guía **sin reparto** producía la MISMA
        clave (firma vacía) y `_i2_get_or_create` devolvía el documento anulado
        ⇒ `UserError` «fue anulado». Con la firma que incluye la selección, la
        operación es nueva y se registra.
        """
        guia = self._guia('DK-03B')
        e1 = self._etq(guia, 'DK-03B-E1', 10.0)
        sv = self._sv(guia, 'SV0000DK003B', 100.0)
        legacy = self.Imputation.sudo().create({
            'guia_processing_id': guia.id,
            'documentary_key': self._base_key_expected(guia),
            'state': 'cancelled'})
        self.assertEqual(legacy.documentary_key, self._base_key_expected(guia))
        wiz = self._wizard(guia, sv)
        line = self._wline(wiz, e1)
        line.selected = True                 # sin reparto (E1 del diagnóstico)
        wiz.sudo().action_prepare()          # NO debe lanzar UserError
        new_doc = wiz.imputation_id
        self.assertNotEqual(new_doc, legacy)
        self.assertNotEqual(new_doc.documentary_key, legacy.documentary_key)
        self.assertEqual(new_doc.line_ids.processed_lot_id, e1)
        legacy.invalidate_recordset()
        self.assertEqual(legacy.state, 'cancelled')

    # ── T1: anulado previo ⇒ documento NUEVO con clave distinta y trazable ─
    def test_dk_04_anulado_previo_crea_documento_nuevo_trazable(self):
        guia = self._guia('DK-04')
        e1 = self._etq(guia, 'DK-04-E1', 10.0)
        sv = self._sv(guia, 'SV0000DK0004', 100.0)
        wiz = self._prepare(guia, sv, e1, 4.0)
        cancelled = wiz.imputation_id
        cancelled_key = cancelled.documentary_key
        cancelled.with_user(self.user_oper).action_cancel()
        self.assertEqual(cancelled.state, 'cancelled')
        # Misma selección y mismo reparto ⇒ misma clave base (ocupada).
        wiz2 = self._wizard(guia, sv)
        line = self._wline(wiz2, e1)
        line.selected = True
        line.cantidad_asignar_m3 = 4.0
        self.assertEqual(
            self.Imputation._i2_build_documentary_key(
                guia, wiz2.processor_id, wiz2._i2_signature()), cancelled_key)
        wiz2.sudo().action_prepare()
        new_doc = wiz2.imputation_id
        self.assertNotEqual(new_doc, cancelled)
        self.assertNotEqual(new_doc.documentary_key, cancelled_key)
        # Clave NUEVA determinista y TRAZABLE: se puede reconstruir a partir del
        # documento terminal que ocupaba la clave (discriminador = su id; el
        # id va en el material hasheado, no literal en la clave).
        expected = self.Imputation._i2_build_documentary_key(
            guia, wiz2.processor_id, wiz2._i2_signature(),
            discriminator=str(cancelled.id))
        self.assertEqual(new_doc.documentary_key, expected)
        self.assertNotEqual(expected, cancelled_key)
        self.assertNotEqual(
            expected,
            self.Imputation._i2_build_documentary_key(
                guia, wiz2.processor_id, wiz2._i2_signature()))
        # El anulado queda INTACTO.
        cancelled.invalidate_recordset()
        self.assertEqual(cancelled.state, 'cancelled')
        self.assertEqual(cancelled.documentary_key, cancelled_key)

    def test_dk_05_misma_seleccion_ya_aplicada_mensaje_claro(self):
        guia = self._guia('DK-05')
        e1 = self._etq(guia, 'DK-05-E1', 10.0)
        sv = self._sv(guia, 'SV0000DK0005', 100.0)
        wiz = self._prepare(guia, sv, e1, 10.0)
        applied = wiz.imputation_id
        applied.with_user(self.user_oper).action_apply()
        wiz2 = self._wizard(guia, sv)
        line = self._wline(wiz2, e1)
        line.selected = True
        line.cantidad_asignar_m3 = 10.0
        try:
            wiz2.sudo().action_prepare()
        except UserError as exc:
            message = str(exc)
        else:
            self.fail('Se esperaba UserError «ya aplicada con esta selección»')
        self.assertIn('ya se aplicó', message)
        self.assertIn(applied.name, message)
        # Sin duplicar: un único documento para la guía.
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)]), 1)

    # ── T4 / T5: idempotencia y unicidad ──────────────────────────────────
    def test_dk_06_idempotencia_misma_seleccion_reutiliza_borrador(self):
        guia = self._guia('DK-06')
        e1 = self._etq(guia, 'DK-06-E1', 10.0)
        sv = self._sv(guia, 'SV0000DK0006', 100.0)
        first = self._prepare(guia, sv, e1, 4.0).imputation_id
        again = self._prepare(guia, sv, e1, 4.0).imputation_id
        self.assertEqual(first, again)
        self.assertEqual(len(again.line_ids), 1)
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)]), 1)

    def test_dk_07_dos_preparaciones_un_solo_documento(self):
        """Dos asistentes abiertos a la vez: un ÚNICO documento (UNIQUE)."""
        guia = self._guia('DK-07')
        e1 = self._etq(guia, 'DK-07-E1', 10.0)
        sv = self._sv(guia, 'SV0000DK0007', 100.0)
        w1 = self._wizard(guia, sv)
        w2 = self._wizard(guia, sv)
        self.assertFalse(w1.imputation_id)
        self.assertFalse(w2.imputation_id)
        self._wline(w1, e1).selected = True
        self._wline(w1, e1).cantidad_asignar_m3 = 4.0
        w1.sudo().action_prepare()
        doc = w1.imputation_id
        w3 = self._wizard(guia, sv)                  # reutiliza el trabajo
        self.assertEqual(w3.imputation_id, doc)
        self._wline(w3, e1).cantidad_asignar_m3 = 4.0
        w3.sudo().action_prepare()
        self.assertEqual(w3.imputation_id, doc)
        self.assertEqual(self.Imputation.sudo().search_count(
            [('guia_processing_id', '=', guia.id)]), 1)

    # ── E7: el caso sano sigue en verde ───────────────────────────────────
    def test_dk_08_caso_sano_aplica_y_registra(self):
        guia = self._guia('DK-08')
        e1 = self._etq(guia, 'DK-08-E1', 3.263)
        sv = self._sv(guia, 'SV0000DK0008', 100.0)
        wiz = self._prepare(guia, sv, e1, 1.781)
        imp = wiz.imputation_id
        self.assertNotEqual(wiz._i2_signature(), '')   # firma no vacía
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertTrue(imp.audit_hash)
        self.assertEqual(len(imp.sv_line_ids), 1)
        self.assertAlmostEqual(
            self.Imputation._i2_sv_documental_assigned_m3(sv), 1.781, 3)
