# -*- coding: utf-8 -*-
"""
Consola Global de Ingresos (readonly) — madenat_lumber_intake.

Modelo consolidado de SOLO LECTURA sobre una vista SQL que une las dos
fuentes operacionales reales sin duplicar datos de negocio:

  - lumber.reception        -> guías de Producto / Madera Bruta (ingestion_type='product')
  - madenat.guia.processing -> guías Procesadas / Servicios  (ingestion_type='processed')

Propósito:
  Materializar la "puerta única" de Ingreso de Madera como cabina de validación
  previa a stock: el operador sube documentos, revisa un resumen confiable y
  decide entre "Enviar a Stock" o "Modificar origen" para corregir.

Diseño:
  - `_auto = False`: Odoo no crea ni altera una tabla real.
  - `init()`: crea/reemplaza una vista PostgreSQL `madenat_lumber_intake_console`.
  - Campos homogenizados son readonly y nunca se escriben.
  - `source_model` + `source_res_id` permiten abrir el registro origen real.
  - Los campos de resumen (volumen, monto, paquetes, lotes, documentos) son
    computados de forma defensiva leyendo el registro origen; nunca persisten.

Unicidad de `id`:
  - Producto:      id = lumber_reception.id (positivo).
  - Procesado:     id = CONSOLE_ID_OFFSET + madenat_guia_processing.id (offset fijo).
"""
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

from .intake_constants import CONSOLE_ID_OFFSET


