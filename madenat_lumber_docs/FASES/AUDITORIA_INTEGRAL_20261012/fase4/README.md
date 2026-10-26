# FASE 4 — Cierre de brechas de seguridad (H1–H7) y saneamiento local

**Proyecto:** MADENAT — Odoo 18 CE · **Entorno:** repo local + `madenat_test` LOCAL (contenedor `odoo18_app`)
**Fecha:** 2026-10-12 · **Alcance autorizado:** H1–H7 · **NO ejecutado:** S1/S2, A2/A3/A5/A6, C1/C2, D1/D2/D4,
D11/D12, DATA-1/2, commit, push, despliegue, `-u all`, borrado de archivos o de datos reales.

## 0. Resumen ejecutivo

| # | Acción | Dictamen |
|---|--------|----------|
| H1 | Motivo obligatorio en la vía directa | **IMPLEMENTADO** (vía nativa bloqueada con mensaje; 1 regresión real detectada y cerrada) |
| H2 | Accesibilidad del permiso de jefatura | **IMPLEMENTADO** (rol jefatura/sistema en una única función; sin tocar permisos de stock) |
| H3 | H-SEC-5 mínimo (inmutabilidad de la bitácora) | **IMPLEMENTADO** con **límite SQL/DBA declarado**; defensa adicional propuesta, **no implementada** |
| H4 | Prueba dedicada del escenario (f) de costos | **IMPLEMENTADO** (bloqueo con mensaje de negocio + control positivo) |
| H5 | Saneamiento local de residuos (con simulación) | **EJECUTADO** (48 socios; 0 guías candidatas; bitácora y usuarios conservados) |
| H6 | Fixtures `test_sv_rebaja_*` sin residuo `*_oper` | **IMPLEMENTADO** (3 suites; 2 ejecuciones consecutivas sin residuo nuevo) |
| H7 | Documentación | **REGISTRADA** (AD-105, CHANGELOGs, manifests, INDICE, este expediente) |

**Invariante probada:** *eliminar una guía exige motivo explícito por cualquier vía; solo jefatura (o sistema)
puede; la bitácora no se altera ni borra por ORM, ni con `sudo`* · **0 fallas nuevas** en la regresión.

## 1. Investigación (regla de oro, pasos 1–3)

- **Llamadores de `unlink()` de guía** (producción): el propio `unlink()` del core (guarda única), el asistente
  de ciclo de vida (`intake_guide_lifecycle_wizard`, 2 llamadas con motivo) y el **asistente de reclasificación
  AD-73** (`intake_reclassify_wizard.action_confirm_reclassify`) — este último **no aportaba motivo** (ver §2).
  No hay botones/acciones XML ni JS propios que borren guías: el botón nativo de lista/formulario usa el
  `unlink()` estándar **sin** motivo.
- **Grupos:** `group_madenat_jefatura_operaciones`, `group_madenat_operaciones`, `group_madenat_auditoria`.
  Verificado en BD: `uid 1` (superusuario de tests) **tiene** `base.group_system` y `stock.group_stock_manager`
  pero **no** jefatura; `uid 2` (admin) tiene system + jefatura + operaciones + stock_manager.
- **Bitácora:** ningún código de producción hace `write()` sobre `madenat.audit.log`; las únicas mutaciones son
  **borrados** de limpieza test-only (`_sv_test_cleanup_token`) y SQL directo en fixtures.
- **Causa raíz del residuo `*_oper`:** `res.users.create` genera un `res.partner` homónimo que **no** se elimina
  al borrar el usuario; los `tearDownClass` borraban el usuario pero no su socio.

## 2. H1 — Motivo obligatorio en la vía directa

- Se **elimina el valor por defecto** («sin motivo declarado») introducido en la FASE 3.
- Sin `madenat_guia_delete_reason` no vacío ⇒ `UserError` de negocio que **guía al asistente**.
- **Decisión de UI:** la eliminación nativa (lista/formulario) queda **bloqueada con mensaje** — opción elegida
  por ser la que **menos cambia las vistas** (no se modifican botones, acciones, menús ni formularios).
- **Regresión real detectada y cerrada:** `TestIntakeReclassifyWizard.test_01_reclassify_guia_draft_success`
  falló en la primera regresión (6 failed / **5** error de 1448): el asistente AD-73 borraba la guía sin motivo.
  Corrección: aporta su **propio motivo de negocio** («Reclasificación de tipo de ingreso (AD-73): X → Y»), no un
  valor por defecto. Tras el arreglo: **7/7** en verde y la regresión vuelve a 6 failed / 4 error.
- Una sola guarda central y **un solo** registro de bitácora por eliminación (contexto
  `madenat_guia_delete_logged` para el asistente).

## 3. H2 — Rol autorizado (jefatura) en lugar del grupo técnico

