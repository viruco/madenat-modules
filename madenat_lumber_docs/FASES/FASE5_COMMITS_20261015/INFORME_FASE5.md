# FASE 5 — COMMITS ORDENADOS (SOLO LOCAL) — INFORME DE CIERRE

**Proyecto:** MADENAT — Odoo 18 CE · **Fecha:** 2026-10-15
**Repo:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (único `.git`; el directorio `odoo-18-ce` NO es repo)
**Rama:** `feat/guia-correccion-documental-preservada-20261002` · **HEAD inicial:** `b1d2d19`
**Base local de pruebas:** `madenat_test` (contenedores `odoo18_app` / `odoo18_db`)
**Respaldo (C-2):** `FASE5_COMMITS_20261015/` (fuera del repo)

**Ejecutado:** C-1 (5 commits locales), C-2 (bundle + tar + SHA256) y C-3 (AD-106 documentado).
**NO ejecutado:** push, ramas nuevas, remoto, reset/clean/stash/rebase/amend/squash, tags, force, despliegue,
`-u all`, borrado de archivos o datos, ni cambios de código/tests (salvo la nota documental C-3).

---

## 1. ESTADO GIT — INICIAL y FINAL

| | Inicial (b1d2d19) | Final (ed42df5) |
|---|---|---|
| Entradas de `git status` | **110** (71 `M` + 39 `??`) | **16** (13 `M` + 3 `??`) |
| `git stash` | vacío | vacío (no se usó) |
| Commits nuevos | — | **5** |
| Archivos commiteados | — | **94** (91 idénticos al respaldo + 3 de C-3) |

Las **16 entradas restantes** son **exactamente** la lista de exclusión de la §3 (`diff` textual = **IDÉNTICO**,
ver `logs/excluded_files.txt`). **Ninguna entrada no listada quedó fuera ni dentro.**

`.gitignore` verificado: `*.tar.gz` (regla 49), `__pycache__/` (regla 13), `filestore/`, `*.log`, `*.pyc`,
`*.bak*`, `*.sha256`; `config/odoo.conf` está **fuera** del repo (no versionado). Los 6 `.tar.gz` de la raíz del
repo están ignorados. **Ningún archivo sin seguimiento supera 5 MB** (máximo real: 44 KB) y ningún archivo mayor
de 5 MB entró en los commits.

---

## 2. COMMITS CREADOS (orden por dependencias)

| # | Hash | Tipo/módulo | Archivos | Versión | Intervenciones |
|---|------|-------------|---------:|---------|----------------|
| ① | `d67313b` | `docs(canon)` | 10 | 02 12.40.0 · 03 6.38.0 · 04 12.21.0→**12.22.0** · 05 8.26.0→**8.27.0** · 18 1.2.0 · 19 1.31.0 · INDICE 12.32.0→**12.33.0** · WIKI 2.0.2 | FASE 2 (D13/D14, AD-103), FASE 3 (AD-104), FASE 4 (AD-105), HOTFIX OWL chatter, rebaja/I2, WIKI (despliegue + higiene), **AD-106 nuevo (C-3)** |
| ② | `0ef4388` | `feat(core)` | 19 | **18.0.6.6.0 → 18.0.6.9.0** | guías-dup (2026-10-07 + incidente 15183), guardas de guía (AD-104), lote/`stock_quant-FK`, FASE 4 H1/H2/H3 (AD-105), ACL, UI/menú |
| ③ | `a691256` | `fix(shipping_core)` | 3 | 18.0.1.0.0 (sin cambio) | reparación de marcado corrupto `hatter/>` (doctrina HOTFIX OWL, AD-105) + aclaración **AD-92** (rolleo desde Embarque) |
| ④ | `ded5e89` | `feat(logistics)` | 46 | **18.0.1.8.0 → 18.0.1.27.0** | I2/imputación SV (AD-91/AD-102) + `ir.rule` multi-compañía (AUD-ETQ-07), rebaja-etiquetas (AUD-ETQ-01..11), reset/reapertura, LOCK, SIMPLE/persistencia, embarque/zarpe-B01 (AD-93/94), rebaja-contenedor, backlog-documental (AD-100), HOTFIX chatter, H6 (AD-105), ACL por rol |
| ⑤ | `ed42df5` | `feat(intake)` | 16 | **18.0.0.11.0 → 18.0.0.15.0** | intake/AD-101 (consola, búsqueda, modalidades), AUD-ETQ-08 (computes/métricas), intake-volumen, guías-dup-delete (AD-104 G1/G2), ACL de borrado, FASE 4 H1 (asistente AD-73 con motivo propio) |

