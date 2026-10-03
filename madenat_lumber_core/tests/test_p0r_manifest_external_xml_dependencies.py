# -*- coding: utf-8 -*-
"""P0-R (F-P0R-A) — Contrato estático de dependencias externas de las vistas.

Verifica, **sin instalar Odoo ni crear base de datos**, que todo XML ID externo
(``modulo.registro``) referenciado desde los XML declarados en ``data[]`` de
``madenat_lumber_core/__manifest__.py`` esté respaldado por una dependencia
explícita (``depends``) o por un módulo del núcleo Odoo garantizado.

Motivación (F-P0R-A): ``views/madenat_views_extensions.xml`` referenciaba el
menú raíz del addon Contacts sin declarar ``contacts`` en ``depends``. En una
base limpia ese addon no está instalado y la carga del XML fallaba con
``odoo.tools.convert.ParseError`` /
``AssertionError: The ID "..." refers to an uninstalled module``.
``madenat_test`` ocultaba el defecto porque Contacts ya estaba instalado.

Alcance (regla 5): el test se limita a los XML declarados por el manifest de
**este** módulo; no explora módulos ajenos ni requiere el ORM.

Detección (sin falsos positivos): se parsean los XML y se extraen únicamente
atributos que portan XML IDs reales — ``id``/``ref``/``parent``/``action``/
``t-call`` (valor único), ``groups`` (lista) y ``eval``/``context``/``name``
(``ref('...')``, ``'..._view_ref': '...'`` y ``%(...)<s|d>``). No se inspecciona
el texto libre (comentarios, dominios de campo ni expresiones de vista), por lo
que nombres de modelo (``stock.lot``), dominios (``parent.x``) o placeholders no
generan falsos positivos.

Integración con el runner de Odoo (P0-R, T-P0R-FIX-04)
------------------------------------------------------
El runner de Odoo solo recoge clases que heredan de ``BaseCase`` y exponen
``test_tags``; una ``unittest.TestCase`` plana queda descartada por
``TagsSelector`` (no tiene ``test_tags``). Por eso la clase de contrato hereda
de ``TransactionCase`` y se etiqueta con ``p0r`` cuando Odoo está disponible,
de modo que ``--test-tags p0r`` la ejecute. El módulo sigue siendo ejecutable de
forma autónoma (gate estático sin Odoo) con ``python3 <este archivo>``.
"""

import ast
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

try:  # Integración con el runner de Odoo (T-P0R-FIX-04).
    from odoo.tests import tagged
    from odoo.tests.common import TransactionCase
except ImportError:  # pragma: no cover - entorno sin Odoo (gate estático).
    def tagged(*_args, **_kwargs):
        """Decorador no-op cuando Odoo no está disponible (ejecución autónoma)."""
        return lambda cls: cls

    TransactionCase = unittest.TestCase


MODULE_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = MODULE_ROOT / '__manifest__.py'
MODULE_TECH_NAME = 'madenat_lumber_core'

# Módulos siempre presentes en cualquier instalación Odoo o garantizados por las
# dependencias declaradas del manifest. `contacts` NO figura aquí a propósito:
# el Core no usa funcionalmente el addon Contacts (solo referenciaba su menú
# accesorio, hoy desacoplado por F-P0R-A). La lista se definió conforme al
# manifest y a las referencias reales verificadas de las vistas del Core.
BASE_MODULES = frozenset({
    'base',      # raíz de Odoo, siempre instalada.
    'web',       # backend web, siempre presente (t-call web.*).
    'mail',      # declarado en `depends`.
    'stock',     # declarado en `depends`.
    'product',   # declarado en `depends`.
    'purchase',  # declarado en `depends`.
    'sale',      # declarado en `depends`.
    'account',   # declarado en `depends`.
    'sms',       # declarado en `depends`.
    # `uom` es dependencia transitiva de `product`/`stock` (ambos en `depends`);
    # sus XML IDs (`uom.product_uom_cubic_meter`) están garantizados.
    'uom',
})

XMLID_RE = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z0-9_.]+$')
REF_CALL_RE = re.compile(r"ref\(\s*['\"]([A-Za-z0-9_.]+)['\"]\s*\)")
ACTION_PLACEHOLDER_RE = re.compile(r'%\(([A-Za-z0-9_.]+)\)[sd]')
VIEW_REF_KEY_RE = re.compile(
    r"['\"](?:form_view_ref|tree_view_ref|view_ref|search_view_ref)['\"]"
    r"\s*:\s*['\"]([A-Za-z0-9_.]+)['\"]")

SINGLE_XMLID_ATTRS = ('id', 'ref', 'parent', 'action', 't-call')
LIST_XMLID_ATTRS = ('groups',)
EXPRESSION_ATTRS = ('eval', 'context', 'name')


def load_manifest():
    """Devuelve el manifest como ``dict`` (regla 1)."""
    return ast.literal_eval(MANIFEST_PATH.read_text(encoding='utf-8'))


