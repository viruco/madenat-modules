# BLINDAJE DE BORRADORES — PROTECCIÓN CONTRA SOBRESCRITURA CONCURRENTE — ENTREGA (2026-10-12)

**Entorno:** `madenat_test` **LOCAL** · **Docs:** `madenat_lumber_docs` · **Autorización:** Mauricio.
**Regla cumplida:** **SIN COMMIT · SIN PUSH · SIN DESPLIEGUE REMOTO · SIN REPARACIÓN HISTÓRICA · TEST remoto intacto.**

---

## 1. Dictamen
**CORREGIDO Y ACREDITADO.** El riesgo «la última escritura gana» queda resuelto para el **recorrido del
asistente** (Guardar/Aplicar/Dejar pendiente): una edición basada en una versión obsoleta se **rechaza de forma
controlada**; no se sobrescribe ni se fusiona; se puede **recargar** la versión vigente. **Límite declarado:** la
edición simultánea de dos **formularios persistentes directos** (form-vs-form, sin asistente) queda **pendiente**
(comportamiento ORM estándar de Odoo).

## 2. Reproducción del defecto original
Antes, `_i2_build_imputation` escribía cabecera/líneas/repartos **sin comparar versión** ⇒ dos sesiones sobre el
mismo borrador: la segunda **sobrescribía** en silencio. Demostrado en
`test_sv_rebaja_save_lock.py::test_repro_defecto_last_write_wins`: neutralizando el guard, B (versión obsoleta)
sobrescribe el valor de A (2.0 sobre 7.0). Con el guard **activo**, `LOCK-01` acredita que B es **rechazada** y los
datos de A quedan **intactos**. El test `SAVE-12` (que codificaba «última escritura gana») se **actualizó** a la
política aprobada (justificado: la aserción anterior quedó **superseded** por la autorización de Mauricio).

## 3. Mapa de dependencias y vías de escritura
| Entrada | Método | Modelos escritos | Validación | Transacción | Impacto versión |
|---|---|---|---|---|---|
| Guardar (asistente) | `action_prepare` → `_i2_guarded_build` → `_i2_build_imputation` | `madenat.sv.imputation` + `.line` + `.sv.line` (+ links) | elegibilidad, estado, **guard de versión**, techo | 1 tx | +1 (por escritura de contenido) |
| Aplicar (asistente) | `action_apply` → `_i2_guarded_build` + `imp.action_apply` | idem + estado | + permisos, capacidad, locks ns2/ns3, hard cap | 1 tx | +1 (build) +1 (`state`) |
| Dejar pendiente | `action_pending` → build + `action_pending` | idem + estado | idem | 1 tx | +1 +1 |
| Cancelar | `action_cancel` | `madenat.sv.imputation` (state) | permisos/estado | 1 tx | +1 |
| Reabrir | `action_reopen_to_draft` | `madenat.sv.imputation` (state) | permisos, capacidad, **locks ns1? no**: ns2/3 | 1 tx | +1 |
| Revertir | `action_reverse` | `madenat.sv.imputation` (state) | permisos, motivo | 1 tx | +1 |
| Reconstruir/Continuar/Recargar | `_i2_reconstruct_commands`, `action_reload_current` | — (solo lee) | — | 1 tx | 0 |
| Edición directa (documento) | `write()` | `madenat.sv.imputation` | guards de estado | 1 tx | +1 (contenido) |
| Edición directa (hijos) | `.line`/`.sv.line` `create/write/unlink` | hijos + **elevan el padre** | inmutabilidad applied | 1 tx | +1 (doc padre) |

**Clave:** la versión vive en el **documento** (fuente única persistente). Todas las vías de escritura de
**contenido** la elevan; las de **trazabilidad/historia** no. Un único punto de comparación
(`_i2_assert_edit_version`) cubre Guardar y Aplicar por igual.

