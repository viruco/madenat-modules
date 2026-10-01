# -*- coding: utf-8 -*-
"""Programa SV — endurecimiento anti-bypass de escrituras protegidas.

Demuestra que ninguna escritura directa (ni con contexto booleano forjado, ni
con id de operación adivinado, ni con capacidad interna reutilizada) puede
modificar los campos protegidos de una etiqueta SV: solo la aplicación atómica
de una operación SV, con capacidad interna de un solo uso, puede hacerlo.
"""

from unittest import mock

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon

CAPABILITY_MODEL = 'madenat.sv.internal.capability'
MARKER_MODEL = 'madenat.sv.internal.marker'
SELLO_TEST = '2026-09-26 00:00:00'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'sv')
class TestSvRpcBypass(SvTestCommon, TransactionCase):
    """Bypass RPC/ORM bloqueado por capacidad interna de un solo uso."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()
        cls.Capability = cls.env[CAPABILITY_MODEL]
        cls.Marker = cls.env[MARKER_MODEL]

    # ── Utilidades ────────────────────────────────────────────────────────
    def _make_rename_op(self, lot, label, reason='Cambio controlado'):
        return self.Operation.create({
            'lot_id': lot.id,
            'action_type': 'rename',
            'new_label': label,
            'reason': reason,
        })

    def _mint(self, operation, values):
        return self.Capability.sudo()._sv_mint(
            operation, self.env.uid,
            {'action_type': operation.action_type, 'values': values})

    def _capability_count(self):
        return self.Capability.sudo().search_count([])

    # ── 1. Escritura directa bloqueada ────────────────────────────────────
    def test_01_escritura_directa_bloqueada(self):
        guia = self._sv_make_guia('SV-BYP-01')
        lot = self._sv_make_lot(guia, label='SV00000000401')
        for vals in (
                {'name': 'SV00000000999'},
                {'volumen_m3': 1.0},
                {'volume_purchase_m3': 1.0},
                {'vol_shipment_m3': 1.0},
                {'piezas': 99}):
            with self.assertRaises(ValidationError):
                lot.write(vals)
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000401')
        self.assertAlmostEqual(lot.volumen_m3, 40.300, places=3)

    # ── 2. Contexto booleano forjado bloqueado ───────────────────────────
    def test_02_contexto_booleano_forjado_bloqueado(self):
        guia = self._sv_make_guia('SV-BYP-02')
        lot = self._sv_make_lot(guia, label='SV00000000402')
        with self.assertRaises(ValidationError):
            lot.with_context(madenat_sv_rename=True).write({
                'name': 'SV00000000998'})

    # ── 3. Id de operación adivinado/forjado bloqueado ───────────────────
    def test_03_operation_id_forjado_bloqueado(self):
        guia = self._sv_make_guia('SV-BYP-03')
        lot = self._sv_make_lot(guia, label='SV00000000403')
        operation = self._make_rename_op(lot, 'SV00000000404')
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_rename=True,
                madenat_sv_operation_id=operation.id,
            ).write({'name': 'SV00000000404'})
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability='0' * 32,
                madenat_sv_capability_txn='1' * 32,
            ).write({'name': 'SV00000000404'})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000403')

    # ── 4. Operación correcta con etiqueta distinta bloqueada ────────────
    def test_04_operacion_correcta_etiqueta_distinta_bloqueada(self):
        guia = self._sv_make_guia('SV-BYP-04')
        lot = self._sv_make_lot(guia, label='SV00000000405')
        operation = self._make_rename_op(lot, 'SV00000000406')
        capability = self._mint(operation, {
            'name': 'SV00000000406',
            'sv_balance_stamp': SELLO_TEST,
        })
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=capability.token,
                madenat_sv_capability_txn=capability.transaction_token,
            ).write({'name': 'SV00000000407', 'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000405')

    # ── 5. Capacidad consumida / replay bloqueado ────────────────────────
    def test_05_capacidad_consumida_y_replay_bloqueado(self):
        guia = self._sv_make_guia('SV-BYP-05')
        lot = self._sv_make_lot(guia, label='SV00000000408')
        operation = self._make_rename_op(lot, 'SV00000000409')
        capability = self._mint(operation, {
            'name': 'SV00000000409',
            'sv_balance_stamp': SELLO_TEST,
        })
        token = capability.token
        transaction_token = capability.transaction_token
        lot.with_context(
            madenat_sv_capability=token,
            madenat_sv_capability_txn=transaction_token,
        ).write({'name': 'SV00000000409', 'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000409')

        # Replay del mismo permiso interno: consumo único ⇒ bloqueado.
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=token,
                madenat_sv_capability_txn=transaction_token,
            ).write({'name': 'SV00000000410', 'sv_balance_stamp': SELLO_TEST})
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=token,
                madenat_sv_capability_txn=transaction_token,
            ).write({'name': 'SV00000000409', 'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000409')

    # ── 6. El asistente controlado renombra una sola vez ─────────────────
    def test_06_asistente_renombra_una_sola_vez_sin_dejar_capacidad(self):
        guia = self._sv_make_guia('SV-BYP-06')
        lot = self._sv_make_lot(guia, label='SV00000000411')
        captured = []
        original_consume = type(self.Capability)._sv_consume

        def recording_consume(model_self, token, transaction_token, lot_arg,
                              actor_uid):
            captured.append((token, transaction_token))
            return original_consume(
                model_self, token, transaction_token, lot_arg, actor_uid)

        with mock.patch.object(
                type(self.Capability), '_sv_consume', recording_consume):
            self.env['madenat.sv.rename.wizard'].create({
                'lot_id': lot.id,
                'new_label': 'SV00000000412',
                'reason': 'Corrección de digitación',
            }).action_submit()

        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000412')
        self.assertEqual(self._capability_count(), 0)
        operation = self.Operation.search([('lot_id', '=', lot.id)])
        self.assertEqual(len(operation), 1)
        self.assertEqual(operation.state, 'applied')
        # El token interno no sale al snapshot, chatter ni auditoría.
        token = captured[0][0]
        self.assertNotIn(token, operation.snapshot_json or '')
        chatter = ' '.join(lot.message_ids.mapped('body') or [])
        self.assertNotIn(token, chatter)
        audit = self.env['madenat.audit.log'].sudo().search([
            ('guia_processing_id', '=', guia.id)])
        self.assertNotIn(token, ' '.join(audit.mapped('description') or []))
        # Replay de la capacidad real consumida: bloqueado.
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=token,
                madenat_sv_capability_txn=captured[0][1],
            ).write({'name': 'SV00000000413'})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000412')

    # ── 7. Infraestructura interna no expuesta ───────────────────────────
    def test_07_infraestructura_interna_no_expuesta(self):
        models = (CAPABILITY_MODEL, MARKER_MODEL)
        self.assertFalse(self.env['ir.model.access'].sudo().search_count([
            ('model_id.model', 'in', models)]))
        self.assertFalse(self.env['ir.ui.view'].sudo().search_count([
            ('model', 'in', models)]))
        self.assertFalse(self.env['ir.actions.act_window'].sudo().search_count([
            ('res_model', 'in', models)]))
        self.assertFalse(self.env['ir.actions.server'].sudo().search_count([
            ('model_id.model', 'in', models)]))
        self.assertFalse(self.env['ir.model.fields'].sudo().search_count([
            ('model', 'in', models), ('related', '!=', False)]))
        # Un usuario funcional no puede leer ni crear capacidades/marcadores.
        group_oper = self.env.ref(
            'madenat_lumber_core.group_madenat_operaciones')
        user_oper = self.env['res.users'].create({
            'name': 'sv_bypass_oper', 'login': 'sv_bypass_oper',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id, group_oper.id])],
        })
        for model_name in models:
            with self.assertRaises(AccessError):
                self.env[model_name].with_user(user_oper).search([])
        # Sin método público de acuñado/consumo.
        self.assertFalse(hasattr(self.Capability, 'sv_mint'))
        self.assertFalse(hasattr(self.Capability, 'sv_consume'))

    # ── 8. Fallo posterior al acuñado: rollback y no reutilizable ────────
    def test_08_fallo_tras_acunar_revierte_todo_y_no_reutiliza(self):
        guia = self._sv_make_guia('SV-BYP-08')
        lot = self._sv_make_lot(guia, label='SV00000000420')
        capabilities_before = self._capability_count()
        chatter_before = len(lot.message_ids)
        op_count_before = self.Operation.search_count([])
        captured = []
        original_consume = type(self.Capability)._sv_consume

        def recording_consume(model_self, token, transaction_token, lot_arg,
                             actor_uid):
            captured.append((token, transaction_token))
            return original_consume(
                model_self, token, transaction_token, lot_arg, actor_uid)

        # La falla ocurre DESPUÉS del acuñado y del write protegido (paso h).
        with mock.patch.object(
                type(self.Capability), '_sv_consume', recording_consume), \
                mock.patch.object(
                    type(self.Operation), '_sv_finalize_apply',
                    side_effect=ValidationError('fallo forzado post-acuñado')):
            with self.assertRaises(ValidationError):
                with self.env.cr.savepoint():
                    operation = self.Operation.create({
                        'lot_id': lot.id,
                        'action_type': 'rename',
                        'new_label': 'SV00000000421',
                        'reason': 'Fallo posterior al acuñado',
                    })
                    operation.action_apply()

        lot.invalidate_recordset()
        # Rollback total: etiqueta, ledger, alias, chatter y capacidad.
        self.assertEqual(lot.name, 'SV00000000420')
        self.assertEqual(self.Operation.search_count([]), op_count_before)
        self.assertEqual(self._capability_count(), capabilities_before)
        self.assertEqual(len(lot.message_ids), chatter_before)
        self.assertEqual(lot.sv_operation_count, 0)
        # La capacidad acuñada (consumida y revertida) no puede reutilizarse.
        self.assertTrue(captured)
        token, transaction_token = captured[0]
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=token,
                madenat_sv_capability_txn=transaction_token,
            ).write({'name': 'SV00000000421'})
        lot.invalidate_recordset()
        self.assertEqual(lot.name, 'SV00000000420')
        self.assertEqual(self._capability_count(), capabilities_before)

    # ── 9. Sello técnico protegido: escritura directa bloqueada ──────────
    def test_09_sello_escritura_directa_bloqueada(self):
        guia = self._sv_make_guia('SV-BYP-09')
        lot = self._sv_make_lot(guia, label='SV00000000431')
        self.assertFalse(lot.sv_balance_stamp)
        with self.assertRaises(ValidationError):
            lot.write({'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        self.assertFalse(lot.sv_balance_stamp)
        # La escritura directa junto a otro campo protegido también se bloquea.
        with self.assertRaises(ValidationError):
            lot.write({
                'name': 'SV00000000432',
                'sv_balance_stamp': SELLO_TEST,
            })

    # ── 10. Sello: contexto forjado bloqueado ────────────────────────────
    def test_10_sello_contexto_forjado_bloqueado(self):
        guia = self._sv_make_guia('SV-BYP-10')
        lot = self._sv_make_lot(guia, label='SV00000000433')
        operation = self._make_rename_op(lot, 'SV00000000434')
        for context in (
                {'madenat_sv_rename': True},
                {'madenat_sv_rename': True,
                 'madenat_sv_operation_id': operation.id},
                {'madenat_sv_capability': '0' * 32,
                 'madenat_sv_capability_txn': '1' * 32}):
            with self.assertRaises(ValidationError):
                lot.with_context(**context).write({
                    'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        self.assertFalse(lot.sv_balance_stamp)

    # ── 11. Sello: flujo controlado de rebaja y reversa ──────────────────
    def test_11_sello_actualizado_por_rebaja_y_reversa(self):
        guia = self._sv_make_guia('SV-BYP-11')
        lot = self._sv_make_lot(guia, label='SV00000000435')
        rebaja = self._sv_rebaja(lot, 5.0)
        lot.invalidate_recordset()
        stamp_rebaja = lot.sv_balance_stamp
        self.assertTrue(stamp_rebaja)

        reverse = self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Reversa para validar sello',
        })
        reverse.action_submit()
        lot.invalidate_recordset()
        self.assertTrue(lot.sv_balance_stamp)
        self.assertNotEqual(lot.sv_balance_stamp, False)

    # ── 12. Sello: flujo controlado de regularización ────────────────────
    def test_12_sello_actualizado_por_regularizacion(self):
        guia = self._sv_make_guia('SV-BYP-12')
        lot = self._sv_make_lot(guia, label='SV00000000436')
        self._sv_regularize(lot, 41.0)
        lot.invalidate_recordset()
        self.assertTrue(lot.sv_balance_stamp)

    # ── 13. Sello: capacidad consumida/stale no lo actualiza ─────────────
    def test_13_sello_no_actualizado_con_capacidad_stale(self):
        guia = self._sv_make_guia('SV-BYP-13')
        lot = self._sv_make_lot(guia, label='SV00000000437')
        operation = self._make_rename_op(lot, 'SV00000000438')
        capability = self._mint(operation, {
            'name': 'SV00000000438',
            'sv_balance_stamp': SELLO_TEST,
        })
        token = capability.token
        transaction_token = capability.transaction_token
        lot.with_context(
            madenat_sv_capability=token,
            madenat_sv_capability_txn=transaction_token,
        ).write({'name': 'SV00000000438', 'sv_balance_stamp': SELLO_TEST})
        lot.invalidate_recordset()
        stamp_after_first = lot.sv_balance_stamp
        self.assertTrue(stamp_after_first)

        # Replay: la capacidad ya fue consumida ⇒ el sello no se actualiza.
        with self.assertRaises(ValidationError):
            lot.with_context(
                madenat_sv_capability=token,
                madenat_sv_capability_txn=transaction_token,
            ).write({'sv_balance_stamp': '2026-09-26 23:59:59'})
        lot.invalidate_recordset()
        self.assertEqual(lot.sv_balance_stamp, stamp_after_first)

    # ── 14. Sello: no visible en vistas ni accesible por API funcional ───
    def test_14_sello_no_visible_ni_accesible(self):
        guia = self._sv_make_guia('SV-BYP-14')
        lot = self._sv_make_lot(guia, label='SV00000000439')
        # Sin vistas/wizard/menú que lo expongan.
        self.assertFalse(self.env['ir.ui.view'].sudo().search_count([
            ('arch_db', 'ilike', 'sv_balance_stamp')]))
        # Ausente del chatter y de la auditoría tras una operación real.
        self._sv_rebaja(lot, 1.0)
        lot.invalidate_recordset()
        self.assertNotIn(
            'sv_balance_stamp',
            ' '.join(lot.message_ids.mapped('body') or []))
        audit = self.env['madenat.audit.log'].sudo().search([
            ('batch_id', '=', lot.name)])
        self.assertNotIn(
            'sv_balance_stamp',
            ' '.join(audit.mapped('description') or []))
        # No accesible por API funcional para un usuario de negocio.
        group_oper = self.env.ref(
            'madenat_lumber_core.group_madenat_operaciones')
        user_oper = self.env['res.users'].create({
            'name': 'sv_bypass_oper_sello', 'login': 'sv_bypass_oper_sello',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id, group_oper.id])],
        })
        with self.assertRaises(AccessError):
            lot.with_user(user_oper).read(['sv_balance_stamp'])
        fields_get = lot.with_user(user_oper).fields_get(['sv_balance_stamp'])
        self.assertNotIn('sv_balance_stamp', fields_get)
        # Escritura por API funcional: bloqueada (por grupo y por la guarda).
        stamp_before = lot.sv_balance_stamp
        try:
            lot.with_user(user_oper).write({'sv_balance_stamp': SELLO_TEST})
            self.fail('La escritura del sello por API funcional debe bloquearse')
        except (AccessError, ValidationError):
            pass
        lot.invalidate_recordset()
        self.assertEqual(lot.sv_balance_stamp, stamp_before)
