# -*- coding: utf-8 -*-
"""Línea extraída de un documento de ingesta (resultado del motor).

DECISIÓN D2: las líneas solo deben existir pobladas por ``action_extract()``.
Nunca se crean/editan/eliminan a mano; son un snapshot inmutable.
"""
import math
from fractions import Fraction

from odoo import _, api, fields, models
from odoo.exceptions import UserError


# ──────────────────────────────────────────────────────────────────────────
# Formato de fracción imperial (réplica EXACTA de Core, no reinvención)
# ──────────────────────────────────────────────────────────────────────────
# Fuente original: madenat_lumber_core/models/utils_uom.py:103
#   decimal_inch_to_fraction_str(decimal_value)
# Core documenta (cabecera de utils_uom.py) que ese archivo NO debe
# importarse entre addons (rompe el registry de Odoo 18 CE), por lo que se
# replica literalmente aquí citando la fuente, sin modificar el algoritmo.


def _decimal_inch_to_fraction_str(decimal_value):
    """Transforma un decimal en pulgadas (ej. 1.5625) a su representación
    fraccionaria maderera (ej. "1 9/16"). Réplica EXACTA de Core (mismo
    redondeo, mismo denominador máximo 64, misma salida).
    """
    if decimal_value in (None, False, ""):
        return ""
    try:
        val = float(decimal_value)
        if math.isnan(val):
            return ""
        if val <= 0:
            return "0"
        frac = Fraction(val).limit_denominator(64)
        whole = frac.numerator // frac.denominator
        remainder = frac.numerator % frac.denominator
        if remainder == 0:
            return str(whole)
        elif whole == 0:
            return f"{remainder}/{frac.denominator}"
        else:
            return f"{whole} {remainder}/{frac.denominator}"
    except (ValueError, TypeError):
        return str(decimal_value)


class MadenatIngestionDocumentLine(models.Model):
    _name = "madenat.ingestion.document.line"
    _description = "Línea extraída de un documento de ingesta"
    _order = "source_row_number asc"

    document_id = fields.Many2one(
        "madenat.ingestion.document", required=True,
        ondelete="cascade", readonly=True)
    source_row_number = fields.Integer(readonly=True)
    package_no = fields.Char(readonly=True)
    product_code = fields.Char(readonly=True)
    product_name_original = fields.Char(readonly=True)
    thickness_value_raw = fields.Char(readonly=True)
    thickness_unit = fields.Char(readonly=True)
    width_value_raw = fields.Char(readonly=True)
    width_unit = fields.Char(readonly=True)
    length_value_raw = fields.Char(readonly=True)
    length_unit = fields.Char(readonly=True)
    rows = fields.Integer(readonly=True)
    columns = fields.Integer(readonly=True)
    pieces = fields.Integer(readonly=True)
    volume_m3 = fields.Float(readonly=True, digits=(16, 3))
    lot_number = fields.Char(readonly=True)
    has_warning = fields.Boolean(readonly=True, default=False)

    thickness_display = fields.Char(
        string="Esp. (fracción)",
        compute="_compute_display",
        readonly=True,
        help="Representación fraccionaria del espesor declarado (ej. '1 9/16') "
             "cuando la unidad es pulgadas; para métrico muestra el valor crudo."
    )
    width_display = fields.Char(
        string="Ancho (fracción)",
        compute="_compute_display",
        readonly=True,
        help="Representación fraccionaria del ancho declarado (ej. '3 5/8') "
             "cuando la unidad es pulgadas; para métrico muestra el valor crudo."
    )

    @api.depends("thickness_value_raw", "thickness_unit",
                 "width_value_raw", "width_unit")
    def _compute_display(self):
        """Muestra el valor documental como fracción imperial (pulgadas) o crudo
        (métrico), replicando el criterio del extractor antiguo (Core)."""
        for rec in self:
            if rec.thickness_unit == "inch":
                rec.thickness_display = _decimal_inch_to_fraction_str(
                    rec.thickness_value_raw
                )
            else:
                rec.thickness_display = rec.thickness_value_raw

            if rec.width_unit == "inch":
                rec.width_display = _decimal_inch_to_fraction_str(
                    rec.width_value_raw
                )
            else:
                rec.width_display = rec.width_value_raw

    def _is_locked(self):
        # Las líneas son siempre inmutables; solo action_extract() las crea.
        self.ensure_one()
        return True

    def write(self, vals):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "Esta línea pertenece a un documento de ingesta ya "
                        "procesado y no puede modificarse. Cargue un documento "
                        "nuevo si necesita corregir algo."
                    ))
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("force_ingestion_write"):
            for rec in self:
                if rec._is_locked():
                    raise UserError(_(
                        "No se puede eliminar una línea de un documento de "
                        "ingesta ya procesado. Es un registro inmutable."
                    ))
        return super().unlink()
