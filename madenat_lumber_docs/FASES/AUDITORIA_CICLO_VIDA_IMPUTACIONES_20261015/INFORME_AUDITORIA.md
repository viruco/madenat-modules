# AUDITORÍA FUNCIONAL — CICLO DE VIDA DE LAS IMPUTACIONES SV (SOLO LECTURA)

**Fecha:** 2026-10-15 · **Entorno:** LOCAL `madenat_test` · **Módulo:** `madenat_lumber_logistics` 18.0.1.32.0
**HEAD auditado:** `ee7b7c681a936775d181ebf3e215900884b941ba` (rama `feat/guia-correccion-documental-preservada-20261002`)
**Alcance:** auditoría de **solo lectura** + reproducción en transacciones **REVERTIDAS** (`odoo shell`,
`env.cr.rollback()`). **Cero cambios** en código, vistas, ACL, datos o repositorio. Sin commit, sin push, sin
remoto, sin `-u all`, sin tocar `IMP04823` ni `IMP02220`.

---

## 0. Dictamen

El ciclo de vida de `madenat.sv.imputation` está **bien construido en su vía oficial**: las transiciones tienen
método propio, permisos por rol, validaciones, locks y bitácora firmada; los saldos documentales son
**coherentes** con los repartos aplicados (verificado con SQL) y las transiciones ilegales se rechazan con
mensajes claros. **El modelo NO toca el ledger `madenat.sv.operation`** (por diseño, D-I2-12), de modo que
«aplicar» no genera asiento de ledger: el efecto es **documental** (campos `sv_assignment_*` de `stock.lot`).

Se han identificado **1 defecto ALTA**, **4 MEDIA** y **3 BAJA**, todos con reproducción. El hallazgo de mayor
severidad es que **la vía pública `write()` permite fijar `state` desde `draft`/`pending` a
`applied`/`cancelled`/`reversed` sin pasar por las acciones oficiales**, lo que **explica con exactitud la huella
de `IMP04823`** (anulada sin metadata, sin bitácora y sin firma) y permite fabricar un documento «aplicado»
**sin firma SHA-256, sin auditoría y sin pasar el techo duro ni los locks**.

---

## 1. Mapa del ciclo de vida (archivo:línea)

Modelo: `madenat_lumber_logistics/models/madenat_sv_imputation.py` (**M**) ·
asistente: `madenat_lumber_logistics/wizards/madenat_sv_imputation_wizard.py` (**W**) ·
vista: `madenat_lumber_logistics/views/madenat_sv_imputation_views.xml` (**V**) ·
ACL: `madenat_lumber_logistics/security/ir.model.access.csv` (**A**).

### 1.1 Estados y constantes

| Elemento | Ubicación |
|---|---|
| Selección de estados (`draft/pending/applied/reversed/cancelled`), `tracking=True` | M:128-137 |
| `I2_ACTIVE_STATES = ('draft','pending','applied')` (techo duro / reserva) | M:32 |
| `I2_DOCUMENTAL_STATES = ('applied',)` (saldo documental) | M:34 |
| `I2_APPLIED_WRITABLE` (campos escribibles sobre un aplicado; **`state` excluido**) | M:48-52 |
| `I2_VERSION_NEUTRAL_FIELDS` (no cuentan como contenido para `edit_version`) | M:68-75 |
| Grupos funcionales (operaciones / jefatura / gerencia) | M:38-40 |

### 1.2 Matriz completa de transiciones

