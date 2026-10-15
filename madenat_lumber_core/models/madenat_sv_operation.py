# -*- coding: utf-8 -*-
"""Gestión operativa de Etiquetas SV — ledger transaccional append-only.

Modelo `madenat.sv.operation`: historia persistente de las operaciones sobre
Etiquetas SV del Ingreso por Volúmenes.

Reglas de negocio (aprobadas):
- `m³` es obligatorio en toda etiqueta SV; el saldo se calcula SIEMPRE como:
      sv_available_volume_m3 = baseline_regularizado - rebajado_activo
- Las piezas solo son balanceables si la Guía declara piezas documentales
  positivas (`piezas_declaradas` o `packing_pieces_declared`). Nunca se usan
  `stock.lot.piezas = 1`, paquetes, líneas PDF ni líneas sintéticas GRANEL.
- La regularización de volumen es DOCUMENTAL/OPERATIVA: no escribe
  `stock.quant`, `stock.move`, `stock.move.line`, `stock.picking`, costos,
  valoración, factura, consolidación ni movimiento físico de inventario.
- Ledger append-only: una operación aplicada no se edita ni se elimina; las
  correcciones son nuevas operaciones y la reversa crea un evento opuesto.
- Concurrencia: toda acción que altere saldo bloquea la fila del `stock.lot`
  (`_lock_sv_lot_for_operation`, SELECT ... FOR UPDATE parametrizado) y
  recalcula el saldo dentro de la misma transacción.
"""

import hashlib
import json
import logging
import re
from contextlib import contextmanager

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
from psycopg2.errors import SerializationFailure

_logger = logging.getLogger(__name__)

# Mensaje funcional aprobado ante conflicto de concurrencia (nunca se expone el
# error técnico PostgreSQL a Operaciones).
SV_CONCURRENCY_MESSAGE = (
    'Otro usuario modificó esta etiqueta SV mientras se procesaba la '
    'operación. La operación no fue aplicada. Actualice la información y '
    'vuelva a intentarlo.')

# Identidad SV: etiqueta global "SV" + 11 dígitos (F3.1).
SV_LABEL_RE = re.compile(r'^SV[0-9]{11}$')



