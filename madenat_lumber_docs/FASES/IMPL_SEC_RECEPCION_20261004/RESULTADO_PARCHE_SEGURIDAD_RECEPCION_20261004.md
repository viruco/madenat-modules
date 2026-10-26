# MADENAT — Resultado Parche Integral Seguridad Recepción / Guías

```
Documento   : RESULTADO_PARCHE_SEGURIDAD_RECEPCION_20261004
Feature     : Cierre de puerta lateral RPC/ORM en Recepción/Guías (Ingreso de Madera)
Fase        : C.1 — Implementación, Update y Tests (módulo objetivo: madenat_lumber_core)
Entorno     : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha       : 2026-10-04
Método      : ORM/ACL + guard server-side. Edición SOLO de madenat_lumber_core.
              Update -u madenat_lumber_core (sin -i, sin update global). Tests aislados.
              SIN SQL de escritura, SIN UAT, SIN Costeo/Billing/Pagos, SIN commit/push.
Evidencia   : ./IMPL_SEC_RECEPCION_20261004/ (00..07 + 04_update.log + 05_tests.log)
Dictamen    : A. SEGURIDAD INTAKE/RECEPCIÓN CORREGIDA — APTO PARA REEJECUTAR INT-4.
```

> **Resultado en una línea:** se cerró la puerta lateral con **ACL de mínimo privilegio**
> (`base.group_user` pasa a solo-lectura y se crean filas operativas dedicadas) **+ guard
> server-side canónico** (`_require_intake_operational_group`) aplicado a create/write-operativo y a
> todas las acciones de ingreso/validación/reapertura/cancelación y a los wizards. La suite
> `TestGuiaProcessingSecurity` (T-INT-SEC-1..8) y `TestReceptionSecurity` (T-REC-SEC-1..5) pasa
> **13/13**. `CDP-V1` y el **backlog documental no bloqueante** quedan preservados; **stock, UAT
> INT-1/2/3, C2/Billing/Pagos y SV intactos** (snapshot final idéntico al baseline).

---

## 1. Precheck e integridad

| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree (pre) | 47 entradas (33 M + 14 ??) |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · **HTTP 200** · `madenat_test` |
| Módulo objetivo | **`madenat_lumber_core`** (confirmado por auditoría; `madenat_guia_processing` no existe como módulo) |
| UAT Intake INT-1/2/3 | intacta — guía **32689** `validated`, lote **16694**, quant interno **4.0 m³**, backlog doc **13420** |
| UAT INT-4 | sin residuo (0 guías `UAT-INT-20261004-PERM`) |
| Congelados | `distributed=0` · `is_c2=True=0` · `lumber.shipment.cost.line=0` · `account.payment=0` |
| Roles | uid 2 (admin) · uid 6 (sin Operaciones; **stock manager**) · uid 8 (Operaciones+Jefatura; stock manager) — sin cambios |

Evidencia: `00_precheck_git.txt`, `01_acl_runtime.txt`, `03_baseline_before.txt`.

## 2. Superficie de rutas cerrada (inventario)

Lista cerrada de las **8 familias de rutas** detectadas (modelo · archivo real · ACL real · acciones
públicas · grupo actual → objetivo):

| # | Modelo técnico | Archivo Python | ACL (archivo/ID) | Acciones públicas / writables | Grupo actual → **objetivo** |
|---|---|---|---|---|---|
| 1 | `madenat.guia.processing` | `models/madenat_guia_processing.py` | `security/ir.model.access.csv`/`access_madenat_guia_processing_user` | `create`, `write`, `action_verify_data`, `action_process_from_staging`, `action_validate`, `action_reopen_to_draft`, `action_force_cancel`, `action_assign_commercial_defaults`, `action_create_purchase_order_from_document` | `base.group_user` (rwc) → **read-only** + Guard; **Operaciones** (rwc) |
| 2 | `madenat.guia.processing.line` | `models/madenat_guia_processing.py` | `.../access_madenat_guia_processing_line` | writable ORM (staging) | `base.group_user` (rwcu) → **read-only** + **Operaciones** (rwc) |
| 3 | `madenat.guia.processing.source.lot.line` | `models/madenat_guia_processing_source_lot_line.py` | `.../access_madenat_guia_processing_source_lot_line` | writable ORM | `base.group_user` (rwcu) → **read-only** + **Operaciones** |
| 4 | `madenat.guia.mass.update` | `wizard/madenat_guia_mass_update.py` | `.../access_madenat_guia_mass_update` | `action_apply` | `base.group_user` (rwcu) → **read-only** + **Operaciones** + Guard |
| 5 | `lumber.reception` | `models/lumber_reception.py` | `.../access_lumber_reception_user` | `create`, `write`, `action_verify_data`, `action_process_documents`, `action_confirm_reception`, `action_reset_to_draft`, `action_cancel` | `base.group_user` (rwc) → **read-only** + Guard; **Operaciones** (rwc) |
| 6 | `lumber.reception.line` | `models/lumber_reception.py` | `.../access_lumber_reception_line_user` | writable ORM | `base.group_user` (rwcu) → **read-only** + **Operaciones** |
| 7 | Wizards guía: `reopen` / `historical.reverse(.wizard/.candidate)` / `documental.correction` | `wizard/madenat_guia_processing_{reopen,historical_reverse,documental_correction}_wizard.py` | 4 ACL rows | `action_confirm` | `base.group_user` (rwc) → **read-only** + **Operaciones** + Guard |
| 8 | Wizard recepción: `reset` + `mass.update` | `wizard/lumber_reception_{reset,mass_update}_wizard.py` | 2 ACL rows | `action_confirm` / `action_apply` | `stock.group_stock_manager`/`base.group_user` → **Operaciones** + Guard |

