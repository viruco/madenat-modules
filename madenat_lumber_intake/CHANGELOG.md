# Changelog

Todos los cambios notables de este módulo se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [18.0.0.17.0] - 2026-10-17

### Added
- **WP-A (FASE 12) — Estado de conciliación 'ok_rounded' en Consola de Ingreso**:
  - Incorporación del valor `'ok_rounded'` ("Consistente por redondeo") en el campo `documental_conciliation_state` de la fachada `madenat.lumber.intake.console`.
  - Decoración visual `decoration-info="documental_conciliation_state == 'ok_rounded'"` en la Consola y en la fachada de formulario (`intake_console_views.xml`, `intake_guia_processing_facade_views.xml`).

## [18.0.0.16.0] - 2026-10-17

### Added
- **WP-C (FASE 12 / AD-111) — Menú y acción dedicados «Ingresos por Volúmenes»**:
  - Acción `action_madenat_lumber_intake_console_volume` sobre `madenat.lumber.intake.console`,
    con dominio pre-filtrado `ingestion_type = 'volume'` y contexto `'search_default_type_volume': 1`.
  - Menú `menu_madenat_lumber_intake_volume` integrado en la rama canónica de recepción
    (`madenat_lumber_core.menu_ops_reception_cat`), visible para el grupo operativo (`group_madenat_operaciones`).
  - Campo de búsqueda por `state` ("Estado") en la vista `view_madenat_lumber_intake_console_search`.
  - Actualización del rótulo del filtro `type_volume` a «Ingresos por Volúmenes».
  - Pruebas automatizadas en `tests/test_volume_console_search_menu.py`.

## [18.0.0.15.0] - 2026-10-12

### Changed
- **H1 (FASE 4) — motivo obligatorio por cualquier vía.** El asistente sigue aportando
  `madenat_guia_delete_reason`; la vía directa (botón nativo de lista/formulario) queda **bloqueada con
  mensaje** que orienta al asistente, sin modificar vistas ni botones.
- **H1 (FASE 4) — asistente de reclasificación AD-73 corregido.** `intake_reclassify_wizard.
  action_confirm_reclassify` aporta un **motivo de negocio explícito** («Reclasificación de tipo de ingreso
  (AD-73): X → Y») al `unlink()`; antes dependía del valor por defecto retirado en el core (regresión
  detectada y cerrada en la FASE 4).
- **H2 (FASE 4) — `_delete_access_blocker`** informa el **rol «Jefatura de Operaciones»**
  (`_guia_delete_group_ok`) en lugar del grupo técnico «Inventario / Administrador»; se elimina la constante
  `GROUP_STOCK_MANAGER` (ya sin uso).

### Added
- **H1/H2/H4 (FASE 4)** ampliación de `tests/test_guia_delete_guards.py`: motivo obligatorio (ausente, vacío,
  solo espacios), equivalencia asistente ≡ vía directa, bypass test-only con token, matriz de roles
  (jefatura sí; operaciones, auditoría, usuario interno, otra compañía y `stock_manager` sin jefatura no) y
  **escenario (f) dedicado**: lote con línea de coste → bloqueo de negocio; sin costos → permitido.

## [18.0.0.14.0] - 2026-10-12

### Changed
- **G1 (FASE 3) — el asistente comparte la guarda central de eliminación.** `_run_delete_definitive` y
  `_run_controlled_purge` invocan `guia.with_context(madenat_guia_delete_logged=True,
  madenat_guia_delete_reason=…)` para (a) reutilizar la guarda única del core y (b) **no duplicar** la
  bitácora (el asistente ya registra con snapshot vía `_lifecycle_log`).

### Fixed
- **G2 (FASE 3) — fixture `TestDeleteConcurrency` sin limpieza.** Se añade `tearDownClass` que elimina
  **solo** lo creado por la suite (ids registrados en la clase: guía + socio + auditoría asociada), sin borrado
  por nombre amplio. Elimina el residuo de socios «P Conc Fase 2» que dejaban las ejecuciones previas.

### Added
- Suite **`tests/test_guia_delete_guards.py`** (escenarios a–m de las guardas de eliminación).

### Notes
- **Local** (`madenat_test`); sin commit/push/despliegue. Expediente `AUDITORIA_INTEGRAL_20261012/fase3/`.

## [18.0.0.13.0] - 2026-10-12

### Fixed
- **P2 — recomputación REAL de las métricas de la consola (AUD-ETQ-08).** La consola es una vista SQL
  (`_auto=False`); su caché **no** se invalidaba al cambiar una línea del detalle documental (no hay relación
  ORM directa consola↔línea), por lo que una **segunda lectura en el MISMO entorno** devolvía valores
  **obsoletos**. `madenat.lumber.volume.detail.line` invalida ahora **dirigidamente** (`invalidate_model`) los
  campos calculados de la consola que dependen del detalle, en `create`/`write`/`unlink`. **No** hay `search`
  ficticio, **no** se elimina la dependencia del origen, **no** se cambia `store` y **no** hay recomputación
  global.

### Tests
- `tests/test_intake_metrics_recompute.py`: create/write/unlink del detalle con lectura en el **MISMO entorno**
  y en **transacción nueva** (cursor independiente). Suites dirigidas **0 failed / 0 error**.

### Notes
- **Local** (`madenat_test`); **sin commit/push/despliegue**. Separado de las reglas documentales de rebaja.

## [18.0.0.12.0] - 2026-10-12

### Fixed
- **AUD-ETQ-08 — dependencias de los campos calculados de la consola.**
  `_compute_review_metrics` (que calcula `total_volume_m3`, `official_volume_m3`, `volume_detail_m3`,
  `volumen_fuente`, `conciliation_status`, `volume_excel_m3`, `supplier_documental_*`, etc.) dependía de
  `volume_detail_line_ids.volume_m3`, donde `volume_detail_line_ids` es un proxy **Many2many VIRTUAL**
  (compute+inverse, `store=False`, **no buscable**). Odoo no podía determinar qué filas de la consola
  recalcular al modificar `madenat.lumber.volume.detail.line` y advertía «should be searchable» para cada
  campo calculado. Se **corrige la dependencia** a los campos de **identidad del origen** (`source_model`,
  `source_res_id`, `ingestion_type`) —la misma que usan el resto de los computes de la consola, incluido
  `_compute_declared_piece_line_totals`, que ya lee `src.volume_detail_m3` sin advertir—. **No** se
  implementa un `search` ficticio, **no** se cambia el `store` del proxy y **no** se usa recomputación
  global. **Sin** cambios en la ingesta, en el volumen oficial ni en la política de volumen.

### Tests
- Nuevo `tests/test_intake_console_compute_depends.py`: verifica que ningún campo calculado por
  `_compute_review_metrics` depende del proxy virtual no buscable y que el proxy conserva su naturaleza
  (compute+inverse, `store=False`, sin `search` ficticio).

### Notes
- **Intervención LOCAL** (`madenat_test`). **Sin commit/push/despliegue.** Separada de las reglas
  documentales de rebaja (que viven en `madenat_lumber_logistics`).

## [18.0.0.11.0] - anterior
