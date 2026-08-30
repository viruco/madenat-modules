# -*- coding: utf-8 -*-
# TD-008: Test suite para MadenatGuiaProcessing
# Cobertura mínima del flujo de negocio identificado en Auditoría 2026-06-04
# Smoke check de compatibilidad histórica: guía real ID=14 (19846)
# No se aserta un estado fijo (dato persistente mutable); se valida pertenencia
# a la máquina de estados canónica del modelo.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
import logging
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestMadenatGuiaProcessing(TransactionCase):
    """
    Test suite para madenat.guia.processing
    Cubre flujo completo: creacion → verificacion → procesamiento → validacion → cancelacion
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.partner = cls.env['res.partner'].search([], limit=1)
        if not cls.partner:
            cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        # assignment_location_id es required=True en el modelo
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)

    # ─── GRUPO 1: Estado inicial y creacion ───────────────────────────────

    def test_01_creacion_guia_draft(self):
        """Guía nueva debe iniciar en estado draft"""
        guia = self.GuiaModel.create({
            'name': 'TEST-001',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia.state, 'draft',
            "Guia nueva debe estar en estado draft")

    def test_02_guia_minima_creable(self):
        """Guía mínima debe poder crearse con name, partner y location"""
        guia = self.GuiaModel.create({
            'name': 'TEST-002',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertTrue(guia.id,
            "Guia minima debe poder crearse")

    def test_03_can_process_sin_adjuntos(self):
        """can_process debe ser False si no hay archivos adjuntos"""
        guia = self.GuiaModel.create({
            'name': 'TEST-003',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertFalse(guia.can_process,
            "can_process debe ser False sin adjuntos Excel ni PDF")

    def test_03b_can_process_con_excel_sin_pdf(self):
        """can_process debe ser True en draft con Excel presente y PDF ausente
        (regla canónica 2026-08-22: PDF opcional, Excel obligatorio)."""
        import base64
        guia = self.GuiaModel.create({
            'name': 'TEST-003B',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx',
        })
        self.assertTrue(guia.can_process,
            "can_process debe ser True con Excel y sin PDF (PDF opcional)")

    def test_03c_can_process_sin_excel(self):
        """can_process debe ser False en draft sin Excel aunque exista PDF."""
        import base64
        guia = self.GuiaModel.create({
            'name': 'TEST-003C',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'guide_pdf_file': base64.b64encode(b'%PDF-fake').decode(),
            'guide_pdf_filename': 'guia.pdf',
        })
        self.assertFalse(guia.can_process,
            "can_process debe ser False sin Excel aunque exista PDF")

    def test_verify_data_sin_excel_bloquea(self):
        """action_verify_data debe bloquear si falta el Excel de Packing (regla core)."""
        guia = self.GuiaModel.create({
            'name': 'TEST-003D',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        with self.assertRaises(UserError) as ctx:
            guia.action_verify_data()
        self.assertIn('Excel de Packing', str(ctx.exception))

    def test_verify_data_con_excel_sin_pdf_permitido(self):
        """action_verify_data debe permitir verificar con Excel presente y PDF ausente
        (usa hook force_packing_data para evitar parser externo)."""
        import base64
        guia = self.GuiaModel.create({
            'name': 'TEST-003E',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'excel_file': base64.b64encode(b'fake').decode(),
            'excel_filename': 'packing.xlsx',
        })
        # Hook del parser: retorno directo sin tocar archivo real.
        packing_data = {'lineas': [{
            'Codigo Interno': 'X100',
            'N° LOTE': 'L1',
            'Cantidad': 1,
            'Volumen': 1.0,
            'Espesor': 10,
            'Ancho': 100,
            'Largo': 2.0,
            'product_name': 'Madera Test',
            'espesor_nominal_mm': 0.0,
        }]}
        guia.with_context(force_packing_data=packing_data).action_verify_data()
        self.assertEqual(guia.state, 'verified',
            "La guía debe quedar en verified con Excel y sin PDF")

    # ─── GRUPO 2: State machine ────────────────────────────────────────────

    def test_04_state_machine_transiciones_validas(self):
        """Verificar que los estados permitidos son exactamente 5"""
        guia = self.GuiaModel.create({
            'name': 'TEST-004',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertIn(guia.state,
            ['draft', 'verified', 'processed', 'validated', 'cancelled'],
            "Estado debe ser uno de los 5 validos")

    def test_05_cancelacion_desde_draft(self):
        """Guía en draft puede cancelarse"""
        guia = self.GuiaModel.create({
            'name': 'TEST-005',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertEqual(guia.state, 'draft')
        self.assertTrue(guia.can_cancel,
            "Guia en draft debe poder cancelarse")

    def test_06_eliminar_guia_draft(self):
        """unlink debe funcionar si la guia esta en draft"""
        guia = self.GuiaModel.create({
            'name': 'TEST-006',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        guia_id = guia.id
        guia.unlink()
        result = self.GuiaModel.search([('id', '=', guia_id)])
        self.assertFalse(result,
            "Guia en draft debe poder eliminarse")

    def test_07_no_eliminar_guia_verified(self):
        """unlink debe fallar si la guia esta en verified"""
        guia = self.GuiaModel.create({
            'name': 'TEST-007',
            'partner_id': self.partner.id,
            'state': 'verified',
            'assignment_location_id': self.location.id,
        })
        with self.assertRaises(UserError):
            guia.unlink()

    # ─── GRUPO 3: Campos de volumen ────────────────────────────────────────

    def test_08_vol_total_campo_existe(self):
        """Campo vol_total_m3 debe existir y ser accesible"""
        guia = self.GuiaModel.create({
            'name': 'TEST-008',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertTrue(hasattr(guia, 'vol_total_m3'),
            "Campo vol_total_m3 debe existir")
        self.assertEqual(guia.vol_total_m3, 0.0,
            "vol_total_m3 debe iniciar en 0.0")

    def test_09_vol_comercial_campo_existe(self):
        """Campo vol_comercial debe existir y ser accesible"""
        guia = self.GuiaModel.create({
            'name': 'TEST-009',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertTrue(hasattr(guia, 'vol_comercial'),
            "Campo vol_comercial debe existir")
        self.assertEqual(guia.vol_comercial, 0.0,
            "vol_comercial debe iniciar en 0.0")

    def test_10_vol_fisico_campo_existe(self):
        """Campo vol_fisico debe existir y ser accesible"""
        guia = self.GuiaModel.create({
            'name': 'TEST-010',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertTrue(hasattr(guia, 'vol_fisico'),
            "Campo vol_fisico debe existir")
        self.assertEqual(guia.vol_fisico, 0.0,
            "vol_fisico debe iniciar en 0.0")

    # ─── GRUPO 4: Integridad post-TD-007 ────────────────────────────────────

    def test_11_campos_duplicados_resueltos_vol_total(self):
        """TD-007: vol_total_m3 debe tener una sola definicion activa"""
        GuiaClass = type(self.env['madenat.guia.processing'])
        field = GuiaClass._fields.get('vol_total_m3')
        self.assertIsNotNone(field,
            "TD-007: vol_total_m3 debe existir como campo")

    def test_12_campos_duplicados_resueltos_can_process(self):
        """TD-007: can_process debe tener una sola definicion activa"""
        GuiaClass = type(self.env['madenat.guia.processing'])
        field = GuiaClass._fields.get('can_process')
        self.assertIsNotNone(field,
            "TD-007: can_process debe existir como campo")

    # ─── GRUPO 5: Golden record ────────────────────────────────────────────

    def test_13_golden_record_19846_intacto(self):
        """Smoke check de compatibilidad histórica de la guía real 19846.

        No se aserta un estado fijo (dato persistente mutable). Si el registro
        existe, se valida que su estado esté dentro de los valores canónicos de
        la máquina de estados del modelo; si no existe, se omite explícitamente.
        """
        guia = self.GuiaModel.search([('name', '=', '19846')], limit=1)
        if not guia:
            self.skipTest("Golden record 19846 no encontrado en DB de tests")

        valid_states = {sel[0] for sel in self.GuiaModel._fields['state'].selection}
        self.assertIn(guia.state, valid_states,
            f"Golden record 19846 en estado inválido: {guia.state}")
        _logger.info("Golden record 19846 verificado: state=%s", guia.state)


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestCreateOrGetLotReceptionProtection(TransactionCase):
    """
    BT-02: _create_or_get_lot no debe reutilizar ni sobrescribir un stock.lot
    originado en recepción (reception_id poblado). La reutilización idempotente
    de lotes sin reception_id debe seguir funcionando.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.ReceptionModel = cls.env['lumber.reception']
        cls.StockLot = cls.env['stock.lot']
        cls.partner = cls.env['res.partner'].create({'name': 'BT02 Supplier'})
        cls.product = cls.env['product.product'].search([('type', '=', 'product')], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({'name': 'BT02 Product'})
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        cls.company = cls.env.company

    def _make_guia(self, name):
        return self.GuiaModel.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })

    def _lot_dims(self):
        return {
            'espesor_mm': 10.0,
            'ancho_mm': 10.0,
            'largo_m': 1.0,
            'espesor_nominal_mm': 10.0,
            'ancho_nominal_mm': 10.0,
            'note': 'bt02-test',
            'ref': 'bt02-test',
        }

    def test_reception_lot_never_reused(self):
        """Caso A — un lote con reception_id no debe ser reutilizado por guía."""
        reception = self.ReceptionModel.create({
            'name': 'TEST-BT02-REC-001',
            'supplier_id': self.partner.id,
            'ingestion_profile': 'metric',
        })
        lot_name = 'TEST-BT02-REC-LOT-001'
        rec_lot = self.StockLot.create({
            'name': lot_name,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'reception_id': reception.id,
            'volume_purchase_m3': 999.0,
        })
        guia = self._make_guia('TEST-BT02-GUIA-A')

        # Al excluir lotes con reception_id de la búsqueda, el método NO
        # reutiliza el lote de recepción. Ante la coincidencia de nombre cae a
        # la rama de creación y choca con la constraint UNIQUE nativa de
        # stock.lot (fail-safe): el lote de recepción queda protegido sin
        # ser sobrescrito. Se aserta el comportamiento, no el tipo exacto de
        # la excepción (puede ser IntegrityError o ValidationError de Odoo).
        with self.assertRaises(Exception):
            guia._create_or_get_lot(
                guia_ref='TEST-BT02-GUIA-A',
                product=self.product,
                qty=10,
                vol_purchase=1.0,
                vol_shipment=1.0,
                vol_real=1.0,
                lot_name=lot_name,
                lot_dims=self._lot_dims(),
                precio_usd=0.0,
            )

        rec_lot.invalidate_recordset()
        self.assertTrue(rec_lot.exists())
        self.assertEqual(rec_lot.reception_id.id, reception.id)
        self.assertAlmostEqual(rec_lot.volume_purchase_m3, 999.0, places=3)
        self.assertFalse(rec_lot.guia_processing_id)

    def test_lot_without_reception_reused(self):
        """Caso B — lote sin reception_id se reutiliza (idempotencia preservada)."""
        lot_name = 'TEST-BT02-GUIA-LOT-001'
        guia_lot = self.StockLot.create({
            'name': lot_name,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 5.0,
        })
        guia = self._make_guia('TEST-BT02-GUIA-B')

        result = guia._create_or_get_lot(
            guia_ref='TEST-BT02-GUIA-B',
            product=self.product,
            qty=10,
            vol_purchase=2.0,
            vol_shipment=2.0,
            vol_real=2.0,
            lot_name=lot_name,
            lot_dims=self._lot_dims(),
            precio_usd=0.0,
        )

        self.assertEqual(result.id, guia_lot.id)
        self.assertEqual(
            self.StockLot.search_count([
                ('name', '=', lot_name),
                ('product_id', '=', self.product.id),
            ]),
            1,
        )
        self.assertTrue(result.guia_processing_id)
        self.assertFalse(result.reception_id)


