# -*- coding: utf-8 -*-
"""
Backfill de dimensiones visuales para lotes pre-fix (reception_service gap).

========================================================================
PROPÓSITO
========================================================================
Los lotes creados por `reception_service.create_lots_from_staging()` antes
del fix de propagación (commit d59e33b) no recibieron los campos visuales
comerciales. Este script rellena esos campos para lotes existentes donde
están vacíos, usando como fuente los datos consolidados en
`lumber.reception.line` (el modelo Comercial — fuente de verdad).

========================================================================
CAMPOS AFECTADOS (stock.lot)
========================================================================
  - espesor_inch_frac   ← lumber.reception.line.thickness_visual
  - ancho_inch_frac     ← lumber.reception.line.width_visual
  - thickness_visual    ← lumber.reception.line.thickness_visual
  - width_visual        ← lumber.reception.line.width_visual
  - length_ft           ← lumber.reception.line.length_input_raw (solo si lengthuom == 'ft')

========================================================================
CRITERIO
========================================================================
  - Solo se escriben campos que están vacíos (NULL, '' o 0.0).
  - Nunca se sobrescriben valores ya existentes.
  - Solo aplica a lotes de recepción (reception_id != False).
  - Excluye lotes de guía procesada (guia_processing_id == False).
  - Si no existe línea de staging matching (lot_name + reception_id),
    el lote se omite con warning.

========================================================================
EJECUCIÓN
========================================================================
  # Dry-run — solo preview, sin escritura:
  docker exec -it odoo18_app python3 -c "
  import odoo; odoo.tools.config.parse_config(['-d','madenat_test','--stop-after-init'])
  env = odoo.api.Environment(odoo.registry('madenat_test').cursor(), odoo.SUPERUSER_ID, {})
  import sys; sys.path.insert(0, '/mnt/extra-addons/madenat_lumber_core/scripts')
  from backfill_lot_visual_dimensions import backfill_lot_visual_dimensions
  backfill_lot_visual_dimensions(env, dry_run=True)
  env.cr.close()
  "

  # Aplicar cambios reales:
  docker exec -it odoo18_app python3 -c "
  import odoo; odoo.tools.config.parse_config(['-d','madenat_test','--stop-after-init'])
  env = odoo.api.Environment(odoo.registry('madenat_test').cursor(), odoo.SUPERUSER_ID, {})
  import sys; sys.path.insert(0, '/mnt/extra-addons/madenat_lumber_core/scripts')
  from backfill_lot_visual_dimensions import backfill_lot_visual_dimensions
  result = backfill_lot_visual_dimensions(env, dry_run=False)
  env.cr.commit()
  env.cr.close()
  print(result)
  "

========================================================================
VALIDACIÓN POSTERIOR
========================================================================
  # Verificar lotes aún vacíos después del backfill:
  SELECT name, espesor_inch_frac, ancho_inch_frac, length_ft
  FROM stock_lot
  WHERE reception_id IS NOT NULL
    AND guia_processing_id IS NULL
    AND (espesor_inch_frac IS NULL OR espesor_inch_frac = ''
         OR ancho_inch_frac IS NULL OR ancho_inch_frac = '');
========================================================================
"""
import logging

_logger = logging.getLogger(__name__)

# Campos a propagar y sus fuentes en lumber.reception.line
_FIELD_MAP = [
    # (campo_en_lot, campo_en_line, tipo_valor)
    ('espesor_inch_frac', 'thickness_visual', 'text'),
    ('ancho_inch_frac',   'width_visual',     'text'),
    ('thickness_visual',  'thickness_visual', 'text'),
    ('width_visual',      'width_visual',     'text'),
    ('length_ft',         'length_input_raw', 'float'),
]


def _is_field_empty(lot, field_name, field_type):
    """Retorna True si el campo del lote está vacío."""
    val = getattr(lot, field_name, None)
    if field_type == 'text':
        return not val or val.strip() == ''
    return not val or val == 0.0


