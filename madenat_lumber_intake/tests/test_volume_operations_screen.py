# -*- coding: utf-8 -*-
"""Contrato aislado de la pantalla operativa de Volumen (Fase 2).

Este archivo es el contrato explícito y AUTÓNOMO de la pantalla simplificada de
Ingreso por Volúmenes: verifica qué queda visible y qué queda retirado, sin
depender de los contratos de jerarquía o comportamiento de otros archivos.

1. Para `ingestion_type == 'volume'` existen EXACTAMENTE los tres bloques de D3
   («DATOS DE LA GUÍA», «DATOS DECLARADOS DE LA GUÍA» y «ETIQUETA SV») y ningún
   bloque adicional visible.
2. Ausencia VISIBLE (los nodos siguen existiendo en el XML, nunca se eliminan)
   de: conciliación, control documental interno, sumatorias del packing,
   indicadores de encabezado, fila de evidencia PDF/Excel y campos operativos de
   referencia.
3. El volumen oficial vigente se muestra UNA SOLA VEZ, con su fuente y su botón
   «Modificar volumen oficial».
4. `declared_pieces` muestra el valor real de la Guía, incluido el caso 0 (que
   no debe interpretarse como «campo vacío»).

Solo inspecciona XML de vista y proxies de solo lectura: no crea pickings, lotes
de stock, movimientos ni secuencias.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DATOS_GUIA_GROUP = 'DATOS DE LA GUÍA'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
SV_GROUP = 'ETIQUETA SV'
VISIBLE_TITLES = [DATOS_GUIA_GROUP, DECLARED_GROUP, SV_GROUP]
ALL_INGESTION_TYPES = ('product', 'processed', 'volume')
VOLUME_CONDITION = "ingestion_type == 'volume'"

# Bloques que no pueden quedar visibles en la pantalla operativa de Volumen.
RETIRED_TITLES = (
    'VOLUMEN OFICIAL DE LA GUÍA',
    'Volumen operativo de referencia (no gobierna stock)',
    'Control documental interno (auditoría)',
    'Resumen del ingreso',
    'Evidencia documental',
    '📄 Evidencia documental',
    'DETALLE DEL PACKING LIST',
)
# Nodos que deben seguir existiendo pero sin quedar visibles en Volumen.
RETIRED_FIELDS = (
    'volume_detail_m3',
    'official_vs_detail_diff_m3',
    'conciliation_status',
    'conciliation_summary',
    'conciliation_manual_note',
    'declared_volume_m3',
    'volume_operational_m3',
    'volume_operational_source',
    'volume_operational_note',
    'total_lots',
    'total_amount',
    'total_volume_m3',
    'packing_volume_total',
    'review_guide_document',
    'review_excel_document',
)
RETIRED_BUTTONS = ('action_confirm_conciliation',)

RETIRED_VOLUME_PLACEHOLDER = 'Se asignará al enviar a stock.'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeOperationsScreen(TransactionCase):
    """Pantalla operativa de Volumen: tres bloques y nodos retirados ocultos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Pantalla Volumen', 'is_company': True})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _root(self):
        return etree.fromstring(self.env.ref(CONSOLE_FORM).arch)

    def _hides(self, invisible, ingestion_type):
        """¿La condición `invisible` oculta el nodo para el tipo indicado?

        Evalúa los marcadores de ingreso de la ficha: `"1"` nunca es visible;
        `ingestion_type == 'X'` oculta al tipo X; `ingestion_type != 'X'`
        oculta a todos los tipos salvo X; `ingestion_type not in (...)` oculta
        al resto.
        """
        if not invisible:
            return False
        invisible = ' '.join(invisible.split())
        if invisible == '1':
            return True
        for itype in ALL_INGESTION_TYPES:
            if ("ingestion_type == '%s'" % itype in invisible
                    and itype == ingestion_type):
                return True
            if ("ingestion_type != '%s'" % itype in invisible
                    and itype != ingestion_type):
                return True
        if ("ingestion_type not in ('processed', 'volume')" in invisible
                and ingestion_type not in ('processed', 'volume')):
            return True
        return False

    def _is_visible(self, node, ingestion_type):
        """¿El nodo (y toda su cadena de ancestros) queda visible?"""
        el = node
        while el is not None:
            if self._hides(el.get('invisible'), ingestion_type):
                return False
            el = el.getparent()
        return True

    def _make_guia(self, name, **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared',
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

    # ── 1. Exactamente los tres bloques de D3 ─────────────────────────────
    def test_01_tres_bloques_exactos(self):
        """Para Volumen solo existen los tres bloques de D3, en ese orden."""
        root = self._root()
        titles = [g.get('string') for g in root.iter('group')
                  if g.get('string') and self._is_visible(g, 'volume')]
        self.assertEqual(
            sorted(set(titles)), sorted(VISIBLE_TITLES),
            'Solo los tres bloques de D3 pueden quedar visibles en Volumen')
        unique = []
        for title in titles:
            if title not in unique:
                unique.append(title)
        self.assertEqual(
            unique, VISIBLE_TITLES, 'El orden de los bloques no es el exigido')

    # ── 2. Ausencia visible de los nodos retirados ────────────────────────
    def test_02_ausencia_visible_de_nodos_retirados(self):
        """Conciliación, auditoría, sumatorias, evidencia y operativos, ocultos."""
        root = self._root()

        for title in RETIRED_TITLES:
            groups = root.xpath("//group[@string='%s']" % title)
            self.assertTrue(groups, 'Falta el nodo del bloque «%s»' % title)
            for group in groups:
                self.assertFalse(
                    self._is_visible(group, 'volume'),
                    'El bloque «%s» no debe quedar visible en Volumen' % title)

        for field_name in RETIRED_FIELDS:
            nodes = root.xpath("//field[@name='%s']" % field_name)
            self.assertTrue(
                nodes, 'El nodo %s debe conservarse en el XML' % field_name)
            for node in nodes:
                self.assertFalse(
                    self._is_visible(node, 'volume'),
                    'El campo %s no debe quedar visible en Volumen'
                    % field_name)

        for name in RETIRED_BUTTONS:
            nodes = root.xpath("//button[@name='%s']" % name)
            self.assertTrue(
                nodes, 'El botón %s debe conservarse en el XML' % name)
            for node in nodes:
                self.assertFalse(
                    self._is_visible(node, 'volume'),
                    'El botón %s no debe quedar visible en Volumen' % name)

        # La fila de evidencia PDF/Excel conserva sus nodos y su guion.
        evidence = root.xpath(
            "//span[normalize-space(text())='Packing List (Excel):']")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].getparent().get('invisible'), '1')

        # El placeholder sin lote SV sigue presente una sola vez.
        arch = etree.tostring(root, encoding='unicode')
        self.assertEqual(
            arch.count(RETIRED_VOLUME_PLACEHOLDER), 1,
            'El placeholder sin lote debe aparecer una sola vez')

    # ── 3. Volumen oficial vigente: una sola vez, con fuente y botón ──────
    def test_03_volumen_oficial_vigente_con_fuente_y_boton(self):
        """El volumen vigente se muestra una vez con su fuente y su acción."""
        root = self._root()
        declared = root.xpath("//group[@string='%s']" % DECLARED_GROUP)
        self.assertEqual(len(declared), 1, 'Falta el bloque declarado')

        volume = declared[0].xpath(
            ".//field[@name='official_volume_effective_m3']")
        self.assertEqual(
            len(volume), 1, 'El volumen vigente debe mostrarse una sola vez')
        source = declared[0].xpath(
            ".//field[@name='official_volume_effective_source']")
        self.assertEqual(
            len(source), 1, 'La fuente del volumen vigente debe mostrarse')
        self.assertFalse(volume[0].get('invisible'))
        self.assertFalse(source[0].get('invisible'))

        buttons = declared[0].xpath(
            ".//button[@name='action_sv_regularize_volume']")
        self.assertEqual(len(buttons), 1, 'Falta el botón de modificación')
        self.assertEqual(buttons[0].get('type'), 'object')
        self.assertEqual(
            buttons[0].get('string'), 'Modificar volumen oficial')
        self.assertEqual(
            buttons[0].get('invisible'), 'not declared_sv_lot_id',
            'El botón debe ocultarse sin lote SV')

        # No existe una segunda instancia en toda la ficha.
        self.assertEqual(
            len(root.xpath("//field[@name='official_volume_effective_m3']")), 1)
        self.assertEqual(
            len(root.xpath(
                "//field[@name='official_volume_effective_source']")), 1)
        self.assertEqual(
            len(root.xpath("//button[@name='action_sv_regularize_volume']")), 1)

    # ── 4. Piezas declaradas: valor real, incluido el caso 0 ──────────────
    def test_04_piezas_declaradas_valor_real(self):
        """`declared_pieces` refleja el valor real de la Guía (0 no es vacío)."""
        guia_cero = self._make_guia('VOL-SCREEN-0', piezas_declaradas=0)
        console = self._console_for(guia_cero)
        self.assertTrue(console, 'La consola debe exponer la guía')
        self.assertEqual(
            console.declared_pieces, 0,
            'El caso 0 debe mostrarse como valor real, no como campo vacío')
        self.assertNotIsInstance(
            console.declared_pieces, bool,
            'declared_pieces debe ser Integer (no un booleano vacío)')

        guia = self._make_guia('VOL-SCREEN-124', piezas_declaradas=124)
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        self.assertEqual(console.declared_pieces, 124)

        # El nodo del campo es editable y visible en el bloque 2.
        root = self._root()
        field = root.xpath(
            "//group[@string='%s']//field[@name='declared_pieces']"
            % DECLARED_GROUP)
        self.assertEqual(len(field), 1)
        self.assertFalse(field[0].get('readonly') in ('1', 'True', 'true'))
        self.assertFalse(field[0].get('invisible'))