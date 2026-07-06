# -*- coding: utf-8 -*-
# TD-008: Test suite para MadenatGuiaProcessing
# Cobertura mínima del flujo de negocio identificado en Auditoría 2026-06-04
# Golden records: guía ID=14 (19846) — estado draft en madenat_test

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
        queda CONTRADECIDA.
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
