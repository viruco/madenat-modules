# -*- coding: utf-8 -*-
"""Ciclo de vida controlado de guías (Fase 2, AD-80).

Contrato verificado para los cuatro modos documentados:

A. Eliminar definitivamente: solo `draft`/`cancelled` sin ninguna traza, con
   motivo, confirmación explícita y auditoría firmada.
B. Cancelar y conservar trazabilidad: usa `action_force_cancel()` sin alterar
   su semántica; pickings, movimientos y lotes se conservan.
C. Purgar de forma controlada: solo guía + lote técnico sin historia material,
   con motivo, confirmación escrita y Jefatura de Operaciones. Nunca nulifica
   `volume_source_guia_id` sobre un lote sobreviviente ni elimina operaciones
   SV rechazadas/aplicadas/reversadas.
D. Bloquear y escalar: lista completa de bloqueadores, evento
   `guia_delete_blocked` y cero eliminaciones.

TransactionCase: todo se revierte. No se toca la Guía 4495589 ni la etiqueta
SV00000000008.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

import base64
import json
import odoo
from unittest.mock import patch

# Parámetro de sistema que habilita el «Modo A autoservicio» en desarrollo
# sin `--test-enable` (implementado 2026-09-28 en `madenat_lumber_core`).
DEV_CLEANUP_PARAM = 'madenat.dev_cleanup_enabled'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestGuideLifecycle(TransactionCase):
    """Modos A/B/C/D del ciclo de vida controlado de guías."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Wizard = cls.env['madenat.lumber.intake.guide.lifecycle']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.Quant = cls.env['stock.quant']
        cls.AuditLog = cls.env['madenat.audit.log']
        # Jefatura de Operaciones es requisito funcional del Modo C (la purga
        # la ejecuta esa jefatura); el usuario de pruebas de la suite SV usa el
        # mismo patrón.
        cls.env.user.sudo().write({
            'groups_id': [(4, cls.env.ref(
                'madenat_lumber_core.group_madenat_jefatura_operaciones').id)],
        })
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Ciclo de Vida', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Ciclo de Vida',
            'is_storable': True,
            'tracking': 'lot',
        })

    # ── Fábricas aisladas ─────────────────────────────────────────────────
    def _make_guia(self, name, state='draft'):
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

    def _make_lot(self, guia, label, volume=40.300, technical=True):
        lot = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'guia_processing_id': guia.id,
            'piezas': 1,
            'volume_purchase_m3': volume,
            'vol_shipment_m3': volume,
            'volumen_m3': volume,
        })
        if not technical:
            guia.write({'lot_ids': [(4, lot.id)]})
        return lot

    def _rebaja(self, lot, volume=10.0):
        operation = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': volume,
            'reason': 'Rebaja de prueba del ciclo de vida',
        })
        operation.action_apply()
        return operation

    def _receipt_done(self, guia, lot, quantity=10.0):
        """Recepción validada del lote con origin de la guía."""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', self.warehouse.id)], limit=1)
        picking = self.Picking.create({
            'picking_type_id': picking_type.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
            'origin': guia.name,
            'partner_id': self.partner.id,
        })
        move = self.Move.create({
            'name': lot.name,
            'product_id': lot.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': lot.product_id.uom_id.id,
            'picking_id': picking.id,
            'origin': guia.name,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
        })
        self.MoveLine.create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': lot.product_id.id,
            'lot_id': lot.id,
            'quantity': quantity,
            'product_uom_id': lot.product_id.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.internal_loc.id,
        })
        picking.action_confirm()
        picking.with_context(
            skip_backorder=True, skip_immediate=True,
            immediate_transfer=True, force_validate=True,
        ).button_validate()
        return picking

    def _wizard(self, guia, mode, reason='Motivo de prueba', **extra):
        vals = {
            'guia_processing_id': guia.id,
            'mode': mode,
            'reason': reason,
        }
        vals.update(extra)
        return self.Wizard.create(vals)

    # ── Modo A — Eliminar definitivamente ─────────────────────────────────
    def test_01_modo_a_elimina_draft_sin_trazas(self):
        """Draft sin trazas: se elimina con motivo, confirmación y auditoría."""
        guia = self._make_guia('LC-A-01')
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertTrue(wizard.requirements_ok)
        self.assertFalse(wizard.blockers)

        action = wizard.action_run()

        self.assertFalse(
            self.Guia.search([('id', '=', guia.id)]),
            'La guía sin trazas debe desaparecer')
        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')
        logs = self.AuditLog.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('description', 'ilike', 'LC-A-01'),
        ])
        self.assertEqual(len(logs), 1, 'Falta la auditoría de eliminación')
        self.assertEqual(logs.user_id, self.env.user)
        self.assertTrue(logs.audit_hash)
        # Sin lote ni stock residual atribuible a la guía eliminada.
        self.assertFalse(self.StockLot.search(
            [('volume_source_guia_id', '=', guia.id)]))
        self.assertFalse(self.Picking.search([('origin', '=', 'LC-A-01')]))

    def test_02_modo_a_exige_motivo_y_confirmacion(self):
        """Sin confirmación explícita o sin motivo no se elimina nada."""
        guia = self._make_guia('LC-A-02')
        wizard = self._wizard(guia, 'A')
        self.assertFalse(wizard.requirements_ok)
        with self.assertRaises(UserError):
            wizard.action_run()

        wizard_blank = self._wizard(guia, 'A', reason='   ', acknowledge=True)
        with self.assertRaises(UserError) as ctx:
            wizard_blank.action_run()
        self.assertIn('motivo es obligatorio', str(ctx.exception))
        self.assertTrue(self.Guia.search([('id', '=', guia.id)]))

    def test_03_modo_a_bloqueado_con_lote(self):
        """Con lote SV vinculado la eliminación definitiva queda bloqueada."""
        guia = self._make_guia('LC-A-03')
        lot = self._make_lot(guia, 'SV00000000401')
        wizard = self._wizard(guia, 'A', acknowledge=True)

        self.assertFalse(wizard.requirements_ok)
        self.assertIn('lote(s) vinculados', wizard.blockers)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())
        self.assertTrue(lot.exists())

    def test_04_modo_a_bloqueado_por_estado_no_terminal(self):
        """Solo Borrador o Cancelado admiten eliminación definitiva."""
        guia = self._make_guia('LC-A-04', state='verified')
        wizard = self._wizard(guia, 'A', acknowledge=True)
        self.assertIn('solo se admite Borrador o Cancelado', wizard.blockers)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())


    # ── Modo B — Cancelar y conservar trazabilidad ────────────────────────
    def test_05_modo_b_conserva_trazabilidad(self):
        """La cancelación conserva pickings, movimientos y lotes."""
        guia = self._make_guia('LC-B-05')
        lot = self._make_lot(guia, 'SV00000000402', technical=False)
        picking = self._receipt_done(guia, lot, quantity=10.0)
        move = picking.move_ids
        self.assertEqual(picking.state, 'done')

        wizard = self._wizard(guia, 'B')
        self.assertTrue(wizard.requirements_ok)
        action = wizard.action_run()

        self.assertEqual(action['type'], 'ir.actions.client')
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'cancelled')
        # Nada histórico se borró: picking, movimiento y lote sobreviven.
        self.assertTrue(picking.exists())
        self.assertEqual(picking.state, 'done')
        self.assertTrue(move.exists())
        self.assertTrue(lot.exists())
        self.assertTrue(self.StockLot.search([('id', '=', lot.id)]))
        # La evidencia del motivo queda en el chatter del origen.
        self.assertTrue(guia.message_ids)

    # ── Modo C — Purgar de forma controlada ───────────────────────────────
    def test_06_modo_c_purga_lote_tecnico_sin_historia(self):
        """Guía + lote técnico sin trazas desaparecen juntos y auditados."""
        guia = self._make_guia('LC-C-06')
        lot = self._make_lot(guia, 'SV00000000403')
        wizard = self._wizard(
            guia, 'C', confirmation='PURGAR')
        self.assertTrue(wizard.requirements_ok, wizard.purge_blockers)
        self.assertIn('SV00000000403', wizard.technical_lots_text)

        action = wizard.action_run()

        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        self.assertFalse(self.StockLot.search([('id', '=', lot.id)]))
        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')
        logs = self.AuditLog.search([
            ('action_type', '=', 'guia_purged'),
            ('description', 'ilike', 'LC-C-06'),
        ])
        self.assertEqual(len(logs), 1, 'Falta la auditoría de purga')
        self.assertTrue(logs.audit_hash)
        # Ningún lote sobreviviente quedó con FK nula o reasignada.
        self.assertFalse(self.StockLot.search(
            [('volume_source_guia_id', '=', guia.id)]))

    def test_07_modo_c_exige_confirmacion_escrita_y_motivo(self):
        """Sin la confirmación literal PURGAR no se purga nada."""
        guia = self._make_guia('LC-C-07')
        lot = self._make_lot(guia, 'SV00000000404')
        wizard = self._wizard(guia, 'C', confirmation='purga')

        self.assertFalse(wizard.requirements_ok)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())
        self.assertTrue(lot.exists())

    def test_08_modo_c_elimina_operaciones_en_borrador(self):
        """Las operaciones SV en borrador sí son eliminables legalmente."""
        guia = self._make_guia('LC-C-08')
        lot = self._make_lot(guia, 'SV00000000405')
        draft = self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Borrador de prueba',
        })
        self.assertEqual(draft.state, 'draft')
        wizard = self._wizard(guia, 'C', confirmation='PURGAR')
        self.assertTrue(
            wizard.requirements_ok,
            'Un lote con solo operaciones en borrador sigue siendo técnico')
        self.assertFalse(wizard.purge_blockers)

        action = wizard.action_run()

        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')
        self.assertFalse(self.Operation.search([('id', '=', draft.id)]))
        self.assertFalse(self.StockLot.search([('id', '=', lot.id)]))
        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))


    def test_09_modo_c_bloqueado_por_operaciones_no_eliminables(self):
        """Aplicadas/reversadas y rechazadas bloquean la purga."""
        guia = self._make_guia('LC-C-09')
        lot = self._make_lot(guia, 'SV00000000406')
        self._rebaja(lot, 5.0)
        wizard = self._wizard(guia, 'C', confirmation='PURGAR')
        self.assertFalse(wizard.requirements_ok)
        self.assertIn('aplicadas o reversadas', wizard.purge_blockers)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(lot.exists())

        guia_rej = self._make_guia('LC-C-09B')
        lot_rej = self._make_lot(guia_rej, 'SV00000000407')
        rejected = self.Operation.create({
            'lot_id': lot_rej.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': 1.0,
            'reason': 'Rechazada de prueba',
        })
        rejected.write({'state': 'rejected'})
        wizard_rej = self._wizard(guia_rej, 'C', confirmation='PURGAR')
        self.assertIn('rechazadas', wizard_rej.purge_blockers)
        with self.assertRaises(UserError):
            wizard_rej.action_run()
        self.assertTrue(lot_rej.exists())

    # ── Modo D — Bloquear y escalar ───────────────────────────────────────
    def test_10_modo_d_bloquea_audita_y_no_elimina(self):
        """Con trazas reales: lista de bloqueadores, evento y cero borrado."""
        guia = self._make_guia('LC-D-10')
        lot = self._make_lot(guia, 'SV00000000408', technical=False)
        self._receipt_done(guia, lot, quantity=10.0)
        self._rebaja(lot, 3.0)

        wizard = self._wizard(guia, 'D')
        self.assertTrue(wizard.requirements_ok)
        self.assertTrue(wizard.blocker_count > 0)
        for token in ('lote(s) vinculados', 'movimiento(s) de stock',
                      'stock.quant', 'operación(es) SV'):
            self.assertIn(token, wizard.blockers)

        action = wizard.action_run()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'danger')
        self.assertIn('lote', action['params']['message'])
        # Nada se eliminó.
        self.assertTrue(guia.exists())
        self.assertTrue(lot.exists())
        self.assertTrue(self.Picking.search([('origin', '=', 'LC-D-10')]))
        self.assertTrue(
            self.Move.search([('move_line_ids.lot_id', '=', lot.id)]))
        self.assertTrue(self.Quant.search([('lot_id', '=', lot.id)]))
        self.assertTrue(self.Operation.search([('lot_id', '=', lot.id)]))
        logs = self.AuditLog.search([
            ('action_type', '=', 'guia_delete_blocked'),
            ('description', 'ilike', 'LC-D-10'),
        ])
        self.assertEqual(len(logs), 1, 'Falta la auditoría de bloqueo')
        self.assertEqual(logs.guia_processing_id, guia)

    def test_11_modo_d_bloquea_por_logistica_y_facturacion(self):
        """Contenedor, embarque y consolidación aparecen como bloqueadores."""
        guia = self._make_guia('LC-D-11')
        lot = self._make_lot(guia, 'SV00000000409')
        shipment = self.env['lumber.export.shipment'].create({
            'name': 'EMB-LC-11',
            'customer_id': self.partner.id,
        })
        container = self.env['lumber.container'].create({
            'name': 'CTN-LC-11',
            'container_type': '40HC',
            'shipment_id': shipment.id,
        })
        self.env['lumber.shipment.line'].create({
            'shipment_id': shipment.id,
            'container_id': container.id,
            'lot_id': lot.id,
        })
        consolidation = self.env['lumber.billing.consolidation'].create({
            'name': 'CONS-LC-11',
            'company_id': self.env.company.id,
            'currency_id': self.env.company.currency_id.id,
            'shipment_id': shipment.id,
        })
        self.env['lumber.billing.consolidation.line'].create({
            'consolidation_id': consolidation.id,
            'lot_id': lot.id,
            'product_id': self.product.id,
            'name': 'Línea de consolidación de prueba',
        })

        wizard = self._wizard(guia, 'D')
        for token in ('contenedor(es)', 'embarque(s)', 'consolidación(es)'):
            self.assertIn(token, wizard.blockers)
        with self.assertRaises(UserError):
            self._wizard(guia, 'C', confirmation='PURGAR').action_run()


    def test_12_lista_completa_de_bloqueadores(self):
        """Las doce categorías de traza se listan (incluye factura)."""
        guia = self._make_guia('LC-D-12')
        lot = self._make_lot(guia, 'SV00000000410')
        wizard = self._wizard(guia, 'D')
        dummy = [object()]
        diag = {
            'guia': guia,
            'state': 'draft',
            'lots': lot,
            'technical_lots': self.StockLot,
            'pickings': dummy,
            'moves': dummy,
            'move_lines': dummy,
            'quants': dummy,
            'nonzero_quants': dummy,
            'operations': dummy,
            'applied_ops': dummy,
            'draft_ops': self.Operation,
            'rejected_ops': dummy,
            'cost_lines': dummy,
            'valuations': dummy,
            'billing_lines': dummy,
            'consolidations': dummy,
            'invoices': dummy,
            'containers': dummy,
            'shipments': dummy,
            'period_closed': True,
            'messages': dummy,
            'attachments': dummy,
            'generic_refs': {'mail.activity': 1},
        }
        trace = wizard._trace_blockers(diag)
        for token in ('lote(s) vinculados', 'albarán(es)',
                      'movimiento(s) de stock', 'línea(s) de movimiento',
                      'stock.quant', 'operación(es) SV', 'línea(s) de costo',
                      'capa(s) de valoración', 'consolidación(es)',
                      'factura(s)', 'contenedor(es)', 'embarque(s)',
                      'mensaje(s) de chatter', 'adjunto(s) de evidencia',
                      'referencia(s) genérica(s)', 'mail.activity',
                      'período financiero cerrado'):
            self.assertTrue(
                any(token in message for message in trace),
                'Falta el bloqueador «%s»' % token)
        purge = wizard._purge_blockers(diag)
        for token in ('historia material', 'aplicadas o reversadas',
                      'rechazadas', 'cantidad distinta de cero',
                      'stock.quant', 'capa(s) de valoración',
                      'consolidación(es)', 'factura(s)', 'contenedor(es)',
                      'embarque(s)', 'mensaje(s) de chatter',
                      'adjunto(s) de evidencia', 'referencia(s) genérica(s)',
                      'período financiero cerrado'):
            self.assertTrue(
                any(token in message for message in purge),
                'Falta el bloqueador de purga «%s»' % token)

    def test_13_diagnostico_es_solo_lectura(self):
        """Diagnosticar no escribe, no borra y no crea nada."""
        guia = self._make_guia('LC-D-13')
        lot = self._make_lot(guia, 'SV00000000411', technical=False)
        self._receipt_done(guia, lot, quantity=10.0)
        before = {
            'write_date': guia.write_date,
            'state': guia.state,
            'pickings': self.Picking.search_count([('origin', '=', 'LC-D-13')]),
            'moves': self.Move.search_count(
                [('move_line_ids.lot_id', '=', lot.id)]),
            'quants': self.Quant.search_count([('lot_id', '=', lot.id)]),
            'operations': self.Operation.search_count(
                [('lot_id', '=', lot.id)]),
            'lots': self.StockLot.search_count(
                [('volume_source_guia_id', '=', guia.id)]),
        }
        wizard = self._wizard(guia, 'D')
        wizard._lifecycle_diagnosis()
        self.assertTrue(wizard.blockers)
        guia.invalidate_recordset()
        self.assertEqual(guia.write_date, before['write_date'])
        self.assertEqual(guia.state, before['state'])
        self.assertEqual(
            self.Picking.search_count([('origin', '=', 'LC-D-13')]),
            before['pickings'])
        self.assertEqual(
            self.Move.search_count([('origin', '=', 'LC-D-13')]),
            before['moves'])
        self.assertEqual(
            self.Quant.search_count([('lot_id', '=', lot.id)]),
            before['quants'])
        self.assertEqual(
            self.Operation.search_count([('lot_id', '=', lot.id)]),
            before['operations'])
        self.assertEqual(
            self.StockLot.search_count(
                [('volume_source_guia_id', '=', guia.id)]), before['lots'])
        self.assertFalse(
            self.AuditLog.search([
                ('action_type', 'in', ('guia_delete_blocked',
                                       'guia_delete_permanent',
                                       'guia_purged')),
                ('description', 'ilike', 'LC-D-13'),
            ]),
            'Diagnosticar no debe registrar eventos de auditoría')

    def test_14_consola_abre_el_ciclo_de_vida(self):
        """La Consola abre el asistente con la guía origen precargada."""
        guia = self._make_guia('LC-14')
        self.env.invalidate_all()
        console = self.env['madenat.lumber.intake.console'].search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía')
        action = console.action_open_guide_lifecycle()
        self.assertEqual(
            action['res_model'], 'madenat.lumber.intake.guide.lifecycle')
        self.assertEqual(
            action['context']['default_guia_processing_id'], guia.id)
        self.assertEqual(action['context']['default_console_id'], console.id)


    # ── Evidencia documental (regla del Modo C) ───────────────────────────
    def _attach_pdf(self, guia, name):
        return self.env['ir.attachment'].create({
            'name': name,
            'res_model': 'madenat.guia.processing',
            'res_id': guia.id,
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(b'%PDF-1.4 evidencia de la guia'),
        })

    def test_15_evidencia_documental_bloquea_purga_y_eliminacion(self):
        """Guía elegible para Modo C con PDF/chatter: se bloquea la purga."""
        guia = self._make_guia('LC-C-15')
        lot = self._make_lot(guia, 'SV00000000412')
        attachment = self._attach_pdf(guia, 'guia-LC-C-15.pdf')
        guia.message_post(
            body='Evidencia documental del ingreso', message_type='notification')

        wizard = self._wizard(guia, 'C', confirmation='PURGAR')
        self.assertFalse(
            wizard.requirements_ok,
            'La evidencia documental debe bloquear la purga')
        blockers = wizard.purge_blockers or ''
        self.assertIn('adjunto(s) de evidencia', blockers)
        self.assertIn('mensaje(s) de chatter', blockers)
        with self.assertRaises(UserError):
            wizard.action_run()

        # Modo A — FASE 2 (Modo A autoservicio en desarrollo): en el entorno de
        # PRUEBAS (BD 'madenat_test' + `--test-enable`, vía
        # `_lifecycle_dev_environment_ok()`) la evidencia DOCUMENTAL
        # (chatter/adjuntos/referencias genéricas) ya NO bloquea el Modo A,
        # porque no representa movimiento real de inventario. El lote TÉCNICO
        # creado arriba SÍ sigue bloqueando (categoría 'lots', material, no
        # relajada): por eso la aserción cambia de los tokens de evidencia
        # documental al bloqueador del lote.
        wizard_a = self._wizard(guia, 'A', acknowledge=True)
        self.assertFalse(wizard_a.requirements_ok)
        self.assertIn('lote(s) vinculados', wizard_a.blockers)
        self.assertNotIn('adjunto(s) de evidencia', wizard_a.blockers or '')
        self.assertNotIn('mensaje(s) de chatter', wizard_a.blockers or '')
        self.assertNotIn('referencia(s) genérica(s)', wizard_a.blockers or '')
        with self.assertRaises(UserError):
            wizard_a.action_run()

        # Nada se eliminó y el documento sigue disponible.
        self.assertTrue(guia.exists())
        self.assertTrue(lot.exists())
        self.assertTrue(attachment.exists())
        self.assertEqual(attachment.res_model, 'madenat.guia.processing')
        self.assertEqual(attachment.res_id, guia.id)

        # Modo D registra el inventario de evidencia en la auditoría firmada.
        self._wizard(guia, 'D').action_run()
        log = self.AuditLog.search([
            ('action_type', '=', 'guia_delete_blocked'),
            ('description', 'ilike', 'LC-C-15'),
        ], limit=1)
        self.assertTrue(log, 'Falta la auditoría de bloqueo')
        snapshot = json.loads(log.audit_snapshot)
        self.assertIn(
            'guia-LC-C-15.pdf',
            [item['name'] for item in snapshot['evidence_attachments']])
        self.assertTrue(snapshot['evidence_messages'])
        self.assertTrue(log.audit_hash)

    def test_16_referencia_generica_res_model_res_id_bloquea(self):
        """Una referencia genérica persistente (mail.activity) bloquea C."""
        guia = self._make_guia('LC-C-16')
        lot = self._make_lot(guia, 'SV00000000413')
        activity_type = self.env['mail.activity.type'].search([], limit=1)
        self.assertTrue(activity_type, 'Se requiere un tipo de actividad')
        self.env['mail.activity'].create({
            'res_model': 'madenat.guia.processing',
            'res_model_id': self.env['ir.model']._get_id(
                'madenat.guia.processing'),
            'res_id': guia.id,
            'activity_type_id': activity_type.id,
            'user_id': self.env.user.id,
            'summary': 'Revisar guía antes de purgar',
        })

        wizard = self._wizard(guia, 'C', confirmation='PURGAR')
        self.assertFalse(wizard.requirements_ok)
        blockers = wizard.purge_blockers or ''
        self.assertIn('referencia(s) genérica(s)', blockers)
        self.assertIn('mail.activity', blockers)
        with self.assertRaises(UserError):
            wizard.action_run()
        self.assertTrue(guia.exists())
        self.assertTrue(lot.exists())

    def test_17_sin_evidencia_la_purga_sigue_vigente(self):
        """Sin evidencia ni trazas, el Modo C sigue operativo.

        El aviso automático de creación de `mail.thread` no es evidencia: la
        guía recién creada tiene mensajes técnicos pero cero evidencia
        documental.
        """
        guia = self._make_guia('LC-C-17')
        lot = self._make_lot(guia, 'SV00000000414')
        self.assertTrue(
            self.env['mail.message'].search_count([
                ('model', '=', 'madenat.guia.processing'),
                ('res_id', '=', guia.id)]),
            'La creación registra el aviso técnico de mail.thread')
        self.assertFalse(
            self.env['ir.attachment'].search_count([
                ('res_model', '=', 'madenat.guia.processing'),
                ('res_id', '=', guia.id)]))
        wizard = self._wizard(guia, 'C', confirmation='PURGAR')
        self.assertFalse(
            self._wizard(guia, 'D')._evidence_messages(guia),
            'El aviso técnico de creación no es evidencia documental')
        self.assertTrue(wizard.requirements_ok, wizard.purge_blockers)
        wizard.action_run()
        self.assertFalse(self.Guia.search([('id', '=', guia.id)]))
        self.assertFalse(self.StockLot.search([('id', '=', lot.id)]))

    # ── Modo A en desarrollo: regresión de seguridad del entorno ──────────
    def test_18_modo_a_no_se_relaja_fuera_de_entorno_test(self):
        """REGRESIÓN DE SEGURIDAD: fuera de entorno de test el Modo A no se relaja.

        Fase 2 (Modo A autoservicio en desarrollo): la relajación de las trazas
        DOCUMENTALES exige `_lifecycle_dev_environment_ok()`, que delega en
        `madenat.sv.internal.marker._sv_test_environment_ok()` (BD con 'test' en
        el nombre **y** `--test-enable`). Aquí se simula PRODUCCIÓN (la guarda
        canónica devuelve False) y se verifica que el Modo A vuelve a bloquear
        ante evidencia documental exactamente como antes del cambio: si alguien
        quitara la condición de entorno, este test debe fallar.
        """
        guia = self._make_guia('LC-A-18')
        self._attach_pdf(guia, 'guia-LC-A-18.pdf')
        guia.message_post(
            body='Evidencia documental del ingreso', message_type='notification')
        wizard = self._wizard(guia, 'A', acknowledge=True)

        # 1) Entorno de PRUEBAS real: sin trazas materiales (ni lote, ni
        #    picking, ni movimiento), la evidencia documental no bloquea.
        self.assertTrue(wizard.requirements_ok, wizard.blockers)
        self.assertFalse(wizard.blockers)

        # 2) PRODUCCIÓN simulada: la guarda canónica de entorno → False.
        marker_cls = type(self.env['madenat.sv.internal.marker'])
        with patch.object(marker_cls, '_sv_test_environment_ok',
                          lambda self: False):
            wizard.invalidate_recordset()
            self.assertFalse(
                wizard.requirements_ok,
                'Fuera de entorno de test el Modo A debe seguir bloqueado')
            self.assertIn('adjunto(s) de evidencia', wizard.blockers or '')
            self.assertIn('mensaje(s) de chatter', wizard.blockers or '')
            with self.assertRaises(UserError):
                wizard.action_run()

        # Nada se borró: la eliminación quedó bloqueada como antes del cambio.
        self.assertTrue(guia.exists())

    # ── Modo A autoservicio vía `ir.config_parameter` (sin --test-enable) ──
    def _restore_dev_param(self):
        """Deja el parámetro de desarrollo en su estado previo (limpio)."""
        icp = self.env['ir.config_parameter'].sudo()
        icp.search([('key', '=', DEV_CLEANUP_PARAM)]).unlink()
        # `ir.config_parameter._get_param` usa `@ormcache`: la caché sobrevive
        # al rollback del TransactionCase, por lo que se limpia explícitamente.
        self.env.registry.clear_cache()

    def test_19_modo_a_se_relaja_via_config_parameter_sin_test_enable(self):
        """El parámetro de desarrollo habilita el Modo A SIN `--test-enable`.

        Es la vía que reemplaza a `--test-enable` en el servidor persistente.
        Se simula el servidor real (`test_enable` en False) y se verifica que
        la relajación DOCUMENTAL del Modo A funciona solo por el parámetro.
        """
        self.addCleanup(self._restore_dev_param)
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param(DEV_CLEANUP_PARAM, 'True')
        guia = self._make_guia('LC-A-19')
        self._attach_pdf(guia, 'guia-LC-A-19.pdf')
        guia.message_post(
            body='Evidencia documental del ingreso', message_type='notification')
        wizard = self._wizard(guia, 'A', acknowledge=True)

        with patch.dict(odoo.tools.config.options, {'test_enable': False}):
            wizard.invalidate_recordset()
            marker = self.env['madenat.sv.internal.marker'].sudo()
            self.assertFalse(
                marker._sv_test_enable_strict(),
                'Se está simulando el servidor real sin --test-enable')
            self.assertTrue(
                marker._sv_test_environment_ok(),
                'El parámetro debe habilitar la vía alternativa')
            self.assertTrue(
                wizard.requirements_ok,
                'Con el parámetro activo el Modo A debe estar disponible: %s'
                % wizard.blockers)
            self.assertFalse(wizard.blockers)
            action = wizard.action_run()

        self.assertFalse(
            self.Guia.search([('id', '=', guia.id)]),
            'El Modo A autoservicio debe eliminar la guía')
        self.assertEqual(action.get('res_model'),
                         'madenat.lumber.intake.console')
        logs = self.AuditLog.search([
            ('action_type', '=', 'guia_delete_permanent'),
            ('guia_processing_id', '=', False),
        ], limit=1)
        self.assertTrue(logs, 'La eliminación deja auditoría firmada')

    def test_20_modo_a_no_se_relaja_con_parametro_falso_o_ausente(self):
        """Sin `--test-enable` y sin parámetro, el Modo A vuelve a bloquear."""
        self.addCleanup(self._restore_dev_param)
        icp = self.env['ir.config_parameter'].sudo()
        guia = self._make_guia('LC-A-20')
        self._attach_pdf(guia, 'guia-LC-A-20.pdf')
        guia.message_post(
            body='Evidencia documental del ingreso', message_type='notification')
        wizard = self._wizard(guia, 'A', acknowledge=True)

        for value in (False, 'False'):
            icp.set_param(DEV_CLEANUP_PARAM, value)
            with patch.dict(odoo.tools.config.options, {'test_enable': False}):
                wizard.invalidate_recordset()
                self.assertFalse(
                    wizard.requirements_ok,
                    'Sin ninguna vía activa el Modo A debe seguir bloqueado')
                self.assertIn('adjunto(s) de evidencia', wizard.blockers or '')
                self.assertIn('mensaje(s) de chatter', wizard.blockers or '')
                with self.assertRaises(UserError):
                    wizard.action_run()

        self.assertTrue(guia.exists(), 'Nada se borró: bloqueo efectivo')


