# -*- coding: utf-8 -*-
"""Guardrail estático manifest↔XML: dependencias de XML IDs externos.

Verifica, **sin instalar Odoo ni crear base de datos**, que todo XML ID externo
(``modulo.registro``) referenciado desde los XML del módulo esté respaldado por
una dependencia declarada (``depends``) o por un módulo del núcleo garantizado.

Origen — F-P0R-A: ``views/madenat_views_extensions.xml`` (saneamiento C15 del
*app switcher*) referenciaba ``contacts.menu_contacts`` sin declarar ``contacts``
en ``depends``. En una base limpia el addon Contacts no está instalado y la carga
del XML fallaba con ``odoo.tools.convert.ParseError`` /
``AssertionError: The ID "contacts.menu_contacts" refers to an uninstalled
module``. Una base con Contacts ya instalado ocultaba el defecto.

Alcance acotado (guardrail de bajo mantenimiento, NO un analizador XML
universal): sólo se inspeccionan los atributos que portan XML IDs reales —
``id``, ``parent``, ``action``, ``ref`` e ``inherit_id`` — y sólo cuando su valor
tiene forma estricta ``modulo.xml_id``. No se inspecciona texto libre
(comentarios, dominios de campo ni expresiones de vista), por lo que nombres de
modelo (``stock.lot``), dominios (``parent.x``) o IDs sin punto no generan
falsos positivos.
"""

import ast
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = MODULE_ROOT / '__manifest__.py'
MODULE_TECH_NAME = 'madenat_lumber_core'

# Vista de registro del hallazgo F-P0R-A. En `main` no está declarada en
# `data[]` (se carga en las ramas de integración), por eso se escanea
# explícitamente además de los XML declarados en el manifest.
F_P0R_A_VIEW = 'views/madenat_views_extensions.xml'

# Módulos del núcleo Odoo garantizados, más los que son dependencia transitiva
# de los declarados en `depends` del manifest:
#   base/web         -> presentes en toda instalación Odoo.
#   mail/stock/product/purchase/sale/account/sms -> declarados en `depends`.
#   uom              -> dependencia transitiva de product/stock (referenciado
#                       por `data/madenat_lumber_product_default_data.xml`).
# `contacts` NO se incluye a propósito: el Core gestiona contactos vía
# `res.partner` (provisto por `base`) y no usa funcionalmente el addon Contacts.
CORE_MODULES = frozenset({
    'base', 'web', 'mail', 'stock', 'product',
    'purchase', 'sale', 'account', 'sms', 'uom',
})

# Atributos que portan XML IDs; se aceptan sólo valores con forma `modulo.xml_id`.
XMLID_ATTRS = ('id', 'parent', 'action', 'ref', 'inherit_id')
XMLID_RE = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z0-9_]+$')


def load_manifest():
    """Carga el manifest como ``dict`` (sólo literal, sin importar Odoo)."""
    return ast.literal_eval(MANIFEST_PATH.read_text(encoding='utf-8'))


def declared_xml_paths(manifest):
    """Itera ``(ruta_relativa, Path)`` de los XML declarados en ``data[]``."""
    for rel in manifest.get('data', []):
        rel = str(rel)
        if rel.endswith('.xml') and (MODULE_ROOT / rel).exists():
            yield rel, MODULE_ROOT / rel


def scanned_xml_paths(manifest):
    """XML bajo contrato: los declarados en ``data[]`` más la vista F-P0R-A.

    La vista F-P0R-A se incluye aunque en `main` no figure en ``data[]``: en las
    ramas de integración sí se carga y es el archivo donde nació el defecto.
    """
    seen = set()
    for rel, path in declared_xml_paths(manifest):
        seen.add(rel)
        yield rel, path
    fp0ra = MODULE_ROOT / F_P0R_A_VIEW
    if F_P0R_A_VIEW not in seen and fp0ra.exists():
        yield F_P0R_A_VIEW, fp0ra


def _external_xmlids_from_root(root):
    """Extrae ``[(xmlid, modulo)]`` de los atributos XML-ID del árbol."""
    found = []
    for element in root.iter():
        for attr in XMLID_ATTRS:
            value = (element.get(attr) or '').strip()
            if XMLID_RE.match(value):
                found.append((value, value.split('.', 1)[0]))
    return found


def extract_external_xmlids(path):
    """XML IDs externos hallados en un archivo XML (``Path``)."""
    return _external_xmlids_from_root(ET.parse(path).getroot())


