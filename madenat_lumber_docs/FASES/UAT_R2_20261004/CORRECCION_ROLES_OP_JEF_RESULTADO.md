# MADENAT — Resultado Corrección de Roles: Cristhian Operaciones + Jefatura

- **Sub-bloque:** 4B — R2 UAT. **Gate previo a reintentar UAT R2** (no se reintenta aquí).
- **Decisión de negocio aplicada:** **Opción 2** de la Auditoría de Roles
  (`AUDITORIA_ROLES_FASE0.md`): mantener Operaciones/Jefatura, retirar Gerencia y
  sus herencias financieras.
- **Método:** `odoo shell` con **`env(user=2, su=False)`** (Administrator puntual);
  **sin uid 1**, **sin `sudo()`**, **sin SQL de escritura**, **sin editar XML /
  `implied_ids` / `res ACL` / reglas / código**. La única escritura fue la relación
  M2M de grupos de **uid 8** (`res_groups_users_rel`), con `commit` explícito.
- **Helpers de evidencia:** `_precheck_roles.py`, `_apply_roles.py`,
  `_validate_roles.py`, `_integridad_post.py`.
- **Fecha:** 2026-10-04.

---

## 1. Precheck e integridad

| Ítem | Valor | Archivo |
|---|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272bb07d48db98d73a7734c81a2a8e384fa` | `10_...`, `13_...` |
| Working tree | **33 = 24 ` M` + 9 `??`** (idéntico antes y después) | `10_...` |
| `git diff --check` | **CLEAN** | `10_...` |
| Runtime / DB | `odoo18_app` Up (4h) · `odoo18_db` healthy · `madenat_test` | `10_...` |
| UAT R2 | **no creada** (0 contenedores/embarques `UAT-R2-20261004-*`) | `10_...`, `13_...` |
| `rebaja_return_total` / `rebaja_reverse` | **0 / 0** | `10_...`, `13_...` |
| B-01 states | **13 none / 1 open / 1 resolved** (sin cambios) | `10_...`, `13_...` |
| Protegidos | Histórica, UAT Rolleo, Borrador, B-01, R1 → **intactos** (verificado id/estado en `13_...`) | `13_...` |
| Delta stock/finanzas/SV/UAT | **0** | `13_...` |

**Grupos efectivos ANTES (uid 8, 46 grupos)** — relevantes:
`group_madenat_operaciones`(256), `group_madenat_costos`(257),
`group_madenat_contabilidad`(258), `group_madenat_gerencia`(259),
`group_madenat_cost_auditor_plus`(260),
`group_madenat_jefatura_operaciones`(261), `group_madenat_cost_auditor`(69),
`account.group_account_manager`(26), `account.group_account_invoice`(23),
huérfanos `#61/#62/#63/#64`; **sin** `group_madenat_admin`, **sin** `base.group_system`.

### Clasificación directa vs. implicada (evidencia `CLS`/`IMPL`/`HIER`)
| Grupo | miembro | implicado por (evidencia) |
|---|---:|---|
| `group_madenat_operaciones` | Sí | Gerencia, **Jefatura** |
| `group_madenat_jefatura_operaciones` | Sí | — (raíz / directo) |
| `group_madenat_gerencia` | Sí | — (raíz / directo) |
| `group_madenat_contabilidad` | Sí | **exclusivamente Gerencia** (`IMPL:= [Gerencia]`) |
| `group_madenat_costos` | Sí | Contabilidad, Gerencia (pre-existente, ver §5) |
| `group_madenat_admin` | No | — (prohibido: ausente) |
| `account.group_account_manager` | Sí | Contabilidad, Gerencia (ambas a retirar) |
| `account.group_account_invoice` | Sí | account_manager, Contabilidad, Gerencia |
| `base.group_system` | No | — (prohibido: ausente) |

**Criterio de detención previo:** **NO se cumple ninguna condición de parada.**
`group_madenat_contabilidad` se implica **sólo** por Gerencia; `account_manager`
sólo por Contabilidad/Gerencia; `account_invoice` sólo por esa cadena
(`account.group_account_basic/user` **no** están en uid 8). Nada re-implica
Gerencia/Contabilidad (los huérfanos `#61/62/63/64` tienen `implied_ids = []`).
No se requirió editar XML/`implied_ids`/ACL/código.

