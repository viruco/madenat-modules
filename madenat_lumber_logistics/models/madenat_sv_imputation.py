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
# FASE 11 (A-1): ``state`` y TODAS las marcas de transición quedaron fuera de la
# vía pública (ver ``I2_TRANSITION_MARK_FIELDS``); sobre un ``applied`` sólo
# queda como ENTRADA el campo libre ``reason`` (texto del motivo; NO forma parte
# del snapshot firmado) y el chatter. La transición ``applied → reversed`` la
# ejecuta ``action_reverse`` (usuario + motivo) por la vía privada del modelo.
I2_APPLIED_WRITABLE = frozenset(['reason', 'edit_version', 'message_ids'])

# ── A-1 / B-1 (FASE 11, 2026-10-15) — MARCAS DE TRANSICIÓN protegidas ────────
# "Marca de transición" = el estado y los campos que PRUEBAN que la transición
# ocurrió (firma, snapshot, ejecutor, fechas, motivos y metadata de
# anulación/reversa/reapertura). Sólo los métodos OFICIALES de transición los
# escriben, y lo hacen por la vía privada ``_i2_write_protected_state``
# (``super().write``), fuera del ``write`` público. La escritura directa por
# ORM/RPC se RECHAZA con un ``UserError`` de negocio, de modo que no se puede
# fabricar un ``applied`` sin firma ni un ``cancelled`` sin rastro (A-1/B-1).
# El MOTIVO se captura como ENTRADA en el campo libre ``reason`` (o como
# parámetro de la acción) y la acción oficial lo congela en su campo de marca.
I2_TRANSITION_MARK_FIELDS = frozenset([
    'state',
    'snapshot_json', 'audit_hash',
    'executed_by_id', 'execution_date',
    'reversed_by_id', 'reversal_date', 'reversal_reason',
    'reversed_imputation_id',
    'cancelled_by_id', 'cancellation_date', 'cancellation_reason',
    'reopened_by_id', 'reopen_date', 'reopen_reason',
])
I2_PROTECTED_TRANSITION_MSG = (
    'El estado y las marcas de transición de la imputación %(name)s sólo '
    'cambian con las acciones oficiales (Aplicar, Reversar, Anular, Volver a '
    'borrador). La escritura directa de estos campos por ORM/RPC no está '
    'autorizada (AD-91 / FASE 11 A-1): usa la acción correspondiente, que '
    'registra usuario, fecha y firma.')

# ── I5 / B-2 (FASE 11) — contenido (líneas y repartos) congelado ─────────────
# Las líneas y los repartos de una imputación sólo se modifican mientras el
# documento está EN PREPARACIÓN. En un estado terminal (aplicada, reversada,
# anulada) el contenido es INMUTABLE: los caminos oficiales («Reversar» para una
# aplicada; «Volver a borrador» para una anulada) devuelven el documento a
# `draft` antes de permitir tocarlo (así lo reabierto conserva su contenido
# íntegro y no se puede alterar a posteriori lo que se aplicó o anuló).
I2_CHILD_EDITABLE_STATES = ('draft', 'pending')

# AUD-ETQ-07/09 (2026-10-12): la autorización de las transiciones protegidas
# (`cancelled → draft`, `applied → reversed`) NO usa un registro global de
# tokens. Se resolvió con una **vía privada de transición**
# (`MadenatSvImputation._i2_write_protected_state`), método `_`-prefijado que
# **no** es invocable por RPC (Odoo bloquea los métodos `_` en `call_kw`) y que
# escribe a través de `super().write`. Así se elimina de raíz cualquier ventana
# de autorización reutilizable: no hay estado compartido, ni contexto, ni token
# del cliente, ni cruce entre transacciones, hilos o procesos.

