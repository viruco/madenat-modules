# -*- coding: utf-8 -*-
"""Wizard (TransientModel) para validar/corregir el proveedor de Producto.

Aísla en madenat_lumber_intake la corrección manual del proveedor. NO duplica
la identificación por RUT ni la creación automática de partner que ya hace el
core en el procesamiento de la Guía; solo permite seleccionar un partner
existente cuando hay ambigüedad o inconsistencia.

No crea partners, no toca stock/lotes/pickings/volúmenes ni inventario: solo
escribe `supplier_id` (vínculo operativo canónico) mediante ORM.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MadenatLumberIntakeSupplierLink(models.TransientModel):
    _name = 'madenat.lumber.intake.supplier.link'
    _description = 'Validar / corregir proveedor (Producto)'

    reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción',
        readonly=True,
        required=True,
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
        """Inicializa el wizard con el proveedor actual de la recepción."""
        res = super().default_get(fields_list)
        reception_id = self.env.context.get('default_reception_id')
        if reception_id:
            rec = self.env['lumber.reception'].browse(reception_id).exists()
            if rec:
                res.update({
                    'reception_id': rec.id,
                    'supplier_id': rec.supplier_id.id,
                })
        return res

    def action_confirm_link(self):
        """Asigna el proveedor elegido a la recepción (solo `supplier_id`)."""
        self.ensure_one()
        rec = self.reception_id
        if not rec:
            raise UserError(_('No se resolvió la recepción a corregir.'))

        if rec.state in ('done', 'cancel', 'error'):
            raise UserError(
                _('Solo se puede corregir el proveedor en un estado preliminar '
                  '(Borrador, Procesando o Verificado).')
            )
        if rec.lot_ids or rec.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede modificarse '
                  'retroactivamente desde Ingreso Global.')
            )
        if not self.supplier_id:
            raise UserError(_('Seleccione un proveedor.'))

        rec.write({'supplier_id': self.supplier_id.id})
        rec.message_post(
            body=_('Proveedor actualizado manualmente: %s') % self.supplier_id.display_name,
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}