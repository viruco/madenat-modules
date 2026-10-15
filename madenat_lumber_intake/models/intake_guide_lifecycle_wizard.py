# -*- coding: utf-8 -*-
"""Ciclo de vida controlado de Guías desde la Consola de Ingreso de Madera.

Fase 2 (AD-80). Cuatro modos documentados, con diagnóstico único y guardas
fail-closed. NUNCA usa SQL de escritura, NUNCA usa ON DELETE CASCADE, NUNCA
borra movimientos, pickings, quants, operaciones SV aplicadas/reversadas ni
registros históricos.

  A. Eliminar definitivamente  — solo `draft`/`cancelled` sin ninguna traza.
  B. Cancelar y conservar      — reutiliza `action_force_cancel()` sin cambiar
                                 su semántica.
  C. Purgar de forma controlada— solo lote SV técnico sin historia material;
                                 exige motivo, confirmación escrita y
                                 Jefatura de Operaciones.
  D. Bloquear y escalar        — muestra la lista completa de bloqueadores,
                                 registra `guia_delete_blocked` y ofrece las
                                 rutas correctas. No elimina nada.
"""
import hashlib
import json
import re
from html import unescape

from odoo import api, fields, models, _
from odoo.exceptions import UserError

GROUP_JEFATURA = 'madenat_lumber_core.group_madenat_jefatura_operaciones'
# H2 (FASE 4): la guarda de eliminación de guía ya NO exige el grupo técnico
# `stock.group_stock_manager`; el rol lo rige `_guia_delete_group_ok()` en el
# modelo (`GUIA_DELETE_GROUPS`).
PURGE_CONFIRMATION = 'PURGAR'

# Modelos que referencian registros por (res_model, res_id) o (model, res_id)
# pero que NO son evidencia documental ni trazabilidad: suscripciones y estado
# transitorio de UI. Odoo los elimina junto con el registro y no representan
# documentos ni bitácora, por lo que no bloquean la eliminación.
NON_EVIDENCE_GENERIC_MODELS = frozenset([
    'ir.actions.act_window',
    'mail.followers',
    'mail.wizard.invite',
    'payment.link.wizard',
    'portal.share',
    'privacy.lookup.wizard.line',
    'sms.composer',
])

# Modelos con evidencia propia (no se cuentan dos veces en el barrido genérico).
EVIDENCE_MODELS = frozenset(['mail.message', 'ir.attachment'])


