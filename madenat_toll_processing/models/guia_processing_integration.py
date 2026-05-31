# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MadenatGuiaProcessing(models.Model):
    _inherit = 'madenat.guia.processing'

    # =========================================================================
    # 1) CONEXIÓN CON ORDEN DE PROCESAMIENTO (Toll Processing)
    # =========================================================================
    toll_order_id = fields.Many2one(
        'toll.processing.order',
        string='Orden de Procesamiento (Origen)',
        domain="[('processor_id', '=', partner_id), ('state', '=', 'in_process')]",
        help="Si esta guía es el retorno de un servicio, selecciona la orden de origen aquí."
    )

    # =========================================================================
    # 2) AUTOMATIZACIÓN DE CAMPOS SEGÚN ORDEN TOLL
    # =========================================================================
    @api.onchange('toll_order_id')
    def _onchange_toll_order(self):
        """
        Al seleccionar una orden de procesamiento:
        1. Cambia el tipo de guía a 'servicio' (retorno de maquila).
        2. Asigna automáticamente el proveedor (procesador).
        """
        if self.toll_order_id:
            self.tipo_recepcion = 'servicio'
            self.partner_id = self.toll_order_id.processor_id

    # =========================================================================
    # 3) HERENCIA DE COSTOS DESDE LOTES ORIGEN HACIA LOTES PROCESADOS
    # =========================================================================
    def _inherit_costs_from_source(self):
        """
        Transfiere el costo de los lotes de origen (materia prima) a los nuevos
        lotes procesados de la guía.

        REGLA:
        - Se toma el costo total de los lotes origen (total_cost_usd).
        - Se distribuye 100% de ese valor sobre los lotes de retorno (self.lot_ids)
          proporcionalmente a su volumen_m3.
        - Se guarda como líneas de costo 'wood' en stock.lot.cost.line.
        """
        CostLine = self.env['stock.lot.cost.line']

        for rec in self:
            if not rec.toll_order_id or not rec.lot_ids:
                continue

            source_lots = rec.toll_order_id.source_lot_ids
            if not source_lots:
                _logger.warning(
                    "Orden Toll %s no tiene lotes de origen para heredar costos.",
                    rec.toll_order_id.name
                )
                continue

            # 1) Valor total a heredar (madera + logística previa, etc.)
            #    Usamos total_cost_usd, que ya contempla wood/logistic/process/other.
            total_source_value = sum(source_lots.mapped('total_cost_usd'))
            if total_source_value <= 0:
                _logger.info(
                    "Lotes origen de Orden Toll %s tienen costo total 0. Nada que heredar.",
                    rec.toll_order_id.name
                )
                continue

            # 2) Volumen total de retorno (solo lotes válidos con volumen)
            return_lots = rec.lot_ids.filtered(lambda l: l.volumen_m3 > 0)
            total_return_vol = sum(return_lots.mapped('volumen_m3'))
            if total_return_vol <= 0:
                _logger.warning(
                    "Guía %s (Orden Toll %s) no tiene volumen de retorno válido.",
                    rec.name,
                    rec.toll_order_id.name
                )
                continue

            _logger.info(
                "💰 Heredando costos Toll: Orden %s | Valor Origen=%.2f USD | Vol Retorno=%.3f m3",
                rec.toll_order_id.name,
                total_source_value,
                total_return_vol,
            )

            # 3) Distribuir costo a cada lote procesado
            for lot in return_lots:
                factor = lot.volumen_m3 / total_return_vol
                allocated_cost = total_source_value * factor

                CostLine.create({
                    'lot_id': lot.id,
                    'name': _("Costo Heredado Orden %s") % rec.toll_order_id.name,
                    'cost_type': 'wood',              # se suma al costo madera
                    'amount_usd': allocated_cost,
                    'partner_id': rec.toll_order_id.processor_id.id,
                    'date': fields.Date.context_today(self),
                    'notes': _(
                        "Costo heredado desde %s lotes origen de la Orden Toll %s."
                    ) % (len(source_lots), rec.toll_order_id.name),
                })

            # Nota: el compute de total_cost_usd en stock.lot se encarga de sumar
            # estas líneas recién creadas; no llamamos manualmente al compute.

    # =========================================================================
    # 4) EXTENSIÓN DE VALIDACIÓN DE GUÍA PROCESADA
    # =========================================================================
    def action_validate(self):
        """
        Extiende la validación original para:
        1. Ejecutar la lógica estándar (creación de recepción y lotes).
        2. Actualizar la Toll Order (volumen de retorno, yield, chatter).
        3. Disparar el consumo de materia prima (si aún no se hizo).
        4. Heredar costos desde lotes origen a lotes procesados.
        """
        # 1) Lógica original: crea recepción, lotes, etc.
        res = super(MadenatGuiaProcessing, self).action_validate()

        # 2) Integración con Orden Toll
        for rec in self:
            if not rec.toll_order_id:
                continue

            toll_order = rec.toll_order_id

            # A) Recalcular volumen de retorno e indicadores
            toll_order._compute_return_volume()
            toll_order._compute_actual_yield()

            # B) Log en el chatter de la orden Toll
            toll_order.message_post(
                body=_(
                    "📦 Retorno registrado: Guía %s procesada con %.3f m³ físico."
                ) % (rec.name, rec.vol_fisico or 0.0),
                subject=_("Material Retornado"),
            )

            # C) Cierre de ciclo físico: consumo de materia prima
            if not toll_order.consumption_picking_id:
                _logger.info(
                    "🚀 Disparando consumo de materia prima para Orden Toll %s desde Guía %s",
                    toll_order.name, rec.name
                )
                toll_order._create_consumption_picking()
            else:
                _logger.info(
                    "ℹ️ Materia prima ya consumida previamente para Orden Toll %s",
                    toll_order.name
                )

        # 3) Cierre de ciclo de COSTOS: herencia de costos de lotes origen → lotes procesados
        self._inherit_costs_from_source()

        return res
