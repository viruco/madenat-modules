# -*- coding: utf-8 -*-
"""AD-92 (2026-10-05) — Rolleo CENTRADO EN EMBARQUE (reprogramación de salida
marítima).

La unidad de negocio del rolleo es EXACTAMENTE un `lumber.export.shipment`.
El asistente recibe `shipment_id` obligatorio; la Motonave y el Viaje de origen
se DERIVAN del Embarque y se muestran sólo lectura. Se escriben
EXCLUSIVAMENTE:

    shipment.vessel_id
    shipment.voyage_id

No mueve inventario ni toca stock/lotes/quants/pickings/moves, costos,
facturas, pagos ni documentos. Modo `strict`: si el Embarque o CUALQUIERA de
sus Contenedores está bloqueado, la operación se aborta sin escribir nada.

Antecedentes y decisión:
- Fase C (2026-10-04) centraba el asistente en `shipping.vessel` y reasignaba
  EN MASA todos los Embarques planificables de la Motonave (y, opcionalmente,
  de un Viaje). Una Motonave es un maestro histórico reutilizable: NO es un
  conjunto seguro de cargas afectadas.
- AD-92 acota el alcance a un único Embarque explícito. Otros Embarques de la
  misma Motonave/Viaje no se leen como candidatos y no se modifican.

Decisiones vinculantes:
- `destination_voyage_id` (opcional) debe pertenecer a la Motonave destino y
  no estar `cancel`; si se indica, el Embarque lo recibe; si no, queda sin
  Viaje (`voyage_id = False`).
- Se conserva `booking_reference` y el estado del Embarque.
- Se registra un pendiente documental NO bloqueante (reutiliza
  `lumber.shipment.document`, sin crear tipos maestros).
"""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

import hashlib
import json
import logging

_logger = logging.getLogger(__name__)


# Grupos autorizados a ejecutar el rolleo de Motonave (contrato único con
# `lumber.container._assert_rollover_eligible`). Auditoría queda fuera.
ROLLEO_VESSEL_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)

# Sólo Embarques en planificación (planificable) son rolleables.
ROLLEO_ELIGIBLE_SHIPMENT_STATES = ('draft', 'confirmed')

# Estados de embarque legibles para los motivos de bloqueo.
SHIPMENT_STATE_LABELS = {
    'draft': 'Borrador',
    'confirmed': 'Confirmado',
    'in_transit': 'Embarcado',
    'delivered': 'Entregado',
    'cancelled': 'Cancelado',
}

# Sólo Contenedores consolidados (sin rebaja) son elegibles.
ROLLEO_ALLOWED_CONTAINER_STATES = ('loading', 'loaded', 'sealed')

CONTAINER_STATE_LABELS = {
    'empty': 'Vacío',
    'loading': 'Cargando',
    'loaded': 'Cargado',
    'sealed': 'Sellado',
    'rebajado': 'Rebajado',
    'shipped': 'Embarcado',
}

# Nombre canónico del pendiente documental NO bloqueante que deja el rolleo.
# Reutiliza `lumber.shipment.document` (no crea tipos maestros/reglas/migración).
ROLLEO_BACKLOG_DOC_NAME = 'Revisión documental por Rollover de Embarque'


