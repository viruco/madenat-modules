# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from ..models.utils_uom import S2S_WIDTH_LOOKUP
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LumberReceptionMassUpdate(models.TransientModel):
    _name = 'lumber.reception.mass.update'
    _description = 'Asignación Masiva de Nominales y Subproducto'

    # 🛡️ BLINDAJE ABSOLUTO: Buscar el perfil real directamente en BD
    # Evita que el Wizard nazca "ciego" si Javascript falla al enviar el contexto.
    def _get_default_profile(self):
        rec_id = self.env.context.get('default_reception_id') or self.env.context.get('active_id')
        if rec_id:
            reception = self.env['lumber.reception'].browse(rec_id)
            if reception.exists():
                return reception.ingestion_profile
        return False

    # =========================================================================
    # CAMPOS — ENLACE CON LA RECEPCIÓN PADRE
    # =========================================================================
    reception_id = fields.Many2one(
        'lumber.reception',
        string="Recepción",
        default=lambda self: self.env.context.get('default_reception_id') or self.env.context.get('active_id')
    )
    
    # Campo normal (NO related) con inyección directa desde la BD mediante _get_default_profile
    ingestion_profile = fields.Selection([
        ('f5085', 'Blanks/Clear (Factor 5085 - Pies)'),
        ('f1550', 'S2S/RIP (Factor 1550 - Metros)'),
        ('metric', 'Madera Bruta (Milimétrico Directo)')
    ], string="Perfil de Ingesta", default=_get_default_profile)

    # =========================================================================
    # CAMPOS — INPUT VISUAL (lo que escribe el humano)
    # =========================================================================
    # REGLA DE ORO DE INPUT:
    #   f5085 (Blanks/Clear) → fracciones imperiales  → parse × 25.4 → mm
    #   f1550 (S2S/RIP)      → fracciones imperiales  → parse × 25.4 → mm
    #   metric (Madera Bruta)→ milímetros directos    → NO multiplicar × 25.4
    # -------------------------------------------------------------------------
    thickness_nominal_frac = fields.Char(
        string="Espesor (Pulg/Fracción)",
        help="Imperial: Ej. 6/4, 1 9/16, 1.5  |  Métrico: Ej. 45 (mm directo)"
    )
    width_nominal_frac = fields.Char(
        string="Ancho (Pulg/Fracción)",
        help="Imperial: Ej. 3 5/8, 4.0  |  Métrico: Ej. 125 (mm directo)"
    )

    # =========================================================================
    # CAMPOS — RESULTADO EN MM (calculado automáticamente por el onchange)
    # =========================================================================
    thickness_nominal = fields.Float(
        string="Espesor Nominal (mm)", default=0.0, digits=(16, 2)
    )
    width_nominal = fields.Float(
        string="Ancho Nominal (mm)", default=0.0, digits=(16, 2)
    )

    # =========================================================================
    # ⚙️ CONVERSOR INTELIGENTE — FRACCIÓN / MM DIRECTO → MILÍMETROS
    # =========================================================================
    @api.onchange('thickness_nominal_frac', 'width_nominal_frac', 'ingestion_profile')
    def _onchange_fraction_to_mm(self):
        """
        Convierte el input visual a mm según el perfil de ingesta activo.

        LÓGICA DE CONVERSIÓN:
          - metric  → el usuario ingresa mm directamente → NO × 25.4
          - f5085   → el usuario ingresa fracción imperial → × 25.4
          - f1550   → AUTO-DETECTA: con '/' → imperial × 25.4; sin '/' → mm directo

        FORMATOS ACEPTADOS (auto-detectados por presencia de '/'):
          "6/4"       → tiene '/' → imperial → 1.5"   × 25.4 = 38.1 mm
          "1 9/16"    → tiene '/' → imperial → 1.5625"× 25.4 = 39.69 mm
          "3 5/8"     → tiene '/' → imperial → 3.625" × 25.4 = 92.08 mm
          "45"        → sin '/' → mm directo → 45 mm (FATIMA entrega mm)
          "145"       → sin '/' → mm directo → 145 mm

        FORMATOS ACEPTADOS (métricos, perfil metric):
          "45"        → 45 mm (directo, sin conversión)
          "125"       → 125 mm (directo, sin conversión)
        """
        # Detectar si estamos en modo métrico puro
        is_metric = (self.ingestion_profile == 'metric')
        warning_messages = []

        def _parse_imperial_to_mm(val_str):
            """Parsea fracción/decimal imperial a milímetros."""
            if not val_str:
                return 0.0
            val_str = str(val_str).strip().replace(',', '.')
            try:
                if ' ' in val_str and '/' in val_str:
                    # Formato mixto: "1 9/16" → entero + fracción
                    whole, frac = val_str.split(' ', 1)
                    num, den = frac.split('/')
                    inches = float(whole) + (float(num) / float(den))
                elif '/' in val_str:
                    # Fracción pura: "6/4" o "3/4"
                    num, den = val_str.split('/')
                    inches = float(num) / float(den)
                else:
                    # Decimal: "1.5"
                    inches = float(val_str)
                return round(inches * 25.4, 2)
            except Exception:
                return 0.0

        def _parse_metric_direct(val_str, campo_nombre):
            """Para Madera Bruta: el usuario entra mm directamente, sin conversión."""
            if not val_str:
                return 0.0
            try:
                return round(float(str(val_str).strip().replace(',', '.')), 2)
            except ValueError:
                # Acumulamos el error en lugar de sobreescribir el campo con basura
                warning_messages.append(
                    f'Para perfil métrico ingrese milímetros directos. '
                    f'Recibido en {campo_nombre}: "{val_str}"'
                )
                return 0.0


        def _parse_smart(val_str):
            """
            Auto-detecta formato sin hardcodear umbrales:
            - Contiene '/' → fracción imperial → _parse_imperial_to_mm
            - Sin '/'      → mm directos (FATIMA entrega mm en f1550/f5085)
            """
            if not val_str:
                return 0.0
            val_str = str(val_str).strip().replace(',', '.')
            if '/' in val_str:
                return _parse_imperial_to_mm(val_str)
            try:
                return round(float(val_str), 2)
            except Exception:
                warning_messages.append(
                    f'Valor no reconocible: "{val_str}". '
                    f'Use fracciones (6/4, 3 5/8) o mm directos (45, 145).'
                )
                return 0.0

        # Aplicar la función correcta según el perfil
        if self.thickness_nominal_frac:
            self.thickness_nominal = (
                _parse_metric_direct(self.thickness_nominal_frac, "Espesor") if is_metric
                else _parse_smart(self.thickness_nominal_frac)
            )
        if self.width_nominal_frac:
            self.width_nominal = (
                _parse_metric_direct(self.width_nominal_frac, "Ancho") if is_metric
                else _parse_smart(self.width_nominal_frac)
            )

        # Si hubo errores tipográficos en modo métrico, lanzar la advertencia visual
        if warning_messages:
            return {'warning': {
                'title': '⚠️ Valor inválido',
                'message': '\n'.join(warning_messages)
            }}

    # =========================================================================
    # 🛡️ FILTRO VISUAL DINÁMICO DE SUBPRODUCTOS
    # =========================================================================
    allowed_subproduct_ids = fields.Many2many(
        'madenat.subproducto',
        compute='_compute_allowed_subproducts',
        string="Subproductos Permitidos"
    )

    def _get_profile_subproduct_filters(self):
        """Fase 2: Lee desde helper centralizado con fallback Fase 1 + legacy."""
        config = self.env['madenat.ingestion.config']
        return {
            "profiles": {
                "f5085": {
                    "allowed_keywords": config.get_profile_subproduct_rules('f5085', 'allowed'),
                    "forbidden_keywords": config.get_profile_subproduct_rules('f5085', 'forbidden'),
                    "forbidden_in_lock": config.get_profile_subproduct_rules('f5085', 'forbidden_in_lock'),
                },
                "f1550": {
                    "allowed_keywords": config.get_profile_subproduct_rules('f1550', 'allowed'),
                    "forbidden_keywords": config.get_profile_subproduct_rules('f1550', 'forbidden'),
                    "forbidden_in_lock": config.get_profile_subproduct_rules('f1550', 'forbidden_in_lock'),
                },
                "metric": {
                    "allowed_keywords": config.get_profile_subproduct_rules('metric', 'allowed'),
                    "forbidden_keywords": config.get_profile_subproduct_rules('metric', 'forbidden'),
                    "forbidden_in_lock": config.get_profile_subproduct_rules('metric', 'forbidden_in_lock'),
                },
            }
        }

    @api.depends('ingestion_profile')
    def _compute_allowed_subproducts(self):
        """
        Filtra subproductos disponibles según la Regla de Oro del perfil.
        FASE 3: Filtro estructural (allowed_formula_ids → lumber.export.formula)
                con fallback textual legacy (lumber.profile.subproduct.rule).

        PRIORIDAD:
          1. Si existe fórmula activa para el perfil:
             → subproductos con esa fórmula en allowed_formula_ids
             → + subproductos sin fórmula asignada (legacy)
          2. Si NO existe fórmula activa:
             → fallback textual legacy (keywords ilike en name)

        MATRIZ DE FILTROS (fallback):
          f5085 (Blanks) → excluye S2S y RIP
          f1550 (S2S)    → solo muestra S2S
          metric         → sin filtro (muestra todos)
        """
        Formula = self.env['lumber.export.formula'].sudo()
        filters_config = self._get_profile_subproduct_filters()
        profiles_cfg = filters_config.get('profiles', {})

        for wizard in self:
            perfil = wizard.ingestion_profile

            # ── PRIORIDAD 1: Filtro estructural por fórmula ──────────────
            formula = Formula.search([
                ('profile', '=', perfil),
                ('active', '=', True),
            ], limit=1, order='sequence')

            if formula:
                # Subproductos con esta fórmula en allowed_formula_ids
                # + subproductos sin fórmula asignada (legacy, visibles en todos)
                domain_structural = [
                    '|',
                    ('allowed_formula_ids', 'in', [formula.id]),
                    ('allowed_formula_ids', '=', False),
                ]
                wizard.allowed_subproduct_ids = self.env['madenat.subproducto'].search(
                    domain_structural
                )
            else:
                # ── PRIORIDAD 2: Fallback textual legacy ─────────────────
                cfg = profiles_cfg.get(perfil, {})
                allowed = cfg.get('allowed_keywords', [])
                forbidden = cfg.get('forbidden_keywords', [])
                domain = [('allowed_formula_ids', '=', False)]
                for kw in forbidden:
                    domain.append(('name', 'not ilike', kw))
                if allowed:
                    if len(allowed) > 1:
                        domain.append('|' * (len(allowed) - 1))
                    for kw in allowed:
                        domain.append(('name', 'ilike', kw))
                wizard.allowed_subproduct_ids = self.env['madenat.subproducto'].search(domain)

    # =========================================================================
    # CAMPOS — CLASIFICACIÓN Y ALCANCE
    # =========================================================================
    subproduct_id = fields.Many2one(
        'madenat.subproducto',
        string="Subproducto / Grado",
        help="Clasificación técnica MADENAT para los paquetes seleccionados"
    )

    apply_to = fields.Selection([
        ('selected', 'Solo líneas seleccionadas'),
        ('all', 'Todas las líneas de la recepción')
    ], string="Aplicar a", default='all', required=True)

    # =========================================================================
    # 🚀 ACCIÓN PRINCIPAL — INYECCIÓN MASIVA
    # =========================================================================
    def action_apply(self):
        """
        Inyecta valores nominales (mm), textos visuales (fracciones)
        y el subproducto en las líneas objetivo del espejo documental.

        FLUJO:
          0. Guardia defensiva (valores anómalos métricos)
          1. Validar integridad (recepción existente)
          2. Validar consistencia comercial (candado perfil vs subproducto)
          3. Determinar líneas objetivo (todas o seleccionadas)
          4. Construir vals y hacer write()
          5. Registrar auditoría en el chatter de la recepción
        """
        self.ensure_one()

        # ── 0. GUARDIA DEFENSIVA CONTRA CORRUPCIÓN DE INVENTARIO ──────────────
        if self.ingestion_profile == 'metric' and (self.thickness_nominal > 500 or self.width_nominal > 500):
            raise UserError(_(
                f"⛔ MADENAT — Perfil Métrico detecta valores anómalos:\n"
                f"  Espesor: {self.thickness_nominal} mm  |  Ancho: {self.width_nominal} mm\n\n"
                f"Para madera bruta los nominales no deben superar los 500 mm.\n"
                f"Verifique que ingresó milímetros directos, no pulgadas o fracciones."
            ))

        # ── 1. GUARDIA DE INTEGRIDAD ──────────────────────────────────────────
        if not self.reception_id:
            raise UserError(_(
                "❌ Error de integridad: No se encontró la recepción principal."
            ))

        # ── 2. CANDADO DE SEGURIDAD COMERCIAL (PARAMETRIZADO FASE 1) ─────────
        if self.subproduct_id and self.ingestion_profile:
            perfil = self.ingestion_profile
            nombre_sub = self.subproduct_id.name.upper()
            filters_config = self._get_profile_subproduct_filters()
            profiles_cfg = filters_config.get('profiles', {})
            cfg = profiles_cfg.get(perfil, {})
            forbidden_in_lock = cfg.get('forbidden_in_lock', [])
            for kw in forbidden_in_lock:
                if kw.upper() in nombre_sub:
                    raise UserError(_(
                        "❌ ERROR DE CONSISTENCIA COMERCIAL:\n"
                        "Está intentando asignar un subproducto '%s' en una "
                        "recepción configurada como %s.\n"
                        "Por favor, seleccione un subproducto válido."
                    ) % (self.subproduct_id.name, perfil.upper()))

        # ── 3. DETERMINAR LÍNEAS OBJETIVO ─────────────────────────────────────
        if self.apply_to == 'selected':
            # Líneas marcadas en la vista lista por el usuario
            active_ids = self.env.context.get('active_ids', [])
            lines = self.env['lumber.reception.line'].browse(active_ids)
        else:
            # Todas las líneas de la recepción padre
            lines = self.reception_id.reception_line_ids

        if not lines:
            raise UserError(_(
                "⚠️ No hay paquetes disponibles para actualizar.\n"
                "Verifique que la recepción tenga líneas o que haya "
                "seleccionado al menos un paquete."
            ))

        # ── 4. CONSTRUIR VALS Y ESCRIBIR ──────────────────────────────────────
        # Solo se incluyen campos con valor real para no sobreescribir
        # datos existentes con ceros accidentalmente.
        vals = {}

        if self.thickness_nominal > 0:
            vals['thickness_nominal'] = self.thickness_nominal
            # thickness_nominal_frac: texto visual para UI y auditoría
            vals['thickness_nominal_frac'] = self.thickness_nominal_frac or ''

        if self.width_nominal > 0:
            vals['width_nominal'] = self.width_nominal
            # width_nominal_frac: texto visual para UI y auditoría
            vals['width_nominal_frac'] = self.width_nominal_frac or ''

        vals['subproduct_id'] = self.subproduct_id.id or False

        if not vals:
            raise UserError(_(
                "⚠️ No hay valores para aplicar.\n"
                "Complete al menos un campo antes de confirmar."
            ))

        # write() dispara la cadena ORM:
        # thickness_nominal → _compute_visual_defaults → thickness_visual
        #                                               → width_visual
        #                                                     ↓
        #                                            _compute_export_values → vol_shipment_m3
        lines.write(vals)

        # ── 5. AUDITORÍA EN CHATTER ───────────────────────────────────────────
        perfil_label = {
            'f5085':  '🪵 Blanks/Clear (Factor 5085 - Pies)',
            'f1550':  '📐 S2S/RIP (Factor 1550 - Metros)',
            'metric': '📏 Madera Bruta (mm directo)',
        }.get(self.ingestion_profile, self.ingestion_profile or 'N/D')

        msg = (
            f"⚡ <b>Actualización Masiva de Inventario</b> "
            f"<span class='text-muted'>— {perfil_label}</span><br/>"
        )

        if self.thickness_nominal:
            frac_str = (
                f" <code>({self.thickness_nominal_frac})</code>"
                if self.thickness_nominal_frac else ""
            )
            msg += f"• Espesor Nominal: <b>{self.thickness_nominal} mm</b>{frac_str}<br/>"

        if self.width_nominal:
            frac_str = (
                f" <code>({self.width_nominal_frac})</code>"
                if self.width_nominal_frac else ""
            )
            msg += f"• Ancho Nominal: <b>{self.width_nominal} mm</b>{frac_str}<br/>"

        if self.subproduct_id:
            msg += f"• Clasificación: <b>{self.subproduct_id.name}</b>"

        self.reception_id.message_post(body=msg)

        return {'type': 'ir.actions.act_window_close'}