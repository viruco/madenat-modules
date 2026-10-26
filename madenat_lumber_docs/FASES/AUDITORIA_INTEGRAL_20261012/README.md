# AUDITORÍA INTEGRAL E HIGIENE DEL REPOSITORIO MADENAT — FASE 1 (AUDITORÍA, SOLO LECTURA)

**Fecha:** 2026-10-12 · **Entorno:** repositorio local + `madenat_test` (LOCAL) · **Odoo:** `18.0-20260817`.
**Alcance:** FASE 1 (solo lectura). **NO se ejecutó ninguna acción de la FASE 2.**
**Prohibiciones respetadas:** sin commit/push/reset/clean/stash/checkout/rebase; sin borrar/mover/renombrar; sin
tocar el TEST remoto ni conectarse a él; sin modificar datos de negocio/`IMP04823`/`IMP02220`/históricos; sin
core de Odoo; sin ampliar permisos/ACL/`ir.rule`; sin `-u all`; sin cambios funcionales.

> **Compuerta:** este informe se DETIENE aquí. La FASE 2 sólo se ejecuta sobre las acciones que Mauricio
> **apruebe expresamente y por escrito**. El silencio NO es autorización.

---

## 1. RESUMEN EJECUTIVO

- **Estado Git:** rama `feat/guia-correccion-documental-preservada-20261002`, **HEAD `b1d2d19`**, **104
  entradas** de WIP (**67 modificados + 37 nuevos**), **0 en stash**. Sin commits de las intervenciones
  recientes (todo vive en el árbol de trabajo).
- **Versiones locales:** `core 18.0.6.7.0`, `logistics 18.0.1.26.0`, `intake 18.0.0.13.0`,
  `costing 18.0.1.0.0`, `vendor_payment 18.0.1.2.0` (instalado).
- **Riesgos principales (severidad):**
  1. **ALTA — WIP heterogéneo sin commits**: 104 entradas de ~9 intervenciones mezcladas (rebaja/SV, I2,
     intake/guias, costing-C2, LOCK, chatter, lote/FK, docs) sin separación por commits ⇒ riesgo de pérdida y
     de mezclar trabajo propio/ajeno. Mitigable con `git bundle`/diff (Fase 2, acción A1).
  2. **MEDIA — Comportamiento funcional ya activo en LOCAL sin commit**: logistics a 18.0.1.26.0 y core a
     18.0.6.7.0 están aplicados en `madenat_test` pero **no** versionados en Git.
  3. **MEDIA — Deuda documental preexistente** declarada (02 comentario duplicado; 03 §5–§9 duplicadas;
     §17.16.19…29 sin cuerpo; 20 copias paralelas de `madenat_lumber_docs` en expedientes).
  4. **MEDIA — Higiene de código**: imports sin uso (varios en archivos del WIP), 1 método sin llamadores
     (`_i2_lock_sv_lots`), archivos huérfanos (`shipping_models.py`, `lumber_consolidation_import_wizard.py`),
     `_archive/` y `LEGADO/backups_modulos` dentro del árbol.
  5. **MEDIA — Datos locales residuales**: 3 usuarios de prueba inactivos (`*@madenat.test`), 11 auditorías
     con "test", 147 lotes con `lot_flow_type` NULL.
  6. **BAJA — ACL**: 1 cambio de permiso en WIP (jefatura gana `unlink` en `madenat.guia.processing`) y 1
     `ir.rule` nueva (multi-compañía). Requieren confirmación de que son intencionales.
- **Fallas preexistentes caracterizadas (NO ocultadas):** `core+intake+logistics` = **6 failed + 4 error**
  (conjunto idéntico al baseline del mismo día); `logistics` = **4 failed**. Detalle en §4.4.
- **TEST remoto:** intacto (no inspeccionado, no tocado).

---

## 2. BASELINE (3.1)

- **Ruta repo:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (`.git`).
- **Rama/HEAD:** `feat/guia-correccion-documental-preservada-20261002` / `b1d2d1911648f3264bf629c8eccf79a1c140eaf3`.
- **`git status`:** 104 entradas (67 `M`, 37 `??`); ver `code/wip_status.txt`. **`git stash`: vacío.**
- **WIP volcado (solo lectura):** `code/wip_tracked.diff` (10.995 líneas), `code/wip_tracked.diffstat.txt`.
- **Base LOCAL:** `madenat_test`. Versiones por módulo: §1.
- **Espacio en disco:** `odoo-18-ce` total **1.1 GB**; `custom_addons` 52 MB; `backups/` 239 MB;
  expedientes raíz ~700 MB (top: `BACKUP_AB_APPLY_20261008` 141M, `FIX_GUIA_DUP_FINAL` 140M,
  `CONCILIACION_ENVIO_RETORNO` 132M, `FIX_GUIA_DUP_CIERRE`/`FIX_GUIA_DUP` 93M c/u, `AUDIT_REBAJA_ETIQUETAS` 50M).
- **Prerequisito de FASE 2 (aún NO ejecutado):** respaldo verificado de código + base (`pg_dump -Fc`) +
  filestore + **`git bundle`/diff completo del WIP**. Se prepara como acción **A1** (§5).

## 3. TRIAJE DEL WIP (3.2)

