# MADENAT — Auditoría de Documentación y Arquitectura de Roles

- **Sub-bloque:** 4B — R2 UAT. **Fase 0 — READ-ONLY (bloqueo previo).**
- **Sin cambios:** no se modificó ningún usuario/grupo/implied/ACL/rule/código/XML/CSV/manifest/test/UAT/stock/Git.
- **Fecha:** 2026-10-04.

---

## 1. Precheck e integridad
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272…` |
| Working tree | **33 = 24 ` M` + 9 `??`** |
| Runtime / DB | `odoo18_app` Up · `odoo18_db` healthy · `madenat_test` |
| UAT R2 | **no creada** (0 contenedores `UAT-R2-*`) |
| `rebaja_return_total` / `rebaja_reverse` | **0 / 0** |
| Protegidos | histórica/Rolleo/Borrador/B-01/R1 intactos (B-01 `13/1/1`) |
| `git diff --check` | CLEAN |

**Roles actuales (verificado):**

| uid | usuario | Oper | Jef | Ger | Cont | Audi | System |
|---:|---|---:|:-:|:-:|:-:|:-:|:-:|
| 2 | Administrator | t | t | t | t | f | **t** |
| 6 | Leonardo Rodriguez | f | f | f | f | f | f |
| 8 | Cristhian Elgueta | t | t | t | t | f | f |

## 2. Fuentes documentales revisadas
| Fuente | Contenido | Vigencia |
|---|---|---|
| `madenat_lumber_core/security/madenat_security.xml` | **Definición canónica de grupos e `implied_ids`** (`<data noupdate="1">`) | Código vigente |
| `madenat_lumber_core/security/ir.model.access.csv` | ACL core | Código vigente |
| `madenat_lumber_logistics/security/ir.model.access.csv` | ACL logística (incl. wizard R2) | Código vigente |
| `CANON/18_CONSOLIDACION_Y_REBAJA.md` §8 | Permisos y **matriz de autorización propuesta** | **BORRADOR/PROPUESTA** (AD-86 `PROPUESTA`) |
| `CANON/16_AUDITORIA_20261001.md` §9 | **Mapeo rol→grupo** y grupos huérfanos (migración **en seco, NO ejecutada**) | Auditoría 2026-10-01 |
| `CANON/04_DECISION_LOG.md` AD-80 §7 | **Autonomía y escalamiento** (Operaciones/Auditoría/Contabilidad) | Vigente |
| `CANON/04_DECISION_LOG.md` AD-86 | Grupo «Logística» + matriz autorización | **PROPUESTA (no aprobada)** |
| `CANON/19...` §D8 | Permisos por rol **duros**; reutiliza grupos vigentes | Vigente |
| `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Menús por grupo | Diagnóstico |
| `CANON/13_CONSOLIDACION_OPERATIVA.md` §navegación | Visibilidad Intake por grupo | Vigente |
| `CANON/05_BACKLOG.md` H-06 | `group_madenat_auditoria` con 0 usuarios | Pendiente |
| `WIKI/02_TECNICO/security_accesos.md` | Grupos/permisos | **Borrador (2026-05-30), desactualizado** |

> **Respuesta A/B/C/D:** la jerarquía `Gerencia → Contabilidad → account.group_account_manager`
> es **B — dependencia técnica DELIBERADA**: está **codificada** en `madenat_security.xml`
> (`noupdate="1"`) con comentarios de diseño explícitos. **No** es C (accidental) ni D (temporal).
> **PERO** **no** es A: **no existe un AD que apruebe** la matriz rol→grupo como decisión de
> negocio; la única matriz documental (`CANON/18 §8.3`) está en estado **PROPUESTA**.

## 3. Roles documentados versus usuarios actuales

