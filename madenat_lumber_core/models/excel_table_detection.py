# -*- coding: utf-8 -*-
"""
Detector genérico y regresivo de tablas Excel para MADENAT.

Fuente ÚNICA de alias semánticos, normalización y detección estructural de
tablas para el módulo Core. No depende de ORM, de pandas ni de ningún nombre
de proveedor / RUT / guía / hoja / fila / columna: trabaja sobre una lista
plana de filas (``rows``) y mapea encabezados por CONTENIDO semántico.

Reglas de diseño (investigación 95083):

- Una sola tabla de alias canónicos (``CANONICAL_ALIASES``).
- Normalización: minúsculas, sin tildes, ``Nº/N°/No./N.`` → ``n``, sin
  puntuación no semántica, tokens separados, sin substring crudo.
- Patrones compuestos antes que alias simples (``pzas paq`` → pieces,
  ``cantidad paquetes`` → package_count, ``volumen paq`` → volume_m3,
  ``orden de produccion`` → production_order).
- Una columna ⇒ un solo campo semántico; un campo ⇒ una sola columna.
- Encabezado en ventanas de 1 a 3 filas.
- Totales/subtotales/notas excluidos por keyword, independiente de columna.
- Nunca fabrica producto, lote, dimensiones, piezas ni volumen.

Este helper es PURO: no usa ``self.env``, no escribe en BD y no lanza
excepciones de negocio. El llamador decide qué hacer según ``confidence``.
"""
import math
import re
import unicodedata


# ──────────────────────────────────────────────────────────────────────────
# 1. Conceptos canónicos y alias (fuente única)
# ──────────────────────────────────────────────────────────────────────────
CANONICAL_ALIASES = {
    'ticket_code':      ['n ticket', 'ticket', 'num ticket', 'etiqueta', 'n etiqueta'],
    'product_code':     ['codigo', 'cod', 'codigos', 'sku', 'material', 'codigo interno'],
    'description':      ['producto', 'descripcion', 'detalle', 'especie', 'subproducto',
                         'articulo', 'product'],
    'quality':          ['calidad', 'grado', 'grade'],
    'finish':           ['terminacion', 'terminado', 'acabado', 'finish'],
    'lot_or_package':   ['lote', 'batch', 'lot', 'paquete', 'bundle', 'pqte', 'package',
                         'n lote', 'n pqte', 'n paquete'],
    'production_order': ['orden', 'produccion', 'production order'],
    'thickness':        ['espesor', 'esp', 'thickness'],
    'width':            ['ancho', 'anc', 'width'],
    'length':           ['largo', 'lar', 'longitud', 'length'],
    'pieces':           ['cantidad', 'piezas', 'pzas', 'pz', 'unidades', 'qty', 'pcs',
                         'cant', 'unid'],
    'package_count':    ['paquetes', 'cant paquetes', 'n paquetes', 'num paquetes'],
    'volume_m3':        ['m3', 'volumen', 'vol', 'cbm', 'volume', 'cubico', 'pt'],
    'price':            ['precio', 'valor unitario', 'unit price', 'precio unitario'],
    'line_total':       ['total', 'importe', 'monto', 'amount'],
    'certificate':      ['certfor', 'certificacion', 'certification', 'certificado', 'certific'],
    'defect':           ['defecto', 'defects', 'defectos'],
    'dimensions_raw':   ['escuadria', 'escuadra', 'dimensiones', 'dimension', 'medida', 'medidas'],
    'document_item':    ['item', 'n item', 'num item', 'linea', 'line item'],
    'reference':        ['marca', 'referencia', 'reference'],
    'currency_or_unit': ['moneda', 'currency', 'divisa'],
}

# Patrones compuestos: se evalúan ANTES que los alias simples para
# desambiguar (p. ej. "Cantidad Paquetes" es package_count, NO pieces).
COMPOUND_PATTERNS = [
    ('orden de produccion', 'production_order'),
    ('orden produccion', 'production_order'),
    ('production order', 'production_order'),
    ('cantidad paquetes', 'package_count'),
    ('cant paquetes', 'package_count'),
    ('n paquetes', 'package_count'),
    ('num paquetes', 'package_count'),
    ('pzas paq', 'pieces'),
    ('piezas paq', 'pieces'),
    ('piezas por paquete', 'pieces'),
    ('volumen paq', 'volume_m3'),
    ('vol paq', 'volume_m3'),
    ('codigo interno', 'product_code'),
    ('n ticket', 'ticket_code'),
    ('valor unitario', 'price'),
    ('unit price', 'price'),
    ('n lote', 'lot_or_package'),
    ('n pqte', 'lot_or_package'),
    ('n paquete', 'lot_or_package'),
    ('esc fact', 'dimensions_raw'),
    ('cat certific', 'certificate'),
    ('n item', 'document_item'),
    ('line item', 'document_item'),
]

