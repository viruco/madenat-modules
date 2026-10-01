# -*- coding: utf-8 -*-
"""Volumen OFICIAL documental del Ingreso por Volúmenes (A + C + D).

Contrato verificado:

1. Precedencia canónica del volumen oficial (primer valor estrictamente
   positivo): `volume_pdf_m3` ("Guía PDF") → `volume_excel_m3`
   ("Packing Excel") → `packing_volume_declared_m3` ("Packing declarado").
2. La suma del detalle documental (`volume_detail_m3`) NUNCA es volumen
   oficial ni respaldo silencioso de stock.
3. `official_vs_detail_diff_m3` = volumen oficial - suma del detalle.
4. Sin fuente oficial positiva, F3.1 bloquea con el mensaje exacto
   "No existe volumen documental oficial para enviar a stock." y no crea ni
   reutiliza lote/picking.
5. Arquitectura de la consola de Volumen: tres bloques visibles («DATOS DE LA
   GUÍA», «DATOS DECLARADOS DE LA GUÍA» y «ETIQUETA SV»); sin volúmenes
   competidores; las acciones SV autorizadas viven en «ETIQUETA SV» y la acción
   «Modificar volumen oficial» queda en «DATOS DECLARADOS DE LA GUÍA», junto al
   volumen oficial VIGENTE (Fase 2, AD-80).
6. F3.1 usa el volumen oficial para el lote SV y para la cantidad del picking;
   el detalle no lo sobreescribe y el mecanismo de etiqueta SV no cambia.
7. Volumen oficial VIGENTE: con una regularización aplicada en la etiqueta SV
   rige el baseline regularizado (`source = "Regularización Operaciones"`); sin
   ella rige el volumen oficial documental de la Guía con su fuente.

Usa TransactionCase: nada se persiste. No toca la Guía 4495589 ni ningún lote
histórico existente.
"""

import base64

from lxml import etree
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

