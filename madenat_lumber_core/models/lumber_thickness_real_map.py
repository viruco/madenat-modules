# -*- coding: utf-8 -*-
"""
TABLA DE ESPESORES REALES FÍSICOS (Bloque 5A — AD-126)

Define el mapeo entre el espesor nominal comercial (visual p.ej. '6/4' o decimal en pulgadas)
y el espesor real físico en milímetros (p.ej. 38.1 mm).
Fuente: Especificación Canónica de Operaciones (Cristhian Elgueta — F3 / CANON/17 §9.1).

Características:
  - Modelo persistente con tracking de cambios (mail.thread) y chatter.
  - Validación de coherencia entre espesor nominal en pulgadas y etiqueta visual (tolerancia <= 0.001").
  - Única fuente de verdad en base de datos; sin copias en código ni en parámetros (D6).
  - Editable por Operaciones y Auditoría.
"""

import logging
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Tolerancia de coherencia decimal<->etiqueta: max 0.001" (coherencia exacta, H3)
_THICKNESS_LABEL_DECIMAL_TOLERANCE = 0.001


def _parse_thickness_visual(label):
    """Convierte una etiqueta fraccionaria o cuarto de pulgada a float decimal.

    Acepta formatos:
      '6/4'    -> 1.5
      '4/4'    -> 1.0
      '5/4'    -> 1.25
      '8/4'    -> 2.0
      '1 1/2'  -> 1.5
      '1.5'    -> 1.5

    Retorna float o None si no se puede parsear.
    """
    if not label:
        return None
    label = str(label).strip().replace('"', '').replace("'", "")

    # Formato fraccionario puro p.ej. '6/4' o '3/4'
    m_frac = re.fullmatch(r'(\d+)/(\d+)', label)
    if m_frac:
        num = int(m_frac.group(1))
        den = int(m_frac.group(2))
        if den == 0:
            return None
        return num / den

    # Formato mixto p.ej. '1 1/2'
    m_mixed = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', label)
    if m_mixed:
        whole = int(m_mixed.group(1))
        num = int(m_mixed.group(2))
        den = int(m_mixed.group(3))
        if den == 0:
            return None
        return whole + num / den

    # Entero o decimal p.ej. '1.5' o '2'
    try:
        return float(label)
    except ValueError:
        return None


class LumberThicknessRealMap(models.Model):
    _name = 'lumber.thickness.real.map'
    _description = 'Tabla de Espesores Reales Físicos'
    _order = 'sequence, thickness_nominal_in'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        (
            'unique_thickness_visual',
            'UNIQUE(thickness_visual)',
            'Ya existe una entrada activa con ese espesor nominal visual.'
        ),
        (
            'check_thickness_nominal_in_positive',
            'CHECK(thickness_nominal_in > 0)',
            'El espesor nominal en pulgadas debe ser mayor a cero.'
        ),
        (
            'check_thickness_real_mm_positive',
            'CHECK(thickness_real_mm > 0)',
            'El espesor real en milímetros debe ser mayor a cero.'
        ),
    ]

    name = fields.Char(
        string='Descripción',
        compute='_compute_name',
        store=True,
        help='Identificador descriptivo del mapeo nominal a real.'
    )

    thickness_visual = fields.Char(
        string='Espesor Nominal Visual',
        required=True,
        tracking=True,
        help='Etiqueta visual del espesor (ej: "4/4", "5/4", "6/4", "8/4").'
    )

    thickness_nominal_in = fields.Float(
        string='Espesor Nominal (in)',
        required=True,
        digits=(16, 4),
        tracking=True,
        help='Espesor nominal en pulgadas decimales (ej: 1.5000 para 6/4). Debe ser coherente con la etiqueta visual.'
    )

    thickness_real_mm = fields.Float(
        string='Espesor Real (mm)',
        required=True,
        digits=(16, 3),
        tracking=True,
        help='Espesor físico neto en milímetros para cálculo de volumen real (ej: 38.100 mm para 6/4).'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden en vistas y búsquedas.'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help='Desmarque para archivar la entrada sin eliminar historial.'
    )

    notes = fields.Text(
        string='Notas',
        help='Observaciones técnicas o referencias contractuales.'
    )

    @api.depends('thickness_visual', 'thickness_nominal_in', 'thickness_real_mm')
    def _compute_name(self):
        for rec in self:
            v = rec.thickness_visual or ''
            tin = rec.thickness_nominal_in or 0.0
            tmm = rec.thickness_real_mm or 0.0
            rec.name = f"{v} ({tin:.3f}\" → {tmm:.1f} mm)"

    @api.constrains('thickness_nominal_in', 'thickness_visual')
    def _check_nominal_visual_coherence(self):
        """Valida que thickness_visual y thickness_nominal_in sean matemáticamente coherentes.

        Tolerancia máxima: +/- 0.001 pulgadas.
        """
        for rec in self:
            parsed = _parse_thickness_visual(rec.thickness_visual)
            if parsed is None:
                raise ValidationError(_(
                    "La etiqueta de espesor visual '%(label)s' no se puede interpretar como fracción o decimal. "
                    "Use formatos como '6/4', '5/4' o '1.5'."
                ) % {'label': rec.thickness_visual})

            diff = abs(parsed - rec.thickness_nominal_in)
            if diff > _THICKNESS_LABEL_DECIMAL_TOLERANCE:
                raise ValidationError(_(
                    "Incoherencia en espesor: la etiqueta '%(label)s' equivale a %(parsed).4f\", "
                    "pero el valor nominal ingresado es %(nominal).4f\". "
                    "La diferencia (%(diff).4f\") excede la tolerancia permitida (0.001\")."
                ) % {
                    'label': rec.thickness_visual,
                    'parsed': parsed,
                    'nominal': rec.thickness_nominal_in,
                    'diff': diff,
                })