# LOCK (2026-10-12): protección contra SOBRESCRITURA de borradores.
# Campos que NO representan contenido editable del trabajo (trazabilidad e
# historia): escribir sólo esto no incrementa `edit_version` (evita conflictos
# falsos por chatter/lecturas o por los sellos de una transición que ya escribe
# `state`, que sí cuenta como contenido).
I2_VERSION_NEUTRAL_FIELDS = frozenset([
    'edit_version', 'message_ids', 'message_main_attachment_id',
    'snapshot_json', 'audit_hash', 'executed_by_id', 'execution_date',
    'reversed_by_id', 'reversal_date', 'reversal_reason',
    'reversed_imputation_id', 'cancelled_by_id', 'cancellation_date',
    'cancellation_reason', 'reopened_by_id', 'reopen_date', 'reopen_reason',
    'write_date', 'write_uid',
])
# Mensaje operativo de conflicto (LOCK-09/§9). No expone contenido ajeno.
I2_CONFLICT_MSG = (
    'El documento %(name)s cambió desde que lo abriste (otra sesión lo '
    'guardó mientras editabas). Tus cambios NO se han guardado para no '
    'sobrescribir los de la otra sesión. Pulsa «Recargar versión actual» '
    'para ver la versión vigente y vuelve a aplicar tus cambios.')


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
    # SAVE (2026-10-11): relación de TRABAJO con la etiqueta SV de origen. Permite
    # localizar un borrador/pendiente desde el SV aunque aún no tenga reparto
    # positivo (destinos previstos). NO es una fuente de saldo ni un ledger: sólo
    # conserva la pertenencia al trabajo para poder reabrir y continuar.
    work_sv_lot_id = fields.Many2one(
        'stock.lot', string='SV de trabajo', index=True,
        domain="[('lot_flow_type', '=', 'volume')]",
        help='Etiqueta SV desde la que se preparó el trabajo. Se fija al '
             'guardar el borrador y permite encontrarlo desde el SV.')
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
    edit_version = fields.Integer(
        string='Versión de edición', default=1, copy=False, readonly=True,
        help='Contador monotónico que identifica cambios de CONTENIDO del '
             'documento (cabecera, líneas y repartos). Sostiene la detección '
             'optimista de edición obsoleta. NO es una credencial: la versión '
             'enviada por el cliente es una condición de concurrencia.')
    reason = fields.Text(
        string='Motivo',
        help='Campo libre para el motivo: obligatorio para exceso SV-side '
             '(blando), falta de SV candidato y para las transiciones de '
             'ANULACIÓN, REVERSA y REAPERTURA (FASE 11 B-3). La acción '
             'oficial lo congela en su campo de marca (cancellation_reason / '
             'reversal_reason / reopen_reason), que es de sólo lectura '
             '(D-I2-16, D-I2-17, AD-91).')
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
    # RESET (2026-10-11): trazabilidad de ANULACIÓN y REAPERTURA
    # (cancelled → draft). La transición es controlada (método explícito).
    cancelled_by_id = fields.Many2one(
        'res.users', string='Anulada por', readonly=True, copy=False)
    cancellation_date = fields.Datetime(
        string='Fecha de anulación', readonly=True, copy=False)
    cancellation_reason = fields.Text(string='Motivo de anulación')
    reopened_by_id = fields.Many2one(
        'res.users', string='Reabierta por', readonly=True, copy=False)
    reopen_date = fields.Datetime(
        string='Fecha de reapertura', readonly=True, copy=False)
    reopen_reason = fields.Text(string='Motivo de reapertura')
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
    def _i2_lot_reserved_m3(self, lot, exclude_imputation=None):
        """Σ nominal de la etiqueta en documentos RESERVADOS (draft/pending).

        La reserva ocupa capacidad (cuenta para el techo duro) pero **no** es
        imputación documental aplicada (D-I2-13/§19.16). ``exclude_imputation``
        excluye el documento en curso para no contarse dos veces al editarse.
        """
        domain = [('processed_lot_id', '=', lot.id),
                  ('imputation_id.state', 'in', ('draft', 'pending'))]
        if exclude_imputation:
            domain.append(('imputation_id', '!=', exclude_imputation.id))
        lines = self.env['madenat.sv.imputation.line'].search(domain)
        return sum(lines.mapped('nominal_volume_m3'))

    @api.model
    def _i2_lot_applied_m3(self, lot, exclude_imputation=None):
        """Σ nominal de la etiqueta en documentos **aplicados** (no revertidos)."""
        domain = [('processed_lot_id', '=', lot.id),
                  ('imputation_id.state', 'in', I2_DOCUMENTAL_STATES)]
        if exclude_imputation:
            domain.append(('imputation_id', '!=', exclude_imputation.id))
        lines = self.env['madenat.sv.imputation.line'].search(domain)
        return sum(lines.mapped('nominal_volume_m3'))

    @api.model
    def _i2_lot_available_for_m3(self, lot, exclude_imputation=None):
        """Disponible documental de la etiqueta PARA una nueva operación.

        Fórmula = ``nominal − Σ nominal de líneas en estados ACTIVOS
        (draft/pending/applied) EXCLUYENDO el documento en curso``. Excluir el
        documento en curso evita contar dos veces la propia operación al
        editarla (§19.16). Puede ser negativa si ya existía exceso (se conserva
        la política blanda etiqueta-side). No toca stock.
        """
        active = self._i2_lot_active_imputed_m3(
            lot, exclude_imputation=exclude_imputation)
        return self._i2_lot_nominal_m3(lot) - active

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
    def _i2_build_documentary_key(self, guia, processor=None, signature='',
                                  discriminator=''):
        """Clave documental (idempotencia, D-I2-17).

        La receta **base** —``I2|guia|processor|signature``— NO cambia: los
        documentos históricos conservan exactamente su clave. El
        ``discriminator`` (S1, FASE 10) es **opcional** y se añade al final SÓLO
        cuando hace falta una clave DISTINTA para una operación nueva que
        colisiona con un documento en estado TERMINAL; así la clave sigue siendo
        determinista y **trazable** (incluye el id del documento que ocupaba la
        clave) sin tocar las existentes ni migrar datos.
        """
        raw = 'I2|%s|%s|%s' % (
            guia.id if guia else 0,
            processor.id if processor else 0,
            signature or '')
        if discriminator:
            raw = '%s|%s' % (raw, discriminator)
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
        """Devuelve (sin duplicar) la imputación de TRABAJO de la guía.

        Idempotencia estable: si existe una imputación de **trabajo**
        (draft/pending) se reutiliza; si no, se busca por ``documentary_key`` un
        documento reutilizable antes de crear.

        S1 (FASE 10): sólo se devuelve un documento en estado de TRABAJO
        (draft/pending). Un documento en estado TERMINAL **no** se adopta:
        ``documentary_key`` es UNIQUE y antes se devolvía por coincidencia de
        clave, provocando «ya no admite preparación (estado applied)» /
        «fue anulado» (defecto F1).

        * ``applied`` → la operación **ya se aplicó con esta selección**: se
          informa con un mensaje claro y NO se duplica.
        * ``reversed``/``cancelled`` → la operación es NUEVA: se crea un
          documento con una clave DISTINTA y **trazable** (discriminador con el
          id del documento que ocupa la clave), sin tocar claves históricas.
        """
        work = self._i2_find_work_for_guia(guia)
        if work:
            return work
        key = self._i2_build_documentary_key(guia, processor, signature)
        existing = self.search([('documentary_key', '=', key)], limit=1)
        if existing and existing.state in ('draft', 'pending'):
            return existing
        if existing and existing.state == 'applied':
            raise UserError(_(
                'Esta rebaja ya se aplicó con esta misma selección de etiquetas '
                '(%s). No se duplica: consulta el documento aplicado o cambia '
                'la selección para una operación nueva.') % existing.name)
        # La clave base está ocupada por un documento terminal no aplicado
        # (anulado/reversado): se busca la primera clave libre con discriminador
        # trazable. Determinista (no depende de fecha ni de sesión).
        discriminator = ''
        # M-4 (FASE 11): documento TERMINAL (anulado/reversado) del mismo
        # alcance (misma clave base = misma guía/procesador/firma) que ocupaba
        # la clave; será el ORIGEN de la nueva operación (cadena de corrección).
        terminal = self.browse()
        while existing:
            # ``existing`` ocupa la clave ACTUAL y es un documento TERMINAL
            # (anulado/reversado): eslabón de la cadena de corrección. El último
            # de la cadena queda como ORIGEN de la operación nueva.
            terminal = existing
            discriminator = ('%s>%s' % (discriminator, existing.id)
                             if discriminator else str(existing.id))
            key = self._i2_build_documentary_key(
                guia, processor, signature, discriminator=discriminator)
            existing = self.search([('documentary_key', '=', key)], limit=1)
            if existing and existing.state in ('draft', 'pending'):
                return existing
            if existing and existing.state == 'applied':
                raise UserError(_(
                    'Esta rebaja ya se aplicó con esta misma selección de '
                    'etiquetas (%s). No se duplica: consulta el documento '
                    'aplicado o cambia la selección para una operación '
                    'nueva.') % existing.name)
        vals = {'guia_processing_id': guia.id, 'documentary_key': key}
        if terminal:
            vals['origin_imputation_id'] = terminal.id
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
            # B-1 (FASE 11): una imputación NACE siempre en borrador. Nacer en
            # un estado distinto de `draft` o traer marcas de transición
            # (firma/snapshot/ejecutor/fechas/motivos/metadata) por ORM/RPC
            # queda RECHAZADO: esos campos sólo los escriben las acciones
            # oficiales (A-1). `reason` y `origin_imputation_id` NO son marcas
            # y siguen admitidos.
            state = vals.get('state')
            if state and state != 'draft':
                raise UserError(_(
                    'Una imputación nueva se crea siempre en borrador; el '
                    'estado «%s» sólo se alcanza con las acciones oficiales '
                    '(FASE 11 B-1).') % state)
            vals.pop('state', None)
            marks = set(vals) & I2_TRANSITION_MARK_FIELDS
            if marks:
                raise UserError(_(
                    'No se pueden fijar marcas de transición (%s) al crear '
                    'una imputación; esos campos sólo los escriben las '
                    'acciones oficiales (FASE 11 B-1).') % ', '.join(
                        sorted(marks)))
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
        # A-1 / B-1 (FASE 11): la vía PÚBLICA (ORM/RPC) nunca cambia el estado
        # ni las marcas de transición. Las transiciones oficiales las escriben
        # por `_i2_write_protected_state` (super().write). Así no se puede
        # fabricar un `applied` sin firma ni un `cancelled` sin rastro, ni
        # falsificar después la firma, el ejecutor, las fechas o los motivos.
        marks = set(vals) & I2_TRANSITION_MARK_FIELDS
        if marks:
            raise UserError(_(
                'No se pueden modificar por escritura directa los campos %s: '
                'son marcas de transición de la imputación %s. Usa las '
                'acciones oficiales (Aplicar, Reversar, Anular, Volver a '
                'borrador), que registran usuario, fecha, motivo y firma '
                '(AD-91 / FASE 11 A-1).') % (
                    ', '.join(sorted(marks)), self[:1].name or ''))
        for rec in self:
            if rec.state == 'applied':
                # Inmutabilidad D-I2-15: sobre un aplicado sólo queda como
                # ENTRADA el motivo (`reason`) y el chatter; cualquier otro
                # campo exige reversa + nueva imputación (AD-91).
                forbidden = set(vals) - I2_APPLIED_WRITABLE
                if forbidden:
                    raise UserError(_(
                        'La imputación aplicada %(name)s es inmutable. Corrija '
                        'mediante reversa y una nueva imputación (AD-91).'
                    ) % {'name': rec.name})
        # LOCK / V1 (2026-10-12): guard de versión para la EDICIÓN DIRECTA del
        # documento persistente. El formulario envía `edit_version` (con
        # `force_save`), que refleja la versión CARGADA: si otro actor escribió
        # desde entonces, se RECHAZA de forma controlada reutilizando el guard
        # ATÓMICO del documento (`_i2_assert_edit_version`: advisory ns 1 +
        # comparación). Las escrituras internas (asistente y sus hijos) NO
        # envían `edit_version` y no se ven afectadas (el asistente tiene su
        # propio guard). Reutiliza `edit_version`; NO usa `write_date`, ni flags
        # de contexto, ni memoria global; NO ofrece sobrescritura forzada.
        if 'edit_version' in vals and len(self) == 1:
            client_version = int(vals['edit_version'] or 0)
            self._i2_assert_edit_version(client_version)
            vals = dict(vals, edit_version=(self.edit_version or 1) + 1)
        return super().write(self._i2_with_version_bump(vals))

    def _i2_with_version_bump(self, vals):
        """Añade el incremento de ``edit_version`` a un ``write`` de CONTENIDO.

        No incrementa si: ya lo trae, si escribe varios registros a la vez (no
        representativo en este flujo), o si sólo toca campos de trazabilidad
        (``I2_VERSION_NEUTRAL_FIELDS``). Así el chatter, las lecturas y los
        sellos de historia no generan conflictos falsos (LOCK-11).
        """
        if 'edit_version' in vals or len(self) != 1:
            return vals
        if not (set(vals) - I2_VERSION_NEUTRAL_FIELDS):
            return vals
        return dict(vals, edit_version=(self.edit_version or 1) + 1)

    def _i2_bump_from_child(self):
        """Incrementa la versión del documento al cambiar sus líneas/repartos.

        La versión pertenece al DOCUMENTO (fuente única persistente); los hijos
        la elevan al cambiar para que un asistente con versión anterior detecte
        la edición (LOCK-06/07). Escritura interna (``super``): no re-dispara la
        guarda pública.
        """
        for rec in self:
            super(MadenatSvImputation, rec).write(
                {'edit_version': (rec.edit_version or 1) + 1})

    def _i2_assert_edit_version(self, expected):
        """Protección + comparación de versión ATÓMICAS (LOCK-06/§6).

        Adquiere (``pg_try_advisory_xact_lock``, namespace **1** = DOCUMENTO) y
        compara. Se integra con los locks de capacidad existentes (namespaces 2
        y 3) en orden determinista creciente → sin interbloqueos. Si el lock
        está ocupado por otra sesión que está guardando, o la versión vigente
        difiere de la esperada, **rechaza** sin escribir (sin cambios parciales).
        La versión enviada es una **condición de concurrencia**, no credencial.
        """
        self.ensure_one()
        self.env.cr.execute(
            'SELECT pg_try_advisory_xact_lock(%s, %s)', (1, self.id))
        if not self.env.cr.fetchone()[0]:
            raise UserError(_(I2_CONFLICT_MSG) % {'name': self.name})
        self.invalidate_recordset(['edit_version'])
        current = self.edit_version or 1
        if expected and current != expected:
            raise UserError(_(I2_CONFLICT_MSG) % {'name': self.name})
        return current

    def _i2_write_protected_state(self, vals):
        """Vía **privada** de transición de estado (AUD-ETQ-09).

        Escribe directamente con ``super().write`` para **saltar la guarda
        pública** de ``write``. Es un método ``_``-prefijado: Odoo **no** lo
        expone por RPC (``name.startswith('_')`` se rechaza en ``call_kw``), de
        modo que **sólo** el código del propio modelo puede invocarlo. Sustituye
        al registro global de tokens: no hay estado compartido, no hay ventana de
        autorización reutilizable, no depende de contexto ni de identidad del
        cliente, y es seguro entre transacciones, hilos y procesos.

        La invocan únicamente las acciones controladas ``action_reopen_to_draft``
        y ``action_reverse``, **después** de validar permisos, compañía, motivo,
        conflicto, capacidad y bloqueos, y de derivar usuario y fecha del entorno
        de ejecución.

        FASE 11 (A-1): es la ÚNICA vía por la que se escriben ``state`` y las
        marcas de transición (``I2_TRANSITION_MARK_FIELDS``); la invocan las
        acciones oficiales ``action_pending``, ``action_back_to_draft``,
        ``action_apply``, ``action_cancel``, ``action_reverse`` y
        ``action_reopen_to_draft`` (además del sello recíproco de la cadena de
        corrección).
        """
        return super().write(self._i2_with_version_bump(vals))

    def _i2_check_children_editable(self, what):
        """I5 / B-2 (FASE 11): bloquea edición de hijos fuera de preparación.

        Se invoca desde ``create``/``write``/``unlink`` de
        ``madenat.sv.imputation.line`` y ``madenat.sv.imputation.sv.line``.
        ``what`` describe la operación («añadir líneas», «modificar repartos»…)
        para dar un mensaje de negocio claro en español.
        """
        for imp in self:
            if imp.state not in I2_CHILD_EDITABLE_STATES:
                raise UserError(_(
                    'No se pueden %(what)s de la imputación %(name)s: está '
                    '%(state)s y su contenido (líneas y repartos) es '
                    'inmutable. Para corregirla usa «Reversar» (si está '
                    'aplicada/reversada) o «Volver a borrador» (si está '
                    'anulada), que la devuelven a preparación (AD-91 / '
                    'FASE 11 B-2).') % {
                        'what': what,
                        'name': imp.name or '',
                        'state': dict(imp._fields['state'].selection).get(
                            imp.state, imp.state)})

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
            guia = line.imputation_id.guia_processing_id
            if line.processed_lot_id.lot_flow_type == 'volume' \
                    or line.processed_lot_id not in guia.lot_ids:
                raise UserError(_(
                    'Integridad etiqueta–guía (D10): la etiqueta %(lot)s no '
                    'pertenece a la guía %(guia)s.') % {
                        'lot': line.processed_lot_id.name,
                        'guia': guia.name})
        # Contrato de aplicación (APROBADO 2026-10-11): Aplicar exige AL MENOS
        # UN reparto con cantidad positiva hacia un SV AUTORIZADO
        # (``lot_flow_type='volume'``). Sin reparto, el documento sólo puede
        # permanecer en un estado NO aplicado; una fila de volumen cero NO
        # satisface el requisito. Sustituye a la excepción por motivo
        # ``NO_SV_CANDIDATE`` (que pasa a ser INFORMATIVA, no aplicable).
        positivos = self.env['madenat.sv.imputation.sv.line']
        for sline in self.sv_line_ids:
            if not sline.sv_lot_id \
                    or sline.sv_lot_id.lot_flow_type != 'volume':
                raise UserError(_(
                    'El destino %(sv)s de la etiqueta %(lot)s no es una '
                    'etiqueta SV autorizada (Lote Volumen).') % {
                        'sv': sline.sv_lot_id.name or '',
                        'lot': (sline.imputation_line_id.processed_lot_id.name
                                or '')})
            if float_compare(sline.imputed_volume_m3, 0.0,
                             precision_rounding=I2_VOLUME_PRECISION) <= 0:
                raise UserError(_(
                    'El volumen imputado al SV %s debe ser mayor que cero.')
                    % (sline.sv_lot_id.name))
            positivos |= sline
        if not positivos:
            # Mensaje según el problema REAL (SIMPLE‑08/10): falta de cantidad
            # vs. falta de disponibilidad de las etiquetas seleccionadas.
            lots = self.line_ids.mapped('processed_lot_id')
            con_disponible = any(
                float_compare(
                    self._i2_lot_available_for_m3(lot, exclude_imputation=self),
                    0.0, precision_rounding=I2_VOLUME_PRECISION) > 0
                for lot in lots)
            if con_disponible:
                raise UserError(_(
                    'Indica los m³ a rebajar en las etiquetas seleccionadas.'))
            raise UserError(_(
                'Las etiquetas seleccionadas no tienen disponibilidad. '
                'Consulta la operación que las compromete o selecciona material '
                'disponible.'))

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

    def _i2_lock_resources(self):
        """Serializa la aplicación concurrente (etiquetas de retorno y SV).

        Bloquea, en un **orden global determinista** para evitar interbloqueos:

        * etiquetas de retorno (namespace **3**) — cierra el riesgo (CON-01) de
          que dos documentos apliquen a la MISMA etiqueta hacia SV distintos y
          superen su techo duro;
        * SV destino (namespace **2**) — serializa el saldo documental del SV.

        Usa advisory locks de **transacción** (``pg_try_advisory_xact_lock``): si
        otra transacción ya posee alguno, se falla de forma **controlada** (sin
        escrituras parciales) en lugar de esperar indefinidamente. Los locks se
        adquieren ANTES de revalidar los techos, de modo que el control lee un
        estado ya serializado.
        """
        self.ensure_one()
        keys = sorted(
            {(3, lot_id)
             for lot_id in self.line_ids.mapped('processed_lot_id').ids}
            | {(2, lot_id)
               for lot_id in self.sv_line_ids.mapped('sv_lot_id').ids})
        for namespace, res_id in keys:
            self.env.cr.execute(
                'SELECT pg_try_advisory_xact_lock(%s, %s)', (namespace, res_id))
            if not self.env.cr.fetchone()[0]:
                raise UserError(_(
                    'Otra operación está modificando la misma etiqueta de '
                    'retorno o el saldo documental de un SV de esta '
                    'imputación. La operación no fue aplicada; actualice la '
                    'información y vuelva a intentarlo.'))

    def _i2_lock_sv_lots(self):
        """Compatibilidad: delega en ``_i2_lock_resources`` (etiquetas + SV)."""
        self.ensure_one()
        return self._i2_lock_resources()

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
            # A-1 (FASE 11): transición por la VÍA PRIVADA del modelo.
            rec._i2_write_protected_state({'state': 'pending'})
        return True

    def action_back_to_draft(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Solo una imputación pendiente puede volver a '
                                  'borrador.'))
            # A-1 (FASE 11): transición por la VÍA PRIVADA del modelo.
            rec._i2_write_protected_state({'state': 'draft'})
        return True

    def action_cancel(self, reason=None):
        """Anula una imputación de TRABAJO (``draft``/``pending``).

        **B-3 (FASE 11):** exige MOTIVO (no vacío tras ``strip``) y lo deja en
        la METADATA de anulación (``cancellation_reason``) y en la bitácora
        ``imputation_cancel`` (texto del motivo dentro del evento firmado). Sin
        cambio de grupos: se mantiene el ACL de escritura vigente.
        """
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise UserError(_(
                    'Solo una imputación en borrador/pendiente puede anularse; '
                    'una aplicada se corrige por reversa (AD-91).'))
            motivo = (reason or rec.cancellation_reason or rec.reason or '').strip()
            if not motivo:
                raise UserError(_(
                    'Indique el motivo de la anulación antes de anular '
                    '(trazabilidad, FASE 11 B-3).'))
            prev = rec.state
            # A-1 (FASE 11): estado y metadata de anulación por la VÍA PRIVADA.
            rec._i2_write_protected_state({
                'state': 'cancelled',
                'cancelled_by_id': self.env.user.id,
                'cancellation_date': fields.Datetime.now(),
                'cancellation_reason': motivo,
            })
            rec.message_post(body=_(
                '⛔ Anulación de %(name)s (%(prev)s → anulado). Motivo: '
                '%(reason)s') % {
                'name': rec.name, 'prev': prev, 'reason': motivo})
            rec._i2_audit(
                'imputation_cancel',
                rec._i2_build_snapshot(extra={'motivo': motivo}))
        return True

    def _i2_check_reopen_permission(self):
        user = self.env.user
        allowed = (user.has_group(GROUP_OPERACIONES)
                   or user.has_group(GROUP_JEFATURA)
                   or user.has_group(GROUP_GERENCIA))
        if not allowed:
            raise AccessError(_(
                'Solo Operaciones, Jefatura de Operaciones o Gerencia pueden '
                'reabrir una imputación anulada (CANON/19 §9).'))

    def _i2_validate_reopen(self):
        """Validaciones de la transición cancelled → draft (RESET).

        Se ejecutan en la propia transición (backend), no sólo al renderizar el
        botón: conflicto con otro trabajo activo, guía vigente y CAPACIDAD
        (el borrador vuelve a reservar el nominal). Nombre etiquetas y
        documentos que explican un conflicto, sin liberar reservas ajenas.
        """
        self.ensure_one()
        if not self.guia_processing_id:
            raise UserError(_('La imputación no tiene guía; no puede reabrirse.'))
        self._i2_check_guia_is_eligible_return(self.guia_processing_id)
        other = self.env['madenat.sv.imputation'].search([
            ('guia_processing_id', '=', self.guia_processing_id.id),
            ('state', 'in', ('draft', 'pending')),
            ('id', '!=', self.id)], limit=1)
        if other:
            raise UserError(_(
                'Ya existe trabajo en preparación para esta guía: %s. Continúa '
                'ese documento o resuelve el conflicto.') % other.name)
        for line in self.line_ids:
            lot = line.processed_lot_id
            nominal = self._i2_lot_nominal_m3(lot)
            if not nominal:
                continue
            others_active = self._i2_lot_active_imputed_m3(
                lot, exclude_imputation=self)
            total = others_active + (line.nominal_volume_m3 or 0.0)
            if float_compare(total, nominal,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                conflict = self.env['madenat.sv.imputation.line'].search([
                    ('processed_lot_id', '=', lot.id),
                    ('imputation_id.state', 'in', I2_ACTIVE_STATES),
                    ('imputation_id', '!=', self.id)])
                docs = ', '.join(sorted(set(
                    conflict.mapped('imputation_id.name')))) or '—'
                raise UserError(_(
                    'No se puede reabrir %(name)s: la etiqueta %(lot)s ya está '
                    'comprometida (%(other).3f m³ de %(nom).3f m³) por: '
                    '%(docs)s.') % {
                    'name': self.name, 'lot': lot.name or '',
                    'other': others_active, 'nom': nominal, 'docs': docs})
        return True

    def action_reopen_to_draft(self, reason=None):
        """Transición controlada **cancelled → draft** («Volver a borrador»).

        Autorizada expresamente por Mauricio (2026-10-11). NO aplica la rebaja;
        el borrador vuelve a **reservar** su nominal (política vigente). Exige
        motivo, permisos, ausencia de conflicto y capacidad suficiente; deja
        historia de anulación y reapertura. Idempotente: si ya está en borrador
        devuelve un resultado controlado sin repetir efectos.

        El motivo se captura en el campo libre ``reason`` (o como parámetro,
        p. ej. desde el asistente) y se congela en ``reopen_reason`` (marca de
        transición, A-1 FASE 11).
        """
        for rec in self:
            if rec.state == 'draft':
                continue                      # idempotente (ya reabierto)
            if rec.state != 'cancelled':
                raise UserError(_(
                    'Sólo un documento ANULADO puede volver a borrador; un '
                    'aplicado se corrige por reversa (AD-91).'))
            rec._i2_check_reopen_permission()
            motivo = (reason or rec.reopen_reason or rec.reason or '').strip()
            if not motivo:
                raise UserError(_(
                    'Indique el motivo de la reapertura (trazabilidad).'))
            rec._i2_validate_reopen()
            rec._i2_lock_resources()
            rec._i2_validate_reopen()          # revalidar tras el bloqueo
            # AUD-ETQ-09 / A-1: transición por la VÍA PRIVADA del modelo
            # (método `_`-prefijado, no invocable por RPC; sin token ni
            # contexto). Usuario y fecha se derivan del entorno de ejecución.
            rec._i2_write_protected_state({
                'state': 'draft',
                'reopened_by_id': self.env.user.id,
                'reopen_reason': motivo,
                'reopen_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                '↩️ Reapertura de %(name)s (anulado → borrador). Motivo: '
                '%(reason)s') % {'name': rec.name, 'reason': motivo})
            rec._i2_audit('imputation_reopen', rec._i2_build_snapshot())
        return True

    def action_continue_preparation(self):
        """Reabre el asistente para CONTINUAR un trabajo NO aplicado (SAVE).

        Reutiliza el asistente existente y precarga la guía y el SV del documento
        guardado, de modo que al continuar se reconstruyan las mismas etiquetas,
        cantidades y destinos. No aplica nada ni crea un documento nuevo: el
        asistente reutiliza la imputación de trabajo de la guía.

        S2 (FASE 10): sobre un estado TERMINAL (aplicado/reversado/anulado) NO
        se lanza un error técnico: se devuelve una **notificación operativa** con
        la ruta disponible («Volver a borrador» para un anulado; reversa para un
        aplicado/reversado). El botón «Continuar» de la sección del SV ya no
        ofrece estados terminales (el campo filtra por estado en el servidor);
        esto cubre la llamada directa y los enlaces heredados.
        """
        self.ensure_one()
        if self.state not in ('draft', 'pending'):
            if self.state == 'cancelled':
                message = _(
                    'El documento %(name)s está ANULADO y no es «Trabajo en '
                    'preparación». Usa «Volver a borrador» en el documento '
                    '(indicando el motivo) para continuar, si su capacidad '
                    'sigue disponible.'
                ) % {'name': self.name}
            else:
                message = _(
                    'El documento %(name)s está %(state)s: ya no es «Trabajo en '
                    'preparación». Se corrige por reversa desde el documento '
                    '(no se continúa un documento ya aplicado).'
                ) % {'name': self.name, 'state': self.state}
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Trabajo en preparación'),
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                },
            }
        action = self.env['ir.actions.act_window']._for_xml_id(
            'madenat_lumber_logistics.action_madenat_sv_imputation_wizard')
        # UI: se usa el mismo formulario amplio (target del propio action) para
        # que las acciones del <header> estén siempre visibles.
        action['context'] = dict(
            self.env.context,
            default_guia_processing_id=self.guia_processing_id.id,
            default_sv_lot_id=self.work_sv_lot_id.id or False,
            active_model='stock.lot',
            active_id=self.work_sv_lot_id.id or False)
        return action

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

    def _i2_build_snapshot(self, extra=None):
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
        if extra:
            # I6 (FASE 11): el evento firmado puede incorporar datos del motivo
            # (p. ej. `{'motivo': ...}` en la anulación) sin alterar el resto del
            # payload ni los snapshots de las otras transiciones.
            payload.update(extra)
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
        """Exige que la guía DESTINO sea un retorno de servicio ELEGIBLE.

        Se comprueba al APLICAR (no al guardar borrador/pendiente). No marca la
        guía automáticamente: la identificación es un acto del operador
        (decisión aprobada 2026-10-07). No altera stock, ledger ni costos. Se
        revalida la **elegibilidad** completa (confirmación Sí y **no**
        cancelada) para que un cambio de estado entre la apertura y la
        aplicación se rechace de forma comprensible y sin estados parciales.
        """
        self.ensure_one()
        return self._i2_check_guia_is_eligible_return(
            self.guia_processing_id)

    @api.model
    def _i2_return_guide_domain(self):
        """Dominio canónico de guía de retorno ELEGIBLE para nueva operación.

        ``service_return_confirmation == 'yes'`` y **no** cancelada. Es la misma
        condición que exige ``action_apply`` (destino Sí) más la exclusión de
        canceladas. **No** se usa ``tipo_recepcion`` como filtro duro: la
        doctrina (CANON/19 §7.3) identifica el retorno por la confirmación, y el
        tipo de ingreso no es prueba suficiente ni necesaria (AD-102).
        """
        return [('service_return_confirmation', '=', 'yes'),
                ('state', '!=', 'cancelled')]

    @api.model
    def _i2_check_guia_is_eligible_return(self, guia):
        """Valida (en el MODELO, no sólo en la UI) la elegibilidad del retorno.

        Se usa en la apertura del asistente, antes de construir/modificar el
        documento, y al aplicar. Rechaza guía sin confirmar (``no`` o vacío) y
        guía cancelada. No marca la guía automáticamente.
        """
        if not guia:
            raise UserError(_('Seleccione una guía de retorno.'))
        if guia.service_return_confirmation != 'yes':
            raise UserError(_(
                'La guía %(guia)s no está confirmada como retorno de servicio '
                '("¿Es retorno de servicio?" = Sí). Revise la identificación '
                'del retorno en su guía; esta operación no la marca '
                'automáticamente.') % {'guia': guia.name})
        if guia.state == 'cancelled':
            raise UserError(_(
                'La guía %s está cancelada y no puede usarse en una nueva '
                'operación de rebaja de etiquetas.') % guia.name)
        return True

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
            rec._i2_lock_resources()
            rec._i2_validate_hard_cap()
            rec._i2_handle_soft_deviations()
            snapshot = rec._i2_build_snapshot()
            # A-1 (FASE 11): la firma, el snapshot, el ejecutor y la fecha son
            # marcas de transición: se escriben por la VÍA PRIVADA del modelo
            # (super().write), nunca por la vía pública.
            rec._i2_write_protected_state({
                'state': 'applied',
                'executed_by_id': self.env.user.id,
                'execution_date': fields.Datetime.now(),
                'snapshot_json': snapshot,
                'audit_hash': hashlib.sha256(snapshot.encode('utf-8')).hexdigest(),
            })
            rec._i2_audit('imputation', snapshot)
            origin = rec.origin_imputation_id
            if origin and not origin.reversed_imputation_id:
                # Sello recíproco de la cadena de corrección (marca de reversa):
                # también por la vía privada.
                origin.sudo()._i2_write_protected_state(
                    {'reversed_imputation_id': rec.id})
        return True

    def action_reverse(self, reason=None):
        """Reversa la imputación: estado `reversed`; historia intacta.

        **M-2 (FASE 11):** toma los MISMOS locks que ``action_apply``
        (etiquetas de retorno ns 3 + SV ns 2, en el mismo orden determinista) y
        **revalida el estado tras el bloqueo**, de modo que dos sesiones no
        pueden reversar a la vez ni dejar marcas de «último gana»
        (usuario/fecha/firma sobrescritos). Si otra conexión tiene el lock, o el
        documento ya no está aplicado, se rechaza de forma CONTROLADA (sin
        cambios) y el operador puede reintentar tras actualizar la información.

        El motivo se captura en el campo libre ``reason`` (o como parámetro) y
        la acción lo congela en ``reversal_reason`` (marca de transición).
        """
        for rec in self:
            if rec.state != 'applied':
                raise UserError(_(
                    'Solo una imputación aplicada puede reversarse (AD-91).'))
            rec._i2_check_reverse_permission()
            # Motivo obligatorio (AUD-ETQ-02, §12/§16-R02): la reversa debe ser
            # trazable. Misma política que la relación de conciliación
            # (`madenat.processor.return.link.action_reverse`). Se exige motivo
            # **no vacío tras strip** (AUD-ETQ-06: un motivo sólo con espacios
            # NO es trazabilidad).
            motivo = (reason or rec.reversal_reason or rec.reason or '').strip()
            if not motivo:
                raise UserError(_(
                    'Indique el motivo de la reversa antes de reversar '
                    '(trazabilidad, AD-91 / CANON/19 §19).'))
            # M-2 (FASE 11): locks de capacidad ANTES de fijar la historia.
            rec._i2_lock_resources()
            # Revalidación del estado bajo el lock: si otra sesión ya reversó
            # (o modificó) el documento, NO se sobrescriben sus marcas.
            rec.invalidate_recordset(['state'])
            if rec.state != 'applied':
                raise UserError(_(
                    'La imputación %(name)s ya no está aplicada: otra sesión la '
                    'revirtió o la modificó. No se ha registrado una segunda '
                    'reversa; actualiza la información y vuelve a intentarlo.'
                ) % {'name': rec.name})
            snapshot = rec._i2_build_snapshot()
            # AUD-ETQ-09 / A-1: `applied → reversed` por la VÍA PRIVADA del
            # modelo (no RPC). Sustituye a la escritura directa, que la guarda
            # pública ahora rechaza.
            rec._i2_write_protected_state({
                'state': 'reversed',
                'reversed_by_id': self.env.user.id,
                'reversal_date': fields.Datetime.now(),
                'reversal_reason': motivo,
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
    etiqueta_pendiente_m3 = fields.Float(
        string='Pendiente de reparto (m³)', digits=(16, 3),
        compute='_compute_etiqueta_pendiente', store=False,
        help='Nominal comprometido de esta línea menos lo ya repartido a SV en '
             'este documento (a cualquier SV). NO es equivalente al nominal.')

    @api.depends('nominal_volume_m3', 'sv_allocation_ids.imputed_volume_m3')
    def _compute_etiqueta_pendiente(self):
        for line in self:
            line.etiqueta_pendiente_m3 = max(
                0.0, (line.nominal_volume_m3 or 0.0)
                - sum(line.sv_allocation_ids.mapped('imputed_volume_m3')))

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

    @api.constrains('processed_lot_id', 'imputation_id')
    def _check_label_belongs_to_guia(self):
        """Bloque E (D10): la etiqueta procesada debe pertenecer a su guía.

        Control de **integridad en el modelo** (no sólo dominio de UI): se
        valida en creación, escritura y por tanto en ``action_apply`` y en
        cualquier selección forzada por ORM/RPC. Una etiqueta de otra guía con
        el mismo proveedor/producto/número visible NO es aceptada.
        """
        for line in self:
            lot = line.processed_lot_id
            guia = line.imputation_id.guia_processing_id
            if not lot or not guia:
                continue
            if lot.lot_flow_type == 'volume':
                raise ValidationError(_(
                    'La etiqueta %s es un Lote Volumen (SV); no puede '
                    'registrarse como etiqueta de retorno.') % lot.name)
            if lot not in guia.lot_ids:
                raise ValidationError(_(
                    'Integridad etiqueta–guía (D10): la etiqueta %(lot)s no '
                    'pertenece a la guía %(guia)s. Seleccione una etiqueta de '
                    'la guía del documento.') % {
                        'lot': lot.name, 'guia': guia.name})

    @api.constrains('nominal_volume_m3', 'sv_allocation_ids')
    def _check_reparto_within_nominal(self):
        """Bloque F (D10/D11): Σ reparto ≤ nominal autorizado de la etiqueta.

        Ambas magnitudes son la **misma magnitud documental** (m³) de la
        etiqueta de retorno. Se admiten asignaciones **parciales**
        (``0 < reparto ≤ nominal``); no se exige igualdad. Un nominal reducido
        por debajo del reparto ya guardado también se rechaza.
        """
        for line in self:
            total = sum(line.sv_allocation_ids.mapped('imputed_volume_m3'))
            if float_compare(total, line.nominal_volume_m3,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                raise ValidationError(_(
                    'El reparto asignado (%.3f m³) supera el volumen nominal '
                    'autorizado (%.3f m³) de la etiqueta %s (D10).') % (
                        total, line.nominal_volume_m3,
                        line.processed_lot_id.name or ''))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            imp = self.env['madenat.sv.imputation'].browse(
                vals.get('imputation_id'))
            # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
            imp._i2_check_children_editable('añadir líneas')
        records = super().create(vals_list)
        records.imputation_id._i2_bump_from_child()
        return records

    def write(self, vals):
        # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
        self.imputation_id._i2_check_children_editable('modificar líneas')
        result = super().write(vals)
        self.imputation_id._i2_bump_from_child()
        return result

    def unlink(self):
        # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
        self.imputation_id._i2_check_children_editable('eliminar líneas')
        parents = self.imputation_id
        result = super().unlink()
        parents._i2_bump_from_child()
        return result


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
    # ── Campos de consulta (Bloque A: pantalla centrada en SV). Relacionados,
    #    no almacenados: el dato vive en la imputación; no se duplica. ────────
    imputation_name = fields.Char(
        related='imputation_id.name', string='Documento')
    guia_processing_id = fields.Many2one(
        related='imputation_id.guia_processing_id', string='Guía de retorno')
    processed_lot_id = fields.Many2one(
        related='imputation_line_id.processed_lot_id',
        string='Etiqueta procesada')
    imputation_state = fields.Selection(
        related='imputation_id.state', string='Estado')
    execution_date = fields.Datetime(
        related='imputation_id.execution_date', string='Fecha de aplicación')
    executed_by_id = fields.Many2one(
        related='imputation_id.executed_by_id', string='Aplicada por')

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

    @api.constrains('imputed_volume_m3', 'imputation_line_id')
    def _check_within_line_nominal(self):
        """Bloque F (D10): el reparto por línea no supera su nominal.

        Se valida en creación/escritura del reparto (control de modelo), por lo
        que también protege la edición directa por ORM/RPC y la elusión por
        varias líneas del mismo documento.
        """
        for sline in self:
            line = sline.imputation_line_id
            total = sum(line.sv_allocation_ids.mapped('imputed_volume_m3'))
            if float_compare(total, line.nominal_volume_m3,
                             precision_rounding=I2_VOLUME_PRECISION) > 0:
                raise ValidationError(_(
                    'El reparto asignado (%.3f m³) supera el volumen nominal '
                    'autorizado (%.3f m³) de la etiqueta %s (D10).') % (
                        total, line.nominal_volume_m3,
                        line.processed_lot_id.name or ''))

    def action_open_imputation(self):
        """Acceso al documento de imputación desde la pantalla centrada en SV."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Imputación documental SV'),
            'res_model': 'madenat.sv.imputation',
            'res_id': self.imputation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            imp = self.env['madenat.sv.imputation'].browse(
                vals.get('imputation_id'))
            # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
            imp._i2_check_children_editable('añadir repartos SV')
        records = super().create(vals_list)
        records.imputation_id._i2_bump_from_child()
        return records

    def write(self, vals):
        # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
        self.imputation_id._i2_check_children_editable('modificar repartos SV')
        result = super().write(vals)
        self.imputation_id._i2_bump_from_child()
        return result

    def unlink(self):
        # I5 / B-2 (FASE 11): contenido congelado fuera de preparación.
        self.imputation_id._i2_check_children_editable('eliminar repartos SV')
        parents = self.imputation_id
        result = super().unlink()
        parents._i2_bump_from_child()
        return result


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


class StockLot(models.Model):
    """Consulta de asignaciones documentales centrada en el SV (Bloque A).

    Campos de **solo lectura** sobre ``stock.lot`` para la pantalla
    «Rebaja de etiquetas». NO crean un modelo persistente nuevo ni duplican el
    dato: el reparto vive en ``madenat.sv.imputation.sv.line`` y aquí se expone
    por relación inversa. No tocan ``stock.quant``, el ledger
    ``madenat.sv.operation`` ni ``sv_available_m3``: el «saldo» mostrado es el
    **saldo documental I2**.
    """

    _inherit = 'stock.lot'

    sv_assignment_sv_line_ids = fields.One2many(
        'madenat.sv.imputation.sv.line', 'sv_lot_id',
        string='Asignaciones documentales SV')
    # SAVE (2026-10-11): TRABAJO NO APLICADO relacionado con este SV (borradores y
    # pendientes). Permite localizar y continuar lo preparado aunque todavía no
    # tenga reparto positivo. Se mantiene SEPARADO de los agregados aplicados.
    # S2 (FASE 10, 2026-10-15): antes era un ``One2many`` con
    # ``domain=[('state','in',('draft','pending'))]``, pero el ORM **no aplica**
    # el ``domain`` declarativo de un O2M al leer (defecto F2): la sección del
    # SV listaba y contaba documentos anulados/aplicados. Ahora es un campo
    # calculado NO almacenado que resuelve la lista con una **búsqueda explícita
    # en el servidor** (mismo patrón que ``sv_assignment_imputation_ids``). No
    # crea tabla alguna (``store=False``) y conserva nombre y semántica.
    sv_assignment_work_imputation_ids = fields.Many2many(
        'madenat.sv.imputation',
        relation='stock_lot_madenat_sv_imputation_work_rel',
        column1='lot_id', column2='imputation_id',
        string='Trabajo en preparación',
        compute='_compute_sv_assignment_work', store=False)
    sv_assignment_work_count = fields.Integer(
        string='N° trabajo en preparación',
        compute='_compute_sv_assignment_work')
    sv_assignment_work_m3 = fields.Float(
        string='Preparado (m³)', digits=(16, 3),
        compute='_compute_sv_assignment_work',
        help='Σ repartos positivos hacia este SV en documentos NO aplicados. '
             'NO se suma a «Rebajado documental» (sólo aplicado).')
    # AUD-ETQ-08/10 (2026-10-12): SEPARACIÓN de computes + régimen de permisos
    # COHERENTE por SEMÁNTICA:
    #   * `_compute_sv_assignment`      -> agregados ALMACENADOS **canónicos**
    #     (`store=True`, `compute_sudo=True`): el mismo valor para todos los
    #     usuarios; se calculan con derechos plenos sobre las relaciones propias
    #     del lote (company-scoped) para que un usuario con visibilidad parcial
    #     NO almacene un saldo incompleto ni provoque AccessError al escribir el
    #     lote. El cómputo lee únicamente `sv_assignment_sv_line_ids` (el propio
    #     lote), por lo que NO expone documentos de otra compañía.
    #   * `_compute_sv_assignment_live` -> proyección NO almacenada **por
    #     usuario** (`store=False`, `compute_sudo=False`): respeta reglas de
    #     registro y compañía del usuario que consulta.
    # Antes ambos grupos compartían un método (avisos `inconsistent 'store'` y
    # `inconsistent 'compute_sudo'`); la separación los resuelve.
    sv_assignment_imputation_ids = fields.Many2many(
        'madenat.sv.imputation', string='Imputaciones que asignan este SV',
        compute='_compute_sv_assignment_live')
    # Agregados documentales ALMACENADOS (store=True): permiten filtrar y
    # agrupar el listado «Etiquetas SV» (con/sin saldo, con/sin rebajas) sin
    # inventar dominios sobre campos no buscables. Siguen siendo sólo lectura.
    sv_assignment_nominal_m3 = fields.Float(
        string='Volumen documental (m³)', digits=(16, 3),
        compute='_compute_sv_assignment', store=True, compute_sudo=True)
    sv_assignment_applied_m3 = fields.Float(
        string='Rebajado documental (m³)', digits=(16, 3),
        compute='_compute_sv_assignment', store=True, compute_sudo=True)
    sv_assignment_applied_count = fields.Integer(
        string='Asignaciones aplicadas', compute='_compute_sv_assignment',
        store=True, compute_sudo=True)
    sv_assignment_documental_balance_m3 = fields.Float(
        string='Saldo documental (m³)', digits=(16, 3),
        compute='_compute_sv_assignment', store=True, compute_sudo=True)
    sv_assignment_processor_id = fields.Many2one(
        'res.partner', string='Procesador', compute='_compute_sv_assignment_live')
    # Columnas de lectura para el listado (relacionadas, no almacenadas):
    # separan nº de guía, proveedor y fecha para evitar textos concatenados.
    sv_assignment_guia_number = fields.Char(
        related='volume_source_guia_id.name', string='N° Guía', store=False)
    sv_assignment_supplier_id = fields.Many2one(
        'res.partner', related='volume_source_guia_id.partner_id',
        string='Proveedor', store=False)
    sv_assignment_guia_date = fields.Date(
        related='volume_source_guia_id.date_emission', string='Fecha guía',
        store=False)

    @api.depends('lot_flow_type', 'volume_purchase_m3', 'volumen_m3',
                 'sv_assignment_sv_line_ids.imputed_volume_m3',
                 'sv_assignment_sv_line_ids.imputation_id',
                 'sv_assignment_sv_line_ids.imputation_id.state')
    def _compute_sv_assignment(self):
        """Agregados documentales ALMACENADOS **canónicos** del SV (store=True).

        ``compute_sudo=True``: el agregado es canónico (el MISMO valor para todos
        los usuarios) y se calcula con derechos plenos para que un usuario con
        visibilidad parcial sobre las imputaciones NO almacene un saldo
        incompleto ni provoque ``AccessError`` al escribir el lote (AUD-ETQ-10).
        El cómputo lee únicamente ``sv_assignment_sv_line_ids`` (las líneas del
        propio lote, acotadas por compañía), por lo que NO expone documentos ni
        datos de otra compañía. Cada campo que comparte este método tiene
        ``store=True`` y ``compute_sudo=True`` -> atributos coherentes (sin aviso
        de registry). La proyección no almacenada vive en
        ``_compute_sv_assignment_live`` (``compute_sudo=False``, por usuario).
        """
        Imputation = self.env['madenat.sv.imputation']
        for lot in self:
            lines = lot.sv_assignment_sv_line_ids
            applied = lines.filtered(
                lambda l: l.imputation_id.state == 'applied')
            is_sv = lot.lot_flow_type == 'volume'
            lot.sv_assignment_nominal_m3 = (
                Imputation._i2_sv_nominal_m3(lot) if is_sv else 0.0)
            lot.sv_assignment_applied_m3 = sum(
                applied.mapped('imputed_volume_m3'))
            lot.sv_assignment_applied_count = len(applied)
            lot.sv_assignment_documental_balance_m3 = (
                Imputation._i2_sv_documental_available_m3(lot) if is_sv
                else 0.0)

    @api.depends('sv_assignment_sv_line_ids.imputation_id',
                 'sv_assignment_sv_line_ids.imputation_id.processor_id')
    def _compute_sv_assignment_live(self):
        """Proyección NO almacenada del SV (lista/lectura en vivo).

        Imputaciones que asignan el SV y su procesador. Campos con
        ``store=False`` y ``compute_sudo=False`` (valor por defecto de un campo
        calculado no almacenado) -> atributos coherentes entre sí y separados
        del compute almacenado (corrige el aviso de ``store``/``compute_sudo``).
        """
        for lot in self:
            lines = lot.sv_assignment_sv_line_ids
            lot.sv_assignment_imputation_ids = lines.mapped('imputation_id')
            lot.sv_assignment_processor_id = lines.mapped(
                'imputation_id.processor_id')[:1]

    @api.depends('sv_assignment_sv_line_ids.imputed_volume_m3',
                 'sv_assignment_sv_line_ids.imputation_id.state')
    def _compute_sv_assignment_work(self):
        """Trabajo NO aplicado del SV (borradores/pendientes), separado de lo
        aplicado. No se suma a «Rebajado documental».

        S2 (FASE 10): la lista y el contador se resuelven con una **búsqueda
        explícita en el servidor** por ``work_sv_lot_id`` y estado de trabajo.
        El ``domain`` declarativo de un O2M no se evaluaba al leer (defecto F2),
        por lo que un documento anulado/aplicado seguía listándose y contando
        como «trabajo en preparación». Sin ``sudo``: respeta compañía y reglas
        de registro del usuario (mismo régimen que la proyección en vivo).
        """
        Imputation = self.env['madenat.sv.imputation']
        for lot in self:
            work = Imputation.search([
                ('work_sv_lot_id', '=', lot.id),
                ('state', 'in', ('draft', 'pending')),
            ])
            lot.sv_assignment_work_imputation_ids = work
            work_lines = lot.sv_assignment_sv_line_ids.filtered(
                lambda l: l.imputation_id.state in ('draft', 'pending'))
            lot.sv_assignment_work_count = len(work)
            lot.sv_assignment_work_m3 = sum(
                work_lines.mapped('imputed_volume_m3'))

    def action_open_sv_rebajas(self):
        """Abre el historial de rebajas documentales del SV (acceso interno).

        Reutiliza la acción existente ``action_madenat_sv_imputation`` (mismo
        modelo ``madenat.sv.imputation`` y mismas vistas) y sólo añade el
        dominio por la etiqueta SV. Es un acceso INTERNO del recorrido «Rebaja
        de etiquetas»: no crea un enlace de menú, no crea documento, no aplica
        ni modifica saldo alguno (consulta de sólo lectura).
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'madenat_lumber_logistics.action_madenat_sv_imputation')
        action['name'] = _('Historial de rebajas — %s') % (self.name or '')
        # SAVE (2026-10-11): incluye el TRABAJO NO APLICADO relacionado con el SV
        # (work_sv_lot_id), no sólo los documentos con reparto positivo hacia él,
        # para que un borrador preparado sin cantidades también sea localizable.
        action['domain'] = [
            '|', ('sv_line_ids.sv_lot_id', '=', self.id),
            ('work_sv_lot_id', '=', self.id)]
        action['context'] = dict(
            self.env.context, search_default_group_state=1)
        return action

class MadenatGuiaProcessingSvRet(models.Model):
    """Cifras documentales de retorno de una guía (para selección/comparación).

    Campos de **sólo lectura** y **no almacenados** que resumen las etiquetas de
    retorno de la guía con la semántica documental I2 (§19.16): capacidad
    nominal, rebajado aplicado y pendiente documental. Se usan como columnas
    opcionales en la selección de la guía; no alteran el modelo de negocio ni el
    stock.
    """

    _inherit = 'madenat.guia.processing'

    sv_ret_etiquetas_count = fields.Integer(
        string='Etiquetas de retorno', compute='_compute_sv_ret')
    sv_ret_nominal_m3 = fields.Float(
        string='Volumen documental (m³)', digits=(16, 3),
        compute='_compute_sv_ret')
    sv_ret_aplicado_m3 = fields.Float(
        string='Rebajado documental (m³)', digits=(16, 3),
        compute='_compute_sv_ret')
    sv_ret_pendiente_m3 = fields.Float(
        string='Pendiente documental (m³)', digits=(16, 3),
        compute='_compute_sv_ret')

    @api.depends('lot_ids', 'lot_ids.lot_flow_type')
    def _compute_sv_ret(self):
        Imputation = self.env['madenat.sv.imputation']
        for guia in self:
            lots = guia.lot_ids.filtered(
                lambda l: l.lot_flow_type != 'volume')
            guia.sv_ret_etiquetas_count = len(lots)
            guia.sv_ret_nominal_m3 = sum(
                Imputation._i2_lot_nominal_m3(lot) for lot in lots)
            guia.sv_ret_aplicado_m3 = sum(
                Imputation._i2_lot_applied_m3(lot) for lot in lots)
            guia.sv_ret_pendiente_m3 = sum(
                Imputation._i2_lot_documental_available_m3(lot) for lot in lots)