## 4. Diseño mínimo elegido y alternativas descartadas
**Elegido:** versión lógica **`edit_version`** (entero monotónico) en `madenat.sv.imputation`; el asistente
captura `expected_edit_version` al abrir; `_i2_build_imputation` valida **estado → versión** de forma **atómica**
(advisory lock ns 1 + comparación) antes de escribir; `_i2_guarded_build` fuerza el **flush** dentro de la
transacción.
**Alternativas descartadas:** (a) **bloqueo pesimista** del documento durante toda la edición → degrada UX y no
cubre sesiones abiertas; (b) **merge/recomputación automática** → riesgo de fusiones incorrectas en repartos; (c)
**`write_date`** como versión → no cambia cuando solo cambian líneas/repartos y su precisión es de **segundo** (no
cubre la carrera); (d) **memoria global del proceso / flag de contexto** → prohibido (no cruza workers;
falsificable).

## 5. Comparación y escritura ATÓMICAS
`_i2_assert_edit_version`: (1) adquiere `pg_try_advisory_xact_lock(1, doc_id)` (namespace **1** = documento); (2)
relee `edit_version`; (3) compara con `expected_edit_version` → si difiere o el lock está ocupado, **rechaza sin
escribir**. Se integra con los locks de capacidad existentes (ns 2 y 3) en **orden creciente 1→2→3** (sin
deadlock). La carrera entre comparación y escritura (REPEATABLE READ) la cubre el **flush** dentro de la
transacción: un `SerializationFailure` se traduce al **mismo** mensaje operativo. **Sin** commits manuales; **sin**
reintento que sobrescriba (una edición obsoleta sigue obsoleta).

## 6. Cobertura de líneas, repartos y edición directa
`create`/`write`/`unlink` de `madenat.sv.imputation.line` y `.sv.line` **elevan** `edit_version` del documento
padre (`_i2_bump_from_child`) ⇒ un asistente abierto con versión anterior **detecta** cualquier cambio de
etiquetas/repartos (LOCK-06/07). La **edición directa** del documento (cabecera) también eleva la versión
(LOCK-19). **No** se añadieron tokens globales ni flags de contexto.

## 7. Mensajes y recuperación del usuario
- **Conflicto:** «El documento IMP… cambió desde que lo abriste (otra sesión lo guardó mientras editabas). Tus
  cambios NO se han guardado… Pulsa «Recargar versión actual»…». Sin error técnico de PostgreSQL.
- **Estado:** si el documento fue anulado/aplicado/reversado, mensaje **de estado** (RESET-11), no de conflicto.
- **Recargar versión actual** (`action_reload_current`): botón en el asistente con `confirm`; descarta los cambios
  no guardados (el usuario confirma en el cliente), reconstruye desde el documento vigente y actualiza la versión
  esperada. **Sin** fusión automática ni bypass. Ante conflicto **no** se modifica el documento ni las reservas.
- **Límite (LOCK-14):** la conservación de las ediciones locales **en el navegador** requiere evidencia de cliente
  (no se afirma solo con ORM); el rechazo **no** adopta la versión ajena en silencio (comprobado en el asistente).

## 8. Pruebas (concurrentes y de comportamiento)
`madenat_lumber_logistics/tests/test_sv_rebaja_save_lock.py` — **23 pruebas, 0 failed / 0 error**:
`LOCK-01..19` (dos sesiones, Guardar vs Aplicar, aplicado no editable, mismo usuario, usuarios distintos, línea
hija, eliminación de reparto, dos primeros guardados, guardado repetido, Guardar→Continuar, chatter, cancelación
externa, recargar, rechazo no adopta versión, rollback intermedio, **LOCK-16 con transacciones independientes y
barrera**, edición vs transición, sin permiso/otra compañía, edición directa) + `FLOW-01..03` + `PHY-01` +
reproducción del defecto. **LOCK-16:** A (cursor principal) adquiere y mantiene el guard; B (cursor independiente)
es **rechazada** con el mensaje operativo (sin sobrescritura parcial).

**Resultados por transacción (LOCK-16 y LOCK-01):** A `draft` y `edit_version` v→v+1; B rechazada, sin cambio de
documento/reservas ni auditoría de transición inexistente.

## 9. Seguridad, reservas y ausencia de efectos físicos
La versión **no** sustituye ACL/reglas de registro/compañía/etapa de destino/etiqueta-guía/capacidad/estado. Un
guardado rechazado **no** cambia reservas ni saldos ni escribe auditoría. `LOCK-18` acredita el bloqueo de acceso
(usuario sin rol y usuario de otra compañía). `PHY-01`: sin movimientos físicos de stock.