| # | Transición | Origen admitido | Método / botón | Quién | Valida | Escribe | Bitácora |
|---|---|---|---|---|---|---|---|
| T1 | `(nuevo) → draft` | — | `create` (M:534-545) / `_i2_get_or_create` (M:475-532) / `_i2_build_imputation` (W:602-737) · botones **Guardar** (W:757-762), **Dejar pendiente** (W:764-769), **Aplicar** (W:771-788) | ACL write (A:27-29) = operaciones/jefatura/gerencia | elegibilidad de guía (M:1093), ≥1 etiqueta incluida (W:617-629), versión (M:621-640), unicidad por guía (M:668-681) | cabecera, líneas, repartos, `work_sv_lot_id`, `edit_version` | **NO** (solo nota de creación de `mail.thread`) |
| T2 | `draft → pending` | draft, **pending** (idempotente) | `action_pending` (M:821-828) · botón **Dejar pendiente** (V:36-38) | ACL write | estado ∈ {draft,pending} | `state`, `edit_version` | **NO** |
| T3 | `pending → draft` | **solo pending** | `action_back_to_draft` (M:830-836) · botón **Volver a borrador** (V:39-41) | ACL write | estado = pending | `state`, `edit_version` | **NO** |
| T4 | `draft/pending → applied` | draft, pending | `action_apply` (M:1114-1146) · botón **Aplicar** (V:42-44) · asistente (W:771-788) | **operaciones / jefatura / gerencia** (M:799-807) | estado, permiso, guía de retorno Sí (M:1065-1077), `_i2_validate_payload` (M:686-744: ≥1 etiqueta, nominal>0, etiqueta↔guía D10, **≥1 reparto > 0 a SV volumen**), **locks advisory ns 3 (etiquetas) y ns 2 (SV)** (M:762-792), techo duro (M:745-760), desviaciones blandas (M:1005-1023) | `state`, `executed_by_id`, `execution_date`, `snapshot_json`, `audit_hash`; sella `reversed_imputation_id` del origen (M:1143-1145) | **SÍ** `imputation` (M:1142) |
| T5 | `applied → reversed` | **solo applied** | `action_reverse` (M:1148-1178) · botón **Reversar** (V:45-47) | **solo jefatura / gerencia** (M:809-816) | estado = applied, permiso, **motivo no vacío** (M:1160-1164) | `state` (vía privada M:642-658), `reversed_by_id`, `reversal_date`, `reversal_reason`, `snapshot_json`, `audit_hash` | **SÍ** `imputation_reverse` (M:1177) |
| T6 | `draft/pending → cancelled` | draft, pending | `action_cancel` (M:838-856) · botón **Anular** (V:48-50) | ACL write (sin chequeo de grupo propio) | estado ∈ {draft,pending} | `state`, `cancelled_by_id`, `cancellation_date`, `cancellation_reason` + `message_post` | **SÍ** `imputation_cancel` (M:855) |
| T7 | `cancelled → draft` («Volver a borrador» / RESET) | **solo cancelled** | `action_reopen_to_draft` (M:912-948) · botón con `groups=` (V:52-56) | **operaciones / jefatura / gerencia** (M:858-866) | estado, permiso, **motivo** (M:929-931), `_i2_validate_reopen` (M:868-910: guía elegible, **sin otro trabajo de la guía**, **capacidad/techo duro**), locks (M:933-934, doble validación) | `state` (vía privada), `reopened_by_id`, `reopen_date`, `reopen_reason` + `message_post` | **SÍ** `imputation_reopen` (M:947) |
| T8 | `cancelled → draft` (desde el asistente) | **solo cancelled** | `action_reopen_to_draft` reutilizado | ACL write del asistente | idem T7 | idem | idem |
| — | **Prohibidas:** `applied → draft/pending/cancelled`, `reversed → *`, `cancelled → applied/reversed`, `reversed/cancelled → applied` | — | guardas M:549-579 (`write`), M:1121-1125 (`action_apply`), M:1151-1153 (`action_reverse`), M:840-843 (`action_cancel`), M:924-927 (`action_reopen_to_draft`) | — | — | — | — |

**Efecto de cada transición**
* **Aplicar (T4):** sube `sv_assignment_applied_m3` y `sv_assignment_applied_count` del SV y baja
  `sv_assignment_documental_balance_m3` (saldo = nominal SV − Σ repartos **aplicados**); en la etiqueta sube el
  «imputado activo» (reserva/consumo). **No** hay movimiento de stock, **no** hay asiento de ledger, **no** hay
  costo. Registra `snapshot_json` + `audit_hash` (SHA-256 del snapshot) y un evento `imputation` en
  `madenat.audit.log` (M:1049-1063) con el mismo hash.
* **Reversar (T5):** restituye el saldo documental del SV y libera la etiqueta; **no** borra líneas ni repartos;
  el vínculo de envío (`madenat.processor.return.link`) **no** cambia su `state` de procedencia, pero su
  `documentary_status` derivado pasa a `reversed` y marca `requires_reimputation=True`
  (`madenat_processor_return_link.py:205-232`).
* **Anular (T6):** estado terminal; **no** borra líneas ni repartos; libera la reserva documental; conserva
  `work_sv_lot_id` (relación de trabajo, solo informativa desde S2).
* **«Volver a borrador» (T7):** reabre y **vuelve a reservar** el nominal; exige que no haya otro trabajo de la
  guía y que la capacidad alcance; deja historia de anulación + reapertura.

### 1.3 Vínculo con el ledger y los envíos

