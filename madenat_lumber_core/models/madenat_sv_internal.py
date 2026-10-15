# -*- coding: utf-8 -*-
"""Infraestructura técnica interna del Programa SV (sin exposición funcional).

Contiene dos modelos deliberadamente invisibles para usuarios de negocio
(no tienen ACL, vistas, acciones, menús ni campos relacionados; solo pueden
usarse mediante `sudo()` desde código servidor):

1. `madenat.sv.internal.capability`
   Capacidad de un solo uso que autoriza una escritura protegida sobre un lote
   SV. Se acuña dentro de la aplicación atómica de una operación y se consume
   (unlink) en la guarda del lote, en la misma transacción. Nunca se expone en
   contexto funcional, vistas, wizard fields, respuestas RPC, chatter,
   snapshots de auditoría, mensajes de error ni logs.

2. `madenat.sv.internal.marker`
   Marcador técnico exclusivamente de pruebas (test-only). Permite limpiar
   registros creados por pruebas de integración que necesitan confirmar
   transacciones. Solo puede borrar registros previamente marcados con un
   token único.

   El marcador distingue DOS vías de entorno, con consumidores disjuntos:

   * Vía ESTRICTA — `_sv_test_enable_strict()`: exige `--test-enable` real
     **y** base de datos de test. Es la única admitida por los mecanismos que
     tocan el ledger SV (`_sv_test_cleanup_allowed()`, `_sv_test_mark()`,
     `_sv_test_cleanup()`); nunca se relaja por configuración.
   * Vía ALTERNATIVA de desarrollo — `_sv_dev_cleanup_enabled()`:
     `ir.config_parameter('madenat.dev_cleanup_enabled') == 'True'` sobre una
     base de datos de test. Existe para que el «Modo A autoservicio» del
     wizard «Ciclo de vida de la guía» funcione en el servidor de desarrollo
     sin `--test-enable` (que en un servidor persistente ejecuta la suite
     completa de todos los módulos dentro del mismo proceso HTTP).

   `_sv_test_environment_ok()` es la suma de ambas vías y la consumen
   exclusivamente el Modo A autoservicio (vía
   `_lifecycle_dev_environment_ok()`) y las pruebas automatizadas.

   Invariante de las DOS vías: el nombre de la base debe contener 'test'.
"""

import json
import logging
import uuid

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Modelos que el cleanup test-only puede eliminar (en este orden).
SV_TEST_CLEANUP_ORDER = (
    'madenat.sv.operation',
    'stock.move.line',
    'stock.move',
    'stock.picking',
    'stock.quant',
    'stock.lot',
    'madenat.guia.processing',
    'product.product',
    'res.partner',
)

# Parámetro de sistema que habilita la vía ALTERNATIVA de desarrollo
# («Modo A autoservicio» sin `--test-enable`). Solo se lee: nunca lo escribe
# este módulo. Valor admitido: exactamente 'True' (fail-closed: cualquier otro
# valor desactiva la vía). Requiere además que el nombre de la BD contenga
# 'test'.
SV_DEV_CLEANUP_PARAM = 'madenat.dev_cleanup_enabled'


