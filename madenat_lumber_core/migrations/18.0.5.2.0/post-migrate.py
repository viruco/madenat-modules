"""
Migration 18.0.5.2.0 — Migrate stock.picking FK: lumber_reception_id → reception_id
Context: reception_id is now the canonical operational FK on stock.picking.
         lumber_reception_id becomes a related field for backwards compatibility.
         This script copies existing data before Odoo drops the old column.
Idempotent: WHERE guards prevent double-apply and NULL writes.
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # 1. Copy lumber_reception_id → reception_id where the new column exists but is NULL
    cr.execute("""
        UPDATE stock_picking
           SET reception_id = lumber_reception_id
         WHERE lumber_reception_id IS NOT NULL
           AND (reception_id IS NULL OR reception_id != lumber_reception_id);
    """)
    _logger.info(
        "Migration 18.0.5.2.0: copied lumber_reception_id → reception_id "
        "on stock_picking (%d rows)", cr.rowcount
    )

    # 2. Fix search_view filter_domain cache
    #    (no specific DB fix needed; just log that views were updated)
    _logger.info("Migration 18.0.5.2.0: stock.picking search views → reception_id")