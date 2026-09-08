# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from .intake_constants import CONSOLE_ID_OFFSET

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    _extract_pdf_text,
)


class MadenatLumberIntakeWizard(models.Model):
    _name = 'madenat.lumber.intake.wizard'
    _description = 'Ingreso de Madera — Fachada de ingreso operacional'

    # ─────────────────────────────────────────────────────────────────────
    # Documentos (Excel obligatorio, PDF opcional)
    # ─────────────────────────────────────────────────────────────────────
    excel_file = fields.Binary(string='Packing list Excel', required=True)
    excel_filename = fields.Char(string='Nombre del Excel')

    pdf_file = fields.Binary(string='Guía o documento PDF')
    pdf_filename = fields.Char(string='Nombre del PDF')

    # ─────────────────────────────────────────────────────────────────────
    # Destino
    # ─────────────────────────────────────────────────────────────────────
    tipo_ingreso = fields.Selection(
        [
            ('producto', 'Madera bruta / compra'),
            ('procesado', 'Madera procesada / servicio'),
        ],
        string='Tipo de ingreso',
        default='producto',
        required=True,
    )

    ingestion_profile = fields.Selection(
        [
            ('f1550', 'Madera Aserrada S2S'),
            ('f5085', 'Madera Bruta — Grado Clear'),
            ('metric', 'Madera Bruta — Sistema Métrico'),
        ],
        string='Perfil de lectura',
        default='metric',
        help='Se utiliza únicamente para la vista previa de producto.',
    )

    tipo_ingreso_auto_detectado = fields.Boolean(
        string='Tipo de ingreso detectado automáticamente',
        default=False, copy=False,
        help='True si el contenido del documento permitió clasificar el '
             'tipo de ingreso sin intervención manual.',
    )

    # Patio de asignación para la rama Procesado (required en la Guía).
    # Decisión funcional 2026-08-16: se expone como selector editable para
    # no inventar una ubicación por defecto.
    assignment_location_id = fields.Many2one(
        'stock.location',
        string='Patio de Asignación (Procesado)',
        domain=[('usage', '=', 'internal')],
        help='Solo requerido al derivar a Procesado; se traslada a '
             'madenat.guia.processing.assignment_location_id.',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Estado del wizard (persistente para evidencia e idempotencia)
    # ─────────────────────────────────────────────────────────────────────
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('previewed', 'Leído'),
            ('routed', 'Derivado'),
            ('error', 'Error'),
        ],
        default='draft',
        required=True,
        readonly=True,
    )

    # ─────────────────────────────────────────────────────────────────────
    # Preview (solo Producto) — resumen informativo, no segunda representación
    # ─────────────────────────────────────────────────────────────────────
    preview_data = fields.Text(string='Resumen de lectura', readonly=True)
    preview_line_count = fields.Integer(string='Líneas detectadas', readonly=True)
    preview_total_volume_m3 = fields.Float(
        string='Volumen fuente M3', readonly=True, digits=(16, 6)
    )
    preview_guide_no = fields.Char(string='Guía detectada', readonly=True)
    preview_warnings = fields.Text(string='Advertencias de lectura', readonly=True)

    # ─────────────────────────────────────────────────────────────────────
    # Destino derivado (idempotencia)
    # ─────────────────────────────────────────────────────────────────────
    target_model = fields.Char(readonly=True)
    target_res_id = fields.Integer(readonly=True)
    target_reference = fields.Char(readonly=True)

    error_message = fields.Text(readonly=True)

    # ─────────────────────────────────────────────────────────────────────
    # Detección asistida de destino (no determinista)
    # ─────────────────────────────────────────────────────────────────────
    @api.onchange('excel_filename', 'pdf_filename', 'pdf_file', 'excel_file')
    def _onchange_suggest_tipo_ingreso(self):
        """Clasifica Producto/Procesado por el CONTENIDO del documento.

        AD-61 (2026-09-08): la fuente primaria es el texto extraído del PDF
        (glosa del documento), no el nombre de archivo. El nombre de archivo
        se conserva como señal adicional (OR). Nunca se usa supplier_id/RUT.

        - Match → tipo_ingreso='procesado' y auto_detectado=True.
        - Sin match → auto_detectado=False + warning visible; NO se fuerza
          tipo_ingreso silenciosamente.
        """
        palabras_proceso = ['cepillado', 'servicio', 'proceso', 'maquila']

        for rec in self:
            # Señal adicional (OR): nombre de archivo.
            nombres = ' '.join([
                rec.excel_filename or '',
                rec.pdf_filename or '',
            ]).casefold()

            # Fuente primaria: texto extraído del PDF (glosa del documento).
            texto_pdf = ''
            if rec.pdf_file:
                try:
                    pdf_bytes = base64.b64decode(rec.pdf_file)
                except Exception:
                    pdf_bytes = None
                if pdf_bytes:
                    try:
                        texto_pdf = _extract_pdf_text(
                            pdf_bytes, rec.pdf_filename or 'guia.pdf'
                        )
                    except DocumentExtractionError:
                        texto_pdf = ''

            texto = (nombres + ' ' + texto_pdf).casefold()

            if any(p in texto for p in palabras_proceso):
                rec.tipo_ingreso = 'procesado'
                rec.tipo_ingreso_auto_detectado = True
            else:
                rec.tipo_ingreso_auto_detectado = False
                return {
                    'warning': {
                        'title': _('No se pudo determinar el tipo de ingreso automáticamente'),
                        'message': _(
                            'No fue posible clasificar el documento como Producto '
                            'o Procesado a partir de su contenido. Seleccione '
                            'manualmente el "Tipo de ingreso" antes de continuar.'
                        ),
                    }
                }

    # ─────────────────────────────────────────────────────────────────────
    # Lectura y preview — solo Producto
    # ─────────────────────────────────────────────────────────────────────
    def action_preview_document(self):
        self.ensure_one()

        if not self.excel_file:
            raise UserError(_('Archivo Excel requerido.'))

        if self.tipo_ingreso == 'procesado':
            self.write({
                'preview_data': False,
                'preview_line_count': 0,
                'preview_total_volume_m3': 0.0,
                'preview_guide_no': False,
                'preview_warnings': False,
                'error_message': False,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Ingreso Procesado',
                    'message': (
                        'El documento fue leído correctamente y será interpretado '
                        'por el flujo de Procesados. Se conservará la estructura '
                        'del Excel, incluidos los paquetes agrupados por número de '
                        'lote. Puede continuar el ingreso; posteriormente deberá '
                        'asignar el producto y subproducto antes de enviarlo a stock.'
                    ),
                    'type': 'info',
                    'sticky': True,
                },
            }

        try:
            excel_bytes = base64.b64decode(self.excel_file)
            parsed = self.env['madenat.reception.parser'].parse_excel(
                excel_bytes,
                self.ingestion_profile,
            )
        except (UserError, ValidationError) as e:
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error al leer el documento de Producto:\n%s') % e)

        lines = parsed.get('lines') or []

        preview_lines = []
        for line in lines[:5]:
            preview_lines.append(
                '%s | paquete %s | %s pzs | %s m³' % (
                    line.get('product_code') or '',
                    line.get('package_no') or '',
                    line.get('pieces') or 0,
                    line.get('volume_m3') or 0,
                )
            )

        warnings_text = self._serialize_parser_feedback(parsed)

        self.write({
            'state': 'previewed',
            'preview_data': '\n'.join(preview_lines),
            'preview_line_count': len(lines),
            'preview_total_volume_m3': parsed.get('total_volume_m3') or 0.0,
            'preview_guide_no': parsed.get('guide_no') or False,
            'preview_warnings': warnings_text,
            'error_message': False,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Documento leído',
                'message': '%s líneas detectadas.' % len(lines),
                'type': 'success',
            },
        }

    @api.model
    def _serialize_parser_feedback(self, parsed, max_chars=4000):
        """Serializa avisos/logs del parser de forma legible y acotada."""
        parts = []
        warnings = parsed.get('warnings') or []
        logs = parsed.get('logs') or []
        if warnings:
            parts.extend(str(w) for w in warnings)
        if logs:
            parts.extend(str(l) for l in logs)
        text = '\n'.join(parts).strip()
        if text and len(text) > max_chars:
            text = text[:max_chars] + '…'
        return text or False

    # ─────────────────────────────────────────────────────────────────────
    # Derivación idempotente y segura
    # ─────────────────────────────────────────────────────────────────────
    def action_route_document(self):
        self.ensure_one()

        # Idempotencia: tiene prioridad sobre las guardas de estado. Un wizard
        # ya derivado (state='routed') debe redirigir al destino, no re-validar.
        existing = self._existing_target()
        if existing is not None:
            return self._open_read_view_action(existing)

        self._guard_route_document()

        if self.tipo_ingreso == 'producto':
            return self._route_producto()
        return self._route_procesado()

    def _guard_route_document(self):
        self.ensure_one()

        if not self.excel_file:
            raise UserError(_('Archivo Excel requerido.'))

        if self.tipo_ingreso == 'producto':
            if self.state != 'previewed':
                raise UserError(
                    _('Debe leer el documento (preview) antes de derivar '
                      'a Producto.')
                )
            if not self.pdf_file:
                raise UserError(
                    _('El PDF de Guía es obligatorio para la Recepción de '
                      'Producto (contrato nativo lumber.reception).')
                )
        else:
            if self.state not in ('draft', 'previewed'):
                raise UserError(
                    _('El ingreso Procesado no está en un estado derivable.')
                )
            if not self.assignment_location_id:
                raise UserError(
                    _('Seleccione el Patio de Asignación para derivar a '
                      'Procesado.')
                )

    def _existing_target(self):
        self.ensure_one()
        if not self.target_model or not self.target_res_id:
            return None
        try:
            record = self.env[self.target_model].browse(self.target_res_id)
        except KeyError:
            return None
        return record if record.exists() else None

    # ── Rama Producto ────────────────────────────────────────────────────
    def _route_producto(self):
        self.ensure_one()

        try:
            with self.env.cr.savepoint():
                reception = self.env['lumber.reception'].create({
                    'pdf_file': self.pdf_file,
                    'pdf_filename': self.pdf_filename,
                    'excel_file': self.excel_file,
                    'excel_filename': self.excel_filename,
                    'ingestion_profile': self.ingestion_profile,
                })
                # Método público canónico: Gate0/Gate1 nativos de Recepción.
                reception.action_process_documents()

                self._persist_target(reception)
                self._log_intake_origin(reception)

            # Post-lectura: la única pantalla automática es la CONSOLA de lectura.
            return self._open_read_view_action(reception)
        except (UserError, ValidationError) as e:
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            # Forzar flush: el estado de error debe quedar visible aunque la
            # excepción se re-lance y evite el flush implícito del RPC.
            self.flush_recordset(['state', 'error_message'])
            raise

    # ── Rama Procesado ────────────────────────────────────────────────────
    def _route_procesado(self):
        self.ensure_one()

        try:
            with self.env.cr.savepoint():
                vals = {
                    'excel_file': self.excel_file,
                    'excel_filename': self.excel_filename,
                    'tipo_recepcion': 'service',
                    'intake_direct_stock': True,
                    'assignment_location_id': self.assignment_location_id.id,
                }
                if self.pdf_file:
                    vals['guide_pdf_file'] = self.pdf_file
                    vals['guide_pdf_filename'] = self.pdf_filename

                guia = self.env['madenat.guia.processing'].create(vals)
                # Parser nativo de Guía Processing (forward-fill N° LOTE).
                guia.action_verify_data()

                self._persist_target(guia)
                self._log_intake_origin(guia)

            # Post-lectura: la única pantalla automática es la CONSOLA de lectura.
            return self._open_read_view_action(guia)
        except (UserError, ValidationError) as e:
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            self.flush_recordset(['state', 'error_message'])
            raise

    # ── Persistencia de destino ──────────────────────────────────────────
    def _persist_target(self, destination):
        self.ensure_one()
        self.write({
            'target_model': destination._name,
            'target_res_id': destination.id,
            'target_reference': destination.display_name,
            'state': 'routed',
            'error_message': False,
        })

    def _open_read_view_action(self, destination):
        """Abre la CONSOLA de lectura en el registro del destino derivado.

        Única pantalla automática post-lectura (regla de separación lectura/edición,
        auditoría 2026-08-20). Sigue el patrón validado de:
          intake_guia_processing.action_back_to_intake_console
        El id canónico de consola depende del modelo origen (regla espejo de la
        vista SQL): `madenat.guia.processing` usa CONSOLE_ID_OFFSET + id;
        `lumber.reception` usa id sin offset. NUNCA abre aquí la fachada de
        edición ni el form nativo del core.
        """
        self.ensure_one()
        if destination._name == 'madenat.guia.processing':
            console_res_id = CONSOLE_ID_OFFSET + destination.id
        elif destination._name == 'lumber.reception':
            console_res_id = destination.id
        else:
            raise UserError(_(
                'Modelo destino no soportado por la consola de Ingreso de Madera: %s'
            ) % destination._name)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.lumber.intake.console',
            'res_id': console_res_id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'madenat_lumber_intake.view_madenat_lumber_intake_console_form'
            ).id,
            'target': 'current',
        }

    def _open_edit_view_action(self, destination):
        """Abre la FACHADA EDITABLE de Intake del destino (exclusivamente por
        acción explícita del usuario, ej: 'Modificar origen').

        Conserva el blindaje anti-form-nativo-del-core: cada modelo destino usa
        su fachada Intake correspondiente. No se usa en rutas automáticas del
        wizard. Espejo del mapeo de intake_console.action_open_source.
        """
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'res_model': destination._name,
            'res_id': destination.id,
            'view_mode': 'form',
            'target': 'current',
        }
        if destination._name == 'madenat.guia.processing':
            action['view_id'] = self.env.ref(
                'madenat_lumber_intake.view_madenat_guia_processing_intake_facade_form'
            ).id
        elif destination._name == 'lumber.reception':
            action['view_id'] = self.env.ref(
                'madenat_lumber_intake.view_lumber_reception_intake_facade_form'
            ).id
        return action

    def action_open_intake_target(self):
        """Botón de cabecera: abre la CONSOLA de lectura del destino ya derivado.

        Regla de separación: este botón NUNCA abre edición; la edición queda
        reservada a la acción explícita 'Modificar origen' (intake_console).
        """
        self.ensure_one()
        existing = self._existing_target()
        if existing is None:
            raise UserError(_('No hay un registro creado que abrir.'))
        return self._open_read_view_action(existing)

    # ── Evento de auditoría de origen intake (sin modificar core) ─────────
    def _log_intake_origin(self, destination):
        """Registra exactamente un evento de trazabilidad de punto de entrada.

        Reutiliza el contrato existente de madenat.audit.log sin agregar
        action_type ni campos nuevos (Decisión 2026-08-16):
          - action_type='creation' (semántica existente compatible);
          - description embute tipo/modelo/id/referencia/archivos;
          - batch_id enlaza al registro de wizard para trazabilidad.
        No se guardan binarios, volúmenes recalculados ni firmas.
        """
        self.ensure_one()

        link = {}
        if destination._name == 'lumber.reception':
            link['reception_id'] = destination.id
        elif destination._name == 'madenat.guia.processing':
            link['guia_processing_id'] = destination.id

        guide_no = (self.preview_guide_no or '').strip() or '(sin guía detectada)'

        description = (
            'Registro creado desde Ingreso de Madera (madenat_lumber_intake).\n'
            'Tipo de ingreso: %s\n'
            'Destino: %s #%s (%s)\n'
            'Excel: %s\n'
            'PDF: %s\n'
            'Guía detectada: %s'
            % (
                self.tipo_ingreso,
                destination._name,
                destination.id,
                destination.display_name or '',
                self.excel_filename or '(sin nombre)',
                self.pdf_filename or '(sin PDF)',
                guide_no,
            )
        )

        self.env['madenat.audit.log'].sudo().create(dict(link, **{
            'action_type': 'creation',
            'description': description,
            'batch_id': 'intake:%s' % self.id,
            'user_id': self.env.user.id,
        }))