# Campos numéricos vs. de texto (para coerción de valores de detalle).
_NUMERIC_FIELDS = {
    'thickness', 'width', 'length', 'pieces', 'package_count',
    'volume_m3', 'price', 'line_total',
}
_TEXT_FIELDS = {
    'ticket_code', 'product_code', 'description', 'quality', 'finish',
    'lot_or_package', 'production_order', 'certificate', 'defect',
    'dimensions_raw', 'document_item', 'reference', 'currency_or_unit',
}
_IDENTIFIER_FIELDS = ('ticket_code', 'product_code', 'lot_or_package')

# Keywords de total/subtotal que marcan el FIN del detalle.
_TOTAL_KEYWORDS = ('total', 'subtotal', 'totales', 'suma', 'grand total')
# Keywords de notas/observaciones que se saltan sin truncar la tabla.
_NOTE_KEYWORDS = ('observacion', 'nota', 'note', 'observation', 'observaciones')

# Rótulos de total declarado (normalizados) para asociar valor→concepto en la
# fila de total. Se usan solo como fallback cuando el valor no está alineado a
# la columna semántica del encabezado.
_TOTAL_LABELS = {
    'volume_m3': ('volumen', 'vol total', 'total volumen', 'vol', 'm3', 'cbm', 'volume'),
    'pieces': ('piezas', 'pzas', 'pcs', 'pieza', 'cantidad', 'total piezas', 'pieces'),
    'package_count': ('paquetes', 'pqts', 'pqt', 'bultos', 'paquete', 'packages', 'total paquetes'),
}

# Umbrales.
_MIN_MATCH_SCORE = 60      # prefijo o mejor (descarta substring crudo = 40)
_COMPOUND_MIN_SCORE = 80   # frase completa para que un compuesto gane
_MIN_FIELDS = 2            # campos canónicos distintos mínimos
_MAX_HEADER_ROW = 60       # fila máxima donde buscar el encabezado


