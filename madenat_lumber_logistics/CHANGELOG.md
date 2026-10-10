# Changelog

Todos los cambios notables de este módulo se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [18.0.1.8.0] - 2026-10-10

### Added
- **Ajuste de integridad del vínculo envío–retorno (CANON/19 §19.13).**
  - **Reversa de imputación vs. procedencia:** `state` = **procedencia** (envío↔retorno);
    nuevos campos **`documentary_status`** (vigencia documental derivada del estado real de la
    imputación) y **`requires_reimputation`**. Reversar la imputación **no** revierte la procedencia.
  - **Reimputación:** `previous_imputation_id` conserva la imputación reemplazada; se deja rastro
    (chatter + auditoría `processor_return_link`, descripción «reimputación») sin sobrescribir en
    silencio ni duplicar vínculos activos.
  - **Consistencia de compañía** (`_check_company_consistency`) y **regla de registro multi-compañía**
    (`security/madenat_processor_return_link_rules.xml`). `madenat.guia.processing` no tiene
    `company_id` (documento): no se compara.
  - **Elegibilidad dura por modelo/ORM/RPC:** sólo envíos validados (`state='done'`) y de tipo interno
    (`picking_type_id.code='internal'`). Dominio y validación alineados.
  - **Volúmenes N:M referenciales:** `aggregator=False` en `shipment_volume_m3`/`return_nominal_m3`
    (sin agregación engañosa en pivot/graph/`read_group`) + ayuda explícita. Sin reparto ni resta.
  - Vistas: badge de vigencia documental, filtro «Requiere reimputación» y grupo por vigencia.
  - Pruebas: `test_processor_return_link.py` **T1–T22** (22/22).

## [18.0.1.7.0] - 2026-10-10

### Added
- **Bloque A/B/C (CANON/19 §19.11) — Relación de conciliación envío–retorno (procesador).**
  - Nuevo modelo persistente `madenat.processor.return.link` (enlaza el **envío** `stock.picking`
    —no el wizard transitorio—, la **guía** de retorno y la **imputación** documental SV). Estados
    `draft` → `linked` → `reversed`; N:M; unicidad por par en estados activos; inversos en
    `stock.picking`, `madenat.guia.processing` y `madenat.sv.imputation`.
  - Magnitudes **separadas** (sin resta): `shipment_volume_m3` y `return_nominal_m3`. **No** calcula
    saldo de proceso, rendimiento ni merma (Bloque D pendiente).
  - Permisos por ORM/RPC (registrar: Operaciones/Jefatura/Gerencia; reversar: Jefatura/Gerencia);
    append-only con motivo, evidencia firmada (SHA-256) y auditoría aditiva
    `processor_return_link` / `processor_return_link_reverse`.
  - Asistente de imputación **reutilizado**: pestaña «Envíos a procesador (retorno)» (envíos
    elegibles del mismo procesador); al aplicar registra las relaciones.
  - Pestañas de trazabilidad en guía y picking; menú de Logística «Conciliación Envío–Retorno».
  - Pruebas: `tests/test_processor_return_link.py` T1–T12 (12/12). Ver `03_TESTS.md` §15.

## [HF-001] — 2026-06-03 — Hotfix: Revertir imports inválidos entre addons

### Fixed
- **CRÍTICO:** Revertidos imports Python absolutos `from madenat_lumber_core.models.utils_uom import MM_PER_INCH, M3_DIVISOR`
  que rompían el mecanismo de carga del registry de Odoo 18 CE en Docker.
  Evidencia: `AssertionError: Invalid import of madenat_lumber_core.models.reception_parser.MadenatReceptionParser,
  it should start with 'odoo.addons'`
  - Línea 79: `ancho_mm / MM_PER_INCH` → `ancho_mm / 25.4  # HF-001`
  - Línea 124: `adjusted_width_inch * MM_PER_INCH` → `adjusted_width_inch * 25.4  # HF-001`
  - Línea 131: `/ float(M3_DIVISOR)` → `/ 1_000_000.0  # HF-001`
  - Restricción documentada en `utils_uom.py` para futuros desarrolladores

