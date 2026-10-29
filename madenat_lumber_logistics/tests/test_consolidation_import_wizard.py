# -*- coding: utf-8 -*-
"""
Pruebas unitarias para LumberConsolidationImportWizard (Bloque 7.2 / TDD).
Valida:
1. Lectura del formato real de doble bloque (Exportación / Compra).
2. Captura de filas sin etiqueta como pendientes de asignación manual sin descartarlas.
3. Validación de volúmenes contra el sistema y emisión de informe de diferencias.
4. Agrupación de contenedores repetidos sin duplicación.
5. Invarianza: no crea lotes ni modifica volúmenes en BD.
"""
import base64
import os
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestConsolidationImportWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.uom_m3 = cls.env.ref('madenat_lumber_core.uom_m3', raise_if_not_found=False) or cls.env['uom.uom'].search([('name', '=', 'm³')], limit=1)
        if not cls.uom_m3:
            cls.uom_m3 = cls.env.ref('uom.product_uom_unit')

        cls.vessel = cls.env['shipping.vessel'].create({'name': 'MSC ELENOIRE'})
        cls.shipment = cls.env['lumber.export.shipment'].create({
            'name': 'EXP-CONSOL-TEST',
            'booking_reference': '29020535',
            'vessel_id': cls.vessel.id,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Mad.Aserrada Seca',
            'type': 'consu',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.partner_fatima = cls.env['res.partner'].create({'name': 'FATIMA', 'ref': 'FATIMA'})

        # Crear 2 lotes reales de la Tarja 4 de FA543R para probar match
        cls.lot_86067 = cls.env['stock.lot'].create({
            'name': '0000000086067',
            'ref': '0000000086067',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'supplier_id': cls.partner_fatima.id,
            'vol_shipment_m3': 3.677,
            'volumen_m3': 4.500,
            'piezas': 200,
        })
        cls.lot_86087 = cls.env['stock.lot'].create({
            'name': '0000000086087',
            'ref': '0000000086087',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'supplier_id': cls.partner_fatima.id,
            'vol_shipment_m3': 3.629,
            'volumen_m3': 4.500,
            'piezas': 250,
        })

        # Rutas de los archivos reales de referencia
        cls.path_fa543r = '/home/viruco/dev-stack/odoo/odoo-18-ce/muestras_documentos_ingreso/Ejercicio Completo Cristhian Elgueta/LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx'
        cls.path_fa610r = '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_docs/RAW/LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx'

    def test_01_import_fa543r_detects_containers_and_pending_rows(self):
        """Valida que FA543R detecta contenedores y captura filas sin etiqueta de San Joaquín."""
        if not os.path.exists(self.path_fa543r):
            self.skipTest(f"Archivo {self.path_fa543r} no encontrado")

        with open(self.path_fa543r, 'rb') as f:
            file_bytes = f.read()

        wiz = self.env['lumber.consolidation.import.wizard'].create({
            'shipment_id': self.shipment.id,
            'file_data': base64.b64encode(file_bytes),
            'file_name': 'LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx',
        })

        wiz.action_validate_file()
        self.assertEqual(wiz.state, 'analyzed')
        self.assertGreater(wiz.total_containers, 0, "Debe detectar contenedores")

        # Verificar que se capturaron filas pendientes sin etiqueta (San Joaquín)
        pending_no_label = wiz.pending_line_ids.filtered(lambda l: 'sin etiqueta' in l.reason.lower())
        self.assertTrue(len(pending_no_label) > 0, "Debe haber filas pendientes por carecer de etiqueta")

        # Verificar caso específico de Tarja 4 (SLSU 803703-3 con San Joaquín sin etiqueta)
        slsu_pending = wiz.pending_line_ids.filtered(lambda l: l.container_code == 'SLSU 803703-3' and 'sin etiqueta' in l.reason.lower())
        self.assertTrue(len(slsu_pending) >= 1, "SLSU 803703-3 debe tener filas pendientes sin etiqueta")

    def test_02_confirm_import_assigns_lots_without_modifying_volumes(self):
        """Confirmar asignación vincula lotes existentes y no altera volúmenes en BD."""
        if not os.path.exists(self.path_fa543r):
            self.skipTest(f"Archivo {self.path_fa543r} no encontrado")

        with open(self.path_fa543r, 'rb') as f:
            file_bytes = f.read()

        orig_exp = self.lot_86067.vol_shipment_m3
        orig_nom = self.lot_86067.volumen_m3

        wiz = self.env['lumber.consolidation.import.wizard'].create({
            'shipment_id': self.shipment.id,
            'file_data': base64.b64encode(file_bytes),
            'file_name': 'LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx',
        })

        wiz.action_confirm_import()
        self.assertEqual(wiz.state, 'done')

        # Buscar el contenedor SLSU 803703-3
        container = self.env['lumber.container'].search([
            ('shipment_id', '=', self.shipment.id),
            ('name', '=', 'SLSU 803703-3')
        ], limit=1)
        self.assertTrue(container, "Debe haber creado/vinculado el contenedor SLSU 803703-3")

        # Los lotes creados en setUpClass deben estar asignados
        self.assertIn(self.lot_86067, container.lot_ids, "El lote 86067 debe estar asignado al contenedor")
        self.assertIn(self.lot_86087, container.lot_ids, "El lote 86087 debe estar asignado al contenedor")

        # Invarianza de volúmenes en BD
        self.assertEqual(self.lot_86067.vol_shipment_m3, orig_exp, "El volumen de exportación no debe modificarse")
        self.assertEqual(self.lot_86067.volumen_m3, orig_nom, "El volumen nominal no debe modificarse")

    def test_03_repeated_containers_do_not_duplicate(self):
        """Si un contenedor ya existe en el embarque, se reutiliza sin duplicar registros."""
        pre_container = self.env['lumber.container'].create({
            'shipment_id': self.shipment.id,
            'name': 'TGBU 617425-8',
            'container_type': '40HC',
            'seal_number': 'PRE-SEAL',
        })

        if not os.path.exists(self.path_fa543r):
            self.skipTest(f"Archivo {self.path_fa543r} no encontrado")

        with open(self.path_fa543r, 'rb') as f:
            file_bytes = f.read()

        wiz = self.env['lumber.consolidation.import.wizard'].create({
            'shipment_id': self.shipment.id,
            'file_data': base64.b64encode(file_bytes),
            'file_name': 'LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx',
        })
        wiz.action_confirm_import()

        # Debe seguir existiendo exactamente un contenedor con ese nombre en el embarque
        containers = self.env['lumber.container'].search([
            ('shipment_id', '=', self.shipment.id),
            ('name', '=', 'TGBU 617425-8')
        ])
        self.assertEqual(len(containers), 1, "No debe duplicar contenedores preexistentes")


@tagged('post_install', '-at_install', 'madenat', 'consolidation_external_labels')
class TestConsolidationExternalLabelsLookup(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.uom_m3 = cls.env.ref('madenat_lumber_core.uom_m3', raise_if_not_found=False) or cls.env['uom.uom'].search([('name', '=', 'm³')], limit=1)
        if not cls.uom_m3:
            cls.uom_m3 = cls.env.ref('uom.product_uom_unit')

        cls.vessel = cls.env['shipping.vessel'].create({'name': 'VESSEL-TEST-EXTERNAL'})
        cls.shipment = cls.env['lumber.export.shipment'].create({
            'name': 'EXP-EXT-TEST',
            'vessel_id': cls.vessel.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Mad. Aserrada Test',
            'type': 'consu',
            'uom_id': cls.uom_m3.id,
            'uom_po_id': cls.uom_m3.id,
        })
        cls.wizard = cls.env['lumber.consolidation.import.wizard'].create({
            'shipment_id': cls.shipment.id,
        })

        # Caso 1: Lote con etiquetas externas compuestas
        cls.lot_single = cls.env['stock.lot'].create({
            'name': 'LOTE-EXT-01',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'external_labels': 'D7731, E8800',
        })

        # Caso 2 & 3: Lotes con etiquetas externas ambiguas
        cls.lot_ambig_1 = cls.env['stock.lot'].create({
            'name': 'LOTE-AMBIG-01',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'external_labels': 'EXT-DUP, OTHER1',
        })
        cls.lot_ambig_2 = cls.env['stock.lot'].create({
            'name': 'LOTE-AMBIG-02',
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'external_labels': 'EXT-DUP, OTHER2',
        })

    def test_01_exact_token_match(self):
        """1) Coincidencia exacta de token por external_labels (case-insensitive)."""
        lot, is_ambig, _ = self.wizard._find_lot_by_label('d7731')
        self.assertFalse(is_ambig, "No debe marcar ambigüedad si hay coincidencia exacta única")
        self.assertEqual(lot, self.lot_single, "Debe resolver el lote correspondiente al token exacto")

        # También debe coincidir con el segundo token
        lot2, is_ambig2, _ = self.wizard._find_lot_by_label('E8800')
        self.assertFalse(is_ambig2)
        self.assertEqual(lot2, self.lot_single)

    def test_02_substring_no_match(self):
        """2) No-coincidencia por subcadena: 'D77' no debe coincidir con 'D7731'."""
        lot, is_ambig, _ = self.wizard._find_lot_by_label('D77')
        self.assertFalse(is_ambig, "No debe marcar ambigüedad para subcadena sin token exacto")
        self.assertFalse(lot, "Subcadena parcial no debe coincidir con token más largo")

    def test_03_ambiguity_detection(self):
        """3) Ambigüedad: dos o más lotes con el mismo token externo no deben enlazarse."""
        lot, is_ambig, amb_lots = self.wizard._find_lot_by_label('EXT-DUP')
        self.assertTrue(is_ambig, "Debe detectar ambigüedad al haber múltiples lotes con el mismo token")
        self.assertFalse(lot, "No debe elegir un lote arbitrario cuando hay ambigüedad")
        self.assertEqual(len(amb_lots), 2, "Debe identificar ambos lotes ambiguos")
