"""
Migration 18.0.5.3.0 — post-migrate: Clean historically inconsistent lots

INCIDENTE PRODUCTIVO 2026-06-18 — Wizard "Agregar Lotes Físicos" mostraba lotes
de guías revertidas/canceladas.

CAUSA RAÍZ:
  action_force_cancel() en madenat_guia_processing.py desvinculaba
  guia_processing_id pero NO marcaba technical_validation='rejected',
  a diferencia de action_reopen_to_draft() que sí lo hacía.
  
  Sin esta marca, los lotes huérfanos (guia_processing_id=NULL,
  reception_id=NULL, technical_validation='approved') pasaban el filtro
  del wizard y aparecían como disponibles.

FIX EN CÓDIGO:
  action_force_cancel ahora marca technical_validation='rejected' de forma
  consistente con action_reopen_to_draft.
  Ver: custom_addons/madenat_lumber_core/models/madenat_guia_processing.py

LIMPIEZA DE DATOS HISTÓRICOS:
  Este script corrige lotes que ya quedaron inconsistentes por ejecuciones
  anteriores de action_force_cancel. Solo afecta lotes huérfanos:
  - guia_processing_id IS NULL → no tienen guía activa
  - reception_id IS NULL        → no provienen de recepción directa
  - technical_validation = 'approved' → aún aparecen como válidos
  Estos lotes fueron creados por una guía de procesamiento que luego fue
  cancelada sin la marca correcta de technical_validation.

SEGURIDAD:
  - No toca lotes de recepción directa (reception_id IS NOT NULL)
  - No toca lotes con guía activa (guia_processing_id IS NOT NULL)
  - No toca lotes ya marcados como rejected
  - Usa savepoint para rollback seguro en caso de error
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("=" * 60)
    _logger.info(
        "Migration 18.0.5.3.0 post-migrate: Cleaning historically "
        "inconsistent lots (guía force_cancel bug)"
    )

    # Count affected lots before fix
    cr.execute("""
        SELECT COUNT(*) FROM stock_lot
        WHERE guia_processing_id IS NULL
          AND reception_id IS NULL
          AND technical_validation = 'approved'
    """)
    affected_count = cr.fetchone()[0]

    if affected_count == 0:
        _logger.info("No historically inconsistent lots found — nothing to clean.")
        _logger.info("=" * 60)
        return

    # Detail the affected lots for audit trail
    cr.execute("""
        SELECT id, name, estado_trazabilidad, technical_validation,
               volumen_m3, piezas
        FROM stock_lot
        WHERE guia_processing_id IS NULL
          AND reception_id IS NULL
          AND technical_validation = 'approved'
        ORDER BY id
    """)
    affected_details = cr.fetchall()

    _logger.warning(
        "Found %d lots with guia_processing_id=NULL, reception_id=NULL, "
        "technical_validation='approved'. These will be marked as 'rejected'.",
        affected_count
    )
    for row in affected_details:
        _logger.info(
            "  Lot id=%s name=%s estado_trazabilidad=%s technical_validation=%s "
            "volumen_m3=%s piezas=%s",
            row[0], row[1], row[2], row[3], row[4], row[5],
        )

    # Apply fix within savepoint for rollback safety
    try:
        with cr.savepoint():
            cr.execute("""
                UPDATE stock_lot
                SET technical_validation = 'rejected'
                WHERE guia_processing_id IS NULL
                  AND reception_id IS NULL
                  AND technical_validation = 'approved'
            """)
            _logger.info(
                "✅ Fixed %d lots: technical_validation set to 'rejected'.",
                affected_count,
            )
    except Exception as e:
        _logger.error(
            "❌ Failed to clean historically inconsistent lots: %s", e
        )
        raise

    _logger.info("=" * 60)