| Rol | Documentado (qué dice) | Implementado (código/BD) | Usuario actual |
|---|---|---|---|
| **Operaciones** | `group_madenat_operaciones` = "Recepción, staging, stock físico, contenedores, embarques y trazabilidad operativa"; ejecuta rutina sin aprobación si no hay impacto financiero/documental (**AD-80 §7**) | Grupo (impl. `stock.group_stock_user`); ACL core/logística `base.group_user` | uid 8; uid 2 |
| **Jefatura de Operaciones** | "Operación avanzada/supervisión... **No** otorga admin transversal, costos ni auditoría" (xml 2026-08-23); reversa = **Jefatura/Gerencia** (CANON/18 §8.3, PROPUESTA) | Grupo (impl. `base.group_user`+`operaciones`) | uid 8 |
| **Gerencia** | "Visión consolidada, autorización y supervisión global" | Grupo (impl. `operaciones`+`costos`+`contabilidad`) | uid 8; uid 2 |
| **Auditoría** | "aprueba el alza de baseline documental y las excepciones de trazabilidad SV" (**AD-80 §7**); lectura | Grupo (impl. `base.group_user`); ACL read | **ninguno** (H-06; dry-run `fmunoz`, no ejecutado) |
| **Contabilidad** | "aprueba cuando existe costo, valoración, factura, consolidación facturada/cerrada o período financiero" (**AD-80 §7**) | Grupo (impl. `costos`+`account.group_account_manager`) | uid 8; uid 2 |
| **Costos** | "Costos base, líneas de costo, distribuciones y auditoría monetaria" | Grupo (impl. `base.group_user`) | uid 8 |
| **Administración MADENAT** | "Administración funcional del núcleo MADENAT" | Grupo (impl. `group_madenat_cost_auditor`) | uid 9; uid 2 |

**Respuestas explícitas:**
- **¿Cristhian documentado?** `CANON/16 §9`: **`cristhian → no tocar`** (mapeo de huérfanos). **Ningún
  documento** lo define como "Operaciones + Jefatura + Gerencia". Su configuración actual
  (OP+JEF+GER+CONT) es una **decisión reciente no documentada** (introducida en el gate anterior).
- **¿Felipe documentado como Auditoría?** **SÍ** — `CANON/16 §9` (`fmunoz → group_madenat_auditoria`)
  y `05_BACKLOG.md` H-06. **No ejecutado** (0 usuarios en Auditoría).
- **¿María Victoria documentada como Contabilidad?** **SÍ** — `CANON/16 §9` (`mvantonio →
  group_madenat_contabilidad`). **No ejecutado** (hoy tiene huérfanos 62/64, sin grupos canónicos).
- **¿Leonardo documentado?** **`CANON/16 §9`: `leonardo → a definir`.** **No** está documentado como
  Gerencia, Logística ni reportería. Su perfil de reportería (gate anterior) **no** está documentado.
- **¿Tabla aprobada de responsables por fase?** **NO.** La única matriz (`CANON/18 §8.3`) es
  **PROPUESTA** (AD-86), y (`CANON/16 §9`) es un mapeo de migración **no ejecutado**.

## 4. Grafo de `implied_ids` y permisos efectivos

**Fuente:** `madenat_security.xml` (`noupdate="1"`) + `res_groups_implied_rel` (BD).

| Grupo (XML ID) | Módulo | implied_ids directos | Transitivo | Lo implican | Riesgo segregación |
|---|---|---|---|---|---|
| `group_madenat_operaciones` | core | `stock.group_stock_user` | +`base.group_user` | jefatura, gerencia | Bajo |
| `group_madenat_jefatura_operaciones` | core | `base.group_user`, `operaciones` | +`stock_user` | — | Bajo |
| `group_madenat_costos` | core | `base.group_user` | — | contabilidad, gerencia | Bajo |
| `group_madenat_contabilidad` | core | `group_madenat_costos`, **`account.group_account_manager`** | +`costos`, `account_invoice`, `base_user` | gerencia | **MEDIO (financiero)** |
| `group_madenat_gerencia` | core | `operaciones`, `costos`, `contabilidad` | +`account_manager`, `account_invoice`, `stock_user`, `base_user` | — | **MEDIO (hereda finanzas)** |
| `group_madenat_auditoria` | core | `base.group_user` | — | — | Bajo |
| `group_madenat_admin` | core | `group_madenat_cost_auditor` | +`base_user` | — | Bajo |
| `group_madenat_cost_auditor` | core | `base.group_user` | — | admin, cost_auditor_plus | Bajo |
| `account.group_account_manager` | account | `account.group_account_invoice` | +`base_user` | contabilidad, gerencia | Alto (contab.) |
| `account.group_account_invoice` | account | `base.group_user` | — | account_manager | Alto (factura) |
| `base.group_system` | base | — | — | — | Crítico |