| Aspecto | Evidencia |
|---|---|
| **El ledger `madenat.sv.operation` NO recibe `action_type='imputacion'`** | docstring M:11; `grep`: solo lo usan `lumber_shipment_rebaja_wizard.py:174` y `lumber_container.py:446/473/1006/1153`. En BD: `action_type` → **`rebaja|1`**, **0 filas `imputacion`** |
| El ledger no es la cabecera de la imputación | M:17-19 (D-I2-11) |
| Envíos a procesador: se sincronizan al guardar (solo `draft`) y se enlazan (`draft→linked`) al aplicar | `madenat_processor_return_link.py:669-687` (`_sync_return_links`), `689-697` (`action_link_return_links`); llamados en W:763 y W:813 |
| Estado documental del vínculo **derivado** del estado de la imputación | `madenat_processor_return_link.py:205-232` |

---

## 2. Vías que NO pasan por los métodos oficiales y transiciones sin bitácora

### 2.1 Vía pública `write()` desde `draft`/`pending` (defecto **A-1**)

`MadenatSvImputation.write` (M:547-593) sólo guarda los estados **terminales**:

```
if rec.state == 'applied':      # bloquea campos y cualquier 'state'
elif rec.state == 'cancelled':  # bloquea 'state'
elif rec.state == 'reversed' and vals.get('state'):  # bloquea 'state'
# (no hay rama para rec.state in ('draft','pending'))
```

⇒ Con el documento en `draft`/`pending`, **`write({'state': X})` acepta cualquier destino**. Reproducido
(`logs/audit_B.log`, `logs/audit_E.log`):

| Escritura directa | Resultado |
|---|---|
| `write({'state':'cancelled'})` sobre `draft` | **PERMITIDO**: `state=cancelled`, `cancelled_by_id=NULL`, `cancellation_date=NULL`, `cancellation_reason=NULL`, **0 registros en bitácora** |
| `write({'state':'applied'})` sobre `draft` | **PERMITIDO**: `state=applied`, **`audit_hash` vacío**, `executed_by_id`/`execution_date` vacíos, **0 bitácora**, y el SV **suma** el volumen como «Rebajado documental» |
| `write({'state':'applied'})` sobre `pending` | **PERMITIDO** (mismo efecto) |
| `write({'state':'reversed'})` sobre `draft` | **PERMITIDO** (documento reversado que nunca se aplicó) |
| `write({'state':'draft'})` sobre `applied`/`cancelled` | **BLOQUEADO** (correcto) |

Alcance del vector: lo pueden ejecutar los grupos con **write** en el modelo (operaciones, jefatura, gerencia —
A:27-29) por ORM/RPC (`write` es público), y cualquier código/script con `sudo()`.

### 2.2 Transiciones sin bitácora

| Transición | Bitácora | Nota |
|---|---|---|
| T1 crear/guardar | **no** | solo la nota automática «… creado» de `mail.thread` (suprimible con `mail_create_nolog`) |
| T2 `draft→pending` | **no** | sin rastro de autor/fecha más allá de `write_uid`/`write_date` |
| T3 `pending→draft` | **no** | idem |
| T4 aplicar | **sí** `imputation` | con snapshot + hash |
| T5 reversar | **sí** `imputation_reverse` | con motivo obligatorio |
| T6 anular | **sí** `imputation_cancel` | con motivo (hereda `reason` si falta) |
| T7 reabrir | **sí** `imputation_reopen` | con motivo obligatorio |
| **`write()` de estado (§2.1)** | **NO** | vector A-1: ninguna bitácora |
| Edición de **líneas/repartos** de un `draft`/`pending`/`cancelled`/`reversed` | **no** | sólo se bloquea si el padre está `applied` (M:1304/1314/1324 y M:1435/1445/1455) |

### 2.3 Otras vías no oficiales identificadas

* **SQL directo** (`UPDATE madenat_sv_imputation SET state=...`): reproduce la huella exacta
  (`state=cancelled` sin metadata y sin bitácora). No dispara recómputos de `stock.lot` (los agregados
  almacenados quedarían desactualizados hasta el siguiente `depends`), ni chatter, ni auditoría.
* **`_i2_write_protected_state` (M:642-658)** es `_`-prefijado ⇒ **no invocable por RPC**, pero **sí** invocable
  desde cualquier código Python de la propia BD/`shell` (es la vía que usan T5/T7 legítimamente).
* **`create()` con `state` distinto de `draft`**: no está restringido (M:534-545 no valida `state`) ⇒ se puede
  crear directamente un documento en `applied`/`cancelled`/`reversed` sin ninguna validación ni hash.

---

## 3. Resultados de la reproducción controlada (transacciones revertidas)

Scripts: `evidence/audit_lifecycle_A..G.py` · salida literal: `logs/audit_A..G.log`.

### Escenario 1 — crear → guardar → aplicar → reversar → nueva (misma selección) → aplicar (`audit_A.log`)

