# -*- coding: utf-8 -*-
"""CDP-V1 — Corrección Documental Preservada para `madenat.guia.processing`.

Permite que un operador autorizado corrija datos DOCUMENTALES de una guía
existente —incluida `validated` o con historia de retorno— SIN modificar
estado, stock, lotes, pickings, movimientos, retornos, costos, SV ni
relaciones físicas.

Aditivo: NO sustituye ni modifica G1/G2/G3/H1/B1, Intake, BT-04, Granel/SV
ni stock nativo. No crea estados. No revalida ni procesa stock.
"""
import hashlib
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MadenatGuiaProcessingDocumental(models.Model):
    """Extensión aditiva CDP-V1 (solo campos documentales)."""

    _inherit = 'madenat.guia.processing'

    # ── Lista blanca EXCLUSIVA de campos documentales corregibles ────────
    # Solo campos reales, editables, sin cómputo físico/financiero ni
    # dependencias que escriban stock/lotes/costos.
    CDP_DOCUMENTAL_WHITELIST = (
        'notes',
        'date_emission',
        'oc_reference_raw',
        'carrier_id',
        'assignment_location_id',
        'packing_volume_declared_m3',
        'packing_pieces_declared',
        'packing_package_count_declared',
        'vol_comercial_pdf',
        'total_paquetes',
        'total_lotes_unicos',
    )

    # Adjuntos versionables: (campo M2O, binario wizard, nombre wizard, desc).
    CDP_ATTACHMENT_WHITELIST = (
        ('pdf_attachment_id', 'new_pdf_file', 'new_pdf_filename', 'Guía PDF'),
        ('excel_attachment_id', 'new_excel_file', 'new_excel_filename',
         'Excel Packing'),
    )

    # ── Acción pública secundaria: abre el asistente (no ejecuta nada) ───
    def action_open_documental_correction_wizard(self):
        """Abre el asistente de corrección documental (CDP-V1)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Corrección documental (CDP-V1)'),
            'res_model':
                'madenat.guia.processing.documental.correction.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref(
                'madenat_lumber_core.'
                'view_madenat_guia_processing_documental_correction_wizard_form'
            ).id,
            'context': {'default_guia_processing_id': self.id},
        }

    # ── Advertencias NO bloqueantes sobre historia física (solo lectura) ─
    def _cdp_physical_history_warnings(self):
        """Lista de advertencias informativas. Nunca bloquea."""
        self.ensure_one()
        warnings = []
        if self.state == 'validated':
            warnings.append(_(
                'La guía está VALIDADA: la corrección documental no revalida '
                'ni reprocesa stock.'))
        done_fk = self.env['stock.picking'].search_count([
            ('guia_processing_id', '=', self.id), ('state', '=', 'done')])
        if done_fk:
            warnings.append(_(
                'Existen %s albarán(es) de ingreso done vinculados (G2): no '
                'se modifican.') % done_fk)
        if self.consumption_picking_id:
            warnings.append(_(
                'Consumo BT-04 activo (%s): no se modifica.'
            ) % self.consumption_picking_id.name)
        if self.lot_ids:
            warnings.append(_(
                'La guía conserva %s lote(s): no se alteran.'
            ) % len(self.lot_ids))
        return warnings

    # ── Utilidades internas CDP-V1 ───────────────────────────────────────
    @api.model
    def _cdp_whitelist(self):
        return frozenset(self.CDP_DOCUMENTAL_WHITELIST)

    def _cdp_validate_whitelist(self, field_names):
        """Valida server-side que todo nombre pertenezca a la lista blanca."""
        unknown = set(field_names or ()) - self._cdp_whitelist()
        if unknown:
            raise UserError(_(
                'Campos NO autorizados por CDP-V1 (solo corrección '
                'documental): %s') % ', '.join(sorted(unknown)))
        return True

    def _cdp_serialize(self, name):
        """Valor JSON-serializable de un campo de la lista blanca."""
        field = self._fields[name]
        value = self[name]
        if field.type == 'many2one':
            return value.id or False
        return value

    def _cdp_wizard_value(self, wizard, name):
        """Lee del asistente el valor de un campo de la lista blanca."""
        self._cdp_validate_whitelist([name])
        field = self._fields[name]
        value = wizard[name]
        if field.type == 'many2one':
            return value.id or False
        return value

    def _cdp_version_attachments(self, wizard):
        """Crea nuevas versiones de adjuntos SIN eliminar las anteriores."""
        self.ensure_one()
        changes = []
        for (attach_field, bin_field, name_field,
             desc) in self.CDP_ATTACHMENT_WHITELIST:
            datas = wizard[bin_field]
            if not datas:
                continue
            old = self[attach_field]
            attachment = self.env['ir.attachment'].create({
                'name': wizard[name_field] or desc,
                'datas': datas,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })
            self[attach_field] = attachment.id
            changes.append({
                'field': attach_field,
                'previous_id': old.id if old else False,
                'previous_name': old.name if old else False,
                'new_id': attachment.id,
                'new_name': attachment.name,
            })
        return changes


    def _cdp_register_audit(self, reason, before, after, attachment_changes):
        """Audit log `deviation` (snapshot/hash) + chatter (no bloqueante)."""
        self.ensure_one()
        edited = sorted(
            name for name in after if before.get(name) != after.get(name))
        snapshot = json.dumps({
            'code': 'CDP-V1',
            'guia': self.name,
            'guia_id': self.id,
            'state': self.state,
            'reason': reason,
            'before': before,
            'after': after,
            'edited_fields': edited,
            'attachments': attachment_changes,
            'lots': self.lot_ids.mapped('name'),
            'user': self.env.user.id,
            'timestamp': fields.Datetime.now().isoformat(),
        }, sort_keys=True, default=str)
        self.env['madenat.audit.log'].sudo().create({
            'guia_processing_id': self.id,
            'action_type': 'deviation',
            'description': '[CDP-V1] Corrección documental | Motivo: %s'
                           % reason[:180],
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })
        attach_txt = ', '.join(
            '%s: %s → %s' % (c['field'], c['previous_name'] or '-',
                             c['new_name'])
            for c in attachment_changes) or '-'
        self.message_post(body=_(
            '✏️ <strong>Corrección documental (CDP-V1)</strong><br/>'
            'Motivo: %(reason)s<br/>'
            'Campos editados: %(fields)s<br/>'
            'Adjuntos: %(attach)s<br/>'
            '<small>No se modificó estado, stock, lotes, pickings, '
            'movimientos, retornos ni costos. Usuario: %(user)s</small>'
        ) % {
            'reason': reason,
            'fields': ', '.join(edited) or '(sin cambios de valor)',
            'attach': attach_txt,
            'user': self.env.user.display_name,
        })

    def _cdp_apply_documental_correction(self, wizard):
        """Aplica la corrección documental (CDP-V1). Privado (no RPC).

        - Exige un asistente válido ligado a esta guía.
        - Escribe EXCLUSIVAMENTE campos de la lista blanca.
        - Versiona adjuntos SIN eliminar la versión anterior.
        - NO llama procesamiento/validación/reversión de stock.
        - Registra auditoría (deviation + snapshot/hash) y chatter.
        """
        self.ensure_one()
        wizard_model = (
            'madenat.guia.processing.documental.correction.wizard')
        if (not wizard or wizard._name != wizard_model
                or not wizard.exists()
                or wizard.guia_processing_id != self):
            raise UserError(_(
                'Confirmación inválida: el asistente no corresponde a esta '
                'guía.'))
        reason = (wizard.reason or '').strip()
        if not reason:
            raise UserError(_(
                'Debe indicar un motivo: la corrección documental es '
                'trazabilidad, no aprobación.'))

        names = list(self.CDP_DOCUMENTAL_WHITELIST)
        self._cdp_validate_whitelist(names)
        before = {name: self._cdp_serialize(name) for name in names}
        vals = {}
        for name in names:
            value = self._cdp_wizard_value(wizard, name)
            if self._fields[name].required and not value:
                # Un campo obligatorio NUNCA se anula: se conserva el vigente.
                continue
            vals[name] = value

        # Escritura documental explícita (solo lista blanca).
        self.write(vals)

        # Versionado de adjuntos sin unlink (preserva la versión anterior).
        attachment_changes = self._cdp_version_attachments(wizard)

        self._cdp_register_audit(reason, before, dict(vals),
                                 attachment_changes)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.guia.processing',
            'res_id': self.id, 'view_mode': 'form', 'target': 'current',
        }

