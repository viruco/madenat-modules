# -*- coding: utf-8 -*-
"""P0-R (F-P0R-B / F-P0R-C / F-P0R-D) — Fixtures SV normalizadas contra el
contrato Core y lectura correcta del CSV de ACL.

Remediación trazable:

* F-P0R-B: ``SvTestCommon._sv_make_guia()`` enviaba ``conciliation_status``
  (inexistente en Core limpio, aportado por el addon externo de ingesta).
* F-P0R-C: ``test_p0r_acl.test_06`` leía ``perm_read`` (índice 4) como si fuera
  ``group_id:id`` (índice 3 del CSV estándar de Odoo).
* F-P0R-D: ``SvTestCommon._sv_make_guia()`` volvía a enviar un campo del addon
  externo, ``volume_pdf_m3``. Se corrige la CLASE del defecto: la fábrica valida
  sus ``vals`` contra ``madenat.guia.processing`` (``_sv_core_guia_vals``) y usa
  el campo Core ``vol_comercial_pdf``.

Cubre T-P0R-TEST-01/02/03 y T-P0R-FIX-01..05. Todos los tests de este módulo
heredan de ``TransactionCase`` y se etiquetan con ``p0r`` para que el runner de
Odoo los recoja bajo ``--test-tags p0r`` (T-P0R-FIX-04). El CSV de seguridad y
el código fuente se inspeccionan de forma estática (AST), sin falsos positivos
sobre comentarios ni documentación.
"""
import ast
from pathlib import Path

from odoo.tests import tagged
from odoo.tests.common import BaseCase, TransactionCase

from .sv_test_common import (
    SV_CORE_GUIA_FIELDS,
    SV_CORE_GUIA_REQUIRED_FIELDS,
    SV_GUIA_FORBIDDEN_EXTERNAL_FIELDS,
    SvTestCommon,
)


TESTS_ROOT = Path(__file__).resolve().parent
MODULE_ROOT = TESTS_ROOT.parent
ACL_CSV_PATH = MODULE_ROOT / 'security' / 'ir.model.access.csv'
HELPER_PATH = TESTS_ROOT / 'sv_test_common.py'
GUIA_MODEL = 'madenat.guia.processing'

# Campo aportado por el addon externo de ingesta; inexistente en Core limpio.
EXTERNAL_GUIA_FIELD = 'conciliation_status'
# Claves de addon externo que jamás deben formar parte de una fixture Core.
FORBIDDEN_GUIA_KEYS = frozenset(SV_GUIA_FORBIDDEN_EXTERNAL_FIELDS)
# Campo real del Core (computado, store=True) de conciliación documental.
CORE_CONCILIATION_FIELD = 'documental_conciliation_state'

# Etiquetas compartidas por los tests P0-R recogidos por el runner de Odoo.
P0R_TAGS = ('post_install', '-at_install', 'madenat', 'madenat_lumber_core',
            'p0r')

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
                and left.value in FORBIDDEN_GUIA_KEYS):
            continue
        if not any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            continue
        for comparator in node.comparators:
            if any(isinstance(sub, ast.Attribute) and sub.attr == '_fields'
                   for sub in ast.walk(comparator)):
                return True
    return False


def _collect_unguarded_field_keys(node, guarded=False):
    """``[(clave, línea)]`` de claves prohibidas usadas como literal de dict sin
    estar protegidas por una guardia explícita de ``_fields``."""
    if isinstance(node, ast.If) and _guards_external_field(node.test):
        guarded = True
    found = []
    if isinstance(node, ast.Dict):
        for key in node.keys:
            if (isinstance(key, ast.Constant)
                    and key.value in FORBIDDEN_GUIA_KEYS and not guarded):
                found.append((key.value, key.lineno))
    for child in ast.iter_child_nodes(node):
        found.extend(_collect_unguarded_field_keys(child, guarded))
    return found


