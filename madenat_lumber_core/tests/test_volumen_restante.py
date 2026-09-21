# -*- coding: utf-8 -*-
"""AD-67: volumen físico remanente tras consumo parcial (stock.lot.volumen_restante_m3).

Cubre la fuente de verdad física (stock.quant) frente al volumen documental
(stock.lot.volumen_m3), garantizando que:
- Sin consumo: volumen_restante_m3 == volumen_m3.
- Tras consumo parcial (AD-66 vía source_lot_line_ids): volumen_restante_m3
  decrece exactamente en qty_to_consume, mientras volumen_m3 permanece intacto.
- Tras reversión (_reverse_consumption_picking): volumen_restante_m3 vuelve al
  valor original.
- estado_trazabilidad no cambia en ningún escenario (regresión Decisión 4 de AD-67).

Se aísla en un archivo propio para no tocar los tests existentes de AD-66 ni de
BT-04; reutiliza el patrón de TestGuiaProcessingConsumptionPartialAD66.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'guia_processing')
class TestVolumenRestante(TransactionCase):
    """AD-67: campo stock.lot.volumen_restante_m3 como fuente de verdad física."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GuiaModel = cls.env['madenat.guia.processing']
        cls.SourceLotLineModel = cls.env['madenat.guia.processing.source.lot.line']
        cls.Quant = cls.env['stock.quant']
        cls.StockLot = cls.env['stock.lot']

        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.location = cls.warehouse.lot_stock_id

        cls.partner = cls.env['res.partner'].create({'name': 'AD67 Processor'})

        uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'AD67 Lumber Storable',
            'is_storable': True,
            'tracking': 'lot',
            'uom_id': uom_m3.id,
            'uom_po_id': uom_m3.id,
        })

    def _make_source_lot(self, name='AD67-SRC', qty=10.0):
        lot = self.StockLot.create({
            'name': name,
            'product_id': self.product.id,
            'volumen_m3': qty,
            'company_id': self.company.id,
        })
        self.Quant._update_available_quantity(
            self.product, self.location, qty, lot_id=lot
        )
        return lot

    def _make_service_guia(self, name='AD67-SERVICE', source_lot=None, qty=None):
        vals = {
            'name': name,
            'partner_id': self.partner.id,
            'assignment_location_id': self.location.id,
            'state': 'draft',
            'tipo_recepcion': 'service',
            'rate_usd': 800.0,
        }
        guia = self.GuiaModel.create(vals)
        if source_lot and qty is not None:
            self.SourceLotLineModel.create({
                'guia_processing_id': guia.id,
                'lot_id': source_lot.id,
                'qty_to_consume': qty,
            })
        return guia

    def _read_volumen_restante(self, lot):
        """Fuerza recomputación de volumen_restante_m3 leyendo quants frescos.

        stock.quant._update_available_quantity y la validación de pickings pueden
        actualizar `quantity` vía SQL sin disparar el @api.depends del campo
        computado; invalidar + recomputar explícitamente hace el test determinista.
        """
        lot.invalidate_recordset(['quant_ids', 'volumen_restante_m3'])
        lot._compute_volumen_restante_m3()
        return lot.volumen_restante_m3

    def test_01_sin_consumo_volumen_restante_igual_volumen_m3(self):
        source_lot = self._make_source_lot(qty=10.0)
        self.assertAlmostEqual(source_lot.volumen_m3, 10.0, places=3)
        self.assertAlmostEqual(
            self._read_volumen_restante(source_lot),
            source_lot.volumen_m3,
            places=3,
            msg="Sin consumo, el volumen remanente debe igualar al volumen documental"
        )

    def test_02_consumo_parcial_decrementa_solo_volumen_restante(self):
        source_lot = self._make_source_lot(qty=10.0)
        estado_inicial = source_lot.estado_trazabilidad
        volumen_origen = source_lot.volumen_m3

        guia = self._make_service_guia(
            name='AD67-PARTIAL', source_lot=source_lot, qty=3.0
        )
        picking = guia._get_or_create_consumption_picking()

        self.assertTrue(picking, "Debe crearse la salida a proceso")
        self.assertAlmostEqual(
            self._read_volumen_restante(source_lot), 7.0, places=3,
            msg="El volumen remanente debe decrecer exactamente en qty_to_consume"
        )
        self.assertAlmostEqual(
            source_lot.volumen_m3, volumen_origen, places=3,
            msg="El volumen documental de origen no debe cambiar"
        )
        self.assertEqual(
            source_lot.estado_trazabilidad, estado_inicial,
            "estado_trazabilidad no debe cambiar tras consumo parcial"
        )

    def test_03_reversion_restaura_volumen_restante(self):
        source_lot = self._make_source_lot(qty=10.0)
        estado_inicial = source_lot.estado_trazabilidad

        guia = self._make_service_guia(
            name='AD67-REVERSE', source_lot=source_lot, qty=3.0
        )
        guia._get_or_create_consumption_picking()
        self.assertAlmostEqual(
            self._read_volumen_restante(source_lot), 7.0, places=3
        )

        return_picking = guia._reverse_consumption_picking()
        self.assertTrue(return_picking, "Debe generarse un retorno")
        self.assertAlmostEqual(
            self._read_volumen_restante(source_lot), 10.0, places=3,
            msg="Tras reversión, el volumen remanente vuelve al valor original"
        )
        self.assertEqual(
            source_lot.estado_trazabilidad, estado_inicial,
            "estado_trazabilidad no debe cambiar tras la reversión"
        )
