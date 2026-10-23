# -*- coding: utf-8 -*-
"""
TESTS: Regla de cálculo derivada del perfil de ingesta (FASE 13/2B, Paso 1)

Cobertura:
  1. `_fill_staging_table` impone el perfil de la cabecera a TODAS las líneas,
     aunque el parser entregue otra regla ('metric').
  2. Cambiar `ingestion_profile` en borrador propaga la regla a las líneas.
  3. El cambio de perfil NO toca un registro fuera de borrador.
  4. Solo se propagan las líneas auto-derivadas del perfil anterior
     (una regla ajena al perfil se respeta).
  5. Guía 40030 con perfil S2S: embarque 44.713 m³ ≠ compra documental
     46.158 m³ (12 paquetes, 6/4 a 4.0 m). El nominal de compra
     (45 mm → 54.518 m³) lo resuelve el Paso 2.
"""
import base64

from odoo.tests import TransactionCase, tagged


PACKAGES_40030 = (
    # (paquete, ancho_mm, piezas, volumen_documental_m3, embarque_m3)
    (1, 170.0, 150, 3.8862, 3.886),
    (2, 170.0, 150, 3.8862, 3.886),
    (3, 150.0, 175, 4.0005, 3.895),
    (4, 150.0, 175, 4.0005, 3.895),
    (5, 125.0, 200, 3.81, 3.677),
    (6, 125.0, 200, 3.81, 3.677),
    (7, 125.0, 200, 3.81, 3.677),
    (8, 125.0, 200, 3.81, 3.677),
    (9, 125.0, 200, 3.81, 3.677),
    (10, 125.0, 200, 3.81, 3.677),
    (11, 100.0, 250, 3.81, 3.629),
    (12, 75.0, 325, 3.71475, 3.460),
)


@tagged('post_install', '-at_install', 'madenat_export_rule_profile')
class TestReceptionExportRuleProfile(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rule = cls.env['madenat.lumber.product.default']
        cls.Product = cls.env['product.product']
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product_fijo = cls.Product.create({
            'name': 'Producto Maestro 2B Paso1',
            'type': 'consu',
            'tracking': 'lot',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
            'sale_line_warn': 'no-message',
            'purchase_line_warn': 'no-message',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor 2B Paso1',
            'is_company': True,
            'supplier_rank': 1,
        })
        # Aislar las reglas sembradas por el XML del módulo.
        cls.Rule.search([]).write({'active': False})
        cls.Rule.create({'tipo_ingreso': 'bruta', 'product_id': cls.product_fijo.id})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _create_reception(self, profile):
        return self.env['lumber.reception'].create({
            'name': 'TEST-2B-%s' % profile.upper(),
            'supplier_id': self.partner.id,
            'ingestion_profile': profile,
            'excel_file': base64.b64encode(b'packing').decode(),
            'excel_filename': 'packing.xlsx',
        })

    def _pl_data(self, export_rule=None):
        lines = []
        for package_no, width_mm, pieces, volumen, _embarque in PACKAGES_40030:
            item = {
                'product_code': 'PKG-%02d' % package_no,
                'product_name': 'MADERA SECA CEPILLADA',
                'package_no': package_no,
                'pieces': pieces,
                'volume_m3': volumen,
                'thickness_mm': 38.1,
                'width_mm': width_mm,
                'length_m': 4.0,
                'thickness_nominal': 45.0,
                'width_nominal': width_mm,
            }
            if export_rule is not None:
                item['export_rule'] = export_rule
            lines.append(item)
        return {'lines': lines}

    def _rules(self, reception):
        return set(reception.reception_line_ids.mapped('export_calculation_rule'))

    # ── Tests ──────────────────────────────────────────────────────────────
    def test_01_fill_staging_impone_el_perfil(self):
        """El perfil manda: un 'metric' del parser no degrada la regla S2S."""
        reception = self._create_reception('f1550')
        reception._fill_staging_table(self._pl_data(export_rule='metric'))
        self.assertEqual(len(reception.reception_line_ids), 12)
        self.assertEqual(self._rules(reception), {'f1550'})

    def test_02_cambio_de_perfil_en_borrador_propaga(self):
        """Perfil cambiado en borrador → regla nueva en todas las líneas."""
        reception = self._create_reception('metric')
        reception._fill_staging_table(self._pl_data())
        self.assertEqual(reception.state, 'draft')
        self.assertEqual(self._rules(reception), {'metric'})
        reception.write({'ingestion_profile': 'f1550'})
        self.assertEqual(self._rules(reception), {'f1550'})

    def test_03_cambio_de_perfil_fuera_de_borrador_no_toca(self):
        """Un registro ya verificado conserva la regla de sus líneas."""
        reception = self._create_reception('metric')
        reception._fill_staging_table(self._pl_data())
        reception.write({'state': 'verified'})
        reception.write({'ingestion_profile': 'f1550'})
        self.assertEqual(self._rules(reception), {'metric'})

    def test_04_guia_40030_export_distinto_de_compra(self):
        """40030 S2S: embarque 44.713 m³ ≠ compra documental 46.158 m³.

        El nominal de compra (45 mm → 54.518 m³) lo resuelve el Paso 2; aquí se
        prueba que la regla S2S se aplica a TODAS las líneas y que la compra
        almacenada es el volumen documental (F-14), no el de embarque.
        """
        reception = self._create_reception('f1550')
        reception._fill_staging_table(self._pl_data())
        lines = reception.reception_line_ids
        by_lot = {line.lot_name: line for line in lines}
        for package_no, _width, _pieces, _vol, embarque in PACKAGES_40030:
            line = by_lot['PKG-%02d' % package_no]
            self.assertAlmostEqual(
                line.vol_shipment_m3, embarque, places=3,
                msg='Embarque paquete %s' % package_no)
        total_compra = sum(lines.mapped('vol_purchase_m3'))
        total_embarque = sum(lines.mapped('vol_shipment_m3'))
        self.assertAlmostEqual(total_embarque, 44.713, places=3)
        self.assertAlmostEqual(total_compra, 46.158, places=2)
        self.assertGreater(total_compra, total_embarque)

    def test_05_no_pisa_reglas_ajenas_al_perfil(self):
        """Solo se propagan las líneas auto-derivadas del perfil anterior."""
        reception = self._create_reception('metric')
        reception._fill_staging_table(self._pl_data())
        manual = reception.reception_line_ids[0]
        manual.write({'export_calculation_rule': 'f5085'})  # regla ajena
        reception.write({'ingestion_profile': 'f1550'})
        self.assertEqual(manual.export_calculation_rule, 'f5085')
        others = reception.reception_line_ids - manual
        self.assertEqual(
            set(others.mapped('export_calculation_rule')), {'f1550'})