class MadenatSvOperation(models.Model):
    """Operación de Etiqueta SV (ledger append-only)."""

    _name = 'madenat.sv.operation'
    _description = 'Operación de Etiqueta SV (Volumen)'
    _order = 'execution_date desc, id desc'
    _rec_name = 'name'

    # ── Identidad ─────────────────────────────────────────────────────────
    name = fields.Char(
        string='Operación',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: (
            self.env['ir.sequence'].next_by_code('madenat.sv.operation')
            or _('Nueva')
        ),
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Etiqueta SV / Lote',
        required=True,
        ondelete='restrict',
        index=True,
        check_company=True,
    )
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía Origen',
        compute='_compute_guia_processing_id',
        store=True,
        readonly=True,
        index=True,
        ondelete='restrict',
        help='Guía de Ingreso por Volúmenes dueña de la etiqueta SV.',
    )

    # ── Tipo y estado ─────────────────────────────────────────────────────
    action_type = fields.Selection(
        [
            ('rename', 'Modificación de etiqueta SV'),
            ('regularize_volume', 'Regularización de volumen'),
            ('rebaja', 'Rebaja de etiqueta'),
            ('rebaja_reverse', 'Reversa de rebaja'),
        ],
        string='Tipo de operación',
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('applied', 'Aplicada'),
            ('reversed', 'Reversada'),
            ('rejected', 'Rechazada'),
        ],
        string='Estado',
        required=True,
        default='draft',
        index=True,
    )

    # ── Etiqueta ──────────────────────────────────────────────────────────
    prior_label = fields.Char(string='Etiqueta anterior', readonly=True)
    new_label = fields.Char(string='Etiqueta nueva')

    # ── Volumen ───────────────────────────────────────────────────────────
    prior_volume_m3 = fields.Float(
        string='Volumen anterior (m³)', digits=(16, 3))
    new_volume_m3 = fields.Float(
        string='Volumen nuevo (m³)', digits=(16, 3))
    volume_diff_m3 = fields.Float(
        string='Diferencia de volumen (m³)',
        digits=(16, 3),
        compute='_compute_volume_diff_m3',
        store=True,
        readonly=False,
    )

    # ── Piezas (solo si hay piezas documentales positivas) ────────────────
    prior_pieces = fields.Integer(string='Piezas anteriores')
    new_pieces = fields.Integer(string='Piezas nuevas')
    pieces_diff = fields.Integer(
        string='Diferencia de piezas',
        compute='_compute_pieces_diff',
        store=True,
        readonly=False,
    )

    # ── Rebaja ────────────────────────────────────────────────────────────
    rebaja_volume_m3 = fields.Float(
        string='Volumen rebajado (m³)', digits=(16, 3))
    rebaja_pieces = fields.Integer(string='Piezas rebajadas')

    # ── Documentación ─────────────────────────────────────────────────────
    reason = fields.Text(string='Motivo', required=True)
    evidence_attachment_id = fields.Many2one(
        'ir.attachment', string='Evidencia documental')
    evidence_reference = fields.Char(
        string='Referencia de respaldo',
        help='Referencia documental de respaldo (folio, guía, correo, etc.).')

    # ── Destino ───────────────────────────────────────────────────────────
    destination_reference = fields.Char(
        string='Destino / referencia',
        help='Destino operativo cuando no corresponde a embarque/contenedor.')

    # ── Vínculos de trazabilidad ──────────────────────────────────────────
    origin_operation_id = fields.Many2one(
        'madenat.sv.operation',
        string='Operación de origen',
        ondelete='restrict',
        index=True,
        help='Operación original a la que esta operación hace referencia '
             '(reversa de rebaja).',
    )
    reversed_operation_id = fields.Many2one(
        'madenat.sv.operation',
        string='Reversada por',
        ondelete='restrict',
        index=True,
        help='Operación de reversa que anuló esta operación.',
    )

    # ── Usuarios y fechas ─────────────────────────────────────────────────
    requested_by_id = fields.Many2one(
        'res.users', string='Solicitada por',
        default=lambda self: self.env.user)
    executed_by_id = fields.Many2one(
        'res.users', string='Ejecutada por', readonly=True)
    approved_by_id = fields.Many2one(
        'res.users', string='Aprobada por', readonly=True)
    approved_by_id_secondary = fields.Many2one(
        'res.users', string='Segunda aprobación', readonly=True,
        help='Cuando la operación requiere Auditoría y Contabilidad a la vez.')
    execution_date = fields.Datetime(
        string='Fecha de ejecución', readonly=True)

    # ── Evidencia firmada ─────────────────────────────────────────────────
    snapshot_json = fields.Text(string='Snapshot JSON', readonly=True)
    audit_hash = fields.Char(string='Firma SHA-256', readonly=True)

    # ── Restricciones SQL ─────────────────────────────────────────────────
    _sql_constraints = [
        ('sv_operation_rebaja_positive',
         'CHECK(rebaja_volume_m3 >= 0)',
         'El volumen rebajado no puede ser negativo.'),
        ('sv_operation_volumes_positive',
         'CHECK(new_volume_m3 >= 0 AND prior_volume_m3 >= 0)',
         'Los volúmenes de la operación no pueden ser negativos.'),
    ]

    # Campos que pueden escribirse cuando la operación ya está aplicada.
    SV_WRITE_WHITELIST = frozenset([
        'state',
        'approved_by_id',
        'approved_by_id_secondary',
        'reversed_operation_id',
        'snapshot_json',
        'audit_hash',
        'execution_date',
        'executed_by_id',
    ])

    # Transiciones de estado permitidas (append-only).
    SV_ALLOWED_TRANSITIONS = {
        'draft': ('applied', 'rejected'),
        'applied': ('reversed',),
        'reversed': (),
        'rejected': (),
    }

    # ── Computes ──────────────────────────────────────────────────────────
    @api.depends('lot_id', 'lot_id.volume_source_guia_id')
    def _compute_guia_processing_id(self):
        for op in self:
            op.guia_processing_id = op.lot_id.volume_source_guia_id or False

    @api.depends('prior_volume_m3', 'new_volume_m3')
    def _compute_volume_diff_m3(self):
        for op in self:
            op.volume_diff_m3 = (
                (op.new_volume_m3 or 0.0) - (op.prior_volume_m3 or 0.0))

    @api.depends('prior_pieces', 'new_pieces')
    def _compute_pieces_diff(self):
        for op in self:
            op.pieces_diff = (op.new_pieces or 0) - (op.prior_pieces or 0)

    # ── Constraints ───────────────────────────────────────────────────────
    @api.constrains('lot_id')
    def _check_sv_lot(self):
        for op in self:
            if op.lot_id and op.lot_id.lot_flow_type != 'volume':
                raise ValidationError(_(
                    'La operación SV solo aplica a etiquetas SV '
                    '(el lote %s no es de flujo Volumen).'
                ) % (op.lot_id.name or op.lot_id.id))

    @api.constrains('reason')
    def _check_reason(self):
        for op in self:
            if not (op.reason or '').strip():
                raise ValidationError(_(
                    'Toda operación de etiqueta SV exige un motivo.'))

    @api.model
    def _sv_validate_non_negative_vals(self, vals):
        """Valida no-negatividad ANTES del INSERT/UPDATE (mensaje amigable)."""
        if ((vals.get('prior_volume_m3') or 0.0) < 0
                or (vals.get('new_volume_m3') or 0.0) < 0
                or (vals.get('rebaja_volume_m3') or 0.0) < 0):
            raise ValidationError(_(
                'Los volúmenes de la operación SV no pueden ser negativos.'))
        if ((vals.get('prior_pieces') or 0) < 0
                or (vals.get('new_pieces') or 0) < 0
                or (vals.get('rebaja_pieces') or 0) < 0):
            raise ValidationError(_(
                'Las piezas de la operación SV no pueden ser negativas.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Valida valores antes de insertar (el CHECK SQL queda como respaldo)."""
        for vals in vals_list:
            self._sv_validate_non_negative_vals(vals)
        return super().create(vals_list)

    @api.constrains('prior_volume_m3', 'new_volume_m3', 'rebaja_volume_m3',
                    'prior_pieces', 'new_pieces', 'rebaja_pieces')
    def _check_sv_non_negative(self):
        """Validación funcional de no-negatividad (además del CHECK SQL)."""
        for op in self:
            self._sv_validate_non_negative_vals({
                'prior_volume_m3': op.prior_volume_m3,
                'new_volume_m3': op.new_volume_m3,
                'rebaja_volume_m3': op.rebaja_volume_m3,
                'prior_pieces': op.prior_pieces,
                'new_pieces': op.new_pieces,
                'rebaja_pieces': op.rebaja_pieces,
            })

    # ── Append-only ───────────────────────────────────────────────────────
    def write(self, vals):
        """Bloquea ediciones de operaciones ya decididas (append-only)."""
        if not self.env.context.get('madenat_sv_history_write'):
            blocked = set(vals) - self.SV_WRITE_WHITELIST
            if blocked:
                for op in self:
                    if op.state != 'draft':
                        raise ValidationError(_(
                            'La operación %s está en estado "%s" y no puede '
                            'editarse (%s). Registre una nueva operación.'
                        ) % (op.name or op.id,
                             dict(self._fields['state'].selection).get(
                                 op.state, op.state),
                             ', '.join(sorted(blocked))))
        if 'state' in vals:
            for op in self:
                allowed = self.SV_ALLOWED_TRANSITIONS.get(op.state, ())
                if vals['state'] != op.state and vals['state'] not in allowed:
                    raise ValidationError(_(
                        'Transición de estado no permitida en la operación '
                        '%s: %s → %s.'
                    ) % (op.name or op.id, op.state, vals['state']))
        return super().write(vals)

    def unlink(self):
        """La historia aplicada no se elimina (solo borradores)."""
        # Excepción exclusiva de entorno de pruebas con marcador (test-only):
        # permite la limpieza de datos de integración sin abrir un permiso
        # funcional genérico. Aplica a operaciones marcadas o a operaciones de
        # lotes marcados (datos derivados de la misma prueba).
        marker_model = self.env['madenat.sv.internal.marker'].sudo()
        if (marker_model._sv_test_cleanup_allowed(
                'madenat.sv.operation', self.ids)
                or marker_model._sv_test_cleanup_allowed(
                    'stock.lot', self.lot_id.ids)):
            return super().unlink()
        for op in self:
            if op.state != 'draft':
                raise ValidationError(_(
                    'La operación %s ya fue aplicada y no puede eliminarse '
                    'del historial SV.'
                ) % (op.name or op.id))
        return super().unlink()

    # ══════════════════════════════════════════════════════════════════════
    # ESCALAMIENTO CONDICIONAL (Operaciones / Auditoría / Contabilidad)
    # ══════════════════════════════════════════════════════════════════════
    def _sv_required_approval_groups(self):
        """Grupos funcionales exigidos para aplicar la operación.

        Rutinario sin impacto financiero → sin aprobación (autonomía de
        Operaciones). Aumento de baseline documental → Auditoría. Costo,
        valoración, factura, consolidación facturada o período cerrado →
        Contabilidad.
        """
        self.ensure_one()
        required = set()
        lot = self.lot_id
        if self.action_type == 'regularize_volume':
            baseline = lot.sv_regularized_baseline_m3 or 0.0
            if float_compare(
                    self.new_volume_m3 or 0.0, baseline,
                    precision_rounding=SV_VOLUME_PRECISION) > 0:
                required.add('auditoria')
        if lot.cost_line_ids:
            required.add('contabilidad')
        if self._sv_has_valuation():
            required.add('contabilidad')
        if self._sv_consolidation_billed():
            required.add('contabilidad')
        if self._sv_period_closed():
            required.add('contabilidad')
        return required

    def _sv_has_valuation(self):
        self.ensure_one()
        layer = self.env.get('stock.valuation.layer')
        if layer is None or 'lot_id' not in layer._fields:
            return False
        return bool(layer.sudo().search_count(
            [('lot_id', '=', self.lot_id.id)]))

    def _sv_consolidation_billed(self):
        self.ensure_one()
        line = self.env.get('lumber.billing.consolidation.line')
        if line is None:
            return False
        lines = line.sudo().search([('lot_id', '=', self.lot_id.id)])
        return any(
            consolidation.state == 'billed'
            for consolidation in lines.mapped('consolidation_id'))

    def _sv_period_closed(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        lot_date = (self.lot_id.create_date or fields.Datetime.now()).date()
        for lock_field in ('hard_lock_date', 'fiscalyear_lock_date'):
            lock = getattr(company, lock_field, False)
            if lock and lot_date <= lock:
                return True
        return False

    def _sv_approved_groups(self):
        self.ensure_one()
        approved = set()
        for user in (self.approved_by_id | self.approved_by_id_secondary):
            if user.has_group(GROUP_AUDITORIA):
                approved.add('auditoria')
            if user.has_group(GROUP_CONTABILIDAD):
                approved.add('contabilidad')
        return approved

    def _sv_pending_approval_groups(self):
        self.ensure_one()
        return self._sv_required_approval_groups() - self._sv_approved_groups()

    def _sv_user_groups(self):
        """Grupos funcionales de SV del usuario actual."""
        user = self.env.user
        groups = set()
        if user.has_group(GROUP_AUDITORIA):
            groups.add('auditoria')
        if user.has_group(GROUP_CONTABILIDAD):
            groups.add('contabilidad')
        return groups

    def _sv_register_current_approval(self):
        """Registra la aprobación del usuario actual si le corresponde."""
        self.ensure_one()
        pending = self._sv_pending_approval_groups()
        mine = pending & self._sv_user_groups()
        if not mine:
            return set()
        if not self.approved_by_id:
            self.write({'approved_by_id': self.env.user.id})
        else:
            self.write({'approved_by_id_secondary': self.env.user.id})
        return mine

    # ══════════════════════════════════════════════════════════════════════
    # APLICACIÓN ATÓMICA
    # ══════════════════════════════════════════════════════════════════════
    @contextmanager
    def _sv_concurrency_guard(self):
        """Aísla el intento y traduce el conflicto de concurrencia.

        Odoo usa aislamiento REPEATABLE READ: dos operaciones concurrentes sobre
        la misma etiqueta no pueden confirmar ambas. El intento se ejecuta en un
        savepoint; ante el conflicto se revierte el intento completo (sin
        operación, alias, chatter, auditoría, saldo ni sello parciales) y se
        entrega el mensaje funcional aprobado, sin exponer el error técnico de
        PostgreSQL. No hay reintento automático silencioso.
        """
        try:
            with self.env.cr.savepoint():
                yield
        except SerializationFailure as error:
            _logger.warning(
                'Conflicto de concurrencia en operación SV; intento revertido: %s',
                error)
            raise UserError(_(SV_CONCURRENCY_MESSAGE))

    def action_register_approval(self):
        """Registra la aprobación funcional sin aplicar (dos personas)."""
        for op in self:
            if op.state != 'draft':
                raise UserError(_(
                    'La operación %s ya no está en borrador.'
                ) % (op.name or op.id))
            if not op._sv_register_current_approval():
                raise AccessError(_(
                    'Su perfil no corresponde a la aprobación pendiente de la '
                    'operación %s (%s).'
                ) % (op.name or op.id,
                     ', '.join(sorted(op._sv_pending_approval_groups()))))
        return True

    def action_apply(self):
        """Aplicación atómica controlada de la operación SV.

        Orden obligatorio (a→i):
          a. capturar `actor_uid` ANTES de cualquier `sudo()`;
          b. bloquear la operación SV (FOR UPDATE);
          c. bloquear el `stock.lot` SV (FOR UPDATE);
          d. recalcular y validar estado, permisos, aprobaciones y valores;
          e. acuñar la capacidad interna `prepared`;
          f. ejecutar la escritura protegida del lote (la guarda la consume);
          g. consumir/eliminar la capacidad;
          h. aplicar ledger/alias/auditoría/chatter;
          i. confirmar la transacción (lo hace el framework al finalizar).
        """
        for op in self:
            if op.state != 'draft':
                raise UserError(_(
                    'La operación %s ya fue aplicada o rechazada.'
                ) % (op.name or op.id))
            # El intento completo queda aislado y traducido ante concurrencia.
            with self._sv_concurrency_guard():
                self._sv_apply_one(op)
        return True

    def _sv_apply_one(self, op):
        """Aplicación atómica de UNA operación (orden a→i)."""
        op.ensure_one()
        # (a) Identidad funcional original: nunca se sustituye por sudo.
        actor_uid = self.env.uid
        # (b) Bloqueo de la operación del ledger.
        op._sv_lock_operation_for_apply()
        # (c) Bloqueo del lote SV.
        lot = op.lot_id._lock_sv_lot_for_operation()
        # (d) Autorizaciones, estado, aprobaciones y valores.
        op._sv_register_current_approval()
        pending = op._sv_pending_approval_groups()
        if pending:
            raise AccessError(_(
                'La operación %s requiere aprobación funcional pendiente '
                '(%s) antes de aplicarse.'
            ) % (op.name or op.id, ', '.join(sorted(pending))))
        op.check_access('write')
        op._sv_validate_payload()
        balances = lot._sv_locked_balance_values()
        op._sv_validate_against_balances(balances)
        # Sello técnico de serialización generado en esta aplicación.
        stamp = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plan = op._sv_protected_write_plan(stamp=stamp)
        # Valor previo capturado ANTES de la escritura protegida (el rename
        # cambia stock.lot.name en el paso f).
        prior_label = lot.name or False
        # (e) Acuñar capacidad interna (no expuesta, un solo uso).
        capability = self.env['madenat.sv.internal.capability'].sudo()._sv_mint(
            op, actor_uid,
            {'action_type': op.action_type, 'values': plan})
        # (f) Escritura protegida del lote: la guarda consume la capacidad.
        #     `sudo()` se usa EXCLUSIVAMENTE porque `sv_balance_stamp` es un
        #     campo restringido a `base.group_system`: la autorización se
        #     evalúa con la identidad funcional capturada en (a).
        try:
            if plan:
                lot.with_context(
                    madenat_sv_capability=capability.token,
                    madenat_sv_capability_txn=capability.transaction_token,
                ).sudo().write(plan)
        finally:
            # (g) Consumo/limpieza defensiva: nunca queda reutilizable.
            self.env['madenat.sv.internal.capability'].sudo(
                )._sv_discard_for_operation(op)
        # (h) Ledger, alias, auditoría y chatter.
        op._sv_finalize_apply(balances, prior_label=prior_label)
        op._sv_apply_side_effects()
        op._sv_post_chatter(balances)

    def action_reject(self):
        """Rechaza un borrador (no altera saldo ni historia previa)."""
        for op in self:
            if op.state != 'draft':
                raise UserError(_(
                    'Solo se puede rechazar una operación en borrador.'))
            op.write({'state': 'rejected'})
        return True

    # ══════════════════════════════════════════════════════════════════════
    # VALIDACIONES
    # ══════════════════════════════════════════════════════════════════════
    def _sv_validate_payload(self):
        """Validaciones de contenido (independientes del saldo)."""
        self.ensure_one()
        lot = self.lot_id
        if lot.lot_flow_type != 'volume':
            raise ValidationError(_(
                'La operación SV solo aplica a etiquetas SV de Volumen.'))
        if not (self.reason or '').strip():
            raise ValidationError(_(
                'Debe indicar el motivo de la operación de etiqueta SV.'))
        if self.action_type == 'rename':
            label = self._sv_normalize_label(self.new_label)
            if not label:
                raise ValidationError(_('Debe indicar la nueva etiqueta SV.'))
            self._sv_validate_label_format(label)
            if label == (lot.name or ''):
                raise ValidationError(_(
                    'La nueva etiqueta SV es igual a la etiqueta actual.'))
            if self._sv_label_in_use(
                    label, exclude_lot=lot, exclude_operation=self):
                raise ValidationError(_(
                    'La etiqueta %s ya existe o fue usada históricamente por '
                    'otra etiqueta SV. No puede reutilizarse.') % label)
            self.new_label = label
        elif self.action_type == 'regularize_volume':
            if float_compare(
                    self.new_volume_m3 or 0.0, 0.0,
                    precision_rounding=SV_VOLUME_PRECISION) <= 0:
                raise ValidationError(_(
                    'El volumen regularizado debe ser estrictamente positivo.'))
            if not (self.evidence_attachment_id or self.evidence_reference):
                raise ValidationError(_(
                    'La regularización de volumen exige evidencia documental '
                    '(adjunto o referencia de respaldo).'))
        elif self.action_type == 'rebaja':
            if float_compare(
                    self.rebaja_volume_m3 or 0.0, 0.0,
                    precision_rounding=SV_VOLUME_PRECISION) <= 0:
                raise ValidationError(_(
                    'El volumen a rebajar debe ser mayor que cero.'))
            if self.rebaja_pieces:
                if not lot.sv_pieces_enabled:
                    raise ValidationError(_(
                        'La etiqueta %s no tiene saldo de piezas documentales '
                        'habilitado: no se puede rebajar piezas.'
                    ) % (lot.name or lot.id))
                if self.rebaja_pieces < 0:
                    raise ValidationError(_(
                        'Las piezas a rebajar no pueden ser negativas.'))
        elif self.action_type == 'rebaja_reverse':
            origin = self.origin_operation_id
            if not origin:
                raise ValidationError(_(
                    'La reversa debe referenciar la rebaja original.'))
            if origin.action_type != 'rebaja':
                raise ValidationError(_(
                    'Solo se puede reversar una operación de rebaja.'))
            if origin.state != 'applied':
                raise ValidationError(_(
                    'La rebaja %s no está aplicada: no puede reversarse.'
                ) % (origin.name or origin.id))
            if origin.reversed_operation_id:
                raise ValidationError(_(
                    'La rebaja %s ya fue reversada por %s.'
                ) % (origin.name or origin.id,
                     origin.reversed_operation_id.name))

    def _sv_validate_against_balances(self, balances):
        """Validaciones contra el saldo recalculado tras el bloqueo del lote."""
        self.ensure_one()
        available = balances.get('available', 0.0)
        rebajado = balances.get('rebajado', 0.0)
        if self.action_type == 'regularize_volume':
            baseline = self.new_volume_m3 or 0.0
            if float_compare(
                    baseline, rebajado,
                    precision_rounding=SV_VOLUME_PRECISION) < 0:
                raise ValidationError(_(
                    'El nuevo volumen regularizado (%.3f m³) no puede ser '
                    'menor que el volumen ya rebajado (%.3f m³).'
                ) % (baseline, rebajado))
            if float_compare(
                    baseline - rebajado, 0.0,
                    precision_rounding=SV_VOLUME_PRECISION) < 0:
                raise ValidationError(_(
                    'La regularización dejaría saldo SV negativo.'))
        elif self.action_type == 'rebaja':
            amount = self.rebaja_volume_m3 or 0.0
            if float_compare(
                    amount, available,
                    precision_rounding=SV_VOLUME_PRECISION) > 0:
                raise ValidationError(_(
                    'La rebaja de %.3f m³ excede el saldo disponible de la '
                    'etiqueta %s (%.3f m³).'
                ) % (amount, self.lot_id.name or self.lot_id.id, available))
            if float_compare(
                    available - amount, 0.0,
                    precision_rounding=SV_VOLUME_PRECISION) < 0:
                raise ValidationError(_(
                    'La rebaja dejaría un saldo SV negativo.'))
            if self.rebaja_pieces:
                available_pieces = balances.get('available_pieces', 0)
                if self.rebaja_pieces > available_pieces:
                    raise ValidationError(_(
                        'La rebaja de %s piezas excede el saldo documental '
                        'disponible (%s piezas).'
                    ) % (self.rebaja_pieces, available_pieces))

    def _sv_protected_write_plan(self, stamp=None):
        """Campos protegidos del lote que esta operación puede escribir.

        `rename` → `name` con la etiqueta nueva.
        Cualquier tipo → `sv_balance_stamp` (sello técnico de serialización).
        La regularización de volumen NO escribe campos documentales del lote
        (Decisión 1: sin ajuste físico ni de valores históricos).
        """
        self.ensure_one()
        plan = {}
        if self.action_type == 'rename':
            plan['name'] = self.new_label or ''
        if stamp:
            plan['sv_balance_stamp'] = stamp
        return plan

    def _sv_lock_operation_for_apply(self):
        """Bloquea la fila de la operación SV dentro de la transacción actual."""
        self.ensure_one()
        if not self.id:
            raise UserError(_('La operación SV debe existir para aplicarse.'))
        self.flush_recordset()
        self.env.cr.execute(
            'SELECT id FROM madenat_sv_operation WHERE id = %s FOR UPDATE',
            (self.id,))
        if not self.env.cr.fetchone():
            raise UserError(_(
                'La operación SV (id %s) ya no existe.') % self.id)
        self.invalidate_recordset([
            'state', 'action_type', 'new_label', 'new_volume_m3',
            'rebaja_volume_m3', 'rebaja_pieces', 'origin_operation_id',
            'approved_by_id', 'approved_by_id_secondary', 'reversed_operation_id',
        ])
        return self

    def _sv_apply_side_effects(self):
        """Efectos laterales NO protegidos de la operación (paso h).

        La escritura protegida del lote (rename) ya ocurrió en el paso f bajo
        capacidad interna; la regularización de volumen NO toca inventario
        (Decisión 1) y la rebaja solo registra el evento documental.

        La marca técnica `sv_balance_stamp` se actualiza en TODA operación SV
        aplicada: es el punto de serialización del lote bajo el aislamiento
        REPEATABLE READ de Odoo (dos aplicaciones concurrentes no pueden
        confirmar ambas sobre la misma etiqueta).
        """
        self.ensure_one()
        if self.action_type == 'rebaja_reverse':
            origin = self.origin_operation_id
            if origin and origin.state == 'applied':
                origin.write({
                    'state': 'reversed',
                    'reversed_operation_id': self.id,
                })

    def _sv_finalize_apply(self, balances, prior_label=None):
        """Cierra la operación: valores previos, firma hash y estado aplicado."""
        self.ensure_one()
        vals = {
            'state': 'applied',
            'execution_date': fields.Datetime.now(),
            'executed_by_id': self.env.user.id,
        }
        if self.action_type == 'rename':
            vals['prior_label'] = (
                prior_label or self.prior_label or self.lot_id.name)
            vals['new_label'] = self.new_label
        elif self.action_type == 'regularize_volume':
            vals['prior_volume_m3'] = balances.get('baseline', 0.0)
            vals['new_volume_m3'] = self.new_volume_m3
            vals['prior_pieces'] = balances.get('original_pieces', 0)
            vals['new_pieces'] = (
                self.new_pieces or balances.get('original_pieces', 0))
        elif self.action_type == 'rebaja':
            vals['prior_volume_m3'] = balances.get('available', 0.0)
            vals['new_volume_m3'] = (
                balances.get('available', 0.0) - (self.rebaja_volume_m3 or 0.0))
            vals['prior_pieces'] = balances.get('available_pieces', 0)
            vals['new_pieces'] = (
                balances.get('available_pieces', 0) - (self.rebaja_pieces or 0))
        elif self.action_type == 'rebaja_reverse':
            origin = self.origin_operation_id
            vals['rebaja_volume_m3'] = (
                origin.rebaja_volume_m3 if origin else 0.0)
            vals['rebaja_pieces'] = origin.rebaja_pieces if origin else 0
            vals['prior_volume_m3'] = balances.get('available', 0.0)
            vals['new_volume_m3'] = (
                balances.get('available', 0.0) + vals['rebaja_volume_m3'])
            vals['prior_pieces'] = balances.get('available_pieces', 0)
            vals['new_pieces'] = (
                balances.get('available_pieces', 0) + vals['rebaja_pieces'])
        snapshot = self._sv_build_snapshot(balances)
        vals['snapshot_json'] = snapshot
        vals['audit_hash'] = hashlib.sha256(
            snapshot.encode('utf-8')).hexdigest()
        self.write(vals)

    def _sv_build_snapshot(self, balances):
        """Snapshot determinista (convención de madenat.audit.log)."""
        self.ensure_one()
        payload = {
            'lot': self.lot_id.name,
            'lot_id': self.lot_id.id,
            'guia': self.guia_processing_id.name or False,
            'guia_id': self.guia_processing_id.id or False,
            'action_type': self.action_type,
            'prior_label': self.prior_label or '',
            'new_label': self.new_label or '',
            'prior_volume_m3': round(self.prior_volume_m3 or 0.0, 3),
            'new_volume_m3': round(self.new_volume_m3 or 0.0, 3),
            'rebaja_volume_m3': round(self.rebaja_volume_m3 or 0.0, 3),
            'rebaja_pieces': self.rebaja_pieces or 0,
            'balances': {
                key: (round(value, 3) if isinstance(value, float) else value)
                for key, value in (balances or {}).items()
            },
            'user': self.env.user.id,
            'timestamp': fields.Datetime.now().isoformat(),
        }
        return json.dumps(payload, sort_keys=True)

    # ══════════════════════════════════════════════════════════════════════
    # CHATTER Y AUDITORÍA
    # ══════════════════════════════════════════════════════════════════════
    def _sv_chatter_body(self, balances=None):
        self.ensure_one()
        type_label = dict(
            self._fields['action_type'].selection).get(self.action_type)
        lines = [
            '<b>%s</b> · %s' % (type_label, self.name or ''),
            'Etiqueta: <b>%s</b>' % (self.lot_id.name or ''),
        ]
        if self.action_type == 'rename':
            lines.append('Etiqueta anterior: %s → nueva: %s' % (
                self.prior_label or '', self.new_label or ''))
        if self.prior_volume_m3 or self.new_volume_m3:
            lines.append('Volumen: %.3f m³ → %.3f m³ (Δ %.3f m³)' % (
                self.prior_volume_m3 or 0.0, self.new_volume_m3 or 0.0,
                self.volume_diff_m3 or 0.0))
        if self.rebaja_volume_m3:
            lines.append('Rebaja: %.3f m³%s' % (
                self.rebaja_volume_m3,
                ' · %s pzas' % self.rebaja_pieces if self.rebaja_pieces else ''))
        if self.origin_operation_id:
            lines.append('Referencia: %s' % self.origin_operation_id.name)
        if self.destination_reference:
            lines.append('Destino: %s' % self.destination_reference)
        if self.evidence_reference:
            lines.append('Respaldo: %s' % self.evidence_reference)
        if balances:
            lines.append('Saldo disponible resultante: <b>%.3f m³</b>' % (
                balances.get('resulting_available', 0.0)))
        lines.append('Motivo: %s' % (self.reason or ''))
        lines.append('Usuario: %s' % (self.env.user.display_name))
        return '<br/>'.join(lines)

    def _sv_chatter_mail_kwargs(self):
        """`email_from` de respaldo cuando el actor no tiene email.

        Odoo 18 exige un email del autor para `message_post`. Una operación SV
        no debe fallar por configuración de correo del usuario: se conserva el
        autor funcional y se usa el email de la compañía (o un remitente de
        sistema) solo cuando el actor no tiene uno.
        """
        partner = self.env.user.partner_id
        if partner.email:
            return {}
        company = self.company_id or self.env.company
        fallback = company.email or company.partner_id.email or (
            'noreply@madenat.local')
        return {'email_from': fallback}

    def _sv_post_chatter(self, balances=None):
        self.ensure_one()
        body = self._sv_chatter_body(balances)
        mail_kwargs = self._sv_chatter_mail_kwargs()
        if self.lot_id:
            self.lot_id.message_post(
                body=body, message_type='notification', **mail_kwargs)
        if self.guia_processing_id:
            self.guia_processing_id.message_post(
                body=body, message_type='notification', **mail_kwargs)
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.guia_processing_id.id or False,
            'action_type': 'sv_operation',
            'description': '[%s] %s · %s · %s' % (
                self.name or '',
                dict(self._fields['action_type'].selection).get(
                    self.action_type),
                self.lot_id.name or '',
                (self.reason or '')[:180]),
            'batch_id': self.lot_id.name or '',
            'audit_snapshot': self.snapshot_json or '',
            'audit_hash': self.audit_hash or '',
            'user_id': self.env.user.id,
        })

    # ══════════════════════════════════════════════════════════════════════
    # ETIQUETAS: NORMALIZACIÓN Y UNICIDAD (incluye alias histórico)
    # ══════════════════════════════════════════════════════════════════════
    @api.model
    def _sv_normalize_label(self, label):
        return (label or '').strip().upper()

    @api.model
    def _sv_validate_label_format(self, label):
        normalized = self._sv_normalize_label(label)
        if not SV_LABEL_RE.match(normalized):
            raise ValidationError(_(
                'Formato de etiqueta SV inválido: "%s". Se exige "SV" seguido '
                'de 11 dígitos (ej. SV00000000008).'
            ) % (label or ''))
        return normalized

    @api.model
    def _sv_label_in_use(self, label, exclude_lot=None, exclude_operation=None):
        """True si la etiqueta está en uso actual o como alias histórico."""
        normalized = self._sv_normalize_label(label)
        if not normalized:
            return False
        lot_domain = [('name', '=', normalized), ('lot_flow_type', '=', 'volume')]
        if exclude_lot:
            lot_domain.append(('id', '!=', exclude_lot.id))
        if self.env['stock.lot'].sudo().search_count(lot_domain):
            return True
        history_domain = [
            '|', ('prior_label', '=', normalized),
            ('new_label', '=', normalized),
        ]
        if exclude_operation:
            history_domain = [
                ('id', '!=', exclude_operation.id)] + history_domain
        return bool(self.sudo().search_count(history_domain))

    # ══════════════════════════════════════════════════════════════════════
    # ACCIONES DE UI Y API PARA FLUJOS EXTERNOS
    # ══════════════════════════════════════════════════════════════════════
    def action_open_reverse_wizard(self):
        """Abre el asistente de reversa para la rebaja seleccionada."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reversar rebaja de etiqueta SV'),
            'res_model': 'madenat.sv.rebaja.reverse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_origin_operation_id': self.id,
                'default_lot_id': self.lot_id.id,
            },
        }

    @api.model
    def sv_create_rebaja(self, lot, volume_m3, reason, destination_container=None,
                         destination_shipment=None, destination_reference=False,
                         pieces=0):
        """Rebaja SV atómica para flujos externos (logística).

        Crea la operación y la aplica en la misma transacción. Si la operación
        requiere aprobación funcional (impacto financiero o período cerrado),
        falla con un mensaje claro para que el usuario use el asistente.
        """
        vals = {
            'lot_id': lot.id,
            'action_type': 'rebaja',
            'rebaja_volume_m3': volume_m3,
            'rebaja_pieces': pieces or 0,
            'reason': reason or _('Asignación logística a contenedor/embarque.'),
            'destination_reference': destination_reference or False,
            'requested_by_id': self.env.user.id,
        }
        if 'destination_container_id' in self._fields and destination_container:
            vals['destination_container_id'] = destination_container.id
        if 'destination_shipment_id' in self._fields and destination_shipment:
            vals['destination_shipment_id'] = destination_shipment.id
        with self._sv_concurrency_guard():
            operation = self.create(vals)
            pending = operation._sv_pending_approval_groups()
            if pending:
                raise ValidationError(_(
                    'La asignación de la etiqueta %s requiere aprobación '
                    'funcional (%s). Regístrela desde el asistente "Rebajar '
                    'etiqueta SV".'
                ) % (lot.name or lot.id, ', '.join(sorted(pending))))
            operation.action_apply()
        return operation

    @api.model
    def sv_reverse_allocation(self, lot, container=None, reason=None):
        """Reversa la rebaja activa de una asignación logística (SV-only)."""
        domain = [
            ('lot_id', '=', lot.id),
            ('action_type', '=', 'rebaja'),
            ('state', '=', 'applied'),
            ('reversed_operation_id', '=', False),
        ]
        if container is not None and 'destination_container_id' in self._fields:
            domain.append(('destination_container_id', '=', container.id))
        origin = self.search(domain, order='id desc', limit=1)
        if not origin:
            return self.browse()
        with self._sv_concurrency_guard():
            reversal = self.create({
                'lot_id': lot.id,
                'action_type': 'rebaja_reverse',
                'origin_operation_id': origin.id,
                'reason': reason or _(
                    'Liberación/reversa de asignación logística de etiqueta SV.'),
                'requested_by_id': self.env.user.id,
            })
            reversal.action_apply()
        return reversal

    def _sv_available_for_lot(self, lot):
        """Saldo disponible de la etiqueta (lectura sin bloqueo, solo UI)."""
        return lot.sv_available_m3 if lot else 0.0


class StockLotSv(models.Model):
    """Saldo y guardas server-side de las Etiquetas SV (flujo Volumen)."""

    _inherit = 'stock.lot'

    # Campos protegidos contra escritura directa en etiquetas SV.
    SV_PROTECTED_FIELDS = frozenset([
        'name',
        'volumen_m3',
        'volume_purchase_m3',
        'vol_shipment_m3',
        'piezas',
        # Marca técnica de serialización: solo el flujo interno autorizado
        # (capacidad de un solo uso) puede actualizarla.
        'sv_balance_stamp',
    ])

    sv_operation_ids = fields.One2many(
        'madenat.sv.operation',
        'lot_id',
        string='Historial de etiqueta SV',
    )
    sv_operation_count = fields.Integer(
        string='Operaciones SV',
        compute='_compute_sv_balances',
    )
    sv_original_volume_m3 = fields.Float(
        string='Volumen original SV (m³)',
        digits=(16, 3),
        compute='_compute_sv_balances',
        help='Volumen documental original capturado en el alta F3.1.',
    )
    sv_regularized_baseline_m3 = fields.Float(
        string='Baseline regularizado (m³)',
        digits=(16, 3),
        compute='_compute_sv_balances',
        help='Volumen original ajustado por la última regularización aplicada.',
    )
    sv_rebajado_m3 = fields.Float(
        string='Rebajado activo (m³)',
        digits=(16, 3),
        compute='_compute_sv_balances',
        help='Suma de rebajas aplicadas menos reversas válidas.',
    )
    sv_available_m3 = fields.Float(
        string='Saldo disponible SV (m³)',
        digits=(16, 3),
        compute='_compute_sv_balances',
        help='baseline regularizado - rebajado activo.',
    )
    sv_pieces_enabled = fields.Boolean(
        string='Saldo de piezas habilitado',
        compute='_compute_sv_balances',
        help='True solo si la Guía declara piezas documentales positivas.',
    )
    sv_original_pieces = fields.Integer(
        string='Piezas documentales',
        compute='_compute_sv_balances',
    )
    sv_rebajado_pieces = fields.Integer(
        string='Piezas rebajadas',
        compute='_compute_sv_balances',
    )
    sv_available_pieces = fields.Integer(
        string='Saldo disponible de piezas',
        compute='_compute_sv_balances',
    )
    sv_documentary_volume_m3 = fields.Float(
        string='Volumen oficial de la Guía (m³)',
        digits=(16, 3),
        compute='_compute_sv_balances',
        help='Volumen oficial documental vigente (PDF → Excel → Packing).',
    )
    sv_documentary_warning = fields.Boolean(
        string='Aviso documental',
        compute='_compute_sv_balances',
        help='True si el volumen oficial difiere del volumen original del lote '
             'o si la etiqueta usa el piezas=1 técnico.',
    )
    sv_balance_stamp = fields.Datetime(
        string='Marca de saldo SV',
        readonly=True,
        copy=False,
        groups='base.group_system',
        help='Marca técnica de serialización (campo técnico protegido): se '
             'actualiza únicamente desde el flujo interno autorizado de una '
             'operación SV, bajo capacidad de un solo uso. No es visible ni '
             'accesible por la API funcional. Odoo usa aislamiento REPEATABLE '
             'READ, por lo que esta escritura hace que dos transacciones '
             'concurrentes sobre el mismo lote no puedan confirmar ambas.',
    )

    @api.depends(
        'lot_flow_type',
        'volumen_m3',
        'volume_purchase_m3',
        'piezas',
        'volume_source_guia_id',
        'volume_source_guia_id.piezas_declaradas',
        'volume_source_guia_id.packing_pieces_declared',
        'sv_operation_ids.state',
        'sv_operation_ids.action_type',
        'sv_operation_ids.rebaja_volume_m3',
        'sv_operation_ids.rebaja_pieces',
        'sv_operation_ids.new_volume_m3',
        'sv_operation_ids.origin_operation_id',
        'sv_operation_ids.execution_date',
    )
    def _compute_sv_balances(self):
        for lot in self:
            values = lot._sv_balance_values()
            lot.sv_original_volume_m3 = values['original']
            lot.sv_regularized_baseline_m3 = values['baseline']
            lot.sv_rebajado_m3 = values['rebajado']
            lot.sv_available_m3 = values['available']
            lot.sv_pieces_enabled = values['pieces_enabled']
            lot.sv_original_pieces = values['original_pieces']
            lot.sv_rebajado_pieces = values['rebajado_pieces']
            lot.sv_available_pieces = values['available_pieces']
            lot.sv_documentary_volume_m3 = values['documentary_volume']
            lot.sv_documentary_warning = values['documentary_warning']
            lot.sv_operation_count = values['operation_count']

    # ── Saldo SV ──────────────────────────────────────────────────────────
    def _sv_documented_pieces(self):
        """Piezas documentales positivas de la Guía (nunca placeholders)."""
        self.ensure_one()
        guia = self.volume_source_guia_id
        if not guia:
            return 0
        declared = guia.piezas_declaradas or 0
        if declared > 0:
            return int(declared)
        packing = getattr(guia, 'packing_pieces_declared', 0) or 0
        return int(packing) if packing > 0 else 0

    def _sv_balance_values(self):
        """Saldo SV derivado del ledger (determinista y auditable)."""
        self.ensure_one()
        original = self.volume_purchase_m3 or self.volumen_m3 or 0.0
        operations = self.sv_operation_ids.filtered(
            lambda o: o.state in ('applied', 'reversed'))
        regularizations = operations.filtered(
            lambda o: o.action_type == 'regularize_volume'
            and o.state == 'applied')
        if regularizations:
            latest = regularizations.sorted(
                lambda o: (o.execution_date or o.create_date, o.id))[-1]
            baseline = latest.new_volume_m3 or 0.0
        else:
            baseline = original
        reversed_ids = set(operations.filtered(
            lambda o: o.action_type == 'rebaja_reverse'
            and o.state == 'applied').mapped('origin_operation_id').ids)
        active_rebajas = operations.filtered(
            lambda o: o.action_type == 'rebaja' and o.id not in reversed_ids)
        rebajado = sum(active_rebajas.mapped('rebaja_volume_m3'))
        rebajado_pieces = sum(active_rebajas.mapped('rebaja_pieces'))
        documented_pieces = self._sv_documented_pieces()
        pieces_enabled = documented_pieces > 0
        available = baseline - rebajado
        documentary_volume = 0.0
        if self.volume_source_guia_id and hasattr(
                self.volume_source_guia_id, 'get_official_volume_m3'):
            try:
                documentary_volume = (
                    self.volume_source_guia_id.get_official_volume_m3()[0]
                    or 0.0)
            except Exception:  # pragma: no cover - defensivo
                documentary_volume = 0.0
        warning = False
        if self.lot_flow_type == 'volume':
            if documentary_volume and float_compare(
                    documentary_volume, original,
                    precision_rounding=SV_VOLUME_PRECISION) != 0:
                warning = True
            if self.piezas == 1 and not pieces_enabled:
                warning = True
        return {
            'original': original,
            'baseline': baseline,
            'rebajado': rebajado,
            'available': available,
            'original_pieces': documented_pieces,
            'rebajado_pieces': rebajado_pieces,
            'available_pieces': max(
                documented_pieces - rebajado_pieces, 0),
            'pieces_enabled': pieces_enabled,
            'documentary_volume': documentary_volume,
            'documentary_warning': warning,
            'operation_count': len(self.sv_operation_ids),
        }

    # ── Concurrencia ──────────────────────────────────────────────────────
    def _lock_sv_lot_for_operation(self):
        """Bloquea la fila del lote SV y devuelve el registro fresco.

        Toda acción que pueda alterar saldo SV debe invocar este helper antes
        de recalcular el saldo. El bloqueo es un SELECT parametrizado
        FOR UPDATE dentro de la transacción actual (sin escrituras SQL).
        """
        self.ensure_one()
        if not self.id:
            raise UserError(_(
                'La etiqueta SV debe existir para poder bloquear su saldo.'))
        self.flush_recordset()
        self.env.cr.execute(
            'SELECT id FROM stock_lot WHERE id = %s FOR UPDATE', (self.id,))
        if not self.env.cr.fetchone():
            raise UserError(_(
                'La etiqueta SV (id %s) ya no existe.') % self.id)
        # Lectura fresca del ledger y del lote DESPUÉS del bloqueo.
        operation_model = self.env['madenat.sv.operation']
        operation_model.flush_model()
        operation_model.invalidate_model([
            'lot_id', 'state', 'action_type', 'rebaja_volume_m3',
            'rebaja_pieces', 'new_volume_m3', 'origin_operation_id',
            'reversed_operation_id', 'execution_date',
        ])
        self.invalidate_recordset([
            'volumen_m3', 'volume_purchase_m3', 'vol_shipment_m3',
            'sv_operation_ids', 'piezas',
        ])
        return self

    def _sv_locked_balance_values(self):
        """Saldo recalculado tras el bloqueo (nunca valores previos)."""
        self.ensure_one()
        values = self._sv_balance_values()
        values['resulting_available'] = values['available']
        return values

    # ── Guardas server-side (write / unlink) ──────────────────────────────
    def _sv_guard_write(self, vals):
        """Bloquea escrituras directas de etiqueta/volumen/piezas en lotes SV.

        La autorización NO depende de ningún flag booleano de contexto: exige
        una capacidad interna (`madenat.sv.internal.capability`) acuñada por la
        aplicación atómica de una operación SV, ligada al mismo lote y a la
        identidad funcional del actor, consumida en un solo uso.
        """
        volume_lots = self.filtered(lambda l: l.lot_flow_type == 'volume')
        if not volume_lots:
            return
        touched = self.SV_PROTECTED_FIELDS & set(vals)
        if not touched:
            return
        # Identidad funcional original, capturada ANTES de cualquier sudo().
        actor_uid = self.env.uid
        token = self.env.context.get('madenat_sv_capability')
        transaction_token = self.env.context.get('madenat_sv_capability_txn')
        blocked_message = _(
            'La etiqueta SV %s no puede modificarse directamente. Use la '
            'acción "Modificar etiqueta SV" para conservar el historial y el '
            'alias.')
        capability_model = self.env['madenat.sv.internal.capability']
        for lot in volume_lots:
            capability_data = None
            if token and transaction_token:
                # Con sudo (camino interno del sello técnico restringido) la
                # identidad se toma del propio registro de capacidad, que solo
                # pudo acuñar el flujo autorizado con el actor original.
                capability_data = capability_model.sudo()._sv_consume(
                    token, transaction_token, lot,
                    None if self.env.su else actor_uid)
            if not capability_data or not lot._sv_capability_authorizes(
                    vals, capability_data, touched, actor_uid):
                raise ValidationError(blocked_message % (lot.name or lot.id))

    def _sv_capability_authorizes(self, vals, capability_data, touched,
                                  actor_uid):
        """Autorización funcional de una escritura protegida con capacidad.

        Valida operación en borrador sobre el MISMO lote, acción y valores
        esperados coincidentes (incluido el sello técnico), permiso del actor
        funcional sobre operación y lote, y aprobaciones requeridas completas.
        """
        self.ensure_one()
        operation = self.env['madenat.sv.operation'].sudo().browse(
            capability_data.get('operation_id') or 0).exists()
        if not operation or operation.lot_id != self or operation.state != 'draft':
            return False
        if operation.action_type != capability_data.get('action_type'):
            return False
        # Permiso funcional del actor (nunca el del usuario técnico de sudo).
        actor = actor_uid if not self.env.su else capability_data.get(
            'actor_uid')
        if not actor:
            return False
        try:
            operation.with_user(actor).check_access('write')
            self.with_user(actor).check_access('write')
        except AccessError:
            return False
        if operation._sv_pending_approval_groups():
            return False
        allowed_values = dict(capability_data.get('values') or {})
        if set(touched) != set(allowed_values):
            return False
        for field_name, expected_value in allowed_values.items():
            if vals.get(field_name) != expected_value:
                return False
        return True

    def _sv_guard_unlink(self):
        """La etiqueta SV con historial no se elimina (salvo cleanup de tests)."""
        if self.env['madenat.sv.internal.marker'].sudo(
                )._sv_test_cleanup_allowed('stock.lot', self.ids):
            return
        for lot in self:
            if lot.sv_operation_ids:
                raise ValidationError(_(
                    'La etiqueta SV %s tiene historial de operaciones '
                    '(madenat.sv.operation) y no puede eliminarse. Registre '
                    'una operación de reversa/regularización.'
                ) % (lot.name or lot.id))
            # La etiqueta SV con existencias tampoco se elimina: es el ancla de
            # trazabilidad de la Guía y `stock.quant` la referencia con
            # ON DELETE RESTRICT (`stock_quant_lot_id_fkey`). El criterio es la
            # EXISTENCIA de fila en `stock.quant` (aunque la cantidad sea 0),
            # idéntico al que aplica PostgreSQL, para dar un mensaje de negocio
            # en lugar del error técnico de integridad.
            if lot.lot_flow_type == 'volume' and self.env['stock.quant'].sudo(
                    ).search_count([('lot_id', '=', lot.id)]):
                raise ValidationError(_(
                    'La etiqueta SV %s tiene existencias en stock y no puede '
                    'eliminarse. Es el ancla de trazabilidad de la Guía %s. '
                    'Registre una operación SV de reversa/regularización.'
                ) % (lot.name or lot.id,
                     lot.guia_number or lot.guia_processing_id.id))

    # ── Acciones de UI ────────────────────────────────────────────────────
    def _sv_wizard_action(self, name, model, **context_defaults):
        self.ensure_one()
        context = {'default_lot_id': self.id}
        context.update(context_defaults)
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def action_sv_rename(self):
        """Abre el asistente de modificación de etiqueta SV."""
        return self._sv_wizard_action(
            _('Modificar etiqueta SV'), 'madenat.sv.rename.wizard')

    def action_sv_regularize_volume(self):
        """Abre el asistente de regularización de volumen."""
        return self._sv_wizard_action(
            _('Regularizar volumen de etiqueta SV'),
            'madenat.sv.volume.regularize.wizard')

    def action_sv_rebaja(self):
        """Abre el asistente de rebaja de etiqueta SV."""
        return self._sv_wizard_action(
            _('Rebajar etiqueta SV'), 'madenat.sv.rebaja.wizard')

    def action_open_sv_history(self):
        """Historial cronológico completo de la etiqueta SV."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial SV · %s') % (self.name or ''),
            'res_model': 'madenat.sv.operation',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'search_default_group_by_action_type': 1,
            },
        }


