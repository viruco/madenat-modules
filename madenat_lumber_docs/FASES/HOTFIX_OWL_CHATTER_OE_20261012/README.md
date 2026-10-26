# HOTFIX_OWL_CHATTER_OE_20261012 — Evidencia (OwlError al «Agregar una línea» en IMPxxxx)

**Fecha:** 2026-10-12 · **Entorno:** `madenat_test` / `odoo18_app` (PostgreSQL `odoo18_db`), Odoo Server `18.0-20260817`.
**Naturaleza:** expediente de **evidencia** de la incidencia bloqueante de renderización del chatter. La doctrina
vive en `madenat_lumber_docs/CANON/` (`19 §19.33`, `18`, `02 §17.16.19`, `03 §30`, `05`, `INDICE`).

## 1. Error real del navegador (reportado por Mauricio)

Pantalla: **formulario del documento persistente de rebaja** (`madenat.sv.imputation`, p. ej. `IMP04823`,
abierto desde «Rebaja de etiquetas / SV…»).

```
Caused by: TypeError: Cannot read properties of undefined (reading 'includes')
    at get urlRelation
    at Many2OneField.template
```

Acción: pulsar **«Agregar una línea»** en una tabla del formulario cuyos encabezados son
`Fecha · Asunto · Autor · Modelo de documento relacionado · ID del documento relacionado`
y otra con `Nombre del modelo del documento relacionado · ID del documento relacionado · Contacto relacionado`.

## 2. Mapeo (lista → modelo → campo conflictivo → tipo → editable → quién crea → permisos)

| Lista (encabezados) | Modelo | Campos | Tipo | Editable en vista | Quién crea | Permisos |
|---|---|---|---|---|---|---|
| `message_ids` (Fecha/Asunto/Autor/Modelo de documento relacionado/ID del documento relacionado) | `mail.message` | `date, subject, author_id, model, res_id` | `res_id` = **`many2one_reference`** (`model_field='model'`); `author_id` = `many2one` | Lista por defecto `mail.message.list` (`view_message_tree`, prioridad 20) — **sin** `create="0"` ⇒ ofrece «Agregar una línea» | `mail.thread` (post del chatter); **no** por la vista | `mail.message`: sin create manual desde el negocio (ACL de `mail`) |
| `message_follower_ids` (Nombre del modelo del documento relacionado/ID del documento relacionado/Contacto relacionado) | `mail.followers` | `res_model, res_id, partner_id` | `res_id` = **`many2one_reference`** (`model_field='res_model'`); `partner_id` = `many2one` | Lista por defecto `mail.followers.list` (`view_followers_tree`) — **sin** `create="0"` | `mail.thread` (seguidores); **no** por la vista | `mail.followers`: idem |

**No** son modelos MADENAT: son los campos del chatter (`message_ids`/`message_follower_ids` de
`mail.thread`). Ningún modelo `madenat.*` define campos `model`/`res_id`/`res_model`
(solo `madenat.sv.internal.marker.res_id` = `integer`, ajeno).

## 3. Causa demostrada

**Odoo 18 CE 18.0-20260817 ya NO compila el marcado heredado `div.oe_chatter`.**

- El compilador de formularios opera por **selector de nodo**: en
  `mail/static/src/chatter/web/form_compiler.js` el chatter se registra con
  `registry.category("form_compilers").add("chatter_compiler", { selector: "chatter", fn: compileChatter })`,
  es decir, sobre el **elemento `<chatter/>`**.
- La cadena literal `oe_chatter` **no existe** en los assets del core
  (`grep -rin oe_chatter web/static/src mail/static/src` ⇒ `EXIT=1`, 0 coincidencias). No hay shim de
  compatibilidad.
- Las vistas del core declaran el chatter con `<chatter/>` (p. ej. `mail/views/res_partner_views.xml:22`).
- Con `div.oe_chatter`, el `<div>` se compila como **div genérico** y sus hijos
  `<field name="message_follower_ids"/>`/`<field name="message_ids"/>` quedan como **campos One2many sueltos**
  ⇒ se renderizan con sus **listas por defecto editables** (`mail.followers`/`mail.message`), que **sí** ofrecen
  «Agregar una línea».
- Al interactuar con esas columnas, el cliente intenta calcular la URL del documento relacionado
  (`Many2OneField.get urlRelation` → `this.relation.includes(".")`); para `res_id`
  (`many2one_reference`, sin relación fija) la relación no es determinable y `this.relation` es `undefined`
  ⇒ `TypeError: Cannot read properties of undefined (reading 'includes')`.

