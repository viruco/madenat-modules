# -*- coding: utf-8 -*-
"""
Migration 18.0.0.2.0 — Clean orphan intake root menu.

Context:
  madenat_lumber_intake used to define a self-owned root menuitem
  ``menu_madenat_lumber_intake_root`` (name "Ingreso Global") at the top level,
  parallel to the canonical MADENAT root owned by madenat_lumber_core.

  In 18.0.0.2.0 the functional menu ``menu_madenat_lumber_intake_wizard`` was
  re-parented to ``madenat_lumber_core.menu_ops_reception_cat`` and the root
  definition was removed from ``views/intake_menus.xml``.

  Odoo does NOT automatically delete ``ir.ui.menu`` records whose XML was
  removed (ir.ui.menu is explicitly excluded from the ORM's obsolete-record
  cleanup because menus can gain children from other modules). Without this
  migration, the orphan root would remain persisted forever.

Safety:
  - Only removes root-level menus (parent_id IS NULL) named "Ingreso Global"
    that have no children left (the functional child is already re-parented
    to the canonical branch by the new XML).
  - Idempotent: if already cleaned, the DELETE matches zero rows.
  - Never touches the re-parented child or the canonical core branch.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_ui_menu
        WHERE parent_id IS NULL
          AND name->>'en_US' = 'Ingreso Global'
          AND id NOT IN (
              SELECT parent_id FROM ir_ui_menu WHERE parent_id IS NOT NULL
          )
        """
    )
    removed = cr.rowcount
    if removed:
        _logger.info(
            "Migration 18.0.0.2.0: removed %s orphan root menu(s) "
            "'Ingreso Global' (madenat_lumber_intake)",
            removed,
        )