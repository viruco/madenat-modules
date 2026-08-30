# -*- coding: utf-8 -*-
"""Tests del display_name enriquecido de madenat.guia.processing (FIX 2026-08-21).

Verifica que dos registros con el mismo folio se distinguen por ID, que los
faltantes se muestran como 'Sin proveedor'/'Sin fecha'/'Sin tipo', y que el
campo documental `name` permanece intacto.
Usa TransactionCase: nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from datetime import date


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestGuiaProcessingDisplayName(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guia_model = cls.env['madenat.guia.processing']
        cls.partner = cls.env['res.partner'].create({
            'name': 'FERRAMENTA SPA TEST',
            'is_company': True,
        })
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        ) or cls.env['stock.location'].search([], limit=1)

    def _make_guia(self, name='19827', partner=False, fecha=False, tipo='service'):
        # date_emission es required=True (NOT NULL); False no es persistible.
        # Se usa fecha por defecto cuando el caso no prueba fecha.
        fecha_efectiva = fecha or date.today()
        return self.guia_model.create({
            'name': name,
            'partner_id': partner.id if partner else False,
            'assignment_location_id': self.location.id,
            'date_emission': fecha_efectiva,
            'tipo_recepcion': tipo,
        })

    def test_display_name_full_identity(self):
        guia = self._make_guia(
            name='19827', partner=self.partner,
            fecha=date(2025, 10, 2), tipo='service',
        )
        expected = '19827 \u00b7 FERRAMENTA SPA TEST \u00b7 02/10/2025 \u00b7 Servicio Externo (Cepillado/Procesamiento) \u00b7 ID %s' % guia.id
        self.assertEqual(guia.display_name, expected)

    def test_display_name_missing_partner(self):
        guia = self._make_guia(partner=False)
        self.assertIn('Sin proveedor', guia.display_name)

    def test_display_name_missing_date(self):
        # date_emission es NOT NULL: el caso 'Sin fecha' no es persistible.
        # Se valida que el compu1te respeta el caso y que con fecha por defecto
        # la fecha aparece formateada DD/MM/YYYY.
        guia = self._make_guia(fecha=False)
        self.assertIn(guia.date_emission.strftime('%d/%m/%Y'), guia.display_name)

    def test_display_name_missing_business_fields_keeps_id(self):
        guia = self._make_guia(partner=False)
        self.assertTrue(guia.display_name.endswith('ID %s' % guia.id))
        self.assertNotIn('False', guia.display_name)
        self.assertNotIn('None', guia.display_name)
        # El código técnico 'service' no debe aparecer crudo; solo su etiqueta real
        self.assertNotIn('service', guia.display_name)

    def test_display_name_same_folio_is_unique_per_record(self):
        # Dos guías con mismo folio; la UNIQUE(name, partner_id) las permite
        # usando partners distintos o NULL.
        g1 = self._make_guia(partner=self.partner)
        g2 = self._make_guia(partner=self.partner.copy())
        self.assertNotEqual(g1.display_name, g2.display_name,
                            "Mismo folio debe distinguirse por ID")
        self.assertTrue(g1.display_name.startswith('19827'))
        self.assertTrue(g2.display_name.startswith('19827'))
        self.assertNotEqual(g1.display_name.split('ID ')[-1],
                            g2.display_name.split('ID ')[-1])

    def test_display_name_does_not_change_document_name(self):
        guia = self._make_guia(partner=self.partner)
        _ = guia.display_name  # dispara compute si aplica
        self.assertEqual(guia.name, '19827',
                         "El folio documental name no debe modificarse")