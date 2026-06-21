"""
Migration 18.0.5.2.0 — Migrate stock.picking FK: lumber_reception_id → reception_id
Context: reception_id is now the canonical operational FK on stock.picking.
         lumber_reception_id becomes a related field for backwards compatibility.
         This script copies existing data before Odoo drops the old column.
Idempotent: WHERE guards prevent double-apply and NULL writes.
Safe re-run: checks column existence before UPDATE (compatible with 18.0.5.3.0 cleanup).
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # 0. Safety: check if legacy column still exists before attempting UPDATE.
    #    After migration 18.0.5.3.0 the column is dropped — skip silently.
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = 'stock_picking'
               AND column_name = 'lumber_reception_id'
        );
    """)
    column_exists = cr.fetchone()[0]

    if column_exists:
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
    else:
        _logger.info(
            "Migration 18.0.5.2.0: stock_picking.lumber_reception_id already removed "
            "by a later migration — UPDATE skipped (idempotent re-run)"
        )

    # 2. Fix search_view filter_domain cache
    #    (no specific DB fix needed; just log that views were updated)
    _logger.info("Migration 18.0.5.2.0: stock.picking search views → reception_id")
