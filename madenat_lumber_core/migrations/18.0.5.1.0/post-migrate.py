"""
Migration 18.0.5.1.0 — Fix thickness_visual range 6/4
Bug: 45mm S2S classified as 7/4 because 6/4 max_thickness was 42mm.
Fix: 6/4 max=46mm, 7/4 min=46mm — covers canonical S2S thickness.
Idempotent: WHERE guards prevent double-apply.
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE lumber_thickness_visual_rule
           SET max_thickness = 46.0
         WHERE visual_label = '6/4'
           AND max_thickness < 46.0;
    """)
    _logger.info("Migration 18.0.5.1.0: 6/4 max_thickness → 46mm (%d rows)", cr.rowcount)

    cr.execute("""
        UPDATE lumber_thickness_visual_rule
           SET min_thickness = 46.0
         WHERE visual_label = '7/4'
           AND min_thickness < 46.0;
    """)
    _logger.info("Migration 18.0.5.1.0: 7/4 min_thickness → 46mm (%d rows)", cr.rowcount)