Clasificación reproducible: `code/triage_wip.py` → **`code/wip_triage.tsv`** (104 filas: estado, módulo,
intervención, ruta, autoría, cobertura). **Autoría:** *no demostrable* para todos (no hay commits ni
trazabilidad de autor); se rotula por **intervención/ventana temporal**, no por persona.

### 3.a Agrupación por intervención (inferida por ruta/evidencia)

| Intervención | Nº | Módulos | Ejemplos |
|---|---|---|---|
| `metadatos` (manifest/`__init__`/CHANGELOG/ACL-csv) | 12 | todos | `madenat_lumber_logistics/__manifest__.py`, `*/tests/__init__.py` |
| `I2/imputacion-SV` | 10 | logistics | `models/madenat_sv_imputation.py`, `wizards/madenat_sv_imputation_wizard*.py/xml` |
| `rebaja-etiquetas` | 9 | logistics | `tests/test_sv_rebaja_{blindaje,cierre,operativa,material,navigation,seleccion,ui_*,assignment_user_rights}.py` |
| `documentacion-canon` | 9 | docs | `CANON/{02,03,05,18,19,INDICE}.md`, `WIKI/*` |
| `intake` | 7 | intake | `models/intake_*.py`, `tests/test_intake_*` |
| `intake/guias-dup-delete` | 6 | core+intake | `tests/test_guide_dup*`, `test_guide_lifecycle*`, `test_guia_delete_acl` |
| `costing-C2` | 6 | costing | `models/stock_lot_cost_line.py`(nuevo), `views/lumber_shipment_costing_views.xml`(nuevo), `tests/test_shipment_costing_c2.py` |
| `reset/reapertura` | 4 | logistics | `tests/test_sv_rebaja_reset*.py` |
| `embarque/zarpe-B01` | 4 | logistics | `wizards/lumber_shipment_zarpe_wizard*`, `models/lumber_export_shipment.py` |
| `UI/navegacion` | 3 | logistics/core | `views/logistics_menus.xml`, `lumber_core_menu.xml`, `wizards/lumber_container_rollover_wizard.py` |
| `sobrescritura-LOCK` | 3 | logistics | `tests/test_sv_rebaja_save_lock*.py` |
| `seguridad/ACL` | 3 | core/logistics | `security/ir.model.access.csv`, `security/madenat_sv_imputation_rules.xml`(nuevo) |
| `rebaja-contenedor` | 3 | logistics | `models/lumber_container.py`, `tests/test_rebaja_contenedor.py` |
| `core/recepcion` | 3 | core | `models/lumber_reception.py`, `mixin_lumber_ingest.py`, `reception_parser.py` |
| `backlog-documental` | 3 | logistics | `views/lumber_document_checklist_views.xml`, `tests/test_documentary_backlog.py` |
| `shipping-core` | 3 | shipping_core | `models/shipping_vessel.py`, `views/shipping_*` |
| `persistencia/SIMPLE` | 2 | logistics | `tests/test_sv_rebaja_{persistencia,simple}.py` |
| `lote/stock_quant-FK` | 2 | core | `models/stock_lot.py`, `tests/test_sv_lot_unlink_guard.py`(nuevo) |
| `core/guias`, `core/sv-ledger`, `core/audit-log`, `intake-volumen`, `reports`, `hotfix-chatter`, `contrato-aplicacion` | 1 c/u | varios | ver TSV |

**5 entradas** requirieron mapeo manual (patrón ausente): `core/tests/test_duplicate_validation.py`
(→ guias-dup), `logistics/tests/test_rebaja_contenedor.py` (→ rebaja-contenedor),
`logistics/tests/test_service_return_imputation_guard.py` (→ retorno-servicio),
`logistics/wizards/lumber_shipment_rebaja_wizard{,_views}.py/xml` (→ rebaja-motonave).

### 3.b Hallazgos del triaje

- **Archivos tocados por varias intervenciones:** `madenat_sv_imputation.py` (I2 + LOCK + rebaja + auditoría);
  `lumber_container.py` (rebaja-contenedor + rolleo + UI); `logistics_menus.xml`/`lumber_actions.xml`
  (navegación + rebaja); `ir.model.access.csv` de logistics (I2 + rebaja-wizard + rules). → **Commit único
  imposible**: exige commits por capas (§6).
- **Cambios sin documentar en CHANGELOG/CANON:** `madenat_lumber_costing` **C2** tiene WIP funcional (modelo +
  vista nuevos, test) **sin** subir `version` (sigue `18.0.1.0.0`) **ni** CHANGELOG ⇒ **H-DOC-1**.
- **Nuevos sin registrar:** `reception_workflow.py`/`core_utils.py`/`document_format.py` son **falsos
  positivos** (se importan **por demanda**); `shipping_core/models/shipping_models.py` y
  `logistics/wizards/lumber_consolidation_import_wizard.py` **sí** parecen huérfanos (0 referencias).
- **Ajenos↔propios:** el bloque `costing-C2` y el de `intake/guias-dup-delete` parecen de líneas distintas a
  la de rebaja/SV; se separan en §6.
- **Temporales dentro del árbol:** `__pycache__`/`*.pyc` (ignorados por `.gitignore`);
  `madenat_lumber_core/_archive/` (5 archivos, **trackeado**); `madenat_lumber_docs/LEGADO/backups_modulos` (1.5 MB).

## 4. HALLAZGOS (3.3–3.8)

### 4.1 Código (3.3)

| ID | Sev | Evidencia | Impacto | Acción propuesta | Riesgo | Reversible |
|---|---|---|---|---|---|---|
| H-CODE-1 | baja | `_i2_lock_sv_lots` sin llamadores (grep=0); `models/madenat_sv_imputation.py:745` | Código muerto (shim de compatibilidad) | Retirar (C1) | Bajo | Sí (git) |
| H-CODE-2 | — | `_I2_REOPEN_TOKENS` **no** existe en código; sólo citado en `test_sv_rebaja_reset_token.py` ("diseño anterior") | **Verificación positiva**: ya no hay resto | Ninguna | — | — |
| H-CODE-3 | baja | `audit_unused_imports.py` → `logs/unused_imports.out` (~30 imports sin uso en `models/wizards`, varios en archivos del WIP: `madenat_guia_processing.py`, `lumber_reception.py`, `stock_lot.py`, `madenat_sv_operation.py`, `reception_workflow.py`) | Ruido, riesgo de confusión | Limpiar selectivamente (C2) | Bajo (requiere pruebas) | Sí |
| H-CODE-4 | baja | `shipping_models.py`, `lumber_consolidation_import_wizard.py` sin referencias (grep=0) | Archivos huérfanos | Archivar/revisar (A2) | Bajo | Sí |
| H-CODE-5 | baja | `madenat_lumber_core/_archive/` (5 archivos de "apply_patch", trackeado) | Restos de parches históricos en el árbol | Mover a cuarentena (A3) | Bajo | Sí |
| H-CODE-6 | baja | `except Exception:` ×3 en `intake_guide_lifecycle_wizard.py` (`_acquire_delete_lock`) y otros en core | Excepciones silenciadas | **Verificado defensivo y documentado**; mantener | Bajo | — |
| H-CODE-7 | — | `madenat.sv.internal.marker._sv_test_*` exige `--test-enable` **real** + token (`_sv_test_enable_strict`); `_sv_guard_unlink` en `stock_lot.py:1261` | Marcadores test-only **inertes** sin `--test-enable`; no expuestos por RPC de negocio | Verificación positiva | — | — |
| H-CODE-8 | baja | Advisory locks: `(1,documento)`, `(2,lot SV)`, `(3,lot retorno)` (`madenat_sv_imputation.py`), intake `(1296122437,guia)` | Sin colisión **interna**; riesgo externo bajo (core no usa advisory) | Documentar inventario | Bajo | — |
| H-CODE-9 | media | `costing-C2` (modelo+vista+test nuevos) con `version` **sin subir** (18.0.1.0.0) y **sin** CHANGELOG | Versión/CHANGELOG incoherentes | Subir versión+CHANGELOG si el C2 se consolida (D1) | Bajo | Sí |
| H-CODE-10 | baja | `madenat_lumber_billing` manifest `version='1.0.0'` vs BD `18.0.1.0.0` | Formato de versión incoherente | Alinear a `18.0.1.0.0` (D2) | Bajo | Sí |
| H-CODE-11 | baja | Manifests: vistas presentes no listadas (varias, legacy); `costing_menus.xml` comentado a propósito | Ruido/legacy | Revisar una a una (D3) | Bajo | Sí |
| H-CODE-12 | — | Vistas: 50 `column_invisible`; el único no-constante es `parent.multi_sv` (correcto); 0 `footer` en formularios de página completa; 3 `widget="many2one"` (todos sobre campos m2o válidos) | **Verificación positiva** (HOTFIX previos OK) | — | — | — |
| H-CODE-13 | baja | `vendor_payment/views/lumber_shipment_cost_views.xml:151` `div.oe_chatter` (archivo **fuera del manifest**, modelo sin `mail.thread`) | Marcado heredado inerte | Ya reportado (HOTFIX chatter) | Bajo | Sí |

### 4.2 Pruebas (3.4)

| ID | Sev | Evidencia | Impacto | Acción propuesta | Riesgo | Reversible |
|---|---|---|---|---|---|---|
| H-TEST-1 | baja | `madenat_lumber_core/tests/__init__.py` no lista `sv_test_common` (helper), `test_ingestion_gate`, `test_lot_costing` | 2 módulos de test **no se ejecutan**; 1 helper OK | Registrar/renombrar o declarar obsoletos (D4) | Bajo | Sí |
| H-TEST-2 | media | 7 suites usan `.commit()` + conexiones independientes (`test_sv_concurrency`, `test_sv_rebaja_reset_concurrency`, `test_sv_rebaja_save_lock`, `reset_lot_capacity`, `save_lock_tx`, `test_intake_metrics_recompute`, `test_guide_lifecycle_phase2`) | Posible **residuo** si algo falla antes del rollback | Auditar `tearDown`/`finally` (D5) | Bajo | — |
| H-TEST-3 | baja | `self.skipTest(...)` ×10 (sin datos reales / sin grupo / sin intake) | SALTOS condicionales (no fallos ocultos) | Declarar; mantener | Bajo | — |
| H-TEST-4 | media | Tests modificados (8): `test_rebaja_contenedor.py` (+396, renombres y nuevas aserciones de rolleo/zarpe), `test_duplicate_validation.py` (rename homónimo guía/recepción), `test_sv_imputation_i2.py`, `test_sv_imputation_candidates.py`, `test_document_status_b2.py`, `test_processor_return_link.py`, `test_documentary_backlog.py`, `test_service_return_imputation_guard.py` | Cambios de aserción en el WIP | Revisar diff (ya archivado en `logs/changed_tests.diff`); **no** debilitar (D6) | Bajo | Sí |
| H-TEST-5 | — | Fixtures/`setUpClass` sin datos residuales detectables salvo lo de H-TEST-2 | — | Verificación | — | — |