class LumberVesselRolloverWizard(models.TransientModel):
    _name = 'lumber.vessel.rollover.wizard'
    _description = 'Rolleo de Embarque (planificación marítima)'

    # ══════════════════════════════════════════════════════════════════════
    # Campos
    # ══════════════════════════════════════════════════════════════════════
    # ── Unidad de negocio del rolleo: EXACTAMENTE un Embarque ────────────
    # Punto de entrada: `lumber.export.shipment.action_open_shipment_rollover_wizard`.
    shipment_id = fields.Many2one(
        'lumber.export.shipment',
        string='Embarque',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('default_shipment_id'),
    )
    # Motonave/Viaje de origen DERIVADOS del Embarque (sólo lectura). No son un
    # alcance: son la planificación marítima actual del Embarque seleccionado.
    origin_vessel_id = fields.Many2one(
        'shipping.vessel',
        string='Motonave Origen',
        related='shipment_id.vessel_id',
        readonly=True,
    )
    origin_voyage_id = fields.Many2one(
        'shipping.voyage',
        string='Viaje Origen',
        related='shipment_id.voyage_id',
        readonly=True,
    )
    destination_vessel_id = fields.Many2one(
        'shipping.vessel',
        string='Motonave Destino',
        required=True,
    )
    destination_voyage_id = fields.Many2one(
        'shipping.voyage',
        string='Viaje Destino',
        domain="[('vessel_id', '=', destination_vessel_id)]",
        help='Opcional. Si se indica, debe pertenecer a la Motonave destino y '
             'no estar cancelado. Si se omite, el Embarque queda sin Viaje.',
    )
    motive = fields.Selection(
        [
            ('overbooking', 'Sobreventa Naviera (Overbooking)'),
            ('technical', 'Falla Técnica de la Motonave'),
            ('customs', 'Revisión o Retención Aduanera'),
            ('commercial', 'Cambio Comercial del Cliente'),
            ('logistics', 'Problema Logístico Interno'),
            ('other', 'Otro Motivo'),
        ],
        string='Motivo del Rolleo',
        required=True,
    )
    other_motive = fields.Char(string='Especifique Otro Motivo')
    note = fields.Text(
        string='Observación',
        required=True,
        help='Describa el contexto del cambio de planificación (obligatorio).',
    )

    shipment_ids = fields.Many2many(
        'lumber.export.shipment',
        'lumber_vessel_rollover_shipment_rel', 'wizard_id', 'shipment_id',
        string='Embarques a reasignar',
        readonly=True,
    )
    blocked_shipment_ids = fields.Many2many(
        'lumber.export.shipment',
        'lumber_vessel_rollover_blocked_shipment_rel', 'wizard_id',
        'shipment_id',
        string='Embarques bloqueados',
        readonly=True,
    )
    container_ids = fields.Many2many(
        'lumber.container',
        'lumber_vessel_rollover_container_rel', 'wizard_id', 'container_id',
        string='Contenedores a reasignar',
        readonly=True,
    )
    blocked_container_ids = fields.Many2many(
        'lumber.container',
        'lumber_vessel_rollover_blocked_container_rel', 'wizard_id',
        'container_id',
        string='Contenedores bloqueados',
        readonly=True,
    )
    block_summary = fields.Text(string='Detalle de bloqueos', readonly=True)

    # Contadores expuestos en la UI (derivados de las listas anteriores).
    shipment_count = fields.Integer(
        string='Embarques rolleables', compute='_compute_counts')
    blocked_shipment_count = fields.Integer(
        string='N° Embarques bloqueados', compute='_compute_counts')
    container_count = fields.Integer(
        string='Contenedores rolleables', compute='_compute_counts')
    blocked_container_count = fields.Integer(
        string='N° Contenedores bloqueados', compute='_compute_counts')

    # ══════════════════════════════════════════════════════════════════════
    # Permisos (contrato operativo único, revalidado en servidor)
    # ══════════════════════════════════════════════════════════════════════
    def _check_group(self):
        if not any(self.env.user.has_group(g) for g in ROLLEO_VESSEL_GROUPS):
            raise AccessError(_(
                'El rolleo de motonave requiere el rol de Operaciones, '
                'Jefatura de Operaciones o Gerencia.'))

    # ══════════════════════════════════════════════════════════════════════
    # Ciclo de vida
    # ══════════════════════════════════════════════════════════════════════
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('shipment_id'):
                vals['shipment_id'] = self.env.context.get(
                    'default_shipment_id')
        wizards = super().create(vals_list)
        wizards._check_group()
        wizards._recompute_preview()
        return wizards

    @api.depends('shipment_ids', 'blocked_shipment_ids',
                 'container_ids', 'blocked_container_ids')
    def _compute_counts(self):
        for wiz in self:
            wiz.shipment_count = len(wiz.shipment_ids)
            wiz.blocked_shipment_count = len(wiz.blocked_shipment_ids)
            wiz.container_count = len(wiz.container_ids)
            wiz.blocked_container_count = len(wiz.blocked_container_ids)

    @api.onchange('destination_vessel_id')
    def _onchange_destination_vessel(self):
        # Un Viaje sólo puede pertenecer a la Motonave destino elegida.
        if (self.destination_voyage_id
                and self.destination_voyage_id.vessel_id
                != self.destination_vessel_id):
            self.destination_voyage_id = False

    # ══════════════════════════════════════════════════════════════════════
    # Selección y clasificación (fuente de verdad en servidor)
    # ══════════════════════════════════════════════════════════════════════
    def _scope_shipments(self):
        """Alcance: EXACTAMENTE el Embarque seleccionado (unidad de negocio).

        El rolleo ya NO se define por Motonave/Viaje (AD-92). Un Embarque
        explícito es la única unidad afectada: otros Embarques de la misma
        Motonave/Viaje no se leen, no se bloquean y no se modifican.
        """
        self.ensure_one()
        return self.shipment_id

    def _container_block_reason(self, container):
        """Motivo legible si el Contenedor NO es elegible; '' si lo es."""
        if container.state in ('rebajado', 'shipped'):
            return _('Contenedor %s con rebaja física o ya embarcado (estado %s).') % (
                container.name,
                CONTAINER_STATE_LABELS.get(container.state, container.state))
        for line in container.line_ids:
            if line.rebaja_state == 'rebajado':
                return _('Contenedor %s con línea rebajada (lote %s).') % (
                    container.name, line.lot_id.name or line.lot_id.id)
            if line.rebaja_picking_id and line.rebaja_picking_id.state == 'done':
                return _('Contenedor %s con picking de rebaja %s validado.') % (
                    container.name, line.rebaja_picking_id.name)
        if container.state not in ROLLEO_ALLOWED_CONTAINER_STATES:
            return _('Contenedor %s en estado no rolleable (%s).') % (
                container.name,
                CONTAINER_STATE_LABELS.get(container.state, container.state))
        return ''

    def _classify(self):
        """Clasifica el alcance en rolleables/bloqueados con motivo legible.

        Regla `strict`: si un Embarque tiene al menos un Contenedor no elegible,
        o su estado no es planificable, o tiene costos distribuidos (B-07), se
        bloquea el Embarque COMPLETO.
        """
        self.ensure_one()
        eligible_shipments = self.env['lumber.export.shipment']
        blocked_shipments = self.env['lumber.export.shipment']
        eligible_containers = self.env['lumber.container']
        blocked_containers = self.env['lumber.container']
        summary = []

        for shipment in self._scope_shipments():
            shipment_label = shipment.name or ('ID %s' % shipment.id)
            shipment_reasons = []
            if shipment.state not in ROLLEO_ELIGIBLE_SHIPMENT_STATES:
                shipment_reasons.append(
                    _('estado no rolleable (%s)') % SHIPMENT_STATE_LABELS.get(
                        shipment.state, shipment.state))
            if shipment.cost_distribution_state == 'distributed':
                shipment_reasons.append(_('costos distribuidos (B-07)'))

            blocked_by_container = self.env['lumber.container']
            for container in shipment.container_ids:
                if self._container_block_reason(container):
                    blocked_by_container |= container

            if shipment_reasons or blocked_by_container:
                blocked_shipments |= shipment
                blocked_containers |= shipment.container_ids  # bloqueo total
                for reason in shipment_reasons:
                    summary.append(_('Embarque %s: %s.') % (
                        shipment_label, reason))
                for container in blocked_by_container:
                    summary.append(_('Embarque %s / Contenedor %s: %s') % (
                        shipment_label, container.name,
                        self._container_block_reason(container)))
            else:
                eligible_shipments |= shipment
                eligible_containers |= shipment.container_ids

        return {
            'eligible_shipments': eligible_shipments,
            'blocked_shipments': blocked_shipments,
            'eligible_containers': eligible_containers,
            'blocked_containers': blocked_containers,
            'summary_lines': summary,
        }

    def _recompute_preview(self):
        """Recalcula la previsualización y la persiste en el asistente."""
        self.ensure_one()
        self._check_group()
        data = self._classify()
        self.write({
            'shipment_ids': [(6, 0, data['eligible_shipments'].ids)],
            'blocked_shipment_ids': [(6, 0, data['blocked_shipments'].ids)],
            'container_ids': [(6, 0, data['eligible_containers'].ids)],
            'blocked_container_ids': [(6, 0, data['blocked_containers'].ids)],
            'block_summary': '\n'.join(data['summary_lines']),
        })

    def action_refresh_preview(self):
        """Botón «Actualizar previsualización» (revalida grupo y recalcula)."""
        self.ensure_one()
        self._recompute_preview()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rollover / Cambiar Planificación Marítima'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ══════════════════════════════════════════════════════════════════════
    # Validación de destino (servidor, modo `strict`)
    # ══════════════════════════════════════════════════════════════════════
    def _validate_destination(self):
        """Valida el destino en servidor y devuelve (vessel, voyage)."""
        self.ensure_one()
        if not self.destination_vessel_id:
            raise UserError(_('Debe indicar la Motonave destino.'))
        if self.destination_vessel_id == self.origin_vessel_id:
            raise UserError(_(
                'La Motonave destino debe ser distinta de la Motonave origen.'))
        voyage = self.destination_voyage_id
        if voyage:
            if voyage.vessel_id != self.destination_vessel_id:
                raise UserError(_(
                    'El Viaje destino %s no pertenece a la Motonave destino %s.'
                ) % (voyage.name, self.destination_vessel_id.name))
            if voyage.state == 'cancel':
                raise UserError(_(
                    'El Viaje destino %s está cancelado y no puede usarse.'
                ) % voyage.name)
        return self.destination_vessel_id, voyage

    def action_confirm_rollover(self):
        """Ejecuta el rolleo `strict` en una única transacción."""
        self.ensure_one()
        self._check_group()

        if not self.motive:
            raise UserError(_('Debe indicar el motivo del rolleo.'))
        if self.motive == 'other' and not (self.other_motive or '').strip():
            raise UserError(_(
                "Debe especificar el motivo cuando selecciona 'Otro Motivo'."))
        if not (self.note or '').strip():
            raise UserError(_('Debe registrar una observación del rolleo.'))

        destination_vessel, destination_voyage = self._validate_destination()

        # Recalcular elegibilidad en servidor (nunca confiar en la UI).
        data = self._classify()
        blocked_shipments = data['blocked_shipments']
        blocked_containers = data['blocked_containers']
        if blocked_shipments or blocked_containers:
            raise UserError(_(
                'Rolleo abortado: la operación es total y existe al menos un '
                'Embarque o Contenedor bloqueado.\n\n%s'
            ) % '\n'.join(data['summary_lines']))

        eligible_shipments = data['eligible_shipments']
        eligible_containers = data['eligible_containers']
        if not eligible_shipments:
            raise UserError(_(
                'El Embarque %s no es rolleable en su estado actual.'
            ) % (self.shipment_id.name or self.shipment_id.id))

        origin_vessel = self.origin_vessel_id
        origin_voyage = self.origin_voyage_id
        actor = self.env.user
        now = fields.Datetime.now()
        state_before_shipment = {s.id: s.state for s in eligible_shipments}
        state_before_container = {c.id: c.state for c in eligible_containers}

        # ── Reasignación: SÓLO vessel_id y voyage_id ──────────────────────
        for shipment in eligible_shipments:
            shipment.write({
                'vessel_id': destination_vessel.id,
                'voyage_id': destination_voyage.id or False,
            })
        eligible_shipments.invalidate_recordset()

        motive_label = dict(
            self._fields['motive'].selection).get(self.motive, self.motive)
        if self.motive == 'other' and self.other_motive:
            motive_label = '%s: %s' % (motive_label, self.other_motive)
        batch_id = 'VESSEL-ROLLOVER-%s' % now.strftime('%Y%m%d%H%M%S%f')

        self._create_audit(
            origin_vessel, origin_voyage, destination_vessel,
            destination_voyage, eligible_shipments, eligible_containers,
            state_before_shipment, state_before_container, motive_label,
            actor, now, batch_id)
        self._post_chatter(
            origin_vessel, origin_voyage, destination_vessel,
            destination_voyage, eligible_shipments, eligible_containers,
            motive_label, actor, now)
        # Backlog documental NO bloqueante (reutiliza `lumber.shipment.document`).
        self._ensure_documentary_backlog(
            eligible_shipments, origin_vessel, origin_voyage,
            destination_vessel, destination_voyage, motive_label, actor, now)

        return self._rollover_result_action(
            origin_vessel, destination_vessel, eligible_shipments,
            eligible_containers)

    # ══════════════════════════════════════════════════════════════════════
    # Auditoría (maestra + por elemento) — misma transacción
    # ══════════════════════════════════════════════════════════════════════
    def _audit_create(self, action_type, description, batch_id, payload):
        snapshot = json.dumps(payload, sort_keys=True, default=str)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': action_type,
            'description': description,
            'batch_id': batch_id,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _create_audit(
            self, origin_vessel, origin_voyage, destination_vessel,
            destination_voyage, shipments, containers, state_before_shipment,
            state_before_container, motive_label, actor, now, batch_id):
        self.ensure_one()

        origin_block = {
            'vessel_id': origin_vessel.id,
            'vessel_name': origin_vessel.name,
            'voyage_id': origin_voyage.id or False,
            'voyage_name': origin_voyage.name or False,
        }
        destination_block = {
            'vessel_id': destination_vessel.id,
            'vessel_name': destination_vessel.name,
            'voyage_id': destination_voyage.id or False,
            'voyage_name': destination_voyage.name or False,
        }
        items = {
            'shipments': [
                {'id': s.id, 'name': s.name or ('ID %s' % s.id)}
                for s in shipments],
            'containers': [
                {'id': c.id, 'name': c.name} for c in containers],
        }
        master_payload = {
            'operation': {
                'type': 'vessel_rollover',
                'timestamp': now.isoformat(),
                'user_id': actor.id,
                'user_name': actor.name,
                'motive': self.motive,
                'other_motive': self.other_motive or '',
                'note': self.note or '',
            },
            'origin': origin_block,
            'destination': destination_block,
            'summary': {
                'shipments_total': len(shipments),
                'shipments_reassigned': len(shipments),
                'containers_total': len(containers),
                'containers_reassigned': len(containers),
                'shipments_blocked': 0,
                'containers_blocked': 0,
            },
            'items': items,
        }
        self._audit_create(
            'vessel_rollover',
            _('Rolleo Motonave %s → %s') % (
                origin_vessel.name, destination_vessel.name),
            batch_id, master_payload)

        # Un evento por Embarque reasignado.
        for shipment in shipments:
            self._audit_create(
                'vessel_rollover_item',
                _('Rolleo · Embarque %s reasignado a %s') % (
                    shipment.name or ('ID %s' % shipment.id),
                    destination_vessel.name),
                batch_id,
                {
                    'action_type': 'vessel_rollover_item',
                    'batch': batch_id,
                    'record_type': 'shipment',
                    'record_id': shipment.id,
                    'record_name': shipment.name or ('ID %s' % shipment.id),
                    'status': 'reassigned',
                    'origin': dict(
                        origin_block,
                        shipment_id=shipment.id,
                        shipment_name=shipment.name or ('ID %s' % shipment.id)),
                    'destination': dict(
                        destination_block,
                        shipment_id=shipment.id,
                        shipment_name=shipment.name or ('ID %s' % shipment.id)),
                    'state_before': state_before_shipment.get(shipment.id),
                    'state_after': shipment.state,
                    'timestamp': now.isoformat(),
                    'actor': {'user_id': actor.id, 'user_name': actor.name},
                })

        # Un evento por Contenedor incluido (derivado de su Embarque).
        for container in containers:
            self._audit_create(
                'vessel_rollover_item',
                _('Rolleo · Contenedor %s (Embarque %s) reasignado a %s') % (
                    container.name,
                    container.shipment_id.name or container.shipment_id.id,
                    destination_vessel.name),
                batch_id,
                {
                    'action_type': 'vessel_rollover_item',
                    'batch': batch_id,
                    'record_type': 'container',
                    'record_id': container.id,
                    'record_name': container.name,
                    'status': 'reassigned',
                    'origin': dict(
                        origin_block,
                        shipment_id=container.shipment_id.id or False,
                        shipment_name=container.shipment_id.name or False),
                    'destination': dict(
                        destination_block,
                        shipment_id=container.shipment_id.id or False,
                        shipment_name=container.shipment_id.name or False),
                    'state_before': state_before_container.get(container.id),
                    'state_after': container.state,
                    'timestamp': now.isoformat(),
                    'actor': {'user_id': actor.id, 'user_name': actor.name},
                })

    # ══════════════════════════════════════════════════════════════════════
    # Chatter (complementario a la auditoría)
    # ══════════════════════════════════════════════════════════════════════
    def _post_chatter(
            self, origin_vessel, origin_voyage, destination_vessel,
            destination_voyage, shipments, containers, motive_label, actor,
            now):
        self.ensure_one()
        stamp = now.strftime('%Y-%m-%d %H:%M')
        shipment_names = ', '.join(
            s.name or ('ID %s' % s.id) for s in shipments) or '-'

        # Motonave origen: resumen de rolleo (salida).
        origin_vessel.message_post(body=(
            "<div style='border-left:4px solid #ff9800; padding:8px;'>"
            "<b>🔄 Rolleo de planificación (origen)</b><br/>"
            "Motonave destino: <b>%s</b><br/>"
            "Viaje destino: %s<br/>"
            "Embarques reasignados (%d): %s<br/>"
            "Contenedores: %d<br/>"
            "Motivo: %s<br/>"
            "<small>Usuario: %s · %s</small></div>"
        ) % (
            destination_vessel.name,
            destination_voyage.name if destination_voyage else '—',
            len(shipments), shipment_names, len(containers), motive_label,
            actor.name, stamp), subject=_('Rollover de Embarque'))

        # Motonave destino: resumen de recepción.
        destination_vessel.message_post(body=(
            "<div style='border-left:4px solid #28a745; padding:8px;'>"
            "<b>🔄 Recepción de planificación (destino)</b><br/>"
            "Motonave origen: <b>%s</b><br/>"
            "Viaje asignado: %s<br/>"
            "Embarques recibidos (%d): %s<br/>"
            "Contenedores: %d<br/>"
            "Motivo: %s<br/>"
            "<small>Usuario: %s · %s</small></div>"
        ) % (
            origin_vessel.name,
            destination_voyage.name if destination_voyage else '—',
            len(shipments), shipment_names, len(containers), motive_label,
            actor.name, stamp), subject=_('Rollover de Embarque'))

        # Viajes (sólo cuando existan).
        if origin_voyage:
            origin_voyage.message_post(body=_(
                "🔄 Rolleo: %d Embarque(s) salen de este Viaje hacia %s."
            ) % (len(shipments), destination_vessel.name))
        if destination_voyage:
            destination_voyage.message_post(body=_(
                "🔄 Rolleo: %d Embarque(s) ingresan a este Viaje desde %s."
            ) % (len(shipments), origin_vessel.name))

        # Cada Embarque reasignado.
        for shipment in shipments:
            shipment.message_post(body=(
                "<b>🔄 Rolleo de planificación marítima</b><br/>"
                "Origen: %s / %s → Destino: %s / %s<br/>"
                "Motivo: %s<br/>"
                "<small>Usuario: %s · %s</small>"
            ) % (
                origin_vessel.name,
                origin_voyage.name if origin_voyage else '—',
                destination_vessel.name,
                destination_voyage.name if destination_voyage else '—',
                motive_label, actor.name, stamp),
                subject=_('Rollover de Embarque'))

        # Cada Contenedor incluido (cambio derivado de su Embarque).
        for container in containers:
            container.message_post(body=_(
                "🔄 Rolleo derivado de su Embarque %s: Motonave %s → %s."
            ) % (
                container.shipment_id.name or container.shipment_id.id,
                origin_vessel.name, destination_vessel.name),
                subject=_('Rollover de Embarque'))

    # ══════════════════════════════════════════════════════════════════════
    # Backlog documental (NO bloqueante) — reutiliza `lumber.shipment.document`
    # ══════════════════════════════════════════════════════════════════════
    def _ensure_documentary_backlog(
            self, shipments, origin_vessel, origin_voyage,
            destination_vessel, destination_voyage, motive_label, actor, now):
        """Registra una tarea documental NO bloqueante por el Rolleo.

        Reutiliza el modelo existente `lumber.shipment.document` SIN crear
        tipos maestros, modelos, reglas ni migraciones. Actualiza el pendiente
        abierto homónimo si ya existe; en caso contrario lo crea. La tarea NO
        afecta al estado físico, stock, costos ni a la elegibilidad del
        Embarque (además, sin `checklist_id`, no entra en el cómputo de
        documentos obligatorios de `document_status`). Cualquier fallo del
        backlog se aísla con savepoint y NUNCA revierte el rolleo.
        """
        self.ensure_one()
        shipment_names = ', '.join(
            s.name or ('ID %s' % s.id) for s in shipments) or '-'
        detail = _(
            'Rolleo de Embarque: %(o)s.\n'
            'Motonave/Viaje origen: %(ov)s / %(ovg)s.\n'
            'Motonave/Viaje destino: %(dv)s / %(dvg)s.\n'
            'Motivo: %(m)s.\n'
            'Operador: %(u)s · %(t)s.\n'
            'Revisar: Booking, Shipping Instructions (SI), VGM, B/L o Sea '
            'Waybill, ETD/ETA e información a cliente/forwarder si aplica.'
        ) % {
            'o': shipment_names,
            'ov': origin_vessel.name or '—',
            'ovg': origin_voyage.name or '—',
            'dv': destination_vessel.name,
            'dvg': destination_voyage.name if destination_voyage else '—',
            'm': motive_label,
            'u': actor.name,
            't': now.strftime('%Y-%m-%d %H:%M'),
        }
        Document = self.env['lumber.shipment.document']
        for shipment in shipments:
            try:
                with self.env.cr.savepoint():
                    pending = shipment.document_ids.filtered(
                        lambda d: d.name == ROLLEO_BACKLOG_DOC_NAME
                        and d.backlog_state in ('open', 'in_progress'))
                    if pending:
                        pending[0].write({'backlog_note': detail})
                    else:
                        Document.create({
                            'shipment_id': shipment.id,
                            'name': ROLLEO_BACKLOG_DOC_NAME,
                            'backlog_note': detail,
                            'backlog_state': 'open',
                            'criticality': 'medium',
                        })
            except Exception as error:  # pragma: no cover — defensivo
                _logger.warning(
                    'No se pudo registrar el backlog documental del Rolleo del '
                    'Embarque %s: %s', shipment.name or shipment.id, error)

    def _rollover_result_action(
            self, origin_vessel, destination_vessel, shipments, containers):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Rolleo de Embarque completado'),
                'message': _(
                    '%(s)d Embarque(s) y %(c)d Contenedor(es) reasignados '
                    '%(o)s → %(d)s.') % {
                    's': len(shipments), 'c': len(containers),
                    'o': origin_vessel.name, 'd': destination_vessel.name,
                },
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
