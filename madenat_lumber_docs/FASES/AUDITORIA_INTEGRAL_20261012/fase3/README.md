# FASE 3 — Guardas de eliminación (G1) y saneamiento de fixtures (T1) — ENTREGA

**Fecha:** 2026-10-12 · **Entorno:** repositorio + `madenat_test` LOCAL · **Sin commit/push/despliegue.**
**Respaldo previo:** `fase3/backups/` (tar del WIP + diff + `pg_dump` + `SHA256SUMS.txt`).
**Expediente:** `AUDITORIA_INTEGRAL_20261012/fase3/`.

## 1. Aclaraciones de la Fase 2 (solo lectura)
1. **D13 «CORREGIDA».** Se **restituyeron** los cuerpos de `02` §17.16.19…§17.16.29 (antes solo citados) por
   transcripción **literal** desde expedientes. **Cuándo:** Fase 2 (2026-10-12). **Por qué:** el changelog los
   citaba sin cuerpo. **Diff:** `fase2/logs/diff_session_docs.diff` → **solo líneas `+`** de encabezados/cuerpos.
2. **«18→19..29→30»: NO hubo renumeración.** Comparación de encabezados pre/post (`comm -23` = vacío): ningún
   encabezado existente desapareció; **solo** se añadieron §17.16.19..29 (y ya existían 17.16.18 y 17.16.30).
3. **Referencias 26 vs 32: diferencia explicada.** La Fase 1 contó ~26 con un patrón **sin `§`**
   (`17\.16\.(19|2[0-9])`); la verificación de Fase 2 usa `§17\.16\.(19|2[0-9])` y da **32** (PRE=27 → POST=32;
   el +5 proviene del comentario de changelog añadido). La cifra de la Fase 1 era **aproximada**; la canónica
   verificada es **32/32 resueltas**.
4. **D14: el marcador SÍ está definido.** README Fase 1, línea 266:
   «`| **D14** | Snapshots de docs | Añadir \`SNAPSHOT.md\` a cada copia en expedientes | … |`». Se añadieron
   **19** `SNAPSHOT.md` (fuera del repo); **no** se retiran.
5. **H-SEC-1 (i) — jefatura NO implica `stock.group_stock_manager`.** El grupo `group_madenat_jefatura_operaciones`
   (id 261) solo implica «Operaciones» (256) e «Internal User» (1) ⇒ **el `unlink` del ACL es inalcanzable con
   jefatura a secas**: la guarda `_cleanup_orphan_moves_guia` exige `stock_manager`. Los **usuarios** uid 2
   (Mauricio) y 8 (Cristhian) **sí** tienen stock_manager; el usuario de prueba `v3_concil_jef` (2975) **no**.
   **Opciones (sin implementar):** (a) añadir jefatura al grupo stock_manager; (b) cambiar la guarda;
   (c) dejar solo el ACL. **Ninguna revela cambio no autorizado.**

## 2. G1 — Guardas de eliminación (`docs/G1_diseno_pruebas.md`)
- **Investigar (4.1):** `unlink()` único en core; llamadores = asistente + vías directas; bypass test-only
  intacto.
- **Diseño (4.2):** guarda única en `unlink()` → `_guia_deletion_blockers()` (D-G1), **mensaje de negocio**
  (D-G2) con alternativas, **motivo + bitácora** (D-G3) y **borrado controlado de lotes vacíos** (sin
  huérfanos). Asistente comparte guarda y **no duplica** bitácora.
- **Impacto (4.4/5):** **0 fallas nuevas** frente al baseline (ver §4).

## 3. G2 — Fixture T1 (`test_guide_lifecycle_phase2.TestDeleteConcurrency`)
- **Antes:** `setUpClass` publicaba socio + guía y **no había limpieza** ⇒ 7 socios «P Conc Fase 2» residuales.
- **Después:** `tearDownClass` que borra **solo** lo creado (ids de la clase: guía + socio + auditoría), y
  `test_99_cleanup_guia` pasa a limpieza **por ID (SQL)** (la guarda G1 bloquea el borrado de una guía con
  dependencias; el cleanup de la suite no es una operación de negocio).
- **Demostración:** **2 ejecuciones consecutivas** con `0 failed / 0 error of 3` cada una y conteos idénticos
  (`res_partner/guia/moves = 76/13/166`; «P Conc Fase 2» = 7 **sin cambios**) ⇒ **sin residuo nuevo**.

## 4. Pruebas y regresión (4.3/4.4)
- **Pruebas nuevas** (`tests/test_guia_delete_guards.py`, escenarios a–m): **0 failed / 0 error of 13**
  (`logs/g1_tests.log`, EXIT 0). Antes de la guarda habrían fallado en **d** (borraba con existencias),
  **e/f** y **g** (error técnico de FK) — según la corrida dinámica de Fase 2.
- **Regresión `core+intake+logistics`:** **6 failed / 4 error of 1297** (baseline Fase 1: **6/4 de 1284**);
  conjunto de fallas **IDÉNTICO** (10/10, `logs/regression_failures.txt` vs baseline) ⇒ **0 fallas nuevas**.