### 4.3 Datos locales (3.5, solo lectura)

| ID | Sev | Evidencia (SQL) | Impacto | Acción propuesta | Riesgo | Reversible |
|---|---|---|---|---|---|---|
| H-DATA-1 | baja | 3 usuarios **inactivos** de prueba: `2974 v3_concil_oper@madenat.test`, `2975 v3_concil_jef@madenat.test`, `3109 impl_sv_check@madenat.test` | Residuo de pruebas | Eliminar/anonimizar (dry-run) (**D7**) | Bajo | Sí (backup) |
| H-DATA-2 | baja | 11 filas `madenat_audit_log` con `description ILIKE '%test%'` | Residuo/ruido de bitácora | Revisar; **no** borrar sin decisión (bitácora) (**D8**) | Medio | Sí (backup) |
| H-DATA-3 | media | `stock_lot`: 151 total, **147 `lot_flow_type` NULL**, 2 `tarja`, 2 `volume` | Anomalía conocida | **No** reparar aquí; saneamiento con dry-run (D9) | Medio | Sí |
| H-DATA-4 | — | `madenat_sv_imputation`: 3 (2 `applied`, 1 `cancelled`); **0** `draft`/`pending` ⇒ **0 reservas** de capacidad | **Verificación positiva** | — | — | — |
| H-DATA-5 | — | **IMP02220** id 1189 `applied`, `write_date == create_date` (sin cambios). **IMP04823** id 2733 `cancelled`, `write_date 2026-10-12 19:43:36` **>** `create_date` (modificado en una sesión previa, anterior a las de este agente) | Trazabilidad | Describir; **no** modificar | — | — |
| H-DATA-6 | — | **0** huérfanos: `imputation_line` sin padre ni auditoría sin guía | **Verificación positiva** | — | — | — |
| H-DATA-7 | — | `sv_operation` 1 (applied); `audit_log` 325; `mail_message(madenat)` 322 (40 de sv.imputation); `madenat_processor_return_link` 1; attachments 1109 | Contexto | — | — | — |

### 4.4 Fallas de la regresión amplia (3.4) — caracterizadas, NO ocultadas

**Conjunto EXACTO (10) — `core+intake+logistics`, 2026-10-12:**

| Tipo | Test | Causa raíz demostrada | ¿Entorno? | ¿Preexistente? |
|---|---|---|---|---|
| FAIL | `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` | AssertionError de dominio/exclusión de retornos (pre-existente) | No | **Sí** (mismo en baseline) |
| FAIL | `TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive` | AssertionError savepoint/cleanup (pre-existente) | No | **Sí** |
| FAIL | `TestProcessorLocations.test_09_auditoria_envio_normal` | AssertionError auditoría envío normal | No | **Sí** |
| FAIL | `TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo` | AssertionError aserción global de `deviation` | No | **Sí** |
| FAIL | `TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1` | ídem | No | **Sí** |
| FAIL | `TestProcessorShipmentAD89.test_t6_idempotencia` | ídem | No | **Sí** |
| ERROR | `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen` | `could not obtain lock on row in relation "stock_lot"` / timeout | **Sí** | **Sí** |
| ERROR | `TestSvEscalationSecurity.test_02_costo_exige_contabilidad` | `null value in column "reason"` (orden de datos) | **Sí** | **Sí** |
| ERROR | `TestSvEscalationSecurity.test_03_alza_de_baseline_exige_auditoria` | ídem / serialización | **Sí** | **Sí** |
| ERROR | `TestSvEscalationSecurity.test_04_auditoria_y_contabilidad_por_dos_personas` | serialización | **Sí** | **Sí** |

**Comparación con baseline verificable (mismo día, mismo WIP):**
- `core+intake+logistics`: **6 failed + 4 error de 1284** (esta auditoría) **vs 6 failed + 4 error de 1217**
  (`BLINDAJE_REBAJA_LOCAL_20261012/logs/regression.log`, 2026-10-12 15:54) ⇒ **mismo conjunto, 0 nuevos**
  (las 67 pruebas extra del WIP no añaden fallas).
- `logistics`: **4 failed de 506** **vs 4 failed de 444** (baseline) ⇒ **0 nuevos**.
- **Tratamiento propuesto:** separar los 4 de `deviation`/`locations` (código) de los 6 de
  entorno/concurrencia (infra de test: serializar las suites concurrentes o marcar como *environment-sensitive*).
  **NO** se corrigen ni debilitan en esta fase (**D10**).

### 4.5 Documentación (3.6)

**Estado verificado (post-alineación del 2026-10-12):** versiones **monótonas** y marcadores `<!--`/`-->`
**balanceados** en 02/03/05/19/INDICE/WIKI (`logs/docs_alignment_recheck.out`).

