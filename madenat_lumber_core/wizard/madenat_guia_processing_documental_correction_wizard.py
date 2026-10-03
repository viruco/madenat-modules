# -*- coding: utf-8 -*-
"""Asistente CDP-V1 — Corrección Documental Preservada.

Solo campos documentales; NO cambia estado, stock, lotes, pickings,
movimientos, retornos ni costos. Motivo obligatorio (trazabilidad, no
aprobación). Advertencias no bloqueantes. El ejecutor real es privado en la
guía (`_cdp_apply_documental_correction`) y exige este asistente como
confirmación.
"""
from odoo import api, fields, models, _


class MadenatGuiaProcessingDocumentalCorrectionWizard(models.TransientModel):
    _name = 'madenat.guia.processing.documental.correction.wizard'
    _description = 'Asistente: corrección documental preservada (CDP-V1)'

    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía', required=True,
        readonly=True,
        default=lambda self: self.env.context.get(
            'default_guia_processing_id'))

    state_name = fields.Char(
        string='Estado actual', compute='_compute_context_info')
    physical_history_text = fields.Text(
        string='Historia física (no se modifica)',
        compute='_compute_context_info')
    warning_text = fields.Text(
        string='Advertencias (no bloquean)',
        compute='_compute_context_info')

    # ── Campos documentales (lista blanca CDP-V1) ───────────────────────
    notes = fields.Text(string='Notas')
    date_emission = fields.Date(string='Fecha de Emisión')
    oc_reference_raw = fields.Char(string='OC Documental')
    carrier_id = fields.Many2one(
        'res.partner', string='Transportista',
        domain=[('is_company', '=', True)])
    assignment_location_id = fields.Many2one(
        'stock.location', string='Patio de Asignación',
        domain=[('usage', '=', 'internal')])
    packing_volume_declared_m3 = fields.Float(
        string='Vol. Packing declarado (m³)', digits=(16, 3))
    packing_pieces_declared = fields.Integer(
        string='Piezas Packing declaradas')
    packing_package_count_declared = fields.Integer(
        string='Paquetes Packing declarados')
    vol_comercial_pdf = fields.Float(
        string='Vol. Guía PDF (m³)', digits=(16, 3))
    total_paquetes = fields.Integer(string='Total Paquetes')
    total_lotes_unicos = fields.Integer(string='Total Lotes')

    # ── Nueva versión de adjuntos (preserva la anterior, sin unlink) ────
    new_pdf_file = fields.Binary(string='Nuevo PDF de Guía')
    new_pdf_filename = fields.Char(string='Nombre nuevo PDF')
    new_excel_file = fields.Binary(string='Nuevo Excel de Packing')
    new_excel_filename = fields.Char(string='Nombre nuevo Excel')

    reason = fields.Text(string='Motivo de la corrección', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        guia_id = self.env.context.get('default_guia_processing_id')
        guia = self.env['madenat.guia.processing'].browse(guia_id) \
            if guia_id else self.env['madenat.guia.processing']
        if guia.exists():
            for name in guia.CDP_DOCUMENTAL_WHITELIST:
                field = self._fields.get(name)
                if not field:
                    continue
                value = guia[name]
                res[name] = (value.id or False) \
                    if field.type == 'many2one' else value
        return res

    @api.depends('guia_processing_id')
    def _compute_context_info(self):
        for wiz in self:
            guia = wiz.guia_processing_id
            if not guia:
                wiz.state_name = False
                wiz.physical_history_text = False
                wiz.warning_text = False
                continue
            wiz.state_name = dict(
                guia._fields['state'].selection).get(guia.state, guia.state)
            warnings = guia._cdp_physical_history_warnings()
            wiz.physical_history_text = '\n'.join(
                '• %s' % w for w in warnings) or False
            wiz.warning_text = _(
                'Las advertencias NO bloquean. La corrección es solo '
                'documental: no cambia estado, stock, lotes, pickings, '
                'movimientos, retornos ni costos. El motivo es obligatorio '
                '(trazabilidad, no aprobación).')

    def action_confirm(self):
        """Confirma la corrección documental (delega en el ejecutor privado)."""
        self.ensure_one()
        return self.guia_processing_id._cdp_apply_documental_correction(self)
