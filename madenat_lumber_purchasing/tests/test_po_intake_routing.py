# -*- coding: utf-8 -*-
"""T-PO-INTAKE — Puerta única: la Orden de Compra no crea lumber.reception.

Cierra la brecha P1 de la auditoría de Intake (AD-50 / CANON 04). El botón
«Recepciones» de ``purchase.order`` deriva SIEMPRE al wizard universal
``madenat.lumber.intake.wizard`` y NUNCA crea ni abre una ``lumber.reception``
desde la Orden de Compra.

Cobertura T-PO-INTAKE-01..05 con conteos reales antes/después en los modelos
relevantes (no se simula únicamente el dict de retorno). Usa TransactionCase:
nada se persiste.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


INTAKE_WIZARD_XMLID = 'madenat_lumber_intake.action_madenat_lumber_intake_new'
INTAKE_WIZARD_MODEL = 'madenat.lumber.intake.wizard'


@tagged('post_install', '-at_install', 'madenat', 'purchasing')
class TestPOIntakeRouting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.intake_installed = bool(cls.env['ir.module.module'].search([
            ('name', '=', 'madenat_lumber_intake'),
            ('state', '=', 'installed'),
        ], limit=1))
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor PO-Intake Test',
            'is_company': True,
            'supplier_rank': 1,
        })
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        if not self.intake_installed:
            self.skipTest('madenat_lumber_intake no está instalado en esta BD.')

    # ── Helpers ────────────────────────────────────────────────────────────
    def _make_po(self, partner=None):
        return self.env['purchase.order'].create({
            'partner_id': (partner or self.partner).id,
        })

    def _counts(self):
        """Conteo real de los modelos que la acción NO debe tocar."""
        return {
            'reception': self.env['lumber.reception'].search_count([]),
            'lot': self.env['stock.lot'].search_count([]),
            'quant': self.env['stock.quant'].search_count([]),
            'move': self.env['stock.move'].search_count([]),
        }

    # ── T-PO-INTAKE-01 ─────────────────────────────────────────────────────
    def test_t_po_intake_01_action_opens_intake_wizard(self):
        """La acción devuelve una act_window del wizard Intake, no de recepción."""
        po = self._make_po()
        action = po.action_create_lumber_reception()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), INTAKE_WIZARD_MODEL)
        # Jamás apunta a lumber.reception (ni por modelo ni por res_id).
        self.assertNotEqual(action.get('res_model'), 'lumber.reception')
        self.assertFalse(action.get('res_id'))

        # La acción canónica de Intake resuelta por XML-ID es la misma familia.
        canonical = self.env.ref(INTAKE_WIZARD_XMLID)
        self.assertEqual(canonical.res_model, INTAKE_WIZARD_MODEL)

    # ── T-PO-INTAKE-02 ─────────────────────────────────────────────────────
    def test_t_po_intake_02_action_preloads_po_context(self):
        """El contexto aporta compañía, proveedor y referencia de PO."""
        po = self._make_po()
        action = po.action_create_lumber_reception()
        ctx = action.get('context') or {}

        self.assertIsInstance(ctx, dict)
        # "cuando existan": en una OC válida proveedor y compañía están presentes.
        self.assertTrue(po.partner_id)
        self.assertTrue(po.company_id)
        self.assertEqual(ctx.get('intake_po_id'), po.id)
        self.assertEqual(ctx.get('intake_po_name'), po.name)
        self.assertEqual(ctx.get('intake_po_partner_id'), po.partner_id.id)
        self.assertEqual(ctx.get('intake_po_company_id'), po.company_id.id)

        # El contexto es inocuo: el wizard real efectivamente abre con él y no
        # se inventan campos (claves de contraste, no `default_` inexistentes).
        wizard = self.env[INTAKE_WIZARD_MODEL].with_context(**ctx).create({})
        self.assertTrue(wizard.exists())
        self.assertEqual(wizard.intake_modality, 'normal')

    # ── T-PO-INTAKE-03 ─────────────────────────────────────────────────────
    def test_t_po_intake_03_action_creates_no_records(self):
        """Invocar la acción no crea recepción, lote, quant ni move."""
        po = self._make_po()
        before = self._counts()

        po.action_create_lumber_reception()

        self.assertEqual(self._counts(), before)
        self.assertEqual(
            self.env['lumber.reception'].search_count(
                [('purchase_id', '=', po.id)]),
            0)
        # La antigua recepción "REC-<PO>" ya no se genera desde la acción.
        self.assertFalse(self.env['lumber.reception'].search([
            ('name', '=', 'REC-%s' % po.name),
        ]))

    # ── T-PO-INTAKE-04 ─────────────────────────────────────────────────────
    def test_t_po_intake_04_po_without_partner_or_company_is_safe(self):
        """Sin proveedor/compañía: defaults válidos y cero recepción parcial.

        ``purchase.order`` exige ``partner_id`` en ``create``; para ejercer el
        contrato defensivo se usa un registro en memoria (``new``) sin proveedor
        ni compañía. La acción no debe fallar ni crear nada parcialmente.
        """
        po = self.env['purchase.order'].new({
            'partner_id': False,
            'company_id': False,
        })
        before = self._counts()

        action = po.action_create_lumber_reception()

        self.assertEqual(action.get('res_model'), INTAKE_WIZARD_MODEL)
        ctx = action.get('context') or {}
        self.assertFalse(ctx.get('intake_po_partner_id'))
        self.assertFalse(ctx.get('intake_po_company_id'))
        self.assertEqual(self._counts(), before)

    # ── T-PO-INTAKE-05 ─────────────────────────────────────────────────────
    def test_t_po_intake_05_intake_owns_documental_reading(self):
        """Sin documento procesado, Intake no genera recepción desde la OC.

        La acción de PO solo abre el wizard; la lectura documental
        (``extract_document``) y la creación de la recepción siguen siendo
        responsabilidad exclusiva de Intake. Sin documento, Intake rechaza la
        lectura y no crea nada.
        """
        po = self._make_po()
        before = self._counts()

        action = po.action_create_lumber_reception()
        ctx = action.get('context') or {}
        wizard = self.env[INTAKE_WIZARD_MODEL].with_context(**ctx).create({})

        with self.assertRaises(UserError):
            wizard.action_preview_document()

        self.assertEqual(wizard.state, 'draft')
        self.assertEqual(self._counts(), before)
        self.assertEqual(
            self.env['lumber.reception'].search_count(
                [('purchase_id', '=', po.id)]),
            0)

