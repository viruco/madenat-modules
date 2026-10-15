# -*- coding: utf-8 -*-
"""Pruebas de la mejora MÍNIMA de búsqueda/filtros/agrupación de la Consola.

Cubre (implementación aislada 2026-10-07):
- OC documental vs OC vinculada: coherencia de columna, búsqueda y agrupación;
  la referencia documental NO se sustituye por el nombre de la OC vinculada.
- Significado real de la Fecha (`guide_date_kind`).
- Diferenciación de modalidad Producto / Procesado / Volúmenes.
- Búsqueda por producto REAL (sin elegir el primero ni duplicar filas).
- Procesador por la relación existente de la Orden de Procesamiento.
- Registros incompletos, ambos modelos origen y usuario operativo.

TransactionCase: nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models.intake_constants import CONSOLE_ID_OFFSET


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeSearchConsole(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Console = cls.env['madenat.lumber.intake.console']
        cls.operator = cls.env['res.users'].create({
            'name': 'Operaciones Search Test',
            'login': 'op_search_test',
            'groups_id': [(6, 0, [cls.env.ref(
                'madenat_lumber_core.group_madenat_operaciones').id])],
        })
        cls.supplier = cls.env['res.partner'].create(
            {'name': 'Proveedor Search', 'is_company': True})
        cls.processor = cls.env['res.partner'].create(
            {'name': 'Procesador Search', 'is_company': True,
             'is_processor': True})
        cls.location = cls.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        cls.product_a = cls.env['product.product'].create(
            {'name': 'Search Product A', 'type': 'consu'})
        cls.product_b = cls.env['product.product'].create(
            {'name': 'Search Product B', 'type': 'consu'})
        cls.service_product = cls.env['product.product'].create(
            {'name': 'Search Service', 'type': 'service'})

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_reception(self, name, **kw):
        vals = {'name': name, 'supplier_id': self.supplier.id}
        vals.update(kw)
        return self.env['lumber.reception'].create(vals)

    def _add_reception_line(self, reception, product, lot):
        return self.env['lumber.reception.line'].create({
            'reception_id': reception.id,
            'lot_name': lot,
            'product_id': product.id,
        })

    def _make_guia(self, name, tipo='service', **kw):
        vals = {
            'name': name,
            'partner_id': self.supplier.id,
            'tipo_recepcion': tipo,
            'assignment_location_id': self.location.id,
        }
        vals.update(kw)
        return self.env['madenat.guia.processing'].create(vals)

    def _add_guia_line(self, guia, product, lot):
        return self.env['madenat.guia.processing.line'].create({
            'processing_id': guia.id,
            'lot_name': lot,
            'product_id': product.id,
        })

    def _console_of(self, src):
        offset = (CONSOLE_ID_OFFSET
                  if src._name == 'madenat.guia.processing' else 0)
        self.env.flush_all()
        return self.Console.browse(offset + src.id).exists()

    def _cnt(self, domain):
        self.env.flush_all()
        return self.Console.search_count(domain)

    # ── 1. OC documental vs OC vinculada ───────────────────────────────────
    def test_01_oc_documental_no_se_sustituye_por_la_vinculada(self):
        rec = self._make_reception(
            'SEARCH-OC-REC', oc_reference_raw='OC-DOC-REC')
        guia = self._make_guia(
            'SEARCH-OC-GUIA', oc_reference_raw='OC-DOC-GUIA')
        c_rec = self._console_of(rec)
        c_guia = self._console_of(guia)
        self.assertTrue(c_rec and c_guia)
        self.assertEqual(c_rec.oc_documental, 'OC-DOC-REC')
        self.assertEqual(c_guia.oc_documental, 'OC-DOC-GUIA')
        self.assertFalse(c_rec.purchase_id)
        self.assertFalse(c_guia.purchase_id)
        # Vincular una OC NO sobrescribe la referencia documental mostrada.
        po = self.env['purchase.order'].create(
            {'partner_id': self.supplier.id})
        guia.write({'order_id': po.id})
        guia.flush_recordset()
        self.env.invalidate_all()
        c_guia = self._console_of(guia)
        self.assertEqual(c_guia.oc_documental, 'OC-DOC-GUIA')  # != po.name
        self.assertEqual(c_guia.purchase_id, po)
        guia.invalidate_recordset()
        self.assertEqual(guia.oc_reference_raw, 'OC-DOC-GUIA')

    def test_02_oc_busqueda_y_agrupacion_coherentes(self):
        names = ['SEARCH-OC-A', 'SEARCH-OC-B', 'SEARCH-OC-C']
        self._make_guia('SEARCH-OC-A', oc_reference_raw='OC-DOC-AAA')
        self._make_guia('SEARCH-OC-B', oc_reference_raw='OC-DOC-AAA')
        self._make_guia('SEARCH-OC-C')  # sin OC informada
        scope = [('guide_name', 'in', names)]
        self.assertEqual(self._cnt(scope), 3)
        self.assertEqual(
            self._cnt(scope + [('oc_documental', '=', 'OC-DOC-AAA')]), 2)
        self.assertEqual(
            self._cnt(scope + [('purchase_id', '=', False),
                               ('oc_documental', '!=', False)]), 2)
        self.assertEqual(
            self._cnt(scope + [('purchase_id', '=', False),
                               ('oc_documental', '=', False)]), 1)
        self.assertEqual(
            self._cnt(scope + [('purchase_id', '!=', False)]), 0)
        groups = self.Console.read_group(scope, ['id'], ['oc_documental'])
        labels = set()
        for g in groups:
            value = g['oc_documental']
            labels.add(value[1] if isinstance(value, tuple) else value)
        self.assertIn('OC-DOC-AAA', labels)

    # ── 2. Significado de la fecha ─────────────────────────────────────────
    def test_03_fecha_significado(self):
        rec_g = self._make_reception('SEARCH-DATE-G', guia_fecha='2026-01-15')
        rec_r = self._make_reception('SEARCH-DATE-R')  # sin fecha de guía
        guia = self._make_guia('SEARCH-DATE-GUIA', date_emission='2026-02-20')
        c_g = self._console_of(rec_g)
        c_r = self._console_of(rec_r)
        c_u = self._console_of(guia)
        self.assertEqual(c_g.guide_date_kind, 'emission')
        self.assertEqual(str(c_g.guide_date), '2026-01-15')
        self.assertEqual(c_r.guide_date_kind, 'reception')
        self.assertEqual(c_u.guide_date_kind, 'emission')
        self.assertEqual(str(c_u.guide_date), '2026-02-20')

    # ── 3. Modalidad Producto / Procesado / Volúmenes ──────────────────────
    def test_04_modalidad_tipos(self):
        names = ['SEARCH-M-PROD', 'SEARCH-M-PROC', 'SEARCH-M-VOL']
        self._make_reception('SEARCH-M-PROD')
        self._make_guia('SEARCH-M-PROC', tipo='service')
        self._make_guia('SEARCH-M-VOL', tipo='granel')
        scope = [('guide_name', 'in', names)]
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'product')]), 1)
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'processed')]), 1)
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'volume')]), 1)
        groups = self.Console.read_group(scope, ['id'], ['ingestion_type'])
        self.assertEqual(len(groups), 3)


    # ── 4. Producto real: búsqueda sin duplicar ────────────────────────────
    def test_05_producto_real_busqueda(self):
        names = ['SEARCH-P-1', 'SEARCH-P-2', 'SEARCH-P-G']
        rec1 = self._make_reception('SEARCH-P-1')
        self._add_reception_line(rec1, self.product_a, 'L1')
        rec2 = self._make_reception('SEARCH-P-2')
        self._add_reception_line(rec2, self.product_a, 'L1')
        self._add_reception_line(rec2, self.product_b, 'L2')
        guia = self._make_guia('SEARCH-P-G', tipo='service')
        self._add_guia_line(guia, self.product_a, 'GL1')
        scope = [('guide_name', 'in', names)]
        self.assertTrue(self._console_of(rec2))
        rows = self.Console.search_read(
            scope + [('product_filter_id', '=', self.product_a.id)], ['id'])
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({r['id'] for r in rows}), 3)
        self.assertEqual(
            self._cnt(scope + [('product_filter_id', '=', self.product_b.id)]),
            1)
        c2 = self._console_of(rec2)
        self.assertFalse(c2.product_id)

    # ── 5. Procesador por relación existente ───────────────────────────────
    def test_06_procesador_por_orden_de_procesamiento(self):
        guia = self._make_guia('SEARCH-PROC', tipo='service')
        c = self._console_of(guia)
        self.assertFalse(c.processor_id)
        toll = self.env['toll.processing.order'].create({
            'processor_id': self.processor.id,
            'service_product_id': self.service_product.id,
        })
        guia.write({'toll_order_id': toll.id})
        guia.flush_recordset()
        self.env.invalidate_all()
        c = self._console_of(guia)
        self.assertEqual(c.processor_id, self.processor)
        self.assertNotEqual(c.processor_id, c.partner_id)
        groups = self.Console.read_group(
            [('guide_name', '=', 'SEARCH-PROC')], ['id'], ['processor_id'])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['processor_id'][0], self.processor.id)

    # ── 6. Incompletos + usuario operativo + navegación ────────────────────
    def test_07_incompletos_usuario_operativo_y_navegacion(self):
        guia = self._make_guia(
            'SEARCH-INCOMPLETE', tipo='service', partner_id=False)
        c = self._console_of(guia)
        self.assertTrue(c)
        self.assertFalse(c.oc_documental)
        self.assertFalse(c.processor_id)
        self.assertFalse(c.partner_id)
        n = self.Console.with_user(self.operator).search_count(
            [('guide_name', 'in', ['SEARCH-INCOMPLETE'])])
        self.assertEqual(n, 1)
        action = c.action_open_source()
        inner = action['params']['action_to_execute']
        self.assertEqual(inner['res_model'], 'madenat.guia.processing')
        self.assertEqual(inner['res_id'], guia.id)

    # ── 7. Sin duplicación de filas en la vista ────────────────────────────
    def test_08_sin_duplicacion_de_filas(self):
        self._make_reception('SEARCH-DUP-R')
        self._make_guia('SEARCH-DUP-G', tipo='granel')
        rows = self.Console.search_read(
            [('guide_name', 'in', ['SEARCH-DUP-R', 'SEARCH-DUP-G'])],
            ['id', 'source_model', 'source_res_id'])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({r['id'] for r in rows}), 2)


    # ── 8. Combinación de filtros de modalidad (verificación aislada) ───────
    def test_09_combinacion_modalidad_por_and(self):
        """Los filtros de modalidad NO son excluyentes en la UI: se pueden
        combinar y se resuelven por AND. Dos modalidades distintas -> vacío.
        (La comprobación en navegador —V3— queda pendiente.)"""
        self._make_reception('SEARCH-MIX-P')
        self._make_guia('SEARCH-MIX-V', tipo='granel')
        scope = [('guide_name', 'in', ['SEARCH-MIX-P', 'SEARCH-MIX-V'])]
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'product')]), 1)
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'volume')]), 1)
        # Combinación (AND) de dos modalidades distintas -> intersección vacía.
        self.assertEqual(
            self._cnt(scope + [('ingestion_type', '=', 'product'),
                               ('ingestion_type', '=', 'volume')]), 0)

    # ── 9. La lista distingue emisión vs recepción (no solo el help) ───────
    def test_10_lista_muestra_origen_de_fecha(self):
        """La vista de LISTA expone `guide_date_kind` para que el usuario
        distinga la fecha de emisión de la de recepción fila a fila."""
        arch = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_list'
        ).arch
        self.assertIn("name=\"guide_date_kind\"", arch)
        self.assertIn("name=\"guide_date\"", arch)

