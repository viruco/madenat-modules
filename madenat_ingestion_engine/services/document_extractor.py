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

from odoo.addons.madenat_lumber_core.models.document_format import (
    detect_document_format,
)


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
# Contrato de `pieces` (piezas declaradas por línea):
#   * entero ≥ 0 → el documento declara esa cantidad de piezas por línea;
#   * None       → el documento NO declara piezas por línea (nunca un marcador
#                  técnico ni un valor inferido): el consumidor persiste 0.
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

# Tolerancia en m3 para descarte de filas de totales de cierre sin etiqueta (Regla V1)
TOTAL_ROW_TOLERANCE_M3 = 0.01


def _is_unlabeled_total_row(line, running_total_m3, tolerance=TOTAL_ROW_TOLERANCE_M3):
    """Detecta si una fila corresponde a un total de cierre sin etiqueta (Regla V1).

    Criterios:
      1. Ningún identificador de paquete, piezas ni dimensiones presentes.
      2. volume_m3 numérico > 0.
      3. running_total_m3 > 0 (acumulador de líneas aceptadas previo).
      4. |volume_m3 - running_total_m3| <= tolerance.
    """
    has_identifier = any(
        line.get(field) not in (None, "")
        for field in (
            "package_no",
            "pieces",
            "thickness_value_raw",
            "width_value_raw",
            "length_value_raw",
            "thickness",
            "width",
            "length",
        )
    )
    if has_identifier:
        return False

    volume_m3 = line.get("volume_m3")
    if not isinstance(volume_m3, (int, float)) or volume_m3 <= 0:
        return False

    if running_total_m3 <= 0:
        return False

    return abs(volume_m3 - running_total_m3) <= tolerance


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
_MONTHS_ES_ABBR = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
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


