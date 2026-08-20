# -*- coding: utf-8 -*-
"""Wizard (TransientModel) para vincular una Orden de Compra a Producto.

Aísla en madenat_lumber_intake la resolución manual de OC de la fachada de
Producto. No crea purchase.order, no toca stock/lotes/pickings/volúmenes ni
inventario: solo escribe `purchase_id` y los campos de estado/nota de OC del
contrato canónico de lumber.reception, mediante ORM.

Reutiliza (no replica) la semántica de matching ya existente:
  - el vínculo operativo real es `lumber.reception.purchase_id`;
  - la referencia documental `oc_reference_raw` NUNCA se sobrescribe;
  - el estado se resuelve a `manual` con nota de trazabilidad del decisor.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MadenatLumberIntakePoLink(models.TransientModel):
    _name = 'madenat.lumber.intake.po.link'
    _description = 'Vincular Orden de Compra (Producto)'

    reception_id = fields.Many2one(
        'lumber.reception',
        string='Recepción',
        readonly=True,
        required=True,
    )

    # Snapshot readonly de contexto OC para auditoría del decisor.
    oc_reference_raw = fields.Char(
        string='Referencia OC del documento',
        readonly=True,
    )
    manual_po_name = fields.Char(
        string='Referencia manual',
        readonly=True,
    )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        readonly=True,
    )

    # Selección editable de una OC existente. Filtrada por proveedor cuando
    # existe, replicando el dominio canónico de lumber.reception.purchase_id.
    purchase_id = fields.Many2one(
        'purchase.order',
        string='Orden de compra asociada',
        domain="[('partner_id', '=', supplier_id), ('state', 'in', ['draft', 'sent', 'purchase', 'done'])]",
        help='Seleccione la Orden de Compra existente a vincular. No se creará '
             'una OC nueva desde aquí.',
    )

    @api.model
    def default_get(self, fields_list):
        """Inicializa el wizard con el contexto OC real de la recepción origen."""
        res = super().default_get(fields_list)
        reception_id = self.env.context.get('default_reception_id')
        if reception_id:
            rec = self.env['lumber.reception'].browse(reception_id).exists()
            if rec:
                res.update({
                    'reception_id': rec.id,
                    'oc_reference_raw': rec.oc_reference_raw,
                    'manual_po_name': rec.manual_po_name,
                    'supplier_id': rec.supplier_id.id,
                    'purchase_id': rec.purchase_id.id,
                })
        return res

    def action_confirm_link(self):
        """Vincula la OC seleccionada a la recepción, con validación server-side.

        La barrera definitiva de seguridad vive aquí (no en el dominio XML):
        antes de escribir purchase_id se valida proveedor, proveedor comercial,
        compañía, estado de la OC y estado de la recepción. No se asocia una OC
        solo por compartir referencia textual o por ser seleccionada.
        """
        self.ensure_one()
        rec = self.reception_id
        if not rec:
            raise UserError(_('No se resolvió la recepción a vincular.'))

        # 6. Recepción en estado permitido (preliminar, sin avance real).
        if rec.state in ('done', 'cancel', 'error'):
            raise UserError(
                _('Solo se puede vincular la OC en un estado preliminar '
                  '(Borrador, Procesando o Verificado).')
            )
        if rec.lot_ids or rec.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede modificarse '
                  'retroactivamente desde Ingreso Global.')
            )

        # 7. No sobrescritura silenciosa de una OC ya vinculada.
        if rec.purchase_id:
            raise UserError(
                _('Esta recepción ya tiene una Orden de Compra vinculada '
                  '(%(current)s). No se reemplaza de forma automática. '
                  'Desvincule la OC mediante una operación trazable antes de '
                  'vincular una diferente.')
                % {'current': rec.purchase_id.name}
            )

        po = self.purchase_id
        if not po:
            raise UserError(_('Seleccione una Orden de Compra para vincular.'))

        # 1. Proveedor de la recepción obligatorio.
        if not rec.supplier_id:
            raise UserError(
                _('Primero debe validar o corregir el proveedor de la recepción '
                  'antes de vincular una Orden de Compra.')
            )

        # 2. La OC debe tener proveedor.
        if not po.partner_id:
            raise UserError(
                _('La Orden de Compra %(po)s no tiene proveedor. No puede '
                  'vincularse.') % {'po': po.name}
            )

        # 3. Coincidencia de proveedor comercial (soporta matriz/sucursal).
        commercial_supplier = rec.supplier_id.commercial_partner_id
        commercial_po = po.partner_id.commercial_partner_id
        if commercial_supplier and commercial_po and commercial_supplier.id != commercial_po.id:
            raise UserError(
                _('La Orden de Compra seleccionada pertenece a un proveedor '
                  'distinto al de esta recepción.\n'
                  'OC: %(po)s (%(po_partner)s)\n'
                  'Recepción: %(supplier)s.') % {
                    'po': po.name,
                    'po_partner': po.partner_id.display_name,
                    'supplier': rec.supplier_id.display_name,
                }
            )

        # 4. Compañía (compatible single-company, sin hardcodear).
        po_company = po.company_id
        active_company = self.env.company
        if po_company and active_company and po_company.id != active_company.id:
            raise UserError(
                _('La Orden de Compra %(po)s pertenece a otra compañía.') %
                {'po': po.name}
            )

        # 5. Estado permitido de la OC (rechaza canceladas/archivadas).
        if po.state not in ('draft', 'sent', 'purchase', 'done'):
            raise UserError(
                _('La Orden de Compra %(po)s está en un estado no válido '
                  'para vincularse.') % {'po': po.name}
            )
        if 'active' in po._fields and not po.active:
            raise UserError(
                _('La Orden de Compra %(po)s está archivada y no puede '
                  'vincularse.') % {'po': po.name}
            )

        # Escritura mínima por ORM: vínculo + estado/nota de OC. No se altera
        # oc_reference_raw, manual_po_name, stock ni volúmenes.
        note = _('Vinculado manualmente a %(po)s desde Ingreso Global. '
                 'Referencia documental: %(ref)s') % {
            'po': po.name,
            'ref': rec.oc_reference_raw or '(sin referencia documental)',
        }
        rec.write({
            'purchase_id': po.id,
            'oc_match_status': 'manual',
            'oc_match_note': note,
        })
        rec.message_post(
            body=_('Orden de Compra vinculada manualmente: %(po)s\n'
                   'Proveedor validado: %(supplier)s\n'
                   'Origen: vinculación manual desde Intake (Producto).') % {
                'po': po.name,
                'supplier': rec.supplier_id.display_name,
            },
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}
