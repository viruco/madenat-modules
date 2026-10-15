# -*- coding: utf-8 -*-
"""AD-88 / B-01 — Asistente de zarpe con contenedores pendientes de rebaja.

El zarpe ya no descuenta stock (AD-82). Cuando hay contenedores sin rebajar,
`lumber.export.shipment.action_set_in_transit` abre este asistente, que ofrece:

* **Rebajar y zarpar** → rebaja los pendientes (savepoint por contenedor) y zarpa.
* **Zarpar con excepción** → exige motivo, registra la desviación (AD-88) y zarpa.

No bloquea al profesional (D8); toda excepción queda auditada.
"""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


# Sub-bloque 3 (2026-10-04): grupos del flujo de zarpe.
# Abrir/visualizar el flujo: Operaciones/Jefatura/Gerencia.
# Confirmar el zarpe (normal o B-01): Jefatura/Gerencia.
ZARPE_OPEN_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
ZARPE_CONFIRM_GROUPS = (
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
ZARPE_B01_MIN_REASON = 20


class LumberShipmentZarpeWizard(models.TransientModel):
    _name = 'lumber.shipment.zarpe.wizard'
    _description = 'Zarpe con contenedores pendientes de rebaja (B-01)'

    shipment_id = fields.Many2one(
        'lumber.export.shipment', string='Embarque', required=True,
        ondelete='cascade')
    pending_container_ids = fields.Many2many(
        'lumber.container', string='Contenedores pendientes',
        compute='_compute_pending')
    pending_count = fields.Integer(
        'N° pendientes', compute='_compute_pending')
    pending_names = fields.Char(
        'Contenedores sin rebajar', compute='_compute_pending')
    reason = fields.Text(
        string='Motivo de la excepción',
        help='Obligatorio para zarpar sin rebajar (excepción registrada).')

    def _check_open_group(self):
        if not any(self.env.user.has_group(g) for g in ZARPE_OPEN_GROUPS):
            raise AccessError(_(
                'No tiene permisos para operar el zarpe. Se requiere el rol de '
                'Operaciones, Jefatura de Operaciones o Gerencia.'))

    def _check_confirm_group(self):
        if not any(self.env.user.has_group(g) for g in ZARPE_CONFIRM_GROUPS):
            raise AccessError(_(
                'No tiene permisos para confirmar el zarpe. Se requiere el rol '
                'de Jefatura de Operaciones o Gerencia.'))

    @api.depends('shipment_id')
    def _compute_pending(self):
        for wiz in self:
            pending = wiz.shipment_id.container_ids.filtered(
                lambda c: not wiz.shipment_id._is_container_rebajado_fisico(c))
            wiz.pending_container_ids = pending
            wiz.pending_count = len(pending)
            wiz.pending_names = ', '.join(pending.mapped('name'))

    def action_rebajar_y_zarpar(self):
        """Rebaja cada contenedor pendiente (savepoint) y luego zarpa."""
        self.ensure_one()
        self._check_confirm_group()
        failures = []
        for container in self.pending_container_ids:
            try:
                with self.env.cr.savepoint():
                    # action_rebajar() impone los permisos por rol (AD-86).
                    container.action_rebajar()
                if container.state != 'rebajado':
                    failures.append(container.name)
            except Exception as exc:  # noqa: BLE001 - se informa al usuario
                failures.append('%s: %s' % (container.name, exc))
        if failures:
            raise UserError(_(
                'No se pudo rebajar todos los contenedores antes del zarpe:'
                '\n\n- %s\n\nCorrija y reintente, o use «Zarpar con excepción».'
            ) % '\n- '.join(failures))
        self.shipment_id._set_in_transit()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zarpe confirmado'),
                'message': _('Contenedores rebajados y nave rematada.'),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_zarpar_con_excepcion(self):
        """Zarpe con excepción DOCUMENTAL B-01 (motivo obligatorio >= 20)."""
        self.ensure_one()
        self._check_confirm_group()
        reason = (self.reason or '').strip()
        if len(reason) < ZARPE_B01_MIN_REASON:
            raise UserError(_(
                'Debe indicar un motivo de al menos %d caracteres para zarpar '
                'con contenedores sin rebajar (excepción B-01).'
            ) % ZARPE_B01_MIN_REASON)
        self.shipment_id._set_in_transit(
            exception_reason=reason, is_b01=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zarpe confirmado con excepción'),
                'message': _('Excepción registrada y nave rematada.'),
                'type': 'warning',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
