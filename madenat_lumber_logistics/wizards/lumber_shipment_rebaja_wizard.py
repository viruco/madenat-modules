# -*- coding: utf-8 -*-
"""B3 / CANON/18 §7.3 — Asistente «Rebajar por nave».

Selecciona nave y viaje, lista los contenedores consolidados pendientes de
rebaja (con su embarque) y ejecuta la rebaja masiva. Cada contenedor corre en
su propio savepoint; se informan éxitos y fallos sin abortar el lote completo.
"""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class LumberShipmentRebajaWizard(models.TransientModel):
    _name = 'lumber.shipment.rebaja.wizard'
    _description = 'Asistente para Rebajar por Nave/Viaje'

    vessel_id = fields.Many2one(
        'shipping.vessel', string='Motonave', required=True)
    voyage_id = fields.Many2one(
        'shipping.voyage', string='Viaje',
        domain="[('vessel_id', '=', vessel_id)]")
    container_ids = fields.Many2many(
        'lumber.container', 'rebaja_wiz_selected_rel', 'wizard_id',
        'container_id', string='Contenedores a rebajar',
        domain="[('state', 'in', ['loaded', 'sealed'])]")
    available_container_ids = fields.Many2many(
        'lumber.container', 'rebaja_wiz_available_rel', 'wizard_id',
        'container_id', string='Contenedores pendientes',
        compute='_compute_available')
    container_count = fields.Integer(
        'N° contenedores', compute='_compute_available')
    total_nominal_m3 = fields.Float(
        'Volumen nominal (m³)', compute='_compute_available', digits=(16, 3))
    result_message = fields.Text('Resultado', readonly=True)

    @api.depends('vessel_id', 'voyage_id', 'container_ids')
    def _compute_available(self):
        Container = self.env['lumber.container']
        for wiz in self:
            domain = [('state', 'in', ['loaded', 'sealed'])]
            if wiz.vessel_id:
                domain.append(
                    ('shipment_id.vessel_id', '=', wiz.vessel_id.id))
            if wiz.voyage_id:
                domain.append(
                    ('shipment_id.voyage_id', '=', wiz.voyage_id.id))
            available = Container.search(domain)
            wiz.available_container_ids = available
            wiz.container_count = len(available)
            wiz.total_nominal_m3 = sum(
                available.mapped('total_volume_purchase_m3'))

    @api.onchange('vessel_id', 'voyage_id')
    def _onchange_scope(self):
        """Preselecciona los contenedores pendientes del alcance elegido."""
        if not self.vessel_id:
            self.container_ids = [(5, 0, 0)]
            return
        self.container_ids = [(6, 0, self.available_container_ids.ids)]

    def action_rebajar(self):
        self.ensure_one()
        if not self.env.user.has_group(
                'madenat_lumber_core.group_madenat_jefatura_operaciones') \
                and not self.env.user.has_group(
                    'madenat_lumber_core.group_madenat_gerencia'):
            raise AccessError(_(
                'La rebaja por nave requiere Jefatura de Operaciones o '
                'Gerencia.'))
        if not self.container_ids:
            raise UserError(_('Seleccione al menos un contenedor para rebajar.'))

        successes, failures = [], []
        for container in self.container_ids:
            try:
                with self.env.cr.savepoint():
                    container._rebajar_container()
                successes.append(container.name)
            except Exception as exc:  # noqa: BLE001 - se informa al usuario
                failures.append('%s: %s' % (container.name, exc))

        lines = [_('Rebaja por nave completada.')]
        lines.append(_('Éxitos (%d): %s') % (
            len(successes), ', '.join(successes) or '-'))
        if failures:
            lines.append(_('Fallos (%d):') % len(failures))
            lines.extend('  - %s' % f for f in failures)
        self.result_message = '\n'.join(lines)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rebajar por nave'),
                'message': _('%d rebajados, %d con error.') % (
                    len(successes), len(failures)),
                'type': 'warning' if failures else 'success',
                'sticky': bool(failures),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
