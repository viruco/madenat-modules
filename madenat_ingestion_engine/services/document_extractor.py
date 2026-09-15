# -*- coding: utf-8 -*-
"""
Motor de extracción de documentos de ingreso MADENAT — Fase 2.

LIMITACIÓN CONOCIDA (P10): esta versión procesa únicamente la primera
hoja / hoja activa de cada archivo Excel. El soporte multi-hoja queda
fuera de alcance de esta fase.

Esta función es PURA (P7): no depende de `self.env`, no realiza consultas
ORM, no escribe en base de datos ni en modelos de auditoría. Cualquier
configuración de perfil debe recibirse como parámetro.

Patrones aplicados (tabla Fase 1B): P1 (scoring de columnas), P2 (perfiles
como datos), P3 (nunca descartar filas silenciosamente), P4 (forward-fill
+ síntesis), P5 (auditoría viva en ``warnings``), P6 (errores combinados),
P8 (autodetección de formato), P9 (salida unificada), P10 (una sola hoja),
P11 (pandas/openpyxl/pdfplumber).

Política de fidelidad de datos (alineada con AD-51 punto 4 de
madenat_lumber_core): este motor NUNCA convierte unidades ni resuelve
catálogos de producto. Los valores dimensionales se preservan tal como
fueron declarados por el proveedor (string + unidad de origen del perfil).
El texto de producto/subproducto se preserva como dato de trazabilidad,
sin resolución. La conversión de unidades y la resolución de
product_id/subproducto_id son responsabilidad de una integración futura
con madenat.ingestion.config.get_default_product() y
find_or_create_lumber_subproducto(), ambos ya existentes en
madenat_lumber_core (AD-ING-001, AD-ING-002) y explícitamente fuera de
alcance en este módulo.
"""
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .column_matching import build_column_mapping, normalize_text
from .ingestion_profiles import DEFAULT_PROFILES, detect_profile


class DocumentExtractionError(Exception):
    """Error catastrófico de extracción: archivo ilegible o sin cabecera
    reconocible. No debe usarse para errores de fila individual (esos se
    reportan como advertencias, no como excepción)."""


@dataclass
class DocumentExtractionResult:
    header: dict = field(default_factory=dict)
    lines: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    detected_profile_code: str = None
    sheet_name_used: str = None


# ── Claves canónicas de línea (contrato Fase 2 corregido) ─────────────────
_LINE_KEYS = [
    "package_no", "product_code", "product_name_original",
    "thickness_value_raw", "width_value_raw", "length_value_raw",
    "rows", "columns", "pieces", "volume_m3", "lot_number",
]
_UNIT_KEYS = ["thickness_unit", "width_unit", "length_unit"]
_INT_FIELDS = {"rows", "columns", "pieces"}
_FLOAT_FIELDS = {"volume_m3"}
_RAW_TEXT_FIELDS = {
    "product_name_original", "thickness_value_raw", "width_value_raw",
    "length_value_raw",
}

# ── Metadatos de cabecera de Excel (etiquetas label:value) ────────────────
_CORE_HEADER_LABELS = {
    "cliente": "customer_name",
    "fecha": "guide_date",
    "orden compra": "oc_reference",
    "guia despacho": "guide_number",
    "destino": "destination_label",
    "chofer": "carrier_name",
    "patente": "license_plate",
}
_EXTRA_HEADER_LABELS = {
    "rut": "carrier_rut",
    "fono": "carrier_phone",
    "trans": "carrier_name",
}

# ── Patrones de cabecera de PDF (extracción por regex, Fase 1 §4.5) ───────
_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
    "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9,
    "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_MONTHS_RE = "|".join(_MONTHS_ES.keys())


