# RESULTADOS DE PRUEBAS (reales, en aislamiento)

## Comando y entorno

* Base aislada: **`delint_test_20261007`** (clon de `srvret_test_20261006`). `madenat_test` no se tocó.
* Código: workcopy `FIX_DELETE_INTAKE_20261007_145130/addons` montado `:ro`.
* Comando: `bash FIX_DELETE_INTAKE_20261007_145130/run_iso.sh` (ver §4 de `IDENTIDAD_REVISION.md`).
* Log definitivo: `logs/iso_run2.log`.

## Resultado

```
0 failed, 0 error(s) of 31 tests when loading database 'delint_test_20261007'
madenat_lumber_intake: 35 tests 5.24s 3787 queries
```

* **`TestDeleteAttribution` (nuevo): 11/11 OK.**
* **`TestGuideLifecycle` (existente): 20/20 OK — sin regresión.**

### Detalle `TestDeleteAttribution`

| Test | Cumple requisito de la matriz |
|---|---|
| `test_a_cancelled_without_dependencies_is_deleted` | **A** — cancelada sin dependencias se elimina desde Modo A; cierra el asistente (action a la Consola) |
| `test_b_foreign_document_same_number_does_not_block` | **B/G** — documento ajeno con nº coincidente **no** bloquea; el ajeno sobrevive; nota en `attribution_notes` |
| `test_c_ambiguous_origin_only_blocks_with_specific_message` | **C/ambigüedad** — coincidencia textual sin vínculo bloquea con mensaje específico |
| `test_d_direct_fk_link_blocks_even_without_origin_match` | **D/E/F** — FK directo detectado aunque el `origin` **no** coincida (punto ciego cerrado) |
| `test_e_linked_return_is_detected` | **E** — retorno con FK queda en `direct_link_pickings` (ya no invisible) |
| `test_f_own_lot_moves_block` | **D/G** — movimiento propio por lote bloquea |
| `test_h_revalidation_blocks_on_late_dependency` | revalidación inmediata: dependencia tardía → bloqueo en ejecución |
| `test_i_core_unlink_protection_preserved` | protecciones del core (`state`) intactas |
| `test_j_non_authorized_user_is_blocked` | permisos preservados (usuario no autorizado) |
| `test_k_no_double_count_when_found_by_several_routes` | sin conteo duplicado (hallado por nº **y** por lote) |
| `test_l_context_default_leak_reproduced_and_prevented` | §6 — fuga por contexto **reproducida** y **prevenida** |

> Iteración 1 (`logs/iso_run.log`): `1 failed, 1 error(s) of 31`. Fueron **defectos de los
> tests**, no del parche: (a) `test_h` esperaba el texto del `action_run` en lugar de la
> revalidación interna — se separó; (b) `assertRaises((UserError, AccessError))` no admite
> tuplas en este runtime. Corregidos; la iteración 2 es verde.

## Fase 2 — resultados (segunda iteración)

Log: `logs/iso_run4.log`. Comando: `run_iso.sh` (misma base aislada `delint_test_20261007`).

```
0 failed, 0 error(s) of 39 tests when loading database 'delint_test_20261007'
```

| Clase | Nº | Resultado |
|---|---|---|
| `TestGuideLifecycle` | 20 | OK (sin regresión) |
| `TestDeleteAttribution` | 11 | OK |
| `TestReturnAttribution` | 4 | OK (Modo B y retornos) |
| `TestDeleteWizardUi` | 1 | OK (**UI real del asistente** vía `Form`) |
| `TestDeleteConcurrency` | 3 | OK (**concurrencia real** con 2ª conexión) |

### Fase 2 — detalle