# ──────────────────────────────────────────────────────────────────────────
# 2. Normalización
# ──────────────────────────────────────────────────────────────────────────
def normalize_header(text):
    """Normaliza una celda de encabezado para comparación semántica.

    - minúsculas;
    - sin acentos/tildes (NFKD + eliminación de marcas);
    - ``Nº`` / ``N°`` / ``No.`` / ``N.`` → ``n``;
    - puntuación no semántica → espacio;
    - colapsa espacios; conserva tokens separados.
    """
    if text is None:
        return ""
    s = str(text)
    # Ordinal/degree ANTES de NFKD: 'º' se descompone a 'o' (Nº → No), así que
    # se elimina primero para que Nº/N° colapsen a 'n'.
    s = s.replace("º", "").replace("°", "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    # Abreviaturas de número antes de eliminar puntuación.
    s = re.sub(r"\bno\.\s*", "n ", s)            # "No."
    s = re.sub(r"\bn\.\s*", "n ", s)             # "N."
    s = re.sub(r"[^\w\s]", " ", s)               # puntuación → espacio
    s = re.sub(r"\s+", " ", s)
    return s.strip()


_normalize_cache = {}


def normalize_cached(text):
    """``normalize_header`` con caché (los alias/patrones son finitos)."""
    key = text if isinstance(text, str) else str(text)
    if key not in _normalize_cache:
        _normalize_cache[key] = normalize_header(key)
    return _normalize_cache[key]


# ──────────────────────────────────────────────────────────────────────────
# 3. Matching por tokens y límites de palabra
# ──────────────────────────────────────────────────────────────────────────
def _match_score(header_norm, alias_norm):
    """Puntaje de coincidencia de un alias normalizado contra un encabezado
    normalizado (sin substring crudo):
      100 exacto · 80 palabra/frase completa · 60 prefijo · 40 subcadena · 0
    """
    if not alias_norm or not header_norm:
        return 0
    if header_norm == alias_norm:
        return 100
    pattern = r"(?<![a-z0-9])" + re.escape(alias_norm) + r"(?![a-z0-9])"
    if re.search(pattern, header_norm):
        return 80
    if header_norm.startswith(alias_norm):
        return 60
    if alias_norm in header_norm:
        return 40
    return 0


def _match_field(header_norm):
    """Devuelve ``(field, score)`` para una celda de encabezado normalizada.

    Los patrones compuestos se prueban primero y, si alcanzan el umbral de
    frase completa, ganan de inmediato (desambiguación de ``Cantidad
    Paquetes`` vs. ``Pzas Paq.``).
    """
    if not header_norm:
        return None, 0

    best_field, best_score = None, 0
    for pattern, field in COMPOUND_PATTERNS:
        score = _match_score(header_norm, normalize_cached(pattern))
        if score > best_score:
            best_score = score
            best_field = field
    if best_score >= _COMPOUND_MIN_SCORE:
        return best_field, best_score

    best_field, best_score = None, 0
    for field, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            score = _match_score(header_norm, normalize_cached(alias))
            if score > best_score:
                best_score = score
                best_field = field
    return best_field, best_score


def build_column_mapping(header_row):
    """Mapeo ``{indice_columna: campo_canonico}`` para una fila de encabezado.

    - Compuestos antes que simples.
    - Una columna ⇒ un campo; un campo ⇒ una columna (el mayor puntaje gana).
    """
    if header_row is None:
        return {}, {}
    header_norm = [normalize_header(c) for c in header_row]
    col_best = []
    for idx, text in enumerate(header_norm):
        if not text:
            continue
        field, score = _match_field(text)
        if field is not None and score >= _MIN_MATCH_SCORE:
            col_best.append((idx, field, score))

    col_best.sort(key=lambda item: item[2], reverse=True)
    mapping = {}
    field_columns = {}
    used_fields = set()
    for idx, field, _score in col_best:
        if field in used_fields:
            continue
        mapping[idx] = field
        field_columns[field] = idx
        used_fields.add(field)
    return mapping, field_columns


# ──────────────────────────────────────────────────────────────────────────
# 4. Utilidades de celdas y valores
# ──────────────────────────────────────────────────────────────────────────
def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _to_number(value):
    """Convierte un valor de celda a float con decimales localizados.

    - ``31,75`` → 31.75 · ``4,877`` → 4.877 · ``1.234,56`` → 1234.56.
    - Devuelve ``None`` si no es parseable (no fabrica números).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in ('nan', 'none', 'null', ''):
        return None
    s = s.replace(' ', '')
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _is_blank_row(row):
    return all(_is_blank(v) for v in row)


def _is_total_row(norm_text):
    return any(k in norm_text for k in _TOTAL_KEYWORDS)


def _is_note_row(norm_text):
    return any(k in norm_text for k in _NOTE_KEYWORDS)


def _is_plausible_line(line):
    has_id = any(line.get(f) for f in _IDENTIFIER_FIELDS)
    has_num = any(
        (line.get(f) or 0) > 0
        for f in ('pieces', 'package_count', 'volume_m3', 'thickness', 'width', 'length')
    )
    if has_id and has_num:
        return True
    populated = [v for v in line.values() if v not in (None, '')]
    return len(populated) >= 2



# ──────────────────────────────────────────────────────────────────────────
# 5. Detección de tabla
# ──────────────────────────────────────────────────────────────────────────
def _build_mapping_from_window(cleaned, start, win):
    """Construye el mapeo combinando verticalmente ``win`` filas desde ``start``."""
    header_rows = cleaned[start:start + win]
    n_cols = max((len(r) for r in header_rows), default=0)
    col_texts = []
    for c in range(n_cols):
        parts = []
        for r in header_rows:
            cell = r[c] if c < len(r) else None
            if _is_blank(cell):
                continue
            parts.append(normalize_header(cell))
        col_texts.append(" ".join(parts))

    col_best = []
    for c, text in enumerate(col_texts):
        if not text:
            continue
        field, score = _match_field(text)
        if field is not None and score >= _MIN_MATCH_SCORE:
            col_best.append((c, field, score))

    col_best.sort(key=lambda item: item[2], reverse=True)
    mapping = {}
    field_columns = {}
    used_fields = set()
    for c, field, _score in col_best:
        if field in used_fields:
            continue
        mapping[c] = field
        field_columns[field] = c
        used_fields.add(field)
    return mapping, field_columns


def _match_total_label(norm_text, labels):
    """Devuelve True si ``norm_text`` es un rótulo de total (exacto o palabra
    completa dentro del texto)."""
    if not norm_text:
        return False
    for lbl in labels:
        if norm_text == lbl:
            return True
        if re.search(r'(?<![a-z0-9])' + re.escape(lbl) + r'(?![a-z0-9])', norm_text):
            return True
    return False


def _extract_declared_totals(row, field_columns, row_index, sheet):
    """Extrae totales declarados de la fila de total (no la agrega a ``lines``).

    - Primero intenta la columna semántica del encabezado (mapeo).
    - Si el valor no está alineado, busca rótulo→valor adyacente.
    - Si es ambiguo (múltiples valores distintos), no lo persiste y avisa.

    Devuelve ``(result, warnings)``.
    """
    n = len(row)
    norm_cells = [normalize_header(c) if not _is_blank(c) else '' for c in row]
    norm_joined = " ".join(x for x in norm_cells if x)

    kind = 'grand_total' if 'grand total' in norm_joined else (
        'subtotal' if 'subtotal' in norm_joined else (
            'total' if any(k in norm_joined for k in ('total', 'totales', 'suma')) else None))

    result = {
        'volume_m3': None,
        'pieces': None,
        'package_count': None,
        'kind': kind,
        'sheet': sheet,
        'row_index': row_index,
    }
    local_warnings = []

    def _num_at(i):
        if 0 <= i < n and not _is_blank(row[i]):
            return _to_number(row[i])
        return None

    for field, key in (('volume_m3', 'volume_m3'),
                       ('pieces', 'pieces'),
                       ('package_count', 'package_count')):
        value = None
        # 1. Alineado a la columna semántica del encabezado.
        col = field_columns.get(field)
        if col is not None:
            v = _num_at(col)
            if v is not None and v > 0:
                value = v
        # 2. Fallback: rótulo adyacente (totales desalineados).
        if value is None:
            candidates = []
            for i in range(n):
                if _match_total_label(norm_cells[i], _TOTAL_LABELS.get(field, ())):
                    for j in (i - 1, i + 1):
                        v = _num_at(j)
                        if v is not None and v > 0:
                            candidates.append(round(v, 4))
            unique = sorted(set(candidates))
            if len(unique) == 1:
                value = unique[0]
            elif len(unique) > 1:
                local_warnings.append(
                    'Total de %s ambiguo (múltiples valores detectados); no se persistirá.' % key)
                value = None

        if value is not None:
            if key in ('pieces', 'package_count'):
                value = int(round(value))
            result[key] = value

    return result, local_warnings


def _collect_detail(cleaned, header_end, field_columns):
    """Recoge líneas de detalle bajo el encabezado (saltando vacías y notas,
    deteniéndose en totales), con coerción tipada y sin fabricar campos.

    Devuelve ``(lines, declared_totals, total_warnings)``; la fila de total
    nunca entra en ``lines``.
    """
    lines = []
    declared_totals = None
    total_warnings = []
    for r in range(header_end, len(cleaned)):
        row = cleaned[r]
        if _is_blank_row(row):
            continue
        norm_text = " ".join(normalize_header(c) for c in row if not _is_blank(c))
        if _is_total_row(norm_text):
            declared_totals, total_warnings = _extract_declared_totals(
                row, field_columns, r, None)
            break
        if _is_note_row(norm_text):
            continue

        line = {}
        for field, col in field_columns.items():
            raw = row[col] if col < len(row) else None
            if _is_blank(raw):
                continue
            if field in _NUMERIC_FIELDS:
                num = _to_number(raw)
                if num is not None:
                    line[field] = num
            else:
                text = str(raw).strip()
                if text:
                    line[field] = text

        if _is_plausible_line(line):
            lines.append(line)
    return lines, declared_totals, total_warnings


def _empty_result(flow=None, warnings=None, diagnosis=None):
    return {
        'sheet': None,
        'header_rows': [],
        'header_start': None,
        'header_end': None,
        'column_mapping': {},
        'field_columns': {},
        'lines': [],
        'declared_totals': None,
        'confidence': 'low',
        'warnings': list(warnings or []),
        'diagnosis': list(diagnosis or []),
        'flow': flow,
    }



def detect_excel_table(rows, flow=None):
    """Detecta estructuralmente una tabla en ``rows`` (lista de listas).

    Devuelve un diccionario con: hoja (None aquí), fila(s) de encabezado,
    mapeo de columnas, líneas tipadas, confianza, warnings y diagnóstico.
    No lanza excepciones de negocio: el llamador decide según ``confidence``.
    """
    warnings = []
    diagnosis = []

    if not rows:
        return _empty_result(
            flow, warnings=['Sin filas para analizar.'],
            diagnosis=['input_vacio'])

    cleaned = []
    max_cols = 0
    for row in rows:
        r = list(row or [])
        cleaned.append(r)
        max_cols = max(max_cols, len(r))
    for r in cleaned:
        r.extend([None] * (max_cols - len(r)))

    n = len(cleaned)
    best = None  # (total_score, candidate)

    for win in (1, 2, 3):
        for start in range(0, min(n, _MAX_HEADER_ROW) - win + 1):
            mapping, field_columns = _build_mapping_from_window(cleaned, start, win)
            if len(field_columns) < _MIN_FIELDS:
                continue
            lines, declared_totals, total_warnings = _collect_detail(
                cleaned, start + win, field_columns)
            if not lines:
                continue
            score = len(field_columns) * 10 + len(lines)
            candidate = {
                'header_rows': list(range(start, start + win)),
                'header_start': start,
                'header_end': start + win,
                'column_mapping': dict(mapping),
                'field_columns': dict(field_columns),
                'lines': lines,
                'declared_totals': declared_totals,
                'total_warnings': total_warnings,
            }
            if best is None or score > best[0]:
                best = (score, candidate)

    if best is None:
        return _empty_result(
            flow,
            warnings=['No se detectó una tabla estructurable de columnas reconocibles.'],
            diagnosis=['sin_encabezado_reconocible'])

    _score, cand = best
    warnings.extend(cand.get('total_warnings') or [])
    fields = len(cand['field_columns'])
    plausible = len(cand['lines'])

    if fields >= 3 and plausible >= 2:
        confidence = 'high'
    elif fields >= 2 and plausible >= 1:
        confidence = 'medium'
        warnings.append(
            'Estructura parcial: %d columna(s) semántica(s), %d línea(s) plausible(s).' % (
                fields, plausible))
    else:
        confidence = 'low'

    diagnosis.append(
        'Encabezado en fila(s) %s (%d columna(s) semántica(s), %d línea(s)).' % (
            [i + 1 for i in cand['header_rows']], fields, plausible))

    return {
        'sheet': None,
        'header_rows': cand['header_rows'],
        'header_start': cand['header_start'],
        'header_end': cand['header_end'],
        'column_mapping': cand['column_mapping'],
        'field_columns': cand['field_columns'],
        'lines': cand['lines'],
        'declared_totals': cand.get('declared_totals'),
        'confidence': confidence,
        'warnings': warnings,
        'diagnosis': diagnosis,
        'flow': flow,
    }


def detect_excel_table_across_sheets(sheets, flow=None):
    """Evalúa todas las hojas candidatas y devuelve la mejor detección.

    ``sheets`` es una lista de ``(nombre, rows)``. No fija una hoja: elige por
    densidad semántica (más campos canónicos y más líneas plausibles).
    """
    best = None
    for name, rows in sheets:
        res = detect_excel_table(rows, flow=flow)
        if res is None or (res['confidence'] == 'low' and not res['field_columns']):
            continue
        res = dict(res)
        res['sheet'] = name
        if res.get('declared_totals'):
            res['declared_totals'] = dict(res['declared_totals'])
            res['declared_totals']['sheet'] = name
        score = len(res['field_columns']) * 10 + len(res['lines'])
        if best is None or score > best[0]:
            best = (score, res)
    if best is None:
        return _empty_result(
            flow,
            warnings=['Ninguna hoja contiene una tabla estructurable.'],
            diagnosis=['sin_hoja_con_tabla'])
    return best[1]
