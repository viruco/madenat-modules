# FIX_ACL_GUIA_20261007_1630 — Fallo de acceso omitido en la eliminación (ACL)

Caso: guía **`madenat.guia.processing` ID 33152** / número **15183** (`cancelled`).
MADENAT — Odoo 18 CE. **Entrega aislada. NO aplicada al árbol activo ni a `madenat_test`.**

## 0. Resumen ejecutivo

El rechazo observado **NO** es una precondición del asistente ni un problema de
atribución material: es un **`AccessError` de ACL**. La tabla `ir.model.access`
de `madenat.guia.processing` **no concedía `perm_unlink` a ningún grupo** (0 en
las tres filas: Usuario interno, Operaciones, Jefatura de Operaciones). El Modo A
llama `guia.unlink()` como el usuario de la sesión; el override del core ejecuta
sus guardas y termina en `super().unlink()`, donde **Odoo 18 hace
`check_access('unlink')`** y, al no hallar grupo, lanza exactamente:

```
No puede eliminar registros 'Recepción de Guías Procesadas'
(madenat.guia.processing). Ningún grupo permite esta operación por el momento.
```

Reproducido y confirmado en aislamiento sin `sudo` (ver §6).

## 1. Causa exacta (cadena de rechazo)

Ruta real del Modo A (asistente → `action_run` → `unlink`):

1. `action_run()` (`intake_guide_lifecycle_wizard.py:691`) → `_run_delete_definitive()` (`:744`) → **`guia.unlink()`** (`:770`).
2. Override del core `MadenatGuiaProcessing.unlink()`
   (`madenat_guia_processing.py:5945`):
   - `_sv_test_cleanup_allowed(...)` → **False** en el servidor persistente.
   - guarda de estado `state in ('draft','cancelled')` → **OK** (cancelled).
   - `_cleanup_orphan_moves_guia()` (`:5970`) → exige `stock.group_stock_manager`
     → el usuario real **lo tiene**, así que **pasa**.
   - `return super().unlink()` → **`BaseModel.unlink()`** (`odoo/models.py:4535`)
     → **`self.check_access('unlink')`** (`:4546`).
3. `_check_access('unlink')` (`models.py:4464`) → `ir.model.access.check(
   'madenat.guia.processing', 'unlink', raise_exception=False)` → **False**
   (ningún grupo concede `unlink`) → devuelve `_make_access_error` → **`AccessError`**.

**Punto exacto de rechazo:** `odoo/models.py:4546` (`self.check_access('unlink')`
dentro de `BaseModel.unlink`). No es el asistente ni el override del core: es la
**capa de ACL**, que se evalúa al final, tras las guardas propias del modelo.

> La auditoría previa (`AUDIT_DELETE_INTAKE_20261007_130559`) miró la **ACL de la
> Consola** (`ir.model.access.csv:3`) y las **guardas `has_group`** del modelo, pero
> **nunca** consultó las filas de `ir.model.access` **del modelo `madenat.guia.processing`**.
> De ahí su frase «los dos guards relevantes pasarían» (cierta) y su conclusión
> equivocada de que «no es un problema de permisos».

## 2. Verificación acotada (solo lectura)

| Dato | Valor verificado (base `madenat_test`) |
|---|---|
| Usuario del caso | **8 = cristhian.elguetag@gmail.com (Cristhian Elgueta)** — `create_uid`/`write_uid` de 33152; no se asumió |
| Guía | `id=33152`, `name='15183'`, `state='cancelled'` |
| Grupos de user 8 | `Operaciones` (gid 256) + `Jefatura de Operaciones` (gid 261) + `stock.group_stock_manager` (gid 49) + `stock.group_stock_user` |
| ACL runtime `madenat.guia.processing` | Operaciones `(1,1,1,0)`; Usuario interno `(1,0,0,0)`; **Jefatura `(1,1,1,0)`** → **`perm_unlink = 0` en TODAS** |
| Correspondencia con `ir.model.access.csv` | Coincide: líneas 26–28 (`_user`,`_operaciones`,`_manager`) con `unlink=0` |
| Reglas de registro (`ir.rule`) | No determinan el rechazo (falla en la capa ACL, antes que la regla) |
| `madenat.dev_cleanup_enabled` | `True` (solo relaja evidencia documental del Modo A, **no** la ACL) |

**La sesión sí era el usuario 8** (no se asumió): es el `write_uid` de la guía y el
usuario que ejecutó la cancelación/Fase C. Y **`stock_manager` NO concede `unlink`**
sobre este modelo: es una guarda aparte que el modelo exige, pero no otorga permiso.

## 3. Por qué las pruebas anteriores no detectaron el rechazo

- La suite `FIX_DELETE_INTAKE_20261007_145130` (39/39 verde) corre en
  `TransactionCase`, cuyo `env` es **superusuario** (`env.su = True`). En Odoo 18
  `_check_access` **solo se evalúa si `not self.env.su`** (`models.py:4443`); con
  superusuario la ACL de `unlink` queda **puenteada**. Por eso pasó.