Total: **94 archivos**, +17.5k/−0.4k líneas. Evidencia: `logs/commits_log_stat.txt`, `logs/commits_hashes.txt`,
`logs/committed_files.txt`, `msgs/*.msg`.

**Orden justificado por el grafo de manifiestos** (`depends`): `shipping_core` (solo `base/mail/uom`) y `core`
(raíz de la que dependen todos) van antes que `logistics` (no depende de `intake`) y `intake`
(`depends: madenat_lumber_core, madenat_toll_processing, madenat_ingestion_engine`). Los `docs` van primero por
ser el registro canónico de las versiones que documentan los commits siguientes.

**Desviación declarada (no corregible):** el **cuerpo del commit ② (`0ef4388`) dice «Commit local 3/5»** por un
error de tipeo al redactar; corresponde a 2/5. La corrección exigiría `--amend`, **prohibido** por esta
autorización; se declara aquí en lugar de reescribir historia.

---

## 3. EXCLUSIONES (16 entradas; NO commiteadas) — con razón

| # | Archivo (WIP restante) | Razón |
|---|---|---|
| 1 | `madenat_lumber_core/tests/test_duplicate_validation.py` | **D18** — entrada `desconocido` del triaje (autoría/intervención no confirmada) |
| 2-7 | `madenat_lumber_costing/__manifest__.py`, `models/__init__.py`, `models/lumber_cost_distribution.py`, `models/lumber_shipment_costing.py`, `security/ir.model.access.csv`, `tests/__init__.py` | **D1 / `costing-C2` bloqueado** (versión sin subir 18.0.1.0.0 y sin CHANGELOG) |
| 8-11 | `madenat_lumber_costing/models/stock_lot_cost_line.py` (nuevo), `tests/test_shipment_costing_c2.py` (nuevo), `views/lumber_shipment_costing_views.xml` (nuevo), `views/lumber_cost_distribution_views.xml` | **D1 / `costing-C2` bloqueado** |
| 12-13 | `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard.py` y `..._views.xml` | **D18** — origen no confirmado |
| 14-15 | `madenat_lumber_logistics/tests/test_rebaja_contenedor.py`, `.../test_service_return_imputation_guard.py` | **D18** — origen no confirmado |
| 16 | `madenat_lumber_reports/views/lumber_reports_menu.xml` | **Sin atribución**: desactiva el menú `menu_lumber_reports_root` (`active="0"`) con un comentario «P2-2» **sin** AD, sin expediente y sin rastro documental localizable ⇒ **ante la duda, no se commitea** |

> **Otras categorías excluidas y por qué NO aparecen en el WIP:** dumps/tar/filestore/backups/`__pycache__`/
> binarios (ignorados o fuera del repo), `_archive/` y `LEGADO/` (trackeados pero **sin cambios**: A2/A3 no
> aprobadas), configuración y credenciales (`config/odoo.conf` fuera del repo) y **todo** cambio no atribuible a
> una intervención cerrada.

### 3.b Consecuencia declarada de excluir los 4 archivos D18 de `logistics`

Al no incluir `lumber_shipment_rebaja_wizard.py{,_views}` (asistente de rebaja, +380 líneas), el commit ④
versiona las **suites** `test_sv_rebaja_*` sin la última versión del **código** que ejercitan. **No rompe nada**
en el árbol de trabajo ni en `madenat_test` (todo sigue aplicado), pero un clon limpio tendría suites
correspondientes a un asistente anterior. Se resuelve con **un commit posterior** cuando se confirme **D18**.

---

## 4. VERIFICACIÓN DE HASHES (árbol commiteado vs. respaldo previo)

* `pre/wip_sha256_before.txt`: **110** entradas (todas las del `git status` inicial).
* **Contenido commiteado** (`git show HEAD:<ruta>` vs. respaldo previo): **91 idénticos**, **3 distintos**:
  `CANON/04_DECISION_LOG.md`, `CANON/05_BACKLOG.md` y `CANON/INDICE_DOCUMENTACION.md` —
  **exactamente** los 3 archivos del cambio documental autorizado (C-3/AD-106). **Cero** diferencias no
  autorizadas. (`pre/` es ANTERIOR a la edición C-3; por eso esos 3 difieren por diseño.)
