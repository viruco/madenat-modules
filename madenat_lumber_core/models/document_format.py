# -*- coding: utf-8 -*-
"""Detección binaria de formato de documento (independiente del nombre/extensión).

Detecta el formato REAL a partir del contenido binario:
  - pdf:         magic bytes "%PDF-" (dentro de los primeros 1024 bytes).
  - xls:         firma OLE2 Compound File (D0 CF 11 E0 A1 B1 1A E1).
  - xlsx:        archivo ZIP con estructura Excel (rutas bajo "xl/").
  - zip_unknown: archivo ZIP que NO es Excel.
  - unknown:     contenido no reconocido o corrupto.

Puro: no depende de `odoo`, no consulta BD ni escribe archivos. No decide rol
documental, modalidad ni clasificación funcional.
"""

import io
import zipfile

_PDF_MAGIC = b"%PDF-"
_PDF_SCAN_WINDOW = 1024
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _is_zip(content):
    """Señal de archivo ZIP (firma PK local/central/eocd)."""
    if len(content) < 4:
        return False
    return content[:2] == b"PK" and content[2:4] in (
        b"\x03\x04", b"\x05\x06", b"\x07\x08")


def _zip_has_excel_structure(content):
    """True si el ZIP contiene estructura de Excel (rutas bajo 'xl/')."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = [n.lower() for n in zf.namelist()]
    except (zipfile.BadZipFile, OSError, ValueError):
        return False
    return any(n.startswith("xl/") for n in names)


def detect_document_format(content):
    """Devuelve 'pdf' | 'xls' | 'xlsx' | 'zip_unknown' | 'unknown'."""
    if not content:
        return "unknown"

    if _PDF_MAGIC in content[:_PDF_SCAN_WINDOW]:
        return "pdf"

    if content[:len(_OLE_MAGIC)] == _OLE_MAGIC:
        return "xls"

    if _is_zip(content):
        if _zip_has_excel_structure(content):
            return "xlsx"
        return "zip_unknown"

    return "unknown"
