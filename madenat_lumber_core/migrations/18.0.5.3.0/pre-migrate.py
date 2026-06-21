"""
Migration 18.0.5.3.0 — Drop legacy orphan columns lumber_reception_id

Context:
  reception_id is the sole canonical FK on both stock.lot and stock.picking.
  The legacy column lumber_reception_id was superseded by data migration
  18.0.5.2.0 (post-migrate) which copied all values to reception_id.
  No model, view, report, wizard or test references lumber_reception_id.
  This is a structural cleanup only — zero functional impact.

Columns removed:
  - stock_lot.lumber_reception_id
  - stock_picking.lumber_reception_id

Safety:
  - IF EXISTS prevents errors if column was already dropped manually.
  - Pre-migrate runs before ORM upgrade, so no code depends on these columns.
  - reception_id remains untouched.
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("ALTER TABLE stock_lot DROP COLUMN IF EXISTS lumber_reception_id")
    _logger.info(
        "Migration 18.0.5.3.0: dropped stock_lot.lumber_reception_id (if existed)"
    )

    cr.execute("ALTER TABLE stock_picking DROP COLUMN IF EXISTS lumber_reception_id")
    _logger.info(
        "Migration 18.0.5.3.0: dropped stock_picking.lumber_reception_id (if existed)"
    )