class MadenatLumberIntakeGuideLifecycle(models.TransientModel):
    """Diagnóstico y ejecución del ciclo de vida controlado de una Guía."""

    _name = 'madenat.lumber.intake.guide.lifecycle'
    _description = 'Ciclo de vida controlado de Guía (Ingreso de Madera)'

    # ── Modo A en entorno de DESARROLLO (autoservicio) ─────────────────────
    # Categorías puramente DOCUMENTALES de `_trace_blockers`: evidencia
    # consultable que NO representa movimiento real de inventario. Solo el
    # Modo A y solo en una BD de test (`'test' in dbname`) las ignora; el resto
    # de las categorías (materiales) bloquean SIEMPRE.
    # El entorno lo determina `_lifecycle_dev_environment_ok()` →
    # `madenat.sv.internal.marker._sv_test_environment_ok()`, que admite DOS
    # vías: `--test-enable` real (estricta) o el parámetro de sistema
    # `madenat.dev_cleanup_enabled = 'True'` (alternativa de desarrollo, sin
    # `--test-enable` en el servidor persistente).
    # (Fase 2 — Modo A autoservicio en desarrollo.)
    DEV_RELAXABLE_KEYS = ('messages', 'attachments')

    console_id = fields.Many2one(
        'madenat.lumber.intake.console',
        string='Consola',
        ondelete='set null',
    )
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía',
        required=True,
        ondelete='cascade',
    )
    guia_name = fields.Char(
        string='N° Guía', related='guia_processing_id.name', readonly=True)
    guia_state = fields.Selection(
        string='Estado', related='guia_processing_id.state', readonly=True)
    tipo_recepcion = fields.Selection(
        string='Tipo de recepción',
        related='guia_processing_id.tipo_recepcion', readonly=True)
    mode = fields.Selection(
        [
            ('A', 'A. Eliminar definitivamente'),
            ('B', 'B. Cancelar y conservar trazabilidad'),
            ('C', 'C. Purgar de forma controlada'),
            ('D', 'D. Bloquear y escalar'),
        ],
        string='Modo',
        required=True,
        default='D',
    )
    reason = fields.Text(
        string='Motivo',
        required=True,
        help='Motivo obligatorio en todos los modos.',
    )
    acknowledge = fields.Boolean(
        string='Confirmo explícitamente que deseo eliminar definitivamente',
        help='Confirmación explícita requerida por el Modo A.',
    )
    confirmation = fields.Char(
        string='Confirmación escrita',
        help='Escriba exactamente PURGAR para habilitar la purga (Modo C).',
    )
    blockers = fields.Text(
        string='Bloqueadores detectados',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
    )
    blocker_count = fields.Integer(
        string='N° de bloqueadores',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
    )
    purge_blockers = fields.Text(
        string='Bloqueadores de purga',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
    )
    requirements_ok = fields.Boolean(
        string='Precondiciones cumplidas',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
    )
    has_volume_lot = fields.Boolean(
        string='Tiene etiqueta SV',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
    )
    technical_lots_text = fields.Char(
        string='Lotes SV técnicos',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
        help='Lotes vinculados a la guía sin historia material (sin '
             'operaciones SV, sin movimientos y sin quants).',
    )
    # Notas de atribución NO bloqueantes: documentos con número coincidente que
    # se atribuyen positivamente a OTRO documento (p. ej. el ingreso de una
    # recepción homónima). Se muestran separados de los bloqueadores reales
    # para no inducir a error («no bloquea por compartir número»).
    attribution_notes = fields.Text(
        string='Atribución documental (no bloqueante)',
        compute='_compute_lifecycle_diagnostics',
        readonly=True,
        help='Coincidencias de número descartadas por atribución a otro '
             'documento. No representan dependencia de esta guía.',
    )


    # ── Atribución por RELACIONES (no por número textual) ─────────────────
    def _picking_positively_foreign(self, picking, own_lot_ids):
        """Evidencia de que el albarán pertenece a OTRO documento.

        Es la clave para no bloquear por una mera coincidencia de número: un
        albarán que la guía NO documenta (p. ej. el ingreso de una recepción
        homónima) se identifica por (1) su vínculo fuerte con una
        `lumber.reception` o (2) portar únicamente lotes de otro documento
        (`stock.lot.reception_id`) y ninguno de los lotes propios de la guía.
        Sin esta evidencia NO se atribuye ni en un sentido ni en otro.
        """
        fields = picking._fields
        if 'reception_id' in fields and picking.reception_id:
            return True
        line_lots = picking.move_line_ids.mapped('lot_id')
        if line_lots and not (set(line_lots.ids) & set(own_lot_ids)):
            if ('reception_id' in line_lots._fields
                    and line_lots.mapped('reception_id')):
                return True
        return False

    def _classify_guia_pickings(self, guia, own_lot_ids):
        """Clasifica los albaranes candidatos en propios / ambiguos / ajenos.

        Candidato = comparte el número por `origin` o porta un vínculo fuerte
        (FK `guia_processing_id` o un lote propio de la guía).

        Devuelve `(own, ambiguous, foreign, direct_link)`:

        * `own`        → dependencia material REAL (FK o lote propio). Bloquea.
        * `ambiguous`  → coincide el número, sin vínculo verificable ni
                         evidencia de pertenencia a otro documento. Bloquea con
                         mensaje específico (requiere verificación/política).
        * `foreign`    → coincide el número pero se atribuye a otro documento.
                         NO bloquea. Se informa por separado.
        * `direct_link`→ subconjunto de `own` vinculado por el FK fuerte.
        """
        Picking = self.env['stock.picking']
        empty = Picking.browse()
        fields = Picking._fields
        direct_link = (
            Picking.search([('guia_processing_id', '=', guia.id)])
            if 'guia_processing_id' in fields else empty)
        lot_link = (
            Picking.search([('move_ids.move_line_ids.lot_id', 'in',
                             list(own_lot_ids))])
            if own_lot_ids else empty)
        own = direct_link | lot_link
        origin = (
            Picking.search([('origin', '=', guia.name)]) if guia.name
            else empty)
        ambiguous = empty
        foreign = empty
        for picking in (origin - own):
            if self._picking_positively_foreign(picking, own_lot_ids):
                foreign |= picking
            else:
                ambiguous |= picking
        return own, ambiguous, foreign, direct_link

    def _attribution_notes(self, diag):
        """Notas NO bloqueantes (coincidencias descartadas por atribución)."""
        notes = []
        foreign = diag.get('foreign_pickings')
        if foreign:
            notes.append(
                '- %s albarán(es) con número coincidente NO vinculados a la '
                'guía (pertenecen a otro documento): no cuentan como '
                'dependencia.' % len(foreign))
        return notes


    # ── Diagnóstico único de bloqueadores ─────────────────────────────────
    def _lifecycle_diagnosis(self):
        """Inspección de solo lectura de todas las trazas de la Guía.

        Devuelve un diccionario con los recordsets y las listas de
        bloqueadores. No escribe, no crea, no borra y no usa SQL.
        """
        self.ensure_one()
        guia = self.guia_processing_id
        env = self.env
        guia_name = guia.name or ''

        lots = env['stock.lot'].search([
            '|',
            ('volume_source_guia_id', '=', guia.id),
            ('guia_processing_id', '=', guia.id),
        ])
        own_lot_ids = lots.ids
        # Atribución por RELACIONES y cadena documental (no por número textual):
        #   · propios   → FK `guia_processing_id` o lotes propios de la guía.
        #   · ajenos    → coinciden en el número pero pertenecen a otro
        #                 documento (p. ej. una recepción homónima).
        #   · ambiguos  → coinciden en el número sin vínculo verificable.
        (own_pickings, ambiguous_pickings, foreign_pickings,
         direct_link_pickings) = self._classify_guia_pickings(guia, own_lot_ids)
        # Sólo propios y ambiguos son dependencias que bloquean; los ajenos se
        # informan aparte y NO bloquean.
        pickings = own_pickings | ambiguous_pickings
        moves = (env['stock.move'].search(
            [('move_line_ids.lot_id', 'in', own_lot_ids)])
            if own_lot_ids else env['stock.move'])
        move_lines = (env['stock.move.line'].search(
            [('lot_id', 'in', own_lot_ids)]) if own_lot_ids
            else env['stock.move.line'])
        quants = (env['stock.quant'].search([('lot_id', 'in', own_lot_ids)])
                  if own_lot_ids else env['stock.quant'])
        nonzero_quants = quants.filtered(
            lambda q: (q.quantity or 0.0) != 0.0)

        operations = env['madenat.sv.operation'].search([
            '|',
            ('lot_id', 'in', lots.ids),
            ('guia_processing_id', '=', guia.id),
        ])
        applied_ops = operations.filtered(
            lambda o: o.state in ('applied', 'reversed'))
        draft_ops = operations.filtered(lambda o: o.state == 'draft')
        rejected_ops = operations.filtered(lambda o: o.state == 'rejected')

        cost_lines = env['stock.lot.cost.line']
        if 'stock.lot.cost.line' in env:
            cost_lines = env['stock.lot.cost.line'].search([
                '|',
                ('name', '=', 'Servicio %s' % guia_name),
                ('lot_id', 'in', lots.ids),
            ])

        valuations = env['stock.valuation.layer']
        if 'stock.valuation.layer' in env:
            layer = env['stock.valuation.layer']
            if 'lot_id' in layer._fields:
                valuations = layer.search([('lot_id', 'in', lots.ids)])

        billing_lines = env['lumber.billing.consolidation.line']
        if 'lumber.billing.consolidation.line' in env:
            billing_lines = env['lumber.billing.consolidation.line'].search(
                [('lot_id', 'in', lots.ids)])
        consolidations = billing_lines.mapped('consolidation_id')
        invoices = (
            consolidations.mapped('invoice_id')
            if 'invoice_id' in consolidations._fields else consolidations)

        shipment_lines = env['lumber.shipment.line']
        if 'lumber.shipment.line' in env:
            shipment_lines = env['lumber.shipment.line'].search(
                [('lot_id', 'in', lots.ids)])
        containers = shipment_lines.mapped('container_id')
        shipments = shipment_lines.mapped('shipment_id')

        company = getattr(guia, 'company_id', False) or env.company
        guia_date = (
            getattr(guia, 'date_emission', False)
            or fields.Date.context_today(self))
        period_closed = any(
            getattr(company, lock_field, False)
            and guia_date and guia_date <= getattr(company, lock_field)
            for lock_field in ('hard_lock_date', 'fiscalyear_lock_date')
        )

        # ── Evidencia documental y trazabilidad genérica (Modo C/A) ───────
        # Odoo destruye chatter y adjuntos al eliminar el registro
        # (`mail.thread.unlink` borra `mail.message`; `BaseModel.unlink` borra
        # los `ir.attachment` con res_model/res_id). Sin la regla de evidencia
        # esos documentos desaparecerían sin trazabilidad.
        empty_message = env['mail.message']
        messages = (
            self._evidence_messages(guia)
            if 'mail.message' in env else empty_message)

        empty_attachment = env['ir.attachment']
        attachments = empty_attachment.search([
            ('res_model', '=', guia._name),
            ('res_id', '=', guia.id),
        ]) if 'ir.attachment' in env else empty_attachment

        generic_refs = {}
        for model_name in self._generic_reference_models():
            if (model_name in NON_EVIDENCE_GENERIC_MODELS
                    or model_name in EVIDENCE_MODELS):
                continue
            model = env[model_name]
            domain = (
                [('res_model', '=', guia._name), ('res_id', '=', guia.id)]
                if 'res_model' in model._fields
                else [('model', '=', guia._name), ('res_id', '=', guia.id)])
            count = model.sudo().search_count(domain)
            if count:
                generic_refs[model_name] = count

        # Lotes técnicos: sin historia material alguna. Las operaciones SV en
        # BORRADOR no son historia material (el ledger permite eliminarlas);
        # nunca se consideran paquetes, líneas PDF ni filas sintéticas.
        technical_lots = lots.filtered(
            lambda lot: not lot.sv_operation_ids.filtered(
                lambda op: op.state != 'draft')
            and not move_lines.filtered(lambda ml: ml.lot_id == lot)
            and not quants.filtered(lambda q: q.lot_id == lot)
        )
        return {
            'guia': guia,
            'state': guia.state,
            'lots': lots,
            'technical_lots': technical_lots,
            'pickings': pickings,
            'own_pickings': own_pickings,
            'ambiguous_pickings': ambiguous_pickings,
            'foreign_pickings': foreign_pickings,
            'direct_link_pickings': direct_link_pickings,
            'moves': moves,
            'move_lines': move_lines,
            'quants': quants,
            'nonzero_quants': nonzero_quants,
            'operations': operations,
            'applied_ops': applied_ops,
            'draft_ops': draft_ops,
            'rejected_ops': rejected_ops,
            'cost_lines': cost_lines,
            'valuations': valuations,
            'billing_lines': billing_lines,
            'consolidations': consolidations,
            'invoices': invoices,
            'containers': containers,
            'shipments': shipments,
            'period_closed': period_closed,
            'messages': messages,
            'attachments': attachments,
            'generic_refs': generic_refs,
        }


    # ── Evidencia documental ──────────────────────────────────────────────
    @api.model
    def _creation_notice_body(self, record):
        """Texto exacto del aviso automático de creación de `mail.thread`.

        Odoo publica en el alta un mensaje con el cuerpo
        `_('%s created', doc_name)` (ver `mail_thread.py`). Se obtiene del
        propio registro para no depender del idioma ni de la plantilla.
        """
        if not hasattr(record, '_creation_message'):
            return False
        try:
            return str(record._creation_message())
        except Exception:  # pragma: no cover - defensivo
            return False

    def _is_creation_notice(self, message, guia):
        """True solo para el aviso automático de creación (no es evidencia).

        El aviso es una notificación sin adjuntos cuyo cuerpo es exactamente la
        plantilla de alta del propio modelo. Cualquier otro mensaje con
        contenido (comentario, correo o notificación de negocio) sí es
        evidencia documental.
        """
        if message.message_type != 'notification' or message.attachment_ids:
            return False
        expected = self._creation_notice_body(guia)
        if not expected:
            return False
        text = unescape(re.sub(r'<[^>]+>', ' ', message.body or ''))
        return ' '.join(text.split()) == ' '.join(expected.split())

    def _evidence_messages(self, guia):
        """Mensajes de chatter de la guía que son evidencia documental."""
        messages = self.env['mail.message'].search([
            ('model', '=', guia._name),
            ('res_id', '=', guia.id),
        ])
        return messages.filtered(
            lambda message: not self._is_creation_notice(message, guia))

    # ── Barrido genérico de referencias ───────────────────────────────────
    @api.model
    def _generic_reference_models(self):
        """Modelos que referencian registros por (res_model, res_id).

        Barrido acotado del registro de modelos: solo los que exponen ambos
        campos (o `model` + `res_id`, como `mail.message`). Es la lista
        completa de modelos con referencia genérica instalados.
        """
        names = []
        for model_name in self.env.registry:
            field_names = self.env.registry[model_name]._fields
            if 'res_id' not in field_names:
                continue
            if 'res_model' in field_names or 'model' in field_names:
                names.append(model_name)
        return names

    # ── Bloqueadores por modo ─────────────────────────────────────────────
    def _lifecycle_dev_environment_ok(self):
        """Entorno de pruebas (BD de test + --test-enable).

        Delega en la guarda canónica del Programa SV
        (`madenat.sv.internal.marker._sv_test_environment_ok`) para no duplicar
        la definición de «entorno de desarrollo». Defensivo: si el modelo o el
        método no estuvieran disponibles, devuelve False (comportamiento
        estricto, nunca permisivo).
        """
        try:
            return bool(self.env['madenat.sv.internal.marker'].sudo()
                        ._sv_test_environment_ok())
        except Exception:  # pragma: no cover - defensivo
            return False

    def _trace_blockers(self, diag):
        """Trazas que impiden el borrado (Modos A y D).

        Modo A en entorno de PRUEBAS (autoservicio de desarrollo): las trazas
        puramente DOCUMENTALES —chatter (`messages`), adjuntos (`attachments`)
        y referencias genéricas (`generic_refs`)— NO bloquean, porque no
        representan movimiento real de inventario y se destruyen con el propio
        registro eliminado (el snapshot firmado de auditoría conserva su
        inventario: ver `_lifecycle_snapshot`).

        Las trazas MATERIALES (lotes, albaranes, movimientos de stock, líneas
        de movimiento, quants, operaciones SV, líneas de costo, valoración,
        consolidación, facturas, contenedores, embarques y período financiero
        cerrado) bloquean SIEMPRE, también en desarrollo.

        Fuera del Modo A (p. ej. Modo D, que debe mostrar el inventario
        completo) o fuera del entorno de pruebas, el comportamiento es
        IDÉNTICO al anterior: bloquea ante cualquier traza.
        """
        relax_documental = (
            self.mode == 'A' and self._lifecycle_dev_environment_ok())
        labels = (
            ('lots', 'lote(s) vinculados a la guía (incluye lote SV técnico)'),
            ('pickings',
             'albarán(es) vinculados a la guía (vínculo directo o lote '
             'propio) o con atribución textual ambigua pendiente'),
            ('moves', 'movimiento(s) de stock con lote propio de la guía'),
            ('move_lines',
             'línea(s) de movimiento con lote propio de la guía'),
            ('quants', 'registro(s) de stock.quant (incluye saldos en cero)'),
            ('operations', 'operación(es) SV en cualquier estado'),
            ('cost_lines', 'línea(s) de costo'),
            ('valuations', 'capa(s) de valoración'),
            ('consolidations', 'consolidación(es)'),
            ('invoices', 'factura(s)'),
            ('containers', 'contenedor(es)'),
            ('shipments', 'embarque(s)'),
            ('messages', 'mensaje(s) de chatter (evidencia documental)'),
            ('attachments',
             'adjunto(s) de evidencia (documentos PDF/Excel)'),
        )
        messages = []
        for key, label in labels:
            if relax_documental and key in self.DEV_RELAXABLE_KEYS:
                continue
            count = len(diag[key])
            if count:
                messages.append('- %s %s' % (count, label))
        # Desglose específico de los albaranes: vínculo directo (FK) vs
        # coincidencia textual ambigua. No duplica la cuenta: describe el
        # mismo conjunto de `diag['pickings']`.
        direct = diag.get('direct_link_pickings')
        if direct:
            messages.append(
                '  · %s por vínculo directo (guia_processing_id): %s'
                % (len(direct),
                   ', '.join('%s [%s]' % (p.name, p.state) for p in direct)))
        ambiguous = diag.get('ambiguous_pickings')
        if ambiguous:
            messages.append(
                '  · %s con coincidencia textual de número sin vínculo '
                'verificable (atribución ambigua, requiere verificación): %s'
                % (len(ambiguous),
                   ', '.join(p.name for p in ambiguous[:10])))
        if not relax_documental:
            for model_name, count in sorted(diag['generic_refs'].items()):
                messages.append(
                    '- %s referencia(s) genérica(s) por (res_model, res_id) en %s'
                    % (count, model_name))
        if diag['period_closed']:
            messages.append(
                '- período financiero cerrado que cubre la fecha de la guía')
        return messages

    def _purge_blockers(self, diag):
        """Trazas que impiden la purga controlada (Modos C y D)."""
        messages = []
        material_lots = diag['lots'] - diag['technical_lots']
        if material_lots:
            messages.append(
                '- %s lote(s) con historia material (no son lotes técnicos)'
                % len(material_lots))
        if diag['applied_ops']:
            messages.append(
                '- %s operación(es) SV aplicadas o reversadas: nunca se '
                'eliminan del ledger' % len(diag['applied_ops']))
        if diag['rejected_ops']:
            messages.append(
                '- %s operación(es) SV rechazadas: el ledger append-only no '
                'permite eliminarlas' % len(diag['rejected_ops']))
        if diag['nonzero_quants']:
            messages.append(
                '- %s quant(s) con cantidad distinta de cero'
                % len(diag['nonzero_quants']))
        for key, label in (
                ('pickings', 'albarán(es), en cualquier estado'),
                ('moves', 'movimiento(s) de stock'),
                ('move_lines', 'línea(s) de movimiento'),
                ('quants', 'registro(s) de stock.quant (la purga no elimina '
                           'registros de inventario)'),
                ('cost_lines', 'línea(s) de costo'),
                ('valuations', 'capa(s) de valoración'),
                ('consolidations', 'consolidación(es)'),
                ('invoices', 'factura(s)'),
                ('containers', 'contenedor(es)'),
                ('shipments', 'embarque(s)'),
                ('messages', 'mensaje(s) de chatter (evidencia documental)'),
                ('attachments',
                 'adjunto(s) de evidencia (documentos PDF/Excel)')):
            count = len(diag[key])
            if count:
                messages.append('- %s %s' % (count, label))
        for model_name, count in sorted(diag['generic_refs'].items()):
            messages.append(
                '- %s referencia(s) genérica(s) por (res_model, res_id) en %s'
                % (count, model_name))
        if diag['period_closed']:
            messages.append('- período financiero cerrado')
        return messages

    def _delete_access_blocker(self):
        """Pre-chequeo de UX: ¿podrá el usuario ejecutar el `unlink()`?

        Comprueba las DOS condiciones que el servidor exigirá al borrar una
        guía elegible:

        1. permiso efectivo `unlink` (`ir.model.access`) sobre
           `madenat.guia.processing`;
        2. **rol autorizado (H2, FASE 4)**: «Jefatura de Operaciones» o
           administrador del sistema (`_guia_delete_group_ok`), NO el grupo
           técnico de Inventario.

        Devuelve la lista de requisitos faltantes (vacía si el usuario podrá
        ejecutar la eliminación). **No sustituye** la seguridad del servidor:
        solo informa ANTES de ofrecer una ejecución que fallará; la ACL y las
        guardas del modelo siguen aplicándose en el momento real.
        """
        self.ensure_one()
        missing = []
        if not self.env['madenat.guia.processing'].has_access('unlink'):
            missing.append(_(
                'permiso de eliminación (unlink) sobre la Guía '
                '(rol «Jefatura de Operaciones»)'))
        # H2 (FASE 4): el rol lo rige la POLÍTICA de guías (jefatura/sistema),
        # no el grupo técnico `stock.group_stock_manager`.
        if not self.env['madenat.guia.processing']._guia_delete_group_ok():
            missing.append(_('rol «Jefatura de Operaciones»'))
        return missing

    def _lifecycle_blockers(self, diag, mode):
        """Bloqueadores aplicables al modo solicitado (textos únicos)."""
        if mode == 'B':
            return []
        messages = []
        if diag['state'] not in ('draft', 'cancelled'):
            messages.append(
                '- estado "%s": solo se admite Borrador o Cancelado'
                % diag['state'])
        if mode in ('A', 'D'):
            messages.extend(self._trace_blockers(diag))
        if mode in ('C', 'D'):
            messages.extend(self._purge_blockers(diag))
        # Permisos de borrado (A intenta eliminar; C elimina guía + lote).
        if mode in ('A', 'C'):
            for missing in self._delete_access_blocker():
                messages.append('- permiso: falta %s' % missing)
        seen, unique = set(), []
        for message in messages:
            if message not in seen:
                seen.add(message)
                unique.append(message)
        return unique

    # ── Campos computados del asistente ───────────────────────────────────
    @api.depends('guia_processing_id', 'mode', 'acknowledge', 'confirmation')
    def _compute_lifecycle_diagnostics(self):
        for wizard in self:
            diag = wizard._lifecycle_diagnosis()
            blockers = wizard._lifecycle_blockers(diag, wizard.mode)
            wizard.blockers = '\n'.join(blockers) if blockers else False
            wizard.blocker_count = len(blockers)
            purge_blockers = wizard._purge_blockers(diag)
            wizard.purge_blockers = (
                '\n'.join(purge_blockers) if purge_blockers else False)
            wizard.has_volume_lot = bool(diag['lots'])
            wizard.technical_lots_text = ', '.join(
                diag['technical_lots'].mapped('name')) or False
            notes = wizard._attribution_notes(diag)
            wizard.attribution_notes = '\n'.join(notes) if notes else False
            wizard.requirements_ok = wizard._requirements_ok(diag)

    # ── Precondiciones por modo ───────────────────────────────────────────
    def _requirements_ok(self, diag):
        """True solo si el modo elegido tiene todas sus precondiciones."""
        self.ensure_one()
        if self.mode in ('B', 'D'):
            return True
        if self.mode == 'A':
            return not self._lifecycle_blockers(diag, 'A') and bool(
                self.acknowledge)
        if self.mode == 'C':
            return (
                not self._lifecycle_blockers(diag, 'C')
                and (self.confirmation or '').strip() == PURGE_CONFIRMATION
                and self.env.user.has_group(GROUP_JEFATURA)
            )
        return False

    # ── Auditoría firmada (convención madenat.audit.log BT-01) ────────────
    def _lifecycle_log(self, action_type, description, guia, snapshot):
        """Registra el evento firmado. La evidencia sobrevive al borrado."""
        payload = json.dumps(
            snapshot or {}, ensure_ascii=False, sort_keys=True, default=str)
        return self.env['madenat.audit.log'].sudo().create({
            'action_type': action_type,
            'description': description,
            'guia_processing_id': guia.id if guia else False,
            'audit_snapshot': payload,
            'audit_hash': hashlib.sha256(
                payload.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })

    def _lifecycle_snapshot(self, diag, mode):
        """Snapshot determinista del diagnóstico (sin datos mutables)."""
        self.ensure_one()
        return {
            'guia': diag['guia'].name or False,
            'guia_id': diag['guia'].id,
            'state': diag['state'],
            'mode': mode,
            'reason': (self.reason or '').strip(),
            'lots': diag['lots'].mapped('name'),
            'technical_lots': diag['technical_lots'].mapped('name'),
            'pickings': len(diag['pickings']),
            'moves': len(diag['moves']),
            'quants': len(diag['quants']),
            'operations': len(diag['operations']),
            'applied_operations': diag['applied_ops'].mapped('name'),
            'cost_lines': len(diag['cost_lines']),
            'valuations': len(diag['valuations']),
            'consolidations': len(diag['consolidations']),
            'invoices': len(diag['invoices']),
            'containers': len(diag['containers']),
            'shipments': len(diag['shipments']),
            'period_closed': diag['period_closed'],
            'evidence_messages': [
                {'id': message.id,
                 'subject': message.subject or '',
                 'date': str(message.date or '')}
                for message in diag['messages']
            ],
            'evidence_attachments': [
                {'id': attachment.id,
                 'name': attachment.name,
                 'mimetype': attachment.mimetype or ''}
                for attachment in diag['attachments']
            ],
            'generic_references': dict(diag['generic_refs']),
            'blockers': self._lifecycle_blockers(diag, mode),
        }

    # ── Entrada única ─────────────────────────────────────────────────────
    def action_run(self):
        """Ejecuta el modo seleccionado con sus precondiciones."""
        self.ensure_one()
        if not (self.reason or '').strip():
            raise UserError(_('El motivo es obligatorio.'))
        guia = self.guia_processing_id
        diag = self._lifecycle_diagnosis()
        if self.mode == 'D':
            return self._run_block_and_escalate(diag)
        if not self._requirements_ok(diag):
            blockers = self._lifecycle_blockers(diag, self.mode)
            raise UserError(_(
                'El modo %(mode)s no cumple sus precondiciones:\n%(blockers)s'
            ) % {
                'mode': self.mode,
                'blockers': '\n'.join(blockers) or _(
                    '(faltan confirmaciones obligatorias)'),
            })
        if self.mode == 'B':
            return self._run_cancel_and_keep(guia)
        if self.mode == 'A':
            return self._run_delete_definitive(diag)
        return self._run_controlled_purge(diag)

    # ── Modo A ────────────────────────────────────────────────────────────
    def _acquire_delete_lock(self, guia_id):
        """Serializa (best-effort) las eliminaciones Modo A concurrentes.

        Toma un *advisory transaction lock* de PostgreSQL sobre la guía para
        que dos eliminaciones Modo A de la MISMA guía no se intercalen entre la
        validación y el borrado. No es `sudo()`, ni `SQL DELETE`, ni un bypass
        de permisos: es un candado de transacción (se libera solo al terminar
        la transacción). Si el backend no fuese PostgreSQL, se degrada sin
        fallar (la revalidación inmediata y el savepoint siguen aplicando).
        """
        try:
            self.env.cr.execute(
                'SELECT pg_advisory_xact_lock(%s, %s)',
                (0x4D414445, int(guia_id)))
        except Exception:  # pragma: no cover - defensivo
            pass

    def _run_delete_definitive(self, diag):
        """Elimina definitivamente la guía sin ninguna traza registrada.

        Antes de borrar REVALIDA, con el MISMO criterio que el diagnóstico
        (`_lifecycle_diagnosis` + `_lifecycle_blockers`), que no apareció
        ninguna dependencia material/financiera propia ni una atribución
        ambigua. La revalidación y el `unlink()` ocurren en la MISMA
        transacción: si algo falla, el rollback es completo (nunca queda una
        eliminación parcial). El `unlink()` conserva intactas todas las
        protecciones del core y las demás rutas.
        """
        self.ensure_one()
        guia = diag['guia']
        self._acquire_delete_lock(guia.id)

        # Revalidación inmediata (ventana mínima validación → borrado): se
        # relee el estado desde la base y se recalcula el diagnóstico con datos
        # frescos, no con el `diag` previo.
        guia.invalidate_recordset()
        fresh = self._lifecycle_diagnosis()
        if not self.acknowledge:
            raise UserError(_(
                'Debe confirmar explícitamente la eliminación definitiva '
                '(Modo A).'))
        blockers = self._lifecycle_blockers(fresh, 'A')
        if blockers:
            raise UserError(_(
                'La guía %(name)s dejó de cumplir las precondiciones del '
                'Modo A y NO se eliminó:\n%(blockers)s'
            ) % {'name': guia.name or '', 'blockers': '\n'.join(blockers)})

        self._lifecycle_log(
            'guia_delete_permanent',
            _('Eliminación definitiva de la guía %s desde la Consola de '
              'Ingreso de Madera. Motivo: %s')
            % (guia.name, (self.reason or '').strip()),
            guia, self._lifecycle_snapshot(fresh, 'A'))
        # G1 (FASE 3): se comparte la guarda central del core. Aquí ya se
        # auditó con snapshot (`_lifecycle_log`), así que se marca como
        # registrada y se pasa el motivo para no duplicar la bitácora.
        guia.with_context(
            madenat_guia_delete_logged=True,
            madenat_guia_delete_reason=(self.reason or '').strip()).unlink()
        return self._console_reload_action()



    # ── Modo B ────────────────────────────────────────────────────────────
    def _run_cancel_and_keep(self, guia):
        """Cancela conservando la trazabilidad (semántica intacta del core)."""
        self.ensure_one()
        reason = (self.reason or '').strip()
        guia.message_post(
            body=_(
                'Ciclo de vida — cancelación conservando trazabilidad desde la '
                'Consola de Ingreso de Madera. Motivo: %s') % reason,
            message_type='notification',
        )
        # Método canónico existente: no se altera su semántica.
        guia.action_force_cancel()
        return self._notification_action(
            _('Guía %s cancelada') % (guia.name or ''),
            _('Se conservan albaranes, movimientos, retornos, auditoría y '
              'relación histórica. Motivo registrado: %s') % reason,
        )

    # ── Modo C ────────────────────────────────────────────────────────────
    def _run_controlled_purge(self, diag):
        """Purga controlada: guía + lote técnico, sin historia material.

        Orden: operaciones SV en borrador (únicas eliminables legalmente por
        el ledger) → lote técnico → guía. Nunca se nulifica ni se reasigna
        `volume_source_guia_id` sobre un lote sobreviviente: el lote técnico
        se elimina junto con la guía.
        """
        self.ensure_one()
        guia = diag['guia']
        snapshot = self._lifecycle_snapshot(diag, 'C')
        if diag['draft_ops']:
            diag['draft_ops'].unlink()
        technical_lots = diag['technical_lots']
        if technical_lots:
            technical_lots.unlink()
        self._lifecycle_log(
            'guia_purged',
            _('Purga controlada de la guía %s y de %s lote(s) SV técnico(s) '
              'sin historia material, ejecutada por Jefatura de Operaciones. '
              'Motivo: %s')
            % (guia.name, len(technical_lots), (self.reason or '').strip()),
            guia, snapshot)
        # G1 (FASE 3): comparte la guarda central del core y evita duplicar la
        # bitácora (ya registrada arriba con snapshot).
        guia.with_context(
            madenat_guia_delete_logged=True,
            madenat_guia_delete_reason=(self.reason or '').strip()).unlink()
        return self._console_reload_action()

    # ── Modo D ────────────────────────────────────────────────────────────
    def _run_block_and_escalate(self, diag):
        """Bloquea, deja evidencia y ofrece las rutas correctas."""
        self.ensure_one()
        blockers = self._lifecycle_blockers(diag, 'D')
        self._lifecycle_log(
            'guia_delete_blocked',
            _('Intento de eliminación/purga bloqueado para la guía %s. '
              'Motivo declarado: %s')
            % (diag['guia'].name, (self.reason or '').strip()),
            diag['guia'], self._lifecycle_snapshot(diag, 'D'))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'title': _('Eliminación bloqueada — guía %s')
                         % (diag['guia'].name or ''),
                'message': '\n'.join(blockers) or _(
                    'Sin bloqueadores técnicos; la guía requiere gestión '
                    'manual.'),
                'sticky': True,
            },
        }

    # ── Rutas correctas ofrecidas por el Modo D ───────────────────────────
    def action_route_cancel_and_keep(self):
        """Ruta 1: cancelación conservando trazabilidad (Modo B)."""
        self.ensure_one()
        self.write({'mode': 'B'})
        return self.action_run()

    def action_route_open_sv_history(self):
        """Ruta 2: gestionar la etiqueta SV (historial + acciones)."""
        self.ensure_one()
        guia = self.guia_processing_id
        if not guia.volume_lot_id:
            raise UserError(_(
                'La Guía %s no tiene una etiqueta SV asociada.')
                % (guia.name or ''))
        return guia.action_open_sv_history()

    def action_route_regularize_sv(self):
        """Ruta 3: regularización documental del volumen (wizard SV)."""
        self.ensure_one()
        guia = self.guia_processing_id
        if not guia.volume_lot_id:
            raise UserError(_(
                'La Guía %s no tiene una etiqueta SV asociada.')
                % (guia.name or ''))
        return guia.action_sv_regularize_volume()

    # ── Utilidades de retorno ─────────────────────────────────────────────
    def _console_reload_action(self):
        """Vuelve a la Consola de Ingreso de Madera (el registro desapareció)."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ingreso de Madera'),
            'res_model': 'madenat.lumber.intake.console',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def _notification_action(self, title, message):
        """Notificación funcional y cierre del asistente."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': title,
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
