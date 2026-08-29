# -*- coding: utf-8 -*-
"""Fachada de operación para Procesados en Intake.

Este modelo hereda `madenat.guia.processing` DENTRO de `madenat_lumber_intake`
para exponer navegación de retorno al Ingreso de Madera sin modificar el core.
No se añade lógica de negocio: solo un método de UX que devuelve la consola
de intake filtrada por el registro origen actual.
"""
from odoo import models, _

from .intake_constants import CONSOLE_ID_OFFSET


class MadenatGuiaProcessingIntake(models.Model):
    _inherit = 'madenat.guia.processing'

    def _get_intake_console_action(self):
        """Acción canónica de retorno a Ingreso de Madera (FIX 2026-08-21).

        Fuente única de verdad de navegación hacia la consola: evita que
        'name' hardcodeado compita con el breadcrumb de la fachada y que
        cada retorno genere una entrada de historial distinta.
        res_id=CONSOLE_ID_OFFSET+self.id es el id sintético de la vista SQL de
        consola. Sin side effects, escrituras ni búsquedas.
        FIX ACCESO (2026-08-22): ya NO se lee la acción técnica
        ir.actions.act_window (action_madenat_lumber_intake_console) para
        obtener el name, porque Operaciones carece de base.group_system y
        env.ref(...).name generaba AccessError. Se usa 'name' fijo
        'Ingreso de Madera', idéntico al nombre canónico de la acción.
        """
        self.ensure_one()
        console_form_view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ingreso de Madera',
            'res_model': 'madenat.lumber.intake.console',
            'res_id': CONSOLE_ID_OFFSET + self.id,
            # ROLLBACK 2026-08-22: se restaura la fachada/formulario original
            # de Ingreso de Madera (view_mode='form') que el flujo de envío a
            # stock necesita operar. El cambio anterior a 'list,form' (botón
            # "Nuevo") se revierte porque perdía la vista operativa principal.
            # views explícito se mantiene para la client action (doAction).
            'view_mode': 'form',
            'view_id': console_form_view.id,
            'views': [(console_form_view.id, 'form')],
            'target': 'current',
        }

    def action_back_to_intake_console(self):
        """Vuelve a Ingreso de Madera vía acción canónica (FIX 2026-08-21).

        AD-55: el core NO tiene este método; se define por herencia en Intake.
        No toca stock ni lógica de negocio. La acción proviene del helper
        único _get_intake_console_action para evitar nombre/contexto ad hoc.
        """
        self.ensure_one()
        # FIX 2026-08-22: envolver en client action para reemplazar el controller
        # actual (evita breadcrumbs repetidos). El helper canónico se preserva.
        inner = self._get_intake_console_action()
        return {
            'type': 'ir.actions.client',
            'tag': 'madenat_lumber_intake.replace_current_action',
            'params': {'action_to_execute': inner},
        }
