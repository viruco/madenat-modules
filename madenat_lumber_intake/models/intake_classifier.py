# -*- coding: utf-8 -*-
"""Clasificador robusto del tipo de ingreso (Producto / Procesado).

Módulo PURO (sin dependencias de Odoo): normalización de texto, comparación
por raíz y extracción de señales. Lo consumen:

  * ``madenat.lumber.intake.wizard`` (clasificación al pulsar "Leer documento");
  * la prueba en seco de solo lectura de la Fase 2A (script externo).

Señales analizadas — y SOLO estas (documentado en README §8):
  1. ``filename``       nombre del PDF y del Excel, sin extensión;
  2. ``pdf_title``      primeras ``TITLE_LINES`` líneas útiles del PDF;
  3. ``pdf_product``    filas de producto del PDF (>= 2 magnitudes numéricas, o
                        las que siguen a una cabecera DESCRIPCIÓN / GLOSA /
                        DETALLE / PRODUCTO);
  4. ``excel_product``  nombres de producto del Excel ya extraídos por
                        ``extract_document`` (``description`` /
                        ``product_name_original``).

El texto legal/institucional del PDF (SII, RUT, timbraje, resolución, firma
electrónica, URLs) NO es señal: se descarta antes de comparar, para evitar
falsos positivos como «Servicio de Impuestos Internos».

Comparación: minúsculas + sin acentos + por raíz al inicio de palabra, con
abreviaturas. Un keyword configurado se compara como raíz (``cepill`` coincide
con ``Cepillada``); además se genera su raíz morfológica (``cepillado`` →
``cepill``) y se aceptan abreviaturas punteadas del documento (``CEP.``) cuyo
prefijo (>= 3 letras) sea prefijo de algún keyword.
"""
import re
import unicodedata
from functools import lru_cache

# Zona de título del PDF: primeras líneas útiles (sin ruido institucional).
TITLE_LINES = 3
# Cota defensiva para documentos muy largos (no altera la decisión).
MAX_PRODUCT_LINES = 200

# Orden de evaluación de señales (determinista para la evidencia).
SOURCE_ORDER = ('filename', 'pdf_title', 'pdf_product', 'excel_product')

SOURCE_LABELS = {
    'filename': 'nombre de archivo',
    'pdf_title': 'título del PDF',
    'pdf_product': 'glosa de producto del PDF',
    'excel_product': 'nombre de producto del Excel',
}

# Unidades de origen que el motor puede etiquetar (perfiles métrico/imperial)
# más los tokens aceptados por `document_extractor._UNIT_TOKEN_RE`.
KNOWN_UNITS = frozenset({
    'mm', 'cm', 'm', 'in', 'inch', 'pulg', 'pies', 'ft', 'mt', 'mts',
    'm3', 'm2',
})

# Códigos de perfil del motor → perfiles de lectura del wizard compatibles.
# `packing_imperial_blanks` es ambiguo por diseño (Grado Clear vs S2S): el
# desempate por nombre de archivo vive en el onchange del wizard.
DETECTED_PROFILE_CODES = {
    'packing_metrico_aserrada': ('metric',),
    'packing_imperial_blanks': ('f1550', 'f5085'),
}

# ── Evidencia fuerte vs. débil (decisión de la Fase 2A, ver INFORME_FASE_2A) ──
# «Cepillada» describe el ARTÍCULO: aparece igual en compras de madera S2S
# (Producto) y en servicios de cepillado (Procesado). Prueba en seco: tratarla
# como decisiva desviaba 6 documentos ya registrados sin justificación.
# Por eso el vocabulario de artículo es ADVISORY (marca de advertencia) salvo
# en las señales donde el documento declara su naturaleza: nombre de archivo y
# título. El vocabulario de servicio («servicio», «maquila», «proceso») es
# decisivo en cualquier señal. Ambos vocabularios son configurables.
STRONG_SOURCES = frozenset({'filename', 'pdf_title'})
WEAK_KEYWORDS_DEFAULT = ('cepill', 'cep.')