### Deuda Técnica
- TD-004B pendiente: diseñar arquitectura correcta para constantes compartidas entre addons
  (módulo utils puro sin modelos ORM)

### Validado
- HTTP 200 en `/web/health`
- Golden records inalterados: A1M2605458=4.893, A1M2602536=4.832

---

## [Unreleased]

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_shipment_line.py:78,123`
- TD-005: Centralización de divisor métrico `1_000_000.0` → `M3_DIVISOR` en `lumber_shipment_line.py:131`. Agregado import `M3_DIVISOR` desde `utils_uom`.
- Wizard de asignación de lotes: corregido el dominio de disponibilidad para incluir lotes con `estado_trazabilidad = 'procesado'` y `'recepcionado'`, además de `'en_patio'`. Anteriormente solo se mostraban lotes con estado `'en_patio'`, lo que excluía lotes válidos de guía procesada y recepciones en curso.
- Clasificación de lotes: corregido `_is_processed_lot()` en `stock_lot.py` para que `subproducto_id` por sí solo no marque un lote como procesado. El subproducto es clasificación comercial, no indicador de procesamiento. Solo `guia_processing_id`, `parent_lot_id` o dimensiones finales indican procesamiento real.

### Added

- Documentación técnica completa del módulo: README, arquitectura y reglas de disponibilidad.
- Definición formal de la regla canónica de disponibilidad para asignación de lotes a contenedores.
- Tabla de semántica de estados de trazabilidad (`estado_trazabilidad`).

### Changed

- UX de consolidación de contenedores alineada con dimensiones comerciales: wizard de asignación muestra E"/A"/L(ft) como principales, mm/m como opcionales. Pestaña "Lotes Asignados" del contenedor prioriza L(ft) sobre L(m).
- Wizard `lumber.consolidation.import.wizard` archivado como dead code documentado. El archivo existe en `wizards/lumber_consolidation_import_wizard.py` pero no está integrado (sin import, sin vista XML, sin acción). Su lógica era incompatible con el modelo actual (escribe campos inexistentes en `stock.lot`). El flujo canónico de asignación a contenedores es `lumber.container.lot.wizard`.
- Documentación del dominio del wizard para reflejar la regla de disponibilidad canónica.
- Comentario en `_is_processed_lot()` para documentar que `subproducto_id` no es indicador de procesamiento.

## [2026-05-31]

### Fixed

- Parche TD-006: corrección en dos pasos de la clasificación de lotes y disponibilidad para contenedor.
- Lotes de recepción con `subproducto_id` ahora se clasifican correctamente como `'en_patio'` en lugar de `'procesado'`.
- Wizard de contenedores muestra lotes de ambos orígenes (recepción y guía procesada) sin exclusión incorrecta.

## [2026-05-30]

### Fixed

- Campo `ref` en `stock.lot` ahora se escribe desde `lumber.reception` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente la etiqueta/código del lote.
- Campo `subproducto_id` en `stock.lot` ahora se escribe desde `lumber.reception.line.subproduct_id` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente el subproducto.
- Data migration: 20 lotes existentes actualizados con `ref` y `subproducto_id` desde las líneas de recepción correspondientes.

## [2.4.0] - 2025-12-13

### Added

- **Constraint Inteligente:** `_check_shipment_change_with_distributed_costs` para proteger integridad financiera.
- **Trazabilidad de Costos:** Campos `is_distributed` y lógica de distribución detallada.

### Changed

- **Distribución de Costos:** Reingeniería de `action_distribute_costs` para soportar escritura en `stock.lot.cost.line` y campos legacy (Dual Write).
- **Estándar:** Alineación con arquitectura de costos SAP/Oracle.
