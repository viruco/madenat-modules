# -*- coding: utf-8 -*-
"""
TABLA ROUGH→S2S (Fase 2 — Modelo Persistente)

Define la conversión de ancho rough (mm) a S2S decimal + etiqueta fraccionaria.
Fuente original: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx — 15 entradas activas canónicas.

Prioridad de fuentes (runtime):
  1. Este modelo (registros activos)
  2. ir.config_parameter 'madenat.width_s2s_map' (Fase 1, fallback)
  3. Hardcode legacy en width_mapping.WidthMappingTable.MAPPING

G8 (AD-120):
  - Tracking activado en rough_mm, s2s_decimal, s2s_label, active (trazabilidad chatter).
  - Validación de coherencia s2s_decimal <-> s2s_label: la etiqueta fraccionaria debe
    corresponder al decimal dentro de una tolerancia de 0.0625 (1/16").
  - Editar un registro SOLO afecta calculos NUEVOS; no recalcula registros historicos
    (vol_shipment_m3, vol_purchase_m3 almacenados). R5/D6.
  - Archivar (active=False) en lugar de borrar.
"""

import logging
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Tolerancia de coherencia decimal<->etiqueta: 1/16" = 0.0625
_S2S_LABEL_DECIMAL_TOLERANCE = 0.0625


def _parse_s2s_label(label):
    """Convierte una etiqueta fraccionaria S2S a decimal.

    Acepta formatos:
      '2 5/8'  -> 2.625
      '4 3/8'  -> 4.375
      '5'      -> 5.0
      '5.875'  -> 5.875

    Retorna float o None si no se puede parsear.
    """
    if not label:
        return None
    label = str(label).strip().replace('"', '').replace("'", "")
    # Formato: 'entero fraccion' p.ej. '4 3/8'
    m = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', label)
    if m:
        whole = int(m.group(1))
        num = int(m.group(2))
        den = int(m.group(3))
        if den == 0:
            return None
        return whole + num / den
    # Fraccion pura p.ej. '3/8'
    m = re.fullmatch(r'(\d+)/(\d+)', label)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
        if den == 0:
            return None
        return num / den
    # Entero o decimal p.ej. '5' o '5.875'
    try:
        return float(label)
    except ValueError:
        return None


class LumberWidthS2SMap(models.Model):
    _name = 'lumber.width.s2s.map'
    _description = 'Tabla Rough->S2S'
    _order = 'sequence, rough_mm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        (
            'unique_rough_mm',
            'UNIQUE(rough_mm)',
            'Ya existe una entrada para ese valor de rough_mm.'
        ),
        (
            'check_rough_mm_positive',
            'CHECK(rough_mm > 0)',
            'El rough_mm debe ser mayor a cero.'
        ),
        (
            'check_s2s_decimal_positive',
            'CHECK(s2s_decimal > 0)',
            'El valor S2S decimal debe ser mayor a cero.'
        ),
    ]

    rough_mm = fields.Integer(
        string='Rough (mm)',
        required=True,
        tracking=True,
        help='Ancho bruto en milimetros (rough). Valor entero canonico de compra.'
    )

    s2s_decimal = fields.Float(
        string='S2S (decimal)',
        required=True,
        digits=(16, 4),
        tracking=True,
        help=(
            'Ancho S2S en pulgadas decimales (ej: 2.625 = 2 5/8). '
            'Debe ser coherente con s2s_label dentro de +/-1/16" (0.0625). '
            'G8: cambios quedan registrados en el chatter con usuario y fecha.'
        )
    )

    s2s_label = fields.Char(
        string='S2S (fraccion)',
        required=True,
        tracking=True,
        help=(
            'Etiqueta fraccionaria para UI (ej: "2 5/8", "3 7/8"). '
            'Se valida coherencia con s2s_decimal al guardar. '
            'G8: cambios quedan registrados en el chatter con usuario y fecha.'
        )
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden en vistas y busquedas. Menor numero = primero.'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help=(
            'Desmarque para deshabilitar esta entrada sin eliminarla (archivar). '
            'G8: archivar en lugar de borrar preserva el historial de cambios.'
        )
    )

    # -------------------------------------------------------------------------
    # Validaciones
    # -------------------------------------------------------------------------

    @api.constrains('s2s_decimal', 's2s_label')
    def _check_decimal_label_coherence(self):
        """G8 (AD-120): valida que s2s_label y s2s_decimal sean coherentes.

        Un registro con s2s_label='4 3/8' (= 4.375) y s2s_decimal=4.125 ('4 1/8')
        seria incoherente (caso historico del 115 mm). Esta validacion lo previene.
        Tolerancia: +/-1/16" = 0.0625 pulgadas.
        """
        for rec in self:
            parsed = _parse_s2s_label(rec.s2s_label)
            if parsed is None:
                raise ValidationError(_(
                    "La etiqueta S2S '%(label)s' del registro %(mm)d mm no se puede "
                    "interpretar como fraccion o decimal. "
                    "Use el formato 'X Y/Z' (ej: '4 3/8') o un decimal (ej: '4.375')."
                ) % {'label': rec.s2s_label, 'mm': rec.rough_mm or 0})
            diff = abs(parsed - rec.s2s_decimal)
            if diff > _S2S_LABEL_DECIMAL_TOLERANCE:
                raise ValidationError(_(
                    "Incoherencia entre etiqueta y decimal S2S para %(mm)d mm:\n"
                    "  Etiqueta '%(label)s' = %(parsed).4f\"\n"
                    "  Decimal almacenado  = %(decimal).4f\"\n"
                    "  Diferencia          = %(diff).4f\" (max. permitido: %(tol).4f\" = 1/16\")\n\n"
                    "Corrija la etiqueta o el decimal para que correspondan."
                ) % {
                    'mm': rec.rough_mm or 0,
                    'label': rec.s2s_label,
                    'parsed': parsed,
                    'decimal': rec.s2s_decimal,
                    'diff': diff,
                    'tol': _S2S_LABEL_DECIMAL_TOLERANCE,
                })

    # -------------------------------------------------------------------------
    # Display
    # -------------------------------------------------------------------------

    def name_get(self):
        result = []
        for rec in self:
            name = f'{rec.rough_mm} mm -> {rec.s2s_label}" ({rec.s2s_decimal})'
            result.append((rec.id, name))
        return result

    # -------------------------------------------------------------------------
    # Nota de diseno -- R5/D6 (AD-120)
    # -------------------------------------------------------------------------
    # Editar un registro de esta tabla SOLO afecta calculos de vol_shipment_m3 /
    # vol_purchase_m3 en lineas NUEVAS o en lineas cuyo campo computed se dispare
    # al abrirse y guardarse de nuevo. Los valores ya almacenados en
    # madenat_guia_processing_line y lumber_reception_line son campos stored=True
    # y NO se recalculan automaticamente al guardar un cambio en esta tabla
    # (R5: historico intocable). La guia 26270 es caso de historico intocable (D3).
    #
    # Advertencia operativa: si Operaciones edita un ancho en esta tabla y luego
    # abre y guarda una linea historica con ese rough_mm, Odoo puede forzar un
    # recompute de los campos depends de width_s2s. Operaciones y Auditoria deben
    # conocer este comportamiento (documentado en CANON/17 F7).