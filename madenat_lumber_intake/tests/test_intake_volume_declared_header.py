# -*- coding: utf-8 -*-
"""Cabecera declarada de la Guía en la Consola de Ingreso (solo Volúmenes).

Cubre el contrato de los proxies NO almacenados de
`madenat.lumber.intake.console` hacia `madenat.guia.processing` (AD-78):

1. Lectura de los cinco datos declarados persistidos en la Guía.
2. Inverse: escribe solo esos cinco campos en la Guía origen.
3. No-volume: proxies vacíos y ninguna escritura sobre el origen.
4. Etiqueta SV: proxy de solo lectura alineado con `volume_lot_id` (F3.1).
5. Arquitectura de vista: bloque «DATOS DECLARADOS DE LA GUÍA» solo volumen,
   con los datos declarados editables y la etiqueta SV sin duplicar.

No ejecuta la validación de intake, no crea pickings ni escribe stock.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeVolumeDeclaredHeader(TransactionCase):
    """Proxies de cabecera declarada (Volumen) en la consola de intake."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Declarado Volumen', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Declarado Volumen',
            'is_storable': True,
            'tracking': 'lot',
        })

        # Valores declarados persistidos en la Guía (campos del core).
        cls.guia_vals = {
            'anchos_variables': 'RW / 4 1/2 - 6 1/4',
            'largos_variables': 'RL / 8 - 12',
            'espesor_nominal_texto': '7/4',
            'piezas_declaradas': 124,
            'volumen_declarado_m3': 57.125,
        }
        # Valores escritos sobre los proxies de la consola.
        cls.proxy_vals = {
            'declared_widths_text': 'RW / 4 1/2 - 6 1/4',
            'declared_lengths_text': 'RL / 8 - 12',
            'declared_thickness_text': '7/4',
            'declared_pieces': 124,
            'declared_volume_m3': 57.125,
        }
        cls.editable_proxies = [
            'declared_widths_text',
            'declared_lengths_text',
            'declared_thickness_text',
            'declared_pieces',
            'declared_volume_m3',
        ]

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, tipo='granel', name=None, **extra):
        """Crea una Guía mínima (sin flujo de stock ni de documentos)."""
        vals = {
            'name': name or 'VOL-DECL-%s' % tipo.upper(),
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo,
            'state': 'draft',
        }
        vals.update(extra)
        return self.Guia.create(vals)

    def _console_for(self, guia):
        """Registro de consola que resuelve a la Guía (misma vista SQL)."""
        guia.flush_recordset()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _make_volume_lot(self, guia, name='SV00000000009'):
        """Etiqueta SV de la guía (identidad documental F3.1, sin validar)."""
        return self.StockLot.create({
            'name': name,
            'product_id': self.product.id,
            'company_id': self.env.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
        })

    # ── 1. Lectura de los proxies (Volumen) ───────────────────────────────
    def test_01_lectura_proxies_volumen(self):
        """Los cinco proxies leen los valores declarados de la Guía."""
        guia = self._make_guia(**self.guia_vals)
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía creada')
        self.assertEqual(console.ingestion_type, 'volume')
        self.assertEqual(console.declared_widths_text, guia.anchos_variables)
        self.assertEqual(console.declared_lengths_text, guia.largos_variables)
        self.assertEqual(console.declared_thickness_text,
                         guia.espesor_nominal_texto)
        self.assertEqual(console.declared_pieces, guia.piezas_declaradas)
        self.assertEqual(console.declared_volume_m3,
                         guia.volumen_declarado_m3)
        # Sin lote SV creado, el proxy de etiqueta queda vacío.
        self.assertFalse(console.declared_sv_lot_id)

    # ── 2. Inverse: escribe solo los cinco campos declarados ──────────────
    def test_02_inverse_escribe_solo_campos_declarados(self):
        """El inverse actualiza la Guía y no toca estado ni otros campos."""
        guia = self._make_guia(name='VOL-DECL-INVERSE')
        console = self._console_for(guia)
        self.assertTrue(console)

        console.write(dict(self.proxy_vals))

        guia.invalidate_recordset()
        for guia_field, expected in self.guia_vals.items():
            self.assertEqual(
                guia[guia_field], expected,
                'Campo declarado %s no persistido en la Guía' % guia_field)
        # Nada más cambia en la guía origen.
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertEqual(guia.state, 'draft')
        self.assertEqual(guia.partner_id, self.partner)
        self.assertFalse(guia.order_id)
        self.assertFalse(guia.processing_line_ids)
        self.assertFalse(guia.volume_lot_id)
        self.assertEqual(guia.volume_operational_m3, 0.0)
        self.assertEqual(guia.conciliation_status, 'not_compared')

    # ── 3. Seguridad fuera de Volumen ─────────────────────────────────────
    def test_03_no_volume_proxies_vacios_y_sin_escritura(self):
        """Registros no-volume: proxies vacíos y ninguna escritura al origen."""
        guia = self._make_guia(tipo='compra', name='VOL-DECL-COMPRA')
        console = self._console_for(guia)
        self.assertTrue(console)
        self.assertEqual(console.ingestion_type, 'processed')

        self.assertFalse(console.declared_widths_text)
        self.assertFalse(console.declared_lengths_text)
        self.assertFalse(console.declared_thickness_text)
        self.assertEqual(console.declared_pieces, 0)
        self.assertEqual(console.declared_volume_m3, 0.0)
        self.assertFalse(console.declared_sv_lot_id)

        console.write(dict(self.proxy_vals))

        guia.invalidate_recordset()
        self.assertFalse(guia.anchos_variables)
        self.assertFalse(guia.largos_variables)
        self.assertFalse(guia.espesor_nominal_texto)
        self.assertFalse(guia.piezas_declaradas)
        self.assertEqual(guia.volumen_declarado_m3, 0.0)
        self.assertEqual(guia.tipo_recepcion, 'compra')
        self.assertEqual(guia.state, 'draft')

    # ── 4. Proxy de la etiqueta SV (solo lectura) ─────────────────────────
    def test_04_proxy_etiqueta_sv_solo_lectura(self):
        """declared_sv_lot_id refleja volume_lot_id y no admite escritura."""
        guia = self._make_guia(name='VOL-DECL-SV')
        lot = self._make_volume_lot(guia)
        console = self._console_for(guia)
        self.assertTrue(console)

        self.env.invalidate_all()
        guia.invalidate_recordset()
        self.assertEqual(guia.volume_lot_id, lot)
        self.assertEqual(console.declared_sv_lot_id, guia.volume_lot_id)
        self.assertEqual(console.declared_sv_lot_id, lot)

        # Proxy de solo lectura (sin inverse): ningún efecto sobre la Guía.
        # Odoo puede rechazar el write o ignorarlo en caché; el invariante es
        # que la etiqueta SV real permanece intacta.
        try:
            console.write({'declared_sv_lot_id': False})
        except Exception:  # noqa: BLE001 — proxy readonly, sin inverse
            pass
        guia.invalidate_recordset()
        self.assertEqual(guia.volume_lot_id, lot)
        self.env.invalidate_all()
        self.assertEqual(console.declared_sv_lot_id, lot)

    # ── 5. Arquitectura de la vista de consola ────────────────────────────
    def test_05_vista_grupo_declarado_solo_volumen(self):
        """El bloque declarado es solo-volumen, editable y sin repetir la SV."""
        view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form')
        root = etree.fromstring(view.arch)

        groups = root.xpath("//group[@string='DATOS DECLARADOS DE LA GUÍA']")
        self.assertEqual(
            len(groups), 1, 'Falta el bloque DATOS DECLARADOS DE LA GUÍA')
        group = groups[0]
        self.assertEqual(
            group.get('invisible'), "ingestion_type != 'volume'")

        for field_name in self.editable_proxies + ['declared_sv_lot_id']:
            nodes = group.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(
                len(nodes), 1,
                'Campo %s ausente del bloque declarado' % field_name)

        # Los cuatro datos declarados operativos siguen editables (D3).
        for field_name in ('declared_pieces', 'declared_widths_text',
                           'declared_lengths_text', 'declared_thickness_text'):
            nodes = group.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(
                len(nodes), 1,
                'Campo declarado %s ausente del bloque' % field_name)
            self.assertFalse(
                nodes[0].get('readonly') in ('1', 'True', 'true'),
                'El campo declarado %s no debe ser readonly' % field_name)

        # El M³ declarado por Operaciones queda retirado de la pantalla
        # operativa (nodo conservado con invisible aplicado).
        volume = group.xpath(".//field[@name='declared_volume_m3']")[0]
        self.assertIn("ingestion_type == 'volume'", volume.get('invisible') or '')

        sv = group.xpath(".//field[@name='declared_sv_lot_id']")[0]
        self.assertIn(
            sv.get('readonly'), ('1', 'True', 'true'),
            'declared_sv_lot_id debe ser readonly en la consola')
        self.assertEqual(
            sv.get('invisible'), '1',
            'declared_sv_lot_id debe seguir invisible (etiqueta SV única)')
