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
    def get_width_s2s_map(self, raise_if_empty=True, include_overwidth=False):
        """Retorna dict {rough_mm: (s2s_decimal, s2s_label)} desde lumber.width.s2s.map.

        Si include_overwidth=True, retorna {rough_mm: (s2s_decimal, s2s_label, overwidth_inches)}.
        Única fuente de verdad: lumber.width.s2s.map.
        Si no hay registros activos y raise_if_empty=True (default), lanza UserError.
        Con raise_if_empty=False retorna dict vacío (para comprobaciones no bloqueantes).
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
        if include_overwidth:
            return {rec.rough_mm: (rec.s2s_decimal, rec.s2s_label, rec.overwidth_inches) for rec in records}
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
    def resolve_export_width_details(
        self,
        rough_mm,
        product_type=None,
        profile=None,
        record=None,
        is_s2s_inches=False,
        width_visual=None,
    ):
        """API Única centralizada para resolución de ancho de exportación y metadatos (H4 / AD-130).

        Retorna un dict con:
            - 'nominal_width_display': str (ej: '5 5/8', '170 mm', '4 5/8')
            - 'nominal_width_inches': float (ej: 5.625 para 150mm; mm / 25.4 si fuera de tabla)
            - 'calc_width_inches': float (ancho de cubicación oficial; ej: 5.750 con +1/8"; mm/25.4 si fuera de tabla)
            - 'overwidth_inches': float (sobreancho aplicado: por fila o global si en tabla; 0.0 si fuera de tabla)
            - 'is_out_of_table': bool (True si rough_mm no pertenece a lumber.width.s2s.map)
            - 'out_of_table_status': str ('ok', 'out_of_table_confirm', 'manual_override')

        Orden canónico de resolución:
        1. Manual Override: si record tiene export_width_manual_inches > 0, se respeta estrictamente.
        2. Señal explícita documental en pulgadas S2S: is_s2s_inches=True (ej. desde normalizador de documentos).
        3. Pertenencia a lumber.width.s2s.map: si rough_mm está en tabla activa:
           nominal = s2s_decimal, display = s2s_label, overwidth = overwidth_fila or global, calc = nominal + overwidth.
        4. Fuera de tabla (incluye anchos ausentes < 170 y >= 170 mm):
           nominal = rough_mm / 25.4, display = width_visual or f"{rough_mm} mm", overwidth = 0.0, calc = nominal.
           is_out_of_table = True, out_of_table_status = 'out_of_table_confirm'.
           Si rough_mm < min_direct, aplica política out_of_table_behavior ('block' -> ValidationError; 'warning' -> advertencia).
        """
        if not rough_mm or rough_mm <= 0:
            return {
                'nominal_width_display': '',
                'nominal_width_inches': 0.0,
                'calc_width_inches': 0.0,
                'overwidth_inches': 0.0,
                'is_out_of_table': False,
                'out_of_table_status': 'ok',
            }

        from .utils_uom import MM_PER_INCH, decimal_inch_to_fraction_simple

        # 1. Manual override
        manual_in = 0.0
        if record and hasattr(record, 'export_width_manual_inches'):
            manual_in = float(record.export_width_manual_inches or 0.0)
        if manual_in > 0.0:
            display = str(getattr(record, 'export_width_manual_display', '') or '')
            if not display:
                display = decimal_inch_to_fraction_simple(manual_in) or f"{manual_in:.3f}\""
            return {
                'nominal_width_display': display,
                'nominal_width_inches': manual_in,
                'calc_width_inches': manual_in,
                'overwidth_inches': 0.0,
                'is_out_of_table': False,
                'out_of_table_status': 'manual_override',
            }

        # 2. Señal explícita documental S2S (is_s2s_inches)
        signal_s2s = is_s2s_inches or (record and getattr(record, 'is_s2s_inches', False))
        if signal_s2s:
            overwidth = self.get_s2s_overwidth_inches()
            nom_in = float(rough_mm) / float(MM_PER_INCH)
            calc_in = nom_in + overwidth
            display = width_visual or decimal_inch_to_fraction_simple(nom_in) or f"{nom_in:.3f}\""
            return {
                'nominal_width_display': display,
                'nominal_width_inches': nom_in,
                'calc_width_inches': calc_in,
                'overwidth_inches': overwidth,
                'is_out_of_table': False,
                'out_of_table_status': 'ok',
            }

        min_direct = self.get_direct_width_min_mm()

        # Si la tabla está vacía en BD y rough_mm < min_direct, get_width_s2s_map(raise_if_empty=True)
        # preserva el UserError canónico exigido por G5
        mapping = self.get_width_s2s_map(raise_if_empty=False, include_overwidth=True)
        if not mapping and rough_mm < min_direct:
            mapping = self.get_width_s2s_map(raise_if_empty=True, include_overwidth=True)

        rough_key = int(round(rough_mm))

        # 3. Pertenencia a lumber.width.s2s.map
        if mapping and rough_key in mapping:
            entry = mapping[rough_key]
            s2s_decimal = entry[0]
            s2s_label = entry[1]
            row_overwidth = entry[2] if len(entry) > 2 and entry[2] > 0.0 else self.get_s2s_overwidth_inches()
            calc_in = s2s_decimal + row_overwidth
            return {
                'nominal_width_display': s2s_label,
                'nominal_width_inches': s2s_decimal,
                'calc_width_inches': calc_in,
                'overwidth_inches': row_overwidth,
                'is_out_of_table': False,
                'out_of_table_status': 'ok',
            }

        # 4. Fuera de tabla (Regla d / CANON/17 §9.2: exportación métrica directa sin +1/8")
        nom_in = float(rough_mm) / float(MM_PER_INCH)
        calc_in = nom_in  # Sin sobreancho

        behavior = self.get_out_of_table_behavior()
        if rough_mm < min_direct:
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

        display = width_visual or (f"{int(rough_mm)} mm" if rough_mm == int(rough_mm) else f"{rough_mm:.1f} mm")
        return {
            'nominal_width_display': display,
            'nominal_width_inches': nom_in,
            'calc_width_inches': calc_in,
            'overwidth_inches': 0.0,
            'is_out_of_table': True,
            'out_of_table_status': 'out_of_table_confirm',
        }

    @api.model
    def resolve_export_width(self, rough_mm, record=None, is_s2s_inches=False):
        """Resuelve el ancho de exportación de cubicación en pulgadas delegando en la API única (H4 / AD-130)."""
        details = self.resolve_export_width_details(
            rough_mm=rough_mm,
            record=record,
            is_s2s_inches=is_s2s_inches,
        )
        return details['calc_width_inches']

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