- Nueva constante `GUIA_DELETE_GROUPS = (jefatura_operaciones, base.group_system)` y **única** función
  `_guia_delete_group_ok()`, reutilizada por `unlink()`, `_cleanup_orphan_moves_guia()` y
  `_delete_access_blocker()` del asistente.
- Se retira la exigencia de `stock.group_stock_manager` (**no** se añadió jefatura al grupo de stock; **no** se
  crean grupos ni se amplían permisos de Inventario).
- Matriz probada: jefatura **sí**; operaciones, auditoría, usuario interno, otra compañía sin jefatura y
  `stock_manager` **sin** jefatura **no**.

## 4. H3 — H-SEC-5 mínimo (bitácora APPEND-ONLY)

- `write()` y `unlink()` de `madenat.audit.log` lanzan `UserError` de negocio **también con `sudo()`** y para el
  grupo de sistema. Excepción **única test-only**: token **vivo** `madenat_sv_test_cleanup_token` +
  `--test-enable` **real** + BD de test (un token arbitrario **no** habilita nada).
- ACL: `access_madenat_audit_log_manager` pasa de `1,1,1,1` a **`1,0,1,0`**; `create`/`read` se conservan.
- La limpieza test-only del ledger (`madenat_sv_internal`) aporta el token (mismo patrón inerte) — sin ella la
  propia limpieza de pruebas se habría roto.
- **Migración:** no requiere datos ni scripts; solo modelo + ACL (aplicado con `-u` de los módulos afectados).
- **Límite honesto:** **no** impide `UPDATE`/`DELETE` por **SQL directo** ni por un **DBA**. Defensa adicional
  **propuesta y NO implementada**: trigger de BD que rechace `UPDATE`/`DELETE`, o **hash encadenado**.
  Las correcciones se registran siempre como **eventos NUEVOS**.

## 5. H4 / H6 / H5

- **H4 — escenario (f):** guía con lote que tiene `stock.lot.cost.line` ⇒ bloqueo con mensaje de negocio
  («No se puede eliminar la guía … coste»); sin costes ⇒ eliminación permitida. El bloqueo no deja bitácora.
- **H6 — fixtures:** `test_sv_rebaja_reset_concurrency`, `test_sv_rebaja_reset_lot_capacity` y
  `test_sv_rebaja_save_lock_tx` eliminan ahora **por IDs explícitos** el socio de sus usuarios de prueba y la
  bitácora de su propia ejecución (`batch_id` de guía / clave documental — la FK queda a `NULL` al borrar la
  guía, por lo que el borrado por FK no encontraba el registro).
- **H5 — saneamiento local (solo `madenat_test`):** simulación previa con `savepoint` + rollback
  (`docs/H5_saneamiento_script.py`, `H5_MODE=dry` por defecto) y ejecución **por IDs explícitos**, uno a uno.

## 6. Pruebas y regresión

| Prueba | Resultado | Log |
|--------|-----------|-----|
| H1/H2/H3 (guards + ACL + inmutabilidad) | **0 failed / 0 error of 36** | `logs/f4_run2.log` |
| Reclasificación AD-73 (tras el arreglo H1) | **0 failed / 0 error of 7** | `logs/f4_rec.log` |
| Regresión 1 (antes de arreglar AD-73) | 6 failed / **5** error of 1448 | `logs/f4_reg1.log` |
| **Regresión final** `core+intake+logistics` | **6 failed / 4 error of 1448** | `logs/f4_reg2.log` |
| Baseline FASE 3 (misma invocación) | 6 failed / 4 error of 1297 | `../fase3/logs/regression_core_intake_logistics.log` |

**Conjunto de fallas: IDÉNTICO (10/10)** — `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos`,
`TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive`,
`TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen`,
`TestSvEscalationSecurity.test_02/03/04`, `TestProcessorLocations.test_09_auditoria_envio_normal`,
`TestProcessorShipmentAD89.test_t1/t5/t6` ⇒ **0 fallas nuevas**.

*Nota de conteo:* 1297 → 1448 (+151) = **+17 pruebas nuevas** (intake +12, core +5) más **+134** de módulos
dependientes (`madenat_ingestion_engine` 96, `madenat_lumber_costing` 38, `madenat_lumber_purchasing` 21,
`madenat_lumber_billing` 11) que la invocación de la FASE 3 no ejecutó; ninguno aportó fallas nuevas.

### Matriz antes/después (comportamiento)

