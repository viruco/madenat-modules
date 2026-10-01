# -*- coding: utf-8 -*-
"""Limpieza de presentación Packing (solo Ingreso por Volumen).

Contrato UI, solo XML de vistas (no crea registros, lotes, pickings,
movimientos ni ejecuta validación):

1. Consola: el grupo "DETALLE DEL PACKING LIST" se oculta para
   `ingestion_type == 'volume'` (sin encabezado vacío), conservando las tres
   grillas hijas y sus condiciones originales.
2. Fachada: en la página Packing, para `tipo_recepcion == 'granel'` se oculta
   la grilla operativa `processing_line_ids` y el botón "Fijar Nominal
   Masivo", y se mantiene visible el detalle documental de Volumen.
3. Preservación fuera de Volumen: sin condiciones nuevas ni atributos
   alterados en las grillas Producto/Procesado (consola) ni en la grilla
   operativa de la fachada.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
FACADE_FORM = ('madenat_lumber_intake'
               '.view_madenat_guia_processing_intake_facade_form')

VOLUME_DETAIL_COLUMNS = [
    'lot_or_package',
    'material_code',
    'description',
    'volume_m3',
    'uom',
    'unit_price',
    'line_amount',
    'observation',
]


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumePackingUxCleanup(TransactionCase):
    """Limpieza Consola/Fachada del detalle Packing para Volumen."""

    def _view_root(self, xmlid):
        """Raíz XML de una vista primaria (convención de test_documental_console)."""
        return etree.fromstring(self.env.ref(xmlid).arch)

    def _packing_page(self, root):
        pages = root.xpath("//page[@name='detail_lines']")
        self.assertEqual(len(pages), 1, 'Falta la página Packing (detail_lines)')
        return pages[0]

    # ── 1. Consola: aislamiento del grupo de detalle ──────────────────────
    def test_01_consola_grupo_detalle_solo_volumen(self):
        """El grupo se oculta solo para volumen y conserva sus tres grillas."""
        root = self._view_root(CONSOLE_FORM)

        groups = root.xpath("//group[@string='DETALLE DEL PACKING LIST']")
        self.assertEqual(
            len(groups), 1,
            'Debe existir exactamente un grupo DETALLE DEL PACKING LIST')
        group = groups[0]
        self.assertEqual(
            group.get('invisible'), "ingestion_type == 'volume'",
            'El grupo de detalle debe ocultarse solo para Volumen')

        for name in ('product_packing_line_ids',
                     'processed_packing_line_ids',
                     'volume_detail_line_ids'):
            self.assertEqual(
                len(group.xpath(".//field[@name='%s']" % name)), 1,
                'La grilla %s debe seguir existiendo' % name)

    def test_02_consola_condiciones_hijas_sin_cambios(self):
        """Las condiciones de las tres grillas hijas permanecen intactas."""
        root = self._view_root(CONSOLE_FORM)
        group = root.xpath("//group[@string='DETALLE DEL PACKING LIST']")[0]

        expected = {
            'product_packing_line_ids': "ingestion_type != 'product'",
            'processed_packing_line_ids': "ingestion_type != 'processed'",
            'volume_detail_line_ids': '1',
        }
        for name, condition in expected.items():
            node = group.xpath(".//field[@name='%s']" % name)[0]
            self.assertEqual(
                node.get('invisible'), condition,
                'Condición alterada en %s' % name)
            self.assertEqual(
                len(node.xpath('.//list')), 1,
                'La definición de lista de %s debe conservarse' % name)

    # ── 2. Fachada: limpieza de la página Packing ─────────────────────────
    def test_03_fachada_oculta_operativo_y_boton(self):
        """Volume oculta grilla operativa y botón de nominales masivos."""
        page = self._packing_page(self._view_root(FACADE_FORM))

        processing = page.xpath(".//field[@name='processing_line_ids']")
        self.assertEqual(
            len(processing), 1,
            'processing_line_ids debe permanecer en la página Packing')
        self.assertEqual(
            processing[0].get('invisible'), "tipo_recepcion == 'granel'",
            'La grilla operativa debe ocultarse solo para granel')

        buttons = page.xpath(
            ".//button[contains(@string, 'Fijar Nominal Masivo')]")
        self.assertEqual(
            len(buttons), 1,
            'Debe existir el botón Fijar Nominal Masivo')
        self.assertEqual(
            buttons[0].get('invisible'), "tipo_recepcion == 'granel'",
            'El botón de nominales masivos debe ocultarse solo para granel')

    def test_04_fachada_detalle_documental_volumen(self):
        """El detalle documental de Volumen conserva regla, edición y columnas."""
        page = self._packing_page(self._view_root(FACADE_FORM))

        nodes = page.xpath(".//field[@name='volume_detail_line_ids']")
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.get('invisible'), "tipo_recepcion != 'granel'")
        self.assertEqual(node.get('editable'), 'bottom')

        lists = node.xpath('.//list')
        self.assertEqual(len(lists), 1)
        columns = [f.get('name') for f in lists[0].xpath('./field')]
        self.assertEqual(columns, VOLUME_DETAIL_COLUMNS)

    # ── 3. Preservación fuera de Volumen ──────────────────────────────────
    def test_05_fachada_grilla_operativa_sin_condiciones_extra(self):
        """La grilla operativa solo lleva la condición de Volumen exacta."""
        page = self._packing_page(self._view_root(FACADE_FORM))

        node = page.xpath(".//field[@name='processing_line_ids']")[0]
        self.assertEqual(
            set(node.attrib), {'name', 'invisible'},
            'La grilla operativa no debe recibir otros atributos')
        lists = node.xpath('.//list')
        self.assertEqual(len(lists), 1)
        self.assertEqual(
            (lists[0].get('create'), lists[0].get('edit'),
             lists[0].get('delete')),
            ('false', 'true', 'false'),
            'La definición de lista operativa debe permanecer igual')
        self.assertEqual(
            len(lists[0].xpath('./field')), 14,
            'Las columnas de la grilla operativa no deben cambiar')