def collect_unguarded_external_field_keys():
    """``{archivo: [(clave, línea)]}`` con claves prohibidas sin guardia."""
    offenders = {}
    for path in sorted(TESTS_ROOT.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        found = _collect_unguarded_field_keys(tree)
        if found:
            offenders[path.name] = sorted(found)
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

    # ── T-P0R-FIX-01 ──────────────────────────────────────────────────────
    def test_fix_01_contrato_de_keys_core(self):
        """Todas las keys de la fixture respetan el contrato Core."""
        Guia = self.env[GUIA_MODEL]
        vals = self._sv_guia_vals('P0R-FIX-01-CONTRACT')

        forbidden = sorted(set(vals) & FORBIDDEN_GUIA_KEYS)
        self.assertEqual(
            forbidden, [],
            'La fixture no debe contener claves de addon externo: %s'
            % forbidden)

        unknown = sorted(set(vals) - set(SV_CORE_GUIA_FIELDS))
        self.assertEqual(
            unknown, [],
            'Claves fuera de la lista blanca Core: %s' % unknown)

        missing_in_model = sorted(
            key for key in vals if key not in Guia._fields)
        self.assertEqual(
            missing_in_model, [],
            'Claves inexistentes en madenat.guia.processing: %s'
            % missing_in_model)

        non_stored_compute = sorted(
            key for key in vals
            if Guia._fields[key].compute and not Guia._fields[key].store)
        self.assertEqual(
            non_stored_compute, [],
            'La fixture no debe enviar campos computados no almacenados: %s'
            % non_stored_compute)

        for required in SV_CORE_GUIA_REQUIRED_FIELDS:
            self.assertIn(required, vals)

        # Regresión F-P0R-D: el volumen de la Guía PDF es `vol_comercial_pdf`.
        self.assertNotIn('volume_pdf_m3', vals)
        self.assertIn('vol_comercial_pdf', vals)

    # ── T-P0R-FIX-02 ──────────────────────────────────────────────────────
    def test_fix_02_fixture_minima_ejecutable(self):
        """La fixture mínima crea una guía Core válida (sin ``Invalid field``)."""
        Guia = self.env[GUIA_MODEL]
        guia = self._sv_make_guia('P0R-FIX-02')
        self.assertTrue(guia.exists())
        guia.invalidate_recordset()
        self.assertEqual(guia.state, 'verified')
        self.assertEqual(guia.tipo_recepcion, 'granel')
        self.assertAlmostEqual(guia.vol_comercial_pdf, 40.315, places=3)
        self.assertTrue(guia.name)
        self.assertTrue(guia.date_emission)
        for forbidden in FORBIDDEN_GUIA_KEYS:
            if forbidden not in Guia._fields:
                self.assertFalse(
                    hasattr(guia, forbidden),
                    'Core limpio no debe exponer %s' % forbidden)


@tagged(*P0R_TAGS)
class TestP0rAclCsvStatic(TransactionCase):
    """T-P0R-TEST-02 — el CSV de ACL se interpreta con el orden real de Odoo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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


@tagged(*P0R_TAGS)
class TestP0rStaticSourceGuards(TransactionCase):
    """T-P0R-TEST-03 / T-P0R-FIX-03 — no regresión de claves externas."""

    def test_03_sin_clave_externa_sin_guardia(self):
        """Ninguna clave prohibida debe usarse como dict key sin guardia."""
        offenders = collect_unguarded_external_field_keys()
        self.assertEqual(
            offenders, {},
            'Uso de claves prohibidas %s como dict key sin guardia de '
            '_fields: %s' % (sorted(FORBIDDEN_GUIA_KEYS), offenders))

    def test_03_helper_no_referencia_modulo_externo(self):
        """La fábrica SV no depende del módulo externo de ingesta."""
        source = HELPER_PATH.read_text(encoding='utf-8')
        self.assertNotIn('madenat_lumber_intake', source)

    def test_03_scanner_detecta_dict_key_prohibida(self):
        """El escáner AST detecta una dict key prohibida y respeta guardias."""
        # Las claves se construyen en runtime para que el propio código fuente
        # del test no contenga el patrón ``'<clave>':`` (evita falsos positivos
        # en los gates de búsqueda de claves externas).
        bad_key = 'volume_pdf_' + 'm3'
        guarded_key = 'conciliation_' + 'status'
        snippet = (
            "vals = {%r: 1.0, 'name': 'x'}\n" % bad_key
            + "msg = 'menciona %s en texto libre'\n" % guarded_key
            + "if %r in Guia._fields:\n" % guarded_key
            + "    guarded = {%r: 'ok'}\n" % guarded_key
        )
        found = _collect_unguarded_field_keys(ast.parse(snippet))
        keys = sorted({key for key, _lineno in found})
        self.assertEqual(
            keys, [bad_key],
            'El escáner debe detectar solo la dict key sin guardia: %s' % found)


# ── T-P0R-FIX-05 ──────────────────────────────────────────────────────────
@tagged(*P0R_TAGS)
class TestP0rStaticSelectionControl(TransactionCase):
    """Control de que las clases estáticas se recogen bajo ``--test-tags p0r``."""

    def test_fix_04_estaticas_heredan_basecase_y_estan_etiquetadas(self):
        """Las clases estáticas de este módulo heredan de BaseCase y tienen p0r."""
        for cls in (TestP0rAclCsvStatic, TestP0rStaticSourceGuards):
            self.assertTrue(
                issubclass(cls, BaseCase),
                '%s debe heredar de una BaseCase de Odoo' % cls.__name__)
            self.assertIn(
                'p0r', cls.test_tags,
                '%s debe estar etiquetada con p0r' % cls.__name__)
            self.assertIn('post_install', cls.test_tags)

    def test_fix_05_manifest_estatica_etiquetada_p0r(self):
        """La clase estática del contrato manifest<->XML está etiquetada p0r."""
        from .test_p0r_manifest_external_xml_dependencies import (
            TestP0rManifestExternalXmlDependencies as cls)
        self.assertTrue(issubclass(cls, BaseCase))
        self.assertIn('p0r', cls.test_tags)
        self.assertIn('post_install', cls.test_tags)
