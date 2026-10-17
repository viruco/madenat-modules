# -*- coding: utf-8 -*-
"""Pruebas TDD para WP-F (P1–P5) — Disponibilidad de etiquetas en imputación SV.

FASE 12 — Bloque 2 (WP-F):
- P1: Campo `asignable` por fila y toggle `selected` con readonly si no es asignable.
- P2: `action_select_all` limita la selección a etiquetas disponibles (asignables).
- P3: Pestaña 'Sin disponibilidad' para trazabilidad y consulta de etiquetas bloqueadas.
- P4: Resumen coherente (`selectable_line_count` y desglose de sin saldo en `assigned_summary`).
- P5: Mensaje de error nominativo al aplicar si se incluyen etiquetas sin saldo.
"""
from lxml import etree
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationAvailabilityP1P5(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.product = cls.env['product.product'].create({
            'name': 'Pino Aserrado Test WP-F',
            'type': 'consu',
        })
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Proveedor WP-F',
            'is_company': True,
        })
        cls.stock_loc = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        cls.guia = cls.env['madenat.guia.processing'].create({
            'name': 'G-WPF-001',
            'partner_id': cls.supplier.id,
            'tipo_recepcion': 'service',
            'service_return_confirmation': 'yes',
            'assignment_location_id': cls.stock_loc.id,
            'state': 'verified',
        })
        # Lote 1: Disponible (4.0 m³)
        cls.lot_available = cls.env['stock.lot'].create({
            'name': 'LOT-WPF-01',
            'ref': 'ETQ-WPF-01',
            'product_id': cls.product.id,
            'guia_processing_id': cls.guia.id,
            'lot_flow_type': 'tarja',
            'volume_purchase_m3': 4.0,
            'volumen_m3': 4.0,
        })
        # Lote 2: Consumido (3.0 m³)
        cls.lot_consumed = cls.env['stock.lot'].create({
            'name': 'LOT-WPF-02',
            'ref': 'ETQ-WPF-02',
            'product_id': cls.product.id,
            'guia_processing_id': cls.guia.id,
            'lot_flow_type': 'tarja',
            'volume_purchase_m3': 3.0,
            'volumen_m3': 3.0,
        })
        cls.guia.write({'lot_ids': [(4, cls.lot_available.id), (4, cls.lot_consumed.id)]})
        # SV destino
        cls.lot_sv = cls.env['stock.lot'].create({
            'name': 'SV-WPF-001',
            'ref': 'SV-WPF-001',
            'product_id': cls.product.id,
            'volume_source_guia_id': cls.guia.id,
            'lot_flow_type': 'volume',
            'volume_purchase_m3': 20.0,
            'volumen_m3': 20.0,
        })
        # Imputación previa que consume lot_consumed (3.0 m³)
        cls.prev_imputation = cls.Imputation.create({
            'name': 'IMP-PREV-01',
            'guia_processing_id': cls.guia.id,
            'state': 'draft',
        })
        prev_line = cls.env['madenat.sv.imputation.line'].create({
            'imputation_id': cls.prev_imputation.id,
            'processed_lot_id': cls.lot_consumed.id,
            'nominal_volume_m3': 3.0,
        })
        cls.env['madenat.sv.imputation.sv.line'].create({
            'imputation_id': cls.prev_imputation.id,
            'imputation_line_id': prev_line.id,
            'sv_lot_id': cls.lot_sv.id,
            'imputed_volume_m3': 3.0,
        })
        cls.user_oper = cls.env['res.users'].create({
            'name': 'Operaciones WP-F',
            'login': 'wpf_oper',
            'email': 'wpf_oper@madenat.cl',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('madenat_lumber_core.group_madenat_operaciones').id,
            ])],
        })
        # Aplicamos por la vía privada/controlada
        cls.prev_imputation._i2_write_protected_state({
            'state': 'applied',
            'executed_by_id': cls.env.user.id,
        })

    def _make_wizard(self):
        wiz = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=self.guia.id,
        ).create({
            'guia_processing_id': self.guia.id,
            'sv_lot_id': self.lot_sv.id,
        })
        wiz._onchange_guia_processing_id()
        return wiz

    def _get_wizard_form_tree(self):
        view = self.env.ref('madenat_lumber_logistics.view_madenat_sv_imputation_wizard_form')
        return etree.fromstring(view.arch)

    def test_01_p1_asignable_field_and_view_readonly(self):
        """P1: Verifica que el campo 'asignable' refleje disponibilidad y que

        la vista aplique readonly cuando not asignable.
        """
        wiz = self._make_wizard()
        line_avail = wiz.line_ids.filtered(lambda l: l.processed_lot_id == self.lot_available)
        line_cons = wiz.line_ids.filtered(lambda l: l.processed_lot_id == self.lot_consumed)

        self.assertTrue(line_avail, "Debe existir fila para lote disponible")
        self.assertTrue(line_cons, "Debe existir fila para lote consumido")

        self.assertTrue(line_avail.asignable, "Lote con saldo debe ser asignable")
        self.assertFalse(line_cons.asignable, "Lote consumido NO debe ser asignable")

        # Verificación en la vista XML
        tree = self._get_wizard_form_tree()
        selected_node = tree.xpath("//field[@name='line_ids']//field[@name='selected']")
        self.assertTrue(selected_node, "Debe existir campo selected en la lista")
        self.assertIn("not asignable", selected_node[0].attrib.get('readonly', ''),
                      "El toggle selected debe tener readonly='not asignable'")

    def test_02_p2_action_select_all_only_assignable(self):
        """P2: Verifica que 'action_select_all' solo marque etiquetas asignables

        y notifique sobre las omitidas.
        """
        wiz = self._make_wizard()
        res = wiz.action_select_all()

        line_avail = wiz.line_ids.filtered(lambda l: l.processed_lot_id == self.lot_available)
        line_cons = wiz.line_ids.filtered(lambda l: l.processed_lot_id == self.lot_consumed)

        self.assertTrue(line_avail.selected, "Lote disponible DEBE quedar seleccionado")
        self.assertFalse(line_cons.selected, "Lote sin disponibilidad NO debe quedar seleccionado")

        # Notificación
        self.assertIsInstance(res, dict, "Debe devolver acción de notificación")
        self.assertEqual(res.get('tag'), 'display_notification')
        self.assertIn("omitida", res.get('params', {}).get('message', ''))

    def test_03_p3_unavailable_page_exists(self):
        """P3: Verifica que la pestaña 'Sin disponibilidad' exista en la vista XML."""
        tree = self._get_wizard_form_tree()
        unavail_page = tree.xpath("//page[@name='unavailable_material']")
        self.assertTrue(unavail_page, "Debe existir la pestaña name='unavailable_material'")
        self.assertIn("not_assignable_line_count == 0", unavail_page[0].attrib.get('invisible', ''))

    def test_04_p4_selection_summary_coherence(self):
        """P4: Verifica coherencia del resumen y conteo de seleccionables."""
        wiz = self._make_wizard()
        self.assertEqual(wiz.selectable_line_count, 1, "Debe haber exactamente 1 seleccionable")
        self.assertEqual(wiz.not_assignable_line_count, 1, "Debe haber 1 no asignable")

        # Marcar la disponible
        line_avail = wiz.line_ids.filtered(lambda l: l.processed_lot_id == self.lot_available)
        line_avail.selected = True

        self.assertIn("sin saldo", wiz.assigned_summary, "El resumen debe mencionar 'sin saldo'")
        self.assertIn("seleccionadas", wiz.assigned_summary)

    def test_05_p5_nominative_error_on_unassignable_apply(self):
        """P5: Verifica que el error al aplicar sin saldo nombre explícitamente

        la etiqueta y el documento causante.
        """
        # Crear imputación directamente con el lote consumido
        imp = self.Imputation.create({
            'name': 'IMP-TEST-NOMINATIVE',
            'guia_processing_id': self.guia.id,
            'state': 'draft',
        })
        imp_line = self.env['madenat.sv.imputation.line'].create({
            'imputation_id': imp.id,
            'processed_lot_id': self.lot_consumed.id,
            'nominal_volume_m3': 3.0,
        })
        self.env['madenat.sv.imputation.sv.line'].create({
            'imputation_id': imp.id,
            'imputation_line_id': imp_line.id,
            'sv_lot_id': self.lot_sv.id,
            'imputed_volume_m3': 3.0,
        })
        with self.assertRaises(UserError) as cm:
            imp.with_user(self.user_oper).action_apply()

        msg = str(cm.exception)
        self.assertIn('ETQ-WPF-02', msg, "El mensaje de error debe nombrar la etiqueta ETQ-WPF-02")
        self.assertIn('IMP-PREV-01', msg, "El mensaje de error debe nombrar el documento IMP-PREV-01")
