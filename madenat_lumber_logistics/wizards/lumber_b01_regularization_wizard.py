# -*- coding: utf-8 -*-
"""Sub-bloque 4A (2026-10-04) — Regularización B-01 (R1, rebaja extemporánea).

Resuelve, de forma trazable, el caso:

    B-01 open + Contenedor pendiente (loaded/sealed) + stock interno disponible
    → rebaja extemporánea R1 (evidencia física real, fecha efectiva = ahora)
    → picking OUT interno → Clientes, lote/volumen preservados
    → auditoría `b01_regularization`.

El asistente **no** cierra la excepción: el cierre open → resolved es una acción
explícita y separada de Gerencia
(`lumber.export.shipment.action_resolve_b01_exception`).

Variante conservadora (la preferida): SÓLO Gerencia puede ejecutar R1; no se
introduce un workflow/modelo de aprobación paralelo. Operaciones/Jefatura pueden
visualizar la situación pero no confirmar.
"""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

GERENCIA_GROUP = 'madenat_lumber_core.group_madenat_gerencia'
B01_WIZ_MIN_REASON = 20


class LumberB01RegularizationWizard(models.TransientModel):
    _name = 'lumber.b01.regularization.wizard'
    _description = 'Regularización B-01'

    shipment_id = fields.Many2one(
        'lumber.export.shipment', string='Embarque', required=True,
        readonly=True, ondelete='cascade')
    original_b01_audit_id = fields.Many2one(
        'madenat.audit.log', string='B-01 original',
        related='shipment_id.b01_exception_audit_id', readonly=True)
    b01_exception_state = fields.Selection(
        related='shipment_id.b01_exception_state',
        string='Estado B-01', readonly=True)
    b01_exception_reason = fields.Text(
        related='shipment_id.b01_exception_reason',
        string='Motivo de la B-01', readonly=True)
    b01_exception_opened_at = fields.Datetime(
        related='shipment_id.b01_exception_opened_at',
        string='Fecha de apertura B-01', readonly=True)
    pending_container_ids = fields.Many2many(
        'lumber.container', string='Contenedores pendientes',
        compute='_compute_pending', readonly=True)
    pending_count = fields.Integer(
        'N° pendientes', compute='_compute_pending')
    selected_container_ids = fields.Many2many(
        'lumber.container', string='Contenedores a regularizar',
        required=True)
    regularization_reason = fields.Text(
        string='Motivo de la regularización', required=True,
        help='Motivo operativo de la rebaja extemporánea (mínimo 20 '
             'caracteres).')
    approval_reason = fields.Text(
        string='Justificación de aprobación (Gerencia)', required=True,
        help='Justificación de la aprobación de Gerencia (mínimo 20 '
             'caracteres).')
    effective_at = fields.Datetime(
        string='Fecha efectiva', default=fields.Datetime.now,
        required=True, readonly=True)
    requested_by_id = fields.Many2one(
        'res.users', string='Solicitado por',
        default=lambda self: self.env.user, readonly=True)

    @api.depends('shipment_id')
    def _compute_pending(self):
        for wiz in self:
            shipment = wiz.shipment_id
            if shipment:
                _rebajados, pendientes = (
                    shipment._classify_departure_containers())
            else:
                pendientes = self.env['lumber.container']
            wiz.pending_container_ids = pendientes
            wiz.pending_count = len(pendientes)

    def _assert_gerencia(self):
        if not self.env.user.has_group(GERENCIA_GROUP):
            raise AccessError(_(
                'La regularización B-01 (R1) sólo puede ejecutarla Gerencia. '
                'Operaciones/Jefatura pueden visualizar la situación, pero no '
                'confirmar.'))

    def action_regularize_rebaja(self):
        """Ejecuta la rebaja extemporánea R1 (NO cierra la excepción B-01)."""
        self.ensure_one()
        # 1) Sólo Gerencia.
        self._assert_gerencia()
        shipment = self.shipment_id
        # 2) Estado B-01 open / Embarque in_transit.
        if not shipment or shipment.state != 'in_transit' \
                or shipment.b01_exception_state != 'open':
            raise UserError(_(
                'La regularización R1 exige un Embarque En Tránsito con '
                'excepción B-01 ABIERTA.'))
        # 3) Recalcular pendientes por evidencia física real.
        _rebajados, pendientes = shipment._classify_departure_containers()
        selected = self.selected_container_ids
        # 4) La selección debe ser un subconjunto real de pendientes.
        if not selected:
            raise UserError(_('Debe seleccionar al menos un Contenedor.'))
        invalid = selected - pendientes
        if invalid:
            raise UserError(_(
                'No se pueden regularizar Contenedores que no son pendientes '
                'elegibles del Embarque %s: %s.') % (
                    shipment.name, ', '.join(invalid.mapped('name'))))
        # 5) Motivo y aprobación suficientes.
        reason = (self.regularization_reason or '').strip()
        approval = (self.approval_reason or '').strip()
        if len(reason) < B01_WIZ_MIN_REASON \
                or len(approval) < B01_WIZ_MIN_REASON:
            raise UserError(_(
                'El motivo de la regularización y la aprobación de Gerencia '
                'son obligatorios y deben tener al menos %d caracteres.'
            ) % B01_WIZ_MIN_REASON)
        # 6) Ejecutar R1 contenedor por contenedor (savepoint por unidad).
        failures = []
        done = self.env['lumber.container']
        for container in selected:
            try:
                container._assert_can_regularize_b01_rebaja(
                    shipment, reason, approval)
            except (UserError, AccessError) as exc:
                failures.append('%s: %s' % (container.name, exc))
                continue
            try:
                with self.env.cr.savepoint():
                    container._rebajar_container()
                    container.invalidate_recordset()
                    if container.state != 'rebajado':
                        raise UserError(_(
                            'La rebaja no dejó el Contenedor en estado '
                            'Rebajado.'))
                    evidence = container.line_ids.filtered(
                        lambda ln: ln.rebaja_state == 'rebajado'
                        and ln.rebaja_picking_id
                        and ln.rebaja_picking_id.state == 'done')
                    if not evidence:
                        raise UserError(_(
                            'La rebaja no generó un picking validado.'))
                done |= container
            except Exception as exc:  # noqa: BLE001 - se informa al usuario
                failures.append('%s: %s' % (container.name, exc))
        if failures:
            raise UserError(_(
                'No se pudo completar la regularización B-01 (se revirtió '
                'todo):\n\n- %s') % '\n- '.join(failures))
        # 7) Recalcular pendientes (evidencia informativa del mensaje).
        _rebajados2, pendientes2 = shipment._classify_departure_containers()
        # 8) Auditoría append-only b01_regularization (NO cierra la excepción).
        shipment._create_b01_regularization_audit(done, reason, approval)
        # 9) Chatter en Embarque y Contenedores.
        for container in done:
            container.message_post(body=_(
                '🩹 <b>Regularización B-01 (R1)</b>: rebaja extemporánea '
                'autorizada por Gerencia (%s). Motivo: %s.'
            ) % (self.env.user.display_name, reason[:180]))
        shipment.message_post(body=_(
            '🩹 <b>Regularización B-01 (R1) ejecutada por Gerencia</b><br/>'
            'Contenedores rebajados físicamente: %s<br/>'
            'Pendientes restantes: %s<br/>'
            'La excepción B-01 NO se cierra automáticamente: confirme «Cerrar '
            'B-01» cuando no queden pendientes.'
        ) % (', '.join(done.mapped('name')) or '—',
             ', '.join(pendientes2.mapped('name')) or 'ninguno'))
        # 10) Recargar.
        return {'type': 'ir.actions.client', 'tag': 'reload'}
