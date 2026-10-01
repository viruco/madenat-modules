# -*- coding: utf-8 -*-
"""«Piezas Declaradas»: grilla one2many del detalle declarado (Volumen).

Contrato verificado (TransactionCase: nada se persiste; no toca guías reales,
lotes, pickings ni secuencias):

1. Vista: el bloque «DATOS DECLARADOS DE LA GUÍA» conserva su encabezado
   (volumen oficial vigente primero), sus datos declarados editables y el
   placeholder de la etiqueta SV, y suma UNA grilla one2many
   (`declared_piece_line_ids`) visible, editable y con las columnas aprobadas.
2. Estado vacío: sin líneas declaradas se muestra el mensaje pedido; la grilla
   sigue visible (no se crean registros ficticios).
3. Captura: agregar, editar y eliminar filas MANUALES desde la consola se
   refleja en el detalle real de la Guía; el contador «Piezas declaradas en
   líneas» es la SUMA de las piezas de las filas VISIBLES de la grilla
   (cabecera declarada + filas manuales).
4. Totales: el volumen del detalle documental y su diferencia contra el volumen
   oficial son informativos y no alteran el volumen oficial de la Guía.
5. «Aplicar datos documentales» conserva su comportamiento: es idempotente y
   NUNCA duplica ni borra líneas del detalle.
6. Estados terminales (`validated`, `cancelled`): la grilla queda en solo
   lectura en la vista y el modelo rechaza la escritura.
7. Fuera de Volumen (Producto/Procesado) la grilla queda vacía y no escribe.
8. Fase UX: la grilla proyecta SOLO las filas declaradas ('header'/'manual').
   Las filas documentales del PDF/Excel NO se muestran aquí: siguen intactas en
   `volume_detail_line_ids` (pestaña Packing de la fachada) y la consola NUNCA
   las borra, escribe ni re-vincula.
"""

from lxml import etree

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
GRID_FIELD = 'declared_piece_line_ids'
GRID_COLUMNS = [
    'line_no',
    'material_code',
    'description',
    'pieces',
    'width_declared',
    'length_declared',
    'thickness_declared',
    'volume_m3',
    'observation',
    'origin',
    # Columna de trazabilidad agregada en Fase 2 (dato documental vs. ajuste
    # manual del operador): campo existente, solo lectura.
    'manually_adjusted',
]
EMPTY_STATE = ('Sin piezas declaradas. Use «Agregar ítem» o «Aplicar datos '
               'documentales» para comenzar.')
DOCUMENTAL_NOTE = ('El detalle de piezas es documental y no reemplaza el '
                   'volumen oficial de la guía.')