**Cadena clave (confirmada en código con comentarios de diseño):**
```
group_madenat_gerencia → group_madenat_contabilidad → account.group_account_manager
      → account.group_account_invoice → base.group_user
group_madenat_gerencia → group_madenat_operaciones → stock.group_stock_user
group_madenat_gerencia → group_madenat_costos
```
**Consecuencia:** otorgar **Gerencia** concede, por diseño, **Operaciones + Costos + Contabilidad +
`account.group_account_manager`**. No es un bug: está escrito en `madenat_security.xml`.

## 5. Matriz de autorización por operación (evidencia)

| Operación MADENAT | Operaciones | Jefatura | Gerencia | Auditoría | Contabilidad | Grupo/documento fuente |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Inventario/Bodega | ✅ | ✅ | ✅ | lectura | — | ACL `base.group_user`/`stock_manager`; AD-78 |
| Recepción/Guías | ✅ | ✅ (RWCU) | ✅ | lectura | — | core ACL; `13_CONSOLIDACION` |
| Lotes/Trazabilidad | ✅ | ✅ | ✅ | lectura | — | `stock.lot` ACL; `15_DIAGNOSTICO` |
| Contenedores/Embarques | ✅ | ✅ | ✅ | lectura | — | logistics ACL; CANON/18 §8.1 |
| Rolleo Motonave | ✅(pre-rebaja) | ✅ | ✅ | lectura | — | CANON/18 §8.3 (PROPUESTA); wizards por grupo |
| Rebaja estándar | ✅ | ✅ | ✅ | lectura | — | `action_rebajar`=oper/jef/ger (código) |
| Zarpe normal | ❌(abre) | ✅ | ✅ | — | — | `action_set_in_transit`; `DEPARTURE_*_GROUPS` |
| B-01 | ❌ | ✅(abre) | ✅ | — | — | zarpe wizard; `_guard_deviation` |
| Borrador Seguro | ❌ | ✅ | ✅ | — | — | `_return_to_draft_assert_group` (jef/ger) |
| R1 rebaja extemporánea | ❌ | ❌ | ✅(solo Gerencia) | — | — | `lumber.b01.regularization.wizard._assert_gerencia` |
| R2 reversa total (normal) | ❌ | ✅ | ✅ | — | — | `_rebaja_require_group(jef,ger)` |
| R2 (override B-01 resolved / delivered / voyage cancel) | ❌ | ❌ | ✅ | — | — | `_assert_can_reverse_rebaja_context` (Gerencia) |
| Cierre B-01 | ❌ | ❌ | ✅ | — | — | `action_resolve_b01_exception` (Gerencia) |
| Entrega/Cierre | ❌ | ✅ | ✅ | — | — | `action_deliver` (`_assert_departure_group`) |
| Costeo | — | — | ✅ | lectura | ✅ | `stock.lot.cost.line` ACL (costos/contab/ger/admin) |
| Facturación/Pagos | — | — | ✅ | lectura | ✅ | `group_madenat_contabilidad`→`account_manager` |

> La matriz `CANON/18 §8.3` (PROPUESTA) coincide en lo esencial: **reversa de rebaja = ❌ Logística,
> ✅ Jefatura, ✅ Gerencia; Auditoría lectura.**

