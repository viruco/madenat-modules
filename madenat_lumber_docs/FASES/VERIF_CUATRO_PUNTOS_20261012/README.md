# VERIFICACIÓN PROBATORIA DE CUATRO PUNTOS DE BLINDAJE — ENTREGA (2026-10-12)

**Entorno:** `madenat_test` **LOCAL** (`odoo18_app` / `odoo18_db`) · **Docs:** `madenat_lumber_docs`
**Regla cumplida:** **SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA.**

---

## 1. Dictamen por punto

| Punto | Dictamen | Resumen |
|---|---|---|
| **P1** — concurrencia sobre la MISMA etiqueta retornada | **ACREDITADO** | El mecanismo (advisory lock + revalidación de capacidad) ya lo garantiza; **sin cambio de código**. |
| **P2** — recomputación real de intake | **CORREGIDO Y ACREDITADO** | Defecto confirmado (caché obsoleta en el MISMO entorno) → corrección por invalidación dirigida. |
| **P3** — saldos almacenados vs derechos del usuario | **CORREGIDO Y ACREDITADO** | Defecto confirmado (`compute_sudo=False` → `AccessError`/dependencia del usuario) → `compute_sudo=True` en los canónicos. |
| **P4** — aislamiento y limpieza de la autorización | **CORREGIDO Y ACREDITADO** | Defecto confirmado (token global sin identidad de transacción) → vía privada de transición. |

## 2. Baseline y respaldos
- **Repositorio/rama/HEAD:** `custom_addons/.git` · `feat/guia-correccion-documental-preservada-20261002` ·
  `b1d2d1911648f3264bf629c8eccf79a1c140eaf3` (sin cambios al cierre ⇒ **sin commit**).
- **Base y conexión LOCAL:** `madenat_test` (contenedor `odoo18_db`); **confirmado**: se operó solo contra la
  base local (el TEST remoto **no** se tocó).
- **Versiones antes:** `madenat_lumber_logistics 18.0.1.22.0`, `madenat_lumber_intake 18.0.0.12.0`,
  `madenat_lumber_core 18.0.6.6.0`.
- **Respaldos reales previos:** `code/` (diff + pre-copias), `db/madenat_test_pre.dump` (`pg_dump -Fc`),
  `filestore/madenat_test_filestore_pre.tgz`.
- **Checklist de evidencias:** `docs/CHECKLIST_P1_P4.md`.

## 3. P1 — Concurrencia sobre la MISMA etiqueta retornada (ACREDITADO)
**Escenario real** (`tests/test_sv_rebaja_reset_lot_capacity.py`): lote `E` nominal **10**; dos **guías**
distintas comparten `E` (la unicidad `_check_single_work_per_guia` es por guía, no por etiqueta); **A** (guía 1)
y **B** (guía 2), ambos **cancelados**, cada uno con línea de **6 m³** (válidos individualmente: 6 ≤ 10; suma
**12 > 10**); SV destino **100** (el límite relevante es el **lote**, no el SV). **Cuándo se toma la reserva:**
al existir la línea en estado activo (`draft`/`pending`/`applied`) —creación de borrador y **reapertura**—.

**Tabla por transacción (órdenes A-primero / B-primero):**

| Concepto | A (ganadora, orden A-primero) | B (perdedora, orden A-primero) |
|---|---|---|
| Lote | E (nominal 10) | E |
| Capacidad inicial | 10 | 10 |
| Reserva/consumo inicial | 0 (cancelado) | 0 (cancelado) |
| Cantidad pretendida | 6 | 6 |
| Estado inicial | cancelled | cancelled |
| Bloqueo relevante | adquiere (3, lote E) | intenta (3, lote E) → **ocupado** |
| Resultado | `action_reopen_to_draft()` OK | **UserError** («Otra operación está modificando…») |
| Estado final | **draft** | **cancelled** |
| Reserva final | **6** | **0** (rollback) |
| Auditorías | `imputation_reopen` = 1 | `imputation_reopen` = **0** |

