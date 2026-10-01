# -*- coding: utf-8 -*-
"""AD-88 — Principio rector «advertir, motivar, auditar».

Helper COMÚN para distinguir decisiones **blandas** (advertir + exigir motivo +
auditar, sin bloquear) de las **duras** (permisos por rol, integridad técnica y
reglas financieras, que sí bloquean).

No implementa reglas de negocio: solo centraliza la política y la evidencia
(snapshot determinista + firma SHA-256) en `madenat.audit.log`, siguiendo el
patrón del ledger SV (`madenat_sv_operation._sv_build_snapshot`).

Uso: el modelo que herede `madenat.deviation.mixin` llama
`self._guard_deviation(code, message, reason=..., hard=...)`.
"""
import hashlib
import json

from odoo import models, fields, _
from odoo.exceptions import UserError


class MadenatDeviationMixin(models.AbstractModel):
    """Mixin transversal del principio AD-88."""

    _name = 'madenat.deviation.mixin'
    _description = 'Mixin AD-88 — advertir, motivar, auditar'

    # Códigos duros por defecto (integridad técnica / financiera / permisos).
    DEVIATION_HARD_CODES = frozenset()

    def _guard_deviation(self, code, message, reason=None, hard=False,
                         extra=None):
        """Evalúa una desviación respecto de la propuesta/regla vigente.

        :param code: identificador estable (p. ej. ``'B-01'``).
        :param message: mensaje profesional para el usuario.
        :param reason: motivo obligatorio cuando la decisión es blanda.
        :param hard: ``True`` bloquea (permisos/integridad/finanzas);
            ``False`` advierte, exige motivo y audita.
        :param extra: ``dict`` opcional con datos para el snapshot.
        :return: ``True`` si la desviación blanda quedó registrada.
        :raises UserError: si ``hard=True`` o si falta el motivo en blando.
        """
        if hard or code in self.DEVIATION_HARD_CODES:
            raise UserError(_(
                '%(msg)s\n\nEsta validación es DURA (permisos, integridad '
                'técnica o reglas financieras) y no admite excepción.'
            ) % {'msg': message})
        reason = (reason or '').strip()
        if not reason:
            raise UserError(_(
                'Debe indicar un motivo para continuar con la excepción.\n\n'
                '%s') % message)
        snapshot = self._deviation_snapshot(code, message, reason, extra)
        self.env['madenat.audit.log'].sudo().create({
            'action_type': 'deviation',
            'description': '[%s] %s | Motivo: %s' % (
                code, message, reason[:180]),
            'batch_id': ','.join(str(rec_id) for rec_id in self.ids),
            'audit_snapshot': snapshot,
            'audit_hash': hashlib.sha256(
                snapshot.encode('utf-8')).hexdigest(),
            'user_id': self.env.user.id,
        })
        # Advertencia NO bloqueante en el chatter del registro (si aplica).
        for record in self:
            if record.id and hasattr(record, 'message_post'):
                record.message_post(body=_(
                    '⚠️ <b>Excepción registrada [%s]</b><br/>%s<br/>'
                    '<b>Motivo:</b> %s<br/><small>Usuario: %s</small>'
                ) % (code, message, reason, self.env.user.display_name))
        return True

    def _deviation_snapshot(self, code, message, reason, extra=None):
        """Snapshot determinista de la excepción (convención audit.log)."""
        payload = {
            'code': code,
            'message': message,
            'reason': reason,
            'model': self._name,
            'ids': sorted(self.ids),
            'extra': extra or {},
            'user': self.env.user.id,
            'timestamp': fields.Datetime.now().isoformat(),
        }
        return json.dumps(payload, sort_keys=True, default=str)
