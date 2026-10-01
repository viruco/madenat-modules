# -*- coding: utf-8 -*-
"""RPC real (HttpCase + JSON-RPC) de la grilla declarada de Volúmenes.

`odoo.tests.common.Form` llama ``record.onchange(...)`` DIRECTAMENTE y no pasa
por el dispatcher ``odoo.api.call_kw``: por eso NO detectó la regresión del
override de ``onchange`` (``@api.model`` → ``_api='model'`` → el dispatcher no
extrae los ids y entrega la lista de ids como primer argumento posicional:

    TypeError: onchange() takes 4 positional arguments but 5 were given

Estas pruebas entran por la ruta REAL del navegador:
``/web/dataset/call_kw/<modelo>/<método>`` con sesión autenticada y la forma
exacta de argumentos que arma el cliente web de Odoo 18.
"""

from odoo.tests import HttpCase, JsonRpcException, tagged

from odoo.addons.madenat_lumber_intake.models.intake_constants import (
    DECLARED_GUIA_ID_CONTEXT,
    DECLARED_MANUAL_ENTRY_CONTEXT,
)

LINE_MODEL = 'madenat.lumber.volume.detail.line'
CONSOLE_MODEL = 'madenat.lumber.intake.console'
# Spec escalar equivalente al formulario curado / a la lista editable.
LINE_SPEC = {name: {} for name in (
    'description', 'observation', 'material_code', 'pieces',
    'width_declared', 'length_declared', 'thickness_declared', 'volume_m3',
    'origin', 'manually_adjusted')}


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredGridRpc(HttpCase):
    """Ruta RPC real (navegador) de la grilla declarada."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.lumber.volume.detail.line']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor RPC', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def setUp(self):
        super().setUp()
        # `authenticate` parchea `_check_credentials`, así que la clave es
        # indiferente; usamos el login REAL del usuario admin (en esta BD no
        # es 'admin', sino su correo).
        self.authenticate(self.env.ref('base.user_admin').login, 'admin')

    def _make_guia(self, name, state='verified', **extra):
        vals = {
            'name': name, 'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'granel', 'state': state,
            'date_emission': '2026-10-01', 'volume_pdf_m3': 40.315,
        }
        vals.update(extra)
        guia = self.Guia.create(vals)
        guia.flush_recordset()
        return guia

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id)], limit=1)

    def _call_kw(self, model, method, args, kwargs=None):
        """Reproduce la llamada JSON-RPC del cliente web (call_kw)."""
        return self.make_jsonrpc_request(
            '/web/dataset/call_kw/%s/%s' % (model, method),
            {'model': model, 'method': method, 'args': args,
             'kwargs': kwargs or {}})

    # ── 1. (a) onchange del diálogo "Agregar ítem" por RPC ─────────────────
    def test_01_rpc_onchange_dialogo_agregar_item(self):
        guia = self._make_guia('RPC-ONC-01')
        console = self._console_for(guia)
        action = console.action_add_declared_piece_line()
        context = dict(action['context'])
        # Forma EXACTA del cliente web: args = [ids, values, field_names, spec].
        result = self._call_kw(
            LINE_MODEL, 'onchange', [[], {}, [], LINE_SPEC],
            {'context': context})
        self.assertIsInstance(result, dict)
        self.assertIn('value', result)

    # ── 2. (b) onchange inline con guia_id = {id: <id de la CONSOLA>} ──────
    def test_02_rpc_onchange_inline_console_id(self):
        guia = self._make_guia('RPC-ONC-02')
        console = self._console_for(guia)
        # Este es el payload que antes rompía con KeyError 'declared_piece_line_ids'.
        result = self._call_kw(
            LINE_MODEL, 'onchange',
            [[], {'guia_id': {'id': console.id}}, [], LINE_SPEC], {})
        self.assertIsInstance(result, dict)

    # ── 3. create del diálogo por RPC (web_save) con texto multilínea ──────
    def test_03_rpc_web_save_dialogo_multilinea(self):
        guia = self._make_guia('RPC-ONC-03')
        console = self._console_for(guia)
        action = console.action_add_declared_piece_line()
        context = dict(action['context'])
        description = 'Descripción RPC\nsegunda línea'
        observation = 'Obs A\nObs B\nObs C'
        result = self._call_kw(
            LINE_MODEL, 'web_save',
            [[], {'description': description, 'observation': observation,
                  'pieces': 4}, {'id': {}}],
            {'context': context})
        new_id = result[0]['id']
        self.env.invalidate_all()
        line = self.Line.browse(new_id)
        self.assertEqual(line.guia_id, guia)
        self.assertEqual(line.origin, 'manual')
        self.assertEqual(line.description, description)
        self.assertEqual(line.observation, observation)
        # Relectura de la consola: la fila aparece en la grilla declarada.
        self.assertEqual(
            len(self._console_for(guia).declared_piece_line_ids), 1)

    # ── 4. alta inline + guardado de la consola por RPC (web_save) ─────────
    def test_04_rpc_web_save_inline_consola(self):
        guia = self._make_guia('RPC-ONC-04')
        console = self._console_for(guia)
        vals = {'declared_piece_line_ids': [
            (0, 'virtual_rpc_04', {
                'description': 'Inline RPC\nL2',
                'observation': 'A\nB',
                'pieces': 3,
            })]}
        self._call_kw(
            CONSOLE_MODEL, 'web_save',
            [[console.id], vals, {'id': {}}], {})
        self.env.invalidate_all()
        rows = self._console_for(guia).declared_piece_line_ids
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.guia_id, guia)
        self.assertEqual(rows.origin, 'manual')
        self.assertEqual(rows.description, 'Inline RPC\nL2')
        self.assertEqual(rows.observation, 'A\nB')

    # ── 5. editar y borrar una fila manual por RPC ─────────────────────────
    def test_05_rpc_editar_y_borrar_fila_manual(self):
        guia = self._make_guia('RPC-ONC-05')
        line = self.Line.create({
            'guia_id': guia.id, 'origin': 'manual',
            'description': 'original RPC', 'pieces': 2})
        guia.flush_recordset()
        console = self._console_for(guia)
        # Editar por la ruta del diálogo (contexto de captura manual).
        self._call_kw(
            LINE_MODEL, 'web_save',
            [[line.id], {'description': 'editada RPC', 'pieces': 9},
             {'id': {}}],
            {'context': {DECLARED_MANUAL_ENTRY_CONTEXT: True}})
        self.env.invalidate_all()
        self.assertEqual(line.description, 'editada RPC')
        self.assertEqual(line.pieces, 9)
        # Borrar desde la lista de la consola (comando DELETE).
        self._call_kw(
            CONSOLE_MODEL, 'web_save',
            [[console.id], {'declared_piece_line_ids': [(2, line.id)]},
             {'id': {}}], {})
        self.env.invalidate_all()
        self.assertFalse(line.exists())

    # ── 6. guía terminal: create por RPC rechazado por el servidor ─────────
    def test_06_rpc_create_guia_terminal_rechazado(self):
        guia = self._make_guia('RPC-ONC-06', state='validated')
        context = {
            DECLARED_MANUAL_ENTRY_CONTEXT: True,
            DECLARED_GUIA_ID_CONTEXT: guia.id,
        }
        with self.assertRaises(JsonRpcException):
            self._call_kw(
                LINE_MODEL, 'create', [[{'description': 'No permitida'}]],
                {'context': context})

    # ── 7. default_get por RPC neutraliza default_guia_id de la consola ────
    def test_07_rpc_default_get_neutraliza_consola(self):
        guia = self._make_guia('RPC-ONC-07')
        console = self._console_for(guia)
        result = self._call_kw(
            LINE_MODEL, 'default_get', [['guia_id']],
            {'context': {'default_guia_id': console.id}})
        self.assertEqual(result.get('guia_id'), guia.id)
