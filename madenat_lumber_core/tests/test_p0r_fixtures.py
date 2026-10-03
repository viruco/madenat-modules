# -*- coding: utf-8 -*-
"""P0-R (F-P0R-B / F-P0R-C) — Fixtures SV compatibles con Core limpio y lectura
correcta del CSV de ACL.

Remediación trazable de los fallos de la segunda validación dinámica:

* F-P0R-B: ``SvTestCommon._sv_make_guia()`` enviaba ``conciliation_status``
  (campo inexistente en Core limpio, aportado por el addon externo de ingesta),
  produciendo ``ValueError: Invalid field ...``.  El campo real del Core,
  ``documental_conciliation_state``, es un computado ``store=True`` y no debe
  ser fijado por la fábrica.
* F-P0R-C: ``test_p0r_acl.test_06`` leía la columna ``perm_read`` (índice 4)
  como si fuera ``group_id:id`` (índice 3 del CSV estándar de Odoo).

Cubre T-P0R-TEST-01, T-P0R-TEST-02 y T-P0R-TEST-03.  Sin dependencia de módulos
externos: el CSV de seguridad y el código fuente de los tests se inspeccionan
también de forma estática (AST), por lo que no generan falsos positivos sobre
comentarios ni documentación.
"""
import ast
import unittest
from pathlib import Path

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .sv_test_common import SvTestCommon


TESTS_ROOT = Path(__file__).resolve().parent
MODULE_ROOT = TESTS_ROOT.parent
ACL_CSV_PATH = MODULE_ROOT / 'security' / 'ir.model.access.csv'
HELPER_PATH = TESTS_ROOT / 'sv_test_common.py'
GUIA_MODEL = 'madenat.guia.processing'

# Campo aportado por el addon externo de ingesta; inexistente en Core limpio.
EXTERNAL_GUIA_FIELD = 'conciliation_status'
# Campo real del Core (computado, store=True) de conciliación documental.
CORE_CONCILIATION_FIELD = 'documental_conciliation_state'

# CSV estándar de ACL de Odoo: el orden de columnas es fijo en el núcleo.
CSV_HEADER = (
    'id', 'name', 'model_id:id', 'group_id:id',
    'perm_read', 'perm_write', 'perm_create', 'perm_unlink',
)
CSV_GROUP_ID_INDEX = CSV_HEADER.index('group_id:id')  # -> 3
CSV_PERMS_SLICE = slice(
    CSV_HEADER.index('perm_read'), CSV_HEADER.index('perm_unlink') + 1)  # 4:8

SV_LEDGER_MODEL_XMLID = 'model_madenat_sv_operation'
SV_LEDGER_GROUPS = frozenset({
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_auditoria',
    'madenat_lumber_core.group_madenat_contabilidad',
})
SV_LEDGER_ALLOWED_GROUPS = SV_LEDGER_GROUPS | frozenset({
    'base.group_user', 'base.group_system',
})


def load_acl_csv():
    """Devuelve ``(encabezado, filas)`` del CSV de ACL, sin líneas vacías."""
    lines = [
        line for line in ACL_CSV_PATH.read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]
    header = tuple(lines[0].split(','))
    rows = [tuple(line.split(',')) for line in lines[1:]]
    return header, rows


def _guards_external_field(test_node):
    """True si ``test_node`` comprueba ``'<campo>' (not) in ...._fields``."""
    for node in ast.walk(test_node):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not (isinstance(left, ast.Constant)
                and left.value == EXTERNAL_GUIA_FIELD):
            continue
        if not any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            continue
        for comparator in node.comparators:
            if any(isinstance(sub, ast.Attribute) and sub.attr == '_fields'
                   for sub in ast.walk(comparator)):
                return True
    return False


def _collect_unguarded_field_keys(node, guarded=False):
    """Líneas donde ``EXTERNAL_GUIA_FIELD`` es clave de diccionario sin estar
    protegida por una guardia explícita de ``_fields``."""
    if isinstance(node, ast.If) and _guards_external_field(node.test):
        guarded = True
    found = []
    if isinstance(node, ast.Dict):
        for key in node.keys:
            if (isinstance(key, ast.Constant)
                    and key.value == EXTERNAL_GUIA_FIELD and not guarded):
                found.append(key.lineno)
    for child in ast.iter_child_nodes(node):
        found.extend(_collect_unguarded_field_keys(child, guarded))
    return found


def collect_unguarded_external_field_keys():
    """``{archivo: [líneas]}`` con claves ``EXTERNAL_GUIA_FIELD`` sin guardia."""
    offenders = {}
    for path in sorted(TESTS_ROOT.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        lines = _collect_unguarded_field_keys(tree)
        if lines:
            offenders[path.name] = sorted(lines)
    return offenders



@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
        'sv', 'p0r')
