# -*- coding: utf-8 -*-
"""
MODELO PERSISTENTE: FORMATOS DE INGESTA/PARSING (H9 — Fase 3)

Parametriza el comportamiento de _process_dataframe en reception_parser.py.
Cada registro define cómo interpretar las columnas y unidades de un Excel
para un perfil de ingesta específico.

USO:
  desde reception_parser._process_dataframe():
    fmt = self.env['lumber.ingestion.format']._resolve_for_profile(formato)
    # fmt dict con mapeos de columna, reglas de conversión y umbrales

PRIORIDAD DE RESOLUCIÓN:
  1. Registro activo en lumber.ingestion.format (Fase 3)
  2. Fallback a hardcode legacy en reception_parser (Fase 1/Fase 2)
"""
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LumberIngestionFormat(models.Model):
    _name = 'lumber.ingestion.format'
    _description = 'Formato de Ingesta/Parsing por Perfil (H9)'
    _order = 'profile, sequence'

    # ── Identidad ──────────────────────────────────────────────────────────
    profile = fields.Selection(
        selection=[
            ('f5085', 'Blanks Clear (Factor 5085 - Pies)'),
            ('f1550', 'S2S / Rough (Factor 1550 - Métrico)'),
            ('blanks', 'Blanks (Legado — métrico/imperial híbrido)'),
            ('metric', 'Madera Bruta (Milimétrico Directo)'),
        ],
        string='Perfil de Ingesta',
        required=True,
        index=True,
        help="Perfil de ingesta al que aplica este formato de parsing."
    )
    active = fields.Boolean(
        default=True,
        help="Desactivar para excluir este formato sin borrarlo."
    )
    sequence = fields.Integer(
        default=10,
        help="Orden de evaluación."
    )

    # ── Metadatos de negocio ───────────────────────────────────────────────
    description = fields.Char(
        string='Descripción',
        help="Nombre legible para el usuario funcional (ej: 'Excel Blanks Clear con pies')."
    )
    source_format = fields.Char(
        string='Formato Fuente',
        default='excel',
        help="Tipo de archivo de origen (excel, csv, etc.)."
    )
    notes = fields.Text(
        string='Notas de Negocio',
        help="Documentación funcional: qué proveedor usa este formato, ejemplos."
    )

    # ── Reglas de interpretación de unidades ───────────────────────────────
    thickness_unit_heuristic = fields.Selection(
        selection=[
            ('auto_lt10_inch', 'Auto: <10 → pulgadas, ≥10 → mm'),
            ('always_mm', 'Siempre milímetros'),
            ('always_inch', 'Siempre pulgadas'),
        ],
        string='Heurística Espesor',
        required=True,
        default='auto_lt10_inch',
        help="Cómo interpretar el valor numérico del espesor en el Excel."
    )
    width_unit_heuristic = fields.Selection(
        selection=[
            ('auto_lt10_inch', 'Auto: <10 → pulgadas, ≥10 → mm'),
            ('always_mm', 'Siempre milímetros'),
            ('always_inch', 'Siempre pulgadas'),
        ],
        string='Heurística Ancho',
        required=True,
        default='auto_lt10_inch',
        help="Cómo interpretar el valor numérico del ancho en el Excel."
    )
    length_unit_heuristic = fields.Selection(
        selection=[
            ('auto_gt10_ft', 'Auto: >10 → pies, ≤10 → metros'),
            ('always_m', 'Siempre metros'),
            ('always_ft', 'Siempre pies'),
        ],
        string='Heurística Largo',
        required=True,
        default='auto_gt10_ft',
        help="Cómo interpretar el valor numérico del largo en el Excel."
    )

    # ── Conversión de unidades ─────────────────────────────────────────────
    conversion_mode = fields.Selection(
        selection=[
            ('inches_to_mm', 'Pulgadas → mm (×25.4)'),
            ('feet_to_m', 'Pies → m (×0.3048)'),
            ('identity', 'Sin conversión (valor directo)'),
        ],
        string='Modo Conversión',
        required=True,
        default='identity',
        help="Conversión a aplicar cuando se detecta unidad imperial."
    )

    # ── Regla de exportación resultante ────────────────────────────────────
    export_rule_outcome = fields.Selection(
        selection=[
            ('f5085', 'Factor 5085 (Blank Clear)'),
            ('f1550', 'Factor 1550 (S2S/Rough)'),
            ('metric', 'Métrico directo'),
        ],
        string='Regla de Exportación',
        required=True,
        help="Regla de cálculo de exportación que se asignará a las líneas parseadas."
    )

    # ── Mapeo de columnas (JSON estructurado) ─────────────────────────────
    column_mapping_json = fields.Text(
        string='Mapeo de Columnas (JSON)',
        default='{}',
        help="Mapeo override de nombres de columna Excel → campos internos. "
             "Formato: {\"thickness_mm\": \"ESPESOR\", \"width_mm\": \"ANCHO\", ...}. "
             "Vacío = usar mapeo estándar del parser."
    )

    # ── Umbrales ──────────────────────────────────────────────────────────
    thickness_threshold = fields.Float(
        string='Umbral Espesor (pulg)',
        default=10.0,
        help="Valor umbral para heurística auto_lt10_inch: < umbral → pulgadas, ≥ umbral → mm."
    )
    length_threshold = fields.Float(
        string='Umbral Largo',
        default=10.0,
        help="Valor umbral para heurística auto_gt10_ft: > umbral → pies, ≤ umbral → metros."
    )

    # ── Constraints ────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'unique_profile_active_format',
            'UNIQUE(profile, active)',
            'Solo puede haber un formato activo por perfil. Desactive el existente antes de crear otro.'
        ),
    ]

    @api.constrains('column_mapping_json')
    def _check_column_mapping_json(self):
        for rec in self:
            if rec.column_mapping_json:
                try:
                    parsed = json.loads(rec.column_mapping_json)
                    if not isinstance(parsed, dict):
                        raise ValidationError(_("El Mapeo de Columnas debe ser un objeto JSON válido (diccionario)."))
                except json.JSONDecodeError:
                    raise ValidationError(_("El Mapeo de Columnas contiene JSON inválido."))

    # ── Helper de resolución centralizado ──────────────────────────────
    @api.model
    def _resolve_for_profile(self, profile):
        """
        Retorna un diccionario con los parámetros de formato para el perfil dado.

        Prioridad de fuentes:
          1. Registro activo en lumber.ingestion.format (Fase 3)
          2. Fallback a hardcode legacy

        Args:
            profile (str): 'f5085', 'f1550', 'blanks', o 'metric'

        Returns:
            dict: {
                'thickness_unit_heuristic': str,
                'width_unit_heuristic': str,
                'length_unit_heuristic': str,
                'conversion_mode': str,
                'export_rule_outcome': str,
                'thickness_threshold': float,
                'length_threshold': float,
                'column_mapping': dict,
                'source': str
            }
        """
        # Fuente 1: Modelo persistente Fase 3
        try:
            record = self.sudo().search([
                ('profile', '=', profile),
                ('active', '=', True),
            ], limit=1, order='sequence')
        except Exception:
            _logger.warning("IngestionFormat: tabla no disponible, usando fallback legacy para perfil=%s", profile)
            record = None
        if record:
            _logger.debug("IngestionFormat: perfil=%s desde modelo Fase3 (id=%s)", profile, record.id)
            col_map = {}
            if record.column_mapping_json:
                try:
                    col_map = json.loads(record.column_mapping_json)
                except Exception:
                    col_map = {}
            return {
                'thickness_unit_heuristic': record.thickness_unit_heuristic,
                'width_unit_heuristic': record.width_unit_heuristic,
                'length_unit_heuristic': record.length_unit_heuristic,
                'conversion_mode': record.conversion_mode,
                'export_rule_outcome': record.export_rule_outcome,
                'thickness_threshold': record.thickness_threshold,
                'length_threshold': record.length_threshold,
                'column_mapping': col_map,
                'source': 'fase3_model',
            }

        # Fuente 2: Hardcode legacy (comportamiento actual exacto)
        _logger.info("IngestionFormat: perfil=%s usando fallback legacy", profile)
        legacy = {
            'f5085': {
                'thickness_unit_heuristic': 'auto_lt10_inch',
                'width_unit_heuristic': 'auto_lt10_inch',
                'length_unit_heuristic': 'auto_gt10_ft',
                'conversion_mode': 'inches_to_mm',
                'export_rule_outcome': 'f5085',
                'thickness_threshold': 10.0,
                'length_threshold': 10.0,
                'column_mapping': {},
                'source': 'fallback_legacy',
            },
            'f1550': {
                'thickness_unit_heuristic': 'always_mm',
                'width_unit_heuristic': 'always_mm',
                'length_unit_heuristic': 'always_m',
                'conversion_mode': 'identity',
                'export_rule_outcome': 'f1550',
                'thickness_threshold': 10.0,
                'length_threshold': 10.0,
                'column_mapping': {},
                'source': 'fallback_legacy',
            },
            'blanks': {
                'thickness_unit_heuristic': 'always_inch',
                'width_unit_heuristic': 'always_inch',
                'length_unit_heuristic': 'always_ft',
                'conversion_mode': 'inches_to_mm',
                'export_rule_outcome': 'f1550',
                'thickness_threshold': 10.0,
                'length_threshold': 10.0,
                'column_mapping': {},
                'source': 'fallback_legacy',
            },
            'metric': {
                'thickness_unit_heuristic': 'always_mm',
                'width_unit_heuristic': 'always_mm',
                'length_unit_heuristic': 'always_m',
                'conversion_mode': 'identity',
                'export_rule_outcome': 'metric',
                'thickness_threshold': 10.0,
                'length_threshold': 10.0,
                'column_mapping': {},
                'source': 'fallback_legacy',
            },
        }
        return legacy.get(profile, legacy['metric'])