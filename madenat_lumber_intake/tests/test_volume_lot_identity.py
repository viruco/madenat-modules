# -*- coding: utf-8 -*-
"""F3.1 — Identidad única (SV) de los Lotes Volumen del Ingreso por Volúmenes.

Contrato verificado:
- Cada Lote Volumen nuevo recibe una etiqueta global `SV` + 11 dígitos.
- `volume_source_guia_id` es la identidad documental permanente de la guía.
- La reapertura de la guía NO destruye esa identidad.
- La revalidación reutiliza el mismo lote: nunca se acuña una segunda SV.
- Los lotes históricos `GRANEL <sufijo>` quedan intactos y nunca se adoptan.

Usa TransactionCase: nada se persiste.
"""

import base64

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

SV_LABEL = r'^SV\d{11}$'


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestVolumeLotIdentity(TransactionCase):
    """F3.1 — Etiqueta SV e identidad documental del Lote Volumen."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.assertTrue(cls.location, 'Se requiere stock.location interno')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Volumen Identidad S.A.', 'is_company': True,
        })

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_guia(self, name, operational=10.0):
        return self.Guia.create({
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'verified',
            'tipo_recepcion': 'granel',
            'date_emission': '2026-09-24',
            'volume_operational_m3': operational,
            # Volumen OFICIAL documental (Guía PDF): es la única fuente de
            # stock para F3.1 desde la regla canónica del volumen oficial.
            'volume_pdf_m3': operational,
            'conciliation_status': 'not_compared',
            'guide_pdf_file': base64.b64encode(b'%PDF-fake'),
            'guide_pdf_filename': 'guia.pdf',
        })

    def _volume_lots(self, guia):
        """Lotes de volumen de la guía por identidad documental (F3.1)."""
        return self.StockLot.search([
            ('volume_source_guia_id', '=', guia.id),
            ('lot_flow_type', '=', 'volume'),
        ])

    def _any_product(self):
        product = self.env['product.product'].search([], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'F3.1 Test Product',
            })
        return product

    # ── 1. Alta de guía de volumen: un único lote con etiqueta SV ──────────
    def test_01_guia_volumen_crea_un_lote_sv(self):
        guia = self._make_guia('VOL-F31-1')
        guia.action_validate()
        self.assertEqual(guia.state, 'validated')
        self.assertEqual(len(guia.lot_ids), 1)
        lot = guia.lot_ids
        self.assertEqual(len(self._volume_lots(guia)), 1)
        self.assertRegex(lot.name, SV_LABEL)
        self.assertEqual(lot.lot_flow_type, 'volume')
        self.assertEqual(lot.volume_source_guia_id, guia)
        self.assertEqual(lot.guia_processing_id, guia)

    # ── 2. Sufijos numéricos idénticos: lotes y etiquetas distintas ────────
    def test_02_sufijos_identicos_no_colisionan(self):
        guia_a = self._make_guia('VOL-F31-19826')
        guia_a.action_validate()
        guia_b = self._make_guia('19826')
        guia_b.action_validate()

        lot_a = self._volume_lots(guia_a)
        lot_b = self._volume_lots(guia_b)
        self.assertEqual(len(lot_a), 1)
        self.assertEqual(len(lot_b), 1)
        self.assertNotEqual(lot_a.id, lot_b.id)
        self.assertNotEqual(lot_a.name, lot_b.name)
        for lot, guia in ((lot_a, guia_a), (lot_b, guia_b)):
            self.assertRegex(lot.name, SV_LABEL)
            self.assertEqual(lot.volume_source_guia_id, guia)
            self.assertEqual(lot.guia_processing_id, guia)
        # Sin vínculos cruzados ni sobrescritura entre guías.
        self.assertNotIn(lot_b.id, guia_a.lot_ids.ids)
        self.assertNotIn(lot_a.id, guia_b.lot_ids.ids)

    # ── 3. Reapertura: la identidad documental sobrevive ──────────────────
    def test_03_reapertura_conserva_identidad_sv(self):
        guia = self._make_guia('VOL-F31-3')
        guia.action_validate()
        lot = guia.lot_ids
        label, lot_id = lot.name, lot.id

        guia.action_reopen_to_draft()
        self.assertEqual(guia.state, 'draft')
        self.assertFalse(guia.lot_ids)
        lot.invalidate_recordset()
        self.assertTrue(lot.exists())
        self.assertEqual(lot.id, lot_id)
        self.assertEqual(lot.name, label)
        self.assertEqual(lot.lot_flow_type, 'volume')
        self.assertEqual(lot.volume_source_guia_id, guia)
        self.assertFalse(lot.guia_processing_id)

    # ── 4. Revalidación: se reutiliza el MISMO lote y la MISMA etiqueta ────
    def test_04_revalidacion_reutiliza_lote_sv(self):
        guia = self._make_guia('VOL-F31-4')
        guia.action_validate()
        lot = guia.lot_ids
        label, lot_id = lot.name, lot.id

        guia.action_reopen_to_draft()
        guia.write({'state': 'verified'})
        guia.action_validate()

        lots = self._volume_lots(guia)
        self.assertEqual(len(lots), 1, 'No debe acuñarse una segunda etiqueta SV')
        self.assertEqual(lots.id, lot_id)
        self.assertEqual(lots.name, label)
        self.assertEqual(lots.guia_processing_id, guia)
        self.assertIn(lot_id, guia.lot_ids.ids)

    # ── 5. Inmutabilidad de la guía origen y coherencia del tipo ───────────
    def test_05_identidad_de_volumen_inmutable(self):
        guia = self._make_guia('VOL-F31-5')
        guia.action_validate()
        lot = guia.lot_ids
        label = lot.name
        otra = self._make_guia('VOL-F31-5B')

        with self.assertRaises(ValidationError):
            lot.write({'volume_source_guia_id': False})
        with self.assertRaises(ValidationError):
            lot.write({'volume_source_guia_id': otra.id})
        # Reescribir el mismo valor está permitido (idempotencia).
        lot.write({'volume_source_guia_id': guia.id})
        lot.invalidate_recordset()
        self.assertEqual(lot.volume_source_guia_id, guia)
        self.assertEqual(lot.name, label)
        # Coherencia obligatoria entre tipo de flujo y guía origen.
        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'SV99999999999',
                'product_id': self._any_product().id,
                'lot_flow_type': 'volume',
            })
        with self.assertRaises(ValidationError):
            self.StockLot.create({
                'name': 'F31-TEST-SIN-TIPO',
                'product_id': self._any_product().id,
                'volume_source_guia_id': guia.id,
            })

    # ── 6. Lote histórico GRANEL: intacto y nunca adoptado ────────────────
    def test_06_lote_historico_granel_intacto(self):
        legacy = self.StockLot.create({
            'name': 'GRANEL 19826',
            'product_id': self._any_product().id,
            'volumen_m3': 5.0,
        })
        guia = self._make_guia('G-19826')
        guia.action_validate()

        legacy.invalidate_recordset()
        self.assertEqual(legacy.name, 'GRANEL 19826')
        self.assertFalse(legacy.lot_flow_type)
        self.assertFalse(legacy.volume_source_guia_id)
        self.assertFalse(legacy.guia_processing_id)
        self.assertAlmostEqual(legacy.volumen_m3, 5.0, places=3)
        nuevo = self._volume_lots(guia)
        self.assertEqual(len(nuevo), 1)
        self.assertNotEqual(nuevo.id, legacy.id)
        self.assertRegex(nuevo.name, SV_LABEL)