## 6. R2: requisitos normales y excepcionales (evidencia de código)
- **`action_reverse_rebaja()`** exige `_rebaja_require_group(group_madenat_jefatura_operaciones,
  group_madenat_gerencia)` → **Jefatura O Gerencia**.
- **Wizard** `lumber.container.rebaja.reverse.wizard`: ACL **solo `group_madenat_gerencia`**
  (`madenat_lumber_logistics/security/ir.model.access.csv:20`).
- **Guard R2 total** `_assert_can_reverse_rebaja_total` / `_assert_can_reverse_rebaja_context`:
  base Jefatura o Gerencia; **exige Gerencia** si **B-01 `resolved`**, **Embarque `delivered`**,
  **viaje `cancel`** (override con motivo ≥ 20).
- **`action_rebajar`** exige `_rebaja_require_group(operaciones, jefatura, gerencia)`.
- **Conclusión:** **Jefatura sola SÍ puede ejecutar el R2 normal** (sin gates). Gerencia se exige
  en: override (B-01 resolved/delivered/voyage cancel), cierre B-01 y wizard de override.

## 7. Leonardo: perfil mínimo de reportería/lectura
- **Lectura ya disponible sin grupos MADENAT:** `lumber.container`/`shipment`/`line` (RWC vía
  `base.group_user`), `stock.lot`, `lumber.reception`, `madenat.audit.log` (**read** vía
  `base.group_user`, `ir.model.access.csv:19`), inventario estándar (`stock.group_stock_manager`).
- **GAP documentado:** **no existe** un grupo de **reportería/métricas MADENAT**. Los menús
  *Dashboard Gerencial* y *Trazabilidad 360* están gated por **`group_madenat_gerencia`**
  (`CANON/15`), que **implica finanzas** → incompatible con "reportería sin finanzas".
- **Mínimo efectivo para reportería/lectura sin acciones operativas ni configuración:**
  `base.group_user` + lectura estándar (Inventario vía `stock.group_stock_manager`). **Para
  métricas/trazabilidad MADENAT dedicadas se requeriría un grupo nuevo** (no existe; §10 Opción 3).

## 8. Discrepancias documentales / técnicas
1. **D-01:** implicación `Gerencia→Contabilidad→account_manager` **codificada** pero **sin AD
   aprobatorio**; la matriz (`CANON/18 §8.3`) sigue **PROPUESTA**.
2. **D-02:** `CANON/16 §9` → `cristhian: no tocar`; su config actual (OP+JEF+GER) **no documentada**.
3. **D-03:** `H-06` Auditoría **0 usuarios**; `fmunoz` documentado, **no asignado**.
4. **D-04:** `mvantonio` documentada Contabilidad pero **sin** `group_madenat_contabilidad`.
5. **D-05:** `leonardo: a definir` (2026-10-01); su reportería **no documentada**.
6. **D-06:** grupos **huérfanos 61/62/63/64** (sin XML-ID, ACL financieras) **presentes**; migración
   **en seco, sin ejecutar**. Miembros: `Cristhian`(61/62/64), `Leonardo`(62/63), `mvantonio`(62/64),
   `fmunoz`(62). **Otorgan `account.move`/`account.payment` fuera del modelo canónico.**
7. **D-07:** `WIKI/security_accesos.md` **desactualizado** (solo 2 grupos, 2026-05-30).
8. **D-08:** grupo «Logística» **inexistente**; AD-86 **PROPUESTA**; ACL logística usan Stock.

## 9. Riesgos de segregación
- **R-S1 (ALTO):** `Gerencia` ⇒ `account.group_account_manager` → un rol operativo obtiene poderes
  contables/facturación.
- **R-S2 (ALTO):** grupos huérfanos 61/62/64 otorgan ACL financieras **fuera del modelo canónico**
  (superficie no gobernada) a Cristhian/Leonardo/mvantonio.
