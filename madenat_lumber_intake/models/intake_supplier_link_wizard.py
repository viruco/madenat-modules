# -*- coding: utf-8 -*-
"""Wizard (TransientModel) para validar/corregir el proveedor (Producto/Volúmenes).

Aísla en madenat_lumber_intake la corrección manual del proveedor. NO duplica
la identificación por RUT ni la creación automática de partner que ya hace el
core en el procesamiento de la Guía; solo permite seleccionar un partner
existente cuando hay ambigüedad o inconsistencia.

No crea partners, no toca stock/lotes/pickings/volúmenes ni inventario: solo
escribe el vínculo canónico (`supplier_id` en Producto o `partner_id` en
Volúmenes) mediante ORM.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MadenatLumberIntakeSupplierLink(models.TransientModel):
    _name = 'madenat.lumber.intake.supplier.link'
    _description = 'Validar / corregir proveedor'

    reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción',
        readonly=True,
    )

    guia_id = fields.Many2one(
        'madenat.guia.processing',
        string='Guía',
        readonly=True,
    )

    supplier_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        domain="['|', ('is_company', '=', True), ('parent_id', '!=', False)]",
        help='Seleccione el proveedor correcto. No se creará un partner nuevo '
             'desde aquí; si el proveedor no existe, reprocese el documento en '
             'Borrador para que el flujo canónico lo registre.',
    )

    @api.model
    def default_get(self, fields_list):
        """Inicializa el wizard con el proveedor actual del registro origen."""
        res = super().default_get(fields_list)
        reception_id = self.env.context.get('default_reception_id')
        if reception_id:
            rec = self.env['lumber.reception'].browse(reception_id).exists()
            if rec:
                res.update({
                    'reception_id': rec.id,
                    'supplier_id': rec.supplier_id.id,
                })
        guia_id = self.env.context.get('default_guia_id')
        if guia_id:
            guia = self.env['madenat.guia.processing'].browse(guia_id).exists()
            if guia:
                res.update({
                    'guia_id': guia.id,
                    'supplier_id': guia.partner_id.id,
                })
        return res

    def action_confirm_link(self):
        """Asigna el proveedor elegido al registro origen."""
        self.ensure_one()
        if not self.supplier_id:
            raise UserError(_('Seleccione un proveedor.'))

        if self.guia_id:
            return self._link_guia()
        if self.reception_id:
            return self._link_reception()
        raise UserError(_('No se resolvió el registro a corregir.'))

    def _link_reception(self):
        """Vincula el proveedor a una recepción de Producto (supplier_id)."""
        rec = self.reception_id
        if rec.state in ('done', 'cancel', 'error'):
            raise UserError(
                _('Solo se puede corregir el proveedor en un estado preliminar '
                  '(Borrador, Procesando o Verificado).')
            )
        if rec.lot_ids or rec.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede modificarse '
                  'retroactivamente desde Ingreso de Madera.')
            )
        rec.write({'supplier_id': self.supplier_id.id})
        rec.message_post(
            body=_('Proveedor actualizado manualmente: %s')
            % self.supplier_id.display_name,
            message_type='notification',
        )
        return {'type': 'ir.actions.act_window_close'}

    def _link_guia(self):
        """Vincula el proveedor a una guía de Volúmenes (partner_id)."""
        guia = self.guia_id
        if guia.state in ('validated', 'cancelled'):
            raise UserError(
                _('Solo se puede asignar el proveedor en un estado preliminar '
                  '(Verificado).')
            )
        guia.write({
            'partner_id': self.supplier_id.id,
            'supplier_resolution_status': 'resolved_manual',
            'supplier_resolution_note': (
                'Proveedor asignado manualmente: %s.'
                % self.supplier_id.display_name
            ),
        })
        guia.message_post(
            body=_('Proveedor asignado manualmente: %s')
            % self.supplier_id.display_name,
            message_type='notification',
        )
        return {'type': 'ir.actions.act_window_close'}