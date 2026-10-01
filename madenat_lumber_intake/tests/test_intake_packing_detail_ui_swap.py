# -*- coding: utf-8 -*-
"""Intercambio de superficie del detalle Packing (solo Ingreso por Volumen).

Contrato UI, sin datos ni flujos (no crea registros, lotes, pickings,
movimientos ni ejecuta validación):

1. Consola: la grilla documental de Volumen queda oculta (`invisible="1"`)
   conservando su nodo y su lista, mientras las grillas de Producto y
   Procesado mantienen exactamente su visibilidad y sus listas.
2. Fachada de origen: la grilla documental de Volumen se muestra solo para
   `tipo_recepcion == 'granel'`, editable y con las ocho columnas aprobadas;
   la grilla operativa `processing_line_ids` permanece en la página Packing
   pero oculta para `granel` (regla de negocio de Volumen: sin cubicación
   geométrica), conservando su definición de lista original.

Solo se inspecciona el XML de las vistas.
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
class TestIntakePackingDetailUiSwap(TransactionCase):
    """Detalle documental de Volumen: oculto en consola, visible en fachada."""

    def _view_root(self, xmlid):
        """Raíz XML de una vista primaria (convención de test_documental_console)."""
        return etree.fromstring(self.env.ref(xmlid).arch)

    # ── 1. Aislamiento de la grilla de Volumen en la consola ──────────────
    def test_01_consola_oculta_grilla_volumen(self):
        """La grilla documental de Volumen queda oculta, conservando su lista."""
        root = self._view_root(CONSOLE_FORM)

        nodes = root.xpath("//field[@name='volume_detail_line_ids']")
        self.assertEqual(
            len(nodes), 1,
            'Debe existir exactamente un nodo volume_detail_line_ids')
        self.assertEqual(
            nodes[0].get('invisible'), '1',
            'La grilla documental de Volumen debe quedar oculta en la consola')
        # Nodo y definición de lista conservados (ocultamiento solo visual).
        self.assertEqual(
            len(nodes[0].xpath('.//list')), 1,
            'La definición de lista del detalle de Volumen debe conservarse')

    def test_02_consola_producto_y_procesado_intactos(self):
        """Producto y Procesado conservan visibilidad y definición de lista."""
        root = self._view_root(CONSOLE_FORM)

        product = root.xpath("//field[@name='product_packing_line_ids']")
        self.assertEqual(len(product), 1)
        self.assertEqual(
            product[0].get('invisible'), "ingestion_type != 'product'")
        self.assertEqual(len(product[0].xpath('.//list')), 1)

        processed = root.xpath("//field[@name='processed_packing_line_ids']")
        self.assertEqual(len(processed), 1)
        self.assertEqual(
            processed[0].get('invisible'), "ingestion_type != 'processed'")
        self.assertEqual(len(processed[0].xpath('.//list')), 1)

    # ── 2. Fachada de origen: detalle documental de Volumen ───────────────
    def test_03_fachada_muestra_detalle_volumen(self):
        """La página Packing expone el detalle de Volumen con sus 8 columnas."""
        root = self._view_root(FACADE_FORM)

        self.assertEqual(
            len(root.xpath("//field[@name='volume_detail_line_ids']")), 1,
            'La fachada debe exponer un único nodo volume_detail_line_ids')

        nodes = root.xpath(
            "//page[@name='detail_lines']"
            "//field[@name='volume_detail_line_ids']")
        self.assertEqual(
            len(nodes), 1,
            'El detalle de Volumen debe estar dentro de la página Packing')
        node = nodes[0]
        self.assertEqual(
            node.get('invisible'), "tipo_recepcion != 'granel'",
            'El detalle de Volumen solo aplica a tipo_recepcion granel')
        self.assertEqual(
            node.get('editable'), 'bottom',
            'La corrección documental debe permanecer disponible')

        lists = node.xpath('.//list')
        self.assertEqual(len(lists), 1)
        columns = [f.get('name') for f in lists[0].xpath('./field')]
        self.assertEqual(columns, VOLUME_DETAIL_COLUMNS)

    # ── 3. Preservación de la relación operativa en la fachada ────────────
    def test_04_fachada_conserva_processing_line_ids(self):
        """processing_line_ids permanece en Packing, oculta solo para granel.

        Regla de negocio de Volumen: la etiqueta SV no usa cubicación
        geométrica, por lo que la grilla operativa se oculta para 'granel'
        (la fila sintética GRANEL con piezas=1 y dimensiones 0 no debe
        presentarse como dato operativo). El nodo y su lista se conservan.
        """
        root = self._view_root(FACADE_FORM)

        nodes = root.xpath(
            "//page[@name='detail_lines']"
            "//field[@name='processing_line_ids']")
        self.assertEqual(
            len(nodes), 1,
            'processing_line_ids debe permanecer en la página Packing')
        self.assertEqual(
            nodes[0].get('invisible'), "tipo_recepcion == 'granel'",
            'La grilla operativa solo debe ocultarse para granel (Volumen)')
        lists = nodes[0].xpath('.//list')
        self.assertEqual(len(lists), 1)
        self.assertEqual(
            (lists[0].get('create'), lists[0].get('edit'),
             lists[0].get('delete')),
            ('false', 'true', 'false'),
            'La definición de lista operativa debe permanecer igual')
        self.assertEqual(
            len(lists[0].xpath('./field')), 14,
            'Las columnas de la grilla operativa no deben cambiar')