La **hipótesis del reporte** (campo renderizado como `many2one` sin modelo determinable) se **confirma**, con la
precisión adicional de que el disparador es el **chatter no compilado** y el campo concreto es `res_id`
(`many2one_reference`) de las listas `mail.message`/`mail.followers`. Se **descartan**: widget `many2one` sobre
campo no-Many2one (0 casos), comodel inválido (0), campo duplicado (0), cambio de tipo de campo, y herencias
(faltantes): **ninguna vista hereda** `madenat.sv.imputation.form`.

## 4. Corrección aplicada (mínima) y alternativas descartadas

**Cambio:** reemplazar el `<div class="oe_chatter">…</div>` por el elemento canónico **`<chatter/>`** en las
**dos** vistas instaladas afectadas (mismo módulo `madenat_lumber_logistics`):

- `views/madenat_sv_imputation_views.xml` → `madenat.sv.imputation.form`.
- `views/madenat_processor_return_link_views.xml` → `madenat.processor.return.link.form`
  (formulario del mecanismo envío–retorno, mismo recorrido de rebaja; mismo defecto).

`madenat.sv.imputation` solo hereda `mail.thread` (sin `mail.activity.mixin`), por lo que el chatter resuelve
`has_activities=False` (auto). No se añade ni cambia nada más.

**Alternativas descartadas:** capturar el error en JavaScript; tocar `mail`/assets del core; crear un
chatter propio; eliminar los campos o la tabla; cambiar el modelo o los datos; `create="0"` sobre las listas
por defecto de `mail.followers`/`mail.message` (global y fuera de alcance). El historial **sigue visible**
dentro del chatter (Odoo 18); no se oculta nada.

## 5. Riesgo RPC residual y decisión requerida

`mail.message`/`mail.followers` permiten `create` por RPC (ACL de `mail`). La vista **no** debe crear filas de
chatter a mano: los registros los generan las operaciones del sistema (`message_post`, seguidores). **No** se
amplían ni restringen permisos/ACL ni se añade `ir.rule` (fuera de autorización). **Decisión separada
requerida** si se desea endurecer el alta manual de `mail.message`/`mail.followers` por RPC; **no** se ejecuta
en este hotfix.

## 6. Vistas similares: hallazgos

- `madenat_vendor_payment/views/lumber_shipment_cost_views.xml:151` conserva un `div.oe_chatter`
  (con `message_follower_ids`/`activity_ids`/`message_ids`). **Mismo riesgo** si el módulo se instala; **NO
  corregido** (módulo **no instalado** en `madenat_test` ⇒ no reproduce; fuera del formulario afectado). **Hallazgo.**
- Resto de MADENAT: coherente con el core — usan `<chatter/>` (`guia_processing`, `stock_lot`, `lumber_reception`,
  `shipping_voyage/vessel/booking`, `lumber_container`, `logistics`, `lumber_export_shipment`,
  `toll_processing_order`, `lumber_cost_distribution`, `lumber_billing_consolidation`).
- 0 vistas MADENAT con `widget="many2one"` sobre un campo que no sea Many2one; 0 `many2one_reference` sin su
  `model_field` en la vista (verificado por prueba `VIEW-05`).

## 7. Pruebas y regresión (cifras y baseline)

**Pruebas nuevas** (`tests/test_hotfix_owl_chatter.py`, `TestHotfixOwlChatter`, VIEW-01..05 de servidor):

```
odoo -d madenat_test --http-port=8079 -u madenat_lumber_logistics --test-enable --stop-after-init \
     --test-tags madenat_lumber_logistics:TestHotfixOwlChatter
→ 0 failed, 0 error(s) of 5 tests   (EXIT=0)   [logs/logs_viewtests.log]
```

**Regresión `madenat_lumber_logistics`:**

```
→ 4 failed, 0 error(s) of 506 tests   (EXIT=1)   [logs/regression_logistics.log]
```

Fallas = **las mismas 4 preexistentes**: `TestProcessorLocations.test_09`, `TestProcessorShipmentAD89.test_t1/t5/t6`.
Baseline del mismo día (mismo WIP, pre-hotfix): `FASES/BLINDAJE_REBAJA_LOCAL_20261012/` (artefacto `regression_logistics.log` en `logs/`, fuera de git)
= **4 failed, 0 error(s) of 444 tests** ⇒ **0 fallas nuevas**.

**Regresión `core + intake + logistics`:**

```
→ 6 failed, 4 error(s) of 1284 tests   (EXIT=1)   [logs/regression_core_intake_logistics.log]
```