| Paso | Resultado |
|---|---|
| guardar | `IMP12850 draft` · clave `IMP-53572-38F3E2EA1BB17001` · 1 línea / 1 reparto · SV `applied_m3=0`, `balance=90` |
| aplicar | `applied` · **firma=True** · `executed_by=aud_oper` · SV `applied_m3=10`, `count=1`, `balance=90` |
| **ledger** | `action_type='imputacion'` → **0 filas** (total operaciones = 1, la `rebaja`) ⇒ **no hay asiento de ledger** |
| reversar | `reversed` · `reversed_by=aud_jef` · SV `applied_m3=0`, `balance=100` ⇒ **saldo restituido** · líneas y repartos **intactos** |
| nueva misma selección | `IMP12851 draft` · **clave distinta** · `origin_imputation_id=None` |
| aplicar la nueva | `applied` · firma=True · SV `applied_m3=10`, `balance=90` · `reversed_imputation_id` de la reversada = **None** |

### Escenario 2 — crear → anular → nueva (misma selección) → reabrir la anulada → aplicar (`audit_A.log`)

| Paso | Resultado |
|---|---|
| anular | `cancelled` · `cancelled_by=aud_oper` · **líneas conservadas=1, repartos conservados=1** (no borra nada) · SV vuelve a `balance=100` |
| nueva misma selección | `IMP12853 draft` · clave distinta (permitido: la anulada no reserva) |
| reabrir la anulada | **BLOQUEADO**: «Ya existe trabajo en preparación para esta guía: IMP12853…» ✔ |
| aplicar la nueva | `applied` · SV `applied_m3=6`, `balance=94` · la anulada sigue `cancelled` y `reopened_by=None` |

### Escenario 3 — dos borradores con las MISMAS etiquetas (`audit_B.log`)

* La **misma etiqueta** se puede asociar a **dos guías** (`guia.lot_ids` es N:M) y con cada una se crea un
  borrador **sin error** (`IMP12861`, `IMP12862`): **la doble asignación NO se impide al guardar**.
* **Se impide al APLICAR**: el **techo duro** cuenta `draft+pending+applied` (`I2_ACTIVE_STATES`, M:32) ⇒
  el primer `apply` falla con «Techo duro … acumula 20.000 m³ activos frente a 10.000 m³ nominales (D-I2-16a)».
* Tras **anular** el segundo (activo 20 → 10), el primero **sí** aplica (`applied`, SV `balance=90`).
* Dentro de la **misma guía** un segundo borrador **no** se crea: el asistente **reutiliza** el trabajo existente
  (`_i2_find_work_for_guia`) y la constraint `_check_single_work_per_guia` (M:668-681) lo impide.

### Escenario 4 — transiciones inválidas (`audit_B.log`, `audit_E.log`)

| Intento | Resultado |
|---|---|
| reversar una **reversada** | BLOQUEADO «Solo una imputación aplicada puede reversarse (AD-91)» |
| anular una **aplicada** | BLOQUEADO «Solo una imputación en borrador/pendiente puede anularse…» |
| reversar una **anulada** | BLOQUEADO (misma guarda) |
| aplicar una **anulada** | BLOQUEADO «Una imputación reversada o anulada no puede aplicarse» |
| `action_back_to_draft` sobre **aplicada** | BLOQUEADO «Solo una imputación pendiente puede volver a borrador» |
| reabrir **sin motivo** | BLOQUEADO «Indique el motivo de la reapertura (trazabilidad)» |
| reversar **sin motivo** (jefatura) | BLOQUEADO «Indique el motivo de la reversa…» |
| aplicar dos veces la misma aplicada | PERMITIDO (**idempotente**, sin efectos) |
| **`write({'state':'applied'})` sobre draft** | **PERMITIDO sin firma, sin auditoría** (defecto A-1) |
| **`write({'state':'cancelled'})` sobre draft** | **PERMITIDO sin metadata ni bitácora** (defecto M-1) |
| `write({'state':'draft'})` sobre aplicada/anulada | BLOQUEADO |

### Escenario 5 — concurrencia (`audit_B.log`)

* Con el **advisory lock de sesión `(2, sv_id)`** tomado por **otra conexión**, el `apply` falla de forma
  **controlada**: «Otra operación está modificando la misma etiqueta de retorno o el saldo documental de un SV…».
  Al liberar el lock, el mismo `apply` **procede**. ⇒ Los locks ns 2/3 (M:762-792) funcionan.
* **La reversa NO toma locks**: `action_reverse` (M:1148-1178) no llama a `_i2_lock_resources` ni compara
  `edit_version`; dos transacciones concurrentes podrían reversar a la vez con «último gana» en
  `reversed_by_id`/`reversal_date`/`reversal_reason` (defecto **M-2**; no demostrable sin dos conexiones con commit).

