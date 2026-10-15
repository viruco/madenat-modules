# -*- coding: utf-8 -*-
"""🛡️ Validación efectiva de guías duplicadas en la ingesta (2026-10-07).

Cierra la brecha de Procesado, Volúmenes y formulario directo de
``madenat.guia.processing`` reutilizando el validador existente
``madenat.reception.parser._check_guide_duplicate()``.

Ejecutado con usuario OPERATIVO real (grupo Operaciones) y SIN superusuario
en las acciones bajo prueba. ``TransactionCase``: todo se revierte al final.

Cobertura (mapea a la lista de pruebas obligatorias):
  IDENTIDAD   1-8    · OPERACIONES 9-17 · COBERTURA 18-21 · INTEGRIDAD 22-26
"""
import base64
import io
import logging

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'guide_duplicate_ingest')
class TestGuideDuplicateIngest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Parser = cls.env['madenat.reception.parser']
        cls.Guia = cls.env['madenat.guia.processing']
        cls.Reception = cls.env['lumber.reception']
        cls.location = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1).lot_stock_id
        if not cls.location:
            cls.location = cls.env['stock.location'].search(
                [('usage', '=', 'internal')], limit=1)
        cls.partner_a = cls.env['res.partner'].create(
            {'name': 'PROV A', 'is_company': True, 'supplier_rank': 1})
        cls.partner_b = cls.env['res.partner'].create(
            {'name': 'PROV B', 'is_company': True, 'supplier_rank': 1})
        # Usuario OPERATIVO real (sin superusuario) para las acciones bajo prueba.
        cls.u_ops = new_test_user(
            cls.env, login='gdup_ops',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_operaciones')
        # Usuario sin rol operativo (control negativo del guard RPC/ORM).
        cls.u_common = new_test_user(
            cls.env, login='gdup_common', groups='base.group_user')

    # ── Helpers ───────────────────────────────────────────────────────────
    def _guia_vals(self, name, partner=None):
        return {
            'name': name,
            'partner_id': (partner or self.partner_a).id,
            'assignment_location_id': self.location.id,
            'date_emission': '2026-06-11',
        }

    def _create_guia(self, name, partner=None, user=None):
        model = self.Guia if user is None else self.Guia.with_user(user)
        return model.create(self._guia_vals(name, partner))

    def _create_guia_incomplete(self, partner=None, user=None):
        """Guía en captura incompleta: sin número (marcador provisional)."""
        model = self.Guia if user is None else self.Guia.with_user(user)
        vals = {'assignment_location_id': self.location.id,
                'date_emission': '2026-06-11'}
        if partner is not None:
            vals['partner_id'] = partner.id
        return model.create(vals)

    def _create_reception(self, name):
        return self.Reception.create({
            'name': name,
            'guia_numero': name,
            'supplier_id': self.partner_a.id,
            'pdf_file': base64.b64encode(b'%PDF-1.4 dummy'),
            'excel_file': base64.b64encode(b'dummy-xlsx'),
        })

    @staticmethod
    def _xlsx_with_guide(number):
        """XLSX mínimo con número de guía legible por la regex de extracción."""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws['A1'] = 'Guía N°'
        ws['B1'] = number
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


    # ══════════════════════════════════════════════════════════════════════
    # IDENTIDAD (1-8)
    # ══════════════════════════════════════════════════════════════════════
    def test_01_new_guide_passes(self):
        """1. Documento nuevo: se crea sin bloqueo (usuario operativo)."""
        g = self._create_guia('NEW-01', user=self.u_ops)
        self.assertTrue(g.id)
        self.assertEqual(g.name, 'NEW-01')

    def test_02_confirmed_duplicate_same_model_blocks_on_create(self):
        """2. Duplicado confirmado en el mismo modelo (create)."""
        self._create_guia('DUP-01', self.partner_a)
        with self.assertRaises(UserError) as ctx:
            self._create_guia('DUP-01', self.partner_a, user=self.u_ops)
        self.assertIn('DUP-01', str(ctx.exception))
        self.assertIn('Guías Procesadas', str(ctx.exception))
        self.assertEqual(self.Guia.search_count([('name', '=', 'DUP-01')]), 1)

    def test_02b_confirmed_duplicate_same_model_blocks_on_write(self):
        """2b. Duplicado confirmado en el mismo modelo (write de la identidad)."""
        self._create_guia('DUP-02', self.partner_a)
        g = self._create_guia_incomplete(self.partner_a, user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'name': 'DUP-02'})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'New')  # sin cabecera parcial duplicada

    def test_03_cross_model_same_issuer_blocks(self):
        """3. CORREGIDO (2026-10-07): un Procesado con el MISMO número y el MISMO
        emisor que una Recepción existente ES el mismo documento → BLOQUEA.
        Homónimo legítimo (mismo nº, emisor DISTINTO) sigue permitido."""
        self._create_reception('HOM-01')          # supplier_id = partner_a
        with self.assertRaises(UserError):
            self._create_guia('HOM-01', self.partner_a, user=self.u_ops)
        g_ok = self._create_guia('HOM-01', self.partner_b, user=self.u_ops)
        self.assertTrue(g_ok.id, 'emisor distinto ⇒ homónimo permitido')

    def test_04_same_number_distinct_supplier_not_blocked(self):
        """4. Mismo número, proveedor positivamente distinto → no bloquea."""
        self._create_guia('SUP-01', self.partner_a)
        g = self._create_guia('SUP-01', self.partner_b, user=self.u_ops)
        self.assertTrue(g.id)

    def test_05_incomplete_capture_preserved(self):
        """5. Identidad incompleta: se conserva; un campo ajeno no revalida."""
        g = self._create_guia_incomplete(user=self.u_ops)
        self.assertEqual(g.name, 'New')
        g.with_user(self.u_ops).write({'date_emission': '2026-06-12'})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'New')
        self.assertEqual(str(g.date_emission), '2026-06-12')

    def test_06_identity_completion_reveals_duplicate(self):
        """6. Completar el emisor convierte la coincidencia en duplicado."""
        self._create_guia('CMP-01', self.partner_a)
        g = self._create_guia('CMP-01', self.partner_b, user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'partner_id': self.partner_a.id})

    def test_06b_incomplete_identity_not_blocked_then_completed(self):
        """6b / AJUSTE A: número homónimo con proveedor aún desconocido NO
        bloquea (se conserva la captura); al completar el proveedor se revalida
        y, si confirma el duplicado, se rechaza esa operación."""
        self._create_guia('CMP-02', self.partner_a)
        g = self._create_guia_incomplete(user=self.u_ops)  # proveedor nulo
        # Identidad incompleta: se permite y conserva (no bloquea).
        g.with_user(self.u_ops).write({'name': 'CMP-02'})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'CMP-02')
        # Completar el proveedor para igualar al existente → revalida y bloquea.
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'partner_id': self.partner_a.id})

    def test_07_cancelled_existing_still_blocks(self):
        """7. Documento existente cancelado NO se ignora (política vigente)."""
        g = self._create_guia('CAN-01', self.partner_a)
        g.write({'state': 'cancelled'})
        with self.assertRaises(UserError):
            self._create_guia('CAN-01', self.partner_a, user=self.u_ops)

    def test_08_self_exclusion_by_model_and_id(self):
        """8. El propio registro NUNCA es duplicado de sí mismo."""
        g = self._create_guia('SELF-01', self.partner_a)
        g.with_user(self.u_ops).write({'name': 'SELF-01'})
        g.with_user(self.u_ops).write({'partner_id': self.partner_a.id})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'SELF-01')

    def test_08b_exclusion_is_model_scoped(self):
        """8b. Excluir en un modelo NO oculta el registro del OTRO modelo.

        Recepción y guía comparten número pero con emisores distintos (para poder
        coexistir bajo la identidad ``número + emisor``); la exclusión se aplica
        sólo al modelo del registro propio.
        """
        r = self._create_reception('XREF-01')                 # supplier = partner_a
        g = self._create_guia('XREF-01', self.partner_b)      # emisor distinto
        # Excluir la GUÍA no oculta la RECEPCIÓN homónima (identidad de la recepción).
        with self.assertRaises(UserError) as ctx:
            self.Parser._check_guide_duplicate(
                'XREF-01', partner_id=self.partner_a.id, exclude_id=g.id,
                exclude_model='madenat.guia.processing', cross_model=True)
        self.assertIn('ya fue registrada en el sistema', str(ctx.exception))
        self.assertIn(str(r.id), str(ctx.exception))
        # Excluir la RECEPCIÓN no oculta la GUÍA homónima (identidad de la guía).
        with self.assertRaises(UserError) as ctx2:
            self.Parser._check_guide_duplicate(
                'XREF-01', partner_id=self.partner_b.id, exclude_id=r.id,
                exclude_model='lumber.reception', cross_model=True)
        self.assertIn('Guías Procesadas', str(ctx2.exception))
        self.assertIn(str(g.id), str(ctx2.exception))

    # ══════════════════════════════════════════════════════════════════════
    # OPERACIONES (9-17)
    # ══════════════════════════════════════════════════════════════════════
    def test_10_batch_create_intra_lote_duplicate_blocks(self):
        """10. create múltiple con duplicado DENTRO del lote → bloquea sin crear."""
        with self.assertRaises(UserError) as ctx:
            self.Guia.with_user(self.u_ops).create([
                self._guia_vals('BATCH-01', self.partner_a),
                self._guia_vals('BATCH-01', self.partner_a),
            ])
        self.assertIn('BATCH-01', str(ctx.exception))
        self.assertEqual(self.Guia.search_count([('name', '=', 'BATCH-01')]), 0)

    def test_12_write_multi_intra_lote_duplicate_blocks(self):
        """12. write sobre varios registros con la misma identidad COMPLETA → bloquea."""
        g1 = self._create_guia_incomplete(self.partner_a, user=self.u_ops)
        g2 = self._create_guia_incomplete(self.partner_b, user=self.u_ops)
        with self.assertRaises(UserError):
            (g1 | g2).with_user(self.u_ops).write(
                {'name': 'MULTI-01', 'partner_id': self.partner_a.id})

    def test_13_write_unrelated_field_not_validated(self):
        """13. Escritura de un campo ajeno a la identidad no revalida (no bloquea)."""
        self._create_guia('UNREL-03', self.partner_a)
        g = self._create_guia('UNREL-03', self.partner_b, user=self.u_ops)
        g.with_user(self.u_ops).write({'date_emission': '2026-06-30'})
        g.invalidate_recordset()
        self.assertEqual(str(g.date_emission), '2026-06-30')

    def test_14_extraction_assigns_number_blocks_on_duplicate(self):
        """14. Extracción que asigna el número después de create → valida."""
        self._create_guia('12345', self.partner_a)
        g = self._create_guia_incomplete(self.partner_a, user=self.u_ops)
        xlsx = self._xlsx_with_guide(12345)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write(
                {'excel_file': base64.b64encode(xlsx)})

    def test_15_reread_own_document_no_block(self):
        """15. Relectura del propio documento: idempotente, sin duplicar."""
        g = self._create_guia('12346', self.partner_a, user=self.u_ops)
        g.with_user(self.u_ops).write({'name': '12346'})
        self.assertEqual(self.Guia.search_count([('name', '=', '12346')]), 1)

    def test_16_complementary_documents_no_second_header(self):
        """16. PDF y Excel complementarios resuelven un único N° (una cabecera).

        Reafirmar el mismo número resuelto (p. ej. Excel tras PDF) no crea una
        segunda cabecera ni bloquea al propio registro.
        """
        g = self._create_guia_incomplete(user=self.u_ops)
        g.with_user(self.u_ops).write({'name': '12347'})
        g.with_user(self.u_ops).write({'name': '12347'})  # reafirmación
        self.assertEqual(self.Guia.search_count([('name', '=', '12347')]), 1)

    # ══════════════════════════════════════════════════════════════════════
    # COBERTURA (18-21)
    # ══════════════════════════════════════════════════════════════════════
    def test_18_procesado_route_write_blocks(self):
        """18. Procesado: action_verify_data fija name+partner vía write → bloquea."""
        self._create_guia('PROC-01', self.partner_a)
        g = self._create_guia_incomplete(user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write(
                {'name': 'PROC-01', 'partner_id': self.partner_a.id})

    def test_19_volumen_route_write_blocks(self):
        """19. Volúmenes: la ruta fija name+proveedor de cabecera vía write → bloquea."""
        self._create_guia('VOL-01', self.partner_a)
        g = self._create_guia_incomplete(user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write(
                {'name': 'VOL-01', 'partner_id': self.partner_a.id})

    def test_20_direct_form_write_blocks(self):
        """20. Formulario directo: nombre tecleado/bloqueado vía write → bloquea."""
        self._create_guia('FORM-01', self.partner_a)
        g = self._create_guia_incomplete(self.partner_a, user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'name': 'FORM-01'})

    def test_21_reception_path_regression(self):
        """21. Regresión del llamador existente (Recepción/Producto)."""
        r = self._create_reception('REC-01')
        with self.assertRaises(UserError):
            self.Parser._check_guide_duplicate('REC-01')
        # El propio registro se excluye correctamente (compatibilidad).
        self.Parser._check_guide_duplicate('REC-01', exclude_id=r.id)


    # ══════════════════════════════════════════════════════════════════════
    # INTEGRIDAD (22-26)
    # ══════════════════════════════════════════════════════════════════════
    def test_22_retry_double_execution(self):
        """22. Reintento/doble ejecución: sigue bloqueando sin duplicar."""
        self._create_guia('RETRY-01', self.partner_a)
        for _ in range(2):
            with self.assertRaises(UserError):
                self._create_guia('RETRY-01', self.partner_a, user=self.u_ops)
        self.assertEqual(self.Guia.search_count([('name', '=', 'RETRY-01')]), 1)

    def test_23_no_partial_header_or_lines_after_block(self):
        """23. Sin cabecera parcial ni líneas/efectos tras el rechazo."""
        self._create_guia('PART-01', self.partner_a)
        g = self._create_guia_incomplete(self.partner_a, user=self.u_ops)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'name': 'PART-01'})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'New')
        self.assertEqual(len(g.processing_line_ids), 0)

    def test_24_rollback_on_rejection(self):
        """24. Rollback completo ante rechazo (savepoint del wizard)."""
        self._create_guia('ROLL-01', self.partner_a)
        count_before = self.Guia.search_count([])
        try:
            with self.env.cr.savepoint():
                self._create_guia('ROLL-01', self.partner_a, user=self.u_ops)
        except UserError:
            pass
        self.assertEqual(self.Guia.search_count([]), count_before)

    def test_25_authorized_and_unauthorized_users(self):
        """25. Usuario autorizado ejecuta el control; sin rol → AccessError."""
        # Usuario operativo: ejecuta el control sin superusuario → bloquea.
        self._create_guia('AUTH-02', self.partner_a)
        with self.assertRaises(UserError):
            self._create_guia('AUTH-02', self.partner_a, user=self.u_ops)
        # Usuario sin rol operativo: el guard server-side lo rechaza.
        with self.assertRaises(AccessError):
            self.Guia.with_user(self.u_common).create(
                self._guia_vals('AUTH-01', self.partner_a))

    def test_26_concurrency_backstop_is_sql_constraint(self):
        """26. Concurrencia: el respaldo es el constraint SQL (no el search previo).

        El `search` previo protege el caso secuencial; NO declara blindaje
        concurrente. El backstop real de dos transacciones simultáneas es
        `UNIQUE(name, partner_id)` (y `UNIQUE(name)` en lumber.reception). Se
        documenta que la carrera con `partner_id` nulo NO queda cubierta por
        este constraint y requiere una propuesta separada.
        """
        names = [c[0] for c in self.Guia._sql_constraints]
        self.assertIn('unique_guia_processing_name_per_partner', names)


    # ══════════════════════════════════════════════════════════════════════
    # AJUSTES A / B / C (cierre 2026-10-07)
    # ══════════════════════════════════════════════════════════════════════
    def test_27_incomplete_unknown_supplier_then_distinct(self):
        """AJUSTE A: captura con proveedor desconocido se conserva; al completar
        con un proveedor distinto NO hay duplicado (homónimo permitido)."""
        self._create_guia('AA-01', self.partner_a)
        g = self._create_guia_incomplete(user=self.u_ops)  # proveedor nulo
        g.with_user(self.u_ops).write({'name': 'AA-01'})   # incompleto → no bloquea
        g.with_user(self.u_ops).write({'partner_id': self.partner_b.id})
        g.invalidate_recordset()
        self.assertEqual(g.name, 'AA-01')
        self.assertEqual(g.partner_id, self.partner_b)
        self.assertEqual(self.Guia.search_count([('name', '=', 'AA-01')]), 2)

    def test_28_cross_model_symmetric_blocks_same_issuer(self):
        """CORREGIDO (2026-10-07): el mismo documento (número + emisor) BLOQUEA
        en ambos sentidos; el emisor distinto sigue permitido. Reemplaza la
        antigua expectativa 'homónimo por modelo'."""
        # Sentido 1 — Recepción (emisor A) existente → ingreso de guía mismo
        # emisor → BLOQUEA.
        self._create_reception('SYM-01')                 # supplier = partner_a
        with self.assertRaises(UserError):
            self._create_guia('SYM-01', self.partner_a, user=self.u_ops)
        # Emisor distinto → homónimo legítimo → permitido.
        g_ok = self._create_guia('SYM-01', self.partner_b, user=self.u_ops)
        self.assertTrue(g_ok.id)
        # Sentido 2 — Guía (emisor A) existente → ingesta de recepción con el
        # MISMO emisor → BLOQUEA (C1 con alcance cruzado e identidad conocida).
        self._create_guia('SYM-02', self.partner_a)
        with self.assertRaises(UserError):
            self.Parser._check_guide_duplicate(
                'SYM-02', partner_id=self.partner_a.id,
                exclude_model='lumber.reception', cross_model=True)
        # Sanity: sin emisor conocido NO se bloquea cross-model (identidad incompleta).
        self.Parser._check_guide_duplicate(
            'SYM-02', partner_id=None,
            exclude_model='lumber.reception', cross_model=True)

    def test_29_homonym_warns_non_blocking(self):
        """AJUSTE C: homónimo → aviso NO bloqueante en el chatter (mecanismo
        existente mail.thread); la validación efectiva permanece en servidor."""
        # Homónimo mismo modelo (otro proveedor).
        self._create_guia('WARN-01', self.partner_a)
        g = self._create_guia_incomplete(user=self.u_ops)
        g.with_user(self.u_ops).write(
            {'name': 'WARN-01', 'partner_id': self.partner_b.id})
        warns = g.message_ids.filtered(
            lambda m: 'coincidente' in (m.body or ''))
        self.assertTrue(warns, "Debe existir un aviso no bloqueante de homónimo")
        self.assertEqual(g.name, 'WARN-01')  # no bloqueó
        # Homónimo entre modelos (recepción homónima, emisor DISTINTO).
        self._create_reception('WARN-02')                 # supplier = partner_a
        g2 = self._create_guia_incomplete(user=self.u_ops)
        g2.with_user(self.u_ops).write(
            {'name': 'WARN-02', 'partner_id': self.partner_b.id})
        warns2 = g2.message_ids.filtered(
            lambda m: 'coincidente' in (m.body or ''))
        self.assertTrue(warns2, "Debe avisar homónimo con la recepción")
        self.assertIn('Recepción directa', warns2[0].body or '')

    def test_30_residual_null_partner_risk_documented(self):
        """LÍMITE (documentado): dos guías con el mismo número y proveedor nulo
        NO colisionan en la SQL `UNIQUE(name, partner_id)` ni se bloquean en la
        captura (identidad incompleta). Riesgo residual visible; su cierre
        exige una propuesta separada (índice único parcial)."""
        a = self._create_guia_incomplete(user=self.u_ops)
        b = self._create_guia_incomplete(user=self.u_ops)
        a.with_user(self.u_ops).write({'name': 'NULL-01'})
        b.with_user(self.u_ops).write({'name': 'NULL-01'})
        self.assertEqual(self.Guia.search_count([('name', '=', 'NULL-01')]), 2)

