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

from .intake_constants import (
    CONSOLE_ID_OFFSET,
    DECLARED_GUIA_ID_CONTEXT,
    DECLARED_MANUAL_ENTRY_CONTEXT,
    HEADER_DECLARED_DESCRIPTION,
    HEADER_DECLARED_ORIGIN,
)


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
        [('product', 'Producto'), ('processed', 'Procesado'),
         ('volume', 'Ingreso por Volúmenes')],
        string='Tipo de Ingreso',
        readonly=True,
    )
    guide_name = fields.Char(string='N° Guía', readonly=True)
    guide_date = fields.Date(string='Fecha Guía', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    purchase_id = fields.Many2one('purchase.order', string='Orden de Compra', readonly=True)
    purchase_reference = fields.Char(string='OC', readonly=True)

    # ── Columnas REALES de la vista SQL (2026-10-07) ───────────────────────
    # Añadidas para que columna, búsqueda y agrupación lean el MISMO dato
    # (sin depender de compute no almacenado). El `init()` las proyecta desde
    # los orígenes; NO alteran `id`/`source_res_id` ni la resolución de filas.
    oc_documental = fields.Char(
        string='OC documental', readonly=True,
        help='Referencia de OC extraída del documento (oc_reference_raw del '
             'origen). NO se sustituye por el nombre de la OC vinculada. La '
             'OC interna vinculada se consulta en «OC vinculada».',
    )
    guide_date_kind = fields.Selection(
        [('emission', 'Emisión de guía (documento)'),
         ('reception', 'Recepción al sistema')],
        string='Origen de fecha', readonly=True,
        help='Significado real de «Fecha de guía»: emisión documental de la '
             'guía o, en Producto sin fecha de guía, fecha de recepción.',
    )
    processor_id = fields.Many2one(
        'res.partner', string='Procesador', readonly=True,
        help='Planta procesadora tomada de la relación existente de la Orden '
             'de Procesamiento (toll_order_id.processor_id). Nunca se usa el '
             'proveedor como procesador.',
    )
    location_id = fields.Many2one(
        'stock.location', string='Patio / Ubicación', readonly=True,
        help='Patio o ubicación de asignación física de la recepción o guía.',
    )
    is_patio = fields.Boolean(
        string='Es Patio', readonly=True,
        help='Indica si la ubicación de asignación es un patio operativo clasificado.',
    )

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

    # ── OC documento y Estado OC documental (3 estados) ───────────────────
    # Proxies readonly NO almacenados: la consola es una vista SQL y no admite
    # columnas. `oc_reference_documental` lee EXCLUSIVAMENTE `oc_reference_raw`
    # del origen real (referencia extraída del documento, que NUNCA se
    # sobrescribe al vincular una `purchase.order` y que tampoco se reemplaza
    # por el nombre de la OC vinculada). `oc_documentary_status` distingue el
    # vínculo operativo del dato documental: sin OC vinculada y sin referencia
    # documental el documento NO indicó OC (jamás se implica lo contrario).
    # Lectura pura: no escriben Guía, OC, proveedor, recepción ni stock, y no
    # redefinen `oc_pending` (operativo, intacto).
    oc_reference_documental = fields.Char(
        string='OC documento',
        compute='_compute_oc_documentary_status',
        readonly=True,
    )
    oc_documentary_status = fields.Selection(
        [('linked', 'Vinculada'),
         ('pending', 'Pendiente de vinculación'),
         ('not_informed', 'No indicada en documento')],
        string='Estado OC',
        compute='_compute_oc_documentary_status',
        readonly=True,
    )

    @api.depends('source_model', 'source_res_id', 'purchase_id')
    def _compute_oc_documentary_status(self):
        """Referencia documental de OC y su estado documental (3 estados).

        - `purchase_id` presente → 'linked' (OC interna vinculada).
        - Sin vínculo pero con referencia documental → 'pending'.
        - Sin vínculo y sin referencia documental → 'not_informed'.

        Lectura pura y defensiva: si el origen ya no existe (o no expone
        `oc_reference_raw`) los proxies quedan neutros. Nunca escribe nada.
        """
        for rec in self:
            rec.oc_reference_documental = False
            rec.oc_documentary_status = 'not_informed'
            reference = ''
            src = rec._get_source_record()
            if src is not None:
                reference = getattr(src, 'oc_reference_raw', '') or ''
            rec.oc_reference_documental = reference or False
            if rec.purchase_id:
                rec.oc_documentary_status = 'linked'
            elif reference:
                rec.oc_documentary_status = 'pending'

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
            ('documental_pending', 'Pendiente documental'),
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

    # ---- Evidencia documental Procesado (proxies read-only hacia origen) ----
    # No escriben en la fuente, no tienen inverse ni columna SQL: leen el
    # registro origen real vía _get_source_record(). Solo aplican a
    # ingestion_type == 'processed'; el resto queda en valores neutros.
    vol_comercial_pdf = fields.Float(
        string='Vol. Guía PDF (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    packing_volume_declared_m3 = fields.Float(
        string='Vol. Packing (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    sum_vol_documental_m3 = fields.Float(
        string='Suma líneas Packing (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    diff_pdf_packing_m3 = fields.Float(
        string='Δ PDF vs Packing (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    diff_packing_lineas_m3 = fields.Float(
        string='Δ Packing vs Líneas (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    documental_conciliation_state = fields.Selection(
        [('not_available', 'Sin evidencia'), ('partial', 'Parcial'),
         ('consistent', 'Consistente'), ('ok_rounded', 'Consistente por redondeo'),
         ('difference', 'Con diferencia')],
        string='Conciliación documental', compute='_compute_review_metrics',
        readonly=True)
    packing_pieces_declared = fields.Integer(
        string='Piezas Packing', compute='_compute_review_metrics', readonly=True)
    packing_package_count_declared = fields.Integer(
        string='Paquetes Packing', compute='_compute_review_metrics', readonly=True)

    # ---- Volumen de compra y de embarque (proxies read-only, Q1 / R07) ----
    # P1 (2026-10-10): presentación explícita de las dos magnitudes distintas
    # del volumen para que el operador no infiera que una reemplaza a la otra.
    # `vol_compra_m3` = Σ del volumen de compra/físico real de las líneas
    # (geometría real del packing); `vol_embarque_m3` = Σ del volumen de
    # embarque (espesor nominal y ancho +1/8"). NO alteran fórmula, unidad,
    # precisión ni valores: sólo proyectan, sin escribir, el origen real.
    vol_compra_m3 = fields.Float(
        string='Vol. compra (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3),
        help='Σ del volumen de compra/físico real de las líneas '
             '(geometría real del packing). Magnitud distinta del '
             'volumen de embarque.')
    vol_embarque_m3 = fields.Float(
        string='Vol. embarque (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3),
        help='Σ del volumen de embarque (espesor nominal y ancho +1/8 '
             'pulgada). Volumen comercial distinto del de compra/físico.')
    documental_pending_count = fields.Integer(
        string='Líneas documentales pendientes',
        compute='_compute_documental_pending_count', readonly=True)

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

    # ---- Ingreso por Volúmenes (bloque compacto informativo) ----
    # El volumen declarado en PDF es evidencia documental (vol_comercial_pdf);
    # el volumen registrado para stock es el de la única línea consolidada.
    volumen_pdf_m3 = fields.Float(
        string='Volumen declarado en PDF (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))
    volumen_stock_m3 = fields.Float(
        string='Volumen registrado para Stock (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))
    volumen_diff_m3 = fields.Float(
        string='Diferencia (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))
    volumen_suma_detalle = fields.Float(
        string='Suma de detalle (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))
    volumen_fuente = fields.Char(
        string='Fuente', compute='_compute_review_metrics', readonly=True)

    # ── Volumen OFICIAL único (solo Volúmenes) ──
    # Proxies readonly y no almacenados: la consola es una vista SQL y no se
    # agregan columnas. Leen EXCLUSIVAMENTE la API canónica de la guía origen
    # (`official_volume_m3` / `official_volume_source` /
    # `official_vs_detail_diff_m3`), sin duplicar la precedencia y sin escribir
    # guía, lote, stock, picking, secuencia, bitácora ni workflow.
    official_volume_m3 = fields.Float(
        string='Volumen Oficial de la Guía (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))
    official_volume_source = fields.Char(
        string='Fuente del volumen oficial',
        compute='_compute_review_metrics', readonly=True)
    official_vs_detail_diff_m3 = fields.Float(
        string='Diferencia vs volumen oficial (m³)',
        compute='_compute_review_metrics', readonly=True, digits=(16, 3))

    # ── Volumen OFICIAL VIGENTE (Fase 2 — pantalla operativa de Volumen) ──
    # Proxies readonly NO almacenados (la consola es una vista SQL: no se
    # agregan columnas). Expresan el volumen oficial que gobierna la pantalla
    # operativa del Ingreso por Volúmenes:
    #   - Con regularización aplicada en la etiqueta SV real rige el baseline
    #     regularizado de `stock.lot` (`sv_regularized_baseline_m3`) y la
    #     fuente es "Regularización Operaciones".
    #   - Sin regularización aplicada rige el volumen oficial documental de la
    #     Guía (`official_volume_m3` / `official_volume_source`, leídos de la
    #     API canónica `get_official_volume_m3()`), con su fuente
    #     ("Guía PDF" / "Packing Excel" / "Packing declarado").
    # Lectura pura: no escribe `stock.lot`, la Guía, el ledger SV ni stock, y
    # nunca modifica `official_volume_m3`.
    official_volume_effective_m3 = fields.Float(
        string='Volumen oficial vigente',
        compute='_compute_official_volume_effective',
        store=False, readonly=True, digits=(16, 3))
    official_volume_effective_source = fields.Char(
        string='Fuente del volumen oficial vigente',
        compute='_compute_official_volume_effective',
        store=False, readonly=True)

    # Proveedor documental (emisor del PDF) y estado de resolución, expuestos
    # desde el origen para mostrar el emisor aunque no exista partner vinculado.
    supplier_documental_name = fields.Char(
        string='Proveedor documental', compute='_compute_review_metrics',
        readonly=True)
    supplier_documental_rut = fields.Char(
        string='RUT documental', compute='_compute_review_metrics', readonly=True)
    supplier_resolution_status = fields.Selection(
        [('resolved_vat', 'Resuelto por RUT'),
         ('resolved_name', 'Resuelto por nombre'),
         ('resolved_manual', 'Resuelto manualmente'),
         ('auto_created', 'Creado automáticamente'),
         ('needs_manual', 'Requiere asignación manual'),
         ('multi_match', 'Múltiples coincidencias')],
        string='Estado de proveedor', compute='_compute_review_metrics',
        readonly=True)

    # Grilla editable de detalle documental (solo Volúmenes). Es un Many2many
    # virtual (compute+inverse) que proxea las líneas del origen real, para que
    # la consola SQL readonly pueda editar el detalle sin tabla intermedia.
    volume_detail_line_ids = fields.Many2many(
        'madenat.lumber.volume.detail.line',
        string='Detalle documental PDF',
        compute='_compute_volume_detail_lines',
        inverse='_inverse_volume_detail_lines',
        store=False,
    )

    # ── Piezas Declaradas: grilla de captura del detalle declarado ────────
    # One2many NO almacenado (compute+inverse) que proxea las MISMAS filas del
    # detalle documental de la Guía origen (`madenat.lumber.volume.detail.line`):
    # no hay tabla intermedia, ni modelo paralelo, ni columnas nuevas en la
    # vista SQL de la consola.
    #
    # Diferencia deliberada con `volume_detail_line_ids` (Many2many del bloque
    # «DETALLE DEL PACKING LIST», oculto en la consola): en un One2many el
    # comando 0 entrega la fila nueva en memoria y el inverse la persiste
    # (mecanismo documentado en `BaseModel.write`), mientras que en un
    # Many2many el comando 0 ejecuta `create()` sin el `guia_id` obligatorio y
    # viola la restricción NOT NULL. El bloque Packing y su Many2many se
    # conservan intactos.
    declared_piece_line_ids = fields.One2many(
        'madenat.lumber.volume.detail.line',
        'guia_id',
        string='Piezas declaradas (detalle documental)',
        compute='_compute_declared_piece_lines',
        inverse='_inverse_declared_piece_lines',
        store=False,
    )

    # Totales informativos de la grilla declarada: SOLO lectura y no
    # almacenados. Nunca sustituyen al volumen oficial ni a la suma del detalle
    # del bloque de auditoría (`volume_detail_m3`, `official_vs_detail_diff_m3`,
    # que siguen retirados de la pantalla operativa de Volumen).
    declared_lines_pieces = fields.Integer(
        string='Total de piezas declaradas',
        compute='_compute_declared_piece_line_totals',
        readonly=True,
        help='Suma de las piezas capturadas en las líneas del detalle '
             'declarado. Es informativo: no gobierna stock ni conciliación.',
    )
    declared_lines_volume_m3 = fields.Float(
        string='Volumen de líneas declaradas (m³)',
        digits=(16, 3),
        compute='_compute_declared_piece_line_totals',
        readonly=True,
        help='Suma de los volúmenes declarados en las líneas del detalle '
             'documental. Es informativo: no reemplaza el volumen oficial.',
    )
    declared_lines_vs_official_m3 = fields.Float(
        string='Diferencia informativa vs volumen oficial (m³)',
        digits=(16, 3),
        compute='_compute_declared_piece_line_totals',
        readonly=True,
        help='Volumen oficial de la guía menos la suma del detalle declarado. '
             'Solo informativo: no bloquea el envío a stock.',
    )

    # ── Volumen operativo editable y conciliación (Volúmenes) ──
    volume_excel_m3 = fields.Float(
        string='Volumen documental Excel (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    volume_detail_m3 = fields.Float(
        string='Suma detalle documental (m³)', compute='_compute_review_metrics',
        readonly=True, digits=(16, 3))
    volume_operational_m3 = fields.Float(
        string='Volumen operativo (m³)',
        compute='_compute_operational_volume', inverse='_inverse_operational_volume',
        digits=(16, 3))
    volume_operational_source = fields.Selection(
        [('pdf', 'PDF'), ('excel', 'Excel'), ('detail', 'Detalle'),
         ('manual', 'Manual')],
        string='Fuente operativa', compute='_compute_review_metrics', readonly=True)
    volume_operational_note = fields.Text(
        string='Motivo del cambio de volumen',
        compute='_compute_operational_note', inverse='_inverse_operational_note')
    conciliation_status = fields.Selection(
        [('not_compared', 'Sin contraste'), ('auto_matched', 'Conciliado'),
         ('matched_with_differences', 'Con diferencias'),
         ('needs_manual_review', 'Requiere revisión'),
         ('incompatible', 'Incompatible'),
         ('manual_confirmed', 'Confirmado manual')],
        string='Conciliación', compute='_compute_review_metrics', readonly=True)
    conciliation_summary = fields.Text(
        string='Resumen de conciliación', compute='_compute_review_metrics',
        readonly=True)
    conciliation_manual_note = fields.Text(
        string='Motivo de confirmación de conciliación',
        compute='_compute_conciliation_note', inverse='_inverse_conciliation_note')

    # ── Cabecera declarada de la Guía (solo Volúmenes) ──
    # Proxies NO almacenados hacia `madenat.guia.processing` (la consola es una
    # vista SQL: no se agregan columnas ni se altera `init()`). La Guía sigue
    # siendo dueña de los valores; la consola solo los opera. Son opcionales,
    # editables y no bloqueantes: no calculan, no concilian, no crean detalle,
    # lotes ni pickings y no disparan ninguna acción de stock.
    declared_widths_text = fields.Char(
        string='Anchos Variables (RW)',
        compute='_compute_declared_volume_header',
        inverse='_inverse_declared_volume_header',
    )
    declared_lengths_text = fields.Char(
        string='Largos Variables (RL)',
        compute='_compute_declared_volume_header',
        inverse='_inverse_declared_volume_header',
    )
    declared_thickness_text = fields.Char(
        string='Espesor Nominal',
        compute='_compute_declared_volume_header',
        inverse='_inverse_declared_volume_header',
    )
    declared_pieces = fields.Integer(
        string='Piezas Declaradas',
        compute='_compute_declared_volume_header',
        inverse='_inverse_declared_volume_header',
    )
    declared_volume_m3 = fields.Float(
        string='M³ Declarado',
        digits=(16, 3),
        compute='_compute_declared_volume_header',
        inverse='_inverse_declared_volume_header',
    )
    # Etiqueta SV única (F3.1): solo lectura y sin inverse. Nunca crea, escribe
    # ni altera el lote; solo lo muestra cuando ya existe.
    declared_sv_lot_id = fields.Many2one(
        'stock.lot',
        string='Etiqueta SV',
        compute='_compute_declared_volume_header',
        readonly=True,
    )

    # ── Sugerencias documentales para la cabecera declarada (solo Volúmenes) ──
    # Campos de SOLO LECTURA, no almacenados y sin inverse: nunca escriben nada
    # por sí mismos. El operador decide si las copia con el botón
    # "Aplicar sugerencias" (y solo rellenan campos vacíos).
    # Nunca consumen, reservan ni predicen la secuencia SV.
    suggested_widths_text = fields.Char(
        string='RW sugerido',
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )
    suggested_lengths_text = fields.Char(
        string='RL sugerido',
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )
    suggested_thickness_text = fields.Char(
        string='Espesor sugerido',
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )
    suggested_pieces = fields.Integer(
        string='Piezas sugeridas',
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )
    suggested_volume_m3 = fields.Float(
        string='M³ sugerido',
        digits=(16, 3),
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )
    suggested_volume_source = fields.Char(
        string='Origen sugerencia M³',
        compute='_compute_declared_volume_suggestions',
        readonly=True,
    )

    # ── Confirmación de retorno de servicio (Procesado, 2026-10-07) ──
    # Proxy NO almacenado hacia `madenat.guia.processing` (la consola es una
    # vista SQL: no se agregan columnas ni se altera `init()`). La Guía es la
    # propietaria del dato; la consola sólo lo opera —y lo puede EDITAR— con el
    # usuario operativo (compute + inverse, store=False). Alcance: ingreso
    # Procesado de servicio (`tipo_recepcion == 'service'`). Sólo identifica la
    # naturaleza del ingreso: no crea lotes/pickings, no valida, no toca stock,
    # costes, OC ni SV.
    service_return_in_scope = fields.Boolean(
        string='En alcance de retorno de servicio',
        compute='_compute_service_return_confirmation',
        readonly=True,
    )
    service_return_confirmation = fields.Selection(
        [('yes', 'Sí, es retorno de servicio'),
         ('no', 'No, no es retorno de servicio')],
        string='¿Es retorno de servicio?',
        compute='_compute_service_return_confirmation',
        inverse='_inverse_service_return_confirmation',
        store=False,
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

    # ── Búsqueda por producto REAL (no por modalidad) ──────────────────────
    # Campo de SOLO búsqueda: filtra los ingresos cuyas LÍNEAS contienen el
    # producto, reutilizando las relaciones existentes
    # `lumber.reception.line.product_id` / `madenat.guia.processing.line.product_id`.
    # NO hace JOIN en la vista SQL (no multiplica filas) y NO elige el primer
    # producto de las líneas. El valor mostrado replica el producto común.
    product_filter_id = fields.Many2one(
        'product.product', string='Producto (contiene)',
        compute='_compute_product_filter_id',
        search='_search_product_filter_id',
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
                (CASE WHEN lr.guia_fecha IS NOT NULL
                      THEN 'emission' ELSE 'reception' END)::text AS guide_date_kind,
                lr.supplier_id AS partner_id,
                lr.purchase_id AS purchase_id,
                lr.purchase_order AS purchase_reference,
                NULLIF(lr.oc_reference_raw, '') AS oc_documental,
                lr.state AS state,
                ('Recepción ' || COALESCE(lr.name, '')) AS display_reference,
                NULL::integer AS processor_id,
                lr.location_id AS location_id,
                COALESCE(loc_lr.is_patio, false) AS is_patio
            FROM lumber_reception lr
            LEFT JOIN stock_location loc_lr ON loc_lr.id = lr.location_id

            UNION ALL

            SELECT
                ({CONSOLE_ID_OFFSET} + gp.id)::integer AS id,
                'madenat.guia.processing'::text AS source_model,
                gp.id::integer AS source_res_id,
                (CASE WHEN gp.tipo_recepcion = 'granel'
                      THEN 'volume' ELSE 'processed' END)::text AS ingestion_type,
                gp.name AS guide_name,
                gp.date_emission AS guide_date,
                'emission'::text AS guide_date_kind,
                gp.partner_id AS partner_id,
                gp.order_id AS purchase_id,
                COALESCE(po.name, gp.oc_reference_raw, '') AS purchase_reference,
                NULLIF(gp.oc_reference_raw, '') AS oc_documental,
                (CASE WHEN gp.state = 'cancelled' THEN 'cancel' ELSE gp.state END) AS state,
                ('Procesada ' || COALESCE(gp.name, '')) AS display_reference,
                tpo.processor_id AS processor_id,
                gp.assignment_location_id AS location_id,
                COALESCE(loc_gp.is_patio, false) AS is_patio
            FROM madenat_guia_processing gp
            LEFT JOIN purchase_order po ON po.id = gp.order_id
            LEFT JOIN toll_processing_order tpo ON tpo.id = gp.toll_order_id
            LEFT JOIN stock_location loc_gp ON loc_gp.id = gp.assignment_location_id
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
            # Estado visual: una guía Procesado con líneas pero TODAS
            # documentales pendientes (sin una sola línea operativa elegible)
            # NO debe mostrarse "Listo para stock". El botón queda oculto por
            # su condición `review_state not in ('ready',)`; action_validate
            # (Core) sigue siendo la defensa real.
            if rec.ingestion_type == 'processed' and rec.review_state == 'ready':
                src = rec._get_source_record()
                if src is not None:
                    doc = src._documentary_pending_lines()
                    if doc and not (src.processing_line_ids - doc):
                        rec.review_state = 'documental_pending'

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
    # AUD-ETQ-08 (2026-10-12): dependencia CORREGIDA. La versión anterior
    # dependía de `volume_detail_line_ids.volume_m3`, donde
    # `volume_detail_line_ids` es un proxy Many2many VIRTUAL (compute+inverse,
    # store=False) NO buscable. Odoo no puede determinar qué filas de la
    # consola recalcular cuando se modifica `madenat.lumber.volume.detail.line`
    # y advertía el aviso «should be searchable» para CADA campo calculado por
    # este método. La consola es una vista SQL de SOLO LECTURA (`_auto=False`)
    # cuyos campos no se almacenan y se recomputan por lectura; los datos reales
    # viven en el registro origen y su detalle documental (relación real
    # `madenat.lumber.volume.detail.line.guia_id`). Por eso la dependencia
    # canónica —idéntica a la del resto de los computes de esta consola, incluido
    # `_compute_declared_piece_line_totals`, que también lee `src.volume_detail_m3`
    # y no advierte— son los campos de IDENTIDAD del origen. No se implementa un
    # `search` ficticio, no se elimina semántica y no se usa recomputación global.
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_review_metrics(self):
        for rec in self:
            src = rec._get_source_record()
            # Volumen documental (solo Ingreso por Volúmenes).
            rec.volumen_pdf_m3 = 0.0
            rec.volumen_suma_detalle = 0.0
            rec.volumen_stock_m3 = 0.0
            rec.volumen_diff_m3 = 0.0
            rec.volumen_fuente = ''
            rec.volume_excel_m3 = 0.0
            rec.official_volume_m3 = 0.0
            rec.official_volume_source = False
            rec.official_vs_detail_diff_m3 = 0.0
            rec.volume_detail_m3 = 0.0
            rec.volume_operational_source = ''
            rec.conciliation_status = 'not_compared'
            rec.conciliation_summary = ''
            # Proveedor documental (emisor del PDF).
            rec.supplier_documental_name = ''
            rec.supplier_documental_rut = ''
            rec.supplier_resolution_status = 'needs_manual'
            # Evidencia documental Procesado (proxies read-only). Valores
            # neutros por defecto; solo la rama 'processed' los rellena.
            rec.vol_comercial_pdf = 0.0
            rec.packing_volume_declared_m3 = 0.0
            rec.sum_vol_documental_m3 = 0.0
            rec.diff_pdf_packing_m3 = 0.0
            rec.diff_packing_lineas_m3 = 0.0
            rec.documental_conciliation_state = 'not_available'
            rec.packing_pieces_declared = 0
            rec.packing_package_count_declared = 0
            rec.vol_compra_m3 = 0.0
            rec.vol_embarque_m3 = 0.0
            if src is None:
                rec.total_volume_m3 = 0.0
                rec.total_packages = 0
                rec.total_lots = 0
                rec.total_amount = 0.0
                rec.currency_id = False
                rec.review_guide_document = ''
                rec.review_excel_document = ''
                continue

            # Proveedor documental (emisor del PDF) y estado de resolución,
            # disponible para guías (Volúmenes/Procesado).
            rec.supplier_documental_name = getattr(src, 'supplier_name', '') or ''
            rec.supplier_documental_rut = getattr(src, 'supplier_rut', '') or ''
            rec.supplier_resolution_status = (
                getattr(src, 'supplier_resolution_status', 'needs_manual')
                or 'needs_manual')

            if rec.ingestion_type == 'product':
                rec.total_volume_m3 = src.total_volume_m3 or 0.0
                rec.total_packages = src.total_packages or 0
                rec.total_lots = len(src.reception_line_ids)
                rec.total_amount = src.total_amount_clp or 0.0
                rec.currency_id = src.currency_id
                rec.review_guide_document = src.pdf_filename or 'Sin PDF'
                rec.review_excel_document = src.excel_filename or 'Sin Excel'
            elif rec.ingestion_type == 'volume':
                rec.total_volume_m3 = src.vol_total_m3 or 0.0
                rec.total_packages = src.total_paquetes or 0
                rec.total_lots = src.total_lotes_unicos or 0
                # Sin monto comercial: Volúmenes no participa del cálculo
                # monetario de Producto/Procesado.
                rec.total_amount = 0.0
                rec.currency_id = src.currency_id
                rec.review_guide_document = src.guide_pdf_filename or 'Sin PDF'
                rec.review_excel_document = (
                    src.excel_filename or 'Sin Excel'
                    if (src.excel_file or src.excel_filename) else 'Sin Excel')
                # Evidencia documental original (PDF/Excel/detalle). El detalle
                # es SOLO control documental: nunca volumen oficial.
                rec.volumen_pdf_m3 = src.volume_pdf_m3 or 0.0
                rec.volume_excel_m3 = src.volume_excel_m3 or 0.0
                rec.volume_detail_m3 = src.volume_detail_m3 or 0.0
                rec.volumen_suma_detalle = rec.volume_detail_m3
                # Volumen OFICIAL único: se lee de la API canónica de la guía
                # (la precedencia vive en el modelo de la guía, no aquí).
                rec.official_volume_m3 = src.official_volume_m3 or 0.0
                rec.official_volume_source = src.official_volume_source or False
                rec.official_vs_detail_diff_m3 = (
                    src.official_vs_detail_diff_m3 or 0.0)
                # Volumen operativo (el único usado para stock) y su fuente.
                rec.volume_operational_source = src.volume_operational_source or ''
                rec.conciliation_status = src.conciliation_status or 'not_compared'
                rec.conciliation_summary = src.conciliation_summary or ''
                rec.volumen_stock_m3 = src.volume_operational_m3 or 0.0
                rec.volumen_diff_m3 = round(
                    (rec.volumen_pdf_m3 or 0.0)
                    - (rec.volumen_stock_m3 or 0.0), 3)
                rec.volumen_fuente = {
                    'pdf': 'PDF', 'excel': 'Excel', 'detail': 'Detalle',
                    'manual': 'Manual',
                }.get(src.volume_operational_source or '', '')
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
                # Proyección documental read-only desde la guía origen.
                rec.vol_comercial_pdf = src.vol_comercial_pdf or 0.0
                rec.packing_volume_declared_m3 = src.packing_volume_declared_m3 or 0.0
                rec.sum_vol_documental_m3 = src.sum_vol_documental_m3 or 0.0
                rec.diff_pdf_packing_m3 = src.diff_pdf_packing_m3 or 0.0
                rec.diff_packing_lineas_m3 = src.diff_packing_lineas_m3 or 0.0
                rec.documental_conciliation_state = (
                    src.documental_conciliation_state or 'not_available')
                rec.packing_pieces_declared = src.packing_pieces_declared or 0
                rec.packing_package_count_declared = src.packing_package_count_declared or 0
                # P1 (Q1/R07): magnitudes de compra (real) y de embarque
                # (nominal comercial), proyectadas desde las líneas reales.
                rec.vol_compra_m3 = sum(
                    src.processing_line_ids.mapped('vol_purchase_m3'))
                rec.vol_embarque_m3 = sum(
                    src.processing_line_ids.mapped('vol_shipment_m3'))

    # ------------------------------------------------------------------
    # Volumen oficial vigente (Fase 2 — solo Volúmenes, sin side effects)
    # ------------------------------------------------------------------
    @api.depends('official_volume_m3', 'official_volume_source',
                 'sv_regularization_applied', 'sv_regularized_baseline_m3')
    def _compute_official_volume_effective(self):
        """Volumen oficial vigente de la pantalla operativa de Volúmenes.

        - Con regularización aplicada en la etiqueta SV real, el lote declara
          un baseline regularizado distinto del volumen documental original
          (`stock.lot.sv_regularized_baseline_m3` gobernado por la última
          operación `regularize_volume` aplicada): rige ese baseline y la
          fuente es "Regularización Operaciones".
        - Sin regularización aplicada rige el volumen oficial documental de la
          Guía (`get_official_volume_m3()` proyectado en `official_volume_m3`),
          con su fuente ("Guía PDF" / "Packing Excel" / "Packing declarado").
        - Sin lote SV y sin fuente documental: 0,000 y sin fuente.

        Lectura pura: no escribe `stock.lot`, la Guía, el ledger SV, stock,
        pickings ni secuencia, y nunca modifica `official_volume_m3`.
        """
        for rec in self:
            if rec.sv_regularization_applied:
                rec.official_volume_effective_m3 = (
                    rec.sv_regularized_baseline_m3 or 0.0)
                rec.official_volume_effective_source = (
                    'Regularización Operaciones')
            else:
                rec.official_volume_effective_m3 = (
                    rec.official_volume_m3 or 0.0)
                rec.official_volume_effective_source = (
                    rec.official_volume_source or False)

    # ------------------------------------------------------------------
    # Líneas documentales pendientes (Procesado, read-only)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_documental_pending_count(self):
        for rec in self:
            count = 0
            if rec.ingestion_type == 'processed':
                src = rec._get_source_record()
                if src is not None:
                    count = len(src._documentary_pending_lines())
            rec.documental_pending_count = count

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
    # Grilla editable de detalle documental (solo Volúmenes)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_volume_detail_lines(self):
        """Proxea las líneas de detalle documental del origen real."""
        Line = self.env['madenat.lumber.volume.detail.line']
        for rec in self:
            src = rec._get_source_record()
            if src is not None and rec.ingestion_type == 'volume':
                rec.volume_detail_line_ids = src.volume_detail_line_ids
            else:
                rec.volume_detail_line_ids = Line.browse()

    def _inverse_volume_detail_lines(self):
        """Sincroniza la grilla editable con el origen real.

        - Las filas nuevas se asocian a la guía (guia_id).
        - Las filas eliminadas se desvinculan/borran.
        Nunca recalcula geometría ni toca el volumen PDF.
        """
        Line = self.env['madenat.lumber.volume.detail.line']
        for rec in self:
            src = rec._get_source_record()
            if not src or rec.ingestion_type != 'volume':
                continue
            current = src.volume_detail_line_ids
            selected = rec.volume_detail_line_ids
            # Borrar las líneas quitadas de la grilla.
            (current - selected).unlink()
            # Asociar las líneas nuevas a la guía.
            for line in selected:
                if line.guia_id.id != src.id:
                    line.write({'guia_id': src.id})

    # ------------------------------------------------------------------
    # Piezas declaradas: grilla one2many del detalle documental (Volúmenes)
    # ------------------------------------------------------------------
    # Campos del detalle capturables desde la grilla declarada. La trazabilidad
    # documental (`source_page`, `source_line_no`, `confidence`) y el flag
    # `manually_adjusted` NO se escriben desde la consola.
    DECLARED_PIECE_GRID_FIELDS = (
        'lot_or_package',
        'material_code',
        'description',
        'pieces',
        'width_declared',
        'length_declared',
        'thickness_declared',
        'volume_m3',
        'uom',
        'unit_price',
        'line_amount',
        'observation',
    )

    # Orígenes que la grilla declarada de la Consola PROYECTA y administra.
    # Regla canónica (fuente única para vista, inverse y contadores):
    #   - 'header': fila de cabecera declarada (a lo sumo UNA por Guía), creada
    #     y mantenida por «Aplicar datos documentales».
    #   - 'manual': filas capturadas por el operador desde la consola.
    # Las filas documentales ('pdf'/'excel') NO se proyectan en esta grilla:
    # siguen existiendo intactas en `volume_detail_line_ids` y visibles en la
    # pestaña Packing de la fachada de la Guía. La consola NUNCA las crea,
    # escribe, re-vincula ni elimina.
    DECLARED_PIECE_GRID_ORIGINS = (HEADER_DECLARED_ORIGIN, 'manual')

    def _declared_piece_grid_lines(self, src):
        """Filas del detalle documental que la grilla declarada proyecta.

        Regla única compartida por la vista (compute), el inverse y los
        contadores: solo las filas cuyo `origin` está en
        `DECLARED_PIECE_GRID_ORIGINS` ('header' y 'manual'). Las filas
        documentales del PDF/Excel quedan fuera del alcance de la consola.

        Es un filtrado de LECTURA: nunca escribe, vincula ni elimina nada.
        """
        return src.volume_detail_line_ids.filtered(
            lambda line: line.origin in self.DECLARED_PIECE_GRID_ORIGINS)

    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_declared_piece_lines(self):
        """Proxea las filas DECLARADAS de la grilla (solo Volúmenes).

        La grilla muestra únicamente las filas con `origin` 'header' (cabecera
        declarada) o 'manual' (captura del operador). Las filas documentales
        del PDF/Excel (`origin` 'pdf'/'excel') NO se proyectan aquí: siguen
        existiendo intactas y se administran en la pestaña Packing de la
        fachada. Por eso una Guía recién ingestada muestra la grilla VACÍA con
        su estado vacío, y «Aplicar datos documentales» agrega solo la fila de
        cabecera.

        Lectura pura: no crea, escribe, valida ni elimina nada. Fuera de una
        Guía de Volumen (o si el origen ya no existe) la grilla queda vacía y
        la UI de Producto/Procesado permanece inalterada.
        """
        Line = self.env['madenat.lumber.volume.detail.line']
        for rec in self:
            src = rec._get_source_record()
            if src is not None and rec.ingestion_type == 'volume':
                rec.declared_piece_line_ids = rec._declared_piece_grid_lines(src)
            else:
                rec.declared_piece_line_ids = Line.browse()

    def _inverse_declared_piece_lines(self):
        """Sincroniza la grilla declarada con el detalle real de la Guía.

        Guardas y alcance:
        - Solo opera sobre una Guía de Volumen real (`source_model`,
          `source_res_id`, `ingestion_type`), igual que el resto de los
          proxies de la consola.
        - Estados terminales (`validated`, `cancelled`): la guía ya no admite
          correcciones (misma regla que usa la consola para Producto/
          Procesado); se informa y no se escribe nada.
        - Las filas NUEVAS que el ORM entrega en memoria durante el inverse se
          crean en el detalle real con `guia_id` y `origin='manual'`: son
          captura del operador, no evidencia PDF/Excel.
        - Solo se eliminan las filas que la grilla EFECTIVAMENTE proyecta
          ('header'/'manual') y que el operador quitó de ella: el alcance del
          borrado es `_declared_piece_grid_lines(src)`, de modo que las filas
          documentales del PDF/Excel ('pdf'/'excel') quedan FUERA del conjunto
          y NUNCA se borran, escriben ni re-vinculan desde la consola. Esas
          filas siguen visibles e intactas en la pestaña Packing de la fachada.
        - Las filas editadas ya fueron escritas por el ORM sobre la línea real.
        - Nunca toca estado, tipo de recepción, proveedor/OC/precios, volumen
          oficial, volumen operativo, conciliación, lotes, stock, pickings,
          chatter ni bitácora. Nunca recalcula volúmenes.
        """
        Line = self.env['madenat.lumber.volume.detail.line']
        for rec in self:
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'volume'):
                continue
            src = rec._get_source_record()
            if not src:
                continue
            if src.state in ('validated', 'cancelled'):
                raise UserError(_(
                    'No se puede modificar el detalle declarado de una guía '
                    'ya validada o cancelada.'))

            persisted_ids = []
            new_rows = []
            for row in rec.declared_piece_line_ids:
                origin = row._origin
                if origin:
                    persisted_ids.append(origin.id)
                else:
                    new_rows.append(row)

            created = Line.browse()
            for row in new_rows:
                vals = {'guia_id': src.id, 'origin': 'manual'}
                for fname in self.DECLARED_PIECE_GRID_FIELDS:
                    vals[fname] = row[fname]
                created |= Line.create(vals)

            # Alcance del borrado: SOLO las filas que la grilla proyecta
            # ('header'/'manual') y que el operador quitó. Las recién creadas y
            # las persistidas que siguen en la grilla se conservan. Las filas
            # documentales del PDF/Excel ('pdf'/'excel') nunca entran en este
            # conjunto: la consola no puede eliminarlas (siguen visibles e
            # intactas en la pestaña Packing de la fachada y alimentan
            # `volume_detail_m3`, la conciliación y la consolidación).
            visible = rec._declared_piece_grid_lines(src)
            kept = Line.browse(persisted_ids) | created
            (visible - kept).unlink()

            # Tras guardar, la consola debe quedar apuntando a las filas YA
            # persistidas: el ORM entrega las nuevas como registros sin guardar
            # y una lectura en la misma transacción (p. ej. `web_save`) las
            # descartaría. Se invalidan los valores en caché del registro (no
            # hay escritura a base de datos: la consola no almacena campos) para
            # que la grilla y los totales se recalculen desde el detalle real de
            # la Guía en la siguiente lectura.
            rec.invalidate_recordset()

    @api.depends('source_model', 'source_res_id', 'ingestion_type',
                 'official_volume_effective_m3')
    def _compute_declared_piece_line_totals(self):
        """Totales informativos del bloque declarado (solo Volúmenes).

        Definición explícita de contadores (sin ambigüedad de alcance):

        - `declared_lines_pieces`: SUMA de `pieces` de las filas VISIBLES de la
          grilla, es decir las que proyecta `_declared_piece_grid_lines(src)`
          (`origin` 'header' o 'manual', ver `DECLARED_PIECE_GRID_ORIGINS`).
          Las piezas de las filas documentales del PDF/Excel NO se cuentan
          aquí: esas filas no forman parte de la grilla declarada.
        - `declared_lines_volume_m3`: agregado canónico del DETALLE DOCUMENTAL
          DEL PDF/EXCEL (`volume_detail_m3`), NO de la grilla; la fila de
          cabecera está excluida del agregado (anti doble conteo en
          `HEADER_DECLARED_ORIGIN`).
        - `declared_lines_vs_official_m3`: diferencia del mismo detalle
          documental contra el volumen oficial vigente
          (`official_vs_detail_diff_m3`); puramente informativa.

        Reutiliza los agregados canónicos de la Guía, no recalcula geometría, no
        concilia y no toca stock: la diferencia contra el volumen oficial es
        solo informativa y nunca bloquea «Enviar a Stock».
        """
        for rec in self:
            rec.declared_lines_pieces = 0
            rec.declared_lines_volume_m3 = 0.0
            rec.declared_lines_vs_official_m3 = 0.0
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'volume'):
                continue
            src = rec._get_source_record()
            if not src:
                continue
            rec.declared_lines_pieces = sum(
                (line.pieces or 0)
                for line in rec._declared_piece_grid_lines(src))
            rec.declared_lines_volume_m3 = src.volume_detail_m3 or 0.0
            rec.declared_lines_vs_official_m3 = (
                src.official_vs_detail_diff_m3 or 0.0)

    # ------------------------------------------------------------------
    # Volumen operativo editable y conciliación (proyección hacia origen)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_operational_volume(self):
        for rec in self:
            src = rec._get_source_record()
            rec.volume_operational_m3 = (
                getattr(src, 'volume_operational_m3', 0.0) or 0.0
                if src is not None and rec.ingestion_type == 'volume' else 0.0)

    def _inverse_operational_volume(self):
        """Escribe el volumen operativo en la guía origen (nunca la vista SQL)."""
        for rec in self:
            src = rec._get_source_record()
            if not src or rec.ingestion_type != 'volume':
                continue
            src.set_volume_operational(
                rec.volume_operational_m3, 'manual',
                rec.volume_operational_note or None)

    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_operational_note(self):
        for rec in self:
            src = rec._get_source_record()
            rec.volume_operational_note = (
                getattr(src, 'volume_operational_note', '') or ''
                if src is not None and rec.ingestion_type == 'volume' else '')

    def _inverse_operational_note(self):
        for rec in self:
            src = rec._get_source_record()
            if not src or rec.ingestion_type != 'volume':
                continue
            src.write({'volume_operational_note': rec.volume_operational_note or False})

    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_conciliation_note(self):
        for rec in self:
            src = rec._get_source_record()
            rec.conciliation_manual_note = (
                getattr(src, 'conciliation_manual_note', '') or ''
                if src is not None and rec.ingestion_type == 'volume' else '')

    def _inverse_conciliation_note(self):
        for rec in self:
            src = rec._get_source_record()
            if not src or rec.ingestion_type != 'volume':
                continue
            src.write({'conciliation_manual_note': rec.conciliation_manual_note or False})

    # ------------------------------------------------------------------
    # Cabecera declarada de la Guía (solo Volúmenes — AD-78)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_declared_volume_header(self):
        """Proxea la cabecera declarada desde la Guía origen (solo Volúmenes).

        Lectura pura: no crea, escribe, valida, concilia ni toca stock. En
        cualquier registro que no sea una Guía de volumen (o si la guía origen
        ya no existe) los seis proxies quedan vacíos, de modo que la UI de
        Producto/Procesado permanece inalterada.
        """
        for rec in self:
            rec.declared_widths_text = False
            rec.declared_lengths_text = False
            rec.declared_thickness_text = False
            rec.declared_pieces = 0
            rec.declared_volume_m3 = 0.0
            rec.declared_sv_lot_id = False
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'volume'):
                continue
            src = rec._get_source_record()
            if not src:
                continue
            rec.declared_widths_text = src.anchos_variables or False
            rec.declared_lengths_text = src.largos_variables or False
            rec.declared_thickness_text = src.espesor_nominal_texto or False
            rec.declared_pieces = src.piezas_declaradas or 0
            rec.declared_volume_m3 = src.volumen_declarado_m3 or 0.0
            rec.declared_sv_lot_id = src.volume_lot_id

    def _inverse_declared_volume_header(self):
        """Escribe los cinco datos declarados en la Guía origen (solo Volumen).

        Guardas duras:
        - Solo escribe si el origen es una Guía real con `ingestion_type ==
          'volume'`; en cualquier otro caso no hace nada (nunca lanza error ni
          toca un origen no-volume).
        - Escribe EXCLUSIVAMENTE los cinco campos declarados. No toca estado,
          tipo de recepción, proveedor/OC/precios, detalle, volumen operativo,
          conciliación, lotes, stock, pickings ni bitácora.
        - Los valores vacíos son válidos (campos opcionales, no bloqueantes).
        """
        for rec in self:
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'volume'):
                continue
            src = rec._get_source_record()
            if not src:
                continue
            src.write({
                'anchos_variables': rec.declared_widths_text or False,
                'largos_variables': rec.declared_lengths_text or False,
                'espesor_nominal_texto': rec.declared_thickness_text or False,
                'piezas_declaradas': rec.declared_pieces or 0,
                'volumen_declarado_m3': rec.declared_volume_m3 or 0.0,
            })

    # ------------------------------------------------------------------
    # Sugerencias de la cabecera declarada (solo Volúmenes — AD-78)
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_declared_volume_suggestions(self):
        """Sugerencias documentales/comerciales para Volumen (solo lectura).

        - RW / RL: designaciones comerciales (Random Widths / Random Lengths).
          Nunca derivan medidas numéricas ni leen geometría del detalle.
        - Espesor: SIN sugerencia (no se infiere ni se fabrica).
        - Piezas: `packing_pieces_declared` > 0; si no, suma de piezas positivas
          de `processing_line_ids` SOLO cuando `detalle_aplicado ==
          'line_by_line'` (la línea sintética consolidada GRANEL trae pieces=1
          y nunca se usa como sugerencia).
        - M³: `volume_pdf_m3` → `volume_excel_m3` → `packing_volume_declared_m3`
          → `volume_detail_m3`. Nunca usa el volumen operativo, el comercial
          calculado, el físico, valores de conciliación ni stock.

        Lectura pura: no escribe, no crea/borra registros, no valida, no toca
        lotes, stock, pickings, bitácora ni secuencia.
        """
        for rec in self:
            rec.suggested_widths_text = False
            rec.suggested_lengths_text = False
            rec.suggested_thickness_text = False
            rec.suggested_pieces = 0
            rec.suggested_volume_m3 = 0.0
            rec.suggested_volume_source = False
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'volume'):
                continue
            src = rec._get_source_record()
            if not src:
                continue

            rec.suggested_widths_text = 'RW'
            rec.suggested_lengths_text = 'RL'
            # Espesor: sin sugerencia por diseño (nunca se infiere).

            pieces = src.packing_pieces_declared or 0
            if pieces <= 0 and src.detalle_aplicado == 'line_by_line':
                eligible = src.processing_line_ids.filtered(
                    lambda l: (l.pieces or 0) > 0)
                if eligible:
                    pieces = sum(eligible.mapped('pieces'))
            rec.suggested_pieces = pieces if pieces > 0 else 0

            if (src.volume_pdf_m3 or 0.0) > 0:
                rec.suggested_volume_m3 = float(src.volume_pdf_m3)
                rec.suggested_volume_source = 'Guía PDF'
            elif (src.volume_excel_m3 or 0.0) > 0:
                rec.suggested_volume_m3 = float(src.volume_excel_m3)
                rec.suggested_volume_source = 'Packing Excel'
            elif (src.packing_volume_declared_m3 or 0.0) > 0:
                rec.suggested_volume_m3 = float(src.packing_volume_declared_m3)
                rec.suggested_volume_source = 'Total declarado Packing'
            elif (src.volume_detail_m3 or 0.0) > 0:
                rec.suggested_volume_m3 = float(src.volume_detail_m3)
                rec.suggested_volume_source = 'Suma detalle documental'

    def action_apply_declared_volume_suggestions(self):
        """Copia las sugerencias a la Guía origen y sincroniza la fila declarada.

        Comportamiento de cabecera (SIN CAMBIOS):
        - Opera únicamente sobre una Guía de Volumen real (misma guarda que los
          proxies: `source_model`, `source_res_id`, `ingestion_type`).
        - Nunca sobrescribe un valor declarado por el operador.
        - Escribe EXCLUSIVAMENTE los cinco campos declarados de la Guía.
        - No toca estado, proveedor/OC/precios, volumen operativo,
          conciliación, lotes, stock, pickings, bitácora ni secuencia.

        Comportamiento agregado: tras aplicar los datos documentales, los
        valores VIGENTES de la cabecera declarada (piezas, RW, RL y espesor
        nominal) se reflejan como UNA sola fila de la grilla «Piezas
        Declaradas» (`origin='header'`), actualizándola si ya existe. Ver
        `_sync_declared_header_line()`.
        """
        self.ensure_one()
        reload_action = {'type': 'ir.actions.client', 'tag': 'reload'}
        if (self.source_model != 'madenat.guia.processing'
                or not self.source_res_id
                or self.ingestion_type != 'volume'):
            return reload_action
        source = self._get_source_record()
        if not source:
            return reload_action

        values = {}
        if not source.anchos_variables:
            values['anchos_variables'] = self.suggested_widths_text
        if not source.largos_variables:
            values['largos_variables'] = self.suggested_lengths_text
        if not source.espesor_nominal_texto and self.suggested_thickness_text:
            values['espesor_nominal_texto'] = self.suggested_thickness_text
        if not source.piezas_declaradas and self.suggested_pieces > 0:
            values['piezas_declaradas'] = self.suggested_pieces
        if not source.volumen_declarado_m3 and self.suggested_volume_m3 > 0:
            values['volumen_declarado_m3'] = self.suggested_volume_m3

        if values:
            source.write(values)

        # La cabecera pudo cambiar: recalcular los proxies no almacenados antes
        # de reflejarlos en la grilla (volumen oficial vigente incluido).
        self.invalidate_recordset()
        # Reflejo de la cabecera declarada en la grilla (una sola fila).
        self._sync_declared_header_line(source)
        # La cabecera y la grilla cambiaron: la consola debe recalcular sus
        # proxies y totales en la misma transacción.
        self.invalidate_recordset()
        return reload_action

    def _sync_declared_header_line(self, source):
        """Sincroniza la fila única de cabecera declarada en la grilla.

        Devuelve el número de filas creadas/actualizadas (0 o 1).

        Reglas:
        - Marca inequívoca de idempotencia: `origin = HEADER_ORIGIN`
          («Cabecera declarada»). Como máximo existe UNA fila así por guía, por
          lo que pulsar el botón varias veces nunca duplica: la fila existente
          se ACTUALIZA en su lugar (también si cambia el volumen oficial).
        - `origin='manual'` NO se usa: esa fila no es una captura manual de un
          ítem documental, sino el reflejo de la cabecera declarada de la guía.
        - La fila lleva las piezas/RW/RL/espesor declarados y el VOLUMEN
          OFICIAL VIGENTE (`official_volume_effective_m3`) en `volume_m3`. Ese
          volumen NO se suma a los agregados del detalle documental (regla anti
          doble conteo en `HEADER_DECLARED_ORIGIN`), de modo que conciliación,
          diferencia documental y consolidación quedan intactas.
        - Sin datos declarados (piezas 0 y RW/RL/espesor vacíos o sólo la
          designación genérica «RW»/«RL») no se crea nada; tampoco se elimina
          una fila preexistente (no destructivo).
        - Una fila con `manually_adjusted=True` (corrección del operador) nunca
          se sobrescribe.
        - Estados terminales (`validated`, `cancelled`): no crea ni actualiza.
        - Solo escribe esa fila: no toca las líneas del PDF/Excel, la cabecera,
          el volumen oficial, la conciliación, lotes, stock ni el chatter.
        """
        Line = self.env['madenat.lumber.volume.detail.line']
        if source.state in ('validated', 'cancelled'):
            return 0
        pieces = source.piezas_declaradas or 0
        width = (source.anchos_variables or '').strip()
        length = (source.largos_variables or '').strip()
        thickness = (source.espesor_nominal_texto or '').strip()
        # Volumen oficial VIGENTE de la guía (con regularización SV si aplica):
        # es el volumen que gobierna stock, conciliación y consolidación.
        volume = self.official_volume_effective_m3 or 0.0
        # Designaciones genéricas que el propio botón sugiere («RW» / «RL»): son
        # el marcador comercial de «anchos/largos variables», NO un dato
        # declarado. Por sí solas no representan información y no crean fila.
        generic_designations = {
            (self.suggested_widths_text or '').strip().lower(),
            (self.suggested_lengths_text or '').strip().lower(),
        } - {''}
        width_is_data = bool(width) and width.lower() not in generic_designations
        length_is_data = (
            bool(length) and length.lower() not in generic_designations)
        if not pieces and not width_is_data and not length_is_data \
                and not thickness:
            # Cabecera sin datos declarados: no hay fila que representar (y no
            # se borra una fila preexistente: eliminar es decisión del
            # operador).
            return 0

        declared_lines = source.volume_detail_line_ids.filtered(
            lambda line: line.origin == Line.HEADER_ORIGIN)
        if len(declared_lines) > 1:
            # Anomalía (no puede ocurrir desde la UI): no se crea ni se
            # reemplaza nada para no destruir información.
            return 0
        vals = {
            'pieces': pieces,
            'width_declared': width,
            'length_declared': length,
            'thickness_declared': thickness,
            'volume_m3': volume,
        }
        if not declared_lines:
            # Descripción por defecto SOLO al crear (primera pulsación): da al
            # operador un texto claro de qué representa la fila. Las
            # actualizaciones posteriores no incluyen `description` ni
            # `observation`, así que nunca pisan una edición del operador; la
            # observación nace vacía.
            Line.create(dict(
                vals,
                guia_id=source.id,
                origin=Line.HEADER_ORIGIN,
                description=HEADER_DECLARED_DESCRIPTION,
            ))
            return 1
        if declared_lines.manually_adjusted:
            # La corrección del operador manda sobre el reflejo de cabecera.
            return 0
        if (declared_lines.pieces or 0) != pieces \
                or (declared_lines.width_declared or '') != width \
                or (declared_lines.length_declared or '') != length \
                or (declared_lines.thickness_declared or '') != thickness \
                or (declared_lines.volume_m3 or 0.0) != volume:
            declared_lines.with_context(**{
                Line.DOCUMENTAL_PIECES_CONTEXT: True,
            }).write(vals)
            return 1
        return 0

    def action_add_declared_piece_line(self):
        """Abre el diálogo «Agregar ítem a piezas declaradas».

        Punto de entrada explícito para crear una fila MANUAL del detalle
        declarado con Descripción y Observación en primer plano.

        Comportamiento:
        - Solo aplica a una Guía de Volumen real (misma guarda que los proxies):
          `source_model`, `source_res_id`, `ingestion_type == 'volume'`.
        - Estados terminales (`validated`/`cancelled`): UserError (misma regla
          vigente del inverse de la grilla). El botón además queda invisible.
        - Devuelve un `ir.actions.act_window` `target='new'` con el formulario
          curado del modelo de línea, preseleccionando la guía y
          `origin='manual'`, y propaga el contexto interno
          `DECLARED_MANUAL_ENTRY_CONTEXT`, que en el `create` de la línea fuerza
          `origin='manual'` y valida guía de Volumen no terminal.
        - La guía viaja en la clave de contexto PROPIA
          `DECLARED_GUIA_ID_CONTEXT` (NO en `default_guia_id`): el formulario no
          expone `guia_id` y el `create` la lee cuando falta. Se evita así el
          `guia_id` "nuevo" que disparaba el KeyError del onchange (el One2many
          `declared_piece_line_ids` figura como inverso global de `guia_id`).
        - No escribe nada por sí mismo: la fila la crea el formulario al
          guardarse. No toca stock, lotes, conciliación, costeo ni chatter.
        """
        self.ensure_one()
        if (self.source_model != 'madenat.guia.processing'
                or not self.source_res_id
                or self.ingestion_type != 'volume'):
            raise UserError(_(
                'El detalle declarado solo aplica a guías de Ingreso por '
                'Volúmenes.'))
        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        if src.state in ('validated', 'cancelled'):
            raise UserError(_(
                'No se puede modificar el detalle declarado de una guía ya '
                'validada o cancelada.'))
        form_view = self.env.ref(
            'madenat_lumber_intake'
            '.view_madenat_lumber_volume_detail_line_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Agregar ítem a piezas declaradas'),
            'res_model': 'madenat.lumber.volume.detail.line',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'new',
            'context': {
                DECLARED_GUIA_ID_CONTEXT: src.id,
                'default_origin': 'manual',
                DECLARED_MANUAL_ENTRY_CONTEXT: True,
            },
        }

    def action_confirm_conciliation(self):
        """Confirma manualmente una conciliación pendiente/incompatible."""
        self.ensure_one()
        if self.ingestion_type != 'volume':
            raise UserError(
                _('La confirmación de conciliación solo aplica a Volúmenes.'))
        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        src.action_confirm_conciliation(self.conciliation_manual_note or None)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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

    # ------------------------------------------------------------------
    # Confirmación de retorno de servicio (Procesado, 2026-10-07)
    # Proxy de lectura/escritura hacia la Guía origen. Editable por el usuario
    # operativo (inverse delega en `src.write`). No bloquea la ingesta ni el
    # envío a stock; el vacío es válido (= pendiente, NO equivale a No).
    # ------------------------------------------------------------------
    @api.depends('source_model', 'source_res_id', 'ingestion_type')
    def _compute_service_return_confirmation(self):
        """Lee la confirmación desde el origen real (solo Procesado servicio).

        Lectura pura: no escribe, no valida, no toca stock. En cualquier fila
        que no sea una Guía Procesada de servicio (Producto, Volumen, guía de
        ``compra`` o ``granel``) el proxy queda vacío y
        ``service_return_in_scope`` en False: la UI de los otros flujos no
        cambia.
        """
        for rec in self:
            rec.service_return_in_scope = False
            rec.service_return_confirmation = False
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'processed'):
                continue
            src = rec._get_source_record()
            if not src or src.tipo_recepcion != 'service':
                continue
            rec.service_return_in_scope = True
            rec.service_return_confirmation = (
                src.service_return_confirmation or False)

    def _inverse_service_return_confirmation(self):
        """Escribe la confirmación en la Guía origen (solo Procesado servicio).

        Guardas duras: solo escribe si el origen es una Guía real de servicio
        (``madenat.guia.processing`` + ``tipo_recepcion == 'service'``). No toca
        estado, tipo de recepción, stock, lotes, pickings, OC, costes ni SV. El
        vacío es válido (pendiente). La regla de cambio Sí→No con imputaciones
        aplicadas reside en `madenat_lumber_logistics` (donde el modelo SV existe)
        y se aplica al delegar en ``src.write``.
        """
        for rec in self:
            if (rec.source_model != 'madenat.guia.processing'
                    or not rec.source_res_id
                    or rec.ingestion_type != 'processed'):
                continue
            src = rec._get_source_record()
            if not src or src.tipo_recepcion != 'service':
                continue
            new_value = rec.service_return_confirmation or False
            if src.service_return_confirmation != new_value:
                src.write({'service_return_confirmation': new_value})

    @api.depends('product_id')
    def _compute_product_filter_id(self):
        """Valor mostrado del filtro: el producto común (mismo criterio que
        `product_id`). La búsqueda real NO usa este valor (ver `_search_`)."""
        for rec in self:
            rec.product_filter_id = rec.product_id

    def _search_product_filter_id(self, operator, value):
        """Traduce el filtro de producto a un dominio sobre los ORÍGENES.

        Reutiliza las relaciones existentes (líneas de recepción y de guía);
        devuelve un dominio sobre (source_model, source_res_id). No hace JOIN
        en la vista SQL: no multiplica filas ni pierde registros.
        """
        RecLine = self.env['lumber.reception.line']
        GuiaLine = self.env['madenat.guia.processing.line']

        def _contains_domain(ids):
            rec_ids = RecLine.search(
                [('product_id', 'in', ids)]).mapped('reception_id').ids
            guia_ids = GuiaLine.search(
                [('product_id', 'in', ids)]).mapped('processing_id').ids
            return ['|',
                    '&', ('source_model', '=', 'lumber.reception'),
                    ('source_res_id', 'in', rec_ids),
                    '&', ('source_model', '=', 'madenat.guia.processing'),
                    ('source_res_id', 'in', guia_ids)]

        if operator in ('=', 'in'):
            ids = value if isinstance(value, (list, tuple)) else [value]
            ids = [i for i in ids if i]
            if not ids:
                return [('id', '=', 0)]
            return _contains_domain(ids)
        if operator in ('!=', 'not in'):
            ids = value if isinstance(value, (list, tuple)) else [value]
            ids = [i for i in ids if i]
            if not ids:
                return []
            return ['!'] + _contains_domain(ids)
        return []

    def _common_many2one(self, lines, field_name):
        """Devuelve el valor común del campo Many2one si todas las líneas
        coinciden; si hay valores mixtos o vacío, devuelve recordset vacío."""
        values = lines.mapped(field_name)
        if values and all(l[field_name] == values[0] for l in lines):
            return values[0]
        return values.browse()

    def action_apply_product_subproduct(self):
        """Botón 'Aplicar cambios' / 'Complementar información del ingreso'.

        Producto/Procesado: abre el wizard masivo existente con defaults.
        Volúmenes: la etiqueta cambia a 'Complementar información del ingreso';
        permite completar producto, subproducto, referencias u observaciones,
        sin recalcular ni anular el volumen documental del PDF.

        No ejecuta el wizard silenciosamente; la confirmación explícita ocurre
        en el botón 'Aplicar Cambios' del wizard del core, que escribe
        Producto, Subproducto y nominales sobre las líneas reales.
        """
        self.ensure_one()
        # Defensa backend: en Volúmenes no hay edición comercial masiva. La
        # grilla de detalle documental es el único punto de complemento y no
        # recalcula geometría ni altera el volumen documental del PDF.
        if self.ingestion_type == 'volume':
            raise UserError(_(
                'El Ingreso por Volúmenes no admite edición comercial masiva. '
                'Use la grilla de detalle documental para corregir o complementar '
                'las filas; el volumen documental del PDF no se recalcula ni se '
                'altera.'))
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

    def action_assign_supplier(self):
        """Abre el wizard de asignación manual de proveedor (solo Volúmenes).

        Reutiliza `madenat.lumber.intake.supplier.link`; no crea partners ni
        escribe directamente sobre la vista SQL. No bloquea si se omite.
        """
        self.ensure_one()
        if self.ingestion_type != 'volume':
            raise UserError(
                _('La asignación manual de proveedor solo aplica a Volúmenes.'))
        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Asignar proveedor'),
            'res_model': 'madenat.lumber.intake.supplier.link',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_guia_id': src.id},
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
        elif self.ingestion_type == 'volume':
            # Volúmenes: PDF o Excel (al menos una evidencia); no exige Excel
            # ni dimensiones comerciales. El stock usa EXCLUSIVAMENTE el
            # volumen oficial documental (Guía PDF > Packing Excel > Packing
            # declarado); la suma del detalle nunca lo sustituye.
            if not (src.guide_pdf_file or src.excel_file or src.excel_attachment_id):
                errors.append(_('Falta evidencia documental (PDF o Excel).'))
            if not src.assignment_location_id:
                errors.append(_('Falta el Patio de Asignación (ubicación interna).'))
            if (src.official_volume_m3 or 0.0) <= 0:
                errors.append(
                    _('No existe volumen documental oficial para enviar a stock.'))
            if src.conciliation_status in ('needs_manual_review', 'incompatible'):
                errors.append(
                    _('La conciliación documental requiere confirmación manual.'))
            if src.state == 'validated':
                errors.append(_('La guía ya fue validada a stock.'))
            elif src.state != 'verified':
                errors.append(_('La guía debe estar en estado "Verificado".'))
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
        field = {'product': 'pdf_file', 'processed': 'guide_pdf_file',
                 'volume': 'guide_pdf_file'}.get(self.ingestion_type)
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

    def action_reclassify(self):
        """Abre el wizard de reclasificación delegando en el registro origen (AD-73)."""
        self.ensure_one()
        src = self._get_source_record()
        if src is None:
            raise UserError(_('El registro origen ya no existe.'))
        return src.action_reclassify()
