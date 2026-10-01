# -*- coding: utf-8 -*-
"""Regresión: onchange real del cliente web en la grilla declarada.

Cubre la causa raíz del RPC_ERROR (``KeyError: 'declared_piece_line_ids'``) que
se producía al añadir una línea inline en la lista editable de la Consola:

    web/models/models.py onchange -> _update_cache -> invf._update
    -> modified(['declared_piece_line_ids'])  (KeyError)

`declared_piece_line_ids` es un One2many NO almacenado de la CONSOLA cuyo campo
inverso es `guia_id` (Many2one a `madenat.guia.processing`). Odoo lo registra
como inverso GLOBAL de `guia_id`; al añadir una línea inline el cliente web
inyecta `guia_id = {..., id: <id de la CONSOLA>}` (el id del registro padre),
Odoo lo convierte en un registro de guía EN MEMORIA y ejecuta
`modified('declared_piece_line_ids')` sobre `madenat.guia.processing` — modelo
que no tiene ese campo — y falla con KeyError.

Se ejercita la RUTA DE ONCHANGE (`Form` / `onchange`), no solo create/web_save.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase

from odoo.addons.madenat_lumber_intake.models.intake_constants import (
    DECLARED_GUIA_ID_CONTEXT,
    DECLARED_MANUAL_ENTRY_CONTEXT,
)

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
# Campos escalares que expone el formulario curado / la lista editable.
LINE_FORM_FIELDS = (
    'description', 'observation', 'material_code', 'pieces',
    'width_declared', 'length_declared', 'thickness_declared', 'volume_m3',
    'origin', 'manually_adjusted',
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredGridOnchange(TransactionCase):
    """Ruta real de onchange del cliente web sobre la grilla declarada."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.lumber.volume.detail.line']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Onchange', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, state='verified', **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'granel',
            'state': state,
            'date_emission': '2026-10-01',
            'volume_pdf_m3': 40.315,
        }
        vals.update(extra)
        guia = self.Guia.create(vals)
        guia.flush_recordset()
        return guia

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _console_form(self, console):
        return Form(console, view=self.env.ref(CONSOLE_FORM).id)

    def _line_fields_spec(self):
        """Especificación mínima del formulario curado de la línea."""
        return {fname: {} for fname in LINE_FORM_FIELDS}

    def _grid_rows(self, guia):
        self.env.invalidate_all()
        return self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.origin in ('header', 'manual'))

    # ── 1. Causa raíz: el registry declara DOS inversos sobre guia_id ──────
    def test_01_registry_inverso_global_sobre_guia_id(self):
        """Evidencia: `declared_piece_line_ids` figura como inverso de guia_id."""
        inverses = {
            '%s.%s' % (inv.model_name, inv.name)
            for inv in self.env.registry.field_inverses[
                self.Line._fields['guia_id']]
        }
        self.assertIn(
            'madenat.lumber.intake.console.declared_piece_line_ids', inverses)
        self.assertNotIn(
            'declared_piece_line_ids', self.Guia._fields,
            'La guía no define el campo: por eso el modified() del inverso '
            'rompía con KeyError.')

    # ── 2. (a) onchange del diálogo "Agregar ítem" con el contexto real ────
    def test_02_onchange_dialogo_agregar_item_sin_error(self):
        guia = self._make_guia('VOL-ONC-02')
        console = self._console_for(guia)
        action = console.action_add_declared_piece_line()
        context = action['context']
        # La guía viaja en la clave propia; NO en default_guia_id.
        self.assertNotIn('default_guia_id', context)
        self.assertEqual(context[DECLARED_GUIA_ID_CONTEXT], guia.id)
        # onchange real del diálogo (ruta del cliente web).
        form = Form.from_action(self.env, action)
        # El formulario no expone guia_id (lo resuelve el servidor al crear).
        self.assertNotIn('guia_id', form._view['fields'])

    # ── 3. create desde el diálogo con texto multilínea ────────────────────
    def test_03_dialogo_create_guia_correcta_origin_manual(self):
        guia = self._make_guia('VOL-ONC-03')
        console = self._console_for(guia)
        action = console.action_add_declared_piece_line()
        form = Form.from_action(self.env, action)
        description = 'Descripción del diálogo\nsegunda línea'
        observation = 'Obs 1\nObs 2\nObs 3'
        form.description = description
        form.observation = observation
        form.pieces = 6
        line = form.save()
        self.assertEqual(line.guia_id, guia)
        self.assertEqual(line.origin, 'manual')
        self.assertEqual(line.description, description)
        self.assertEqual(line.observation, observation)
        guia.flush_recordset()
        self.env.invalidate_all()
        self.assertEqual(len(self._grid_rows(guia)), 1)

    # ── 4. (b) onchange inline: guia_id = {id: <id de la CONSOLA>} ─────────
    def test_04_onchange_inline_consola_id_no_falla(self):
        guia = self._make_guia('VOL-ONC-04')
        console = self._console_for(guia)
        # Replica exacta del cliente web (StaticList._createNewRecordDatapoint
        # -> Record._getOnchangeValues): guia_id = {..., id: <padre consola>}.
        result = self.Line.onchange(
            {'guia_id': {'id': console.id,
                         'display_name': console.display_name}},
            [], self._line_fields_spec())
        self.assertIsInstance(result, dict)

    # ── 5. (b) agregar línea inline y guardar en la Consola ────────────────
    def test_05_inline_nueva_linea_guia_correcta(self):
        guia = self._make_guia('VOL-ONC-05')
        console = self._console_for(guia)
        form = self._console_form(console)
        with form.declared_piece_line_ids.new() as line_form:
            line_form.description = 'Inline 05'
            line_form.observation = 'Línea A\nLínea B'
            line_form.pieces = 3
        form.save()
        rows = self._grid_rows(guia)
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows.guia_id, guia,
            'La fila inline debe quedar con la guía REAL, no con el id de '
            'la consola')
        self.assertEqual(rows.origin, 'manual')
        self.assertEqual(rows.description, 'Inline 05')
        self.assertEqual(rows.observation, 'Línea A\nLínea B')

    # ── 6. (c)(d) abrir/editar y borrar una fila manual existente ──────────
    def test_06_ver_editar_borrar_fila_manual(self):
        guia = self._make_guia('VOL-ONC-06')
        line = self.Line.create({
            'guia_id': guia.id, 'origin': 'manual',
            'description': 'original', 'pieces': 2})
        guia.flush_recordset()
        console = self._console_for(guia)
        form = self._console_form(console)
        with form.declared_piece_line_ids.edit(0) as line_form:
            line_form.description = 'editada'
            line_form.pieces = 9
        form.save()
        self.env.invalidate_all()
        self.assertEqual(line.description, 'editada')
        self.assertEqual(line.pieces, 9)
        # Borrado desde la lista.
        console = self._console_for(guia)
        form = self._console_form(console)
        form.declared_piece_line_ids.remove(index=0)
        form.save()
        self.env.invalidate_all()
        self.assertFalse(line.exists(), 'La fila debe eliminarse')

    # ── 7. id de la CONSOLA se resuelve a la guía real en create/onchange ──
    def test_07_console_id_resuelve_guia_real(self):
        guia = self._make_guia('VOL-ONC-07')
        console = self._console_for(guia)
        # create sin guia_id: la toma del contexto propio del diálogo.
        ctx = {
            DECLARED_MANUAL_ENTRY_CONTEXT: True,
            DECLARED_GUIA_ID_CONTEXT: console.id,
        }
        line = self.Line.with_context(**ctx).create(
            {'description': 'via contexto'})
        self.assertEqual(line.guia_id, guia)
        self.assertEqual(line.origin, 'manual')
        # default_get neutraliza default_guia_id = id de la consola.
        defaults = self.Line.with_context(
            default_guia_id=console.id).default_get(['guia_id'])
        self.assertEqual(defaults['guia_id'], guia.id)

    # ── 8. Guía terminal: onchange tolerante, create rechazado ─────────────
    def test_08_guia_terminal_onchange_tolera_create_rechaza(self):
        guia = self._make_guia('VOL-ONC-08', state='validated')
        console = self._console_for(guia)
        # El onchange no debe romper (neutraliza la referencia de consola).
        self.Line.onchange(
            {'guia_id': {'id': console.id}}, [], self._line_fields_spec())
        with self.assertRaises(UserError):
            self.Line.with_context(
                **{DECLARED_MANUAL_ENTRY_CONTEXT: True}).create(
                {'guia_id': guia.id, 'description': 'No'})

    # ── 9. Filas pdf/excel/header intactas y no proyectadas ────────────────
    def test_09_filas_documentales_intactas(self):
        guia = self._make_guia('VOL-ONC-09')
        pdf = self.Line.create({
            'guia_id': guia.id, 'origin': 'pdf', 'source_line_no': 1,
            'description': 'PDF', 'volume_m3': 1.0})
        excel = self.Line.create({
            'guia_id': guia.id, 'origin': 'excel', 'source_line_no': 2,
            'description': 'Excel', 'volume_m3': 2.0})
        header = self.Line.create({
            'guia_id': guia.id, 'origin': 'header',
            'description': 'Cabecera declarada'})
        guia.flush_recordset()
        console = self._console_for(guia)
        # La grilla declarada proyecta sólo 'header' (y 'manual').
        self.assertEqual(console.declared_piece_line_ids, header)
        # Añadir una fila manual inline.
        form = self._console_form(console)
        with form.declared_piece_line_ids.new() as line_form:
            line_form.description = 'Manual 09'
        form.save()
        self.env.invalidate_all()
        # PDF/Excel/Header siguen intactos.
        self.assertEqual(pdf.origin, 'pdf')
        self.assertEqual(pdf.description, 'PDF')
        self.assertEqual(excel.origin, 'excel')
        self.assertEqual(excel.description, 'Excel')
        self.assertEqual(header.origin, 'header')
        self.assertEqual(header.description, 'Cabecera declarada')
        # Y no se proyectan en la grilla declarada.
        rows = self._console_for(guia).declared_piece_line_ids
        self.assertNotIn(pdf, rows)
        self.assertNotIn(excel, rows)