class MadenatSvInternalCapability(models.Model):
    """Capacidad técnica de un solo uso para escrituras protegidas SV."""

    _name = 'madenat.sv.internal.capability'
    _description = 'Capacidad interna de aplicación SV'
    _log_access = False
    _order = 'id desc'

    token = fields.Char(required=True, index=True, readonly=True)
    transaction_token = fields.Char(required=True, index=True, readonly=True)
    operation_id = fields.Many2one(
        'madenat.sv.operation', required=True, ondelete='cascade',
        index=True, readonly=True)
    lot_id = fields.Many2one(
        'stock.lot', required=True, ondelete='cascade', index=True,
        readonly=True)
    actor_uid = fields.Many2one(
        'res.users', required=True, ondelete='cascade', index=True,
        readonly=True,
        help='Identidad funcional original que ejecuta la aplicación.')
    expected_values = fields.Text(readonly=True)
    state = fields.Selection(
        [('prepared', 'Preparada'), ('consumed', 'Consumida')],
        required=True, default='prepared', readonly=True)
    company_id = fields.Many2one(
        'res.company', required=True, readonly=True,
        default=lambda self: self.env.company)

    @api.model
    def _sv_mint(self, operation, actor_uid, expected_values):
        """Acuña la capacidad (uso interno exclusivo; no es API pública)."""
        if not operation or operation.state != 'draft':
            raise UserError(_('La operación SV no está en borrador.'))
        operation.ensure_one()
        capability = self.sudo().create({
            'token': uuid.uuid4().hex,
            'transaction_token': uuid.uuid4().hex,
            'operation_id': operation.id,
            'lot_id': operation.lot_id.id,
            'actor_uid': actor_uid,
            'expected_values': json.dumps(expected_values or {}, sort_keys=True),
            'company_id': operation.company_id.id or self.env.company.id,
        })
        return capability

    @api.model
    def _sv_consume(self, token, transaction_token, lot, actor_uid=None):
        """Consume la capacidad (un solo uso) y devuelve sus datos.

        Valida token, token de transacción y lote. Si `actor_uid` se informa
        (camino funcional normal), también exige que la identidad funcional
        coincida; en el camino interno técnico (escritura de un campo restringido
        por grupo) se omite solo esa comparación y se devuelve el actor original
        para que la autorización se evalúe con su identidad.

        Devuelve `None` si no autoriza.
        """
        if not (token and transaction_token and lot):
            return None
        capability_model = self.sudo()
        domain = [
            ('token', '=', token),
            ('transaction_token', '=', transaction_token),
            ('lot_id', '=', lot.id),
            ('state', '=', 'prepared'),
        ]
        if actor_uid is not None:
            domain.append(('actor_uid', '=', actor_uid))
        capability = capability_model.search(domain, limit=1)
        if not capability:
            return None
        try:
            expected = json.loads(capability.expected_values or '{}')
        except ValueError:
            expected = {}
        data = {
            'actor_uid': capability.actor_uid.id,
            'operation_id': capability.operation_id.id,
            'action_type': expected.get('action_type'),
            'values': expected.get('values') or {},
        }
        capability.unlink()
        return data

    @api.model
    def _sv_discard_for_operation(self, operation):
        """Elimina cualquier capacidad remanente de una operación."""
        if not operation:
            return
        self.sudo().search([
            ('operation_id', '=', operation.id)]).unlink()