| ID | Sev | Evidencia | Impacto | Acción propuesta | Riesgo | Reversible |
|---|---|---|---|---|---|---|
| H-DOC-1 | media | `costing` C2 sin `version`/CHANGELOG (ver H-CODE-9) | Fuente canónica incompleta | Documentar C2 (D1) | Bajo | Sí |
| H-DOC-2 | baja | `CANON/02` tiene **dos** comentarios `2026-10-10 (3)` y faltan `(4)(5)(6)` | Numeración no única | Renumerar (arrastra 7 entradas) (**D11**) | Bajo | Sí |
| H-DOC-3 | media | `CANON/03` tiene **dos series** de secciones `## 5.`…`## 9.` | Secciones duplicadas | Renumerar 2.ª serie (26 encabezados o anexar 31–35) (**D12**) | Medio | Sí |
| H-DOC-4 | media | `CANON/02` e `INDICE` citan **§17.16.19…§17.16.29** sin sección de cuerpo (contenido sólo en expedientes) | Changelog sin sección | Restaurar desde expedientes o aceptar (**D13**) | Medio | Sí |
| H-DOC-5 | baja | **20** árboles `madenat_lumber_docs` (19 snapshots en expedientes + 1 canónico) | Posibles fuentes paralelas | Etiquetar snapshots como copia (**D14**) | Bajo | Sí |
| H-DOC-6 | baja | `.gitignore` ignora `madenat_lumber_docs/PLAN_*.md`, `CIERRE_*.md`, `AUDITORIA_*.md`, etc. ⇒ docs de trabajo fuera de Git | Trazabilidad | Aceptar (regla vigente) | Bajo | — |

> **No** se ha creado ningún documento paralelo ni se ha reescrito contenido de entregas previas.

### 4.6 Artefactos y respaldos (3.7)

- **Inventario:** **85** directorios raíz (~700 MB) + `backups/` **239 MB**; `custom_addons` 52 MB.
  Detalle (tamaño/README/nº de respaldos) en el listado §2. Con README: 26 expedientes.
- **Clasificación:**
  - **CONSERVAR (evidencia canónica/única):** todos los expedientes `HOTFIX_*`, `CIERRE_*`, `BLINDAJE_*`,
    `RESET_*`, `SIMPLE_*`, `SAVE_*`, `UI_SAVE_*`, `CONTRATO_*`, `AUDIT_REBAJA_*`, `CONCILIACION_*`,
    `VERIF_*`, `DIAGNOSTICO_*`, `IMPL_*` (contienen diffs/logs/dumps no reproducibles).
  - **ARCHIVAR (comprimir + índice):** expedientes sin README y sólo logs pequeños (`AUDIT_*` de 2026-10-04,
    `UAT_*`, `FASE_B/C/D`); `_archive_pre_cleanup_*`.
  - **CANDIDATO A ELIMINAR (duplicado/regenerable):** **sólo** tras verificar unicidad: los `verify_unpatched`/
    `verify_apply` que repiten el árbol completo (p. ej. `FIX_GUIA_DUP_FINAL/verify_unpatched`,
    `verify_apply`), y `.pyc`/`__pycache__`. **Nada se elimina en Fase 1.**
- **Credenciales/datos personales:** `config/odoo.conf` contiene credenciales locales (esperado; **no** debe
  versionarse). Los documentos que "matchean" `password` son **ejemplos de comandos** (`--db_password=odoo`),
  no secretos reales. **No se reproduce ningún valor.**
- **Restaurabilidad:** cada expediente trae su `README`/`logs` y varios `db/*.dump`; se propone **verificar**
  (pg_restore --list, no restauración) antes de cualquier eliminación (**A4**).

### 4.7 Seguridad y consistencia (3.8)

| ID | Sev | Evidencia | Impacto | Acción propuesta | Riesgo | Reversible |
|---|---|---|---|---|---|---|
| H-SEC-1 | media | `core/security/ir.model.access.csv`: `access_madenat_guia_processing_manager` pasa **unlink 0→1** (jefatura) | **Cambio de permiso** en WIP | Confirmar autorización (**D15**) | Medio | Sí |
| H-SEC-2 | — | **Nueva** `ir.rule` multi-compañía para `sv.imputation{,.line,.sv.line}` (AUD-ETQ-07), **listada** en manifest | **Endurece** aislamiento | Mantener | Bajo | Sí |
| H-SEC-3 | media | `madenat.sv.imputation.write()` guarda **transiciones de estado**; una escritura **ORM/RPC** directa de campos **sin** `edit_version` **no** se compara (límite ya declarado) | Riesgo de sobrescritura por RPC | Documentar; decisión separada (**D16**) | Medio | — |
| H-SEC-4 | — | `stock.lot.unlink` con `_sv_guard_unlink()` (guarda proactiva) + traducción de FK | Protección presente | Verificación positiva | — | — |
| H-SEC-5 | baja | ACL `madenat.audit.log`: `group_system` CRUD; `group_user` lee+escribe; sin `ir.rule` de inmutabilidad | Bitácora no *append-only* por ACL | Evaluar `ir.rule` (sólo lectura/append) (**D17**) | Medio | Sí |
| H-SEC-6 | — | Métodos de transición privados `_i2_*` y de estado (`action_*`) con llamadores dentro del módulo; `write()` protege estados | Inventario coherente | Documentar (no cambia nada) | — | — |
| H-SEC-7 | baja | ACL rebaja-wizard: `oper/jef/ger` presentes para wizard y línea (verificado) | Coherente | — | — | — |

