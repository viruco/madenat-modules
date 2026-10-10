# -*- coding: utf-8 -*-
"""I2 — Consolidación / imputación DOCUMENTAL de etiquetas procesadas contra SV.

Norma: ``CANON/19_IMPUTACION_SV_Y_PROCESADORES.md`` v1.6.0 (§4/§5/§6/§7/§16) y
**AD-91** (``04_DECISION_LOG.md`` v12.16.0, D-I2-11..D-I2-19).

**I2 es documental.** Este módulo:

* **NO** crea ni modifica ``stock.quant``, ``stock.picking``, ``stock.move``,
  ``stock.move.line``, reservas ni transferencia alguna (D-I2-12).
* **NO** añade ``action_type='imputacion'`` al ledger ``madenat.sv.operation``.
* **NO** altera ``_sv_balance_values`` ni ``sv_available_m3``.
* Computa un **saldo documental SEPARADO** derivado exclusivamente de
  ``madenat.sv.imputation`` **aplicado/no revertido** (D-I2-13).
* **NO** registra costo (I5), merma automática, cierre ni genealogía.

Modelos (D-I2-11): ``madenat.sv.imputation`` (cabecera por guía),
``madenat.sv.imputation.line`` (etiquetas) y ``madenat.sv.imputation.sv.line``
(reparto N:M etiqueta↔SV). El ledger **no** es la cabecera.
"""
import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare

# ── Semántica de estados (única fuente; reutilizada por constraints, UI,
#    apply/reverse y pruebas — AD-91) ──────────────────────────────────────
# Estados que cuentan para el TECHO DURO por etiqueta:
#   Σ imputaciones activas/aplicadas no revertidas ≤ volumen nominal editable.
I2_ACTIVE_STATES = ('draft', 'pending', 'applied')
# Estados que cuentan para el SALDO DOCUMENTAL (aplicado / no revertido).
I2_DOCUMENTAL_STATES = ('applied',)
I2_VOLUME_PRECISION = 0.001

# Grupos funcionales vigentes (sin crear grupos nuevos — CANON/19 §9).
GROUP_OPERACIONES = 'madenat_lumber_core.group_madenat_operaciones'
GROUP_JEFATURA = 'madenat_lumber_core.group_madenat_jefatura_operaciones'
GROUP_GERENCIA = 'madenat_lumber_core.group_madenat_gerencia'

# Campos escribibles sobre una imputación ya ``applied`` (inmutabilidad D-I2-15).
I2_APPLIED_WRITABLE = frozenset([
    'state', 'reversal_date', 'reversal_reason', 'reversed_by_id',
    'reversed_imputation_id', 'snapshot_json', 'audit_hash',
    'executed_by_id', 'execution_date', 'message_ids',
])


