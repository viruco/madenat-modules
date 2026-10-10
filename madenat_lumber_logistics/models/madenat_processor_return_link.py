# -*- coding: utf-8 -*-
"""Bloque A/B/C — Relación de conciliación envío↔retorno (CANON/19 §19.11).

Vínculo **persistente** y **DOCUMENTAL** entre:

* el **envío a procesador** — transferencia interna nativa validada hacia
  ``Procesadores/<X>`` (I1, ``stock.picking``; ``location_dest_id`` con
  ``processor_partner_id``);
* el **retorno** — guía de procesados (``madenat.guia.processing``) con sus
  etiquetas procesadas;
* (opcional) la **imputación documental SV** (``madenat.sv.imputation``, I2).

Principios (CANON/19 §3/§19.10):
* **No** crea ni modifica ``stock.quant``/``stock.move``/``stock.picking`` ni
  el ledger ``madenat.sv.operation``: es **trazabilidad y estado** de la
  relación, no un movimiento ni un saldo nuevo (D-I2-12 extendido).
* **No** sustituye la imputación SV (C). La imputación sigue siendo la
  asignación documental; esta relación sólo declara **qué envío atiende cada
  retorno** (D).
* Una relación en ``draft`` **no** equivale a conciliación aplicada.
* Historia **append-only**: una relación aplicada no se elimina; se reversa
  (``reversed``) conservando usuario, fecha y motivo.
* **No** calcula rendimiento ni merma: las magnitudes (enviado/retornado/
  imputado) se muestran **separadas**, sin resta (Bloque D pendiente).
"""
import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_round

# Estados ACTIVOS (VIGENTES) de la relación: cuentan para la unicidad y para el
# estado derivado del envío/retorno. `reversed` es historia (append-only).
LINK_ACTIVE_STATES = ('draft', 'linked')
LINK_STATE_DRAFT = 'draft'
LINK_STATE_LINKED = 'linked'
LINK_STATE_REVERSED = 'reversed'

# Grupos funcionales vigentes (sin crear grupos nuevos — CANON/19 §9).
GROUP_OPERACIONES = 'madenat_lumber_core.group_madenat_operaciones'
GROUP_JEFATURA = 'madenat_lumber_core.group_madenat_jefatura_operaciones'
GROUP_GERENCIA = 'madenat_lumber_core.group_madenat_gerencia'

# Campos escribibles sobre una relación ya `linked` (inmutabilidad append-only).
LINK_LINKED_WRITABLE = frozenset([
    'state', 'reversal_reason', 'reversal_date', 'reversed_by_id',
    'reversed_link_id', 'snapshot_json', 'audit_hash', 'message_ids',
    'origin_link_id', 'imputation_id',
])





