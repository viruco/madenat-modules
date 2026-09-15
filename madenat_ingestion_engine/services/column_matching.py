# -*- coding: utf-8 -*-
"""
Scoring de coincidencia de columnas (patrón P1 de Fase 1B).

Generaliza, como funciones puras sin ORM, el patrón de scoring de alias
validado en `reception_parser.py` (líneas 238-267): una columna real se
compara contra una lista de alias esperados de un campo canónico y se le
asigna un puntaje.

Reglas de puntaje:
  - Coincidencia exacta (normalizada): 100
  - Palabra completa dentro del encabezado: 80
  - Prefijo: 60
  - Subcadena: 40
  - Sin coincidencia: 0

La normalización (minúsculas, sin tildes, sin espacios sobrantes) usa
`unicodedata` de la librería estándar de Python.
"""
import re
import unicodedata


def normalize_text(text):
    """Normaliza un texto para comparación de encabezados.

    - minúsculas
    - sin acentos/tildes (via ``unicodedata`` NFKD + eliminación de marcas
      de combinación)
    - normaliza los ordinales/degree ``º`` y ``°`` a vacío (para que
      ``N°``/``Nº``/``n`` colapsen al mismo token)
    - colapsa espacios múltiples y recorta extremos
    """
    if text is None:
        return ""
    text = str(text)
    text = text.replace("º", "").replace("°", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _alias_match_score(normalized_header, normalized_alias):
    """Compara un alias normalizado contra un encabezado normalizado."""
    if not normalized_alias or not normalized_header:
        return 0
    if normalized_header == normalized_alias:
        return 100
    # palabra completa (límites no alfanuméricos)
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_alias) + r"(?![a-z0-9])"
    if re.search(pattern, normalized_header):
        return 80
    if normalized_header.startswith(normalized_alias):
        return 60
    if normalized_alias in normalized_header:
        return 40
    return 0


def score_column_match(header_text, aliases):
    """Calcula el mejor puntaje de coincidencia entre un encabezado real y
    una lista de alias esperados.

    Retorna el mayor puntaje obtenido por cualquiera de los alias (entero).
    No decide el mapeo final; eso lo hace ``build_column_mapping``.
    """
    normalized_header = normalize_text(header_text)
    best = 0
    for alias in aliases:
        score = _alias_match_score(normalized_header, normalize_text(alias))
        if score > best:
            best = score
    return best


def build_column_mapping(headers, column_aliases, min_score=40):
    """Retorna el mapeo ``{indice_columna: campo_canonico}``.

    Para cada columna real se elige el campo canónico de mayor puntaje
    (si supera ``min_score``). Si varias columnas compiten por el mismo
    campo, se asigna a la de mayor puntaje y las demás quedan sin mapear
    (no se duplica un campo).
    """
    col_best = []
    for idx, header in enumerate(headers):
        best_field = None
        best_score = 0
        for field, aliases in column_aliases.items():
            score = score_column_match(header, aliases)
            if score > best_score:
                best_score = score
                best_field = field
        if best_score >= min_score:
            col_best.append((idx, best_field, best_score))

    col_best.sort(key=lambda item: item[2], reverse=True)
    mapping = {}
    used_fields = set()
    for idx, field, _score in col_best:
        if field in used_fields:
            continue
        mapping[idx] = field
        used_fields.add(field)
    return mapping