Adicional auditado y **sin acción** (no es puerta lateral física): `madenat.reception.mass.update`
(sin fila ACL), `madenat.subproducto`, `madenat.audit.log`, `stock.lot` (fuera de alcance). **No
aparecieron** modelos operativos adicionales no auditados.

## 3. ACL antes / después

Archivo único modificado: **`madenat_lumber_core/security/ir.model.access.csv`** (41 líneas ±).

| Modelo | Grupo | Antes r/w/c/u | Después r/w/c/u |
|---|---|---|---|
| `madenat.guia.processing` | `base.group_user` | 1/**1**/**1**/0 | **1/0/0/0** |
| `madenat.guia.processing` | `group_madenat_operaciones` | *(no existía)* | **1/1/1/0** |
| `madenat.guia.processing` | `group_madenat_jefatura_operaciones` | 1/1/1/**1** | 1/1/1/**0** |
| `madenat.guia.processing.line` | `base.group_user` | 1/1/1/1 | **1/0/0/0** |
| `madenat.guia.processing.line` | `group_madenat_operaciones` | *(no existía)* | **1/1/1/0** |
| `madenat.guia.processing.source.lot.line` | `base.group_user` | 1/1/1/1 | **1/0/0/0** |
| `madenat.guia.mass.update` | `base.group_user` | 1/1/1/1 | **1/0/0/0** |
| `lumber.reception` | `base.group_user` | 1/**1**/**1**/0 | **1/0/0/0** |
| `lumber.reception` | `group_madenat_operaciones` | *(no existía)* | **1/1/1/0** |
| `lumber.reception` | `group_madenat_jefatura_operaciones` | 1/1/1/**1** | 1/1/1/**0** |
| `lumber.reception.line` | `base.group_user` | 1/1/1/1 | **1/0/0/0** |
| `lumber.reception.mass.update` | `base.group_user` | 1/1/1/1 | **1/0/0/0** |
| `lumber.reception.reset.wizard` | `stock.group_stock_manager` | 1/1/1/0 | → **group_madenat_operaciones** 1/1/1/0 |
| wizards guía (reopen/documental/historical/candidate) | `base.group_user` | 1/1/1/x | **1/0/0/0** |

Se añadieron **filas nuevas para `group_madenat_operaciones`** en las 8 familias (y `group_madenat_
gerencia` queda cubierta por *implicación*: `group_madenat_gerencia` → `group_madenat_operaciones`).
**Ningún** `base.group_user` conserva create/write en modelos operativos (verificado con `awk`).

Evidencia: `01_acl_runtime.txt` (antes) y `01b_acl_runtime_after.txt` (después, runtime).

## 4. ACL legacy restringidas / neutralizadas

| ACL | Grupo | Modelo | r/w/c/u | Acción |
|---|---|---|---|---|
| **802** (huérfana, sin `ir.model.data`) | “MADENAT: Compras y Operaciones” (id 61; usuarios 2,8) | `lumber.reception` | 1/**1**/**1**/**1** | **Neutralizada por el guard** |
| **827** (huérfana, sin `ir.model.data`) | “MADENAT: Validación Contable (Auditoría)” (id 62; usuarios 8,9,**6**,7) | `lumber.reception` | 1/**1**/**1**/0 | **Neutralizada por el guard** |