class MadenatProcessorReturnLink(models.Model):
    """Relación de conciliación envío↔retorno (Bloque A, CANON/19 §19.11)."""

    _name = 'madenat.processor.return.link'
    _description = 'Relación de conciliación envío–retorno (procesador)'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Relación', required=True, copy=False, readonly=True,
        default=lambda self: (
            self.env['ir.sequence'].next_by_code(
                'madenat.processor.return.link') or _('Nueva')))
    company_id = fields.Many2one(
        'res.company', string='Compañía', index=True,
        related='picking_id.company_id', store=True)
    picking_id = fields.Many2one(
        'stock.picking', string='Envío a procesador', required=True,
        ondelete='restrict', index=True, copy=False,
        help='Transferencia interna validada hacia «Procesadores/<X>» (I1) que '
             'atiende este retorno.')
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía de retorno', required=True,
        ondelete='restrict', index=True, copy=False,
        help='Guía de procesados (retorno) que se asocia al envío.')
    imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación documental SV',
        ondelete='set null', index=True, copy=False,
        help='Imputación SV (I2) con la que se registra este retorno. Opcional: '
             'la relación puede existir antes de la imputación.')
    processor_id = fields.Many2one(
        'res.partner', string='Procesador', index=True,
        related='picking_id.location_dest_id.processor_partner_id',
        store=True,
        help='Procesador titular de la ubicación destino del envío.')
    state = fields.Selection(
        [
            ('draft', 'Propuesta (sin registrar)'),
            ('linked', 'Conciliación registrada'),
            ('reversed', 'Revertida'),
        ],
        string='Estado', required=True, default='draft', index=True,
        tracking=True,
        help='«Conciliación registrada» declara el vínculo envío↔retorno; NO '
             'afirma igualdad cuantitativa (conciliación cuantitativa: Bloque D '
             'pendiente).')
    reason = fields.Text(
        string='Motivo',
        help='Observaciones de la relación. Obligatorio al reversar.')
    note = fields.Text(string='Nota operativa')

    # Fechas/espejo (solo lectura): trazabilidad, NUNCA usadas para restar.
    shipment_date = fields.Datetime(
        string='Fecha de envío', related='picking_id.date_done',
        store=True, readonly=True)
    return_date = fields.Date(
        string='Fecha de emisión (retorno)',
        related='guia_processing_id.date_emission', store=True, readonly=True)

    # Magnitudes SEPARADAS (sin resta — Bloque D pendiente).
    shipment_volume_m3 = fields.Float(
        string='Volumen enviado (m³)', digits=(16, 3),
        compute='_compute_volumes', store=False,
        help='Σ cantidad de las líneas del envío. Magnitud FÍSICA separada; no '
             'se resta contra el volumen retornado.')
    return_nominal_m3 = fields.Float(
        string='Volumen nominal del retorno (m³)', digits=(16, 3),
        compute='_compute_volumes', store=False,
        help='Σ volumen nominal de las etiquetas procesadas del retorno. '
             'Magnitud DOCUMENTAL separada; no se resta contra el enviado.')

    # Autoría / historia (append-only).
    linked_by_id = fields.Many2one(
        'res.users', string='Registrada por', readonly=True)
    linked_date = fields.Datetime(string='Fecha de registro', readonly=True)
    reversed_by_id = fields.Many2one(
        'res.users', string='Revertida por', readonly=True)
    reversal_date = fields.Datetime(string='Fecha de reversa', readonly=True)
    reversal_reason = fields.Text(string='Motivo de reversa')
    origin_link_id = fields.Many2one(
        'madenat.processor.return.link', string='Relación de origen',
        ondelete='restrict', index=True, copy=False,
        help='Relación revertida que esta nueva relación corrige (historia).')
    reversed_link_id = fields.Many2one(
        'madenat.processor.return.link', string='Revertida por (relación)',
        ondelete='restrict', index=True, copy=False,
        help='Relación que revirtió/reemplazó a esta (historia).')
    snapshot_json = fields.Text(string='Snapshot JSON', readonly=True, copy=False)
    audit_hash = fields.Char(string='Firma SHA-256', readonly=True, copy=False)

    _sql_constraints = [
        ('processor_return_link_name_unique',
         'unique(name)',
         'El identificador de la relación de conciliación debe ser único.'),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # COMPUTOS
    # ══════════════════════════════════════════════════════════════════════
    @api.depends('picking_id', 'picking_id.move_line_ids.quantity',
                 'guia_processing_id', 'guia_processing_id.lot_ids')
    def _compute_volumes(self):
        Imputation = self.env['madenat.sv.imputation']
        for rec in self:
            rec.shipment_volume_m3 = float_round(
                sum(rec.picking_id.move_line_ids.mapped('quantity')),
                precision_digits=3)
            lots = rec.guia_processing_id.lot_ids.filtered(
                lambda l: l.lot_flow_type != 'volume')
            rec.return_nominal_m3 = float_round(
                sum(Imputation._i2_lot_nominal_m3(lot) for lot in lots),
                precision_digits=3)

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS DE ELEGIBILIDAD (dominio único reutilizable)
    # ══════════════════════════════════════════════════════════════════════
    @api.model
    def _guia_processor(self, guia):
        """Procesador del retorno (orden toll primero, luego partner)."""
        if not guia:
            return self.env['res.partner']
        if guia.toll_order_id and guia.toll_order_id.processor_id:
            return guia.toll_order_id.processor_id
        if guia.partner_id and guia.partner_id.is_processor:
            return guia.partner_id
        return self.env['res.partner']

    @api.model
    def _eligible_shipment_pickings(self, guia, processor=None):
        """Envíos ELEGIBLES para el retorno: transferencias internas VALIDADAS
        hacia la ubicación de un procesador (``processor_partner_id``).

        Si se indica un procesador, se limita a ese procesador («siempre el
        procesador correspondiente», CANON/19 §5). **No** excluye envíos ya
        relacionados: un envío admite varios retornos parciales (regla
        propuesta, §19.11).
        """
        if not processor:
            processor = self._guia_processor(guia)
        domain = [
            ('state', '=', 'done'),
            ('location_dest_id.processor_partner_id', '!=', False),
            '|', ('company_id', '=', self.env.company.id),
            ('company_id', '=', False),
        ]
        if processor:
            domain.append(
                ('location_dest_id.processor_partner_id', '=', processor.id))
        return self.env['stock.picking'].search(domain, order='date_done desc')

    def _active_link(self):
        """Relación activa (draft/linked) de este par envío↔retorno, o vacío."""
        self.ensure_one()
        return self.search([
            ('picking_id', '=', self.picking_id.id),
            ('guia_processing_id', '=', self.guia_processing_id.id),
            ('state', 'in', LINK_ACTIVE_STATES),
        ], limit=1)

    @api.model
    def _get_or_create_link(self, picking, guia, imputation=None):
        """Relación activa idempotente para el par envío↔retorno."""
        existing = self.search([
            ('picking_id', '=', picking.id),
            ('guia_processing_id', '=', guia.id),
            ('state', 'in', LINK_ACTIVE_STATES),
        ], limit=1)
        if existing:
            if imputation and existing.imputation_id != imputation:
                existing.imputation_id = imputation.id
            return existing
        return self.create({
            'picking_id': picking.id,
            'guia_processing_id': guia.id,
            'imputation_id': imputation.id if imputation else False,
        })


    # ══════════════════════════════════════════════════════════════════════
    # VALIDACIONES (reglas duras de integridad de la relación)
    # ══════════════════════════════════════════════════════════════════════
    @api.constrains('picking_id', 'guia_processing_id', 'state')
    def _check_unique_active_link(self):
        for rec in self:
            if rec.state not in LINK_ACTIVE_STATES:
                continue
            others = self.search_count([
                ('picking_id', '=', rec.picking_id.id),
                ('guia_processing_id', '=', rec.guia_processing_id.id),
                ('state', 'in', LINK_ACTIVE_STATES),
                ('id', '!=', rec.id),
            ])
            if others:
                raise ValidationError(_(
                    'Ya existe una relación de conciliación vigente entre el '
                    'envío %(p)s y el retorno %(g)s. No se duplica (CANON/19 '
                    '§19.11).') % {
                    'p': rec.picking_id.name or rec.picking_id.id,
                    'g': rec.guia_processing_id.name or rec.guia_processing_id.id,
                })

    @api.constrains('picking_id')
    def _check_shipment_is_processor_shipment(self):
        for rec in self:
            if not rec.picking_id:
                continue
            dest = rec.picking_id.location_dest_id
            if not dest.processor_partner_id:
                raise ValidationError(_(
                    'El traslado %s no es un «envío a procesador»: su destino '
                    'no es la ubicación de un procesador.') % (
                    rec.picking_id.name or rec.picking_id.id))

    @api.constrains('picking_id', 'guia_processing_id')
    def _check_processor_consistency(self):
        for rec in self:
            if not rec.processor_id or not rec.guia_processing_id:
                continue
            guia_processor = rec._guia_processor(rec.guia_processing_id)
            if guia_processor and guia_processor != rec.processor_id:
                raise ValidationError(_(
                    'El envío es a «%(env)s» pero el retorno corresponde a '
                    '«%(ret)s». La relación se limita al procesador '
                    'correspondiente (CANON/19 §5).') % {
                    'env': rec.processor_id.name,
                    'ret': guia_processor.name,
                })


    # ══════════════════════════════════════════════════════════════════════
    # PERMISOS (ORMs/RPC, no sólo botones) — CANON/19 §9/§19.11
    # ══════════════════════════════════════════════════════════════════════
    def _link_check_apply_permission(self):
        user = self.env.user
        if not (user.has_group(GROUP_OPERACIONES)
                or user.has_group(GROUP_JEFATURA)
                or user.has_group(GROUP_GERENCIA)):
            raise AccessError(_(
                'Solo Operaciones o Jefatura de Operaciones pueden registrar '
                'la conciliación envío–retorno (CANON/19 §9).'))

    def _link_check_reverse_permission(self):
        user = self.env.user
        if not (user.has_group(GROUP_JEFATURA)
                or user.has_group(GROUP_GERENCIA)):
            raise AccessError(_(
                'Solo Jefatura de Operaciones o Gerencia pueden reversar la '
                'conciliación envío–retorno (CANON/19 §9).'))

    # ══════════════════════════════════════════════════════════════════════
    # EVIDENCIA FIRMADA (política AD-79/AD-80) — append-only
    # ══════════════════════════════════════════════════════════════════════
    def _link_build_snapshot(self):
        self.ensure_one()
        payload = {
            'name': self.name,
            'picking': self.picking_id.name or False,
            'picking_id': self.picking_id.id or False,
            'guia': self.guia_processing_id.name or False,
            'guia_id': self.guia_processing_id.id or False,
            'imputation': self.imputation_id.name or False,
            'processor': self.processor_id.name or False,
            'state': self.state,
            'shipment_volume_m3': round(self.shipment_volume_m3, 3),
            'return_nominal_m3': round(self.return_nominal_m3, 3),
            'user': self.env.user.id,
        }
        return json.dumps(payload, sort_keys=True)

    def _link_audit(self, action, snapshot):
        self.ensure_one()
        self.env['madenat.audit.log'].sudo().create({
            'action_type': action,
            'guia_processing_id': self.guia_processing_id.id,
            'description': '%s — envío %s ↔ retorno %s' % (
                self.name or '', self.picking_id.name or '',
                self.guia_processing_id.name or ''),
            'batch_id': self.name,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })


    # ══════════════════════════════════════════════════════════════════════
    # ACCIONES (registrar / reversar)
    # ══════════════════════════════════════════════════════════════════════
    def _link_validate_payload(self):
        self.ensure_one()
        if not self.picking_id or not self.guia_processing_id:
            raise UserError(_('La relación requiere un envío y un retorno.'))
        if not self.processor_id:
            raise UserError(_(
                'El envío no tiene un procesador identificado; no se puede '
                'registrar la conciliación.'))
        if self.guia_processing_id.service_return_confirmation != 'yes':
            raise UserError(_(
                'Solo se registra la conciliación cuando la guía de retorno '
                'está marcada como retorno de servicio ("Sí"). Identifique la '
                'guía y vuelva a intentarlo.'))

    def action_link(self):
        """Registra la relación envío↔retorno. Documental, idempotente."""
        for rec in self:
            if rec.state == 'linked':
                continue  # idempotente
            if rec.state == 'reversed':
                raise UserError(_(
                    'Una relación revertida no puede volver a registrarse; '
                    'cree una nueva relación de corrección (append-only).'))
            rec._link_check_apply_permission()
            rec._link_validate_payload()
            snapshot = rec._link_build_snapshot()
            rec.write({
                'state': 'linked',
                'linked_by_id': self.env.user.id,
                'linked_date': fields.Datetime.now(),
                'snapshot_json': snapshot,
                'audit_hash': hashlib.sha256(
                    snapshot.encode('utf-8')).hexdigest(),
            })
            rec._link_audit('processor_return_link', snapshot)
        return True

    def action_back_to_draft(self):
        for rec in self:
            if rec.state != 'linked':
                raise UserError(_(
                    'Solo una relación registrada puede volver a propuesta.'))
            rec.write({'state': 'draft'})
        return True

    def action_reverse(self):
        """Reversa la relación: estado `reversed`; historia intacta."""
        for rec in self:
            if rec.state != 'linked':
                raise UserError(_(
                    'Solo una relación registrada puede reversarse.'))
            rec._link_check_reverse_permission()
            if not (rec.reversal_reason or rec.reason):
                raise UserError(_(
                    'Indique el motivo de la reversa (trazabilidad).'))
            snapshot = rec._link_build_snapshot()
            rec.write({
                'state': 'reversed',
                'reversed_by_id': self.env.user.id,
                'reversal_date': fields.Datetime.now(),
                'reversal_reason': rec.reversal_reason or rec.reason,
                'snapshot_json': snapshot,
                'audit_hash': hashlib.sha256(
                    snapshot.encode('utf-8')).hexdigest(),
            })
            rec._link_audit('processor_return_link_reverse', snapshot)
        return True

    # ══════════════════════════════════════════════════════════════════════
    # INMUTABILIDAD APPEND-ONLY
    # ══════════════════════════════════════════════════════════════════════
    def write(self, vals):
        for rec in self:
            if rec.state == 'linked':
                forbidden = set(vals) - LINK_LINKED_WRITABLE
                if forbidden:
                    raise UserError(_(
                        'La relación registrada %s es inmutable. Corrija '
                        'mediante reversa (append-only).') % rec.name)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('linked', 'reversed'):
                raise UserError(_(
                    'No se puede eliminar una relación registrada o reversada: '
                    'la historia es append-only.'))
        return super().unlink()



class StockPicking(models.Model):
    """Vista inversa del envío: qué retornos lo atienden (Bloque A)."""

    _inherit = 'stock.picking'

    madenat_processor_return_link_ids = fields.One2many(
        'madenat.processor.return.link', 'picking_id',
        string='Relaciones de retorno (procesador)')
    madenat_return_link_state = fields.Selection(
        [
            ('no_return', 'Sin retorno asociado'),
            ('proposed', 'Retorno propuesto (sin registrar)'),
            ('linked', 'Retorno registrado'),
            ('reversed', 'Retorno revertido'),
        ],
        string='Estado de conciliación (retorno)', compute='_compute_return_link_state',
        help='Estado basado en las RELACIONES existentes; NO es una '
             'conciliación cuantitativa (Bloque D pendiente).')
    madenat_shipment_volume_m3 = fields.Float(
        string='Volumen enviado (m³)', digits=(16, 3),
        compute='_compute_shipment_volume', store=False,
        help='Σ cantidad de las líneas de este envío (magnitud FÍSICA; no se '
             'resta contra el retorno).')

    @api.depends('madenat_processor_return_link_ids.state')
    def _compute_return_link_state(self):
        for picking in self:
            links = picking.madenat_processor_return_link_ids
            if links.filtered(lambda l: l.state == 'linked'):
                state = 'linked'
            elif links.filtered(lambda l: l.state == 'draft'):
                state = 'proposed'
            elif links:
                state = 'reversed'
            else:
                state = 'no_return'
            picking.madenat_return_link_state = state

    @api.depends('move_line_ids.quantity')
    def _compute_shipment_volume(self):
        for picking in self:
            picking.madenat_shipment_volume_m3 = float_round(
                sum(picking.move_line_ids.mapped('quantity')),
                precision_digits=3)


class MadenatGuiaProcessingReturnLink(models.Model):
    """Vista inversa del retorno: qué envíos lo atienden (Bloque A)."""

    _inherit = 'madenat.guia.processing'

    processor_return_link_ids = fields.One2many(
        'madenat.processor.return.link', 'guia_processing_id',
        string='Relaciones envío–retorno')
    processor_return_link_state = fields.Selection(
        [
            ('no_return', 'Sin envío asociado'),
            ('proposed', 'Envío propuesto (sin registrar)'),
            ('linked', 'Envío registrado'),
            ('reversed', 'Envío revertido'),
        ],
        string='Estado de conciliación (envío)',
        compute='_compute_processor_return_link_state',
        help='Estado basado en las RELACIONES existentes; NO es una '
             'conciliación cuantitativa (Bloque D pendiente).')

    @api.depends('processor_return_link_ids.state')
    def _compute_processor_return_link_state(self):
        for guia in self:
            links = guia.processor_return_link_ids
            if links.filtered(lambda l: l.state == 'linked'):
                state = 'linked'
            elif links.filtered(lambda l: l.state == 'draft'):
                state = 'proposed'
            elif links:
                state = 'reversed'
            else:
                state = 'no_return'
            guia.processor_return_link_state = state


class MadenatSvImputationReturnLink(models.Model):
    """La imputación documental SV enlaza los envíos que atiende (Bloque A/B)."""

    _inherit = 'madenat.sv.imputation'

    return_link_ids = fields.One2many(
        'madenat.processor.return.link', 'imputation_id',
        string='Envíos a procesador (retorno)')

    def _sync_return_links(self, pickings):
        """Sincroniza (idempotente) las relaciones de la guía con `pickings`.

        * Crea/reutiliza relaciones ACTIVAS para los envíos seleccionados.
        * Elimina SOLO las relaciones en ``draft`` que ya no estén
          seleccionadas (las ``linked``/``reversed`` no se tocan: append-only).
        """
        Link = self.env['madenat.processor.return.link']
        for imp in self:
            pickings = pickings or self.env['stock.picking']
            selected_ids = set(pickings.ids)
            for picking in pickings:
                Link._get_or_create_link(
                    picking, imp.guia_processing_id, imputation=imp)
            for link in imp.return_link_ids.filtered(
                    lambda l: l.state == 'draft'):
                if link.picking_id.id not in selected_ids:
                    link.unlink()
        return True

    def action_link_return_links(self):
        """Registra (``draft`` → ``linked``) las relaciones en propuesta.

        Acción pública (botón del formulario y RPC). Los permisos se validan
        en cada relación (``action_link``)."""
        for imp in self:
            imp.return_link_ids.filtered(
                lambda l: l.state == 'draft').action_link()
        return True