class TestP0rFixtures(SvTestCommon, TransactionCase):
    """T-P0R-TEST-01 — fábricas SV compatibles con instalación limpia de Core."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sv_setup_base()

    def test_01_helper_guia_compatible_core_limpio(self):
        """La fábrica crea la guía sin exigir campos de módulos externos."""
        Guia = self.env[GUIA_MODEL]
        # Regresión F-P0R-B: antes enviaba `conciliation_status` (inexistente en
        # Core limpio) y abortaba con ValueError al crear la guía.
        guia = self._sv_make_guia('P0R-FIX-01')
        self.assertTrue(guia.exists(), 'La fábrica SV debe crear la guía')

        # En una base sin el addon externo, el campo no existe y no se requiere.
        if EXTERNAL_GUIA_FIELD not in Guia._fields:
            self.assertFalse(
                hasattr(guia, EXTERNAL_GUIA_FIELD),
                'Core limpio no debe exponer el campo externo')

        # El campo real de conciliación documental del Core recibe un valor
        # válido de su selección (computado, store=True; no se inventa).
        self.assertIn(CORE_CONCILIATION_FIELD, Guia._fields)
        selection_values = {
            value for value, _label
            in Guia._fields[CORE_CONCILIATION_FIELD].selection
        }
        self.assertIn(guia.documental_conciliation_state, selection_values)


class TestP0rAclCsvStatic(unittest.TestCase):
    """T-P0R-TEST-02 — el CSV de ACL se interpreta con el orden real de Odoo."""

    @classmethod
    def setUpClass(cls):
        cls.header, cls.rows = load_acl_csv()

    def test_02_encabezado_estandar(self):
        """El encabezado coincide con el contrato estándar de Odoo."""
        self.assertEqual(self.header, CSV_HEADER)
        self.assertEqual(self.header[CSV_GROUP_ID_INDEX], 'group_id:id')
        self.assertEqual(
            self.header[CSV_PERMS_SLICE],
            ('perm_read', 'perm_write', 'perm_create', 'perm_unlink'))

    def test_02_todas_las_filas_tienen_ocho_columnas(self):
        """Toda fila se divide en las ocho columnas del contrato."""
        for row in self.rows:
            self.assertEqual(
                len(row), len(CSV_HEADER), 'Fila ACL malformada: %r' % (row,))

    def test_02_grupo_del_ledger_por_indice_correcto(self):
        """El grupo del ledger se lee en ``cols[3]`` y los permisos en 4:8."""
        ledger_rows = [r for r in self.rows if r[2] == SV_LEDGER_MODEL_XMLID]
        self.assertTrue(ledger_rows,
                        'Debe existir ACL para madenat.sv.operation')
        groups = set()
        for row in ledger_rows:
            group_xmlid = row[CSV_GROUP_ID_INDEX]
            groups.add(group_xmlid)
            # El grupo es un XML ID, nunca un dígito de permiso (regresión
            # F-P0R-C: antes se leía `perm_read` en cols[4]).
            self.assertNotIn(group_xmlid, ('0', '1'))
            self.assertIn(
                group_xmlid, SV_LEDGER_ALLOWED_GROUPS,
                'Grupo fuera de alcance en ACL SV: %s' % group_xmlid)
            perms = row[CSV_PERMS_SLICE]
            self.assertEqual(len(perms), 4)
            self.assertTrue(
                all(perm in ('0', '1') for perm in perms),
                'Permisos malformados: %r' % (perms,))
        # Presencia esperada de los tres grupos funcionales de Core.
        self.assertTrue(
            SV_LEDGER_GROUPS <= groups,
            'Faltan grupos funcionales: %s' % sorted(SV_LEDGER_GROUPS - groups))


class TestP0rStaticSourceGuards(unittest.TestCase):
    """T-P0R-TEST-03 — no regresión de campos inexistentes como clave."""

    def test_03_sin_clave_externa_sin_guardia(self):
        """``conciliation_status`` no debe usarse como clave sin guardia."""
        offenders = collect_unguarded_external_field_keys()
        self.assertEqual(
            offenders, {},
            'Uso de %r como clave sin guardia de _fields: %s' % (
                EXTERNAL_GUIA_FIELD, offenders))

    def test_03_helper_no_referencia_modulo_externo(self):
        """La fábrica SV no depende del módulo externo de ingesta."""
        source = HELPER_PATH.read_text(encoding='utf-8')
        self.assertNotIn('madenat_lumber_intake', source)


if __name__ == '__main__':
    unittest.main()
