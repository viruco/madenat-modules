# -*- coding: utf-8 -*-
import base64
import json
import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from .intake_constants import CONSOLE_ID_OFFSET
from .intake_classifier import (
    WEAK_KEYWORDS_DEFAULT,
    advisory_message,
    build_reading_warnings,
    classify,
    collect_signals,
    no_signal_message,
    profile_message,
    unit_message,
    unit_stats,
)

from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    DocumentExtractionError,
    extract_document,
    _extract_pdf_text,
)


class MadenatLumberIntakeWizard(models.Model):
    _name = 'madenat.lumber.intake.wizard'
    _description = 'Ingreso de Madera — Fachada de ingreso operacional'

    # ─────────────────────────────────────────────────────────────────────
    # Documentos (Excel obligatorio, PDF opcional)
    # ─────────────────────────────────────────────────────────────────────
    excel_file = fields.Binary(string='Packing list Excel')
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
            ('granel', 'Madera a granel / volumen total'),
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
        help='Perfil de ingesta aplicado a la lectura previa y transferido al registro derivado (Producto o Procesado).',
    )

    confirm_profile_mismatch = fields.Boolean(
        string='Confirmar discrepancia de perfil',
        default=False,
        help='Marque esta casilla si verificó que el perfil seleccionado es el deseado '
             'a pesar de la advertencia de coherencia entre el perfil y los datos del documento.',
    )
    profile_warning_message = fields.Text(
        string='Advertencia de coherencia de perfil',
        readonly=True,
    )

    tipo_ingreso_auto_detectado = fields.Boolean(
        string='Tipo de ingreso detectado automáticamente',
        default=False, copy=False,
        help='True si el contenido del documento permitió clasificar el '
             'tipo de ingreso sin intervención manual.',
    )

    # Indicador readonly del resultado de clasificación (Producto/Procesado)
    # aplicado al leer el documento. No es editable; informa al operador.
    classification_result = fields.Char(
        string='Clasificación documental detectada', readonly=True,
        help='Resultado de la clasificación Producto/Procesado aplicada al '
             'leer el documento (no cambia al adjuntar archivos).',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Marca de advertencia de lectura (NO bloqueante)
    # ─────────────────────────────────────────────────────────────────────
    reading_warning = fields.Text(
        string='Advertencia de lectura',
        readonly=True,
        copy=False,
        help='Motivos por los que la lectura del documento merece revisión: '
             'sin señal de tipo, perfil de lectura no detectable o distinto '
             'del elegido, unidad no reconocida. Nunca bloquea el ingreso.',
    )
    has_reading_warning = fields.Boolean(
        string='Tiene advertencia de lectura',
        readonly=True,
        copy=False,
        default=False,
    )

    tipo_detalle_granel = fields.Selection(
        [('agregado', 'Consolidado (volumen total de cabecera)'),
         ('linea_por_linea', 'Línea por línea (usar tabla del PDF si existe)')],
        string='Nivel de detalle',
        default='agregado',
        help='Solo aplica a la modalidad "Ingreso por Volúmenes". Define si la '
             'guía crea una única línea consolidada con el volumen total o una '
             'línea real por cada línea de detalle extraída del PDF.',
    )

    # Modalidad de Ingesta: decide el flujo interno del wizard. El Patio de
    # Asignación es únicamente el destino físico; no decide la ruta.
    intake_modality = fields.Selection(
        [
            ('normal', 'Ingesta normal'),
            ('volume', 'Ingreso por Volúmenes'),
        ],
        string='Modalidad de Ingesta',
        required=True,
        default='normal',
        help='Ingesta normal: madera bruta o procesada, la ruta la decide el '
             'tipo de ingreso detectado del documento. Ingreso por Volúmenes: '
             'guías a granel o con volumen total, deriva directo al flujo '
             'Granel.',
    )

    # Patio de Asignación: destino físico del ingreso (no decide la ruta).
    assignment_location_id = fields.Many2one(
        'stock.location',
        string='Patio de Asignación',
        domain=[('usage', '=', 'internal')],
        help='Patio de destino físico del ingreso. Acepta cualquier modalidad '
             'de ingesta; no clasifica ni restringe Producto, Procesado o '
             'Volumen.',
    )

    # Mensaje informativo de requisitos (dependiente de la modalidad).
    requirements_info = fields.Char(
        string='Requisitos del ingreso',
        compute='_compute_requirements_info',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'assignment_location_id' in fields_list and not res.get('assignment_location_id'):
            modality = res.get('intake_modality') or self._context.get('default_intake_modality', 'product')
            target_type = 'service' if modality in ('volume', 'service') else 'port'
            patio, warn = self.env['stock.location'].resolve_patio_by_type(target_type)
            if patio:
                res['assignment_location_id'] = patio.id
        return res

    @api.onchange('intake_modality')
    def _onchange_intake_modality_patio(self):
        if not self.assignment_location_id or (self.assignment_location_id.is_patio and self.assignment_location_id.patio_type):
            target_type = 'service' if self.intake_modality in ('volume', 'service') else 'port'
            patio, warn = self.env['stock.location'].resolve_patio_by_type(target_type)
            if patio:
                self.assignment_location_id = patio

    @api.depends('intake_modality')
    def _compute_requirements_info(self):
        for rec in self:
            if rec.intake_modality == 'volume':
                rec.requirements_info = (
                    'Requisito obligatorio: Patio de Asignación. '
                    'Adjunte al menos una evidencia documental: Guía/PDF, '
                    'Archivo Excel o ambos.'
                )
            else:
                rec.requirements_info = (
                    'Requisitos obligatorios: Guía/PDF, Archivo Excel y Patio '
                    'de Asignación.'
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

    # Resumen documental compacto para Ingreso por Volúmenes (paridad Normal).
    preview_guide_date = fields.Char(string='Fecha guía', readonly=True)
    preview_supplier = fields.Char(string='Proveedor (RUT)', readonly=True)
    preview_oc = fields.Char(string='OC', readonly=True)
    preview_origin = fields.Char(string='Pedido/Origen', readonly=True)
    preview_exchange_rate = fields.Float(
        string='Tipo de cambio', readonly=True, digits=(16, 2))
    preview_total_packages = fields.Integer(string='Paquetes', readonly=True)
    preview_document_lines = fields.Text(string='Detalle documental', readonly=True)
    preview_has_detail = fields.Boolean(string='Tiene detalle', readonly=True)

    # Resultado del nivel de detalle (separado de la selección).
    detalle_aplicado = fields.Selection(
        [('line_by_line', 'Línea por Línea'), ('consolidated', 'Consolidado')],
        string='Nivel aplicado', readonly=True)
    detalle_motivo = fields.Char(string='Motivo', readonly=True)
    preview_line_volume_m3 = fields.Float(
        string='Volumen de líneas', readonly=True, digits=(16, 3))

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
        """Al adjuntar documentos NO se clasifica ni se cambia tipo_ingreso en
        modalidad normal: la clasificación Producto/Procesado ocurre al ejecutar
        'Leer documento'. En modalidad volume la selección manual prevalece
        (tipo_ingreso técnico = granel) y no se emite warning."""
        for rec in self:
            if rec.intake_modality == 'volume':
                rec.tipo_ingreso = 'granel'
                rec.tipo_ingreso_auto_detectado = False
                rec.classification_result = False
                continue
            # normal: no clasificar al adjuntar; solo limpiar indicadores previos.
            rec.tipo_ingreso_auto_detectado = False
            rec.classification_result = False

    @api.onchange('excel_file', 'excel_filename', 'pdf_filename')
    def _onchange_suggest_ingestion_profile(self):
        """Sugiere el perfil de lectura (ingestion_profile) analizando el
        contenido real del Excel con madenat_ingestion_engine.extract_document().

        Reutiliza la detección de perfil (heurística de rango de espesor) del
        motor de ingesta, y un desempate por palabra clave en el nombre de
        archivo para el caso imperial ambiguo (Grado Clear vs S2S).

        Comportamiento "asistido, no determinista", igual que
        _onchange_suggest_tipo_ingreso:
          - Nunca lanza una excepción visible al usuario.
          - Nunca sobrescribe con una decisión de baja confianza; en el caso
            ambiguo, solo advierte, no cambia el valor.
        """
        for rec in self:
            # Volúmenes no usa perfil de lectura: no se sugiere ni modifica.
            if rec.intake_modality == 'volume':
                continue
            if not rec.excel_file:
                continue

            try:
                excel_bytes = base64.b64decode(rec.excel_file)
            except Exception:
                continue

            try:
                result = extract_document(
                    excel_bytes, rec.excel_filename or 'packing.xlsx'
                )
            except (DocumentExtractionError, Exception):
                continue

            detected = getattr(result, 'detected_profile_code', None)

            if detected == 'packing_metrico_aserrada':
                rec.ingestion_profile = 'metric'
                continue

            if detected == 'packing_imperial_blanks':
                nombres = ' '.join([
                    rec.excel_filename or '',
                    rec.pdf_filename or '',
                ]).casefold()

                if 'blank' in nombres or 'clear' in nombres:
                    rec.ingestion_profile = 'f5085'
                elif 's2s' in nombres:
                    rec.ingestion_profile = 'f1550'
                else:
                    return {
                        'warning': {
                            'title': _('Verifique el perfil de lectura antes de continuar'),
                            'message': _(
                                'Este packing está en pulgadas. Por el nombre del archivo no '
                                'fue posible sugerir automáticamente si corresponde a Grado '
                                'Clear (f5085) o S2S (f1550). Seleccione el perfil correcto en '
                                'el campo "Perfil de lectura"; esto no bloquea la lectura, solo '
                                'asegura que se interprete correctamente.'
                            ),
                        }
                    }

    # ─────────────────────────────────────────────────────────────────────
    # Guarda de coherencia de perfil (asistida, no bloqueante)
    # ─────────────────────────────────────────────────────────────────────
    def _check_profile_coherence(self):
        """Verifica coherencia entre el perfil seleccionado y los datos del documento.

        Devuelve un texto de advertencia si detecta inconsistencia, o None si no hay.
        No bloqueante: requiere confirmación explícita (confirm_profile_mismatch).
        """
        self.ensure_one()
        if self.intake_modality == 'volume' or not self.excel_file:
            return None

        try:
            excel_bytes = base64.b64decode(self.excel_file)
            result = extract_document(
                excel_bytes, self.excel_filename or 'packing.xlsx'
            )
        except Exception:
            return None

        lines = result.lines or []
        if not lines:
            return None

        # 1. Perfil f5085 con largos métricos estándar sin pies
        if self.ingestion_profile == 'f5085':
            metric_lengths = []
            has_feet_indicator = False
            for l in lines:
                l_raw = str(l.get('length_value_raw') or '').strip()
                l_unit = str(l.get('length_unit') or '').strip().lower()
                if "'" in l_raw or 'ft' in l_raw or l_unit == 'ft':
                    has_feet_indicator = True
                    break
                try:
                    val = float(l_raw)
                    # Largos típicos en metros con decimales (ej: 3.2, 3.25, 3.7, 4.05) o en mm (> 100)
                    if (1.5 <= val <= 6.5 and (round(val, 2) != round(val, 0) or val in (2.0, 3.0, 4.0, 5.0, 6.0))) or val > 100:
                        metric_lengths.append(l_raw)
                except (ValueError, TypeError):
                    pass

            if metric_lengths and not has_feet_indicator:
                ejemplos = ', '.join(metric_lengths[:3])
                return _(
                    "El perfil seleccionado es 'Madera Bruta — Grado Clear (f5085)', "
                    "pero el documento contiene largos métricos estándar (ej: %s) "
                    "sin indicación de pies (ft). El perfil f5085 interpreta los largos en pies "
                    "y aplica factores imperiales, lo que causará una subestimación severa "
                    "del volumen si las medidas están en metros."
                ) % ejemplos

        # 2. Perfil metric con anchos fraccionarios
        elif self.ingestion_profile == 'metric':
            frac_widths = []
            frac_pattern = re.compile(r'\d+\s+\d+/\d+|\b\d+/\d+|[½¼¾⅜⅝⅞]')
            for l in lines:
                w_raw = str(l.get('width_value_raw') or '').strip()
                if frac_pattern.search(w_raw) or l.get('width_unit') == 'inch':
                    frac_widths.append(w_raw)

            if frac_widths:
                ejemplos = ', '.join(frac_widths[:3])
                return _(
                    "El perfil seleccionado es 'Madera Bruta — Sistema Métrico', "
                    "pero el documento contiene anchos fraccionarios en pulgadas (ej: %s). "
                    "El perfil métrico espera anchos en milímetros y no interpretará "
                    "adecuadamente las fracciones imperiales."
                ) % ejemplos

        return None

    # ─────────────────────────────────────────────────────────────────────
    # Lectura y preview — solo Producto
    # ─────────────────────────────────────────────────────────────────────
    def _resolve_granel_volume(self, result):
        """Resuelve el volumen total de una extracción Granel/Volumen.

        Fuentes en orden:
          1. Total explícito del header (si es > 0).
          2. Suma de volúmenes de las líneas de detalle.
        Devuelve (total_volume_m3, warnings); emite warning de coherencia
        cuando el total explícito y la suma difieren más que la tolerancia.
        """
        warnings = list(result.warnings or [])

        explicit = result.header.get('total_volume_m3')
        line_sum = None
        volumes = [
            l.get('volume_m3')
            for l in (result.lines or [])
            if l.get('volume_m3') is not None
        ]
        if volumes:
            line_sum = round(sum(volumes), 3)

        total = explicit if (explicit is not None and explicit > 0) else None

        if total is not None and line_sum is not None:
            diff = round(abs(total - line_sum), 3)
            if diff > 0.001:
                warnings.append(
                    'Discrepancia de volumen: total explícito %.3f m³ vs suma de '
                    'líneas %.3f m³ (diferencia %.3f m³, tolerancia superada). '
                    'Se usa el total explícito.' % (total, line_sum, diff))
            else:
                warnings.append(
                    'Volumen validado: total explícito %.3f m³ coincide con la '
                    'suma de líneas %.3f m³.' % (total, line_sum))

        if total is None and line_sum is not None and line_sum > 0:
            total = line_sum
            warnings.append(
                'Sin total explícito: se usó la suma de líneas de detalle '
                '(%.3f m³).' % line_sum)

        return total, warnings

    def _preview_volume(self):
        """Lectura para modalidad 'volume': PDF o Excel (al menos uno).

        Extrae el volumen desde la fuente disponible (PDF prioritario, Excel
        como alternativa independiente) y deja el wizard en 'previewed' para
        permitir _route_granel(). No exige tipo_ingreso.
        """
        self.ensure_one()

        if not self.pdf_file and not self.excel_file:
            raise UserError(
                _('Debe adjuntar al menos un documento: Guía/PDF o Packing Excel.'))

        total_volume = 0.0
        guide_no = False
        warnings_text = False
        line_count = 0
        header = {}
        document_lines_text = False
        line_volume = 0.0
        detalle_aplicado = 'consolidated'
        detalle_motivo = False
        extraction_warning = False

        source_bytes = None
        source_filename = None
        if self.pdf_file:
            source_bytes = base64.b64decode(self.pdf_file)
            source_filename = self.pdf_filename or 'guia.pdf'
        elif self.excel_file:
            source_bytes = base64.b64decode(self.excel_file)
            source_filename = self.excel_filename or 'packing.xlsx'
        if source_bytes:
            try:
                result = extract_document(source_bytes, source_filename)
                header = result.header or {}
                total_volume, warnings = self._resolve_granel_volume(result)
                total_volume = total_volume or 0.0
                guide_no = header.get('guide_number') or False
                warnings_text = '\n'.join(warnings) or False
                line_count = len(result.lines or [])

                line_volume = round(
                    sum(l.get('volume_m3') or 0 for l in result.lines), 3) \
                    if result.lines else 0.0

                if self.tipo_detalle_granel == 'linea_por_linea' and result.lines:
                    detalle_aplicado = 'line_by_line'
                    detalle_motivo = False
                else:
                    detalle_aplicado = 'consolidated'
                    detalle_motivo = (
                        'Tabla PDF no reconocida'
                        if self.tipo_detalle_granel == 'linea_por_linea' else False)

                if result.lines:
                    document_lines_text = '\n'.join(
                        '#%d | Lote=%s | Código=%s | %s | Vol=%s m³ | %s | '
                        'Precio=%s | Total=%s' % (
                            idx,
                            l.get('lot_or_package_ref')
                            or l.get('lot_number') or '',
                            l.get('material_code')
                            or l.get('product_code') or '',
                            l.get('description')
                            or l.get('product_name_original') or '',
                            l.get('volume_m3') or 0,
                            l.get('uom') or '',
                            l.get('unit_price') or '',
                            l.get('line_amount') or '',
                        )
                        for idx, l in enumerate(result.lines, start=1)
                    )
            except DocumentExtractionError as e:
                # Volúmenes: la estructura/cabecera no reconocida NO bloquea.
                # Se conserva el adjunto como evidencia y se permite completar
                # cabecera, volumen operativo o detalle manualmente.
                extraction_warning = str(e)
            except Exception as e:
                self.write({'state': 'error', 'error_message': str(e)})
                raise UserError(_('Error inesperado al leer el documento:\n%s') % e)

        if extraction_warning:
            manual_msg = _(
                'No fue posible extraer automáticamente la estructura del '
                'documento. Complete cabecera, volumen operativo o detalle '
                'manualmente.')
            warnings_text = '\n'.join(
                filter(None, [warnings_text, manual_msg])) or False

        self.write({
            'state': 'previewed',
            'preview_data': False,
            'preview_line_count': line_count,
            'preview_total_volume_m3': total_volume,
            'preview_guide_no': guide_no,
            'preview_warnings': warnings_text,
            'preview_guide_date': header.get('guide_date') or False,
            'preview_supplier': header.get('supplier_rut') or False,
            'preview_oc': header.get('oc_reference') or False,
            'preview_origin': header.get('origin_reference') or False,
            'preview_exchange_rate': header.get('exchange_rate') or 0.0,
            'preview_total_packages': header.get('total_packages') or 0,
            'preview_document_lines': document_lines_text,
            'preview_has_detail': bool(document_lines_text),
            'preview_line_volume_m3': line_volume,
            'detalle_aplicado': detalle_aplicado,
            'detalle_motivo': detalle_motivo,
            'error_message': False,
        })

        if extraction_warning:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Documento adjunto conservado'),
                    'message': _(
                        'No fue posible extraer automáticamente la estructura. '
                        'Complete cabecera, volumen operativo o detalle manualmente.'),
                    'type': 'warning',
                    'sticky': True,
                },
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Documento de Volumen leído',
                'message': 'Volumen total detectado: %.3f m³.' % total_volume,
                'type': 'success',
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # Clasificación por señales relevantes (Fase 2A)
    # ─────────────────────────────────────────────────────────────────────
    def _reading_keywords(self):
        """Vocabularios del clasificador: decisivo y de artículo (débil).

        - Decisivo: ``madenat.ingestion.config.get_tipo_ingreso_keywords(
          'procesado')`` (parámetro ``madenat.tipo_ingreso_keywords`` con su
          fallback del núcleo). Sigue siendo la única fuente del vocabulario.
        - Débil: parámetro ``madenat.tipo_ingreso_weak_keywords`` (lista JSON);
          si falta o es inválido se usa ``WEAK_KEYWORDS_DEFAULT`` del código.
        """
        config = self.env['madenat.ingestion.config']
        strong = config.get_tipo_ingreso_keywords('procesado') or []
        weak = list(WEAK_KEYWORDS_DEFAULT)
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'madenat.tipo_ingreso_weak_keywords', '')
        if raw:
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError):
                parsed = None
            if isinstance(parsed, list):
                cleaned = [
                    str(item).strip() for item in parsed if str(item).strip()
                ]
                if cleaned:
                    weak = cleaned
        return strong, weak

    def _extract_pdf_text_safe(self):
        """Texto del PDF adjunto; cadena vacía si no hay o no es legible."""
        if not self.pdf_file:
            return ''
        try:
            return _extract_pdf_text(
                base64.b64decode(self.pdf_file),
                self.pdf_filename or 'guia.pdf') or ''
        except Exception:
            return ''

    def _reading_signals(self, result=None, pdf_text=None):
        """Señales relevantes: archivo, título/glosa del PDF y producto Excel."""
        names = []
        if result is not None:
            for line in result.lines or []:
                name = line.get('description') or line.get('product_name_original')
                if name:
                    names.append(str(name))
        if pdf_text is None:
            pdf_text = self._extract_pdf_text_safe()
        return collect_signals(
            pdf_text=pdf_text,
            filenames=[self.pdf_filename, self.excel_filename],
            excel_product_names=names,
        )

    def _reading_analysis(self, result=None, pdf_text=None):
        """Clasifica y compone la marca de advertencia (nunca bloquea).

        Sin `result` sólo se dispone de PDF + nombres de archivo (rama
        Procesado, que por diseño no invoca el motor). Con `result` se añaden
        nombres de producto del Excel, perfil detectado y unidades de origen.
        """
        strong, weak = self._reading_keywords()
        signals = self._reading_signals(result=result, pdf_text=pdf_text)
        outcome = classify(signals, strong, weak)
        detected = getattr(result, 'detected_profile_code', None) \
            if result is not None else None
        warning = build_reading_warnings(
            no_type_signal=None if outcome['tipo'] else no_signal_message(
                signals, outcome['analyzed']),
            advisory=advisory_message(outcome['advisory']),
            profile=profile_message(detected, self.ingestion_profile)
            if result is not None else '',
            units=unit_message(unit_stats(result.lines))
            if result is not None else '',
        )
        return outcome, warning

    def _write_reading_result(self, outcome, warning):
        """Persiste tipo detectado + marca de advertencia (sin popups)."""
        procesado = outcome['tipo'] == 'procesado'
        self.write({
            'tipo_ingreso': 'procesado' if procesado else 'producto',
            'tipo_ingreso_auto_detectado': procesado,
            'classification_result': 'Procesado' if procesado else 'Producto',
            'reading_warning': warning or False,
            'has_reading_warning': bool(warning),
        })

    def _classify_normal_document(self, pdf_text=None):
        """Clasifica Producto/Procesado desde señales relevantes del documento.

        Señales (documentadas en README §8): nombre de archivo, título del PDF,
        glosa de producto del PDF y —cuando ya se leyó el Excel— nombres de
        producto del motor. Comparación sin acentos, por raíz al inicio de
        palabra y con abreviaturas. El texto legal del PDF se descarta.
        """
        self.ensure_one()
        outcome, warning = self._reading_analysis(pdf_text=pdf_text)
        self._write_reading_result(outcome, warning)
        return outcome

    def action_preview_document(self):
        self.ensure_one()

        # Modalidad por Volúmenes: solo PDF; Excel opcional (respaldo/detalle).
        if self.intake_modality == 'volume':
            return self._preview_volume()

        # Modalidad normal: clasificación Producto/Procesado por contenido real,
        # al ejecutar Leer documento (no al adjuntar). El texto del PDF se
        # extrae una sola vez y se reutiliza en el enriquecimiento posterior.
        pdf_text = self._extract_pdf_text_safe()
        self._classify_normal_document(pdf_text=pdf_text)

        # Normal requiere Excel para el detalle/preview.
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
            result = extract_document(
                excel_bytes, self.excel_filename or 'packing.xlsx'
            )
        except DocumentExtractionError as e:
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error al leer el documento de Producto:\n%s') % e)
        except Exception as e:
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error inesperado al leer el documento:\n%s') % e)

        lines = result.lines or []

        # Enriquecimiento con el Excel ya leído: nombres de producto del motor,
        # perfil detectado y unidades de origen. Nunca bloquea: sólo marca.
        outcome, reading_warning = self._reading_analysis(
            result=result, pdf_text=pdf_text)
        if outcome['tipo'] == 'procesado':
            # Señal decisiva que sólo aporta el Excel → se deriva a Procesado.
            self._write_reading_result(outcome, reading_warning)
        else:
            self.write({
                'reading_warning': reading_warning or False,
                'has_reading_warning': bool(reading_warning),
            })

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

        total_volume = sum((l.get('volume_m3') or 0) for l in lines)
        warnings_text = '\n'.join(result.warnings or []) or False
        if reading_warning:
            warnings_text = (
                reading_warning + '\n' + warnings_text
                if warnings_text else reading_warning
            )

        profile_warning = self._check_profile_coherence()
        if profile_warning:
            self.profile_warning_message = profile_warning
            if warnings_text:
                warnings_text = profile_warning + '\n' + warnings_text
            else:
                warnings_text = profile_warning

        self.write({
            'state': 'previewed',
            'preview_data': '\n'.join(preview_lines),
            'preview_line_count': len(lines),
            'preview_total_volume_m3': total_volume,
            'preview_guide_no': (result.header or {}).get('guide_number') or False,
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

        # Modalidad por Volúmenes → deriva directo al flujo Granel existente.
        if self.intake_modality == 'volume':
            return self._route_granel()

        # Modalidad normal → el tipo de ingreso detectado decide la ruta.
        if self.tipo_ingreso == 'producto':
            return self._route_producto()
        if self.tipo_ingreso == 'procesado':
            return self._route_procesado()

        raise UserError(
            _('No se pudo determinar el tipo de ingreso (Producto o '
              'Procesado) desde el documento. Verifique los archivos o use la '
              'modalidad "Ingreso por Volúmenes" si corresponde.')
        )

    def _guard_route_document(self):
        self.ensure_one()

        if not self.assignment_location_id:
            raise UserError(
                _('Seleccione el Patio de Asignación para continuar el ingreso.')
            )

        if self.assignment_location_id.usage != 'internal':
            raise UserError(
                _('El Patio de Asignación debe ser una ubicación interna.')
            )

        # Documentos independientes: la modalidad Volúmenes acepta PDF o Excel
        # (o ambos); la modalidad normal conserva PDF obligatorio + Excel.
        if self.intake_modality == 'volume':
            if not self.pdf_file and not self.excel_file:
                raise UserError(
                    _('Debe adjuntar al menos un documento: Guía/PDF o Packing Excel.')
                )
        else:
            if not self.pdf_file:
                raise UserError(
                    _('Guía/PDF requerido para continuar el ingreso.')
                )
            if not self.excel_file:
                raise UserError(_('Archivo Excel requerido.'))

        # Validaciones de estado según modalidad y tipo.
        if self.intake_modality == 'normal' and self.tipo_ingreso == 'producto':
            if self.state != 'previewed':
                raise UserError(
                    _('Debe leer el documento (preview) antes de derivar '
                      'a Producto.')
                )
        elif self.state not in ('draft', 'previewed'):
            raise UserError(
                _('El ingreso no está en un estado derivable.')
            )

        # Guarda de coherencia de perfil (ADVERTENCIA con confirmación explícita)
        if self.intake_modality == 'normal':
            profile_warning = self._check_profile_coherence()
            if profile_warning:
                self.profile_warning_message = profile_warning
                if not self.confirm_profile_mismatch:
                    raise UserError(
                        _('⚠️ ADVERTENCIA DE COHERENCIA DE PERFIL:\n\n'
                          '%(warning)s\n\n'
                          'Para continuar de todos modos con este perfil, marque la casilla '
                          '"Confirmar discrepancia de perfil" en el formulario y vuelva a '
                          'presionar "Continuar ingreso".') % {'warning': profile_warning}
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
                    'location_id': self.assignment_location_id.id,
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
                    'guide_pdf_file': self.pdf_file,
                    'guide_pdf_filename': self.pdf_filename,
                    'ingestion_profile': self.ingestion_profile,
                }

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

    # ── Helpers de lectura y conciliación para Volúmenes ────────────────────
    def _read_volume_document(self, is_pdf):
        """Decodifica y extrae un documento (PDF o Excel) o devuelve None."""
        if is_pdf:
            if not self.pdf_file:
                return None
            data = base64.b64decode(self.pdf_file)
            filename = self.pdf_filename or 'guia.pdf'
        else:
            if not self.excel_file:
                return None
            data = base64.b64decode(self.excel_file)
            filename = self.excel_filename or 'packing.xlsx'
        try:
            return extract_document(data, filename)
        except Exception:
            return None

    def _document_volume(self, result):
        """Volumen documental de una extracción (evidencia de la fuente).

        Fase 2 (Bug #1): si la extracción expone el volumen DECLARADO por la
        cabecera del documento (`declared_volume_m3`, solo PDF), ese es el
        volumen documental de la fuente. Si la clave no existe (Excel, o
        extracciones previas al fix), se conserva EXACTAMENTE el
        comportamiento anterior: `total_volume_m3` y, en su defecto, la suma
        de las líneas del detalle.
        """
        if result is None:
            return 0.0
        header = result.header or {}
        declared = header.get('declared_volume_m3')
        if declared is not None and declared > 0:
            return round(float(declared), 3)
        total = header.get('total_volume_m3')
        if total is not None and total > 0:
            return round(float(total), 3)
        line_sum = round(
            sum(l.get('volume_m3') or 0.0 for l in (result.lines or [])), 3)
        return line_sum if line_sum > 0 else 0.0

    def _conciliate_documents(self, pdf_result, excel_result):
        """Compara PDF y Excel y devuelve (status, summary).

        Estados: not_compared (una sola fuente), auto_matched,
        matched_with_differences, incompatible, needs_manual_review.
        """
        if pdf_result is None and excel_result is None:
            return 'not_compared', ''
        if pdf_result is None or excel_result is None:
            return 'not_compared', _('Solo existe una fuente documental.')

        ph = pdf_result.header or {}
        eh = excel_result.header or {}
        p_vol = self._document_volume(pdf_result)
        e_vol = self._document_volume(excel_result)

        diffs = []
        p_guide = str(ph.get('guide_number') or '').strip()
        e_guide = str(eh.get('guide_number') or '').strip()
        if p_guide and e_guide and p_guide != e_guide:
            diffs.append('Nº guía distinto (PDF=%s, Excel=%s)' % (p_guide, e_guide))
        p_rut = str(ph.get('supplier_rut') or '').strip()
        e_rut = str(eh.get('supplier_rut') or '').strip()
        if p_rut and e_rut and p_rut != e_rut:
            diffs.append('RUT proveedor distinto (PDF=%s, Excel=%s)' % (p_rut, e_rut))
        p_oc = str(ph.get('oc_reference') or '').strip()
        e_oc = str(eh.get('oc_reference') or '').strip()
        if p_oc and e_oc and p_oc != e_oc:
            diffs.append('OC distinta (PDF=%s, Excel=%s)' % (p_oc, e_oc))
        if p_vol > 0 and e_vol > 0 and abs(p_vol - e_vol) > 0.001:
            diffs.append('Volumen distinto (PDF=%.3f, Excel=%.3f)' % (p_vol, e_vol))

        strong_conflict = bool(p_guide and e_guide and p_guide != e_guide) or \
            bool(p_rut and e_rut and p_rut != e_rut)

        if strong_conflict:
            status = 'incompatible'
        elif diffs:
            status = 'matched_with_differences'
        elif (p_guide and p_guide == e_guide) or \
                (p_vol > 0 and abs(p_vol - e_vol) <= 0.001):
            status = 'auto_matched'
        else:
            status = 'needs_manual_review'

        summary = '; '.join(diffs) if diffs else _('Documentos coherentes.')
        return status, summary

    def _resolve_operational_volume(self, pdf_vol, excel_vol, detail_sum,
                                    prefer_detail):
        """Prellena el volumen operativo y su fuente (sin borrar evidencia)."""
        if prefer_detail and detail_sum > 0:
            return detail_sum, 'detail'
        if pdf_vol > 0:
            return pdf_vol, 'pdf'
        if excel_vol > 0:
            return excel_vol, 'excel'
        if detail_sum > 0:
            return detail_sum, 'detail'
        return 0.0, 'manual'

    def _build_volume_detail_vals(self, lines, origin):
        """Convierte líneas extraídas a vals de detalle documental.

        Designaciones comerciales por fila (`width_declared`,
        `length_declared`, `thickness_declared`): se persisten SOLO cuando el
        documento las trae explícitas (`*_value_raw` del contrato de
        extracción). Si la clave no existe en la extracción, la celda queda
        vacía: nunca se derivan del encabezado ni se inventan.

        `pieces` (piezas declaradas por línea): la fila transporta el valor
        EXACTO que entregó el motor (`int` cuando el documento declara una
        columna de piezas inequívoca, `None` cuando no la declara). El valor NO
        se persiste en el `create`: lo aplica
        `madenat.lumber.volume.detail.line._apply_documental_pieces()`, único
        escritor, de forma idempotente y protegiendo el ajuste manual. El
        marcador técnico histórico (`pieces=1` de la ruta PDF genérica) fue
        eliminado del motor: ya no existe dato fabricado que transportar.
        """
        vals_list = []
        for idx, line in enumerate(lines or [], start=1):
            vals_list.append({
                'lot_or_package': (
                    line.get('lot_or_package_ref')
                    or line.get('lot_number') or ''),
                'material_code': (
                    line.get('material_code')
                    or line.get('product_code') or ''),
                'description': (
                    line.get('description')
                    or line.get('product_name_original') or ''),
                'volume_m3': line.get('volume_m3') or 0.0,
                'uom': line.get('uom') or '',
                'unit_price': line.get('unit_price') or 0.0,
                'line_amount': line.get('line_amount') or 0.0,
                'width_declared': line.get('width_value_raw') or '',
                'length_declared': line.get('length_value_raw') or '',
                'thickness_declared': line.get('thickness_value_raw') or '',
                'source_page': line.get('source_page') or 0,
                'source_line_no': idx,
                'confidence': line.get('confidence') or 0.0,
                'origin': origin,
                # Solo transporte: lo aplica `_apply_documental_pieces`.
                'pieces': line.get('pieces'),
            })
        return vals_list

    # ── Rama Granel ────────────────────────────────────────────────────────
    def _route_granel(self):
        self.ensure_one()

        try:
            with self.env.cr.savepoint():
                # PDF y Excel son fuentes independientes: se leen por separado.
                pdf_result = self._read_volume_document(is_pdf=True)
                excel_result = self._read_volume_document(is_pdf=False)
                # Documento adjunto pero no extraíble: NO bloquea. Se conserva
                # como evidencia y se permite completar manualmente.
                extraction_failed = (pdf_result is None and excel_result is None)

                # Evidencia original por documento (independiente, no se pisa).
                volume_pdf_m3 = self._document_volume(pdf_result)
                volume_excel_m3 = self._document_volume(excel_result)

                conciliation_status, conciliation_summary = \
                    self._conciliate_documents(pdf_result, excel_result)

                # Detalle documental combinado (PDF + Excel) con origen real.
                detail_vals = []
                if pdf_result and pdf_result.lines:
                    detail_vals += self._build_volume_detail_vals(
                        pdf_result.lines, 'pdf')
                if excel_result and excel_result.lines:
                    detail_vals += self._build_volume_detail_vals(
                        excel_result.lines, 'excel')
                detail_sum = round(sum(v['volume_m3'] for v in detail_vals), 3)

                prefer_detail = (
                    self.tipo_detalle_granel == 'linea_por_linea' and detail_sum > 0)
                operational_volume, operational_source = \
                    self._resolve_operational_volume(
                        volume_pdf_m3, volume_excel_m3, detail_sum, prefer_detail)

                warnings = []
                if pdf_result:
                    warnings = list(pdf_result.warnings or [])
                if excel_result:
                    warnings += list(excel_result.warnings or [])

                if extraction_failed:
                    warnings.append(_(
                        'No fue posible extraer automáticamente la estructura '
                        'del documento. Complete cabecera, volumen operativo o '
                        'detalle manualmente.'))

                # Coherencia interna PDF: total explícito vs suma de detalle.
                if (volume_pdf_m3 > 0 and detail_sum > 0
                        and abs(volume_pdf_m3 - detail_sum) > 0.001):
                    warnings.append(
                        'Discrepancia de volumen: total explícito %.3f m³ vs '
                        'suma de líneas %.3f m³.' % (volume_pdf_m3, detail_sum))

                result = pdf_result or excel_result

                vals = {
                    'tipo_recepcion': 'granel',
                    'intake_direct_stock': False,
                    'assignment_location_id': self.assignment_location_id.id,
                    'guide_pdf_file': self.pdf_file,
                    'guide_pdf_filename': self.pdf_filename,
                    'excel_file': self.excel_file,
                    'excel_filename': self.excel_filename,
                    # Evidencia documental original (inmutable).
                    'volume_pdf_m3': volume_pdf_m3,
                    'volume_excel_m3': volume_excel_m3,
                    # Volumen operativo prellenado (editable en consola).
                    'volume_operational_m3': operational_volume,
                    'volume_operational_source': operational_source,
                    # Conciliación documental PDF–Excel.
                    'conciliation_status': conciliation_status,
                    'conciliation_summary': conciliation_summary,
                    # Retrocompatibilidad: conservar el volumen PDF comercial.
                    'vol_comercial_pdf': volume_pdf_m3 or operational_volume,
                }
                guia = self.env['madenat.guia.processing'].create(vals)

                # Paridad documental: persistir cabecera del PDF en la guía
                # (número, fecha, OC, tipo de cambio y proveedor), igual que la
                # ingesta normal. Sin datos de transporte.
                header = (result.header or {}) if result is not None else {}
                header_update = {}
                if header.get('guide_number'):
                    header_update['name'] = header['guide_number']
                if header.get('guide_date'):
                    header_update['date_emission'] = header['guide_date']
                if header.get('oc_reference'):
                    header_update['oc_reference_raw'] = header['oc_reference']
                if header.get('exchange_rate'):
                    header_update['rate_usd'] = header['exchange_rate']

                supplier_rut = header.get('supplier_rut')
                supplier_name = header.get('supplier_name')
                # Persistir el proveedor documental (nombre y RUT) separado del
                # partner resuelto en Odoo, con fuente y confianza para auditoría.
                header_update['supplier_name'] = supplier_name or False
                header_update['supplier_rut'] = supplier_rut or False
                header_update['supplier_source'] = (
                    header.get('supplier_source') or False)
                header_update['supplier_confidence'] = (
                    header.get('supplier_confidence') or 'none')

                # Resolver partner con AMBOS datos (nombre y RUT) y confianza;
                # nunca solo RUT.
                if supplier_rut or supplier_name:
                    partner = guia._resolve_or_create_supplier(
                        supplier_rut, supplier_name,
                        confidence=header.get('supplier_confidence'),
                    )
                    if partner:
                        header_update['partner_id'] = partner.id
                    header_update['supplier_resolution_status'] = (
                        guia.supplier_resolution_status)
                    header_update['supplier_resolution_note'] = (
                        guia.supplier_resolution_note)

                if header_update:
                    guia.write(header_update)

                # Pedido/Origen se conserva de forma independiente (no se
                # mezcla con la OC). Sin campo equivalente, va al chatter
                # claramente etiquetado.
                if header.get('origin_reference'):
                    guia.message_post(
                        body='Pedido/Origen: %s' % header['origin_reference'])

                # Detalle documental: persiste las líneas realmente extraídas
                # (PDF y/o Excel), conservando el origen de cada fila.
                if detail_vals:
                    # `pieces` viaja en la fila pero NO se crea aquí: lo aplica
                    # `_apply_documental_pieces` (único escritor de piezas
                    # documentales, idempotente y con protección del ajuste
                    # manual).
                    detail_lines = self.env[
                        'madenat.lumber.volume.detail.line'].create([
                            {key: value for key, value in vals.items()
                             if key != 'pieces'} | {'guia_id': guia.id}
                            for vals in detail_vals])
                    pieces_summary = detail_lines._apply_documental_pieces(
                        detail_vals)
                    if pieces_summary['invalid']:
                        warnings.append(_(
                            'Piezas declaradas: %(count)s fila(s) con valor '
                            'ambiguo o inválido en el documento; no se '
                            'persistió cantidad. Referencias: %(refs)s'
                        ) % {
                            'count': len(pieces_summary['invalid']),
                            'refs': ', '.join(pieces_summary['invalid'][:10]),
                        })
                    if pieces_summary['mismatch']:
                        warnings.append(_(
                            'Piezas declaradas: %(count)s fila(s) sin '
                            'equivalencia inequívoca en el detalle '
                            'documental; no se modificó nada. Referencias: '
                            '%(refs)s'
                        ) % {
                            'count': len(pieces_summary['mismatch']),
                            'refs': ', '.join(pieces_summary['mismatch'][:10]),
                        })
                    detail_lines_text = [
                        '#%d | Origen=%s | Lote=%s | Código=%s | %s | Piezas=%s | '
                        'Vol=%s m³ | %s | Precio=%s | Total=%s' % (
                            idx,
                            v['origin'] or '',
                            v['lot_or_package'] or '',
                            v['material_code'] or '',
                            v['description'] or '',
                            detail_lines[idx - 1].pieces or 0,
                            v['volume_m3'] or 0,
                            v['uom'] or '',
                            v['unit_price'] or '',
                            v['line_amount'] or '',
                        )
                        for idx, v in enumerate(detail_vals, start=1)
                    ]
                    guia.message_post(
                        body='Detalle documental: %d líneas estructuradas '
                             'disponibles.\n%s'
                             % (len(detail_lines_text),
                                '\n'.join(detail_lines_text)))
                else:
                    guia.message_post(
                        body='Detalle documental no estructurado para este '
                             'formato. Los adjuntos se conservan como fuente '
                             'documental de consulta.')

                for warning in warnings:
                    guia.message_post(body=warning)

                # Poblar la línea consolidada según el nivel elegido (AD-72).
                # El lote sintético consolidado se crea en la validación usando
                # volume_operational_m3; el staging conserva el detalle elegido.
                raw_lines = []
                if pdf_result and pdf_result.lines:
                    raw_lines += list(pdf_result.lines)
                if excel_result and excel_result.lines:
                    raw_lines += list(excel_result.lines)

                nivel_aplicado = 'consolidated'
                if float_compare(
                        operational_volume, 0.0, precision_rounding=0.001) <= 0:
                    # Sin volumen válido: el usuario completará el volumen
                    # operativo manualmente antes de enviar a stock.
                    guia.message_post(body=_(
                        "Sin volumen válido detectado: complete el volumen "
                        "operativo manualmente antes de enviar a stock."))
                elif self.tipo_detalle_granel == 'linea_por_linea' and raw_lines:
                    guia._create_granel_detail_lines(raw_lines)
                    nivel_aplicado = 'line_by_line'
                else:
                    if self.tipo_detalle_granel == 'linea_por_linea':
                        guia.message_post(body=_(
                            "Nivel solicitado: Línea por Línea. "
                            "Nivel aplicado: Consolidado. "
                            "Motivo: no se pudo reconocer una tabla válida."))
                    guia._create_granel_summary_line(operational_volume)

                # Estado equivalente al post-action_verify_data del flujo Procesado.
                guia.write({'state': 'verified',
                            'detalle_aplicado': nivel_aplicado})

                self._persist_target(guia)
                self._log_intake_origin(guia)

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
            'Guía detectada: %s\n'
            'Advertencia de lectura: %s'
            % (
                self.tipo_ingreso,
                destination._name,
                destination.id,
                destination.display_name or '',
                self.excel_filename or '(sin nombre)',
                self.pdf_filename or '(sin PDF)',
                guide_no,
                self.reading_warning or '(ninguna)',
            )
        )

        self.env['madenat.audit.log'].sudo().create(dict(link, **{
            'action_type': 'creation',
            'description': description,
            'batch_id': 'intake:%s' % self.id,
            'user_id': self.env.user.id,
        }))