| Test | Cubre |
|---|---|
| `TestReturnAttribution.test_modo_b_does_not_reverse_foreign_picking` | Modo B **no** revierte documento ajeno (nº compartido) — `03` |
| `TestReturnAttribution.test_modo_b_reverses_own_picking_without_fk_leak` | Modo B revierte el propio y el retorno **no** hereda FK (contexto contaminado) — `02` |
| `TestReturnAttribution.test_own_return_with_fk_still_blocks_modo_a` | Retorno propio con FK **sigue bloqueando** |
| `TestReturnAttribution.test_case_15183_..._eligible_after_repair` | Reproducción 15183: bloqueada por FK espurio; **elegible tras reparar**, sin tocar la cadena ajena |
| `TestDeleteWizardUi.test_form_view_renders_field_and_runs` | Formulario REAL del asistente (vista con `attribution_notes`), Ejecutar cierra y vuelve a la Consola |
| `TestDeleteConcurrency.test_01_advisory_lock_serializes_same_key` | El candado serializa 2 transacciones con la **misma** clave (la 2ª se bloquea, timeout esperado) |
| `TestDeleteConcurrency.test_02_committed_dependency_blocks_deletion` | Una dependencia creada por **otra transacción y comprometida** es detectada por la revalidación → bloquea |

### Candado de concurrencia — alcance real (sin sobreafirmar)

* **Quién adquiere la misma clave:** **solo** `_acquire_delete_lock` (Modo A). Serializa
  eliminaciones Modo A concurrentes **de la misma guía**. Los **escritores de dependencias**
  (creadores de pickings/movimientos) **no** participan del candado.
* **Garantía demostrada:** una dependencia **comprometida** por otra transacción **antes** de
  la revalidación **bloquea** el borrado (`test_02`), porque la revalidación relee bajo
  READ COMMITTED.
* **Ventana residual (declarada):** una dependencia creada por otra transacción **entre** la
  revalidación y el `unlink()` **no** está cubierta por el candado. Cerrarla requiere una
  restricción a nivel de esquema (FK de las dependencias → guía) o aislamiento
  `SERIALIZABLE`. **No implementado** (propuesta, requiere aprobación). El candado **no**
  pretende evitarlo y así se documenta.

## Fase 2 — pendiente / fuera de alcance

* **Tour de navegador (Owl/Chrome):** la UI se prueba al nivel de framework (`Form`, vista
  real); no se ejecutó un tour headless en navegador (no garantizado en este stack).
* **UI “después del éxito” con refresco de Consola en sesión real:** verificado por el
  `action` devuelto (`_console_reload_action`) y la vista; el refresco de Owl no se audita.
* **Logística/billing/costing** (categorías G): cubiertas por `TestGuideLifecycle.test_11`
  (verde), sin fixtures nuevas propias.


## Caso 15183 (informe honesto, por equivalencia)

No se ejecutó el registro real. Se reproduce su **estructura** con fixtures:

* Documento **ajeno** con nº compartido (picking con `reception_id`) → **no bloquea**
  (`test_b`). Espeja el picking 436 / recepción 1369.
* **Retorno con FK** a la guía (`origin='Return of …'`) → **bloquea** por vínculo directo
  (`test_e`). Espeja el retorno 7813 (FK=33152).
* **Fuga de contexto** reproducible: crear un picking con
  `default_guia_processing_id` en el contexto le asigna el FK (`test_l`).

**Veredicto sobre 15183:** con el parche, el **falso positivo** (el picking 436 de la
recepción homónima) **deja de bloquear**; pero el caso **sigue bloqueado** por el
**vínculo directo del retorno** (FK). **No** se promete su borrado. Para eliminarlo hace
falta la **decisión de política D-POL-1** de `DICTAMEN_CAMBIO.md` §4 (tratamiento del
retorno derivado) y, en su caso, resolver el destino de la cadena 436→7813→7814 **sin**
borrar ni reasignar histórico.

## Veredicto de integridad

* No se modificó stock, quants, lotes, valoraciones ni contabilidad para facilitar
  borrados. `test_b` demuestra que un documento ajeno **sobrevive** a la eliminación.
* El snapshot firmado (`madenat.audit.log`, `guia_delete_permanent`) conserva la evidencia
  del borrado. Ningún permiso/protección se debilitó.
* Árbol activo y bases activas **sin cambios** (solo se escribió en `delint_test_20261007`).
