# -*- coding: utf-8 -*-
"""
MIGRATION 18.0.2.2.0 → pre-migrate

Backfill reception.supplier_id desde purchase_id.partner_id para todas las
recepciones que tienen OC asignada pero supplier_id vacío.

Corrige la causa raíz de "Sin Proveedor" en R5/R6: partner_name depende de
reception_id.supplier_id, y si éste es NULL, el compute produce "Sin Proveedor"
aunque purchase_id.partner_id sí exista.

Luego de este backfill, el post_init_hook (que se ejecuta en install) ya no
es una dependencia — las nuevas instalaciones usan post_init_hook, los upgrades
existentes usan este script.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("madenat_lumber_reports [18.0.2.2.0]: Iniciando backfill de supplier_id...")

    # ── PASO 0: Backfill reception.supplier_id desde purchase_id.partner_id ──
    cr.execute("""
        UPDATE lumber_reception
        SET supplier_id = purchase_order.partner_id
        FROM purchase_order
        WHERE lumber_reception.purchase_id = purchase_order.id
          AND lumber_reception.supplier_id IS NULL
          AND purchase_order.partner_id IS NOT NULL
    """)
    backfilled = cr.rowcount
    _logger.info(
        "madenat_lumber_reports [18.0.2.2.0]: Backfill supplier_id completado para %d recepciones.",
        backfilled,
    )

    # ── PASO 1: Recomputar partner_name en lumber.reception.line ──
    cr.execute("""
        UPDATE lumber_reception_line
        SET partner_name = res_partner.name
        FROM lumber_reception
        JOIN res_partner ON lumber_reception.supplier_id = res_partner.id
        WHERE lumber_reception_line.reception_id = lumber_reception.id
          AND lumber_reception.supplier_id IS NOT NULL
    """)
    recomputed = cr.rowcount
    _logger.info(
        "madenat_lumber_reports [18.0.2.2.0]: Recomputation partner_name completada para %d lineas.",
        recomputed,
    )

    # ── PASO 2: Registrar líneas realmente huérfanas (sin supplier_id posible) ──
    cr.execute("""
        SELECT COUNT(*) FROM lumber_reception_line lrl
        JOIN lumber_reception lr ON lrl.reception_id = lr.id
        WHERE lr.supplier_id IS NULL
    """)
    orphan_count = cr.fetchone()[0]
    if orphan_count > 0:
        _logger.info(
            "madenat_lumber_reports [18.0.2.2.0]: %d lineas permanecen como 'Sin Proveedor' "
            "(reception.supplier_id IS NULL y no hay purchase_id.partner_id).",
            orphan_count,
        )

    _logger.info("madenat_lumber_reports [18.0.2.2.0]: Migracion completada.")