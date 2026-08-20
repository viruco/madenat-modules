# -*- coding: utf-8 -*-
"""Fachada de operación para Procesados en Intake.

Este modelo hereda `madenat.guia.processing` DENTRO de `madenat_lumber_intake`
para exponer navegación de retorno al Ingreso Global sin modificar el core.
No se añade lógica de negocio: solo un método de UX que devuelve la consola
de intake filtrada por el registro origen actual.
"""
from odoo import models, _


class MadenatGuiaProcessingIntake(models.Model):
    _inherit = 'madenat.guia.processing'

    def action_back_to_intake_console(self):
        """Vuelve al Ingreso Global abriendo el registro de consola del Procesado.

        AD-55: el core NO tiene este método; se define por herencia en Intake
        para dar la misma navegación que Producto. No toca stock ni lógica de
        negocio.
        """
        self.ensure_one()
        # Vuelve EXACTAMENTE al registro de la consola del que se abrió la
        # fachada (patrón Producto): res_id=900000000+self.id es el id canónico
        # que la vista SQL de la consola asigna a cada madenat.guia.processing.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ingreso Global'),
            'res_model': 'madenat.lumber.intake.console',
            'res_id': 900000000 + self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
            ).id,
            'target': 'current',
        }
