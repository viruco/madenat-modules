# -*- coding: utf-8 -*-
"""
Perfiles de ingesta como datos (patrones P2 y P8 de Fase 1B).

Inspirado en `lumber.ingestion.format` (madenat_lumber_core), PERO como
estructuras de datos Python puras, SIN depender del modelo ORM. La
integración con `madenat.ingestion.column.profile` (persistencia en BD)
queda para la Fase 3.

Evidencia de los perfiles: `docs/fase1_contrato_extraccion.md` (secciones
4.2 y 4.5). Ambos perfiles comparten el mismo esqueleto de columnas
(`N° PQTE. / CODIGOS / PRODUCTO / ESPESOR / ANCHO / LARGO / FILAS /
COLUMNAS / PIEZAS / VOLUMEN`); difieren en unidades, formato de código y
columnas de metadatos de transportista.
"""
from .column_matching import build_column_mapping

PACKING_METRICO_ASERRADA = {
    "code": "packing_metrico_aserrada",
    "description": "Madera seca cepillada — sistema métrico (mm / m).",
    "unit_system": "metric",
    "column_aliases": {
        "package_no": ["n°", "nº", "pqte", "paquete", "n° pqte", "nº pqte"],
        "product_code": ["codigos", "codigo", "códigos", "código"],
        "product_name_original": ["producto"],
        "thickness_value_raw": ["espesor mm", "espesor"],
        "width_value_raw": ["ancho mm", "ancho"],
        "length_value_raw": ["largo mm", "largo"],
        "rows": ["filas"],
        "columns": ["columnas"],
        "pieces": ["piezas"],
        "volume_m3": ["volumen m3", "volumen"],
        "lot_number": ["lote", "n° lote", "nº lote"],
    },
    "forward_fill_fields": ["lot_number"],
    "synthesis_rule": {
        "field": "lot_number",
        "template": "LOTE-{product_code}",
    },
    "detection_heuristic": {
        "field": "thickness_value_raw",
        "rule": "typical_range_mm",
        "min": 10,
    },
    "source_units": {
        "thickness_unit": "mm",
        "width_unit": "mm",
        "length_unit": "m",
    },
    # Campos de transportista NO presentes en el formato métrico (Fase 1).
    "header_extra_fields": [],
}

PACKING_IMPERIAL_BLANKS = {
    "code": "packing_imperial_blanks",
    "description": "Blanks Clear — sistema imperial (pulgadas / pies).",
    "unit_system": "imperial",
    "column_aliases": {
        "package_no": ["n°", "nº", "pqte", "paquete", "n° pqte", "nº pqte"],
        "product_code": ["codigos", "codigo", "códigos", "código"],
        "product_name_original": ["producto"],
        "thickness_value_raw": ["espesor mm", "espesor"],
        "width_value_raw": ["ancho mm", "ancho"],
        "length_value_raw": ["largo mm", "largo"],
        "rows": ["filas"],
        "columns": ["columnas"],
        "pieces": ["piezas"],
        "volume_m3": ["volumen m3", "volumen"],
        "lot_number": ["lote", "n° lote", "nº lote"],
    },
    "forward_fill_fields": ["lot_number"],
    "synthesis_rule": {
        "field": "lot_number",
        "template": "LOTE-{product_code}",
    },
    "detection_heuristic": {
        "field": "thickness_value_raw",
        "rule": "typical_range_mm",
        "max": 10,
    },
    "source_units": {
        "thickness_unit": "inch",
        "width_unit": "inch",
        "length_unit": "ft",
    },
    # Fase 1 4.2: columnas extra RUT/FONO/TRANS presentes solo en este perfil.
    "header_extra_fields": ["carrier_rut", "carrier_phone", "carrier_name"],
}

DEFAULT_PROFILES = [PACKING_METRICO_ASERRADA, PACKING_IMPERIAL_BLANKS]

# ──────────────────────────────────────────────────────────────────────────
# Clave opcional ``pdf_table_strategy`` por perfil (AD-68 cascada PDF):
#   - "lines"         → Nivel 1: tabla con bordes vía extract_tables().
#   - "word_cluster"  → Nivel 2: tabla sin bordes por clustering de palabras.
#   - "none"          → saltar directo a Nivel 4 (regex de cabecera).
#   - ausente         → autodetección: Nivel 1 y luego Nivel 2.
# Los perfiles actuales no la fijan (usan autodetección), por lo que la
# cascada itera ambos niveles y elige el primer perfil con cabecera
# reconocible. Los proveedores con layouts fijos pueden declararla para
# saltarse el intento fallido de nivel.
# ──────────────────────────────────────────────────────────────────────────


def _get_numeric(values):
    """Devuelve los valores numéricos de una lista de celdas."""
    nums = []
    for value in values:
        if value is None:
            continue
        try:
            nums.append(float(value))
        except (TypeError, ValueError):
            continue
    return nums


def detect_profile(headers, sample_rows, profiles=None):
    """Aplica la heurística de detección (P8) y retorna el perfil más probable.

    Regla evidenciada (reception_parser.py ``_detect_format``, Fase 1):
    se usa el valor máximo del campo ``thickness_value_raw`` (leído en bruto,
    antes de cualquier interpretación de unidades). Si ``max < 10`` →
    imperial (pulgadas); si ``max >= 10`` → métrico (mm).

    Retorna el dict del perfil, o ``None`` si no hay confianza suficiente.
    """
    if profiles is None:
        profiles = DEFAULT_PROFILES

    for profile in profiles:
        heuristic = profile.get("detection_heuristic") or {}
        field = heuristic.get("field", "thickness_value_raw")
        mapping = build_column_mapping(headers, profile["column_aliases"], min_score=40)
        field_col = next((idx for idx, f in mapping.items() if f == field), None)
        if field_col is None:
            continue

        values = []
        for row in sample_rows:
            if field_col < len(row):
                values.extend(_get_numeric([row[field_col]]))
        if not values:
            continue

        max_val = max(values)
        if "max" in heuristic and max_val < heuristic["max"]:
            return profile
        if "min" in heuristic and max_val >= heuristic["min"]:
            return profile

    return None