def extract_external_xmlids_from_text(xml_text):
    """XML IDs externos hallados en un texto XML (para casos de prueba)."""
    return _external_xmlids_from_root(ET.fromstring(xml_text))


def undeclared_references(manifest, paths):
    """Devuelve ``[(rel, xmlid, modulo)]`` sin dependencia ni módulo core."""
    allowed = (set(manifest.get('depends', []))
               | CORE_MODULES
               | {MODULE_TECH_NAME})
    missing = []
    for rel, path in paths:
        for xmlid, module in extract_external_xmlids(path):
            if module not in allowed:
                missing.append((rel, xmlid, module))
    return missing


class TestManifestExternalXmlDependencies(unittest.TestCase):
    """Contrato estático manifest <-> XML de vistas (F-P0R-A)."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()
        cls.depends = set(cls.manifest.get('depends', []))
        cls.scanned = list(scanned_xml_paths(cls.manifest))

    def test_manifest_is_readable_dict_with_depends(self):
        """El manifest es un ``dict`` con ``depends`` y ``data``."""
        self.assertIsInstance(self.manifest, dict)
        self.assertIn('depends', self.manifest)
        self.assertIn('data', self.manifest)

    def test_no_undeclared_external_xmlid_reference(self):
        """Todo XML ID externo debe estar en ``depends`` o en módulos core."""
        missing = undeclared_references(self.manifest, self.scanned)
        if missing:
            lines = [
                '  %s -> %s (falta dependencia: %s)' % (rel, xmlid, module)
                for rel, xmlid, module in missing
            ]
            self.fail(
                'XML ID(s) externos sin dependencia declarada (declarar el '
                'módulo en depends o desacoplar la referencia):\n'
                + '\n'.join(lines))

    def test_contacts_reference_requires_declared_dependency(self):
        """F-P0R-A: ninguna referencia a ``contacts.*`` sin declararla."""
        offenders = []
        for rel, path in self.scanned:
            for xmlid, module in extract_external_xmlids(path):
                if module == 'contacts' and 'contacts' not in self.depends:
                    offenders.append('%s -> %s' % (rel, xmlid))
        if offenders:
            self.fail(
                "F-P0R-A: referencia(s) externa(s) al addon 'contacts' sin "
                'declararlo en depends=:\n  ' + '\n  '.join(offenders)
                + "\nDeclara 'contacts' en depends o desacopla la referencia.")

    def test_detector_flags_external_xmlid_without_dependency(self):
        """El detector marca un ``modulo.xml_id`` externo sin dependencia."""
        sample = (
            '<odoo><data>'
            '<menuitem id="contacts.menu_contacts" groups="base.group_system"/>'
            '</data></odoo>'
        )
        found = extract_external_xmlids_from_text(sample)
        self.assertIn(('contacts.menu_contacts', 'contacts'), found)
        # Sin `contacts` en depends (ni en los módulos core) -> violación.
        allowed = self.depends | CORE_MODULES | {MODULE_TECH_NAME}
        self.assertNotIn('contacts', allowed)

    def test_detector_ignores_own_core_and_dotless_ids(self):
        """Ignora IDs sin punto, propios del módulo y módulos core/depends."""
        sample = (
            '<odoo><data>'
            '<field name="model">stock.lot</field>'
            '<field name="categ_id" ref="product.product_category_all"/>'
            '<field name="uom_id" ref="uom.product_uom_cubic_meter"/>'
            '<field name="inherit_id" ref="madenat_lumber_core.view_x"/>'
            '<record id="no_dot_id" model="ir.ui.view">'
            '<field name="domain">[("parent.x", "=", 1)]</field>'
            '</record>'
            '</data></odoo>'
        )
        modules = {module for _xmlid, module
                   in extract_external_xmlids_from_text(sample)}
        self.assertNotIn('stock', modules)       # 'stock.lot': texto, no atributo
        self.assertNotIn('no_dot_id', modules)   # id sin punto
        self.assertNotIn('parent', modules)      # 'parent.x': dominio, no atributo
        self.assertNotIn('ir', modules)          # model='ir.ui.view': no es XML-ID
        self.assertIn('product', modules)
        self.assertIn('uom', modules)
        self.assertIn('madenat_lumber_core', modules)


if __name__ == '__main__':
    unittest.main()
