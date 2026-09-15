# -*- coding: utf-8 -*-
"""Cabecera de un documento de ingesta procesado por el motor de extracción.

DECISIÓN D2 (inmutabilidad post-extracción): una vez que ``action_extract()``
ejecuta (con éxito o error), los campos de resultado, las líneas y las
advertencias quedan blindados. Si el archivo es incorrecto, se carga un
documento nuevo; nunca se sobrescribe uno existente.
"""
import base64
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    extract_document,
)


class MadenatIngestionDocument(models.Model):
    _name = "madenat.ingestion.document"
    _description = "Documento de Ingesta (staging de extracción)"
    _order = "id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False)
    file = fields.Binary(string="Archivo", required=True, attachment=True)
    filename = fields.Char(string="Nombre de archivo")
    state = fields.Selection([
        ("draft", "Borrador"),
        ("extracted", "Extraído"),
        ("error", "Error"),
    ], default="draft", readonly=True, copy=False)

    # Campos de resultado (header de DocumentExtractionResult, 1 a 1).
    # Todos readonly; solo los pobla action_extract().
    guide_number = fields.Char(readonly=True)
    guide_date = fields.Date(readonly=True)
    supplier_rut = fields.Char(readonly=True)
    supplier_name = fields.Char(readonly=True)
    customer_rut = fields.Char(readonly=True)
    customer_name = fields.Char(readonly=True)
    oc_reference = fields.Char(readonly=True)
    carrier_name = fields.Char(readonly=True)
    carrier_rut = fields.Char(readonly=True)
    carrier_phone = fields.Char(readonly=True)
    license_plate = fields.Char(readonly=True)
    destination_label = fields.Char(readonly=True)
    net_total = fields.Float(readonly=True)
    tax_total = fields.Float(readonly=True)
    total = fields.Float(readonly=True)
    exchange_rate = fields.Float(readonly=True)
    total_volume_m3 = fields.Float(readonly=True, digits=(16, 3))
    detected_profile_code = fields.Char(readonly=True)
    sheet_name_used = fields.Char(readonly=True)

    error_message = fields.Text(readonly=True)
    warning_count = fields.Integer(readonly=True, default=0)

    line_ids = fields.One2many(
        "madenat.ingestion.document.line", "document_id",
        string="Líneas extraídas", readonly=True)
    warning_ids = fields.One2many(
        "madenat.ingestion.document.warning", "document_id",
        string="Advertencias", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nuevo":
                vals["name"] = (
                    seq.next_by_code("madenat.ingestion.document") or "Nuevo"
                )
        return super().create(vals_list)

    # ──────────────────────────────────────────────────────────────────────
    # Blindaje D2: inmutabilidad post-extracción
    # ──────────────────────────────────────────────────────────────────────
    def _is_locked(self):
        self.ensure_one()
        return self.state != "draft"

    def write(self, vals):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "Este documento de ingesta ya fue procesado y no puede "
                        "modificarse. Cargue un documento nuevo si necesita "
                        "corregir algo."
                    ))
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "No se puede eliminar un documento de ingesta ya "
                        "procesado. Es un registro de auditoría inmutable."
                    ))
        return super().unlink()

    # ──────────────────────────────────────────────────────────────────────
    # Extracción
    # ──────────────────────────────────────────────────────────────────────
    def action_extract(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_(
                "Este documento ya fue procesado y no puede volver a procesarse. "
                "Si el archivo es incorrecto, cargue un documento nuevo."
            ))
        if not self.file:
            raise UserError(_("Debe adjuntar un archivo antes de procesar."))

        try:
            file_bytes = base64.b64decode(self.file)
        except Exception as exc:
            raise UserError(_("El archivo adjunto no es válido: %s") % exc)

        try:
            result = extract_document(file_bytes, self.filename or "")
        except DocumentExtractionError as exc:
            # D2: el estado 'error' también es inmutable (no se reprocesa).
            self.with_context(force_ingestion_write=True).write({
                "state": "error",
                "error_message": str(exc),
            })
            return self._reload_form_action()

        forced = self.with_context(force_ingestion_write=True)

        line_commands = []
        warning_commands = []
        warning_row_numbers = set()

        for line_data in result.lines:
            line_commands.append((0, 0, {
                "source_row_number": line_data.get("source_row_number"),
                "package_no": line_data.get("package_no"),
                "product_code": line_data.get("product_code"),
                "product_name_original": line_data.get("product_name_original"),
                "thickness_value_raw": line_data.get("thickness_value_raw"),
                "thickness_unit": line_data.get("thickness_unit"),
                "width_value_raw": line_data.get("width_value_raw"),
                "width_unit": line_data.get("width_unit"),
                "length_value_raw": line_data.get("length_value_raw"),
                "length_unit": line_data.get("length_unit"),
                "rows": line_data.get("rows"),
                "columns": line_data.get("columns"),
                "pieces": line_data.get("pieces"),
                "volume_m3": line_data.get("volume_m3"),
                "lot_number": line_data.get("lot_number"),
            }))

        # Parseo best-effort de row_number en advertencias.
        for message in result.warnings:
            row_number = 0
            match = re.match(r"^Fila (\d+):", message)
            if match:
                row_number = int(match.group(1))
            warning_commands.append((0, 0, {
                "row_number": row_number,
                "message": message,
            }))
            warning_row_numbers.add(row_number)

        # Marcar has_warning en las líneas cuyo source_row_number tiene warning.
        for command in line_commands:
            line_vals = command[2]
            line_vals["has_warning"] = (
                line_vals.get("source_row_number") in warning_row_numbers
            )

        forced.write({
            "guide_number": result.header.get("guide_number"),
            "guide_date": result.header.get("guide_date"),
            "supplier_rut": result.header.get("supplier_rut"),
            "supplier_name": result.header.get("supplier_name"),
            "customer_rut": result.header.get("customer_rut"),
            "customer_name": result.header.get("customer_name"),
            "oc_reference": result.header.get("oc_reference"),
            "carrier_name": result.header.get("carrier_name"),
            "carrier_rut": result.header.get("carrier_rut"),
            "carrier_phone": result.header.get("carrier_phone"),
            "license_plate": result.header.get("license_plate"),
            "destination_label": result.header.get("destination_label"),
            "net_total": result.header.get("net_total"),
            "tax_total": result.header.get("tax_total"),
            "total": result.header.get("total"),
            "exchange_rate": result.header.get("exchange_rate"),
            "total_volume_m3": result.header.get("total_volume_m3"),
            "detected_profile_code": result.detected_profile_code,
            "sheet_name_used": result.sheet_name_used,
            "line_ids": line_commands,
            "warning_ids": warning_commands,
            "warning_count": len(result.warnings),
            "state": "extracted",
        })

        return self._reload_form_action()

    def _reload_form_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }