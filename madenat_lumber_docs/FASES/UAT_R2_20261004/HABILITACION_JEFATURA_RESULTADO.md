# MADENAT — Resultado Habilitación Jefatura Operativa para UAT R2

- **Sub-bloque:** 4B — R2 UAT. **Fases A (resolución) + B (aplicación autorizada).**
- **Autorización recibida:** uid 6 — Leonardo Rodriguez.
- **Regla cumplida:** sin `base.group_system`; sin uid 1; sin `sudo()`; sin SQL de
  escritura; sin ACL/código/manifest/tests; sin update/install; sin git mutante.
- **Fecha:** 2026-10-04.

---

## 1. Precheck y registros protegidos

| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272…` |
| Working tree | **33 = 24 ` M` + 9 `??`** (idéntico antes y después) |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · Core 18.0.6.5.0 / Logistics 18.0.1.6.0 |
| UAT R2 | **no creada** (0) |
| `rebaja_return_total` / `rebaja_reverse` | **0 / 0** |
| Protegidos | histórica, UAT Rolleo, Borrador, B-01, R1 → **intactos** (B-01 `13/1/1`) |
| Cambios de seguridad | sólo `ir.model.access.csv` (+7) = **baseline** (no de esta fase) |

## 2. Candidatos revisados

| UID | Usuario | Login | Activo | Interno | System | Oper | Jef | Ger | Auditoría | Recomendación |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | OdooBot | `__system__` | ❌ | (t) | ⚠️ | no | no | no | no | EXCLUIDO |
| 2 | Administrator | mauricio.seo@gmail.com | ✅ | ✅ | ⚠️ sí | sí | sí | sí | no | EXCLUIDO (`group_system`) |
| 3 | Default User Template | `default` | ❌ | (t) | no | no | no | no | no | EXCLUIDO |
| 4 | Public user | `public` | ❌ | ❌ | no | no | no | no | no | EXCLUIDO |
| 5 | Portal User Template | `portaltemplate` | ❌ | ❌ | no | no | no | no | no | EXCLUIDO |
| **6** | **Leonardo Rodriguez** | **leonardo@pinelli.com.mx** | ✅ | ✅ | no | (→sí) | (→sí) | no | no | **SELECCIONADO** |
| 7 | María Victoria Antonio | mvantonio@valean.cl | ✅ | ✅ | no | no | no | no | no | Alternativa |
| 8 | Cristhian Elgueta | cristhian.elguetag@gmail.com | ✅ | ✅ | no | sí | no | no | no | No recomendado (Operaciones) |
| 9 | Felipe Muñoz | fmunoz@valean.cl | ✅ | ✅ | no | no | no | no | no | EXCLUIDO (`group_madenat_admin`) |

## 3. Usuario resuelto
**uid 6 — Leonardo Rodriguez** (`leonardo@pinelli.com.mx`): activo, interno
(`share=False`), `uid≠1`, no Administrator, **no** `base.group_system`, **no**
Auditoría, no técnico. **Salvedad reconocida:** posee `account.group_account_manager`
y `account.group_account_invoice` (y `base.group_no_one`) **preexistentes** de
Odoo estándar — no agregados por esta habilitación.

## 4. Grupos antes / después

| | Grupos MADENAT |
|---|---|
| **Antes** | (ninguno) |
| **Después** | `group_madenat_operaciones` + `group_madenat_jefatura_operaciones` |
| **Agregados** | `['MADENAT: Gestión Madera / Jefatura de Operaciones', 'MADENAT: Gestión Madera / Operaciones']` |
| **Eliminados** | `[]` (no se quitó ningún grupo) |

Aplicado con `env(user=2, su=False)` (**no** uid 1, **no** `sudo()`), sólo al
verificar que faltaban los dos grupos.

## 5. Confirmación de Operaciones + Jefatura
`OPER=True` · `JEF=True` (uid 6) — verificado en ORM (`env(user=6, su=False)`) y en
BD directa.

## 6. Confirmación de ausencia de system / Gerencia / Costeo / Contabilidad
`SYS=False` · `GER=False` · `COST=False` · `CONT=False` · `AUD=False`.
Además, como uid 6 (`su=False`): `can_write_users=False`, `can_write_acl=False`,
`can_write_configparam=False` (no puede alterar configuración/seguridad);
`can_read/write_container=True`, `can_read_shipment=True`, `can_read_audit=True`;
`_rebaja_require_group(jefatura, gerencia)=PASS`.
`can_write_rev_wizard=False` → el **wizard de override** es Gerencia-only por ACL
(por diseño); el **camino R2 normal** (sin gates) es server-side vía
`action_reverse_rebaja`, ejecutable por Jefatura.

## 7. Confirmación de que UAT R2 todavía no se ejecutó
✅ Sin `UAT-R2-20261004-*`, sin `rebaja`/`rebaja_return_total`/`rebaja_reverse`,
sin pickings/moves/quant nuevos. Delta de inventario/finanzas/SV = 0.

## 8. Dictamen

### **A. `EJECUTOR JEFATURA OPERATIVA HABILITADO — APTO PARA REINTENTAR UAT R2`**

- Ejecutor UAT R2: **Leonardo Rodriguez (uid 6)**, no-administrador.
- Grupos: **Operaciones + Jefatura de Operaciones** (agregados), **sin** system,
  Gerencia, Costeo, Contabilidad, Pagos ni privilegios técnicos; ningún grupo
  eliminado.
- UAT R2 **aún no ejecutada**; sin cambios de stock/finanzas/SV; protegidos intactos;
  Git sin cambios.

**Fase B completada.** Siguiente paso (a la espera de su orden): **reintentar la
UAT R2** (Fase D) con `UAT-R2-20261004-*`, sin retorno parcial, sin R3, sin
Entrega/Costeo/Facturación/Pagos.

*No se ejecutó R2. No se creó UAT. Sin commit/push. Fin del informe.*