### Escenario 6 — permisos por grupo (`audit_G.log`)

| Grupo | Aplicar | Reversar | Anular | Volver a borrador | Crear borrador |
|---|---|---|---|---|---|
| operaciones | ✅ | ❌ AccessError (solo jefatura/gerencia) | ✅ | ✅ | ✅ |
| jefatura | ✅ | ✅ | ✅ | ✅ | ✅ |
| gerencia | ✅ | ✅ | ✅ | ✅ | ✅ |
| auditoría | ❌ AccessError | n/a | ❌ AccessError (ACL) | n/a | ❌ AccessError |
| sin grupos | ❌ AccessError | n/a | ❌ AccessError (ACL) | n/a | ❌ AccessError |

### Escenario 7 — saldos e invariantes tras cada escenario

Coherentes en todos los casos (ver §5): p. ej. SV de 100 m³ → aplicar 6 → `balance=94`; reversar → `100`; nueva
aplicación → `94`.

---

## 4. Cómo quedó `IMP04823` anulada **sin rastro** (forense)

Datos reales, solo lectura (`logs/audit_C.log`, `logs/audit_E.log`, `logs/audit_F.log`):

| Documento | state | firma | líneas | repartos | `create_uid`/`write_uid` | chatter | bitácora | metadata anulación |
|---|---|---|---|---|---|---|---|---|
| `IMP00946` (492) | applied | ✔ | 1 | 1 | 1 / 1 | 1 (creación) | `imputation` | — |
| `IMP02220` (1189) | applied | ✔ | 2 | **0** | 8 / 8 | 1 (creación) | `imputation` | — |
| **`IMP04823` (2733)** | **cancelled** | **✘** | **0** | 0 | 8 / 8 | **0** | **0** | **ninguna** |

**Conclusiones razonadas (con reproducción):**

1. **No fue `action_cancel`.** Esa acción (M:838-856) **siempre** escribe `cancelled_by_id`,
   `cancellation_date`, `cancellation_reason`, un `message_post` y la bitácora `imputation_cancel`. En `IMP04823`
   los tres campos son **NULL** y **no existe** evento en `madenat.audit_log` (0 filas con su `batch_id`).
2. **La huella se reproduce exactamente con `write({'state':'cancelled'})`** (ORM o SQL) desde `draft`: la
   reproducción da `state=cancelled`, `cancelled_by_id NULL`, `cancellation_date NULL`,
   `cancellation_reason NULL` y **0 bitácora** — idéntico a `IMP04823` (`logs/audit_E.log`, casos 1/3/4).
3. **Anomalía añadida: 0 mensajes de chatter.** Toda imputación creada por ORM recibe la nota automática
   «Imputación documental SV (I2) creado» (reproducido: `create()` normal → 1 mensaje). `IMP04823` tiene **0**; la
   variante que reproduce 0 mensajes **conservando** `create_uid`/`write_uid` es `create()` con
   `mail_create_nolog` (reproducido en `logs/audit_F.log`). Alternativas equivalentes: SQL `INSERT`/`UPDATE` con
   `write_uid`/`write_date` explícitos, o borrado manual del chatter.
4. **Ventana temporal coherente con una intervención manual/de desarrollo**: creado `2026-10-11 02:27:56` y
   modificado `2026-10-12 19:43:36` por **uid 8** (mismo usuario del resto del trabajo del 11–12/10), sin ningún
   rastro funcional.
5. **El vaciado (0 líneas) NO vino de la anulación** (que conserva líneas, §3-Esc.2) sino del **guardado sin
   etiquetas**, ya corregido en la FASE 10 (**F3/S3**: `wizards/madenat_sv_imputation_wizard.py:617-629`).

**Veredicto:** `IMP04823` proviene de una **vía no oficial** (escritura directa de estado + creación sin registro
de chatter), no de un defecto del flujo actual. La causa raíz es la **ausencia de guarda para `draft`/`pending`
en `write()`** (**A-1**), que es además el vector para fabricar un «aplicado sin firma».

---

## 5. Hallazgos clasificados

### ALTA