---

## 2. Matriz de membresías antes/después de Cristhian (uid 8)

| Grupo (xmlid) | gid | Antes | Después | Acción |
|---|---:|---:|---:|---|
| `group_madenat_operaciones` | 256 | Sí | **Sí** | Mantener |
| `group_madenat_jefatura_operaciones` | 261 | Sí | **Sí** | Mantener |
| `group_madenat_gerencia` | 259 | Sí | **No** | **Removido** |
| `group_madenat_contabilidad` | 258 | Sí (impl. Gerencia) | **No** | **Removido** |
| `account.group_account_manager` | 26 | Sí (impl. Gerencia) | **No** | **Removido** |
| `account.group_account_invoice` | 23 | Sí (impl. Gerencia) | **No** | **Removido** |
| `group_madenat_costos` | 257 | Sí | **Sí** | **NO modificar** (§5) |
| `group_madenat_cost_auditor` | 69 | Sí | Sí | Sin cambios (fuera de alcance) |
| `group_madenat_cost_auditor_plus` | 260 | Sí | Sí | Sin cambios (fuera de alcance) |
| `group_madenat_admin` | — | No | No | Prohibido: ausente |
| `base.group_system` | 4 | No | No | Prohibido: ausente |

- **Total grupos uid 8: 46 → 42** (−4: gerencia, contabilidad, account_manager,
  account_invoice). Evidencia: `11_roles_cristhian_before_after.txt`
  (`COMMITTED| gerencia=False contabilidad=False account_manager=False
  account_invoice=False` · `operaciones=True jefatura=True costos=True
  system=False admin=False`).
- `PRECHECK_NO_READD` confirmó que ninguna membresía conservada re-implica los
  4 grupos retirados.

---

## 3. Gerencia removida / causa de bloqueo

**Resultado: REMOVIDA** de uid 8 (`group_madenat_gerencia`, gid 259).
- `group_madenat_gerencia` era **raíz/directa** (`CLS ... implied_by=[—]`).
- Tras el ajuste: `USERS| group_madenat_gerencia [2:mauricio.seo@gmail.com]` →
  sólo Administrator (uid 2). **Sin causa de bloqueo.**

## 4. Grupos financieros heredados — evidencia y resultado

| Grupo | Ruta exclusiva | ¿Asignación independiente? | Resultado |
|---|---|---|---|
| `group_madenat_contabilidad` | `Gerencia → Contabilidad` (`IMPL:= [Gerencia]`) | **No** (ningún otro grupo lo implica) | **Removido** |
| `account.group_account_manager` | `Contabilidad/Gerencia → account_manager` | **No** | **Removido** |
| `account.group_account_invoice` | `account_manager/Contabilidad/Gerencia → account_invoice` | **No** (`account_basic/user` ausentes) | **Removido** |

Evidencia dura:
- `IMPL| group_madenat_contabilidad <= [Gerencia]` (única fuente).
- `HIER| group_madenat_contabilidad implied_direct=[Costos, account.group_account_manager]`
  — es decir, account_manager se logra **vía** Contabilidad, que se logra **vía** Gerencia.
- Precheck `USERS` mostraba uid 8 en `account_manager`/`account_invoice`; postquirk
  (`13_...`) ya **no** aparece en esas listas (queda `[2, 6, 7, 9]`).

## 5. Grupo Costos — origen, ACL y estado (SIN modificación)

