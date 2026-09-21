# -*- coding: utf-8 -*-
"""Wizard (TransientModel) para reclasificar el tipo de ingreso (AD-73).

Corrige una clasificación errónea de tipo_ingreso ANTES de Gate 3: elimina el
destino mal clasificado (lumber.reception o madenat.guia.processing), registra
evidencia en madenat.audit.log, y reabre un wizard de ingesta nuevo en draft con
el tipo correcto. Es una vía ligera y pre-Gate-3; NO reemplaza action_force_cancel
ni action_cancel (cancelaciones pesadas post-Gate-3).

Orquesta (unlink + audit_log + reabrir wizard de intake), sin reimplementar Gates
ni crear un segundo camino de escritura a stock.lot.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MadenatLumberIntakeReclassifyWizard(models.TransientModel):
    _name = 'madenat.lumber.intake.reclassify.wizard'
    _description = 'Reclasificar Tipo de Ingreso'

    source_model = fields.Char(string='Modelo Origen', readonly=True, required=True)
    source_res_id = fields.Integer(string='ID Origen', readonly=True, required=True)

    # Snapshot readonly del origen, para no reclasificar a ciegas.
    source_display_name = fields.Char(string='Registro a eliminar', readonly=True)
    source_create_date = fields.Datetime(string='Fecha de creación', readonly=True)

    tipo_ingreso_correcto = fields.Selection(
        [('producto', 'Madera bruta / compra'),
         ('procesado', 'Madera procesada / servicio'),
         ('granel', 'Madera a granel / volumen total')],
        string='Tipo de ingreso correcto',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        model = self.env.context.get('default_source_model')
        res_id = self.env.context.get('default_source_res_id')
        if model and res_id:
            Model = self.env.get(model)
            src = Model.browse(res_id).exists() if Model else Model
            if src:
                res.update({
                    'source_model': model,
                    'source_res_id': src.id,
                    'source_display_name': src.display_name or src.name or '',
                    'source_create_date': src.create_date,
                })
        return res

    def _get_source(self):
        if not self.source_model or not self.source_res_id:
            raise UserError(_('No se resolvió el registro a reclasificar.'))
        Model = self.env.get(self.source_model)
        if Model is None:
            raise UserError(_('Modelo origen desconocido: %s') % self.source_model)
        src = Model.browse(self.source_res_id).exists()
        if not src:
            raise UserError(_('El registro origen ya no existe.'))
        return src

    def _check_eligible(self, src):
        """Guardia de elegibilidad: solo antes de Gate 3."""
        if src._name == 'madenat.guia.processing':
            if src.state not in ('draft', 'verified'):
                raise UserError(
                    _('La guía ya pasó Gate 3 (estado "%s") y no puede reclasificarse '
                      'por esta vía. Use la cancelación formal (action_force_cancel).')
                    % src.state)
        elif src._name == 'lumber.reception':
            if src.state not in ('draft', 'processing', 'verified'):
                raise UserError(
                    _('La recepción ya pasó Gate 3 (estado "%s") y no puede '
                      'reclasificarse por esta vía. Use la cancelación formal '
                      '(action_cancel).') % src.state)
        else:
            raise UserError(_('Modelo no soportado para reclasificación: %s') % src._name)

    def _check_no_lots(self, src):
        """Defensa en profundidad: sin stock.lot vinculado, aunque el state sea pre-Gate-3."""
        has_lots = bool(src.lot_ids)
        if src._name == 'madenat.guia.processing':
            has_lots = has_lots or bool(src.source_lot_ids)
        if has_lots:
            raise UserError(
                _('El registro ya tiene lotes de inventario vinculados y no puede '
                  'reclasificarse por esta vía.'))

    def _old_tipo_label(self, src):
        if src._name == 'lumber.reception':
            return 'producto'
        if src._name == 'madenat.guia.processing':
            return 'granel' if src.tipo_recepcion == 'granel' else 'procesado'
        return 'desconocido'

    def _audit_vals(self, src, old_tipo):
        description = (
            "Reclasificación de Tipo de Ingreso (AD-73).\n"
            "Registro eliminado: %s (%s)\n"
            "Tipo incorrecto original: %s\n"
            "Tipo correcto elegido: %s"
        ) % (src.display_name or src.name, src._name, old_tipo, self.tipo_ingreso_correcto)

        vals = {
            'action_type': 'reclassification',
            'description': description,
            'user_id': self.env.user.id,
        }
        if src._name == 'lumber.reception':
            vals['reception_id'] = src.id
        else:
            vals['guia_processing_id'] = src.id
        return vals

    def action_confirm_reclassify(self):
        self.ensure_one()
        src = self._get_source()

        # Re-validar guardia y defensa en profundidad (el estado pudo cambiar).
        self._check_eligible(src)
        self._check_no_lots(src)

        if not self.tipo_ingreso_correcto:
            raise UserError(_('Seleccione el tipo de ingreso correcto.'))

        old_tipo = self._old_tipo_label(src)

        # Auditoría ANTES del unlink: el origen debe existir para popular la FK.
        self.env['madenat.audit.log'].sudo().create(self._audit_vals(src, old_tipo))

        src.with_context(
            madenat_reclassify_allow_verified_unlink=True
        ).unlink()

        new_wizard = self.env['madenat.lumber.intake.wizard'].create({
            'tipo_ingreso': self.tipo_ingreso_correcto,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reclasificar Tipo de Ingreso'),
            'res_model': 'madenat.lumber.intake.wizard',
            'res_id': new_wizard.id,
            'view_mode': 'form',
            'target': 'current',
        }
