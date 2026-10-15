# -*- coding: utf-8 -*-
"""Línea de detalle documental editable para Ingreso por Volúmenes.

Es una representación consultable y editable del detalle extraído del PDF
(lote/paquete, código, descripción, volumen, U/M, precio, total), SIN
dimensiones físicas ni cálculo geométrico. El operador puede corregir o
complementar cada fila; el volumen documental del PDF nunca se recalcula
automáticamente desde estas líneas.

Captura declarada por fila (bloque «DATOS DECLARADOS DE LA GUÍA»):

- `pieces`: piezas declaradas de la fila (columna «Piezas»). Es SIEMPRE
  captura humana o valor documental explícito: el motor de extracción de la
  ruta PDF genérica entrega `pieces=1` como marcador interno
  (`document_extractor._build_generic_line`), por lo que ese valor NO se
  persiste (fabricaría piezas). Sin captura queda en 0.
- `width_declared` / `length_declared` / `thickness_declared`: designación
  comercial declarada por fila (RW / RL / espesor nominal) como TEXTO, igual
  que la cabecera declarada de la Guía. Nunca se usan para calcular volumen.
- `line_no`: correlativo de la fila dentro del detalle de su Guía (solo
  lectura, calculado; no se almacena ni reemplaza a `source_line_no`).

Fila de cabecera declarada (`origin = 'header'`): como máximo UNA por guía.
Representa los datos declarados de la cabecera (piezas, RW, RL y espesor
nominal) cuando el operador pulsa «Aplicar datos documentales». Su marca de
idempotencia es el propio `origin`; se actualiza en el lugar (nunca se
duplica) y nunca se sobrescribe si tiene `manually_adjusted=True`.

Ninguno de estos campos altera el volumen documental/oficial, el stock, los
lotes, la conciliación ni la consolidación.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .intake_constants import (
    CONSOLE_ID_OFFSET,
    DECLARED_GUIA_ID_CONTEXT,
    DECLARED_MANUAL_ENTRY_CONTEXT,
    HEADER_DECLARED_ORIGIN,
)


class MadenatLumberVolumeDetailLine(models.Model):
    _name = 'madenat.lumber.volume.detail.line'
    _description = 'Línea de detalle documental — Ingreso por Volúmenes'
    _order = 'source_line_no, id'

    guia_id = fields.Many2one(
        'madenat.guia.processing', string='Guía',
        ondelete='cascade', required=True, index=True,
        help='Guía de recepción Granel a la que pertenece esta línea documental.'
    )

    lot_or_package = fields.Char(string='Lote/Paquete')
    material_code = fields.Char(string='Código')
    description = fields.Char(string='Descripción')
    volume_m3 = fields.Float(string='Volumen (m³)', digits=(16, 3))
    uom = fields.Char(string='U/M')
    unit_price = fields.Float(string='Precio unitario', digits=(16, 3))
    line_amount = fields.Float(string='Total línea', digits=(16, 3))
    observation = fields.Text(string='Observación')

    # Trazabilidad del origen documental (solo lectura, evidencia).
    source_page = fields.Integer(string='Página fuente')
    source_line_no = fields.Integer(string='Línea fuente')
    confidence = fields.Float(string='Confianza', digits=(16, 3))
    origin = fields.Selection(
        [('pdf', 'PDF'), ('excel', 'Excel'), ('manual', 'Manual'),
         ('header', 'Cabecera declarada')],
        string='Origen', default='pdf', required=True,
        help='Origen de la fila: extraída del PDF, del Excel, ingresada '
             'manualmente o declarada en la cabecera de la guía (una sola '
             'fila por guía, sincronizada por «Aplicar datos documentales»).'
    )

    # Origen EXCLUSIVO de la fila única que representa los datos declarados de
    # la cabecera de la guía. Es la marca inequívoca de idempotencia: como
    # máximo existe una fila con este origen por guía.
    HEADER_ORIGIN = HEADER_DECLARED_ORIGIN

    # Flag de ajuste manual: registra que una fila documental fue corregida
    # por el operador sin sobrescribir su origen original.
    manually_adjusted = fields.Boolean(
        string='Ajustada manualmente', default=False,
        help='Marca que la fila fue editada por el usuario después de la '
             'extracción, conservando el origen documental original.',
    )

    # ── Captura declarada por fila (bloque «Piezas Declaradas») ───────────
    pieces = fields.Integer(
        string='Piezas',
        help='Piezas declaradas de la fila. Se captura desde el detalle '
             'declarado de la guía y queda en 0 cuando el documento no '
             'declara piezas por fila (nunca se infiere ni se fabrica).',
    )
    width_declared = fields.Char(
        string='Ancho (RW)',
        help='Designación comercial declarada de la fila (Random Width). '
             'Texto documental; no calcula volumen.',
    )
    length_declared = fields.Char(
        string='Largo (RL)',
        help='Designación comercial declarada de la fila (Random Length). '
             'Texto documental; no calcula volumen.',
    )
    thickness_declared = fields.Char(
        string='Espesor nominal',
        help='Espesor nominal declarado de la fila (designación comercial). '
             'Texto documental; no calcula volumen.',
    )
    line_no = fields.Integer(
        string='N°',
        compute='_compute_line_no',
        help='Número correlativo e informativo de la fila dentro del detalle '
             'declarado de su guía. No se almacena y no reemplaza la '
             'trazabilidad documental (`source_line_no`).',
    )

    # ── Piezas declaradas: aplicación documental y protección manual ───────
    # Contexto interno: la escritura de `pieces` proviene de la extracción
    # documental (no marca ajuste manual del operador).
    DOCUMENTAL_PIECES_CONTEXT = 'madenat_volume_pieces_from_document'

    @api.model
    def _documental_pieces(self, row):
        """Clasifica `pieces` de una fila extraída: (declarado, valor, inválido).

        Reglas no negociables (una pieza real nunca se fabrica):

        - entero ≥ 0 provisto explícitamente por la extracción documental →
          ``(True, valor, False)``;
        - clave ausente / ``None`` / cadena vacía → ``(False, 0, False)``: el
          documento NO declara piezas por línea (el marcador técnico histórico
          ya no existe en el extractor);
        - valor booleano, no numérico, con decimales inválidos o negativo →
          ``(False, 0, True)``: es ambiguo, NO se persiste y se informa.
        """
        raw = row.get('pieces')
        if raw is None or raw == '' or raw is False:
            return (False, 0, False)
        if isinstance(raw, bool):
            return (False, 0, True)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            try:
                value = int(round(float(raw)))
            except (TypeError, ValueError):
                return (False, 0, True)
        if value < 0:
            return (False, 0, True)
        return (True, value, False)

    def _apply_documental_pieces(self, rows):
        """Aplica las piezas declaradas por el documento (idempotente).

        Empareja cada fila extraída con su línea real por la trazabilidad del
        origen documental (``origin`` + ``source_line_no``), de modo que
        re-procesar el mismo documento no duplica líneas ni cantidades.

        Garantías:
        - las líneas con ``manually_adjusted=True`` NUNCA se sobrescriben;
        - si no existe una equivalencia inequívoca (0 o más de 1 candidata) no
          se borra ni se reemplaza nada: se informa la incidencia;
        - los valores ambiguos o negativos no se persisten y se informan;
        - no crea ni elimina líneas, no toca ``origin``, volúmenes, estado,
          lotes, stock, conciliación, chatter ni bitácora.

        Retorna un resumen con contadores e incidencias para auditoría.
        """
        summary = {
            'applied': 0,
            'protected': 0,
            'mismatch': [],
            'invalid': [],
        }
        for guia in self.mapped('guia_id'):
            lines = self.filtered(lambda line: line.guia_id == guia)
            for row in rows or []:
                declared, value, invalid = self._documental_pieces(row)
                origin = row.get('origin') or ''
                source_line_no = row.get('source_line_no') or 0
                reference = '%s/%s' % (origin or '?', source_line_no)
                if invalid:
                    summary['invalid'].append(reference)
                    continue
                if not declared:
                    continue
                target = lines.filtered(
                    lambda line: line.origin == origin
                    and line.source_line_no == source_line_no)
                if len(target) != 1:
                    summary['mismatch'].append(reference)
                    continue
                if target.manually_adjusted:
                    summary['protected'] += 1
                    continue
                if (target.pieces or 0) != value:
                    target.with_context(**{
                        self.DOCUMENTAL_PIECES_CONTEXT: True,
                    }).write({'pieces': value})
                    summary['applied'] += 1
        return summary

    # ── Captura manual del detalle declarado (diálogo «Agregar ítem») ──────
    @api.model
    def _resolve_declared_guia_id(self, reference):
        """Resuelve la guía REAL de Volumen a partir de una referencia.

        Acepta un id, un ``{'id': ...}`` (formato del cliente web para x2many),
        un recordset de guía o uno de la CONSOLA. Si la referencia es un id de
        la consola (`CONSOLE_ID_OFFSET + id`), se resuelve la guía real vía
        ``source_res_id``; así un ``default_guia_id`` o el ``guia_id`` que el
        cliente web inyecta en el onchange NUNCA se interpreta como una guía.

        Es defensivo y de LECTURA: devuelve ``False`` cuando no puede
        resolverse a una guía existente (no crea, no escribe y no valida
        estados).
        """
        if isinstance(reference, models.BaseModel):
            if reference._name == 'madenat.guia.processing':
                return reference.id or False
            if reference._name == 'madenat.lumber.intake.console':
                return reference.source_res_id or False
            reference = reference.id
        elif isinstance(reference, dict):
            reference = reference.get('id')
        if not reference or not isinstance(reference, int):
            return False
        if reference >= CONSOLE_ID_OFFSET:
            console = self.env['madenat.lumber.intake.console'].browse(reference)
            if (console.source_model == 'madenat.guia.processing'
                    and console.ingestion_type == 'volume'
                    and console.source_res_id):
                return console.source_res_id
            return False
        return self.env['madenat.guia.processing'].browse(reference).exists().id \
            or False

    @api.model
    def _check_declared_manual_entry_guia(self, guia_id):
        """Valida la guía destino de una captura manual desde el diálogo.

        Guardas duras (servidor, no solo vista):
        - debe existir la guía;
        - debe ser una guía REAL de Ingreso por Volúmenes
          (`tipo_recepcion == 'granel'`);
        - no puede estar en estado terminal (`validated`/`cancelled`).
        """
        guia = self.env['madenat.guia.processing'].browse(guia_id or 0)
        if not guia:
            raise UserError(_('Debe indicar la guía de la línea declarada.'))
        if guia.tipo_recepcion != 'granel':
            raise UserError(_(
                'El detalle declarado solo aplica a guías de Ingreso por '
                'Volúmenes.'))
        if guia.state in ('validated', 'cancelled'):
            raise UserError(_(
                'No se puede modificar el detalle declarado de una guía ya '
                'validada o cancelada.'))

    @api.model
    def default_get(self, fields_list):
        """Neutraliza un ``default_guia_id`` que apunte a la CONSOLA.

        Si algún flujo entrega la guía del detalle declarado como
        ``default_guia_id`` con el id del registro padre de la consola (offset
        de la vista SQL), se traduce a la guía real antes de exponerla, de modo
        que el formulario nunca precargue una guía inexistente.
        """
        vals = super().default_get(fields_list)
        if vals.get('guia_id'):
            guia_id = self._resolve_declared_guia_id(vals['guia_id'])
            if guia_id:
                vals['guia_id'] = guia_id
            else:
                vals.pop('guia_id', None)
        return vals

    # IMPORTANTE (capa RPC): `onchange` NO lleva `@api.model`.
    # El dispatcher `odoo.api.call_kw` decide cómo despachar según
    # `getattr(method, '_api', None)`: si `_api` existe (@api.model) NO extrae
    # los ids y pasa la lista de ids como PRIMER argumento posicional, con lo
    # que el RPC del navegador rompía:
    #   TypeError: onchange() takes 4 positional arguments but 5 were given
    # El `onchange` base (`addons/web/models/models.py`) es un método de
    # registro con `_api=None`; replicamos exactamente eso (misma firma, sin
    # decorador) para que `call_kw` haga `ids, args = args[0], args[1:]` y
    # llame `records.onchange(values, field_names, fields_spec)`.
    def onchange(self, values, field_names, fields_spec):
        """Normaliza el ``guia_id`` que el cliente web inyecta al añadir una
        línea inline en ``declared_piece_line_ids``.

        `declared_piece_line_ids` (Consola) es un One2many no almacenado cuyo
        campo inverso es ``guia_id``. Al añadir una línea en la lista editable,
        el cliente web envía ``guia_id`` con el id del registro padre (la
        CONSOLA) con forma de dict; Odoo lo convierte en un registro de guía EN
        MEMORIA (``NewId``) y su ``_update_cache`` ejecuta
        ``modified('declared_piece_line_ids')`` sobre registros de
        ``madenat.guia.processing`` — modelo que NO tiene ese campo — y falla
        con KeyError. Aquí se resuelve la guía real (o se descarta la
        referencia) ANTES de delegar al onchange estándar, de modo que la caché
        sólo vea un id real de guía existente.

        No altera onchanges propios: solo normaliza el valor de ``guia_id``.
        """
        if values and 'guia_id' in values:
            values = dict(values)
            guia_id = self._resolve_declared_guia_id(values.get('guia_id'))
            if guia_id:
                values['guia_id'] = guia_id
            else:
                values.pop('guia_id', None)
        return super().onchange(values, field_names, fields_spec)

    # ── Recomputación real de la consola (AUD-ETQ-08, 2026-10-12) ─────────
    # La consola `madenat.lumber.intake.console` es una VISTA SQL (`_auto=False`)
    # cuyos campos no se almacenan y se recomputan por lectura. No existe una
    # relación ORM directa consola↔línea de detalle, por lo que la caché de la
    # consola NO se invalidaba sola al cambiar una línea: una segunda lectura en
    # el MISMO entorno devolvía valores obsoletos (defecto confirmado). Para que
    # la actualización sea real en el mismo entorno, cada create/write/unlink de
    # esta línea invalida de forma DIRIGIDA los campos calculados de la consola
    # que dependen del detalle (un solo modelo, sólo los campos afectados).
    # No es recomputación global, no hay `search` ficticio y no se cambia `store`.
    CONSOLE_METRIC_COMPUTES = (
        '_compute_review_metrics',
        '_compute_declared_piece_line_totals',
        '_compute_official_volume_effective',
    )

    def _invalidate_console_metrics(self):
        """Invalida (dirigidamente) las métricas de la consola que dependen del
        detalle documental, para que se recomputen en el MISMO entorno."""
        Console = self.env['madenat.lumber.intake.console']
        fnames = [name for name, field in Console._fields.items()
                  if field.compute in self.CONSOLE_METRIC_COMPUTES]
        if fnames:
            Console.invalidate_model(fnames)

    @api.model_create_multi
    def create(self, vals_list):
        """Crea líneas del detalle documental.

        La guía puede llegar:
        - en ``guia_id`` (ruta estándar / wizard de ingesta); o
        - en el contexto propio del diálogo ``DECLARED_GUIA_ID_CONTEXT``
          cuando el formulario del diálogo NO expone ``guia_id`` (evita
          ``default_guia_id`` y su KeyError de onchange).

        Con el contexto del diálogo «Agregar ítem»
        (`DECLARED_MANUAL_ENTRY_CONTEXT`) la operación es captura HUMANA del
        detalle declarado: valida la guía y fuerza `origin='manual'`, de modo
        que el diálogo nunca crea evidencia `pdf`/`excel` ni la fila `header`.
        Sin ese contexto el comportamiento es el estándar (wizard de ingesta y
        cualquier otra ruta). En todos los casos un ``guia_id`` que llegue con
        el id de la CONSOLA se resuelve a la guía real.
        """
        declared_entry = self.env.context.get(DECLARED_MANUAL_ENTRY_CONTEXT)
        context_guia = self.env.context.get(DECLARED_GUIA_ID_CONTEXT)
        sanitized = []
        for vals in vals_list:
            vals = dict(vals)
            guia_ref = vals.get('guia_id')
            if not guia_ref and declared_entry and context_guia:
                # El diálogo transporta la guía en su contexto propio.
                guia_ref = context_guia
            guia_id = self._resolve_declared_guia_id(guia_ref)
            if guia_id:
                vals['guia_id'] = guia_id
            if declared_entry:
                self._check_declared_manual_entry_guia(vals.get('guia_id'))
                # El diálogo es SIEMPRE captura manual: nunca pdf/excel/header.
                vals['origin'] = 'manual'
            sanitized.append(vals)
        records = super().create(sanitized)
        records._invalidate_console_metrics()
        return records

    def write(self, vals):
        """Marca el ajuste manual del operador sobre las piezas declaradas.

        Toda escritura de `pieces` que NO provenga de la aplicación documental
        (contexto interno `DOCUMENTAL_PIECES_CONTEXT`) marca la fila como
        ``manually_adjusted``: es el flag de diseño existente y la garantía de
        que una nueva lectura/procesamiento del documento no sobrescriba una
        corrección manual del operador.
        """
        if 'guia_id' in vals:
            # Nunca (re)asignar la guía de la línea con un id de la CONSOLA
            # (offset de la vista SQL): se resuelve a la guía real de Volumen.
            guia_id = self._resolve_declared_guia_id(vals['guia_id'])
            if guia_id:
                vals = dict(vals, guia_id=guia_id)
        if self.env.context.get(DECLARED_MANUAL_ENTRY_CONTEXT):
            # El diálogo de captura solo admite filas MANUALES y nunca cambia
            # el origen: no edita evidencia pdf/excel ni la fila header.
            if any(line.origin != 'manual' for line in self):
                raise UserError(_(
                    'Solo se pueden editar filas manuales desde el diálogo de '
                    'captura declarada.'))
            vals = {key: value for key, value in vals.items()
                    if key != 'origin'}
        if ('pieces' in vals
                and not self.env.context.get(self.DOCUMENTAL_PIECES_CONTEXT)):
            incoming = vals.get('pieces') or 0
            if any((line.pieces or 0) != incoming for line in self):
                vals = dict(vals, manually_adjusted=True)
        result = super().write(vals)
        self._invalidate_console_metrics()
        return result

    def unlink(self):
        """Elimina líneas del detalle documental.

        Además de la baja ORM, invalida de forma dirigida las métricas de la
        consola que dependen del detalle, para que una lectura posterior en el
        MISMO entorno refleje la eliminación (AUD-ETQ-08).
        """
        Console = self.env['madenat.lumber.intake.console']
        fnames = [name for name, field in Console._fields.items()
                  if field.compute in self.CONSOLE_METRIC_COMPUTES]
        result = super().unlink()
        if fnames:
            Console.invalidate_model(fnames)
        return result

    @api.depends('guia_id', 'guia_id.volume_detail_line_ids', 'source_line_no')
    def _compute_line_no(self):
        """Numera las filas 1..N según el orden real del detalle de la guía.

        Solo lectura y de presentación: no escribe en la base de datos, no
        reordena nada y nunca se usa en cálculos de volumen, stock ni costos.
        """
        for line in self:
            line.line_no = 0
        for guia in self.guia_id:
            siblings = guia.volume_detail_line_ids.sorted(
                key=lambda row: (
                    row.source_line_no or 0,
                    row.id if isinstance(row.id, int) else 0,
                ))
            for index, sibling in enumerate(siblings, start=1):
                if sibling in self:
                    sibling.line_no = index

    @api.constrains('pieces')
    def _check_pieces(self):
        """Previene una cantidad de piezas claramente inválida (negativa)."""
        for line in self:
            if line.pieces < 0:
                raise ValidationError(_(
                    'Las piezas declaradas no pueden ser negativas '
                    '(línea %(name)s).') % {'name': line.description or line.id})