READONLY_EXPRESSION = "state in ('validated', 'cancelled')"


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredPiecesGrid(TransactionCase):
    """Grilla declarada de piezas: vista, captura, totales y solo lectura."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.lumber.volume.detail.line']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Piezas Declaradas', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _root(self):
        return etree.fromstring(self.env.ref(CONSOLE_FORM).arch)

    def _declared_group(self, root):
        groups = root.xpath("//group[@string='%s']" % DECLARED_GROUP)
        self.assertEqual(len(groups), 1, 'Falta el bloque declarado')
        return groups[0]

    def _make_guia(self, name, tipo='granel', **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo,
            'state': 'verified',
            'date_emission': '2026-09-24',
            'volume_pdf_m3': 10.0,
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

    def _grid_rows(self, guia):
        return (self.Guia.browse(guia.id).volume_detail_line_ids
                .sorted(key=lambda l: (l.source_line_no, l.id)))

    # ── 1. Contrato de vista del bloque declarado ─────────────────────────
    def test_01_vista_grilla_declarada_unica_y_editable(self):
        """La grilla declarada es única, visible y editable con sus columnas."""
        group = self._declared_group(self._root())

        nodes = group.xpath(".//field[@name='%s']" % GRID_FIELD)
        self.assertEqual(
            len(nodes), 1, 'Debe existir una sola grilla declarada')
        node = nodes[0]
        self.assertFalse(
            node.get('invisible'),
            'La grilla declarada debe quedar visible en Volumen')
        self.assertEqual(
            node.get('readonly'), READONLY_EXPRESSION,
            'La grilla debe ser solo lectura en estados terminales')

        lists = node.xpath('.//list')
        self.assertEqual(len(lists), 1)
        self.assertEqual(lists[0].get('editable'), 'bottom')
        columns = [f.get('name') for f in lists[0].xpath('./field')]
        self.assertEqual(columns, GRID_COLUMNS)
        self.assertEqual(
            lists[0].xpath("./field[@name='line_no']")[0].get('readonly'), '1',
            'El correlativo de fila es informativo (solo lectura)')
        self.assertEqual(
            lists[0].xpath("./field[@name='origin']")[0].get('readonly'), '1',
            'El origen documental/manual es evidencia (solo lectura)')

    def test_02_vista_conserva_bloque_declarado(self):
        """El resto del bloque declarado permanece intacto y en su orden."""
        group = self._declared_group(self._root())

        declared_fields = [f.get('name') for f in group.xpath('.//field')]
        self.assertEqual(
            declared_fields[0], 'official_volume_effective_m3',
            'El volumen oficial vigente debe seguir siendo el primer campo')

        for field_name in ('declared_pieces', 'declared_widths_text',
                           'declared_lengths_text', 'declared_thickness_text',
                           'declared_sv_lot_id', 'suggested_pieces',
                           'suggested_widths_text', 'suggested_lengths_text',
                           'suggested_thickness_text'):
            self.assertEqual(
                len(group.xpath(".//field[@name='%s']" % field_name)), 1,
                'Campo declarado %s ausente o duplicado' % field_name)

        for field_name in ('declared_pieces', 'declared_widths_text',
                           'declared_lengths_text', 'declared_thickness_text'):
            node = group.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertFalse(
                node.get('readonly') in ('1', 'True', 'true'),
                'El campo declarado %s debe seguir editable' % field_name)

        buttons = group.xpath(
            ".//button[@name='action_apply_declared_volume_suggestions']")
        self.assertEqual(len(buttons), 1)
        placeholders = group.xpath(".//div[@invisible='declared_sv_lot_id']")
        self.assertEqual(len(placeholders), 1)
        self.assertIn(
            'Se asignará al enviar a stock', placeholders[0].text or '')

        # La grilla declarada no introduce grupos con título nuevos: los únicos
        # grupos titulados del bloque son los preexistentes (el bloque
        # «ETIQUETA SV» se movió DENTRO del bloque declarado en la Fase 4, por
        # orden vertical: volumen oficial → ETIQUETA SV → datos → grilla).
        titled = sorted({g.get('string') for g in group.iter('group')
                         if g.get('string')})
        self.assertEqual(titled, [
            'DATOS DECLARADOS DE LA GUÍA',
            'ETIQUETA SV',
            'Volumen operativo de referencia (no gobierna stock)',
        ])

    def test_03_vista_totales_y_estado_vacio(self):
        """Totales informativos y estado vacío presentes una sola vez."""
        group = self._declared_group(self._root())

        for field_name in ('declared_lines_pieces',
                           'declared_lines_volume_m3',
                           'declared_lines_vs_official_m3'):
            nodes = group.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(len(nodes), 1, 'Falta el total %s' % field_name)
            self.assertEqual(
                nodes[0].get('readonly'), '1',
                'El total %s debe ser de solo lectura' % field_name)

        empties = group.xpath(".//div[@invisible='%s']" % GRID_FIELD)
        self.assertEqual(len(empties), 1, 'Falta el estado vacío de la grilla')
        text = ' '.join((empties[0].text or '').split())
        self.assertEqual(text, EMPTY_STATE)

        arch = ' '.join(
            etree.tostring(group, encoding='unicode').split())
        self.assertIn(DOCUMENTAL_NOTE, arch)

    # ── 2. Guía sin líneas: estado vacío y formulario operativo ───────────
    def test_04_guia_sin_lineas_estado_vacio(self):
        """Sin líneas: grilla vacía, contador 0 y totales coherentes."""
        guia = self._make_guia('VOL-PIEZAS-VACIA')
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')

        self.assertFalse(
            console.declared_piece_line_ids,
            'Sin detalle documental la grilla debe quedar vacía')
        self.assertEqual(console.declared_lines_pieces, 0)
        self.assertEqual(console.declared_lines_volume_m3, 0.0)
        self.assertEqual(console.declared_pieces, 0)
        self.assertEqual(console.declared_sv_lot_id, self.StockLot.browse())
        # La diferencia informativa es el espejo del cálculo canónico de la
        # Guía (volumen oficial − suma del detalle), nunca un cálculo paralelo.
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3,
            self.Guia.browse(guia.id).official_vs_detail_diff_m3, places=3)
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3, 10.0, places=3)

    # ── 3. Captura: crear, editar y eliminar ─────────────────────────────
    def test_05_captura_agregar_editar_eliminar(self):
        """El contador es la SUMA de piezas capturadas, no el número de filas."""
        guia = self._make_guia('VOL-PIEZAS-CAPTURA')
        console = self._console_for(guia)

        # Agregar dos líneas con los comandos reales de la grilla editable.
        console.write({GRID_FIELD: [
            (0, 'virtual_1', {
                'material_code': 'C-1',
                'description': 'Tabla 1',
                'pieces': 3,
                'volume_m3': 1.5,
                'width_declared': 'RW 4 1/2',
            }),
            (0, 'virtual_2', {
                'material_code': 'C-2',
                'description': 'Tabla 2',
                'pieces': 4,
                'volume_m3': 2.5,
            }),
        ]})
        rows = self._grid_rows(guia)
        self.assertEqual(len(rows), 2, 'Deben existir dos líneas capturadas')
        self.assertEqual(
            rows.mapped('origin'), ['manual', 'manual'],
            'Las filas creadas desde la consola son captura manual')
        self.assertEqual(rows.mapped('pieces'), [3, 4])
        self.assertEqual(rows.mapped('line_no'), [1, 2])
        self.assertEqual(rows[0].width_declared, 'RW 4 1/2')
        console = self._console_for(guia)
        self.assertEqual(console.declared_lines_pieces, 7)
        self.assertAlmostEqual(console.declared_lines_volume_m3, 4.0, places=3)

        # Editar una línea: el contador se recalcula (suma, no número de filas).
        first = self._grid_rows(guia)[0]
        console.write({GRID_FIELD: [(1, first.id, {'pieces': 10})]})
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(console.declared_lines_pieces, 14)
        self.assertEqual(len(self._grid_rows(guia)), 2)

        # Eliminar una línea: el detalle y los totales se actualizan.
        second = self._grid_rows(guia)[1]
        console.write({GRID_FIELD: [(2, second.id, False)]})
        self.env.invalidate_all()
        rows = self._grid_rows(guia)
        self.assertEqual(len(rows), 1, 'La línea eliminada debe desaparecer')
        console = self._console_for(guia)
        self.assertEqual(console.declared_lines_pieces, 10)
        self.assertAlmostEqual(console.declared_lines_volume_m3, 1.5, places=3)
        self.assertEqual(rows.mapped('line_no'), [1])

    def test_06_piezas_negativas_rechazadas(self):
        """Una cantidad negativa de piezas se rechaza con ValidationError."""
        guia = self._make_guia('VOL-PIEZAS-NEG')
        console = self._console_for(guia)
        with self.assertRaises(ValidationError):
            console.write({GRID_FIELD: [
                (0, 'virtual_neg', {'description': 'Inválida', 'pieces': -1}),
            ]})

    # ── 4. Totales informativos: no cambian el volumen oficial ni stock ───
    def test_07_totales_informativos_sin_efectos(self):
        """Los totales de líneas no alteran volumen oficial, stock ni chatter."""
        guia = self._make_guia('VOL-PIEZAS-TOTALES', volume_pdf_m3=40.315)
        console = self._console_for(guia)
        console.write({GRID_FIELD: [
            (0, 'virtual_1', {'description': 'Fila A', 'pieces': 2,
                              'volume_m3': 3.0}),
        ]})
        self.env.invalidate_all()
        guia = self.Guia.browse(guia.id)
        console = self._console_for(guia)

        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)
        self.assertAlmostEqual(
            console.official_volume_effective_m3, 40.315, places=3)
        self.assertEqual(console.official_volume_effective_source, 'Guía PDF')
        self.assertAlmostEqual(
            console.declared_lines_volume_m3, 3.0, places=3)
        self.assertAlmostEqual(
            console.declared_lines_vs_official_m3, 37.315, places=3)
        self.assertEqual(console.declared_lines_pieces, 2)

        # El volumen oficial NO se reemplaza por la suma de líneas.
        self.assertAlmostEqual(
            self.Guia.browse(guia.id).official_volume_m3, 40.315, places=3)
        # La captura no toca lotes SV, movimientos de stock, estado ni chatter.
        self.assertFalse(guia.lot_ids)
        self.assertFalse(guia.volume_lot_id)
        self.assertFalse(guia.consumption_picking_id)
        self.assertFalse(guia.processing_line_ids)
        self.assertEqual(guia.state, 'verified')
        self.assertEqual(console.state, 'verified')

    # ── 5. «Aplicar datos documentales» sigue siendo idempotente ──────────
    def test_08_aplicar_datos_documentales_no_duplica_ni_borra(self):
        """Dos pulsaciones del botón no duplican ni borran líneas declaradas."""
        guia = self._make_guia('VOL-PIEZAS-IDEMP', volume_pdf_m3=12.5)
        self.Line.create([
            {'guia_id': guia.id, 'description': 'Doc 1', 'volume_m3': 6.0,
             'pieces': 5, 'source_line_no': 1, 'origin': 'pdf'},
            {'guia_id': guia.id, 'description': 'Doc 2', 'volume_m3': 6.5,
             'pieces': 7, 'source_line_no': 2, 'origin': 'pdf'},
        ])
        guia.write({'anchos_variables': 'RW manual'})
        self.env.invalidate_all()

        def snapshot():
            rows = self._grid_rows(guia)
            return sorted(rows.ids), sorted(rows.mapped('pieces'))

        console = self._console_for(guia)
        before_ids, before_pieces = snapshot()
        messages_before = self.env['mail.message'].search_count([
            ('model', '=', 'madenat.guia.processing'), ('res_id', '=', guia.id),
        ])
        lots_before = self.StockLot.search_count([('lot_flow_type', '=', 'volume')])

        console.action_apply_declared_volume_suggestions()
        console.action_apply_declared_volume_suggestions()
        self.env.invalidate_all()

        rows = self._grid_rows(guia)
        documental = rows.filtered(lambda line: line.origin == 'pdf')
        header_rows = rows.filtered(lambda line: line.origin == 'header')
        self.assertEqual(
            sorted(documental.ids), before_ids,
            'El botón no debe duplicar ni borrar las líneas documentales')
        self.assertEqual(
            sorted(documental.mapped('pieces')), before_pieces,
            'Las piezas documentales no se alteran')
        self.assertEqual(
            len(header_rows), 1,
            'El botón refleja la cabecera declarada en UNA sola fila (Fase 3)')
        console = self._console_for(guia)
        self.assertEqual(
            len(console.declared_piece_line_ids), 1,
            'La grilla proyecta SOLO la fila de cabecera declarada')
        self.assertEqual(
            console.declared_lines_pieces, sum(header_rows.mapped('pieces')),
            'El contador suma solo las piezas de las filas VISIBLES de la '
            'grilla (cabecera/manual): las piezas documentales del PDF no se '
            'cuentan aquí')
        # Nunca sobrescribe un dato declarado por el operador.
        self.assertEqual(
            self.Guia.browse(guia.id).anchos_variables, 'RW manual')
        self.assertEqual(
            self.StockLot.search_count([('lot_flow_type', '=', 'volume')]),
            lots_before, 'El botón no debe crear lotes SV')
        self.assertEqual(
            self.env['mail.message'].search_count([
                ('model', '=', 'madenat.guia.processing'),
                ('res_id', '=', guia.id)]),
            messages_before, 'El botón no debe escribir chatter')

    # ── 6. Estados terminales: solo lectura ───────────────────────────────
    def test_09_estados_terminales_solo_lectura(self):
        """Validada o cancelada: la grilla es visible pero no editable."""
        for state in ('validated', 'cancelled'):
            guia = self._make_guia(
                'VOL-PIEZAS-%s' % state.upper(), state=state)
            self.Line.create({
                'guia_id': guia.id, 'description': 'Doc', 'volume_m3': 2.0,
                'pieces': 4, 'origin': 'pdf', 'source_line_no': 1})
            self.env.invalidate_all()
            console = self._console_for(guia)
            self.assertTrue(
                console, 'La consola debe seguir exponiendo la guía %s' % state)
            self.assertFalse(
                console.declared_piece_line_ids,
                'La grilla declarada NO proyecta las filas documentales del PDF '
                '(origen pdf/excel): solo cabecera declarada y filas manuales')
            self.assertEqual(console.declared_lines_pieces, 0)

            with self.assertRaises(UserError):
                console.write({GRID_FIELD: [
                    (0, 'virtual_%s' % state,
                     {'description': 'No permitida', 'pieces': 1}),
                ]})
            self.env.invalidate_all()
            self.assertEqual(
                len(self._grid_rows(guia)), 1,
                'La guía en estado %s no admite nuevas líneas' % state)

    # ── 7. Lectura inmediata (misma transacción, como `web_save`) ─────────
    def test_10_lectura_inmediata_tras_guardar(self):
        """Tras guardar, la grilla ya apunta a las filas persistidas."""
        guia = self._make_guia('VOL-PIEZAS-READ-INMEDIATO')
        console = self._console_for(guia)

        # Crear: la lectura inmediata (sin invalidar caché) ve la fila real,
        # nunca un identificador virtual del cliente.
        console.write({GRID_FIELD: [
            (0, 'virtual_1', {'description': 'Fila', 'pieces': 2})]})
        self.assertEqual(
            console.read([GRID_FIELD])[0][GRID_FIELD],
            [self._grid_rows(guia).id],
            'La lectura inmediata debe devolver la fila persistida')
        self.assertFalse(
            console.declared_piece_line_ids.filtered(
                lambda line: not line._origin),
            'La grilla no debe conservar registros sin guardar')
        self.assertEqual(console.declared_lines_pieces, 2)

        # Editar y eliminar: misma garantía de lectura inmediata.
        row = self._grid_rows(guia)
        console.write({GRID_FIELD: [(1, row.id, {'pieces': 5})]})
        self.assertEqual(console.declared_lines_pieces, 5)
        console.write({GRID_FIELD: [(2, row.id, False)]})
        self.assertEqual(
            console.read([GRID_FIELD])[0][GRID_FIELD], [],
            'Tras eliminar, la lectura inmediata debe quedar vacía')
        self.assertEqual(self._grid_rows(guia), self.Line.browse())

    # ── 8. Fuera de Volumen: grilla vacía y sin escritura ─────────────────
    def test_11_fuera_de_volumen_sin_efectos(self):
        """Producto/Procesado: grilla vacía y ninguna escritura al origen."""
        guia = self._make_guia('PIEZAS-COMPRA', tipo='compra')
        self.Line.create({
            'guia_id': guia.id, 'description': 'No es volumen',
            'volume_m3': 1.0, 'pieces': 3})
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(console.ingestion_type, 'processed')
        self.assertFalse(console.declared_piece_line_ids)
        self.assertEqual(console.declared_lines_pieces, 0)

        console.write({GRID_FIELD: [
            (0, 'virtual_x', {'description': 'Fantasma', 'pieces': 9}),
        ]})
        self.env.invalidate_all()
        rows = self._grid_rows(guia)
        self.assertEqual(len(rows), 1, 'No debe crear líneas fuera de Volumen')
        self.assertEqual(rows.pieces, 3, 'La línea existente no debe cambiar')