def preview_backfill(env):
    """
    Preview sin escritura — muestra qué lotes se actualizarían y con qué valores.

    Retorna:
        list[dict]: cada dict tiene 'lot_name', 'reception_id', y los campos a actualizar.
    """
    lots = env['stock.lot'].search([
        ('reception_id', '!=', False),
        ('guia_processing_id', '=', False),
    ])

    candidates = []

    for lot in lots:
        line = env['lumber.reception.line'].search([
            ('reception_id', '=', lot.reception_id.id),
            ('lot_name', '=', lot.name),
        ], limit=1)

        if not line:
            continue

        vals = {}
        for lot_field, line_field, field_type in _FIELD_MAP:
            if _is_field_empty(lot, lot_field, field_type):
                source_val = getattr(line, line_field, None)
                # Condición especial para length_ft
                if lot_field == 'length_ft':
                    if line.lengthuom == 'ft' and source_val:
                        vals[lot_field] = source_val
                elif source_val:
                    vals[lot_field] = source_val

        if vals:
            candidates.append({
                'lot_name': lot.name,
                'reception_id': lot.reception_id.id,
                'reception_name': lot.reception_id.name,
                'updates': vals,
            })

    return candidates


def backfill_lot_visual_dimensions(env, dry_run=False):
    """
    Propaga dimensiones visuales desde reception lines a lots pre-fix.

    Args:
        env: Odoo environment.
        dry_run: Si True, solo preview sin escritura.

    Returns:
        dict: {'updated': int, 'skipped': int, 'errors': int, 'preview': list|None}
    """
    lots = env['stock.lot'].search([
        ('reception_id', '!=', False),
        ('guia_processing_id', '=', False),
    ])

    if not lots:
        _logger.info("✅ No hay lotes de recepción para procesar.")
        return {'updated': 0, 'skipped': 0, 'errors': 0}

    stats = {'updated': 0, 'skipped': 0, 'errors': 0}
    updated_ids = []

    for lot in lots:
        # Buscar la línea de staging correspondiente
        line = env['lumber.reception.line'].search([
            ('reception_id', '=', lot.reception_id.id),
            ('lot_name', '=', lot.name),
        ], limit=1)

        if not line:
            _logger.warning("⚠️ Lote %s (reception %s): no se encontró línea de staging",
                            lot.name, lot.reception_id.name)
            stats['errors'] += 1
            continue

        # Construir valores solo para campos vacíos
        vals = {}
        for lot_field, line_field, field_type in _FIELD_MAP:
            if _is_field_empty(lot, lot_field, field_type):
                source_val = getattr(line, line_field, None)
                # Condición especial para length_ft
                if lot_field == 'length_ft':
                    if line.lengthuom == 'ft' and source_val:
                        vals[lot_field] = source_val
                elif source_val:
                    vals[lot_field] = source_val

        if not vals:
            stats['skipped'] += 1
            continue

        if dry_run:
            updated_ids.append(f"{lot.name} (DRY RUN: {vals})")
            stats['updated'] += 1
            continue

        # Aplicar escritura
        try:
            lot.write(vals)
            updated_ids.append(lot.name)
            stats['updated'] += 1
        except Exception as e:
            _logger.error("❌ Error actualizando lote %s: %s", lot.name, e)
            stats['errors'] += 1

    mode = "🔍 DRY RUN — " if dry_run else ""
    _logger.info(
        "%s📦 Backfill %scompletado: %d actualizados, %d sin cambios, %d errores",
        mode, "" if not dry_run else "",
        stats['updated'], stats['skipped'], stats['errors']
    )

    if updated_ids:
        _logger.info("%sLotes procesados: %s", mode, ', '.join(sorted(updated_ids)))

    return stats


if __name__ == '__main__':
    import odoo

    odoo.tools.config.parse_config(['--stop-after-init'])
    db = odoo.tools.config['db_name']

    if not db:
        print("⚠️ Especificar base de datos con -d <dbname>")
        exit(1)

    registry = odoo.registry(db)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        result = backfill_lot_visual_dimensions(env, dry_run=False)
        cr.commit()
        print(f"Resultado: {result}")
