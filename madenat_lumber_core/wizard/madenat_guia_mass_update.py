# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MadenatGuiaMassUpdate(models.TransientModel):
    _name = 'madenat.guia.mass.update'
    _description = 'Actualización Masiva de Espesor, Subproducto y Producto'

    # === ESPESOR (OPCIONAL) ===
    new_thickness_mm = fields.Float(
        string="Espesor Nominal (mm)",
        required=False,
        help="Si se informa, actualiza el espesor nominal y recalcula la fracción visual."
    )

    # === SUBPRODUCTO (OPCIONAL) ===
    subproducto_id = fields.Many2one(
        'madenat.subproducto',
        string="Subproducto / Grado",
        help="Clasificación comercial (Ej: Rough, s2s)"
    )

    # === PRODUCTO (OPCIONAL) ===
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        help="Producto a asignar en las líneas. Si no se selecciona, se mantiene el actual."
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

    def action_apply(self):
        self.ensure_one()

        thickness_informed = bool(self.new_thickness_mm and self.new_thickness_mm > 0)
        subproduct_informed = bool(self.subproducto_id)
        product_informed = bool(self.product_id)

        if not (thickness_informed or subproduct_informed or product_informed):
            raise UserError(_("⚠️ Debe indicar al menos un valor para actualizar: espesor, subproducto o producto."))

        if self.new_thickness_mm and self.new_thickness_mm < 0:
            raise UserError(_("⚠️ El espesor nominal no puede ser negativo."))

        guia_id = self.env.context.get('active_id')
        if not guia_id:
            return {'type': 'ir.actions.act_window_close'}

        guia = self.env['madenat.guia.processing'].browse(guia_id)

        # 🛡️ CANDADO DE SEGURIDAD (Prevención de mezcla comercial) — solo si se cambia subproducto
        if self.subproducto_id:
            nombre_sub = self.subproducto_id.name.upper()
            if hasattr(guia, 'ingestion_profile'):
                perfil = getattr(guia, 'ingestion_profile')
                filters_config = self._get_profile_subproduct_filters()
                profiles_cfg = filters_config.get('profiles', {})
                cfg = profiles_cfg.get(perfil, {})
                forbidden_in_lock = cfg.get('forbidden_in_lock', [])
                for kw in forbidden_in_lock:
                    if kw.upper() in nombre_sub:
                        raise UserError(_("❌ No puede asignar un producto '%s' en una guía de tipo %s.") % (
                            self.subproducto_id.name, perfil.upper()
                        ))

        lines = guia.processing_line_ids
        if not lines:
            raise UserError(_("⚠️ No hay líneas de procesamiento para actualizar."))

        msg_lines = ["⚡ <b>Actualización de Procesamiento:</b>"]

        # 1. Aplicar Espesor solo si fue informado
        if thickness_informed:
            lines.write({'espesor_nominal_mm': self.new_thickness_mm})

            for line in lines:
                nom_frac = guia._get_nominal_dimension(self.new_thickness_mm, 'thickness')
                if nom_frac:
                    line.write({'thickness_visual': nom_frac})

            msg_lines.append(f"• Espesor nominal: {self.new_thickness_mm} mm")

        # 2. Aplicar Subproducto solo si fue informado
        if subproduct_informed:
            lines.write({'subproducto_id': self.subproducto_id.id})
            msg_lines.append(f"• Subproducto asignado: {self.subproducto_id.name}")

        # 3. Aplicar Producto solo si fue informado
        if product_informed:
            lines.write({'product_id': self.product_id.id})
            msg_lines.append(f"• Producto asignado: {self.product_id.display_name}")

        # 4. Rastro en chatter
        if hasattr(guia, 'message_post'):
            guia.message_post(body="<br/>".join(msg_lines))

        return {'type': 'ir.actions.act_window_close'}