# Ruido institucional/legal: nunca describe el producto. Se descarta la línea
# completa ANTES de comparar (evita «Servicio de Impuestos Internos»).
_NOISE_RE = re.compile(
    r'impuestos\s+internos'
    r'|\bs\s*i\s*i\b'
    r'|\br\s*u\s*t\b'
    r'|timbraje'
    r'|timbre\s+electronico'
    r'|resolucion\s+(ex|n)'
    r'|firma\s+electronica'
    r'|www\s'
    r'|@'
)

# Cabecera de la tabla de detalle (habilita las líneas siguientes como señal).
_PRODUCT_HEADER_RE = re.compile(r'\b(descripcion|glosa|detalle|producto|especie)\b')
_NUMBER_RE = re.compile(r'\d+(?:[.,]\d+)?')

# Filas administrativas (transportista, chofer, dirección, giro): no describen
# el producto aunque incluyan la palabra «servicio» (ej. «SERVICIO Y
# TRANSPORTES … LTDA»). Se excluyen de las señales.
_ADMIN_RE = re.compile(
    r'\b(transport\w*|chofer|conductor|patente|comuna|direccion|giro|'
    r'vendedor|telefono|fono|correo|email)\b'
)

# Sufijos morfológicos españoles que se recortan UNA vez (raíz >= 4 letras).
_SUFFIXES = (
    'aciones', 'acion', 'ciones', 'cion', 'amientos', 'amiento',
    'ados', 'adas', 'idos', 'idas', 'ajes', 'aje',
    'ado', 'ada', 'ido', 'ida', 'es', 'os', 'as', 'o', 'a',
)


def strip_accents(value):
    """Devuelve el texto sin marcas diacríticas (NFKD)."""
    if not value:
        return ''
    decomposed = unicodedata.normalize('NFKD', str(value))
    return ''.join(c for c in decomposed if not unicodedata.combining(c))


def normalize(value):
    """Minúsculas, sin acentos y con toda la puntuación convertida en espacio."""
    text = strip_accents(value).casefold()
    text = re.sub(r'[^0-9a-z]+', ' ', text)
    return ' '.join(text.split())