- **R-S3 (MEDIO):** `Operaciones` ejecuta rebaja irreversible sin separación de quien aprueba.
- **R-S4 (MEDIO):** `Auditoría` **sin usuarios** ⇒ control de trazabilidad (AD-80 §7) **no operativo**.
- **R-S5 (BAJO):** `cost_auditor` legacy aún referenciado por menús (CANON/15).

## 10. Opciones de decisión con recomendación

| Opción | Descripción | Evidencia a favor | Evidencia en contra |
|---|---|---|---|
| **1** | Cristhian conserva OP+JEF+GER (acceso financiero aprobado) | La implicación es **deliberada** (código, `noupdate=1`) | **No** hay AD aprobatorio; `CANON/16` dice `cristhian: no tocar`; sin matriz aprobada |
| **2** | Cristhian conserva **OP+JEF**, se **retira Gerencia** (separa operaciones de finanzas) | **AD-80 §7** separa Operaciones de Contabilidad; **Jefatura basta para R2 normal**; matriz `CANON/18 §8.3` (PROPUESTA) da reversa a Jefatura | Gerencia sí requerida para overrides/cierre B-01 (pero no para R2 normal) |
| **3** | Conservar Gerencia y **rediseñar `implied_ids`** en un futuro sub-bloque de seguridad (desacoplar Contabilidad/Costos) | La implicación es deliberada; el desacople es limpio y trazable | Requiere cambio de seguridad (fuera de Fase 0) |
| **4** | **No hay evidencia suficiente** para decidir → **mantener roles sin cambios y escalar** (negocio) | Faltan AD y matriz aprobada; discrepancias D-01..D-08 | Posterga la habilitación R2 |

**Recomendación basada en evidencia: Opción 4 (escalar) con objetivo de diseño Opción 3.**
- La jerarquía es **B (deliberada en código)** pero **sin decisión de negocio aprobada** (no es A):
  no existe AD ni matriz aprobada para Cristhian = OP+JEF+GER.
- Para **estrictamente** separar Operaciones de Finanzas **hoy**, la vía segura es **Opción 2**
  (Jefatura basta para el **R2 normal**); para conservar Gerencia sin acoplar finanzas, **Opción 3**
  (rediseño de `implied_ids`, sub-bloque de seguridad futuro).
- Además, cualquier decisión debe abordar los **grupos huérfanos 61/62/64** (R-S2), que hoy ya
  otorgan acceso financiero al margen del modelo canónico.

## 11. Dictamen

### **B. `DECISIÓN DE NEGOCIO REQUERIDA — INDICAR DISCREPANCIA`**

**Discrepancia principal (D-01):** la jerarquía `group_madenat_gerencia → group_madenat_contabilidad
→ account.group_account_manager` está **codificada deliberadamente** en
`madenat_lumber_core/security/madenat_security.xml` (`noupdate="1"`), pero **no existe un AD
aprobatorio** que la respalde como política de roles; la única matriz de autorización
(`CANON/18 §8.3`) permanece en estado **PROPUESTA (AD-86)**, y `CANON/16 §9` indica
`cristhian: no tocar`.

**Discrepancias secundarias:** D-02 (Cristhian no documentado OP+JEF+GER), D-03 (Auditoría 0
usuarios), D-04 (Contabilidad no asignada a mvantonio), D-05 (Leonardo "a definir"), D-06 (grupos
huérfanos 61/62/64 con ACL financieras), D-07 (WIKI desactualizado), D-08 (grupo Logística
inexistente).

**Se requiere decisión de negocio** para elegir entre Opción 1/2/3/4 (§10). **No se modifica ningún
rol en esta fase.** Roles actuales preservados: uid 2 (sin cambios), uid 6 (sin grupos MADENAT),
uid 8 (OP+JEF+GER+CONT por implicación).

*Read-only. No se modificaron roles, grupos, implied_ids, ACL, rules, código, XML/CSV, manifest,
tests, UAT, inventario, stock, SV, B-01, R1/R2, costeo, facturación, pagos ni BT-04. Sin commit/push.
No se continuó UAT R2. Fin del informe.*


