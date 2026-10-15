# -*- coding: utf-8 -*-
"""B3 / CANON/18 §7.3 — Asistente «Rebaja Inteligente por Motonave».

Orquesta la rebaja física NATIVA por contenedor, reutilizando el motor único
`lumber.container._rebajar_container()` (creación de picking OUT, moves, reglas
Producto/Procesados/SV, `rebaja_state/qty/picking`, estado e idempotencia).

Este asistente NO duplica ni reemplaza ese motor: sólo
- exige la Motonave y permite el Viaje como filtro opcional (oculto si no hay
  viajes de la motonave);
- carga exclusivamente los contenedores del alcance motonave/viaje;
- clasifica rebajables vs. excluidos y explica el motivo de exclusión;
- restringe la selección al universo de la motonave (dominio + validación
  servidor);
- calcula los totales sólo sobre la selección;
- ejecuta con savepoint independiente por contenedor y muestra el resultado
  por contenedor sin cerrar automáticamente el asistente.

Regla de Oro: cambio mínimo sobre el motor físico ya validado.
"""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare


# Contrato operativo único: la rebaja por motonave no puede ser más restrictiva
# que la rebaja individual (`lumber.container.action_rebajar`).
REBAJA_WIZARD_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)

REBAJA_STATE_LABELS = {
    'empty': 'Vacío',
    'loading': 'Cargando',
    'loaded': 'Cargado',
    'sealed': 'Sellado',
    'rebajado': 'Rebajado',
    'shipped': 'Embarcado',
}

# Estados consolidados (mismos que `lumber.container.REBAJA_ALLOWED_STATES`).
REBAJA_ALLOWED_STATES = ('loaded', 'sealed')


