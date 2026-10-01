# Implementación — Identificación operativa y trazabilidad visible de lotes en R1 (Programación 1, 2026-09-25)

> **Documento NO canónico.** Registra evidencia de implementación, comandos, validaciones y
> diagnóstico. No introduce normas: la regla vive en `CANON/04_DECISION_LOG.md` (AD-77), el inventario
> de campos en `CANON/00_ARQUITECTURA.md` §4.7, el estado/retoma en `CANON/02_CONTINUIDAD.md` §13, la
> evidencia en `CANON/03_TESTS.md` §8 y los pendientes en `CANON/05_BACKLOG.md`.

## 1. Alcance

Hacer R1 ("Detalle por Patio — Stock Real", `stock.quant`) localizable y trazable en segundos para
operación masiva: qué lote es, de qué guía/recepción proviene, cuándo ingresó, qué proveedor lo
originó, dónde está y cuánto volumen ingresó/queda. La nomenclatura visible pasa de `GRANEL` (token
técnico interno) a `Lote Volumen`.

## 2. Exclusiones

- Sin rebaja por volumen, merma, ajuste de inventario ni movimientos de stock nuevos.
- Sin cambios de costeo, facturación, pagos ni embarques.
- Sin SQL directo sobre `stock_quant`, `stock_move`, `stock_move_line` ni `stock_lot`.
- Sin migraciones, backfill ni cambios de `stock.lot.name`.
- No se editaron `madenat_lumber_core/models/stock_lot.py`,
  `madenat_lumber_core/models/madenat_guia_processing.py` ni
  `madenat_ingestion_engine/services/document_extractor.py`.

## 3. Archivos funcionales modificados

| Archivo | Cambio |
|---|---|
| `madenat_lumber_reports/models/lumber_stock_report.py` | Cinco campos compute almacenados en `stock.quant` + helper `_is_volume_lot_name()` |
| `madenat_lumber_reports/views/inventory_report_views.xml` | Vista R1 reordenada con trazabilidad de origen; `lot_id` conservado como columna opcional; search view ampliada y filtro `filter_volume_lots` |
| `madenat_lumber_reports/__manifest__.py` | Versión `18.0.2.2.0` → `18.0.2.3.0` |
| `madenat_lumber_reports/CHANGELOG.md` | Entrada `[18.0.2.3.0] - 2026-09-25` |

Sin migraciones: no existe `migrations/18.0.2.3.0/`. El `migrations/18.0.2.2.0/pre-migrate.py`
existente pertenece a otra versión (backfill de `supplier_id` en recepciones) y no fue tocado.

## 4. Campos implementados y función

| Campo | Tipo | Función | Fuente | `store` |
|---|---|---|---|---|
| `lot_operational_label` | Char | Etiqueta operativa: presenta `Lote Volumen` en lugar del token técnico inicial `GRANEL` | `stock.lot.name` | Sí |
| `is_volume_lot` | Boolean (`index=True`) | Criterio técnico del flujo por volumen; alimenta el filtro `Lotes Volumen` | `stock.lot.name` normalizado | Sí |
| `lot_entry_datetime` | Datetime | Fecha/hora de ingreso (recepción documental o fallback de creación del lote) | `lot_id.reception_id.reception_date`; fallback `lot_id.create_date` con guía de procesamiento | Sí |
| `lot_entry_datetime_source` | Selection (`reception` / `lot_creation`) | Distingue si la fecha provino de recepción documental o del fallback | Igual que `lot_entry_datetime` | Sí |
| `lot_origin_document` | Char | Documento de origen real enlazado | `lot_id.reception_id.name` o `lot_id.guia_processing_id.name` | Sí |

Todos son de solo lectura; ninguno escribe en `stock.lot`, `stock.quant.quantity`, movimientos,
recepciones ni guías.

## 5. Regla técnica `GRANEL` → `Lote Volumen`

Un lote es de volumen si el nombre técnico normalizado (`' '.join(name.split())`) es exactamente
`GRANEL` o comienza con `GRANEL `. La etiqueta operativa sustituye **solo** ese token inicial por
`Lote Volumen`; en cualquier otro caso devuelve el nombre técnico intacto (sin reemplazos parciales
ni globales). `GRANEL` no es nomenclatura de negocio: es token técnico interno del flujo.

| Nombre técnico | `is_volume_lot` | Etiqueta operativa visible |
|---|---:|---|
| `GRANEL 4495589` | Sí | `Lote Volumen 4495589` |
| `GRANEL` | Sí | `Lote Volumen` |
| `  GRANEL  4495589  ` | Sí | `Lote Volumen 4495589` |
| `GRANELITO 123` | No | `GRANELITO 123` (sin cambio) |
| `MAD-001 GRANEL` | No | `MAD-001 GRANEL` (sin cambio) |
| `granel 4495589` | No | `granel 4495589` (sin cambio) |

Detección y presentación comparten la misma fuente (`_is_volume_lot_name()`), por lo que el filtro
técnico y la etiqueta no pueden divergir. El filtro de R1 usa
`[('is_volume_lot', '=', True)]`, no el texto visible.

## 6. Evidencia del upgrade

Comando ejecutado (solo `madenat_test`, solo `madenat_lumber_reports`; sin `-u all`, sin SQL manual):

```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_reports --stop-after-init > /tmp/upgrade_madenat_lumber_reports_18_0_2_3_0.log 2>&1
upgrade_exit_code=$?
printf 'UPGRADE_EXIT_CODE=%s\n' "$upgrade_exit_code"
tail -n 40 /tmp/upgrade_madenat_lumber_reports_18_0_2_3_0.log
```

Resultado observado:

- `UPGRADE_EXIT_CODE=0`.
- Log de 2.608 líneas: `ERROR=0`, `CRITICAL=0`, 61 `WARNING` (todas preexistentes y ajenas al cambio:
  `UserWarning` de `odoo/fields.py:834` sobre dependencias no buscables de
  `madenat.lumber.intake.console`, y avisos de etiquetas duplicadas ya existentes en `stock.quant`,
  p. ej. `lot_supplier` vs `supplier_id`).
- `Module madenat_lumber_reports loaded in 1.44s, 448 queries` y `Modules loaded.` (cierre limpio).
- Sin reinicio de contenedores ni servicios; log preservado durante la sesión.

## 7. Consultas de verificación (solo lectura)

Las dos comprobaciones siguientes son consultas de **solo lectura** usadas para validar la estructura
y el caso histórico. Fueron reportadas por la validación del despliegue (no ejecutadas desde este
informe):

```sql
-- Estructura: columnas nuevas en stock_quant
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_name = 'stock_quant'
   AND column_name IN ('lot_operational_label','is_volume_lot','lot_entry_datetime',
                       'lot_entry_datetime_source','lot_origin_document')
 ORDER BY column_name;

-- Caso histórico
SELECT q.lot_id, l.name, q.lot_operational_label, q.is_volume_lot,
       q.lot_entry_datetime, q.lot_entry_datetime_source, q.lot_origin_document,
       q.lot_guia_number, q.lot_supplier, q.location_name, q.quantity,
       q.lot_volumen_m3, q.lot_volumen_restante_m3
  FROM stock_quant q JOIN stock_lot l ON l.id = q.lot_id
 WHERE l.id = 3753;
```

Resultado reportado: las **cinco columnas existen** en `stock_quant`.

## 8. Resultado del lote 3753

```text
stock.lot(3753)
Técnico: GRANEL 4495589
Operativo: Lote Volumen 4495589
is_volume_lot: true
saldo: 0,000
```

Interpretación: la etiqueta operativa se calcula correctamente y el nombre técnico permanece intacto
(la búsqueda por `GRANEL 4495589` y por `4495589` sigue operando por `lot_id`). El saldo `0,000`
confirma que **no** se alteraron cantidades ni volúmenes.

## 9. Limitación de prueba visual

No existían lotes por volumen con cantidad positiva en ubicación interna, por lo que **R1 y el filtro
`Lotes Volumen` no quedaron validados visualmente con stock**. La validación cubre: upgrade
(estructura de columnas), cálculo de campos y consulta de solo lectura sobre el lote histórico 3753.
No se creó stock artificial para forzar la prueba. Programación 1 **no** se declara validada
visualmente en R1.

## 10. Hallazgos de auditoría (H1–H9)

Clasificación: **deuda previa** (ya existía antes de Programación 1), **brecha de alcance**
(necesidad derivada de Programación 1 no incluida en la iteración) y **pendiente** (trabajo
acordado/no ejecutado).

| # | Hallazgo | Clasificación | Estado al 2026-09-25 |
|---|---|---|---|
| H1 | Las exportaciones XLSX (R1/R2/R5/R7/R9) usan `report_helpers.py` (`_report_get_canonical_lot_label`), que devuelve el nombre técnico del lote: aún **no** presentan `Lote Volumen` | Brecha de alcance | Pendiente — decisión e implementación en backlog |
| H2 | Etiquetas duplicadas en `stock.quant`: `lot_supplier` vs `supplier_id` ("Proveedor") y `lot_subproducto` vs `subproducto_id` ("Subproducto"), con avisos en el log de upgrade | Deuda previa | Sin acción en esta iteración (no autorizado) |
| H3 | Múltiples fuentes de fecha de ingreso en `stock.quant` (`lot_reception_date`, `lot_entry_datetime`, `reception_date` de Core, `lot_id.reception_id.reception_date`) | Deuda previa (ampliada) | Pendiente — revisión arquitectónica en backlog |
| H4 | `lot_origin_document` coincide con el N° de guía cuando el origen es guía de procesamiento | Comportamiento esperado | Documentado (no es defecto) |
| H5 | Cinco campos `store=True` + índice booleano de baja cardinalidad sobre `stock.quant` | Pendiente | Observar rendimiento a escala (backlog) |
| H6 | `05_AUDITORIA_XML_IDS.md` describía R1 con campos y líneas desactualizados | Drift documental | **Corregido** en esta sesión (v1.1.0) |
| H7 | Sin test automatizado del token técnico, la etiqueta operativa y `is_volume_lot` en `madenat_lumber_reports/tests/` | Pendiente | Backlog |
| H8 | `is_volume_lot` no sigue el prefijo `lot_*` del resto de campos del modelo | Excepción deliberada (aprobada) | Documentado en AD-77 y `00_ARQUITECTURA.md` §4.7 |
| H9 | CANON no tenía dueño del inventario de campos de R1 | Brecha de propiedad documental | **Resuelto** con `00_ARQUITECTURA.md` §4.7 |

## 11. Referencias

- `CANON/04_DECISION_LOG.md` — AD-77 (decisión canónica de esta implementación).
- `CANON/00_ARQUITECTURA.md` — §4.7 (inventario de campos de R1 y frontera de propiedad con Core).
- `CANON/02_CONTINUIDAD.md` — §13 (estado, evidencia, límite y retoma).
- `CANON/03_TESTS.md` — §8 (evidencia y matriz de la regla de token).
- `CANON/05_BACKLOG.md` — hitos pendientes derivados (validación visual, XLSX, test, fuentes de fecha, rendimiento).
- `CANON/05_AUDITORIA_XML_IDS.md` — v1.1.0 (XML IDs de R1 y referencias revalidadas).
- Código: `madenat_lumber_reports/models/lumber_stock_report.py`, `views/inventory_report_views.xml`,
  `__manifest__.py`, `CHANGELOG.md`.