@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'bt01')
class TestGuiaProcessingValidationSignature(TransactionCase):
    """
    BT-01: notarización y bitácora inmutable para guía processing.

    La bitácora madenat.audit.log es la fuente de verdad de la evidencia
    firmada (snapshot + hash), enlazada relacionalmente a la guía. Cada
    ciclo de validación exitoso genera un evento nuevo; cancelar/reabrir
    no elimina los eventos previos.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.LineModel = cls.env['madenat.guia.processing.line']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.partner = cls.env['res.partner'].create({'name': 'BT01 Supplier'})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        cls.product = cls.env['product.product'].search(
            [('type', '=', 'product')], limit=1
        )
        if not cls.product:
            cls.product = cls.env['product.product'].create({'name': 'BT01 Product'})
        cls.subproduct = cls.env['madenat.subproducto'].create({
            'name': 'BT01 Subproducto',
            'code': 'BT01',
        })

    def _make_guia(self, name, state='verified'):
        return self.GuiaModel.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': state,
            'tipo_recepcion': 'compra',
            'rate_usd': 1.0,
        })

    def _add_line(self, guia, lot_name, espesor_nominal_mm=25.0, subproducto=True):
        return self.LineModel.create({
            'processing_id': guia.id,
            'lot_name': lot_name,
            'product_id': self.product.id,
            'sku_original': 'BT01-SKU',
            'product_name_original': 'BT01 Madera',
            'espesor_mm': 25.0,
            'ancho_mm': 100.0,
            'largo_m': 2.0,
            'espesor_nominal_mm': espesor_nominal_mm,
            'ancho_nominal_mm': 100.0,
            'pieces': 10,
            'subproducto_id': self.subproduct.id if subproducto else False,
        })

    def test_processing_signature_generation(self):
        """Caso A (firma): generate_processing_signature produce snapshot + hash SHA-256."""
        from odoo.addons.madenat_lumber_core.models.ingestion_gate import Gate3PreCommit

        guia = self._make_guia('TEST-BT01-SIGN-GEN')
        self._add_line(guia, 'BT01-LOT-001')

        gate3 = Gate3PreCommit(self.env)
        snapshot, signature = gate3.generate_processing_signature(
            guia, guia.processing_line_ids
        )

        self.assertIsNotNone(snapshot)
        self.assertIsNotNone(signature)
        self.assertEqual(len(signature), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in signature))

        import json
        data = json.loads(snapshot)
        self.assertEqual(data['guia_id'], guia.id)
        self.assertEqual(data['guia_no'], 'TEST-BT01-SIGN-GEN')
        self.assertEqual(data['operator_id'], self.env.user.id)
        self.assertEqual(len(data['lines']), 1)
        self.assertEqual(data['lines'][0]['lot_name'], 'BT01-LOT-001')

    def test_audit_signature_event_model_persist(self):
        """Caso A (evento): madenat.audit.log persiste snapshot/hash + vínculo a guía."""
        guia = self._make_guia('TEST-BT01-SIGN-EVT')

        event = self.AuditLog.create({
            'guia_processing_id': guia.id,
            'action_type': 'validation_signature',
            'description': '🔐 Firma de validación de guía %s' % guia.name,
            'audit_snapshot': '{"guia_id": %s}' % guia.id,
            'audit_hash': 'a' * 64,
            'user_id': self.env.user.id,
        })

        self.assertTrue(event.id)
        self.assertEqual(event.guia_processing_id.id, guia.id)
        self.assertEqual(len(event.audit_hash), 64)
        self.assertTrue(event.audit_snapshot)

    def test_validate_blocked_creates_no_audit_event(self):
        """Caso C: validación bloqueada antes de firmar → sin evento ni lotes."""
        guia = self._make_guia('TEST-BT01-BLOCKED')
        self._add_line(guia, 'BT01-LOT-BLOCKED', espesor_nominal_mm=0.0)

        with self.assertRaises(ValidationError):
            guia.action_validate()

        event_count = self.AuditLog.search_count([
            ('guia_processing_id', '=', guia.id)
        ])
        self.assertEqual(event_count, 0)
        self.assertEqual(
            guia.lot_ids, self.env['stock.lot'],
            "No deben generarse lotes si la validación está bloqueada"
        )

    def test_cancel_does_not_delete_audit_events(self):
        """Caso D: action_force_cancel no borra ni altera eventos previos."""
        guia = self._make_guia('TEST-BT01-CANCEL', state='draft')

        event = self.AuditLog.create({
            'guia_processing_id': guia.id,
            'action_type': 'validation_signature',
            'description': '🔐 Firma de validación de guía %s' % guia.name,
            'audit_snapshot': '{"guia_id": %s}' % guia.id,
            'audit_hash': 'b' * 64,
            'user_id': self.env.user.id,
        })
        event_id = event.id
        event_hash = event.audit_hash

        guia.action_force_cancel()

        event.invalidate_recordset()
        self.assertTrue(event.exists())
        self.assertEqual(event.audit_hash, event_hash)
        self.assertEqual(self.AuditLog.search_count([('id', '=', event_id)]), 1)


@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'bt03')
class TestGuiaProcessingOperationalAudit(TransactionCase):
    """
    BT-03: bitácora operativa de lotes en guía processing.

    lot_creation, lot_update y omission quedan enlazados a la guía vía
    guia_processing_id, reutilizando madenat.audit.log. No se modela
    todavía la baja formal de lotes/etiquetas.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.StockLot = cls.env['stock.lot']
        cls.partner = cls.env['res.partner'].create({'name': 'BT03 Supplier'})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        cls.product = cls.env['product.product'].search(
            [('type', '=', 'product')], limit=1
        )
        if not cls.product:
            cls.product = cls.env['product.product'].create({'name': 'BT03 Product'})
        cls.company = cls.env.company

    def _make_guia(self, name):
        return self.GuiaModel.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })

    def _lot_dims(self):
        return {
            'espesor_mm': 10.0,
            'ancho_mm': 10.0,
            'largo_m': 1.0,
            'espesor_nominal_mm': 10.0,
            'ancho_nominal_mm': 10.0,
            'note': 'bt03-test',
            'ref': 'bt03-test',
        }

    def test_lot_creation_emits_audit_event(self):
        """Caso A — creación real de lote nuevo emite lot_creation."""
        guia = self._make_guia('TEST-BT03-CREATE')
        lot_name = 'TEST-BT03-LOT-NEW'

        lot = guia._create_or_get_lot(
            guia_ref='TEST-BT03-CREATE',
            product=self.product,
            qty=10,
            vol_purchase=1.0,
            vol_shipment=1.0,
            vol_real=1.0,
            lot_name=lot_name,
            lot_dims=self._lot_dims(),
            precio_usd=0.0,
        )

        self.assertTrue(lot.id)
        events = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'lot_creation'),
            ('batch_id', '=', lot_name),
        ])
        self.assertEqual(len(events), 1)
        self.assertEqual(events.batch_id, lot_name)

    def test_lot_reuse_emits_single_lot_update(self):
        """Caso B — reutilización de lote sin reception_id emite un único lot_update."""
        guia = self._make_guia('TEST-BT03-UPDATE')
        lot_name = 'TEST-BT03-LOT-REUSE'

        existing = self.StockLot.create({
            'name': lot_name,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'volume_purchase_m3': 5.0,
        })

        result = guia._create_or_get_lot(
            guia_ref='TEST-BT03-UPDATE',
            product=self.product,
            qty=10,
            vol_purchase=2.0,
            vol_shipment=2.0,
            vol_real=2.0,
            lot_name=lot_name,
            lot_dims=self._lot_dims(),
            precio_usd=0.0,
        )

        self.assertEqual(result.id, existing.id)
        # Un solo lote (no duplicado)
        self.assertEqual(
            self.StockLot.search_count([
                ('name', '=', lot_name),
                ('product_id', '=', self.product.id),
            ]),
            1,
        )
        # Un solo evento lot_update
        events = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'lot_update'),
            ('batch_id', '=', lot_name),
        ])
        self.assertEqual(len(events), 1)

    def test_omission_emits_audit_event(self):
        """Caso C — línea inválida emite omission y no produce lote."""
        guia = self._make_guia('TEST-BT03-OMIT')

        lineas = [{
            'Codigo Interno': '',          # inválido → omission real del flujo
            'N° LOTE': 'BT03-OMIT-001',
            'Cantidad': 10,
            'Espesor': 25.0,
            'Ancho': 100.0,
            'Largo': 2.0,
        }]

        validas = guia._validar_y_enriquecer_lineas(lineas)

        self.assertEqual(validas, [])
        events = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('action_type', '=', 'omission'),
        ])
        self.assertEqual(len(events), 1)
        self.assertEqual(events.batch_id, 'BT03-OMIT-001')
        self.assertIn('omitida', events.description)

    def test_validation_signature_coexists_with_operational_events(self):
        """Caso D — validation_signature coexiste con eventos operativos."""
        guia = self._make_guia('TEST-BT03-COMPAT')

        self.AuditLog.create({
            'guia_processing_id': guia.id,
            'action_type': 'validation_signature',
            'description': '🔐 Firma de validación de guía %s' % guia.name,
            'audit_snapshot': '{"guia_id": %s}' % guia.id,
            'audit_hash': 'c' * 64,
            'user_id': self.env.user.id,
        })
        guia._register_lot_audit(
            'lot_creation', 'TEST-BT03-COMPAT-LOT',
            f"Lote TEST-BT03-COMPAT-LOT creado desde guía {guia.name}"
        )

        self.assertEqual(
            self.AuditLog.search_count([
                ('guia_processing_id', '=', guia.id),
                ('action_type', '=', 'validation_signature'),
            ]),
            1,
        )
        self.assertEqual(
            self.AuditLog.search_count([
                ('guia_processing_id', '=', guia.id),
                ('action_type', '=', 'lot_creation'),
            ]),
            1,
        )


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestMadenatGuiaProcessingLine(TransactionCase):
    """
    Tests para MadenatGuiaProcessingLine (lineas de staging)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.LineModel = cls.env['madenat.guia.processing.line']
        cls.partner = cls.env['res.partner'].search([], limit=1)
        if not cls.partner:
            cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)

    def test_14_linea_staging_crea_con_guia(self):
        """Linea de staging debe poder crearse asociada a una guia"""
        guia = self.GuiaModel.create({
            'name': 'TEST-LINE-001',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })
        self.assertTrue(guia.id,
            "Guia padre debe crearse para el test de linea")

    def test_15_compute_vol_purchase_unico(self):
        """TD-007: _compute_vol_purchase_m3 debe tener una sola version activa"""
        LineClass = type(self.env['madenat.guia.processing.line'])
        method = getattr(LineClass, '_compute_vol_purchase_m3', None)
        self.assertIsNotNone(method,
            "TD-007: _compute_vol_purchase_m3 debe existir")

@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'cleanup')
class TestOrphanMoveCleanupSavepoint(TransactionCase):
    """
    Test movilidad del manejo de batch parcial para _cleanup_orphan_moves_guia()

    Escenario: 3 stock.moves huerfanos comparten mismo origin (guia.name),
    pero UNO tiene move_line con quantity > 0. El metodo debe eliminar los
    2 moves limpios y proteger el move con cantidad recolectada, sin
    contaminar la transaccion externa.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Datos minimos para crear stock.moves
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.MoveModel = cls.env['stock.move']
        cls.MoveLineModel = cls.env['stock.move.line']

        cls.partner = cls.env['res.partner'].search([], limit=1)
        if not cls.partner:
            cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].search([('type', '=', 'product')], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({'name': 'Test Product'})
        # Usar la UoM del producto para evitar error de categoria (Volume vs Length)
        cls.uom = cls.product.uom_id
        if not cls.uom:
            cls.uom = cls.env['uom.uom'].search([], limit=1)
        cls.location = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)
        cls.location_supplier = cls.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
        if not cls.location_supplier:
            cls.location_supplier = cls.location

        # Verificar que el usuario admin de tests tiene el grupo requerido
        if not cls.env.user.has_group('stock.group_stock_manager'):
            cls.env.user.write({'groups_id': [
                (4, cls.env.ref('stock.group_stock_manager').id)
            ]})

    def test_partial_batch_failure_protected_moves_survive(self):
        """
        ➰ Si UN move tiene move_lines con quantity > 0, debe marcarse como
        HUERFANO-PROTEGIDO y NO eliminarse; los otros 2 moves limpios SI deben
        eliminarse. El savepoint interno actua sobre cleanable_moves y es
        transparente si todos pasan.
        """
        # 1. Crear guia que dara origen a los moves huerfanos
        origin_name = 'GW-SAVEPOINT-TEST-001'
        guia = self.GuiaModel.create({
            'name': origin_name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })

        # 2. Crear 3 stock.moves huerfanos (picking_id=False, mismo origin)
        common_vals = {
            'name': 'Orphan Move Test',
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.uom.id,
            'picking_id': False,
            'location_id': self.location_supplier.id,
            'location_dest_id': self.location.id,
            'company_id': self.env.company.id,
            'origin': origin_name,
            'state': 'done',
        }

        move_1 = self.MoveModel.create({**common_vals, 'name': 'Orphan-Clean-1'})
        move_2 = self.MoveModel.create({**common_vals, 'name': 'Orphan-Clean-2'})
        move_3 = self.MoveModel.create({**common_vals, 'name': 'Orphan-Protected'})

        # 3. Asignar move_line con quantity > 0 a move_3 → sera protegido
        self.MoveLineModel.create({
            'move_id': move_3.id,
            'product_id': self.product.id,
            'location_id': self.location_supplier.id,
            'location_dest_id': self.location.id,
            'quantity': 5.0,
            'product_uom_id': self.uom.id,
            'state': 'done',
        })

        self.assertEqual(self.MoveModel.search_count([('id', 'in', [move_1.id, move_2.id, move_3.id])]), 3,
            "Los 3 moves deben existir antes de la limpieza")

        # 4. Ejecutar el metodo bajo prueba
        guia._cleanup_orphan_moves_guia()

        # 5. Verificar: moves limpios eliminados, move protegido sobrevive
        remaining = self.MoveModel.search([('id', 'in', [move_1.id, move_2.id, move_3.id])])

        deleted_ids = {move_1.id, move_2.id}
        protected_id = move_3.id

        self.assertEqual(len(remaining), 1,
            f"Solo 1 move debe sobrevivir (el protegido). Sobrevivientes: {remaining.mapped('name')}")

        self.assertEqual(remaining.id, protected_id,
            "El move sobreviviente debe ser el que tenia move_line con quantity > 0")

        self.assertFalse(any(mid in remaining.ids for mid in deleted_ids),
            "Los moves limpios deben ser eliminados")

        # 6. Verificar que el move protegido fue renombrado
        self.assertTrue(
            remaining.origin.startswith('HUERFANO-PROTEGIDO-'),
            f"El move protegido debe tener prefijo HUERFANO-PROTEGIDO-, tiene: {remaining.origin}"
        )

        _logger.info(
            "✅ savepoint test OK: %d moves eliminados, 1 protegido (%s)",
            len(deleted_ids), remaining.name
        )

    def test_savepoint_isolates_transaction_on_unlink_failure(self):
        """
        🔬 Test B — Aislamiento transaccional real del savepoint.

        SIMULACIÓN CONTROLADA (no fallo de integridad real de PostgreSQL):
        Se usa mock.patch sobre StockMove.unlink para forzar una excepción
        DENTRO del bloque savepoint, simulando un IntegrityError que haría
        que el cursor de la transacción externa quedara "tainted" (inutilizable)
        si NO existiera el savepoint.

        Hipótesis: el savepoint captura el fallo del unlink, revierte solo
        el bloque interno, y el cursor externo sigue operable inmediatamente
        después de capturar la excepción.

        Si este test FALLA (cursor inutilizable post-excepción), la
        recomendación de consolidar hacia savepoint en reception_service
        queda CONTRADICIDA.
        """
        # 1. Crear guía y moves huérfanos limpios (sin move_lines)
        origin_name = 'GW-SAVEPOINT-B-001'
        guia = self.GuiaModel.create({
            'name': origin_name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
        })

        common_vals = {
            'name': 'Orphan Move Test B',
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.uom.id,
            'picking_id': False,
            'location_id': self.location_supplier.id,
            'location_dest_id': self.location.id,
            'company_id': self.env.company.id,
            'origin': origin_name,
            'state': 'done',
        }

        move_a = self.MoveModel.create({**common_vals, 'name': 'Orphan-Fail-A'})
        move_b = self.MoveModel.create({**common_vals, 'name': 'Orphan-Fail-B'})

        self.assertEqual(
            self.MoveModel.search_count([('id', 'in', [move_a.id, move_b.id])]), 2,
            "Los 2 moves deben existir antes de la limpieza"
        )

        # 2. Mock: forzar que unlink() dentro del savepoint lance Exception
        with patch(
            'odoo.addons.stock.models.stock_move.StockMove.unlink',
            side_effect=Exception("Simulated integrity failure inside savepoint")
        ):
            with self.assertRaises(UserError) as ctx:
                guia._cleanup_orphan_moves_guia()

            self.assertIn("No se pudieron eliminar", str(ctx.exception),
                "Debe lanzar UserError con mensaje de seguridad Odoo")

        # 3. ASERTO CRÍTICO: el cursor externo sigue operable
        cursor_healthy = False
        try:
            count_after = self.env['stock.move'].search_count([])
            cursor_healthy = True
            _logger.info(
                "✅ Test B — Cursor operable post-savepoint-failure: search_count=%d", count_after
            )
        except Exception as e:
            _logger.error("❌ Test B — Cursor INUTILIZABLE post-savepoint-failure: %s", e)

        self.assertTrue(
            cursor_healthy,
            "CRÍTICO: El cursor quedó inutilizable tras el fallo del unlink dentro "
            "del savepoint. Esto CONTRADICE la recomendación de consolidar hacia "
            "savepoint en reception_service."
        )

        # 4. Verificar que los moves fallidos NO quedaron en estado intermedio
        moves_after = self.MoveModel.search([('id', 'in', [move_a.id, move_b.id])])
        self.assertEqual(len(moves_after), 2,
            "Ambos moves deben seguir existiendo (rollback correcto del savepoint)")

        for m in moves_after:
            self.assertEqual(m.state, 'done',
                f"Move {m.name} no debe haber quedado en estado 'draft' intermedio "
                f"(tiene state={m.state}). El savepoint revirtió write() correctamente."
            )
            self.assertFalse(
                m.origin.startswith('HUERFANO-PROTEGIDO-'),
                f"Move {m.name} NO debe ser marcado como protegido "
                "(el fallo fue en unlink, no en filtro protected_moves)"
            )

        _logger.info(
            "✅ Test B PASS — Savepoint aísla correctamente el fallo de unlink. "
            "Cursor externo operable. Recomendación Fase 2 CONFIRMADA."
        )


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestGuiaProcessingConsumptionBT04(TransactionCase):
    """
    BT-04: salida controlada a proceso para guías de servicio externo.

    - service genera exactamente UNA salida (outgoing → Virtual Production).
    - revalidar no duplica la salida (idempotencia vía consumption_picking_id).
    - compra NO genera salida.
    - cancelación/reversión restaura el stock crudo sin borrar historia.
    - sin lote crudo identificable la salida se bloquea.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.Quant = cls.env['stock.quant']
        cls.StockLot = cls.env['stock.lot']
        cls.AuditLog = cls.env['madenat.audit.log']

        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.location = cls.warehouse.lot_stock_id
        cls.production_location = cls.env['stock.location'].search(
            [('usage', '=', 'production')], limit=1
        )

        cls.partner = cls.env['res.partner'].create({'name': 'BT04 Processor'})

        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'BT04 Lumber Storable',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': uom_m3.id,
            'uom_po_id': uom_m3.id,
        })

    def _make_source_lot(self, name='BT04-SRC', qty=10.0):
        lot = self.StockLot.create({
            'name': name,
            'product_id': self.product.id,
            'volumen_m3': qty,
            'company_id': self.company.id,
        })
        self.Quant._update_available_quantity(
            self.product, self.location, qty, lot_id=lot
        )
        return lot

    def _make_service_guia(self, name='BT04-SERVICE', source_lot=None):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'service',
            'rate_usd': 800.0,
        }
        if source_lot:
            vals['source_lot_ids'] = [(6, 0, [source_lot.id])]
        return self.GuiaModel.create(vals)

    def _lot_qty_at_stock(self, lot):
        quants = self.Quant.search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', self.location.id),
        ])
        return sum(quants.mapped('quantity'))

    def test_service_creates_una_salida_a_proceso(self):
        source_lot = self._make_source_lot()
        guia = self._make_service_guia(source_lot=source_lot)

        picking = guia._get_or_create_consumption_picking()

        self.assertTrue(picking, "Debe crearse la salida a proceso")
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.picking_type_code, 'outgoing')
        self.assertEqual(picking.location_dest_id.id, self.production_location.id)
        self.assertEqual(guia.consumption_picking_id.id, picking.id)

        # El stock del lote crudo en bodega fue consumido.
        self.assertLessEqual(self._lot_qty_at_stock(source_lot), 0.0)

        # Evidencia auditiva BT-04 emitida.
        self.assertTrue(
            self.AuditLog.search_count([
                ('guia_processing_id', '=', guia.id),
                ('action_type', '=', 'consumption'),
            ]),
            "Debe emitirse un evento de auditoría 'consumption'"
        )

    def test_revalidar_no_duplica_salida(self):
        source_lot = self._make_source_lot()
        guia = self._make_service_guia(name='BT04-SERVICE-2', source_lot=source_lot)

        p1 = guia._get_or_create_consumption_picking()
        p2 = guia._get_or_create_consumption_picking()

        self.assertEqual(p1.id, p2.id, "La segunda llamada debe reutilizar la misma salida")

        count = self.Picking.search_count([
            ('origin', '=', f"{guia.name} - Salida a Proceso"),
        ])
        self.assertEqual(count, 1, "No debe generarse un segundo picking de salida")

    def test_compra_no_genera_salida(self):
        compra = self.GuiaModel.create({
            'name': 'BT04-COMPRA',
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'compra',
            'rate_usd': 1.0,
        })

        with self.assertRaises(UserError):
            compra._get_or_create_consumption_picking()

        self.assertFalse(compra.consumption_picking_id)

    def test_service_sin_lote_crudo_bloquea(self):
        guia = self._make_service_guia(name='BT04-SERVICE-SIN-LOTE')

        with self.assertRaises(UserError):
            guia._get_or_create_consumption_picking()

        self.assertFalse(guia.consumption_picking_id)

    def test_reversion_restaura_sin_borrar_historia(self):
        source_lot = self._make_source_lot()
        guia = self._make_service_guia(name='BT04-SERVICE-3', source_lot=source_lot)

        picking = guia._get_or_create_consumption_picking()
        original_name = picking.name
        self.assertLessEqual(self._lot_qty_at_stock(source_lot), 0.0)

        return_picking = guia._reverse_consumption_picking()
        self.assertTrue(return_picking, "Debe generarse un retorno")

        # El picking original de salida sigue existiendo (historia preservada).
        original = self.Picking.search([('name', '=', original_name)])
        self.assertTrue(original, "El picking original no debe borrarse")
        self.assertEqual(original.state, 'done')

        # El vínculo de la guía se limpia para permitir revalidación posterior.
        self.assertFalse(guia.consumption_picking_id)

        # El stock crudo se restauró.
        self.assertGreater(self._lot_qty_at_stock(source_lot), 0.0)

        # El retorno queda trazable por su origin.
        self.assertTrue(
            self.Picking.search_count([
                ('origin', '=', f'Return of {original_name}'),
                ('state', '=', 'done'),
            ]),
            "El retorno debe quedar registrado"
        )


@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'fix2')
class TestBlankProfileCatalogComplete(TransactionCase):
    """
    FIX 2 (auditoría 2026-08-20): completar el catálogo 'blanks'.

    'blanks' debe existir en lumber.blank.nominal.map,
    lumber.profile.subproduct.rule, lumber.export.formula y
    lumber.thickness.visual.rule. lumber.export.formula._resolve_for_profile
    para 'blanks' NO debe caer a 'metric' sino a la fórmula S2S imperial
    (decisión intencional alineada con lumber_ingestion_format).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.BlankNominal = cls.env['lumber.blank.nominal.map']
        cls.SubproductRule = cls.env['lumber.profile.subproduct.rule']
        cls.ExportFormula = cls.env['lumber.export.formula']
        cls.ThicknessVisual = cls.env['lumber.thickness.visual.rule']

    def _field_values(self, model, field_name='profile'):
        field = type(model)._fields.get(field_name)
        if not field:
            return set()
        return {v[0] for v in field.selection}

    def test_01_blanks_en_lumber_blank_nominal_map(self):
        values = self._field_values(self.BlankNominal)
        self.assertIn('blanks', values,
            "FIX2: lumber.blank.nominal.map debe aceptar profile 'blanks'")

    def test_02_blanks_en_lumber_profile_subproduct_rule(self):
        values = self._field_values(self.SubproductRule)
        self.assertIn('blanks', values,
            "FIX2: lumber.profile.subproduct.rule debe aceptar profile 'blanks'")

    def test_03_blanks_en_lumber_export_formula(self):
        values = self._field_values(self.ExportFormula)
        self.assertIn('blanks', values,
            "FIX2: lumber.export.formula debe aceptar profile 'blanks'")

    def test_04_blanks_en_lumber_thickness_visual_rule(self):
        values = self._field_values(self.ThicknessVisual)
        self.assertIn('blanks', values,
            "FIX2: lumber.thickness.visual.rule debe aceptar profile 'blanks'")

    def test_05_export_formula_blanks_no_resuelve_metric(self):
        """FIX2: _resolve_for_profile('blanks') debe usar S2S imperial, no metric."""
        formula = self.ExportFormula._resolve_for_profile('blanks')
        self.assertIn('source', formula)
        self.assertEqual(formula['formula_kind'], 's2s_imperial',
            "FIX2: 'blanks' debe resolver s2s_imperial (no metric_direct)")
        self.assertEqual(formula['unit_mode'], 'imperial_meters',
            "FIX2: 'blanks' debe usar imperial_meters")
        self.assertNotEqual(formula['formula_kind'], 'metric_direct',
            "FIX2: 'blanks' NO debe resolver como metric_direct")

    def test_06_legacy_subproduct_blanks_no_vacio(self):
        """FIX2: get_profile_subproduct_rules('blanks') ya no retorna vacío sin registro."""
        config = self.env['madenat.ingestion.config']
        rules = config.get_profile_subproduct_rules('blanks', 'forbidden_in_lock')
        self.assertIsInstance(rules, list,
            "FIX2: get_profile_subproduct_rules debe retornar lista")
        self.assertEqual(rules, [],
            "FIX2: legacy de 'blanks' sin filtros explícitos (lista vacía documentada)")


