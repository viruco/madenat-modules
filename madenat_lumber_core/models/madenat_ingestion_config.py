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
from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError
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
    def get_width_s2s_map(self, raise_if_empty=True):
        """Retorna dict {rough_mm: (s2s_decimal, s2s_label)} desde lumber.width.s2s.map.

        Única fuente de verdad: lumber.width.s2s.map.
        Si no hay registros activos y raise_if_empty=True (default), lanza UserError.
        Con raise_if_empty=False retorna dict vacío (para comprobaciones no bloqueantes).

        G5 (AD-120): El UserError solo se propaga cuando el perfil depende de la tabla
        S2S (perfiles imperiales f1550/f5085 con ancho < direct_width_min_mm).
        Los perfiles métricos y anchos directos llaman con raise_if_empty=False.
        """
        records = self.env['lumber.width.s2s.map'].sudo().search([
            ('active', '=', True),
        ], order='sequence, rough_mm')
        if not records:
            _logger.error(
                "IngestionConfig: tabla S2S vacia o sin registros activos. "
                "El modelo lumber.width.s2s.map no contiene anchos activos."
            )
            if raise_if_empty:
                raise UserError(
                    _("No existen registros activos en la tabla de mapeo S2S (lumber.width.s2s.map). "
                      "Configure y active los anchos S2S antes de procesar maderas S2S.")
                )
            return {}
        _logger.debug("IngestionConfig: width_s2s_map desde modelo lumber.width.s2s.map (%d regs)", len(records))
        return {rec.rough_mm: (rec.s2s_decimal, rec.s2s_label) for rec in records}

    @api.model
    def get_thickness_real_mm(self, thickness_visual=None, thickness_inches=None, raise_if_empty=False):
        """Retorna espesor real físico en mm desde lumber.thickness.real.map (Bloque 5A / AD-126).

        Única fuente de verdad: lumber.thickness.real.map.
        Sin copias en código ni en parámetros (D6 / AD-126).
        Busca primero por thickness_visual (ej: '6/4', '5/4'). Si no encuentra y se provee
        thickness_inches, busca por coincidencia numérica con thickness_nominal_in.
        Retorna float (mm) o None si no encuentra coincidencia.
        """
        if not thickness_visual and not thickness_inches:
            return None

        RealMap = self.env['lumber.thickness.real.map'].sudo()
        if thickness_visual:
            clean_vis = str(thickness_visual).strip()
            rec = RealMap.search([
                ('active', '=', True),
                ('thickness_visual', '=', clean_vis)
            ], limit=1)
            if rec:
                return rec.thickness_real_mm

        if thickness_inches and float(thickness_inches) > 0:
            recs = RealMap.search([('active', '=', True)])
            for rec in recs:
                if abs(rec.thickness_nominal_in - float(thickness_inches)) <= 0.001:
                    return rec.thickness_real_mm

        _logger.debug("IngestionConfig: espesor real no encontrado en lumber.thickness.real.map para visual='%s', in=%s",
                      thickness_visual, thickness_inches)
        if raise_if_empty:
            raise UserError(_("No se encontró el espesor real en lumber.thickness.real.map para '%s'.") % (thickness_visual or thickness_inches))
        return None

    @api.model
    def get_s2s_overwidth_inches(self):
        """Retorna sobreancho S2S en pulgadas (parámetro madenat.s2s_overwidth_inches, default 0.125)."""
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.s2s_overwidth_inches', '0.125')
            if raw:
                return float(raw.strip())
        except Exception as e:
            _logger.warning("IngestionConfig: error al leer madenat.s2s_overwidth_inches: %s", e)
        return 0.125

    @api.model
    def get_out_of_table_behavior(self):
        """Retorna comportamiento para anchos fuera de tabla S2S (default 'warning')."""
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            val = param_obj.get_param('madenat.out_of_table_behavior', 'warning')
            if val in ('direct', 'warning', 'block'):
                return val
        except Exception as e:
            _logger.warning("IngestionConfig: error al leer madenat.out_of_table_behavior: %s", e)
        return 'warning'

    @api.model
    def get_direct_width_min_mm(self):
        """Retorna el umbral mínimo en mm para conversión directa sin advertencia (default 170.0)."""
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.direct_width_min_mm', '170.0')
            if raw:
                return float(str(raw).strip())
        except Exception as e:
            _logger.warning("IngestionConfig: error al leer madenat.direct_width_min_mm: %s", e)
        return 170.0

    @api.model
    def resolve_export_width(self, rough_mm, record=None, is_s2s_inches=False):
        """Resuelve el ancho de exportación en pulgadas de forma guiada por datos (AD-116/AD-117/AD-118/AD-120).

        Orden canónico de resolución del ancho (G5 AD-120 — tabla S2S acotada a perfiles imperiales):
        3. Documental en pulgadas S2S: is_s2s_inches=True → (rough_mm / 25.4) + overwidth (no usa tabla).
        4a. Ancho directo anticipado: rough_mm >= direct_width_min_mm → conversión directa (no usa tabla).
        2. Tabla S2S activa: solo si rough_mm < direct_width_min_mm → s2s_decimal + overwidth.
           Si la tabla está vacía, lanza UserError (solo alcanzable desde perfil imperial).
        4b. Fuera de tabla con política: 'block' → ValidationError; 'warning'/'direct' → mm/25.4.
        """
        if not rough_mm or rough_mm <= 0:
            return 0.0

        overwidth = self.get_s2s_overwidth_inches()
        from .utils_uom import MM_PER_INCH

        # Rama 3: Documental en pulgadas S2S (señal explícita del normalizador de documentos).
        # G5: no depende de la tabla S2S → nunca dispara UserError de tabla vacía.
        signal_s2s = is_s2s_inches or (record and getattr(record, 'is_s2s_inches', False))
        if signal_s2s:
            return (float(rough_mm) / float(MM_PER_INCH)) + overwidth

        # Rama 4a anticipada: ancho >= umbral directo → conversión directa sin tabla S2S.
        # G5: anchos >= 170 mm y perfiles métricos no dependen de la tabla → sin UserError.
        min_direct = self.get_direct_width_min_mm()
        if rough_mm >= min_direct:
            _logger.debug(
                "resolve_export_width: %.1f mm >= umbral directo %.1f mm → conversión directa (sin tabla S2S).",
                rough_mm, min_direct,
            )
            return float(rough_mm) / float(MM_PER_INCH)

        # Rama 2: Tabla S2S activa — solo alcanzada por perfiles imperiales (f1550/f5085)
        # con ancho < min_direct. raise_if_empty=True: tabla vacía dispara UserError.
        # G5: perfiles métricos y anchos >= min_direct NUNCA llegan aquí.
        mapping = self.get_width_s2s_map(raise_if_empty=True)
        rough_key = int(round(rough_mm))
        if rough_key in mapping:
            s2s_decimal = mapping[rough_key][0]
            return s2s_decimal + overwidth

        # Rama 4b: ancho no encontrado en tabla y < min_direct.
        behavior = self.get_out_of_table_behavior()

        if behavior == 'block':
            raise ValidationError(
                _("Ancho rough %.1f mm fuera de tabla S2S (menor al umbral directo %.1f mm configurado como 'block').")
                % (rough_mm, min_direct)
            )
        elif behavior == 'warning':
            _logger.warning(
                "Ancho rough %.1f mm fuera de tabla S2S (menor al umbral directo %.1f mm). Se aplica conversión directa mm/25.4.",
                rough_mm, min_direct
            )
            if record:
                target = getattr(record, 'processing_id', record)
                if hasattr(target, 'message_post') and hasattr(target, 'id') and target.id:
                    try:
                        if not self.env.is_computing():
                            target.message_post(
                                body=_(
                                    "⚠️ <b>Advertencia Ancho S2S</b>: El ancho rough %.1f mm en línea/lote <i>%s</i> "
                                    "está ausente de la tabla S2S (menor al umbral directo %.1f mm). "
                                    "Se aplica conversión directa milimétrica."
                                ) % (rough_mm, getattr(record, 'lot_name', None) or f"ID {record.id}", min_direct)
                            )
                    except Exception:
                        pass

        return float(rough_mm) / float(MM_PER_INCH)

    @api.model
    def get_drying_temp_range(self):
        """Retorna tupla (min_c, max_c) para temperatura de secado en horno (default 50.0, 90.0)."""
        param_obj = self.env['ir.config_parameter'].sudo()
        try:
            min_c = float(param_obj.get_param('madenat.drying_temp_min_c', '50.0'))
            max_c = float(param_obj.get_param('madenat.drying_temp_max_c', '90.0'))
            return (min_c, max_c)
        except Exception as e:
            _logger.warning("IngestionConfig: error al leer rangos de temp de secado: %s", e)
            return (50.0, 90.0)

    @api.model
    def get_drying_duration_range(self):
        """Retorna tupla (min_h, max_h) para duración de secado en horno (default 50.0, 80.0)."""
        param_obj = self.env['ir.config_parameter'].sudo()
        try:
            min_h = float(param_obj.get_param('madenat.drying_duration_min_hours', '50.0'))
            max_h = float(param_obj.get_param('madenat.drying_duration_max_hours', '80.0'))
            return (min_h, max_h)
        except Exception as e:
            _logger.warning("IngestionConfig: error al leer rangos de duración de secado: %s", e)
            return (50.0, 80.0)

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
            # FIX 2 (auditoría 2026-08-20): 'blanks' ya no cae a lista vacía en
            # silencio. Se comporta como perfil legado sin filtros explícitos
            # (misma semántica que 'metric') hasta que se parametrice un registro
            # Fase 2/3 real con reglas para este perfil.
            'blanks': {'allowed':[], 'forbidden':[], 'forbidden_in_lock':[]},
            'metric': {'allowed':[], 'forbidden':[], 'forbidden_in_lock':[]},
        }
        return legacy.get(profile, {}).get(rule_type, [])

    # =====================================================================
    # 6. PRODUCTO MAESTRO POR TIPO DE INGRESO (Fase 1)
    # =====================================================================
    @api.model
    def get_default_product(self, tipo_ingreso, profile=None):
        """Resuelve el producto maestro configurado para un tipo de ingreso.

        Prioridad de búsqueda (de mayor a menor):
          1. coincidencia exacta tipo + perfil, de la compañía activa;
          2. coincidencia exacta tipo + perfil, global (sin compañía);
          3. fallback solo por tipo (perfil vacío), de la compañía activa;
          4. fallback solo por tipo (perfil vacío), global (sin compañía).

        Devuelve un recordset `product.product` único. Si no hay regla activa,
        lanza `UserError` accionable y nunca crea un producto dinámico.
        """
        Rule = self.env['madenat.lumber.product.default']
        company_id = self.env.company.id if self.env.company else False

        def _find(prof, comp):
            domain = [
                ('tipo_ingreso', '=', tipo_ingreso),
                ('ingestion_profile', '=', prof or False),
                ('company_id', '=', comp),
                ('active', '=', True),
            ]
            return Rule.sudo().search(domain, order='sequence, id', limit=1)

        rule = False
        if profile:
            rule = _find(profile, company_id) or _find(profile, False)
        if not rule:
            rule = _find(False, company_id) or _find(False, False)

        if not rule:
            tipo_label = dict(Rule._fields['tipo_ingreso'].selection).get(
                tipo_ingreso, tipo_ingreso)
            raise UserError(_(
                "No hay un Producto Maestro configurado para el tipo de "
                "ingreso '%(tipo)s'.\n\n"
                "Operaciones debe completar la configuración en "
                "MADENAT Lumber → Configuración Ingesta → Productos Maestros "
                "por Tipo y activar una regla para '%(tipo)s'.\n\n"
                "No se creó ningún producto automáticamente."
            ) % {'tipo': tipo_label})

        return rule.product_id

    # =====================================================================
    # 8. KEYWORDS DE CLASIFICACIÓN DE TIPO DE INGRESO (AD-68)
    # =====================================================================
    @api.model
    def get_tipo_ingreso_keywords(self, tipo_ingreso):
        """Retorna la lista de keywords (lowercase) para clasificar un tipo de
        ingreso a partir del CONTENIDO del documento (glosa del PDF + nombre de
        archivo), usada por `intake_wizard._onchange_suggest_tipo_ingreso`.

        Fuentes (cascada):
          1. ir.config_parameter 'madenat.tipo_ingreso_keywords' (JSON dict).
          2. Hardcode legacy.
        """
        # Fuente 1: ir.config_parameter Fase 1
        try:
            param_obj = self.env['ir.config_parameter'].sudo()
            raw = param_obj.get_param('madenat.tipo_ingreso_keywords', '')
            if raw:
                config = json.loads(raw)
                keywords = config.get(tipo_ingreso, [])
                if keywords:
                    _logger.info(
                        "IngestionConfig: tipo_ingreso_keywords desde Fase1 (%s, %d kw)",
                        tipo_ingreso, len(keywords),
                    )
                    return [str(k).lower() for k in keywords]
        except Exception as e:
            _logger.warning(
                "IngestionConfig: fallo Fase1 tipo_ingreso_keywords: %s", e)

        # Fuente 2: Hardcode legacy
        legacy = {
            'procesado': ['cepillado', 'servicio', 'proceso', 'maquila'],
            'granel': ['granel', 'volumen total', 'a granel', 'sin desglose'],
        }
        _logger.warning(
            "IngestionConfig: usando hardcode legacy tipo_ingreso_keywords (%s)",
            tipo_ingreso,
        )
        return legacy.get(tipo_ingreso, [])