class MadenatGuiaProcessingSv(models.Model):
    """Acceso a la gestión SV desde la Guía por Volúmenes."""

    _inherit = 'madenat.guia.processing'

    sv_operation_ids = fields.One2many(
        'madenat.sv.operation',
        'guia_processing_id',
        string='Operaciones SV de la Guía',
    )
    sv_operation_count = fields.Integer(
        string='Operaciones SV',
        compute='_compute_sv_operation_count',
    )

    @api.depends('sv_operation_ids')
    def _compute_sv_operation_count(self):
        for guia in self:
            guia.sv_operation_count = len(guia.sv_operation_ids)

    def action_open_sv_history(self):
        """Historial SV completo de la Guía (etiqueta y operaciones)."""
        self.ensure_one()
        lot = self.volume_lot_id
        domain = [('guia_processing_id', '=', self.id)]
        if lot:
            domain = ['|', ('lot_id', '=', lot.id)] + domain
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial SV · Guía %s') % (self.name or ''),
            'res_model': 'madenat.sv.operation',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_guia_processing_id': self.id,
                'default_lot_id': lot.id if lot else False,
            },
        }

    def _sv_require_volume_lot(self):
        """Etiqueta SV de la Guía (o error claro)."""
        self.ensure_one()
        lot = self.volume_lot_id
        if not lot:
            raise UserError(_(
                'La Guía %s no tiene una etiqueta SV asociada.'
            ) % (self.name or self.id))
        return lot

    def action_sv_rename(self):
        return self._sv_require_volume_lot().action_sv_rename()

    def action_sv_regularize_volume(self):
        return self._sv_require_volume_lot().action_sv_regularize_volume()

    def action_sv_rebaja(self):
        return self._sv_require_volume_lot().action_sv_rebaja()

# Grupos funcionales que pueden aprobar operaciones escaladas.
GROUP_AUDITORIA = 'madenat_lumber_core.group_madenat_auditoria'
GROUP_CONTABILIDAD = 'madenat_lumber_core.group_madenat_contabilidad'

# Redondeo canónico de volumen (3 decimales, utils_uom.r3).
SV_VOLUME_PRECISION = 0.001
