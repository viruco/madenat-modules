# -*- coding: utf-8 -*-
"""🔐 Seguridad de Recepción (`lumber.reception`) — Fase C.1, 2026-10-04.

Solo Operaciones/Jefatura/Gerencia pueden crear, procesar, confirmar, reabrir,
resetear o cancelar recepciones. Cobertura T-REC-SEC-1..7.
``TransactionCase``: todo se revierte.
"""
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'intake_security')
class TestReceptionSecurity(TransactionCase):
    """T-REC-SEC-1..7 — guard server-side de `lumber.reception`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reception = cls.env['lumber.reception']
        cls.ReceptionLine = cls.env['lumber.reception.line']
        cls.ResetWizard = cls.env['lumber.reception.reset.wizard']
        cls.MassWizard = cls.env['lumber.reception.mass.update']
        cls.Picking = cls.env['stock.picking']
        cls.Move = cls.env['stock.move']
        cls.MoveLine = cls.env['stock.move.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Quant = cls.env['stock.quant']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.partner = cls.env['res.partner'].create(
            {'name': 'SEC REC Proveedor', 'is_company': True})
        cls.u_ops = new_test_user(
            cls.env, login='sec_rec_ops',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_operaciones')
        cls.u_common = new_test_user(
            cls.env, login='sec_rec_common', groups='base.group_user')

    # ── Helpers ───────────────────────────────────────────────────────────
    def _rec_vals(self, name):
        return {
            'name': name, 'supplier_id': self.partner.id,
            'ingestion_profile': 'metric',
        }

    def _phys(self):
        """Huella física/documental: nada debe cambiar si el guard bloquea."""
        return (
            self.Reception.search_count([]),
            self.ReceptionLine.search_count([]),
            self.Picking.search_count([]),
            self.Move.search_count([]),
            self.MoveLine.search_count([]),
            self.StockLot.search_count([]),
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

    # ── T-REC-SEC-1 — Operaciones crea y procesa ──────────────────────────
    def test_t_rec_sec_1_operaciones_crea_y_procesa(self):
        rec = self.Reception.with_user(self.u_ops).create(
            self._rec_vals('SEC-R1'))
        rec.with_user(self.u_ops).write({'state': 'verified'})
        self.assertTrue(rec.exists())
        self.assertEqual(rec.state, 'verified')

    # ── T-REC-SEC-2 — Interno común no crea/edita/confirma ────────────────
    def test_t_rec_sec_2_common_no_opera(self):
        with self.assertRaises(AccessError):
            self.Reception.with_user(self.u_common).create(
                self._rec_vals('SEC-R2'))
        rec = self.Reception.create(self._rec_vals('SEC-R2b'))
        with self.assertRaises(AccessError):
            rec.with_user(self.u_common).write({'state': 'verified'})
        with self.assertRaises(AccessError):
            rec.with_user(self.u_common).action_confirm_reception()

    # ── T-REC-SEC-3 — Interno común no usa mass update ni reset wizard ────
    def test_t_rec_sec_3_common_no_usa_wizards(self):
        rec = self.Reception.create(self._rec_vals('SEC-R3'))
        # Reset wizard: creación denegada por ACL para el usuario base.
        with self.assertRaises(AccessError):
            self.ResetWizard.with_user(self.u_common).create(
                {'reception_id': rec.id})
        # Aun creado por el sistema, action_confirm exige rol operativo.
        wiz = self.ResetWizard.create({'reception_id': rec.id})
        with self.assertRaises(AccessError):
            wiz.with_user(self.u_common).action_confirm()
        # Mass update: action_apply exige rol operativo.
        mass = self.MassWizard.create({'reception_id': rec.id})
        with self.assertRaises(AccessError):
            mass.with_user(self.u_common).action_apply()

    # ── T-REC-SEC-4 — Interno común no cancela ni resetea/reabre ──────────
    def test_t_rec_sec_4_common_no_cancela_ni_resetea(self):
        rec = self.Reception.create(self._rec_vals('SEC-R4'))
        before_state = rec.state
        before = self._phys()
        with self.assertRaises(AccessError):
            rec.with_user(self.u_common).action_cancel()
        with self.assertRaises(AccessError):
            rec.with_user(self.u_common).action_reset_to_draft()
        rec.invalidate_recordset()
        self.assertEqual(rec.state, before_state)
        self.assertEqual(self._phys(), before)

    # ── T-REC-SEC-5 — Importación real (load) no crea ─────────────────────
    def test_t_rec_sec_5_importacion_real_no_crea(self):
        fields = ['name', 'supplier_id', 'ingestion_profile']
        rows = [['SEC-R5-IMP', str(self.partner.id), 'metric']]
        self._import_denied(self.Reception, self.u_common, fields, rows,
                            'lumber.reception')

    # ── T-REC-SEC-6 — Operaciones conserva el flujo completo ──────────────
    def test_t_rec_sec_6_operaciones_flujo_completo(self):
        rec = self.Reception.with_user(self.u_ops).create(
            self._rec_vals('SEC-R6'))
        rec.with_user(self.u_ops).write({'state': 'verified'})
        rec.with_user(self.u_ops).action_cancel()
        rec.invalidate_recordset()
        self.assertEqual(rec.state, 'cancel')

    # ── T-REC-SEC-7 — ACL legacy/huérfana no elude el guard ───────────────
    def test_t_rec_sec_7_acl_legacy_no_elude(self):
        model_id = self.env['ir.model']._get_id('lumber.reception')
        legacy = self.env['res.groups'].create({
            'name': 'SEC Legacy Reception',
            'implied_ids': [(4, self.env.ref('base.group_user').id)],
        })
        self.env['ir.model.access'].create({
            'name': 'SEC legacy reception access', 'model_id': model_id,
            'group_id': legacy.id, 'perm_read': 1, 'perm_write': 1,
            'perm_create': 1, 'perm_unlink': 0,
        })
        u_legacy = new_test_user(
            self.env, login='sec_rec_legacy', groups='base.group_user')
        u_legacy.groups_id = [(4, legacy.id)]
        with self.assertRaises(AccessError):
            self.Reception.with_user(u_legacy).create(self._rec_vals('SEC-R7'))
        rec = self.Reception.create(self._rec_vals('SEC-R7b'))
        with self.assertRaises(AccessError):
            rec.with_user(u_legacy).write({'state': 'verified'})
        with self.assertRaises(AccessError):
            rec.with_user(u_legacy).action_cancel()
