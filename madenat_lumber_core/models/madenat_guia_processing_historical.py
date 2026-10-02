# -*- coding: utf-8 -*-
"""H1 — Reversión física ASISTIDA de producción histórica (sin llave G2).

Este archivo EXTIENDE `madenat.guia.processing` de forma aditiva. NO modifica
G1 (`action_reopen_to_draft` / `_reopen_to_draft_confirmed`), G2/G3
(`guia_processing_id`, `_attributed_production_pickings`,
`_reverse_production_picking`) ni BT-04 (`_reverse_consumption_picking`).

Reglas aprobadas (informe H1):
- Sin atribución automática: `origin`/`lot_id`/producto/proveedor/fecha son
  señales de propuesta, nunca llaves.
- Solo retorno TOTAL por picking seleccionado explícitamente.
- Se preserva la historia (nunca `stock.quant.write/unlink`, ni borrar/
  desvincular lotes, pickings, moves o move lines). `lot_ids` intacto.
- Idempotente: retorno previo ⇒ no se propone ni se permite revertir.
- G1 conserva la reapertura documental; H1 no la invoca.
"""
import hashlib
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Prefijos históricos de `origin` (evidencia débil): NUNCA se proponen.
_H1_HISTORICAL_PREFIXES = (
    'REVERTIDO-', 'ANULADO-', 'PURGADO-', 'HUERFANO-PROTEGIDO-',
)


