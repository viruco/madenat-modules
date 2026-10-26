# MADENAT — Resultado Habilitación Jefatura Operativa para UAT R2 (FASE A)

- **Sub-bloque:** 4B — R2 UAT. **Fase A — resolución read-only.**
- **Estado:** usuario resuelto; **detenido a la espera de autorización explícita** (Fase B no aplicada).
- **Regla cumplida:** sin modificar grupos/ACL/código; sin `base.group_system`; sin uid 1; sin `sudo()`; sin SQL de escritura; sin update/install; sin git mutante.
- **Fecha:** 2026-10-04.

---

## 1. Precheck y registros protegidos

| Ítem | Valor |
|---|---|
| Repo | `custom_addons/` |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Working tree | **33 = 24 ` M` + 9 `??`** (idéntico) |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy |

- **UAT R2 no creada:** contenedores `UAT-R2-20261004-*` = **0**.
- **Sin `rebaja_return_total` / `rebaja_reverse` persistidos** = **0**.
- **Protegidos intactos:** histórica (1537/1509/7065/1880-1881/15970-15971/1528/1500/7062/SV 5822/imput 492), UAT Rolleo (619-620/565/1644-1646/1629-1631/19699-19704), UAT Borrador (1704-1707/1678-1680/19742), UAT B-01 (746/1867-1869/1868-1871/19890), UAT R1 (747/1885/1888/16312/7238/13973/19941-19945).
- **B-01 sin cambios:** `none=13 / open=1 / resolved=1`.
- **Cambios de seguridad:** sólo `madenat_lumber_logistics/security/ir.model.access.csv` (+7) — **baseline** de sub-bloques previos (B-01/R1), **no** de esta fase.

## 2. Candidatos revisados

| UID | Usuario | Login | Activo | Interno | System | Operaciones | Jefatura | Gerencia | Auditoría | Recomendación |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | OdooBot | `__system__` | ❌ | (t) | ⚠️ | no | no | no | no | EXCLUIDO (uid 1 / system) |
| 2 | Administrator | mauricio.seo@gmail.com | ✅ | ✅ | ⚠️ **sí** | sí | sí | sí | no | EXCLUIDO (Administrator + `group_system`) |
| 3 | Default User Template | `default` | ❌ | (t) | no | no | no | no | no | EXCLUIDO (inactivo/plantilla) |
| 4 | Public user | `public` | ❌ | ❌ | no | no | no | no | no | EXCLUIDO (público) |
| 5 | Portal User Template | `portaltemplate` | ❌ | ❌ | no | no | no | no | no | EXCLUIDO (plantilla portal) |
| **6** | **Leonardo Rodriguez** | **leonardo@pinelli.com.mx** | ✅ | ✅ | no | no | no | no | no | **RECOMENDADO** (§3) |
| 7 | María Victoria Antonio | mvantonio@valean.cl | ✅ | ✅ | no | no | no | no | no | Alternativa (misma salvedad §3) |
| 8 | Cristhian Elgueta | cristhian.elguetag@gmail.com | ✅ | ✅ | no | sí | no | no | no | No recomendado (Operaciones; §3) |
| 9 | Felipe Muñoz | fmunoz@valean.cl | ✅ | ✅ | no | no | no | no | no | EXCLUIDO (`group_madenat_admin`) |

Ningún usuario tiene `group_madenat_auditoria`. uid 8 (Operaciones) tiene además `group_madenat_costos`.

## 3. Usuario resuelto

**uid 6 — Leonardo Rodriguez** — `leonardo@pinelli.com.mx` (activo, interno, `share=False`).

Cumple **todos** los criterios de exclusión del mandato: `active=True` · `share=False` ·
`uid != 1` · no Administrator · **no** `base.group_system` · **no** Auditoría · no
cuenta técnica · login válido · puede recibir Operaciones · perfil de coordinación
Bodega/Logística (`stock.group_stock_manager`, `group_tracking_lot`, `purchase.group_purchase_manager`).