Orden B-primero: simétrico (gana B). **Revalidación de capacidad tras el bloqueo**
(`test_p1_capacity_tras_bloqueo`): tras confirmar A (draft, 6), B reabre en transacción nueva; al quedar libre el
bloqueo la **revalidación** de capacidad rechaza («…ya está comprometida (6,000 de 10,000)…»). **El límite lo
protege la ETIQUETA (lote) + el advisory lock de transacción (`_i2_lock_resources`) + la revalidación posterior
(`_i2_validate_reopen`).** Compromiso agregado dentro del límite, sin reserva parcial, sin doble consumo, sin
auditoría de la transición que no ocurrió, sin modificar el otro documento. RESET-17 se conserva como caso
**adicional** (saldo del SV) en `test_sv_rebaja_reset_concurrency.py`.

## 4. P2 — Recomputación REAL de intake (CORREGIDO Y ACREDITADO)
**Defecto reproducido (probe + test):** la consola `madenat.lumber.intake.console` es una vista SQL
(`_auto=False`); su caché **no** se invalidaba al cambiar una línea de detalle → **lectura obsoleta en el MISMO
entorno** (solo un entorno nuevo reflejaba el cambio). Guía actualizaba `volume_detail_m3` a 5.0; la **consola**
seguía en 0.0.

**Corrección mínima:** `madenat.lumber.volume.detail.line` invalida **dirigidamente** (`invalidate_model`) los
campos calculados de la consola que dependen del detalle, en `create`/`write`/`unlink`.

**Métricas tras create/write/unlink (operación → fuente → esperado → observado mismo entorno → entorno nuevo):**

| Operación | Fuente (`guia.volume_detail_m3`) | Console `volume_detail_m3` esperado | Mismo entorno | Transacción nueva |
|---|---|---|---|---|
| Inicial | 0.0 | 0.0 | 0.0 ✔ | 0.0 ✔ |
| Create detalle (5 m³) | 5.0 | 5.0 | **5.0 ✔** (antes: 0.0 ✗) | 5.0 ✔ |
| Write `volume_m3=9` | 9.0 | 9.0 (`official_vs_detail_diff_m3`=31.0) | **9.0 ✔** (antes: 5.0 ✗) | 9.0 ✔ |
| Unlink | 0.0 | 0.0 | **0.0 ✔** | 0.0 ✔ |

`store`/`compute` de la consola **sin cambios**; no se llamó manualmente al compute; no se recreó la consola; no
se invalidó caché en la prueba (la invalidación es el mecanismo productivo). Aviso `should be searchable`
ausente (0).

## 5. P3 — Saldos almacenados vs derechos del usuario (CORREGIDO Y ACREDITADO)
**Semántica:** `sv_assignment_nominal_m3` / `_applied_m3` / `_applied_count` / `_documental_balance_m3` =
**agregado canónico almacenado** (`store=True`, `compute_sudo=True`); `sv_assignment_imputation_ids` /
`sv_assignment_processor_id` = **proyección por usuario** (`store=False`, `compute_sudo=False`).

**Defecto reproducido (probe + test):** con `compute_sudo=False` en los almacenados, un usuario con acceso a
`stock.lot` pero **sin** acceso a `madenat.sv.imputation` (ACL por rol) provocaba **`AccessError`** al recomputar
→ el saldo canónico dependía de **quién** disparaba el cálculo. **Corrección:** `compute_sudo=True` en los
canónicos (acotado a las relaciones propias del lote → company-scoped).

**Matriz (campo → semántica → quién recalcula → valor almacenado → acceso):**

| Campo | Semántica | Recalcula | Valor (restricted / autorizado) | Acceso |
|---|---|---|---|---|
| `sv_assignment_applied_m3` | canónico almacenado | cualquiera (sudo) | **6.0 / 6.0** | lectura por ambos |
| `sv_assignment_applied_count` | canónico almacenado | cualquiera (sudo) | **1 / 1** | lectura por ambos |
| `sv_assignment_imputation_ids` | por usuario (no almac.) | por usuario | autorizado=OK; **restringido=AccessError** (sin filtración) | — |
| lote SV de compañía A | — | — | **no visible por compañía B** (0 filas / AccessError) | — |