| Escenario | Antes (FASE 3) | Después (FASE 4) |
|-----------|----------------|------------------|
| `unlink()` directo sin motivo (jefatura) | eliminaba con «sin motivo declarado» | **bloqueado** (`UserError`, guía al asistente) |
| Botón nativo de lista/formulario (sin motivo) | eliminaba con motivo por defecto | **bloqueado con mensaje** |
| Asistente Modo A / ciclo de vida | eliminaba (con motivo) | eliminaba (con motivo) — **igual** |
| Reclasificación AD-73 | eliminaba con motivo por defecto | eliminaba con **motivo de negocio propio** |
| `unlink()` con `stock_manager` y sin jefatura | permitido (guarda técnica) | **bloqueado** (rol jefatura/sistema) |
| `write()`/`unlink()` sobre la bitácora (ORM o `sudo`) | permitido | **bloqueado** (`UserError` APPEND-ONLY) |
| ACL `write`/`unlink` de la bitácora (sistema) | `1,1,1,1` | **`1,0,1,0`** |
| Lote con línea de coste (escenario f) | bloqueo indirecto | **bloqueo directo probado** |

## 7. Saneamiento H5 (solo `madenat_test` local)

| Grupo | Antes | Acción | Después |
|-------|-------|--------|---------|
| 8 socios nombrados (`Proveedor TEST MADENAT` + 7 × «P Conc Fase 2») | 8 | eliminados por ID (sin dependientes) | **0** |
| Socios `*_oper` (homónimos de usuarios de prueba) | 40 | eliminados por ID (sin dependientes) | **0** |
| Guías con nombre de prueba (draft/cancelled) | **0** | nada que eliminar | **0** |
| Usuarios `@madenat.test` inactivos | 3 | **NO** eliminados (documentados) | 3 |
| Auditorías con «test» (historia) | 11 | **CONSERVADAS** | 11 |
| Bitácora total | 332 | −5 residuo `G3-CONC` de ejecuciones previas (limpiado por la fixture corregida) | **327** |
| Guías / recepciones / usuarios / lotes | 13 / 8 / 12 / 151 | intactos | **13 / 8 / 12 / 151** |

Verificación de fixtures (H6) en dos ejecuciones consecutivas de las 4 clases con commit:
**A: 0/0 de 10 → socios `*_oper` = 0, bitácora 327**; **B: 0/0 de 10 → socios `*_oper` = 0, bitácora 327**
(sin residuo nuevo). Post-verificación en `logs/h5_post_verificacion.log`.

## 8. Alcance (nada fuera de lo autorizado)

`code/cambiados.txt`: **18 archivos modificados** + **1 nuevo** + 3 que pasaron de limpios a modificados —
todos dentro del alcance (core, intake, logistics-test, CANON 04/INDICE, CHANGELOGs y manifests). Los **96**
archivos restantes del WIP conservan su SHA-256 **byte-idéntico** (`wip_sha256_before` vs `wip_sha256_after`).
Sin `git commit`, `push`, `checkout`, `reset`, `stash`, `rebase` ni cambio de rama; TEST remoto intacto.

## 9. Riesgos residuales

1. **SQL/DBA (declarado):** la bitácora sigue siendo alterable por SQL directo; la defensa (trigger / hash
   encadenado) está **propuesta y no implementada**.
2. **`madenat.guia.processing` no tiene `company_id` ni `ir.rule` de compañía:** un usuario **con jefatura** de
   otra compañía podría eliminar (probado que **sin** jefatura se bloquea). Requiere decisión.
3. **Suites de concurrencia con COMMIT real:** su limpieza se apoya en `batch_id` (la FK queda a `NULL`), lo que
   se documenta como parte de la técnica de fixtures.
4. **Baseline no idéntico en invocación:** el conteo absoluto de pruebas depende de qué módulos actualiza `-u`;
   la comparación válida es el **conjunto de fallas** (idéntico).

## 10. Pendientes y decisiones para Mauricio

- ¿H-SEC-5 se amplía con **trigger de BD** o **hash encadenado** (bloqueado, requiere autorización)?
- ¿Se añade `company_id` / `ir.rule` a `madenat.guia.processing`?
- ¿Se generaliza la limpieza de bitácora de pruebas a **todas** las suites que commitean?
- ¿Se limpian los **3 usuarios** `@madenat.test` inactivos (hoy solo documentados)?

## 11. Secuencia de commits propuesta (SIN ejecutar)

1. `core`: H1 motivo obligatorio + H2 rol jefatura + H3 bitácora APPEND-ONLY + ACL + CHANGELOG/manifest
   18.0.6.9.0 + suites.
2. `intake`: H1/H2 asistente + motivo AD-73 + suites + CHANGELOG/manifest 18.0.0.15.0.
3. `logistics`: H6 fixtures + CHANGELOG/manifest 18.0.1.27.0.
4. `docs`: AD-105, INDICE 12.32.0, expediente `fase4/`.

**Desbloqueado:** el ACL de `intake` (la eliminación ya exige rol, motivo y trazabilidad) y el cierre de la
brecha H-SEC-5 mínima. **Sigue bloqueado:** trigger/hash de la bitácora, aislamiento por compañía y despliegue
remoto (TEST remoto intacto).