## 10. Regresión (cifras exactas)
- **Dirigidas LOCK:** **23 tests → 0 failed / 0 error** (`lock_run2.log`).
- **Logistics (comparable con la base):** **479 tests → 4 failed / 0 error** — las **mismas 4** preexistentes
  (baseline `VERIF_CUATRO_PUNTOS` solo-logistics **444/4**). `+35 tests` (12 de P1/P3/P4 + 23 de LOCK), **0 fallas
  nuevas**.
- **Amplia** (`core+intake+logistics`): **1253 tests → 6 failed / 4 error** — el **mismo conjunto exacto** de 10
  fallas que la base (baseline `VERIF_CUATRO_PUNTOS` amplia **1217 → 6 failed / 4 error**). `+36 tests` (todos
  verde), **0 fallas nuevas**. `intake` **467/0**; las fallas son de `core` (no modificado) y del conjunto
  preexistente de logistics.
- **Tests modificados (justificados, no debilitados):** `test_sv_rebaja_persistencia.test_save_12` (codificaba
  «última escritura gana» → se **actualizó** a la política aprobada: la sesión obsoleta se **rechaza**);
  `test_sv_rebaja_simple.test_simple_01` (inventario de botones del header → se añadió `action_reload_current`).
  Ambas son actualizaciones de **aserción de política/UI**, no relajación.

## 11. Evidencia de navegador
**No ejecutada en esta intervención** (sin navegador). Guion sugerido en `docs/PLAN_DESPLIEGUE.md` (smoke test).
Se declara como **pendiente**; no se afirma conservación de las ediciones locales en el cliente (LOCK-14).

## 12. Versiones y documentación
- `madenat_lumber_logistics` **18.0.1.23.0 → 18.0.1.24.0**; `madenat_lumber_core` **18.0.6.6.0** (sin cambios);
  `madenat_lumber_intake` **18.0.0.13.0** (sin cambios; `-u` solo del módulo afectado + core).
- Docs: `CANON/19 §19.30` (1.27.0 → **1.28.0**), `CANON/02 §17.16.28` (12.36.0 → **12.37.0**), `CANON/03 §29`
  (6.35.0 → **6.36.0**), `CANON/INDICE`; `CHANGELOG.md` del módulo.

## 13. Archivos afectados y WIP ajeno preservado
- **Modelo:** `models/madenat_sv_imputation.py` (`edit_version`, `_i2_with_version_bump`, `_i2_bump_from_child`,
  `_i2_assert_edit_version`, bumps en hijos).
- **Asistente:** `wizards/madenat_sv_imputation_wizard.py` (`expected_edit_version`, `_i2_guarded_build`,
  `action_reload_current`, guard en `_i2_build_imputation`), `wizards/..._views.xml` (botón).
- **Pruebas:** `tests/test_sv_rebaja_save_lock.py` (nuevo); `tests/test_sv_rebaja_persistencia.py` y
  `tests/test_sv_rebaja_simple.py` (actualizadas); `tests/__init__.py`.
- **Metadata/docs:** `__manifest__.py`, `CHANGELOG.md`, CANON 19/02/03/índice.
- **WIP ajeno** preservado (solo se tocaron los archivos anteriores); **sin commit** (HEAD `b1d2d19`).

## 14. Pendientes reales
1. **Edición directa form-vs-form** (sin asistente): **pendiente** (límite declarado; comportamiento ORM estándar).
2. **Evidencia de navegador** (conservación local en el cliente): **pendiente**.
3. **Aceptación de Cristhian**: pendiente (TEST remoto intacto).
4. **Multi-worker real**: no se levantaron dos procesos; el guard no depende del proceso que atiende (límite).

## 15. Plan de despliegue (PREPARADO, NO EJECUTADO)
Ver `docs/PLAN_DESPLIEGUE.md`: módulo `madenat_lumber_logistics` 18.0.1.24.0; migración **aditiva**; comando
`odoo -d <db> -u madenat_lumber_logistics --stop-after-init --no-http`; respaldos; smoke test; rollback.
**Requiere autorización independiente de Mauricio. El TEST remoto permanece estable para Cristhian.**

---
**SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA.**