class MadenatLumberIntakeConsole(models.Model):
    _name = 'madenat.lumber.intake.console'
    _description = 'Consola de Ingreso de Madera (readonly)'
    _auto = False
    _rec_name = 'guide_name'
    _order = 'guide_date desc, id desc'

    # ---- Identidad de origen (trazabilidad) ----
    source_model = fields.Char(string='Modelo Origen', readonly=True)
    source_res_id = fields.Integer(string='ID Origen', readonly=True)

    # ---- Homologación de negocio ----
    ingestion_type = fields.Selection(
        [('product', 'Producto'), ('processed', 'Procesado')],
        string='Tipo de Ingreso',
        readonly=True,
    )
    guide_name = fields.Char(string='N° Guía', readonly=True)
    guide_date = fields.Date(string='Fecha Guía', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    purchase_id = fields.Many2one('purchase.order', string='Orden de Compra', readonly=True)
    purchase_reference = fields.Char(string='OC', readonly=True)

    # Estado legible de la OC (fuente de verdad: purchase_id). Se usa Selection
    # en lugar de Boolean para renderizar como badge real y evitar el HTML crudo
    # de un checkbox que producía un Boolean con widget="badge".
    oc_pending = fields.Selection(
        [('linked', 'OC vinculada'), ('pending', 'Pendiente de vinculación')],
        string='OC',
        compute='_compute_oc_pending',
        readonly=True,
    )

    @api.depends('purchase_id')
    def _compute_oc_pending(self):
        for rec in self:
            rec.oc_pending = 'linked' if rec.purchase_id else 'pending'

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('processing', 'Procesando'),
            ('verified', 'Verificado'),
            ('done', 'Recibido'),
            ('validated', 'Validada'),
            ('processed', 'Procesada'),
            ('cancel', 'Cancelado'),
            ('error', 'Error'),
            ('pending_link', 'Pendiente OC'),
        ],
        string='Estado',
        readonly=True,
    )

    display_reference = fields.Char(string='Referencia', readonly=True)

    # ---- Microestado de revisión (derivado del origen, readonly) ----
    review_state = fields.Selection(
        [
            ('ready', 'Listo para stock'),
            ('needs_review', 'Requiere revisión'),
            ('sent', 'Enviado a stock'),
            ('cancel', 'Cancelado'),
            ('error', 'Error'),
            ('invalid', 'Sin origen'),
        ],
        string='Estado de revisión',
        compute='_compute_review_state',
        readonly=True,
    )

    # ---- Resumen de decisión (computado, readonly) ----
    total_volume_m3 = fields.Float(
        string='Volumen total (m³)', compute='_compute_review_metrics', readonly=True, digits=(16, 3)
    )
    total_packages = fields.Integer(
        string='Total paquetes', compute='_compute_review_metrics', readonly=True
    )
    total_lots = fields.Integer(
        string='Total lotes/líneas', compute='_compute_review_metrics', readonly=True
    )
    total_amount = fields.Monetary(
        string='Total guía', compute='_compute_review_metrics', readonly=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', compute='_compute_review_metrics', readonly=True
    )

    # ---- Evidencia documental (nombre de archivos cargados) ----
    review_guide_document = fields.Char(
        string='Guía (PDF)', compute='_compute_review_metrics', readonly=True
    )
    review_excel_document = fields.Char(
        string='Packing list (Excel)', compute='_compute_review_metrics', readonly=True
    )

    # ---- Detalle del Packing List (readonly, reusa líneas origen) ----
    # Many2many computados NO almacenados: no crean tabla intermedia ni
    # requieren inverse; resuelven en vivo las líneas del origen real.
    product_packing_line_ids = fields.Many2many(
        'lumber.reception.line',
        string='Líneas de Packing (Producto)',
        compute='_compute_packing_lines',
        readonly=True,
    )
    processed_packing_line_ids = fields.Many2many(
        'madenat.guia.processing.line',
        string='Líneas de Packing (Procesado)',
        compute='_compute_packing_lines',
        readonly=True,
    )
    packing_line_count = fields.Integer(
        string='Líneas del packing', compute='_compute_packing_lines', readonly=True
    )
    packing_volume_total = fields.Float(
        string='Volumen del detalle (m³)', compute='_compute_packing_lines',
        readonly=True, digits=(16, 3),
    )
    stock_volume_total = fields.Float(
        string='Volumen stock (m³)', compute='_compute_packing_lines',
        readonly=True, digits=(16, 3),
    )

    # ------------------------------------------------------------------
    # Cabecera editable no almacenada (2026-08-29)
    # "Ingreso Global" pasa a llamarse "Ingreso de Madera". Estos campos son
    # editables y NO persistidos (store=False): muestran el Producto/Subproducto
    # vigente y retienen la selección temporal del operador. Al guardar (clic en
    # "Aplicar"), el inverse delega en el wizard existente del core; nunca se
    # escribe directamente sobre las líneas.
    # ------------------------------------------------------------------
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        compute='_compute_header_product_id',
        inverse='_inverse_header_product_subproduct',
        store=False,
    )
    subproduct_id = fields.Many2one(
        'madenat.subproducto',
        string='Subproducto',
        compute='_compute_header_subproduct_id',
        inverse='_inverse_header_product_subproduct',
        store=False,
    )

    def init(self):
        """Crea (o reemplaza) la vista SQL consolidada de solo lectura."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS
            SELECT
                lr.id::integer AS id,
                'lumber.reception'::text AS source_model,
                lr.id::integer AS source_res_id,
                'product'::text AS ingestion_type,
                lr.name AS guide_name,
                COALESCE(lr.guia_fecha, lr.reception_date::date) AS guide_date,
                lr.supplier_id AS partner_id,
                lr.purchase_id AS purchase_id,
                lr.purchase_order AS purchase_reference,
                lr.state AS state,
                ('Recepción ' || COALESCE(lr.name, '')) AS display_reference
            FROM lumber_reception lr

            UNION ALL

            SELECT
                ({CONSOLE_ID_OFFSET} + gp.id)::integer AS id,
                'madenat.guia.processing'::text AS source_model,
                gp.id::integer AS source_res_id,
                'processed'::text AS ingestion_type,
                gp.name AS guide_name,
                gp.date_emission AS guide_date,
                gp.partner_id AS partner_id,
                gp.order_id AS purchase_id,
                COALESCE(po.name, gp.oc_reference_raw, '') AS purchase_reference,
                (CASE WHEN gp.state = 'cancelled' THEN 'cancel' ELSE gp.state END) AS state,
                ('Procesada ' || COALESCE(gp.name, '')) AS display_reference
            FROM madenat_guia_processing gp
            LEFT JOIN purchase_order po ON po.id = gp.order_id
            """
        )

    # ------------------------------------------------------------------
    # Origen real
    # ------------------------------------------------------------------
    def _get_source_record(self):
        """Devuelve el registro origen real y existente, o un recordset vacío.

        Defensivo: tolera modelo inexistente y origen borrado sin lanzar
        excepción. Es la base de todo el diagnóstico de la cabina de revisión.
        """
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return None
        try:
            return self.env[self.source_model].browse(self.source_res_id).exists()
        except (KeyError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Microestado de revisión
    # ------------------------------------------------------------------
    @api.depends('state', 'ingestion_type')
    def _compute_review_state(self):
        for rec in self:
            rec.review_state = rec._review_state_for_state(rec.state)

    def _review_state_for_state(self, state):
        """Traduce el estado homologado de la vista SQL al microestado de revisión.

        No requiere leer el origen: `state` ya es una columna de la vista que
        refleja en vivo el estado del registro fuente.
        """
        if self.ingestion_type == 'product':
            mapping = {
                'done': 'sent',
                'verified': 'ready',
                'cancel': 'cancel',
                'error': 'error',
            }
        else:
            mapping = {
                'validated': 'sent',
                'verified': 'ready',
                'processed': 'ready',
                'cancel': 'cancel',
                'error': 'error',
            }
        return mapping.get(state, 'needs_review')

    # ------------------------------------------------------------------
    # Resumen y evidencia documental
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id')
    def _compute_review_metrics(self):
        for rec in self:
            src = rec._get_source_record()
            if src is None:
                rec.total_volume_m3 = 0.0
                rec.total_packages = 0
                rec.total_lots = 0
                rec.total_amount = 0.0
                rec.currency_id = False
                rec.review_guide_document = ''
                rec.review_excel_document = ''
                continue

            if rec.ingestion_type == 'product':
                rec.total_volume_m3 = src.total_volume_m3 or 0.0
                rec.total_packages = src.total_packages or 0
                rec.total_lots = len(src.reception_line_ids)
                rec.total_amount = src.total_amount_clp or 0.0
                rec.currency_id = src.currency_id
                rec.review_guide_document = src.pdf_filename or 'Sin PDF'
                rec.review_excel_document = src.excel_filename or 'Sin Excel'
            else:
                rec.total_volume_m3 = src.vol_total_m3 or 0.0
                rec.total_packages = src.total_paquetes or 0
                rec.total_lots = src.total_lotes_unicos or 0
                # FIX 2026-08-21 (Auditoría 11): total monetario real de la guía
                # Procesados ya existe en additional_cost (Subtotal Neto del PDF);
                # antes se proyectaba 0.0 por hardcode. Criterio aditivo como
                # Producto usa con total_amount_clp.
                rec.total_amount = src.additional_cost or 0.0
                rec.currency_id = src.currency_id
                rec.review_guide_document = src.guide_pdf_filename or 'Sin PDF'
                rec.review_excel_document = src.excel_filename or 'Sin Excel'

    # ------------------------------------------------------------------
    # Detalle del Packing List (readonly, sin side effects)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_packing_lines(self):
        """Resuelve las líneas de detalle del origen real, sin escribir nada.

        - Producto  -> lumber.reception.line (reception_id)
        - Procesado -> madenat.guia.processing.line (processing_id)
        Orden: preserva el orden de inserción (id asc), que en el caso
        verificado (guía 41471) coincide con la secuencia del documento.
        """
        for rec in self:
            product_lines = self.env['lumber.reception.line'].browse()
            processed_lines = self.env['madenat.guia.processing.line'].browse()

            src = rec._get_source_record()

            if src is not None and rec.ingestion_type == 'product':
                product_lines = src.reception_line_ids.sorted(key=lambda l: l.id)
            elif src is not None and rec.ingestion_type == 'processed':
                processed_lines = src.processing_line_ids.sorted(key=lambda l: l.id)

            rec.product_packing_line_ids = product_lines
            rec.processed_packing_line_ids = processed_lines
            rec.packing_line_count = len(product_lines) + len(processed_lines)

            lines = product_lines or processed_lines
            rec.packing_volume_total = sum(
                (l.vol_shipment_m3 or 0.0) for l in lines
            )
            rec.stock_volume_total = sum(
                (l.vol_purchase_m3 or 0.0) for l in lines
            )

    # ------------------------------------------------------------------
    # Cabecera informativa Producto / Subproducto (solo lectura)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_header_product_id(self):
        """Muestra el Producto cuando todas las líneas coinciden."""
        for rec in self:
            rec.product_id = False
            src = rec._get_source_record()
            if not src:
                continue
            lines = (src.reception_line_ids if rec.ingestion_type == 'product'
                     else src.processing_line_ids)
            products = lines.mapped('product_id')
            if products and all(l.product_id == products[0] for l in lines):
                rec.product_id = products[0].id

    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_header_subproduct_id(self):
        """Muestra el Subproducto/Grado cuando todas las líneas coinciden."""
        for rec in self:
            rec.subproduct_id = False
            src = rec._get_source_record()
            if not src:
                continue
            if rec.ingestion_type == 'product':
                lines = src.reception_line_ids
                sub_field = 'subproduct_id'
            else:
                lines = src.processing_line_ids
                sub_field = 'subproducto_id'
            subs = lines.mapped(sub_field)
            if subs and all(l[sub_field] == subs[0] for l in lines):
                rec.subproduct_id = subs[0].id

    def _inverse_header_product_subproduct(self):
        """La cabecera es solo informativa; la aplicación real se hace desde
        el botón 'Aplicar cambios' → wizard → 'Aplicar Cambios'."""
        return True

    def _common_many2one(self, lines, field_name):
        """Devuelve el valor común del campo Many2one si todas las líneas
        coinciden; si hay valores mixtos o vacío, devuelve recordset vacío."""
        values = lines.mapped(field_name)
        if values and all(l[field_name] == values[0] for l in lines):
            return values[0]
        return values.browse()

    def action_apply_product_subproduct(self):
        """Botón 'Aplicar cambios': abre el wizard masivo existente con defaults.

        No ejecuta el wizard silenciosamente; la confirmación explícita ocurre
        en el botón 'Aplicar Cambios' del wizard del core, que escribe
        Producto, Subproducto y nominales sobre las líneas reales.
        """
        self.ensure_one()
        src = self._get_source_record()
        if not src:
            raise UserError(_('El registro origen ya no existe.'))

        if self.ingestion_type == 'product':
            if src.state in ('done', 'cancel', 'error'):
                raise UserError(_('No se puede modificar Producto/Subproducto sobre una recepción ya cerrada o cancelada.'))
            lines = src.reception_line_ids
            common_product = self._common_many2one(lines, 'product_id')
            common_sub = self._common_many2one(lines, 'subproduct_id')
            context = {
                'default_reception_id': src.id,
                'default_ingestion_profile': src.ingestion_profile,
            }
            if common_product:
                context['default_product_id'] = common_product.id
            if common_sub:
                context['default_subproduct_id'] = common_sub.id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Asignación Masiva'),
                'res_model': 'lumber.reception.mass.update',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }

        if src.state in ('validated', 'cancelled'):
            raise UserError(_('No se puede modificar Producto/Subproducto sobre una guía ya validada o cancelada.'))
        lines = src.processing_line_ids
        common_product = self._common_many2one(lines, 'product_id')
        common_sub = self._common_many2one(lines, 'subproducto_id')
        context = {
            'active_id': src.id,
            'active_ids': [src.id],
            'active_model': 'madenat.guia.processing',
        }
        if common_product:
            context['default_product_id'] = common_product.id
        if common_sub:
            context['default_subproducto_id'] = common_sub.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fijar valores comerciales masivos'),
            'res_model': 'madenat.guia.mass.update',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    # ------------------------------------------------------------------
    # Validación previa a stock (errores bloqueantes vs advertencias)
    # ------------------------------------------------------------------
    def _get_ready_for_stock_diagnostics(self):
        """Reúne errores bloquantes y advertencias sin ejecutar nada.

        Separación explícita:
          - errores  -> bloquean `Enviar a Stock`;
          - advertencias -> visibles pero no bloquean.

        No se inventan reglas: se exige lo mínimo indispensable que los
        métodos reales del origen (`action_confirm_reception` /
        `action_validate`) ya necesitan o que impiden una confirmación
        con sentido (guía, fecha, proveedor, tipo, documento y líneas).
        """
        self.ensure_one()
        errors = []
        warnings = []

        if not self.source_model or not self.source_res_id:
            errors.append(_('No hay registro origen vinculado.'))
            return errors, warnings

        src = self._get_source_record()
        if src is None:
            errors.append(_('El registro origen ya no existe.'))
            return errors, warnings

        if not self.guide_name:
            errors.append(_('No se detectó número de guía.'))
        if not self.guide_date:
            errors.append(_('No se detectó fecha documental.'))
        if not self.partner_id:
            errors.append(_('No se resolvió el proveedor.'))
        if not self.ingestion_type:
            errors.append(_('Tipo de ingreso no definido.'))

        if self.ingestion_type == 'product':
            if not src.pdf_file:
                errors.append(_('Falta el PDF de guía de despacho.'))
            if not src.reception_line_ids:
                errors.append(_('No hay líneas de staging verificadas.'))
            if src.state == 'done':
                errors.append(_('La recepción ya fue enviada a stock.'))
            elif src.state != 'verified':
                errors.append(_('La recepción debe estar en estado "Verificado".'))
        else:
            # Regla canónica documental (decisión funcional 2026-08-22):
            # para Procesado el Packing Excel es OBLIGATORIO; el PDF de guía es
            # OPCIONAL (aporta costos/proveedor/OC pero no bloquea el envío).
            if not (src.excel_attachment_id or src.excel_file):
                errors.append(_('❌ Falta el archivo Excel de Packing.'))
            if not src.processing_line_ids:
                errors.append(_('No hay líneas verificadas para procesar.'))
            if src.state == 'validated':
                errors.append(_('La guía ya fue validada a stock.'))
            elif src.state not in ('verified', 'processed'):
                errors.append(_('La guía debe estar "Verificada" para enviarse a stock.'))

        # OC: advertencia fuerte y controlada, nunca bloqueo arbitrario
        # (la exigencia real de OC para "processed" la aplica el propio core
        # en action_validate cuando detecta OC documental sin vínculo).
        if not self.purchase_id and not (self.purchase_reference or '').strip():
            warnings.append(
                _('No se detectó OC vinculada ni referencia de OC. Valide antes de enviar a stock.')
            )

        return errors, warnings

    # ------------------------------------------------------------------
    # Acciones de decisión del header
    # ------------------------------------------------------------------
    def action_send_to_stock(self):
        """Envía el ingreso a stock invocando el método canónico del origen.

        No duplica el flujo: delega en `action_confirm_reception` (producto) o
        `action_validate` (procesado). Protege contra doble ejecución y deja
        rastro en el chatter del origen.
        """
        self.ensure_one()

        errors, warnings = self._get_ready_for_stock_diagnostics()
        if errors:
            raise UserError(
                _('No se puede enviar a stock:\n\n') +
                '\n'.join('- %s' % e for e in errors)
            )

        src = self._get_source_record()
        if not src:
            raise UserError(_('No se pudo recuperar el registro de origen. La operación fue abortada.'))

        if self.ingestion_type == 'product':
            result = src.action_confirm_reception()
        else:
            result = src.action_validate()

        # Trazabilidad en chatter del origen (ambos heredan mail.thread).
        src.message_post(
            body=_('Enviado a stock desde la consola Ingreso de Madera.'),
            message_type='notification',
        )

        if warnings:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Enviado a stock con advertencias'),
                    'message': '\n'.join('- %s' % w for w in warnings),
                    'type': 'warning',
                    'sticky': True,
                },
            }

        return result

    def action_open_source(self):
        """Abre el registro origen real.

        Si el origen ya está en estado terminal (enviado/validado), se abre en
        modo solo lectura usando el mecanismo nativo `flags`.
        """
        self.ensure_one()
        src = self._get_source_record()
        if src is None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Registro no encontrado'),
                    'message': _('El registro de origen ya no existe.'),
                    'type': 'warning',
                },
            }

        action = {
            'type': 'ir.actions.act_window',
            'res_model': self.source_model,
            'res_id': self.source_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

        terminal = False
        if self.ingestion_type == 'product':
            terminal = src.state == 'done'
            # Fachada ligera de Producto: reduce el ruido del form XXL del core
            # y centra la corrección en el packing, sin duplicar lógica.
            action['view_id'] = self.env.ref(
                'madenat_lumber_intake.view_lumber_reception_intake_facade_form'
            ).id
        else:
            terminal = src.state == 'validated'
            # Fachada ligera de Procesados (AD-55): reduce el ruido del form
            # pesado del core y homogeneiza la UX con Producto. NO se toca el
            # core; la vista estándar de madenat.guia.processing permanece como
            # fallback/operación completa.
            action['view_id'] = self.env.ref(
                'madenat_lumber_intake.view_madenat_guia_processing_intake_facade_form'
            ).id

        if terminal:
            action['flags'] = {'mode': 'readonly'}

        # FIX 2026-08-22 (payload views): el action dict interno debe incluir
        # `views` explícito ([view_id, 'form']) porque la client action re-envía
        # el dict a doAction/_preprocessAction que requiere views.map(...).
        action['views'] = [(action['view_id'], 'form')]
        action['view_mode'] = action.get('view_mode', 'form')

        # FIX CABECERA GUÍA ORIGEN (2026-08-22): la fachada no desactiva
        # create, y el modelo es creable → el header mostraba "Nuevo".
        # Se desactiva SOLO la creación en la apertura de la guía (context
        # create=0), preservando edición, paginador y botones de negocio.
        # NO se toca el retorno a Ingreso de Madera (_get_intake_console_action).
        if not terminal:
            ctx = dict(action.get('context') or {})
            ctx['create'] = 0
            # 2026-08-29: los campos informativos de cabecera (Producto/
            # Subproducto) pre-cargan el wizard de asignación masiva vía
            # contexto. El botón "Asignación Masiva"/"Fijar Nominal Masivo" de
            # la fachada los propaga como defaults sin reescribir su lógica.
            if self.product_id:
                ctx['default_product_id'] = self.product_id.id
            if self.subproduct_id:
                ctx['default_subproduct_id'] = self.subproduct_id.id
                # madenat.guia.mass.update usa `subproducto_id` como campo.
                ctx['default_subproducto_id'] = self.subproduct_id.id
            action['context'] = ctx

        # FIX 2026-08-22: envolver en client action para reemplazar el controller
        # actual del action stack y evitar breadcrumbs repetidos del ciclo.
        return {
            'type': 'ir.actions.client',
            'tag': 'madenat_lumber_intake.replace_current_action',
            'params': {'action_to_execute': action},
        }

    # ------------------------------------------------------------------
    # Descarga de documentos del origen (reusa binarios reales)
    # ------------------------------------------------------------------
    def _download_source_field(self, field_name):
        """Acción de descarga nativa para un binario del origen real.

        Blindaje documental: no se genera URL si el binario requerido está
        vacío en el registro origen. La descarga solo es coherente si el
        documento realmente existe; en caso contrario se lanza UserError.
        """
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            raise UserError(_('No hay registro origen vinculado.'))
        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        if not getattr(src, field_name, False):
            if field_name in ('pdf_file', 'guide_pdf_file'):
                raise UserError(_('La guía PDF es obligatoria para esta operación.'))
            raise UserError(_('El archivo de Packing Excel es obligatorio para esta operación.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/%s?download=true' % (
                self.source_model,
                self.source_res_id,
                field_name,
            ),
            'target': 'self',
        }

    def action_download_guide_pdf(self):
        """Descarga la Guía / PDF del origen real (Producto o Procesado)."""
        self.ensure_one()
        field = {'product': 'pdf_file', 'processed': 'guide_pdf_file'}.get(self.ingestion_type)
        if not field:
            raise UserError(_('Tipo de ingesta no soportado para descarga de guía: %s') % self.ingestion_type)
        return self._download_source_field(field)

    def action_download_packing_excel(self):
        """Descarga el Packing list Excel del origen real (Producto o Procesado)."""
        self.ensure_one()
        return self._download_source_field('excel_file')

    # ------------------------------------------------------------------
    # Cancelación controlada del ingreso preliminar (Producto)
    # ------------------------------------------------------------------
    def action_cancel_intake(self):
        """Abre el wizard para capturar el motivo y cancelar un preliminar.

        Regla de avance (no destructiva):
          - "Avanzado" si el origen ya impactó stock: state='done', lot_ids o
            picking_id.
          - En preliminar: abre el wizard de motivo (target=new).
          - En avanzado/cancelado: bloquea con UserError.
        No se borran registros; el cancelado se conserva como evidencia.
        """
        self.ensure_one()
        if self.ingestion_type != 'product':
            raise UserError(_('La cancelación controlada solo está disponible para Producto.'))

        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))

        # Delegación: la condición se evalúa en el helper del registro real;
        # la consola conserva su texto visible ('reiniciar').
        if src._has_intake_stock_advance():
            raise UserError(
                _('El ingreso ya avanzó (enviado a stock). No se puede '
                  'reiniciar de forma preliminar.')
            )
        src._check_intake_can_be_cancelled()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Motivo de cancelación'),
            'res_model': 'madenat.lumber.intake.cancel',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reception_id': src.id},
        }

    def action_reopen_intake(self):
        """Reabre un registro cancelado y preliminar de Producto a `draft`.

        Delegado en `lumber.reception.action_reopen_cancelled_intake()` (intake),
        sin tocar stock ni crear un segundo registro con el mismo name.
        """
        self.ensure_one()
        if self.ingestion_type != 'product':
            raise UserError(_('La reapertura controlada solo está disponible para Producto.'))

        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        src._check_intake_can_be_reopened()

        return src.action_reopen_cancelled_intake()
