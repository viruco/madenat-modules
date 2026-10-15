# -*- coding: utf-8 -*-
"""HOTFIX OWL — «Agregar una línea» en el documento de rebaja (2026-10-12).

Odoo 18 CE ya **no** compila el marcado heredado ``div.oe_chatter`` (el
compilador de formularios registra el selector ``chatter`` sobre el elemento
``<chatter/>``). Cuando el chatter no se reconoce, los campos
``message_follower_ids``/``message_ids`` se renderizan como **listas o2m
editables por defecto** (``mail.followers`` / ``mail.message``), mostrando
«Agregar una línea» y provocando un ``OwlError`` en
``Many2OneField.get urlRelation`` al interactuar con la columna ``res_id``
(``many2one_reference`` sin modelo determinable).

Casos (VIEW — evidencia de servidor; la renderización en navegador es
PENDIENTE y se documenta en el expediente ``HOTFIX_OWL_CHATTER_OE_20261012``):

* VIEW-02/03/04 — El chatter se declara con ``<chatter/>``; NO hay
  ``div.oe_chatter`` ni ``message_ids``/``message_follower_ids`` como campos
  sueltos (por lo tanto no aparecen listas editables con «Agregar una línea»).
* VIEW-05      — En el *arch efectivo* del documento y del asistente ningún
  ``Many2one`` carece de relación determinable: ningún ``many2one_reference``
  se declara sin su ``model_field`` presente en la vista.

Datos 100 % transaccionales (TransactionCase, rollback). Sin efectos físicos.
"""
from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOD = 'madenat_lumber_logistics'

# (modelo, xmlid de la vista form) de los formularios con chatter del
# mecanismo documental de rebaja/retorno.
FORMS = [
    ('madenat.sv.imputation',
     'madenat_lumber_logistics.view_madenat_sv_imputation_form'),
    ('madenat.processor.return.link',
     'madenat_lumber_logistics.view_madenat_processor_return_link_form'),
]

# Formularios que deben declararse con <chatter/> (incluye el asistente, que
# NO tiene chatter de negocio; se verifica que no quede marcado heredado).
WIZARD = ('madenat.sv.imputation.wizard',
          'madenat_lumber_logistics.view_madenat_sv_imputation_wizard_form')


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_logistics')
class TestHotfixOwlChatter(TransactionCase):

    def _effective_form_arch(self, model, xmlid):
        view = self.env.ref(xmlid)
        arch = self.env[model].get_view(
            view_id=view.id, view_type='form')['arch']
        if isinstance(arch, bytes):
            arch = arch.decode('utf-8')
        return arch

    def _field_nodes(self, arch):
        root = etree.fromstring(arch.encode('utf-8'))
        for node in root.iter('field'):
            yield node

    # ── VIEW-02/03/04: chatter canónico, sin listas editables filtradas ──
    def test_01_forms_declaran_chatter_canonico(self):
        for model, xmlid in FORMS:
            arch = self._effective_form_arch(model, xmlid)
            self.assertIn(
                '<chatter', arch,
                '%s debe declarar el chatter con el elemento <chatter/>' % model)
            self.assertNotIn(
                'class="oe_chatter"', arch,
                '%s no debe usar el marcado heredado div.oe_chatter' % model)
            self.assertIsNotNone(
                etree.fromstring(arch.encode('utf-8')).find('.//chatter'),
                '%s: el chatter debe declararse con <chatter/>' % model)

    def test_02_sin_campos_de_chatter_como_listas(self):
        """Los campos del chatter NO deben quedar como One2many sueltos."""
        forbidden = ('message_ids', 'message_follower_ids')
        for model, xmlid in FORMS:
            arch = self._effective_form_arch(model, xmlid)
            names = {node.get('name') for node in self._field_nodes(arch)}
            leaked = sorted(n for n in forbidden if n in names)
            self.assertFalse(
                leaked,
                '%s: campos de chatter filtrados como listas: %s'
                % (model, leaked))

    def test_03_wizard_sin_marcado_heredado(self):
        model, xmlid = WIZARD
        arch = self._effective_form_arch(model, xmlid)
        self.assertNotIn(
            'class="oe_chatter"', arch,
            'El asistente %s no debe contener marcado heredado oe_chatter'
            % model)

    # ── VIEW-05: sin Many2one con relación indeterminable en el arch efectivo ──
    def test_04_arch_efectivo_sin_many2one_sin_relacion(self):
        models = list(FORMS) + [WIZARD]
        for model, xmlid in models:
            arch = self._effective_form_arch(model, xmlid)
            Model = self.env[model]
            names = {node.get('name') for node in self._field_nodes(arch)}
            for node in self._field_nodes(arch):
                fname = node.get('name')
                if not fname or fname not in Model._fields:
                    continue
                field = Model._fields[fname]
                # Un campo declarado con widget exacto "many2one" debe ser
                # realmente Many2one con comodel válido.
                if node.get('widget') == 'many2one':
                    self.assertEqual(
                        field.type, 'many2one',
                        '%s.%s usa widget="many2one" pero es tipo %s'
                        % (model, fname, field.type))
                    self.assertTrue(
                        getattr(field, 'comodel_name', False),
                        '%s.%s es Many2one sin comodel' % (model, fname))
                # Un many2one_reference exige que su model_field esté en la
                # vista (si no, el cliente no puede resolver la relación).
                if field.type == 'many2one_reference':
                    model_field = getattr(field, 'model_field', None)
                    self.assertTrue(
                        model_field,
                        '%s.%s es many2one_reference sin model_field'
                        % (model, fname))
                    self.assertIn(
                        model_field, names,
                        '%s: %s (many2one_reference) requiere el campo '
                        'model_field "%s" en la vista'
                        % (model, fname, model_field))

    # ── VIEW-01 (proxy de servidor): la vista se compila/resuelve ──
    def test_05_get_view_resuelve_form_y_chatter(self):
        model, xmlid = FORMS[0]
        arch = self._effective_form_arch(model, xmlid)
        root = etree.fromstring(arch.encode('utf-8'))
        self.assertEqual(root.tag, 'form')
        self.assertIsNotNone(root.find('.//chatter'))
