# MADENAT — Hoja de Ruta de Refactorización
# Ingesta Profesional con Gates de Validación
# ============================================================
# ESTADO:     🟡 EN PROGRESO
# VERSIÓN:    1.0.0
# INICIO:     2026-04-03
# AUTOR:      Equipo MADENAT / Viruco
# MÓDULO:     madenat_lumber_core
# ============================================================
#
# 🚩 BANDERA DE CONTINUIDAD
# Si se interrumpe el trabajo, retomar desde:
#   CHECKPOINT_ACTUAL = "FASE 0.5 / SANEAMIENTO — Refactorización a Servicio (Sección 7)"
#   ARCHIVO_ACTIVO    = "models/lumber_reception.py"
#   DEPENDENCIAS_OK   = ["docs/Errores/*"]
#   TESTS_PENDIENTES  = ["Verificación de integridad ORM tras limpieza"]
#   ÚLTIMO_COMMIT     = "docs: Inicio oficial de saneamiento de lumber_reception.py"
# ============================================================

## PRINCIPIO RECTOR
## ─────────────────
## Cada dato que entra al sistema MADENAT debe pasar por una
## compuerta (Gate) explícita antes de escribir en stock real.
## "Lo que no se valida explícitamente, se valida tarde y caro."

## ════════════════════════════════════════════════════════════
##  FASE 0 — AUDITORÍA (COMPLETADA 2026-04-03)
## ════════════════════════════════════════════════════════════
## [✅] Mapa de archivos y tamaños
## [✅] SQL directo identificado (lumber_reception:1018, guia_processing:3451)
## [✅] Métodos God-Class identificados (3469L / 3252L)
## [✅] Campos temporales sin fecha de retiro catalogados
## [✅] Fix action_force_cancel → return_type incoming (WHIN vs WHOUT)
## [✅] Limpieza bytecode .pyc → deploy confiable
## RESULTADO: Mapa completo. Sistema estable. Iniciando refactor.

## ════════════════════════════════════════════════════════════
##  FASE 0.5 — SANEAMIENTO CRÍTICO (INICIADA 2026-04-18) 🟡 EN PROGRESO
## ════════════════════════════════════════════════════════════ 
## [✅] Eliminación de campos duplicados en LumberReceptionLine
## [✅] Consolidación de decoradores @api.depends
## [✅] Resolución de importaciones rotas (pandas -> openpyxl)
## [✅] Implementación de métodos incompletos (Sección 5)
## [🟡] Consolidación de lógica de anchos y Refactor a Servicio (Secciones 6 y 7)

## ════════════════════════════════════════════════════════════
##  FASE 1 — GATES DE VALIDACIÓN  🟡 EN PROGRESO
## ════════════════════════════════════════════════════════════
##
## OBJETIVO: Crear un pipeline explícito de validación antes
##           de que cualquier dato toque stock real.
##
## NUEVO ARCHIVO: models/ingestion_gate.py
## ─────────────────────────────────────────
## Responsabilidad ÚNICA: validar, nunca procesar.
## Sin side effects. Sin writes a BD en Gate 0/1/2.
##
## [✅] STEP 1 — Gate 0: Pre-Upload
##      • Formato de archivo (xlsx / pdf)
##      • Tamaño dentro de límite (config)
##      • Nombre de archivo no contiene caracteres peligrosos
##
## [🟡] STEP 2 — Gate 1: Post-Parse / Reconciliación Documental
##      • nro_guia PDF == nro_guia Excel
##      • nro_guia NO existe ya en BD (deduplicación)
##      • total_vol Excel ≈ total_vol PDF (±2% tolerancia configurable)
##      • tipo_cambio > 0 y dentro de rango (±20% valor config)
##      • OC existe en Odoo y está en estado 'purchase' o 'done'
##      → PRODUCE: ValidationResult con errores/warnings estructurados
##
## [⬜] STEP 3 — Gate 2: Post-Análisis Comercial
##      • nominal IS NOT NULL y > 0
##      • tipo_subproducto IS NOT NULL
##      • Todos los lotes tienen producto válido en catálogo
##      • Volumen recalculado con nominal == volumen_declarado ±tol
##      → BLOQUEA botón "Validar" en UI si falla
##
## [⬜] STEP 4 — Gate 3: Pre-Commit a Stock Real
##      • Snapshot inmutable del estado staging (JSON + hash SHA256)
##      • Log de auditoría: usuario + timestamp + hash + resumen
##      • Confirmación explícita del operador ("Confirmar y Mover a Stock")
##      → ÚNICO punto de write en stock.move y stock.quant

## ════════════════════════════════════════════════════════════
##  FASE 2 — REFACTOR GOD-CLASS  ⬜ PENDIENTE
## ════════════════════════════════════════════════════════════
##
## OBJETIVO: Dividir lumber_reception.py (3252L) y
##           madenat_guia_processing.py (3469L) en módulos
##           con responsabilidad única.
##
## [⬜] lumber_reception.py → 4 módulos:
##      • lumber_reception_core.py       (modelo, campos, ORM)
##      • lumber_reception_parse.py      (parseo Excel/PDF)
##      • lumber_reception_workflow.py   (botones, estados)
##      • lumber_reception_validators.py (llamadas a Gates)
##
## [⬜] madenat_guia_processing.py → 3 módulos:
##      • madenat_guia_core.py           (modelo, campos)
##      • madenat_guia_stock_engine.py   (motor de stock)
##      • madenat_guia_cancel.py         (action_force_cancel)

## ════════════════════════════════════════════════════════════
##  FASE 3 — ELIMINACIÓN SQL DIRECTO  ⬜ PENDIENTE
## ════════════════════════════════════════════════════════════
##
## [⬜] lumber_reception.py:1018  DELETE SQL → _unlink_draft_picking()
## [⬜] lumber_reception.py:1549  SELECT SQL → lot.volumen_m3 (ORM)
## [⬜] lumber_reception.py:1560  SELECT SQL → lot.volumen_m3 (ORM)
## [⬜] madenat_guia_processing.py:2646  → _find_product_by_name()
## [⬜] madenat_guia_processing.py:3451-3461 → _destroy_done_picking()

## ════════════════════════════════════════════════════════════
##  FASE 4 — TESTS  ⬜ PENDIENTE
## ════════════════════════════════════════════════════════════
##
## [⬜] tests/test_ingestion_gate.py    (Gates 0, 1, 2, 3)
## [⬜] tests/test_force_cancel.py      (WHIN vs WHOUT)
## [⬜] tests/test_stock_lot_volume.py  (cálculo volumen dual)

## ════════════════════════════════════════════════════════════
##  CRITERIOS DE ÉXITO
## ════════════════════════════════════════════════════════════
## ✅ 0 lotes huérfanos en BD tras cualquier cancelación
## ✅ 0 guías duplicadas posibles en BD
## ✅ 0 commits a stock real sin confirmación explícita del operador
## ✅ 100% de campos críticos validados antes del Gate 3
## ✅ Cada módulo < 500 líneas y con responsabilidad única
## ✅ 0 sentencias SQL raw en código de producción
