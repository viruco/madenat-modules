# -*- coding: utf-8 -*-
"""Jerarquía y visibilidad de la pantalla operativa de Volumen (Fase 2).

Contrato verificado (solo arquitectura de vista; no crea registros, lotes,
pickings, movimientos ni ejecuta validación):

1. Para `ingestion_type == 'volume'` la ficha muestra EXACTAMENTE tres bloques
   visibles, en este orden: «DATOS DE LA GUÍA», «DATOS DECLARADOS DE LA GUÍA»
   y «ETIQUETA SV». Cualquier otro grupo con título queda oculto (por su propio
   `invisible` o por el de un ancestro).
2. El volumen oficial VIGENTE (`official_volume_effective_m3`) es el primer
   campo del bloque «DATOS DECLARADOS DE LA GUÍA» y se muestra una sola vez.
3. Los nodos retirados de la pantalla (conciliación, control documental
   interno, sumatorias, indicadores de encabezado, evidencia PDF/Excel y campos
   operativos de referencia) siguen existiendo en el XML con `invisible`
   aplicado: nunca se eliminan del archivo.
4. Los campos SV técnicos quedan con `invisible="1"`; `sv_lot_label` se muestra
   una sola vez y, sin lote SV, aparece el placeholder
   «Se asignará al enviar a stock.» sin ningún botón de mutación.
5. Fuera de Volumen (Producto/Procesado) los nodos retirados NO llevan la
   condición de Volumen: conservan la visibilidad anterior.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DATOS_GUIA_GROUP = 'DATOS DE LA GUÍA'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
SV_GROUP = 'ETIQUETA SV'
VISIBLE_TITLES = [DATOS_GUIA_GROUP, DECLARED_GROUP, SV_GROUP]

# Bloques que NO pueden quedar visibles en la pantalla operativa de Volumen.
HIDDEN_TITLES = (
    'Resumen del ingreso',
    'Evidencia documental',
    '📄 Evidencia documental',
    'VOLUMEN OFICIAL DE LA GUÍA',
    'Volumen operativo de referencia (no gobierna stock)',
    'Control documental interno (auditoría)',
    'DETALLE DEL PACKING LIST',
)

# Condición exacta de retiro para los nodos que siguen existiendo en el XML.
VOLUME_CONDITION = "ingestion_type == 'volume'"
# Campos SV técnicos retirados de la pantalla (nodos conservados).
SV_TECHNICAL_FIELDS = (
    'sv_original_volume_m3',
    'sv_regularized_baseline_m3',
    'sv_rebajado_m3',
    'sv_available_m3',
    'sv_available_pieces',
    'sv_documentary_warning',
    'sv_pieces_enabled',
    'sv_reversible_rebaja_id',
)
# Campos retirados que llevan la condición de Volumen en su propio nodo.
RETIRED_VOLUME_FIELDS = (
    'volume_detail_m3',
    'official_vs_detail_diff_m3',
    'conciliation_status',
    'conciliation_summary',
    'conciliation_manual_note',
    'declared_volume_m3',
)
# Campos operativos de referencia del bloque retirado por completo.
RETIRED_OPERATIONAL_FIELDS = (
    'volume_operational_m3',
    'volume_operational_source',
    'volume_operational_note',
    'review_state',
)
ALL_INGESTION_TYPES = ('product', 'processed', 'volume')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeUiHierarchy(TransactionCase):
    """Pantalla operativa de Volumen: tres bloques y nodos retirados ocultos."""

    def _root(self):
        return etree.fromstring(self.env.ref(CONSOLE_FORM).arch)

    # ── Evaluador de visibilidad de la ficha ──────────────────────────────
    def _hides(self, invisible, ingestion_type):
        """¿La condición `invisible` oculta el nodo para el tipo indicado?

        Solo evalúa los marcadores de ingreso presentes en la ficha:
        `"1"` nunca es visible; `ingestion_type == 'X'` oculta al tipo X;
        `ingestion_type != 'X'` oculta a todos los tipos salvo X;
        `ingestion_type not in ('processed', 'volume')` oculta al resto.
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

    def _visible_titles(self, root, ingestion_type, ordered=False):
        titles = [g.get('string') for g in root.iter('group')
                  if g.get('string') and self._is_visible(g, ingestion_type)]
        if not ordered:
            return titles
        unique = []
        for title in titles:
            if title not in unique:
                unique.append(title)
        return unique

    # ── 1. Exactamente tres bloques visibles, en orden ────────────────────
    def test_01_tres_bloques_visibles_en_orden(self):
        """Para Volumen solo se ven los tres bloques de D3, en ese orden."""
        root = self._root()
        titles = self._visible_titles(root, 'volume')
        self.assertEqual(
            sorted(set(titles)), sorted(VISIBLE_TITLES),
            'La pantalla de Volumen debe mostrar solo los tres bloques de D3')
        self.assertEqual(
            self._visible_titles(root, 'volume', ordered=True),
            VISIBLE_TITLES,
            'Los tres bloques deben respetar el orden documental exigido')

    # ── 2. El volumen oficial vigente encabeza el bloque 2 ────────────────
    def test_02_volumen_oficial_vigente_primero(self):
        """El volumen oficial vigente es el primer campo del bloque 2."""
        root = self._root()
        declared = root.xpath("//group[@string='%s']" % DECLARED_GROUP)
        self.assertEqual(len(declared), 1, 'Falta el bloque declarado')
        fields = declared[0].xpath('.//field')
        self.assertEqual(
            fields[0].get('name'), 'official_volume_effective_m3',
            'El volumen oficial vigente debe ser el primer campo del bloque')
        for field_name in ('official_volume_effective_m3',
                           'official_volume_effective_source'):
            self.assertEqual(
                len(root.xpath("//field[@name='%s']" % field_name)), 1,
                '%s debe mostrarse una sola vez' % field_name)

    # ── 3. Bloques retirados ocultos para Volumen ─────────────────────────
    def test_03_bloques_retirados_ocultos_para_volumen(self):
        """Ningún bloque adicional queda visible en la pantalla de Volumen."""
        root = self._root()
        for title in HIDDEN_TITLES:
            groups = root.xpath("//group[@string='%s']" % title)
            self.assertTrue(groups, 'Falta el nodo del bloque «%s»' % title)
            for group in groups:
                self.assertFalse(
                    self._is_visible(group, 'volume'),
                    'El bloque «%s» no debe quedar visible en Volumen' % title)

    # ── 4. Nodos retirados con `invisible` aplicado ───────────────────────
    def test_04_nodos_retirados_con_invisible(self):
        """Los nodos de la sección 4 existen con el `invisible` aplicado."""
        root = self._root()
        for field_name in RETIRED_VOLUME_FIELDS:
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            self.assertIn(
                VOLUME_CONDITION, node.get('invisible') or '',
                '%s debe llevar la condición de Volumen' % field_name)
        button = root.xpath("//button[@name='action_confirm_conciliation']")[0]
        self.assertIn(
            VOLUME_CONDITION, button.get('invisible') or '',
            'Confirmar conciliación debe quedar retirado en Volumen')

        # Bloque operativo de referencia retirado por completo.
        operational = root.xpath(
            "//group[@string='Volumen operativo de referencia "
            "(no gobierna stock)']")
        self.assertEqual(len(operational), 1)
        self.assertIn(
            VOLUME_CONDITION, operational[0].get('invisible') or '')
        for field_name in RETIRED_OPERATIONAL_FIELDS:
            node = operational[0].xpath(
                ".//field[@name='%s']" % field_name)[0]
            self.assertIn(
                VOLUME_CONDITION, node.get('invisible') or '',
                '%s debe quedar retirado de la pantalla' % field_name)

        # Indicadores de encabezado: contenedor oculto para Volumen.
        for field_name in ('total_lots', 'total_amount', 'total_volume_m3'):
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.getparent().get('invisible'), VOLUME_CONDITION,
                'El indicador %s debe ocultarse en Volumen' % field_name)
        header_review = root.xpath(
            "//div[contains(@class, 'indicator')]"
            "//field[@name='review_state']")
        self.assertEqual(len(header_review), 1)
        self.assertEqual(
            header_review[0].getparent().get('invisible'), VOLUME_CONDITION)

        # Fila de evidencia documental PDF/Excel retirada (nodos conservados).
        spans = root.xpath(
            "//span[normalize-space(text())='Packing List (Excel):']")
        self.assertEqual(
            len(spans), 1, 'Falta la fila de evidencia PDF/Excel')
        evidence = spans[0].getparent()
        self.assertEqual(evidence.get('invisible'), '1')
        for field_name in ('review_guide_document', 'review_excel_document'):
            self.assertEqual(
                len(evidence.xpath(".//field[@name='%s']" % field_name)), 1,
                'El nodo %s debe conservarse en el XML' % field_name)

        # Sumatorias del packing fuera de Volumen.
        packing = root.xpath("//field[@name='packing_volume_total']")[0]
        self.assertFalse(
            self._is_visible(packing, 'volume'),
            'La sumatoria del packing no debe quedar visible en Volumen')
        # packing_line_count no tiene nodo propio en la ficha: nada que ocultar.
        self.assertFalse(root.xpath("//field[@name='packing_line_count']"))

    # ── 5. Etiqueta SV única y saldos SV técnicos ocultos ─────────────────
    def test_05_sv_tecnico_oculto_y_etiqueta_unica(self):
        """`sv_lot_label` se muestra una sola vez; saldos técnicos ocultos."""
        root = self._root()
        self.assertEqual(
            len(root.xpath("//field[@name='sv_lot_label']")), 1,
            'La etiqueta SV debe mostrarse una sola vez')
        for field_name in SV_TECHNICAL_FIELDS:
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('invisible'), '1',
                '%s no debe quedar visible en la pantalla' % field_name)

        # Sin lote SV: solo el placeholder, sin ningún botón de mutación.
        arch = etree.tostring(root, encoding='unicode')
        self.assertEqual(
            arch.count('Se asignará al enviar a stock.'), 1,
            'El placeholder sin lote debe aparecer una sola vez')
        placeholders = [d for d in root.iter('div')
                        if 'Se asignará al enviar a stock.' in (d.text or '')]
        self.assertEqual(len(placeholders), 1, 'Falta el placeholder')
        state = placeholders[0].getparent().getparent()
        self.assertEqual(
            state.get('invisible'),
            "ingestion_type != 'volume' or declared_sv_lot_id")
        self.assertFalse(
            state.xpath('.//button'),
            'Sin lote SV no debe existir ningún botón de mutación')

    # ── 6. Fuera de Volumen la condición de Volumen no aplica ─────────────
    def test_06_fuera_de_volumen_sin_condicion_de_volumen(self):
        """Los nodos retirados no quedan ocultos para Producto/Procesado."""
        root = self._root()
        for field_name in RETIRED_VOLUME_FIELDS + RETIRED_OPERATIONAL_FIELDS:
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            invisible = node.get('invisible') or ''
            self.assertNotEqual(
                invisible, '1',
                '%s no debe ocultarse fuera de Volumen' % field_name)
            self.assertNotIn(
                "ingestion_type != 'volume'", invisible,
                '%s no debe bloquearse fuera de Volumen' % field_name)
        for field_name in ('total_lots', 'total_amount', 'total_volume_m3'):
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.getparent().get('invisible'), VOLUME_CONDITION,
                'El indicador %s debe seguir visible fuera de Volumen'
                % field_name)
            self.assertTrue(self._is_visible(node, 'product'))
            self.assertTrue(self._is_visible(node, 'processed'))

        # Los bloques de Producto/Procesado siguen visibles como antes.
        for title, itype in (('DETALLE DEL PACKING LIST', 'product'),
                             ('DETALLE DEL PACKING LIST', 'processed'),
                             ('Resumen del ingreso', 'product'),
                             ('📄 Evidencia documental', 'processed')):
            groups = root.xpath("//group[@string='%s']" % title)
            self.assertEqual(len(groups), 1, 'Falta el bloque «%s»' % title)
            self.assertTrue(
                self._is_visible(groups[0], itype),
                'El bloque «%s» debe seguir visible para %s' % (title, itype))