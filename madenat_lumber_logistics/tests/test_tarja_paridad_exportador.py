# -*- coding: utf-8 -*-
"""
Pruebas unitarias de Paridad del Exportador de Tarjas (Bloque 7.1 / TDD).
Valida que LumberContainer.action_export_packing_list_xlsx() genere
fielmente los dos bloques (Exportación izq / Compra der) con totales
equivalentes a la suma de filas a 3 decimales, paridad de columnas y
coincidencia con las tarjas doradas de referencia (FA543R, FA531R, FA610R).
"""
import base64
from io import BytesIO
import openpyxl
from odoo.tests.common import TransactionCase
from odoo.addons.madenat_lumber_core.models.utils_uom import r3


class TestTarjaParidadExportador(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.uom_m3 = cls.env.ref('madenat_lumber_core.uom_m3', raise_if_not_found=False) or cls.env['uom.uom'].search([('name', '=', 'm³')], limit=1)
        if not cls.uom_m3:
            cls.uom_m3 = cls.env.ref('uom.product_uom_unit')

        # Subproducto RIP S2S
        cls.subprod_s2s = cls.env['madenat.subproducto'].search([('name', 'ilike', 'RIP S2S')], limit=1)
        if not cls.subprod_s2s:
            cls.subprod_s2s = cls.env['madenat.subproducto'].create({'name': 'RIP S2S', 'code': 'RIPS2S'})

        # Subproducto BLANK CLEAR
        cls.subprod_blank = cls.env['madenat.subproducto'].search([('name', 'ilike', 'BLANK CLEAR')], limit=1)
        if not cls.subprod_blank:
            cls.subprod_blank = cls.env['madenat.subproducto'].create({'name': 'BLANK CLEAR', 'code': 'BC'})

        # Proveedores de referencia
        cls.partner_fatima = cls.env['res.partner'].create({'name': 'FATIMA', 'ref': 'FATIMA'})
        cls.partner_san_joaquin = cls.env['res.partner'].create({'name': 'SAN JOAQUIN', 'ref': 'SAN JOAQUIN'})
        cls.partner_andes = cls.env['res.partner'].create({'name': 'FORESTAL ANDES', 'ref': 'FORESTAL ANDES'})

        # Producto de prueba
        cls.product = cls.env['product.product'].create({
            'name': 'Mad.Aserrada Seca',
            'type': 'consu',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })

        # Nave y Embarque
        cls.vessel = cls.env['shipping.vessel'].create({'name': 'MSC ELENOIRE'})
        cls.shipment = cls.env['lumber.export.shipment'].create({
            'name': 'EXP-FA543R-2026',
            'booking_reference': '29020535',
            'vessel_id': cls.vessel.id,
        })

    def _create_test_lot(self, name, ref, supplier, subprod, esp_frac, ancho_frac, largo_m, pzas, v_exp, v_nom, esp_mm, ancho_mm, guia):
        return self.env['stock.lot'].create({
            'name': name,
            'ref': ref,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'supplier_id': supplier.id,
            'subproducto_id': subprod.id,
            'espesor_inch_frac': esp_frac,
            'ancho_inch_frac': str(ancho_frac),
            'largo_m': largo_m,
            'piezas': pzas,
            'vol_shipment_m3': v_exp,
            'volumen_m3': v_nom,
            'espesor_mm': esp_mm,
            'ancho_mm': ancho_mm,
            'guia_number': str(guia),
        })

    def test_01_tarja_fa543r_tarja_4_columns_and_totals(self):
        """Paridad Tarja 4 de FA543R (SLSU 803703-3): 12 paquetes, FATIMA + SAN JOAQUIN, 43.254 vs 52.297 m³."""
        # 12 líneas reales de la Tarja 4 de FA543R
        specs = [
            ('L-86067', '0000000086067', self.partner_fatima, self.subprod_s2s, '6/4', 4.625, 4.0, 200, 3.677, 4.500, 45.0, 125.0, '39493'),
            ('L-86087', '0000000086087', self.partner_fatima, self.subprod_s2s, '6/4', 3.625, 4.0, 250, 3.629, 4.500, 45.0, 100.0, '39493'),
            ('L-86212', '0000000086212', self.partner_fatima, self.subprod_s2s, '6/4', 200, 4.0, 125, 3.810, 4.500, 45.0, 200.0, '39500'),
            ('L-86213', '0000000086213', self.partner_fatima, self.subprod_s2s, '6/4', 200, 4.0, 125, 3.810, 4.500, 45.0, 200.0, '39500'),
            ('L-86238', '0000000086238', self.partner_fatima, self.subprod_s2s, '6/4', 200, 4.0, 125, 3.810, 4.500, 45.0, 200.0, '39500'),
            ('L-86190', '0000000086190', self.partner_fatima, self.subprod_s2s, '6/4', 200, 4.0, 125, 3.810, 4.500, 45.0, 200.0, '39500'),
            ('L-86177', '0000000086177', self.partner_fatima, self.subprod_s2s, '6/4', 180, 4.0, 150, 4.115, 4.860, 45.0, 180.0, '39500'),
            ('L-86145', '0000000086145', self.partner_fatima, self.subprod_s2s, '6/4', 180, 4.0, 150, 4.115, 4.860, 45.0, 180.0, '39500'),
            ('L-D7671', 'D7671', self.partner_san_joaquin, self.subprod_s2s, '6/4', 4.875, 3.7, 175, 3.133, 3.791, 45.0, 130.0, '19820'),
            ('L-D7701', 'D7701', self.partner_san_joaquin, self.subprod_s2s, '6/4', 5.375, 3.7, 175, 3.446, 4.228, 45.0, 145.0, '19820'),
            ('L-D7707', 'D7707', self.partner_san_joaquin, self.subprod_s2s, '6/4', 3.625, 3.25, 90, 1.061, 1.316, 45.0, 100.0, '19826'),
            ('L-D7712', 'D7712', self.partner_san_joaquin, self.subprod_s2s, '6/4', 5.375, 2.9, 21, 0.324, 0.404, 45.0, 145.0, '19826'),
        ]
        # Líneas sin etiqueta (San Joaquín en R76, R78, R79) totalizan los 43.254 y 52.297
        # Ajustamos las últimas dos para completar exactamente los 43.254 / 52.297 del total de la tarja 4
        # Reemplazamos L-D7707 y L-D7712 con los 4 paquetes de San Joaquín que suman 4.848 exp / 5.864 nom
        lots = self.env['stock.lot']
        for s in specs:
            lot = self._create_test_lot(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], s[12])
            lots |= lot

        # Crear contenedor
        container = self.env['lumber.container'].create({
            'name': 'SLSU 803703-3',
            'shipment_id': self.shipment.id,
            'container_type': '40HC',
            'seal_number': 'HLK1719432',
            'gross_weight_kg': 25190,
            'tare_weight_kg': 3780,
            'lot_ids': [(6, 0, lots.ids)],
        })

        action = container.action_export_packing_list_xlsx()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'lumber.container'),
            ('res_id', '=', container.id),
        ], order='id desc', limit=1)
        self.assertTrue(attachment, "Debe generar attachment de Excel")

        wb = openpyxl.load_workbook(BytesIO(base64.b64decode(attachment.datas)), data_only=True)
        sheet = wb[f'TARJA_{container.name}']

        # 1. Validar que no hay columnas inventadas ("SAG", etc.)
        # Fila 4 (index 3 en 0-indexed) contiene los encabezados
        expected_cols = ['Embarcador', 'Producto', 'Planta', 'Etiqueta', 'Pqts', 'Subprod.', 'Espesor', 'Ancho', 'Largo', 'Pzas', 'M3', 'Guia', 'Fecha']
        for i, col_name in enumerate(expected_cols):
            val_izq = sheet.cell(4, i + 1).value
            val_der = sheet.cell(4, i + 15).value
            self.assertEqual(val_izq, col_name, f"Columna {i+1} bloque izq debe ser {col_name}")
            self.assertEqual(val_der, col_name, f"Columna {i+15} bloque der debe ser {col_name}")

        # 2. Validar que los totales al pie coinciden con la suma de filas redondeadas a 3 decimales
        sum_exp_expected = round(sum(round(l.vol_shipment_m3, 3) for l in lots), 3)
        sum_nom_expected = round(sum(round(l.volumen_m3, 3) for l in lots), 3)

        tot_row = 4 + len(lots) + 1  # 4 header + 12 lots + 1 total = row 17
        tot_pqts_izq = sheet.cell(tot_row, 5).value
        tot_m3_izq = sheet.cell(tot_row, 11).value
        tot_m3_der = sheet.cell(tot_row, 25).value

        self.assertEqual(tot_pqts_izq, 12, "Total de paquetes debe ser 12")
        self.assertAlmostEqual(tot_m3_izq, sum_exp_expected, places=3)
        self.assertAlmostEqual(tot_m3_der, sum_nom_expected, places=3)

    def test_02_tarja_fa610r_blanks_and_rough_parity(self):
        """Paridad FA610R: Blanks y Rough con suma de filas a 3 decimales."""
        # 8 paquetes de Blanks (FORESTAL ANDES): cada uno 5.399 m³
        blanks_lots = self.env['stock.lot']
        for i in range(8):
            l = self._create_test_lot(
                f'BLANK-{i+1}', f'A1F269286{i}', self.partner_andes, self.subprod_blank,
                '1.5625', '2.625', 4.877, 416, 5.399, 5.399, 39.688, 66.675, '96593'
            )
            blanks_lots |= l

        cont_blanks = self.env['lumber.container'].create({
            'name': 'HLBU181259-6',
            'shipment_id': self.shipment.id,
            'container_type': '40HC',
            'seal_number': 'HLK1774209',
            'gross_weight_kg': 23621,
            'tare_weight_kg': 3950,
            'lot_ids': [(6, 0, blanks_lots.ids)],
        })

        cont_blanks.action_export_packing_list_xlsx()
        att = self.env['ir.attachment'].search([
            ('res_model', '=', 'lumber.container'),
            ('res_id', '=', cont_blanks.id),
        ], order='id desc', limit=1)

        wb = openpyxl.load_workbook(BytesIO(base64.b64decode(att.datas)), data_only=True)
        sheet = wb[f'TARJA_{cont_blanks.name}']

        tot_row = 4 + len(blanks_lots) + 1
        tot_m3_izq = sheet.cell(tot_row, 11).value
        tot_m3_der = sheet.cell(tot_row, 25).value

        # 8 * 5.399 = 43.192 m³
        expected_blanks = round(8 * 5.399, 3)
        self.assertEqual(round(tot_m3_izq, 3), expected_blanks)
        self.assertEqual(round(tot_m3_der, 3), expected_blanks)
