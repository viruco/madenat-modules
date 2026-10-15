# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import UserError

class MadenatAuditLog(models.Model):
    _name = 'madenat.audit.log'
    _description = 'Logs de Auditoría MADENAT'
    _order = 'timestamp desc'

    # ══════════════════════════════════════════════════════════════════════
    # H3 (FASE 4) — INMUTABILIDAD MÍNIMA (H-SEC-5)
    # La bitácora es APPEND-ONLY: no se edita ni se borra por ORM, NI con
    # `sudo()`. Única excepción: limpieza de PRUEBAS (test-only, inerte sin
    # `--test-enable` real) que aporta el token de contexto
    # `madenat_sv_test_cleanup_token`.
    # LÍMITE HONESTO: NO impide UPDATE/DELETE por SQL directo ni por un
    # administrador de base de datos (ver CANON/04 AD-105).
    # ══════════════════════════════════════════════════════════════════════
    def _audit_mutation_allowed(self):
        """Única excepción: limpieza de PRUEBAS con token VIVO.

        Exige (1) el token `madenat_sv_test_cleanup_token` en el contexto,
        (2) el entorno de pruebas ESTRICTO (`--test-enable` real + BD de test)
        y (3) que el token corresponda a una limpieza EN CURSO (marcadores
        existentes). Un token arbitrario NO habilita nada.
        """
        token = self.env.context.get('madenat_sv_test_cleanup_token')
        marker = self.env['madenat.sv.internal.marker'].sudo()
        if not token or not marker._sv_test_enable_strict():
            return False
        return bool(marker.search_count([('token', '=', token)]))

    def write(self, vals):
        if self._audit_mutation_allowed():
            return super().write(vals)
        raise UserError(_(
            'La bitácora de auditoría (madenat.audit.log) es APPEND-ONLY: no '
            'se puede modificar. Registre una CORRECCIÓN como un evento NUEVO, '
            'nunca editando el registro anterior.'))

    def unlink(self):
        if self._audit_mutation_allowed():
            return super().unlink()
        raise UserError(_(
            'La bitácora de auditoría (madenat.audit.log) es APPEND-ONLY: no '
            'se puede eliminar. Registre una CORRECCIÓN como un evento NUEVO.'))

    reception_id = fields.Many2one('lumber.reception', string='Recepción', ondelete='cascade')
    # ══════════════════════════════════════════════════════════════════════════
    # BT-01 (2026-08-16): vínculo canónico al flujo de guías procesadas.
    # ondelete='set null' conserva la evidencia firmada si la guía se elimina;
    # NO replica 'cascade' para no destruir la bitácora inmutable.
    # ══════════════════════════════════════════════════════════════════════════
    guia_processing_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía de Procesamiento',
        ondelete='set null',
        index=True,
        help='Evento de auditoría originado en una guía procesada.'
    )
    action_type = fields.Selection([
        ('creation', 'Creación Producto'),
        ('omission', 'Omisión Producto'),
        ('lot_creation', 'Creación Lote'),
        ('lot_update', 'Actualización Lote'),
        # BT-04: salida controlada del material crudo hacia proceso (solo service).
        ('consumption', 'Salida a Proceso'),
        # BT-01: firma criptográfica de un ciclo de validación de guía procesada.
        ('validation_signature', 'Firma de Validación'),
        # AD-73: reclasificación de tipo de ingreso previa a Gate 3 (Intake).
        ('reclassification', 'Reclasificación de Tipo de Ingreso'),
        # Ingreso por Volúmenes: edición controlada del volumen operativo y
        # confirmación manual de conciliación documental (Intake).
        ('volume_operational_update', 'Actualización Volumen Operativo'),
        ('conciliation_manual_confirm', 'Confirmación Manual de Conciliación'),
        # Programa SV: operación del ledger de etiquetas SV (rename,
        # regularización de volumen, rebaja y reversa de rebaja).
        ('sv_operation', 'Operación de Etiqueta SV'),
        # Fase 2 (AD-80): ciclo de vida controlado de guías desde la Consola
        # de Ingreso de Madera. El bloqueo se registra SIEMPRE (incluso sin
        # borrado); la eliminación definitiva y la purga controlada dejan su
        # evento firmado y sobreviven al borrado de la guía
        # (`guia_processing_id` es `ondelete='set null'`).
        ('guia_delete_blocked', 'Eliminación de Guía Bloqueada'),
        ('guia_delete_permanent', 'Eliminación Definitiva de Guía'),
        ('guia_purged', 'Purga Controlada de Guía'),
        # AD-82 / CANON/18: rebaja de inventario de contenedor/embarque y su
        # reversa (salida nativa única y su retorno).
        ('rebaja', 'Rebaja de Contenedor'),
        ('rebaja_reverse', 'Reversa de Rebaja de Contenedor'),
        # Sub-bloque 4B (2026-10-04) — R2: retorno FÍSICO TOTAL de la rebaja de
        # un Contenedor (Customers → ubicación interna de origen, mismo lote,
        # `origin_returned_move_id`) con evidencia determinista. Valor ADITIVO
        # al Selection (no reemplaza a 'rebaja'/'rebaja_reverse').
        ('rebaja_return_total', 'Retorno Físico Total de Rebaja'),
        # AD-88 (2026-10-01): desviación aceptada con motivo (advertencia no
        # bloqueante) — zarpe con excepción, reversa con override de Gerencia,
        # etc. El código (p. ej. 'B-01') va en la descripción/batch_id.
        ('deviation', 'Desviación Aceptada con Motivo'),
        # I1 canónico (CANON/19 §16, 2026-10-02): envío de lotes a la
        # ubicación de un procesador mediante transferencia interna nativa.
        # Valor ADITIVO al Selection (no reemplaza a 'rebaja'/'deviation').
        ('processor_shipment', 'Envío a Procesador'),
        # I2 (CANON/19 v1.6.0 / AD-91, 2026-10-02): imputación DOCUMENTAL de
        # etiquetas procesadas contra SV por guía (sin efecto en stock) y su
        # reversa. Valores ADITIVOS al Selection.
        ('imputation', 'Imputación Documental SV'),
        ('imputation_reverse', 'Reversa de Imputación Documental SV'),
        # RESET (2026-10-11): ciclo de mantenimiento de la imputación documental
        # — anulación (draft/pending → cancelled) y REAPERTURA controlada
        # (cancelled → draft, «Volver a borrador»). Valores ADITIVOS.
        ('imputation_cancel', 'Anulación de Imputación Documental SV'),
        ('imputation_reopen', 'Reapertura de Imputación Documental SV'),
        # AD-92 (2026-10-05): rolleo centrado en Embarque.
        ('vessel_rollover', 'Rolleo de Embarque'),
        ('vessel_rollover_item', 'Detalle de Rolleo de Embarque'),
        # AD-93 (2026-10-05): Borrador Seguro autónomo — retorno administrativo
        # de un Embarque confirmed → draft. Evento append-only con snapshot
        # determinista y firma SHA-256. Valor ADITIVO al Selection.
        ('shipment_return_to_draft', 'Retorno Seguro a Borrador'),
        # Sub-bloque 3 (2026-10-04): zarpe con excepción documental B-01
        # (Contenedores sin rebaja física). Evento append-only con snapshot
        # determinista y firma SHA-256. Valor ADITIVO al Selection.
        ('b01_departure_exception', 'Zarpe con Excepción B-01'),
        # Sub-bloque 4A (2026-10-04): regularización B-01 (R1, rebaja
        # extemporánea por evidencia física real) y su cierre controlado
        # open → resolved (R4). Eventos append-only con snapshot determinista
        # y firma SHA-256. Valores ADITIVOS al Selection.
        ('b01_regularization', 'Regularización B-01'),
        ('b01_resolution', 'Cierre de Excepción B-01'),
        # Sub-bloque 5 (2026-10-04): Entrega/Cierre seguro de Embarque
        # (Política D2, AD-98, hito logístico controlado). Evento append-only
        # con snapshot determinista y firma SHA-256. Valor ADITIVO al Selection.
        ('shipment_delivery', 'Entrega de Embarque'),
        # Sub-bloque 6 (2026-10-04): Costeo provisional post-Entrega (Política
        # C2). Distribución por volumen logístico final por lote, su
        # redistribución formal (supersede de costos tardíos) y su anulación.
        # Eventos append-only con snapshot determinista y firma SHA-256.
        # Valores ADITIVOS al Selection (no reemplazan a otros).
        ('shipment_cost_distribution',
         'Distribución de Costos de Embarque'),
        ('shipment_cost_distribution_supersede',
         'Redistribución de Costos de Embarque'),
        ('shipment_cost_distribution_cancel',
         'Anulación de Distribución de Costos'),
        # AD-100 (2026-10-05): workflow NO bloqueante del Backlog Documental.
        # Escalamiento, cierre y exoneración de `lumber.shipment.document` con
        # snapshot determinista y firma SHA-256 + chatter. Valores ADITIVOS al
        # Selection (no reemplazan a D2/C2/R1/R2).
        ('documentary_backlog_escalation',
         'Escalamiento de Backlog Documental'),
        ('documentary_backlog_completion',
         'Cierre de Backlog Documental'),
        ('documentary_backlog_waiver',
         'Exoneración de Backlog Documental'),
        # Bloque A (CANON/19 §19.11, 2026-10-10): relación de conciliación
        # envío a procesador ↔ retorno (registro y reversa). Eventos
        # append-only con snapshot determinista y firma SHA-256. Valores
        # ADITIVOS al Selection (no reemplazan a otros).
        ('processor_return_link',
         'Conciliación Envío–Retorno (procesador)'),
        ('processor_return_link_reverse',
         'Reversa de Conciliación Envío–Retorno'),
    ], string='Tipo de Acción', required=True)
    # ══════════════════════════════════════════════════════════════════════════
    # BT-01: evidencia firmada. La bitácora es la fuente de verdad inmutable.
    # Recepción no los escribe (NULL por defecto); guías procesadas sí.
    # ══════════════════════════════════════════════════════════════════════════
    audit_snapshot = fields.Text(string='Snapshot JSON', readonly=True)
    audit_hash = fields.Char(string='Firma SHA-256', readonly=True)
    description = fields.Text(string='Descripción', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    batch_id = fields.Char(string='ID de Lote')
    month = fields.Char(string='Mes (YYYY-MM)', compute='_compute_month', store=True)

    @api.depends('timestamp')
    def _compute_month(self):
        for log in self:
            log.month = log.timestamp.strftime('%Y-%m') if log.timestamp else False