* **WIP restante (16 entradas): 0 hashes cambiados** respecto del respaldo previo.
* `post/wip_sha256_after.txt` (16) y `post/_ref_sha256_before.txt` (110) permiten reproducir la comparación.

---

## 5. RESULTADO DE LA REGRESIÓN (`madenat_test`, LOCAL)

**Comando** (idéntico patrón a los baselines previos; HTTP en 9999 como las corridas de referencia):

```
docker exec odoo18_app odoo -d madenat_test \
  -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics \
  --test-enable --stop-after-init --http-port=9999 --max-cron-threads=0
```

| Métrica | Baseline vigente (FASE 4) | **FASE 5 (post-commits)** |
|---|---|---|
| Resultado global | **6 failed + 4 error de 1448** | **6 failed + 4 error de 1448** |
| `post-tests` | 1359 en 247 s | 1359 en 246.9 s |
| core / intake / logistics | 500 / 496 / 594 | 500 / 496 / 594 |
| ingestion_engine / billing / costing / purchasing | 96 / 11 / 38 / 21 | 96 / 11 / 38 / 21 |
| Conjunto de pruebas fallidas | 10 tests (nombres §4.4 del informe de auditoría) | **los MISMOS 10 tests** |

**Comparación por NOMBRE de prueba: `diff` = IDÉNTICO ⇒ 0 fallas nuevas.** Detalle:
`logs/regression_fase5.log`, `logs/regression_fase5_failures.txt`, `logs/baseline_10_fallas.txt`.

**Matiz honesto (declarado):** dos de los diez cambiaron de **manifestación**, no de identidad:
`TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive` pasó de `FAIL`
(AssertionError de savepoint) a `ERROR` (`UserError` de `stock_account`: «La valuación de este producto es por
lote…», al crear una `stock.move.line` sin lote) y `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen`
pasó de `ERROR` (timeout de lock) a `FAIL` (`AssertionError: 2 != 1`). Ambos ya estaban clasificados en la
auditoría como **dependientes de entorno/orden de ejecución** (D10 pendiente) y el contenido de código es
byte-idéntico al que produjo el baseline, por lo que la diferencia es de entorno/orden y no de los commits.

**Efecto lateral de la regresión (residual, no bloqueante):** `-u` re-afirmó core/intake/logistics en
`madenat_test` y las suites con `commit()` dejan residuo mínimo (usuarios/socios `*_oper` y bitácora) — es el
comportamiento ya documentado (H-TEST-2 / D5). Se tomó `pg_dump` previo para poder revertir la base si hiciera
falta.

---

## 6. PRUEBA DE INTEGRIDAD — CLON TEMPORAL LOCAL

* `git clone --no-hardlinks <ruta local del repo> /tmp/fase5_integrity_clone` ⇒ **HEAD del clon =
  `ed42df54dab62beea0780337971d3657b4232ac1` = HEAD del repo**, rama correcta, **los 5 commits presentes**.
* `python3 -m compileall` de los 4 módulos commiteados (`core`, `logistics`, `intake`, `shipping_core`):
  **237 archivos `.py` compilan sin error** (excluido `madenat_lumber_core/_archive/`, ver §8).
* Manifests (`literal_eval` + claves `name/version/depends`) + XML + CSV de esos módulos: **101 archivos: OK**
  (excluido 1 XML legacy mal formado y no listado en manifest, ver §8).
* **Clon temporal eliminado** (`rm -rf /tmp/fase5_integrity_clone`, 45 MB) — **solo** el creado por esta prueba.

---

## 7. RESPALDO POSTERIOR (C-2) — verificado

Todo en `FASE5_COMMITS_20261015/` (**fuera** del repo; sin sobrescribir respaldos previos).

