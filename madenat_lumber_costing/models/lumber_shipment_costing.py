# -*- coding: utf-8 -*-
"""Costeo provisional post-Entrega — Política C2 (Odoo 18 CE).

Este módulo REEMPLAZA el motor inseguro/inoperante histórico de
`lumber.export.shipment.action_distribute_costs()` (que usaba SQL de escritura
sobre `logistic_cost_usd` y el campo inexistente `partner_id`).

Contrato C2:
  - se ejecuta sólo sobre Embarques `delivered`;
  - se basa en líneas de costo aprobadas (`lumber.shipment.cost.line`);
  - distribuye por volumen logístico final por lote;
  - NO modifica inventario físico (move/quant/lote/cantidades);
  - genera una versión de distribución auditada (SHA-256);
  - conserva la historia anterior (append-only);
  - los costos tardíos requieren una nueva versión formal (supersede).

El motor legado de Logistics queda CLAUSURADO desde aquí: al ser
`madenat_lumber_costing` la herencia más externa del MRO de
`lumber.export.shipment`, la sobreescritura de `action_distribute_costs`
intercepta cualquier llamada RPC/import antes de llegar a Logistics.
"""
from decimal import Decimal, ROUND_HALF_UP

from odoo import models, fields, _
from odoo.exceptions import AccessError, UserError
import logging

_logger = logging.getLogger(__name__)

# ── Rol autorizado a operar el costeo C2 (Costos o Contabilidad) ──────────
C2_COSTING_GROUPS = (
    'madenat_lumber_core.group_madenat_costos',
    'madenat_lumber_core.group_madenat_contabilidad',
)
# ── Rol autorizado a APLICAR (liquidar) la distribución C2 ───────────────
C2_APPLY_GROUPS = (
    'madenat_lumber_core.group_madenat_contabilidad',
)
# ── Estados reales de la línea fuente que equivalen a "aprobada" ──────────
# El modelo `lumber.shipment.cost.line` (madenat_vendor_payment) usa
# draft/validated/paid. "approved" ⇔ `validated` (o `paid`).
C2_APPROVED_SOURCE_STATES = ('validated', 'paid')
# ── Base de prorrateo aprobada ────────────────────────────────────────────
C2_BASIS = 'final_logistic_volume'
# Tolerancia monetaria explícita (centavos por distribución).
C2_MONETARY_TOLERANCE = Decimal('0.01')
# Regla determinista de ajuste de residual.
C2_RESIDUAL_RULE = 'largest_base_lot'
# Mapeo categoría de costo de embarque -> cost_type de `stock.lot.cost.line`
# para que el compute ORM existente clasifique el gasto correctamente
# (fletes/puerto/aduanas/seguro -> logistic_cost_usd).
C2_LEDGER_COST_TYPE_MAP = {
    'freight': 'freight',
    'inland_freight': 'ocean_freight',
    'port_charges': 'port',
    'customs': 'customs',
    'insurance': 'insurance',
}
C2_LEDGER_DEFAULT_COST_TYPE = 'other'


