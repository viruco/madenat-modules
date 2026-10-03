# -*- coding: utf-8 -*-
"""VOL — Cabecera declarada de Guías por Volumen (tipo_recepcion == 'granel').

Contrato cubierto:
1. Los cinco campos documentales se guardan y se leen sin alteración y sin
   crear líneas de detalle (processing_line_ids).
2. Siguen siendo editables en estado 'validated' sin tocar la lógica del
   modelo ni los volúmenes calculados.
3. El accesor de la etiqueta SV única (F3.1) es de solo lectura y localiza el
   lote por identidad documental (volume_source_guia_id + lot_flow_type).
4. Metadatos: opcionales, sin compute y con digits=(16, 3) en el volumen.
5. Arquitectura de vista: página 'volume_reception_header' condicional y grids
   de detalle operativo ocultos SOLO para volumen.

No ejecuta el flujo de stock/picking: no crea movimientos ni cantidades, y no
modifica datos históricos.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestVolumeGuideHeader(TransactionCase):
    """Cabecera declarada + etiqueta SV única en la Guía por Volumen."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']

        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id

        cls.partner = cls.env['res.partner'].create(
            {'name': 'VOL Header Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'VOL Header Storable',
            'is_storable': True,
            'tracking': 'lot',
        })

        cls.declared_vals = {
            'anchos_variables': '4 1/2 - 6 1/4',
            'largos_variables': '8 - 12',
            'espesor_nominal_texto': '7/4',
            'piezas_declaradas': 124,
            'volumen_declarado_m3': 57.125,
        }
        cls.document_fields = [
            'anchos_variables',
            'largos_variables',
            'espesor_nominal_texto',
            'piezas_declaradas',
            'volumen_declarado_m3',
        ]

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, tipo='granel', name=None):
        """Crea una Guía mínima (sin flujo de stock ni de documentos)."""
        return self.GuiaModel.create({
            'name': name or 'VOL-%s' % tipo.upper(),
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'tipo_recepcion': tipo,
            'state': 'draft',
        })

    def _make_volume_lot(self, guia, name='SV00000000001'):
        """Crea la etiqueta SV de la guía (identidad documental F3.1)."""
        return self.StockLot.create({
            'name': name,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'lot_flow_type': 'volume',
            'volume_source_guia_id': guia.id,
        })

    def _merged_form_arch(self):
        """Arch combinada (herencias aplicadas) del form de la Guía."""
        form_view = self.env.ref(
            'madenat_lumber_core.view_madenat_guia_processing_form')
        return self.GuiaModel.get_view(
            view_id=form_view.id, view_type='form')['arch']

    # ── 1. Campos documentales editables ──────────────────────────────────
    def test_01_campos_declarados_sin_crear_detalle(self):
        """Los cinco campos se guardan/leen sin crear detalle operativo."""
        guia = self._make_guia()
        self.assertFalse(guia.processing_line_ids)
        guia.write(self.declared_vals)
        for field_name, expected in self.declared_vals.items():
            self.assertEqual(
                guia[field_name], expected,
                'Campo %s alterado tras la escritura' % field_name)
        self.assertFalse(
            guia.processing_line_ids,
            'La cabecera declarada no debe crear detalle operativo')

    # ── 2. Edición no bloqueante post-validación ──────────────────────────
    def test_02_edicion_no_bloqueante_post_validacion(self):
        """En 'validated' la escritura sigue permitida y no altera cálculos."""
        guia = self._make_guia(name='VOL-POST-VALIDATED')
        guia.write({'state': 'validated'})
        vol_comercial = guia.vol_comercial
        vol_fisico = guia.vol_fisico

        guia.write(self.declared_vals)  # No debe lanzar excepción.

        self.assertEqual(guia.state, 'validated')
        for field_name, expected in self.declared_vals.items():
            self.assertEqual(
                guia[field_name], expected,
                'Campo %s no editable tras validar' % field_name)
        self.assertFalse(
            guia.processing_line_ids,
            'La edición documental no debe crear ni tocar el detalle')
        self.assertEqual(
            guia.vol_comercial, vol_comercial,
            'La cabecera declarada no debe alterar el volumen comercial')
        self.assertEqual(
            guia.vol_fisico, vol_fisico,
            'La cabecera declarada no debe alterar el volumen físico')

    # ── 3. Accesor de la etiqueta SV única ────────────────────────────────
    def test_03_accesor_etiqueta_sv_unica(self):
        """volume_lot_id localiza la única etiqueta SV de la guía granel."""
        guia = self._make_guia(name='VOL-SV-ACCESSOR')
        self.assertFalse(guia.volume_lot_id)
        lot = self._make_volume_lot(guia)
        # El lote se creó fuera de la guía: en producción F3.1 escribe lot_ids
        # e invalida la caché; aquí se refresca explícitamente.
        self.env.invalidate_all()
        self.assertEqual(guia.volume_lot_id, lot)
        self.assertEqual(guia.volume_lot_id.lot_flow_type, 'volume')

        guia_compra = self._make_guia(tipo='compra', name='VOL-SV-COMPRA')
        self.assertFalse(
            guia_compra.volume_lot_id,
            'Una guía no-granel nunca expone etiqueta SV')

    # ── 4. Metadatos de los campos ────────────────────────────────────────
    def test_04_metadatos_campos_declarados(self):
        """Opcionales, sin compute/related/default; volumen con digits."""
        for field_name in self.document_fields:
            field = self.GuiaModel._fields[field_name]
            self.assertFalse(
                field.required, '%s no debe ser obligatorio' % field_name)
            self.assertFalse(
                field.compute, '%s no debe tener compute' % field_name)
            self.assertFalse(
                field.related, '%s no debe ser related' % field_name)
            self.assertFalse(
                field.default, '%s no debe tener default' % field_name)
        # Odoo 18 expone la precisión de un campo Float mediante get_digits(env);
        # el atributo público `.digits` no existe (el valor interno es `_digits`).
        self.assertEqual(
            self.GuiaModel._fields['volumen_declarado_m3'].get_digits(self.env),
            (16, 3))
        self.assertEqual(
            self.GuiaModel._fields['volume_lot_id'].compute,
            '_compute_volume_lot_id')

    # ── 5. Arquitectura de la vista ───────────────────────────────────────
    def test_05_arquitectura_vista_volumen(self):
        """Página condicional de volumen y grids de detalle condicionales."""
        arch = self._merged_form_arch()
        root = etree.fromstring(
            arch if isinstance(arch, bytes) else arch.encode('utf-8'))

        pages = root.xpath("//page[@name='volume_reception_header']")
        self.assertEqual(
            len(pages), 1, 'Falta la página volume_reception_header')
        page = pages[0]
        self.assertIn(
            "tipo_recepcion != 'granel'",
            etree.tostring(page, encoding='unicode'),
            'La página de volumen debe ser condicional a granel')

        for field_name in self.document_fields + ['volume_lot_id', 'volume_lot_ids']:
            nodes = page.xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(
                len(nodes), 1,
                'Campo %s ausente de la página de volumen' % field_name)
            if field_name in self.document_fields:
                self.assertFalse(
                    nodes[0].get('readonly') in ('1', 'True', 'true'),
                    'El campo declarado %s no debe ser readonly' % field_name)

        arch_text = arch if isinstance(arch, str) else arch.decode('utf-8')
        self.assertIn(
            'Los valores corresponden a la información declarada en la Guía.',
            arch_text)
        self.assertIn(
            'Son referenciales, no se calculan ni bloquean la recepción.',
            arch_text)
        self.assertIn(
            'Pueden ajustarse posteriormente según la documentación disponible.',
            arch_text)
        self.assertIn(
            'Una Guía por Volumen genera una etiqueta SV por cada línea.', arch_text)

        # Los tres grids de detalle operativo son condicionales a volumen.
        for page_name in ('physical_reception', 'commercial_analysis',
                          'export_view'):
            nodes = root.xpath(
                "//page[@name='%s']//field[@name='processing_line_ids']"
                % page_name)
            self.assertEqual(
                len(nodes), 1,
                'Grid de detalle no localizado en la página %s' % page_name)
            self.assertIn(
                "tipo_recepcion == 'granel'",
                etree.tostring(nodes[0], encoding='unicode'),
                'El grid de %s debe ocultarse solo para volumen' % page_name)
