# -*- coding: utf-8 -*-
"""
📏 UTILIDADES DE MAPEO Y CONVERSIONES

Contiene tablas de verdad centralizadas para conversiones de unidades.
"""
import json
import logging

_logger = logging.getLogger(__name__)


class WidthMappingTable:
    """Tabla única de mapeo de anchos Rough -> S2S"""

    # Formato: mm -> (decimal_inch, texto_fraccionario)
    MAPPING = {
        75:   (2.625, "2 5/8"),
        85:   (2.875, "2 7/8"),
        90:   (3.125, "3 1/8"),
        95:   (3.375, "3 3/8"),
        100:  (3.625, "3 5/8"),
        105:  (3.875, "3 7/8"),
        110:  (3.875, "3 7/8"),
        115:  (4.375, "4 3/8"),
        120:  (4.375, "4 3/8"),
        125:  (4.625, "4 5/8"),
        130:  (4.875, "4 7/8"),
        140:  (4.875, "4 7/8"),
        145:  (5.375, "5 3/8"),  # Valor Crítico
        150:  (5.625, "5 5/8"),
        155:  (5.875, "5 7/8"),
    }

    @classmethod
    def _get_mapping_from_param(cls, env):
        """
        Fase 2: Lee desde helper centralizado con fallback Fase 1 + legacy.
        Retorna dict {mm_int: (decimal_inch, texto_fraccionario)}.
        """
        if env and 'madenat.ingestion.config' in env:
            return env['madenat.ingestion.config'].get_width_s2s_map()
        return cls.MAPPING

    @classmethod
    def get_value(cls, mm, format_type='text', tolerance=2.5, env=None):
        """
        Busca el valor mapeado por vecino más cercano.

        Args:
            mm: medida en milímetros
            format_type: 'text' ("5 3/8") o 'decimal' (5.375)
            tolerance: tolerancia de búsqueda ±mm
            env: Odoo environment (opcional; si se provee, lee ir.config_parameter)
        """
        if not mm:
            return "" if format_type == 'text' else 0.0

        mapping = cls._get_mapping_from_param(env) if env else cls.MAPPING

        # Búsqueda exacta primero
        if mm in mapping:
            val = mapping[mm]
            return val[1] if format_type == 'text' else val[0]

        # Búsqueda por vecino más cercano
        matches = [(m, v) for m, v in mapping.items() if abs(m - mm) <= tolerance]
        if not matches:
            return None

        closest_mm, closest_val = min(matches, key=lambda x: abs(x[0] - mm))
        return closest_val[1] if format_type == 'text' else closest_val[0]
