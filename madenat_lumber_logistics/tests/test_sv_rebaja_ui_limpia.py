# -*- coding: utf-8 -*-
"""Interfaz clara y concisa del asistente «Registrar rebaja» (2026-10-10).

Cubre, sobre el MISMO asistente y sin efectos físicos:

* CAB   — cabecera única: seleccionadas ≠ con reparto preparado ≠ total;
* EDIT  — «A asignar» editable integrado con el reparto (sin saldo paralelo);
* MED   — medidas legibles que distinguen etiquetas repetidas;
* ETQ   — etiqueta limpia (sin el nombre concatenado del lote);
* SIN   — causa REAL del saldo cero (aplicado/reservado/sin capacidad);
* USE   — «Usar disponible» no sobrescribe cantidades editadas;
* MULTI — columna «SV destino» sólo con varios SV (flag multi_sv);
* ARCH  — vista: columnas, etiquetas de botones y textos de una línea.

Datos 100 % transaccionales (TransactionCase, rollback).
"""
import re

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaUiLimpia(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'UI Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'UI Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.PackingLine = cls.env['madenat.guia.processing.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.ImputationSvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardLine = cls.env['madenat.sv.imputation.wizard.line']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']
        # FASE 11 (A-1): el estado `applied` sólo se alcanza con la acción
        # OFICIAL, que exige un rol de Operaciones/Jefatura/Gerencia.
        cls.user_oper = cls.env['res.users'].create({
            'name': 'ui_limpia_oper', 'login': 'ui_limpia_oper',
            'email': 'ui_limpia_oper@madenat.cl',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref(
                    'madenat_lumber_core.group_madenat_operaciones').id])]})

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _guia(self, name):
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-10'})

    def _packing_line(self, guia, lot_name, sku, esp, anc, largo, pieces, vol):
        return self.PackingLine.sudo().create({
            'processing_id': guia.id, 'product_id': self.product.id,
            'lot_name': lot_name, 'sku_original': sku,
            'espesor_nominal_mm': esp, 'ancho_nominal_mm': anc,
            'largo_nominal_m': largo, 'pieces': pieces, 'vol_purchase_m3': vol})

    def _lot(self, guia, lot_name, sku, esp, anc, largo, pieces, vol,
             ref=True):
        digits = re.sub(r'[^0-9]', '', guia.name or '')
        name = ' '.join(p for p in (lot_name, sku, digits) if p)
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': self.product.id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'ref': lot_name if ref else False,
            'espesor_mm': esp, 'ancho_mm': anc, 'largo_m': largo,
            'piezas': pieces, 'volume_purchase_m3': vol,
            'vol_shipment_m3': vol})
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

    def _line(self, wiz, lot):
        return wiz.line_ids.filtered(lambda l: l.processed_lot_id == lot)

    def _alloc(self, wiz, wline, sv, vol):
        return self.WizardSvLine.sudo().create({
            'wizard_id': wiz.id, 'wizard_line_id': wline.id,
            'sv_lot_id': sv.id, 'imputed_volume_m3': vol})

    def _imputation(self, guia, etiqueta, sv, vol, state='draft',
                    line_nominal=None):
        # El estado se fija al crear para no chocar con la regla de una sola
        # imputación de trabajo por guía (draft/pending). La etiqueta debe
        # pertenecer a la guía del documento (D10): lot_ids es M2M.
        if etiqueta not in guia.lot_ids:
            guia.sudo().write({'lot_ids': [(4, etiqueta.id)]})
        imp = self.Imputation.sudo().create({'guia_processing_id': guia.id})
        line = self.ImputationLine.sudo().create({
            'imputation_id': imp.id, 'processed_lot_id': etiqueta.id,
            'nominal_volume_m3': (line_nominal if line_nominal is not None
                                  else etiqueta.volume_purchase_m3)})
        if sv:
            self.ImputationSvLine.sudo().create({
                'imputation_id': imp.id, 'imputation_line_id': line.id,
                'sv_lot_id': sv.id, 'imputed_volume_m3': vol})
        if state == 'applied':
            # FASE 11 (A-1): el estado se alcanza por la acción OFICIAL; la
            # escritura directa de `state` está prohibida.
            imp.with_user(self.user_oper).action_apply()
            imp.invalidate_recordset()
        return imp

    # ══════════════════════════════════════════════════════════════════════
    # CAB — cabecera única y distinción de totales
    # ══════════════════════════════════════════════════════════════════════
    def test_cab_01_seleccionadas_no_es_reparto_preparado(self):
        guia = self._guia('UI-CAB01')
        self._lot(guia, 'D101', 'SKU-101', 45.0, 125.0, 2.9, 100, 5.0)
        self._lot(guia, 'D102', 'SKU-102', 45.0, 145.0, 3.0, 60, 3.0)
        self._lot(guia, 'D103', 'SKU-103', 50.0, 100.0, 2.5, 40, 2.0)
        sv = self._sv(guia, 'SV00000130001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        wiz.action_select_all()
        # 3 seleccionadas pero 0 con reparto válido: no se presentan como 3.
        self.assertEqual(wiz.selected_line_count, 3)
        self.assertEqual(wiz.prepared_line_count, 0)
        self.assertAlmostEqual(wiz.prepared_total_m3, 0.0, 3)
        self.assertEqual(wiz.packing_pieces_total, 200)
        self.assertAlmostEqual(
            wiz.packing_documental_volume_total_m3, 10.0, 3)
        self.assertIn('3 seleccionadas', wiz.assigned_summary)
        self.assertIn('0 etiquetas', wiz.assigned_summary)
        # Con un reparto real el subtotal del SV de trabajo sube.
        line = self._line(wiz, wiz.line_ids[0].processed_lot_id)
        self._alloc(wiz, line, sv, 2.5)
        self.assertEqual(wiz.prepared_line_count, 1)
        self.assertAlmostEqual(wiz.prepared_total_m3, 2.5, 3)
        self.assertIn('2.500', wiz.assigned_summary)

    # ══════════════════════════════════════════════════════════════════════
    # EDIT — «A asignar» editable integrado con el reparto
    # ══════════════════════════════════════════════════════════════════════
    def test_edit_01_a_asignar_editable_crea_reparto(self):
        guia = self._guia('UI-EDIT01')
        self._packing_line(guia, 'D801', 'SKU-801', 45.0, 125.0, 2.9, 100, 5.0)
        e = self._lot(guia, 'D801', 'SKU-801', 45.0, 125.0, 2.9, 100, 5.0)
        sv = self._sv(guia, 'SV00000131001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = self._line(wiz, e)
        self.assertFalse(line.sv_alloc_ids)
        line.cantidad_asignar_m3 = 4.0
        line.invalidate_recordset()
        line = self._line(wiz, e)
        allocs = line.sv_alloc_ids.filtered(lambda a: a.sv_lot_id == sv)
        self.assertEqual(len(allocs), 1)
        self.assertAlmostEqual(allocs.imputed_volume_m3, 4.0, 3)
        self.assertTrue(line.selected)
        self.assertAlmostEqual(line.cantidad_asignar_m3, 4.0, 3)
        self.assertAlmostEqual(wiz.prepared_total_m3, 4.0, 3)
        self.assertEqual(wiz.prepared_line_count, 1)

    def test_edit_02_cero_borra_solo_su_reparto(self):
        guia = self._guia('UI-EDIT02')
        e = self._lot(guia, 'D802', 'SKU-802', 45.0, 125.0, 2.9, 100, 5.0)
        sv = self._sv(guia, 'SV00000131002', 100.0)
        sv2 = self._sv(guia, 'SV00000131003', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = self._line(wiz, e)
        line.selected = True
        self._alloc(wiz, line, sv, 3.0)
        other = self._alloc(wiz, line, sv2, 2.0)
        line.invalidate_recordset()
        line = self._line(wiz, e)
        line.cantidad_asignar_m3 = 0.0
        line.invalidate_recordset()
        line = self._line(wiz, e)
        self.assertFalse(line.sv_alloc_ids.filtered(
            lambda a: a.sv_lot_id == sv))
        self.assertEqual(len(line.sv_alloc_ids.filtered(
            lambda a: a.sv_lot_id == sv2)), 1)
        self.assertAlmostEqual(other.imputed_volume_m3, 2.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # MED / ETQ — identificación y medidas
    # ══════════════════════════════════════════════════════════════════════
    def test_med_01_medidas_legibles(self):
        guia = self._guia('UI-MED01')
        self._packing_line(guia, 'D901', 'SKU-901', 45.0, 125.0, 2.9, 100, 5.0)
        self._lot(guia, 'D901', 'SKU-901', 45.0, 125.0, 2.9, 100, 5.0)
        wiz = self._wizard(guia)
        self.assertEqual(wiz.line_ids[0].medidas, '45 × 125 mm · 2,900 m')

    def test_etq_01_etiqueta_limpia_no_concatenada(self):
        guia = self._guia('UI-ETQ01')
        self._packing_line(guia, 'D7670', 'SKU-X', 45.0, 125.0, 3.0, 100, 5.0)
        e = self._lot(guia, 'D7670', 'SKU-X', 45.0, 125.0, 3.0, 100, 5.0)
        wiz = self._wizard(guia)
        line = self._line(wiz, e)
        self.assertEqual(line.etiqueta, 'D7670')
        self.assertNotEqual(line.etiqueta, e.name)   # no el nombre concatenado
        self.assertIn('D7670', e.name)               # el técnico sigue completo

    def test_etq_02_sin_packing_usa_referencia(self):
        guia = self._guia('UI-ETQ02')
        e = self._lot(guia, 'D555', 'SKU-555', 45.0, 125.0, 3.0, 10, 1.0)
        wiz = self._wizard(guia)
        self.assertEqual(self._line(wiz, e).etiqueta, 'D555')

    def test_etq_03_repetida_se_distingue(self):
        guia = self._guia('UI-ETQ03')
        e1 = self._lot(guia, 'D7719', 'SKU-A', 45.0, 145.0, 3.25, 165, 3.445)
        e2 = self._lot(guia, 'D7719', 'SKU-B', 45.0, 145.0, 3.2, 10, 0.212)
        wiz = self._wizard(guia)
        l1, l2 = self._line(wiz, e1), self._line(wiz, e2)
        self.assertEqual(l1.etiqueta, l2.etiqueta)          # misma etiqueta
        self.assertNotEqual(l1.medidas, l2.medidas)         # medidas distintas

    # ══════════════════════════════════════════════════════════════════════
    # SIN — causa real del saldo cero
    # ══════════════════════════════════════════════════════════════════════
    def test_sin_01_causas_disponibilidad(self):
        guia = self._guia('UI-SIN01')
        e_free = self._lot(guia, 'D-A', 'SKU-A', 45.0, 125.0, 3.0, 10, 5.0)
        e_zero = self._lot(guia, 'D-B', 'SKU-B', 45.0, 125.0, 3.0, 0, 0.0)
        e_res = self._lot(guia, 'D-C', 'SKU-C', 45.0, 125.0, 3.0, 10, 4.0)
        e_app = self._lot(guia, 'D-D', 'SKU-D', 45.0, 125.0, 3.0, 10, 6.0)
        sv = self._sv(guia, 'SV00000132001', 100.0)
        # Consumo por otro documento (guía ajena, no la del asistente):
        # reservado (draft) y aplicado.
        guia_cons = self._guia('UI-SIN01-CONS')
        # Aplicada primero (deja de ser «trabajo»); reservada después.
        self._imputation(guia_cons, e_app, sv, 6.0, state='applied')
        self._imputation(guia_cons, e_res, sv, 4.0, state='draft')
        wiz = self._wizard(guia, sv=sv)
        self.assertEqual(
            self._line(wiz, e_free).disponibilidad_estado, 'available')
        self.assertEqual(
            self._line(wiz, e_zero).disponibilidad_estado, 'no_capacity')
        self.assertEqual(
            self._line(wiz, e_res).disponibilidad_estado, 'reserved')
        self.assertEqual(
            self._line(wiz, e_app).disponibilidad_estado, 'applied')

    def test_sin_02_seleccionar_todas_informa_no_asignables(self):
        guia = self._guia('UI-SIN02')
        self._lot(guia, 'D-E', 'SKU-E', 45.0, 125.0, 3.0, 10, 5.0)
        e_res = self._lot(guia, 'D-F', 'SKU-F', 45.0, 125.0, 3.0, 10, 4.0)
        sv = self._sv(guia, 'SV00000132002', 100.0)
        guia_cons = self._guia('UI-SIN02-CONS')
        self._imputation(guia_cons, e_res, sv, 4.0, state='draft')
        wiz = self._wizard(guia, sv=sv)
        wiz.action_select_all()
        self.assertEqual(wiz.selected_line_count, 2)
        self.assertEqual(wiz.not_assignable_line_count, 1)
        self.assertTrue(wiz.no_availability_note)
        self.assertIn('1 de las etiquetas', wiz.no_availability_note)

    # ══════════════════════════════════════════════════════════════════════
    # USE — «Usar disponible» no sobrescribe lo editado
    # ══════════════════════════════════════════════════════════════════════
    def test_use_01_no_sobrescribe_editado(self):
        guia = self._guia('UI-USE01')
        e1 = self._lot(guia, 'D-G', 'SKU-G', 45.0, 125.0, 3.0, 10, 10.0)
        e2 = self._lot(guia, 'D-H', 'SKU-H', 45.0, 125.0, 3.0, 10, 10.0)
        sv = self._sv(guia, 'SV00000133001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        l1, l2 = self._line(wiz, e1), self._line(wiz, e2)
        l1.selected = True
        l2.selected = True
        a1 = self._alloc(wiz, l1, sv, 7.0)   # cantidad editada por el usuario
        a2 = self._alloc(wiz, l2, sv, 0.0)   # aún sin cantidad
        wiz.action_use_available()
        self.assertAlmostEqual(a1.imputed_volume_m3, 7.0, 3)
        self.assertAlmostEqual(a2.imputed_volume_m3, 10.0, 3)

    # ══════════════════════════════════════════════════════════════════════
    # MULTI — SV destino sólo con varios SV
    # ══════════════════════════════════════════════════════════════════════
    def test_multi_01_flag_segun_numero_de_sv(self):
        guia = self._guia('UI-MULTI01')
        e = self._lot(guia, 'D-I', 'SKU-I', 45.0, 125.0, 3.0, 10, 10.0)
        sv = self._sv(guia, 'SV00000134001', 100.0)
        sv2 = self._sv(guia, 'SV00000134002', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = self._line(wiz, e)
        line.selected = True
        self._alloc(wiz, line, sv, 4.0)
        self.assertFalse(wiz.multi_sv)
        self._alloc(wiz, line, sv2, 3.0)
        self.assertTrue(wiz.multi_sv)
        self.assertAlmostEqual(wiz.prepared_total_m3, 4.0, 3)   # sólo trabajo
        self.assertAlmostEqual(wiz.assigned_total_m3, 7.0, 3)   # todos

    # ══════════════════════════════════════════════════════════════════════
    # ARCH — la vista presenta el material y los textos breves
    # ══════════════════════════════════════════════════════════════════════
    def test_arch_01_columnas_botones_y_textos(self):
        form = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        root = etree.fromstring(form.arch.encode())

        def btn(label):
            return root.xpath(".//button[@string=%s]" % repr(label))
        # Etiquetas breves de botones (§4).
        for label in ('Seleccionar todas', 'Quitar selección',
                      'Preparar asignación', 'Usar disponible'):
            self.assertTrue(btn(label), 'falta botón %s' % label)
        # UI (2026-10-11): acciones operativas en el <header> nativo; el <footer>
        # no se renderiza en el formulario amplio (target=current).
        for label in ('Guardar', 'Aplicar', 'Volver'):
            self.assertTrue(btn(label), 'falta botón %s' % label)
        self.assertIsNotNone(root.find('.//header'))
        self.assertIsNone(root.find('.//footer'))
        # Opciones avanzadas agrupadas (no en la botonera principal).
        for label in ('Abrir documento', 'Dejar pendiente', 'Proponer FIFO'):
            self.assertTrue(btn(label), 'falta opción avanzada %s' % label)
        # «Preparar asignación» aclara que no aplica la rebaja.
        prepare = btn('Preparar asignación')[0]
        self.assertIn('no aplica la rebaja', prepare.get('help') or '')

        # Tabla de materiales: «A asignar» editable + identidad limpia.
        mat = root.xpath(".//field[@name='line_ids']//field")
        names = [n.get('name') for n in mat]
        self.assertIn('etiqueta', names)
        self.assertIn('medidas' and 'sku_origen', names)
        meter = [n for n in mat if n.get('name') == 'cantidad_asignar_m3'][0]
        self.assertNotEqual(meter.get('readonly'), '1')

        # Asignación a SV: columnas pedidas y SV destino condicional.
        svl = root.xpath(".//field[@name='sv_line_ids']//field")
        sv_names = [n.get('name') for n in svl]
        for col in ('etiqueta', 'medidas', 'etiqueta_disponible_m3',
                    'imputed_volume_m3'):
            self.assertIn(col, sv_names)
        destino = [n for n in svl if n.get('name') == 'sv_lot_id'][0]
        # HOTFIX OwlError: la expresión usa el contexto del PADRE, no la fila.
        self.assertEqual(
            destino.get('column_invisible'), 'not parent.multi_sv')
        self.assertNotIn('wizard_id', destino.get('column_invisible') or '')

        # Texto de ayuda de una línea y aviso documental breve.
        text = etree.tostring(root, encoding='unicode')
        self.assertIn('Sólo Aplicar registra la rebaja.', text)
        self.assertIn('Rebaja documental: no mueve stock físico.', text)
        # Sin explicaciones de implementación en el TEXTO visible.
        visible = ' '.join(root.xpath('//text()'))
        self.assertNotIn('sv_line_ids', visible)
        self.assertNotIn('nominal comprometido', visible)

    def test_arch_02_cabecera_unica_sin_repetir_saldo_por_fila(self):
        form = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        root = etree.fromstring(form.arch.encode())
        svl = root.xpath(".//field[@name='sv_line_ids']//field")
        sv_names = [n.get('name') for n in svl]
        # El saldo completo del SV no se repite en cada fila.
        self.assertNotIn('sv_saldo_documental_m3', sv_names)
        self.assertNotIn('sv_nominal_m3', sv_names)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvRebajaOwlColumnInvisible(TransactionCase):
    """HOTFIX OwlError — `column_invisible` de «SV destino» fuera de contexto.

    `ListRenderer.evalColumnInvisible` evalúa la expresión con el contexto del
    PADRE (formulario), no con cada fila: por eso `wizard_id` no está definido y
    debe usarse `parent.multi_sv`. Casos A–E. La renderización real queda
    pendiente (sin navegador).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'OWL Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'OWL Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.WizardSvLine = cls.env['madenat.sv.imputation.wizard.sv.line']

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
            'ref': name, 'volume_purchase_m3': nominal,
            'vol_shipment_m3': nominal})
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

    def test_owl_01_arch_sin_campos_de_fila(self):
        # Invariante de la vista EFECTIVA: ningún column_invisible usa wizard_id.
        form = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        root = etree.fromstring(form.arch.encode())
        nodes = root.xpath('//*[@column_invisible]')
        self.assertTrue(nodes, 'no hay column_invisible que verificar')
        for node in nodes:
            self.assertNotIn('wizard_id', node.get('column_invisible'))

    def test_owl_02_padre_carga_multi_sv(self):
        # El formulario padre carga `multi_sv` (para `parent.multi_sv`).
        form = self.env.ref(
            '%s.view_madenat_sv_imputation_wizard_form' % MOD)
        root = etree.fromstring(form.arch.encode())
        node = root.find(".//field[@name='multi_sv']")
        self.assertIsNotNone(node)
        self.assertEqual(node.get('invisible'), '1')

    def test_owl_03_caso_a_apertura_sin_reparto(self):
        guia = self._guia('OWL-A')
        self._etiqueta(guia, 'OWL-A-E', 10.0)
        wiz = self._wizard(guia)
        self.assertFalse(wiz.sv_line_ids)
        self.assertFalse(wiz.multi_sv)      # columna «SV destino» oculta

    def test_owl_04_caso_b_reparto_solo_sv_trabajo(self):
        guia = self._guia('OWL-B')
        e = self._etiqueta(guia, 'OWL-B-E', 10.0)
        sv = self._sv(guia, 'SV00000135001', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        self._alloc(wiz, line, sv, 4.0)
        self.assertFalse(wiz.multi_sv)      # un solo SV → columna oculta


    def test_owl_05_caso_c_varios_sv_muestra_destinos(self):
        guia = self._guia('OWL-C')
        e = self._etiqueta(guia, 'OWL-C-E', 10.0)
        sv = self._sv(guia, 'SV00000135002', 100.0)
        sv2 = self._sv(guia, 'SV00000135003', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        self._alloc(wiz, line, sv, 4.0)
        self._alloc(wiz, line, sv2, 3.0)
        self.assertTrue(wiz.multi_sv)       # varios SV → columna visible
        self.assertEqual(
            set(wiz.sv_line_ids.mapped('sv_lot_id').ids),
            {sv.id, sv2.id})

    def test_owl_06_caso_d_ida_y_vuelta_sin_perdida(self):
        guia = self._guia('OWL-D')
        e = self._etiqueta(guia, 'OWL-D-E', 10.0)
        sv = self._sv(guia, 'SV00000135004', 100.0)
        sv2 = self._sv(guia, 'SV00000135005', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        work = self._alloc(wiz, line, sv, 4.0)
        extra = self._alloc(wiz, line, sv2, 3.0)
        self.assertTrue(wiz.multi_sv)
        # Quitar el SV adicional → vuelve a un solo SV, sin perder el reparto.
        extra.unlink()
        self.assertFalse(wiz.multi_sv)
        self.assertAlmostEqual(work.imputed_volume_m3, 4.0, 3)
        self.assertEqual(len(line.sv_alloc_ids.filtered(
            lambda a: a.sv_lot_id == sv)), 1)

    def test_owl_07_caso_e_guardar_reabrir_conserva(self):
        guia = self._guia('OWL-E')
        e = self._etiqueta(guia, 'OWL-E-E', 10.0)
        sv = self._sv(guia, 'SV00000135006', 100.0)
        sv2 = self._sv(guia, 'SV00000135007', 100.0)
        wiz = self._wizard(guia, sv=sv)
        line = wiz.line_ids.filtered(lambda l: l.processed_lot_id == e)
        line.selected = True
        self._alloc(wiz, line, sv, 4.0)
        self._alloc(wiz, line, sv2, 3.0)
        imp = wiz._i2_build_imputation()
        defaults = self.Wizard.with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).default_get(
                ['guia_processing_id', 'imputation_id', 'line_ids'])
        wiz2 = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create(defaults)
        self.assertEqual(wiz2.imputation_id, imp)
        self.assertTrue(wiz2.multi_sv)      # visibilidad conservada
        # El reparto guardado se conserva en `sv_line_ids` (no sólo anidado).
        self.assertEqual(len(wiz2.sv_line_ids), 2)
        self.assertAlmostEqual(
            sum(wiz2.sv_line_ids.mapped('imputed_volume_m3')), 7.0, 3)
        self.assertEqual(
            set(wiz2.sv_line_ids.mapped('sv_lot_id').ids),
            {sv.id, sv2.id})
        self.assertAlmostEqual(wiz2.assigned_total_m3, 7.0, 3)
        self.assertFalse(wiz2.line_ids.sv_alloc_ids.filtered(
            lambda a: not a.wizard_id))