| Artefacto | Contenido | Verificación |
|---|---|---|
| `post/repo_history_after.bundle` (3.5 MB) | `git bundle --all` con los 5 commits (`HEAD ed42df5`) | `git bundle verify` ⇒ **«records a complete history» OK** |
| `post/wip_restante.tar.gz` (41 KB) | los **16** archivos del WIP no commiteado (193 KB sin comprimir) | `gzip -t` **OK** |
| `post/wip_sha256_after.txt` (16), `post/git_status_after.txt`, `post/head_after.txt` | huella del WIP restante y del HEAD final | `sha256sum -c SHA256SUMS.txt` ⇒ **5/5 OK** |
| `pre/custom_addons_worktree.tar.gz` (2.5 MB) | árbol de trabajo **completo** antes de tocar nada (**717/717** archivos = 678 trackeados + 39 nuevos) | `gzip -t` OK |
| `pre/wip_tracked_HEAD.diff` (753 KB) | diff del WIP vs `b1d2d19` (evidencia previa) | — |
| `pre/madenat_test_pre_fase5.dump` (11.5 MB) | `pg_dump -Fc` previo de `madenat_test` | dump no vacío; `pg_dump.err` vacío |
| `pre/repo_history_before.bundle` (3.2 MB) | historia completa ANTES de los commits | `git bundle verify` ⇒ complete history OK |
| `pre/wip_sha256_before.txt` (110), listas y `logs/`, `msgs/` | manifiestos SHA-256, listas por commit, logs y mensajes usados | `pre/SHA256SUMS.txt` generado |

---

## 8. HALLAZGOS NUEVOS (pre-existentes, NO introducidos por estos commits)

1. **Marcado XML corrupto en HEAD (reparado en ③):** `shipping_vessel_views.xml:48` y
   `shipping_voyage_views.xml:45` contenían la línea literal `hatter/>` (residuo de `div.oe_chatter`). Ambas
   vistas **están listadas en el manifest**, de modo que en `HEAD` el módulo no podía cargar sus vistas. No
   estaba documentado en ningún expediente.
2. **XML legacy mal formado y NO listado en manifest (inerte, sigue igual):**
   `madenat_lumber_core/views/wizard_lumber_reception_mass_update.xml` (línea 30). Último commit que lo tocó:
   `994bcbd` (baseline v1.0, 2026-05-31).
3. **4 XML vacíos/ilegibles en `madenat_vendor_payment`** (`report/vendor_payment_templates.xml`,
   `report/vendor_payment_reports.xml`, `wizards/payment_approval_views.xml`,
   `wizards/vendor_payment_batch_views.xml`): tampoco listados en su manifest (módulo no instalado). Se suma al
   `div.oe_chatter` ya reportado.
4. **Código en cuarentena que no compila:** `madenat_lumber_core/_archive/_cleanup_orphan_moves.py`
   (IndentationError), archivado a propósito en `9677f53` (2026-07-06). Hoy está **trackeado** dentro del repo
   (relacionado con **A3**, no aprobada).
5. **Import sin uso introducido en el WIP de `shipping_core`:** `from odoo.exceptions import AccessError` en
   `models/shipping_vessel.py` (se conserva tal cual en ③ para no alterar contenido; candidato a **C2**).
6. **Sin archivos pesados ni sensibles nuevos:** ningún archivo del WIP > 5 MB; 0 credenciales/tokens en los
   diffs; los únicos correos son **fixtures sintéticos** (`*@madenat.cl`, `*@test.local`).
7. **El expediente `AUDITORIA_INTEGRAL_20261012/` está FUERA del repo** (177 MB, con dumps `.dump`, `.tar.gz`
   del worktree/filestore y un `.bundle`): **no es commiteable** sin copiarlo dentro del repo (cambio no
   autorizado) y, por la regla de la §4-⑦, su parte pesada/sensible quedaría fuera igualmente. **Commit ⑦
   omitido y documentado** (ver §9-3).
8. **Los 5 archivos `desconocido` (D18)** y el **menú de `reports`** quedan excluidos (§3) pese a que la §3.a de
   la Fase 1 los mapea manualmente a `guias-dup`/`rebaja-contenedor`/`retorno-servicio`/`rebaja-motonave`: la
   regla operativa aplicada fue *«ante la duda, NO commitear y reportar»*.

---

## 9. RIESGOS RESIDUALES Y PENDIENTES

1. **Trigger/hash de la bitácora (H-SEC-5 ampliado):** la inmutabilidad es **por ORM**; SQL directo o un DBA
   siguen pudiendo alterar `madenat_audit_log`. Defensa propuesta y **NO implementada**.
