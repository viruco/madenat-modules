# -*- coding: utf-8 -*-
"""
HELPER CENTRALIZADO DE CONFIGURACION DE INGESTA (Fase 2)

AbstractModel que centraliza TODA la lectura de reglas de negocio de ingesta.
Ningun consumidor debe leer directamente los modelos ni ir.config_parameter.

Prioridad de fuentes en cada metodo:
  1. Modelo persistente Fase 2 (registros activos en BD)
  2. ir.config_parameter Fase 1 (JSON, fallback de transicion)
  3. Hardcode legacy (ultimo recurso, solo si todo lo anterior falla)

USO:
  desde cualquier modelo Odoo:
    config = self.env['madenat.ingestion.config']
    nominal_map = config.get_blank_nominal_map(profile)
"""
import json
import logging
from odoo import models, api
_logger = logging.getLogger(__name__)

class MadenatIngestionConfig(models.AbstractModel):
    _name = 'madenat.ingestion.config'
    _description = 'Configuracion Centralizada de Ingesta'

    # =====================================================================
    # 1. MAPA FISICO->NOMINAL BLANKS
    # =====================================================================
    @api.model
    def get_blank_nominal_map(self, profile='f5085'):
        """Retorna lista de tuplas (physical, nominal) para el perfil dado."""
        # Fuente 1: Modelo persistente Fase 2
        records = self.env['lumber.blank.nominal.map'].sudo().search([
            ('profile', '=', profile), ('active', '=', True),
        ], order='sequence, physical_min')
        if records:
            _logger.debug("IngestionConfig: blank_nominal_map desde modelo Fase2 (%d regs, perfil=%s)", len(records), profile)
            result = []
            for rec in records:
                result.append((rec.physical_min, rec.nominal))
                if rec.physical_max != rec.physical_min:
                    result.append((rec.physical_max, rec.nominal))
            return result

        # Fuente 2: ir.config_parameter Fase 1
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.blanks_nominal_map', '')
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], list):
                    _logger.info("IngestionConfig: blank_nominal_map desde Fase1 (ir.config_parameter)")
                    return [(float(p[0]), float(p[1])) for p in parsed]
        except Exception as e:
            _logger.warning("IngestionConfig: fallo Fase1 blank_nominal_map: %s", e)

        # Fuente 3: Hardcode legacy
        _logger.warning("IngestionConfig: usando hardcode legacy blank_nominal_map")
        return [(1.0,1.0),(1.25,1.25),(1.5,1.5),(1.5625,1.5),(2.0,2.0),(2.0625,2.0),(2.5,2.5),(3.0,3.0)]

    # =====================================================================
    # 2. TOLERANCIA NOMINAL
    # =====================================================================
    @api.model
    def get_nominal_tolerance(self):
        """Retorna la tolerancia nominal como float."""
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.nominal_tolerance', '')
            if raw:
                val = float(raw)
                if val > 0:
                    _logger.debug("IngestionConfig: nominal_tolerance=%.4f desde settings", val)
                    return val
        except Exception as e:
            _logger.warning("IngestionConfig: fallo al leer nominal_tolerance: %s", e)
        _logger.warning("IngestionConfig: usando hardcode legacy nominal_tolerance=0.08")
        return 0.08

    # =====================================================================
    # 3. TABLA ROUGH->S2S
    # =====================================================================
    @api.model
    def get_width_s2s_map(self):
        """Retorna dict {rough_mm: (s2s_decimal, s2s_label)}."""
        # Fuente 1: Modelo persistente Fase 2
        records = self.env['lumber.width.s2s.map'].sudo().search([
            ('active', '=', True),
        ], order='sequence, rough_mm')
        if records:
            _logger.debug("IngestionConfig: width_s2s_map desde modelo Fase2 (%d regs)", len(records))
            return {rec.rough_mm: (rec.s2s_decimal, rec.s2s_label) for rec in records}

        # Fuente 2: ir.config_parameter Fase 1
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.width_s2s_map', '')
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and parsed:
                    from fractions import Fraction
                    mapping = {}
                    for k, v in parsed.items():
                        mm = int(k); dec = float(v)
                        if dec >= 160: txt = str(int(round(dec)))
                        else:
                            frac = Fraction(dec).limit_denominator(8)
                            w = frac.numerator // frac.denominator
                            r = frac.numerator % frac.denominator
                            txt = str(w) if r == 0 else f"{w} {r}/{frac.denominator}" if w else f"{r}/{frac.denominator}"
                        mapping[mm] = (dec, txt)
                    if mapping:
                        _logger.info("IngestionConfig: width_s2s_map desde Fase1")
                        return mapping
        except Exception as e:
            _logger.warning("IngestionConfig: fallo Fase1 width_s2s_map: %s", e)

        # Fuente 3: Hardcode legacy
        _logger.warning("IngestionConfig: usando hardcode legacy width_s2s_map")
        return {75:(2.625,"2 5/8"),85:(2.875,"2 7/8"),90:(3.125,"3 1/8"),95:(3.375,"3 3/8"),
                100:(3.625,"3 5/8"),105:(3.875,"3 7/8"),110:(3.875,"3 7/8"),115:(4.375,"4 3/8"),
                120:(4.375,"4 3/8"),125:(4.625,"4 5/8"),130:(4.875,"4 7/8"),140:(4.875,"4 7/8"),
                145:(5.375,"5 3/8"),150:(5.625,"5 5/8"),155:(5.875,"5 7/8")}

    # =====================================================================
    # 4. RANGOS ESPESOR->VISUAL
    # =====================================================================
    @api.model
    def get_thickness_visual_rules(self, profile='f5085'):
        """Retorna lista [[min, max, value, label], ...] para el perfil dado."""
        # Fuente 1: Modelo persistente Fase 2
        records = self.env['lumber.thickness.visual.rule'].sudo().search([
            ('profile', '=', profile), ('active', '=', True),
        ], order='sequence, min_thickness')
        if records:
            _logger.debug("IngestionConfig: thickness_visual_rules desde modelo Fase2 (%d regs)", len(records))
            return [[r.min_thickness, r.max_thickness, r.visual_value, r.visual_label] for r in records]

        # Fuente 2: ir.config_parameter Fase 1
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.thickness_visual_ranges', '')
            if raw:
                parsed = json.loads(raw)
                ranges = parsed.get('ranges', [])
                if ranges:
                    _logger.info("IngestionConfig: thickness_visual_rules desde Fase1")
                    return ranges
        except Exception as e:
            _logger.warning("IngestionConfig: fallo Fase1 thickness_visual_rules: %s", e)

        # Fuente 3: Hardcode legacy
        _logger.warning("IngestionConfig: usando hardcode legacy thickness_visual_rules")
        return [[37,46,1.5,"6/4"],[22,29,1.0,"4/4"],[30,36,1.25,"5/4"],[47,56,2.0,"8/4"]]

    # =====================================================================
    # 5. REGLAS PERFIL<->SUBPRODUCTO
    # =====================================================================
    @api.model
    def get_profile_subproduct_rules(self, profile, rule_type):
        """Retorna lista de keywords para el perfil y tipo de regla dados."""
        # Fuente 1: Modelo persistente Fase 2
        records = self.env['lumber.profile.subproduct.rule'].sudo().search([
            ('profile', '=', profile), ('rule_type', '=', rule_type), ('active', '=', True),
        ])
        if records:
            keywords = [rec.keyword.upper() for rec in records]
            _logger.debug("IngestionConfig: profile_subproduct_rules desde modelo Fase2 (profile=%s, type=%s, %d kw)", profile, rule_type, len(keywords))
            return keywords

        # Fuente 2: ir.config_parameter Fase 1
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.profile_subproduct_filters', '')
            if raw:
                config = json.loads(raw)
                pc = config.get('profiles', {}).get(profile, {})
                key = 'allowed_keywords' if rule_type == 'allowed' else 'forbidden_keywords' if rule_type == 'forbidden' else 'forbidden_in_lock'
                keywords = pc.get(key, [])
                if keywords:
                    _logger.info("IngestionConfig: profile_subproduct_rules desde Fase1")
                    return [kw.upper() for kw in keywords]
        except Exception as e:
            _logger.warning("IngestionConfig: fallo Fase1 profile_subproduct_rules: %s", e)

        # Fuente 3: Hardcode legacy
        _logger.warning("IngestionConfig: usando hardcode legacy profile_subproduct_rules")
        legacy = {
            'f5085': {'allowed':[], 'forbidden':['S2S','RIP'], 'forbidden_in_lock':['S2S','RIP']},
            'f1550': {'allowed':['S2S'], 'forbidden':[], 'forbidden_in_lock':['ROUGH','BLANK']},
            'metric': {'allowed':[], 'forbidden':[], 'forbidden_in_lock':[]},
        }
        return legacy.get(profile, {}).get(rule_type, [])

    # =====================================================================
    # 6. EXCLUSIONES S2S (Fase 3) — cierra brecha de lectura directa
    # =====================================================================
    @api.model
    def get_s2s_exclusion_widths(self):
        """
        Retorna lista de anchos (float, en mm) excluidos del ajuste S2S +1/8".

        Prioridad de fuentes:
          1. ir.config_parameter 'madenat.s2s_exclusion_widths' (Fase 1)
          2. Hardcode legacy: [150, 160, 170, 180, 200]

        Returns:
            list[float]: Lista de anchos en mm excluidos del recargo S2S.
        """
        # Fuente 1: ir.config_parameter (mantiene compatibilidad Fase 1)
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.s2s_exclusion_widths', '')
            if raw:
                exceptions = [float(x.strip()) for x in raw.split(',') if x.strip()]
                if exceptions:
                    _logger.debug("IngestionConfig: s2s_exclusion_widths desde Fase1 (%d anchos)", len(exceptions))
                    return exceptions
        except Exception as e:
            _logger.warning("IngestionConfig: fallo al leer s2s_exclusion_widths: %s", e)

        # Fuente 2: Hardcode legacy
        _logger.warning("IngestionConfig: usando hardcode legacy s2s_exclusion_widths")
        return [150.0, 160.0, 170.0, 180.0, 200.0]