CONSOLE_FORM = 'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
DATOS_GUIA_GROUP = 'DATOS DE LA GUÍA'
DECLARED_GROUP = 'DATOS DECLARADOS DE LA GUÍA'
SV_GROUP = 'ETIQUETA SV'
AUDIT_GROUP = 'Control documental interno (auditoría)'
REGULARIZED_SOURCE = 'Regularización Operaciones'
NO_OFFICIAL_MSG = 'No existe volumen documental oficial para enviar a stock.'
SV_LABEL = r'^SV\d{11}$'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeOfficialVolume(TransactionCase):
    """Volumen oficial: precedencia, auditoría documental, consola y F3.1."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.DetailLine = cls.env['madenat.lumber.volume.detail.line']
        cls.StockLot = cls.env['stock.lot']
        cls.Picking = cls.env['stock.picking']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor Volumen Oficial', 'is_company': True})
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Volumen Oficial',
            'is_storable': True,
            'tracking': 'lot',
        })
        # Suma de líneas documentales del caso de negocio: 40,300 m³ en 12 filas
        # (mismos valores documentales que la Guía de referencia 4495589, sin
        # tocar esa guía real).
        cls.detail_values = (
            2.920, 2.700, 2.800, 2.640, 2.940, 4.190,
            4.180, 3.870, 2.840, 3.870, 4.030, 3.320,
        )

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, **extra):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'conciliation_status': 'not_compared',
            'guide_pdf_file': base64.b64encode(b'%PDF-fake'),
            'guide_pdf_filename': 'guia.pdf',
        }
        vals.update(extra)
        guia = self.Guia.create(vals)
        guia.invalidate_recordset()
        return guia

    def _add_detail(self, guia, values=None):
        for value in (values if values is not None else self.detail_values):
            self.DetailLine.create({
                'guia_id': guia.id, 'origin': 'pdf', 'volume_m3': value,
            })
        guia.invalidate_recordset()
        return guia

    def _make_volume_lot(self, guia, label, volume=40.300, piezas=1):
        """Crea la etiqueta SV real de la Guía (sin stock ni pickings)."""
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
        guia.invalidate_recordset()
        return lot

    def _console_for(self, guia):
        self.env.invalidate_all()
        return self.Console.search([
            ('source_model', '=', 'madenat.guia.processing'),
            ('source_res_id', '=', guia.id),
        ], limit=1)

    def _view_root(self):
        view = self.env.ref(CONSOLE_FORM)
        return etree.fromstring(view.arch)

    # ── 1. Precedencia canónica ────────────────────────────────────────────
    def test_01_precedencia_pdf_excel_packing(self):
        """Primer valor estrictamente positivo con su etiqueta exacta."""
        guia = self._make_guia('VOL-OFIC-PREC')
        self.assertEqual(guia.official_volume_m3, 0.0)
        self.assertFalse(guia.official_volume_source)

        guia.write({'packing_volume_declared_m3': 30.0})
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.official_volume_m3, 30.0, places=3)
        self.assertEqual(guia.official_volume_source, 'Packing declarado')

        guia.write({'volume_excel_m3': 20.0})
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.official_volume_m3, 20.0, places=3)
        self.assertEqual(guia.official_volume_source, 'Packing Excel')

        guia.write({'volume_pdf_m3': 40.315})
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertEqual(guia.official_volume_source, 'Guía PDF')

        # La API canónica devuelve exactamente (volumen, fuente).
        volume, source = guia.get_official_volume_m3()
        self.assertAlmostEqual(volume, 40.315, places=3)
        self.assertEqual(source, 'Guía PDF')

        # Un candidato negativo o cero nunca es oficial.
        guia.write({'volume_pdf_m3': -5.0})
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.official_volume_m3, 20.0, places=3)
        self.assertEqual(guia.official_volume_source, 'Packing Excel')

    # ── 2. El detalle nunca es volumen oficial ─────────────────────────────
    def test_02_detalle_nunca_es_oficial(self):
        """Ni el detalle, ni el operativo, ni el declarado, ni el comercial."""
        guia = self._add_detail(self._make_guia('VOL-OFIC-DETALLE'))
        self.assertAlmostEqual(guia.volume_detail_m3, 40.300, places=3)
        self.assertEqual(guia.official_volume_m3, 0.0)
        self.assertFalse(guia.official_volume_source)
        self.assertAlmostEqual(guia.official_vs_detail_diff_m3, 0.0, places=3)

        guia.write({
            'volume_operational_m3': 99.0,
            'volumen_declarado_m3': 98.0,
            'vol_comercial_pdf': 97.0,
        })
        guia.invalidate_recordset()
        self.assertEqual(guia.official_volume_m3, 0.0)
        self.assertFalse(guia.official_volume_source)

    # ── 3. Diferencia contra el volumen oficial ────────────────────────────
    def test_03_diferencia_vs_detalle(self):
        """official_vs_detail_diff_m3 = oficial - suma de líneas PDF."""
        guia = self._add_detail(self._make_guia(
            'VOL-OFIC-DIFF', volume_pdf_m3=40.315))
        self.assertAlmostEqual(guia.volume_detail_m3, 40.300, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertAlmostEqual(
            guia.official_vs_detail_diff_m3, 0.015, places=3)

        # Sin volumen oficial la diferencia es 0 aunque exista detalle.
        sin_oficial = self._add_detail(
            self._make_guia('VOL-OFIC-DIFF-0'), values=(1.0, 2.0))
        self.assertAlmostEqual(sin_oficial.volume_detail_m3, 3.0, places=3)
        self.assertEqual(sin_oficial.official_vs_detail_diff_m3, 0.0)

        # Editar el detalle recalcula la diferencia sin tocar el oficial.
        guia.volume_detail_line_ids[0].volume_m3 = 3.0  # +0.080
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.volume_detail_m3, 40.380, places=3)
        self.assertAlmostEqual(guia.official_volume_m3, 40.315, places=3)
        self.assertAlmostEqual(
            guia.official_vs_detail_diff_m3, -0.065, places=3)


    # ── 4. Sin volumen oficial: bloqueo antes de lote/picking ──────────────
    def test_04_sin_volumen_oficial_bloquea(self):
        """El detalle y el operativo no sustituyen al volumen oficial."""
        guia = self._add_detail(self._make_guia(
            'VOL-OFIC-BLOQ', volume_operational_m3=40.300))
        with self.assertRaises(ValidationError) as ctx:
            guia.action_validate()
        self.assertEqual(str(ctx.exception), NO_OFFICIAL_MSG)

        # Nada se creó ni se reutilizó.
        guia.invalidate_recordset()
        self.assertFalse(guia.lot_ids)
        self.assertFalse(guia.volume_lot_id)
        self.assertEqual(
            self.StockLot.search_count(
                [('volume_source_guia_id', '=', guia.id)]), 0)
        self.assertEqual(
            self.Picking.search_count([('origin', '=', guia.name)]), 0)

        # La consola bloquea con el mismo mensaje.
        errors, _warnings = self._console_for(
            guia)._get_ready_for_stock_diagnostics()
        self.assertIn(NO_OFFICIAL_MSG, errors)

    # ── 5. F3.1 usa el volumen oficial ─────────────────────────────────────
    def test_05_f3_1_usa_volumen_oficial(self):
        """Lote SV y cantidad de picking reciben el volumen oficial."""
        guia = self._add_detail(self._make_guia(
            'VOL-OFIC-F31', volume_pdf_m3=40.315,
            volume_operational_m3=40.300))
        # Mecanismo de etiqueta SV sin cambios: secuencia global, prefijo SV,
        # padding 11, sin rango de fechas y sin compañía.
        seq = self.env['ir.sequence'].search(
            [('code', '=', 'madenat.volume.lot')], limit=1)
        self.assertTrue(seq, 'Debe existir la secuencia madenat.volume.lot')
        self.assertEqual(seq.code, 'madenat.volume.lot')
        self.assertEqual(seq.prefix, 'SV')
        self.assertEqual(seq.padding, 11)
        self.assertFalse(seq.use_date_range)
        self.assertFalse(seq.company_id)

        guia.action_validate()
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'validated')

        lot = guia.lot_ids
        self.assertEqual(len(lot), 1)
        # Mecanismo de etiqueta SV intacto.
        self.assertRegex(lot.name, SV_LABEL)
        self.assertEqual(lot.lot_flow_type, 'volume')
        self.assertEqual(lot.volume_source_guia_id, guia)
        # Volumen oficial en los campos autoritativos del lote.
        self.assertAlmostEqual(lot.volume_purchase_m3, 40.315, places=3)
        self.assertAlmostEqual(lot.vol_shipment_m3, 40.315, places=3)
        self.assertAlmostEqual(lot.volumen_m3, 40.315, places=3)
        # El detalle (40,300) no sobreescribe al oficial.
        self.assertNotAlmostEqual(lot.volumen_m3, 40.300, places=3)

        picking = self.Picking.search([('origin', '=', guia.name)])
        self.assertEqual(len(picking), 1)
        self.assertAlmostEqual(
            picking.move_ids.product_uom_qty, 40.315, places=3)
        self.assertAlmostEqual(
            sum(picking.move_line_ids.mapped('quantity')), 40.315, places=3)
        self.assertEqual(picking.move_line_ids.lot_id, lot)
        # La etiqueta proviene de la secuencia: SV + 11 dígitos.
        self.assertTrue(lot.name.startswith('SV'))
        self.assertEqual(len(lot.name), 13)
        self.assertTrue(lot.name[2:].isdigit())


    # ── 6. Arquitectura de la consola ──────────────────────────────────────
    def test_06_consola_arquitectura_volumen(self):
        """Tres bloques visibles; el volumen oficial vigente es el primero."""
        root = self._view_root()

        # D3: los tres bloques visibles existen con sus títulos exactos.
        for title in (DATOS_GUIA_GROUP, DECLARED_GROUP, SV_GROUP):
            self.assertTrue(
                root.xpath("//group[@string='%s']" % title),
                'Falta el bloque %s' % title)

        # El bloque declarado encabeza con el volumen oficial VIGENTE y solo
        # la muestra una vez en toda la ficha.
        declared = root.xpath("//group[@string='%s']" % DECLARED_GROUP)
        self.assertEqual(len(declared), 1, 'Falta el bloque declarado')
        self.assertEqual(
            declared[0].get('invisible'), "ingestion_type != 'volume'")
        declared_fields = [f.get('name') for f in declared[0].xpath('.//field')]
        self.assertEqual(
            declared_fields[0], 'official_volume_effective_m3',
            'El volumen oficial vigente debe ser el primer campo del bloque')
        for field_name in ('official_volume_effective_m3',
                           'official_volume_effective_source'):
            self.assertEqual(
                len(root.xpath("//field[@name='%s']" % field_name)), 1,
                '%s debe mostrarse una sola vez' % field_name)

        # Los cuatro datos declarados operativos siguen editables.
        for field_name in ('declared_pieces', 'declared_widths_text',
                           'declared_lengths_text', 'declared_thickness_text',
                           'declared_sv_lot_id'):
            nodes = declared[0].xpath(".//field[@name='%s']" % field_name)
            self.assertEqual(
                len(nodes), 1, 'Campo declarado %s ausente' % field_name)
        for field_name in ('declared_pieces', 'declared_widths_text',
                           'declared_lengths_text', 'declared_thickness_text'):
            node = declared[0].xpath(".//field[@name='%s']" % field_name)[0]
            self.assertFalse(
                node.get('readonly') in ('1', 'True', 'true'),
                'El campo declarado %s debe seguir editable' % field_name)

        # RW/RL, botón de sugerencias y placeholder SV sin cambios.
        for field_name in ('suggested_widths_text', 'suggested_lengths_text',
                           'suggested_thickness_text'):
            self.assertEqual(
                len(declared[0].xpath(".//field[@name='%s']" % field_name)),
                1, 'Falta el nodo %s' % field_name)
        self.assertEqual(
            len(declared[0].xpath(
                ".//button[@name='action_apply_declared_volume_suggestions']")),
            1)
        placeholders = declared[0].xpath(
            ".//div[@invisible='declared_sv_lot_id']")
        self.assertEqual(len(placeholders), 1)
        self.assertIn('Se asignará al enviar a stock',
                      placeholders[0].text or '')

        # El M³ declarado por Operaciones queda retirado de la pantalla.
        declared_volume = root.xpath("//field[@name='declared_volume_m3']")[0]
        self.assertIn(
            "ingestion_type == 'volume'",
            declared_volume.get('invisible') or '')

        # Control documental interno retirado: nodos y leyenda conservados.
        audit = root.xpath("//group[@string='%s']" % AUDIT_GROUP)
        self.assertEqual(len(audit), 1, 'Falta el nodo de control documental')
        self.assertEqual(audit[0].get('invisible'), '1')
        audit_fields = [f.get('name') for f in audit[0].xpath('.//field')]
        self.assertIn('volume_detail_m3', audit_fields)
        self.assertIn('official_vs_detail_diff_m3', audit_fields)
        self.assertIn(
            'El detalle es evidencia documental y no',
            etree.tostring(audit[0], encoding='unicode'))

        # Bloque 1: OC documento (proxy) ≠ OC vinculada ≠ Estado OC.
        documentary = root.xpath("//group[@string='%s']" % DATOS_GUIA_GROUP)
        self.assertEqual(
            len(documentary), 1, 'Falta el bloque DATOS DE LA GUÍA')
        for field_name in ('oc_reference_documental', 'purchase_id',
                           'oc_documentary_status'):
            self.assertEqual(
                len(documentary[0].xpath(
                    ".//field[@name='%s']" % field_name)), 1,
                'Falta %s en el bloque DATOS DE LA GUÍA' % field_name)
        self.assertEqual(
            len(documentary[0].xpath(".//field[@name='oc_pending']")), 0,
            'El bloque DATOS DE LA GUÍA no debe repetir el estado OC operativo')

        # El bloque oficial crudo queda conservado, fuera de la pantalla.
        primary = root.xpath("//group[@string='VOLUMEN OFICIAL DE LA GUÍA']")
        self.assertEqual(len(primary), 1, 'Falta el nodo oficial conservado')
        self.assertEqual(primary[0].get('invisible'), '1')
        self.assertEqual(
            sorted(f.get('name') for f in primary[0].xpath('.//field')),
            ['official_volume_m3', 'official_volume_source'])

        # Los saldos SV técnicos no compiten: quedan ocultos en su bloque.
        for field_name in ('sv_original_volume_m3',
                           'sv_regularized_baseline_m3',
                           'sv_rebajado_m3', 'sv_available_m3'):
            node = root.xpath("//field[@name='%s']" % field_name)[0]
            self.assertEqual(
                node.get('invisible'), '1',
                '%s debe quedar oculto' % field_name)

        # Encabezado: sin agregado competitivo "Volumen:" para Volume y con el
        # agregado de volumen total oculto para Volumen.
        for span in root.xpath("//span"):
            self.assertNotEqual(
                (span.text or '').strip(), 'Volumen:',
                'El encabezado no debe ofrecer el agregado «Volumen:»')
        for indicator in root.xpath("//div[contains(@class, 'indicator')]"):
            self.assertNotIn(
                '>Volumen:<',
                etree.tostring(indicator, encoding='unicode'))
        aggregates = root.xpath("//field[@name='total_volume_m3']")
        self.assertEqual(
            len(aggregates), 1, 'Falta el nodo total_volume_m3')
        self.assertIn(
            "ingestion_type == 'volume'",
            aggregates[0].getparent().get('invisible'),
            'El agregado de volumen total no debe mostrarse en Volumen')

    # ── 12. Botón «Modificar volumen oficial» (D2) ─────────────────────────
    def test_12_boton_modificar_volumen_oficial(self):
        """Una sola instancia, junto al volumen vigente y fuera de ETIQUETA SV."""
        root = self._view_root()

        buttons = root.xpath("//button[@name='action_sv_regularize_volume']")
        self.assertEqual(
            len(buttons), 1,
            'Debe existir una sola instancia del botón de volumen oficial')
        button = buttons[0]
        self.assertEqual(button.get('type'), 'object')
        self.assertEqual(button.get('string'), 'Modificar volumen oficial')

        # Vive en el bloque declarado, junto al volumen oficial vigente.
        declared = root.xpath("//group[@string='%s']" % DECLARED_GROUP)[0]
        self.assertEqual(
            len(declared.xpath(
                ".//button[@name='action_sv_regularize_volume']")),
            1,
            'El botón debe estar en el bloque DATOS DECLARADOS DE LA GUÍA')
        # Oculto cuando no existe lote SV real (misma guarda del bloque SV).
        self.assertEqual(
            button.get('invisible'), 'not declared_sv_lot_id',
            'El botón debe ocultarse sin lote SV')

        # NO se repite en el bloque «ETIQUETA SV».
        sv_blocks = root.xpath("//group[@string='%s']" % SV_GROUP)
        self.assertEqual(
            len(sv_blocks), 2, 'Faltan los dos estados de ETIQUETA SV')
        for block in sv_blocks:
            self.assertFalse(
                block.xpath(
                    ".//button[@name='action_sv_regularize_volume']"),
                'El botón no debe aparecer en el bloque ETIQUETA SV')

        # El wizard canónico del Programa SV no cambió.
        wizard = 'madenat.sv.volume.regularize.wizard'
        self.assertIn(wizard, self.env, 'Falta el wizard canónico de SV')
        self.assertEqual(
            self.env[wizard]._name, 'madenat.sv.volume.regularize.wizard')

    # ── 13. Volumen oficial vigente (D1) ───────────────────────────────────
    def test_13_volumen_oficial_vigente(self):
        """Documental sin regularización; regularizado con operación aplicada."""
        guia = self._make_guia('VOL-OFIC-VIGENTE', volume_pdf_m3=40.315)
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        self.assertAlmostEqual(
            console.official_volume_effective_m3, 40.315, places=3)
        self.assertEqual(
            console.official_volume_effective_source, 'Guía PDF')
        self.assertFalse(console.sv_regularization_applied)

        # Con lote SV sin regularización rige el volumen documental.
        lot = self._make_volume_lot(guia, 'SV00000000501', volume=40.300)
        console = self._console_for(guia)
        self.assertEqual(console.declared_sv_lot_id, lot)
        self.assertAlmostEqual(
            console.official_volume_effective_m3, 40.315, places=3)
        self.assertEqual(
            console.official_volume_effective_source, 'Guía PDF')

        # Regularización APLICADA (hacia abajo: sin escalamiento adicional).
        self.env['madenat.sv.volume.regularize.wizard'].create({
            'lot_id': lot.id,
            'new_volume_m3': 39.0,
            'reason': 'Ajuste documental verificado',
            'evidence_reference': 'PDF-TEST-VIGENTE',
        }).action_submit()
        operation = self.Operation.search([
            ('lot_id', '=', lot.id),
            ('action_type', '=', 'regularize_volume'),
        ], limit=1)
        self.assertEqual(
            operation.state, 'applied',
            'La regularización debe quedar aplicada para regir el baseline')

        console = self._console_for(guia)
        self.assertTrue(console.sv_regularization_applied)
        self.assertAlmostEqual(
            console.official_volume_effective_m3, 39.0, places=3)
        self.assertEqual(
            console.official_volume_effective_source, REGULARIZED_SOURCE)
        # El volumen oficial documental de la Guía no se modifica.
        self.assertAlmostEqual(console.official_volume_m3, 40.315, places=3)
        self.assertEqual(console.official_volume_source, 'Guía PDF')
        guia.invalidate_recordset()
        self.assertAlmostEqual(guia.volume_pdf_m3, 40.315, places=3)

    # ── 14. Campos vigentes no almacenados ─────────────────────────────────
    def test_14_campos_vigentes_no_almacenados(self):
        """Los dos campos del volumen vigente son computados y readonly."""
        for field_name in ('official_volume_effective_m3',
                           'official_volume_effective_source'):
            field = self.Console._fields[field_name]
            self.assertTrue(
                field.compute, '%s debe ser computado' % field_name)
            self.assertFalse(
                field.store, '%s no debe almacenarse' % field_name)
            self.assertTrue(
                field.readonly, '%s debe ser readonly' % field_name)

    # ── 7. Proxies de la consola ───────────────────────────────────────────
    def test_07_consola_proxies_oficiales(self):
        """La consola expone el oficial de la guía sin duplicar precedencia."""
        guia = self._add_detail(self._make_guia(
            'VOL-OFIC-CONS', volume_pdf_m3=40.315))
        console = self._console_for(guia)
        self.assertTrue(console)
        self.assertEqual(console.ingestion_type, 'volume')
        self.assertAlmostEqual(console.official_volume_m3, 40.315, places=3)
        self.assertEqual(console.official_volume_source, 'Guía PDF')
        self.assertAlmostEqual(
            console.official_vs_detail_diff_m3, 0.015, places=3)
        # Los proxies legacy siguen definidos para compatibilidad.
        self.assertAlmostEqual(
            console.volumen_pdf_m3, console.official_volume_m3, places=3)

        # Guía no-Volumen: proxies oficiales neutros.
        compra = self._make_guia('VOL-OFIC-COMPRA', tipo_recepcion='compra')
        console_compra = self._console_for(compra)
        if console_compra:
            self.assertEqual(console_compra.official_volume_m3, 0.0)
            self.assertFalse(console_compra.official_volume_source)

    # ── 8. La consola nunca escribe en la guía ─────────────────────────────
    def test_08_consola_readonly_no_escribe(self):
        """Leer el oficial no muta guía, lote, picking ni secuencia."""
        guia = self._add_detail(self._make_guia(
            'VOL-OFIC-RO', volume_pdf_m3=40.315), values=(1.0, 2.0))
        before = {
            'write_date': guia.write_date,
            'volume_pdf_m3': guia.volume_pdf_m3,
            'volume_operational_m3': guia.volume_operational_m3,
            'volumen_declarado_m3': guia.volumen_declarado_m3,
        }
        lots_before = self.StockLot.search_count(
            [('lot_flow_type', '=', 'volume')])

        # Leer el oficial nunca acuña una etiqueta SV (la secuencia no se toca).
        with patch.object(
                type(self.StockLot), '_next_volume_lot_label',
                side_effect=AssertionError('la consola no debe acuñar SV')) as spy:
            console = self._console_for(guia)
            self.assertAlmostEqual(console.official_volume_m3, 40.315, places=3)
            self.assertAlmostEqual(
                self._console_for(guia).official_vs_detail_diff_m3, 37.315,
                places=3)
        spy.assert_not_called()

        guia.invalidate_recordset()
        self.assertEqual(guia.write_date, before['write_date'])
        self.assertAlmostEqual(
            guia.volume_pdf_m3, before['volume_pdf_m3'], places=3)
        self.assertAlmostEqual(
            guia.volume_operational_m3, before['volume_operational_m3'], places=3)
        self.assertAlmostEqual(
            guia.volumen_declarado_m3, before['volumen_declarado_m3'], places=3)
        self.assertEqual(
            self.StockLot.search_count([('lot_flow_type', '=', 'volume')]),
            lots_before)

    # ── 9. Coherencia del campo computado (no almacenado) ──────────────────
    def test_09_campos_oficiales_no_almacenados(self):
        """Los tres campos oficiales son computados, no almacenados y readonly."""
        for field_name in ('official_volume_m3', 'official_volume_source',
                           'official_vs_detail_diff_m3'):
            field = self.Guia._fields[field_name]
            self.assertTrue(
                field.compute, '%s debe ser computado' % field_name)
            self.assertFalse(
                field.store, '%s no debe almacenarse' % field_name)
            self.assertTrue(
                field.readonly, '%s debe ser readonly' % field_name)

    # ── 10. Proxies documentales de OC (D1/D2) ─────────────────────────────
    def test_10_proxies_documentales_disponibles(self):
        """Proxies OC readonly, no almacenados y con tres estados."""
        for field_name in ('oc_reference_documental', 'oc_documentary_status'):
            field = self.Console._fields[field_name]
            self.assertTrue(
                field.compute, '%s debe ser computado' % field_name)
            self.assertFalse(
                field.store, '%s no debe almacenarse' % field_name)
            self.assertTrue(
                field.readonly, '%s debe ser readonly' % field_name)
        sv_flag = self.Console._fields['sv_regularization_applied']
        self.assertTrue(sv_flag.compute)
        self.assertFalse(sv_flag.store)
        self.assertTrue(sv_flag.readonly)
        self.assertEqual(
            [value for value, _label in
             self.Console._fields['oc_documentary_status'].selection],
            ['linked', 'pending', 'not_informed'])
        # D1: el campo operativo `oc_pending` NO se modifica.
        self.assertEqual(
            [value for value, _label in
             self.Console._fields['oc_pending'].selection],
            ['linked', 'pending'])

    # ── 11. Estado OC documental sin inventar datos (D2) ───────────────────
    def test_11_estado_oc_documental_sin_inventar(self):
        """Vacío → not_informed; referencia documental → pending; OC → linked."""
        guia = self._make_guia('VOL-OC-DOC', volume_pdf_m3=40.315)
        console = self._console_for(guia)
        self.assertTrue(console, 'La consola debe exponer la guía')
        self.assertFalse(console.oc_reference_documental)
        self.assertEqual(console.oc_documentary_status, 'not_informed')

        # La referencia documental se lee tal cual: sin copiar ni inferir.
        guia.write({'oc_reference_raw': 'OC-TEST-0001'})
        guia.flush_recordset()
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(console.oc_reference_documental, 'OC-TEST-0001')
        self.assertEqual(console.oc_documentary_status, 'pending')

        # Con OC interna vinculada el estado es 'linked' y la referencia
        # documental del documento NUNCA se sobrescribe.
        po = self.env['purchase.order'].create({'partner_id': self.partner.id})
        guia.write({'order_id': po.id})
        guia.flush_recordset()
        self.env.invalidate_all()
        console = self._console_for(guia)
        self.assertEqual(console.oc_documentary_status, 'linked')
        self.assertEqual(console.oc_reference_documental, 'OC-TEST-0001')
        guia.invalidate_recordset()
        self.assertEqual(guia.oc_reference_raw, 'OC-TEST-0001')