- **Base local:** sin residuo **de la Fase 3** (`res_partner/guias/moves` y «P Conc Fase 2» = 7 sin cambios).
  Se observaron **4 socios** nuevos (`conc_oper`, `p1_oper`, `v3_oper`, `v3_oper`) provenientes de suites
  **preexistentes** de concurrencia (`test_sv_rebaja_reset_concurrency`, `reset_lot_capacity`, `save_lock_tx`):
  **demostrado** ejecutando `TestSvRebajaSaveLockTxConcurrency` aislado (deja **+1** socio por sí sola). Se
  añaden al dry-run G4; **no** son atribuibles a la Fase 3.

## 5. T1 — fixture (G2)
Ver §3. Antes (residuo) → después (sin residuo nuevo), con 2 corridas consecutivas. La suite preexistente
`TestDeleteConcurrency` pasó de **1 error** (al introducir la guarda) a **0 fallas** tras ajustar su limpieza.

## 6. G4 — dry-run de residuos (`docs/G4_dryrun_residuos.md`, solo lectura)
Socios «P Conc Fase 2» (×7) + «Proveedor TEST MADENAT» (×1) = **8 socios sin dependientes** (borrado seguro);
**3 usuarios** `@madenat.test` inactivos; **11** auditorías con motivo «test» (**historia → conservar**);
**6** guías con nombre de prueba. Script de **simulación** propuesto; **limpieza NO ejecutada** (autorización
aparte).

## 7. Documentación (G3)
- `CANON/04_DECISION_LOG.md` → **AD-104** (D-G1..D-G4 + H-SEC-5 sigue pendiente); versión 12.19.0 → **12.20.0**.
- `CANON/INDICE_DOCUMENTACION.md` → versión 12.30.0 → **12.31.0**.
- `CHANGELOG.md` de `madenat_lumber_core` (**18.0.6.8.0**) y `madenat_lumber_intake` (**18.0.0.14.0**).
- Expediente `fase3/` (este informe + diseño/matriz + dry-run + logs + backups).

## 8. Nada fuera del alcance cambió
Diff de la sesión (vs respaldo A1 de Fase 3): **10 modificados + 1 nuevo** —
`core/{CHANGELOG.md,__manifest__.py,models/madenat_guia_processing.py}`,
`intake/{CHANGELOG.md,__manifest__.py,models/intake_guide_lifecycle_wizard.py,tests/__init__.py,tests/test_guide_lifecycle_phase2.py}`,
`docs/CANON/{04_DECISION_LOG.md,INDICE_DOCUMENTACION.md}`, y **nuevo** `intake/tests/test_guia_delete_guards.py`.
**Ningún** otro archivo del WIP cambió (hashes); **sin** cambios en datos reales, core de Odoo, otros módulos
ni TEST remoto. `git status`: 105 → **106** (solo el archivo nuevo).

## 9. Riesgos residuales
1. **Brecha H-SEC-5** (D-G4): la bitácora `madenat.audit.log` **sigue siendo alterable** (write para
   `group_system`; sin `ir.rule`) ⇒ el registro de eliminaciones **no es inmutable por garantía técnica**.
2. **Motivo en la vía directa** por defecto (compatibilidad) ⇒ D-G3 es estricto sólo vía asistente.
3. **Cobertura de costos (f)** indirecta.
4. **Residuo de suites preexistentes** (`*_oper` socios) — ajeno a la Fase 3; propuesto para G4.

## 10. Pendientes / decisiones para Mauricio
1. Endurecer el **motivo obligatorio** en la vía directa (implica actualizar un test existente).
2. **H-SEC-5**: bloqueo de `write`/`unlink` de la bitácora + `ir.rule`.
3. Aprobar la **limpieza real** de residuos (G4) y de los socios `*_oper`.
4. Prueba dedicada para **costos (f)**.
5. ACL: jefatura NO implica stock_manager (opciones a/b/c de §1.5).

## 11. Secuencia de commits (NO ejecutada)
1) `docs(canon): AD-104 guardas G1/G2` (04, INDICE) → 2) `feat(core): guardas de eliminación de guía`
(core: modelo+manifest+CHANGELOG) → 3) `feat(intake): comparte guarda + fixture G2 + tests a–m`
(intake: wizard+manifest+CHANGELOG+tests) → 4) `docs(fase3): expediente de guardas`.
**BLOQUEADO**: el **ACL de intake** no debe desplegarse sin las guardas (ya presentes) y sin resolver H-SEC-5.

## 12. Criterio de cierre
Aclaraciones resueltas ✅ · eliminar con existencias/dependencias **bloqueado con mensaje de negocio (sin FK
técnica ni lotes sin vínculo)** ✅ · toda eliminación permitida deja registro con motivo; directa y asistente
comparten guarda ✅ · fixture T1 sin residuo nuevo; limpieza real propuesta, no ejecutada ✅ · **0 fallas
nuevas** vs baseline ✅ · documentación al día, versiones monótonas ✅ · nada fuera del alcance modificado ✅.

**SIN COMMIT · SIN PUSH · SIN DESPLIEGUE REMOTO · SIN CONEXIÓN AL REMOTO · SIN ELIMINACIÓN DE DATOS REALES NI
DE ARCHIVOS · SIN `-u all`.**
