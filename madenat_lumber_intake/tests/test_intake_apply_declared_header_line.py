# -*- coding: utf-8 -*-
"""«Aplicar datos documentales» agrega los datos de cabecera como UNA fila.

Contrato verificado (TransactionCase: nada se persiste; no se tocan guías,
lotes, pickings ni secuencias reales):

1. Cabecera declarada con datos + botón → aparece **1 fila** en la grilla con
   `pieces`, `width_declared`, `length_declared` y `thickness_declared`.
2. Idempotencia: pulsar el botón N veces deja **una sola** fila (se actualiza
   en el lugar); si cambia la cabecera, la misma fila se actualiza.
3. Cabecera sin datos declarados (piezas 0 y sólo las designaciones genéricas
   «RW»/«RL») → **no se crea** fila.
4. Una edición manual de la fila generada (`manually_adjusted=True`) **nunca**
   se sobrescribe al volver a pulsar el botón.
5. Guías en estado terminal (`validated`/`cancelled`): no se crea ni actualiza.
6. Las líneas del PDF no se tocan; el volumen oficial no cambia; la grilla
   proyecta solo la fila de cabecera y el contador «Piezas declaradas en
   líneas» es la suma de las filas VISIBLES (cabecera/manual).
7. Fase 4: la fila lleva el VOLUMEN OFICIAL VIGENTE en `volume_m3` sin doble
   conteo (los agregados del detalle documental excluyen `origin='header'`);
   la fila nace SOLO al pulsar el botón (no hay creación automática); y el
   orden vertical de la vista es volumen oficial → ETIQUETA SV → cabecera
   declarada + botón → grilla y totales.
8. Fase UX: la grilla proyecta SOLO las filas declaradas ('header'/'manual').
   Las líneas documentales del PDF/Excel no se muestran en ella (siguen
   intactas en el detalle/Packing) y la consola nunca las elimina.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
SV_GROUP = 'ETIQUETA SV'
HEADER_ORIGIN = 'header'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeApplyDeclaredHeaderLine(TransactionCase):
    """Fila única de cabecera declarada generada por el botón documental."""

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
            'name': 'Proveedor Cabecera Declarada', 'is_company': True})

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

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id)], limit=1)

    def _header_lines(self, guia):
        self.env.invalidate_all()
        return self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda line: line.origin == HEADER_ORIGIN)

    def _guia_with_header_data(self, name, state='verified'):
        return self._make_guia(
            name, state=state,
            piezas_declaradas=124,
            anchos_variables='RW / 4 1/2 - 6 1/4',
            largos_variables='RL / 8 - 12',
            espesor_nominal_texto='7/4',
        )

    # ── 1. Cabecera con datos → una fila con los cuatro valores ───────────
    def test_01_boton_crea_fila_de_cabecera(self):
        """El botón refleja la cabecera declarada como una fila de la grilla."""
        guia = self._guia_with_header_data('VOL-HEADER-01')
        console = self._console_for(guia)
        self.assertTrue(console)

        console.action_apply_declared_volume_suggestions()

        lines = self._header_lines(guia)
        self.assertEqual(len(lines), 1, 'Debe aparecer exactamente una fila')
        self.assertEqual(lines.origin, HEADER_ORIGIN)
        self.assertEqual(lines.pieces, 124)
        self.assertEqual(lines.width_declared, 'RW / 4 1/2 - 6 1/4')
        self.assertEqual(lines.length_declared, 'RL / 8 - 12')
        self.assertEqual(lines.thickness_declared, '7/4')
        self.assertFalse(
            lines.manually_adjusted,
            'Un reflejo de cabecera no es un ajuste manual del operador')
        self.assertEqual(
            lines.source_line_no, 0,
            'No proviene de una línea documental del PDF/Excel')
        guia = self.Guia.browse(guia.id)
        self.assertEqual(guia.piezas_declaradas, 124)
        self.assertEqual(guia.anchos_variables, 'RW / 4 1/2 - 6 1/4')

    # ── 2. Idempotencia ───────────────────────────────────────────────────
    def test_02_boton_dos_veces_no_duplica_y_actualiza(self):
        """Pulsar N veces mantiene una fila; si cambia la cabecera, se actualiza."""
        guia = self._guia_with_header_data('VOL-HEADER-02')
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        first = self._header_lines(guia)
        self.assertEqual(len(first), 1)

        for _index in range(3):
            self._console_for(guia).action_apply_declared_volume_suggestions()
        lines = self._header_lines(guia)
        self.assertEqual(len(lines), 1, 'Nunca se duplica la fila')
        self.assertEqual(lines.id, first.id, 'Se actualiza en el lugar')
        self.assertEqual(lines.pieces, 124)

        self.Guia.browse(guia.id).write({
            'piezas_declaradas': 150,
            'espesor_nominal_texto': '8/4',
        })
        self._console_for(guia).action_apply_declared_volume_suggestions()
        lines = self._header_lines(guia)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.id, first.id)
        self.assertEqual(lines.pieces, 150)
        self.assertEqual(lines.thickness_declared, '8/4')

    # ── 3. Cabecera vacía → no crea fila ──────────────────────────────────
    def test_03_cabecera_vacia_no_crea_fila(self):
        """Sin datos declarados (sólo placeholders RW/RL) no se crea fila."""
        guia = self._make_guia('VOL-HEADER-03')
        self.assertFalse(guia.piezas_declaradas)
        self.assertFalse(guia.anchos_variables)
        console = self._console_for(guia)

        console.action_apply_declared_volume_suggestions()

        self.assertFalse(
            self._header_lines(guia),
            'Una cabecera sin datos declarados no genera fila en la grilla')
        guia = self.Guia.browse(guia.id)
        self.assertEqual(guia.anchos_variables, 'RW')
        self.assertEqual(guia.largos_variables, 'RL')
        self._console_for(guia).action_apply_declared_volume_suggestions()
        self.assertFalse(self._header_lines(guia))

    # ── 4. Edición manual protegida ───────────────────────────────────────
    def test_04_edicion_manual_no_se_sobrescribe(self):
        """La fila editada a mano conserva la corrección al pulsar de nuevo."""
        guia = self._guia_with_header_data('VOL-HEADER-04')
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        line = self._header_lines(guia)
        self.assertEqual(line.pieces, 124)

        # Corrección del operador (como desde la grilla de la consola).
        line.write({'pieces': 999, 'width_declared': 'RW corregido'})
        self.env.invalidate_all()
        line = self.Guia.browse(guia.id).volume_detail_line_ids.filtered(
            lambda row: row.origin == HEADER_ORIGIN)
        self.assertEqual(line.pieces, 999)
        self.assertTrue(line.manually_adjusted)

        # Nuevo «Aplicar datos documentales»: la corrección persiste.
        self._console_for(guia).action_apply_declared_volume_suggestions()
        lines = self._header_lines(guia)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.pieces, 999)
        self.assertEqual(lines.width_declared, 'RW corregido')
        self.assertTrue(lines.manually_adjusted)

    # ── 5. Estados terminales: no crea ni actualiza ───────────────────────
    def test_05_estados_terminales_no_crean_fila(self):
        """Guias validadas o canceladas: el botón no agrega fila de cabecera."""
        for state in ('validated', 'cancelled'):
            guia = self._guia_with_header_data(
                'VOL-HEADER-%s' % state.upper(), state=state)
            console = self._console_for(guia)
            self.assertTrue(console)
            console.action_apply_declared_volume_suggestions()
            self.assertFalse(
                self._header_lines(guia),
                'En estado %s no debe crearse la fila de cabecera' % state)

        # Con una fila ya existente, el estado terminal tampoco la actualiza.
        guia = self._guia_with_header_data('VOL-HEADER-TERM')
        self._console_for(guia).action_apply_declared_volume_suggestions()
        line = self._header_lines(guia)
        self.assertEqual(line.pieces, 124)
        self.Guia.browse(guia.id).write({
            'state': 'validated', 'piezas_declaradas': 300})
        self._console_for(guia).action_apply_declared_volume_suggestions()
        self.assertEqual(
            self._header_lines(guia).pieces, 124,
            'En estado terminal la fila existente no se modifica')

    # ── 6. Coherencia: PDF, volumen oficial y contador ────────────────────
    def test_06_no_toca_pdf_ni_volumen_ni_contador(self):
        """Las líneas del PDF, el volumen oficial y el contador quedan coherentes."""
        guia = self._guia_with_header_data('VOL-HEADER-06')
        pdf_line = self.Line.create({
            'guia_id': guia.id, 'origin': 'pdf', 'source_line_no': 1,
            'description': 'Línea del PDF', 'volume_m3': 40.3, 'pieces': 7,
        })
        console = self._console_for(guia)
        self.assertFalse(
            console.declared_piece_line_ids,
            'La grilla declarada no proyecta la línea documental del PDF')

        console.action_apply_declared_volume_suggestions()

        guia = self.Guia.browse(guia.id)
        pdf_line = self.Line.browse(pdf_line.id)
        self.assertEqual(pdf_line.pieces, 7, 'La línea del PDF no se toca')
        self.assertEqual(pdf_line.origin, 'pdf')
        self.assertAlmostEqual(pdf_line.volume_m3, 40.3, places=3)
        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertEqual(guia.official_volume_source, 'Guía PDF')
        self.assertEqual(guia.state, 'verified')
        # El contador suma SOLO las filas visibles de la grilla (la cabecera):
        # las 7 piezas documentales del PDF no forman parte de la grilla.
        console = self._console_for(guia)
        self.assertEqual(console.declared_lines_pieces, 124)
        self.assertEqual(len(console.declared_piece_line_ids), 1)
        self.assertEqual(console.declared_piece_line_ids.origin, HEADER_ORIGIN)

    # ── 7. Volumen oficial en la fila, sin doble conteo ───────────────────
    def test_07_fila_lleva_volumen_oficial_sin_doble_conteo(self):
        """La fila registra `volume_m3` = volumen oficial vigente."""
        guia = self._guia_with_header_data('VOL-HEADER-07')
        self.Line.create({
            'guia_id': guia.id, 'origin': 'pdf', 'source_line_no': 1,
            'description': 'Detalle del PDF', 'volume_m3': 40.3,
        })
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()

        guia = self.Guia.browse(guia.id)
        line = self._header_lines(guia)
        self.assertEqual(len(line), 1)
        self.assertAlmostEqual(line.volume_m3, 40.315, places=3)
        self.assertEqual(line.pieces, 124)
        # Anti doble conteo: los agregados del detalle documental excluyen la
        # fila de cabecera (su volumen ES el oficial).
        self.assertAlmostEqual(guia.volume_detail_m3, 40.3, places=3)
        self.assertAlmostEqual(
            guia.official_vs_detail_diff_m3, 0.015, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        console = self._console_for(guia)
        self.assertAlmostEqual(
            console.declared_lines_volume_m3, 40.3, places=3)
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3, 0.015, places=3)
        self.assertEqual(console.declared_lines_pieces, 124)

    def test_08_sin_fila_prematura_antes_de_aplicar(self):
        """Abrir/leer/guardar la ficha NO crea la fila de cabecera."""
        guia = self._guia_with_header_data('VOL-HEADER-08')
        console = self._console_for(guia)
        self.assertEqual(len(console.declared_piece_line_ids), 0)
        console.write({
            'declared_pieces': 124,
            'declared_widths_text': 'RW / 4 1/2 - 6 1/4',
        })
        self.assertEqual(len(self._header_lines(guia)), 0)
        self.assertEqual(
            len(self._console_for(guia).declared_piece_line_ids), 0)
        self.assertFalse(
            guia.volume_detail_line_ids,
            'Ninguna fila existe antes de pulsar «Aplicar datos documentales»')

    def test_09_piezas_declaradas_es_campo_de_captura(self):
        """`declared_pieces` es editable (mismo criterio que RW/RL/espesor)."""
        guia = self._make_guia('VOL-HEADER-09')
        fields = self.Console.fields_get(
            ['declared_pieces', 'declared_widths_text',
             'declared_lengths_text', 'declared_thickness_text'],
            ['readonly', 'type'])
        for name in fields:
            self.assertFalse(
                fields[name]['readonly'],
                '%s debe ser editable en la cabecera' % name)

        console = self._console_for(guia)
        console.write({
            'declared_pieces': 124,
            'declared_widths_text': 'RW / 4 1/2',
            'declared_lengths_text': 'RL / 10',
            'declared_thickness_text': '7/4',
        })
        guia = self.Guia.browse(guia.id)
        self.assertEqual(guia.piezas_declaradas, 124)
        self.assertEqual(guia.anchos_variables, 'RW / 4 1/2')
        self.assertEqual(guia.largos_variables, 'RL / 10')
        self.assertEqual(guia.espesor_nominal_texto, '7/4')
        console.action_apply_declared_volume_suggestions()
        line = self._header_lines(guia)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.pieces, 124)
        self.assertEqual(line.width_declared, 'RW / 4 1/2')

    def test_10_volumen_oficial_cambiado_actualiza_la_fila(self):
        """Cambiar el volumen oficial y reapuntar actualiza la MISMA fila."""
        guia = self._guia_with_header_data('VOL-HEADER-10')
        console = self._console_for(guia)
        console.action_apply_declared_volume_suggestions()
        first = self._header_lines(guia)
        self.assertAlmostEqual(first.volume_m3, 40.315, places=3)

        self.Guia.browse(guia.id).write({'volume_pdf_m3': 50.0})
        self._console_for(guia).action_apply_declared_volume_suggestions()
        lines = self._header_lines(guia)
        self.assertEqual(len(lines), 1, 'Nunca se duplica')
        self.assertEqual(lines.id, first.id, 'Se actualiza en el lugar')
        self.assertAlmostEqual(lines.volume_m3, 50.0, places=3)

    # ── 8. Orden vertical de la vista ─────────────────────────────────────
    def test_11_orden_vertical_volumen_sv_cabecera_grilla(self):
        """Vista: volumen oficial → ETIQUETA SV → cabecera+botón → grilla."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)

        groups = [group.get('string') for group in root.iter('group')
                  if group.get('string')]
        self.assertLess(
            groups.index(DECLARED_GROUP), groups.index(SV_GROUP),
            'ETIQUETA SV debe quedar después de DATOS DECLARADOS')
        visible_order = [title for title in (
            'DATOS DE LA GUÍA', DECLARED_GROUP, SV_GROUP)
            if title in groups]
        self.assertEqual(
            visible_order, ['DATOS DE LA GUÍA', DECLARED_GROUP, SV_GROUP])

        declared = root.xpath("//group[@string='%s']" % DECLARED_GROUP)[0]
        names = []
        for node in declared.iter():
            if node.tag in ('field', 'button') and node.get('name'):
                names.append(node.get('name'))
            elif node.tag == 'group' and node.get('string'):
                names.append('GRP:%s' % node.get('string'))
        position = {name: index for index, name in enumerate(names)}
        expected = [
            'official_volume_effective_m3',
            'GRP:%s' % SV_GROUP,
            'declared_pieces',
            'declared_widths_text',
            'declared_lengths_text',
            'declared_thickness_text',
            'action_apply_declared_volume_suggestions',
            'declared_lines_pieces',
            'declared_piece_line_ids',
            'declared_lines_volume_m3',
            'declared_lines_vs_official_m3',
        ]
        for index in range(len(expected) - 1):
            self.assertLess(
                position[expected[index]], position[expected[index + 1]],
                '%s debe ir antes de %s' % (expected[index],
                                           expected[index + 1]))

        # El bloque SV conserva sus dos estados y no duplica nodos.
        self.assertEqual(
            len(declared.xpath(".//group[@string='%s']" % SV_GROUP)), 2)
        self.assertEqual(
            len(root.xpath(".//field[@name='sv_lot_label']")), 1)
        self.assertEqual(
            len(root.xpath(".//field[@name='declared_piece_line_ids']")), 1)
        # El nodo del placeholder SV y su etiqueta estimada se conservan.
        self.assertEqual(
            len(root.xpath(
                ".//div[@invisible='declared_sv_lot_id']")), 1)
        self.assertEqual(
            len(root.xpath(".//field[@name='sv_next_label_estimate']")), 1)