**Variantes permitidas (reglas vigentes):** el restringido **no** lee imputaciones **ni** escribe el lote SV
(guard del core) ⇒ **no** hay vía normal de corrupción; forzando el recompute del ORM
(`add_to_compute`+lectura, igual que un write) bajo el restringido el saldo queda **canónico sin `AccessError`**;
la reversa **autorizada** sí actualiza el canónico (applied→0). **Sin** exposición entre compañías.

## 6. P4 — Aislamiento y limpieza de la autorización (CORREGIDO Y ACREDITADO)
**Defecto reproducido (auditoría):** `_I2_REOPEN_TOKENS` con clave `(dbname, uid, id)` **no** distinguía
transacción ⇒ ventana de autorización reutilizable (una escritura directa en otra transacción podía consumir el
token de la acción en curso). **Corrección:** se elimina el registro global; **vía privada de transición**
`_i2_write_protected_state` (método `_`-prefijado → **no** invocable por RPC; `service/model.py` bloquea
`name.startswith('_')`; escribe con `super().write`). La guarda pública `write()` rechaza **toda** transición
protegida (`cancelled → draft`, `applied → reversed`, y cualquier cambio sobre `reversed`).

**Pruebas (`tests/test_sv_rebaja_reset_token.py`):**

| TOK | Verificación | Resultado |
|---|---|---|
| 01 | Reapertura exitosa deja **cero** autorización residual; no hay registro global | ✔ |
| 02 | Excepción en la transición ⇒ documento **intacto** (`cancelled`), sin residual | ✔ |
| 03 | Fallo de validación intermedio ⇒ sin transición ni residual | ✔ |
| 04 | Escritura directa posterior **no** aprovecha autorización | ✔ |
| 05/06 | La vía privada **no** es RPC (`get_public_method` → AccessError); sin autorización cruzada (otro usuario / `sudo` / contexto) | ✔ |
| 07 | Multi-registro + repetición (idempotencia) | ✔ |
| 08 | Autor y fecha del entorno; valores del cliente **no** falsifican la auditoría | ✔ |
| 09 | **Sin estado compartido** (no hay contenedor global de tokens) | ✔ |

**Límite declarado:** no se levantaron dos workers reales; la garantía multi-proceso es **por construcción** (la
vía privada no usa estado compartido). No se equipara prueba de hilos con prueba de procesos.

## 7. Correcciones y archivos afectados
- **P2 (intake):** `madenat_lumber_intake/models/volume_detail_line.py` — invalidación dirigida de las métricas
  de la consola en `create`/`write`/`unlink` (nuevo `_invalidate_console_metrics` + `unlink`).
- **P3 (logistics):** `madenat_lumber_logistics/models/madenat_sv_imputation.py` — `compute_sudo=True` en los 4
  agregados almacenados (los 2 no almacenados siguen `False`).
- **P4 (logistics):** mismo archivo — se elimina `_I2_REOPEN_TOKENS`; `write()` rechaza toda transición
  protegida; nueva vía privada `_i2_write_protected_state`; `action_reopen_to_draft` y `action_reverse` la usan.
- **Pruebas:** `test_intake_metrics_recompute.py` (nuevo, intake); `test_sv_rebaja_reset_lot_capacity.py`,
  `test_sv_assignment_user_rights.py`, `test_sv_rebaja_reset_token.py` (nuevos, logistics);
  `test_sv_rebaja_reset.py` (ajustado: atributos de los agregados). Registros en los `tests/__init__.py`.
- **Metadata:** `__manifest__.py` (versiones) y `CHANGELOG.md` de ambos módulos.
- **Docs:** `CANON/19 §19.29`, `CANON/02 §17.16.27`, `CANON/03 §29`, `CANON/INDICE_DOCUMENTACION.md`.
- **Sin cambios** en modelos de negocio, wizard, menú, ledger, políticas de reserva/aplicación, ingesta
  (salvo el cálculo auditado) ni permisos.

