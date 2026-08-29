# -*- coding: utf-8 -*-
"""Extensiones de lumber.reception desde madenat_lumber_intake (aisladas del core).

No modifica archivos de madenat_lumber_core. Aporta:
  - `cancel_reason`: motivo obligatorio de cancelación (trazabilidad, sin
    impacto en stock ni volúmenes).
  - `action_reopen_cancelled_intake`: reapertura controlada de un registro
    cancelado y aún preliminar hacia `draft`, para releer Guía/Packing sobre
    el mismo origen (sin duplicar `name`, sin SQL, sin tocar stock).
  - `action_back_to_intake_console`: retorno a la consola principal.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LumberReceptionIntake(models.Model):
    _inherit = 'lumber.reception'

    # Motivo de cancelación (obligatorio al cancelar un preliminar de Producto).
    # Campo informativo/trazable: no participa en stock, lotes, volúmenes ni costos.
    cancel_reason = fields.Text(
        string='Motivo de cancelación',
        help='Motivo registrado al cancelar el ingreso preliminar. No afecta stock ni volúmenes.',
    )

    # Advertencia NO bloqueante de "OC pendiente" (solo presentación).
    # Reutiliza campos canónicos (purchase_id, oc_reference_raw, manual_po_name,
    # oc_match_status) sin duplicar matching ni crear estados nuevos. No escribe stock.
    oc_pending_alert = fields.Html(
        string='Alerta OC pendiente',
        compute='_compute_oc_pending_alert',
        sanitize=False,
        help='Bloque visual persistente mientras la recepción preliminar no tenga '
             'una Orden de Compra vinculada. Informativo: no bloquea el ingreso.',
    )

    # Advertencia NO bloqueante de "proveedor pendiente" (solo presentación).
    # Reutiliza el contrato canónico (supplier_id). No duplica la identificación
    # por RUT ni la creación de partner del core: solo expone el resultado.
    supplier_pending_alert = fields.Html(
        string='Alerta proveedor pendiente',
        compute='_compute_supplier_pending_alert',
        sanitize=False,
        help='Bloque visual persistente mientras la recepción preliminar no '
             'tenga un proveedor validado. Informativo: no bloquea el ingreso.',
    )

    @api.depends('supplier_id', 'state')
    def _compute_supplier_pending_alert(self):
        for rec in self:
            if rec.supplier_id or rec.state in ('done', 'cancel', 'error'):
                rec.supplier_pending_alert = False
                continue
            rec.supplier_pending_alert = (
                '<div class="alert alert-warning" role="alert" style="margin: 8px 0;">'
                '<i class="fa fa-exclamation-triangle"/> '
                '<strong>Proveedor pendiente de validación.</strong><br/>'
                'No se ha detectado o seleccionado un proveedor. El ingreso puede '
                'continuar, pero debe completarse para la trazabilidad operativa.'
                '</div>'
            )

    @api.depends('purchase_id', 'oc_reference_raw', 'manual_po_name',
                 'oc_match_status', 'state')
    def _compute_oc_pending_alert(self):
        for rec in self:
            if rec.purchase_id or rec.state in ('done', 'cancel', 'error'):
                rec.oc_pending_alert = False
                continue

            if rec.oc_match_status == 'multi_match':
                rec.oc_pending_alert = (
                    '<div class="alert alert-warning" role="alert" style="margin: 8px 0;">'
                    '<i class="fa fa-exclamation-triangle"/> '
                    '<strong>Orden de Compra pendiente de vinculación.</strong><br/>'
                    'Se encontraron <b>varias</b> órdenes de compra coincidentes. '
                    'Debe resolverse manualmente para elegir la correcta.'
                    '</div>'
                )
            elif rec.oc_reference_raw:
                rec.oc_pending_alert = (
                    '<div class="alert alert-warning" role="alert" style="margin: 8px 0;">'
                    '<i class="fa fa-exclamation-triangle"/> '
                    '<strong>Orden de Compra pendiente de vinculación.</strong><br/>'
                    'Se detectó la referencia documental '
                    '<b>%(ref)s</b>, pero aún no existe una OC asociada.<br/>'
                    'El ingreso puede continuar; la OC debe resolverse posteriormente '
                    'para el control comercial.'
                    '</div>' % {'ref': rec.oc_reference_raw}
                )
            elif rec.manual_po_name:
                rec.oc_pending_alert = (
                    '<div class="alert alert-warning" role="alert" style="margin: 8px 0;">'
                    '<i class="fa fa-exclamation-triangle"/> '
                    '<strong>Orden de Compra pendiente de vinculación.</strong><br/>'
                    'Solo existe una <b>referencia manual</b> (%(ref)s), no una compra '
                    'real asociada. El ingreso puede continuar; la OC debe resolverse '
                    'posteriormente.'
                    '</div>' % {'ref': rec.manual_po_name}
                )
            else:
                rec.oc_pending_alert = (
                    '<div class="alert alert-warning" role="alert" style="margin: 8px 0;">'
                    '<i class="fa fa-exclamation-triangle"/> '
                    '<strong>Orden de Compra pendiente de vinculación.</strong><br/>'
                    'No se detectó una Orden de Compra ni una referencia manual. '
                    'El ingreso puede continuar; complete la OC posteriormente.'
                    '</div>'
                )

    # ------------------------------------------------------------------
    # Validaciones compartidas de cancelación / reapertura
    # ------------------------------------------------------------------
    def _has_intake_stock_advance(self):
        """True si el ingreso ya avanzó a stock (finalizado, lotes o picking).

        Condición compartida entre el flujo directo de lumber.reception y la
        consola. No escribe ni lanza: cada llamador conserva su mensaje
        'UserError' (flujo directo 'cancelar', consola 'reiniciar').
        """
        self.ensure_one()
        return bool(self.state == 'done' or self.lot_ids or self.picking_id)

    def _check_intake_can_be_cancelled(self):
        """Valida precondiciones de cancelación (sin escribir ni abrir wizard).

        Centraliza SOLO la guarda con mensaje idéntico entre rutas. La guarda
        de avance (`_has_intake_stock_advance`) se evalúa en el llamador para
        preservar el texto visible actual de cada flujo.
        """
        self.ensure_one()
        if self.state == 'cancel':
            raise UserError(_('El ingreso ya se encuentra cancelado.'))

    def _check_intake_can_be_reopened(self):
        """Valida que el ingreso cancelado pueda reabrirse (sin escribir)."""
        self.ensure_one()
        if self.state != 'cancel':
            raise UserError(_('Solo se puede reabrir un registro en estado "Cancelado".'))
        if self._has_intake_stock_advance():
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede reabrirse de forma preliminar.')
            )

    def action_reopen_cancelled_intake(self):
        """Reabre un registro cancelado y aún preliminar a `draft`.

        Reglas:
          - solo aplica a state='cancel';
          - bloquea si existe avance real (lotes, picking o done);
          - NO limpia stock (no debe existir en preliminar);
          - preserva el motivo de cancelación previo y deja rastro en chatter.
        Devuelve la fachada de Producto en estado draft para releer documentos.
        """
        self.ensure_one()
        self._check_intake_can_be_reopened()

        prev_reason = self.cancel_reason or _('(sin motivo registrado)')
        self.write({'state': 'draft'})
        self.message_post(
            body=_('Reabierto a Borrador desde Ingreso de Madera. Motivo de cancelación previo: %s')
            % prev_reason,
            message_type='notification',
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.reception',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'madenat_lumber_intake.view_lumber_reception_intake_facade_form'
            ).id,
            'target': 'current',
        }

    def action_back_to_intake_console(self):
        """Vuelve a Ingreso de Madera reemplazando la vista actual (client action).

        Espejo de madenat.guia.processing.action_back_to_intake_console: evita
        breadcrumbs duplicados y apilamiento de navegación en el ciclo.
        Producto (lumber.reception) usa id de consola SIN offset (regla vista SQL).
        """
        self.ensure_one()
        console_form_view = self.env.ref(
            'madenat_lumber_intake.view_madenat_lumber_intake_console_form')
        inner = {
            'type': 'ir.actions.act_window',
            'res_model': 'madenat.lumber.intake.console',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': console_form_view.id,
            'views': [(console_form_view.id, 'form')],
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'madenat_lumber_intake.replace_current_action',
            'params': {'action_to_execute': inner},
        }

    def action_cancel_intake(self):
        """Abre el wizard de cancelación con motivo obligatorio."""
        self.ensure_one()
        if self._has_intake_stock_advance():
            raise UserError(
                _('El ingreso ya avanzó (enviado a stock). No se puede '
                  'cancelar de forma preliminar.')
            )
        self._check_intake_can_be_cancelled()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Motivo de cancelación'),
            'res_model': 'madenat.lumber.intake.cancel',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }

    def action_resolve_supplier(self):
        """Abre el wizard de validación/corrección manual del proveedor.

        - Solo aplica a registros preliminares (draft/processing/verified).
        - Bloquea si el ingreso ya avanzó a stock (done, lot_ids o picking_id).
        - No crea partners: solo permite seleccionar uno existente. La creación
          automática por RUT ya la cubre el flujo canónico de la Guía.
        """
        self.ensure_one()
        if self.state in ('done', 'cancel', 'error'):
            raise UserError(
                _('Solo se puede corregir el proveedor en un estado preliminar '
                  '(Borrador, Procesando o Verificado).')
            )
        if self.lot_ids or self.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede modificarse '
                  'retroactivamente desde Ingreso de Madera.')
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Validar / corregir proveedor'),
            'res_model': 'madenat.lumber.intake.supplier.link',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }

    def action_resolve_oc(self):
        """Abre el wizard de resolución manual de OC desde la fachada de Producto.

        - Solo aplica a registros preliminares (draft/processing/verified).
        - Bloquea si el ingreso ya avanzó a stock (done, lot_ids o picking_id).
        - No crea ni vincula nada aquí: la escritura queda en el wizard, que
          reutiliza purchase_id/oc_match_status del contrato canónico.
        """
        self.ensure_one()
        if self.state in ('done', 'cancel', 'error'):
            raise UserError(
                _('Solo se puede resolver la OC en un estado preliminar '
                  '(Borrador, Procesando o Verificado).')
            )
        if self.lot_ids or self.picking_id:
            raise UserError(
                _('El ingreso ya avanzó a stock y no puede modificarse '
                  'retroactivamente desde Ingreso de Madera.')
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Resolver Orden de Compra'),
            'res_model': 'madenat.lumber.intake.po.link',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }
