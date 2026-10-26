# MADENAT — Resultado Micro-Parche de Seguridad Recepción / Guías

```
Documento   : RESULTADO_SEC_RECEPCION_20261004
Feature     : Cierre de puerta lateral RPC/ORM en Recepción/Guías (Ingreso de Madera)
Fase        : C.1 — Precheck + auditoría de ruta (SOLO LECTURA). Implementación NO ejecutada.
Entorno     : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha       : 2026-10-04
Método      : READ-ONLY (git, docker, `odoo shell` SELECT/browse, grep). Sin edición de archivos,
              sin -u/update, sin tests, sin SQL de escritura, sin UAT, sin roles, sin commit/push.
Dictamen    : B. BLOQUEADO — DETALLAR ACL, MODELO O RUTA FALTANTE.
```

> **Resultado en una línea:** el micro-parche **NO se implementó** porque se activaron **dos
> criterios de detención** del propio mandato: **(1)** el módulo nombrado en “Archivos autorizados”
> —`madenat_guia_processing`— **no existe**; el modelo `madenat.guia.processing` y **todas** las ACL
> afectadas viven en **`madenat_lumber_core`** (módulo **no listado** entre los autorizados ni entre
> los prohibidos), igual que la ACL de `lumber.reception` (que **no** está en
> `madenat_lumber_reception_improvements`, cuyo único ACL es `res.partner`); y **(2)** la puerta
> lateral **no es una sola ACL del encabezado** sino **≥8 rutas de escritura** con `create`/`write`
> para `base.group_user` (encabezado, líneas, source-lot-lines, mass-update, recepción, líneas de
> recepción y 3 wizards). El mandato ordena **“si hay más de una ruta de escritura no auditada,
> detenerse y reportar antes de implementar”** y define el dictamen **B — MODELO O RUTA FALTANTE**.
> Se entrega la auditoría completa + el parche listo para aplicar (ACL + guard + tests).

---

## 1. Precheck e integridad (read-only)

| Ítem | Valor |
|---|---|
| Repo | `custom_addons` |
| Rama / HEAD | `feat/guia-correccion-documental-preservada-20261002` / `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree | 47 entradas (33 M + 14 ??) — sin cambios introducidos por esta fase |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · **HTTP 200** · `madenat_test` |
| **UAT Intake INT-1/2/3** | guía **32689** `UAT-INT-20261004-RECEPTION` `validated`; lote **16694**; quant interno **4.0 m³**; backlog doc **13420** — **intacta** |
| **UAT INT-4** | sin residuo: 0 guías `UAT-INT-20261004-PERM` (revertida) |
| **Congelados** | `distributed=0` · `is_c2=True=0` · `lumber.shipment.cost.line=0` · `account.payment=0` |
| Base (defensa) | guías 10 · recepciones 7 · pickings 31 · quants 170 |

Evidencia: `00_precheck_git.txt`, `01_acl_runtime.txt`, `02_integridad.txt` (crudos read-only).

## 2. Ruta de bypass identificada

### 2.1 Hechos
- **NO existen record rules** (`ir.rule` = **0** sobre los modelos afectados) → el **único** control
  es la **ACL** (`ir.model.access`). Confirmado en runtime.
- La UAT-INT-4 probó que **uid 6** (sin Operaciones, pero *stock user/manager*) pudo
  **crear y validar** una guía vía ORM/RPC (`action_validate` cambió `state` y creó lote/picking/
  move/quant), pese al bloqueo de la Consola/Wizard.

### 2.2 ACL efectiva en runtime (tabla `ir.model.access`)
| Modelo | ACL (xmlid) | Grupo | r/w/c/u | Puerta lateral |
|---|---|---|---|---|
| `madenat.guia.processing` | `...guia_processing.user` (3678) | **base.group_user** | 1/**1**/**1**/0 | **SÍ** |
| `madenat.guia.processing` | `...guia_processing.manager` (3679) | Jefatura de Operaciones | 1/1/1/1 | — (autorizado) |
| `madenat.guia.processing.line` | `access_madenat_guia_processing_line` (3685) | **base.group_user** | 1/**1**/**1**/**1** | **SÍ** |
| `madenat.guia.processing.source.lot.line` | `...source_lot_line` (3738) | **base.group_user** | 1/**1**/**1**/**1** | **SÍ** |
| `madenat.guia.mass.update` | `access_madenat_guia_mass_update` (3686) | **base.group_user** | 1/**1**/**1**/**1** | **SÍ** |
| `lumber.reception` | `access_lumber_reception_user` (3670) | **base.group_user** | 1/**1**/**1**/0 | **SÍ** |
| `lumber.reception` | `...reception.manager` (3671) | Jefatura de Operaciones | 1/1/1/1 | — |
| `lumber.reception` | `access_lumber_reception_auditoria` (3775) | Auditoría | 1/0/0/0 | — (lectura) |
| `lumber.reception` | *(legacy 802)* | “MADENAT: Compras y Operaciones” | 1/1/1/1 | SÍ (usuarios 2,8) |
| `lumber.reception` | *(legacy 827)* | “MADENAT: Validación Contable (Auditoría)” | 1/1/1/0 | **SÍ** (usuarios 8,9,**6**,7) |
| `lumber.reception.line` | `...reception.line.user` (3682) | **base.group_user** | 1/**1**/**1**/**1** | **SÍ** |
| wizards (reopen / documental / historical) | 3853/3856/3854 | **base.group_user** | 1/1/1/0 | **SÍ** |
| `...historical.reverse.candidate` | 3855 | **base.group_user** | 1/1/1/1 | **SÍ** |

**Observaciones críticas:**
1. **No existe** una ACL dedicada para `group_madenat_operaciones` en el encabezado de guía:
   Operaciones depende hoy de la fila `base.group_user`. Bajar `base.group_user` a solo lectura
   **exige añadir** una fila para `group_madenat_operaciones`.
2. La ACL de `lumber.reception` tiene además **dos filas legacy** (grupos “MADENAT: Compras y
   Operaciones” y “MADENAT: Validación Contable (Auditoría)”), y **uid 6 pertenece a la legacy 827**
   → segunda vía de escritura sobre recepción.
3. Todas las filas `ir.model.access` relevantes se **declaran en `madenat_lumber_core/security/
   ir.model.access.csv`** (no en `madenat_lumber_reception_improvements/security/ir.model.access.csv`,
   que solo define `res.partner`).

## 3. Bloqueo de implementación — criterios de detención activados

El mandato establece: *“Si hay más de una ruta de escritura no auditada, detenerse y reportar antes de
implementar”* y el dictamen **B: “BLOQUEADO — DETALLAR ACL, MODELO O RUTA FALTANTE”**. Se activan:

1. **MÓDULO/ARCHIVOS AUTORIZADOS INEXISTENTES.** `madenat_guia_processing/` **no existe** como módulo.
   El modelo `madenat.guia.processing` y sus ACL viven en **`madenat_lumber_core`**.
2. **MISMATCH DE ARCHIVOS.** Los “Archivos autorizados” no coinciden con la realidad:

| Autorizado por el mandato | Realidad en el repo |
|---|---|
| `madenat_guia_processing/security/ir.model.access.csv` | ❌ no existe → **`madenat_lumber_core/security/ir.model.access.csv`** |
| `madenat_guia_processing/models/madenat_guia_processing.py` | ❌ no existe → **`madenat_lumber_core/models/madenat_guia_processing.py`** |
| `madenat_guia_processing/{models,tests}/__init__.py`, `__manifest__.py` | ❌ no existe → **`madenat_lumber_core/…`** |
| `madenat_guia_processing/tests/test_guia_processing_security.py` | ❌ no existe → a crear en **`madenat_lumber_core/tests/`** |
| `madenat_lumber_reception_improvements/security/ir.model.access.csv` | ⚠️ existe pero **solo define `res.partner`** (no la ACL de `lumber.reception`) |
| `madenat_lumber_reception_improvements/models/lumber_reception.py` | ⚠️ existe (hereda `lumber.reception`), pero la ACL de recepción está en **core** |

   → El material del parche (**ACL de `madenat.guia.processing` y de `lumber.reception`**) está en
   **`madenat_lumber_core`**, módulo **fuera** de la lista de “Archivos autorizados”. No se edita.

3. **MÚLTIPLES RUTAS DE ESCRITURA (≥8).** Además del encabezado de guía, hay escritura con
   `base.group_user` en: líneas de guía, `source.lot.line`, `madenat.guia.mass.update`,
   `lumber.reception` (incl. 2 filas legacy), `lumber.reception.line` y 3 wizards (§2.2). Cerrar la
   puerta exige tocar **varios modelos del core**, superando el set autorizado.

## 4. ACL corregida — PROPUESTA (NO aplicada)

> No se aplicó ninguna edición. Se documenta el cambio exacto para autorización del operador.

Archivo: **`madenat_lumber_core/security/ir.model.access.csv`**

```diff
 # Encabezado de guía: base.group_user pasa a SOLO LECTURA
-access_madenat_guia_processing_user,madenat.guia.processing.user,model_madenat_guia_processing,base.group_user,1,1,1,0
+access_madenat_guia_processing_user,madenat.guia.processing.user,model_madenat_guia_processing,base.group_user,1,0,0,0
+# NUEVA fila Operaciones (hoy Operaciones depende de base.group_user)
+access_madenat_guia_processing_operaciones,madenat.guia.processing.operaciones,model_madenat_guia_processing,madenat_lumber_core.group_madenat_operaciones,1,1,1,0
 # (Jefatura conserva create/write/unlink: access_madenat_guia_processing_manager)

 # Recepción: mismo criterio
-access_lumber_reception_user,lumber.reception.user,model_lumber_reception,base.group_user,1,1,1,0
+access_lumber_reception_user,lumber.reception.user,model_lumber_reception,base.group_user,1,0,0,0
+access_lumber_reception_operaciones,lumber.reception.operaciones,model_lumber_reception,madenat_lumber_core.group_madenat_operaciones,1,1,1,0

 # Rutas laterales relacionadas (evaluar caso a caso; NO todas necesitan revocarse,
 # pero DEBEN quedar como lectura para no-Operaciones):
-access_madenat_guia_processing_line,model_madenat_guia_processing_line,base.group_user,1,1,1,1  → 1,0,0,0 (+fila Operaciones 1,1,1,0)
-access_madenat_guia_processing_source_lot_line,... ,base.group_user,1,1,1,1                 → 1,0,0,0 (+fila Operaciones)
-access_madenat_guia_mass_update,...,base.group_user,1,1,1,1                                  → 1,0,0,0 (+fila Operaciones)
-access_lumber_reception_line_user,...,base.group_user,1,1,1,1                                → 1,0,0,0 (+fila Operaciones)
```

**Advertencias de impacto (a validar antes de aplicar):**
- **Legacy 802/827** de `lumber.reception`: deberán revocarse/limpiarse también (uid 6 pertenece a la 827).
- Bajar `base.group_user` sin añadir la fila **Operaciones** **rompería** el ingreso para Operaciones.
- La ACL `madenat.reception.mass.update` **no tiene fila** en runtime (no es puerta lateral).

## 5. Guard server-side — PROPUESTA (NO aplicado)

Archivo previsto: **`madenat_lumber_core/models/madenat_guia_processing.py`** (misma lógica en
`madenat_lumber_core/models/lumber_reception.py`).

```python
OPERATIONAL_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)

def _check_operational_group(self):
    """Cierra la puerta lateral RPC/ORM: solo Operaciones/Jefatura/Gerencia."""
    if self.env.su:
        return  # el superusuario del sistema no aplica (coherente con Odoo)
    if not any(self.env.user.has_group(g) for g in OPERATIONAL_GROUPS):
        raise AccessError(_(
            "La operación de recepción/guía requiere el rol de Operaciones, "
            "Jefatura de Operaciones o Gerencia."))