- Las pruebas invocaban el **flujo completo** (`action_run`), pero **siempre** con
  `self.env` (admin) y **nunca** con `with_user(<usuario operativo>)` ni `su=False`.
- `test_j_non_authorized_user_is_blocked` probaba un usuario *sin* Operaciones,
  que falla en **otra** capa (lectura/escritura del asistente), no en la ACL de
  `unlink` del modelo real.
- Conclusión: «permisos verificados» se afirmó **sin** probar `ir.model.access`
  con el usuario operativo y `su=False`. Esta entrega cierra exactamente esa brecha.

## 4. Corrección mínima (diff)

Doctrina leída (`madenat_lumber_docs`): AD-80 / `13_CONSOLIDACION_OPERATIVA.md` §10
reserva la operación destructiva del ciclo de vida (Modo C, purga) a **Jefatura de
Operaciones**; el modo A («eliminación definitiva») es igual de destructivo. El rol
funcional correcto es, por tanto, **`group_madenat_jefatura_operaciones`** (más
estrecho que el grupo transversal `stock.group_stock_manager`, y ya lo posee el
usuario real). No se concede `unlink` a `base.group_user` ni a Operaciones.

**Diff de seguridad (separado): `patch/01_acl_security.diff`** — una sola línea:

```diff
-access_madenat_guia_processing_manager,...,group_madenat_jefatura_operaciones,1,1,1,0
+access_madenat_guia_processing_manager,...,group_madenat_jefatura_operaciones,1,1,1,1
```

**Diff auxiliar (UX, no seguridad): `patch/02_wizard_precheck.diff`** — añade el
pre-chequeo `_delete_access_blocker()` y lo integra en `_lifecycle_blockers`
(modos A y C) para que el asistente informe la falta de permiso **antes** de
ofrecer una ejecución que fallará. **No sustituye** la seguridad del servidor.

Archivos y hashes:

| Archivo | sha256 (activo → corregido) |
|---|---|
| `madenat_lumber_core/security/ir.model.access.csv` | `b946c6a5…` → `bc0c8b55…` |
| `madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` | `b632d79d…` → `174282a2…` |
| `madenat_lumber_intake/tests/test_guia_delete_acl.py` (nuevo) | — (`c983b71b…`) |

## 5. Alcance de seguridad

- **Quién puede borrar:** cualquier usuario del grupo **Jefatura de Operaciones**
  (ACL) **y** `stock.group_stock_manager` (guarda del core) **y** solo guías en
  `draft`/`cancelled`. En este entorno: user 2 (admin) y **user 8 (Cristhian)**, sin
  cambiar los grupos de ningún usuario.
- **Llamadas directas al modelo:** sí, un usuario autorizado puede llamar
  `unlink()` por RPC fuera del asistente (documentado y verificado en `ACL-07`).
  Esto es **intencional** (el core ya exige `stock_manager`); el asistente sigue
  siendo la vía recomendada.
- **Validaciones de negocio en todas las rutas:** se conservan intactas — el
  override del core mantiene `state`+`stock_manager`; el asistente mantiene sus
  precondiciones, revalidación y auditoría firmada.
- **NO se hace:** `sudo` en el asistente; `unlink` en la Consola SQL; `SQL DELETE`;
  relajar guardas del core; conceder `unlink` a todos los usuarios internos.

## 6. Pruebas en aislamiento (con identidad de usuario, `su=False`)

Entorno: base clon `aclf_test_20261007`, addons del workcopy `:ro`, contenedor
one-shot (`--no-http --max-cron-threads=0 --test-enable`). **`madenat_test`, el
árbol activo y producción: intactos.**

**Positivo (con la corrección) — `logs/iso_run.log`:**
`0 failed, 0 error(s) of 27 tests` (20 `TestGuideLifecycle` sin regresión + 7
`TestGuiaDeleteAcl` nuevos). La eliminación la ejecuta el usuario **no-superusuario**
autorizado (log: `User #2915 deleted madenat.guia.processing records with IDs: [33285]`).

**Negativo (sin la corrección, misma prueba) — `logs/iso_run_unpatched.log`:**
`2 failed, 1 error(s) of 7 tests`, con el mensaje **exacto del incidente**:

```
odoo.exceptions.AccessError: No puede eliminar registros 'Recepción de Guías Procesadas'
(madenat.guia.processing). Ningún grupo permite esta operación por el momento.
```

| Caso (identidad) | Positivo | Negativo |
|---|---|---|
| `test_01` Jefatura tiene `unlink`; otros no | ✔ | ✘ (reproduce la causa) |
| `test_02` autorizado + guía cancelada elegible → asistente→`action_run`→`unlink`: **éxito** | ✔ | ✘ (AccessError) |
| `test_03` llamada directa sin ACL → **rechazo** (guía sobrevive, sin auditoría de éxito) | ✔ | ✔ |
| `test_04` asistente informa falta de permiso **antes** de ejecutar | ✔ | ✔ |
| `test_05` guarda del core `stock_manager` preservada (UserError «Inventario/Administrador») | ✔ | ✔ |
| `test_06` protección de estado del core preservada (`SEGURIDAD MADENAT`) | ✔ | ✔ |
| `test_07` alcance: llamada directa de autorizado funciona | ✔ | ✘ (AccessError) |

