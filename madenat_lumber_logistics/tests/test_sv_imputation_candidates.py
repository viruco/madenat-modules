# -*- coding: utf-8 -*-
"""I2 — Candidatos SV CONTEXTUALES (contrato canónico único).

Cubre T-I2-CAND-01..12: elegibilidad por visibilidad multi-company estándar,
saldo documental I2, filtro condicional por ubicación del procesador,
prioridad procesador/producto/FIFO, reserva documental por estado, semántica
única flag/FIFO/guard y ausencia de efectos en stock/ledger/finanzas.

Datos 100 % transaccionales (TransactionCase, rollback). Ninguna prueba
asume BD vacía ni elimina el lote persistente de ``madenat_test``.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestSvImputationCandidatesI2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.uom_m3 = cls.env.ref('uom.product_uom_cubic_meter')
        cls.product = cls.env['product.product'].create({
            'name': 'I2C Lumber', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.product_other = cls.env['product.product'].create({
            'name': 'I2C Other', 'is_storable': True, 'tracking': 'lot',
            'uom_id': cls.uom_m3.id, 'uom_po_id': cls.uom_m3.id})
        cls.supplier = cls.env['res.partner'].create({
            'name': 'I2C Supplier', 'is_company': True})
        cls.Guia = cls.env['madenat.guia.processing']
        cls.StockLot = cls.env['stock.lot']
        cls.Imputation = cls.env['madenat.sv.imputation']
        cls.ImputationLine = cls.env['madenat.sv.imputation.line']
        cls.SvLine = cls.env['madenat.sv.imputation.sv.line']
        cls.AuditLog = cls.env['madenat.audit.log']
        cls.Operation = cls.env['madenat.sv.operation']
        cls.Wizard = cls.env['madenat.sv.imputation.wizard']

        def _mk(name, groups):
            return cls.env['res.users'].create({
                'name': name, 'login': name.lower(),
                'email': '%s@madenat.cl' % name.lower(),
                'groups_id': [(6, 0, [cls.env.ref(g).id for g in groups])]})
        cls.user_oper = _mk('i2c_oper', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_operaciones'])
        cls.user_jef = _mk('i2c_jef', [
            'base.group_user',
            'madenat_lumber_core.group_madenat_jefatura_operaciones'])

    # ── Fábricas (sudo: evita ACL de setup; las acciones usan with_user) ──
    def _guia(self, name):
        # `service_return_confirmation='yes'`: la guía destino debe estar marcada
        # como retorno de servicio para poder APLICAR (regla 2026-10-07).
        return self.Guia.sudo().create({
            'name': name, 'partner_id': self.supplier.id,
            'assignment_location_id': self.stock_loc.id,
            'state': 'verified', 'tipo_recepcion': 'granel',
            'service_return_confirmation': 'yes',
            'date_emission': '2026-10-02'})

    def _etiqueta(self, guia, name, nominal, product=None):
        lot = self.StockLot.sudo().create({
            'name': name, 'product_id': (product or self.product).id,
            'company_id': self.company.id, 'lot_flow_type': 'tarja',
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal})
        guia.sudo().write({'lot_ids': [(4, lot.id)]})
        return lot

    def _sv(self, guia, name, nominal, product=None, company_id=None,
            subproducto=None):
        vals = {
            'name': name, 'product_id': (product or self.product).id,
            'lot_flow_type': 'volume', 'volume_source_guia_id': guia.id,
            'volume_purchase_m3': nominal, 'vol_shipment_m3': nominal}
        if company_id is not None:
            vals['company_id'] = company_id
        if subproducto is not None:
            vals['subproducto_id'] = subproducto.id
        return self.StockLot.sudo().create(vals)

    def _quant(self, sv, location, qty):
        self.env['stock.quant'].sudo()._update_available_quantity(
            sv.product_id, location, qty, lot_id=sv)

    def _processor(self, name='I2C Planta'):
        partner = self.env['res.partner'].sudo().create({
            'name': name, 'is_company': True, 'is_processor': True})
        return partner, partner._get_or_create_processor_location()

    def _imp(self, guia, lines=None, reason=None, key=None,
             processor=None, processor_location=None):
        vals = {'guia_processing_id': guia.id, 'reason': reason}
        if key:
            vals['documentary_key'] = key
        if processor:
            vals['processor_id'] = processor.id
        if processor_location:
            vals['processor_location_id'] = processor_location.id
        imp = self.Imputation.sudo().create(vals)
        for etiqueta, allocs in (lines or []):
            line = self.ImputationLine.sudo().create({
                'imputation_id': imp.id,
                'processed_lot_id': etiqueta.id,
                'nominal_volume_m3': etiqueta.volume_purchase_m3})
            for sv, vol in allocs:
                self.SvLine.sudo().create({
                    'imputation_id': imp.id,
                    'imputation_line_id': line.id,
                    'sv_lot_id': sv.id,
                    'imputed_volume_m3': vol})
        return imp

    def _wiz(self, guia, processor=None):
        wiz = self.Wizard.sudo().with_context(
            active_model='madenat.guia.processing',
            active_id=guia.id).create({
                'guia_processing_id': guia.id,
                'processor_id': processor.id if processor else False})
        wiz._onchange_guia_processing_id()
        return wiz

    def _cand_lots(self, imp):
        return [d['lot'] for d in imp._i2_get_sv_candidate_data()]

    def _avail(self, sv):
        return self.Imputation._i2_sv_documental_available_m3(sv)

    def _snapshot(self):
        snap = {
            'quant': self.env['stock.quant'].search_count([]),
            'move': self.env['stock.move'].search_count([]),
            'lot': self.env['stock.lot'].search_count([]),
            'sv_op': self.env['madenat.sv.operation'].search_count([]),
        }
        for model in ('account.move', 'account.payment'):
            if model in self.env:
                snap[model] = self.env[model].search_count([])
        return snap


    # ── T-I2-CAND-01 ─────────────────────────────────────────────────────
    def test_t_i2_cand_01_sin_procesador_candidato_y_fifo(self):
        """Lote volume global, saldo documental > 0 y sin procesador: candidato."""
        guia = self._guia('I2C-01')
        etiqueta = self._etiqueta(guia, 'I2C-E01', 10.0)
        sv = self._sv(guia, 'SV00000009011', 50.0)
        imp = self._imp(guia, [(etiqueta, [])])
        self.assertIn(sv, self._cand_lots(imp))
        proposal = self._wiz(guia)._i2_propose_fifo(
            etiqueta.volume_purchase_m3, etiqueta)
        self.assertIn(sv, [lot for lot, _v in proposal])

    # ── T-I2-CAND-02 ─────────────────────────────────────────────────────
    def test_t_i2_cand_02_saldo_documental_no_positivo(self):
        """Saldo documental cero/negativo: no candidato; FIFO sin fallback."""
        guia = self._guia('I2C-02')
        etiqueta = self._etiqueta(guia, 'I2C-E02', 10.0)
        sv_zero = self._sv(guia, 'SV00000009021', 0.0)
        imp = self._imp(guia, [(etiqueta, [])])
        self.assertNotIn(sv_zero, self._cand_lots(imp))
        # Negativo: nominal 10 con 15 ya imputados activos.
        sv_neg = self._sv(guia, 'SV00000009022', 10.0)
        g2 = self._guia('I2C-02b')
        e2 = self._etiqueta(g2, 'I2C-E02b', 20.0)
        self._imp(g2, [(e2, [(sv_neg, 15.0)])])
        self.assertAlmostEqual(self._avail(sv_neg), -5.0, 3)
        self.assertNotIn(sv_neg, self._cand_lots(imp))
        # FIFO: ni fallback al nominal ni inclusión de no elegibles.
        proposal = self._wiz(guia)._i2_propose_fifo(10.0, etiqueta)
        proposed = [lot for lot, _v in proposal]
        self.assertNotIn(sv_zero, proposed)
        self.assertNotIn(sv_neg, proposed)

    # ── T-I2-CAND-03 ─────────────────────────────────────────────────────
    def test_t_i2_cand_03_procesador_filtra_por_ubicacion(self):
        """Con processor_location: exige quant interno positivo en su árbol."""
        processor, proc_loc = self._processor('I2C Planta 03')
        guia = self._guia('I2C-03')
        etiqueta = self._etiqueta(guia, 'I2C-E03', 10.0)
        sv_out = self._sv(guia, 'SV00000009031', 40.0)
        sv_in = self._sv(guia, 'SV00000009032', 40.0)
        self._quant(sv_in, proc_loc, 30.0)
        imp = self._imp(guia, [(etiqueta, [])], processor=processor,
                        processor_location=proc_loc)
        lots = self._cand_lots(imp)
        self.assertNotIn(sv_out, lots)
        self.assertIn(sv_in, lots)

    # ── T-I2-CAND-04 ─────────────────────────────────────────────────────
    def test_t_i2_cand_04_sin_procesador_no_excluye(self):
        """Sin procesador configurado no se excluye por falta de ubicación."""
        guia = self._guia('I2C-04')
        etiqueta = self._etiqueta(guia, 'I2C-E04', 10.0)
        sv = self._sv(guia, 'SV00000009041', 25.0)  # sin quant físico alguno
        imp = self._imp(guia, [(etiqueta, [])])
        self.assertFalse(imp.processor_location_id)
        self.assertIn(sv, self._cand_lots(imp))


    # ── T-I2-CAND-05 ─────────────────────────────────────────────────────
    def test_t_i2_cand_05_prioridad_producto_y_fifo(self):
        """producto antecede a no-producto; FIFO (create_date/id) desempata."""
        processor, proc_loc = self._processor('I2C Planta 05')
        guia = self._guia('I2C-05')
        etiqueta = self._etiqueta(guia, 'I2C-E05', 10.0)
        sv_a = self._sv(guia, 'SV00000009051', 40.0, product=self.product)
        self._quant(sv_a, proc_loc, 40.0)
        sv_b = self._sv(guia, 'SV00000009052', 40.0,
                        product=self.product_other)
        self._quant(sv_b, proc_loc, 40.0)
        sv_c = self._sv(guia, 'SV00000009053', 40.0, product=self.product)
        self._quant(sv_c, proc_loc, 40.0)
        imp = self._imp(guia, [(etiqueta, [])], processor=processor,
                        processor_location=proc_loc)
        lots = self._cand_lots(imp)
        # producto coincidente (A, C) precede a no coincidente (B)...
        self.assertLess(lots.index(sv_a), lots.index(sv_b))
        self.assertLess(lots.index(sv_c), lots.index(sv_b))
        # ...y entre coincidentes, FIFO por create_date/id: A < C.
        self.assertLess(lots.index(sv_a), lots.index(sv_c))
        # producto/proveedor NO son exclusión dura.
        self.assertIn(sv_b, lots)

    # ── T-I2-CAND-06 ─────────────────────────────────────────────────────
    def test_t_i2_cand_06_reserva_documental_por_estado(self):
        """draft/pending/applied consumen; reversed/cancelled no consumen."""
        g0 = self._guia('I2C-06o')
        sv = self._sv(g0, 'SV00000009061', 100.0)
        self.assertAlmostEqual(self._avail(sv), 100.0, 3)
        g = self._guia('I2C-06a')
        e = self._etiqueta(g, 'I2C-E06a', 40.0)
        self._imp(g, [(e, [(sv, 30.0)])])                      # draft
        self.assertAlmostEqual(self._avail(sv), 70.0, 3)
        g = self._guia('I2C-06b')
        e = self._etiqueta(g, 'I2C-E06b', 40.0)
        imp_p = self._imp(g, [(e, [(sv, 20.0)])])
        imp_p.with_user(self.user_oper).action_pending()        # pending
        self.assertAlmostEqual(self._avail(sv), 50.0, 3)
        g = self._guia('I2C-06c')
        e = self._etiqueta(g, 'I2C-E06c', 40.0)
        imp_a = self._imp(g, [(e, [(sv, 10.0)])])
        imp_a.with_user(self.user_oper).action_apply()          # applied
        self.assertAlmostEqual(self._avail(sv), 40.0, 3)
        g = self._guia('I2C-06d')
        e = self._etiqueta(g, 'I2C-E06d', 40.0)
        imp_r = self._imp(g, [(e, [(sv, 5.0)])])
        imp_r.with_user(self.user_oper).action_apply()
        self.assertAlmostEqual(self._avail(sv), 35.0, 3)
        imp_r.with_user(self.user_jef).action_reverse()         # reversed
        self.assertAlmostEqual(self._avail(sv), 40.0, 3)
        g = self._guia('I2C-06e')
        e = self._etiqueta(g, 'I2C-E06e', 40.0)
        imp_c = self._imp(g, [(e, [(sv, 5.0)])])
        imp_c.with_user(self.user_oper).action_cancel()         # cancelled
        self.assertAlmostEqual(self._avail(sv), 40.0, 3)


    # ── T-I2-CAND-07 ─────────────────────────────────────────────────────
    def test_t_i2_cand_07_semantica_unica_flag_fifo_guard(self):
        """flag/FIFO/guard comparten la MISMA semántica de candidato."""
        # A) candidato elegible sin sv_line_ids -> NO hay NO_SV_CANDIDATE.
        guia = self._guia('I2C-07a')
        etiqueta = self._etiqueta(guia, 'I2C-E07a', 10.0)
        sv = self._sv(guia, 'SV00000009071', 50.0)
        imp = self._imp(guia, [(etiqueta, [])])
        self.assertFalse(imp._i2_is_missing_sv_candidate())
        self.assertNotIn('NO_SV_CANDIDATE', imp.deviation_flags or '')
        imp.with_user(self.user_oper).action_apply()  # sin motivo: permitido
        self.assertEqual(imp.state, 'applied')
        # B) sin candidato y sin sv_line_ids -> SÍ hay NO_SV_CANDIDATE.
        processor, proc_loc = self._processor('I2C Planta 07')
        g = self._guia('I2C-07b')
        e = self._etiqueta(g, 'I2C-E07b', 10.0)
        imp_b = self._imp(g, [(e, [])], processor=processor,
                          processor_location=proc_loc)
        self.assertTrue(imp_b._i2_is_missing_sv_candidate())
        self.assertIn('NO_SV_CANDIDATE', imp_b.deviation_flags or '')
        # C) con sv_line_ids -> NO hay NO_SV_CANDIDATE.
        g = self._guia('I2C-07c')
        e = self._etiqueta(g, 'I2C-E07c', 10.0)
        sv_c = self._sv(g, 'SV00000009072', 50.0)
        imp_c = self._imp(g, [(e, [(sv_c, 10.0)])], processor=processor,
                          processor_location=proc_loc)
        self.assertFalse(imp_c._i2_is_missing_sv_candidate())
        self.assertNotIn('NO_SV_CANDIDATE', imp_c.deviation_flags or '')

    # ── T-I2-CAND-08 ─────────────────────────────────────────────────────
    def test_t_i2_cand_08_guard_blando(self):
        """Sin candidato: sin motivo pide motivo; con motivo aplica y audita."""
        processor, proc_loc = self._processor('I2C Planta 08')
        guia = self._guia('I2C-08')
        etiqueta = self._etiqueta(guia, 'I2C-E08', 10.0)
        imp = self._imp(guia, [(etiqueta, [])], processor=processor,
                        processor_location=proc_loc)
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'draft')
        imp.reason = 'Sin SV candidato; se deja constancia'
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')
        self.assertTrue(self.AuditLog.search([
            ('action_type', '=', 'deviation'),
            ('description', 'like', 'I2-NO-SV-CANDIDATE')]))


    # ── T-I2-CAND-09 ─────────────────────────────────────────────────────
    def test_t_i2_cand_09_aislado_sin_candidato(self):
        """Aislado: hay lote volume ajeno, pero el contexto no tiene candidato.

        Reproduce el espíritu de T-I2-06 sin asumir BD vacía ni borrar datos:
        flag + guard blando + aplicación con motivo.
        """
        guia = self._guia('I2C-09')
        etiqueta = self._etiqueta(guia, 'I2C-E09', 8.0)
        ajeno = self._sv(guia, 'SV00000009091', 100.0)
        processor, proc_loc = self._processor('I2C Planta 09')
        imp = self._imp(guia, [(etiqueta, [])], processor=processor,
                        processor_location=proc_loc)
        self.assertIn(ajeno, self.StockLot.search(
            [('lot_flow_type', '=', 'volume')]))
        self.assertNotIn(ajeno, self._cand_lots(imp))
        self.assertIn('NO_SV_CANDIDATE', imp.deviation_flags or '')
        with self.assertRaises(UserError):
            imp.with_user(self.user_oper).action_apply()
        imp.reason = 'Contexto sin candidato elegible'
        imp.with_user(self.user_oper).action_apply()
        self.assertEqual(imp.state, 'applied')

    # ── T-I2-CAND-10 ─────────────────────────────────────────────────────
    def test_t_i2_cand_10_visibilidad_multi_company(self):
        """company_id=False visible/elegible; otra compañía no elegible."""
        other = self.env['res.company'].sudo().create({
            'name': 'I2C Otra Compania'})
        guia = self._guia('I2C-10')
        etiqueta = self._etiqueta(guia, 'I2C-E10', 10.0)
        sv_global = self._sv(guia, 'SV00000009101', 40.0)    # company False
        sv_other = self._sv(guia, 'SV00000009102', 40.0, company_id=other.id)
        self.assertFalse(sv_global.company_id)
        self.assertEqual(sv_other.company_id, other)
        imp = self._imp(guia, [(etiqueta, [])])
        lots = self._cand_lots(imp)
        self.assertIn(sv_global, lots)
        self.assertNotIn(sv_other, lots)

    # ── T-I2-CAND-11 ─────────────────────────────────────────────────────
    def test_t_i2_cand_11_sin_efectos(self):
        """El helper/FIFO son solo consulta: sin efectos en stock/ledger/Fin."""
        guia = self._guia('I2C-11')
        etiqueta = self._etiqueta(guia, 'I2C-E11', 10.0)
        self._sv(guia, 'SV00000009111', 50.0)
        imp = self._imp(guia, [(etiqueta, [])])
        before = self._snapshot()
        imp._i2_get_sv_candidate_data()
        self._wiz(guia)._i2_propose_fifo(10.0, etiqueta)
        self.assertEqual(self._snapshot(), before)

    # ── T-I2-CAND-12 ─────────────────────────────────────────────────────
    def test_t_i2_cand_12_ausencias_orden_estable(self):
        """Ausencia de procesador/proveedor/producto: sin error ni exclusión."""
        guia = self._guia('I2C-12')
        etiqueta = self._etiqueta(guia, 'I2C-E12', 10.0)
        # volumen sin procesador y con producto no coincidente.
        sv = self._sv(guia, 'SV00000009121', 30.0, product=self.product_other)
        imp = self._imp(guia, [(etiqueta, [])])
        first = [d['lot'].id for d in imp._i2_get_sv_candidate_data()]
        second = [d['lot'].id for d in imp._i2_get_sv_candidate_data()]
        self.assertEqual(first, second)          # orden estable
        self.assertIn(sv, self._cand_lots(imp))  # no exclusión accidental
