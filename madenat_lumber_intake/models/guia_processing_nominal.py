# -*- coding: utf-8 -*-
"""Auto-sugerencia del espesor nominal en líneas de Procesado (Intake).

Cuando una línea ``madenat.guia.processing.line`` se crea desde el Excel con
``espesor_mm`` y sin ``espesor_nominal_mm`` informado, se copia el valor físico
al nominal en el propio ``vals`` de creación. Sin campos nuevos, sin compute y
sin imports del core.
"""
from odoo import api, models


class GuiaProcessingLineNominal(models.Model):
    _inherit = "madenat.guia.processing.line"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("espesor_mm") and not vals.get("espesor_nominal_mm"):
                vals["espesor_nominal_mm"] = vals["espesor_mm"]
        return super().create(vals_list)