# ──────────────────────────────────────────────────────────────────────────
# Coerciones de tipo (sin ORM)
# ──────────────────────────────────────────────────────────────────────────
def _to_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _to_raw_text(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        rounded = round(float(value), 6)
        if rounded == int(rounded):
            return str(int(rounded))
        return f"{rounded:g}"
    return str(value).strip()


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(value):
    f = _to_float(value)
    if f is None:
        return None
    return int(round(f))


def _to_money_float(value):
    if value is None:
        return None
    s = str(value).strip().replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
    try:
        return float(s)
    except ValueError:
        return None


def _coerce_value(raw, field_name):
    if raw is None:
        return None
    if field_name in _INT_FIELDS:
        return _to_int(raw)
    if field_name in _FLOAT_FIELDS:
        return _to_float(raw)
    if field_name in _RAW_TEXT_FIELDS:
        return _to_raw_text(raw)
    return _to_text(raw)


def _is_row_empty(row):
    return all(
        cell is None or (isinstance(cell, str) and not cell.strip())
        for cell in row
    )


# Tokens de unidad usados en las "filas fantasma" de etiquetas de unidades
# (ej. la fila "PQTE. | mm. | mm | mm | ... | M3" justo debajo del encabezado).
_UNIT_TOKEN_RE = re.compile(
    r"^(mm|cm|m|in|inch|pulg|ft|pies|mt|mts|m3|m³|m2|m²)\.?$",
    re.IGNORECASE,
)


def _is_unit_label_row(line):
    """Detecta una fila que en realidad es una fila de etiquetas de unidades
    (ej. 'mm.', 'mm', 'M3') y no una línea de datos real.

    Criterio robusto frente a falsos positivos/negativos:
      - NINGUNA columna numérica (espesor/ancho/largo/filas/columnas/piezas/
        volumen) trae un número parseable; y
      - al menos una columna dimensional (espesor/ancho/largo) es un token
        de unidad conocido.

    Una fila de datos real con un solo campo vacío/no numérico NO cumple el
    patrón (el resto de columnas sí traen números), por lo que no se excluye.
    """
    dimensional = (
        line.get("thickness_value_raw"),
        line.get("width_value_raw"),
        line.get("length_value_raw"),
    )
    numeric_candidates = dimensional + (
        line.get("rows"),
        line.get("columns"),
        line.get("pieces"),
        line.get("volume_m3"),
    )
    for value in numeric_candidates:
        if value is not None and _to_float(value) is not None:
            return False
    for value in dimensional:
        if value is not None and _UNIT_TOKEN_RE.match(str(value).strip()):
            return True
    return False

# ──────────────────────────────────────────────────────────────────────────
# Lectura de Excel (primera hoja / hoja activa — P10)
# ──────────────────────────────────────────────────────────────────────────
def _read_excel_rows(file_bytes, filename):
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        ws = wb.active
        sheet_name = ws.title
        rows = [list(row) for row in ws.iter_rows(values_only=True)]
        wb.close()
        return sheet_name, rows
    except Exception as openpyxl_error:
        # Fallback para .xls (OLE2) via pandas/xlrd (P11: pandas ya validado)
        try:
            import pandas as pd
            sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
            first_sheet_name = next(iter(sheets))
            df = sheets[first_sheet_name]
            rows = [[None if pd.isna(v) else v for v in row] for row in df.values.tolist()]
            return str(first_sheet_name), rows
        except Exception:
            raise DocumentExtractionError(
                f"No se pudo leer el archivo Excel '{filename}': {openpyxl_error}"
            )


# ──────────────────────────────────────────────────────────────────────────
# Detección de cabecera y perfil
# ──────────────────────────────────────────────────────────────────────────
def _find_header_row(rows, column_aliases, min_fields=3, min_score=40):
    best_idx = None
    best_count = 0
    for i, row in enumerate(rows[:30]):
        if _is_row_empty(row):
            continue
        mapping = build_column_mapping(row, column_aliases, min_score=min_score)
        count = len(mapping)
        if count > best_count:
            best_count = count
            best_idx = i
    if best_count < min_fields:
        return None
    return best_idx


def _select_profile_and_mapping(rows, column_profile):
    """Retorna (profile, header_row_idx, mapping) o lanza DocumentExtractionError."""
    if column_profile is not None:
        header_idx = _find_header_row(rows, column_profile["column_aliases"])
        if header_idx is None:
            raise DocumentExtractionError(
                "No se detectó una cabecera de columnas reconocible en el archivo."
            )
        mapping = build_column_mapping(rows[header_idx], column_profile["column_aliases"])
        return column_profile, header_idx, mapping

    # Autodetección (P8): probar cada perfil, priorizando la heurística.
    best = None
    for profile in DEFAULT_PROFILES:
        header_idx = _find_header_row(rows, profile["column_aliases"])
        if header_idx is None:
            continue
        mapping = build_column_mapping(rows[header_idx], profile["column_aliases"])
        detected = detect_profile(rows[header_idx], rows[header_idx + 1:header_idx + 8], [profile])
        if detected is not None:
            return profile, header_idx, mapping
        if best is None or len(mapping) > len(best[2]):
            best = (profile, header_idx, mapping)

    if best is None:
        raise DocumentExtractionError(
            "No se detectó una cabecera de columnas reconocible en el archivo."
        )
    return best


# ──────────────────────────────────────────────────────────────────────────
# Forward-fill + síntesis (P4)
# ──────────────────────────────────────────────────────────────────────────
def _synthesize(synthesis_rule, line):
    template = synthesis_rule.get("template", "")
    if not template:
        return ""
    result = template
    for key, value in line.items():
        result = result.replace("{" + key + "}", _to_text(value))
    if re.search(r"\{[a-z_]+\}", result):
        return ""
    return result


def _synthesis_source_fields(synthesis_rule):
    template = synthesis_rule.get("template", "")
    return re.findall(r"\{([a-z_]+)\}", template)


# ──────────────────────────────────────────────────────────────────────────
# Construcción de líneas (P3, P4, P5)
# ──────────────────────────────────────────────────────────────────────────
def _build_lines(rows, header_idx, mapping, profile):
    lines = []
    warnings = []
    forward_fill_state = {}
    forward_fill_fields = profile.get("forward_fill_fields", [])
    synthesis_rule = profile.get("synthesis_rule") or {}

    for row_idx in range(header_idx + 1, len(rows)):
        row = rows[row_idx]
        source_row_number = row_idx + 1  # 1-based
        if _is_row_empty(row):
            # Fila totalmente vacía = espaciador, no fila de datos: omitir sin
            # advertencia (decisión explícita de P3, distinta de "fila parcial").
            continue

        line = {key: None for key in _LINE_KEYS}
        for col_idx, field_name in mapping.items():
            raw = row[col_idx] if col_idx < len(row) else None
            line[field_name] = _coerce_value(raw, field_name)

        # Unidades de origen declaradas por el perfil (no inferidas por celda)
        source_units = profile.get("source_units") or {}
        for key in _UNIT_KEYS:
            line[key] = source_units.get(key)

        if _is_unit_label_row(line):
            tokens = [
                str(line[field]).strip()
                for field in ("thickness_value_raw", "width_value_raw",
                              "length_value_raw")
                if line.get(field) not in (None, "")
            ]
            warnings.append(
                f"Fila {source_row_number}: se omitió una fila de encabezado de "
                f"unidades (valores no numéricos: {', '.join(repr(t) for t in tokens)})."
            )
            continue

        # Forward-fill + síntesis para los campos declarados en el perfil
        for field_name in forward_fill_fields:
            current = line.get(field_name)
            if current in (None, ""):
                if forward_fill_state.get(field_name) not in (None, ""):
                    line[field_name] = forward_fill_state[field_name]
                    warnings.append(
                        f"Fila {source_row_number}: '{field_name}' no informado, "
                        f"heredado (forward-fill) de la fila anterior."
                    )
                elif synthesis_rule.get("field") == field_name:
                    synthesized = _synthesize(synthesis_rule, line)
                    if synthesized:
                        line[field_name] = synthesized
                        source_fields = ", ".join(
                            f"'{f}'" for f in _synthesis_source_fields(synthesis_rule)
                        )
                        warnings.append(
                            f"Fila {source_row_number}: '{field_name}' no informado, "
                            f"sintetizado como '{synthesized}' a partir de {source_fields}."
                        )
                if line.get(field_name) in (None, ""):
                    warnings.append(
                        f"Fila {source_row_number}: '{field_name}' no informado y "
                        f"no pudo heredarse ni sintetizarse."
                    )
            # Actualizar el estado de forward-fill con el valor final resuelto
            # (leído, heredado o sintetizado), para que filas posteriores hereden.
            if line.get(field_name) not in (None, ""):
                forward_fill_state[field_name] = line[field_name]

        line["source_row_number"] = source_row_number
        lines.append(line)

    return lines, warnings

# ──────────────────────────────────────────────────────────────────────────
# Metadatos de cabecera de Excel
# ──────────────────────────────────────────────────────────────────────────
def _find_value_right(row, label_col_idx, max_offset=3):
    for offset in range(1, max_offset + 1):
        idx = label_col_idx + offset
        if idx < len(row) and row[idx] not in (None, ""):
            return row[idx]
    return None


def _excel_serial_to_iso(value):
    try:
        serial = float(value)
        if serial < 1 or serial > 100000:
            return _to_text(value)
        return (datetime(1899, 12, 30) + timedelta(days=serial)).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return _to_text(value)


def _extract_excel_header(rows, header_idx, header_extra_fields):
    header = {}
    extra_fields = set(header_extra_fields or [])
    for row in rows[:header_idx]:
        for col_idx, cell in enumerate(row):
            norm = normalize_text(cell)
            if not norm:
                continue
            field_name = _CORE_HEADER_LABELS.get(norm)
            if field_name is None:
                extra = _EXTRA_HEADER_LABELS.get(norm)
                if extra and extra in extra_fields:
                    field_name = extra
            if field_name and field_name not in header:
                value = _find_value_right(row, col_idx)
                if value is not None:
                    if field_name == "guide_date":
                        value = _excel_serial_to_iso(value)
                    header[field_name] = value
    return header


# ──────────────────────────────────────────────────────────────────────────
# Extracción de PDF (regex, Fase 1 §4.5)
# ──────────────────────────────────────────────────────────────────────────
def _extract_pdf_text(file_bytes, filename):
    import pdfplumber
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except Exception as exc:
        raise DocumentExtractionError(
            f"No se pudo leer el archivo PDF '{filename}': {exc}"
        )


def _search_first(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m
    return None

def _extract_pdf_header(text):
    header = {}

    m = _search_first([r"N[°ºo]\s*[:.\-]?\s*(\d{3,})"], text)
    if m:
        header["guide_number"] = m.group(1)

    m = _search_first(
        [r"(\d{1,2})\s+de\s+(%s)\s+de\s+(\d{4})" % _MONTHS_RE], text
    )
    if m:
        day, month, year = m.group(1), m.group(2).lower(), m.group(3)
        header["guide_date"] = "%04d-%02d-%02d" % (
            int(year), _MONTHS_ES[month], int(day)
        )

    # RUTs: el primero (emisor) y el que sigue a "Señor(es)" (receptor)
    ruts = re.findall(r"R\.?U\.?T\.?\s*[:.]?\s*([\d\.]+-[0-9kK])", text, re.IGNORECASE)
    if ruts:
        header["supplier_rut"] = ruts[0].strip()
    m = re.search(r"Se[nñ]or\(es\)\s*[:.]\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        header["customer_name"] = m.group(1).strip()
    m = re.search(
        r"Se[nñ]or\(es\)[^\n]*?R\.?U\.?T\.?\s*[:.]?\s*([\d\.]+-[0-9kK])",
        text, re.IGNORECASE,
    )
    if m:
        header["customer_rut"] = m.group(1).strip()
    elif len(ruts) >= 2:
        header["customer_rut"] = ruts[1].strip()

    m = _search_first(
        [r"Orden\s*[:.]\s*(\S+)", r"Referencia[^\n]*?Nro\.?\s*[:.]?\s*(\S+)"],
        text,
    )
    if m:
        header["oc_reference"] = m.group(1).strip()

    m = _search_first([r"Transportista\s*[:.]\s*([^\n]+)"], text)
    if m:
        header["carrier_name"] = m.group(1).strip()
    m = _search_first([r"RUT\s+Transportista\s*[:.]\s*([\d\.]+-[0-9kK])"], text)
    if m:
        header["carrier_rut"] = m.group(1).strip()
    m = _search_first([r"Patente\s*[:.]\s*(\S+)"], text)
    if m:
        header["license_plate"] = m.group(1).strip()

    m = _search_first([r"Neto\s*[:.]\s*\$?\s*([\d\.,]+)"], text)
    if m:
        header["net_total"] = _to_money_float(m.group(1))
    m = _search_first([r"I\.?V\.?A\.?\s*\$?\s*([\d\.,]+)"], text)
    if m:
        header["tax_total"] = _to_money_float(m.group(1))
    m = _search_first([r"Total\s*[:.]\s*\$?\s*([\d\.,]+)"], text)
    if m:
        header["total"] = _to_money_float(m.group(1))

    m = _search_first([r"Tipo\s+de\s+Cambio[^\n]*?([\d\.,]+)"], text)
    if m:
        header["exchange_rate"] = _to_money_float(m.group(1))

    m = _search_first([r"(\d{2,4})\s*M3"], text)
    if m:
        header["total_volume_m3"] = _to_float(m.group(1))

    m = _search_first([r"Destino\s*[:.]\s*([^\n]+)"], text)
    if m:
        header["destination_label"] = m.group(1).strip()

    return header


def _extract_pdf(file_bytes, filename, column_profile):
    text = _extract_pdf_text(file_bytes, filename)
    header = _extract_pdf_header(text)
    warnings = []
    if not header.get("guide_number"):
        warnings.append(
            "PDF sin folio de guía reconocible: no se pudo extraer 'guide_number'."
        )
    return DocumentExtractionResult(
        header=header,
        lines=[],
        warnings=warnings,
        detected_profile_code=None,
        sheet_name_used=None,
    )


# ──────────────────────────────────────────────────────────────────────────
# Punto de entrada único
# ──────────────────────────────────────────────────────────────────────────
def extract_document(file_bytes, filename, column_profile=None):
    """Punto de entrada único del motor de extracción.

    Parámetros:
        file_bytes: contenido binario del archivo (Excel o PDF).
        filename: nombre original, usado solo para diagnóstico.
        column_profile: dict de perfil (formato de ingestion_profiles.py)
            ya resuelto externamente, o None para autodetección.

    Retorna DocumentExtractionResult. Lanza DocumentExtractionError solo
    ante error catastrófico (archivo ilegible / sin cabecera reconocible).
    """
    if not file_bytes:
        raise DocumentExtractionError("Archivo vacío: no hay contenido que extraer.")

    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _extract_pdf(file_bytes, filename, column_profile)

    sheet_name, rows = _read_excel_rows(file_bytes, filename)
    if not rows:
        raise DocumentExtractionError(f"El archivo Excel '{filename}' está vacío.")

    profile, header_idx, mapping = _select_profile_and_mapping(rows, column_profile)
    lines, warnings = _build_lines(rows, header_idx, mapping, profile)
    header = _extract_excel_header(rows, header_idx, profile.get("header_extra_fields", []))

    return DocumentExtractionResult(
        header=header,
        lines=lines,
        warnings=warnings,
        detected_profile_code=profile.get("code"),
        sheet_name_used=sheet_name,
    )
