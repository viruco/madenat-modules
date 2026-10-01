# -*- coding: utf-8 -*-
"""Grilla declarada: proyecta SOLO filas 'header'/'manual' (Fase UX).

Contrato verificado (TransactionCase: nada se persiste; no se tocan guías,
lotes, pickings ni secuencias reales):

1. Guía con detalle documental (12 líneas del PDF + 1 del Excel): la grilla de
   la consola aparece VACÍA y su contador en 0, mientras
   `volume_detail_line_ids` conserva las 13 líneas (pestaña Packing intacta).
2. «Aplicar datos documentales» agrega SOLO la fila de cabecera; las líneas
   documentales no aparecen en la grilla ni se modifican.
3. Agregar, editar y eliminar una fila manual: las líneas del PDF/Excel quedan
   intactas (mismos ids y mismos valores).
4. Quitar TODAS las filas visibles (lista vacía / DELETE): las líneas
   'pdf'/'excel' NO se borran (alcance del inverse limitado a la grilla).
5. Los agregados canónicos no cambian: `volume_detail_m3`,
   `official_vs_detail_diff_m3`, conciliación, estado y volumen oficial.
6. Vista: mismo inventario de campos/botones, tres bloques titulados, los
   cuatro campos declarados en una sola fila y la grilla a ancho completo con
   los pies etiquetados como DETALLE DOCUMENTAL DEL PDF/EXCEL.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
GRID_FIELD = 'declared_piece_line_ids'
VISIBLE_ORIGINS = ('header', 'manual')
DOCUMENTAL_ORIGINS = ('pdf', 'excel')

# Columnas aprobadas de la grilla declarada (inventario sin pérdidas).
GRID_COLUMNS = [
    'line_no', 'material_code', 'description', 'pieces', 'width_declared',
    'length_declared', 'thickness_declared', 'volume_m3', 'observation',
    'origin', 'manually_adjusted',
]
# Campos del formulario de detalle de la fila (inline <form> dentro del campo):
# reutilizan campos YA existentes de la lista — Descripción y Observación de
# varias líneas más la captura—; no introducen campos nuevos ni pierden nodos.
GRID_FORM_FIELDS = (
    'material_code', 'description', 'pieces', 'width_declared',
    'length_declared', 'thickness_declared', 'volume_m3', 'observation',
    'origin', 'manually_adjusted',
)
# Inventario COMPLETO de nodos del bloque declarado (antes == después + el
# formulario de detalle, que reutiliza los mismos nombres de campo).
DECLARED_GROUP_FIELDS = (
    'official_volume_effective_m3', 'official_volume_effective_source',
    'declared_pieces', 'declared_widths_text', 'declared_lengths_text',
    'declared_thickness_text', 'declared_volume_m3', 'declared_sv_lot_id',
    'suggested_pieces', 'suggested_widths_text', 'suggested_lengths_text',
    'suggested_thickness_text', 'suggested_volume_m3',
    'suggested_volume_source', 'declared_lines_pieces',
    'declared_piece_line_ids', 'declared_lines_volume_m3',
    'declared_lines_vs_official_m3',
    'sv_lot_label', 'sv_available_m3', 'sv_original_volume_m3',
    'sv_regularized_baseline_m3', 'sv_rebajado_m3', 'sv_pieces_enabled',
    'sv_available_pieces', 'sv_documentary_warning',
    'sv_reversible_rebaja_id', 'sv_next_label_estimate',
    'volume_operational_m3', 'volume_operational_source',
    'volume_operational_note', 'review_state',
) + tuple(GRID_COLUMNS) + GRID_FORM_FIELDS
DECLARED_GROUP_BUTTONS = (
    'action_sv_regularize_volume', 'action_sv_rename', 'action_sv_rebaja',
    'action_sv_reverse_rebaja', 'action_open_sv_history',
    'action_apply_declared_volume_suggestions',
    # Punto de entrada «Agregar ítem» (captura manual del detalle declarado).
    'action_add_declared_piece_line',
)
DECLARED_GROUP_TITLES = [
    DECLARED_GROUP, 'ETIQUETA SV',
    'Volumen operativo de referencia (no gobierna stock)',
]
# Fórmulas declaradas de la fila de cabecera y de los pies documentales.
CAPTURE_FIELDS = (
    'declared_pieces', 'declared_widths_text', 'declared_lengths_text',
    'declared_thickness_text',
)
DOCUMENTAL_VOLUME_LABEL = 'Volumen del detalle documental del PDF/Excel:'
DOCUMENTAL_DIFF_LABEL = (
    'Diferencia del detalle documental vs volumen oficial:')
DOCUMENTAL_NOTE = ('El detalle de piezas es documental y no reemplaza el '
                   'volumen oficial de la guía.')
EMPTY_STATE = ('Sin piezas declaradas. Use «Agregar ítem» o «Aplicar datos '
               'documentales» para comenzar.')



@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredGridFilter(TransactionCase):
    """La grilla declarada no proyecta el detalle documental del PDF/Excel."""

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
            'name': 'Proveedor Grilla Declarada', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': 'granel',
            'state': 'verified',
            'date_emission': '2026-09-24',
            'volume_pdf_m3': 40.315,
            'conciliation_status': 'not_compared',
            # Datos declarados de cabecera (los refleja el botón documental).
            'piezas_declaradas': 124,
            'anchos_variables': 'RW / 4 1/2 - 6 1/4',
            'largos_variables': 'RL / 8 - 12',
            'espesor_nominal_texto': '7/4',
        }
        vals.update(extra)
        guia = self.Guia.create(vals)
        guia.flush_recordset()
        return guia

    def _make_documental_detail(self, guia):
        """Detalle documental: 12 líneas del PDF (36.000 m³) + 1 del Excel."""
        vals = [{
            'guia_id': guia.id,
            'origin': 'pdf',
            'source_line_no': index,
            'source_page': 1,
            'description': 'Línea PDF %d' % index,
            'material_code': 'M-%02d' % index,
            'volume_m3': 3.0,
            'pieces': 7 if index == 1 else 0,
        } for index in range(1, 13)]
        vals.append({
            'guia_id': guia.id,
            'origin': 'excel',
            'source_line_no': 13,
            'lot_or_package': 'D8828',
            'description': 'Línea Excel',
            'volume_m3': 4.3,
            'pieces': 264,
        })
        lines = self.Line.create(vals)
        self.env.flush_all()
        return lines

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _guia(self, guia):
        self.env.invalidate_all()
        return self.Guia.browse(guia.id)

    def _documental_snapshot(self, guia):
        """Ids y valores de las líneas documentales (evidencia intacta)."""
        lines = self._guia(guia).volume_detail_line_ids.filtered(
            lambda line: line.origin in DOCUMENTAL_ORIGINS)
        return {
            line.id: (
                line.origin, line.description, line.pieces, line.volume_m3,
                line.source_line_no,
            ) for line in lines
        }

    # ── 1. Guía con detalle documental: grilla vacía y detalle intacto ────
    def test_01_grilla_vacia_con_detalle_documental(self):
        """12 líneas del PDF + 1 del Excel: la grilla aparece VACÍA."""
        guia = self._make_guia('VOL-GRID-FILTER-01')
        detail = self._make_documental_detail(guia)
        self.assertEqual(len(detail), 13)
        console = self._console_for(guia)

        self.assertTrue(
            console, 'La consola debe exponer la guía de Volumen')
        self.assertFalse(
            console.declared_piece_line_ids,
            'La grilla declarada debe empezar vacía: el detalle del PDF/Excel '
            'no se proyecta')
        self.assertEqual(console.declared_lines_pieces, 0)
        # El detalle documental sigue completo y con sus piezas reales.
        lineas = self._guia(guia).volume_detail_line_ids
        self.assertEqual(len(lineas), 13, 'El Packing de la fachada no cambia')
        self.assertEqual(
            sorted(lineas.mapped('origin')), ['excel'] + ['pdf'] * 12)
        self.assertEqual(
            sum(lineas.filtered(lambda l: l.origin == 'pdf').mapped('pieces')),
            7)
        self.assertEqual(
            lineas.filtered(lambda l: l.origin == 'excel').pieces, 264)
        # El detalle documental (no la grilla) alimenta los agregados y pies.
        self.assertAlmostEqual(console.declared_lines_volume_m3, 40.3, places=3)
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3, 0.015, places=3)

    # ── 2. «Aplicar datos documentales»: solo la fila de cabecera ─────────
    def test_02_aplicar_agrega_solo_la_fila_de_cabecera(self):
        """El botón agrega UNA fila 'header': el detalle no aparece ni cambia."""
        guia = self._make_guia('VOL-GRID-FILTER-02')
        self._make_documental_detail(guia)
        before = self._documental_snapshot(guia)
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        self.env.invalidate_all()

        console = self._console_for(guia)
        rows = console.declared_piece_line_ids
        self.assertEqual(len(rows), 1, 'Solo la fila de cabecera declarada')
        self.assertEqual(rows.origin, 'header')
        self.assertEqual(rows.pieces, 124)
        self.assertEqual(rows.width_declared, 'RW / 4 1/2 - 6 1/4')
        self.assertAlmostEqual(rows.volume_m3, 40.315, places=3)
        self.assertEqual(
            console.declared_lines_pieces, 124,
            'El contador suma solo las filas visibles de la grilla')
        # Las 13 líneas documentales siguen idénticas (ids y valores).
        self.assertEqual(self._documental_snapshot(guia), before)
        self.assertEqual(len(self._guia(guia).volume_detail_line_ids), 14)

    # ── 3. Captura manual sin tocar el detalle documental ─────────────────
    def test_03_captura_manual_intacta_el_detalle_documental(self):
        """Agregar, editar y eliminar filas manuales no toca pdf/excel."""
        guia = self._make_guia('VOL-GRID-FILTER-03')
        self._make_documental_detail(guia)
        before = self._documental_snapshot(guia)
        console = self._console_for(guia)

        console.write({GRID_FIELD: [
            (0, 'virtual_1', {'description': 'Manual A', 'pieces': 3}),
            (0, 'virtual_2', {'description': 'Manual B', 'pieces': 4}),
        ]})
        self.env.invalidate_all()
        console = self._console_for(guia)
        rows = console.declared_piece_line_ids
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows.mapped('origin'), ['manual', 'manual'])
        self.assertEqual(console.declared_lines_pieces, 7)
        self.assertEqual(self._documental_snapshot(guia), before)

        # Editar una fila manual: el detalle documental no cambia.
        console.write({GRID_FIELD: [(1, rows[0].id, {'pieces': 10})]})
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(console.declared_lines_pieces, 10 + 4)
        self.assertEqual(self._documental_snapshot(guia), before)

        # Eliminar la otra fila manual: el detalle documental no cambia.
        console.write({GRID_FIELD: [(2, rows[1].id, False)]})
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(len(console.declared_piece_line_ids), 1)
        self.assertEqual(console.declared_lines_pieces, 10)
        self.assertEqual(self._documental_snapshot(guia), before)
        self.assertEqual(len(self._guia(guia).volume_detail_line_ids), 14)



    # ── 4. Vaciar la grilla NUNCA borra las líneas documentales ───────────
    def test_04_quitar_filas_visibles_no_borra_documentales(self):
        """Vaciar la grilla (False, CLEAR o SET vacío) no borra pdf/excel."""
        guia = self._make_guia('VOL-GRID-FILTER-04')
        self._make_documental_detail(guia)
        before = self._documental_snapshot(guia)

        for label, empty_value in (
                ('lista vacía (False)', False),
                ('CLEAR (5,)', [(5,)]),
                ('SET vacío (6, 0, [])', [(6, 0, [])])):
            with self.subTest(form=label):
                console = self._console_for(guia)
                # Fila de cabecera (botón documental) + una fila manual.
                console.action_apply_declared_volume_suggestions()
                console.write({GRID_FIELD: [
                    (0, 'virtual_manual',
                     {'description': 'Manual', 'pieces': 3}),
                ]})
                self.env.invalidate_all()
                console = self._console_for(guia)
                self.assertEqual(
                    len(console.declared_piece_line_ids), 2,
                    'Dos filas visibles antes de vaciar la grilla')

                console.write({GRID_FIELD: empty_value})
                self.env.invalidate_all()
                console = self._console_for(guia)
                self.assertFalse(
                    console.declared_piece_line_ids,
                    'La grilla queda vacía con %s' % label)
                self.assertEqual(console.declared_lines_pieces, 0)
                # El inverse solo puede eliminar filas que la grilla proyecta.
                self.assertEqual(
                    self._documental_snapshot(guia), before,
                    'Las líneas pdf/excel no se borran al vaciar la grilla')
                self.assertEqual(
                    len(self._guia(guia).volume_detail_line_ids), 13,
                    'El detalle documental conserva sus 13 líneas')

    # ── 5. Agregados canónicos: 40.300 y 0.015 sin cambios ───────────────
    def test_05_agregados_canonicos_intactos(self):
        """La grilla declarada no altera `volume_detail_m3` ni la conciliación."""
        guia = self._make_guia('VOL-GRID-FILTER-05')
        self._make_documental_detail(guia)
        baseline = self._guia(guia)
        self.assertAlmostEqual(baseline.volume_detail_m3, 40.3, places=3)
        self.assertAlmostEqual(
            baseline.official_vs_detail_diff_m3, 0.015, places=3)
        self.assertAlmostEqual(baseline.official_volume_m3, 40.315, places=3)
        status = baseline.conciliation_status

        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        # Fila manual SIN volumen: la captura declarada no alimenta el detalle
        # documental (solo la fila de cabecera lleva el volumen oficial).
        console.write({GRID_FIELD: [
            (0, 'virtual_manual', {'description': 'Manual', 'pieces': 5}),
        ]})
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(len(console.declared_piece_line_ids), 2)
        console.action_apply_declared_volume_suggestions()
        self.env.invalidate_all()

        guia = self._guia(guia)
        self.assertAlmostEqual(guia.volume_detail_m3, 40.3, places=3)
        self.assertAlmostEqual(
            guia.official_vs_detail_diff_m3, 0.015, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)
        self.assertEqual(
            guia.conciliation_status, status,
            'La grilla declarada no altera la conciliación')
        self.assertEqual(guia.state, 'verified')
        self.assertEqual(guia.official_volume_source, 'Guía PDF')
        console = self._console_for(guia)
        self.assertAlmostEqual(
            console.declared_lines_volume_m3, 40.3, places=3)
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3, 0.015, places=3)
        self.assertEqual(
            console.declared_lines_pieces, 5 + 124,
            'Cabecera + fila manual (las documentales no se cuentan)')
        # Nada de stock, lotes SV ni pickings: la grilla es documental.
        self.assertFalse(guia.lot_ids)
        self.assertFalse(guia.volume_lot_id)
        self.assertFalse(guia.consumption_picking_id)

    # ── 6. Vista: inventario sin pérdidas y nueva disposición ─────────────
    def test_06_vista_inventario_y_disposicion(self):
        """Campos, botones y textos idénticos; 4 columnas de captura + grilla."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        groups = root.xpath("//group[@string='%s']" % DECLARED_GROUP)
        self.assertEqual(len(groups), 1, 'Falta el bloque declarado')
        group = groups[0]

        # Inventario COMPLETO de nodos: ni pérdidas ni duplicados.
        fields = [node.get('name') for node in group.iter('field')]
        self.assertEqual(sorted(fields), sorted(DECLARED_GROUP_FIELDS))
        button_names = sorted(node.get('name') for node in group.iter('button'))
        self.assertEqual(button_names, sorted(DECLARED_GROUP_BUTTONS))
        # Títulos exactos: no se agregó ningún bloque titulado nuevo.
        titled = sorted({node.get('string') for node in group.iter('group')
                         if node.get('string')})
        self.assertEqual(titled, sorted(DECLARED_GROUP_TITLES))
        # El volumen oficial vigente sigue encabezando el bloque (una vez).
        self.assertEqual(
            fields[0], 'official_volume_effective_m3',
            'El volumen oficial vigente debe seguir siendo el primero')
        for field_name in ('official_volume_effective_m3',
                           'official_volume_effective_source'):
            self.assertEqual(
                len(root.xpath("//field[@name='%s']" % field_name)), 1,
                'El campo %s debe mostrarse una sola vez' % field_name)

        # Fila de captura: los cuatro datos declarados juntos y editables, con
        # el botón documental, dentro de un grupo SIN título.
        captures = group.xpath("./group[@col='4']")
        self.assertEqual(len(captures), 1, 'Falta la fila de captura')
        capture = captures[0]
        self.assertFalse(
            capture.get('string'), 'La fila de captura no agrega título')
        self.assertFalse(
            capture.get('invisible'), 'La fila de captura debe ser visible')
        for field_name in CAPTURE_FIELDS:
            nodes = capture.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(
                len(nodes), 1,
                'Campo declarado %s ausente en la fila de captura'
                % field_name)
            self.assertFalse(
                nodes[0].get('readonly') in ('1', 'True', 'true'),
                'El campo declarado %s debe capturarse' % field_name)
        self.assertEqual(
            len(capture.xpath(".//button[@name='%s']"
                              % 'action_apply_declared_volume_suggestions')),
            1, 'El botón documental vive en la fila de captura')
        # Las sugerencias acompañan a su campo, no en columnas sueltas.
        for field_name in ('suggested_pieces', 'suggested_widths_text',
                           'suggested_lengths_text',
                           'suggested_thickness_text'):
            self.assertEqual(
                len(capture.xpath(".//field[@name='%s']" % field_name)), 1,
                'La sugerencia %s debe convivir con su campo' % field_name)

        # Grilla declarada a ancho completo, con sus columnas y estado vacío.
        grids = group.xpath(
            "./div[@colspan='2'][.//field[@name='%s']]" % GRID_FIELD)
        self.assertEqual(len(grids), 1, 'La grilla debe ir a ancho completo')
        grid = grids[0]
        self.assertEqual(
            len(grid.xpath(".//field[@name='declared_lines_pieces']")), 1)
        self.assertEqual(
            len(grid.xpath(".//field[@name='declared_piece_line_ids']")), 1)
        columns = [node.get('name') for node in grid.xpath('.//list/field')]
        self.assertEqual(columns, GRID_COLUMNS)
        empties = grid.xpath(".//div[@invisible='%s']" % GRID_FIELD)
        self.assertEqual(len(empties), 1, 'El estado vacío debe ser único')
        self.assertEqual(
            ' '.join((empties[0].text or '').split()), EMPTY_STATE)
        # Anchos y jerarquía: las columnas de captura declaran ancho fijo;
        # Descripción (la más ancha) absorbe el sobrante sin declararlo.
        widths = {node.get('name'): node.get('width')
                  for node in grid.xpath('.//list/field')}
        for column in ('line_no', 'material_code', 'pieces', 'width_declared',
                       'length_declared', 'thickness_declared', 'volume_m3',
                       'observation', 'origin', 'manually_adjusted'):
            self.assertTrue(
                widths.get(column),
                'La columna %s debe declarar su ancho fijo' % column)
        self.assertFalse(
            widths.get('description'),
            'Descripción absorbe el espacio sobrante (sin ancho fijo)')
        observation_width = int(
            (widths.get('observation') or '0').replace('px', ''))
        volume_width = int((widths.get('volume_m3') or '0').replace('px', ''))
        self.assertTrue(
            observation_width > volume_width,
            'Observación debe ser la segunda columna más ancha')

        # Descripción y Observación se leen con widget de texto (multilínea).
        for column in ('description', 'observation'):
            node = grid.xpath(".//list/field[@name='%s']" % column)[0]
            self.assertEqual(
                node.get('widget'), 'text',
                'La columna %s debe usar widget de texto' % column)

        # `open_form_view` habilita abrir cada fila en un formulario; el
        # formulario vive DENTRO del campo y replica la captura.
        self.assertEqual(
            grid.xpath(".//list")[0].get('open_form_view'), '1',
            'La grilla debe habilitar abrir la fila en su formulario')
        forms = grid.xpath(".//form")
        self.assertEqual(
            len(forms), 1, 'La grilla debe declarar su formulario de detalle')
        form_fields = [node.get('name') for node in forms[0].iter('field')]
        for field_name in GRID_FORM_FIELDS:
            self.assertIn(
                field_name, form_fields,
                'El formulario de detalle debe incluir %s' % field_name)
        for field_name in ('description', 'observation'):
            node = forms[0].xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('widget'), 'text',
                '%s debe ser multilínea en el formulario' % field_name)
        for field_name in ('origin', 'manually_adjusted'):
            node = forms[0].xpath(".//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('readonly'), '1',
                '%s debe ser solo lectura en el formulario' % field_name)

        # Pies etiquetados como DETALLE DOCUMENTAL DEL PDF/EXCEL.
        arch = ' '.join(etree.tostring(group, encoding='unicode').split())
        self.assertIn(DOCUMENTAL_VOLUME_LABEL, arch)
        self.assertIn(DOCUMENTAL_DIFF_LABEL, arch)
        self.assertIn(DOCUMENTAL_NOTE, arch)
        self.assertIn(
            'Piezas declaradas en líneas:', arch,
            'El contador de la grilla conserva su etiqueta')

        # Regla canónica del filtro expuesta por el modelo (fuente única).
        self.assertEqual(
            tuple(self.Console.DECLARED_PIECE_GRID_ORIGINS), VISIBLE_ORIGINS)