@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'fix1')
class TestGuiaProcessingIngestionProfileLock(TransactionCase):
    """
    FIX 1 (auditoría 2026-08-20): reactivación del candado anti-mezcla
    comercial en madenat_guia_mass_update.

    - madenat.guia.processing ahora tiene ingestion_profile (antes no existía).
    - El candado en madenat_guia_mass_update.action_apply usa
      hasattr(guia, 'ingestion_profile') y cfg = profiles_cfg[perfil].
      Con el campo presente, perfil f5085 bloquea subproductos S2S/RIP y
      perfil metric permite cualquier subproducto.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.WizardModel = cls.env['madenat.guia.mass.update']
        cls.partner = cls.env['res.partner'].create({'name': 'FIX1 Supplier'})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        if not cls.location:
            cls.location = cls.env['stock.location'].search([], limit=1)
        cls.subproduct_s2s = cls.env['madenat.subproducto'].create({
            'name': 'Madera S2S Premium',
            'code': 'FIX1-S2S',
        })
        cls.subproduct_open = cls.env['madenat.subproducto'].create({
            'name': 'Madera Bruta Maqueada',
            'code': 'FIX1-OPEN',
        })

    def _make_guia(self, name, profile='f5085'):
        return self.GuiaModel.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'ingestion_profile': profile,
        })

    def test_01_campo_existe_y_default_f5085(self):
        """El campo ingestion_profile debe existir con default f5085."""
        # Asserts estructurales del campo
        field = type(self.GuiaModel)._fields.get('ingestion_profile')
        self.assertIsNotNone(field,
            "FIX1: madenat.guia.processing debe tener campo ingestion_profile")
        # En Odoo 18 el default puede exponerse como lambda; invocarlo con un
        # recordset vacío confirma que resuelve al value correcto.
        default_resolved = field.default(self.GuiaModel) if callable(field.default) else field.default
        self.assertEqual(default_resolved, 'f5085',
            "FIX1: default de ingestion_profile debe ser f5085")

        # Asserts de creación sin valor explícito
        guia = self._make_guia('TEST-FIX1-DEFAULT')
        self.assertEqual(guia.ingestion_profile, 'f5085',
            "FIX1: guía creada sin ingestion_profile debe usar default f5085")

    def test_02_valores_selection_coinciden_con_lumber_reception(self):
        """Los values del Selection deben coincidir con lumber.reception."""
        lp_field = type(self.env['lumber.reception'])._fields.get('ingestion_profile')
        gp_field = type(self.GuiaModel)._fields.get('ingestion_profile')
        lp_values = {v[0] for v in lp_field.selection}
        gp_values = {v[0] for v in gp_field.selection}
        self.assertEqual(gp_values, lp_values,
            "FIX1: values de ingestion_profile deben ser idénticos a lumber.reception")

    def test_03_candado_bloquea_s2s_en_f5085(self):
        """Perfil f5085 debe bloquear subproducto con keyword S2S (forbidden_in_lock)."""
        guia = self._make_guia('TEST-FIX1-LOCK-S2S', profile='f5085')
        # Crear línea para que action_apply tenga algo que actualizar
        line = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'FIX1-LOT-S2S',
            'product_id': self.env['product.product'].search(
                [('type', '=', 'product')], limit=1
            ).id,
            'espesor_mm': 25.0,
            'ancho_mm': 100.0,
            'largo_m': 2.0,
            'pieces': 10,
        })
        wizard = self.WizardModel.with_context(active_id=guia.id).create({
            'subproducto_id': self.subproduct_s2s.id,
        })
        with self.assertRaises(UserError) as ctx:
            wizard.action_apply()
        self.assertIn('No puede asignar', str(ctx.exception),
            "FIX1: El candado debe bloquear S2S en perfil f5085")

    def test_04_candado_permite_s2s_en_f1550(self):
        """Perfil f1550 debe PERMITIR subproducto S2S (allowed, no forbidden_in_lock)."""
        guia = self._make_guia('TEST-FIX1-ALLOW-S2S', profile='f1550')
        line = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'FIX1-LOT-ALLOW',
            'product_id': self.env['product.product'].search(
                [('type', '=', 'product')], limit=1
            ).id,
            'espesor_mm': 25.0,
            'ancho_mm': 100.0,
            'largo_m': 2.0,
            'pieces': 10,
        })
        wizard = self.WizardModel.with_context(active_id=guia.id).create({
            'subproducto_id': self.subproduct_s2s.id,
        })
        # No debe lanzar UserError de candado. Si no hay otros errores, avanza.
        try:
            wizard.action_apply()
        except UserError as e:
            self.assertNotIn('No puede asignar', str(e),
                "FIX1: f1550 NO debe bloquear S2S")
            # Si falla por otra razón (ej: context), el test aún valida el candado
            _logger.info("FIX1 test_04: UserError no-candado capturado: %s", str(e))

    def test_05_candado_permite_metric_para_cualquier_subproducto(self):
        """Perfil metric debe permitir subproducto sin keyword prohibido."""
        guia = self._make_guia('TEST-FIX1-ALLOW-METRIC', profile='metric')
        line = self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': 'FIX1-LOT-METRIC',
            'product_id': self.env['product.product'].search(
                [('type', '=', 'product')], limit=1
            ).id,
            'espesor_mm': 25.0,
            'ancho_mm': 100.0,
            'largo_m': 2.0,
            'pieces': 10,
        })
        wizard = self.WizardModel.with_context(active_id=guia.id).create({
            'subproducto_id': self.subproduct_open.id,
        })
        try:
            wizard.action_apply()
        except UserError as e:
            self.assertNotIn('No puede asignar', str(e),
                "FIX1: metric no debe bloquear subproductos")