```

Puntos de aplicación (todos server-side, cubren UI/RPC/import/ORM): `create()`, `write()` **cuando
altera campos físicos/operativos** (no campos documentales CDP-V1), `action_verify_data()`,
`action_process_from_staging()`, `action_validate()`, `action_reopen_to_draft()`,
`action_force_cancel()` y cualquier acción que confirme/cambie estado físico. **Sin** `sudo()`,
**sin** bypass por contexto, **sin** SQL.

> **Ojo (riesgo de diseño):** el ejecutor CDP-V1 (`_cdp_apply_documental_correction`) y los wizards
> de intake/toll/logistics invocan `write()`/`action_validate()`; el guard debe permitir a
> Operaciones/Jefatura (roles autorizados reales) y **no** bloquear CDP-V1 documental de un usuario
> autorizado. Requiere pruebas de no-regresión de intake/toll/CDP antes de aplicar.


## 6. CDP-V1 y backlog documental — PRESERVADOS (sin tocar)

- **CDP-V1**: no se modificó ninguna ACL/acción del flujo documental preservado (archivo
  `madenat_lumber_core/models/madenat_guia_processing_documental.py` **no editado**). La UAT-INT-3
  sigue íntegra: guía 32689 `validated`, auditoría `deviation` (hash SHA-256) presente, adjunto v2
  versionado y versión anterior viva. El diseño del guard (§5) mantiene explícitamente la corrección
  documental para Operaciones/Jefatura.
- **Backlog documental**: `lumber.shipment.document` **no tocado**. Registro UAT 13420 sigue
  `missing`/`backlog_state=completed`, con criticidad/responsable/fecha; comportamiento no bloqueante
  intacto.
- **Documentación tardía no bloqueante**: sin cambios (no se alteró ningún gate de validación).

## 7. Update — NO ejecutado

No se ejecutó `-u madenat_guia_processing,madenat_lumber_reception_improvements` (ni ningún `-u`)
porque **no hubo archivos modificados** (implementación detenida). No se usó `-i`, ni update global,
ni SQL de escritura. El único módulo candidato real sería **`madenat_lumber_core`** (no listado).

## 8. Tests de seguridad — PLAN (NO ejecutados)

No se crearon ni ejecutaron tests. Plan propuesto (archivo
`madenat_lumber_core/tests/test_guia_processing_security.py`, `@tagged('post_install','-at_install')`):

| Test | Caso |
|---|---|
| **T-INT-SEC-1** | Operaciones **sí** crea y valida una guía fixture válida. |
| **T-INT-SEC-2** | Interno común (`base.group_user`) **no** puede `create()` `madenat.guia.processing`. |
| **T-INT-SEC-3** | Interno común **no** puede `write()` campos operativos. |
| **T-INT-SEC-4** | Interno común **no** puede `action_validate()` (ORM/RPC) → `AccessError`. |
| **T-INT-SEC-5** | Auditoría **no** puede modificar/procesar/validar (solo lectura). |
| **T-INT-SEC-6** | `with_context(allow_intake=True)` **no** elude el guard. |
| **T-INT-SEC-7** | Fallo de seguridad **no** crea guía/lote/picking/move/quant. |
| **T-INT-SEC-8** | CDP-V1 documental autorizado conserva stock y respeta roles. |
| **T-REC-SEC-1..N** | Equivalentes sobre `lumber.reception` (interno común sin create/write/validate). |

> Nota de diseño: si el guard se implementa en `madenat_lumber_core`, corresponde a ese módulo; si se
> prefiere aislarlo, el wrapper `_inherit` podría ubicarse en `madenat_lumber_reception_improvements`
> (autorizado), pero **la revocación de ACL debe hacerse en `madenat_lumber_core`** (no editable con
> el set autorizado actual).

## 9. Integridad de stock / UAT / finanzas / SV

| Verificación | Resultado |
|---|---|
| UAT Intake INT-1/2/3 | **intacta** (guía 32689 `validated`, lote 16694, quant 4.0, doc 13420) |
| UAT INT-4 | **sin residuo** (0 guías `…-PERM`) |
| Stock/lotes/pickings/moves/quants | base 10/7/31/170 — **sin cambio** en esta fase (no hubo escritura) |
| Costeo C2 | `distributed=0`, `is_c2=True=0` — **congelado** |
| Billing / Pagos | `lumber.shipment.cost.line=0`, `account.payment=0` — **congelado** |
| SV | `madenat.sv.operation` / `imputation` — sin cambio |
| Git | HEAD `34c81272…`; **sin** commit/push; working tree igual (47 entradas) |

## 10. Dictamen

> **B. `BLOQUEADO — DETALLAR ACL, MODELO O RUTA FALTANTE`.**
>
> **Faltante (modelo/ruta):** el módulo `madenat_guia_processing` **no existe**; el modelo
> `madenat.guia.processing` y **todas** las ACL afectadas residen en **`madenat_lumber_core`**
> (`security/ir.model.access.csv`), módulo **fuera** de los “Archivos autorizados”; la ACL de
> `lumber.reception` tampoco está en `madenat_lumber_reception_improvements` (ahí solo hay
> `res.partner`).
>
> **ACL/rutas faltantes:** la puerta lateral es **múltiple** (≥8 rutas con create/write para
> `base.group_user`: encabezado de guía, líneas, source-lot-lines, mass-update, `lumber.reception`
> —incl. 2 filas legacy, una con **uid 6**—, líneas de recepción y 3 wizards); **no** hay `ir.rule`.
> Conforme al stop-criterion del mandato, **no se implementó**.
>
> **Acción solicitada para desbloquear (autorizar y luego ejecutar):**
> 1. **Autorizar `madenat_lumber_core`** como módulo objetivo (o confirmar su alias como
>    `madenat_guia_processing`).
> 2. Aplicar el parche ACL (§4) + guard (§5) **en `madenat_lumber_core`**, con **fila nueva para
>    `group_madenat_operaciones`** (hoy no existe) y **limpieza de las filas legacy 802/827**.
> 3. Decidir alcance de las rutas laterales relacionadas (líneas, mass-update, wizards).
> 4. Crear/ejecutar `TestGuiaProcessingSecurity` (+ `TestReceptionSecurity`) y actualizar **solo**
>    `madenat_lumber_core`: `odoo -u madenat_lumber_core --stop-after-init --no-http`.
> 5. **Re-ejecutar UAT-INT-4** (no la UAT completa).

**Estado:** auditoría completa; **cero ediciones**, **cero updates**, **cero tests**, **cero commit**.
Detenido a la espera de decisión sobre el módulo objetivo y el alcance del parche.

