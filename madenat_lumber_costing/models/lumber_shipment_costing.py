# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class LumberExportShipmentCosting(models.Model):
    """
    Extensión ligera de lumber.export.shipment desde el módulo de Costeo.

    REGLA DE ORO:
    - El dueño de la lógica de costeo y distribución de costos de embarque
      es madenat_lumber_logistics.
    - Este módulo NO reimplementa action_distribute_costs; solo delega
      a la implementación principal para mantener compatibilidad.
    """
    _inherit = 'lumber.export.shipment'

    def action_distribute_costs(self):
        """
        Delegar la distribución de costos al dueño real (logística).

        Cualquier llamada a este método desde el módulo de Costeo pasará
        directamente a la lógica central definida en madenat_lumber_logistics,
        que ya usa:
        - total_shipment_costs_usd / totalshipmentcostsusd
        - volumen total del embarque
        - distribución proporcional a los lotes del embarque.
        """
        _logger.info(
            "Delegando action_distribute_costs desde madenat_lumber_costing "
            "a la implementación principal de logística para embarques: %s",
            ", ".join(self.mapped("name")),
        )
        return super().action_distribute_costs()
