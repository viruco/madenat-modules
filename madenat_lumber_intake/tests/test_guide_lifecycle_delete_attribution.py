# -*- coding: utf-8 -*-
"""MADENAT — Atribución robusta para la eliminación (Modo A) de la guía.

Contrato verificado (FIX_DELETE_INTAKE — corrección de atribución):

El diagnóstico y la ejecución del Modo A comparten el MISMO criterio y
atribuyen los albaranes por RELACIONES (no por número textual):

* propios    → vínculo fuerte (`guia_processing_id`) o lotes propios de la
               guía. BLOQUEAN.
* ambiguos   → coincidencia textual de número sin vínculo verificable.
               BLOQUEAN con mensaje específico.
* ajenos     → coincidencia de número, pero atribuidos positivamente a OTRO
               documento (p. ej. la recepción homónima). NO bloquean y se
               informan aparte (`attribution_notes`).

Además:
* revalidación inmediata antes de borrar (una dependencia que aparezca entre el
  diagnóstico y la ejecución bloquea el borrado);
* se conservan las protecciones del core en `unlink()` y las demás rutas.

TransactionCase: todo se revierte. No se toca la guía real 33152 ni el retorno
7813 (caso de referencia); las fixtures son propias y aisladas.
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestDeleteAttribution(TransactionCase):
    """Fixture de la matriz de elegibilidad de eliminación (Modo A)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env['madenat.lumber.intake.guide.lifecycle']
        cls.StockLot = cls.env['stock.lot']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.Reception = cls.env['lumber.reception']
        # El usuario de prueba necesita rol operativo (crear recepciones) y el
        # grupo de Inventario (el unlink del core lo exige).
        cls.env.user.sudo().write({'groups_id': [
            (4, cls.env.ref(
                'madenat_lumber_core.group_madenat_jefatura_operaciones').id),
            (4, cls.env.ref('stock.group_stock_manager').id),
        ]})
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Delete Attribution', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Delete Attribution',
            'is_storable': True,
            'tracking': 'lot',
        })

    # ── Fábricas aisladas ─────────────────────────────────────────────────
    def _make_guia(self, name, state='cancelled'):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.internal_loc.id,
            'state': state,
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared',
            'volume_pdf_m3': 40.315,
        })

    def _own_lot(self, guia, label):
        """Lote propio de la guía (vínculo por `volume_source_guia_id`)."""
        return self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'guia_processing_id': guia.id,
            'volumen_m3': 10.0,
        })

    def _reception(self, name):
        return self.Reception.create({
            'name': name,
            'ingestion_profile': 'metric',
        })

    def _incoming_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', self.warehouse.id)], limit=1)


    def _picking(self, origin, **extra):
        vals = {
            'picking_type_id': self._incoming_type().id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
            'origin': origin,
            'partner_id': self.partner.id,
        }
        vals.update(extra)
        return self.Picking.create(vals)

    def _picking_with_lot(self, origin, lot, quantity=5.0, **extra):
        picking = self._picking(origin, **extra)
        move = self.Move.create({
            'name': lot.name,
            'product_id': self.product.id,
            'product_uom_qty': quantity,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'origin': origin,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
        })
        self.MoveLine.create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.product.id,
            'lot_id': lot.id,
            'quantity': quantity,
            'product_uom_id': self.product.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
        })
        return picking

    def _wizard(self, guia, mode, reason='Motivo de prueba', **extra):
        vals = {'guia_processing_id': guia.id, 'mode': mode, 'reason': reason}
        vals.update(extra)
        return self.Wizard.create(vals)

    # ── Caso A: cancelada sin dependencias → se elimina ───────────────────
    def test_a_cancelled_without_dependencies_is_deleted(self):
        guia = self._make_guia('DA-A-01')
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertTrue(wizard.requirements_ok, wizard.blockers)
        self.assertFalse(wizard.blocker_count)

        action = wizard.action_run()

        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')

    # ── Caso B/G: documento ajeno con número coincidente → NO bloquea ─────
    def test_b_foreign_document_same_number_does_not_block(self):
        guia = self._make_guia('DA-B-15183')
        reception = self._reception('DA-B-15183')
        foreign = self._picking('DA-B-15183', reception_id=reception.id)

        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertTrue(wizard.requirements_ok, wizard.blockers)
        diag = wizard._lifecycle_diagnosis()
        self.assertFalse(diag['pickings'])
        self.assertIn(foreign, diag['foreign_pickings'])
        self.assertIn('no cuentan como dependencia',
                      wizard.attribution_notes or '')

        wizard.action_run()

        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        # El documento ajeno NO se toca.
        self.assertTrue(foreign.exists())
        self.assertEqual(foreign.reception_id, reception)

    # ── Caso C: coincidencia textual sin vínculo → bloqueo específico ────
    def test_c_ambiguous_origin_only_blocks_with_specific_message(self):
        guia = self._make_guia('DA-C-01')
        ambiguous = self._picking('DA-C-01')

        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('atribución textual ambigua', wizard.blockers)
        self.assertIn('atribución ambigua, requiere verificación',
                      wizard.blockers)
        self.assertIn(ambiguous.name, wizard.blockers)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())

    # ── Caso D: vínculo directo (FK) aunque el origin NO coincida ────────
    def test_d_direct_fk_link_blocks_even_without_origin_match(self):
        guia = self._make_guia('DA-D-01')
        linked = self._picking('Albaran ajeno sin coincidencia',
                               guia_processing_id=guia.id)

        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(
            wizard.requirements_ok,
            'El vínculo directo por FK debe bloquear aunque no coincida el '
            'número textual')
        self.assertIn('vínculo directo (guia_processing_id)', wizard.blockers)
        self.assertIn(linked.name, wizard.blockers)
        self.assertTrue(guia.exists())

    # ── Caso E: retorno propio vinculado directamente (punto ciego) ──────
    def test_e_linked_return_is_detected(self):
        guia = self._make_guia('DA-E-01')
        retorno = self._picking(
            'Return of EMB-99999', guia_processing_id=guia.id)

        diag = self._wizard(guia, 'A', acknowledge=True)._lifecycle_diagnosis()
        self.assertIn(retorno, diag['direct_link_pickings'])
        self.assertIn(retorno, diag['pickings'])

    # ── Lote propio → dependencia material ────────────────────────────────
    def test_f_own_lot_moves_block(self):
        guia = self._make_guia('DA-F-01')
        lot = self._own_lot(guia, 'SVDAF01')
        self._picking_with_lot(guia.name, lot)

        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('lote(s) vinculados', wizard.blockers)
        self.assertTrue(guia.exists())

    # ── Sin doble conteo: hallado por número Y por lote ───────────────────
    def test_k_no_double_count_when_found_by_several_routes(self):
        guia = self._make_guia('DA-K-01')
        lot = self._own_lot(guia, 'SVDAK01')
        picking = self._picking_with_lot(guia.name, lot)

        diag = self._wizard(guia, 'A', acknowledge=True)._lifecycle_diagnosis()
        # Hallado por `origin` y por lote: se cuenta UNA sola vez.
        self.assertEqual(len(diag['pickings']), 1)
        self.assertEqual(diag['pickings'], picking)

    # ── Revalidación inmediata: dependencia aparecida tras el diagnóstico ─
    def test_h_revalidation_blocks_on_late_dependency(self):
        guia = self._make_guia('DA-H-01')
        wizard = self._wizard(guia, 'A', acknowledge=True)
        diag = wizard._lifecycle_diagnosis()
        self.assertTrue(wizard._requirements_ok(diag))  # elegible al diagnosticar

        # Aparece una dependencia DESPUÉS del diagnóstico y ANTES de borrar.
        late = self._picking('Albaran tardio', guia_processing_id=guia.id)

        # (1) La REVALIDACIÓN interna de la ejecución la detecta y no borra.
        with self.assertRaises(UserError) as ctx:
            wizard._run_delete_definitive(diag)
        self.assertIn('dejó de cumplir las precondiciones', str(ctx.exception))
        self.assertTrue(guia.exists())
        self.assertTrue(late.exists())

        # (2) `action_run` también vuelve a diagnosticar con datos frescos.
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())

    # ── Protección del core preservada (state) ────────────────────────────
    def test_i_core_unlink_protection_preserved(self):
        guia = self._make_guia('DA-I-01', state='verified')
        with self.assertRaises(UserError) as ctx:
            guia.unlink()
        self.assertIn('SEGURIDAD MADENAT', str(ctx.exception))
        self.assertTrue(guia.exists())

    # ── Permisos: usuario no autorizado no evade protecciones ─────────────
    def test_j_non_authorized_user_is_blocked(self):
        guia = self._make_guia('DA-J-01')
        restricted = self.env['res.users'].create({
            'name': 'Usuario sin permisos DA',
            'login': 'da_restricted_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        # `assertRaises` no admite tuplas en este runtime: se captura aparte.
        raised = None
        try:
            guia.with_user(restricted).unlink()
        except (UserError, AccessError) as exc:
            raised = exc
        self.assertIsNotNone(
            raised, 'El usuario no autorizado no fue bloqueado')
        self.assertTrue(guia.exists())

    # ── §6: fuga por contexto reproducida y prevenida ─────────────────────
    def test_l_context_default_leak_reproduced_and_prevented(self):
        """El contexto `default_guia_processing_id` se filtra a cualquier
        `stock.picking.create`; forzar `False` (patrón preventivo aplicado a
        la creación del retorno) lo neutraliza."""
        guia = self._make_guia('DA-L-01')
        ctx = {'default_guia_processing_id': guia.id}
        base = {
            'picking_type_id': self._incoming_type().id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
            'origin': 'Return of EMB-00001',
        }
        # Sin la corrección: la FK se "filtra" al retorno.
        leaked = self.Picking.with_context(**ctx).create(dict(base))
        self.assertEqual(leaked.guia_processing_id, guia)
        # Con la corrección: `False` explícito desactiva la fuga.
        fixed = self.Picking.with_context(**ctx).create(
            dict(base, guia_processing_id=False))
        self.assertFalse(fixed.guia_processing_id)
        # Un retorno con FK espurio bloquea Modo A por vínculo directo.
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertIn('vínculo directo (guia_processing_id)', wizard.blockers)

