# -*- coding: utf-8 -*-
"""🔐 Seguridad de Ingreso/Recepción/Guías (Fase C.1, 2026-10-04).

Cierra la puerta lateral RPC/ORM descubierta en UAT-INT-4: la guía de
procesamiento NO debe poder ser creada, modificada, procesada, validada,
reabierta ni cancelada por usuarios internos sin rol MADENAT operativo
(Operaciones/Jefatura/Gerencia). Tampoco por Auditoría ni Contabilidad, ni por
un grupo legacy que herede una ACL accidental.

Cobertura: T-INT-SEC-1..10. ``TransactionCase``: todo se revierte.
"""
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'intake_security')
class TestGuiaProcessingSecurity(TransactionCase):
    """T-INT-SEC-1..10 — guard server-side de `madenat.guia.processing`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.Wizard = cls.env[
            'madenat.guia.processing.documental.correction.wizard']
        cls.ReopenWizard = cls.env['madenat.guia.processing.reopen.wizard']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.AuditLog = cls.env['madenat.audit.log']
        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.location = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1).lot_stock_id
        cls.partner = cls.env['res.partner'].create(
            {'name': 'SEC INT Proveedor', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'SEC INT Product', 'is_storable': True, 'tracking': 'lot',
            'uom_id': uom_m3.id, 'uom_po_id': uom_m3.id})
        cls.subproducto = cls.env['madenat.subproducto'].search([], limit=1) \
            or cls.env['madenat.subproducto'].create(
                {'name': 'SEC INT Sub', 'code': 'SECINT'})
        cls.u_ops = new_test_user(
            cls.env, login='sec_ops',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_operaciones,'
                   'stock.group_stock_manager')
        cls.u_common = new_test_user(
            cls.env, login='sec_common', groups='base.group_user')
        cls.u_audit = new_test_user(
            cls.env, login='sec_audit',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_auditoria')
        cls.u_contab = False
        if cls.env.ref('madenat_lumber_core.group_madenat_contabilidad',
                       raise_if_not_found=False):
            cls.u_contab = new_test_user(
                cls.env, login='sec_contab',
                groups='base.group_user,'
                       'madenat_lumber_core.group_madenat_contabilidad')

    # ── Helpers ───────────────────────────────────────────────────────────
    def _guia_vals(self, name):
        return {
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'compra', 'ingestion_profile': 'f5085',
            'rate_usd': 900.0, 'date_emission': '2026-10-04',
            'additional_cost': 0.0,
        }

    def _ops_guia(self, name, state='draft'):
        guia = self.Guia.with_user(self.u_ops).create(self._guia_vals(name))
        self.Line.with_user(self.u_ops).create({
            'processing_id': guia.id, 'lot_name': name + '-LOT',
            'sku_original': 'SEC', 'product_id': self.product.id,
            'subproducto_id': self.subproducto.id, 'pieces': 10,
            'espesor_mm': 100.0, 'ancho_mm': 1000.0, 'largo_m': 4.0,
            'espesor_nominal_mm': 100.0, 'ancho_nominal_mm': 1000.0,
            'largo_nominal_m': 4.0})
        if state != 'draft':
            guia.with_user(self.u_ops).write({'state': state})
        return guia

    def _phys(self):
        """Huella física/documental: nada debe cambiar si el guard bloquea."""
        return (
            self.Guia.search_count([]),
            self.Line.search_count([]),
            self.StockLot.search_count([]),
            self.Picking.search_count([]),
            self.Move.search_count([]),
            self.MoveLine.search_count([]),
            self.Quant.search_count([]),
            self.AuditLog.search_count([]),
        )

    def _import_denied(self, model, user, fields, rows, label):
        """Ejecuta una importación real y exige denegación + Δ0.

        Resultados válidos (contrato flexible, Odoo 18):
          a) lanza ``AccessError``;
          b) devuelve una estructura de resultado sin ids creados
             (``load()`` retorna ``{'ids': …, 'messages': …}``).
        No se asume tuple/list/dict: se inspecciona el tipo real.
        """
        before = self._phys()
        result = None
        raised = None
        try:
            result = model.with_user(user).load(fields, rows)
        except AccessError as exc:
            raised = exc
        except Exception as exc:  # noqa: BLE001 - error controlado esperado
            raised = exc
        if raised is None:
            self.assertIsInstance(
                result, dict,
                'load() devolvió un tipo inesperado: %s'
                % type(result).__name__)
            created = result.get('ids')
            self.assertFalse(
                created,
                'La importación (%s) no debe crear registros; ids=%s keys=%s'
                % (label, created, sorted(result)))
        # Sin efectos laterales en ningún caso (excepción o denegación).
        self.assertEqual(
            self._phys(), before,
            'Efectos laterales detectados en importación denegada (%s)'
            % label)

    # ── T-INT-SEC-1 — Operaciones crea y valida ───────────────────────────
    def test_t_int_sec_1_operaciones_crea_y_valida(self):
        guia = self._ops_guia('SEC-T1')
        guia.with_user(self.u_ops).write({'state': 'verified'})
        guia.with_user(self.u_ops).action_validate()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'validated')
        self.assertTrue(guia.lot_ids)

    # ── T-INT-SEC-2 — Interno común no puede crear ────────────────────────
    def test_t_int_sec_2_common_no_crea(self):
        with self.assertRaises(AccessError):
            self.Guia.with_user(self.u_common).create(
                self._guia_vals('SEC-T2'))

    # ── T-INT-SEC-3 — Interno común no escribe campos operativos ──────────
    def test_t_int_sec_3_common_no_escribe_operativo(self):
        guia = self.Guia.create(self._guia_vals('SEC-T3'))
        with self.assertRaises(AccessError):
            guia.with_user(self.u_common).write({'state': 'verified'})

    # ── T-INT-SEC-4 — Interno común no valida ni procesa ──────────────────
    def test_t_int_sec_4_common_no_valida_ni_procesa(self):
        guia = self._ops_guia('SEC-T4', state='verified')
        with self.assertRaises(AccessError):
            guia.with_user(self.u_common).action_validate()
        with self.assertRaises(AccessError):
            guia.with_user(self.u_common).action_process_from_staging()
        guia.invalidate_recordset()
        self.assertNotEqual(guia.state, 'validated')

    # ── T-INT-SEC-5 — Interno común no reabre ni cancela ──────────────────
    def test_t_int_sec_5_common_no_reabre_ni_cancela(self):
        guia = self._ops_guia('SEC-T5')
        before_state = guia.state
        before = self._phys()
        with self.assertRaises(AccessError):
            guia.with_user(self.u_common).action_reopen_to_draft()
        with self.assertRaises(AccessError):
            guia.with_user(self.u_common).action_force_cancel()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, before_state)
        self.assertEqual(self._phys(), before)

    # ── T-INT-SEC-5b — Auditoría no crea/modifica/valida ──────────────────
    def test_t_int_sec_5b_auditoria_no_modifica(self):
        guia = self._ops_guia('SEC-T5B', state='verified')
        with self.assertRaises(AccessError):
            guia.with_user(self.u_audit).write({'state': 'validated'})
        with self.assertRaises(AccessError):
            guia.with_user(self.u_audit).action_validate()
        with self.assertRaises(AccessError):
            self.Guia.with_user(self.u_audit).create(
                self._guia_vals('SEC-T5Bb'))

    # ── T-INT-SEC-5c — Contabilidad no opera ──────────────────────────────
    def test_t_int_sec_5c_contabilidad_no_opera(self):
        if not self.u_contab:
            self.skipTest('Sin grupo Contabilidad en este entorno.')
        guia = self._ops_guia('SEC-T5C', state='verified')
        with self.assertRaises(AccessError):
            self.Guia.with_user(self.u_contab).create(
                self._guia_vals('SEC-T5Cb'))
        with self.assertRaises(AccessError):
            guia.with_user(self.u_contab).action_validate()

    # ── T-INT-SEC-6 — Interno común no usa wizard de Guía ─────────────────
    def test_t_int_sec_6_common_no_usa_wizard(self):
        guia = self._ops_guia('SEC-T6', state='verified')
        # ACL: el usuario base no puede ni crear el wizard.
        with self.assertRaises(AccessError):
            self.Wizard.with_user(self.u_common).create({
                'guia_processing_id': guia.id, 'reason': 'SEC-T6'})
        with self.assertRaises(AccessError):
            self.ReopenWizard.with_user(self.u_common).create({
                'guia_processing_id': guia.id})
        # Aun creado por el sistema, action_confirm exige rol operativo.
        wiz = self.Wizard.create({
            'guia_processing_id': guia.id, 'reason': 'SEC-T6'})
        with self.assertRaises(AccessError):
            wiz.with_user(self.u_common).action_confirm()

    # ── T-INT-SEC-7 — Contexto falso no elude ─────────────────────────────
    def test_t_int_sec_7_contexto_no_elude(self):
        with self.assertRaises(AccessError):
            self.Guia.with_user(self.u_common).with_context(
                allow_intake=True, intake=True, force=True,
                allow_operational=True).create(self._guia_vals('SEC-T7'))

    # ── T-INT-SEC-8 — Importación real (load) no crea ─────────────────────
    def test_t_int_sec_8_importacion_real_no_crea(self):
        fields = ['name', 'partner_id', 'tipo_recepcion', 'ingestion_profile']
        rows = [['SEC-T8-IMP', str(self.partner.id), 'compra', 'f5085']]
        self._import_denied(self.Guia, self.u_common, fields, rows,
                            'madenat.guia.processing')

    # ── T-INT-SEC-9 — Operaciones conserva el flujo completo ──────────────
    def test_t_int_sec_9_operaciones_flujo_completo(self):
        guia = self._ops_guia('SEC-T9')
        guia.with_user(self.u_ops).write({'state': 'verified'})
        guia.with_user(self.u_ops).action_validate()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'validated')
        before = self._phys()
        # CDP-V1 (documental) por Operaciones: no altera lo físico.
        wiz = self.Wizard.with_user(self.u_ops).create({
            'guia_processing_id': guia.id,
            'reason': 'SEC-T9 corrección documental', 'notes': 'SEC-T9'})
        wiz.with_user(self.u_ops).action_confirm()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'validated')
        after = self._phys()
        # Físico (Guía/Línea/Lote/Picking/Move/MoveLine/Quant) inmutable.
        self.assertEqual(after[:7], before[:7],
                         'CDP-V1 no debe alterar registros físicos')
        # Auditoría: CDP-V1 SÍ registra un evento (append-only, nunca baja).
        self.assertGreaterEqual(after[7], before[7],
                                'La auditoría no debe disminuir tras CDP-V1')
        cdp_audit = self.AuditLog.search([
            ('guia_processing_id', '=', guia.id),
            ('description', 'like', 'CDP-V1'),
        ], limit=1)
        self.assertTrue(cdp_audit,
                        'CDP-V1 debe registrar el evento de auditoría esperado')

    # ── T-INT-SEC-10 — ACL legacy/huérfana no elude el guard ──────────────
    def test_t_int_sec_10_acl_legacy_no_elude(self):
        model_id = self.env['ir.model']._get_id('madenat.guia.processing')
        legacy = self.env['res.groups'].create({
            'name': 'SEC Legacy Guia',
            'implied_ids': [(4, self.env.ref('base.group_user').id)],
        })
        self.env['ir.model.access'].create({
            'name': 'SEC legacy guia access', 'model_id': model_id,
            'group_id': legacy.id, 'perm_read': 1, 'perm_write': 1,
            'perm_create': 1, 'perm_unlink': 0,
        })
        u_legacy = new_test_user(
            self.env, login='sec_g_legacy', groups='base.group_user')
        u_legacy.groups_id = [(4, legacy.id)]
        with self.assertRaises(AccessError):
            self.Guia.with_user(u_legacy).create(self._guia_vals('SEC-T10'))
        guia = self.Guia.create(self._guia_vals('SEC-T10b'))
        with self.assertRaises(AccessError):
            guia.with_user(u_legacy).write({'state': 'verified'})
        with self.assertRaises(AccessError):
            guia.with_user(u_legacy).action_force_cancel()