**Observaciones de segregación (preexistentes, a reconocer explícitamente):**
- `account.group_account_manager` (Contabilidad – gerente) y `account.group_account_invoice`
  (Facturación). **No** son grupos MADENAT y **no** se agregarían en Fase B, pero
  implican acceso contable/facturación vía Odoo estándar.
- `base.group_no_one` (Funciones técnicas). No es `base.group_system`.

> No existe usuario interno con Jefatura/Gerencia **sin** grupo contable preexistente
> (uid 6 y 7 comparten `account.group_account_manager`; uid 9 tiene `group_madenat_admin`).
> Se recomienda uid 6 y se solicita **reconocimiento explícito** de la salvedad contable.

## 4. Grupos antes/después

- **Antes (uid 6):** sin grupos MADENAT. Relevantes: `base.group_user`,
  `stock.group_stock_manager`, `stock.group_tracking_lot`,
  `purchase.group_purchase_manager`, `sale.group_sale_manager`,
  `account.group_account_manager`, `account.group_account_invoice`, `base.group_no_one`.
- **Después:** **NO APLICADO** (a la espera de autorización). Objetivo de Fase B:
  agregar únicamente `group_madenat_operaciones` (gid 256) y
  `group_madenat_jefatura_operaciones` (gid 261).

## 5. Confirmación de Operaciones + Jefatura
**Pendiente** — no aplicado. No se ejecutó ningún `write` de grupos.

## 6. Confirmación de ausencia de system / Gerencia / Costeo / Contabilidad
- `base.group_system`: **no** (uid 6) → ✅ objetivo.
- MADENAT `group_madenat_gerencia`: **no** (uid 6) → ✅ objetivo.
- MADENAT `group_madenat_costos` / `group_madenat_contabilidad`: **no** (uid 6) → ✅ objetivo.
- (`account.group_account_manager` Odoo estándar: presente — **salvedad registrada §3.**)

## 7. Confirmación de que UAT R2 no se ejecutó
✅ Sin datos `UAT-R2-20261004-*`, sin `rebaja`, sin `rebaja_return_total`,
sin `rebaja_reverse`, sin pickings/moves/quant nuevos. Delta = 0.

## 8. Dictamen

### **B. `BLOQUEADO — INDICAR USUARIO O AUTORIZACIÓN FALTANTE`** (usuario resuelto)

**Usuario resuelto:** **Leonardo Rodriguez (uid 6, `leonardo@pinelli.com.mx`)**.

**Autorización solicitada (Fase B — sólo tras su confirmación):**

> ¿Autoriza asignar los grupos **Operaciones** (`group_madenat_operaciones`) y
> **Jefatura de Operaciones** (`group_madenat_jefatura_operaciones`) al usuario
> interno **Leonardo Rodriguez (uid 6, login `leonardo@pinelli.com.mx`)** para
> cubrir Inventario, Bodega, Logística, Rolleo y la confirmación controlada del
> retorno físico total R2, **sin** asignar `base.group_system`, Gerencia, Costeo,
> Facturación, Pagos ni privilegios técnicos, **reconociendo** que ya posee
> `account.group_account_manager` / `account.group_account_invoice` y
> `base.group_no_one` (preexistentes, no agregados por esta habilitación)?
>
> Alternativa si prefiere otro ejecutor: **María Victoria Antonio (uid 7)** — misma
> salvedad contable; o indicar otro usuario.

Al aprobar, la Fase B se limitará a: revalidar (activo/interno/sin `system`) →
agregar **sólo** los dos grupos faltantes → **no** eliminar grupos → verificar con
`env(user=6, su=False)` → **detenerse sin ejecutar R2**, guardando evidencia
antes/después.

*No se creó UAT. No se modificaron grupos/ACL/código. Sin commit/push. Fin del informe Fase A.*