Identidades: `user_authorized` = Operaciones+Jefatura+`stock_manager`;
`user_no_acl` = Operaciones+`stock_manager` (reproduce el rechazo del usuario real);
`user_no_stock` = Operaciones.

## 7. Sin efectos parciales tras el fallo (verificado en `madenat_test`)

| Comprobación | Resultado |
|---|---|
| Guía 33152 existe | ✔ (`count=1`), sigue `cancelled` |
| Cadena material 436→7813→7814 | intacta (Fase C; no re-auditada) |
| Auditoría coherente | solo `creation` (21738) y `deviation`/Fase C (21739) |
| Evento de éxito indebido `guia_delete_permanent` | **0 filas** → el `_lifecycle_log` previo al `unlink()` se **revirtió** con la transacción |

> Confirma **rollback correcto**: el fallo de acceso no dejó auditoría falsa de éxito.

## 8. Plan de aplicación y reversión (no ejecutado)

**Aplicación propuesta** (tras aprobación):
1. Aplicar `patch/01_acl_security.diff` y `patch/02_wizard_precheck.diff` a
   `custom_addons/` y `-u madenat_lumber_core,madenat_lumber_intake` en ventana
   operativa (idealmente con `odoo18_app` detenido o `--max-cron-threads=0`).
2. Repetir la verificación de pantalla de Fase D con el usuario **8** (0 bloqueadores).
3. Solo entonces, solicitar la Fase E (eliminación real) con su propia autorización.

**Reversión:**
- Código: `patch -R` de ambos diffs (orden inverso).
- Esquema/ACL: reejecutar `-u`; la ACL es un dato (`ir_model_access`) que el `-u`
  devuelve al valor del CSV. Retorno exacto: restaurar `dump + filestore`
  (`backups/FASE_B_20261007_153214/`, permisos 700).
- Riesgo: bajo (una línea de ACL + un pre-chequeo de lectura); no toca stock,
  valoración, contabilidad ni datos históricos.

## 9. Solicitud de aprobación (específica)

> **¿Autorizas aplicar la corrección mínima de ACL** — conceder `perm_unlink` sobre
> `madenat.guia.processing` **únicamente** al grupo `Jefatura de Operaciones`, más el
> pre-chequeo de UX del asistente — **sobre el entorno activo** (`custom_addons` +
> `-u` en `madenat_test`), **sin** cambiar los grupos de ningún usuario, **sin**
> `sudo`, **sin** tocar la Consola ni las guardas del core, y **sin** eliminar la
> guía 33152 (la Fase E se autoriza aparte)?

Alternativa a decidir por política: si se prefiere que también Operaciones-manager
pueda borrar, la ACL se concedería a `stock.group_stock_manager` en lugar de
Jefatura (más amplio: incluiría a los Auditores que hoy tienen ese grupo).
Recomendación: **Jefatura de Operaciones** (más estrecho y coherente con AD-80).

---

## 10. APLICACIÓN EN EL ENTORNO ACTIVO (ejecutada tras aprobación)

Aprobación recibida: *«conceder unlink SOLO a Jefatura de Operaciones + pre-chequeo del
asistente»*. Aplicado a `custom_addons` y a la base **`madenat_test`**.

**Método:** parada controlada de `odoo18_app` → `-u madenat_lumber_core,
madenat_lumber_intake` en contenedor one-shot (`--no-http --max-cron-threads=0
--stop-after-init`, `logs/apply_update.log`) → reinicio de `odoo18_app`.

**Verificación post-aplicación:**

| Comprobación | Resultado |
|---|---|
| ACL runtime `madenat.guia.processing` | **Jefatura de Operaciones: `unlink = t`**; Operaciones y Usuario interno siguen `f` |
| Errores en la actualización | `0` (`ERROR`/`CRITICAL`/`Traceback`, case-sensitive) |
| Servicio `odoo18_app` | **Up**; `GET /web/login` → **HTTP 200** |
| Guía 33152 | **intacta** (`cancelled`); **NO** eliminada |
| Evento indebido `guia_delete_permanent` | **0** filas |
| Árbol activo | ACL `,1,1,1,1`; `_delete_access_blocker` presente; test nuevo registrado |

**Pendiente (autorización aparte):** la **Fase E** (eliminación real de la guía 33152
con el usuario 8) no se ejecutó. La corrección ya está operativa para que, una vez
confirmada la pantalla de Fase D, sea posible.

**Reversión (si se requiriera):** `git`/editor de vuelta a `,1,1,1,0` y retirar
`_delete_access_blocker`, luego `-u` de ambos módulos; o restaurar
`backups/FASE_B_20261007_153214/` (dump + filestore).
