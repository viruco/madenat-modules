# -*- coding: utf-8 -*-
"""
MODELO PERSISTENTE: FÓRMULAS DE EXPORTACIÓN (H8 — Fase 3)

Parametriza el motor de cálculo de _compute_export_values en lumber_reception.py.
Cada registro define la fórmula matemática aplicable a un perfil de ingesta.

USO:
  desde lumber_reception._compute_export_values():
    formula = self.env['lumber.export.formula']._resolve_for_profile(profile)
    # formula dict con todos los parámetros de cálculo

PRIORIDAD DE RESOLUCIÓN:
  1. Registro activo en lumber.export.formula (Fase 3)
  2. Fallback a constantes de utils_uom (Fase 2/Fase 1)
  3. Hardcode legacy (último recurso)
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LumberExportFormula(models.Model):
    _name = 'lumber.export.formula'
    _description = 'Fórmula de Exportación por Perfil (H8)'
    _order = 'profile, sequence'

    # ── Display name legible para UI ─────────────────────────────────────────
    @api.depends('profile', 'description')
    def _compute_display_name(self):
        """Muestra etiquetas legibles de negocio en vez de 'lumber.export.formula, ID'."""
        for rec in self:
            desc = rec.description or ''
            rec.display_name = f"{rec.profile} — {desc}" if desc else f"{rec.profile}"

    # ── Identidad ──────────────────────────────────────────────────────────
    profile = fields.Selection(
        selection=[
            ('f5085', 'Blanks Clear (Factor 5085 - Pies)'),
            ('f1550', 'S2S / Rough (Factor 1550 - Métrico)'),
            ('metric', 'Madera Bruta (Milimétrico Directo)'),
        ],
        string='Perfil de Ingesta',
        required=True,
        index=True,
        help="Perfil de ingesta al que aplica esta fórmula."
    )
    active = fields.Boolean(
        default=True,
        help="Desactivar para excluir esta fórmula sin borrarla."
    )
    sequence = fields.Integer(
        default=10,
        help="Orden de evaluación cuando hay múltiples fórmulas para el mismo perfil."
    )

    # ── Metadatos de negocio ───────────────────────────────────────────────
    description = fields.Char(
        string='Descripción',
        help="Nombre legible para el usuario funcional (ej: 'Blank Clear 1 9/16 Col A')."
    )
    notes = fields.Text(
        string='Notas de Negocio',
        help="Documentación funcional: cuándo se usa, qué proveedor, qué producto."
    )

    # ── Parámetros de fórmula ─────────────────────────────────────────────
    formula_kind = fields.Selection(
        selection=[
            ('blank_clear', 'Blank Clear — pies, sin recargo S2S'),
            ('s2s_imperial', 'S2S/Rough — metros, con recargo +1/8"'),
            ('metric_direct', 'Métrico directo — mm×mm×m / 1.000.000'),
        ],
        string='Tipo de Fórmula',
        required=True,
        help="Define qué rama matemática se ejecuta en _compute_export_values."
    )
    unit_mode = fields.Selection(
        selection=[
            ('imperial_feet', 'Imperial — largo en PIES'),
            ('imperial_meters', 'Imperial — largo en METROS'),
            ('metric_mm', 'Métrico — dimensiones en MM'),
        ],
        string='Modo de Unidad',
        required=True,
        help="Sistema de unidades que espera la fórmula para el largo."
    )
    principal_factor = fields.Float(
        string='Factor Principal',
        digits=(16, 6),
        required=True,
        default=5085.312,
        help="Factor volumétrico principal. f5085→5085.312, f1550→1550.003, metric→1000000."
    )
    deduction_factor = fields.Float(
        string='Deducción de Cara (pulg)',
        digits=(16, 6),
        default=0.0,
        help="Deducción aplicada al espesor en pulgadas. Blank Clear: 0.0625 (-1/16\"). Otros: 0.0."
    )
    s2s_adjustment_mode = fields.Selection(
        selection=[
            ('none', 'Sin ajuste S2S'),
            ('standard', 'Ajuste estándar +1/8"'),
            ('per_width', 'Ajuste por ancho (consulta exclusiones)'),
        ],
        string='Modo Ajuste S2S',
        required=True,
        default='none',
        help="Cómo se aplica el ajuste S2S al ancho. Blank Clear: none. S2S/Rough: per_width."
    )
    mbf_divisor = fields.Float(
        string='Divisor MBF',
        digits=(16, 3),
        default=12000.0,
        help="Divisor para cálculo de MBF (board feet). Estándar: 12000."
    )
    threshold_note = fields.Char(
        string='Nota de Umbral',
        help="Documentación: condiciones especiales de aplicación (ej: 'solo espesor < 2\"')."
    )

    # ── Constraints ────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'unique_profile_active_formula',
            'UNIQUE(profile, active)',
            'Solo puede haber una fórmula activa por perfil. Desactive la existente antes de crear otra.'
        ),
    ]

    @api.constrains('principal_factor')
    def _check_principal_factor_positive(self):
        for rec in self:
            if rec.principal_factor <= 0:
                raise ValidationError(_("El Factor Principal debe ser mayor que cero."))

    @api.constrains('deduction_factor')
    def _check_deduction_factor_range(self):
        for rec in self:
            if rec.deduction_factor < 0:
                raise ValidationError(_("La Deducción de Cara no puede ser negativa."))
            if rec.deduction_factor > 1.0:
                raise ValidationError(_("La Deducción de Cara no puede superar 1 pulgada."))

    # ── Helper de resolución centralizado ──────────────────────────────
    @api.model
    def _resolve_for_profile(self, profile):
        """
        Retorna un diccionario con los parámetros de fórmula para el perfil dado.

        Prioridad de fuentes:
          1. Registro activo en lumber.export.formula (Fase 3)
          2. Fallback a constantes de utils_uom
          3. Hardcode legacy

        Args:
            profile (str): 'f5085', 'f1550', o 'metric'

        Returns:
            dict: {
                'formula_kind': str,
                'unit_mode': str,
                'principal_factor': float,
                'deduction_factor': float,
                's2s_adjustment_mode': str,
                'mbf_divisor': float,
                'source': str  # trazabilidad de dónde se resolvió
            }
        """
        # Fuente 1: Modelo persistente Fase 3
        record = self.sudo().search([
            ('profile', '=', profile),
            ('active', '=', True),
        ], limit=1, order='sequence')
        if record:
            _logger.debug("ExportFormula: perfil=%s desde modelo Fase3 (id=%s)", profile, record.id)
            return {
                'formula_kind': record.formula_kind,
                'unit_mode': record.unit_mode,
                'principal_factor': record.principal_factor,
                'deduction_factor': record.deduction_factor,
                's2s_adjustment_mode': record.s2s_adjustment_mode,
                'mbf_divisor': record.mbf_divisor,
                'source': 'fase3_model',
            }

        # Fuente 2+3: Fallback a constantes canónicas de utils_uom
        _logger.info("ExportFormula: perfil=%s usando fallback canónico (utils_uom)", profile)
        from . import utils_uom
        fallbacks = {
            'f5085': {
                'formula_kind': 'blank_clear',
                'unit_mode': 'imperial_feet',
                'principal_factor': float(utils_uom.BLANK_CLEAR_FACTOR),
                'deduction_factor': float(utils_uom.FACE_DEDUCTION_INCH),
                's2s_adjustment_mode': 'none',
                'mbf_divisor': float(utils_uom.MBF_DIVISOR),
                'source': 'fallback_utils_uom',
            },
            'f1550': {
                'formula_kind': 's2s_imperial',
                'unit_mode': 'imperial_meters',
                'principal_factor': float(utils_uom.INCH_SQ_METERS_TO_M3),
                'deduction_factor': 0.0,
                's2s_adjustment_mode': 'per_width',
                'mbf_divisor': float(utils_uom.MBF_DIVISOR),
                'source': 'fallback_utils_uom',
            },
            'metric': {
                'formula_kind': 'metric_direct',
                'unit_mode': 'metric_mm',
                'principal_factor': float(utils_uom.M3_DIVISOR),
                'deduction_factor': 0.0,
                's2s_adjustment_mode': 'none',
                'mbf_divisor': float(utils_uom.MBF_DIVISOR),
                'source': 'fallback_utils_uom',
            },
        }
        return fallbacks.get(profile, fallbacks['metric'])