- **gid 257**, `madenat_lumber_core.group_madenat_costos`.
- **Origen / directo-transitivo:** hoy está implicado por Contabilidad/Gerencia en
  el grafo (`IMPL| costos <= [Contabilidad, Gerencia]`), **pero es una pertenencia
  pre-existente e independiente** de uid 8 (documentada en
  `FASE_A_HABILITACION_JEFATURA.md` §2: *"uid 8 (Operaciones) tiene además
  group_madenat_costos"* **antes** de agregar Jefatura/Gerencia). Por mandato
  explícito **NO se removió**.
- **ACL que otorga** (core `ir.model.access.csv` línea 13):
  `access_stock_lot_cost_line_costos` → modelo **`stock.lot.cost.line`** con
  **`1,1,1,1`** (read/write/create/unlink) + `base.group_user` (implied).
- **Usuarios que lo poseen:** `[2:mauricio.seo@gmail.com, 8:cristhian.elguetag@gmail.com]`.
- **Decisión futura requerida:** definir si Costos debe desacoplarse de
  Gerencia/Contabilidad (`implied_ids`) y si Cristhian debe conservar formalmente
  el CRUD de `stock.lot.cost.line` (hoy lo retiene vía Costos).

## 6. Validación de Cristhian (uid 8) — `env(user=8, su=False)`

| Verificación | Valor |
|---|---|
| `uid` | 8 · `_is_internal()` = True |
| `group_madenat_operaciones` | **True** |
| `group_madenat_jefatura_operaciones` | **True** |
| `group_madenat_gerencia` | **False** |
| `group_madenat_contabilidad` | **False** |
| `account.group_account_manager` | **False** |
| `account.group_account_invoice` | **False** |
| `group_madenat_costos` | True (reportado, **no** modificado) |
| `group_madenat_admin` / `base.group_system` | **False / False** |

**Guardas (read-only, sin crear/mover inventario):**
| Guard | Grupo exigido | uid 8 |
|---|---|---|
| **R2 normal** `_rebaja_require_group(REBAJA_REVERSE_GROUPS)` | Jefatura **o** Gerencia | **PASS** (Jefatura) |
| R1 rebaja extemporánea `_assert_can_regularize_b01_rebaja` | Gerencia | **BLOCKED** (AccessError) |
| R1 wizard `_assert_gerencia` | Gerencia | **BLOCKED** (AccessError) |
| Cierre B-01 `_assert_can_resolve_b01_exception` | Gerencia | **BLOCKED** (AccessError) |
| Reversa sobre B-01 `resolved` `_assert_can_reverse_rebaja_context` | Gerencia | **BLOCKED** (UserError) |
| Override Embarque `delivered` / Viaje `cancel` | Gerencia | **BLOCKED** (no hay fixture `delivered`; validado por `has_group(gerencia)=False` + código) |
| Wizard override `lumber.container.rebaja.reverse.wizard` (ACL) | Gerencia | **create=False** |

> **Limitación declarada:** el override `delivered`/`voyage cancel` no tiene fixture
> en la BD; se valida por **evidencia de código** (`_assert_can_reverse_rebaja_context`
> exige Gerencia) + `has_group(gerencia)=False`. No se crea/mueve inventario para probarlo.

---

## 7. Validación de Leonardo (uid 6) — SIN cambios

| Verificación | Valor |
|---|---|
| `_is_internal()` | True · activo · `share=False` |
| Operaciones / Jefatura / Gerencia | **False / False / False** |
| Costos / Contabilidad / Admin / Auditoría | False / False / False / False |
| `base.group_system` | **False** |
| Lectura estándar | container=True · shipment=True · audit=True · lot=True |
| Guard R2 `_rebaja_require_group` | **BLOCKED** (AccessError) |
| Total de grupos | **35 (idéntico al baseline `10_...`)** — GIDS `[…60, 62, 63]` |

- Conserva `account.group_account_manager` y `account.group_account_invoice`
  **preexistentes** (no tocados, mismo criterio que `FASE_A`/`CORRECCION_ROLES`).
- **No se le agregó ni quitó ningún grupo.**

## 8. Administrator (uid 2) — SIN cambios

- `_is_internal()`=True · `base.group_system`=**True** · 54 grupos (idéntico).
- GIDS antes/después idénticos (incluye `gerencia`(259), `contabilidad`(258),
  `operaciones`(256), `costos`(257), `jefatura`(261), `admin`).
- **No se usó como ejecutor operativo ni de UAT.** Sólo administración puntual de
  membresía (`env(user=2, su=False)`).

## 9. Confirmación de que UAT R2 NO se ejecutó

✅ `UAT-R2-20261004-*` contenedores = **0** · embarques = **0**.
✅ `rebaja_reverse` = **0** · `rebaja_return_total` = **0** (no persistidas).
✅ Sin `stock.move`/`stock.move.line`/`stock.picking`/`stock.quant` nuevos.

## 10. Conteos / integridad (idénticos a la línea base)

| Modelo | Antes | Después | | Modelo | Antes | Después |
|---|---:|---:|---|---|---:|---:|
| `stock.move` | 143 | **143** | | `shipping.vessel` | 7 | **7** |
| `stock.move.line` | 210 | **210** | | `shipping.voyage` | 1 | **1** |
| `stock.picking` | 28 | **28** | | `madenat.audit.log` | 270 | **270** |
| `stock.quant` | 171 | **171** | | `madenat.sv.operation` | 1 | **1** |
| `stock.lot` | 127 | **127** | | `madenat.sv.imputation` | 1 | **1** |
| `stock.lot.cost.line` | 53 | **53** | | `account.move` | 1 | **1** |
| `lumber.shipment.cost.line` | 0 | **0** | | `account.payment` | 0 | **0** |
| `lumber.export.shipment` | 15 | **15** | | `lumber.billing.consolidation` | 0 | **0** |
| `lumber.container` | 16 | **16** | | UAT Rolleo/Borrador/B-01/R1 | — | **intactos** |
| `lumber.shipment.line` | 6 | **6** | | `b01_exception_state` | 13/1/1 | **13/1/1** |

- **Único cambio permitido y observado:** membresía efectiva de grupos de uid 8.
- Git: rama/HEAD **sin cambios**; working tree **33 = 24 M + 9 ??**; `diff --check` **CLEAN**.

## 11. Riesgos pendientes

1. **Grupos huérfanos `#61/#62/#63/#64`** (sin XML-ID; `implied_ids=[]`) otorgan ACL
   financieras fuera del modelo canónico. Precisas:
   - `#61` "Compras y Operaciones": `stock.picking`, `stock.lot`, `stock.lot.cost.line`,
     `lumber.reception`, `purchase.order`, `account.move.send.*` → **uid 2, 8**.
   - `#62` "Validación Contable (Auditoría)": `account.move`, `account.move.line`,
     `validate.account.move`, etc. → **uid 6, 7, 8, 9**.
   - `#64` "MADENAT Aprobación Financiera y Pagos": `account.payment`,
     `account.move.reversal`, etc. → **uid 7, 8**.
   Cristhian (uid 8) **sigue** siendo miembro de `#61/#62/#64` (fuera del alcance de
   esta corrección). Decisión futura.
2. **Diseño futuro de Gerencia:** decidir si Gerencia debe implicar
   Contabilidad/`account_manager` (hoy acoplado por `implied_ids`, `noupdate=1`).
3. **Auditoría sin usuarios:** `group_madenat_auditoria` con **0 usuarios** (control
   de trazabilidad AD-80 §7 no operativo).
4. **Contabilidad sin asignación formal:** `group_madenat_contabilidad` sólo en uid 2
   (`mvantonio` documentada pero no asignada).
5. **Costos** acoplado a Gerencia/Contabilidad por `implied_ids`; revisar §5.

## 12. Dictamen

### **A. `CRISTHIAN OPERACIONES + JEFATURA CONFIRMADO — APTO PARA REINTENTAR UAT R2 NORMAL`**

- Cristhian (uid 8): **Operaciones + Jefatura**; **sin** Gerencia; **sin**
  Contabilidad/`account_manager`/`account_invoice` (heredadas exclusivamente de
  Gerencia, removidas); **sin** `base.group_system`; **sin** `group_madenat_admin`.
  Guard **R2 normal = PASS**; guardas exclusivas de **Gerencia = BLOCKED**.
- Leonardo (uid 6) y Administrator (uid 2): **sin cambios**.
- **UAT R2 no ejecutada**; stock/finanzas/SV/B-01/UAT/R1/R2/R3/Rolleo/Borrador
  intactos (delta = 0); Git/HEAD/working tree sin cambios.
- No se modificaron XML, `implied_ids`, ACL, reglas ni grupos huérfanos.

*Se detiene aquí. No se reintenta UAT R2. No se avanza a R3/Entrega/Costeo/
Facturación/Pagos. Sin commit/push. Fin del informe.*