Fallas/errores = **conjunto IDÉNTICO al baseline** del mismo día
(`FASES/BLINDAJE_REBAJA_LOCAL_20261012/` (artefacto `regression.log` en `logs/`, fuera de git) = **6 failed, 4 error(s) of 1217 tests**):
`TestGuiaPickingLink.test_t_g2_03`, `TestOrphanMoveCleanupSavepoint.test_partial_batch_failure…`,
`TestProcessorLocations.test_09`, `TestProcessorShipmentAD89.test_t1/t5/t6`,
`TestSvConcurrency.test_01`, `TestSvEscalationSecurity.test_02/03/04`
(errores de **entorno/concurrencia**: `statement timeout`, `could not obtain lock…`, `could not serialize…`,
`null value in column "reason"`, FK `stock_quant_lot_id_fkey`). **0 fallas/errores nuevos**
(1284−1217 = 67 pruebas nuevas del WIP ajeno, ajenas al cambio). **No** se debilitó ninguna prueba.

> El cambio es **exclusivamente de vistas** (marcado del chatter); no toca modelos, datos ni permisos.

## 8. Evidencia de navegador (límite explícito)

**No hay navegador** en el entorno (ni `chromium`/`firefox`/`playwright`): las vistas **VIEW-01/02/03/04/06/07
en cliente quedan PENDIENTES**. Una validación XML/ORM **no** demuestra que el cliente Owl evalúe la vista sin
errores. Guion exacto de comprobación manual: `docs/GUION_MANUAL_NAVEGADOR.md`.

## 9. Versiones instaladas localmente (`madenat_test`)

| Módulo | Versión |
|---|---|
| `madenat_lumber_logistics` | **18.0.1.25.0 → 18.0.1.26.0** (este hotfix) |
| `madenat_lumber_core` | 18.0.6.7.0 (sin cambios) |
| `madenat_lumber_intake` | 18.0.0.13.0 (sin cambios) |

`odoo -d madenat_test -u madenat_lumber_logistics --stop-after-init --no-http` → **EXIT 0**, 0 `ERROR`
(`logs/logs_update.log`; solo `WARNING` preexistentes de etiquetas/roles/grupos).

## 10. Documentación actualizada

- `madenat_lumber_docs/CANON/19_IMPUTACION_SV_Y_PROCESADORES.md` → **§19.33** (versión 1.30.0 → **1.31.0**).
- `madenat_lumber_docs/CANON/02_CONTINUIDAD.md` → **§17.16.19** (versión 12.34.0 → **12.35.0**).
- `madenat_lumber_docs/CANON/03_TESTS.md` → **§30** (versión 6.x → +1).
- `madenat_lumber_docs/CANON/05_BACKLOG.md` → sección del hotfix.
- `madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md` → versión + entrada.
- `madenat_lumber_docs/WIKI/00_INDICE.md` → versión + entrada.
- `madenat_lumber_logistics/CHANGELOG.md` → `[18.0.1.26.0]`.
- Plan de despliegue acumulado: `docs/PLAN_DESPLIEGUE_ACUMULADO.md` (**sin ejecutar**).

## 11. Archivos afectados y WIP ajeno preservado

**Tocados por este hotfix (módulo `madenat_lumber_logistics`):**
- `views/madenat_sv_imputation_views.xml` (chatter).
- `views/madenat_processor_return_link_views.xml` (chatter).
- `tests/test_hotfix_owl_chatter.py` (**nuevo**), `tests/__init__.py` (import).
- `__manifest__.py` (**18.0.1.25.0 → 18.0.1.26.0**), `CHANGELOG.md`.

**WIP ajeno:** preservado. `git status` = **104** entradas (incluye el WIP previo de `core`/`intake`/`costing`/
`logistics` y el presente hotfix); **solo** se editaron los archivos anteriores. Volcados: `code/wip_status_post.txt`.
**Sin** commit, push, despliegue, `-u all`, ni reparación histórica. **No** se tocaron `IMP04823` ni `IMP02220`.

## 12. Plan de despliegue acumulado (sin ejecutarlo)

Ver `docs/PLAN_DESPLIEGUE_ACUMULADO.md`. Paquete pendiente para TEST remoto:
`madenat_lumber_core` **18.0.6.7.0**, `madenat_lumber_logistics` **18.0.1.26.0** (este hotfix),
`madenat_lumber_intake` **18.0.0.13.0** (+ WIP de `costing`). El **TEST remoto NO se inspecciona ni se toca**;
su versión instalada debe leerse **en solo lectura** antes de desplegar. Cristhian sigue en la versión anterior.

## 13. Pendientes

1. **Aceptación en navegador** (VIEW-01/02/03/04/06/07 cliente) — guion `docs/GUION_MANUAL_NAVEGADOR.md`.
2. **Hallazgo** `madenat_vendor_payment` (`div.oe_chatter`) — corregir cuando se autorice (módulo no instalado).
3. **Decisión separada** sobre `create` por RPC de `mail.message`/`mail.followers` (no ejecutada).
4. Confirmar versión del TEST remoto (solo lectura) antes del despliegue.