def parse_localized_decimal(value):
    """Normaliza un número con separadores decimal/miles localizados a float.

    Criterio de separación decimal/miles (documentado y cubierto por tests):
      1. Si hay ambos separadores (',' y '.'), el de más a la derecha es el
         decimal y el otro es separador de miles.
         ("1.234,56" → 1234.56; "1,234.56" → 1234.56)
      2. Si solo hay coma (','), la coma es el decimal (convención
         chilena/latam). ("40,315" → 40.315; "2,92" → 2.92)
      3. Si solo hay punto ('.'), el punto es el decimal (formato estándar).
         ("1234.56" → 1234.56)
      4. Sin separador → entero/float directo.

    Devuelve None si el valor no es interpretable como número.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "").replace("\u00a0", "")
    if not s:
        return None

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def _to_float(value):
    return parse_localized_decimal(value)


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
def _read_xlsx_rows(file_bytes, filename):
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        ws = wb.active
        sheet_name = ws.title
        rows = [list(row) for row in ws.iter_rows(values_only=True)]
        wb.close()
        return sheet_name, rows
    except Exception as e:
        raise DocumentExtractionError(
            f"No se pudo leer el archivo Excel '{filename}': {e}")


def _read_xls_rows(file_bytes, filename):
    try:
        import pandas as pd
        sheets = pd.read_excel(
            io.BytesIO(file_bytes), sheet_name=None, header=None, engine="xlrd")
    except ImportError:
        raise DocumentExtractionError(
            "Dependencia faltante: se requiere 'xlrd' para leer archivos Excel .xls (OLE2)."
        )
    except Exception as e:
        raise DocumentExtractionError(
            f"No se pudo leer el archivo Excel .xls '{filename}': {e}")

    first_sheet_name = next(iter(sheets))
    df = sheets[first_sheet_name]
    rows = [[None if pd.isna(v) else v for v in row] for row in df.values.tolist()]
    return str(first_sheet_name), rows


# Magic bytes para detección de formato Excel por contenido:
# - OOXML: contenedor ZIP, inicia con "PK" (0x50 0x4B)
# - XLS antiguo: OLE2 Compound Document, inicia con D0 CF 11 E0
_OOXML_MAGIC = b"PK"
_XLS_LEGACY_MAGIC = b"\xd0\xcf\x11\xe0"
_INVALID_EXCEL_MSG = (
    "El archivo no parece un Excel válido; ábrelo en Excel y guárdalo como .xlsx"
)


def _read_excel_rows(file_bytes, filename, detected_format=None):
    """Lee filas de Excel eligiendo el lector por los primeros bytes del archivo.

    - OOXML (inicia con b'PK') → openpyxl (_read_xlsx_rows).
    - XLS antiguo (inicia con D0 CF 11 E0) → pandas + xlrd (_read_xls_rows).
    - Otro → DocumentExtractionError con mensaje claro en español.
    """
    if file_bytes and file_bytes.startswith(_OOXML_MAGIC):
        return _read_xlsx_rows(file_bytes, filename)
    if file_bytes and file_bytes.startswith(_XLS_LEGACY_MAGIC):
        return _read_xls_rows(file_bytes, filename)

    raise DocumentExtractionError(_INVALID_EXCEL_MSG)


read_excel_rows = _read_excel_rows


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
    running_total_m3 = 0.0

    for row_idx in range(header_idx + 1, len(rows)):
        row = rows[row_idx]
        source_row_number = row_idx + 1  # 1-based
        if _is_row_empty(row):
            # Fila totalmente vacía = espaciador, no fila de datos: omitir sin
            # advertencia (decisión explícita de P3, distinta de "fila parcial").
            continue

        # Fila de subtotal/total: no es una línea de detalle (en los packing
        # list reales aparece como «TOTAL: 3201 57,8396» al cierre). Se omite
        # con advertencia de auditoría para no duplicar piezas ni volúmenes.
        row_text = normalize_text(" ".join(
            str(cell) for cell in row if cell not in (None, "")))
        if _TOTALS_ROW_RE.match(row_text):
            warnings.append(
                f"Fila {source_row_number}: se omitió una fila de "
                f"totales ({row_text[:60]!r})."
            )
            continue

        line = {key: None for key in _LINE_KEYS}
        for col_idx, field_name in mapping.items():
            raw = row[col_idx] if col_idx < len(row) else None
            line[field_name] = _coerce_value(raw, field_name)

        # Valor de piezas declarado pero NO interpretable (p. ej. «N/A», «s/i»):
        # se conserva el contrato «None = sin cantidad» y se deja constancia en
        # advertencias (patrón P5/P3): nunca se inventa ni se redondea un dato
        # ambiguo.
        pieces_columns = [
            col_idx for col_idx, field_name in mapping.items()
            if field_name == 'pieces']
        if pieces_columns:
            raw_pieces = row[pieces_columns[0]] \
                if pieces_columns[0] < len(row) else None
            if raw_pieces not in (None, '') and line.get('pieces') is None:
                warnings.append(
                    f"Fila {source_row_number}: 'pieces' con valor no "
                    f"numérico ({str(raw_pieces).strip()!r}); no se informa "
                    f"cantidad de piezas."
                )

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

        # Fila de totales de cierre sin etiqueta (Regla V1):
        # Descarte antes del forward-fill para no contaminar forward_fill_state
        # ni emitir aviso de lote heredado.
        if _is_unlabeled_total_row(line, running_total_m3):
            vol_val = line.get("volume_m3")
            v_disp = str(round(float(vol_val), 6)) if isinstance(vol_val, (int, float)) else str(vol_val)
            s_disp = str(round(float(running_total_m3), 6))
            warnings.append(
                f"Fila {source_row_number}: fila de totales sin etiqueta omitida "
                f"(volumen {v_disp} ≈ suma acumulada {s_disp})"
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

        vol = line.get("volume_m3")
        if isinstance(vol, (int, float)) and vol > 0:
            running_total_m3 += vol

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

# ──────────────────────────────────────────────────────────────────────────
# Extracción de partes documentales (emisor/proveedor vs receptor/cliente)
# ──────────────────────────────────────────────────────────────────────────
_RUT_PATTERN = r"R\.?U\.?T\.?\s*[:.]?\s*([\d\.]+-[0-9kK])"

_CUSTOMER_LABEL_RE = (
    r"(?:Se[nñ]or\s*\(\s*es\s*\)|Cliente|Receptor|Destinatario|Comprador|"
    r"Facturar\s+a)\s*[:.]\s*(.+)"
)

_SUPPLIER_LABEL_RE = (
    r"(?:Emisor|Raz[oó]n\s+Social|Vendedor|Proveedor|Remitente|"
    r"Emitido\s+por)\s*[:.]\s*(.+)"
)

# Tokens que delimitan el fin del nombre de una parte en una línea.
_PARTY_NAME_STOP_RE = (
    r"(?:\s|^)(?:Emitido|Vence|Giro|RUT|R\.U\.T|CLI|DOC|TIPO|Pago|"
    r"Direcci[oó]n|Comuna|Ciudad|DESTINO|VOL|TOT|TEL|FAX|PEDIDO|Fecha)"
    r"(?=\s|:|$)"
)

# Etiquetas de campos/partes que indican que una línea NO es una razón social
# limpia (usadas para descartar encabezados y bloques de firma/contacto).
_PARTY_LABEL_RE = (
    r"(?:Nombre|C[oó]digo|SAP|Firma|Cargo|Chofer|Despachador|Fletero|"
    r"Telef?ono|Giro|CASA\s+MATRIZ|SUCURSAL|Direcci[oó]n|Cliente|"
    r"Se[nñ]or\s*(?:\(\s*es\s*\))?|"
    r"Receptor|Destinatario|Comprador|Facturar|Emisor|Vendedor|Proveedor|"
    r"Remitente|Raz[oó]n\s+Social|Transportista|Transporte|GU[IÍ]A|FACTURA|"
    r"BOLETA|NOTA|DESPACHO|ELECTR[OÓ]NICA|S\.I\.I\.|N[°º])\s*[:.]"
)

# Palabras de encabezado documental (no requieren ":"): descartan títulos de
# documento que no son razón social.
_DOC_HEADER_RE = (
    r"(?:GU[IÍ]A|FACTURA|BOLETA|NOTA|DESPACHO|ELECTR[OÓ]NICA|S\.I\.I\.|"
    r"N[°º]\s*\d)"
)


def _clean_party_name(value):
    """Recorta el nombre de una parte en el primer separador contextual."""
    if not value:
        return None
    name = value.strip()
    m = re.search(_PARTY_NAME_STOP_RE, name, re.IGNORECASE)
    if m:
        name = name[:m.start()]
    name = re.sub(r"\s{2,}", " ", name).strip(" :")
    return name or None


def _looks_like_company_name(line):
    """Heurística: la línea es una razón social plausible, no un encabezado."""
    if not line:
        return False
    s = line.strip()
    if not s:
        return False
    if re.search(r"R\.?U\.?T\.?", s, re.IGNORECASE):
        return False
    # Descartar etiquetas de campos/partes y bloques de firma/contacto.
    if re.search(_PARTY_LABEL_RE, s, re.IGNORECASE):
        return False
    # Descartar encabezados documentales (GUÍA, FACTURA, etc.).
    if re.search(_DOC_HEADER_RE, s, re.IGNORECASE):
        return False
    # Descartar líneas con fechas o montos.
    if re.search(r"\d{1,2}\s*[-/]\s*\d{1,2}|\$\s*\d|\d{1,3}(?:\.\d{3}){2,}", s):
        return False
    if not re.search(r"[A-ZÁÉÍÓÚÑ]{2,}", s, re.IGNORECASE):
        return False
    if len(s) > 80:
        return False
    # Sufijo societario → empresa.
    if re.search(
        r"\b(S\.?A\.?|LTDA|LIMITADA|SPA|E\.?I\.?R\.?L\.?|C\.?I\.?A\.?)\b",
        s, re.IGNORECASE,
    ):
        return True
    # Sin sufijo: solo nombres cortos plausibles (Title Case o MAYÚSCULAS).
    words = s.split()
    if not (2 <= len(words) <= 4):
        return False
    return all(
        (w.isupper() or w[0].isupper()) and not w[0].isdigit()
        for w in words if w
    )


def _extract_pdf_parties(text):
    """Extrae emisor/proveedor y receptor/cliente de un PDF de guía.

    Estrategia en capas basada en contexto y relaciones (sin hardcodear RUT,
    nombre, guía ni archivo):

    1. Receptor (customer): etiqueta Señor(es)/Cliente/Receptor/Destinatario/
       Comprador; se asocia el RUT más cercano al bloque.
    2. Emisor (supplier): RUT del membrete superior (no receptor ni
       transportista) y nombre de empresa inmediatamente anterior.

    Devuelve ``supplier_name/supplier_rut/customer_name/customer_rut`` junto
    con ``*_source`` y ``*_confidence`` para auditoría.
    """
    result = {}
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return result

    rut_re = re.compile(_RUT_PATTERN, re.IGNORECASE)
    ruts = []
    for i, ln in enumerate(lines):
        for m in rut_re.finditer(ln):
            ruts.append({"rut": m.group(1).strip(), "line": i})

    # Receptor (customer) por etiqueta.
    customer_name = None
    customer_label_line = None
    for i, ln in enumerate(lines):
        m = re.search(_CUSTOMER_LABEL_RE, ln, re.IGNORECASE)
        if m:
            customer_name = _clean_party_name(m.group(1))
            customer_label_line = i
            break

    # Emisor (supplier) por etiqueta explícita.
    supplier_name_label = None
    supplier_label_line = None
    for i, ln in enumerate(lines):
        m = re.search(_SUPPLIER_LABEL_RE, ln, re.IGNORECASE)
        if m:
            supplier_name_label = _clean_party_name(m.group(1))
            supplier_label_line = i
            break

    # Transportista/carrier RUT (para excluir del emisor).
    carrier_rut = None
    m = re.search(
        r"R\.?U\.?T\.?\s*(?:Trans\.?|Transportista)\s*[:.]?\s*([\d\.]+-[0-9kK])",
        text, re.IGNORECASE,
    )
    if m:
        carrier_rut = m.group(1).strip()

    # RUT más cercano a una etiqueta (asociación contextual por cercanía).
    # Prefiere el RUT en la misma línea o después (patrón "Etiqueta: X / RUT: Y").
    def _rut_near(label_line):
        for r in ruts:
            if r["rut"] == carrier_rut:
                continue
            if label_line is not None and 0 <= (r["line"] - label_line) <= 2:
                return r["rut"]
        for r in ruts:
            if r["rut"] == carrier_rut:
                continue
            if label_line is not None and -2 <= (r["line"] - label_line) < 0:
                return r["rut"]
        return None

    # Emisor RUT: etiqueta explícita, luego membrete, luego fallback.
    supplier_rut = _rut_near(supplier_label_line)
    supplier_rut_line = None
    if supplier_rut is not None:
        supplier_rut_line = next(
            (r["line"] for r in ruts if r["rut"] == supplier_rut), None)

    if supplier_rut is None:
        # Membrete: RUT con nombre de empresa inmediatamente antes.
        for r in ruts:
            if r["rut"] == carrier_rut:
                continue
            if r["line"] > 0 and _looks_like_company_name(lines[r["line"] - 1]):
                supplier_rut = r["rut"]
                supplier_rut_line = r["line"]
                break

    # Receptor RUT: RUT cercano a la etiqueta de cliente, excluyendo emisor y
    # transportista. Preferir el RUT en la misma línea o después (patrón
    # "Cliente: X / R.U.T.: Y"); si no, el RUT inmediatamente antes (patrón
    # "RUT: Y / Señor(es): X").
    customer_rut = None
    if customer_label_line is not None:
        for r in ruts:
            if r["rut"] in (supplier_rut, carrier_rut):
                continue
            if 0 <= (r["line"] - customer_label_line) <= 2:
                customer_rut = r["rut"]
                break
        if customer_rut is None:
            for r in ruts:
                if r["rut"] in (supplier_rut, carrier_rut):
                    continue
                if -2 <= (r["line"] - customer_label_line) < 0:
                    customer_rut = r["rut"]
                    break

    if supplier_rut is None:
        # Fallback: primer RUT que no sea receptor ni transportista.
        for r in ruts:
            if r["rut"] in (customer_rut, carrier_rut):
                continue
            supplier_rut = r["rut"]
            supplier_rut_line = r["line"]
            break

    # Nombre del emisor: etiqueta explícita, luego membrete.
    supplier_name = supplier_name_label
    supplier_source = "label" if supplier_name else None
    if not supplier_name and supplier_rut_line is not None \
            and supplier_rut_line > 0:
        prev = lines[supplier_rut_line - 1]
        if _looks_like_company_name(prev):
            supplier_name = prev
            supplier_source = "letterhead"
    if not supplier_name:
        # Sin RUT emisor: buscar nombre de empresa en el membrete (líneas
        # previas al bloque de cliente).
        limit = (
            customer_label_line
            if customer_label_line is not None else len(lines)
        )
        for i in range(0, limit):
            if _looks_like_company_name(lines[i]):
                supplier_name = lines[i]
                supplier_source = "letterhead"
                break

    if supplier_name and supplier_rut:
        supplier_confidence = "high"
    elif supplier_rut:
        supplier_confidence = "medium"
    elif supplier_name:
        supplier_confidence = "low"
    else:
        supplier_confidence = "none"

    if customer_name and customer_rut:
        customer_confidence = "high"
    elif customer_name or customer_rut:
        customer_confidence = "medium"
    else:
        customer_confidence = "none"

    result["supplier_name"] = supplier_name
    result["supplier_rut"] = supplier_rut
    result["supplier_source"] = supplier_source
    result["supplier_confidence"] = supplier_confidence
    result["customer_name"] = customer_name
    result["customer_rut"] = customer_rut
    result["customer_source"] = "label" if customer_name else None
    result["customer_confidence"] = customer_confidence
    return result



def _extract_pdf_header(text):
    header = {}

    m = _search_first([r"N[°ºo]\s*[:.\-]?\s*(\d{3,})"], text)
    if m:
        header["guide_number"] = m.group(1)

    m = _search_first([r"GU[IÍ]A\s+DE\s+DESPACHO"], text)
    if m:
        header["document_type"] = "Guía de Despacho Electrónica"

    m = _search_first(
        [
            r"(\d{1,2})\s+de\s+(%s)\s+de\s+(\d{4})" % _MONTHS_RE,
            r"(\d{1,2})\s*[-/]\s*([A-Za-z]{3,9})\s*[-/]\s*(\d{4})",
        ],
        text,
    )
    if m:
        day, month, year = m.group(1), m.group(2).lower(), m.group(3)
        month_num = _MONTHS_ES.get(month) or _MONTHS_ES_ABBR.get(month)
        if month_num:
            header["guide_date"] = "%04d-%02d-%02d" % (
                int(year), month_num, int(day)
            )

    # Partes documentales: emisor/proveedor vs receptor/cliente por contexto.
    parties = _extract_pdf_parties(text)
    for key, value in parties.items():
        if not value:
            continue
        # No contaminar el header con "sin detección" (confianza none).
        if key.endswith('_confidence') and value == 'none':
            continue
        header[key] = value

    m = _search_first(
        [
            r"O\s*/\s*C\s*[:.]\s*(\S+)",
            r"Orden\s+de\s+Compra\s*[:.]?\s*(\S+)",
            r"Orden\s*[:.]\s*(\S+)",
            r"Referencia[^\n]*?Nro\.?\s*[:.]?\s*(\S+)",
        ],
        text,
    )
    if m:
        header["oc_reference"] = m.group(1).strip()

    m = _search_first(
        [r"PEDIDO\s*/\s*ORIGEN\s*[:.]\s*(\S+)"], text
    )
    if m:
        header["origin_reference"] = m.group(1).strip()

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

    # Totales documentales: paquetes, piezas y montos (nombres canónicos).
    m = _search_first([r"TOT\s*\.?\s*PAQ\s*\.?\s*:\s*(\d+)"], text)
    if m:
        header["total_packages"] = _to_int(m.group(1))
    m = _search_first([r"TOT\s+PZAS\s*\.?\s*:\s*([\d\.,]+)"], text)
    if m:
        header["total_pieces"] = _to_int(m.group(1))
    m = _search_first([r"Monto\s+Neto\s*\$?\s*([\d\.,]+)"], text)
    if m:
        header["net_amount"] = _to_money_float(m.group(1))
    m = _search_first(
        [r"I\.?V\.?A\.?\s*\(?\s*\d+\s*%?\s*\)?\s*([\d\.,]+)"], text
    )
    if m:
        header["vat_amount"] = _to_money_float(m.group(1))
    m = _search_first([r"Total\s*\$?\s*([\d\.,]+)"], text)
    if m:
        header["total_amount"] = _to_money_float(m.group(1))

    m = _search_first(
        [
            r"Tipo\s+de\s+Cambio[^\n]*?([\d\.,]+)",
            r"TIPO\s+CAMBIO\s*[:.]?\s*([\d\.,]+)",
        ],
        text,
    )
    if m:
        header["exchange_rate"] = _to_money_float(m.group(1))

    volume_patterns = [
        r"TON\s*/\s*M3\s*[:.]?\s*([\d\.,]+)",
        r"VOLUMEN\s*/\s*TON\s*[:.]?\s*([\d\.,]+)",
        r"VOL\s*\.?\s*TOT\s*\.?\s*[:.]?\s*([\d\.,]+)",
        r"TOTAL\s+VOLUMEN\s*[:.]?\s*([\d\.,]+)",
        r"VOLUMEN\s+TOTAL\s*[:.]?\s*([\d\.,]+)",
        r"TOTAL\s*(?:M3|M\u00b3)\s*[:.]?\s*([\d\.,]+)",
        r"(?:M3|M\u00b3)\s+TOTAL\s*[:.]?\s*([\d\.,]+)",
        r"VOLUMEN\s*[:.]?\s*([\d\.,]+)",
        r"([\d]{1,4}(?:[.,]\d+)?)\s*(?:M3|M\u00b3)",
    ]
    m = _search_first(volume_patterns, text)
    if m:
        header["total_volume_m3"] = _to_float(m.group(1))

    m = _search_first([r"Destino\s*[:.]\s*([^\n]+)"], text)
    if m:
        header["destination_label"] = m.group(1).strip()

    return header


# ── Nivel 2 — clustering de palabras (tablas PDF sin bordes) ─────────────
# Tolerancias de agrupación en puntos PDF (1 punto ≈ 1/72 pulgada).
_WORD_CLUSTER_X_TOLERANCE = 8.0   # horizontal: palabras de la misma columna
_WORD_CLUSTER_Y_TOLERANCE = 5.0   # vertical: palabras de la misma fila


def _clean_table_rows(rows):
    """Normaliza celdas de pdfplumber (None → '', strip, sin saltos de línea)."""
    cleaned = []
    for row in rows:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                cleaned_row.append(re.sub(r"\s+", " ", str(cell)).strip())
        cleaned.append(cleaned_row)
    return cleaned


def _extract_pdf_table_bordered(file_bytes, filename):
    """Nivel 1 — tabla con bordes reales vía page.extract_tables().

    Retorna una lista de filas (listas de celdas) de la primera tabla con al
    menos una fila de datos no vacía, o None si no se encontró ninguna tabla
    utilizable. Nunca lanza: ante cualquier error devuelve None.
    """
    import pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    if not table:
                        continue
                    rows = _clean_table_rows(table)
                    if len(rows) >= 2 and any(not _is_row_empty(r) for r in rows[1:]):
                        return rows
    except Exception:
        pass
    return None


def _cluster_words_to_rows(words):
    """Agrupa palabras (dicts con ``x0``/``top``/``text``) en filas y columnas.

    Paso 1: agrupa por fila (``top``, tolerancia ``_WORD_CLUSTER_Y_TOLERANCE``).
    Paso 2: dentro de cada fila, agrupa por columna (``x0``, tolerancia
    ``_WORD_CLUSTER_X_TOLERANCE``).
    """
    if not words:
        return None

    sorted_words = sorted(
        words, key=lambda w: (w.get("top", 0) or 0, w.get("x0", 0) or 0))
    rows_by_y = []
    for word in sorted_words:
        top = word.get("top", 0) or 0
        for row in rows_by_y:
            if abs(row["top"] - top) <= _WORD_CLUSTER_Y_TOLERANCE:
                row["words"].append(word)
                break
        else:
            rows_by_y.append({"top": top, "words": [word]})

    result_rows = []
    for row in rows_by_y:
        cols = []
        for word in sorted(row["words"], key=lambda w: w.get("x0", 0) or 0):
            x0 = word.get("x0", 0) or 0
            for col in cols:
                if abs(col["x0"] - x0) <= _WORD_CLUSTER_X_TOLERANCE:
                    col["text"] = (col["text"] + " " + word.get("text", "")).strip()
                    break
            else:
                cols.append({"x0": x0, "text": word.get("text", "")})
        result_rows.append([col["text"] for col in cols])

    return result_rows


def _extract_pdf_table_word_cluster(file_bytes, filename):
    """Nivel 2 — tabla sin bordes reconstruida por clustering de palabras.

    Retorna una lista de filas (listas de celdas) o None. Nunca lanza.
    """
    import pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                words = page.extract_words() or []
                rows = _cluster_words_to_rows(words)
                if rows and any(not _is_row_empty(r) for r in rows):
                    return rows
    except Exception:
        pass
    return None


def _resolve_pdf_table_strategies(column_profile):
    """Estrategias de extracción de tabla PDF a intentar, en orden.

    - 'lines' → solo Nivel 1 (tabla con bordes).
    - 'word_cluster' → solo Nivel 2 (clustering de palabras).
    - 'none' → saltar directo a Nivel 4.
    - sin clave / autodetección → Nivel 1 y luego Nivel 2.
    """
    if column_profile is not None:
        strategy = column_profile.get("pdf_table_strategy")
        if strategy == "none":
            return []
        if strategy == "lines":
            return ["lines"]
        if strategy == "word_cluster":
            return ["word_cluster"]
        return ["lines", "word_cluster"]
    return ["lines", "word_cluster"]


def _select_pdf_profile_mapping(rows, column_profile):
    """Igual que _select_profile_and_mapping pero sin lanzar: retorna
    (profile, header_idx, mapping) o (None, None, None)."""
    if column_profile is not None:
        header_idx = _find_header_row(rows, column_profile["column_aliases"])
        if header_idx is None:
            return None, None, None
        mapping = build_column_mapping(rows[header_idx], column_profile["column_aliases"])
        return column_profile, header_idx, mapping

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
        return None, None, None
    return best


# ──────────────────────────────────────────────────────────────────────────
# Extracción genérica de tablas PDF por coordenadas de palabras + sinónimos
# ──────────────────────────────────────────────────────────────────────────
_GENERIC_COLUMN_SYNONYMS = {
    "material_code": ["codigo", "cod.", "material", "item", "producto",
                      "entrega", "nave"],
    "description": ["descripcion", "descrip.", "detalle", "producto"],
    "quantity": ["cantidad", "cant.", "cant", "volumen", "vol.", "vol"],
    "uom": ["u/m", "um", "unid.", "unidad"],
    "lot": ["lote", "paquete", "bulto", "tarja"],
    "unit_price": ["precio", "p. unitario", "precio unitario", "unitario"],
    "total": ["total", "importe", "monto"],
    # Dimensiones declaradas por columna (espesor/ancho/largo). Se reconocen para
    # que cada valor caiga en SU banda: sin ellas, una columna intermedia no
    # reconocida (p. ej. «Largo» en el Anexo de Guía) se reparte por cercanía y
    # contamina la banda vecina —incluso la de piezas—. Convención auditada:
    # `madenat_lumber_core/models/excel_table_detection.py:44-46`.
    "thickness": ["espesor", "esp.", "esp"],
    "width": ["ancho", "anc.", "anc"],
    "length": ["largo", "lar.", "lar", "longitud"],
    # Piezas declaradas por línea. SOLO la familia inequívoca «piezas»: en esta
    # ruta los encabezados «Cantidad»/«Cant.» son VOLUMEN (m³) — así ocurre en
    # las guías de despacho reales y en los fixtures de
    # `test_generic_pdf_table.py` (Fixtures A-D) —, por lo que jamás se
    # interpretan como piezas. Convención auditada del packing list MADENAT:
    # `madenat_lumber_core/models/excel_table_detection.py:47`.
    "pieces": ["piezas", "pzas", "piezas paq", "pzas paq",
               "piezas por paquete", "pcs"],
}
_TABLE_END_MARKERS = (
    "observacion", "despachado", "despacho:", "tot.paq", "total pqt",
    "volumen/ton", "peso carga", "reserva", "marca", "documento", "folio",
    "neto", "cert", "subtotal", "iva", "descuento", "pago", "condiciones",
)

# Filas de totales/subtotales: NO son líneas de detalle. En el «ANEXO GUIA DE
# DESPACHO» real aparecen «TOTAL MATERIAL :» entre grupos y «TOTAL :» al
# cierre; leerlas como líneas duplicaría piezas y volúmenes (subtotal + total).
# Solo se omiten cuando la fila EMPIEZA con la etiqueta de totales (evita
# descartar un código de material que contenga la palabra).
_TOTALS_ROW_RE = re.compile(
    r"^(sub)?total(es)?(\s+(material|general|paq\w*|pqt\w*|m3|piezas?|pzas?))?"
    r"\s*:?(\s|$)"
)


def _match_generic_column(header_word):
    """Devuelve el campo semántico de un token de encabezado, o None."""
    norm = normalize_text(header_word)
    if not norm:
        return None
    for field, aliases in _GENERIC_COLUMN_SYNONYMS.items():
        for alias in aliases:
            a = normalize_text(alias)
            if not a:
                continue
            if norm == a or norm.startswith(a) or a in norm:
                return field
    return None


def _cluster_words_by_top(words, tolerance=4.0):
    """Agrupa palabras en filas por coordenada `top` (con tolerancia)."""
    rows = []
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        placed = False
        for r in rows:
            if abs(w["top"] - r[0]["top"]) <= tolerance:
                r.append(w)
                placed = True
                break
        if not placed:
            rows.append([w])
    return rows


def _assign_word_to_band(word, bands):
    """Asigna una palabra a la banda de columna que contiene su centro X."""
    center = (word["x0"] + word["x1"]) / 2.0
    for b in bands:
        if b["x0"] <= center <= b["x1"]:
            return b["field"]
    best_field = None
    best_dist = float("inf")
    for b in bands:
        dist = min(abs(center - b["x0"]), abs(center - b["x1"]))
        if dist < best_dist:
            best_dist = dist
            best_field = b["field"]
    return best_field


def _build_midpoint_bands(matched):
    """Construye bandas de columna usando puntos medios entre cabeceras.

    Cada banda es ``{field, x0, x1}``; la primera se extiende a -inf y la
    última a +inf, de modo que las columnas extremas capturan valores que
    sobresalen del texto de cabecera (p. ej. totales alineados a la derecha).
    """
    centers = [m["center"] for m in matched]
    boundaries = []
    for i in range(len(centers) - 1):
        boundaries.append((centers[i] + centers[i + 1]) / 2.0)
    bands = []
    for i, m in enumerate(matched):
        x0 = boundaries[i - 1] if i > 0 else float("-inf")
        x1 = boundaries[i] if i < len(boundaries) else float("inf")
        bands.append({"field": m["field"], "x0": x0, "x1": x1})
    return bands


def _build_generic_line(row, header_bands, line_no, page_no):
    """Construye una línea estándar a partir de una fila de palabras.

    ``pieces`` (piezas declaradas por línea) sale EXCLUSIVAMENTE de una columna
    explícita de piezas del documento:

    - columna presente y valor numérico ≥ 0 → entero extraído;
    - columna presente y valor no numérico o negativo → ``None`` + advertencia
      de auditoría (nunca se inventa ni se corrige silenciosamente);
    - columna ausente → ``None``.

    ``None`` significa "el documento no declara piezas por línea" y NUNCA un
    marcador técnico: el consumidor debe persistir 0 y no fabricar cantidades.
    """
    columns = {f: [] for f in _GENERIC_COLUMN_SYNONYMS}
    for w in sorted(row, key=lambda x: x["x0"]):
        field = _assign_word_to_band(w, header_bands)
        if field:
            columns[field].append(w["text"])

    def _num(tokens):
        for t in tokens:
            v = parse_localized_decimal(t)
            if v is not None:
                return float(v)
            # Fallback: múltiples puntos como separador de miles (23.805.042).
            s = str(t).strip().replace(" ", "").replace("\u00a0", "")
            if s.count(".") > 1 and "," not in s:
                try:
                    return float(s.replace(".", ""))
                except ValueError:
                    continue
        return None

    def _text(tokens):
        return " ".join(tokens).strip() or None

    material_code = _text(columns["material_code"])
    description = _text(columns["description"])
    lot = _text(columns["lot"])
    uom = _text(columns["uom"])
    volume_m3 = _num(columns["quantity"])
    unit_price = _num(columns["unit_price"])
    line_amount = _num(columns["total"])

    # Dimensiones declaradas por columna (texto crudo, tal como lo declara el
    # documento: nunca se convierten ni se interpretan).
    thickness_raw = _text(columns["thickness"])
    width_raw = _text(columns["width"])
    length_raw = _text(columns["length"])

    warnings = []
    if volume_m3 is None:
        warnings.append("Columna de cantidad sin valor numérico válido.")

    # Piezas declaradas: solo desde la columna explícita de piezas, y solo en
    # filas que además declaran una referencia de línea (lote/paquete) o un
    # volumen. Una fila de cabecera/etiqueta capturada por el clustering
    # (p. ej. «Centro : TD04 Almacén : 0100» en el Anexo real) puede arrastrar
    # números a la banda de piezas y NO es evidencia de piezas: ante la duda no
    # se informa cantidad (el consumidor persistirá 0).
    pieces_raw = _num(columns["pieces"])
    pieces = None
    is_line_row = bool(lot) or volume_m3 is not None
    if columns["pieces"] and is_line_row:
        if pieces_raw is None:
            warnings.append("Columna de piezas sin valor numérico válido.")
        else:
            pieces = int(round(pieces_raw))
            if pieces < 0:
                warnings.append(
                    "Columna de piezas con valor negativo: no se persiste."
                )
                pieces = None

    detected_fields = sum(
        1 for v in (material_code, description, lot, uom, volume_m3,
                    unit_price, line_amount) if v is not None)
    confidence = round(detected_fields / 7.0, 3)

    return {
        "source_line_no": line_no,
        "source_page": page_no,
        "material_code": material_code,
        "description": description,
        "lot_or_package_ref": lot,
        "quantity": None,
        "uom": uom,
        "volume_m3": volume_m3,
        "unit_price": unit_price,
        "line_amount": line_amount,
        "confidence": confidence,
        "warnings": warnings,
        # Claves compatibles con el contrato _LINE_KEYS (consumo interno).
        "product_code": material_code,
        "product_name_original": description,
        "lot_number": lot or "GRANEL",
        # Dimensiones declaradas por columna (texto crudo del documento).
        "thickness_value_raw": thickness_raw,
        "width_value_raw": width_raw,
        "length_value_raw": length_raw,
        # SIN marcador técnico: ver docstring.
        "pieces": pieces,
    }


def _extract_table_from_page_words(words):
    """Detecta cabecera y construye líneas para las palabras de una página."""
    all_rows = _cluster_words_by_top(words)
    header_row = None
    header_bands = []
    for r in all_rows:
        matched = []
        for w in sorted(r, key=lambda x: x["x0"]):
            field = _match_generic_column(w["text"])
            if field:
                matched.append({
                    "field": field,
                    "center": (w["x0"] + w["x1"]) / 2.0,
                })
        if len(matched) >= 2:
            header_row = r
            header_bands = _build_midpoint_bands(matched)
            break
    if header_row is None:
        return None

    header_bottom = max(w["bottom"] for w in header_row)
    data_words = [w for w in words if w["top"] >= header_bottom - 2.0]
    data_rows = _cluster_words_by_top(data_words)

    lines = []
    for row in data_rows:
        if all(not (w["text"] or "").strip() for w in row):
            continue
        row_text = normalize_text(" ".join(w["text"] for w in row))
        # Filas de subtotal/total: no son líneas de detalle (se omiten sin
        # cortar la tabla, porque pueden aparecer entre grupos de materiales).
        if _TOTALS_ROW_RE.match(row_text):
            continue
        if any(marker in row_text for marker in _TABLE_END_MARKERS):
            break
        line = _build_generic_line(row, header_bands, len(lines) + 1, row[0]["page"])
        if line["volume_m3"] is not None or line["description"] or line["material_code"]:
            lines.append(line)
    return lines or None


def _extract_generic_pdf_table(file_bytes, filename):
    """Extrae una tabla PDF genérica a partir de coordenadas de palabras.

    Procesa página por página y devuelve la primera tabla con líneas
    reconocibles (evita duplicar tablas repetidas en páginas de copia).
    """
    import pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
                words = [
                    {
                        "text": w["text"],
                        "x0": w["x0"], "x1": w["x1"],
                        "top": w["top"], "bottom": w["bottom"],
                        "page": page_no,
                    }
                    for w in (page.extract_words() or [])
                ]
                lines = _extract_table_from_page_words(words)
                if lines:
                    return lines
    except Exception:
        return None
    return None


def _resolve_pdf_detail(file_bytes, filename, column_profile, header, text):
    """Cascada de 4 niveles para extraer detalle + total_volume_m3 de un PDF.

    Nivel 1 (tabla con bordes) → Nivel 2 (clustering de palabras) → Nivel 3
    (suma de volúmenes de las líneas, derivado de 1/2) → Nivel 4 (regex de
    cabecera). Se detiene en el primer nivel que produce líneas con volumen.

    Nunca lanza DocumentExtractionError por no encontrar tabla: degrada de
    nivel y deja auditoría explícita en ``warnings`` (P5). Retorna
    (lines, warnings, total_volume_m3, detected_profile_code).
    """
    warnings = []
    lines = []
    profile_code = None

    strategies = _resolve_pdf_table_strategies(column_profile)

    rows = None
    level_used = None
    for strategy in strategies:
        if strategy == "lines":
            candidate = _extract_pdf_table_bordered(file_bytes, filename)
        else:
            candidate = _extract_pdf_table_word_cluster(file_bytes, filename)
        if candidate is not None:
            rows = candidate
            level_used = 1 if strategy == "lines" else 2
            break

    detail_total = None
    if rows is not None:
        profile, header_idx, mapping = _select_pdf_profile_mapping(rows, column_profile)
        if profile is not None:
            profile_code = profile.get("code")
            lines, build_warnings = _build_lines(rows, header_idx, mapping, profile)
            warnings.extend(build_warnings)
            volumes = [l.get("volume_m3") for l in lines if l.get("volume_m3") is not None]
            if volumes:
                detail_total = round(sum(volumes), 3)
                level_label = (
                    "Nivel 1 (tabla con bordes)" if level_used == 1
                    else "Nivel 2 (tabla sin bordes, clustering de palabras)"
                )
                warnings.append(
                    f"'total_volume_m3' resuelto vía {level_label}, {len(lines)} líneas; "
                    f"no se usó fallback."
                )
            else:
                warnings.append(
                    f"Se detectó una tabla PDF ({'Nivel %d' % level_used}) pero sin volúmenes; "
                    f"se usará el regex de cabecera."
                )
        else:
            warnings.append(
                "Se detectó una tabla PDF pero sin cabecera reconocible; "
                "se usará el regex de cabecera."
            )

    # Fallback genérico: si el perfil no produjo líneas con volumen, usar el
    # extractor genérico por coordenadas de palabras + sinónimos de cabecera.
    if detail_total is None:
        generic_lines = _extract_generic_pdf_table(file_bytes, filename)
        if generic_lines:
            lines = generic_lines
            generic_volumes = [
                l.get("volume_m3") for l in lines
                if l.get("volume_m3") is not None
            ]
            if generic_volumes:
                detail_total = round(sum(generic_volumes), 3)
                warnings.append(
                    "'total_volume_m3' resuelto vía extractor genérico de tabla, "
                    f"{len(lines)} líneas."
                )
            else:
                warnings.append(
                    "Extractor genérico detectó una tabla pero sin volúmenes."
                )

    regex_total = header.get("total_volume_m3")

    if detail_total is not None:
        # Priorizar siempre la suma de líneas de detalle sobre el regex.
        if regex_total is not None:
            diff = round(abs(detail_total - regex_total), 3)
            if diff > 0.001:
                warnings.append(
                    f"Discrepancia: suma de líneas = {detail_total} m3 vs. regex de cabecera = "
                    f"{regex_total} m3 (diferencia {diff} m3, tolerancia superada)"
                )
        return lines, warnings, detail_total, profile_code

    if regex_total is not None:
        warnings.append(
            "'total_volume_m3' resuelto vía Nivel 4 (regex de cabecera); "
            "no se detectó tabla de detalle."
        )
        return lines, warnings, regex_total, profile_code

    return lines, warnings, None, profile_code


def _extract_pdf(file_bytes, filename, column_profile):
    text = _extract_pdf_text(file_bytes, filename)
    header = _extract_pdf_header(text)
    warnings = []

    # Fase 2 (Bug #1) — Aditivo: conservar el volumen DECLARADO en la cabecera
    # del documento (regex "TON/M3:", "VOL.TOT.", "TOTAL M3", …) ANTES de que la
    # cascada de detalle sobrescriba `total_volume_m3`. Es la evidencia original
    # que declara el propio PDF. NO altera la clave existente
    # (`total_volume_m3` mantiene intacta la prioridad de la suma de líneas) ni
    # la lógica interna de `_resolve_pdf_detail`.
    # Sin fallback silencioso: la clave se agrega SOLO si la cabecera declara un
    # volumen; si no lo declara, la clave NO existe (equivale a None) y el
    # `header` conserva su contrato previo (dict vacío cuando no hay etiquetas).
    # OJO (homónimo): no confundir con el campo de modelo `declared_volume_m3`
    # («M³ declarado por Operaciones»); aquí es el total declarado en el PDF.
    declared_volume_m3 = header.get("total_volume_m3")
    if declared_volume_m3 is not None:
        header["declared_volume_m3"] = declared_volume_m3

    lines, detail_warnings, total_volume, profile_code = _resolve_pdf_detail(
        file_bytes, filename, column_profile, header, text)
    warnings.extend(detail_warnings)

    if total_volume is not None:
        header["total_volume_m3"] = total_volume

    if not header.get("guide_number"):
        warnings.append(
            "PDF sin folio de guía reconocible: no se pudo extraer 'guide_number'."
        )

    return DocumentExtractionResult(
        header=header,
        lines=lines,
        warnings=warnings,
        detected_profile_code=profile_code,
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

    # El formato binario real decide el parser; el nombre/extensión es solo
    # contexto de diagnóstico (nunca decide PDF vs Excel).
    detected = detect_document_format(file_bytes)

    if detected == "pdf":
        return _extract_pdf(file_bytes, filename, column_profile)

    # Lector de Excel por contenido (detecta OOXML por 'PK', XLS por 'D0 CF 11 E0')
    sheet_name, rows = _read_excel_rows(file_bytes, filename, detected)
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