class MadenatSvImputation(models.Model):
    """Cabecera de imputación documental por guía procesada (I2)."""

    _name = 'madenat.sv.imputation'
    _description = 'Imputación documental SV (I2)'
    _inherit = ['mail.thread', 'madenat.deviation.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Imputación', required=True, copy=False, readonly=True,
        default=lambda self: (
            self.env['ir.sequence'].next_by_code('madenat.sv.imputation')
            or _('Nueva')))
    date = fields.Date(
        string='Fecha', required=True, index=True,
        default=fields.Date.context_today)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True, index=True,
        default=lambda self: self.env.company)
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing', string='Guía de procesados',
        required=True, index=True, ondelete='restrict',
        help='Guía de procesados que origina el retorno (D-I2-15).')
    processor_id = fields.Many2one(
        'res.partner', string='Procesador', index=True,
        domain="[('is_processor', '=', True)]",
        help='Procesador del retorno. Opcional (permite registrar antes del SV).')
    processor_location_id = fields.Many2one(
        'stock.location', string='Ubicación del procesador',
        domain="[('usage', '=', 'internal')]")
    line_ids = fields.One2many(
        'madenat.sv.imputation.line', 'imputation_id', string='Etiquetas')
    sv_line_ids = fields.One2many(
        'madenat.sv.imputation.sv.line', 'imputation_id', string='Reparto SV')
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('pending', 'Pendiente'),
            ('applied', 'Aplicada'),
            ('reversed', 'Reversada'),
            ('cancelled', 'Anulada'),
        ],
        string='Estado', required=True, default='draft', index=True,
        tracking=True)
    reason = fields.Text(
        string='Motivo',
        help='Obligatorio para exceso SV-side (blando) o falta de SV '
             'candidato, mientras se respeta el techo duro de etiqueta '
             '(D-I2-16, D-I2-17).')
    deviation_flags = fields.Char(
        string='Desviaciones', compute='_compute_deviation_flags',
        store=True, readonly=True)
    documentary_key = fields.Char(
        string='Clave documental', required=True, index=True, copy=False,
        readonly=True,
        help='Clave documental propia para idempotencia estable (no picking_id).')
    snapshot_json = fields.Text(string='Snapshot JSON', readonly=True, copy=False)
    audit_hash = fields.Char(string='Firma SHA-256', readonly=True, copy=False)
    executed_by_id = fields.Many2one(
        'res.users', string='Aplicada por', readonly=True)
    execution_date = fields.Datetime(string='Fecha de aplicación', readonly=True)
    reversed_by_id = fields.Many2one(
        'res.users', string='Reversada por', readonly=True)
    reversal_date = fields.Datetime(string='Fecha de reversa', readonly=True)
    reversal_reason = fields.Text(string='Motivo de reversa')
    # Cadena de corrección (historia append-only)
    origin_imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación de origen',
        ondelete='restrict', index=True,
        help='Imputación (reversada) que esta nueva imputación corrige.')
    reversed_imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Reversada por',
        ondelete='restrict', index=True,
        help='Imputación que revirtió/reemplazó a esta (historia).')
    # Totales informativos (documentales)
    nominal_total_m3 = fields.Float(
        string='Nominal etiquetas (m³)', digits=(16, 3),
        compute='_compute_totals', store=False)
    imputed_total_m3 = fields.Float(
        string='Volumen asignado (m³)', digits=(16, 3),
        compute='_compute_totals', store=False)
    has_sv_excess = fields.Boolean(
        string='Exceso SV-side', compute='_compute_totals', store=False)

    _sql_constraints = [
        ('i2_documentary_key_unique',
         'unique(documentary_key)',
         'La clave documental de la imputación debe ser única (idempotencia).'),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # COMPUTOS
    # ══════════════════════════════════════════════════════════════════════
    @api.depends('line_ids.nominal_volume_m3', 'sv_line_ids.imputed_volume_m3',
                 'state')
    def _compute_totals(self):
        for rec in self:
            rec.nominal_total_m3 = sum(
                rec.line_ids.mapped('nominal_volume_m3'))
            rec.imputed_total_m3 = sum(
                rec.sv_line_ids.mapped('imputed_volume_m3'))
            rec.has_sv_excess = bool(rec._i2_sv_excess_lines())

    @api.depends('state', 'reason', 'line_ids', 'line_ids.processed_lot_id',
                 'sv_line_ids', 'sv_line_ids.sv_lot_id',
                 'processor_id', 'processor_location_id')
    def _compute_deviation_flags(self):
        for rec in self:
            flags = []
            if rec._i2_sv_excess_lines():
                flags.append('SV_EXCESS')
            if rec._i2_is_missing_sv_candidate():
                flags.append('NO_SV_CANDIDATE')
            rec.deviation_flags = ','.join(flags) or False

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS DE SALDO DOCUMENTAL (D-I2-13) — solo lectura; NO tocan `stock`,
    # NO reutilizan `sv_available_m3` ni `_sv_balance_values`.
    # ══════════════════════════════════════════════════════════════════════
    @api.model
    def _i2_lot_nominal_m3(self, lot):
        """Volumen nominal editable de una etiqueta (por defecto el de compra)."""
        return lot.volume_purchase_m3 or lot.volumen_m3 or 0.0

    @api.model
    def _i2_lot_active_imputed_m3(self, lot, exclude_imputation=None):
        """Σ imputado a una etiqueta en estados ACTIVOS (techo duro, D-I2-16a)."""
        domain = [('processed_lot_id', '=', lot.id),
                  ('imputation_id.state', 'in', I2_ACTIVE_STATES)]
        if exclude_imputation:
            domain.append(('imputation_id', '!=', exclude_imputation.id))
        lines = self.env['madenat.sv.imputation.line'].search(domain)
        return sum(lines.mapped('nominal_volume_m3'))

    @api.model
    def _i2_lot_documental_imputed_m3(self, lot):
        """Σ imputado DOCUMENTAL (aplicado/no revertido) a una etiqueta."""
        lines = self.env['madenat.sv.imputation.line'].search([
            ('processed_lot_id', '=', lot.id),
            ('imputation_id.state', 'in', I2_DOCUMENTAL_STATES)])
        return sum(lines.mapped('nominal_volume_m3'))

    @api.model
    def _i2_lot_documental_available_m3(self, lot):
        """Saldo documental de la etiqueta = nominal − documental imputado."""
        return (self._i2_lot_nominal_m3(lot)
                - self._i2_lot_documental_imputed_m3(lot))

    @api.model
    def _i2_sv_nominal_m3(self, sv_lot):
        return sv_lot.volume_purchase_m3 or sv_lot.volumen_m3 or 0.0

    @api.model
    def _i2_sv_documental_assigned_m3(self, sv_lot, exclude_imputation=None):
        """Σ asignado documental a un SV en estados activos (blando, D-I2-16b)."""
        domain = [('sv_lot_id', '=', sv_lot.id),
                  ('imputation_id.state', 'in', I2_ACTIVE_STATES)]
        if exclude_imputation:
            domain.append(('imputation_id', '!=', exclude_imputation.id))
        lines = self.env['madenat.sv.imputation.sv.line'].search(domain)
        return sum(lines.mapped('imputed_volume_m3'))

    @api.model
    def _i2_sv_documental_available_m3(self, sv_lot):
        """Saldo documental disponible del SV = nominal SV − asignado activo.

        Magnitud **documental propia**: no usa `sv_available_m3` ni el ledger
        `madenat.sv.operation` (AD-91, D-I2-13). Puede ser negativa.
        """
        return (self._i2_sv_nominal_m3(sv_lot)
                - self._i2_sv_documental_assigned_m3(sv_lot))

    def _i2_sv_excess_lines(self):
        """Líneas SV cuyo SV destino supera su saldo documental (blando)."""
        self.ensure_one()
        excess = self.env['madenat.sv.imputation.sv.line']
        for sv_lot in self.sv_line_ids.mapped('sv_lot_id'):
            nominal = self._i2_sv_nominal_m3(sv_lot)
            if not nominal:
                continue
            assigned = self._i2_sv_documental_assigned_m3(sv_lot)
            if float_compare(assigned, nominal,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                excess |= self.sv_line_ids.filtered(
                    lambda l: l.sv_lot_id == sv_lot)
        return excess

    # ── Candidatos SV — dominio canónico I2, CONTEXTUAL (AD-91 / CANON §10.2)
    #    Fuente única compartida por el flag `NO_SV_CANDIDATE`, la propuesta
    #    FIFO del asistente y el guard blando previo a aplicar. NO replicar el
    #    dominio en cada ruta (causa raíz del fallo T-I2-06).
    def _i2_sv_candidate_data(self, company=None, processor=None,
                              processor_location=None, processed_lots=None):
        """Candidatos SV elegibles, ordenados, con su saldo documental I2.

        Elegibilidad (decisión funcional I2):
        * ``lot_flow_type = 'volume'``;
        * visibilidad multi-company **estándar** (compañía operativa o
          ``company_id = False``), sin filtro estricto;
        * ``_i2_sv_documental_available_m3 > 0`` (magnitud documental propia;
          **nunca** ``sv_available_m3`` del ledger ni stock físico);
        * si hay ``processor_location``, exige quant interno positivo en su
          árbol; si **no** hay procesador configurado, **no** excluye.

        Prioridad (determinista): ``processor_match`` DESC,
        ``product_match`` DESC, ``create_date`` ASC, ``id`` ASC.
        Proveedor/producto **no** son filtros duros.

        Devuelve una lista de ``dict`` (uno por candidato elegible).
        """
        company = company or self.env.company
        if not processor_location and processor:
            processor_location = processor.processor_location_id
        # Visibilidad multi-company ESTÁNDAR (compañía operativa o
        # ``company_id=False``), explícita para ser determinista también bajo
        # superusuario (que bypassa record rules). Nunca filtro estricto.
        lots = self.env['stock.lot'].with_context(
            allowed_company_ids=[company.id]).search([
                ('lot_flow_type', '=', 'volume'),
                '|', ('company_id', '=', company.id),
                ('company_id', '=', False),
            ])
        processed_lots = processed_lots or self.env['stock.lot']
        processed_products = processed_lots.mapped('product_id')
        processed_subproducts = processed_lots.mapped('subproducto_id')
        Quant = self.env['stock.quant']
        data = []
        for sv in lots:
            available = self._i2_sv_documental_available_m3(sv)
            if float_compare(available, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                continue
            physical = 0.0
            if processor_location:
                quants = Quant.search([
                    ('lot_id', '=', sv.id),
                    ('location_id', 'child_of', processor_location.id),
                    ('location_id.usage', '=', 'internal'),
                ])
                physical = sum(quants.mapped('quantity'))
                if float_compare(physical, 0.0,
                                 precision_rounding=I2_VOLUME_PRECISION) <= 0:
                    continue
            data.append({
                'lot': sv,
                'nominal': self._i2_sv_nominal_m3(sv),
                'assigned': self._i2_sv_documental_assigned_m3(sv),
                'available': available,
                'physical': physical,
                'processor_match': bool(processor_location),
                'product_match': bool(
                    (sv.product_id and sv.product_id in processed_products)
                    or (sv.subproducto_id
                        and sv.subproducto_id in processed_subproducts)),
            })
        data.sort(key=lambda item: (
            not item['processor_match'],
            not item['product_match'],
            item['lot'].create_date or fields.Datetime.now(),
            item['lot'].id,
        ))
        return data

    def _i2_get_sv_candidate_data(self):
        """Candidatos elegibles para **esta** imputación (mismo contexto)."""
        self.ensure_one()
        return self._i2_sv_candidate_data(
            company=self.company_id,
            processor=self.processor_id,
            processor_location=self.processor_location_id,
            processed_lots=self.line_ids.processed_lot_id)

    def _i2_has_sv_candidate(self):
        """True si existe al menos un candidato SV elegible en el contexto."""
        self.ensure_one()
        return bool(self._i2_get_sv_candidate_data())

    def _i2_is_missing_sv_candidate(self):
        """Desviación BLANDA ``NO_SV_CANDIDATE`` (D-I2-16, decisión D).

        Existe si la imputación tiene etiquetas (``line_ids``), **no** tiene
        asignaciones (``sv_line_ids``) y **no** hay candidato elegible bajo su
        contexto. Si hay candidato elegible (aunque aún no asignado) NO se
        marca. Es advertencia no bloqueante (motivo + auditoría).
        """
        self.ensure_one()
        return bool(
            self.line_ids and not self.sv_line_ids
            and not self._i2_has_sv_candidate())

    # ══════════════════════════════════════════════════════════════════════
    # CLAVE DOCUMENTAL E IDEMPOTENCIA (D-I2-17) — sin `picking_id`.
    # ══════════════════════════════════════════════════════════════════════
    @api.model
    def _i2_build_documentary_key(self, guia, processor=None, signature=''):
        raw = 'I2|%s|%s|%s' % (
            guia.id if guia else 0,
            processor.id if processor else 0,
            signature or '')
        digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16].upper()
        return 'IMP-%s-%s' % (guia.id if guia else 0, digest)

    @api.model
    def _i2_find_work_for_guia(self, guia):
        """Imputación de TRABAJO (draft/pending) de la guía, o vacío."""
        return self.search([
            ('guia_processing_id', '=', guia.id),
            ('state', 'in', ('draft', 'pending')),
        ], limit=1)

    @api.model
    def _i2_get_or_create(self, guia, processor=None, signature=''):
        """Devuelve (sin duplicar) la imputación de trabajo de la guía.

        Idempotencia estable: si existe una imputación de trabajo, se reutiliza;
        si no, se busca por `documentary_key` (reintento) antes de crear.
        """
        work = self._i2_find_work_for_guia(guia)
        if work:
            return work
        key = self._i2_build_documentary_key(guia, processor, signature)
        existing = self.search([('documentary_key', '=', key)], limit=1)
        if existing:
            return existing
        vals = {'guia_processing_id': guia.id, 'documentary_key': key}
        if processor:
            vals['processor_id'] = processor.id
            vals['processor_location_id'] = processor.processor_location_id.id
        return self.create(vals)

    # ══════════════════════════════════════════════════════════════════════
    # CREATE / WRITE / UNLINK — inmutabilidad append-only (D-I2-15)
    # ══════════════════════════════════════════════════════════════════════
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('documentary_key'):
                guia = self.env['madenat.guia.processing'].browse(
                    vals.get('guia_processing_id'))
                processor = self.env['res.partner'].browse(
                    vals.get('processor_id'))
                vals['documentary_key'] = self._i2_build_documentary_key(
                    guia, processor,
                    signature=str(self.env['ir.sequence'].next_by_code(
                        'madenat.sv.imputation') or ''))
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if rec.state == 'applied':
                forbidden = set(vals) - I2_APPLIED_WRITABLE
                if forbidden:
                    raise UserError(_(
                        'La imputación aplicada %(name)s es inmutable. Corrija '
                        'mediante reversa y una nueva imputación (AD-91).'
                    ) % {'name': rec.name})
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('applied', 'reversed'):
                raise UserError(_(
                    'No se puede eliminar una imputación aplicada o reversada: '
                    'la historia es append-only (AD-91).'))
        return super().unlink()

    @api.constrains('guia_processing_id', 'state')
    def _check_single_work_per_guia(self):
        for rec in self:
            if rec.state in ('draft', 'pending') and rec.guia_processing_id:
                others = self.search_count([
                    ('guia_processing_id', '=', rec.guia_processing_id.id),
                    ('state', 'in', ('draft', 'pending')),
                    ('id', '!=', rec.id)])
                if others:
                    raise ValidationError(_(
                        'La guía %s ya tiene una imputación de trabajo '
                        '(borrador/pendiente). Aplíquela o anúlela antes de '
                        'crear otra (D-I2-15).'
                    ) % rec.guia_processing_id.name)

    # ══════════════════════════════════════════════════════════════════════
    # VALIDACIONES DURAS (D-I2-16a) Y CONCURRENCIA
    # ══════════════════════════════════════════════════════════════════════
    def _i2_validate_payload(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('La imputación debe tener al menos una etiqueta.'))
        for line in self.line_ids:
            if not line.processed_lot_id:
                raise UserError(_('Cada línea debe referenciar una etiqueta.'))
            if float_compare(line.nominal_volume_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                raise UserError(_(
                    'El volumen nominal de la etiqueta %s debe ser mayor que '
                    'cero.') % (line.processed_lot_id.name))
        for sline in self.sv_line_ids:
            if float_compare(sline.imputed_volume_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                raise UserError(_(
                    'El volumen imputado al SV %s debe ser mayor que cero.')
                    % (sline.sv_lot_id.name))

    def _i2_validate_hard_cap(self):
        """Techo DURO etiqueta-side: Σ activos ≤ volumen nominal editable."""
        self.ensure_one()
        for line in self.line_ids:
            lot = line.processed_lot_id
            nominal = self._i2_lot_nominal_m3(lot)
            if not nominal:
                continue
            total = self._i2_lot_active_imputed_m3(lot)
            if float_compare(total, nominal,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                raise UserError(_(
                    'Techo duro de etiqueta superado: la etiqueta %(lot)s '
                    'acumula %(total).3f m³ imputados (activos) frente a su '
                    'volumen nominal editable de %(nominal).3f m³ (D-I2-16a).'
                ) % {'lot': lot.name, 'total': total, 'nominal': nominal})

    def _i2_lock_sv_lots(self):
        """Serializa la aplicación concurrente sobre los mismos SV.

        Advisory lock por SV (namespace 2). Si otra transacción ya lo posee, se
        falla de forma **controlada** (sin escrituras parciales) en lugar de
        esperar indefinidamente.
        """
        self.ensure_one()
        for lot_id in sorted(set(self.sv_line_ids.mapped('sv_lot_id').ids)):
            self.env.cr.execute(
                'SELECT pg_try_advisory_xact_lock(%s, %s)', (2, lot_id))
            if not self.env.cr.fetchone()[0]:
                raise UserError(_(
                    'Otra operación está modificando el saldo documental de un '
                    'SV de esta imputación. La operación no fue aplicada; '
                    'actualice la información y vuelva a intentarlo.'))

    def _i2_check_apply_permission(self):
        user = self.env.user
        allowed = (user.has_group(GROUP_OPERACIONES)
                   or user.has_group(GROUP_JEFATURA)
                   or user.has_group(GROUP_GERENCIA))
        if not allowed:
            raise AccessError(_(
                'Solo Operaciones o Jefatura de Operaciones pueden aplicar la '
                'imputación documental SV (CANON/19 §9).'))

    def _i2_check_reverse_permission(self):
        user = self.env.user
        allowed = (user.has_group(GROUP_JEFATURA)
                   or user.has_group(GROUP_GERENCIA))
        if not allowed:
            raise AccessError(_(
                'Solo Jefatura de Operaciones o Gerencia pueden reversar la '
                'imputación documental SV (CANON/19 §9).'))

    # ══════════════════════════════════════════════════════════════════════
    # TRANSICIONES DE ESTADO
    # ══════════════════════════════════════════════════════════════════════
    def action_pending(self):
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise UserError(_(
                    'Solo una imputación en borrador/pendiente puede cambiarse '
                    'de estado.'))
            rec.write({'state': 'pending'})
        return True

    def action_back_to_draft(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Solo una imputación pendiente puede volver a '
                                  'borrador.'))
            rec.write({'state': 'draft'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise UserError(_(
                    'Solo una imputación en borrador/pendiente puede anularse; '
                    'una aplicada se corrige por reversa (AD-91).'))
            rec.write({'state': 'cancelled'})
        return True

    # ══════════════════════════════════════════════════════════════════════
    # APLICAR / REVERSAR (append-only; inmutabilidad de `applied`)
    # ══════════════════════════════════════════════════════════════════════
    def _i2_handle_soft_deviations(self):
        """Severidad BLANDA (AD-88 / D-I2-16b): advertir, motivar, auditar."""
        self.ensure_one()
        excess = self._i2_sv_excess_lines()
        if excess:
            self._guard_deviation(
                'I2-SV-EXCESS',
                _('El volumen asignado supera el saldo documental disponible '
                  'del SV: %s.') % ', '.join(excess.mapped('sv_lot_id.name')),
                reason=self.reason,
                extra={'svs': excess.mapped('sv_lot_id.name')})
        if self._i2_is_missing_sv_candidate():
            self._guard_deviation(
                'I2-NO-SV-CANDIDATE',
                _('La imputación registra etiquetas sin etiquetas SV '
                  'candidatas asignadas ni disponibles en su contexto '
                  '(se permite dejar constancia con motivo).'),
                reason=self.reason)

    def _i2_build_snapshot(self):
        self.ensure_one()
        payload = {
            'documentary_key': self.documentary_key,
            'guia': self.guia_processing_id.name or False,
            'guia_id': self.guia_processing_id.id or False,
            'processor': self.processor_id.name or False,
            'state': self.state,
            'etiquetas': [{
                'lot': line.processed_lot_id.name,
                'nominal': round(line.nominal_volume_m3 or 0.0, 3),
                'saldo_documental': round(
                    self._i2_lot_documental_available_m3(
                        line.processed_lot_id), 3),
            } for line in self.line_ids],
            'sv': [{
                'sv': sline.sv_lot_id.name,
                'imputado': round(sline.imputed_volume_m3 or 0.0, 3),
                'saldo_documental': round(
                    self._i2_sv_documental_available_m3(sline.sv_lot_id), 3),
            } for sline in self.sv_line_ids],
            'user': self.env.user.id,
        }
        return json.dumps(payload, sort_keys=True)

    def _i2_audit(self, action, snapshot):
        """Evento operacional firmado en `madenat.audit.log` (tipo aditivo)."""
        self.ensure_one()
        self.env['madenat.audit.log'].sudo().create({
            'action_type': action,
            'guia_processing_id': self.guia_processing_id.id,
            'description': '%s — %s (%s)' % (
                self.name or self.documentary_key,
                self.guia_processing_id.name or '',
                self.documentary_key),
            'batch_id': self.documentary_key,
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _i2_check_destination_is_service_return(self):
        """Exige que la guía DESTINO esté marcada como retorno de servicio (Sí).

        Se comprueba al APLICAR (no al guardar borrador/pendiente). No marca la
        guía automáticamente: la identificación es un acto del operador
        (decisión aprobada 2026-10-07). No altera stock, ledger ni costos.
        """
        self.ensure_one()
        if self.guia_processing_id.service_return_confirmation != 'yes':
            raise UserError(_(
                'Solo se puede aplicar una imputación SV cuando la guía destino '
                'está marcada como retorno de servicio ("Sí"). Identifique la '
                'guía (¿Es retorno de servicio? = Sí) y vuelva a intentarlo.'))

    def action_apply(self):
        """Aplica la imputación de forma DOCUMENTAL (sin efecto en stock).

        Idempotente: reintentar sobre una imputación ya aplicada no duplica
        cabecera, líneas, auditorías ni saldo documental (D-I2-17).
        """
        for rec in self:
            if rec.state == 'applied':
                continue  # idempotente: reintento sin efectos
            if rec.state in ('reversed', 'cancelled'):
                raise UserError(_(
                    'Una imputación reversada o anulada no puede aplicarse.'))
            rec._i2_check_apply_permission()
            # Destino marcado Sí (retorno de servicio): se exige al APLICAR, no
            # al guardar un borrador/pendiente (decisión aprobada 2026-10-07).
            rec._i2_check_destination_is_service_return()
            rec._i2_validate_payload()
            rec._i2_validate_hard_cap()
            rec._i2_handle_soft_deviations()
            rec._i2_lock_sv_lots()
            snapshot = rec._i2_build_snapshot()
            rec.write({
                'state': 'applied',
                'executed_by_id': self.env.user.id,
                'execution_date': fields.Datetime.now(),
                'snapshot_json': snapshot,
                'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            })
            rec._i2_audit('imputation', snapshot)
            origin = rec.origin_imputation_id
            if origin and not origin.reversed_imputation_id:
                origin.sudo().write({'reversed_imputation_id': rec.id})
        return True

    def action_reverse(self):
        """Reversa la imputación: estado `reversed`; historia intacta."""
        for rec in self:
            if rec.state != 'applied':
                raise UserError(_(
                    'Solo una imputación aplicada puede reversarse (AD-91).'))
            rec._i2_check_reverse_permission()
            snapshot = rec._i2_build_snapshot()
            rec.write({
                'state': 'reversed',
                'reversed_by_id': self.env.user.id,
                'reversal_date': fields.Datetime.now(),
                'reversal_reason': rec.reversal_reason or rec.reason,
                'snapshot_json': snapshot,
                'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            })
            rec._i2_audit('imputation_reverse', snapshot)
        return True


class MadenatSvImputationLine(models.Model):
    """Etiqueta de retorno imputada documentalmente (D-I2-15b)."""

    _name = 'madenat.sv.imputation.line'
    _description = 'Línea de imputación documental SV'

    imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación', required=True,
        ondelete='cascade', index=True)
    processed_lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta procesada', required=True,
        ondelete='restrict', index=True,
        domain="[('lot_flow_type', '!=', 'volume')]")
    nominal_volume_m3 = fields.Float(
        string='Volumen nominal (m³)', digits=(16, 3), required=True,
        help='Volumen nominal editable de la etiqueta (por defecto el de compra).')
    pieces = fields.Integer(string='Piezas')
    product_id = fields.Many2one(
        related='processed_lot_id.product_id', string='Producto', store=False)
    subproducto_id = fields.Many2one(
        related='processed_lot_id.subproducto_id', string='Subproducto',
        store=False)
    sv_allocation_ids = fields.One2many(
        'madenat.sv.imputation.sv.line', 'imputation_line_id',
        string='Reparto SV')
    etiqueta_nominal_m3 = fields.Float(
        string='Nominal referencia (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos', store=False)
    etiqueta_imputado_activo_m3 = fields.Float(
        string='Imputado activo (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos', store=False)
    etiqueta_saldo_documental_m3 = fields.Float(
        string='Saldo documental etiqueta (m³)', digits=(16, 3),
        compute='_compute_etiqueta_saldos', store=False)

    @api.depends('processed_lot_id', 'nominal_volume_m3', 'imputation_id.state')
    def _compute_etiqueta_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for line in self:
            lot = line.processed_lot_id
            line.etiqueta_nominal_m3 = Imputation._i2_lot_nominal_m3(lot)
            line.etiqueta_imputado_activo_m3 = (
                Imputation._i2_lot_active_imputed_m3(lot) if lot else 0.0)
            line.etiqueta_saldo_documental_m3 = (
                Imputation._i2_lot_documental_available_m3(lot) if lot else 0.0)

    @api.onchange('processed_lot_id')
    def _onchange_processed_lot_id(self):
        for line in self:
            if line.processed_lot_id and not line.nominal_volume_m3:
                line.nominal_volume_m3 = (
                    self.env['madenat.sv.imputation']._i2_lot_nominal_m3(
                        line.processed_lot_id))

    @api.constrains('nominal_volume_m3')
    def _check_nominal_positive(self):
        for line in self:
            if float_compare(line.nominal_volume_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                raise ValidationError(_(
                    'El volumen nominal de la etiqueta debe ser mayor que cero.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            imp = self.env['madenat.sv.imputation'].browse(
                vals.get('imputation_id'))
            if imp.state == 'applied':
                raise UserError(_(
                    'No se pueden añadir líneas a una imputación aplicada '
                    '(inmutable, AD-91).'))
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if rec.imputation_id.state == 'applied':
                raise UserError(_(
                    'No se pueden modificar líneas de una imputación aplicada '
                    '(inmutable, AD-91).'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.imputation_id.state == 'applied':
                raise UserError(_(
                    'No se pueden eliminar líneas de una imputación aplicada '
                    '(inmutable, AD-91).'))
        return super().unlink()


class MadenatSvImputationSvLine(models.Model):
    """Reparto de una etiqueta hacia un SV (N:M) (D-I2-15b)."""

    _name = 'madenat.sv.imputation.sv.line'
    _description = 'Reparto documental etiqueta→SV'

    imputation_id = fields.Many2one(
        'madenat.sv.imputation', string='Imputación', required=True,
        ondelete='cascade', index=True)
    imputation_line_id = fields.Many2one(
        'madenat.sv.imputation.line', string='Etiqueta', required=True,
        ondelete='cascade', index=True)
    sv_lot_id = fields.Many2one(
        'stock.lot', string='Etiqueta SV', required=True, ondelete='restrict',
        index=True, domain="[('lot_flow_type', '=', 'volume')]")
    imputed_volume_m3 = fields.Float(
        string='Volumen imputado (m³)', digits=(16, 3), required=True)
    sv_nominal_m3 = fields.Float(
        string='Nominal SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos', store=False)
    sv_saldo_documental_m3 = fields.Float(
        string='Saldo documental SV (m³)', digits=(16, 3),
        compute='_compute_sv_saldos', store=False)

    @api.depends('sv_lot_id', 'imputed_volume_m3', 'imputation_id.state')
    def _compute_sv_saldos(self):
        Imputation = self.env['madenat.sv.imputation']
        for sline in self:
            sv = sline.sv_lot_id
            sline.sv_nominal_m3 = (
                Imputation._i2_sv_nominal_m3(sv) if sv else 0.0)
            sline.sv_saldo_documental_m3 = (
                Imputation._i2_sv_documental_available_m3(sv) if sv else 0.0)

    @api.constrains('imputed_volume_m3')
    def _check_imputed_positive(self):
        for sline in self:
            if float_compare(sline.imputed_volume_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                raise ValidationError(_(
                    'El volumen imputado al SV debe ser mayor que cero.'))

    @api.constrains('imputation_line_id', 'imputation_id')
    def _check_same_imputation(self):
        for sline in self:
            if sline.imputation_line_id.imputation_id != sline.imputation_id:
                raise ValidationError(_(
                    'El reparto SV debe pertenecer a la misma imputación que '
                    'su línea de etiqueta.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            imp = self.env['madenat.sv.imputation'].browse(
                vals.get('imputation_id'))
            if imp.state == 'applied':
                raise UserError(_(
                    'No se pueden añadir repartos SV a una imputación aplicada '
                    '(inmutable, AD-91).'))
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if rec.imputation_id.state == 'applied':
                raise UserError(_(
                    'No se pueden modificar repartos SV de una imputación '
                    'aplicada (inmutable, AD-91).'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.imputation_id.state == 'applied':
                raise UserError(_(
                    'No se pueden eliminar repartos SV de una imputación '
                    'aplicada (inmutable, AD-91).'))
        return super().unlink()


class MadenatGuiaProcessingServiceReturn(models.Model):
    """Relación de lectura + regla de identificación de retorno de servicio.

    Añade a ``madenat.guia.processing`` (modelo del core) la relación inversa
    con sus imputaciones SV (``madenat.sv.imputation.guia_processing_id``), para
    consulta y filtro sin duplicar el dato. Vive en ``madenat_lumber_logistics``
    porque aquí es donde existe el modelo I2 (`madenat.sv.imputation`): así se
    respeta la dependencia core ← logistics y NO se introduce dependencia
    core→logistics ni circular.

    Aplica también la regla aprobada (2026-10-07): con imputaciones SV
    ``applied`` no se permite cambiar la identificación a "No" ni vaciarla; la
    corrección exige primero REVERSAR las imputaciones (mecanismo existente). No
    elimina ni altera relaciones en silencio.
    """

    _inherit = 'madenat.guia.processing'

    sv_imputation_ids = fields.One2many(
        'madenat.sv.imputation', 'guia_processing_id',
        string='Imputaciones SV')

    def write(self, vals):
        if 'service_return_confirmation' in vals:
            new_value = vals.get('service_return_confirmation')
            # Cambiar a "No" o vaciar la identificación con imputaciones
            # aplicadas leaving relaciones incoherentes: se rechaza. La
            # corrección es reversar primero (AD-91).
            if not new_value or new_value == 'no':
                for rec in self:
                    applied = rec.sv_imputation_ids.filtered(
                        lambda imp: imp.state == 'applied')
                    if applied:
                        raise UserError(_(
                            'No se puede cambiar la identificación a "No" (ni '
                            'dejarla vacía) mientras existan imputaciones SV '
                            'aplicadas en la guía. Revierta primero las '
                            'imputaciones (%s) y vuelva a intentarlo.'
                        ) % ', '.join(applied.mapped('name')))
        return super().write(vals)
