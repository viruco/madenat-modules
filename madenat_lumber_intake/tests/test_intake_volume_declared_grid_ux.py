# -*- coding: utf-8 -*-
"""Grilla declarada: descripción/observación, formulario de detalle y riesgo.

Cubre el refinamiento UX del bloque «DATOS DECLARADOS DE LA GUÍA»:

1. Primera pulsación de «Aplicar datos documentales»: la fila de cabecera nace
   con la DESCRIPCIÓN POR DEFECTO y la observación vacía.
2. Editar la descripción/observación de la fila de cabecera y volver a pulsar el
   botón: AMBAS se conservan (la sincronización no las pisa).
3. Fila MANUAL con descripción y observación largas (multilínea): persisten tras
   guardar y releer.
4. Estados terminales (`validated`/`cancelled`): la grilla y su formulario de
   detalle quedan en solo lectura (readonly del campo completo) y el modelo
   rechaza la escritura.
5. Vista: `open_form_view` + `<form>` inline dentro del campo, con
   Descripción/Observación de varias líneas (widget text) y Origen/Ajuste
   manual de solo lectura.
6. RIESGO DE VOLUMEN (NO corregido sin aprobación): una fila MANUAL con
   `volume_m3 > 0` SÍ se suma a `volume_detail_m3` —el agregado solo excluye
   `origin='header'`— y contamina `official_vs_detail_diff_m3`,
   `declared_lines_volume_m3` y `declared_lines_vs_official_m3`. La prueba
   documenta el efecto exacto ANTES/DESPUÉS.
7. Botón «Agregar ítem» (captura manual del detalle declarado): visible solo en
   guías no terminales, abre el diálogo `target='new'` con el formulario curado;
   el servidor fuerza `origin='manual'` y valida guía de Volumen no terminal.

TransactionCase: nada se persiste; no se tocan guías/lotes/pickings reales.
"""

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.madenat_lumber_intake.models.intake_constants import (
    DECLARED_GUIA_ID_CONTEXT,
    DECLARED_MANUAL_ENTRY_CONTEXT,
    HEADER_DECLARED_DESCRIPTION,
)

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
GRID_FIELD = 'declared_piece_line_ids'
READONLY_EXPRESSION = "state in ('validated', 'cancelled')"
# Campos que el formulario de detalle debe ofrecer (reutilizan los de la lista).
FORM_FIELDS = (
    'material_code', 'description', 'pieces', 'width_declared',
    'length_declared', 'thickness_declared', 'volume_m3', 'observation',
    'origin', 'manually_adjusted',
)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredGridUx(TransactionCase):
    """Descripción/Observación, formulario de detalle y riesgo de volumen."""

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
            'name': 'Proveedor Grilla UX', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, state='verified', **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'granel',
            'state': state,
            'date_emission': '2026-09-24',
            'volume_pdf_m3': 40.315,
        }
        vals.update(extra)
        guia = self.Guia.create(vals)
        guia.flush_recordset()
        return guia

    def _guia_with_header_data(self, name, state='verified'):
        return self._make_guia(
            name, state=state,
            piezas_declaradas=124,
            anchos_variables='RW / 4 1/2 - 6 1/4',
            largos_variables='RL / 8 - 12',
            espesor_nominal_texto='7/4',
        )

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _header_lines(self, guia):
        self.env.invalidate_all()
        return self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.origin == 'header')

    def _grid_rows(self, guia):
        self.env.invalidate_all()
        return (self.Guia.browse(guia.id).volume_detail_line_ids
                .sorted(key=lambda line: (line.source_line_no, line.id)))

    # ── 1. Descripción por defecto SOLO al crear la fila de cabecera ──────
    def test_01_cabecera_nace_con_descripcion_por_defecto(self):
        """Primera pulsación: descripción por defecto y observación vacía."""
        guia = self._guia_with_header_data('VOL-UX-01')
        self._console_for(guia).action_apply_declared_volume_suggestions()

        line = self._header_lines(guia)
        self.assertEqual(len(line), 1)
        self.assertEqual(
            line.description, HEADER_DECLARED_DESCRIPTION,
            'La fila de cabecera nace con la descripción por defecto')
        self.assertFalse(line.observation, 'La observación nace vacía')

        # Reaplicar sin cambios no crea filas nuevas ni altera la descripción.
        for _index in range(2):
            self._console_for(guia).action_apply_declared_volume_suggestions()
        line = self._header_lines(guia)
        self.assertEqual(len(line), 1, 'La sincronización es idempotente')
        self.assertEqual(line.description, HEADER_DECLARED_DESCRIPTION)

    def test_02_edicion_de_descripcion_y_observacion_se_conserva(self):
        """Editar descripción y observación; reaplicar NO las pisa."""
        guia = self._guia_with_header_data('VOL-UX-02')
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        line = self._header_lines(guia)

        edited_description = 'Corrección del operador\nsegunda línea'
        edited_observation = 'Observación del operador\ncon varias líneas'
        line.write({
            'description': edited_description,
            'observation': edited_observation,
        })
        self.env.invalidate_all()

        # Nueva pulsación del botón documental.
        self._console_for(guia).action_apply_declared_volume_suggestions()

        line = self._header_lines(guia)
        self.assertEqual(len(line), 1)
        self.assertEqual(
            line.description, edited_description,
            'La sincronización NO pisa la descripción editada')
        self.assertEqual(
            line.observation, edited_observation,
            'La sincronización NO pisa la observación editada')

    # ── 3. Fila manual con texto largo multilínea ─────────────────────────
    def test_03_fila_manual_multilinea_persiste(self):
        """Descripción y observación largas de una fila manual sobreviven."""
        guia = self._make_guia('VOL-UX-03')
        console = self._console_for(guia)

        description = (
            'Descripción extensa de la línea manual que ocupa varias líneas\n'
            'y contiene un salto de línea y un tabulador\tinterno.')
        observation = (
            'Observación línea 1\nObservación línea 2\nObservación línea 3')
        console.write({GRID_FIELD: [
            (0, 'virtual_ux', {
                'description': description,
                'observation': observation,
                'material_code': 'COD-UX',
                'pieces': 2,
                'volume_m3': 1.5,
            }),
        ]})

        rows = self._grid_rows(guia)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.origin, 'manual')
        self.assertEqual(rows.description, description,
                         'La descripción multilínea debe persistir')
        self.assertEqual(rows.observation, observation,
                         'La observación multilínea debe persistir')

        # Relectura limpia (nueva transacción lógica).
        self.env.invalidate_all()
        rows = self._grid_rows(guia)
        self.assertEqual(rows.description, description)
        self.assertEqual(rows.observation, observation)


    # ── 4. Estados terminales: grilla y formulario solo lectura ───────────
    def test_04_estados_terminales_solo_lectura(self):
        """La grilla y su formulario quedan en solo lectura por estado."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        grid = root.xpath("//field[@name='%s']" % GRID_FIELD)[0]
        self.assertEqual(
            grid.get('readonly'), READONLY_EXPRESSION,
            'El readonly del campo completo gobierna grilla y formulario')
        self.assertEqual(
            len(grid.xpath(".//form")), 1,
            'El formulario de detalle vive dentro del campo readonly')

        for state in ('validated', 'cancelled'):
            guia = self._make_guia(
                'VOL-UX-TERM-%s' % state.upper(), state=state)
            console = self._console_for(guia)
            self.assertTrue(console)
            with self.assertRaises(UserError):
                console.write({GRID_FIELD: [
                    (0, 'virtual_%s' % state, {'description': 'No permitida'}),
                ]})

    # ── 5. Vista: open_form_view + formulario de detalle ──────────────────
    def test_05_vista_formulario_de_detalle(self):
        """El formulario inline es multilínea y respeta readonly de evidencia."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        grid = root.xpath("//field[@name='%s']" % GRID_FIELD)[0]

        lists = grid.xpath(".//list")
        self.assertEqual(len(lists), 1)
        self.assertEqual(
            lists[0].get('open_form_view'), '1',
            'La lista habilita abrir cada fila en su formulario')

        forms = grid.xpath(".//form")
        self.assertEqual(len(forms), 1, 'Debe existir un formulario de detalle')
        form = forms[0]
        form_fields = [node.get('name') for node in form.iter('field')]
        for field_name in FORM_FIELDS:
            self.assertIn(
                field_name, form_fields,
                'El formulario debe incluir %s' % field_name)
        for field_name in ('description', 'observation'):
            node = form.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('widget'), 'text',
                '%s debe ser de varias líneas (widget text)' % field_name)
        for field_name in ('origin', 'manually_adjusted'):
            node = form.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('readonly'), '1',
                '%s es evidencia: solo lectura en el formulario' % field_name)


    # ── 6. RIESGO DE VOLUMEN (documentado, SIN corregir) ──────────────────
    def test_06_riesgo_fila_manual_con_volumen_contamina_agregados(self):
        """Fila MANUAL con volumen SÍ se suma al detalle documental.

        REGLA VIGENTE: `_compute_volume_detail_m3` excluye SOLO
        `origin='header'`. Una fila `origin='manual'` con `volume_m3 > 0` entra
        al agregado, alterando `official_vs_detail_diff_m3` y los totales
        informativos de la consola.

        Esta prueba CODIFICA la conducta ACTUAL (riesgo pendiente). Si el
        cliente aprueba excluir también 'manual' del agregado, las aserciones de
        `after` deben invertirse a 0.0 / 40.315.
        """
        guia = self._make_guia('VOL-UX-RIESGO', volume_pdf_m3=40.315)
        console = self._console_for(guia)
        guia = self.Guia.browse(guia.id)

        before = {
            'volume_detail_m3': guia.volume_detail_m3,
            'official_vs_detail_diff_m3': guia.official_vs_detail_diff_m3,
            'official_volume_m3': guia.official_volume_m3,
            'conciliation_status': guia.conciliation_status,
            'declared_lines_volume_m3': console.declared_lines_volume_m3,
            'declared_lines_vs_official_m3':
                console.declared_lines_vs_official_m3,
        }

        # Fila MANUAL con volumen (> 0): captura del operador.
        console.write({GRID_FIELD: [
            (0, 'virtual_vol', {
                'description': 'Manual con volumen',
                'pieces': 3,
                'volume_m3': 5.0,
            }),
        ]})

        guia = self.Guia.browse(guia.id)
        console = self._console_for(guia)
        after = {
            'volume_detail_m3': guia.volume_detail_m3,
            'official_vs_detail_diff_m3': guia.official_vs_detail_diff_m3,
            'official_volume_m3': guia.official_volume_m3,
            'conciliation_status': guia.conciliation_status,
            'declared_lines_volume_m3': console.declared_lines_volume_m3,
            'declared_lines_vs_official_m3':
                console.declared_lines_vs_official_m3,
        }

        # Antes: sin detalle → agregado 0 y diferencia = volumen oficial.
        self.assertAlmostEqual(before['volume_detail_m3'], 0.0, places=3)
        self.assertAlmostEqual(
            before['official_vs_detail_diff_m3'], 40.315, places=3)
        self.assertAlmostEqual(
            before['declared_lines_volume_m3'], 0.0, places=3)
        self.assertAlmostEqual(
            before['declared_lines_vs_official_m3'], 40.315, places=3)

        # Después: el volumen MANUAL entró al agregado del detalle documental.
        self.assertAlmostEqual(
            after['volume_detail_m3'], 5.0, places=3,
            msg='CONTAMINACIÓN: el volumen manual se sumó a volume_detail_m3')
        self.assertAlmostEqual(
            after['official_vs_detail_diff_m3'], 35.315, places=3,
            msg='La diferencia vs el volumen oficial cambió por la fila manual')
        self.assertAlmostEqual(
            after['declared_lines_volume_m3'], 5.0, places=3,
            msg=('El pie «Volumen del detalle documental del PDF/Excel» '
                 'incluye la fila manual'))
        self.assertAlmostEqual(
            after['declared_lines_vs_official_m3'], 35.315, places=3)

        # El volumen OFICIAL nunca se toca (la fila manual no es fuente oficial).
        self.assertAlmostEqual(
            after['official_volume_m3'], before['official_volume_m3'],
            places=3)

        # La conciliación almacenada NO cambia: compara cabeceras documentales
        # (PDF vs Excel) al ingestarse, no la suma del detalle.
        self.assertEqual(
            after['conciliation_status'], before['conciliation_status'],
            'La conciliación almacenada no se recalcula desde el detalle')


    # ── 7. Formulario curado del botón «Ver» (vista form por defecto) ──────
    def test_07_formulario_ver_curado(self):
        """El botón «Ver» abre la vista form curada, no una autogenerada.

        En Odoo 18 `open_form_view` (lista x2many editable) abre el registro con
        la vista form por defecto del modelo. Se define una vista curada para
        que muestre los mismos campos que el `<form>` inline.
        """
        Line = self.env['madenat.lumber.volume.detail.line']
        view = self.env.ref(
            'madenat_lumber_intake'
            '.view_madenat_lumber_volume_detail_line_form')
        self.assertEqual(
            view.model, 'madenat.lumber.volume.detail.line')
        self.assertEqual(
            self.env['ir.ui.view'].default_view(Line._name, 'form'), view.id,
            'La vista curada debe ser la form por defecto del modelo')

        field_names = [node.get('name') for node in etree.fromstring(
            view.arch).iter('field')]
        for field_name in FORM_FIELDS:
            self.assertIn(
                field_name, field_names,
                'La vista curada debe incluir %s' % field_name)
        self.assertEqual(
            field_names[:2], ['description', 'observation'],
            'Descripción y Observación van en primer plano en el diálogo')
        arch = etree.fromstring(view.arch)
        for field_name in ('description', 'observation'):
            node = arch.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(node.get('widget'), 'text')
        for field_name in ('origin', 'manually_adjusted'):
            node = arch.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(node.get('readonly'), '1')


    # ── 8. Botón «Agregar ítem»: acción y vista ────────────────────────────
    def test_08_accion_agregar_item_abre_dialogo(self):
        """El botón devuelve el diálogo de captura con la guía y origen fijados."""
        guia = self._make_guia('VOL-UX-08')
        console = self._console_for(guia)
        action = console.action_add_declared_piece_line()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(
            action.get('res_model'),
            'madenat.lumber.volume.detail.line')
        self.assertEqual(
            action.get('name'), 'Agregar ítem a piezas declaradas')
        form_view = self.env.ref(
            'madenat_lumber_intake'
            '.view_madenat_lumber_volume_detail_line_form')
        self.assertEqual(action.get('views'), [(form_view.id, 'form')])
        context = action.get('context') or {}
        # La guía viaja en la clave PROPIA (no en default_guia_id, que provocaba
        # el KeyError del onchange por el inverso global declarado sobre guia_id).
        self.assertNotIn(
            'default_guia_id', context,
            'El diálogo no debe usar default_guia_id (causa del KeyError)')
        self.assertEqual(context.get(DECLARED_GUIA_ID_CONTEXT), guia.id)
        self.assertEqual(context.get('default_origin'), 'manual')
        self.assertTrue(context.get(DECLARED_MANUAL_ENTRY_CONTEXT))

    def test_09_boton_en_vista_y_estado_vacio(self):
        """Botón único junto al contador; estado vacío con el texto nuevo."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        buttons = root.xpath(
            "//button[@name='action_add_declared_piece_line']")
        self.assertEqual(
            len(buttons), 1, 'Debe existir un solo botón Agregar ítem')
        button = buttons[0]
        self.assertEqual(button.get('type'), 'object')
        self.assertEqual(button.get('string'), 'Agregar ítem')
        self.assertEqual(
            button.get('invisible'),
            "state in ('validated', 'cancelled')",
            'El botón se oculta en estados terminales')

        grids = root.xpath(
            "//div[@colspan='2'][.//field[@name='%s']]" % GRID_FIELD)
        self.assertEqual(len(grids), 1, 'Falta el contenedor de la grilla')
        empties = grids[0].xpath(".//div[@invisible='%s']" % GRID_FIELD)
        self.assertEqual(len(empties), 1)
        self.assertEqual(
            ' '.join((empties[0].text or '').split()),
            'Sin piezas declaradas. Use «Agregar ítem» o «Aplicar datos '
            'documentales» para comenzar.')

    # ── 9. Diálogo: crea fila manual multilínea ───────────────────────────
    def test_10_dialogo_crea_fila_manual(self):
        """La creación del diálogo (contexto interno) persiste la fila manual."""
        guia = self._make_guia('VOL-UX-10')
        description = 'Descripción del diálogo\nsegunda línea'
        observation = 'Obsc 1\nObsc 2\nObsc 3'
        Line = self.Line.with_context(**{DECLARED_MANUAL_ENTRY_CONTEXT: True})
        line = Line.create({
            'guia_id': guia.id,
            'material_code': 'DIAL-1',
            'description': description,
            'observation': observation,
            'pieces': 4,
            'volume_m3': 2.0,
        })
        self.assertEqual(line.origin, 'manual')
        self.assertEqual(line.description, description)
        self.assertEqual(line.observation, observation)

        console = self._console_for(guia)
        self.assertEqual(len(console.declared_piece_line_ids), 1)
        self.assertEqual(console.declared_lines_pieces, 4)

    def test_11_dialogo_fuerza_origin_manual(self):
        """Aunque el vals diga pdf/excel/header, el diálogo fuerza manual."""
        guia = self._make_guia('VOL-UX-11')
        Line = self.Line.with_context(**{DECLARED_MANUAL_ENTRY_CONTEXT: True})
        for origin in ('pdf', 'excel', 'header'):
            line = Line.create({
                'guia_id': guia.id, 'origin': origin,
                'description': 'Intento %s' % origin,
            })
            self.assertEqual(line.origin, 'manual')
        self.assertEqual(
            guia.volume_detail_line_ids.mapped('origin'), ['manual'] * 3,
            'Ninguna fila del diálogo puede ser pdf/excel/header')

    # ── 10. Guardas de servidor (terminal y no-volumen) ───────────────────
    def test_12_guardas_servidor(self):
        """Terminal y no-volumen: UserError en la acción y en el create."""
        Line = self.Line.with_context(**{DECLARED_MANUAL_ENTRY_CONTEXT: True})
        for state in ('validated', 'cancelled'):
            guia = self._make_guia(
                'VOL-UX-T-%s' % state.upper(), state=state)
            console = self._console_for(guia)
            with self.assertRaises(UserError):
                console.action_add_declared_piece_line()
            with self.assertRaises(UserError):
                Line.create({'guia_id': guia.id, 'description': 'No'})

        compra = self._make_guia(
            'VOL-UX-COMPRA', tipo_recepcion='compra')
        self.assertNotEqual(
            self._console_for(compra).ingestion_type, 'volume')
        with self.assertRaises(UserError):
            Line.create({'guia_id': compra.id, 'description': 'No'})

        with self.assertRaises(UserError):
            Line.create({'description': 'Sin guía'})

    # ── 11. El diálogo no edita evidencia ni la fila de cabecera ──────────
    def test_13_dialogo_no_edita_filas_no_manuales(self):
        """Con el contexto del diálogo, write rechaza filas no manuales."""
        guia = self._make_guia('VOL-UX-13')
        pdf = self.Line.create({
            'guia_id': guia.id, 'origin': 'pdf', 'source_line_no': 1,
            'description': 'PDF', 'volume_m3': 1.0})
        header = self.Line.create({
            'guia_id': guia.id, 'origin': 'header',
            'description': 'Cabecera'})
        manual = self.Line.create({
            'guia_id': guia.id, 'origin': 'manual', 'description': 'Manual'})

        ctx = self.Line.with_context(**{DECLARED_MANUAL_ENTRY_CONTEXT: True})
        with self.assertRaises(UserError):
            ctx.browse(pdf.id).write({'description': 'No'})
        with self.assertRaises(UserError):
            ctx.browse(header.id).write({'description': 'No'})
        # La fila manual sí se edita, pero nunca cambia el origen.
        ctx.browse(manual.id).write({
            'description': 'Sí', 'origin': 'pdf'})
        self.assertEqual(manual.description, 'Sí')
        self.assertEqual(manual.origin, 'manual')
        # La evidencia documental y la cabecera quedan intactas.
        self.assertEqual(pdf.description, 'PDF')
        self.assertEqual(header.description, 'Cabecera')
