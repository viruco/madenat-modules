# CHANGELOG — madenat_lumber_reports

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Historial de decisiones: [../madenat_lumber_docs/CANON/04_DECISION_LOG.md](../madenat_lumber_docs/CANON/04_DECISION_LOG.md)
> Estado vigente: [../madenat_lumber_docs/CANON/02_CONTINUIDAD.md](../madenat_lumber_docs/CANON/02_CONTINUIDAD.md)

## [18.0.2.3.0] - 2026-09-25
- **Programación 1 — Identificación Operativa y Trazabilidad Visible de Lotes (vista R1).**
- `stock.quant.lot_operational_label` (Char, compute `store=True`): etiqueta operativa de presentación. El token técnico inicial `GRANEL` se presenta como `Lote Volumen` (`GRANEL 4495589` → `Lote Volumen 4495589`). No se altera `stock.lot.name` ni los datos históricos; la búsqueda por `GRANEL 4495589` sigue disponible vía `lot_id`.
- `stock.quant.lot_entry_datetime` (Datetime, compute `store=True`) + `lot_entry_datetime_source` (Selection): fecha/hora de ingreso desde la recepción documental o, en su defecto, desde la creación del lote para guías de procesamiento. Sin fuente real queda vacío.
- `stock.quant.lot_origin_document` (Char, compute `store=True`): documento de origen real enlazado (recepción de compra o guía de procesamiento).
- `view_stock_quant_tree_r1_detail_patio` reordenada con trazabilidad de origen; `lot_id` y `lot_reception_date` se conservan como columnas opcionales.
- `stock.quant.is_volume_lot` (Boolean, compute `store=True`, `index=True`): criterio TÉCNICO del flujo por volumen (token `GRANEL` al inicio de `stock.lot.name`, con espacios normalizados). Es la única fuente de detección y alimenta el filtro `Lotes Volumen`; no depende de la etiqueta visible.
- Search view R1 ampliada (etiqueta operativa, guía, proveedor, fecha/hora) y filtro `Lotes Volumen` (`domain="[('is_volume_lot', '=', True)]"`).
- Sin migraciones, sin backfill, sin escritura SQL y sin cambios en quants, movimientos, lotes, recepciones ni guías.

## [18.0.2.2.0] - 2026-07-01
- Versión base registrada durante la auditoría forense documental 2026-07-01.
- Sin CHANGELOG previo.
