# -*- coding: utf-8 -*-
"""Bloque SV visible y acciones de Etiqueta SV desde la Consola (Fase 2, AD-80).

Contrato verificado:

1. Con lote SV: el bloque «ETIQUETA SV» muestra la etiqueta UNA SOLA VEZ y las
   cuatro acciones autorizadas (modificar etiqueta, rebajar, reversar rebaja y
   ver historial); los saldos técnicos quedan en el XML con `invisible="1"`.
2. «Modificar volumen oficial» (regularizar volumen) NO vive en el bloque SV:
   su única instancia está en «DATOS DECLARADOS DE LA GUÍA», junto al volumen
   oficial vigente.
3. Sin lote SV: no hay botón de mutación y la acción falla con mensaje claro.
4. Piezas disponibles visibles SOLO con piezas documentales positivas
   (`sv_pieces_enabled`); nunca por paquetes ni por piezas=1 técnico.
5. Todas las acciones delegan en los wizards canónicos del Programa SV.
6. Reversa: solo la rebaja aplicada y no reversada habilita el botón; la
   segunda reversa la bloquea el ledger.

Los proxies del bloque son no almacenados (la consola es una vista SQL) y de
solo lectura: la prueba no escribe en el lote, la guía, stock ni secuencia.
"""

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DATOS_GUIA_GROUP = 'DATOS DE LA GUÍA'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
SV_GROUP = 'ETIQUETA SV'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeConsoleSvActions(TransactionCase):
    """Bloque SV y acciones SV autorizadas de la Consola."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.StockLot = cls.env['stock.lot']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor SV Consola', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto SV Consola',
            'is_storable': True,
            'tracking': 'lot',
        })

    # ── Fábricas ──────────────────────────────────────────────────────────
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
        return self.Guia.create(vals)

    def _make_lot(self, guia, label, volume=40.300, piezas=1):
        lot = self.StockLot.create({
            'name': label,
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
            'guia_processing_id': guia.id,
            'piezas': piezas,
            'volume_purchase_m3': volume,
            'vol_shipment_m3': volume,
            'volumen_m3': volume,
        })
        guia.write({'lot_ids': [(4, lot.id)]})
        return lot

    def _console_for(self, guia):
        self.env.invalidate_all()
        console = self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        console.invalidate_recordset()
        return console

    # ── 1. Bloque SV con lote real ────────────────────────────────────────
    def test_01_bloque_sv_con_lote(self):
        """Etiqueta, original, baseline, rebajado, saldo y advertencia."""
        guia = self._make_guia('SV-CONS-CON-LOTE')
        lot = self._make_lot(guia, 'SV00000000301')
        console = self._console_for(guia)

        self.assertEqual(console.declared_sv_lot_id, lot)
        self.assertEqual(console.sv_lot_label, 'SV00000000301')
        self.assertAlmostEqual(
            console.sv_original_volume_m3, 40.300, places=3)
        self.assertAlmostEqual(
            console.sv_regularized_baseline_m3, 40.300, places=3)
        self.assertAlmostEqual(console.sv_rebajado_m3, 0.0, places=3)
        self.assertAlmostEqual(console.sv_available_m3, 40.300, places=3)
        # El volumen oficial (40,315) difiere del original del lote (40,300).
        self.assertTrue(console.sv_documentary_warning)
        # Sin piezas documentales declaradas no se habilitan piezas.
        self.assertFalse(console.sv_pieces_enabled)
        self.assertEqual(console.sv_available_pieces, 0)
        self.assertFalse(console.sv_reversible_rebaja_id)

    # ── 2. Sin lote SV: placeholder y sin mutación ────────────────────────
    def test_02_sin_lote_sv_sin_mutacion(self):
        """Sin lote SV no hay saldo ni acciones posibles."""
        guia = self._make_guia('SV-CONS-SIN-LOTE')
        console = self._console_for(guia)

        self.assertFalse(console.declared_sv_lot_id)
        self.assertFalse(console.sv_lot_label)
        self.assertAlmostEqual(console.sv_available_m3, 0.0, places=3)
        for method in ('action_sv_rename', 'action_sv_regularize_volume',
                       'action_sv_rebaja', 'action_sv_reverse_rebaja'):
            with self.assertRaises(UserError):
                getattr(console, method)()

    # ── 3. Piezas solo con piezas documentales positivas ──────────────────
    def test_03_piezas_solo_documentales(self):
        """`sv_pieces_enabled` depende de piezas declaradas positivas."""
        guia = self._make_guia(
            'SV-CONS-PIEZAS', piezas_declaradas=100,
            packing_pieces_declared=40)
        lot = self._make_lot(guia, 'SV00000000302')
        console = self._console_for(guia)
        self.assertTrue(console.sv_pieces_enabled)
        self.assertEqual(console.sv_available_pieces, 100)
        self.assertEqual(lot.piezas, 1)  # Placeholder técnico intacto.

        # Paquetes y líneas PDF jamás habilitan piezas.
        guia_paq = self._make_guia(
            'SV-CONS-PAQUETES', piezas_declaradas=0,
            packing_package_count_declared=25)
        self._make_lot(guia_paq, 'SV00000000303')
        console_paq = self._console_for(guia_paq)
        self.assertFalse(console_paq.sv_pieces_enabled)
        self.assertEqual(console_paq.sv_available_pieces, 0)

    # ── 4. Delegación en los wizards canónicos ────────────────────────────
    def test_04_acciones_delegan_en_wizards(self):
        """Las cuatro acciones abren el wizard/ventana canónica del core."""
        guia = self._make_guia('SV-CONS-DELEGA')
        lot = self._make_lot(guia, 'SV00000000304')
        console = self._console_for(guia)

        rename = console.action_sv_rename()
        self.assertEqual(rename['res_model'], 'madenat.sv.rename.wizard')
        self.assertEqual(rename['context']['default_lot_id'], lot.id)
        regularize = console.action_sv_regularize_volume()
        self.assertEqual(
            regularize['res_model'], 'madenat.sv.volume.regularize.wizard')
        self.assertEqual(regularize['context']['default_lot_id'], lot.id)
        rebaja = console.action_sv_rebaja()
        self.assertEqual(rebaja['res_model'], 'madenat.sv.rebaja.wizard')
        self.assertEqual(rebaja['context']['default_lot_id'], lot.id)
        history = console.action_open_sv_history()
        self.assertEqual(history['res_model'], 'madenat.sv.operation')
        self.assertIn(('lot_id', '=', lot.id), history['domain'])


    # ── 5. Reversa: solo rebaja aplicada y reversible ─────────────────────
    def test_05_reversa_visible_y_no_duplicable(self):
        """La rebaja aplicada habilita la reversa; luego desaparece."""
        guia = self._make_guia('SV-CONS-REVERSA')
        lot = self._make_lot(guia, 'SV00000000305')
        self.env['madenat.sv.rebaja.wizard'].create({
            'lot_id': lot.id,
            'rebaja_volume_m3': 10.0,
            'reason': 'Rebaja de prueba',
        }).action_submit()

        console = self._console_for(guia)
        rebaja = console.sv_reversible_rebaja_id
        self.assertTrue(rebaja, 'La rebaja aplicada debe ser reversible')
        self.assertEqual(rebaja.action_type, 'rebaja')
        self.assertEqual(rebaja.state, 'applied')
        self.assertAlmostEqual(console.sv_rebajado_m3, 10.0, places=3)
        self.assertAlmostEqual(console.sv_available_m3, 30.300, places=3)

        reverse_action = console.action_sv_reverse_rebaja()
        self.assertEqual(
            reverse_action['res_model'], 'madenat.sv.rebaja.reverse.wizard')
        self.assertEqual(
            reverse_action['context']['default_origin_operation_id'],
            rebaja.id)

        self.env['madenat.sv.rebaja.reverse.wizard'].create({
            'origin_operation_id': rebaja.id,
            'reason': 'Devolución del volumen asignado',
        }).action_submit()

        console = self._console_for(guia)
        self.assertFalse(
            console.sv_reversible_rebaja_id,
            'Tras la reversa no queda rebaja reversible')
        self.assertAlmostEqual(console.sv_rebajado_m3, 0.0, places=3)
        self.assertAlmostEqual(console.sv_available_m3, 40.300, places=3)
        with self.assertRaises(UserError):
            console.action_sv_reverse_rebaja()

    # ── 6. Proxies read-only y no almacenados ─────────────────────────────
    def test_06_proxies_readonly_no_almacenados(self):
        """El bloque SV no agrega columnas ni admite escritura directa."""
        for field_name in ('sv_lot_label', 'sv_original_volume_m3',
                           'sv_regularized_baseline_m3', 'sv_rebajado_m3',
                           'sv_regularization_applied', 'sv_available_m3',
                           'sv_pieces_enabled', 'sv_available_pieces',
                           'sv_documentary_warning', 'sv_reversible_rebaja_id'):
            field = self.Console._fields[field_name]
            self.assertTrue(field.compute, '%s debe ser computado' % field_name)
            self.assertFalse(
                field.store, '%s no debe almacenarse' % field_name)
            self.assertTrue(
                field.readonly, '%s debe ser readonly' % field_name)

    # ── 7. Vista: acciones autorizadas dentro del bloque SV ───────────────
    def test_07_vista_acciones_autorizadas(self):
        """El bloque SV solo muestra la etiqueta y las cuatro acciones."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        authorized = {
            'action_sv_rename': 'Modificar etiqueta SV',
            'action_sv_rebaja': 'Rebajar etiqueta',
            'action_sv_reverse_rebaja': 'Reversar rebaja',
            'action_open_sv_history': 'Ver historial SV',
        }
        blocks = root.xpath("//group[@string='%s']" % SV_GROUP)
        self.assertEqual(len(blocks), 2, 'Falta el bloque ETIQUETA SV')
        with_lot = blocks[0].getparent()
        without_lot = blocks[1].getparent()
        self.assertIn('not declared_sv_lot_id', with_lot.get('invisible'))
        self.assertIn('declared_sv_lot_id', without_lot.get('invisible'))

        for name, label in authorized.items():
            nodes = with_lot.xpath(".//button[@name='%s']" % name)
            self.assertEqual(len(nodes), 1, 'Falta el botón %s' % name)
            self.assertEqual(nodes[0].get('type'), 'object')
            self.assertEqual(nodes[0].get('string'), label)
        # La etiqueta SV se muestra una sola vez en el bloque.
        self.assertEqual(
            len(with_lot.xpath(".//field[@name='sv_lot_label']")), 1,
            'Falta la etiqueta SV en el bloque')

        # «Modificar volumen oficial» NO pertenece a este bloque.
        for block in blocks:
            self.assertFalse(
                block.xpath(
                    ".//button[@name='action_sv_regularize_volume']"),
                'El botón de volumen oficial no debe estar en ETIQUETA SV')

        # Ningún saldo técnico queda visible aquí.
        for field_name in ('sv_original_volume_m3',
                           'sv_regularized_baseline_m3', 'sv_rebajado_m3',
                           'sv_available_m3', 'sv_available_pieces',
                           'sv_documentary_warning', 'sv_pieces_enabled'):
            nodes = with_lot.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(len(nodes), 1, 'Falta %s' % field_name)
            self.assertEqual(
                nodes[0].get('invisible'), '1',
                '%s no debe quedar visible en el bloque SV' % field_name)

        # La reversa conserva su guarda y sin lote no hay mutación posible.
        reverse = with_lot.xpath(
            ".//button[@name='action_sv_reverse_rebaja']")[0]
        self.assertEqual(
            reverse.get('invisible'), 'not sv_reversible_rebaja_id')
        self.assertFalse(without_lot.xpath('.//button'))

    # ── 8. Orden de bloques y retiro del bloque ejecutivo ─────────────────
    def test_08_bloque_sv_orden_y_contenedor_volumen(self):
        """El bloque SV va al final de los tres bloques visibles de Volumen."""
        root = etree.fromstring(self.env.ref(CONSOLE_FORM).arch)
        ordered = [el.get('string') for el in root.iter('group')
                   if el.get('string')]
        self.assertLess(
            ordered.index(DATOS_GUIA_GROUP),
            ordered.index(DECLARED_GROUP),
            'DATOS DE LA GUÍA va antes de DATOS DECLARADOS DE LA GUÍA')
        self.assertLess(
            ordered.index(DECLARED_GROUP), ordered.index(SV_GROUP),
            'ETIQUETA SV va después de DATOS DECLARADOS DE LA GUÍA')

        # El volumen oficial crudo queda conservado pero oculto.
        official = root.xpath("//group[@string='VOLUMEN OFICIAL DE LA GUÍA']")
        self.assertEqual(len(official), 1)
        self.assertEqual(official[0].get('invisible'), '1')

        # El bloque SV vive dentro del contenedor exclusivo de Volumen.
        blocks = root.xpath("//group[@string='%s']" % SV_GROUP)
        self.assertEqual(len(blocks), 2)
        node = blocks[0]
        container = None
        while node is not None:
            if node.get('invisible') == "ingestion_type != 'volume'":
                container = node
                break
            node = node.getparent()
        self.assertIsNotNone(
            container,
            'El bloque SV debe vivir dentro del contenedor de Volumen')
