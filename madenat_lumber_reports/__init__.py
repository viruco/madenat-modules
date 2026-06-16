# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Hook ejecutado al instalar o actualizar el módulo.
    Recomputa partner_name en todos los registros existentes de
    lumber.reception.line para garantizar consistencia tras el cambio
    de lógica de proveedor (ahora reception_id.supplier_id, antes purchase_id.partner_id).
    La operación es idempotente y segura para ejecuciones repetidas.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("madenat_lumber_reports: Iniciando recomputación de partner_name...")

    # ── PASO 0: Backfill reception.supplier_id desde purchase_id.partner_id ──
    # Si una recepción tiene purchase_id.partner_id pero no supplier_id,
    # se copia el partner de la OC al supplier_id de la recepción.
    # Esto asegura que partner_name se compute correctamente para líneas huérfanas.
    orphan_receptions = env['lumber.reception'].search([
        ('supplier_id', '=', False),
        ('purchase_id', '!=', False),
    ])
    if orphan_receptions:
        _logger.info(
            "madenat_lumber_reports: Backfill supplier_id desde purchase_id.partner_id "
            "para %d recepciones.", len(orphan_receptions)
        )
        for reception in orphan_receptions:
            if reception.purchase_id.partner_id:
                reception.supplier_id = reception.purchase_id.partner_id

    lines = env['lumber.reception.line'].search([])
    count = len(lines)
    _logger.info("madenat_lumber_reports: %d líneas encontradas para recomputar partner_name.", count)

    if lines:
        # Invocar directamente el método compute que recalcula partner_name
        # desde reception_id.supplier_id
        lines._compute_partner_name()
        _logger.info("madenat_lumber_reports: Recomputation de partner_name completada para %d líneas.", count)
    else:
        _logger.info("madenat_lumber_reports: No hay líneas para recomputar.")

    env.cr.commit()


from . import models