**A-1 · `write()` permite cambiar el estado desde `draft`/`pending` sin pasar por las acciones oficiales.**
*Causa:* `MadenatSvImputation.write` (M:547-593) sólo protege `applied`/`cancelled`/`reversed`; no hay rama para
`draft`/`pending`, de modo que `state` es libre en esos estados.
*Efecto:* (a) anular sin metadata ni bitácora (huella de `IMP04823`); (b) marcar `applied` **sin firma SHA-256,
sin snapshot, sin `executed_by`, sin auditoría, sin techo duro y sin locks**, y ese documento **cuenta** en el
saldo documental (`I2_DOCUMENTAL_STATES`, M:34) y en `sv_assignment_applied_m3`; (c) `draft → reversed` sin haber
estado aplicada; (d) `create({'state': 'applied'})` directo también es posible (M:534-545).
*Reproducción:* `logs/audit_B.log` (bloque «ESC-4b») y `logs/audit_E.log` (casos 6/7/8).
*Alcance:* RPC/ORM por operaciones/jefatura/gerencia (A:27-29) y cualquier script con `sudo()`.

### MEDIA

**M-1 · Anulación sin trazabilidad posible por `write` (consecuencia directa de A-1).** `state='cancelled'` sin
`cancelled_by_id`/`cancellation_date`/`cancellation_reason` ni bitácora: no se puede reconstruir quién ni por qué.
*Reproducción:* `logs/audit_E.log` (caso 1). *Invariante en datos reales:* `canceladas_sin_metadata=1`,
`canceladas_sin_bitacora=1` (`IMP04823`).

**M-2 · La reversa no toma locks ni valida versión.** `action_reverse` (M:1148-1178) no llama a
`_i2_lock_resources` (M:762-792) ni a `_i2_assert_edit_version` (M:621-640): dos transacciones concurrentes
pueden reversar a la vez y la segunda **sobrescribe** `reversed_by_id`/`reversal_date`/`reversal_reason`/
`audit_hash` («último gana»), dejando la firma correspondiente a la segunda. *Reproducción:* lectura de código +
verificación de que `apply` **sí** bloquea (Esc. 5) mientras `reverse` no toma ningún lock.
*Sugerencia de prueba:* dos conexiones sobre el mismo `applied` (patrón de `test_sv_rebaja_save_lock_tx`).

**M-3 · Inconsistencia `compute_sudo`/`store` en `stock.lot`: comportamiento distinto según el usuario.** Los
agregados canónicos son `store=True, compute_sudo=True` (M:1567-1575, cómputo M:1596-1624) mientras la proyección
viva y el trabajo son `store=False` con `compute_sudo` implícito `False` (M:1561-1563, M:1533-1546, cómputo
M:1643-1660). Consecuencia reproducible: un usuario **sin ACL** sobre `madenat.sv.imputation` obtiene
**`AccessError`** al leer `sv_assignment_work_imputation_ids`/`_work_count` (porque el compute hace `search` sin
`sudo`), aunque **sí** ve los agregados almacenados (`sudo`). *Reproducción:* `logs/audit_D.log` (bloque b:
`sin_grupos → AccessError`; `auditoria`/superusuario → `work_count=1`).
*Aclaración importante:* el aviso histórico de Odoo
(`UserWarning: stock.lot: inconsistent 'compute_sudo' … inconsistent 'store' …`, visto en
`SIMPLE_REBAJA_20261011/logs/regression.log:43/89`) **ya no se emite** con el código actual: 0 `UserWarning` en
las cargas recientes (`FASE10_…/logs/{s1_logistics_full,s2_logistics_full,clean_install}.log`), porque los
**métodos** se separaron (AUD-ETQ-08/10). La incoherencia que permanece es **de régimen de acceso**, no de
registry.

**M-4 · El uso normal del asistente no enlaza la cadena de corrección.** `origin_imputation_id` /
`reversed_imputation_id` (M:178-185) se sellan en `action_apply` **solo si la nueva operación ya trae
`origin_imputation_id`** (M:1143-1145), pero el asistente **nunca lo fija**: en el Esc. 1 la nueva imputación
(uniforme tras reversar) quedó con `origin=None` y la reversada con `reversed_imputation_id=None`.
*Efecto:* la «cadena de corrección» no se reconstruye por estos campos; solo por la clave/firma y la bitácora.

### BAJA

**B-1 · `create()` acepta `state` distinto de `draft`** (M:534-545 no lo valida) ⇒ se puede nacer en estado
terminal sin validaciones ni hash (variante de A-1).

**B-2 · Líneas y repartos de documentos terminales (`cancelled`/`reversed`) son editables por ORM/RPC.** Los
guards de los modelos hijos sólo bloquean cuando el padre está `applied` (M:1304/1314/1324 y M:1435/1445/1455):
se pueden añadir/quitar líneas de un anulado y luego reabrirlo con un contenido distinto al que se anuló.
*(La UI no ofrece esa edición; el vector es ORM/RPC.)*