### 4.8 Profundización (2.ª pasada de 3.3/3.8) — verificaciones adicionales

| ID | Sev | Evidencia | Resultado |
|---|---|---|---|
| H-CODE-14 | — | Puntos **explicitados** por el encargo: `_i2_build_imputation`, `action_prepare`, `action_pending`, `action_apply`, `_i2_guarded_build`, `_i2_assert_edit_version` | **Verificación positiva (NO hay duplicación):** `action_prepare`/`action_pending`/`action_apply` **delegan** todas en `_i2_guarded_build()` → `_i2_build_imputation()` (única vía de construcción), que envuelve atomicidad + versión (`flush_all`, `SerializationFailure`→conflicto). Capas limpias. |
| H-CODE-15 | — | `_sv_guard_unlink` (`madenat_sv_operation.py:1292`) con bypass test-only | **Verificación positiva:** el "bypass" es `_sv_test_cleanup_allowed(...)`, que exige **token** de contexto **Y** `_sv_test_enable_strict()` (`--test-enable` real, **nunca** el parámetro de desarrollo); sin ambos ⇒ denegado. **Inerte** en producción y no accesible por RPC de negocio. |
| H-CODE-16 | — | Valores fijos/IDs/usuarios/compañías/rutas en `models`/`wizards` (grep) | **Verificación positiva:** **0** IDs/nombres/usuarios/compañías/rutas hardcodeados. Sólo constantes de dominio (`_PDF_SCAN_WINDOW=1024`, `5085.312`, `12000.0`, `1550.003` histórico) — legítimas. |
| H-CODE-17 | — | `madenat.sv.imputation.unlink()` (`:611`) y `write()` (`:498`) | **Verificación positiva:** `unlink` **prohíbe** `applied`/`reversed` ("historia append-only, AD-91"); `write` guarda **transiciones de estado** y eleva `edit_version`. Límite RPC-sin-`edit_version` ya declarado (H-SEC-3). |
| H-CODE-18 | — | `print`/`pdb`: sólo en `madenat_lumber_core/scripts/*` (utilidades CLI) | **No** hay `print`/`pdb` en código de modelos/wizards. |
| H-CODE-19 | — | `TODO/FIXME/XXX/HACK` en modelos: **0** (los matches son `# MÉTODOS …`/`TODO actor RPC` en prosa) | Sin marcadores técnicos pendientes. |

### 4.9 Referencias cruzadas (para decidir las deudas documentales, 3.6)

- **§17.16.19…§17.16.29** (02/INDICE, sin cuerpo): **26** referencias en total
  (19:5, 20:2, 21:4, 22–28:2 c/u, 29:3). → **Añadir los cuerpos no rompe ninguna**; **renombrarlos
  rompería 26**. Por eso sólo se propone RESTAURAR o ACEPTAR (D13).
- **`CANON/03` §5–§9 duplicadas:** **0** referencias cruzadas externas a esas 5 secciones concretas.
  Opciones: (i) renumerar **sólo** la 2.ª serie → **§31–§35** ⇒ **rompe 0**; (ii) desplazar §10–§30 → §15–§35
  ⇒ **rompe las referencias a §10–§30** (varias, p. ej. §15.6/§17.16/§22/§27–29). Se recomienda **(i)** por
  mínima, con la advertencia de orden cosmético (D12).

---

## 5. ACCIONES PROPUESTAS DE LIMPIEZA (numeradas; **NADA ejecutado**)

Etiquetas: **SEGURA** (no cambia comportamiento, reversible) · **REQUIERE_PRUEBAS** (toca código/tests) ·
**REQUIERE_DECISIÓN** (ambigua/impacto) · **NO_RECOMENDADA**.

