# -*- coding: utf-8 -*-
"""Migration 18.0.0.21.0 — vocabulario del clasificador de tipo (Fase 2A).

Contexto
--------
`_classify_normal_document` dejó de comparar subcadenas sobre el texto
completo del PDF: ahora compara por raíz sobre SEÑALES relevantes (nombre de
archivo, título del PDF, glosa de producto y nombre de producto del Excel) y
descarta el texto legal/institucional.

El vocabulario DECISIVO sigue en `madenat.tipo_ingreso_keywords` (propiedad del
núcleo, sin cambios): su lista `procesado` conserva contenido y orden.

«Cepillada» describe el ARTÍCULO —aparece igual en compras de madera S2S— y no
el servicio; tratarla como decisiva desviaba documentos ya registrados. Por eso
el vocabulario de artículo vive en un parámetro NUEVO,
`madenat.tipo_ingreso_weak_keywords`, que sólo es decisivo en las señales donde
el documento declara su naturaleza (nombre de archivo y título).

Garantías
---------
* Nunca pisa valores personalizados: si el parámetro débil ya existe, no se toca.
* El parámetro vigente del núcleo sólo se reescribe cuando su contenido
  normalizado es EXACTAMENTE el seed canónico (misma lista y orden); cualquier
  personalización se registra y se deja intacta.
* Idempotente: ejecutarla dos veces no produce cambios adicionales.
"""
import json
import logging
import unicodedata

_logger = logging.getLogger(__name__)

KEYWORDS_KEY = 'madenat.tipo_ingreso_keywords'
WEAK_KEY = 'madenat.tipo_ingreso_weak_keywords'
WEAK_DEFAULT = ['cepill', 'cep.']

# Seed canónico del núcleo (madenat_lumber_core/data/ir_config_parameter.xml).
SEED = {
    'procesado': ['cepillado', 'servicio', 'proceso', 'maquila'],
    'granel': ['granel', 'volumen total', 'a granel', 'sin desglose'],
}


def _normalized(value):
    """minúsculas + sin acentos + espacios colapsados (una sola palabra)."""
    text = unicodedata.normalize('NFKD', str(value))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(text.casefold().split())


def _normalized_payload(payload):
    """Copia normalizada del payload, conservando claves, listas y orden."""
    if not isinstance(payload, dict):
        return None
    result = {}
    for tipo, values in payload.items():
        if isinstance(values, list):
            result[tipo] = [_normalized(value) for value in values]
        else:
            result[tipo] = values
    return result


def migrate(cr, version):
    # 1. Vocabulario débil: crear sólo si no existe (nunca pisar).
    cr.execute("SELECT 1 FROM ir_config_parameter WHERE key = %s", (WEAK_KEY,))
    if cr.fetchone():
        _logger.info(
            "Migration 18.0.0.21.0: '%s' ya existe; se conserva tal cual.",
            WEAK_KEY)
    else:
        cr.execute(
            "INSERT INTO ir_config_parameter (key, value) VALUES (%s, %s)",
            (WEAK_KEY, json.dumps(WEAK_DEFAULT, ensure_ascii=False)))
        _logger.info(
            "Migration 18.0.0.21.0: creado '%s' = %s (vocabulario de artículo; "
            "decisivo sólo en nombre de archivo/título).",
            WEAK_KEY, WEAK_DEFAULT)

    # 2. Vocabulario vigente del núcleo: normalizar sólo si sigue siendo el seed.
    cr.execute(
        "SELECT id, value FROM ir_config_parameter WHERE key = %s",
        (KEYWORDS_KEY,))
    row = cr.fetchone()
    if not row:
        _logger.info(
            "Migration 18.0.0.21.0: '%s' ausente; el fallback del núcleo "
            "sigue vigente.", KEYWORDS_KEY)
        return

    param_id, raw = row
    try:
        payload = json.loads(raw or '{}')
    except (TypeError, ValueError):
        _logger.warning(
            "Migration 18.0.0.21.0: '%s' no es JSON válido; no se modifica.",
            KEYWORDS_KEY)
        return

    normalized = _normalized_payload(payload)
    if normalized != SEED:
        _logger.info(
            "Migration 18.0.0.21.0: '%s' personalizado; no se modifica.",
            KEYWORDS_KEY)
        return
    if payload == SEED:
        _logger.info(
            "Migration 18.0.0.21.0: '%s' ya es el seed canónico; sin cambios.",
            KEYWORDS_KEY)
        return

    cr.execute(
        "UPDATE ir_config_parameter SET value = %s WHERE id = %s",
        (json.dumps(SEED, ensure_ascii=False), param_id))
    _logger.info(
        "Migration 18.0.0.21.0: '%s' normalizado al seed canónico (misma "
        "lista y orden).", KEYWORDS_KEY)