2. **Suites que hacen `commit()` y dejan residuo (D5):** la limpieza generalizada de bitácora de pruebas sigue
   pendiente; la regresión confirmó el patrón (H-TEST-2).
3. **`docs(auditoria)` (commit ⑦) no ejecutado:** el expediente vive fuera del repo (177 MB, con material
   sensible/pesado). Opciones: (a) copiar al repo solo `README.md`/`docs/`/logs de texto livianos; (b) dejarlo
   fuera y referenciarlo (situación actual).
4. **`costing` D1/C2 sigue bloqueado** (10 entradas): sin subir versión ni CHANGELOG ⇒ no desplegable.
5. **D18 (5 entradas) sigue sin resolver:** incluye el asistente de rebaja. Consecuencia declarada en §3.b.
6. **`reports`:** cambio de menú (`active="0"`) sin atribución documental ⇒ fuera del historial hasta que se
   confirme su origen.
7. **D10 — 10 fallas preexistentes:** 4 de código + 6 de entorno/orden (2 cambiaron de manifestación en esta
   corrida). Sigue pendiente decidir si se corrigen o se aíslan/serializan.
8. **Errata en el mensaje del commit ②** («3/5» en lugar de «2/5»): no corregible sin `--amend` (prohibido).
9. **`-u all` no se usó** y **no hubo cambios de código/tests**: cualquier efecto funcional ya estaba aplicado en
   `madenat_test` antes de esta fase.

---

## 10. PRERREQUISITOS PARA UN DESPLIEGUE AL TEST REMOTO (NO ejecutado)

1. **Confirmar D18** (5 archivos) y crear el commit de cierre de `logistics` (asistente de rebaja) + `core`.
2. **Decidir el destino del expediente de auditoría** (commit ⑦): copiar la parte liviana o dejarlo fuera.
3. **Actualizar** en el TEST remoto, como mínimo, `madenat_lumber_shipping_core`, `madenat_lumber_core`,
   `madenat_lumber_intake` y `madenat_lumber_logistics` (orden por `depends`), **sin** `-u all`.
4. **Respaldo del TEST remoto** (dump + filestore) + ventana de mantenimiento; verificar respaldos previos.
5. **`-u` de los 4 módulos** + humo funcional: carga de las vistas de Motonave/Viaje (⇒ `<chatter/>`), ingreso de
   guía por Volúmenes/Procesado (duplicados), eliminación de guía (motivo + rol jefatura), rebaja de etiquetas y
   documento de imputación SV (chatter sin `OwlError`).
6. **Comprobación manual en navegador pendiente** desde el HOTFIX OWL chatter (VIEW-01/04) — sigue sin evidencia
   de navegador.
7. **Aceptar los pendientes** disparables: trigger/hash de bitácora, residuo de suites, D1/D18.
8. **No desplegar** `madenat_lumber_costing` (D1) ni el cambio de menú de `reports` (sin atribución).

---

## CRITERIO DE CIERRE — ESTADO

| Criterio | Estado |
|---|---|
| Commits locales ordenados por módulo, con mensajes trazables | ✅ 5 commits (94 archivos) |
| Nada sensible, pesado ni bloqueado fue commiteado | ✅ 0 secretos, 0 > 5 MB, 16 bloqueados intactos |
| El contenido commiteado es idéntico al del respaldo previo | ✅ 91/94 idénticos; los 3 = C-3 autorizado |
| El WIP restante es exactamente el bloqueado y sin cambios | ✅ `diff` = IDÉNTICO; 0 hashes cambiados |
| 0 fallas nuevas | ✅ mismo conjunto de 10 (2 flips de manifestación, declarados) |
| Respaldo posterior verificado | ✅ bundle + tar + `SHA256SUMS` (`sha256sum -c` 5/5 OK) |
| Supuesto de una compañía documentado | ✅ **AD-106** (04 12.22.0), 05 8.27.0 e INDICE 12.33.0 |

**SIN PUSH · SIN RAMAS NUEVAS · SIN RESET/CLEAN/STASH/REBASE/AMEND · SIN DESPLIEGUE REMOTO ·
SIN CONEXIÓN AL REMOTO · SIN ELIMINACIÓN DE DATOS NI DE ARCHIVOS · SIN `-u all`.**