def iter_data_xml_paths(manifest):
    """Itera ``(ruta_relativa, Path)`` de los XML declarados en ``data[]``."""
    for rel in manifest.get('data', []):
        rel = str(rel)
        if not rel.endswith('.xml'):
            continue
        path = MODULE_ROOT / rel
        if path.exists():
            yield rel, path


def extract_external_xmlids(path):
    """Devuelve ``[(xmlid, etiqueta_elemento)]`` de los XML IDs hallados."""
    refs = []
    if path.suffix != '.xml' or not path.exists():
        return refs
    for element in ET.parse(path).iter():
        for attr, value in element.attrib.items():
            candidates = []
            if attr in SINGLE_XMLID_ATTRS:
                candidates.append(value)
            elif attr in LIST_XMLID_ATTRS:
                candidates.extend(part for part in value.split(','))
            elif attr in EXPRESSION_ATTRS:
                candidates.extend(REF_CALL_RE.findall(value))
                candidates.extend(ACTION_PLACEHOLDER_RE.findall(value))
                candidates.extend(VIEW_REF_KEY_RE.findall(value))
            for candidate in candidates:
                candidate = candidate.strip()
                if XMLID_RE.match(candidate):
                    refs.append((candidate, element.tag))
    return refs


def collect_missing_dependencies(manifest):
    """Devuelve ``[(xml_rel, xmlid, modulo)]`` sin dependencia declarada."""
    allowed = (set(manifest.get('depends', []))
               | BASE_MODULES
               | {MODULE_TECH_NAME})
    missing = []
    for rel, path in iter_data_xml_paths(manifest):
        for xmlid, _tag in extract_external_xmlids(path):
            module = xmlid.split('.', 1)[0]
            if module not in allowed:
                missing.append((rel, xmlid, module))
    return missing



@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core', 'p0r')
class TestP0rManifestExternalXmlDependencies(TransactionCase):
    """Contrato estático manifest <-> XML de vistas (F-P0R-A).

    F-P0R-I: los métodos ``test_*`` viven DIRECTAMENTE en ``__dict__`` de esta
    clase (no en un mixin), de modo que el loader de Odoo los descubre bajo
    ``--test-tags p0r``. Sin Odoo, ``TransactionCase`` degrada a
    ``unittest.TestCase`` y el módulo sigue siendo ejecutable de forma autónoma.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manifest = load_manifest()
        cls.depends = set(cls.manifest.get('depends', []))
        cls.data_xml = [rel for rel, _path in iter_data_xml_paths(cls.manifest)]

    # ── Regla 1 ───────────────────────────────────────────────────────────
    def test_manifest_is_readable_as_dict(self):
        self.assertIsInstance(self.manifest, dict)
        self.assertIn('depends', self.manifest)
        self.assertIn('data', self.manifest)

    # ── Reglas 2 y 3 ──────────────────────────────────────────────────────
    def test_contacts_reference_requires_declared_dependency(self):
        """No debe quedar ninguna referencia al addon Contacts sin declararlo."""
        offenders = []
        for rel, path in iter_data_xml_paths(self.manifest):
            for xmlid, _tag in extract_external_xmlids(path):
                module = xmlid.split('.', 1)[0]
                if module == 'contacts' and 'contacts' not in self.depends:
                    offenders.append('%s -> %s' % (rel, xmlid))
        if offenders:
            self.fail(
                "F-P0R-A: referencia(s) externa(s) al addon 'contacts' sin "
                "declararlo en depends=:\n  " + "\n  ".join(offenders)
                + "\nDeclara 'contacts' en depends o desacopla la referencia.")

    # ── Reglas 4, 5 y 6 ───────────────────────────────────────────────────
    def test_no_undeclared_external_xmlid_reference(self):
        """Todo XML ID externo debe estar en depends o en los módulos base."""
        missing = collect_missing_dependencies(self.manifest)
        if missing:
            lines = [
                "  %s -> %s (falta dependencia: %s)" % (rel, xmlid, module)
                for rel, xmlid, module in missing
            ]
            self.fail(
                "XML ID(s) de módulo(s) sin dependencia declarada "
                "(revisar depends o desacoplar la referencia):\n"
                + "\n".join(lines))

    # ── Regresión F-P0R-A ─────────────────────────────────────────────────
    def test_views_extensions_declared_and_dependencies_satisfied(self):
        """La vista C15/C16 sigue declarada y con dependencias satisfechas."""
        rel = 'views/madenat_views_extensions.xml'
        self.assertIn(rel, self.data_xml,
                      "%s debe permanecer declarado en data[]." % rel)
        allowed = self.depends | BASE_MODULES | {MODULE_TECH_NAME}
        offenders = [
            xmlid for xmlid, _tag in extract_external_xmlids(MODULE_ROOT / rel)
            if xmlid.split('.', 1)[0] not in allowed
        ]
        self.assertEqual(
            offenders, [],
            "Referencias XML sin dependencia declarada en %s: %s" % (
                rel, ", ".join(offenders)))


if __name__ == '__main__':
    # Ejecución autónoma sin Odoo (gate estático Fase 6): unittest plano.
    unittest.main(verbosity=2)