| # | Acción | Qué se hace / archivos | Reversibilidad | Verificación | Etiqueta |
|---|---|---|---|---|---|
| **A1** | Respaldar antes de Fase 2 | `pg_dump -Fc madenat_test`, tar de filestore, tar de `custom_addons`, **`git bundle`/diff** del WIP → `code/` | N/A (crea artefactos) | `pg_restore --list` + `sha256` | **SEGURA** |
| **A2** | Cuarentena de huérfanos | Mover a `cuarentena/`: `shipping_core/models/shipping_models.py`, `logistics/wizards/lumber_consolidation_import_wizard.py` | Sí (mover, no borrar) | `git status`; smoke de módulos | **REQUIERE_DECISIÓN** |
| **A3** | Cuarentena de restos históricos | Mover `core/_archive/` y `docs/LEGADO/backups_modulos` a `cuarentena/` con índice | Sí | `git status`; grep 0 refs | **REQUIERE_DECISIÓN** |
| **A4** | Verificar restaurabilidad | `pg_restore --list` de cada `.dump` (sin restaurar) + `tar tzf` de cada `.tar.gz`; índice de unicidad | N/A (sólo lee) | Informe de restaurabilidad | **SEGURA** |
| **A5** | Archivar expedientes sin README | Comprimir + índice (sin borrar) los `UAT_*`/`AUDIT_*`(2026-10-04)/`FASE_*` | Sí | Índice de cuarentena | **REQUIERE_DECISIÓN** |
| **A6** | Eliminar duplicados verificados | `verify_unpatched/`+`verify_apply/` repetidos y `__pycache__`/`.pyc` | **No** (2.ª confirmación) | Diff 0 / ausencia de referencias | **REQUIERE_DECISIÓN** |
| **C1** | Retirar método muerto | Quitar `_i2_lock_sv_lots` (y su docstring) en `madenat_sv_imputation.py` | Sí (git) | Suite rebaja/logistics | **REQUIERE_PRUEBAS** |
| **C2** | Limpiar imports sin uso | Sólo en archivos del WIP (lista de `logs/unused_imports.out`) | Sí | `py_compile` + suites | **REQUIERE_PRUEBAS** |
| **D1** | Versionar C2 | `costing`: subir `version` + CHANGELOG del C2 | Sí | Manifest vs CHANGELOG | **REQUIERE_DECISIÓN** |
| **D2** | Normalizar versión billing | `madenat_lumber_billing` `1.0.0` → `18.0.1.0.0` | Sí | Odoo carga el módulo | **REQUIERE_DECISIÓN** |
| **D4** | Tests no listados | Registrar o declarar obsoletos `test_ingestion_gate`/`test_lot_costing` | Sí | `--test-tags` corre | **REQUIERE_DECISIÓN** |
| **T1** | Auditar suites con `commit()` | Revisar `tearDown`/`finally` de las 7 suites | N/A → fija residuos | Ejecución repetida sin residuo | **SEGURA** + **REQUIERE_PRUEBAS** |
| **D11** | 02 comentario duplicado | Renumerar `2026-10-10 (3)`→`(3),(4)` + cascada | Sí | Script de alineación | **REQUIERE_DECISIÓN** |
| **D12** | 03 secciones duplicadas | Renumerar 2.ª serie (§5–§9) → §31–§35 (opción (i)) | Sí | Script (**0 refs**) | **REQUIERE_DECISIÓN** |
| **D13** | §17.16.19…29 sin cuerpo | Restaurar cuerpos desde expedientes **o** aceptar como índice | Sí | Script (**26 refs intactas**) | **REQUIERE_DECISIÓN** |
| **D14** | Snapshots de docs | Añadir `SNAPSHOT.md` a cada copia en expedientes | Sí | Índice | **SEGURA** |
| **S1** | ACL unlink jefatura | Confirmar/ajustar `access_madenat_guia_processing_manager` | Sí | Prueba ACL | **REQUIERE_DECISIÓN** |
| **S2** | Inmutabilidad bitácora | Evaluar `ir.rule` de sólo-lectura/append sobre `madenat.audit.log` | Sí | Prueba ACL | **REQUIERE_DECISIÓN** |
| **DATA-1** | Usuarios de prueba | Dry-run + eliminar 3 usuarios `*@madenat.test` | Sí (backup) | Dry-run previo | **REQUIERE_DECISIÓN** |
| **DATA-2** | Auditorías con "test" | Revisar 11 filas; **no** borrar bitácora sin decisión | Sí (backup) | Listado exacto | **REQUIERE_DECISIÓN** |
| **—** | Tocar core de Odoo, ACL/`ir.rule` de `mail`, `-u all`, reparación histórica, borrado de evidencia única | — | — | — | **NO_RECOMENDADA** |

---

## 6. PROPUESTA DE SECUENCIA DE COMMITS (**NO ejecutada**)

> Orden: **docs → logistics → core → intake → costing**. Cada commit sólo añade/actualiza sus archivos.
> **Aviso:** `madenat_sv_imputation.py`, `lumber_container.py` y los `ir.model.access.csv` **mezclan**
> intervenciones ⇒ **no** se pueden partir sin cirugía de hunks; se asigna el archivo al commit de su
> intervención **dominante** y se documenta la mezcla. El bloque `costing-C2` **no** debe commitearse sin la
> decisión D1. El bloque `unknown` requiere revisión humana (D18).

