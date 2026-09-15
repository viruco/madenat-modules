# -*- coding: utf-8 -*-
"""Advertencia generada durante la extracción de un documento de ingesta.

DECISIÓN D2: las advertencias solo deben existir pobladas por
``action_extract()``; son un snapshot inmutable de trazabilidad.
"""
from odoo import _, fields, models
from odoo.exceptions import UserError


class MadenatIngestionDocumentWarning(models.Model):
    _name = "madenat.ingestion.document.warning"
    _description = "Advertencia generada durante la extracción"
    _order = "row_number asc, id asc"

    document_id = fields.Many2one(
        "madenat.ingestion.document", required=True,
        ondelete="cascade", readonly=True)
    row_number = fields.Integer(readonly=True)
    message = fields.Char(readonly=True, required=True)

    def _is_locked(self):
        self.ensure_one()
        return True

    def write(self, vals):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "Esta advertencia pertenece a un documento de ingesta "
                        "ya procesado y no puede modificarse."
                    ))
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "No se puede eliminar una advertencia de un documento "
                        "de ingesta ya procesado. Es un registro inmutable."
                    ))
        return super().unlink()