**B-3 · `action_cancel` no exige grupo específico ni motivo** (M:838-856): cualquier rol con `write`
(operaciones incluida) anula sin motivo obligatorio, y el motivo se **hereda** de `reason` si está vacío
(M:848). Coherente con la política vigente, pero deja la anulación con menos trazabilidad que la reversa.

---

## 6. Invariantes de datos en `madenat_test` (solo lectura, `psql`)

Ejecutado en una sesión **sin datos de prueba** (los escenarios corren con `rollback`):

| Invariante | Valor | Interpretación |
|---|---|---|
| `imp_total` | **3** | `492`, `1189`, `2733` |
| `applied_sin_firma` | **0** | todos los aplicados tienen `audit_hash` ✔ |
| `applied_sin_snapshot` | **0** | ✔ |
| `applied_sin_ejecutor` | **0** | todos tienen `executed_by_id` + `execution_date` ✔ |
| `applied_sin_reparto_positivo` | **1** | ⚠ `IMP02220`: aplicada **con 0 repartos**, estado que hoy `action_apply` prohíbe (M:686-744). Herencia previa al contrato (ANOMALÍA DE DATO, no de código) |
| `canceladas` / `canceladas_sin_metadata` / `canceladas_sin_bitacora` | **1 / 1 / 1** | ⚠ `IMP04823` (hallazgos A-1/M-1) |
| `terminales_con_lineas` | **0** | los terminales existentes no conservan líneas (por el vaciado previo, no por la anulación) |
| `reversed_total` | **0** | no hay reversas persistidas |
| `claves_duplicadas` | **0** | UNIQUE respetado ✔ |
| `lineas_huerfanas` / `repartos_huerfanos` / `repartos_sin_sv` | **0 / 0 / 0** | integridad referencial ✔ |
| `saldo_doc_negativo` | **0** | ningún `sv_assignment_documental_balance_m3 < 0` ✔ |
| `audit_imp_sin_guia` | **8** | 8 eventos `imputation` **sin `guia_processing_id`**, todos de guías `TX10` (2026-10-12/13, ver `logs/audit_E.log`) ⇒ **defecto de dato/bitácora** |
| `mail_msg_IMP04823` / `IMP02220` | **0 / 1** | confirma el forense (§4) |
| `sv_op_imputacion` | **0** | el ledger no recibe la imputación (por diseño) |
| `sv.operation.action_type` | **`rebaja|1`** | única fila del ledger |

**Coherencia de agregados `stock.lot` vs repartos aplicados (SQL):**

```
lot=15892 SV00000001175  stored_applied=10.000  real=10.000  stored_cnt=1  real_cnt=1   ✔
                         nominal_etiquetas=10.000 · stored_balance=30.315 · stored_nominal=40.315   ✔ (40.315 − 10)
```

⇒ **los campos almacenados `sv_assignment_*` son coherentes** con los repartos aplicados y con el saldo
documental. No se observó ningún caso de valor obsoleto ni divergente entre usuario y usuario **salvo** el
`AccessError` de M-3 (que es un problema de permisos, no de exactitud).

---

## 7. Propuestas mínimas de corrección (NO implementadas)

| Hallazgo | Propuesta mínima | Pruebas necesarias |
|---|---|---|
| **A-1** | En `write` (M:547) **rechazar `state` en `vals`** para `draft`/`pending` salvo por la vía privada `_i2_write_protected_state` (p. ej. que `action_pending`/`action_back_to_draft` marquen la transición con un `context` interno no falsificable desde el cliente, o que usen también la vía privada). En `create`, **forzar `state='draft'`**. | `write`/RPC `draft→applied|cancelled|reversed` → `UserError`; `action_pending`/`action_back_to_draft`/`action_apply`/`action_cancel`/`action_reverse`/`action_reopen_to_draft` siguen verdes; `create(state='applied')` rechazado; regresión de SAVE/LOCK/RESET/SIMPLE |
| **M-1** | Se resuelve con A-1: al ser `action_cancel` la única vía, siempre deja metadata + bitácora. | Nuevo invariante de test: toda `cancelled` tiene `cancelled_by_id`/`cancellation_date` y un `imputation_cancel` |
| **M-2** | Añadir `_i2_lock_resources()` + `_i2_assert_edit_version` **y revalidar el estado tras el lock** en `action_reverse` (mismo patrón que `action_apply`, M:1131-1132, y `action_reopen_to_draft`, M:933-934). | Dos conexiones sobre el mismo `applied`: sólo una revierte; la segunda recibe el mensaje de conflicto (patrón `test_sv_rebaja_save_lock_tx`) |
| **M-3** | Decidir régimen: excluir los campos de trabajo de la vista para quien no tenga el grupo, **o** documentar el `AccessError`, **o** envolver el `search` del compute con `sudo` acotado a compañía (como los agregados canónicos). | Formulario de `stock.lot` legible por usuario de cada grupo sin `AccessError` (o con mensaje claro); el valor no difiere del canónico |
| **M-4** | Que el asistente fije `origin_imputation_id` cuando la operación se crea tras una reversa/anulación de la misma guía (el dato ya está disponible al resolver la clave en `_i2_get_or_create`). | aplicar → reversar → nueva con la misma selección ⇒ `origin_imputation_id` = la reversada y `reversed_imputation_id` recíproco |
| **B-1** | Segunda parte de A-1 (`create` sólo `draft`). | Idem A-1 |
| **B-2** | Extender los guards de `madenat.sv.imputation.line`/`.sv.line` a **todo estado ≠ `draft`/`pending`** (hoy sólo bloquean `applied`: M:1304/1314/1324, M:1435/1445/1455). | Añadir/quitar líneas de `cancelled`/`reversed` → `UserError`; el RESET reabre con el contenido íntegro |
| **B-3** | (Decisión funcional) exigir motivo en `action_cancel` como en la reversa, o restringirla a jefatura/gerencia. | Pruebas de mensaje y de permisos por grupo |
| **Datos** | `IMP02220` (`applied` sin repartos) e `IMP04823` (`cancelled` sin metadata) son **dato de origen**, no defecto de código. Decisión de negocio (conservar como historia / regularizar) — **fuera del alcance y no ejecutada**. | — |

