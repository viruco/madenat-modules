# -*- coding: utf-8 -*-
"""🛡️ REGRESIÓN — Incidente guía 15183 (MADENAT, 2026-10-07).

Brecha comprobada del incidente:

    Un ingreso **Procesado** (`madenat.guia.processing`) con el MISMO número
    de guía y el MISMO emisor que una **Recepción** (`lumber.reception`) ya
    existente **NO se bloquea** con el código activo. La comprobación de
    duplicado confirmado usa `cross_model=False` y por tanto sólo inspecciona
    el propio modelo; el otro flujo sólo se advierte (aviso no bloqueante en
    el chatter), nunca bloquea.

Doctrina de la expectativa (requisito del incidente):
    Identidad documental = ``número + emisor``. Detectar una guía ya ingresada
    ANTES de duplicar sus efectos, aunque todavía esté en staging (sin stock).
    No usar el modelo distinto como exclusión automática; no bloquear números
    homónimos legítimos (mismo número, emisor DISTINTO).

Ejecutado con usuario OPERATIVO real y SIN superusuario. ``TransactionCase``:
todo se revierte. Sólo lectura sobre los datos reales; ningún registro real se
modifica. Se ejecuta contra una base AISLADA (`repro_inc_15183_20261007`).
"""
import base64
import logging

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user

_logger = logging.getLogger(__name__)

GUIDE_NO = '15183'          # número REAL del incidente
REG_NO = 'REPRO-15183'      # número sintético (fixture, no colisiona con reales)


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'guide_dup_regression_15183')
class TestGuideDuplicateRegression15183(TransactionCase):

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
        cls.emisor = cls.env['res.partner'].create(
            {'name': 'Emisor X', 'is_company': True, 'supplier_rank': 1})
        cls.otro = cls.env['res.partner'].create(
            {'name': 'Otro emisor', 'is_company': True, 'supplier_rank': 1})
        cls.u_ops = new_test_user(
            cls.env, login='gdup15183_ops',
            groups='base.group_user,'
                   'madenat_lumber_core.group_madenat_operaciones')

    # ── Helpers ──────────────────────────────────────────────────────────
    def _create_reception(self, name, partner):
        return self.Reception.create({
            'name': name,
            'guia_numero': name,
            'supplier_id': partner.id,
            'pdf_file': base64.b64encode(b'%PDF-1.4 dummy'),
            'excel_file': base64.b64encode(b'dummy-xlsx'),
        })

    def _guia_vals(self, name, partner):
        return {
            'name': name,
            'partner_id': partner.id,
            'assignment_location_id': self.location.id,
            'date_emission': '2026-10-07',
        }

    # ══════════════════════════════════════════════════════════════════════
    # EXACTO — datos REALES del incidente (sólo lectura)
    # ══════════════════════════════════════════════════════════════════════
    def test_E1_exact_incident_real_rows(self):
        """E1 — Sobre la Recepción REAL 15183 (id 1369) y su emisor real: la
        llamada de BLOQUEO de la ruta Procesado (`cross_model=False`) NO la ve;
        la llamada de AVISO (`cross_model=True`) SÍ la ve. Es el mecanismo
        exacto del incidente."""
        rec = self.Reception.sudo().search([('name', '=', GUIDE_NO)], limit=1)
        if not rec:
            self.skipTest('Sin datos reales 15183 en esta base aislada')
        sup = rec.supplier_id
        guia = self.Guia.sudo().search([('name', '=', GUIDE_NO)], limit=1)
        excl = guia.id if guia else None
        # Llamada de BLOQUEO de la ruta Procesado (idéntica al log del incidente):
        bloqueo = self.Parser._check_guide_duplicate(
            GUIDE_NO, partner_id=sup.id,
            exclude_id=excl,
            exclude_model='madenat.guia.processing',
            cross_model=False, raise_on_match=False)
        self.assertIsNone(
            bloqueo, 'cross_model=False NO ve la Recepción (no bloquea)')
        # Llamada de AVISO (cross_model=True) sí ve la Recepción:
        aviso = self.Parser._check_guide_duplicate(
            GUIDE_NO, partner_id=None,
            exclude_id=excl,
            exclude_model='madenat.guia.processing',
            cross_model=True, raise_on_match=False)
        self.assertIsNotNone(aviso, 'cross_model=True SÍ ve la Recepción')
        self.assertEqual(aviso[0], 'lumber.reception')
        self.assertEqual(aviso[1].id, rec.id)

    # ══════════════════════════════════════════════════════════════════════
    # REGRESIÓN (debe FALLAR con el código activo: la brecha se confirma)
    # ══════════════════════════════════════════════════════════════════════
    def test_R1_same_document_across_models_blocks_on_create(self):
        """R1 — Recepción 'REPRO-15183' (emisor E) existe; crear un Procesado
        del MISMO número y emisor E debe BLOQUEARSE (mismo documento)."""
        self._create_reception(REG_NO, self.emisor)
        with self.assertRaises(UserError):
            self.Guia.with_user(self.u_ops).create(
                self._guia_vals(REG_NO, self.emisor))

    def test_R2_same_document_across_models_blocks_on_write(self):
        """R2 — Ruta de fachada: guía incompleta → al fijar nombre + emisor
        iguales a la Recepción existente debe BLOQUEAR."""
        self._create_reception(REG_NO, self.emisor)
        g = self.Guia.with_user(self.u_ops).create({
            'assignment_location_id': self.location.id,
            'date_emission': '2026-10-07',
        })
        g.with_user(self.u_ops).write({'name': REG_NO})  # emisor desconocido → no bloquea (AJUSTE A)
        with self.assertRaises(UserError):
            g.with_user(self.u_ops).write({'partner_id': self.emisor.id})

    # ══════════════════════════════════════════════════════════════════════
    # NO-REGRESIÓN (homónimo legítimo: no debe bloquear AHORA ni tras el fix)
    # ══════════════════════════════════════════════════════════════════════
    def test_NG1_distinct_issuer_same_number_not_blocked(self):
        """NG1 — Mismo número, emisor DISTINTO ⇒ homónimo legítimo: NO bloquea."""
        self._create_reception(REG_NO, self.emisor)
        g = self.Guia.with_user(self.u_ops).create(
            self._guia_vals(REG_NO, self.otro))
        self.assertTrue(g.id)
        self.assertEqual(g.partner_id, self.otro)

