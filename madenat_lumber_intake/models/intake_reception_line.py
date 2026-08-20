# -*- coding: utf-8 -*-
"""Fachada de edición individual de línea de Producto (readonly, sin lógica nueva).

Agrega sobre `lumber.reception.line` únicamente la acción que abre el editor
modal. No duplica writes, recomputes ni validaciones del core: al guardar, el
ORM del propio `lumber.reception.line` (compute store, inverse, onchange)
recalcula y valida igual que en la form XXL del core.
"""
from odoo import models


class LumberReceptionLineIntake(models.Model):
    _inherit = 'lumber.reception.line'

    def action_open_intake_line_editor(self):
        """Abre esta línea real en un editor modal (target=new, no se crea registro)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.reception.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'madenat_lumber_intake.view_lumber_reception_line_intake_editor_form'
            ).id,
            'target': 'new',
        }