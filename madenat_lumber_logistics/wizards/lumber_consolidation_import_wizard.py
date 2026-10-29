# -*- coding: utf-8 -*-
"""
Asistente de Importación de Consolidación de Tarjas desde Excel (Bloque 7.2).
Parser del formato real de doble bloque (Exportación izq / Compra der) de MADENAT.
Permite analizar y validar volúmenes contra el sistema antes de confirmar,
registra filas sin etiqueta como pendientes de asignación manual sin descartarlas
ni asignarlas en silencio, y agrupa contenedores repetidos sin duplicarlos.
No crea lotes ni modifica volúmenes en el inventario.
"""
import base64
import datetime
from io import BytesIO
import logging
import openpyxl
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LumberConsolidationImportWizard(models.TransientModel):
    _name = 'lumber.consolidation.import.wizard'
    _description = 'Asistente de Importación de Consolidación desde Excel'

    shipment_id = fields.Many2one(
        'lumber.export.shipment',
        string='Embarque',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    file_data = fields.Binary(
        string='Archivo Excel (TARJAS / LISTADO)',
        required=True,
        help='Subir Excel con formato de doble bloque de tarjas consolidadas'
    )
    file_name = fields.Char('Nombre Archivo')
    validate_only = fields.Boolean(
        string='Solo Validar',
        default=False,
        help='Si está marcado, solo valida sin importar'
    )
    state = fields.Selection([
        ('draft', 'Selección de Archivo'),
        ('analyzed', 'Analizado / Validación'),
        ('done', 'Importado'),
    ], default='draft', readonly=True)

    validation_summary = fields.Text(string='Resumen de Validación', readonly=True)
    difference_report = fields.Text(string='Informe de Discrepancias de Volumen', readonly=True)
    total_containers = fields.Integer(string='Contenedores Detectados', readonly=True)
    total_lots_matched = fields.Integer(string='Lotes Asignados / Coincidentes', readonly=True)
    total_pending_rows = fields.Integer(string='Filas Pendientes Asignación Manual', readonly=True)

    pending_line_ids = fields.One2many(
        'lumber.consolidation.import.pending',
        'wizard_id',
        string='Filas Pendientes de Asignación Manual'
    )

    def _find_lot_by_label(self, clean_label):
        """Busca un lote en el sistema por name, ref o external_labels.
        Retorna (lot, is_ambiguous, candidate_lots).
        DISC-OP-01 / DISC-LOG-01.
        """
        lot = self.env['stock.lot'].search([('name', '=', clean_label)], limit=1)
        if not lot:
            lot = self.env['stock.lot'].search([('ref', '=', clean_label)], limit=1)
        if not lot:
            # 1) Búsqueda exacta en external_labels
            exact_lots = self.env['stock.lot'].search([('external_labels', '=', clean_label)])
            if len(exact_lots) == 1:
                return exact_lots[0], False, exact_lots
            elif len(exact_lots) > 1:
                return self.env['stock.lot'], True, exact_lots
            else:
                # 2) Búsqueda de candidatos vía ilike y filtrado en Python por token exacto
                candidates = self.env['stock.lot'].search([('external_labels', 'ilike', clean_label)])
                target_upper = clean_label.upper()
                matched_lots = self.env['stock.lot']
                for cand in candidates:
                    tokens = [t.strip().upper() for t in (cand.external_labels or '').split(',') if t.strip()]
                    if target_upper in tokens:
                        matched_lots |= cand
                if len(matched_lots) == 1:
                    return matched_lots[0], False, matched_lots
                elif len(matched_lots) > 1:
                    return self.env['stock.lot'], True, matched_lots
        return lot, False, self.env['stock.lot']

    def action_validate_file(self):
        """Valida el archivo y extrae discrepancias sin aplicar cambios en BD."""
        self.ensure_one()
        self.validate_only = True
        return self._execute_import(apply_changes=False)

    def action_confirm_import(self):
        """Aplica la asignación de lotes a contenedores en el embarque."""
        self.ensure_one()
        self.validate_only = False
        return self._execute_import(apply_changes=True)

    def _execute_import(self, apply_changes=False):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_('Debe subir un archivo Excel.'))

        # Limpiar pendientes previos
        self.pending_line_ids.unlink()

        try:
            file_content = base64.b64decode(self.file_data)
            wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        except Exception as e:
            _logger.error(f'Error al abrir archivo Excel: {e}', exc_info=True)
            raise UserError(_('No se pudo leer el archivo Excel: %s') % str(e))

        # Selección de hoja prioritaria: busca 'TARJA' o 'LISTADO'
        target_sheet = None
        for sname in wb.sheetnames:
            if 'TARJA' in sname.upper():
                target_sheet = wb[sname]
                break
        if not target_sheet:
            for sname in wb.sheetnames:
                if 'LISTADO' in sname.upper():
                    target_sheet = wb[sname]
                    break
        if not target_sheet:
            target_sheet = wb.active

        # Estructuras de recolección
        containers_dict = {}  # container_code -> {'tarja': ..., 'seal': ..., 'gross': ..., 'tare': ..., 'lots': []}
        pending_rows = []
        differences = []

        # Parser de doble bloque
        current_tarja = None
        current_container = None
        current_seal = ''
        current_gross = 0.0
        current_tare = 0.0

        max_r = target_sheet.max_row
        for r in range(1, max_r + 1):
            # 1. Detección de Tarja / Contenedor
            cell_c = target_sheet.cell(r, 3).value
            cell_l = target_sheet.cell(r, 12).value
            cell_m = target_sheet.cell(r, 13).value
            cell_b = target_sheet.cell(r, 2).value

            # Patrón de Tarja: "TARJA " en col L o M
            if cell_l and 'TARJA' in str(cell_l).upper():
                current_tarja = str(cell_m or '').strip()
            elif cell_m and 'TARJA' in str(cell_m).upper():
                current_tarja = str(target_sheet.cell(r, 14).value or '').strip()

            # Encabezado "Contenedor" en col C / D
            if cell_c and 'CONTENEDOR' in str(cell_c).upper():
                # En la fila siguiente están los datos del contenedor
                next_c = target_sheet.cell(r + 1, 3).value or target_sheet.cell(r + 1, 2).value
                if next_c and not str(next_c).strip().upper().startswith('EMBARCADOR'):
                    current_container = str(next_c).strip()
                    current_seal = str(target_sheet.cell(r + 1, 4).value or target_sheet.cell(r + 1, 5).value or '').strip()
                    try:
                        current_gross = float(target_sheet.cell(r + 1, 5).value or target_sheet.cell(r + 1, 6).value or 0.0)
                    except (ValueError, TypeError):
                        current_gross = 0.0
                    try:
                        current_tare = float(target_sheet.cell(r + 1, 6).value or target_sheet.cell(r + 1, 7).value or 0.0)
                    except (ValueError, TypeError):
                        current_tare = 0.0

                    if current_container not in containers_dict:
                        containers_dict[current_container] = {
                            'tarja': current_tarja,
                            'seal': current_seal,
                            'gross': current_gross,
                            'tare': current_tare,
                            'lots': []
                        }

            # 2. Filas de datos de madera
            # Se identifican porque Col 2 (Embarcador) o Col 3 (Producto) contienen datos y no son encabezados
            val_emb = target_sheet.cell(r, 2).value
            val_prod = target_sheet.cell(r, 3).value
            val_planta = target_sheet.cell(r, 4).value
            val_label = target_sheet.cell(r, 5).value
            val_pqts = target_sheet.cell(r, 6).value
            val_sub = target_sheet.cell(r, 7).value
            val_esp = target_sheet.cell(r, 8).value
            val_ancho = target_sheet.cell(r, 9).value
            val_largo = target_sheet.cell(r, 10).value
            val_pzas = target_sheet.cell(r, 11).value
            val_m3_exp = target_sheet.cell(r, 12).value
            val_guia = target_sheet.cell(r, 13).value
            val_fecha = target_sheet.cell(r, 14).value

            val_m3_nom = target_sheet.cell(r, 26).value

            # Si es fila de encabezados o vacía, continuar
            if str(val_emb).strip().upper() in ('EMBARCADOR', 'NONE', '') and str(val_prod).strip().upper() in ('PRODUCTO', 'NONE', ''):
                continue

            # Si es fila de totales (Pqts > 1 sin etiqueta o M3 total al pie), continuar
            if not val_label and isinstance(val_pqts, (int, float)) and val_pqts > 1 and not val_guia:
                continue

            # Detectar fila de datos válida si tiene piezas, subproducto o medidas
            is_wood_row = (val_sub is not None or val_pzas is not None or val_guia is not None) and current_container
            if not is_wood_row:
                continue

            # Conversión segura de campos
            try:
                pzas_int = int(float(val_pzas)) if val_pzas is not None else 0
            except (ValueError, TypeError):
                pzas_int = 0

            try:
                largo_flt = float(val_largo) if val_largo is not None else 0.0
            except (ValueError, TypeError):
                largo_flt = 0.0

            try:
                m3_exp_flt = float(val_m3_exp) if val_m3_exp is not None else 0.0
            except (ValueError, TypeError):
                m3_exp_flt = 0.0

            try:
                m3_nom_flt = float(val_m3_nom) if val_m3_nom is not None else 0.0
            except (ValueError, TypeError):
                m3_nom_flt = 0.0

            fecha_dt = False
            if isinstance(val_fecha, datetime.datetime):
                fecha_dt = val_fecha.date()
            elif isinstance(val_fecha, datetime.date):
                fecha_dt = val_fecha

            # 3. Regla: Filas SIN etiqueta (San Joaquín, Ferramenta, etc.)
            clean_label = str(val_label).strip() if val_label is not None else ''
            if not clean_label or clean_label.upper() in ('NONE', 'S/N', 'SN', '0', ''):
                pending_rows.append({
                    'wizard_id': self.id,
                    'container_code': current_container,
                    'tarja_num': current_tarja or '',
                    'guia': str(val_guia or '').strip(),
                    'planta': str(val_planta or '').strip(),
                    'subproducto': str(val_sub or '').strip(),
                    'espesor': str(val_esp or '').strip(),
                    'ancho': str(val_ancho or '').strip(),
                    'largo': largo_flt,
                    'piezas': pzas_int,
                    'm3_exp': m3_exp_flt,
                    'm3_nom': m3_nom_flt,
                    'fecha': fecha_dt,
                    'reason': _('Fila sin etiqueta (requiere asignación manual).')
                })
                continue

            # 4. Filas CON etiqueta: buscar lote en el sistema (sin crear ni modificar)
            lot, is_ambiguous, _amb_lots = self._find_lot_by_label(clean_label)
            if is_ambiguous:
                pending_rows.append({
                    'wizard_id': self.id,
                    'container_code': current_container,
                    'tarja_num': current_tarja or '',
                    'guia': str(val_guia or '').strip(),
                    'planta': str(val_planta or '').strip(),
                    'subproducto': str(val_sub or '').strip(),
                    'espesor': str(val_esp or '').strip(),
                    'ancho': str(val_ancho or '').strip(),
                    'largo': largo_flt,
                    'piezas': pzas_int,
                    'm3_exp': m3_exp_flt,
                    'm3_nom': m3_nom_flt,
                    'fecha': fecha_dt,
                    'reason': _('Ambigüedad: múltiples lotes encontrados con la etiqueta externa %s.') % clean_label
                })
                continue

            if not lot:
                pending_rows.append({
                    'wizard_id': self.id,
                    'container_code': current_container,
                    'tarja_num': current_tarja or '',
                    'guia': str(val_guia or '').strip(),
                    'planta': str(val_planta or '').strip(),
                    'subproducto': str(val_sub or '').strip(),
                    'espesor': str(val_esp or '').strip(),
                    'ancho': str(val_ancho or '').strip(),
                    'largo': largo_flt,
                    'piezas': pzas_int,
                    'm3_exp': m3_exp_flt,
                    'm3_nom': m3_nom_flt,
                    'fecha': fecha_dt,
                    'reason': _('Etiqueta %s no encontrada en inventario.') % clean_label
                })
                continue

            # Lote encontrado: validar volúmenes contra el sistema
            sys_exp = round(lot.vol_shipment_m3 or 0.0, 3)
            sys_nom = round(lot.volumen_m3 or 0.0, 3)
            diff_exp = abs(sys_exp - round(m3_exp_flt, 3))
            diff_nom = abs(sys_nom - round(m3_nom_flt, 3))

            if diff_exp > 0.005 or diff_nom > 0.005:
                differences.append(
                    _('Lote %s (Cont. %s): EXP Archivo=%0.3f vs Sistema=%0.3f (dif %0.3f) | NOM Archivo=%0.3f vs Sistema=%0.3f (dif %0.3f)') % (
                        lot.name, current_container, m3_exp_flt, sys_exp, diff_exp, m3_nom_flt, sys_nom, diff_nom
                    )
                )

            containers_dict[current_container]['lots'].append(lot)

        # Crear filas pendientes en el wizard
        if pending_rows:
            self.env['lumber.consolidation.import.pending'].create(pending_rows)

        total_matched = sum(len(c['lots']) for c in containers_dict.values())
        summary_lines = [
            _('✓ Contenedores detectados: %d') % len(containers_dict),
            _('✓ Lotes coincidentes validados: %d') % total_matched,
            _('⚠ Filas pendientes de asignación manual: %d') % len(pending_rows),
        ]
        if differences:
            summary_lines.append(_('⚠ Discrepancias de volumen detectadas: %d') % len(differences))

        self.write({
            'total_containers': len(containers_dict),
            'total_lots_matched': total_matched,
            'total_pending_rows': len(pending_rows),
            'validation_summary': '\n'.join(summary_lines),
            'difference_report': '\n'.join(differences) if differences else _('Sin discrepancias significativas de volumen (tolerancia 0.005 m³).'),
            'state': 'analyzed' if not apply_changes else 'done',
        })

        # Aplicar asignaciones solo si apply_changes=True (sin crear lotes ni modificar volúmenes)
        if apply_changes:
            for cont_code, cdata in containers_dict.items():
                if not cont_code:
                    continue
                # Buscar o crear contenedor en el embarque
                container = self.env['lumber.container'].search([
                    ('shipment_id', '=', self.shipment_id.id),
                    ('name', '=', cont_code)
                ], limit=1)
                if not container:
                    container = self.env['lumber.container'].create({
                        'shipment_id': self.shipment_id.id,
                        'name': cont_code,
                        'seal_number': cdata.get('seal') or '',
                        'container_type': '40HC',
                        'gross_weight_kg': cdata.get('gross') or 0.0,
                        'tare_weight_kg': cdata.get('tare') or 0.0,
                    })
                # Asignar lotes encontrados (acumular sin descartar previos de contenedor repetido)
                if cdata['lots']:
                    lot_ids = [l.id for l in cdata['lots']]
                    container.write({'lot_ids': [(4, lid) for lid in lot_ids]})

            self.shipment_id.message_post(body=_(
                '📥 <b>Consolidación Importada desde Excel</b><br/>'
                'Archivo: %s<br/>Contenedores: %d | Lotes asignados: %d | Filas pendientes: %d'
            ) % (self.file_name or 'Excel', len(containers_dict), total_matched, len(pending_rows)))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Consolidación Aplicada'),
                    'message': _('Se procesaron %d contenedores y se asignaron %d lotes.') % (len(containers_dict), total_matched),
                    'type': 'success',
                    'sticky': False,
                }
            }

        # Retornar vista del wizard en estado analizado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.consolidation.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class LumberConsolidationImportPending(models.TransientModel):
    _name = 'lumber.consolidation.import.pending'
    _description = 'Fila Pendiente de Asignación Manual'

    wizard_id = fields.Many2one('lumber.consolidation.import.wizard', string='Wizard', ondelete='cascade')
    container_code = fields.Char('Contenedor', readonly=True)
    tarja_num = fields.Char('Tarja N°', readonly=True)
    guia = fields.Char('Guía', readonly=True)
    planta = fields.Char('Planta', readonly=True)
    subproducto = fields.Char('Subproducto', readonly=True)
    espesor = fields.Char('Espesor', readonly=True)
    ancho = fields.Char('Ancho', readonly=True)
    largo = fields.Float('Largo (m)', digits=(16, 3), readonly=True)
    piezas = fields.Integer('Piezas', readonly=True)
    m3_exp = fields.Float('M3 Exportación', digits=(16, 3), readonly=True)
    m3_nom = fields.Float('M3 Nominal/Compra', digits=(16, 3), readonly=True)
    fecha = fields.Date('Fecha', readonly=True)
    reason = fields.Char('Motivo Pendiente', readonly=True)