> Ninguna propuesta se ha implementado. Cualquier cambio requeriría fase propia con TDD y regresión por nombre.

---

## 8. Evidencia de que NADA cambió

```
HEAD = ee7b7c681a936775d181ebf3e215900884b941ba   (idéntico antes y después)
rama = feat/guia-correccion-documental-preservada-20261002
git status --porcelain → 11 entradas (10 costing + 1 menú de reports)   [idénticas antes/después]

madenat_test → guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1 sv_op=1
               (idéntico antes y después de la auditoría)
IMP00946 applied / IMP02220 applied IMP-1198-E95825AAF94E58AD / IMP04823 cancelled IMP-1198-A87816E2021EC9AA
mail_message de IMP04823 = 0 (sin cambios)
```

* **Todos** los escenarios corrieron con `env.cr.rollback()` y **nunca** `commit` ⇒ **cero residuos**
  (`audit_A..G.log` terminan con «ROLLBACK (sin cambios persistidos)»).
* **Sin** `-u`, `-u all`, `--test-enable`, escrituras de negocio, ni SQL de escritura fuera de la transacción
  revertida; sin cambios en vistas, ACL, secuencias ni parámetros.
* **No** se abrió `IMP04823` ni `IMP02220` en modo escritura (solo `read`/`search`/SQL de lectura).
* Los scripts y logs de esta auditoría viven en `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/`, **fuera** del
  repositorio git (`custom_addons/`), por lo que `git status` sigue con **11** entradas.

---

## 9. Criterio de cierre

| Criterio | Estado |
|---|---|
| Cada transición de estado documentada, con quién la ejecuta y qué escribe | ✅ §1.2 (T1–T8 + prohibidas) |
| Reversa, nueva imputación y anulación probadas en escenarios reproducibles, con saldos coherentes o el defecto demostrado | ✅ §3 (Esc. 1–7) + §6 (coherencia SQL) |
| Se sabe cómo quedó `IMP04823` anulada sin rastro | ✅ §4 (vía no oficial reproducida; no fue `action_cancel`) |
| Cero cambios en datos, código y repositorio | ✅ §8 |

---

## 10. Anexo — comandos de reproducción

```bash
# Escenarios (transacción revertida; NUNCA commit)
for S in A B C D E F G; do
  docker exec -i odoo18_app odoo shell -d madenat_test --no-http \
    < AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/evidence/audit_lifecycle_${S}.py \
    > AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/logs/audit_${S}.log 2>&1
done

# Verificación de no-cambios
cd custom_addons && git status --porcelain | wc -l && git rev-parse HEAD
docker exec odoo18_db psql -U odoo -d madenat_test -t -A -F'|' -c \
  "SELECT (SELECT count(*) FROM madenat_guia_processing), (SELECT count(*) FROM stock_lot),
          (SELECT count(*) FROM madenat_sv_imputation), (SELECT count(*) FROM madenat_sv_operation)"
```

**Archivos:** `evidence/audit_lifecycle_A..G.py` (7 scripts) · `logs/audit_A..G.log` (salida literal) · este
informe (`INFORME_AUDITORIA.md`).