class MadenatSvInternalMarker(models.Model):
    """Marcador técnico de pruebas (test-only) para limpieza de datos."""

    _name = 'madenat.sv.internal.marker'
    _description = 'Marcador interno de pruebas SV'
    _log_access = False

    token = fields.Char(required=True, index=True, readonly=True)
    model_name = fields.Char(required=True, index=True, readonly=True)
    res_id = fields.Integer(required=True, index=True, readonly=True)

    # ── Entorno de pruebas ────────────────────────────────────────────────
    @api.model
    def _sv_test_enable_strict(self):
        """Vía ESTRICTA: exige `--test-enable` real **y** BD de test.

        Única vía admitida por los mecanismos que tocan el ledger SV
        (`_sv_test_cleanup_allowed`, `_sv_test_mark`, `_sv_test_cleanup`).
        NUNCA se relaja por `ir.config_parameter`.
        """
        if not odoo.tools.config.get('test_enable'):
            return False
        return 'test' in (self.env.cr.dbname or '').lower()

    @api.model
    def _sv_dev_cleanup_enabled(self):
        """Vía ALTERNATIVA de desarrollo: parámetro de sistema explícito.

        Pensada EXCLUSIVAMENTE para el «Modo A autoservicio» en el servidor de
        desarrollo, sin `--test-enable` (que en un servidor persistente lanza
        la suite completa de todos los módulos dentro del proceso HTTP).

        Exige que el nombre de la BD contenga 'test' — invariante inviolable,
        igual que en la vía estricta — y que `madenat.dev_cleanup_enabled` sea
        exactamente 'True' (fail-closed: `1`, `true`, `yes` o ausente → False).
        """
        if 'test' not in (self.env.cr.dbname or '').lower():
            return False
        return self.env['ir.config_parameter'].sudo().get_param(
            SV_DEV_CLEANUP_PARAM, '') == 'True'

    @api.model
    def _sv_test_environment_ok(self):
        """Entorno de desarrollo: `test_enable` real O parámetro explícito.

        Consumida SOLO por el Modo A autoservicio (vía
        `_lifecycle_dev_environment_ok`) y por las pruebas automatizadas. Los
        mecanismos de limpieza del ledger SV (`_sv_test_cleanup_allowed`,
        `_sv_test_mark`, `_sv_test_cleanup`) usan `_sv_test_enable_strict()`
        directamente y NUNCA esta vía ampliada.
        """
        return self._sv_test_enable_strict() or self._sv_dev_cleanup_enabled()

    @api.model
    def _sv_test_cleanup_allowed(self, model_name, res_ids):
        """True si TODOS los ids están marcados con el token del contexto.

        No existe permiso genérico: sin token, sin entorno de pruebas ESTRICTO
        (`--test-enable` real, nunca el parámetro de desarrollo) o con algún id
        no marcado, la operación queda denegada.
        """
        token = self.env.context.get('madenat_sv_test_cleanup_token')
        if not token or not self._sv_test_enable_strict():
            return False
        ids = list(res_ids or [])
        if not ids or len(set(ids)) != len(ids):
            return False
        marked = self.sudo().search([
            ('token', '=', token),
            ('model_name', '=', model_name),
            ('res_id', 'in', ids),
        ])
        return len(marked) == len(ids)

    # ── API interna test-only (privada: no accesible por RPC) ─────────────
    @api.model
    def _sv_test_mark(self, token, records):
        """Marca registros de prueba con un token único.

        Vía ESTRICTA: `--test-enable` real + BD de test. El parámetro de
        desarrollo (`madenat.dev_cleanup_enabled`) NO habilita este método.
        """
        if not token or not self._sv_test_enable_strict():
            raise UserError(_('Marcador de pruebas no disponible.'))
        marker_model = self.sudo()
        vals_list = []
        for record in records:
            if not record or not record.id:
                continue
            vals_list.append({
                'token': token,
                'model_name': record._name,
                'res_id': record.id,
            })
        if vals_list:
            marker_model.create(vals_list)
        return True

    @api.model
    def _sv_test_cleanup(self, token=None):
        """Elimina los registros marcados (token dado o todos los huérfanos).

        Solo disponible en entorno de pruebas ESTRICTO (`--test-enable` real +
        BD de test): es el mecanismo test-only que evita dejar datos de
        integración persistentes tras confirmar transacciones (imprescindible
        para la prueba de concurrencia real). El parámetro de desarrollo
        (`madenat.dev_cleanup_enabled`) NUNCA habilita el borrado del ledger.
        """
        if not self._sv_test_enable_strict():
            raise UserError(_('Limpieza de pruebas no disponible.'))
        marker_model = self.sudo()
        domain = [('token', '=', token)] if token else []
        markers = marker_model.search(domain)
        removed = 0
        for marker_token in set(markers.mapped('token')):
            removed += self._sv_test_cleanup_token(marker_token)
        return removed

    @api.model
    def _sv_test_cleanup_token(self, marker_token):
        """Elimina un token de marcadores completo (orden seguro)."""
        marker_model = self.sudo()
        markers = marker_model.search([('token', '=', marker_token)])
        if not markers:
            return 0
        cleanup_ctx = {'madenat_sv_test_cleanup_token': marker_token}
        # Bitácora de auditoría derivada: se elimina ANTES de borrar guía/lote
        # (referencia por guía y por nombre de lote en `batch_id`).
        lot_ids = markers.filtered(
            lambda m: m.model_name == 'stock.lot').mapped('res_id')
        lot_names = self.env['stock.lot'].sudo().browse(lot_ids).mapped('name')
        guia_ids = markers.filtered(
            lambda m: m.model_name == 'madenat.guia.processing'
        ).mapped('res_id')
        audit_domain = [('id', '=', 0)]
        if lot_names or guia_ids:
            audit_domain = ['|',
                            ('guia_processing_id', 'in', guia_ids),
                            ('batch_id', 'in', lot_names)]
        audit = self.env['madenat.audit.log'].sudo().search(audit_domain)
        if audit:
            # H3 (FASE 4): la bitácora es APPEND-ONLY; el borrado test-only
            # requiere el token de limpieza (mismo patrón inerte que el resto).
            audit.with_context(**cleanup_ctx).unlink()
        # Operaciones SV DERIVADAS de lotes marcados (el ledger es append-only:
        # solo se eliminan en este contexto test-only).
        if lot_ids:
            derived_ops = self.env['madenat.sv.operation'].sudo().search([
                ('lot_id', 'in', lot_ids)])
            if derived_ops:
                derived_ops.with_context(**cleanup_ctx).unlink()
        removed = 0
        for model_name in SV_TEST_CLEANUP_ORDER:
            ids = markers.filtered(
                lambda m: m.model_name == model_name).mapped('res_id')
            if not ids:
                continue
            records = self.env[model_name].sudo().browse(ids).exists()
            if records:
                # Guías: estado neutro previo para el borrado test-only.
                if model_name == 'madenat.guia.processing':
                    records.with_context(**cleanup_ctx).write(
                        {'state': 'draft'})
                records.with_context(**cleanup_ctx).unlink()
                removed += len(ids)
        marker_model.search([('token', '=', marker_token)]).unlink()
        return removed
