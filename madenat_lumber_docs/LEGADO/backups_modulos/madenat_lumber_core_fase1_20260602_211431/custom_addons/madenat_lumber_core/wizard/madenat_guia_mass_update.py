# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MadenatGuiaMassUpdate(models.TransientModel):
    _name = 'madenat.guia.mass.update'
    _description = 'Actualización Masiva de Espesor y Subproducto'

    # === ESPESOR (OBLIGATORIO) ===
    new_thickness_mm = fields.Float(
        string="Espesor Nominal (mm)",
        required=True,
        help="Espesor nominal obligatorio para cálculo de fracciones."
    )

    # === SUBPRODUCTO (OPCIONAL) ===
    subproducto_id = fields.Many2one(
        'madenat.subproducto',
        string="Subproducto / Grado",
        help="Clasificación comercial (Ej: Rough, s2s)"
    )

    def action_apply(self):
        self.ensure_one()
        
        # Validación
        if self.new_thickness_mm <= 0:
            raise UserError(_("⚠️ El espesor nominal es obligatorio y debe ser mayor a cero."))

        guia_id = self.env.context.get('active_id')
        if not guia_id:
            return {'type': 'ir.actions.act_window_close'}

        guia = self.env['madenat.guia.processing'].browse(guia_id)
        
        # 🛡️ CANDADO DE SEGURIDAD (Prevención de mezcla comercial)
        if self.subproducto_id:
            # Asumiendo que esta guía también tiene un perfil o tipo. Si no lo tiene, evalúa su nombre.
            nombre_sub = self.subproducto_id.name.upper()
            if hasattr(guia, 'ingestion_profile'):
                perfil = getattr(guia, 'ingestion_profile')
                if perfil == 'f5085' and ('S2S' in nombre_sub or 'RIP' in nombre_sub):
                    raise UserError(_("❌ No puede asignar un producto 'S2S/RIP' en una guía de tipo Rough/Blanks."))

        lines = guia.processing_line_ids
        if not lines:
            raise UserError(_("⚠️ No hay líneas de procesamiento para actualizar."))

        # 1. Aplicar Espesor (Siempre)
        lines.write({'espesor_nominal_mm': self.new_thickness_mm})

        # Recalcular visuales (Lógica de la guía intacta)
        for line in lines:
            nom_frac = guia._get_nominal_dimension(self.new_thickness_mm, 'thickness')
            if nom_frac:
                line.write({'thickness_visual': nom_frac})

        # 2. Aplicar Subproducto (Solo si se eligió)
        msg = f"⚡ <b>Actualización de Procesamiento:</b><br/>• Espesor Nominal: {self.new_thickness_mm} mm"
        
        if self.subproducto_id:
            lines.write({'subproducto_id': self.subproducto_id.id})
            msg += f"<br/>• Subproducto asignado: {self.subproducto_id.name}"

        # 3. Dejar rastro en el documento padre
        if hasattr(guia, 'message_post'):
            guia.message_post(body=msg)

        return {'type': 'ir.actions.act_window_close'}