class LumberShipmentRebajaWizard(models.TransientModel):
    _name = 'lumber.shipment.rebaja.wizard'
    _description = 'Asistente para Rebajar por Motonave/Viaje'

    vessel_id = fields.Many2one(
        'shipping.vessel', string='Motonave', required=True)
    voyage_id = fields.Many2one(
        'shipping.voyage', string='Viaje',
        domain="[('vessel_id', '=', vessel_id)]")
    voyage_available = fields.Boolean(
        'Hay viajes', compute='_compute_voyage_available')

    container_ids = fields.Many2many(
        'lumber.container', 'rebaja_wiz_selected_rel', 'wizard_id',
        'container_id', string='Contenedores a rebajar',
        domain="[('state', 'in', ['loaded', 'sealed']),"
               " ('vessel_id', '=', vessel_id)]")
    line_ids = fields.One2many(
        'lumber.shipment.rebaja.wizard.line', 'wizard_id',
        string='Clasificación por contenedor')
    available_container_ids = fields.Many2many(
        'lumber.container', 'rebaja_wiz_available_rel', 'wizard_id',
        'container_id', string='Contenedores rebajables',
        compute='_compute_from_lines')
    excluded_container_ids = fields.Many2many(
        'lumber.container', 'rebaja_wiz_excluded_rel', 'wizard_id',
        'container_id', string='Contenedores excluidos',
        compute='_compute_from_lines')

    container_count = fields.Integer(
        'N° rebajables', compute='_compute_from_lines')
    excluded_count = fields.Integer(
        'N° excluidos', compute='_compute_from_lines')
    selected_count = fields.Integer(
        'N° seleccionados', compute='_compute_totals')
    total_lots = fields.Integer(
        'Lotes seleccionados', compute='_compute_totals')
    total_nominal_m3 = fields.Float(
        'Vol. nominal (m³)', compute='_compute_totals', digits=(16, 3))
    total_export_m3 = fields.Float(
        'Vol. exportable (m³)', compute='_compute_totals', digits=(16, 3))
    total_physical_m3 = fields.Float(
        'Vol. físico disponible (m³)', compute='_compute_totals',
        digits=(16, 3))
    total_rebaja_m3 = fields.Float(
        'Vol. a rebajar (m³)', compute='_compute_totals', digits=(16, 3))
    total_sv_m3 = fields.Float(
        'Vol. oficial SV (m³)', compute='_compute_totals', digits=(16, 3))
    total_rebajado_m3 = fields.Float(
        'Vol. ya rebajado (m³)', compute='_compute_totals', digits=(16, 3))
    result_message = fields.Text('Resultado', readonly=True, default='')

    # ══════════════════════════════════════════════════════════════════════
    # Permisos (contrato operativo único)
    # ══════════════════════════════════════════════════════════════════════
    def _rebaja_require_group(self):
        if not any(self.env.user.has_group(g) for g in REBAJA_WIZARD_GROUPS):
            raise AccessError(_(
                'La rebaja por motonave requiere el rol de Operaciones, '
                'Jefatura de Operaciones o Gerencia.'))

    # ══════════════════════════════════════════════════════════════════════
    # Alcance y computed
    # ══════════════════════════════════════════════════════════════════════
    @api.depends('vessel_id')
    def _compute_voyage_available(self):
        Voyage = self.env['shipping.voyage']
        for wiz in self:
            wiz.voyage_available = bool(wiz.vessel_id) and bool(
                Voyage.search_count([('vessel_id', '=', wiz.vessel_id.id)]))

    @api.depends('line_ids', 'line_ids.eligible')
    def _compute_from_lines(self):
        for wiz in self:
            eligible = wiz.line_ids.filtered('eligible')
            excluded = wiz.line_ids.filtered(lambda l: not l.eligible)
            wiz.available_container_ids = eligible.mapped('container_id')
            wiz.excluded_container_ids = excluded.mapped('container_id')
            wiz.container_count = len(eligible)
            wiz.excluded_count = len(excluded)

    @api.depends('container_ids', 'line_ids', 'line_ids.eligible')
    def _compute_totals(self):
        for wiz in self:
            selected = wiz.container_ids & wiz.available_container_ids
            wiz.selected_count = len(selected)
            lots = 0
            nominal = export = physical = rebaja = sv = already = 0.0
            for container in selected:
                metrics = wiz._container_metrics(container)
                lots += metrics['lot_count']
                nominal += metrics['nominal_m3']
                export += metrics['export_m3']
                physical += metrics['physical_m3']
                rebaja += metrics['rebaja_m3']
                sv += metrics['sv_m3']
                already += metrics['already_rebajado_m3']
            wiz.total_lots = lots
            wiz.total_nominal_m3 = nominal
            wiz.total_export_m3 = export
            wiz.total_physical_m3 = physical
            wiz.total_rebaja_m3 = rebaja
            wiz.total_sv_m3 = sv
            wiz.total_rebajado_m3 = already

    # ══════════════════════════════════════════════════════════════════════
    # Clasificación (no destructiva) — espejo de `_rebaja_planned_lines`
    # ══════════════════════════════════════════════════════════════════════
    def _scope_containers(self):
        """Contenedores asociados al alcance motonave/viaje (todos los estados,
        para poder explicar exclusiones)."""
        self.ensure_one()
        if not self.vessel_id:
            return self.env['lumber.container']
        domain = [('vessel_id', '=', self.vessel_id.id)]
        if self.voyage_id:
            domain.append(
                ('shipment_id.voyage_id', '=', self.voyage_id.id))
        return self.env['lumber.container'].search(domain)

    def _planned_lines_safe(self, container):
        """Copia no destructiva de `_rebaja_planned_lines` que NO lanza:
        retorna (plan, None) o (None, motivo). Réplica de la fuente de verdad
        para no divergir del motor físico."""
        plan = []
        for line in container.line_ids:
            lot = line.lot_id
            sv_op = self.env['madenat.sv.operation']
            if lot.lot_flow_type == 'volume':
                sv_op = self.env['madenat.sv.operation'].search([
                    ('lot_id', '=', lot.id),
                    ('action_type', '=', 'rebaja'),
                    ('state', '=', 'applied'),
                    ('destination_container_id', '=', container.id),
                ], order='id desc', limit=1)
                if not sv_op:
                    return None, _(
                        'Etiqueta SV %s sin operación de rebaja aplicada para '
                        'este contenedor.'
                    ) % (lot.name or lot.id)
                qty = sv_op.rebaja_volume_m3
            else:
                qty = lot.volumen_restante_m3
            if float_compare(qty, 0.0, precision_rounding=0.001) <= 0:
                return None, _(
                    'Lote %s sin volumen disponible para rebajar.'
                ) % (lot.name or lot.id)
            quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ], limit=1)
            if not quant:
                return None, _(
                    'Lote %s sin stock físico en bodega interna.'
                ) % (lot.name or lot.id)
            plan.append((line, lot, qty, quant.location_id, sv_op))
        return plan, None

    def _classify(self, container):
        """(eligible: bool, reason: str) para un contenedor del alcance."""
        self.ensure_one()
        rebaja_applied = container.state in ('rebajado', 'shipped') or any(
            line.rebaja_state == 'rebajado'
            or (line.rebaja_picking_id
                and line.rebaja_picking_id.state == 'done')
            for line in container.line_ids)
        if rebaja_applied:
            return False, _('Rebaja física ya aplicada o contenedor embarcado.')
        if container.state == 'loading':
            return False, _(
                'Estado Cargando: el contenedor aún no está consolidado.')
        if container.state not in REBAJA_ALLOWED_STATES:
            return False, _('Estado no rebajable (%s).') % (
                REBAJA_STATE_LABELS.get(container.state, container.state))
        if not container.line_ids:
            return False, _('Contenedor sin lotes consolidados.')
        _plan, reason = self._planned_lines_safe(container)
        if reason:
            return False, reason
        return True, ''

    def _container_metrics(self, container):
        """Volumetría por contenedor (no lanza)."""
        self.ensure_one()
        already = sum(container.line_ids.filtered(
            lambda l: l.rebaja_state == 'rebajado').mapped('rebaja_qty_m3'))
        plan, _reason = self._planned_lines_safe(container)
        physical = rebaja = sv = 0.0
        if plan:
            for _line, lot, qty, _src, sv_op in plan:
                rebaja += qty
                if lot.lot_flow_type == 'volume':
                    physical += sv_op.rebaja_volume_m3 if sv_op else 0.0
                    sv += sv_op.rebaja_volume_m3 if sv_op else 0.0
                else:
                    physical += qty
        return {
            'lot_count': len(container.line_ids),
            'nominal_m3': container.total_volume_purchase_m3,
            'export_m3': container.total_vol_shipment_m3,
            'physical_m3': physical,
            'rebaja_m3': rebaja,
            'sv_m3': sv,
            'already_rebajado_m3': already,
        }

    def _get_selection_domain(self):
        """Dominio de selección: sólo elegibles del alcance motonave/viaje."""
        self.ensure_one()
        domain = [('state', 'in', list(REBAJA_ALLOWED_STATES))]
        if self.vessel_id:
            domain.append(('vessel_id', '=', self.vessel_id.id))
        if self.voyage_id:
            domain.append(
                ('shipment_id.voyage_id', '=', self.voyage_id.id))
        eligible = self._scope_containers().filtered(
            lambda c: self._classify(c)[0])
        domain.append(('id', 'in', eligible.ids))
        return domain

    # ══════════════════════════════════════════════════════════════════════
    # Grilla de clasificación (transient, se reconstruye al cambiar alcance)
    # ══════════════════════════════════════════════════════════════════════
    def _line_commands(self):
        self.ensure_one()
        commands = []
        for container in self._scope_containers():
            eligible, reason = self._classify(container)
            metrics = self._container_metrics(container)
            commands.append((0, 0, {
                'container_id': container.id,
                'eligible': eligible,
                'exclusion_reason': reason,
                'lot_count': metrics['lot_count'],
                'nominal_m3': metrics['nominal_m3'],
                'export_m3': metrics['export_m3'],
                'physical_m3': metrics['physical_m3'],
                'rebaja_m3': metrics['rebaja_m3'],
                'sv_m3': metrics['sv_m3'],
                'already_rebajado_m3': metrics['already_rebajado_m3'],
            }))
        return commands

    def _rebuild_lines(self):
        for wiz in self:
            wiz.write({'line_ids': [(5, 0, 0)] + wiz._line_commands()})

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        wizards._rebuild_lines()
        return wizards

    def write(self, vals):
        vals = dict(vals)
        scope_changed = any(f in vals for f in ('vessel_id', 'voyage_id'))
        if scope_changed:
            # Nunca arrastrar la selección entre motonaves/viajes distintos.
            vals['container_ids'] = [(5, 0, 0)]
        res = super().write(vals)
        if scope_changed:
            self._rebuild_lines()
        return res

    @api.onchange('vessel_id', 'voyage_id')
    def _onchange_scope(self):
        """Limpia la selección y reconstruye la grilla; restringe el dominio de
        selección a los elegibles del nuevo alcance."""
        if self.vessel_id:
            self.voyage_id = (
                self.voyage_id
                if self.voyage_id.vessel_id == self.vessel_id else False)
        self.container_ids = [(5, 0, 0)]
        self.line_ids = [(5, 0, 0)] + self._line_commands()
        return {'domain': {'container_ids': self._get_selection_domain()}}

    # ══════════════════════════════════════════════════════════════════════
    # Ejecución — reutiliza el motor físico, un savepoint por contenedor
    # ══════════════════════════════════════════════════════════════════════
    def action_rebajar(self):
        self.ensure_one()
        self._rebaja_require_group()
        if not self.vessel_id:
            raise UserError(_('Seleccione una Motonave.'))
        if self.voyage_id and self.voyage_id.vessel_id != self.vessel_id:
            raise UserError(_(
                'El Viaje seleccionado no pertenece a la Motonave.'))
        if not self.container_ids:
            raise UserError(_(
                'Seleccione al menos un contenedor para rebajar.'))

        successes, failures = [], []
        for container in self.container_ids:
            # Validación servidor obligatoria (no confiar sólo en el dominio).
            if container.shipment_id.vessel_id != self.vessel_id:
                failures.append('%s: %s' % (
                    container.name,
                    _('no pertenece a la Motonave seleccionada.')))
                continue
            if self.voyage_id and \
                    container.shipment_id.voyage_id != self.voyage_id:
                failures.append('%s: %s' % (
                    container.name,
                    _('no pertenece al Viaje seleccionado.')))
                continue
            eligible, reason = self._classify(container)
            if not eligible:
                failures.append('%s: %s' % (container.name, reason))
                continue
            try:
                with self.env.cr.savepoint():
                    container._rebajar_container()
                successes.append(container.name)
            except Exception as exc:  # noqa: BLE001 - se informa al usuario
                failures.append('%s: %s' % (container.name, exc))

        lines = [_('Rebaja por motonave completada.')]
        lines.append(_('Éxitos (%d): %s') % (
            len(successes), ', '.join(successes) or '-'))
        if failures:
            lines.append(_('Fallos (%d):') % len(failures))
            lines.extend('  - %s' % f for f in failures)
        self.result_message = '\n'.join(lines)
        # Refrescar la clasificación (los rebajados pasan a excluidos con su
        # motivo) sin cerrar el asistente.
        self._rebuild_lines()
        self.write({'container_ids': [(5, 0, 0)]})

        # NO se cierra automáticamente: se recarga el propio registro para que
        # el usuario lea el resultado por contenedor.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rebajar por motonave'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class LumberShipmentRebajaWizardLine(models.TransientModel):
    """Línea de clasificación por contenedor (sólo lectura).

    Necesaria porque un `Many2many` a `lumber.container` no puede portar el
    motivo de exclusión ni la volumetría por contenedor exigida por la UI.
    """
    _name = 'lumber.shipment.rebaja.wizard.line'
    _description = 'Clasificación de contenedor para rebaja por motonave'
    _order = 'eligible desc, id'

    wizard_id = fields.Many2one(
        'lumber.shipment.rebaja.wizard', required=True, ondelete='cascade')
    container_id = fields.Many2one(
        'lumber.container', string='Contenedor', required=True,
        ondelete='cascade')
    shipment_id = fields.Many2one(
        'lumber.export.shipment', string='Embarque',
        related='container_id.shipment_id')
    booking = fields.Char(
        string='Booking', related='container_id.shipment_id.booking_reference')
    container_state = fields.Selection(
        related='container_id.state', string='Estado')
    patio_names = fields.Char('Patio(s)', compute='_compute_patio_names')
    lot_count = fields.Integer('Lotes')
    nominal_m3 = fields.Float('Vol. nominal (m³)', digits=(16, 3))
    export_m3 = fields.Float('Vol. exportable (m³)', digits=(16, 3))
    physical_m3 = fields.Float('Vol. físico (m³)', digits=(16, 3))
    rebaja_m3 = fields.Float('Vol. a rebajar (m³)', digits=(16, 3))
    sv_m3 = fields.Float('Vol. oficial SV (m³)', digits=(16, 3))
    already_rebajado_m3 = fields.Float(
        'Vol. ya rebajado (m³)', digits=(16, 3))
    eligible = fields.Boolean('Rebajable')
    exclusion_reason = fields.Char('Motivo de exclusión')

    @api.depends('container_id')
    def _compute_patio_names(self):
        for line in self:
            locations = line.container_id.lot_ids.mapped(
                'quant_ids').filtered(
                lambda q: q.location_id.usage == 'internal'
            ).mapped('location_id')
            names = sorted({loc.display_name for loc in locations if loc})
            line.patio_names = ', '.join(names)
