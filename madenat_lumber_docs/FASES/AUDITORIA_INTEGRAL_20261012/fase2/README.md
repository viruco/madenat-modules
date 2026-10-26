# FASE 2 LIMITADA (rev. 2) — ENTREGA FINAL (higiene + H-SEC-1/D15 formalizada)

**Fecha:** 2026-10-12 · **Entorno:** repositorio + `madenat_test` LOCAL · **Sin commit/push/despliegue.**
**Orden ejecutado:** A1 → A4 → T1 → H-SEC-1 → H-SEC-5 → D14 → D13 → registro D15.
**Expediente:** `AUDITORIA_INTEGRAL_20261012/fase2/`.

## 1. Dictamen por acción
| Acción | Dictamen |
|---|---|
| **A1** respaldo completo y verificable | **EJECUTADA** (FAIL=0; prueba de restauración 104/104 por hash) |
| **A4** verificación de dumps | **EJECUTADA** (31/31 válidos; 31 hashes únicos) |
| **T1** auditoría de fixtures (solo revisión) | **EJECUTADA** (riesgo ALTO identificado: `TestDeleteConcurrency`) |
| **H-SEC-1 / D15** eliminación de guías | **EJECUTADA (análisis)**; guardas **PENDIENTES** |
| **H-SEC-5** inmutabilidad de bitácora (solo lectura) | **EJECUTADA (análisis)**; propuesta **PENDIENTE** |
| **D14** snapshots de documentación | **EJECUTADA** (canónica demostrada; 19 marcadores; 0 archivos alterados) |
| **D13** cuerpos §17.16.19…§17.16.29 en CANON/02 | **CORREGIDA** (11/11 literales; 0 refs sin resolver) |
| **Registro D15** en la documentación | **EJECUTADA** (AD-103 en `04_DECISION_LOG.md`) |

**No aprobadas ⇒ no ejecutadas:** A2, A3, A5, A6, C1, C2, D1, D2, D4, D11, D12, S1, S2, DATA-1, DATA-2; ni
eliminaciones/movimientos/renombres ni datos reales.

## 2. A1 — respaldo (manifiesto, hashes, restauración)
Artefactos en `backups/` (sha256 en `backups/SHA256SUMS.txt`, verificado OK):
`custom_addons_worktree_full.tar.gz` (9.4 M, **905** entradas, **incluye los 37 nuevos**),
`wip_tracked_HEAD.diff` (10.995 líneas), `untracked_list.txt` + `untracked_sha256.txt` (**37**),
`repo_history_all.bundle` (3.1 M, «complete history»), `madenat_test_pre_fase2.dump` (11 M, `pg_restore --list`
OK, 13.428 líneas), `filestore_pre_fase2.tar.gz` (104 M), `odoo_conf_keys_only.txt` (18 claves, **sin valores**).
- `gzip -t` OK en ambos tar.gz; **los 37 nuevos presentes**.
- **Prueba de restauración:** extracción en `/tmp/fase2_restore_test` (nuevo) y comparación de hashes con el
  manifiesto previo ⇒ **104/104 coinciden, 0 mismatches**; directorio temporal eliminado. **No** se restauró la base.

## 3. A4 — dumps (`logs/a4_dumps.tsv`)
**31 dumps**, **31 válidos** (`pg_restore --list` sin error), **31 hashes únicos** (ninguna copia duplicada ⇒
cada una es **única**). Tablas clave `stock_lot`/`stock_quant` presentes en **todos**; `madenat_sv_imputation`
ausente solo en los 4 más antiguos (2026-08-21 y 2026-10-01/02), anteriores al modelo. **Ninguno se restauró
ni modificó**; no hay inválidos.

## 4. T1 — fixtures (`docs/T1_fixtures.md`)
7 suites revisadas. **6 con `tearDownClass`** que borra lo creado (riesgo Bajo-Medio, condicionado a que el
proceso no muera). **1 sin limpieza: `test_guide_lifecycle_phase2.TestDeleteConcurrency`** ⇒ **riesgo ALTO**;
residuo empírico confirmado: **7× «P Conc Fase 2»** (+1 «Proveedor TEST MADENAT», 3 usuarios `@madenat.test`,
11 auditorías «test»). **No** se corrigió ningún test.

## 5. H-SEC-1 / D15 (`docs/H_SEC_1_FICHA.md`)
- ACL: `madenat_lumber_core/security/ir.model.access.csv:28`, jefatura, `unlink 0→1` (modifica línea previa).
- Eliminación hoy: estado draft/cancelled + `stock.group_stock_manager`; luego CASCADE (líneas/rels/wizards),
  RESTRICT (SV ops, imputaciones, return-links, lotes de volumen) y SET NULL (lotes, pickings, recepciones,
  **bitácora**).
- **Dinámico (11 escenarios a–g + variantes, rollback, 0 residuo):** (a,b,c,g,j) éxito; (**d**) **éxito ⚠️**
  borra con **lotes con existencias** y los deja sin vínculo; (**e,f**) **error técnico de FK**; (**h**) estado
  → negocio ✅; (**i2**) **sin jefatura → ACL rechaza** ✅; (**i**) la guarda de stock-manager **enmascara** el ACL.
- **Trazabilidad:** la vía asistente audita; la vía **`unlink` directa NO** (brecha).
- **Guardas:** propuestas, **REQUIERE_DECISIÓN**, **no implementadas**.

## 6. H-SEC-5 (`docs/H_SEC_5_analisis.md`)
ACL: `group_user` (read+create, **sin write**), `group_system` (**write+unlink**), `group_madenat_auditoria`
(read). **Sin `ir.rule`**; **sin** guarda de `write`/`unlink` en el modelo. **34** puntos de escritura.
Afirmaciones canónicas de «bitácora inmutable/append-only» (AD-47, AD-79, D-I2-15) **no** garantizadas
técnicamente. **Propuesta** (bloquear write/unlink + `ir.rule` + matizar enunciados), **sin implementar**.

## 7. D14 — snapshots (`docs/D14_snapshots_index.md`)
**20** copias de `madenat_lumber_docs`; **canónica demostrada:** `custom_addons/madenat_lumber_docs`
(INDICE 12.29.0, sha256 `7332c6eaf8fc`, 218 archivos; única bajo `.git` y referenciada por los módulos).
Índice con fecha/INDICE/sha/difs por copia. **19 `SNAPSHOT.md` añadidos** (marcador definido por D14);
**verificación por hashes: 3.445 archivos existentes, 0 cambios** (`logs/d14_prehashes.txt` = posthashes).

## 8. D13 — cuerpos §17.16.19…§17.16.29 (`docs/D13_verificacion.md`)
**11/11** secciones insertadas **literalmente** desde los expedientes (mapeo con ruta exacta), en su posición
numérica. **0** referencias sin resolver. Versiones `02` 12.39.0 → **12.40.0**; índice 12.29.0 → **12.30.0**.
Marcadores balanceados. **Diff de la sesión: solo añadidos** + las 5 líneas de versión/fecha exigidas.

## 9. Registro D15
`CANON/04_DECISION_LOG.md` → **AD-103 (2026-10-12)**: jefatura puede eliminar `madenat.guia.processing` por
higiene de la base; permiso como **política**; **no** autoriza borrado de datos reales; guardas **pendientes**;
riesgo residual declarado. Versión `04` 12.18.0 → **12.19.0**.

## 10. Nada fuera del alcance cambió (evidencia)
- **`git status`:** **104 → 105** entradas (solo aparece `04_DECISION_LOG.md`, autorizado por D15).
- **Hashes del WIP:** **cambiados** = `02_CONTINUIDAD.md`, `INDICE_DOCUMENTACION.md`; **nuevo** = `04_DECISION_LOG.md`;
  **desaparecidos = 0**; **los otros 102 archivos, byte a byte idénticos** (`code/wip_sha256_{before,after}.txt`).
- **Base local:** sin residuo (guías/socios/movimientos `13/76/166` antes y después; rollback de la Parte B).
- **No** se tocó código, tests, vistas, manifests, ACL, ir.rule, datos de negocio, IMP04823/IMP02220, core ni
  TEST remoto. **No** hay archivos nuevos dentro de `custom_addons` (los `SNAPSHOT.md` y este expediente viven
  fuera del repo).

## 11. Pendientes y decisiones para Mauricio
1. **Guardas H-SEC-1** (§5): bloquear borrado con existencias; traducir FK a negocio; auditar la vía directa.
2. **H-SEC-5:** decidir bloqueo de `write`/`unlink` de la bitácora + `ir.rule`.
3. **T1:** decidir limpieza de `TestDeleteConcurrency` y saneamiento (dry-run) de los residuos.
4. **A4:** decidir si se propone una restauración de prueba (base temporal) de algún dump.
5. Mantener las acciones **no aprobadas** sin ejecutar (A2/A3/A5/A6/C1/C2/D1/D2/D4/D11/D12/S1/S2/DATA-*).

## 12. Secuencia de commits (actualizada, **NO ejecutada**)
1. `docs(canon): D13 restituye §17.16.19..29 + D15 AD-103` (02, INDICE, 04).
2. `docs(fase2): expediente de higiene` (este expediente).
3. (ya propuestos en Fase 1) `feat(logistics) chatter` → `feat(logistics) rebaja` → `feat(core)` →
   `feat(intake)` → `feat(shipping/reports)`; **BLOQUEADO**: `feat(costing)` (D1), y el **ACL de intake**
   **no** debe desplegarse sin las guardas H-SEC-1.

## 13. Criterio de cierre (Fase 2)
- WIP recuperable demostrado con hashes ✅ · dumps verificados y copias únicas identificadas ✅ · riesgos de
  residuo caracterizados ✅ · eliminación de guías caracterizada por escenario ✅ · guardas propuestas **sin
  implementar** ✅ · bitácora analizada con propuesta ✅ · fuente canónica demostrada y §17.16.19..29 presentes
  sin romper referencias (32/32) ✅ · decisión D15 registrada (AD-103) ✅ · **nada fuera del alcance modificado** ✅.

**SIN COMMIT. SIN PUSH. SIN DESPLIEGUE REMOTO. SIN CONEXIÓN AL REMOTO. SIN REPARACIÓN HISTÓRICA. SIN
ELIMINACIÓN DE DATOS REALES NI DE ARCHIVOS.**

