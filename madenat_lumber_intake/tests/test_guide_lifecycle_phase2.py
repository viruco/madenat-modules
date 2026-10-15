# -*- coding: utf-8 -*-
"""MADENAT — Fase 2: atribución del retorno y Modo B (aislado).

Verifica, con fixtures reproducibles:

* El Modo B NO revierte un documento AJENO por coincidencia textual de número
  (`action_force_cancel` filtra `_picking_is_foreign_document`).
* El Modo B SÍ revierte el albarán propio y su retorno no hereda
  `guia_processing_id` por el contexto (`default_guia_processing_id`).
* Un retorno propio con vínculo directo (FK) sigue BLOQUEANDO el Modo A.
* Reproducción del caso 15183: bloqueado por el FK espurio del retorno;
  **elegible** tras reparar ese FK (procedimiento separado, aquí simulado).

TransactionCase: todo se revierte. No se toca la guía real 33152 ni los
pickings reales 436/7813/7814.
"""

from odoo import api
from odoo.exceptions import UserError
from odoo.sql_db import db_connect
from odoo.tests import tagged
from odoo.tests.common import Form, SingleTransactionCase, TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestReturnAttribution(TransactionCase):
    """Modo B y atribución de retornos por relaciones (no por número)."""

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
            'name': 'Proveedor Fase 2', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Fase 2', 'is_storable': True, 'tracking': 'lot',
        })

    # ── Fábricas ──────────────────────────────────────────────────────────
    def _make_guia(self, name, state='cancelled'):
        return self.Guia.create({
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.internal_loc.id, 'state': state,
            'tipo_recepcion': 'granel', 'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared', 'volume_pdf_m3': 40.315,
        })

    def _own_lot(self, guia, label):
        return self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.env.company.id, 'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id, 'guia_processing_id': guia.id,
            'volumen_m3': 10.0,
        })

    def _reception_lot(self, reception, label):
        return self.StockLot.create({
            'name': label, 'product_id': self.product.id,
            'company_id': self.env.company.id, 'reception_id': reception.id,
            'volumen_m3': 10.0,
        })

    def _reception(self, name):
        return self.Reception.create({'name': name, 'ingestion_profile': 'metric'})

    def _incoming_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', self.warehouse.id)], limit=1)

    def _picking(self, origin, lot=None, **extra):
        picking = self.Picking.create(dict({
            'picking_type_id': self._incoming_type().id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
            'origin': origin, 'partner_id': self.partner.id}, **extra))
        if lot is not None:
            move = self.Move.create({
                'name': lot.name, 'product_id': self.product.id,
                'product_uom_qty': 5.0, 'product_uom': self.product.uom_id.id,
                'picking_id': picking.id, 'origin': origin,
                'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal_loc.id})
            self.MoveLine.create({
                'move_id': move.id, 'picking_id': picking.id,
                'product_id': self.product.id, 'lot_id': lot.id,
                'quantity': 5.0, 'product_uom_id': self.product.uom_id.id,
                'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal_loc.id})
            picking.action_confirm()
            picking.with_context(
                skip_backorder=True, skip_immediate=True,
                immediate_transfer=True, force_validate=True,
            ).button_validate()
        return picking

    def _wizard(self, guia, mode, reason='Motivo', **extra):
        vals = {'guia_processing_id': guia.id, 'mode': mode, 'reason': reason}
        vals.update(extra)
        return self.Wizard.create(vals)

    # ── Modo B no revierte un documento ajeno (mismo número) ──────────────
    def test_modo_b_does_not_reverse_foreign_picking(self):
        guia = self._make_guia('DA2-B-15183')
        reception = self._reception('DA2-B-15183')
        rlot = self._reception_lot(reception, 'REC2B01')
        foreign = self._picking(
            guia.name, lot=rlot, reception_id=reception.id)
        self.assertEqual(foreign.state, 'done')
        returns_before = self.Picking.search_count(
            [('origin', '=', 'Return of %s' % foreign.name)])

        self._wizard(guia, 'B').action_run()

        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'cancelled')
        self.assertEqual(
            self.Picking.search_count(
                [('origin', '=', 'Return of %s' % foreign.name)]),
            returns_before, 'Modo B no debe revertir un documento ajeno')
        foreign.invalidate_recordset()
        self.assertEqual(foreign.state, 'done')
        self.assertTrue(reception.exists())

    # ── Modo B revierte el albarán propio sin fuga de FK ──────────────────
    def test_modo_b_reverses_own_picking_without_fk_leak(self):
        guia = self._make_guia('DA2-OWN-01')
        lot = self._own_lot(guia, 'SV2OWN01')
        own = self._picking(guia.name, lot=lot)
        self.assertEqual(own.state, 'done')

        # Contexto CONTAMINADO (como lo abre la Consola).
        wizard = self.Wizard.with_context(
            default_guia_processing_id=guia.id).create({
                'guia_processing_id': guia.id, 'mode': 'B',
                'reason': 'Cancelar y conservar'})
        wizard.action_run()

        returns = self.Picking.search(
            [('origin', '=', 'Return of %s' % own.name)])
        self.assertTrue(returns, 'Modo B debe revertir el albarán propio')
        # El retorno NO queda atribuido a la guía (corrección preventiva).
        self.assertFalse(returns.guia_processing_id)

    # ── Un retorno propio con FK sigue bloqueando el Modo A ───────────────
    def test_own_return_with_fk_still_blocks_modo_a(self):
        guia = self._make_guia('DA2-RET-01')
        retorno = self._picking(
            'Return of EMB-XXXXX', guia_processing_id=guia.id)
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('vínculo directo (guia_processing_id)', wizard.blockers)
        self.assertIn(retorno.name, wizard.blockers)
        self.assertTrue(guia.exists())

    # ── Reproducción del caso 15183 ───────────────────────────────────────
    def test_case_15183_blocked_by_spurious_fk_then_eligible_after_repair(self):
        guia = self._make_guia('DA2-15183-G')
        reception = self._reception('DA2-15183-G')   # nº compartido con la guía
        rlot = self._reception_lot(reception, 'REC15183')
        receipt = self._picking(                        # ~ picking 436
            guia.name, lot=rlot, reception_id=reception.id)
        retorno = self._picking(                        # ~ retorno 7813
            'Return of %s' % receipt.name, guia_processing_id=guia.id)

        # (1) Bloqueada por el FK espurio del retorno.
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('vínculo directo (guia_processing_id)', wizard.blockers)
        # El documento ajeno NO aparece como bloqueador.
        diag = wizard._lifecycle_diagnosis()
        self.assertIn(retorno, diag['direct_link_pickings'])
        self.assertNotIn(receipt, diag['pickings'])

        # (2) Reparación del FK (procedimiento separado; aquí simulado).
        retorno.write({'guia_processing_id': False})

        # (3) Ahora la guía no tiene dependencia propia: elegible (dev).
        wizard2 = self._wizard(guia, 'A', acknowledge=True)
        self.assertTrue(wizard2.requirements_ok, wizard2.blockers)
        wizard2.action_run()
        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        # La cadena material ajena sobrevive intacta.
        self.assertTrue(receipt.exists())
        self.assertTrue(retorno.exists())
        self.assertTrue(reception.exists())



@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestDeleteWizardUi(TransactionCase):
    """UI del asistente: formulario REAL renderiza y ejecuta (framework Form)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env['madenat.lumber.intake.guide.lifecycle']
        cls.env.user.sudo().write({'groups_id': [
            (4, cls.env.ref('stock.group_stock_manager').id)]})
        cls.partner = cls.env['res.partner'].create({
            'name': 'P UI Fase 2', 'is_company': True})
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)

    def test_form_view_renders_field_and_runs(self):
        view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_guide_lifecycle_form')
        self.assertIn('attribution_notes', view.arch)
        self.assertIn('blockers', view.arch)

        guia = self.Guia.create({
            'name': 'DA2-UI-01', 'partner_id': self.partner.id,
            'assignment_location_id': self.warehouse.lot_stock_id.id,
            'state': 'cancelled', 'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared', 'volume_pdf_m3': 40.315})

        # `guia_processing_id` no está en la vista (se muestra `guia_name`),
        # así que se crea el asistente y se opera el resto por el formulario REAL
        # (radio `mode`, motivo y confirmación), que sí incluye la vista.
        wizard = self.Wizard.create({
            'guia_processing_id': guia.id, 'mode': 'D', 'reason': 'tmp'})
        with Form(wizard) as form:
            form.mode = 'A'
            form.reason = 'Motivo desde el formulario'
            form.acknowledge = True
        wizard = form.save()

        self.assertTrue(wizard.requirements_ok, wizard.blockers)
        action = wizard.action_run()
        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        self.assertEqual(
            action.get('res_model'), 'madenat.lumber.intake.console')

@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake',
        'delete_concurrency')
class TestDeleteConcurrency(SingleTransactionCase):
    """Concurrencia real: candado de eliminación y dependencia comprometida."""

    NS = 0x4D414445  # namespace del candado (igual que _acquire_delete_lock)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env['madenat.lumber.intake.guide.lifecycle']
        cls.env.user.sudo().write({'groups_id': [
            (4, cls.env.ref('stock.group_stock_manager').id)]})
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', cls.warehouse.id)], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'P Conc Fase 2', 'is_company': True})
        cls.guia = cls.Guia.create({
            'name': 'DA2-CONC-GUIA', 'partner_id': cls.partner.id,
            'assignment_location_id': cls.internal_loc.id, 'state': 'cancelled',
            'tipo_recepcion': 'granel', 'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared', 'volume_pdf_m3': 40.315})
        cls.cr.commit()  # publica la guía para la 2ª conexión

    @classmethod
    def tearDownClass(cls):
        """G2 (FASE 3): limpieza GARANTIZADA de lo creado por ESTA suite.

        Usa los **ids registrados en la clase** (`cls.guia`, `cls.partner`),
        nunca un borrado por nombre amplio. `SingleTransactionCase` permite
        `commit`, así que el `setUpClass` publicó datos fuera del rollback; sin
        esta limpieza quedaban socios «P Conc Fase 2» residuales.
        """
        try:
            cls.cr.rollback()
        except Exception:  # pragma: no cover - defensivo
            pass
        cls.env.invalidate_all()
        try:
            gid = cls.guia.id
            pid = cls.partner.id
            cls.cr.execute(
                'DELETE FROM madenat_audit_log WHERE guia_processing_id = %s',
                (gid,))
            cls.cr.execute(
                'DELETE FROM madenat_guia_processing WHERE id = %s', (gid,))
            cls.cr.execute(
                'DELETE FROM res_partner WHERE id = %s', (pid,))
            cls.cr.commit()
        except Exception:  # pragma: no cover - defensivo
            cls.cr.rollback()
        super().tearDownClass()

    def _new_conn(self):
        """Conexión PostgreSQL REAL e independiente (no el proxy de test)."""
        conn = db_connect(self.env.cr.dbname)
        cr = conn.cursor()
        cr.transaction = api.Transaction(self.registry)
        return conn, cr

    def test_01_advisory_lock_serializes_same_key(self):
        conn_a, cr_a = self._new_conn()
        conn_b, cr_b = self._new_conn()
        try:
            cr_a.execute("SELECT pg_advisory_xact_lock(%s, %s)",
                         (self.NS, self.guia.id))
            cr_b.execute("SET statement_timeout = 900")
            blocked = False
            try:
                cr_b.execute("SELECT pg_advisory_xact_lock(%s, %s)",
                             (self.NS, self.guia.id))
            except Exception:
                blocked = True
            cr_b.rollback()  # limpia el estado abortado
            self.assertTrue(
                blocked, 'La misma clave debe serializar dos transacciones')
            cr_a.rollback()  # libera el candado
            cr_b.execute("SET statement_timeout = 5000")
            cr_b.execute("SELECT pg_advisory_xact_lock(%s, %s)",
                         (self.NS, self.guia.id))
            cr_b.rollback()
        finally:
            cr_a.close()
            cr_b.close()

    def test_02_committed_dependency_blocks_deletion(self):
        conn, cr = self._new_conn()
        try:
            env2 = api.Environment(cr, self.env.uid, {})
            dep = env2['stock.picking'].create({
                'picking_type_id': self.picking_type.id,
                'location_id': self.supplier_loc.id,
                'location_dest_id': self.internal_loc.id,
                'origin': 'DA2-CONC-DEP', 'partner_id': self.partner.id,
                'guia_processing_id': self.guia.id})
            cr.commit()  # otra transacción PUBLICA la dependencia
            self.env.invalidate_all()

            wizard = self.Wizard.create({
                'guia_processing_id': self.guia.id, 'mode': 'A',
                'reason': 'Conc', 'acknowledge': True})
            raised = None
            try:
                wizard._run_delete_definitive(wizard._lifecycle_diagnosis())
            except UserError as exc:
                raised = exc
            self.assertIsNotNone(
                raised, 'Una dependencia comprometida debe bloquear')
            self.assertTrue(self.Guia.browse(self.guia.id).exists())

            env2['stock.picking'].browse(dep.id).unlink()
            cr.commit()
        finally:
            cr.close()

    def test_99_cleanup_guia(self):
        """G2 (FASE 3): limpieza del fixture por ID (SQL).

        La guarda G1 bloquea eliminar una guía con dependencias (p. ej. un
        albarán creado por la propia prueba); esta limpieza es un **artefacto
        de la suite**, no una operación de negocio, así que borra por **ID**
        (solo lo creado por esta clase), sin pasar por las guardas.
        """
        gid = self.guia.id
        self.cr.execute(
            'DELETE FROM madenat_audit_log WHERE guia_processing_id = %s',
            (gid,))
        self.cr.execute(
            'DELETE FROM madenat_guia_processing WHERE id = %s', (gid,))
        self.cr.commit()