## 8. Pruebas dirigidas y regresión (cifras exactas)
- **Dirigidas (verde):** `TestSvRebajaResetLotCapacity` (3) + `TestIntakeMetricsRecompute` (1) +
  `TestSvAssignmentUserRights` (2) + `TestSvRebajaResetToken` (7) = **13 tests → 0 failed / 0 error / 0
  warnings** (EXIT=0). Más las suites de §19.28 (`TestSvRebajaReset`, `TestSvRebajaResetConcurrency`,
  `TestIntakeConsoleComputeDepends`) → **21 tests → 0 failed / 0 error**.
- **Regresión amplia** (`core+intake+logistics`): **1230 tests → 6 failed, 4 error**.
  - `madenat_lumber_intake`: **467 tests, 0 fallas** (verde).
  - Fallas en `madenat_lumber_core` (no modificado) y en el **conjunto preexistente** de logistics.
- **Comparación verificable de baseline** (`FASES/BLINDAJE_REBAJA_LOCAL_20261012/` (artefacto `regression.log` en `logs/`, fuera de git), estado
  **previo** 18.0.1.22.0 / 18.0.0.12.0): **1217 tests → 6 failed, 4 error** con el **mismo** conjunto exacto de
  10 fallas. La corrida actual (18.0.1.23.0 / 18.0.0.13.0) suma **+13 tests (todos verde)** y **no** añade
  fallas. Conjunto idéntico en ambas: `TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive`,
  `TestSvEscalationSecurity.test_02/03/04`, `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos`,
  `TestProcessorLocations.test_09_auditoria_envio_normal`, `TestProcessorShipmentAD89.test_t1/t5/t6`,
  `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen`.
- **Regresión solo-logistics** (mismo alcance que la base documentada): **456 tests → 4 failed, 0 error** — las
  **mismas 4** de la base (444/4; `TestProcessorLocations.test_09`, `TestProcessorShipmentAD89.test_t1/t5/t6`).
  La corrida actual suma **+12 tests (mis nuevas suites)** sin añadir fallas.
- **Sin debilitar tests**: no se relajó ninguna aserción; el cambio en `test_sv_rebaja_reset.py` **refuerza**
  (los almacenados son `compute_sudo=True`).

## 9. Versiones locales instaladas
- `madenat_lumber_logistics`: **18.0.1.22.0 → 18.0.1.23.0**
- `madenat_lumber_intake`: **18.0.0.12.0 → 18.0.0.13.0**
- `madenat_lumber_core`: **18.0.6.6.0** (sin cambios; **no** se incrementó)
- Docs: `19` 1.26.0 → **1.27.0**; `03` 6.34.0 → **6.35.0**; `02` 12.35.0 → **12.36.0**.
- Comando: `odoo -d madenat_test -u madenat_lumber_logistics,madenat_lumber_intake --stop-after-init --no-http`
  → **EXIT=0** (`logs/update_final.log`). **No** `-u all`.

## 10. Documentación actualizada
`madenat_lumber_docs`: `CANON/19_IMPUTACION_SV_Y_PROCESADORES.md` (**§19.29**),
`CANON/02_CONTINUIDAD.md` (§17.16.27), `CANON/03_TESTS.md` (§29), `CANON/INDICE_DOCUMENTACION.md`; más
`CHANGELOG.md` de ambos módulos. No se creó otra fuente canónica. Evidencia before/after conservada
(probes en el log de la sesión y prueba de regresión reproducible).

## 11. WIP ajeno preservado
- **Solo** se modificaron archivos de `madenat_lumber_logistics`, `madenat_lumber_intake` y `madenat_lumber_docs`.
- El resto del WIP (modificados/no rastreados) queda **intacto** (`code/wip_status.txt`); HEAD sin cambios
  (sin commit). Respaldos en `code/`, `db/`, `filestore/`.

## 12. Pendientes y autorizaciones necesarias
1. **Sobrescritura de borradores:** propuesta registrada; **pendiente de autorización** de Mauricio (no activada).
2. **Multi-worker real:** no se levantaron dos procesos; garantía por construcción (límite declarado).
3. **Aceptación de Cristhian:** pendiente (TEST remoto reservado; no se tocó).
4. `IMP02220`/`IMP04823` e históricos **intactos**.

---
**SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA.**