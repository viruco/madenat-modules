# MADENAT — Resultado Corrección Definitiva de Roles

- **Sub-bloque:** 4B — R2 UAT. **Gate previo a UAT R2.**
- **Ejecución:** `odoo shell` con `env(user=2, su=False)` → **NO** uid 1, **NO** `sudo()`.
- **Sin tocar:** código, XML, ACL, manifest, datos/UAT/stock/lotes/pickings/movimientos/costos/facturas/pagos/SV/B-01/Rolleo/Borrador/R1/R2/BT-04.
- **Fecha:** 2026-10-04.

---

## 1. Precheck e integridad
| Ítem | Valor |
|---|---|
| Repo / Rama / HEAD | `custom_addons/` · `feat/guia-correccion-documental-preservada-20261002` · `34c81272…` |
| Working tree | **33 = 24 ` M` + 9 `??`** |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy |
| UAT R2 | **no creada** (0) |
| `rebaja_return_total` / `rebaja_reverse` | **0 / 0** |
| Protegidos | histórica/Rolleo/Borrador/B-01/R1 **intactos** (B-01 `13/1/1`) |
| Delta stock/finanzas/SV | **0** |

## 2. Grupos antes/después de Leonardo (uid 6)

| Grupo | Antes | Después | Acción |
|---|---:|---:|---|
| `group_madenat_operaciones` | **Sí** | **No** | **Removido** |
| `group_madenat_jefatura_operaciones` | **Sí** | **No** | **Removido** |
| `group_madenat_gerencia` | No | No | Mantener |

- `LEO removed = ['… / Jefatura de Operaciones', '… / Operaciones']` · `LEO added = []`.
- **Grupos estándar preexistentes preservados:** `account.group_account_manager`,
  `account.group_account_invoice`, `stock.group_stock_manager`,
  `stock.group_tracking_lot`, `base.group_no_one` (sin cambios).

## 3. Grupos antes/después de Cristhian (uid 8)

| Grupo | Antes | Después | Acción |
|---|---:|---:|---|
| `group_madenat_operaciones` | **Sí** | **Sí** | Mantener (no duplicado) |
| `group_madenat_jefatura_operaciones` | No | **Sí** | **Agregado** |
| `group_madenat_gerencia` | No | **Sí** | **Agregado** |

- `CRIS removed = []` · `CRIS added ⊆ {jefatura, gerencia}` (+ **implícitos**, ver Salvedad).
- `base.group_system` = **No** · `group_madenat_admin` = **No**.

## 4. Leonardo (uid 6) — perfil de reportería/lectura
Verificación ORM `env(user=6, su=False)`:
- `OPER=False · JEF=False · GER=False · SYS=False`.
- Lectura OK: `read container=True`, `read shipment=True`, `read audit=True`
  (acceso de lectura de reportes/métricas/trazabilidad).
- **Guard de reversa R2 BLOQUEADO** (`_rebaja_require_group` → `AccessError`).
- No puede ejecutar rebaja/zarpe/B-01/rolleo/Borrador/R1/R2/reversa/Entrega
  (requieren grupos MADENAT que ya no posee).

## 5. Cristhian (uid 8) — Operaciones + Jefatura + Gerencia
Verificación ORM `env(user=8, su=False)`:
- `OPER=True · JEF=True · GER=True · SYS=False`.
- `read container=True`, `write container=True`,
  `write reverse wizard=True`, `read shipment=True`.
- **Guard de reversa R2 = PASS** (puede ejecutar el caso positivo con guards
  normales).
- Mantiene acceso integral de Inventario/Bodega/Logística (Operaciones +
  `stock.group_stock_manager` + `group_tracking_lot`).

## 6. Ausencia de system / uid 1
- uid 6 y uid 8: `base.group_system = False`; ninguno es uid 1.
- **uid 2 (Administrator): sin cambios** (verificado `snapshot before == after`).

## 7. UAT R2 aún no ejecutada
✅ Sin `UAT-R2-20261004-*`, sin `rebaja_return_total`/`rebaja_reverse`, sin
picking/move/quant nuevos. Delta stock/finanzas/SV = 0.

## 8. Dictamen

### **A. `ROLES MADENAT CORREGIDOS — CRISTHIAN APTO PARA EJECUTAR UAT R2`**
(con **salvedad de segregación** por implicación de grupos, ver abajo)

- Leonardo (uid 6): removidos Operaciones + Jefatura; perfil de **reportería/lectura**.
- Cristhian (uid 8): **Operaciones + Jefatura + Gerencia** (Jefatura/Gerencia agregados;
  Operaciones conservado sin duplicar); sin `base.group_system`; no uid 1.
- uid 2 sin cambios; UAT R2 aún no ejecutada; integridad intacta; Git sin cambios.

> **SALVEDAD DE SEGREGACIÓN (implicación de grupos, no evitable por diseño):**
> `group_madenat_gerencia` **implica** (jerarquía MADENAT confirmada en BD):
> `group_madenat_contabilidad`, `group_madenat_costos`, `group_madenat_operaciones`;
> y `group_madenat_contabilidad` **implica** `account.group_account_manager`.
> Por ello, al agregar **Gerencia** a Cristhian se incorporaron **implícitamente**
> `group_madenat_contabilidad`, `account.group_account_manager` y
> `account.group_account_invoice`. Esto **no** puede evitarse conservando Gerencia
> (el cierre transitivo de grupos los re-aplica), y por tanto la restricción
> "no agregar contabilidad/account_manager/account_invoice" (acción 5) es
> **mutuamente excluyente** con "agregar Gerencia" (acción 4) en este modelo.
> `group_madenat_costos` ya lo tenía Cristhian antes.
>
> **Recomendación:** para sellar la segregación Operaciones↔Finanzas, considere
> **otorgar sólo `group_madenat_jefatura_operaciones`** (suficiente para el caso
> R2 normal) y **no** Gerencia, o **reconocer formalmente** que el rol Gerencia
> incluye Contabilidad/account_manager por diseño.

*No se ejecutó UAT R2. No se creó UAT. Sin commit/push. Fin del informe.*
