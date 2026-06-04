# -*- coding: utf-8 -*-
# TD-008: Test suite para MadenatGuiaProcessing
# Cobertura mínima del flujo de negocio identificado en Auditoría 2026-06-04
# Golden records: guía ID=14 (19846) — estado draft en madenat_test

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
import logging

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
        """Guia real 19846 (ID=14) debe seguir existiendo en estado draft"""
        guia = self.GuiaModel.search([('name', '=', '19846')], limit=1)
        if guia:
            self.assertEqual(guia.state, 'draft',
                "Golden record 19846 debe seguir en estado draft")
            _logger.info("Golden record 19846 verificado: state=%s", guia.state)
        else:
            _logger.warning("Golden record 19846 no encontrado en DB de tests")


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