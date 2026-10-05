# -*- coding: utf-8 -*-
import hashlib
import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# AD-100 (2026-10-05) — BACKLOG DOCUMENTAL NO BLOQUEANTE Y AUDITADO
# Gestiona trabajo pendiente documental. NO es gate físico ni financiero, NO
# cambia B2, NO bloquea D2 y NO toca stock/B-01/R1/R2/R4/Costeo/Finanzas/SV.
# ════════════════════════════════════════════════════════════════════════════
# Roles server-side (XML IDs reales de `madenat_lumber_core`).
BACKLOG_OPERATIONS_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
)
BACKLOG_ESCALATE_GROUPS = (
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
BACKLOG_CLOSE_GROUPS = (
    'madenat_lumber_core.group_madenat_gerencia',
)
# Motivo mínimo de exoneración (medido tras `strip()`).
BACKLOG_WAIVE_MIN_REASON = 20
# Campos de workflow reservados a las acciones autorizadas (nunca write directo).
BACKLOG_WORKFLOW_FIELDS = frozenset({
    'backlog_state',
    'escalated_at',
    'escalated_by_id',
})
# Tokens efímeros de PROCESO (set en memoria; NO un context RPC y no eludibles
# por `with_context(...)`). Clave: (dbname, uid, document_id). Se añaden justo
# antes de cada write de workflow y se consumen (`discard`) en `finally`.
_BACKLOG_ESCALATE_TOKENS = set()
_BACKLOG_CLOSE_TOKENS = set()
_BACKLOG_WAIVE_TOKENS = set()


class LumberDocumentChecklist(models.Model):
    _name = 'lumber.document.checklist'
    _description = 'Checklist Documental de Exportación'
    _order = 'sequence, id'

    name = fields.Char('Nombre Documento', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    is_required = fields.Boolean('Obligatorio', default=True)
    description = fields.Text('Instrucciones')
    active = fields.Boolean('Activo', default=True)


class LumberShipmentDocument(models.Model):
    _name = 'lumber.shipment.document'
    _description = 'Documento de Embarque'
    # AD-100: chatter del backlog documental. `mail` ya es dependencia del
    # módulo; el mixin se añade al modelo existente (columnas ADITIVAS, sin
    # migración de datos). El chatter se publica SÓLO en transiciones reales.
    _inherit = ['mail.thread', 'mail.activity.mixin']

    shipment_id = fields.Many2one('lumber.export.shipment', string='Embarque', ondelete='cascade')
    checklist_id = fields.Many2one('lumber.document.checklist', string='Tipo Documento')
    
    # Campo nombre autocompletado si está vacío, pero editable
    name = fields.Char('Referencia/Nombre', compute='_compute_name', store=True, readonly=False, required=True)
    
    file_data = fields.Binary('Archivo')
    file_name = fields.Char('Nombre Archivo')
    
    state = fields.Selection([
        ('missing', 'Pendiente'),
        ('attached', 'Adjunto'),
        ('verified', 'Verificado')
    ], string='Estado', default='missing', index=True, compute='_compute_state', store=True, readonly=False)
    
    notes = fields.Text('Notas Adicionales')

    # ── Backlog documental (NO bloqueante) ────────────────────────────────
    # La documentación tardía genera pendiente + advertencia + responsable +
    # fecha objetivo + escalamiento. NUNCA lanza UserError ni bloquea la
    # operación física (rebaja/zarpe/B-01/R1/R2/Entrega).
    criticality = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Criticidad', default='medium', index=True)
    responsible_id = fields.Many2one(
        'res.users', string='Responsable', index=True)
    due_date = fields.Date('Fecha Objetivo')
    backlog_state = fields.Selection([
        ('open', 'Abierto'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('waived', 'Exonerado'),
    ], string='Estado Backlog', default='open', index=True)
    backlog_note = fields.Text('Nota de Backlog')
    escalated_at = fields.Datetime('Escalado el', readonly=True, copy=False)
    escalated_by_id = fields.Many2one(
        'res.users', string='Escalado por', readonly=True, copy=False)

    backlog_overdue = fields.Boolean(
        string='Vencido', compute='_compute_backlog_flags')
    backlog_attention = fields.Boolean(
        string='Requiere Atención', compute='_compute_backlog_flags')

    @api.depends('checklist_id')
    def _compute_name(self):
        for doc in self:
            if not doc.name and doc.checklist_id:
                doc.name = doc.checklist_id.name
            elif not doc.name:
                doc.name = 'Documento Nuevo'

    @api.depends('file_data')
    def _compute_state(self):
        for doc in self:
            # Lógica robusta: Si suben archivo -> Adjunto. Si lo borran -> Pendiente.
            # Respeta el estado 'verified' si ya fue verificado manualmente.
            if doc.file_data:
                if doc.state != 'verified':
                    doc.state = 'attached'
            else:
                doc.state = 'missing'

    @api.onchange('file_data')
    def _onchange_file_data(self):
        # Mejora UX: Feedback inmediato en interfaz antes de guardar
        if self.file_data:
            self.state = 'attached'

    @api.depends('due_date', 'backlog_state', 'criticality')
    def _compute_backlog_flags(self):
        today = fields.Date.context_today(self)
        for doc in self:
            open_backlog = doc.backlog_state in ('open', 'in_progress')
            doc.backlog_overdue = bool(
                open_backlog and doc.due_date and doc.due_date < today)
            doc.backlog_attention = bool(
                open_backlog and (
                    doc.backlog_overdue
                    or doc.criticality in ('high', 'critical')))

    # ── AD-100 · Puerta lateral de escritura (write directo) ────────────────
    # Nota de diseño: el superusuario (env.su, código interno/tests) mantiene la
    # vía de escape estándar de Odoo (patrón MADENAT); la protección con token
    # aplica a TODO actor RPC/real (su=False) y NO es eludible por
    # `with_context(...)` porque el token es un set en memoria del proceso.
    def write(self, vals):
        if any(f in vals for f in BACKLOG_WORKFLOW_FIELDS):
            self._assert_backlog_workflow_write_authorized()
        return super().write(vals)

    def _assert_backlog_workflow_write_authorized(self):
        """Bloquea el write directo de los campos de workflow del backlog."""
        for rec in self:
            if rec.env.su:
                continue
            key = (rec.env.cr.dbname, rec.env.uid, rec.id)
            if (key in _BACKLOG_ESCALATE_TOKENS
                    or key in _BACKLOG_CLOSE_TOKENS
                    or key in _BACKLOG_WAIVE_TOKENS):
                _BACKLOG_ESCALATE_TOKENS.discard(key)
                _BACKLOG_CLOSE_TOKENS.discard(key)
                _BACKLOG_WAIVE_TOKENS.discard(key)
                continue
            raise UserError(_(
                'El estado del backlog documental del documento %s sólo puede '
                'cambiarse mediante las acciones autorizadas «Escalar», '
                '«Cerrar» o «Exonerar».') % (rec.name or rec.id))

    # ── AD-100 · Autorización server-side por rol ───────────────────────────
    def _assert_backlog_operations_group(self):
        if self.env.su:
            return
        if not any(
                self.env.user.has_group(g) for g in BACKLOG_OPERATIONS_GROUPS):
            raise AccessError(_(
                'No tiene permisos para gestionar el backlog documental. Se '
                'requiere el rol de Operaciones.'))

    def _assert_backlog_escalate_group(self):
        if self.env.su:
            return
        if not any(
                self.env.user.has_group(g) for g in BACKLOG_ESCALATE_GROUPS):
            raise AccessError(_(
                'No tiene permisos para escalar el backlog documental. Se '
                'requiere el rol de Jefatura de Operaciones o Gerencia.'))

    def _assert_backlog_close_group(self):
        if self.env.su:
            return
        if not any(self.env.user.has_group(g) for g in BACKLOG_CLOSE_GROUPS):
            raise AccessError(_(
                'No tiene permisos para cerrar o exonerar el backlog '
                'documental. Se requiere el rol de Gerencia.'))

    # ── AD-100 · Workflow: escalar / cerrar / exonerar ──────────────────────
    def action_backlog_escalate(self):
        """Escalamiento del backlog documental (Jefatura de Operaciones o
        Gerencia). Workflow NO bloqueante:

        * ``completed``/``waived`` → no-op (sin auditoría ni chatter).
        * ``in_progress``          → no-op estricto (no reescribe ``escalated_*``).
        * ``open``                 → ``in_progress`` + sello ``escalated_at``/``by``.

        No toca el estado documental, el Embarque, B2, D2, stock ni finanzas.
        """
        self._assert_backlog_escalate_group()
        now = fields.Datetime.now()
        for doc in self:
            if doc.backlog_state in ('completed', 'waived', 'in_progress'):
                continue
            key = (doc.env.cr.dbname, doc.env.uid, doc.id)
            with doc.env.cr.savepoint():
                doc._create_backlog_audit(
                    'escalation', state_before='open',
                    state_after='in_progress', reason=None,
                    escalated_at=now, escalated_by_id=doc.env.user.id)
                _BACKLOG_ESCALATE_TOKENS.add(key)
                try:
                    doc.write({
                        'backlog_state': 'in_progress',
                        'escalated_at': now,
                        'escalated_by_id': doc.env.user.id,
                    })
                finally:
                    _BACKLOG_ESCALATE_TOKENS.discard(key)
            doc._backlog_message_post('escalation')
        return True

    def action_backlog_complete(self):
        """Cierre del backlog documental (Gerencia).

        * ``completed``/``waived`` → no-op (sin auditoría ni chatter).
        * ``open``/``in_progress`` → ``completed``.

        NO modifica el ``state`` documental: backlog cerrado y evidencia
        documental son dimensiones distintas.
        """
        self._assert_backlog_close_group()
        for doc in self:
            if doc.backlog_state in ('completed', 'waived'):
                continue
            key = (doc.env.cr.dbname, doc.env.uid, doc.id)
            with doc.env.cr.savepoint():
                doc._create_backlog_audit(
                    'completion', state_before=doc.backlog_state,
                    state_after='completed', reason=None)
                _BACKLOG_CLOSE_TOKENS.add(key)
                try:
                    doc.write({'backlog_state': 'completed'})
                finally:
                    _BACKLOG_CLOSE_TOKENS.discard(key)
            doc._backlog_message_post('completion')
        return True

    def action_backlog_waive(self, reason=False):
        """Exoneración del backlog documental (Gerencia).

        Motivo obligatorio (>= ``BACKLOG_WAIVE_MIN_REASON`` tras ``strip()``):
        si no se pasa ``reason`` se usa ``self.backlog_note`` (regla de UI).
        ``waived`` es no-op idempotente; ``completed`` eleva ``UserError`` (no
        se reabre ni exonera un backlog cerrado). La nota previa se CONSERVA y
        el motivo se anexa de forma trazable, sin destruir texto previo.
        """
        self._assert_backlog_close_group()
        now = fields.Datetime.now()
        for doc in self:
            if doc.backlog_state == 'waived':
                continue
            if doc.backlog_state == 'completed':
                raise UserError(_(
                    'No se puede exonerar el documento %s: su backlog '
                    'documental ya está completado.') % (doc.name or doc.id))
            reason_text = (reason or doc.backlog_note or '').strip()
            if len(reason_text) < BACKLOG_WAIVE_MIN_REASON:
                raise UserError(_(
                    'El motivo de exoneración del documento %s debe tener al '
                    'menos %s caracteres (complete la nota de backlog).') % (
                        doc.name or doc.id, BACKLOG_WAIVE_MIN_REASON))
            new_note = doc._build_backlog_waiver_note(reason_text, now)
            key = (doc.env.cr.dbname, doc.env.uid, doc.id)
            with doc.env.cr.savepoint():
                doc._create_backlog_audit(
                    'waiver', state_before=doc.backlog_state,
                    state_after='waived', reason=reason_text)
                _BACKLOG_WAIVE_TOKENS.add(key)
                try:
                    doc.write({
                        'backlog_state': 'waived',
                        'backlog_note': new_note,
                    })
                finally:
                    _BACKLOG_WAIVE_TOKENS.discard(key)
            doc._backlog_message_post('waiver', reason=reason_text)
        return True

    def _build_backlog_waiver_note(self, reason_text, now):
        """Conserva la nota previa y anexa el motivo de exoneración de forma
        trazable (sin duplicar el motivo si ya estaba en la nota)."""
        self.ensure_one()
        existing = (self.backlog_note or '').strip()
        marker = _('— Exonerado el %(t)s por %(u)s —') % {
            't': now.strftime('%Y-%m-%d %H:%M:%S'),
            'u': self.env.user.name,
        }
        parts = []
        if existing:
            parts.append(existing)
        if reason_text and reason_text not in existing:
            parts.append(reason_text)
        parts.append(marker)
        return '\n'.join(parts)

    # ── AD-100 · Evidencia: snapshot SHA-256 + auditoría + chatter ──────────
    def _backlog_snapshot(self, action, state_before, state_after,
                          reason=None, escalated_at=None,
                          escalated_by_id=None):
        """Snapshot determinista (JSON-able) del evento de backlog documental.

        Incluye la lectura B2 (`shipment.document_status`) SÓLO como evidencia;
        nunca escribe el estado documental ni del Embarque.
        """
        self.ensure_one()
        shipment = self.shipment_id
        return {
            'operation': {
                'action_type': 'documentary_backlog_%s' % action,
                'action': action,
                'timestamp': fields.Datetime.now().strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                'actor': {'id': self.env.user.id, 'name': self.env.user.name},
                'reason': reason or False,
            },
            'document': {
                'document_id': self.id,
                'document_name': self.name or False,
                'shipment_id': shipment.id or False,
                'checklist_id': self.checklist_id.id or False,
                'state': self.state,
                'criticality': self.criticality,
                'responsible_id': self.responsible_id.id or False,
                'due_date': (
                    self.due_date.isoformat() if self.due_date else False),
                'backlog_state_before': state_before,
                'backlog_state_after': state_after,
                'escalated_at': (
                    escalated_at.isoformat() if escalated_at
                    else (self.escalated_at.isoformat()
                          if self.escalated_at else False)),
                'escalated_by_id': (
                    escalated_by_id or (self.escalated_by_id.id or False)),
            },
            'shipment': {
                'shipment_id': shipment.id or False,
                'shipment_name': shipment.name or False,
                'document_status': shipment.document_status or False,
            },
        }

    def _create_backlog_audit(self, action, state_before, state_after,
                              reason=None, escalated_at=None,
                              escalated_by_id=None):
        """Crea el evento append-only (SHA-256) del backlog documental.

        SÓLO el alta de `madenat.audit.log` usa `sudo()` (patrón MADENAT); el
        resto del flujo respeta los permisos del usuario real. `batch_id`
        identifica el documento con el prefijo `doc:`.
        """
        self.ensure_one()
        snapshot = json.dumps(
            self._backlog_snapshot(
                action, state_before, state_after, reason=reason,
                escalated_at=escalated_at, escalated_by_id=escalated_by_id),
            sort_keys=True, default=str)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': 'documentary_backlog_%s' % action,
            'description': _('Backlog documental · %(a)s · %(d)s') % {
                'a': action, 'd': self.name or self.id},
            'batch_id': 'doc:%s' % self.id,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _backlog_message_post(self, action, reason=None):
        """Publica el chatter del backlog SI `message_post` está disponible.

        Nunca se publica chatter en un no-op idempotente (los `action_*` no
        llaman a este helper cuando no hay transición real).
        """
        self.ensure_one()
        if not hasattr(self, 'message_post'):
            return
        actor_name = self.env.user.name
        if action == 'escalation':
            body = self.env._('Backlog documental escalado por %s.') % actor_name
        elif action == 'completion':
            body = self.env._('Backlog documental cerrado por %s.') % actor_name
        elif action == 'waiver':
            body = self.env._(
                'Backlog documental exonerado por %s. Motivo: %s.') % (
                    actor_name, reason)
        else:
            return
        self.message_post(body=body)


class LumberExportShipment(models.Model):
    _inherit = 'lumber.export.shipment'

    document_ids = fields.One2many('lumber.shipment.document', 'shipment_id', string='Documentos')

    @api.depends('document_ids.state',
                 'document_ids.checklist_id.is_required',
                 'document_ids.checklist_id.active')
    def _compute_document_status(self):
        """Fuente ÚNICA de la semántica documental (B2).

        Sólo se consideran documentos cuyo checklist esté ACTIVO. El universo
        (`target`) son los documentos requeridos activos; si no existe ninguno
        requerido, todos los documentos activos.

        Valores deterministas de `document_status`:
          not_configured · missing · pending · partial · attached · verified
        Indicador INFORMATIVO: nunca es gate de operación física. No usa los
        valores legacy `complete`/`incomplete`.
        """
        for shipment in self:
            active_docs = shipment.document_ids.filtered(
                lambda d: d.checklist_id.active)
            required = active_docs.filtered(
                lambda d: d.checklist_id.is_required)
            target = required if required else active_docs
            total = len(target)
            verified = len(target.filtered(lambda d: d.state == 'verified'))
            attached = len(target.filtered(lambda d: d.state == 'attached'))
            missing = len(target.filtered(lambda d: d.state == 'missing'))

            shipment.document_verified_count = verified
            shipment.document_missing_count = missing
            shipment.document_pending_count = total - verified
            shipment.document_completion = (
                ((verified + attached) / total) * 100.0) if total else 0.0

            if total == 0:
                shipment.document_status = 'not_configured'
            elif verified == total:
                shipment.document_status = 'verified'
            elif verified > 0:
                shipment.document_status = 'partial'
            elif attached == total:
                shipment.document_status = 'attached'
            elif attached > 0:
                shipment.document_status = 'pending'
            else:
                shipment.document_status = 'missing'

    @api.model_create_multi
    def create(self, vals_list):
        # Auto-generación de checklist al crear el embarque
        shipments = super(LumberExportShipment, self).create(vals_list)
        for shipment in shipments:
            # Buscar configuración activa
            checklists = self.env['lumber.document.checklist'].search([('active', '=', True)])
            if checklists:
                docs_vals = []
                for check in checklists:
                    docs_vals.append({
                        'shipment_id': shipment.id,
                        'checklist_id': check.id,
                        'name': check.name,
                        'state': 'missing'
                    })
                self.env['lumber.shipment.document'].create(docs_vals)
        return shipments
