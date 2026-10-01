# -*- coding: utf-8 -*-
"""Asistentes de Etiquetas SV — flujo común de envío/aprobación.

Convención MADENAT: TransientModel con motivo obligatorio y aplicación
atómica delegada en `madenat.sv.operation` (ledger append-only).
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MadenatSvWizardMixin(models.AbstractModel):
    """Comportamiento común de los asistentes de etiqueta SV."""

    _name = 'madenat.sv.wizard.mixin'
    _description = 'Mixin de asistentes de etiqueta SV'

    def _sv_submit_operation(self, operation_vals):
        """Crea la operación, la aplica o la deja pendiente de aprobación."""
        self.ensure_one()
        operation_model = self.env['madenat.sv.operation']
        # El intento (alta + aplicación) queda aislado: ante un conflicto de
        # concurrencia se revierte completo y se entrega el mensaje funcional.
        with operation_model._sv_concurrency_guard():
            operation = operation_model.create(operation_vals)
            operation._sv_validate_payload()
            pending = operation._sv_pending_approval_groups()
            if not pending or pending <= operation._sv_user_groups():
                operation.action_apply()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'title': _('Operación SV aplicada'),
                        'message': '%s · %s' % (
                            operation.name, operation.lot_id.name or ''),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    },
                }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'title': _('Requiere aprobación funcional'),
                'message': _(
                    'La operación %s quedó en borrador pendiente de aprobación '
                    '(%s).'
                ) % (operation.name, ', '.join(sorted(pending))),
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class MadenatSvRenameWizard(models.TransientModel):
    """Modificar etiqueta SV (solo identificador, con alias histórico)."""

    _name = 'madenat.sv.rename.wizard'
    _inherit = ['madenat.sv.wizard.mixin']
    _description = 'Asistente: modificar etiqueta SV'

    lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', required=True, readonly=True,
        default=lambda self: self.env.context.get('default_lot_id'))
    current_label = fields.Char(
        string='Etiqueta actual', compute='_compute_current_label')
    new_label = fields.Char(
        string='Nueva etiqueta SV', required=True,
        help='Formato obligatorio: SV seguido de 11 dígitos.')
    reason = fields.Text(string='Motivo', required=True)
    sv_available_m3 = fields.Float(
        string='Saldo disponible SV (m³)', digits=(16, 3),
        related='lot_id.sv_available_m3', readonly=True)
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía Origen', readonly=True,
        related='lot_id.volume_source_guia_id')

    @api.depends('lot_id')
    def _compute_current_label(self):
        for wizard in self:
            wizard.current_label = wizard.lot_id.name or ''

    def action_submit(self):
        self.ensure_one()
        return self._sv_submit_operation({
            'lot_id': self.lot_id.id,
            'action_type': 'rename',
            'new_label': self.new_label,
            'reason': self.reason,
            'guia_processing_id': self.lot_id.volume_source_guia_id.id or False,
        })


class MadenatSvVolumeRegularizeWizard(models.TransientModel):
    """Regularizar volumen documental/operativo de una etiqueta SV."""

    _name = 'madenat.sv.volume.regularize.wizard'
    _inherit = ['madenat.sv.wizard.mixin']
    _description = 'Asistente: regularizar volumen de etiqueta SV'

    lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', required=True, readonly=True,
        default=lambda self: self.env.context.get('default_lot_id'))
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía Origen', readonly=True,
        related='lot_id.volume_source_guia_id')
    current_baseline_m3 = fields.Float(
        string='Baseline vigente (m³)', digits=(16, 3),
        related='lot_id.sv_regularized_baseline_m3', readonly=True)
    current_rebajado_m3 = fields.Float(
        string='Rebajado activo (m³)', digits=(16, 3),
        related='lot_id.sv_rebajado_m3', readonly=True)
    current_available_m3 = fields.Float(
        string='Saldo disponible (m³)', digits=(16, 3),
        related='lot_id.sv_available_m3', readonly=True)
    documentary_volume_m3 = fields.Float(
        string='Volumen oficial de la Guía (m³)', digits=(16, 3),
        related='lot_id.sv_documentary_volume_m3', readonly=True)
    documentary_warning = fields.Boolean(
        string='Aviso documental', related='lot_id.sv_documentary_warning')
    new_volume_m3 = fields.Float(
        string='Nuevo volumen regularizado (m³)', digits=(16, 3), required=True)
    difference_m3 = fields.Float(
        string='Diferencia (m³)', digits=(16, 3),
        compute='_compute_difference_m3')
    reason = fields.Text(string='Motivo', required=True)
    evidence_attachment_id = fields.Many2one(
        'ir.attachment', string='Evidencia documental',
        help='Obligatoria: la regularización exige respaldo documental.')
    evidence_reference = fields.Char(
        string='Referencia de respaldo',
        help='Alternativa al adjunto (folio, guía, correo, etc.).')
    requires_auditoria = fields.Boolean(
        string='Requiere Auditoría', compute='_compute_escalation')
    requires_contabilidad = fields.Boolean(
        string='Requiere Contabilidad', compute='_compute_escalation')

    @api.depends('new_volume_m3', 'current_baseline_m3')
    def _compute_difference_m3(self):
        for wizard in self:
            wizard.difference_m3 = (
                (wizard.new_volume_m3 or 0.0)
                - (wizard.current_baseline_m3 or 0.0))

    @api.depends('lot_id', 'new_volume_m3')
    def _compute_escalation(self):
        for wizard in self:
            required = set()
            if wizard.lot_id:
                preview = self.env['madenat.sv.operation'].new({
                    'lot_id': wizard.lot_id.id,
                    'action_type': 'regularize_volume',
                    'new_volume_m3': wizard.new_volume_m3 or 0.0,
                    'company_id': wizard.lot_id.company_id.id,
                })
                required = preview._sv_required_approval_groups()
            wizard.requires_auditoria = 'auditoria' in required
            wizard.requires_contabilidad = 'contabilidad' in required

    def action_submit(self):
        self.ensure_one()
        return self._sv_submit_operation({
            'lot_id': self.lot_id.id,
            'action_type': 'regularize_volume',
            'prior_volume_m3': self.current_baseline_m3 or 0.0,
            'new_volume_m3': self.new_volume_m3,
            'reason': self.reason,
            'evidence_attachment_id': self.evidence_attachment_id.id or False,
            'evidence_reference': self.evidence_reference or False,
        })


class MadenatSvRebajaWizard(models.TransientModel):
    """Rebajar saldo de una etiqueta SV (volumen y piezas documentales)."""

    _name = 'madenat.sv.rebaja.wizard'
    _inherit = ['madenat.sv.wizard.mixin']
    _description = 'Asistente: rebajar etiqueta SV'

    lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', required=True, readonly=True,
        default=lambda self: self.env.context.get('default_lot_id'))
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía Origen', readonly=True,
        related='lot_id.volume_source_guia_id')
    current_label = fields.Char(
        string='Etiqueta actual', compute='_compute_current_label')
    available_volume_m3 = fields.Float(
        string='Saldo disponible (m³)', digits=(16, 3),
        related='lot_id.sv_available_m3', readonly=True)
    available_pieces = fields.Integer(
        string='Saldo disponible de piezas',
        related='lot_id.sv_available_pieces', readonly=True)
    pieces_enabled = fields.Boolean(
        string='Saldo de piezas habilitado',
        related='lot_id.sv_pieces_enabled', readonly=True,
        help='Solo se habilita cuando la Guía declara piezas documentales '
             'positivas. Nunca por paquetes, líneas PDF ni piezas=1 técnico.')
    rebaja_volume_m3 = fields.Float(
        string='Volumen a rebajar (m³)', digits=(16, 3), required=True)
    rebaja_pieces = fields.Integer(
        string='Piezas a rebajar',
        help='Opcional; solo disponible con saldo de piezas documentales.')
    reason = fields.Text(string='Motivo', required=True)
    destination_reference = fields.Char(
        string='Destino / referencia',
        help='Destino operativo (proceso, embarque, contenedor, etc.).')

    @api.depends('lot_id')
    def _compute_current_label(self):
        for wizard in self:
            wizard.current_label = wizard.lot_id.name or ''

    def action_submit(self):
        self.ensure_one()
        if self.rebaja_pieces and not self.pieces_enabled:
            raise ValidationError(_(
                'La etiqueta %s no tiene saldo de piezas documentales '
                'habilitado.') % (self.lot_id.name or ''))
        return self._sv_submit_operation({
            'lot_id': self.lot_id.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': self.rebaja_volume_m3,
            'rebaja_pieces': self.rebaja_pieces if self.pieces_enabled else 0,
            'reason': self.reason,
            'destination_reference': self.destination_reference or False,
        })


class MadenatSvRebajaReverseWizard(models.TransientModel):
    """Reversar una rebaja SV creando el evento opuesto (nunca se borra)."""

    _name = 'madenat.sv.rebaja.reverse.wizard'
    _inherit = ['madenat.sv.wizard.mixin']
    _description = 'Asistente: reversar rebaja de etiqueta SV'

    origin_operation_id = fields.Many2one(
        'madenat.sv.operation', string='Rebaja original', required=True,
        readonly=True,
        default=lambda self: self.env.context.get('default_origin_operation_id'))
    lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', readonly=True,
        related='origin_operation_id.lot_id')
    rebaja_volume_m3 = fields.Float(
        string='Volumen a restituir (m³)', digits=(16, 3),
        related='origin_operation_id.rebaja_volume_m3', readonly=True)
    rebaja_pieces = fields.Integer(
        string='Piezas a restituir',
        related='origin_operation_id.rebaja_pieces', readonly=True)
    destination_reference = fields.Char(
        string='Destino original',
        related='origin_operation_id.destination_reference', readonly=True)
    reason = fields.Text(string='Motivo de la reversa', required=True)

    def action_submit(self):
        self.ensure_one()
        return self._sv_submit_operation({
            'lot_id': self.origin_operation_id.lot_id.id,
            'action_type': 'rebaja_reverse',
            'origin_operation_id': self.origin_operation_id.id,
            'rebaja_volume_m3': self.origin_operation_id.rebaja_volume_m3,
            'rebaja_pieces': self.origin_operation_id.rebaja_pieces,
            'reason': self.reason,
            'destination_reference': (
                self.origin_operation_id.destination_reference or False),
        })
