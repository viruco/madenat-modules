# -*- coding: utf-8 -*-
"""Resolución del espesor NOMINAL declarado por el documento (S2S).

Módulo PURO (sin dependencias de Odoo), igual que ``intake_classifier``: lo
usa ``madenat.lumber.intake.wizard`` para escribir ``thickness_nominal`` en
las líneas de staging de la ruta Producto.

Regla de negocio (FASE 13/2B, hechos verificados §4 del prompt):
  * el packing trae el espesor FÍSICO del embarque (6/4 = 38,1 mm);
  * la guía declara el NOMINAL de compra ("de 45mm") y su volumen total;
  * la compra se cubica con el nominal: V = t · w · l · pzas / 10⁶.

Fuentes, sin hardcode por proveedor, ancho, largo ni espesor:
  1. glosa del documento: ``de NNmm``;
  2. reconciliación aritmética con el volumen declarado.

Condiciones (si no se cumplen, el llamador NO escribe nada):
  * glosa y aritmética deben coincidir (± ``GLOSA_TOLERANCE_MM``);
  * el nominal nunca es menor que el espesor físico;
  * el volumen declarado debe ser plausible frente al del packing.
"""
import re

# "… Calidad Col A de 45mm" · "MADERA DE 38,1 MM"
GLOSA_RE = re.compile(r'\bde\s+(\d{2,3}(?:[.,]\d+)?)\s*mm\b', re.IGNORECASE)

# Diferencia máxima aceptada entre la glosa y la aritmética del volumen.
GLOSA_TOLERANCE_MM = 2.0
# El volumen de compra debe ser >= al del packing y <= 1,4 veces ese valor
# (el nominal nunca es más delgado que el físico: 45/38,1 = 1,18 en 40030).
VOLUME_RATIO_MIN = 1.0
VOLUME_RATIO_MAX = 1.4


def nominal_from_text(text):
    """Espesor nominal declarado en la glosa ("de 45mm"), o None.

    Devuelve None si no hay declaración o si el documento declara más de un
    valor distinto: en ese caso no hay evidencia única.
    """
    values = {
        round(float(match.group(1).replace(',', '.')), 1)
        for match in GLOSA_RE.finditer(text or '')
    }
    return values.pop() if len(values) == 1 else None


def nominal_from_volume(volume_m3, lines):
    """Espesor implícito en el volumen total declarado, o None.

    ``t = V · 10⁶ / Σ(w · l · pzas)``, con w en mm y l en m. ``lines`` acepta
    registros de staging o diccionarios con ``width``, ``length`` y ``pieces``.
    """
    volume = float(volume_m3 or 0.0)
    if volume <= 0:
        return None
    geometry = 0.0
    counted = 0
    for line in lines or ():
        width = float(_get(line, 'width') or 0.0)
        length = float(_get(line, 'length') or 0.0)
        pieces = float(_get(line, 'pieces') or 0.0)
        if width > 0 and length > 0 and pieces > 0:
            geometry += width * length * pieces
            counted += 1
    if not geometry or not counted:
        return None
    return round(volume * 1000000.0 / geometry, 1)


def resolve_nominal(glosa, aritmetico, physical_max):
    """Decide el nominal aplicable; ``None`` si no hay evidencia coherente.

    ``glosa`` y ``aritmetico`` son opcionales: basta una fuente, pero si vienen
    las dos deben coincidir. ``physical_max`` es el espesor físico mayor del
    documento: el nominal nunca puede ser menor.
    """
    values = [value for value in (glosa, aritmetico) if value]
    if not values:
        return None
    if glosa and aritmetico and abs(glosa - aritmetico) > GLOSA_TOLERANCE_MM:
        return None
    nominal = values[0]
    if physical_max and nominal < physical_max:
        return None
    return nominal


def volume_is_plausible(volume_m3, document_volume_m3):
    """El volumen declarado debe superar al del packing sin dispararse."""
    if not volume_m3 or not document_volume_m3:
        return False
    ratio = float(volume_m3) / float(document_volume_m3)
    return VOLUME_RATIO_MIN <= ratio <= VOLUME_RATIO_MAX


def _get(line, field):
    if isinstance(line, dict):
        return line.get(field)
    return getattr(line, field, None)