def _stem(word):
    """Raíz morfológica simple: recorta un sufijo una sola vez."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[:-len(suffix)]
    return word


def keyword_variants(keyword):
    """Variantes normalizadas de un keyword (él mismo + su raíz morfológica)."""
    base = normalize(keyword)
    if not base:
        return ()
    words = base.split()
    variants = {base}
    if len(words[-1]) > 3:
        stem = _stem(words[-1])
        if stem != words[-1]:
            variants.add(' '.join(words[:-1] + [stem]))
    return tuple(sorted(variants))


@lru_cache(maxsize=512)
def _variant_pattern(variant):
    """Regex de raíz al inicio de palabra sobre texto ya normalizado."""
    body = r'\s+'.join(re.escape(part) for part in variant.split())
    return re.compile(r'(?<![0-9a-z])' + body)


def _dotted_abbreviations(text):
    """Tokens punteados del texto original (candidatos a abreviatura)."""
    plain = strip_accents(text).casefold()
    return {
        match.group(1)
        for match in re.finditer(r'(?<![0-9a-z])([a-z]{3,})\s*\.', plain)
    }

def match_keywords(text, keywords):
    """Coincidencias de `keywords` en `text` (raíz al inicio de palabra).

    Devuelve una lista de ``{'keyword', 'variant', 'abbreviation'}`` con el
    keyword configurado, la variante que coincidió y si fue por abreviatura
    punteada (token de >= 3 letras que es prefijo de una variante).
    """
    result = []
    normalized = normalize(text)
    if not normalized:
        return result
    abbreviations = _dotted_abbreviations(text)
    for keyword in keywords or ():
        variants = keyword_variants(keyword)
        if not variants:
            continue
        matched = [
            variant for variant in variants
            if _variant_pattern(variant).search(normalized)
        ]
        if matched:
            result.append({
                'keyword': keyword,
                'variant': matched[0],
                'abbreviation': False,
            })
            continue
        abbr = [
            abbreviation
            for abbreviation in abbreviations
            for variant in variants
            if variant.startswith(abbreviation)
        ]
        if abbr:
            result.append({
                'keyword': keyword,
                'variant': sorted(abbr)[0],
                'abbreviation': True,
            })
    return result


def _is_noise(line):
    """True si la línea es ruido institucional/legal (no es señal)."""
    return bool(_NOISE_RE.search(normalize(line)))


def _is_admin(line):
    """True si la línea es administrativa (transportista, dirección, giro)."""
    return bool(_ADMIN_RE.search(normalize(line)))


def _is_product_row(line):
    """Fila de producto: dos o más magnitudes numéricas en la misma línea."""
    return len(_NUMBER_RE.findall(line)) >= 2


def pdf_signals(pdf_text):
    """Extrae título y filas de producto de un texto de PDF.

    Devuelve ``{'title': [...], 'products': [...]}``. Las líneas de ruido
    institucional se descartan antes de clasificar la zona.
    """
    raw_lines = [line.strip() for line in (pdf_text or '').splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines and (pdf_text or '').strip():
        lines = [pdf_text.strip()]
    clean = [
        line for line in lines
        if not _is_noise(line) and not _is_admin(line)
    ]
    title = clean[:TITLE_LINES]
    products = []
    pending = 0
    for line in clean:
        if _PRODUCT_HEADER_RE.search(normalize(line)) and not _NUMBER_RE.search(line):
            pending = 2
            continue
        if _is_product_row(line):
            products.append(line)
            pending = 0
        elif pending:
            products.append(line)
            pending -= 1
        if len(products) >= MAX_PRODUCT_LINES:
            break
    return {'title': title, 'products': products}


def _filename_text(filename):
    """Nombre de archivo como señal: sin extensión y sin separadores."""
    if not filename:
        return ''
    stem = re.sub(r'\.[A-Za-z0-9]{1,5}$', '', str(filename).strip())
    return re.sub(r'[_\-]+', ' ', stem)


def collect_signals(pdf_text=None, filenames=(), excel_product_names=()):
    """Construye el mapa ``source -> texto`` con las señales relevantes."""
    extracted = pdf_signals(pdf_text or '')
    names = [text for text in (_filename_text(f) for f in filenames) if text]
    products = [str(name).strip() for name in excel_product_names or () if name]
    return {
        'filename': ' '.join(names),
        'pdf_title': ' '.join(extracted['title']),
        'pdf_product': ' '.join(extracted['products']),
        'excel_product': ' '.join(products),
    }


def classify(signals, keywords, weak_keywords=(), strong_sources=STRONG_SOURCES):
    """Clasifica a partir de las señales, separando evidencia fuerte y débil.

    - ``keywords``: vocabulario decisivo en cualquier señal (servicio/maquila/
      proceso); una coincidencia fija ``tipo='procesado'``.
    - ``weak_keywords``: vocabulario de artículo (``cepill``, ``cep.``). Sólo es
      decisivo en ``strong_sources`` (nombre de archivo / título del PDF); en
      glosa o nombre de producto del Excel queda como advertencia.

    Devuelve ``{'tipo': 'procesado'|None, 'matches': [...], 'advisory': [...],
    'analyzed': bool, 'sources': [...]}``. ``tipo is None`` significa "sin
    señal decisiva": el llamador conserva el valor por defecto y marca la
    advertencia.
    """
    decisive = []
    advisory = []
    weak_roots = {
        variant
        for keyword in weak_keywords or ()
        for variant in keyword_variants(keyword)
    }
    for source in SOURCE_ORDER:
        text = signals.get(source) or ''
        hits = match_keywords(text, list(keywords or ()) + list(weak_keywords or ()))
        for hit in hits:
            item = {
                'source': source,
                'keyword': hit['keyword'],
                'variant': hit['variant'],
                'abbreviation': hit['abbreviation'],
            }
            is_weak = any(
                hit['variant'].startswith(root) or root.startswith(hit['variant'])
                for root in weak_roots
            )
            if is_weak and source not in strong_sources:
                advisory.append(item)
            else:
                decisive.append(item)
    return {
        'tipo': 'procesado' if decisive else None,
        'matches': decisive,
        'advisory': advisory,
        'analyzed': any((signals.get(source) or '').strip() for source in SOURCE_ORDER),
        'sources': [
            source for source in SOURCE_ORDER
            if (signals.get(source) or '').strip()
        ],
    }


def format_matches(matches):
    """Texto legible de las coincidencias (para la marca de advertencia)."""
    parts = []
    for match in matches or ():
        label = SOURCE_LABELS.get(match['source'], match['source'])
        extra = ' (abreviatura)' if match.get('abbreviation') else ''
        parts.append('«%s» en %s%s' % (match['keyword'], label, extra))
    return '; '.join(parts)


def advisory_message(advisory):
    """Advertencia por evidencia débil de servicio (no cambia el tipo)."""
    if not advisory:
        return ''
    return (
        'Posible servicio (señal de artículo, no de servicio): %s. NO se '
        'cambió el tipo de ingreso; confirme el destino si corresponde.'
        % format_matches(advisory)
    )


def profile_message(detected_code, selected_profile):
    """Advertencia si el perfil no es detectable o no coincide con el elegido."""
    selected = selected_profile or 'sin perfil'
    if not detected_code:
        return (
            'Perfil de lectura no detectable: el documento no expone una '
            'estructura reconocible. Se conserva el perfil elegido (%s).'
            % selected
        )
    allowed = DETECTED_PROFILE_CODES.get(detected_code)
    if allowed is None:
        return (
            'Perfil de lectura detectado no reconocido (%s). Se conserva el '
            'perfil elegido (%s).' % (detected_code, selected)
        )
    if selected_profile not in allowed:
        return (
            'El perfil detectado (%s) no coincide con el elegido (%s). '
            'Verifique la lectura del documento.'
            % (detected_code, selected)
        )
    return ''


def unit_stats(lines):
    """Cuenta dimensiones con unidad ausente y unidades desconocidas."""
    missing = 0
    unknown = set()
    for line in lines or ():
        for dimension in ('thickness', 'width', 'length'):
            raw = line.get('%s_value_raw' % dimension)
            if raw in (None, ''):
                continue
            unit = line.get('%s_unit' % dimension)
            normalized = normalize(unit) if unit else ''
            if not normalized:
                missing += 1
            elif normalized not in KNOWN_UNITS:
                unknown.add(str(unit).strip())
    return {'missing': missing, 'unknown': sorted(unknown)}


def unit_message(stats):
    """Advertencia de unidad no reconocida (nunca bloquea)."""
    if not stats:
        return ''
    missing = stats.get('missing') or 0
    unknown = stats.get('unknown') or []
    if not missing and not unknown:
        return ''
    parts = []
    if unknown:
        parts.append('unidades no reconocidas: %s' % ', '.join(unknown))
    if missing:
        parts.append('%d dimensión(es) sin unidad de origen' % missing)
    return (
        'Unidad no reconocida: %s. Revise las dimensiones; no se bloquea el '
        'ingreso.' % '; '.join(parts)
    )


def no_signal_message(signals, analyzed):
    """Advertencia de ausencia de señal de tipo (se conserva el default)."""
    if not analyzed:
        return (
            'Sin señal de tipo: no hay texto analizable (PDF ausente o '
            'ilegible y sin nombre de archivo útil). Se conserva el tipo por '
            'defecto.'
        )
    labels = ', '.join(
        SOURCE_LABELS.get(source, source)
        for source in SOURCE_ORDER if (signals.get(source) or '').strip()
    )
    return (
        'Sin señal de tipo en las señales revisadas (%s). Se conserva el tipo '
        'por defecto; confirme el destino del ingreso.' % labels
    )


def build_reading_warnings(no_type_signal=None, advisory='', profile='', units=''):
    """Compone el texto de la marca de advertencia (una línea por caso).

    `no_type_signal` acepta el mensaje ya redactado (o True) para no duplicar
    la lógica de señales en el llamador.
    """
    messages = []
    if no_type_signal:
        messages.append(
            no_type_signal if isinstance(no_type_signal, str)
            else 'Sin señal de tipo: se conserva el tipo por defecto.')
    if advisory:
        messages.append(advisory)
    if profile:
        messages.append(profile)
    if units:
        messages.append(units)
    return '\n'.join(message for message in messages if message)