class LumberExportShipmentCosting(models.Model):
    """Extensión de `lumber.export.shipment` desde el módulo de Costeo (C2)."""

    _inherit = 'lumber.export.shipment'

    # ── Campos de apoyo para UI C2 (read-only / compute) ──────────────────
    c2_distribution_ids = fields.One2many(
        'lumber.cost.distribution',
        'shipment_id',
        string='Distribuciones C2',
        readonly=True,
    )
    c2_active_distribution_id = fields.Many2one(
        'lumber.cost.distribution',
        string='Distribución C2 activa',
        compute='_compute_c2_active_distribution',
        store=False,
    )
    c2_version = fields.Integer(
        string='Versión C2',
        compute='_compute_c2_active_distribution', store=False)
    c2_total_source_usd = fields.Float(
        string='Total fuente USD (C2)',
        compute='_compute_c2_active_distribution', store=False,
        digits=(16, 2))
    c2_total_distributed_usd = fields.Float(
        string='Total distribuido USD (C2)',
        compute='_compute_c2_active_distribution', store=False,
        digits=(16, 2))
    c2_residual_usd = fields.Float(
        string='Residual USD (C2)',
        compute='_compute_c2_active_distribution', store=False,
        digits=(16, 2))
    c2_basis = fields.Selection(
        [('final_logistic_volume', 'Volumen logístico final (m³)')],
        string='Base de prorrateo (C2)',
        compute='_compute_c2_active_distribution', store=False)
    c2_gate_ok = fields.Boolean(
        string='Gate C2 OK', compute='_compute_c2_gate', store=False)
    c2_gate_message = fields.Text(
        string='Estado del gate C2', compute='_compute_c2_gate', store=False)
    c2_ledger_line_ids = fields.One2many(
        'stock.lot.cost.line',
        'shipment_id',
        string='Ledger por lote (C2)',
        readonly=True,
    )

    # ══════════════════════════════════════════════════════════════════════
    # MOTOR LEGADO — CLAUSURADO (P0)
    # ══════════════════════════════════════════════════════════════════════
    def action_distribute_costs(self):
        """Motor histórico DESHABILITADO por la Política C2.

        El motor anterior (definido en `madenat_lumber_logistics`) ejecutaba
        SQL de escritura sobre `stock_lot.logistic_cost_usd` (campo
        compute/store) e intentaba escribir el campo inexistente `partner_id`.
        Queda bloqueado en cualquier vía (UI/RPC/import) para impedir que se
        ejecute; el flujo válido es prepare + apply C2.
        """
        raise UserError(_(
            'El motor de distribución de costos anterior está DESHABILITADO.\n'
            'El costeo post-Entrega se realiza con la Política C2: use '
            '«Preparar distribución» y «Aplicar distribución» desde la '
            'pestaña «Costeo C2» del Embarque entregado.\n'
            'No se permite SQL ni sobrescritura directa de costos de lote.'
        ))

    # ══════════════════════════════════════════════════════════════════════
    # GATES C2 (sólo lectura, sin sudo, sin escrituras)
    # ══════════════════════════════════════════════════════════════════════
    def _c2_assert_user(self, groups=C2_COSTING_GROUPS):
        if not any(self.env.user.has_group(g) for g in groups):
            raise AccessError(_(
                'No tiene permisos para operar el Costeo post-Entrega (C2). '
                'Se requiere el rol de Costos o Contabilidad.'))

    def _c2_source_cost_lines(self):
        """Líneas de costo fuente APROBADAS del Embarque."""
        self.ensure_one()
        return self.cost_line_ids.filtered(
            lambda l: l.state in C2_APPROVED_SOURCE_STATES)

    def _c2_applied_distribution(self):
        """Distribución C2 activa (applied) del Embarque, si existe."""
        self.ensure_one()
        return self.env['lumber.cost.distribution'].search([
            ('shipment_id', '=', self.id),
            ('is_c2', '=', True),
            ('state', '=', 'applied'),
        ], order='version_number desc, id desc', limit=1)

    def _c2_eligible_lots(self):
        """Lotes elegibles: contenedores con rebaja física ACTIVA.

        Excluye Contenedores pendientes/inconsistentes (gate) y líneas
        reversed/compensadas por R2 (segunda barrera).
        """
        self.ensure_one()
        active = self.container_ids.filtered(
            lambda c: self._container_rebaja_classification(c) == 'active')
        lots = active.mapped('lot_ids')
        reversed_lots = active.line_ids.filtered(
            lambda l: l.rebaja_state == 'reversed').mapped('lot_id')
        return lots - reversed_lots

    def _c2_lot_volume(self, lot):
        """Volumen logístico final del lote (m³)."""
        return (lot.vol_shipment_m3 or lot.volumen_m3 or 0.0)

    def _c2_total_volume(self, lots):
        total = Decimal('0.000')
        for lot in lots:
            total += Decimal(str(self._c2_lot_volume(lot))).quantize(
                Decimal('0.001'), rounding=ROUND_HALF_UP)
        return total

    def _c2_gate_checks(self):
        """Evalúa el gate C2 SIN lanzar excepciones (para UI y asserts)."""
        self.ensure_one()
        checks = {
            'delivered': self.state == 'delivered',
            'no_b01_open': self.b01_exception_state != 'open',
            'b01_resolved_or_none': self.b01_exception_state in
                ('none', 'resolved'),
            'no_pending': False,
            'no_inconsistency': True,
            'no_return_incomplete': True,
            'has_source_cost': False,
            'currency_ok': False,
            'idempotency': True,
        }
        try:
            self._assert_no_rebaja_inconsistency()
        except UserError:
            checks['no_inconsistency'] = False
            checks['no_return_incomplete'] = False
        _rebajados, pendientes = self._classify_departure_containers()
        checks['no_pending'] = not pendientes
        approved = self._c2_source_cost_lines()
        checks['has_source_cost'] = bool(approved)
        checks['currency_ok'] = bool(approved) and all(
            l.currency_id and (l.amount_usd or 0.0) > 0 for l in approved)
        applied = self._c2_applied_distribution()
        if applied and set(applied.source_cost_line_ids.ids) != set(
                approved.ids):
            checks['idempotency'] = False
        return checks


    def _assert_can_distribute_costs_c2(self):
        """Gate de servidor C2 (NO escribe, sin sudo)."""
        self.ensure_one()
        self._c2_assert_user(C2_COSTING_GROUPS)
        checks = self._c2_gate_checks()
        if not checks['delivered']:
            raise UserError(_(
                'Sólo se pueden distribuir costos sobre un Embarque '
                'ENTREGADO (delivered). Estado actual: %s.') % self.state)
        if not checks['no_b01_open']:
            raise UserError(_(
                'No se puede distribuir costos del Embarque %s: tiene una '
                'excepción B-01 ABIERTA. Regularice y cierre la excepción '
                'antes del costeo.') % self.name)
        if not checks['no_inconsistency']:
            raise UserError(_(
                'No se puede distribuir costos del Embarque %s: existe una '
                'inconsistencia de rebaja física / retorno R2 incompleto.') %
                self.name)
        if not checks['no_pending']:
            raise UserError(_(
                'No se puede distribuir costos del Embarque %s: existen '
                'Contenedores pendientes de rebaja física.') % self.name)
        if not checks['has_source_cost']:
            raise UserError(_(
                'No hay líneas de costo APROBADAS para el Embarque %s. '
                'Valide/apruebe al menos una línea de costo de embarque.') %
                self.name)
        if not checks['currency_ok']:
            raise UserError(_(
                'Las líneas de costo fuente del Embarque %s deben tener '
                'moneda y monto USD válidos (> 0).') % self.name)
        if not checks['idempotency']:
            raise UserError(_(
                'Existen costos tardíos en el Embarque %s que no están '
                'cubiertos por la versión aplicada. Se requiere una '
                'redistribución formal (supersede), no disponible en esta '
                'entrega.') % self.name)
        return True

    # ══════════════════════════════════════════════════════════════════════
    # ACCIONES C2
    # ══════════════════════════════════════════════════════════════════════
    def _c2_open_distribution(self, dist):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Distribución de Costos C2'),
            'res_model': 'lumber.cost.distribution',
            'res_id': dist.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _c2_next_version(self):
        self.ensure_one()
        last = self.env['lumber.cost.distribution'].search([
            ('shipment_id', '=', self.id),
            ('is_c2', '=', True),
        ], order='version_number desc, id desc', limit=1)
        return (last.version_number or 0) + 1


    def action_prepare_distribution(self):
        """Prepara (crea/reutiliza) la versión C2 en borrador."""
        self.ensure_one()
        self._assert_can_distribute_costs_c2()
        Distribution = self.env['lumber.cost.distribution']
        approved = self._c2_source_cost_lines()
        approved_ids = set(approved.ids)

        applied = self._c2_applied_distribution()
        if applied:
            if set(applied.source_cost_line_ids.ids) == approved_ids:
                raise UserError(_(
                    'El Embarque %s ya tiene una distribución C2 aplicada '
                    '(versión %s). No se duplica.') % (
                        self.name, applied.version_number))
            raise UserError(_(
                'El Embarque %s tiene costos tardíos. Se requiere una '
                'redistribución formal (supersede) que no está disponible '
                'en esta entrega.') % self.name)

        draft = Distribution.search([
            ('shipment_id', '=', self.id),
            ('is_c2', '=', True),
            ('state', '=', 'draft'),
        ])
        draft = draft.filtered(
            lambda d: set(d.source_cost_line_ids.ids) == approved_ids)
        if draft:
            return self._c2_open_distribution(draft[0])

        lots = self._c2_eligible_lots()
        total_volume = self._c2_total_volume(lots)
        if total_volume <= 0:
            raise UserError(_(
                'No se puede preparar la distribución del Embarque %s: el '
                'volumen logístico total final es 0.') % self.name)

        total_source = Decimal('0.00')
        for line in approved:
            total_source += Decimal(str(line.amount_usd)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

        version = self._c2_next_version()
        dist = Distribution.create({
            'shipment_id': self.id,
            'booking_id': self.id,
            'ref': self.name,
            'target_model': 'booking',
            'state': 'draft',
            'is_c2': True,
            'version_number': version,
            'basis': C2_BASIS,
            'distribution_date': fields.Date.context_today(self),
            'source_cost_line_ids': [(6, 0, approved.ids)],
            'total_source_cost_usd': float(total_source),
            'total_distributed_usd': 0.0,
            'residual_usd': 0.0,
        })
        self.message_post(body=_(
            '🧾 <b>Costeo C2</b>: versión %(v)s preparada (borrador) con '
            '%(n)s línea(s) de costo aprobada(s). Base: volumen logístico '
            'final. <b>No modifica inventario físico.</b>'
        ) % {'v': version, 'n': len(approved)})
        return self._c2_open_distribution(dist)


    def action_apply_distribution(self):
        """Aplica (liquida) la versión C2 en borrador del Embarque."""
        self.ensure_one()
        self._assert_can_distribute_costs_c2()
        self._c2_assert_user(C2_APPLY_GROUPS)
        if self._c2_applied_distribution():
            raise UserError(_(
                'El Embarque %s ya tiene una distribución C2 aplicada. No se '
                'duplica (use supersede formal para costos tardíos).') %
                self.name)
        Distribution = self.env['lumber.cost.distribution']
        draft = Distribution.search([
            ('shipment_id', '=', self.id),
            ('is_c2', '=', True),
            ('state', '=', 'draft'),
        ], order='version_number desc, id desc', limit=1)
        if not draft:
            self.action_prepare_distribution()
            draft = Distribution.search([
                ('shipment_id', '=', self.id),
                ('is_c2', '=', True),
                ('state', '=', 'draft'),
            ], order='version_number desc, id desc', limit=1)
        draft.action_apply_c2()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # ══════════════════════════════════════════════════════════════════════
    # COMPUTES DE UI
    # ══════════════════════════════════════════════════════════════════════
    def _compute_c2_active_distribution(self):
        for rec in self:
            dist = rec._c2_applied_distribution()
            rec.c2_active_distribution_id = dist
            rec.c2_version = dist.version_number or 0
            rec.c2_total_source_usd = dist.total_source_cost_usd or 0.0
            rec.c2_total_distributed_usd = dist.total_distributed_usd or 0.0
            rec.c2_residual_usd = dist.residual_usd or 0.0
            rec.c2_basis = dist.basis or False

    def _compute_c2_gate(self):
        for rec in self:
            checks = rec._c2_gate_checks()
            rec.c2_gate_ok = all(checks.values())
            pending = [k for k, v in checks.items() if not v]
            if not pending:
                rec.c2_gate_message = _('Gate C2 OK: listo para distribuir.')
            else:
                rec.c2_gate_message = _(
                    'Gate C2 bloqueado por: %s') % ', '.join(pending)
