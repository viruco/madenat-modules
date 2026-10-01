# -*- coding: utf-8 -*-
"""Sugerencias de la cabecera declarada (solo Ingreso por Volumen).

Cubre el contrato de los proxies de solo lectura y de la acción explícita
"Aplicar sugerencias" de `madenat.lumber.intake.console`:

1. RW / RL comerciales y espesor sin sugerencia; vacío fuera de Volumen.
2. Precedencia de piezas (Packing > suma line_by_line; nunca la línea GRANEL).
3. Precedencia de M³ con su etiqueta de origen exacta.
4. Acción: rellena solo campos vacíos y no toca nada más.
5. Etiqueta SV: placeholder antes del lote, relación real después; sin
   creación de lotes ni consumo/lectura de secuencia.
6. Arquitectura de la vista de consola.

No ejecuta validación, no crea pickings ni escribe stock.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredSuggestions(TransactionCase):
    """Sugerencias documentales de la cabecera declarada de Volumen."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.Line = cls.env['madenat.guia.processing.line']
        cls.DetailLine = cls.env['madenat.lumber.volume.detail.line']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Sugerencias Volumen', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Sugerencias Volumen',
            'is_storable': True,
            'tracking': 'lot',
        })

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, tipo='granel', name=None, **extra):
        """Crea una Guía mínima (sin flujo de stock ni de documentos)."""
        vals = {
            'name': name or 'VOL-SUG-%s' % tipo.upper(),
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo,
            'state': 'draft',
        }
        vals.update(extra)
        return self.Guia.create(vals)

    def _suggestions(self, guia):
        """Registro de consola con las sugerencias recalculadas (frescas)."""
        self.env.invalidate_all()
        guia.flush_recordset()
        console = self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        return console

    def _make_line(self, guia, lot_name='L1', pieces=1):
        return self.Line.create({
            'processing_id': guia.id,
            'lot_name': lot_name,
            'sku_original': lot_name,
            'product_id': self.product.id,
            'pieces': pieces,
        })

    def _make_detail_line(self, guia, volume=10.0):
        return self.DetailLine.create({
            'guia_id': guia.id,
            'lot_or_package': 'P1',
            'description': 'Detalle documental PDF',
            'volume_m3': volume,
        })

    # ── 1. RW / RL (y espesor sin sugerencia) ─────────────────────────────
    def test_01_sugerencias_rw_rl_solo_volumen(self):
        """RW/RL para Volumen; espesor vacío; nada fuera de Volumen."""
        guia = self._make_guia(name='VOL-SUG-RWRL')
        console = self._suggestions(guia)
        self.assertEqual(console.suggested_widths_text, 'RW')
        self.assertEqual(console.suggested_lengths_text, 'RL')
        self.assertFalse(console.suggested_thickness_text)
        self.assertEqual(console.suggested_pieces, 0)
        self.assertEqual(console.suggested_volume_m3, 0.0)
        self.assertFalse(console.suggested_volume_source)

        guia_compra = self._make_guia(tipo='compra', name='VOL-SUG-COMPRA')
        console_compra = self._suggestions(guia_compra)
        self.assertFalse(console_compra.suggested_widths_text)
        self.assertFalse(console_compra.suggested_lengths_text)
        self.assertFalse(console_compra.suggested_thickness_text)
        self.assertEqual(console_compra.suggested_pieces, 0)
        self.assertEqual(console_compra.suggested_volume_m3, 0.0)
        self.assertFalse(console_compra.suggested_volume_source)

    # ── 2. Precedencia de piezas ──────────────────────────────────────────
    def test_02_precedencia_piezas(self):
        """Packing > suma line_by_line; la línea GRANEL consolidada no sugiere."""
        guia_pack = self._make_guia(
            name='VOL-SUG-PZ-PACK', packing_pieces_declared=124)
        self._make_line(guia_pack, lot_name='GRANEL', pieces=1)
        self.assertEqual(self._suggestions(guia_pack).suggested_pieces, 124)

        guia_ll = self._make_guia(
            name='VOL-SUG-PZ-LL', detalle_aplicado='line_by_line')
        self._make_line(guia_ll, lot_name='L1', pieces=5)
        self._make_line(guia_ll, lot_name='L2', pieces=7)
        self._make_line(guia_ll, lot_name='L0', pieces=0)
        self.assertEqual(self._suggestions(guia_ll).suggested_pieces, 12)

        guia_cons = self._make_guia(
            name='VOL-SUG-PZ-CONS', detalle_aplicado='consolidated')
        self._make_line(guia_cons, lot_name='GRANEL', pieces=1)
        self.assertEqual(
            self._suggestions(guia_cons).suggested_pieces, 0,
            'La línea sintética GRANEL no debe sugerir una pieza')

    # ── 3. Precedencia de M³ y etiqueta de origen ─────────────────────────
    def test_03_precedencia_m3_y_origen(self):
        """PDF > Excel > Packing declarado > suma del detalle documental."""
        guia = self._make_guia(name='VOL-SUG-M3')
        self._make_detail_line(guia, volume=10.0)

        console = self._suggestions(guia)
        self.assertAlmostEqual(console.suggested_volume_m3, 10.0, places=3)
        self.assertEqual(
            console.suggested_volume_source, 'Suma detalle documental')

        guia.write({'packing_volume_declared_m3': 20.0})
        console = self._suggestions(guia)
        self.assertAlmostEqual(console.suggested_volume_m3, 20.0, places=3)
        self.assertEqual(
            console.suggested_volume_source, 'Total declarado Packing')

        guia.write({'volume_excel_m3': 30.0})
        console = self._suggestions(guia)
        self.assertAlmostEqual(console.suggested_volume_m3, 30.0, places=3)
        self.assertEqual(console.suggested_volume_source, 'Packing Excel')

        guia.write({'volume_pdf_m3': 40.0})
        console = self._suggestions(guia)
        self.assertAlmostEqual(console.suggested_volume_m3, 40.0, places=3)
        self.assertEqual(console.suggested_volume_source, 'Guía PDF')

        # El volumen operativo nunca participa de la sugerencia.
        guia.write({'volume_operational_m3': 99.0})
        self.assertAlmostEqual(
            self._suggestions(guia).suggested_volume_m3, 40.0, places=3)

    # ── 4. Acción "Aplicar sugerencias" ───────────────────────────────────
    def test_04_accion_aplicar_solo_campos_vacios(self):
        """Rellena RW/RL/piezas/M³ vacíos y jamás sobrescribe al operador."""
        guia = self._make_guia(name='VOL-SUG-APPLY')
        guia.write({'packing_pieces_declared': 124, 'volume_pdf_m3': 40.0})
        console = self._suggestions(guia)

        result = console.action_apply_declared_volume_suggestions()
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

        guia.invalidate_recordset()
        self.assertEqual(guia.anchos_variables, 'RW')
        self.assertEqual(guia.largos_variables, 'RL')
        self.assertFalse(guia.espesor_nominal_texto)
        self.assertEqual(guia.piezas_declaradas, 124)
        self.assertAlmostEqual(guia.volumen_declarado_m3, 40.0, places=3)
        # Nada más cambia en la guía origen.
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(guia.state, 'draft')
        self.assertEqual(guia.partner_id, self.partner)
        self.assertFalse(guia.order_id)
        self.assertEqual(guia.volume_operational_m3, 0.0)
        self.assertFalse(guia.processing_line_ids)
        # El botón sólo puede AGREGAR el reflejo de la cabecera declarada
        # (Fase 3): nunca crea detalle documental PDF/Excel.
        self.assertEqual(
            guia.volume_detail_line_ids.mapped('origin'), ['header'],
            'El botón no debe crear líneas documentales')
        self.assertFalse(guia.volume_lot_id)

        # Valores del operador: intactos.
        guia_full = self._make_guia(name='VOL-SUG-APPLY-FULL')
        guia_full.write({
            'anchos_variables': '4 1/2',
            'largos_variables': '10',
            'espesor_nominal_texto': '7/4',
            'piezas_declaradas': 99,
            'volumen_declarado_m3': 5.0,
            'packing_pieces_declared': 124,
            'volume_pdf_m3': 40.0,
        })
        console_full = self._suggestions(guia_full)
        console_full.action_apply_declared_volume_suggestions()
        guia_full.invalidate_recordset()
        self.assertEqual(guia_full.anchos_variables, '4 1/2')
        self.assertEqual(guia_full.largos_variables, '10')
        self.assertEqual(guia_full.espesor_nominal_texto, '7/4')
        self.assertEqual(guia_full.piezas_declaradas, 99)
        self.assertAlmostEqual(guia_full.volumen_declarado_m3, 5.0, places=3)

        # No-volume: la acción no escribe nada.
        guia_compra = self._make_guia(
            tipo='compra', name='VOL-SUG-APPLY-COMPRA')
        console_compra = self._suggestions(guia_compra)
        console_compra.action_apply_declared_volume_suggestions()
        guia_compra.invalidate_recordset()
        self.assertFalse(guia_compra.anchos_variables)
        self.assertFalse(guia_compra.largos_variables)
        self.assertEqual(guia_compra.piezas_declaradas, 0)
        self.assertEqual(guia_compra.volumen_declarado_m3, 0.0)

    # ── 5. Etiqueta SV y seguridad de secuencia ───────────────────────────
    def test_05_sv_y_secuencia_sin_consumo(self):
        """Sin lote SV: vacío; con lote F3.1: visible. Nunca consume secuencia."""
        guia = self._make_guia(name='VOL-SUG-SV')
        console = self._suggestions(guia)
        self.assertFalse(console.declared_sv_lot_id)

        seq = self.env['ir.sequence'].search(
            [('code', '=', 'madenat.volume.lot')], limit=1)
        number_before = seq.number_next if seq else None
        lots_before = self.StockLot.search_count(
            [('lot_flow_type', '=', 'volume')])

        # Compute + acción: sin efectos en lotes ni en la secuencia SV.
        console.action_apply_declared_volume_suggestions()
        self.assertEqual(
            self.StockLot.search_count([('lot_flow_type', '=', 'volume')]),
            lots_before, 'Las sugerencias no deben crear lotes')
        if seq:
            self.assertEqual(
                seq.number_next, number_before,
                'Las sugerencias no deben consumir la secuencia SV')

        # Con la etiqueta SV real (F3.1), el proxy la muestra.
        lot = self.StockLot.create({
            'name': 'SV00000000042',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
        })
        console = self._suggestions(guia)
        self.assertEqual(console.declared_sv_lot_id, lot)

    # ── 6. Arquitectura de la vista ───────────────────────────────────────
    def test_06_vista_sugerencias_placeholder_y_edicion(self):
        """Campos sugeridos, botón, placeholder SV y campos editables."""
        view = self.env.ref(CONSOLE_FORM)
        arch = view.arch
        root = etree.fromstring(arch)

        groups = root.xpath("//group[@string='DATOS DECLARADOS DE LA GUÍA']")
        self.assertEqual(len(groups), 1)
        group = groups[0]

        for field_name in ('suggested_widths_text', 'suggested_lengths_text',
                           'suggested_thickness_text', 'suggested_pieces',
                           'suggested_volume_m3', 'suggested_volume_source'):
            self.assertEqual(
                len(group.xpath(".//field[@name='%s']" % field_name)), 1,
                'Falta el campo %s en la cabecera declarada' % field_name)

        # El espesor no se sugiere visualmente: nodo presente pero invisible.
        thickness = group.xpath(
            ".//field[@name='suggested_thickness_text']")[0]
        self.assertEqual(thickness.get('invisible'), '1')

        buttons = group.xpath(
            ".//button[@name='action_apply_declared_volume_suggestions']")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(
            buttons[0].get('invisible'),
            'not suggested_widths_text and not suggested_lengths_text'
            ' and not suggested_pieces and not suggested_volume_m3')

        placeholders = group.xpath(".//div[@invisible='declared_sv_lot_id']")
        self.assertEqual(len(placeholders), 1)
        self.assertIn('Se asignará al enviar a stock',
                      placeholders[0].text or '')

        self.assertIn(
            'RW y RL se sugieren como designaciones comerciales; el espesor '
            'se registra según la documentación disponible.', arch)

        for field_name in ('declared_widths_text', 'declared_lengths_text',
                           'declared_thickness_text', 'declared_pieces',
                           'declared_volume_m3'):
            node = group.xpath(".//field[@name='%s']" % field_name)[0]
            self.assertFalse(
                node.get('readonly') in ('1', 'True', 'true'),
                'El campo declarado %s debe seguir editable' % field_name)