| # | Mensaje | Archivos (grupos) | Módulo/versión | Pruebas que lo cubren | Dependencia |
|---|---|---|---|---|---|
| 1 | `docs(canon): alinea numeración/versiones y repara marcadores` | 8 `madenat_lumber_docs/*` (02,03,05,18,19,WIKI) | — (docs) | script `verify_doc_alignment.py` | — |
| 2 | `feat(logistics): hotfix chatter <chatter/> + pruebas VIEW` | `views/madenat_sv_imputation_views.xml`, `views/madenat_processor_return_link_views.xml`, `tests/test_hotfix_owl_chatter.py`, `tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md` | logistics 18.0.1.26.0 | `TestHotfixOwlChatter` (5) | 1 |
| 3 | `feat(logistics): rebaja de etiquetas SV (I2, blindaje, reset, LOCK, persistencia)` | `models/madenat_sv_imputation.py`, `wizards/*sv_imputation*`, `models/lumber_container.py`, `models/lumber_export_shipment.py`, `security/*`, `views/*`, `tests/test_sv_*` (≈45 archivos) | logistics | suites `test_sv_rebaja_*`, `test_rebaja_contenedor` | 2 |
| 4 | `feat(core): ledger SV, auditoría y guarda de lote (stock_quant FK)` | `models/{madenat_sv_operation,madenat_audit_log,stock_lot,madenat_guia_processing,lumber_reception,mixin_lumber_ingest,reception_parser,reception_workflow}.py`, `security/ir.model.access.csv`, `views/lumber_core_menu.xml`, `tests/*` (≈17) | core 18.0.6.7.0 | `test_sv_lot_unlink_guard`, `test_sv_*` | 3 |
| 5 | `feat(intake): guías (dup/delete/ciclo de vida) y consola` | `madenat_lumber_intake/**` | intake 18.0.0.13.0 | `test_intake_*`, `test_guide_lifecycle_*` | 4 |
| 6 | `feat(shipping): ajustes de motonave/viaje` + `fix(reports): menú` | `madenat_lumber_shipping_core/{models,views}`, `madenat_lumber_reports/views/lumber_reports_menu.xml` | shipping_core / reports | suites de embarque | 5 |
| 7 | **BLOQUEADO**: `feat(costing): C2 costeo de embarque` | `madenat_lumber_costing/**` | costing (**D1** pendiente) | `test_shipment_costing_c2` | decisión D1 |
| 8 | `chore(repo): cuarentena de huérfanos y restos históricos` | resultado de A2/A3/A6 | — | `git status` limpio | Fase 2 |

**No commiteable sin decisión:** bloque 7 (costing-C2), las 5 entradas de `desconocido` (§3.a), y cualquier
acción A6/eliminación (requiere 2.ª confirmación).

---

## 7. PENDIENTES QUE REQUIEREN DECISIÓN DE MAURICIO

| ID | Decisión requerida |
|---|---|
| **D1** | ¿Se consolida el `costing-C2` (subir versión + CHANGELOG) o se revierte? |
| **D2** | Normalizar `madenat_lumber_billing` `1.0.0` → `18.0.1.0.0`? |
| **D3** | Vistas legacy no listadas en manifests: ¿revisar/retirar una a una? |
| **D4** | Tests no listados (`test_ingestion_gate`, `test_lot_costing`): ¿registrar o declarar obsoletos? |
| **D5** | Suites con `commit()`: ¿exigir auditoría de `tearDown`/residuos? |
| **D6** | Cambios de aserción en 8 tests del WIP: ¿se aceptan como están? |
| **D7** | Eliminar los 3 usuarios de prueba inactivos (dry-run)? |
| **D8** | Auditorías con "test" (11): ¿revisar/anonimizar/no tocar? |
| **D9** | 147 lotes con `lot_flow_type` NULL: ¿saneamiento con dry-run? |
| **D10** | Fallas preexistentes: ¿corregir las 4 de código y aislar las 6 de entorno? |
| **D11** | 02: renumerar el comentario duplicado `2026-10-10 (3)` (+cascada)? |
| **D12** | 03: renumerar la 2.ª serie §5–§9 → §31–§35 (opción (i), 0 refs)? |
| **D13** | §17.16.19…29: restaurar cuerpos desde expedientes **o** aceptar como índice? |
| **D14** | Etiquetar las 19 copias de `madenat_lumber_docs` como snapshot? |
| **D15** | ACL: confirmar el `unlink` de jefatura en `madenat.guia.processing`? |
| **D16** | Límite ORM/RPC sin `edit_version`: ¿endurecer o documentar como límite? |
| **D17** | ¿`ir.rule` de inmutabilidad (append-only) sobre `madenat.audit.log`? |
| **D18** | Las 5 entradas `desconocido` del WIP: confirmar intervención/autoría. |
| **D19** | Autorizar la **FASE 2** (y qué acciones numeradas, una por una o por bloque). |

---

## 8. ENTREGABLES DE LA FASE 1 (evidencia, en `AUDITORIA_INTEGRAL_20261012/`)

- `README.md` (este informe).
- `code/`: `wip_status.txt`, `wip_tracked.diff`, `wip_tracked.diffstat.txt`, `wip_triage.tsv`,
  `triage_wip.py`, `audit_unused_imports.py`, `audit_manifests.py`.
- `logs/`: `unused_imports.out`, `manifests_hygiene.out`, `tests_init_check.out`, `changed_tests.diff`,
  `docs_alignment_recheck.out`.
- **No** se creó ni modificó ningún archivo del repositorio ni de los módulos; **no** se tocó la base ni el
  TEST remoto.

## 9. CRITERIO DE CIERRE (Fase 1)

- **Cada entrada del WIP clasificada y trazable** a una intervención ✅ (`code/wip_triage.tsv`, 104/104).
- **Hallazgos priorizados con evidencia**, sin acciones no aprobadas ✅.
- **Ninguna pérdida** de trabajo/evidencia/respaldo ✅ (solo lectura).
- **Sin cambios funcionales ni efectos físicos de stock** ✅.
- **Fallas preexistentes caracterizadas, no ocultadas** ✅ (§4.4, con baseline idéntico).
- **Documentación con numeración monótona** o ambigüedad declarada y decidible ✅ (§4.5/§4.9).
- **TEST remoto intacto** ✅.

> **FIN DE LA FASE 1 — SE DETIENE AQUÍ.** La FASE 2 no se inicia sin la autorización expresa (D19) indicando qué
> acciones numeradas se aprueban.