Ambas son **filas ACL huérfanas** (sin XML ID) → **no gestionables desde el CSV**; y no se tocaron
roles/grupos (prohibido). La restricción efectiva se logra con el **guard server-side** (que no
depende de ACL): un usuario de estos grupos NO es “operativo”, por lo que no puede crear ni escribir
campos operativos de recepción aunque la ACL se lo permita. Verificado por **T-REC-SEC-5**. *Limpieza
DB de las filas 802/827: opcional, requiere migración/manual fuera del set autorizado.*

## 5. Guard server-side (implementado)

**Helper canónico compartido** en `models/mixin_lumber_ingest.py` (el mixin `madenat.lumber.ingest.
mixin` es heredado por `madenat.guia.processing` **y** `lumber.reception` → máxima reutilización):

```python
INTAKE_OPERATIONAL_GROUPS = (
    'madenat_lumber_core.group_madenat_operaciones',
    'madenat_lumber_core.group_madenat_jefatura_operaciones',
    'madenat_lumber_core.group_madenat_gerencia',
)
def is_intake_operational_user(env):        # env.su => True (motor interno)
    return env.su or any(env.user.has_group(g) for g in INTAKE_OPERATIONAL_GROUPS)
def assert_intake_operational_user(env):    # AccessError con mensaje canónico
    if not is_intake_operational_user(env):
        raise AccessError(_('La operación de ingreso/recepción requiere el rol de '
                            'Operaciones, Jefatura de Operaciones o Gerencia.'))
# métodos del mixin: _require_intake_operational_group(), _intake_has_operational_change(vals),
#                    _check_intake_operational_write(vals)
```

**Puntos de aplicación** (`self._require_intake_operational_group()` / `_check_intake_operational_write(vals)`):

- `madenat.guia.processing`: `create()`, `write()` (si toca campo operativo), `action_verify_data`,
  `action_process_from_staging`, `action_validate`, `action_reopen_to_draft`, `action_force_cancel`,
  `action_assign_commercial_defaults`, `action_create_purchase_order_from_document`.
- `lumber.reception`: `create()`, `write()` (operativo), `action_verify_data`, `action_process_documents`,
  `action_confirm_reception`, `action_reset_to_draft`, `action_cancel`.
- Wizards: `madenat.guia.mass.update.action_apply`, `lumber.reception.mass.update.action_apply`,
  `reopen.wizard.action_confirm`, `historical.reverse.wizard.action_confirm`,
  `lumber.reception.reset.wizard.action_confirm`, `documental.correction.wizard.action_confirm` (CDP-V1).

`write()` **distingue** la edición estrictamente documental (lista blanca CDP-V1 / adjuntos) de la
modificación operativa (`INTAKE_OPERATIONAL_FIELDS`: estado, lotes, líneas, proveedor, orden, tipo,
perfil, ubicación, picking, consumo, tarifas, volumen, adjuntos de guía). **No** se usa `sudo()`, ni
contexto como bypass, ni SQL. El **superusuario** (`env.su`) sigue operando (motor interno aprobado).


## 6. CDP-V1 y backlog documental — PRESERVADOS

- **CDP-V1** (corrección documental preservada) **intacto**: `models/madenat_guia_processing_documental.py`
  no fue editado. El wizard CDP-V1 sigue disponible para roles operativos (fila nueva Operaciones) y
  su `action_confirm` incorpora el guard (Operaciones/Jefatura/Gerencia), sin bloquear la corrección
  documental autorizada. **T-INT-SEC-8** demuestra que CDP-V1 por Operaciones **conserva** stock/lotes/
  pickings/moves/quants y mantiene la guía en `validated`.
- **Backlog documental** (`lumber.shipment.document`) **no tocado** (registro UAT 13420 intacto:
  missing · backlog_state=completed · criticidad/responsable/fecha). Reglas de no bloqueo documental
  sin cambios.
- La **documentación tardía sigue siendo no bloqueante**: el guard solo restringe *quién* opera, no
  convierte documentos pendientes en bloqueo de recepción/stock.

## 7. Update

```
docker exec odoo18_app odoo --config /etc/odoo/odoo.conf --database madenat_test \
  -u madenat_lumber_core --stop-after-init --no-http
```
Resultado: **módulo cargado en 4.22s**, registry recargado, **0 ERROR / 0 CRITICAL**, sin `-i`, sin
update global, sin SQL de escritura. Log: `04_update.log`. Los avisos presentes son **pre-existentes**
(etiquetas duplicadas de campos en `*_reports`, modelos SV internos sin ACL) y no derivan de este parche.

## 8. Tests de seguridad (T-INT-SEC / T-REC-SEC)

Ejecutados **exclusivamente** `TestGuiaProcessingSecurity` y `TestReceptionSecurity`
(`-u madenat_lumber_core --test-enable --test-tags /madenat_lumber_core:<clase> --stop-after-init`):

> **`0 failed, 0 error(s) of 13 tests`** — log `05_tests.log`.

| Test | Cobertura | Resultado |
|---|---|---|
| T-INT-SEC-1 | Operaciones **crea y valida** una guía fixture válida | ✔ `validated` + lote |
| T-INT-SEC-2 | Interno común **no** puede `create()` la guía | ✔ AccessError |
| T-INT-SEC-3 | Interno común **no** puede `write()` campo operativo | ✔ AccessError |
| T-INT-SEC-4 | Interno común **no** puede `action_validate()` (ORM/RPC) | ✔ AccessError |
| T-INT-SEC-5 | **Auditoría** no modifica/procesa/valida | ✔ AccessError (×3) |
| T-INT-SEC-6 | `with_context(allow_intake=True, …)` **no** elude | ✔ AccessError |
| T-INT-SEC-7 | El fallo **no** crea guía/lote/picking/move/quant | ✔ Δ0 |
| T-INT-SEC-8 | CDP-V1 autorizado **conserva stock** y respeta rol | ✔ |
| T-REC-SEC-1 | Operaciones **crea** recepción | ✔ |
| T-REC-SEC-2 | Interno común **no** crea/escribe/confirma recepción | ✔ AccessError (×3) |
| T-REC-SEC-3 | Wizard de reapertura **no** elude el grupo | ✔ AccessError |
| T-REC-SEC-4 | El fallo **no** crea recepción/lote/picking/move/quant | ✔ Δ0 |
| T-REC-SEC-5 | **ACL legacy huérfana (827) no elude** el guard | ✔ AccessError |

> Nota de fixture: el usuario “Operaciones” de prueba incluye `stock.group_stock_manager` porque
> `action_validate` ejecuta `stock.move.unlink()`, que en stock core exige ese grupo (el operador real
> uid 8 ya lo posee). No es un permiso concedido por este parche.

## 9. Integridad stock / UAT / finanzas / SV

| Verificación | Antes | Después | Resultado |
|---|---|---|---|
| Snapshot global (move/move.line/picking/quant/lot/guía/recepción/…) | `03_baseline_before.txt` | `07_final.txt` | **idéntico** (Δ0) |
| UAT Intake INT-1/2/3 | guía 32689 `validated`, lote 16694, quant 4.0, doc 13420 | igual | ✔ intacta |
| UAT INT-4 | sin residuo | sin residuo | ✔ |
| Costeo C2 / Billing / Pagos | `distributed=0`, `is_c2=0`, cost lines 0, `account.payment=0` | igual | ✔ congelado |
| SV | `madenat.sv.operation`/`imputation` sin cambio | igual | ✔ |
| Git | 47 entradas | + nuevo parche en `madenat_lumber_core` | sin commit/push |

## 10. Dictamen

> **A. `SEGURIDAD INTAKE/RECEPCIÓN CORREGIDA — APTO PARA REEJECUTAR INT-4`.**
>
> La puerta lateral RPC/ORM quedó cerrada en las **8 familias de rutas**: `base.group_user` es
> solo-lectura en los modelos operativos, los roles **Operaciones/Jefatura/Gerencia** conservan la
> operación (filas ACL dedicadas), y el **guard server-side** bloquea create/write-operativo y todas
> las acciones de proceso/validación/reapertura/cancelación y wizards — cubriendo UI, RPC, importación
> y ORM, incluido el contexto forzado y las rutas legacy. **CDP-V1 y el backlog documental quedan
> preservados**; stock, UAT y finanzas intactos. Suite **13/13** en verde.
>
> **Residual documentado:** las filas ACL **huérfanas 802/827** (sin XML ID) permanecen en BD pero
> **neutralizadas por el guard** (probado T-REC-SEC-5); su limpieza a nivel DB requeriría una migración
> fuera del set de archivos autorizado (no ejecutada).
>
> **Siguiente paso autorizado:** **re-ejecutar UAT-INT-4** (no la UAT completa).

**Estado:** implementación + update + tests completados; **sin** UAT, **sin** Costeo/Billing/Pagos,
**sin** cambio de roles/grupos, **sin** commit/push.