class MadenatGuiaProcessingHistorical(models.Model):
    _inherit = 'madenat.guia.processing'

    can_historical_reverse = fields.Boolean(
        string='Puede reversión histórica asistida (H1)',
        compute='_compute_can_historical_reverse',
        help='True solo si la guía es producción histórica elegible para H1: '
             'no granel, sin consumo BT-04 y sin producción atribuida por la '
             'llave fuerte G2.')

    @api.depends('state', 'tipo_recepcion', 'consumption_picking_id', 'lot_ids')
    def _compute_can_historical_reverse(self):
        for rec in self:
            rec.can_historical_reverse = rec._h1_is_historical_production()

    # ══════════════════════════════════════════════════════════════════════
    # ELEGIBILIDAD (solo producción histórica no-granel, sin BT-04 ni FK G2)
    # ══════════════════════════════════════════════════════════════════════
    def _h1_is_historical_production(self):
        """H1 aplica solo a producción histórica no-granel.

        Excluye explícitamente: granel/SV, consumo BT-04 (`consumption_picking_id`)
        y producción con llave fuerte G2 (que pertenece a G3).
        """
        self.ensure_one()
        if self.tipo_recepcion == 'granel':
            return False
        if self.consumption_picking_id:
            return False
        if self._attributed_production_pickings():
            return False
        return True

    # ══════════════════════════════════════════════════════════════════════
    # PROPUESTA DE CANDIDATOS (señales, NUNCA atribución automática)
    # ══════════════════════════════════════════════════════════════════════
    def _h1_origin_candidates(self):
        """Pickings cuyo `origin` textual coincide con el nombre de la guía."""
        self.ensure_one()
        return self.env['stock.picking'].search([('origin', '=', self.name)])

    def _h1_lot_candidates(self):
        """Pickings cuyas move lines referencian lotes vinculados a la guía."""
        self.ensure_one()
        if not self.lot_ids:
            return self.env['stock.picking']
        return self.env['stock.picking'].search([
            ('move_line_ids.lot_id', 'in', self.lot_ids.ids)])

    def _h1_collect_candidates(self):
        """Lista de dicts (uno por picking candidato) para las líneas del wizard."""
        self.ensure_one()
        candidates = self._h1_origin_candidates() | self._h1_lot_candidates()
        return [self._h1_classify_candidate(picking) for picking in candidates]

    @api.model
    def _h1_historical_prefix(self, text):
        value = (text or '').strip().upper()
        return any(value.startswith(prefix) for prefix in _H1_HISTORICAL_PREFIXES)

    def _h1_picking_has_return(self, picking):
        """True si ya existe un retorno técnico DONE para el picking."""
        self.ensure_one()
        if not picking:
            return False
        if self.env['stock.picking'].search_count([
                ('return_id', '=', picking.id), ('state', '=', 'done')]):
            return True
        moves = picking.move_ids
        if moves and self.env['stock.move'].search_count([
                ('origin_returned_move_id', 'in', moves.ids),
                ('state', '!=', 'cancel')]):
            return True
        return False

    def _h1_exclusion_reason(self, picking):
        """Motivo de exclusión dura (categoría C) o cadena vacía si es proponible."""
        self.ensure_one()
        if picking.guia_processing_id:
            return 'Pertenece a G3 (llave fuerte G2); use la reversión G3.'
        if picking.reception_id:
            return 'Recepción normal (no es producción de guía).'
        if picking.state != 'done':
            return 'Albarán no validado (no reversible).'
        if picking.picking_type_code != 'incoming':
            return 'No es ingreso de producción (incoming).'
        if picking.company_id and picking.company_id != self.env.company:
            return 'Compañía ajena.'
        if self._h1_historical_prefix(picking.origin):
            return 'Origen con prefijo histórico (evidencia débil).'
        if picking.return_id:
            return 'Es un retorno (return_id).'
        if picking.move_ids.filtered(lambda m: m.origin_returned_move_id):
            return 'Contiene movimientos de retorno.'
        if not picking.move_ids.filtered(lambda m: (m.quantity or 0) > 0):
            return 'Sin cantidad realizada.'
        if self._h1_picking_has_return(picking):
            return 'Ya existe retorno para este albarán (idempotencia).'
        return ''

    def _h1_classify_candidate(self, picking):
        """Clasifica un candidato en A/B/C mostrando señales (sin atribuir).

        - A: origen exacto + cobertura total de lotes de la guía + incoming/done
          + sin retorno ⇒ propuesto y preseleccionable.
        - B: una sola señal media / evidencia parcial ⇒ visible, NO preseleccionado.
        - C: excluido o sin evidencia ⇒ no proponible.
        """
        self.ensure_one()
        signals = []
        exclusion = self._h1_exclusion_reason(picking)
        origin_exact = (
            (picking.origin or '').strip() == (self.name or '').strip())
        if origin_exact:
            signals.append('origen exacto')
        picking_lots = picking.move_line_ids.mapped('lot_id')
        guia_lot_ids = set(self.lot_ids.ids)
        picking_lot_ids = set(picking_lots.ids)
        lot_full = bool(guia_lot_ids) and picking_lot_ids == guia_lot_ids
        lot_partial = bool(guia_lot_ids) and bool(picking_lot_ids & guia_lot_ids)
        if lot_full:
            signals.append('cobertura total de lotes de la guía')
        elif lot_partial:
            signals.append('cobertura parcial de lotes de la guía')
        category, eligible, selected = 'C', False, False
        if not exclusion:
            if origin_exact and lot_full:
                category, eligible, selected = 'A', True, True
            elif origin_exact or lot_partial:
                category, eligible = 'B', True
        return {
            'picking_id': picking.id,
            'category': category,
            'eligible': eligible,
            'selected': selected,
            'product_names': ', '.join(sorted({
                name for name in picking.move_ids.mapped(
                    'product_id.display_name') if name})),
            'lot_names': '\n'.join(sorted(set(picking_lots.mapped('name')))),
            'move_count': len(picking.move_ids),
            'total_qty': sum(picking.move_ids.mapped('quantity')),
            'signal_summary': ', '.join(signals) or '—',
            'exclusion_reason': exclusion,
        }

    def _h1_warnings(self):
        """Advertencias no bloqueantes (contexto operativo)."""
        self.ensure_one()
        warnings = []
        if self.tipo_recepcion == 'granel':
            warnings.append(
                'Guía por Volumen (granel): H1 no aplica (flujo SV).')
        if self.consumption_picking_id:
            warnings.append(
                'Guía con consumo a proceso BT-04: use la reapertura G1.')
        if self._attributed_production_pickings():
            warnings.append(
                'Producción atribuida por llave fuerte G2: use la reversión '
                'G3 (G1).')
        if self.lot_ids and 'lumber.container' in self.env:
            contenedores = self.env['lumber.container'].search(
                [('lot_ids', 'in', self.lot_ids.ids)])
            if contenedores:
                warnings.append(
                    '📦 %d lote(s) en contenedor/consolidados; no se '
                    'modifican.' % len(contenedores))
        quants_externos = self.env['stock.quant'].search([
            ('lot_id', 'in', self.lot_ids.ids), ('quantity', '>', 0),
            ('location_id.usage', 'not in',
             ['internal', 'inventory', 'production'])])
        if quants_externos:
            warnings.append(
                '🚚 Stock en ubicación externa detectado; no se modifica.')
        albaranes_externos = self.env['stock.picking'].search([
            ('origin', '=', self.name), ('state', '=', 'done'),
            ('location_dest_id.usage', '!=', 'internal')])
        if albaranes_externos:
            warnings.append(
                '📤 Albarán(es) con salida externa validada (%s); no se '
                'modifican.' % ', '.join(albaranes_externos.mapped('name')))
        return warnings

    # ══════════════════════════════════════════════════════════════════════
    # EJECUCIÓN: retorno TOTAL nativo por picking seleccionado (H1)
    # ══════════════════════════════════════════════════════════════════════
    def _h1_confirm_historical_reverse(self, pickings, reason=None):
        """Revierte TOTALMENTE los pickings seleccionados (revalidando antes).

        No cambia el estado de la guía ni limpia `lot_ids`: la reapertura
        documental sigue siendo responsabilidad exclusiva de G1.
        """
        self.ensure_one()
        reason = (reason or '').strip()
        if not self._h1_is_historical_production():
            raise UserError(_(
                'H1 no aplica a esta guía (granel/SV, consumo BT-04 o '
                'producción con llave fuerte G2). Use el flujo correspondiente.'))
        to_reverse = self.env['stock.picking']
        skipped = []
        for picking in pickings:
            why = self._h1_exclusion_reason(picking)
            if why:
                skipped.append((picking, why))
                continue
            to_reverse |= picking
        results = []
        for picking in to_reverse:
            return_picking = self._h1_reverse_picking_total(picking)
            if return_picking:
                results.append((picking, return_picking))
        self._h1_register_audit(reason, to_reverse, results, skipped)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.guia.processing',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _h1_reverse_picking_total(self, picking):
        """Retorno TOTAL nativo (salida inversa) preservando la historia.

        - Nativo: crea picking/move/move.line invertidos y valida con API.
        - Preserva producto, UoM, lote, ubicaciones, owner, paquete y compañía.
        - Idempotente vía `return_id`/`origin_returned_move_id`. Nunca escribe
          quants directamente ni borra registros originales.
        """
        self.ensure_one()
        if not picking or picking.state != 'done':
            return self.env['stock.picking']
        existing = self.env['stock.picking'].search([
            ('return_id', '=', picking.id), ('state', '=', 'done')], limit=1)
        if existing:
            return existing
        moves_done = picking.move_ids.filtered(
            lambda m: m.state == 'done' and not m.returned_move_ids.filtered(
                lambda r: r.state == 'done'))
        if not moves_done:
            return self.env['stock.picking']
        warehouse = picking.picking_type_id.warehouse_id
        return_type = (
            picking.picking_type_id.return_picking_type_id
            or (warehouse.out_type_id if warehouse else False)
            or self.env.ref('stock.picking_type_out', raise_if_not_found=False))
        if not return_type:
            raise UserError(_(
                'No existe un tipo de operación de salida para revertir el '
                'albarán %s.') % picking.name)
        return_picking = self.env['stock.picking'].create({
            'picking_type_id': return_type.id,
            'partner_id': picking.partner_id.id,
            'origin': 'Return of %s' % picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': picking.location_id.id,
            'company_id': picking.company_id.id,
        })
        for move in moves_done:
            qty = move.quantity or move.product_uom_qty
            return_move = self.env['stock.move'].create({
                'name': 'Return of %s' % move.name,
                'product_id': move.product_id.id,
                'product_uom_qty': qty,
                'product_uom': move.product_uom.id,
                'picking_id': return_picking.id,
                'location_id': move.location_dest_id.id,
                'location_dest_id': move.location_id.id,
                'company_id': move.company_id.id,
                'origin_returned_move_id': move.id,
                'to_refund': True,
            })
            for line in move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': return_move.id,
                    'picking_id': return_picking.id,
                    'product_id': line.product_id.id,
                    'lot_id': line.lot_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'location_id': return_move.location_id.id,
                    'location_dest_id': return_move.location_dest_id.id,
                    'owner_id': line.owner_id.id,
                    'package_id': line.package_id.id,
                    'result_package_id': line.result_package_id.id,
                })
        return_picking.action_confirm()
        return_picking.action_assign()
        return_picking.with_context(
            skip_backorder=True, skip_immediate=True,
            force_validate=True, immediate_transfer=True,
        ).button_validate()
        return_picking.return_id = picking.id
        _logger.info(
            '✅ H1 reversión histórica: %s → %s (guía %s).',
            picking.name, return_picking.name, self.name)
        return return_picking

    # ══════════════════════════════════════════════════════════════════════
    # AUDITORÍA (AD-88) + ACCIÓN PÚBLICA
    # ══════════════════════════════════════════════════════════════════════
    def _h1_register_audit(self, reason, reversed_pickings, results, skipped):
        """Snapshot + hash + `madenat.audit.log` (deviation) + chatter."""
        self.ensure_one()
        snapshot = json.dumps({
            'h1': True,
            'guia': self.name,
            'guia_id': self.id,
            'state': self.state,
            'tipo_recepcion': self.tipo_recepcion,
            'reason': reason,
            'selection': [
                {'picking': p.name, 'origin': p.origin}
                for p in reversed_pickings],
            'returns': [
                {'origin': p.name, 'return': r.name} for p, r in results],
            'skipped': [
                {'picking': p.name, 'why': why} for p, why in skipped],
            'warnings': self._h1_warnings(),
            'lots': self.lot_ids.mapped('name'),
            'user': self.env.user.id,
        }, sort_keys=True, default=str)
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.id,
            'action_type': 'deviation',
            'description': '[H1-REVERSIÓN-HISTÓRICA] Motivo: %s'
                           % (reason or '(sin efecto físico)'),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })
        self.message_post(body=_(
            '↩️ <strong>Reversión histórica asistida (H1)</strong><br/>'
            'Motivo: %(reason)s<br/>'
            'Seleccionados: %(sel)s<br/>'
            'Retornos: %(ret)s<br/>'
            'Omitidos: %(skip)s<br/>'
            'Advertencias: %(warn)s'
        ) % {
            'reason': reason or '(sin efecto físico)',
            'sel': ', '.join(reversed_pickings.mapped('name')) or '-',
            'ret': ', '.join(r.name for _p, r in results) or '-',
            'skip': ', '.join(
                '%s (%s)' % (p.name, why) for p, why in skipped) or '-',
            'warn': ' | '.join(self._h1_warnings()) or '-',
        })

    def action_open_historical_reverse_wizard(self):
        """Abre el asistente H1 (acción pública secundaria, aditiva a G1)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reversión histórica asistida'),
            'res_model': 'madenat.guia.processing.historical.reverse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref(
                'madenat_lumber_core.'
                'view_madenat_guia_processing_historical_reverse_wizard_form'
            ).id,
            'context': {'default_guia_processing_id': self.id},
        }
